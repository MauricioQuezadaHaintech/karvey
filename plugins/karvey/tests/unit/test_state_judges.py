"""judge-run and the blocking judge mode (architecture §1.4, §1.7 of wave2-structural).

@req REQ-W2-028 REQ-W2-029 REQ-W2-030
"""
import json
import os
import unittest
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from _state import make_project, run_json
from karvey_lib import approval as ap

g.isolate_git()
T0 = "2026-09-25T10:00:00-03:00"
PROJECT = {"git_platform": "github", "repos": ["r"], "spec_repo": "r",
           "branch_flow": {"integration": "main", "production": "main"}}
HEAD = ("| ID | Date | Phase | Origin | Type | Severity | Finding | Status | Routed to |\n"
        "|----|------|-------|--------|------|----------|---------|--------|-----------|\n")


def run_rec(**over):
    r = {"lens": "methods", "model": "model-a", "intra_model": True, "verdict": "concerns",
         "findings": {"High": 1}, "discarded": 0, "tokens_in": 100, "tokens_out": 10, "usd": 0.25, "estimated": True,
         "at": T0}
    r.update(over)
    return r


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        self.envp = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg"), ap.COMPAT_ENV: ""})
        self.envp.start()

    def tearDown(self):
        self.envp.stop()
        self.t.cleanup()

    def put(self, mode="advisory", finding="| F-01 | 2026-09-25 | requirements | judge:methods | spec-gap | High | x (a:1) | open | — |\n"):
        pj = dict(PROJECT, judges={"mode": mode})
        self.f = make_project(self.root, project=pj, spec={
            "change_id": "feat-a", "phase": "requirements", "lane": "standard",
            "phase_history": [{"phase": "init", "entered_at": T0, "exited_at": T0},
                              {"phase": "requirements", "entered_at": T0}],
            "approvals": {"requirements": {"generated": True, "approved": False}}})
        (self.f.parent / "findings.md").write_text("# Findings\n\n" + HEAD + finding)

    def st(self, *argv):
        return run_json(*(list(argv) + ["--root", str(self.root)]))

    def read(self):
        return json.loads(self.f.read_text(encoding="utf-8"))

    def approve(self):
        return self.st("approve", "feat-a", "requirements", "--by", "owner", "--role", "human", "--ref", "D-1")


class Blocking(Base):
    def test_REQ_W2_028_advisory_open_high_still_approves(self):
        self.put("advisory")
        code, env = self.approve()
        self.assertEqual(code, 0, env)
        self.assertTrue(self.read()["approvals"]["requirements"]["approved"])

    def test_REQ_W2_028_blocking_open_critical_refused_naming_it(self):
        self.put("blocking", "| F-03 | 2026-09-25 | requirements | judge:domain | bug | Critical | y (a:1) | open | — |\n")
        before = self.f.read_bytes()
        code, env = self.approve()
        self.assertEqual(code, 3)
        self.assertIn("F-03", env["errors"][0]["message"])
        self.assertEqual(self.f.read_bytes(), before)

    def test_blocking_ignores_routed_other_phase_and_low(self):
        rows = ("| F-01 | d | requirements | judge:methods | bug | High | x | routed | BUG-1 |\n"
                "| F-02 | d | architecture | judge:security | bug | Critical | x | open | — |\n"
                "| F-03 | d | requirements | judge:methods | bug | Low | x | open | — |\n"
                "| F-04 | d | requirements | qa | bug | Critical | x | open | — |\n")
        self.put("blocking", rows)
        code, env = self.approve()
        self.assertEqual(code, 0, env)


class JudgeRun(Base):
    def write(self, recs):
        p = self.t.path / "runs.json"
        p.write_text(json.dumps(recs))
        return str(p)

    def test_REQ_W2_030_records_appended_and_total_computable(self):
        self.put()
        code, env = self.st("judge-run", "feat-a", "requirements", "--from",
                            self.write([run_rec(), run_rec(lens="domain", usd=0.5)]))
        self.assertEqual(code, 0, env)
        self.assertEqual(env["result"]["change_usd"], 0.75)
        runs = self.read()["judge_runs"]
        self.assertEqual([r["lens"] for r in runs], ["methods", "domain"])
        self.assertTrue(all(r["phase"] == "requirements" for r in runs))

    def test_REQ_W2_029_record_without_model_refused(self):
        self.put()
        before = self.f.read_bytes()
        rec = run_rec()
        del rec["model"]
        code, env = self.st("judge-run", "feat-a", "requirements", "--from", self.write([rec]))
        self.assertEqual(code, 3)
        self.assertIn("model", env["errors"][0]["message"])
        self.assertEqual(self.f.read_bytes(), before)

    def test_non_numeric_cost_refused(self):
        self.put()
        code, env = self.st("judge-run", "feat-a", "requirements", "--from", self.write([run_rec(usd="cheap")]))
        self.assertEqual(code, 3)

    def test_nan_and_infinite_cost_refused(self):
        """BUG-61 (F-22): NaN / Infinity would make spec.json non-standard JSON."""
        for bad in (float("nan"), float("inf")):
            self.put()
            before = self.f.read_bytes() if hasattr(self, "f") else None
            code, env = self.st("judge-run", "feat-a", "requirements", "--from", self.write([run_rec(usd=bad)]))
            self.assertEqual(code, 3, env)
            if before is not None:
                self.assertEqual(self.f.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
