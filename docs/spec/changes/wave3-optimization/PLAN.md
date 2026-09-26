# Plan: wave3-optimization

**Capability:** method | **Security Tier:** 2 | **Layers:** Backend, Frontend, Infra
**Created:** 2026-09-26 | **Status:** 🔄 requirements generated — awaiting the *what* gate (requirements + mockup + design)
**Lane:** feature-ui (the sponsor page and the method page are UI: mockup and design-graphic run)
**Release target:** 4.1.0 (minor, backward compatible with 4.0.0)
**Flow:** trunk (`feature/wave3-optimization` → PR → `main`) · **Decisions:** D-30, D-31, D-32 (D-01..D-29 hold)
**Depends on:** `wave2-structural` (3.13.0 / 4.0.0) merged first

---

## Epic: Wave 3 optimisation — smaller phases, informed sponsors, one portfolio

### Description
Every phase still loads most of the rules transitively; the sponsor learns a change's state only by asking; open
questions and risks have no owner or date; the cost of a change is measured only for judges and teams; each UI change
redesigns the palette; "Feature" means two things; nobody sees all the organisation's repositories at once; the backlog
does not rank; several steps assume one OS, country, language and runtime (panel review 2026-09-23, Ola 3: R-15, R-19,
R-24..R-30). This Epic measures the per-phase context first, adds the data areas, reorganises the skills on top of the
final text, and — last, by the owner's request — adds four languages to the method page (B-06).

North star: *every phase loads only the instructions it declares, and the sponsor of any change can read — from one page
produced from the change's own artifacts — its scope, state, measured cost, open risks and the decisions it waits for,
while the organisation sees every Karvey repo in one read-only portfolio; the per-phase instruction size and the cost per
change are measured before and after, never capped.*

### Strategic value
Instructions a phase does not use cost money and attention on every turn; a sponsor who is not told waits or escalates;
an unowned risk reaches production; an unmeasured change cannot be priced. Wave 3 turns the data Wave 2 started to
record into views for the people who decide, and makes the method cheaper to run and easier to adopt outside the
author's environment.

### Design decisions
| Topic | Decision |
|------|----------|
| Client report | D-31 — one HTML page per change for the sponsor (scope, state, cost, risks), at every gate close, to the stakeholder declared in `project.json` |
| Portfolio and runtimes | D-32 — one portfolio over every Karvey repo of the organisation; Claude Code only; R-30 = portability guide |
| Cost | D-30 — measured, never capped |
| Architecture | (pending — karvey-architecture) |

---

## Features

Internal order: F1 (baseline) first; F3..F10 add data and views; F2 (reorganisation) runs over the final Wave 3 text;
F11 rollout; **F12 last** (B-06).

| Feature | Area | Requirements covered | Panel / sources | Status |
|---------|------|----------------------|-----------------|--------|
| F1 | Context measurement: size tool, baseline, CI | REQ-W3-001, 002, 010, 011 | R-15 · AG-04, H-34 · BL-18 | ⬜ |
| F2 | Context budget: core, load lists, adapters, references, routing-only orchestrator, contract coverage, generated lists, one phase per session | REQ-W3-003..009, 012, 013 | R-15 · AG-04 · BL-18, BL-39 | ⬜ |
| F3 | Cost per change with a single agent | REQ-W3-014..019 | R-25 · PM-08 · D-30 · BL-28, BL-37 | ⬜ |
| F4 | Sponsor page, report, "your turn" events, deduplication | REQ-W3-020..027 | R-19 · PM-07 · D-31 · BL-22, BL-43 | ⬜ |
| F5 | Open questions Q-NN and risk register | REQ-W3-028..034 | R-24 · PM-11 · BL-27 | ⬜ |
| F6 | Project design system, design delta, contrast tool, design judge | REQ-W3-035..039 | R-26 · DM-13, AG-12 · D-23, D-30 · BL-29 | ⬜ |
| F7 | One work breakdown (WBS) | REQ-W3-040..043 | R-27 · PM-10 · BL-30 | ⬜ |
| F8 | Organisation portfolio | REQ-W3-044..048 | R-28 · PM-14 · D-32 · BL-31, BL-40 | ⬜ |
| F9 | Backlog ranked by WSJF, `done-direct` | REQ-W3-049..052 | R-29 · PM-15 · BL-32 | ⬜ |
| F10 | Portability (guide, browse.via, OS/time neutrality, neutral states, loaded version, settings validation) | REQ-W3-053..060 | R-30 · AG-14 · D-32 · BL-33, BL-38 | ⬜ |
| F11 | Rollout 4.1.0 and dogfooding | REQ-W3-061..065 | Ola 3 plan · D-24, D-26, D-31 | ⬜ |
| F12 | **Last:** method page in it / ja / fr / ko, alias table | REQ-W3-066..070 | B-06 · BL-42 | ⬜ |

Coverage: 70 of 70 REQ-W3 in exactly one Feature.

## Tasks
(pending — karvey-tasks)

## History
| Date | Phase | Action |
|-------|------|--------|
| 2026-09-26 | init | Change initialised (state tool), lane `feature-ui`; prd.md; spec.json validated `--strict` |
| 2026-09-26 | requirements | requirements.md (70 REQ-W3, 11 areas), spec-delta.md (ADDED 70, MODIFIED 6, REMOVED 0), Features F1..F12; generated — awaiting the *what* gate |
