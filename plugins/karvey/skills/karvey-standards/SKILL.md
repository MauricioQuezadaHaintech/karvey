---
name: karvey-standards
description: Uplift engineering standards (golden paths) from the team's ACTUAL system into the standards repo, following the engineering-standards template. Discovers real patterns per layer, drafts db/backend/frontend standards, and is re-runnable to refresh them. Triggers include "karvey standards", "levantamiento de estándares", "engineering standards", "golden path", "extraer estándares", "standards uplift", "definir cómo se hace un SP/servicio/componente", "actualizar estándares".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion
argument-hint: [<layer>] [--bootstrap | --refresh] [--repo <git-url>] [-y]
---

# Karvey Standards (engineering golden-paths uplift)

## Purpose

Populate and maintain the **engineering standards** (`standards/{layer}.md`) by reading the team's
**real codebase**, not by inventing them. This is the skill the public method ships so that each team
that installs Karvey can **lift its own standards** into the structure defined by
`karvey/rules/engineering-standards.md`, and keep them fresh over time.

> **Two planes — read this first.** The Karvey **method** (this plugin) is generic and public; it MUST
> NOT contain any team's concrete standards. The **standards themselves** are the team's data and live in
> the team's **own standards repo** (e.g. a private Azure DevOps repo), resolved via
> `project.json:standards`. This skill **writes to that standards repo, never into the plugin**.

## When to use

- **Bootstrap** (`--bootstrap`): first time — there are no standards yet, distill them from the system.
- **Refresh** (`--refresh`): standards exist but drifted, or recurring `deviations.md` entries should become
  the new norm (see `engineering-standards.md` feedback loop), or a migration advanced (e.g. frontend v2→v3).

## Execution steps

### Step 1 — Resolve the standards target

Read `docs/spec/project.json` → `standards` (`source`, `dir`/`repo`, `path`, `by_layer`) and `repos`, `targets`.
Resolve **where standards live and will be written**:
- `source: "local"` → the folder `standards.dir` inside the `spec_repo`.
- `source: "git"` → the external standards repo (`standards.repo`, `ref`, `path`). Ensure a working copy
  exists (shallow clone/pull into a cache, e.g. `.karvey/standards/`), and work there. This is the private
  org repo (e.g. Azure DevOps).

If `standards` is not configured, ask the user where standards should live (local vs git repo) and write it
back to `project.json` per `rules/project-config.md`. **Never** target the public plugin repo.

### Step 2 — Decide scope (which layers/targets)

From the argument `<layer>` if given, else from `project.json:targets` and the repos' nature, decide which
standards to lift: typically `db`, `backend`, `frontend` (+ `infra`, mobile/CLI per `targets`).

### Step 3 — Discovery per layer (read the real system)

For each layer, dispatch **parallel subagents** (Explore) over the relevant `project.json:repos` to extract,
with concrete `file:line` evidence:
- The **golden path**: the canonical, real pattern (naming, structure, layering) + a copyable reference example.
- **MUST** (hard rules already enforced de facto) and **MUST NOT** (anti-patterns visible in the code).
- **Divergences** between repos (where the same thing is done in several ways → a standard must pick one).
- **Migration state** if applicable (e.g. a `current`/v2 pattern being replaced by a `target`/v3 one).
- **Gaps**: things genuinely undefined.

Also read each repo's `CLAUDE.md` / `CONTRIBUTING.md` / `README.md` / steering docs and fold in tribal rules.

### Step 4 — Draft each `standards/{layer}.md`

Follow the **fixed template** in `karvey/rules/engineering-standards.md` exactly:
`Status` · `Applies to targets`/`Repos` · `Source of truth` · `Golden path` (with real example) · `MUST` ·
`MUST NOT` · `Gray zones` (decisions that must trigger design-mode questions) · `Migration` (if `migrating`).

Rules while drafting:
- Distill from evidence; **cite the `Source of truth`** files. Do not idealize.
- Where a divergence exists, pick the **recommended** golden path and record the others as `MUST NOT` or as a
  gray zone, with a one-line rationale.
- Anything undefined → a `> TODO` placeholder **and** a gray zone (so it surfaces as a design-mode question the
  first time it's hit, instead of being silently guessed).
- Migrations → `Status: migrating`, with `current` (deprecated) and `target` (mandatory for new work).

### Step 5 — Human review gate (standards are policy)

Present each drafted standard's summary (golden path + MUST/MUST NOT + gray zones + open TODOs) and get
approval. Standards govern every future change, so they are not auto-adopted.
- With `-y`: auto-approve (use only when re-running a previously approved draft).
- Otherwise: use `AskUserQuestion` per layer (adopt as-is / adjust / skip).

### Step 6 — Write to the standards repo + index

In the resolved standards working copy (Step 1):
- Write/update each `standards/{layer}.md`.
- Update `standards/_index.md`: layer → file, maturity (`draft`/`active`), `applies-to` targets/repos, last-uplift date.
- Update `project.json:standards.by_layer` if files were added.
- **Git**: if the standards repo is versioned, work on a feature branch (respect `rules/deploy-workflow.md`),
  commit with human + AI traceability (`rules/changelog-policy.md`). **Do not push without the user's OK.**
- **Never** write any of this into the public plugin repo.

### Step 7 — Output

```
✅ Standards uplift complete ({bootstrap|refresh})

Standards repo: {local dir | git repo}
Layers: {db, backend, frontend, ...}
  db.md       — active   (source: {ref})
  backend.md  — draft    ({N} divergences flagged as gray zones)
  frontend.md — migrating (current: v2 / target: v3)
Open TODOs / gray zones: {N}  → will surface as design-mode questions in architecture/impl

Next: architecture and impl will load these as a hard constraint (conformance gate).
Refresh anytime with: /karvey-standards --refresh
```

## Relationship with the rest of the method

- **Feeds** `karvey-architecture` (Step 4B gate) and `karvey-impl` (Step 4) — they read what this skill writes.
- **Closes the loop** with `deviations.md`: at `--refresh`, review recurring deviations and promote the ones
  that should become the new norm into the standard (see `engineering-standards.md`).
- **Not a pipeline phase**: it does not advance `spec.json:phase` (see `rules/support-skills.md`).
- `karvey-init` may invoke this on first project setup to bootstrap standards for the declared `targets`.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
