# Plan: project-upgrade

**Capability:** method | **Security Tier:** 2 | **Layers:** Backend
**Created:** 2026-09-25 | **Status:** 🔄 in_progress
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
| F1 | The once-per-version offer (session hook) | REQ-UP-001..006 | ⬜ |
| F2 | The plan (upgrade tool `plan`) | REQ-UP-007..010 | ⬜ |
| F3 | Applying the plan (upgrade tool `apply`) | REQ-UP-011..019 | ⬜ |
| F4 | Initial step catalogue | REQ-UP-020..026 | ⬜ |
| F5 | The upgrade skill `/karvey-upgrade` | REQ-UP-027..029 | ⬜ |
| F6 | Every release declares its upgrade (L-37, docs) | REQ-UP-030..032 | ⬜ |

## Tasks

(pending — karvey-tasks)

## History

| Date | Phase | Note |
|---|---|---|
| 2026-09-25 | init | spec.json, prd.md, checkpoint with the plan checklist (D-20). |
| 2026-09-25 | requirements | 32 EARS requirements in 6 areas (REQ-UP-001..032), spec-delta ADDED 32; D-20 and BL-51 recorded. Awaiting the owner's approval. REQ-UP-005 (no offer when nothing applies) is an interpretation of D-20 to confirm at this gate. |
| 2026-09-25 | architecture | `architecture.md`: hook offer with an in-hook short-circuit probe (1.5 s budget), seen record resolved only by `karvey-upgrade.py seen` / the skill, engine as the single writer (pure step functions → edits, confinement, CAS, preview digest), 8 initial steps, skill flow to one PR, L-37 (release-surface fingerprint) + L-38 (catalogue) + L-39 (docs); 32/32 REQ-UP covered; architect decisions A-01..A-14 under D-21. Infra skipped (no cloud). Awaiting approval. |
