"""Lane-aware next / advance (architecture §1.4 of wave2-structural).

@req REQ-W2-014 REQ-W2-015 REQ-W2-016 REQ-W2-018 REQ-W2-019 REQ-W2-021
"""
import json
import os
import unittest
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from _state import make_project, run_json, state
from karvey_lib import approval as ap

g.isolate_git()
T0 = "2026-09-25T10:00:00-03:00"


def ok():
    return {"generated": True, "approved": True, "by": "owner", "role": "human", "date": T0, "ref": "D-1"}


def at_requirements(lane=None, approved=True):
    s = {"change_id": "feat-a", "phase": "requirements",
         "phase_history": [{"phase": "init", "entered_at": T0, "exited_at": T0},
                           {"phase": "requirements", "entered_at": T0}],
         "approvals": {"requirements": ok() if approved else {"generated": True, "approved": False}}}
    if lane:
        s["lane"] = lane
    return s


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path

    def tearDown(self):
        self.t.cleanup()

    def put(self, data):
        self.f = make_project(self.root, spec=data)

    def st(self, *argv):
        return run_json(*(list(argv) + ["--root", str(self.root)]))

    def read(self):
        return json.loads(self.f.read_text(encoding="utf-8"))


class Standard(Base):
    def test_REQ_W2_015_standard_passes_mockup_and_design(self):
        self.put(at_requirements("standard"))
        code, env = self.st("next", "feat-a")
        self.assertEqual(code, 0, env)
        r = env["result"]
        self.assertEqual((r["next_phase"], r["status"], r["lane"]), ("architecture", "ready", "standard"))
        self.assertEqual(r["blockers"], [])
        code, env = self.st("advance", "feat-a", "architecture")
        self.assertEqual(code, 0, env)
        data = self.read()
        self.assertEqual(data["skipped"], {"mockup": "lane:standard", "design_graphic": "lane:standard"})
        self.assertEqual(env["result"]["lane_skipped"], ["mockup", "design_graphic"])
        self.assertEqual(state.validate_data(data, "spec", True, "spec.json"), [])

    def test_REQ_W2_021_manual_skip_is_kept(self):
        s = at_requirements("standard")
        s["skipped"] = {"mockup": "no UI at all"}
        self.put(s)
        self.st("advance", "feat-a", "architecture")
        self.assertEqual(self.read()["skipped"]["mockup"], "no UI at all")


class FeatureUi(Base):
    def test_REQ_W2_015_feature_ui_without_mockup_refused(self):
        self.put(at_requirements("feature-ui"))
        before = self.f.read_bytes()
        code, env = self.st("advance", "feat-a", "architecture")
        self.assertEqual(code, 3)
        self.assertIn("mockup", env["errors"][0]["message"])
        self.assertEqual(self.f.read_bytes(), before)
        code, env = self.st("next", "feat-a")
        self.assertEqual(env["result"]["next_phase"], "mockup")


class Patch(Base):
    def test_patch_goes_from_init_to_impl(self):
        s = {"change_id": "feat-a", "phase": "init", "lane": "patch", "approvals": {},
             "phase_history": [{"phase": "init", "entered_at": T0}]}
        self.put(s)
        code, env = self.st("next", "feat-a")
        self.assertEqual(env["result"]["next_phase"], "impl")
        code, env = self.st("advance", "feat-a", "impl")
        self.assertEqual(code, 0, env)
        self.assertEqual(sorted(self.read()["skipped"]),
                         sorted(["requirements", "mockup", "design_graphic", "architecture", "infra", "tasks"]))


class Validation(Base):
    def errs(self, data):
        return [(i["code"], i["path"]) for i in state.validate_data(data, "spec", False, "spec.json")
                if i["severity"] == "error"]

    def test_REQ_W2_015_lane_reason_not_matching_lane_is_an_error(self):
        s = at_requirements("feature-ui")
        s["skipped"] = {"mockup": "lane:standard"}
        self.assertIn(("state.skip_not_lane", "$.skipped.mockup"), self.errs(s))

    def test_lane_reason_for_a_phase_the_lane_runs_is_an_error(self):
        s = at_requirements("standard")
        s["skipped"] = {"architecture": "lane:standard"}
        self.assertIn(("state.skip_not_lane", "$.skipped.architecture"), self.errs(s))


