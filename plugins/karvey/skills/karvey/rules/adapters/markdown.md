# Tracker adapter: Markdown (`PLAN.md`)

Loaded only when `karvey-config.py resolve management` returns `tool: markdown`. The logical operations, states,
natural keys, outbox, work breakdown, cascade and estimation are tool-neutral and live in the management
adapters rule[^r-ma]; this file holds only how Markdown (`PLAN.md`) does them.

<!-- karvey:generated load-lists:adapter-used-by -->
<!-- /karvey:generated load-lists:adapter-used-by -->

The fallback tracker: `PLAN.md` in the change directory. `external: false`.

| Operation | Markdown | log_time |
|---|---|---|
| `create_epic` | the `# Plan: {change-id}` header and the Epic section | — |
| `create_feature` / `create_task` | a Feature heading and a task line `E{n}.F{n}.T{n} [Layer] …` with its estimate | — |
| `set_status` | the marker of the task's row in *Task status* | — |
| `comment` | a row of the *History* table | — |
| dependencies | `(depends E1.F1.T1)` after the task line | — |
| `log_time` | none: the `actual_ai_min` / `actual_review_min` columns | none |

Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked · 🙋 awaiting-human` (🙋 next to ⛔ for a
`[human]` task). A row is found by its task id; never add a second row for it. The estimate column is written
once by `karvey-tasks` and never edited.

[^r-ma]: management-adapters.md — the tool-neutral contract; context only, not opened.
