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
    git-flow        opt-in (``enforcement.git_flow_hook``): the §3.4 rule table on the target
                    repository of each segment; fail closed when enabled.
    prod-gate       ON by default (D-02): a merge into the production set needs the human prod
                    approval of the change being released (``check-prod``); fail closed.

Configuration that can weaken a guard is read from the reviewed line (§3.5) through the small
local helpers below (``project_wc`` / ``project_reviewed`` / ``enforcement``). They are the
minimal subset of the settings resolver that ``karvey-config.py`` (lane B, E1.F7) owns; the
orchestrator reconciles them at merge (finding F-10).
"""
import importlib.util
import json
import os
import posixpath
import re
import shlex
import subprocess
import time

from . import PLUGIN_ROOT, SCRIPTS_DIR, approval, audit, hookio
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


enforcement = pj.enforcement_of  # the §3.5 rules live in karvey_lib/project.py (shared with the dashboard)


def _reviewed(ctx, root):
    return lambda: project_reviewed(ctx, root)


def reviewed_setting(ctx, key, root=None):
    """``enforcement.<key>`` from the reviewed line, or None."""
    return pj.reviewed_value(key, _reviewed(ctx, root))


def opt_in_enabled(ctx, key, root=None):
    """git-flow / plan-gate: on if ``true`` in the working copy OR on the reviewed line (§3.5)."""
    if ctx.force_enabled:
        return True
    root = root or ctx.root
    if root is None:
        return False
    wc, _ = project_wc(ctx, root)
    return pj.opt_in_state(key, wc, _reviewed(ctx, root))


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
# notify-last.json and approvals/notify also name the notification record and its human confirmation
# outside git (the XDG state dir, D-16 / F-15)
STATE_NEEDLES = ("karvey/approvals", "karvey/ledger", ".git/karvey", "notify-last.json", "approvals/notify")
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


# --------------------------------------------------------------------------- git targets (shared)
GIT_GATED = frozenset({"commit", "push", "merge", "cherry-pick", "revert", "am"})
GIT_BUILTINS = frozenset({
    "add", "am", "annotate", "apply", "archive", "bisect", "blame", "branch", "bundle", "cat-file", "checkout",
    "cherry", "cherry-pick", "clean", "clone", "commit", "config", "describe", "diff", "difftool", "fetch",
    "format-patch", "fsck", "gc", "grep", "help", "init", "log", "ls-files", "ls-remote", "ls-tree", "merge",
    "merge-base", "mv", "notes", "pull", "push", "range-diff", "rebase", "reflog", "remote", "reset", "restore",
    "rev-list", "rev-parse", "revert", "rm", "shortlog", "show", "show-ref", "sparse-checkout", "stash", "status",
    "submodule", "switch", "symbolic-ref", "tag", "update-ref", "version", "worktree", "for-each-ref",
    "name-rev", "var", "hash-object", "whatchanged", "maintenance", "prune", "repack"})


class GitTarget:
    """The repository one git segment acts on (§3.4 target resolution)."""

    __slots__ = ("dir", "git_dir", "work_tree", "unresolved", "sub", "args", "via_alias")

    def __init__(self, seg):
        g = seg.git or {}
        self.dir, self.git_dir, self.work_tree = g.get("dir"), g.get("git_dir"), g.get("work_tree")
        self.unresolved = bool(g.get("unresolved")) or self.dir is None
        for v in (self.git_dir, self.work_tree):
            if isinstance(v, str) and ("$" in v or "`" in v):
                self.unresolved = True
        self.sub, self.args, self.via_alias = g.get("sub"), list(g.get("args") or []), None

    def prefix(self):
        a = []
        if self.git_dir:
            a += ["--git-dir", self.git_dir]
        if self.work_tree:
            a += ["--work-tree", self.work_tree]
        return a

    def git(self, ctx, *args):
        if self.unresolved or not self.dir or not os.path.isdir(self.dir):
            return 128, ""
        key = ("git", self.dir, tuple(self.prefix()), args)
        return _memo(ctx, key, lambda: pj.git(self.prefix() + list(args), self.dir))

    def config_dir(self):
        """Where the target's project config is looked up: the work tree, else the directory that
        holds ``--git-dir``/``GIT_DIR`` (``/x/.git`` → ``/x``), else the segment's directory."""
        if self.work_tree:
            return self.work_tree
        if self.git_dir:
            gd = posixpath.normpath(self.git_dir)
            return posixpath.dirname(gd) if posixpath.basename(gd) == ".git" else gd
        return self.dir

    def branch(self, ctx):
        rc, out = self.git(ctx, "symbolic-ref", "--quiet", "--short", "HEAD")
        return out if rc == 0 and out else None

    def toplevel(self, ctx):
        rc, out = self.git(ctx, "rev-parse", "--show-toplevel")
        if rc == 0 and out:
            return out
        return self.git_dir or self.dir

    def resolve_alias(self, ctx):
        """Replace an alias subcommand by what it runs (``git config --get alias.X``)."""
        if not self.sub or self.sub in GIT_BUILTINS or self.unresolved:
            return None
        rc, val = self.git(ctx, "config", "--get", "alias." + self.sub)
        if rc != 0 or not val:
            return None
        self.via_alias = self.sub
        if val.startswith("!"):
            return val[1:] + (" " + " ".join(shlex.quote(a) for a in self.args) if self.args else "")
        try:
            words = shlex.split(val)
        except ValueError:
            return None
        if words:
            self.sub, self.args = words[0], words[1:] + self.args
        return None


