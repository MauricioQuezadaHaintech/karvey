# Plan: wave1-hardening

**Capability:** method | **Security Tier:** 2 | **Layers:** Backend, Infra
**Created:** 2026-09-23 | **Status:** 🔄 in_progress
**Lane:** standard (recorded workaround — no lanes until R-09) · **Skipped:** mockup, design_graphic (no UI)
**Release target:** 3.12.0 · **Flow:** trunk (`feature/wave1-hardening` → PR → `main`) · **Decisions:** D-01..D-04

---

## Epic: Wave 1 hardening — guarantees enforced by code, not by prose

### Description
Karvey 3.11.2 states its guarantees in prose that no script or hook enforces: a phase state the orchestrator
cannot read, guards weaker than their rule, no guard on the production merge, instructions that force commits
on `dev`, double versioning, estimates overwritten, a session hook that restores archived changes, 9 rule
copies and no CI. The method's own repo skipped its gates (H-22). This Epic implements the panel's Wave 1
(R-01..R-07, R-16, R-17 script, R-18, R-21, R-22) and converges the open bugs (BUG-05..BUG-17) and
spec-gaps of `team-adapters` (D-04).

North star: *everything the method claims to guarantee is either enforced by a script or hook with a test,
or stated as a recommendation — never promised in prose and silently skipped.*

### Strategic value
A method that sells "gates" and "never delegated prod approval" must be able to show them working. Wave 1 is
the foundation every Wave 2 item (lanes, judges, metrics, release per change) reads from, and it removes the
failure mode that let two changes ship without QA.

### Design decisions
| Topic | Decision |
|------|----------|
| Plan-approval marker | D-01 — created by a `UserPromptSubmit` hook on the human's approval; never by the agent |
| prod-gate default | D-02 — ON by default, switchable off per project |
| Where prod approval lives | D-03 — D-NN + PR + `spec.json` at archive; never a commit on dev/integration |
| Dogfooding | D-04 — built with Karvey on itself; team-adapters converges here |
| Architecture | D-09 — approved with the architect's recommended defaults |
| Prod approval words | D-10 — approval word AND production word in the human's own prompt |
| Owner's plan hooks | D-11 — `KARVEY_COMPAT_MARKER` |

---

## Features

| Feature | Area | Requirements covered | Panel / sources | Status |
|---------|------|----------------------|-----------------|--------|
| F1 | Single phase state machine | REQ-W1-001..013 | R-01 · H-01, H-02, H-03, H-07, H-22, H-24, H-25 · BUG-06, F-40 · BL-04 | ⬜ |
| F2 | Guards with table tests, prod-gate, approval hook | REQ-W1-014..030 | R-02 · H-10..H-15 · BUG-15 · D-01, D-02 · BL-05 | ⬜ |
| F3 | Deploy and archive off integration/production | REQ-W1-031..035 | R-03 · H-18, H-19, H-20 · D-03 · BL-06 | ⬜ |
| F4 | One versioning moment | REQ-W1-036..041 | R-04 · H-17 · F-20, F-38, F-43 · BL-07 | ⬜ |
| F5 | Estimate never overwritten | REQ-W1-042..044 | R-05 · H-16 · BL-08 | ⬜ |
| F6 | Session hook: archive, bounded injection, state.json, threshold, settings notice | REQ-W1-045..051 | R-06 · H-08, H-09, H-32 · F-34, BUG-16 · BL-09 | ⬜ |
| F7 | Plugin as code + CI linter | REQ-W1-052..060 | R-07 · H-23, H-24, H-26, H-27, H-33 · F-44, BUG-07, BUG-17 · BL-10 | ⬜ |
| F8 | Graphify and tracker ritual off the hot path | REQ-W1-061..064 | R-16 · H-31 · BL-19 | ⬜ |
| F9 | Spec-delta merge tool | REQ-W1-065..067 | R-17 (script) · BL-20 | ⬜ |
| F10 | Open-work dashboard | REQ-W1-068..072 | R-18 · H-30 · BL-21 | ⬜ |
| F11 | QA observes only; review inside the change | REQ-W1-073..076 | R-21 · H-28, H-29 · BL-24 | ⬜ |
| F12 | Short descriptions, no generic triggers | REQ-W1-077..079 | R-22 · H-23 · BL-25 | ⬜ |
| F13 | Tracker adapters converged (team-adapters) | REQ-W1-080..096 | F-05, F-06, F-10, F-12..F-19, F-36, F-37, F-39..F-41, BUG-05, BUG-06, F-01 (verify) | ⬜ |
| F14 | Notifications converged (team-adapters) | REQ-W1-097..099 | F-11, F-32, F-33 | ⬜ |
| F15 | Statusline and method-page defects | REQ-W1-100..106 | BUG-08..BUG-14, F-35 | ⬜ |
| F16 | Convergence and dogfooding | REQ-W1-107..109 | D-04 · BUG-05..BUG-17 · H-22 | ⬜ |

