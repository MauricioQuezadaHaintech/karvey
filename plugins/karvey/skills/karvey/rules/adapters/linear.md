# Tracker adapter: Linear

Loaded only when `karvey-config.py resolve management` returns `tool: linear`. The logical operations, states,
natural keys, outbox, work breakdown, cascade and estimation are tool-neutral and live in the management
adapters rule[^r-ma]; this file holds only how Linear does them.

<!-- karvey:generated load-lists:adapter-used-by -->
<!-- /karvey:generated load-lists:adapter-used-by -->

| Operation | Linear | log_time |
|---|---|---|
| session access | Linear MCP or the GraphQL API | — |
| `create_epic` | a project (or a parent issue) | — |
| `create_feature` | a sub-issue or a project milestone | — |
| `create_task` | an issue under the Feature | — |
| `set_status` | the team's workflow state (`workflowStates` of the team) | — |
| dependencies | issue relations (`blocks` / `blocked by`) | — |
| `log_time` | none: the actual goes to the task record's columns | none |

- Workflow states are per team: resolve the state id from the team named in `location`.
- The cycle (`management.sprints`) is the team's active cycle when the team uses cycles.

[^r-ma]: management-adapters.md — the tool-neutral contract; context only, not opened.
