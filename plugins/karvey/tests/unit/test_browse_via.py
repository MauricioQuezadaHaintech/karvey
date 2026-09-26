"""``project.json:browse.via`` (architecture §1.22, C-22).

@req REQ-W3-054
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
from _state import make_project, state
from _config import run_json


def project(**browse):
    p = {"git_platform": "github", "repos": ["r"], "spec_repo": "r",
         "branch_flow": {"feature_prefix": "feature/", "integration": "main", "production": "main"}}
    if browse:
        p["browse"] = browse
    return p


class BrowseVia(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-browse-"))

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def resolve(self, **browse):
        make_project(self.tmp, project=project(**browse))
        return run_json("resolve", "browse", "--root", str(self.tmp))

    def test_REQ_W3_054_agent_name_is_valid(self):
        code, env = self.resolve(via="agent:qa-browser")
        self.assertEqual(code, 0, env)
        self.assertEqual((env["result"]["via"], env["result"]["agent"]), ("agent", "qa-browser"))

    def test_REQ_W3_054_empty_or_spaced_agent_refused(self):
        for bad in ("agent:", "agent:qa browser", "agent:$(x)"):
            code, env = self.resolve(via=bad)
            self.assertEqual(code, 3, bad)
            self.assertIn("browse.via", env["errors"][0]["message"])
            errs = [i for i in state.validate_data(project(via=bad), "project", True, "project.json")
                    if i["severity"] == "error"]
            self.assertTrue(errs, bad)

    def test_REQ_W3_054_none_is_not_evaluated(self):
        code, env = self.resolve(via="none")
        self.assertEqual(env["result"]["note"], "not evaluated (browse.via: none)")

    def test_default_is_local(self):
        code, env = self.resolve()
        self.assertEqual((code, env["result"]["via"], env["result"]["source"]), (0, "local", "default"))


if __name__ == "__main__":
    unittest.main()
