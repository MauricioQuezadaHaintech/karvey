# ClickUp Protocol — Karvey Method

> This is the **ClickUp adapter** of `management-adapters.md` (used when `project.json:management.tool = clickup`).
> Other trackers (Jira, Linear, Azure Boards, GitHub Projects, spreadsheet, Markdown) are described there;
> the estimation rules below apply to every tool.

## Credentials — `.connections.json`

Credentials are stored in `.connections.json` at the project root. **This file is NEVER committed to the repository.**

### Initial setup (if it does not exist)

If `.connections.json` does not exist in the project, create it with this structure and add it to `.gitignore`:

```bash
# Add to .gitignore
echo ".connections.json" >> .gitignore
```

```json
{
  "clickup": {
    "api_key": "YOUR_CLICKUP_API_KEY",
    "user_id": "YOUR_CLICKUP_USER_ID",
    "workspace_id": "YOUR_WORKSPACE_ID"
  }
}
```

> Tell the user to fill in the real values in `.connections.json` locally before continuing.

### Read credentials in bash

```bash
API_KEY=$(python3 -c "import json; print(json.load(open('.connections.json'))['clickup']['api_key'])")
USER_ID=$(python3 -c "import json; print(json.load(open('.connections.json'))['clickup']['user_id'])")
WORKSPACE_ID=$(python3 -c "import json; print(json.load(open('.connections.json'))['clickup']['workspace_id'])")
```

## WBS structure: Epic > Feature > Task

```
E{n} Epic name
├── E{n}.F{n} Feature name
│   ├── E{n}.F{n}.T{n} [BD] Description
│   ├── E{n}.F{n}.T{n} [Backend] Description
│   └── E{n}.F{n}.T{n} [Frontend] Description
```

### Valid layers
| Tag | Agent |
|---|---|
| `[BD]` | Database (SPs, migrations, queries) |
| `[Backend]` | Server logic (API, services, functions) |
| `[Frontend]` | Vue/React/UI |
| `[Infra]` | Docker, pipelines, infra |
| `[Test]` | Testing and QA |

## MCP operations

### Create Epic
```
clickup_create_task
  name: "E{n} {Epic name}"
  list_id: "{BACKLOG_LIST_ID}"
  task_type: "Epic"
  description: (see epic template)
  tags: ["{client}"]
  priority: "normal"
```

### Create Feature
```
clickup_create_task
  name: "E{n}.F{n} {Feature name}"
  list_id: "{BACKLOG_LIST_ID}"
  task_type: "Feature"
  description: (see feature template)
  tags: ["{client}"]
```

### Create Task
```
clickup_create_task
  name: "E{n}.F{n}.T{n} [Layer] {Description}"
  list_id: "{BACKLOG_LIST_ID}"
  description: (see task template)
  tags: ["{client}"]
  priority: "normal"
  start_date: "YYYY-MM-DD"
  due_date: "YYYY-MM-DD"
```
> NOTE: `time_estimate` does NOT work via MCP. Always update it via REST API after creating.

## REST API operations

### Create dependency (task A waits for task B)
```bash
curl -s -X POST "https://api.clickup.com/api/v2/task/{A}/dependency" \
  -H "Authorization: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"depends_on":"{B}"}'
```

### Add task to the active Sprint
```bash
curl -s -X POST "https://api.clickup.com/api/v2/list/{SPRINT_LIST_ID}/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" \
  -H "Content-Type: application/json"
```

### Update time_estimate (MANDATORY at creation, MCP does not save it)

`time_estimate` is written **once**, by `karvey-tasks`, from the task's estimate. It is never overwritten
afterwards: the actual time is a time entry (start/stop tracking, or a manual entry), so estimate vs actual
stays measurable.
```bash
curl -s -X PUT "https://api.clickup.com/api/v2/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"time_estimate": {MS}}'
```

### Time → ms conversion
| Time | Ms |
|---|---|
| 10min | 600,000 |
| 15min | 900,000 |
| 20min | 1,200,000 |
| 30min | 1,800,000 |
| 60min | 3,600,000 |

## Estimation — AI times, in minutes (not hours)

> **Estimates reflect AI execution time + human review, expressed in MINUTES — not human coding hours.**
> An AI develops a whole 30-SP API in ~15 min; a single endpoint in ~30 s. The real bottleneck is human
> review and the cross-layer dependencies (BD → Backend → Frontend), not the AI.

