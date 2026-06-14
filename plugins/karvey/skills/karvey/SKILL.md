---
name: karvey
description: Orchestrator of the Karvey Method — the complete spec-driven development (SDD) pipeline, stack-agnostic. Shows the pipeline state, guides which skill to run at each phase, and is the method's entry point. A synthesis of first-hand experience + Kiro + gstack. Triggers include "karvey", "método karvey", "karvey method", "pipeline karvey", "qué sigue en karvey", "what's next in karvey", "iniciar proyecto", "start project", "spec-driven", "spec driven development", "SDD", "specification-driven", "kiro", "cc-sdd", "openspec", "gstack", "g-stack", "Garry Tan", "spec kit", "PRD", "requirements engineering", "living specs", "método de desarrollo", "development method", "development pipeline", "SDLC", "desarrollo con IA", "AI-assisted development", "agentic development", "equipo virtual de ingeniería", "virtual engineering team", "vibe coding".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [<change-id>] [--phase <fase>] [--autoplan]
---

# Karvey — Method Orchestrator

> **Karvey** is an **ona/selknam** word meaning ***Afán*** ('Afán' = zeal/drive).
> A **stack-agnostic** business development method (web, mobile/iOS/Android, desktop, CLI, API, embedded…). Created by **Mauricio Quezada Ibáñez** (HainTech). See "Authorship, license, and trademark" at the end.

## Purpose

The entry point to the Karvey Method. It shows the complete pipeline, the current state of a specific change, and guides the engineer toward the next skill to run. It works for **any stack**: the project declares its `targets` and each phase adapts (see `rules/targets.md`).

## The Karvey Method

Karvey is a spec-driven development (SDD) method for enterprise projects, **stack-agnostic**. It combines:
- **Pre-spec interrogation** (grill-me style) + "10-star product" reframe: discover and improve what's going to be built before specifying it
- **PRD as foundation**: every change is born from a Product Requirements Document (`prd.md`); the EARS requirements trace back to it
- **EARS requirements + living specs** (openspec/kiro style): formal, cumulative specifications
- **Navigable mockup** (with shotgun mode for variants): validate UX before designing
- **Systemic graphic design** with 0-10 scoring: OKLCH colors, typography, spacing, per platform (WCAG/HIG/Material)
- **Enterprise architecture**: layered security Tiers 1–4, diagrams, edge cases, trust boundaries, cloud infrastructure
- **Infrastructure as code + CI/CD**: IaC and pipelines per cloud and git platform, with a security review
- **10–30 min AI tasks** + ClickUp or Markdown management
- **DB/Backend/Frontend + E2E testing** in the target's real runtime, with benchmark and regression
- **8-dimension QA**: includes a blocking security gate (OWASP+STRIDE), cross-model second opinion, and visual audit
- **Orderly deployment**: feature branch → dev → PR to master, triggered by the pipeline, with post-deploy canary
- **Semver versioning + CHANGELOG** per component/repo, with human + AI model traceability
- **Persistent goal**: a north star that every phase re-reads so it never stops until the result is achieved, while respecting the gates
- **Cross-cutting layer of support skills** (investigate, second-opinion, health, browse, etc.) callable at any time
- **Optional enforcement via hooks** (git-flow + plan-gate) and **archive** with spec merge

## Complete pipeline

```
PHASE 0 ─── /karvey-grill          → Pre-spec + 10-star reframe (+ platform/cloud)
PHASE 1 ─── /karvey-init           → change-id, project.json, prd.md, spec.json, ClickUp Epic
PHASE 2 ─── /karvey-requirements   → EARS requirements (trace to the PRD), spec-delta, approval
PHASE 3 ─── /karvey-mockup         → Navigable 3 levels (+ shotgun variants mode)
PHASE 4 ─── /karvey-design-graphic → OKLCH visual system + 0-10 scoring per dimension
PHASE 5 ─── /karvey-architecture   → Architecture, Tiers, diagrams, edge cases, Cloud Infra
PHASE 6 ─── /karvey-infra          → IaC + CI/CD pipelines + infra security review
PHASE 7 ─── /karvey-tasks          → 10–30 min tasks, E{n}.F{n}.T{n}, ClickUp sprint
PHASE 8 ─── /karvey-impl           → Implementation DB→Backend→Frontend, commits + CHANGELOG
PHASE 9 ─── /karvey-test           → Unit + E2E in the target's real runtime, benchmark, regression
PHASE 10 ── /karvey-qa             → QA 8D + blocking security gate, REVISION_PR
PHASE 11 ── /karvey-deploy         → Orderly deployment feature→dev→PR master + canary
PHASE 12 ── /karvey-archive        → Merge spec-deltas, retro, docs, close Epic
```

