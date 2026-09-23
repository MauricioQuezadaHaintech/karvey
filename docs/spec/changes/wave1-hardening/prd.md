# PRD: wave1-hardening

## 1. Executive summary
Karvey 3.11.2 has first-class content and fragile execution: its determinism is written in prose, the
prose contradicts itself, and the method's own repo skipped its gates (expert panel 2026-09-23, 34 confirmed
findings). Wave 1 — released as **3.12.0**, backward compatible — replaces the guarantees stated in prose
with a validated phase state, guards backed by table tests, a production gate, one versioning moment, a
bounded session hook and a CI linter, and closes the retroactive QA of `team-adapters` (BUG-05..BUG-17 and
23 spec-gaps) inside the same change.

## 2. 🎯 Goal (the change's north star)
> **Everything the method claims to guarantee is either enforced by a script or hook with a test, or stated
> as a recommendation — never promised in prose and silently skipped.**

This goal is the north star that all Karvey phases pursue: each phase re-reads it on start to advance
toward the result without stopping until it's achieved, respecting the plan and security gates.

## 3. Problem and context
- **Who has it:** every team using Karvey (the human who approves gates and the agent that follows the
  skills), and first of all the method's owner, whose own repo is the evidence (H-22).
- **Current situation** (`docs/spec/reviews/2026-09-23-panel-review.md` §2):
  - The state machine does not exist as code: skills write 11 `phase` values the orchestrator does not know,
    impl writes none, and a change without UI dead-ends between mockup and architecture (H-01..H-03).
  - The declared guarantees are not real: the hooks do less than `enforcement.md` says, two cited hooks do
    not exist, nothing guards the merge to production, and three instructions force the agent to commit on
    `dev` (H-10..H-15, H-18..H-20).
  - Two version bumps per release (H-17); the estimate is overwritten by the actual (H-16).
  - The session hook takes `archive/` as the active change and injects the manifest twice (H-08, H-09).
  - 9 rule copies, 109 unresolvable paths, no CI (H-26, H-27); graphify runs in every phase (H-31); the
    dashboard shows no findings, incidents or backlog (H-30); QA commits fixes (H-28); 12 skills lose their
    description in the listing (H-23).
  - `team-adapters` reached production with no `approvals.qa`; its retroactive QA (NOT APPROVED) left 13 open
    bugs and 23 spec-gaps routed to this change (`docs/spec/changes/team-adapters/findings.md`,
    `docs/bugs_dev_testing.md`, `REVISION_PR_17-19_20260923.md`).
- **Impact:** a gate that exists only in prose is skipped under pressure — which is exactly what happened to
  `team-layer` and `team-adapters`. Every structural improvement of Wave 2 (lanes, judges, metrics,
  release per change) needs a trustworthy phase state to stand on.

## 4. Objectives and success metrics
| # | Objective | Metric (measured at 3.12.0) |
|---|---|---|
| O-1 | Reproducible phase state | 0 `spec.json`/`project.json` errors in `validate` over `docs/spec/`; 100% of phase writes through the state tool |
| O-2 | Guards do what the rule says | 100% of guard-table cases pass; the 5 evasions of H-10/H-12 blocked; 0 false positives in the table |
| O-3 | The production gate is code | 0 merges to production possible without `approvals.prod` = human + ref (table cases) |
| O-4 | No forced commits on integration/production | 0 direct commits on `dev`/`master`/`main` in `git log --first-parent` for this change's cycle |
| O-5 | One versioning moment | exactly 1 version bump in the 3.12.0 release |
| O-6 | Estimates preserved | 100% of this change's tasks keep estimate and actual separately |
| O-7 | Session hook correct and bounded | 0 false restores after an archive; ≤40 board rows and ≤6 KB handoff injected |
| O-8 | Drift caught before release | plugin linter green on every PR; 0 "documentation drift" fixes needed after 3.12.0 |
| O-9 | Knowledge sync out of the hot path | 0 graphify runs outside archive / on demand |
| O-10 | Open work visible | the dashboard lists findings, open BUG-NN, `awaiting-human` tasks, open backlog, age and WIP |
| O-11 | `team-adapters` converged | 0 open bug/spec-gap in its findings; BUG-05..BUG-17 RESUELTO with a regression check |
| O-12 | Every skill visible to the model | 32/32 skills listed with a description ≤250 chars |

