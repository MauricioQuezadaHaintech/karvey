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

Last refinement: 2026-06-20

| ID | Date | Origin | Type | Priority | Title | Status | Tracker | Promoted to change-id | Value | Effort | CoD | Needed by | Client | Reviewed | Commit |
|----|------|--------|------|----------|-------|--------|---------|-----------------------|-------|--------|-----|-----------|--------|----------|--------|
| BL-12 | 2026-06-17 | add-claim-filter / F-03 | feature | med | PDF export of the report | open | task xyz | — | 4 | M | 3 | — | sample-client | 2026-06-20 | — |
| BL-13 | 2026-06-17 | retro add-claim-filter | tech-debt | low | extract claims helper | done-direct | — | — | 2 | 45 | — | — | — | 2026-06-20 | abc1234 |

## BL-12 — PDF export of the report
- **Origin:** change add-claim-filter, finding F-03 (browse, emergent)
- **Why:** users asked to share the report outside the app
- **Rough scope:** new endpoint + front button; needs a PDF lib decision
- **Status:** open
```

`status`: `open` → `promoted` (a `change-id` was created from it) · `discarded` (with a reason) · `done-direct` (small
work done without a change — the `Commit` column is required; `validate` refuses the state without it).

## Ranking — WSJF (REQ-W3-049)

```
wsjf = (value + urgency) / effort          two decimals
```

- **Value** 1–5 (what doing it is worth).
- **Urgency** = **CoD** (cost of delay) 1–5; without it, from the days left to **Needed by**: past or ≤ 14 → 5,
  ≤ 30 → 4, ≤ 60 → 3, ≤ 90 → 2, otherwise 1.
- **Effort** S / M / L = 1 / 2 / 3, or minutes: ≤ 60 → 1, ≤ 240 → 2, otherwise 3.
- A missing value, effort or urgency leaves the item **unscored** (listed apart, never 0); a malformed cell is an
  **invalid row** named by its id. **Client** says whom it serves; **Reviewed** is the last date someone looked at
  it — more than 30 days ago is **stale**.

`karvey-context.py --backlog` lists the open items by score, the unscored apart, the stale ones flagged
(read-only; `karvey_lib/backlog.py` computes it).

## Refinement cadence (REQ-W3-052)

Refine the backlog every **14 days** (`project.json:backlog.refine_days`): re-score, mark `Reviewed`, discard what no
longer matters, then update the `Last refinement: YYYY-MM-DD` line at the top of `backlog.md`. The dashboard's
overview shows that date, `overdue` past the cadence, or `never refined`.

## Promotion to a change-id

The backlog is swept at two moments:

1. **`karvey-archive` (cycle close):** after merging spec-deltas, review `open` backlog items whose origin was this change and offer to promote the relevant ones into new `change-id`s via `/karvey-grill` or `/karvey-init` (carrying the backlog context as seed for the PRD). This is the step that guarantees post-cycle discoveries don't evaporate.
2. **`karvey-context` / orchestrator (any time):** the dashboard surfaces the count of `open` backlog items so they stay visible and get scheduled, not forgotten.

When an item is promoted, set its `status: promoted` and fill `Promoted to change-id`. When the new change is created, its `spec.json` records `seed_backlog_id` for traceability.

## Sweep is not silent

When a sweep drops or defers items, **say so** to the user (count of open/deferred). Silent truncation reads as "everything is captured" when it isn't.
