"""The project-upgrade engine (architecture §1.3, §1.4 of the project-upgrade change).

After a plugin update, a project may need upgrade steps: migrate legacy file shapes, drop copied hook
shims, add team settings, adopt new defaults. The steps are **data plus pure functions**:

- the catalogue ``upgrade-steps.json`` declares every step (validated against
  ``schemas/upgrade-steps.schema.json`` and the invariants below, REQ-UP-008);
- each step's ``check`` / ``fix`` lives in ``upgrade_steps.REGISTRY`` and only reads the project
  through a read-only :class:`Probe`, returning planned :class:`Edit` objects;
- this engine is the **only writer**: path confinement, compare-and-swap atomic writes, the preview
  digest and the journal are implemented once, here.

Python >= 3.9, standard library only. Every subprocess is an argv list.
"""
import json
from pathlib import Path

from . import LIB_DIR, SCHEMAS_DIR
from . import schema_lite as sl

CATALOGUE_PATH = LIB_DIR / "upgrade-steps.json"
SCHEMA_PATH = SCHEMAS_DIR / "upgrade-steps.schema.json"
REQUIRED_FIELDS = ("id", "since", "check", "fix", "dry_run", "human", "risk")
WRITE_SCOPES = ("project", "git_dir")
STEP_DEFAULTS = {"title": "", "report_only": False, "writes": ["project"], "cost": "low", "params": {}}


# --------------------------------------------------------------------------- catalogue (REQ-UP-008)
class CatalogueError(Exception):
    """The catalogue is missing, unreadable or invalid: nothing is evaluated."""


def _step_name(step, index):
    if isinstance(step, dict) and isinstance(step.get("id"), str) and step["id"]:
        return step["id"]
    return "#%d" % (index + 1)


def _default_registry():
    from . import upgrade_steps
    return upgrade_steps.REGISTRY


def load_catalogue(path=None, registry=None):
    """The validated step list, in catalogue order, with the optional fields filled in.

    Raises :class:`CatalogueError` naming the step and the field (``step <id>: missing field <f>``).
    """
    p = Path(path) if path is not None else CATALOGUE_PATH
    try:
        with open(p, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise CatalogueError("step catalogue not found: %s" % p.name)
    except (OSError, ValueError) as exc:
        raise CatalogueError("step catalogue unreadable: %s (%s)" % (p.name, exc))
    if registry is None:
        registry = _default_registry()
    if not isinstance(data, dict):
        raise CatalogueError("step catalogue is not a JSON object")
    steps = data.get("steps")
    # the per-step required fields first, so the message names the step and the field
    if isinstance(steps, list):
        for i, st in enumerate(steps):
            if not isinstance(st, dict):
                raise CatalogueError("step %s: not an object" % _step_name(st, i))
            for f in REQUIRED_FIELDS:
                if f not in st:
                    raise CatalogueError("step %s: missing field %s" % (_step_name(st, i), f))
    try:
        with open(SCHEMA_PATH, encoding="utf-8-sig") as fh:
            schema = json.load(fh)
        issues = sl.validate(data, schema, registry={})
    except (OSError, ValueError, sl.SchemaError) as exc:
        raise CatalogueError("step catalogue schema unusable: %s" % exc)
    errs = [i for i in issues if i["severity"] == "error"]
    if errs:
        first = errs[0]
        where = first.get("path") or "$"
        name = "catalogue"
        if where.startswith("$.steps["):
            try:
                idx = int(where[len("$.steps["):].split("]", 1)[0])
                name = "step %s" % _step_name(steps[idx], idx)
            except (ValueError, IndexError, TypeError):
                pass
        raise CatalogueError("%s: %s: %s" % (name, where, first["message"]))
    seen = set()
    out = []
    for i, st in enumerate(steps):
        sid = st["id"]
        if sid in seen:
            raise CatalogueError("step %s: duplicate id" % sid)
        seen.add(sid)
        if st["check"] not in registry:
            raise CatalogueError("step %s: unknown check function %s" % (sid, st["check"]))
        if st["fix"] is not None and st["fix"] not in registry:
            raise CatalogueError("step %s: unknown fix function %s" % (sid, st["fix"]))
        full = dict(STEP_DEFAULTS)
        full["params"] = {}
        full.update(st)
        if full["human"] and full["fix"] is not None:
            raise CatalogueError("step %s: a human step has fix null" % sid)
        if full["report_only"] and full["fix"] is not None:
            raise CatalogueError("step %s: a report_only step has fix null" % sid)
        if full["fix"] is None and not full["human"] and not full["report_only"]:
            raise CatalogueError("step %s: fix null on a non-human step requires report_only" % sid)
        if not full["human"] and not set(full["writes"]) <= set(WRITE_SCOPES):
            raise CatalogueError("step %s: writes outside %s" % (sid, "|".join(WRITE_SCOPES)))
        out.append(full)
    return out