def git_targets(ctx, parsed=None):
    """``[(segment, GitTarget)]`` for every git segment, aliases expanded (shell aliases parsed)."""
    from . import shellparse
    out = []
    parsed = parsed or ctx.parsed
    for seg in parsed.segments:
        if seg.argv0 != "git" or not seg.git:
            continue
        t = GitTarget(seg)
        script = t.resolve_alias(ctx)
        if script is not None:
            sub = shellparse.parse(script, cwd=t.dir)
            for s2 in sub.segments:
                if s2.argv0 == "git" and s2.git:
                    t2 = GitTarget(s2)
                    t2.via_alias = t.via_alias
                    out.append((s2, t2))
            continue
        out.append((seg, t))
    return out


def flow_config(ctx, target_dir):
    """``(root, integration, production)`` for a target dir: its own Karvey project, else the
    session's; ``(None, None, None)`` when neither is a Karvey project."""
    root = None
    if target_dir and os.path.isdir(target_dir):
        root = _memo(ctx, ("root-of", target_dir), lambda: pj.find_root(start=target_dir))
    root = root or ctx.root
    if root is None:
        return None, None, None
    wc, _ = project_wc(ctx, root)
    _, integ, prod = pj.branch_flow(wc or {})
    return root, integ, prod


def _push_parse(args):
    """``(remote, refspecs, flags)`` of ``git push`` arguments."""
    flags, pos = set(), []
    with_arg = {"--repo", "-o", "--push-option", "--receive-pack", "--exec"}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            pos += args[i + 1:]
            break
        if a in with_arg:
            i += 2
            continue
        if a.startswith("--"):
            flags.add(a.split("=", 1)[0])
        elif a.startswith("-") and len(a) > 1:
            for ch in a[1:]:
                flags.add("-" + ch)
        else:
            pos.append(a)
        i += 1
    remote = pos[0] if pos else None
    return remote, pos[1:], flags


def _strip_heads(ref):
    for p in ("refs/heads/", "heads/"):
        if ref.startswith(p):
            return ref[len(p):]
    return ref


def push_destinations(args, head):
    """``[(src, dst, forced, delete)]`` for a push, ``[]`` for a bare push."""
    remote, specs, flags = _push_parse(args)
    forced_all = bool(flags & {"-f", "--force", "--force-with-lease", "--force-if-includes"})
    out = []
    for spec in specs:
        forced = forced_all or spec.startswith("+")
        spec = spec.lstrip("+")
        if ":" in spec:
            src, dst = spec.split(":", 1)
        else:
            src, dst = spec, spec
        if src == "HEAD" and dst == "HEAD":
            dst = head or "HEAD"
        delete = src == "" or "--delete" in flags or "-d" in flags
        if delete and ":" not in spec:
            src = ""
        out.append((_strip_heads(src), _strip_heads(dst), forced, delete))
    return out, flags


