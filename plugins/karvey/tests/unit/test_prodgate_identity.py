"""BUG-145 (QA of 3.12.1, F-12): the "not a Karvey repo" warning must not be reachable for a Karvey target."""
import os
import unittest

import _gitrepo as g
from _prodgate import World

GUID = "0f6a1c52-6d7e-4c4b-9a52-2b2f0c1d9e11"


class Identity(World):
    def setUp(self):
        super().setUp()
        self.web = self.clone("app-web", changes={"feat-a": {}}, remote_url="git@github.com:org/app-web.git",
                              project_extra={"repos": ["app-web", "app-mobile"]})
        self.h = self.head(self.web)

    def test_look_alike_clone_in_the_cwd_does_not_bypass(self):
        fake = g.init(self.base / "elsewhere" / "f")
        g.commit_all(fake)
        g.run(["remote", "add", "origin", "git@github.com:org/app-web.git"], fake)
        self.gh_pr("main", "feature/feat-a", self.h)
        self.assertBlock(self.run_gate("gh pr merge 12 --repo org/app-web", fake, project_dir=self.web))

    def test_look_alike_sibling_does_not_shadow_the_real_clone(self):
        fake = g.init(self.base / "aaa-fake")
        g.commit_all(fake)
        g.run(["remote", "add", "origin", "git@github.com:org/app-api.git"], fake)
        api = self.clone("app-api", changes={"api-login": {}}, remote_url="git@github.com:org/app-api.git")
        h = self.head(api)
        self.gh_pr("main", "feature/api-login", h)
        self.assertBlock(self.run_gate("gh pr merge 12 --repo org/app-api", self.web), "change=api-login")
        self.approve(api, "api-login", h)
        self.assertAllow(self.run_gate("gh pr merge 12 --repo org/app-api", self.web), "change=api-login")

    def test_renamed_repo_is_identified_by_the_host(self):
        self.gh_pr("main", "feature/feat-a", self.h, url="https://github.com/org/app-web/pull/12")
        self.assertBlock(self.run_gate("gh pr merge 12 -R org/old-app-web", self.web), "change=feat-a")

    def test_fork_upstream_is_identified_by_the_head_commit(self):
        self.gh_pr("main", "feature/feat-a", self.h, url="https://github.com/upstream/app-core/pull/12")
        self.assertBlock(self.run_gate("gh pr merge 12 --repo upstream/app-core", self.web), "change=feat-a")

    def test_azure_repo_guid_is_resolved_by_the_host(self):
        self.answer(("az", "repos", "pr", "show"), {"targetRefName": "refs/heads/main",
                                                    "sourceRefName": "refs/heads/feature/feat-a", "title": "x",
                                                    "lastMergeSourceCommit": {"commitId": self.h},
                                                    "repository": {"name": "app-web", "id": GUID}})
        cmd = ("curl -X PATCH https://dev.azure.com/org/proj/_apis/git/repositories/%s/pullrequests/12 "
               "-d '{\"status\":\"completed\"}'" % GUID)
        self.assertBlock(self.run_gate(cmd, self.web), "change=feat-a")
        self.approve(self.web, "feat-a", self.h)
        self.assertAllow(self.run_gate(cmd, self.web), "change=feat-a")

    def test_session_in_the_folder_that_holds_the_repos(self):
        api = self.clone("app-api", changes={"api-login": {}})
        self.gh_pr("main", "feature/api-login", self.head(api))
        self.assertBlock(self.run_gate("gh pr merge 12 --repo org/app-api", self.base, project_dir=self.base),
                         "change=api-login")

    def test_named_repo_without_a_clone_passes_only_into_integration(self):
        self.gh_pr("prod", "feature/x", "c" * 40, url="https://github.com/org/app-mobile/pull/3")
        self.assertBlock(self.run_gate("gh pr merge 3 --repo org/app-mobile", self.web), "run it from the clone")
        self.cli = []
        self.gh_pr("dev", "feature/x", "c" * 40, url="https://github.com/org/app-mobile/pull/3")
        res = self.run_gate("gh pr merge 3 --repo org/app-mobile", self.web)
        self.assertAllow(res)
        self.assertNotIn("WARNING", res[1])


if __name__ == "__main__":
    unittest.main()
