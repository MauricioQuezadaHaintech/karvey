#!/usr/bin/env python3
"""karvey-health-score.py — the 0–10 code health score, computed the same way every time (architecture §1.14 C-17).

    karvey-health-score.py --inputs FILE.json [--json]

The ``karvey-health`` skill runs the tools and writes one JSON with what they returned::

    {"types": {"errors": 3}, "lint": {"errors_per_kloc": 0.5, "warnings_per_kloc": 4},
     "tests": {"passed": 120, "failed": 2, "coverage_pct": 71}, "deadcode": {"items": 6}}

A dimension that is absent or ``null`` had no tool: it is excluded and its weight is redistributed among the
others (``defaults.json:health_weights``). Each sub-score is a named pure function. The same input gives the same
score. The time of the report uses ``KARVEY_TZ``; an invalid zone prints ``fallback zone: {system zone}``.

Exit: 0 · 2 usage · 4 input not found / invalid. Python >= 3.9, stdlib only.
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402

TOOL = "karvey-health-score"
DIMENSIONS = ("types", "tests", "lint", "deadcode")
BANDS = ((9.0, "excellent"), (7.0, "healthy"), (5.0, "attention"), (0.0, "critical"))


def _clamp(x):
    return max(0.0, min(10.0, float(x)))


def score_types(d):
    """10 with no type error; each error takes 0.5."""
    return _clamp(10 - 0.5 * float(d.get("errors") or 0))


def score_lint(d):
    """Per KLOC: an error takes 1, a warning 0.1."""
    return _clamp(10 - float(d.get("errors_per_kloc") or 0) - 0.1 * float(d.get("warnings_per_kloc") or 0))


def score_coverage(pct):
    """Coverage % over 10."""
    return _clamp(float(pct) / 10.0)


def score_tests(d):
    """Pass ratio over 10; with coverage, 80 % pass ratio + 20 % coverage (the coverage bonus)."""
    passed, failed = int(d.get("passed") or 0), int(d.get("failed") or 0)
    if passed + failed == 0:
        return 0.0
    base = 10.0 * passed / (passed + failed)
    if d.get("coverage_pct") is not None:
        return _clamp(0.8 * base + 0.2 * score_coverage(d["coverage_pct"]))
    return _clamp(base)


def score_deadcode(d):
    """Each unused symbol, export or file takes 0.2."""
    return _clamp(10 - 0.2 * float(d.get("items") or 0))


SCORERS = {"types": score_types, "tests": score_tests, "lint": score_lint, "deadcode": score_deadcode}


def compute(inputs, weights=None):
    """``{score, band, sub_scores, weights, excluded}``; deterministic for the same input."""
    weights = dict(weights or (kl.defaults() or {}).get("health_weights") or {})
    present = [k for k in DIMENSIONS if isinstance(inputs.get(k), dict) and float(weights.get(k) or 0) > 0]
    total = sum(float(weights[k]) for k in present)
    subs, eff = {}, {}
    for k in present:
        subs[k] = round(SCORERS[k](inputs[k]), 2)
        eff[k] = round(float(weights[k]) / total, 4) if total else 0.0
    score = round(sum(subs[k] * float(weights[k]) for k in present) / total, 1) if total else None
    band = next(b for lim, b in BANDS if score is None or score >= lim) if score is not None else "not assessable"
    return {"score": score, "band": band, "sub_scores": subs, "weights": eff,
            "excluded": [k for k in DIMENSIONS if k not in present]}


def report_time():
    """``(iso time, fallback line | None)`` in ``KARVEY_TZ`` (the system zone when unset or invalid)."""
    name = os.environ.get("KARVEY_TZ") or ""
    now = datetime.now().astimezone()
    if not name:
        return now.isoformat(timespec="seconds"), None
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(name)).isoformat(timespec="seconds"), None
    except Exception:
        return now.isoformat(timespec="seconds"), "fallback zone: %s (KARVEY_TZ %r is not a valid zone)" % (
            now.tzname() or "system", name[:40])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="karvey-health-score.py", description="0-10 code health score")
    ap.add_argument("--inputs", required=True, help="JSON with the tool results")
    ap.add_argument("--json", action="store_true")
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return kl.EXIT_USAGE if exc.code else 0
    try:
        with open(args.inputs, encoding="utf-8-sig") as fh:
            inputs = json.load(fh)
        if not isinstance(inputs, dict):
            raise ValueError("not a JSON object")
    except (OSError, ValueError) as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("health.input", str(exc))]), args.json)
    res = compute(inputs)
    at, fallback = report_time()
    res["at"] = at
    lines = []
    if fallback:
        lines.append(fallback)
        sys.stderr.write(fallback + "\n")
    lines.append("health %s/10 (%s) at %s" % (res["score"] if res["score"] is not None else "n/a", res["band"], at))
    for k in DIMENSIONS:
        if k in res["sub_scores"]:
            lines.append("  %-9s %5.2f  weight %.2f" % (k, res["sub_scores"][k], res["weights"][k]))
        else:
            lines.append("  %-9s excluded (no tool; weight redistributed)" % k)
    warnings = [kl.issue("health.tz", fallback, severity="warning")] if fallback else []
    return kl.emit(kl.envelope(TOOL, kl.EXIT_OK, result=res, warnings=warnings), args.json, human="\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
