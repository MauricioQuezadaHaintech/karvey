---
name: karvey-impl
description: Karvey phase 8 — implements approved tasks DB→Backend→Frontend, one commit and one [Unreleased] line each, tracker current — after tasks approval. Triggers include "karvey impl", "karvey implementar", "ejecutar tasks karvey", "execute karvey tasks".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion
argument-hint: <change-id> [F{n}.T{n}] [--from F{n}.T{n}]
---

# Karvey Impl

## Purpose

Execute the implementation tasks in DB→Backend→Frontend order. Per-task cycle: read → execute → test → validate. Update the team's tracker (`../karvey/rules/management-adapters.md`) or `PLAN.md` in real time. States are logical (`todo | in_progress | review | done | blocked`), resolved through `project.json:management.statuses`.

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/tasks.md`
- `docs/spec/changes/{change-id}/architecture.md`
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/deviations.md` (if it exists — deviations already approved at design time)
- Pinned inputs from other agents (`spec.json:inputs` — design, design system, copy, legal), read **at the pinned commit**. Copy and legal texts are implemented verbatim from that commit; if the source moved on, stop and route it through `/karvey-iterate` instead of silently taking the newer version (`../karvey/rules/multi-agent.md` §3).
- **Engineering standards** for the layers being implemented: resolve `project.json:standards` (or `docs/spec/standards/_index.md`) and read the relevant `standards/{layer}.md` (see `../karvey/rules/engineering-standards.md`). These are a **hard constraint** on the code you write.

Enter the phase through the state tool; it refuses (and names the gate) when `tasks` is not approved:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" advance "{change-id}" impl
```
On a resumed run the change is already in `impl`: `karvey-state.py next "{change-id}" --json` confirms it.

If a specific task is given (`F{n}.T{n}`): execute only that one.
If `--from F{n}.T{n}` is given: start from that task and continue sequentially.
If nothing is specified: start from the next selectable task (Step 2).

### Step 2 — Select the task to execute

Select from **one declared source** — the tracker when `karvey-config.py resolve management` reports `external: true`, else `PLAN.md` — and say which. A task is selectable when it is `todo`, or an orphan `in_progress` (a previous session died) whose dependencies are all `review` or `done`. When the other source disagrees (a task `done` in one, `todo` in the other), report the drift; do not reconcile it silently. Respect dependencies — a dependency is satisfied when it is at `review` or `done` (impl leaves its own tasks at `review`; `done` comes at QA approval), never only at `done`:
- Start a [Backend] task only when the [DB] tasks it depends on are at `review` or `done`
- Start a [Frontend] task only when the [Backend] tasks it depends on are at `review` or `done`
- Tasks marked `(P)` can be executed in parallel with subagents
- **`[human]` tasks are never executed by the agent** (see `../karvey/rules/multi-agent.md` §5). When one is next:
  1. Present its command, verification and rollback to the executor exactly as written in `tasks.md`.
  2. Set it to **`awaiting-human`** — tracker: `comment(task, "🙋 AWAITING HUMAN: {executor} · {command}")` + the tool's tag/label `awaiting-human` (the logical state stays `todo`, or `blocked` if the team maps it so); Markdown: `🙋 awaiting-human` in `PLAN.md`.
  3. Skip to the next task that does **not** depend on it. Dependents stay blocked.
  4. When the human reports it done, run the **read-only verification** yourself. Matches the expected result → fill **Executed** (who · date · evidence) and close the task. Does not match → keep `awaiting-human` and report the difference; never "fix" it with privileged commands of your own.

### Step 3 — Start the task in management

**In the team's tracker** (`../karvey/rules/management-adapters.md`): `set_status(task, in_progress)`, plus the tool's timer if it has one. **Markdown:** edit `PLAN.md`, `⬜ todo` → `🔄 in_progress`.

### Step 4 — Execute the task

Read the full task description and its acceptance criteria.
Do the technical work: create/modify files per the File Structure Plan.

**Execution rules:**
- Respect the task's boundary — do not touch code outside its scope
- **Conform to the engineering standard** of the layer (golden path, MUST/MUST NOT) loaded in Step 1. Follow the existing stack's patterns (read the standard's `Source of truth` files before writing).
- **Do not step outside the standard silently.** If a task needs a `deprecated` pattern (e.g. frontend `current`/v2 instead of `target`/v3), a new schema, an unapproved library, or anything a standard lists as a gray zone or MUST NOT — and it is not already covered by an approved entry in `deviations.md` — **stop and raise a Deviation Request to the user before writing the code** (what the standard says · what's needed · why · options recommended-first · blast radius). On approval, append it to `deviations.md` (format in `engineering-standards.md`), then implement. Never invent a deviation mid-code.
- Do not hardcode secrets or credentials
- Validate the user context/authentication on every endpoint and data access, per the project's pattern

**Branching rules (see `../karvey/rules/deploy-workflow.md`):**
- Before starting: `git pull` and work on `feature/{change-id}` (the prefix is `karvey-config.py get branch_flow.feature_prefix --shell`). Create the branch if it does not exist.
- NEVER commit directly to `dev` or `master`.
- 1 commit per task on the feature branch, with a descriptive message following the project's git conventions.
- If the project is multi-repo (`project.json:repos`): apply the branching and the `CHANGELOG.md` entry in each repo that receives changes.

**CHANGELOG, not the version:** each commit adds its line under `## [Unreleased]` in `CHANGELOG.md` (`../karvey/rules/changelog-policy.md`), in every repo it touches. Never bump the version here: the version moves once per release, at the release step of `/karvey-deploy` (`../karvey/rules/versioning.md`). The line MUST include:
- **Responsible human**: from `git config user.name` / `user.email`. Never empty, never the AI.
- **AI model** used for the change.
- **The why** of the change (motivation, not just the what).

