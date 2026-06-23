# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/) + human/AI traceability (Karvey policy).

## [3.4.0] - 2026-06-23

### Added
- **AI-time estimation in `clickup-protocol.md`**: estimates are expressed in **minutes** (AI execution + human review), not human coding hours. Typical task 10–30 min, **cap ~60 min → split if it exceeds**. Added a per-work-type reference table (SP/endpoint/service/UI/parser/test) and Feature/Epic aggregation. The legacy "6-hour rule" is reframed: it assumed human time; under AI-driven dev the effective cap is ~60 min.

### Why
Reconciliation of the team's `GESTION_PROYECTOS_IA` governance doc into Karvey: that doc was the Paáutin-specific, prior form of the same method (its ClickUp folder is literally "Dev Sprints Metodo Karvey"). The clickup-protocol already covered WBS/naming/dependencies/status; the missing piece was the AI-time estimation model. Project-specific bits (2026 sprint calendar, workspace IDs, client tags) go to the team's `paautin-standards`, not here.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: rule refinement (clickup-protocol estimation) · Apache 2.0

## [3.3.0] - 2026-06-23

### Added
- **Engineering Standards layer** (`rules/engineering-standards.md`): a third source of truth beside living specs and `project.json` — the **golden paths** ("how we build here") per layer/target, living in `docs/spec/standards/` (`db.md`, `backend.md`, `frontend.md`, `_index.md`). Fixed file structure (Golden path · MUST · MUST NOT · Gray zones · Migration `current`/`target`) so they are consumed as hard constraints, not prose.
- **Conformance gate (design mode)** in `karvey-architecture` (new Step 4B) and `karvey-impl` (Step 4 execution rules): both load the relevant standards as a **hard input** and validate against them. Conforms → proceed citing the standard; gray zone / outside the standard → **Deviation Request** asked to the user in design mode (never resolved silently); MUST/MUST NOT violation without justification → blocked.
- **`deviations.md`** per change: approved departures from a standard, with rationale + human/AI traceability. Recurring deviations feed back into the standard at `karvey-archive` (mirrors the spec-gap → requirements loop).
- **`karvey-standards`** support skill: lifts the team's engineering golden paths (db/backend/frontend…) from the **real system** into the team's standards repo, in the standard template format. Discovery subagents per layer, picks a golden path where repos diverge, marks undefined things as gray zones, human-approved, re-runnable (`--refresh` promotes recurring deviations into the standard). Registered in the orchestrator + support-skills rule.
- **Method/standards separation (two planes):** the public plugin stays generic and **never** holds a team's concrete standards; those live in the team's own repo. `project.json:standards` gains `source: "local" | "git"` (+ `repo`/`ref`/`path`) so standards can live in a **separate private repo** (e.g. Azure DevOps) that the team installs, read via a cached checkout (`.karvey/standards/`).
- **`project.json:standards`** field (`source`/`dir`/`repo`/`ref`/`path`/`by_layer`) so phases know which standard to load; fallback chain to `_index.md` and, failing that, to "no standard found → ask".
- Migration support as a first-class concept (`Status: migrating`, `current` vs `target`) — covers the frontend v2→v3 case: new work MUST use `target`, touching `current` is a deviation.
- Optional `standards-guard` enforcement hook (opt-in) and registration of the rule in the orchestrator (rules table + `docs/spec/` structure).

### Why
Closed a real blind spot: the method specified *what* to build (living specs) but had no canonical place for *how* to build it per layer, so `architecture`/`impl` drifted on tribal knowledge. Now the pipeline stays inside the house style and, when something must go outside it, it asks in design mode instead of deciding alone — while keeping the generic method and each team's private standards cleanly decoupled.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: method extension (rules + architecture/impl gate) · Apache 2.0

## [3.2.0] - 2026-06-17

### Added — Iteration loop (Karvey becomes a spiral, not a line)
- **`karvey-iterate`** support skill: the iteration engine. Reads the change's `findings.md` inbox and routes each finding to its feedback edge — `bug` → incident tracker + QA micro-loop · `spec-gap` → re-open `requirements` (rippling only the affected phases) · `emergent` → discovery backlog. The single place loop logic lives; phase skills only observe/classify.
- **`rules/iteration-loop.md`**: the three feedback edges, the `findings.md` triage artifact, the spec-revision sub-cycle, and the convergence gate (a change is done only when no open `bug`/`spec-gap` remains and all `emergent` are captured).
- **`rules/incident-tracking.md`**: a dedicated `BUG-NN` incident tracker (`docs/bugs_dev_testing.md` per repo + global `incidents-index.md`) with a **state-history** machine (DETECTADO → DIAGNOSTICADO → EN FIX → RESUELTO → REABIERTO). Complementary to ClickUp; integrates with `karvey-investigate` and regression tests.
- **`rules/backlog.md`**: a **dual** discovery backlog — `docs/spec/backlog.md` (source of truth) mirrored into the ClickUp `backlog_list_id`. Swept at archive to promote emergent items into new change-ids (`seed_backlog_id`).
- **`rules/phase-close.md`**: a **mandatory** phase-close ritual (comment + status + cascade on ClickUp/PLAN.md, findings/backlog sweep, spec.json + knowledge update) at the end of every phase and every task — fixes stale ClickUp tasks by making the update a numbered step, not a "should".

