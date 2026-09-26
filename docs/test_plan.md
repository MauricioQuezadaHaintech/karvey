# Test Plan: wave1-hardening

> The contract is `docs/spec/changes/wave1-hardening/architecture.md` §6. This file maps each §6 row to how
> it is run; the results live in `docs/test_evidence.md`.

## Scope
Requirements covered: REQ-W1-001..109 (traceability: `architecture.md` §11, `tasks.md` requirement index).
Layers: Backend (Python stdlib scripts, bash hooks), Frontend (`docs/karvey.html` page logic), skill and rule text (lint).
Target: `cli` (`docs/spec/project.json:targets`). Runtime: the terminal and a real Claude Code session.

## Unit and table tests

| ID | Suite | Command | Covers (§6) |
|----|-------|---------|-------------|
| UT-BE-01 | Python unit | `python3 -m unittest discover -s plugins/karvey/tests/unit` | §6.2 (every module row), §6.3 fixtures |
| UT-BE-02 | Regression index BUG-05..21 | `python3 -m unittest discover -s plugins/karvey/tests/regression` | §6.4 |
| UT-BE-03 | Hook commands as declared in `hooks.json` + no-python modes | `bash plugins/karvey/hooks/tests/test-hooks.sh` | §6.1 dispatcher, BUG-18 |
| UT-BE-04 | Guard tables (plan-gate, git-flow, prod-gate, approval, protect-paths, notify-confirm, spec-write, session, statusline) incl. `nopy` pass | `python3 plugins/karvey/tests/hooks/run_tables.py` | §6.1 |
| UT-FE-01 | Page logic (node) | `node --test plugins/karvey/tests/page/` | §6.4 BUG-10..13 |
| UT-LINT-01 | Plugin linter, whole repo | `python3 plugins/karvey/scripts/lint-plugin.py` | L-NN, §6.4 lint rows |

## Integration

| ID | Case | Command | Expected |
|----|------|---------|----------|
| IT-01 | This repo's spec files validate (AC-1) | `python3 plugins/karvey/scripts/karvey-state.py validate --all --root .` | exit 0, 0 errors |
| IT-02 | CI proof on the PR (REQ-W1-030, 054) | `gh run view <id> --json jobs` on PR #24 | 7 jobs green, none under 5 s |

## E2E (target `cli`: a real Claude Code session with the branch plugin)

| ID | Flow | Expected |
|----|------|----------|
| E2E-01 | Dogfood cycle: every phase from `tasks` on recorded with `karvey-state.py` | `phase_history` complete; `advance` refuses a skipped edge |
| E2E-02 | Approval hook in a live session (plan kind, prod kind) | `[karvey] approval recorded (…)` on the owner's own words |
| E2E-03 | protect-paths in a live session | the agent's attempt to read/write the marker path is blocked |
| E2E-04 | 3.12.0 release PR through the prod-gate (blocked, then allowed after the prod phrase) | runs in `karvey-deploy` (E1.F16.T4..T6), owner present |
| E2E-05 | Archive on `chore/archive-wave1-hardening` | runs in `karvey-archive` |

## Manual agent-behaviour scripts (`plugins/karvey/tests/manual/`, AC-7)

`find-or-create`, `impl-resume`, `init-not-now`, `missing-status-map`, `no-human-no-mapping`, `per-level-maps`,
`qa-review-to-done`, `settings-docs-branch`, `settings-merge`, `visible-version`. Each needs a real session in a
throw-away repo; several need a tracker test list, a DEV front with the browser agent, or interactive answers.

## Benchmark (CLI)

Median and p95 wall-clock of the hook dispatcher (`pre-bash`), the session hook (`startup`), `karvey-state.py next`
and `karvey-context.py`, run locally with the plugin as the hooks call it.

## Test phase 2 (2026-09-25)

Second pass after the architecture revision (D-19, revision 1), the E1.F17 fixes (BUG-22..26) and the
`subagent-prompt` guard kept by D-33 (architecture revision 2). Same rows as above, plus:

| ID | Suite | Command | Covers (§6) |
|----|-------|---------|-------------|
| UT-BE-04b | `subagent-prompt.json` table (7 cases, sp-01 also `nopy`) | `python3 plugins/karvey/tests/hooks/run_tables.py` | §6.1 (revision 2) |
| MAN-01..10 | The 10 manual scripts, run by the owner with the agent, one throw-away repo each; four re-run after their fixes | evidence under `docs/spec/changes/wave1-hardening/qa/manual/` | §6.5 (revision 1) |
| IT-02b | CI on the pushed head of `feature/wave1-hardening` | `gh run list -b feature/wave1-hardening -L 1` | §1.11 |
| BM-02 | Dispatcher latency: `pre-bash` again, `pre-agent` new | as in the benchmark row above, n=20 | baseline comparison |

E2E-04 (release PR through the prod-gate) and E2E-05 (archive) stay in `karvey-deploy` and `karvey-archive`.
