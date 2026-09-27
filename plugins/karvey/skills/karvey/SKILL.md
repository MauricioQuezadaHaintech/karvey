---
name: karvey
description: Karvey support — method entry point: shows the pipeline, a change's state and the next skill to run. Triggers include "karvey", "método karvey", "karvey method", "pipeline karvey", "qué sigue en karvey", "what's next in karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: [<change-id>] [--phase <fase>] [--autoplan]
---

# Karvey — Method Orchestrator

Load: _core.md, references/overview.md?, references/equivalences.md?

## Purpose

The entry point of the Karvey Method: it says where a change is and which skill runs next. It **only routes**:
the state tool decides the phase, the lane decides which phases run, the skill does the work.

## Route a change

Ask the state tool (`karvey-state.py next`):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" next "{change-id}" --json
```

Relay `status` (`in-progress | awaiting-approval | ready | invalid`), the next `skill` and its `blockers`; never
infer the phase from `spec.json` by hand. On `invalid`, show the validation errors and offer
`karvey-state.py validate --fix --dry-run`; do not guess a next step. Then:

- **Findings first:** an open `bug` or `spec-gap` in `findings.md`, or an `emergent` item not yet in the backlog →
  the next step is `/karvey-iterate`, not forward (convergence).
- **`awaiting-human` tasks** block only their dependents: show each first, with its executor and verification.
- **Parent change** (`links.children` not empty): show each child's phase (`{change-id}@{repo}`); the parent reaches
  `deployed` only when every child is deployed or descoped by a decision.
- Show the status line: capability, lane, phase, Tier, goal, approvals (with `by`/`ref`), open findings, next skill.

## The pipeline

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

`/karvey-grill` (phase 0) is optional and runs before `init`. Which phases a change runs depends on its lane
(`spec.json:lane`, `${CLAUDE_PLUGIN_ROOT}/schemas/lanes.json`): `m` runs, `o` optional, `s` skipped (recorded by the state tool).

<!-- karvey:generated routing -->
| Phase | Skill | patch | standard | feature-ui | ops | hotfix | docs |
|---|---|---|---|---|---|---|---|
| `init` | `/karvey-init` | m | m | m | m | m | m |
| `requirements` | `/karvey-requirements` | s | m | m | m | s | o |
| `mockup` | `/karvey-mockup` | s | s | m | s | s | s |
| `design_graphic` | `/karvey-design-graphic` | s | s | m | s | s | s |
| `architecture` | `/karvey-architecture` | s | m | m | s | s | s |
| `infra` | `/karvey-infra` | s | o | o | m | s | s |
| `tasks` | `/karvey-tasks` | s | m | m | m | s | o |
| `impl` | `/karvey-impl` | m | m | m | m | m | m |
| `test` | `/karvey-test` | m | m | m | m | m | o |
| `qa` | `/karvey-qa` | m | m | m | o | o | m |
| `deploying` | `/karvey-deploy` | m | m | m | m | m | m |
| `deployed` | `/karvey-deploy` | m | m | m | m | m | m |
| `archived` | `/karvey-archive` | m | m | m | m | m | m |
<!-- /karvey:generated routing -->

## Arguments

- **No arguments:** show the pipeline, then run `/karvey-context` (capabilities, active changes, queue).
- **`<change-id>`:** *Route a change* above.
- **`--phase <phase>`:** what a phase does and its rules → load `references/overview.md`.
- **`--autoplan`:** run the planning phases in sequence (grill → architecture), grouping the gate questions and
  escalating only the substantive decisions (taste, scope, security). It never skips a gate.
- **The user asks what Karvey is**, its features, files or authorship → load `references/overview.md`.
- **The user comes from Kiro or gstack** and asks where a command lives → load `references/equivalences.md`.

## Support skills (callable at any time; they never advance the phase)

`/karvey-iterate` (route findings) · `/karvey-investigate` (root cause first) · `/karvey-judges` (independent
verdict before a gate) · `/karvey-second-opinion` · `/karvey-health` · `/karvey-browse` · `/karvey-checkpoint`
(save/restore, handoff; one phase per session) · `/karvey-context` (dashboard, report, portfolio, backlog) ·
`/karvey-decisions` · `/karvey-diagram` · `/karvey-docs` · `/karvey-guard` · `/karvey-devex` · `/karvey-retro` ·
`/karvey-scrape` · `/karvey-benchmark-models` · `/karvey-import` · `/karvey-standards` · `/karvey-team` (optional
team layer; one agent is the default).

## Rules each phase loads

Each phase skill declares its closed list on its `Load:` line; this table is generated from those lines
(`karvey-context-budget.py render`).

<!-- karvey:generated load-lists:orchestrator -->
| Rule | Applies in |
|---|---|
| `_core` | every skill with a `Load:` line |
| `adapters/{tool}` | init, requirements, tasks, impl, qa, deploy, archive |
| `backlog` | archive, iterate |
| `changelog-policy` | impl, deploy |
| `deploy-workflow` | infra, deploy |
| `ears-format` | requirements |
| `engineering-standards` | architecture, impl |
| `gates` | init, requirements, mockup, design-graphic, architecture, infra, tasks, impl, test, qa, deploy, archive |
| `incident-tracking` | iterate |
| `iteration-loop` | test, qa, iterate |
| `judges` | requirements, design-graphic, architecture, judges |
| `judges/{phase}` | judges |
| `knowledge-sync` | archive |
| `lanes` | init |
| `living-specs` | requirements, archive |
| `management-adapters` | init, requirements, tasks, impl, qa, deploy, archive, iterate |
| `multi-agent` | decisions |
| `notifications` | qa, deploy, iterate |
| `phase-close` | impl, test, qa, iterate |
| `project-config` | init |
| `risks` | archive, iterate |
| `security-tiers` | requirements, architecture, infra |
| `targets` | mockup, design-graphic, infra, test |
| `versioning` | qa, deploy |
<!-- /karvey:generated load-lists:orchestrator -->

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `TRADEMARK.md`. Karvey = Afán, an ona/selknam word.*
