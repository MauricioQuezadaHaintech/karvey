# Test Evidence: wave1-hardening

**Date:** 2026-09-24 18:50 -03
**Environment:** local (haintech-lab, Linux 6.8, Python 3, node) + GitHub Actions on draft PR #24
**Stack:** Python stdlib scripts, bash hooks, static HTML/JS page
**Targets:** `cli`
**E2E Runtime:** terminal + a real Claude Code 2.1.282 session loading the branch plugin (`plugins/karvey`)
**Commit under test:** `b9c7fab` (feature/wave1-hardening)
**Plan:** `docs/test_plan.md` (contract: `architecture.md` §6)

## Unit and table tests

| ID | Command | Output (tail) | Result |
|----|---------|---------------|--------|
| UT-BE-01 | `python3 -m unittest discover -s plugins/karvey/tests/unit` | `Ran 694 tests in 10.434s` · `OK` | ✅ PASS |
| UT-BE-02 | `python3 -m unittest discover -s plugins/karvey/tests/regression` | `Ran 10 tests in 0.184s` · `OK` | ✅ PASS |
| UT-BE-03 | `bash plugins/karvey/hooks/tests/test-hooks.sh` | `result: 58 passed, 0 failed` (includes "hooks.json: every declared command runs as written") | ✅ PASS |
| UT-BE-04 | `python3 plugins/karvey/tests/hooks/run_tables.py` | `guard tables: 313 cases, 381 runs (68 nopy), 381 passed, 0 failed` | ✅ PASS |
| UT-FE-01 | `node --test plugins/karvey/tests/page/` | `# pass 22` · `# fail 0` | ✅ PASS |
| UT-LINT-01 | `python3 plugins/karvey/scripts/lint-plugin.py` | `0 errors, 3 warnings (36 checks)` — the 3 warnings are L-18 advisory counts on the archived team-layer, team-adapters and wave1-hardening `spec.json` | ✅ PASS |

## Integration

### IT-01: `validate --all` (AC-1)
**Result: ✅ PASS**
```
OK         docs/spec/changes/team-adapters/spec.json (0 errors, 15 warnings)
OK         docs/spec/changes/wave1-hardening/spec.json (0 errors, 3 warnings)
OK         docs/spec/project.json (0 errors, 0 warnings)
mode: advisory · 4 files · 0 errors · 35 warnings
rc=0
```
Warnings are legacy date-only approvals and missing `role`/`ref` on pre-3.12 history (D-14, F-05/F-06): advisory by design.

### IT-02: CI on PR #24 (REQ-W1-030, REQ-W1-054)
**Result: ✅ PASS** — run 36063032643 @ `febcf59`
```
windows-advisory success 22s
page success 11s
tests (macos-latest, 3.9) success 279s
tests (ubuntu-latest, 3.9) success 108s
lint success 6s
tests (macos-latest, 3.12) success 260s
tests (ubuntu-latest, 3.12) success 93s
```
No job under 5 s. `b9c7fab` is a docs-only commit on top.

## E2E Tests (real session, branch plugin)

| ID | Step | Observed | Status |
|----|------|----------|--------|
| E2E-01 | `karvey-state.py advance wave1-hardening qa` from `impl` | `[error] edge not in the graph: impl → qa (test not passed)`, rc 3, file untouched | ✅ |
| E2E-01 | `advance wave1-hardening test` | `wave1-hardening: impl → test`; `phase_history` init → requirements → architecture (D-05) → tasks (D-09) → impl (D-13) → test, each with entered/exited | ✅ |
| E2E-01 | `advance wave1-hardening deploying` from `test` | `[error] qa not approved or skipped` | ✅ |
| E2E-02 | Owner typed `ok` | `[karvey] approval recorded (plan, wave1-hardening, expires 23:38)` | ✅ |
| E2E-02 | Owner typed «ok, registra la aprobación de prod de team-adapters con D-08» | `[karvey] approval recorded (prod, team-adapters, expires 23:39)`; then `approve team-adapters prod --role human --ref D-08 --write-spec` → `approvals.prod written to spec.json from the decision (ref D-08)` | ✅ |
| E2E-03 | Agent ran a command that opened `$(git rev-parse --git-common-dir)/karvey/approvals/team-adapters.json` | `[karvey] BLOCK protect-paths: approval comes only from the human's message (D-01)…` | ✅ |
| E2E-04 | 3.12.0 release PR through the prod-gate | not run yet: belongs to `karvey-deploy` (E1.F16.T4..T6), owner present | ⏳ pending |
| E2E-05 | Archive of the change | not run yet: belongs to `karvey-archive` | ⏳ pending |

