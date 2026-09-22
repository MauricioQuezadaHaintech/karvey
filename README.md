# Karvey

> **Karvey** is an Ona/Selknam word meaning ***Afán*** (zeal / drive).

A **spec-driven development (SDD)** method for Claude Code, **stack-agnostic** (web, iOS/Android, desktop, CLI, API, embedded). It takes a change from idea to production through a 13-phase pipeline (0–12) with approval gates, plus a cross-cutting layer of support skills.

Created by **Mauricio Quezada Ibáñez** · **HainTech**. A synthesis of first-hand experience with conceptual ideas from **Kiro** (cc-sdd) and **gstack** (Garry Tan) — conceptual inspiration, none of their code.

## Pipeline (0–12)

```
0 grill → 1 init → 2 requirements → 3 mockup → 4 design-graphic → 5 architecture
→ 6 infra → 7 tasks → 8 impl → 9 test → 10 qa → 11 deploy → 12 archive
```

Each phase produces a document under `docs/spec/` and asks for your OK before advancing. The orchestrator `/karvey:karvey <change-id>` always tells you which phase you're in and which comes next.

### A spiral, not a line — the iteration loop

The pipeline is the happy path; real work iterates. Findings from `test`/`qa`/`browse` land in `findings.md` and the **iteration engine** `/karvey:karvey-iterate` routes each one:

```
test · qa · browse → findings.md → karvey-iterate
                                      ├─ bug      → BUG-NN incident tracker → impl→test→qa micro-loop
                                      ├─ spec-gap → re-open requirements (ripple only affected phases)
                                      └─ emergent → discovery backlog → future change-id (swept at archive)
```

A change is *done* only when no open `bug`/`spec-gap` remains and every `emergent` idea is captured — so nothing gets dropped and nothing stays "in the air".

## Cross-cutting layer (support skills, invokable any time)

`context` · `iterate` · `investigate` · `second-opinion` · `health` · `browse` · `checkpoint` · `diagram` · `docs` · `guard` · `devex` · `retro` · `scrape` · `benchmark-models` · `import` · `standards`

Optional team layer (opt-in, **not** the default — Karvey is complete with one agent): `team` · `decisions`.

## Skills catalog (32)

Invoked as `/karvey:<skill>`. **1 orchestrator + 13 phase skills + 18 support skills.** Each skill's full contract lives in `plugins/karvey/skills/<skill>/SKILL.md`; the shared rules in `plugins/karvey/skills/karvey/rules/`.

### Orchestrator

| Skill | What it does |
|---|---|
| `karvey` | Entry point. Shows the change's phase and approvals, tells you the next skill, `--autoplan` chains the planning phases. |

### Pipeline phases (0–12)

| # | Skill | Produces | Key rules |
|---|---|---|---|
| 0 | `karvey-grill` | Pre-spec interview + "10-star" reframe → synthesis that seeds the PRD | — |
| 1 | `karvey-init` | `project.json`, `change-id`, `prd.md`, `spec.json`, Epic (ClickUp) or `PLAN.md` | project-config, clickup-protocol, living-specs, enforcement |
| 2 | `karvey-requirements` | EARS `requirements.md` traced to the PRD + `spec-delta.md` | ears-format, living-specs, security-tiers |
| 3 | `karvey-mockup` | Navigable mockup, 3–4 levels + spec↔mockup validation | targets |
| 4 | `karvey-design-graphic` | `design-spec.md` (OKLCH, type, 0-10 scoring) + `design-components.md` | targets |
| 5 | `karvey-architecture` | `architecture.md`: boundaries, security tier, diagrams, cloud; standards conformance gate | security-tiers, engineering-standards |
| 6 | `karvey-infra` | IaC + CI/CD pipelines with infra security review → `infra.md` | project-config, deploy-workflow |
| 7 | `karvey-tasks` | `tasks.md`: 10–30 min AI tasks `E{n}.F{n}.T{n}` with dependencies | clickup-protocol |
| 8 | `karvey-impl` | Code on `feature/{change-id}`, per-task commit + version + CHANGELOG | deploy-workflow, versioning, engineering-standards |
| 9 | `karvey-test` | Unit + E2E in the real runtime → `test_evidence.md`, findings, `BUG-NN` | targets, iteration-loop, incident-tracking |
| 10 | `karvey-qa` | 9-dimension review (security gate, standards conformance…) → `REVISION_PR_*.md` | changelog-policy, versioning, iteration-loop |
| 11 | `karvey-deploy` | feature → dev → PR master, PR gates verified, human OK, canary, **branch hygiene** | deploy-workflow, versioning, changelog-policy |
| 12 | `karvey-archive` | Spec-deltas merged into living specs, Epic closed, backlog + branch sweep | living-specs, backlog, phase-close |