## Cross-cutting layer — support skills (callable at any time)

These are not phases; they do not advance `spec.json:phase`. See `rules/support-skills.md`.

```
/karvey-investigate        → Root-cause debugging (Iron Law: no fix without investigating)
/karvey-second-opinion     → Adversarial cross-model review (Claude vs another model)
/karvey-health             → 0-10 dashboard (type/lint/tests/dead-code) + trend
/karvey-browse             → "Give it eyes": the target's real runtime (browser/sim/CLI)
/karvey-checkpoint         → Save/restore work state (handoff)
/karvey-diagram            → Text → mermaid + excalidraw + SVG/PNG
/karvey-docs               → Diataxis + update stale docs + PDF
/karvey-guard              → Install/remove enforcement hooks; edit-lock
/karvey-devex              → Onboarding/DX review (time-to-hello-world)
/karvey-retro              → Retrospective (velocity, test health, per person)
/karvey-scrape             → Extract web data + encode it as a skill
/karvey-benchmark-models   → Compare models (latency/tokens/cost/quality)
```

Support view: `/karvey-context [--capability X] [--change Y]` → dashboard + deployment queue.

## Execution by argument

### No arguments — Show the pipeline and project context

Show the pipeline above, then run the steps of `/karvey-context` (capabilities, active changes, archived ones, sprint, deployment queue).

### With `<change-id>` — Show the change's current phase

```bash
cat docs/spec/changes/{change-id}/spec.json 2>/dev/null || echo "Not found"
```

Read `spec.json` and determine the current phase based on `phase` and `approvals`:

| `phase` | `approvals` | Next skill |
|---------|-------------|-----------------|
| `init` | requirements.generated=false | `/karvey-requirements {change-id}` |
| `requirements` | requirements.approved=false | Approve requirements with the user |
| `requirements` | mockup.generated=false | `/karvey-mockup {change-id}` |
| `mockup` | mockup.approved=false | Iterate the mockup with the user |
| `mockup` | design_graphic.generated=false | `/karvey-design-graphic {change-id}` |
| `design_graphic` | design_graphic.approved=false | Review the design with the user |
| `design_graphic` | architecture.generated=false | `/karvey-architecture {change-id}` |
| `architecture` | architecture.approved=false | Review the architecture with the user |
| `architecture` | infra.generated=false | `/karvey-infra {change-id}` |
| `infra` | infra.approved=false | Review infra/pipelines with the user |
| `infra` | tasks.generated=false | `/karvey-tasks {change-id}` |
| `tasks` | tasks.approved=false | Review tasks with the user |
| `tasks` | tasks.approved=true | `/karvey-impl {change-id}` |
| `impl` | — | `/karvey-test {change-id}` |
| `test` | — | `/karvey-qa {change-id}` |
| `qa` | qa.approved=false (open criticals/highs) | Fix → re-impl → re-test → re-qa |
| `qa` | qa.approved=true | `/karvey-deploy {change-id}` |
| `deployed` | — | `/karvey-archive {change-id}` |

Show the user the status (capability, phase, Tier, management, **goal**, approvals including `infra`, `qa`, `deploy`) and the next step.

### With `--phase <fase>` — Detailed description of a phase

Valid phases: `grill`, `init`, `requirements`, `mockup`, `design-graphic`, `architecture`, `infra`, `tasks`, `impl`, `test`, `qa`, `deploy`, `archive`.

### With `--autoplan` — Planning chain

Run the planning phases (0→5) in sequence, chaining approvals, escalating to the user only the substantive decisions (taste, scope, security). Inspired by gstack's `autoplan`. It does not skip the approval gates; it groups them.

---

## Description of each phase

### PHASE 0: /karvey-grill
Pre-spec interrogation + "10-star product" reframe (optional). Produces a synthesis (input to the PRD). Asks about git platform, cloud, IaC.

