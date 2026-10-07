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
| `UserPromptSubmit` | `karvey-hook.sh prompt` → **approval** | The human's own approval word records a marker and prints `[karvey] approval recorded (<kind>, <scope>, expires hh:mm)`. <!-- guard-case: ap-02-approval-ok --> A production approval is recorded only for the change it names (or the single active change, said in the line); a change held by another local clone is recorded in that clone, named in the line, and two clones holding it record nothing <!-- guard-case: ap-an-01-named-change-of-a-sibling-clone-recorded-there, ap-an-02-two-clones-hold-the-named-change-records-nothing -->; the phrase to type is «aprobado para producción <change-id>» (PR and version optional, the approval binds to the commit passed with `approve … --sha`); a phrase with approval and production words that records nothing prints `[karvey] prod approval NOT recorded: <reason> — type: «<phrase>»`. <!-- guard-case: ap-hf-02-named-change-only-on-a-branch-records-nothing, ap-hf-07-negated-prod-phrase-says-why --> A negation, a question or quoted text records nothing. <!-- guard-case: ap-08-negation-or-question, ap-15-quoted-code-fence --> `confirmo notificacion <code>` records the human's confirmation of a changed notification destination (D-16). <!-- guard-case: nc-01-human-phrase-records-the-confirmation --> | on |
| `PreToolUse` Bash, Edit/Write | **protect-paths** | Blocks any write to the approval markers, the release ledger, the state dir and the plugin root; the agent never creates its own approval. <!-- guard-case: pp-01-touch-marker, pp-07-write-tool-on-marker --> | always on |
| `PreToolUse` Bash | **prod-gate** | Blocks a merge or push into production without a human prod approval in the release ledger. <!-- guard-case: pg1-01-gh-merge-admin-no-approval, pg1-25-git-push-main-no-approval --> With the approval recorded it allows the merge. <!-- guard-case: pg1-02-gh-merge-with-ledger --> The approval counts only with the approval hook's audit line of its marker, for the approved head commit, within 24 h of the OK. <!-- guard-case: pg5-01-ledger-without-the-hook-audit-record, pg5-02-commit-after-the-approval, pg5-06-approval-older-than-24h --> It decides on the repo the command names (`--repo`, a PR URL, a REST URL) and lets a target that is not a Karvey repo pass with a warning line. <!-- guard-case: pg-hf-01-repo-flag-names-a-non-karvey-repo, pg-hf-02-merge-into-integration-of-the-named-repo --> REST completions and branch writes need the same approval; variable-built or inline-script forms are blocked. <!-- guard-case: pg-hf-03-curl-azure-completion-no-approval, pg-hf-06-curl-variable-url-blocks, pg-hf-08-curl-ref-write-of-main-blocks --> | on (`enforcement.prod_gate_hook`) |
| `PreToolUse` Bash | **git-flow** | Blocks commits, merges and pushes on the integration or production branch and manual deploys. <!-- guard-case: gf-01-commit-on-master, gf-02-commit-on-dev, gf-34-manual-deploy-func-publish --> | opt-in (`enforcement.git_flow_hook`) |
| `PreToolUse` Bash, Edit/Write | **plan-gate** | Blocks consequential actions (deleting tracked files, history rewrites, database writes, software changes, PR/merge to production, deploys, infrastructure) without an approved plan; the approval lasts until the plan ends or the human says stop (D-47). <!-- guard-case: pg-15-destructive, d47-03-update-is-gated, d47-05-pip-install-is-gated --> Investigation, scripts and file edits are not gated (see `../skills/karvey/rules/enforcement.md`). With `plan_gate_edits` it also blocks edits. <!-- guard-case: pg-43-edit-without-marker, d47-18-edit-gated-with-plan-gate-edits --> | opt-in (`enforcement.plan_gate_hook`, `plan_gate_edits`) |
| `PreToolUse` Agent/Task | **subagent-prompt** | In a Karvey project, blocks a subagent prompt that lets the subagent write the project settings (`project.json`, a status map) and tells the session to re-send it with the ban line of `management-adapters.md` rule 5. <!-- guard-case: sp-01-rerun-prompt-persist-settings-blocked, sp-02-first-run-prompt-persist-map-blocked --> A prompt that carries the line, or does not touch the settings, is allowed. <!-- guard-case: sp-03-ban-line-present-allowed, sp-04-no-settings-talk-allowed --> | on (fail open) |
| `PostToolUse` Edit/Write | **spec-write**, **pending-sync** | An invalid `spec.json` / `project.json` write is blocked back to the session with the errors. <!-- guard-case: sw-03-enum-violation-qa-approved --> A valid one stays silent. <!-- guard-case: sw-01-valid-spec-silent --> | on |