class NoLane(Base):
    def test_REQ_W2_019_no_lane_keeps_312_and_warns_once(self):
        self.put(at_requirements())
        code, env = self.st("next", "feat-a")
        self.assertEqual(code, 0)
        self.assertEqual(env["result"]["next_phase"], "mockup")
        self.assertEqual([w["code"] for w in env["warnings"]].count("state.lane_missing"), 1)
        self.assertEqual(env["result"]["lane"], "legacy")

    def test_no_warning_with_a_lane(self):
        self.put(at_requirements("standard"))
        code, env = self.st("next", "feat-a")
        self.assertNotIn("state.lane_missing", [w["code"] for w in env["warnings"]])


PATCH_SKIPS = ("requirements", "mockup", "design_graphic", "architecture", "infra", "tasks")


def patch_at_impl(lane="patch", **over):
    s = {"change_id": "feat-a", "phase": "impl", "lane": lane, "approvals": {},
         "skipped": {p: "lane:%s" % lane for p in PATCH_SKIPS},
         "phase_history": [{"phase": "init", "entered_at": T0, "exited_at": T0}, {"phase": "impl", "entered_at": T0}]}
    s.update(over)
    return s


class GitBase(Base):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        self.envp = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg"), ap.COMPAT_ENV: ""})
        self.envp.start()

    def tearDown(self):
        self.envp.stop()
        self.t.cleanup()

    def refused(self, argv, needle):
        before = self.f.read_bytes()
        code, env = self.st(*argv)
        self.assertEqual(code, 3, env)
        self.assertIn(needle, env["errors"][0]["message"])
        self.assertEqual(self.f.read_bytes(), before)
        return env


class LaneChanges(GitBase):
    def test_REQ_W2_016_raise_patch_to_standard_reopens_requirements(self):
        self.put(patch_at_impl())
        code, env = self.st("lane", "feat-a", "raise", "standard", "--reason", "needs an API contract change",
                            "--by", "agent")
        self.assertEqual(code, 0, env)
        data = self.read()
        self.assertEqual(data["lane"], "standard")
        self.assertEqual(data["phase"], "requirements")
        self.assertEqual(data["lane_history"][0]["from"], "patch")
        self.assertEqual(data["lane_history"][0]["to"], "standard")
        self.assertEqual(data["skipped"], {"mockup": "lane:standard", "design_graphic": "lane:standard"})
        self.assertEqual(env["result"]["pending"], ["requirements", "architecture", "infra", "tasks"])
        self.assertEqual(state.validate_data(data, "spec", False, "spec.json"), [])

    def test_REQ_W2_016_manual_skips_survive_a_raise(self):
        s = patch_at_impl()
        s["skipped"]["infra"] = "no cloud"
        self.put(s)
        self.st("lane", "feat-a", "raise", "standard", "--reason", "grew")
        self.assertEqual(self.read()["skipped"]["infra"], "no cloud")

    def test_REQ_W2_016_lower_without_marker_refused(self):
        self.put(dict(at_requirements("standard")))
        self.refused(("lane", "feat-a", "lower", "patch", "--reason", "small", "--by", "owner", "--role", "human",
                      "--ref", "D-1"), "approval marker")
        self.refused(("lane", "feat-a", "lower", "patch", "--reason", "small"), "missing: --by")
        self.refused(("lane", "feat-a", "raise", "patch", "--reason", "small"), "not a raise")

    def test_REQ_W2_016_lower_with_human_marker(self):
        self.put(dict(at_requirements("standard")))
        ap.write_marker(self.root, "plan", "feat-a", "aprobado, bájalo a patch")
        code, env = self.st("lane", "feat-a", "lower", "patch", "--reason", "one-line fix", "--by", "owner",
                            "--role", "human", "--ref", "D-1")
        self.assertEqual(code, 0, env)
        self.assertEqual(self.read()["lane_history"][-1]["ref"], "D-1")

    def test_unknown_lane_lists_valid(self):
        self.put(dict(at_requirements("standard")))
        self.refused(("lane", "feat-a", "raise", "express", "--reason", "x"), "feature-ui")


