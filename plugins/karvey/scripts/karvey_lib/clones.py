"""Local clones a release command may target (REQ-HF-007, 008, 014, 024..026; architecture §1.3).

No network: a clone is known by the names it answers to (the main clone's folder name, the last path segment
of each remote URL, ``owner/name`` for host URLs). The places searched are bounded: the session's project and
its worktrees, the command's directory, the folders next to them, and paths listed in ``project.json:repos``.
"""
import json
import os
import re
from pathlib import Path

from . import project as pj

SIBLINGS_MAX = 200
_URL_NAME = re.compile(r"(?:[:/])([^/:]+)/([^/]+?)(?:\.git)?/?$")
_AZ_NAME = re.compile(r"/_git/([^/]+?)/?$")


def norm(name):
    """``owner/name`` (host URLs, ``owner/name`` arguments) or ``name``, lower case, ``.git`` removed.
    A local path (a remote that is a folder) gives its folder name."""
    if not isinstance(name, str):
        return None
    n = name.strip().rstrip("/")
    m = _AZ_NAME.search(n)
    if m:
        return m.group(1).lower()
    if "://" in n and not n.startswith("file://") or n.startswith("git@") or re.match(r"^[^/\s]+@[^/\s]+:", n):
        m = _URL_NAME.search(n)
        return ("%s/%s" % (m.group(1), m.group(2))).lower() if m else None
    if n.startswith(("/", ".", "file://", "~")) or n.count("/") > 1:
        n = n.rsplit("/", 1)[-1]
    n = n[:-4] if n.endswith(".git") else n
    return n.lower() or None


def short(name):
    n = norm(name)
    return n.rsplit("/", 1)[-1] if n else None


def toplevel(path):
    try:
        if not path or not os.path.isdir(str(path)):
            return None
    except (OSError, ValueError):
        return None
    t = pj.git_toplevel(path)
    return os.path.realpath(str(t)) if t else None


def main_name(top):
    common = pj.git_common_dir(top)
    if common is None:
        return os.path.basename(str(top))
    c = str(common)
    if os.path.basename(c) == ".git":
        return os.path.basename(os.path.dirname(c))
    return os.path.basename(c)[:-4] if c.endswith(".git") else os.path.basename(c)


def names(top):
    """The names the clone at ``top`` answers to."""
    out = {main_name(top).lower()}
    rc, urls = pj.git(["remote", "-v"], top)
    if rc == 0:
        for ln in urls.splitlines():
            parts = ln.split()
            if len(parts) >= 2:
                n = norm(parts[1])
                if n:
                    out.add(n)
                    out.add(n.rsplit("/", 1)[-1])
    return out


def answers_to(top, target):
    t = norm(target)
    if not t:
        return False
    ns = names(top)
    hosted = {n for n in ns if "/" in n}
    plain = {n for n in ns if "/" not in n}
    if "/" in t:
        return t in hosted or (not hosted and t.rsplit("/", 1)[-1] in plain)
    return t in plain


def _worktrees(top):
    rc, out = pj.git(["worktree", "list", "--porcelain"], top)
    if rc != 0:
        return []
    return [ln[len("worktree "):].strip() for ln in out.splitlines() if ln.startswith("worktree ")]


def _project_paths(root):
    data, _ = pj.load_project_json(root)
    out = []
    for r in (data or {}).get("repos") or []:
        if isinstance(r, str) and ("/" in r or r.startswith(".")):
            p = r if os.path.isabs(r) else os.path.join(str(root), r)
            out.append(os.path.realpath(p))
    return out


def search_dirs(anchors):
    """The ordered, de-duplicated candidate folders around ``anchors`` (paths that may be None)."""
    seen, out = set(), []

    def add(p):
        if p and p not in seen and os.path.isdir(p):
            seen.add(p)
            out.append(p)

    tops = []
    for a in anchors:
        t = toplevel(a) if a else None
        if t:
            tops.append(t)
            add(t)
    for t in list(tops):
        for wt in _worktrees(t):
            add(os.path.realpath(wt))
        if pj.is_karvey_project(t):
            for p in _project_paths(t):
                add(p)
    # BUG-145: a session in a folder that holds the repos (not a repo itself) — its children, two levels
    budget = [SIBLINGS_MAX * 2]

    def kids_of(d, depth):
        if depth == 0 or budget[0] <= 0:
            return
        try:
            names = sorted(os.listdir(d))
        except OSError:
            return
        for k in names:
            if budget[0] <= 0:
                return
            p = os.path.join(d, k)
            if k.startswith(".") or not os.path.isdir(p):
                continue
            budget[0] -= 1
            if os.path.exists(os.path.join(p, ".git")):
                add(os.path.realpath(p))
            else:
                kids_of(p, depth - 1)

    for a in anchors:
        if a and os.path.isdir(a) and not toplevel(a):
            kids_of(os.path.realpath(a), 2)
    parents = []
    for a in [x for x in anchors if x] + tops:
        par = os.path.dirname(os.path.realpath(str(a)))
        if par not in parents:
            parents.append(par)
    for par in parents:
        try:
            kids = sorted(os.listdir(par))[:SIBLINGS_MAX]
        except OSError:
            continue
        for k in kids:
            p = os.path.join(par, k)
            if os.path.isdir(os.path.join(p, ".git")) or os.path.isfile(os.path.join(p, ".git")):
                add(os.path.realpath(p))
    return out


def find_clones(anchors, target):
    """Every local clone (top level) that answers to ``target``, in search order (BUG-145: a look-alike
    clone must not shadow the real one)."""
    out = []
    for d in search_dirs(anchors):
        t = toplevel(d)
        if t and t not in out and answers_to(t, target):
            out.append(t)
    return out


def find_clone(anchors, target):
    """The first local clone (top level) that answers to ``target``, or None."""
    found = find_clones(anchors, target)
    return found[0] if found else None


def has_commit(top, sha):
    """True when the clone at ``top`` holds commit ``sha`` (identity by history, BUG-145)."""
    if not top or not isinstance(sha, str) or not re.match(r"^[0-9a-f]{40}([0-9a-f]{24})?$", sha):
        return False
    rc, _ = pj.git(["cat-file", "-e", sha + "^{commit}"], top)
    return rc == 0


def find_owner(anchors, change):
    """The first Karvey clone that holds ``docs/spec/changes/<change>/spec.json``, or None."""
    for d in search_dirs(anchors):
        t = toplevel(d)
        if t and pj.is_karvey_project(t) and (Path(t) / pj.CHANGES_DIR / change / "spec.json").is_file():
            return t
    return None


def karvey_named(root, target):
    """True when the Karvey project at ``root`` names ``target`` among its repos or a change's ``repos``."""
    if root is None:
        return False
    t = short(target)
    if not t:
        return False
    data, _ = pj.load_project_json(root)
    listed = [r for r in ((data or {}).get("repos") or []) if isinstance(r, str)]
    for c in pj.list_changes(root):
        spec = read_spec(Path(c["dir"]) / "spec.json")
        if isinstance(spec, dict) and isinstance(spec.get("repos"), list):
            listed += [r for r in spec["repos"] if isinstance(r, str)]
    return any(short(os.path.basename(r.rstrip("/"))) == t for r in listed)


def read_spec(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
