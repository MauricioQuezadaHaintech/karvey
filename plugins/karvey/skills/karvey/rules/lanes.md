# Rule: lanes — the process scales with the change

Every change runs in one **lane**. The lane says, per phase, whether the phase is mandatory, optional or skipped,
how many human gates apply and how many judges review each judged phase. The table is data:
`${CLAUDE_PLUGIN_ROOT}/schemas/lanes.json`. `karvey-state.py` reads it: `next` passes the phases the lane skips,
`advance` records them as `skipped[phase] = "lane:{lane}"`, and a phase the lane requires is never passed.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py"
python3 "$S" lane "{change-id}" set standard                                 # at init
python3 "$S" lane "{change-id}" set patch --answers answers.json             # D-29 criteria checked
python3 "$S" lane "{change-id}" raise standard --reason "needs a contract change" --by "{name}"
python3 "$S" lane "{change-id}" lower patch --reason "…" --by "{name}" --role human --ref D-NN   # the human only
python3 "$S" lane-evidence "{change-id}" --bug BUG-NN --finding F-NN --regression-test PATH::NAME
```

## The table

The block below is generated from `lanes.json`; do not edit it by hand (lint L-40 fails when it drifts).

<!-- generated:lanes -->
| lane | `requirements` | `mockup` | `design_graphic` | `architecture` | `infra` | `tasks` | `impl` | `test` | `qa` | `deploying` | human gates (merged) | judges per judged phase |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `patch` | s | s | s | s | s | s | m (test-first) | m (regression) | m (qa-lite) | m | 1 (prod) | 0 |
| `standard` | m | s | s | m | o | m | m | m | m | m | 3 (what, how, release) | 2 |
| `feature-ui` | m | m | m | m | o | m | m | m | m | m | 3 (what, how, release) | 3 |
| `ops` | m (lite) | s | s | s | m | m | m | m (verification) | o | m | 2 (what+how, release) | 2 |
| `hotfix` | s | s | s | s | s | s | m (no tasks approval) | m (regression) | o (qa-lite) | m | 1 (prod) | 0 |
| `docs` | o | s | s | s | s | o | m | o | m (qa-lite) | m | 1 (release) | 0 |

- `m` mandatory · `o` optional (runs when the change needs it; a skip with a reason is accepted) · `s` skipped by the lane (recorded as `skipped[phase] = "lane:{lane}"`). `init`, `deployed` and `archived` are `m` in every lane.
- `patch` requires `bug_id`, `finding`, `regression_test`.
- `patch` admission: at most 3 code files; no schema, no api contract, no permissions; Security Tier at most 2.
- `hotfix` requires `bug_id`, `finding`, `regression_test`.
- A change without `lane` is `legacy`: the 3.12 pipeline, every phase mandatory unless recorded as skipped (a `type: ops|hotfix` without `lane` is shown as that lane, and `lane set` records it).
<!-- /generated:lanes -->

## Choosing the lane at init (objective questions)

`karvey-init` asks, and records the answers in a JSON file for `lane set`:

1. Does the change touch UI? (`touches_ui`)
2. Does it change a data schema? (`schema`) An API contract? (`api_contract`)
3. Does it change permissions or a trust boundary? (`permissions_or_trust`)
4. Which Security Tier? (`tier`) How many code files? (`code_files`)

- UI → `feature-ui`. No UI → `standard`. An answer nobody can give → `standard`, and the agent says which one.
- `patch` is the official path for a **small bug** (D-25): at most 3 code files, no schema, API contract or
  permissions change, Tier below 3 (D-29). `lane set patch` refuses a failing criterion and names it
  (`patch: schema change — use standard`).
- `ops` is a change without application code (IAM, DNS, secrets rotation, quota, console configuration): the
  requirements are the verifiable goal, infra is a command plan, tasks are `[human]`/`[Infra]`, and the test is
  the read-only verification of each step, recorded in `test_evidence.md`. It skips mockup, design and
  architecture unless the plan touches a trust boundary (then raise it to `standard`).
- `hotfix` is a production defect that must be fixed now. It is fast, **not** unrecorded: the same PR carries the
  fix, the `BUG-NN` (tracker + `findings.md`) and the regression test that fails without the fix. impl starts
  without a tasks approval only once `lane-evidence` records the BUG-NN and the regression test. Root cause is
  still investigated (Iron Law), and the incident reaches `RESUELTO` only with the regression test. Chained
  hotfixes on the same day are each a separate version, appended to `revision_history`. The production gate
  still applies.
- `docs` changes only documentation and specs: QA-lite and one release gate.

## Changing lanes

- **Raise freely.** `lane raise` records `{from, to, at, reason, by}` in `lane_history`; the phases the new lane
  requires and the old one skipped become pending (the change goes back to the first of them). Manual skips are
  kept. A raise only adds process: every phase keeps at least its mode (mandatory stays mandatory, optional stays at
  least optional). A lane that runs more phases but makes one optional (e.g. `docs` → `ops` makes QA optional) is
  a lower.
- **Lower only with the human.** `lane lower` refuses without `--by`, `--role human`, `--ref` and a valid human
  approval marker. A lower lane is less review: the human decides it, never the agent.
- **The diff is checked against the lane.** QA (or QA-lite) measures the diff against the lane's criteria and
  reports every exceeded one as a finding with a raise proposal (`lane exceeded: 5 > 3 code files`); in 3.13 the
  check warns (`check-modes.json:lane.diff`).

A change without `lane` keeps the 3.12 pipeline and `next` prints one warning; under `schema.strict` (4.0) the
missing lane is an error.

