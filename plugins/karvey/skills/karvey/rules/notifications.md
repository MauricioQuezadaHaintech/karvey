# Rule: Notifications — the team's channel, never an assumed one

> Karvey used to notify **one** channel (Google Chat, looked up in a table of the project's `CLAUDE.md`).
> A team on Slack, Teams or e-mail hit a step that failed or did not apply. The channel is now a **team
> setting**, asked once by `karvey-init` and stored in `project.json:notifications`.

## Settings (`project.json:notifications`)

```json
"notifications": {
  "channel": "google-chat | slack | teams | email | webhook | none",
  "target": "{space / #channel / team+channel / address or list / webhook URL reference}",
  "via": "mcp | cli | webhook | api",
  "events": ["qa", "deploy"]
}
```

- **`channel`** — where the team talks. `none` is a valid, explicit answer.
- **`target`** — the concrete destination: a Google Chat space id (`spaces/XXXX`), a Slack channel
  (`#dev-releases`), a Teams team/channel, an e-mail list, or the **name of the secret** that holds a webhook
  URL. **Never write a webhook URL or token in `project.json`** — reference where it lives (`.connections.json`,
  an env var, a key vault), same policy as `clickup-protocol.md`.
- **`via`** — how this session reaches it: an MCP server, a CLI the team uses (e.g. a Workspace CLI, `slack`,
  `az`), an incoming webhook (`curl`), or the tool's REST API. The skill uses what is actually available and
  **says so if it is not**.
- **`events`** — which moments notify. Default `["qa", "deploy"]`.

## Who notifies, and what

| Event | Skill | Content |
|---|---|---|
| `qa` | `karvey-qa` (Step 4) | change-id, source → target, findings by severity, manual-testing areas, review document |
| `deploy` | `karvey-deploy` (final output) | repos + versions, DEV/PROD state, canary result, branches cleaned |
| `incident` (opt-in) | `karvey-iterate` | a `BUG-NN` reaching `DIAGNOSTICADO` or `REABIERTO` |

## Message format per channel

Write the same content, in the channel's own markup — do not send Markdown where it does not render:

- **Google Chat:** `*bold*`, `_italic_`, `` `code` ``, fenced blocks; no Markdown tables or `#` headers.
- **Slack:** mrkdwn — `*bold*`, `_italic_`, `` `code` ``, `>` quotes; tables as a code block.
- **Teams:** Markdown subset or an Adaptive Card when posting through a webhook.
- **E-mail:** plain HTML; subject `[Karvey] {event} — {change-id}`.
- **Webhook (generic):** JSON `{"event","change_id","summary","severity_counts","link"}`.

## Rules

1. **Unset or `none` → skip and say it.** The skill's output shows `Notification: skipped (channel none)`
   or `(not configured — run /karvey:karvey-init --settings)`. Never invent a destination.
2. **Never read destinations from `CLAUDE.md` tables** or any file other than `project.json` (+ the secret it
   references). A team's private address book is not method configuration.
3. **A failed send is reported, not swallowed** — the phase still closes, and the output says the
   notification failed and why.
4. **No secrets in the message** and none in the repo.
