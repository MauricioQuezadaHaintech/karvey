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
| (pending — karvey-architecture) | |

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
(pending — karvey-tasks)

---

## Task status
> Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked`

| Task | Status | Estimated time | Actual time |
|------|--------|----------------|-------------|
| (pending) | | | |

---

## History
| Date | Phase | Action |
|-------|------|--------|
| 2026-09-23 | init | Spec initialized on `feature/wave1-hardening` (Markdown tracker; no external tracker item). Decisions D-01..D-04 recorded in `docs/spec/decisions.md`. mockup and design_graphic recorded as skipped (no UI). |
| 2026-09-23 | init | Knowledge sync (init Step 9C, `/graphify docs/spec/ --update`) **not run**, deliberately: this change moves the sync to archive only (REQ-W1-062). To run at archive. |
| 2026-09-23 | requirements | 109 EARS requirements (REQ-W1-001..109) in 16 areas; spec-delta ADDED 109 + 12 carried REQ-ADP, MODIFIED 4 REQ-TEAM, REMOVED 0. `approvals.requirements.generated = true`; awaiting the owner's approval. Open question Q-01 (rotation threshold). |
