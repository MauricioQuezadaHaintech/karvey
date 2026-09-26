#!/usr/bin/env python3
"""karvey-trace.py — requirement → task → commit → test traceability of a change (architecture §1.12 C-14).

    karvey-trace.py <change> [--base REF] [--write] [--check] [--root DIR] [--json]
    karvey-trace.py <change> --wbs [--root DIR] [--json]

- **Requirements**: the ``REQ-…-NNN`` headings of ``requirements.md`` and the ADDED / MODIFIED ids of
  ``spec-delta.md``.
- **Tasks**: the ``### E{n}.F{n}.T{n} [Layer] …`` blocks of ``tasks.md`` and the requirements they cite. A
  requirement is covered by a ``[Test]`` task, by a task whose ``Tests added`` is not ``none``, or by a
  ``manual: {reason}`` line naming it; otherwise it is ``uncovered``. ``test_first`` says whether every
  implementation task citing it depends (transitively) on one of its test tasks.
- **Commits**: ``base..HEAD`` commits whose ``Karvey-Change`` trailer is the change, linked to a requirement when
  the message cites its id or the id of a task that cites it; none → ``no commit``.
- **Tests**: files matched by ``project.json:tests.globs`` (defaults below) carrying ``@req REQ-…-NNN`` or a
  ``test_REQ_…_NNN`` name; a JSON test table (``{"cases": [{"tags": [...]}]}``) references the ids in its cases'
  tags. A Markdown script under a ``tests/manual/`` folder is a **manual exception** for the ids its title
  names (reason: the script). A test file added by the change's commits with no reference is an ``unmapped test``.

- **Last result** of each test file: from the JUnit XML files named in ``changes/{id}/evidence.jsonl`` (the
  newest file that has a test case of it), else from the newest evidence line whose command ran it (the file,
  its name or a directory holding it in the argv; exit 0 → ``pass``); with neither it is ``not run``.
- ``--write`` renders ``changes/{id}/traceability.md`` (the only file this tool writes).
- ``--check`` is the coverage gate (REQ-W2-062): every requirement needs a green test (last result ``pass``) or
  a ``manual`` exception. Its mode is ``coverage.requirements`` (warn in 3.13): one ``checks.jsonl`` hit per
  uncovered requirement; ``blocking`` exits 1.

- ``--wbs`` (wave3 §1.19, REQ-W3-043): every task of ``tasks.md`` under exactly one ``## Feature E{n}.F{n}`` (or
  the Epic items ``## Epic item E{n}.QA`` / ``E{n}.DEPLOY``) whose id it carries; a requirement whose tasks span two
  Features needs a ``Split:`` line in the later Feature. Issues are reported in the ``wbs.split`` mode.

Exit: 0 · 1 coverage gate refused (blocking) · 2 usage · 4 not found. Python >= 3.9, stdlib only.
"""
import argparse
import fnmatch
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import atomicio, gitlog, manifest as mf, modes, project as pj  # noqa: E402

TOOL = "karvey-trace"
DEFAULT_GLOBS = ("tests/**", "**/test_*", "**/*_test.*", "**/*.test.*", "**/*.spec.*")
REQ_ID = re.compile(r"\bREQ-[A-Z0-9]+-\d{3}\b")
_REQ_HEAD = re.compile(r"^#{2,4}\s+(?:[\d.]+\s+)?(REQ-[A-Z0-9]+-\d{3})\b", re.M)
_DELTA_ITEM = re.compile(r"^\s*-\s+\*\*(REQ-[A-Z0-9]+-\d{3})\*\*", re.M)
_TASK_HEAD = re.compile(r"^###\s+(E\d+\.F\d+\.T\d+)\s+\[([^\]]+)\]\s*(.*)$", re.M)
_TASK_ID = re.compile(r"\bE\d+\.F\d+\.T\d+\b")
_TAG = re.compile(r"@req((?:\s+REQ-[A-Z0-9]+-\d{3})+)")
_NAME = re.compile(r"\btest_REQ_([A-Z0-9]+)_(\d{3})")
_MANUAL = re.compile(r"\bmanual:\s*\S")


class NotFound(Exception):
    pass


def _read(p):
    try:
        return Path(p).read_text(encoding="utf-8-sig")
    except OSError:
        return None


