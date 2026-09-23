# Graph Report - karvey  (2026-09-23)

## Corpus Check
- 98 files · ~161,270 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 8)

## Summary
- 712 nodes · 2516 edges · 26 communities
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 248 edges (avg confidence: 0.88)
- Token cost: 1,588,546 input · 0 output

## Community Hubs (Navigation)
- Hotfix 3.11.2 & Incidents
- Releases 3.9–3.11 & Changes
- Team Layer (3.8)
- Team-Layer Findings & Equivalences
- Discovery Backlog
- Panel: Hooks & Context Findings
- Method Page & Deploy Flow
- EARS, Infra & Spec Rules
- Judges & Test-First (R-11, R-12)
- Living Specs & docs/spec
- Causal Investigation
- Pipeline & Plugin-as-Code
- Early Release History
- State Machine & Lanes
- Gates, Interruptions & Rule Drift
- Change Lanes & Approvals
- Estimation & ClickUp Adapter
- Graphify & Ritual Overhead
- Panel Reports & Design System
- Notifications Requirements
- Security Tiers
- Licensing & Trademark
- README & Method Page
- Logical States & Adapters
- team-adapters PRD
- Community 25

## God Nodes (most connected - your core abstractions)
1. `Karvey 3.11.1 Expert Panel Decision Report` - 99 edges
2. `Karvey Method Page (docs/karvey.html)` - 83 edges
3. `karvey-deploy SKILL` - 83 edges
4. `Change team-adapters` - 73 edges
5. `Discovery Backlog rule` - 73 edges
6. `karvey-qa Skill` - 66 edges
7. `karvey-init Skill` - 62 edges
8. `Retroactive QA review team-adapters PRs #17-#19` - 56 edges
9. `karvey-impl Skill` - 55 edges
10. `Multi-agent and Multi-repo rule` - 53 edges

## Surprising Connections (you probably didn't know these)
- `Stack-agnostic (targets)` --references--> `Stack Agnosticism (Targets) rule`  [INFERRED]
  README.md → plugins/karvey/skills/karvey/rules/targets.md
- `Constraint: Claude Code plugin has no install hook` --rationale_for--> `Team settings asked on first use`  [INFERRED]
  docs/spec/changes/team-adapters/prd.md → README.md
- `Knowledge graph of the method (graphify-out/)` --references--> `Knowledge Sync rule`  [INFERRED]
  README.md → plugins/karvey/skills/karvey/rules/knowledge-sync.md
- `BUG-NN incident tracker with state history` --references--> `Incident Tracking rule`  [INFERRED]
  README.md → plugins/karvey/skills/karvey/rules/incident-tracking.md
- `Discovery backlog (swept at archive)` --references--> `Discovery Backlog rule`  [INFERRED]
  README.md → plugins/karvey/skills/karvey/rules/backlog.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Hotfix 3.11.2 lane (BUG-01..04 + regression suite)** — changelog_release_3_11_2, docs_bugs_dev_testing_bug_01, docs_bugs_dev_testing_bug_02, docs_bugs_dev_testing_bug_03, docs_bugs_dev_testing_bug_04, plugins_karvey_hooks_tests_test_hooks, plugins_karvey_hooks_karvey_session_context, plugins_karvey_hooks_karvey_statusline [EXTRACTED 1.00]
