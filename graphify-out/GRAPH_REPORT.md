# Graph Report - karvey  (2026-09-22)

## Corpus Check
- 82 files · ~77,957 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 7)

## Summary
- 384 nodes · 912 edges · 12 communities
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 85 edges (avg confidence: 0.85)
- Token cost: 555,065 input · 0 output

## Community Hubs (Navigation)
- Iteration Loop & Runtime Evidence
- Handoff, Team Layer & Verification
- Release Flow & Branch Hygiene
- EARS, Living Specs & Spec Metadata
- Engineering Standards & Security Tiers
- Releases, Import & Enforcement
- Plugin Hooks & Scripts
- Support Skills (DevEx, Diagram, Benchmark)
- Pre-Spec & ClickUp Protocol
- Multi-Agent Multi-Repo
- Design & Visual Catalog
- Causal Investigation

## God Nodes (most connected - your core abstractions)
1. `Karvey orchestrator skill` - 50 edges
2. `Karvey Deploy (Phase 11)` - 35 edges
3. `karvey-init skill` - 34 edges
4. `karvey-iterate skill` - 34 edges
5. `Multi-agent and Multi-repo rule` - 34 edges
6. `karvey-qa skill` - 27 edges
7. `Knowledge Sync rule` - 26 edges
8. `Deployment Flow rule` - 24 edges
9. `Release 3.7.0 — multi-agent / multi-repo` - 23 edges
10. `karvey-test skill` - 23 edges

## Surprising Connections (you probably didn't know these)
- `REQ-TEAM-020 cross decision log before declaring block` --semantically_similar_to--> `Causal-coherence gate`  [INFERRED] [semantically similar]
  docs/spec/changes/team-layer/requirements.md → CHANGELOG.md
- `Feedback edges bug / spec-gap / emergent` --semantically_similar_to--> `Iteration loop (spiral, not a line)`  [INFERRED] [semantically similar]
  plugins/karvey/skills/karvey/SKILL.md → README.md
- `Trademark Policy (skill copy)` --semantically_similar_to--> `Trademark Policy — Karvey`  [INFERRED] [semantically similar]
  plugins/karvey/skills/karvey/TRADEMARK.md → TRADEMARK.md
- `Trademark Policy (plugin copy)` --semantically_similar_to--> `Trademark Policy — Karvey`  [INFERRED] [semantically similar]
  plugins/karvey/TRADEMARK.md → TRADEMARK.md
- `F-04 plugin cannot declare statusline` --references--> `karvey-statusline.sh (rotation statusline)`  [INFERRED]
  docs/spec/changes/team-layer/findings.md → plugins/karvey/hooks/README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three-phase standards conformance gate (design decides, impl follows, QA verifies)** — changelog_engineering_standards_layer, changelog_deviation_request, changelog_standards_conformance_dimension, plugins_karvey_skills_karvey_architecture_skill, plugins_karvey_skills_karvey_impl_skill, plugins_karvey_skills_karvey_qa_skill [EXTRACTED 1.00]
