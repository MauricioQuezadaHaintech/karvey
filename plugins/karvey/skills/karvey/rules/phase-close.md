# Phase-Close Ritual — every phase and every task closes the same way

> The problem: Karvey **documented** tracker updates (ClickUp at the time) as a "should", so in practice they got skipped
> and tasks were left stale. This rule makes the close a **mandatory, numbered step** at the end of
> every phase skill and every impl task. No phase advances silently.

## When it runs

- At the **end of every pipeline phase** (`requirements`, `mockup`, `design-graphic`, `architecture`, `infra`, `tasks`, `impl`, `test`, `qa`, `deploy`, `archive`), before asking the user to advance.
- At the **end of every impl task** (`karvey-impl` already does this per task — see its Step 6; this rule is the shared contract).

## The ritual (4 actions, in order)

### 1. Comment what happened
Leave a short, factual close comment on the unit of work.

- **Team's tracker** (`project.json:management.tool`, see `management-adapters.md`): `comment(<item>, "<summary>")` where `<item>` is the task (impl), or the Feature/Epic that represents the phase. Summary = what was done · artifacts produced · result. ClickUp adapter example: `clickup_create_task_comment(<id>, "<summary>")`.
- **Markdown** (`PLAN.md`): append a history row in `PLAN.md` for the phase/task.

### 2. Change state (+ cascade)
- **Team's tracker:** `set_status(<item>, <logical state>)` following the logical flow `todo → in_progress → review → done` (`blocked` when it cannot advance), resolved to the tool's names via `project.json:management.statuses` (`management-adapters.md`; missing map → read the tool's statuses, confirm once, persist).
  - **Cascade:** when ALL tasks of a Feature are `review` → move the Feature; when ALL Features of an Epic are done → move the Epic. A Feature only advances when ALL its layers (BD+Backend+Frontend+Infra) are done. (See `management-adapters.md` → `cascade`; ClickUp detail in `clickup-protocol.md`.)
  - **Phase-level state:** each pipeline phase maps to a Feature/checklist item in the Epic; closing the phase advances that item, so the board reflects pipeline progress, not just leaf tasks.
- **Markdown:** flip the phase/task marker in `PLAN.md` (`🔄 → 👀` for review, `→ ✅` when done), update actual time and date.

### 3. Sweep findings & backlog
- If this phase produced findings (`test`/`qa`/`browse`), make sure they are appended to `findings.md` (see `iteration-loop.md`) and, if any are still `open`, **point the user to `/karvey-iterate`** before advancing.
- If any `emergent` items were noted, ensure they reached the backlog (`backlog.md`) — mirrored to the team's tracker if applicable (`mirror_backlog`).

### 4. Update spec.json + knowledge
- Update `docs/spec/changes/{change-id}/spec.json` (`phase`, the relevant `approvals.*`, `updated_at`).
- When the phase's gate was **approved**, record who and where on that approval: `approvals.<phase>.by`, `role` (`human` | `ceo-delegate`), `date`, `ref` (the `D-NN` of the decision log where the approval is written). An approval without `ref` in a multi-agent project is incomplete (see `multi-agent.md` §4).
- Sync knowledge per `knowledge-sync.md`.

## Gate before advancing

Do not run the "Shall we advance to the next phase?" prompt until actions 1–4 are done. If a tracker is configured and the comment/status update failed (API error, missing `backlog_list_id` / location, unmapped status, etc.), **say so** — do not pretend the phase closed cleanly.

## Optional enforcement

`karvey-guard` can install a `clickup-sync-guard` hook (tracker-agnostic despite the name) that warns when a phase advances (`spec.json:phase` changes) without a corresponding close comment/status in the cycle. Opt-in, like the other enforcement hooks (`enforcement.md`). A skill never forces this on its own — only the hook blocks.

## Credentials

Tracker credentials come from `.connections.json` (never committed), env vars or a vault — see `management-adapters.md` (ClickUp: `clickup-protocol.md`).
