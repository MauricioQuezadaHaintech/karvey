"""D-55 (BUG-167): no production without a QA review of the released commit.

The owner: «no podemos pasar a prod sin un proceso de qa. el pr de prod debe obligadamente tener un proceso de qa».
Until 3.13.3 the prod-gate asked only for the human's approval: a hotfix lane skipped karvey-qa, and a follow-up
commit of an approved change reached production without anyone reviewing it. Now ``check-prod`` (the gate's
question) also needs a QA review recorded with ``qa-pass`` for the released commit — or for an ancestor whose delta
touches only docs. The agent runs the review and records it; the human is not asked."""
import unittest

import _path  # noqa: F401
import _gitrepo as g
from _state import qa_reviewed
from karvey_lib import approval as ap
from test_state_approve import Base, head


class QaBeforeProd(Base):
    def approve(self):
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod", session_id="s9")
        c, env = self.st("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20")
        self.assertEqual(c, 0, env)

    def test_an_approved_release_without_qa_is_not_released(self):
        self.approve()
        c, env = self.st("check-prod", "feat-a", "--sha", head(self.root))
        self.assertEqual(c, 1, env)
        self.assertEqual(env["result"]["missing"], ["qa"])
        self.assertIn("qa-pass feat-a --sha %s" % head(self.root), env["result"]["reason"])
        self.assertIn("the human is not asked", env["result"]["reason"])

    def test_a_qa_review_of_the_released_commit_releases_it(self):
        self.approve()
        c, env = qa_reviewed(self.root, "feat-a", head(self.root))
        self.assertEqual(c, 0, env)
        c, env = self.st("check-prod", "feat-a", "--sha", head(self.root))
        self.assertEqual(c, 0, env)

    def test_a_code_commit_after_the_review_needs_its_own_review(self):
        self.approve()
        reviewed = head(self.root)
        qa_reviewed(self.root, "feat-a", reviewed)
        g.write(self.root, "src/app.py", "x = 1\n")
        g.commit_all(self.root, "follow-up code")
        self.st("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20", "--sha", "HEAD")
        c, env = self.st("check-prod", "feat-a", "--sha", head(self.root))
        self.assertEqual(env["result"]["missing"], ["qa"], env)
        qa_reviewed(self.root, "feat-a", head(self.root))
        c, env = self.st("check-prod", "feat-a", "--sha", head(self.root))
        self.assertEqual(c, 0, env)

    def test_a_docs_only_commit_after_the_review_is_covered(self):
        self.approve()
        qa_reviewed(self.root, "feat-a", head(self.root))
        g.write(self.root, "docs/notes.md", "n\n")
        g.write(self.root, "CHANGELOG.md", "c\n")
        g.commit_all(self.root, "docs")
        self.st("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20", "--sha", "HEAD")
        c, env = self.st("check-prod", "feat-a", "--sha", head(self.root))
        self.assertEqual(c, 0, env)


class QaPassRefusals(Base):
    def test_open_blocking_findings_are_refused(self):
        c, env = qa_reviewed(self.root, "feat-a", head(self.root), open_blocking=2)
        self.assertEqual(c, 3, env)
        self.assertIn("2 open blocking findings", env["errors"][0]["message"])

    def test_a_review_of_another_commit_is_refused(self):
        rel = "docs/spec/changes/feat-a/qa/REVISION_PR_2.md"
        g.write(self.root, rel, "- Reviewed commit: %s\n- Open blocking findings (critical/high): 0\n" % ("a" * 40))
        c, env = self.st("qa-pass", "feat-a", "--sha", "HEAD", "--review", rel)
        self.assertEqual(c, 3, env)
        self.assertIn("does not name the reviewed commit", env["errors"][0]["message"])

    def test_a_review_outside_the_change_is_refused(self):
        g.write(self.root, "REVIEW.md", "- Reviewed commit: %s\n- Open blocking findings: 0\n" % head(self.root))
        c, env = self.st("qa-pass", "feat-a", "--sha", "HEAD", "--review", "REVIEW.md")
        self.assertEqual(c, 3, env)
        self.assertIn("qa/", env["errors"][0]["message"])


if __name__ == "__main__":
    unittest.main()
