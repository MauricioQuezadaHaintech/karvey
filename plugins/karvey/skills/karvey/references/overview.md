# Karvey — overview of the method

Reference of the orchestrator, loaded only when the user asks what Karvey is, how its phases work or where its files
live. Routing (what runs next) never needs it: the state tool answers that.

> **Karvey** is an **ona/selknam** word meaning ***Afán*** ('Afán' = zeal/drive). A **stack-agnostic** business
> development method (web, mobile, desktop, CLI, API, embedded…).

## The Karvey Method

Karvey is a spec-driven development (SDD) method for enterprise projects, **stack-agnostic**. It combines:
- **Pre-spec interrogation** (grill-me style) + "10-star product" reframe: discover and improve what's going to be built before specifying it
- **PRD as foundation**: every change is born from a Product Requirements Document (`prd.md`); the EARS requirements trace back to it
- **EARS requirements + living specs** (openspec/kiro style): formal, cumulative specifications
- **Navigable mockup** (with shotgun mode for variants): validate UX before designing
- **Systemic graphic design** over one project design system: a per-change delta, computed contrast and a design judge; OKLCH colors, typography, spacing, per platform (WCAG/HIG/Material)
- **Enterprise architecture**: layered security Tiers 1–4, diagrams, edge cases, trust boundaries, cloud infrastructure
- **Infrastructure as code + CI/CD**: IaC and pipelines per cloud and git platform, with a security review
- **10–30 min AI tasks** + management in the **team's tracker** (ClickUp, Jira, Linear, Azure Boards, GitHub Projects, spreadsheet) or Markdown `PLAN.md` — tool and status flow are **team settings** in `project.json`, spoken as logical states `todo | in_progress | review | done | blocked` (`../rules/management-adapters.md`); notifications go to the **team's channel** (`../rules/notifications.md`)
- **DB/Backend/Frontend + E2E testing** in the target's real runtime, with benchmark and regression
- **9-dimension QA**: includes a blocking security gate (OWASP+STRIDE), cross-model second opinion, visual audit, and standards conformance (golden path + approved deviations)
- **Orderly deployment**: feature branch → living spec on the branch → PR to integration → release manifest and release gate → PR to production, triggered by the pipeline, verifying the PR's gates (CI + branch policies) before the prod OK, with post-deploy verification against thresholds
- **Branch hygiene — nothing left in branches**: once a branch is absorbed into production it is deleted (remote + local); a branch still carrying unreleased work is never deleted, it is reported — see `../rules/deploy-workflow.md` → *Branch hygiene*
- **Semver versioning + CHANGELOG** per component/repo, with human + AI model traceability
- **Persistent goal**: a north star that every phase re-reads so it never stops until the result is achieved, while respecting the gates
- **Spiral, not a line — iteration loop**: testing/QA/real-runtime surface defects and new ideas; the **iteration engine** (`karvey-iterate`) routes each finding back to its edge (`bug` → incident tracker + QA micro-loop · `spec-gap` → re-open requirements · `emergent` → discovery backlog) so **nothing is dropped**. See `../rules/iteration-loop.md`.
- **Incident tracker** (`BUG-NN` with state history) + **discovery backlog** (Markdown + the team's tracker) so bugs and post-cycle ideas stay traceable (`../rules/incident-tracking.md`, `../rules/backlog.md`)
- **Phase-close ritual**: logical status per task; tracker comment + cascade per Feature, so tasks never go stale — see `../rules/phase-close.md`
- **Multi-agent and multi-repo work**: parent/child changes across repos, business decisions (`D-NN`) and pinned inputs from design/copy/legal agents (`repo path @commit`) in `spec.json`, approvals that cite who approved and where, `[human]` tasks for steps only a person may run, `ops` and `hotfix` change types, light CI for docs-only PRs — see `../rules/multi-agent.md`
- **Cross-cutting layer of support skills** (investigate, second-opinion, health, browse, etc.) callable at any time
- **Agent handoff on every rotation** (`karvey-checkpoint`): identity, standing rules, board, closing checklist, **measured** repo state and scheduled tasks — for a single agent as much as for a team, and reinjected by the plugin's session hook, which also contrasts it against the live repos
- **Optional team layer** (`../rules/team.md`): roles, census, decision log and **cost measurement** for work split across several agent sessions. **Opt-in and not the default** — Karvey is complete with one agent, and the measured run behind this layer cost ≈US$1,000 in 3 days before going back to one.
- **Verification rules before reporting "done"** (`../rules/verification.md`): the failure modes that make a green report false
- **Enforcement by hooks**: prod-gate on by default, git-flow and plan-gate opt-in (`../rules/enforcement.md`); the phase graph is data (`../rules/state-machine.md`) and **archive** merges the spec-delta with a script

## Complete pipeline

```
PHASE 0 ─── /karvey-grill          → Pre-spec + 10-star reframe (+ platform/cloud)
PHASE 1 ─── /karvey-init           → change-id, project.json (+ team settings), prd.md, spec.json, Epic
PHASE 2 ─── /karvey-requirements   → EARS requirements (trace to the PRD), spec-delta, approval
PHASE 3 ─── /karvey-mockup         → Navigable 3–4 levels + spec↔mockup validation (+ shotgun mode)
PHASE 4 ─── /karvey-design-graphic → OKLCH visual system + 0-10 scoring + visual components catalog
PHASE 5 ─── /karvey-architecture   → Architecture, Tiers, diagrams, edge cases, Cloud Infra
PHASE 6 ─── /karvey-infra          → IaC + CI/CD pipelines + infra security review
PHASE 7 ─── /karvey-tasks          → 10–30 min tasks, E{n}.F{n}.T{n}, team's tracker / sprint
PHASE 8 ─── /karvey-impl           → Implementation DB→Backend→Frontend, commits + CHANGELOG
PHASE 9 ─── /karvey-test           → Unit + E2E in the target's real runtime, benchmark, regression
PHASE 10 ── /karvey-qa             → QA 9D + blocking security gate, REVISION_PR
PHASE 11 ── /karvey-deploy         → Orderly deployment feature→PR dev→release gate→PR master + post-deploy verification
PHASE 12 ── /karvey-archive        → Merge spec-deltas, retro, docs, close Epic + backlog sweep
```

### Feedback edges — the spiral (not part of the linear count)

Findings from `test`/`qa`/`browse` land in `findings.md` and are routed by `/karvey-iterate`:

```
   test · qa · browse ──→ findings.md ──→ /karvey-iterate (the engine)
                                              ├─ bug      → BUG-NN tracker → impl→test→qa micro-loop
                                              ├─ spec-gap → re-open PHASE 2 requirements (ripple only affected phases)
                                              └─ emergent → discovery backlog → future change-id (swept at archive)
```

A change is **done** only when `findings.md` has no open `bug`/`spec-gap` and all `emergent` are captured (convergence rule, `../rules/iteration-loop.md`).

## Cross-cutting layer — support skills (callable at any time)

These are not phases; they do not advance `spec.json:phase` forward. See `../rules/support-skills.md`.

```
/karvey-iterate            → Iteration engine: route findings (bug/spec-gap/emergent) to their edge
/karvey-investigate        → Root-cause debugging (Iron Law: no fix without investigating)
/karvey-second-opinion     → Adversarial cross-model review (Claude vs another model)
/karvey-judges             → Independent judges per lens before a gate (advisory, cited findings)
/karvey-health             → 0-10 dashboard (type/lint/tests/dead-code) + trend
/karvey-browse             → "Give it eyes": the target's real runtime (browser/sim/CLI)
/karvey-checkpoint         → Save/restore work state + the agent's handoff (who I am, rules, board, checklist, state)
/karvey-diagram            → Text → mermaid + excalidraw + SVG/PNG
/karvey-docs               → Diataxis + update stale docs + PDF
/karvey-guard              → Install/remove enforcement hooks; edit-lock
/karvey-devex              → Onboarding/DX review (time-to-hello-world)
/karvey-retro              → Retrospective (velocity, test health, per person)
/karvey-scrape             → Extract web data + encode it as a skill
/karvey-benchmark-models   → Compare models (latency/tokens/cost/quality)
/karvey-import             → Convert Kiro/gstack specs into Karvey (docs/spec/)
/karvey-standards          → Uplift engineering standards (golden paths) from the real system → standards repo
/karvey-team               → OPTIONAL team layer: roles, census, relay, cost (one agent is the default)
/karvey-decisions          → Decision log (D-NN / C-NN) + cross-check before declaring a block
```

Support view: `/karvey-context [--capability X] [--change Y]` → dashboard + deployment queue + live branches (read-only; one of the 19 support skills).

## Description of each phase

### PHASE 0: /karvey-grill
Pre-spec interrogation + "10-star product" reframe (optional). Produces a synthesis (input to the PRD). Asks about git platform, cloud, IaC.

### PHASE 1: /karvey-init
Creates/reads `docs/spec/project.json` (git, cloud, IaC, knowledge_sync, targets, repos, spec_repo, branch_flow, enforcement) plus the **team settings** asked once — `notifications` (channel) and `management` (tool + status map); `/karvey-init --settings` re-runs only that step. Captures the **goal**. Generates `change-id`, `prd.md`, `spec.json`. Epic in the team's tracker or `PLAN.md`.

### PHASE 2: /karvey-requirements
EARS requirements, each one **traced to a section of the PRD**. `requirements.md`, `spec-delta.md`.

### PHASE 3: /karvey-mockup
Navigable **3–4 levels** (deeper when the flow warrants it), adapted to the target. Shotgun mode (N variants + board). Includes a **spec↔mockup validation** pass: walk the mockup against `requirements.md` to catch spec-gaps *before* design/architecture/impl (cheap correction). `mockup.html` (or the target's equivalent).

### PHASE 4: /karvey-design-graphic
Reads the project design system and records only the change's **design delta**; contrast computed by `karvey-contrast-check.py`; the score comes from a **design judge**, not the phase. Per-platform guidance (WCAG/HIG/Material). The **visual components catalog** (art brief per screen/modal/component) only on an asset request. `design-spec.md`, `design-delta.md`, `contrast.json`.

### PHASE 5: /karvey-architecture
Boundaries, security per Tier, diagrams (mermaid), edge cases, trust boundaries, test coverage plan, **Cloud Infrastructure** section. `architecture.md`.

### PHASE 6: /karvey-infra
IaC (Terraform/Bicep/Pulumi) + CI/CD pipelines (GitHub Actions/Azure Pipelines), idempotent + platform auto-detection + infra security review. `infra.md`.

### PHASE 7: /karvey-tasks
10–30 min tasks, `E{n}.F{n}.T{n} [DB/Backend/Frontend/Infra]`. Reads `architecture.md` + `infra.md`. `tasks.md`.

### PHASE 8: /karvey-impl
Executes tasks on `feature/{change-id}` (never dev/master). One CHANGELOG `[Unreleased]` line per commit (human + AI model + why); the version is bumped once, at the release.

### PHASE 9: /karvey-test
Unit + E2E in the target's **real runtime**, performance benchmark, regression tests. Writes observations to `findings.md` (classified bug/spec-gap/emergent) and promotes confirmed bugs to the `BUG-NN` incident tracker. `test_evidence.md`.

### PHASE 10: /karvey-qa
9-dimension QA: Security (blocking gate, OWASP+STRIDE), Errors, Consistency, Impact, Env vars, Versioning (CHANGELOG), cross-model Second-opinion, Visual audit, Standards conformance (golden path + `deviations.md`). Appends findings to `findings.md`; on open `bug`/`spec-gap` it routes via `/karvey-iterate` instead of advancing. `REVISION_PR_{n}_{date}.md`. Notifies the team's channel (event `qa`).

### PHASE 11: /karvey-deploy
Orderly per-repo flow: pull → feature → living spec merged on the branch → PR to dev, merged by the host (DEV pipeline) → post-deploy verification → pull → release manifest + release gate → PR dev→master listing every change → verify the PR's gates (CI + branch policies) → PROD with human OK → post-deploy verification → **branch hygiene** (delete absorbed branches, report the rest). Detects the git host (`gh` / `az repos` / `glab`). Semver bump + CHANGELOG per component/repo. Version visible in the front end (recommended): **dev version in DEV** (`x.y.z-dev.N+sha`), **release version in PROD**, checked by the post-deploy verification. Never deploy manually. Notifies the team's channel (event `deploy`).

### PHASE 12: /karvey-archive
Merge spec-deltas into living specs, archive, close the Epic. **Backlog sweep:** review open `emergent` items from this change and offer to promote them into new `change-id`s (so post-cycle discoveries don't evaporate). Recommended optional: `/karvey-retro` + `/karvey-docs`.


## Method directory structure

`docs/spec/` lives in the project's **main repo** (`spec_repo`). A project has 1 or more repos, never zero.

In multi-repo work each repo with its own code keeps its own `docs/spec/` with **child** changes; the **parent** change and the business decision log (`D-NN`) live in the operations repo. Cross-repo references are always `{change-id}@{repo}`, `D-NN@{repo}` or `{repo} {path} @{commit}` (see `../rules/multi-agent.md`).

```
docs/spec/
├── project.json                       ← Config (git, cloud, IaC, targets, knowledge_sync, repos, enforcement, notifications, management)
├── backlog.md                         ← Discovery backlog (emergent items → future change-ids)
├── incidents-index.md                 ← Global index of all BUG-NN across repos + current state
├── standards/                         ← Engineering golden paths ("how we build here", per layer)
│   ├── _index.md  · db.md · backend.md · frontend.md   ← loaded as a hard constraint by architecture/impl
├── specs/{capability}/spec.md         ← Living specs (cumulative per capability)
└── changes/{change-id}/
    ├── spec.json                      ← Metadata, type, phase, approvals (+ by/ref, prod), goal, links, decisions, inputs, iteration_count, revision_history
    ├── prd.md                         ← Product Requirements Document
    ├── requirements.md                ← EARS (trace to the PRD)
    ├── spec-delta.md  · mockup.* · design-spec.md
    ├── architecture.md                ← + Cloud Infrastructure
    ├── infra.md  · tasks.md  · checkpoint.md
    ├── findings.md                    ← Triage inbox (bug/spec-gap/emergent) routed by karvey-iterate
    ├── deviations.md                  ← Approved departures from engineering standards (design mode)
    ├── PLAN.md (Markdown tracker)  · IMPLEMENTED
    └── archive/{YYYY-MM-DD}-{change-id}/
```

The code (incl. IaC and pipelines), each repo's `docs/bugs_dev_testing.md` incident tracker, the per-component/repo `CHANGELOG.md`, and the `settings.json` hooks live in each repo of `project.json:repos`.

## Authorship, license, and trademark

- **Etymology:** *Karvey* is an **ona/selknam** word meaning ***Afán*** ('Afán' = zeal/drive).
- **Author:** A business development model created by **Mauricio Quezada Ibáñez**, **HainTech**. Owned by HainTech.
- **License:** **Apache License 2.0** — see `LICENSE` and `NOTICE`. Anyone may use, modify, and adapt it (incl. commercial use) while respecting the license.
- **Trademark:** "Karvey" and the `karvey-*` convention are a trademark of HainTech. Adaptations permitted with attribution; see `TRADEMARK.md`.
- **Credits / inspiration:** Karvey synthesizes the **first-hand experience** of Mauricio Quezada Ibáñez (HainTech) with conceptual ideas from **Kiro** (spec-driven / cc-sdd) and **gstack** (Garry Tan). It is synthesis and conceptual inspiration; it **does not incorporate code** from those projects.
