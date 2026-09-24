"""karvey-config.py notify-check [--confirm] (REQ-W1-097, REQ-W1-098)."""
import json
import os
import stat
import unittest
from unittest import mock

import _config as C
import _gitrepo as g

GCHAT = {"channel": "google-chat", "target": "spaces/AAAAQCj0Cjc", "via": "cli", "events": ["qa", "deploy"]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = g.TempDir()
        self.root = self.tmp.path / "proj"
        self.state_home = self.tmp.path / "state"
        self.env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.state_home)})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def set_notifications(self, nt):
        C.make_project(self.root, {"notifications": nt})

    def check(self, *extra):
        return C.run_json("notify-check", "--root", self.root, *extra)


class NotifyCheck(Base):
    def test_never_confirmed_requires_confirmation(self):
        self.set_notifications(GCHAT)
        code, env = self.check()
        self.assertEqual((code, env["exit"], env["ok"]), (10, 10, False))
        self.assertTrue(env["result"]["changed"])
        self.assertIsNone(env["result"]["last"])

    def test_confirm_then_unchanged_is_0(self):
        self.set_notifications(GCHAT)
        code, env = self.check("--confirm")
        self.assertEqual((code, env["result"]["recorded"]), (0, True))
        code, env = self.check()
        self.assertEqual((code, env["result"]["changed"]), (0, False))

    def test_changed_target_is_10_with_the_new_destination(self):
        self.set_notifications(GCHAT)
        self.check("--confirm")
        self.set_notifications(dict(GCHAT, target="spaces/EVILSPACE"))
        code, out, _ = C.run("notify-check", "--root", self.root)
        self.assertEqual(code, 10)
        self.assertIn("CONFIRMATION REQUIRED", out)
        self.assertIn("spaces/EVILSPACE", out)
        self.assertIn("spaces/AAAAQCj0Cjc", out)  # the previous one, for comparison
        code, env = self.check()
        self.assertEqual(env["result"]["destination"]["target"], "spaces/EVILSPACE")
        self.assertEqual(env["result"]["last"]["destination"]["target"], "spaces/AAAAQCj0Cjc")

    def test_changed_channel_or_events_is_10(self):
        self.set_notifications(GCHAT)
        self.check("--confirm")
        for nt in (dict(GCHAT, events=["qa"]), dict(GCHAT, detail="full"),
                   {"channel": "slack", "target": "#dev", "via": "cli", "events": ["qa", "deploy"]}):
            with self.subTest(nt=nt):
                self.set_notifications(nt)
                self.assertEqual(self.check()[0], 10)

    def test_confirm_records_the_hash(self):
        self.set_notifications(GCHAT)
        code, env = self.check("--confirm")
        rec_path = self.state_home / "karvey"
        files = list(rec_path.rglob("notify-last.json"))
        self.assertEqual(len(files), 1)
        rec = json.loads(files[0].read_text(encoding="utf-8"))
        entry = list(rec["entries"].values())[0]
        self.assertEqual(entry["hash"], env["result"]["hash"])
        self.assertEqual(entry["destination"]["target"], "spaces/AAAAQCj0Cjc")
        self.assertIn("confirmed_at", entry)
        self.assertEqual(stat.S_IMODE(files[0].stat().st_mode), 0o600)

    def test_url_target_refused_exit_3(self):
        self.set_notifications({"channel": "webhook", "target": "https://hooks.example/abc"})
        for extra in ((), ("--confirm",)):
            with self.subTest(extra=extra):
                code, env = self.check(*extra)
                self.assertEqual(code, 3)
                self.assertIn("://", env["errors"][0]["message"])
        self.assertEqual(list(self.state_home.rglob("notify-last.json")), [])

    def test_metacharacter_target_refused_exit_3(self):
        self.set_notifications({"channel": "google-chat", "target": "spaces/AAA; rm -rf ~"})
        self.assertEqual(self.check()[0], 3)

    def test_detail_defaults_to_counts(self):
        self.set_notifications(GCHAT)
        env = self.check()[1]
        self.assertEqual(env["result"]["destination"]["detail"], "counts")
        # an explicit "counts" is the same destination as the default
        self.check("--confirm")
        self.set_notifications(dict(GCHAT, detail="counts"))
        self.assertEqual(self.check()[0], 0)

    def test_invalid_detail_falls_back_to_counts(self):
        self.set_notifications(dict(GCHAT, detail="verbose"))
        code, env = self.check()
        self.assertEqual(env["result"]["destination"]["detail"], "counts")
        self.assertIn("config.invalid_value", [w["code"] for w in env["warnings"]])

    def test_channel_none_sends_nothing_and_asks_nothing(self):
        self.set_notifications({"channel": "none", "target": "", "via": "", "events": []})
        code, env = self.check()
        self.assertEqual((code, env["result"]["send"]), (0, False))

    def test_worktrees_share_the_record(self):
        g.isolate_git()
        g.init(self.root)
        C.make_project(self.root, {"notifications": GCHAT})
        g.commit_all(self.root)
        self.check("--confirm")
        wt = self.tmp.path / "wt"
        g.run(["worktree", "add", "-q", str(wt)], self.root)
        code, env = C.run_json("notify-check", "--root", wt)
        self.assertEqual(code, 0)
        self.assertTrue((self.root / ".git" / "karvey" / "notify-last.json").is_file())


if __name__ == "__main__":
    unittest.main()
