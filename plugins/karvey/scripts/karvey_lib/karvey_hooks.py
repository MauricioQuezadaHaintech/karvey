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
import json
import os
import re
import sys
import threading
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from karvey_lib import HOOK_ALLOW, HOOK_BLOCK, atomicio, audit, defaults, guards, hookio, livestate  # noqa: E402
    from karvey_lib import shellparse  # noqa: E402
    from karvey_lib import project as pj  # noqa: E402
else:
    from . import HOOK_ALLOW, HOOK_BLOCK, atomicio, audit, defaults, guards, hookio, livestate, shellparse
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


# --------------------------------------------------------------------------- post-edit (E1.F5.T7)
PENDING_NAME = ".graph-pending"


def _edited(ctx):
    """``(root, path, rel)`` for a PostToolUse on a file inside ``<root>/docs/spec/``, else None."""
    path = ctx.payload.file_path
    if not path:
        return None
    parent = os.path.dirname(path)
    root = pj.find_root(start=parent if os.path.isdir(parent) else ctx.payload.cwd)
    if root is None:
        return None
    spec_dir = os.path.join(os.path.realpath(str(root)), str(pj.SPEC_DIR))
    real = os.path.realpath(path)
    if not (real + "/").startswith(spec_dir.rstrip("/") + "/"):
        return None
    return root, real, os.path.relpath(real, os.path.realpath(str(root))).replace(os.sep, "/")


def spec_write(ctx):
    """Validate a written ``docs/spec/**/spec.json`` or ``docs/spec/project.json`` (REQ-W1-028).
    Violations: exit 2 with the list on stderr (A-4: PostToolUse feeds it back to the session)."""
    hit = _edited(ctx)
    if hit is None:
        return None
    root, path, rel = hit
    name = os.path.basename(path)
    if not (name == "spec.json" or rel == str(pj.PROJECT_JSON).replace(os.sep, "/")):
        return None
    tool = guards.state_tool()
    try:
        loaded = tool.load(path)
        tool.check_schema_version(loaded.data, rel)
        strict = tool.schema_mode(root) == "strict"
        issues = tool.validate_data(loaded.data, tool.kind_of(path), strict, file=rel)
    except tool.NotFound as exc:
        issues = [{"severity": "error", "path": "$", "message": str(exc)}]
    errors = [i for i in issues if i.get("severity") == "error"]
    if not errors:
        return None
    lines = ["[karvey] spec-write: %s has %d violation(s); the write already happened, fix the file "
             "(or use karvey-state.py):" % (rel, len(errors))]
    for i in errors[:20]:
        lines.append("  - %s: %s" % (i.get("path") or "$", i.get("message")))
    if len(errors) > 20:
        lines.append("  … %d more (karvey-state.py validate %s)" % (len(errors) - 20, rel))
    return Decision.block("\n".join(lines), record={"reason": "spec.json invalid", "file": rel})


def pending_sync(ctx):
    """Append the written ``docs/spec/**`` path to ``docs/spec/.graph-pending`` (sorted, deduped,
    LF), never the pending file itself nor ``graphify-out/**`` (REQ-W1-063). Silent."""
    hit = _edited(ctx)
    if hit is None:
        return None
    root, path, rel = hit
    parts = rel.split("/")
    if parts[-1] == PENDING_NAME or "graphify-out" in parts:
        return None
    pending = os.path.join(str(root), str(pj.SPEC_DIR), PENDING_NAME)
    try:
        with open(pending, encoding="utf-8-sig") as fh:
            current = fh.read()
    except FileNotFoundError:
        current = None
    lines = sorted({ln.strip() for ln in (current or "").splitlines() if ln.strip()} | {rel})
    text = "\n".join(lines) + "\n"
    if text != current:
        expected = atomicio.file_sha256(pending) if current is not None else None
        atomicio.write_text_atomic(pending, text, expected_sha256=expected)
    return None


