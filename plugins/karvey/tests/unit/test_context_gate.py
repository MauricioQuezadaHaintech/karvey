"""Dashboard lane column, lane skips and automatic approvals (architecture §1.6 of wave2-structural).

@req REQ-W2-021 REQ-W2-040 REQ-W2-027 REQ-W2-037 REQ-W2-056 REQ-W2-068 REQ-W2-075
"""
import contextlib
import importlib.util
import io
import json
import unittest

import _path
import _gitrepo as g
from _state import make_project

g.isolate_git()
_SPEC = importlib.util.spec_from_file_location("karvey_context_g", str(_path.SCRIPTS_DIR / "karvey-context.py"))
ctxmod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ctxmod)
T0 = "2026-09-25T10:00:00-03:00"
NOW = "2026-09-25T12:00:00-03:00"


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = ctxmod.main(list(argv))
    return code, out.getvalue()


def standard_at_architecture():
    ok = {"generated": True, "approved": True, "by": "owner", "role": "human", "date": T0, "ref": "D-1"}
    return {"change_id": "feat-a", "phase": "architecture", "lane": "standard",
            "skipped": {"mockup": "lane:standard", "design_graphic": "lane:standard"},
            "phase_history": [{"phase": "init", "entered_at": T0, "exited_at": T0},
                              {"phase": "requirements", "entered_at": T0, "exited_at": T0},
                              {"phase": "architecture", "entered_at": T0}],
            "approvals": {"requirements": dict(ok, role="auto", by="agent"),
                          "architecture": {"generated": True, "approved": False}}}


