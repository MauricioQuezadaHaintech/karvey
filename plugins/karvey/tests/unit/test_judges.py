"""Judges: closed inputs (architecture §1.7 of wave2-structural).

@req REQ-W2-022 REQ-W2-023 REQ-W2-031 REQ-W2-032
"""
import json
import unittest

import _path  # noqa: F401
import _gitrepo as g
from _state import make_project
from karvey_lib import judges as jd

g.isolate_git()
T0 = "2026-09-25T10:00:00-03:00"


def spec(lane="standard", **over):
    s = {"change_id": "feat-a", "phase": "architecture", "lane": lane, "goal": "the goal",
         "phase_history": [{"phase": "init", "entered_at": T0}], "approvals": {}}
    s.update(over)
    return s


class Inputs(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path
        self.put(spec())

    def tearDown(self):
        self.t.cleanup()

    def put(self, data, project=None):
        f = make_project(self.root, spec=data, project=project)
        for name in ("requirements.md", "architecture.md", "prd.md", "spec-delta.md"):
            (f.parent / name).write_text("# %s\n" % name)
        (f.parent / "qa").mkdir(exist_ok=True)
        (f.parent / "qa" / "REVISION_PR_1.md").write_text("# review\n")

    def test_REQ_W2_023_architecture_closed_inputs(self):
        r = jd.build_inputs(self.root, "feat-a", "architecture", project={})
        self.assertEqual(r["inputs"], ["docs/spec/changes/feat-a/architecture.md",
                                       "docs/spec/changes/feat-a/requirements.md"])
        self.assertEqual(r["goal"], "the goal")
        self.assertTrue(r["rubric"].endswith("rules/judges/architecture.md"))
        self.assertEqual(r["lenses"], ["security", "methods"])  # standard: 2 lenses

    def test_REQ_W2_023_extra_argument_dropped_and_logged(self):
        r = jd.build_inputs(self.root, "feat-a", "architecture", extras=["session-transcript.jsonl"], project={})
        self.assertEqual(r["dropped"], ["dropped: session-transcript.jsonl (not a phase input)"])
        self.assertNotIn("session-transcript.jsonl", r["inputs"])

    def test_REQ_W2_031_patch_has_no_judges(self):
        self.put(spec(lane="patch"))
        r = jd.build_inputs(self.root, "feat-a", "qa", project={})
        self.assertEqual((r["lenses"], r["status"]), ([], "judges: none for lane patch"))

    def test_REQ_W2_031_feature_ui_three_and_override(self):
        self.put(spec(lane="feature-ui"))
        self.assertEqual(len(jd.build_inputs(self.root, "feat-a", "architecture", project={})["lenses"]), 3)
        r = jd.build_inputs(self.root, "feat-a", "architecture", project={"judges": {"per_lane": {"feature-ui": 1}}})
        self.assertEqual(r["lenses"], ["security"])

    def test_REQ_W2_032_qa_always_includes_the_fiscal(self):
        r = jd.build_inputs(self.root, "feat-a", "qa", project={"judges": {"per_lane": {"standard": 1}}},
                            diff_path="/tmp/x.diff")
        self.assertEqual(r["lenses"][0], "fiscal")
        self.assertIn("docs/spec/changes/feat-a/qa/REVISION_PR_1.md", r["inputs"])
        self.assertIn("/tmp/x.diff", r["inputs"])

    def test_REQ_W2_022_disabled_and_not_judged(self):
        r = jd.build_inputs(self.root, "feat-a", "architecture", project={"judges": {"enabled": False}})
        self.assertEqual(r["status"], "judges: disabled by project setting")
        r = jd.build_inputs(self.root, "feat-a", "architecture", project={"judges": {"phases": ["qa"]}})
        self.assertIn("not in judges.phases", r["status"])
        r = jd.build_inputs(self.root, "feat-a", "tasks", project={"judges": {"phases": ["tasks"]}})
        self.assertIn("no rubric rules/judges/tasks.md: no lens can run", r["notes"])
        self.assertEqual(r["lenses"], [])

    def test_budget_reported_ignored(self):
        r = jd.build_inputs(self.root, "feat-a", "architecture", project={"judges": {"budget": 3}})
        self.assertIn("judges.budget: ignored (measure only, D-30)", r["notes"])

    def test_cli_json(self):
        import contextlib, io, importlib.util
        spec_ = importlib.util.spec_from_file_location("kj", str(_path.SCRIPTS_DIR / "karvey-judges.py"))
        m = importlib.util.module_from_spec(spec_)
        spec_.loader.exec_module(m)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = m.main(["inputs", "feat-a", "architecture", "--root", str(self.root), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["result"]["lenses"], ["security", "methods"])


if __name__ == "__main__":
    unittest.main()