## Manual agent-behaviour scripts (AC-7)

**Not run in this phase.** Each of the 10 scripts under `plugins/karvey/tests/manual/` needs a separate real
session in a throw-away repo, and several need resources this session does not have: a ClickUp test list
(`no-human-no-mapping`, `missing-status-map`, `per-level-maps`, `find-or-create`), a DEV front plus the browser
agent (`visible-version`), or interactive answers from a human (`init-not-now`, `settings-merge`,
`settings-docs-branch`). The regression index still names a check for every incident (UT-BE-02); BUG-05's manual
half (`impl-resume.md`) is among the pending scripts. Evidence goes to
`docs/spec/changes/wave1-hardening/qa/manual/<script>-<date>.md` when they run.

## Performance benchmark (baseline)

**Measured runtime:** terminal, local (`CLAUDE_PLUGIN_ROOT=plugins/karvey`), wall-clock per process.

| Metric | Current run (median / p95) | Previous baseline | Delta | Status |
|--------|---------------------------|-------------------|-------|--------|
| `karvey-hook.sh pre-bash` (`ls 2>/dev/null`), n=20 | 88 ms / 92 ms | — (first baseline) | — | ✅ under the 5 s hook timeout |
| `karvey-session-context.sh startup`, n=10 | 92 ms / 95 ms | — | — | ✅ under the 10 s timeout |
| `karvey-state.py next`, n=10 | 72 ms / 84 ms | — | — | ✅ |
| `karvey-context.py`, n=5 | 92 ms / 97 ms | — | — | ✅ |

## Generated regression tests

No test failed in this run, so no new regression test was generated. The BUG-05..21 regression index is
`plugins/karvey/tests/regression/test_incidents.py` (UT-BE-02).

## Summary

| Category | Total | PASS | FAIL | Pending |
|----------|-------|------|------|---------|
| Backend unit | 694 | 694 | 0 | — |
| Regression | 10 | 10 | 0 | — |
| Hook commands | 58 | 58 | 0 | — |
| Guard table runs | 381 | 381 | 0 | — |
| Frontend (page) | 22 | 22 | 0 | — |
| Integration | 2 | 2 | 0 | — |
| E2E | 5 | 3 | 0 | 2 (deploy, archive) |
| Manual scripts | 10 | — | — | 10 |

## Test phase 2 (2026-09-25)

**Date:** 2026-09-25 (run 2026-09-26 01:30 UTC) · **Environment:** local (Linux, Python 3, node) + GitHub Actions
**Commit under test:** `07e964c` + architecture revision 2 (docs only) · **Targets:** `cli`

### Full suite

| ID | Command | Output (tail) | Result |
|----|---------|---------------|--------|
| UT-BE-01 | `python3 -m unittest discover -s plugins/karvey/tests/unit` | `Ran 711 tests` · `OK` | ✅ PASS |
| UT-BE-02 | `python3 -m unittest discover -s plugins/karvey/tests/regression` | `Ran 10 tests` · `OK` (BUG-05..26 index) | ✅ PASS |
| UT-BE-03 | `bash plugins/karvey/hooks/tests/test-hooks.sh` | `result: 68 passed, 0 failed` | ✅ PASS |
| UT-BE-04 | `python3 plugins/karvey/tests/hooks/run_tables.py` | `321 cases, 390 runs (69 nopy), 390 passed, 0 failed` (incl. `subagent-prompt.json` 7 + 1 nopy) | ✅ PASS |
| UT-FE-01 | `node --test plugins/karvey/tests/page/` | `# pass 22` · `# fail 0` | ✅ PASS |
| UT-LINT-01 | `python3 plugins/karvey/scripts/lint-plugin.py` | `0 errors, 3 warnings (36 checks)` (L-18 advisory counts) | ✅ PASS |
| IT-01 | `karvey-state.py validate --all --root .` | `4 files · 0 errors · 33 warnings` | ✅ PASS |

