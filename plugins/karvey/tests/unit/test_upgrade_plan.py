"""The read-only Probe and the plan (REQ-UP-005, 007, 009, 010, 016)."""
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

import _gitrepo as g
import _path  # noqa: F401
from karvey_lib import upgrade


class ProbeReads(unittest.TestCase):
    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "proj")
        g.write(self.root, "docs/spec/project.json", {"a": 1})
        g.write(self.root, "notes.txt", "hello\n")
        self.outside = self.t.path / "outside.txt"
        self.outside.write_text("secret\n", encoding="utf-8")
        self.home = self.t.path / "home"
        g.write(self.home, ".claude/settings.json", {"statusLine": {"command": "x"}})
        g.write(self.home, ".ssh/id", "key\n")

    def tearDown(self):
        self.t.cleanup()

    def probe(self, **kw):
        return upgrade.Probe(self.root, home=self.home, **kw)

    def test_reads_only_under_the_root(self):
        p = self.probe()
        self.assertEqual(p.read_text("notes.txt"), "hello\n")
        self.assertIsNone(p.read_text("absent.txt"))
        for bad in ("../outside.txt", "/etc/hostname", str(self.outside), "docs/../../outside.txt"):
            with self.subTest(path=bad):
                with self.assertRaises(upgrade.ProbeError):
                    p.read_text(bad)

    def test_a_symlink_out_of_the_root_is_refused(self):
        os.symlink(str(self.outside), str(self.root / "link.txt"))
        with self.assertRaises(upgrade.ProbeError):
            self.probe().read_text("link.txt")

    def test_read_json_keeps_format_and_hash(self):
        doc = self.probe().read_json("docs/spec/project.json")
        self.assertEqual(doc.data, {"a": 1})
        self.assertEqual(doc.fmt["indent"], 2)
        self.assertEqual(doc.dumps(doc.data), (self.root / "docs/spec/project.json").read_text(encoding="utf-8"))
        g.write(self.root, "bad.json", "{nope")
        with self.assertRaises(upgrade.CheckFailed):
            self.probe().read_json("bad.json")

    def test_git_read_allow_list_and_no_shell(self):
        p = self.probe()
        rc, out = p.git_read("rev-parse", "--show-toplevel")
        self.assertEqual(rc, 0)
        self.assertEqual(os.path.realpath(out.strip()), str(self.root))
        for bad in (("commit", "-m", "x"), ("push",), ("checkout", "-b", "x"), ("config", "user.name", "x"),
                    ("status",), ("reset", "--hard")):
            with self.subTest(args=bad):
                with self.assertRaises(upgrade.ProbeError):
                    p.git_read(*bad)
        calls = []
        real = subprocess.run

        def spy(*a, **kw):
            calls.append((a, kw))
            return real(*a, **kw)
        with mock.patch.object(upgrade.subprocess, "run", side_effect=spy):
            p.git_read("status", "--porcelain")
        self.assertIsInstance(calls[0][0][0], list)
        self.assertNotIn("shell", calls[0][1])

    def test_home_read_only_three_files_capped(self):
        p = self.probe()
        self.assertIn("statusLine", p.home_read(".claude/settings.json"))
        self.assertIsNone(p.home_read(".claude/CLAUDE.md"))
        for bad in (".ssh/id", ".claude/../.ssh/id", ".bashrc"):
            with self.subTest(path=bad):
                with self.assertRaises(upgrade.ProbeError):
                    p.home_read(bad)
        big = self.home / ".claude/settings.local.json"
        big.write_bytes(b" " * (upgrade.HOME_READ_MAX + 1))
        with self.assertRaises(upgrade.CheckFailed):
            p.home_read(".claude/settings.local.json")

    def test_overlay_makes_a_pending_edit_visible(self):
        overlay = {}
        p = self.probe(overlay=overlay)
        upgrade.overlay_apply(overlay, [upgrade.Edit("write", "notes.txt", before_sha256=p.sha256("notes.txt"),
                                                     text="changed\n"),
                                        upgrade.Edit("write", "new.txt", text="n\n"),
                                        upgrade.Edit("delete", "docs/spec/project.json", before_sha256="x")])
        self.assertEqual(p.read_text("notes.txt"), "changed\n")
        self.assertTrue(p.exists("new.txt"))
        self.assertFalse(p.exists("docs/spec/project.json"))
        self.assertIn("new.txt", p.glob("*.txt"))
        self.assertNotIn("docs/spec/project.json", p.glob("docs/spec/*.json"))
        self.assertEqual((self.root / "notes.txt").read_text(encoding="utf-8"), "hello\n", "nothing written")

    def test_state_and_config_modules_load_via_importlib(self):
        p = self.probe()
        self.assertTrue(callable(p.state.fix_spec))
        self.assertTrue(callable(p.state.fix_project))
        self.assertTrue(callable(p.config.propose_settings))
        self.assertIs(p.state, upgrade.state_module())

    def test_edit_and_result_contracts(self):
        with self.assertRaises(ValueError):
            upgrade.Edit("move", "a")
        with self.assertRaises(ValueError):
            upgrade.Edit("write", "a", scope="home", text="x")
        with self.assertRaises(ValueError):
            upgrade.Edit("write", "a")
        with self.assertRaises(ValueError):
            upgrade.StepResult("maybe")

    def test_deadline(self):
        import time
        p = self.probe(deadline=time.monotonic() - 1)
        with self.assertRaises(upgrade.DeadlineExceeded):
            p.check_deadline()


if __name__ == "__main__":
    unittest.main()
