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


if __name__ == "__main__":
    unittest.main()
