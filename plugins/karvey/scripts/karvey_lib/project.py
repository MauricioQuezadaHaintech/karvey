"""Project discovery, the active change, the reviewed configuration and the state dir.

- Root discovery (§1.1): ``--root DIR``, or walk up from the cwd **no further than the git top
  level** looking for ``docs/spec/project.json`` or ``docs/spec/changes/`` (the REQ-W1-050
  definition of a Karvey project). Outside git only the start directory itself is checked, so
  a Karvey project in a parent directory is never picked up by accident.
- Active change (§5): (1) the branch is ``feature_prefix + <id>`` and ``changes/<id>`` exists;
  (2) else the only change not archived, without ``IMPLEMENTED`` and not ``deployed``;
  (3) else none (project scope; the candidates are returned for "several active: a, b").
- Reviewed configuration (§3.5): ``git show origin/<production>:<root>/docs/spec/project.json``,
  read from the local ref only (no network).
- State dir (§2.4): ``$(git rev-parse --git-common-dir)/karvey`` (shared by all worktrees), else
  ``${XDG_STATE_HOME:-~/.local/state}/karvey/<sha256(realpath(root))[:16]>``; mode 0700.

Every subprocess call is an argv list (§3.1 rule 1).
"""
import hashlib
import json
import os
import subprocess
from pathlib import Path

from .atomicio import ReadError, read_json
from .safe_values import LOGICAL_STATES

SPEC_DIR = Path("docs") / "spec"
PROJECT_JSON = SPEC_DIR / "project.json"
CHANGES_DIR = SPEC_DIR / "changes"
ARCHIVE_NAME = "archive"
IMPLEMENTED_MARKER = "IMPLEMENTED"
INACTIVE_PHASES = frozenset({"deployed", "archived"})
DEFAULT_FEATURE_PREFIX = "feature/"
GIT_TIMEOUT_S = 5


def git(args, cwd, timeout=GIT_TIMEOUT_S):
    """Run ``git <args>`` in ``cwd``; return ``(returncode, stdout)`` (stdout stripped).

    A missing git binary or a timeout returns ``(127, "")`` / ``(124, "")``.
    """
    try:
        cp = subprocess.run(["git"] + list(args), cwd=str(cwd), stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, timeout=timeout, check=False)
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired:
        return 124, ""
    except NotADirectoryError:
        return 128, ""
    return cp.returncode, cp.stdout.decode("utf-8", "replace").strip()


def _abs(path):
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def git_toplevel(path):
    rc, out = git(["rev-parse", "--show-toplevel"], path)
    return Path(out) if rc == 0 and out else None


def git_common_dir(path):
    """Absolute ``--git-common-dir`` (the main ``.git`` even from a worktree), or None."""
    rc, out = git(["rev-parse", "--git-common-dir"], path)
    if rc != 0 or not out:
        return None
    p = Path(out)
    if not p.is_absolute():
        p = _abs(Path(path) / p)
    return Path(os.path.realpath(str(p)))


def current_branch(path):
    rc, out = git(["symbolic-ref", "--quiet", "--short", "HEAD"], path)
    return out if rc == 0 and out else None


ALT_SPEC_DIR = Path("spec")
TWO_ROOTS = "two spec roots"


def _has_spec(d, spec):
    if spec == ALT_SPEC_DIR and d.name == "docs" and _has_spec(d.parent, SPEC_DIR):
        return False  # the docs/ folder of a docs/spec project is not a spec/ project of its own
    return (d / spec / "project.json").is_file() or (d / spec / "changes").is_dir()


def spec_layout(directory):
    """``(spec dir relative to the root, layout label, note)``: ``docs/spec/`` or ``spec/`` (REQ-W3-048). With both,
    ``docs/spec/`` is used and the note is ``two spec roots``; with neither, ``docs/spec/`` and ``None`` label."""
    d = Path(directory)
    main, alt = _has_spec(d, SPEC_DIR), _has_spec(d, ALT_SPEC_DIR)
    if main and alt:
        return SPEC_DIR, "docs/spec/", TWO_ROOTS
    if alt:
        return ALT_SPEC_DIR, "spec/", None
    return SPEC_DIR, "docs/spec/" if main else None, None


def spec_dir(root):
    """The absolute spec directory of a project root (``docs/spec`` or ``spec``)."""
    return Path(root) / spec_layout(root)[0]


def is_karvey_project(directory):
    d = Path(directory)
    return _has_spec(d, SPEC_DIR) or _has_spec(d, ALT_SPEC_DIR)


