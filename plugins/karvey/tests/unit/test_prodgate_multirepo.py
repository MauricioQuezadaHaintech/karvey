"""REQ-HF-007, 008: a declared repo's [Deploy] <id> PR is released under the owning repo's approval."""
import unittest

from _prodgate import World
from karvey_lib import approval


class MultiRepo(World):
    def setUp(self):
        super().setUp()
        self.api = self.clone("app-api")
        self.h_api = self.head(self.api)

    def owner(self, repos=("app-web", "app-api"), bind=True):
        web = self.clone("app-web", changes={"project-upgrade": {"repos": list(repos)}})
        self.approve(web, "project-upgrade", self.head(web))
        if bind:
            led = approval.read_ledger(web, "project-upgrade")[0]["prod"]
            led["repos"] = {"app-api": self.h_api}
            approval.record_prod(web, "project-upgrade", led)
        return web

    def merge(self):
        self.gh_pr("main", "feature/project-upgrade", self.h_api, title="[Deploy] project-upgrade")
        return self.run_gate("gh pr merge 12", self.api)

    def test_bound_repo_is_released_and_the_line_names_the_owner(self):
        web = self.owner()
        res = self.merge()
        self.assertAllow(res, "change=project-upgrade")
        self.assertIn(str(web), res[1])

    def test_unbound_repo_blocks_with_the_command_to_run_in_the_owner(self):
        web = self.owner(bind=False)
        res = self.merge()
        self.assertBlock(res, "approve project-upgrade prod --by")
        self.assertIn("--repo app-api --sha %s" % self.h_api, res[2])
        self.assertIn(str(web), res[2])

    def test_undeclared_repo_blocks(self):
        self.owner(repos=("app-web",))
        self.assertBlock(self.merge(), "does not declare")

    def test_owner_not_found_says_where_it_looked(self):
        res = self.merge()
        self.assertBlock(res, "looked in")
        self.assertIn("project.json repos", res[2])


if __name__ == "__main__":
    unittest.main()
