# The retro works on the method's artifacts and follows up its actions (REQ-W2-008, REQ-W2-009)

> Manual agent-behaviour script (architecture §6.4 of wave2-structural, E1.F1.T10). Run it in a real session
> started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's configuration.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Copy `plugins/karvey/tests/unit/fixtures/metrics/docs` into the scratch repo (four archived changes, one of
  them legacy with date-only approvals) and commit it.
- Add `docs/spec/retros/retro-2026-09-07.md` with two agreed actions, `BL-01` and `BL-02`, and a
  `docs/spec/backlog.md` whose `BL-01` row is `done` and `BL-02` row is `open`.

## Prompt
1. `/karvey:karvey-retro --from 2026-09-01 --to 2026-09-14`
2. When the retro proposes actions, agree two: one with an owner ("the reviewer role") and one without an owner;
   when asked for the missing owner, answer "none".

## Expected:
- The agent runs `karvey-context.py --metrics --from 2026-09-01 --to 2026-09-14 --as-of <today>` and reports the
  lead time `1.25` days in total, `n/a — approvals without time (delta)` as n/a with its reason (never 0).
- Findings are shown by type and by phase; estimate accuracy `0.96`; judge cost `1.0` USD marked estimated.
- Both previous actions are listed with their state: `BL-01` done, `BL-02` open.
- The owned action becomes one `process` row in `backlog.md` with the next free `BL-NN` and its owner; the
  agent asks once for the owner of the other action and, with no owner given, writes **no** backlog row for it
  (it stays `unowned` in the retro file).
- `docs/spec/retros/retro-2026-09-14.md` exists with the period, the commands and the sections of Step 5.
- No per-author commit analysis or ranking appears (no `--per-person`).

## Evidence
- The transcript lines with the commands and the reported numbers.
- `git diff docs/spec/backlog.md` and the new retro file.