- **Deploy-to-prod safeguards** — changelog_pr_gates_verification, changelog_git_host_detection, changelog_prod_approval_record, changelog_branch_hygiene, plugins_karvey_skills_karvey_deploy_skill [INFERRED 0.85]
- **Iteration loop feedback edges (bug / spec-gap / emergent)** — readme_iteration_loop_spiral, readme_findings_md, readme_bug_nn_incident_tracker, readme_discovery_backlog, plugins_karvey_skills_karvey_iterate_skill, changelog_convergence_gate [EXTRACTED 1.00]
- **Karvey trademark policy and its copies** — trademark, plugins_karvey_trademark, plugins_karvey_skills_karvey_trademark, trademark_karvey_trademark, _github_workflows_close_external_prs [INFERRED 0.85]
- **Team-layer change (PRD, requirements, findings, skills, rules, hooks)** — docs_spec_changes_team_layer_prd, docs_spec_changes_team_layer_requirements, docs_spec_changes_team_layer_findings, plugins_karvey_skills_karvey_team_skill, plugins_karvey_skills_karvey_decisions_skill, plugins_karvey_skills_karvey_rules_team, plugins_karvey_skills_karvey_rules_verification [EXTRACTED 1.00]
- **Karvey phase pipeline: design-graphic → architecture → infra → impl → deploy → archive** — plugins_karvey_skills_karvey_design_graphic_skill, plugins_karvey_skills_karvey_architecture_skill, plugins_karvey_skills_karvey_infra_skill, plugins_karvey_skills_karvey_impl_skill, plugins_karvey_skills_karvey_deploy_skill, plugins_karvey_skills_karvey_archive_skill [EXTRACTED 1.00]
- **Pipeline-only deploy with human prod OK (never manual)** — plugins_karvey_skills_karvey_deploy_skill, plugins_karvey_skills_karvey_infra_skill, plugins_karvey_skills_karvey_guard_skill, plugins_karvey_skills_karvey_rules_deploy_workflow, plugins_karvey_skills_karvey_hooks_git_flow_guard [INFERRED 0.85]
- **Cross-cutting support skills that never modify spec.json:phase** — plugins_karvey_skills_karvey_benchmark_models_skill, plugins_karvey_skills_karvey_browse_skill, plugins_karvey_skills_karvey_checkpoint_skill, plugins_karvey_skills_karvey_context_skill, plugins_karvey_skills_karvey_decisions_skill, plugins_karvey_skills_karvey_devex_skill, plugins_karvey_skills_karvey_diagram_skill, plugins_karvey_skills_karvey_docs_skill, plugins_karvey_skills_karvey_guard_skill, plugins_karvey_skills_karvey_health_skill, plugins_karvey_skills_karvey_import_skill [EXTRACTED 1.00]
- **Karvey iteration feedback loop (observe/classify -> route)** — plugins_karvey_skills_karvey_test_skill, plugins_karvey_skills_karvey_qa_skill, plugins_karvey_skills_karvey_mockup_skill, plugins_karvey_skills_karvey_iterate_skill, plugins_karvey_skills_karvey_iterate_skill_findings_inbox, plugins_karvey_skills_karvey_iterate_skill_bug_route, plugins_karvey_skills_karvey_iterate_skill_spec_revision_subcycle, plugins_karvey_skills_karvey_iterate_skill_emergent_backlog_route [EXTRACTED 1.00]
- **QA micro-loop impl -> test -> qa for bug fixes** — plugins_karvey_skills_karvey_impl_skill, plugins_karvey_skills_karvey_test_skill, plugins_karvey_skills_karvey_qa_skill, plugins_karvey_skills_karvey_iterate_skill_bug_route, plugins_karvey_skills_karvey_test_skill_regression_tests [EXTRACTED 1.00]
- **Cross-cutting support skills that never advance spec.json:phase** — plugins_karvey_skills_karvey_investigate_skill, plugins_karvey_skills_karvey_iterate_skill, plugins_karvey_skills_karvey_retro_skill, plugins_karvey_skills_karvey_scrape_skill, plugins_karvey_skills_karvey_second_opinion_skill, plugins_karvey_skills_karvey_standards_skill, plugins_karvey_skills_karvey_team_skill [EXTRACTED 1.00]
- **Iteration feedback loop (findings routed by karvey-iterate)** — plugins_karvey_skills_karvey_iterate_skill, plugins_karvey_skills_karvey_skill_feedback_edges, plugins_karvey_skills_karvey_skill_incident_tracker_bug_nn, plugins_karvey_skills_karvey_rules_backlog, plugins_karvey_skills_karvey_requirements_skill [EXTRACTED 1.00]
- **Release traceability: semver + CHANGELOG + 6-step checklist + prod approval** — plugins_karvey_skills_karvey_rules_versioning_semver, plugins_karvey_skills_karvey_rules_changelog_policy_changelog_md, plugins_karvey_skills_karvey_rules_deploy_workflow_six_step_checklist, plugins_karvey_skills_karvey_rules_multi_agent_approvals_with_ref [INFERRED 0.85]
- **Opt-in enforcement hooks (git-flow, plan-gate, standards-guard, clickup-sync-guard)** — plugins_karvey_skills_karvey_rules_enforcement_git_flow_guard, plugins_karvey_skills_karvey_rules_enforcement_plan_gate, plugins_karvey_skills_karvey_rules_engineering_standards_standards_guard, plugins_karvey_skills_karvey_rules_phase_close_clickup_sync_guard [EXTRACTED 1.00]
- **Finding routing: findings.md to BUG-NN, spec-revision, backlog** — plugins_karvey_skills_karvey_rules_iteration_loop_findings_md, plugins_karvey_skills_karvey_rules_incident_tracking_bug_nn, plugins_karvey_skills_karvey_rules_iteration_loop_spec_revision_subcycle, plugins_karvey_skills_karvey_rules_backlog_backlog_md [EXTRACTED 1.00]

