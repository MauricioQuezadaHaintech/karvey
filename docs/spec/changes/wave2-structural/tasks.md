# Tasks: wave2-structural

> PHASE 7 (`karvey-tasks`, skill text read from `plugins/karvey/skills/karvey-tasks/SKILL.md` in this worktree) · Security Tier 2 · Lane `standard` · Tracker: Markdown (`project.json:management.tool = markdown`): this file + `PLAN.md`, no external tracker.
> Inputs: `architecture.md` (approved, D-21), `requirements.md` (REQ-W2-001..088, approved, D-21), `prd.md`, `spec.json`, the house style of `project-upgrade/tasks.md` and `wave1-hardening/tasks.md`, and the code on `feature/wave2-structural`.
>
> **Estimates are calibrated.** In this repo the skill's 10–30 min band ran about 10× high. The minutes below are realistic **AI execution + human review** for one task (typically 3–8 min AI + 2–7 min review). `karvey-impl` records the actuals next to them in `PLAN.md` and never edits an estimate.

## Summary

| Item | Value |
|---|---|
| Features | 13 (the PLAN.md features F1..F13, same numbering) |
| Tasks | 71 (61 Backend, 8 Test, 2 human) |
| Agent tasks / `[human]` tasks | 69 / 2 |
| Total estimate (agent tasks, AI + review, calibrated) | **706 min** (≈ 11.8 h) |
| Critical path by dependencies (agent minutes; `[human]` waits not counted) | **141 min** (≈ 2.4 h), 12 tasks |
| REQ-W2 coverage | 88/88 |
| Largest task | 15 min (cap 60) |

## Conventions

