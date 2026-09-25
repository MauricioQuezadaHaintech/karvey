# Karvey hooks

What the plugin runs on its own, and the statusline the user installs once. **They work for a single
agent**; a team (`../skills/karvey/rules/team.md`, optional) only changes where the agent's profile lives.
Every behaviour below is pinned by a guard-table case (`../tests/hooks/tables/*.json`), cited next to it.

**Requirements:** `bash` and **python ≥ 3.9**. The dispatcher `karvey-hook.sh` finds `python3`, then
`python` (major 3), then `py -3`. Without python it falls back to a bash-only classifier: each guard keeps
its fail mode (closed guards stay closed, open ones let the call through).

## What ships

Plugin hooks **add to** the user's own hooks; there is no installation step. `hooks.json` declares them:

| Event | Hook | Behaviour | Default |
|---|---|---|---|
| `SessionStart` | `karvey-session-context.sh startup\|resume` | Reinjects identity, manifest (compact XOR full), board, checklist and handoff, and measures the live repos against `state.json`. Outside a Karvey project or agent profile it prints nothing. <!-- guard-case: ss-20-non-karvey-dir-silent --> | on |
| `UserPromptSubmit` | `karvey-hook.sh prompt` → **approval** | The human's own approval word records a marker and prints `[karvey] approval recorded (<kind>, <scope>, expires hh:mm)`. <!-- guard-case: ap-02-approval-ok --> A negation, a question or quoted text records nothing. <!-- guard-case: ap-08-negation-or-question, ap-15-quoted-code-fence --> `confirmo notificacion <code>` records the human's confirmation of a changed notification destination (D-16). <!-- guard-case: nc-01-human-phrase-records-the-confirmation --> | on |
| `PreToolUse` Bash, Edit/Write | **protect-paths** | Blocks any write to the approval markers, the release ledger, the state dir and the plugin root; the agent never creates its own approval. <!-- guard-case: pp-01-touch-marker, pp-07-write-tool-on-marker --> | always on |
| `PreToolUse` Bash | **prod-gate** | Blocks a merge or push into production without a human prod approval in the release ledger. <!-- guard-case: pg1-01-gh-merge-admin-no-approval, pg1-25-git-push-main-no-approval --> With the approval recorded it allows the merge. <!-- guard-case: pg1-02-gh-merge-with-ledger --> | on (`enforcement.prod_gate_hook`) |
| `PreToolUse` Bash | **git-flow** | Blocks commits, merges and pushes on the integration or production branch and manual deploys. <!-- guard-case: gf-01-commit-on-master, gf-02-commit-on-dev, gf-34-manual-deploy-func-publish --> | opt-in (`enforcement.git_flow_hook`) |
| `PreToolUse` Bash, Edit/Write | **plan-gate** | Blocks writes and destructive commands without a fresh human approval marker. <!-- guard-case: pg-09-write, pg-15-destructive, pg-43-edit-without-marker --> | opt-in (`enforcement.plan_gate_hook`) |
| `PostToolUse` Edit/Write | **spec-write**, **pending-sync** | An invalid `spec.json` / `project.json` write is blocked back to the session with the errors. <!-- guard-case: sw-03-enum-violation-qa-approved --> A valid one stays silent. <!-- guard-case: sw-01-valid-spec-silent --> | on |

The switches live in `project.json:enforcement` and count only when the reviewed line agrees
(`../skills/karvey/rules/enforcement.md`). Hooks named elsewhere in older docs (`clickup-sync-guard`,
`standards-guard`) are **not shipped**.

## The session hook

It walks up from the session's directory looking for `docs/spec/team.json`, a legacy `.ceo-agentes`, or
`docs/spec/agent/` (the single-agent profile). With a team, the role comes from the directory's name
relative to the team root; anything not listed is `ceo`. The profile lives in the sibling ops repo
(`{ops_repo}/agents/<role>/`) or, when `team.json` sits inside the repo it names, in
`docs/spec/agents/<role>/`.

Inside a Karvey project whose team settings (`notifications`, `management`) are missing, on `startup` only
it adds one informational line pointing to `/karvey:karvey-init --settings`.
<!-- guard-case: ss-13-empty-notifications-startup-one-line --> On resume, or when the settings are merged on
`origin/{integration}`, it prints nothing. <!-- guard-case: ss-14-empty-notifications-resume-silent, ss-16-settings-only-on-origin-main-silent -->

For each repo in `state.json` it compares branch, last commit and uncommitted count with the live tree
(`matches` or `DRIFT — branch X -> Y`) and tells the session to run `/karvey:karvey-checkpoint restore`
first. Commits since the save that touch only the profile's own files (`state.json`, `handoff.md`,
`board.md`, `manifest.md`, `checklist.md`), on a descendant of the recorded commit, are the save itself
and read `matches (…; profile-only commits since the save)` (BUG-22). **A hook cannot invoke a skill**: crossing open questions against the decision log and proposing
the next step stay the skill's job.

