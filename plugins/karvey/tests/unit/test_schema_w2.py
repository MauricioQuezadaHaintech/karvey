"""Wave 2 schema additions (architecture §2.1, §2.2 of wave2-structural).

@req REQ-W2-019 REQ-W2-074
"""
import copy
import json
import unittest

import _path
from karvey_lib import schema_lite as sl
from _state import state

REG = sl.load_registry(_path.SCHEMAS_DIR)
SPEC = sl.Validator(REG["karvey:spec.schema.json"], REG, file="spec.json")
PROJ = sl.Validator(REG["karvey:project.schema.json"], REG, file="project.json")
T0 = "2026-09-25T10:00:00-03:00"
LANES = ["patch", "standard", "feature-ui", "ops", "hotfix", "docs"]

BASE = {"change_id": "feat-a", "phase": "requirements",
        "phase_history": [{"phase": "init", "entered_at": T0, "exited_at": T0},
                          {"phase": "requirements", "entered_at": T0}],
        "approvals": {}}
BASE_PROJECT = {"git_platform": "github", "repos": ["r"], "spec_repo": "r",
                "branch_flow": {"feature_prefix": "feature/", "integration": "main", "production": "main"}}


def spec(**over):
    s = copy.deepcopy(BASE)
    s.update(over)
    return s


def errs(out):
    return [i for i in out if i["severity"] == "error"]


class Decisions(unittest.TestCase):
    def test_REQ_W2_074_qualified_decision_valid(self):
        self.assertEqual(errs(SPEC.validate(spec(decisions=["D-12@ops", "D-3", "C-2@spec-repo"]))), [])

    def test_REQ_W2_074_malformed_decision_refused_with_pattern(self):
        out = errs(SPEC.validate(spec(decisions=["D12"])))
        self.assertEqual([i["path"] for i in out], ["$.decisions"])
        self.assertIn("D12", out[0]["message"])


class Lane(unittest.TestCase):
    def test_REQ_W2_019_every_lane_valid(self):
        for lane in LANES:
            self.assertEqual(errs(SPEC.validate(spec(lane=lane))), [], lane)

    def test_REQ_W2_019_unknown_lane_names_the_six(self):
        out = errs(SPEC.validate(spec(lane="express")))
        self.assertEqual([i["path"] for i in out], ["$.lane"])
        for lane in LANES:
            self.assertIn(lane, out[0]["message"])

    def test_lane_history_requires_reason(self):
        out = errs(SPEC.validate(spec(lane_history=[{"from": "patch", "to": "standard", "at": T0}])))
        self.assertEqual([i["path"] for i in out], ["$.lane_history[0].reason"])


class Logs(unittest.TestCase):
    def test_deploy_without_env_is_named(self):
        out = errs(SPEC.validate(spec(deploys=[{"version": "1.0.0", "at": T0, "verification": "pass"}])))
        self.assertEqual([i["path"] for i in out], ["$.deploys[0].env"])

    def test_deploy_rollback_may_be_null(self):
        d = {"env": "prod", "version": "1.0.0", "at": T0, "verification": "pass", "rollback": None}
        self.assertEqual(errs(SPEC.validate(spec(deploys=[d]))), [])

    def test_REQ_W2_029_judge_run_without_model_reported(self):
        r = {"phase": "requirements", "lens": "adversarial", "intra_model": True, "verdict": "pass", "at": T0}
        out = errs(SPEC.validate(spec(judge_runs=[r])))
        self.assertEqual([i["path"] for i in out], ["$.judge_runs[0].model"])

    def test_gate_outcome_shape(self):
        g = {"outcome": "changes_requested", "phases": ["requirements"], "by": "owner", "role": "human",
             "ref": "D-1", "at": T0, "reason": "no reason given", "kind": "gate", "gate": "phase"}
        self.assertEqual(errs(SPEC.validate(spec(gate_outcomes=[g]))), [])
        bad = dict(g, outcome="maybe")
        self.assertEqual([i["path"] for i in errs(SPEC.validate(spec(gate_outcomes=[bad])))],
                         ["$.gate_outcomes[0].outcome"])


