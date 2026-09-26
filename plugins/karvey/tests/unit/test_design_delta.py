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


if __name__ == "__main__":
    unittest.main()