### Support skills (any time, do not advance the phase)

| Skill | Role |
|---|---|
| `karvey-context` | Read-only dashboard: config, changes, deploy queue, backlog, live branches |
| `karvey-iterate` | Iteration engine: routes findings → `bug` / `spec-gap` / `emergent` |
| `karvey-investigate` | Root-cause debugging — Iron Law: no fix without investigation; dates the symptom, asks what changed |
| `karvey-second-opinion` | Adversarial cross-model review (Review / Challenge / Consult) |
| `karvey-health` | 0-10 code-quality score with trend + method readiness (skills installed, pinned inputs) |
| `karvey-browse` | Eyes on the real runtime: browser, simulator, terminal |
| `karvey-checkpoint` | Save / restore work state **and the agent handoff** (+ `state.json`) |
| `karvey-diagram` | Text → mermaid + excalidraw + SVG/PNG |
| `karvey-docs` | Diataxis docs, stale-doc refresh, PDF export |
| `karvey-guard` | Opt-in enforcement hooks, edit-lock, `--verify` checklist |
| `karvey-devex` | Developer-experience / onboarding review |
| `karvey-retro` | Cycle retrospective |
| `karvey-scrape` | Web extraction codified as a reusable skill |
| `karvey-benchmark-models` | Compare models: latency, tokens, cost, quality |
| `karvey-import` | Convert Kiro / gstack specs into `docs/spec/` |
| `karvey-standards` | Uplift the team's golden paths from the real system into its standards repo |
| `karvey-team` | **Optional** team layer: roles, census, relay, cost |
| `karvey-decisions` | Decision log (`D-NN` / `C-NN`) + `cross` before declaring a block |

## Team settings — asked on first use

A Claude Code plugin cannot run anything at install time, so Karvey asks the team's settings **the first time it is used** in a project (`/karvey:karvey-init`, Step 3.2) and stores them in `docs/spec/project.json`. Change them any time with `/karvey:karvey-init --settings`. Until they are set, the session hook prints a one-line reminder (only inside a Karvey project).

| Setting | Options | Rule |
|---|---|---|
| **Notifications** (QA / deploy / incidents) | Google Chat · Slack · Microsoft Teams · e-mail · webhook · none | `rules/notifications.md` |
| **Task management** | ClickUp · Jira · Linear · Azure Boards · GitHub Projects · spreadsheet (Excel/Sheets/CSV) · Markdown (`PLAN.md`) · other | `rules/management-adapters.md` |
| **Status flow** | the team's real statuses mapped to 5 logical states: `todo` · `in_progress` · `review` · `done` · `blocked` | `rules/management-adapters.md` |

Skills never assume a tool or a status name: they speak in logical states and the adapter resolves them. A project created before 3.10 with only `"management": "clickup"` keeps working — the statuses are read from the list and the mapping is confirmed once.

## Method explainer (`docs/karvey.html`)

A self-contained page (no external requests), **in English by default with a switch to Español, Português, Deutsch and 中文** (`?lang=es|pt|de|zh`, remembered per browser), that complements this README: what the method is, the meaning of the name (*Karvey* = **Afán**, from the Ona language of the Selknam people of Patagonia), and a map of the whole plugin — orchestrator, phases, support skills, rules, hooks, artifacts and team settings. Open it locally in any browser.

## Hooks — what runs on install and what is opt-in

- **Active on install (plugin hooks, `plugins/karvey/hooks/`):** a `SessionStart` hook (`karvey-session-context.sh`, on startup / resume / compact / clear) that reinjects the agent handoff and contrasts it against the live repos (`matches` / `DRIFT`), and reminds you to set the team settings when a Karvey project lacks them. It is **inert** (no output, exit 0) outside Karvey projects. The statusline script (context, account limits **with the next reset time and time left**, hours, cost, rotation warning) ships alongside but a plugin cannot declare it — install it by hand (see `plugins/karvey/hooks/README.md`).
- **Opt-in per project (`plugins/karvey/skills/karvey/hooks/`):** `git-flow-guard.sh` and `plan-gate.sh`, installed and removed by `/karvey:karvey-guard` according to `project.json:enforcement`. Not active by default.

