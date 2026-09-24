"""The guards of the hook dispatcher (architecture §1.3, §3.2..§3.5).

Each guard is a function ``guard(ctx) -> Decision | None`` called by ``karvey_hooks.dispatch`` in
the §1.3 order (first block wins). ``None`` means "nothing to say" (allow, silent). Every
subprocess call is an argv list (§3.1 rule 1). Critical output is ASCII (``[karvey] …``).

    protect-paths   always on, also outside a Karvey project (the state dirs are protected
                    wherever they live); fail closed.
    approval        UserPromptSubmit: records the human's approval marker (D-01, D-10, D-11);
                    fail open (no marker is the safe side).

Configuration that can weaken a guard is read from the reviewed line (§3.5) through the small
local helpers below (``project_wc`` / ``project_reviewed`` / ``enforcement``). They are the
minimal subset of the settings resolver that ``karvey-config.py`` (lane B, E1.F7) owns; the
orchestrator reconciles them at merge (finding F-10).
"""
import os
import posixpath
import re

from . import PLUGIN_ROOT, approval, audit, hookio
from . import project as pj


class Decision:
    """A guard's verdict. ``audit`` asks the dispatcher to log an *allow* too (prod-gate)."""

    __slots__ = ("decision", "message", "stdout", "record", "audit")

    def __init__(self, decision, message="", stdout=None, record=None, audit=False):
        self.decision, self.message, self.stdout = decision, message, list(stdout or [])
        self.record, self.audit = record or {}, audit

    @classmethod
    def allow(cls, stdout=None, record=None, audit=False):
        return cls("allow", stdout=stdout, record=record, audit=audit)

    @classmethod
    def block(cls, message, record=None):
        return cls("block", message=message, record=record)


EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})


# --------------------------------------------------------------------------- shared helpers
def env_expand(text, env, home=None):
    """``text`` with ``~``, ``$HOME`` and the hook-relevant variables expanded (others kept)."""
    if not isinstance(text, str):
        return text
    home = home if home is not None else env.get("HOME") or os.path.expanduser("~")
    if text == "~" or text.startswith("~/"):
        text = home + text[1:]
    names = {"HOME": home}
    for k in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR", "KARVEY_COMPAT_MARKER", "TMPDIR", "XDG_STATE_HOME"):
        if env.get(k):
            names[k] = env[k]
    for k, v in names.items():
        text = text.replace("${%s}" % k, v).replace("$" + k + "/", v + "/")
        if text.endswith("$" + k):
            text = text[: -len(k) - 1] + v
    return text


def seg_path(seg, text, env):
    """An argument of ``seg`` as an absolute, normalised path (None when it cannot be resolved)."""
    t = env_expand(text, env)
    if not t or "$" in t or "`" in t:
        return None
    if not t.startswith("/"):
        if not seg.cwd:
            return None
        t = posixpath.join(seg.cwd, t)
    return posixpath.normpath(t)


def realpath(p):
    try:
        return os.path.realpath(p)
    except (OSError, ValueError):
        return p


def under(path, base):
    if not path or not base:
        return False
    path, base = posixpath.normpath(path), posixpath.normpath(base)
    return path == base or path.startswith(base.rstrip("/") + "/")


# --------------------------------------------------------------------------- config (§3.5), local helpers
def _memo(ctx, key, fn):
    if key not in ctx.cache:
        ctx.cache[key] = fn()
    return ctx.cache[key]


def project_wc(ctx, root=None):
    """``(data, error)`` of the working copy's ``project.json`` of ``root`` (default ctx.root)."""
    root = root or ctx.root
    if root is None:
        return None, "no project"
    return _memo(ctx, ("wc", str(root)), lambda: pj.load_project_json(root))


def project_reviewed(ctx, root=None, production=None):
    """``(data, status)`` of ``project.json`` on ``origin/{production}`` (local ref, no fetch)."""
    root = root or ctx.root
    if root is None:
        return None, "no project"
    return _memo(ctx, ("rev", str(root), production),
                 lambda: pj.read_reviewed_project_json(root, production=production))


def enforcement(data):
    enf = data.get("enforcement") if isinstance(data, dict) else None
    return enf if isinstance(enf, dict) else {}


def reviewed_setting(ctx, key, root=None):
    """``enforcement.<key>`` from the reviewed line, or None."""
    data, status = project_reviewed(ctx, root)
    return enforcement(data).get(key) if status == "ok" else None


