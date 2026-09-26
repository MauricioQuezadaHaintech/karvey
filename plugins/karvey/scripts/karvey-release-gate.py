#!/usr/bin/env python3
"""karvey-release-gate.py — the release manifest and the release gate (architecture §1.9, wave2-structural).

    karvey-release-gate.py manifest [--base REF] [--head REF] [--root DIR] [--json]
    karvey-release-gate.py check <change> [--pr-body FILE] [--base REF] [--head REF] [--root DIR] [--json]
    karvey-release-gate.py release-branch [--version X.Y.Z] [--base REF] [--head REF] [--root DIR] [--json]

``manifest`` maps every commit of ``base..head`` (default ``origin/{production}..HEAD``) to its change through
the ``Karvey-Change`` trailer (merge commits through their parents, spec bookkeeping by path) and lists each
change with its version (the CHANGELOG block that names it), lane and QA state, plus the unmapped commits.
Verdict: ``pass`` when nothing is unmapped and every change has QA approved or skipped by its lane; otherwise
``warn`` (mode ``warn``, 3.13) or ``fail`` (mode ``blocking``, 4.0). A non-pass verdict appends one
``checks.jsonl`` hit per active change of the manifest (``--no-record`` writes nothing). Git is read only.

``check`` is the deploy pre-check (REQ-W2-069): items ``qa_gate``, ``tests``, ``changelog``, ``version_match``,
``lane_triplet``, ``manifest``, ``spec_merged`` and ``pr_body``, each ``pass`` · ``warn`` (a failing check whose
mode is ``warn``, 3.13) · ``fail`` · ``not-applicable`` with its detail; the verdict is ``fail`` when any item
fails, else ``warn`` when any warns, else ``pass``. It writes nothing. ``release-branch`` is the read-only plan of
a ``release/{version}`` branch from production holding only the approved changes' commits, oldest first
(REQ-W2-050): it prints the commands and runs none.

Exit: 0 pass or warn · 1 fail · 2 usage · 4 not found (no project, git cannot answer) · 5 internal.
Python >= 3.9, stdlib only.
"""
import argparse
import importlib.util
import json
import re
import subprocess
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import manifest as mf, modes, project as pj  # noqa: E402

TOOL = "karvey-release-gate"


class NotFound(Exception):
    pass


def _root(args):
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None:
        raise NotFound("not a Karvey project (no docs/spec): %s" % (args.root or os.getcwd()))
    return root


def default_base(root):
    project, _ = pj.load_project_json(root)
    _, _, production = pj.branch_flow(project or {})
    return "origin/%s" % (production or "main")


def record_hits(root, man):
    """One ``release.manifest`` hit per change of the manifest that has an active folder."""
    detail = "; ".join(mf.problems_of(man))
    out = []
    for c in man["changes"]:
        if (root / pj.CHANGES_DIR / c["id"]).is_dir():
            modes.record_hit(root, c["id"], "release.manifest", detail, mode=man["mode"])
            out.append(c["id"])
    return out


def cmd_manifest(args):
    root = _root(args)
    base = args.base or default_base(root)
    mode = modes.resolve(root, "release.manifest")["mode"]
    try:
        man = mf.release_manifest(root, base, args.head, mode=mode)
    except mf.ManifestError as exc:
        raise NotFound("manifest not computable: %s" % exc)
    man["recorded"] = [] if man["verdict"] == "pass" or args.no_record else record_hits(root, man)
    lines = ["manifest %s..%s (mode %s): %s" % (base, args.head, mode, man["verdict"].upper())]
    for c in man["changes"]:
        lines.append("  %-28s version %-11s lane %-10s QA %-12s %d commit(s)" % (
            c["id"], c["version"] or "?", c["lane"] or "?", c["qa"], len(c["commits"])))
    for u in man["unmapped"]:
        lines.append("  unmapped %s %s — %s" % (u["sha"][:10], u["subject"][:60], u["reason"]))
    code = kl.EXIT_FINDINGS if man["verdict"] == "fail" else kl.EXIT_OK
    return code, man, "\n".join(lines)


# --------------------------------------------------------------------------- check (REQ-W2-069)
ITEMS = ("qa_gate", "tests", "changelog", "version_match", "lane_triplet", "manifest", "spec_merged", "pr_body")
_SCRIPTS = Path(os.path.dirname(os.path.abspath(__file__)))
_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def _ids(values, cap=10):
    values = list(values)
    more = len(values) - cap
    return ", ".join(values[:cap]) + (" (+%d more)" % more if more > 0 else "")