## Communities (12 total, 0 thin omitted)

### Community 0 - "Iteration Loop & Runtime Evidence"
Cohesion: 0.06
Nodes (60): AI-time estimation in minutes (10-30 min, cap 60), Convergence gate, Mandatory phase-close ritual, Release 3.2.0 — iteration loop, Release 3.4.0 — AI-time estimation, Discovery Backlog — Karvey Method, Karvey Browse, findings.md (bug/spec-gap/emergent) (+52 more)

### Community 1 - "Handoff, Team Layer & Verification"
Cohesion: 0.06
Nodes (56): Agent handoff (handoff.md + state.json), Decision log D-NN / C-NN with cross-check, Release 3.8.0 — agent handoff, team layer, verification, 18 verification failure modes, F-03 team cost collection unproven, PRD — Optional team layer, Team cost measurement (karvey-team cost), Agents never rotate sessions (terminal action) (+48 more)

### Community 2 - "Release Flow & Branch Hygiene"
Cohesion: 0.09
Nodes (43): Karvey CHANGELOG, Branch hygiene (nothing left in branches), Documentation-only PR lane (light CI), Documentation drift (counts, hooks, stale rule copies), Git host detection (project.json:git_platform), Hotfix lane (fix + BUG-NN + regression test same PR), Human/AI traceability in changelog entries, Change type ops (+35 more)

### Community 3 - "EARS, Living Specs & Spec Metadata"
Cohesion: 0.07
Nodes (38): EARS Format (init copy), EARS patterns (Ubiquitous/Event/State/Conditional/Optional), Litmus test: requirements vs design (technology-free), Living Specs (init copy), approvals.* phase gates in spec.json, Archiving protocol (merge deltas into living specs), Capabilities convention (functional domains), iteration_count / revision_history fields (+30 more)

### Community 4 - "Engineering Standards & Security Tiers"
Cohesion: 0.08
Nodes (34): Deviation Request / deviations.md, Engineering standards layer (golden paths), [human] tasks and awaiting-human state, PR gates verification before prod OK, Release 3.3.0 — engineering standards layer, QA Dimension 9 — Standards conformance, Method/standards separation (two planes), Security Tiers (architecture rules) (+26 more)

### Community 5 - "Releases, Import & Enforcement"
Cohesion: 0.10
Nodes (32): Release 3.0.0 — initial publication, Release 3.1.0 — karvey-import, Unreleased — graphify-out repo maintenance, BL-01 Run graphify over the repo, Spec-Delta Merge into Living Specs (ADDED/MODIFIED/REMOVED), Karvey Import (Kiro/gstack), Kiro (cc-sdd) to Karvey mapping, Sweep is not silent (+24 more)

### Community 6 - "Plugin Hooks & Scripts"
Cohesion: 0.11
Nodes (26): Close external PRs workflow, emit(), karvey-session-context.sh script, Karvey hooks README, Plugin: karvey README, Plan-gate override (approval marker), block(), git-flow-guard.sh script (+18 more)

### Community 7 - "Support Skills (DevEx, Diagram, Benchmark)"
Cohesion: 0.08
Nodes (24): Findings — team-layer, F-01 health checks team-layer readiness, F-02 auditor audits whoever directs, F-04 plugin cannot declare statusline, Karvey Benchmark Models, LLM-Judge quality scoring, Karvey DevEx Reviewer, Docs lies (+16 more)

