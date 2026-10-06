"""BUG-156: the no-python plan-gate refused checkpoint saves when a folder above the project is a symlink (macOS
/var -> /private/var). Reproduced on any OS by running the checkpoint rows with TMPDIR through a symlink."""
import os
import subprocess
import sys
import tempfile
import unittest

import _path


class SymlinkedTemp(unittest.TestCase):
    def test_checkpoint_rows_pass_under_a_symlinked_temp_folder(self):
        if os.name == "nt":
            self.skipTest("symlinks need a privilege on Windows runners")
        with tempfile.TemporaryDirectory() as t:
            real = os.path.join(t, "real")
            os.mkdir(real)
            link = os.path.join(t, "link")
            os.symlink(real, link)
            env = dict(os.environ, TMPDIR=link)
            r = subprocess.run([sys.executable, str(_path.TESTS_DIR / "hooks" / "run_tables.py"), "--only",
                                "plan-gate", "--tag", "REQ-HF-031"], env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=300)
            out = r.stdout.decode("utf-8", "replace")
            self.assertEqual(r.returncode, 0, out[-2000:])
            self.assertIn(" 0 failed", out)


if __name__ == "__main__":
    unittest.main()
