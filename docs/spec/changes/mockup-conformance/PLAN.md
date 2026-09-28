# Plan: mockup-conformance

**Capability:** method | **Security Tier:** 3 | **Layers:** Backend
**Created:** 2026-09-27 | **Status:** 🔄 tasks (merged *how* gate pending)
**Lane:** standard (this repository has no UI; mockup and design-graphic skipped by the lane — the change is proven on fixture UI projects, REQ-MC-052)
**Release target:** 4.3.0 (minor, backward compatible with 4.2.0)
**Flow:** trunk (`feature/mockup-conformance` → PR → `main`) · **Decision:** D-40 (D-01, D-20, D-21, D-22, D-24, D-30, D-38 hold)
**Sequencing:** spec phases now; implementation after `living-docs`' implementation (REQ-MC-053)

---

## Epic: Mockup conformance — what is built matches the approved mockup, one to one

### Description
The owner approves a navigable mockup, and the build drifts from it: implementation works from requirements,
architecture and tasks without the mockup as an input; mockup and requirements are compared only before
implementing; after implementing, QA's visual audit compares the build with the design specification, not with the
mockup, and is settled by a glance; decisions taken while iterating the mockup do not always return to the
requirements. This Epic gives every mockup element a stable id tied to its requirements and writes iteration
decisions back before approval; makes the approved mockup, frozen by hash, a mandatory input of implementation that
keeps the same ids; adds a blocking conformance gate (presence of every element, side-by-side captures at the same
viewport and state with a marked, thresholded difference, every difference a deviation approved by the owner through
the hook); and extends the traceability matrix to requirement → element → test → evidence before release.

North star: *the UI a change ships is the UI the owner approved in its mockup — every approved element present under
the same id, every visible difference fixed or approved by the owner through the hook, every UI requirement traced to
its elements, tests and evidence before the release gate opens.*

### Strategic value
Rework found after release in three applications built with the method (D-40). An approval that binds what ships
turns the mockup from a sketch into a contract, moves the discovery of a difference from the owner's eyes after
release to a measured report before it, and keeps the requirements as complete as the mockup the owner agreed to.

### Design decisions
| Topic | Decision |
|------|----------|
| Scope | D-40 — element ids + decisions written back (mockup); approved mockup as mandatory impl input; blocking conformance gate with owner-approved deviations; traceability matrix to evidence |
| Trust model | D-01 — a deviation approval comes only from the owner's confirm phrase, written by the hook as a one-use marker; thresholds and storage settings read from the reviewed line |
| Architecture | `architecture.md` — element contract + `karvey-mockup.py` (check, assign, propose); decision log and *what*-gate blockers in the state tool; mockup hash at mockup and design approvals; tasks `Elements:` lines and a generated conformance plan; capture separate from comparison (`browse.via` side writes images + probes + manifest; `karvey-conformance.py` verifies and compares with a standard-library PNG codec); report recomputed at every gate; deviations with a hook-written marker and a per-clone ledger; release blockers in approve, approve-gate, `check-prod` and the release-gate script; traceability columns; check modes 4.3; upgrade steps MC-1..MC-3; architect decisions A-01..A-15 for the owner to confirm at the *how* gate; infra skipped (no cloud) |

---

## Features

| Feature | Area | Requirements covered | Status |
|---------|------|----------------------|--------|
| F1 | Element ids in the mockup: required kinds, format and uniqueness, requirement attribute, UI coverage, deterministic element check and map, stability across iterations, preserved by design-graphic | REQ-MC-001..007 | ⬜ |
| F2 | Decisions written back: decision log, resolution into requirement revisions, approval refusal, captured-instruction link, frozen mockup hash, revisions shown at the gate | REQ-MC-008..013 | ⬜ |
| F3 | Implementation from the mockup: mandatory input, tasks name elements, the mockup as primary source of structure, layout, content and style and the requirements of behaviour (equal or better, never different — D-42), stack-forced differences and improvements declared when made, requirement/mockup conflicts asked to the owner, same ids in the build, no invented elements | REQ-MC-014..018, 055..057 | ⬜ |
| F4 | Conformance gate: plan, viewports, presence, same viewport and state, marked difference, text and style differences, pixel threshold, unmeasured pairs, browse settings, no production, evidence bound to the commit, capture storage | REQ-MC-019..029, 054 | ⬜ |
| F5 | Mockup deviations: every difference an entry, resolutions, owner approval through the hook, QA / release / deploy refusal, gate summary, QA's visual audit | REQ-MC-030..035 | ⬜ |
| F6 | Traceability matrix to evidence, complete before release | REQ-MC-036, 037 | ⬜ |
| F7 | Targets: web, mobile and desktop, command line, others out of scope by name | REQ-MC-038..041 | ⬜ |
| F8 | Integration: lanes, gates, design system, load lists and size, frontend-module sheets, upgrade steps MC-1..MC-3, changes past their mockup, check modes, backward compatibility, documentation | REQ-MC-042..051 | ⬜ |
| F9 | Change-scoped: dogfooding on fixture projects, implementation after living-docs | REQ-MC-052, 053 | ⬜ |

