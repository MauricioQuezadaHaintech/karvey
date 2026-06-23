# Engineering Standards — the golden paths ("how we build here")

> The problem this solves: Karvey has **living specs** (`specs/{capability}/spec.md` — *what* the system does)
> and `project.json` (config), but no canonical place for the **engineering conventions** of each layer —
> *how* a table/SP is created, *how* a backend service is structured, *which* frontend pattern is current.
> Without it, `architecture` and `impl` lean on tribal knowledge + the agent's taste, and work drifts out
> of the house style. This rule adds a **third source of truth**: the engineering standards, and a **conformance
> gate** so the pipeline stays inside the margin — and, when something must go outside it, **asks in design mode
> instead of deciding alone**.

Standards are the **golden paths** (the canonical, approved way to build in each layer/target). They are
distinct from living specs: a spec says *"the system sends a claim notification"*; a standard says
*"every DB write goes through a stored procedure in the `sip` schema; direct SQL from the backend is forbidden"*.

## Location

```
docs/spec/
├── standards/
│   ├── _index.md          ← which standard applies to which target/repo + maturity
│   ├── db.md              ← schemas, naming, "all writes via SP", canonical SP example, forbidden
│   ├── backend.md         ← service/function structure, layering, event-driven pattern (the chosen one)
│   ├── frontend.md        ← component/store/API patterns + migration state (current vs target)
│   └── {layer-or-target}.md
```

`docs/spec/standards/` lives in the **`spec_repo`** (same as the rest of `docs/spec/`). Standards are
**cumulative and versioned with the repo** — they evolve, they are not rewritten per change.

## Standard file structure (fixed — meant to be consumed as constraints, not prose)

Each `standards/{layer}.md` MUST follow this shape so the agent can apply it mechanically:

```markdown
# Standard: {layer} — {stack}

**Status:** active | migrating | deprecated
**Applies to targets:** {web | api | ...}   **Repos:** {repo(s)}
**Source of truth:** {canonical file path(s) in the codebase this is distilled from}

## Golden path
{The canonical pattern, with a REAL, copyable example from the codebase (file:line).}

## MUST (hard rules)
- {non-negotiable 1 — e.g. "every DB write goes through an SP in schema `sip`"}
- {non-negotiable 2}

## MUST NOT (anti-patterns)
- {forbidden 1 — e.g. "no dynamic/inline SQL from the backend"}
- {forbidden 2}

## Gray zones (REQUIRE a human decision → design mode)
- {decision that is NOT pre-resolved by this standard — e.g. "introducing a new schema",
  "a new event topic", "deviating from the v3 frontend pattern"}

## Migration (only if Status = migrating)
- **current:** {pattern v_n} — `deprecated`, only for touching existing code
- **target:** {pattern v_n+1} — MANDATORY for all new work
- **rule:** new work uses target; touching `current` code is a deviation (ask)
```

> The `migrating` status is exactly the frontend v2→v3 case: mark `target: v3` and `current: v2 (deprecated)`.
> New screens → v3. Touching a v2 screen → a deviation request (see below). This makes the migration a
> property of the method, not something someone has to remember.

## The conformance gate (where it plugs into the pipeline)

Two phases load the relevant standards as a **mandatory input** and validate against them. The relevant
standards are those of the change's `layers`/`targets` (from `spec.json`/`project.json`), resolved via
`standards/_index.md`.

### In `karvey-architecture` (PHASE 5)
After drafting the design and before writing `architecture.md`, classify it against the loaded standards:

| Outcome | Action |
|---------|--------|
| ✅ **Conforms** to the golden path | Proceed. Cite the standard it follows in "Architectural decisions". |
| ⚠️ **Gray zone / must go outside the standard** | Do **NOT** decide alone. Emit a **Deviation Request** and ask the user **in design mode** (see below). Only a user-approved deviation is recorded and allowed. |
| ❌ **Violates a MUST / MUST NOT** without justification | Block. Rework the design to conform, or escalate it explicitly as a deviation. |