# --------------------------------------------------------------------------- git-flow (§3.4)
DEPLOY_PATTERNS = (
    ("func", ("azure", "functionapp", "publish")),
    ("az", ("webapp", "up")),
    ("az", ("functionapp", "deployment", "source", "config-zip")),
    ("az", ("webapp", "deployment", "source", "config-zip")),
    ("firebase", ("deploy",)),
    ("gcloud", ("app", "deploy")),
    ("gcloud", ("run", "deploy")),
)


def manual_deploy(seg):
    n, args = seg.argv0, [a for a in seg.argv[1:] if not a.startswith("-")]
    for name, words in DEPLOY_PATTERNS:
        if n == name and tuple(args[:len(words)]) == words:
            return " ".join((name,) + words)
    if n == "vercel" and "--prod" in seg.argv:
        return "vercel --prod"
    if n == "netlify" and "deploy" in args[:1] and "--prod" in seg.argv:
        return "netlify deploy --prod"
    return None


def _gf_block(rule, repo, branch):
    return Decision.block("[karvey] BLOCK git-flow: %s (%s@%s)" % (rule, repo or "?", branch or "?"),
                          record={"reason": rule, "branch": branch})


def git_flow_enabled(ctx):
    """Runs when forced, or when the command has a git or deploy segment (cheap); whether the
    target's project has git-flow on is decided per segment in :func:`git_flow`."""
    if ctx.force_enabled:
        return True
    cmd = ctx.payload.command or ""
    return bool(re.search(r"\bgit\b|functionapp|webapp|vercel|netlify|firebase|gcloud", cmd))


def _gf_on(ctx, root):
    return ctx.force_enabled or opt_in_enabled(ctx, "git_flow_hook", root)


def git_flow(ctx):
    cmd = ctx.payload.command or ""
    parsed = ctx.parsed
    if parsed.unparsed:
        if _gf_on(ctx, ctx.root) and re.search(r"\bgit\b.*\b(commit|push|merge|cherry-pick|revert|am)\b", cmd):
            return _gf_block("cannot parse the command; rewrite it without unbalanced quotes", None, None)
        return None
    for seg in parsed.segments:
        d = manual_deploy(seg)
        if d and _gf_on(ctx, ctx.root):
            return _gf_block("manual deploy (%s) is forbidden; deploys run from the pipeline" % d, None, None)
    for seg, t in git_targets(ctx, parsed):
        if t.sub not in GIT_GATED:
            continue
        root, integ, prod = flow_config(ctx, t.config_dir())
        if root is None and not ctx.force_enabled:
            continue
        if not _gf_on(ctx, root):
            continue
        if ctx.force_enabled and root is None:  # legacy shim outside a project: the template defaults
            integ = ctx.env.get("KARVEY_BRANCH_INTEGRATION") or "dev"
            prod = ctx.env.get("KARVEY_BRANCH_PRODUCTION") or "master"
        if t.unresolved:
            return _gf_block("cannot resolve the target repository; rewrite without variables "
                             "(use a literal path with git -C or cd)", t.dir, None)
        prods = {prod} if prod else {"main", "master"}
        trunk = integ is not None and integ in prods
        protected = prods | ({integ} if integ else set())
        repo = t.toplevel(ctx)
        head = t.branch(ctx)
        how = " via alias %s" % t.via_alias if t.via_alias else ""
        if t.sub in ("commit", "cherry-pick", "revert", "am"):
            if t.sub != "commit" and any(a in ("--abort", "--quit", "--skip") for a in t.args):
                continue
            if head in protected:
                return _gf_block("%s%s on %s; work on a feature branch" % (t.sub, how, head), repo, head)
            continue
        if t.sub == "merge":
            if any(a in ("--abort", "--quit") for a in t.args):
                continue
            if head in prods:
                return _gf_block("merge%s on the production branch; merges into %s go through a PR" % (how, head),
                                 repo, head)
            continue
        # push
        dests, flags = push_destinations(t.args, head)
        if "--dry-run" in flags or "-n" in flags:
            continue
        if "--all" in flags or "--mirror" in flags:
            return _gf_block("push --all/--mirror also pushes the protected branches", repo, head)
        forced = bool(flags & {"-f", "--force", "--force-with-lease", "--force-if-includes"})
        if not dests:
            if head in prods or (trunk and head == integ):
                return _gf_block("bare push%s on the production branch" % how, repo, head)
            if forced and head in protected:
                return _gf_block("force push to %s" % head, repo, head)
            continue
        for src, dst, f, delete in dests:
            if "$" in dst or "`" in dst or "$" in src:
                return _gf_block("cannot resolve the push destination; rewrite without variables", repo, head)
            if dst in prods:
                return _gf_block("push to the production branch %s%s; it goes through a PR" % (dst, how), repo, head)
            if integ and dst == integ:
                if f or delete:
                    return _gf_block("force push or delete of the integration branch %s" % dst, repo, head)
                local_integ = src in (integ, "refs/heads/" + integ) or (src == "HEAD" and head == integ)
                if not local_integ:
                    return _gf_block("push of %s into the integration branch %s; merge locally into %s, then "
                                     "push %s" % (src or "?", dst, integ, integ), repo, head)
    return None


