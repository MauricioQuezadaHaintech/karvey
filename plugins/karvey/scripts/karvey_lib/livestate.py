"""Live repository state: the one resolver shared by the session hook and the handoff capture.

Ported from the 3.11.4 ``karvey-session-context.sh`` (BUG-20, BUG-21), not rewritten:

- ``resolve(root, p)``: ``''``, ``.`` or the root's own name mean the root itself (a ``team.json``
  inside the repo it names — BUG-20); an absolute path is itself; anything else is relative to
  the root. The first candidate that is a repository wins, else the last one is returned.
- ``is_repo(path)``: a directory where ``git rev-parse --git-dir`` answers — a worktree has a
  ``.git`` *file*, so looking for a ``.git/`` directory reports it as missing (BUG-21, F-01).
- ``measure(path)``: branch (``rev-parse --abbrev-ref HEAD``), commit (``log -1 --pretty=%h``)
  and the uncommitted count (``status --porcelain``), or ``None`` with the reason.
- ``profile_only_since(path, recorded, profile_dir)``: the commits since the save touch only the
  profile's own files (BUG-22); the degraded bash path in ``karvey-session-context.sh`` agrees.

Every subprocess call is an argv list (§3.1 rule 1).
"""
import json
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


# The profile's own files (architecture §1.4 revision 1, BUG-22): committing them after the capture
# is the save finishing, not the tree moving on.
PROFILE_FILES = ("state.json", "handoff.md", "board.md", "manifest.md", "checklist.md")


def profile_only_since(path, recorded, profile_dir):
    """True when ``recorded`` is an ancestor of HEAD and every path touched by
    ``git log <recorded>..HEAD`` is one of the profile's own files, as paths relative to the
    repository top level (BUG-22). Anything unknown is False: the caller then reports DRIFT."""
    if not isinstance(recorded, str) or not recorded or recorded.startswith("-") or not profile_dir:
        return False
    if git(path, "merge-base", "--is-ancestor", recorded, "HEAD")[0] != 0:
        return False
    rc, top = git(path, "rev-parse", "--show-toplevel")
    if rc != 0 or not top:
        return False
    rel = os.path.relpath(os.path.realpath(str(profile_dir)), os.path.realpath(top))
    if rel == ".." or rel.startswith(".." + os.sep):
        return False  # the profile lives outside this repository: none of its files can be touched here
    allowed = {os.path.normpath(os.path.join(rel, f)).replace(os.sep, "/") for f in PROFILE_FILES}
    touched = set()
    for args in (("log", "-z", "--no-renames", "--format=", "--name-only", recorded + "..HEAD"),
                 ("diff", "-z", "--no-renames", "--name-only", recorded, "HEAD")):
        rc, out = git(path, *args)
        if rc != 0:
            return False
        touched.update(x.strip("\n") for x in out.split("\0") if x.strip("\n"))
    return touched <= allowed


# --------------------------------------------------------------------------- session identity (BUG-140)
# REQ-HF-020..023: the profile comes from the repo the session works in (its git top level), never from
# a folder above it, and never by a default role. A team or legacy configuration above the repo only maps
# that repo, by its exact name, to a role. Ambiguity injects nothing.
TOP_TIMEOUT_S = 2
FRONT_MATTER_LINES = 20


def git_top(path):
    """The git top level of ``path`` (realpath), or None."""
    if not path or not os.path.isdir(str(path)):
        return None
    rc, top = git(path, "rev-parse", "--show-toplevel", timeout=TOP_TIMEOUT_S)
    return os.path.realpath(top) if rc == 0 and top else None


def _common(top):
    rc, common = git(top, "rev-parse", "--git-common-dir", timeout=TOP_TIMEOUT_S)
    if rc != 0 or not common:
        return None
    return os.path.realpath(common if os.path.isabs(common) else os.path.join(str(top), common))


def repo_name(top):
    """The name a repo answers to: the basename of its main clone (a linked worktree maps by it)."""
    rc, common = git(top, "rev-parse", "--git-common-dir", timeout=TOP_TIMEOUT_S)
    if rc == 0 and common:
        common = common if os.path.isabs(common) else os.path.join(str(top), common)
        common = os.path.realpath(common)
        if os.path.basename(common) == ".git":
            return os.path.basename(os.path.dirname(common))
        return os.path.basename(common)[:-4] if common.endswith(".git") else os.path.basename(common)
    return os.path.basename(str(top).rstrip("/"))


def _ancestors(start):
    d = os.path.realpath(str(start))
    while True:
        yield d
        parent = os.path.dirname(d)
        if parent == d:
            return
        d = parent