### In `karvey-impl` (PHASE 8)
Same contract at code level. Before writing code that would step outside the standard
(e.g. using a `deprecated` pattern, a new schema, an unapproved library), **raise the deviation first** —
not after the code is written. Code that conforms cites the standard; code that deviates needs an
approved entry in `deviations.md`.

## Deviation Request — the "design mode" escalation

A deviation is any departure from a standard's golden path, or any decision a standard explicitly lists
as a gray zone. The agent **never resolves it silently**. It presents:

```
⚠️ DEVIATION REQUEST — {layer} standard
- What the standard says: {the MUST / golden path / gray zone}
- What this change needs instead: {the proposed departure}
- Why: {driver — constraint, perf, missing capability, legacy code}
- Options:
   A) {recommended option} — {trade-off}   ← recommended, with reason
   B) {alternative} — {trade-off}
- Blast radius: {what else this affects}
```

Then it uses `AskUserQuestion` (architecture) / stops and asks (impl) and waits for the user's decision.
On approval, append it to the change's deviation log:

```
docs/spec/changes/{change-id}/deviations.md
```

```markdown
## DEV-01 — {title}
- **Standard:** {layer} · **Rule departed from:** {MUST / golden path / gray zone}
- **Decision:** {chosen option} · **Approved by:** {human} / {AI model} · **Date:** {YYYY-MM-DD}
- **Rationale:** {why} · **Scope:** {where it applies, this change only or wider}
```

## Feedback loop — deviations improve the standard

A deviation is a signal, not just an exception. At `karvey-archive` (or when a deviation **repeats** across
changes), review `deviations.md`:
- If the deviation should become the new norm → **update the standard** (the golden path was wrong/outdated).
- If it was a one-off → leave it logged as a justified exception.

This mirrors the iteration loop (`iteration-loop.md`): a `spec-gap` re-opens requirements; a recurring
deviation re-opens the **standard**. Standards are living, like specs.

## Bootstrapping standards (how to populate them without inventing)

Standards are **distilled from what already exists**, never idealized from scratch:
- Read each repo's `CLAUDE.md` / `CONTRIBUTING.md` / `README.md` and steering docs (`tech.md`, `product.md`).
- Read **canonical real code** (a well-made SP, a reference service, a reference component) and cite it as
  `Source of truth`.
- Fold in tribal rules that currently live only in chat/memory.
- Anything genuinely undefined becomes a `> TODO` placeholder + a gray zone (so it surfaces as a design-mode
  question the first time it is hit, instead of being guessed).

`karvey-init` offers to bootstrap `standards/` for the declared `targets`; they can also be authored manually.
If `standards/` is absent, `architecture`/`impl` still run but **must announce** that no standard was found for
the layer and treat every non-trivial pattern choice as a gray zone (ask), rather than silently picking one.

## Optional enforcement

`karvey-guard` can install a `standards-guard` hook that warns/blocks when `impl` touches a pattern marked
`MUST NOT` (or a `deprecated` pattern under `migrating`) without a matching approved entry in
`deviations.md` for the current change. Opt-in, like the other enforcement hooks (`enforcement.md`).
A skill never forces this on its own — only the hook blocks.

## project.json reference

The applicable standards are declared at project level so phases know what to load:

```json
"standards": {
  "dir": "docs/spec/standards",
  "by_layer": { "db": "db.md", "backend": "backend.md", "frontend": "frontend.md" }
}
```

See `project-config.md`. If `standards` is absent, phases fall back to `docs/spec/standards/_index.md`,
and if that is missing too, to the "no standard found → ask" behavior above.

## Who writes / who reads

- **Writes / updates:** `karvey-init` (bootstrap), maintainers (manually), `karvey-archive` (folds recurring
  deviations back into the standard).
- **Reads (as a hard constraint):** `karvey-architecture`, `karvey-impl`, and `karvey-qa` (the Consistency
  dimension checks conformance + that every deviation has an approved entry).

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0.*