def requirement_ids(cdir):
    ids = []
    req = _read(cdir / "requirements.md") or ""
    for m in _REQ_HEAD.finditer(req):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    delta = _read(cdir / "spec-delta.md") or ""
    section = None
    for line in delta.splitlines():
        h = re.match(r"^##\s+(ADDED|MODIFIED|REMOVED)\b", line)
        if h:
            section = h.group(1)
            continue
        m = _DELTA_ITEM.match(line)
        if m and section in ("ADDED", "MODIFIED") and m.group(1) not in ids:
            ids.append(m.group(1))
    return ids


def parse_tasks(text):
    """``{task_id: {layer, title, reqs, depends, tests_added, manual_reqs}}`` from ``tasks.md``."""
    tasks = {}
    heads = list(_TASK_HEAD.finditer(text or ""))
    for i, m in enumerate(heads):
        body = text[m.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        body = re.split(r"^## ", body, maxsplit=1, flags=re.M)[0]
        title = m.group(3)
        dep = re.search(r"_Depends:\s*([^_]+)_", title)
        req_line = re.search(r"^\*\*Requirements:\*\*(.*)$", body, re.M)
        ta = re.search(r"^\*\*Tests added:\*\*\s*(.*)$", body, re.M)
        tests_added = bool(ta and ta.group(1).strip() and not re.match(r"none\b", ta.group(1).strip(), re.I))
        manual = set()
        for line in body.splitlines():
            if _MANUAL.search(line):
                manual.update(REQ_ID.findall(line))
        tasks[m.group(1)] = {"layer": m.group(2), "title": title.split(" — _Depends")[0].strip(),
                             "reqs": REQ_ID.findall(req_line.group(1)) if req_line else [],
                             "depends": _TASK_ID.findall(dep.group(1)) if dep else [],
                             "tests_added": tests_added, "manual_reqs": sorted(manual)}
    return tasks


def _ancestors(tasks, tid, seen=None):
    seen = set() if seen is None else seen
    for d in tasks.get(tid, {}).get("depends", []):
        if d not in seen:
            seen.add(d)
            _ancestors(tasks, d, seen)
    return seen


def change_commits(root, change, base):
    """``[{sha, message}]`` of ``base..HEAD`` commits whose trailer is ``change`` (empty when git cannot answer)."""
    try:
        out = gitlog.run(["log", "--format=%H%x1f%B%x1e", "%s..HEAD" % gitlog.check_ref(base)], root)
    except gitlog.GitLogError:
        return None
    rows = []
    for rec in out.split("\x1e"):
        rec = rec.strip("\n")
        if "\x1f" not in rec:
            continue
        sha, msg = rec.split("\x1f", 1)
        vals = re.findall(r"^Karvey-Change:\s*(\S+)\s*$", msg, re.M)
        if mf.parse_trailers(vals)[0] == change:
            rows.append({"sha": sha.strip(), "message": msg})
    return rows


def _match(rel, globs):
    return any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch("/" + rel, "/" + g.lstrip("*/"))
               or (g.startswith("**/") and fnmatch.fnmatch(rel.rsplit("/", 1)[-1], g[3:])) for g in globs)


def test_files(root, globs):
    try:
        names = gitlog.run(["ls-files"], root).splitlines()
    except gitlog.GitLogError:
        names = [str(p.relative_to(root)).replace(os.sep, "/") for p in Path(root).rglob("*") if p.is_file()]
    return [n for n in names if _match(n, globs) and not n.startswith("docs/")]


def _json_table_refs(text):
    try:
        data = json.loads(text)
    except ValueError:
        return set()
    cases = data.get("cases") if isinstance(data, dict) else data
    refs = set()
    for c in cases if isinstance(cases, list) else []:
        for t in (c.get("tags") or []) if isinstance(c, dict) else []:
            if isinstance(t, str) and REQ_ID.fullmatch(t):
                refs.add(t)
    return refs


def is_manual_script(rel):
    return rel.endswith(".md") and "/tests/manual/" in "/" + rel


def manual_script_refs(text):
    """The ids a manual script's title names (its first heading)."""
    for line in (text or "").splitlines():
        if line.startswith("#"):
            return set(REQ_ID.findall(line))
    return set()


def test_refs(text, rel=""):
    if rel.endswith(".json"):
        return _json_table_refs(text)
    refs = set()
    for m in _TAG.finditer(text):
        refs.update(REQ_ID.findall(m.group(1)))
    for m in _NAME.finditer(text):
        refs.add("REQ-%s-%s" % (m.group(1), m.group(2)))
    return refs


