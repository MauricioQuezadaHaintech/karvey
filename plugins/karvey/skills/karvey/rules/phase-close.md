# Phase-Close Ritual — every phase closes the same way

> The problem: tracker updates were a "should", so they got skipped and tasks were left stale. The close
> is a **numbered step** at the end of the skills that run it. No phase advances silently.

## Who runs it

`karvey-impl`, `karvey-test` and `karvey-qa` run this ritual at their close and cite this rule;
`karvey-iterate` runs action 3 when it routes findings. Granularity:

- **Status per task:** each impl task moves its own status when it closes (`todo → in_progress → review`).
- **Comment and cascade per Feature:** the close comment and the cascade run once per Feature (when its last
  task closes) and once at the phase close — never per task.

## The ritual (4 actions, in order)

### 1. Comment what happened
A short, factual close comment on the Feature (or the Epic item that represents the phase): what was done ·
artifacts produced · result. Team's tracker: the `comment` operation of `management-adapters.md`.
Markdown: a history row in `PLAN.md`.

### 2. Change state
- `set_status(<item>, <logical state>)`, resolved through `management-adapters.md` (resolution order and the
  missing-map clause live there; this rule does not restate them).
- **Cascade:** apply the one cascade of `management-adapters.md` → `cascade`. The Epic reaches `done` only at
  archive.
- Markdown: flip the marker in `PLAN.md` (legend in `management-adapters.md`, 🙋 included) and fill the actual
  time. The estimate column is never overwritten.

### 3. Sweep findings, backlog and the outbox
- Findings from `test`/`qa`/`browse` are in `findings.md` (`iteration-loop.md`); if any is `open`, point the
  user to `/karvey-iterate` before advancing.
- `emergent` items reached `backlog.md` (mirrored to the tracker if the team wants it).
- **Outbox retry:** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" outbox list {change-id}`; apply
  each ready entry, then `outbox done {change-id} <entry_id>` (or `--failed "<error>"` to keep it).

### 4. Record the state
- `phase` and approvals are written only by `karvey-state.py` (`generated`, `approve`, `advance`; see
  `state-machine.md`), never by hand.
- An approval carries `--by`, `--role` (`human` | `ceo-delegate`) and `--ref` (the `D-NN`, or a URL).
- Knowledge sync does not run here: it runs at archive and on demand (`knowledge-sync.md`).

## Gate before advancing

Do not ask the gate question (`gates.md`) until actions 1–4 are done. If a tracker update failed (API
error, missing location, unmapped status), **say so** and leave it in the outbox — do not pretend the phase
closed cleanly.

## Credentials

Tracker credentials come from `.connections.json` (never committed), env vars or a vault — see
`management-adapters.md` (ClickUp: `clickup-protocol.md`).
