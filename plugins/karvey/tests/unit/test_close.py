"""The gate-close script (architecture §1.22-bis, C-26).

@req REQ-W3-022 REQ-W3-014
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _path

FIX = _path.UNIT_DIR / "fixtures" / "sponsor"
TOOL = _path.SCRIPTS_DIR / "karvey-close.py"
CHANGE = "sample-change"
CONN = "Server=db.example;Database=sales;" + "Pass" + "word=" + "z" * 12


class Close(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-close-"))
        self.root = self.tmp / "proj"
        shutil.copytree(str(FIX), str(self.root))
        self.cdir = self.root / "docs/spec/changes" / CHANGE
        self.env = dict(os.environ, XDG_STATE_HOME=str(self.tmp / "state"))

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def close(self, outcome="approved", phase="architecture", *extra):
        cp = subprocess.run([sys.executable, str(TOOL), CHANGE, phase, "--outcome", outcome, "--root",
                             str(self.root), "--json"] + list(extra), capture_output=True, text=True, timeout=120,
                            env=self.env)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        return json.loads(cp.stdout)["result"]

    def spec(self):
        return json.loads((self.cdir / "spec.json").read_text(encoding="utf-8"))

    def test_steps_run_in_the_fixed_order_and_effort_is_the_last_write(self):
        before = self.spec()
        res = self.close()
        self.assertEqual(res["order"], ["sponsor", "events", "risks", "effort", "checkpoint"])
        self.assertEqual(res["failures"], [])
        hist = json.loads((self.cdir / "sponsor-history.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        after = self.spec()
        self.assertEqual(len(after["effort"]), len(before["effort"]) + 1)
        self.assertGreaterEqual(after["effort"][-1]["at"], hist["at"])
        self.assertEqual(after["effort"][-1]["phase"], "architecture")
        self.assertIn("fresh session", " ".join(res["steps"][-1]["lines"]))

    def test_a_failing_sponsor_build_is_reported_and_the_next_steps_still_run(self):
        risks = self.cdir / "risks.md"
        risks.write_text(risks.read_text(encoding="utf-8").replace("Sign-in records kept longer than allowed",
                                                                   "The job reads " + CONN), encoding="utf-8")
        res = self.close()
        sponsor = res["steps"][0]
        self.assertFalse(sponsor["ok"])
        self.assertIn("leak check", sponsor["error"])
        self.assertNotIn("z" * 12, json.dumps(res))
        self.assertTrue(res["steps"][3]["ok"])
        self.assertEqual(self.spec()["effort"][-1]["phase"], "architecture")

    def test_changes_requested_also_regenerates_the_page(self):
        self.close("changes_requested")
        hist = [json.loads(x) for x in (self.cdir / "sponsor-history.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(hist[-1]["outcome"], "changes_requested")
        self.assertTrue((self.cdir / "sponsor.html").is_file())

    def test_the_gate_outcome_is_never_changed(self):
        before = self.spec()
        self.close("changes_requested")
        after = self.spec()
        for k in ("phase", "approvals", "gate_outcomes", "phase_history"):
            self.assertEqual(after.get(k), before.get(k), k)

    def test_qa_close_prints_the_due_qa_event_once(self):
        pj = self.root / "docs/spec/project.json"
        data = json.loads(pj.read_text(encoding="utf-8"))
        data["notifications"] = {"channel": "slack", "target": "#team-sample", "events": ["qa"]}
        pj.write_text(json.dumps(data), encoding="utf-8")
        a = self.close("approved", "qa", "--verdict", "pass", "--run-id", "qa-1")
        b = self.close("approved", "qa", "--verdict", "pass", "--run-id", "qa-2")
        self.assertEqual(len(a["steps"][1]["payloads"]), 1)
        self.assertEqual(a["steps"][1]["payloads"][0]["run_id"], "qa-1")
        self.assertEqual(b["steps"][1]["payloads"], [])
        self.assertIn("already sent", " ".join(b["steps"][1]["skipped"]))


    def test_REQ_W3_033_qa_close_lists_the_owners_to_ask_in_order(self):
        reg = self.cdir / "risks.md"
        reg.write_text(reg.read_text(encoding="utf-8").rstrip("\n") + "\n| R-3 | Late import | Medium | High | "
                       "data owner | import fails twice | retry | open | 2026-10-02 |\n", encoding="utf-8")
        res = self.close("approved", "qa", "--verdict", "pass")
        step = res["steps"][2]
        self.assertEqual(step["step"], "risks")
        self.assertEqual([(a["risk"], a["owner"]) for a in step["ask"]],
                         [("R-1", "security officer"), ("R-3", "data owner")])
        self.assertIn("karvey-state.py risk", step["note"])

    def test_no_risk_review_outside_qa_and_release(self):
        res = self.close()
        self.assertEqual(res["steps"][2]["ask"], [])
        self.assertEqual(res["steps"][2]["note"], "no risk review at this gate")

class OnePhasePerSession(unittest.TestCase):
    """@req REQ-W3-013 — step 5 compares the capture's context reading with the checkpoint threshold."""
    setUp, tearDown, close = Close.setUp, Close.tearDown, Close.close

    def capture(self, pct=None, tokens=None):
        sys.path.insert(0, str(_path.SCRIPTS_DIR))
        from karvey_lib import effort as ef
        from karvey_lib import project as pj
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.tmp / "state")}):
            d = pj.state_dir(self.root) / ef.CAPTURE_DIR
        d.mkdir(parents=True, exist_ok=True)
        rec = {"root_key": ef.root_key(self.root), "usd": 0.5, "transcript": None, "context_pct": pct,
               "context_tokens": tokens, "at": "2026-01-01T00:00:00+00:00"}
        (d / "0123456789abcdef.json").write_text(json.dumps(rec), encoding="utf-8")

    def step5(self):
        res = self.close()
        self.assertEqual(res["order"][-1], "checkpoint")
        return res["steps"][-1]

    def test_REQ_W3_013_at_the_red_threshold_recommends_a_fresh_session(self):
        self.capture(pct=55)
        s = self.step5()
        self.assertEqual(s["context"], "recommend")
        self.assertIn("recommend: checkpoint + fresh session before the next skill", " ".join(s["lines"]))

    def test_below_the_threshold_only_offers(self):
        self.capture(pct=20)
        s = self.step5()
        self.assertEqual(s["context"], "offer")
        text = " ".join(s["lines"])
        self.assertIn("/karvey-checkpoint save", text)
        self.assertNotIn("recommend:", text)
        self.assertIn("continuing in this session is allowed", text)

    def test_tokens_are_the_fallback_when_the_percentage_is_unknown(self):
        self.capture(tokens=160000)
        self.assertEqual(self.step5()["context"], "recommend")

    def test_no_reading_says_so(self):
        s = self.step5()
        self.assertEqual(s["context"], "unavailable")
        self.assertIn("context reading unavailable", " ".join(s["lines"]))