---

## Tasks

Full detail (files, REQs, tests, done criteria, dependencies) in [`tasks.md`](tasks.md).

> The task Features `E1.F1..E1.F16` group work by **architecture component**. The *Features* table above groups the **requirements by area**; its F-numbers are independent. The REQ → task matrix is at the end of `tasks.md`.

### Feature E1.F1: Hook contract capture (T-0)

- [x] E1.F1.T1 [Test] Capture one real hook payload per event in a throw-away plugin (T-0) — est: 30min
- [ ] E1.F1.T2 [human] (Conditional) capture the payloads interactively if F1.T1 could not — executor: owner (depends E1.F1.T1)

### Feature E1.F2: Shared library and schemas

- [x] E1.F2.T1 [Backend] `karvey_lib` package skeleton, exit codes, JSON envelope and `defaults.json` — est: 15min (P)
- [x] E1.F2.T2 [Backend] `atomicio.py`: BOM-tolerant read, format-preserving atomic write, lock and compare-and-swap — est: 20min (depends E1.F2.T1) (P)
- [x] E1.F2.T3 [Backend] `schema_lite.py`: the JSON-Schema subset validator with the two `x-karvey-*` extensions — est: 25min (depends E1.F2.T1) (P)
- [x] E1.F2.T4 [Backend] `project.py` (root discovery, active change, reviewed-config read, state dir) and `audit.py` — est: 30min (depends E1.F2.T1) (P)
- [x] E1.F2.T5 [Backend] `schemas/spec.schema.json` and `schemas/project.schema.json` — est: 30min (depends E1.F2.T3)
- [x] E1.F2.T6 [Backend] `schemas/state-machine.json` and `schemas/legacy-phase-map.json` — est: 15min (depends E1.F2.T5)

### Feature E1.F3: State tool `karvey-state.py`

- [x] E1.F3.T1 [Backend] `karvey-state.py` CLI and `validate` (schema + semantic checks, advisory/strict) — est: 30min (depends E1.F2.T2, E1.F2.T4, E1.F2.T5, E1.F2.T6)
- [x] E1.F3.T2 [Backend] `validate --fix` migration (exact tier, `--accept-proposed`, `--dry-run`, idempotent) — est: 45min (depends E1.F3.T1)
- [x] E1.F3.T3 [Backend] `next` and `active` commands — est: 20min (depends E1.F3.T2)
- [x] E1.F3.T4 [Backend] `advance`, `generated`, `skip`, `reopen` with history, lock and legacy in-memory mapping — est: 40min (depends E1.F3.T3)
- [x] E1.F3.T5 [Backend] Marker store and release ledger in `approval.py` — est: 30min (depends E1.F2.T2, E1.F2.T4) (P)
- [x] E1.F3.T6 [Backend] `approve` (prod → ledger, `--write-spec`), `check-prod`, marker consumption on `advance` — est: 30min (depends E1.F3.T4, E1.F3.T5)

### Feature E1.F4: Hook runtime: parser, shell segmentation, dispatcher, table runner

- [x] E1.F4.T1 [Backend] `hookio.py`: tolerant payload parser and path normalisation — est: 20min (depends E1.F1.T1, E1.F2.T1) (P)
- [x] E1.F4.T2 [Backend] `shellparse.py`: segmentation, wrappers, recursion, `cd` and git global options — est: 40min (depends E1.F2.T1) (P)
- [x] E1.F4.T3 [Backend] Dispatcher `karvey-hook.sh`, `karvey_hooks.py` entry points with the guard registry, new `hooks.json` events — est: 35min (depends E1.F4.T1, E1.F4.T2, E1.F2.T4)
- [x] E1.F4.T4 [Test] Table runner `run_tables.py` (throw-away repos, bare origin, CLI stubs, `nopy` pass) — est: 35min (depends E1.F4.T3)

### Feature E1.F5: Guards and the approval hook

- [x] E1.F5.T1 [Backend] protect-paths guard and its table — est: 20min (depends E1.F4.T4, E1.F3.T5)
- [x] E1.F5.T2 [Backend] Approval hook: vocabulary, quote stripping, prod kind (D-10), scope, compat marker (D-11) — est: 45min (depends E1.F3.T5, E1.F4.T4) (P)
- [x] E1.F5.T3 [Backend] plan-gate classifier and its table — est: 45min (depends E1.F5.T1, E1.F5.T2)
- [x] E1.F5.T4 [Backend] git-flow guard (target repo per segment, aliases, whole-name match, trunk) and its table — est: 50min (depends E1.F5.T3)
- [x] E1.F5.T5 [Backend] prod-gate: candidates, production set, base and change resolution, `check-prod` — est: 45min (depends E1.F5.T4, E1.F3.T6)
- [x] E1.F5.T6 [Backend] prod-gate: reviewed-line switch-off, fail-closed reasons, audit lines, `nopy` classifier — est: 30min (depends E1.F5.T5)
- [x] E1.F5.T7 [Backend] post-edit: spec-write validator and pending-sync recorder — est: 25min (depends E1.F3.T1, E1.F4.T4) (P)
- [x] E1.F5.T8 [Backend] Legacy template shims (`--only <guard> --force-enabled`) — est: 15min (depends E1.F5.T4, E1.F6.T2)

