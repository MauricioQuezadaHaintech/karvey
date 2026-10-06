"""REQ-HF-010..013, 015: REST and inline-script forms of a PR completion, a branch write or a pipeline approval."""
import json
import os
import tempfile
import unittest

import _path  # noqa: F401
from karvey_lib import restcalls as rc
from karvey_lib import shellparse

AZ = "https://dev.azure.com/org/proj/_apis/git/repositories/app-web/pullrequests/7?api-version=7.1"
SHA = "a" * 40


def calls(cmd, cwd=None):
    out = []
    for seg in shellparse.parse(cmd, cwd=cwd or "/").segments:
        c = rc.classify_segment(seg, cmd)
        if c is not None:
            out.append(c)
    return out


class Parse(unittest.TestCase):
    def one(self, cmd, cwd=None):
        cs = calls(cmd, cwd)
        self.assertEqual(len(cs), 1, cs)
        return cs[0]

    def test_azure_completion(self):
        c = self.one("curl -s -X PATCH '%s' -H 'Authorization: Basic x' -d '%s'" % (
            AZ, json.dumps({"status": "completed", "lastMergeSourceCommit": {"commitId": SHA}})))
        self.assertEqual((c.kind, c.host, c.repo, c.number, c.bound, c.deferred),
                         ("pr-complete", "azure", "app-web", "7", SHA, False))
        self.assertEqual(c.org, "https://dev.azure.com/org")

    def test_azure_auto_complete_is_deferred(self):
        c = self.one("curl -X PATCH %s --data '{\"autoCompleteSetBy\":{\"id\":\"x\"}}'" % AZ)
        self.assertTrue(c.deferred)

    def test_github_and_gitlab_merges(self):
        c = self.one("curl -X PUT https://api.github.com/repos/org/app-web/pulls/7/merge")
        self.assertEqual((c.kind, c.host, c.repo, c.number), ("pr-complete", "github", "org/app-web", "7"))
        c = self.one("curl --request PUT https://gitlab.example/api/v4/projects/org%2Fapp-web/merge_requests/3/merge")
        self.assertEqual((c.kind, c.host, c.repo, c.number), ("pr-complete", "gitlab", "org/app-web", "3"))
        c = self.one("http PUT https://api.github.com/repos/org/app-web/pulls/7/merge sha=%s" % SHA)
        self.assertEqual((c.kind, c.bound), ("pr-complete", SHA))

    def test_reads_and_non_completing_updates_are_not_candidates(self):
        for cmd in ("curl -s %s" % AZ.replace("?", "x?"), "curl -s '%s'" % AZ,
                    "curl -X PATCH '%s' -d '{\"title\":\"x\"}'" % AZ,
                    "curl -X PATCH '%s' -d '{\"status\":\"abandoned\"}'" % AZ,
                    "curl -X PATCH https://dev.azure.com/org/proj/_apis/pipelines/approvals "
                    "-d '[{\"approvalId\":\"1\",\"status\":\"rejected\"}]'",
                    "curl https://example.com/health", "wget -q https://example.com/x"):
            self.assertEqual(calls(cmd), [], cmd)

    def test_variables_unreadable_bodies_and_inline_scripts_fail(self):
        for cmd in ('curl -X PATCH "$URL" -d \'{"status":"completed"}\'',
                    'curl -X PATCH "https://dev.azure.com/org/proj/_apis/git/repositories/$R/pullrequests/7" -d x',
                    "curl -X PATCH '%s' -d @-" % AZ,
                    "curl -X PATCH '%s' -d @/nonexistent/body.json" % AZ,
                    "python3 -c \"import requests; requests.patch('%s', json={'status': 'completed'})\"" % AZ,
                    "node -e \"fetch('https://api.github.com/repos/o/r/pulls/7/merge',{method:'PUT'})\"",
                    "curl -X PATCH https://vsrm.dev.azure.com/org/proj/_apis/release/approvals/5 "
                    "-d '{\"status\":\"approved\"}'"):
            c = self.one(cmd)
            self.assertEqual(c.kind, "fail", cmd)
            self.assertTrue(c.reason)

    def test_readable_body_file(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "body.json"), "w") as fh:
                fh.write('{"title": "x"}')
            self.assertEqual(calls("curl -X PATCH '%s' -d @body.json" % AZ, cwd=d), [])
            with open(os.path.join(d, "body.json"), "w") as fh:
                fh.write('{"status": "completed"}')
            self.assertEqual(self.one("curl -X PATCH '%s' -d @body.json" % AZ, cwd=d).kind, "pr-complete")

    def test_ref_writes(self):
        c = self.one("curl -X PATCH https://api.github.com/repos/org/app-web/git/refs/heads/main -d '{\"sha\":\"x\"}'")
        self.assertEqual((c.kind, c.branch, c.repo), ("ref-write", "main", "org/app-web"))
        c = self.one("curl -X POST https://dev.azure.com/org/proj/_apis/git/repositories/app-web/refs "
                     "-d '[{\"name\":\"refs/heads/main\",\"oldObjectId\":\"0\",\"newObjectId\":\"1\"}]'")
        self.assertEqual((c.kind, c.branch), ("ref-write", "main"))

    def test_pipeline_approvals(self):
        c = self.one("curl -X PATCH 'https://dev.azure.com/org/proj/_apis/pipelines/approvals?api-version=7.1' "
                     "-d '[{\"approvalId\":\"ab-1\",\"status\":\"approved\"}]'")
        self.assertEqual((c.kind, c.host, c.approvals, c.org, c.project),
                         ("pipeline-approve", "azure", ["ab-1"], "https://dev.azure.com/org", "proj"))
        c = self.one("gh api -X POST repos/org/app-web/actions/runs/99/pending_deployments -f state=approved "
                     "-F environment_ids[]=1")
        self.assertEqual((c.kind, c.host, c.repo, c.run), ("pipeline-approve", "github", "org/app-web", "99"))
        self.assertEqual(calls("gh api -X POST repos/org/app-web/actions/runs/99/pending_deployments "
                               "-f state=rejected"), [])

    def test_credentials_never_kept(self):
        c = self.one("curl -u user:secret -H 'Authorization: Bearer tok' -X PUT "
                     "https://user:pw@api.github.com/repos/org/app-web/pulls/7/merge")
        self.assertNotIn("secret", repr(vars(c)) if hasattr(c, "__dict__") else repr(c))
        self.assertNotIn("pw@", c.url)


if __name__ == "__main__":
    unittest.main()
