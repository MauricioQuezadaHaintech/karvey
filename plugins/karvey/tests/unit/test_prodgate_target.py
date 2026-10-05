"""REQ-HF-014, 024..026 (BUG-141): the prod-gate decides on the PR's own repo and base, not the session's cwd."""
import unittest

from _prodgate import World


class Target(World):
    def setUp(self):
        super().setUp()
        # the session's repo: trunk flow, and its origin/HEAD is `dev` (as on hosts that default to it)
        self.web = self.clone("app-web", flow={"feature_prefix": "feature/", "integration": "main",
                                               "production": "main"},
                              project_extra={"repos": ["app-web", "app-api", "app-mobile"]}, origin_head="dev")
        self.api = self.clone("app-api", changes={"api-login": {}})
        self.h = self.head(self.api)

    def test_merge_into_the_target_integration_branch_passes(self):
        self.gh_pr("dev", "feature/api-login", self.h)
        res = self.run_gate("gh pr merge 30 --repo org/app-api", self.web)
        self.assertAllow(res)
        self.assertNotIn("WARNING", res[1])

    def test_production_merge_is_checked_on_the_target_ledger(self):
        self.approve(self.api, "api-login", self.h)
        self.gh_pr("main", "feature/api-login", self.h)
        self.assertAllow(self.run_gate("gh pr merge 12 --repo org/app-api", self.web), "change=api-login")

    def test_production_merge_without_the_target_approval_blocks(self):
        self.gh_pr("main", "feature/api-login", self.h)
        self.assertBlock(self.run_gate("gh pr merge 12 --repo org/app-api", self.web), "change=api-login")

    def test_pr_url_selector_names_the_target(self):
        self.approve(self.api, "api-login", self.h)
        self.gh_pr("main", "feature/api-login", self.h)
        self.assertAllow(self.run_gate("gh pr merge https://github.com/org/app-api/pull/12", self.web),
                         "change=api-login")

    def test_non_karvey_target_passes_with_a_warning(self):
        self.gh_pr("main", "feature/x", "c" * 40)
        res = self.run_gate("gh pr merge 3 --repo org/static-site", self.web)
        self.assertAllow(res, "org/static-site is not a Karvey repo")

    def test_named_karvey_repo_without_a_clone_blocks(self):
        self.gh_pr("main", "feature/x", "c" * 40)
        self.assertBlock(self.run_gate("gh pr merge 3 --repo org/app-mobile", self.web), "run it from the clone")

    def test_host_answer_for_another_repo_blocks(self):
        self.approve(self.api, "api-login", self.h)
        self.gh_pr("main", "feature/api-login", self.h, url="https://github.com/org/app-other/pull/12")
        self.assertBlock(self.run_gate("gh pr merge 12 --repo org/app-api", self.web), "disagree")

    def test_outside_a_repo_is_tied_to_the_named_clone(self):
        outside = self.base / "scratch"
        outside.mkdir()
        self.approve(self.api, "api-login", self.h)
        self.gh_pr("main", "feature/api-login", self.h)
        self.assertAllow(self.run_gate("gh pr merge 12 -R org/app-api", outside, project_dir=self.web),
                         "change=api-login")


if __name__ == "__main__":
    unittest.main()
