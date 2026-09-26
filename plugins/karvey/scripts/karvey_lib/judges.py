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


# --------------------------------------------------------------------------- collect (REQ-W2-025, 026, 029, 030)
VERDICTS = ("pass", "concerns", "fail")
SEVERITIES = ("Critical", "High", "Medium", "Low")
TYPES = ("bug", "spec-gap", "emergent")
FINDINGS_HEAD = "| ID | Date | Phase | Origin | Type | Severity | Finding | Status | Routed to |"
_FENCE = re.compile(r"```.*?(```|\Z)", re.S)
_PATCH_LINE = re.compile(r"^(diff --git|@@|\+\+\+|---|[+-])", re.M)
_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_FID = re.compile(r"^\|\s*F-(\d+)\s*\|", re.M)
_LINE_NO = re.compile(r"^[0-9]+$")  # ASCII digits only: str.isdigit() also takes '²' (BUG-56)


def sanitise(text):
    """Finding text for a Markdown table cell: no code block or patch, escaped, at most 300 characters."""
    t = _FENCE.sub(" ", str(text or ""))
    if re.search(r"^(@@|diff --git|\+\+\+ )", t, re.M):  # a patch: drop its lines, keep the prose
        t = "\n".join(ln for ln in t.splitlines() if not _PATCH_LINE.match(ln))
    t = t.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    t = _CTRL.sub("", t).replace("|", "\\|")
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= TEXT_MAX else t[:TEXT_MAX - 1] + "…"


def _lines_of(root, path):
    p = Path(path) if os.path.isabs(path) else Path(root) / path
    try:
        return len(p.read_text(encoding="utf-8-sig", errors="replace").splitlines())
    except OSError:
        return None


def resolve_cite(root, cite, allowed):
    """True when ``path:line`` names one of the inputs and a line within its length."""
    if not isinstance(cite, str) or ":" not in cite:
        return False
    path, _, line = cite.rpartition(":")
    path, line = path.strip(), line.strip()
    if not _LINE_NO.match(line):
        return False
    if path not in allowed:
        return False
    n = _lines_of(root, path)
    return n is not None and 1 <= int(line) <= n


def _valid_result(r):
    if not isinstance(r, dict) or r.get("verdict") not in VERDICTS or not isinstance(r.get("lens"), str):
        return False
    fs = r.get("findings", [])
    if not isinstance(fs, list):
        return False
    return all(isinstance(f, dict) and f.get("severity") in SEVERITIES and isinstance(f.get("text"), str)
               for f in fs)


def price(model):
    table = defaults().get("judge_price_table") or {}
    p = table.get(model) or table.get("default") or {"in": 0.0, "out": 0.0}
    return float(p.get("in", 0.0)), float(p.get("out", 0.0))


def cost(usage, chars_in, chars_out, model):
    """``(tokens_in, tokens_out, usd, estimated)``: measured when ``usage`` has tokens, else chars ÷ 4."""
    pin, pout = price(model)
    if isinstance(usage, dict) and isinstance(usage.get("tokens_in"), int) and isinstance(usage.get("tokens_out"), int):
        ti, to = usage["tokens_in"], usage["tokens_out"]
        usd = usage.get("usd")
        if not isinstance(usd, (int, float)) or isinstance(usd, bool):
            usd = (ti * pin + to * pout) / 1e6
        return ti, to, round(float(usd), 6), False
    ti, to = chars_in // 4, chars_out // 4
    return ti, to, round((ti * pin + to * pout) / 1e6, 6), True


