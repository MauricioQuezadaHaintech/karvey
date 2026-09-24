# impl selects and resumes in logical states (REQ-W1-085, BUG-05)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Scratch repo with Markdown tracking. A change `fixture-05` at phase `impl` whose `PLAN.md` has
  `E1.F1.T1 [DB]` and `E1.F1.T2 [DB]` at `👀 review`, `E1.F2.T1 [Backend]` (depends on both) at `⬜ todo`,
  and `E1.F2.T2 [Backend]` at `⬜ todo`.
- Second variant: set `E1.F2.T1` to `🔄 in_progress` in `PLAN.md` (an orphan from a dead session) and, with a
  tracker configured, leave the same task at `todo` in the tracker.

## Prompt
Variant A: `/karvey:karvey-impl fixture-05`
Variant B: `/karvey:karvey-impl fixture-05` (tracker configured, `resolve management` reports `external: true`)

## Expected:
- A: the agent says which source it reads task state from (`PLAN.md`), treats the `[DB]` tasks at
  `👀 review` as satisfied dependencies, and starts `E1.F2.T1 [Backend]`. It does **not** wait for the `[DB]`
  tasks to reach `done`.
- B: the agent declares the tracker as its source, reports the drift (`E1.F2.T1` is `in_progress` in `PLAN.md`
  and `todo` in the tracker) and resumes from the tracker's state without silently reconciling `PLAN.md`.

## Evidence
- The transcript lines where the agent names its source and picks the task.
- `git diff PLAN.md` after the first task starts.
