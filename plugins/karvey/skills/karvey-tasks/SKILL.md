---
name: karvey-tasks
description: Generate implementation tasks from approved architecture. Creates Tasks (E{n}.F{n}.T{n}) with dependencies in the team's tracker, or updates PLAN.md checklist. Triggers include "karvey tasks", "generar tareas", "generate tasks", "planificar implementación", "plan implementation".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion
argument-hint: <change-id> [-y] [--sequential]
---

# Karvey Tasks

## Purpose

Generate the implementation task plan from the approved architecture. Record it in the team's tracker (Epic > Feature > Tasks with dependencies — `karvey/rules/management-adapters.md`) or in a PLAN.md checklist. Target size: 10–30 minutes per task (AI timings).

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/architecture.md`
- `docs/spec/changes/{change-id}/infra.md`
- `docs/spec/project.json` → `management` (tool, location, statuses) and `karvey/rules/management-adapters.md`
- `rules/clickup-protocol.md` (estimation rules for every tool; the ClickUp adapter when `management.tool = clickup`)

Verify `approvals.infra.approved = true`. If not, stop.

Determine sequential mode: if `--sequential`, do not use parallelism markers.

### Step 2 — Generate tasks.md draft

For each Feature identified in architecture.md, generate tasks per layer following the File Structure Plan.

**Granularity rules:**
- 1 task = 1 unit of work executable by an AI agent
- Estimated time: 10–30 minutes (AI timings)
- Maximum 1h per task. If it exceeds that, split it.
- Each task produces a verifiable artifact (SP, endpoint, component, test)
- The "done" criterion must be observable (not "implement X", but "the SP works and returns {Y}")

**Mandatory execution order:**
```
[DB] → [Backend] → [Frontend]
```
Tasks of the same layer within a Feature can be marked `(P)` if they are independent.

**Valid layer labels:** `[DB/Backend/Frontend/Infra/human]`. `Infra`-type tasks are allowed for IaC/pipeline adjustments that come up during implementation (the base infra is already defined in `infra.md`).

**`[human]` tasks** (see `karvey/rules/multi-agent.md` §5): any step the agent must not or cannot execute — IAM grants, destructive deletions, console-only settings, registrar DNS without API, payments. The agent writes it so a person can run it without interpretation:
```markdown
### F2.T3 [human] {Description} — _Depends: F2.T2_
**Executor:** {name / role}
**Command:** `{exact command or console path; prefer a versioned script in the repo}`
**Verification:** `{read-only command}` → expected: {observable result}
**Rollback:** `{exact command to undo}`
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)
```
A `[human]` task has no AI time estimate; it declares the executor instead. Tasks that depend on it wait in `awaiting-human`; independent tasks do not.

**Structure of tasks.md:**
```markdown
# Tasks: {change-id}

## Feature F1: {Name}
Requirements covered: {N.N, N.N}
Total estimated time: {sum}

### F1.T1 [DB] {Description}
**Estimate:** 15min
**Artifact:** `{db_path}/{sp_name}.sql`
**Done when:** the SP / query compiles without errors, runs with test parameters, and returns {expected result}
- Create `{schema}.{sp_name}` with parameters: `@{contextKey}`, `@{param2}`
- Validate the user context on the first line
- Return {result structure}
- Requirements: {N.N}

### F1.T2 [Backend] {Description} — _Depends: F1.T1_
**Estimate:** 20min
**Artifact:** `{backend_path}/{name}`
**Done when:** the endpoint returns 200 with {structure} for a valid request, 401 without auth, 422 with invalid input
- Create endpoint `{name}`
- Validate the auth token and extract the user context
- Call the DB with `{db_helper()}`
- Handle errors without exposing the stack trace
- Requirements: {N.N}

### F1.T3 [Frontend] {Description} — _Depends: F1.T2_ (P)
**Estimate:** 25min
**Artifact:** `{frontend_path}/{name}`
**Done when:** the component renders data from the endpoint, handles loading/error/empty states
- Create component `{name}`
- Consume the endpoint via `{api_layer}/{service}`
- Implement states: loading, error, empty, with data
- Requirements: {N.N}
```

### Step 3 — Review gate

Verify before writing:
- [ ] Every requirement has at least one task that implements it
- [ ] Every component of the File Structure Plan has its corresponding task
- [ ] The DB→Backend→Frontend order is respected with explicit dependencies
- [ ] Every task has an observable done criterion
- [ ] No task exceeds a 1h estimate
- [ ] [DB] tasks do not modify application code and vice versa
- [ ] Testing tasks are included (at least one per Feature)
- [ ] Every step the agent must not execute is a `[human]` task with executor, command, verification and rollback — none is hidden inside an agent task

If there are gaps: fix and re-verify. Maximum 2 iterations.

### Step 4 — Write tasks.md

```
docs/spec/changes/{change-id}/tasks.md
```

Update `spec.json`: `phase: "tasks-generated"`, `approvals.tasks.generated: true`.

### Step 4B — Update knowledge graph

Sync the knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`) to reflect the created `tasks.md`.
If `docs/spec/graphify-out/` does not exist, invoke `/graphify docs/spec/` without `--update`.