- **A task is estimated in minutes. Typical task: 10–30 min. Cap: ~60 min → if it exceeds, split it.**
- The legacy "6-hour rule" assumed *human* coding time; under AI-driven development the effective cap is **~60 min**.
- Splitting keeps progress traceable, commits atomic/reviewable, and surfaces blockers early.

| Work type | AI dev | + Human review | **Estimate** |
|---|---|---|---|
| SP simple (basic CRUD) | ~1min | 5min | **10min** |
| SP with business logic | 2–3min | 5–10min | **15min** |
| SP complex + new table | 3–5min | 10min | **20min** |
| Endpoint simple (calls SP, returns) | ~30s | 5min | **10min** |
| Endpoint with logic (validation, integration) | 1–2min | 5–10min | **15min** |
| Complex service (queue, external integration) | 5–10min | 10–15min | **25–30min** |
| UI simple form/component | 2–3min | 10min | **20min** |
| UI complex (state, preview, drag&drop) | 5–10min | 10–15min | **25–30min** |
| Parser / data processing | 5–10min | 10min | **25min** |
| Test plan + run with evidence | 5–10min | 5min | **15min** |

**Aggregation:** Feature = sum of its tasks (typ. 1–3 h) · Epic = sum of its features (typ. 3–8 h). A whole API
can be one Epic (~15 min–2 h of pure AI, ~1 day with review). Testing is included in "AI dev" (the AI writes
and runs tests as part of development).

## Status flow

ClickUp statuses are the **team's** — mapped in `project.json:management.statuses` to the logical states
`todo | in_progress | review | done | blocked` (see `management-adapters.md`). HainTech example:
```
to do → in progress → listo! para pap → complete
```
Below, `{status:in_progress}` / `{status:review}` mean "the ClickUp status the team mapped to that logical state".

> **Mandatory, not optional.** Status changes per task; the comment and the cascade run per Feature and at every phase close: the `phase-close.md` ritual — a numbered step, not a "should". Tasks left stale (work done but ClickUp not moved) are a process defect. See `phase-close.md`.

### When starting a task
```
clickup_update_task(task_id, status="{status:in_progress}")   # set_status(task, in_progress)
clickup_start_time_tracking(task_id)
```

### When completing a task
```
clickup_stop_time_tracking()                              # the actual, as a time entry
clickup_update_task(task_id, status="{status:review}")   # set_status(task, review)
```
When the last task of a Feature closes: one summary comment on the Feature (what was done · files · result)
and the cascade (`phase-close.md`).

### Status cascade
The one cascade is defined in `management-adapters.md` → *The cascade*; ClickUp applies it with
`clickup_update_task(<feature or epic id>, status=…)`.

### Phase-level status (not just leaf tasks)

The pipeline phases are a **checklist of the Epic** (a ClickUp checklist on the Epic task, one item per phase), never Features — Features are the change's functional areas (`management-adapters.md` → *One work breakdown*). Closing a phase ticks its item, so the board reflects pipeline progress (`requirements → … → deploy`), not only leaf impl tasks. QA and deploy items are the subtasks `E{n}.QA` and `E{n}.DEPLOY` of the Epic. Run this at every phase close, per `phase-close.md`.

### Incident & backlog mirroring
- A `BUG-NN` (see `incident-tracking.md`) created during test/qa is mirrored to a ClickUp task; the `BUG-NN` records the task id and vice-versa.
- An `emergent` finding goes to the ClickUp backlog list (`backlog_list_id`) and to `docs/spec/backlog.md` (see `backlog.md`). Status is kept in sync at phase close.

## Backlogs per project

List IDs are specific to each workspace. Get them with:
```
clickup_get_workspace_hierarchy
  max_depth: 3
```
Find the project's folder and copy the `list_id` of the corresponding backlog.

| Project | List ID |
|---|---|
| {Project 1} | `YOUR_BACKLOG_LIST_ID` |
| {Project 2} | `YOUR_BACKLOG_LIST_ID` |

## Active sprint

Verify before each record:
```
clickup_get_list
  list_name: "Sprint XX"
```
Find it in the workspace's sprints folder (e.g. "Dev Sprints").