# --------------------------------------------------------------------------- registry
REGISTRY = [
    Guard("selftest", ("pre-bash", "pre-edit"), "closed", False, wired=True, run=_selftest_run,
          enabled=_selftest_enabled),
    Guard("protect-paths", ("pre-bash", "pre-edit"), "closed", True, wired=True,
          run=guards.protect_paths),                                    # E1.F5.T1
    Guard("prod-gate", ("pre-bash",), "closed", True, wired=True, run=guards.prod_gate,
          enabled=guards.prod_gate_enabled),                            # E1.F5.T5, E1.F5.T6
    Guard("git-flow", ("pre-bash",), "closed", False, wired=True, run=guards.git_flow,
          enabled=guards.git_flow_enabled),                             # E1.F5.T4
    Guard("plan-gate", ("pre-bash", "pre-edit"), "closed", False, wired=True, run=guards.plan_gate,
          enabled=guards.plan_gate_enabled),                            # E1.F5.T3
    Guard("trailer", ("pre-bash",), "open", False, wired=True, run=guards.trailer,
          enabled=guards.trailer_enabled),                              # wave2 E1.F5.T4
    Guard("spec-write", ("post-edit",), "open", True, wired=True, run=spec_write),      # E1.F5.T7
    Guard("pending-sync", ("post-edit",), "open", True, wired=True, run=pending_sync),  # E1.F5.T7
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
    deferred = HOOK_ALLOW
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
            if g.name == "spec-write":
                err.write("[karvey] spec.json not validated: %s: %s\n" % (type(exc).__name__, exc))
            elif g.name != "pending-sync":  # pending-sync is silent (§3.2); archive recomputes from git
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
            if event == "post-edit":  # the write already happened: the other recorders still run
                deferred = HOOK_BLOCK
                continue
            return HOOK_BLOCK
    return deferred


# --------------------------------------------------------------------------- session (E1.F6.T1)
# Port of the 3.11.4 karvey-session-context.sh (BUG-18..21 fixes kept): identity, rules, board,
# checklist and handoff reinjected; live repo state measured against state.json; the instruction
# to run /karvey-checkpoint restore. Changes (REQ-W1-045..047): the active change comes from
# project.active_change (archive/ and IMPLEMENTED excluded, H-08); compact manifest XOR full
# (H-09); open board rows <= 40 and handoff <= 6 KB, each with a truncation notice; the text is
# emitted as hookSpecificOutput.additionalContext (A-6).
_SEPARATOR = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_DONE_CELL = re.compile(r"\|\s*done\s*\|", re.I)
_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s+")


def _read(path, limit=None):
    try:
        with open(path, "rb") as fh:
            data = fh.read() if limit is None else fh.read(limit)
    except OSError:
        return None
    return data.decode("utf-8", "replace")


def _is_done(line):
    return "\u2705" in line or bool(_DONE_CELL.search(line)) or bool(re.match(r"^\s*[-*+]\s+\[[xX]\]", line))


def bound_board(text, path, max_rows):
    """Only the open rows (table rows and list items not marked ✅ / done / [x]), at most
    ``max_rows``; headings, table headers and separators kept; then ``… N more open rows``."""
    lines = text.splitlines()
    out, kept, more, done = [], 0, 0, 0
    for i, ln in enumerate(lines):
        st = ln.strip()
        is_row = st.startswith("|")
        header = is_row and i + 1 < len(lines) and _SEPARATOR.match(lines[i + 1].strip() or "x")
        if is_row and (_SEPARATOR.match(st) or header):
            out.append(ln)
            continue
        if is_row or _ITEM.match(ln):
            if _is_done(ln):
                done += 1
                continue
            if kept >= max_rows:
                more += 1
                continue
            kept += 1
        out.append(ln)
    if more:
        out.append("\u2026 %d more open rows in %s" % (more, path))
    if done:
        out.append("(%d done rows not shown)" % done)
    return "\n".join(out)


def bound_text(text, path, max_bytes):
    """At most ``max_bytes`` of ``text``, cut at a line boundary, with the truncation notice."""
    data = text.encode("utf-8")
    if len(data) <= max_bytes:
        return text
    cut = data[:max_bytes].decode("utf-8", "ignore")
    if "\n" in cut:
        cut = cut[:cut.rfind("\n")]
    return "%s\n\u2026 truncated (%.1f KB of %.1f KB) \u2014 full file: %s" % (
        cut, len(cut.encode("utf-8")) / 1024.0, len(data) / 1024.0, path)


def _legacy_kv(cfg):
    kv = {}
    for ln in (_read(cfg) or "").splitlines():
        if "=" in ln and not ln.lstrip().startswith("#"):
            k, _, v = ln.partition("=")
            kv.setdefault(k.strip(), v.strip())
    return kv


def resolve_profile(root, cfg, kind, top):
    """``(name, role, profile, board)`` — the 3.11.4 resolution (BUG-19 layouts)."""
    name, role = "", "solo"
    profile = os.path.join(root, "docs", "spec", "agent")
    board = os.path.join(profile, "board.md")
    if kind == "team":
        try:
            d = json.loads(_read(cfg) or "")
        except ValueError:
            d = None
        if isinstance(d, dict):
            roles = d.get("roles") if isinstance(d.get("roles"), dict) else {}
            role = roles.get(top) or (roles.get(os.path.basename(root)) if not top else None) or "ceo"
            names = d.get("display_names") if isinstance(d.get("display_names"), dict) else {}
            name = names.get(role) or "agent-%s-%s" % (d.get("code", ""), role)
            ops = str(d.get("ops_repo", "") or "")
        else:
            role, ops = "ceo", ""
        if ops and ops != os.path.basename(root) and os.path.isdir(os.path.join(root, ops)):
            opsdir = os.path.join(root, ops)
        else:
            opsdir = os.path.dirname(cfg)
        profile = os.path.join(opsdir, "agents", role)
        board = os.path.join(opsdir, "board", role + ".md")
    elif kind == "legacy":
        kv = _legacy_kv(cfg)
        code = kv.get("CODIGO") or kv.get("CODE") or ""
        ops = kv.get("OPS", "")
        role = kv.get("AGENTE_%s" % top) or kv.get("AGENT_%s" % top) or "ceo"
        name = kv.get("NOMBRE_%s" % role) or kv.get("NAME_%s" % role) or "agent-%s-%s" % (code, role)
        profile = os.path.join(root, ops, "agents", role)
        board = os.path.join(root, ops, "board", role + ".md")
    return name or os.path.basename(root), role, profile, board


def live_state(state_path, root):
    """``(lines, drift)`` comparing state.json with the measured repositories."""
    try:
        d = json.loads(_read(state_path) or "")
    except ValueError:
        return ["state.json unreadable \u2014 treat the handoff as unverified."], True
    if not isinstance(d, dict):
        return ["state.json unreadable \u2014 treat the handoff as unverified."], True
    out, drift = [], False
    for r in d.get("repos") or []:
        if not isinstance(r, dict):
            continue
        p = r.get("path", "")
        if r.get("measured") is False:
            out.append("  %s: not measured at save (%s) \u2014 verify it by hand." % (p, r.get("reason", "no reason")))
            drift = True
            continue
        rp = livestate.resolve(root, p)
        if not livestate.is_repo(rp):
            out.append("  %s: NOT FOUND at %s \u2014 the handoff describes a tree that is not here." % (p, rp))
            drift = True
            continue
        m, why = livestate.measure(rp)
        if m is None:
            out.append("  %s: cannot measure (%s)." % (p, why))
            drift = True
            continue
        marks = []
        # BUG-22: commits since the save that touch only the profile's own files are the save itself
        # finishing (state.json committed after the capture); then a lower uncommitted count matches too.
        profile_only = (m["branch"] == r.get("branch") and m["commit"] != r.get("commit")
                        and livestate.profile_only_since(rp, r.get("commit"), os.path.dirname(state_path)))
        rec_un = r.get("uncommitted")
        if m["branch"] != r.get("branch"):
            marks.append("branch %s -> %s" % (r.get("branch"), m["branch"]))
        if m["commit"] != r.get("commit") and not profile_only:
            marks.append("commit %s -> %s" % (r.get("commit"), m["commit"]))
        if m["uncommitted"] != rec_un and not (profile_only and isinstance(rec_un, int)
                                               and not isinstance(rec_un, bool) and m["uncommitted"] <= rec_un):
            marks.append("uncommitted %s -> %s" % (rec_un, m["uncommitted"]))
        if marks:
            out.append("  %s: DRIFT \u2014 %s" % (p, " \u00b7 ".join(marks)))
            drift = True
        elif profile_only:
            out.append("  %s: matches (%s @%s; profile-only commits since the save)" % (p, m["branch"], m["commit"]))
        else:
            out.append("  %s: matches (%s @%s)" % (p, m["branch"], m["commit"]))
    if d.get("saved_at"):
        out.append("  saved_at: %s" % d["saved_at"])
    if d.get("scheduled_tasks"):
        out.append("  scheduled tasks to recreate: %s (they died with the reset)" % d["scheduled_tasks"])
    if d.get("ready_to_rotate"):
        out.append("  this agent had already declared itself ready to rotate.")
    return out, drift


def _settings_gaps(data):
    """``(missing, legacy)`` of a project.json object: ``notifications`` / ``management`` that are
    absent or empty (``{}`` counts as missing), and the legacy shapes that count as present."""
    missing, legacy = [], []
    for k in ("notifications", "management"):
        v = data.get(k)
        if k == "management" and isinstance(v, str) and v.strip():
            legacy.append('management: "%s"' % v)
        elif not isinstance(v, dict) or not v:
            missing.append(k)
    return missing, legacy


def settings_notice(start, team_root, mode, env):
    """The team-settings line (REQ-ADP-003 as amended by REQ-W1-050 and REQ-W1-083), or None.

    Only on ``startup``; only in a Karvey project found by walking up no further than the git
    top level; the settings count as present when the working copy **or** ``project.json`` on
    ``origin/{integration}`` (local ref, no fetch) has them."""
    if mode != "startup":
        return None
    kp = pj.find_root(start=start)  # REQ-W1-050: walk up no further than the git top level
    if kp is None and team_root and pj.is_karvey_project(team_root):
        kp = team_root
    if kp is None:
        return None
    data, err = pj.load_project_json(kp)
    legacy = []
    if err == "missing":
        missing = ["no project.json"]
    elif data is None:
        missing = ["project.json is not an object" if "not an object" in (err or "") else "project.json unreadable"]
    else:
        missing, legacy = _settings_gaps(data)
    if missing:
        _, integ, _ = pj.branch_flow(data or {})
        for ref in [x for x in (integ, _origin_head(kp)) if x]:
            rdata, status = pj.read_reviewed_project_json(kp, production=ref)
            if status == "ok":
                rmissing, rlegacy = _settings_gaps(rdata)
                if not rmissing:
                    return None if not rlegacy else _legacy_line(rlegacy, " on origin/%s" % ref)
                break
    if missing:
        return ("Karvey (info): team settings not set (%s). To set them, the user can run "
                "`/karvey:karvey-init --settings` \u2014 settings only, it creates no change and nothing in any "
                "tracker." % " + ".join(missing + legacy))
    if legacy:
        return _legacy_line(legacy, "")
    return None


def _legacy_line(legacy, where):
    return ("Karvey (info): team settings in a legacy shape (%s)%s \u2014 run `karvey-state.py validate --fix` "
            "to migrate them." % (", ".join(legacy), where))


def _origin_head(root):
    rc, out = pj.git(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], root)
    return out[len("origin/"):] if rc == 0 and out.startswith("origin/") else None


