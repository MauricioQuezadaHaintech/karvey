"""karvey-handoff-capture.py writes state.json by measuring (E1.F6.T3, REQ-W1-048)."""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import unittest

import _gitrepo as g
import _path
from karvey_lib import karvey_hooks as kh

_spec = importlib.util.spec_from_file_location("handoff_capture", str(_path.SCRIPTS_DIR / "karvey-handoff-capture.py"))
hc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hc)


def git_out(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), stdout=subprocess.PIPE, check=True).stdout.decode().strip()


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = hc.main(list(argv))
    return code, out.getvalue()


class Capture(unittest.TestCase):
    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = self.t.path / "myrepo"
        g.init(self.root)
        g.write(self.root, "docs/spec/team.json", {"ops_repo": "myrepo", "roles": {"myrepo": "ceo"}})
        g.write(self.root, "docs/spec/agents/ceo/handoff.md", "H\n")
        g.commit_all(self.root)
        g.write(self.root, "dirty.txt", "x")
        self.profile = self.root / "docs/spec/agents/ceo"

    def tearDown(self):
        self.t.cleanup()

    def state(self):
        return json.loads((self.profile / "state.json").read_text())

    def test_values_equal_git_and_in_repo_team_writes_the_repo_name(self):
        porcelain = [x for x in git_out(self.root, "status", "--porcelain").splitlines() if x]
        code, _ = run("--profile", str(self.profile))
        self.assertEqual(code, 0)
        st = self.state()
        self.assertEqual(len(st["repos"]), 1)
        r = st["repos"][0]
        self.assertEqual(r["path"], "myrepo")  # the repo name, resolved by the BUG-20 rule
        self.assertTrue(r["measured"])
        self.assertEqual(r["branch"], git_out(self.root, "rev-parse", "--abbrev-ref", "HEAD"))
        self.assertEqual(r["commit"], git_out(self.root, "log", "-1", "--pretty=%h"))
        # the tree as it is once state.json (inside the repo) exists: the session hook compares this
        self.assertEqual(r["uncommitted"], len(porcelain) + 1)
        self.assertIn("saved_at", st)

    def test_the_session_hook_reads_what_it_writes(self):
        run("--profile", str(self.profile))
        lines, drift = kh.live_state(str(self.profile / "state.json"), str(self.root))
        self.assertFalse(drift, lines)
        self.assertIn("matches", lines[0])

    def test_unmeasurable_repo_is_recorded_not_invented(self):
        g.write(self.root, "docs/spec/agents/ceo/state.json",
                {"repos": [{"path": "myrepo"}, {"path": "/nonexistent/other"}, {"path": str(self.t.path / "plain")}]})
        (self.t.path / "plain").mkdir()
        code, out = run("--profile", str(self.profile), "--repos-from", "state")
        self.assertEqual(code, 0)
        repos = {r["path"]: r for r in self.state()["repos"]}
        self.assertTrue(repos["myrepo"]["measured"])
        for p in ("/nonexistent/other", str(self.t.path / "plain")):
            self.assertFalse(repos[p]["measured"])
            self.assertIn("reason", repos[p])
            self.assertNotIn("branch", repos[p])
        self.assertIn("NOT MEASURED", out)
        lines, drift = kh.live_state(str(self.profile / "state.json"), str(self.root))
        self.assertTrue(drift)
        self.assertTrue(any("not measured at save" in x for x in lines))

    def test_worktree_is_measured(self):
        wt = self.t.path / "wt"
        g.run(["worktree", "add", "-q", "-b", "wtb", str(wt)], self.root)
        g.write(self.root, "docs/spec/agents/ceo/state.json", {"repos": [{"path": str(wt)}]})
        run("--profile", str(self.profile), "--repos-from", "state")
        r = self.state()["repos"][0]
        self.assertTrue(r["measured"], r)
        self.assertEqual(r["branch"], "wtb")

    def test_sibling_repo_is_recorded_relative(self):
        sib = g.init(self.t.path / "api")
        g.commit_all(sib)
        g.write(self.root, "docs/spec/team.json", {"ops_repo": "myrepo", "roles": {"myrepo": "ceo", "api": "ceo"}})
        run("--profile", str(self.profile), "--repos-from", "team")
        repos = {r["path"]: r for r in self.state()["repos"]}
        self.assertTrue(repos["../api"]["measured"])
        lines, _ = kh.live_state(str(self.profile / "state.json"), str(self.root))
        self.assertFalse(any("NOT FOUND" in x for x in lines), lines)

    def test_options_and_dry_run(self):
        code, out = run("--profile", str(self.profile), "--scheduled-tasks", "3", "--ready-to-rotate", "--dry-run",
                        "--json")
        self.assertEqual(code, 0)
        env = json.loads(out)
        self.assertEqual(env["tool"], "karvey-handoff-capture")
        self.assertFalse(env["result"]["written"])
        self.assertEqual(env["result"]["state"]["scheduled_tasks"], 3)
        self.assertTrue(env["result"]["state"]["ready_to_rotate"])
        self.assertFalse((self.profile / "state.json").exists())

    def test_missing_profile_exits_4_and_usage_exits_2(self):
        self.assertEqual(run("--profile", str(self.t.path / "nope"))[0], 4)
        self.assertEqual(run()[0], 2)
        self.assertEqual(run("--profile", str(self.profile), "--repos-from", "bogus")[0], 2)
        self.assertEqual(run("--profile", str(self.profile), "--scheduled-tasks", "-1")[0], 2)

    def test_no_shell_true(self):
        src = (_path.SCRIPTS_DIR / "karvey-handoff-capture.py").read_text() + \
            (_path.SCRIPTS_DIR / "karvey_lib" / "livestate.py").read_text()
        self.assertNotIn("shell=True", src)
        self.assertNotIn("os.system", src)


if __name__ == "__main__":
    unittest.main()
