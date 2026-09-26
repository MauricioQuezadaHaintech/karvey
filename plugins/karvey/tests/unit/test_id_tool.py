"""karvey-id.py: the next free ID under a lock (architecture §1.14 C-16 of wave2-structural).

@req REQ-W2-070 REQ-W2-071 REQ-W2-081
"""
import json
import os
import subprocess
import sys
import unittest

import _path
import _gitrepo as g

g.isolate_git()
ID = str(_path.SCRIPTS_DIR / "karvey-id.py")


def run(root, *argv, env=None):
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run([sys.executable, ID, "next"] + list(argv) + ["--root", str(root), "--json"], cwd=str(root),
                       capture_output=True, text=True, timeout=60, env=e)
    return p.returncode, json.loads(p.stdout)


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        g.write(self.root, "docs/spec/project.json", {"repos": ["acme-app"], "spec_repo": "acme-app"})
        g.write(self.root, "docs/bugs_dev_testing.md", "# Bugs\n\n## BUG-03 — a\n## BUG-07 — b\n")
        g.commit_all(self.root, "base")

    def tearDown(self):
        self.t.cleanup()


class Next(Base):
    def test_max_plus_one_and_reserved(self):
        c, env = run(self.root, "BUG")
        self.assertEqual((c, env["result"]["id"]), (0, "BUG-08"))
        c, env = run(self.root, "BUG")
        self.assertEqual(env["result"]["id"], "BUG-09")  # the clone-local reservation counts

    def test_REQ_W2_070_two_processes_at_once_get_different_numbers(self):
        procs = [subprocess.Popen([sys.executable, ID, "next", "BUG", "--root", str(self.root)], cwd=str(self.root),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        outs = [p.communicate(timeout=60)[0].strip() for p in procs]
        self.assertEqual([p.returncode for p in procs], [0, 0])
        self.assertEqual(sorted(outs), ["BUG-08", "BUG-09"])

    def test_REQ_W2_070_lock_held_exit_3_no_number(self):
        lock = self.root / ".git/karvey/ids.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("999")
        c, env = run(self.root, "BUG", env={"KARVEY_ID_LOCK_WAIT_S": "0.2"})
        self.assertEqual(c, 3)
        self.assertNotIn("id", env["result"] or {})
        self.assertIn("held by another process", env["errors"][0]["message"])

    def test_REQ_W2_070_remote_branch_only_counts(self):
        g.with_origin(self.root)
        g.run(["checkout", "-q", "-b", "other"], self.root)
        g.write(self.root, "docs/bugs_dev_testing.md", "# Bugs\n\n## BUG-12 — elsewhere\n")
        g.commit_all(self.root, "bug 12")
        g.run(["push", "-q", "origin", "other"], self.root)
        g.run(["checkout", "-q", "main"], self.root)
        g.run(["branch", "-q", "-D", "other"], self.root)
        c, env = run(self.root, "BUG")
        self.assertEqual(env["result"]["id"], "BUG-13")

    def test_REQ_W2_071_qualified(self):
        c, env = run(self.root, "BUG", "--qualified")
        self.assertEqual(env["result"]["id"], "BUG-08@acme-app")

    def test_REQ_W2_081_decisions_per_period_files_counted(self):
        g.write(self.root, "docs/spec/decisions.md", "## D-04 — x\n")
        g.write(self.root, "docs/spec/decisions/2026-09.md", "| D-21 | y |\n")
        c, env = run(self.root, "D")
        self.assertEqual(env["result"]["id"], "D-22")

    def test_findings_are_per_change(self):
        g.write(self.root, "docs/spec/changes/feat-a/findings.md", "| F-05 | x |\n")
        g.write(self.root, "docs/spec/changes/feat-b/findings.md", "| F-40 | x |\n")
        self.assertEqual(run(self.root, "F", "--change", "feat-a")[1]["result"]["id"], "F-06")
        c, env = run(self.root, "F")
        self.assertEqual(c, 3)


def load_id():
    import importlib.util
    spec_ = importlib.util.spec_from_file_location("karvey_id_mod", ID)
    m = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(m)
    return m


class Bug60(Base):
    """BUG-60 (finding F-21): branch scan boundary, --qualified burning a number, corrupt ids.json, lock race.

    @req REQ-W2-070 REQ-W2-071
    """

    def test_BUG_60_branch_scan_applies_the_word_boundary(self):
        """BUG-60 a: ``HEAD-977`` on a branch is not ``D-977``."""
        g.write(self.root, "docs/spec/decisions.md", "## D-04 — x (see HEAD-977, XD-500)\n")
        g.commit_all(self.root, "decisions")
        c, env = run(self.root, "D")
        self.assertEqual((c, env["result"]["id"], env["result"]["max_refs"]), (0, "D-05", 4))

    def test_BUG_60_qualified_refusal_burns_no_number(self):
        """BUG-60 b: an unsafe repo slug is refused before any number is reserved."""
        g.write(self.root, "docs/spec/project.json", {"repos": ["bad slug!"], "spec_repo": "x"})
        c, env = run(self.root, "BUG", "--qualified")
        self.assertEqual(c, 3)
        self.assertIn("not a safe repo slug", env["errors"][0]["message"])
        c, env = run(self.root, "BUG")
        self.assertEqual((c, env["result"]["id"]), (0, "BUG-08"))

    def test_BUG_60_corrupt_ids_json_is_rebuilt_not_exit_5(self):
        """BUG-60 c: a list, or a non-list/non-int under a kind, is corrupt: rebuilt from the scan, kept aside."""
        sd = self.root / ".git/karvey"
        sd.mkdir(parents=True, exist_ok=True)
        for bad in ([1, 2], {"BUG": 5}, {"BUG": [{"n": "x"}, 3]}):
            (sd / "ids.json").write_text(json.dumps(bad))
            c, env = run(self.root, "BUG")
            self.assertEqual(c, 0, env)
            self.assertIn("ids.json", " ".join(env["result"]["notes"]))
            data = json.loads((sd / "ids.json").read_text())
            self.assertIsInstance(data, dict)
        self.assertTrue(list(sd.glob("ids.json.corrupt-*")))

    def test_BUG_60_release_deletes_only_its_own_lock(self):
        """BUG-60 d: a lock taken over by another process is not deleted on release."""
        m = load_id()
        path = self.t.path / "ids.lock"
        with m.Lock(path, 30):
            self.assertIn(str(os.getpid()), path.read_text())
            path.write_text("4242 other-token\n")  # another process took it over
        self.assertEqual(path.read_text(), "4242 other-token\n")
        with m.Lock(self.t.path / "own.lock", 30):
            pass
        self.assertFalse((self.t.path / "own.lock").exists())

    def test_BUG_60_stale_takeover_moves_the_stale_lock_aside(self):
        """BUG-60 d: a stale lock is renamed away atomically, then the new lock is ours."""
        m = load_id()
        path = self.t.path / "ids.lock"
        path.write_text("999 old\n")
        os.utime(str(path), (1, 1))
        with m.Lock(path, 30) as lk:
            self.assertEqual(path.read_text().split()[1], lk.token)
        self.assertEqual(sorted(p.name for p in self.t.path.iterdir() if "lock" in p.name), [])

    def test_BUG_60_takeover_does_not_steal_a_fresh_lock(self):
        """BUG-60 d: if the file renamed aside is not the stale one judged, it is put back."""
        m = load_id()
        path = self.t.path / "ids.lock"
        path.write_text("777 fresh\n")  # another waiter's new lock, created after we judged "999 old" stale
        lk = m.Lock(path, 30)
        self.assertFalse(lk._take_over_stale("999 old\n"))
        self.assertEqual(path.read_text(), "777 fresh\n")


if __name__ == "__main__":
    unittest.main()
