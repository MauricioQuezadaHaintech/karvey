"""Wave 3 linter checks L-55..L-75 (architecture §1.25): one passing and one failing mutation per check.

Each case copies the good mini-plugin of ``test_lint_plugin`` and applies one mutation.
"""
import json
import unittest

import _path
from test_lint_plugin import SKILLS, LintCase

MODES = "plugins/karvey/schemas/check-modes.json"


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


class L73(LintCase):
    """@req REQ-W3-061 — every check id used in code is registered with a 4.1 mode."""
    SCRIPT = "plugins/karvey/scripts/karvey-sample.py"

    def setUp(self):
        super().setUp()
        self.t.write(MODES, json.loads((_path.SCHEMAS_DIR / "check-modes.json").read_text(encoding="utf-8")))

    def test_registered_id_passes(self):
        self.t.write(self.SCRIPT, "from karvey_lib import modes\nm = modes.resolve(root, \"risks.owner\")\n")
        self.assertPasses("L-73")

    def test_unregistered_id_fails(self):
        self.t.write(self.SCRIPT, "from karvey_lib import modes\n\nm = modes.resolve(root, \"nope.check\")\n")
        fs = self.assertFails("L-73", "'nope.check'", file=self.SCRIPT)
        self.assertEqual(fs[0]["line"], 3)

    def test_row_without_41_fails(self):
        reg = json.loads(self.t.read(MODES))
        del reg["checks"][0]["defaults"]["4.1"]
        self.t.write(MODES, reg)
        self.assertFails("L-73", "no 4.1 default", file=MODES)


class L47(LintCase):
    """@req REQ-W2-083 REQ-W2-085 — the Wave 2 rows keep their 3.13/4.0 contract."""

    def setUp(self):
        super().setUp()
        self.t.write(MODES, json.loads((_path.SCHEMAS_DIR / "check-modes.json").read_text(encoding="utf-8")))

    def test_registry_passes(self):
        self.assertPasses("L-47")

    def test_blocking_313_default_fails(self):
        reg = json.loads(self.t.read(MODES))
        row = next(c for c in reg["checks"] if c["id"] == "lane.diff")
        row["defaults"]["3.13"] = "blocking"
        self.t.write(MODES, reg)
        self.assertFails("L-47", "lane.diff: the 3.13 default", file=MODES)


if __name__ == "__main__":
    unittest.main()
