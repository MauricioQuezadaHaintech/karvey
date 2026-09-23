# Graph Report - karvey  (2026-09-23)

## Corpus Check
- 88 files · ~115,479 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 7)

## Summary
- 467 nodes · 1059 edges · 14 communities
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 147 edges (avg confidence: 0.89)
- Token cost: 1,183,362 input · 0 output

## Community Hubs (Navigation)
- Runtime Evidence & Iteration
- Deploy, Canary & Notifications
- Handoff, Team Layer & Decisions
- Team Settings, Releases & Method Page
- Plugin Map & Guardrails
- Multi-Agent Inputs & Findings
- Release History
- Archive & Backlog Sweep
- Security Tiers
- Imports, EARS & Specs
- Session Hooks & Scripts
- Change Lanes & Approvals
- Infra & CI/CD
- Discovery Backlog

## God Nodes (most connected - your core abstractions)
1. `Plugin org chart (32 skills, 22 rules, hooks, artefacts)` - 57 edges
2. `karvey-deploy SKILL` - 39 edges
3. `Multi-agent and Multi-repo rule` - 35 edges
4. `Skills catalog (32 = 1 orchestrator + 13 phases + 18 support)` - 34 edges
5. `karvey-init Skill` - 34 edges
6. `Management Adapters rule` - 32 edges
7. `karvey-iterate Skill` - 31 edges
8. `karvey-qa Skill` - 29 edges
9. `docs/karvey.html (method explainer page)` - 26 edges
10. `Deployment Flow rule` - 25 edges

## Surprising Connections (you probably didn't know these)
- `Measured, not remembered` --semantically_similar_to--> `Verification rules before reporting "done"`  [INFERRED] [semantically similar]
  docs/karvey.html → README.md
- `Causal discipline (date the symptom; what changed before what is wrong; causal-coherence gate)` --semantically_similar_to--> `Verification rules before reporting "done"`  [INFERRED] [semantically similar]
  CHANGELOG.md → README.md
- `PR gates verification before prod OK` --semantically_similar_to--> `Blocking security gate (OWASP + STRIDE)`  [INFERRED] [semantically similar]
  CHANGELOG.md → README.md
- `Approval gates (--autoplan batches, never skips)` --conceptually_related_to--> `13-phase pipeline (0-12) with approval gates`  [INFERRED]
  docs/karvey.html → README.md
- `Constraint: Claude Code plugin has no install hook` --rationale_for--> `Team settings asked on first use`  [INFERRED]
  docs/spec/changes/team-adapters/prd.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Karvey pipeline 0-12 phase skills** — plugins_karvey_skills_karvey_grill_skill, plugins_karvey_skills_karvey_init_skill, plugins_karvey_skills_karvey_requirements_skill, plugins_karvey_skills_karvey_mockup_skill, plugins_karvey_skills_karvey_design_graphic_skill, plugins_karvey_skills_karvey_architecture_skill, plugins_karvey_skills_karvey_infra_skill, plugins_karvey_skills_karvey_tasks_skill, plugins_karvey_skills_karvey_impl_skill, plugins_karvey_skills_karvey_test_skill, plugins_karvey_skills_karvey_qa_skill, plugins_karvey_skills_karvey_deploy_skill, plugins_karvey_skills_karvey_archive_skill [EXTRACTED 1.00]
- **Iteration loop: findings routed by karvey-iterate to three edges** — readme_findings_md, plugins_karvey_skills_karvey_iterate_skill, readme_bug_edge, readme_spec_gap_edge, readme_emergent_edge, readme_convergence_gate, plugins_karvey_skills_karvey_test_skill, plugins_karvey_skills_karvey_qa_skill, plugins_karvey_skills_karvey_browse_skill [EXTRACTED 1.00]
- **Team settings on first use (team-adapters)** — readme_team_settings_first_use, readme_notification_channels, readme_management_tools, readme_five_logical_states, readme_project_json, plugins_karvey_skills_karvey_rules_notifications, plugins_karvey_skills_karvey_rules_management_adapters, plugins_karvey_skills_karvey_init_skill [EXTRACTED 1.00]
- **Karvey trademark policy and its copies** — trademark, plugins_karvey_trademark, plugins_karvey_skills_karvey_trademark, trademark_karvey_trademark, _github_workflows_close_external_prs [INFERRED 0.85]
- **team-adapters change: settings on first use for notifications + management** — docs_spec_changes_team_adapters_prd, docs_spec_changes_team_adapters_requirements, docs_spec_backlog_bl_02, docs_spec_backlog_bl_03, plugins_karvey_skills_karvey_rules_notifications, plugins_karvey_skills_karvey_rules_management_adapters, readme_team_settings_first_use [EXTRACTED 1.00]
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

