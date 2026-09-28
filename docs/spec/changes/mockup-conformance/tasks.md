# Tasks: mockup-conformance

> PHASE 7 (`karvey-tasks`, skill text read from `plugins/karvey/skills/karvey-tasks/SKILL.md` in this worktree) · Security Tier 3 · Lane `standard` · Tracker: Markdown (`project.json:management.tool = markdown`): this file + `PLAN.md`, no external tracker.
> Inputs: `architecture.md` (generated for the merged *how* gate; revised after its judges, F-32..F-54), `requirements.md` (REQ-MC-001..055, approved under D-21; revised under D-42 / F-55 on 2026-09-28: 016, 030, 055 revised, 056 and 057 added → REQ-MC-001..057, re-approval pending), `prd.md`, `spec.json`, `risks.md`, the house style of `living-docs/tasks.md`, and the code on `feature/mockup-conformance` at `1eb6e9c`.
>
> **Estimates are calibrated.** In this repo the skill's 10–30 min band ran about 10× high. The minutes below are realistic **AI execution + human review** for one task (typically 3–8 min AI + 2–7 min review), as in Waves 2 and 3 and `living-docs`. `karvey-impl` records the actuals next to them in `PLAN.md` and never edits an estimate.

## Summary

| Item | Value |
|---|---|
| Features | 9 (the PLAN.md features F1..F9, same numbering) + `E1.DEPLOY` |
| Tasks | 69 (53 Backend, 14 Test, 2 human) |
| Agent tasks / `[human]` tasks | 67 / 2 |
| Total estimate (agent tasks, AI + review, calibrated) | **782 min** (≈ 13.0 h) |
| Critical path by dependencies (agent minutes; the `[human]` waits not counted) | **192 min** (≈ 3.2 h), 15 tasks |
| REQ-MC coverage | 57/57 |
| Largest task | 15 min (cap 60) |

## Conventions

