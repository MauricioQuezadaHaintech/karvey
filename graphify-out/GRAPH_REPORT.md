# Graph Report - karvey  (2026-09-22)

## Corpus Check
- 88 files · ~90,798 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 7)

## Summary
- 446 nodes · 968 edges · 22 communities
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 96 edges (avg confidence: 0.89)
- Token cost: 878,335 input · 0 output

## Community Hubs (Navigation)
- Team Layer & Support Map
- Pipeline Phases & Architecture
- Iteration Loop & Incidents
- Deploy, Branches & Rules Map
- Method Principles & Governance
- Import, EARS & Spec Templates
- Release History
- Opt-in Enforcement Hooks
- Team-Adapters Requirements
- Runtime Evidence & Testing
- QA Review & Standards Gate
- Multi-Agent Findings & Health
- Impl Cycle & Phase Close
- Release 3.10 & Backlog
- docs/spec Artifacts Map
- Hooks Map (active vs opt-in)
- ClickUp Adapter & Estimation
- Logical States & Adapters
- Multi-Agent Multi-Repo Rule
- Security Tiers
- Method Explainer Page
- Project Configuration

## God Nodes (most connected - your core abstractions)
1. `Karvey Orchestrator Skill` - 41 edges
2. `karvey-deploy Skill` - 37 edges
3. `karvey-init Skill` - 35 edges
4. `karvey-iterate Skill` - 35 edges
5. `Management Adapters rule` - 33 edges
6. `Multi-agent and Multi-repo rule` - 30 edges
7. `karvey-qa Skill` - 28 edges
8. `karvey-test Skill` - 24 edges
9. `Deployment Flow rule` - 24 edges
10. `Org chart branch c: 22 shared rules` - 23 edges

## Surprising Connections (you probably didn't know these)
- `SessionStart hook · karvey-session-context.sh` --semantically_similar_to--> `SessionStart hook (hooks.json + karvey-session-context.sh)`  [INFERRED] [semantically similar]
  docs/karvey.html → plugins/karvey/hooks/README.md
- `Historial de versiones (3.0.0 → 3.10.0)` --references--> `CHANGELOG`  [INFERRED]
  docs/karvey.html → CHANGELOG.md
- `El bucle de iteración (bug / spec-gap / emergent)` --semantically_similar_to--> `Iteration loop — a spiral, not a line`  [INFERRED] [semantically similar]
  docs/karvey.html → README.md
- `Team settings 6-step first-use flow (session → init 3.2 → notifications → management → states → project.json)` --semantically_similar_to--> `Team settings asked on first use`  [INFERRED] [semantically similar]
  docs/karvey.html → README.md
- `5 estados lógicos` --semantically_similar_to--> `5 logical states (todo · in_progress · review · done · blocked)`  [INFERRED] [semantically similar]
  docs/karvey.html → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Karvey trademark policy and its copies** — trademark, plugins_karvey_trademark, plugins_karvey_skills_karvey_trademark, trademark_karvey_trademark, _github_workflows_close_external_prs [INFERRED 0.85]
