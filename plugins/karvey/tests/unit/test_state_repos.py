"""REQ-HF-005, 006, 009, 030 (BUG-144): spec.json repos, binding a declared repo's commit, the refusal text."""
import json
import unittest

import _path  # noqa: F401
from test_state_approve import Base
from karvey_lib import approval as ap

SHA_API = "a" * 40


class Repos(Base):
    def declare(self, repos):
        d = self.read()
        d["repos"] = repos
        self.f.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")

    def approve_prod(self):
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod", session_id="s1")
        c, env = self.st("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20")
        self.assertEqual(c, 0, env)

    def bind(self, repo, sha=SHA_API):
        return self.st("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20",
                       "--repo", repo, "--sha", sha)

    def test_validate_repos(self):
        self.declare(["app-web", "app-api"])
        c, env = self.st("validate", str(self.f))
        self.assertEqual(c, 0, env)
        for bad in ("app-api", [""], []):
            self.declare(bad)
            c, env = self.st("validate", str(self.f))
            self.assertTrue(any("repos" in (i.get("path") or "") for i in env["errors"]), (bad, env))

    def test_bind_and_check(self):
        self.declare(["app-web", "app-api"])
        self.approve_prod()
        exp = ap.read_ledger(self.root, "feat-a")[0]["prod"]["expires_at"]
        c, env = self.bind("app-api")
        self.assertEqual(c, 0, env)
        prod = ap.read_ledger(self.root, "feat-a")[0]["prod"]
        self.assertEqual((prod["repos"], prod["expires_at"]), ({"app-api": SHA_API}, exp))
        c, env = self.bind("app-api")  # idempotent
        self.assertEqual(c, 0, env)
        c, env = self.st("check-prod", "feat-a", "--repo", "app-api", "--sha", SHA_API)
        self.assertEqual(c, 0, env)
        c, env = self.st("check-prod", "feat-a", "--repo", "app-api", "--sha", "b" * 40)
        self.assertNotEqual(c, 0)
        self.assertIn("repo", env["result"]["missing"])

    def test_bind_refusals(self):
        self.declare(["app-web", "app-api"])
        c, env = self.bind("app-api")
        self.assertEqual(c, 3, env)  # no approval yet
        self.approve_prod()
        for repo, sha, needle in (("app-mobile", SHA_API, "not declared"), ("app-api", "abc123", "full commit id")):
            c, env = self.bind(repo, sha)
            self.assertEqual(c, 3, env)
            self.assertIn(needle, env["errors"][0]["message"])
        self.assertEqual(self.bind("app-api")[0], 0)
        c, env = self.bind("app-api", "b" * 40)
        self.assertEqual(c, 3, env)
        self.assertIn("new OK", env["errors"][0]["message"])
        self.assertEqual(ap.read_ledger(self.root, "feat-a")[0]["prod"]["repos"], {"app-api": SHA_API})

    def test_check_prod_without_binding_names_repo(self):
        self.declare(["app-web", "app-api"])
        self.approve_prod()
        c, env = self.st("check-prod", "feat-a", "--repo", "app-api", "--sha", SHA_API)
        self.assertNotEqual(c, 0)
        self.assertEqual(env["result"]["missing"], ["repo"])


class Refusal(Base):
    def test_refusal_lists_markers_and_missing_piece(self):
        ap.write_marker(self.root, "plan", "feat-a", "aprobado", session_id="s1")
        ap.write_marker(self.root, "prod", "feat-b", "ok, merge a prod feat-b", session_id="s1",
                        now=ap.now_dt() - ap.timedelta(minutes=600))
        env = self.refused(("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20"),
                           "found: ")
        msg = env["errors"][0]["message"]
        self.assertIn("plan feat-a 0 min (live)", msg)
        self.assertIn("prod feat-b 600 min (expired)", msg)
        self.assertIn("missing: a live prod marker for feat-a", msg)
        self.assertIn("aprobado para producción feat-a PR #<n> v<version>", msg)

    def test_refusal_with_no_marker(self):
        env = self.refused(("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20"),
                           "found: no approval marker")
        self.assertIn("missing: a live prod marker for feat-a", env["errors"][0]["message"])


if __name__ == "__main__":
    unittest.main()