### PHASE 1: /karvey-init
Creates/reads `docs/spec/project.json` (git, cloud, IaC, knowledge_sync, targets, repos, spec_repo, branch_flow, enforcement). Captures the **goal**. Generates `change-id`, `prd.md`, `spec.json`. ClickUp Epic or `PLAN.md`.
**Rules:** `project-config.md`, `clickup-protocol.md`, `living-specs.md`, `knowledge-sync.md`, `enforcement.md`

### PHASE 2: /karvey-requirements
EARS requirements, each one **traced to a section of the PRD**. `requirements.md`, `spec-delta.md`.
**Rules:** `ears-format.md`, `living-specs.md`, `security-tiers.md`

### PHASE 3: /karvey-mockup
Navigable 3 levels, adapted to the target. Shotgun mode (N variants + board). `mockup.html` (or the target's equivalent).

### PHASE 4: /karvey-design-graphic
OKLCH system + 0-10 scoring per dimension (what a 10 would be). Per-platform guidance (WCAG/HIG/Material). `design-spec.md`.

### PHASE 5: /karvey-architecture
Boundaries, security per Tier, diagrams (mermaid), edge cases, trust boundaries, test coverage plan, **Cloud Infrastructure** section. `architecture.md`.
**Rules:** `security-tiers.md`

### PHASE 6: /karvey-infra
IaC (Terraform/Bicep/Pulumi) + CI/CD pipelines (GitHub Actions/Azure Pipelines), idempotent + platform auto-detection + infra security review. `infra.md`.
**Rules:** `project-config.md`, `deploy-workflow.md`, `security-tiers.md`, `changelog-policy.md`

### PHASE 7: /karvey-tasks
10–30 min tasks, `E{n}.F{n}.T{n} [DB/Backend/Frontend/Infra]`. Reads `architecture.md` + `infra.md`. `tasks.md`.
**Rules:** `clickup-protocol.md`

### PHASE 8: /karvey-impl
Executes tasks on `feature/{change-id}` (never dev/master). Version bump + CHANGELOG per commit (human + AI model + why).
**Rules:** `deploy-workflow.md`, `changelog-policy.md`, `versioning.md`

### PHASE 9: /karvey-test
Unit + E2E in the target's **real runtime**, performance benchmark, regression tests. `test_evidence.md`.
**Rules:** `targets.md`

### PHASE 10: /karvey-qa
8-dimension QA: Security (blocking gate, OWASP+STRIDE), Errors, Consistency, Impact, Env vars, Versioning (CHANGELOG), cross-model Second-opinion, Visual audit. `REVISION_PR_{n}_{date}.md`.
**Rules:** `changelog-policy.md`, `versioning.md`

### PHASE 11: /karvey-deploy
Orderly per-repo flow: pull → feature → pull → merge dev (DEV pipeline) → canary → pull → PR dev→master (PROD with human OK) → canary. Semver bump + CHANGELOG per component/repo. Version visible in the front end (recommended). Never deploy manually.
**Rules:** `deploy-workflow.md`, `versioning.md`, `changelog-policy.md`, `project-config.md`

### PHASE 12: /karvey-archive
Merge spec-deltas into living specs, archive, close the Epic. Recommended optional: `/karvey-retro` + `/karvey-docs`.

---

## Method directory structure

`docs/spec/` lives in the project's **main repo** (`spec_repo`). A project has 1 or more repos, never zero.

```
docs/spec/
├── project.json                       ← Config (git, cloud, IaC, targets, knowledge_sync, repos, enforcement)
├── specs/{capability}/spec.md         ← Living specs (cumulative per capability)
└── changes/{change-id}/
    ├── spec.json                      ← Metadata, phase, approvals, goal
    ├── prd.md                         ← Product Requirements Document
    ├── requirements.md                ← EARS (trace to the PRD)
    ├── spec-delta.md  · mockup.* · design-spec.md
    ├── architecture.md                ← + Cloud Infrastructure
    ├── infra.md  · tasks.md  · checkpoint.md
    ├── PLAN.md (if markdown)  · IMPLEMENTED
    └── archive/{YYYY-MM-DD}-{change-id}/
```

The code (incl. IaC and pipelines), the per-component/repo `CHANGELOG.md`, and the `settings.json` hooks live in each repo of `project.json:repos`.

## Shared rules

| File | Applies in |
|---------|-----------|
| `rules/project-config.md` | init, architecture, infra, deploy, context |
| `rules/clickup-protocol.md` | init, tasks, impl, qa, deploy, archive |
| `rules/ears-format.md` | requirements |
| `rules/security-tiers.md` | requirements, architecture, infra, qa |
| `rules/living-specs.md` | init, requirements, archive |
| `rules/knowledge-sync.md` | all phases (at close) |
| `rules/targets.md` | mockup, design-graphic, architecture, test, qa, deploy |
| `rules/deploy-workflow.md` | infra, impl, deploy |
| `rules/changelog-policy.md` | impl, infra, deploy, qa |
| `rules/versioning.md` | impl, deploy, qa |
| `rules/enforcement.md` | init, guard |
| `rules/support-skills.md` | cross-cutting layer |

## If you come from Kiro or gstack — equivalences

Karvey absorbs the value of both. What in gstack are standalone commands lives here in a **phase** or in the **cross-cutting layer**.

| Kiro / gstack | In Karvey |
|---------------|-----------|
| kiro `/spec`, `/kiro-spec-*` | grill + PRD + EARS requirements (PHASE 0–2) |
| office-hours, plan-ceo-review | 10-star reframe in `karvey-grill` |
| plan-design-review, design-consultation, design-shotgun | `karvey-design-graphic` + `karvey-mockup` (shotgun) |
| plan-eng-review, diagram | `karvey-architecture` + `karvey-diagram` |
| setup-deploy | `karvey-infra` (platform auto-detection) |
| review, cso (OWASP+STRIDE), codex, design-review | `karvey-qa` (8 dim) + `karvey-second-opinion` |
| qa, browse, benchmark | `karvey-test` + `karvey-browse` + `karvey-health` |
| ship, land-and-deploy, canary | `karvey-deploy` |
| investigate | `karvey-investigate` |
| health | `karvey-health` |
| context-save/restore | `karvey-checkpoint` |
| document-generate/release, make-pdf | `karvey-docs` |
| retro | `karvey-retro` / PHASE 12 |
| learn, gbrain | `knowledge-sync` (graphify/obsidian) |
| careful, freeze, guard | `karvey-guard` + `enforcement.md` hooks |
| devex-review | `karvey-devex` |
| scrape, skillify | `karvey-scrape` |
| benchmark-models | `karvey-benchmark-models` |
| ios-qa, ios-fix, ios-design-review | generalized via `targets.md` (real runtime per target) |

N/A (gstack-proprietary, with a generic equivalent): `open-gstack-browser` → `karvey-browse` runtime; `gstack-upgrade` → N/A; `pair-agent`/`gbrain` → `knowledge-sync`.

## Quick reference commands

```
/karvey [<change-id>] [--phase <f>] [--autoplan]   → State / pipeline / chained planning
/karvey-context                                     → Dashboard + deployment queue
Phases: grill init requirements mockup design-graphic architecture infra
        tasks impl test qa deploy archive
Support: investigate second-opinion health browse checkpoint diagram
        docs guard devex retro scrape benchmark-models
```

---

## Authorship, license, and trademark

- **Etymology:** *Karvey* is an **ona/selknam** word meaning ***Afán*** ('Afán' = zeal/drive).
- **Author:** A business development model created by **Mauricio Quezada Ibáñez**, **HainTech**. Owned by HainTech.
- **License:** **Apache License 2.0** — see `LICENSE` and `NOTICE`. Anyone may use, modify, and adapt it (incl. commercial use) while respecting the license.
- **Trademark:** "Karvey" and the `karvey-*` convention are a trademark of HainTech. Adaptations permitted with attribution; see `TRADEMARK.md`.
- **Credits / inspiration:** Karvey synthesizes the **first-hand experience** of Mauricio Quezada Ibáñez (HainTech) with conceptual ideas from **Kiro** (spec-driven / cc-sdd) and **gstack** (Garry Tan). It is synthesis and conceptual inspiration; it **does not incorporate code** from those projects.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`. Karvey = Afán, an ona/selknam word.*
