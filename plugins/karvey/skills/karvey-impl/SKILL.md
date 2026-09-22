---
name: karvey-impl
description: Execute implementation tasks sequentially updating the team's tracker (ClickUp, Jira, Linear, Azure Boards, GitHub Projects, spreadsheet) or PLAN.md. Read → execute → test → validate cycle per task. Triggers include "karvey impl", "implementar", "implement", "ejecutar tasks", "execute tasks", "desarrollar", "develop".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
argument-hint: <change-id> [F{n}.T{n}] [--from F{n}.T{n}]
---

# Karvey Impl

## Purpose

Execute the implementation tasks in DB→Backend→Frontend order. Per-task cycle: read → execute → test → validate. Update the team's tracker (`karvey/rules/management-adapters.md`) or `PLAN.md` in real time. States are logical (`todo | in_progress | review | done | blocked`), resolved through `project.json:management.statuses`.

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/tasks.md`
- `docs/spec/changes/{change-id}/architecture.md`
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/deviations.md` (if it exists — deviations already approved at design time)
- Pinned inputs from other agents (`spec.json:inputs` — design, design system, copy, legal), read **at the pinned commit**. Copy and legal texts are implemented verbatim from that commit; if the source moved on, stop and route it through `/karvey-iterate` instead of silently taking the newer version (`karvey/rules/multi-agent.md` §3).
- **Engineering standards** for the layers being implemented: resolve `project.json:standards` (or `docs/spec/standards/_index.md`) and read the relevant `standards/{layer}.md` (see `karvey/rules/engineering-standards.md`). These are a **hard constraint** on the code you write.

Verify `approvals.tasks.approved = true`. If not, stop.

If a specific task is given (`F{n}.T{n}`): execute only that one.
If `--from F{n}.T{n}` is given: start from that task and continue sequentially.
If nothing is specified: start from the first pending task.

### Step 2 — Select the task to execute

Identify the next pending task while respecting dependencies:
- Do not execute [Backend] until its dependent [DB] is completed
- Do not execute [Frontend] until its dependent [Backend] is completed
- Tasks marked `(P)` can be executed in parallel with subagents
- **`[human]` tasks are never executed by the agent** (see `karvey/rules/multi-agent.md` §5). When one is next:
  1. Present its command, verification and rollback to the executor exactly as written in `tasks.md`.
  2. Set it to **`awaiting-human`** — tracker: `comment(task, "🙋 AWAITING HUMAN: {executor} · {command}")` + the tool's tag/label `awaiting-human` (the logical state stays `todo`, or `blocked` if the team maps it so); Markdown: `🙋 awaiting-human` in `PLAN.md`.
  3. Skip to the next task that does **not** depend on it. Dependents stay blocked.
  4. When the human reports it done, run the **read-only verification** yourself. Matches the expected result → fill **Executed** (who · date · evidence) and close the task. Does not match → keep `awaiting-human` and report the difference; never "fix" it with privileged commands of your own.

### Step 3 — Start the task in management

**In the team's tracker** (`management-adapters.md`): `set_status(task, in_progress)` — plus time tracking if the tool has it.
ClickUp adapter example:
```
clickup_update_task(task_id, status="{status:in_progress}")
clickup_start_time_tracking(task_id)
```

**Markdown (`PLAN.md`):**
Edit `PLAN.md`, change `⬜ todo` → `🔄 in_progress` for the task.

### Step 4 — Execute the task

Read the full task description and its acceptance criteria.
Do the technical work: create/modify files per the File Structure Plan.

