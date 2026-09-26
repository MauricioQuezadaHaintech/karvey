import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
from karvey_lib import audit


class Audit(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.d = Path(self.t.name) / "karvey"

    def tearDown(self):
        self.t.cleanup()

    def test_jsonl_and_mode_0600(self):
        audit.append(self.d, {"guard": "prod-gate", "decision": "block", "reason": "no approval",
                              "change": "wave1-hardening", "ref": None})
        audit.append(self.d, {"guard": "plan-gate", "decision": "allow"})
        p = self.d / "audit.log"
        lines = p.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        first = json.loads(lines[0])
        self.assertEqual((first["guard"], first["decision"], first["change"]), ("prod-gate", "block", "wave1-hardening"))
        self.assertIn("ts", first)
        self.assertRegex(first["ts"], r"[+-]\d{2}:\d{2}$")
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
        self.assertEqual([r["guard"] for r in audit.read(self.d)], ["prod-gate", "plan-gate"])

    def test_no_token_fields_no_bodies(self):
        rec = audit.append(self.d, {"guard": "prod-gate", "gh_token": "ghp_x", "Authorization": "Bearer y",
                                    "api_key": "k", "password": "p", "prompt": "full prompt text",
                                    "command": "gh pr merge 1", "prompt_excerpt": "a" * 200})
        raw = (self.d / "audit.log").read_text()
        for s in ("ghp_x", "Bearer", "\"k\"", "full prompt", "gh pr merge"):
            self.assertNotIn(s, raw)
        self.assertEqual(len(rec["prompt_excerpt"]), 80)

    def test_rotation_at_limit(self):
        audit.append(self.d, {"guard": "a", "reason": "x" * 300}, limit=200)
        audit.append(self.d, {"guard": "b"}, limit=200)  # first file >= 200 bytes → rotated
        self.assertTrue((self.d / "audit.log.1").exists())
        self.assertEqual([r["guard"] for r in audit.read(self.d)], ["b"])
        self.assertEqual([r["guard"] for r in audit.read(self.d, include_rotated=True)], ["a", "b"])
        audit.append(self.d, {"guard": "c", "reason": "y" * 300}, limit=200)  # b is small: c joins it
        audit.append(self.d, {"guard": "d"}, limit=200)  # b+c >= limit → rotated, a is dropped
        self.assertEqual([r["guard"] for r in audit.read(self.d, include_rotated=True)], ["b", "c", "d"])

    def test_default_limit_is_1mb(self):
        from karvey_lib import defaults
        self.assertEqual(defaults()["audit_rotate_bytes"], 1024 * 1024)

    def test_unwritable_never_raises(self):
        blocker = Path(self.t.name) / "file"
        blocker.write_text("x")
        self.assertIsNone(audit.append(blocker / "sub", {"guard": "x"}))

    def test_corrupt_line_skipped(self):
        self.d.mkdir(parents=True)
        (self.d / "audit.log").write_text('{"guard":"a"}\nnot json\n{"guard":"b"}\n')
        self.assertEqual([r["guard"] for r in audit.read(self.d)], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
