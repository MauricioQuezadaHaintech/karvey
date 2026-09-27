# Plan: mockup-conformance

**Capability:** method | **Security Tier:** 3 | **Layers:** Backend
**Created:** 2026-09-27 | **Status:** 🔄 requirements (merged *what* gate pending)
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
| Architecture | (pending — karvey-architecture) |

---

## Features

| Feature | Area | Requirements covered | Status |
|---------|------|----------------------|--------|
| F1 | Element ids in the mockup: required kinds, format and uniqueness, requirement attribute, UI coverage, deterministic element check and map, stability across iterations, preserved by design-graphic | REQ-MC-001..007 | ⬜ |
| F2 | Decisions written back: decision log, resolution into requirement revisions, approval refusal, captured-instruction link, frozen mockup hash, revisions shown at the gate | REQ-MC-008..013 | ⬜ |
| F3 | Implementation from the mockup: mandatory input, tasks name elements, structure and tokens from the mockup, stack-forced differences declared when made, same ids in the build, no invented elements | REQ-MC-014..018, 055 | ⬜ |
| F4 | Conformance gate: plan, viewports, presence, same viewport and state, marked difference, text and style differences, pixel threshold, unmeasured pairs, browse settings, no production, evidence bound to the commit, capture storage | REQ-MC-019..029, 054 | ⬜ |
| F5 | Mockup deviations: every difference an entry, resolutions, owner approval through the hook, QA / release / deploy refusal, gate summary, QA's visual audit | REQ-MC-030..035 | ⬜ |
| F6 | Traceability matrix to evidence, complete before release | REQ-MC-036, 037 | ⬜ |
| F7 | Targets: web, mobile and desktop, command line, others out of scope by name | REQ-MC-038..041 | ⬜ |
| F8 | Integration: lanes, gates, design system, load lists and size, frontend-module sheets, upgrade steps MC-1..MC-3, changes past their mockup, check modes, backward compatibility, documentation | REQ-MC-042..051 | ⬜ |
| F9 | Change-scoped: dogfooding on fixture projects, implementation after living-docs | REQ-MC-052, 053 | ⬜ |

## Tasks

(pending — karvey-tasks)

## History
| Date | Phase | Action |
|-------|------|--------|
| 2026-09-27 | init | Change initialised (lane standard, Tier 3, D-40) |
| 2026-09-27 | requirements | 55 EARS requirements (51 ADDED, 2 MODIFIED living blocks through REQ-MC-036/046, 2 change-scoped); judges domain + methods (intra-model, concerns) — 31 findings routed in place pre-approval (30 accepted, F-29 partly rejected with reason); merged *what* gate pending |
| 2026-09-27 | mockup, design_graphic | to be skipped by the lane on advance (standard: this repository has no UI; proven on fixture UI projects, REQ-MC-052) |
