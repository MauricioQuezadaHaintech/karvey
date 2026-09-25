"""Lanes as data (architecture §1.3 of wave2-structural).

@req REQ-W2-011 REQ-W2-019 REQ-W2-031
"""
import copy
import json
import unittest

import _path
from karvey_lib import lanes as L

SM = json.loads((_path.SCHEMAS_DIR / "state-machine.json").read_text(encoding="utf-8"))
PHASES = [p["id"] for p in SM["phases"]]
APPROVABLE = [p["id"] for p in SM["phases"] if p["approval"]]


class Table(unittest.TestCase):
    def test_REQ_W2_011_six_lanes(self):
        self.assertEqual(sorted(L.names()), sorted(["patch", "standard", "feature-ui", "ops", "hotfix", "docs"]))

    def test_REQ_W2_011_every_lane_lists_every_phase(self):
        for lane in L.names():
            rules = L.lane_def(lane)["phases"]
            for p in PHASES:
                self.assertIn(rules.get(p), ("m", "o", "s"), (lane, p))
            for p in APPROVABLE:
                self.assertIn(p, rules, (lane, p))

    def test_init_never_skipped(self):
        for lane in L.names():
            self.assertEqual(L.phase_rule(lane, "init"), "m", lane)
            self.assertEqual(L.phase_rule(lane, "archived"), "m", lane)

    def test_table_rows_match_architecture(self):
        self.assertEqual(L.phase_rule("standard", "mockup"), "s")
        self.assertEqual(L.phase_rule("standard", "infra"), "o")
        self.assertEqual(L.phase_rule("feature-ui", "mockup"), "m")
        self.assertEqual(L.phase_rule("patch", "requirements"), "s")
        self.assertEqual(L.phase_rule("ops", "infra"), "m")
        self.assertEqual(L.phase_rule("ops", "qa"), "o")
        self.assertEqual(L.gates_of("ops"), ["what+how", "release"])
        self.assertEqual(L.gates_of("patch"), ["prod"])
        self.assertEqual(L.lane_def("patch")["criteria"]["max_code_files"], 3)

    def test_semantic_checks_refuse_a_bad_table(self):
        t = L.load()
        bad = copy.deepcopy(t)
        del bad["lanes"]["standard"]["phases"]["qa"]
        with self.assertRaises(L.LaneError) as cm:
            L.load(bad)
        self.assertIn("standard does not list qa", str(cm.exception))
        bad = copy.deepcopy(t)
        bad["lanes"]["docs"]["phases"]["init"] = "s"
        with self.assertRaises(L.LaneError):
            L.load(bad)
        bad = copy.deepcopy(t)
        bad["lanes"]["docs"]["phases"]["qa"] = "x"
        with self.assertRaises(L.LaneError):
            L.load(bad)


class LaneOf(unittest.TestCase):
    def test_REQ_W2_019_fallbacks(self):
        self.assertEqual(L.lane_of({"lane": "patch", "type": "ops"}), ("patch", "spec"))
        self.assertEqual(L.lane_of({"type": "ops"}), ("ops", "type"))
        self.assertEqual(L.lane_of({"type": "hotfix"}), ("hotfix", "type"))
        self.assertEqual(L.lane_of({}), ("legacy", "legacy"))

    def test_REQ_W2_019_legacy_is_the_312_pipeline(self):
        for p in PHASES:
            self.assertEqual(L.phase_rule("legacy", p), "m")
        self.assertFalse(L.lane_skips("legacy", "mockup"))

    def test_unknown_lane(self):
        with self.assertRaises(L.LaneError) as cm:
            L.phase_rule("express", "qa")
        self.assertIn("feature-ui", str(cm.exception))


class Judges(unittest.TestCase):
    def test_REQ_W2_031_default_counts(self):
        self.assertEqual(L.judges_for("patch"), 0)
        self.assertEqual(L.judges_for("standard"), 2)
        self.assertEqual(L.judges_for("feature-ui"), 3)

    def test_REQ_W2_031_override(self):
        self.assertEqual(L.judges_for("patch", {"judges": {"per_lane": {"patch": 1}}}), 1)
        with self.assertRaises(L.LaneError):
            L.judges_for("standard", {"judges": {"per_lane": {"standard": -1}}})


class Globs(unittest.TestCase):
    def test_matches_top_level_and_nested(self):
        g = L.globs()
        self.assertTrue(L.matches("db/migrations/001_add.sql", g["schema"]))
        self.assertTrue(L.matches("openapi.yaml", g["api_contract"]))
        self.assertTrue(L.matches("src/app.py", g["code"]))
        self.assertFalse(L.matches("README.md", g["code"]))

    def test_project_extends(self):
        g = L.globs({"lanes": {"globs": {"schema": ["**/*.avsc"]}}})
        self.assertIn("**/*.avsc", g["schema"])


if __name__ == "__main__":
    unittest.main()
