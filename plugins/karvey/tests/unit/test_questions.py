"""Open questions ``Q-NN`` (architecture §1.16, C-16).

@req REQ-W3-028 REQ-W3-029 REQ-W3-030
"""
import shutil
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
from karvey_lib import questions as qs
from _state import GOOD_SPEC, make_project, run_json

TABLE = qs.TITLE + qs.HEADER + (
    "| Q-01 | Keep the old screen? | sponsor | 2026-10-20 | sample-change | Keeping it costs a week. | open | — |\n"
    "| Q-02 | Which retention applies? | tech lead | 2026-10-01 | sample-change | — | resolved → D-39 | D-39 |\n")


class Parse(unittest.TestCase):
    """@req REQ-W3-028"""

    def test_an_open_and_a_resolved_question(self):
        rows = qs.parse(TABLE)
        self.assertEqual([(q["id"], q["state"], q["resolved_by"]) for q in rows],
                         [("Q-01", "open", None), ("Q-02", "resolved", "D-39")])
        self.assertEqual(rows[0]["context"], "Keeping it costs a week.")
        self.assertEqual(rows[0]["changes"], ["sample-change"])
        self.assertEqual(rows[1]["context"], "")


class Ask(unittest.TestCase):
    """@req REQ-W3-028"""

    def test_REQ_W3_028_recorded_with_owner_and_needed_by(self):
        text = qs.add("", "Q-03", "Same-day access removal?", "sponsor", "2026-10-16", ["sample-change"],
                      "Same day needs a nightly check.")
        q = qs.parse(text)[0]
        self.assertEqual((q["id"], q["owner"], q["needed_by"], q["state"]), ("Q-03", "sponsor", "2026-10-16", "open"))
        more = qs.add(text, "Q-04", "Another?", "approver", "2026-10-18")
        self.assertEqual([q["id"] for q in qs.parse(more)], ["Q-03", "Q-04"])

    def test_REQ_W3_028_missing_owner_or_needed_by_names_the_field(self):
        with self.assertRaises(qs.QuestionError) as cm:
            qs.add("", "Q-03", "Same-day access removal?", "", "2026-10-16")
        self.assertEqual(cm.exception.field, "owner")
        self.assertIn("owner", str(cm.exception))
        with self.assertRaises(qs.QuestionError) as cm:
            qs.add("", "Q-03", "Same-day access removal?", "sponsor", "")
        self.assertEqual(cm.exception.field, "needed_by")
        with self.assertRaises(qs.QuestionError) as cm:
            qs.add("", "Q-03", "Same-day access removal?", "sponsor", "next week")
        self.assertEqual(cm.exception.field, "needed_by")

    def test_the_id_comes_from_the_id_tool(self):
        with self.assertRaises(qs.QuestionError) as cm:
            qs.add("", "3", "x?", "sponsor", "2026-10-16")
        self.assertIn("karvey-id.py next Q", str(cm.exception))


class Resolve(unittest.TestCase):
    """@req REQ-W3-029"""

    def test_REQ_W3_029_resolving_keeps_the_row_and_cites_the_decision(self):
        text = qs.resolve(TABLE, "Q-01", "D-40")
        rows = qs.parse(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[0]["state"], rows[0]["resolved_by"]), ("resolved", "D-40"))
        self.assertIn("| resolved → D-40 | D-40 |", text)

    def test_an_unknown_question_is_refused(self):
        with self.assertRaises(qs.QuestionError):
            qs.resolve(TABLE, "Q-09", "D-40")


class Open(unittest.TestCase):
    """@req REQ-W3-030"""

    def test_overdue_and_invalid_dates_are_flagged_overdue_first(self):
        text = qs.add(TABLE, "Q-05", "Needed yesterday?", "sponsor", "2026-10-13")
        text = text.replace("| Q-01 | Keep the old screen? | sponsor | 2026-10-20 |",
                            "| Q-01 | Keep the old screen? | sponsor | soon |")
        out = qs.open_questions(qs.parse(text), "2026-10-14")
        self.assertEqual([(q["id"], q["overdue"], q["date_invalid"]) for q in out],
                         [("Q-05", True, False), ("Q-01", False, True)])


class Validate(unittest.TestCase):
    """@req REQ-W3-029 — ``validate --all`` reports a decision citing a missing question."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-q-"))
        make_project(self.tmp, spec=dict(GOOD_SPEC))
        (self.tmp / "docs/spec/questions.md").write_text(TABLE, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def test_REQ_W3_029_dangling_reference(self):
        (self.tmp / "docs/spec/decisions.md").write_text(
            "# Decisions\n\n## D-40 — Keep the old screen (resolves Q-01)\n\n## D-41 — Retention (resolves Q-99)\n",
            encoding="utf-8")
        code, env = run_json("validate", "--all", "--root", str(self.tmp))
        self.assertEqual(code, 0, env["errors"])
        msgs = [w["message"] for w in env["warnings"] if w["code"] == "questions.dangling"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("dangling reference Q-99", msgs[0])
        self.assertIn("D-41", msgs[0])

    def test_no_register_no_check(self):
        (self.tmp / "docs/spec/questions.md").unlink()
        (self.tmp / "docs/spec/decisions.md").write_text("## D-06 — Something (Q-01)\n", encoding="utf-8")
        code, env = run_json("validate", "--all", "--root", str(self.tmp))
        self.assertFalse([w for w in env["warnings"] if w["code"] == "questions.dangling"])


if __name__ == "__main__":
    unittest.main()
