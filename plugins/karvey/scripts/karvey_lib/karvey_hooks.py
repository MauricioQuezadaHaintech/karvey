"""Event entry points called by ``hooks/karvey-hook.sh`` (architecture §1.3).

    python3 karvey_hooks.py <event> [--only <guard>[,<guard>…]] [--force-enabled]

Events: ``prompt`` (UserPromptSubmit) · ``pre-bash`` / ``pre-edit`` (PreToolUse) ·
``post-edit`` (PostToolUse) · ``session`` (SessionStart, E1.F6.T1).

One process per event: the payload is parsed once (``hookio``), the command is segmented once
(``shellparse``) and the project is located once, then the registered guards run **in the §1.3
order; the first block wins** (exit 2, reason on stderr — the harness contract). Every block is
recorded in ``audit.log``.

Guard registry (order, fail mode — §3.2):

    pre-bash   protect-paths (closed) → prod-gate (closed) → git-flow (closed) → plan-gate (closed)
    pre-edit   protect-paths (closed) → plan-gate (closed)
    post-edit  spec-write (open) → pending-sync (open)
    prompt     approval (open)

The guards live in ``guards.py`` (and ``post_edit`` / ``approval_hook`` below); a guard
registered with ``wired = False`` is an allow-stub that neither runs nor applies its fail mode.

``selftest`` is a diagnostic, block-only guard that runs first on the tool events, only when
``KARVEY_HOOK_SELFTEST=1`` is in the hook's environment, and blocks a call whose command or
path contains ``KARVEY-SELFTEST-BLOCK``. It can add a block, never remove one; the table runner
uses it to prove the block path end to end before the real guards exist.

Time budget (A-7): each event has an internal budget below its ``hooks.json`` timeout. When it
runs out, the guard being evaluated decides by its fail mode (closed → block), so the decision is
reached before the harness would cancel the hook (a cancelled hook does not block).
"""
import argparse
import os
import sys
import threading
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from karvey_lib import HOOK_ALLOW, HOOK_BLOCK, audit, guards, hookio, shellparse  # noqa: E402
    from karvey_lib import project as pj  # noqa: E402
else:
    from . import HOOK_ALLOW, HOOK_BLOCK, audit, guards, hookio, shellparse
    from . import project as pj

EVENTS = ("prompt", "pre-bash", "pre-edit", "post-edit", "session")
# hooks.json timeouts: prompt 5 s · pre-bash 15 s · pre-edit 5 s · post-edit 10 s · session 10 s
BUDGET_S = {"prompt": 4.0, "pre-bash": 12.0, "pre-edit": 4.0, "post-edit": 8.0, "session": 8.0}
STDIN_MAX = 4 * 1024 * 1024
SELFTEST_ENV = "KARVEY_HOOK_SELFTEST"
SELFTEST_TOKEN = "KARVEY-SELFTEST-BLOCK"


Decision = guards.Decision


class Context:
    """What every guard of one event shares: the payload, the segments, the project."""

    def __init__(self, event, payload, env, only=None, force_enabled=False):
        self.event, self.payload, self.env = event, payload, env
        self.only, self.force_enabled = only, force_enabled
        self._parsed = self._root = None
        self._root_done = False
        self.cache = {}  # per-event memo shared by the guards (config, active change, git lookups)

    @property
    def parsed(self):
        if self._parsed is None:
            self._parsed = shellparse.parse(self.payload.command or "", cwd=self.payload.cwd)
        return self._parsed

    @property
    def root(self):
        """The Karvey project root for the payload's cwd, or None (guards then stay inert)."""
        if not self._root_done:
            self._root_done = True
            try:
                self._root = pj.find_root(start=self.payload.cwd or os.getcwd())
            except OSError:
                self._root = None
        return self._root


class Guard:
    __slots__ = ("name", "events", "fail", "default_on", "wired", "run", "enabled")

    def __init__(self, name, events, fail, default_on, wired=False, run=None, enabled=None):
        self.name, self.events, self.fail, self.default_on = name, tuple(events), fail, default_on
        self.wired, self.run, self.enabled = wired, run, enabled

    def is_enabled(self, ctx):
        if ctx.force_enabled:
            return True
        if self.enabled is None:
            return self.default_on
        return bool(self.enabled(ctx))


