import os
import stat
import unittest
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from karvey_lib import project as pj

g.isolate_git()


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.d = self.t.path

    def tearDown(self):
        self.t.cleanup()


class KarveyProjectDefinition(Base):
    def test_project_json_or_changes(self):
        a, b, c = self.d / "a", self.d / "b", self.d / "c"
        g.write(a, "docs/spec/project.json", {"repos": ["a"]})
        (b / "docs/spec/changes").mkdir(parents=True)
        g.write(c, "docs/spec/openapi.yaml", "openapi: 3.0.0\n")
        self.assertTrue(pj.is_karvey_project(a))
        self.assertTrue(pj.is_karvey_project(b))
        self.assertFalse(pj.is_karvey_project(c))


class RootDiscovery(Base):
    def test_walk_up_inside_repo(self):
        repo = g.init(self.d / "repo")
        g.write(repo, "docs/spec/project.json", {})
        (repo / "src/deep").mkdir(parents=True)
        self.assertEqual(pj.find_root(repo / "src/deep"), repo)
        self.assertEqual(pj.find_root(repo / "src/deep/missing-file.txt"), repo)

    def test_bounded_by_git_top_level(self):
        # REQ-W1-050 error scenario: a Karvey parent above the git top level is not used.
        parent = self.d / "parent"
        (parent / "docs/spec/changes").mkdir(parents=True)
        child = g.init(parent / "child")
        g.write(child, "docs/spec/openapi.yaml", "x: 1\n")
        self.assertIsNone(pj.find_root(child / "docs/spec"))
        self.assertEqual(pj.find_root(parent), parent)  # parent is not a repo: start dir only

    def test_outside_git_only_start_dir(self):
        parent = self.d / "p"
        (parent / "docs/spec/changes").mkdir(parents=True)
        (parent / "sub").mkdir()
        self.assertIsNone(pj.find_root(parent / "sub"))

    def test_explicit_root(self):
        (self.d / "docs/spec/changes").mkdir(parents=True)
        self.assertEqual(pj.find_root(root=str(self.d)), self.d)
        self.assertIsNone(pj.find_root(root=str(self.d / "docs")))

    def test_worktree(self):
        repo = g.init(self.d / "repo")
        g.write(repo, "docs/spec/project.json", {})
        g.commit_all(repo)
        g.run(["worktree", "add", "-q", "-b", "feature/x", str(self.d / "wt")], repo)
        wt = self.d / "wt"
        self.assertTrue((wt / ".git").is_file())  # BUG-21 shape
        self.assertEqual(pj.find_root(wt / "docs"), wt)
        self.assertEqual(pj.git_common_dir(wt), Path(os.path.realpath(str(repo / ".git"))))


def mkchange(root, cid, phase="impl", implemented=False, archived=False):
    base = "docs/spec/changes/archive/" if archived else "docs/spec/changes/"
    g.write(root, base + cid + "/spec.json", {"change_id": cid, "phase": phase})
    if implemented:
        g.write(root, base + cid + "/IMPLEMENTED", "")


class ActiveChange(Base):
    def setUp(self):
        super().setUp()
        self.repo = g.init(self.d / "repo")
        g.write(self.repo, "docs/spec/project.json", {"branch_flow": {"feature_prefix": "feature/",
                                                                      "integration": "dev", "production": "main"}})

    def test_feature_branch_wins(self):
        mkchange(self.repo, "a")
        mkchange(self.repo, "b")
        r = pj.active_change(self.repo, branch="feature/b")
        self.assertEqual((r["change"], r["reason"]), ("b", "branch"))

    def test_current_git_branch_used(self):
        mkchange(self.repo, "a")
        mkchange(self.repo, "b")
        g.commit_all(self.repo)
        g.run(["checkout", "-q", "-b", "feature/a"], self.repo)
        self.assertEqual(pj.active_change(self.repo)["change"], "a")

    def test_single_non_archived(self):
        mkchange(self.repo, "zz-old", archived=True)  # REQ-W1-045: newer archive not chosen
        mkchange(self.repo, "feat-a")
        r = pj.active_change(self.repo, branch="main")
        self.assertEqual((r["change"], r["reason"]), ("feat-a", "single"))

    def test_implemented_and_deployed_excluded(self):
        mkchange(self.repo, "done", implemented=True)
        mkchange(self.repo, "shipped", phase="deployed")
        mkchange(self.repo, "live", phase="tasks")
        self.assertEqual(pj.active_change(self.repo, branch="main")["change"], "live")

    def test_only_archived_is_none(self):
        mkchange(self.repo, "x", archived=True)
        r = pj.active_change(self.repo, branch="main")
        self.assertEqual((r["change"], r["reason"], r["candidates"]), (None, "none", []))

    def test_several(self):
        mkchange(self.repo, "a")
        mkchange(self.repo, "b")
        r = pj.active_change(self.repo, branch="main")
        self.assertEqual((r["change"], r["reason"], r["candidates"]), (None, "several", ["a", "b"]))

    def test_branch_for_unknown_change_falls_through(self):
        mkchange(self.repo, "a")
        self.assertEqual(pj.active_change(self.repo, branch="feature/nope")["reason"], "single")


