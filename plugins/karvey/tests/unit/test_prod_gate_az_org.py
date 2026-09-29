import unittest
from unittest import mock

import _path  # noqa: F401
from karvey_lib import guards as gd


class AzPrLookupKeepsTheOrganization(unittest.TestCase):
    """BUG-52: the PR lookup of `az repos pr update` must reach the organization the command names."""

    def _lookup(self, command):
        seg = mock.Mock(cwd=None, argv=command.split())
        a = seg.argv[1:]
        org = gd._opt(a, "--org", "--organization")
        c = gd.Candidate("az", seg, selector=gd._opt(a, "--id"), repo_arg=["--org", org] if org else None)
        seen = {}

        def fake(argv, cwd, budget):
            seen["argv"] = argv
            return {"targetRefName": "refs/heads/dev", "sourceRefName": "refs/heads/fix/x", "title": "t"}, None
        with mock.patch.object(gd, "_run_cli", fake):
            gd.pr_info(c, None, 5)
        return seen["argv"]

    def test_org_is_forwarded(self):
        argv = self._lookup("az repos pr update --id 9 --status completed --org https://dev.azure.com/acme")
        self.assertEqual(argv[:5], ["az", "repos", "pr", "show", "--id"])
        self.assertIn("https://dev.azure.com/acme", argv)

    def test_organization_long_form_is_forwarded(self):
        argv = self._lookup("az repos pr update --id 9 --status completed --organization=https://dev.azure.com/acme")
        self.assertIn("https://dev.azure.com/acme", argv)

    def test_without_org_nothing_is_added(self):
        argv = self._lookup("az repos pr update --id 9 --status completed")
        self.assertEqual(argv, ["az", "repos", "pr", "show", "--id", "9", "--output", "json"])

    def test_prod_candidates_carries_the_org(self):
        seg = mock.Mock(cwd=None, argv0="az", argv="az repos pr update --id 9 --status completed --org https://dev.azure.com/acme".split())
        ctx = mock.Mock()
        ctx.parsed.segments = [seg]
        with mock.patch.object(gd, "git_targets", return_value=[]), \
                mock.patch.object(gd, "_wrapped_command", return_value=None):
            cands = [c for c in gd.prod_candidates(ctx) if c.kind == "az"]
        self.assertEqual(cands[0].repo_arg, ["--org", "https://dev.azure.com/acme"])


if __name__ == "__main__":
    unittest.main()