# --------------------------------------------------------------------------- selftest
def _selftest_enabled(ctx):
    return ctx.env.get(SELFTEST_ENV) == "1"


def _selftest_run(ctx):
    hay = " ".join(x for x in (ctx.payload.command, ctx.payload.file_path_raw) if x)
    if SELFTEST_TOKEN in hay:
        return Decision.block("[karvey] BLOCK selftest: %s found (diagnostic guard, %s=1)" % (SELFTEST_TOKEN,
                                                                                            SELFTEST_ENV))
    return Decision.allow()


# --------------------------------------------------------------------------- registry
REGISTRY = [
    Guard("selftest", ("pre-bash", "pre-edit"), "closed", False, wired=True, run=_selftest_run,
          enabled=_selftest_enabled),
    Guard("protect-paths", ("pre-bash", "pre-edit"), "closed", True, wired=True,
          run=guards.protect_paths),                                    # E1.F5.T1
    Guard("prod-gate", ("pre-bash",), "closed", True),                   # E1.F5.T5, E1.F5.T6
    Guard("git-flow", ("pre-bash",), "closed", False),                   # E1.F5.T4
    Guard("plan-gate", ("pre-bash", "pre-edit"), "closed", False),       # E1.F5.T3
    Guard("spec-write", ("post-edit",), "open", True),                   # E1.F5.T7
    Guard("pending-sync", ("post-edit",), "open", True),                 # E1.F5.T7
    Guard("approval", ("prompt",), "open", True, wired=True, run=guards.approval_hook),  # E1.F5.T2
]


def guards_for(event, only=None):
    names = set(only) if only else None
    return [g for g in REGISTRY if event in g.events and (names is None or g.name in names)]


# --------------------------------------------------------------------------- dispatch
def _audit_block(ctx, guard, message, record=None):
    try:
        # a Karvey project, or at least a git clone (its common dir); never a stray XDG dir for
        # an arbitrary non-project cwd
        base = ctx.root or (ctx.payload.cwd if ctx.payload.cwd and pj.git_common_dir(ctx.payload.cwd) else None)
        if not base:
            return
        rec = {"guard": guard, "event": ctx.event, "decision": "block", "reason": message,
               "session_id": ctx.payload.session_id}
        rec.update(record or {})
        audit.append(pj.state_dir(base), rec)
    except Exception:
        pass  # logging never changes a decision


def _audit_decision(ctx, guard, decision, record=None):
    try:
        base = ctx.root or (ctx.payload.cwd if ctx.payload.cwd and pj.git_common_dir(ctx.payload.cwd) else None)
        if not base:
            return
        rec = {"guard": guard, "event": ctx.event, "decision": decision, "session_id": ctx.payload.session_id}
        rec.update(record or {})
        audit.append(pj.state_dir(base), rec)
    except Exception:
        pass


class _Watchdog:
    """Applies the fail mode of the guard being evaluated when the event budget runs out."""

    def __init__(self, budget_s, out, err, default=None):
        self.current = None
        self.default = default  # the guard whose fail mode applies between guards (a closed, default-on one)
        self.out, self.err = out, err
        self.timer = threading.Timer(budget_s, self._expire)
        self.timer.daemon = True

    def start(self):
        self.timer.start()

    def cancel(self):
        self.timer.cancel()

    def _expire(self):
        g = self.current or self.default
        try:
            if g is not None and g.fail == "closed":
                self.err.write("[karvey] BLOCK %s: cannot decide within the time budget (fail closed)\n" % g.name)
                self.err.flush()
                os._exit(HOOK_BLOCK)
            self.out.flush()
        finally:
            os._exit(HOOK_ALLOW)


