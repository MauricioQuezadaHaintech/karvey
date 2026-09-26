#!/usr/bin/env python3
"""karvey-trace.py — requirement → task → commit → test traceability of a change (architecture §1.12 C-14).

    karvey-trace.py <change> [--base REF] [--root DIR] [--json]

- **Requirements**: the ``REQ-…-NNN`` headings of ``requirements.md`` and the ADDED / MODIFIED ids of
  ``spec-delta.md``.
- **Tasks**: the ``### E{n}.F{n}.T{n} [Layer] …`` blocks of ``tasks.md`` and the requirements they cite. A
  requirement is covered by a ``[Test]`` task, by a task whose ``Tests added`` is not ``none``, or by a
  ``manual: {reason}`` line naming it; otherwise it is ``uncovered``. ``test_first`` says whether every
  implementation task citing it depends (transitively) on one of its test tasks.
- **Commits**: ``base..HEAD`` commits whose ``Karvey-Change`` trailer is the change, linked to a requirement when
  the message cites its id or the id of a task that cites it; none → ``no commit``.
- **Tests**: files matched by ``project.json:tests.globs`` (defaults below) carrying ``@req REQ-…-NNN`` or a
  ``test_REQ_…_NNN`` name. A test file added by the change's commits with no reference is an ``unmapped test``.

Read-only. Exit: 0 · 2 usage · 4 not found. Python >= 3.9, stdlib only.
"""
import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import gitlog, manifest as mf, project as pj  # noqa: E402

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


def test_refs(text):
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
    by_req, file_refs = {}, {}
    for f in files:
        refs = test_refs(_read(Path(root) / f) or "")
        file_refs[f] = refs
        for r in refs:
            by_req.setdefault(r, []).append(f)
    rows = []
    for rid in reqs:
        citing = [t for t, d in tasks.items() if rid in d["reqs"]]
        test_tasks = [t for t in citing if tasks[t]["layer"].lower() == "test"]
        impl_tasks = [t for t in citing if t not in test_tasks]
        with_tests = [t for t in impl_tasks if tasks[t]["tests_added"]]
        manual = [t for t, d in tasks.items() if rid in d["manual_reqs"]]
        test_first = bool(test_tasks) and all(set(test_tasks) & _ancestors(tasks, t) for t in impl_tasks)
        if commits is None:
            linked = None
        else:
            keys = [rid] + citing
            linked = [c["sha"] for c in commits if any(k in c["message"] for k in keys)]
        status = "covered" if (test_tasks or with_tests or manual) else "uncovered"
        rows.append({"id": rid, "tasks": citing, "test_tasks": test_tasks, "manual": bool(manual),
                     "test_first": test_first, "status": status, "tests": sorted(by_req.get(rid, [])),
                     "commits": linked, "commit_text": "no commit" if linked == [] else None})
    added = added_files(root, base)
    unmapped = sorted(f for f in files if f in added and not file_refs.get(f))
    return {"change": change, "base": base, "requirements": rows, "unmapped_tests": unmapped,
            "uncovered": [r["id"] for r in rows if r["status"] == "uncovered"],
            "no_commit": [r["id"] for r in rows if r["commits"] == []],
            "commits_readable": commits is not None, "globs": globs}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="karvey-trace.py", description="requirement → task → commit → test")
    ap.add_argument("change")
    ap.add_argument("--base", help="default origin/{branch_flow.production}")
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
        res = build(root, args.change, args.base)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("trace.not_found", str(exc))]), args.json)
    n = len(res["requirements"])
    lines = ["%s: %d requirement(s), %d covered, %d uncovered, %d without commit, %d unmapped test(s)" % (
        args.change, n, n - len(res["uncovered"]), len(res["uncovered"]), len(res["no_commit"]),
        len(res["unmapped_tests"]))]
    lines += ["  uncovered %s" % r for r in res["uncovered"]]
    lines += ["  unmapped test %s" % f for f in res["unmapped_tests"]]
    return kl.emit(kl.envelope(TOOL, kl.EXIT_OK, result=res), args.json, human="\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