The switches live in `project.json:enforcement` and count only when the reviewed line agrees
(`../skills/karvey/rules/enforcement.md`). Hooks named elsewhere in older docs (`clickup-sync-guard`,
`standards-guard`) are **not shipped**.

## The session hook

It loads a profile only from the repo the session works in (the git top level of its directory, 3.12.1,
BUG-140): `docs/spec/agent/` in that repo (the single-agent profile), or a team (`docs/spec/team.json`) or
legacy (`.ceo-agentes`) configuration above it that maps the repo, by its exact name, to a role. There is no
default role and no walk above the repo. <!-- guard-case: ss-hf-01-ancestor-folder-profile-not-injected, ss-hf-03-unmapped-repo-no-default-role -->
When the session started in one repo and works in another, or two profiles claim the repo, it injects nothing and prints one line with `/karvey:karvey-checkpoint restore --profile <role|path>`. <!-- guard-case: ss-hf-05-cwd-changed-to-another-repo-ambiguous, ss-hf-06-two-candidates-inject-nothing -->
A handoff whose front matter says `sensitive: true` is shown only in the profile's own repo. The team
profile lives in the sibling ops repo (`{ops_repo}/agents/<role>/`) or, when `team.json` sits inside the repo
it names, in `docs/spec/agents/<role>/`.

Inside a Karvey project whose team settings (`notifications`, `management`) are missing, on `startup` only
it adds one informational line pointing to `/karvey:karvey-init --settings`.
<!-- guard-case: ss-13-empty-notifications-startup-one-line --> On resume, or when the settings are merged on
`origin/{integration}` or `origin/{production}`, it prints nothing. <!-- guard-case: ss-14-empty-notifications-resume-silent, ss-16-settings-only-on-origin-main-silent, ss-24-settings-on-origin-production-not-integration-silent -->

For each repo in `state.json` it compares branch, last commit and uncommitted count with the live tree
(`matches` or `DRIFT — branch X -> Y`) and tells the session to run `/karvey:karvey-checkpoint restore`
first. Commits since the save that touch only the profile's own files (`state.json`, `handoff.md`,
`board.md`, `manifest.md`, `checklist.md`), on a descendant of the recorded commit, are the save itself
and read `matches (…; profile-only commits since the save)` (BUG-22). **A hook cannot invoke a skill**: crossing open questions against the decision log and proposing
the next step stay the skill's job.

## The upgrade offer

After a plugin update, the first `startup` session in a Karvey project compares the installed version with the
clone's seen-version record (`<git-common-dir>/karvey/seen-version`: shared by worktrees, never committed).
When they differ and a step of the upgrade catalogue applies, it prints two lines (each at most `session.offer_line_max` characters): a notice of the plugin saying what the user can do — get an upgrade plan, or decline for this version — and how the session offers it as one question. <!-- guard-case: ss-24-offer-on-version-change, ss-25-offer-absent-record -->
On resume it prints nothing, and it stays silent outside a Karvey project or for a bare `docs/spec/`. <!-- guard-case: ss-26-no-offer-on-resume, ss-27-silent-outside-karvey, ss-28-bare-docs-spec-silent -->
A Karvey project outside git gets no offer and no record either: the answer is kept per clone, and the upgrade needs a branch (unit test `test_karvey_hooks`, F-27).
Once the person has answered ("Not for this version" runs `karvey-upgrade.py seen --decline`; the upgrade skill records the rest), that version stays silent in the clone and its worktrees. <!-- guard-case: ss-29-declined-no-offer, ss-34-worktree-shares-record -->
When no step applies it records the version as seen (`empty`) and prints nothing. <!-- guard-case: ss-30-empty-plan-records-seen -->
The probe has a budget (`session.upgrade_probe_ms` in `../scripts/karvey_lib/defaults.json`); past it the hook prints the offer anyway and records nothing; it also stops waiting for a probe stuck in one call (a watchdog), and the probe never reads a project file above 2 MiB. <!-- guard-case: ss-31-budget-exceeded-offers -->
A step whose check fails still counts as work (the offer is shown). A broken step catalogue, a version that is not a release number or an internal error prints one line `[karvey] upgrade offer unavailable: <reason>` (without python: `python 3 not found`) and the session starts as usual. <!-- guard-case: ss-32-bad-catalogue-one-line, ss-35-degraded-no-python -->
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
