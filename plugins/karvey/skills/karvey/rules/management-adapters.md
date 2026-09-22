# Rule: Management adapters — the team's tracker and its status flow

> Karvey used to assume **ClickUp**, with a team-specific status name (`listo! para pap`) written as a
> literal in several skills; everything else fell back to `PLAN.md`. A team on Jira, Linear, Azure Boards,
> GitHub Projects or a spreadsheet had no path. The tool and its status flow are now **team settings**,
> asked once by `karvey-init` and stored in `project.json:management`. Phase skills speak in **logical
> operations and logical states**; this rule maps them to each tool.

## Settings (`project.json:management`)

```json
"management": {
  "tool": "clickup | jira | linear | azure-boards | github-projects | spreadsheet | markdown | other",
  "location": "{ClickUp backlog list id | Jira project key | Linear team | ADO project/area | GitHub project number | spreadsheet path or id}",
  "statuses": {
    "todo": "{tool status name}",
    "in_progress": "{…}",
    "review": "{…}",
    "done": "{…}",
    "blocked": "{…}"
  },
  "hierarchy": "epic>feature>task",
  "via": "mcp | cli | api | file"
}
```

`spec.json:management` keeps naming the **tool** of each change (`"clickup"`, `"markdown"`, `"jira"`…), so
changes created before this rule stay valid.

## The 5 logical states

| Logical | Meaning in Karvey | Example — ClickUp (HainTech) | Example — Jira | Example — spreadsheet |
|---|---|---|---|---|
| `todo` | planned, not started | `to do` | `To Do` | `Pending` |
| `in_progress` | being worked on | `in progress` | `In Progress` | `In progress` |
| `review` | implemented, awaiting validation / human review | `listo! para pap` | `In Review` | `Review` |
| `done` | validated / released | `complete` | `Done` | `Done` |
| `blocked` | cannot advance | `blocked` | `Blocked` | `Blocked` |

Skills write `status → review`, never a literal name. The table's examples are **values a team declares**,
not defaults.

### Missing map (compatibility)
IF a tracker tool is set and `statuses` is missing (e.g. a project created before 3.10 with only
`"management": "clickup"`), THEN before the first status change the skill **reads the real statuses of the
list/project from the tool**, proposes the mapping, confirms it **once** with the user and writes it to
`project.json`. It never guesses a status name silently.

## Logical operations

| Operation | Used by | What it means |
|---|---|---|
| `create_epic(change)` | init | the unit that represents the change |
| `create_feature(epic, capability/layer)` | requirements, tasks | grouping level (skip if `hierarchy` has no feature level) |
| `create_task(feature, E{n}.F{n}.T{n}, estimate_min)` | tasks | a 10–30 min AI task (see `clickup-protocol.md` → Estimation) |
| `set_status(item, logical_state)` | impl, qa, deploy, phase-close | resolved via `statuses` |
| `comment(item, text)` | phase-close, qa, deploy | factual close comment |
| `cascade(parent)` | phase-close, impl | parent → `review` when ALL children are; epic when ALL features are |
| `link(item, url)` | deploy, qa | PR / review document |
| `mirror_backlog(BL-NN)` | iterate, archive | backlog item in the tracker, if the team wants it |

## Adapters

| Tool | How the session does it | Notes |
|---|---|---|
| **ClickUp** | ClickUp MCP or REST API — full protocol in `clickup-protocol.md` | `time_estimate` only via REST (MCP does not persist it) |
| **Jira** | Atlassian MCP, `jira` CLI or REST (`/rest/api/3/issue`, `/transitions`) | status change = **transition**, look up the transition id for the target status |
| **Linear** | Linear MCP or GraphQL API | states are per team (`workflowStates`) |
| **Azure Boards** | `az boards work-item create/update` | Epic/Feature/Task or User Story per process template; state per template |
| **GitHub Projects** | `gh project item-add/item-edit`, issues | status is a single-select field of the project |
| **Spreadsheet** (Excel/Sheets/CSV) | a file in the repo (`docs/spec/plan.csv` / `.xlsx`) or a Sheet via the team's CLI/MCP | one row per item: `id, level, title, layer, estimate_min, status, updated_at, link` |
| **Markdown** | `PLAN.md` in the change directory | the fallback; markers `⬜ 🔄 👀 ✅ ⛔` for `todo in_progress review done blocked` |
| **Other** | ask how the team tracks work; record it in `location` + `via` | if no programmatic path exists, keep `PLAN.md` and tell the user what to copy |

## Rules

1. **Never assume the tool or a status name.** Read `project.json:management`; if it is missing, run the
   settings step (`karvey-init --settings`) or ask.
2. **Credentials never in the repo** — `.connections.json` (git-ignored), env vars or a vault.
3. **A failed tracker update is reported** (phase-close gate): the phase does not pretend it closed cleanly.
4. **`PLAN.md` is always a valid fallback** when the tracker is unreachable — say so and keep going.