### Feature E1.F6: Session hook and handoff capture (on the 3.11.4 code)

- [x] E1.F6.T1 [Backend] `karvey_hooks.py session`: active change, manifest xor, bounded board/handoff, structured output (port of the 3.11.4 logic) — est: 45min (depends E1.F4.T3, E1.F2.T4, E1.F5.T7)
- [x] E1.F6.T2 [Backend] Settings notice on `startup` only, `origin/{integration}` check, legacy-shape message; SessionStart split by matcher — est: 30min (depends E1.F6.T1)
- [x] E1.F6.T3 [Backend] `karvey-handoff-capture.py` writes `state.json` in the shape the 3.11.4 resolver reads — est: 25min (depends E1.F2.T2, E1.F2.T4) (P)
- [x] E1.F6.T4 [Test] `session.json` table; `test-hooks.sh` becomes the entry point that also runs the tables — est: 30min (depends E1.F6.T2, E1.F6.T3, E1.F4.T4)

### Feature E1.F7: Settings resolver `karvey-config.py` and safe values

- [x] E1.F7.T1 [Backend] `safe_values.py` patterns and the no-shell rule — est: 25min (depends E1.F2.T1) (P)
- [x] E1.F7.T2 [Backend] `karvey-config.py resolve | get --shell | propose-settings` — est: 30min (depends E1.F7.T1, E1.F2.T4, E1.F2.T5)
- [x] E1.F7.T3 [Backend] `karvey-config.py notify-check [--confirm]` and `outbox add|list|done` — est: 30min (depends E1.F7.T2)

### Feature E1.F8: Dashboard `karvey-context.py`

- [x] E1.F8.T1 [Backend] `karvey-context.py`: overview, open work, approvals, WIP, enforcement (read-only) — est: 45min (depends E1.F3.T3, E1.F7.T3, E1.F2.T4)
- [x] E1.F8.T2 [Backend] `karvey-context.py`: calibration, close report, convergence, audit block counts — est: 35min (depends E1.F8.T1)

### Feature E1.F9: Spec-delta merge `karvey-spec-merge.py`

- [x] E1.F9.T1 [Backend] `karvey-spec-merge.py` (ADDED / MODIFIED / REMOVED, `--dry-run`) — est: 40min (depends E1.F2.T1, E1.F2.T2) (P)

### Feature E1.F10: Plugin linter `lint-plugin.py`

- [x] E1.F10.T1 [Backend] Linter framework (registry, `--list`, `--only`, `--paths`, formats) and L-01..L-04 — est: 45min (depends E1.F2.T1) (P)
- [x] E1.F10.T2 [Backend] Linter L-05..L-10 and L-14 (phase literals, no hand phase edits, `next`, produces/reads, paths, rule copies, allowed-tools) — est: 50min (depends E1.F10.T1, E1.F2.T6)
- [x] E1.F10.T3 [Backend] Linter L-11..L-13, L-17, L-18 (counts, versions, release docs, rule JSON vs schema, docs/spec validate) — est: 40min (depends E1.F10.T2, E1.F3.T1, E1.F2.T5)
- [x] E1.F10.T4 [Backend] Linter L-15, L-16 (hooks exist; guard-case anchors match the tables) and L-19..L-24 — est: 50min (depends E1.F10.T3)
- [x] E1.F10.T5 [Backend] Linter L-25..L-30 (QA, stack rules, deploy/archive, management, shell interpolation, H-33) — est: 45min (depends E1.F10.T4)
- [x] E1.F10.T6 [Backend] Linter L-31..L-35 (public tracker text, RESUELTO needs a regression, duplicate ids, subagent project.json writes, CHANGELOG compat line) — est: 30min (depends E1.F10.T5)

### Feature E1.F11: Statusline and method page

- [x] E1.F11.T1 [Backend] Statusline: visible invalid TZ, clean separators, rotation default from `defaults.json` — est: 25min (depends E1.F2.T1, E1.F4.T4) (P)
- [x] E1.F11.T2 [Frontend] Method page `docs/karvey.html`: pure functions + `init(window)`; BUG-10..14 fixed; node and static tests — est: 45min (P)

### Feature E1.F12: Skill and rule text changes

