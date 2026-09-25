#!/usr/bin/env python3
"""karvey-judges.py — the deterministic half of the judges (architecture §1.7, wave2-structural).

    karvey-judges.py inputs <change> <phase> [--extra ITEM…] [--base REF] [--root DIR] [--json]
    karvey-judges.py collect <change> <phase> --results DIR [--out FILE] [--root DIR] [--json]

``inputs`` prints the closed input list of a judge run: the phase's artifacts and the artifacts it reads, the
goal, the rubric and its lens sections; for ``qa`` also the change's diff (written to a temporary file). An extra
item is dropped and listed. It never starts a judge: the ``karvey-judges`` skill does, one clean-context
subagent per lens, with only these paths.

``collect`` filters what the judges returned (schema, citations, sanitiser, cost), appends the kept findings to
the change's ``findings.md`` and writes the run records for ``karvey-state.py judge-run``. It never routes a
finding, edits an artifact or writes ``spec.json``.

Exit: 0 ok · 2 usage · 3 refused · 4 not found · 5 internal. Python >= 3.9, stdlib only.
"""
import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import gitlog, judges as jd, project as pj  # noqa: E402

TOOL = "karvey-judges"


class Usage(Exception):
    pass


def _root(args):
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None:
        raise jd.JudgeError("not a Karvey project: %s" % (args.root or os.getcwd()))
    return root


def cmd_inputs(args):
    root = _root(args)
    diff_path = None
    if args.phase == "qa" and args.base:
        try:
            out = gitlog.run(["diff", "%s...HEAD" % gitlog.check_ref(args.base)], root)
        except gitlog.GitLogError as exc:
            raise jd.JudgeError("cannot read the diff: %s" % exc)
        fd, diff_path = tempfile.mkstemp(prefix="karvey-judge-%s-" % args.change, suffix=".diff")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(out)
    res = jd.build_inputs(root, args.change, args.phase, extras=args.extra or (), diff_path=diff_path)
    lines = ["%s %s (lane %s): %s" % (res["change"], res["phase"], res["lane"], res["status"])]
    for p in res["inputs"]:
        lines.append("  input  %s" % p)
    if res["rubric"]:
        lines.append("  rubric %s (lenses: %s)" % (res["rubric"], ", ".join(res["lenses"])))
    lines += ["  " + d for d in res["dropped"]] + ["  " + n for n in res["notes"]]
    return kl.EXIT_OK, res, "\n".join(lines)


def cmd_collect(args):
    root = _root(args)
    rdir = Path(args.results)
    if not rdir.is_dir():
        raise jd.JudgeError("--results %s is not a directory" % rdir)
    inp = jd.build_inputs(root, args.change, args.phase, diff_path=args.diff)
    allowed = list(inp["inputs"])
    chars_in = 0
    for p in allowed + ([inp["rubric"]] if inp["rubric"] else []):
        q = Path(p) if os.path.isabs(p) else Path(root) / p
        try:
            chars_in += q.stat().st_size
        except OSError:
            pass
    out_path = Path(args.out) if args.out else rdir / "runs.json"
    results = []
    for f in sorted(rdir.glob("*.json")):
        if f.resolve() == out_path.resolve():
            continue
        results.append((f.name, f.read_text(encoding="utf-8-sig", errors="replace")))
    at = datetime.now().astimezone().isoformat(timespec="seconds")
    runs, kept, lines = jd.collect(root, args.change, args.phase, results, allowed, model=args.model,
                                   intra_model=args.intra_model, at=at, chars_in=chars_in)
    ids = []
    if not args.dry_run:
        fpath = Path(root) / pj.CHANGES_DIR / args.change / "findings.md"
        ids = jd.append_findings(fpath, args.phase, kept, at[:10])
        out_path.write_text(json.dumps(runs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    discarded = sum(r.get("discarded", 0) for r in runs)
    lines.append("%d finding(s) appended to findings.md (%s) · %d discarded (no citation)%s" % (
        len(ids), ", ".join(ids) or "none", discarded, " · dry run" if args.dry_run else ""))
    lines += inp["notes"]
    lines.append("next: karvey-state.py judge-run %s %s --from %s" % (args.change, args.phase, out_path))
    res = {"change": args.change, "phase": args.phase, "runs": runs, "appended": ids, "discarded": discarded,
           "runs_file": str(out_path), "notes": inp["notes"]}
    return kl.EXIT_OK, res, "\n".join(lines)


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="Karvey project root (default: walk up from the cwd)")
    common.add_argument("--json", action="store_true", help="print one JSON envelope")
    p = argparse.ArgumentParser(prog="karvey-judges.py", description="Judges: closed inputs and output filter")
    sub = p.add_subparsers(dest="command")
    i = sub.add_parser("inputs", parents=[common], help="the closed input list of a judge run")
    i.add_argument("change")
    i.add_argument("phase")
    i.add_argument("--extra", action="append", help="an item a caller wants to add (it is dropped and listed)")
    i.add_argument("--base", help="qa: the ref the diff is taken from (base...HEAD)")
    c = sub.add_parser("collect", parents=[common], help="filter judge results, append findings, write run records")
    c.add_argument("change")
    c.add_argument("phase")
    c.add_argument("--results", required=True, help="directory with one JSON result per judge")
    c.add_argument("--out", help="run records for karvey-state.py judge-run (default: <results>/runs.json)")
    c.add_argument("--diff", help="qa: the diff file the judges read (from inputs)")
    c.add_argument("--model", help="the model the judges ran on, when a result does not say")
    c.add_argument("--intra-model", dest="intra_model", action="store_true",
                   help="the judges ran on the author's model family")
    c.add_argument("--dry-run", action="store_true", help="filter only; append and write nothing")
    return p


COMMANDS = {"inputs": cmd_inputs, "collect": cmd_collect}


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
    except Usage as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", str(exc))]), args.json)
    except jd.JudgeError as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("judges.not_found", str(exc))]),
                       args.json)
    except Exception as exc:  # pragma: no cover - last resort, exit 5
        return kl.emit(kl.envelope(TOOL, kl.EXIT_INTERNAL,
                                   errors=[kl.issue("internal", "%s: %s" % (type(exc).__name__, exc))]), args.json)
    return kl.emit(kl.envelope(TOOL, code, result=result), args.json, human=human)


if __name__ == "__main__":
    sys.exit(main())
