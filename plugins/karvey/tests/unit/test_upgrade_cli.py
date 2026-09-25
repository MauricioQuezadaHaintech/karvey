"""commit (library level) and the karvey-upgrade.py CLI (REQ-UP-013, 018, 028)."""
import subprocess
import unittest

import _gitrepo as g
import _path  # noqa: F401
from karvey_lib import upgrade
from test_upgrade_apply import INSTALLED, REG, appender


class CommitLibrary(unittest.TestCase):
    UB = "chore/karvey-upgrade-" + INSTALLED

    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "proj")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"}})
        g.write(self.root, "notes.txt", "hello\n")
        g.commit_all(self.root)
        self.steps = [appender("a", "A"), appender("b", "B", file="b.txt")]
        upgrade.write_seen(self.root, "3.12.0", "accepted")
        rep = upgrade.apply(self.root, ["a", "b"], steps=self.steps, registry=REG, installed=INSTALLED, dry_run=True)
        rep = upgrade.apply(self.root, ["a", "b"], steps=self.steps, registry=REG, installed=INSTALLED,
                            preview=rep.preview)
        self.assertEqual(rep.applied, ["a", "b"])

    def tearDown(self):
        self.t.cleanup()

    def git(self, *args):
        return subprocess.run(["git"] + list(args), cwd=str(self.root), capture_output=True, text=True).stdout

    def test_message_and_pr_text(self):
        res = upgrade.commit(self.root, "The Owner", picked_at="2026-09-25T10:00:00-03:00",
                             answer="yes,\tgo ahead\n" + "x" * 300, trailers=["Co-Authored-By=An Agent <a.invalid>"],
                             installed=INSTALLED)
        msg = self.git("log", "-1", "--format=%B")
        self.assertTrue(msg.startswith("chore(karvey): project upgrade 3.12.0 → %s\n\n" % INSTALLED))
        self.assertIn("Steps: a, b\n", msg)
        self.assertIn("Picked-by: The Owner\n", msg)
        self.assertIn("Picked-at: 2026-09-25T10:00:00-03:00\n", msg)
        answer = [line for line in msg.splitlines() if line.startswith("Answer: ")][0]
        self.assertNotIn("\t", answer)
        self.assertLessEqual(len(answer), len('Answer: ""') + upgrade.ANSWER_MAX)
        self.assertIn("\nCo-Authored-By: An Agent <a.invalid>", msg)
        self.assertEqual(res["pr_title"], "chore(karvey): project upgrade 3.12.0 → %s" % INSTALLED)
        self.assertIn("Steps applied: a, b", res["pr_body"])
        self.assertIn("never merges", res["pr_body"])
        self.assertEqual(res["branch"], self.UB)
        self.assertEqual(res["sha"], self.git("rev-parse", "HEAD").strip())

    def test_stages_exactly_the_journal_files(self):
        g.write(self.root, "stray.txt", "not mine\n")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"},
                                                      "x": 1})
        upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        files = sorted(self.git("show", "--name-only", "--format=", "HEAD").split())
        self.assertEqual(files, ["b.txt", "notes.txt"])
        status = self.git("status", "--porcelain")
        self.assertIn("stray.txt", status)
        self.assertIn("docs/spec/project.json", status)

    def test_refused_on_integration_or_production(self):
        g.run(["checkout", "-q", "main"], self.root)
        with self.assertRaises(upgrade.Refused) as cm:
            upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        self.assertIn("commit refused on main", str(cm.exception))

    def test_refused_on_a_branch_the_journal_does_not_name(self):
        g.run(["checkout", "-q", "-b", "other"], self.root)
        with self.assertRaises(upgrade.Refused) as cm:
            upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        self.assertIn("the journal belongs to " + self.UB, str(cm.exception))

    def test_picked_by_required_and_trailers_checked(self):
        with self.assertRaises(upgrade.Refused):
            upgrade.commit(self.root, "  \n", installed=INSTALLED)
        with self.assertRaises(upgrade.Refused):
            upgrade.commit(self.root, "The Owner", trailers=["no equals sign"], installed=INSTALLED)

    def test_nothing_left_to_commit(self):
        upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        with self.assertRaises(upgrade.Refused) as cm:
            upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        self.assertIn("nothing to commit", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