class ReviewedConfig(Base):
    def setUp(self):
        super().setUp()
        self.repo = g.init(self.d / "repo")
        g.write(self.repo, "docs/spec/project.json",
                {"branch_flow": {"integration": "main", "production": "main"},
                 "enforcement": {"prod_gate_hook": True}})
        g.commit_all(self.repo)

    def test_reads_origin_not_working_copy(self):
        g.with_origin(self.repo)
        g.write(self.repo, "docs/spec/project.json",
                {"branch_flow": {"integration": "main", "production": "main"},
                 "enforcement": {"prod_gate_hook": False}})  # uncommitted weakening
        data, status = pj.read_reviewed_project_json(self.repo)
        self.assertEqual(status, "ok")
        self.assertIs(data["enforcement"]["prod_gate_hook"], True)

    def test_uses_git_show_argv(self):
        g.with_origin(self.repo)
        calls = []
        real = pj.subprocess.run

        def spy(args, **kw):
            calls.append((args, kw.get("shell", False)))
            return real(args, **kw)

        with mock.patch.object(pj.subprocess, "run", side_effect=spy):
            pj.read_reviewed_project_json(self.repo)
        self.assertIn(["git", "show", "refs/remotes/origin/main:docs/spec/project.json"], [c[0] for c in calls])
        self.assertTrue(all(isinstance(c[0], list) and not c[1] for c in calls))

    def test_no_ref_and_missing(self):
        self.assertEqual(pj.read_reviewed_project_json(self.repo)[1], "no-ref")
        g.with_origin(self.repo)
        self.assertEqual(pj.read_reviewed_project_json(self.repo, production="nope")[1], "no-ref")
        g.run(["rm", "-q", "docs/spec/project.json"], self.repo)
        g.commit_all(self.repo)
        g.run(["push", "-q", "origin", "main"], self.repo)
        self.assertEqual(pj.read_reviewed_project_json(self.repo, production="main")[1], "missing")

    def test_root_below_top_level(self):
        mono = g.init(self.d / "mono")
        g.write(mono, "svc/docs/spec/project.json", {"branch_flow": {"production": "main"}, "k": 1})
        g.commit_all(mono)
        g.with_origin(mono)
        data, status = pj.read_reviewed_project_json(mono / "svc")
        self.assertEqual((status, data["k"]), ("ok", 1))

    def test_no_git(self):
        plain = self.d / "plain"
        g.write(plain, "docs/spec/project.json", {})
        self.assertEqual(pj.read_reviewed_project_json(plain)[1], "no-git")


class StateDir(Base):
    def test_git_common_dir_0700(self):
        repo = g.init(self.d / "repo")
        d = pj.state_dir(repo)
        self.assertEqual(d, Path(os.path.realpath(str(repo / ".git"))) / "karvey")
        self.assertEqual(stat.S_IMODE(d.stat().st_mode), 0o700)

    def test_worktree_shares_state_dir(self):
        repo = g.init(self.d / "repo")
        g.commit_all(repo)
        g.run(["worktree", "add", "-q", "-b", "feature/y", str(self.d / "wt")], repo)
        self.assertEqual(pj.state_dir(self.d / "wt"), pj.state_dir(repo))

    def test_xdg_fallback(self):
        plain = self.d / "plain"
        plain.mkdir()
        xdg = self.d / "xdg"
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(xdg)}):
            d = pj.state_dir(plain)
        self.assertEqual(d.parent, xdg / "karvey")
        self.assertEqual(len(d.name), 16)
        self.assertEqual(stat.S_IMODE(d.stat().st_mode), 0o700)
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(xdg)}):
            self.assertEqual(pj.state_dir(plain), d)  # stable per realpath

    def test_no_create(self):
        repo = g.init(self.d / "repo")
        d = pj.state_dir(repo, create=False)
        self.assertFalse(d.exists())


if __name__ == "__main__":
    unittest.main()
