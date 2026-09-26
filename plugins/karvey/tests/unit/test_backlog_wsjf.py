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


if __name__ == "__main__":
    unittest.main()
