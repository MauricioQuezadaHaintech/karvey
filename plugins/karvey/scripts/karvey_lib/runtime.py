"""The plugin version the runtime has loaded vs the one this clone offers (architecture §1.22, C-22; REQ-W3-058).

``loaded_version()`` reads the runtime's installed-plugins record — ``$CLAUDE_CONFIG_DIR/plugins/installed_plugins.json``,
else the default config directory's — **read-only**: it never writes, touches or locks the runtime's files. Both
record shapes are read (``{"plugins": {"karvey@<marketplace>": {...}}}`` and version 2's list per plugin).
``available_version()`` is the clone's ``.claude-plugin/plugin.json``. Standard library only.
"""
import json
import os
from pathlib import Path

PLUGIN = "karvey"
RECORD = Path("plugins") / "installed_plugins.json"
UNKNOWN = "loaded version unknown"


def config_dir(env=None):
    env = os.environ if env is None else env
    d = env.get("CLAUDE_CONFIG_DIR")
    return Path(d) if d else Path(env.get("HOME") or os.path.expanduser("~")) / ".claude"


def _read(p):
    try:
        with open(str(p), "rb") as fh:
            return json.loads(fh.read(2 * 1024 * 1024).decode("utf-8-sig"))
    except (OSError, ValueError):
        return None


def loaded_version(env=None, plugin=PLUGIN):
    """The version of ``plugin`` in the runtime's record (the most recently updated install), or None."""
    data = _read(config_dir(env) / RECORD)
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        return None
    best = None
    for key, v in sorted(plugins.items()):
        if key.split("@", 1)[0] != plugin:
            continue
        for e in (v if isinstance(v, list) else [v]):
            if isinstance(e, dict) and isinstance(e.get("version"), str):
                stamp = str(e.get("lastUpdated") or e.get("installedAt") or "")
                if best is None or stamp > best[0]:
                    best = (stamp, e["version"])
    return best[1] if best else None


def available_version(plugin_root):
    data = _read(Path(plugin_root) / ".claude-plugin" / "plugin.json")
    v = data.get("version") if isinstance(data, dict) else None
    return v if isinstance(v, str) else None


def report(plugin_root, env=None):
    """``loaded X, available Y`` (with ``— restart the session to load it`` when they differ), or
    ``loaded version unknown, available Y``."""
    loaded, avail = loaded_version(env), available_version(plugin_root)
    if loaded is None:
        return "%s, available %s" % (UNKNOWN, avail or "unknown")
    line = "loaded %s, available %s" % (loaded, avail or "unknown")
    if avail and avail != loaded:
        line += " — update the plugin and start a new session to load it"
    return line


if __name__ == "__main__":  # python3 -m karvey_lib.runtime (from scripts/) — the health skill's call
    print(report(Path(__file__).resolve().parents[2]))
