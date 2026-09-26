"""The CI workflow `.github/workflows/lint.yml` (architecture §1.11) selects real work, once (F-36, F-37).

Read as text: no YAML parser in the standard library, and the checks only need the ``run:`` lines.
"""
import re
import subprocess
import sys
import unittest

import _path

WORKFLOW = _path.REPO_ROOT / ".github" / "workflows" / "lint.yml"
RUN_TABLES = _path.PLUGIN_ROOT / "tests" / "hooks" / "run_tables.py"


def jobs():
    """``{job: text}`` of the workflow's jobs."""
    text = WORKFLOW.read_text(encoding="utf-8")
    body = text.split("\njobs:\n", 1)[1]
    out, cur = {}, None
    for line in body.splitlines():
        m = re.match(r"^  ([\w-]+):\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = ""
        elif cur:
            out[cur] += line + "\n"
    return out


@unittest.skipUnless(WORKFLOW.is_file(), "not this repository")
class WindowsAdvisory(unittest.TestCase):
    def setUp(self):
        self.job = jobs()["windows-advisory"]

    def test_stays_advisory(self):
        self.assertIn("continue-on-error: true", self.job)

    def test_every_tag_selection_selects_cases(self):
        tags = re.findall(r"run_tables\.py[^\n]*--tag\s+([\w-]+)", self.job)
        self.assertTrue(tags, "the job runs no guard-table selection")
        for tag in tags:
            with self.subTest(tag=tag):
                p = subprocess.run([sys.executable, str(RUN_TABLES), "--tag", tag], capture_output=True, text=True,
                                   timeout=300)
                self.assertNotIn("no case selected", p.stdout)
                self.assertRegex(p.stdout, r"guard tables: [1-9]\d* cases")

    def test_runs_the_path_translation_unit_tests(self):
        for mod in ("test_paths", "test_hookio", "test_atomicio"):
            self.assertIn(mod, self.job)
            self.assertTrue((_path.UNIT_DIR / (mod + ".py")).is_file())


@unittest.skipUnless(WORKFLOW.is_file(), "not this repository")
class TablesRunOnce(unittest.TestCase):
    """F-37: test-hooks.sh runs every guard table unless KARVEY_SKIP_TABLES=1; the tests job already runs
    run_tables.py (with junit), so the test-hooks.sh step must skip them."""

    def test_test_hooks_step_skips_the_tables_when_run_tables_runs(self):
        job = jobs()["tests"]
        self.assertIn("run_tables.py --junit", job)
        steps = re.split(r"\n      - ", job)
        hooks = [s for s in steps if s.startswith("run: bash") and "test-hooks.sh" in s]
        self.assertEqual(len(hooks), 1, hooks)
        self.assertRegex(hooks[0], r"KARVEY_SKIP_TABLES:\s*'?1'?")

    def test_test_hooks_honours_the_switch(self):
        text = (_path.PLUGIN_ROOT / "hooks" / "tests" / "test-hooks.sh").read_text(encoding="utf-8")
        self.assertIn('"${KARVEY_SKIP_TABLES:-}" != "1"', text)


@unittest.skipUnless(WORKFLOW.is_file(), "not this repository")
class ContextSizeStep(unittest.TestCase):
    """@req REQ-W3-011 — the lint job runs the size comparison after the linter, read-only and pinned."""

    def test_size_step_follows_the_linter_in_the_lint_job(self):
        job = jobs()["lint"]
        runs = re.findall(r"- run: (.*)", job)
        lint = next(i for i, r in enumerate(runs) if "lint-plugin.py" in r)
        size = next(i for i, r in enumerate(runs) if "karvey-context-budget.py compare" in r)
        self.assertGreater(size, lint)
        self.assertIn("--live", runs[size])
        self.assertIn("--warn-growth 10", runs[size])
        base = re.search(r"compare (\S+)", runs[size]).group(1)
        self.assertTrue((_path.REPO_ROOT / base).is_file(), base)

    def test_workflow_stays_read_only_and_pinned(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("secrets.", text)
        self.assertNotRegex(text, r"(?m)^\s*pull_request_target:")
        self.assertNotRegex(text, r"(?m)^\s*(contents|packages|id-token|pull-requests):\s*write")
        for use in re.findall(r"uses:\s*(\S+)", text):
            self.assertRegex(use, r"@[0-9a-f]{40}$", use)


if __name__ == "__main__":
    unittest.main()
