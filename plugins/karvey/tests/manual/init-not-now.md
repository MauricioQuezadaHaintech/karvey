# init: "not now" is persisted; one Epic state; Settings line (REQ-W1-095)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Scratch repo with a `project.json` that has no `notifications` block; Markdown tracking.

## Prompt
`/karvey:karvey-init fixture-07` and, at the notifications question, answer `not now`. Then run
`/karvey:karvey-init fixture-08` in the same repo.

## Expected:
- First run: the final output has a `Settings:` line; `project.json` now records the answer
  (`notifications.channel: "none"` or an explicit deferred marker); the Epic in `PLAN.md` starts in the one
  initial state the skill states for every tool.
- First run: Step 3 does not re-ask fields that `project.json` already has.
- Second run: the notifications question is **not** asked again; the output says how to set them later
  (`/karvey:karvey-init --settings`).

## Evidence
- Both final outputs, `git diff docs/spec/project.json` after the first run, the Epic line of `PLAN.md`,
  and `python3 ~/Dev/karvey/plugins/karvey/scripts/lint-plugin.py --only L-28` (0 errors).
