"""karvey-evidence.py: hashed evidence of a command run (architecture §1.14 C-18 of wave2-structural).

@req REQ-W2-073
"""
import json
import os
import subprocess
import sys
import unittest

import _path
import _gitrepo as g
from _state import make_project

g.isolate_git()
EV = str(_path.SCRIPTS_DIR / "karvey-evidence.py")
SECRET = "s3cr3t-value-do-not-store"


def run(root, *argv, change="feat-a"):
    extra = ["--change", change] if change else []
    return subprocess.run([sys.executable, EV, "--root", str(root)] + extra + ["--label", "unit"] + ["--"] + list(argv),
                          cwd=str(root), capture_output=True, text=True, timeout=60)


class Evidence(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        make_project(self.t.path, spec={"change_id": "feat-a", "phase": "test"})
        self.ev = self.t.path / "docs/spec/changes/feat-a/evidence.jsonl"

    def tearDown(self):
        self.t.cleanup()

    def test_REQ_W2_073_one_line_and_exit_code_unchanged(self):
        p = run(self.t.path, sys.executable, "-c", "import sys; print('%s'); sys.exit(3)" % SECRET)
        self.assertEqual(p.returncode, 3)
        self.assertIn(SECRET, p.stdout)  # streamed through
        lines = self.ev.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual((rec["change"], rec["exit"], rec["label"]), ("feat-a", 3, "unit"))
        self.assertEqual(len(rec["stdout_sha256"]), 64)
        self.assertIn("evidence.jsonl:1", p.stderr)

    def test_no_output_text_stored(self):
        run(self.t.path, sys.executable, "-c", "print('s3cr3t-' + 'value-do-not-store')")  # output ≠ argv text
        self.assertNotIn(SECRET, self.ev.read_text())
        rec = json.loads(self.ev.read_text().splitlines()[0])
        self.assertEqual(set(rec), {"at", "change", "label", "argv", "cwd_rel", "exit", "duration_ms",
                                    "stdout_sha256", "stderr_sha256", "bytes", "junit"})

    def test_REQ_W2_073_no_active_change_runs_and_says_so(self):
        make_project(self.t.path, spec={"change_id": "feat-b", "phase": "test"}, change="feat-b")
        p = run(self.t.path, sys.executable, "-c", "print('ran')", change=None)  # two open changes: none active
        self.assertEqual(p.returncode, 0)
        self.assertIn("ran", p.stdout)
        self.assertIn("[karvey] evidence not recorded: no active change", p.stderr)
        self.assertFalse(self.ev.exists())

    def test_secrets_in_argv_are_redacted(self):
        """@req REQ-W2-073 — BUG-55 (F-16): secret values on the command line never reach evidence.jsonl; argv[0]
        and ordinary arguments (test file names) stay intact."""
        args = [sys.executable, "-c", "pass", "--password=pw111", "--api-key", "ak222", "--auth-token", "tk333",
                "DB_SECRET=sv444", "https://user:up555@host.example/x", "tests/test_orders.py", "-p", "test_*.py",
                "--verbose", "NAME=plain"]
        p = run(self.t.path, *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        text = self.ev.read_text()
        for s in ("pw111", "ak222", "tk333", "sv444", "up555"):
            self.assertNotIn(s, text)
        argv = json.loads(text.splitlines()[0])["argv"]
        self.assertEqual(argv[0], sys.executable)
        for keep in ("tests/test_orders.py", "-p", "test_*.py", "--verbose", "NAME=plain", "--api-key"):
            self.assertIn(keep, argv)
        self.assertIn("--password=***", argv)
        self.assertIn("DB_SECRET=***", argv)
        self.assertIn("https://***@host.example/x", argv)

    def test_ordinary_flags_that_contain_a_secret_word_are_kept(self):
        """@req REQ-W2-073 — BUG-71 (F-42): `--passWithNoTests` or `--author` are not secrets; the argument after
        them (a test file the trace must see) stays."""
        args = [sys.executable, "-c", "pass", "--passWithNoTests", "src/auth/login.test.js", "--author", "someone",
                "--authToken", "tk777", "--db-pass", "pw888"]
        p = run(self.t.path, *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        argv = json.loads(self.ev.read_text().splitlines()[0])["argv"]
        for keep in ("src/auth/login.test.js", "someone"):
            self.assertIn(keep, argv)
        for s in ("tk777", "pw888"):
            self.assertNotIn(s, argv)

    def test_query_tokens_and_auth_headers_are_redacted(self):
        """@req REQ-W2-073 — BUG-75 (F-65, F-66): URL query secrets and an Authorization header value never reach
        evidence.jsonl (short flags stay: `-p` is a test pattern for the trace)."""
        args = [sys.executable, "-c", "pass", "https://h.example/x?token=qt111&page=2", "-H",
                "Authorization: Bearer hb222", "--url=https://h.example/y?api_key=qk333"]
        p = run(self.t.path, *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        text = self.ev.read_text()
        for s in ("qt111", "hb222", "qk333"):
            self.assertNotIn(s, text)
        self.assertIn("page=2", text)

    def test_junit_path_home_is_collapsed(self):
        """@req REQ-W2-073 — BUG-75 (F-65, F-66): the --junit path is written like argv, home as ``~``."""
        home = os.path.expanduser("~")
        p = subprocess.run([sys.executable, EV, "--root", str(self.t.path), "--change", "feat-a", "--label", "unit",
                            "--junit", home + "/nowhere-karvey-test/r.xml", "--", sys.executable, "-c", "pass"],
                           cwd=str(self.t.path), capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn(home + "/", self.ev.read_text())

    def test_home_directory_is_collapsed(self):
        """@req REQ-W2-073 — BUG-69 (F-40): a user's home path never reaches the committed evidence (it names
        the user); it is written as ``~``. The file name stays, so the trace still matches test files."""
        home = os.path.expanduser("~")
        args = [sys.executable, "-c", "pass", home + "/proj/tests/test_orders.py", "--root=" + home + "/proj"]
        p = run(self.t.path, *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        argv = json.loads(self.ev.read_text().splitlines()[0])["argv"]
        self.assertNotIn(home + "/", json.dumps(argv))
        self.assertIn("~/proj/tests/test_orders.py", argv)
        self.assertIn("--root=~/proj", argv)

    def test_change_id_outside_changes_dir_refused(self):
        """@req REQ-W2-073 — BUG-55 (F-16): --change must be a plain change id; a path never writes elsewhere."""
        outside = g.TempDir()
        try:
            for bad in ("..", "../feat-a", str(outside.path)):
                p = run(self.t.path, sys.executable, "-c", "print('ran')", change=bad)
                self.assertEqual(p.returncode, 2, (bad, p.stderr))
                self.assertIn("invalid change id", p.stderr)
            self.assertFalse((self.t.path / "docs/spec/evidence.jsonl").exists())
            self.assertFalse((outside.path / "evidence.jsonl").exists())
        finally:
            outside.cleanup()

    def test_missing_trailing_newline_does_not_glue_records(self):
        """@req REQ-W2-073 — BUG-55 (F-16): a file without a trailing newline gets a separator; the cited line is
        the new record's."""
        self.ev.write_text('{"exit": 0}', encoding="utf-8")
        p = run(self.t.path, sys.executable, "-c", "pass")
        lines = self.ev.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[1])["change"], "feat-a")
        self.assertIn("evidence.jsonl:2 ", p.stderr)

    def test_unstartable_command_is_127_not_a_traceback(self):
        """BUG-55 (F-16): any OSError starting the command (e.g. exec format error) is reported, not raised."""
        bad = self.t.path / "not-a-program"
        bad.write_bytes(b"\x00\x01garbage")
        bad.chmod(0o755)
        p = run(self.t.path, str(bad))
        self.assertEqual(p.returncode, 127, p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("cannot start", p.stderr)

    def test_missing_command_is_127(self):
        p = run(self.t.path, "no-such-command-karvey")
        self.assertEqual(p.returncode, 127)


if __name__ == "__main__":
    unittest.main()
