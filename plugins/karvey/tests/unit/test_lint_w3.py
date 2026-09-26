"""Wave 3 linter checks L-55..L-75 (architecture §1.25): one passing and one failing mutation per check.

Each case copies the good mini-plugin of ``test_lint_plugin`` and applies one mutation.
"""
import unittest

import _path  # noqa: F401
from test_lint_plugin import SKILLS, LintCase


class L62(LintCase):
    """@req REQ-W3-072 — a Load: entry names an existing file."""
    SKILL = SKILLS + "/karvey-qa/SKILL.md"

    def test_good_fixture_passes(self):
        self.assertPasses("L-62")

    def test_existing_entry_passes(self):
        self.t.write(SKILLS + "/karvey/rules/gates.md", "# Gates\n")
        self.t.sub(self.SKILL, r"(?m)^(# .*)$", r"\1\nLoad: gates.md")
        self.assertPasses("L-62")

    def test_missing_reference_fails_naming_skill_line_and_file(self):
        self.t.sub(self.SKILL, r"(?m)^(# .*)$", r"\1\nLoad: references/gone.md")
        fs = self.assertFails("L-62", "references/gone.md", file=self.SKILL)
        self.assertIn("skill karvey-qa", fs[0]["message"])
        text = self.t.read(self.SKILL).splitlines()
        self.assertEqual(text[fs[0]["line"] - 1], "Load: references/gone.md")


if __name__ == "__main__":
    unittest.main()
