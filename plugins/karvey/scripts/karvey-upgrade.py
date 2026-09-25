#!/usr/bin/env python3
"""karvey-upgrade.py — the project-upgrade tool (architecture §1.5 of the project-upgrade change).

After a plugin update, computes from the project's state which upgrade steps apply, previews them, and
applies only the picked ones on an upgrade branch, as one commit. Every write goes through
``karvey_lib/upgrade.py`` (the single writer). Python >= 3.9, standard library only.

Shared CLI contract: ``--root DIR`` (else walk up from the cwd to the git top level), ``--json`` (one
envelope on stdout), exit codes 0 ok · 1 findings · 2 usage · 3 refused · 4 not found / unreadable /
corrupt · 5 internal. Outside a Karvey project every command refuses (exit 3) and writes nothing.

Commands:
  plan                                   the table (step · what changes · dry-run · risk · needs human);
                                         writes nothing; exit 1 when a check failed
  branch                                 create / switch to chore/karvey-upgrade-<installed> (never fetches)
  apply --steps a,b [--dry-run] [--preview ID] [--confirm-no-preview ID…] [--values FILE]
                                         the picked steps, in catalogue order; --dry-run prints the diffs and
                                         the preview id that apply then requires
  commit --picked-by NAME [--picked-at ISO] [--answer TEXT] [--trailer K=V…]
                                         one commit of exactly the files the upgrade wrote; prints the PR text
  seen --decline | --accept | --empty | --show
                                         resolve (or show) the once-per-version offer of this clone
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import atomicio, upgrade  # noqa: E402
from karvey_lib import project as pj  # noqa: E402

TOOL = "karvey-upgrade"


class Usage(Exception):
    pass


class NotFound(Exception):
    pass


def resolve_root(args):
    root = pj.find_root(start=os.getcwd(), root=getattr(args, "root", None))
    if root is None:
        where = args.root if getattr(args, "root", None) else os.getcwd()
        raise upgrade.Refused("not a Karvey project (no docs/spec/project.json or docs/spec/changes/): %s — "
                              "nothing written" % where)
    return root


def _split(items):
    out = []
    for item in items or []:
        out += [x.strip() for x in str(item).split(",") if x.strip()]
    return out


def read_values(path):
    """``--values FILE``: JSON ``{step_id: {key: value}}``; values are strings, numbers, booleans or lists of
    strings. Each value is checked by its step through safe_values (REQ-UP-019)."""
    if not path:
        return {}
    try:
        data = atomicio.read_json(path).data
    except atomicio.ReadError as exc:
        raise NotFound("--values: %s" % exc)
    if not isinstance(data, dict):
        raise Usage("--values: expected a JSON object {step_id: {key: value}}")
    for sid, vals in data.items():
        if not isinstance(vals, dict):
            raise Usage("--values: %s must map keys to values" % sid)
        for k, v in vals.items():
            ok = isinstance(v, (str, int, float, bool)) or (isinstance(v, list) and all(isinstance(x, str) for x in v))
            if not isinstance(k, str) or not ok:
                raise Usage("--values: %s.%s must be a string, number, boolean or a list of strings" % (sid, k))
    return data


# --------------------------------------------------------------------------- commands
def cmd_plan(args, root):
    p = upgrade.plan(root)
    return p.exit, p.as_json(), [], [], p.table()


def cmd_branch(args, root):
    res = upgrade.ensure_branch(root)
    if res["created"]:
        human = "created %s from %s and switched to it" % (res["branch"], res["base"])
    elif res["switched"]:
        human = "switched to the existing %s" % res["branch"]
    else:
        human = "already on %s" % res["branch"]
    return kl.EXIT_OK, res, [], [], human


def cmd_apply(args, root):
    ids = _split(args.steps)
    if not ids:
        raise Usage("apply needs --steps a,b")
    rep = upgrade.apply(root, ids, dry_run=args.dry_run, preview=args.preview, inputs=read_values(args.values),
                        confirm_no_preview=_split(args.confirm_no_preview))
    errors = [kl.issue("upgrade.step_failed", "%s: %s" % (k, v)) for k, v in rep.failed.items()]
    return rep.exit, rep.as_json(), errors, [], rep.text()


def cmd_commit(args, root):
    res = upgrade.commit(root, args.picked_by, picked_at=args.picked_at, answer=args.answer,
                         trailers=args.trailer)
    human = "committed %s on %s (%s)\n\nPR title: %s\n\n%s" % (res["sha"][:12], res["branch"], ", ".join(res["files"]),
                                                             res["pr_title"], res["pr_body"])
    return kl.EXIT_OK, res, [], [], human


def cmd_seen(args, root):
    if args.show:
        rec = upgrade.read_seen(root)
        human = ("no upgrade resolved yet in this clone" if rec is None else
                 "%s %s (at %s, by %s)" % (rec["resolution"], rec["version"], rec.get("at"), rec.get("by") or "?"))
        return kl.EXIT_OK, {"record": rec, "installed": upgrade.INSTALLED}, [], [], human
    resolution = "declined" if args.decline else "accepted" if args.accept else "empty"
    try:
        rec = upgrade.write_seen(root, upgrade.INSTALLED, resolution)
    except upgrade.SeenWriteError as exc:
        raise upgrade.Refused(str(exc))
    return kl.EXIT_OK, {"record": rec}, [], [], "recorded: %s %s" % (resolution, rec["version"])


COMMANDS = {"plan": cmd_plan, "branch": cmd_branch, "apply": cmd_apply, "commit": cmd_commit, "seen": cmd_seen}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        sys.exit(kl.EXIT_USAGE)


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="the Karvey project root (default: walk up from the cwd)")
    common.add_argument("--json", action="store_true", help="print one JSON envelope")
    p = _Parser(prog="karvey-upgrade.py", description="Karvey project upgrade: plan, preview, apply, commit.")
    sub = p.add_subparsers(dest="command", parser_class=_Parser)
    sub.add_parser("plan", parents=[common], help="the upgrade plan (writes nothing)")
    sub.add_parser("branch", parents=[common], help="create / switch to the upgrade branch")
    a = sub.add_parser("apply", parents=[common], help="apply the picked steps")
    a.add_argument("--steps", action="append", default=[], help="comma list of step ids")
    a.add_argument("--dry-run", action="store_true", help="print the diffs and the preview id; write nothing")
    a.add_argument("--preview", help="the preview id printed by --dry-run")
    a.add_argument("--confirm-no-preview", action="append", default=[], metavar="ID",
                   help="a step without a preview the person confirmed (repeatable, comma list)")
    a.add_argument("--values", help="JSON file {step_id: {key: value}} (keep it outside the repository)")
    c = sub.add_parser("commit", parents=[common], help="commit the files the upgrade wrote")
    c.add_argument("--picked-by", required=True, help="the person who picked the steps")
    c.add_argument("--picked-at", help="when they picked (ISO 8601; default now)")
    c.add_argument("--answer", help="their words (up to 200 characters)")
    c.add_argument("--trailer", action="append", default=[], metavar="KEY=VALUE", help="a commit trailer")
    s = sub.add_parser("seen", parents=[common], help="resolve or show the offer of this clone")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--decline", action="store_true", help="'Not for this version'")
    g.add_argument("--accept", action="store_true", help="the person picked at least one step")
    g.add_argument("--empty", action="store_true", help="the plan was empty")
    g.add_argument("--show", action="store_true", help="print the record")
    return p


def main(argv=None):
    parser = build_parser()
    raw = argv if argv is not None else sys.argv[1:]
    as_json = "--json" in raw
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
        root = resolve_root(args)
        code, result, errors, warnings, human = COMMANDS[args.command](args, root)
    except Usage as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", str(exc))]), args.json)
    except upgrade.Refused as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, errors=[kl.issue("upgrade.refused", str(exc))]), args.json)
    except (NotFound, upgrade.CatalogueError) as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("upgrade.not_found", str(exc))]),
                       args.json)
    except (atomicio.LockBusy, atomicio.CASConflict) as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, errors=[kl.issue("upgrade.concurrent", str(exc))]),
                       args.json)
    except Exception as exc:  # pragma: no cover - last resort, exit 5
        return kl.emit(kl.envelope(TOOL, kl.EXIT_INTERNAL,
                                   errors=[kl.issue("internal", "%s: %s" % (type(exc).__name__, exc))]), args.json)
    return kl.emit(kl.envelope(TOOL, code, result=result, errors=errors, warnings=warnings), args.json, human=human)


if __name__ == "__main__":
    sys.exit(main())
