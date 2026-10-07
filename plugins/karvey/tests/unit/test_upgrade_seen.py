"""The seen-version record: per clone, shared by worktrees, 0600, atomic, audited (REQ-UP-001, REQ-UP-004)."""
import json
import os
import stat
import unittest
from unittest import mock

import _gitrepo as g
import _path  # noqa: F401
from karvey_lib import audit, upgrade
from karvey_lib import project as pj


class SeenRecord(unittest.TestCase):
    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "proj")
        g.write(self.root, "docs/spec/project.json", {"a": 1})
        g.commit_all(self.root)

    def tearDown(self):
        for d, _, _ in os.walk(str(self.t.path)):
            try:
                os.chmod(d, 0o700)
            except OSError:
                pass
        self.t.cleanup()

    def test_location_mode_and_content(self):
        self.assertIsNone(upgrade.read_seen(self.root))
        rec = upgrade.write_seen(self.root, "3.13.0", "declined")
        p = self.root / ".git" / "karvey" / "seen-version"
        self.assertEqual(p, upgrade.seen_path(self.root))
        self.assertTrue(p.is_file())
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(p.parent.stat().st_mode), 0o700)
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual({k: data[k] for k in ("v", "version", "resolution", "from")},
                         {"v": 1, "version": "3.13.0", "resolution": "declined", "from": None})
        self.assertEqual(data["by"], "Karvey Test" if data["by"] else None)
        self.assertEqual(upgrade.read_seen(self.root), rec)
        self.assertFalse((p.parent / "seen-version.lock").exists(), "the lock is released")
        again = upgrade.write_seen(self.root, "3.14.0", "accepted")
        self.assertEqual(again["from"], "3.13.0")

    def test_malformed_or_unknown_v_counts_as_absent(self):
        d = pj.state_dir(self.root)
        for text in ("{not json", json.dumps({"v": 2, "version": "3.13.0", "resolution": "empty"}),
                     json.dumps({"v": 1, "version": "latest", "resolution": "empty"}),
                     json.dumps({"v": 1, "version": "3.13.0", "resolution": "maybe"}), "[]"):
            with self.subTest(text=text):
                (d / "seen-version").write_text(text, encoding="utf-8")
                self.assertIsNone(upgrade.read_seen(self.root))

    def test_a_worktree_reads_the_main_copy_record(self):
        upgrade.write_seen(self.root, "3.13.0", "empty")
        wt = self.t.path / "wt"
        g.run(["worktree", "add", "-q", "-b", "side", str(wt)], self.root)
        rec = upgrade.read_seen(wt)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["resolution"], "empty")
        cp = __import__("subprocess").run(["git", "status", "--porcelain"], cwd=str(wt), capture_output=True, text=True)
        self.assertEqual(cp.stdout, "", "the record is never in the working tree")

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores file modes")
    def test_read_only_git_dir_gives_the_repeat_message(self):
        os.chmod(str(self.root / ".git"), 0o500)
        with self.assertRaises(upgrade.SeenWriteError) as cm:
            upgrade.write_seen(self.root, "3.13.0", "declined")
        self.assertIn("could not record the upgrade answer", str(cm.exception))
        self.assertIn("the offer will repeat next session", str(cm.exception))

    def test_audit_line(self):
        upgrade.write_seen(self.root, "3.13.0", "declined")
        recs = [r for r in audit.read(pj.state_dir(self.root)) if r.get("event") == "upgrade.seen"]
        self.assertEqual(len(recs), 1)
        self.assertEqual((recs[0]["resolution"], recs[0]["version"]), ("declined", "3.13.0"))

    def test_version_re(self):
        for ok in ("3.13.0", "10.0.1", "3.13.0-rc.1"):
            self.assertTrue(upgrade.VERSION_RE.match(ok), ok)
        for bad in ("3.13", "v3.13.0", "3.13.0; rm -rf ~", "3.13.0\n", "latest", "", "3.13.0-" + "x" * 30):
            self.assertIsNone(upgrade.VERSION_RE.match(bad), bad)
        with self.assertRaises(upgrade.SeenWriteError):
            upgrade.write_seen(self.root, "3.13", "declined")
        self.assertIsNone(upgrade.read_seen(self.root))

    def test_plan_reads_from_the_record(self):
        upgrade.write_seen(self.root, "3.0.0", "declined")
        p = upgrade.plan(self.root, steps=[], registry={})
        self.assertEqual(p.from_version, "3.0.0")


class SeenCli(unittest.TestCase):
    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "proj")
        g.write(self.root, "docs/spec/project.json", {"a": 1})
        g.commit_all(self.root)

    def tearDown(self):
        self.t.cleanup()

    def seen(self, flag):
        from test_upgrade_cli import run_tool
        code, out, err = run_tool("seen", flag, "--json", cwd=self.root)
        return code, json.loads(out)

    def test_decline_accept_empty_show(self):
        code, env = self.seen("--show")
        self.assertEqual((code, env["result"]["record"]), (0, None))
        for flag, res in (("--decline", "declined"), ("--accept", "accepted"), ("--empty", "empty")):
            with self.subTest(flag=flag):
                code, env = self.seen(flag)
                self.assertEqual(code, 0, env)
                self.assertEqual(env["result"]["record"]["resolution"], res)
                self.assertEqual(env["result"]["record"]["version"], upgrade.INSTALLED)
                self.assertEqual(upgrade.read_seen(self.root)["resolution"], res)
        code, env = self.seen("--show")
        self.assertEqual(env["result"]["record"]["resolution"], "empty")

    def test_decline_suppresses_this_version_only(self):
        self.seen("--decline")
        self.assertTrue(upgrade.is_resolved(self.root, upgrade.INSTALLED))
        self.assertFalse(upgrade.is_resolved(self.root, "99.0.0"), "the next version is offered again")

    def test_unanswered_means_offered_again(self):
        self.assertFalse(upgrade.is_resolved(self.root, upgrade.INSTALLED))

    def test_f27_outside_git_nothing_is_recorded(self):
        """regression_project-upgrade_iterate_seen_outside_git (F-27): no record under the home's state dir."""
        from test_upgrade_cli import run_tool
        plain = self.t.path / "nogit"
        g.write(plain, "docs/spec/project.json", {"a": 1})
        state = self.t.path / "xdg"
        env = {"XDG_STATE_HOME": str(state)}
        with mock.patch.dict(os.environ, env):
            code, out, _ = run_tool("seen", "--decline", "--json", cwd=plain)
            self.assertEqual(code, 3, out)
            self.assertIn("git", json.loads(out)["errors"][0]["message"])
            with self.assertRaises(upgrade.SeenWriteError):
                upgrade.write_seen(plain, upgrade.INSTALLED, "empty")
        self.assertFalse(state.exists())

    def test_one_flag_required(self):
        from test_upgrade_cli import run_tool
        self.assertEqual(run_tool("seen", cwd=self.root)[0], 2)
        self.assertEqual(run_tool("seen", "--decline", "--accept", cwd=self.root)[0], 2)


if __name__ == "__main__":
    unittest.main()
