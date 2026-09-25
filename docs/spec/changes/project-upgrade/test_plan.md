# Test Plan: project-upgrade

The contract is `architecture.md` §6 (test coverage plan). Every case listed there is run below, or reported as
not run with the reason.

## Scope

- **Requirements covered:** REQ-UP-001..032 (32 of 32).
- **Layers:** Backend only (the session hook, the upgrade engine and tool, the step catalogue, the skill text, the
  linter). There is no DB layer and no UI layer: mockup, design-graphic and infra were skipped (`spec.json:skipped`).
- **Targets:** `cli` (`docs/spec/project.json:targets`). The E2E runtime is the terminal: a real headless
  `claude -p` session with the branch plugin, in a throw-away git repository with a bare local origin.
- **Stack:** Python 3 stdlib (`unittest`), bash, node (`node --test` for the page), git.

## Suites (whole repo, the CI gate)

| ID | Command | Expected |
|---|---|---|
| S-01 | `python3 -m unittest discover -s plugins/karvey/tests/unit` | OK |
| S-02 | `python3 -m unittest discover -s plugins/karvey/tests/regression` | OK |
| S-03 | `bash plugins/karvey/hooks/tests/test-hooks.sh` | 0 failed |
| S-04 | `python3 plugins/karvey/tests/hooks/run_tables.py` | 0 failed |
| S-05 | `node --test plugins/karvey/tests/page/` | 0 failed |
| S-06 | `python3 plugins/karvey/scripts/lint-plugin.py` | 0 errors |
| S-07 | `python3 plugins/karvey/scripts/karvey-state.py validate --all --root .` | 0 errors |

## Unit tests — Backend (architecture §6.1–6.2)

| ID | Suite / cases | Case | Input | Expected | REQ-UP |
|---|---|---|---|---|---|
| UT-BE-01 | `tables/session.json` ss-24, ss-25 | offer on a version change / absent record | seen 3.12.0 or none; an applicable step | one offer naming `from → installed` | 001, 002 |
| UT-BE-02 | ss-26 | no offer on resume | `resume` | no offer, record unchanged | 002 |
| UT-BE-03 | ss-27, ss-28 (+ nopy) | silent outside a Karvey project / bare `docs/spec/` | plain repo | output as before, no state dir | 003 |
| UT-BE-04 | ss-29; `test_upgrade_seen` | a decline lasts until the next version | record `declined` = installed | no offer; offer on the next version | 004 |
| UT-BE-05 | ss-30, ss-31 | nothing applies / budget exceeded | clean fixture home; probe budget 0 | no offer + `empty`; offer shown | 005 |
| UT-BE-06 | ss-32, ss-33, ss-35 (+ nopy) | bad catalogue, bounds, no python | invalid JSON; 40-row board + 6 KB handoff | one `unavailable` line; bounds unchanged | 006 |
| UT-BE-07 | ss-34 | a worktree shares the record | resolved in the main copy | no offer in the worktree, tree clean | 001 |
| UT-BE-08 | `test_upgrade_catalogue` (12) | catalogue contract | each missing field in turn | `step <id>: missing field <f>`, nothing evaluated | 008 |
| UT-BE-09 | `test_upgrade_plan` (19) | state-based plan, `--json`, check failed, read-only | seen 3.0.0 vs 3.11.4; a raising check | identical plans; exit 1 with the others evaluated; checksums unchanged | 007, 009, 010 |
| UT-BE-10 | `test_upgrade_apply` (27) | picked ids only, dry-run + preview digest, branch, idempotence, human steps, home untouched, failure stop, values as data, mixed selection | fixtures in temp git repos | as §6.2 | 011–017, 019 |
| UT-BE-11 | `test_upgrade_steps` (29) | the 8 steps on fixtures (+ plan-gate / git-flow tables after `legacy-shims`) | legacy fixture, fake home | as §6.2 | 020–026 |
| UT-BE-12 | `test_upgrade_seen` (11) | `seen --decline/--accept/--empty` 0600 atomic; outside a Karvey project refused; read-only git dir | temp repos | as §6.2 | 001, 004 |
| UT-BE-13 | `test_upgrade_cli` (21, incl. 6 regression) | commit message, staging, refusals, `pr_title` / `pr_body`, `surface` | temp repos | as §6.2 | 013, 018, 028 |
| UT-BE-14 | `test_lint_plugin` L37 (8), L38 (9), L39 (7) | L-37 surface fingerprint, L-38 catalogue lint, L-39 docs; `--list` with `REQ-UP` claims | mini plugin trees, mutated | pass / warning / error as §6.2 | 030–032 |
| UT-BE-15 | `test_no_shell_true` | no `shell=True` in the new scripts | the plugin tree | OK | 019 |

## E2E tests (terminal target, architecture §6.4)

Runtime: `claude -p --plugin-dir <worktree>/plugins/karvey --setting-sources project,local` with `HOME` pointed to a
copy of `tests/fixtures/upgrade/fake-home` under the scratch dir, in a clone of
`tests/fixtures/upgrade/legacy-project` with a bare local origin. Multi-turn via `--resume <session>`: a headless
session cannot use AskUserQuestion, so each answer is the next turn's prompt. Evidence:
`qa/manual/e2e-2026-09-25.md`.

### Flow 1: offer → accept → pick → dry-run → apply → commit → push → PR offered (E1.F8.T2)
| Step | Action | Expected |
|---|---|---|
| 1 | Start a session (no seen record) | the startup context carries the offer `Karvey → <v>`; the agent asks; nothing recorded |
| 2 | Answer "yes, show me the plan" | the skill runs; the table is the tool's rows; resume shows no second offer |
| 3 | Answer "recommended" | `seen --accept`; `branch` creates `chore/karvey-upgrade-<v>` from `origin/dev`; the dry-run diffs; one confirmation |
| 4 | Answer "yes, apply" | `apply --preview <id>`; `commit` by the tool with `Steps`, `Picked-by`, `Picked-at` |
| 5 | Answer "push and open the PR" | push to the bare origin; the PR command fails (no PR host) → the exact command is offered, nothing merged |

### Flow 2: second session in the same clone
| Step | Action | Expected |
|---|---|---|
| 1 | New session | no offer line |

### Flow 3: decline in a fresh clone, then a version change
| Step | Action | Expected |
|---|---|---|
| 1 | Fresh clone, new session | offer shown |
| 2 | Answer "not for this version" | `seen --decline`; no branch, no commit |
| 3 | New session | no offer |
| 4 | Edit the seen record's version to an older release (simulated update) and start a session | the offer is back, naming `<old> → <v>` |

### Flow 4: the manual skill script `tests/manual/upgrade-skill.md` (6 cases)
Evidence: `qa/manual/upgrade-skill-2026-09-25.md`.

## Infrastructure tests

Not applicable: no `[Infra]` task and no IAM binding (`spec.json:skipped.infra`).

## Performance benchmark (baseline)

The session hook's startup time, `bash hooks/karvey-session-context.sh startup` on the legacy fixture clone, 20 runs
after one warm-up, median:
- with the offer (no seen record: the probe runs until the first applicable step);
- without the offer (the record resolves the installed version: short-circuit, no probe);
- outside a Karvey project (reference).

Plus the full `karvey-upgrade.py plan --json` on the same clone (the worst case for the probe, all 8 steps).