# --------------------------------------------------------------------------- prod-gate (§3.4, §3.2)
NET_BUDGET_S = 6.0          # within the 15 s pre-bash timeout (A-7)
_DEPLOY_TITLE = re.compile(r"^\[Deploy\] ([a-z0-9][a-z0-9-]{1,62})\b")
_PULL_MERGE = re.compile(r"(?:^|[\s/])repos/([^/\s]+/[^/\s]+)/pulls/(\d+)/merge\b")
_GRAPHQL_MERGE = re.compile(r"mergePullRequest|enablePullRequestAutoMerge", re.I)
_RAW_MERGE = re.compile(r"\bgh\b.*\bpr\b.*\bmerge\b|\baz\b.*\brepos\b.*\bpr\b.*\bupdate\b|\bglab\b.*\bmr\b.*"
                        r"\bmerge\b|\bgh\b.*\bapi\b.*(pulls/\d+/merge|mergePullRequest)|\bgit\b.*\bpush\b", re.I)
_STATE_MOD = None


class Candidate:
    """A production-merge candidate: the command, the repo it acts on and how to find its base."""

    __slots__ = ("kind", "seg", "dir", "selector", "repo_arg", "dst", "src", "target", "fail")

    def __init__(self, kind, seg, **kw):
        self.kind, self.seg = kind, seg
        for k in ("dir", "selector", "repo_arg", "dst", "src", "target", "fail"):
            setattr(self, k, kw.get(k))


def _positional(args, with_arg):
    pos, i = [], 0
    while i < len(args):
        a = args[i]
        if a in with_arg:
            i += 2
            continue
        if not a.startswith("-"):
            pos.append(a)
        i += 1
    return pos


def _opt(args, *names):
    for i, a in enumerate(args):
        for n in names:
            if a == n and i + 1 < len(args):
                return args[i + 1]
            if a.startswith(n + "="):
                return a[len(n) + 1:]
    return None


