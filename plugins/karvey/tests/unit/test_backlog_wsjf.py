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


class DoneDirectInGit(unittest.TestCase):
    """BUG-135: in a repository the done-direct commit must exist; an unknown state is reported."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        import _gitrepo as g
        from _state import GOOD_SPEC, make_project
        g.isolate_git()
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-bl-git-"))
        self.addCleanup(__import__("shutil").rmtree, str(self.tmp), True)
        self.root = g.init(self.tmp / "repo")
        make_project(self.root, spec=dict(GOOD_SPEC))
        g.run(["add", "-A"], self.root)
        g.run(["commit", "-q", "-m", "base"], self.root)

    def validate(self, commit, status="done-direct"):
        from _state import run_json
        (self.root / "docs/spec/backlog.md").write_text((BACKLOG % commit).replace("| done-direct |", "| %s |" % status),
                                                        encoding="utf-8")
        return run_json("validate", "--all", "--root", str(self.root))

    def test_BUG_135_a_done_direct_commit_that_is_not_in_git_is_refused(self):
        code, env = self.validate("0000000")
        self.assertEqual(code, 1, env)
        self.assertTrue(any("0000000 is not a commit of this repository" in e["message"] for e in env["errors"]))

    def test_BUG_135_a_real_commit_is_accepted(self):
        import subprocess
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(self.root), capture_output=True,
                             text=True).stdout.strip()
        code, env = self.validate(sha)
        self.assertEqual(code, 0, env["errors"])

    def test_BUG_135_an_unknown_state_is_a_warning_not_dropped(self):
        code, env = self.validate("—", status="done")
        self.assertEqual(code, 0, env["errors"])
        self.assertTrue(any(w["code"] == "backlog.state" and "BL-01" in w["message"] for w in env["warnings"]))
        self.assertEqual(bk.state_of("open (blocked)"), "open")


class View(unittest.TestCase):
    """@req REQ-W3-051"""

    def setUp(self):
        import tempfile
        from pathlib import Path
        import _gitrepo as g
        g.isolate_git()
        self.g = g
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-bl-view-"))
        self.addCleanup(__import__("shutil").rmtree, str(self.tmp), True)
        self.root = g.init(self.tmp / "repo")
        rows = []
        for i in range(1, 11):
            value, cod, eff, reviewed = str(1 + i % 5), str(1 + (i * 2) % 5), "SML"[i % 3], "2026-10-%02d" % i
            if i == 3:
                eff = "—"  # unscored
            if i == 7:
                value = "high"  # malformed
            if i in (1, 2):
                reviewed = "2026-08-01"  # stale
            rows.append("| BL-%02d | 2026-08-01 | retro | feature | low | Item %d | open | — | — | %s | %s | %s | — | — "
                        "| %s | — |" % (i, i, value, eff, cod, reviewed))
        rows.append("| BL-11 | 2026-08-01 | retro | feature | low | Closed one | discarded | — | — | 5 | S | 5 | — | — "
                    "| 2026-10-01 | — |")
        text = ("# Discovery Backlog\n\n| ID | Date | Origin | Type | Priority | Title | Status | Tracker | Promoted "
                "to change-id | Value | Effort | CoD | Needed by | Client | Reviewed | Commit |\n" + "|---" * 16 + "|\n"
                + "\n".join(rows) + "\n")
        g.write(self.root, "docs/spec/backlog.md", text)
        g.write(self.root, "docs/spec/project.json", {"repos": ["repo"]})
        g.run(["add", "-A"], self.root)
        g.run(["commit", "-q", "-m", "fixture"], self.root)

    def view(self, *argv):
        import contextlib
        import importlib.util
        import io
        import json
        m = importlib.util.spec_from_file_location("karvey_context_bl", str(_path.SCRIPTS_DIR / "karvey-context.py"))
        mod = importlib.util.module_from_spec(m)
        m.loader.exec_module(mod)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = mod.main(["--backlog", "--root", str(self.root), "--as-of", TODAY] + list(argv))
        return code, out.getvalue()

    def test_REQ_W3_051_ordered_by_score_with_stale_flagged(self):
        import json
        code, out = self.view("--json")
        self.assertEqual(code, 0, out)
        res = json.loads(out)["result"]
        scores = [x["score"] for x in res["scored"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(len(res["scored"]), 8)
        self.assertEqual({x["id"] for x in res["scored"] if x["stale"]}, {"BL-01", "BL-02"})
        self.assertEqual([x["id"] for x in res["unscored"]], ["BL-03"])
        self.assertNotIn("BL-11", out)

    def test_REQ_W3_051_a_malformed_row_is_an_invalid_row_and_the_rest_render(self):
        code, out = self.view()
        self.assertIn("invalid row BL-07: Value 'high' is not 1-5", out)
        self.assertIn("BL-01", out)
        self.assertIn("stale (reviewed 2026-08-01)", out)

    def test_BUG_135_open_with_a_note_is_listed_and_an_unknown_state_is_invalid(self):
        import json
        p = self.root / "docs/spec/backlog.md"
        text = p.read_text(encoding="utf-8").replace("| Item 4 | open |", "| Item 4 | open (blocked) |")
        text = text.replace("| Item 5 | open |", "| Item 5 | done |")
        p.write_text(text, encoding="utf-8")
        code, out = self.view("--json")
        res = json.loads(out)["result"]
        listed = {x["id"] for x in res["scored"] + res["unscored"]}
        self.assertIn("BL-04", listed)
        self.assertNotIn("BL-05", listed)
        self.assertIn({"id": "BL-05", "reason": "status 'done' is not one of open, promoted, discarded, done-direct"},
                      res["invalid"])

    def test_read_only(self):
        import subprocess
        self.view()
        st = subprocess.run(["git", "status", "--porcelain"], cwd=str(self.root), capture_output=True, text=True)
        self.assertEqual(st.stdout.strip(), "")


class Cadence(unittest.TestCase):
    """@req REQ-W3-052"""

    def overview(self, header, project=None):
        import contextlib
        import importlib.util
        import io
        import json
        import tempfile
        from pathlib import Path
        from _state import make_project
        tmp = Path(tempfile.mkdtemp(prefix="karvey-bl-cad-"))
        self.addCleanup(__import__("shutil").rmtree, str(tmp), True)
        make_project(tmp, project=project or {"repos": ["r"]})
        (tmp / "docs/spec/backlog.md").write_text("# Discovery Backlog\n\n%s\n| ID | Status |\n|---|---|\n" % header,
                                                   encoding="utf-8")
        m = importlib.util.spec_from_file_location("karvey_context_cad", str(_path.SCRIPTS_DIR / "karvey-context.py"))
        mod = importlib.util.module_from_spec(m)
        m.loader.exec_module(mod)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            mod.main(["--root", str(tmp), "--section", "overview", "--now", "2026-10-14T10:00:00-03:00"])
        text = out.getvalue()
        return [ln for ln in text.splitlines() if ln.startswith("backlog refinement")][0]

    def test_REQ_W3_052_refined_5_days_ago_shows_the_date_without_a_flag(self):
        self.assertEqual(self.overview("Last refinement: 2026-10-09"), "backlog refinement: 2026-10-09 (5 days ago)")

    def test_20_days_is_overdue(self):
        self.assertIn("overdue: every 14 days", self.overview("Last refinement: 2026-09-24"))

    def test_REQ_W3_052_no_header_is_never_refined(self):
        self.assertEqual(self.overview(""), "backlog refinement: never refined")

    def test_the_cadence_is_configurable(self):
        line = self.overview("Last refinement: 2026-09-24", {"repos": ["r"], "backlog": {"refine_days": 30}})
        self.assertEqual(line, "backlog refinement: 2026-09-24 (20 days ago)")



class StaleHeader(unittest.TestCase):
    def test_BUG_115_a_row_less_table_before_does_not_hide_the_backlog(self):
        pre = [b["id"] for b in bk.parse(BACKLOG)]
        self.assertTrue(pre)
        self.assertEqual([b["id"] for b in bk.parse("| Note | Value |\n|------|-------|\n\n" + BACKLOG)], pre)


if __name__ == "__main__":
    unittest.main()
