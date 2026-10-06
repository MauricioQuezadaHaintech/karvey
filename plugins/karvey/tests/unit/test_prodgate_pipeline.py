"""REQ-HF-010, 012, 026 through the gate: REST completions and pipeline approvals."""
import unittest

from _prodgate import World, git_out
import _gitrepo as g

AZ = "https://dev.azure.com/org/proj/_apis/git/repositories/app-web/pullrequests/7"


class RestGate(World):
    def setUp(self):
        super().setUp()
        self.web = self.clone("app-web", changes={"feat-a": {}})
        self.h = self.head(self.web)
        self.answer(("az", "repos", "pr", "show"), {"targetRefName": "refs/heads/main",
                                                    "sourceRefName": "refs/heads/feature/feat-a", "title": "x",
                                                    "lastMergeSourceCommit": {"commitId": self.h}})

    def test_azure_completion_needs_the_approval(self):
        cmd = "curl -X PATCH %s -d '{\"status\":\"completed\"}'" % AZ
        self.assertBlock(self.run_gate(cmd, self.web), "change=feat-a")
        self.approve(self.web, "feat-a", self.h)
        self.assertAllow(self.run_gate(cmd, self.web), "change=feat-a")
        self.assertTrue(any("--org" in c[0] for c in self.calls))

    def test_github_merge_of_a_non_karvey_repo_warns(self):
        self.gh_pr("main", "x", "c" * 40, url="https://github.com/org/static-site/pull/3")
        res = self.run_gate("curl -X PUT https://api.github.com/repos/org/static-site/pulls/3/merge", self.web)
        self.assertAllow(res, "org/static-site is not a Karvey repo")

    def test_ref_write_into_production_blocks(self):
        self.assertBlock(self.run_gate("curl -X PATCH https://api.github.com/repos/org/app-web/git/refs/heads/main "
                                       "-d '{\"sha\":\"x\"}'", self.web), "merge through a PR")
        self.assertAllow(self.run_gate("curl -X PATCH https://api.github.com/repos/org/app-web/git/refs/heads/"
                                       "feature-x -d '{\"sha\":\"x\"}'", self.web))

    def test_unreadable_forms_block(self):
        self.assertBlock(self.run_gate("curl -X PATCH \"$URL\" -d '{\"status\":\"completed\"}'", self.web))


class Pipelines(World):
    def setUp(self):
        super().setUp()
        self.web = self.clone("app-web", changes={"feat-a": {}})
        g.run(["checkout", "-q", "-b", "feature/feat-a"], self.web)
        g.write(self.web, "x.txt", "x\n")
        g.commit_all(self.web, "feature")
        self.h = self.head(self.web)
        g.run(["checkout", "-q", "main"], self.web)
        g.run(["merge", "-q", "--no-ff", "-m", "merge", "feature/feat-a"], self.web)
        self.m = self.head(self.web)
        self.cmd = ("curl -X PATCH 'https://dev.azure.com/org/proj/_apis/pipelines/approvals?api-version=7.1' "
                    "-d '[{\"approvalId\":\"ab-1\",\"status\":\"approved\"}]'")
        self.answer(("az", "rest"), {"id": "ab-1", "pipeline": {"owner": {"id": 77}}})

    def run_of(self, branch, sha):
        self.answer(("az", "pipelines", "runs", "show"), {"id": 77, "sourceBranch": "refs/heads/" + branch,
                                                          "sourceVersion": sha, "repository": {"name": "app-web"}})

    def test_merge_of_the_approved_head_passes(self):
        self.approve(self.web, "feat-a", self.h)
        self.run_of("main", self.m)
        self.assertAllow(self.run_gate(self.cmd, self.web), "change=feat-a")

    def test_without_approval_blocks(self):
        self.run_of("main", self.m)
        self.assertBlock(self.run_gate(self.cmd, self.web))

    def test_unrelated_commit_blocks(self):
        self.approve(self.web, "feat-a", "b" * 40)
        self.run_of("main", self.m)
        self.assertBlock(self.run_gate(self.cmd, self.web))

    def test_integration_run_passes(self):
        self.run_of("dev", self.m)
        self.assertAllow(self.run_gate(self.cmd, self.web))

    def test_unresolved_run_blocks(self):
        self.cli = []
        self.answer(("az", "rest"), err="az exited 1")
        self.assertBlock(self.run_gate(self.cmd, self.web), "cannot resolve")

    def test_github_pending_deployment(self):
        self.approve(self.web, "feat-a", self.h)
        self.answer(("gh", "api"), {"head_branch": "main", "head_sha": self.m})
        self.assertAllow(self.run_gate("gh api -X POST repos/org/app-web/actions/runs/99/pending_deployments "
                                       "-f state=approved", self.web), "change=feat-a")

    def test_classic_release_approval_blocks(self):
        self.assertBlock(self.run_gate("curl -X PATCH https://vsrm.dev.azure.com/org/proj/_apis/release/approvals/5 "
                                       "-d '{\"status\":\"approved\"}'", self.web))


if __name__ == "__main__":
    unittest.main()