class Dashboard(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        make_project(self.t.path, spec=standard_at_architecture())

    def tearDown(self):
        self.t.cleanup()

    def dash(self, *extra):
        code, out = run("--root", str(self.t.path), "--now", NOW, "--json", *extra)
        return json.loads(out)["result"]

    def test_REQ_W2_021_lane_column_and_lane_skips(self):
        r = self.dash()
        self.assertEqual(r["overview"]["active"][0]["lane"], "standard")
        rows = {x["key"]: x for x in r["approvals"]["feat-a"]["approvals"]}
        for k in ("mockup", "design_graphic"):
            self.assertEqual(rows[k]["state"], "skipped (lane)")
            self.assertEqual(rows[k]["text"], "skipped (lane standard)")
            self.assertNotIn(rows[k]["text"], ("pending", "awaiting approval"))
        self.assertEqual(rows["architecture"]["text"], "awaiting approval")
        self.assertEqual(r["approvals"]["feat-a"]["lane"], "standard")

    def test_REQ_W2_040_auto_approvals_apart(self):
        r = self.dash()
        rows = {x["key"]: x for x in r["approvals"]["feat-a"]["approvals"]}
        self.assertTrue(rows["requirements"]["auto"])
        self.assertTrue(rows["requirements"]["text"].startswith("auto-approved (-y)"))
        self.assertEqual(r["approvals"]["feat-a"]["auto"], ["requirements"])
        code, human = run("--root", str(self.t.path), "--now", NOW)
        self.assertIn("automatic approvals (role auto, not human): requirements", human)
        self.assertIn("lane standard", human)


HEAD = ("| ID | Date | Phase | Origin | Type | Severity | Finding | Status | Routed to |\n"
        "|----|------|-------|--------|------|----------|---------|--------|-----------|\n")


def run_rec(lens, verdict, **over):
    r = {"lens": lens, "phase": "architecture", "model": "model-a", "intra_model": True, "verdict": verdict,
         "findings": {"High": 1} if verdict != "pass" else {}, "discarded": 0, "tokens_in": 10, "tokens_out": 5,
         "usd": 0.5, "estimated": True, "at": T0}
    r.update(over)
    return r


class GateSummary(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        spec = standard_at_architecture()
        spec["phase"] = "tasks"
        spec["skipped"]["infra"] = "no cloud"
        spec["approvals"]["tasks"] = {"generated": True, "approved": False}
        self.f = make_project(self.t.path, spec=spec)
        self.d = self.f.parent
        (self.d / "requirements.md").write_text("REQ-X-001 a\nREQ-X-002 b\n")
        (self.d / "architecture.md").write_text(
            "# A\n\n## 10. Decisions\n- A-01 keep it\n\n## 12. Risks\n- R1 slow\n\n## 13. Deploy\npost-deploy check, rollback by revert\n")
        (self.d / "tasks.md").write_text("### E1.F1.T1 [Backend] x\n**Estimate:** 10 min\nREQ-X-001\n"
                                         "### E1.F1.T2 [human] apply it\n")
        (self.d / "findings.md").write_text(
            "# F\n\n" + HEAD + "| F-01 | d | architecture | judge:security | bug | High | token in log | open | — |\n")

    def tearDown(self):
        self.t.cleanup()

    def gate(self, name="how"):
        code, out = run("--root", str(self.t.path), "--section", "gate", "--change", "feat-a", "--gate", name, "--json")
        env = json.loads(out)
        return env["result"]["gate"], env

    def setruns(self, runs):
        data = json.loads(self.f.read_text())
        data["judge_runs"] = runs
        self.f.write_text(json.dumps(data))

    def test_REQ_W2_027_pass_and_concerns_disagreement_stated(self):
        self.setruns([run_rec("security", "concerns"), run_rec("methods", "pass")])
        g_, _ = self.gate()
        lines = [j["line"] for j in g_["judges"]]
        self.assertTrue(any("disagree" in x and "concerns vs pass" in x for x in lines), lines)
        self.assertTrue(any("F-01 High judge:security" in x for x in lines), lines)
        self.assertEqual(g_["judge_cost_usd"], 1.0)

    def test_REQ_W2_027_missing_judge_not_run(self):
        self.setruns([run_rec("security", "pass")])
        g_, _ = self.gate()
        self.assertIn("judge methods: not run (no run record)", [j["line"] for j in g_["judges"]])

    def test_REQ_W2_037_how_sections(self):
        g_, _ = self.gate()
        s = g_["sections"]
        self.assertEqual(s["decisions"], ["- A-01 keep it"])
        self.assertEqual(s["risks"], ["- R1 slow"])
        self.assertEqual(s["human_tasks"], ["E1.F1.T2 apply it"])
        self.assertEqual(s["uncovered_requirements"], ["REQ-X-002"])
        self.assertEqual(s["contract_gaps"], ["none"])
        self.assertEqual([p["phase"] for p in g_["phases"]], ["architecture", "infra", "tasks"])

    def test_REQ_W2_037_deviation_not_shown_is_an_omission(self):
        (self.d / "deviations.md").write_text("# Deviations\n\n## DEV-01 — v2 grid\n\nalso see DEV-02 in a note\n")
        g_, _ = self.gate()
        self.assertEqual(g_["sections"]["deviations"], ["## DEV-01 — v2 grid"])
        self.assertTrue(any("DEV-02" in o for o in g_["omissions"]), g_["omissions"])

    def test_REQ_W2_068_pipeline_without_security_scan_is_a_deviation(self):
        (self.d / "infra.md").write_text("# Infra\n\n## CI/CD\n- build, test, deploy\n")
        g_, _ = self.gate()
        self.assertEqual(g_["sections"]["deviations"],
                         ["pipeline without a security-scan stage (infra.md; REQ-W2-068)"])
        (self.d / "infra.md").write_text("# Infra\n\n## CI/CD\n- build, test, security-scan, deploy\n")
        g_, _ = self.gate()
        self.assertEqual(g_["sections"]["deviations"], ["none (no deviations.md)"])

    def test_REQ_W2_075_contract_without_rollback_listed_incomplete(self):
        block = {"service": "web", "env": "prod", "health": ["https://example.org/health"],
                 "thresholds": {"error_rate_pct": 1}, "metrics_source": {"kind": "apm", "how": "x"}}
        (self.d / "infra.md").write_text("# Infra\nsecurity-scan\n\n```karvey-postdeploy\n%s\n```\n" % json.dumps(block))
        g_, _ = self.gate()
        self.assertEqual(g_["sections"]["contract_gaps"],
                         ["post-deploy contract web/prod: incomplete (no rollback command)"])
        block["rollback"] = {"command": "platform rollback web", "doc": "runbook"}
        (self.d / "infra.md").write_text("# Infra\nsecurity-scan\n\n```karvey-postdeploy\n%s\n```\n" % json.dumps(block))
        g_, _ = self.gate()
        self.assertEqual(g_["sections"]["contract_gaps"], ["none"])
        (self.d / "infra.md").write_text("# Infra\nsecurity-scan\n")
        g_, _ = self.gate()
        self.assertEqual(g_["sections"]["contract_gaps"], ["post-deploy contract: no karvey-postdeploy block in infra.md"])

    def test_missing_source_named(self):
        (self.d / "tasks.md").unlink()
        g_, _ = self.gate()
        self.assertIn("missing: docs/spec/changes/feat-a/tasks.md", g_["missing"])
        code, human = run("--root", str(self.t.path), "--section", "gate", "--change", "feat-a", "--gate", "how")
        self.assertIn("missing: docs/spec/changes/feat-a/tasks.md", human)

    def test_patch_lane_says_none(self):
        data = json.loads(self.f.read_text())
        data["lane"] = "patch"
        self.f.write_text(json.dumps(data))
        g_, _ = self.gate("release")
        self.assertIn("judges: none for lane patch", [j["line"] for j in g_["judges"]])


class DeployedNotArchived(unittest.TestCase):
    """@req REQ-W2-056"""

    def setUp(self):
        self.t = g.TempDir()
        make_project(self.t.path, spec={"change_id": "feat-d", "phase": "deployed", "lane": "standard",
                                        "phase_history": [{"phase": "init", "entered_at": "2026-09-01T10:00:00-03:00",
                                                           "exited_at": "2026-09-16T10:00:00-03:00"},
                                                          {"phase": "deployed",
                                                           "entered_at": "2026-09-16T10:00:00-03:00"}]},
                     change="feat-d")

    def tearDown(self):
        self.t.cleanup()

    def test_REQ_W2_056_deployed_9_days_not_archived(self):
        code, out = run("--root", str(self.t.path), "--now", NOW, "--json")
        ov = json.loads(out)["result"]["overview"]
        self.assertEqual(ov["deployed_not_archived"], [{"change": "feat-d", "days": 9,
                                                        "text": "deployed 9 d, not archived"}])
        code, human = run("--root", str(self.t.path), "--now", NOW)
        self.assertIn("deployed 9 d, not archived", human)

    def test_within_seven_days_silent(self):
        code, out = run("--root", str(self.t.path), "--now", "2026-09-20T10:00:00-03:00", "--json")
        self.assertEqual(json.loads(out)["result"]["overview"]["deployed_not_archived"], [])


if __name__ == "__main__":
    unittest.main()
