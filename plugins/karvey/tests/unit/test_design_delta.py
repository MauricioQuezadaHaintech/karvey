"""The design system and a change's design delta (architecture §1.18, C-18).

@req REQ-W3-035 REQ-W3-036 REQ-W3-076
"""
import unittest

import _path
from karvey_lib import designsys as ds

FIX = _path.UNIT_DIR / "fixtures" / "design"
SPEC = _path.REPO_ROOT / "docs/spec/changes/wave3-optimization/design-spec.md"


def seed():
    return ds.parse((FIX / "design-system.md").read_text(encoding="utf-8"))


def byte(rgb):
    return tuple(int(round(c * 255)) for c in rgb)


class Parser(unittest.TestCase):
    """@req REQ-W3-035"""

    def test_REQ_W3_035_the_seed_parses_into_light_dark_tokens_pairs_and_components(self):
        s = seed()
        t = s["tokens"]["--color-background"]
        self.assertEqual((t["light"], t["dark"], t["changed_by"]), ("#f3eee3", "#10161c", "sample-first-ui"))
        self.assertEqual(ds.resolved(s["tokens"], "--color-border-strong", "dark"), "#a8b1ba")
        self.assertEqual(ds.resolved(s["tokens"], "--color-semantic-warning", "light"), "#8f5312")
        self.assertEqual(ds.resolved(s["tokens"], "--space-4", "dark"), "16px")  # "=" → the light value
        self.assertEqual(s["tokens"]["--duration-fast"]["light"], "100ms")
        self.assertEqual(len(s["pairs"]), 13)
        self.assertEqual(s["pairs"][0]["level"], ("AAA", "normal"))
        self.assertEqual(s["pairs"][-1]["level"], ("UI", "normal"))
        self.assertEqual([c["name"] for c in s["components"]], ["Card", "Status pill"])

    @unittest.skipUnless(SPEC.is_file(), "not this repository")
    def test_a_design_spec_colour_table_parses_too(self):
        t = ds.parse(SPEC.read_text(encoding="utf-8"))["tokens"]
        self.assertEqual(t["--color-accent"]["light"], "#8f5312")
        self.assertEqual(t["--color-accent"]["dark"], "#e2ab5f")

    def test_undeclared_level_is_aa_normal(self):
        self.assertEqual(ds.parse_level(""), ("AA", "normal"))
        self.assertEqual(ds.parse_level("AAA large"), ("AAA", "large"))


class Colour(unittest.TestCase):
    """@req REQ-W3-035 REQ-W3-038"""

    def test_oklch_converts_within_one_step_of_the_hex(self):
        got = byte(ds.parse_color("oklch(50.2% 0.108 61)"))
        want = (0x8f, 0x53, 0x12)
        self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(got, want)), (got, want))

    def test_hex_short_and_rgb(self):
        self.assertEqual(byte(ds.parse_color("#fff")), (255, 255, 255))
        self.assertEqual(byte(ds.parse_color("rgb(29, 40, 49)")), (29, 40, 49))
        self.assertEqual(byte(ds.parse_color("rgb(100% 0% 0%)")), (255, 0, 0))

    def test_unknown_colour_syntax_is_a_named_error(self):
        with self.assertRaises(ds.DesignError) as cm:
            ds.parse_color("hsl(10 20% 30%)", "--color-x")
        self.assertEqual(cm.exception.token, "--color-x")
        self.assertIn("--color-x", str(cm.exception))


class Project(unittest.TestCase):
    """A project with the seed design system and one change (``sample-change``) whose design-spec is the seed."""

    def setUp(self):
        import shutil
        import tempfile
        from pathlib import Path
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-design-"))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.system = self.tmp / "docs/spec/design-system.md"
        self.cdir = self.tmp / "docs/spec/changes/sample-change"
        self.cdir.mkdir(parents=True)
        (self.cdir / "spec.json").write_text('{"change_id": "sample-change", "phase": "design_graphic"}\n')
        self.seed = (FIX / "design-system.md").read_text(encoding="utf-8")
        self.system.write_text(self.seed, encoding="utf-8")
        (self.cdir / "design-spec.md").write_text(self.seed, encoding="utf-8")

    def delta(self, text):
        (self.cdir / "design-delta.md").write_text(text, encoding="utf-8")

    def tool(self, *argv):
        import json
        import subprocess
        import sys
        cp = subprocess.run([sys.executable, str(_path.SCRIPTS_DIR / "karvey-design.py")] + list(argv) +
                            ["--root", str(self.tmp), "--json"], capture_output=True, text=True, timeout=60)
        return cp.returncode, json.loads(cp.stdout)


