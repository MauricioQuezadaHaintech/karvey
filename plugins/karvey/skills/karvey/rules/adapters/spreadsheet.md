# Tracker adapter: Spreadsheet

Loaded only when `karvey-config.py resolve management` returns `tool: spreadsheet`. The logical operations, states,
natural keys, outbox, work breakdown, cascade and estimation are tool-neutral and live in the management
adapters rule[^r-ma]; this file holds only how Spreadsheet does them.

<!-- karvey:generated load-lists:adapter-used-by -->
<!-- /karvey:generated load-lists:adapter-used-by -->

| Operation | Spreadsheet | log_time |
|---|---|---|
| session access | a CSV file under `docs/spec/`, or a sheet through its CLI or MCP | — |
| `create_*` | a row keyed by its natural key | — |
| `set_status` | the `status` column | — |
| `comment` | a `notes` column or a history row | — |
| dependencies | a `depends_on` column (keys, comma-separated) | — |
| `log_time` | none: `actual_ai_min` / `actual_review_min` columns | none |

Row: `id, level, title, layer, estimate_min, actual_ai_min, actual_review_min, status, updated_at, link` (plus
`parent` when the sheet is flat, and `depends_on`). The estimate column is written once and never overwritten.

[^r-ma]: management-adapters.md — the tool-neutral contract; context only, not opened.