- **IDs** `E1.F{n}.T{n}`; E1 = this change, F{n} = the PLAN.md feature of the same number (the architecture's components C-01..C-19 map to them in the feature headers). The production OK is `E1.DEPLOY.T1`.
- **Layers:** `[Backend]` = plugin hooks, scripts, library, schemas, templates and skill/rule text; `[Test]` = test-only work (fixtures, failing suites written first, end-to-end suites, the base check, the whole-repo gate); `[human]` = a step only a person may run (`rules/multi-agent.md` §5): the owner's deviation approval in the manual E2E and the prod OK. No DB, Frontend or Infra task: this repository has no database, no UI (the fixture UIs are test data) and no cloud (infra skipped, architecture A-13).
- **Estimate** = AI execution + review, minutes, calibrated (header). A `[human]` task carries no estimate; it declares the executor.
- **(P)** = can run in parallel with other (P) tasks whose dependencies are met, because the files differ. Tasks that share `karvey-state.py`, `karvey-conformance.py`, `mockup.py`, `conformance/__init__.py`, `lint-plugin.py` or `karvey-context.py` run in sequence even when marked (P); `karvey-impl` picks the order.
- **Test first** (REQ-W2-057): each feature opens with a `[Test]` task whose suites fail for a named reason before the code; every task's **Tests added** are written before its code; tests are tagged `@req REQ-MC-NNN` or named `test_REQ_MC_NNN_*`. Manual scripts carry `manual:` reasons.
- **Sheet line** (REQ-LD-027 of `living-docs`): every task that edits a path of this repository's component map updates the component's sheet in the same commit (the Component delta of the architecture lists the five components); the sheet check runs at every task close.
- **Every impl commit** carries `Karvey-Change: mockup-conformance`, adds one line under `## [Unreleased]` in `CHANGELOG.md`, and changes no version (4.3.0 is fixed at release by `karvey-deploy`).
- **Done criterion** is a command, run from the repo root. Unit tests: `python3 -m unittest discover -s plugins/karvey/tests/unit -p '<file>' -v`. Tables: `python3 plugins/karvey/tests/hooks/run_tables.py --only <table>`. Lint: `python3 plugins/karvey/scripts/lint-plugin.py [--only L-NN]` — 0 errors after every task.
- **Neutral text:** no organisation, product, client or person names, no ids, no home paths, no secrets in any new file (PRD §9). Fixtures are fictional (an invoice list, a fixture command); browser or image tools appear only as examples.
- **Nothing outside the repository is written** by an agent task, except the machine-local state directory inside the git common dir, which the hook and the tools own.
- **Line numbers** in the architecture are from `1eb6e9c`; E1.F9.T1 re-verifies the architecture §13 list after the rebase onto `living-docs`' final head, and each task re-reads the lines it edits.
- **One requirement, one Feature**: every requirement's tasks sit in its PLAN.md Feature; the exceptions carry a `Split:` line.

## Execution order

1. **E1.F9.T1 first**: `living-docs`' implementation is in the base, or impl waits (REQ-MC-053). Then **E1.F9.T2**: the size base snapshot in a commit of its own, before any rule or skill edit (REQ-MC-045). **E1.F8.T1** (the `4.3` check-mode rows and the `approved_under` resolver) runs early: every later check reads its mode from it (L-83).
2. The failing-suite tasks that open each feature (E1.F1.T1, E1.F2.T1, E1.F4.T2, E1.F5.T1, E1.F6.T1, E1.F7.T1) can start in parallel after the base check.
3. **F1 → F2 → F3** (ids, decisions, impl inputs) and **F4 → F5 → F6, F7** (comparison, deviations and release blockers, traceability, targets) run as their dependencies land; they meet at E1.F3.T5, E1.F3.T6 and E1.F5.T7.
4. **F8** wires rules, load lists, skill texts, sheets, upgrade steps and compatibility.
5. **F9 last**: the fixture end-to-end suites, the owner's approval in the manual E2E (`[human]`), the size comparison and the whole-repo gate. `E1.DEPLOY.T1` (`[human]`) is the production OK at release; QA and archive are phases, not tasks here.

## Feature E1.F1: Element ids in the mockup: contract, parser, rules, surface coverage, deterministic map, history and renames, design keeps ids

Architecture §1.3, §3 (S-11).  
Requirements covered: 001..007  
Total estimated time: 74 min (6 tasks)

### E1.F1.T1 [Test] Web fixture `tests/fixtures/conformance/web/` (fictional invoice list: `requirements.md` with `Surface:` lines, `mockup.html` with ids, a repeat, a dynamic date, empty and export-error states) + failing `test_mockup_check.py` for REQ-MC-001..006 — _Depends: E1.F9.T1_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/tests/fixtures/conformance/web/{requirements.md,mockup.html}` (NEW, fictional); `plugins/karvey/tests/unit/test_mockup_check.py` (NEW)  
**Requirements:** REQ-MC-001, REQ-MC-002, REQ-MC-003, REQ-MC-004, REQ-MC-005, REQ-MC-006, REQ-MC-007  
**Tests added:** `test_REQ_MC_001_*` … `test_REQ_MC_006_*` from the requirements' scenarios fail with `ModuleNotFoundError: karvey_lib.mockup` until E1.F1.T2  
**Done when:** the suite runs and fails for that reason (`python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_check.py' -v`)

### E1.F1.T2 [Backend] `karvey_lib/mockup.py` parser (`html.parser`, `file:line:col` + CSS-like path) and element rules: required kinds (tag/ARIA inference, `data-mk-kind`), id pattern, ≤ 48 chars, digit run ≥ 6, `secret` leak pattern, duplicates vs `data-mk-repeat`, `data-mk-req` ids or `gap` — _Depends: E1.F1.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/mockup.py` (NEW); `plugins/karvey/tests/unit/test_mockup_check.py` (cases)  
**Requirements:** REQ-MC-001, REQ-MC-002, REQ-MC-003  
**Tests added:** the REQ-MC-001..003 scenarios (missing id: control; duplicate id: export; bad id format; id carries a digit run; unknown requirement; gap → spec-gap)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_check.py' -v` passes its 001–003 cases

### E1.F1.T3 [Backend] Surface and coverage: `Surface: ui|none` read from `requirements.md` trace lines (`surface missing`), uncovered `ui` requirements, elements citing `none`, living-spec requirements counted `ui` for the element and outside coverage — _Depends: E1.F1.T2_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/mockup.py`; `plugins/karvey/tests/unit/test_mockup_check.py` (cases)  
**Requirements:** REQ-MC-004  
**Tests added:** `uncovered ui requirement REQ-INV-007`, `surface missing`, a living-spec citation outside coverage  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_check.py' -v` passes its 004 cases

### E1.F1.T4 [Backend] `karvey-mockup.py check <change>`: deterministic `mockup-map.json` (kind, screen, state, parent, order, text, reqs, repeat, instances, dynamic, path, file hashes), exit codes, `--json`; `generated mockup` refuses `element check not run` when the map's file hashes do not match — _Depends: E1.F1.T3_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-mockup.py` (NEW); `plugins/karvey/scripts/karvey_lib/mockup.py`; `plugins/karvey/scripts/karvey-state.py` (`cmd_generated`); `plugins/karvey/tests/unit/test_mockup_check.py` (cases)  
**Requirements:** REQ-MC-005  
**Tests added:** byte-identical map on two runs; map content scenario (`export` parent `filter-bar`, order 2); parse error → exit 5, no map; skill-wiring refusal  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_check.py' -v` passes its 005 cases; `python3 plugins/karvey/scripts/karvey-mockup.py check --root plugins/karvey/tests/fixtures/conformance/web --json` exits 0

### E1.F1.T5 [Backend] History: `mockup-map.prev.json`, `history.removed`, `--rename old=new`, `history.retired` across all iterations (reuse refused), unlogged-change list (added, removed, text or requirement changed) for REQ-MC-008 — _Depends: E1.F1.T4, E1.F2.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/mockup.py`; `plugins/karvey/scripts/karvey-mockup.py`; `plugins/karvey/tests/unit/test_mockup_check.py` (cases)  
**Requirements:** REQ-MC-006, REQ-MC-008  
**Tests added:** rename accepted; `reused id export (control → message)`; `removed: print`; `unlogged change: export (text)` listed  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_check.py' -v` passes; all REQ-MC-001..006 cases green

### E1.F1.T6 [Backend] Design-graphic keeps the ids: `approve design_graphic` runs the element check and refuses a lost or changed id without a rename (`filter-status`); `karvey-design-graphic` skill text: keep attributes, re-run the check, tokens by name — _Depends: E1.F1.T5, E1.F2.T4, E1.F1.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`cmd_approve`); `plugins/karvey/skills/karvey-design-graphic/SKILL.md`; `plugins/karvey/tests/unit/test_mockup_hash.py` (NEW, cases)  
**Requirements:** REQ-MC-007  
**Tests added:** `test_REQ_MC_007_design_drops_id_refused` fails until the check is wired  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_hash.py' -v` passes its 007 cases

## Feature E1.F2: Decisions written back: decision log, resolution against revision_history, what-gate blockers, instruction link, mockup hash, gate summary

Architecture §1.4, §1.5, §3 (S-9).  
Requirements covered: 008..013  
Total estimated time: 81 min (7 tasks)

### E1.F2.T1 [Test] Failing `test_mockup_log.py` for REQ-MC-008..011, 013, 043 (add/resolve, hand edit, revision link, blockers, instruction link, dismissals and revisions in the summary, gate mapping) — _Depends: E1.F9.T1_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/tests/unit/test_mockup_log.py` (NEW)  
**Requirements:** REQ-MC-008, REQ-MC-009, REQ-MC-010, REQ-MC-011, REQ-MC-013, REQ-MC-043, REQ-MC-012  
**Tests added:** each scenario of the six requirements; they fail with `invalid choice: 'mockup'` until E1.F2.T2  
**Done when:** the suite runs and fails for that reason (`python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_log.py' -v`)

### E1.F2.T2 [Backend] `karvey-state.py mockup decision add|list`: `mockup-log.md` written only by the tool (fixed header, `MD-NN`, iteration, origin owner|agent, quote ≤ 200 chars leak-checked or `F-NN`, elements, `unresolved`), `spec.json:mockup.log_sha256` under the state lock; `validate` reports `decision log not written by the state tool` — _Depends: E1.F2.T1, E1.F8.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`build_parser`, new group); `plugins/karvey/scripts/karvey_lib/mockup.py` (log section); `plugins/karvey/tests/unit/test_mockup_log.py` (cases)  
**Requirements:** REQ-MC-008  
**Tests added:** REQ-MC-008 scenarios incl. the hand-edit refusal and origin `agent`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_log.py' -v` passes its 008 cases

### E1.F2.T3 [Backend] `mockup decision resolve`: `requirement-revision --reqs … --revision <at>` checked against `revision_history` (entry exists, names the MD id, requirement ids exist) or `no-spec-impact --reason` (≥ 10 chars) — _Depends: E1.F2.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/scripts/karvey_lib/mockup.py`; `plugins/karvey/tests/unit/test_mockup_log.py` (cases)  
**Requirements:** REQ-MC-009  
**Tests added:** `no revision_history entry names MD-03`; reason missing refused; a valid resolution recorded  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_log.py' -v` passes its 009 cases

### E1.F2.T4 [Backend] `mockup.gate_blockers`: element-check errors, unresolved rows, missing revision entries, requirements gone, unlogged element changes; wired in `cmd_approve` (mockup, design_graphic), `cmd_approve_gate` (gates covering them) and `compute_next` — _Depends: E1.F2.T3, E1.F1.T5_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/scripts/karvey_lib/mockup.py`; `plugins/karvey/tests/unit/test_mockup_log.py` (cases)  
**Requirements:** REQ-MC-010, REQ-MC-043  
**Tests added:** `mockup: MD-05 unresolved` refuses `approve-gate what` and records nothing; `next` lists the causes; the *what* gate holds these checks (043)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_log.py' -v` passes its 010 and 043 (what-gate) cases

### E1.F2.T5 [Backend] Captured-instruction link: an `instruction` row captured in `mockup` and classified `requirement-revision` must be cited by an MD row (`instructions.read_rows` of `living-docs`); blocker cause names `F-NN` — _Depends: E1.F2.T4_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/mockup.py`; `plugins/karvey/tests/unit/test_mockup_log.py` (cases)  
**Requirements:** REQ-MC-011  
**Tests added:** REQ-MC-011 success and error scenarios over a fixture `findings.md`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_log.py' -v` passes its 011 cases

### E1.F2.T6 [Backend] Mockup hash: `approvals.<phase>.artifact_sha256` and `spec.json:mockup.{hash, map_sha256, approved_under}` written at `approve mockup` and `approve design_graphic`; `validate` reports `mockup changed after approval` — _Depends: E1.F2.T4, E1.F8.T1, E1.F2.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`cmd_approve`, `cmd_validate`); `plugins/karvey/tests/unit/test_mockup_hash.py` (cases)  
**Requirements:** REQ-MC-012  
**Tests added:** hash re-recorded after a design-graphic restyle; edit after approval reported; both fields written together  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_hash.py' -v` passes its 012 cases

### E1.F2.T7 [Backend] *Mockup decisions* gate-summary block (revisions with REQ and MD ids, then `no-spec-impact` with reasons) and the approval `ref` composed with the MD ids; summary refuses to present when a revision lacks its MD — _Depends: E1.F2.T3_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (`gate_summary`); `plugins/karvey/scripts/karvey-state.py` (`cmd_approve_gate` ref); `plugins/karvey/tests/unit/test_mockup_log.py` (cases)  
**Requirements:** REQ-MC-013  
**Tests added:** REQ-MC-013 scenarios; dismissals listed  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_log.py' -v` passes; all 008–011, 013 cases green

## Feature E1.F3: Implementation from the mockup: impl refusal, Elements lines, impl and tasks text (mockup first, requirements for behaviour — D-42), strip setting, extra ids, declared deviations (forced, improvement), conflicts asked

Architecture §1.6, §1.7.  
Requirements covered: 014..018, 055..057  
Total estimated time: 72 min (7 tasks)

### E1.F3.T1 [Test] Failing cases for F3 in `test_mockup_hash.py` (impl refusal, lane raise), `test_tasks_elements.py` (Elements lines, assignment), `test_conformance_settings.py` (strip setting), `test_lint_mc.py` (impl and tasks text anchors), `test_deviations.py` (declared deviations: forced and improvement; conflict open at close) — _Depends: E1.F9.T1_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/tests/unit/test_mockup_hash.py` (NEW); `plugins/karvey/tests/unit/test_tasks_elements.py` (NEW); `plugins/karvey/tests/unit/test_conformance_settings.py` (NEW); `plugins/karvey/tests/unit/test_lint_mc.py` (NEW)  
**Requirements:** REQ-MC-014, REQ-MC-015, REQ-MC-016, REQ-MC-017, REQ-MC-018, REQ-MC-055, REQ-MC-056, REQ-MC-057  
**Tests added:** scenarios of 014–018 and 055–057 fail with a named reason (`invalid choice`, missing module, missing lint id) until their tasks land  
**Done when:** the suites run and fail for those reasons (`python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_tasks_elements.py' -v`)

### E1.F3.T2 [Backend] `advance … impl` on a UI change: refuse `mockup not approved` and `mockup changed after approval`; warn `mockup hash absent (approved before 4.3)` for a 4.2 approval; a lane raised to `feature-ui` without a mockup is refused — _Depends: E1.F2.T6, E1.F3.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`cmd_advance`); `plugins/karvey/tests/unit/test_mockup_hash.py` (cases)  
**Requirements:** REQ-MC-014, REQ-MC-042  
**Tests added:** REQ-MC-014 scenarios; the REQ-MC-042 lane-raise error scenario  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_hash.py' -v` passes its 014 and 042 cases

### E1.F3.T3 [Backend] `Elements:` line parsed next to `**Requirements:**` (`karvey-trace.py parse_tasks`); `karvey-mockup.py assign <change>` lists ids in no task and unknown ids; `approve tasks` / `approve-gate how` refuse on either — _Depends: E1.F1.T4, E1.F3.T1, E1.F8.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-trace.py` (`parse_tasks`); `plugins/karvey/scripts/karvey-mockup.py` (`assign`); `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/tests/unit/test_tasks_elements.py` (NEW)  
**Requirements:** REQ-MC-015, REQ-MC-043  
**Tests added:** `filter-status` unassigned refuses the tasks approval; the *how* gate holds it (043)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_tasks_elements.py' -v` passes its 015 cases

### E1.F3.T4 [Backend] Skill text: `karvey-tasks` (Elements lines, one presence `[Test]` task per screen before its first UI task, plan build side) and `karvey-impl` (Step 1 reads the map and mockup files; source order — the approved mockup for structure, layout, content and style, the requirements for behaviour, equal or better never different (D-42); parent, order, text, states, tokens per element; same ids; declare forced differences and improvements; on a requirement/mockup conflict stop, ask the owner and record a `spec-gap` finding; presence test at task close); L-87 anchors for both — _Depends: E1.F3.T3, E1.F8.T6_

**Estimate:** 14 min  
**Files:** `plugins/karvey/skills/karvey-tasks/SKILL.md`; `plugins/karvey/skills/karvey-impl/SKILL.md`; `plugins/karvey/scripts/lint-plugin.py` (L-87); `plugins/karvey/tests/unit/test_lint_mc.py` (cases)  
**Requirements:** REQ-MC-015, REQ-MC-016, REQ-MC-017, REQ-MC-057  
**Tests added:** L-87 mutations: impl text without the map input, without the source order or without the conflict duty → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-87` exits 0 and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_mc.py' -v` passes

### E1.F3.T5 [Backend] `conformance.strip_in_production` read from the reviewed line only (working copy ignored and audited); the gate never strips — _Depends: E1.F4.T1, E1.F3.T1_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/__init__.py`; `plugins/karvey/tests/unit/test_conformance_settings.py` (cases)  
**Requirements:** REQ-MC-017  
**Tests added:** REQ-MC-017 error scenario (`conformance setting ignored (not reviewed)`)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_settings.py' -v` passes its 017 cases

### E1.F3.T6 [Backend] `extra` ids: build-probe ids not in the approved map reported and counted as differences needing a deviation — _Depends: E1.F4.T6, E1.F3.T1_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/elements.py`; `plugins/karvey/tests/unit/test_conformance_compare.py` (cases)  
**Requirements:** REQ-MC-018  
**Tests added:** `extra: bulk-delete`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_compare.py' -v` passes its 018 cases

- **Split:** REQ-MC-018 sits in F3 (PLAN) but its code lives in the F4 comparator; it runs after E1.F4.T6.

### E1.F3.T7 [Backend] `karvey-state.py deviation add … --origin impl --kind forced|improvement` (REQ-MC-055, 056): an improvement needs `--better` and its side-by-side image, owner rejection → `fix-build`; the task summary names it; entries found later carry origin `gate`, kind `found`, and the metrics count undeclared-at-impl; `compare --presence-only` exits non-zero with `conflict open: F-NN` while an open `spec-gap` names an element of the entry (REQ-MC-057) — _Depends: E1.F5.T2, E1.F3.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/scripts/karvey_lib/deviations.py`; `plugins/karvey/scripts/karvey_lib/metrics.py`; `plugins/karvey/tests/unit/test_deviations.py` (cases)  
**Requirements:** REQ-MC-055, REQ-MC-056, REQ-MC-057  
**Tests added:** REQ-MC-055, 056 and 057 scenarios (`improvement without reason`, `improvement without side-by-side image`, rejection → `fix-build`, `conflict open`)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_deviations.py' -v` passes its 055, 056 and 057 cases

- **Split:** depends on the deviation group of F5.

## Feature E1.F4: Conformance gate: settings, codec, plan, probe, elements, pixels, side-by-side, request, captures, browse, report and recomputation, storage

Architecture §1.6, §1.8–§1.11, §3 (S-3..S-8, S-10).  
Requirements covered: 019..029, 054  
Total estimated time: 180 min (14 tasks)

### E1.F4.T1 [Backend] `project.schema.json:conformance` (viewport string pattern, devices, `pixel_threshold` percent, `pixel_tolerance` fraction, `box_tolerance_px`, `captures`, `ui_paths`, `cli_command` argv, `terminal_width`, `strip_in_production`, `dev_hosts`, `forbid`) + reviewed-line reader for every gate value — _Depends: E1.F9.T1, E1.F4.T2_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/project.schema.json`; `plugins/karvey/scripts/karvey_lib/conformance/__init__.py` (NEW, settings); `plugins/karvey/tests/unit/test_conformance_settings.py` (NEW)  
**Requirements:** REQ-MC-020, REQ-MC-024  
**Tests added:** `conformance.viewports invalid` for `1280x`; defaults; working-copy threshold ignored and audited  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_settings.py' -v` passes; `python3 plugins/karvey/scripts/karvey-state.py validate --all` exits 0

### E1.F4.T2 [Test] Pre-rendered web captures and probes for the fixture (mockup and build sides at 1280×800 and 390×844; one moved button, one changed label, one hidden element at phone width) + failing `test_conformance_compare.py` — _Depends: E1.F1.T1_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/tests/fixtures/conformance/web/{build/,captures/,plan.json,fixtures.json}` (NEW, fictional); `plugins/karvey/tests/unit/test_conformance_compare.py` (NEW)  
**Requirements:** REQ-MC-021, REQ-MC-022, REQ-MC-023, REQ-MC-024, REQ-MC-025, REQ-MC-054, REQ-MC-020, REQ-MC-019, REQ-MC-026, REQ-MC-027, REQ-MC-028, REQ-MC-029  
**Tests added:** scenarios of 021–025 and 054 fail with `ModuleNotFoundError` until E1.F4.T6  
**Done when:** the suite runs and fails for that reason (`python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_compare.py' -v`)

### E1.F4.T3 [Backend] `conformance/png.py`: decode 8-bit RGB/RGBA non-interlaced, filters 0–4, header dimensions checked before inflation, inflation bounded to `w × h × 4 + h`; encode RGBA filter 0; unsupported → `unmeasured (unsupported image)` — _Depends: E1.F4.T2_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/png.py` (NEW); `plugins/karvey/tests/unit/test_conformance_png.py` (NEW)  
**Requirements:** REQ-MC-025  
**Tests added:** round trip; 16-bit and interlaced refused; a decompression bomb stops at the bound  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_png.py' -v` passes

### E1.F4.T4 [Backend] `conformance/plan.py` + `karvey-conformance.py plan`: entries per screen and state from the map, every id in ≥ 1 entry (`unplanned: <id>`), closed step vocabulary, fixture keys resolved from `fixtures.json` (≤ 200 printable chars, leak-checked), viewports from settings — _Depends: E1.F4.T1, E1.F1.T4, E1.F4.T2, E1.F8.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-conformance.py` (NEW); `plugins/karvey/scripts/karvey_lib/conformance/plan.py` (NEW); `plugins/karvey/tests/unit/test_tasks_elements.py` (cases)  
**Requirements:** REQ-MC-019, REQ-MC-020, REQ-MC-043  
**Tests added:** REQ-MC-019 scenarios; an unknown step refused; a secret-shaped fixture refused; the *how* gate lists plan coverage  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_tasks_elements.py' -v` passes its 019, 020 cases

### E1.F4.T5 [Backend] Probe contract: `templates/conformance/mk-probe.js` (reads `data-mk`, boxes, text, computed styles, visibility, the `karvey-build` meta; disables animation and caret) + `request`, `manifest`, `probe` schemas; L-84 (no write API in the probe) — _Depends: E1.F9.T1, E1.F4.T2, E1.F7.T1_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/templates/conformance/{mk-probe.js,request.schema.json,manifest.schema.json,probe.schema.json}` (NEW); `plugins/karvey/scripts/lint-plugin.py` (L-84); `plugins/karvey/tests/unit/test_targets.py` (NEW, probe schema cases); `plugins/karvey/tests/unit/test_lint_mc.py` (cases)  
**Requirements:** REQ-MC-021, REQ-MC-022, REQ-MC-038  
**Tests added:** fixture probes validate against the schema; L-84 mutation: `fetch(` in the probe → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-84` exits 0 and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_targets.py' -v` passes its schema cases

### E1.F4.T6 [Backend] `conformance/elements.py`: present / missing / hidden per entry and viewport, box Δ, text (whitespace-normalised, approved dynamic excluded) and style (colour, font size ±0.5 px, weight) differences, `unapproved dynamic marker` — _Depends: E1.F4.T2, E1.F4.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/elements.py` (NEW); `plugins/karvey/tests/unit/test_conformance_compare.py` (cases)  
**Requirements:** REQ-MC-021, REQ-MC-022, REQ-MC-023, REQ-MC-054  
**Tests added:** `hidden: filter-status @390x844`; `export: box Δy +20px`; `text differs`/`style differs` at a 0.1 % pixel ratio  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_compare.py' -v` passes its 021, 022 (markers), 054 cases

### E1.F4.T7 [Backend] `conformance/imgdiff.py`: masking of approved dynamic boxes on both sides, per-pixel distance vs `pixel_tolerance`, ratio vs `pixel_threshold` (percent), box tolerance, `over threshold` — _Depends: E1.F4.T3, E1.F4.T6_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/imgdiff.py` (NEW); `plugins/karvey/tests/unit/test_conformance_compare.py` (cases)  
**Requirements:** REQ-MC-022, REQ-MC-024  
**Tests added:** 0.2 % → within; 12 % with a 50 % working-copy value → over threshold and audited  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_compare.py' -v` passes its 024 cases

### E1.F4.T8 [Backend] `conformance/render.py`: side-by-side PNG (mockup | build | overlay: build dimmed, differing pixels red, outlined elements); size mismatch → side-by-side only and `unmeasured (size differs)` — _Depends: E1.F4.T7_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/render.py` (NEW); `plugins/karvey/tests/unit/test_conformance_compare.py` (cases)  
**Requirements:** REQ-MC-023, REQ-MC-025  
**Tests added:** REQ-MC-023 scenarios; REQ-MC-025 success scenario  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_compare.py' -v` passes all its cases

### E1.F4.T9 [Backend] `karvey-conformance.py request`: `request.json` from the plan, reviewed base URL (host in `dev_hosts`, not a production environment, not in `forbid`; empty allow-list refused) or CLI argv, build commit, mockup hash, probe hash, fixture user by name; leak-checked — _Depends: E1.F4.T4, E1.F4.T5, E1.F4.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-conformance.py`; `plugins/karvey/scripts/karvey_lib/conformance/captures.py` (NEW); `plugins/karvey/tests/unit/test_conformance_captures.py` (NEW)  
**Requirements:** REQ-MC-026, REQ-MC-027  
**Tests added:** `production target refused`; empty allow-list refused; a secret-shaped value refused; `browse.via: none` → nothing requested  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_captures.py' -v` passes its request cases

### E1.F4.T10 [Backend] `karvey-conformance.py verify-captures`: manifest vs files (hash, size caps), manifest vs request (entry, viewport, commit, mockup hash, probe hash), PNG dimensions vs viewport × ratio, `karvey-build` meta vs commit (`unverified` / `build commit unproven`) — _Depends: E1.F4.T9, E1.F4.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/captures.py`; `plugins/karvey/tests/unit/test_conformance_captures.py` (cases)  
**Requirements:** REQ-MC-026  
**Tests added:** REQ-MC-026 error scenarios (hash differs, size does not match); meta mismatch → unverified  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_captures.py' -v` passes all its cases

### E1.F4.T11 [Backend] `karvey-browse` skill text: run a conformance request `local` (environment's automation, examples only), `agent:<name>` (self-contained instruction from the request, files and manifest back into `captures/`), `none` (nothing, `not evaluated`) — _Depends: E1.F4.T9_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/skills/karvey-browse/SKILL.md`  
**Requirements:** REQ-MC-026  
**Tests added:** none new (text; L-87 anchor `conformance request` added in E1.F8.T7)  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0 (neutrality checks green over the new text)

### E1.F4.T12 [Backend] `karvey-conformance.py compare`: `report.json` + `report.md` (commit, mockup hash, reviewed settings, results per entry, images with hashes); text layers leak-checked; staleness (`status`: UI-code commits via the component map → `ui_paths` → outside `docs/`, or mockup hash changed); recomputation function used by the gate — _Depends: E1.F4.T8, E1.F4.T10, E1.F4.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-conformance.py`; `plugins/karvey/scripts/karvey_lib/conformance/__init__.py`; `plugins/karvey/tests/unit/test_conformance_report.py` (NEW)  
**Requirements:** REQ-MC-028  
**Tests added:** REQ-MC-028 scenarios incl. `stale (mockup hash changed)`; a hand-edited report ≠ recomputation  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_report.py' -v` passes its 028 cases

### E1.F4.T13 [Backend] Capture storage: `captures: commit` (under the change) or `local` (`<state>/conformance/<change>/`, report keeps hashes); `capture missing: <name>` at a gate — _Depends: E1.F4.T12, E1.F4.T2_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/__init__.py`; `plugins/karvey/tests/unit/test_conformance_report.py` (cases)  
**Requirements:** REQ-MC-029  
**Tests added:** REQ-MC-029 scenarios  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_report.py' -v` passes all its cases

### E1.F4.T14 [Test] No-network and read-only AST test over `karvey-mockup.py`, `karvey-conformance.py`, `karvey_lib/{mockup,deviations}.py`, `karvey_lib/conformance/` (no `socket`, `urllib`, `http.client`; `subprocess` only git and `run_streamed`) — _Depends: E1.F4.T12_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/tests/unit/test_no_network_mc.py` (NEW)  
**Requirements:** REQ-MC-026  
**Tests added:** a mutation importing `urllib` in a fixture copy fails the test  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_no_network_mc.py' -v` passes

## Feature E1.F5: Mockup deviations and the owner's approval: entries, resolutions, phrase, marker, ledger, release blockers, gate summary, QA text

Architecture §1.12–§1.14, §3 (S-1, S-2).  
Requirements covered: 030..035  
Total estimated time: 112 min (9 tasks)

### E1.F5.T1 [Test] Failing `test_deviations.py` and `test_deviation_approval.py` + hook table `deviation-confirm.json` (five languages, lists, ranges, 11 ids, quoted phrase, agent-shaped text, protect-paths cases) — _Depends: E1.F9.T1_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/tests/unit/test_deviations.py` (NEW); `plugins/karvey/tests/unit/test_deviation_approval.py` (NEW); `plugins/karvey/tests/hooks/tables/deviation-confirm.json` (NEW)  
**Requirements:** REQ-MC-030, REQ-MC-031, REQ-MC-032, REQ-MC-033, REQ-MC-034, REQ-MC-035  
**Tests added:** scenarios of 030–034 fail with `invalid choice: 'deviation'` / no marker written  
**Done when:** both suites run and fail for those reasons; `python3 plugins/karvey/tests/hooks/run_tables.py --only deviation-confirm` fails as expected

### E1.F5.T2 [Backend] `karvey_lib/deviations.py` + `karvey-state.py deviation add|update|list` (`## Mockup deviations`, fixed block, only the tool writes) and `deviation add --from-report` (coverage of every report finding; one entry per screen for `unmeasured`) — _Depends: E1.F5.T1, E1.F4.T12_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/deviations.py` (NEW); `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/tests/unit/test_deviations.py` (cases)  
**Requirements:** REQ-MC-030, REQ-MC-025  
**Tests added:** REQ-MC-030 scenarios (`uncovered` difference); REQ-MC-025 error scenario  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_deviations.py' -v` passes its 030 cases

### E1.F5.T3 [Backend] Resolutions: `fix-build` closes `fixed` only in a recomputation where the difference is gone; `revise-mockup` hands a spec-revision to `/karvey-iterate` (`reopen … mockup`) and closes after re-approval + a passing run; hand-set status reported — _Depends: E1.F5.T2_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/deviations.py`; `plugins/karvey/scripts/karvey_lib/conformance/__init__.py`; `plugins/karvey/tests/unit/test_deviations.py` (cases)  
**Requirements:** REQ-MC-031  
**Tests added:** REQ-MC-031 scenarios  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_deviations.py' -v` passes its 031 cases

### E1.F5.T4 [Backend] Vocabulary `confirm.deviation` (en, es, pt, de, fr) + `classify_confirm` extension (1–10 `DV-NN`, no ranges, notice when not recorded); L-85 — _Depends: E1.F5.T1_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/vocabulary.json`; `plugins/karvey/scripts/karvey_lib/approval.py`; `plugins/karvey/scripts/lint-plugin.py` (L-85); `plugins/karvey/tests/unit/test_deviation_approval.py` (cases)  
**Requirements:** REQ-MC-032  
**Tests added:** phrases in five languages recognised; 11 ids and ranges → no marker; L-85 mutation  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-85` exits 0 and the phrase cases of `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_deviation_approval.py' -v` pass

### E1.F5.T5 [Backend] Hook side: transcript cross-check of the phrase, entry hashes from `deviations.md` (≤ 256 KB, read-only), one-use marker `approvals/confirm/deviation-<change>.json`, echo of bound titles/Differs/short hashes, audit record; needles `karvey/deviations` and the confirm directory in `STATE_NEEDLES` and `karvey-hook.sh` — _Depends: E1.F5.T4_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/approval.py`; `plugins/karvey/scripts/karvey_lib/guards.py`; `plugins/karvey/hooks/karvey-hook.sh`; `plugins/karvey/tests/hooks/tables/deviation-confirm.json`  
**Requirements:** REQ-MC-032  
**Tests added:** the table's marker, echo, transcript and protect-paths cases  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only deviation-confirm` passes

### E1.F5.T6 [Backend] `deviation approve <change>`: consume the marker (≤ 30 min), re-hash, `accepted (owner, <at>)`, protected ledger + tracked `deviation_log`; verification at every blocker call: ledger ↔ audit ↔ text (tampered / void), other clone or CI `accepted (not verifiable here)` listed — _Depends: E1.F5.T5, E1.F5.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/deviations.py`; `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/tests/unit/test_deviation_approval.py` (cases)  
**Requirements:** REQ-MC-032  
**Tests added:** REQ-MC-032 scenarios (tampered, void on edit, agent text ignored); audit cross-check; other-clone case  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_deviation_approval.py' -v` passes all its cases

### E1.F5.T7 [Backend] `conformance.gate_blockers` (recompute the report, stale, not evaluated, uncovered, pending, tampered, unverified) in `cmd_approve` (qa, prod), `cmd_approve_gate` (release), `check-prod` (prod-gate hook) and `karvey-release-gate.py item_conformance`; modes from the registry — _Depends: E1.F5.T6, E1.F4.T12, E1.F8.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/__init__.py`; `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/scripts/karvey-release-gate.py`; `plugins/karvey/tests/unit/test_deviations.py` (cases)  
**Requirements:** REQ-MC-033, REQ-MC-043  
**Tests added:** `conformance: DV-03 pending` refuses the release gate; a forged all-pass report refused; `check-prod` refuses; release gate holds these checks (043)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_deviations.py' -v` passes its 033 and 043 (release) cases

### E1.F5.T8 [Backend] *Conformance* block in the release (or granular qa) gate summary: counts per result, pending deviations with side-by-side paths, `capture missing`, report path and commit, bound short hashes, `not verifiable here` entries — _Depends: E1.F5.T7_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-context.py`; `plugins/karvey/tests/unit/test_deviations.py` (cases)  
**Requirements:** REQ-MC-034  
**Tests added:** REQ-MC-034 scenarios  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_deviations.py' -v` passes all its cases

### E1.F5.T9 [Backend] `karvey-qa` Dimension 8 cites the report (else `not evaluated`), keeps the design-spec and platform audit; `rules/judges/qa.md` fiscal question on conformance claims; L-87 anchors — _Depends: E1.F5.T7, E1.F3.T4, E1.F5.T1_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/skills/karvey-qa/SKILL.md`; `plugins/karvey/skills/karvey/rules/judges/qa.md`; `plugins/karvey/scripts/lint-plugin.py` (L-87 anchors)  
**Requirements:** REQ-MC-035  
**Tests added:** L-87 mutation: qa text without the report citation → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-87` exits 0

## Feature E1.F6: Traceability to evidence: element columns, empty-cell refusal

Architecture §1.15.  
Requirements covered: 036, 037  
Total estimated time: 30 min (3 tasks)

### E1.F6.T1 [Test] Failing `test_trace_elements.py` (columns per requirement, `n/a (target api)`, empty cell refusal) — _Depends: E1.F9.T1_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/tests/unit/test_trace_elements.py` (NEW)  
**Requirements:** REQ-MC-036, REQ-MC-037, REQ-W2-060  
**Tests added:** REQ-MC-036/037 scenarios fail until E1.F6.T2  
**Done when:** the suite runs and fails for that reason (`python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_trace_elements.py' -v`)

### E1.F6.T2 [Backend] `karvey-trace.py build/render`: elements, entries and conformance result per requirement of a UI change; generated block drift unchanged — _Depends: E1.F6.T1, E1.F4.T12, E1.F3.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-trace.py`; `plugins/karvey/tests/unit/test_trace_elements.py` (cases)  
**Requirements:** REQ-MC-036, REQ-W2-060  
**Tests added:** the REQ-MC-036 row example; hand edit → drift  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_trace_elements.py' -v` passes its 036 cases

### E1.F6.T3 [Backend] `karvey-trace.py check`: empty cell of a `ui` requirement fails; `n/a (target <t>)` accepted; release-gate item reads it — _Depends: E1.F6.T2, E1.F5.T7_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-trace.py`; `plugins/karvey/scripts/karvey-release-gate.py`; `plugins/karvey/tests/unit/test_trace_elements.py` (cases)  
**Requirements:** REQ-MC-037, REQ-W2-060  
**Tests added:** `REQ-INV-007: date-range has no conformance result`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_trace_elements.py' -v` passes all its cases

## Feature E1.F7: Targets: web, native (mobile and desktop), CLI, other targets

Architecture §1.8, §1.10.  
Requirements covered: 038..041  
Total estimated time: 55 min (5 tasks)

### E1.F7.T1 [Test] Failing target cases in `test_targets.py` + CLI fixture `tests/fixtures/conformance/cli/` (transcript mockup with `[mk:…]` anchors and restricted patterns; a tiny fixture module whose output differs in one anchor) — _Depends: E1.F9.T1_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/tests/unit/test_targets.py` (cases); `plugins/karvey/tests/fixtures/conformance/cli/` (NEW, fictional)  
**Requirements:** REQ-MC-038, REQ-MC-039, REQ-MC-040, REQ-MC-041  
**Tests added:** scenarios of 038–041 fail until E1.F7.T2..T5  
**Done when:** the suite runs and fails for that reason (`python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_targets.py' -v`)

### E1.F7.T2 [Backend] Web rules: presence from the rendered document incl. visibility, pixel diff on; `rules/targets.md` rows (element id and capture per target) — _Depends: E1.F7.T1, E1.F4.T6_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/elements.py`; `plugins/karvey/skills/karvey/rules/targets.md`; `plugins/karvey/tests/unit/test_targets.py` (cases)  
**Requirements:** REQ-MC-038  
**Tests added:** a template-only id is `missing`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_targets.py' -v` passes its 038 cases

### E1.F7.T3 [Backend] Native: accessibility-dump → probe converter contract (documented shape, schema-validated), no tree → `not evaluated` needing a deviation, pixel diff only at equal sizes; manual `tests/manual/conformance-native.md` — _Depends: E1.F7.T1, E1.F4.T8_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/captures.py`; `plugins/karvey/tests/manual/conformance-native.md` (NEW, `manual:` reason); `plugins/karvey/tests/unit/test_targets.py` (cases)  
**Requirements:** REQ-MC-039  
**Tests added:** REQ-MC-039 scenarios over fixture dumps  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_targets.py' -v` passes its 039 cases

### E1.F7.T4 [Backend] CLI: transcript parser (`[mk:<id>]`, anchors, restricted patterns checked by the element check), runner through `run_streamed` with a minimal environment and 30 s timeout, `textdiff.py` normalisation and per-block diff, transcript leak check — _Depends: E1.F7.T1, E1.F1.T4_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/mockup.py` (transcript); `plugins/karvey/scripts/karvey_lib/conformance/textdiff.py` (NEW); `plugins/karvey/scripts/karvey_lib/conformance/captures.py`; `plugins/karvey/tests/unit/test_targets.py` (cases)  
**Requirements:** REQ-MC-040  
**Tests added:** REQ-MC-040 scenarios; `.*` pattern refused; nested quantifier refused; environment has no inherited variables  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_targets.py' -v` passes its 040 cases

### E1.F7.T5 [Backend] Other targets: `not applicable: target <t>` written to the report (satisfies the release blocker, matrix `n/a`); `target undeclared` refused — _Depends: E1.F7.T1, E1.F5.T7_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/__init__.py`; `plugins/karvey/tests/unit/test_targets.py` (cases)  
**Requirements:** REQ-MC-041  
**Tests added:** REQ-MC-041 scenarios (web + api; api only)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_targets.py' -v` passes all its cases

## Feature E1.F8: Integration: check modes, lanes, gates, tokens, rule and load lists, skill texts, frontend sheets, upgrade steps, compatibility, documentation

Architecture §1.14, §1.16–§1.20.  
Requirements covered: 042..051  
Total estimated time: 123 min (10 tasks)

### E1.F8.T1 [Backend] Check-mode registry: `4.3` column and the 23 rows of architecture §1.16 (21 blocking-when-4.3, `conformance.production` blocking always, `sheet.elements` and `design.token` warn); resolver reads `spec.json:mockup.approved_under` with the absent-value rules (neither → warn; one of two → blocking + `validate` error); L-83 — _Depends: E1.F9.T1, E1.F8.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/schemas/check-modes.json`; `plugins/karvey/scripts/karvey_lib/modes.py`; `plugins/karvey/schemas/spec.schema.json` (`mockup`, `conformance`, `deviation_log`); `plugins/karvey/scripts/lint-plugin.py` (L-83); `plugins/karvey/tests/unit/test_modes_mc.py` (NEW); `plugins/karvey/tests/unit/test_lint_mc.py` (NEW)  
**Requirements:** REQ-MC-048, REQ-MC-049  
**Tests added:** `test_REQ_MC_049_rows_and_defaults`, `test_REQ_MC_048_absent_values_warn`, `..._one_of_two_blocks`, `..._reapproval_under_43_blocks`; L-83 mutation: a script check id without a `4.3` row → error  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_modes_mc.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-83` exits 0

### E1.F8.T2 [Test] Failing cases for F8 in `test_modes_mc.py` (lanes, compatibility), `test_conformance_compare.py` (tokens), `test_sheet_elements.py`, `test_upgrade_mc.py`, `test_lint_mc.py` (L-82, L-86, L-87 for mockup/test/deploy/archive) — _Depends: E1.F9.T1_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/tests/unit/test_sheet_elements.py` (NEW); `plugins/karvey/tests/unit/test_upgrade_mc.py` (NEW); `plugins/karvey/tests/unit/test_lint_mc.py` (cases); `plugins/karvey/tests/unit/test_modes_mc.py` (cases)  
**Requirements:** REQ-MC-042, REQ-MC-043, REQ-MC-044, REQ-MC-045, REQ-MC-046, REQ-MC-047, REQ-MC-050, REQ-MC-051, REQ-LD-022, REQ-MC-048, REQ-MC-049  
**Tests added:** scenarios of 042–047, 050, 051 fail with a named reason until their tasks land  
**Done when:** the suites run and fail for those reasons (`python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sheet_elements.py' -v`)

### E1.F8.T3 [Backend] Lane scoping: every check silent outside UI changes except `sheet.elements`; a lane raise makes them pending with the raised phases — _Depends: E1.F5.T7, E1.F2.T4_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/__init__.py`; `plugins/karvey/scripts/karvey_lib/mockup.py`; `plugins/karvey/tests/unit/test_mockup_hash.py` (cases)  
**Requirements:** REQ-MC-042  
**Tests added:** REQ-MC-042 success scenario (no conformance check listed for a `standard` change)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_mockup_hash.py' -v` passes all its cases

### E1.F8.T4 [Backend] Tokens: build computed values matched to design-system tokens (`designsys.resolved`), `undeclared token` (warn), style differences on resolved values — _Depends: E1.F4.T6, E1.F8.T2_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/conformance/elements.py`; `plugins/karvey/tests/unit/test_conformance_compare.py` (token cases)  
**Requirements:** REQ-MC-044  
**Tests added:** REQ-MC-044 scenarios  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_conformance_compare.py' -v` passes its 044 cases

### E1.F8.T5 [Backend] `rules/mockup-conformance.md` (≤ 900 words: element contract, decision duty, probe per target, deviation phrase, gate order) + `Load:` of the eight acting skills; L-82 — _Depends: E1.F9.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/skills/karvey/rules/mockup-conformance.md` (NEW); `plugins/karvey/skills/karvey-{mockup,design-graphic,tasks,impl,test,qa,deploy,archive}/SKILL.md` (`Load:` lines); `plugins/karvey/scripts/lint-plugin.py` (L-82); `plugins/karvey/tests/unit/test_lint_mc.py` (cases)  
**Requirements:** REQ-MC-045  
**Tests added:** L-82 mutation: the requirements skill loading the rule → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-82` exits 0

### E1.F8.T6 [Backend] Skill texts `karvey-mockup` (ids on generation, check each iteration, decision log, `--rename`, gap routing), `karvey-test` (request → browse → verify → compare → deviations → trace), `karvey-deploy` (blockers first), `karvey-archive` (sheet merge); L-87 anchors — _Depends: E1.F8.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/skills/karvey-{mockup,test,deploy,archive}/SKILL.md`; `plugins/karvey/scripts/lint-plugin.py` (L-87); `plugins/karvey/tests/unit/test_lint_mc.py` (cases)  
**Requirements:** REQ-MC-051, REQ-MC-045  
**Tests added:** L-87 mutation per skill  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-87` exits 0 and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_mc.py' -v` passes

### E1.F8.T7 [Backend] Frontend-module sheets: `Mockup elements` section in `component-kinds.json` and the template; archive merge of the map into module sheets; `components --check --commits` warns when an id listed in a sheet is removed without the sheet (every lane) — _Depends: E1.F1.T4, E1.F9.T1, E1.F8.T2_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/schemas/component-kinds.json`; `plugins/karvey/templates/components/frontend-module.md`; `plugins/karvey/scripts/karvey_lib/components.py`; `plugins/karvey/tests/unit/test_sheet_elements.py` (NEW)  
**Requirements:** REQ-MC-046, REQ-LD-022  
**Tests added:** REQ-MC-046 scenarios (archive lists the ids; `patch` removal warned)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sheet_elements.py' -v` passes

### E1.F8.T8 [Backend] Upgrade steps `mc-1-settings`, `mc-2-mockup-ids` (human; `karvey-mockup.py propose` writes `mockup.proposed.html`), `mc-3-capture` (report only) with the seven fields, idempotent, upgrade branch only — _Depends: E1.F4.T1, E1.F1.T4, E1.F8.T2_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade-steps.json`; `plugins/karvey/scripts/karvey_lib/upgrade_steps.py`; `plugins/karvey/scripts/karvey-mockup.py` (`propose`); `plugins/karvey/tests/unit/test_upgrade_mc.py` (NEW)  
**Requirements:** REQ-MC-047  
**Tests added:** REQ-MC-047 scenarios; dry-run writes nothing; L-38 invariant holds  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_mc.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-38` exits 0

### E1.F8.T9 [Test] Backward compatibility: 4.2 fixture projects (only `standard` changes; a UI change approved under 4.2) give identical validate/lint/gate results; hand-written unknown key still an error — _Depends: E1.F5.T7, E1.F8.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/tests/unit/test_modes_mc.py` (compat cases); `plugins/karvey/tests/fixtures/compat-4.2/` (NEW)  
**Requirements:** REQ-MC-050, REQ-MC-048  
**Tests added:** REQ-MC-050 scenarios  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_modes_mc.py' -v` passes all its cases

### E1.F8.T10 [Backend] Plugin README section (settings, both scripts, the phrase, MC-1..MC-3) + `hooks/README.md` (deviation phrase); L-86 — _Depends: E1.F8.T8, E1.F5.T5_

**Estimate:** 10 min  
**Files:** `README.md`; `plugins/karvey/hooks/README.md`; `plugins/karvey/scripts/lint-plugin.py` (L-86); `plugins/karvey/tests/unit/test_lint_mc.py` (cases)  
**Requirements:** REQ-MC-051  
**Tests added:** L-86 mutation: the section without `MC-3` → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-86` exits 0

## Feature E1.F9: Change-scoped: base after living-docs and size base (first); fixture dogfooding, owner's approval in the E2E, size and whole-repo gate (last)

Architecture §1.21, §6.3, §6.4, §7.1, §13.  
Requirements covered: 052, 053  
Total estimated time: 55 min (7 tasks, 1 `[human]`)

### E1.F9.T1 [Test] Base check: `living-docs`' implementation is in this branch's base (its last task's commit is an ancestor; `karvey_lib/components.py`, `instructions.py`, the confirm markers, the `4.2` check-mode column and `--fail-growth` exist); rebase; walk the architecture §13 list and note moved lines in the PLAN history

**Estimate:** 8 min  
**Files:** `plugins/karvey/tests/unit/test_base_living_docs.py` (NEW, change-scoped); `docs/spec/changes/mockup-conformance/PLAN.md` (history line with the base commit)  
**Requirements:** REQ-MC-053  
**Tests added:** `test_REQ_MC_053_base_holds_living_docs` fails naming the missing file or commit while `living-docs` is not merged  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_base_living_docs.py' -v` passes; `git merge-base --is-ancestor <living-docs last task commit> HEAD` exits 0

- If it fails, impl waits: no other task starts (REQ-MC-053). Lint ids L-82..L-87 are re-numbered here if `living-docs` took them (architecture A-12).

### E1.F9.T2 [Backend] Size base snapshot `docs/spec/retros/context-size-4.3.0-base.json` in a commit of its own, before any rule or skill edit of this change — _Depends: E1.F9.T1, E1.F8.T2_

**Estimate:** 6 min  
**Files:** `docs/spec/retros/context-size-4.3.0-base.json` (NEW, from `karvey-context-budget.py measure --label 4.3.0-base --json`)  
**Requirements:** REQ-MC-045  
**Tests added:** none new (the Wave 3 `order` check proves the snapshot precedes the edits)  
**Done when:** the file exists, re-running `measure` gives the same bytes (`cmp`), and `python3 plugins/karvey/scripts/karvey-context-budget.py order --json` names no later-edited skill

- **Split:** REQ-MC-045 sits in F8; its base snapshot must precede every edit, so it runs here.

### E1.F9.T3 [Test] `test_fixture_web_e2e.py`: the web fixture end to end (element check, decisions, assignment, plan, pre-rendered captures, verify, compare, deviations, matrix) asserting AC-1..AC-8, including text/token equality (REQ-MC-016) and QA `not evaluated` without a report (REQ-MC-035) — _Depends: E1.F5.T8, E1.F6.T3, E1.F3.T7_

**Estimate:** 15 min  
**Files:** `plugins/karvey/tests/unit/test_fixture_web_e2e.py` (NEW, change-scoped)  
**Requirements:** REQ-MC-052, REQ-MC-016, REQ-MC-035  
**Tests added:** the deliberate difference must be reported; removing it from the fixture makes the test fail  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_fixture_web_e2e.py' -v` passes

### E1.F9.T4 [Test] `test_fixture_cli_e2e.py`: the CLI fixture end to end (AC-9) and an `api` target reporting `not applicable` — _Depends: E1.F7.T4, E1.F7.T5_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/tests/unit/test_fixture_cli_e2e.py` (NEW, change-scoped)  
**Requirements:** REQ-MC-052  
**Tests added:** the differing anchor reported as `missing: summary-table`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_fixture_cli_e2e.py' -v` passes

### E1.F9.T5 [human] The owner approves a deviation in the manual E2E on the web fixture (`tests/manual/conformance-e2e.md`): real captures where `browse.via` allows, one deliberate difference, and the owner's own phrase — _Depends: E1.F9.T3, E1.F4.T11_

**Executor:** the owner (the person with `role: human` for this change); an agent cannot, by REQ-MC-032  
**Command:** the agent runs the steps of `tests/manual/conformance-e2e.md` up to `deviation add --from-report` and shows the side-by-side image of the pending `DV-NN`; the owner looks at it and types in the session `approve deviation DV-NN`; the agent then runs `python3 plugins/karvey/scripts/karvey-state.py deviation approve <fixture change>` and the release-gate check  
**Verification:** `python3 plugins/karvey/scripts/karvey-state.py deviation list <fixture change> --json` shows `DV-NN accepted (owner, …)` with a ledger line; `karvey-release-gate.py check` shows the conformance item green  
**Rollback:** the fixture change is disposable; delete its state-dir ledger and reset the fixture folder with `git checkout -- plugins/karvey/tests/fixtures/conformance/web`  
**Requirements:** REQ-MC-052, REQ-MC-032  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

### E1.F9.T6 [Backend] Size comparison against the base snapshot: `karvey-context-budget.py compare --fail-growth 10`; result in the PLAN history — _Depends: E1.F8.T6, E1.F8.T10, E1.F5.T9, E1.F3.T4_

**Estimate:** 6 min  
**Files:** `docs/spec/changes/mockup-conformance/PLAN.md` (history)  
**Requirements:** REQ-MC-045  
**Tests added:** none new (the Wave 3 compare with `--fail-growth`)  
**Done when:** `python3 plugins/karvey/scripts/karvey-context-budget.py compare --base docs/spec/retros/context-size-4.3.0-base.json --fail-growth 10` exits 0

- **Split:** REQ-MC-045's measurement closes the change; it runs last.

### E1.F9.T7 [Test] Whole-repo gate: all unit suites, hook tables, `lint-plugin.py` 0 errors, `validate --all`, `karvey-trace.py mockup-conformance --check` 57/57 + 2 MODIFIED — _Depends: E1.F9.T3, E1.F9.T4, E1.F9.T6, E1.F8.T9_

**Estimate:** 8 min  
**Files:** `docs/spec/changes/mockup-conformance/PLAN.md` (history)  
**Requirements:** REQ-MC-052, REQ-MC-053  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -v` passes; `python3 plugins/karvey/scripts/lint-plugin.py` 0 errors; `python3 plugins/karvey/scripts/karvey-trace.py mockup-conformance --check` exits 0

## E1.DEPLOY

### E1.DEPLOY.T1 [human] The prod OK for the release that ships this change (D-10) — _Depends: E1.F9.T7, E1.F9.T5_

**Executor:** the owner — never delegated (D-10)  
**Command:** inside `karvey-deploy`, after reading the release PR (its manifest lists every change and commit), type your own words with an approval **and** a production term, and answer the structured question that records the D-NN  
**Verification:** `python3 plugins/karvey/scripts/karvey-state.py check-prod mockup-conformance --json` → `ok: true` after `approve prod`  
**Rollback:** before the merge: nothing, the marker expires; after it: a revert PR, as a new change through the method  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

## Traceability matrix (REQ-MC → tasks)

| REQ-MC | Tasks |
|---|---|
| 001 | E1.F1.T1, E1.F1.T2 |
| 002 | E1.F1.T1, E1.F1.T2 |
| 003 | E1.F1.T1, E1.F1.T2 |
| 004 | E1.F1.T1, E1.F1.T3 |
| 005 | E1.F1.T1, E1.F1.T4 |
| 006 | E1.F1.T1, E1.F1.T5 |
| 007 | E1.F1.T1, E1.F1.T6 |
| 008 | E1.F1.T5, E1.F2.T1, E1.F2.T2 |
| 009 | E1.F2.T1, E1.F2.T3 |
| 010 | E1.F2.T1, E1.F2.T4 |
| 011 | E1.F2.T1, E1.F2.T5 |
| 012 | E1.F2.T1, E1.F2.T6 |
| 013 | E1.F2.T1, E1.F2.T7 |
| 014 | E1.F3.T1, E1.F3.T2 |
| 015 | E1.F3.T1, E1.F3.T3, E1.F3.T4 |
| 016 | E1.F3.T1, E1.F3.T4, E1.F9.T3 |
| 017 | E1.F3.T1, E1.F3.T4, E1.F3.T5 |
| 018 | E1.F3.T1, E1.F3.T6 |
| 019 | E1.F4.T2, E1.F4.T4 |
| 020 | E1.F4.T1, E1.F4.T2, E1.F4.T4 |
| 021 | E1.F4.T2, E1.F4.T5, E1.F4.T6 |
| 022 | E1.F4.T2, E1.F4.T5, E1.F4.T6, E1.F4.T7 |
| 023 | E1.F4.T2, E1.F4.T6, E1.F4.T8 |
| 024 | E1.F4.T1, E1.F4.T2, E1.F4.T7 |
| 025 | E1.F4.T2, E1.F4.T3, E1.F4.T8, E1.F5.T2 |
| 026 | E1.F4.T2, E1.F4.T9, E1.F4.T10, E1.F4.T11, E1.F4.T14 |
| 027 | E1.F4.T2, E1.F4.T9 |
| 028 | E1.F4.T2, E1.F4.T12 |
| 029 | E1.F4.T2, E1.F4.T13 |
| 030 | E1.F5.T1, E1.F5.T2 |
| 031 | E1.F5.T1, E1.F5.T3 |
| 032 | E1.F5.T1, E1.F5.T4, E1.F5.T5, E1.F5.T6, E1.F9.T5 |
| 033 | E1.F5.T1, E1.F5.T7 |
| 034 | E1.F5.T1, E1.F5.T8 |
| 035 | E1.F5.T1, E1.F5.T9, E1.F9.T3 |
| 036 | E1.F6.T1, E1.F6.T2 |
| 037 | E1.F6.T1, E1.F6.T3 |
| 038 | E1.F4.T5, E1.F7.T1, E1.F7.T2 |
| 039 | E1.F7.T1, E1.F7.T3 |
| 040 | E1.F7.T1, E1.F7.T4 |
| 041 | E1.F7.T1, E1.F7.T5 |
| 042 | E1.F3.T2, E1.F8.T2, E1.F8.T3 |
| 043 | E1.F2.T1, E1.F2.T4, E1.F3.T3, E1.F4.T4, E1.F5.T7, E1.F8.T2 |
| 044 | E1.F8.T2, E1.F8.T4 |
| 045 | E1.F8.T2, E1.F8.T5, E1.F8.T6, E1.F9.T2, E1.F9.T6 |
| 046 | E1.F8.T2, E1.F8.T7 |
| 047 | E1.F8.T2, E1.F8.T8 |
| 048 | E1.F8.T1, E1.F8.T2, E1.F8.T9 |
| 049 | E1.F8.T1, E1.F8.T2 |
| 050 | E1.F8.T2, E1.F8.T9 |
| 051 | E1.F8.T2, E1.F8.T6, E1.F8.T10 |
| 052 | E1.F9.T3, E1.F9.T4, E1.F9.T5, E1.F9.T7 |
| 053 | E1.F9.T1, E1.F9.T7 |
| 054 | E1.F4.T2, E1.F4.T6 |
| 055 | E1.F3.T1, E1.F3.T7 |
| 056 | E1.F3.T1, E1.F3.T7 |
| 057 | E1.F3.T1, E1.F3.T4, E1.F3.T7 |

MODIFIED living requirements: **REQ-W2-060** (the traceability matrix) → E1.F6.T2, E1.F6.T3 (with REQ-MC-036, 037); **REQ-LD-022** (the frontend-module template) → E1.F8.T6 (with REQ-MC-046). `karvey-trace.py mockup-conformance` counts 59 requirements: 57 REQ-MC + these two.

**Coverage:** 57/57. No REQ-MC is left without a task. Every component of the architecture's file plan (§1.2) has a task: `karvey-mockup.py` (check, assign, propose), `karvey-conformance.py` (plan, request, verify-captures, compare, status); `karvey_lib/mockup.py`, `deviations.py` and the `conformance/` package (`__init__`, `png`, `imgdiff`, `render`, `elements`, `textdiff`, `plan`, `captures`); the probe and its three schemas; `vocabulary.json`, `approval.py`, `guards.py`, `karvey-hook.sh`; `check-modes.json`, `modes.py`, both schemas; `karvey-state.py` (`mockup`, `deviation`, blockers, hashes, `check-prod`), `karvey-context.py`, `karvey-trace.py`, `karvey-release-gate.py`; `components.py`, `component-kinds.json`, the frontend-module template; the upgrade catalogue rows; `lint-plugin.py` (L-82..L-87); the rule, `targets.md`, the fiscal rubric and the nine skill texts; the READMEs; the fixtures and manual scripts (§6).

## Totals and critical path

- **Tasks:** 69, of which 2 `[human]` and 67 agent tasks (53 Backend, 14 Test).
- **Total estimate:** 782 min ≈ 13.0 h of AI + review, calibrated. Per feature: F1 74 · F2 81 · F3 72 · F4 180 · F5 112 · F6 30 · F7 55 · F8 123 · F9 55.
- **Critical path by dependencies:** 192 min ≈ 3.2 h:
  E1.F9.T1 → E1.F1.T1 → E1.F1.T2 → E1.F1.T3 → E1.F1.T4 → E1.F4.T4 → E1.F4.T9 → E1.F4.T10 → E1.F4.T12 → E1.F5.T2 → E1.F5.T6 → E1.F5.T7 → E1.F5.T8 → E1.F9.T3 → E1.F9.T7.
  The `[human]` waits (the owner's deviation approval, the prod OK) and CI queue time are not counted.
- **Serial file spines** (not dependencies, but they serialise work): `lint-plugin.py` (8), `mockup.py` (14), `karvey-state.py` (13), `karvey-context.py` (2), `conformance/__init__.py` (8), `karvey-conformance.py` (3). With one agent the realistic wall time is the total; with parallel agents the floor is the critical path plus the `karvey-state.py` spine.

## What proved impractical when breaking the architecture into tasks

1. **Nothing starts before `living-docs`.** E1.F9.T1 is a hard gate (REQ-MC-053): the confirm phrases, reviewed settings, component sheets and `4.2` modes this change extends do not exist in this branch yet. The plan can only be made ready.
2. **The size base belongs to F8 but must run first**, and its comparison last (`Split:` lines on E1.F9.T2 and E1.F9.T6).
3. **Some requirements sit in one Feature and are coded in another**: REQ-MC-018 (extra ids) in the F4 comparator, REQ-MC-055 and 056 (declared deviations) and 057 (`conflict open` at close) on the F5 deviation group, REQ-MC-043 (which gate holds which check) across the three blocker tasks; their tasks carry `Split:` lines or name 043 explicitly.
4. **No browser in CI.** The web end-to-end runs on pre-rendered captures and probes; the real-browser run and the owner's phrase are the manual E2E (E1.F9.T5, `[human]`), which is also the only place REQ-MC-016 is exercised on a UI built by the impl skill.