def open_work_block(kroot):
    """The bounded open-work lines of the session context: open questions (overdue first) and open risks of
    active changes, at most five lines per list plus ``+N more — karvey-context`` (F-50, REQ-W3-030); ``[]``
    when there is nothing open or anything fails (the session hook informs, never breaks)."""
    try:
        from datetime import datetime
        try:
            from karvey_lib import risks as rsk
        except ImportError:  # pragma: no cover - package import
            from . import risks as rsk
        active = [c["id"] for c in pj.list_changes(kroot)
                  if not c["implemented"] and c["phase"] not in pj.INACTIVE_PHASES]
        ql, rl = rsk.open_work_lines(kroot, datetime.now().astimezone().date().isoformat(), active, cap=5)
    except Exception:  # noqa: BLE001
        return []
    out = []
    if ql:
        out += ["", "=== Open questions ==="] + ql
    if rl:
        out += ["", "=== Open risks (active changes) ==="] + rl
    return out


def session_text(mode, env):
    """The SessionStart context as text ('' when there is nothing to say)."""
    start = env.get("CLAUDE_PROJECT_DIR") or env.get("PWD") or os.getcwd()
    try:
        start = os.path.realpath(os.path.abspath(start))
    except (OSError, ValueError):
        return ""
    if not os.path.isdir(start):
        return ""
    cfg_d = defaults().get("session", {})
    max_rows, max_bytes = int(cfg_d.get("board_rows_max", 40)), int(cfg_d.get("handoff_bytes_max", 6144))
    root, cfg, kind = livestate.find_team_root(start)
    out = []
    if root is None:
        n = settings_notice(start, None, mode, env)
        kp = pj.find_root(start=start)
        ow = open_work_block(kp) if kp else []
        return "\n".join(([n] if n else []) + ow).strip("\n")
    rel = os.path.relpath(start, root) if start != root else ""
    top = rel.split(os.sep, 1)[0] if rel and not rel.startswith("..") else ""
    name, role, profile, board = resolve_profile(root, cfg, kind, top)
    handoff, state = os.path.join(profile, "handoff.md"), os.path.join(profile, "state.json")
    out.append("=== Karvey \u2014 session context (%s) ===" % kind)
    out.append("You are `%s`%s. Profile: %s" % (name, " (role: %s)" % role if role != "solo" else "", profile))

    def emit(path, title, body=None):
        text = body if body is not None else _read(path)
        if text is None:
            return
        out.append("")
        out.append("=== %s ===" % title)
        out.append(text.rstrip("\n"))

    compact = next((c for c in (os.path.join(profile, "manifest-compact.md"),
                                os.path.join(os.path.dirname(profile), "manifest-compact.md")) if os.path.isfile(c)), None)
    if not os.path.isdir(profile):
        out.append("")
        out.append("(profile directory not found: %s \u2014 nothing to reinject; run `/karvey-checkpoint save` to "
                   "create it)" % profile)
    elif not os.path.isfile(handoff):
        out.append("")
        out.append("(no handoff at %s \u2014 the previous session did not save one)" % handoff)
    if compact:
        emit(compact, "Compact manifest")     # compact XOR full (H-09, REQ-W1-046)
    else:
        emit(os.path.join(profile, "manifest.md"), "Manifest (%s)" % name)
    emit(os.path.join(profile, "checklist.md"), "Closing checklist")
    btext = _read(board)
    if btext is not None:
        emit(board, "Board", bound_board(btext, board, max_rows))
    htext = _read(handoff)
    if htext is not None:
        emit(handoff, "Handoff", bound_text(htext, handoff, max_bytes))
    drift = False
    if os.path.isfile(state):
        out.append("")
        out.append("=== Live state vs. what the handoff claims ===")
        lines, drift = live_state(state, root)
        out.extend(lines)
    elif os.path.isfile(handoff):
        out.append("")
        out.append("(no state.json beside the handoff: nothing was measured, so treat every claim in it as unverified)")
        drift = True
    kroot = root if pj.is_karvey_project(root) else pj.find_root(start=start)
    act = pj.active_change(kroot) if kroot else {"change": None, "reason": "none", "candidates": []}
    n = settings_notice(start, root, mode, env)
    if n:
        out.append(n)
    if kroot:
        out.extend(open_work_block(kroot))
    out.append("")
    out.append("=== First action ===")
    if act["change"] or drift or not os.path.isfile(handoff):
        line = "Run `/karvey-checkpoint restore` BEFORE anything else"
        if act["change"]:
            line += " (active change: %s)" % act["change"]
        out.append(line + ".")
        out.append("It contrasts the rest, crosses open questions against the decision log, recreates the")
        out.append("scheduled tasks and proposes the next step. A hook cannot do any of that.")
    else:
        out.append("Nothing pending to restore. Re-read the board before starting.")
    if act["reason"] == "several":
        out.append("(several active changes: %s \u2014 none selected)" % ", ".join(act["candidates"]))
    return "\n".join(out)


def session_main(mode, env=None, out=None):
    """SessionStart entry point: always exit 0 (it informs, never gates)."""
    env = os.environ if env is None else env
    out = out or sys.stdout
    try:
        text = session_text(mode, env)
    except Exception as exc:  # open: a broken session hook must not break the session
        text = "[karvey] session context unavailable: %s: %s" % (type(exc).__name__, exc)
    if text:
        out.write(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
                             ensure_ascii=False) + "\n")
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
        mode = args.rest[0] if args.rest else "startup"
        return session_main(mode if mode in ("startup", "resume") else "startup")
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
