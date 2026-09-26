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


def snapshot(sizes, hook=None):
    return {"method_version": "x", "rows": [{"skill": k, "closure_max": {"bytes": v}} for k, v in sorted(sizes.items())],
            "session_hook": {"bytes": hook}}


class Compare(unittest.TestCase):
    """@req REQ-W3-010 REQ-W3-011 — the ``compare`` command."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-budget-c-"))

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def write(self, name, obj):
        p = self.tmp / name
        p.write_text(json.dumps(obj), encoding="utf-8")
        return str(p)

    BASE = {"a": 1000, "b": 1000, "c": 1000}

    def test_median_below_target_exits_1_naming_the_median(self):
        base = self.write("base.json", snapshot(self.BASE))
        after = self.write("after.json", snapshot({"a": 650, "b": 650, "c": 650}))
        rc, out, err = run("compare", base, after)
        self.assertEqual(rc, 1)
        self.assertIn("median reduction 35% is below the 40% target", err)

    def test_phase_below_target_listed_with_reason_or_unexplained(self):
        base = self.write("base.json", snapshot(self.BASE))
        after = self.write("after.json", snapshot({"a": 550, "b": 550, "c": 800}))
        rc, out, _ = run("compare", base, after, "--json")
        self.assertEqual(rc, 0, out)
        res = json.loads(out)["result"]
        self.assertEqual(res["median_reduction_pct"], 45.0)
        self.assertEqual(res["below_target"], [{"skill": "c", "before": 1000, "after": 800, "reduction_pct": 20.0,
                                                "reason": "unexplained"}])
        reasons = self.write("reasons.json", {"reasons": {"c": "the phase keeps its full deploy flow"}})
        rc, out, _ = run("compare", base, after, "--reasons", reasons)
        self.assertEqual(rc, 0)
        self.assertIn("the phase keeps its full deploy flow", out)

    def test_growth_warns_with_phase_and_percent_and_exits_0(self):
        base = self.write("base.json", snapshot(self.BASE))
        after = self.write("after.json", snapshot({"a": 1150, "b": 1000, "c": 1050}))
        rc, out, _ = run("compare", base, after, "--warn-growth", "10")
        self.assertEqual(rc, 0)
        warns = [ln for ln in out.splitlines() if ln.startswith("::warning")]
        self.assertEqual(len(warns), 1)
        self.assertIn("a closure grew 15%", warns[0])

    def test_live_against_itself_does_not_warn(self):
        rc, out, _ = run("measure", "--label", "now", "--json")
        base = self.write("now.json", json.loads(out))
        rc, out, _ = run("compare", base, "--live", "--warn-growth", "10")
        self.assertEqual(rc, 0)
        self.assertNotIn("::warning", out)

    def test_missing_snapshot_exits_4(self):
        rc, _, _ = run("compare", str(self.tmp / "none.json"), "--live")
        self.assertEqual(rc, 4)


BASELINE = "docs/spec/retros/context-size-4.0.0.json"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True, timeout=30,
                          check=True).stdout


class Order(unittest.TestCase):
    """@req REQ-W3-002 — the baseline commit precedes every reorganisation commit of the change."""

    @unittest.skipUnless((_path.REPO_ROOT / BASELINE).is_file(), "not this repository")
    def test_REQ_W3_002_baseline_precedes_moves(self):
        shallow = subprocess.run(["git", "-C", str(_path.REPO_ROOT), "rev-parse", "--is-shallow-repository"],
                                 capture_output=True, text=True).stdout.strip()
        if shallow == "true":
            self.skipTest("shallow clone: no history to order")
        rc, out, err = run("order", "--baseline", BASELINE, "--change", "wave3-optimization", "--root",
                           str(_path.REPO_ROOT), "--json")
        res = json.loads(out)["result"]
        self.assertTrue(res["baseline_commit"], "the baseline is not committed")
        self.assertEqual(rc, 0, res["message"])

    def test_the_stored_baseline_is_reproducible_at_its_commit(self):
        path = _path.REPO_ROOT / BASELINE
        if not path.is_file():
            self.skipTest("not this repository")
        snap = json.loads(path.read_text(encoding="utf-8"))["result"]
        self.assertEqual(snap["method_version"], "4.0.0")
        self.assertTrue(snap["date"])

    def test_a_move_before_the_baseline_is_reported(self):
        tmp = Path(tempfile.mkdtemp(prefix="karvey-budget-o-"))
        try:
            git(tmp, "init", "-q")
            git(tmp, "config", "user.email", "dev@example.org")
            git(tmp, "config", "user.name", "Developer")
            sk = tmp / "plugins" / "karvey" / "skills" / "karvey-x"
            sk.mkdir(parents=True)
            (sk / "SKILL.md").write_text("x\n", encoding="utf-8")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-q", "-m", "seed")
            git(tmp, "mv", "plugins/karvey/skills/karvey-x/SKILL.md", "plugins/karvey/skills/karvey-x/OLD.md")
            git(tmp, "commit", "-q", "-m", "move\n\nKarvey-Change: demo")
            (tmp / "docs" / "spec" / "retros").mkdir(parents=True)
            (tmp / BASELINE).write_text("{}\n", encoding="utf-8")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-q", "-m", "baseline\n\nKarvey-Change: demo")
            rc, out, err = run("order", "--baseline", BASELINE, "--change", "demo", "--root", str(tmp))
            self.assertEqual(rc, 1)
            self.assertIn("baseline missing or taken after the reorganisation", err)
        finally:
            shutil.rmtree(str(tmp), ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
