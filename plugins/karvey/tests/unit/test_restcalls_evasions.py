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

    def test_bug151_curl_globs_and_dot_segments(self):
        self.assertEqual(self.kind("curl -X PUT 'https://api.github.com/repos/org/app-web/pulls/{12}/merge'"),
                         "pr-complete")
        self.assertEqual(self.kind("curl -X PUT 'https://api.github.com/repos/org/app-web/pulls/1[2-2]/merge'"),
                         "pr-complete")
        self.assertEqual(self.kind("curl -X PUT https://api.github.com/repos/org/app-web/pulls/12/./merge"),
                         "pr-complete")
        self.assertEqual(self.kind("curl --path-as-is -X PUT https://api.github.com/repos/org/app-web/pulls/12/"
                                   "merge/../merge"), "fail")
        self.assertEqual(self.kind("curl -X PUT 'https://api.github.com/repos/org/app-web/pulls/[1-999]/merge'"),
                         "fail")

    def test_bug152_request_target_and_variable_expansion(self):
        self.assertEqual(self.kind("curl -X PUT --request-target /repos/org/app-web/pulls/12/merge "
                                   "https://api.github.com/"), "pr-complete")
        self.assertEqual(self.kind("curl --variable p=pulls --expand-url "
                                   "'https://api.github.com/repos/org/app-web/{{p}}/12/merge' -X PUT"), "fail")

    def test_bug151_raw_http_by_hand(self):
        self.assertEqual(self.kind("printf 'PUT /repos/org/app-web/pulls/12/merge HTTP/1.1\\r\\nHost: "
                                   "api.github.com\\r\\n\\r\\n' | openssl s_client -connect api.github.com:443"),
                         "fail")

    def test_bug151_credentials_in_variables_do_not_block_a_non_completing_update(self):
        self.assertIsNone(self.kind('curl -u "$USER:$PAT" -X PATCH -d \'{"title":"x"}\' \'%s\'' % AZ))
        self.assertIsNone(self.kind('curl -H "$AUTH" -X PATCH -d \'{"title":"x"}\' \'%s\'' % AZ))
        self.assertIsNone(self.kind('wget --header "$H" --method=PATCH --body-data=\'{"title":"x"}\' \'%s\'' % AZ))

    def test_bug151_text_output_is_not_a_request(self):
        self.assertIsNone(self.kind("echo POST %s" % AZ))

    def test_inline_read_is_not_a_candidate(self):
        self.assertIsNone(self.kind("python3 -c \"print(open('.git/refs/heads/main').read())\""))

    def test_azure_numeric_status(self):
        self.assertEqual(self.kind("curl -X PATCH '%s' -d '{\"status\":3}'" % AZ), "pr-complete")


if __name__ == "__main__":
    unittest.main()