### Step 5 — Present for approval

If flag `-y`: auto-approve.

Show a summary:
```
📋 Tasks generated: docs/spec/changes/{change-id}/tasks.md

Summary:
  Features: {N}
  Total tasks: {N} ({N} DB, {N} Backend, {N} Frontend, {N} Test)
  Total estimated time: {sum}

Coverage:
  Requirements covered: {N}/{N}
  File Structure Plan components: {N}/{N}

Do you approve the tasks to continue?
```

### Step 6A — Create Tasks in the team's tracker (`management-adapters.md`)

Read `spec.json` for the tracker ids (`clickup.epic_id`, `clickup.feature_ids`, `clickup.backlog_list_id` — historical key, used for every tool).

For each task: `create_task(feature, E{n}.F{n}.T{n}, estimate_min)` in `project.json:management.tool`, initial state `todo`,
then the dependencies below with the tool's own mechanism (Jira issue links, Linear relations, ADO predecessor/successor
links, GitHub sub-issues/"blocked by", spreadsheet `depends_on` column). Credentials from `.connections.json` (git-ignored),
env vars or a vault — never in the repo.

**ClickUp adapter example:**

Read credentials from `.connections.json` (see `rules/clickup-protocol.md`). If it does not exist, create it and add it to `.gitignore` before continuing.

For each task, create it in ClickUp:
```
clickup_create_task
  name: "E{n}.F{n}.T{n} [Layer] {Description}"
  list_id: "{backlog_list_id}"
  tags: ["{client_tag}"]
  description: (see format)
  priority: "normal"
  start_date: "YYYY-MM-DD"
  due_date: "YYYY-MM-DD"
```

Task description format:
```
E{n}.F{n}.T{n}: [Layer] {Name}

Parent feature: E{n}.F{n} {Feature name}

Description:
{what to do in detail so that an AI agent can execute it}

Acceptance criteria:
- [ ] {criterion 1}
- [ ] {criterion 2}

Dependencies:
- Depends on: {list of previous tasks}
- Blocks: {list of tasks waiting on this one}

Estimate: {N}min

When finished:
1. Stop time tracking (if the tool has it)
2. Comment: a summary of what was done, modified files
3. Change status to the team's `review` state ({status:review})

Done with the Karvey Method
```

Immediately after creating each task:
```
clickup_add_tag_to_task(task_id, "{client_tag}")
```

Update `time_estimate` via the REST API (the MCP does not save it):
```bash
curl -s -X PUT "https://api.clickup.com/api/v2/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -d '{"time_estimate": {MIN * 60000}}'
```

Create dependencies via the REST API:
```bash
# Task B depends on Task A: B waits for A
curl -s -X POST "https://api.clickup.com/api/v2/task/{B_ID}/dependency" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -d '{"depends_on":"{A_ID}"}'
```

Dependencies to create (every tool):
- Feature ← its Tasks (the Feature depends on all its Tasks finishing)
- Epic ← its Features
- [Backend] → [DB] within each Feature
- [Frontend] → [Backend] within each Feature

Check the active sprint and add the tasks (ClickUp; other tools: their sprint/iteration/cycle, if the team uses one):
```bash
curl -s -X POST "https://api.clickup.com/api/v2/list/{SPRINT_LIST_ID}/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json"
```

Update `spec.json` with the IDs of the created tasks.

### Step 6B — Update PLAN.md (Markdown)

Replace the "Tasks" and "Task status" sections with the full checklist:

```markdown
## Tasks

### Feature F1: {Name}

- [ ] F1.T1 [DB] {description} — est: 15min
- [ ] F1.T2 [Backend] {description} — est: 20min (depends F1.T1)
- [ ] F1.T3 [Frontend] {description} — est: 25min (depends F1.T2)

## Task status
> Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked`

| Task | Status | Estimate | Actual | Notes |
|------|--------|----------|------|-------|
| F1.T1 [DB] | ⬜ todo | 15min | — | |
| F1.T2 [Backend] | ⬜ todo | 20min | — | |
| F1.T3 [Frontend] | ⬜ todo | 25min | — | |
```

### Step 7 — Final output

On approval: `approvals.tasks.approved: true`, `phase: "tasks-approved"`.

```
✅ Tasks approved

Management: {N tasks created in {tool} with dependencies | PLAN.md updated}

Next step:
/karvey-impl {change-id}
```


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Implementation phase now?"
- If they confirm → run `/karvey-impl {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (the method's gate).
- If you resume in another session, `/karvey {change-id}` shows which phase you are in and which one is next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