## Communities (14 total, 0 thin omitted)

### Community 0 - "Runtime Evidence & Iteration"
Cohesion: 0.05
Nodes (65): [human] tasks and awaiting-human state, Karvey Browse, findings.md (bug/spec-gap/emergent), Session cookie import for authenticated views, karvey-impl Skill, DB->Backend->Frontend Execution Order, Deviation Request (deviations.md), [human] Tasks and awaiting-human State (+57 more)

### Community 1 - "Deploy, Canary & Notifications"
Cohesion: 0.05
Nodes (52): Post-deploy canary (dev and prod), 6-step deploy checklist, REQ-ADP-010 notification channel enum + target + via, REQ-ADP-011 skills notify via configured channel; none -> skip and say so, REQ-ADP-012 never read notification targets from CLAUDE.md tables, karvey-deploy SKILL, Step 2.12 branch hygiene, Step 2-bis post-deploy canary loop (zero downtime) (+44 more)

### Community 2 - "Handoff, Team Layer & Decisions"
Cohesion: 0.07
Nodes (48): Agent handoff (produced, not composed) + state.json, Context cost: at 588k a turn costs 7x what it costs at 80k, Decision log (D-NN business / C-NN direction) with cross check, Release 3.8.0 - agent handoff, optional team layer, verification rules, SessionStart hook, Measured, not remembered, Honest team cost warning (when not to use a team), F-03 team cost collection unproven, PRD — Optional team layer (+40 more)

### Community 3 - "Team Settings, Releases & Method Page"
Cohesion: 0.08
Nodes (45): Logical tracker operations (create_epic, set_status, cascade, ...), Release 3.10.0 - team settings on first use (team-adapters), Release 3.11.0 - visible version by environment + multilingual method page, Release 3.11.1 - karvey.html picks browser language, per-language tab title, docs/karvey.html (method explainer page), Approval gates (--autoplan batches, never skips), Artefacts map (docs/spec/ structure), Finding types litmus tests (bug / spec-gap / emergent) (+37 more)

### Community 4 - "Plugin Map & Guardrails"
Cohesion: 0.08
Nodes (39): Plugin org chart (32 skills, 22 rules, hooks, artefacts), A skill is guidance; a hook actually blocks, Karvey Guard, Freeze edit-lock, Plan-gate override (approval marker), block(), git-flow-guard.sh script, block() (+31 more)

### Community 5 - "Multi-Agent Inputs & Findings"
Cohesion: 0.07
Nodes (37): Pinned inputs (repo path @commit) from design/copy/legal agents, Findings — team-layer, F-01 health checks team-layer readiness, F-02 auditor audits whoever directs, F-04 plugin cannot declare statusline, Karvey Benchmark Models, LLM-Judge quality scoring, state.json (handoff machine-readable twin) (+29 more)

### Community 6 - "Release History"
Cohesion: 0.08
Nodes (33): AI-time estimation in minutes (10-30, cap ~60), approvals.prod = {by, date, ref: D-NN} recorded in git, Causal discipline (date the symptom; what changed before what is wrong; causal-coherence gate), Visual components catalog (design-components.md), Deviation Request + deviations.md, Documentation-only PR lane (light CI), Engineering standards layer (golden paths, third source of truth), Git host detection (gh pr / az repos pr / glab mr) (+25 more)

### Community 7 - "Archive & Backlog Sweep"
Cohesion: 0.09
Nodes (30): karvey-archive Skill, Discovery Backlog Sweep, Branch Sweep at Archive, Change Directory Archival, IMPLEMENTED Production Marker, Spec-delta Merge into Living Specs (ADDED/MODIFIED/REMOVED), Karvey Grill (Pre-Spec Interrogation), Interrogation tree (branches A-F) (+22 more)

### Community 8 - "Security Tiers"
Cohesion: 0.09
Nodes (26): Security Tiers (architecture rules), Security Tier Application by Layer, Security Anti-Patterns (forbidden), Tier 1 Public, Tier 2 Authenticated, Tier 3 Privileged, Tier 4 Critical, Karvey Architecture (Phase 5) (+18 more)

