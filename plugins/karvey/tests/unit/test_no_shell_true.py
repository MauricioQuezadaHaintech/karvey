"""§3.1 rule 1: every subprocess call in scripts/ is an argv list (REQ-W1-093).

A grep of ``plugins/karvey/scripts/`` for the three shell entry points must find nothing.
"""
import re
import unittest

import _path

FORBIDDEN = re.compile(r"shell\s*=\s*True|os\.system|os\.popen")


class NoShellTrue(unittest.TestCase):
    def test_scripts_never_use_a_shell(self):
        files = sorted(p for p in _path.SCRIPTS_DIR.rglob("*.py") if "__pycache__" not in p.parts)
        self.assertTrue(files, "no scripts found under %s" % _path.SCRIPTS_DIR)
        hits = []
        for p in files:
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if FORBIDDEN.search(line):
                    hits.append("%s:%d: %s" % (p.relative_to(_path.PLUGIN_ROOT), n, line.strip()))
        self.assertEqual(hits, [], "shell entry points found:\n" + "\n".join(hits))

    def test_the_pattern_catches_each_form(self):
        for s in ("subprocess.run(c, shell=True)", "shell = True", "os.system('x')", "os.popen('x')"):
            with self.subTest(s=s):
                self.assertTrue(FORBIDDEN.search(s))


if __name__ == "__main__":
    unittest.main()