## Features

- **PRD as the base** + traceable EARS requirements.
- **Navigable mockup** (with shotgun variant mode) and **design** with 0-10 scoring per platform (WCAG/HIG/Material).
- **Architecture** with diagrams, edge cases, trust boundaries and a **Cloud Infrastructure** section.
- **IaC + CI/CD pipelines** (Terraform/Bicep/Pulumi · GitHub Actions/Azure Pipelines) with security review.
- **9-dimension QA** with a **blocking security gate** (OWASP + STRIDE), a **standards-conformance** dimension (golden path + approved deviations) and cross-model second opinion.
- **Iteration loop** that routes findings back to their edge (`bug` / `spec-gap` / `emergent`) so the method guides you through iteration, not just the happy path.
- **Incident tracker** (`BUG-NN` with state history) per repo + a global index — complementary to ClickUp.
- **Discovery backlog** (Markdown + ClickUp) so emergent ideas become future change-ids, swept at archive.
- **Mandatory phase-close** ritual: every phase/task updates management (ClickUp comment + status + cascade) so nothing goes stale.
- **Ordered deployment** `feature → dev → PR master`, pipeline-triggered, verifying the **PR gates** (CI + branch policies) before the prod OK, with **canary** post-deploy and **branch hygiene** (absorbed branches deleted, unreleased ones reported — nothing left in branches).
- **Semver versioning + CHANGELOG** per component/repo, with human + AI-model traceability; every deploy bumps the version, and a front shows the **dev version in DEV** (`x.y.z-dev.N+sha`) and the **release version in PROD**, read from the version file and checked by the canary.
- **Multi-agent & multi-repo work**: parent/child changes across repos, `D-NN` decisions and pinned inputs (`repo path @commit`) from design/copy/legal agents, approvals that record who and where, `[human]` tasks with verification and rollback, `ops` and `hotfix` change types, light CI for docs-only PRs.
- **Optional team layer** (`rules/team.md`): roles, a **rotation handoff captured by commands** (not composed from memory), census, decision log with a cross-check that stops you re-asking what was already decided, and **cost measurement**. Opt-in, and the rule opens by telling you when *not* to use it: the measured run behind it cost ≈US$1,000 over 3 days with 6 agents and ended back on a single agent.
- **Verification rules before reporting "done"** (`rules/verification.md`): the failure modes that make a green report false — a citation is not the thing cited, exit 0 is not success, a green test over uncalled code, a filename that does not identify a version.
- **Optional hook-based enforcement** (git-flow + plan-gate) — opt-in per project.

## Install (as a Claude Code plugin)

```
/plugin marketplace add MauricioQuezadaHaintech/karvey
/plugin install karvey@karvey-methods
```

## Update to the latest version

```
claude plugin marketplace update karvey-methods
claude plugin update karvey@karvey-methods
```

Then **restart the session** for the new version to load. Verify with `claude plugin list`
(or `/plugin` inside Claude Code, which does the same from a menu).

Then invoke the namespaced skills, for example:

```
/karvey:grill            # start pre-spec
/karvey:karvey <id>      # see status and next step
```

The skills' bodies are in English (what Claude reads), but **artifacts are generated in the project's language** (`spec.json` `language` field) and Claude replies in your language. Triggers are bilingual (English + Spanish).

## Knowledge graph (`graphify-out/`)

The repo ships a [graphify](https://github.com/safishamsi/graphify) knowledge graph of the method itself (`project.json:knowledge_sync = "graphify"`): skills, shared rules, releases and the concepts that connect them.

- `graphify-out/GRAPH_REPORT.md` — communities, god nodes, surprising connections, suggested questions.
- `graphify-out/graph.html` — interactive graph, opens in any browser. `graphify-out/graph.json` — raw graph.
- All paths inside are **relative to the repo root**. After changing skills or rules, refresh it incrementally with `graphify . --update` from the repo root and commit the result.

## License and trademark

Code under the **Apache License 2.0** (see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE)). You may use, modify and adapt `karvey-*` with attribution.

The **"Karvey"** name and the `karvey-*` convention are trademarks of **HainTech** — see [`TRADEMARK.md`](TRADEMARK.md). Adaptations must keep attribution to Mauricio Quezada Ibáñez / HainTech and must not imply official endorsement without permission.