## The upgrade offer

After a plugin update, the first `startup` session in a Karvey project compares the installed version with the
clone's seen-version record (`<git-common-dir>/karvey/seen-version`: shared by worktrees, never committed).
When they differ and a step of the upgrade catalogue applies, it prints two lines (each at most `session.offer_line_max` characters) asking the session to put one question to the person. <!-- guard-case: ss-24-offer-on-version-change, ss-25-offer-absent-record -->
On resume it prints nothing, and it stays silent outside a Karvey project or for a bare `docs/spec/`. <!-- guard-case: ss-26-no-offer-on-resume, ss-27-silent-outside-karvey, ss-28-bare-docs-spec-silent -->
Once the person has answered ("Not for this version" runs `karvey-upgrade.py seen --decline`; the upgrade skill records the rest), that version stays silent in the clone and its worktrees. <!-- guard-case: ss-29-declined-no-offer, ss-34-worktree-shares-record -->
When no step applies it records the version as seen (`empty`) and prints nothing. <!-- guard-case: ss-30-empty-plan-records-seen -->
The probe has a budget (`session.upgrade_probe_ms` in `../scripts/karvey_lib/defaults.json`); past it the hook prints the offer anyway and records nothing. <!-- guard-case: ss-31-budget-exceeded-offers -->
A broken step catalogue, a version that is not a release number or any error prints one line `[karvey] upgrade offer unavailable: <reason>` (without python: `python 3 not found`) and the session starts as usual. <!-- guard-case: ss-32-bad-catalogue-one-line, ss-35-degraded-no-python -->
The offer lines are separate from the board and the handoff, whose bounds do not change. <!-- guard-case: ss-33-bounds-with-offer -->
An unanswered offer is not recorded, so it comes back next session. The hook never fetches and never writes a
project file; the plan and every write belong to `../scripts/karvey-upgrade.py` and the `/karvey:karvey-upgrade`
skill.

## The statusline is installed by the user, once

**A plugin cannot declare a statusline.** The script ships here and the user adds to
`~/.claude/settings.json` this **stable** command, which runs the newest installed Karvey, so a plugin update
never breaks it (a path with a version in it goes stale at the next update; the upgrade step
`statusline-launcher` detects it):

```json
{
  "statusLine": {
    "type": "command",
    "padding": 0,
    "command": "bash -c 'f=$(ls -1dt \"$HOME\"/.claude/plugins/cache/*/karvey/*/hooks/karvey-statusline.sh 2>/dev/null | head -1); [ -n \"$f\" ] && exec bash \"$f\"'"
  }
}
```

It runs outside the turn (no model tokens) and shows context, account limits with the next reset
(`5h 29% ↻18:05 (1h31m) · 7d 35% ↻Thu 21:20 (2d4h)`, clock in `KARVEY_TZ`), hours, cost and a
"TIME TO ROTATE" warning.

| Variable | Default | Meaning |
|---|---|---|
| `KARVEY_ROTATE_CTX_YELLOW_PCT` | `context_pct.yellow` in `../scripts/karvey_lib/defaults.json` (D-18) | amber light, percent of the context window |
| `KARVEY_ROTATE_CTX_RED_PCT` | `context_pct.red` in `../scripts/karvey_lib/defaults.json` (D-18) | red light + "TIME TO ROTATE" |
| `KARVEY_ROTATE_CTX_YELLOW` · `KARVEY_ROTATE_CTX_RED` | `context_tokens` in `../scripts/karvey_lib/defaults.json` | token thresholds, used only when the window size is unknown |
| `KARVEY_ROTATE_HOURS` | `rotation_hours` in `../scripts/karvey_lib/defaults.json` (D-06) | session hours before red |

**Why a context threshold:** a percentage scales with the window (200k or 1M). A turn at 588k of context costs **7×** one at 80k, and rotating costs ~40k to
re-read the handoff.

## Lessons kept in the scripts

- A statusline that vanishes looks like one that is off: on a stdin it cannot read, the script shows
  `karvey statusline down` and keeps the last stdin in `$TMPDIR/.karvey-statusline-last.<uid>.json`
  (per user, mode 600).
- `current_usage` changed from an integer to an object; both shapes are accepted.
- Windows + WSL: `C:\...` transcript paths are translated to `/mnt/c/...`.
- Writing these scripts through a PowerShell pipe can replace the emoji with `?`: copy the file and compare
  its size.
- Check an installer's evidence from a neutral directory, never from inside a configured project.