- **Karvey pipeline 0-12 phase skills** — plugins_karvey_skills_karvey_grill_skill, plugins_karvey_skills_karvey_init_skill, plugins_karvey_skills_karvey_requirements_skill, plugins_karvey_skills_karvey_mockup_skill, plugins_karvey_skills_karvey_design_graphic_skill, plugins_karvey_skills_karvey_architecture_skill, plugins_karvey_skills_karvey_infra_skill, plugins_karvey_skills_karvey_tasks_skill, plugins_karvey_skills_karvey_impl_skill, plugins_karvey_skills_karvey_test_skill, plugins_karvey_skills_karvey_qa_skill, plugins_karvey_skills_karvey_deploy_skill, plugins_karvey_skills_karvey_archive_skill [EXTRACTED 1.00]
- **Iteration loop: findings routed by karvey-iterate to three edges** — readme_findings_md, plugins_karvey_skills_karvey_iterate_skill, readme_bug_edge, readme_spec_gap_edge, readme_emergent_edge, readme_convergence_gate, plugins_karvey_skills_karvey_test_skill, plugins_karvey_skills_karvey_qa_skill, plugins_karvey_skills_karvey_browse_skill [EXTRACTED 1.00]
- **Team settings on first use (team-adapters)** — readme_team_settings_first_use, readme_notification_channels, readme_management_tools, readme_five_logical_states, readme_project_json, plugins_karvey_skills_karvey_rules_notifications, plugins_karvey_skills_karvey_rules_management_adapters, plugins_karvey_skills_karvey_init_skill [EXTRACTED 1.00]
- **Open high findings blocking team-adapters QA** — revision_pr_17_19_20260923_qa_verdict, docs_spec_changes_team_adapters_findings_f_05, docs_spec_changes_team_adapters_findings_f_06, docs_spec_changes_team_adapters_findings_f_07, docs_spec_changes_team_adapters_findings_f_08, docs_bugs_dev_testing_bug_05, docs_bugs_dev_testing_bug_06, docs_spec_backlog_wave1_hardening [EXTRACTED 1.00]
- **Karvey trademark policy and its copies** — trademark, plugins_karvey_trademark, plugins_karvey_skills_karvey_trademark, trademark_karvey_trademark, _github_workflows_close_external_prs [INFERRED 0.85]
- **Iteration loop feedback edges** — docs_karvey_iteration_loop, docs_karvey_finding_bug, docs_karvey_finding_spec_gap, docs_karvey_finding_emergent, plugins_karvey_skills_karvey_iterate_skill, docs_karvey_findings_inbox [EXTRACTED 1.00]
- **Team-layer handoff and session reinjection flow** — plugins_karvey_skills_karvey_checkpoint_skill, plugins_karvey_hooks_karvey_session_context, docs_spec_changes_archive_2026_09_22_team_layer_requirements_state_json, docs_spec_changes_archive_2026_09_22_team_layer_prd_handoff_artifact, docs_spec_changes_archive_2026_09_22_team_layer_requirements_req_team_handoff [EXTRACTED 1.00]
- **Retroactive QA routing: findings -> BUG tracker / spec-gap / backlog** — revision_pr_17_19_20260923, docs_spec_changes_team_adapters_findings, docs_bugs_dev_testing, docs_spec_incidents_index, docs_spec_backlog, plugins_karvey_skills_karvey_rules_iteration_loop [EXTRACTED 1.00]
- **team-adapters change: settings on first use for notifications + management** — docs_spec_changes_team_adapters_prd, docs_spec_changes_team_adapters_requirements, docs_spec_backlog_bl_02, docs_spec_backlog_bl_03, plugins_karvey_skills_karvey_rules_notifications, plugins_karvey_skills_karvey_rules_management_adapters, readme_team_settings_first_use [EXTRACTED 1.00]
- **Wave 1: correction and quick wins (3.12.0)** — docs_spec_reviews_2026_09_23_panel_review_r_01, docs_spec_reviews_2026_09_23_panel_review_r_02, docs_spec_reviews_2026_09_23_panel_review_r_03, docs_spec_reviews_2026_09_23_panel_review_r_04, docs_spec_reviews_2026_09_23_panel_review_r_05, docs_spec_reviews_2026_09_23_panel_review_r_06, docs_spec_reviews_2026_09_23_panel_review_r_07, docs_spec_reviews_2026_09_23_panel_review_r_16, docs_spec_reviews_2026_09_23_panel_review_r_17, docs_spec_reviews_2026_09_23_panel_review_r_18, docs_spec_reviews_2026_09_23_panel_review_r_21, docs_spec_reviews_2026_09_23_panel_review_r_22 [EXTRACTED 1.00]
- **Wave 2: structural (3.13.0 advisory / 4.0.0 blocking)** — docs_spec_reviews_2026_09_23_panel_review_r_08, docs_spec_reviews_2026_09_23_panel_review_r_09, docs_spec_reviews_2026_09_23_panel_review_r_10, docs_spec_reviews_2026_09_23_panel_review_r_11, docs_spec_reviews_2026_09_23_panel_review_r_12, docs_spec_reviews_2026_09_23_panel_review_r_13, docs_spec_reviews_2026_09_23_panel_review_r_14, docs_spec_reviews_2026_09_23_panel_review_r_20, docs_spec_reviews_2026_09_23_panel_review_r_23, docs_spec_reviews_2026_09_23_panel_review_r_17 [EXTRACTED 1.00]
- **Wave 3: optimization (4.1.0)** — docs_spec_reviews_2026_09_23_panel_review_r_15, docs_spec_reviews_2026_09_23_panel_review_r_19, docs_spec_reviews_2026_09_23_panel_review_r_24, docs_spec_reviews_2026_09_23_panel_review_r_25, docs_spec_reviews_2026_09_23_panel_review_r_26, docs_spec_reviews_2026_09_23_panel_review_r_27, docs_spec_reviews_2026_09_23_panel_review_r_28, docs_spec_reviews_2026_09_23_panel_review_r_29, docs_spec_reviews_2026_09_23_panel_review_r_30 [EXTRACTED 1.00]
- **Gates before production merge** — plugins_karvey_skills_karvey_deploy_skill_release_gate_step0, plugins_karvey_skills_karvey_deploy_skill_pr_gates_verification, plugins_karvey_skills_karvey_deploy_skill_approvals_prod, plugins_karvey_skills_karvey_deploy_skill_six_step_checklist, plugins_karvey_skills_karvey_deploy_skill_canary_loop [EXTRACTED 1.00]
- **Cross-cutting support skills that never modify spec.json:phase** — plugins_karvey_skills_karvey_benchmark_models_skill, plugins_karvey_skills_karvey_browse_skill, plugins_karvey_skills_karvey_checkpoint_skill, plugins_karvey_skills_karvey_context_skill, plugins_karvey_skills_karvey_decisions_skill, plugins_karvey_skills_karvey_devex_skill, plugins_karvey_skills_karvey_diagram_skill, plugins_karvey_skills_karvey_docs_skill, plugins_karvey_skills_karvey_guard_skill, plugins_karvey_skills_karvey_health_skill, plugins_karvey_skills_karvey_import_skill [EXTRACTED 1.00]
- **Team settings on first use (3.10)** — plugins_karvey_skills_karvey_init_skill_team_settings_step, plugins_karvey_skills_karvey_rules_notifications, plugins_karvey_skills_karvey_rules_management_adapters, docs_karvey_five_logical_states, plugins_karvey_hooks_karvey_session_context [EXTRACTED 1.00]
- **Findings Feedback Loop (observe/classify -> route)** — plugins_karvey_skills_karvey_test_skill_findings_classification, plugins_karvey_skills_karvey_qa_skill_nine_dimension_review, plugins_karvey_skills_karvey_iterate_skill_iteration_engine_router, plugins_karvey_skills_karvey_iterate_skill_bug_route_micro_loop, plugins_karvey_skills_karvey_iterate_skill_spec_revision_ripple_set, plugins_karvey_skills_karvey_iterate_skill_emergent_backlog_route, plugins_karvey_skills_karvey_skill_convergence_gate [EXTRACTED 1.00]
- **Cross-cutting support skills that never advance spec.json:phase** — plugins_karvey_skills_karvey_investigate_skill, plugins_karvey_skills_karvey_iterate_skill, plugins_karvey_skills_karvey_retro_skill, plugins_karvey_skills_karvey_scrape_skill, plugins_karvey_skills_karvey_second_opinion_skill, plugins_karvey_skills_karvey_standards_skill, plugins_karvey_skills_karvey_team_skill [EXTRACTED 1.00]
- **Human-in-the-loop Controls** — plugins_karvey_skills_karvey_impl_skill_human_tasks_awaiting_human, plugins_karvey_skills_karvey_tasks_skill_human_task_format, plugins_karvey_skills_karvey_infra_skill_ops_command_plan, plugins_karvey_skills_karvey_test_skill_infrastructure_tests [INFERRED 0.85]
- **Production safety gates** — plugins_karvey_skills_karvey_rules_deploy_workflow_pipeline_only_deploy, plugins_karvey_skills_karvey_rules_deploy_workflow_pr_gates_before_ok, plugins_karvey_skills_karvey_rules_multi_agent_approvals_with_ref, plugins_karvey_skills_karvey_rules_multi_agent_hotfix_lane, plugins_karvey_skills_karvey_rules_deploy_workflow_zero_downtime [INFERRED 0.85]
- **Opt-in enforcement hooks (git-flow, plan-gate, standards-guard, clickup-sync-guard)** — plugins_karvey_skills_karvey_rules_enforcement_git_flow_guard, plugins_karvey_skills_karvey_rules_enforcement_plan_gate, plugins_karvey_skills_karvey_rules_engineering_standards_standards_guard, plugins_karvey_skills_karvey_rules_phase_close_clickup_sync_guard [EXTRACTED 1.00]
- **Finding routing: findings.md to BUG-NN, spec-revision, backlog** — plugins_karvey_skills_karvey_rules_iteration_loop_findings_md, plugins_karvey_skills_karvey_rules_iteration_loop_spec_revision_subcycle, plugins_karvey_skills_karvey_rules_backlog_backlog_md [EXTRACTED 1.00]
- **Nothing-lost feedback artifacts (findings, BUG-NN, backlog, revision history)** — plugins_karvey_skills_karvey_rules_backlog_backlog_md, plugins_karvey_skills_karvey_rules_incident_tracking_bug_nn_tracker, plugins_karvey_skills_karvey_rules_incident_tracking_incidents_index, plugins_karvey_skills_karvey_rules_living_specs_revision_history, plugins_karvey_skills_karvey_rules_phase_close_four_action_ritual [INFERRED 0.85]
- **Team settings stored in project.json** — plugins_karvey_skills_karvey_rules_project_config_project_json_schema, plugins_karvey_skills_karvey_rules_notifications_notification_settings, plugins_karvey_skills_karvey_rules_management_adapters_five_logical_states, plugins_karvey_skills_karvey_rules_project_config_branch_flow, plugins_karvey_skills_karvey_rules_project_config_standards_source [INFERRED 0.85]
- **Visible version by environment (rule, deploy step, canary check, release)** — plugins_karvey_skills_karvey_rules_versioning_visible_version_by_env, plugins_karvey_skills_karvey_deploy_skill_step_2_4_bis_visible_version, plugins_karvey_skills_karvey_deploy_skill_canary_loop, changelog_release_3_11_0, plugins_karvey_skills_karvey_rules_versioning_version_file_source [EXTRACTED 1.00]

