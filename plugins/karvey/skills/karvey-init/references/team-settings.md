# Init reference: team settings (first use, or `--settings`)

Loaded by `karvey-init` only when `project.json` lacks `notifications` or `management`, or with `--settings`.
The settings are asked once, because a plugin cannot run anything at install time.

## Ask the settings

Ask with `AskUserQuestion`, one block at a time, with examples — never assume the answer:

1. **Notifications** (the notifications rule[^r-notifications]): `Google Chat` · `Slack` · `Microsoft Teams` ·
   `E-mail` · `Webhook` · `None` · `Not now`. Then the **target** (space id, `#channel`, list, or the *name*
   of the secret holding a webhook — never a URL), **via** (`mcp` · `cli` · `webhook` · `api`, checking what
   is available) and **events** (default `qa`, `deploy`). **Not now** → write `notifications.deferred: true`
   and say how to set it later (`/karvey-init --settings`); the question is not asked again.
   If the project's `CLAUDE.md` holds a destination table (pre-3.10 setups), offer those values as the
   pre-filled answer for the human to confirm; nothing is read from `CLAUDE.md` after that.
2. **Task management** (the management adapters rule, on the skill's `Load:` line): `ClickUp` · `Jira` · `Linear` ·
   `Azure Boards` · `GitHub Projects` · `Spreadsheet` · `Markdown (PLAN.md)` · `Other`, then **location** and **via**.
3. **Status flow**: map the team's real statuses to `todo · in_progress · review · done · blocked`. For a
   tracker, read the statuses from the tool and propose the map; the user confirms. For `Markdown` the
   markers are fixed: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked · 🙋 awaiting-human (a blocked qualifier)`.

4. **Branch mode** (`branch_flow.mode`): `trunk (recommended)` — integration = production, one PR per change ·
   `env-branches` — an integration branch deployed to its own environment. Offer trunk first; keep an existing
   `env-branches` project as it is unless the team asks to move.

Credentials go to `.connections.json` (git-ignored) or the team's vault — never into `project.json`.

## Write the settings as a reviewed change

`project.json` changes travel on a docs branch and take effect **after merge** (the hooks read the reviewed
line on `origin/{production}`). Never commit it on the integration or production branch:

```bash
I="$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" get branch_flow.integration --shell)"
git switch -c "docs/karvey-settings" "origin/$I"   # skip if already on a feature/docs branch
```

Print one line: `Settings: notifications slack #dev-releases (webhook) · management jira PAY (5 states mapped)`
(or `notifications deferred`).

[^r-notifications]: ../../karvey/rules/notifications.md — context only, not opened.
