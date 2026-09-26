---
name: karvey-iterate
description: Karvey support — routes each finding (bug / spec-gap / emergent) to the incident tracker, a reopened spec or the backlog. Triggers include "karvey iterate", "iterar con karvey", "triage findings", "reabrir requirements", "reopen spec", "afán".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Agent
argument-hint: <change-id> [--finding F-NN] [--auto]
---

# Karvey Iterate — The Iteration Engine

> **Afán** = don't stop until the result is really achieved. This skill is where that lives: it takes
> what testing/QA/real-runtime surfaced and sends each item back to where it belongs, instead of
> letting it die at the end of a linear pipeline.

## Purpose

The pipeline (0→12) is the happy path. `karvey-iterate` is the **feedback brain** that closes the loop. It does ONE thing: read the findings inbox and **route** each finding to its correct edge. The phase skills (`test`, `qa`, `browse`) only **observe and classify**; this skill **routes**. Keeping routing in one place is the whole design.

Read these rules before acting:
- `../karvey/rules/iteration-loop.md` — the three feedback edges, `findings.md`, the spec-revision sub-cycle, convergence.
- `../karvey/rules/incident-tracking.md` — the `BUG-NN` tracker with state history.
- `../karvey/rules/backlog.md` — the discovery backlog (Markdown, mirrored to the team's tracker when there is one).
- `../karvey/rules/management-adapters.md` — the team's tracker and its logical states.
- `../karvey/rules/notifications.md` — the team's channel (event `incident`, opt-in).
- `../karvey/rules/phase-close.md` — the close ritual.

## When to run it

- After `test` / `qa` / `browse` produced findings.
- Any time a finding appears mid-flow ("this spec was wrong", "a new bug showed up", "good idea but out of scope").
- The orchestrator routes you here whenever `findings.md` has `open` items.

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/findings.md` (the inbox; if it doesn't exist, there's nothing to iterate — tell the user and stop)
- `docs/spec/changes/{change-id}/requirements.md` and `spec-delta.md` (for spec-gap routing)
- `docs/spec/project.json` (notifications, repos); the tracker through `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" resolve management --change "{change-id}" --json`
- `spec.json:type`, `links` and `inputs` (hotfix lane, parent/child ripple and input drift — see `../karvey/rules/multi-agent.md`). A `spec-gap` in a **child** change that alters the parent's acceptance criteria is also reported to the parent change.

If `--finding F-NN` is given, process only that finding. Otherwise process every `open` finding.

### Step 2 — Confirm/correct the classification of each finding

For each `open` finding, re-judge its type with the litmus test from `iteration-loop.md`:
- "Spec is right, code is wrong" → `bug`
- "If we'd specified this correctly, impl would differ" → `spec-gap`
- "Good idea, but a different change" → `emergent`

If a finding's type is ambiguous or its routing is irreversible (re-opening requirements, creating a new change), confirm with the user via AskUserQuestion. In `--auto` mode, route the unambiguous ones and only stop for the ambiguous/irreversible ones.

### Step 3 — Route by type

#### 3a · `bug` → incident tracker + QA micro-loop
1. Promote to a `BUG-NN` in the repo's `docs/bugs_dev_testing.md` (continue the incremental counter — read the file first). Fill priority, detection, component, reproduction, actual vs expected, and open the **State history** at `DETECTADO` (see `incident-tracking.md`).
2. Mirror to the global index `docs/spec/incidents-index.md`.
3. If the cause is unclear → recommend/invoke `/karvey-investigate` (Iron Law: no fix without investigating); paste its result as Root cause and move the incident to `DIAGNOSTICADO`.
4. The fix itself runs through the existing micro-loop: `/karvey-impl {change-id}` (fix) → `/karvey-test {change-id}` (incl. its regression test, Step 4C) → `/karvey-qa {change-id}`. The incident reaches `RESUELTO` only once a regression test exists.
5. If the resolved tracker is `external`, create/link the item there (`create_task` / `link`, see `management-adapters.md`) and record its id on the `BUG-NN`.
   If `project.json:notifications.events` includes `incident`, notify the team's channel when the `BUG-NN` reaches `DIAGNOSTICADO` or `REABIERTO` (`notifications.md`); otherwise skip.
6. **Hotfix lane** (`spec.json:type = "hotfix"`, or a production defect that cannot wait — including one found **during an E2E run in production**), see `../karvey/rules/multi-agent.md` §7:
   - **Rule: fix + `BUG-NN` + regression test in the same PR.** The PR that ships the fix also adds the tracker entry, the `findings.md` entry and a regression test that fails without the fix. A fix PR missing any of the three is not mergeable.
   - The Iron Law still holds: if the incident is live, the root cause may be written right after the fix, but the incident stays `EN FIX` until it is; `RESUELTO` only with the regression test green.
   - Each hotfix is its own release (rev bump + CHANGELOG). Chained hotfixes on the same day append one `revision_history` entry each: `{ "date", "finding": "F-NN", "bug": "BUG-NN", "release": "x.y.z", "reason" }`.
   - If the E2E run that found it is still in progress, record the run as interrupted in `test_evidence.md` and re-run it in full after the hotfix deploys — never resume it from the middle.

#### 3b · `spec-gap` → re-open requirements (spec-revision sub-cycle)
1. Reopen through the state tool (never by hand); it moves the approvals of the reopened phase and every later one to `revision_history`, and supersedes a prod approval already in the release ledger:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" reopen "{change-id}" requirements --reason "{why}" --ref "F-NN"
   ```
   The target is the earliest affected phase (`requirements`, `architecture`, `tasks` or `impl`); increment `iteration_count`.
2. Amend **only the affected requirement** in `requirements.md` + `spec-delta.md`, keeping PRD traceability. Do not rewrite the whole spec.
3. Determine the **ripple set** — which downstream phases the change actually invalidates (mockup? design? architecture? tasks? impl?). Only those are regenerated; the others are re-approved as they are, each through its own skill's gate.
4. Hand back to the user to re-approve requirements (the gate applies); `/karvey {change-id}` then shows what runs next.
5. Re-run `test`/`qa` for the affected scope.

> Be surgical. The point of the ripple set is to avoid redoing the whole pipeline for a one-line spec fix.

#### 3b-bis · Input drift → automatic ripple candidate
When a pinned input (`spec.json:inputs.design|design_system|copy|legal`, format `{repo} {path} @{commit}`) is behind its source repo — reported by `karvey-health` or noticed by any agent — create a `spec-gap` candidate finding and handle it here (see `../karvey/rules/multi-agent.md` §3):
1. Diff the input: `git -C {repo} diff {pinned}..{head} -- {path}`.
2. No behavioral impact (typo, formatting) → re-pin, append `revision_history` `{ "date", "input": "{key}", "from": "{old}", "to": "{new}", "reason", "ripple": [] }`, close the finding.
3. Impact → treat as a `spec-gap` (3b): re-pin, amend the affected requirement, and ripple by input type — `design`/`design_system` → design-graphic (+ impl of the touched components) · `copy` → impl of the touched texts · `legal` → requirements + impl, and QA re-checks the legal texts verbatim.

#### 3c · `emergent` → discovery backlog
1. Add to `docs/spec/backlog.md` as `BL-NN` (origin = this change + finding id, rough scope, priority). See `backlog.md`.
2. If the resolved tracker is `external`, also mirror it there (`mirror_backlog`, at the backlog location of `management-adapters.md`) and record the tracker id.
3. Never absorb emergent scope into the current change silently. It is captured, not done now.

### Step 4 — Update findings status

For each routed finding, set `status: routed` and fill `routed to` (BUG-NN / spec-delta req / BL-NN) in `findings.md`. A finding becomes `closed` only when its destination resolves it (incident `RESUELTO`, requirement re-approved, or backlog item acknowledged).

### Step 5 — Phase-close

Run the phase-close ritual (`phase-close.md`): comment + status in the team's tracker (or `PLAN.md`), findings and backlog in step. The knowledge sync waits for archive.

### Step 6 — Report convergence status

```
🔁 Iteration routed — {change-id}  (iteration #{iteration_count})

Findings processed: {N}
  → bug:       {N}  (BUG-{list})  → QA micro-loop
  → spec-gap:  {N}  (requirements re-opened; ripple: {phases})
  → input drift: {N}  (re-pinned: {keys} · ripple: {phases | none})
  → hotfix:    {N}  (BUG-{list} · release {x.y.z} · fix+BUG+regression in PR #{n})
  → emergent:  {N}  (backlog BL-{list})

Open findings remaining: {N bug/spec-gap blocking · N emergent captured}
Notification (incident): {channel → target | skipped (none) | not configured | not in events}

Convergence: {CONVERGED — no open bug/spec-gap, all emergent captured → can proceed to deploy/archive}
            {NOT YET — {what's left}}

Next step:
  - bugs:      /karvey-impl {change-id}  → /karvey-test → /karvey-qa
  - spec-gap:  re-approve requirements, then /karvey {change-id} for the next affected phase
  - emergent:  captured in backlog; promoted to change-ids at /karvey-archive
```

## Convergence rule (the gate)

A change may proceed to `deploy`/`archive` only when `findings.md` has **no `open` `bug` or `spec-gap`** and **all `emergent` are captured** in the backlog (see `iteration-loop.md`). `emergent` findings never block — they only need capturing. This is how the loop is guaranteed to be honored instead of optional.

## What this skill does NOT do

- It does not apply fixes (that's `impl`) or diagnose root cause itself for complex bugs (that's `investigate`).
- It never moves a change forward; its only state write is the **backward** `reopen` of the spec-revision sub-cycle. It is a support skill that orchestrates feedback, not a pipeline phase.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`. Karvey = Afán, an ona/selknam word.*