- [x] E1.F12.T1 [Backend] Delete the 9 rule copies; rewrite references to `../karvey/rules/x.md` — est: 20min (depends E1.F10.T2)
- [x] E1.F12.T2 [Backend] New rule `rules/state-machine.md` (generated block) and its agreement test — est: 20min (depends E1.F2.T6) (P)
- [x] E1.F12.T3 [Backend] Text: orchestrator `karvey/SKILL.md`, `karvey-init`, `karvey-requirements` — est: 45min (depends E1.F12.T1, E1.F3.T6, E1.F7.T2) (P)
- [x] E1.F12.T4 [Backend] Text: `karvey-mockup`, `karvey-design-graphic`, `karvey-architecture`, `karvey-infra`, `karvey-tasks` — est: 40min (depends E1.F12.T1, E1.F3.T6) (P)
- [x] E1.F12.T5 [Backend] Text: `karvey-impl`, `karvey-test`, `karvey-qa` — est: 45min (depends E1.F12.T1, E1.F3.T6, E1.F7.T3) (P)
- [x] E1.F12.T6 [Backend] Text: `karvey-deploy`, `karvey-archive`, `karvey-iterate` — est: 45min (depends E1.F12.T1, E1.F3.T6, E1.F9.T1, E1.F8.T2) (P)
- [x] E1.F12.T7 [Backend] Text: context, checkpoint, guard, team, benchmark-models, scrape, import, retro, browse, health, decisions + `rules/multi-agent.md` — est: 45min (depends E1.F12.T1, E1.F6.T3, E1.F8.T1) (P)
- [x] E1.F12.T8 [Backend] Text: frontmatter of the remaining 7 skills (devex, diagram, docs, grill, investigate, second-opinion, standards) — est: 20min (depends E1.F12.T1) (P)
- [x] E1.F12.T9 [Backend] Rules A: `enforcement.md` (guard-case anchors), `deploy-workflow.md`, `versioning.md`, `knowledge-sync.md`, `engineering-standards.md` — est: 45min (depends E1.F12.T1, E1.F5.T6, E1.F5.T8) (P)
- [x] E1.F12.T10 [Backend] Rules B: phase-close, management-adapters, notifications, project-config, living-specs, team, clickup-protocol, backlog, incident-tracking — est: 50min (depends E1.F12.T1, E1.F7.T3) (P)
- [x] E1.F12.T11 [Backend] `hooks/README.md`, `README.md`, `plugins/karvey/README.md`, descriptions in `plugin.json` / `marketplace.json` — est: 30min (depends E1.F12.T1, E1.F6.T4, E1.F5.T6) (P)
- [x] E1.F12.T12 [Backend] Move `REVISION_PR_17-19_20260923.md` into `docs/spec/changes/team-adapters/qa/` and update references — est: 10min (P)
- [x] E1.F12.T13 [Backend] Text gate: the whole-repo lint is green — est: 30min (depends E1.F12.T2, E1.F12.T3, E1.F12.T4, E1.F12.T5, E1.F12.T6, E1.F12.T7, E1.F12.T8, E1.F12.T9, E1.F12.T10, E1.F12.T11, E1.F12.T12, E1.F10.T6, E1.F11.T1)

### Feature E1.F13: CI workflow

- [x] E1.F13.T1 [Infra] `.github/workflows/lint.yml` (4 jobs, pinned SHAs, read-only) and `.gitattributes` — est: 25min (depends E1.F12.T13, E1.F4.T4, E1.F6.T4, E1.F11.T2)
- [ ] E1.F13.T2 [Infra] CI observed on a draft PR `feature/wave1-hardening → main` — est: 15min (depends E1.F13.T1, E1.F14.T3, E1.F15.T3)

### Feature E1.F14: Migration fixtures and regression suite

- [x] E1.F14.T1 [Test] Legacy `spec.json` fixtures (anonymised) and the tests that iterate them — est: 40min (depends E1.F3.T2) (P)
- [x] E1.F14.T2 [Test] Legacy `project.json` fixtures and config resolution over them — est: 20min (depends E1.F7.T2) (P)
- [ ] E1.F14.T3 [Test] Regression index BUG-05..17 (`tests/regression/test_incidents.py`) and its CI step — est: 25min (depends E1.F10.T6, E1.F11.T1, E1.F11.T2, E1.F13.T1, E1.F6.T4)
- [ ] E1.F14.T4 [Test] Agent-behaviour manual scripts under `tests/manual/` — est: 30min (depends E1.F12.T3, E1.F12.T5, E1.F12.T6, E1.F12.T10) (P)

### Feature E1.F15: Dogfood migration of this repo

- [ ] E1.F15.T1 [Backend] This repo through `validate --fix`: dry-run diff shown, then applied to `wave1-hardening` and `team-adapters` — est: 20min (depends E1.F3.T2, E1.F14.T1)
- [ ] E1.F15.T2 [human] Owner's prod-kind approval phrase for the retroactive team-adapters record (D-08) — executor: owner (depends E1.F15.T1, E1.F5.T2, E1.F3.T6)
- [ ] E1.F15.T3 [Backend] Record the retro prod approval (`--write-spec`, D-08); this repo validates with 0 errors — est: 15min (depends E1.F15.T2)

