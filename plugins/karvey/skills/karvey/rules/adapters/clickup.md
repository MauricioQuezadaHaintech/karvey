# Tracker adapter: ClickUp

Loaded only when `karvey-config.py resolve management` returns `tool: clickup`. The logical operations, states,
natural keys, outbox, work breakdown, cascade and estimation are tool-neutral and live in the management
adapters rule[^r-ma]; this file holds only how ClickUp does them.

<!-- karvey:generated load-lists:adapter-used-by -->
<!-- /karvey:generated load-lists:adapter-used-by -->

| Operation | ClickUp | log_time |
|---|---|---|
| `create_epic` / `create_feature` / `create_task` | `clickup_create_task` (MCP) with `task_type` Epic / Feature, or REST | — |
| `set_status` | `clickup_update_task(id, status=…)` | — |
| `comment` | `clickup_create_task_comment` | — |
| `log_time` | time entry: start/stop tracking, or `POST /task/{id}/time` | time entry |
| estimate | `time_estimate` via REST only (the MCP does not save it), written once | — |

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

## Creating a change's tasks (`karvey-tasks` Step 6A)

For each task, after the find-by-key search:
```
clickup_create_task
  name: "E{n}.F{n}.T{n} [Layer] {Description}"
  list_id: "{location}"
  tags: ["{client}"]
  description: (the task description format of karvey-tasks)
  priority: "normal"
  start_date: "YYYY-MM-DD"
  due_date: "YYYY-MM-DD"
```
Immediately after creating each task: `clickup_add_tag_to_task(task_id, "{client}")`, then the estimate through
REST (`time_estimate` = minutes × 60,000, written once, never overwritten with an actual) and the dependencies
through REST (task B waits for task A: `POST /task/{B_ID}/dependency` with `{"depends_on":"{A_ID}"}`). Add the
tasks to the active sprint list when the team uses one (`POST /list/{SPRINT_LIST_ID}/task/{TASK_ID}`).

## Status flow

ClickUp statuses are the **team's** — mapped in `project.json:management.statuses` to the logical states
`todo | in_progress | review | done | blocked`. An example flow a team might declare:
```
to do → in progress → ready for review → complete
```
Below, `{status:in_progress}` / `{status:review}` mean "the ClickUp status the team mapped to that logical state".

> **Mandatory, not optional.** Status changes per task; the comment and the cascade run per Feature and at every phase close (the phase-close ritual[^r-pc]) — a numbered step, not a "should". Tasks left stale (work done but ClickUp not moved) are a process defect.

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
and the cascade (the phase-close ritual[^r-pc]).

### Status cascade
The one cascade is defined in the management adapters rule[^r-ma] → *The cascade*; ClickUp applies it with
`clickup_update_task(<feature or epic id>, status=…)`.

### Phase-level status (not just leaf tasks)

The pipeline phases are a **checklist of the Epic** (a ClickUp checklist on the Epic task, one item per phase), never Features — Features are the change's functional areas (*One work breakdown*[^r-ma]). Closing a phase ticks its item, so the board reflects pipeline progress (`requirements → … → deploy`), not only leaf impl tasks. QA and deploy items are the subtasks `E{n}.QA` and `E{n}.DEPLOY` of the Epic. Run this at every phase close[^r-pc].

### Incident & backlog mirroring
- A `BUG-NN`[^r-inc] created during test/qa is mirrored to a ClickUp task; the `BUG-NN` records the task id and vice-versa.
- An `emergent` finding goes to the ClickUp backlog list (`backlog_list_id`) and to `docs/spec/backlog.md`[^r-bl]. Status is kept in sync at phase close.

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

[^r-ma]: management-adapters.md — the tool-neutral contract; context only, not opened.
[^r-pc]: phase-close.md — the close ritual; context only, not opened.
[^r-inc]: incident-tracking.md — the incident tracker; context only, not opened.
[^r-bl]: backlog.md — the backlog format; context only, not opened.