def dispatch(event, stdin_text, env=None, only=None, force_enabled=False, out=None, err=None, budget_s=None):
    """Run the guards of ``event``; return the hook exit code (0 allow, 2 block)."""
    out = out or sys.stdout
    err = err or sys.stderr
    env = os.environ if env is None else env
    payload = hookio.parse(stdin_text, env=env)
    ctx = Context(event, payload, env, only=only, force_enabled=force_enabled)
    for g in guards_for(event, only):
        if not g.wired:
            continue  # allow-stub: implemented and wired in batch 3
        try:
            enabled = g.is_enabled(ctx)
        except Exception:
            enabled = g.default_on or g.fail == "closed"
        if not enabled:
            continue
        if not payload.ok:
            if g.fail == "closed":
                msg = "[karvey] BLOCK %s: cannot evaluate: %s (fail closed)" % (g.name, payload.error)
                err.write(msg + "\n")
                _audit_block(ctx, g.name, msg)
                return HOOK_BLOCK
            continue
        started = time.monotonic()
        try:
            d = g.run(ctx)
        except Exception as exc:
            if g.fail == "closed":
                msg = "[karvey] BLOCK %s: cannot evaluate: %s: %s (fail closed)" % (g.name, type(exc).__name__, exc)
                err.write(msg + "\n")
                _audit_block(ctx, g.name, msg)
                return HOOK_BLOCK
            err.write("[karvey] %s not evaluated: %s\n" % (g.name, exc))
            continue
        if d is None:
            continue
        for line in d.stdout:
            out.write(line.rstrip("\n") + "\n")
        if d.decision == "allow" and d.audit:
            _audit_decision(ctx, g.name, "allow", d.record)
        if d.decision == "block":
            err.write(d.message.rstrip("\n") + "\n")
            rec = dict(d.record)
            rec["duration_ms"] = int((time.monotonic() - started) * 1000)
            _audit_block(ctx, g.name, d.message, rec)
            return HOOK_BLOCK
    return HOOK_ALLOW


def main(argv=None):
    ap = argparse.ArgumentParser(prog="karvey_hooks.py", add_help=True)
    ap.add_argument("event")
    ap.add_argument("rest", nargs="*", help=argparse.SUPPRESS)  # e.g. session's startup|resume
    ap.add_argument("--only", action="append", default=[], help="run only these guards (legacy shims)")
    ap.add_argument("--force-enabled", action="store_true", help="treat the selected guards as enabled")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        sys.stderr.write("[karvey] hook dispatcher: bad arguments (not blocking)\n")
        return HOOK_ALLOW
    if args.event not in EVENTS:
        sys.stderr.write("[karvey] unknown hook event %r (not blocking)\n" % args.event)
        return HOOK_ALLOW
    only = [x for item in args.only for x in item.split(",") if x] or None
    if args.event == "session":
        return HOOK_ALLOW  # the session entry point is ported in E1.F6.T1
    closed = [g for g in guards_for(args.event, only) if g.wired and g.fail == "closed" and g.default_on]
    watchdog = _Watchdog(BUDGET_S[args.event], sys.stdout, sys.stderr, default=closed[0] if closed else None)
    watchdog.start()
    try:
        data = sys.stdin.buffer.read(STDIN_MAX) if hasattr(sys.stdin, "buffer") else sys.stdin.read(STDIN_MAX)
        code = _dispatch_watched(watchdog, args.event, data, only, args.force_enabled)
    finally:
        watchdog.cancel()
    sys.stdout.flush()
    sys.stderr.flush()
    return code


def _dispatch_watched(watchdog, event, data, only, force_enabled):
    # the watchdog needs to know which guard is running: wrap each guard's run
    wrapped = []
    for g in REGISTRY:
        if g.run is not None:
            orig = g.run

            def run(ctx, _g=g, _orig=orig):
                watchdog.current = _g
                try:
                    return _orig(ctx)
                finally:
                    watchdog.current = None
            wrapped.append((g, orig))
            g.run = run
    try:
        return dispatch(event, data, only=only, force_enabled=force_enabled)
    finally:
        for g, orig in wrapped:
            g.run = orig


if __name__ == "__main__":
    sys.exit(main())