### Manual agent-behaviour scripts (AC-7): 10/10 PASS

| Script | REQ | First run | Re-run after fix | Evidence |
|--------|-----|-----------|------------------|----------|
| find-or-create | 089 | PASS | — | `qa/manual/find-or-create-2026-09-25.md` |
| impl-resume | 085 (BUG-05) | PASS | — | `qa/manual/impl-resume-2026-09-25.md` |
| init-not-now | 095 | PASS | — | `qa/manual/init-not-now-2026-09-25.md` |
| missing-status-map | 080 | PASS | — | `qa/manual/missing-status-map-2026-09-25.md` |
| qa-review-to-done | 084 | PASS | — | `qa/manual/qa-review-to-done-2026-09-25.md` |
| settings-merge | 096 (BUG-01) | PASS | — | `qa/manual/settings-merge-2026-09-25.md` |
| settings-docs-branch | 083 | FAIL → BUG-23 | PASS | `qa/manual/settings-docs-branch-2026-09-25{,-rerun}.md` |
| visible-version | 041 | FAIL → BUG-24 | PASS | `qa/manual/visible-version-2026-09-25{,-rerun}.md` |
| no-human-no-mapping | 081 | FAIL → BUG-25 | PASS (tracker lines by the regression tests) | `qa/manual/no-human-no-mapping-2026-09-25{,-rerun}.md` |
| per-level-maps | 082 | FAIL → BUG-26 | PASS (tracker lines by the regression tests) | `qa/manual/per-level-maps-2026-09-25{,-rerun}.md` |

Paths are under `docs/spec/changes/wave1-hardening/`.

### PASS/FAIL per requirement area

| Area (requirements.md) | Evidence | Result |
|------------------------|----------|--------|
| R1 State machine (001..013) | unit (`test_state_*`, schemas), IT-01, E2E-01 | ✅ PASS |
| R2 Guards (014..030) + subagent-prompt (081, D-33) | tables (390 runs), test-hooks, E2E-02/03, CI | ✅ PASS |
| R3 Deploy/archive off integration (031..035) | unit + prod-gate table; E2E-04/05 in deploy/archive | ✅ PASS (E2E pending) |
| R4 One versioning moment (036..041) | unit, lint; visible-version manual | ✅ PASS |
| R5 Estimates preserved (042..044) | unit, lint | ✅ PASS |
| R6 Session hook (045..051) | session table, test-hooks, BUG-22/23 regressions | ✅ PASS |
| R7 Plugin as code (052..) | lint 0 errors, CI | ✅ PASS |
| R8 Graphify / tracker ritual off the hot path | unit, pending-sync table | ✅ PASS |
| R9 Spec-delta merge tool | unit (`test_spec_merge*`) | ✅ PASS |
| R10 Dashboard | unit (`test_context*`) | ✅ PASS |
| R11 QA observes only | lint, qa-review-to-done manual | ✅ PASS |
| R12 Short descriptions | lint | ✅ PASS |
| R13 Tracker adapters (080..096) | 8 manual scripts, unit, BUG-25/26 regressions | ✅ PASS |
| R14 Notifications | notify-confirm table, unit | ✅ PASS |
| R15 Statusline and method page | statusline table, page tests | ✅ PASS |
| R16 Convergence and dogfooding | this repo's own state (IT-01), regression index BUG-01..26 RESUELTO | ✅ PASS (archive pending) |

### Benchmark (BM-02)

| Metric | This run (median / p95) | Previous baseline | Delta | Status |
|--------|-------------------------|-------------------|-------|--------|
| `karvey-hook.sh pre-bash` (`ls 2>/dev/null`), n=20 | 128 ms / 156 ms (second sample; first 148 / 177) | 88 / 92 ms | +40 ms | ⚠️ slower, far under the 15 s timeout; host load average 3.3 during the run → F-55 |
| `karvey-hook.sh pre-agent` (plain prompt), n=20 | 138 ms / 151 ms | — (new) | — | ✅ under the 5 s timeout |

### Regression tests added since phase 1

BUG-22..26, each red first on its parent commit (`docs/bugs_dev_testing.md`): `test_incidents.py` index entries,
`session.json`, `subagent-prompt.json` sp-01..07, unit tests in `test_karvey_hooks.py` and the config/adapter tests.
