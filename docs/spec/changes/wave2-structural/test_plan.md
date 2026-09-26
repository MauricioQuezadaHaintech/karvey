# Test Plan: wave2-structural

> PHASE 9 (`karvey-test`). Contract: `architecture.md` §6 (test coverage plan). Evidence:
> `test_evidence.md` in this folder; every command ran through `karvey-evidence.py` (`evidence.jsonl`);
> the requirement → test map is `traceability.md` (generated).

## Scope
Requirements: REQ-W2-001..088 (ADDED) and the 9 MODIFIED Wave 1 requirements of `spec-delta.md` (REQ-W1-006, 007,
009, 034, 035, 042, 051, 061, 067). Layers: Backend (plugin scripts, library, schemas, hooks, skill and rule text).
Target: `cli` — the runtime is a terminal on the local machine; no cloud, no UI (the method page is static).

## Coverage plan rows (architecture §6) and their state

| Row | Kind | Command / artifact | State |
|---|---|---|---|
| §6.1 unit suites (21 files: lanes, state lane/outcomes/gates/deploys/judges, schema_w2, modes, metrics, context_gate, judges, manifest, release_gate, trace, security_scan, id_tool, health_score, evidence, postdeploy, spec_merge_check, lint_plugin) | unit | `python3 -m unittest discover -s plugins/karvey/tests/unit` | executed |
| §6.2 `trailer.json` | guard table | `python3 plugins/karvey/tests/hooks/run_tables.py --junit …` | executed |
| §6.2 `prod-gate.json` manifest cases (`pgm-01..08`) | guard table | same run | executed |
| §6.2 `compat.json` (74 Wave 1 allow cases under 3.13 defaults) | guard table | same run | executed |
| §6.2 `statusline.json` failure-line case | guard table | same run | executed |
| §6.3 regression index | regression | `python3 -m unittest discover -s plugins/karvey/tests/regression` | executed (no Wave 2 BUG-NN closed in impl: no new row) |
| §6.3 integration `test_wave2_flow.py` (AC-4, AC-5) | integration | unit run | executed |
| §6.3 integration `test_patch_lane_flow.py` (AC-2) | integration | unit run | executed |
| hook commands | shell | `KARVEY_SKIP_TABLES=1 bash plugins/karvey/hooks/tests/test-hooks.sh` | executed |
| method page | node | `node --test plugins/karvey/tests/page/` | executed |
| lint (L-01..L-54) and `--list` REQ claims | lint | `python3 plugins/karvey/scripts/lint-plugin.py` · `--list` | executed |
| schema of every `spec.json` / `project.json` | validate | `python3 plugins/karvey/scripts/karvey-state.py validate --all --root .` | executed |
| coverage gate and trace | script | `python3 plugins/karvey/scripts/karvey-trace.py wave2-structural --base origin/main --write --check` | executed |
| performance benchmark (hooks and CLIs, medians) | benchmark | scratch script, n = 5..20 per command | executed |
| §6.4 `judges-gate.md` | manual | real session, headless | planned, not executed — owner run before QA (D-19) |
| §6.4 `merged-gates-three-questions.md` | manual | real session, headless | planned, not executed — owner run before QA (D-19) |
| §6.4 `grill-batches.md` | manual | real session | planned, not executed — owner run before QA (D-19) |
| §6.4 `retro-from-metrics.md` | manual | real session | planned, not executed — owner run before QA (D-19) |
| §6.4 `import-through-gates.md` | manual | real session | planned, not executed — owner run before QA (D-19) |
| §6.4 `deploy-postdeploy.md` | manual | real session + local HTTP server | planned, not executed — owner run before QA (D-19) |
| §6.4 `security-tools-present.md` | manual | real session with real scanners installed | planned, not executed — owner run before QA (D-19) |

Why the manual rows are not executed here: each needs a separate real agent session with the branch plugin; a
session started from this one would write its transcript under the user configuration, which this run may not
touch. The requirements they alone verify are listed `PENDING (manual)` in `test_evidence.md` (finding F-08).