def prod_candidates(ctx):
    """Every production-merge candidate segment of the command (§3.4)."""
    out = []
    for seg in ctx.parsed.segments:
        a = seg.argv[1:]
        if seg.argv0 == "gh" and a[:2] == ["pr", "merge"]:
            rest = a[2:]
            pos = _positional(rest, {"-R", "--repo", "-t", "--subject", "-b", "--body", "-F", "--body-file",
                                     "--match-head-commit", "-A", "--author-email"})
            out.append(Candidate("gh", seg, dir=seg.cwd, selector=pos[0] if pos else None,
                                 repo_arg=_opt(rest, "-R", "--repo")))
        elif seg.argv0 == "gh" and a[:1] == ["api"]:
            joined = " ".join(a[1:])
            m = _PULL_MERGE.search(joined)
            if m:
                out.append(Candidate("gh", seg, dir=seg.cwd, selector=m.group(2), repo_arg=m.group(1)))
            elif _GRAPHQL_MERGE.search(joined) or ("graphql" in a[1:2] and "@" in joined):
                out.append(Candidate("gh", seg, dir=seg.cwd, fail="a GraphQL merge mutation cannot be resolved "
                                                                  "to a PR base; merge through gh pr merge"))
        elif seg.argv0 == "az" and a[:3] == ["repos", "pr", "update"]:
            status, auto = _opt(a, "--status"), _opt(a, "--auto-complete")
            if (status or "").lower() == "completed" or (auto or "").lower() in ("true", "yes", "1"):
                out.append(Candidate("az", seg, dir=seg.cwd, selector=_opt(a, "--id")))
        elif seg.argv0 == "glab" and a[:2] == ["mr", "merge"]:
            pos = _positional(a[2:], {"-m", "--message", "--sha", "-R", "--repo"})
            out.append(Candidate("glab", seg, dir=seg.cwd, selector=pos[0] if pos else None,
                                 repo_arg=_opt(a[2:], "-R", "--repo")))
        elif seg.argv0 == "git" and seg.git and seg.git.get("sub") == "push":
            out.append(Candidate("git-push", seg, target=GitTarget(seg)))
    return out


ALWAYS_PRODUCTION = ("master", "main")


def production_set(ctx, root, integ, prod):
    """The branches a merge or push into needs the human prod approval (D-15, finding F-12):
    ``branch_flow.production`` ∪ ``origin/HEAD`` ∪ {master, main on the remote}, minus the
    integration branch when it differs from production. ``master``/``main`` are never removed, so a
    renamed ``production`` or ``integration`` cannot hide them; ``origin/HEAD`` counts only when it is
    not the integration branch (Azure Repos often defaults to ``dev``)."""
    out = {prod} if prod else set()
    rc, head = pj.git(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], root)
    if rc == 0 and head.startswith("origin/"):
        out.add(head[len("origin/"):])
    for b in ALWAYS_PRODUCTION:
        rc, _ = pj.git(["rev-parse", "--verify", "--quiet", "refs/remotes/origin/" + b], root)
        if rc == 0:
            out.add(b)
    if integ and integ != prod and integ not in ALWAYS_PRODUCTION:
        out.discard(integ)
    return out


def _run_cli(argv, cwd, budget):
    try:
        cp = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=budget)
    except FileNotFoundError:
        return None, "%s is not installed" % argv[0]
    except subprocess.TimeoutExpired:
        return None, "%s did not answer within %.0f s" % (argv[0], budget)
    except OSError as exc:
        return None, "%s failed: %s" % (argv[0], exc)
    if cp.returncode != 0:
        msg = cp.stderr.decode("utf-8", "replace").strip().splitlines()
        return None, "%s exited %d%s" % (argv[0], cp.returncode, (": " + msg[0][:120]) if msg else "")
    try:
        data = json.loads(cp.stdout.decode("utf-8", "replace") or "null")
    except ValueError:
        return None, "%s printed no JSON" % argv[0]
    if not isinstance(data, dict):
        return None, "%s printed no JSON object" % argv[0]
    return data, None


def pr_info(c, cwd, budget):
    """``({base, head, title}, error)`` of the PR/MR a candidate merges."""
    if c.kind == "gh":
        argv = ["gh", "pr", "view"] + ([c.selector] if c.selector else []) + \
               (["-R", c.repo_arg] if c.repo_arg else []) + ["--json", "baseRefName,headRefName,title,number"]
        data, err = _run_cli(argv, cwd, budget)
        keys = ("baseRefName", "headRefName", "title")
    elif c.kind == "az":
        if not c.selector:
            return None, "az repos pr update without --id"
        data, err = _run_cli(["az", "repos", "pr", "show", "--id", c.selector, "--output", "json"], cwd, budget)
        keys = ("targetRefName", "sourceRefName", "title")
    else:
        argv = ["glab", "mr", "view"] + ([c.selector] if c.selector else []) + \
               (["-R", c.repo_arg] if c.repo_arg else []) + ["--output", "json"]
        data, err = _run_cli(argv, cwd, budget)
        keys = ("target_branch", "source_branch", "title")
    if err:
        return None, err
    base, head, title = (data.get(k) for k in keys)
    if not isinstance(base, str) or not base:
        return None, "the %s answer has no %s" % (c.kind, keys[0])
    return {"base": _strip_heads(base.replace("refs/heads/", "")),
            "head": _strip_heads(head.replace("refs/heads/", "")) if isinstance(head, str) else None,
            "title": title if isinstance(title, str) else ""}, None


