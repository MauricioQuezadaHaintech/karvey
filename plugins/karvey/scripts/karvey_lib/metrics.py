"""Flow metrics over a change's own artifacts (architecture §1.6, wave2-structural).

Pure functions: no I/O, no wall clock. The caller (``karvey-context.py --metrics``) parses the files into
*change records* and passes them in::

    {"id": str, "spec": dict, "findings": [..] | None, "plan_rows": [..] | None, "archived_on": "YYYY-MM-DD" | None}

``findings`` items carry ``type``, ``status``, ``origin`` and ``phase``; ``plan_rows`` items carry the
``estimate`` / ``actual_ai`` / ``actual_review`` cells as text.

Every metric returns ``(value | None, reasons)``. Missing data is never zero (REQ-W2-004): a change without
the data a metric needs is excluded from that metric only and listed in ``reasons`` as
``n/a — {reason} ({change-id})``. Durations are hours (lead time: days); floats are rounded to 2 decimals.
"""
import re
from datetime import date, datetime

from . import lanes

NO_CHANGE = "n/a — no archived change in period"
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})$")


# --------------------------------------------------------------------------- helpers
def r2(x):
    return None if x is None else round(float(x) + 0.0, 2)


def na(reason, cid=None):
    return "n/a — %s (%s)" % (reason, cid) if cid else "n/a — %s" % reason


def parse_dt(value):
    """An ISO 8601 date-time with zone, else None (a date-only value has no time)."""
    if not isinstance(value, str) or not _DT.match(value):
        return None
    v = value[:-1] + "+00:00" if value.endswith("Z") else value
    if "." in v:
        head, rest = v.split(".", 1)
        digits = "".join(ch for ch in rest if ch.isdigit())
        v = head + "." + (digits + "000000")[:6] + rest[len(digits):]
    try:
        return datetime.fromisoformat(v)
    except ValueError:
        return None


def is_date_only(value):
    return isinstance(value, str) and bool(_DATE.match(value))


def hours(a, b):
    return (b - a).total_seconds() / 3600.0


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def spec_of(c):
    return c.get("spec") if isinstance(c.get("spec"), dict) else {}


def lane_of(spec):
    """``spec.lane``, else ``type: ops|hotfix``, else ``legacy`` (the 3.12 pipeline; ``lanes.lane_of``)."""
    return lanes.lane_of(spec)[0]


def _approvals(spec):
    a = spec.get("approvals")
    return a if isinstance(a, dict) else {}


def _list(spec, key):
    v = spec.get(key)
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def weeks_between(frm, to):
    """Weeks in the closed period ``[frm, to]`` (dates as ``YYYY-MM-DD``), at least 1 day."""
    d0, d1 = date.fromisoformat(frm), date.fromisoformat(to)
    return max(1, (d1 - d0).days + 1) / 7.0


def in_period(value, frm, to):
    d = value[:10] if isinstance(value, str) else None
    return bool(d and _DATE.match(d) and (frm is None or d >= frm) and (to is None or d <= to))


# --------------------------------------------------------------------------- metrics
def lead_time(changes):
    """Mean days from ``created_at`` to the production approval."""
    vals, reasons = [], []
    for c in changes:
        s = spec_of(c)
        prod = _approvals(s).get("prod") if isinstance(_approvals(s).get("prod"), dict) else {}
        created, pdate = s.get("created_at"), prod.get("date")
        if not pdate:
            reasons.append(na("no production approval", c["id"]))
            continue
        a, b = parse_dt(created), parse_dt(pdate)
        if a is None or b is None:
            reasons.append(na("approvals without time", c["id"]))
            continue
        vals.append(hours(a, b) / 24.0)
    return r2(mean(vals)), reasons


def cycle_time(changes):
    """``{phase: mean hours}`` over closed ``phase_history`` entries."""
    acc, reasons = {}, []
    for c in changes:
        hist = [e for e in _list(spec_of(c), "phase_history") if "phase" in e]
        closed = [(e["phase"], parse_dt(e.get("entered_at")), parse_dt(e.get("exited_at"))) for e in hist]
        closed = [(p, a, b) for p, a, b in closed if a and b]
        if not closed:
            reasons.append(na("no timed phase history", c["id"]))
            continue
        for p, a, b in closed:
            acc.setdefault(p, []).append(hours(a, b))
    return ({p: r2(mean(v)) for p, v in sorted(acc.items())} or None), reasons


