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
```

**Tracker ids** of a change live in `spec.json:clickup` (historical name, any tool): `epic_id`,
`feature_ids`, `task_ids` (`{"E1.F1.T1": "<id>"}`), `backlog_list_id`. Never read
`backlog_list_id` from `project.json` directly; resolve `location`.

## The 5 logical states

| Logical | Meaning | Example team status | Markdown |
|---|---|---|---|
| `todo` | planned, not started | `To Do` | ⬜ |
| `in_progress` | being worked on | `In Progress` | 🔄 |
| `review` | implemented, awaiting validation | `In Review` | 👀 |
| `done` | validated / released | `Done` | ✅ |
| `blocked` | cannot advance | `Blocked` | ⛔ |

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
| `create_feature(epic, functional area)` | requirements, tasks | a functional area of the change (skip if `hierarchy` has none) |
| `create_task(feature, E{n}.F{n}.T{n}, estimate_min)` | tasks | a 10–30 min AI task (*Estimation* below) |
| `set_status(item, logical_state)` | impl, qa, deploy, archive, phase-close | resolved via `statuses` |
| `comment(item, text)` | phase-close, qa, deploy | factual close comment |
| `cascade(parent)` | phase-close, impl | the one cascade (below) |
| `link(item, url)` | deploy, qa | PR / review document |
| `mirror_backlog(BL-NN)` | iterate, archive | backlog item in the tracker, if the team wants it |
| `log_time(task, actual_min)` | impl | the actual time as the tool's own time object (the `log_time` column below); `none` → the task record's `actual_ai_min` / `actual_review_min` columns. The estimate is never touched |

**Natural keys (find-or-create):** before creating, search for the item by its key — `E{n}`, `E{n}.F{n}`,
`E{n}.F{n}.T{n}`, `E{n}.QA`, `E{n}.DEPLOY`, `F-NN`, `BUG-NN`, `[Deploy] {change-id}@{version}` — and reuse it; store the id in
`spec.json:clickup`. Two items with the same key → stop and ask which is canonical.

**Outbox:** a failed operation is queued, not dropped:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" outbox add {change-id} --op set_status --args '{…}' --key E1.F1.T1 --error "…"`.
The next phase-close retries it. A child is never created under a parent missing in the tracker: queue it with
`--parent-key`.

## One work breakdown (the only statement of it)

The tracker holds **one** hierarchy per change, the same in every tool (REQ-W3-040..042):

- **Epic** `E{n}` = the change. **Feature** `E{n}.F{n}` = a **functional area** of the change (what it delivers —
  never a pipeline phase, never a layer on its own). **Task** `E{n}.F{n}.T{n}` = a 10–30 min unit under exactly one
  Feature.
- **Pipeline phases** (`requirements → … → deploy`) are a **checklist or a field of the Epic**, ticked at each phase
  close — they are never Features.
- **QA and deploy** live under the Epic as the natural keys **`E{n}.QA`** (the QA review item; the fix tasks of a
  review are its children) and **`E{n}.DEPLOY`** (the deploy item; `[Deploy] {change-id}@{version}` is its child) —
  found or created once, never at the root of the list.
- **Parent/child** carries the hierarchy (the tool's own parent link). **Dependencies only between siblings**: tasks
  of one Feature, or Features of one Epic; a cross-area need is a dependency between the two Features.
- A tool **without parent/child** (a flat list, a spreadsheet, some boards) records the parent key in a field or
  label (`parent: E1.F2`) and the skill says so in its report.
- Items in the 4.0 shape (a Feature per phase, QA or deploy items at the root) are **reported, never rewritten**:
  `legacy shape` / `outside the hierarchy` (the phase-close ritual[^r-pc], `karvey-trace.py --wbs`).

## The cascade (the only statement of it)

- A Task reaches `review` when it is implemented; `done` when QA approves (QA moves every Task and Feature of
  the change in `review` to `done`).
- A Feature moves to `review` once every one of its Tasks, across all its layers, is at `review` or later.
- The Epic moves to `review` at impl once every Feature is at `review`; it reaches `done` **only at archive**,
  which first checks that nothing is left in `review` and lists what is.

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

## Adapters (one per tool, loaded alone)

The tool-specific detail — how the session reaches the tool, the operation calls, the `log_time` object and the
tool's quirks — lives in one file per tool under `adapters/`, named after the tool: `clickup`, `jira`,
`linear`, `azure-boards`, `github-projects`, `spreadsheet`, `markdown`. A phase skill lists the adapter
placeholder on its `Load:` line and loads **only** the file of the tool that `resolve management` returns; no skill body carries a
tool's API calls or examples (lint L-58).

| Tool | log_time |
|---|---|
| ClickUp | time entry |
| Jira | worklog |
| Azure Boards | `Completed Work` field |
| Linear, GitHub Projects, Spreadsheet, Markdown | none |
| Other | ask how the team tracks work; record `location` + `via`; no programmatic path → Markdown |

`log_time: none` means the tool has no time object the method writes: the actual goes to the task record's
`actual_ai_min` / `actual_review_min` columns (`PLAN.md`, the spreadsheet row), never over the estimate.

## Rules

1. **Never assume the tool or a status name.** Resolve it; if missing, run `karvey-init --settings` or ask.
2. **Credentials never in the repo** — `.connections.json` (git-ignored), env vars or a vault.
3. **A failed tracker update is reported** and queued in the outbox (phase-close gate).
4. **`PLAN.md` is always a valid fallback** when the tracker is unreachable — say so and keep going.
5. **Subagents never write `project.json`**; settings travel as a reviewed change.

[^r-pc]: phase-close.md — the close ritual; context only, not opened.