- **Iteration spiral: findings routed to bug / spec-gap / emergent** — readme_iteration_loop_spiral, docs_karvey_iteration_loop_diagram, plugins_karvey_skills_karvey_iterate_skill, plugins_karvey_skills_karvey_rules_iteration_loop, plugins_karvey_skills_karvey_rules_incident_tracking, plugins_karvey_skills_karvey_rules_backlog, docs_karvey_findings_md [EXTRACTED 1.00]
- **Ordered deploy flow: checklist, PR gates, human OK, canary, branch hygiene** — docs_karvey_deploy_and_branches, docs_karvey_six_step_checklist, docs_karvey_pr_gates_human_ok, docs_karvey_canary_post_deploy, docs_karvey_branch_hygiene, plugins_karvey_skills_karvey_deploy_skill, plugins_karvey_skills_karvey_rules_deploy_workflow [EXTRACTED 1.00]
- **team-adapters change: settings on first use for notifications + management** — docs_spec_changes_team_adapters_prd, docs_spec_changes_team_adapters_requirements, docs_spec_backlog_bl_02, docs_spec_backlog_bl_03, plugins_karvey_skills_karvey_rules_notifications, plugins_karvey_skills_karvey_rules_management_adapters, readme_team_settings_first_use, changelog_v3_10_0 [EXTRACTED 1.00]
- **Team-layer change (PRD, requirements, findings, skills, rules, hooks)** — docs_spec_changes_team_layer_prd, docs_spec_changes_team_layer_requirements, docs_spec_changes_team_layer_findings, plugins_karvey_skills_karvey_team_skill, plugins_karvey_skills_karvey_decisions_skill, plugins_karvey_skills_karvey_rules_team, plugins_karvey_skills_karvey_rules_verification [EXTRACTED 1.00]
- **Release-to-close Flow (gate, deploy, canary, branch hygiene, archive)** — plugins_karvey_skills_karvey_deploy_skill_release_gate, plugins_karvey_skills_karvey_deploy_skill_ordered_deployment_flow, plugins_karvey_skills_karvey_deploy_skill_pr_gates_verification, plugins_karvey_skills_karvey_deploy_skill_approvals_prod_record, plugins_karvey_skills_karvey_deploy_skill_post_deploy_canary_loop, plugins_karvey_skills_karvey_deploy_skill_branch_hygiene_step, plugins_karvey_skills_karvey_archive_skill_change_archival, plugins_karvey_skills_karvey_archive_skill_branch_sweep [INFERRED 0.85]
- **Cross-cutting support skills that never modify spec.json:phase** — plugins_karvey_skills_karvey_benchmark_models_skill, plugins_karvey_skills_karvey_browse_skill, plugins_karvey_skills_karvey_checkpoint_skill, plugins_karvey_skills_karvey_context_skill, plugins_karvey_skills_karvey_decisions_skill, plugins_karvey_skills_karvey_devex_skill, plugins_karvey_skills_karvey_diagram_skill, plugins_karvey_skills_karvey_docs_skill, plugins_karvey_skills_karvey_guard_skill, plugins_karvey_skills_karvey_health_skill, plugins_karvey_skills_karvey_import_skill [EXTRACTED 1.00]
- **Findings Feedback Loop (observe/classify -> route)** — plugins_karvey_skills_karvey_test_skill_findings_classification, plugins_karvey_skills_karvey_qa_skill_nine_dimension_review, plugins_karvey_skills_karvey_iterate_skill_iteration_engine_router, plugins_karvey_skills_karvey_iterate_skill_bug_route_micro_loop, plugins_karvey_skills_karvey_iterate_skill_spec_revision_ripple_set, plugins_karvey_skills_karvey_iterate_skill_emergent_backlog_route, plugins_karvey_skills_karvey_skill_convergence_gate [EXTRACTED 1.00]
- **Cross-cutting support skills that never advance spec.json:phase** — plugins_karvey_skills_karvey_investigate_skill, plugins_karvey_skills_karvey_iterate_skill, plugins_karvey_skills_karvey_retro_skill, plugins_karvey_skills_karvey_scrape_skill, plugins_karvey_skills_karvey_second_opinion_skill, plugins_karvey_skills_karvey_standards_skill, plugins_karvey_skills_karvey_team_skill [EXTRACTED 1.00]
- **Human-in-the-loop Controls** — plugins_karvey_skills_karvey_impl_skill_human_tasks_awaiting_human, plugins_karvey_skills_karvey_tasks_skill_human_task_format, plugins_karvey_skills_karvey_infra_skill_ops_command_plan, plugins_karvey_skills_karvey_deploy_skill_approvals_prod_record, plugins_karvey_skills_karvey_test_skill_infrastructure_tests [INFERRED 0.85]
- **Production safety gates** — plugins_karvey_skills_karvey_rules_deploy_workflow_pipeline_only_deploy, plugins_karvey_skills_karvey_rules_deploy_workflow_pr_gates_before_ok, plugins_karvey_skills_karvey_rules_multi_agent_approvals_with_ref, plugins_karvey_skills_karvey_rules_multi_agent_hotfix_lane, plugins_karvey_skills_karvey_rules_deploy_workflow_zero_downtime [INFERRED 0.85]
- **Opt-in enforcement hooks (git-flow, plan-gate, standards-guard, clickup-sync-guard)** — plugins_karvey_skills_karvey_rules_enforcement_git_flow_guard, plugins_karvey_skills_karvey_rules_enforcement_plan_gate, plugins_karvey_skills_karvey_rules_engineering_standards_standards_guard, plugins_karvey_skills_karvey_rules_phase_close_clickup_sync_guard [EXTRACTED 1.00]
- **Finding routing: findings.md to BUG-NN, spec-revision, backlog** — plugins_karvey_skills_karvey_rules_iteration_loop_findings_md, plugins_karvey_skills_karvey_rules_iteration_loop_spec_revision_subcycle, plugins_karvey_skills_karvey_rules_backlog_backlog_md [EXTRACTED 1.00]
- **Nothing-lost feedback artifacts (findings, BUG-NN, backlog, revision history)** — plugins_karvey_skills_karvey_rules_backlog_backlog_md, plugins_karvey_skills_karvey_rules_incident_tracking_bug_nn_tracker, plugins_karvey_skills_karvey_rules_incident_tracking_incidents_index, plugins_karvey_skills_karvey_rules_living_specs_revision_history, plugins_karvey_skills_karvey_rules_phase_close_four_action_ritual [INFERRED 0.85]
- **Team settings stored in project.json** — plugins_karvey_skills_karvey_rules_project_config_project_json_schema, plugins_karvey_skills_karvey_rules_notifications_notification_settings, plugins_karvey_skills_karvey_rules_management_adapters_five_logical_states, plugins_karvey_skills_karvey_rules_project_config_branch_flow, plugins_karvey_skills_karvey_rules_project_config_standards_source [INFERRED 0.85]

