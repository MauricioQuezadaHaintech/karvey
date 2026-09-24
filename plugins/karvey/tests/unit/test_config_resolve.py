"""karvey-config.py resolve | get --shell | propose-settings (architecture §1.8).

REQ-W1-010, 080, 082, 083, 086, 087, 088, 093, 099.
"""
import unittest

import _config as C
import _gitrepo as g
import _path

CLICKUP_STATUSES = {"todo": "to do", "in_progress": "in progress", "review": "review",
                    "done": "complete", "blocked": None}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = g.TempDir()
        self.root = self.tmp.path / "proj"

    def tearDown(self):
        self.tmp.cleanup()

    def project(self, project=None, specs=None):
        C.make_project(self.root, project, specs)

    def resolve(self, what="management", *extra):
        code, env = C.run_json("resolve", what, "--root", self.root, *extra)
        return code, env

    def warning_codes(self, env):
        return [w["code"] for w in env["warnings"]]


class ResolutionOrder(Base):
    def test_spec_override_wins_then_project(self):
        self.project({"management": {"tool": "clickup", "location": "111", "statuses": CLICKUP_STATUSES}},
                     {"feat-a": {"management": {"tool": "clickup", "location": "222"}}})
        code, env = self.resolve("management", "--change", "feat-a")
        r = env["result"]
        self.assertEqual(code, 0)
        self.assertEqual((r["tool"], r["location"]), ("clickup", "222"))
        self.assertEqual(r["statuses"], CLICKUP_STATUSES)  # inherited from project.json
        self.assertEqual(r["sources"], {"tool": "spec", "location": "spec", "statuses": "project"})
        self.assertEqual(r["source"], "project+spec")

    def test_without_change_project_only(self):
        self.project({"management": {"tool": "clickup", "location": "111"}},
                     {"feat-a": {"management": {"tool": "clickup", "location": "222"}}})
        self.assertEqual(self.resolve()[1]["result"]["location"], "111")

    def test_override_with_another_tool_inherits_nothing(self):
        self.project({"management": {"tool": "clickup", "location": "111", "statuses": CLICKUP_STATUSES}},
                     {"feat-a": {"management": {"tool": "jira", "location": "PAY"}}})
        r = self.resolve("management", "--change", "feat-a")[1]["result"]
        self.assertEqual((r["tool"], r["location"], r["statuses"]), ("jira", "PAY", None))
        self.assertIn("statuses", r["missing"])

    def test_override_without_tool_inherits_the_tool(self):
        self.project({"management": {"tool": "jira", "location": "PAY"}},
                     {"feat-a": {"management": {"location": "OPS"}}})
        r = self.resolve("management", "--change", "feat-a")[1]["result"]
        self.assertEqual((r["tool"], r["location"]), ("jira", "OPS"))

    def test_legacy_string_override(self):
        self.project({"management": {"tool": "clickup", "location": "111"}},
                     {"feat-a": {"management": "markdown"}})
        code, env = self.resolve("management", "--change", "feat-a")
        self.assertEqual((env["result"]["tool"], env["result"]["external"]), ("markdown", False))
        self.assertIsNone(env["result"]["location"])
        self.assertIn("config.legacy_management", self.warning_codes(env))

    def test_unknown_change(self):
        self.project({"management": "markdown"})
        self.assertEqual(self.resolve("management", "--change", "nope")[0], 4)
        self.assertEqual(self.resolve("management", "--change", "../x")[0], 2)