def added_files(root, base):
    try:
        out = gitlog.run(["diff", "--name-only", "--diff-filter=A", "--no-renames", "%s...HEAD" % gitlog.check_ref(base)],
                         root)
    except gitlog.GitLogError:
        return set()
    return {x.strip() for x in out.splitlines() if x.strip()}


EVIDENCE_FILE = "evidence.jsonl"
TRACE_FILE = "traceability.md"
JUNIT_MAX_BYTES = 20 * 1024 * 1024


def evidence_records(cdir):
    """The ``evidence.jsonl`` records of the change, oldest first (unreadable lines skipped)."""
    out = []
    for line in (_read(cdir / EVIDENCE_FILE) or "").splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _junit_path(root, rec):
    j = rec.get("junit")
    if not isinstance(j, str) or not j:
        return None
    p = Path(j)
    if not p.is_absolute():
        p = Path(root) / (rec.get("cwd_rel") or ".") / p
    return p


def junit_cases(path):
    """``[(file_or_class, name, outcome)]`` of a JUnit XML (outcome pass | fail | skipped); [] when unreadable."""
    try:
        if path.stat().st_size > JUNIT_MAX_BYTES:
            return []
        tree = ET.parse(str(path))
    except (OSError, ET.ParseError):
        return []
    cases = []
    for tc in tree.getroot().iter("testcase"):
        tags = {c.tag for c in tc}
        outcome = "fail" if tags & {"failure", "error"} else ("skipped" if "skipped" in tags else "pass")
        cases.append((tc.get("file") or tc.get("classname") or "", tc.get("name") or "", outcome))
    return cases


def _case_is_of(case_ref, rel):
    """A JUnit case belongs to a test file by its ``file`` attribute or by its class/module name."""
    if not case_ref:
        return False
    ref = case_ref.replace("\\", "/")
    if ref == rel or ref.endswith("/" + rel) or rel.endswith("/" + ref):
        return True
    stem = rel.rsplit("/", 1)[-1].split(".", 1)[0]
    parts = re.split(r"[./]", ref)
    return stem in parts


def _argv_ran(rec, rel):
    """Did an evidence command run this test file (its path, name, stem or a directory above it)?"""
    argv = rec.get("argv") if isinstance(rec.get("argv"), list) else []
    base = rel.rsplit("/", 1)[-1]
    stem = base.split(".", 1)[0]
    cwd = (rec.get("cwd_rel") or ".").strip("/")
    pattern = None
    for i, a in enumerate(argv):
        if a == "-p" and i + 1 < len(argv):
            pattern = argv[i + 1]
    for a in argv:
        if not isinstance(a, str) or not a or a.startswith("-"):
            continue
        cand = a.replace("\\", "/").rstrip("/")
        full = cand if cwd in ("", ".") else "%s/%s" % (cwd, cand)
        if cand in (rel, base, stem) or full == rel or re.search(r"(^|[./])%s($|[.:])" % re.escape(stem), cand):
            return True
        if cand and (rel.startswith(cand + "/") or rel.startswith(full + "/")):
            if pattern is None or fnmatch.fnmatch(base, pattern):
                return True
    return False


def last_results(root, cdir, files):
    """``{test_file: pass | fail | skipped | not run}`` from JUnit files named in evidence, else the evidence exit."""
    recs = evidence_records(cdir)
    res = {}
    junits = []
    for rec in reversed(recs):
        p = _junit_path(root, rec)
        if p is not None:
            junits.append(junit_cases(p))
    for f in files:
        outcome = None
        for cases in junits:
            mine = [c for c in cases if _case_is_of(c[0], f)]
            if mine:
                outs = {c[2] for c in mine}
                outcome = "fail" if "fail" in outs else ("pass" if "pass" in outs else "skipped")
                break
        if outcome is None:
            for rec in reversed(recs):
                if _argv_ran(rec, f):
                    outcome = "pass" if rec.get("exit") == 0 else "fail"
                    break
        res[f] = outcome or "not run"
    return res


def _req_result(results):
    if not results:
        return "no test"
    if "fail" in results:
        return "fail"
    if "pass" in results:
        return "pass"
    return "not run" if "not run" in results else "skipped"


