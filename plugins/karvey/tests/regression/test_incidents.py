"""Regression index BUG-05..BUG-22 and BUG-84 onwards (architecture §6.4, REQ-W1-107, E1.F14.T3).

Each incident names the check that proves its fix. This file does not re-run those checks' own suites (CI
runs them: the unit suite, the guard tables, test-hooks.sh and the node page tests). It fails when:

- a named check disappears: a lint id leaves the registry, a table case id or a test function / node test
  title is renamed or deleted, a manual script or a test-hooks.sh section goes away;
- a named lint check reports an error on this repository (the check is run in process, so the fix is proved
  live, not only by its fixture);
- ``docs/bugs_dev_testing.md`` marks an incident RESUELTO while this index gives it no automated check, or
  its ``### Regression test`` section does not name one of the checks listed here (L-32 cross-checks the
  same section against the files on disk);
- ``docs/spec/incidents-index.md`` disagrees with the tracker on an incident's state.
"""
import ast
import importlib.util
import json
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent.parent
REPO = PLUGIN.parent.parent
TESTS = PLUGIN / "tests"
TRACKER = REPO / "docs" / "bugs_dev_testing.md"
INCIDENTS_INDEX = REPO / "docs" / "spec" / "incidents-index.md"

_spec = importlib.util.spec_from_file_location("lint_plugin", str(PLUGIN / "scripts" / "lint-plugin.py"))
lp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lp)