class LaneSet(GitBase):
    def init_spec(self):
        return {"change_id": "feat-a", "phase": "init", "approvals": {},
                "phase_history": [{"phase": "init", "entered_at": T0}]}

    def answers(self, **over):
        a = {"touches_ui": False, "schema": False, "api_contract": False, "permissions_or_trust": False,
             "tier": 2, "code_files": 2}
        a.update(over)
        p = self.t.path / "answers.json"
        p.write_text(json.dumps(a))
        return str(p)

    def test_REQ_W2_013_set_patch_admitted(self):
        self.put(self.init_spec())
        code, env = self.st("lane", "feat-a", "set", "patch", "--answers", self.answers())
        self.assertEqual(code, 0, env)
        self.assertEqual(self.read()["lane"], "patch")

    def test_REQ_W2_013_set_patch_with_schema_refused(self):
        self.put(self.init_spec())
        env = self.refused(("lane", "feat-a", "set", "patch", "--answers", self.answers(schema=True)),
                           "patch: schema change — use standard")
        self.assertEqual(env["result"]["proposed"], "standard")

    def test_set_only_at_init(self):
        self.put(at_requirements())
        self.refused(("lane", "feat-a", "set", "standard"), "only for a change in init")


class Hotfix(GitBase):
    def hotfix(self, **ev):
        s = {"change_id": "feat-a", "phase": "init", "lane": "hotfix", "approvals": {},
             "phase_history": [{"phase": "init", "entered_at": T0}]}
        if ev:
            s["lane_evidence"] = ev
        return s

    def test_REQ_W2_018_hotfix_with_evidence_starts_impl_without_tasks(self):
        self.put(self.hotfix())
        code, env = self.st("lane-evidence", "feat-a", "--bug", "BUG-7", "--finding", "F-2",
                            "--regression-test", "tests/test_x.py::test_bug_7")
        self.assertEqual(code, 0, env)
        code, env = self.st("advance", "feat-a", "impl")
        self.assertEqual(code, 0, env)
        self.assertNotIn("tasks", self.read()["approvals"])

    def test_REQ_W2_018_hotfix_without_evidence_refused_naming_both(self):
        self.put(self.hotfix())
        env = self.refused(("advance", "feat-a", "impl"), "BUG-NN")
        self.assertIn("regression test", env["errors"][0]["message"])
        code, env = self.st("next", "feat-a")
        self.assertTrue(any("BUG-NN" in b for b in env["result"]["blockers"]))

    def test_REQ_W2_018_hotfix_qa_is_optional(self):
        s = self.hotfix(bug_id="BUG-7", regression_test="t.py::t")
        s["phase"] = "qa"
        s["skipped"] = {p: "lane:hotfix" for p in PATCH_SKIPS}
        s["phase_history"] = [{"phase": "init", "entered_at": T0, "exited_at": T0},
                              {"phase": "impl", "entered_at": T0, "exited_at": T0},
                              {"phase": "test", "entered_at": T0, "exited_at": T0}, {"phase": "qa", "entered_at": T0}]
        self.put(s)
        code, env = self.st("skip", "feat-a", "qa", "--reason", "no full QA review (hotfix)")
        self.assertEqual(code, 0, env)
        code, env = self.st("advance", "feat-a", "deploying")
        self.assertEqual(code, 0, env)

    def test_REQ_W2_014_lane_evidence_only_for_patch_and_hotfix(self):
        self.put(dict(at_requirements("standard")))
        self.refused(("lane-evidence", "feat-a", "--bug", "BUG-1"), "patch and hotfix")

    def test_qa_not_skippable_in_standard(self):
        s = dict(at_requirements("standard"))
        self.put(s)
        self.refused(("skip", "feat-a", "qa", "--reason", "x"), "not skippable")


if __name__ == "__main__":
    unittest.main()
