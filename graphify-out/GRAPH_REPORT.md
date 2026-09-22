# Graph Report - karvey  (2026-09-22)

## Corpus Check
- 82 files · ~77,745 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 7)

## Summary
- 399 nodes · 753 edges · 21 communities (18 shown, 3 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 68 edges (avg confidence: 0.84)
- Token cost: 477,137 input · 0 output

## Community Hubs (Navigation)
- Deploy, Context & Release Flow
- Runtime Evidence & Investigation
- Security Tiers & Architecture
- Archive, Docs & Pre-Spec
- Living Specs & spec.json
- Team Layer & Causal Discipline
- Handoff, Decisions & Guard
- Licensing, Trademark & Pipeline
- Orchestrator Skill Map
- Backlog & Knowledge Sync
- Team-Layer Findings
- Security Tier Rule Copies
- Standards & Design Releases
- AI Estimation & Rule Drift
- Branch Hygiene & PR Gates
- Iteration Loop Core
- Multi-Agent Multi-Repo
- DevEx Review
- Session Context Hook
- Statusline Script
- Model Benchmarking

## God Nodes (most connected - your core abstractions)
1. `Karvey orchestrator skill` - 54 edges
2. `Multi-agent and Multi-repo rule` - 28 edges
3. `karvey-iterate skill` - 28 edges
4. `karvey-init skill` - 27 edges
5. `Karvey Deploy (Phase 11)` - 23 edges
6. `karvey-qa skill` - 22 edges
7. `Knowledge Sync rule` - 20 edges
8. `karvey-test skill` - 19 edges
9. `Engineering Standards rule` - 17 edges
10. `Iteration Loop rule` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Feedback edges bug / spec-gap / emergent` --semantically_similar_to--> `Iteration loop (spiral, not a line)`  [INFERRED] [semantically similar]
  plugins/karvey/skills/karvey/SKILL.md → README.md
- `Karvey orchestrator skill` --implements--> `13-phase pipeline (0-12)`  [INFERRED]
  plugins/karvey/skills/karvey/SKILL.md → README.md
- `Trademark Policy (skill copy)` --semantically_similar_to--> `Trademark Policy — Karvey`  [INFERRED] [semantically similar]
  plugins/karvey/skills/karvey/TRADEMARK.md → TRADEMARK.md
- `Trademark Policy (plugin copy)` --semantically_similar_to--> `Trademark Policy — Karvey`  [INFERRED] [semantically similar]
  plugins/karvey/TRADEMARK.md → TRADEMARK.md
- `REQ-TEAM-020 cross decision log before declaring block` --semantically_similar_to--> `Causal-coherence gate (what CHANGED before what is WRONG)`  [INFERRED] [semantically similar]
  docs/spec/changes/team-layer/requirements.md → CHANGELOG.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Team-layer change (PRD, requirements, findings, skills, rules, hooks)** — docs_spec_changes_team_layer_prd, docs_spec_changes_team_layer_requirements, docs_spec_changes_team_layer_findings, plugins_karvey_skills_karvey_skill_karvey_team, plugins_karvey_skills_karvey_skill_karvey_decisions, plugins_karvey_skills_karvey_skill_rules_team, plugins_karvey_skills_karvey_skill_rules_verification, readme_session_start_hook [EXTRACTED 1.00]
- **Iteration feedback loop (findings routed by karvey-iterate)** — plugins_karvey_skills_karvey_skill_karvey_iterate, plugins_karvey_skills_karvey_skill_feedback_edges, plugins_karvey_skills_karvey_skill_incident_tracker_bug_nn, plugins_karvey_skills_karvey_skill_rules_backlog, plugins_karvey_skills_karvey_skill_karvey_requirements, readme_convergence_rule [EXTRACTED 1.00]
- **Karvey trademark policy and its copies** — trademark, plugins_karvey_trademark, plugins_karvey_skills_karvey_trademark, trademark_karvey_trademark, _github_workflows_close_external_prs [INFERRED 0.85]
- **Opt-in enforcement hooks (git-flow, plan-gate, standards-guard, clickup-sync-guard)** — plugins_karvey_skills_karvey_rules_enforcement_git_flow_guard, plugins_karvey_skills_karvey_rules_enforcement_plan_gate, plugins_karvey_skills_karvey_rules_engineering_standards_standards_guard, plugins_karvey_skills_karvey_rules_phase_close_clickup_sync_guard [EXTRACTED 1.00]
- **Finding routing: findings.md to BUG-NN, spec-revision, backlog** — plugins_karvey_skills_karvey_rules_iteration_loop_findings_md, plugins_karvey_skills_karvey_rules_incident_tracking_bug_nn, plugins_karvey_skills_karvey_rules_iteration_loop_spec_revision_subcycle, plugins_karvey_skills_karvey_rules_backlog_backlog_md [EXTRACTED 1.00]
- **Release traceability: semver + CHANGELOG + 6-step checklist + prod approval** — plugins_karvey_skills_karvey_rules_versioning_semver, plugins_karvey_skills_karvey_rules_changelog_policy_changelog_md, plugins_karvey_skills_karvey_rules_deploy_workflow_six_step_checklist, plugins_karvey_skills_karvey_rules_multi_agent_approvals_with_ref [INFERRED 0.85]
- **Karvey phase pipeline: design-graphic → architecture → infra → impl → deploy → archive** — plugins_karvey_skills_karvey_design_graphic_skill, plugins_karvey_skills_karvey_architecture_skill, plugins_karvey_skills_karvey_infra_skill, plugins_karvey_skills_karvey_impl_skill, plugins_karvey_skills_karvey_deploy_skill, plugins_karvey_skills_karvey_archive_skill [EXTRACTED 1.00]
- **Cross-cutting support skills that never modify spec.json:phase** — plugins_karvey_skills_karvey_benchmark_models_skill, plugins_karvey_skills_karvey_browse_skill, plugins_karvey_skills_karvey_checkpoint_skill, plugins_karvey_skills_karvey_context_skill, plugins_karvey_skills_karvey_decisions_skill, plugins_karvey_skills_karvey_devex_skill, plugins_karvey_skills_karvey_diagram_skill, plugins_karvey_skills_karvey_docs_skill, plugins_karvey_skills_karvey_guard_skill, plugins_karvey_skills_karvey_health_skill, plugins_karvey_skills_karvey_import_skill [EXTRACTED 1.00]
- **Pipeline-only deploy with human prod OK (never manual)** — plugins_karvey_skills_karvey_deploy_skill, plugins_karvey_skills_karvey_infra_skill, plugins_karvey_skills_karvey_guard_skill, plugins_karvey_skills_karvey_rules_deploy_workflow, plugins_karvey_skills_karvey_hooks_git_flow_guard [INFERRED 0.85]
- **Karvey iteration feedback loop (observe/classify -> route)** — plugins_karvey_skills_karvey_test_skill, plugins_karvey_skills_karvey_qa_skill, plugins_karvey_skills_karvey_mockup_skill, plugins_karvey_skills_karvey_iterate_skill, plugins_karvey_skills_karvey_iterate_skill_findings_inbox, plugins_karvey_skills_karvey_iterate_skill_bug_route, plugins_karvey_skills_karvey_iterate_skill_spec_revision_subcycle, plugins_karvey_skills_karvey_iterate_skill_emergent_backlog_route [EXTRACTED 1.00]
- **QA micro-loop impl -> test -> qa for bug fixes** — plugins_karvey_skills_karvey_impl_skill, plugins_karvey_skills_karvey_test_skill, plugins_karvey_skills_karvey_qa_skill, plugins_karvey_skills_karvey_iterate_skill_bug_route, plugins_karvey_skills_karvey_test_skill_regression_tests [EXTRACTED 1.00]
- **Cross-cutting support skills that never advance spec.json:phase** — plugins_karvey_skills_karvey_investigate_skill, plugins_karvey_skills_karvey_iterate_skill, plugins_karvey_skills_karvey_retro_skill, plugins_karvey_skills_karvey_scrape_skill, plugins_karvey_skills_karvey_second_opinion_skill, plugins_karvey_skills_karvey_standards_skill, plugins_karvey_skills_karvey_team_skill [EXTRACTED 1.00]

## Communities (21 total, 3 thin omitted)

### Community 0 - "Deploy, Context & Release Flow"
Cohesion: 0.05
Nodes (61): Branch Sweep, Karvey Context Dashboard, Deploy Queue / Landing Report, D-NN / C-NN decision series, Karvey Deploy (Phase 11), approvals.prod record (by/date/D-NN), Post-deploy Canary Loop (zero-downtime), Deploy platform auto-detection (+53 more)

### Community 1 - "Runtime Evidence & Investigation"
Cohesion: 0.07
Nodes (42): Karvey Browse, findings.md (bug/spec-gap/emergent), Session cookie import for authenticated views, Karvey Health Dashboard, health-history.jsonl, Change goal (north star), karvey-investigate skill, Causal-coherence gate (cause vs latent fragility) (+34 more)

### Community 2 - "Security Tiers & Architecture"
Cohesion: 0.06
Nodes (41): Security Tiers (architecture rules), Security Tier Application by Layer, Security Anti-Patterns (forbidden), Tier 1 Public, Tier 2 Authenticated, Tier 3 Privileged, Tier 4 Critical, Karvey Architecture (Phase 5) (+33 more)

### Community 3 - "Archive, Docs & Pre-Spec"
Cohesion: 0.08
Nodes (40): Karvey Archive (Phase 12), Discovery Backlog Sweep, IMPLEMENTED production marker, Spec-Delta Merge into Living Specs (ADDED/MODIFIED/REMOVED), Karvey Docs (Doc Engineer), Diataxis framework (tutorial/how-to/reference/explanation), pdf mode: publication-quality PDF export, release mode: update stale docs (+32 more)

### Community 4 - "Living Specs & spec.json"
Cohesion: 0.07
Nodes (39): Living Specs (init copy), approvals.* phase gates in spec.json, Archiving protocol (merge deltas into living specs), Capabilities convention (functional domains), iteration_count / revision_history fields, spec-delta.md (ADDED/MODIFIED/REMOVED), spec.json change metadata schema, spec-gap -> spec-revision sub-cycle with ripple set (+31 more)

### Community 5 - "Team Layer & Causal Discipline"
Cohesion: 0.10
Nodes (38): Causal-coherence gate (what CHANGED before what is WRONG), 3.6.0 causal discipline in investigate, 3.8.0 team layer + handoff + hooks, F-03 team cost collection unproven, PRD — Optional team layer, Team cost measurement (karvey-team cost), Agents never rotate sessions (terminal action), Optional team layer (opt-in, not default) (+30 more)

### Community 6 - "Handoff, Decisions & Guard"
Cohesion: 0.08
Nodes (33): Karvey Checkpoint, Change checkpoint.md, Agent handoff.md, Measured, not recalled (handoff principle), state.json (handoff machine-readable twin), Karvey Decisions Log, cross: check before declaring a block, Karvey Guard (+25 more)

### Community 7 - "Licensing, Trademark & Pipeline"
Cohesion: 0.17
Nodes (18): Close external PRs workflow, 3.0.0 initial publication, --autoplan planning chain, Trademark Policy (skill copy), Trademark Policy (plugin copy), 13-phase pipeline (0-12), Apache License 2.0, Convergence rule / gate (+10 more)

### Community 8 - "Orchestrator Skill Map"
Cohesion: 0.15
Nodes (16): Karvey orchestrator skill, karvey-architecture, karvey-browse, karvey-context, karvey-docs, karvey-grill, karvey-impl, karvey-infra (+8 more)

### Community 9 - "Backlog & Knowledge Sync"
Cohesion: 0.25
Nodes (9): Discovery Backlog — Karvey Method, BL-01 Run graphify over the repo, karvey-archive, karvey-init, project.json (config incl. knowledge_sync), rules/backlog.md, rules/knowledge-sync.md, rules/living-specs.md (+1 more)

### Community 10 - "Team-Layer Findings"
Cohesion: 0.25
Nodes (9): Findings — team-layer, F-01 health checks team-layer readiness, F-02 auditor audits whoever directs, F-04 plugin cannot declare statusline, Feedback edges bug / spec-gap / emergent, BUG-NN incident tracker, karvey-health, karvey-retro (+1 more)

### Community 11 - "Security Tier Rule Copies"
Cohesion: 0.25
Nodes (9): Security Tiers (init copy), Forbidden security anti-patterns, Security Tiers 1-4 (Public/Authenticated/Privileged/Critical), Security Tiers (requirements copy), BL-NN backlog item, spec.json change metadata, Security Tiers rule, Security anti-patterns (+1 more)

### Community 12 - "Standards & Design Releases"
Cohesion: 0.25
Nodes (8): CHANGELOG (Karvey), deviations.md (approved departures from standards), 3.1.0 karvey-import, 3.3.0 engineering standards layer, 3.5.0 visual components catalog, karvey-design-graphic, karvey-import, karvey-standards

### Community 13 - "AI Estimation & Rule Drift"
Cohesion: 0.29
Nodes (7): AI-time estimation in minutes, Stale local rule copies (silent behavior bug), 3.4.0 AI-time estimation in minutes, 3.9.1 documentation drift fix, karvey-tasks, rules/clickup-protocol.md, Skills catalog (32 = 1+13+18)

### Community 14 - "Branch Hygiene & PR Gates"
Cohesion: 0.38
Nodes (7): PR gates verification + git host detection, 3.9.0 branch hygiene + standards conformance + PR gates, Branch hygiene — nothing left in branches, karvey-deploy, karvey-qa, 9-dimension QA with blocking security gate, rules/deploy-workflow.md

### Community 15 - "Iteration Loop Core"
Cohesion: 0.50
Nodes (5): 3.2.0 iteration loop, karvey-iterate, rules/incident-tracking.md, rules/iteration-loop.md, rules/phase-close.md

### Community 16 - "Multi-Agent Multi-Repo"
Cohesion: 0.83
Nodes (4): 3.7.0 multi-agent / multi-repo, Change types ops / hotfix, Parent / child changes across repos, rules/multi-agent.md

### Community 17 - "DevEx Review"
Cohesion: 0.50
Nodes (4): Karvey DevEx Reviewer, Docs lies, Three lenses: Expansion / Polish / Triage, Time-to-Hello-World (TTHW)

## Knowledge Gaps
- **27 isolated node(s):** `karvey-statusline.sh script`, `Karvey = Afan (Ona/Selknam word)`, `karvey-grill`, `karvey-mockup`, `karvey-infra` (+22 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 95 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Karvey orchestrator skill` connect `Orchestrator Skill Map` to `Runtime Evidence & Investigation`, `Security Tiers & Architecture`, `Archive, Docs & Pre-Spec`, `Team Layer & Causal Discipline`, `Licensing, Trademark & Pipeline`, `Backlog & Knowledge Sync`, `Team-Layer Findings`, `Standards & Design Releases`, `AI Estimation & Rule Drift`, `Branch Hygiene & PR Gates`, `Iteration Loop Core`, `Multi-Agent Multi-Repo`?**
  _High betweenness centrality (0.468) - this node is a cross-community bridge._
- **Why does `karvey-iterate skill` connect `Runtime Evidence & Investigation` to `Deploy, Context & Release Flow`, `Security Tiers & Architecture`, `Archive, Docs & Pre-Spec`, `Living Specs & spec.json`, `Orchestrator Skill Map`?**
  _High betweenness centrality (0.170) - this node is a cross-community bridge._
- **Why does `Multi-agent and Multi-repo rule` connect `Deploy, Context & Release Flow` to `Runtime Evidence & Investigation`, `Security Tiers & Architecture`, `Archive, Docs & Pre-Spec`, `Living Specs & spec.json`, `Handoff, Decisions & Guard`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **What connects `karvey-statusline.sh script`, `Karvey = Afan (Ona/Selknam word)`, `karvey-grill` to the rest of the system?**
  _27 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Deploy, Context & Release Flow` be split into smaller, more focused modules?**
  _Cohesion score 0.05081967213114754 - nodes in this community are weakly interconnected._
- **Should `Runtime Evidence & Investigation` be split into smaller, more focused modules?**
  _Cohesion score 0.0743321718931475 - nodes in this community are weakly interconnected._
- **Should `Security Tiers & Architecture` be split into smaller, more focused modules?**
  _Cohesion score 0.05975609756097561 - nodes in this community are weakly interconnected._