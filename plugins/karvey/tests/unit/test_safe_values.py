"""safe_values: accept/reject pairs for every §3.1 pattern (REQ-W1-093, REQ-W1-097)."""
import unittest

import _path  # noqa: F401
from karvey_lib import safe_values as sv


class CommonRefusal(unittest.TestCase):
    def test_metacharacters_refused(self):
        for ch in "`$;|&<>\\(){}\"":
            with self.subTest(ch=ch):
                with self.assertRaises(sv.UnsafeValue) as cm:
                    sv.check_common("a%sb" % ch, key="k")
                self.assertIn("metacharacter", cm.exception.rule)

    def test_control_characters_and_newline_refused(self):
        for v in ("a\nb", "a\rb", "a\x00b", "a\tb", "a\x1bb", "a\x7fb"):
            with self.subTest(v=v):
                with self.assertRaises(sv.UnsafeValue) as cm:
                    sv.check_common(v)
                self.assertIn("control", cm.exception.rule)

    def test_leading_dash_refused(self):
        with self.assertRaises(sv.UnsafeValue) as cm:
            sv.check_common("--upload-pack=x")
        self.assertIn("leading '-'", cm.exception.rule)

    def test_non_string_refused(self):
        for v in (42, None, ["a"], {"a": 1}, True):
            with self.subTest(v=v):
                with self.assertRaises(sv.UnsafeValue):
                    sv.check_common(v)

    def test_plain_value_accepted(self):
        self.assertEqual(sv.check_common("PAY-1 board/x"), "PAY-1 board/x")

    def test_error_names_key_kind_and_rule(self):
        with self.assertRaises(sv.UnsafeValue) as cm:
            sv.check_target("google-chat", "spaces/AAA; rm -rf ~")
        e = cm.exception
        self.assertEqual(e.key, "notifications.target")
        self.assertEqual(e.kind, "target:google-chat")
        msg = str(e)
        self.assertIn("notifications.target", msg)
        self.assertIn("target:google-chat", msg)
        self.assertIn(";", msg)


class Targets(unittest.TestCase):
    CASES = {
        "google-chat": (["spaces/AAAAQCj0Cjc", "spaces/a_b-c"],
                        ["spaces/AAA; rm -rf ~", "spaces/", "rooms/AAA", "spaces/AAA/threads/x",
                         "spaces/" + "A" * 65, "-spaces/AAA", "spaces/$(id)"]),
        "slack": (["#dev-ops", "#a.b_c", "C0123ABCD", "C0123ABCD45"],
                  ["dev-ops", "#Dev", "C0123", "#a;b", "C0123abcd", "#" + "a" * 81]),
        "teams": (["General", "team@x.cl:General", "19:abc.def@thread.tacv2"],
                  ["a;b", "a|b", "x" * 129, "", "-General"]),
        "email": (["alguien@haintech.cl", "a.b+c@x.co"],
                  ["noat", "a@b", "a b@x.cl", "a@x.cl;rm", "-a@x.cl", "a@@x.cl", "$(id)@x.cl"]),
        "webhook": (["QA_WEBHOOK", "KV_TEAMS_URL"],
                    ["https://hooks.slack.com/services/x", "qa_webhook", "QA", "1QA_HOOK", "QA-HOOK"]),
    }

    def test_accept_reject_pairs(self):
        for ch, (good, bad) in self.CASES.items():
            for v in good:
                with self.subTest(ch=ch, accept=v):
                    self.assertEqual(sv.check_target(ch, v), v)
            for v in bad:
                with self.subTest(ch=ch, reject=v):
                    with self.assertRaises(sv.UnsafeValue):
                        sv.check_target(ch, v)

    def test_url_refused_for_every_channel(self):
        for ch in list(self.CASES) + ["none", "google_chat"]:
            with self.subTest(ch=ch):
                with self.assertRaises(sv.UnsafeValue) as cm:
                    sv.check_target(ch, "https://evil.example/hook")
                self.assertIn("://", cm.exception.rule)
                self.assertIn("REQ-W1-097", cm.exception.rule)

    def test_google_chat_alias(self):
        self.assertEqual(sv.check_target("google_chat", "spaces/AAA"), "spaces/AAA")

    def test_channel_none(self):
        self.assertEqual(sv.check_target("none", ""), "")
        with self.assertRaises(sv.UnsafeValue):
            sv.check_target("none", "spaces/AAA")

    def test_unknown_channel(self):
        with self.assertRaises(sv.UnsafeValue):
            sv.check_target("carrier-pigeon", "x")


