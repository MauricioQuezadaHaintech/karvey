"""karvey_lib: shared library of the Karvey plugin scripts (architecture §1.1).

Python >= 3.9, standard library only. Every tool shares:
- the exit codes below (hooks use the harness contract instead: 0 allow, 2 block);
- the ``--json`` envelope ``{tool, version, ok, exit, result, errors, warnings}``;
- the defaults of ``defaults.json`` (D-06/D-07), the one place for them (REQ-W1-049).
"""
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = LIB_DIR.parent
PLUGIN_ROOT = SCRIPTS_DIR.parent
SCHEMAS_DIR = PLUGIN_ROOT / "schemas"

# Exit codes (§1.1 shared conventions).
EXIT_OK = 0          # ok
EXIT_FINDINGS = 1    # validation errors, lint failures, convergence not reached
EXIT_USAGE = 2       # usage error
EXIT_REFUSED = 3     # unmet precondition, unsafe value, write that would be invalid
EXIT_NOT_FOUND = 4   # input not found / unreadable / corrupt
EXIT_INTERNAL = 5    # internal error

EXIT_CODES = {
    EXIT_OK: "ok",
    EXIT_FINDINGS: "findings",
    EXIT_USAGE: "usage",
    EXIT_REFUSED: "refused",
    EXIT_NOT_FOUND: "not-found",
    EXIT_INTERNAL: "internal",
}

# Hook exit codes (harness contract).
HOOK_ALLOW = 0
HOOK_BLOCK = 2

ENVELOPE_KEYS = ("tool", "version", "ok", "exit", "result", "errors", "warnings")
ISSUE_KEYS = ("code", "severity", "file", "path", "expected", "got", "message")


def _read_version():
    """The plugin version, read from plugin.json so no second literal exists."""
    try:
        with open(PLUGIN_ROOT / ".claude-plugin" / "plugin.json", encoding="utf-8-sig") as fh:
            return str(json.load(fh).get("version", "0.0.0"))
    except (OSError, ValueError):
        return "0.0.0"


__version__ = _read_version()

_DEFAULTS = None


def defaults():
    """The D-06/D-07 defaults (a fresh copy each call, so callers cannot mutate the cache)."""
    global _DEFAULTS
    if _DEFAULTS is None:
        with open(LIB_DIR / "defaults.json", encoding="utf-8-sig") as fh:
            _DEFAULTS = json.load(fh)
    return json.loads(json.dumps(_DEFAULTS))


def issue(code, message, severity="error", file=None, path=None, expected=None, got=None):
    """One error/warning entry of the envelope."""
    if severity not in ("error", "warning"):
        raise ValueError("severity must be 'error' or 'warning'")
    return {"code": code, "severity": severity, "file": file, "path": path,
            "expected": expected, "got": got, "message": message}


def envelope(tool, exit_code, result=None, errors=None, warnings=None):
    """The ``--json`` envelope. ``ok`` is derived from the exit code."""
    if exit_code not in EXIT_CODES:
        raise ValueError("unknown exit code %r" % (exit_code,))
    return {
        "tool": tool,
        "version": __version__,
        "ok": exit_code == EXIT_OK,
        "exit": exit_code,
        "result": result if result is not None else {},
        "errors": list(errors or []),
        "warnings": list(warnings or []),
    }


def emit(env, as_json, human=None, stream=None):
    """Print the envelope (``--json``) or the human text; return the exit code."""
    out = stream or sys.stdout
    if as_json:
        out.write(json.dumps(env, ensure_ascii=False, sort_keys=False) + "\n")
    else:
        if human:
            out.write(human.rstrip("\n") + "\n")
        for item in env.get("errors", []) + env.get("warnings", []):
            loc = ":".join(x for x in (item.get("file"), item.get("path")) if x)
            sys.stderr.write("[%s] %s%s\n" % (item["severity"], (loc + ": ") if loc else "", item["message"]))
    return env["exit"]
