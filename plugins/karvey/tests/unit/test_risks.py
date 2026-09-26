"""The risk register (architecture §1.17, C-17).

@req REQ-W3-031 REQ-W3-033 REQ-W3-034
"""
import shutil
import tempfile
import unittest
from pathlib import Path

import json

import _path
import _gitrepo as g
from karvey_lib import risks as rk
from _state import GOOD_SPEC, make_project, run_json

g.isolate_git()

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


class Command(unittest.TestCase):
    """@req REQ-W3-031 REQ-W3-034 — ``karvey-state.py risk``."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-risk-cmd-"))
        self.root = g.init(self.tmp / "repo")
        self.spec = make_project(self.root, spec=dict(GOOD_SPEC), project={"repos": ["sample-repo"]})
        self.reg = self.spec.parent / "risks.md"
        self.reg.write_text(REG.replace("|  | retention review", "| product owner | retention review"),
                            encoding="utf-8")
        g.run(["add", "-A"], self.root)
        g.run(["commit", "-q", "-m", "fixture"], self.root)

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def risk(self, *argv):
        return run_json("risk", "feat-a", *(list(argv) + ["--root", str(self.root)]))

    def data(self):
        return json.loads(self.spec.read_text(encoding="utf-8"))

    def test_review_updates_last_review_and_logs(self):
        code, env = self.risk("R-1", "review", "--by-role", "tech lead", "--reason", "still relevant")
        self.assertEqual(code, 0, env)
        row = rk.read(self.spec.parent)[0]
        self.assertEqual(row["state"], "open")
        self.assertTrue(row["last_review"].endswith("tech lead"))
        log = self.data()["risk_log"]
        self.assertEqual((log[0]["risk"], log[0]["from"], log[0]["to"], log[0]["reason"]),
                         ("R-1", "open", "open", "still relevant"))

    def test_REQ_W3_034_move_reserves_a_backlog_id_and_writes_the_row(self):
        code, env = self.risk("R-1", "move", "--by-role", "tech lead", "--reason", "later release")
        self.assertEqual(code, 0, env)
        row = rk.read(self.spec.parent)[0]
        self.assertRegex(row["state_cell"], r"^moved → BL-\d+$")
        bl = row["state_cell"].split("→ ")[1]
        backlog = (self.root / "docs/spec/backlog.md").read_text(encoding="utf-8")
        self.assertIn("| %s |" % bl, backlog)
        self.assertIn("feat-a / R-1", backlog)
        self.assertEqual(self.data()["risk_log"][-1]["ref"], bl)

    def test_close_and_mitigate(self):
        self.risk("R-1", "close", "--reason", "provider replaced")
        self.risk("R-2", "mitigate")
        self.assertEqual([r["state"] for r in rk.read(self.spec.parent)], ["closed", "mitigated"])
        self.assertEqual([e["to"] for e in self.data()["risk_log"]], ["closed", "mitigated"])

    def test_unknown_risk_id_is_exit_4(self):
        before = self.reg.read_bytes()
        code, env = self.risk("R-9", "close")
        self.assertEqual(code, 4)
        self.assertEqual(self.reg.read_bytes(), before)
        self.assertNotIn("risk_log", self.data())

    def test_the_spec_stays_valid_strict(self):
        self.risk("R-1", "accept", "--by-role", "sponsor")
        code, env = run_json("validate", str(self.spec), "--strict", "--root", str(self.root))
        self.assertEqual(code, 0, env["errors"])


if __name__ == "__main__":
    unittest.main()
