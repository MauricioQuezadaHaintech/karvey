# Rule: Notifications — the team's channel, never an assumed one

> Karvey used to notify **one** channel (Google Chat, looked up in a table of the project's `CLAUDE.md`).
> A team on Slack, Teams or e-mail hit a step that failed or did not apply. The channel is now a **team
> setting**, asked once by `karvey-init` and stored in `project.json:notifications`.

## Settings (`project.json:notifications`)

```json
"notifications": {
  "channel": "google-chat | slack | teams | email | webhook | none",
  "target": "{space id / #channel / team+channel / address or list / name of the secret holding a webhook}",
  "via": "mcp | cli | webhook | api",
  "events": ["qa", "deploy"],
  "qa_every_run": false,
  "detail": "counts",
  "deferred": false
}
```

- **`channel`** — where the team talks. `none` is a valid, explicit answer.
- **`target`** — the concrete destination: a Google Chat space (`spaces/XXXX`), a Slack channel
  (`#dev-releases`), a Teams team/channel, an e-mail list, or the **name of the secret** that holds a webhook
  URL. A value containing `://` is refused: URLs and tokens never live in `project.json`
  (`.connections.json`, an env var or a vault, as in `clickup-protocol.md`).
- **`via`** — how this session reaches it (MCP server, the team's CLI, an incoming webhook, REST). The skill
  uses what is available and **says so if it is not**.
- **`events`** — which moments notify. Default `["qa", "deploy"]`; also `incident` and the "your turn" events
  `approval_requested`, `awaiting_human`, `blocked`.
- **`detail`** — `counts` (default: severity counts, ids and the link) or `full` (the findings text too).
- **`deferred`** — `true` records a "not now" at init, so the question is not repeated; set it later with
  `/karvey:karvey-init --settings`.

## Before every send

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" notify-check --json
```

Exit `0`: the destination is the one the human last confirmed — send. Exit `10`: it changed (or was never
confirmed) — show the new and previous destination and ask the human to confirm it **by typing** the phrase
the command prints, `confirmo notificacion <code>` (or `confirm notification <code>`), where `<code>` is the
first 8 hex characters of the destination's hash. The approval hook records that confirmation for this project
and exactly that destination, with the approval-marker TTL (`plan_marker_ttl_min`, `karvey_lib/defaults.json`).
Then run `notify-check --confirm` and send. `--confirm` counts only against that confirmation (D-16): without
it — the agent alone, a confirmation of another destination or project, or an expired one — it records nothing
and exits `10` again with the phrase to type. The confirmation is used once; the agent can never write it
(protect-paths). The command also validates the target (§3.1 patterns); an invalid target is reported, never
sent to.

## Who notifies, and what

| Event | Skill | Content |
|---|---|---|
| `qa` | `karvey-qa` | change-id, source → target, findings by severity, manual-testing areas, review document |
| `deploy` | `karvey-deploy` (final output) | repos + versions, DEV/PROD state, canary result, branches cleaned |
| `incident` (opt-in) | `karvey-iterate` | a `BUG-NN` reaching `DIAGNOSTICADO` or `REABIERTO` |
| `approval_requested` (opt-in) | the phase asking a gate question | change, gate, what is expected — to the **approver** |
| `awaiting_human` (opt-in) | `karvey-impl` (a `[human]` task) | change, task, command to run — to the **executor** |
| `blocked` (opt-in) | the phase that blocks (a judge verdict in blocking mode included) | change, item, the verdict line — to whoever unblocks (the **executor**) |

### "Your turn" events — the person who must act

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" resolve notifications --event approval_requested \
  --change "{change-id}" --item "{gate or task}" [--verdict "{judge verdict line}"] [--run-id "{run id}"] --json
```

The destination is the `project.json:stakeholders` entry of the acting role (a change may override it in its
`spec.json`): `approver` for `approval_requested`, `executor` for `awaiting_human` and `blocked`. Without one it is
the team destination and the payload says `no approver declared` / `no executor declared`. Send the printed
payload as it is; it names the change, the item and what is expected, with a run id and a timestamp.

## Message format per channel

Write the same content, in the channel's own markup — do not send Markdown where it does not render:

- **Google Chat:** `*bold*`, `_italic_`, `` `code` ``, fenced blocks; no Markdown tables or `#` headers.
- **Slack:** mrkdwn — `*bold*`, `_italic_`, `` `code` ``, `>` quotes; tables as a code block.
- **Teams:** Markdown subset or an Adaptive Card when posting through a webhook.
- **E-mail:** plain HTML; subject `[Karvey] {event} — {change-id}`.
- **Webhook (generic):** JSON `{"event","change_id","summary","severity_counts","link"}`.

## Rules

1. **Unset or `none` → skip and say it.** The output shows `Notification: skipped (channel none)` or
   `(not configured — run /karvey:karvey-init --settings)`. Never invent a destination.
2. **Destinations come only from `project.json`** (+ the secret it references), never from `CLAUDE.md`
   tables or other files. A project that kept them in `CLAUDE.md` moves them with `karvey-init --settings`,
   which offers the values it finds there as a migration aid for the human to confirm.
3. **A failed send is reported, not swallowed** — the phase still closes, and the output says why.
4. **No secrets in the message** and none in the repo.