### Community 8 - "Pre-Spec & ClickUp Protocol"
Cohesion: 0.13
Nodes (23): Karvey Grill (Pre-Spec Interrogation), Interrogation tree (branches A-F), Pre-Spec Summary (PRD input), 10-star reframe, gstack to Karvey mapping, ClickUp Protocol (init copy), AI-time estimation in minutes (10-30 min, cap ~60 min), .connections.json credentials file (never committed) (+15 more)

### Community 9 - "Multi-Agent Multi-Repo"
Cohesion: 0.12
Nodes (17): Parent / child changes across repos, Verify PR gates before prod OK, Regression test required for RESUELTO, Multi-agent and Multi-repo rule, Agent environment readiness, Approvals with decision reference (by/role/ref), Business decisions D-NN, Documentation-only PR lane (spec-lint) (+9 more)

### Community 10 - "Design & Visual Catalog"
Cohesion: 0.15
Nodes (16): Release 3.5.0 — visual components catalog, Visual components catalog (design-components.md), architecture.md, Karvey Design Graphic, Forbidden design anti-patterns, design-components.md (visual components catalog), Design scoring 0-10 by dimension, design-spec.md (+8 more)

### Community 11 - "Causal Investigation"
Cohesion: 0.31
Nodes (11): Causal-coherence gate, Causal discipline: what CHANGED before what is WRONG, Incident window (dated symptom), Release 3.6.0 — causal discipline in investigate, karvey-investigate skill, Causal-coherence gate (cause vs latent fragility), Incident window (date the symptom), Iron Law: no fix without root-cause investigation (+3 more)

## Knowledge Gaps
- **24 isolated node(s):** `karvey-statusline.sh script`, `Human/AI traceability in changelog entries`, `Claude Code plugin install (karvey@karvey-methods)`, `Karvey = Afan (Ona/Selknam word)`, `IMPLEMENTED production marker` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 87 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Karvey orchestrator skill` connect `Releases, Import & Enforcement` to `Iteration Loop & Runtime Evidence`, `Handoff, Team Layer & Verification`, `Release Flow & Branch Hygiene`, `EARS, Living Specs & Spec Metadata`, `Engineering Standards & Security Tiers`, `Plugin Hooks & Scripts`, `Support Skills (DevEx, Diagram, Benchmark)`, `Pre-Spec & ClickUp Protocol`, `Multi-Agent Multi-Repo`, `Design & Visual Catalog`, `Causal Investigation`?**
  _High betweenness centrality (0.314) - this node is a cross-community bridge._
- **Why does `Multi-agent and Multi-repo rule` connect `Multi-Agent Multi-Repo` to `Iteration Loop & Runtime Evidence`, `Handoff, Team Layer & Verification`, `Release Flow & Branch Hygiene`, `EARS, Living Specs & Spec Metadata`, `Engineering Standards & Security Tiers`, `Releases, Import & Enforcement`, `Pre-Spec & ClickUp Protocol`, `Design & Visual Catalog`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `karvey-iterate skill` connect `Iteration Loop & Runtime Evidence` to `Release Flow & Branch Hygiene`, `EARS, Living Specs & Spec Metadata`, `Engineering Standards & Security Tiers`, `Releases, Import & Enforcement`, `Support Skills (DevEx, Diagram, Benchmark)`, `Pre-Spec & ClickUp Protocol`, `Multi-Agent Multi-Repo`, `Design & Visual Catalog`, `Causal Investigation`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **What connects `karvey-statusline.sh script`, `Human/AI traceability in changelog entries`, `Claude Code plugin install (karvey@karvey-methods)` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Iteration Loop & Runtime Evidence` be split into smaller, more focused modules?**
  _Cohesion score 0.06497175141242938 - nodes in this community are weakly interconnected._
- **Should `Handoff, Team Layer & Verification` be split into smaller, more focused modules?**
  _Cohesion score 0.05827067669172932 - nodes in this community are weakly interconnected._
- **Should `Release Flow & Branch Hygiene` be split into smaller, more focused modules?**
  _Cohesion score 0.08527131782945736 - nodes in this community are weakly interconnected._