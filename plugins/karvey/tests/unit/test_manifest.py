"""Commit → change mapping for the release manifest (architecture §1.9 of wave2-structural, A-12).

@req REQ-W2-043 REQ-W2-045 REQ-W2-088
"""
import unittest

import _path  # noqa: F401
import _gitrepo as g
from karvey_lib import manifest as mf

g.isolate_git()
TRAILER = "\n\nKarvey-Change: %s\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        g.write(self.root, "README.md", "x\n")
        g.commit_all(self.root, "base")
        g.run(["tag", "base"], self.root)

    def tearDown(self):
        self.t.cleanup()

    def commit(self, rel, msg):
        g.write(self.root, rel, msg + "\n")
        g.commit_all(self.root, msg)

    def m(self):
        return mf.map_commits(self.root, "base", "HEAD")


class Trailers(Base):
    def test_REQ_W2_043_trailer_maps(self):
        self.commit("src/a.py", "feat: a" + TRAILER % "feat-a")
        r = self.m()
        self.assertEqual(list(r["changes"]), ["feat-a"])
        self.assertEqual((r["commits"][0]["mapped_by"], r["unmapped"]), ("trailer", []))

    def test_no_trailer_is_unmapped_with_reason(self):
        self.commit("src/a.py", "feat: a")
        r = self.m()
        self.assertEqual(r["unmapped"][0]["reason"], "no Karvey-Change trailer")
        self.assertEqual(r["changes"], {})

    def test_malformed_and_two_values_unmapped(self):
        self.commit("src/a.py", "feat: a" + TRAILER % "Feat_A!")
        self.commit("src/b.py", "feat: b\n\nKarvey-Change: feat-a\nKarvey-Change: feat-b\n")
        r = self.m()
        reasons = [u["reason"] for u in r["unmapped"]]
        self.assertTrue(reasons[0].startswith("malformed Karvey-Change value"), reasons)
        self.assertEqual(reasons[1], "several Karvey-Change values: feat-a, feat-b")

    def test_parse_trailers_same_value_twice_is_one(self):
        self.assertEqual(mf.parse_trailers(["feat-a", "feat-a"]), ("feat-a", None))
        self.assertEqual(mf.parse_trailers(["archive"])[0], None)


class Merge(Base):
    def test_merge_commit_mapped_through_its_parents(self):
        g.run(["checkout", "-q", "-b", "feature/feat-a"], self.root)
        self.commit("src/a.py", "feat: a" + TRAILER % "feat-a")
        self.commit("src/b.py", "feat: b" + TRAILER % "feat-a")
        g.run(["checkout", "-q", "main"], self.root)
        self.commit("src/c.py", "fix: c" + TRAILER % "fix-c")
        g.run(["merge", "-q", "--no-ff", "--no-edit", "feature/feat-a"], self.root)
        r = self.m()
        merge = r["commits"][-1]
        self.assertEqual((merge["change"], merge["mapped_by"]), ("feat-a", "merge"))
        self.assertEqual(r["unmapped"], [])
        self.assertEqual(len(r["changes"]["feat-a"]), 3)

    def test_merge_of_mixed_changes_unmapped(self):
        g.run(["checkout", "-q", "-b", "side"], self.root)
        self.commit("src/a.py", "feat: a" + TRAILER % "feat-a")
        self.commit("src/b.py", "feat: b" + TRAILER % "feat-b")
        g.run(["checkout", "-q", "main"], self.root)
        self.commit("src/c.py", "fix: c" + TRAILER % "fix-c")
        g.run(["merge", "-q", "--no-ff", "--no-edit", "side"], self.root)
        r = self.m()
        self.assertEqual(len(r["unmapped"]), 1)
        self.assertIn("feat-a, feat-b", r["unmapped"][0]["reason"])


class PathOnly(Base):
    def test_spec_bookkeeping_maps_by_path(self):
        self.commit("docs/spec/changes/feat-a/PLAN.md", "docs: plan")
        r = self.m()
        self.assertEqual((r["commits"][0]["change"], r["commits"][0]["mapped_by"]), ("feat-a", "path"))

    def test_mixed_paths_or_archive_stay_unmapped(self):
        self.commit("docs/spec/changes/feat-a/PLAN.md", "docs: plan")
        g.write(self.root, "src/x.py", "y\n")
        g.write(self.root, "docs/spec/changes/feat-a/PLAN.md", "z\n")
        g.commit_all(self.root, "mixed")
        self.commit("docs/spec/changes/archive/2026-01-01-old/spec.json", "archive move")
        r = self.m()
        self.assertEqual([u["subject"] for u in r["unmapped"]], ["mixed", "archive move"])

    def test_bad_ref_raises(self):
        with self.assertRaises(mf.ManifestError):
            mf.map_commits(self.root, "no-such-ref", "HEAD")


if __name__ == "__main__":
    unittest.main()
