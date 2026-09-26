"""``karvey-trace.py --wbs`` (architecture §1.19, C-19): one work breakdown per change.

@req REQ-W3-043 REQ-W3-040 REQ-W3-041
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

_SPEC = importlib.util.spec_from_file_location("karvey_trace_wbs", str(_path.SCRIPTS_DIR / "karvey-trace.py"))
trace = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(trace)
OWN = _path.REPO_ROOT / "docs/spec/changes/wave3-optimization/tasks.md"

GOOD = """# Tasks: sample-change

## Feature E1.F1: Sign-in

### E1.F1.T1 [Backend] Sign-in endpoint
**Requirements:** REQ-SC-001

### E1.F1.T2 [Test] Sign-in tests — _Depends: E1.F1.T1_
**Requirements:** REQ-SC-001, REQ-SC-002 (MODIFIES REQ-OLD-004)

## Feature E1.F2: Reports

### E1.F2.T1 [Frontend] Report screen
**Requirements:** REQ-SC-003 (MODIFIES REQ-OLD-004)

## Epic item E1.DEPLOY

### E1.DEPLOY.T1 [human] The production OK
**Requirements:** REQ-SC-001
"""


class Wbs(unittest.TestCase):
    def test_a_clean_plan_has_no_issue(self):
        r = trace.wbs(GOOD)
        self.assertEqual((r["tasks"], r["features"], r["epic_items"], r["issues"]),
                         (4, ["E1.F1", "E1.F2"], ["E1.DEPLOY"], []))

    def test_REQ_W3_043_a_task_outside_any_feature_is_reported_with_its_id(self):
        text = GOOD.replace("# Tasks: sample-change\n", "# Tasks: sample-change\n\n### E1.F9.T1 [Backend] Stray\n")
        self.assertIn("E1.F9.T1: outside any Feature (line 3)", trace.wbs(text)["issues"])

    def test_a_task_under_the_wrong_feature_is_reported(self):
        text = GOOD.replace("### E1.F2.T1 [Frontend]", "### E1.F3.T1 [Frontend]")
        self.assertEqual(trace.wbs(text)["issues"][0][:44], "E1.F3.T1: under E1.F2 but its id names E1.F3")

    def test_REQ_W3_043_a_requirement_in_two_features_needs_split(self):
        text = GOOD.replace("**Requirements:** REQ-SC-003", "**Requirements:** REQ-SC-002, REQ-SC-003")
        self.assertEqual(trace.wbs(text)["issues"],
                         ["REQ-SC-002: tasks in E1.F1 and E1.F2 without a Split: line in E1.F2"])
        with_split = text.replace("## Feature E1.F2: Reports\n",
                                  "## Feature E1.F2: Reports\n\n**Split:** REQ-SC-002 — the export half lives here.\n")
        self.assertEqual(trace.wbs(with_split)["issues"], [])

    def test_modified_ids_and_epic_items_do_not_count_as_a_split(self):
        self.assertEqual(trace.wbs(GOOD)["issues"], [])  # REQ-OLD-004 twice, REQ-SC-001 also under E1.DEPLOY

    @unittest.skipUnless(OWN.is_file(), "not this repository")
    def test_this_changes_own_plan_has_no_issue(self):
        r = trace.wbs(OWN.read_text(encoding="utf-8"))
        self.assertEqual(r["issues"], [])
        self.assertEqual(r["epic_items"], ["E1.DEPLOY"])


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-wbs-"))
        d = self.tmp / "docs/spec/changes/sample-change"
        d.mkdir(parents=True)
        (d / "spec.json").write_text('{"change_id": "sample-change", "phase": "tasks"}\n')
        (d / "tasks.md").write_text(GOOD.replace("# Tasks: sample-change\n",
                                                 "# Tasks: sample-change\n\n### E1.F9.T1 [Backend] Stray\n"))

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def test_warn_mode_reports_and_exits_0(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = trace.main(["sample-change", "--wbs", "--root", str(self.tmp), "--json"])
        env = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(env["result"]["mode"], "warn")
        self.assertIn("E1.F9.T1", env["warnings"][0]["message"])


LEGACY_PLAN = """# Plan: sample-change

## Tasks

### Feature E1.F1: Requirements
- [x] E1.F1.T1 [Backend] Write requirements

### Feature E1.F2: Sign-in
- [ ] E1.F2.T1 [Backend] Sign-in endpoint

- [ ] QA Review sample-change (feature → main)
- [ ] [Deploy] sample-change@1.2.0

### Epic item E1.DEPLOY
- [ ] E1.DEPLOY.T1 [human] The production OK
"""


class Legacy(unittest.TestCase):
    """@req REQ-W3-040 REQ-W3-041 — the tracker reconciliation reports, never rewrites."""

    def test_REQ_W3_040_a_phase_feature_is_legacy_shape_and_a_root_qa_item_is_outside(self):
        out = trace.wbs_plan(LEGACY_PLAN)
        self.assertEqual(len(out), 3, out)
        self.assertTrue(out[0].startswith("legacy shape: Feature E1.F1 'Requirements' is a pipeline phase"))
        self.assertTrue(out[1].startswith("outside the hierarchy: 'QA Review sample-change"))
        self.assertTrue(out[2].startswith("outside the hierarchy: '[Deploy] sample-change@1.2.0'"))

    def test_the_file_is_unchanged_through_the_cli(self):
        tmp = Path(tempfile.mkdtemp(prefix="karvey-wbs-legacy-"))
        self.addCleanup(shutil.rmtree, str(tmp), True)
        d = tmp / "docs/spec/changes/sample-change"
        d.mkdir(parents=True)
        (d / "spec.json").write_text('{"change_id": "sample-change", "phase": "impl"}\n')
        (d / "tasks.md").write_text(GOOD)
        (d / "PLAN.md").write_text(LEGACY_PLAN)
        before = (d / "PLAN.md").read_bytes()
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = trace.main(["sample-change", "--wbs", "--root", str(tmp), "--json"])
        env = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(len(env["result"]["tracker"]), 3)
        self.assertEqual((d / "PLAN.md").read_bytes(), before)

    @unittest.skipUnless(OWN.is_file(), "not this repository")
    def test_this_changes_own_plan_is_in_the_new_shape(self):
        self.assertEqual(trace.wbs_plan((OWN.parent / "PLAN.md").read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