def opt_in_enabled(ctx, key, root=None):
    """git-flow / plan-gate: on if ``true`` in the working copy OR on the reviewed line (§3.5)."""
    if ctx.force_enabled:
        return True
    root = root or ctx.root
    if root is None:
        return False
    wc, _ = project_wc(ctx, root)
    return enforcement(wc).get(key) is True or reviewed_setting(ctx, key, root) is True


def active_change(ctx, root=None):
    root = root or ctx.root
    if root is None:
        return {"change": None, "reason": "none", "candidates": []}
    return _memo(ctx, ("active", str(root)), lambda: pj.active_change(root, project=project_wc(ctx, root)[0]))


def ttl_min(ctx, root=None):
    """``plan_marker_ttl_min`` from the reviewed line, else the default; clamped (D-07)."""
    return approval.clamp_ttl(reviewed_setting(ctx, "plan_marker_ttl_min", root))


# --------------------------------------------------------------------------- protect-paths
PROTECT_MSG = ("[karvey] BLOCK protect-paths: approval comes only from the human's message (D-01). "
               "The Karvey approval markers, release ledger and plugin files are written only by the "
               "hooks and the state tool; wait for the human to approve in their own message.")
STATE_NEEDLES = ("karvey/approvals", "karvey/ledger", ".git/karvey")
READ_ONLY = frozenset({"cat", "ls", "head", "tail", "stat", "wc", "file", "less", "more", "grep", "egrep",
                       "fgrep", "rg", "jq", "test", "[", "diff", "cmp", "sha256sum", "shasum", "md5sum",
                       "readlink", "realpath", "basename", "dirname", "du", "tree"})
# commands that change files they name: which arguments count (None = every non-option argument)
MUTATORS = {"cp": "last", "install": "last", "ln": "last", "rsync": "last", "mv": None, "rm": None,
            "rmdir": None, "touch": None, "tee": None, "truncate": None, "chmod": None, "chown": None,
            "unlink": None, "mkdir": None, "shred": None, "dd": "of", "patch": None}


def _compat(env):
    v = env.get("KARVEY_COMPAT_MARKER") or ""
    return env_expand(v, env) if v.strip() else ""


def _plugin_roots(env):
    roots = {realpath(str(PLUGIN_ROOT))}
    if env.get("CLAUDE_PLUGIN_ROOT"):
        roots.add(realpath(env_expand(env["CLAUDE_PLUGIN_ROOT"], env)))
    return {r for r in roots if r and r != "/"}


def _xdg_state_root(env):
    x = env.get("XDG_STATE_HOME")
    base = x if x and x.startswith("/") else posixpath.join(env.get("HOME") or os.path.expanduser("~"),
                                                              ".local", "state")
    return posixpath.join(base, "karvey")


def _state_needles(env):
    needles = list(STATE_NEEDLES)
    c = _compat(env)
    if c:
        needles += [c, posixpath.basename(c.rstrip("/"))]
    return [n for n in needles if n]


def _hits(text, needles):
    if not isinstance(text, str) or not text:
        return None
    for n in needles:
        if n in text:
            return n
    return None


def _unquote(text):
    return text.replace("'", "").replace('"', "").replace("\\", "")


def _mutated_args(seg):
    """The arguments a mutating command writes to (``[]`` for read-only or unknown commands)."""
    name = seg.argv0
    args = seg.argv[1:]
    if name in ("sed", "perl"):
        if any(a == "-i" or a.startswith("-i") or a == "--in-place" or a.startswith("--in-place=")
               or (name == "perl" and a.startswith("-") and not a.startswith("--") and "i" in a[1:])
               for a in args):
            return [a for a in args if not a.startswith("-")]
        return []
    rule = MUTATORS.get(name, "absent")
    if rule == "absent":
        return []
    pos = [a for a in args if not a.startswith("-")]
    if rule == "last":
        return pos[-1:]
    if rule == "of":
        return [a[3:] for a in args if a.startswith("of=")]
    return pos