# Kinds: lint (L-NN) · table (file stem, case id) · unit (file, Class.test) · node (file, title fragment) ·
# hooks (test-hooks.sh section fragment) · manual (script under tests/manual/). "manual" alone is not an
# automated regression: an incident whose only checks are manual cannot be RESUELTO.
INDEX = {
    "BUG-05": [  # impl resume on dead states (REQ-W1-085)
        ("lint", "L-36"),
        ("unit", "test_lint_plugin.py", "L36.test_completed_dependency_fails"),
        ("unit", "test_lint_plugin.py", "L36.test_first_pending_task_fails"),
        ("unit", "test_lint_plugin.py", "L36.test_dependency_at_done_only_fails"),
        ("manual", "impl-resume.md"),
    ],
    "BUG-06": [  # legacy management string breaks the != markdown guards
        ("lint", "L-28"),
        ("unit", "test_config_resolve.py", "LegacyShapes.test_legacy_string_markdown"),
        ("unit", "test_config_resolve.py", "LegacyShapes.test_legacy_clickup_string_with_backlog_list_id"),
        ("unit", "test_config_resolve.py", "LegacyShapes.test_none_string_and_object_are_markdown"),
        ("unit", "test_config_resolve.py", "LegacyProjectFixtures.test_resolve_management"),
        ("unit", "test_state_fix.py", "Management.test_project_string"),
        ("unit", "test_state_fix.py", "Management.test_spec_none_to_markdown_and_string_kept"),
    ],
    "BUG-07": [("lint", "L-31")],  # README / plugin.json present ClickUp as the tracker
    "BUG-08": [  # invalid KARVEY_TZ silently falls back
        ("table", "statusline", "statusline-01-valid-tz-no-marker"),
        ("table", "statusline", "statusline-02-invalid-tz-marked"),
        ("table", "statusline", "statusline-03-no-tz-no-marker"),
    ],
    "BUG-09": [  # stray separator with only the 7-day window
        ("table", "statusline", "statusline-04-only-7d-no-leading-separator"),
        ("table", "statusline", "statusline-05-both-windows-one-separator"),
        ("table", "statusline", "statusline-06-only-5h"),
    ],
    "BUG-10": [  # malformed hash throws before the switch binds
        ("node", "test_page.mjs", "safeDecodeHash returns null for a malformed or empty hash, never throws (BUG-10)"),
        ("node", "test_page.mjs", "init with a malformed hash still binds the switch"),
    ],
    "BUG-11": [  # invalid ?lang= saved as the viewer's choice
        ("node", "test_page.mjs", "pickLang: a ?lang= link is one-off when a choice was saved (BUG-11"),
        ("node", "test_page.mjs", "pickLang: an invalid ?lang= is ignored and nothing is saved"),
        ("node", "test_page.mjs", "init: ?lang=xx saves nothing (BUG-11)"),
    ],
    "BUG-12": [  # switching language drops the other query parameters
        ("node", "test_page.mjs", "withLang changes only lang and keeps the other parameters (BUG-12"),
        ("node", "test_page.mjs", "init: switching keeps the other query parameters (BUG-12)"),
    ],
    "BUG-13": [  # no hashchange handling
        ("node", "test_page.mjs", "init binds hashchange and jumps to the shown block (BUG-13"),
    ],
    "BUG-14": [  # inert switch without JS
        ("unit", "test_page_static.py", "NoInertSwitch.test_switch_links_are_inside_a_hidden_container"),
        ("unit", "test_page_static.py", "NoInertSwitch.test_css_hides_the_switch_until_js"),
        ("unit", "test_page_static.py", "NoInertSwitch.test_scripts_add_the_js_class"),
        ("node", "test_page.mjs", "init shows the switch (hidden without JS, BUG-14)"),
    ],
    "BUG-15": [("lint", "L-15")],  # clickup-sync-guard referenced, nothing installs it
    "BUG-16": [  # hooks/README vs session-hook behaviour
        ("lint", "L-16"),
        ("table", "session", "ss-13-empty-notifications-startup-one-line"),
        ("table", "session", "ss-15-bare-openapi-under-karvey-parent-silent"),
        ("table", "session", "ss-20-non-karvey-dir-silent"),
    ],
    "BUG-17": [("lint", "L-13")],  # release docs incomplete (CHANGELOG Why, page history)
    # 3.11.3 / 3.11.4: already regression-tested in test-hooks.sh; listed, not re-implemented.
    "BUG-18": [("hooks", "every declared command runs as written (BUG-18")],
    "BUG-19": [("hooks", "team.json inside the repo (BUG-19)")],
    "BUG-20": [("hooks", "state.json paths (BUG-20)")],
    "BUG-21": [("hooks", "worktrees (BUG-21)")],
    "BUG-22": [("hooks", "profile-only commits since the save (BUG-22)")],  # python and degraded paths
    "BUG-84": [  # the sponsor page is rebuilt at every gate close (REQ-W3-022)
        ("unit", "test_sponsor.py", "Cli.test_BUG_84_the_page_is_rebuilt_at_a_later_gate"),
        ("unit", "test_sponsor.py", "Cli.test_BUG_84_a_page_changed_by_another_writer_is_refused_not_overwritten"),
    ],
    "BUG-86": [  # On a phone the overdue tag squeezes the question text of the sponsor page
        ('node', 'test_sponsor_page.mjs', 'BUG-86: at 360 px the question text wraps under a wide tag instead of being squeezed'),
    ],
    "BUG-87": [  # Sponsor page progress steps show done by colour only
        ('unit', 'test_sponsor.py', 'Page.test_BUG_87_every_step_state_is_a_word_not_only_a_colour'),
        ('unit', 'test_sponsor.py', 'Page.test_BUG_87_spanish_step_words'),
    ],
    "BUG-88": [  # Touch targets under 44 px on the phone surfaces
        ('node', 'test_sponsor_page.mjs', 'BUG-88: summaries meet the 44 px touch target'),
        ('node', 'test_page.mjs', 'BUG-88: the phone language select meets the 44 px touch target'),
    ],
    "BUG-89": [  # The sponsor page prints light-grey text on white in the dark scheme
        ('node', 'test_sponsor_page.mjs', 'BUG-89: print keeps the light scheme and uses the print tokens, no literal colour'),
    ],
    "BUG-90": [  # Sponsor page landmarks carry the wrong accessible names
        ('unit', 'test_sponsor.py', 'Page.test_BUG_90_landmarks_are_named_for_what_they_hold'),
    ],
    "BUG-91": [  # Accepted and carried risks shown with the success fill
        ('unit', 'test_sponsor.py', 'Page.test_BUG_91_risk_state_tag_fill_follows_the_design_spec'),
    ],
    "BUG-92": [  # A long change goal is cut mid-word in the sponsor page title
        ('unit', 'test_sponsor.py', 'Page.test_BUG_92_a_long_goal_is_cut_at_a_word_with_an_ellipsis'),
    ],
    "BUG-93": [  # The portfolio view does not say it is read-only and offline
        ('unit', 'test_portfolio.py', 'View.test_BUG_93_the_text_view_ends_with_the_read_only_footer'),
    ],
    "BUG-94": [  # The security scan records absolute local paths in committed evidence
        ('unit', 'test_security_scan.py', 'Run.test_BUG_94_the_recorded_command_carries_no_absolute_path'),
    ],
    "BUG-95": [  # The gate summary's judge line omits the discarded count and the tokens
        ('unit', 'test_context_gate.py', 'GateSummary.test_BUG_95_judge_line_has_discarded_and_tokens_with_their_source'),
    ],
    "BUG-96": [  # The gate close drops the leak check's field and rule
        ('unit', 'test_close.py', 'Close.test_BUG_96_a_leak_refusal_names_each_field_and_rule_never_the_value'),
    ],
    "BUG-97": [  # `karvey-trace.py --wbs` misses root-level QA and deploy sections
        ('unit', 'test_wbs.py', 'Legacy.test_BUG_97_root_qa_and_deploy_sections_with_table_rows_are_outside'),
        ('unit', 'test_wbs.py', 'Legacy.test_BUG_97_an_epic_item_twice_is_a_duplicate_and_children_inside_are_fine'),
    ],
    "BUG-98": [  # QA and deploy write root-level sections on the Markdown tracker
        ('unit', 'test_wbs.py', 'SkillText.test_BUG_98_qa_deploy_and_the_markdown_adapter_name_the_epic_item_shape'),
    ],
    "BUG-99": [  # With browse.via agent the session fetched an undeclared URL itself
        ('unit', 'test_browse_via.py', 'SkillText.test_BUG_99_the_session_opens_no_url_itself'),
    ],
    "BUG-100": [  # Changes requested after an approval leave the phase approved
        ('unit', 'test_state_outcomes.py', 'Outcomes.test_BUG_100_changes_requested_on_an_approved_phase_is_refused_with_the_way_out'),
    ],
    "BUG-101": [  # `observed` is blind to Skill loads and shell reads
        ('unit', 'test_close.py', 'Observed.test_BUG_101_skill_loads_and_shell_reads_count_as_opened'),
    ],
    "BUG-102": [  # The sponsor fixture fails validation with an "expected = got" message
        ('unit', 'test_schema_w2.py', 'SkippedLane.test_BUG_102_a_lane_reason_for_a_phase_the_lane_makes_optional_says_so'),
        ('unit', 'test_sponsor.py', 'FixtureValid.test_BUG_102_the_sponsor_fixture_validates_without_errors'),
    ],
    "BUG-103": [  # The gate close is skipped after an approval
        ('unit', 'test_close.py', 'AdvanceText.test_BUG_103_every_gated_phase_skill_names_karvey_close'),
    ],
    "BUG-104": [  # `observed` reads a shell brace list as one file
        ('unit', 'test_close.py', 'Observed.test_BUG_101_skill_loads_and_shell_reads_count_as_opened'),
    ],
    "BUG-105": [  # Writing tools on a spec/ project create a second spec root
        ('unit', 'test_context.py', 'SpecLayoutIsReadOnly.test_BUG_105_writers_refuse_the_spec_layout_and_create_no_second_root'),
    ],
    "BUG-126": [  # `observed` flags the tracker adapter in use as outside the load list
        ('unit', 'test_close.py', 'ObservedAlternatives.test_BUG_126_any_tracker_adapter_of_the_load_list_is_inside_it'),
    ],
    "BUG-106": [  # Sponsor delivery sends a page other than the one the leak check passed
        ('unit', 'test_sponsor.py', 'Security.test_BUG_106_deliver_refuses_a_page_changed_after_the_checked_build'),
    ],
    "BUG-107": [  # Stakeholder destination not checked where it is used
        ('unit', 'test_notify_events.py', 'Events.test_BUG_107_an_unsafe_stakeholder_destination_is_refused_at_use'),
        ('unit', 'test_sponsor.py', 'Security.test_BUG_107_a_change_override_with_an_unsafe_destination_is_refused_at_use'),
    ],
    "BUG-108": [  # Portfolio follows symlinks out of a listed repository
        ('unit', 'test_portfolio.py', 'Containment.test_BUG_108_symlinks_out_of_the_repository_are_not_read'),
    ],
    "BUG-109": [  # Hex secrets pass the leak check
        ('unit', 'test_leakcheck.py', 'QaDimension1.test_BUG_109_a_hex_secret_is_caught_and_short_commit_ids_are_not'),
    ],
    "BUG-110": [  # Unreadable declared portfolio disables the other-clients rule
        ('unit', 'test_sponsor.py', 'Security.test_BUG_110_an_unreadable_declared_portfolio_fails_closed'),
    ],
    "BUG-111": [  # Braces in free text crash the sponsor render
        ('unit', 'test_sponsor.py', 'Security.test_BUG_111_braces_in_free_text_neither_crash_nor_fill_a_slot'),
    ],
    "BUG-112": [  # Leak check misses some paths and exempts formatted ids
        ('unit', 'test_leakcheck.py', 'QaDimension1.test_BUG_112_paths_in_urls_and_forward_slash_drives_are_caught'),
        ('unit', 'test_leakcheck.py', 'QaDimension1.test_BUG_112_only_a_plausible_date_exempts_eight_digits_and_dotted_ids_are_pii'),
    ],
    "BUG-113": [  # Event change id and foreign text not constrained
        ('unit', 'test_portfolio.py', 'Containment.test_BUG_113_sanitise_strips_bidi_and_zero_width'),
        ('unit', 'test_notify_events.py', 'Events.test_BUG_113_change_must_be_an_id_and_no_item_reads_naturally'),
    ],
    "BUG-114": [  # Moving a risk half-applies when the backlog exists
        ('unit', 'test_risks.py', 'Command.test_BUG_114_move_with_an_existing_backlog_writes_everything_once'),
        ('unit', 'test_risks.py', 'Command.test_BUG_114_a_failed_spec_write_puts_register_and_backlog_back'),
    ],
    "BUG-115": [  # A row-less table hides the risk register, questions or backlog
        ('unit', 'test_risks.py', 'Archive.test_BUG_115_a_row_less_table_before_the_register_does_not_hide_an_open_risk'),
        ('unit', 'test_backlog_wsjf.py', 'StaleHeader.test_BUG_115_a_row_less_table_before_does_not_hide_the_backlog'),
        ('unit', 'test_questions.py', 'Parse.test_BUG_115_a_row_less_table_before_does_not_hide_the_questions'),
    ],
    "BUG-116": [  # The qa notification is re-sent: two sources for its state
        ('unit', 'test_close.py', 'Close.test_BUG_116_the_qa_notification_state_is_the_verdict_only'),
    ],
    "BUG-117": [  # Four new validate warnings ignore their check modes
        ('unit', 'test_stakeholders.py', 'Client.test_BUG_117_the_mismatch_warning_follows_its_check_mode'),
    ],
    "BUG-118": [  # Applying a design delta can traceback or half-write
        ('unit', 'test_design_delta.py', 'Apply.test_BUG_118_an_empty_design_system_file_is_applied_not_a_traceback'),
        ('unit', 'test_design_delta.py', 'Apply.test_BUG_118_a_conflict_stops_and_writes_nothing_not_even_the_additions'),
    ],
    "BUG-119": [  # New scripts end in a traceback on an unexpected error
        ('unit', 'test_design_delta.py', 'Apply.test_BUG_119_an_internal_error_is_an_envelope_exit_5'),
        ('unit', 'test_close.py', 'Close.test_BUG_119_an_internal_error_is_an_envelope_exit_5'),
    ],
    "BUG-120": [  # A malformed deploys entry crashes the report
        ('unit', 'test_context_report.py', 'Report.test_BUG_120_a_non_object_deploys_entry_is_skipped_not_a_crash'),
    ],
    "BUG-121": [  # Concurrent closes can charge the same interval twice
        ('unit', 'test_effort.py', 'Command.test_BUG_121_the_interval_is_read_stored_and_charged_under_one_lock'),
    ],
    "BUG-123": [  # Risk rewrite fails on a differently cased header
        ('unit', 'test_risks.py', 'Command.test_BUG_123_rewrite_finds_its_header_whatever_the_case'),
    ],
    "BUG-127": [  # `observed` misses files read relative to a `cd`
        ('unit', 'test_close.py', 'Observed.test_BUG_101_skill_loads_and_shell_reads_count_as_opened'),
    ],
    "BUG-128": [  # Contract coverage passes with a contract gone
        ('unit', 'test_contracts.py', 'Coverage.test_BUG_128_the_core_counts_only_for_a_phase_that_loads_it'),
        ('unit', 'test_contracts.py', 'Coverage.test_BUG_128_an_emptied_contract_section_is_not_loaded'),
    ],
    "BUG-129": [  # Webhook URLs with the secret in the path pass the leak check
        ('unit', 'test_leakcheck.py', 'QaDimension1.test_BUG_129_webhook_urls_and_random_url_segments_are_secrets'),
    ],
    "BUG-130": [  # Phone-like numbers exempt as versions
        ('unit', 'test_leakcheck.py', 'QaDimension1.test_BUG_130_a_version_needs_a_v_or_version_context'),
    ],
    "BUG-131": [  # Secret assignments in Spanish or Portuguese pass
        ('unit', 'test_leakcheck.py', 'QaDimension1.test_BUG_131_spanish_and_portuguese_assignments_are_secrets'),
    ],
    "BUG-132": [  # Other-client names missed with other accents or case
        ('unit', 'test_leakcheck.py', 'QaDimension1.test_BUG_132_client_names_ignore_accents_and_case_and_match_as_prefix'),
    ],
    "BUG-133": [  # A phase dropped from the snapshot leaves the median silently
        ('unit', 'test_context_budget.py', 'Compare.test_BUG_133_a_phase_only_in_the_baseline_fails_the_gate'),
    ],
    "BUG-134": [  # Effort charges another session capture as exact
        ('unit', 'test_effort.py', 'Lib.test_BUG_134_only_the_closing_sessions_capture_is_exact'),
        ('unit', 'test_effort.py', 'Lib.test_BUG_134_review_minutes_are_never_exact'),
    ],
    "BUG-135": [  # done-direct accepts a commit that does not exist
        ('unit', 'test_backlog_wsjf.py', 'DoneDirectInGit.test_BUG_135_a_done_direct_commit_that_is_not_in_git_is_refused'),
        ('unit', 'test_backlog_wsjf.py', 'DoneDirectInGit.test_BUG_135_a_real_commit_is_accepted'),
        ('unit', 'test_backlog_wsjf.py', 'DoneDirectInGit.test_BUG_135_an_unknown_state_is_a_warning_not_dropped'),
        ('unit', 'test_backlog_wsjf.py', 'View.test_BUG_135_open_with_a_note_is_listed_and_an_unknown_state_is_invalid'),
    ],
    "BUG-136": [  # A risk can be moved to an unrelated item or moved twice
        ('unit', 'test_risks.py', 'Command.test_BUG_136_move_to_an_unrelated_backlog_item_is_refused'),
        ('unit', 'test_risks.py', 'Command.test_BUG_136_a_second_move_is_refused'),
    ],
    "BUG-137": [  # Sponsor delivery crashes when the portfolio becomes unreadable after the model c
        ('unit', 'test_sponsor.py', 'Security.test_BUG_137_a_portfolio_unreadable_at_delivery_refuses_not_a_traceback'),
    ],
}
AUTOMATED = {"lint", "table", "unit", "node", "hooks"}


