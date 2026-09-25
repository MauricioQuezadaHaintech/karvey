"""Lane-aware next / advance (architecture §1.4 of wave2-structural).

@req REQ-W2-015 REQ-W2-019 REQ-W2-021
"""
import json
import unittest

import _path  # noqa: F401
import _gitrepo as g
from _state import make_project, run_json, state

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


if __name__ == "__main__":
    unittest.main()