class Diff(Project):
    """@req REQ-W3-036"""

    def test_REQ_W3_036_one_new_component_is_the_only_delta(self):
        spec = self.seed.replace("| Status pill | sample-first-ui |", "| Status pill | sample-first-ui |\n| Tag | — |")
        (self.cdir / "design-spec.md").write_text(spec, encoding="utf-8")
        self.delta("## Components\n\n| Component | Action |\n|---|---|\n| Tag | added |\n")
        code, env = self.tool("diff", "sample-change")
        r = env["result"]
        self.assertEqual(code, 0, env)
        self.assertEqual((r["added"], r["modified"], r["components"], r["undeclared"]), ([], [], ["Tag"], []))
        self.assertEqual(r["declared"]["components"], ["Tag"])

    def test_REQ_W3_036_an_undeclared_primary_change_is_reported(self):
        spec = self.seed.replace("| `--color-primary` | `#2b4256` |", "| `--color-primary` | `#1f4f7a` |")
        (self.cdir / "design-spec.md").write_text(spec, encoding="utf-8")
        self.delta("empty\n")
        code, env = self.tool("diff", "sample-change")
        self.assertEqual(code, 0, env)  # warn in 4.1
        self.assertEqual(env["result"]["undeclared"], ["undeclared modification: --color-primary"])
        self.assertEqual(env["result"]["modified"][0]["base"], "#2b4256")
        self.assertIn("undeclared modification: --color-primary", [w["message"] for w in env["warnings"]])

    def test_REQ_W3_036_no_change_is_empty(self):
        self.delta("empty\n")
        code, env = self.tool("diff", "sample-change")
        self.assertTrue(env["result"]["empty"])
        self.assertEqual(env["warnings"], [])

    def test_without_a_design_system_everything_is_an_addition(self):
        self.system.unlink()
        self.delta("empty\n")
        code, env = self.tool("diff", "sample-change")
        self.assertFalse(env["result"]["system"])
        self.assertIn("undeclared addition: --color-primary", env["result"]["undeclared"])


class Apply(Project):
    """@req REQ-W3-076"""

    MOD = ("## Modified\n\n| Token | Scheme | Base value | New value |\n|---|---|---|---|\n"
           "| `--color-primary` | light | `#2b4256` | `%s` |\n")

    def test_REQ_W3_076_untouched_token_and_addition_written_without_question(self):
        self.delta(self.MOD % "#1f4f7a" + "\n## Added\n\n| Token | Scheme | Base value | New value |\n|---|---|---|---|\n"
                   "| `--color-info` | both | — | `#1c5d96` |\n\n## Components\n\n| Component | Action |\n|---|---|\n"
                   "| Tag | added |\n")
        code, env = self.tool("apply", "sample-change")
        self.assertEqual(code, 0, env)
        s = ds.parse(self.system.read_text(encoding="utf-8"))
        self.assertEqual((s["tokens"]["--color-primary"]["light"], s["tokens"]["--color-primary"]["changed_by"]),
                         ("#1f4f7a", "sample-change"))
        self.assertEqual(s["tokens"]["--color-primary"]["dark"], "#a3bfd8")
        self.assertEqual(s["tokens"]["--color-info"]["dark"], "#1c5d96")
        self.assertIn("Tag", [c["name"] for c in s["components"]])
        code, env = self.tool("apply", "sample-change")  # idempotent
        self.assertEqual((code, env["result"]["applied"]), (0, []))

    def test_REQ_W3_076_second_change_on_the_same_token_stops_with_both_values(self):
        self.delta(self.MOD % "#1f4f7a")
        self.assertEqual(self.tool("apply", "sample-change")[0], 0)  # the first change, archived
        other = self.tmp / "docs/spec/changes/second-change"
        other.mkdir()
        (other / "spec.json").write_text('{"change_id": "second-change", "phase": "archived"}\n')
        (other / "design-delta.md").write_text(self.MOD % "#335577", encoding="utf-8")
        before = self.system.read_bytes()
        code, env = self.tool("apply", "second-change")
        self.assertEqual(code, 3, env)
        msg = env["errors"][0]["message"]
        for part in ("--color-primary", "#1f4f7a", "#2b4256", "#335577", "sample-change"):
            self.assertIn(part, msg)
        self.assertEqual(self.system.read_bytes(), before)
        code, env = self.tool("apply", "second-change", "--keep=--color-primary=new")
        self.assertEqual(code, 0, env)
        self.assertEqual(ds.parse(self.system.read_text())["tokens"]["--color-primary"]["light"], "#335577")

    def test_REQ_W3_076_dry_run_writes_nothing(self):
        self.delta(self.MOD % "#1f4f7a")
        before = self.system.read_bytes()
        code, env = self.tool("apply", "sample-change", "--dry-run")
        self.assertEqual(code, 0, env)
        self.assertEqual(env["result"]["applied"], ["modified --color-primary (light)"])
        self.assertEqual(self.system.read_bytes(), before)

    def test_the_first_ui_change_seeds_the_design_system(self):
        self.system.unlink()
        self.delta("## Added\n\n| Token | Scheme | Base value | New value |\n|---|---|---|---|\n"
                   "| `--color-primary` | both | — | `#2b4256` |\n| `--space-1` | both | — | `4px` |\n")
        code, env = self.tool("apply", "sample-change")
        self.assertEqual(code, 0, env)
        s = ds.parse(self.system.read_text(encoding="utf-8"))
        self.assertEqual(sorted(s["tokens"]), ["--color-primary", "--space-1"])
        self.assertIn("## Colour", self.system.read_text())


if __name__ == "__main__":
    unittest.main()
