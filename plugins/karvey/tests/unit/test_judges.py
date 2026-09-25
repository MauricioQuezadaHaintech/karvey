"""Judges: closed inputs (architecture §1.7 of wave2-structural).

@req REQ-W2-022 REQ-W2-023 REQ-W2-025 REQ-W2-026 REQ-W2-029 REQ-W2-030 REQ-W2-031 REQ-W2-032
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


def load_cli():
    import importlib.util
    spec_ = importlib.util.spec_from_file_location("kj2", str(_path.SCRIPTS_DIR / "karvey-judges.py"))
    m = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(m)
    return m


class Collect(unittest.TestCase):
    ARCH = "docs/spec/changes/feat-a/architecture.md"

    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path
        f = make_project(self.root, spec=spec(), project={"git_platform": "github", "repos": ["r"], "spec_repo": "r",
                                                          "branch_flow": {"integration": "main",
                                                                          "production": "main"},
                                                          "judges": {"budget": 5}})
        (f.parent / "architecture.md").write_text("# a\nline 2\nline 3\n")
        (f.parent / "requirements.md").write_text("# r\n")
        self.results = self.t.path / "results"
        self.results.mkdir()
        self.cli = load_cli()

    def tearDown(self):
        self.t.cleanup()

    def result(self, name, obj):
        (self.results / name).write_text(obj if isinstance(obj, str) else json.dumps(obj))

    def collect(self, *extra):
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.cli.main(["collect", "feat-a", "architecture", "--results", str(self.results),
                                  "--root", str(self.root), "--model", "model-a", "--intra-model", "--json"] + list(extra))
        return code, json.loads(out.getvalue())["result"]

    def findings(self):
        return (self.root / "docs/spec/changes/feat-a/findings.md").read_text()

    def test_REQ_W2_025_cite_past_eof_discarded(self):
        self.result("methods.json", {"lens": "methods", "verdict": "concerns", "findings": [
            {"severity": "High", "type_guess": "spec-gap", "text": "decision without options", "cite": self.ARCH + ":2"},
            {"severity": "Low", "type_guess": "bug", "text": "past the end", "cite": self.ARCH + ":99"},
            {"severity": "Low", "type_guess": "bug", "text": "not an input", "cite": "README.md:1"}]})
        code, r = self.collect()
        self.assertEqual(code, 0)
        self.assertEqual(r["discarded"], 2)
        self.assertEqual(r["runs"][0]["findings"], {"High": 1})

    def test_REQ_W2_026_two_rows_appended_open_with_origin(self):
        self.result("methods.json", {"lens": "methods", "verdict": "concerns", "findings": [
            {"severity": "High", "type_guess": "spec-gap", "text": "one", "cite": self.ARCH + ":1"},
            {"severity": "Medium", "type_guess": "emergent", "text": "two", "cite": self.ARCH + ":3"}]})
        code, r = self.collect()
        self.assertEqual(r["appended"], ["F-01", "F-02"])
        rows = [ln for ln in self.findings().splitlines() if ln.startswith("| F-")]
        self.assertEqual(len(rows), 2)
        for ln in rows:
            self.assertIn("| judge:methods |", ln)
            self.assertIn("| open |", ln)
        self.assertEqual(json.loads((self.results / "runs.json").read_text())[0]["lens"], "methods")

    def test_REQ_W2_026_invalid_json_is_not_run(self):
        self.result("security.json", "{not json")
        code, r = self.collect()
        self.assertEqual(r["runs"][0]["verdict"], "not-run")
        self.assertEqual(r["runs"][0]["reason"], "invalid output")

    def test_REQ_W2_026_sanitiser(self):
        self.assertEqual(jd.sanitise("a | b\nc"), "a \\| b c")
        s = jd.sanitise("fix it:\n```python\nos.remove(x)\n```\nthen done")
        self.assertNotIn("os.remove", s)
        self.assertIn("then done", s)
        self.assertNotIn("+x = 1", jd.sanitise("patch:\n@@ -1 +1 @@\n+x = 1\n-x = 0"))
        self.assertEqual(len(jd.sanitise("x" * 400)), 300)

    def test_REQ_W2_030_no_usage_is_estimated_and_budget_ignored(self):
        self.result("methods.json", {"lens": "methods", "verdict": "pass", "findings": []})
        code, r = self.collect()
        run = r["runs"][0]
        self.assertTrue(run["estimated"])
        self.assertGreaterEqual(run["usd"], 0)
        self.assertIn("judges.budget: ignored (measure only, D-30)", r["notes"])

    def test_REQ_W2_030_usage_is_measured(self):
        self.result("methods.json", {"lens": "methods", "verdict": "pass", "findings": [],
                                     "usage": {"tokens_in": 1000, "tokens_out": 100}})
        code, r = self.collect()
        self.assertFalse(r["runs"][0]["estimated"])
        self.assertEqual(r["runs"][0]["tokens_in"], 1000)

    def test_REQ_W2_029_model_and_intra_model_recorded(self):
        self.result("methods.json", {"lens": "methods", "verdict": "pass", "findings": []})
        code, r = self.collect()
        self.assertEqual((r["runs"][0]["model"], r["runs"][0]["intra_model"]), ("model-a", True))


if __name__ == "__main__":
    unittest.main()