## Tasks

Detail per task (files, requirements, tests, done-when command) in `tasks.md`. Estimates are calibrated to realistic AI execution + review (the default scale ran ~10× high in this repo). 69 tasks (67 agent, 2 `[human]`), 782 min total, critical path 192 min. Execution order: E1.F9.T1 (base after living-docs) → E1.F9.T2 (size base) + E1.F8.T1 (modes) → failing suites per feature → F1 → F2 → F3 and F4 → F5 → F6, F7 → F8 → F9 end-to-end, owner's approval in the E2E, size, whole-repo gate → E1.DEPLOY.

### Feature E1.F1: Element ids in the mockup: contract, parser, rules, surface coverage, deterministic map, history and renames, design keeps ids

- [ ] E1.F1.T1 [Test] Web fixture `tests/fixtures/conformance/web/` (fictional invoice list: `requirements.md` with `Surface:` lines, `mockup.html` with ids, a repeat, a dynamic date, empty and export-error states) + failing `test_mockup_check.py` for REQ-MC-001..006 — est: 12min (depends E1.F9.T1) (P)
- [ ] E1.F1.T2 [Backend] `karvey_lib/mockup.py` parser (`html.parser`, `file:line:col` + CSS-like path) and element rules: required kinds (tag/ARIA inference, `data-mk-kind`), id pattern, ≤ 48 chars, digit run ≥ 6, `secret` leak pattern, duplicates vs `data-mk-repeat`, `data-mk-req` ids or `gap` — est: 15min (depends E1.F1.T1)
- [ ] E1.F1.T3 [Backend] Surface and coverage: `Surface: ui|none` read from `requirements.md` trace lines (`surface missing`), uncovered `ui` requirements, elements citing `none`, living-spec requirements counted `ui` for the element and outside coverage — est: 10min (depends E1.F1.T2)
- [ ] E1.F1.T4 [Backend] `karvey-mockup.py check <change>`: deterministic `mockup-map.json` (kind, screen, state, parent, order, text, reqs, repeat, instances, dynamic, path, file hashes), exit codes, `--json`; `generated mockup` refuses `element check not run` when the map's file hashes do not match — est: 15min (depends E1.F1.T3)
- [ ] E1.F1.T5 [Backend] History: `mockup-map.prev.json`, `history.removed`, `--rename old=new`, `history.retired` across all iterations (reuse refused), unlogged-change list (added, removed, text or requirement changed) for REQ-MC-008 — est: 12min (depends E1.F1.T4, E1.F2.T1)
- [ ] E1.F1.T6 [Backend] Design-graphic keeps the ids: `approve design_graphic` runs the element check and refuses a lost or changed id without a rename (`filter-status`); `karvey-design-graphic` skill text: keep attributes, re-run the check, tokens by name — est: 10min (depends E1.F1.T5, E1.F2.T4, E1.F1.T1)

### Feature E1.F2: Decisions written back: decision log, resolution against revision_history, what-gate blockers, instruction link, mockup hash, gate summary