class Observed(unittest.TestCase):
    """@req REQ-W3-013 — ``observed`` lists the plugin text a session opened; a footnote-only rule is flagged."""

    def test_a_footnote_only_rule_that_was_opened_is_listed(self):
        tmp = Path(tempfile.mkdtemp(prefix="karvey-observed-"))
        try:
            def read(path):
                return {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "name": "Read", "input": {"file_path": path}}]}}
            lines = [read("/work/plugin/skills/karvey-impl/SKILL.md"),
                     read("/work/plugin/skills/karvey/rules/gates.md"),
                     read("/work/plugin/skills/karvey/rules/deploy-workflow.md"),
                     read("/work/app/src/main.py"), {"type": "user", "message": {"content": "hi"}}]
            tr = tmp / "session.jsonl"
            tr.write_text("\n".join(json.dumps(x) for x in lines) + "\nnot json\n", encoding="utf-8")
            cp = subprocess.run([sys.executable, str(_path.SCRIPTS_DIR / "karvey-context-budget.py"), "observed",
                                 "--transcript", str(tr), "--skill", "karvey-impl", "--json"],
                                capture_output=True, text=True, timeout=60)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            res = json.loads(cp.stdout)["result"]
            self.assertEqual(res["opened"], ["skills/karvey-impl/SKILL.md", "skills/karvey/rules/deploy-workflow.md",
                                             "skills/karvey/rules/gates.md"])
            self.assertEqual(res["outside_load_list"], ["skills/karvey/rules/deploy-workflow.md"])
            self.assertNotIn("/work/", cp.stdout)
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
