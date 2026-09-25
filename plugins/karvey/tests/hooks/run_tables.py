#!/usr/bin/env python3
"""Guard-table runner (architecture §6.1, REQ-W1-030). Python 3 standard library only.

    python3 plugins/karvey/tests/hooks/run_tables.py [--tag T]… [--only TABLE]… [--junit PATH] [-v]

Every case of ``tables/*.json`` runs the real dispatcher (``hooks/karvey-hook.sh``) with a payload
on stdin, inside a throw-away world built for that case:

- ``given.repo``: a ``git init`` repository with a **bare origin** (so ``origin/*`` refs are real,
  ``origin/HEAD`` included), ``docs/spec/project.json``, change ``spec.json`` files, extra files,
  branches pushed to the origin, and the checked-out branch;
- ``given.ledger`` / ``given.marker``: machine-local state written under
  ``<git-common-dir>/karvey/`` (a marker may be ``{"@valid": "plan|prod", "age_min": N}``, a raw
  object or ``""`` for an empty ``touch`` file);
- ``given.stubs``: canned output for the ``gh`` / ``az`` / ``glab`` stubs put first on ``PATH``;
- an isolated ``HOME``, ``XDG_STATE_HOME`` and git config.

Case format (§6.1)::

    {"id", "guard", "given": {"repo": {"branch", "remote_branches", "project_json", "spec": {id: obj},
                                       "ledger": {id: obj}, "marker": {scope: …}, "files": {path: text}},
                              "cwd", "env", "stubs": {"gh": {"stdout", "stderr", "rc", "sleep"}}},
     "input": {"tool_name", "tool_input"} | {"prompt"}, "event"?,
     "expect": {"decision": "allow|block", "stdout_contains"?, "stderr_contains"?, "stdout_empty"?,
                "stderr_empty"?, "marker_created"?, "max_s"?},
     "expect_nopy"?: {…}, "tags": […], "limitation"?: true}

Strings may use ``{{root}}`` (the case's repo), ``{{repo}}`` (its git common dir), ``{{home}}``,
``{{plugin}}`` (the plugin root under test),
``{{now}}`` and ``{{now-121m}}``-style offsets.

Statusline cases (``"event": "statusline"``) run ``hooks/karvey-statusline.sh`` instead, with
``input.stdin`` (an object) as its stdin; the script always exits 0, so their decision is ``allow``.
``given.script_copy: true`` runs a copy of the script from the case's temp dir, where
``defaults.json`` cannot be found (the ``rot?`` case, REQ-W1-049).

Session cases and the project-upgrade offer: every repository gets a seen-version record equal to the
installed version (so the once-per-version offer stays silent, as before the offer existed) unless the
case sets ``given.seen_version``: ``null`` = no record, a version string = resolved ``accepted`` for it,
or ``{"version", "resolution"}`` (``"@installed"`` = the plugin version). ``{{installed}}`` expands to
the plugin version. ``given.plugin_copy: {path: text}`` runs the session hook from a copy of the plugin
with those files replaced (e.g. a broken step catalogue).

Assertions: the decision (exit 0 allow, 2 block), the stdout/stderr substrings, ``marker_created``
and a duration below 1 s per case unless tagged ``network`` or given ``max_s``. Cases tagged
``nopy`` run a second time with ``PATH`` stripped of every python interpreter, which exercises the
dispatcher's bash-only fail modes (§3.2).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent.parent
DISPATCHER = PLUGIN_ROOT / "hooks" / "karvey-hook.sh"
STATUSLINE = PLUGIN_ROOT / "hooks" / "karvey-statusline.sh"
TABLES = HERE / "tables"
STUBS = HERE / "stubs"
# The bash on PATH, resolved once: on Windows CreateProcess searches System32 before PATH, so a bare
# "bash" runs WSL's bash.exe instead of Git Bash (F-43).
BASH = shutil.which("bash") or "bash"
# Multiplies every case's time limit; the Windows CI job sets 2 (slower process start-up, F-46).
try:
    TIME_FACTOR = max(1.0, float(os.environ.get("KARVEY_TABLES_TIME_FACTOR") or 1))
except ValueError:
    TIME_FACTOR = 1.0
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
from karvey_lib import approval  # noqa: E402
from karvey_lib import __version__ as INSTALLED  # noqa: E402

CASE_KEYS = {"id", "guard", "given", "input", "event", "expect", "expect_nopy", "tags", "limitation", "note",
             "command"}
GIVEN_KEYS = {"repo", "cwd", "env", "stubs", "dir", "outer_files", "no_python", "setup", "script_copy", "seen_version",
              "plugin_copy"}
REPO_KEYS = {"branch", "remote_branches", "project_json", "spec", "ledger", "marker", "files", "default_branch",
             "wc_files", "origin_files", "git_config", "at", "worktree", "no_origin", "commit_files"}
EXPECT_KEYS = {"decision", "stdout_contains", "stderr_contains", "stdout_not_contains", "stderr_not_contains",
               "stdout_empty", "stderr_empty", "marker_created", "max_s", "marker", "files_exist",
               "files_absent", "file_contains", "context_contains", "context_not_contains", "context_max_bytes",
               "structured"}
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SESSION = "00000000-0000-0000-0000-000000000000"
SESSION_HOOK = PLUGIN_ROOT / "hooks" / "karvey-session-context.sh"
_PY = re.compile(r"^(python|py)(\d[\d.]*)?(-config)?(\.exe)?$")


class CaseError(Exception):
    pass


def git(args, cwd, env):
    cp = subprocess.run(["git"] + args, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if cp.returncode != 0:
        raise CaseError("git %s failed: %s" % (" ".join(args), cp.stderr.decode("utf-8", "replace").strip()))
    return cp.stdout.decode("utf-8", "replace").strip()


def base_env(tmp):
    home = tmp / "home"
    home.mkdir(exist_ok=True)
    env = {
        "HOME": str(home), "XDG_STATE_HOME": str(tmp / "xdg"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "Karvey Table", "GIT_AUTHOR_EMAIL": "table@example.invalid",
        "GIT_COMMITTER_NAME": "Karvey Table", "GIT_COMMITTER_EMAIL": "table@example.invalid",
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "TMPDIR": str(tmp),
    }
    return env


class Templ:
    def __init__(self, root=None, repo=None, home=None):
        self.root, self.repo, self.home = root, repo, home
        self.plugin = PLUGIN_ROOT
        self.tmp = None
        self.python = sys.executable  # for setup commands, also in the nopy pass
        self.now = datetime.now().astimezone()

    def s(self, text):
        if not isinstance(text, str):
            return text

        def now(m):
            sign, n, unit = m.group(1), int(m.group(2)), m.group(3)
            delta = timedelta(minutes=n) if unit == "m" else timedelta(hours=n)
            return (self.now + delta if sign == "+" else self.now - delta).isoformat(timespec="seconds")
        text = re.sub(r"\{\{now([+-])(\d+)([mh])\}\}", now, text)
        text = text.replace("{{now}}", self.now.isoformat(timespec="seconds"))
        text = text.replace("{{installed}}", INSTALLED)
        for k in ("root", "repo", "home", "plugin", "tmp", "python"):
            v = getattr(self, k)
            if v is not None:
                text = text.replace("{{%s}}" % k, str(v))
        return text

    def deep(self, obj):
        if isinstance(obj, dict):
            return {self.s(k): self.deep(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.deep(v) for v in obj]
        return self.s(obj)


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_repo(spec, tmp, env):
    root = tmp / spec.get("at", "repo")
    root.mkdir(parents=True)
    default = spec.get("default_branch", "main")
    git(["init", "-q", "-b", default], root, env)
    git(["config", "commit.gpgsign", "false"], root, env)
    t = Templ(root=root, home=env["HOME"])
    t.tmp = tmp
    if "project_json" in spec and spec["project_json"] is not None:
        write_file(root / "docs/spec/project.json", t.deep(spec["project_json"]))
    for cid, data in (spec.get("spec") or {}).items():
        write_file(root / "docs/spec/changes" / cid / "spec.json", t.deep(data))
    for rel, content in (spec.get("files") or {}).items():
        write_file(root / rel, t.deep(content))
    for k, v in (spec.get("git_config") or {}).items():
        git(["config", k, v], root, env)
    git(["add", "-A"], root, env)
    git(["commit", "-q", "--allow-empty", "-m", "table fixture"], root, env)
    if spec.get("no_origin"):
        return _finish_repo(spec, root, tmp, env, t, default)
    bare = tmp / "origin.git"
    git(["init", "-q", "--bare", "-b", default, str(bare)], tmp, env)
    git(["remote", "add", "origin", str(bare)], root, env)
    git(["push", "-q", "origin", default], root, env)
    for b in spec.get("remote_branches") or []:
        if b != default:
            git(["push", "-q", "origin", "HEAD:refs/heads/%s" % b], root, env)
    for ob, files in (spec.get("origin_files") or {}).items():
        git(["checkout", "-q", "-b", "karvey-table-origin-tmp"], root, env)
        for rel, content in files.items():
            write_file(root / rel, t.deep(content))
        git(["add", "-A"], root, env)
        git(["commit", "-q", "--allow-empty", "-m", "origin-only fixture"], root, env)
        git(["push", "-q", "-f", "origin", "HEAD:refs/heads/%s" % ob], root, env)
        git(["checkout", "-q", default], root, env)
        git(["branch", "-q", "-D", "karvey-table-origin-tmp"], root, env)
    git(["fetch", "-q", "origin"], root, env)
    git(["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/%s" % default], root, env)
    return _finish_repo(spec, root, tmp, env, t, default)


def _finish_repo(spec, root, tmp, env, t, default):
    branch = spec.get("branch", default)
    if branch != default:
        git(["checkout", "-q", "-b", branch], root, env)
    common = Path(os.path.realpath(str(root / ".git")))
    t.repo = common
    for cid, data in (spec.get("ledger") or {}).items():
        d = common / "karvey" / "ledger"
        d.mkdir(parents=True, exist_ok=True, mode=0o700)
        write_file(d / (cid + ".json"), t.deep(data))
    for scope, data in (spec.get("marker") or {}).items():
        if isinstance(data, dict) and "@valid" in data:
            age = int(data.get("age_min", 0))
            approval.write_marker(root, data["@valid"], scope, data.get("prompt", "aprobado"),
                                  now=approval.now_dt() - timedelta(minutes=age), compat="")
            continue
        d = common / "karvey" / "approvals"
        d.mkdir(parents=True, exist_ok=True, mode=0o700)
        write_file(d / (scope + ".json"), t.deep(data) if not isinstance(data, str) else data)
    if spec.get("commit_files"):
        for rel, content in spec["commit_files"].items():
            write_file(root / rel, t.deep(content))
        git(["add", "-A"], root, env)
        git(["commit", "-q", "-m", "branch fixture"], root, env)
    for rel, content in (spec.get("wc_files") or {}).items():
        write_file(root / rel, t.deep(content))
    if spec.get("worktree"):
        wt = tmp / spec["worktree"]
        git(["worktree", "add", "-q", "-b", "wt-" + spec["worktree"], str(wt)], root, env)
    return root, common, t


def seed_seen(given, root, common, env):
    """The seen-version record of the project-upgrade offer (see the module docstring)."""
    if "seen_version" in given:
        sv = given["seen_version"]
        if sv is None:
            return
        rec = dict(sv) if isinstance(sv, dict) else {"version": sv, "resolution": "accepted"}
    else:
        rec = {"version": "@installed", "resolution": "accepted"}
    if rec.get("version") == "@installed":
        rec["version"] = INSTALLED
    data = {"v": 1, "version": rec["version"], "resolution": rec.get("resolution", "accepted"),
            "at": datetime.now().astimezone().isoformat(timespec="seconds"), "by": None, "from": None}
    if common is not None:
        d = common / "karvey"
    else:  # outside git: the XDG fallback of project.state_dir
        key = hashlib.sha256(os.path.realpath(str(root)).encode("utf-8")).hexdigest()[:16]
        d = Path(env["XDG_STATE_HOME"]) / "karvey" / key
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    write_file(d / "seen-version", data)


def plugin_copy(files, tmp, t):
    """A copy of the plugin (hooks, scripts, schemas, manifest) with ``files`` replaced."""
    dst = tmp / "plugin-copy"
    for part in ("hooks", "scripts", "schemas", ".claude-plugin"):
        shutil.copytree(str(PLUGIN_ROOT / part), str(dst / part),
                        ignore=shutil.ignore_patterns("__pycache__", "tests"))
    for rel, content in (files or {}).items():
        write_file(dst / rel, t.deep(content))
    return dst


def approvals_snapshot(common):
    if common is None:
        return {}
    d = common / "karvey" / "approvals"
    if not d.is_dir():
        return {}
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in d.glob("*.json")}


def nopy_path(tmp, stubs_dir):
    """A PATH with every executable of the current PATH except the python interpreters."""
    if os.name == "nt":
        # Symlinks need a privilege Windows runners lack, and Git Bash's tools need their DLLs beside
        # them: drop every PATH directory that holds an interpreter instead (F-45). Git's usr\bin has none.
        keep = [str(stubs_dir)]
        for part in os.environ.get("PATH", "").split(os.pathsep):
            try:
                if part and os.path.isdir(part) and not any(_PY.match(n.lower()) for n in os.listdir(part)):
                    keep.append(part)
            except OSError:
                continue
        return os.pathsep.join(keep)
    d = tmp / "nopy-bin"
    if d.is_dir():
        return "%s:%s" % (stubs_dir, d)
    d.mkdir()
    for part in os.environ.get("PATH", "").split(os.pathsep):
        if not part or not os.path.isdir(part):
            continue
        try:
            names = os.listdir(part)
        except OSError:
            continue
        for n in names:
            if _PY.match(n) or (d / n).exists():
                continue
            src = os.path.join(part, n)
            if os.path.isfile(src) and os.access(src, os.X_OK):
                try:
                    os.symlink(src, str(d / n))
                except OSError:
                    pass
    return "%s:%s" % (stubs_dir, d)


def check_keys(case):
    bad = set(case) - CASE_KEYS
    if bad:
        raise CaseError("unknown case keys %s" % sorted(bad))
    given = case.get("given") or {}
    if set(given) - GIVEN_KEYS:
        raise CaseError("unknown given keys %s" % sorted(set(given) - GIVEN_KEYS))
    if set(given.get("repo") or {}) - REPO_KEYS:
        raise CaseError("unknown repo keys %s" % sorted(set(given["repo"]) - REPO_KEYS))
    for k in ("expect", "expect_nopy"):
        if k in case and set(case[k]) - EXPECT_KEYS:
            raise CaseError("unknown %s keys %s" % (k, sorted(set(case[k]) - EXPECT_KEYS)))
    if (case.get("expect") or {}).get("decision") not in ("allow", "block"):
        raise CaseError("expect.decision must be allow or block")


def event_of(case):
    if case.get("event"):
        return case["event"]
    if "source" in (case.get("input") or {}):
        return "session"
    inp = case.get("input") or {}
    if "prompt" in inp:
        return "prompt"
    if inp.get("tool_name") == "Bash":
        return "pre-bash"
    if inp.get("tool_name") in EDIT_TOOLS:
        return "pre-edit"
    raise CaseError("cannot infer the event (set 'event')")


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def assert_files(expect, t, common):
    """``marker: {scope, kind, excerpt?}`` · ``files_exist`` / ``files_absent`` · ``file_contains: {path: s}``."""
    problems = []
    m = expect.get("marker")
    if m:
        p = (common / "karvey" / "approvals" / (m["scope"] + ".json")) if common else None
        try:
            data = json.loads(p.read_text(encoding="utf-8")) if p else None
        except (OSError, ValueError):
            data = None
        if not isinstance(data, dict):
            problems.append("no marker for scope %s" % m["scope"])
        else:
            for k in ("kind", "prompt_excerpt", "ttl_min"):
                if k in m and data.get(k) != m[k]:
                    problems.append("marker %s=%r, expected %r" % (k, data.get(k), m[k]))
            if len(data.get("prompt_excerpt", "")) > 80:
                problems.append("marker excerpt longer than 80 characters")
    for f in _as_list(expect.get("files_exist")):
        if not Path(t.s(f)).exists():
            problems.append("missing file %s" % t.s(f))
    for f in _as_list(expect.get("files_absent")):
        if Path(t.s(f)).exists():
            problems.append("unexpected file %s" % t.s(f))
    for f, sub in (expect.get("file_contains") or {}).items():
        try:
            text = Path(t.s(f)).read_text(encoding="utf-8")
        except OSError:
            text = None
        for x in _as_list(sub):
            if text is None or t.s(x) not in text:
                problems.append("%s lacks %r" % (t.s(f), x))
    return problems


def assert_context(expect, out):
    """SessionStart: ``structured`` (one hookSpecificOutput JSON object) and the context text."""
    keys = ("context_contains", "context_not_contains", "context_max_bytes", "structured")
    if not any(k in expect for k in keys):
        return []
    problems = []
    ctx_text = None
    try:
        obj = json.loads(out) if out.strip() else None
        hso = obj.get("hookSpecificOutput") if isinstance(obj, dict) else None
        if isinstance(hso, dict) and hso.get("hookEventName") == "SessionStart":
            ctx_text = hso.get("additionalContext")
    except ValueError:
        obj = None
    if expect.get("structured") and not isinstance(ctx_text, str):
        problems.append("stdout is not one hookSpecificOutput SessionStart object")
    text = ctx_text if isinstance(ctx_text, str) else out
    for x in _as_list(expect.get("context_contains")):
        if x not in text:
            problems.append("context lacks %r" % x)
    for x in _as_list(expect.get("context_not_contains")):
        if x in text:
            problems.append("context has %r" % x)
    if "context_max_bytes" in expect and len(text.encode("utf-8")) > expect["context_max_bytes"]:
        problems.append("context is %d bytes (max %d)" % (len(text.encode("utf-8")), expect["context_max_bytes"]))
    return problems


def assert_expect(expect, rc, out, err, created, duration, tags):
    problems = assert_context(expect, out)
    want = expect["decision"]
    got = {0: "allow", 2: "block"}.get(rc, "rc=%d" % rc)
    if got != want:
        problems.append("decision %s, expected %s" % (got, want))
    for s in _as_list(expect.get("stdout_contains")):
        if s not in out:
            problems.append("stdout lacks %r" % s)
    for s in _as_list(expect.get("stderr_contains")):
        if s not in err:
            problems.append("stderr lacks %r" % s)
    for s in _as_list(expect.get("stdout_not_contains")):
        if s in out:
            problems.append("stdout has %r" % s)
    for s in _as_list(expect.get("stderr_not_contains")):
        if s in err:
            problems.append("stderr has %r" % s)
    if expect.get("stdout_empty") and out.strip():
        problems.append("stdout not empty")
    if expect.get("stderr_empty") and err.strip():
        problems.append("stderr not empty")
    if "marker_created" in expect and bool(expect["marker_created"]) != created:
        problems.append("marker_created %s, expected %s" % (created, expect["marker_created"]))
    limit = expect.get("max_s", None if "network" in tags else 1.0)
    if limit is not None:
        limit *= TIME_FACTOR
    if limit is not None and duration >= limit:
        problems.append("took %.2f s (limit %.2f s)" % (duration, limit))
    return problems


def run_case(case, nopy=False, keep=False):
    """Returns ``(problems, detail)``."""
    tmp = Path(tempfile.mkdtemp(prefix="karvey-table-"))
    try:
        env = base_env(tmp)
        given = case.get("given") or {}
        root = common = None
        t = Templ(home=env["HOME"])
        for rel, content in (given.get("outer_files") or {}).items():
            write_file(tmp / rel, Templ(home=env["HOME"]).deep(content))
        if given.get("repo") is not None:
            root, common, t = build_repo(given["repo"], tmp, env)
        else:
            root = tmp / given.get("dir", "plain")
            root.mkdir(parents=True, exist_ok=True)
        t.tmp = tmp
        cwd_s = t.s(given.get("cwd", "."))
        cwd = (Path(cwd_s) if cwd_s.startswith("/") else root / cwd_s).resolve()
        cwd.mkdir(parents=True, exist_ok=True)
        stub_data = tmp / "stub-data"
        stub_data.mkdir()
        for name, spec in (given.get("stubs") or {}).items():
            for k in ("stdout", "stderr", "rc", "sleep"):
                if k in spec:
                    v = spec[k]
                    (stub_data / ("%s.%s" % (name, k))).write_text(
                        t.s(v) if isinstance(v, str) else (json.dumps(v) if k in ("stdout", "stderr") else str(v)),
                        encoding="utf-8")
        seed_seen(given, root, common, env)
        session_hook = SESSION_HOOK
        if given.get("plugin_copy"):
            session_hook = plugin_copy(given["plugin_copy"], tmp, t) / "hooks" / SESSION_HOOK.name
        env["PATH"] = nopy_path(tmp, STUBS) if nopy else os.pathsep.join((str(STUBS), env["PATH"]))
        env.update({"CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "CLAUDE_PROJECT_DIR": str(cwd),
                    "KARVEY_STUB_DATA": str(stub_data)})
        for k, v in (given.get("env") or {}).items():
            if v is None:
                env.pop(k, None)  # e.g. a settings.json hook runs without CLAUDE_PLUGIN_ROOT
            else:
                env[k] = t.s(v)
        event = event_of(case)
        inp = t.deep(case.get("input") or {})
        for cmd in _as_list(given.get("setup")):
            sp = subprocess.run([BASH, "-c", t.s(cmd)], cwd=str(root), env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=60)
            if sp.returncode != 0:
                raise CaseError("setup %r failed: %s" % (cmd, sp.stderr.decode("utf-8", "replace").strip()))
        payload = {"session_id": SESSION, "transcript_path": "", "cwd": str(cwd)}
        if event == "session":
            payload.update(hook_event_name="SessionStart", source=inp.get("source", "startup"))
        elif event == "prompt":
            payload.update(hook_event_name="UserPromptSubmit", prompt=inp.get("prompt", ""))
        else:
            payload.update(hook_event_name="PostToolUse" if event == "post-edit" else "PreToolUse",
                           tool_name=inp.get("tool_name"), tool_input=inp.get("tool_input") or {})
        before = approvals_snapshot(common)
        started = time.monotonic()
        # ``command``: run this instead of the dispatcher (a legacy settings.json entry, a shim)
        if case.get("command"):
            argv = [BASH, "-c", t.s(case["command"])]
        elif event == "session":  # hooks.json passes the matcher's source as the argument
            argv = [BASH, str(session_hook), "startup" if inp.get("source", "startup") == "startup" else "resume"]
        elif event == "statusline":  # the statusline script, stdin = input.stdin
            script = STATUSLINE
            if given.get("script_copy"):
                script = tmp / "copied" / STATUSLINE.name
                script.parent.mkdir()
                shutil.copy(str(STATUSLINE), str(script))
            argv = [BASH, str(script)]
            payload = inp.get("stdin") or {}
        else:
            argv = [BASH, str(DISPATCHER), event]
        cp = subprocess.run(argv, input=json.dumps(payload).encode("utf-8"),
                            cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        duration = time.monotonic() - started
        after = approvals_snapshot(common)
        created = any(before.get(k) != v for k, v in after.items())  # a new or rewritten marker file
        out = cp.stdout.decode("utf-8", "replace")
        err = cp.stderr.decode("utf-8", "replace")
        expect = case.get("expect_nopy", case["expect"]) if nopy else case["expect"]
        problems = assert_expect(expect, cp.returncode, out, err, created, duration, case.get("tags") or [])
        problems += assert_files(expect, t, common)
        return problems, {"rc": cp.returncode, "stdout": out, "stderr": err, "duration": duration,
                          "tmp": str(tmp) if keep else None}
    finally:
        if not keep:
            shutil.rmtree(str(tmp), ignore_errors=True)


def load_tables(only=None):
    tables = []
    for p in sorted(TABLES.glob("*.json")):
        if only and p.stem not in only:
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        cases = data["cases"] if isinstance(data, dict) else data
        tables.append((p.stem, cases))
    return tables


def check_stubs():
    """The stubs print their canned data and exit with the canned code (self-check)."""
    tmp = Path(tempfile.mkdtemp(prefix="karvey-stubs-"))
    try:
        problems = []
        for name in ("gh", "az", "glab"):
            (tmp / (name + ".stdout")).write_text('{"stub":"%s"}' % name)
            (tmp / (name + ".rc")).write_text("3")
            # through BASH, as every other script here: Windows cannot exec a shebang (F-43)
            env = {"KARVEY_STUB_DATA": str(tmp), "PATH": os.environ.get("PATH", "")}
            if os.environ.get("SYSTEMROOT"):
                env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
            cp = subprocess.run([BASH, str(STUBS / name), "pr", "view"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            if cp.returncode != 3 or json.loads(cp.stdout.decode() or "{}").get("stub") != name:
                problems.append("stub %s: rc=%d out=%r" % (name, cp.returncode, cp.stdout))
        calls = (tmp / "calls.log").read_text() if (tmp / "calls.log").exists() else ""
        if calls.count("pr view") != 3:
            problems.append("stubs did not log their calls: %r" % calls)
        return problems
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)


def write_junit(path, results):
    suite = ET.Element("testsuite", name="karvey-guard-tables", tests=str(len(results)),
                       failures=str(sum(1 for r in results if r["problems"])))
    for r in results:
        tc = ET.SubElement(suite, "testcase", classname=r["table"], name=r["name"], time="%.3f" % r["duration"])
        if r["problems"]:
            f = ET.SubElement(tc, "failure", message="; ".join(r["problems"]))
            f.text = "stdout:\n%s\nstderr:\n%s" % (r["stdout"], r["stderr"])
    ET.ElementTree(suite).write(path, encoding="utf-8", xml_declaration=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run the Karvey guard tables (architecture §6.1).")
    ap.add_argument("--tag", action="append", default=[], help="only cases with this tag (repeatable)")
    ap.add_argument("--only", action="append", default=[], help="only this table (file stem; repeatable)")
    ap.add_argument("--junit", help="write a JUnit XML report")
    ap.add_argument("--keep", action="store_true", help="keep the per-case temp dirs")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    stub_problems = check_stubs()
    if stub_problems:
        for p in stub_problems:
            print("FAIL stubs: " + p)
        return 1
    results = []
    n_cases = 0
    for table, cases in load_tables(args.only or None):
        for case in cases:
            tags = case.get("tags") or []
            if args.tag and not set(args.tag) & set(tags):
                continue
            n_cases += 1
            runs = [False] + ([True] if "nopy" in tags else [])
            for nopy in runs:
                name = case.get("id", "?") + (" [nopy]" if nopy else "")
                try:
                    check_keys(case)
                    problems, detail = run_case(case, nopy=nopy, keep=args.keep)
                except (CaseError, subprocess.TimeoutExpired, OSError, ValueError) as exc:
                    problems, detail = ["case error: %s" % exc], {"stdout": "", "stderr": "", "duration": 0.0}
                results.append({"table": table, "name": name, "problems": problems, **detail})
                if problems:
                    print("  FAIL %s/%s: %s" % (table, name, "; ".join(problems)))
                    if args.verbose:
                        print("       stdout: %r\n       stderr: %r" % (detail.get("stdout"), detail.get("stderr")))
                elif args.verbose:
                    print("  ok   %s/%s (%.2f s)%s" % (table, name, detail["duration"],
                                                       " [limitation]" if case.get("limitation") else ""))
    if args.junit:
        write_junit(args.junit, results)
    failed = sum(1 for r in results if r["problems"])
    print("guard tables: %d cases, %d runs (%d nopy), %d passed, %d failed" % (
        n_cases, len(results), sum(1 for r in results if r["name"].endswith("[nopy]")), len(results) - failed,
        failed))
    if n_cases == 0:
        print("no case selected")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
