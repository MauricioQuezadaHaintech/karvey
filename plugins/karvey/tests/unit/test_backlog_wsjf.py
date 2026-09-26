"""The backlog ranked by WSJF (architecture §1.21, C-21).

@req REQ-W3-049 REQ-W3-050 REQ-W3-051 REQ-W3-052
"""
import unittest

import _path  # noqa: F401
from karvey_lib import backlog as bk

TODAY = "2026-10-14"


class Score(unittest.TestCase):
    """@req REQ-W3-049"""

    def test_REQ_W3_049_value_4_cod_3_effort_s_is_7(self):
        self.assertEqual(bk.score({"value": "4", "cod": "3", "effort": "S"}, TODAY)["score"], 7.0)

    def test_needed_by_in_20_days_value_2_effort_90_min_is_3(self):
        r = bk.score({"value": "2", "needed_by": "2026-11-03", "effort": "90 min"}, TODAY)
        self.assertEqual((r["urgency"], r["effort"], r["score"]), (4, 2, 3.0))

    def test_REQ_W3_049_no_effort_is_unscored_never_zero(self):
        r = bk.score({"value": "4", "cod": "3"}, TODAY)
        self.assertIsNone(r["score"])
        self.assertEqual(r["unscored"], "no effort")

    def test_urgency_mapping_and_past_dates(self):
        cases = {"2026-10-01": 5, "2026-10-28": 5, "2026-11-13": 4, "2026-12-13": 3, "2027-01-12": 2, "2027-03-01": 1}
        for day, want in cases.items():
            self.assertEqual(bk.urgency(None, day, TODAY)[0], want, day)
        self.assertEqual([bk.effort(x)[0] for x in ("S", "m", "L", "60", "240m", "241")], [1, 2, 3, 1, 2, 3])

    def test_a_malformed_cell_is_invalid(self):
        self.assertEqual(bk.score({"value": "high", "cod": "3", "effort": "S"}, TODAY)["invalid"],
                         "Value 'high' is not 1-5")
        self.assertIn("Effort", bk.score({"value": "2", "cod": "3", "effort": "XL"}, TODAY)["invalid"])


BACKLOG = ("# Discovery Backlog\n\n| ID | Date | Origin | Type | Priority | Title | Status | Tracker | "
           "Promoted to change-id | Value | Effort | CoD | Needed by | Client | Reviewed | Commit |\n"
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
           "| BL-01 | 2026-10-01 | retro | tech-debt | low | Tidy a helper | done-direct | — | — | 2 | 30 | — | — | — | "
           "2026-10-10 | %s |\n")


class DoneDirect(unittest.TestCase):
    """@req REQ-W3-050"""

    def setUp(self):
        import tempfile
        from pathlib import Path
        from _state import GOOD_SPEC, make_project
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-bl-"))
        self.addCleanup(__import__("shutil").rmtree, str(self.tmp), True)
        make_project(self.tmp, spec=dict(GOOD_SPEC))

    def validate(self, commit):
        from _state import run_json
        (self.tmp / "docs/spec/backlog.md").write_text(BACKLOG % commit, encoding="utf-8")
        return run_json("validate", "--all", "--root", str(self.tmp))

    def test_REQ_W3_050_done_direct_with_a_commit_is_valid(self):
        code, env = self.validate("abc1234")
        self.assertEqual(code, 0, env["errors"])

    def test_REQ_W3_050_done_direct_without_a_commit_is_refused_naming_the_row(self):
        code, env = self.validate("—")
        self.assertEqual(code, 1)
        err = [e for e in env["errors"] if e["code"] == "backlog.done_direct"]
        self.assertEqual(len(err), 1)
        self.assertIn("BL-01: done-direct needs the commit", err[0]["message"])


if __name__ == "__main__":
    unittest.main()