- **IDs** `E1.F{n}.T{n}`; E1 = this change, F{n} = the PLAN.md feature of the same number (the architecture's components C-01..C-24 map to them in each feature header).
- **Layers:** `[Backend]` = plugin scripts, library, schemas, hooks and skill/rule text (the plugin is this change's backend, `spec.json:layers`); `[Test]` = test-only work (tables, integration suites, manual scripts); `[human]` = a step only a person may run (`rules/multi-agent.md` §5). No DB, Frontend or Infra task: no cloud, CI is the existing `lint.yml` (infra skipped).
- **Estimate** = AI execution + review, minutes, calibrated (header). `[human]` tasks carry no estimate; they declare the executor.
- **(P)** = can run in parallel with other (P) tasks whose dependencies are met, because the files differ. Tasks that share `karvey-state.py`, `lint-plugin.py`, `karvey-context.py` or `karvey-release-gate.py` run in sequence even when marked (P) elsewhere; `karvey-impl` picks the order.
- **Every impl commit** carries `Karvey-Change: wave2-structural` (REQ-W2-043, 088), adds one line under `## [Unreleased]` in `CHANGELOG.md`, and changes no version. The version number is fixed at release by `karvey-deploy` (architecture A-01).
- **Tests** are tagged `@req REQ-W2-NNN` in their docstring or named `test_REQ_W2_NNN_*` (REQ-W2-058 applies to this change's own tests).
- **Done criterion** is a command, run from the repo root. Unit tests: `python3 -m unittest discover -s plugins/karvey/tests/unit -p '<file>' -v`. Tables: `python3 plugins/karvey/tests/hooks/run_tables.py --only <table>`. Lint: `python3 plugins/karvey/scripts/lint-plugin.py [--only L-NN]` — 0 errors after every task.
- **Neutral text:** no organisation, product, client or person names, no ids, no home paths, no secrets in any new file (PRD §9). Fixtures are anonymised (`test_fixtures_anonymous.py`).
- **Nothing outside the repository is written** by an agent task; the owner's global instructions change is a diff file (E1.F2.T8) applied by the owner (E1.F13.T8).

## Execution order

1. **F1 first** (panel Ola 2 order): schemas, check modes, the state-tool logs, the metrics view — and the **baseline** of this repo (E1.F1.T9) before any Wave 2 default is set here (E1.F13.T4 depends on it).
2. **F2 lanes + F3 judges** once the schemas exist. The state-tool spine runs E1.F1.T3 → T4 → T5 → E1.F2.T3 → E1.F2.T4 → E1.F3.T4 → E1.F4.T1 → E1.F4.T2 → E1.F5.T5 → E1.F13.T1 (one file).
3. **F4 merged gates + F5 release per change** (warn mode). F9 scripts (id, health, evidence) and F6 `--check` can start at any time: they have no dependency.
4. **F6..F12** as their dependencies land.
5. **F13**: `--fix`, compat table, the end-to-end flow, this repo's settings, the upgrade-step hand-off, the whole-repo gate, release docs, then the two `[human]` tasks. Archive is the next phase, not a task here. 4.0.0 is a later release of its own (REQ-W2-086).

## Feature E1.F1: Records and flow metrics (first: the baseline precedes every default)

Architecture §1.4 (logs), §1.5, §1.6, §2.1, §2.2, §7.1 step 2.  
Requirements covered: 001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 019, 038, 040, 042, 051, 053, 074, 083, 084, 085, 086, 088  
Total estimated time: 116 min (11 tasks)

### E1.F1.T1 [Backend] Schema additions: lane enum, the four logs, role `auto`, `generated_at`/`imported`, `skipped` keys, `D-NN@repo`; project `gates`/`judges`/`lanes`/`checks`/`branch_flow.mode`/`trailer_guard`/`tests`/`security`

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/spec.schema.json`, `plugins/karvey/schemas/project.schema.json` (§2.1, §2.2); `plugins/karvey/tests/unit/test_schema_w2.py` (NEW)  
**Requirements:** REQ-W2-019, REQ-W2-074  
**Tests added:** `test_schema_w2.py`: `D-12@ops` valid, `D12` refused with the accepted patterns; unknown lane named with the six valid ones; `deploys[n].env` missing named; `judge_runs` record without `model` reported; role `auto` accepted outside `approvals.prod`; every keyword inside the `schema_lite` subset  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_schema_w2.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_schemas.py' -v` pass

### E1.F1.T2 [Backend] Check-mode registry `check-modes.json` + `karvey_lib/modes.py` (`resolve`, `record_hit` → `changes/{id}/checks.jsonl`) — _Depends: E1.F1.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/check-modes.json` (NEW, the nine rows of §1.5); `plugins/karvey/scripts/karvey_lib/modes.py` (NEW); `plugins/karvey/tests/unit/test_modes.py` (NEW)  
**Requirements:** REQ-W2-083, REQ-W2-084, REQ-W2-085, REQ-W2-010  
**Tests added:** `test_modes.py`: no 3.13 default is `blocking`; 4.0 differs only for `schema.strict`, `gates.merged`, `release.manifest`; a project override stricter is taken, laxer than 4.0 warns naming the check; `record_hit` appends one JSON line with `check, at, mode, would_refuse, detail, finding`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_modes.py' -v` passes

### E1.F1.T3 [Backend] State tool: `generated_at`, `outcome` command (`changes_requested`, `--kind plan-exception`, `no reason given`), `approve` appends `gate_outcomes`, `--role auto` (refused on prod) — _Depends: E1.F1.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`cmd_generated`, `cmd_approve`, new `cmd_outcome`, `ROLES`); `plugins/karvey/tests/unit/test_state_outcomes.py` (NEW)  
**Requirements:** REQ-W2-001, REQ-W2-038, REQ-W2-040, REQ-W2-042  
**Tests added:** `test_state_outcomes.py`: requested-changes at 10:40 and approve at 11:30 → two entries, wait computable from `generated_at`; outcome without role or ref → exit 3 and `spec.json` byte-identical; `-y` path → `role: auto`; `approve prod --role auto` → `production approval is never automatic`; empty reason → `no reason given`; `generated_at` never overwritten  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_outcomes.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_approve.py' -v` pass

### E1.F1.T4 [Backend] State tool: `deploy-record`, `approvals.deploy` legacy warning, `deploying.approval → null`, `advance deployed --attested --ref D-NN --pipeline-run URL` — _Depends: E1.F1.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (new `cmd_deploy_record`, `cmd_advance`); `plugins/karvey/schemas/state-machine.json` (`deploying.approval: null`, precondition text); `plugins/karvey/skills/karvey/rules/state-machine.md` (regenerated block); `plugins/karvey/tests/unit/test_state_deploys.py` (NEW)  
**Requirements:** REQ-W2-002, REQ-W2-051, REQ-W2-053  
**Tests added:** `test_state_deploys.py`: prod deploy `pass` → `deploys` gains `{env, version, at, verification, rollback: null}`; entry without env refused; new change never writes `approvals.deploy`; legacy key → warning naming the migration; no ledger + `--attested` with D-NN and URL → `attested: true`; missing either → exit 3 naming both evidences; `--attested` while a ledger exists → refused  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_deploys.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_machine_data.py' -v` pass

### E1.F1.T5 [Backend] State tool: `next` prints each blocker once (F-26) — _Depends: E1.F1.T4_

**Estimate:** 5 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`compute_next`, `cmd_next`); `plugins/karvey/tests/unit/test_state_next.py`  
**Requirements:** REQ-W2-074  
**Tests added:** `test_state_next.py`: a change whose current phase is also a precondition lists `architecture not approved or skipped` once (reproduces the duplicate seen on this change today)  
**Done when:** `python3 plugins/karvey/scripts/karvey-state.py next wave2-structural | grep -c 'blocker:'` prints 1 and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_next.py' -v` passes

### E1.F1.T6 [Backend] `karvey_lib/metrics.py`: one pure function per metric returning `(value|None, reasons)`, per lane and total — _Depends: E1.F1.T1_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/metrics.py` (NEW); `plugins/karvey/tests/unit/fixtures/metrics/` (NEW: three archived changes + one legacy date-only change, anonymised); `plugins/karvey/tests/unit/test_metrics.py` (NEW)  
**Requirements:** REQ-W2-003, REQ-W2-004  
**Tests added:** `test_metrics.py`: every §1.6 metric on the fixtures, per lane and total; legacy change → `n/a — approvals without time ({id})` and excluded only from that metric; no metric returns 0 for missing data; auto approvals counted apart  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_metrics.py' -v` passes

### E1.F1.T7 [Backend] `karvey-context.py --metrics [--from --to --as-of --lane --json]`: read-only, byte-identical, table + JSON — _Depends: E1.F1.T6, E1.F1.T4_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (new builder, parser flags); `plugins/karvey/tests/unit/test_metrics.py` (CLI section)  
**Requirements:** REQ-W2-003, REQ-W2-005  
**Tests added:** run twice with the same period → identical JSON bytes; `git status --porcelain` empty after the run; empty period → every metric `n/a — no archived change in period`; JSON has sorted keys, no wall clock, no absolute path  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_metrics.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context.py' -v` pass

### E1.F1.T8 [Backend] `--readiness`: measured changes (A-06), would-refuse / confirmed per check from `checks.jsonl`, `schema.strict` computed on the fly, `ready for 4.0: N of 4` — _Depends: E1.F1.T7, E1.F1.T2_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-context.py`; `plugins/karvey/tests/unit/test_metrics.py` (readiness section)  
**Requirements:** REQ-W2-010, REQ-W2-086  
**Tests added:** five measured fixture changes → `5 measured` and a count per check; a check without hits → `no data`, not omitted; two measured → `not ready: 2 of 4`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_metrics.py' -v` passes

### E1.F1.T9 [Backend] Baseline of this repo + L-48 (baseline before any Wave 2 default is set here) — _Depends: E1.F1.T7_

**Estimate:** 8 min  
**Files:** `docs/spec/retros/baseline-{date}.json` (NEW, from `karvey-context.py --metrics --from 2026-09-01 --to {date} --as-of {date} --json`); `plugins/karvey/scripts/lint-plugin.py` (L-48); `plugins/karvey/tests/unit/test_lint_plugin.py` (L-48 mutation)  
**Requirements:** REQ-W2-006, REQ-W2-088  
**Tests added:** L-48 mutation: `project.json` with `gates: merged` and no baseline file → error; baseline dated after the first commit that set it → error  
**Done when:** `ls docs/spec/retros/baseline-*.json` lists one file, re-running the same command gives the same bytes (`cmp`), `python3 plugins/karvey/scripts/lint-plugin.py --only L-48` exits 0

### E1.F1.T10 [Backend] `karvey-retro` on the method's artifacts: metrics, findings by type and phase, estimate accuracy, judge cost, `retro-{date}.md`, actions as `process` BL-NN with owner, follow-up of previous actions, `--per-person` optional — _Depends: E1.F1.T7_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/skills/karvey-retro/SKILL.md`; `plugins/karvey/tests/manual/retro-from-metrics.md` (NEW)  
**Requirements:** REQ-W2-008, REQ-W2-009  
**Tests added:** manual script `retro-from-metrics.md` (a previous retro with two actions, one done; an action without owner is asked for, not written)  
**Done when:** `grep -c 'karvey-context.py --metrics' plugins/karvey/skills/karvey-retro/SKILL.md` ≥ 1, `grep -n 'Commits per author' plugins/karvey/skills/karvey-retro/SKILL.md` shows it only under `--per-person`, and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F1.T11 [Backend] Tracker `log_time` column per tool (`none` → actual columns) + impl text + L-50 (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/skills/karvey/rules/management-adapters.md`; `plugins/karvey/skills/karvey-impl/SKILL.md`; `plugins/karvey/scripts/lint-plugin.py` (L-50); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-W2-007  
**Tests added:** L-50 mutation: a tool row without a `log_time` cell → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-50` exits 0 and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes


## Feature E1.F2: Lanes

Architecture §1.3, §1.4 (lane rows), §2.1.  
Requirements covered: 011, 012, 013, 014, 015, 016, 017, 018, 019, 020, 021, 031, 040  
Total estimated time: 94 min (9 tasks)

### E1.F2.T1 [Backend] `schemas/lanes.json` (six lanes, §1.3 table) + `karvey_lib/lanes.py` (`load`, `phase_rule`, `lane_of` with the `type`/legacy fallback, per-lane judge counts) — _Depends: E1.F1.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/lanes.json` (NEW); `plugins/karvey/scripts/karvey_lib/lanes.py` (NEW); `plugins/karvey/tests/unit/test_lanes.py` (NEW)  
**Requirements:** REQ-W2-011, REQ-W2-019, REQ-W2-031  
**Tests added:** `test_lanes.py`: every lane lists every approvable phase; `init` never skipped; no `lane` + `type: ops` → `ops`; neither → `legacy` (3.12 pipeline); judge counts 0/2/3; override −1 refused  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lanes.py' -v` passes

### E1.F2.T2 [Backend] `karvey_lib/gitlog.py` (argv allow-list) + `lanes.admit_patch` (D-29 answers) + `lanes.measure_diff` — _Depends: E1.F2.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/gitlog.py` (NEW: `diff_names`, `log_trailers`, `grep_refs`, allow-list); `plugins/karvey/scripts/karvey_lib/lanes.py`; `plugins/karvey/tests/unit/test_lanes.py`  
**Requirements:** REQ-W2-012, REQ-W2-013, REQ-W2-017  
**Tests added:** 2 code files, Tier 2, no schema → admitted; + a migration file → `patch: schema change — use standard`; unknown answer → `standard` with the reason; on a temp repo a 5-file diff → `lane exceeded: 5 > 3 code files`; `gitlog` refuses a sub-command outside the list; `test_no_shell_true.py` still passes  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lanes.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_no_shell_true.py' -v` pass

### E1.F2.T3 [Backend] State tool: lane-aware `next`/`advance` (lane-`s` passed through and written `skipped: lane:{lane}`; manual `skip` unchanged) — _Depends: E1.F2.T1, E1.F1.T5_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`next_phase_of`, `gate_phases_before`, `cmd_advance`, `semantic_spec`); `plugins/karvey/tests/unit/test_state_lane.py` (NEW)  
**Requirements:** REQ-W2-015, REQ-W2-019, REQ-W2-021  
**Tests added:** `standard` requirements approved → `next` = architecture, `skipped.mockup = lane:standard`; `feature-ui` without mockup → architecture refused; `lane:` reason not matching `spec.json:lane` → validation error; no lane → 3.12 behaviour + one warning  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_lane.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_transitions.py' -v` pass

### E1.F2.T4 [Backend] State tool: `lane set|raise|lower`, `lane_history`, `lane-evidence`, hotfix preconditions — _Depends: E1.F2.T3, E1.F2.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (new `cmd_lane`, `cmd_lane_evidence`, `compute_next` hotfix rule); `plugins/karvey/tests/unit/test_state_lane.py`  
**Requirements:** REQ-W2-014, REQ-W2-016, REQ-W2-018  
**Tests added:** raise `patch → standard` → requirements pending, `lane_history` entry; `lower` without marker → exit 3; manual skips survive a raise; hotfix with `bug_id` + `regression_test` → impl without `tasks.approved`; hotfix without them → refused naming both  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_lane.py' -v` passes

### E1.F2.T5 [Backend] `rules/lanes.md` (generated table between markers) + `rules/multi-agent.md` §6–§7 pointer + L-40 — _Depends: E1.F2.T1_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/skills/karvey/rules/lanes.md` (NEW); `plugins/karvey/skills/karvey/rules/multi-agent.md`; `plugins/karvey/scripts/lint-plugin.py` (L-40); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-W2-011, REQ-W2-021  
**Tests added:** L-40 mutations: hand-edited table → error; lane missing a phase → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-40` exits 0

### E1.F2.T6 [Backend] Init lane questions → `lane set`; QA / QA-lite lane check (`measure_diff` + finding + `lane.diff` hit) — _Depends: E1.F2.T4, E1.F1.T2_

**Estimate:** 10 min  
**Files:** `plugins/karvey/skills/karvey-init/SKILL.md`; `plugins/karvey/skills/karvey-qa/SKILL.md`  
**Requirements:** REQ-W2-012, REQ-W2-017  
**Tests added:** text checked by L-06 (state writes only through the tool) and L-14 (allowed tools)  
**Done when:** `grep -n 'karvey-state.py" lane' plugins/karvey/skills/karvey-init/SKILL.md` and `grep -n 'measure-diff\|lane check' plugins/karvey/skills/karvey-qa/SKILL.md` match, `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F2.T7 [Backend] Dashboard: `lane` column, `skipped (lane)`, `auto` approvals apart — _Depends: E1.F2.T3, E1.F1.T7_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (`overview`, `approval_row`); `plugins/karvey/tests/unit/test_context_gate.py` (NEW)  
**Requirements:** REQ-W2-021, REQ-W2-040  
**Tests added:** `standard` change → `lane standard`, mockup `skipped (lane)`, never listed pending or awaiting approval  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_gate.py' -v` passes

### E1.F2.T8 [Backend] `global-instructions.diff` for the `patch` lane (one bullet, neutral header, A-11) (P)

**Estimate:** 5 min  
**Files:** `docs/spec/changes/wave2-structural/global-instructions.diff` (NEW)  
**Requirements:** REQ-W2-020  
**Tests added:** none (a delivered file); protect-paths tables already cover writes outside the repo  
**Done when:** `git apply --check` is not run against any personal file; `grep -c '^[-+][^-+]' docs/spec/changes/wave2-structural/global-instructions.diff` ≥ 2 and `grep -ciE 'home/|@' docs/spec/changes/wave2-structural/global-instructions.diff` = 0

### E1.F2.T9 [Test] Integration `test_patch_lane_flow.py` (AC-2) — _Depends: E1.F2.T4, E1.F5.T3_

**Estimate:** 10 min  
**Files:** `plugins/karvey/tests/unit/test_patch_lane_flow.py` (NEW)  
**Requirements:** REQ-W2-013, REQ-W2-014  
**Tests added:** temp repo: patch change with 2 files → lane admitted, triplet recorded, release gate `lane_triplet: pass`, one human gate; same change + migration → refused at `lane set`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_patch_lane_flow.py' -v` passes


## Feature E1.F3: Advisory judges

Architecture §1.7, §2.1 (`judge_runs`), §3 S-1, S-2.  
Requirements covered: 022, 023, 024, 025, 026, 027, 028, 029, 030, 031, 032, 033  
Total estimated time: 72 min (7 tasks)

### E1.F3.T1 [Backend] `rules/judges.md` (prompt template, output contract, Read/Grep/Glob only) + rubrics `rules/judges/{requirements,architecture,qa}.md` + L-51 (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/skills/karvey/rules/judges.md` (NEW); `plugins/karvey/skills/karvey/rules/judges/requirements.md`, `architecture.md`, `qa.md` (NEW); `plugins/karvey/scripts/lint-plugin.py` (L-51); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-W2-023, REQ-W2-024, REQ-W2-032  
**Tests added:** L-51 mutations: a rubric missing a default lens section → error; a template that allows Edit → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-51` exits 0

### E1.F3.T2 [Backend] `karvey_lib/judges.py` input builder + `karvey-judges.py inputs` (closed list, per-lane count, `dropped:` lines, `disabled by project setting`, `none for lane patch`) — _Depends: E1.F3.T1, E1.F2.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/judges.py` (NEW); `plugins/karvey/scripts/karvey-judges.py` (NEW); `plugins/karvey/tests/unit/test_judges.py` (NEW)  
**Requirements:** REQ-W2-022, REQ-W2-023, REQ-W2-031  
**Tests added:** architecture judge inputs = `requirements.md`, `architecture.md`, goal, rubric; a transcript argument is dropped and logged; `patch` → 0 lenses; qa always includes `fiscal`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_judges.py' -v` passes

### E1.F3.T3 [Backend] `karvey-judges.py collect`: schema check, citation resolver, sanitiser (cap 300, escape, drop patches), measured/estimated cost, `budget` ignored, append `findings.md` rows — _Depends: E1.F3.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/judges.py`; `plugins/karvey/scripts/karvey-judges.py`; `plugins/karvey/scripts/karvey_lib/defaults.json` (`judges` defaults, `judge_price_table` marked estimate-only); `plugins/karvey/tests/unit/test_judges.py`  
**Requirements:** REQ-W2-025, REQ-W2-026, REQ-W2-029, REQ-W2-030  
**Tests added:** cite past EOF → discarded, `1 discarded (no citation)`; invalid JSON → `not run (invalid output)`; `|` and newlines escaped; code block stripped; no usage → `estimated: true`; `judges.budget` → `ignored (measure only, D-30)`; two rows appended with origin `judge:methods`, status `open`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_judges.py' -v` passes

### E1.F3.T4 [Backend] State tool: `judge-run` append + judge `blocking` refusal in `approve` — _Depends: E1.F3.T3, E1.F2.T4, E1.F1.T2_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (new `cmd_judge_run`, `cmd_approve`); `plugins/karvey/tests/unit/test_state_judges.py` (NEW)  
**Requirements:** REQ-W2-028, REQ-W2-029, REQ-W2-030  
**Tests added:** advisory + open High → approval recorded; blocking + open Critical of this phase → exit 3 naming the finding; record without `model` → refused; per-change total computable  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_judges.py' -v` passes

### E1.F3.T5 [Backend] Skill `karvey-judges` + calls in `karvey-requirements`, `karvey-architecture`, `karvey-qa` (fiscal before `approve qa`) + README/`plugin.json` counts (L-11) — _Depends: E1.F3.T4_

**Estimate:** 10 min  
**Files:** `plugins/karvey/skills/karvey-judges/SKILL.md` (NEW); `plugins/karvey/skills/karvey-{requirements,architecture,qa}/SKILL.md`; `README.md`, `plugins/karvey/README.md`, `plugins/karvey/.claude-plugin/plugin.json` (counts only)  
**Requirements:** REQ-W2-022, REQ-W2-027, REQ-W2-032  
**Tests added:** L-01, L-02, L-11, L-14 on the new skill  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F3.T6 [Backend] Iterate: `accepted:{type} {ref}` / `rejected: {reason}` for judge rows; convergence lists `unresolved (no routing or reason)` — _Depends: E1.F3.T3_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/skills/karvey-iterate/SKILL.md`; `plugins/karvey/scripts/karvey-context.py` (`convergence`); `plugins/karvey/tests/unit/test_judges.py` (convergence case)  
**Requirements:** REQ-W2-033  
**Tests added:** a closed judge row with neither form → listed unresolved; two routed + one rejected → lens acceptance 2/3 in `--metrics`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_judges.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context.py' -v` pass

### E1.F3.T7 [Test] Manual script `judges-gate.md` (real subagents, verdicts at the gate, intra-model declared) — _Depends: E1.F3.T5_ (P)

**Estimate:** 5 min  
**Files:** `plugins/karvey/tests/manual/judges-gate.md` (NEW)  
**Requirements:** REQ-W2-022, REQ-W2-027, REQ-W2-029  
**Tests added:** the script itself (run headless under D-19 in E1.F13.T6)  
**Done when:** `test -f plugins/karvey/tests/manual/judges-gate.md` and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0


## Feature E1.F4: Three merged human gates

Architecture §1.8, §1.4 (`approve-gate`), §1.6 (gate summary).  
Requirements covered: 027, 034, 035, 036, 037, 038, 039, 040, 041, 042, 080  
Total estimated time: 72 min (7 tasks)

### E1.F4.T1 [Backend] `state-machine.json:gate` per phase + `approve-gate what|how|release` + imported phases need the human marker (`generated --imported`) — _Depends: E1.F3.T4_

**Estimate:** 15 min  
**Files:** `plugins/karvey/schemas/state-machine.json`; `plugins/karvey/scripts/karvey-state.py` (new `cmd_approve_gate`, `cmd_generated --imported`, `cmd_approve`); `plugins/karvey/tests/unit/test_state_gates.py` (NEW)  
**Requirements:** REQ-W2-034, REQ-W2-036, REQ-W2-080  
**Tests added:** *how* with infra skipped → `architecture` and `tasks` hold the same record, one outcome entry; `tasks.md` not generated → refused naming it; *release* without prod marker → `qa` only, prod pending; imported phase without marker → exit 3  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_gates.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_machine_data.py' -v` pass

### E1.F4.T2 [Backend] Gate mode resolution (`project.json:gates` via `gates.merged`), `--granular-gates`, invalid value refused — _Depends: E1.F4.T1, E1.F1.T2_

**Estimate:** 6 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`semantic_project`, `gate_mode`); `plugins/karvey/tests/unit/test_state_gates.py`  
**Requirements:** REQ-W2-039  
**Tests added:** 3.13 without setting → granular; `gates: fused` → refused; 4.0 default read from the registry → merged  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_gates.py' -v` passes

### E1.F4.T3 [Backend] `karvey-context.py --section gate --change --gate`: one-page summary (phases, lane, judges verdicts / disagreement / not run, decisions, risks, deviations, cost, `[human]` tasks, uncovered REQs, contract gaps, manifest) — _Depends: E1.F4.T1, E1.F3.T4, E1.F2.T7_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (new `gate` builder); `plugins/karvey/tests/unit/test_context_gate.py`  
**Requirements:** REQ-W2-027, REQ-W2-037  
**Tests added:** `pass` + `concerns` → disagreement stated; missing judge → `judge {lens}: not run ({reason})`; a `deviations.md` entry absent from the summary → omission reported; missing source → `missing: {path}`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_gate.py' -v` passes

### E1.F4.T4 [Backend] `rules/gates.md` (the one closing block, granular / merged, `-y` = `role: auto`, plan exceptions) + the 13 phase-skill closings + `rules/phase-close.md:45` — _Depends: E1.F4.T2, E1.F3.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/skills/karvey/rules/gates.md` (NEW); the 13 `SKILL.md` files listed by `grep -rln 'Shall we advance' plugins/karvey/skills`; `plugins/karvey/skills/karvey/rules/phase-close.md`  
**Requirements:** REQ-W2-034, REQ-W2-035, REQ-W2-038, REQ-W2-040, REQ-W2-042  
**Tests added:** covered by L-41 / L-52 in E1.F4.T5  
**Done when:** `grep -rln 'Shall we advance' plugins/karvey/skills | wc -l` prints 0 and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F4.T5 [Backend] L-41 (no second gate question; closings cite `rules/gates.md`) + L-52 (`-y` = auto, never prod) — _Depends: E1.F4.T4_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-41, L-52); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-W2-034, REQ-W2-035, REQ-W2-040  
**Tests added:** mutations: a closing `Shall we advance` after an approval question → error; `-y` described as approving prod → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-41,L-52` exits 0

### E1.F4.T6 [Backend] Grill: batches ≤ 4, recommended first, stack inferred from lockfiles / CI and only confirmed + manual script (P)

**Estimate:** 6 min  
**Files:** `plugins/karvey/skills/karvey-grill/SKILL.md`; `plugins/karvey/tests/manual/grill-batches.md` (NEW)  
**Requirements:** REQ-W2-041  
**Tests added:** manual script `grill-batches.md`  
**Done when:** `grep -n 'at most four' plugins/karvey/skills/karvey-grill/SKILL.md` matches and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F4.T7 [Test] Manual script `merged-gates-three-questions.md` (AC-4: count the gate questions of a real `standard` run) — _Depends: E1.F4.T4_ (P)

**Estimate:** 5 min  
**Files:** `plugins/karvey/tests/manual/merged-gates-three-questions.md` (NEW)  
**Requirements:** REQ-W2-034, REQ-W2-035, REQ-W2-038  
**Tests added:** the script itself (run in E1.F13.T6)  
**Done when:** `test -f plugins/karvey/tests/manual/merged-gates-three-questions.md`


## Feature E1.F5: Release per change

Architecture §1.9, §1.10, §1.11, §3 S-4, S-5.  
Requirements covered: 014, 043, 044, 045, 046, 047, 048, 049, 050, 052, 053, 054, 069, 076, 088  
Total estimated time: 104 min (9 tasks)

### E1.F5.T1 [Backend] `karvey_lib/manifest.py`: trailer parse (strict pattern), merge-commit mapping, path-only mapping (A-12) — _Depends: E1.F2.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/manifest.py` (NEW); `plugins/karvey/tests/unit/test_manifest.py` (NEW)  
**Requirements:** REQ-W2-043, REQ-W2-045, REQ-W2-088  
**Tests added:** temp repo: trailer → mapped; none → unmapped with reason; malformed / two values → unmapped; merge commit through its parents; commit touching only `docs/spec/changes/{id}/**` → `mapped_by: path`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_manifest.py' -v` passes

### E1.F5.T2 [Backend] `karvey-release-gate.py manifest`: changes with version / lane / QA state, `unmapped`, verdict per mode, hits — _Depends: E1.F5.T1, E1.F1.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-release-gate.py` (NEW); `plugins/karvey/tests/unit/test_release_gate.py` (NEW)  
**Requirements:** REQ-W2-045, REQ-W2-046  
**Tests added:** two changes → both listed with commits; unmapped → `warn` in warn mode, `fail` in blocking; every change QA-approved or lane-skipped → `pass`; non-pass → one `checks.jsonl` line per change  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_release_gate.py' -v` passes

### E1.F5.T3 [Backend] `karvey-release-gate.py check` (qa_gate, tests, changelog, version_match, lane_triplet, manifest, spec_merged, pr_body) + `release-branch` (read-only plan) — _Depends: E1.F5.T2, E1.F2.T4, E1.F6.T1, E1.F7.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-release-gate.py`; `plugins/karvey/tests/unit/test_release_gate.py`  
**Requirements:** REQ-W2-014, REQ-W2-047, REQ-W2-050, REQ-W2-069  
**Tests added:** all items pass → exit 0 `verdict: pass`; no `[Unreleased]` line → exit 1 naming `changelog`; PR body lists one of two changes → `pr_body: fail`; release-branch lists the approved commits in order  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_release_gate.py' -v` passes

### E1.F5.T4 [Backend] Trailer guard (`enforcement.trailer_guard: off|warn|blocking`, reviewed line, `-m`/`-F`/`--trailer`, fail open) + table `trailer.json` + hooks README anchors — _Depends: E1.F1.T2_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/guards.py` (`trailer`, `trailer_enabled`); `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (REGISTRY); `plugins/karvey/tests/hooks/tables/trailer.json` (NEW); `plugins/karvey/hooks/README.md`  
**Requirements:** REQ-W2-044  
**Tests added:** `trailer.json`: off silent; warn + missing → warning line; blocking + missing → exit 2 with the trailer to add; present → silent; editor commit → silent; branch of no active change → silent; `-F` file  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only trailer` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-16` exits 0

### E1.F5.T5 [Backend] Prod gate: manifest verdict after the Wave 1 allow (warn → allow + line; blocking → block; not computable), every manifest change through `check_prod`; `approve prod --manifest` — _Depends: E1.F5.T2, E1.F4.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/guards.py` (`_evaluate_candidate`); `plugins/karvey/scripts/karvey-state.py` (`cmd_approve --manifest`); `plugins/karvey/tests/hooks/tables/prod-gate.json` (new cases)  
**Requirements:** REQ-W2-046, REQ-W2-047  
**Tests added:** warn: allow + `MANIFEST WARNING`; warn + not computable → allow + `not evaluated`; blocking: unmapped → block, change without QA → block naming it, not computable → block; two-change manifest with both prod approvals → allow; one marker consumed once after both ledger writes  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only prod-gate` passes

### E1.F5.T6 [Backend] Deploy flow text: 2.4-bis spec merge on the change branch, 2.5 integration by PR, 2.8-bis manifest + release gate, prod OK in PR body at deploy → D-NN at archive, attested fallback, `release/*` offer — _Depends: E1.F5.T3_

**Estimate:** 15 min  
**Files:** `plugins/karvey/skills/karvey-deploy/SKILL.md`; `plugins/karvey/skills/karvey/rules/deploy-workflow.md`  
**Requirements:** REQ-W2-045, REQ-W2-048, REQ-W2-050, REQ-W2-052, REQ-W2-053, REQ-W2-054  
**Tests added:** covered by L-43 / L-53 in E1.F5.T8 and L-27 (existing)  
**Done when:** `grep -n 'git merge "feature' plugins/karvey/skills/karvey-deploy/SKILL.md plugins/karvey/skills/karvey/rules/deploy-workflow.md` prints nothing and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F5.T7 [Backend] `branch_flow.mode` derived (trunk when integration = production), contradiction reported, trunk recommended by `karvey-init --settings` — _Depends: E1.F1.T1_ (P)

**Estimate:** 6 min  
**Files:** `plugins/karvey/scripts/karvey_lib/project.py` (`branch_flow`); `plugins/karvey/scripts/karvey-state.py` (`semantic_project`); `plugins/karvey/skills/karvey-init/SKILL.md`; `plugins/karvey/tests/unit/test_project.py`  
**Requirements:** REQ-W2-049  
**Tests added:** `main`/`main` → `trunk`; `mode: trunk` with `dev`/`master` → contradiction reported  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_project.py' -v` passes

### E1.F5.T8 [Backend] L-42 (commit examples carry the trailer), L-43 (no local merge + push into integration), L-53 (deploy order and naming) — _Depends: E1.F5.T6, E1.F10.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py`; `plugins/karvey/tests/unit/test_lint_plugin.py`; the skill texts with commit examples found by L-42  
**Requirements:** REQ-W2-043, REQ-W2-048, REQ-W2-052, REQ-W2-054, REQ-W2-076  
**Tests added:** mutations: a `git commit -m` example without trailer → error; `git merge` + `git push "$I"` → error; PR before spec merge → error; `canary` outside traffic splitting → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-42,L-43,L-53` exits 0

### E1.F5.T9 [Backend] Inherited base commits: map `390e6cb`, `02b460b`, `62ffc6d`, `38f42bf` (wave1-hardening decision commits on the base branch) to `wave1-hardening` — no rewrite — _Depends: E1.F5.T2_

**Estimate:** 5 min  
**Files:** `docs/spec/changes/wave2-structural/PLAN.md` (note under History); nothing else  
**Requirements:** REQ-W2-088  
**Tests added:** none: `manifest` run against the base after `wave1-hardening` merges  
**Done when:** after `wave1-hardening` is on `main`: `python3 plugins/karvey/scripts/karvey-release-gate.py manifest --base origin/main --json` shows `unmapped: []`; before that, the four shas are listed and the PLAN note names their change

- They are spec-only commits of `wave1-hardening` inherited from the base branch, and they leave this change's range once that change is merged to production. If they are still in the range at the release gate, the release gate is run with `--base` at the merge base and the mapping note is quoted in the PR body. No history is rewritten.


## Feature E1.F6: Living spec merged before production

Architecture §1.11 (`--check`), §1.6 (dashboard line).  
Requirements covered: 054, 055, 056  
Total estimated time: 26 min (3 tasks)

### E1.F6.T1 [Backend] `karvey-spec-merge.py --check` (merged | unmerged with ids | conflict), read-only (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-spec-merge.py`; `plugins/karvey/tests/unit/test_spec_merge_check.py` (NEW)  
**Requirements:** REQ-W2-054, REQ-W2-055  
**Tests added:** merged delta → `merged`, nothing written; missing id → `unmerged` naming it; different text → `conflict`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_spec_merge_check.py' -v` passes

### E1.F6.T2 [Backend] Archive: `--check` first, move and close only, merge on `chore/archive-{id}` only when unmerged — _Depends: E1.F6.T1_

**Estimate:** 6 min  
**Files:** `plugins/karvey/skills/karvey-archive/SKILL.md`  
**Requirements:** REQ-W2-055  
**Tests added:** L-27 (existing) on the archive branch rule  
**Done when:** `grep -n 'spec-merge.py.*--check' plugins/karvey/skills/karvey-archive/SKILL.md` matches and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F6.T3 [Backend] L-49 (deployed with unmerged delta → error) + dashboard `deployed N d, not archived` (`deployed_stall_days: 7`) — _Depends: E1.F6.T1, E1.F2.T7_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-49); `plugins/karvey/scripts/karvey-context.py`; `plugins/karvey/scripts/karvey_lib/defaults.json`; `plugins/karvey/tests/unit/test_context_gate.py`; `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-W2-056  
**Tests added:** deployed 9 days ago → `deployed 9 d, not archived`; L-49 mutation → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-49` exits 0 and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_gate.py' -v` passes


## Feature E1.F7: Test-first and traceability

Architecture §1.12.  
Requirements covered: 057, 058, 059, 060, 061, 062, 063  
Total estimated time: 39 min (3 tasks)

### E1.F7.T1 [Backend] `karvey-trace.py`: parse requirements, tasks (test task precedes impl task, `manual:`), trailer commits, tests by globs and `@req`/`test_REQ_*` — _Depends: E1.F5.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-trace.py` (NEW); `plugins/karvey/tests/unit/test_trace.py` (NEW)  
**Requirements:** REQ-W2-057, REQ-W2-058, REQ-W2-060  
**Tests added:** requirement with no test task and no `manual` → `uncovered`; test tagged `@req REQ-W2-013` → mapped; new test without reference → `unmapped test`; requirement with no commit → `no commit`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_trace.py' -v` passes

### E1.F7.T2 [Backend] `karvey-trace.py --write` (`traceability.md`) and `--check` (coverage gate, `coverage.requirements` mode, hits); last result from JUnit / `evidence.jsonl` — _Depends: E1.F7.T1, E1.F1.T2, E1.F9.T4_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-trace.py`; `plugins/karvey/tests/unit/test_trace.py`  
**Requirements:** REQ-W2-060, REQ-W2-062  
**Tests added:** every requirement covered → `N/N`; two uncovered → listed, warn, two hits; result `not run` without evidence  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_trace.py' -v` passes

### E1.F7.T3 [Backend] Tasks / test / QA text: test task per requirement, coverage plan read and `planned, not executed`, evidence under `changes/{id}/`, QA runs or cites the CI run of the reviewed commit + L-44 — _Depends: E1.F7.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/skills/karvey-tasks/SKILL.md`; `plugins/karvey/skills/karvey-test/SKILL.md` (lines 38, 103, 167, 190); `plugins/karvey/skills/karvey-deploy/SKILL.md:32`; `plugins/karvey/skills/karvey-qa/SKILL.md`; `plugins/karvey/scripts/lint-plugin.py` (L-44); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-W2-057, REQ-W2-059, REQ-W2-061, REQ-W2-063  
**Tests added:** L-44 mutation: `docs/test_evidence.md` → error  
**Done when:** `grep -rn 'docs/test_evidence.md\|docs/test_plan.md' plugins/karvey/skills` prints nothing and `python3 plugins/karvey/scripts/lint-plugin.py --only L-44` exits 0


## Feature E1.F8: Deterministic security tools

Architecture §1.13, §3 S-3.  
Requirements covered: 064, 065, 066, 067, 068  
Total estimated time: 30 min (3 tasks)

### E1.F8.T1 [Backend] `security_tools.json` (fixed argv templates per category) + `karvey-security-scan.py run` (applies?, first tool, timeout, cap, evidence wrapper, `not evaluated` / `not applicable`) — _Depends: E1.F9.T4_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/security_tools.json` (NEW); `plugins/karvey/scripts/karvey-security-scan.py` (NEW); `plugins/karvey/tests/unit/stubs/security/` (NEW: stub tools); `plugins/karvey/tests/unit/test_security_scan.py` (NEW)  
**Requirements:** REQ-W2-064, REQ-W2-065, REQ-W2-067  
**Tests added:** stub scanner on PATH → command, version, `0 findings`; stub exits with an error → `not evaluated (tool error)`; none on PATH → `not evaluated (no tool)`; no IaC files → `not applicable`; a `project.json` value with `;` → refused; no catalogue command is replaceable by the project  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_security_scan.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_no_shell_true.py' -v` pass

### E1.F8.T2 [Backend] Suppressions (`validate-suppressions`), QA Dimension 1 cites tool lines and reviews what tools miss, infra `security-scan` CI stage — _Depends: E1.F8.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-security-scan.py`; `plugins/karvey/skills/karvey-qa/SKILL.md` (Dimension 1); `plugins/karvey/skills/karvey-infra/SKILL.md`; `plugins/karvey/tests/unit/test_security_scan.py`  
**Requirements:** REQ-W2-066, REQ-W2-068  
**Tests added:** suppression without reason or scope → reported  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_security_scan.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F8.T3 [Test] Manual script `security-tools-present.md` (real tools installed) — _Depends: E1.F8.T2_ (P)

**Estimate:** 5 min  
**Files:** `plugins/karvey/tests/manual/security-tools-present.md` (NEW)  
**Requirements:** REQ-W2-064, REQ-W2-068  
**Tests added:** the script itself  
**Done when:** `test -f plugins/karvey/tests/manual/security-tools-present.md`


## Feature E1.F9: Deterministic scripts: IDs, health score, evidence

Architecture §1.14.  
Requirements covered: 070, 071, 072, 073, 081  
Total estimated time: 41 min (4 tasks)

### E1.F9.T1 [Backend] `karvey-id.py next BUG|D|BL|F|Q` (lock, working tree + both decision-log shapes + `refs/remotes/*` scan, clone-local reservation, `--qualified`) + skills that mint IDs call it (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-id.py` (NEW); `plugins/karvey/tests/unit/test_id_tool.py` (NEW); the skills that mint IDs (`karvey-iterate`, `karvey-decisions`, `karvey-investigate`, `karvey-retro`, `karvey-test`)  
**Requirements:** REQ-W2-070, REQ-W2-071, REQ-W2-081  
**Tests added:** two processes at once → different numbers; lock held → exit 3, no number; BUG-12 on a remote branch only → next is 13; `--qualified` → `BUG-13@{repo}`; D-NN in `decisions/*.md` counted  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_id_tool.py' -v` passes

### E1.F9.T2 [Backend] L-45 (no bounded Epic range in any skill) + L-33 as an error for duplicate IDs created after the release — _Depends: E1.F9.T1_

**Estimate:** 6 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-45, L-33); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-W2-071  
**Tests added:** mutation: `E{1..99}` in any skill → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-45,L-33` exits 0

### E1.F9.T3 [Backend] `karvey-health-score.py` (named sub-score functions, `health_weights`, `KARVEY_TZ` fallback line) + health skill calls it (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-health-score.py` (NEW); `plugins/karvey/scripts/karvey_lib/defaults.json` (`health_weights`); `plugins/karvey/skills/karvey-health/SKILL.md`; `plugins/karvey/tests/unit/test_health_score.py` (NEW)  
**Requirements:** REQ-W2-072  
**Tests added:** same input twice → identical score; invalid `KARVEY_TZ` → `fallback zone: …` printed; missing tool's weight redistributed  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_health_score.py' -v` passes

### E1.F9.T4 [Backend] `karvey-evidence.py -- <cmd>` (argv, streamed, hashes only, own exit code, `--junit`) + `rules/verification.md` cites `evidence.jsonl` lines (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-evidence.py` (NEW); `plugins/karvey/skills/karvey/rules/verification.md`; `plugins/karvey/tests/unit/test_evidence.py` (NEW)  
**Requirements:** REQ-W2-073  
**Tests added:** one JSON line appended, exit code returned unchanged; no active change → command runs, `evidence not recorded: no active change`; no output text stored  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_evidence.py' -v` passes


## Feature E1.F10: Post-deploy verification with thresholds

Architecture §1.15, §3 S-6.  
Requirements covered: 002, 075, 076, 077, 078  
Total estimated time: 23 min (2 tasks)

### E1.F10.T1 [Backend] `karvey-postdeploy.py probe|evaluate` (contract block parse, https-only probes, no cross-host redirect, thresholds, `deploy_evidence.md`, prints `deploy-record`) — _Depends: E1.F1.T4_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-postdeploy.py` (NEW); `plugins/karvey/tests/unit/test_postdeploy.py` (NEW: local HTTP stub)  
**Requirements:** REQ-W2-002, REQ-W2-075, REQ-W2-076, REQ-W2-077  
**Tests added:** all probes inside thresholds → `pass`; error rate above → `regression`; no contract → `not-evaluated`, never `pass`; contract without rollback → reported incomplete; redirect to another host not followed  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_postdeploy.py' -v` passes

### E1.F10.T2 [Backend] Infra contract text + deploy 2.6/2.10 "post-deploy verification", regression → rollback asked, `deploy-record --rollback`, `karvey-id next BUG` + manual script — _Depends: E1.F10.T1, E1.F5.T6_

**Estimate:** 8 min  
**Files:** `plugins/karvey/skills/karvey-infra/SKILL.md`; `plugins/karvey/skills/karvey-deploy/SKILL.md`; `plugins/karvey/tests/manual/deploy-postdeploy.md` (NEW)  
**Requirements:** REQ-W2-075, REQ-W2-076, REQ-W2-078  
**Tests added:** manual script `deploy-postdeploy.md`  
**Done when:** `grep -c 'post-deploy verification' plugins/karvey/skills/karvey-deploy/SKILL.md` ≥ 2 and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0


## Feature E1.F11: Knowledge sync optional

Architecture §1.16 (L-46), §2.2.  
Requirements covered: 079  
Total estimated time: 8 min (1 tasks)

### E1.F11.T1 [Backend] Knowledge sync optional everywhere (`none` default), archive syncs only when declared + L-46 (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/skills/karvey/rules/knowledge-sync.md`; `plugins/karvey/skills/karvey-archive/SKILL.md`; `README.md`; `plugins/karvey/schemas/project.schema.json` (`x-karvey-default: none`); `plugins/karvey/scripts/lint-plugin.py` (L-46); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-W2-079  
**Tests added:** mutation: `graphify is required` in a skill → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-46,L-23` exits 0


## Feature E1.F12: Deferred Wave 1 backlog

Architecture §1.17, §6.2.  
Requirements covered: 080, 081, 082  
Total estimated time: 19 min (3 tasks)

### E1.F12.T1 [Backend] Import: `generated --imported` per artifact, gate questions in order (merged when enabled), resume at the first unapproved gate + manual script — _Depends: E1.F4.T1_

**Estimate:** 6 min  
**Files:** `plugins/karvey/skills/karvey-import/SKILL.md`; `plugins/karvey/tests/manual/import-through-gates.md` (NEW)  
**Requirements:** REQ-W2-080  
**Tests added:** manual script `import-through-gates.md`; the refusal is unit-tested in E1.F4.T1  
**Done when:** `grep -n 'generated.*--imported' plugins/karvey/skills/karvey-import/SKILL.md` matches and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F12.T2 [Backend] Decisions: one log written, per-period files read with a migration note once, duplicates reported — _Depends: E1.F9.T1_ (P)

**Estimate:** 5 min  
**Files:** `plugins/karvey/skills/karvey-decisions/SKILL.md`  
**Requirements:** REQ-W2-081  
**Tests added:** the scan of both shapes is tested in E1.F9.T1  
**Done when:** `grep -n 'decisions/\*.md' plugins/karvey/skills/karvey-decisions/SKILL.md` matches and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F12.T3 [Test] Statusline failure-line table case + hooks README anchor + L-54 (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/tests/hooks/tables/statusline.json`; `plugins/karvey/hooks/README.md`; `plugins/karvey/scripts/lint-plugin.py` (L-54); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-W2-082  
**Tests added:** `statusline.json` case `sl-fail-*` asserting the failure line; L-54 mutation: README sentence without anchor → error  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only statusline` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-54,L-16` exits 0


## Feature E1.F13: Rollout 3.13 → 4.0, dogfooding and release

Architecture §7, §6.2 (`compat.json`), §6.3.  
Requirements covered: 006, 020, 034, 036, 045, 046, 047, 051, 059, 062, 069, 083, 084, 085, 086, 087, 088  
Total estimated time: 62 min (9 tasks)

### E1.F13.T1 [Backend] `validate --fix`: lane proposal (proposed tier), `approvals.deploy` → `deploys[]` only with data, idempotent, never an approval — _Depends: E1.F4.T1, E1.F1.T4_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`fix_spec`); `plugins/karvey/tests/unit/test_state_fix.py`; `plugins/karvey/tests/fixtures/legacy/spec/` (one more fixture with `approvals.deploy`)  
**Requirements:** REQ-W2-051, REQ-W2-087  
**Tests added:** mockup + design skipped → `lane: standard` proposed with the diff; `type: ops` → `ops`; second run changes nothing; no approval created or flipped  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_fix.py' -v` passes

### E1.F13.T2 [Test] `compat.json`: the 3.12.0 fixtures replayed under 3.13 defaults — every Wave 1 allow still allows — _Depends: E1.F5.T5, E1.F13.T1, E1.F5.T4_

**Estimate:** 10 min  
**Files:** `plugins/karvey/tests/hooks/tables/compat.json` (NEW); `plugins/karvey/tests/hooks/run_tables.py` (table registered)  
**Requirements:** REQ-W2-084  
**Tests added:** one case per Wave 1 allow case of `prod-gate`, `git-flow`, `plan-gate`, `spec-write` with Wave 2 defaults active  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only compat` passes

### E1.F13.T3 [Test] Integration `test_wave2_flow.py`: init → lane → three `approve-gate` → trailer commits → `release-gate check` pass (AC-4, AC-5) — _Depends: E1.F5.T3, E1.F5.T5, E1.F4.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/tests/unit/test_wave2_flow.py` (NEW)  
**Requirements:** REQ-W2-034, REQ-W2-036, REQ-W2-045, REQ-W2-046, REQ-W2-069  
**Tests added:** the flow on a temp repo with a planted test marker; exactly three gate outcomes; manifest `pass`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_wave2_flow.py' -v` passes

### E1.F13.T4 [Backend] This repo: `validate --fix --accept-proposed` on its own changes, `branch_flow.mode: trunk`, then `gates: merged` and `judges` (after the baseline, L-48) — _Depends: E1.F1.T9, E1.F13.T1, E1.F4.T2, E1.F5.T7_

**Estimate:** 6 min  
**Files:** `docs/spec/project.json`; `docs/spec/changes/*/spec.json` (lane proposals, shown as a diff first); `docs/spec/changes/archive/*/spec.json`  
**Requirements:** REQ-W2-006, REQ-W2-088  
**Tests added:** L-18 / L-48 on the result  
**Done when:** `python3 plugins/karvey/scripts/karvey-state.py validate --all` exits 0 and `python3 plugins/karvey/scripts/lint-plugin.py --only L-18,L-48` exits 0

- The `--fix` diff is shown in the task's commit message body before writing; archived changes are touched only where the proposed tier adds `lane` (no approval is created).

### E1.F13.T5 [Backend] Hand-off of the §7.4 upgrade steps for project-upgrade's catalogue (declarations only) — _Depends: E1.F13.T1, E1.F5.T7_

**Estimate:** 8 min  
**Files:** `docs/spec/changes/wave2-structural/upgrade-steps.handoff.json` (NEW: the ten §7.4 rows in the catalogue's field shape — `id`, `since` = the Wave 2 release number placeholder, `check`, `fix`, `dry_run`, `human`, `risk`, `report_only`, plus `component` and `status: declared`); the CHANGELOG manual "Upgrade" list is written at release by E1.F13.T7  
**Requirements:** REQ-W2-083, REQ-W2-084, REQ-W2-087  
**Tests added:** a one-line shape check (below)  
**Done when:** `python3 -c "import json;d=json.load(open('docs/spec/changes/wave2-structural/upgrade-steps.handoff.json'));r={'id','since','check','fix','dry_run','human','risk'};assert len(d['steps'])==10 and all(r<=set(s) for s in d['steps']);print('ok')"` prints `ok`

- Scope stops at the declaration. Once both `project-upgrade` and this change are on `main`, the rows become catalogue entries (and `upgrade_steps.py` functions) in a follow-up under the `patch` or `standard` lane — owned by whoever takes that follow-up, recorded as a backlog item at archive. Nothing of project-upgrade's engine is implemented here.

### E1.F13.T6 [Test] Whole-repo gate: lint 0 errors, every unit and regression suite, every table, `validate --all`, `karvey-trace.py wave2-structural --write --check`, manual scripts run headless (D-19) — _Depends: every other agent task_

**Estimate:** 10 min  
**Files:** `docs/spec/changes/wave2-structural/traceability.md` (generated); `docs/spec/changes/wave2-structural/test_evidence.md`; `docs/spec/changes/wave2-structural/evidence.jsonl`  
**Requirements:** REQ-W2-059, REQ-W2-062, REQ-W2-088  
**Tests added:** none new; runs everything through `karvey-evidence.py`  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0; `python3 -m unittest discover -s plugins/karvey/tests/unit` and `-s plugins/karvey/tests/regression` pass; `python3 plugins/karvey/tests/hooks/run_tables.py` passes; `python3 plugins/karvey/scripts/karvey-trace.py wave2-structural --check` prints `88/88`

### E1.F13.T7 [Backend] Release docs: `[Unreleased]` summary (modes table, the manual Upgrade list from the hand-off, the 3.13 → 4.0 note), no version or date — _Depends: E1.F13.T6, E1.F13.T5_

**Estimate:** 6 min  
**Files:** `CHANGELOG.md` (the `[Unreleased]` block; each impl task already added its own line); `docs/spec/changes/wave2-structural/PLAN.md` (feature states)  
**Requirements:** REQ-W2-083, REQ-W2-085, REQ-W2-086  
**Tests added:** L-12, L-13, L-19 (existing) on the block  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0 and `sed -n '/## \[Unreleased\]/,/## \[/p' CHANGELOG.md | grep -c -E 'lane-infer|approvals-deploy-retire|branch-flow-mode'` ≥ 3

- The version number, the release date and the `since` values belong to `karvey-deploy` at release (architecture A-01).

### E1.F13.T8 [human] Apply the `patch`-lane bullet to the owner's global instructions — _Depends: E1.F2.T8_

**Executor:** the owner  
**Command:** read `docs/spec/changes/wave2-structural/global-instructions.diff`, then apply that one bullet by hand to your own global instructions file (the agent never writes it, D-01, D-11)  
**Verification:** `grep -c 'patch' <your global instructions file>` ≥ 1, run by you  
**Rollback:** remove the bullet you added  
**Requirements:** REQ-W2-020  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

### E1.F13.T9 [human] The prod OK for the release that ships this change (D-10) — _Depends: E1.F13.T7_

**Executor:** the owner — never delegated  
**Command:** inside `karvey-deploy`, after reading the release PR (its manifest lists every change and commit), type your own words with an approval **and** a production term, and answer the structured question that records the D-NN  
**Verification:** `python3 plugins/karvey/scripts/karvey-state.py check-prod wave2-structural --json` → `ok: true` after `approve prod`  
**Rollback:** before the merge: nothing, the marker expires; after it: a revert PR, as a new change through the method  
**Requirements:** REQ-W2-047, REQ-W2-088  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)


## Traceability matrix (REQ-W2 → tasks)

| REQ-W2 | Tasks |
|---|---|
| 001 | E1.F1.T3 |
| 002 | E1.F1.T4, E1.F10.T1 |
| 003 | E1.F1.T6, E1.F1.T7 |
| 004 | E1.F1.T6 |
| 005 | E1.F1.T7 |
| 006 | E1.F1.T9, E1.F13.T4 |
| 007 | E1.F1.T11 |
| 008 | E1.F1.T10 |
| 009 | E1.F1.T10 |
| 010 | E1.F1.T2, E1.F1.T8 |
| 011 | E1.F2.T1, E1.F2.T5 |
| 012 | E1.F2.T2, E1.F2.T6 |
| 013 | E1.F2.T2, E1.F2.T9 |
| 014 | E1.F2.T4, E1.F2.T9, E1.F5.T3 |
| 015 | E1.F2.T3 |
| 016 | E1.F2.T4 |
| 017 | E1.F2.T2, E1.F2.T6 |
| 018 | E1.F2.T4 |
| 019 | E1.F1.T1, E1.F2.T1, E1.F2.T3 |
| 020 | E1.F2.T8, E1.F13.T8 |
| 021 | E1.F2.T3, E1.F2.T5, E1.F2.T7 |
| 022 | E1.F3.T2, E1.F3.T5, E1.F3.T7 |
| 023 | E1.F3.T1, E1.F3.T2 |
| 024 | E1.F3.T1 |
| 025 | E1.F3.T3 |
| 026 | E1.F3.T3 |
| 027 | E1.F3.T5, E1.F3.T7, E1.F4.T3 |
| 028 | E1.F3.T4 |
| 029 | E1.F3.T3, E1.F3.T4, E1.F3.T7 |
| 030 | E1.F3.T3, E1.F3.T4 |
| 031 | E1.F2.T1, E1.F3.T2 |
| 032 | E1.F3.T1, E1.F3.T5 |
| 033 | E1.F3.T6 |
| 034 | E1.F4.T1, E1.F4.T4, E1.F4.T5, E1.F4.T7, E1.F13.T3 |
| 035 | E1.F4.T4, E1.F4.T5, E1.F4.T7 |
| 036 | E1.F4.T1, E1.F13.T3 |
| 037 | E1.F4.T3 |
| 038 | E1.F1.T3, E1.F4.T4, E1.F4.T7 |
| 039 | E1.F4.T2 |
| 040 | E1.F1.T3, E1.F2.T7, E1.F4.T4, E1.F4.T5 |
| 041 | E1.F4.T6 |
| 042 | E1.F1.T3, E1.F4.T4 |
| 043 | E1.F5.T1, E1.F5.T8 |
| 044 | E1.F5.T4 |
| 045 | E1.F5.T1, E1.F5.T2, E1.F5.T6, E1.F13.T3 |
| 046 | E1.F5.T2, E1.F5.T5, E1.F13.T3 |
| 047 | E1.F5.T3, E1.F5.T5, E1.F13.T9 |
| 048 | E1.F5.T6, E1.F5.T8 |
| 049 | E1.F5.T7 |
| 050 | E1.F5.T3, E1.F5.T6 |
| 051 | E1.F1.T4, E1.F13.T1 |
| 052 | E1.F5.T6, E1.F5.T8 |
| 053 | E1.F1.T4, E1.F5.T6 |
| 054 | E1.F5.T6, E1.F5.T8, E1.F6.T1 |
| 055 | E1.F6.T1, E1.F6.T2 |
| 056 | E1.F6.T3 |
| 057 | E1.F7.T1, E1.F7.T3 |
| 058 | E1.F7.T1 |
| 059 | E1.F7.T3, E1.F13.T6 |
| 060 | E1.F7.T1, E1.F7.T2 |
| 061 | E1.F7.T3 |
| 062 | E1.F7.T2, E1.F13.T6 |
| 063 | E1.F7.T3 |
| 064 | E1.F8.T1, E1.F8.T3 |
| 065 | E1.F8.T1 |
| 066 | E1.F8.T2 |
| 067 | E1.F8.T1 |
| 068 | E1.F8.T2, E1.F8.T3 |
| 069 | E1.F5.T3, E1.F13.T3 |
| 070 | E1.F9.T1 |
| 071 | E1.F9.T1, E1.F9.T2 |
| 072 | E1.F9.T3 |
| 073 | E1.F9.T4 |
| 074 | E1.F1.T1, E1.F1.T5 |
| 075 | E1.F10.T1, E1.F10.T2 |
| 076 | E1.F5.T8, E1.F10.T1, E1.F10.T2 |
| 077 | E1.F10.T1 |
| 078 | E1.F10.T2 |
| 079 | E1.F11.T1 |
| 080 | E1.F4.T1, E1.F12.T1 |
| 081 | E1.F9.T1, E1.F12.T2 |
| 082 | E1.F12.T3 |
| 083 | E1.F1.T2, E1.F13.T5, E1.F13.T7 |
| 084 | E1.F1.T2, E1.F13.T2, E1.F13.T5 |
| 085 | E1.F1.T2, E1.F13.T7 |
| 086 | E1.F1.T8, E1.F13.T7 |
| 087 | E1.F13.T1, E1.F13.T5 |
| 088 | E1.F1.T9, E1.F5.T1, E1.F5.T9, E1.F13.T4, E1.F13.T6, E1.F13.T9 |

**Coverage:** 88/88. No REQ-W2 is left without a task. Every component of the architecture's file plan (§1.2) has a task: `lanes.json`, `check-modes.json`, `state-machine.json`, both schemas, the state tool, `karvey-context.py`, `karvey-spec-merge.py`, `lint-plugin.py` (L-40..L-54), the eight new scripts, `karvey_lib/{lanes,modes,metrics,manifest,gitlog,judges}.py`, `security_tools.json`, `guards.py`, `karvey_hooks.py`, `defaults.json`, the `karvey-judges` skill, `rules/{lanes,gates,judges}.md` and the rubrics, the §8 skill/rule texts, the tables, unit suites, manual scripts, and the dogfooding artifacts (§7.1, §7.2, §7.4).

## Totals and critical path

- **Tasks:** 71, of which 2 `[human]` and 69 agent tasks (61 Backend, 8 Test).
- **Total estimate:** 706 min ≈ 11.8 h of AI + review, calibrated. Per feature: F1 116 · F2 94 · F3 72 · F4 72 · F5 104 · F6 26 · F7 39 · F8 30 · F9 41 · F10 23 · F11 8 · F12 19 · F13 62.
- **Critical path by dependencies:** 141 min ≈ 2.4 h:
  E1.F1.T1 → E1.F2.T1 → E1.F2.T2 → E1.F5.T1 → E1.F7.T1 → E1.F7.T2 → E1.F5.T3 → E1.F5.T6 → E1.F10.T2 → E1.F5.T8 → E1.F13.T6 → E1.F13.T7 → [E1.F13.T9 human].
  The `[human]` waits and CI queue time are not counted.
- **Serial file spines** (not dependencies, but they serialise work): `karvey-state.py` (11 tasks, 118 min), `lint-plugin.py` (11 tasks, 104 min) and `karvey-context.py` (7 tasks, 71 min). With one agent the realistic wall time is the total, not the critical path; with parallel agents the floor is the longest spine plus its dependencies, so the dependency path of 141 min, not 118.

## What proved impractical when breaking the architecture into tasks

1. **The state tool is one file.** Eleven tasks change `karvey-state.py`, so they cannot run (P) whatever their dependencies say. Splitting it into `karvey_lib/state_*.py` modules would open parallel lanes; it is left as in the approved file plan, and `karvey-impl` may propose the split as an implementation detail.
2. **Lint checks ride with their feature.** Each L-NN is added in the task that makes its rule true, so the whole-repo lint stays at 0 errors after every task, at the cost of serialising `lint-plugin.py` across features.
3. **The four commits without trailer** (`390e6cb`, `02b460b`, `62ffc6d`, `38f42bf`) are `wave1-hardening` decision commits inherited from the base branch, not this change's. E1.F5.T9 records that mapping; they leave the manifest range once `wave1-hardening` is on `main`. History is not rewritten.
4. **Upgrade steps are a hand-off, not code.** Project-upgrade's catalogue and engine live on another branch; E1.F13.T5 writes the ten §7.4 rows as a declared file in the catalogue's field shape. Turning them into catalogue entries and `upgrade_steps.py` functions is a follow-up once both changes are on `main`.
5. **The living-spec merge of this change waits for Wave 1's.** `karvey-spec-merge.py wave2-structural` refuses until the nine MODIFIED REQ-W1 blocks are in the living spec (spec-delta note); that merge belongs to `karvey-deploy` step 2.4-bis at release, after `wave1-hardening` is merged — not a task here.
6. **Manual scripts run once, together.** The seven `tests/manual/*.md` scripts are written in their features and executed headless (D-19) in E1.F13.T6, so a script that needs another feature's code never runs early.
7. **This change counts as measured only from its release gate.** Its earlier approvals predate `gate_outcomes`, and nothing is back-filled (architecture A-06); the readiness report will show it as the first measured change once the release gate is recorded by the new tool.

---
*Generated by `karvey-tasks` (PHASE 7) on 2026-09-25 for `wave2-structural`. Not approved by this document.*
