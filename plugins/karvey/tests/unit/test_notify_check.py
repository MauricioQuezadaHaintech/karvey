"""karvey-config.py notify-check [--confirm] (REQ-W1-097, REQ-W1-098; D-16 / F-15: --confirm needs the
human's typed confirmation, recorded by the UserPromptSubmit hook)."""
import io
import json
import os
import stat
import unittest
from datetime import timedelta
from unittest import mock

import _config as C
import _gitrepo as g
from karvey_lib import approval, karvey_hooks as kh

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

    def check(self, *extra, root=None):
        return C.run_json("notify-check", "--root", root or self.root, *extra)

    def prompt(self, text, root=None):
        """The human types ``text``: the real UserPromptSubmit dispatcher runs on it."""
        root = root or self.root
        out, err = io.StringIO(), io.StringIO()
        payload = {"session_id": "s1", "transcript_path": "", "cwd": str(root),
                   "hook_event_name": "UserPromptSubmit", "prompt": text}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
        code = kh.dispatch("prompt", json.dumps(payload), env=env, out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def human_confirms(self, root=None):
        """The human types the phrase notify-check printed; returns that phrase."""
        phrase = self.check(root=root)[1]["result"]["confirm_phrase"]
        self.assertEqual(self.prompt(phrase, root=root)[0], 0)
        return phrase

    def confirm(self, root=None):
        self.human_confirms(root=root)
        return self.check("--confirm", root=root)


class NotifyCheck(Base):
    def test_never_confirmed_requires_confirmation(self):
        self.set_notifications(GCHAT)
        code, env = self.check()
        self.assertEqual((code, env["exit"], env["ok"]), (10, 10, False))
        self.assertTrue(env["result"]["changed"])
        self.assertIsNone(env["result"]["last"])

    def test_confirm_then_unchanged_is_0(self):
        self.set_notifications(GCHAT)
        code, env = self.confirm()
        self.assertEqual((code, env["result"]["recorded"]), (0, True))
        code, env = self.check()
        self.assertEqual((code, env["result"]["changed"]), (0, False))

    def test_changed_target_is_10_with_the_new_destination(self):
        self.set_notifications(GCHAT)
        self.confirm()
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
        self.confirm()
        for nt in (dict(GCHAT, events=["qa"]), dict(GCHAT, detail="full"),
                   {"channel": "slack", "target": "#dev", "via": "cli", "events": ["qa", "deploy"]}):
            with self.subTest(nt=nt):
                self.set_notifications(nt)
                self.assertEqual(self.check()[0], 10)

    def test_confirm_records_the_hash(self):
        self.set_notifications(GCHAT)
        code, env = self.confirm()
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
        self.confirm()
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
        self.assertEqual(self.confirm()[0], 0)
        wt = self.tmp.path / "wt"
        g.run(["worktree", "add", "-q", str(wt)], self.root)
        code, env = C.run_json("notify-check", "--root", wt)
        self.assertEqual(code, 0)
        self.assertTrue((self.root / ".git" / "karvey" / "notify-last.json").is_file())


class HumanConfirmation(Base):
    """D-16 / F-15: the agent alone cannot confirm a changed destination."""

    def test_agent_alone_cannot_confirm(self):
        self.set_notifications(GCHAT)
        code, env = self.check("--confirm")
        self.assertEqual((code, env["result"]["recorded"]), (10, False))
        self.assertEqual(env["result"]["human_confirmation"], "no human confirmation recorded")
        self.assertEqual(list(self.state_home.rglob("notify-last.json")), [])
        self.assertEqual(self.check()[0], 10)  # still unconfirmed

    def test_refusal_tells_the_human_what_to_type(self):
        self.set_notifications(GCHAT)
        code_ = self.check()[1]["result"]["code"]
        code, out, _ = C.run("notify-check", "--root", self.root, "--confirm")
        self.assertEqual(code, 10)
        self.assertIn("NOT CONFIRMED", out)
        self.assertIn("confirmo notificacion %s" % code_, out)
        self.assertIn("confirm notification %s" % code_, out)

    def test_human_prompt_confirms_once(self):
        self.set_notifications(GCHAT)
        phrase = self.check()[1]["result"]["confirm_phrase"]
        code, out, _ = self.prompt(phrase)
        self.assertIn("[karvey] notification destination confirmation recorded (", out)
        code, env = self.check("--confirm")
        self.assertEqual((code, env["result"]["recorded"], env["result"]["human_confirmation"]), (0, True, "ok"))
        self.assertEqual(self.check()[0], 0)
        # single use: the next change needs a new human confirmation
        self.set_notifications(dict(GCHAT, target="spaces/OTHER"))
        code, env = self.check("--confirm")
        self.assertEqual(code, 10)

    def test_human_phrase_variants(self):
        self.set_notifications(GCHAT)
        c = self.check()[1]["result"]["code"]
        for text in ("Confirmo notificación %s" % c, "ok, confirm notification %s" % c,
                     "confirmo destino: %s" % c, "`confirmo notificacion %s`" % c):
            with self.subTest(text=text):
                self.assertEqual(approval.classify_notify(text), c)
        for text in ("no confirmo notificacion %s" % c, "confirmo notificacion %s?" % c,
                     "> confirmo notificacion %s" % c, "```\nconfirmo notificacion %s\n```" % c,
                     "confirmo notificacion", "confirmo %s" % c, "notificacion %s" % c,
                     "confirmo notificacion %s" % c + " " + "x" * 200):
            with self.subTest(text=text):
                self.assertIsNone(approval.classify_notify(text))

    def test_marker_for_another_destination_does_not_count(self):
        self.set_notifications(GCHAT)
        self.human_confirms()
        self.set_notifications(dict(GCHAT, target="spaces/EVILSPACE"))
        code, env = self.check("--confirm")
        self.assertEqual(code, 10)
        self.assertIn("another destination", env["result"]["human_confirmation"])

    def test_marker_for_another_project_does_not_count(self):
        g.isolate_git()
        g.init(self.root)
        C.make_project(self.root, {"notifications": GCHAT})
        other = self.root / "sub"
        C.make_project(other, {"notifications": GCHAT})
        g.commit_all(self.root)
        self.human_confirms(root=other)  # same clone, same destination, other project
        code, env = self.check("--confirm")
        self.assertEqual(code, 10)
        self.assertEqual(env["result"]["human_confirmation"], "no human confirmation recorded")
        # a marker copied from the other project is still bound to it
        src = approval.notify_marker_path(other)
        dst = approval.notify_marker_path(self.root)
        dst.write_bytes(src.read_bytes())
        code, env = self.check("--confirm")
        self.assertEqual(code, 10)
        self.assertIn("another project", env["result"]["human_confirmation"])
        self.assertEqual(self.check("--confirm", root=other)[0], 0)

    def test_expired_marker_does_not_count(self):
        self.set_notifications(GCHAT)
        h = self.check()[1]["result"]["hash"]
        ttl = approval.defaults()["plan_marker_ttl_min"]
        approval.write_notify_marker(self.root, approval.notify_code(h), "confirmo",
                                     now=approval.now_dt() - timedelta(minutes=ttl + 1))
        code, env = self.check("--confirm")
        self.assertEqual(code, 10)
        self.assertIn("expired", env["result"]["human_confirmation"])

    def test_ttl_is_the_approval_marker_ttl(self):
        self.set_notifications(GCHAT)
        self.human_confirms()
        data = json.loads(approval.notify_marker_path(self.root).read_text(encoding="utf-8"))
        self.assertEqual(data["ttl_min"], approval.defaults()["plan_marker_ttl_min"])
        self.assertEqual(stat.S_IMODE(approval.notify_marker_path(self.root).stat().st_mode), 0o600)

    def test_forged_marker_does_not_count(self):
        self.set_notifications(GCHAT)
        h = self.check()[1]["result"]["hash"]
        p = approval.notify_marker_path(self.root)
        for data in ("", {"v": 1, "kind": "notify", "code": approval.notify_code(h)}):
            with self.subTest(data=data):
                p.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
                code, env = self.check("--confirm")
                self.assertEqual(code, 10)
                self.assertIn("forged", env["result"]["human_confirmation"])

    def test_protect_paths_blocks_the_agent_writing_the_marker(self):
        self.set_notifications(GCHAT)
        p = str(approval.notify_marker_path(self.root))
        rec = str(approval.notify_marker_path(self.root).parent.parent.parent / "notify-last.json")
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        for payload in ({"tool_name": "Write", "tool_input": {"file_path": p, "content": "{}"}},
                        {"tool_name": "Bash", "tool_input": {"command": "echo {} > %s" % p}},
                        {"tool_name": "Bash", "tool_input": {"command": "echo {} > %s" % rec}}):
            with self.subTest(payload=payload):
                payload = dict(payload, session_id="s1", cwd=str(self.root), hook_event_name="PreToolUse")
                event = "pre-edit" if payload["tool_name"] == "Write" else "pre-bash"
                out, err = io.StringIO(), io.StringIO()
                code = kh.dispatch(event, json.dumps(payload), env=env, out=out, err=err)
                self.assertEqual(code, 2, err.getvalue())
                self.assertIn("protect-paths", err.getvalue())


if __name__ == "__main__":
    unittest.main()
