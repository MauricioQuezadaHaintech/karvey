# Plan: project-upgrade

**Capability:** method | **Security Tier:** 2 | **Layers:** Backend
**Created:** 2026-09-25 | **Status:** 👀 QA re-run after karvey-iterate rev. 2 (every spec-gap closed, emergent deferred with reason; security gate PASS; QA approval is the owner's) — E1.F8.T4 (prod OK) is `[human]`
**Skipped (planned):** mockup, design_graphic (no UI), infra (no cloud)
**Release target:** the release right after 3.12.0 · **Flow:** trunk (`feature/project-upgrade` → PR → `main`) · **Decisions:** D-20

---

## Epic: Project upgrade — every plugin update ends in an offer

### Description
Updating Karvey never brings an existing project up to the new method. After this change, the first session
in a Karvey project after an update asks once (per clone) whether to build a project upgrade plan; the plan is
computed from the project's state, previewed, and only the picked steps are applied on a branch through one PR.

### Design decisions
| Topic | Decision |
|------|----------|
| Scope, release, who is asked | D-20 — separate change after 3.12.0; each person, per clone |

---

## Features

| Feature | Area | Requirements | State |
|---|---|---|---|
| F1 | The once-per-version offer (session hook) | REQ-UP-001..006 | ✅ impl |
| F2 | The plan (upgrade tool `plan`) | REQ-UP-007..010 | ✅ impl |
| F3 | Applying the plan (upgrade tool `apply`) | REQ-UP-011..019 | ✅ impl |
| F4 | Initial step catalogue | REQ-UP-020..026 | ✅ impl |
| F5 | The upgrade skill `/karvey-upgrade` | REQ-UP-027..029 | ✅ impl |
| F6 | Every release declares its upgrade (L-37, docs) | REQ-UP-030..032 | ✅ impl |

## Tasks

Detail per task (files, requirements, tests, done-when command) in `tasks.md`. Estimates are calibrated to realistic AI execution + review (the default scale ran ~10× high in this repo). 25 tasks (23 agent, 2 `[human]`), 262 min total, critical path 144 min.

### Feature E1.F1: Engine foundation — catalogue, Probe, plan, seen record

- [x] E1.F1.T1 [Backend] Catalogue contract: schema, `load_catalogue`, `CatalogueError`, empty `REGISTRY` — est: 12min
- [x] E1.F1.T2 [Backend] Read-only `Probe`, `StepResult`, `Edit`, overlay — est: 12min (depends E1.F1.T1)
- [x] E1.F1.T3 [Test] Fixtures `legacy-project` and `fake-home` (anonymised) — est: 8min (P)
- [x] E1.F1.T4 [Backend] `plan(root)` and `any_applicable(root, deadline)` — est: 12min (depends E1.F1.T2, E1.F1.T3)
- [x] E1.F1.T5 [Backend] Seen record: `read_seen`, `write_seen`, `VERSION_RE`, audit line — est: 8min (depends E1.F1.T4)

### Feature E1.F2: Apply engine

- [x] E1.F2.T1 [Backend] `apply` planning half: ids, values as data, selection, order, human/report, confinement, dry-run + preview id — est: 15min (depends E1.F1.T5)
- [x] E1.F2.T2 [Backend] `apply` write half: clean tree, CAS writes, stop at first failure, journal, audit — est: 12min (depends E1.F2.T1)
- [x] E1.F2.T3 [Backend] `ensure_branch` and `commit` — est: 12min (depends E1.F2.T2)

### Feature E1.F3: The initial step catalogue (8 steps)

- [x] E1.F3.T1 [Backend] `schema-migrate`, `schema-migrate-proposed` — est: 12min (depends E1.F1.T4, E1.F1.T3)
- [x] E1.F3.T2 [Backend] `legacy-shims` — est: 10min (depends E1.F3.T1)
- [x] E1.F3.T3 [Backend] `team-settings`, `enforcement-defaults` — est: 10min (depends E1.F3.T2)
- [x] E1.F3.T4 [Backend] `statusline-launcher`, `global-config`, `STABLE_STATUSLINE` — est: 10min (depends E1.F3.T3)
- [x] E1.F3.T5 [Backend] `changes-in-flight`; shipped catalogue complete — est: 8min (depends E1.F3.T4)

### Feature E1.F4: The upgrade tool

- [x] E1.F4.T1 [Backend] CLI `plan | branch | apply | commit | seen` — est: 15min (depends E1.F2.T3, E1.F1.T5)

### Feature E1.F5: The once-per-version offer (session hook)

- [x] E1.F5.T1 [Backend] `upgrade_offer()` in `session_text()`, `defaults.json` keys, bash degraded line — est: 15min (depends E1.F1.T5) (P)
- [x] E1.F5.T2 [Test] Session table ss-24..ss-35, runner `given.seen_version` — est: 15min (depends E1.F5.T1, E1.F3.T5, E1.F4.T1)

### Feature E1.F6: The upgrade skill

- [x] E1.F6.T1 [Backend] `skills/karvey-upgrade/SKILL.md`, orchestrator line, counts 18 → 19 — est: 10min (depends E1.F4.T1) (P)
- [x] E1.F6.T2 [Test] Manual script `tests/manual/upgrade-skill.md` — est: 8min (depends E1.F6.T1)

### Feature E1.F7: Linter, fingerprint and docs

- [x] E1.F7.T1 [Backend] L-38 and `--list` accepting `REQ-UP` claims — est: 12min (depends E1.F3.T5) (P)
- [x] E1.F7.T2 [Backend] `upgrade-surface.json`, `surface [--write]`, L-37 — est: 15min (depends E1.F7.T1, E1.F4.T1)
- [x] E1.F7.T3 [Backend] L-39 and the docs (READMEs, hooks README, versioning, deploy) — est: 15min (depends E1.F7.T2, E1.F5.T2, E1.F6.T1, E1.F3.T4)

### Feature E1.F8: Verification, release docs and the prod OK

- [x] E1.F8.T1 [Backend] Whole-repo gate and read-only dogfood plan — est: 8min (depends E1.F7.T3, E1.F6.T2, E1.F5.T2)
- [x] E1.F8.T2 [human] E2E offer → accept → PR on a throw-away repo + manual skill script — executor: owner; run headless by the maintainer agent under D-21 (depends E1.F8.T1)
- [x] E1.F8.T3 [Backend] Release docs: `[Unreleased]` declares the project upgrade — est: 8min (depends E1.F8.T2)
- [ ] E1.F8.T4 [human] Prod OK for the release (D-10), inside `karvey-deploy` — executor: owner (depends E1.F8.T3)

### Feature E1.F9: Iteration rev. 2 (karvey-iterate, 2026-09-26)

- [x] E1.F9.T1 [Backend] Steps: F-21 statusline note, F-22 archive, F-23 init defaults, F-28 one-line strings — est: 10min
- [x] E1.F9.T2 [Backend] F-08 remote upgrade branch as base, F-24 dry-run base check — est: 10min (depends E1.F9.T1)
- [x] E1.F9.T3 [Backend] F-25 bounded probe + watchdog, F-27 silent outside git — est: 8min (depends E1.F9.T2)
- [x] E1.F9.T4 [Backend] F-09 offer wording — est: 4min (depends E1.F9.T3)
- [x] E1.F9.T5 [Backend] F-26 L-38 scan — est: 8min (depends E1.F9.T1) (P)

---

## Task status
> Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked` · 🙋 `awaiting-human` (qualifier of `blocked`)

| Task | Status | estimate_min | actual_ai_min | actual_review_min | Notes |
|------|--------|--------------|---------------|-------------------|-------|
| E1.F1.T1 [Backend] | ✅ done | 12 | 7 | 0 |  |
| E1.F1.T2 [Backend] | ✅ done | 12 | 5 | 0 |  |
| E1.F1.T3 [Test] | ✅ done | 8 | 5 | 0 |  |
| E1.F1.T4 [Backend] | ✅ done | 12 | 5 | 0 |  |
| E1.F1.T5 [Backend] | ✅ done | 8 | 4 | 0 |  |
| E1.F2.T1 [Backend] | ✅ done | 15 | 9 | 0 |  |
| E1.F2.T2 [Backend] | ✅ done | 12 | 6 | 0 |  |
| E1.F2.T3 [Backend] | ✅ done | 12 | 7 | 0 |  |
| E1.F3.T1 [Backend] | ✅ done | 12 | 6 | 0 |  |
| E1.F3.T2 [Backend] | ✅ done | 10 | 8 | 0 |  |
| E1.F3.T3 [Backend] | ✅ done | 10 | 7 | 0 |  |
| E1.F3.T4 [Backend] | ✅ done | 10 | 7 | 0 |  |
| E1.F3.T5 [Backend] | ✅ done | 8 | 5 | 0 |  |
| E1.F4.T1 [Backend] | ✅ done | 15 | 8 | 0 |  |
| E1.F5.T1 [Backend] | ✅ done | 15 | 9 | 0 |  |
| E1.F5.T2 [Test] | ✅ done | 15 | 10 | 0 | done-when path: `plugins/karvey/hooks/tests/test-hooks.sh` (tasks.md names `tests/test-hooks.sh`) |
| E1.F6.T1 [Backend] | ✅ done | 10 | 6 | 0 |  |
| E1.F6.T2 [Test] | ✅ done | 8 | 4 | 0 |  |
| E1.F7.T1 [Backend] | ✅ done | 12 | 9 | 0 | F-01: since > plugin version = warning during [Unreleased] |
| E1.F7.T2 [Backend] | ✅ done | 15 | 10 | 0 | F-04: re-record the fingerprint if 3.12.0 ships first |
| E1.F7.T3 [Backend] | ✅ done | 15 | 9 | 0 |  |
| E1.F8.T1 [Backend] | ✅ done | 8 | 6 | 0 | gate: unit 860, regr 10, hooks 66, tables 325/396, page 22, lint 0E/5W, validate 0E; dogfood: enforcement-defaults applies, global-config human, changes-in-flight report, statusline-launcher nothing here (own statusline in this environment, not the versioned one §7 expected); tree clean |
| E1.F8.T2 [human] | ✅ done | — | 15 | 0 | Executed: maintainer agent, headless under D-21 · 2026-09-25 · `qa/manual/e2e-2026-09-25.md` (PASS after F-05, F-06, F-07) |
| E1.F8.T3 [Backend] | ✅ done | 8 | 4 | 0 |  |
| E1.F8.T4 [human] | 🙋 awaiting-human | — | — | — | executor: owner — prod OK inside karvey-deploy (D-10), after E1.F8.T3 |
| E1.F9.T1 [Backend] | ✅ done | 10 | 8 | 0 | tests red first (F-21, F-22, F-23, F-28) |
| E1.F9.T2 [Backend] | ✅ done | 10 | 8 | 0 | tests red first (F-08, F-24) |
| E1.F9.T3 [Backend] | ✅ done | 8 | 7 | 0 | tests red first (F-25, F-27) |
| E1.F9.T4 [Backend] | ✅ done | 4 | 4 | 0 | test red first (F-09); line length bound kept |
| E1.F9.T5 [Backend] | ✅ done | 8 | 8 | 0 | test red first (F-26, 10 cases) |

`estimate_min` is written here once; impl fills the two actual columns and never edits the estimate.

## History

| Date | Phase | Note |
|---|---|---|
| 2026-09-25 | init | spec.json, prd.md, checkpoint with the plan checklist (D-20). |
| 2026-09-25 | requirements | 32 EARS requirements in 6 areas (REQ-UP-001..032), spec-delta ADDED 32; D-20 and BL-51 recorded. Awaiting the owner's approval. REQ-UP-005 (no offer when nothing applies) is an interpretation of D-20 to confirm at this gate. |
| 2026-09-25 | architecture | `architecture.md`: hook offer with an in-hook short-circuit probe (1.5 s budget), seen record resolved only by `karvey-upgrade.py seen` / the skill, engine as the single writer (pure step functions → edits, confinement, CAS, preview digest), 8 initial steps, skill flow to one PR, L-37 (release-surface fingerprint) + L-38 (catalogue) + L-39 (docs); 32/32 REQ-UP covered; architect decisions A-01..A-14 under D-21. Infra skipped (no cloud). Awaiting approval. |
| 2026-09-25 | tasks | `tasks.md`: 25 tasks in 8 features (20 Backend, 3 Test, 2 `[human]`: the E2E offer → PR on a throw-away repo, and the prod OK), 262 min calibrated to realistic AI + review (the default scale ran ~10× high), critical path 144 min along `karvey_lib/upgrade.py`; 32/32 REQ-UP traced. Awaiting approval. |
| 2026-09-25 | impl | 23 agent tasks done (E1.F1.T1 … E1.F8.T3), one commit each with its `[Unreleased]` line; whole-repo gate green (unit 860, regression 10, test-hooks 66, guard tables 325 cases / 396 runs, page 22, lint 0 errors, validate 0 errors). Findings F-01..F-04: L-38 treats a `since` newer than `plugin.json` as a warning while `[Unreleased]` holds entries (F-01, deviation from §1.8); `Probe.plugin_read` / `plugin_json` added for the shipped shims and schema (F-02); the test-hooks path and its isolated HOME (F-03); re-record the fingerprint if 3.12.0 ships first (F-04). E1.F8.T3 done before the `[human]` E1.F8.T2 on the owner's instruction (release text only). E1.F8.T2 and E1.F8.T4 await the owner. |
| 2026-09-25 | test | Whole-repo gate green (unit 857, regression 10, test-hooks 66, guard tables 396 runs, page 22, lint 0 errors, validate 0 errors); E1.F8.T2 run headless under D-21 in a throw-away repo with a bare origin: offer → accept → PR offered, second session silent, decline until the version changes, manual script 6/6. F-05, F-06, F-07, F-10 bugs fixed with regression tests; F-08 spec-gap and F-09 emergent open for karvey-iterate. 32/32 REQ-UP PASS. Benchmark: startup hook median 114 ms with the offer, 113 ms without. `test_plan.md`, `test_evidence.md`. |
| 2026-09-25 | qa | 9-dimension review `qa/REVISION_PR_feature-project-upgrade_20260925.md`: 20 findings (0 critical, 3 high, 8 medium, 9 low); security gate PASS; second opinion intra-model (FAIL on the reviewed code). Bugs F-11..F-20, F-30 fixed in the iterate micro-loop with regression tests (unit 870, all gates green). Open: spec-gaps F-08, F-21..F-27; emergent F-09, F-28, F-29. QA not approved (owner). |
| 2026-09-26 | iterate | `karvey-iterate` rev. 2 under D-21: spec-gaps F-08, F-21..F-27 resolved by requirements rev. 2 (REQ-UP-003, 006, 012, 013, 016, 020, 023, 026, 031 rewritten; recommended option taken, listed in `requirements.md` § Revision history for the owner), architecture rev. 2, tasks E1.F9.T1..T5 with red-first regression tests; F-01, F-02 folded into architecture §1.8 / §1.4; emergent F-09, F-28 fixed, F-29 deferred (docstring fixed), F-04 left to karvey-deploy. QA dimensions D1–D4 re-run on the new diff: 9 more findings F-31..F-39 (0 critical/high, 3 medium) all fixed with regression tests; security gate PASS; converged (appended to the REVISION_PR). QA approval is the owner's. |

## QA Review

Document: `qa/REVISION_PR_feature-project-upgrade_20260925.md` (2026-09-25, re-run 2026-09-26). Security gate: PASS.
Verdict: converged — no open or routed bug/spec-gap; emergent F-04, F-29 deferred with reason. Awaiting the owner's
QA approval (not recorded by the agent).

| Finding | Severity | Type | Resolution |
|---|---|---|---|
| F-08, F-21..F-27 | low–medium | spec-gap | requirements rev. 2 (recommended option each, listed for the owner), implemented, closed |
| F-09, F-28 | low | emergent | fixed (cheap and clearly right), closed |
| F-31..F-39 | low–medium | bug / spec-gap | QA re-run findings, fixed with regression tests, closed |
| F-04, F-29 | low | emergent | deferred with reason → backlog (orchestrator) |