### Community 9 - "Imports, EARS & Specs"
Cohesion: 0.11
Nodes (23): Kiro/gstack -> Karvey equivalents table, EARS Format (init copy), EARS patterns (Ubiquitous/Event/State/Conditional/Optional), Litmus test: requirements vs design (technology-free), PRD Template (prd.md), EARS Format (requirements copy), EARS Requirements Traced to PRD, EARS Format rule (+15 more)

### Community 10 - "Session Hooks & Scripts"
Cohesion: 0.14
Nodes (18): Close external PRs workflow, emit(), settings_nudge(), karvey-session-context.sh script, karvey-statusline.sh script, Karvey hooks README, State drift measurement (matches / DRIFT vs state.json), Things learned the hard way (stdin format, WSL paths, emoji codepage) (+10 more)

### Community 11 - "Change Lanes & Approvals"
Cohesion: 0.11
Nodes (19): approvals.prod {by,date,ref D-NN} human OK, Docs-only PR lane (light CI), Hotfix lane (fix + BUG-NN + regression test same PR), RESUELTO requires regression test, iteration_count + revision_history (append-only), spec.json change metadata schema, Multi-agent and Multi-repo rule, Approvals with decision reference (prod never delegated) (+11 more)

### Community 12 - "Infra & CI/CD"
Cohesion: 0.14
Nodes (16): karvey-infra Skill, CI/CD Pipeline Generation, Deploy Platform One-time Configuration, IaC Generation (terraform/bicep/pulumi), Idempotent Infra Discovery, Infra Security Review Gate, Ops Command Plan + Versioned IAM Scripts, Security Tiers (init copy) (+8 more)

### Community 13 - "Discovery Backlog"
Cohesion: 0.28
Nodes (9): Discovery Backlog — Karvey Method, BL-01 Run graphify over the repo (done), BL-02 Notifications configurable per team, BL-03 Task-management tool + status flow configurable, PRD team-adapters, Acceptance criteria team-adapters, Problem: hard-coded Google Chat + ClickUp "listo! para pap", Constraint: Claude Code plugin has no install hook (+1 more)

## Knowledge Gaps
- **68 isolated node(s):** `karvey-statusline.sh script`, `Close external PRs workflow`, `Mauricio Quezada Ibanez / HainTech (author)`, `Multi-agent & multi-repo work`, `Karvey = Afan (Ona/Selknam word)` (+63 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 139 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Plugin org chart (32 skills, 22 rules, hooks, artefacts)` connect `Plugin Map & Guardrails` to `Runtime Evidence & Iteration`, `Deploy, Canary & Notifications`, `Handoff, Team Layer & Decisions`, `Team Settings, Releases & Method Page`, `Multi-Agent Inputs & Findings`, `Archive & Backlog Sweep`, `Security Tiers`, `Imports, EARS & Specs`, `Change Lanes & Approvals`, `Infra & CI/CD`?**
  _High betweenness centrality (0.295) - this node is a cross-community bridge._
- **Why does `Multi-agent and Multi-repo rule` connect `Change Lanes & Approvals` to `Runtime Evidence & Iteration`, `Deploy, Canary & Notifications`, `Handoff, Team Layer & Decisions`, `Plugin Map & Guardrails`, `Multi-Agent Inputs & Findings`, `Release History`, `Archive & Backlog Sweep`, `Security Tiers`, `Imports, EARS & Specs`, `Infra & CI/CD`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `karvey-deploy SKILL` connect `Deploy, Canary & Notifications` to `Runtime Evidence & Iteration`, `Team Settings, Releases & Method Page`, `Plugin Map & Guardrails`, `Multi-Agent Inputs & Findings`, `Release History`, `Archive & Backlog Sweep`, `Imports, EARS & Specs`, `Change Lanes & Approvals`, `Infra & CI/CD`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `karvey-deploy SKILL` (e.g. with `REQ-ADP-011 skills notify via configured channel; none -> skip and say so` and `karvey orchestrator SKILL`) actually correct?**
  _`karvey-deploy SKILL` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `karvey-statusline.sh script`, `Close external PRs workflow`, `Mauricio Quezada Ibanez / HainTech (author)` to the rest of the system?**
  _68 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Runtime Evidence & Iteration` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Deploy, Canary & Notifications` be split into smaller, more focused modules?**
  _Cohesion score 0.054426705370101594 - nodes in this community are weakly interconnected._