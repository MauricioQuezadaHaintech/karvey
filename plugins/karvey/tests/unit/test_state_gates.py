"""Merged human gates: approve-gate, the imported marker, gate mode (architecture §1.4, §1.8 of wave2-structural).

@req REQ-W2-034 REQ-W2-036 REQ-W2-039 REQ-W2-080 REQ-W2-047
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
    def put(self, spec, project=None):
        super().put(spec, project)
        g.commit_all(self.root, "fixture")  # D-35: a prod approval is bound to a commit

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

    def test_project_wide_prod_marker_does_not_approve_prod_at_the_release_gate(self):
        """BUG-70 (F-41): the release gate followed the `_project` fallback, so one project-wide prod phrase
        approved production of any change (the rule BUG-41 set for `approve prod`)."""
        self.put(self.spec())
        ap.write_marker(self.root, "prod", "_project", "aprobado, pasa a prod")
        c, env = self.gate("release")
        self.assertEqual(c, 0, env)
        self.assertIn("pending", env["result"]["prod"])
        self.assertIsNone(ap.read_ledger(self.root, "feat-a")[0])

    def test_release_gate_consumes_the_prod_marker(self):
        """BUG-70 (F-41): one approval, one change — the marker is consumed once prod is written."""
        self.put(self.spec())
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod")
        c, env = self.gate("release")
        self.assertEqual(c, 0, env)
        m, status = ap.read_marker(self.root, "feat-a")
        self.assertEqual(status, "ok")
        self.assertIsNotNone(m["consumed_at"])

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


class Mode(Base):
    """@req REQ-W2-039"""
    def spec(self):
        return {"phase": "architecture", "skipped": {"infra": "no cloud"},
                "approvals": {"requirements": ok(), "architecture": {"generated": True, "approved": False}},
                "phase_history": hist("init", "requirements", "architecture")}

    def test_REQ_W2_039_313_without_setting_is_granular(self):
        self.put(self.spec())
        c, env = self.st("gate", "feat-a", "architecture")
        self.assertEqual(c, 0, env)
        self.assertEqual((env["result"]["mode"], env["result"]["closes_gate"]), ("granular", True))
        self.assertEqual(env["result"]["record_with"], "approve feat-a architecture")

    def test_merged_architecture_does_not_close_how(self):
        self.put(self.spec(), project=dict(PROJECT, gates="merged"))
        c, env = self.st("gate", "feat-a", "architecture")
        self.assertEqual((env["result"]["mode"], env["result"]["closes_gate"]), ("merged", False))
        self.assertEqual(env["result"]["pending_in_gate"], ["tasks"])
        c, env = self.st("gate", "feat-a", "tasks")
        self.assertEqual((env["result"]["closes_gate"], env["result"]["record_with"]),
                         (True, "approve-gate feat-a how"))

    def test_granular_flag_wins_over_merged(self):
        self.put(self.spec(), project=dict(PROJECT, gates="merged"))
        c, env = self.st("gate", "feat-a", "architecture", "--granular-gates")
        self.assertEqual((env["result"]["mode"], env["result"]["source"]), ("granular", "--granular-gates"))

    def test_REQ_W2_039_invalid_value_refused(self):
        self.put(self.spec(), project=dict(PROJECT, gates="fused"))
        c, env = self.st("gate", "feat-a", "architecture")
        self.assertEqual(c, 3, env)
        self.assertIn("fused", env["errors"][0]["message"])
        c, env = self.st("validate", str(self.root / "docs/spec/project.json"))
        self.assertNotEqual(c, 0, env)

    def test_40_default_from_the_registry_is_merged(self):
        from _state import state
        self.assertEqual(state.gate_mode(self.root, project={}, version="4.0.0"), ("merged", "default 4.0"))
        self.assertEqual(state.gate_mode(self.root, project={}, version="3.13.0"), ("granular", "default 3.13"))


class ProdManifest(Base):
    """@req REQ-W2-047 — approve prod --manifest: every manifest change, one marker consumed once."""

    def setUp(self):
        super().setUp()
        for cid in ("feat-a", "feat-c"):
            g.write(self.root, "docs/spec/changes/%s/spec.json" % cid, {
                "change_id": cid, "phase": "deploying", "lane": "standard",
                "phase_history": hist("init", "deploying")})
        g.write(self.root, "docs/spec/project.json", PROJECT)
        (self.root / "docs/spec/decisions.md").write_text("## D-8 — prod OK\n")
        g.commit_all(self.root, "base")
        g.with_origin(self.root)
        g.run(["checkout", "-q", "-b", "feature/feat-a"], self.root)
        for cid in ("feat-a", "feat-c"):
            g.write(self.root, "src/%s.py" % cid, "x\n")
            g.commit_all(self.root, "feat: %s\n\nKarvey-Change: %s" % (cid, cid))
        self.f = self.root / "docs/spec/changes/feat-a/spec.json"

    def approve(self):
        return self.st("approve", "feat-a", "prod", "--manifest", "--by", "owner", "--role", "human", "--ref", "D-8")

    def test_project_marker_records_both_and_is_consumed_once(self):
        ap.write_marker(self.root, "prod", "_project", "ok, merge a prod")
        c, env = self.approve()
        self.assertEqual(c, 0, env)
        self.assertEqual(env["result"]["manifest"], ["feat-a", "feat-c"])
        for cid in ("feat-a", "feat-c"):
            led, _ = ap.read_ledger(self.root, cid)
            self.assertEqual((led["prod"]["by"], led["prod"]["ref"]), ("owner", "D-8"))
        self.assertEqual(env["result"]["consumed"], ["_project"])
        m, _ = ap.read_marker(self.root, "_project")
        self.assertIsNotNone(m["consumed_at"])
        self.assertNotIn("prod", self.read().get("approvals", {}))  # D-03

    def test_marker_for_one_change_only_refused_and_nothing_written(self):
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod")
        c, env = self.approve()
        self.assertEqual(c, 3, env)
        self.assertIn("feat-c", env["errors"][0]["message"])
        self.assertIsNone(ap.read_ledger(self.root, "feat-a")[0])
        self.assertIsNone(ap.read_marker(self.root, "feat-a")[0]["consumed_at"])

    def test_a_marker_that_cannot_be_consumed_is_reported(self):
        """BUG-73 (F-62): a failed consume after the ledger writes was swallowed, so the marker stayed live
        silently; it is now a warning naming the scope, and consume is bound to the marker that approved."""
        ap.write_marker(self.root, "prod", "_project", "ok, merge a prod")
        calls = []

        def boom(root, scope, now=None, created_at=None):
            calls.append((scope, created_at))
            raise OSError("disk full")
        with mock.patch.object(ap, "consume", boom):
            c, env = self.approve()
        self.assertEqual(c, 0, env)
        self.assertEqual(env["result"]["consumed"], [])
        self.assertTrue(any("_project" in w["message"] for w in env["warnings"]), env["warnings"])
        self.assertTrue(all(ca is not None for _, ca in calls), calls)

    def test_auto_refused(self):
        c, env = self.st("approve", "feat-a", "prod", "--manifest", "--by", "a", "--role", "auto", "--ref", "D-8")
        self.assertEqual(c, 3)
        self.assertIn("never automatic", env["errors"][0]["message"])


class MergedGateAdvance(Base):
    """F-06 regression: in merged mode a phase that does not close its gate is passed once generated; the gate's
    single approval comes at its last phase (REQ-W2-034)."""

    MERGED = dict(PROJECT, gates="merged")

    def at_architecture(self, generated=True):
        return {"phase": "architecture", "skipped": {"infra": "no cloud"},
                "approvals": {"requirements": ok(), "architecture": {"generated": generated, "approved": False}},
                "phase_history": hist("init", "requirements", "architecture")}

    def test_merged_advances_inside_the_gate_without_a_second_question(self):
        self.put(self.at_architecture(), project=self.MERGED)
        c, env = self.st("next", "feat-a")
        self.assertEqual((env["result"]["next_phase"], env["result"]["blockers"]), ("tasks", []), env)
        c, env = self.st("advance", "feat-a", "tasks")
        self.assertEqual(c, 0, env)
        self.assertFalse(self.read()["approvals"]["architecture"]["approved"])  # approved by approve-gate later

    def test_merged_leaving_the_gate_needs_the_gate_approval(self):
        spec = self.at_architecture()
        spec["phase"] = "tasks"
        spec["approvals"]["tasks"] = {"generated": True, "approved": False}
        spec["phase_history"] = hist("init", "requirements", "architecture", "tasks")
        self.put(spec, project=self.MERGED)
        self.refused(("advance", "feat-a", "impl"), "architecture not approved or skipped")
        c, env = self.gate("how")
        self.assertEqual(c, 0, env)
        c, env = self.st("advance", "feat-a", "impl")
        self.assertEqual(c, 0, env)

    def test_merged_needs_the_artifact_generated(self):
        self.put(self.at_architecture(generated=False), project=self.MERGED)
        self.refused(("advance", "feat-a", "tasks"), "architecture not approved or skipped")

    def test_granular_keeps_the_per_phase_approval(self):
        self.put(self.at_architecture())
        self.refused(("advance", "feat-a", "tasks"), "architecture not approved or skipped")


class MergedGateChangesRequested(Base):
    """BUG-81 (F-12, REQ-W2-080 / REQ-W2-001): *Request changes* at a merged gate holds its phases — the generated
    artifact is not passed inside the open gate until it is generated again after the request."""

    MERGED = dict(PROJECT, gates="merged")

    def spec(self):
        return {"phase": "architecture", "skipped": {"mockup": "no UI", "design_graphic": "no UI"},
                "approvals": {"requirements": ok(),
                              "architecture": {"generated": True, "approved": False,
                                               "generated_at": "2026-09-20T10:00:00+00:00"}},
                "gate_outcomes": [{"outcome": "changes_requested", "kind": "gate", "gate": "how",
                                   "phases": ["architecture", "infra", "tasks"], "by": "owner", "role": "human",
                                   "ref": "D-2", "at": "2026-09-20T11:00:00+00:00", "reason": "cloud section"}],
                "phase_history": hist("init", "requirements", "architecture")}

    def test_next_names_the_phase_that_was_sent_back(self):
        self.put(self.spec(), project=self.MERGED)
        c, env = self.st("next", "feat-a")
        self.assertIn("architecture not approved or skipped", env["result"]["blockers"], env)
        self.refused(("advance", "feat-a", "infra"), "architecture not approved or skipped")

    def test_generated_again_after_the_request_passes(self):
        self.put(self.spec(), project=self.MERGED)
        c, env = self.st("generated", "feat-a", "architecture")
        self.assertEqual(c, 0, env)
        ap = self.read()["approvals"]["architecture"]
        self.assertEqual(ap["generated_at"], "2026-09-20T10:00:00+00:00")  # the approval wait keeps its start
        self.assertIn("regenerated_at", ap)
        c, env = self.st("next", "feat-a")
        self.assertEqual(env["result"]["blockers"], [], env)

    def test_request_on_an_earlier_generation_only(self):
        spec = self.spec()
        spec["approvals"]["architecture"]["regenerated_at"] = "2026-09-20T12:00:00+00:00"
        self.put(spec, project=self.MERGED)
        c, env = self.st("advance", "feat-a", "infra")
        self.assertEqual(c, 0, env)


if __name__ == "__main__":
    unittest.main()