## Communities (26 total, 0 thin omitted)

### Community 0 - "Hotfix 3.11.2 & Incidents"
Cohesion: 0.08
Nodes (90): Release 3.11.1 (2026-09-23), Release 3.11.2 (2026-09-23), Incident tracker karvey (BUG-NN), BUG-01 karvey-init --settings created a phantom change and a real tracker Epic, BUG-02 Session-hook settings nudge fired where it should not and mis-read project.json, BUG-03 Odd resets_at took the statusline down; time left truncated, BUG-04 Statusline debug copy at fixed shared world-readable /tmp path, BUG-05 impl decides dependencies and resume with non-logical states (+82 more)

### Community 1 - "Releases 3.9–3.11 & Changes"
Cohesion: 0.06
Nodes (75): Release 3.10.0 (2026-09-22), Release 3.11.0 (2026-09-22), Release 3.9.0 (2026-09-22), Release 3.9.1 (2026-09-22), BL-01 Run graphify over the repo, Karvey 3.11.1 Review: Agent-Execution Judge (AG), AG-02: Resolve contradictions forcing agent to break hard rules, AG-10: Release gate, dashboard, spec merge and health score as scripts (+67 more)

### Community 2 - "Team Layer (3.8)"
Cohesion: 0.06
Nodes (67): Release 3.8.0 (2026-09-22), Agent-Team Layer (optional), Measured team cost evidence (6 agents, 3 days, ~US$1,000), F-04 plugin cannot declare statusline (BL-36), team-layer PRD, Agent handoff captured from commands, Reference run: 6-agent team, 3 days, ~US$1,000, Change team-layer: optional team layer (+59 more)

