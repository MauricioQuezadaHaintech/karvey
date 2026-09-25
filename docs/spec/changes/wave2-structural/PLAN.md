# Plan: wave2-structural

**Capability:** method | **Security Tier:** 2 | **Layers:** Backend, Infra
**Created:** 2026-09-25 | **Status:** 🔄 in_progress (requirements generated, awaiting the *what* gate)
**Lane:** standard (no UI: mockup and design_graphic to be skipped at the architecture transition)
**Release target:** 3.13.0 (advisory / opt-in) → 4.0.0 when the D-24 defaults turn blocking
**Flow:** trunk (`feature/wave2-structural` → PR → `main`) · **Decisions:** D-22..D-27, D-29, D-30 (D-01..D-19 hold)
**Depends on:** `wave1-hardening` (3.12.0) merged first

---

## Epic: Wave 2 structural — process cost that scales with the change, measured

### Description
One pipeline for every change, seven human gates, no independent review before QA, a released unit that is not
the approved unit, tests after code, a security gate judged by the model and no flow metric (panel review
2026-09-23, R-08..R-14, R-17, R-20, R-23). This Epic implements the panel's Wave 2 in its internal order — R-14
metrics first, then R-09 lanes + R-11 judges advisory, then R-10 merged gates + R-08 release manifest in warn
mode — and ships 3.13.0 with every new check advisory; 4.0.0 follows after 4–6 measured changes (D-24). It also
absorbs the Wave 1 findings deferred by D-17 (BL-44..BL-50, F-33).

North star: *the cost of the process scales with the size and risk of the change, and every gate, lane and judge
the method adds is measured from the change's own artifacts — so that turning the 3.13 advisory defaults into 4.0
blocking ones is decided on data from 4–6 measured changes, not on opinion.*

### Strategic value
A method that is skipped for small work, or approved as a rubber stamp, protects nothing. Lanes make the method the
cheapest legitimate path; judges give the human an independent verdict at the cheap end of the cycle; the release
manifest makes "what was approved" equal "what shipped"; metrics make every one of these claims checkable.

### Design decisions
| Topic | Decision |
|------|----------|
| Human gates per feature | D-22 — three merged gates (+ `--granular-gates`) |
| Judges | D-23 — advisory at requirements, architecture, qa; intra-model accepted when declared |
| Versioning | D-24 — 3.13 opt-in / advisory; 4.0 when defaults turn blocking |
| `patch` lane | D-25 — official path for a small bug (BUG-NN + finding + fix + regression test) |
| Release per change | D-26 — `Karvey-Change` trailer required; integration by PR; trunk recommended |
| Knowledge sync | D-27 — graphify optional; `knowledge_sync: none` by default |
| `patch` criterion | D-29 — ≤ 3 code files, no schema / API contract / permissions change, Tier < 3 |
| Judge budget | D-30 — no cap; cost measured per gate and per change |
| Architecture | `architecture.md` — lane table + check-mode registry as data; append-only logs in spec.json; judges as clean-context subagents + deterministic collector; release manifest from trailers; L-40..L-54 (architect's defaults A-01..A-13, D-21) |

---

## Features

| Feature | Area | Requirements covered | Panel / sources | Status |
|---------|------|----------------------|-----------------|--------|
| F1 | Flow metrics, gate outcomes, deploy records, retro | REQ-W2-001..010 | R-14 · DM-11, PM-05, PM-12 · D-24, D-30 · BL-17, BL-45 | ⬜ |
| F2 | Lanes with objective criteria, official `patch` lane | REQ-W2-011..021 | R-09 · DM-01, PM-09, H-03, H-04 · D-25, D-29 · BL-12 | ⬜ |
| F3 | Advisory judges (incl. the qa fiscal) | REQ-W2-022..033 | R-11 / JU-01 · AG-12, DM-06, DM-08, B-12 · D-23, D-30 · BL-14 | ⬜ |
| F4 | Three merged human gates, one question, `-y` = auto | REQ-W2-034..042 | R-10 · DM-06, AG-08, H-06 · D-22 · BL-13 | ⬜ |
| F5 | Release per change: trailer, manifest, integration PR, trunk | REQ-W2-043..053 | R-08 · DM-03, PM-04, H-21, F-28..F-30 · D-26 · BL-11, BL-46..BL-48 | ⬜ |
| F6 | Living spec merged before production | REQ-W2-054..056 | R-17 (timing) · DM-09 · BL-20 | ⬜ |
| F7 | Test-first and traceability | REQ-W2-057..063 | R-12 · DM-07 · BL-15 | ⬜ |
| F8 | Deterministic security tools | REQ-W2-064..068 | R-13 · DM-08 · BL-16 | ⬜ |
| F9 | Release-gate, id, health and evidence scripts | REQ-W2-069..074 | R-20 · AG-07, AG-10, AG-12, PM-13, F-26 · BL-23, BL-44 | ⬜ |
| F10 | Post-deploy verification with thresholds | REQ-W2-075..078 | R-23 · DM-10 · BL-26 | ⬜ |
| F11 | Knowledge sync optional | REQ-W2-079 | R-16 · D-27 | ⬜ |
| F12 | Deferred Wave 1 backlog | REQ-W2-080..082 | F-31, F-32, F-33 · BL-49, BL-50 | ⬜ |
| F13 | Rollout 3.13 → 4.0 and dogfooding | REQ-W2-083..088 | Ola 2 plan · D-24, D-26 | ⬜ |

Internal order for tasks (panel Ola 2): F1 → F2 + F3 → F4 + F5 → F6..F12 → F13 (4.0 is a later release of its own).

## Tasks
(pending — karvey-tasks)

## History
| Date | Phase | Action |
|-------|------|--------|
| 2026-09-25 | init | Change initialised by the state tool; PRD written; spec.json metadata filled (strict validate 0 errors) |
| 2026-09-25 | requirements | 88 EARS requirements (REQ-W2-001..088), spec-delta (ADDED 88 · MODIFIED 9 · REMOVED 0); 13 open points listed for the *what* gate; not approved |
| 2026-09-25 | architecture | `architecture.md` generated (C-01..C-24, REQ-W2-001..088 covered, Tier 2 controls S-1..S-12, project-upgrade step declarations §7.4); infra skipped (no cloud); not approved |
