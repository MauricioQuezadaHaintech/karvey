"""``karvey-contrast-check.py`` (architecture §1.18, C-18).

@req REQ-W3-038
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _path

TOOL = _path.SCRIPTS_DIR / "karvey-contrast-check.py"
SEED = _path.UNIT_DIR / "fixtures" / "design" / "design-system.md"
PAIRS = "\n## Pairs\n\n| Text token | Background token | Level |\n|---|---|---|\n"


def palette(rows, pairs):
    return ("## Colour\n\n| Token | Light | Dark | Changed by |\n|---|---|---|---|\n" +
            "".join("| `%s` | `%s` | `%s` | sample |\n" % r for r in rows) + PAIRS +
            "".join("| `%s` | `%s` | %s |\n" % p for p in pairs))


class Contrast(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-contrast-"))

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def run_tool(self, *argv):
        cp = subprocess.run([sys.executable, str(TOOL), "--root", str(self.tmp), "--json"] + list(argv),
                            capture_output=True, text=True, timeout=60)
        return cp.returncode, json.loads(cp.stdout)

    def write(self, text, name="design-system.md"):
        p = self.tmp / name
        p.write_text(text, encoding="utf-8")
        return str(p)

    def test_REQ_W3_038_the_design_spec_ratio(self):
        code, env = self.run_tool("--file", str(SEED))
        self.assertEqual(code, 0, env)
        r = next(x for x in env["result"]["rows"] if x["text"] == "--color-text-primary"
                 and x["background"] == "--color-background" and x["scheme"] == "light")
        self.assertAlmostEqual(r["ratio"], 12.96, delta=0.01)
        self.assertEqual(env["result"]["below"], [])

    def test_REQ_W3_038_a_7_to_1_pair_passes_aa_and_aaa(self):
        f = self.write(palette([("--color-text", "#595959", "#595959"), ("--color-bg", "#ffffff", "#ffffff")],
                               [("--color-text", "--color-bg", "AA normal")]))
        code, env = self.run_tool("--file", f)
        self.assertEqual(code, 0, env)
        row = env["result"]["rows"][0]
        self.assertGreaterEqual(row["ratio"], 7.0)
        self.assertEqual(row["passed"], ["AA", "AAA"])

    def test_REQ_W3_038_a_pair_declared_aaa_at_5_8_is_reported(self):
        code, env = self.run_tool("--file", str(SEED))
        text = self.write(SEED.read_text(encoding="utf-8").replace(
            "| `--color-accent` | `--color-surface` | AA normal |", "| `--color-accent` | `--color-surface` | AAA |"))
        code, env = self.run_tool("--file", text)
        self.assertEqual(code, 0, env)  # advisory: reported, not refused
        below = [(b["text"], b["scheme"], b["ratio"]) for b in env["result"]["below"]]
        self.assertEqual(below, [("--color-accent", "light", 5.8)])

    def test_REQ_W3_038_an_unparseable_token_is_named_exit_1(self):
        f = self.write(palette([("--color-x", "foo", "foo"), ("--color-bg", "#ffffff", "#ffffff")],
                               [("--color-x", "--color-bg", "AA")]))
        code, env = self.run_tool("--file", f)
        self.assertEqual(code, 1)
        self.assertIn("--color-x", env["errors"][0]["message"])

    def test_delta_values_are_applied(self):
        d = self.tmp / "docs/spec/changes/sample-change"
        d.mkdir(parents=True)
        (self.tmp / "docs/spec/design-system.md").write_text(SEED.read_text(encoding="utf-8"), encoding="utf-8")
        (d / "design-delta.md").write_text(
            "## Modified\n\n| Token | Scheme | Base value | New value |\n|---|---|---|---|\n"
            "| `--color-accent` | light | `#8f5312` | `#c08a4a` |\n", encoding="utf-8")
        code, env = self.run_tool("--delta", "sample-change")
        self.assertEqual(code, 0, env)
        self.assertIn(("--color-accent", "light"), [(b["text"], b["scheme"]) for b in env["result"]["below"]])

    def test_missing_file_is_exit_4(self):
        code, env = self.run_tool()
        self.assertEqual(code, 4)


if __name__ == "__main__":
    unittest.main()