## 5. User stories / main use cases
- As the **human approver**, I want the plan and production gates to be enforced by hooks, so that an agent
  cannot proceed past me by creating a marker or using `--admin`.
- As the **agent**, I want one command that tells me the next phase and records transitions, so that I do not
  interpret a table and write an invented state.
- As a **team lead** on a legacy repo (`"management": "markdown"` as a string), I want a migration that fixes
  my `project.json`, so that Markdown repos stop being sent to a tracker.
- As a **maintainer of the plugin**, I want a CI linter, so that a rule copy, a broken path or a missing
  "Why" is caught in the PR, not after release.
- As a **reader of the dashboard**, I want open findings, incidents, human tasks and stalled changes in one
  place.
- As the **owner**, I want 3.12.0 itself built under the method, so that the release proves the guards work.

## 6. Scope (in scope)
| # | Area | Panel item | Backlog |
|---|---|---|---|
| S-1 | Single phase state machine: closed enum, schemas, state tool (`next/advance/approve/skip/validate --fix`), `phase_history`, `skipped`, migration of legacy `spec.json` and `project.json` (incl. `management` string → object — the 16 HainTech repos case) | R-01 | BL-04 |
| S-2 | Guards that do what `enforcement.md` says, with table tests: plan-gate regex and classes, scoped/expiring marker created by a `UserPromptSubmit` hook (D-01), git-flow `-C`/`cd`/bare push/`master-notes`, new `prod-gate` ON by default (D-02), spec.json validator, removal or implementation of `clickup-sync-guard` / `standards-guard` | R-02 | BL-05 |
| S-3 | Deploy and archive never commit on integration/production (D-03); checklist before the first push; trunk projects | R-03 | BL-06 |
| S-4 | One versioning moment (`[Unreleased]` in impl, bump at release); QA D6; visible-version check | R-04 | BL-07 |
| S-5 | Estimate never overwritten; estimate + actual AI + actual review per task; calibration at archive | R-05 | BL-08 |
| S-6 | Session hook: `archive/` not active; bounded injection; `state.json` by script; one rotation threshold; settings notice (REQ-ADP-003 amendment) | R-06 | BL-09 |
| S-7 | Plugin as code: no rule copies (or verified copies); resolvable paths; CI linter `lint-plugin` | R-07 | BL-10 |
| S-8 | Graphify and the tracker ritual out of the hot path (graphify at archive only) | R-16 | BL-19 |
| S-9 | Spec-delta merge **script** (timing unchanged) | R-17 (script only) | BL-20 |
| S-10 | Dashboard with open work, age and WIP (`karvey-context` backed by a script) | R-18 | BL-21 |
| S-11 | QA observes without fixing; `REVISION_PR` inside the change; stack rules to standards | R-21 | BL-24 |
| S-12 | Short frontmatter descriptions, no generic triggers | R-22 | BL-25 |
| S-13 | Convergence of `team-adapters`: BUG-05..BUG-17 and every spec-gap routed here (F-05, F-06, F-10..F-20, F-32..F-41), amending REQ-ADP-001/002/003/010/011/012/020/021/022/023/031 | QA of PRs #17-#19 | — |

**Note — lanes do not exist yet.** The method still has a single pipeline (lanes are R-09, Wave 2). This
change has no UI, so it records `lane: "standard"` and `skipped: {mockup: "no UI", design_graphic: "no UI"}`
in its own `spec.json` as **its own workaround**. The state tool of S-1 must support `skipped` (REQ-W1-004,
REQ-W1-007) so that this workaround becomes a validated fact rather than a note; `lane` is recorded as data
only and decides nothing in Wave 1.

## 7. Out of scope
- Wave 2 items: R-08 release per change and trunk mode as a setting, R-09 lanes, R-10 fewer gates and `-y`
  semantics, R-11 judges, R-12 test-first traceability, R-13 security tools, R-14 metrics (beyond writing
  `phase_history`), R-20 scripts, R-23 post-deploy thresholds, and the R-17 *timing* (merge before prod).