def _item(status, detail):
    return {"status": status, "detail": detail}


def _trace_module():
    spec = importlib.util.spec_from_file_location("karvey_trace", str(_SCRIPTS / "karvey-trace.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def item_qa(spec_data):
    state = mf.qa_state(spec_data)
    return _item("pass" if state in ("approved", "lane-skipped") else "fail", "QA %s" % state)


def item_tests(root, change, base):
    """Coverage (``coverage.requirements`` mode) plus the latest ``evidence.jsonl`` run of the change."""
    tr = _trace_module()
    cdir = Path(root) / pj.CHANGES_DIR / change
    recs = tr.evidence_records(cdir)
    if not recs:
        return _item("fail", "not evaluated: no run in %s/evidence.jsonl (run the suite through karvey-evidence.py)"
                     % change)
    last = recs[-1]
    run = "latest run %r exit %s (evidence.jsonl:%d)" % (last.get("label") or " ".join(last.get("argv") or [])[:60],
                                                         last.get("exit"), len(recs))
    if last.get("exit") != 0:
        return _item("fail", run)
    try:
        res = tr.build(root, change, base)
    except tr.NotFound as exc:
        return _item("fail", str(exc))
    mode = modes.resolve(root, "coverage.requirements")["mode"]
    n, missing = len(res["requirements"]), res["not_green"]
    cov = "coverage %d/%d" % (n - len(missing), n)
    if missing and mode == "blocking":
        return _item("fail", "%s; %s; not green: %s" % (run, cov, _ids(missing)))
    if missing and mode != "off":
        return _item("warn", "%s; %s (mode %s); not green: %s" % (run, cov, mode, _ids(missing)))
    return _item("pass", "%s; %s" % (run, cov))


def item_changelog(root, change):
    v = mf.changelog_version(root, change)
    if v is None:
        return _item("fail", "CHANGELOG.md names %s in no block ([Unreleased] or a release)" % change)
    return _item("pass", "CHANGELOG.md [%s] names %s" % (v, change))


def _json_version(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    v = data.get("version") if isinstance(data, dict) else None
    return str(v) if isinstance(v, (str, int, float)) and str(v) else None


def version_sources(root):
    """``{source: version}``: plugin manifests, package.json, pyproject.toml, VERSION and the top numbered
    CHANGELOG release — the comparison L-12 makes for the plugin, for any project."""
    root = Path(root)
    out = {}
    for p in sorted(list(root.glob(".claude-plugin/plugin.json")) + list(root.glob("plugins/*/.claude-plugin/plugin.json"))):
        v = _json_version(p)
        if v:
            out[str(p.relative_to(root)).replace(os.sep, "/")] = v
    v = _json_version(root / "package.json")
    if v:
        out["package.json"] = v
    try:
        m = re.search(r'^\[project\][^\[]*?^version\s*=\s*"([^"]+)"', (root / "pyproject.toml").read_text(
            encoding="utf-8-sig"), re.M | re.S)
        if m:
            out["pyproject.toml"] = m.group(1)
    except OSError:
        pass
    try:
        v = (root / "VERSION").read_text(encoding="utf-8-sig").strip()
        if _VERSION.match(v):
            out["VERSION"] = v
    except OSError:
        pass
    try:
        for line in (root / "CHANGELOG.md").read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"^## \[(\d+\.\d+\.\d+[^\]]*)\]", line)
            if m:
                out["CHANGELOG.md"] = m.group(1)
                break
    except OSError:
        pass
    return out


def item_version(root):
    src = version_sources(root)
    if len(src) < 2:
        return _item("not-applicable", "fewer than two version sources (%s)" % (", ".join(src) or "none"))
    if len(set(src.values())) == 1:
        return _item("pass", "%s everywhere (%s)" % (next(iter(src.values())), ", ".join(src)))
    return _item("fail", "versions disagree: %s" % ", ".join("%s %s" % kv for kv in sorted(src.items())))


def item_lane_triplet(root, spec_data):
    lane = spec_data.get("lane") if isinstance(spec_data, dict) else None
    if lane not in ("patch", "hotfix"):
        return _item("not-applicable", "lane %s" % (lane or "unknown"))
    ev = spec_data.get("lane_evidence") if isinstance(spec_data.get("lane_evidence"), dict) else {}
    missing = [n for k, n in (("bug_id", "BUG-NN"), ("finding", "finding"), ("regression_test", "regression test"))
               if not (isinstance(ev.get(k), str) and ev[k].strip())]
    if missing:
        return _item("fail", "lane %s without %s (lane-evidence)" % (lane, ", ".join(missing)))
    path = ev["regression_test"].split("::", 1)[0]
    if not (Path(root) / path).is_file():
        return _item("fail", "regression test file %s does not exist" % path)
    return _item("pass", "%s · %s · %s" % (ev["bug_id"], ev["finding"], ev["regression_test"]))


def item_manifest(root, change, base, head):
    mode = modes.resolve(root, "release.manifest")["mode"]
    try:
        man = mf.release_manifest(root, base, head, mode=mode)
    except mf.ManifestError as exc:
        return _item("fail" if mode == "blocking" else "warn", "not evaluated (%s)" % exc), None
    ids = [c["id"] for c in man["changes"]]
    if change not in ids:
        return _item("fail", "%s has no commit in %s..%s" % (change, base, head)), man
    if man["verdict"] == "pass":
        return _item("pass", "%d change(s): %s" % (len(ids), ", ".join(ids))), man
    return _item("fail" if man["verdict"] == "fail" else "warn",
                 "mode %s: %s" % (mode, _ids(mf.problems_of(man), 5).replace(", ", "; "))), man


def item_spec_merged(root, change):
    cdir = Path(root) / pj.CHANGES_DIR / change
    if not (cdir / "spec-delta.md").is_file():
        return _item("not-applicable", "no spec-delta.md")
    proc = subprocess.run([sys.executable, str(_SCRIPTS / "karvey-spec-merge.py"), change, "--check", "--json",
                           "--root", str(root)], capture_output=True, text=True, timeout=60)
    try:
        env = json.loads(proc.stdout)
    except ValueError:
        return _item("fail", "spec-merge --check gave no answer (exit %d)" % proc.returncode)
    res = env.get("result") or {}
    status = res.get("status")
    if status == "merged":
        return _item("pass", "merged into %s" % res.get("target"))
    if status in ("unmerged", "conflict"):
        ids = (res.get("conflict_ids") if status == "conflict" else res.get("pending")) or []
        return _item("fail", "%s in %s: %s" % (status, res.get("target"), _ids(ids)))
    msg = "; ".join(e.get("message", "") for e in env.get("errors") or [])
    return _item("fail", "spec-merge --check: %s" % (msg or "exit %d" % proc.returncode))


def item_pr_body(path, man):
    if not path:
        return _item("not-applicable", "no --pr-body given")
    try:
        body = Path(path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        return _item("fail", "PR body unreadable: %s" % exc)
    if man is None:
        return _item("fail", "manifest not computable: the PR body cannot be compared")
    missing = []
    for c in man["changes"]:
        if not re.search(r"(?<![a-z0-9-])%s(?![a-z0-9-])" % re.escape(c["id"]), body):
            missing.append(c["id"])
        elif c.get("version") and _VERSION.match(c["version"]) and c["version"] not in body:
            missing.append("%s version %s" % (c["id"], c["version"]))
    if missing:
        return _item("fail", "the PR body does not list: %s" % ", ".join(missing))
    return _item("pass", "lists %d change(s)" % len(man["changes"]))


def cmd_check(args):
    root = _root(args)
    path, spec_data = mf.change_spec(root, args.change)
    if path is None or not isinstance(spec_data, dict):
        raise NotFound("change %r not found or unreadable" % args.change)
    base = args.base or default_base(root)
    items = {"qa_gate": item_qa(spec_data), "tests": item_tests(root, args.change, base),
             "changelog": item_changelog(root, args.change), "version_match": item_version(root),
             "lane_triplet": item_lane_triplet(root, spec_data)}
    items["manifest"], man = item_manifest(root, args.change, base, args.head)
    items["spec_merged"] = item_spec_merged(root, args.change)
    items["pr_body"] = item_pr_body(args.pr_body, man)
    statuses = [items[k]["status"] for k in ITEMS]
    verdict = "fail" if "fail" in statuses else ("warn" if "warn" in statuses else "pass")
    res = {"change": args.change, "base": base, "head": args.head, "verdict": verdict,
           "items": {k: items[k] for k in ITEMS},
           "failed": [k for k in ITEMS if items[k]["status"] == "fail"]}
    lines = ["release gate %s (%s..%s): verdict: %s" % (args.change, base, args.head, verdict)]
    lines += ["  %-14s %-15s %s" % (k, items[k]["status"], items[k]["detail"]) for k in ITEMS]
    return (kl.EXIT_FINDINGS if verdict == "fail" else kl.EXIT_OK), res, "\n".join(lines)


# --------------------------------------------------------------------------- release-branch (REQ-W2-050)
def cmd_release_branch(args):
    root = _root(args)
    base = args.base or default_base(root)
    mode = modes.resolve(root, "release.manifest")["mode"]
    try:
        m = mf.map_commits(root, base, args.head)
        man = mf.release_manifest(root, base, args.head, mode=mode)
    except mf.ManifestError as exc:
        raise NotFound("manifest not computable: %s" % exc)
    approved = {c["id"] for c in man["changes"] if c["qa"] in ("approved", "lane-skipped")}
    picks = [{"sha": r["sha"], "subject": r["subject"], "change": r["change"]} for r in m["commits"]
             if r["change"] in approved and r["mapped_by"] != "merge"]
    excluded = [{"id": c["id"], "qa": c["qa"]} for c in man["changes"] if c["id"] not in approved]
    version = args.version or "{version}"
    branch = "release/%s" % version
    commands = ["git switch -c %s %s" % (branch, base)] + ["git cherry-pick -x %s" % p["sha"] for p in picks]
    res = {"base": base, "head": args.head, "branch": branch, "commits": picks, "excluded": excluded,
           "unmapped": man["unmapped"], "commands": commands, "executed": False}
    lines = ["release branch plan (read-only, nothing run): %s from %s" % (branch, base)]
    lines += ["  pick %s %s [%s]" % (p["sha"][:10], p["subject"][:60], p["change"]) for p in picks]
    lines += ["  leave out %s (QA %s)" % (e["id"], e["qa"]) for e in excluded]
    lines += ["  leave out unmapped %s — %s" % (u["sha"][:10], u["reason"]) for u in man["unmapped"]]
    lines.append("on a cherry-pick conflict: stop, report the commit, git cherry-pick --abort — never resolve it")
    return kl.EXIT_OK, res, "\n".join(lines)


COMMANDS = {"manifest": cmd_manifest, "check": cmd_check, "release-branch": cmd_release_branch}


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="Karvey project root (default: walk up from the cwd)")
    common.add_argument("--json", action="store_true", help="print one JSON envelope")
    p = argparse.ArgumentParser(prog="karvey-release-gate.py", description="Release manifest and release gate")
    sub = p.add_subparsers(dest="command")
    m = sub.add_parser("manifest", parents=[common], help="commits of base..head mapped to their changes")
    m.add_argument("--base", help="default: origin/{branch_flow.production}")
    m.add_argument("--head", default="HEAD")
    m.add_argument("--no-record", action="store_true", help="write no checks.jsonl hit")
    c = sub.add_parser("check", parents=[common], help="the deploy pre-check of one change (read-only)")
    c.add_argument("change")
    c.add_argument("--pr-body", help="a file with the production PR body")
    c.add_argument("--base", help="default: origin/{branch_flow.production}")
    c.add_argument("--head", default="HEAD")
    r = sub.add_parser("release-branch", parents=[common], help="read-only plan of a release/* branch")
    r.add_argument("--version", help="the release version (branch release/{version})")
    r.add_argument("--base", help="default: origin/{branch_flow.production}")
    r.add_argument("--head", default="HEAD")
    return p


def main(argv=None):
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else kl.EXIT_USAGE
        if code != 0 and as_json:
            kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", "invalid arguments")]), True)
        return kl.EXIT_USAGE if code != 0 else 0
    if not args.command:
        parser.print_help(sys.stderr)
        return kl.EXIT_USAGE
    try:
        code, result, human = COMMANDS[args.command](args)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("release.not_found", str(exc))]),
                       args.json)
    except Exception as exc:  # pragma: no cover - last resort, exit 5
        return kl.emit(kl.envelope(TOOL, kl.EXIT_INTERNAL,
                                   errors=[kl.issue("internal", "%s: %s" % (type(exc).__name__, exc))]), args.json)
    return kl.emit(kl.envelope(TOOL, code, result=result), args.json, human=human)


if __name__ == "__main__":
    sys.exit(main())
