# Tracker adapter: Jira

Loaded only when `karvey-config.py resolve management` returns `tool: jira`. The logical operations, states,
natural keys, outbox, work breakdown, cascade and estimation are tool-neutral and live in the management
adapters rule[^r-ma]; this file holds only how Jira does them.

<!-- karvey:generated load-lists:adapter-used-by -->
<!-- /karvey:generated load-lists:adapter-used-by -->

| Operation | Jira | log_time |
|---|---|---|
| session access | Atlassian MCP, the `jira` CLI or REST | — |
| `create_epic` / `create_feature` / `create_task` | issue of type Epic / Feature (or the team's type) / Task, parent link | — |
| `set_status` | a **transition**: look up the transition id that reaches the mapped status, then apply it | — |
| `comment` | issue comment | — |
| dependencies | issue links (`blocks` / `is blocked by`) | — |
| `log_time` | worklog (`POST /issue/{key}/worklog`) | worklog |

Values used in commands come from `karvey-config.py get … --shell`, double-quoted:

```bash
LOC="$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" get management.location --change "{change-id}" --shell)" || exit 1
jira issue list --project "$LOC"
```

- Statuses belong to the project's workflow; a status is reached through a transition, never set directly.
- The sprint (`management.sprints`) is the board's active sprint; never guess one.

[^r-ma]: management-adapters.md — the tool-neutral contract; context only, not opened.
