# Discovery Backlog — nothing stays "in the air"

> Emergent ideas and out-of-scope discoveries (mid-cycle or post-archive) must land **somewhere
> concrete** and become future `change-id`s. This rule defines a **dual** backlog: a Markdown source
> of truth **mirrored** into the team's tracker (`management-adapters.md` → `mirror_backlog`) when one is configured.

## Storage — both (mirror)

- **Always:** `docs/spec/backlog.md` in the `spec_repo` — the source of truth, versioned with the specs.
- **If the team uses a tracker** (`karvey-config.py resolve management` reports `external: true`): each item is **also** created in the tracker's backlog (`mirror_backlog`, find-or-create by its `BL-NN` key; see `management-adapters.md`) in the resolved `location`. The Markdown item records the tracker id; the two are reconciled at the phase-close ritual.

If the resolved `location` is empty, ask the user for it once and store it on a docs branch; never pick one.

## What lands here

Findings classified as **`emergent`** (see `iteration-loop.md`): valid new scope/ideas that are NOT this change's job. Also: opportunities surfaced by `karvey-retro`, tech debt noted during impl/qa, and any "we should also…" that would otherwise be lost.

A `spec-gap` does **not** go to the backlog — it re-opens `requirements` for the current change. Only genuinely out-of-scope work goes to the backlog.

## backlog.md format

```markdown
# Discovery Backlog — {project}

| ID | Date | Origin | Type | Priority | Title | Status | Tracker | Promoted to change-id |
|----|------|--------|------|----------|-------|--------|---------|-----------------------|
| BL-12 | 2026-06-17 | add-claim-filter / F-03 | feature | med | PDF export of the report | open | task xyz | — |
| BL-13 | 2026-06-17 | retro add-claim-filter | tech-debt | low | extract claims helper | open | — | — |

## BL-12 — PDF export of the report
- **Origin:** change add-claim-filter, finding F-03 (browse, emergent)
- **Why:** users asked to share the report outside the app
- **Rough scope:** new endpoint + front button; needs a PDF lib decision
- **Status:** open
```

`status`: `open` → `promoted` (a `change-id` was created from it) → `discarded` (with a reason).

## Promotion to a change-id

The backlog is swept at two moments:

1. **`karvey-archive` (cycle close):** after merging spec-deltas, review `open` backlog items whose origin was this change and offer to promote the relevant ones into new `change-id`s via `/karvey-grill` or `/karvey-init` (carrying the backlog context as seed for the PRD). This is the step that guarantees post-cycle discoveries don't evaporate.
2. **`karvey-context` / orchestrator (any time):** the dashboard surfaces the count of `open` backlog items so they stay visible and get scheduled, not forgotten.

When an item is promoted, set its `status: promoted` and fill `Promoted to change-id`. When the new change is created, its `spec.json` records `seed_backlog_id` for traceability.

## Sweep is not silent

When a sweep drops or defers items, **say so** to the user (count of open/deferred). Silent truncation reads as "everything is captured" when it isn't.
