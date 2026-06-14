# ClickUp Protocol — Karvey Method

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

### Update time_estimate (MANDATORY, MCP does not save it)
```bash
curl -s -X PUT "https://api.clickup.com/api/v2/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"time_estimate": {MS}}'
```

### Hours → ms conversion
| Time | Ms |
|---|---|
| 10min | 600,000 |
| 15min | 900,000 |
| 20min | 1,200,000 |
| 30min | 1,800,000 |
| 1h | 3,600,000 |
| 2h | 7,200,000 |

## Status flow
```
to do → in progress → listo! para pap → complete
```

### When starting a task
```
clickup_update_task(task_id, status="in progress")
clickup_start_time_tracking(task_id)
```

### When completing a task
```
clickup_stop_time_tracking()
clickup_create_task_comment(task_id, "SUMMARY:\n- what was done\n- files modified\n- result: OK")
clickup_update_task(task_id, status="listo! para pap")
```

### Status cascade
- When ALL tasks of a Feature → Feature to "listo! para pap"
- When ALL Features of an Epic → Epic to "listo! para pap"
- A Feature only changes when ALL layers (BD+Backend+Frontend) are done

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