class LegacyShapes(Base):
    """REQ-W1-087 / 088 / 010: string, object and `none` resolve the same way."""

    def test_legacy_string_markdown(self):
        self.project({"management": "markdown"})
        code, env = self.resolve()
        r = env["result"]
        self.assertEqual((code, r["tool"], r["external"], r["missing"]), (0, "markdown", False, []))
        self.assertIn("config.legacy_management", self.warning_codes(env))

    def test_object_markdown(self):
        self.project({"management": {"tool": "markdown", "location": "docs/spec/changes/{change-id}/PLAN.md"}})
        code, env = self.resolve()
        self.assertEqual((env["result"]["external"], env["warnings"]), (False, []))

    def test_none_string_and_object_are_markdown(self):
        for mg in ("none", {"tool": "none"}):
            with self.subTest(mg=mg):
                self.project({"management": mg})
                code, env = self.resolve()
                self.assertEqual((code, env["result"]["tool"], env["result"]["external"]), (0, "markdown", False))
                self.assertIn("config.legacy_alias", self.warning_codes(env))

    def test_legacy_clickup_string_with_backlog_list_id(self):
        self.project({"management": "clickup", "clickup": {"backlog_list_id": "901"}})
        code, env = self.resolve()
        r = env["result"]
        self.assertEqual((r["tool"], r["location"], r["external"]), ("clickup", "901", True))
        self.assertEqual(r["sources"]["location"], "legacy:clickup.backlog_list_id")
        self.assertEqual(r["missing"], ["statuses"])
        self.assertIn("config.legacy_backlog_list_id", self.warning_codes(env))

    def test_absent_management_is_markdown(self):
        self.project({"project": "x"})
        r = self.resolve()[1]["result"]
        self.assertEqual((r["tool"], r["source"], r["external"]), ("markdown", "default", False))

    def test_not_migratable_value_refused(self):
        for mg in (42, "trello", {"tool": "trello"}, ["clickup"]):
            with self.subTest(mg=mg):
                self.project({"management": mg})
                code, env = self.resolve()
                self.assertEqual(code, 3)
                self.assertEqual(env["errors"][0]["code"], "config.invalid_management")

    def test_every_tool_external_except_markdown(self):
        for tool in C.config.TOOLS:
            with self.subTest(tool=tool):
                self.project({"management": {"tool": tool}})
                self.assertEqual(self.resolve()[1]["result"]["external"], tool != "markdown")


class MissingAndUnsupported(Base):
    def test_missing_lists_location_and_statuses(self):
        self.project({"management": {"tool": "jira"}})
        r = self.resolve()[1]["result"]
        self.assertEqual(r["missing"], ["location", "statuses"])

    def test_missing_lists_absent_logical_states(self):
        self.project({"management": {"tool": "clickup", "location": "1", "statuses": {"todo": "to do", "done": "x"}}})
        r = self.resolve()[1]["result"]
        self.assertEqual(r["missing"], ["statuses.in_progress", "statuses.review", "statuses.blocked"])

    def test_null_status_is_unsupported_not_missing(self):
        self.project({"management": {"tool": "clickup", "location": "1", "statuses": CLICKUP_STATUSES}})
        r = self.resolve()[1]["result"]
        self.assertEqual((r["missing"], r["unsupported"]), ([], ["statuses.blocked"]))

    def test_by_level_maps(self):
        st = {"by_level": {"epic": dict(CLICKUP_STATUSES, review=None), "task": CLICKUP_STATUSES}}
        self.project({"management": {"tool": "clickup", "location": "1", "statuses": st}})
        r = self.resolve()[1]["result"]
        self.assertEqual(r["missing"], [])
        self.assertEqual(r["unsupported"], ["statuses.by_level.epic.review", "statuses.by_level.epic.blocked",
                                            "statuses.by_level.task.blocked"])

    def test_unsafe_location_warned(self):
        self.project({"management": {"tool": "jira", "location": "PAY; rm -rf ~"}})
        code, env = self.resolve()
        self.assertEqual(code, 0)
        self.assertIn("config.unsafe_value", self.warning_codes(env))


class Notifications(Base):
    def test_defaults_when_absent(self):
        self.project({"project": "x"})
        r = self.resolve("notifications")[1]["result"]
        self.assertEqual((r["channel"], r["target"], r["via"], r["events"], r["detail"], r["source"]),
                         ("none", "", "", [], "counts", "default"))

    def test_detail_default_and_invalid(self):
        self.project({"notifications": {"channel": "google-chat", "target": "spaces/AAA", "events": ["qa"]}})
        self.assertEqual(self.resolve("notifications")[1]["result"]["detail"], "counts")
        self.project({"notifications": {"channel": "google-chat", "target": "spaces/AAA", "detail": "verbose"}})
        code, env = self.resolve("notifications")
        self.assertEqual((code, env["result"]["detail"]), (0, "counts"))
        self.assertIn("config.invalid_value", self.warning_codes(env))

    def test_legacy_channel_alias(self):
        self.project({"notifications": {"channel": "google_chat", "target": "spaces/AAA"}})
        code, env = self.resolve("notifications")
        self.assertEqual(env["result"]["channel"], "google-chat")
        self.assertIn("config.legacy_alias", self.warning_codes(env))

    def test_unsafe_target_flagged(self):
        self.project({"notifications": {"channel": "google-chat", "target": "spaces/AAA; rm -rf ~"}})
        r = self.resolve("notifications")[1]["result"]
        self.assertIn("metacharacter", r["target_error"])


