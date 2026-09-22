# Requirements (EARS) — `team-adapters`

Traced to `prd.md`.

## Settings on first use (PRD §3, §4)
- **REQ-ADP-001** — WHEN `karvey-init` runs AND `project.json` lacks `notifications` or `management`, THE
  skill SHALL ask the team-settings block and write the answers to `project.json`.
- **REQ-ADP-002** — WHERE `project.json` already holds both blocks, THE skill SHALL NOT ask them again,
  unless invoked with `--settings`.
- **REQ-ADP-003** — WHEN a session starts in a project that has `docs/spec/` AND lacks those settings, THE
  session hook SHALL print a single line pointing to `/karvey:karvey-init --settings`; WHERE the project has
  no `docs/spec/`, THE hook SHALL print nothing and exit 0.

## Notifications (PRD §4)
- **REQ-ADP-010** — THE notification channel SHALL be one of `google-chat | slack | teams | email |
  webhook | none`, with a `target` and a `via` (`mcp | cli | webhook | api`).
- **REQ-ADP-011** — WHEN a skill notifies (QA summary, deploy result), THE skill SHALL use the configured
  channel; IF the channel is `none` or unset, THEN it SHALL skip the notification and SAY so in its output.
- **REQ-ADP-012** — THE method SHALL NOT read notification targets from a project's `CLAUDE.md` tables.

## Task management (PRD §4)
- **REQ-ADP-020** — THE management tool SHALL be one of `clickup | jira | linear | azure-boards |
  github-projects | spreadsheet | markdown | other`.
- **REQ-ADP-021** — Phase skills SHALL express state changes as the logical states `todo | in_progress |
  review | done | blocked`, resolved through `project.json:management.statuses`.
- **REQ-ADP-022** — IF the status map is missing for a tracker tool, THEN the skill SHALL read the real
  statuses from the tool (or ask), propose the mapping, confirm it once with the user and persist it.
- **REQ-ADP-023** — `spec.json:management` SHALL keep naming the tool, so existing changes with
  `"clickup"` or `"markdown"` remain valid.

## Documentation (PRD §4)
- **REQ-ADP-030** — THE repo SHALL ship a self-contained `docs/karvey.html` (no external requests)
  explaining the method, the meaning and origin of the name, and a map of every skill, phase, rule, hook
  and artifact; linked from the README.
