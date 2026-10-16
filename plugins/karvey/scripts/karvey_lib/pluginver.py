"""Which Karvey version runs, which one is installed (BUG-163).

A session keeps the plugin it loaded: its hooks and the script paths its skills expanded point into that
version's cache folder. After ``claude plugin update`` the session still runs the old code until it restarts,
and nothing told it so. Two remedies live here:

- ``drift_line``: the prompt hook says, once per session and installed version, that the session runs an older
  version than the installed one and must be restarted;
- ``maybe_reexec``: a script started from an older cached version re-runs itself from the installed version, so
  a skill's command lands on the installed code whatever path the session expanded.

Both read the harness's plugin registry (``~/.claude/plugins/installed_plugins.json``) and never fail: any doubt
leaves things as they are.
"""
import json
import os
import re
import sys
import tempfile

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NO_REEXEC_ENV = "KARVEY_NO_REEXEC"
_VER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_version(text):
    m = _VER.match(str(text or "").strip())
    return tuple(int(x) for x in m.groups()) if m else None


def running_version(root=PLUGIN_ROOT):
    try:
        with open(os.path.join(root, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
            return json.load(fh).get("version")
    except (OSError, ValueError, AttributeError):
        return None


def _registry_path(env=None):
    env = os.environ if env is None else env
    base = env.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(base, "plugins", "installed_plugins.json")


def installed(env=None):
    """``(version, install_path)`` of the installed Karvey plugin, or ``(None, None)``."""
    try:
        with open(_registry_path(env), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None, None
    plugins = data.get("plugins", data) if isinstance(data, dict) else {}
    best = (None, None)
    for key, entries in (plugins or {}).items():
        if not str(key).startswith("karvey@"):
            continue
        for e in entries if isinstance(entries, list) else [entries]:
            if not isinstance(e, dict):
                continue
            v, p = e.get("version"), e.get("installPath")
            if parse_version(v) and isinstance(p, str) and (best[0] is None or
                                                            parse_version(v) > parse_version(best[0])):
                best = (v, p)
    return best


def _in_cache(root):
    parts = os.path.realpath(root).replace("\\", "/").split("/")
    return "plugins" in parts and "cache" in parts


def newer_installed(root=PLUGIN_ROOT, env=None):
    """``(running, installed, path)`` when the installed version is newer than the running one and this copy
    runs from the plugin cache (a development checkout never counts); else None."""
    run = running_version(root)
    inst, path = installed(env)
    if not (parse_version(run) and parse_version(inst)) or not _in_cache(root):
        return None
    if parse_version(inst) <= parse_version(run):
        return None
    if not (isinstance(path, str) and os.path.isfile(os.path.join(path, ".claude-plugin", "plugin.json"))):
        return None
    if os.path.realpath(path) == os.path.realpath(root):
        return None
    return run, inst, path


def drift_line(session_id, root=PLUGIN_ROOT, env=None):
    """The one-line notice, or None. Said once per session and installed version."""
    found = newer_installed(root, env)
    if found is None:
        return None
    run, inst, _ = found
    tag = re.sub(r"[^A-Za-z0-9_.-]", "_", "%s-%s" % (session_id or "nosession", inst))[:120]
    seen = os.path.join(tempfile.gettempdir(), "karvey-drift-%s" % tag)
    if os.path.exists(seen):
        return None
    try:
        with open(seen, "w") as fh:
            fh.write(run or "")
    except OSError:
        pass
    return ("[karvey] this session runs Karvey %s but %s is installed: its hooks stay on %s until the session is "
            "restarted. Tell the human once, in one line, to restart this session; the Karvey scripts already run "
            "the installed %s." % (run, inst, run, inst))


def maybe_reexec(script_file, argv=None, env=None):
    """Re-run ``script_file`` from the installed version when this copy is an older cached one. Returns only when
    nothing is to be done (or the exec failed)."""
    env = os.environ if env is None else env
    if env.get(NO_REEXEC_ENV):
        return
    root = os.path.dirname(os.path.dirname(os.path.abspath(script_file)))
    found = newer_installed(root, env)
    if found is None:
        return
    target = os.path.join(found[2], "scripts", os.path.basename(script_file))
    if not os.path.isfile(target):
        return
    new_env = dict(env)
    new_env[NO_REEXEC_ENV] = "1"
    try:
        sys.stdout.flush()
        os.execve(sys.executable, [sys.executable, target] + list(sys.argv[1:] if argv is None else argv), new_env)
    except OSError:
        return