### Changed
- **`karvey-mockup`**: navigable depth 3 → **3–4 levels** (sub-flows/states where spec-gaps hide) + a **spec↔mockup validation** pass (Step 4C) to catch spec defects before design/architecture/impl.
- **`karvey-test`**: writes classified findings to `findings.md`, logs bugs to the `BUG-NN` tracker, and routes via `karvey-iterate` (Step 5B/5C/5D).
- **`karvey-qa`**: classifies findings (bug/spec-gap/emergent), routes via `karvey-iterate`, convergence gate before deploy (Step 3E/3F).
- **`karvey-impl`**: per-task completion is now the explicit per-task phase-close ritual.
- **`karvey-archive`**: discovery-backlog sweep (Step 7E) that promotes emergent work into future change-ids.
- **`karvey-browse`**: surfaced defects/gaps are recorded as classified findings.
- **Orchestrator + `living-specs.md`**: state machine gains the feedback edges and convergence gate; `spec.json` gains `iteration_count`, `revision_history`, `seed_backlog_id` and explicit `infra`/`qa`/`deploy` approvals; directory structure adds `findings.md`, `backlog.md`, `incidents-index.md`.
- **`clickup-protocol.md`**: ClickUp updates declared mandatory (phase-close), phase-level status mapping, incident/backlog mirroring.
- Support layer now **14** skills (adds `karvey-iterate`).

### Why
Karvey was a waterfall with a single QA micro-loop: findings that were really spec defects had no edge back to `requirements`, and post-cycle discoveries stayed "in the air". ClickUp updates were documented as a "should" and got skipped, leaving tasks stale, and bugs had no dedicated incremental tracker with history. This release makes the method guide **iteration** itself — close the feedback loops, track incidents with state history, capture emergent work, and enforce the close ritual — so nothing gets dropped.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8 (1M context)
> 🔗 Karvey phase: method evolution (iteration loop + incident tracking + backlog + phase-close) · Apache 2.0

## [3.1.0] - 2026-06-14

### Added
- **`karvey-import`** support skill: converts existing **Kiro** (`.kiro/specs/*` + steering) and **gstack** specs into Karvey's `docs/spec/` structure (prd.md, requirements.md, architecture.md, tasks.md, spec.json/project.json). Non-destructive on the source; missing Karvey-required sections become `> TODO` placeholders; all gates imported as not-approved for re-validation. Registered in the orchestrator, support-skills rule and coverage table.

### Why
Let teams already using Kiro or gstack adopt Karvey without rewriting their existing specs by hand.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: support skill addition · Apache 2.0

## [3.0.0] - 2026-06-14

### Added
- Initial publication of the **Karvey** Method as a Claude Code plugin/marketplace.
- 12-phase pipeline (0–12): grill, init, requirements, mockup, design-graphic, architecture, **infra**, tasks, impl, test, qa, **deploy**, archive.
- Cross-cutting layer of 12 support skills: investigate, second-opinion, health, browse, checkpoint, diagram, docs, guard, devex, retro, scrape, benchmark-models.
- Stack agnosticism (`targets`), PRD base, traceable EARS, blocking security gate (OWASP+STRIDE), ordered deployment with canary, semver versioning, optional hook-based enforcement (git-flow + plan-gate), persistent `goal` field.
- Shared rules: project-config, knowledge-sync, targets, deploy-workflow, changelog-policy, versioning, enforcement, support-skills (+ the previous ones).
- Apache 2.0 license, NOTICE and TRADEMARK.md ("Karvey" trademark = *Afán*, Selknam).
- Skill bodies authored in English with bilingual triggers; generated artifacts follow the project's language.

### Why
Formalize Karvey as HainTech's own stack-agnostic method, absorbing the value of Kiro and gstack, installable/versionable as a plugin (no manual copying of skills).

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: initial publication · Apache 2.0
