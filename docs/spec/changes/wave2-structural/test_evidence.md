# Test Evidence: wave2-structural

**Date:** 2026-09-26 (Chile time)
**Environment:** local (Linux 6.8, Python 3, node)
**Stack:** Python stdlib scripts, bash hooks, static HTML/JS page
**Targets:** `cli`
**Runtime:** terminal
**Commit under test:** `3cabf6c` (feature/wave2-structural; every one of the 79 commits of this change carries `Karvey-Change: wave2-structural`)
**Plan:** `test_plan.md` (contract: `architecture.md` §6) · **Trace:** `traceability.md` · **Evidence lines:** `evidence.jsonl`

## Suite runs (each through `karvey-evidence.py`; hashes only, no output stored)

| ID | Command | Output (tail) | Evidence | Result |
|----|---------|---------------|----------|--------|
| UT-01 | `python3 -m unittest discover -s plugins/karvey/tests/unit` | `Ran 1017 tests` · `OK` | `evidence.jsonl:11` | ✅ PASS |
| UT-02 | `python3 -m unittest discover -s plugins/karvey/tests/regression` | `Ran 10 tests` · `OK` | `evidence.jsonl:12` | ✅ PASS |
| TB-01 | `python3 plugins/karvey/tests/hooks/run_tables.py --junit …/test-results/tables.xml` | `guard tables: 406 cases, 474 runs (68 nopy), 474 passed, 0 failed` | `evidence.jsonl:13` | ✅ PASS |
| HK-01 | `KARVEY_SKIP_TABLES=1 bash plugins/karvey/hooks/tests/test-hooks.sh` | `result: 65 passed, 0 failed` | `evidence.jsonl:14` | ✅ PASS |
| PG-01 | `node --test plugins/karvey/tests/page/` | `# tests 22` · `# pass 22` · `# fail 0` | `evidence.jsonl:15` | ✅ PASS |
| LT-01 | `python3 plugins/karvey/scripts/lint-plugin.py` | `0 errors, 3 warnings (50 checks)` — the warnings are L-18 advisory counts on the older changes | `evidence.jsonl:16` | ✅ PASS |
| VD-01 | `python3 plugins/karvey/scripts/karvey-state.py validate --all --root .` | `mode: advisory · 5 files · 0 errors · 27 warnings` | `evidence.jsonl:17` | ✅ PASS |
| LT-02 | `python3 plugins/karvey/scripts/lint-plugin.py --list` (REQ claims resolve) | exit 0 | `evidence.jsonl:18` | ✅ PASS |
| TR-01 | `python3 plugins/karvey/scripts/karvey-trace.py wave2-structural --base origin/main --write --check` | `coverage: 97/97 (pass, mode warn)` · `traceability.md` written | `evidence.jsonl:19` | ✅ PASS |

Integration (inside UT-01): `test_wave2_flow.py` (init → lane → three `approve-gate` → trailer commits →
`release-gate check` pass; AC-4, AC-5) and `test_patch_lane_flow.py` (one human gate; a migration refused at
`lane set`; AC-2) — both PASS.

## Results per requirement (REQ-W2-001..088)

