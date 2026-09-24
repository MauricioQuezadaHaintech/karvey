"""JSONL decision log (architecture §9): ``<state dir>/audit.log``, mode 0600, 1 MB rotation.

One line per prod-gate decision, per block, per recorded or ignored marker, per hook error.
It never holds tokens, full prompts or command bodies: fields that look like credentials are
dropped, and the prompt excerpt is cut to 80 characters (REQ-W1-017).
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

from . import defaults

LOG_NAME = "audit.log"
FIELDS = ("ts", "guard", "event", "decision", "reason", "repo", "change", "branch", "approver",
          "ref", "session_id", "duration_ms")
EXCERPT_MAX = 80
_SECRETISH = re.compile(r"(token|secret|password|passwd|authorization|api[_-]?key|cookie|credential)", re.I)
_DROP = frozenset({"prompt", "command", "tool_input", "content", "transcript"})


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sanitize(record):
    """Copy of ``record`` safe to log: no secret-like keys, no bodies, bounded excerpt."""
    out = {}
    for k, v in record.items():
        if _SECRETISH.search(k) or k in _DROP:
            continue
        if k == "prompt_excerpt" and isinstance(v, str):
            v = v[:EXCERPT_MAX]
        if isinstance(v, str) and len(v) > 500:
            v = v[:500] + "…"
        out[k] = v
    return out


def _rotate_if_needed(path, limit):
    try:
        if path.stat().st_size >= limit:
            os.replace(str(path), str(path) + ".1")
    except FileNotFoundError:
        pass


def append(state_dir, record, limit=None):
    """Append one JSON line to ``<state_dir>/audit.log``. Returns the written record.

    Logging never raises into the caller: a hook must not fail because the log is unwritable.
    """
    if limit is None:
        limit = defaults().get("audit_rotate_bytes", 1048576)
    rec = {"ts": now_iso()}
    rec.update(sanitize(record))
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n"
    path = Path(state_dir) / LOG_NAME
    try:
        Path(state_dir).mkdir(parents=True, exist_ok=True, mode=0o700)
        _rotate_if_needed(path, limit)
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
        try:
            os.chmod(str(path), 0o600)
        except OSError:
            pass
    except OSError:
        return None
    return rec


def read(state_dir, include_rotated=False):
    """All parseable records, oldest first (skips corrupt lines)."""
    paths = [Path(state_dir) / (LOG_NAME + ".1")] if include_rotated else []
    paths.append(Path(state_dir) / LOG_NAME)
    out = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue
        except FileNotFoundError:
            continue
    return out