### Community 3 - "Team-Layer Findings & Equivalences"
Cohesion: 0.05
Nodes (62): Kiro / gstack equivalence table, team-layer Findings, F-01 health checks team-layer readiness (BL-34), F-02 sampled weekly audit incl. director (BL-35), F-03 karvey-team cost collection unproven (BL-37), AG-11: Short frontmatter descriptions without generic/brand triggers, AG-14: Portability to other runtimes and teams, DM-08: Security gate with deterministic tools, not only LLM judgment (+54 more)

### Community 4 - "Discovery Backlog"
Cohesion: 0.10
Nodes (52): Discovery Backlog Karvey, BL-02 Notifications configurable per team, BL-03 Task-management tool + status flow configurable, BL-04 [Ola 1] Single state machine with schema and karvey-state.py, BL-05 [Ola 1] Hooks that do what they say, prod-gate, table tests, BL-06 [Ola 1] Take deploy/archive commits out of dev; order checklist, BL-07 [Ola 1] Single versioning moment, BL-08 [Ola 1] Keep estimate and actual (+44 more)

### Community 5 - "Panel: Hooks & Context Findings"
Cohesion: 0.08
Nodes (50): AG-03: Hooks must cover what the method calls 'never' (prod-gate), AG-04: Per-phase context budget and progressive loading (_core.md), DM-05: Hooks must do what rules say, with tests (bats), H-10: plan-gate false positive on 2> and destructive commands pass, H-11: plan-gate marker never expires, is global and agent-created, H-12: git-flow-guard evasions and false positive, H-13: enforcement.md promises integration-push block that is not implemented, H-14: Described hooks do not exist (clickup-sync-guard, standards-guard) (+42 more)