def approval_wait(changes):
    """``{phase: mean hours}`` from ``approvals.{phase}.generated_at`` to each gate outcome of that phase."""
    acc, reasons = {}, []
    for c in changes:
        s = spec_of(c)
        outcomes = _list(s, "gate_outcomes")
        aps = _approvals(s)
        timed = {k: parse_dt(v.get("generated_at")) for k, v in aps.items() if isinstance(v, dict)}
        if not outcomes or not any(timed.values()):
            reasons.append(na("approvals without time", c["id"]))
            continue
        used = False
        for o in outcomes:
            at = parse_dt(o.get("at"))
            for p in o.get("phases") or []:
                g = timed.get(p)
                if g and at and at >= g:
                    acc.setdefault(p, []).append(hours(g, at))
                    used = True
        if not used:
            reasons.append(na("approvals without time", c["id"]))
    return ({p: r2(mean(v)) for p, v in sorted(acc.items())} or None), reasons


def throughput(changes, frm, to):
    """Archived changes per week in the period."""
    n = len([c for c in changes if c.get("archived_on") and in_period(c["archived_on"], frm, to)])
    if not n:
        return None, [NO_CHANGE]
    return r2(n / weeks_between(frm, to)), []


def _prod_deploys(changes, frm=None, to=None):
    out = []
    for c in changes:
        for d in _list(spec_of(c), "deploys"):
            if d.get("env") == "prod" and (frm is None or in_period(d.get("at"), frm, to)):
                out.append((c["id"], d))
    return out


def deploy_frequency(changes, frm, to):
    """Production deploys per week in the period."""
    deps = _prod_deploys(changes, frm, to)
    if not deps:
        return None, [na("no production deploy recorded (deploys[])")]
    return r2(len(deps) / weeks_between(frm, to)), []


def change_failure_rate(changes, frm=None, to=None):
    """Production deploys with a regression or a rollback / production deploys."""
    deps = _prod_deploys(changes, frm, to)
    if not deps:
        return None, [na("no production deploy recorded (deploys[])")]
    bad = [d for _, d in deps if d.get("verification") == "regression" or d.get("rollback")]
    return r2(len(bad) / len(deps)), []


def time_to_restore(changes):
    """Mean hours from a regression deploy to the next ``pass`` deploy of the same change."""
    vals = []
    for c in changes:
        deps = sorted((d for d in _list(spec_of(c), "deploys") if parse_dt(d.get("at"))),
                      key=lambda d: parse_dt(d["at"]))
        for i, d in enumerate(deps):
            if d.get("verification") != "regression":
                continue
            nxt = next((x for x in deps[i + 1:] if x.get("env") == d.get("env") and x.get("verification") == "pass"),
                       None)
            if nxt:
                vals.append(hours(parse_dt(d["at"]), parse_dt(nxt["at"])))
    if not vals:
        return None, [na("no regression deploy")]
    return r2(mean(vals)), []


def spec_gap_rate(changes):
    """Spec-gap findings per change with a findings.md."""
    counts, reasons = [], []
    for c in changes:
        if c.get("findings") is None:
            reasons.append(na("no findings.md", c["id"]))
            continue
        counts.append(len([f for f in c["findings"] if f.get("type") == "spec-gap"]))
    return r2(mean(counts)), reasons


def ripple(changes):
    """``revision_history`` entries per change."""
    vals = [len(spec_of(c).get("revision_history") or []) for c in changes
            if isinstance(spec_of(c).get("revision_history", []), list)]
    return r2(mean(vals)), []


def _gate_key(o):
    g = o.get("gate")
    if g and g != "phase":
        return g
    ph = o.get("phases") or []
    return ph[0] if ph else "unknown"