### Feature E1.F16: Release 3.12.0 (one versioning moment) and deploy-phase human steps

- [ ] E1.F16.T1 [Backend] Release docs and the single version bump to 3.12.0 — est: 30min (depends E1.F13.T2, E1.F14.T2, E1.F14.T4)
- [ ] E1.F16.T2 [Backend] Prepare, never apply, the owner's global-config diffs (D-01, D-11) — est: 15min (depends E1.F5.T2) (P)
- [ ] E1.F16.T3 [human] Branch protection on `main`: require the CI checks (Q-A8, D-09) — executor: owner (depends E1.F13.T2)
- [ ] E1.F16.T4 [Backend] Release PR ready; `advance deploying` on the feature branch; the unapproved merge is blocked (E2E evidence) — est: 20min (depends E1.F16.T1, E1.F16.T3)
- [ ] E1.F16.T5 [human] The prod OK for 3.12.0 (D-10) and the D-NN answer — executor: owner (depends E1.F16.T4)
- [ ] E1.F16.T6 [Backend] `approve prod` (ledger), merge through the prod-gate, release facts in the ledger — est: 20min (depends E1.F16.T5)
- [ ] E1.F16.T7 [human] Apply the diffs to `~/.claude/CLAUDE.md` and `~/.claude/settings.json` after seeing them (D-01, D-11) — executor: owner (depends E1.F16.T6, E1.F16.T2)

---

