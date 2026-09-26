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


class SentLog(unittest.TestCase):
    """@req REQ-W3-027 — no duplicate qa, deploy or "your turn" notification."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-sent-"))
        (self.tmp / "docs/spec/changes/sample-change").mkdir(parents=True)
        (self.tmp / "docs/spec/project.json").write_text(json.dumps(PROJECT), encoding="utf-8")
        self.log = self.tmp / "docs/spec/changes/sample-change/notifications.jsonl"

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def sent(self, *extra):
        code, out = run("notify-sent", "sample-change", "--root", str(self.tmp), "--record", "--json", *extra)
        self.assertEqual(code, 0, out)
        return json.loads(out)["result"]

    def test_REQ_W3_027_three_qa_runs_same_verdict_one_new(self):
        got = [self.sent("--event", "qa", "--item", "qa", "--state", "concerns", "--run-id", "run-%d" % i)["status"]
               for i in (1, 2, 3)]
        self.assertEqual(got, ["new", "sent", "sent"])
        self.assertEqual(self.sent("--event", "qa", "--item", "qa", "--state", "pass")["status"], "new")

    def test_REQ_W3_027_deploy_retry_same_version_env_is_sent_with_the_retry_run_id(self):
        a = self.sent("--event", "deploy", "--version", "4.1.0", "--env", "prod", "--run-id", "pipeline-10")
        b = self.sent("--event", "deploy", "--version", "4.1.0", "--env", "prod", "--run-id", "pipeline-11")
        self.assertEqual((a["status"], b["status"], b["run_id"]), ("new", "sent", "pipeline-11"))
        self.assertTrue(b["at"])
        self.assertEqual(self.sent("--event", "deploy", "--version", "4.1.0", "--env", "dev")["status"], "new")

    def test_qa_every_run_notifies_every_run(self):
        p = dict(PROJECT)
        p["notifications"] = dict(PROJECT["notifications"], qa_every_run=True)
        (self.tmp / "docs/spec/project.json").write_text(json.dumps(p), encoding="utf-8")
        got = [self.sent("--event", "qa", "--item", "qa", "--state", "pass")["status"] for _ in range(3)]
        self.assertEqual(got, ["new", "new", "new"])

    def test_your_turn_once_per_state(self):
        args = ("--event", "awaiting_human", "--item", "E1.F2.T3")
        self.assertEqual(self.sent(*(args + ("--state", "awaiting")))["status"], "new")
        self.assertEqual(self.sent(*(args + ("--state", "awaiting")))["status"], "sent")
        self.assertEqual(self.sent(*(args + ("--state", "done")))["status"], "new")

    def test_the_log_holds_hashes_and_no_destination(self):
        self.sent("--event", "qa", "--item", "qa", "--state", "pass", "--run-id", "run-1")
        text = self.log.read_text(encoding="utf-8")
        self.assertNotIn("#team-sample", text)
        self.assertNotIn("approver@example.org", text)
        self.assertNotIn("pass", text.replace("run-1", ""))
        rec = json.loads(text.splitlines()[0])
        self.assertRegex(rec["key"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
