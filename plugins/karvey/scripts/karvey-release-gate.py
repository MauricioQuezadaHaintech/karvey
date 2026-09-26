#!/usr/bin/env python3
"""karvey-release-gate.py — the release manifest and the release gate (architecture §1.9, wave2-structural).

    karvey-release-gate.py manifest [--base REF] [--head REF] [--root DIR] [--json]

``manifest`` maps every commit of ``base..head`` (default ``origin/{production}..HEAD``) to its change through
the ``Karvey-Change`` trailer (merge commits through their parents, spec bookkeeping by path) and lists each
change with its version (the CHANGELOG block that names it), lane and QA state, plus the unmapped commits.
Verdict: ``pass`` when nothing is unmapped and every change has QA approved or skipped by its lane; otherwise
``warn`` (mode ``warn``, 3.13) or ``fail`` (mode ``blocking``, 4.0). A non-pass verdict appends one
``checks.jsonl`` hit per active change of the manifest (``--no-record`` writes nothing). Git is read only.

Exit: 0 pass or warn · 1 fail · 2 usage · 4 not found (no project, git cannot answer) · 5 internal.
Python >= 3.9, stdlib only.
"""
import argparse
import os
import sys

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


COMMANDS = {"manifest": cmd_manifest}


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
