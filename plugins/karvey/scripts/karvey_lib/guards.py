"""The guards of the hook dispatcher (architecture §1.3, §3.2..§3.5).

Each guard is a function ``guard(ctx) -> Decision | None`` called by ``karvey_hooks.dispatch`` in
the §1.3 order (first block wins). ``None`` means "nothing to say" (allow, silent). Every
subprocess call is an argv list (§3.1 rule 1). Critical output is ASCII (``[karvey] …``).

    protect-paths   always on, also outside a Karvey project (the state dirs are protected
                    wherever they live); fail closed.
    approval        UserPromptSubmit: records the human's approval marker (D-01, D-10, D-11);
                    fail open (no marker is the safe side).
    plan-gate       opt-in (``enforcement.plan_gate_hook``): Edit/Write and the write /
                    destructive command classes of §3.4 need a live marker; fail closed.

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


# --------------------------------------------------------------------------- plan-gate (§3.4)
PLAN_MSG = ("[karvey] BLOCK plan-gate: %s. Present the plan and wait for the human's approval; "
            "the approval hook records it.")
NULL_TARGETS = frozenset({"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty", "-"})
WRITE_OPS = frozenset({">", ">>", ">|", "&>", "&>>", "<>"})
SQL_CLIENTS = frozenset({"psql", "mysql", "mariadb", "sqlcmd", "sqlite3", "sqlplus", "bq", "clickhouse-client",
                         "cockroach", "duckdb", "osql", "isql", "snowsql", "trino", "presto"})
_SQL_DROP = re.compile(r"\bdrop\s+(table|database|schema)\b", re.I)
_SQL_TRUNC = re.compile(r"\btruncate\s+(table\s+)?[\w.\[\]\"`]+", re.I)
_SQL_DELETE = re.compile(r"\bdelete\s+from\s+[\w.\[\]\"`]+(?P<rest>[^;]*)", re.I)
_RAW_WRITE = re.compile(r"(^|[^0-9&>])>>?\|?\s*(?!&|/dev/null|/dev/std(out|err))[^\s&|;]")
_RAW_DESTRUCTIVE = re.compile(
    r"\brm\s+-[a-zA-Z]*[rR]|\brm\s+--recursive|\bgit\s+(clean|reset\s+--hard|push\s+.*(--force|-f\b))|"
    r"\bsed\s+(-[a-zA-Z]*i|--in-place)|\bperl\s+-[a-zA-Z]*i|\btruncate\b|\bfind\b.*\s-(delete|exec)|"
    r"\bdrop\s+(table|database)\b|\bdelete\s+from\b|\bterraform\s+(destroy|apply\s.*-destroy)|"
    r"\b(az|gcloud|kubectl)\b.*\sdelete\b|\baws\b.*\s(delete-|rm\b|rb\b)", re.I)


def _is_write_redirect(r):
    if r.op in WRITE_OPS:
        return bool(r.target) and r.target not in NULL_TARGETS and not r.target.startswith("/dev/fd/")
    if r.op == ">&":  # N>&M and >&2 duplicate a descriptor; `>& file` writes a file
        t = r.target or ""
        return bool(t) and not t.isdigit() and t != "-" and t not in NULL_TARGETS
    return False


def _sql_text(seg):
    parts = list(seg.argv[1:])
    parts += [r.body for r in seg.redirects if getattr(r, "body", None)]
    parts += [r.target for r in seg.redirects if r.op == "<<<" and r.target]
    return "\n".join(p for p in parts if isinstance(p, str))


def _sql_class(text):
    if _SQL_DROP.search(text):
        return "SQL DROP"
    if _SQL_TRUNC.search(text):
        return "SQL TRUNCATE"
    for m in _SQL_DELETE.finditer(text):
        if not re.search(r"\bwhere\b", m.group("rest"), re.I):
            return "SQL DELETE without WHERE"
    return None


def _flag(args, short, long=()):
    """``short`` appears as a flag (alone or combined: ``-rf``) or one of ``long``."""
    for a in args:
        if a in long or any(a.startswith(x + "=") for x in long):
            return True
        if a.startswith("-") and not a.startswith("--") and short in a[1:]:
            return True
    return False


def destructive_class(seg):
    """The §3.4 destructive class of one segment, or None."""
    n, args = seg.argv0, seg.argv[1:]
    if n == "rm" and (_flag(args, "r", ("--recursive",)) or _flag(args, "R")):
        return "recursive rm"
    if n == "git" and seg.git:
        sub, ga = seg.git.get("sub"), seg.git.get("args") or []
        if sub == "clean":
            return "git clean"
        if sub == "reset" and "--hard" in ga:
            return "git reset --hard"
        if sub == "checkout" and "--" in ga:
            return "git checkout --"
        if sub == "restore" and ("--staged" not in ga and "-S" not in ga or "--worktree" in ga or "-W" in ga):
            return "git restore"
        if sub == "push" and (any(a in ("-f", "--force", "--mirror") or a.startswith("--force") for a in ga)
                              or any(a.startswith("+") for a in ga if not a.startswith("-"))):
            return "git push --force"
    if n == "sed" and any(a == "-i" or a.startswith("-i") or a == "--in-place" or a.startswith("--in-place=")
                          or (a.startswith("-") and not a.startswith("--") and "i" in a[1:] and len(a) <= 4)
                          for a in args):
        return "sed -i"
    if n == "perl" and _flag(args, "i"):
        return "perl -i"
    if n == "truncate":
        return "truncate"
    if n == "find" and ("-delete" in args or any(a in ("-exec", "-execdir", "-ok", "-okdir") and i + 1 < len(args)
                                                  and posixpath.basename(args[i + 1]) in ("rm", "rmdir", "unlink",
                                                                                          "shred")
                                                  for i, a in enumerate(args))):
        return "find -delete"
    if n in SQL_CLIENTS:
        c = _sql_class(_sql_text(seg))
        if c:
            return c
    if n in ("terraform", "tofu") and args:
        if args[0] == "destroy" or (args[0] == "apply" and "-destroy" in args):
            return "terraform destroy"
    if n in ("az", "gcloud") and "delete" in args:
        return "%s delete" % n
    if n == "aws" and any(a.startswith("delete-") or a in ("rm", "rb") for a in args[:3]):
        return "aws delete"
    if n == "kubectl" and "delete" in args[:2]:
        return "kubectl delete"
    return None


def write_class(seg):
    for r in seg.redirects:
        if _is_write_redirect(r):
            return "write to %s" % r.target
    if seg.argv0 == "tee":
        files = [a for a in seg.argv[1:] if not a.startswith("-") and a not in NULL_TARGETS]
        if files:
            return "write to %s" % files[0]
    return None


def plan_classes(ctx):
    """The gated classes of this tool call (empty = not gated)."""
    if ctx.event == "pre-edit":
        return ["file edit (%s)" % (ctx.payload.tool_name or "Edit")]
    cmd = ctx.payload.command or ""
    if not cmd.strip():
        return []
    parsed = ctx.parsed
    if parsed.unparsed:  # conservative regex over the raw string (§3.2)
        if _RAW_DESTRUCTIVE.search(cmd) or _RAW_WRITE.search(cmd):
            return ["unparsable command that may write or destroy"]
        return []
    out = []
    for seg in parsed.segments:
        c = destructive_class(seg) or write_class(seg)
        if c:
            out.append(c)
    return out


def _gate_root(ctx):
    """The project whose marker counts: the edited file's project, else the session's."""
    if ctx.event == "pre-edit" and ctx.payload.file_path:
        r = _memo(ctx, ("root-of", ctx.payload.file_path),
                  lambda: pj.find_root(start=posixpath.dirname(ctx.payload.file_path)))
        if r is not None:
            return r
    return ctx.root


def plan_gate_enabled(ctx):
    return opt_in_enabled(ctx, "plan_gate_hook", _gate_root(ctx))


def plan_gate(ctx):
    classes = plan_classes(ctx)
    if not classes:
        return None
    root = _gate_root(ctx)
    base = root or ctx.payload.cwd
    change = active_change(ctx, root)["change"] if root else None
    marker, scope, reasons = approval.find_valid(base, change=change, ttl_min=ttl_min(ctx, root) if root else None)
    if marker is not None:
        approval.cross_check(base, marker, ctx.payload.transcript_path)
        return None
    why = "; ".join("%s: %s" % (k, v) for k, v in reasons.items())
    return Decision.block(PLAN_MSG % classes[0] + " (marker %s)" % why,
                          record={"reason": classes[0], "change": change, "marker": why})


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


__all__ = ["Decision", "protect_paths", "approval_hook", "plan_gate", "plan_gate_enabled", "EDIT_TOOLS", "hookio"]