### Community 6 - "Method Page & Deploy Flow"
Cohesion: 0.10
Nodes (35): Karvey Method Page (docs/karvey.html), Branch hygiene, clickup-sync-guard (described in rule), Deploy & Branch Flow (feature -> dev -> PR -> master), Finding type: bug, Finding type: emergent, Finding type: spec-gap, findings.md single inbox (+27 more)

### Community 7 - "EARS, Infra & Spec Rules"
Cohesion: 0.08
Nodes (29): Infra Security Review Gate, EARS Format (init copy), EARS patterns (Ubiquitous/Event/State/Conditional/Optional), Litmus test: requirements vs design (technology-free), Security Tiers (init copy), Forbidden security anti-patterns, Security Tiers 1-4 (Public/Authenticated/Privileged/Critical), prd.md PRD template (+21 more)

### Community 8 - "Judges & Test-First (R-11, R-12)"
Cohesion: 0.12
Nodes (27): DM-07: Test-first and verifiable REQ->task->commit->test traceability matrix, Owner Mauricio (proposal JU-01), R-11: Expert judge panels at early gates (JU-01, karvey-judges), R-12: Test-first and REQ->task->commit->test traceability matrix, Karvey Architecture (Phase 5), Mandatory Edge Cases section, Architecture Review Gate, Test Coverage Plan (contract for karvey-test) (+19 more)

### Community 9 - "Living Specs & docs/spec"
Cohesion: 0.08
Nodes (26): docs/spec/ artefacts structure, Spec-delta Merge into Living Specs (ADDED/MODIFIED/REMOVED), living-specs.md (copy in karvey-init), living-specs.md (copy in karvey-requirements), Spec-delta Generation, docs/spec/backlog.md (BL-NN), Deviation Request (design mode escalation), docs/spec/incidents-index.md global index (+18 more)

### Community 10 - "Causal Investigation"
Cohesion: 0.11
Nodes (22): karvey-investigate skill, Causal-coherence gate (cause vs latent fragility), Incident window (date the symptom), Iron Law: no fix without root-cause investigation, Stop after ~3 failed hypothesis cycles, Ask 'what CHANGED?' before 'what is WRONG?', karvey-iterate Skill, bug -> BUG-NN + impl/test/qa Micro-loop (+14 more)

### Community 11 - "Pipeline & Plugin-as-Code"
Cohesion: 0.19
Nodes (20): Pipeline 0-12 (13 phases), AG-06: Remove rule copies and make paths resolvable, AG-13: Plugin CI linter to catch drift before release, DM-12: Remove rule copies and give the plugin a light CI, PM-11: Pending decisions (Q-NN) and risks with owner and deadline, H-24: proposal.md is a phantom artifact, H-26: 9 duplicated rule copies, H-27: Plugin has no CI of its own (+12 more)

### Community 12 - "Early Release History"
Cohesion: 0.25
Nodes (16): CHANGELOG (Karvey), Release 3.0.0 (2026-06-14), Release 3.1.0 (2026-06-14), Release 3.2.0 (2026-06-17), Release 3.3.0 (2026-06-23), Release 3.4.0 (2026-06-23), Release 3.5.0 (2026-07-05), Release 3.6.0 (2026-09-08) (+8 more)

### Community 13 - "State Machine & Lanes"
Cohesion: 0.30
Nodes (16): AG-01: Deterministic state machine for spec.json (karvey-state.py), DM-01: Lanes by change size with recorded phase skips, DM-02: Single state machine with JSON schema and executable linter, PM-01: Single phase state machine with a validator that detects lies, H-01: Phase values written by skills do not match orchestrator table, H-02: karvey-impl never writes phase, H-03: Dead end for changes without UI (mockup->architecture), H-04: Hotfix lane collides with phase preconditions (+8 more)

