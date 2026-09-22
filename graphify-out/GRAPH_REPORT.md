# Graph Report - karvey  (2026-09-22)

## Corpus Check
- 88 files · ~115,258 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 7)

## Summary
- 472 nodes · 1026 edges · 18 communities
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 125 edges (avg confidence: 0.9)
- Token cost: 1,071,986 input · 0 output

## Community Hubs (Navigation)
- Hooks & docs/spec Artifacts
- Iteration Loop, Living Specs & Rules
- Team Settings & Adapters (3.10)
- Handoff, Team Layer & Statusline
- Deploy, Versions & Branch Hygiene
- Release History
- Multi-Agent Changes & Pipeline
- Security Tiers
- Identity, License & Method Core
- Session Hooks & Scripts
- Support Skills & Equivalences
- Infra & CI/CD
- Team-Layer Findings & Health
- Runtime Evidence & Testing
- QA Review & Standards Gate
- Git-Flow Guard & Branch Flow
- Causal Investigation
- Iteration Engine

## God Nodes (most connected - your core abstractions)
1. `karvey-deploy SKILL` - 42 edges
2. `Multi-agent and Multi-repo rule` - 38 edges
3. `karvey-init Skill` - 34 edges
4. `Management Adapters rule` - 33 edges
5. `Deployment Flow rule` - 32 edges
6. `karvey-iterate Skill` - 29 edges
7. `karvey-qa Skill` - 29 edges
8. `Kiro/gstack to Karvey equivalents table` - 25 edges
9. `karvey-test Skill` - 24 edges
10. `ClickUp Protocol rule` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Convergence gate (no open bug/spec-gap, emergent captured)` --semantically_similar_to--> `Iteration loop (spiral, not a line)`  [INFERRED] [semantically similar]
  plugins/karvey/skills/karvey/SKILL.md → README.md
- `REQ-ADP-021 logical states via management.statuses` --semantically_similar_to--> `5 logical states (todo/in_progress/review/done/blocked)`  [INFERRED] [semantically similar]
  docs/spec/changes/team-adapters/requirements.md → README.md
- `Trademark Policy (skill copy)` --semantically_similar_to--> `Trademark Policy — Karvey`  [INFERRED] [semantically similar]
  plugins/karvey/skills/karvey/TRADEMARK.md → TRADEMARK.md
- `Trademark Policy (plugin copy)` --semantically_similar_to--> `Trademark Policy — Karvey`  [INFERRED] [semantically similar]
  plugins/karvey/TRADEMARK.md → TRADEMARK.md
- `BUG-NN tracker (docs/bugs_dev_testing.md)` --references--> `Incident Tracking rule`  [INFERRED]
  docs/karvey.html → plugins/karvey/skills/karvey/rules/incident-tracking.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Karvey trademark policy and its copies** — trademark, plugins_karvey_trademark, plugins_karvey_skills_karvey_trademark, trademark_karvey_trademark, _github_workflows_close_external_prs [INFERRED 0.85]
- **Karvey iteration loop: findings routed along three edges** — docs_karvey_findings_md, plugins_karvey_skills_karvey_iterate_skill, docs_karvey_finding_bug, docs_karvey_finding_spec_gap, docs_karvey_finding_emergent, docs_karvey_bug_nn_tracker, docs_karvey_spec_revision_subcycle, docs_karvey_discovery_backlog [EXTRACTED 1.00]
- **Karvey enforcement hooks managed by karvey-guard** — docs_karvey_git_flow_guard, docs_karvey_plan_gate, docs_karvey_standards_guard, docs_karvey_clickup_sync_guard, docs_karvey_freeze_edit_lock, plugins_karvey_skills_karvey_guard_skill, plugins_karvey_skills_karvey_rules_enforcement [EXTRACTED 1.00]
- **Karvey ordered deployment flow** — docs_karvey_pipeline_triggered_deploy, docs_karvey_six_step_checklist, docs_karvey_pr_gates, docs_karvey_post_deploy_canary, docs_karvey_branch_hygiene, docs_karvey_visible_version_by_environment, plugins_karvey_skills_karvey_deploy_skill [EXTRACTED 1.00]
- **team-adapters change: settings on first use for notifications + management** — docs_spec_changes_team_adapters_prd, docs_spec_changes_team_adapters_requirements, docs_spec_backlog_bl_02, docs_spec_backlog_bl_03, plugins_karvey_skills_karvey_rules_notifications, plugins_karvey_skills_karvey_rules_management_adapters, readme_team_settings_first_use [EXTRACTED 1.00]
- **Team settings on first use: requirements, README section, release 3.10.0** — docs_spec_changes_team_adapters_requirements_team_adapters_change, readme_team_settings_first_use, readme_logical_states, docs_spec_changes_team_adapters_requirements_req_adp_021, docs_spec_changes_team_adapters_requirements_req_adp_011, changelog_release_3_10_0 [INFERRED 0.85]
- **Team-layer change (PRD, requirements, findings, skills, rules, hooks)** — docs_spec_changes_team_layer_prd, docs_spec_changes_team_layer_requirements, docs_spec_changes_team_layer_findings, plugins_karvey_skills_karvey_team_skill, plugins_karvey_skills_karvey_decisions_skill, plugins_karvey_skills_karvey_rules_team, plugins_karvey_skills_karvey_rules_verification [EXTRACTED 1.00]
- **Gates before production merge** — plugins_karvey_skills_karvey_deploy_skill_release_gate_step0, plugins_karvey_skills_karvey_deploy_skill_pr_gates_verification, plugins_karvey_skills_karvey_deploy_skill_approvals_prod, plugins_karvey_skills_karvey_deploy_skill_six_step_checklist, plugins_karvey_skills_karvey_deploy_skill_canary_loop [EXTRACTED 1.00]
- **Cross-cutting support skills that never modify spec.json:phase** — plugins_karvey_skills_karvey_benchmark_models_skill, plugins_karvey_skills_karvey_browse_skill, plugins_karvey_skills_karvey_checkpoint_skill, plugins_karvey_skills_karvey_context_skill, plugins_karvey_skills_karvey_decisions_skill, plugins_karvey_skills_karvey_devex_skill, plugins_karvey_skills_karvey_diagram_skill, plugins_karvey_skills_karvey_docs_skill, plugins_karvey_skills_karvey_guard_skill, plugins_karvey_skills_karvey_health_skill, plugins_karvey_skills_karvey_import_skill [EXTRACTED 1.00]
- **Findings Feedback Loop (observe/classify -> route)** — plugins_karvey_skills_karvey_test_skill_findings_classification, plugins_karvey_skills_karvey_qa_skill_nine_dimension_review, plugins_karvey_skills_karvey_iterate_skill_iteration_engine_router, plugins_karvey_skills_karvey_iterate_skill_bug_route_micro_loop, plugins_karvey_skills_karvey_iterate_skill_spec_revision_ripple_set, plugins_karvey_skills_karvey_iterate_skill_emergent_backlog_route, plugins_karvey_skills_karvey_skill_convergence_gate [EXTRACTED 1.00]
- **Cross-cutting support skills that never advance spec.json:phase** — plugins_karvey_skills_karvey_investigate_skill, plugins_karvey_skills_karvey_iterate_skill, plugins_karvey_skills_karvey_retro_skill, plugins_karvey_skills_karvey_scrape_skill, plugins_karvey_skills_karvey_second_opinion_skill, plugins_karvey_skills_karvey_standards_skill, plugins_karvey_skills_karvey_team_skill [EXTRACTED 1.00]
- **Human-in-the-loop Controls** — plugins_karvey_skills_karvey_impl_skill_human_tasks_awaiting_human, plugins_karvey_skills_karvey_tasks_skill_human_task_format, plugins_karvey_skills_karvey_infra_skill_ops_command_plan, plugins_karvey_skills_karvey_test_skill_infrastructure_tests [INFERRED 0.85]
- **Production safety gates** — plugins_karvey_skills_karvey_rules_deploy_workflow_pipeline_only_deploy, plugins_karvey_skills_karvey_rules_deploy_workflow_pr_gates_before_ok, plugins_karvey_skills_karvey_rules_multi_agent_approvals_with_ref, plugins_karvey_skills_karvey_rules_multi_agent_hotfix_lane, plugins_karvey_skills_karvey_rules_deploy_workflow_zero_downtime [INFERRED 0.85]
- **Opt-in enforcement hooks (git-flow, plan-gate, standards-guard, clickup-sync-guard)** — plugins_karvey_skills_karvey_rules_enforcement_git_flow_guard, plugins_karvey_skills_karvey_rules_enforcement_plan_gate, plugins_karvey_skills_karvey_rules_engineering_standards_standards_guard, plugins_karvey_skills_karvey_rules_phase_close_clickup_sync_guard [EXTRACTED 1.00]
- **Finding routing: findings.md to BUG-NN, spec-revision, backlog** — plugins_karvey_skills_karvey_rules_iteration_loop_findings_md, plugins_karvey_skills_karvey_rules_iteration_loop_spec_revision_subcycle, plugins_karvey_skills_karvey_rules_backlog_backlog_md [EXTRACTED 1.00]
- **Nothing-lost feedback artifacts (findings, BUG-NN, backlog, revision history)** — plugins_karvey_skills_karvey_rules_backlog_backlog_md, plugins_karvey_skills_karvey_rules_incident_tracking_bug_nn_tracker, plugins_karvey_skills_karvey_rules_incident_tracking_incidents_index, plugins_karvey_skills_karvey_rules_living_specs_revision_history, plugins_karvey_skills_karvey_rules_phase_close_four_action_ritual [INFERRED 0.85]
- **Team settings stored in project.json** — plugins_karvey_skills_karvey_rules_project_config_project_json_schema, plugins_karvey_skills_karvey_rules_notifications_notification_settings, plugins_karvey_skills_karvey_rules_management_adapters_five_logical_states, plugins_karvey_skills_karvey_rules_project_config_branch_flow, plugins_karvey_skills_karvey_rules_project_config_standards_source [INFERRED 0.85]
- **Visible version by environment (rule, deploy step, canary check, release)** — plugins_karvey_skills_karvey_rules_versioning_visible_version_by_env, plugins_karvey_skills_karvey_deploy_skill_step_2_4_bis_visible_version, plugins_karvey_skills_karvey_deploy_skill_canary_loop, changelog_release_3_11_0, plugins_karvey_skills_karvey_rules_versioning_version_file_source [EXTRACTED 1.00]

## Communities (18 total, 0 thin omitted)

### Community 0 - "Hooks & docs/spec Artifacts"
Cohesion: 0.05
Nodes (59): clickup-sync-guard (described in rule), docs/spec/ artefact structure, --freeze edit-lock, git-flow-guard hook, Hooks: active on install vs opt-in, Living specs specs/{capability}/spec.md, notifications.channel (google-chat/slack/teams/email/webhook/none), Pipeline-triggered deploy (feature -> dev -> PR -> master) (+51 more)

### Community 1 - "Iteration Loop, Living Specs & Rules"
Cohesion: 0.06
Nodes (58): Release 3.2.0 iteration loop, Release 3.3.0 engineering standards layer, Nothing left hanging principle, Shared rules catalogue (22 rules), Discovery Backlog Sweep, Spec-delta Merge into Living Specs (ADDED/MODIFIED/REMOVED), living-specs.md (copy in karvey-init), emergent -> Discovery Backlog BL-NN (+50 more)

### Community 2 - "Team Settings & Adapters (3.10)"
Cohesion: 0.06
Nodes (56): Plugin hard-coded HainTech tooling (Google Chat via CLAUDE.md, ClickUp statuses), Release 3.10.0 team settings on first use (team-adapters), Five logical states (todo/in_progress/review/done/blocked), management.tool (clickup/jira/linear/azure-boards/github-projects/spreadsheet/markdown/other), Discovery Backlog — Karvey Method, BL-01 Run graphify over the repo (done), BL-02 Notifications configurable per team, BL-03 Task-management tool + status flow configurable (+48 more)

### Community 3 - "Handoff, Team Layer & Statusline"
Cohesion: 0.07
Nodes (40): Agent handoff (docs/spec/agent: handoff.md, state.json, board.md), Agent-team layer (optional), Context rotation threshold (150k / 24h), Decision log D-NN / C-NN, Statusline karvey-statusline.sh, Measured team cost warning, F-03 team cost collection unproven, PRD — Optional team layer (+32 more)

### Community 4 - "Deploy, Versions & Branch Hygiene"
Cohesion: 0.09
Nodes (38): Release 3.11.0 visible version by env + multilingual karvey.html, Release 3.9.0 branch hygiene + standards conformance + PR gates, Stuck pipeline variable showed old version in prod front, approvals.prod {by, date, ref}, Branch hygiene, Post-deploy canary, PR gates and human OK, 6-step pre-deploy checklist (+30 more)

### Community 5 - "Release History"
Cohesion: 0.08
Nodes (33): Release 3.0.0 initial publication, Release 3.1.0 karvey-import, Release 3.4.0 AI-time estimation, Release 3.5.0 visual components catalog, Release 3.6.0 causal discipline in investigate, Release 3.8.0 agent handoff + optional team layer, Release 3.9.1 documentation drift fix, Stale local copies of shared rules (+25 more)

### Community 6 - "Multi-Agent Changes & Pipeline"
Cohesion: 0.09
Nodes (31): Release 3.7.0 multi-agent / multi-repo, hotfix change type, ops change type, Documentation-only PR, Parent change (links.children), Pipeline 0–12 (13 phases), approvals.prod {by,date,ref D-NN} human OK, Docs-only PR lane (light CI) (+23 more)

### Community 7 - "Security Tiers"
Cohesion: 0.10
Nodes (24): Security Tiers (architecture rules), Security Tier Application by Layer, Security Anti-Patterns (forbidden), Tier 1 Public, Tier 2 Authenticated, Tier 3 Privileged, Tier 4 Critical, Karvey Architecture (Phase 5) (+16 more)

### Community 8 - "Identity, License & Method Core"
Cohesion: 0.12
Nodes (22): Afán — Ona (Selknam) word meaning zeal, Apache-2.0 licence and karvey-* trademark, Mauricio Quezada Ibáñez (author, HainTech), --autoplan mode, BUG-NN tracker (docs/bugs_dev_testing.md), Convergence rule, Discovery backlog (docs/spec/backlog.md), Finding type: bug (+14 more)

### Community 9 - "Session Hooks & Scripts"
Cohesion: 0.14
Nodes (18): Close external PRs workflow, emit(), settings_nudge(), karvey-session-context.sh script, karvey-statusline.sh script, Karvey hooks README, State drift measurement (matches / DRIFT vs state.json), Things learned the hard way (stdin format, WSL paths, emoji codepage) (+10 more)

### Community 10 - "Support Skills & Equivalences"
Cohesion: 0.15
Nodes (17): Kiro/gstack to Karvey equivalents table, Kiro (cc-sdd) and gstack (Garry Tan) inspiration, Support layer (18 skills), Karvey Benchmark Models, LLM-Judge quality scoring, Karvey DevEx Reviewer, Docs lies, Three lenses: Expansion / Polish / Triage (+9 more)

### Community 11 - "Infra & CI/CD"
Cohesion: 0.14
Nodes (16): karvey-infra Skill, CI/CD Pipeline Generation, Deploy Platform One-time Configuration, IaC Generation (terraform/bicep/pulumi), Idempotent Infra Discovery, Infra Security Review Gate, Ops Command Plan + Versioned IAM Scripts, Security Tiers (init copy) (+8 more)

### Community 12 - "Team-Layer Findings & Health"
Cohesion: 0.18
Nodes (13): Findings — team-layer, F-01 health checks team-layer readiness, F-02 auditor audits whoever directs, F-04 plugin cannot declare statusline, state.json (handoff machine-readable twin), Design scoring 0-10 by dimension, Karvey Health Dashboard, health-history.jsonl (+5 more)

### Community 13 - "Runtime Evidence & Testing"
Cohesion: 0.22
Nodes (11): Karvey Browse, findings.md (bug/spec-gap/emergent), Session cookie import for authenticated views, Dimension 8 Visual Audit vs design-spec, Stack Agnosticism (Targets) rule, targets field (stack agnosticism), karvey-test Skill, E2E in Target's Real Runtime (+3 more)

### Community 14 - "QA Review & Standards Gate"
Cohesion: 0.22
Nodes (10): Deviation Request (deviations.md), karvey-qa Skill, 9-dimension QA Review, QA Team Notification, REVISION_PR Review Document, Dimension 7 Cross-model Second Opinion, Dimension 9 Standards Conformance, karvey-second-opinion skill (+2 more)

### Community 15 - "Git-Flow Guard & Branch Flow"
Cohesion: 0.33
Nodes (6): block(), git-flow-guard.sh script, Branch hygiene (delete only absorbed branches), git-flow-guard hook, standards-guard hook, branch_flow (feature/ -> dev -> master, protected_branches)

### Community 16 - "Causal Investigation"
Cohesion: 0.43
Nodes (7): karvey-investigate skill, Causal-coherence gate (cause vs latent fragility), Incident window (date the symptom), Iron Law: no fix without root-cause investigation, Stop after ~3 failed hypothesis cycles, Ask 'what CHANGED?' before 'what is WRONG?', bug -> BUG-NN + impl/test/qa Micro-loop

### Community 17 - "Iteration Engine"
Cohesion: 0.29
Nodes (7): karvey-iterate Skill, Hotfix Lane (fix + BUG-NN + regression test same PR), Input Drift Ripple Candidate, Iteration Engine - Single Router, Finding Litmus Test (bug/spec-gap/emergent), spec-gap -> Spec-revision Sub-cycle with Ripple Set, Findings Classification into findings.md

## Knowledge Gaps
- **77 isolated node(s):** `karvey-statusline.sh script`, `Close external PRs workflow`, `Release 3.6.0 causal discipline in investigate`, `Release 3.5.0 visual components catalog`, `Release 3.1.0 karvey-import` (+72 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 145 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `karvey-deploy SKILL` connect `Deploy, Versions & Branch Hygiene` to `Hooks & docs/spec Artifacts`, `Iteration Loop, Living Specs & Rules`, `Team Settings & Adapters (3.10)`, `Release History`, `Multi-Agent Changes & Pipeline`, `Support Skills & Equivalences`, `Infra & CI/CD`, `Runtime Evidence & Testing`, `QA Review & Standards Gate`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `Multi-agent and Multi-repo rule` connect `Multi-Agent Changes & Pipeline` to `Hooks & docs/spec Artifacts`, `Iteration Loop, Living Specs & Rules`, `Handoff, Team Layer & Statusline`, `Deploy, Versions & Branch Hygiene`, `Release History`, `Security Tiers`, `Infra & CI/CD`, `Team-Layer Findings & Health`, `Runtime Evidence & Testing`, `Iteration Engine`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Why does `Management Adapters rule` connect `Team Settings & Adapters (3.10)` to `Hooks & docs/spec Artifacts`, `Iteration Loop, Living Specs & Rules`, `Deploy, Versions & Branch Hygiene`, `Multi-Agent Changes & Pipeline`, `Infra & CI/CD`, `Runtime Evidence & Testing`, `QA Review & Standards Gate`, `Iteration Engine`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `karvey-deploy SKILL` (e.g. with `karvey orchestrator SKILL` and `README.md (Karvey)`) actually correct?**
  _`karvey-deploy SKILL` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `Multi-agent and Multi-repo rule` (e.g. with `hotfix change type` and `ops change type`) actually correct?**
  _`Multi-agent and Multi-repo rule` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Management Adapters rule` (e.g. with `REQ-ADP-020 management tool enum` and `REQ-ADP-021 logical states via management.statuses`) actually correct?**
  _`Management Adapters rule` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Deployment Flow rule` (e.g. with `Branch hygiene` and `git-flow-guard hook`) actually correct?**
  _`Deployment Flow rule` has 8 INFERRED edges - model-reasoned connections that need verification._