**88 PASS · 0 FAIL · 0 PENDING** (the five manual ones closed at QA on 2026-09-26 by the headless runs under `qa/manual/`, F-08). The 9 MODIFIED Wave 1 requirements are green in `traceability.md`
(coverage 97/97). "Verified by" names the test files that tag the requirement (`@req` / `test_REQ_*`, or a guard
table's case tags); the last result comes from the evidence line shown.

| Requirement | Title | Verified by | Result |
|---|---|---|---|
| REQ-W2-001 | Gate outcomes are recorded | `test_state_outcomes.py` · evidence.jsonl:11 | PASS |
| REQ-W2-002 | Deploy records | `test_postdeploy.py`, `test_state_deploys.py` · evidence.jsonl:11 | PASS |
| REQ-W2-003 | Metrics per lane and period | `test_metrics.py` · evidence.jsonl:11 | PASS |
| REQ-W2-004 | Missing data is stated, never zero | `test_metrics.py` · evidence.jsonl:11 | PASS |
| REQ-W2-005 | Read-only, reproducible, machine-readable | `test_metrics.py` · evidence.jsonl:11 | PASS |
| REQ-W2-006 | Baseline before the process changes | `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-007 | Actual time through the tracker adapter | `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-008 | The retro works on the method's artifacts | manual: retro-from-metrics.md · `qa/manual/retro-from-metrics-2026-09-26.md` (run 2, after BUG-80) · `test_metrics.py` `RetroActionOwner` | PASS |
| REQ-W2-009 | Actions are followed up; per-person analysis is optional | manual: retro-from-metrics.md · `qa/manual/retro-from-metrics-2026-09-26.md` | PASS |
| REQ-W2-010 | 4.0 readiness report | `test_metrics.py`, `test_modes.py` · evidence.jsonl:11 | PASS |
| REQ-W2-011 | Lanes as data | `test_lanes.py`, `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-012 | Lane chosen at init with objective questions | `test_lanes.py` · evidence.jsonl:11 | PASS |
| REQ-W2-013 | Objective criterion of the `patch` lane | `test_lanes.py`, `test_patch_lane_flow.py`, `test_state_lane.py` · evidence.jsonl:11 | PASS |
| REQ-W2-014 | The `patch` path | `test_patch_lane_flow.py`, `test_release_gate.py`, `test_state_lane.py` · evidence.jsonl:11 | PASS |
| REQ-W2-015 | Lane-skipped phases are recorded automatically | `test_state_lane.py` · evidence.jsonl:11 | PASS |
| REQ-W2-016 | Lane changes: up freely, down only by the human | `test_state_lane.py` · evidence.jsonl:11 | PASS |
| REQ-W2-017 | The diff is checked against its lane | `test_lanes.py`, `test_state_lane.py` · evidence.jsonl:11 | PASS |
| REQ-W2-018 | Hotfix lane preconditions are consistent | `test_state_lane.py` · evidence.jsonl:11 | PASS |
| REQ-W2-019 | A change without a lane keeps today's pipeline | `test_lanes.py`, `test_schema_w2.py`, `test_state_lane.py` · evidence.jsonl:11 | PASS |
| REQ-W2-020 | The owner's global instruction diff for the `patch` lane | inspection: `global-instructions.diff` is in the change folder; nothing was written outside the repository (owner applies it, E1.F13.T8) | PASS |
| REQ-W2-021 | Lane is visible | `test_context_gate.py`, `test_lint_plugin.py`, `test_state_lane.py` · evidence.jsonl:11 | PASS |
| REQ-W2-022 | Where judges run | `test_judges.py` · evidence.jsonl:11 | PASS |
| REQ-W2-023 | Clean context and closed inputs | `test_judges.py`, `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-024 | One rubric and lenses per phase | `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-025 | A finding without a citation is discarded | `test_judges.py` · evidence.jsonl:11 | PASS |
| REQ-W2-026 | Judges observe; the iterate skill routes | `test_judges.py` · evidence.jsonl:11 | PASS |
| REQ-W2-027 | The gate summary carries the verdicts | `test_context_gate.py` · evidence.jsonl:11 | PASS |
| REQ-W2-028 | Advisory by default; blocking is opt-in | `test_state_judges.py` · evidence.jsonl:11 | PASS |
| REQ-W2-029 | Cross-model preferred, intra-model declared | `test_judges.py`, `test_schema_w2.py`, `test_state_judges.py` · evidence.jsonl:11 | PASS |
| REQ-W2-030 | Judge cost is measured, never capped | `test_judges.py`, `test_state_judges.py` · evidence.jsonl:11 | PASS |
| REQ-W2-031 | Judges per lane | `test_judges.py`, `test_lanes.py` · evidence.jsonl:11 | PASS |
| REQ-W2-032 | The fiscal before `qa.approved` | `test_judges.py` · evidence.jsonl:11 | PASS |
| REQ-W2-033 | Acceptance of judge findings is recorded | `test_judges.py` · evidence.jsonl:11 | PASS |
| REQ-W2-034 | Three gates per feature | `test_lint_plugin.py`, `test_state_gates.py`, `test_wave2_flow.py` · evidence.jsonl:11 | PASS |
| REQ-W2-035 | One question per gate | `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-036 | A merged gate records every phase's approval | `test_state_gates.py`, `test_wave2_flow.py` · evidence.jsonl:11 | PASS |
| REQ-W2-037 | The *how* gate carries a one-page summary | `test_context_gate.py` · evidence.jsonl:11 | PASS |
| REQ-W2-038 | Continuous execution between gates | `test_state_outcomes.py` · evidence.jsonl:11 | PASS |
| REQ-W2-039 | Granular gates remain available | `test_state_gates.py` · evidence.jsonl:11 | PASS |
| REQ-W2-040 | `-y` is an automatic approval, never production | `test_context_gate.py`, `test_lint_plugin.py`, `test_metrics.py`, `test_schema_w2.py`, `test_state_gates.py`, `test_state_outcomes.py` · evidence.jsonl:11 | PASS |
| REQ-W2-041 | Grill asks in batches | manual: grill-batches.md · `qa/manual/grill-batches-2026-09-26.md` | PASS |
| REQ-W2-042 | *Request changes* keeps the phase and records why | `test_state_outcomes.py` · evidence.jsonl:11 | PASS |
| REQ-W2-043 | Every commit carries the change trailer | `test_lint_plugin.py`, `test_manifest.py` · evidence.jsonl:11 | PASS |
| REQ-W2-044 | Missing trailers are detected at commit time | `trailer.json` · evidence.jsonl:13 (JUnit test-results/tables.xml) | PASS |
| REQ-W2-045 | The release manifest | `test_lint_plugin.py`, `test_manifest.py`, `test_release_gate.py`, `test_wave2_flow.py` · evidence.jsonl:11 | PASS |
| REQ-W2-046 | Manifest verdict | `prod-gate.json`, `test_release_gate.py`, `test_wave2_flow.py` · evidence.jsonl:11 · evidence.jsonl:13 (JUnit test-results/tables.xml) | PASS |
| REQ-W2-047 | The PR lists every change; each gets its approval | `prod-gate.json`, `test_release_gate.py`, `test_state_gates.py` · evidence.jsonl:11 · evidence.jsonl:13 (JUnit test-results/tables.xml) | PASS |
| REQ-W2-048 | Integration by PR | `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-049 | Branch mode, trunk recommended | `test_project.py` · evidence.jsonl:11 | PASS |
| REQ-W2-050 | A release branch as the way out | `test_release_gate.py` · evidence.jsonl:11 | PASS |
| REQ-W2-051 | `approvals.deploy` is retired | `test_state_deploys.py`, `test_state_fix.py` · evidence.jsonl:11 | PASS |
| REQ-W2-052 | Where the production OK is written, in order | `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-053 | Deployed without the local ledger | `test_state_deploys.py` · evidence.jsonl:11 | PASS |
| REQ-W2-054 | Merge on the change branch, before the production PR | `test_lint_plugin.py`, `test_spec_merge_check.py` · evidence.jsonl:11 | PASS |
| REQ-W2-055 | Archive only moves and closes | `test_spec_merge_check.py` · evidence.jsonl:11 | PASS |
| REQ-W2-056 | A deployed change without its delta is visible | `test_context_gate.py`, `test_spec_merge_check.py` · evidence.jsonl:11 | PASS |
| REQ-W2-057 | A test task before each implementation task | `test_trace.py` · evidence.jsonl:11 | PASS |
| REQ-W2-058 | Tests name their requirement | `test_trace.py` · evidence.jsonl:11 | PASS |
| REQ-W2-059 | The test phase starts from the architecture's coverage plan | this test phase: `test_plan.md` lists every §6 row as executed or planned, not executed | PASS |
| REQ-W2-060 | Trace generated by a script | `test_trace.py` · evidence.jsonl:11 | PASS |
| REQ-W2-061 | Evidence lives inside the change | `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-062 | Coverage gate | `test_trace.py` · evidence.jsonl:11 | PASS |
| REQ-W2-063 | QA runs the suite or cites the exact run | QA behaviour: `qa/manual/security-tools-present-2026-09-26.md` (no tests → `Tests: not evaluated`), `qa/manual/merged-gates-three-questions-2026-09-26.md` (`Tests: pass — evidence.jsonl:12 (commit …)`), and this change's own review (`qa/REVISION_PR_*`: every suite run through `karvey-evidence.py`, cited by line) | PASS |
| REQ-W2-064 | QA runs the available tools per category | `test_security_scan.py` · evidence.jsonl:11 | PASS |
| REQ-W2-065 | A missing tool is "not evaluated" | `test_security_scan.py` · evidence.jsonl:11 | PASS |
| REQ-W2-066 | Triage and suppressions carry a reason | `test_security_scan.py` · evidence.jsonl:11 | PASS |
| REQ-W2-067 | Tool invocation is safe | `test_security_scan.py` · evidence.jsonl:11 | PASS |
| REQ-W2-068 | The tools move into the PR pipeline | `test_context_gate.py` · evidence.jsonl:11 | PASS |
| REQ-W2-069 | Release gate as a script | `test_release_gate.py`, `test_wave2_flow.py` · evidence.jsonl:11 | PASS |
| REQ-W2-070 | IDs reserved by a tool | `test_id_tool.py` · evidence.jsonl:11 | PASS |
| REQ-W2-071 | Qualified and unbounded IDs | `test_id_tool.py`, `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-072 | Health score as a script | `test_health_score.py` · evidence.jsonl:11 | PASS |
| REQ-W2-073 | Evidence wrapper | `test_evidence.py` · evidence.jsonl:11 | PASS |
| REQ-W2-074 | Cross-repo decision references validate | `test_schema_w2.py`, `test_state_next.py` · evidence.jsonl:11 | PASS |
| REQ-W2-075 | A post-deploy contract per service | `test_context_gate.py`, `test_postdeploy.py` · evidence.jsonl:11 | PASS |
| REQ-W2-076 | Deploy runs the contract and keeps evidence | `test_lint_plugin.py`, `test_postdeploy.py` · evidence.jsonl:11 | PASS |
| REQ-W2-077 | No contract is "not evaluated" | `test_postdeploy.py` · evidence.jsonl:11 | PASS |
| REQ-W2-078 | A regression proposes the rollback and opens the incident | manual: deploy-postdeploy.md · `qa/manual/deploy-postdeploy-2026-09-26.md` (run 2, after BUG-79) · lint L-53 · `test_postdeploy.py` | PASS |
| REQ-W2-079 | No text requires graphify | `test_lint_plugin.py` · evidence.jsonl:11 | PASS |
| REQ-W2-080 | Import resumes through recorded gates | `test_state_gates.py` · evidence.jsonl:11 | PASS |
| REQ-W2-081 | One decision-log shape | `test_id_tool.py` · evidence.jsonl:11 | PASS |
| REQ-W2-082 | The statusline failure line has a table case | `statusline.json`, `test_lint_plugin.py` · evidence.jsonl:11 · evidence.jsonl:13 (JUnit test-results/tables.xml) | PASS |
| REQ-W2-083 | Every new check has a mode | `test_modes.py` · evidence.jsonl:11 | PASS |
| REQ-W2-084 | Nothing that passed in 3.12 fails in 3.13 | `compat.json`, `test_modes.py` · evidence.jsonl:11 · evidence.jsonl:13 (JUnit test-results/tables.xml) | PASS |
| REQ-W2-085 | 4.0 flips exactly the D-24 defaults | `test_modes.py` · evidence.jsonl:11 | PASS |
| REQ-W2-086 | 4.0 only on measured data | `test_metrics.py` · evidence.jsonl:11 | PASS |
| REQ-W2-087 | Migration to the Wave 2 shape | `test_state_fix.py` · evidence.jsonl:11 | PASS |
| REQ-W2-088 | Built with itself | `test_lint_plugin.py`, `test_manifest.py` · evidence.jsonl:11 | PASS |

## Performance benchmark

**Measured runtime:** terminal, local, `CLAUDE_PLUGIN_ROOT=plugins/karvey`, wall-clock per process, `HOME` and
`XDG_STATE_HOME` in a scratch folder. **Baseline:** the Wave 1 measurement in `docs/test_evidence.md` (the only
timing baseline: `docs/spec/retros/baseline-2026-09-25.json` holds flow metrics, compared below).

| Metric | Current (median / p95) | Wave 1 baseline | Delta (median) | Status |
|--------|------------------------|-----------------|----------------|--------|
| `karvey-hook.sh pre-bash` (`ls 2>/dev/null`), n=20 | 86 / 98 ms | 88 / 92 ms | −2 % | ✅ under the 5 s hook timeout |
| `karvey-session-context.sh startup`, n=10 | 81 / 87 ms | 92 / 95 ms | −12 % | ✅ under the 10 s timeout |
| `karvey-state.py next`, n=10 | 86 / 109 ms | 72 / 84 ms | +19 % | ⚠️ F-09 (gate-mode lookup, F-06) |
| `karvey-context.py`, n=5 | 117 / 118 ms | 92 / 97 ms | +27 % | ⚠️ F-09 (lane, metrics, stall sections) |
| `karvey-release-gate.py check` (new), n=5 | 417 / 451 ms | — | — | ✅ first measurement (8 items, spec-merge subprocess, git) |
| `karvey-trace.py` (new), n=5 | 127 / 130 ms | — | — | ✅ first measurement |

**Flow metrics vs `baseline-2026-09-25.json`** (`karvey-context.py --metrics --from 2026-09-01 --to 2026-09-26
--as-of 2026-09-26`): the same measured change (`team-layer`, the only archived one); every metric equal —
automatic approvals 0 / human 3, ripple 0.0, spec-gap rate 0.0 — except throughput 0.28 → 0.27 per week (the
window is one day longer); the others stay `n/a` with the same reasons. `--readiness`: `not ready: 0 of 4 measured
changes`; `schema.strict` would refuse 3 changes (computed).

## Manual agent-behaviour scripts

**Not run in this phase** (the seven of architecture §6.4, listed in `test_plan.md`): each needs a real session with
the branch plugin, and a session started from here would write under the user configuration. Per D-19 they are the
owner's headless run before QA; evidence goes to `docs/spec/changes/wave2-structural/qa/manual/<script>-<date>.md`.

## Findings from this phase

| ID | Type | What | State |
|----|------|------|-------|
| F-06 | bug | Merged gates unreachable past one phase (found by `test_wave2_flow.py` during impl) — fixed with regression `test_state_gates.py` `MergedGateAdvance` | fixed in impl; `BUG-NN` for `karvey-iterate` |
| F-07 | emergent | The trace reads guard tables and manual scripts; coverage counts the 9 MODIFIED REQ-W1 (97, not 88) | open |
| F-08 | emergent | 5 requirements verified only by manual scripts / QA behaviour: PENDING, not PASS | closed (QA, qa/manual/) |
| F-09 | emergent | `next` +19 %, dashboard +27 % against the Wave 1 medians; far under budget | open |

No test failed in the final run, so no new regression test was generated in this phase (F-06's regression tests
were written with its fix).

## Summary

| Category | Total | PASS | FAIL | Pending |
|----------|-------|------|------|---------|
| Unit (incl. 2 integration suites) | 1017 | 1017 | 0 | — |
| Regression | 10 | 10 | 0 | — |
| Hook commands | 65 | 65 | 0 | — |
| Guard table runs | 474 | 474 | 0 | — |
| Page (node) | 22 | 22 | 0 | — |
| Lint checks / validate files | 50 / 5 | 0 errors | 0 | — |
| Requirements REQ-W2 | 88 | 83 | 0 | 5 (manual) |
| Coverage gate (ADDED + MODIFIED) | 97 | 97 | 0 | — |
| Manual scripts | 7 | — | — | 7 (owner, D-19) |
