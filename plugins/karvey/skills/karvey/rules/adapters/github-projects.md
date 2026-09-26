# Tracker adapter: GitHub Projects

Loaded only when `karvey-config.py resolve management` returns `tool: github-projects`. The logical operations, states,
natural keys, outbox, work breakdown, cascade and estimation are tool-neutral and live in the management
adapters rule[^r-ma]; this file holds only how GitHub Projects does them.

<!-- karvey:generated load-lists:adapter-used-by -->
<!-- /karvey:generated load-lists:adapter-used-by -->

| Operation | GitHub Projects | log_time |
|---|---|---|
| session access | `gh` CLI (`gh project`, `gh issue`) or GraphQL | — |
| `create_epic` / `create_feature` / `create_task` | issues added to the project; parent through sub-issues or a `parent: E1.F2` field | — |
| `set_status` | the project's single-select Status field (`gh project item-edit`) | — |
| `comment` | issue comment | — |
| dependencies | "blocked by" issue relations, or a task-list reference in the body | — |
| `log_time` | none: the actual goes to the task record's columns | none |

```bash
gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" --url "$ISSUE_URL"
```

- Status is a single-select field of the project, not the issue state; closing the issue is `done` only when the
  team maps it so.

[^r-ma]: management-adapters.md — the tool-neutral contract; context only, not opened.
