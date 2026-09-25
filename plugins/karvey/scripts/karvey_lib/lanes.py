"""Lanes (architecture §1.3, wave2-structural): ``schemas/lanes.json`` as data.

- ``load()``: the table, validated with ``schema_lite`` plus two semantic checks (every lane lists every
  phase of the state machine; ``init`` and ``archived`` are never skipped).
- ``phase_rule(lane, phase)``: ``m`` mandatory · ``o`` optional · ``s`` skipped by the lane. The ``legacy``
  lane (no ``lane``, no ``type: ops|hotfix``) is the 3.12 pipeline: every phase ``m``.
- ``lane_of(spec)``: ``(lane, source)`` with source ``spec`` · ``type`` · ``legacy`` (REQ-W2-019).
- ``judges_for(lane, project)``: the default lenses per judged phase, or the project override (REQ-W2-031).
Standard library only.
"""
import fnmatch
import json

from . import SCHEMAS_DIR
from . import schema_lite as sl

LANES_FILE = "lanes.json"
LEGACY = "legacy"
RULES = ("m", "o", "s")
NEVER_SKIPPED = ("init", "archived")
_CACHE = {}

_SCHEMA = {
    "type": "object", "required": ["version", "phases", "lanes", "globs"],
    "properties": {
        "version": {"const": 1},
        "phases": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "lanes": {"type": "object", "additionalProperties": {
            "type": "object", "required": ["phases", "gates", "judges"],
            "properties": {
                "phases": {"type": "object", "additionalProperties": {"enum": list(RULES)}},
                "notes": {"type": "object", "additionalProperties": {"type": "string"}},
                "gates": {"type": "array", "minItems": 1, "items": {"enum": ["what", "how", "what+how", "release",
                                                                            "prod"]}},
                "judges": {"type": "integer", "minimum": 0},
                "requires": {"type": "array", "items": {"enum": ["bug_id", "finding", "regression_test"]}},
                "criteria": {"type": "object", "properties": {
                    "max_code_files": {"type": "integer", "minimum": 0},
                    "forbid": {"type": "array", "items": {"enum": ["schema", "api_contract", "permissions"]}},
                    "max_tier": {"type": "integer", "minimum": 1, "maximum": 4}}}}}},
        "globs": {"type": "object", "additionalProperties": {"type": "array", "items": {"type": "string"}}},
    },
}


class LaneError(Exception):
    """An unknown lane, an invalid table or an invalid override."""


def _machine_phases():
    with open(SCHEMAS_DIR / "state-machine.json", encoding="utf-8-sig") as fh:
        return [p["id"] for p in json.load(fh)["phases"]]


def problems(table):
    """Every problem of a parsed lane table (schema + semantic), as strings."""
    out = ["%s %s" % (i["path"], i["message"]) for i in sl.Validator(_SCHEMA).validate(table)
           if i["severity"] == "error"]
    if out:
        return out
    phases = _machine_phases()
    if table["phases"] != phases:
        out.append("phases %s differ from state-machine.json %s" % (table["phases"], phases))
    for name, lane in sorted(table["lanes"].items()):
        missing = [p for p in phases if p not in lane["phases"]]
        if missing:
            out.append("lane %s does not list %s" % (name, ", ".join(missing)))
        extra = [p for p in lane["phases"] if p not in phases]
        if extra:
            out.append("lane %s lists unknown phases %s" % (name, ", ".join(extra)))
        for p in NEVER_SKIPPED:
            if lane["phases"].get(p) == "s":
                out.append("lane %s skips %s, which is never skipped" % (name, p))
    return out


def load(table=None):
    """The lane table (cached). Raises :class:`LaneError` when it is invalid."""
    if table is not None:
        bad = problems(table)
        if bad:
            raise LaneError("; ".join(bad))
        return table
    if "table" not in _CACHE:
        with open(SCHEMAS_DIR / LANES_FILE, encoding="utf-8-sig") as fh:
            data = json.load(fh)
        bad = problems(data)
        if bad:
            raise LaneError("schemas/lanes.json is invalid: " + "; ".join(bad))
        _CACHE["table"] = data
    return json.loads(json.dumps(_CACHE["table"]))


def names():
    return list(load()["lanes"])


def lane_def(lane):
    t = load()
    if lane not in t["lanes"]:
        raise LaneError("unknown lane %r (one of %s)" % (lane, ", ".join(t["lanes"])))
    return t["lanes"][lane]


def phase_rule(lane, phase):
    """``m`` · ``o`` · ``s`` for ``phase`` in ``lane`` (``legacy`` → ``m``)."""
    if lane in (None, LEGACY):
        return "m"
    return lane_def(lane)["phases"].get(phase, "m")


def lane_skips(lane, phase):
    return lane not in (None, LEGACY) and lane in load()["lanes"] and phase_rule(lane, phase) == "s"


def lane_of(spec):
    """``(lane, source)``: ``spec.json:lane``, else ``type: ops|hotfix``, else ``legacy``."""
    spec = spec if isinstance(spec, dict) else {}
    lane = spec.get("lane")
    if isinstance(lane, str) and lane:
        return lane, "spec"
    if spec.get("type") in ("ops", "hotfix"):
        return spec["type"], "type"
    return LEGACY, "legacy"


def gates_of(lane):
    """The merged human gates of a lane (``legacy`` → the three gates)."""
    if lane in (None, LEGACY):
        return ["what", "how", "release"]
    return list(lane_def(lane)["gates"])


def judges_for(lane, project=None):
    """Lenses per judged phase: ``project.json:judges.per_lane.{lane}``, else the table default."""
    per = ((project or {}).get("judges") or {}).get("per_lane") if isinstance(project, dict) else None
    if isinstance(per, dict) and lane in per:
        v = per[lane]
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise LaneError("judges.per_lane.%s must be an integer >= 0 (got %r)" % (lane, v))
        return v
    if lane in (None, LEGACY):
        return lane_def("standard")["judges"]
    return lane_def(lane)["judges"]


def globs(project=None):
    """The table's globs, extended by ``project.json:lanes.globs``."""
    out = {k: list(v) for k, v in load()["globs"].items()}
    extra = ((project or {}).get("lanes") or {}).get("globs") if isinstance(project, dict) else None
    if isinstance(extra, dict):
        for k, v in extra.items():
            if isinstance(v, list):
                out.setdefault(k, [])
                out[k] += [g for g in v if isinstance(g, str) and g not in out[k]]
    return out


def matches(path, patterns):
    """Glob match where ``**/`` also matches the top level."""
    p = path.replace("\\", "/")
    for g in patterns:
        if fnmatch.fnmatchcase(p, g) or (g.startswith("**/") and fnmatch.fnmatchcase(p, g[3:])):
            return True
    return False
