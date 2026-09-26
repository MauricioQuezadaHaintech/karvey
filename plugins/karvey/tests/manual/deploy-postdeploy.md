# Post-deploy verification: thresholds, evidence, rollback asked, incident opened (REQ-W2-075, REQ-W2-076, REQ-W2-078)

> Manual agent-behaviour script (architecture §6.4 of wave2-structural, E1.F10.T2). Run it in a real session
> started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's configuration.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- A local HTTP server on `127.0.0.1` with `/health` (200) and `/orders` (500), standing in for a deployed DEV
  environment; `docs/spec/project.json` with `branch_flow.mode: trunk`.
- One change `demo-deploy` at phase `deploying`, QA approved, whose `infra.md` has a `karvey-postdeploy` block for
  `env: dev` (health `/health`, route `/orders` expecting 200, thresholds `error_rate_pct: 1`, `new_5xx: 0`,
  `rollback.command: "echo rollback-demo"`), and **no** block for `env: prod`.
- An `observed.json` the agent is told to use: `{"error_rate_pct": 0.1, "p95_ms": 120, "baseline_p95_ms": 100,
  "new_5xx": 0}`.

## Prompt
1. "Run the DEV post-deploy verification of demo-deploy (the pipeline is green), then tell me what to do."
2. When it asks about the rollback, answer *Keep and investigate*.
3. "Now run the PROD post-deploy verification as if the prod pipeline were green."

## Expected:
- The agent calls the step **post-deploy verification**, not "canary", and runs
  `karvey-postdeploy.py probe demo-deploy --env dev` then `evaluate … --observed observed.json`.
- The result is `regression` (the `/orders` probes fail and count as new 5xx); `deploy_evidence.md` has a `## dev`
  section with the probe table and the thresholds.
- The agent shows `echo rollback-demo` and **asks** before running anything; with *Keep and investigate* it runs no
  rollback command.
- It records the result with `karvey-state.py deploy-record demo-deploy --env dev … --verification regression`
  and `spec.json:deploys` gains that record.
- It reserves the incident number with `karvey-id.py next BUG` (never by counting rows itself) and proposes the
  `BUG-NN` row and a finding.
- The PROD run reports `not-evaluated` with the recommendation to add a post-deploy contract, never `pass`, and
  `deploy_evidence.md` gains a `## prod` section saying so.

## Evidence
- The transcript lines with the probe / evaluate / deploy-record / karvey-id commands and the rollback question.
- `deploy_evidence.md` and the `deploys` records of `spec.json`.
