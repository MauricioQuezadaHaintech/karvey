# Rule: Management adapters — the team's tracker and its status flow

> The tool and its status flow are **team settings**, asked once by `karvey-init` and stored in
> `project.json:management` (schema: `${CLAUDE_PLUGIN_ROOT}/schemas/project.schema.json`). Phase skills speak
> in **logical operations and logical states**; this rule maps them to each tool.

## Settings (`project.json:management`)

```json
"management": {
  "tool": "clickup | jira | linear | azure-boards | github-projects | spreadsheet | markdown | other",
  "location": "{ClickUp list id | Jira project key | Linear team | ADO project/area | GitHub project number | spreadsheet path under docs/spec/}",
  "statuses": {"todo": "…", "in_progress": "…", "review": "…", "done": "…", "blocked": null},
  "sprints": "{optional: folder, iteration or cycle}",
  "hierarchy": "epic>feature>task",
  "via": "mcp | cli | api | file"
}
```

- `none` is a legacy alias of `markdown` (accepted with a warning). The legacy string shape
  (`"management": "clickup"`) is still read; `karvey-state.py validate --fix` migrates it.
- **Per-level or per-list maps:** `statuses` may be `{"by_level": {"task": {…}, "feature": {…}}}` or
  `{"by_list": {"<list>": {…}}}`. A logical state the tracker cannot represent is `null`: keep the tracker
  status, add a comment, record the state in `PLAN.md`.
- `sprints` absent → work is filed in `location`; never guess a sprint.

## Resolution order (one, cited by every skill)

1. The change's `spec.json:management` override `{tool, location, statuses, sprints}`.
2. `project.json:management` (working copy, then `origin/{integration}` before declaring it missing).

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" resolve management --change "{change-id}" --json
```

The result carries `external` (false for `markdown`/`none`): that is the one "is there a tracker" test —
never compare the tool name by hand. A value used in a command goes through `get --shell` and is
double-quoted:

```bash
LOC="$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" get management.location --change "{change-id}" --shell)" || exit 1
jira issue list --project "$LOC"
```

**Tracker ids** of a change live in `spec.json:clickup` (historical name, any tool): `epic_id`,
`feature_ids`, `task_ids` (`{"E1.F1.T1": "<id>"}`), `backlog_list_id`. Never read
`backlog_list_id` from `project.json` directly; resolve `location`.

## The 5 logical states

| Logical | Meaning | Example — ClickUp | Example — Jira | Markdown |
|---|---|---|---|---|
| `todo` | planned, not started | `to do` | `To Do` | ⬜ |
| `in_progress` | being worked on | `in progress` | `In Progress` | 🔄 |
| `review` | implemented, awaiting validation | `listo! para pap` | `In Review` | 👀 |
| `done` | validated / released | `complete` | `Done` | ✅ |
| `blocked` | cannot advance | `blocked` | `Blocked` | ⛔ |

**`awaiting-human` (🙋)** is a qualifier, not a sixth state: a `[human]` task waiting for its executor is
`blocked` plus the `awaiting-human` tag (🙋 next to ⛔ in `PLAN.md`); only its dependents are held.

Skills write `status → review`, never a literal name. The examples are values a team declares, not defaults.

### Missing map (the one clause)
Before the first status change of a run: resolve tool and location (above). IF `location` is missing, ask for
it and change no status meanwhile. IF `statuses` (or one entry) is missing, read the real statuses of that
location from the tool, propose the mapping, confirm it with the human and persist it on a feature or docs
branch (it takes effect after merge). IF no human can answer (subagent, headless), persist nothing, use
`PLAN.md` for that run and report "status map unresolved — no human". A mapped status that disappeared is
re-mapped alone. The method never creates or edits the team's workflow states. `karvey-tasks` resolves the map
as a precondition of its gate.

## Logical operations

| Operation | Used by | What it means |
|---|---|---|
| `create_epic(change)` | init | the unit that represents the change |
| `create_feature(epic, capability/layer)` | requirements, tasks | grouping level (skip if `hierarchy` has none) |
| `create_task(feature, E{n}.F{n}.T{n}, estimate_min)` | tasks | a 10–30 min AI task (`clickup-protocol.md` → Estimation) |
| `set_status(item, logical_state)` | impl, qa, deploy, archive, phase-close | resolved via `statuses` |
| `comment(item, text)` | phase-close, qa, deploy | factual close comment |
| `cascade(parent)` | phase-close, impl | the one cascade (below) |
| `link(item, url)` | deploy, qa | PR / review document |
| `mirror_backlog(BL-NN)` | iterate, archive | backlog item in the tracker, if the team wants it |
| `log_time(task, actual_min)` | impl | the actual time as the tool's own time object (the `log_time` column below); `none` → the task record's `actual_ai_min` / `actual_review_min` columns. The estimate is never touched |

**Natural keys (find-or-create):** before creating, search for the item by its key — `E{n}`, `E{n}.F{n}`,
`E{n}.F{n}.T{n}`, `F-NN`, `BUG-NN`, `[Deploy] {change-id}@{version}` — and reuse it; store the id in
`spec.json:clickup`. Two items with the same key → stop and ask which is canonical.

**Outbox:** a failed operation is queued, not dropped:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" outbox add {change-id} --op set_status --args '{…}' --key E1.F1.T1 --error "…"`.
The next phase-close retries it. A child is never created under a parent missing in the tracker: queue it with
`--parent-key`.

## The cascade (the only statement of it)

- A Task reaches `review` when it is implemented; `done` when QA approves (QA moves every Task and Feature of
  the change in `review` to `done`).
- A Feature moves to `review` once every one of its Tasks, across all its layers, is at `review` or later.
- The Epic moves to `review` at impl once every Feature is at `review`; it reaches `done` **only at archive**,
  which first checks that nothing is left in `review` and lists what is.

## Adapters

| Tool | How the session does it | log_time | Notes |
|---|---|---|---|
| **ClickUp** | ClickUp MCP or REST — `clickup-protocol.md` | time entry (`POST /task/{id}/time`) | `time_estimate` only via REST |
| **Jira** | Atlassian MCP, `jira` CLI or REST | worklog (`POST /issue/{key}/worklog`) | status change = **transition** (look up its id) |
| **Linear** | Linear MCP or GraphQL | none | states are per team (`workflowStates`) |
| **Azure Boards** | `az boards work-item create/update` | `Completed Work` field of the Task | Epic/Feature/Task per process template |
| **GitHub Projects** | `gh project item-add/item-edit`, issues | none | status is a single-select field |
| **Spreadsheet** | a file under `docs/spec/` or a Sheet via CLI/MCP | none | row: `id, level, title, layer, estimate_min, actual_ai_min, actual_review_min, status, updated_at, link` |
| **Markdown** | `PLAN.md` in the change directory | none | the fallback; legend in the states table |
| **Other** | ask how the team tracks work; record `location` + `via` | none unless the team names one | no programmatic path → `PLAN.md` |

`log_time: none` means the tool has no time object the method writes: the actual goes to the task record's
`actual_ai_min` / `actual_review_min` columns (`PLAN.md`, the spreadsheet row), never over the estimate.

## Rules

1. **Never assume the tool or a status name.** Resolve it; if missing, run `karvey-init --settings` or ask.
2. **Credentials never in the repo** — `.connections.json` (git-ignored), env vars or a vault.
3. **A failed tracker update is reported** and queued in the outbox (phase-close gate).
4. **`PLAN.md` is always a valid fallback** when the tracker is unreachable — say so and keep going.
5. **Subagents never write `project.json`**; settings travel as a reviewed change.
