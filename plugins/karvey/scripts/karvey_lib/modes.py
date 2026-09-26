"""Check-mode registry (architecture §1.5, wave2-structural).

``schemas/check-modes.json`` lists every check Wave 2 introduces with its 3.13, 4.0 and 4.1 default, and every
check Wave 3 introduces with its 4.1 default (wave3-optimization §1.23).
``resolve`` returns the mode a project runs a check in; ``record_hit`` appends the evidence that a
check *would* have refused to ``docs/spec/changes/{id}/checks.jsonl`` (the readiness report reads it,
REQ-W2-010). Standard library only.
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

from . import SCHEMAS_DIR, __version__
from . import project as pj

REGISTRY_FILE = "check-modes.json"
HITS_FILE = "checks.jsonl"
_CHANGE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_CACHE = {}


class ModeError(Exception):
    """Unknown check id or an invalid mode value."""


def registry():
    if "reg" not in _CACHE:
        with open(SCHEMAS_DIR / REGISTRY_FILE, encoding="utf-8-sig") as fh:
            _CACHE["reg"] = json.load(fh)
    return json.loads(json.dumps(_CACHE["reg"]))


def check_ids():
    return [c["id"] for c in registry()["checks"]]


def row(check_id):
    for c in registry()["checks"]:
        if c["id"] == check_id:
            return c
    raise ModeError("unknown check %r (one of %s)" % (check_id, ", ".join(check_ids())))


def levels_of(check_id):
    reg = registry()
    return reg["strictness"][row(check_id).get("levels", "levels")]


LINES = ("3.13", "4.0", "4.1")


def release_line(version=None):
    """``"3.13"`` for a 3.x plugin, ``"4.0"`` for 4.0.x, ``"4.1"`` from 4.1 on (wave3-optimization, §1.23)."""
    v = version or __version__
    parts = str(v).split(".")
    try:
        major = int(parts[0])
    except ValueError:
        major = 3
    try:
        minor = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        minor = 0
    if major < 4:
        return "3.13"
    return "4.0" if (major == 4 and minor == 0) else "4.1"


def default(check_id, line=None):
    """The check's default on a release line; a check introduced after that line (a Wave 3 row declares only
    ``4.1``) takes its first declared default."""
    defaults = row(check_id)["defaults"]
    line = line or release_line()
    if line in defaults:
        return defaults[line]
    later = [x for x in LINES if x in defaults and LINES.index(x) > LINES.index(line)] if line in LINES else []
    return defaults[later[0]] if later else defaults[sorted(defaults)[-1]]


def _project_value(project, check_id):
    """The project's override: ``checks.{id}``, else the check's own ``project_key``."""
    if not isinstance(project, dict):
        return None
    checks = project.get("checks")
    if isinstance(checks, dict) and isinstance(checks.get(check_id), str):
        return checks[check_id]
    key = row(check_id).get("project_key")
    if not key:
        return None
    cur = project
    for part in key.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    if check_id == "schema.strict" and isinstance(cur, str):
        return {"strict": "blocking", "advisory": "warn"}.get(cur)
    return cur if isinstance(cur, str) else None


def resolve(root=None, check_id=None, project=None, version=None):
    """``{check, mode, source, default, warning}`` for one check.

    The project override is taken when it is a valid level; a mode laxer than the 4.0 default is
    accepted with a warning naming the check; an invalid value falls back to the default with a warning."""
    if project is None and root is not None:
        project, _ = pj.load_project_json(root)
    line = release_line(version)
    levels = levels_of(check_id)
    dflt = default(check_id, line)
    res = {"check": check_id, "mode": dflt, "source": "default %s" % line, "default": dflt, "warning": None}
    val = _project_value(project, check_id)
    if val is None:
        return res
    if val not in levels:
        res["warning"] = "%s: project value %r is not one of %s; default %r used" % (
            check_id, val, ", ".join(levels), dflt)
        return res
    res["mode"], res["source"] = val, "project.json"
    ref_line = "4.0" if "4.0" in row(check_id)["defaults"] else "4.1"
    four = default(check_id, ref_line)
    if levels.index(val) < levels.index(four):
        res["warning"] = "%s: project mode %r is laxer than the %s default %r" % (check_id, val, ref_line, four)
    return res


def would_refuse(mode):
    """True when a mode would refuse (``blocking`` or ``merged`` is the enforced end)."""
    return mode in ("blocking",)


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def hits_path(root, change):
    if not isinstance(change, str) or not _CHANGE_ID.match(change):
        raise ModeError("invalid change id %r" % (change,))
    return Path(root) / pj.CHANGES_DIR / change / HITS_FILE


def record_hit(root, change, check_id, detail, finding=None, mode=None, at=None):
    """Append ``{check, at, mode, would_refuse, detail, finding}`` to ``changes/{id}/checks.jsonl``."""
    row(check_id)
    if mode is None:
        mode = resolve(root, check_id)["mode"]
    rec = {"check": check_id, "at": at or now_iso(), "mode": mode, "would_refuse": True,
           "detail": str(detail)[:300], "finding": finding}
    p = hits_path(root, change)
    if not p.parent.is_dir():
        raise ModeError("change %r has no folder under %s" % (change, pj.CHANGES_DIR))
    line = json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n"
    fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)
    return rec


def read_hits(path):
    """Parsed lines of a ``checks.jsonl`` (malformed lines are skipped)."""
    out = []
    try:
        with open(path, encoding="utf-8-sig") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rec = json.loads(ln)
                except ValueError:
                    continue
                if isinstance(rec, dict) and isinstance(rec.get("check"), str):
                    out.append(rec)
    except OSError:
        pass
    return out