### Step 5 — Immediate test

Run a verification before setting the task to `review`:

**For [DB] tasks:**
- Run the query, SP, migration, or function with test data
- Confirm it returns the expected structure and produces no errors

**For [Backend] tasks:**
- Run the endpoint/function locally or on dev if available
- Verify the correct response for valid input, an auth error without credentials, and a validation error with invalid input (per the project's protocol: HTTP status codes, GraphQL errors, etc.)

**For [Frontend] tasks:**
- Verify the component/view renders without errors
- Verify states: loading, error, empty, with data

If the test fails: fix it within the same task before advancing.

### Step 6 — Complete the task in management

A task is not done until its record is updated (`../karvey/rules/phase-close.md`): **status per task**; the close comment and the cascade run per Feature.

- **Tracker:** `set_status(task, review)`; stop the timer; record the actual with `log_time(task, actual_min)`, the operation the tool's adapter row declares (`../karvey/rules/management-adapters.md`); when its `log_time` is `none`, fill the task record's `actual_ai_min` / `actual_review_min` columns instead. The estimate field is never overwritten.
- **Markdown:** `🔄 in_progress` → `👀 review` in `PLAN.md` (it becomes `✅ done` at QA approval); fill `actual_ai_min` / `actual_review_min`, keep `estimate_min`; date the history.
- **Feature finished:** `comment(feature, "✅ COMPLETED …")` with what was done and the files, then `cascade(feature)` exactly as `management-adapters.md` defines it.

### Step 7 — Continue with the next task

Repeat steps 2–6 until no task is selectable (all are `review` or `done`, or wait on an `awaiting-human` or `blocked` task).

If there are `(P)` tasks: dispatch parallel subagents to execute them simultaneously.

### Step 8 — Complete the Epic

`cascade(epic)` per `management-adapters.md` (the Epic reaches `done` only at archive). **Markdown:** overall status `👀 Implementation complete — ready for QA` in `PLAN.md`.

### Step 9 — Final output

```
✅ Implementation complete

Tasks executed: {N}/{N}
Awaiting human: {N} ({task ids · executor}) — dependents blocked
Total estimated time: {sum} | Actual time: {sum}

Files created/modified:
  DB: {list}
  Backend: {list}
  Frontend: {list}

Commits made: {N} ({N} [Unreleased] lines)

Next step:
/karvey-test {change-id}
```

## Handling blockers

If a task cannot be completed:

- **Tracker:** `comment(task, "BLOCKED: {blocker} · I need: {what unblocks it}")` + `set_status(task, blocked)`; stop the timer.
- **Markdown:** `⛔ blocked` + a note in `PLAN.md`.

Report to the user with the specific blocker and wait for it to be unblocked.


## Advance to the next phase

At the end of the phase, **ask the user**: "Shall we advance to the Testing phase now?" On their OK, run `/karvey-test {change-id}` (it advances the state). Otherwise wait. In a new session, `karvey-state.py next "{change-id}"` says where the change is.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