def build(root, change, base=None, project=None):
    """The traceability model of one change (pure over the repo; nothing written)."""
    cdir = Path(root) / pj.CHANGES_DIR / change
    if not (cdir / "spec.json").is_file():
        raise NotFound("change %r not found (no %s)" % (change, cdir / "spec.json"))
    if project is None:
        project, _ = pj.load_project_json(root)
    if base is None:
        _, _, prod = pj.branch_flow(project or {})
        base = "origin/%s" % (prod or "main")
    globs = list(((project or {}).get("tests") or {}).get("globs") or DEFAULT_GLOBS)
    reqs = requirement_ids(cdir)
    tasks = parse_tasks(_read(cdir / "tasks.md") or "")
    commits = change_commits(root, change, base)
    files = test_files(root, globs)
    by_req, file_refs, manual_scripts = {}, {}, {}
    for f in files:
        text = _read(Path(root) / f) or ""
        if is_manual_script(f):
            refs = manual_script_refs(text)
            file_refs[f] = refs
            for r in refs:
                manual_scripts.setdefault(r, []).append(f)
            continue
        refs = test_refs(text, f)
        file_refs[f] = refs
        for r in refs:
            by_req.setdefault(r, []).append(f)
    rows = []
    for rid in reqs:
        citing = [t for t, d in tasks.items() if rid in d["reqs"]]
        test_tasks = [t for t in citing if tasks[t]["layer"].lower() == "test"]
        impl_tasks = [t for t in citing if t not in test_tasks]
        with_tests = [t for t in impl_tasks if tasks[t]["tests_added"]]
        manual = [t for t, d in tasks.items() if rid in d["manual_reqs"]] + sorted(manual_scripts.get(rid, []))
        test_first = bool(test_tasks) and all(set(test_tasks) & _ancestors(tasks, t) for t in impl_tasks)
        if commits is None:
            linked = None
        else:
            keys = [rid] + citing
            linked = [c["sha"] for c in commits if any(k in c["message"] for k in keys)]
        status = "covered" if (test_tasks or with_tests or manual) else "uncovered"
        rows.append({"id": rid, "tasks": citing, "test_tasks": test_tasks, "manual": bool(manual),
                     "manual_reasons": ["manual script %s" % m if "/" in m else "manual: line in %s" % m
                                        for m in manual],
                     "test_first": test_first, "status": status, "tests": sorted(by_req.get(rid, [])),
                     "commits": linked, "commit_text": "no commit" if linked == [] else None})
    results = last_results(root, cdir, sorted({f for r in rows for f in r["tests"]}))
    for r in rows:
        r["results"] = {f: results[f] for f in r["tests"]}
        r["result"] = _req_result(list(r["results"].values()))
        r["green"] = r["manual"] or r["result"] == "pass"
    added = added_files(root, base)
    unmapped = sorted(f for f in files if f in added and not file_refs.get(f))
    return {"change": change, "base": base, "requirements": rows, "unmapped_tests": unmapped,
            "uncovered": [r["id"] for r in rows if r["status"] == "uncovered"],
            "no_commit": [r["id"] for r in rows if r["commits"] == []],
            "commits_readable": commits is not None, "globs": globs,
            "not_green": [r["id"] for r in rows if not r["green"]]}


def render(res):
    """``traceability.md`` — deterministic for the same model (no timestamps)."""
    n = len(res["requirements"])
    green = n - len(res["not_green"])
    out = ["# Traceability: %s" % res["change"], "",
           "> Generated by `karvey-trace.py %s --write` — do not edit by hand; re-run it. Base `%s`."
           % (res["change"], res["base"]), "",
           "Coverage: %d/%d requirements with a green test or a `manual` exception · %d uncovered by tasks · "
           "%d without commit · %d unmapped test(s)" % (green, n, len(res["uncovered"]), len(res["no_commit"]),
                                                       len(res["unmapped_tests"])), "",
           "| Requirement | Tasks | Commits | Tests | Last result | Coverage |",
           "|---|---|---|---|---|---|"]
    for r in res["requirements"]:
        if r["commits"] is None:
            commits = "not readable"
        elif not r["commits"]:
            commits = "no commit"
        else:
            commits = ", ".join("`%s`" % c[:7] for c in r["commits"])
        tests = ", ".join("`%s`" % t for t in r["tests"]) or "—"
        result = r["result"] + (" · manual" if r["manual"] else "")
        cov = "green" if r["green"] else ("uncovered" if r["status"] == "uncovered" else "not green")
        out.append("| %s | %s | %s | %s | %s | %s |" % (r["id"], ", ".join(r["tasks"]) or "—", commits, tests,
                                                      result, cov))
    manual = [(r["id"], r.get("manual_reasons") or []) for r in res["requirements"] if r["manual"]]
    if manual:
        out += ["", "## Manual exceptions", ""] + ["- %s — %s" % (rid, "; ".join(why)) for rid, why in manual]
    if res["unmapped_tests"]:
        out += ["", "## Unmapped tests", ""] + ["- `%s`" % f for f in res["unmapped_tests"]]
    return "\n".join(out) + "\n"


