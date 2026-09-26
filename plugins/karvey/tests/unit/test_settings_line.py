"""``settings invalid ({key} …)`` in the session hook and the dashboard (architecture §1.22, C-22).

@req REQ-W3-059
"""
import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import _path
from _state import make_project

BASE = {"git_platform": "github", "repos": ["r"], "spec_repo": "r",
        "branch_flow": {"feature_prefix": "feature/", "integration": "main", "production": "main"},
        "notifications": {"channel": "none"}}


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, str(_path.SCRIPTS_DIR / file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CONFIG = load("karvey_config_sl", "karvey-config.py")
CONTEXT = load("karvey_context_sl", "karvey-context.py")


class SettingsLine(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-settings-"))

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def put(self, **extra):
        make_project(self.tmp, project=dict(BASE, **extra))

    def test_REQ_W3_059_a_status_map_under_an_unknown_key_names_the_key(self):
        self.put(management={"tool": "jira", "location": "SAMPLE", "status_map": {"todo": "To Do"}})
        line = CONFIG.settings_line(self.tmp)
        self.assertIn("settings invalid (management.statuses missing)", line)

    def test_REQ_W3_059_a_documented_alias_passes_shown_normalised(self):
        self.put(management={"tool": "none"})
        invalid, normalised = CONFIG.settings_problems(self.tmp)
        self.assertEqual(invalid, [])
        self.assertTrue(any("'markdown'" in n for n in normalised), normalised)
        self.assertIsNone(CONFIG.settings_line(self.tmp))

    def test_dashboard_overview_prints_the_line(self):
        self.put(management={"tool": "jira", "location": "SAMPLE", "status_map": {"todo": "To Do"}})
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            CONTEXT.main(["--root", str(self.tmp), "--section", "overview", "--json"])
        env = json.loads(out.getvalue())
        self.assertIn("management.statuses missing", env["result"]["overview"]["settings"]["invalid"])
        self.assertIn("settings.valid", [w["code"] for w in env["warnings"]])

    def test_an_absent_block_is_not_invalid(self):
        self.put()
        self.assertEqual(CONFIG.settings_problems(self.tmp), ([], []))


if __name__ == "__main__":
    unittest.main()
