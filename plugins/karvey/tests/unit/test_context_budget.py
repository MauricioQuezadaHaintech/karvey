"""The size tool (architecture §1.3, C-01): ``karvey_lib/loadlist.py`` and ``karvey-context-budget.py``.

@req REQ-W3-001 REQ-W3-002 REQ-W3-010 REQ-W3-011 REQ-W3-071 REQ-W3-072
"""
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
from karvey_lib import loadlist

FIX = _path.UNIT_DIR / "fixtures" / "budget"
RULES = FIX / "skills" / "karvey" / "rules"
TOOL = _path.SCRIPTS_DIR / "karvey-context-budget.py"


def names(paths):
    return [loadlist.rel(p, FIX) for p in paths]


class Library(unittest.TestCase):
    """@req REQ-W3-001 — declared, cited, graph, closure and size."""

    def setUp(self):
        self.alpha = (FIX / "skills" / "karvey-alpha" / "SKILL.md").read_text(encoding="utf-8")
        self.g = loadlist.graph(RULES)

    def test_declared_parses_the_load_line(self):
        self.assertEqual(loadlist.declared(self.alpha), ["a.md", "adapters/{tool}.md", "e.md?"])
        self.assertEqual(loadlist.parse_load(self.alpha)[0], 7)
        beta = (FIX / "skills" / "karvey-beta" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIsNone(loadlist.declared(beta))

    def test_footnote_and_fenced_paths_are_not_cited(self):
        toks = loadlist.cited(self.alpha)
        self.assertNotIn("rules/c.md", toks)
        self.assertNotIn("rules/d.md", toks)
        self.assertIn("a.md", toks)

    def test_closure_of_the_fixture(self):
        refs = loadlist.refs_of(self.alpha, RULES, FIX / "skills" / "karvey-alpha")
        self.assertEqual(names(loadlist.closure(refs, self.g, "max")),
                         ["skills/karvey/rules/a.md", "skills/karvey/rules/adapters/large.md",
                          "skills/karvey/rules/b.md", "skills/karvey/rules/e.md"])
        self.assertEqual(names(loadlist.closure(refs, self.g, "min")),
                         ["skills/karvey/rules/a.md", "skills/karvey/rules/adapters/small.md",
                          "skills/karvey/rules/b.md"])

    def test_rule_cycle_terminates(self):
        a = RULES / "a.md"
        self.assertEqual(names(loadlist.closure([((a,), False)], self.g)),
                         ["skills/karvey/rules/a.md", "skills/karvey/rules/b.md"])

    def test_placeholder_min_is_smallest_max_is_largest(self):
        small, large = RULES / "adapters" / "small.md", RULES / "adapters" / "large.md"
        ref = (tuple(sorted((small, large))), False)
        self.assertEqual(loadlist.pick(ref, "min"), small)
        self.assertEqual(loadlist.pick(ref, "max"), large)
        self.assertIsNone(loadlist.pick(((small,), True), "min"))

    def test_words_exclude_frontmatter_and_tokens_are_estimated(self):
        p = FIX / "skills" / "karvey-beta" / "SKILL.md"
        s = loadlist.size(p)
        raw = p.read_bytes()
        self.assertEqual(s["bytes"], len(raw))
        self.assertEqual(s["tokens_est"], math.ceil(len(raw) / 4))
        self.assertEqual(s["tokens_quality"], "estimated")
        self.assertEqual(s["words"], len("# Beta Read `../karvey/rules/b.md` before starting.".split()))

    def test_missing_load_entry_is_reported(self):
        text = "---\nname: x\n---\nLoad: a.md, references/gone.md\n"
        self.assertEqual(loadlist.missing_load_entries(text, RULES, FIX / "skills" / "karvey-alpha"),
                         [(4, "references/gone.md")])

    def test_first_diff_names_the_line(self):
        self.assertIsNone(loadlist.first_diff("a\nb\n", "a\nb\n"))
        self.assertEqual(loadlist.first_diff("a\nb\n", "a\nc\n"), (2, "b", "c"))


if __name__ == "__main__":
    unittest.main()