def protect_paths(ctx):
    env = ctx.env
    needles = _state_needles(env)
    plugin_roots = _plugin_roots(env)
    compat = _compat(env)
    if ctx.event == "pre-edit":
        raw = ctx.payload.file_path_raw
        path = ctx.payload.file_path
        if not raw and not path:
            return None
        cands = {p for p in (path, realpath(path) if path else None) if p}
        for p in cands:
            if _hits(p + "/", ("/karvey/approvals/", "/karvey/ledger/", "/.git/karvey/")) or \
                    under(p, _xdg_state_root(env)) or (compat and p in (compat, realpath(compat))) or \
                    any(under(p, r) for r in plugin_roots):
                return Decision.block(PROTECT_MSG, record={"reason": "edit of a protected path", "path": p})
            common = pj.git_common_dir(posixpath.dirname(p)) if os.path.isdir(posixpath.dirname(p)) else None
            if common is not None and under(p, str(common / "karvey")):
                return Decision.block(PROTECT_MSG, record={"reason": "edit of the Karvey state dir"})
        return None
    # pre-bash
    cmd = ctx.payload.command or ""
    if not cmd.strip():
        return None
    parsed = ctx.parsed
    expanded_raw = env_expand(cmd, env)
    if parsed.unparsed:
        if _hits(cmd, needles) or _hits(_unquote(expanded_raw), needles):
            return Decision.block(PROTECT_MSG, record={"reason": "unparsed command names a protected path"})
        return None
    for seg in parsed.segments:
        texts = [env_expand(a, env) for a in seg.argv]
        targets = [env_expand(r.target, env) for r in seg.redirects
                   if r.target and r.op in (">", ">>", ">|", "&>", "&>>", "<>", ">&")]
        # the state dirs and the compat marker: any mention, except by a read-only command
        if seg.argv0 not in READ_ONLY or any(_hits(t, needles) for t in targets):
            joined = " ".join(texts + targets)
            if _hits(joined, needles) or _hits(_unquote(joined), needles):
                return Decision.block(PROTECT_MSG, record={"reason": "command names a protected path"})
        elif seg.argv0 == "find" and any(a in ("-delete", "-exec", "-execdir", "-ok") for a in seg.argv):
            if _hits(" ".join(texts), needles):
                return Decision.block(PROTECT_MSG, record={"reason": "command names a protected path"})
        # the plugin root: only writes (running the plugin's own scripts is normal)
        writes = [seg_path(seg, a, env) for a in _mutated_args(seg)] + \
                 [seg_path(seg, r.target, env) for r in seg.redirects
                  if r.target and r.op in (">", ">>", ">|", "&>", "&>>", "<>") or
                  (r.op == ">&" and r.target and not r.target.isdigit() and r.target != "-")]
        for w in writes:
            if w and any(under(w, root) or under(realpath(w), root) for root in plugin_roots):
                return Decision.block(PROTECT_MSG, record={"reason": "write under the plugin root"})
    # a needle hidden by quoting across words (``karvey/"approvals"``) in the whole command
    if _hits(_unquote(expanded_raw), [n for n in needles if "/" in n]) and not all(
            s.argv0 in READ_ONLY for s in parsed.segments):
        return Decision.block(PROTECT_MSG, record={"reason": "command names a protected path"})
    return None


# --------------------------------------------------------------------------- approval hook
def _audit(root, record):
    try:
        audit.append(pj.state_dir(root), record)
    except Exception:
        pass


def approval_hook(ctx):
    """UserPromptSubmit (REQ-W1-017, 019; D-01, D-10, D-11). Silent unless it records a marker;
    it never blocks the prompt. Outside a Karvey project it does nothing."""
    root = ctx.root
    text = ctx.payload.prompt
    if root is None or not isinstance(text, str) or not text.strip():
        return None
    try:
        vocab = approval.vocabulary(reviewed_setting(ctx, "approval_vocabulary"))
        verdict = approval.classify(text, vocab)
        approval.gc(root)
        if not verdict["approved"]:
            return None
        ids = [c["id"] for c in pj.list_changes(root)]
        scope = approval.scope_for(verdict["cleaned"], ids, active_change(ctx)["change"])
        ttl = ttl_min(ctx)
        marker = approval.write_marker(root, verdict["kind"], scope, text, session_id=ctx.payload.session_id,
                                       ttl_min=ttl, compat=ctx.env.get(approval.COMPAT_ENV, ""))
        created = approval.parse_dt(marker["created_at"])
        expires = (created + approval.timedelta(minutes=marker["ttl_min"])).strftime("%H:%M")
        return Decision.allow(stdout=["[karvey] approval recorded (%s, %s, expires %s)"
                                      % (verdict["kind"], scope, expires)])
    except Exception as exc:  # fail open: no marker is the safe side (§3.2)
        _audit(root, {"guard": "approval", "event": "prompt", "decision": "error",
                      "reason": "approval-hook error: %s: %s" % (type(exc).__name__, exc)})
        return None


__all__ = ["Decision", "protect_paths", "approval_hook", "EDIT_TOOLS", "hookio"]