def check_path(ref):
    """The file on disk that holds the named check (repo-relative string)."""
    kind = ref[0]
    if kind == "lint":
        return "plugins/karvey/scripts/lint-plugin.py"
    if kind == "table":
        return "plugins/karvey/tests/hooks/tables/%s.json" % ref[1]
    if kind == "unit":
        return "plugins/karvey/tests/unit/%s" % ref[1]
    if kind == "node":
        return "plugins/karvey/tests/page/%s" % ref[1]
    if kind == "hooks":
        return "plugins/karvey/hooks/tests/test-hooks.sh"
    if kind == "manual":
        return "plugins/karvey/tests/manual/%s" % ref[1]
    raise AssertionError("unknown kind %r" % kind)


def test_names(path):
    """``{"Class.method"}`` of a unittest file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test"):
                    out.add("%s.%s" % (node.name, item.name))
    return out


def tracker_sections():
    """``{BUG-NN: {"state": str, "regression": str}}`` from docs/bugs_dev_testing.md."""
    out, cur, in_reg = {}, None, False
    for line in TRACKER.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(BUG-\d+)\b", line)
        if m:
            cur = out.setdefault(m.group(1), {"state": None, "regression": ""})
            in_reg = False
            continue
        if line.startswith("## "):
            cur = None
            continue
        if cur is None:
            continue
        m = re.search(r"\*\*Current state:\*\*\s*([A-Z ]+)", line)
        if m and cur["state"] is None:
            cur["state"] = m.group(1).strip()
        if re.match(r"^###\s+Regression", line, re.I):
            in_reg = True
            continue
        if line.startswith("### "):
            in_reg = False
        elif in_reg:
            cur["regression"] += line + "\n"
    return out


class NamedChecksExist(unittest.TestCase):
    def test_every_routed_incident_is_indexed(self):
        for n in range(5, 23):
            self.assertIn("BUG-%02d" % n, INDEX)

    def test_lint_ids_are_registered(self):
        known = {c.id for c in lp.registry()}
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] == "lint":
                    self.assertIn(ref[1], known, "%s names %s" % (bug, ref[1]))

    def test_table_cases_exist(self):
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] != "table":
                    continue
                data = json.loads((REPO / check_path(ref)).read_text(encoding="utf-8"))
                cases = data["cases"] if isinstance(data, dict) else data
                ids = {c.get("id") for c in cases}
                self.assertIn(ref[2], ids, "%s names table case %s/%s" % (bug, ref[1], ref[2]))

    def test_unit_tests_exist(self):
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] == "unit":
                    self.assertIn(ref[2], test_names(REPO / check_path(ref)), "%s names %s" % (bug, ref[1:]))

    def test_node_tests_exist(self):
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] != "node":
                    continue
                text = (REPO / check_path(ref)).read_text(encoding="utf-8")
                titles = re.findall(r"\btest\(\s*'((?:[^'\\]|\\.)*)'", text)
                self.assertTrue(any(ref[2] in t for t in titles), "%s names node test %r" % (bug, ref[2]))

    def test_hooks_sections_exist(self):
        text = (REPO / "plugins/karvey/hooks/tests/test-hooks.sh").read_text(encoding="utf-8")
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] == "hooks":
                    self.assertIn(ref[1], text, "%s names test-hooks.sh section %r" % (bug, ref[1]))

    def test_manual_scripts_exist(self):
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] == "manual":
                    p = REPO / check_path(ref)
                    self.assertTrue(p.is_file(), "%s names %s" % (bug, p))
                    self.assertIn("Expected:", p.read_text(encoding="utf-8"))


class NamedLintChecksPassOnThisRepo(unittest.TestCase):
    """The fix is proved live: each named lint check reports no error on this repository."""

    def test_named_lint_checks_are_green(self):
        ids = {ref[1] for refs in INDEX.values() for ref in refs if ref[0] == "lint"}
        findings = lp.run_checks(lp.Ctx(REPO), only=ids)
        errors = ["%s %s:%s %s" % (f["check"], f["file"], f["line"], f["message"])
                  for f in findings if f["severity"] == "error"]
        self.assertEqual(errors, [])


class TrackerAgreesWithTheIndex(unittest.TestCase):
    def setUp(self):
        self.sections = tracker_sections()

    def test_resuelto_needs_an_automated_check_named_in_the_tracker(self):
        for bug, refs in sorted(INDEX.items()):
            sec = self.sections.get(bug)
            self.assertIsNotNone(sec, "%s is not in docs/bugs_dev_testing.md" % bug)
            if sec["state"] != "RESUELTO":
                continue
            automated = [r for r in refs if r[0] in AUTOMATED]
            self.assertTrue(automated, "%s is RESUELTO but its only checks are manual" % bug)
            named = [r for r in automated
                     if check_path(r) in sec["regression"] or (r[0] == "lint" and r[1] in sec["regression"])]
            self.assertTrue(named, "%s: the tracker's Regression test section names none of %s" % (bug, automated))

    def test_incidents_index_state_matches_the_tracker(self):
        rows = {}
        for line in INCIDENTS_INDEX.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and re.match(r"^BUG-\d+$", cells[0]) and len(cells) >= 8:
                rows[cells[0]] = cells
        for bug, sec in self.sections.items():
            with self.subTest(bug=bug):
                self.assertIn(bug, rows, "%s missing from incidents-index.md" % bug)
                self.assertEqual(rows[bug][5], sec["state"])
                if sec["state"] == "RESUELTO":
                    self.assertNotIn(rows[bug][6], ("", "—"), "%s RESUELTO without a regression column" % bug)


if __name__ == "__main__":
    unittest.main()
