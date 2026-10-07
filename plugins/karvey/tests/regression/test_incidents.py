"""Regression index BUG-05..BUG-51, BUG-138..BUG-161 (architecture §6.4, REQ-W1-107, E1.F14.T3).

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
        ("unit", "test_state_approve.py", "ProdMarkerScope.test_prod_marker_is_used_once_by_the_approval"),
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
    # hotfix 3.12.1 (prod-gate-scope, D-43/D-45); BUG-52..137 are held by other branches
    "BUG-138": [  # F-01: prod approval bound to the active change instead of the named one
        ("table", "approval", "ap-hf-02-named-change-only-on-a-branch-records-nothing"),
        ("table", "approval", "ap-hf-03-named-change-nowhere-records-nothing"),
        ("table", "approval", "ap-hf-05-several-active-records-nothing"),
        ("table", "approval", "ap-hf-06-several-named-records-nothing"),
        ("unit", "test_approval_scope.py", "ProdScope.test_named_change_in_a_worktree_is_named_as_the_fix"),
        ("unit", "test_approval_scope.py", "ProdScope.test_named_change_on_a_branch_names_the_branch"),
    ],
    "BUG-139": [  # F-04 / BL-64: read-only listings of the state paths blocked
        ("table", "protect-paths", "pp-hf-01-ls-then-echo"),
        ("table", "protect-paths", "pp-hf-02-cat-into-json-tool"),
        ("table", "protect-paths", "pp-hf-03-ls-of-rev-parse-substitution"),
    ],
    "BUG-140": [  # F-05: another agent's profile (and a sensitive handoff) injected
        ("table", "session", "ss-hf-01-ancestor-folder-profile-not-injected"),
        ("table", "session", "ss-hf-02-team-folder-not-a-repo-gets-nothing"),
        ("table", "session", "ss-hf-03-unmapped-repo-no-default-role"),
        ("table", "session", "ss-hf-05-cwd-changed-to-another-repo-ambiguous"),
        ("table", "session", "ss-hf-06-two-candidates-inject-nothing"),
        ("unit", "test_session_profile.py", "SessionProfile.test_bug140_sensitive_handoff_withheld_on_explicit_restore_elsewhere"),
    ],
    "BUG-141": [  # F-06: prod-gate decided by the session's repo, not the PR's
        ("unit", "test_prodgate_target.py", "Target.test_merge_into_the_target_integration_branch_passes"),
        ("unit", "test_prodgate_target.py", "Target.test_production_merge_is_checked_on_the_target_ledger"),
        ("unit", "test_prodgate_target.py", "Target.test_non_karvey_target_passes_with_a_warning"),
        ("table", "prod-gate", "pg-hf-01-repo-flag-names-a-non-karvey-repo"),
    ],
    "BUG-142": [  # F-07: production OK asked through a question tool
        ("lint", "L-80"),
        ("unit", "test_lint_plugin.py", "L80.test_question_tool_for_prod_ok_fails"),
    ],
    "BUG-143": [  # F-08: a production-shaped phrase that recorded nothing printed nothing
        ("table", "approval", "ap-hf-07-negated-prod-phrase-says-why"),
        ("table", "approval", "ap-hf-09-late-prod-phrase-says-why"),
        ("table", "approval", "ap-hf-10-not-recorded-line-suggests-the-phrase"),
    ],
    "BUG-144": [  # F-09: the approve refusal did not name the markers found
        ("unit", "test_state_repos.py", "Refusal.test_refusal_lists_markers_and_missing_piece"),
        ("unit", "test_state_repos.py", "Refusal.test_refusal_with_no_marker"),
    ],
    "BUG-145": [  # F-12: the not-a-Karvey-repo warning reachable for Karvey targets
        ("unit", "test_prodgate_identity.py", "Identity.test_look_alike_clone_in_the_cwd_does_not_bypass"),
        ("unit", "test_prodgate_identity.py", "Identity.test_look_alike_sibling_does_not_shadow_the_real_clone"),
        ("unit", "test_prodgate_identity.py", "Identity.test_renamed_repo_is_identified_by_the_host"),
        ("unit", "test_prodgate_identity.py", "Identity.test_fork_upstream_is_identified_by_the_head_commit"),
        ("unit", "test_prodgate_identity.py", "Identity.test_azure_repo_guid_is_resolved_by_the_host"),
        ("unit", "test_prodgate_identity.py", "Identity.test_session_in_the_folder_that_holds_the_repos"),
        ("unit", "test_prodgate_identity.py", "Identity.test_named_repo_without_a_clone_passes_only_into_integration"),
    ],
    "BUG-146": [  # F-13: REST parser evasions
        ("unit", "test_restcalls_evasions.py", "Evasions.test_every_url_is_classified"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_unknown_or_value_options_do_not_hide_the_url"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_curl_config_fails_closed"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_wget_separate_option_values"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_branch_writes_through_other_endpoints"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_here_documents_and_encoded_paths"),
    ],
    "BUG-147": [  # F-14: a token in a fail-closed message
        ("unit", "test_karvey_hooks.py", "Dispatch.test_bug147_exception_text_never_reaches_the_message"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_httpie_auth_is_not_the_url_and_is_not_kept"),
    ],
    "BUG-148": [  # F-15: approval scope gaps after BUG-138
        ("unit", "test_approval_scope.py", "ProdScope.test_bug148_change_id_without_hyphen_on_a_branch"),
        ("unit", "test_approval_scope.py", "ProdScope.test_bug148_versions_and_release_names_are_not_change_ids"),
        ("unit", "test_approval_scope.py", "ProdScope.test_bug148_unknown_word_is_never_the_suggested_change"),
        ("unit", "test_approval_scope.py", "ProdScope.test_bug148_two_named_ids_one_inside_the_other"),
    ],
    "BUG-149": [  # F-16: L-80 wordings and negations
        ("lint", "L-80"),
        ("unit", "test_lint_plugin.py", "L80Bug149.test_spanish_and_other_wordings_fail"),
        ("unit", "test_lint_plugin.py", "L80Bug149.test_unrelated_not_is_not_a_negation"),
        ("unit", "test_lint_plugin.py", "L80Bug149.test_other_question_in_the_same_paragraph_passes"),
    ],
    "BUG-150": [  # F-17: a worktree of the same repo read as two repos
        ("unit", "test_session_profile.py", "SessionProfile.test_bug150_session_moved_into_a_worktree_of_the_same_repo"),
    ],
    "BUG-151": [  # F-19: QA re-check — fake Karvey clone, curl globs, dot segments, raw HTTP, Azure repo answer
        ("unit", "test_prodgate_identity.py", "Identity.test_bug151_fake_karvey_clone_cannot_decide_or_switch_the_gate_off"),
        ("unit", "test_prodgate_identity.py", "Identity.test_bug151_azure_host_answer_names_the_repo"),
        ("unit", "test_prodgate_identity.py", "Identity.test_karvey_repo_in_another_wrapper_folder_is_found"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_bug151_curl_globs_and_dot_segments"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_bug151_raw_http_by_hand"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_bug151_credentials_in_variables_do_not_block_a_non_completing_update"),
        ("unit", "test_restcalls_evasions.py", "Evasions.test_bug151_text_output_is_not_a_request"),
    ],
    "BUG-152": [  # F-20: curl request-target / variable expansion; named fake clone switch-off
        ("unit", "test_restcalls_evasions.py", "Evasions.test_bug152_request_target_and_variable_expansion"),
        ("unit", "test_prodgate_identity.py", "Identity.test_bug152_switch_off_of_a_named_clone_needs_a_trusted_session"),
    ],
    "BUG-153": [("unit", "test_restcalls_evasions.py", "Evasions.test_bug153_scheme_less_urls")],  # F-21
    "BUG-154": [  # F-22: a checkpoint save blocked by the plan-gate
        ("table", "plan-gate", "cp-01-handoff-save-needs-no-approval"),
        ("table", "plan-gate", "cp-03-change-checkpoint-needs-no-approval"),
        ("table", "plan-gate", "cp-07-symlinked-handoff-gated"),
        ("table", "plan-gate", "cp-10-handoff-write-with-another-write-gated"),
        ("unit", "test_plangate_checkpoint.py", "TeamLayout.test_own_team_profile_files_need_no_approval"),
        ("unit", "test_plangate_checkpoint.py", "TeamLayout.test_another_agents_profile_and_other_files_stay_gated"),
    ],
    "BUG-155": [  # F-24: QA of the D-47 delta
        ("table", "plan-gate", "d47-22-terraform-global-flag-before-verb"),
        ("table", "plan-gate", "d47-26-sql-from-a-pipe-is-gated"),
        ("table", "plan-gate", "d47-35-az-config-list-is-free"),
        ("table", "plan-gate", "d47-40-alembic-upgrade-is-gated"),
        ("table", "plan-gate", "d47-43-curl-delete-is-gated"),
        ("unit", "test_plangate_checkpoint.py", "ProjectMarkerSession.test_same_session_proceeds_another_session_is_gated"),
        ("unit", "test_marker.py", "TTL.test_d47_stop_withdraws_and_prod_use_keeps_the_plan"),
    ],
    "BUG-156": [("unit", "test_plangate_symlinked_tmp.py",
                 "SymlinkedTemp.test_checkpoint_rows_pass_under_a_symlinked_temp_folder")],  # F-25
    "BUG-157": [  # F-26: a phase close consumed the plan approval
        ("unit", "test_plangate_checkpoint.py", "ApprovalSurvivesPhases.test_one_approval_covers_the_phases_and_the_implementation"),
        ("unit", "test_state_approve.py", "Consumption.test_phase_close_keeps_the_plan_approval"),
        ("unit", "test_state_approve.py", "Consumption.test_project_marker_used_as_evidence_is_kept"),
        ("unit", "test_state_approve.py", "Consumption.test_bug157_d1_a_message_evidences_only_the_phase_it_was_typed_in"),
    ],
    "BUG-158": [  # approval-by-name F-01: a change of another clone was refused, the active change suggested
        ("unit", "test_approval_by_name.py", "ByName.test_bug158_named_change_of_a_sibling_clone_is_recorded_there"),
        ("unit", "test_approval_by_name.py", "ByName.test_bug158_two_owning_clones_record_nothing_and_are_listed"),
        ("unit", "test_approval_by_name.py", "ByName.test_bug158_unknown_word_never_suggests_the_active_change"),
        ("unit", "test_approval_by_name.py",
         "ByName.test_bug158_negated_phrase_naming_another_clone_never_suggests_the_active_change"),
        ("table", "approval", "ap-an-01-named-change-of-a-sibling-clone-recorded-there"),
        ("table", "approval", "ap-an-02-two-clones-hold-the-named-change-records-nothing"),
    ],
    "BUG-159": [  # approval-by-name F-02: PR and version in the phrase read as mandatory
        ("unit", "test_state_repos.py", "Refusal.test_refusal_lists_markers_and_missing_piece"),
        ("lint", "L-82"),
    ],
    "BUG-160": [  # approval-by-name F-03 (QA D1 H1): any word routed the approval to another clone
        ("unit", "test_approval_by_name.py", "D1OnBug158.test_d1_a_vocabulary_word_never_names_a_change_of_another_clone"),
        ("unit", "test_approval_by_name.py", "D1OnBug158.test_d1_c_an_ordinary_word_never_names_a_change_of_another_clone"),
        ("unit", "test_approval_by_name.py", "D1OnBug158.test_d1_e_outside_a_project_a_vocabulary_word_records_nothing"),
        ("unit", "test_approval_by_name.py", "D1OnBug158.test_d1_an_uncommitted_change_of_another_clone_does_not_count"),
        ("unit", "test_approval_by_name.py", "D1OnBug158.test_d7_f1_common_words_never_route_to_another_clone"),
        ("unit", "test_approval_by_name.py",
         "D1OnBug158.test_d1_h1b_a_hyphenless_id_of_another_clone_is_never_recorded_from_here"),
        ("table", "approval", "ap-an-03-common-word-never-routes-to-another-clone"),
    ],
    "BUG-161": [  # approval-by-name F-04 (QA D7 F2, F3)
        ("unit", "test_approval_by_name.py", "D1OnBug158.test_d7_f2_one_id_here_and_one_in_another_clone_records_nothing"),
        ("unit", "test_approval_by_name.py",
         "D1OnBug158.test_d7_f3_negated_phrase_naming_a_hyphenless_id_elsewhere_never_suggests_the_active_change"),
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
