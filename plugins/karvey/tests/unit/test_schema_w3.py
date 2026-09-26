"""Wave 3 schema additions (architecture §2.1, §2.2 of wave3-optimization).

@req REQ-W3-014 REQ-W3-016 REQ-W3-062
"""
import copy
import unittest

import _path
from karvey_lib import schema_lite as sl

REG = sl.load_registry(_path.SCHEMAS_DIR)
SPEC = sl.Validator(REG["karvey:spec.schema.json"], REG, file="spec.json")
T0 = "2026-09-26T10:00:00-03:00"
BASE = {"change_id": "feat-a", "phase": "requirements", "lane": "standard", "skipped": {},
        "phase_history": [{"phase": "init", "entered_at": T0, "exited_at": T0},
                          {"phase": "requirements", "entered_at": T0}],
        "approvals": {}}
EFFORT = {"kind": "phase", "phase": "requirements", "at": T0, "session": "0123456789abcdef",
          "usd": {"value": 1.25, "quality": "exact", "source": "runtime statusline"},
          "tokens": {"in": 1000, "out": 200, "cache": 5000, "total": 6200, "quality": "exact",
                     "source": "session transcript"},
          "review_min": {"value": None, "quality": "n/a", "reason": "not stated at the gate"}}


def spec(**over):
    s = copy.deepcopy(BASE)
    s.update(over)
    return s


def errs(out):
    return [i for i in out if i["severity"] == "error"]


class Effort(unittest.TestCase):
    def test_REQ_W3_014_valid_entry_passes(self):
        self.assertEqual(errs(SPEC.validate(spec(effort=[EFFORT]), strict=True)), [])

    def test_REQ_W3_014_quality_outside_the_three_fails(self):
        bad = copy.deepcopy(EFFORT)
        bad["usd"]["quality"] = "guessed"
        out = errs(SPEC.validate(spec(effort=[bad])))
        self.assertEqual([i["path"] for i in out], ["$.effort[0].usd.quality"])

    def test_effort_at_needs_an_offset(self):
        bad = copy.deepcopy(EFFORT)
        bad["at"] = "2026-09-26"
        self.assertTrue(errs(SPEC.validate(spec(effort=[bad]))))


class JudgeRuns(unittest.TestCase):
    RUN = {"phase": "architecture", "lens": "security", "model": "model-a", "intra_model": True,
           "verdict": "pass", "at": T0}

    def test_REQ_W3_016_tokens_total_and_source(self):
        run = dict(self.RUN, tokens_total=12000, usd_estimated=True, source="runtime")
        self.assertEqual(errs(SPEC.validate(spec(judge_runs=[run]))), [])

    def test_unknown_source_fails(self):
        run = dict(self.RUN, source="guess")
        out = errs(SPEC.validate(spec(judge_runs=[run])))
        self.assertEqual([i["path"] for i in out], ["$.judge_runs[0].source"])


class Compatibility(unittest.TestCase):
    def test_REQ_W3_062_a_40_spec_without_the_fields_passes_strict(self):
        self.assertEqual(errs(SPEC.validate(spec(), strict=True)), [])

    def test_every_keyword_is_in_the_schema_lite_subset(self):
        # load_registry raises SchemaError on any keyword outside the subset
        self.assertIn("karvey:spec.schema.json", sl.load_registry(_path.SCHEMAS_DIR))


if __name__ == "__main__":
    unittest.main()
