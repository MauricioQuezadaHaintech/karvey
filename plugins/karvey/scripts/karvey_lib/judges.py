"""Judges (architecture §1.7, wave2-structural): the closed input list, the output filter, the cost.

A judge is a clean-context subagent; this module never starts one. It decides what a judge may read
(``build_inputs``), and it filters what a judge returned (``collect``): schema check, citation resolver,
sanitiser, cost. Kept findings are appended to ``findings.md``; the run records go to ``spec.json`` only
through ``karvey-state.py judge-run``. Standard library only.
"""
import glob
import json
import os
import re
from pathlib import Path

from . import SCHEMAS_DIR, defaults
from . import lanes as ln
from . import project as pj

PHASES_WITH_RUBRIC = ("requirements", "architecture", "qa")
TEXT_MAX = 300
NONE_FOR_LANE = "judges: none for lane %s"
DISABLED = "judges: disabled by project setting"
NOT_JUDGED = "judges: not run (phase %s is not in judges.phases)"
_LENS_HEAD = re.compile(r"^## Lens: ([a-z0-9-]+)\s*$", re.M)


class JudgeError(Exception):
    """Unknown phase, unknown change or an invalid setting."""


def _machine():
    with open(SCHEMAS_DIR / "state-machine.json", encoding="utf-8-sig") as fh:
        return {p["id"]: p for p in json.load(fh)["phases"]}


def settings(project):
    """``project.json:judges`` over ``defaults.json:judges``."""
    d = defaults().get("judges") or {}
    p = (project or {}).get("judges") if isinstance(project, dict) else None
    p = p if isinstance(p, dict) else {}
    out = {k: d.get(k) for k in ("enabled", "mode", "phases", "lenses", "always", "cross_model")}
    for k in ("enabled", "mode", "phases", "cross_model"):
        if k in p:
            out[k] = p[k]
    lenses = dict(out.get("lenses") or {})
    if isinstance(p.get("lenses"), dict):
        lenses.update({k: v for k, v in p["lenses"].items() if isinstance(v, list)})
    out["lenses"] = lenses
    out["per_lane"] = p.get("per_lane") if isinstance(p.get("per_lane"), dict) else {}
    out["budget_ignored"] = "budget" in p
    return out


def rubric_path(plugin_rules, phase):
    return Path(plugin_rules) / "judges" / ("%s.md" % phase)


def rubric_lenses(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return []
    return _LENS_HEAD.findall(text)


def lens_section(path, lens):
    """The text of ``## Lens: {lens}`` in a rubric, or None."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return None
    m = re.search(r"^## Lens: %s\s*$(.*?)(?=^## |\Z)" % re.escape(lens), text, re.M | re.S)
    return m.group(1).strip() if m else None


def pick_lenses(phase, count, st):
    """The first ``count`` lenses of the phase, with the ``always`` ones (the qa fiscal) first."""
    if count <= 0:
        return []
    always = list((st.get("always") or {}).get(phase) or [])
    rest = [x for x in (st.get("lenses") or {}).get(phase, []) if x not in always]
    return (always + rest)[:max(count, len(always))]


def _expand(cdir, item):
    """Change-relative paths of one ``produces`` / ``reads`` item (``?`` optional, globs, dirs)."""
    optional = item.endswith("?")
    item = item.rstrip("?")
    if any(c in item for c in "*?["):
        return sorted(os.path.relpath(p, cdir) for p in glob.glob(str(cdir / item)))
    p = cdir / item
    if p.exists():
        return [item.rstrip("/")]
    return [] if optional else [item.rstrip("/") + " (missing)"]


def build_inputs(root, change, phase, extras=(), project=None, diff_path=None, plugin_rules=None):
    """The closed input list of a judge run (REQ-W2-022, 023, 031). Pure of side effects."""
    machine = _machine()
    if phase not in machine:
        raise JudgeError("unknown phase %r" % phase)
    cdir = Path(root) / pj.CHANGES_DIR / change
    spec_p = cdir / "spec.json"
    if not spec_p.is_file():
        raise JudgeError("change %r not found (no %s)" % (change, spec_p))
    spec = json.loads(spec_p.read_text(encoding="utf-8-sig"))
    if project is None:
        project, _ = pj.load_project_json(root)
    st = settings(project)
    lane, _src = ln.lane_of(spec)
    res = {"change": change, "phase": phase, "lane": lane, "mode": st["mode"], "cross_model": st["cross_model"],
           "lenses": [], "inputs": [], "goal": spec.get("goal"), "rubric": None, "dropped": [], "status": None,
           "notes": []}
    if st["budget_ignored"]:
        res["notes"].append("judges.budget: ignored (measure only, D-30)")
    if st["enabled"] is False:
        res["status"] = DISABLED
        return res
    if phase not in (st["phases"] or []):
        res["status"] = NOT_JUDGED % phase
        return res
    count = ln.judges_for(lane, {"judges": {"per_lane": st["per_lane"]}})
    if count == 0:
        res["status"] = NONE_FOR_LANE % lane
        return res
    rules = Path(plugin_rules) if plugin_rules else SCHEMAS_DIR.parent / "skills" / "karvey" / "rules"
    rp = rubric_path(rules, phase)
    have = rubric_lenses(rp)
    if not rp.is_file():
        res["notes"].append("no rubric rules/judges/%s.md: no lens can run" % phase)
    lenses = pick_lenses(phase, count, st)
    for lens in lenses:
        if lens not in have:
            res["notes"].append("unknown lens %s (no section in rules/judges/%s.md)" % (lens, phase))
    res["lenses"] = [x for x in lenses if x in have]
    res["rubric"] = str(rp) if rp.is_file() else None  # the plugin's own file (read by path)
    pdef = machine[phase]
    items = list(pdef.get("produces") or []) + list(pdef.get("reads") or [])
    paths = []
    for it in items:
        for p in _expand(cdir, it):
            q = "%s/%s/%s" % (pj.CHANGES_DIR.as_posix(), change, p)
            if q not in paths:
                paths.append(q)
    if phase == "qa" and diff_path:
        paths.append(str(diff_path))
    res["inputs"] = paths
    allowed = set(paths) | {res["rubric"]}
    for x in extras or ():
        if x not in allowed:
            res["dropped"].append("dropped: %s (not a phase input)" % x)
    res["status"] = "%d judge(s): %s" % (len(res["lenses"]), ", ".join(res["lenses"]) or "none")
    return res
