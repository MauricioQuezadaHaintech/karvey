"""Flow metrics (architecture §1.6 of wave2-structural).

@req REQ-W2-003 REQ-W2-004
"""
import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import unittest

import _path
import _gitrepo as g
from karvey_lib import metrics as M

g.isolate_git()
_SPEC = importlib.util.spec_from_file_location("karvey_context_m", str(_path.SCRIPTS_DIR / "karvey-context.py"))
ctxmod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ctxmod)


def run_ctx(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = ctxmod.main(list(argv))
    return code, out.getvalue()

FIX = _path.UNIT_DIR / "fixtures" / "metrics"
ARCH = FIX / "docs/spec/changes/archive"
FRM, TO = "2026-09-01", "2026-09-14"


def _table(text):
    lines = [ln for ln in text.splitlines() if ln.startswith("|")]
    head = [h.strip().lower() for h in lines[0].strip("|").split("|")]
    return [dict(zip(head, [c.strip() for c in ln.strip("|").split("|")])) for ln in lines[2:]]


def records():
    out = []
    for d in sorted(ARCH.iterdir()):
        spec = json.loads((d / "spec.json").read_text(encoding="utf-8"))
        f = d / "findings.md"
        p = d / "PLAN.md"
        findings = [{"id": r["#"], "type": r["type"], "origin": r["origin"], "phase": r["phase"],
                     "status": r["status"]} for r in _table(f.read_text())] if f.exists() else None
        rows = [{"task": r["task"], "estimate": r["estimate_min"], "actual_ai": r["actual_ai_min"],
                 "actual_review": r["actual_review_min"]} for r in _table(p.read_text())] if p.exists() else None
        out.append({"id": spec["change_id"], "spec": spec, "findings": findings, "plan_rows": rows,
                    "archived_on": d.name[:10]})
    return out


class Metrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recs = records()
        cls.all = M.compute_all(cls.recs, FRM, TO)
        cls.t = cls.all["total"]

    def v(self, m, lane=None):
        return (self.all["lanes"][lane] if lane else self.t)[m]["value"]

    def test_REQ_W2_003_every_metric_on_fixtures(self):
        self.assertEqual(self.v("lead_time_days"), 1.25)
        self.assertEqual(self.v("cycle_time_hours")["requirements"], 3.0)
        self.assertEqual(self.v("approval_wait_hours"), {"architecture": 1.0, "qa": 0.75, "requirements": 0.75,
                                                         "tasks": 1.0})
        self.assertEqual(self.v("throughput_per_week"), 2.0)
        self.assertEqual(self.v("deploy_frequency_per_week"), 1.5)
        self.assertEqual(self.v("change_failure_rate"), 0.33)
        self.assertEqual(self.v("time_to_restore_hours"), 4.0)
        self.assertEqual(self.v("spec_gap_rate"), 0.5)
        self.assertEqual(self.v("ripple"), 0.25)
        self.assertEqual(self.v("gate_rejection_rate"), {"architecture": 0.0, "qa": 0.0, "requirements": 0.5,
                                                         "tasks": 0.0})
        self.assertEqual(self.v("estimate_accuracy"), 0.96)
        self.assertEqual(self.v("judge_acceptance"), {"adversarial": 1.0, "security": 0.0})
        self.assertEqual(self.v("judge_cost_usd")["total"], 1.0)
        self.assertTrue(self.v("judge_cost_usd")["estimated"])

    def test_REQ_W2_003_per_lane(self):
        self.assertEqual(sorted(self.all["lanes"]), ["legacy", "ops", "patch", "standard"])
        self.assertEqual(self.v("lead_time_days", "standard"), 2.0)
        self.assertEqual(self.v("lead_time_days", "patch"), 0.5)
        self.assertEqual(self.v("change_failure_rate", "patch"), 0.5)
        self.assertIsNone(self.v("lead_time_days", "ops"))

    def test_REQ_W2_004_legacy_excluded_only_from_that_metric(self):
        self.assertIn("n/a — approvals without time (delta)", self.t["lead_time_days"]["reasons"])
        self.assertIn("n/a — approvals without time (delta)", self.t["approval_wait_hours"]["reasons"])
        self.assertIn("n/a — no production approval (gamma)", self.t["lead_time_days"]["reasons"])
        # delta still counts where it has the data: throughput and approvals
        self.assertEqual(self.v("throughput_per_week"), 2.0)
        self.assertEqual(self.v("automatic_approvals"), {"auto": 1, "human": 9})

    def test_REQ_W2_004_no_metric_returns_zero_for_missing_data(self):
        legacy = self.all["lanes"]["legacy"]
        for m in ("lead_time_days", "cycle_time_hours", "approval_wait_hours", "deploy_frequency_per_week",
                  "change_failure_rate", "time_to_restore_hours", "spec_gap_rate", "gate_rejection_rate",
                  "estimate_accuracy", "judge_acceptance", "judge_cost_usd"):
            self.assertIsNone(legacy[m]["value"], m)
            self.assertTrue(legacy[m]["reasons"], m)

    def test_REQ_W2_040_auto_counted_apart(self):
        self.assertEqual(self.v("automatic_approvals", "standard"), {"auto": 1, "human": 4})

    def test_empty_period(self):
        out = M.compute_all([], FRM, TO)
        for m, r in out["total"].items():
            self.assertIsNone(r["value"], m)
            self.assertEqual(r["reasons"], ["n/a — no archived change in period"], m)

    def test_lane_filter(self):
        out = M.compute_all(self.recs, FRM, TO, lane="patch")
        self.assertEqual(out["changes"], ["beta"])


class Cli(unittest.TestCase):
    """@req REQ-W2-003 REQ-W2-005 — ``karvey-context.py --metrics``."""

    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        shutil.copytree(str(FIX / "docs"), str(self.root / "docs"))
        g.run(["add", "-A"], self.root)
        g.run(["commit", "-q", "-m", "fixtures"], self.root)

    def tearDown(self):
        self.t.cleanup()

    def metrics(self, *extra):
        return run_ctx("--root", str(self.root), "--metrics", "--from", FRM, "--to", TO, "--as-of", TO, "--json",
                       *extra)

    def test_REQ_W2_005_byte_identical_and_read_only(self):
        c1, a = self.metrics()
        c2, b = self.metrics()
        self.assertEqual((c1, c2), (0, 0))
        self.assertEqual(a, b)
        st = subprocess.run(["git", "status", "--porcelain"], cwd=str(self.root), capture_output=True, text=True)
        self.assertEqual(st.stdout, "")

    def test_REQ_W2_005_sorted_keys_no_absolute_path(self):
        _, out = self.metrics()
        self.assertNotIn(str(self.root), out)
        self.assertNotIn(str(self.t.path), out)
        env = json.loads(out)
        self.assertEqual(out.strip(), json.dumps(env, ensure_ascii=False, sort_keys=True))
        self.assertEqual(env["result"]["total"]["lead_time_days"]["value"], 1.25)
        self.assertEqual(env["result"]["period"], {"from": FRM, "to": TO, "as_of": TO})

    def test_REQ_W2_004_empty_period(self):
        _, out = run_ctx("--root", str(self.root), "--metrics", "--from", "2025-01-01", "--to", "2025-01-28",
                         "--as-of", "2025-01-28", "--json")
        tot = json.loads(out)["result"]["total"]
        for m, r in tot.items():
            self.assertIsNone(r["value"], m)
            self.assertEqual(r["reasons"], ["n/a — no archived change in period"])

    def test_lane_and_human_table(self):
        _, out = self.metrics("--lane", "patch")
        self.assertEqual(json.loads(out)["result"]["changes"], ["beta"])
        code, human = run_ctx("--root", str(self.root), "--metrics", "--from", FRM, "--to", TO, "--as-of", TO)
        self.assertEqual(code, 0)
        self.assertIn("lead_time_days", human)
        self.assertIn("n/a — approvals without time (delta)", human)

    def test_bad_date_is_usage(self):
        code, _ = run_ctx("--root", str(self.root), "--metrics", "--from", "09/01", "--json")
        self.assertEqual(code, 2)


class Readiness(unittest.TestCase):
    """@req REQ-W2-010 REQ-W2-086 — ``karvey-context.py --readiness``."""

    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path / "proj"
        shutil.copytree(str(FIX), str(self.root))

    def tearDown(self):
        self.t.cleanup()

    def readiness(self):
        code, out = run_ctx("--root", str(self.root), "--readiness", "--json")
        self.assertEqual(code, 0)
        return json.loads(out)["result"]

    def test_REQ_W2_086_two_measured_not_ready(self):
        r = self.readiness()
        self.assertEqual(r["measured_changes"], ["alpha", "beta"])
        self.assertEqual(r["text"], "not ready: 2 of 4 measured changes")

    def test_REQ_W2_010_five_measured_counts_per_check(self):
        arch = self.root / "docs/spec/changes/archive"
        for n in ("epsilon", "zeta", "eta"):
            d = arch / ("2026-09-13-" + n)
            shutil.copytree(str(arch / "2026-09-10-alpha"), str(d))
            spec = json.loads((d / "spec.json").read_text())
            spec["change_id"] = n
            (d / "spec.json").write_text(json.dumps(spec, indent=2))
        hits = [{"check": "lane.diff", "at": "2026-09-10T10:00:00-03:00", "mode": "warn", "would_refuse": True,
                 "detail": "lane exceeded: 5 > 3 code files", "finding": "F-1"},
                {"check": "lane.diff", "at": "2026-09-10T11:00:00-03:00", "mode": "warn", "would_refuse": True,
                 "detail": "lane exceeded", "finding": "F-3"},
                {"check": "release.manifest", "at": "2026-09-10T12:00:00-03:00", "mode": "warn",
                 "would_refuse": True, "detail": "unmapped abc", "finding": None}]
        (arch / "2026-09-10-alpha/checks.jsonl").write_text("".join(json.dumps(h) + "\n" for h in hits))
        r = self.readiness()
        self.assertEqual(r["measured"], 5)
        self.assertEqual(r["text"], "ready for 4.0: 5 of 4 measured changes")
        self.assertEqual((r["checks"]["lane.diff"]["would_refuse"], r["checks"]["lane.diff"]["confirmed"]), (2, 1))
        self.assertEqual(r["checks"]["release.manifest"]["would_refuse"], 1)
        self.assertEqual(r["checks"]["coverage.requirements"]["text"], "no data")
        self.assertTrue(r["checks"]["schema.strict"]["computed"])
        self.assertEqual(sorted(r["checks"]), sorted(__import__("karvey_lib.modes").modes.check_ids()))


if __name__ == "__main__":
    unittest.main()


class RetroActionOwner(unittest.TestCase):
    """@req REQ-W2-008 — BUG-80 (F-11): an agreed retro action's backlog row carries its owner, in the row itself
    (the backlog table has no owner column, so the Origin cell holds it)."""

    def read(self, rel):
        return (_path.PLUGIN_ROOT / rel).read_text(encoding="utf-8")

    def test_retro_skill_writes_owner_in_the_row(self):
        self.assertIn("retro-{to} · owner: {owner}", self.read("skills/karvey-retro/SKILL.md"))

    def test_backlog_rule_documents_the_owner_cell(self):
        text = self.read("skills/karvey/rules/backlog.md")
        self.assertIn("· owner: ", text)
        self.assertRegex(text, r"\| BL-\d+ \| [0-9-]+ \| retro-[0-9-]+ · owner: [^|]+\| process \|")


class FractionalSecondsKeepTheZone(unittest.TestCase):
    """BUG-54 (F-15): a timestamp with fractional seconds keeps its zone (the zone's digits are not the fraction)."""

    def test_metrics_parse_dt(self):
        for v, off in (("2026-09-10T10:00:00.5Z", 0), ("2026-09-10T10:00:00.5-03:00", -3 * 3600),
                       ("2026-09-10T10:00:00.123456+02:00", 2 * 3600)):
            dt = M.parse_dt(v)
            self.assertIsNotNone(dt, v)
            self.assertEqual(dt.utcoffset().total_seconds(), off, v)
        self.assertEqual(M.hours(M.parse_dt("2026-09-10T10:00:00.5-03:00"),
                                 M.parse_dt("2026-09-10T14:00:00-03:00")), 3.9998611111111112)


def _rec(cid, **spec):
    base = {"change_id": cid, "lane": "standard", "created_at": "2026-09-01T09:00:00-03:00"}
    base.update(spec)
    return {"id": cid, "spec": base, "findings": [], "plan_rows": [], "archived_on": "2026-09-10"}


class MalformedDataIsNa(unittest.TestCase):
    """@req REQ-W2-004 — BUG-57 (F-18): a change with malformed data is left out of THAT metric with an
    ``n/a — reason (change-id)``; the report never crashes and never shows a wrong number."""

    @classmethod
    def setUpClass(cls):
        cls.recs = records()
        cls.ref = M.compute_all(cls.recs, FRM, TO)["total"]

    def compute(self, *extra):
        return M.compute_all(self.recs + list(extra), FRM, TO)["total"]

    def test_malformed_gate_outcome_phases_skipped_with_reason(self):
        bad = _rec("bad", approvals={"requirements": {"generated_at": "2026-09-01T10:00:00-03:00"}},
                   gate_outcomes=[{"gate": "phase", "at": "2026-09-01T11:00:00-03:00", "phases": 5},
                                  {"gate": "phase", "at": "2026-09-01T11:00:00-03:00", "phases": {"x": 1}},
                                  {"gate": ["what"], "at": "2026-09-01T11:00:00-03:00", "phases": ["qa"]}])
        t = self.compute(bad)
        for m in ("approval_wait_hours", "gate_rejection_rate"):
            self.assertEqual(t[m]["value"], self.ref[m]["value"], m)
            self.assertIn("n/a — malformed gate outcome (bad)", t[m]["reasons"], m)

    def test_malformed_gate_outcome_via_cli_exits_0(self):
        tmp = g.TempDir()
        try:
            root = tmp.path / "proj"
            shutil.copytree(str(FIX), str(root))
            p = root / "docs/spec/changes/archive/2026-09-10-alpha/spec.json"
            spec = json.loads(p.read_text(encoding="utf-8"))
            spec["gate_outcomes"][0]["phases"] = 7
            p.write_text(json.dumps(spec), encoding="utf-8")
            code, out = run_ctx("--root", str(root), "--metrics", "--from", FRM, "--to", TO, "--as-of", TO, "--json")
            self.assertEqual(code, 0, out)
            self.assertIn("n/a — malformed gate outcome (alpha)",
                          json.loads(out)["result"]["total"]["gate_rejection_rate"]["reasons"])
        finally:
            tmp.cleanup()

    def test_prod_approval_before_creation_is_na(self):
        bad = _rec("early", created_at="2026-09-05T09:00:00-03:00",
                   approvals={"prod": {"by": "owner", "date": "2026-09-04T09:00:00-03:00"}})
        v, reasons = M.lead_time([bad])
        self.assertIsNone(v)
        self.assertEqual(reasons, ["n/a — prod approval before creation (early)"])
        self.assertEqual(self.compute(bad)["lead_time_days"]["value"], self.ref["lead_time_days"]["value"])

    def test_deploy_without_zone_is_reported_not_hidden(self):
        bad = _rec("nozone", deploys=[{"env": "prod", "at": "2026-09-10T10:00:00", "verification": "regression"},
                                      {"env": "prod", "at": "2026-09-10T12:00:00-03:00", "verification": "pass"}])
        v, reasons = M.time_to_restore([bad])
        self.assertIsNone(v)
        self.assertEqual(reasons, ["n/a — deploy time without zone (nozone)"])
        t = self.compute(bad)["time_to_restore_hours"]
        self.assertEqual(t["value"], self.ref["time_to_restore_hours"]["value"])
        self.assertIn("n/a — deploy time without zone (nozone)", t["reasons"])

    def test_other_malformed_shapes_never_crash(self):
        weird = [
            dict(_rec("f1"), findings={"not": "a list"}),
            dict(_rec("f2"), findings=["row", {"type": "spec-gap", "origin": "judge:x", "routed_to": 3}]),
            dict(_rec("p1"), plan_rows="nope"),
            dict(_rec("p2"), plan_rows=["row", {"task": 5, "estimate": [10], "actual_ai": {"x": 1}}]),
            _rec("a1", approvals=["prod"]),
            _rec("a2", approvals={"prod": "yes", "qa": 3}),
            _rec("j1", judge_runs=[{"phase": "qa", "usd": "1.5"}, {"phase": ["qa"], "usd": 0.5}]),
            _rec("h1", phase_history=[{"phase": ["x"], "entered_at": "2026-09-01T09:00:00-03:00",
                                       "exited_at": "2026-09-01T10:00:00-03:00"}]),
            _rec("d1", deploys=["prod", {"env": ["prod"], "at": 3}]),
            _rec("r1", revision_history="many"),
        ]
        t = self.compute(*weird)  # must not raise
        for m in ("lead_time_days", "deploy_frequency_per_week", "change_failure_rate", "time_to_restore_hours",
                  "estimate_accuracy", "judge_acceptance"):
            self.assertEqual(t[m]["value"], self.ref[m]["value"], m)
        self.assertIn("n/a — malformed findings (f1)", t["spec_gap_rate"]["reasons"])
        self.assertIn("n/a — malformed PLAN rows (p1)", t["estimate_accuracy"]["reasons"])
        self.assertIn("n/a — judge run without numeric usd (j1)", t["judge_cost_usd"]["reasons"])
        self.assertIn("n/a — malformed judge run (j1)", t["judge_cost_usd"]["reasons"])
        self.assertIn("n/a — malformed phase history (h1)", t["cycle_time_hours"]["reasons"])
        self.assertIn("n/a — malformed revision history (r1)", t["ripple"]["reasons"])
        self.assertIn("n/a — deploy without time (d1)", t["time_to_restore_hours"]["reasons"])
        self.assertEqual(t["cycle_time_hours"]["value"], self.ref["cycle_time_hours"]["value"])

    def test_a_crashing_metric_is_na_not_a_crash(self):
        orig = M.ripple
        M.ripple = lambda changes: 1 / 0
        try:
            out = M.compute([_rec("x")], FRM, TO)
        finally:
            M.ripple = orig
        self.assertIsNone(out["ripple"]["value"])
        self.assertEqual(out["ripple"]["reasons"], ["n/a — malformed data (ZeroDivisionError)"])