## Task status
> Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked` · 🙋 `awaiting-human` (qualifier of `blocked`)

| Task | Status | estimate_min | actual_ai_min | actual_review_min | Notes |
|------|--------|--------------|---------------|-------------------|-------|
| E1.F1.T1 [Test] | ✅ done | 30 | 3 | 0 | captured headless (CLI 2.1.281); A-1..A-7 confirmed, A-8 nuance → F-04; no human review yet |
| E1.F1.T2 [human] | ➖ not needed | — | — | — | conditional: F1.T1 captured headless, no human step required |
| E1.F2.T1 [Backend] | ✅ done | 15 | 1 | 0 | no human review yet |
| E1.F2.T2 [Backend] | ✅ done | 20 | 1 | 0 | no human review yet |
| E1.F2.T3 [Backend] | ✅ done | 25 | 3 | 0 | no human review yet; F-05 logged |
| E1.F2.T4 [Backend] | ✅ done | 30 | 2 | 0 | no human review yet |
| E1.F2.T5 [Backend] | ✅ done | 30 | 2 | 0 | no human review yet; F-06 logged |
| E1.F2.T6 [Backend] | ✅ done | 15 | 1 | 0 | no human review yet |
| E1.F3.T1 [Backend] | ✅ done | 30 | 7 | 0 | no human review yet; F-07 logged (legacy shapes as state.legacy_* warnings) |
| E1.F3.T2 [Backend] | ✅ done | 45 | 2 | 0 | no human review yet |
| E1.F3.T3 [Backend] | ✅ done | 20 | 2 | 0 | no human review yet |
| E1.F3.T4 [Backend] | ✅ done | 40 | 3 | 0 | no human review yet |
| E1.F3.T5 [Backend] | ✅ done | 30 | 2 | 0 | no human review yet; done before T4 (T4's deployed precondition reads the ledger); F-04 applied |
| E1.F3.T6 [Backend] | ✅ done | 30 | 3 | 0 | no human review yet |
| E1.F4.T1 [Backend] | ✅ done | 20 | 2 | 0 | no human review yet; field order per F-02 (no correction to A-2/A-3) |
| E1.F4.T2 [Backend] | ✅ done | 40 | 3 | 0 | no human review yet; hand-written lexer instead of shlex (fd redirections, $( ) positions) |
| E1.F4.T3 [Backend] | ✅ done | 35 | 4 | 0 | no human review yet; guards registered as allow-stubs (wired in batch 3); diagnostic block-only selftest guard (F-08) |
| E1.F4.T4 [Test] | ✅ done | 35 | 3 | 0 | no human review yet; smoke block case uses the selftest guard (F-08) |
| E1.F5.T1 [Backend] | ✅ done | 20 | 7 | 0 | no human review yet; 17 table cases (13 required + 4 allow); plugin-root rule vs dogfooding → F-09 |
| E1.F5.T2 [Backend] | ✅ done | 45 | 4 | 0 | no human review yet; 39 table cases + 12 unit tests; local config helpers → F-10; 200-char pasted-line rule → F-11 |
| E1.F5.T3 [Backend] | ✅ done | 45 | 3 | 0 | no human review yet; 63 table cases (13 nopy); marker cannot be verified without python, so nopy blocks when enabled |
| E1.F5.T4 [Backend] | ✅ done | 50 | 3 | 0 | no human review yet; 59 table cases (10 nopy); branch switch inside the same command not followed (limitation case) |
| E1.F5.T5 [Backend] | ✅ done | 45 | 5 | 0 | no human review yet; 35 table cases (part 1); production set minus integration → F-12; git-flow push cases now run with prod-gate off (first block wins) |
| E1.F5.T6 [Backend] | ✅ done | 30 | 4 | 0 | no human review yet; 53 prod-gate cases (13 nopy); without python every PR merge blocks (base unresolvable) |
| E1.F5.T7 [Backend] | ✅ done | 25 | 2 | 0 | no human review yet; 14 table cases; post-edit keeps running the recorders after a validator block |
| E1.F5.T8 [Backend] | ✅ done | 15 | 2 | 0 | no human review yet; 4 table cases; runner gained a command key and env unset; a missing plugin makes the shim warn and not block |
| E1.F6.T1 [Backend] | ✅ done | 45 | 3 | 0 | no human review yet; port of the 3.11.4 logic; live-state resolver in new karvey_lib/livestate.py (shared with F6.T3); one legacy assertion changed for REQ-W1-046 → F-13 |
| E1.F6.T2 [Backend] | ✅ done | 30 | 1 | 0 | no human review yet; hooks.json SessionStart split (startup | resume|compact|clear), both double-quoted; test-hooks 57/57 |
| E1.F6.T3 [Backend] | ✅ done | 25 | 2 | 0 | no human review yet; 8 unit tests; re-measures after writing when state.json is inside the measured repo; save-order note → F-14 |
| E1.F6.T4 [Test] | ✅ done | 30 | 3 | 0 | no human review yet; 23 session cases (5 nopy); runner: session event, setup commands, context assertions; test-hooks 58/58 incl. all tables |
| E1.F7.T1 [Backend] | ✅ done | 25 | 8 | 0 | no human review yet; lane B; safe_values patterns; findings F-16..F-19 (§3.1 pattern gaps) |
| E1.F7.T2 [Backend] | ✅ done | 30 | 3 | 0 | no human review yet; lane B |
| E1.F7.T3 [Backend] | ✅ done | 30 | 2 | 0 | no human review yet; lane B; notify-check --confirm not tied to a human → F-15 |
| E1.F8.T1 [Backend] | ✅ done | 45 | 4 | 0 | no human review yet; lane D; built without lane B: outbox format reconciled at integration (F-23) |
| E1.F8.T2 [Backend] | ✅ done | 35 | 2 | 0 | no human review yet; lane D |
| E1.F9.T1 [Backend] | ✅ done | 40 | 6 | 0 | no human review yet; lane D |
| E1.F10.T1 [Backend] | ✅ done | 45 | 9 | 0 | no human review yet; lane C |
| E1.F10.T2 [Backend] | ✅ done | 50 | 3 | 0 | no human review yet; lane C |
| E1.F10.T3 [Backend] | ✅ done | 40 | 4 | 0 | no human review yet; lane C; L-17 found `capability` missing from spec.schema.json (fixed at integration, F-21) |
| E1.F10.T4 [Backend] | ✅ done | 50 | 4 | 0 | no human review yet; lane C |
| E1.F10.T5 [Backend] | ✅ done | 45 | 3 | 0 | no human review yet; lane C; L-29 flags 18 `branch_flow` placeholders in shell examples → E1.F12 (F-20) |
| E1.F10.T6 [Backend] | ✅ done | 30 | 2 | 0 | no human review yet; lane C |
| E1.F11.T1 [Backend] | ✅ done | 25 | 2 | 0 | no human review yet; lane D; 8 statusline table cases |
| E1.F11.T2 [Frontend] | ✅ done | 45 | 4 | 0 | no human review yet; lane D; 22 node tests + static page tests |
| E1.F12.T1 [Backend] | ✅ done | 20 | 5 | 0 | no human review yet; 9 identical copies deleted; 188 citations rewritten relative (L-09 README heuristic narrowed, F-24) |
| E1.F12.T2 [Backend] | ✅ done | 20 | 1 | 0 | no human review yet; 3 agreement tests; block regenerated with --write |
| E1.F12.T3 [Backend] | ✅ done | 45 | 6 | 0 | no human review yet; state init command added (F-25); 955 → 795 lines; 68 → 0 errors on the three files |
| E1.F12.T4 [Backend] | ✅ done | 40 | 3 | 0 | no human review yet; 48 → 0 errors on the five files; 1478 → 1461 lines; advance into mockup/infra verified in a scratch repo |
| E1.F12.T5 [Backend] | ✅ done | 45 | 3 | 0 | no human review yet; 910 → 798 lines; nested-fence linter weakness reported (fixed in T13) |
| E1.F12.T6 [Backend] | ✅ done | 45 | 5 | 0 | no human review yet; 717 → 447 lines; 41 → 0 errors; findings F-28..F-30 |
| E1.F12.T7 [Backend] | ✅ done | 45 | 7 | 0 | no human review yet; 11 skills + multi-agent.md, 1312 → 1159 lines; 59 → 0 errors; findings F-31, F-32 |
| E1.F12.T8 [Backend] | ✅ done | 20 | 3 | 0 | no human review yet; 7 descriptions 200–223 chars; L-01..L-04 green on all 32 skills |
| E1.F12.T9 [Backend] | ✅ done | 45 | 3 | 0 | no human review yet; enforcement 40 → 99 lines (one anchored line per promise); L-23 residue in project-config/support-skills handled in T10 |
| E1.F12.T10 [Backend] | ✅ done | 50 | 5 | 0 | no human review yet; 9 rules + support-skills.md, 935 → 1034 lines (the one cascade, missing-map clause, outbox, natural keys and schema fields now live here, cited by the skills); L-24 comma heuristic narrowed (F-34) |
| E1.F12.T11 [Backend] | ✅ done | 30 | 4 | 0 | no human review yet; hooks/README 'What ships' table anchored to table cases; clickup-sync-guard/standards-guard named only as not shipped; plugin.json/marketplace.json descriptions (versions untouched) |
| E1.F12.T12 [Backend] | ✅ done | 10 | 3 | 0 | no human review yet; git mv; 11 references updated (CHANGELOG, backlog, decisions, team-adapters spec.json/findings, prd); graphify-out left for the archive sync; the qa/deploy L-25 hits close in T5/T6 |
| E1.F12.T13 [Backend] | ✅ done | 30 | 4 | 0 | no human review yet; text residue fixed (init CLAUDE.md migration aid, karvey-test AskUserQuestion); whole-repo lint 539 → 7 errors, all L-18 spec.json data owned by E1.F15 (F-35); 0 errors in plugins/** |
| E1.F13.T1 [Infra] | ✅ done | 25 | 9 | 0 | no human review yet; 4 jobs, actions pinned by commit SHA (checkout v7.0.1, setup-python v7.0.0, setup-node v7.0.0); every run: step executed locally, the unit suite, tables and test-hooks also under Python 3.9.25; lint and validate --all red until F-35 / E1.F15 (not hidden); act not installed; F-36, F-37 |
| E1.F13.T2 [Infra] | ⬜ todo | 15 | — | — |  |
| E1.F14.T1 [Test] | ✅ done | 40 | 5 | 0 | no human review yet; 57 hand-written synthetic fixtures: 35 phase shapes (8 enum incl. requirements, found in the 2026-09-24 re-scan, 10 exact, 14 proposed, iterate, null, missing ⊇ the 31 of §2.5), 6 embedded skips, approvals null / unknown keys, 4 management, 6 multi-type, gates-skipped, team-adapters-like, bom, unknown top-level keys; --fix idempotent and approval-neutral on all of them, with and without --accept-proposed |
| E1.F14.T2 [Test] | ✅ done | 20 | 8 | 0 | no human review yet; 9 synthetic project.json fixtures (management markdown/clickup/absent/object, notifications absent/google_chat/none, clickup-backlog-list, trunk); resolve, propose-settings --from-legacy (never writes) and validate --fix (string → object, idempotent) over each; F-38 (status_flow not proposed as statuses) |
| E1.F14.T3 [Test] | ⬜ todo | 25 | — | — |  |
| E1.F14.T4 [Test] | ⬜ todo | 30 | — | — |  |
| E1.F15.T1 [Backend] | ⬜ todo | 20 | — | — |  |
| E1.F15.T2 [human] | ⬜ todo | — | — | — | [human] |
| E1.F15.T3 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F16.T1 [Backend] | ⬜ todo | 30 | — | — |  |
| E1.F16.T2 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F16.T3 [human] | ⬜ todo | — | — | — | [human] |
| E1.F16.T4 [Backend] | ⬜ todo | 20 | — | — |  |
| E1.F16.T5 [human] | ⬜ todo | — | — | — | [human] |
| E1.F16.T6 [Backend] | ⬜ todo | 20 | — | — |  |
| E1.F16.T7 [human] | ⬜ todo | — | — | — | [human] |

---

## History
| Date | Phase | Action |
|-------|------|--------|
| 2026-09-23 | init | Spec initialized on `feature/wave1-hardening` (Markdown tracker; no external tracker item). Decisions D-01..D-04 recorded in `docs/spec/decisions.md`. mockup and design_graphic recorded as skipped (no UI). |
| 2026-09-23 | init | Knowledge sync (init Step 9C, `/graphify docs/spec/ --update`) **not run**, deliberately: this change moves the sync to archive only (REQ-W1-062). To run at archive. |
| 2026-09-23 | requirements | 109 EARS requirements (REQ-W1-001..109) in 16 areas; spec-delta ADDED 109 + 12 carried REQ-ADP, MODIFIED 4 REQ-TEAM, REMOVED 0. `approvals.requirements.generated = true`; awaiting the owner's approval. Open question Q-01 (rotation threshold). |
| 2026-09-23 | tasks | 73 tasks in 16 Features (`tasks.md`): 68 agent tasks, 2150 min total, critical path 550 min; 5 `[human]` (1 conditional). REQ-W1-001..109 all covered. `approvals.tasks.generated = true`; awaiting the owner's approval. Open point OP-1: `infra` neither approved nor skipped (recommended: skip, no cloud). Knowledge sync not run (REQ-W1-062). |
| 2026-09-24 | impl | Batch 1 done: E1.F1.T1 (T-0 payload capture, headless; F-02 closed, F-04 opened; E1.F1.T2 [human] not needed) and E1.F2.T1..T6 (`karvey_lib` skeleton, `atomicio`, `schema_lite`, `project`, `audit`, the four schemas). 106 unit tests green; test-hooks.sh 32/32. New findings F-04, F-05, F-06 (F-06 must be decided before E1.F3.T1/E1.F15.T3). |
| 2026-09-24 | impl | Batch 2 done: F-06/F-05 resolved (legacy date-only approvals are warnings, REQ-W1-003; §2.2 documents the subset). E1.F3.T1..T6 (`karvey-state.py` validate / --fix / next / active / advance / generated / skip / reopen / approve / check-prod; `approval.py` markers + ledger; T5 done before T4) and E1.F4.T1..T4 (`hookio`, `shellparse`, dispatcher `karvey-hook.sh` + `karvey_hooks.py` with allow-stub guards, `hooks.json` +UserPromptSubmit/PreToolUse/PostToolUse, `run_tables.py` + `smoke.json`). 275 unit tests green; test-hooks.sh 55/55; smoke table 9 cases / 16 runs. F-04 resolved; new findings F-07 (resolved), F-08 (open, owner). This change's own spec.json is not migrated yet (E1.F15.T1). |
| 2026-09-24 | impl | Batch 3, lane A done: E1.F5.T1..T8 (protect-paths, approval hook with D-10 prod words and D-11 compat marker, plan-gate, git-flow, prod-gate ×2, post-edit validator + pending-sync, legacy shims) and E1.F6.T1..T4 (session hook ported to python on the 3.11.4 logic, settings notice on startup only with the `origin/{integration}` check, `karvey-handoff-capture.py`, `session.json`). Every guard wired in `hooks.json` is table-tested through the real dispatcher in throw-away repos (never through a live session); `KARVEY_COMPAT_MARKER` is implemented and tested, set nowhere. 295 unit tests green; test-hooks.sh 58/58 (it now also runs the tables); guard tables 281 cases / 343 runs (62 nopy). Estimate 405 min vs 39 min wall-clock (AI). New findings F-09..F-14 (F-10 is the lane A/lane B config-helper reconciliation for the merge). |
| 2026-09-24 | impl | Batch 3, lanes B/C/D merged into `feature/wave1-hardening` (merge commits, `--no-ff`): E1.F7.T1..T3 (`safe_values.py`, `karvey-config.py`), E1.F10.T1..T6 (`lint-plugin.py`, L-01..L-35), E1.F8.T1..T2 (`karvey-context.py`), E1.F9.T1 (`karvey-spec-merge.py`), E1.F11.T1..T2 (statusline, method page). One conflict (`tests/hooks/run_tables.py`, lanes A and D), resolved keeping both. Integration fixes: `capability` in `spec.schema.json` (F-21), shared outbox format `karvey_lib/outbox.py` (F-23), §3.5 enforcement rules shared by guards and dashboard (F-10 resolved); test-pollution `audit.log` removed (F-22). Estimate 535 min vs 56 min wall-clock (AI). New findings F-15..F-23. The whole-repo lint fails as expected: it is the E1.F12 worklist. |
| 2026-09-24 | impl | Batch 4 done: E1.F12.T1..T13 (skill and rule text). 9 rule copies deleted; new `rules/state-machine.md` (generated block + agreement test); new `karvey-state.py init` (F-25); every phase/approval write in the skills goes through `karvey-state.py`, settings through `karvey-config.py`, the dashboard, handoff and spec-merge through their scripts; QA review moved into `team-adapters/qa/`. T3..T11 ran as parallel forks on disjoint files, committed one per task. Whole-repo lint 539 → 7 errors (all L-18 in two `spec.json` data files, owned by E1.F15: F-35); `plugins/**` 0 errors. Skill corpus 8900 → 7433 lines, 122 090 → 108 436 tokens (cl100k). Four linter heuristics narrowed with tests (F-24, F-34). 642 unit tests, test-hooks 58/58, guard tables 289 cases / 351 runs, page 22/22. New findings F-24..F-35. |
