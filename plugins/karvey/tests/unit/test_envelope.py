import io
import json
import unittest

import _path  # noqa: F401
import karvey_lib as kl


class ExitCodes(unittest.TestCase):
    def test_values(self):
        self.assertEqual((kl.EXIT_OK, kl.EXIT_FINDINGS, kl.EXIT_USAGE, kl.EXIT_REFUSED,
                          kl.EXIT_NOT_FOUND, kl.EXIT_INTERNAL), (0, 1, 2, 3, 4, 5))
        self.assertEqual(sorted(kl.EXIT_CODES), [0, 1, 2, 3, 4, 5])
        self.assertEqual((kl.HOOK_ALLOW, kl.HOOK_BLOCK), (0, 2))


class Envelope(unittest.TestCase):
    def test_keys_and_ok(self):
        env = kl.envelope("karvey-state", kl.EXIT_OK, {"a": 1})
        self.assertEqual(tuple(env), kl.ENVELOPE_KEYS)
        self.assertTrue(env["ok"])
        self.assertEqual(env["version"], kl.__version__)
        self.assertEqual(env["result"], {"a": 1})
        bad = kl.envelope("t", kl.EXIT_FINDINGS, errors=[kl.issue("E1", "boom", file="f", path="$.phase")])
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["exit"], 1)
        self.assertEqual(tuple(bad["errors"][0]), kl.ISSUE_KEYS)

    def test_unknown_exit_refused(self):
        with self.assertRaises(ValueError):
            kl.envelope("t", 9)
        with self.assertRaises(ValueError):
            kl.issue("x", "m", severity="info")

    def test_emit_json(self):
        buf = io.StringIO()
        rc = kl.emit(kl.envelope("t", kl.EXIT_REFUSED), True, stream=buf)
        self.assertEqual(rc, 3)
        self.assertEqual(json.loads(buf.getvalue())["exit"], 3)

    def test_version_from_plugin_json(self):
        with open(_path.PLUGIN_ROOT / ".claude-plugin" / "plugin.json") as fh:
            self.assertEqual(kl.__version__, json.load(fh)["version"])


class Defaults(unittest.TestCase):
    def test_d06_d07_values(self):
        d = kl.defaults()
        self.assertEqual(d["rotation_hours"], 8)            # D-06
        self.assertEqual(d["plan_marker_ttl_min"], 120)      # D-07
        self.assertEqual(d["stall_days"], 7)                 # D-07
        self.assertEqual(d["calibration"], {"threshold_pct": 30, "window": 3})  # D-07
        self.assertEqual(d["session"], {"board_rows_max": 40, "handoff_bytes_max": 6144})
        self.assertEqual(d["plan_marker_ttl_bounds"], {"minimum": 5, "maximum": 1440})

    def test_copy_is_isolated(self):
        d = kl.defaults()
        d["rotation_hours"] = 99
        self.assertEqual(kl.defaults()["rotation_hours"], 8)


if __name__ == "__main__":
    unittest.main()
