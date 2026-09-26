# Manual script: retro-from-metrics — 2026-09-26

**Script:** `plugins/karvey/tests/manual/retro-from-metrics.md` (REQ-W2-008, REQ-W2-009) · **Result: FAIL on run 1
→ BUG-80 fixed → PASS on run 2**

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-28 (the owner's authorisation for this change's scripts),
  2026-09-26. The agent under test is a separate `claude -p` session per turn, with the branch plugin and without
  the user settings; multi-turn scripts resume the same session.
- **Throw-away repo:** `git init -q --bare "$SCRATCH/<name>.git"`, `git init -q -b main "$SCRATCH/<name>"` with
  `origin` pointing at the bare repo; fixture state written only through `plugins/karvey/scripts/karvey-state.py`
  (`init`, `lane set`, `advance`, `generated`, `approve --role human --ref D-01`, `skip`). `$SCRATCH` is a
  `mktemp -d` directory, deleted after the run, and the sessions' transcript directories were deleted with it.
- **Agent-under-test command** (every turn; later turns add `--resume <session>`):

```bash
cd "$SCRATCH/<name>" && claude -p [--resume <session>] \
  --plugin-dir <worktree>/plugins/karvey --setting-sources project,local \
  --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent,Skill,TodoWrite,WebFetch" \
  --output-format stream-json --verbose "<prompt>"
```

- **Harness limit:** a `-p` session has no `AskUserQuestion` tool (its init event lists the tools), so every
  question arrives as one prose message and the answer is the next turn's prompt. Where a script counts questions
  per `AskUserQuestion` call, the count is taken per question message.

## Setup done

- `plugins/karvey/tests/unit/fixtures/metrics/docs` copied into the repo (archived `alpha`, `beta`, `delta` legacy
  with date-only approvals, `gamma`); `docs/spec/retros/retro-2026-09-07.md` with `BL-01` (owner: the reviewer role)
  and `BL-02` (owner: the maintainer role); `docs/spec/backlog.md` with `BL-01` `done` and `BL-02` `open`. Committed.

## Prompts

1. `/karvey:karvey-retro --from 2026-09-01 --to 2026-09-14`
2. Two actions agreed, one with owner "the reviewer role", one without an owner (run 1: actions 1 and 3; run 2:
   actions 3 and 1 of that run's proposals).

## Transcript excerpt (run 2)

```
TOOL Bash: python3 "$C" --metrics --from 2026-09-01 --to 2026-09-14 --as-of 2026-09-26 --json
TOOL Bash: python3 "$C" --metrics --from 2026-09-01 --to 2026-09-14 --as-of 2026-09-26
… I'll ask for each owner once. An action left without an owner goes in the retro file as `unowned` and gets
no backlog row. … The Origin cell will read `retro-2026-09-14 · owner: …`.
- "No archive with open findings" is recorded as `unowned`, so it has no backlog row. I had already asked for an
  owner for each action, and none was given for this one.
```

## Evidence

Retro file (run 2, on `docs/retro-2026-09-14`): `lead_time_days | 1.25`; `lead_time_days: n/a — approvals without
time (delta)`; `estimate_accuracy | 0.96`; `judge_cost_usd | total 1.0 (estimated)`; section `## Findings by type and
phase`; previous actions `BL-01 … done`, `BL-02 … open`; agreed actions `BL-03 | the reviewer role` and `— | unowned`.

`git diff docs/spec/backlog.md` (run 2):

```
+| BL-03 | 2026-09-26 | retro-2026-09-14 · owner: the reviewer role | process | med | Regression check before patch-lane deploys | open | — | — |
```

Run 1 wrote `| BL-03 | 2026-09-14 | retro-2026-09-14 | process | med | Record the actual column … | open | — | — |`:
the owner lived only in the retro file.

## Expected lines

| Expected | Run 1 | Run 2 |
|---|---|---|
| runs `--metrics --from … --to … --as-of <today>`; lead time 1.25; `n/a — approvals without time (delta)`, never 0 | PASS | PASS |
| findings by type and phase; estimate accuracy 0.96; judge cost 1.0 USD marked estimated | PASS | PASS |
| both previous actions listed with state (`BL-01` done, `BL-02` open) | PASS | PASS |
| owned action → one `process` row with the next free `BL-NN` **and its owner**; unowned action asked once, no row | **FAIL**: row without owner | PASS (owner question asked once for every proposed action; no second ask, no row) |
| `retro-2026-09-14.md` with period, commands and the Step 5 sections | PASS | PASS |
| no per-author analysis (no `--per-person`) | PASS | PASS |

**Overall: PASS after the fix.** Run 1's failure is F-11 / BUG-80: the backlog table has no owner column and the skill
did not say where the owner goes; `karvey-retro` Step 4 and `rules/backlog.md` now put it in the Origin cell
(`retro-{to} · owner: {owner}`), guarded by `test_metrics.py` `RetroActionOwner`. Side note (F-28): the agent ran
`karvey-id.py next BL` three times "to check" and each call reserved a number.