def state_tool():
    """``karvey-state.py`` loaded in-process (its ``check_prod``), once per process."""
    global _STATE_MOD
    if _STATE_MOD is None:
        spec = importlib.util.spec_from_file_location("karvey_state_tool", str(SCRIPTS_DIR / "karvey-state.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _STATE_MOD = mod
    return _STATE_MOD


def released_change(root, head, title, prefix):
    """The change being released (§3.4): head branch → ``[Deploy] <id>`` title → the only
    change in ``deploying``. Returns ``(change, others_deploying)``."""
    changes = pj.list_changes(root)
    ids = {c["id"] for c in changes}
    deploying = [c["id"] for c in changes if c["phase"] == "deploying"]
    cid = None
    if head and prefix and head.startswith(prefix) and head[len(prefix):] in ids:
        cid = head[len(prefix):]
    if cid is None and title:
        m = _DEPLOY_TITLE.match(title)
        if m and m.group(1) in ids:
            cid = m.group(1)
    if cid is None and len(deploying) == 1:
        cid = deploying[0]
    return cid, [d for d in deploying if d != cid]


def _pg_block(change, missing, reason):
    return Decision.block("[karvey] prod-gate BLOCK change=%s missing=%s reason=%s" % (change or "?", missing, reason),
                          record={"reason": reason, "change": change, "missing": missing})


_PG_WHY = {"default": "on (default)", "on": "on", "invalid": "on", "off": "off (project.json, reviewed)",
           "wc-only": "on (false only in the working copy; not on origin/{production})"}


def prod_gate_setting(ctx, root):
    """``(on, why)``: off only if ``false`` in the working copy AND on ``origin/{production}``
    (§3.5, REQ-W1-027); a missing key or a non-boolean counts as on (REQ-W1-026)."""
    wc, _ = project_wc(ctx, root)
    on, code = pj.prod_gate_state(wc, _reviewed(ctx, root))
    return on, _PG_WHY[code]


def _evaluate_candidate(ctx, c, deadline):
    root = None
    if c.kind == "git-push":
        t = c.target
        if t.unresolved:
            return _pg_block(None, "target", "cannot verify the production approval: the push target cannot be "
                                             "resolved; rewrite without variables")
        root = _memo(ctx, ("root-of", t.config_dir()), lambda: pj.find_root(start=t.config_dir()))
    elif c.dir:
        root = _memo(ctx, ("root-of", c.dir), lambda: pj.find_root(start=c.dir)) if os.path.isdir(c.dir) else None
    root = root or (ctx.root if c.kind != "git-push" else None)
    if root is None:
        return None  # not a Karvey project: inert and silent
    on, why = prod_gate_setting(ctx, root)
    if not on:
        return Decision.allow(stdout=["[karvey] prod-gate DISABLED for this project (project.json)"],
                              record={"decision_detail": "disabled", "reason": why}, audit=True)
    wc, err = project_wc(ctx, root)
    if wc is None and err != "missing":
        return _pg_block(None, "project.json", "cannot verify the production approval: project.json unreadable (%s)"
                         % err)
    prefix, integ, prod = pj.branch_flow(wc or {})
    prods = production_set(ctx, root, integ, prod)
    note = " (project.json missing)" if wc is None else ""
    if c.fail:
        return _pg_block(None, "base", "cannot verify the production approval: " + c.fail)
    if c.kind == "git-push":
        t = c.target
        head_branch = t.branch(ctx)
        dests, flags = push_destinations(t.args, head_branch)
        if "--dry-run" in flags or "-n" in flags:
            return None
        hit = None
        if "--all" in flags or "--mirror" in flags:
            hit = (head_branch, sorted(prods)[0] if prods else "?")
        elif not dests:
            if head_branch in prods:
                hit = (head_branch, head_branch)
        for src, dst, _f, _d in dests:
            if "$" in dst or "`" in dst:
                return _pg_block(None, "target", "cannot verify the production approval: the push destination "
                                                 "cannot be resolved; rewrite without variables")
            if dst in prods:
                hit = (head_branch if src in ("HEAD", "") else src, dst)
                break
        if hit is None:
            return None
        head, base, title = hit[0], hit[1], ""
    else:
        budget = max(0.5, min(NET_BUDGET_S, deadline - time.monotonic()))
        info, err = pr_info(c, str(root), budget)
        if err:
            return _pg_block(None, "base", "cannot verify the production approval: cannot resolve the PR base (%s)"
                             % err)
        if info["base"] not in prods:
            return None  # e.g. a PR into the integration branch: allow, silent
        head, base, title = info["head"], info["base"], info["title"]
    cid, others = released_change(root, head, title, prefix)
    if cid is None:
        return _pg_block(None, "change", "cannot verify the production approval: cannot determine the change being "
                                         "released into %s (head %s; name the branch %s<id> or title the PR "
                                         "'[Deploy] <id>')%s" % (base, head or "?", prefix, note))
    try:
        res = state_tool().check_prod(root, cid)
    except Exception as exc:
        return _pg_block(cid, "valid spec.json", "cannot verify the production approval: %s" % exc)
    warn = []
    if others:
        tool = state_tool()
        pending = []
        for o in others:
            try:
                if not tool.check_prod(root, o)["ok"]:
                    pending.append(o)
            except Exception:
                pending.append(o)
        if pending:
            warn.append("[karvey] prod-gate WARNING: other changes are deploying without a prod approval: %s"
                        % ", ".join(pending))
    if not res.get("ok"):
        d = _pg_block(cid, ",".join(res.get("missing") or ["?"]), (res.get("reason") or "no production approval") + note)
        d.stdout = warn
        return d
    rec = {"change": cid, "approver": res.get("by"), "ref": res.get("ref"), "branch": base, "reason": "approved"}
    return Decision.allow(stdout=warn + ["[karvey] prod-gate ALLOW change=%s by=%s ref=%s"
                                         % (cid, res.get("by"), res.get("ref"))], record=rec, audit=True)


def prod_gate_enabled(ctx):
    """Runs on any command that could be a production merge (cheap test); the per-project
    switch (§3.5) is decided per candidate, so a disabled gate still prints its notice."""
    return bool(_RAW_MERGE.search(ctx.payload.command or ""))


def prod_gate(ctx):
    cmd = ctx.payload.command or ""
    deadline = time.monotonic() + NET_BUDGET_S
    if ctx.parsed.unparsed:
        if ctx.root is not None and _RAW_MERGE.search(cmd):
            return _pg_block(None, "command", "cannot verify the production approval: unparsable command with a "
                                              "merge verb")
        return None
    allow = None
    for c in prod_candidates(ctx):
        d = _evaluate_candidate(ctx, c, deadline)
        if d is None:
            continue
        if d.decision == "block":
            return d
        allow = allow or d
    return allow


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
        approval.gc(root)
        ttl = ttl_min(ctx)
        lines = []
        # D-16 / F-15: a human confirmation of a changed notification destination
        code = approval.classify_notify(text, vocab)
        if code is not None:
            nm = approval.write_notify_marker(root, code, text, session_id=ctx.payload.session_id, ttl_min=ttl)
            created = approval.parse_dt(nm["created_at"])
            lines.append("[karvey] notification destination confirmation recorded (%s, expires %s)"
                         % (code, (created + approval.timedelta(minutes=nm["ttl_min"])).strftime("%H:%M")))
        verdict = approval.classify(text, vocab)
        if verdict["approved"]:
            ids = [c["id"] for c in pj.list_changes(root)]
            scope = approval.scope_for(verdict["cleaned"], ids, active_change(ctx)["change"])
            marker = approval.write_marker(root, verdict["kind"], scope, text, session_id=ctx.payload.session_id,
                                           ttl_min=ttl, compat=ctx.env.get(approval.COMPAT_ENV, ""))
            created = approval.parse_dt(marker["created_at"])
            expires = (created + approval.timedelta(minutes=marker["ttl_min"])).strftime("%H:%M")
            lines.append("[karvey] approval recorded (%s, %s, expires %s)" % (verdict["kind"], scope, expires))
        return Decision.allow(stdout=lines) if lines else None
    except Exception as exc:  # fail open: no marker is the safe side (§3.2)
        _audit(root, {"guard": "approval", "event": "prompt", "decision": "error",
                      "reason": "approval-hook error: %s: %s" % (type(exc).__name__, exc)})
        return None



# --------------------------------------------------------------------------- subagent-prompt (BUG-25)
# A subagent never writes docs/spec/project.json (management-adapters.md rule 5, REQ-W1-081). The rule in
# the skill text does not reach an orchestrating session that composes a subagent prompt before it loads
# any skill (F-52 rerun), so the prompt itself is checked when the Agent/Task tool is called.
SUBAGENT_TOOLS = frozenset({"Agent", "Task"})
SUBAGENT_BAN = "Do not write `docs/spec/project.json`. If a setting or a status map is missing, return the " \
               "proposed values to me and change no tracker status that needs them."
_BAN_RE = re.compile(r"\b(do not|don't|never|must not)\s+(write|edit|modify|change|touch)\s+`?"
                     r"(docs/spec/)?project\.json`?", re.I)
_SETTINGS_WRITE_RE = re.compile(
    r"\b(persist\w*|writ(e|es|ing)|sav(e|es|ing)|updat(e|es|ing)|stor(e|es|ing)|record(s|ing)?|"
    r"edit(s|ing)?|modif(y|ies|ying)|chang(e|es|ing)|authori[sz]\w*|set(s|ting)?)\b", re.I)
_SETTINGS_TARGET_RE = re.compile(r"project\.json|\bsettings\b|\b(tracker|team|project)\s+setting\b|status(es)?\s+map|"
                                 r"management\.statuses|"
                                 r"\bstatus\s+mapping\b", re.I)
_NEGATION_RE = re.compile(r"\b(not|never|no|don't|doesn't|mustn't|cannot|can't|without)\b[\s\w`'-]{0,20}$", re.I)


def _sentences(text):
    return [s for s in re.split(r"(?<=[.;!?])\s+|\n+", text) if s.strip()]


def _allows_writing(sentence):
    """A sentence naming the settings with a write/persist/authorise verb that is not negated just
    before it ("do not write", "never change" …)."""
    if not _SETTINGS_TARGET_RE.search(sentence):
        return False
    return any(not _NEGATION_RE.search(sentence[max(0, m.start() - 30):m.start()])
               for m in _SETTINGS_WRITE_RE.finditer(sentence))


def subagent_prompt(ctx):
    """Block a subagent prompt, in a Karvey project, that lets the subagent write the project settings
    and does not carry the ban line. Fail open: the text rule still applies without this guard."""
    p = ctx.payload
    if p.tool_name not in SUBAGENT_TOOLS or ctx.root is None:
        return None
    prompt = (p.tool_input or {}).get("prompt")
    if not isinstance(prompt, str) or not prompt.strip() or _BAN_RE.search(prompt):
        return None
    for s in _sentences(prompt):
        if _allows_writing(s):
            return Decision.block(
                "[karvey] BLOCK subagent-prompt: this subagent prompt lets the subagent write the project "
                "settings (\"%s\"). Subagents never write docs/spec/project.json (management-adapters.md "
                "rule 5): the orchestrating session persists settings with the human, on a docs branch. "
                "Re-send the prompt without that permission and with this line: %s"
                % (s.strip()[:160], SUBAGENT_BAN),
                record={"reason": "subagent prompt allows writing project.json"})
    return None


__all__ = ["Decision", "protect_paths", "approval_hook", "plan_gate", "plan_gate_enabled", "git_flow",
           "git_flow_enabled", "prod_gate", "prod_gate_enabled", "prod_gate_setting", "EDIT_TOOLS", "hookio",
           "subagent_prompt"]