## Communities (22 total, 0 thin omitted)

### Community 0 - "Team Layer & Support Map"
Cohesion: 0.05
Nodes (66): Release 3.8.0 agent handoff, optional team layer, verification rules, SessionStart hook, Org chart branch b: Capa transversal · 18 support skills, F-03 team cost collection unproven, PRD — Optional team layer, Team cost measurement (karvey-team cost), Agents never rotate sessions (terminal action), Optional team layer (opt-in, not default), 6-agent 3-day run evidence (~US$1,000, 7x turn cost, 13/14 blocks already answered) (+58 more)

### Community 1 - "Pipeline Phases & Architecture"
Cohesion: 0.07
Nodes (56): Org chart branch a: Pipeline 0–12 · 13 phase skills, Karvey Architecture (Phase 5), architecture.md, Mandatory Edge Cases section, Architecture Review Gate, karvey-archive Skill, Change Directory Archival, IMPLEMENTED Production Marker (+48 more)

### Community 2 - "Iteration Loop & Incidents"
Cohesion: 0.06
Nodes (52): Release 3.2.0 Iteration loop (spiral), Release 3.6.0 causal discipline in karvey-investigate, BUG-NN state history (DETECTADO → DIAGNOSTICADO → EN FIX → RESUELTO → REABIERTO), Finding types and their edge (bug · spec-gap · emergent), findings.md (single findings inbox), El bucle de iteración (bug / spec-gap / emergent), Discovery Backlog Sweep, PR Gates Verification (CI + Branch Policies) (+44 more)

### Community 3 - "Deploy, Branches & Rules Map"
Cohesion: 0.07
Nodes (39): Higiene de ramas (git merge-tree absorption proof), Canary post-deploy (zero downtime), Deploy y ramas: feature → dev → PR master, pipeline-triggered, Org chart branch c: 22 shared rules, PR gates + OK humano (approvals.prod = {by,date,ref}), OK humano para producción, Checklist de 6 pasos antes de deploy, Branch Sweep at Archive (+31 more)

### Community 4 - "Method Principles & Governance"
Cohesion: 0.08
Nodes (32): Close external PRs workflow, Compuertas de aprobación, Medido, no recordado, Nada queda en el aire, Guiado por especificaciones, Espiral, no línea, Agnóstico de stack, Cómo se piensa — seven principles (+24 more)

### Community 5 - "Import, EARS & Spec Templates"
Cohesion: 0.08
Nodes (29): gstack Heuristic Confirmation-driven Mapping, Kiro .kiro/specs to Karvey Mapping, EARS Format (init copy), EARS patterns (Ubiquitous/Event/State/Conditional/Optional), Litmus test: requirements vs design (technology-free), PRD Template (prd.md), project.json Project Config, spec.json Schema (+21 more)

### Community 6 - "Release History"
Cohesion: 0.11
Nodes (22): CHANGELOG, Human/AI traceability footer (Karvey changelog policy), Release 3.0.0, Release 3.1.0 karvey-import, Release 3.3.0 Engineering Standards layer, Release 3.4.0 AI-time estimation in minutes, Release 3.5.0 visual components catalog, Release 3.9.0 branch hygiene, standards conformance in QA, PR gates (+14 more)

### Community 7 - "Opt-in Enforcement Hooks"
Cohesion: 0.16
Nodes (12): Plan-gate override (approval marker), block(), git-flow-guard.sh script, block(), plan-gate.sh script, Branch hygiene (delete only absorbed branches), Hook-based Enforcement rule, Approval marker / override (+4 more)