def _read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def legacy_kv(cfg):
    kv = {}
    try:
        with open(cfg, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                if "=" in ln and not ln.lstrip().startswith("#"):
                    k, _, v = ln.partition("=")
                    kv.setdefault(k.strip(), v.strip())
    except OSError:
        pass
    return kv


def find_team_config(top):
    """``(root, cfg, kind)`` of the nearest team (``docs/spec/team.json``) or legacy (``.ceo-agentes``)
    configuration at or above ``top``, or ``(None, None, None)``."""
    for d in _ancestors(top):
        if os.path.isfile(os.path.join(d, "docs", "spec", "team.json")):
            return d, os.path.join(d, "docs", "spec", "team.json"), "team"
        if os.path.isfile(os.path.join(d, ".ceo-agentes")):
            return d, os.path.join(d, ".ceo-agentes"), "legacy"
    return None, None, None


def config_roles(cfg, kind):
    """``{repo name: role}`` declared by a team or legacy configuration (no default)."""
    if kind == "team":
        d = _read_json(cfg)
        roles = d.get("roles") if d and isinstance(d.get("roles"), dict) else {}
        return {str(k): str(v) for k, v in roles.items() if isinstance(v, str) and v.strip()}
    if kind == "legacy":
        out = {}
        for k, v in legacy_kv(cfg).items():
            for pre in ("AGENTE_", "AGENT_"):
                if k.startswith(pre) and v:
                    out.setdefault(k[len(pre):], v)
        return out
    return {}


def repo_candidates(top, name):
    """The profiles that claim the repo ``top`` named ``name``: a list of
    ``{kind, root, cfg, role, label}`` (``role`` is ``solo`` for ``docs/spec/agent/``)."""
    out = []
    solo = os.path.join(top, "docs", "spec", "agent")
    if os.path.isdir(solo):
        out.append({"kind": "solo", "root": top, "cfg": solo, "role": "solo", "label": "solo (%s)" % name})
    root, cfg, kind = find_team_config(top)
    if cfg is not None:
        role = config_roles(cfg, kind).get(name)
        if role:
            out.append({"kind": kind, "root": root, "cfg": cfg, "role": role, "label": "%s (%s)" % (role, name)})
    return out


def resolve_session_profile(start, cwd):
    """Where the session's profile comes from (REQ-HF-020, 021). Returns a dict with ``status``:

    - ``ok``: ``profile`` = the one candidate (``kind``, ``root``, ``cfg``, ``role``), ``repo`` = its name;
    - ``none``: the session's directory is not inside a git repository;
    - ``unmapped``: no profile claims the working repo;
    - ``ambiguous``: the starting and current directories are different repos, or 2+ profiles claim it.

    ``legacy_hit`` tells whether the 3.12.0 walk up the folder tree would have found a profile (the
    "profile not loaded" line is printed only then; elsewhere the hook stays silent)."""
    start = os.path.realpath(str(start))
    cwd = os.path.realpath(str(cwd or start))
    legacy_hit = any(find_team_root(d)[0] is not None for d in {start, cwd} if os.path.isdir(d))
    res = {"status": None, "legacy_hit": legacy_hit, "candidates": [], "repo": None, "profile": None, "top": None}
    tops = {}
    for d in (start, cwd):
        if os.path.isdir(d) and d not in tops:
            tops[d] = git_top(d)
    top_s, top_c = tops.get(start), tops.get(cwd, tops.get(start))
    if top_s != top_c and top_s and top_c and _common(top_s) == _common(top_c):
        top_s = top_c  # BUG-150: a worktree of the same repo is the same repo
    if top_s != top_c:
        labels = []
        for t in (top_s, top_c):
            if t is None:
                continue
            n = repo_name(t)
            cands = repo_candidates(t, n)
            labels += [c["label"] for c in cands if c["label"] not in labels] or ["%s (no profile)" % n]
        res.update(status="ambiguous", candidates=labels,
                   reason="the session started in one repo and now works in another")
        return res
    if top_c is None:
        res.update(status="none", reason="the session's directory is not inside a git repository")
        return res
    name = repo_name(top_c)
    cands = repo_candidates(top_c, name)
    res.update(repo=name, top=top_c, candidates=[c["label"] for c in cands])
    if not cands:
        res.update(status="unmapped", reason="no profile claims the repo %s (no docs/spec/agent/ in it and no "
                                             "team mapping for its name)" % name)
    elif len(cands) > 1:
        res.update(status="ambiguous", reason="more than one profile claims the repo %s" % name)
    else:
        res.update(status="ok", profile=cands[0])
    return res


def handoff_sensitive(text):
    """True when the handoff's front matter (a first ``---`` block) carries ``sensitive:`` with a value
    other than ``false`` (REQ-HF-022)."""
    lines = (text or "").splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for ln in lines[1:1 + FRONT_MATTER_LINES]:
        if ln.strip() == "---":
            return False
        k, sep, v = ln.partition(":")
        if sep and k.strip().lower() == "sensitive":
            return v.strip().strip("'\"").lower() != "false"
    return False


def profile_repos(kind, root, cfg, role):
    """The repos a profile belongs to: those its configuration maps to ``role``, or the repo that holds
    ``docs/spec/agent/`` (REQ-HF-022)."""
    if kind == "solo":
        top = git_top(root)
        return [repo_name(top)] if top else []
    return sorted(n for n, r in config_roles(cfg, kind).items() if r == role)