### Community 14 - "Gates, Interruptions & Rule Drift"
Cohesion: 0.17
Nodes (15): Multilingual Page Design (EN/ES/PT/DE/ZH), team-adapters requirements (EARS), REQ-ADP-001 ask team settings on init when missing, REQ-ADP-002 do not re-ask settings unless --settings, REQ-ADP-003 session hook one-line reminder, silent outside Karvey, REQ-ADP-020 management tool enum, REQ-ADP-021 phase skills use logical states via management.statuses, REQ-ADP-022 missing status map -> read real statuses, propose, confirm once, persist (+7 more)

### Community 15 - "Change Lanes & Approvals"
Cohesion: 0.23
Nodes (14): F-44 Local rule copies with dangling sibling references, AG-08: Fewer interruptions: one AskUserQuestion per gate, batched grill, DM-06: Fewer, heavier human gates; remove silent auto-approval, PM-09: Scale ritual cost to work size (batching, small lane, attributed -y), PM-10: Unambiguous WBS: 'Feature' means two things, H-05: design-graphic self-approves, H-06: -y auto-approves without by/role/ref, R-10: Fewer, heavier human gates without auto-approval (+6 more)

### Community 16 - "Estimation & ClickUp Adapter"
Cohesion: 0.17
Nodes (13): Change types: feature, ops, hotfix, parent change, docs-only PR, approvals.prod {by,date,ref D-NN} human OK, Docs-only PR lane (light CI), Hotfix lane (fix + BUG-NN + regression test same PR), Multi-agent and Multi-repo rule, Business decisions D-NN, Documentation-only PR light CI, Agent environment readiness (+5 more)

### Community 17 - "Graphify & Ritual Overhead"
Cohesion: 0.18
Nodes (13): PM-02: Do not overwrite the estimate with actual time; store both and measure accuracy, H-16: time_estimate overwritten with actual time, R-05: Do not overwrite the estimate; keep estimate and actual, clickup-protocol.md (copy in karvey-init), create_epic in team's tracker, PLAN.md markdown fallback, ClickUp Protocol rule, AI-time estimation in minutes (10-30 min, cap ~60) (+5 more)

### Community 18 - "Panel Reports & Design System"
Cohesion: 0.36
Nodes (11): AG-05: Remove graphify from every phase close, DM-15: Lower per-task overhead (knowledge-sync, tracker ritual) and fix time logging, H-31: Graphify runs every phase and every mockup iteration, R-16: Graphify and tracker ritual off the hot path, karvey-mockup skill, Mockup navigation levels 1-4, Shotgun mode (N variants + comparison board), Spec<->mockup validation (Step 4C) (+3 more)

### Community 19 - "Notifications Requirements"
Cohesion: 0.22
Nodes (11): AG-12: Independent verification of self-judgments (clean-context judge, evidence log), Karvey 3.11.1 Review: Development-Methods Judge (DM), DM-13: Project-level design system; design-graphic as optional delta, Development-methods judge (DM), R-26: Project-level design system; design-graphic as delta, architecture.md, Karvey Design Graphic, Forbidden design anti-patterns (+3 more)

### Community 20 - "Security Tiers"
Cohesion: 0.31
Nodes (9): REQ-ADP-010 notification channel enum + target + via, REQ-ADP-011 skills notify via configured channel; none -> skip and say so, REQ-ADP-012 never read notification targets from CLAUDE.md tables, Step 8 deploy notification to team channel, .connections.json credentials (never committed), Notifications rule, Per-channel message markup, No webhook URLs or tokens in project.json (+1 more)

### Community 21 - "Licensing & Trademark"
Cohesion: 0.25
Nodes (8): Security Tiers (architecture rules), Security Tier Application by Layer, Security Anti-Patterns (forbidden), Tier 1 Public, Tier 2 Authenticated, Tier 3 Privileged, Tier 4 Critical, Trust Boundaries

### Community 22 - "README & Method Page"
Cohesion: 0.48
Nodes (7): Close external PRs workflow, Trademark Policy (skill copy), Trademark Policy (plugin copy), Trademark Policy — Karvey, Karvey = Afan (Ona/Selknam word), Karvey trademark (HainTech), Required attribution (Mauricio Quezada Ibanez / HainTech)