def collect(root, change, phase, results, allowed, model=None, intra_model=None, at=None, chars_in=0,
            lenses=None, rejected=None):
    """Filter the judge results (``[(name, raw_text)]``). Returns ``(runs, kept, lines)``; writes nothing.

    With ``lenses`` (the lenses of this run, from ``build_inputs``), a result naming any other lens is
    discarded — no run record, no finding — and listed in ``rejected`` with its reason (BUG-56)."""
    runs, kept, lines = [], [], []
    for name, raw in results:
        try:
            r = json.loads(raw)
        except ValueError:
            r = None
        lens = r.get("lens") if isinstance(r, dict) and isinstance(r.get("lens"), str) else Path(name).stem
        if lenses is not None and lens not in lenses:
            why = "lens %r is not a lens of this run (%s)" % (sanitise(lens)[:60], ", ".join(lenses) or "none")
            if rejected is not None:
                rejected.append({"file": sanitise(name)[:120], "lens": sanitise(lens)[:60], "reason": why})
            lines.append("%s: discarded (%s)" % (sanitise(name)[:120], why))
            continue
        if not _valid_result(r):
            rmodel = r.get("model") if isinstance(r, dict) and isinstance(r.get("model"), str) else None
            runs.append({"phase": phase, "lens": lens, "model": rmodel or model or "unknown",
                         "intra_model": bool(intra_model), "verdict": "not-run",
                         "findings": {}, "discarded": 0, "at": at, "reason": "invalid output"})
            lines.append("%s: not run (invalid output)" % lens)
            continue
        discarded, counts = 0, {}
        for f in r.get("findings", []):
            if not resolve_cite(root, f.get("cite"), allowed):
                discarded += 1
                continue
            sev = f["severity"]
            counts[sev] = counts.get(sev, 0) + 1
            kept.append({"lens": r["lens"], "severity": sev, "type": f.get("type_guess") if f.get("type_guess") in TYPES
                         else "emergent", "text": sanitise(f["text"]), "cite": f["cite"]})
        m = r.get("model") or model or "unknown"
        im = r.get("intra_model") if isinstance(r.get("intra_model"), bool) else bool(intra_model)
        ti, to, usd, est = cost(r.get("usage"), chars_in, len(raw), m)
        runs.append({"phase": phase, "lens": r["lens"], "model": m, "intra_model": im, "verdict": r["verdict"],
                     "findings": counts, "discarded": discarded, "tokens_in": ti, "tokens_out": to, "usd": usd,
                     "estimated": est, "at": at})
        lines.append("%s: %s · %d kept · %d discarded (no citation) · %s%s" % (
            r["lens"], r["verdict"], sum(counts.values()), discarded, m, " (intra-model)" if im else ""))
    return runs, kept, lines


def _finding_cell(k):
    return "%s (%s)" % (k["text"], str(k["cite"]).replace("|", "\\|"))


def append_findings(path, phase, kept, day, skipped=None):
    """Append the kept judge findings as ``open`` rows (origin ``judge:{lens}``); returns the new ids.

    Idempotent (BUG-56): a finding whose lens, cite and text already have a row is not appended again; it is
    added to ``skipped`` when a list is given. The lens is sanitised like the text."""
    from . import atomicio
    path = Path(path)
    exists = path.is_file()
    text = path.read_text(encoding="utf-8-sig") if exists else "# Findings\n\n%s\n%s\n" % (
        FINDINGS_HEAD, "|" + "----|" * 9)
    expected = atomicio.file_sha256(path) if exists else None  # compare-and-swap under the writer's lock
    nums = [int(n) for n in _FID.findall(text)]
    nxt = max(nums) + 1 if nums else 1
    have = {(r.get("origin"), r.get("finding")) for r in read_rows_text(text)}
    rows, ids = [], []
    for k in kept:
        key = ("judge:%s" % sanitise(k["lens"]), _finding_cell(k).strip())
        if key in have:
            if skipped is not None:
                skipped.append(k)
            continue
        have.add(key)
        fid = "F-%02d" % nxt
        nxt += 1
        ids.append(fid)
        rows.append("| %s | %s | %s | %s | %s | %s | %s | open | — |" % (
            fid, day, phase, key[0], k["type"], k["severity"], _finding_cell(k)))
    if rows:
        lines = text.rstrip("\n").split("\n")
        last = max((i for i, ln in enumerate(lines) if ln.startswith("|")), default=len(lines) - 1)
        lines[last + 1:last + 1] = rows
        atomicio.write_text_atomic(str(path), "\n".join(lines) + "\n", expected_sha256=expected)
    return ids


def read_rows(path):
    """The rows of the findings table (by header name, lower-case keys), or []."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return []
    return read_rows_text(text)


def read_rows_text(text):
    head, rows = None, []
    for ln in text.splitlines():
        if not ln.startswith("|"):
            head = None if rows or head is None else head
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", ln.strip())[1:-1]]
        if head is None:
            head = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(dict(zip(head, cells)))
    return rows


def open_blocking(path, phase):
    """Ids of ``open`` Critical/High judge findings of ``phase`` (REQ-W2-028)."""
    out = []
    for r in read_rows(path):
        if (r.get("origin") or "").startswith("judge:") and r.get("phase") == phase \
                and r.get("severity") in ("Critical", "High") and (r.get("status") or "").split(" ")[0] == "open":
            out.append(r.get("id") or r.get("#") or "?")
    return out
