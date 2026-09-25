import json
import unittest

import _path


def load(name):
    with open(_path.SCHEMAS_DIR / name, encoding="utf-8-sig") as fh:
        return json.load(fh)


SM = load("state-machine.json")
LM = load("legacy-phase-map.json")
SPEC = load("spec.schema.json")
ENUM = SPEC["$defs"]["phase"]["enum"]
PHASES = [p["id"] for p in SM["phases"]]


class StateMachine(unittest.TestCase):
    def test_phase_ids_equal_spec_enum_in_order(self):
        self.assertEqual(PHASES, ENUM)

    def test_skippable(self):
        self.assertEqual({p["id"] for p in SM["phases"] if p["skippable"]}, {"mockup", "design_graphic", "infra"})
        # wave2 §2.1: skipped names every approvable phase before deploy (lane skips); the manual skip
        # stays limited to the skippable three (semantic check state.skip_not_lane)
        self.assertEqual(set(SPEC["properties"]["skipped"]["propertyNames"]["enum"]),
                         {p["id"] for p in SM["phases"] if p["approval"] and p["approval"] not in ("deploy", "prod")})

    def test_reopen_targets(self):
        self.assertEqual(SM["reopen_targets"], ["requirements", "architecture", "tasks", "impl"])
        self.assertTrue(set(SM["reopen_targets"]) <= set(ENUM))

    def test_approval_keys_exist_in_spec_schema(self):
        keys = set(SPEC["properties"]["approvals"]["properties"])
        approvals = [p["approval"] for p in SM["phases"] if p["approval"] is not None]
        self.assertEqual(len(approvals), len(set(approvals)))
        self.assertTrue(set(approvals) <= keys, set(approvals) - keys)
        self.assertEqual(set(approvals), keys)

    def test_skills_exist(self):
        for p in SM["phases"]:
            self.assertTrue((_path.PLUGIN_ROOT / "skills" / p["skill"] / "SKILL.md").is_file(), p["skill"])

    def test_every_phase_has_the_fields(self):
        for p in SM["phases"]:
            self.assertTrue({"id", "approval", "skippable", "skill"} <= set(p), p["id"])
            for k in ("produces", "reads"):
                self.assertIsInstance(p.get(k, []), list)

    def test_optional_read_marker(self):
        arch = next(p for p in SM["phases"] if p["id"] == "architecture")
        self.assertIn("design-spec.md?", arch["reads"])

    def test_preconditions_present(self):
        self.assertEqual(set(SM["preconditions"]), {"enter(P)", "enter(deployed)", "enter(archived)"})


class LegacyMap(unittest.TestCase):
    def test_every_target_is_in_the_enum(self):
        for tier in ("exact", "proposed"):
            for legacy, target in LM["tiers"][tier].items():
                self.assertIn(target, ENUM, "%s:%s" % (tier, legacy))

    def test_tiers_disjoint_and_not_enum_values(self):
        exact, proposed = set(LM["tiers"]["exact"]), set(LM["tiers"]["proposed"])
        self.assertFalse(exact & proposed)
        self.assertFalse((exact | proposed) & set(ENUM))

    def test_req_w1_009_list_is_exact(self):
        req = ["requirements-generated", "mockup-generated", "design-graphic-approved", "architecture-generated",
               "architecture-approved", "infra-generated", "infra-approved", "tasks-generated", "tasks-approved",
               "deploy"]
        self.assertEqual(sorted(LM["tiers"]["exact"]), sorted(req))
        self.assertEqual(LM["tiers"]["exact"]["deploy"], "deploying")  # conservative
        self.assertEqual(LM["tiers"]["exact"]["tasks-generated"], "tasks")

    def test_proposed_tier_d09(self):
        p = LM["tiers"]["proposed"]
        self.assertEqual(len(p), 14)
        self.assertEqual(p["deployed-prod"], "deployed")
        self.assertEqual(p["implemented-pending-test"], "test")
        self.assertEqual(LM["applied_by"]["proposed"], "--fix --accept-proposed")

    def test_iterate_and_null_unmappable(self):
        self.assertEqual(LM["unmappable"]["values"], ["iterate"])
        self.assertIs(LM["unmappable"]["missing_or_null"], True)
        for tier in ("exact", "proposed"):
            self.assertNotIn("iterate", LM["tiers"][tier])
            self.assertNotIn("null", LM["tiers"][tier])
            self.assertNotIn("", LM["tiers"][tier])


if __name__ == "__main__":
    unittest.main()
