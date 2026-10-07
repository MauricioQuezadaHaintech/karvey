import copy
import json
import unittest

import _path
from karvey_lib import schema_lite as sl

REG = sl.load_registry(_path.SCHEMAS_DIR)
SPEC = sl.Validator(REG["karvey:spec.schema.json"], REG, file="spec.json")
PROJ = sl.Validator(REG["karvey:project.schema.json"], REG, file="project.json")


def errs(out):
    return [i for i in out if i["severity"] == "error"]


def paths(out):
    return [i["path"] for i in errs(out)]


BASE_PROJECT = {"git_platform": "github", "repos": ["karvey"], "spec_repo": "karvey",
                "branch_flow": {"feature_prefix": "feature/", "integration": "main", "production": "main"}}


def project(**over):
    p = copy.deepcopy(BASE_PROJECT)
    p.update(over)
    return p


class Loaded(unittest.TestCase):
    def test_both_schemas_in_registry_and_in_subset(self):
        self.assertEqual(set(REG), {"karvey:spec.schema.json", "karvey:project.schema.json",
                                    "karvey:upgrade-steps.schema.json"})
        for s in REG.values():
            self.assertEqual(sl.check_schema(s), [])
            self.assertEqual(s["x-karvey-schema-version"], 1)


class ProjectSchema(unittest.TestCase):
    def test_this_repo_project_json_validates(self):
        with open(_path.REPO_ROOT / "docs/spec/project.json", encoding="utf-8-sig") as fh:
            data = json.load(fh)
        self.assertEqual(errs(PROJ.validate(data)), [])
        self.assertEqual(errs(PROJ.validate(data, strict=True)), [])

    def test_required_top_level(self):
        out = PROJ.validate({})
        self.assertEqual(sorted(paths(out)), ["$.branch_flow", "$.git_platform", "$.repos", "$.spec_repo"])

    def test_prod_gate_hook_must_be_boolean(self):
        out = PROJ.validate(project(enforcement={"prod_gate_hook": "no"}))
        self.assertEqual(paths(out), ["$.enforcement.prod_gate_hook"])
        self.assertEqual(errs(PROJ.validate(project(enforcement={"prod_gate_hook": False}))), [])

    def test_accepted_shapes(self):
        cases = [
            project(knowledge_sync="none"),
            project(notifications={"channel": "google-chat", "target": "spaces/AAAA", "detail": "counts"}),
            project(notifications={"channel": "slack", "detail": "full", "deferred": True}),
            project(management={"tool": "clickup", "location": "901234", "sprints": "901235"}),
            project(management={"tool": "jira", "statuses": {"todo": "To Do", "in_progress": None,
                                                             "review": "In Review", "done": "Done",
                                                             "blocked": None}}),
            project(management={"tool": "clickup", "statuses": {"by_level": {
                "epic": {"todo": "backlog", "done": "closed"}, "task": {"todo": "to do", "blocked": None}}}}),
            project(management={"tool": "clickup", "statuses": {"by_list": {"901": {"todo": "open"}}}}),
            project(stall_days=7, wip_limit=3, calibration={"threshold_pct": 30, "window": 3},
                    schema_mode="strict", karvey_version="3.12.0"),
            project(enforcement={"plan_marker_ttl_min": 120, "approval_vocabulary": {"approve": ["dale"]}}),
        ]
        for c in cases:
            self.assertEqual(errs(PROJ.validate(c)), [], json.dumps(c))

    def test_rejected_shapes(self):
        cases = {
            "$.knowledge_sync": project(knowledge_sync="notion"),
            "$.notifications.detail": project(notifications={"detail": "verbose"}),
            "$.stall_days": project(stall_days=0),
            "$.wip_limit": project(wip_limit=0),
            "$.enforcement.plan_marker_ttl_min": project(enforcement={"plan_marker_ttl_min": 2000}),
            "$.branch_flow.production": project(branch_flow={"integration": "dev", "production": "-x"}),
            "$.branch_flow.feature_prefix": project(branch_flow={"feature_prefix": "feature",
                                                                 "integration": "dev", "production": "main"}),
            "$.management": project(management={"tool": "clickup", "statuses": {"todo": 5}}),
            "$.git_platform": project(git_platform="bitbucket"),
        }
        for want, c in cases.items():
            got = paths(PROJ.validate(c))
            self.assertIn(want, got, want)

    def test_legacy_management_string_is_a_warning(self):
        out = PROJ.validate(project(management="markdown"))
        self.assertEqual(errs(out), [])
        self.assertEqual([(i["severity"], i["code"]) for i in out], [("warning", "schema.legacy")])
        self.assertTrue(errs(PROJ.validate(project(management=42))))

    def test_legacy_clickup_block_and_google_chat_alias(self):
        out = PROJ.validate(project(clickup={"backlog_list_id": "9"}, notifications={"channel": "google_chat"}))
        self.assertEqual(errs(out), [])
        self.assertEqual([i["path"] for i in out], ["$.clickup"])

    def test_safe_kinds_named(self):
        kinds = set()

        def walk(n):
            if isinstance(n, dict):
                if "x-karvey-safe" in n:
                    kinds.add(n["x-karvey-safe"])
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(REG["karvey:project.schema.json"])
        self.assertEqual(kinds, {"notifications.target", "management.location", "management.sprints", "status"})


