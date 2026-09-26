"""Incident states: neutral names with the localized ones as permanent aliases (architecture §1.22; REQ-W3-057).

``schemas/incident-states.json`` lists ``detected, diagnosed, in-fix, resolved, reopened``, each with its aliases
(the names a tracker already uses, e.g. ``RESUELTO``). Matching ignores case and treats ``_`` / ``-`` / spaces
alike. Standard library only.
"""
import json
import re

from . import SCHEMAS_DIR

_CACHE = {}


def table():
    if "t" not in _CACHE:
        with open(SCHEMAS_DIR / "incident-states.json", encoding="utf-8-sig") as fh:
            _CACHE["t"] = json.load(fh)["states"]
    return _CACHE["t"]


def _key(v):
    return re.sub(r"[\s_-]+", " ", (v or "").strip()).lower()


def neutral(state):
    """The neutral id of a state or alias (``RESUELTO`` → ``resolved``); None when unknown or empty."""
    k = _key(state)
    for s in table():
        if k == _key(s["id"]) or any(k == _key(a) for a in s.get("aliases") or []):
            return s["id"]
    return None


def is_resolved(state):
    return neutral(state) == "resolved"


def accepted():
    """``detected (DETECTADO), diagnosed (DIAGNOSTICADO), …`` — the list an unknown state is reported with."""
    return ", ".join("%s (%s)" % (s["id"], ", ".join(s.get("aliases") or [])) if s.get("aliases") else s["id"]
                     for s in table())