class Roles(unittest.TestCase):
    def test_REQ_W2_040_role_auto_accepted_outside_prod(self):
        ap = {"generated": True, "approved": True, "by": "agent", "role": "auto", "date": T0, "ref": "D-1",
              "generated_at": T0}
        self.assertEqual(errs(SPEC.validate(spec(approvals={"requirements": ap}))), [])

    def test_REQ_W2_040_role_auto_refused_on_prod(self):
        prod = {"by": "agent", "role": "auto", "date": T0, "ref": "D-1"}
        out = errs(SPEC.validate(spec(approvals={"prod": prod})))
        self.assertEqual([i["path"] for i in out], ["$.approvals.prod.role"])

    def test_generated_at_must_have_zone(self):
        ap = {"generated": True, "approved": False, "generated_at": "2026-09-25"}
        out = SPEC.validate(spec(approvals={"requirements": ap}))
        self.assertEqual([i["path"] for i in errs(out)], ["$.approvals.requirements.generated_at"])


class SkippedLane(unittest.TestCase):
    def issues(self, data):
        return [i for i in state.validate_data(data, "spec", False, "spec.json") if i["severity"] == "error"]

    def test_non_skippable_phase_needs_matching_lane_reason(self):
        ok = spec(lane="patch", skipped={"requirements": "lane:patch"})
        self.assertEqual([i["code"] for i in self.issues(ok)], [])
        wrong = spec(lane="standard", skipped={"requirements": "lane:patch"})
        self.assertIn("state.skip_not_lane", [i["code"] for i in self.issues(wrong)])
        nolane = spec(skipped={"requirements": "not needed"})
        self.assertIn("state.skip_not_lane", [i["code"] for i in self.issues(nolane)])

    def test_skippable_phase_keeps_free_reason(self):
        self.assertEqual(self.issues(spec(skipped={"mockup": "no UI"})), [])


class ProjectW2(unittest.TestCase):
    def test_new_blocks_accepted(self):
        p = dict(copy.deepcopy(BASE_PROJECT), gates="merged",
                 judges={"enabled": True, "mode": "advisory", "phases": ["requirements", "qa"],
                         "per_lane": {"standard": 2}, "cross_model": "prefer"},
                 lanes={"globs": {"schema": ["**/migrations/**"]}},
                 checks={"release.manifest": "blocking", "lane.diff": "warn"},
                 tests={"globs": ["tests/**/*.py"]}, security={"tools": {}})
        p["branch_flow"]["mode"] = "trunk"
        p["enforcement"] = {"trailer_guard": "warn"}
        self.assertEqual(errs(PROJ.validate(p)), [])

    def test_bad_values_refused(self):
        cases = {"$.gates": {"gates": "some"}, "$.judges.mode": {"judges": {"mode": "loud"}},
                 "$.enforcement.trailer_guard": {"enforcement": {"trailer_guard": "on"}},
                 "$.tests.globs[0]": {"tests": {"globs": ["tests/$(x)"]}},
                 "$.judges.per_lane.patch": {"judges": {"per_lane": {"patch": -1}}}}
        for path, over in cases.items():
            p = dict(copy.deepcopy(BASE_PROJECT), **over)
            self.assertEqual([i["path"] for i in errs(PROJ.validate(p))], [path], path)

    def test_budget_is_a_warning(self):
        # wave3 §1.9 (F-62): reported by the state tool as cost.cap_key, a warning even in strict mode
        p = dict(copy.deepcopy(BASE_PROJECT), judges={"budget": 5})
        self.assertEqual(errs(PROJ.validate(p, strict=True)), [])
        out = state.validate_data(p, "project", True, "project.json")
        self.assertEqual(errs(out), [])
        self.assertTrue(any("D-30" in i["message"] for i in out))


class Subset(unittest.TestCase):
    def test_every_keyword_inside_schema_lite_subset(self):
        for sid, s in REG.items():
            self.assertEqual(sl.check_schema(s), [], sid)
            json.dumps(s)


if __name__ == "__main__":
    unittest.main()
