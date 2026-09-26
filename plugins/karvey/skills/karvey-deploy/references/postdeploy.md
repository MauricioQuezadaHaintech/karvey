# Deploy reference: post-deploy verification

Loaded by `karvey-deploy` when the change's `infra.md` has a post-deploy contract (steps 2.6 and 2.10).

After each deploy (DEV in 2.6, PROD in 2.10), against the post-deploy contract `karvey-infra` wrote in `infra.md` (REQ-W2-075..078). The word "canary" is kept only where the platform really splits traffic between two versions; everything else is **post-deploy verification**.
```bash
PD="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-postdeploy.py"
python3 "$PD" probe "{change-id}" --env "{env}" --json        # health + routes, spread over the window
# gather error rate, p95, the production baseline p95 and new 5xx from the contract's metrics_source into
# observed.json — a presented command, under the plan gate (platform-specific; the script only compares numbers)
python3 "$PD" evaluate "{change-id}" --env "{env}" --observed observed.json --version "{version}" --json
```
1. The result is `pass`, `regression` or `not-evaluated` — **say it as the tool says it**. The probe table and the thresholds go to `docs/spec/changes/{change-id}/deploy_evidence.md`.
2. **No contract, or no thresholds** → `not-evaluated`, with the recommendation to add the contract to `infra.md`; it is never reported as a pass.
3. Record every result with the printed command: `python3 "$S" deploy-record "{change-id}" --env "{env}" --version "{version}" --verification {result} --evidence docs/spec/changes/{change-id}/deploy_evidence.md`.
4. **`regression`** (REQ-W2-078):
   - DEV → stop before prod.
   - PROD → show the contract's `rollback.command` and **ask the human** with `AskUserQuestion` (*Roll back now (recommended)* / *Keep and investigate*). The rollback affects production: it runs only after that answer, through the plan gate, never on the agent's initiative. Then record it: `python3 "$S" deploy-record "{change-id}" --env prod --version "{version}" --verification regression --rollback "{what was run}" --evidence …`.
   - Open the incident with a reserved number: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-id.py" next BUG`, then the `BUG-NN` row in `docs/bugs_dev_testing.md` and a finding in the change's `findings.md` (the incident tracker[^r-incident-tracking]).

[^r-incident-tracking]: ../../karvey/rules/incident-tracking.md — context only, not opened.
