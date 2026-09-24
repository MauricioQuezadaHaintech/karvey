# Idempotent creation: find-or-create (REQ-W1-089)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Scratch repo tracked in a sandbox tracker list you own. A change `fixture-06` whose tasks were already
  created by `karvey-tasks` (their ids are in `spec.json:clickup.task_ids`). Save
  `jq -S .clickup docs/spec/changes/fixture-06/spec.json > "$SCRATCH/ids-before.json"` and the list's item count.
- Second variant: create by hand in the tracker a second item named exactly like `E1.F1.T1`.

## Prompt
Variant A: `/karvey:karvey-tasks fixture-06` (re-run).
Variant B: `/karvey:karvey-tasks fixture-06` with the duplicate present.

## Expected:
- A: the agent searches for each natural key (`E1`, `E1.F1`, `E1.F1.T1`, …) before creating; no new item is
  created; the list's item count is unchanged; `jq -S .clickup …` equals `ids-before.json`.
- B: the agent stops at the duplicated key and asks which item is canonical; it creates nothing for that key.

## Evidence
- The list's item count before and after, the `diff` of the two id dumps, and the question printed in B.