def find_root(start=None, root=None):
    """The Karvey project root, or None when there is none (see module docstring)."""
    if root is not None:
        r = _abs(root)
        return r if is_karvey_project(r) else None
    cur = _abs(start if start is not None else os.getcwd())
    if cur.is_file():
        cur = cur.parent
    while not cur.exists() and cur != cur.parent:
        cur = cur.parent
    top = git_toplevel(cur)
    if top is None:
        return cur if is_karvey_project(cur) else None
    top = Path(os.path.realpath(str(top)))
    cur = Path(os.path.realpath(str(cur)))
    while True:
        if is_karvey_project(cur):
            return cur
        if cur == top or cur == cur.parent:
            return None
        try:
            cur.relative_to(top)
        except ValueError:
            return None
        cur = cur.parent


def load_project_json(root):
    """``(data, error)``: data is None when the file is missing or unreadable."""
    p = spec_dir(root) / "project.json"
    if not p.is_file():
        return None, "missing"
    try:
        data = read_json(p).data
    except ReadError as exc:
        return None, str(exc)
    if not isinstance(data, dict):
        return None, "project.json is not an object"
    return data, None


def branch_flow(project):
    """``(feature_prefix, integration, production)`` with defaults for a missing block."""
    bf = project.get("branch_flow") if isinstance(project, dict) else None
    bf = bf if isinstance(bf, dict) else {}
    fp = bf.get("feature_prefix") if isinstance(bf.get("feature_prefix"), str) else DEFAULT_FEATURE_PREFIX
    integ = bf.get("integration") if isinstance(bf.get("integration"), str) else None
    prod = bf.get("production") if isinstance(bf.get("production"), str) else None
    return fp, integ, prod


BRANCH_MODES = ("trunk", "env-branches")


def branch_mode(project):
    """``(mode, source, contradiction)`` of ``branch_flow.mode`` (REQ-W2-049): the declared mode, else derived —
    ``trunk`` when integration equals production (or no integration branch is set), ``env-branches`` otherwise.
    ``contradiction`` names a declared ``trunk`` with integration ≠ production (or ``env-branches`` with them
    equal); it is None when the declaration agrees with the branches."""
    bf = project.get("branch_flow") if isinstance(project, dict) else None
    bf = bf if isinstance(bf, dict) else {}
    _, integ, prod = branch_flow(project)
    derived = "trunk" if (integ is None or prod is None or integ == prod) else "env-branches"
    declared = bf.get("mode")
    if declared not in BRANCH_MODES:
        return derived, "derived", None
    contradiction = None
    if declared != derived and integ is not None and prod is not None:
        contradiction = ("branch_flow.mode is %r but integration %r %s production %r" % (
            declared, integ, "differs from" if declared == "trunk" else "equals", prod))
    return declared, "project.json", contradiction


def list_changes(root):
    """Change directories under ``docs/spec/changes`` (not ``archive/``), sorted by name.

    Each item: ``{id, dir, phase, implemented, spec_error}``.
    """
    base = spec_dir(root) / "changes"
    out = []
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir(), key=lambda p: p.name):
        if not d.is_dir() or d.name == ARCHIVE_NAME or d.name.startswith("."):
            continue
        phase, err = None, None
        spec = d / "spec.json"
        if spec.is_file():
            try:
                data = read_json(spec).data
                phase = data.get("phase") if isinstance(data, dict) else None
            except ReadError as exc:
                err = str(exc)
        else:
            err = "spec.json missing"
        out.append({"id": d.name, "dir": str(d), "phase": phase,
                    "implemented": (d / IMPLEMENTED_MARKER).exists(), "spec_error": err})
    return out


def active_change(root, branch=None, project=None):
    """The §5 active-change rule. Returns ``{change, reason, candidates}``.

    ``reason``: ``branch`` · ``single`` · ``none`` · ``several``.
    ``branch`` defaults to the current git branch of ``root``.
    """
    root = Path(root)
    if project is None:
        project, _ = load_project_json(root)
    prefix, _, _ = branch_flow(project or {})
    if branch is None:
        branch = current_branch(root)
    changes = list_changes(root)
    ids = {c["id"] for c in changes}
    if branch and prefix and branch.startswith(prefix):
        cid = branch[len(prefix):]
        if cid in ids:
            return {"change": cid, "reason": "branch", "candidates": [cid]}
    cands = [c["id"] for c in changes
             if not c["implemented"] and c["phase"] not in INACTIVE_PHASES]
    if len(cands) == 1:
        return {"change": cands[0], "reason": "single", "candidates": cands}
    return {"change": None, "reason": "several" if cands else "none", "candidates": cands}