def gate_rejection_rate(changes):
    """``{gate: changes_requested / all outcomes}`` (plan exceptions are not gates)."""
    acc, reasons = {}, []
    for c in changes:
        outs = [o for o in _list(spec_of(c), "gate_outcomes") if o.get("kind", "gate") == "gate"]
        if not outs:
            reasons.append(na("no gate outcomes", c["id"]))
            continue
        for o in outs:
            a = acc.setdefault(_gate_key(o), [0, 0])
            a[1] += 1
            if o.get("outcome") == "changes_requested":
                a[0] += 1
    return ({k: r2(v[0] / v[1]) for k, v in sorted(acc.items())} or None), reasons


def _num(v):
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(?:min)?\s*$", v or "")
    return float(m.group(1)) if m else None


def estimate_accuracy(changes):
    """Σ actual (AI + review) / Σ estimate over task rows with both (1.0 = on estimate)."""
    est = act = 0.0
    reasons = []
    for c in changes:
        rows = c.get("plan_rows")
        used = False
        for r in rows or []:
            if "[human]" in (r.get("task") or "").lower():
                continue
            e, ai, rv = _num(r.get("estimate")), _num(r.get("actual_ai")), _num(r.get("actual_review"))
            if not e or ai is None:
                continue
            est += e
            act += ai + (rv or 0.0)
            used = True
        if not used:
            reasons.append(na("no actual column", c["id"]))
    if not est:
        return None, reasons
    return r2(act / est), reasons


def judge_acceptance(changes):
    """``{lens: routed / (routed + rejected)}`` over findings whose origin is ``judge:{lens}``."""
    acc, reasons = {}, []
    for c in changes:
        rows = [f for f in (c.get("findings") or []) if str(f.get("origin") or "").startswith("judge:")]
        if not rows:
            continue
        for f in rows:
            lens = f["origin"].split(":", 1)[1] or "unknown"
            a = acc.setdefault(lens, [0, 0])
            st, to = f.get("status"), (f.get("routed_to") or "").strip()
            if to.startswith("accepted:") or (not to.startswith("rejected:") and st in ("routed", "accepted")):
                a[0] += 1
                a[1] += 1
            elif to.startswith("rejected:") or st == "rejected":
                a[1] += 1
    acc = {k: v for k, v in acc.items() if v[1]}
    if not acc:
        return None, [na("no judge rows")]
    return {k: r2(v[0] / v[1]) for k, v in sorted(acc.items())}, reasons


def judge_cost(changes):
    """``{total, estimated, by_phase, by_change}`` in USD from ``judge_runs[]``."""
    by_phase, by_change, total, estimated = {}, {}, 0.0, False
    for c in changes:
        for j in _list(spec_of(c), "judge_runs"):
            usd = j.get("usd")
            if not isinstance(usd, (int, float)) or isinstance(usd, bool):
                continue
            total += usd
            by_phase[j.get("phase") or "unknown"] = by_phase.get(j.get("phase") or "unknown", 0.0) + usd
            by_change[c["id"]] = by_change.get(c["id"], 0.0) + usd
            estimated = estimated or bool(j.get("estimated"))
    if not by_change:
        return None, [na("no judge rows")]
    return {"total": r2(total), "estimated": estimated,
            "by_phase": {k: r2(v) for k, v in sorted(by_phase.items())},
            "by_change": {k: r2(v) for k, v in sorted(by_change.items())}}, []


def automatic_approvals(changes):
    """``{auto, human}``: approvals recorded with ``role: auto`` apart from human ones (REQ-W2-040)."""
    auto = human = 0
    for c in changes:
        for k, a in _approvals(spec_of(c)).items():
            if not isinstance(a, dict) or not (a.get("approved") is True or k == "prod" and a.get("by")):
                continue
            if a.get("role") == "auto":
                auto += 1
            else:
                human += 1
    return {"auto": auto, "human": human}, []


METRICS = ("lead_time_days", "cycle_time_hours", "approval_wait_hours", "throughput_per_week",
           "deploy_frequency_per_week", "change_failure_rate", "time_to_restore_hours", "spec_gap_rate",
           "ripple", "gate_rejection_rate", "estimate_accuracy", "judge_acceptance", "judge_cost_usd",
           "automatic_approvals")


