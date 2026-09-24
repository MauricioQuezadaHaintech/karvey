# Rule: the phase state machine

The phases of a change, their order and their preconditions are data:
`${CLAUDE_PLUGIN_ROOT}/schemas/state-machine.json`. `karvey-state.py` reads it and is the only writer of
`phase`, `approvals`, `skipped` and `phase_history` in `spec.json`. No skill edits those fields by hand, and
no skill keeps its own phase→next table: ask the tool.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py"
python3 "$S" next "{change-id}" --json          # where the change is, what runs next, what blocks it
python3 "$S" generated "{change-id}" requirements  # the phase's artifact is ready for review
python3 "$S" approve "{change-id}" requirements --by "{name}" --role human --ref D-NN
python3 "$S" advance "{change-id}" mockup         # forward edge; refused with the unmet phase named
python3 "$S" skip "{change-id}" mockup --reason "no UI"   # mockup, design_graphic, infra only
python3 "$S" reopen "{change-id}" requirements --reason "..." --ref F-NN   # karvey-iterate, spec-gap
```

## The graph

The table below is generated from `state-machine.json`; do not edit it by hand (the agreement test
`${CLAUDE_PLUGIN_ROOT}/tests/unit/test_state_machine_rule.py` fails when it drifts, and `--write` regenerates it).

<!-- generated:state-machine -->
| # | Phase | Skill | Approval key | Skippable | Produces | Reads |
|---|---|---|---|---|---|---|
| 0 | `init` | `/karvey-init` | — | no | `prd.md`, `spec.json`, `findings.md`, `PLAN.md` | — |
| 1 | `requirements` | `/karvey-requirements` | `requirements` | no | `requirements.md`, `spec-delta.md` | `prd.md` |
| 2 | `mockup` | `/karvey-mockup` | `mockup` | yes | `mockup/` | `requirements.md`, `prd.md` |
| 3 | `design_graphic` | `/karvey-design-graphic` | `design_graphic` | yes | `design-spec.md` | `mockup/`, `requirements.md` |
| 4 | `architecture` | `/karvey-architecture` | `architecture` | no | `architecture.md` | `requirements.md`, `design-spec.md?` |
| 5 | `infra` | `/karvey-infra` | `infra` | yes | `infra.md` | `architecture.md` |
| 6 | `tasks` | `/karvey-tasks` | `tasks` | no | `tasks.md` | `architecture.md`, `requirements.md` |
| 7 | `impl` | `/karvey-impl` | — | no | — | `tasks.md`, `architecture.md` |
| 8 | `test` | `/karvey-test` | — | no | — | `architecture.md`, `requirements.md` |
| 9 | `qa` | `/karvey-qa` | `qa` | no | `qa/REVISION_PR_*.md` | — |
| 10 | `deploying` | `/karvey-deploy` | `deploy` | no | — | `qa/REVISION_PR_*.md` |
| 11 | `deployed` | `/karvey-deploy` | `prod` | no | — | — |
| 12 | `archived` | `/karvey-archive` | — | no | — | `spec-delta.md` |

- **Edges:** forward: phases[i] -> phases[i+1]; a skipped phase is passed through.
- **Reopen targets** (`karvey-state.py reopen`): `requirements`, `architecture`, `tasks`, `impl`.
- **enter(P):** every phase before P with a non-null approval is approved or skipped; approvals.deploy is not a precondition in Wave 1.
- **enter(deployed):** release ledger holds a human prod approval + pipeline run + post-deploy check.
- **enter(archived):** phase = deployed AND spec.json approvals.prod.by set, role human, ref non-empty.
<!-- /generated:state-machine -->

## Preconditions and refusals

- A phase is entered only when every earlier phase with an approval key is **approved or skipped**. A refusal
  names the phase that is missing (`requirements not approved or skipped`) and leaves the file byte-identical.
- An approval needs `--by`, `--role` and `--ref` (a `D-NN` or a URL). A non-prod approval without a fresh
  marker from the approval hook is recorded with a warning (`evidence.marker: none`).
- `reopen` is a backward edge up to `qa`: the approvals of the reopened phase and every later one move to
  `revision_history`, so the downstream gates run again.
- `validate` checks the file against the schema and the graph; `validate --fix` migrates legacy shapes after
  printing the diff.

## Where each phase is committed (D-03)

| Phases | Branch | What is written |
|---|---|---|
| `init` … `qa` | the change's feature branch | `spec.json` through the tool, with the phase's artifacts |
| `deploying` | the feature branch, before the integration merge | `advance {change-id} deploying` |
| prod approval | **no commit** | the human's OK as a `D-NN`, in the PR, and in the release ledger (`approve {change-id} prod`) |
| `deployed`, `archived` | `chore/archive-{change-id}`, cut from production | `advance … deployed` with the pipeline evidence, `approve … prod --write-spec`, `advance … archived` |

Nothing is ever committed on the integration or production branch directly: those receive merges only
(`deploy-workflow.md`).
