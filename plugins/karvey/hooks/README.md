# Karvey hooks

Two pieces that keep a session from forgetting who it is and from running past the point where
rotating is cheaper than continuing. **Both belong to the OPTIONAL team layer** (`karvey/rules/team.md`)
— read that rule, including "When NOT to use a team", before adopting them.

| File | What it is | How it is installed |
|---|---|---|
| `hooks.json` + `karvey-session-context.sh` | `SessionStart` hook (`startup\|resume\|compact\|clear`): reinjects identity + compact manifest + this agent's handoff | **Automatic** with the plugin |
| `karvey-statusline.sh` | Rotation statusline: context, account limits, hours, cost, and a "TIME TO ROTATE" warning | **By hand, once** — see below |

## The session hook needs no installation

Plugin hooks **add to** the user's own hooks, they do not replace them. With the plugin installed, the
hook runs on every session start. **Without a team configured it prints nothing and exits 0** — on a
single-agent project it is inert, which is the default and the recommended state.

It finds the team by walking up from the session's directory looking for `docs/spec/team.json` (or a
legacy `.ceo-agentes`). The role comes from the directory's name relative to the team root; anything
not listed, and the root itself, is `ceo`.

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
  `$TMPDIR/.karvey-statusline-last.json` so the change can be seen.
- **`current_usage` changed from an integer to an object.** Both shapes are accepted.
- **Windows + WSL:** the CLI hands over `C:\...` transcript paths that do not exist inside WSL.
  Untranslated, `isfile()` returns False **silently** and the statusline quietly loses half its data.
  The script translates to `/mnt/c/...` and does not split basenames on `/` only.
- **On Windows, writing these scripts through a PowerShell pipe can replace the emoji with `?`
  inside the file** — it installs, runs without error and shows garbage. Copy the file; do not pipe
  it through a console with a legacy codepage, and compare the size afterwards.
- **Check an installer's own evidence from a neutral directory.** A check for "is the hook inert?"
  run from inside a configured project prints a handoff and passes anyway.
