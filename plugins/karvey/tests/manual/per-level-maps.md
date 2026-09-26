# Per-level maps, unsupported states, no workflow edits (REQ-W1-082)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Scratch repo with `management.statuses` given per level: a map for Tasks and another for Features, and
  `"blocked": null` in the Task map (the test list has no blocked status).
- A change `fixture-03` at phase `impl` with task `E1.F1.T1` `🔄 in_progress` in the tracker and `PLAN.md`.
- Second variant: delete in the tool the status mapped to `review`, keep the map unchanged.

## Prompt
Variant A: `Task E1.F1.T1 of fixture-03 is blocked waiting on the vendor API key. Record it.`
Variant B: `/karvey:karvey-impl fixture-03` and let the task reach review.

## Expected:
- A: the tracker status of the task is **unchanged**; a comment explaining the block is added to the task;
  `PLAN.md` shows the task as `blocked`.
- A: the Feature-level map is used for Features and the Task-level map for Tasks (check one status change of
  each level in the transcript).
- B: when the mapped `review` status is missing, the agent asks to re-map **only** the `review` entry; it
  neither creates the status in the tool nor edits any other entry of the map.

## Evidence
- Tracker activity log for the task (status unchanged, comment added) and `git diff PLAN.md`.
- For B: the question as printed and `git diff docs/spec/project.json` (one key changed at most).