class Locations(unittest.TestCase):
    CASES = {
        "clickup": (["901234567890", "1"], ["90123a", "", "1" * 21, "-1", "123;id"]),
        "jira": (["PAY", "AB_1"], ["pay", "P", "PAYMENTS123", "PAY;rm", "-PAY"]),
        "linear": (["ENG", "team_a-1"], ["a b", "x" * 33, "ENG;x", "-ENG"]),
        "azure-boards": (["Paautin V2", "1395PY - Paautin V2\\Area\\Sub"],
                         ["Proj\\", "a\\b\\c\\d\\e\\f\\g", "Proj;x", "Proj$(id)", "\\Proj", "-Proj"]),
        "github-projects": (["emekui/12", "my-org/1"], ["emekui", "a/b", "emekui/1234567", "a_b/1"]),
        "markdown": (["docs/spec/changes/{change-id}/PLAN.md", "docs/spec/PLAN.md"],
                     ["PLAN.md", "docs/spec/../../etc/x.md", "docs/spec/x.txt", "/docs/spec/x.md",
                      "docs/spec/a;b.md", "docs/spec/$(id).md"]),
        "spreadsheet": (["docs/spec/backlog.csv", "docs/spec/team/plan.xlsx", "docs/spec/b.ods",
                         "docs/spec/b.md"],
                        ["../x.csv", "docs/spec/../x.csv", "/tmp/x.csv", "docs/x.csv", "docs/spec/x.exe",
                         "docs/spec//x.csv", "docs/spec/./x.csv", "C:/docs/spec/x.csv", "docs/spec/x;y.csv"]),
    }

    def test_accept_reject_pairs(self):
        for tool, (good, bad) in self.CASES.items():
            for v in good:
                with self.subTest(tool=tool, accept=v):
                    self.assertEqual(sv.check_location(tool, v), v)
            for v in bad:
                with self.subTest(tool=tool, reject=v):
                    with self.assertRaises(sv.UnsafeValue):
                        sv.check_location(tool, v)

    def test_spreadsheet_error_clause(self):
        with self.assertRaises(sv.UnsafeValue) as cm:
            sv.check_location("spreadsheet", "../x.csv")
        self.assertIn("..", cm.exception.rule)

    def test_none_alias_is_markdown(self):
        self.assertEqual(sv.check_location("none", "docs/spec/PLAN.md"), "docs/spec/PLAN.md")

    def test_braces_only_exempt_for_markdown(self):
        with self.assertRaises(sv.UnsafeValue):
            sv.check_location("other", "board{x}")
        with self.assertRaises(sv.UnsafeValue):
            sv.check_location("spreadsheet", "docs/spec/{id}.csv")

    def test_backslash_only_exempt_for_azure(self):
        with self.assertRaises(sv.UnsafeValue):
            sv.check_location("other", "Proj\\Area")

    def test_unknown_tool(self):
        with self.assertRaises(sv.UnsafeValue):
            sv.check_location("trello", "x")


class SprintsStatusesBranches(unittest.TestCase):
    def test_sprints(self):
        self.assertEqual(sv.check_sprints("clickup", "90155"), "90155")
        self.assertEqual(sv.check_sprints("azure-boards", "Proj\\Sprint 4"), "Proj\\Sprint 4")
        self.assertEqual(sv.check_sprints("linear", "Cycle 12"), "Cycle 12")
        for tool, v in (("clickup", "Sprint 1"), ("linear", "c;1"), ("jira", "-1"), ("jira", "a$b")):
            with self.subTest(tool=tool, v=v):
                with self.assertRaises(sv.UnsafeValue):
                    sv.check_sprints(tool, v)

    def test_status_names(self):
        for v in ("to do", "In Progress", "✅", "👀", "Code Review"):
            with self.subTest(accept=v):
                self.assertEqual(sv.check_status(v), v)
        for v in ("", "x" * 65, "done; rm -rf ~", "a`b`", "a$b", "a|b", "a\nb", "-done", 7, None):
            with self.subTest(reject=v):
                with self.assertRaises(sv.UnsafeValue):
                    sv.check_status(v)

    def test_branch_names(self):
        for v in ("main", "dev", "release/3.12", "feature/wave1-hardening"):
            with self.subTest(accept=v):
                self.assertEqual(sv.check_branch(v), v)
        for v in ("-main", "a..b", "x.lock", "x/", "a b", "a;b", "a~1", "", "a" * 101, "a$(id)"):
            with self.subTest(reject=v):
                with self.assertRaises(sv.UnsafeValue):
                    sv.check_branch(v)

    def test_branch_git_check(self):
        # the pattern admits "a/.b"; git refuses a component starting with '.'
        if sv._git_check_ref_format("main") is None:
            self.skipTest("git not present")
        with self.assertRaises(sv.UnsafeValue) as cm:
            sv.check_branch("a/.b")
        self.assertIn("check-ref-format", cm.exception.rule)
        self.assertEqual(sv.check_branch("a/.b", use_git=False), "a/.b")

    def test_ref_prefix(self):
        self.assertEqual(sv.check_ref_prefix("feature/"), "feature/")
        for v in ("feature", "a/b/", "-f/", "f;/"):
            with self.subTest(reject=v):
                with self.assertRaises(sv.UnsafeValue):
                    sv.check_ref_prefix(v)

    def test_enum(self):
        self.assertEqual(sv.check_enum("counts", ("counts", "full"), "notifications.detail"), "counts")
        with self.assertRaises(sv.UnsafeValue):
            sv.check_enum("verbose", ("counts", "full"), "notifications.detail")


if __name__ == "__main__":
    unittest.main()
