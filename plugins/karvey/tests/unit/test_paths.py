"""hookio.norm_path: Windows / WSL / Git-Bash paths (A-10)."""
import unittest

import _path  # noqa: F401
from karvey_lib.hookio import norm_path

H = "/home/u"


class Posix(unittest.TestCase):
    def n(self, p, cwd="/w"):
        return norm_path(p, cwd=cwd, platform="posix", home=H)

    def test_drive_letter_to_mnt(self):
        self.assertEqual(self.n("C:\\Users\\me\\repo\\docs\\spec\\spec.json"), "/mnt/c/Users/me/repo/docs/spec/spec.json")
        self.assertEqual(self.n("D:/x/../y"), "/mnt/d/y")
        self.assertEqual(self.n("c:\\"), "/mnt/c")

    def test_wsl_unc(self):
        self.assertEqual(self.n("\\\\wsl$\\Ubuntu\\home\\u\\p\\a.txt"), "/home/u/p/a.txt")
        self.assertEqual(self.n("\\\\wsl.localhost\\Ubuntu-22.04\\home\\u"), "/home/u")
        self.assertEqual(self.n("//wsl$/Ubuntu/tmp/x"), "/tmp/x")

    def test_plain_posix(self):
        self.assertEqual(self.n("/c/Users/me"), "/c/Users/me")  # a real directory on posix, left alone
        self.assertEqual(self.n("a/./b/../c"), "/w/a/c")
        self.assertEqual(self.n("~/x"), "/home/u/x")
        self.assertEqual(self.n("~"), "/home/u")

    def test_empty(self):
        self.assertIsNone(self.n(""))
        self.assertIsNone(self.n(None))
        self.assertIsNone(self.n(5))


class Windows(unittest.TestCase):
    def n(self, p, cwd="C:/w"):
        return norm_path(p, cwd=cwd, platform="windows", home="C:/Users/u")

    def test_git_bash_to_drive(self):
        self.assertEqual(self.n("/c/Users/me/repo"), "C:/Users/me/repo")
        self.assertEqual(self.n("/d/"), "D:/")

    def test_drive_backslashes(self):
        self.assertEqual(self.n("C:\\Users\\me\\..\\you"), "C:/Users/you")

    def test_relative_and_home(self):
        self.assertEqual(self.n("docs\\spec"), "C:/w/docs/spec")
        self.assertEqual(self.n("~/x"), "C:/Users/u/x")

    def test_wsl_unc_left_as_is(self):
        self.assertEqual(self.n("\\\\wsl$\\Ubuntu\\home"), "\\\\wsl$\\Ubuntu\\home")


if __name__ == "__main__":
    unittest.main()
