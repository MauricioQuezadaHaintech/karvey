"""Merged human gates: approve-gate, the imported marker, gate mode (architecture §1.4, §1.8 of wave2-structural).

@req REQ-W2-034 REQ-W2-036 REQ-W2-039 REQ-W2-080
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


def ok():
    return {"generated": True, "approved": True, "by": "owner", "role": "human", "date": T0, "ref": "D-1"}


def hist(*phases):
    return [{"phase": p, "entered_at": T0, "exited_at": T0} for p in phases[:-1]] + \
        [{"phase": phases[-1], "entered_at": T0}]


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        self.envp = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg"), ap.COMPAT_ENV: ""})
        self.envp.start()

    def tearDown(self):
        self.envp.stop()
        self.t.cleanup()

    def put(self, spec, project=None):
        base = {"change_id": "feat-a", "lane": "standard"}
        base.update(spec)
        self.f = make_project(self.root, project=project or PROJECT, spec=base)

    def st(self, *argv):
        return run_json(*(list(argv) + ["--root", str(self.root)]))

    def read(self):
        return json.loads(self.f.read_text(encoding="utf-8"))

    def gate(self, name, role="human", ref="D-1"):
        return self.st("approve-gate", "feat-a", name, "--by", "owner", "--role", role, "--ref", ref)

    def refused(self, argv, needle):
        before = self.f.read_bytes()
        c, env = self.st(*argv)
        self.assertEqual(c, 3, env)
        self.assertIn(needle, env["errors"][0]["message"])
        self.assertEqual(self.f.read_bytes(), before)
        return env


class How(Base):
    def spec(self, tasks_generated=True):
        return {"phase": "tasks", "skipped": {"infra": "no cloud"},
                "approvals": {"requirements": ok(),
                              "architecture": {"generated": True, "approved": False},
                              "tasks": {"generated": tasks_generated, "approved": False}},
                "phase_history": hist("init", "requirements", "architecture", "tasks")}

    def test_REQ_W2_034_how_with_infra_skipped_one_record_one_outcome(self):
        self.put(self.spec())
        c, env = self.gate("how")
        self.assertEqual(c, 0, env)
        data = self.read()
        arch, tasks = data["approvals"]["architecture"], data["approvals"]["tasks"]
        for k in ("approved", "by", "role", "ref", "date", "evidence"):
            self.assertEqual(arch[k], tasks[k], k)
        self.assertTrue(arch["approved"])
        self.assertNotIn("infra", data["approvals"])
        self.assertEqual(len(data["gate_outcomes"]), 1)
        self.assertEqual((data["gate_outcomes"][0]["gate"], data["gate_outcomes"][0]["phases"]),
                         ("how", ["architecture", "tasks"]))
        self.assertEqual(env["result"]["skipped"], ["infra"])

    def test_REQ_W2_036_tasks_not_generated_refused_naming_it(self):
        self.put(self.spec(tasks_generated=False))
        env = self.refused(("approve-gate", "feat-a", "how", "--by", "o", "--role", "human", "--ref", "D-1"),
                           "tasks.md")
        self.assertIn("tasks", env["result"]["missing"][0])

    def test_what_passes_lane_skipped_mockup(self):
        self.put({"phase": "requirements", "approvals": {"requirements": {"generated": True, "approved": False}},
                  "phase_history": hist("init", "requirements")})
        c, env = self.gate("what")
        self.assertEqual(c, 0, env)
        self.assertEqual(env["result"]["approved"], ["requirements"])
        self.assertEqual(env["result"]["skipped"], ["mockup", "design_graphic"])

    def test_nothing_to_approve_refused(self):
        self.put({"phase": "architecture", "approvals": {"requirements": ok()},
                  "phase_history": hist("init", "requirements", "architecture")})
        self.refused(("approve-gate", "feat-a", "what", "--by", "o", "--role", "human", "--ref", "D-1"),
                     "nothing to approve")


class Release(Base):
    def spec(self):
        a = {k: ok() for k in ("requirements", "architecture", "tasks")}
        a["qa"] = {"generated": True, "approved": False}
        return {"phase": "qa", "approvals": a, "skipped": {"infra": "no cloud"},
                "phase_history": hist("init", "requirements", "architecture", "tasks", "impl", "test", "qa")}

    def test_release_without_prod_marker_records_qa_only(self):
        self.put(self.spec())
        c, env = self.gate("release")
        self.assertEqual(c, 0, env)
        self.assertTrue(self.read()["approvals"]["qa"]["approved"])
        self.assertIn("pending", env["result"]["prod"])
        self.assertIsNone(ap.read_ledger(self.root, "feat-a")[0])

    def test_release_with_prod_marker_writes_the_ledger(self):
        self.put(self.spec())
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod")
        c, env = self.gate("release")
        self.assertEqual(c, 0, env)
        led, _ = ap.read_ledger(self.root, "feat-a")
        self.assertEqual((led["prod"]["by"], led["prod"]["role"]), ("owner", "human"))
        self.assertNotIn("prod", self.read()["approvals"])  # D-03: never spec.json

    def test_REQ_W2_040_auto_refused_when_prod_would_be_written(self):
        self.put(self.spec())
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod")
        self.refused(("approve-gate", "feat-a", "release", "--by", "agent", "--role", "auto", "--ref", "D-1"),
                     "never automatic")

    def test_auto_release_without_prod_marker_records_qa(self):
        self.put(self.spec())
        c, env = self.gate("release", role="auto")
        self.assertEqual(c, 0, env)
        self.assertEqual(self.read()["approvals"]["qa"]["role"], "auto")


class Imported(Base):
    def spec(self):
        return {"phase": "requirements", "approvals": {"requirements": {"generated": False, "approved": False}},
                "phase_history": hist("init", "requirements")}

    def test_generated_imported_marks_the_phase(self):
        self.put(self.spec())
        c, env = self.st("generated", "feat-a", "requirements", "--imported")
        self.assertEqual(c, 0, env)
        self.assertTrue(self.read()["approvals"]["requirements"]["imported"])

    def test_REQ_W2_080_imported_without_marker_exit_3(self):
        self.put(self.spec())
        self.st("generated", "feat-a", "requirements", "--imported")
        self.refused(("approve", "feat-a", "requirements", "--by", "o", "--role", "human", "--ref", "D-1"),
                     "imported phase")
        self.refused(("approve-gate", "feat-a", "what", "--by", "o", "--role", "human", "--ref", "D-1"),
                     "imported phase")

    def test_imported_with_human_marker_approved_and_kept(self):
        self.put(self.spec())
        self.st("generated", "feat-a", "requirements", "--imported")
        ap.write_marker(self.root, "plan", "feat-a", "aprobado")
        c, env = self.st("approve", "feat-a", "requirements", "--by", "o", "--role", "human", "--ref", "D-1")
        self.assertEqual(c, 0, env)
        r = self.read()["approvals"]["requirements"]
        self.assertTrue(r["approved"] and r["imported"])

    def test_imported_auto_refused_even_with_marker(self):
        self.put(self.spec())
        self.st("generated", "feat-a", "requirements", "--imported")
        ap.write_marker(self.root, "plan", "feat-a", "aprobado")
        self.refused(("approve", "feat-a", "requirements", "--by", "a", "--role", "auto", "--ref", "D-1"),
                     "not human")


if __name__ == "__main__":
    unittest.main()
