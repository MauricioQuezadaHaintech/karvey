# `--settings` merge semantics (REQ-W1-096; verification of 3.11.2, BUG-01)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Scratch repo with `project.json` containing
  `"notifications": {"channel": "slack", "target": "#dev", "events": ["qa", "deploy", "incident"], "x_custom": 1}`
  and `"management": {"tool": "markdown", "location": "docs/spec/changes/{change-id}/PLAN.md"}`.
- `ls docs/spec/changes/ > "$SCRATCH/changes-before.txt"`.

## Prompt
`/karvey:karvey-init --settings`, and change **only** the channel to `google-chat` with target `spaces/AAAA`.

## Expected:
- Every question is pre-filled with the current value.
- After the run, `notifications.events` is still `["qa", "deploy", "incident"]`, `x_custom` is still `1`, and
  `management` is unchanged; only `channel` and `target` differ.
- The skill prints one summary line and stops: `ls docs/spec/changes/` equals `changes-before.txt` and no
  tracker item exists.

## Evidence
- `git diff docs/spec/project.json`, the `diff` of the two `ls` outputs, and the final line printed.
- The existing automated guard for the entry point: `bash ~/Dev/karvey/plugins/karvey/hooks/tests/test-hooks.sh`
  (case "notice says settings-only (BUG-01 guard)").
