"""BUG-146 (QA of 3.12.1, F-13): REST forms that slipped past the first parser."""
import unittest

import _path  # noqa: F401
from test_restcalls import AZ, calls

GH = "https://api.github.com/repos/org/app-web/pulls/12/merge"


class Evasions(unittest.TestCase):
    def kind(self, cmd, cwd=None):
        cs = calls(cmd, cwd)
        return cs[0].kind if cs else None

    def test_every_url_is_classified(self):
        self.assertEqual(self.kind("curl -X PUT https://example.com/ %s" % GH), "pr-complete")

    def test_unknown_or_value_options_do_not_hide_the_url(self):
        self.assertEqual(self.kind("curl --max-redirs 3 -X PUT %s" % GH), "pr-complete")
        self.assertEqual(self.kind("curl -s -D /dev/stderr -X PATCH -d '{\"status\":\"completed\"}' '%s'" % AZ),
                         "pr-complete")

    def test_curl_config_fails_closed(self):
        self.assertEqual(self.kind("curl -K cfg"), "fail")

    def test_wget_separate_option_values(self):
        self.assertEqual(self.kind("wget --method PUT %s" % GH), "pr-complete")
        self.assertEqual(self.kind("wget --header 'Accept: x' -O out.json --method=PATCH "
                                   "--body-data='{\"status\":\"completed\"}' '%s'" % AZ), "pr-complete")

    def test_httpie_auth_is_not_the_url_and_is_not_kept(self):
        cs = calls("http -a bot:SECRETTOKEN PUT %s" % GH)
        self.assertEqual(cs[0].kind, "pr-complete")
        self.assertNotIn("SECRETTOKEN", repr(cs[0]))
        self.assertEqual(self.kind("httpx -m PUT %s" % GH), "pr-complete")

    def test_branch_writes_through_other_endpoints(self):
        c = calls("gh api -X PUT repos/org/app-web/contents/x.txt -f branch=main -f message=m -f content=eA==")[0]
        self.assertEqual((c.kind, c.branch), ("ref-write", "main"))
        c = calls("az rest -m post --url https://dev.azure.com/o/p/_apis/git/repositories/app/pushes "
                  "--body '{\"refUpdates\":[{\"name\":\"refs/heads/main\",\"oldObjectId\":\"0\"}]}'")[0]
        self.assertEqual((c.kind, c.branch), ("ref-write", "main"))
        self.assertEqual(self.kind("curl -X POST https://api.github.com/graphql "
                                   "-d '{\"query\":\"mutation { mergePullRequest(input:{}) { clientMutationId } }\"}'"),
                         "fail")

    def test_here_documents_and_encoded_paths(self):
        self.assertEqual(self.kind("python3 - <<EOF\nimport urllib.request as u\n"
                                   "u.urlopen(u.Request('%s', method='PUT'))\nEOF" % GH), "fail")
        self.assertEqual(self.kind("curl -X PUT https://api.github.com/repos/org/app-web/%70ulls/12/merge"),
                         "pr-complete")
        self.assertEqual(self.kind('curl -X PUT "https://api.github.com/repos/org/app-web/pulls/$N/merge"'), "fail")

    def test_inline_read_is_not_a_candidate(self):
        self.assertIsNone(self.kind("python3 -c \"print(open('.git/refs/heads/main').read())\""))

    def test_azure_numeric_status(self):
        self.assertEqual(self.kind("curl -X PATCH '%s' -d '{\"status\":3}'" % AZ), "pr-complete")


if __name__ == "__main__":
    unittest.main()
