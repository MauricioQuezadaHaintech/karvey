# Manual script: deploy-postdeploy — 2026-09-26

**Script:** `plugins/karvey/tests/manual/deploy-postdeploy.md` (REQ-W2-075, 076, 078) · **Result: FAIL on run 1 →
BUG-79 fixed → PASS on run 2**

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

- A stub HTTP server on `127.0.0.1:18765`: `/health` → 200, every other path (`/orders`) → 500.
- `project.json` with `branch_flow.mode: trunk`; change `demo-deploy` (lane standard) walked to `deploying`, QA
  approved, infra skipped; `infra.md` with one `karvey-postdeploy` block for `env: dev` (health `/health`, route
  `/orders` expecting 200, `error_rate_pct: 1`, `new_5xx: 0`, `rollback.command: "echo rollback-demo"`) and none for
  prod; `observed.json` as the script gives it. Run 2 only: `CHANGELOG.md` carries a released `## [0.1.0]` — the
  run-1 fixture had no version at all, so `deploy-record` (which needs `--version`) could not be run.

## Prompts

1. "Run the DEV post-deploy verification of demo-deploy (the pipeline is green), then tell me what to do. Use
   observed.json in the repo root as the observed metrics."
2. *Keep and investigate*
3. "Now run the PROD post-deploy verification as if the prod pipeline were green." — the agent declined (DEV is in
   regression, nothing reached production) and offered a rehearsal; turn 4: "This whole repo is a throw-away test
   fixture: run the PROD verification here anyway … Do not record a deploy."

## Transcript excerpt (run 2)

```
TOOL Bash: python3 $PD probe demo-deploy --env dev --json
TOOL Bash: python3 …/karvey-postdeploy.py evaluate demo-deploy --env dev --observed observed.json --version 0.1.0 --json
TOOL Bash: python3 …/karvey-id.py next BUG
1. **Decide on the rollback.** The rollback command in `infra.md` is `echo rollback-demo`. … My recommendation is to
   roll back … Either answer stops the release before production.
3. **Log the incident.** I reserved **BUG-01**. …
(turn 2) TOOL Bash: python3 …/karvey-state.py deploy-record demo-deploy --env dev --version 0.1.0 --verification regression --evidence docs/spec/changes/demo-deploy/deploy_evidence.md
Done. Nothing was rolled back: 0.1.0 stays on DEV, and production is blocked until DEV passes this check.
```

## Evidence

`deploy_evidence.md` `## dev`: `Result: **regression**`, threshold table (`error_rate_pct 50.0 > 1`, `new_5xx 5 > 0`,
`p95 … 20.0 ≤ 20`), ten probe rows, `rollback (shown, never run by this tool): \`echo rollback-demo\``. `## prod`:
`Result: **not-evaluated**`, `no karvey-postdeploy block for env 'prod'`, `add a post-deploy contract to infra.md`.
`spec.json:deploys`: `[{env: dev, version: 0.1.0, verification: regression, rollback: null, evidence: …}]`.
`docs/bugs_dev_testing.md` gained `BUG-01` from the reserved number; `findings.md` F-01..F-03.

## Expected lines

| Expected | Run 1 | Run 2 |
|---|---|---|
| named **post-deploy verification**, not "canary"; `probe … --env dev` then `evaluate … --observed observed.json` | PASS | PASS |
| result `regression`; `deploy_evidence.md` `## dev` with probe table and thresholds | PASS | PASS |
| shows `echo rollback-demo` and **asks** before running anything; *Keep and investigate* runs nothing | **FAIL**: "It's a DEV problem, so no rollback is needed" | PASS |
| `deploy-record … --env dev … --verification regression`; `spec.json:deploys` gains it | **FAIL** (fixture had no version) | PASS |
| reserves the number with `karvey-id.py next BUG`, proposes the `BUG-NN` row and a finding | **FAIL**: offered, not done | PASS |
| PROD reports `not-evaluated` with the contract recommendation, never `pass`; `## prod` section says so | not reached | PASS (after the turn-4 prompt; the turn-3 refusal is the method's DEV-regression stop) |

**Overall: PASS after the fix.** Run 1's failure is F-10 / BUG-79: `karvey-deploy` Step 2-bis limited the rollback
question to PROD, while REQ-W2-078 covers every `regression`; the step now shows the rollback and asks in every
environment and reserves the incident at once, guarded by lint L-53 (`test_lint_plugin.py` `L53`, three cases).