- Wave 3 items (R-15, R-19, R-24..R-30), including unifying the decision-log path as a feature (this change
  only makes the two texts agree, REQ-W1-059).
- Emergent findings of `team-adapters` that stay in the backlog: BL-38..BL-43.
- Editing the owner's global `~/.claude/CLAUDE.md` (D-01 consequence): shown to him as a diff, outside this
  repo.
- Running `--fix` in other repos (HainTech's 16 repos, Tarien): each repo's own docs PR.

## 8. Stakeholders
- **Requests and approves:** Mauricio Quezada Ibáñez (owner of the method; approves requirements, tasks and
  production — `role: human`).
- **Impacted:** every project using Karvey (HainTech's ~22 Karvey repos first), and agents running the skills.
- **Sources:** the expert panel (DM, PM, AG judges) and the retroactive QA of `team-adapters`.

## 9. Constraints
- **Security Tier: 2** — the change adds hooks that gate git operations and the merge to production, and
  handles values from a committed `project.json` that end up in commands. Controls required: the production
  gate fails closed and logs every decision (REQ-W1-024, REQ-W1-025); the approval comes only from the
  human's message (REQ-W1-017, REQ-W1-018); `project.json` values are validated before use in commands
  (REQ-W1-093); notification destinations are confirmed when they change (REQ-W1-097).
- **Backward compatible (3.12.0):** `validate` runs in warning mode on legacy files; `--fix` migrates; no
  existing `spec.json` becomes unreadable.
- **Dogfooding (D-04):** built through the method on this repo, trunk flow (`main` = integration =
  production), Markdown tracker (`PLAN.md`), no external tracker items.
- **Decisions this change depends on:** D-01, D-02, D-03, D-04 (`docs/spec/decisions.md`).
- **Prerequisites:** hotfix 3.11.2 released (BUG-01..BUG-04 RESUELTO) — done.

## 10. Acceptance criteria
- **AC-1** `validate` over this repo's `docs/spec/` reports 0 errors, after `--fix` migrated
  `team-adapters/spec.json` and the archived `team-layer/spec.json` without changing any approval.
- **AC-2** The guard tables pass in CI and include every H-10 and H-12 case plus the plan-gate false
  positives/negatives and the approval-vocabulary cases.
- **AC-3** A production merge (`gh pr merge`, incl. `--admin`) is blocked without a human `approvals.prod`,
  and allowed with one; the 3.12.0 release itself goes through that gate.
- **AC-4** The plugin linter runs on every PR and is green on the 3.12.0 release commit.
- **AC-5** `team-adapters/findings.md` has no open bug or spec-gap; BUG-05..BUG-17 are RESUELTO with a named
  regression test or linter check.
- **AC-6** QA review documents live under `changes/{id}/qa/`; none at the repo root.
- **AC-7** Every requirement REQ-W1-001..109 is covered by a test, a linter check or a guard-table case, or is
  explicitly marked manual (agent behaviour) with its manual-test script.

## 11. Assumptions and open questions (to confirm at the requirements gate)
- **Q-01 — Rotation threshold value** (panel Wave 1 owner decision 4, not among D-01..D-04). REQ-W1-049 only
  requires one value in one place; the panel recommends **8 h** (the statusline's value). Needs the owner's
  answer before `tasks`.
- **A-1** Plan-marker TTL default **120 minutes**, configurable per project (REQ-W1-016).
- **A-2** Stall threshold default **7 days** in the current phase (REQ-W1-069).
- **A-3** Calibration proposal when a work type deviates more than **±30% in each of the last 3** archived
  changes (REQ-W1-044; the panel says "N cambios").
- **A-4** Backlog seeds: the panel's Wave 1 maps to BL-04..BL-10, BL-19, BL-20, BL-21, BL-24 and BL-25 (the
  items marked `promoted → wave1-hardening` in `docs/spec/backlog.md`). BL-11..BL-15 are Wave 2 items (R-08..R-12),
  still `open`, and are **not** seeds of this change.
