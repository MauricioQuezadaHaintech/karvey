"""karvey-health-score.py: deterministic 0-10 health score (architecture §1.14 C-17 of wave2-structural).

@req REQ-W2-072
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

import _path

HS = str(_path.SCRIPTS_DIR / "karvey-health-score.py")
FULL = {"types": {"errors": 2}, "lint": {"errors_per_kloc": 1, "warnings_per_kloc": 10},
        "tests": {"passed": 90, "failed": 10, "coverage_pct": 50}, "deadcode": {"items": 5}}


def run(inputs, tz=None):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(inputs, fh)
    env = dict(os.environ)
    env.pop("KARVEY_TZ", None)
    if tz is not None:
        env["KARVEY_TZ"] = tz
    try:
        p = subprocess.run([sys.executable, HS, "--inputs", fh.name, "--json"], capture_output=True, text=True,
                           timeout=30, env=env)
    finally:
        os.unlink(fh.name)
    return p.returncode, json.loads(p.stdout), p.stderr


class Score(unittest.TestCase):
    def test_REQ_W2_072_same_input_twice_identical(self):
        a, b = run(FULL)[1]["result"], run(FULL)[1]["result"]
        a.pop("at"), b.pop("at")
        self.assertEqual(a, b)
        # types 9, lint 8, tests 0.8*9 + 0.2*5 = 8.2, deadcode 9 → (9*.3 + 8.2*.3 + 8*.25 + 9*.15) / 1 = 8.51 → 8.5
        self.assertEqual(a["score"], 8.5)
        self.assertEqual(a["band"], "healthy")

    def test_REQ_W2_072_invalid_tz_prints_fallback(self):
        code, env, err = run(FULL, tz="Mars/Olympus")
        self.assertEqual(code, 0)
        self.assertIn("fallback zone:", err)
        self.assertEqual(env["warnings"][0]["code"], "health.tz")

    def test_missing_tool_weight_redistributed(self):
        inp = dict(FULL)
        inp.pop("deadcode")
        r = run(inp)[1]["result"]
        self.assertEqual(r["excluded"], ["deadcode"])
        self.assertAlmostEqual(sum(r["weights"].values()), 1.0, places=3)
        self.assertEqual(r["weights"]["types"], round(0.30 / 0.85, 4))

    def test_named_subscores(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("hs", HS)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        self.assertEqual(m.score_types({"errors": 0}), 10.0)
        self.assertEqual(m.score_deadcode({"items": 100}), 0.0)
        self.assertEqual(m.score_coverage(71), 7.1)


if __name__ == "__main__":
    unittest.main()
