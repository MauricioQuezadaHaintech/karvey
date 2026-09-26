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


def run(*args, cwd=None):
    p = subprocess.run([sys.executable, str(TOOL)] + list(args), capture_output=True, text=True, timeout=120,
                       cwd=cwd)
    return p.returncode, p.stdout, p.stderr


def git_status():
    return subprocess.run(["git", "-C", str(_path.REPO_ROOT), "status", "--porcelain"], capture_output=True,
                          text=True, timeout=30).stdout


class Measure(unittest.TestCase):
    """@req REQ-W3-001 REQ-W3-071 REQ-W3-072 — the ``measure`` command."""

    def test_REQ_W3_071_two_runs_give_identical_bytes(self):
        before = git_status()
        rc1, out1, _ = run("measure", "--label", "check", "--json")
        rc2, out2, _ = run("measure", "--label", "check", "--json")
        self.assertEqual(rc1, 0)
        self.assertIsNone(loadlist.first_diff(out1, out2))
        self.assertEqual(out1, out2)
        self.assertEqual(git_status(), before, "the measure run wrote into the repository")
        # a stamped output is caught and the first differing line is named
        lines = out1.splitlines()
        stamped = "\n".join(lines[:3] + ['  "at": "2026-01-01T00:00:00+00:00",'] + lines[3:]) + "\n"
        diff = loadlist.first_diff(out1, stamped)
        self.assertEqual(diff[0], 4)
        self.assertIn('"at"', diff[2])

    def test_every_phase_skill_has_a_row_and_json_is_sorted_without_absolute_paths(self):
        rc, out, _ = run("measure", "--label", "check", "--json")
        env = json.loads(out)
        snap = env["result"]
        skills = [r["skill"] for r in snap["rows"]]
        self.assertEqual(skills, sorted(skills))
        for sk in ("karvey", "karvey-requirements", "karvey-deploy", "karvey-archive"):
            self.assertIn(sk, skills)
        for r in snap["rows"]:
            for k in ("own", "direct", "closure_min", "closure_max"):
                self.assertEqual(r[k]["tokens_quality"], "estimated")
            self.assertLessEqual(r["closure_min"]["bytes"], r["closure_max"]["bytes"])
        self.assertIsInstance(snap["session_hook"]["bytes"], int)
        self.assertEqual(out, json.dumps(env, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        self.assertNotIn(str(_path.REPO_ROOT), out)
        self.assertNotIn(tempfile.gettempdir(), out)

    def test_fixture_rows_and_phases(self):
        rc, out, _ = run("measure", "--plugin", str(FIX), "--json")
        self.assertEqual(rc, 0, out)
        rows = {r["skill"]: r for r in json.loads(out)["result"]["rows"]}
        self.assertEqual(sorted(rows), ["karvey", "karvey-alpha", "karvey-beta"])
        self.assertEqual(rows["karvey-beta"]["phases"], ["beta", "beta-close"])
        self.assertTrue(rows["karvey-alpha"]["has_load_line"])
        self.assertIsNone(json.loads(out)["result"]["session_hook"]["bytes"])

    def test_REQ_W3_072_missing_load_file_exits_1_naming_skill_line_file(self):
        tmp = tempfile.mkdtemp(prefix="karvey-budget-t-")
        try:
            tree = Path(tmp) / "plugin"
            shutil.copytree(str(FIX), str(tree))
            sk = tree / "skills" / "karvey-alpha" / "SKILL.md"
            sk.write_text(sk.read_text(encoding="utf-8").replace("e.md?", "e.md?, references/gone.md"),
                          encoding="utf-8")
            rc, out, err = run("measure", "--plugin", str(tree))
            self.assertEqual(rc, 1)
            self.assertIn("skills/karvey-alpha/SKILL.md:7", err)
            self.assertIn("references/gone.md", err)
            rc, out, _ = run("measure", "--plugin", str(tree), "--json")
            e = json.loads(out)["errors"][0]
            self.assertEqual((e["file"], e["path"], e["got"]),
                             ("skills/karvey-alpha/SKILL.md", "line 7", "references/gone.md"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
