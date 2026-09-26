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


if __name__ == "__main__":
    unittest.main()
