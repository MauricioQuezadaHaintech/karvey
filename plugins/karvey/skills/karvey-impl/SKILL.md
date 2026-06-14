---
name: karvey-impl
description: Execute implementation tasks sequentially with ClickUp time tracking or PLAN.md updates. Read → execute → test → validate cycle per task. Triggers include "karvey impl", "implementar", "implement", "ejecutar tasks", "execute tasks", "desarrollar", "develop".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
argument-hint: <change-id> [F{n}.T{n}] [--from F{n}.T{n}]
---

# Karvey Impl

## Purpose

Execute the implementation tasks in DB→Backend→Frontend order. Per-task cycle: read → execute → test → validate. Update ClickUp or PLAN.md in real time.

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/tasks.md`
- `docs/spec/changes/{change-id}/architecture.md`
- `docs/spec/changes/{change-id}/requirements.md`

Verify `approvals.tasks.approved = true`. If not, stop.

If a specific task is given (`F{n}.T{n}`): execute only that one.
If `--from F{n}.T{n}` is given: start from that task and continue sequentially.
If nothing is specified: start from the first pending task.

### Step 2 — Select the task to execute

Identify the next pending task while respecting dependencies:
- Do not execute [Backend] until its dependent [DB] is completed
- Do not execute [Frontend] until its dependent [Backend] is completed
- Tasks marked `(P)` can be executed in parallel with subagents

### Step 3 — Start the task in management

**If ClickUp:**
```
clickup_update_task(task_id, status="in progress")
clickup_start_time_tracking(task_id)
```

**If Markdown:**
Edit `PLAN.md`, change `⬜ pending` → `🔄 in progress` for the task.

### Step 4 — Execute the task

Read the full task description and its acceptance criteria.
Do the technical work: create/modify files per the File Structure Plan.

**Execution rules:**
- Respect the task's boundary — do not touch code outside its scope
- Follow the existing stack's patterns (read similar files from the codebase before writing)
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

**If ClickUp:**
```
clickup_stop_time_tracking()
clickup_create_task_comment(task_id,
  "✅ COMPLETED\n\nDone:\n- {what was done}\n\nFiles:\n- {list}\n\nResult: OK")
clickup_update_task(task_id, status="listo! para pap")
```

Update the actual time via the REST API:
```bash
curl -s -X PUT "https://api.clickup.com/api/v2/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -d '{"time_estimate": {actual_time_ms}}'
```

**ClickUp status cascade:**
When ALL tasks of a Feature are in "listo! para pap":
```
clickup_create_task_comment(feature_id, "All {layer} tasks completed.")
# Only change the Feature if ALL layers are finished
clickup_update_task(feature_id, status="listo! para pap")  # if applicable
```

**If Markdown:**
Edit `PLAN.md`:
- Change `🔄 in progress` → `✅ completed`
- Update the actual time in the status table
- Update the date in the history

### Step 7 — Continue with the next task

Repeat steps 2–6 until all tasks are completed.

If there are `(P)` tasks: dispatch parallel subagents to execute them simultaneously.

### Step 8 — Complete the Epic

When ALL Features are in "listo! para pap":

**If ClickUp:**
```
clickup_create_task_comment(epic_id, "All Features completed. Epic ready for QA.")
clickup_update_task(epic_id, status="listo! para pap")
```

**If Markdown:**
Update `PLAN.md`: overall status `✅ Implementation complete`.

### Step 9 — Final output

```
✅ Implementation complete

Tasks executed: {N}/{N}
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

**If ClickUp:**
```
clickup_stop_time_tracking()
clickup_create_task_comment(task_id, "BLOCKED: {description of the blocker}\n\nI need: {what is needed to unblock}")
clickup_update_task(task_id, status="blocked")
```

**If Markdown:**
Mark `⛔ blocked` + a note in PLAN.md.

Report to the user with the specific blocker and wait for it to be unblocked.


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Testing phase now?"
- If they confirm → run `/karvey-test {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (the method's gate).
- If you resume in another session, `/karvey {change-id}` shows which phase you are in and which one is next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