def write(root, res):
    path = Path(root) / pj.CHANGES_DIR / res["change"] / TRACE_FILE
    atomicio.write_text_atomic(path, render(res), expected_sha256="*")  # a generated file: this tool owns it
    return path


def check(root, res, project=None):
    """The coverage gate: ``{mode, verdict, line, missing, hits}``; a hit per requirement not green."""
    m = modes.resolve(root, "coverage.requirements", project=project)
    missing = list(res["not_green"])
    n = len(res["requirements"])
    hits = 0
    for rid in missing:
        try:
            modes.record_hit(root, res["change"], "coverage.requirements",
                             "%s: no green test and no manual exception" % rid, mode=m["mode"])
            hits += 1
        except (modes.ModeError, OSError):
            pass
    if not missing:
        verdict = "pass"
    elif m["mode"] == "blocking":
        verdict = "fail"
    elif m["mode"] == "off":
        verdict = "off"
    else:
        verdict = "warn"
    return {"mode": m["mode"], "verdict": verdict, "line": "coverage: %d/%d" % (n - len(missing), n),
            "missing": missing, "hits": hits, "warning": m["warning"]}


# --------------------------------------------------------------------------- WBS (wave3 §1.19, REQ-W3-043)
_WBS_SECTION = re.compile(r"^##\s+(?:Feature\s+(E\d+\.F\d+)\b|Epic item\s+(E\d+\.(?:QA|DEPLOY))\b)", re.I)
_WBS_TASK = re.compile(r"^###\s+(E\d+\.(?:F\d+|QA|DEPLOY))\.T\d+\b")


def wbs(text):
    """``{tasks, features, issues}`` of a ``tasks.md``: every task under exactly one Feature (or the Epic items
    ``E{n}.QA`` / ``E{n}.DEPLOY``) whose id it carries; a requirement whose tasks span two Features needs a
    ``Split:`` line (naming it, or naming none) in the later Feature."""
    section, order, tasks, issues = None, [], {}, []
    splits = {}
    body_req = None
    cur_task = None
    for n, line in enumerate((text or "").splitlines(), 1):
        if line.startswith("## "):
            m = _WBS_SECTION.match(line)
            section = (m.group(1) or m.group(2)).upper().replace(".F", ".F") if m else None
            if section and section not in order:
                order.append(section)
            cur_task = None
            continue
        m = _WBS_TASK.match(line)
        if m:
            tid = line.split()[1]
            parent = m.group(1)
            cur_task = tid
            if section is None:
                issues.append("%s: outside any Feature (line %d)" % (tid, n))
            elif section.upper() != parent.upper():
                issues.append("%s: under %s but its id names %s (line %d)" % (tid, section, parent, n))
            if tid in tasks:
                issues.append("%s: listed twice (line %d)" % (tid, n))
            tasks[tid] = {"parent": section, "reqs": []}
            continue
        if cur_task and re.match(r"^\*\*Requirements:\*\*", line):
            # an id the requirement MODIFIES is another change's requirement, not one this plan places
            tasks[cur_task]["reqs"] = REQ_ID.findall(re.sub(r"MODIFIES\s+(?:REQ-[A-Z0-9]+-\d{3}[,\s]*)+", "", line))
        if section and re.search(r"\bSplit:", line):
            ids = REQ_ID.findall(line)
            splits.setdefault(section, set()).update(ids or {"*"})
    by_req = {}
    for tid, t in tasks.items():
        if t["parent"] and ".F" in t["parent"]:
            for r in t["reqs"]:
                by_req.setdefault(r, [])
                if t["parent"] not in by_req[r]:
                    by_req[r].append(t["parent"])
    for r, feats in sorted(by_req.items()):
        if len(feats) < 2:
            continue
        feats = sorted(feats, key=order.index)
        for later in feats[1:]:
            sp = splits.get(later, set())
            if r not in sp and "*" not in sp:
                issues.append("%s: tasks in %s without a Split: line in %s" % (r, " and ".join(feats), later))
    return {"tasks": len(tasks), "features": [x for x in order if ".F" in x],
            "epic_items": [x for x in order if ".F" not in x], "issues": issues}


