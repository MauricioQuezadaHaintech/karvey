"""Gate outcomes, generated_at and role auto (architecture §1.4 of wave2-structural).

@req REQ-W1-006 REQ-W2-001 REQ-W2-038 REQ-W2-040 REQ-W2-042
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


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        self.envp = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg"), ap.COMPAT_ENV: ""})
        self.envp.start()
        self.f = make_project(self.root, spec={
            "change_id": "feat-a", "phase": "requirements", "approvals": {},
            "phase_history": [{"phase": "init", "entered_at": T0, "exited_at": T0},
                              {"phase": "requirements", "entered_at": T0}]})

    def tearDown(self):
        self.envp.stop()
        self.t.cleanup()

    def st(self, *argv):
        return run_json(*(list(argv) + ["--root", str(self.root)]))

    def read(self):
        return json.loads(self.f.read_text(encoding="utf-8"))

    def refused(self, argv, needle):
        before = self.f.read_bytes()
        c, env = self.st(*argv)
        self.assertEqual(c, 3, env)
        self.assertIn(needle, env["errors"][0]["message"])
        self.assertEqual(self.f.read_bytes(), before)


class GeneratedAt(Base):
    def test_REQ_W2_001_generated_at_written_once(self):
        c, env = self.st("generated", "feat-a", "requirements")
        self.assertEqual(c, 0, env)
        first = self.read()["approvals"]["requirements"]["generated_at"]
        self.st("generated", "feat-a", "requirements")
        self.assertEqual(self.read()["approvals"]["requirements"]["generated_at"], first)

    def test_generated_at_survives_approve(self):
        self.st("generated", "feat-a", "requirements")
        first = self.read()["approvals"]["requirements"]["generated_at"]
        self.st("approve", "feat-a", "requirements", "--by", "owner", "--role", "human", "--ref", "D-1")
        self.assertEqual(self.read()["approvals"]["requirements"]["generated_at"], first)


class Outcomes(Base):
    def test_REQ_W2_001_request_changes_then_approve_two_entries(self):
        self.st("generated", "feat-a", "requirements")
        c, env = self.st("outcome", "feat-a", "requirements", "changes_requested", "--by", "owner", "--role", "human",
                         "--ref", "D-1", "--reason", "REQ-3 is vague", "--date", "2026-09-25T10:40:00-03:00")
        self.assertEqual(c, 0, env)
        self.assertEqual(self.read()["phase"], "requirements")
        c, env = self.st("approve", "feat-a", "requirements", "--by", "owner", "--role", "human", "--ref", "D-1",
                         "--date", "2026-09-25T11:30:00-03:00")
        self.assertEqual(c, 0, env)
        data = self.read()
        log = data["gate_outcomes"]
        self.assertEqual([e["outcome"] for e in log], ["changes_requested", "approved"])
        self.assertEqual([e["at"] for e in log], ["2026-09-25T10:40:00-03:00", "2026-09-25T11:30:00-03:00"])
        self.assertEqual(log[0]["reason"], "REQ-3 is vague")
        self.assertEqual(log[1]["phases"], ["requirements"])
        self.assertTrue(data["approvals"]["requirements"]["generated_at"])  # wait computable

    def test_REQ_W2_001_outcome_without_role_or_ref_refused_byte_identical(self):
        self.refused(("outcome", "feat-a", "requirements", "changes_requested", "--by", "owner", "--ref", "D-1"),
                     "missing: --role")
        self.refused(("outcome", "feat-a", "requirements", "changes_requested", "--by", "owner", "--role", "human"),
                     "missing: --ref")

    def test_REQ_W2_042_empty_reason_recorded_as_no_reason_given(self):
        c, env = self.st("outcome", "feat-a", "requirements", "changes_requested", "--by", "owner", "--role", "human",
                         "--ref", "D-1", "--reason", "  ")
        self.assertEqual(c, 0, env)
        self.assertEqual(self.read()["gate_outcomes"][0]["reason"], "no reason given")

    def test_REQ_W2_038_plan_exception_is_not_a_gate(self):
        c, env = self.st("outcome", "feat-a", "requirements", "changes_requested", "--by", "owner", "--role", "human",
                         "--ref", "D-1", "--kind", "plan-exception", "--reason", "outside the plan")
        self.assertEqual(c, 0, env)
        e = self.read()["gate_outcomes"][0]
        self.assertEqual(e["kind"], "plan-exception")
        self.assertEqual(self.read()["phase"], "requirements")

    def test_unknown_target_refused(self):
        self.refused(("outcome", "feat-a", "nowhere", "changes_requested", "--by", "o", "--role", "human",
                      "--ref", "D-1"), "unknown phase or gate")

    def test_outcomes_are_append_only(self):
        for r in ("a", "b"):
            self.st("outcome", "feat-a", "requirements", "changes_requested", "--by", "o", "--role", "human",
                    "--ref", "D-1", "--reason", r)
        self.assertEqual([e["reason"] for e in self.read()["gate_outcomes"]], ["a", "b"])


class Auto(Base):
    def test_REQ_W2_040_y_path_records_role_auto(self):
        c, env = self.st("approve", "feat-a", "requirements", "--by", "agent", "--role", "auto", "--ref", "D-1")
        self.assertEqual(c, 0, env)
        data = self.read()
        self.assertEqual(data["approvals"]["requirements"]["role"], "auto")
        self.assertEqual(data["gate_outcomes"][0]["role"], "auto")

    def test_REQ_W2_040_prod_auto_refused(self):
        self.refused(("approve", "feat-a", "prod", "--by", "agent", "--role", "auto", "--ref", "D-1"),
                     "production approval is never automatic")


if __name__ == "__main__":
    unittest.main()