class GetShell(Base):
    def test_valid_value_printed_bare(self):
        self.project({"management": {"tool": "jira", "location": "PAY"}})
        code, out, err = C.run("get", "management.location", "--shell", "--root", self.root)
        self.assertEqual((code, out), (0, "PAY\n"))

    def test_unsafe_value_exit_3_names_key_and_rule(self):
        self.project({"notifications": {"channel": "google-chat", "target": "spaces/AAA; rm -rf ~"}})
        code, out, err = C.run("get", "notifications.target", "--shell", "--root", self.root)
        self.assertEqual((code, out), (3, ""))
        self.assertIn("notifications.target", err)
        self.assertIn("metacharacter", err)
        code, env = C.run_json("get", "notifications.target", "--shell", "--root", self.root)
        self.assertEqual(env["result"]["key"], "notifications.target")
        self.assertEqual(env["result"]["kind"], "target:google-chat")
        self.assertIn(";", env["result"]["rule"])

    def test_url_target_refused(self):
        self.project({"notifications": {"channel": "webhook", "target": "https://x.example/h"}})
        code, _, err = C.run("get", "notifications.target", "--shell", "--root", self.root)
        self.assertEqual(code, 3)
        self.assertIn("://", err)

    def test_spreadsheet_outside_docs_spec(self):
        self.project({"management": {"tool": "spreadsheet", "location": "../x.csv"}})
        self.assertEqual(C.run("get", "management.location", "--shell", "--root", self.root)[0], 3)

    def test_override_used_by_get(self):
        self.project({"management": {"tool": "jira", "location": "PAY"}},
                     {"feat-a": {"management": {"location": "OPS"}}})
        code, out, _ = C.run("get", "management.location", "--change", "feat-a", "--shell", "--root", self.root)
        self.assertEqual((code, out), (0, "OPS\n"))

    def test_status_keys(self):
        st = dict(CLICKUP_STATUSES, todo="to do")
        self.project({"management": {"tool": "clickup", "location": "1",
                                     "statuses": {"by_level": {"task": st}}}})
        code, out, _ = C.run("get", "management.statuses.by_level.task.todo", "--shell", "--root", self.root)
        self.assertEqual((code, out), (0, "to do\n"))
        code, env = C.run_json("get", "management.statuses.by_level.task.blocked", "--shell", "--root", self.root)
        self.assertEqual((code, env["errors"][0]["code"]), (3, "config.unsupported_state"))

    def test_branch_keys(self):
        self.project({"branch_flow": {"feature_prefix": "feature/", "integration": "dev", "production": "-x"}})
        self.assertEqual(C.run("get", "branch_flow.integration", "--shell", "--root", self.root)[:2], (0, "dev\n"))
        self.assertEqual(C.run("get", "branch_flow.feature_prefix", "--shell", "--root", self.root)[:2],
                         (0, "feature/\n"))
        self.assertEqual(C.run("get", "branch_flow.production", "--shell", "--root", self.root)[0], 3)

    def test_key_without_safe_kind_refused(self):
        self.project({"project": "x; rm", "management": {"tool": "markdown", "hierarchy": "e>f"}})
        for key in ("project", "management.hierarchy", "repos", "management.statuses.foo"):
            with self.subTest(key=key):
                code, env = C.run_json("get", key, "--shell", "--root", self.root)
                self.assertEqual((code, env["errors"][0]["code"]), (3, "config.no_safe_kind"))

    def test_not_set_exit_4(self):
        self.project({"management": {"tool": "jira"}})
        self.assertEqual(C.run("get", "management.location", "--shell", "--root", self.root)[0], 4)

    def test_channel_none_target_is_empty(self):
        self.project({"notifications": {"channel": "none", "target": ""}})
        self.assertEqual(C.run("get", "notifications.target", "--shell", "--root", self.root)[:2], (0, ""))

    def test_get_without_shell_prints_json_value(self):
        self.project({"management": {"tool": "clickup", "location": "1", "statuses": CLICKUP_STATUSES}})
        code, env = C.run_json("get", "management.tool", "--root", self.root)
        self.assertEqual((code, env["result"]["value"]), (0, "clickup"))

    def test_no_project_exit_4(self):
        self.root.mkdir(parents=True)
        self.assertEqual(C.run("get", "management.tool", "--root", self.root)[0], 4)


