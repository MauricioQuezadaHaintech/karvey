"""The risk register (architecture §1.17, C-17).

@req REQ-W3-031 REQ-W3-033 REQ-W3-034
"""
import shutil
import tempfile
import unittest
from pathlib import Path

import _path
from karvey_lib import risks as rk
from _state import GOOD_SPEC, make_project, run_json

OWN = _path.REPO_ROOT / "docs/spec/changes/wave3-optimization"
REG = rk.HEADER + ("| R-1 | Provider outage | Low | Medium | tech lead | outage notice | message on screen | open | "
                   "2026-10-13 tech lead |\n"
                   "| R-2 | Records kept too long | Low | Medium |  | retention review | purge | mitigated | "
                   "2026-10-12 |\n")


class Register(unittest.TestCase):
    """@req REQ-W3-031"""

    @unittest.skipUnless((OWN / "risks.md").is_file(), "not this repository")
    def test_this_changes_own_register_parses(self):
        rows = rk.read(OWN)
        self.assertEqual([r["id"] for r in rows], ["R-%d" % i for i in range(1, 10)])
        self.assertEqual(rk.problems(rows), [])
        self.assertTrue(all(r["state"] in rk.STATES for r in rows))

    def test_REQ_W3_031_a_row_without_owner_is_reported(self):
        self.assertEqual(rk.problems(rk.parse(REG)), [("R-2", "owner", "R-2: owner missing")])

    def test_no_file_is_no_risks(self):
        tmp = Path(tempfile.mkdtemp(prefix="karvey-risks-"))
        try:
            self.assertEqual(rk.read(tmp), [])
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)

    def test_state_and_review_date(self):
        rows = rk.parse(REG.replace("| mitigated |", "| moved → BL-12 |"))
        self.assertEqual((rows[1]["state"], rows[0]["reviewed_on"]), ("moved", "2026-10-13"))
        self.assertEqual([r["id"] for r in rk.open_risks(rows)], ["R-1"])


class Validate(unittest.TestCase):
    """@req REQ-W3-031 — the state tool reports the risk id and the missing owner."""

    def test_validate_reports_the_missing_owner_as_a_warning(self):
        tmp = Path(tempfile.mkdtemp(prefix="karvey-risks-v-"))
        try:
            spec = make_project(tmp, spec=dict(GOOD_SPEC))
            (spec.parent / "risks.md").write_text(REG, encoding="utf-8")
            code, env = run_json("validate", str(spec), "--strict", "--root", str(tmp))
            self.assertEqual(code, 0, env["errors"])
            w = [x for x in env["warnings"] if x["code"] == "risks.owner"]
            self.assertEqual([(x["path"], x["message"]) for x in w], [("R-2", "R-2: owner missing")])
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
