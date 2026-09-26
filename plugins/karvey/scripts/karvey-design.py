#!/usr/bin/env python3
"""karvey-design.py — a change's design delta against the project design system (architecture §1.18, C-18).

    karvey-design.py diff  <change> [--root DIR] [--json]
    karvey-design.py apply <change> [--dry-run] [--root DIR] [--json]

``diff`` (REQ-W3-036) compares the tokens and components of ``changes/{id}/design-spec.md`` with
``docs/spec/design-system.md`` and with the declared ``changes/{id}/design-delta.md``: it prints the delta (Added,
Modified with the base value, components, or ``empty``) and reports every modification or addition the delta does
not declare (``undeclared modification: --color-primary``) in the ``design.undeclared`` mode (warn in 4.1: exit 0;
blocking: exit 1). Without a design system every token is an addition: the delta seeds it at archive.

``apply`` (REQ-W3-076) runs at archive: added tokens and components are written with ``Changed by``; a modified
token whose design-system value is no longer the delta's base value stops (exit 3) naming the token, both values and
the change that last modified it; ``--keep=TOKEN=current|new`` records the human's answer; ``--dry-run`` writes
nothing. Exit: 0 · 1 findings (blocking) · 2 usage ·
3 conflict (apply) · 4 not found. Stdlib only.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import designsys as ds, modes, project as pj  # noqa: E402

TOOL = "karvey-design"
SYSTEM = pj.SPEC_DIR / "design-system.md"


class NotFound(Exception):
    pass


def _read(p, required=True):
    try:
        return Path(p).read_text(encoding="utf-8-sig")
    except OSError:
        if required:
            raise NotFound("not found: %s" % p)
        return None


def cmd_diff(args, root):
    cdir = Path(root) / pj.CHANGES_DIR / args.change
    if not (cdir / "spec.json").is_file():
        raise NotFound("change %r not found" % args.change)
    spec = ds.parse(_read(cdir / "design-spec.md"))
    st = _read(Path(root) / SYSTEM, required=False)
    system = ds.parse(st or "")
    delta_t = _read(cdir / "design-delta.md", required=False)
    delta = ds.parse_delta(delta_t or "")
    res = ds.diff(system, spec, delta)
    res.update(change=args.change, system=st is not None, delta_file=delta_t is not None,
               declared={"added": [r["token"] for r in delta["added"]],
                         "modified": [r["token"] for r in delta["modified"]],
                         "components": [c["name"] for c in delta["components"]]})
    mode = modes.resolve(root=root, check_id="design.undeclared")["mode"]
    res["mode"] = mode
    warns = [kl.issue("design.undeclared", u, severity="warning") for u in res["undeclared"]]
    if not res["delta_file"]:
        warns.append(kl.issue("design.no_delta", "%s has no design-delta.md (write it, `empty` when nothing "
                                                 "changes)" % args.change, severity="warning"))
    if res["undeclared"] and modes.would_refuse(mode):
        return kl.EXIT_FINDINGS, res, [kl.issue("design.undeclared", u) for u in res["undeclared"]], []
    return kl.EXIT_OK, res, [], warns


def render_diff(res):
    L = ["design delta — %s (%s)" % (res["change"], "design system present" if res["system"]
                                     else "no design system: the delta seeds it at archive")]
    if res["empty"]:
        L.append("empty")
    for a in res["added"]:
        L.append("added     %s  light %s · dark %s" % (a["token"], a["light"], a["dark"] or "= light"))
    for m in res["modified"]:
        L.append("modified  %s (%s)  base %s → new %s" % (m["token"], m["scheme"], m["base"], m["new"]))
    for c in res["components"]:
        L.append("component %s" % c)
    for u in res["undeclared"]:
        L.append("WARNING " + u if res["mode"] != "blocking" else "ERROR " + u)
    return "\n".join(L)


def cmd_apply(args, root):
    """``apply <change> [--dry-run] [--keep TOKEN=current|new]`` at archive (REQ-W3-076): the delta's added tokens
    and components are written to the design system with ``Changed by``; a modified token is written only when the
    system still holds the delta's base value — otherwise it stops (exit 3) with both values and the change that
    last modified it, and the archive skill asks the human which to keep (``--keep``). ``--dry-run`` writes
    nothing."""
    from karvey_lib import atomicio
    cdir = Path(root) / pj.CHANGES_DIR / args.change
    if not (cdir / "spec.json").is_file():
        raise NotFound("change %r not found" % args.change)
    delta = ds.parse_delta(_read(cdir / "design-delta.md"))
    keep = {}
    for k in args.keep or []:
        tok, _, choice = k.partition("=")
        if choice not in ("current", "new") or not tok.startswith("--"):
            return kl.EXIT_USAGE, None, [kl.issue("usage", "--keep TOKEN=current|new, got %r" % k)], []
        keep[tok] = choice
    spath = Path(root) / SYSTEM
    before = _read(spath, required=False)
    text, applied, conflicts = ds.apply_delta(before, delta, args.change, keep)
    changed = text != (before or "")
    res = {"change": args.change, "applied": applied, "conflicts": conflicts, "dry_run": bool(args.dry_run),
           "written": False, "file": SYSTEM.as_posix(), "empty": delta["empty"] or not applied and not conflicts}
    if changed and not args.dry_run:
        atomicio.write_text_atomic(str(spath), text, expected_sha256=atomicio.file_sha256(spath) if before else None)
        res["written"] = True
    if conflicts:
        return kl.EXIT_REFUSED, res, [kl.issue("design.conflict", "%s (%s): design system has %s, the delta's base "
                                               "was %s, new %s — last changed by %s" % (
                                                   c["token"], c["scheme"], c["current"], c["base"], c["new"],
                                                   c["last_change"] or "unknown")) for c in conflicts], []
    return kl.EXIT_OK, res, [], []


def render_apply(res):
    L = ["design apply — %s%s" % (res["change"], " (dry run: nothing written)" if res["dry_run"] else "")]
    L += ["  " + a for a in res["applied"]] or ["  nothing to apply"]
    for c in res["conflicts"]:
        L.append("  CONFLICT %s (%s): current %s · base %s · new %s · last changed by %s — ask the human which to "
                 "keep, then --keep=%s=current|new" % (c["token"], c["scheme"], c["current"], c["base"], c["new"],
                                                       c["last_change"] or "unknown", c["token"]))
    return "\n".join(L)


COMMANDS = {"diff": (cmd_diff, render_diff), "apply": (cmd_apply, render_apply)}


def build_parser():
    p = argparse.ArgumentParser(prog="karvey-design.py", description="design delta vs the project design system")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("diff", "apply"):
        s = sub.add_parser(name)
        s.add_argument("change")
        s.add_argument("--root")
        s.add_argument("--json", action="store_true")
        if name == "apply":
            s.add_argument("--dry-run", action="store_true")
            s.add_argument("--keep", action="append", metavar="TOKEN=current|new",
                           help="the human's answer for a conflicting token")
    return p


def main(argv=None):
    parser = build_parser()
    as_json = "--json" in (argv if argv is not None else sys.argv[1:])
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else kl.EXIT_USAGE
        if code != 0 and as_json:
            kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", "invalid arguments")]), True)
        return kl.EXIT_USAGE if code != 0 else 0
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("design.not_found",
                                                                             "no Karvey project here")]), args.json)
    fn, render = COMMANDS[args.cmd]
    try:
        code, res, errors, warns = fn(args, root)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("design.not_found", str(exc))]),
                       args.json)
    return kl.emit(kl.envelope(TOOL, code, result=res, errors=errors, warnings=warns), args.json,
                   human=render(res) if res else None)


if __name__ == "__main__":
    sys.exit(main())