SPEC_OK = {
    "change_id": "wave1-hardening", "phase": "impl", "schema_version": 1, "lane": "standard",
    "seed_backlog_id": ["BL-04", "BL-05"],
    "skipped": {"mockup": "no UI", "infra": "no cloud"},
    "phase_history": [{"phase": "init", "entered_at": "2026-09-23T10:00:00-03:00",
                       "exited_at": "2026-09-23T11:00:00-03:00"},
                      {"phase": "requirements", "entered_at": "2026-09-23T11:00:00-03:00"}],
    "approvals": {
        "requirements": {"generated": True, "approved": True, "by": "Mauricio Quezada Ibáñez", "role": "human",
                         "date": "2026-09-23T12:00:00-03:00", "ref": "D-05"},
        "prod": {},
    },
    "management": "markdown",
    "decisions": ["D-01", "C-02"],
    "created_at": "2026-09-23T10:00:00-03:00",
}


def spec(**over):
    s = copy.deepcopy(SPEC_OK)
    for k, v in over.items():
        if v is None:
            s.pop(k, None)
        else:
            s[k] = v
    return s


class SpecSchema(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(SPEC.validate(spec()), [])
        self.assertEqual(errs(SPEC.validate(spec(seed_backlog_id="BL-04"))), [])

    def test_phase_enum(self):
        self.assertEqual(paths(SPEC.validate(spec(phase="qa-approved"))), ["$.phase"])  # REQ-W1-028 shape
        for ph in ("init", "requirements", "mockup", "design_graphic", "architecture", "infra", "tasks",
                   "impl", "test", "qa", "deploying", "deployed", "archived"):
            self.assertEqual(errs(SPEC.validate(spec(phase=ph))), [], ph)

    def test_capability_is_declared(self):  # C2: living-specs.md documents it; spec-merge reads it
        self.assertIn("capability", REG["karvey:spec.schema.json"]["properties"])
        for ok in ("method", "demo", "team.adapters", "a_b-1"):
            self.assertEqual(errs(SPEC.validate(spec(capability=ok))), [], ok)
        for bad in ("Method", "-x", "a/b", "", 3):
            self.assertEqual(paths(SPEC.validate(spec(capability=bad))), ["$.capability"], bad)

    def test_required_and_change_id(self):
        self.assertEqual(sorted(paths(SPEC.validate({}))), ["$.change_id", "$.phase"])
        self.assertEqual(paths(SPEC.validate(spec(change_id="Bad_ID"))), ["$.change_id"])

    def test_prod_by_with_prose_ref_is_an_error(self):
        # H-22: team-adapters prod.ref = "session approval: …"
        bad = spec(approvals={"prod": {"by": "Mauricio Quezada Ibáñez", "role": "human",
                                       "date": "2026-09-22T18:00:00-03:00",
                                       "ref": "session approval: commit, push, merge"}})
        self.assertEqual(paths(SPEC.validate(bad)), ["$.approvals.prod.ref"])
        self.assertEqual(paths(SPEC.validate(bad, strict=False)), ["$.approvals.prod.ref"])  # error even advisory

    def test_prod_by_without_ref_is_an_error(self):
        bad = spec(approvals={"prod": {"by": "X", "role": "human", "date": "2026-09-22T18:00:00-03:00"}})
        self.assertEqual(paths(SPEC.validate(bad)), ["$.approvals.prod.ref"])
        empty = spec(approvals={"prod": {"by": "X", "role": "human", "date": "2026-09-22T18:00:00-03:00", "ref": ""}})
        self.assertIn("$.approvals.prod.ref", paths(SPEC.validate(empty)))

    def test_prod_never_delegated(self):
        bad = spec(approvals={"prod": {"by": "X", "role": "ceo-delegate", "date": "2026-09-22T18:00:00-03:00",
                                       "ref": "D-08"}})
        self.assertEqual(paths(SPEC.validate(bad)), ["$.approvals.prod.role"])
        ok = spec(approvals={"prod": {"by": "X", "role": "human", "date": "2026-09-22T18:00:00-03:00",
                                      "ref": "https://github.com/o/r/pull/19"}})
        self.assertEqual(errs(SPEC.validate(ok)), [])

    def test_legacy_approval_without_by_is_a_warning_strict_error(self):
        leg = spec(approvals={"tasks": {"approved": True}})
        out = SPEC.validate(leg)
        self.assertEqual(errs(out), [])
        self.assertEqual(sorted(i["path"] for i in out),
                         ["$.approvals.tasks.by", "$.approvals.tasks.date", "$.approvals.tasks.ref",
                          "$.approvals.tasks.role"])
        self.assertEqual(len(errs(SPEC.validate(leg, strict=True))), 4)

    def test_unknown_approval_key_and_gates_skipped_warn(self):
        out = SPEC.validate(spec(approvals={"impl": {"approved": True}},
                                 gates_skipped={"phases": ["qa"], "reason": "x"}))
        self.assertEqual(errs(out), [])
        self.assertEqual(sorted(i["path"] for i in out), ["$.approvals.impl", "$.gates_skipped"])

    def test_skipped_only_skippable_and_with_reason(self):
        self.assertEqual(paths(SPEC.validate(spec(skipped={"tasks": "x"}))), ["$.skipped.tasks"])
        self.assertEqual(paths(SPEC.validate(spec(skipped={"infra": ""}))), ["$.skipped.infra"])

    def test_history_entry_shape(self):
        bad = spec(phase_history=[{"from": "tasks", "to": "impl", "at": "2026-09-24"}])
        self.assertEqual(sorted(paths(SPEC.validate(bad))),
                         ["$.phase_history[0].entered_at", "$.phase_history[0].phase"])
        tz = spec(phase_history=[{"phase": "init", "entered_at": "2026-09-23 10:00"}])
        self.assertEqual(paths(SPEC.validate(tz)), ["$.phase_history[0].entered_at"])

    def test_management_override_uses_project_statuses(self):
        ok = spec(management={"tool": "clickup", "location": "9", "statuses": {"todo": "open", "blocked": None}})
        self.assertEqual(errs(SPEC.validate(ok)), [])
        bad = spec(management={"tool": "clickup", "statuses": {"todo": 1}})
        self.assertTrue(errs(SPEC.validate(bad)))
        self.assertTrue(errs(SPEC.validate(spec(management="trello"))))

    def test_created_at_without_zone_is_a_warning(self):
        out = SPEC.validate(spec(created_at="2026-09-23"))
        self.assertEqual([(i["severity"], i["path"]) for i in out], [("warning", "$.created_at")])

    def test_legacy_date_only_approval_is_a_warning(self):
        # F-06 / REQ-W1-003: every spec.json of this repo carries "date": "2026-09-22"-style approvals.
        s = spec(approvals={"tasks": {"approved": True, "by": "X", "role": "human", "date": "2026-09-24",
                                      "ref": "D-13"}})
        out = SPEC.validate(s)
        self.assertEqual(errs(out), [])
        self.assertEqual([(i["severity"], i["code"], i["path"]) for i in out],
                         [("warning", "schema.format", "$.approvals.tasks.date")])
        self.assertEqual(paths(SPEC.validate(s, strict=True)), ["$.approvals.tasks.date"])

    def test_prod_date_only_stays_an_error(self):
        # F-06: prodApproval is the non-delegable record and keeps a strict datetime-tz, even in advisory mode.
        s = spec(approvals={"prod": {"by": "X", "role": "human", "date": "2026-09-24", "ref": "D-08"}})
        self.assertEqual(paths(SPEC.validate(s)), ["$.approvals.prod.date"])

    def test_evidence_excerpt_bounded(self):
        s = spec(approvals={"tasks": {"approved": True, "by": "X", "role": "human",
                                      "date": "2026-09-23T12:00:00-03:00", "ref": "D-13",
                                      "evidence": {"marker": "approvals/x.json", "prompt_excerpt": "a" * 81}}})
        self.assertEqual(paths(SPEC.validate(s)), ["$.approvals.tasks.evidence.prompt_excerpt"])

    def test_additional_top_level_keys_allowed(self):
        self.assertEqual(SPEC.validate(spec(fases=["x"], tenant="t", notes="n")), [])


if __name__ == "__main__":
    unittest.main()
