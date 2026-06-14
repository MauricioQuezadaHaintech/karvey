---
name: karvey-import
description: Convert existing specs from Kiro (cc-sdd) or gstack into the Karvey method's `docs/spec/` structure. Maps requirements/design/tasks into Karvey's prd.md, requirements.md, architecture.md, tasks.md + spec.json/project.json. Cross-cutting support skill — does NOT advance any change's phase. Triggers include "karvey import", "import kiro", "kiro to karvey", "migrate kiro", "migrar kiro", "convertir kiro", "import gstack", "gstack to karvey", "migrate gstack", "convertir gstack", "convert specs", "importar specs".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: --from <kiro|gstack> [path] [--change-id <id>]
---

# Karvey Import — convert Kiro / gstack specs into Karvey

## Purpose

Bring pre-existing specifications from **Kiro** (cc-sdd) or **gstack** into the Karvey `docs/spec/` structure, so they can continue through the Karvey pipeline. This is a **cross-cutting support skill** (cross-cutting layer): it does **NOT** advance `spec.json:phase` of any change — it materializes the imported documents and leaves the change at the phase its content supports.

It is **idempotent and non-destructive**: it never deletes the source (`.kiro/`, gstack docs); it only creates/updates files under `docs/spec/`. Generated artifacts follow the project's language (per `spec.json` `language`).

## Mode selection

- `--from kiro` → import from a Kiro `.kiro/` directory.
- `--from gstack` → import from gstack artifacts (design docs, specs, plans).
- If `--from` is omitted, detect: if a `.kiro/` directory exists → kiro; otherwise ask the user which source to use.

---

## Step 1 — Ensure project config

Read `docs/spec/project.json` (see `karvey/rules/project-config.md`). If it does not exist, create it (or run `/karvey-init`'s project-config step): ask/infer `git_platform`, `cloud`, `iac_tool`, `knowledge_sync`, `targets`, `repos` (min 1), `spec_repo`, `branch_flow`. For Kiro, pre-fill `targets`/stack from `.kiro/steering/tech.md` if present.

---

## Step 2A — Import from Kiro (`--from kiro`)

Kiro layout (source):
```
.kiro/
├── steering/{product.md, tech.md, structure.md, ...}   ← project-level context
└── specs/{feature-name}/
    ├── spec.json            ← kiro metadata + approvals
    ├── requirements.md      ← EARS requirements
    ├── design.md            ← technical design
    └── tasks.md             ← implementation tasks
```

For **each** `.kiro/specs/{feature-name}/`:

1. **change-id**: use `{feature-name}` (or `--change-id`). Make it URL-safe; prefix with `add|fix|update` if it improves clarity. Avoid collisions in `docs/spec/changes/`.
2. **Create** `docs/spec/changes/{change-id}/`.
3. **Map files** into Karvey:

   | Kiro source | → Karvey target | Notes |
   |-------------|-----------------|-------|
   | `requirements.md` (EARS) | `requirements.md` | Compatible. Add a `Traces to PRD:` line per requirement (point to the PRD section once the PRD exists). |
   | `design.md` | `architecture.md` | Map onto Karvey's architecture template. Sections Karvey requires but Kiro lacks (**Cloud Infrastructure**, edge cases, trust boundaries, test-coverage plan, diagrams) are added as `> TODO (karvey-architecture): ...` placeholders, NOT invented. |
   | `tasks.md` | `tasks.md` | Keep tasks; re-label to `E{n}.F{n}.T{n} [layer]` if feasible, otherwise keep and note. |
   | `steering/product.md` | feeds `prd.md` | Problem, goals, users. |
   | `steering/tech.md` | feeds `project.json` (stack/targets) + architecture context | |

4. **Generate `prd.md`** (Kiro has no formal PRD): synthesize from `steering/product.md` + the intent of `requirements.md` into Karvey's PRD structure (executive summary, problem & context, goals & success metrics, user stories, scope/out-of-scope, stakeholders, constraints, acceptance criteria). Mark inferred parts as `> inferred from Kiro — review`.
5. **Generate `spec.json`**: `change_id`, `capability` (infer or ask), `goal` (from product/requirements; ask if unclear), `language`, `management`, `security_tier` (ask; default per project), `phase` and `approvals` set to the **furthest phase the imported content supports** (e.g. if requirements+design+tasks exist → `phase: "tasks"`, with `requirements/architecture/tasks` marked generated; approvals left `approved:false` so the user re-validates each gate). Map Kiro `approvals` where present.
6. **spec-delta.md / living specs**: create a `spec-delta.md` stub for `karvey-archive` to merge later.
7. Report per feature: what mapped cleanly vs. what needs review (the TODO placeholders).

---

## Step 2B — Import from gstack (`--from gstack`)

gstack does **not** persist a fixed on-disk spec layout, so this mode is **heuristic and confirmation-driven**.

1. **Discover** candidate artifacts (ask the user to confirm/point if ambiguous):
   - Design docs / "10-star" or office-hours outputs, CEO/eng review plans.
   - `/spec` outputs (executable specs, backlog-ready).
   - Plan files (e.g. `PLAN.md`, `docs/plan*`, `*.spec.md`, design notes).
2. **Map** onto Karvey:

   | gstack artifact | → Karvey target |
   |-----------------|-----------------|
   | office-hours / CEO review / 10-star doc | `prd.md` (vision + problem + goals) |
   | `/spec` executable spec | `requirements.md` (convert to EARS; mark non-EARS items) |
   | eng-review plan / architecture notes | `architecture.md` (+ TODO placeholders for missing Karvey sections) |
   | task/backlog list | `tasks.md` |
   | design-system notes | `design-spec.md` |
3. **Generate `prd.md`**, `spec.json` and (if missing) `project.json` as in the Kiro flow. Set `phase`/`approvals` to the furthest phase the mapped content supports; leave approvals `approved:false` for re-validation.
4. Because mapping is heuristic, **always present the proposed file map to the user for confirmation before writing**.

---

## Step 3 — Knowledge sync

After writing, run the sync step per `karvey/rules/knowledge-sync.md` (Obsidian if available; otherwise `/graphify docs/spec/ --update`).

## Step 4 — Output

Report, per imported change:
```
✅ Imported {change-id} from {kiro|gstack}
   Created: prd.md, requirements.md, architecture.md, tasks.md, spec.json
   Resume phase: {phase}  (all gates require re-approval)
   ⚠️ Needs review: {list of TODO placeholders / non-EARS items}

Next step: /karvey {change-id}   → see status and continue the pipeline
```

## Safety

- **Never delete or modify the source** (`.kiro/`, gstack docs) — read-only on the origin.
- **Do not invent** content Karvey requires but the source lacks — use clearly marked `> TODO` placeholders so the user fills them via the proper phase.
- All gates are imported as **not approved**, so the user re-validates requirements/architecture/etc. through Karvey.
- Generated artifacts follow the project's language (`spec.json` `language`), never forced to English.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