### Community 8 - "Team-Adapters Requirements"
Cohesion: 0.20
Nodes (12): Requirements (EARS) team-adapters, REQ-ADP-001 ask team settings in init when missing, REQ-ADP-002 do not re-ask unless --settings, REQ-ADP-003 session hook one-line nudge, inert elsewhere, REQ-ADP-010 notification channel enum + target + via, REQ-ADP-011 notify via configured channel, skip and say if none, REQ-ADP-012 never read targets from CLAUDE.md, REQ-ADP-020 management tool enum (+4 more)

### Community 9 - "Runtime Evidence & Testing"
Cohesion: 0.20
Nodes (12): Test Coverage Plan (contract for karvey-test), Karvey Browse, findings.md (bug/spec-gap/emergent), Session cookie import for authenticated views, Post-deploy Canary Loop, Ops Command Plan + Versioned IAM Scripts, Dimension 8 Visual Audit vs design-spec, karvey-test Skill (+4 more)

### Community 10 - "QA Review & Standards Gate"
Cohesion: 0.18
Nodes (12): Release Gate (QA 0 critical/high, tests PASS, CHANGELOG), Deviation Request (deviations.md), karvey-qa Skill, 9-dimension QA Review, QA Team Notification, REVISION_PR Review Document, Dimension 7 Cross-model Second Opinion, Dimension 9 Standards Conformance (+4 more)

### Community 11 - "Multi-Agent Findings & Health"
Cohesion: 0.20
Nodes (11): Release 3.7.0 multi-agent & multi-repo work, Findings — team-layer, F-01 health checks team-layer readiness, F-02 auditor audits whoever directs, F-04 plugin cannot declare statusline, state.json (handoff machine-readable twin), Design scoring 0-10 by dimension, Karvey Health Dashboard (+3 more)

### Community 12 - "Impl Cycle & Phase Close"
Cohesion: 0.20
Nodes (11): karvey-impl Skill, DB->Backend->Frontend Execution Order, [human] Tasks and awaiting-human State, Read-Execute-Test-Validate Per-task Cycle, Pinned Inputs Read at Commit, Status Cascade Task->Feature->Epic, Phase-Close Ritual rule, clickup-sync-guard hook (opt-in) (+3 more)

### Community 13 - "Release 3.10 & Backlog"
Cohesion: 0.27
Nodes (10): Release 3.10.0 team settings on first use (team-adapters), Discovery Backlog — Karvey Method, BL-01 Run graphify over the repo (done), BL-02 Notifications configurable per team, BL-03 Task-management tool + status flow configurable, PRD team-adapters, Acceptance criteria team-adapters, Problem: hard-coded Google Chat + ClickUp "listo! para pap" (+2 more)

### Community 14 - "docs/spec Artifacts Map"
Cohesion: 0.20
Nodes (10): agent/ handoff.md · state.json · board.md, docs/bugs_dev_testing.md (BUG-NN per repo), decisions/ (D-NN · C-NN), specs/{capability}/spec.md (living specs), management.tool (clickup|jira|linear|azure-boards|github-projects|spreadsheet|markdown|other), notifications.channel (google-chat|slack|teams|email|webhook|none), Org chart branch e: Artefactos docs/spec/, Org chart branch f: Configuración del equipo (3.10) (+2 more)

### Community 15 - "Hooks Map (active vs opt-in)"
Cohesion: 0.20
Nodes (10): clickup-sync-guard (described, no script), git-flow-guard.sh (opt-in), Org chart branch d: Hooks, plan-gate.sh (opt-in), project.json (config + team settings), SessionStart hook · karvey-session-context.sh, standards-guard (described, no script), Team settings 6-step first-use flow (session → init 3.2 → notifications → management → states → project.json) (+2 more)

### Community 16 - "ClickUp Adapter & Estimation"
Cohesion: 0.20
Nodes (10): clickup-protocol.md (copy in karvey-init), ClickUp Protocol rule, AI-time estimation in minutes (10-30 min, cap ~60), .connections.json credentials (never committed), Layer tags [BD]/[Backend]/[Frontend]/[Infra]/[Test], time_estimate only via REST API (MCP does not persist it), WBS Epic > Feature > Task (E{n}.F{n}.T{n}), Tracker adapters (ClickUp, Jira, Linear, Azure Boards, GitHub Projects, spreadsheet, Markdown) (+2 more)