- [ ] E1.F2.T1 [Test] Failing `test_mockup_log.py` for REQ-MC-008..011, 013, 043 (add/resolve, hand edit, revision link, blockers, instruction link, dismissals and revisions in the summary, gate mapping) — est: 10min (depends E1.F9.T1) (P)
- [ ] E1.F2.T2 [Backend] `karvey-state.py mockup decision add|list`: `mockup-log.md` written only by the tool (fixed header, `MD-NN`, iteration, origin owner|agent, quote ≤ 200 chars leak-checked or `F-NN`, elements, `unresolved`), `spec.json:mockup.log_sha256` under the state lock; `validate` reports `decision log not written by the state tool` — est: 15min (depends E1.F2.T1, E1.F8.T1)
- [ ] E1.F2.T3 [Backend] `mockup decision resolve`: `requirement-revision --reqs … --revision <at>` checked against `revision_history` (entry exists, names the MD id, requirement ids exist) or `no-spec-impact --reason` (≥ 10 chars) — est: 12min (depends E1.F2.T2)
- [ ] E1.F2.T4 [Backend] `mockup.gate_blockers`: element-check errors, unresolved rows, missing revision entries, requirements gone, unlogged element changes; wired in `cmd_approve` (mockup, design_graphic), `cmd_approve_gate` (gates covering them) and `compute_next` — est: 12min (depends E1.F2.T3, E1.F1.T5)
- [ ] E1.F2.T5 [Backend] Captured-instruction link: an `instruction` row captured in `mockup` and classified `requirement-revision` must be cited by an MD row (`instructions.read_rows` of `living-docs`); blocker cause names `F-NN` — est: 8min (depends E1.F2.T4)
- [ ] E1.F2.T6 [Backend] Mockup hash: `approvals.<phase>.artifact_sha256` and `spec.json:mockup.{hash, map_sha256, approved_under}` written at `approve mockup` and `approve design_graphic`; `validate` reports `mockup changed after approval` — est: 12min (depends E1.F2.T4, E1.F8.T1, E1.F2.T1)
- [ ] E1.F2.T7 [Backend] *Mockup decisions* gate-summary block (revisions with REQ and MD ids, then `no-spec-impact` with reasons) and the approval `ref` composed with the MD ids; summary refuses to present when a revision lacks its MD — est: 12min (depends E1.F2.T3) (P)

### Feature E1.F3: Implementation from the mockup: impl refusal, Elements lines, impl and tasks text (mockup first, requirements for behaviour — D-42), strip setting, extra ids, declared deviations (forced, improvement), conflicts asked

- [ ] E1.F3.T1 [Test] Failing cases for F3 in `test_mockup_hash.py` (impl refusal, lane raise), `test_tasks_elements.py` (Elements lines, assignment), `test_conformance_settings.py` (strip setting), `test_lint_mc.py` (impl and tasks text anchors), `test_deviations.py` (declared deviations: forced and improvement; conflict open at close) — est: 10min (depends E1.F9.T1) (P)
- [ ] E1.F3.T2 [Backend] `advance … impl` on a UI change: refuse `mockup not approved` and `mockup changed after approval`; warn `mockup hash absent (approved before 4.3)` for a 4.2 approval; a lane raised to `feature-ui` without a mockup is refused — est: 10min (depends E1.F2.T6, E1.F3.T1)
- [ ] E1.F3.T3 [Backend] `Elements:` line parsed next to `**Requirements:**` (`karvey-trace.py parse_tasks`); `karvey-mockup.py assign <change>` lists ids in no task and unknown ids; `approve tasks` / `approve-gate how` refuse on either — est: 12min (depends E1.F1.T4, E1.F3.T1, E1.F8.T2)
- [ ] E1.F3.T4 [Backend] Skill text: `karvey-tasks` (Elements lines, one presence `[Test]` task per screen before its first UI task, plan build side) and `karvey-impl` (Step 1 reads the map and mockup files; source order — the approved mockup for structure, layout, content and style, the requirements for behaviour, equal or better never different (D-42); parent, order, text, states, tokens per element; same ids; declare forced differences and improvements; on a requirement/mockup conflict stop, ask the owner and record a `spec-gap` finding; presence test at task close); L-87 anchors for both — est: 14min (depends E1.F3.T3, E1.F8.T6)
- [ ] E1.F3.T5 [Backend] `conformance.strip_in_production` read from the reviewed line only (working copy ignored and audited); the gate never strips — est: 8min (depends E1.F4.T1, E1.F3.T1) (P)
- [ ] E1.F3.T6 [Backend] `extra` ids: build-probe ids not in the approved map reported and counted as differences needing a deviation — est: 8min (depends E1.F4.T6, E1.F3.T1)
- [ ] E1.F3.T7 [Backend] `karvey-state.py deviation add … --origin impl --kind forced|improvement` (REQ-MC-055, 056): an improvement needs `--better` and its side-by-side image, owner rejection → `fix-build`; the task summary names it; entries found later carry origin `gate`, kind `found`, and the metrics count undeclared-at-impl; `compare --presence-only` exits non-zero with `conflict open: F-NN` while an open `spec-gap` names an element of the entry (REQ-MC-057) — est: 10min (depends E1.F5.T2, E1.F3.T1)

