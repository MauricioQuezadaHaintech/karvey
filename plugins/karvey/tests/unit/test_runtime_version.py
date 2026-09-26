"""Loaded plugin version vs the clone's (architecture §1.22, C-22).

@req REQ-W3-058
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import _path
from karvey_lib import runtime as rt


class Version(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-runtime-"))
        self.cfg = self.tmp / "config"
        self.clone = self.tmp / "clone"
        (self.clone / ".claude-plugin").mkdir(parents=True)
        (self.clone / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "karvey", "version": "4.1.0"}))
        self.env = {"CLAUDE_CONFIG_DIR": str(self.cfg), "HOME": str(self.tmp / "home")}

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def record(self, data):
        p = self.cfg / "plugins/installed_plugins.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data))
        return p

    def test_REQ_W3_058_loaded_and_available_differ(self):
        p = self.record({"version": 2, "plugins": {"karvey@sample-market": [
            {"scope": "user", "version": "4.0.0", "lastUpdated": "2026-10-01T00:00:00Z"}]}})
        before = os.stat(str(p)).st_mtime_ns
        line = rt.report(self.clone, self.env)
        self.assertTrue(line.startswith("loaded 4.0.0, available 4.1.0"), line)
        self.assertEqual(os.stat(str(p)).st_mtime_ns, before)

    def test_the_older_record_shape_is_read(self):
        self.record({"plugins": {"karvey@sample-market": {"version": "4.1.0"}, "other@x": {"version": "9"}}})
        self.assertEqual(rt.report(self.clone, self.env), "loaded 4.1.0, available 4.1.0")

    def test_REQ_W3_058_no_record_is_unknown(self):
        self.assertEqual(rt.report(self.clone, self.env), "loaded version unknown, available 4.1.0")

    def test_default_config_dir_under_home(self):
        self.assertEqual(rt.config_dir({"HOME": "/h"}), Path("/h/.claude"))


if __name__ == "__main__":
    unittest.main()