def wbs_main(root, args):
    cdir = Path(root) / pj.CHANGES_DIR / args.change
    text = _read(cdir / "tasks.md")
    if text is None:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue(
            "trace.not_found", "no tasks.md for %s" % args.change)]), args.json)
    res = wbs(text)
    res["change"] = args.change
    mode = modes.resolve(root=root, check_id="wbs.split")["mode"]
    res["mode"] = mode
    lines = ["%s: WBS — %d task(s) under %d Feature(s)%s · %d issue(s) (wbs.split: %s)" % (
        args.change, res["tasks"], len(res["features"]),
        (" + " + ", ".join(res["epic_items"])) if res["epic_items"] else "", len(res["issues"]), mode)]
    lines += ["  " + i for i in res["issues"]]
    code, warnings, errors = kl.EXIT_OK, [], []
    for i in res["issues"]:
        if modes.would_refuse(mode):
            errors.append(kl.issue("trace.wbs", i))
            code = kl.EXIT_FINDINGS
        elif mode != "off":
            warnings.append(kl.issue("trace.wbs", i, severity="warning"))
    return kl.emit(kl.envelope(TOOL, code, result=res, warnings=warnings, errors=errors), args.json,
                   human="\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="karvey-trace.py", description="requirement → task → commit → test")
    ap.add_argument("change")
    ap.add_argument("--base", help="default origin/{branch_flow.production}")
    ap.add_argument("--write", action="store_true", help="render changes/{id}/traceability.md")
    ap.add_argument("--check", action="store_true", help="coverage gate (coverage.requirements mode)")
    ap.add_argument("--wbs", action="store_true", help="the work breakdown of tasks.md (REQ-W3-043)")
    ap.add_argument("--root")
    ap.add_argument("--json", action="store_true")
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        if exc.code and as_json:
            kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", "invalid arguments")]), True)
        return kl.EXIT_USAGE if exc.code else 0
    root = pj.find_root(start=os.getcwd(), root=args.root)
    try:
        if root is None:
            raise NotFound("not a Karvey project (no docs/spec)")
        if args.wbs:
            return wbs_main(root, args)
        res = build(root, args.change, args.base)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("trace.not_found", str(exc))]), args.json)
    n = len(res["requirements"])
    lines = ["%s: %d requirement(s), %d covered, %d uncovered, %d without commit, %d unmapped test(s)" % (
        args.change, n, n - len(res["uncovered"]), len(res["uncovered"]), len(res["no_commit"]),
        len(res["unmapped_tests"]))]
    lines += ["  uncovered %s" % r for r in res["uncovered"]]
    lines += ["  unmapped test %s" % f for f in res["unmapped_tests"]]
    code, warnings, errors = kl.EXIT_OK, [], []
    if args.write:
        path = write(root, res)
        res["written"] = os.path.relpath(str(path), str(root)).replace(os.sep, "/")
        lines.append("written %s" % res["written"])
    if args.check:
        gate = check(root, res)
        res["coverage"] = gate
        lines.append("%s (%s, mode %s)" % (gate["line"], gate["verdict"], gate["mode"]))
        lines += ["  not green %s" % r for r in gate["missing"]]
        if gate["warning"]:
            warnings.append(kl.issue("trace.mode", gate["warning"], severity="warning"))
        if gate["verdict"] == "warn":
            warnings.append(kl.issue("trace.coverage", "%d requirement(s) without a green test or manual "
                                     "exception" % len(gate["missing"]), severity="warning"))
        elif gate["verdict"] == "fail":
            code = 1
            errors.append(kl.issue("trace.coverage", "coverage gate refused: %s" % ", ".join(gate["missing"])))
    return kl.emit(kl.envelope(TOOL, code, result=res, warnings=warnings, errors=errors), args.json,
                   human="\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
