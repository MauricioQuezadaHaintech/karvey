"""Live repository state: the one resolver shared by the session hook and the handoff capture.

Ported from the 3.11.4 ``karvey-session-context.sh`` (BUG-20, BUG-21), not rewritten:

- ``resolve(root, p)``: ``''``, ``.`` or the root's own name mean the root itself (a ``team.json``
  inside the repo it names — BUG-20); an absolute path is itself; anything else is relative to
  the root. The first candidate that is a repository wins, else the last one is returned.
- ``is_repo(path)``: a directory where ``git rev-parse --git-dir`` answers — a worktree has a
  ``.git`` *file*, so looking for a ``.git/`` directory reports it as missing (BUG-21, F-01).
- ``measure(path)``: branch (``rev-parse --abbrev-ref HEAD``), commit (``log -1 --pretty=%h``)
  and the uncommitted count (``status --porcelain``), or ``None`` with the reason.

Every subprocess call is an argv list (§3.1 rule 1).
"""
import os
import subprocess

GIT_TIMEOUT_S = 10


def find_team_root(start):
    """``(root, cfg, kind)`` walking up from ``start``: ``docs/spec/team.json`` (team),
    ``.ceo-agentes`` (legacy) or ``docs/spec/agent/`` (solo); ``(None, None, None)`` if none."""
    d = os.path.realpath(str(start))
    while True:
        if os.path.isfile(os.path.join(d, "docs", "spec", "team.json")):
            return d, os.path.join(d, "docs", "spec", "team.json"), "team"
        if os.path.isfile(os.path.join(d, ".ceo-agentes")):
            return d, os.path.join(d, ".ceo-agentes"), "legacy"
        if os.path.isdir(os.path.join(d, "docs", "spec", "agent")):
            return d, os.path.join(d, "docs", "spec", "agent"), "solo"
        parent = os.path.dirname(d)
        if parent == d:
            return None, None, None
        d = parent


def git(repo, *args, timeout=GIT_TIMEOUT_S):
    """``(returncode, stdout)`` of ``git -C <repo> <args>``; never raises."""
    try:
        cp = subprocess.run(["git", "-C", str(repo)] + list(args), stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, timeout=timeout)
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired:
        return 124, ""
    except OSError:
        return 126, ""
    return cp.returncode, cp.stdout.decode("utf-8", "replace").strip()


def is_repo(path):
    return os.path.isdir(str(path)) and git(path, "rev-parse", "--git-dir")[0] == 0


def resolve(root, p):
    root = str(root)
    p = p if isinstance(p, str) else ""
    if p in ("", ".") or p.rstrip("/") == os.path.basename(root.rstrip("/")):
        cands = [root] + ([os.path.join(root, p)] if p not in ("", ".") else [])
    else:
        cands = [p] if os.path.isabs(p) else [os.path.join(root, p)]
    for c in cands:
        if is_repo(c):
            return c
    return cands[-1]


def measure(path):
    """``({branch, commit, uncommitted}, None)`` or ``(None, reason)``."""
    if not os.path.isdir(str(path)):
        return None, "directory not found: %s" % path
    rc, _ = git(path, "rev-parse", "--git-dir")
    if rc != 0:
        return None, "not a git repository: %s" % path
    rc, branch = git(path, "rev-parse", "--abbrev-ref", "HEAD")
    if rc != 0 or not branch:
        return None, "git rev-parse --abbrev-ref HEAD failed (rc %d)" % rc
    rc, commit = git(path, "log", "-1", "--pretty=%h")
    if rc != 0 or not commit:
        return None, "git log -1 failed (rc %d; a repository without commits?)" % rc
    rc, status = git(path, "status", "--porcelain")
    if rc != 0:
        return None, "git status --porcelain failed (rc %d)" % rc
    return {"branch": branch, "commit": commit,
            "uncommitted": len([x for x in status.splitlines() if x])}, None
