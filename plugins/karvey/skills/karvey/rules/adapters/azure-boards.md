# Tracker adapter: Azure Boards

Loaded only when `karvey-config.py resolve management` returns `tool: azure-boards`. The logical operations, states,
natural keys, outbox, work breakdown, cascade and estimation are tool-neutral and live in the management
adapters rule[^r-ma]; this file holds only how Azure Boards does them.

<!-- karvey:generated load-lists:adapter-used-by -->
<!-- /karvey:generated load-lists:adapter-used-by -->

| Operation | Azure Boards | log_time |
|---|---|---|
| session access | `az boards` CLI or REST | — |
| `create_epic` / `create_feature` / `create_task` | work items of type Epic / Feature / Task (per the process template), parent link | — |
| `set_status` | the work item's `State` field (`az boards work-item update --state`) | — |
| `comment` | work item discussion | — |
| dependencies | predecessor / successor links | — |
| `log_time` | the Task's `Completed Work` field | field |

```bash
az boards work-item create --type Task --title "E{n}.F{n}.T{n} [Layer] {Description}" --project "$LOC"
```

- The work item types and states come from the project's process template (Agile, Scrum, CMMI or custom).
- The iteration path (`management.sprints`) is set only when the team declared one.

[^r-ma]: management-adapters.md — the tool-neutral contract; context only, not opened.