def read_reviewed_project_json(root, production=None):
    """``project.json`` as committed on ``origin/<production>`` (local ref, no fetch).

    Returns ``(data, status)`` with status ``ok`` · ``no-git`` · ``no-ref`` · ``missing`` ·
    ``invalid``. ``production`` defaults to the working copy's ``branch_flow.production``.
    """
    root = Path(root)
    top = git_toplevel(root)
    if top is None:
        return None, "no-git"
    if production is None:
        wc, _ = load_project_json(root)
        _, _, production = branch_flow(wc or {})
    if not production:
        return None, "no-ref"
    ref = "refs/remotes/origin/" + production
    rc, _ = git(["rev-parse", "--verify", "--quiet", ref], root)
    if rc != 0:
        return None, "no-ref"
    rel = os.path.relpath(os.path.realpath(str(root / PROJECT_JSON)), os.path.realpath(str(top)))
    rel = rel.replace(os.sep, "/")
    rc, out = git(["show", "%s:%s" % (ref, rel)], root)
    if rc != 0:
        return None, "missing"
    try:
        data = json.loads(out.lstrip("﻿"))
    except ValueError:
        return None, "invalid"
    if not isinstance(data, dict):
        return None, "invalid"
    return data, "ok"


# --------------------------------------------------------------------------- §3.5 enforcement rules
# One implementation of the switch rules, used by the guards (karvey_lib/guards.py) and by the dashboard
# (karvey-context.py). ``reviewed`` is a zero-argument callable returning ``read_reviewed_project_json``'s
# ``(data, status)``, so the git read happens only when a rule needs it.
def enforcement_of(data):
    """``data["enforcement"]`` when it is an object, else ``{}``."""
    enf = data.get("enforcement") if isinstance(data, dict) else None
    return enf if isinstance(enf, dict) else {}


def reviewed_value(key, reviewed):
    """``enforcement.<key>`` from the reviewed line, or None when absent or unreadable."""
    data, status = reviewed()
    return enforcement_of(data).get(key) if status == "ok" else None


def opt_in_state(key, wc, reviewed):
    """git-flow / plan-gate: on if ``true`` in the working copy OR on the reviewed line."""
    return enforcement_of(wc).get(key) is True or reviewed_value(key, reviewed) is True


def prod_gate_state(wc, reviewed):
    """``(on, code)`` for prod-gate (REQ-W1-026, REQ-W1-027): off only if ``false`` in the working copy
    AND on the reviewed line. ``code``: ``default`` (key absent) · ``on`` (true) · ``invalid`` (not a
    boolean; counts as on) · ``off`` · ``wc-only`` (false only in the working copy; counts as on)."""
    enf = enforcement_of(wc)
    if "prod_gate_hook" not in enf:
        return True, "default"
    v = enf["prod_gate_hook"]
    if v is True:
        return True, "on"
    if v is not False:
        return True, "invalid"
    if reviewed_value("prod_gate_hook", reviewed) is False:
        return False, "off"
    return True, "wc-only"


def _xdg_state_home():
    x = os.environ.get("XDG_STATE_HOME")
    if x and os.path.isabs(x):
        return Path(x)
    return Path(os.path.expanduser("~")) / ".local" / "state"


def state_dir(root, create=True):
    """Machine-local state directory for markers, ledger and audit (mode 0700)."""
    common = git_common_dir(root)
    if common is not None:
        d = common / "karvey"
    else:
        key = hashlib.sha256(os.path.realpath(str(root)).encode("utf-8")).hexdigest()[:16]
        d = _xdg_state_home() / "karvey" / key
    if create:
        d.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(str(d), 0o700)
        except OSError:
            pass  # native Windows: the profile ACL applies
    return d


# --------------------------------------------------------------------------- legacy settings (F-38)
LEGACY_CHANNELS = {"google_chat": "google-chat"}


def legacy_status_flow(mg):
    """The legacy ``management.status_flow`` as a ``statuses`` proposal, or None.

    Proposed only when ``statuses`` is absent and ``status_flow`` is a flat map whose keys are all
    logical states and whose values are tracker status names (strings) or ``null`` (the tracker cannot
    represent that state, REQ-W1-082) — the shape the owner already wrote, never an invented map."""
    if not isinstance(mg, dict) or "statuses" in mg:
        return None
    sf = mg.get("status_flow")
    if not isinstance(sf, dict) or not sf or not set(sf) <= set(LOGICAL_STATES):
        return None
    if not all(v is None or (isinstance(v, str) and v.strip()) for v in sf.values()):
        return None
    return dict(sf)



# --------------------------------------------------------------------------- stakeholders (wave3 §1.12)
STAKEHOLDER_ROLES = ("sponsor", "approver", "executor")


def stakeholders(project, spec=None):
    """``{role: {role, name, destination}}`` of the project, each role overridden by the change's own
    ``spec.json:stakeholders`` entry (REQ-W3-020). ``name`` defaults to the stakeholder's ``role``."""
    out = {}
    for src in (project, spec):
        block = src.get("stakeholders") if isinstance(src, dict) else None
        if not isinstance(block, dict):
            continue
        for key in STAKEHOLDER_ROLES:
            st = block.get(key)
            if isinstance(st, dict) and isinstance(st.get("role"), str) and st["role"].strip():
                entry = dict(st)
                if not (isinstance(entry.get("name"), str) and entry["name"].strip()):
                    entry["name"] = entry["role"]
                out[key] = entry
    return out
