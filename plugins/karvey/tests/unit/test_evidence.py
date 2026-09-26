"""karvey-evidence.py: hashed evidence of a command run (architecture §1.14 C-18 of wave2-structural).

@req REQ-W2-073
"""
import json
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

    def test_missing_command_is_127(self):
        p = run(self.t.path, "no-such-command-karvey")
        self.assertEqual(p.returncode, 127)


if __name__ == "__main__":
    unittest.main()
