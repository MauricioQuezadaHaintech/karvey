# Karvey hooks

Two pieces that keep a session from forgetting who it is and from running past the point where
rotating is cheaper than continuing. **They work for a single agent**; a team (`karvey/rules/team.md`,
optional) only changes where the agent's profile lives.

| File | What it is | How it is installed |
|---|---|---|
| `hooks.json` + `karvey-session-context.sh` | `SessionStart` hook (`startup\|resume\|compact\|clear`): reinjects identity, manifest, board, checklist and handoff; **measures the live repos against `state.json`**; and tells the session to run `/karvey-checkpoint restore` first | **Automatic** with the plugin |
| `karvey-statusline.sh` | Rotation statusline: context, account limits **with the next reset time and time left** (`5h 29% ↻18:05 (1h31m) · 7d 35% ↻Thu 21:20 (2d4h)`; clock in `KARVEY_TZ`, default the system zone), hours, cost, and a "TIME TO ROTATE" warning | **By hand, once** — see below |

## The session hook needs no installation

Plugin hooks **add to** the user's own hooks, they do not replace them. With the plugin installed, the
hook runs on every session start, resume, compact and clear.

It walks up from the session's directory looking for, in order: `docs/spec/team.json`, a legacy
`.ceo-agentes`, or `docs/spec/agent/` (the single-agent profile). **With none of them it prints
nothing and exits 0** — with one exception: inside a Karvey project (`docs/spec/project.json` or
`docs/spec/changes/`) whose team settings (`notifications`, `management`) are missing, it prints one
informational line pointing to `/karvey:karvey-init --settings` (settings only; it creates nothing). A bare
`docs/spec/` folder (OpenAPI, RFCs, studies) is not a Karvey project and stays silent. With a team, the role comes from the directory's name relative to the team
root (at the root itself, the root's own name is looked up in `roles`); anything not listed is `ceo`. The
profile lives in the sibling ops repo (`{ops_repo}/agents/<role>/`) or — when `team.json` sits inside the
repo it names — in `docs/spec/agents/<role>/`. If the profile or the handoff is missing, the hook says so.

**What it does, and what it deliberately does not.** It reinjects the documents *and* measures: for
each repo in `state.json` it compares branch, last commit and uncommitted count against the live tree
and prints `matches` or `DRIFT — branch X -> Y`. Then it tells the session to run
`/karvey-checkpoint restore` **before anything else** when there is an active change, when the state
drifted, or when there is no handoff at all.

**A hook cannot invoke a skill**, so it stops there. Crossing open questions against the decision log,
recreating the scheduled tasks and proposing the next step are the skill's job — the hook's
contribution is that the session starts knowing it must ask for them, and knowing which parts of the
handoff are already suspect.

## The statusline is installed by the user, once

**A plugin cannot declare a statusline** — only the `agent` and `subagentStatusLine` keys are accepted
from a plugin. There is no honest way around it, so the script ships here and the user pastes three
lines into their own `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/plugins/<marketplace>/karvey/<version>/hooks/karvey-statusline.sh",
    "padding": 0
  }
}
```

Adjust the path to where the plugin is installed (or copy the script to `~/.claude/hooks/` and point
at that — it has no dependency on the plugin). It runs **outside the turn, so it costs no model
tokens**. Requires `bash` and `python3`.

Thresholds, by environment variable:

| Variable | Default | Meaning |
|---|---|---|
| `KARVEY_ROTATE_CTX_YELLOW` | `100000` | amber light |
| `KARVEY_ROTATE_CTX_RED` | `150000` | red light + "TIME TO ROTATE" |
| `KARVEY_ROTATE_HOURS` | `8` | session hours before red |

**Where 150k comes from:** measurement, not taste. At 588k of context a turn costs **7×** what it costs
at 80k, and rotating costs ~40k to re-read the handoff — it amortizes in under half a turn.

## Things these scripts learned the hard way

- **A statusline that vanishes is indistinguishable from one that is off.** If the CLI changes the
  stdin format, the script prints the failure instead of nothing, and keeps the last stdin in
  `$TMPDIR/.karvey-statusline-last.<uid>.json` (per user, mode 600) so the change can be seen.
- **`current_usage` changed from an integer to an object.** Both shapes are accepted.
- **Windows + WSL:** the CLI hands over `C:\...` transcript paths that do not exist inside WSL.
  Untranslated, `isfile()` returns False **silently** and the statusline quietly loses half its data.
  The script translates to `/mnt/c/...` and does not split basenames on `/` only.
- **On Windows, writing these scripts through a PowerShell pipe can replace the emoji with `?`
  inside the file** — it installs, runs without error and shows garbage. Copy the file; do not pipe
  it through a console with a legacy codepage, and compare the size afterwards.
- **Check an installer's own evidence from a neutral directory.** A check for "is the hook inert?"
  run from inside a configured project prints a handoff and passes anyway.