### Community 17 - "Logical States & Adapters"
Cohesion: 0.31
Nodes (9): 5 estados lógicos, REQ-ADP-021 logical states resolved via management.statuses, Status cascade (Task -> Feature -> Epic), Management Adapters rule, 5 logical states todo/in_progress/review/done/blocked, Logical tracker operations (create_epic, set_status, cascade, mirror_backlog...), PLAN.md fallback, 4-action close ritual (comment, state, sweep, spec.json) (+1 more)

### Community 18 - "Multi-Agent Multi-Repo Rule"
Cohesion: 0.22
Nodes (9): Multi-agent and Multi-repo rule, Business decisions D-NN, Documentation-only PR light CI, Agent environment readiness, [human] tasks and awaiting-human state, Change type ops (short pipeline), Parent/child changes (links), Pinned inputs from other agents @commit (+1 more)

### Community 19 - "Security Tiers"
Cohesion: 0.25
Nodes (8): Security Tiers (architecture rules), Security Tier Application by Layer, Security Anti-Patterns (forbidden), Tier 1 Public, Tier 2 Authenticated, Tier 3 Privileged, Tier 4 Critical, Trust Boundaries

### Community 20 - "Method Explainer Page"
Cohesion: 0.40
Nodes (5): Karvey method explainer page (karvey.html), Change types: feature, ops, hotfix, parent change, docs-only PR, Historial de versiones (3.0.0 → 3.10.0), REQ-ADP-030 ship self-contained docs/karvey.html, Karvey = Afán (Ona/Selknam word for zeal/drive)

### Community 21 - "Project Configuration"
Cohesion: 0.40
Nodes (5): project.json:notifications (channel/target/via/events), Project Configuration rule, docs/spec/project.json schema, spec_repo (1+ repos, never zero), standards source local|git (decoupled from plugin)

## Knowledge Gaps
- **78 isolated node(s):** `karvey-statusline.sh script`, `Close external PRs workflow`, `Release 3.0.0`, `Human/AI traceability footer (Karvey changelog policy)`, `Apache 2.0 license + Karvey trademark (HainTech)` (+73 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 151 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Karvey Orchestrator Skill` connect `Import, EARS & Spec Templates` to `Team Layer & Support Map`, `Pipeline Phases & Architecture`, `Iteration Loop & Incidents`, `Deploy, Branches & Rules Map`, `Method Principles & Governance`, `Release History`, `Opt-in Enforcement Hooks`, `Team-Adapters Requirements`, `Impl Cycle & Phase Close`, `docs/spec Artifacts Map`, `ClickUp Adapter & Estimation`, `Logical States & Adapters`, `Multi-Agent Multi-Repo Rule`, `Project Configuration`?**
  _High betweenness centrality (0.185) - this node is a cross-community bridge._
- **Why does `Multi-agent and Multi-repo rule` connect `Multi-Agent Multi-Repo Rule` to `Team Layer & Support Map`, `Pipeline Phases & Architecture`, `Iteration Loop & Incidents`, `Deploy, Branches & Rules Map`, `Import, EARS & Spec Templates`, `Opt-in Enforcement Hooks`, `Runtime Evidence & Testing`, `Multi-Agent Findings & Health`, `Impl Cycle & Phase Close`, `Project Configuration`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `karvey-init Skill` connect `Pipeline Phases & Architecture` to `Team Layer & Support Map`, `Iteration Loop & Incidents`, `Deploy, Branches & Rules Map`, `Import, EARS & Spec Templates`, `Release History`, `Opt-in Enforcement Hooks`, `Team-Adapters Requirements`, `Release 3.10 & Backlog`, `Hooks Map (active vs opt-in)`, `ClickUp Adapter & Estimation`, `Logical States & Adapters`, `Multi-Agent Multi-Repo Rule`, `Project Configuration`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Management Adapters rule` (e.g. with `REQ-ADP-020 management tool enum` and `REQ-ADP-021 logical states resolved via management.statuses`) actually correct?**
  _`Management Adapters rule` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `karvey-statusline.sh script`, `Close external PRs workflow`, `Release 3.0.0` to the rest of the system?**
  _78 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Team Layer & Support Map` be split into smaller, more focused modules?**
  _Cohesion score 0.05454545454545454 - nodes in this community are weakly interconnected._
- **Should `Pipeline Phases & Architecture` be split into smaller, more focused modules?**
  _Cohesion score 0.07077922077922078 - nodes in this community are weakly interconnected._