### Feature E1.F4: Conformance gate: settings, codec, plan, probe, elements, pixels, side-by-side, request, captures, browse, report and recomputation, storage

- [ ] E1.F4.T1 [Backend] `project.schema.json:conformance` (viewport string pattern, devices, `pixel_threshold` percent, `pixel_tolerance` fraction, `box_tolerance_px`, `captures`, `ui_paths`, `cli_command` argv, `terminal_width`, `strip_in_production`, `dev_hosts`, `forbid`) + reviewed-line reader for every gate value — est: 12min (depends E1.F9.T1, E1.F4.T2) (P)
- [ ] E1.F4.T2 [Test] Pre-rendered web captures and probes for the fixture (mockup and build sides at 1280×800 and 390×844; one moved button, one changed label, one hidden element at phone width) + failing `test_conformance_compare.py` — est: 15min (depends E1.F1.T1) (P)
- [ ] E1.F4.T3 [Backend] `conformance/png.py`: decode 8-bit RGB/RGBA non-interlaced, filters 0–4, header dimensions checked before inflation, inflation bounded to `w × h × 4 + h`; encode RGBA filter 0; unsupported → `unmeasured (unsupported image)` — est: 15min (depends E1.F4.T2) (P)
- [ ] E1.F4.T4 [Backend] `conformance/plan.py` + `karvey-conformance.py plan`: entries per screen and state from the map, every id in ≥ 1 entry (`unplanned: <id>`), closed step vocabulary, fixture keys resolved from `fixtures.json` (≤ 200 printable chars, leak-checked), viewports from settings — est: 15min (depends E1.F4.T1, E1.F1.T4, E1.F4.T2, E1.F8.T2)
- [ ] E1.F4.T5 [Backend] Probe contract: `templates/conformance/mk-probe.js` (reads `data-mk`, boxes, text, computed styles, visibility, the `karvey-build` meta; disables animation and caret) + `request`, `manifest`, `probe` schemas; L-84 (no write API in the probe) — est: 15min (depends E1.F9.T1, E1.F4.T2, E1.F7.T1) (P)
- [ ] E1.F4.T6 [Backend] `conformance/elements.py`: present / missing / hidden per entry and viewport, box Δ, text (whitespace-normalised, approved dynamic excluded) and style (colour, font size ±0.5 px, weight) differences, `unapproved dynamic marker` — est: 15min (depends E1.F4.T2, E1.F4.T5)
- [ ] E1.F4.T7 [Backend] `conformance/imgdiff.py`: masking of approved dynamic boxes on both sides, per-pixel distance vs `pixel_tolerance`, ratio vs `pixel_threshold` (percent), box tolerance, `over threshold` — est: 15min (depends E1.F4.T3, E1.F4.T6)
- [ ] E1.F4.T8 [Backend] `conformance/render.py`: side-by-side PNG (mockup | build | overlay: build dimmed, differing pixels red, outlined elements); size mismatch → side-by-side only and `unmeasured (size differs)` — est: 15min (depends E1.F4.T7)
- [ ] E1.F4.T9 [Backend] `karvey-conformance.py request`: `request.json` from the plan, reviewed base URL (host in `dev_hosts`, not a production environment, not in `forbid`; empty allow-list refused) or CLI argv, build commit, mockup hash, probe hash, fixture user by name; leak-checked — est: 12min (depends E1.F4.T4, E1.F4.T5, E1.F4.T2)
- [ ] E1.F4.T10 [Backend] `karvey-conformance.py verify-captures`: manifest vs files (hash, size caps), manifest vs request (entry, viewport, commit, mockup hash, probe hash), PNG dimensions vs viewport × ratio, `karvey-build` meta vs commit (`unverified` / `build commit unproven`) — est: 12min (depends E1.F4.T9, E1.F4.T3)
- [ ] E1.F4.T11 [Backend] `karvey-browse` skill text: run a conformance request `local` (environment's automation, examples only), `agent:<name>` (self-contained instruction from the request, files and manifest back into `captures/`), `none` (nothing, `not evaluated`) — est: 8min (depends E1.F4.T9) (P)
- [ ] E1.F4.T12 [Backend] `karvey-conformance.py compare`: `report.json` + `report.md` (commit, mockup hash, reviewed settings, results per entry, images with hashes); text layers leak-checked; staleness (`status`: UI-code commits via the component map → `ui_paths` → outside `docs/`, or mockup hash changed); recomputation function used by the gate — est: 15min (depends E1.F4.T8, E1.F4.T10, E1.F4.T2)
- [ ] E1.F4.T13 [Backend] Capture storage: `captures: commit` (under the change) or `local` (`<state>/conformance/<change>/`, report keeps hashes); `capture missing: <name>` at a gate — est: 8min (depends E1.F4.T12, E1.F4.T2)
- [ ] E1.F4.T14 [Test] No-network and read-only AST test over `karvey-mockup.py`, `karvey-conformance.py`, `karvey_lib/{mockup,deviations}.py`, `karvey_lib/conformance/` (no `socket`, `urllib`, `http.client`; `subprocess` only git and `run_streamed`) — est: 8min (depends E1.F4.T12) (P)

### Feature E1.F5: Mockup deviations and the owner's approval: entries, resolutions, phrase, marker, ledger, release blockers, gate summary, QA text

- [ ] E1.F5.T1 [Test] Failing `test_deviations.py` and `test_deviation_approval.py` + hook table `deviation-confirm.json` (five languages, lists, ranges, 11 ids, quoted phrase, agent-shaped text, protect-paths cases) — est: 12min (depends E1.F9.T1) (P)
- [ ] E1.F5.T2 [Backend] `karvey_lib/deviations.py` + `karvey-state.py deviation add|update|list` (`## Mockup deviations`, fixed block, only the tool writes) and `deviation add --from-report` (coverage of every report finding; one entry per screen for `unmeasured`) — est: 15min (depends E1.F5.T1, E1.F4.T12)
- [ ] E1.F5.T3 [Backend] Resolutions: `fix-build` closes `fixed` only in a recomputation where the difference is gone; `revise-mockup` hands a spec-revision to `/karvey-iterate` (`reopen … mockup`) and closes after re-approval + a passing run; hand-set status reported — est: 10min (depends E1.F5.T2)
- [ ] E1.F5.T4 [Backend] Vocabulary `confirm.deviation` (en, es, pt, de, fr) + `classify_confirm` extension (1–10 `DV-NN`, no ranges, notice when not recorded); L-85 — est: 12min (depends E1.F5.T1) (P)
- [ ] E1.F5.T5 [Backend] Hook side: transcript cross-check of the phrase, entry hashes from `deviations.md` (≤ 256 KB, read-only), one-use marker `approvals/confirm/deviation-<change>.json`, echo of bound titles/Differs/short hashes, audit record; needles `karvey/deviations` and the confirm directory in `STATE_NEEDLES` and `karvey-hook.sh` — est: 15min (depends E1.F5.T4)
- [ ] E1.F5.T6 [Backend] `deviation approve <change>`: consume the marker (≤ 30 min), re-hash, `accepted (owner, <at>)`, protected ledger + tracked `deviation_log`; verification at every blocker call: ledger ↔ audit ↔ text (tampered / void), other clone or CI `accepted (not verifiable here)` listed — est: 15min (depends E1.F5.T5, E1.F5.T2)
- [ ] E1.F5.T7 [Backend] `conformance.gate_blockers` (recompute the report, stale, not evaluated, uncovered, pending, tampered, unverified) in `cmd_approve` (qa, prod), `cmd_approve_gate` (release), `check-prod` (prod-gate hook) and `karvey-release-gate.py item_conformance`; modes from the registry — est: 15min (depends E1.F5.T6, E1.F4.T12, E1.F8.T1)
- [ ] E1.F5.T8 [Backend] *Conformance* block in the release (or granular qa) gate summary: counts per result, pending deviations with side-by-side paths, `capture missing`, report path and commit, bound short hashes, `not verifiable here` entries — est: 10min (depends E1.F5.T7) (P)
- [ ] E1.F5.T9 [Backend] `karvey-qa` Dimension 8 cites the report (else `not evaluated`), keeps the design-spec and platform audit; `rules/judges/qa.md` fiscal question on conformance claims; L-87 anchors — est: 8min (depends E1.F5.T7, E1.F3.T4, E1.F5.T1) (P)

### Feature E1.F6: Traceability to evidence: element columns, empty-cell refusal

- [ ] E1.F6.T1 [Test] Failing `test_trace_elements.py` (columns per requirement, `n/a (target api)`, empty cell refusal) — est: 8min (depends E1.F9.T1) (P)
- [ ] E1.F6.T2 [Backend] `karvey-trace.py build/render`: elements, entries and conformance result per requirement of a UI change; generated block drift unchanged — est: 12min (depends E1.F6.T1, E1.F4.T12, E1.F3.T3)
- [ ] E1.F6.T3 [Backend] `karvey-trace.py check`: empty cell of a `ui` requirement fails; `n/a (target <t>)` accepted; release-gate item reads it — est: 10min (depends E1.F6.T2, E1.F5.T7)

### Feature E1.F7: Targets: web, native (mobile and desktop), CLI, other targets

- [ ] E1.F7.T1 [Test] Failing target cases in `test_targets.py` + CLI fixture `tests/fixtures/conformance/cli/` (transcript mockup with `[mk:…]` anchors and restricted patterns; a tiny fixture module whose output differs in one anchor) — est: 10min (depends E1.F9.T1) (P)
- [ ] E1.F7.T2 [Backend] Web rules: presence from the rendered document incl. visibility, pixel diff on; `rules/targets.md` rows (element id and capture per target) — est: 8min (depends E1.F7.T1, E1.F4.T6)
- [ ] E1.F7.T3 [Backend] Native: accessibility-dump → probe converter contract (documented shape, schema-validated), no tree → `not evaluated` needing a deviation, pixel diff only at equal sizes; manual `tests/manual/conformance-native.md` — est: 12min (depends E1.F7.T1, E1.F4.T8)
- [ ] E1.F7.T4 [Backend] CLI: transcript parser (`[mk:<id>]`, anchors, restricted patterns checked by the element check), runner through `run_streamed` with a minimal environment and 30 s timeout, `textdiff.py` normalisation and per-block diff, transcript leak check — est: 15min (depends E1.F7.T1, E1.F1.T4)
- [ ] E1.F7.T5 [Backend] Other targets: `not applicable: target <t>` written to the report (satisfies the release blocker, matrix `n/a`); `target undeclared` refused — est: 10min (depends E1.F7.T1, E1.F5.T7)

### Feature E1.F8: Integration: check modes, lanes, gates, tokens, rule and load lists, skill texts, frontend sheets, upgrade steps, compatibility, documentation

- [ ] E1.F8.T1 [Backend] Check-mode registry: `4.3` column and the 23 rows of architecture §1.16 (21 blocking-when-4.3, `conformance.production` blocking always, `sheet.elements` and `design.token` warn); resolver reads `spec.json:mockup.approved_under` with the absent-value rules (neither → warn; one of two → blocking + `validate` error); L-83 — est: 15min (depends E1.F9.T1, E1.F8.T2)
- [ ] E1.F8.T2 [Test] Failing cases for F8 in `test_modes_mc.py` (lanes, compatibility), `test_conformance_compare.py` (tokens), `test_sheet_elements.py`, `test_upgrade_mc.py`, `test_lint_mc.py` (L-82, L-86, L-87 for mockup/test/deploy/archive) — est: 10min (depends E1.F9.T1) (P)
- [ ] E1.F8.T3 [Backend] Lane scoping: every check silent outside UI changes except `sheet.elements`; a lane raise makes them pending with the raised phases — est: 8min (depends E1.F5.T7, E1.F2.T4)
- [ ] E1.F8.T4 [Backend] Tokens: build computed values matched to design-system tokens (`designsys.resolved`), `undeclared token` (warn), style differences on resolved values — est: 10min (depends E1.F4.T6, E1.F8.T2) (P)
- [ ] E1.F8.T5 [Backend] `rules/mockup-conformance.md` (≤ 900 words: element contract, decision duty, probe per target, deviation phrase, gate order) + `Load:` of the eight acting skills; L-82 — est: 15min (depends E1.F9.T2)
- [ ] E1.F8.T6 [Backend] Skill texts `karvey-mockup` (ids on generation, check each iteration, decision log, `--rename`, gap routing), `karvey-test` (request → browse → verify → compare → deviations → trace), `karvey-deploy` (blockers first), `karvey-archive` (sheet merge); L-87 anchors — est: 15min (depends E1.F8.T5)
- [ ] E1.F8.T7 [Backend] Frontend-module sheets: `Mockup elements` section in `component-kinds.json` and the template; archive merge of the map into module sheets; `components --check --commits` warns when an id listed in a sheet is removed without the sheet (every lane) — est: 15min (depends E1.F1.T4, E1.F9.T1, E1.F8.T2) (P)
- [ ] E1.F8.T8 [Backend] Upgrade steps `mc-1-settings`, `mc-2-mockup-ids` (human; `karvey-mockup.py propose` writes `mockup.proposed.html`), `mc-3-capture` (report only) with the seven fields, idempotent, upgrade branch only — est: 15min (depends E1.F4.T1, E1.F1.T4, E1.F8.T2) (P)
- [ ] E1.F8.T9 [Test] Backward compatibility: 4.2 fixture projects (only `standard` changes; a UI change approved under 4.2) give identical validate/lint/gate results; hand-written unknown key still an error — est: 10min (depends E1.F5.T7, E1.F8.T1)
- [ ] E1.F8.T10 [Backend] Plugin README section (settings, both scripts, the phrase, MC-1..MC-3) + `hooks/README.md` (deviation phrase); L-86 — est: 10min (depends E1.F8.T8, E1.F5.T5)

### Feature E1.F9: Change-scoped: base after living-docs and size base (first); fixture dogfooding, owner's approval in the E2E, size and whole-repo gate (last)

- [ ] E1.F9.T1 [Test] Base check: `living-docs`' implementation is in this branch's base (its last task's commit is an ancestor; `karvey_lib/components.py`, `instructions.py`, the confirm markers, the `4.2` check-mode column and `--fail-growth` exist); rebase; walk the architecture §13 list and note moved lines in the PLAN history — est: 8min
- [ ] E1.F9.T2 [Backend] Size base snapshot `docs/spec/retros/context-size-4.3.0-base.json` in a commit of its own, before any rule or skill edit of this change — est: 6min (depends E1.F9.T1, E1.F8.T2)
- [ ] E1.F9.T3 [Test] `test_fixture_web_e2e.py`: the web fixture end to end (element check, decisions, assignment, plan, pre-rendered captures, verify, compare, deviations, matrix) asserting AC-1..AC-8, including text/token equality (REQ-MC-016) and QA `not evaluated` without a report (REQ-MC-035) — est: 15min (depends E1.F5.T8, E1.F6.T3, E1.F3.T7)
- [ ] E1.F9.T4 [Test] `test_fixture_cli_e2e.py`: the CLI fixture end to end (AC-9) and an `api` target reporting `not applicable` — est: 12min (depends E1.F7.T4, E1.F7.T5) (P)
- [ ] E1.F9.T5 [human] The owner approves a deviation in the manual E2E on the web fixture (`tests/manual/conformance-e2e.md`): real captures where `browse.via` allows, one deliberate difference, and the owner's own phrase — executor: the owner (depends E1.F9.T3, E1.F4.T11)
- [ ] E1.F9.T6 [Backend] Size comparison against the base snapshot: `karvey-context-budget.py compare --fail-growth 10`; result in the PLAN history — est: 6min (depends E1.F8.T6, E1.F8.T10, E1.F5.T9, E1.F3.T4)
- [ ] E1.F9.T7 [Test] Whole-repo gate: all unit suites, hook tables, `lint-plugin.py` 0 errors, `validate --all`, `karvey-trace.py mockup-conformance --check` 57/57 + 2 MODIFIED — est: 8min (depends E1.F9.T3, E1.F9.T4, E1.F9.T6, E1.F8.T9)

### E1.DEPLOY

- [ ] E1.DEPLOY.T1 [human] The prod OK for the release that ships this change (D-10) — executor: the owner (depends E1.F9.T7, E1.F9.T5)

### Status

| Task | Status | estimate_min | actual_ai_min | actual_review_min | Notes |
|------|--------|--------------|---------------|-------------------|-------|
| E1.F1.T1 [Test] | ⬜ todo | 12 | — | — |  |
| E1.F1.T2 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F1.T3 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F1.T4 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F1.T5 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F1.T6 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F2.T1 [Test] | ⬜ todo | 10 | — | — |  |
| E1.F2.T2 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F2.T3 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F2.T4 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F2.T5 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F2.T6 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F2.T7 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F3.T1 [Test] | ⬜ todo | 10 | — | — |  |
| E1.F3.T2 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F3.T3 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F3.T4 [Backend] | ⬜ todo | 14 | — | — |  |
| E1.F3.T5 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F3.T6 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F3.T7 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F4.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T2 [Test] | ⬜ todo | 15 | — | — |  |
| E1.F4.T3 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T4 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T5 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T6 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T7 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T8 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T9 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T10 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T11 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F4.T12 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T13 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F4.T14 [Test] | ⬜ todo | 8 | — | — |  |
| E1.F5.T1 [Test] | ⬜ todo | 12 | — | — |  |
| E1.F5.T2 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F5.T3 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F5.T4 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F5.T5 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F5.T6 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F5.T7 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F5.T8 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F5.T9 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F6.T1 [Test] | ⬜ todo | 8 | — | — |  |
| E1.F6.T2 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F6.T3 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F7.T1 [Test] | ⬜ todo | 10 | — | — |  |
| E1.F7.T2 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F7.T3 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F7.T4 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F7.T5 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F8.T1 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F8.T2 [Test] | ⬜ todo | 10 | — | — |  |
| E1.F8.T3 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F8.T4 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F8.T5 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F8.T6 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F8.T7 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F8.T8 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F8.T9 [Test] | ⬜ todo | 10 | — | — |  |
| E1.F8.T10 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F9.T1 [Test] | ⬜ todo | 8 | — | — |  |
| E1.F9.T2 [Backend] | ⬜ todo | 6 | — | — |  |
| E1.F9.T3 [Test] | ⬜ todo | 15 | — | — |  |
| E1.F9.T4 [Test] | ⬜ todo | 12 | — | — |  |
| E1.F9.T5 [human] | ⬜ todo | — | — | — | human |
| E1.F9.T6 [Backend] | ⬜ todo | 6 | — | — |  |
| E1.F9.T7 [Test] | ⬜ todo | 8 | — | — |  |
| E1.DEPLOY.T1 [human] | ⬜ todo | — | — | — | human |

`estimate_min` is written here once; impl fills the two actual columns and never edits the estimate.

## History
| Date | Phase | Action |
|-------|------|--------|
| 2026-09-27 | init | Change initialised (lane standard, Tier 3, D-40) |
| 2026-09-27 | requirements | 55 EARS requirements (51 ADDED, 2 MODIFIED living blocks through REQ-MC-036/046, 2 change-scoped); judges domain + methods (intra-model, concerns) — 31 findings routed in place pre-approval (30 accepted, F-29 partly rejected with reason); merged *what* gate pending |
| 2026-09-27 | requirements | merged *what* gate approved (D-21, commit `1eb6e9c`) |
| 2026-09-27 | mockup, design_graphic | skipped by the lane (standard: this repository has no UI; proven on fixture UI projects, REQ-MC-052) |
| 2026-09-27 | architecture | `architecture.md` + `risks.md` (R-1..R-11) generated; 19 components, 55/55 REQ-MC covered, component delta (5 MODIFIED), §13 integration after living-docs; judges security + methods (intra-model, concerns) — 23 findings (F-32..F-54) accepted and fixed in place pre-approval |
| 2026-09-27 | infra | skipped: no cloud (`cloud.provider = none`); CI runs the new suites in its existing test step (architecture A-13) |
| 2026-09-27 | tasks | `tasks.md`: 69 tasks (67 agent, 2 `[human]`), 778 min calibrated, critical path 192 min; 57/57 requirements traced (55 REQ-MC + 2 MODIFIED), test-first for every requirement; merged *how* gate pending |
| 2026-09-28 | iterate (spec revision) | Owner instruction D-42 (finding F-55, `instruction` → `spec-gap`): with an approved mockup the build is based on the mockup **and** the documented specs — equal or better, never different. `reopen requirements` through the state tool (approvals of requirements, architecture and tasks moved to `revision_history`; iteration 1). Rewritten in place: REQ-MC-016 (the approved mockup is the primary source of structure, layout, content and style; the requirements give the behaviour; an undeclared difference blocks), REQ-MC-030 (deviation kind and the reason an improvement is better), REQ-MC-055 (kind `forced`); added REQ-MC-056 ("better" = a declared improvement the owner approves with side-by-side evidence, else `fix-build`) and REQ-MC-057 (a requirement/mockup conflict is asked to the owner, never resolved silently). Ripple: `spec-delta.md` (ADDED 53), `architecture.md` §1.7, §1.12, §2.2, §6.1, §11 + revision history, `tasks.md` (E1.F3.T1, T4, T7; 57/57; 782 min; critical path unchanged 192 min). Mockup and design-graphic stay skipped by the lane. Owner re-approval of the *what* and *how* gates pending |
