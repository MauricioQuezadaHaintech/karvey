"""BUG-163: the human approves a change once.

Reproduces the dialogue that triggered it: the agent summarised the release proposal in its own words (naming the
change, not the proposal id) and the human's «ok» was refused; after the first merge, a follow-up PR of the same
change (two files left out) asked the human for production approval again. With the fix the «ok» is recorded and
the follow-up commit is carried into the live approval without asking; it still stops when the approval expired or
the change was archived. Also: a session that runs an older cached Karvey than the installed one is told once, and
the scripts re-run from the installed version."""
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
import _path  # noqa: F401,E402
import _gitrepo as g  # noqa: E402
import _state  # noqa: E402
from karvey_lib import approval, karvey_hooks as kh, pluginver, project as pj  # noqa: E402

g.isolate_git()
CID = "integrations-adjust"
FLOW = {"branch_flow": {"feature_prefix": "feature/", "integration": "main", "production": "main"}}


def head(root):
    return pj.git(["rev-parse", "HEAD"], root)[1]


class ApproveOnce(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = g.init(Path(self.tmp.name).resolve() / "work" / "app")
        g.write(self.repo, "docs/spec/project.json", FLOW)
        g.write(self.repo, "docs/spec/changes/%s/spec.json" % CID, {"change_id": CID, "phase": "deploying"})
        g.commit_all(self.repo)
        env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(Path(self.tmp.name) / "state"),
                                           "CLAUDE_PROJECT_DIR": str(self.repo)})
        env.start()
        self.addCleanup(env.stop)
        self.tr = Path(self.tmp.name) / "transcript.jsonl"

    def say(self, text):
        with open(self.tr, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "assistant", "timestamp": approval.iso(approval.now_dt()),
                                 "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}) + "\n")

    def human(self, text):
        out, err = io.StringIO(), io.StringIO()
        payload = {"session_id": "s1", "transcript_path": str(self.tr), "cwd": str(self.repo),
                   "hook_event_name": "UserPromptSubmit", "prompt": text}
        self.assertEqual(kh.dispatch("prompt", json.dumps(payload), env=dict(os.environ), out=out, err=err), 0)
        return out.getvalue()

    def st(self, *argv):
        return _state.run_json(*argv, cwd=self.repo)

    def approve(self, sha="HEAD"):
        return self.st("approve", CID, "prod", "--by", "Owner", "--role", "human", "--ref", "D-52", "--sha", sha)

    def first_release(self):
        c, env = self.st("propose-release", "--change", CID, "--pr", "10177", "--sha", "HEAD", "--effect", "merge")
        self.assertEqual(c, 0, env)
        # the agent summarises the block in its own words: the change, not the proposal id
        self.say("Esta es la propuesta: %s · PR #10177 · merge a master. Responde ok." % CID)
        out = self.human("ok")
        self.assertIn("production approval recorded", out)
        c, env = self.approve()
        self.assertEqual(c, 0, env)
        return head(self.repo)

    def follow_up_commit(self):
        g.write(self.repo, "two-missing-files.txt", "x")
        g.commit_all(self.repo)
        return head(self.repo)

    def test_the_dialogue_asks_the_human_once(self):
        first = self.first_release()
        second = self.follow_up_commit()
        c, env = self.st("check-prod", CID, "--sha", second)
        self.assertNotEqual(c, 0)
        self.assertIn("without asking the human", env["result"]["reason"])
        c, env = self.approve(second)  # the agent carries it; no human message in between
        self.assertEqual(c, 0, env)
        self.assertTrue(env["result"]["followup"])
        c, env = self.st("check-prod", CID, "--sha", second)
        self.assertEqual(c, 0, env)
        fol = approval.read_ledger(self.repo, CID)[0]["prod"]["followups"]
        self.assertEqual([(f["from"], f["to"]) for f in fol], [(first, second)])

    def test_a_summary_that_names_nothing_is_still_refused(self):
        self.st("propose-release", "--change", CID, "--pr", "1", "--sha", "HEAD")
        self.say("Listo, ¿apruebas?")
        self.assertIn("NOT approved", self.human("ok"))

    def test_an_expired_approval_does_not_carry(self):
        self.first_release()
        second = self.follow_up_commit()
        ledger = approval.read_ledger(self.repo, CID)[0]
        prod = dict(ledger["prod"], expires_at=approval.iso(approval.now_dt() - approval.timedelta(minutes=1)))
        approval.record_prod(self.repo, CID, prod)
        c, env = self.approve(second)
        self.assertEqual(c, 3, env)

    def test_an_archived_change_does_not_carry(self):
        self.first_release()
        second = self.follow_up_commit()
        g.write(self.repo, "docs/spec/changes/%s/spec.json" % CID, {"change_id": CID, "phase": "archived"})
        c, env = self.approve(second)
        self.assertNotEqual(c, 0, env)
        self.assertFalse((env.get("result") or {}).get("followup"))


class VersionDrift(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name).resolve()
        self.cfg = base / "cfg"
        self.cache = self.cfg / "plugins" / "cache" / "m" / "karvey"
        for v in ("3.13.1", "3.13.2"):
            d = self.cache / v / ".claude-plugin"
            d.mkdir(parents=True)
            (d / "plugin.json").write_text(json.dumps({"version": v}), encoding="utf-8")
            (self.cache / v / "scripts").mkdir()
        self.env = {"CLAUDE_CONFIG_DIR": str(self.cfg)}
        self.install("3.13.2")

    def install(self, v):
        (self.cfg / "plugins" / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": {
            "karvey@m": [{"version": v, "installPath": str(self.cache / v)}]}}), encoding="utf-8")

    def test_an_older_cached_copy_sees_the_installed_one(self):
        old = str(self.cache / "3.13.1")
        self.assertEqual(pluginver.newer_installed(old, self.env)[:2], ("3.13.1", "3.13.2"))
        self.assertIsNone(pluginver.newer_installed(str(self.cache / "3.13.2"), self.env))
        sid = "drift-%s" % os.getpid()
        line = pluginver.drift_line(sid, old, self.env)
        self.assertIn("runs Karvey 3.13.1 but 3.13.2 is installed", line)
        self.assertIsNone(pluginver.drift_line(sid, old, self.env))  # once per session

    def test_a_development_checkout_never_counts(self):
        self.assertIsNone(pluginver.newer_installed(str(HERE.parent.parent), self.env))

    def test_reexec_targets_the_installed_script(self):
        script = self.cache / "3.13.1" / "scripts" / "karvey-state.py"
        (self.cache / "3.13.2" / "scripts" / "karvey-state.py").write_text("", encoding="utf-8")
        with mock.patch.object(os, "execve") as ex:
            pluginver.maybe_reexec(str(script), argv=["check-prod"], env=self.env)
        args = ex.call_args[0]
        self.assertEqual(args[1][1:], [str(self.cache / "3.13.2" / "scripts" / "karvey-state.py"), "check-prod"])
        self.assertEqual(args[2][pluginver.NO_REEXEC_ENV], "1")
        with mock.patch.object(os, "execve") as ex:
            pluginver.maybe_reexec(str(script), argv=[], env=dict(self.env, KARVEY_NO_REEXEC="1"))
        ex.assert_not_called()


if __name__ == "__main__":
    unittest.main()
