# Plan: living-docs

**Capability:** method | **Security Tier:** 3 | **Layers:** Backend
**Created:** 2026-09-26 | **Status:** 🔄 requirements
**Lane:** standard (no UI: sheets and READMEs are documents; mockup and design-graphic skipped by the lane)
**Release target:** 4.2.0 (minor, backward compatible with 4.1.0)
**Flow:** trunk (`feature/living-docs` → PR → `main`) · **Decision:** D-38 (D-01, D-20, D-21, D-24, D-30 hold)
**Sequencing:** spec phases now; implementation after `wave3-optimization`'s implementation (REQ-LD-057)

---

## Epic: Living documentation — captured instructions, component sheets, current READMEs

### Description
While a change is in flight the owner's instructions stay in the conversation and never reach the specs; the
project has no technical sheet per component (data shapes of a document store, service contracts, frontend
routes and permissions, infrastructure runbooks), so agents learn them from code or from failures; READMEs drift.
This Epic captures the owner's instructions through the prompt hook and gates every phase on their
classification, adds living component sheets mapped to code paths with a read-only schema check for document
stores, keeps each repository's README to a minimal section set, and brings all three to existing projects through
the upgrade plan.

North star: *no instruction the owner gives during an active change is lost — each is captured verbatim by the hook
and classified before its gate closes — and every component and repository of a project has a technical sheet and
a README that change in the same change as the code they describe.*

### Strategic value
Instructions repeated or lost between sessions cost the owner's time and produce specs that diverge from what was
asked; undocumented data shapes cause production failures; a repository nobody can start from its README costs
every newcomer. Documentation checked at the moment the code or the conversation changes stays true without a
documentation sprint.

### Design decisions
| Topic | Decision |
|------|----------|
| Scope | D-38 — instruction capture by the hook (agent never writes the rows) + classification gated by the state tool; component sheets per kind with lifecycle like living specs and a read-only NoSQL sampler; README section set; upgrade steps |
| Trust model | D-01 — rows written only by the hook, verified against a store the agent cannot write; review of generated sheets and removal of a row need the owner's own message |
| Architecture | (pending — karvey-architecture) |

---

## Features

| Feature | Area | Requirements covered | Status |
|---------|------|----------------------|--------|
| F1 | Instruction capture: detection, multilingual vocabulary, measured detector, off the record, only the human's text, redaction, tamper evidence, project inbox, never blocks, owner's setting, removal on request | REQ-LD-001..012, 058, 059, 060, 063 | ⬜ |
| F2 | Instruction classification: four classes with evidence, revision linkage, state-tool only, phase/gate refusal, gate summary, session/dashboard counts | REQ-LD-013..018 | ⬜ |
| F3 | Component map and sheet templates (data store, backend service, frontend module, infra resource), section check, no secrets, references resolve | REQ-LD-019..025 | ⬜ |
| F4 | Sheet lifecycle: component delta at architecture, tasks pair code and sheet, same-commit check, archive reconciliation, parallel deltas, judges read sheets, lanes without architecture, archive stamps and retires | REQ-LD-026..032, 062 | ⬜ |
| F5 | Document-schema check: example vs schema, read-only adapter, development targets by reference, bounded sample, value-free output, drift reported, relational sheets vs schema files | REQ-LD-033..038, 061 | ⬜ |
| F6 | Bootstrap for existing repositories: proposed map, draft sheets, leak check, human review, safe re-run | REQ-LD-039..043 | ⬜ |
| F7 | README kept current: section set, trigger check, undocumented settings, bootstrap/update, every repository | REQ-LD-044..048 | ⬜ |
| F8 | Integration: upgrade steps LD-1..LD-3, lanes and gates, load lists and size, core contract, check modes, backward compatibility, documentation | REQ-LD-049..055 | ⬜ |
| F9 | Change-scoped: dogfooding on this repository, implementation after Wave 3 | REQ-LD-056, 057 | ⬜ |

## Tasks
(pending — karvey-tasks)

## History
| Date | Phase | Action |
|-------|------|--------|
| 2026-09-26 | init | Change initialised (lane standard, Tier 3, D-38) |
| 2026-09-26 | requirements | 63 EARS requirements (61 ADDED, 2 MODIFIED living blocks, 2 change-scoped); judges domain + methods (intra-model, concerns) — 30 findings accepted and fixed in place, 1 rejected with reason |
| 2026-09-26 | mockup, design_graphic | skipped by the lane (standard: no UI — sheets and READMEs are documents) |
