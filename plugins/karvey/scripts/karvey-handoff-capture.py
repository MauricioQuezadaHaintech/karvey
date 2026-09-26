#!/usr/bin/env python3
"""karvey-handoff-capture.py — write the handoff's ``state.json`` by measuring (architecture §1.5).

    karvey-handoff-capture.py --profile <dir> [--repos-from state|team|project]
                              [--scheduled-tasks N] [--ready-to-rotate] [--dry-run] [--json]

For each owned repository it runs ``git rev-parse --abbrev-ref HEAD``, ``git log -1 --pretty=%h``
and ``git status --porcelain`` and writes ``<profile>/state.json`` atomically::

    {"saved_at", "repos": [{"path", "branch", "commit", "uncommitted", "measured": true}
                           | {"path", "measured": false, "reason"}],
     "scheduled_tasks"?, "ready_to_rotate"?}

in the shape the session hook's live-state check reads (the 3.11.4 resolver: a ``path`` equal to
the root's name, ``.`` or empty is the root itself — BUG-20; worktrees are repositories — BUG-21).
A repository that cannot be measured is recorded as ``measured: false`` with the reason, never
with invented values (REQ-W1-048). ``karvey-checkpoint save`` runs this; state.json is never
written by hand.

Owned repositories (``--repos-from``, default: ``state`` when state.json lists repos, else ``team``
when a team.json names repos for this role, else ``project`` (project.json ``repos``), else the
root itself):
- ``state``   the paths already in ``<profile>/state.json``;
- ``team``    the repos whose ``team.json`` role is this profile's role (``…/agents/<role>``);
- ``project`` ``project.json:repos`` of the Karvey project that holds the profile.

Exit codes: 0 (some repos may be unmeasured, and are listed) · 2 usage · 4 profile dir missing.
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import karvey_lib as kl  # noqa: E402
from karvey_lib import atomicio, livestate, project as pj  # noqa: E402

TOOL = "karvey-handoff-capture"


def _load_json(path):
    try:
        return atomicio.read_json(path).data
    except atomicio.ReadError:
        return None


def repos_from_state(profile):
    d = _load_json(os.path.join(profile, "state.json"))
    if not isinstance(d, dict) or not isinstance(d.get("repos"), list):
        return None
    out = [r.get("path", "") for r in d["repos"] if isinstance(r, dict) and isinstance(r.get("path", ""), str)]
    return out or None


def repos_from_team(root, cfg, kind, profile):
    if kind != "team":
        return None
    d = _load_json(cfg)
    if not isinstance(d, dict) or not isinstance(d.get("roles"), dict):
        return None
    role = os.path.basename(os.path.normpath(profile))
    out = [repo for repo, r in d["roles"].items() if r == role and isinstance(repo, str)]
    return sorted(out) or None


def repos_from_project(root):
    kp = pj.find_root(start=root) if root else None
    if kp is None:
        return None
    data, _ = pj.load_project_json(kp)
    repos = data.get("repos") if isinstance(data, dict) else None
    if not isinstance(repos, list):
        return None
    return [r for r in repos if isinstance(r, str) and r.strip()] or None


def owned_repos(profile, root, cfg, kind, source):
    order = [source] if source else ["state", "team", "project"]
    for src in order:
        if src == "state":
            got = repos_from_state(profile)
        elif src == "team":
            got = repos_from_team(root, cfg, kind, profile)
        else:
            got = repos_from_project(root)
        if got:
            return got, src
    if source:
        return [], source
    return ["."], "root"


def locate(root, p):
    """``(path to record, directory to measure)``: the 3.11.4 resolver first; a sibling of the
    root second, recorded as ``../<p>`` so the session hook resolves it the same way."""
    rp = livestate.resolve(root, p)
    if livestate.is_repo(rp) or os.path.isabs(p) or p in ("", "."):
        return p, rp
    sib = os.path.join(os.path.dirname(os.path.normpath(root)), p)
    if livestate.is_repo(sib):
        return "../" + p.strip("/"), sib
    return p, rp


def capture(profile, source=None, scheduled=None, ready=False):
    root, cfg, kind = livestate.find_team_root(profile)
    if root is None:
        # a profile outside any team/solo layout: measure relative to the profile's project
        root = str(pj.find_root(start=profile) or profile)
    paths, used = owned_repos(profile, root, cfg, kind, source)
    repos = []
    for p in paths:
        rec_path, where = locate(root, p)
        m, why = livestate.measure(where)
        if m is None:
            repos.append({"path": rec_path, "measured": False, "reason": why})
        else:
            repos.append({"path": rec_path, "branch": m["branch"], "commit": m["commit"],
                          "uncommitted": m["uncommitted"], "measured": True})
    state = {"saved_at": datetime.now().astimezone().isoformat(timespec="seconds"), "repos": repos}
    if scheduled is not None:
        state["scheduled_tasks"] = scheduled
    if ready:
        state["ready_to_rotate"] = True
    return state, {"root": root, "kind": kind, "repos_from": used}


def _contains(repo_dir, path):
    top = livestate.git(repo_dir, "rev-parse", "--show-toplevel")[1]
    if not top:
        return False
    top, path = os.path.realpath(top), os.path.realpath(path)
    return path == top or path.startswith(top.rstrip(os.sep) + os.sep)


def write_state(target, state, profile, root):
    """Write state.json; when the profile lives inside a measured repo, writing it changes that
    repo's uncommitted count, so re-measure and write once more (the count is then stable: the
    session hook compares against the tree *with* state.json in it, as in 3.11.4)."""
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    atomicio.write_text_atomic(target, text, expected_sha256="*")
    changed = False
    for r in state["repos"]:
        if not r.get("measured"):
            continue
        _, where = locate(root, r["path"])
        if _contains(where, profile):
            m, _why = livestate.measure(where)
            if m is not None and m["uncommitted"] != r["uncommitted"]:
                r["uncommitted"] = m["uncommitted"]
                changed = True
    if changed:
        atomicio.write_text_atomic(target, json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                                   expected_sha256="*")


def main(argv=None):
    ap = argparse.ArgumentParser(prog=TOOL, description="Write the handoff state.json by measuring the repos.")
    ap.add_argument("--profile", required=True, help="the agent profile directory (holds handoff.md)")
    ap.add_argument("--repos-from", choices=("state", "team", "project"))
    ap.add_argument("--scheduled-tasks", type=int, metavar="N")
    ap.add_argument("--ready-to-rotate", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the state without writing it")
    ap.add_argument("--json", action="store_true", help="print the --json envelope")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return kl.EXIT_USAGE if exc.code else kl.EXIT_OK
    if args.scheduled_tasks is not None and args.scheduled_tasks < 0:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("capture.usage",
                                                                         "--scheduled-tasks must be >= 0")]), args.json)
    profile = os.path.realpath(os.path.expanduser(args.profile))
    if not os.path.isdir(profile):
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue(
            "capture.profile", "profile directory not found: %s (run karvey-checkpoint save to create it)" % profile,
            file=profile)]), args.json)
    state, info = capture(profile, args.repos_from, args.scheduled_tasks, args.ready_to_rotate)
    target = os.path.join(profile, "state.json")
    if not args.dry_run:
        write_state(target, state, profile, info["root"])
    unmeasured = [r for r in state["repos"] if not r["measured"]]
    warnings = [kl.issue("capture.unmeasured", "%s not measured: %s" % (r["path"], r["reason"]), severity="warning")
                for r in unmeasured]
    result = dict(info, state=state, file=target, written=not args.dry_run)
    lines = ["%s %s (%d repos, from %s)" % ("would write" if args.dry_run else "wrote", target, len(state["repos"]),
                                            info["repos_from"])]
    for r in state["repos"]:
        lines.append("  %s: %s" % (r["path"], "%s @%s, %d uncommitted" % (r["branch"], r["commit"], r["uncommitted"])
                                   if r["measured"] else "NOT MEASURED (%s)" % r["reason"]))
    if args.dry_run and not args.json:
        lines.append(json.dumps(state, indent=2, ensure_ascii=False))
    return kl.emit(kl.envelope(TOOL, kl.EXIT_OK, result=result, warnings=warnings), args.json, human="\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