**Execution rules:**
- Respect the task's boundary — do not touch code outside its scope
- **Conform to the engineering standard** of the layer (golden path, MUST/MUST NOT) loaded in Step 1. Follow the existing stack's patterns (read the standard's `Source of truth` files before writing).
- **Do not step outside the standard silently.** If a task needs a `deprecated` pattern (e.g. frontend `current`/v2 instead of `target`/v3), a new schema, an unapproved library, or anything a standard lists as a gray zone or MUST NOT — and it is not already covered by an approved entry in `deviations.md` — **stop and raise a Deviation Request to the user before writing the code** (what the standard says · what's needed · why · options recommended-first · blast radius). On approval, append it to `deviations.md` (format in `engineering-standards.md`), then implement. Never invent a deviation mid-code.
- Do not hardcode secrets or credentials
- Validate the user context/authentication on every endpoint and data access, per the project's pattern

**Branching rules (see `karvey/rules/deploy-workflow.md`):**
- Before starting: do a `git pull` and work on the `feature/{change-id}` branch (use the `feature_prefix` from `docs/spec/project.json` if it differs). Create the branch if it does not exist.
- NEVER commit directly to `dev` or `master`.
- 1 commit per task on the feature branch, with a descriptive message following the project's git conventions.
- If the project is multi-repo (`project.json:repos`): apply the branching and the `CHANGELOG.md` entry in each repo that receives changes.

**Version bump (if the project manages it):**
Detect the versioning mechanism by reading `architecture.md` or exploring the project:
- `package.json` → update the `version` field
- `pyproject.toml` / `setup.py` → update `version`
- `VERSION` file → update the value
- `git tags` → create a tag at the end of the Epic
- If there is a `CHANGELOG.md` or equivalent → add an entry with the version, date, and description
- If the project has no versioning → skip this step

IN ADDITION to the bump, record an entry in `CHANGELOG.md` following the `karvey/rules/changelog-policy.md` policy. The entry MUST include:
- **Responsible human**: taken from `git config user.name` / `git config user.email`. Never leave it empty nor replace it with the AI.
- **AI model** used for the change.
- **The why** of the change (motivation / objective, not just the what).

### Step 5 — Immediate test

Run a verification before marking it as completed:

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

This is the **per-task phase-close ritual** (`karvey/rules/phase-close.md`): comment + status + cascade, applied to every task. It is mandatory, not a "should" — a task is not done until its management record is updated.

**In the team's tracker:** `comment(task, "✅ COMPLETED …")` + `set_status(task, review)` + record the actual time where the tool supports it.
ClickUp adapter example:
```
clickup_stop_time_tracking()
clickup_create_task_comment(task_id,
  "✅ COMPLETED\n\nDone:\n- {what was done}\n\nFiles:\n- {list}\n\nResult: OK")
clickup_update_task(task_id, status="{status:review}")
```

ClickUp: update the actual time via the REST API:
```bash
curl -s -X PUT "https://api.clickup.com/api/v2/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -d '{"time_estimate": {actual_time_ms}}'
```

**Status cascade** (`cascade(feature)`):
When ALL tasks of a Feature are in `review`:
```
comment(feature, "All {layer} tasks completed.")
# Only change the Feature if ALL layers are finished
set_status(feature, review)  # if applicable
```

**Markdown (`PLAN.md`):**
Edit `PLAN.md`:
- Change `🔄 in_progress` → `👀 review` (it becomes `✅ done` once validated by test/qa)
- Update the actual time in the status table
- Update the date in the history

### Step 7 — Continue with the next task

Repeat steps 2–6 until all tasks are completed.

If there are `(P)` tasks: dispatch parallel subagents to execute them simultaneously.

### Step 8 — Complete the Epic

When ALL Features are in `review`:

**In the team's tracker:**
```
comment(epic, "All Features completed. Epic ready for QA.")
set_status(epic, review)
```

**Markdown (`PLAN.md`):**
Update `PLAN.md`: overall status `👀 Implementation complete — ready for QA`.

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

Commits made: {N}
Version: {new version}

Next step:
/karvey-test {change-id}
```

## Handling blockers

If a task cannot be completed:

**In the team's tracker:**
```
comment(task, "BLOCKED: {description of the blocker}\n\nI need: {what is needed to unblock}")
set_status(task, blocked)      # ClickUp: also clickup_stop_time_tracking()
```

**Markdown (`PLAN.md`):**
Mark `⛔ blocked` + a note in PLAN.md.

Report to the user with the specific blocker and wait for it to be unblocked.


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Testing phase now?"
- If they confirm → run `/karvey-test {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (the method's gate).
- If you resume in another session, `/karvey {change-id}` shows which phase you are in and which one is next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
