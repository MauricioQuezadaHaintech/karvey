"""Regression index BUG-05..BUG-81 (architecture §6.4, REQ-W1-107, E1.F14.T3).

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
    "BUG-23": [  # settings on origin/{production} only (REQ-W1-083)
        ("table", "session", "ss-24-settings-on-origin-production-not-integration-silent"),
        ("unit", "test_config_resolve.py", "OriginProductionFallback.test_resolve_reads_production_after_integration"),
        ("unit", "test_config_resolve.py", "OriginProductionFallback.test_session_notice_silent"),
    ],
    "BUG-24": [  # visible version vs the deployed commit (REQ-W1-041)
        ("unit", "test_skill_rules.py", "VisibleVersionCheck.test_deploy_reads_the_version_file_of_the_deployed_commit"),
        ("unit", "test_skill_rules.py", "VisibleVersionCheck.test_deploy_accepts_any_dev_mark_format"),
        ("unit", "test_skill_rules.py", "VisibleVersionCheck.test_deploy_never_compares_with_the_tip"),
        ("unit", "test_skill_rules.py", "VisibleVersionCheck.test_versioning_rule_says_the_same"),
        ("manual", "visible-version.md"),
    ],
    "BUG-25": [  # composed subagent prompts carry the project.json ban (REQ-W1-081)
        ("lint", "L-34"),
        ("unit", "test_skill_rules.py", "SubagentPromptsCarryTheProjectJsonBan.test_rule_5_puts_the_ban_in_every_prompt"),
        ("unit", "test_skill_rules.py", "SubagentPromptsCarryTheProjectJsonBan.test_a_user_request_to_persist_is_not_delegated"),
        ("unit", "test_skill_rules.py", "SubagentPromptsCarryTheProjectJsonBan.test_impl_dispatch_carries_the_ban"),
        ("table", "subagent-prompt", "sp-01-rerun-prompt-persist-settings-blocked"),
        ("table", "subagent-prompt", "sp-02-first-run-prompt-persist-map-blocked"),
        ("table", "subagent-prompt", "sp-03-ban-line-present-allowed"),
        ("unit", "test_karvey_hooks.py", "Registry.test_order_and_fail_modes_of_section_1_3"),
        ("manual", "no-human-no-mapping.md"),
    ],
    "BUG-26": [  # tracker credentials looked up in .connections.json first (REQ-W1-082)
        ("unit", "test_skill_rules.py", "TrackerCredentialsAreLookedUpEverywhere.test_rule_2_is_a_lookup_order"),
        ("unit", "test_skill_rules.py", "TrackerCredentialsAreLookedUpEverywhere.test_impl_points_to_the_lookup_when_it_touches_the_tracker"),
        ("unit", "test_skill_rules.py", "TrackerCredentialsAreLookedUpEverywhere.test_impl_blocker_keeps_status_and_comments_when_blocked_is_null"),
        ("manual", "per-level-maps.md"),
    ],
    "BUG-27": [  # F-56 (QA D1 security (S-1))
        ("table", "protect-paths", "pp-18-glob-in-state-dir-path-blocked"),
        ("table", "protect-paths", "pp-19-cd-chain-glob-then-mkdir-blocked"),
        ("table", "protect-paths", "pp-20-variable-path-component-blocked"),
        ("table", "protect-paths", "pp-21-bare-wildcard-under-git-into-ledger-blocked"),
    ],
    "BUG-28": [  # F-57 (QA D1 security (S-2, S-3), D2 (E-1))
        ("table", "prod-gate", "pg4-01-inline-alias-to-push-main"),
        ("table", "prod-gate", "pg4-02-configured-alias-to-push-main"),
        ("table", "prod-gate", "pg4-03-inline-remote-push-refspec"),
        ("table", "prod-gate", "pg4-05-configured-upstream-bare-push"),
        ("table", "prod-gate", "pg4-06-configured-remote-push-refspec"),
        ("table", "prod-gate", "pg4-07-send-pack-into-main"),
        ("table", "prod-gate", "pg4-08-xargs-git-push"),
        ("table", "prod-gate", "pg4-10-gh-alias-to-pr-merge"),
        ("table", "prod-gate", "pg4-11-gh-api-merges-endpoint-into-main"),
        ("table", "prod-gate", "pg4-12-gh-api-ref-update-of-main"),
        ("table", "prod-gate", "pg4-13-gh-api-graphql-merge-branch"),
        ("table", "prod-gate", "pg4-19-push-at-sign-from-main"),
        ("table", "prod-gate", "pg4-22-shell-alias-push-into-main"),
        ("table", "git-flow", "gf-bug28-push-at-sign-on-master"),
    ],
    "BUG-29": [  # F-58 (QA D4 impact (I-4))
        ("table", "prod-gate", "pg4-17-push-tags-from-main-allowed"),
    ],
    "BUG-30": [  # F-59 (QA D4 impact (I-3))
        ("table", "prod-gate", "pg4-23-block-says-how-to-record-the-approval"),
        ("table", "prod-gate", "pg4-24-unknown-change-names-the-switch"),
    ],
    "BUG-31": [  # F-60 (QA D4 impact (I-1), D2 (E-4))
        ("table", "subagent-prompt", "sp-08-settings-page-component-allowed"),
        ("table", "subagent-prompt", "sp-09-editor-settings-file-allowed"),
        ("table", "subagent-prompt", "sp-10-tests-for-a-status-mapping-function-allowed"),
        ("table", "subagent-prompt", "sp-11-typographic-apostrophe-ban-allowed"),
        ("table", "subagent-prompt", "sp-12-another-tools-project-json-allowed"),
        ("table", "subagent-prompt", "sp-13-ban-like-sentence-does-not-excuse-a-write-blocked"),
    ],
    "BUG-32": [  # F-61 (QA D1 security (S-6))
        ("unit", "test_fixtures_anonymous.py", "NoRealChatSpaceIds.test_space_ids_are_placeholders"),
    ],
    "BUG-33": [  # F-62 (QA D4 impact (I-2))
        ("unit", "test_state_validate.py", "LegacyRealShapesAreWarnings.test_repos_as_objects_is_a_warning"),
        ("unit", "test_state_validate.py", "LegacyRealShapesAreWarnings.test_generated_as_a_date_is_a_warning"),
    ],
    "BUG-34": [  # F-63 (QA D2 errors (E-2))
        ("unit", "test_karvey_hooks.py", "Dispatch.test_crash_outside_a_guard_applies_the_fail_mode"),
    ],
    "BUG-35": [  # F-64 (QA D2 errors (E-3))
        ("unit", "test_state_validate.py", "NonStringPhase.test_list_phase_in_history_is_a_validation_error"),
        ("unit", "test_state_validate.py", "NonStringPhase.test_active_change_and_dashboard_survive"),
    ],
    "BUG-36": [  # F-65 (QA D2 errors (E-5))
        ("unit", "test_config_resolve.py", "NonStringSettings.test_list_channel_and_tool_are_refused_not_crashes"),
    ],
    "BUG-37": [  # F-66 (QA D2 errors (E-6))
        ("unit", "test_atomicio.py", "LockOwnership.test_release_keeps_a_lock_that_is_not_ours"),
        ("unit", "test_atomicio.py", "LockOwnership.test_breaking_does_not_remove_a_fresh_lock_taken_meanwhile"),
    ],
    "BUG-38": [  # F-67 (QA D2 errors (E-8))
        ("unit", "test_spec_merge.py", "LineEndings.test_bom_and_crlf_are_kept"),
    ],
    "BUG-39": [  # F-68 (QA D4 impact (I-5))
        ("table", "protect-paths", "pp-25-commit-message-mentioning-the-path-allowed"),
        ("table", "protect-paths", "pp-26-echo-text-mentioning-the-record-allowed"),
    ],
    "BUG-40": [  # F-69 (QA D6 versioning)
        ("unit", "test_skill_rules.py", "ChangelogUnreleasedTraceability.test_unreleased_names_the_owner_and_the_model"),
    ],
    "BUG-41": [  # F-70 (QA D7 second opinion (X-1))
        ("unit", "test_state_approve.py", "ProdMarkerScope.test_project_wide_prod_marker_is_not_a_prod_approval_of_a_change"),
        ("unit", "test_state_approve.py", "ProdMarkerScope.test_prod_marker_is_consumed_by_the_approval"),
    ],
    "BUG-42": [  # F-71 (QA D7 second opinion (X-2))
        ("unit", "test_approval_vocab.py", "ConditionalSi.test_conditional_si_is_not_an_approval"),
    ],
    "BUG-43": [  # F-72 (QA D7 second opinion (X-5))
        ("unit", "test_state_approve.py", "ConsumeOnlyWhatClosed.test_prod_marker_survives_a_phase_without_approval"),
    ],
    "BUG-44": [  # F-73 (QA D7 second opinion (X-6))
        ("unit", "test_state_fix.py", "NothingLostInMigration.test_transition_keeps_every_other_field"),
        ("unit", "test_state_fix.py", "NothingLostInMigration.test_gates_skipped_record_is_kept_in_the_reason"),
    ],
    "BUG-45": [  # F-74 (QA D7 second opinion (X-7))
        ("unit", "test_spec_merge.py", "DuplicateIds.test_removed_twice_is_refused_and_nothing_is_written"),
        ("unit", "test_spec_merge.py", "DuplicateIds.test_modified_and_removed_is_refused"),
    ],
    "BUG-46": [  # F-75 (QA D7 second opinion (X-9))
        ("lint", "L-06"),
        ("unit", "test_lint_plugin.py", "L06.test_hand_edits_in_other_words_fail"),
    ],
    "BUG-47": [  # F-92 (QA re-run D7 second opinion (X-1..X-7))
        ("table", "prod-gate", "pg6-01-wildcard-refspec-into-main"),
        ("table", "prod-gate", "pg6-02-matching-colon-refspec"),
        ("table", "prod-gate", "pg6-03-configured-mirror"),
        ("table", "prod-gate", "pg6-04-configured-push-default-matching"),
        ("table", "prod-gate", "pg6-05-tag-shadows-the-pushed-branch"),
        ("table", "prod-gate", "pg6-06-second-production-destination"),
        ("table", "prod-gate", "pg6-07-configured-wildcard-push-refspec"),
    ],
    "BUG-48": [  # F-93 (QA re-run D7 second opinion (X-9))
        ("table", "prod-gate", "pg6-08-gh-auto-merge-unbound"),
        ("table", "prod-gate", "pg6-09-gh-auto-merge-bound-to-the-approved-commit"),
        ("table", "prod-gate", "pg6-10-gh-auto-merge-bound-to-another-commit"),
        ("table", "prod-gate", "pg6-11-az-auto-complete-deferred"),
        ("table", "prod-gate", "pg6-12-glab-merge-without-sha"),
    ],
    "BUG-49": [  # F-94 (QA re-run D7 second opinion (X-10))
        ("unit", "test_state_approve.py", "ReopenSupersedesProd.test_ledger_failure_leaves_the_spec_unreopened"),
        ("unit", "test_state_approve.py", "ReopenSupersedesProd.test_refused_reopen_keeps_the_ledger"),
    ],
    "BUG-50": [  # F-95 (QA re-run D7 second opinion re-check (N-1..N-4))
        ("table", "prod-gate", "pg6-13-refs-wildcard-refspec"),
        ("table", "prod-gate", "pg6-14-push-option-cluster-is-not-a-dry-run"),
        ("table", "prod-gate", "pg6-15-abbreviated-mirror-option"),
        ("table", "prod-gate", "pg6-16-unknown-long-option"),
        ("table", "prod-gate", "pg6-17-remote-name-with-a-slash"),
    ],
    "BUG-51": [  # F-96 (QA re-run D7 second opinion re-check (N-5, N-6))
        ("table", "prod-gate", "pg6-18-dry-run-cancelled-by-no-dry-run"),
        ("table", "prod-gate", "pg6-19-repo-option-names-a-mirror-remote"),
        ("table", "prod-gate", "pg6-20-repo-option-names-a-wildcard-remote"),
    ],
    "BUG-78": [  # merged gates could not be walked past their first phase (wave2-structural F-06)
        ("unit", "test_state_gates.py", "MergedGateAdvance.test_merged_advances_inside_the_gate_without_a_second_question"),
        ("unit", "test_state_gates.py", "MergedGateAdvance.test_merged_leaving_the_gate_needs_the_gate_approval"),
        ("unit", "test_state_gates.py", "MergedGateAdvance.test_merged_needs_the_artifact_generated"),
        ("unit", "test_state_gates.py", "MergedGateAdvance.test_granular_keeps_the_per_phase_approval"),
    ],
    "BUG-79": [  # Deploy asked for the rollback only on PROD; a DEV regression neither a (F-10)
        ('lint', 'L-53'),
        ('unit', 'test_lint_plugin.py', 'L53.test_rollback_question_limited_to_prod_fails'),
        ('unit', 'test_lint_plugin.py', 'L53.test_regression_without_reserved_incident_fails'),
        ('unit', 'test_lint_plugin.py', 'L53.test_no_regression_handling_fails'),
        ('manual', 'deploy-postdeploy.md'),
    ],
    "BUG-80": [  # A retro action's backlog row carried no owner (F-11)
        ('unit', 'test_metrics.py', 'RetroActionOwner.test_retro_skill_writes_owner_in_the_row'),
        ('unit', 'test_metrics.py', 'RetroActionOwner.test_backlog_rule_documents_the_owner_cell'),
        ('manual', 'retro-from-metrics.md'),
    ],
    "BUG-81": [  # Merged gate: a phase sent back by Request changes was still passed ins (F-12)
        ('unit', 'test_state_gates.py', 'MergedGateChangesRequested.test_next_names_the_phase_that_was_sent_back'),
        ('unit', 'test_state_gates.py', 'MergedGateChangesRequested.test_generated_again_after_the_request_passes'),
        ('unit', 'test_state_gates.py', 'MergedGateChangesRequested.test_request_on_an_earlier_generation_only'),
        ('manual', 'import-through-gates.md'),
    ],
    "BUG-52": [  # Post-deploy verification could pass while the service was down, and le (F-13)
        ('unit', 'test_postdeploy.py', 'Verify.test_unreachable_service_is_never_pass'),
        ('unit', 'test_postdeploy.py', 'Verify.test_probe_urls_are_redacted_in_the_evidence'),
        ('unit', 'test_postdeploy.py', 'Verify.test_new_5xx_without_probe_or_observed_value_is_not_evaluated'),
        ('unit', 'test_postdeploy.py', 'Verify.test_non_numeric_threshold_is_not_evaluated_not_a_crash'),
        ('unit', 'test_postdeploy.py', 'Verify.test_malformed_probe_file_counts_as_no_probes'),
        ('unit', 'test_postdeploy.py', 'Verify.test_internal_error_is_an_error_envelope_not_exit_1'),
    ],
    "BUG-53": [  # Requirements written from the template gave coverage 0/0, read as a pa (F-14)
        ('unit', 'test_trace.py', 'WriteAndCheck.test_no_requirement_ids_is_not_evaluated_never_pass'),
        ('unit', 'test_trace.py', 'WriteAndCheck.test_requirements_template_heading_is_read_by_the_trace'),
    ],
    "BUG-54": [  # Timestamps with fractional seconds lost their zone (metrics crash, wro (F-15)
        ('unit', 'test_metrics.py', 'FractionalSecondsKeepTheZone.test_metrics_parse_dt'),
    ],
    "BUG-55": [  # The evidence wrapper stored secrets from the command line and could wr (F-16)
        ('unit', 'test_evidence.py', 'Evidence.test_secrets_in_argv_are_redacted'),
        ('unit', 'test_evidence.py', 'Evidence.test_change_id_outside_changes_dir_refused'),
        ('unit', 'test_evidence.py', 'Evidence.test_missing_trailing_newline_does_not_glue_records'),
        ('unit', 'test_evidence.py', 'Evidence.test_unstartable_command_is_127_not_a_traceback'),
    ],
    "BUG-56": [  # Judge collect could forge findings rows and crash on a bad citation (F-17)
        ('unit', 'test_judges.py', 'Bug56.test_BUG_56_lens_is_sanitised_in_the_row'),
        ('unit', 'test_judges.py', 'Bug56.test_BUG_56_unexpected_lens_is_discarded_with_a_reason'),
        ('unit', 'test_judges.py', 'Bug56.test_BUG_56_non_ascii_digit_cite_discards_only_that_finding'),
        ('unit', 'test_judges.py', 'Bug56.test_BUG_56_collect_twice_is_idempotent'),
        ('unit', 'test_judges.py', 'Bug56.test_BUG_56_diff_file_is_deleted_by_collect'),
        ('unit', 'test_judges.py', 'Bug56.test_BUG_56_collect_never_deletes_a_foreign_diff'),
    ],
    "BUG-57": [  # One malformed archived change crashed or skewed the metrics report (F-18)
        ('unit', 'test_metrics.py', 'MalformedDataIsNa.test_malformed_gate_outcome_phases_skipped_with_reason'),
        ('unit', 'test_metrics.py', 'MalformedDataIsNa.test_prod_approval_before_creation_is_na'),
        ('unit', 'test_metrics.py', 'MalformedDataIsNa.test_deploy_without_zone_is_reported_not_hidden'),
        ('unit', 'test_metrics.py', 'MalformedDataIsNa.test_other_malformed_shapes_never_crash'),
        ('unit', 'test_metrics.py', 'MalformedDataIsNa.test_a_crashing_metric_is_na_not_a_crash'),
    ],
    "BUG-58": [  # karvey-trace crashed with exit 1 (the coverage-refused code) on malfor (F-19)
        ('unit', 'test_trace.py', 'MalformedInputNeverExits1.test_tests_config_as_list_is_invalid_config_not_1'),
        ('unit', 'test_trace.py', 'MalformedInputNeverExits1.test_globs_not_a_list_of_strings_is_invalid_config'),
        ('unit', 'test_trace.py', 'MalformedInputNeverExits1.test_evidence_line_with_non_string_cwd_is_ignored_with_warning'),
        ('unit', 'test_trace.py', 'MalformedInputNeverExits1.test_unexpected_error_exits_internal_never_1'),
    ],
    "BUG-59": [  # Release gate cited the wrong evidence line and read the manifest mode  (F-20)
        ('unit', 'test_release_gate.py', 'Bug59.test_BUG_59_evidence_cite_is_the_physical_line'),
        ('unit', 'test_release_gate.py', 'Bug59.test_BUG_59_manifest_mode_is_the_stricter_of_working_copy_and_reviewed_line'),
        ('unit', 'test_release_gate.py', 'Bug59.test_BUG_59_release_branch_refuses_a_non_semver_version'),
    ],
    "BUG-60": [  # karvey-id: inflated numbers from branch text, burnt numbers on refusal (F-21)
        ('unit', 'test_id_tool.py', 'Bug60.test_BUG_60_branch_scan_applies_the_word_boundary'),
        ('unit', 'test_id_tool.py', 'Bug60.test_BUG_60_qualified_refusal_burns_no_number'),
        ('unit', 'test_id_tool.py', 'Bug60.test_BUG_60_corrupt_ids_json_is_rebuilt_not_exit_5'),
        ('unit', 'test_id_tool.py', 'Bug60.test_BUG_60_release_deletes_only_its_own_lock'),
        ('unit', 'test_id_tool.py', 'Bug60.test_BUG_60_stale_takeover_moves_the_stale_lock_aside'),
        ('unit', 'test_id_tool.py', 'Bug60.test_BUG_60_takeover_does_not_steal_a_fresh_lock'),
    ],
    "BUG-61": [  # State validation ignored the check-mode registry, never refused a miss (F-22)
        ('unit', 'test_state_validate.py', 'StrictModeFromRegistry.test_registry_blocking_is_strict_and_missing_lane_errors'),
        ('unit', 'test_state_validate.py', 'StrictModeFromRegistry.test_advisory_keeps_validate_quiet_about_lane'),
        ('unit', 'test_state_judges.py', 'JudgeRun.test_nan_and_infinite_cost_refused'),
    ],
    "BUG-62": [  # An agent could make QA optional by a lane "raise" (F-23)
        ('unit', 'test_state_lane.py', 'LaneChanges.test_REQ_W2_016_raise_that_makes_qa_optional_is_a_lower'),
        ('unit', 'test_state_lane.py', 'LaneChanges.test_REQ_W2_016_raise_keeps_every_mandatory_phase'),
    ],
    "BUG-63": [  # The trailer guard missed `git commit -am "msg"` (F-24)
        ('table', 'trailer', 'tr-11-combined-am-without-trailer-blocks'),
        ('table', 'trailer', 'tr-12-combined-am-with-trailer-silent'),
    ],
    "BUG-64": [  # Lint L-47 (check-mode registry invariants) was declared but not implem (F-25)
        ('lint', 'L-47'),
        ('unit', 'test_lint_plugin.py', 'L47.test_missing_line_default_fails'),
        ('unit', 'test_lint_plugin.py', 'L47.test_313_blocking_fails'),
        ('unit', 'test_lint_plugin.py', 'L47.test_40_differs_without_decision_fails'),
        ('unit', 'test_lint_plugin.py', 'L47.test_unregistered_id_in_a_script_fails'),
    ],
    "BUG-65": [  # The how-gate summary reported the post-deploy contract missing althoug (F-26)
        ('unit', 'test_context_gate.py', 'GateSummary.test_complete_infra_contract_clears_the_architecture_gaps'),
    ],
    "BUG-66": [  # The method page kept the old skill / support / rule counts (F-05)
        ('unit', 'test_page_static.py', 'CurrentCounts.test_counts_match_the_files'),
    ],
    "BUG-67": [  # The impl skill never told the agent to add the Karvey-Change trailer (F-27)
        ('lint', 'L-42'),
        ('unit', 'test_lint_plugin.py', 'L42ImplTrailer.test_impl_without_the_trailer_rule_fails'),
    ],
    "BUG-68": [  # A RESUELTO incident written from the rule's template read as having no (F-39)
        ('unit', 'test_context.py', 'RegressionHeadingOfTheRule.test_rule_heading_is_read'),
    ],
    "BUG-69": [  # The evidence wrapper wrote the user's home path into committed evidenc (F-40)
        ('unit', 'test_evidence.py', 'Evidence.test_home_directory_is_collapsed'),
    ],
    "BUG-70": [  # The release gate recorded production from a project-wide prod marker a (F-41)
        ('unit', 'test_state_gates.py', 'Release.test_project_wide_prod_marker_does_not_approve_prod_at_the_release_gate'),
        ('unit', 'test_state_gates.py', 'Release.test_release_gate_consumes_the_prod_marker'),
        ('unit', 'test_state_approve.py', 'ProdMarkerScope.test_project_wide_prod_marker_is_not_a_prod_approval_of_a_change'),
        ('unit', 'test_state_approve.py', 'ProdMarkerScope.test_prod_marker_is_consumed_by_the_approval'),
    ],
    "BUG-71": [  # Evidence redaction hid ordinary flags' arguments (`--passWithNoTests < (F-42)
        ('unit', 'test_evidence.py', 'Evidence.test_ordinary_flags_that_contain_a_secret_word_are_kept'),
    ],
    "BUG-72": [  # Under strict mode a missing lane named a remedy that is refused outsid (F-43)
        ('unit', 'test_state_validate.py', 'StrictModeFromRegistry.test_registry_blocking_is_strict_and_missing_lane_errors'),
    ],
    "BUG-73": [  # The manifest prod path swallowed a failed marker consume (F-62)
        ('unit', 'test_state_gates.py', 'ProdManifest.test_a_marker_that_cannot_be_consumed_is_reported'),
    ],
    "BUG-74": [  # A project-wide plan marker could lower any change's lane, repeatedly (F-63)
        ('unit', 'test_state_lane.py', 'LaneChanges.test_lower_needs_the_changes_own_marker_and_consumes_it'),
    ],
    "BUG-75": [  # Evidence kept URL query secrets, auth headers and a home path in `--ju (F-65, F-66)
        ('unit', 'test_evidence.py', 'Evidence.test_query_tokens_and_auth_headers_are_redacted'),
        ('unit', 'test_evidence.py', 'Evidence.test_junit_path_home_is_collapsed'),
    ],
    "BUG-76": [  # A judge could declare itself cross-model in its own output (F-67)
        ('unit', 'test_judges.py', 'Bug76.test_judge_cannot_declare_itself_cross_model'),
    ],
    "BUG-77": [  # The security scan wrote absolute user paths into committed evidence an (F-71)
        ('unit', 'test_security_scan.py', 'Run.test_no_absolute_path_in_argv_or_evidence'),
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
        for n in range(5, 47):
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