### Community 23 - "Logical States & Adapters"
Cohesion: 0.29
Nodes (6): REQ-ADP-030 ship self-contained docs/karvey.html linked from README, Plugin: karvey README, English skill bodies, artifacts in project language, bilingual triggers, Install / update via plugin marketplace (karvey@karvey-methods), Knowledge graph of the method (graphify-out/), Apache 2.0 license + Karvey trademark (HainTech)

### Community 24 - "team-adapters PRD"
Cohesion: 0.33
Nodes (6): Status cascade (Task -> Feature -> Epic), 5 logical states todo/in_progress/review/done/blocked, Logical tracker operations (create_epic, set_status, cascade, mirror_backlog...), project.json:notifications (channel/target/via/events), 4-action close ritual (comment, state, sweep, spec.json), docs/spec/project.json schema

### Community 25 - "Community 25"
Cohesion: 0.40
Nodes (5): PRD team-adapters, Acceptance criteria team-adapters, Problem: hard-coded Google Chat + ClickUp "listo! para pap", Constraint: Claude Code plugin has no install hook, North star: no skill assumes a tool the team does not use

## Ambiguous Edges - Review These
- `H-35: BUG-NN/D-NN/E{n} ID collision across parallel sessions` → `Karvey Decisions Log`  [AMBIGUOUS]
  docs/spec/reviews/2026-09-23-panel-review.md · relation: references
- `H-35: BUG-NN/D-NN/E{n} ID collision across parallel sessions` → `Incident Tracking rule`  [AMBIGUOUS]
  docs/spec/reviews/2026-09-23-panel-review.md · relation: references

## Knowledge Gaps
- **74 isolated node(s):** `karvey-statusline.sh script`, `TMPDIR`, `Close external PRs workflow`, `Karvey = Afan (Ona/Selknam word for zeal)`, `findings.md (single findings inbox)` (+69 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 147 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `H-35: BUG-NN/D-NN/E{n} ID collision across parallel sessions` and `Karvey Decisions Log`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `H-35: BUG-NN/D-NN/E{n} ID collision across parallel sessions` and `Incident Tracking rule`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `Karvey Method Page (docs/karvey.html)` connect `Method Page & Deploy Flow` to `Hotfix 3.11.2 & Incidents`, `Releases 3.9–3.11 & Changes`, `Team Layer (3.8)`, `Team-Layer Findings & Equivalences`, `Discovery Backlog`, `Panel: Hooks & Context Findings`, `EARS, Infra & Spec Rules`, `Living Specs & docs/spec`, `Pipeline & Plugin-as-Code`, `Early Release History`, `Gates, Interruptions & Rule Drift`, `Estimation & ClickUp Adapter`, `Graphify & Ritual Overhead`, `Panel Reports & Design System`, `Security Tiers`, `Logical States & Adapters`, `Community 25`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `karvey-deploy SKILL` connect `Releases 3.9–3.11 & Changes` to `Hotfix 3.11.2 & Incidents`, `Team Layer (3.8)`, `Team-Layer Findings & Equivalences`, `Discovery Backlog`, `Panel: Hooks & Context Findings`, `Method Page & Deploy Flow`, `Judges & Test-First (R-11, R-12)`, `Pipeline & Plugin-as-Code`, `Early Release History`, `State Machine & Lanes`, `Change Lanes & Approvals`, `Estimation & ClickUp Adapter`, `Graphify & Ritual Overhead`, `Panel Reports & Design System`, `Security Tiers`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `Discovery Backlog rule` connect `Discovery Backlog` to `Hotfix 3.11.2 & Incidents`, `Releases 3.9–3.11 & Changes`, `Team Layer (3.8)`, `Team-Layer Findings & Equivalences`, `Panel: Hooks & Context Findings`, `Method Page & Deploy Flow`, `EARS, Infra & Spec Rules`, `Living Specs & docs/spec`, `Causal Investigation`, `Early Release History`, `Graphify & Ritual Overhead`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `karvey-deploy SKILL` (e.g. with `REQ-ADP-011 skills notify via configured channel; none -> skip and say so` and `karvey orchestrator SKILL`) actually correct?**
  _`karvey-deploy SKILL` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 48 inferred relationships involving `Change team-adapters` (e.g. with `F-01 karvey-init --settings does not stop after Step 3.2` and `F-02 Session-hook settings nudge scope/parsing/hang`) actually correct?**
  _`Change team-adapters` has 48 INFERRED edges - model-reasoned connections that need verification._