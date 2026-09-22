# PRD — `team-adapters`: the method adapts to the team's tools

## 1. Executive summary
Karvey hard-coded one team's tooling: QA always notified **Google Chat** through a table in `CLAUDE.md`, and
every status update used **ClickUp** with a team-specific status name (`listo! para pap`). Any other team —
Slack, Teams, Jira, a spreadsheet — hit a step that failed or did not apply. This change turns both into
**team settings asked on first use** and stored in `project.json`, and makes every phase speak in **logical
states** mapped to the team's real ones.

## 2. 🎯 Goal (north star)
A team that installs Karvey answers a short settings block once (notification channel, task-management
tool, its status flow) and from then on **no skill assumes a tool the team does not use**; HainTech's own
flow (Google Chat + ClickUp) keeps working by declaring it, not by being the default.

## 3. Problem and context
- A Claude Code plugin has **no install hook**: nothing can run when the plugin is installed. The earliest
  moment is the first use — the session hook (to nudge) and `karvey-init` (to ask).
- `management` only knew `clickup | markdown`; ~20 files branched on that, and the ClickUp status names were
  literals.
- QA Step 4 read "the known-spaces table" of `CLAUDE.md` — a HainTech convention, not a method rule.

## 4. Scope
- `rules/notifications.md` (new): channels `google-chat | slack | teams | email | webhook | none`, target, how.
- `rules/management-adapters.md` (new): tools `clickup | jira | linear | azure-boards | github-projects |
  spreadsheet | markdown | other`; the logical operations; the 5 logical states and their mapping.
- `project.json`: `notifications` and `management` blocks (`rules/project-config.md`).
- `karvey-init`: a **team settings** step asked when `project.json` lacks them; `--settings` re-runs it.
- Session hook: a one-line nudge in a Karvey project whose settings are missing; still silent elsewhere.
- Every skill/rule that named a tool or a literal status now uses the logical state + adapter.
- Complementary self-contained HTML (`docs/karvey.html`) explaining the method and the plugin map.

## 5. Out of scope
- Shipping API clients for each tool: the adapter says *what* to do and *which* channel (MCP, CLI, REST),
  the session uses what it has.
- Migrating existing HainTech repos' `project.json` (each repo declares its settings on next `init`).

## 6. Acceptance criteria
- No skill mentions Google Chat or `listo! para pap` as behavior; they appear only as examples of values.
- `karvey-init` on a project without settings asks the block; with settings, asks nothing.
- A project with `management: "clickup"` and no status map still works (statuses read from the list,
  mapping confirmed once).
- The session hook stays silent outside Karvey projects.