def compute(changes, frm, to):
    """``{metric: {value, reasons}}`` for one set of change records in the period ``[frm, to]``."""
    if not changes:
        return {m: {"value": None, "reasons": [NO_CHANGE]} for m in METRICS}
    fns = {
        "lead_time_days": lambda: lead_time(changes),
        "cycle_time_hours": lambda: cycle_time(changes),
        "approval_wait_hours": lambda: approval_wait(changes),
        "throughput_per_week": lambda: throughput(changes, frm, to),
        "deploy_frequency_per_week": lambda: deploy_frequency(changes, frm, to),
        "change_failure_rate": lambda: change_failure_rate(changes, frm, to),
        "time_to_restore_hours": lambda: time_to_restore(changes),
        "spec_gap_rate": lambda: spec_gap_rate(changes),
        "ripple": lambda: ripple(changes),
        "gate_rejection_rate": lambda: gate_rejection_rate(changes),
        "estimate_accuracy": lambda: estimate_accuracy(changes),
        "judge_acceptance": lambda: judge_acceptance(changes),
        "judge_cost_usd": lambda: judge_cost(changes),
        "automatic_approvals": lambda: automatic_approvals(changes),
    }
    out = {}
    for m in METRICS:
        v, reasons = fns[m]()
        out[m] = {"value": v, "reasons": list(reasons)}
    return out


def compute_all(changes, frm, to, lane=None):
    """``{total, lanes: {lane: …}, changes: [ids]}``; ``lane`` limits the set to one lane."""
    if lane:
        changes = [c for c in changes if lane_of(spec_of(c)) == lane]
    groups = {}
    for c in changes:
        groups.setdefault(lane_of(spec_of(c)), []).append(c)
    return {"total": compute(changes, frm, to),
            "lanes": {k: compute(v, frm, to) for k, v in sorted(groups.items())},
            "changes": sorted(c["id"] for c in changes)}


# --------------------------------------------------------------------------- readiness (REQ-W2-010, 086)
READY_AT = 4
MEASURED_PHASES = ("deployed", "archived")


def is_measured(spec):
    """Deployed or archived, with a ``lane``, a timed ``phase_history`` and at least one gate outcome (A-06)."""
    if spec.get("phase") not in MEASURED_PHASES or not (isinstance(spec.get("lane"), str) and spec["lane"]):
        return False
    hist = _list(spec, "phase_history")
    if not hist or not all(parse_dt(e.get("entered_at")) for e in hist):
        return False
    return bool(_list(spec, "gate_outcomes"))


def readiness(records, check_ids):
    """``{measured, measured_changes, checks: {id: {would_refuse, confirmed, text}}, ready, text}``.

    Each record: ``{id, spec, findings, hits, strict_errors}`` — ``hits`` are the ``checks.jsonl`` lines,
    ``strict_errors`` the number of ``validate --strict`` errors (``schema.strict`` is computed, not recorded)."""
    measured = sorted(r["id"] for r in records if is_measured(spec_of(r)))
    checks = {}
    for cid in check_ids:
        hits = confirmed = 0
        seen = False
        for r in records:
            if cid == "schema.strict":
                if r.get("strict_errors") is not None:
                    seen = True
                    if r["strict_errors"]:
                        hits += 1
                continue
            finds = {f.get("id"): f for f in (r.get("findings") or [])}
            for h in r.get("hits") or []:
                if h.get("check") != cid or not h.get("would_refuse"):
                    continue
                seen = True
                hits += 1
                f = finds.get(h.get("finding"))
                if f and f.get("type") in ("bug", "spec-gap") and f.get("status") not in ("open", "rejected"):
                    confirmed += 1
        entry = {"would_refuse": hits, "confirmed": confirmed}
        if cid == "schema.strict":
            entry["computed"] = True
        entry["text"] = ("no data" if not seen else
                         "%d would refuse · %d confirmed" % (hits, confirmed) if cid != "schema.strict" else
                         "%d change(s) with strict errors (computed)" % hits)
        checks[cid] = entry
    n = len(measured)
    ready = n >= READY_AT
    text = ("ready for 4.0: %d of %d measured changes" % (n, READY_AT) if ready
            else "not ready: %d of %d measured changes" % (n, READY_AT))
    return {"measured": n, "measured_changes": measured, "checks": checks, "ready": ready, "text": text}
