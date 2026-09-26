"""'Your turn' events and the sent-log (architecture §1.15, C-15).

@req REQ-W3-026 REQ-W3-027
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

_SPEC = importlib.util.spec_from_file_location("karvey_config_ev", str(_path.SCRIPTS_DIR / "karvey-config.py"))
cfg = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cfg)

PROJECT = {"notifications": {"channel": "slack", "target": "#team-sample", "events": ["qa", "deploy",
                                                                                     "approval_requested",
                                                                                     "awaiting_human", "blocked"]},
           "management": {"tool": "markdown"},
           "stakeholders": {"approver": {"role": "approver", "name": "Area lead",
                                         "destination": {"channel": "email", "target": "approver@example.org"}}}}


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = cfg.main(list(argv))
    return code, out.getvalue()


class Events(unittest.TestCase):
    """@req REQ-W3-026"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-events-"))
        (self.tmp / "docs/spec/changes/sample-change").mkdir(parents=True)
        (self.tmp / "docs/spec/project.json").write_text(json.dumps(PROJECT), encoding="utf-8")
        (self.tmp / "docs/spec/changes/sample-change/spec.json").write_text(
            json.dumps({"change_id": "sample-change", "phase": "architecture"}), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def event(self, *extra):
        code, out = run("resolve", "notifications", "--root", str(self.tmp), "--change", "sample-change",
                        "--json", *extra)
        self.assertEqual(code, 0, out)
        return json.loads(out)["result"]["event"]

    def test_REQ_W3_026_approval_requested_goes_to_the_approver(self):
        e = self.event("--event", "approval_requested", "--item", "how", "--run-id", "sample-change/architecture/1")
        self.assertEqual((e["source"], e["destination"]), ("stakeholder:approver",
                                                          {"channel": "email", "target": "approver@example.org"}))
        self.assertEqual((e["payload"]["change"], e["payload"]["item"]), ("sample-change", "how"))
        self.assertIn("how gate", e["payload"]["expected"])
        self.assertTrue(e["enabled"])
        self.assertTrue(e["payload"]["at"])
        self.assertEqual(e["payload"]["run_id"], "sample-change/architecture/1")

    def test_REQ_W3_026_awaiting_human_without_executor_goes_to_the_team(self):
        e = self.event("--event", "awaiting_human", "--item", "E1.F2.T3")
        self.assertEqual((e["source"], e["destination"]["target"], e["note"]), ("team", "#team-sample",
                                                                                "no executor declared"))
        self.assertEqual(e["payload"]["note"], "no executor declared")

    def test_REQ_W3_026_a_judge_blocked_event_carries_the_verdict(self):
        e = self.event("--event", "blocked", "--item", "architecture gate", "--verdict", "security: fail (2 High)")
        self.assertEqual(e["payload"]["verdict"], "security: fail (2 High)")

    def test_a_change_override_wins(self):
        spec = {"change_id": "sample-change", "phase": "architecture",
                "stakeholders": {"executor": {"role": "operator", "destination": {"channel": "slack",
                                                                                   "target": "#ops-sample"}}}}
        (self.tmp / "docs/spec/changes/sample-change/spec.json").write_text(json.dumps(spec), encoding="utf-8")
        e = self.event("--event", "awaiting_human", "--item", "E1.F2.T3")
        self.assertEqual((e["source"], e["destination"]["target"]), ("stakeholder:executor", "#ops-sample"))

    def test_unknown_event_is_usage(self):
        code, _ = run("resolve", "notifications", "--root", str(self.tmp), "--event", "nope", "--json")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
