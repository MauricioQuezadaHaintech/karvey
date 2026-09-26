"""The sponsor page (architecture §1.13, C-13): the allow-listed model and ``karvey-sponsor.py``.

@req REQ-W3-021 REQ-W3-022 REQ-W3-023 REQ-W3-080
"""
import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import _path
from karvey_lib import sponsor

FIX = _path.UNIT_DIR / "fixtures" / "sponsor"
CHANGE = "sample-change"
TODAY = "2026-10-14"


class Tree:
    """A temp copy of the sponsor fixture a test can edit."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-sponsor-"))
        self.root = self.tmp / "proj"
        shutil.copytree(str(FIX), str(self.root))
        self.cdir = self.root / "docs/spec/changes" / CHANGE

    def spec(self):
        return json.loads((self.cdir / "spec.json").read_text(encoding="utf-8"))

    def write_spec(self, data):
        (self.cdir / "spec.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    def cleanup(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)


class Model(unittest.TestCase):
    """@req REQ-W3-021 REQ-W3-080"""

    def setUp(self):
        self.t = Tree()

    def tearDown(self):
        self.t.cleanup()

    def model(self):
        return sponsor.build_model(self.t.root, CHANGE, today=TODAY)

    def test_REQ_W3_021_scope_phase_cost_risks_questions_each_dated(self):
        m = self.model()
        self.assertIn("company account", m["scope"]["summary"])
        self.assertEqual(m["scope"]["areas"], ["Sign-in with the company account", "Access ends with the account"])
        self.assertEqual(m["progress"]["phase"], "Technical design")
        self.assertEqual((m["cost"]["usd"], m["cost"]["estimated_share"], m["cost"]["judge_usd"]), (41.2, 0.25, 2.1))
        self.assertEqual(m["risks"]["open"], 1)
        for sec in ("scope", "progress", "cost", "risks", "waiting"):
            self.assertRegex(m[sec]["as_of"] or "", r"^\d{4}-\d{2}-\d{2}$", sec)

    def test_REQ_W3_021_owner_matched_by_role_or_name_case_insensitively(self):
        qs = self.model()["waiting"]["questions"]
        # Q-01 owner "area lead" = the sponsor's name; Q-02 is someone else's; Q-03 resolved; Q-04 another change
        self.assertEqual([q["question"] for q in qs], ["Should people who leave lose access the same day?"])
        self.assertTrue(qs[0]["overdue"])
        self.assertIn("nightly check", qs[0]["context"])

    def test_REQ_W3_021_sponsor_who_is_the_approver_sees_the_pending_gate(self):
        self.assertEqual(self.model()["waiting"]["gates"], [{"step": "Technical design", "gate": "how"}])

    def test_sponsor_who_is_not_the_approver_sees_no_gate(self):
        pj = self.t.root / "docs/spec/project.json"
        data = json.loads(pj.read_text(encoding="utf-8"))
        data["stakeholders"]["approver"]["name"] = "Someone else"
        pj.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.model()["waiting"]["gates"], [])

    def test_REQ_W3_021_no_effort_is_not_measured(self):
        s = self.t.spec()
        del s["effort"]
        self.t.write_spec(s)
        c = self.model()["cost"]
        self.assertEqual((c["measured"], c["text"]), (False, "Not measured"))
        self.assertNotIn("usd", c)

    def test_REQ_W3_021_ids_paths_and_commands_removed_from_the_body(self):
        body = json.dumps({k: v for k, v in self.model().items() if k != "change"})
        self.assertNotRegex(body, r"\b(?:REQ-[A-Z0-9-]+|F-\d+|D-\d+|Q-\d+|R-\d+)\b")
        self.assertNotIn("docs/spec", body)
        self.assertNotIn("purge", body)

    def test_REQ_W3_080_risk_state_through_the_wording_table(self):
        states = [r["state"] for r in self.model()["risks"]["items"]]
        self.assertEqual(states, ["being watched", "reduced"])

    def test_spanish_change_uses_the_spanish_wording(self):
        s = self.t.spec()
        s["language"] = "es"
        self.t.write_spec(s)
        m = self.model()
        self.assertEqual((m["progress"]["phase"], m["risks"]["items"][1]["state"]), ("Diseño técnico", "reducido"))

    def test_unlisted_language_falls_back_to_english_with_a_note(self):
        s = self.t.spec()
        s["language"] = "it"
        self.t.write_spec(s)
        m = self.model()
        self.assertEqual(m["language"], "en")
        self.assertTrue(m["language_note"])


if __name__ == "__main__":
    unittest.main()
