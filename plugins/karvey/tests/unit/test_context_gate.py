"""Dashboard lane column, lane skips and automatic approvals (architecture §1.6 of wave2-structural).

@req REQ-W2-021 REQ-W2-040
"""
import contextlib
import importlib.util
import io
import json
import unittest

import _path
import _gitrepo as g
from _state import make_project

g.isolate_git()
_SPEC = importlib.util.spec_from_file_location("karvey_context_g", str(_path.SCRIPTS_DIR / "karvey-context.py"))
ctxmod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ctxmod)
T0 = "2026-09-25T10:00:00-03:00"
NOW = "2026-09-25T12:00:00-03:00"


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = ctxmod.main(list(argv))
    return code, out.getvalue()


def standard_at_architecture():
    ok = {"generated": True, "approved": True, "by": "owner", "role": "human", "date": T0, "ref": "D-1"}
    return {"change_id": "feat-a", "phase": "architecture", "lane": "standard",
            "skipped": {"mockup": "lane:standard", "design_graphic": "lane:standard"},
            "phase_history": [{"phase": "init", "entered_at": T0, "exited_at": T0},
                              {"phase": "requirements", "entered_at": T0, "exited_at": T0},
                              {"phase": "architecture", "entered_at": T0}],
            "approvals": {"requirements": dict(ok, role="auto", by="agent"),
                          "architecture": {"generated": True, "approved": False}}}


class Dashboard(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        make_project(self.t.path, spec=standard_at_architecture())

    def tearDown(self):
        self.t.cleanup()

    def dash(self, *extra):
        code, out = run("--root", str(self.t.path), "--now", NOW, "--json", *extra)
        return json.loads(out)["result"]

    def test_REQ_W2_021_lane_column_and_lane_skips(self):
        r = self.dash()
        self.assertEqual(r["overview"]["active"][0]["lane"], "standard")
        rows = {x["key"]: x for x in r["approvals"]["feat-a"]["approvals"]}
        for k in ("mockup", "design_graphic"):
            self.assertEqual(rows[k]["state"], "skipped (lane)")
            self.assertEqual(rows[k]["text"], "skipped (lane standard)")
            self.assertNotIn(rows[k]["text"], ("pending", "awaiting approval"))
        self.assertEqual(rows["architecture"]["text"], "awaiting approval")
        self.assertEqual(r["approvals"]["feat-a"]["lane"], "standard")

    def test_REQ_W2_040_auto_approvals_apart(self):
        r = self.dash()
        rows = {x["key"]: x for x in r["approvals"]["feat-a"]["approvals"]}
        self.assertTrue(rows["requirements"]["auto"])
        self.assertTrue(rows["requirements"]["text"].startswith("auto-approved (-y)"))
        self.assertEqual(r["approvals"]["feat-a"]["auto"], ["requirements"])
        code, human = run("--root", str(self.t.path), "--now", NOW)
        self.assertIn("automatic approvals (role auto, not human): requirements", human)
        self.assertIn("lane standard", human)


if __name__ == "__main__":
    unittest.main()