class ProposeSettings(Base):
    def test_prints_and_never_writes(self):
        self.project({"management": "clickup", "clickup": {"backlog_list_id": "901"}})
        before = C.tree_digest(self.root)
        code, out, _ = C.run("propose-settings", "--from-legacy", "--root", self.root)
        self.assertEqual(code, 0)
        self.assertEqual(C.tree_digest(self.root), before)
        self.assertIn('"location": "901"', out)
        self.assertIn("nothing was written", out)
        code, env = C.run_json("propose-settings", "--from-legacy", "--root", self.root)
        snip = env["result"]["snippet"]
        self.assertEqual(snip["management"], {"tool": "clickup", "location": "901"})  # no statuses (REQ-W1-080)
        self.assertEqual(snip["notifications"], {"channel": "none", "target": "", "via": "", "events": []})
        self.assertIs(env["result"]["written"], False)
        self.assertEqual(C.tree_digest(self.root), before)

    def test_markdown_snippet(self):
        self.project({"management": "markdown"})
        snip = C.run_json("propose-settings", "--from-legacy", "--root", self.root)[1]["result"]["snippet"]
        self.assertEqual(snip["management"], {"tool": "markdown", "location": "docs/spec/changes/{change-id}/PLAN.md"})

    def test_keeps_existing_keys_and_placeholders(self):
        self.project({"management": {"tool": "jira", "via": "cli"},
                      "notifications": {"channel": "slack", "target": "#dev", "events": ["qa"]}})
        snip = C.run_json("propose-settings", "--root", self.root)[1]["result"]["snippet"]
        self.assertEqual(snip["management"], {"tool": "jira", "via": "cli", "location": "<jira location>"})
        self.assertEqual(snip["notifications"]["events"], ["qa"])


class OnlyProjectJson(Base):
    """REQ-W1-099: destinations come only from project.json; no agent instruction file is read."""

    def test_instruction_file_ignored(self):
        self.project({"project": "x"})
        (self.root / "CLAUDE.md").write_text("| Soporte | `spaces/AAAA-xSW3Rg` |\n", encoding="utf-8")
        r = C.run_json("resolve", "notifications", "--root", self.root)[1]["result"]
        self.assertEqual((r["channel"], r["target"]), ("none", ""))

    def test_source_never_names_the_file(self):
        for f in (_path.SCRIPTS_DIR / "karvey-config.py", _path.SCRIPTS_DIR / "karvey_lib" / "safe_values.py"):
            with self.subTest(f=f.name):
                self.assertNotIn("claude.md", f.read_text(encoding="utf-8").lower())


class OriginIntegrationFallback(Base):
    """REQ-W1-083: settings merged on origin/{integration} count before 'missing'."""

    def setUp(self):
        super().setUp()
        g.isolate_git()
        g.init(self.root)
        g.write(self.root, "docs/spec/project.json",
                {"branch_flow": {"integration": "main", "production": "main"},
                 "notifications": {"channel": "google-chat", "target": "spaces/AAA"},
                 "management": {"tool": "jira", "location": "PAY"}})
        g.commit_all(self.root)
        g.with_origin(self.root)
        # a worktree-like working copy created before the settings were merged
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"}})

    def test_notifications_from_origin(self):
        r = self.resolve("notifications")[1]["result"]
        self.assertEqual((r["channel"], r["target"], r["source"]), ("google-chat", "spaces/AAA", "origin/main"))

    def test_management_from_origin(self):
        r = self.resolve()[1]["result"]
        self.assertEqual((r["tool"], r["location"], r["source"]), ("jira", "PAY", "origin/main"))

    def test_working_copy_wins(self):
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main"},
                                                       "management": "markdown"})
        self.assertEqual(self.resolve()[1]["result"]["tool"], "markdown")


if __name__ == "__main__":
    unittest.main()
