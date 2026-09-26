# Test Evidence: project-upgrade

**Date:** 2026-09-25 13:25–13:45 UTC
**Environment:** local (worktree of `feature/project-upgrade`), Linux, Python 3.12.3, node 20.20.2, git 2.43.0,
Claude Code CLI 2.1.282
**Stack:** Python 3 stdlib (`unittest`), bash hooks, node (`node --test`), git
**Targets:** `cli`
**E2E runtime:** terminal: real headless `claude -p` sessions with the branch plugin in a throw-away repository
with a bare local origin (`qa/manual/e2e-2026-09-25.md`)
**Executed by:** maintainer agent, headless under D-21

## Whole-repo suites

### S-01..S-07 — first run (before the fixes)
**Result: ✅ PASS**

Request:
```
python3 -m unittest discover -s plugins/karvey/tests/unit
python3 -m unittest discover -s plugins/karvey/tests/regression
bash plugins/karvey/hooks/tests/test-hooks.sh
python3 plugins/karvey/tests/hooks/run_tables.py
node --test plugins/karvey/tests/page/
python3 plugins/karvey/scripts/lint-plugin.py
python3 plugins/karvey/scripts/karvey-state.py validate --all --root .
```

Response:
```
Ran 860 tests in 53.410s — OK                                            (exit 0)
Ran 10 tests in 0.287s — OK                                              (exit 0)
guard tables: 325 cases, 396 runs (71 nopy), 396 passed, 0 failed
result: 66 passed, 0 failed                                              (exit 0)
guard tables: 325 cases, 396 runs (71 nopy), 396 passed, 0 failed        (exit 0)
# tests 22  # pass 22  # fail 0                                         (exit 0)
0 errors, 5 warnings (39 checks)                                         (exit 0)
mode: advisory · 5 files · 0 errors · 33 warnings                        (exit 0)
```

Notes: the 5 lint warnings are the expected ones while `[Unreleased]` holds the change: L-37 (upgrade surface
changed since 3.11.4, F-04), L-38 (`since` 3.13.0 newer than `plugin.json`, F-01) and three L-18 advisory
validation warnings of other changes.

### S-01..S-07 — final run (after the fixes F-05, F-06, F-07, F-10)
**Result: ✅ PASS**

Response:
```
Ran 857 tests in 36.954s — OK            (+6 regression tests of F-05, F-06, F-07; −9 duplicate L-38 runs, F-10)
Ran 10 tests — OK
test-hooks.sh: 66 passed, 0 failed
guard tables: 325 cases, 396 runs (71 nopy), 396 passed, 0 failed
page: 22/22
lint: 0 errors, 5 warnings (39 checks)
validate: 0 errors · 33 warnings (project-upgrade/spec.json: 0 errors, 0 warnings)
```

## Unit tests — Backend

### UT-BE-01..07 — session table ss-24..ss-35 (REQ-UP-001..006)
**Result: ✅ PASS (15 runs, 3 of them nopy)**

Request: `python3 plugins/karvey/tests/hooks/run_tables.py --only session -v`

Response:
```
ok   session/ss-24-offer-on-version-change
ok   session/ss-25-offer-absent-record
ok   session/ss-26-no-offer-on-resume
ok   session/ss-27-silent-outside-karvey           ok [nopy]
ok   session/ss-28-bare-docs-spec-silent           ok [nopy]
ok   session/ss-29-declined-no-offer
ok   session/ss-30-empty-plan-records-seen
ok   session/ss-31-budget-exceeded-offers
ok   session/ss-32-bad-catalogue-one-line
ok   session/ss-33-bounds-with-offer
ok   session/ss-34-worktree-shares-record
ok   session/ss-35-degraded-no-python              ok [nopy]
```

### UT-BE-08..13 — the upgrade suites (REQ-UP-001, 004, 007..029)
**Result: ✅ PASS (119 tests)**

Request: `python3 -m unittest test_upgrade_<suite>` in `plugins/karvey/tests/unit`

Response:
```
test_upgrade_catalogue.py  Ran 12 tests — OK
test_upgrade_plan.py       Ran 19 tests — OK
test_upgrade_apply.py      Ran 27 tests — OK
test_upgrade_steps.py      Ran 29 tests — OK
test_upgrade_seen.py       Ran 11 tests — OK
test_upgrade_cli.py        Ran 21 tests — OK   (15 + 6 regression)
```

### UT-BE-14 — linter L-37, L-38, L-39 (REQ-UP-030..032)
**Result: ✅ PASS**

Request: `python3 -m unittest -v test_lint_plugin` (classes `L37`, `L38`, `L39`)

Response (excerpt):
```
L37.test_unchanged_surface_passes ... ok
L37.test_changed_under_unreleased_is_a_warning_listing_the_files ... ok
L37.test_a_new_release_without_a_declaration_is_an_error ... ok
L37.test_declaration_or_step_plus_refreshed_fingerprint_passes ... ok
L38.test_missing_risk_names_the_step ... ok
L38.test_direct_writes_in_a_step_function_fail ... ok
L38.test_a_non_human_fix_reading_the_home_fails ... ok
L39.test_readme_section_removed ... ok
L39.test_hooks_readme_section_removed ... ok
L39.test_readme_section_without_the_decline ... ok
```

Notes: `L39` subclassed `L38`, so the 9 L-38 tests also ran a second time under `L39` (F-10, fixed: shared base `UpgradeMiniPlugin`).

### UT-BE-15 — no `shell=True`
**Result: ✅ PASS** — part of S-01 (`test_no_shell_true`).

## E2E Tests (terminal)

Full transcripts summarised with request/response per step in `qa/manual/e2e-2026-09-25.md` and
`qa/manual/upgrade-skill-2026-09-25.md`.

### Flow 1: offer → accept → pick → dry-run → apply → commit → push → PR offered
**Result: ❌ FAIL on the first run (F-05, F-06) → ✅ PASS on the re-run after the fixes**

| Step | Action | Result | Status |
|---|---|---|---|
| 1 | new session, no seen record | offer `Karvey → 3.11.4` in the startup context; asked; nothing recorded | ✅ |
| 2 | "yes, show me the plan" | skill table = the tool's 6 rows; no offer on resume | ✅ |
| 3 | "recommended" | `seen --accept`, `branch` → `chore/karvey-upgrade-3.11.4` from `origin/dev`, dry-run, one confirmation | ✅ |
| 4 | "yes, apply" | `apply --preview`, `commit` with `Steps`/`Picked-by`/`Picked-at`; title `3.11.4 → 3.11.4` | ❌ F-05 → ✅ `none → 3.11.4` |
| 5 | "push and open the PR" | the skill's `git push -u origin "$UB"` blocked by the prod-gate; literal push OK; `gh` unauthenticated → exact `gh pr create` offered, no merge | ❌ F-06 → ✅ |

Actual runtime used: terminal (`claude -p`, CLI 2.1.282).

### Flow 2: second session in the same clone
**Result: ✅ PASS** — no `Karvey (upgrade)` line; `seen --show` → `accepted 3.11.4`.

### Flow 3: decline in a fresh clone, then a version change
**Result: ✅ PASS** — decline recorded (`declined 3.11.4`), no branch; next session no offer; after the record's
version was edited to 3.11.3, the offer `3.11.3 → 3.11.4` is back.

### Flow 4: manual skill script (6 cases)
**Result: ✅ PASS 6/6**

### Re-run (clone3) after the fixes
**Result: ✅ PASS** — diffs verbatim; `none → 3.11.4`; the skill's literal push passes the prod-gate; the push
is then rejected as non-fast-forward because Flow 1 already pushed the same branch name from another clone: the
commit stays local and the exact retry command is printed (the REQ-UP-018 error scenario, observed live; F-08).

## Requirement results (REQ-UP-001..032)

| REQ-UP | Evidence | Result |
|---|---|---|
| 001 | ss-25, ss-34; `test_upgrade_seen` (read-only git dir); E2E Flow 1 step 1 (unanswered → no record) | ✅ PASS |
| 002 | ss-24, ss-25, ss-26; E2E Flow 1 steps 1–2, Flow 3 step 4 | ✅ PASS |
| 003 | ss-27, ss-28 (+ nopy); E2E Case 5 (plain repo: empty startup context) | ✅ PASS |
| 004 | ss-29; `test_upgrade_seen`; E2E Flow 3 | ✅ PASS |
| 005 | ss-30, ss-31 | ✅ PASS |
| 006 | ss-32, ss-33, ss-35 (+ nopy); benchmark below | ✅ PASS |
| 007 | `test_upgrade_plan` (seen 3.0.0 vs 3.11.4 → identical plans) | ✅ PASS |
| 008 | `test_upgrade_catalogue`; L-38 | ✅ PASS |
| 009 | `test_upgrade_plan` (`--json` rows, check failed exit 1); E2E Case 1 | ✅ PASS |
| 010 | `test_upgrade_plan` checksums; L-38 mutation tests; E2E Case 1 (tree clean) | ✅ PASS |
| 011 | `test_upgrade_apply`; E2E Flow 1 (only the 3 picked steps written) | ✅ PASS |
| 012 | `test_upgrade_apply` (preview digest, confirm-no-preview); E2E Flow 1 step 3–4 | ✅ PASS |
| 013 | `test_upgrade_apply`, `test_upgrade_cli`; E2E Flow 1 (commit on `chore/karvey-upgrade-3.11.4`, `dev` unchanged) | ✅ PASS |
| 014 | `test_upgrade_apply` (double apply → nothing to do) | ✅ PASS |
| 015 | `test_upgrade_apply`; E2E (statusline shown, not applied; fake home byte-identical) | ✅ PASS |
| 016 | `test_upgrade_apply` (home byte-identical, symlink escape); L-38 | ✅ PASS |
| 017 | `test_upgrade_apply` (step 2 of 3 fails → report + re-plan) | ✅ PASS |
| 018 | `test_upgrade_cli`; E2E Flow 1 (one commit naming the ids, PR offered without tooling, no merge) and the re-run (push rejected → commit local + retry command) | ✅ PASS after F-05/F-06 |
| 019 | `test_upgrade_apply` (`dev; rm -rf ~` refused naming the source); `test_no_shell_true` | ✅ PASS |
| 020 | `test_upgrade_steps` (`schema-migrate`, `-proposed`); E2E diffs | ✅ PASS |
| 021 | `test_upgrade_steps` (`team-settings`, placeholders) | ✅ PASS |
| 022 | `test_upgrade_steps` (`legacy-shims` + guard tables on the fixture) | ✅ PASS |
| 023 | `test_upgrade_steps` (`statusline-launcher`); E2E (versioned statusline in the fake home → human row) | ✅ PASS |
| 024 | `test_upgrade_steps` (`changes-in-flight`); E2E (report row, archived change not listed) | ✅ PASS |
| 025 | `test_upgrade_steps` (`global-config` diff, unreadable) | ✅ PASS |
| 026 | `test_upgrade_steps` (`enforcement-defaults`); E2E diff (`prod_gate_hook`, `plan_marker_ttl_min`) | ✅ PASS |
| 027 | manual Cases 1, 2 | ✅ PASS |
| 028 | `test_upgrade_cli`; manual Cases 3, 6; E2E Flow 1 | ✅ PASS after F-05/F-07 |
| 029 | manual Cases 4, 5 | ✅ PASS |
| 030 | `test_lint_plugin` L37; whole-repo lint (L-37 warning during `[Unreleased]`) | ✅ PASS |
| 031 | `test_lint_plugin` L38; whole-repo lint | ✅ PASS |
| 032 | `test_lint_plugin` L39; whole-repo lint; README / hooks README read in review | ✅ PASS |

**32 of 32 PASS** (REQ-UP-018 and 028 after the fixes of this phase).

## Performance benchmark (baseline)

**Measured runtime:** terminal, `bash plugins/karvey/hooks/karvey-session-context.sh startup` with
`CLAUDE_PROJECT_DIR` = the legacy fixture clone and `HOME` = the fake home; 20 runs after one warm-up.

| Metric | Current run | Previous baseline | Delta | Status |
|---|---|---|---|---|
| startup hook, offer shown (no record; probe until the first applicable step) | median 114.1 ms (min 105.9, max 127.3) | — (first measurement) | — | ✅ |
| startup hook, no offer (record = installed; no probe) | median 112.8 ms (min 104.1, max 158.0) | — | — | ✅ |
| startup hook outside a Karvey project (reference) | median 83.8 ms (min 80.4, max 89.8) | — | — | ✅ |
| full `karvey-upgrade.py plan --json` (all 8 steps; the probe's worst case) | 0.08–0.10 s (5 runs) | — | — | ✅ |

Notes: the offer costs ≈ 1 ms over the no-offer path on this fixture (the probe stops at the first hit), well
inside the 1500 ms `upgrade_probe_ms` budget and the 10 s hook timeout (REQ-UP-006). Both Karvey-project paths are
≈ 30 ms above the non-Karvey reference because of the project discovery and settings notice, which exist without
this change.

## Generated regression tests

| Regression test ID | Covers bug (original test ID) | Layer | File | Status |
|---|---|---|---|---|
| `regression_project-upgrade_from_after_accept` (`RegressionProjectUpgradeFromVersion`, 3 tests) | F-05 (E2E Flow 1 step 4, manual Case 4) | Backend | `plugins/karvey/tests/unit/test_upgrade_cli.py` | ✅ PASS (3 FAIL on the code before the fix) |
| `regression_project-upgrade_skill_push_literal` (`RegressionProjectUpgradeSkillPush`, 2 tests) | F-06 (E2E Flow 1 step 5) | Backend (skill text × prod-gate) | `plugins/karvey/tests/unit/test_upgrade_cli.py` | ✅ PASS (FAIL on the skill before the fix) |
| `regression_project-upgrade_skill_wording` (`RegressionProjectUpgradeSkillWording`, 1 test) | F-07 (E2E Flow 1 step 3, manual Case 3) | Backend (skill text) | `plugins/karvey/tests/unit/test_upgrade_cli.py` | ✅ PASS |
| `test_lint_plugin.L38` / `L39` on the shared base `UpgradeMiniPlugin` | F-10 (UT-BE-14: L-38 tests run twice) | Backend (test code) | `plugins/karvey/tests/unit/test_lint_plugin.py` | ✅ PASS (`L39` runs 7, `L38` 9) |

## Summary

| Category | Total | PASS | FAIL |
|---|---|---|---|
| DB | 0 (no DB layer) | — | — |
| Backend (unit suite, whole repo) | 857 | 857 | 0 |
| Backend (guard tables, runs) | 396 | 396 | 0 |
| Backend (test-hooks.sh) | 66 | 66 | 0 |
| Frontend (page, node) | 22 | 22 | 0 |
| Regression (index) | 10 | 10 | 0 |
| E2E (flows 1–3 + re-run) | 4 | 4 | 0 (Flow 1 failed first, fixed) |
| Manual skill script | 6 | 6 | 0 |
| **Total** | **1361** | **1361** | **0** |

Requirements: **32/32 PASS**. Findings: F-05, F-06, F-07, F-10 (bugs, fixed with regression tests), F-08
(spec-gap), F-09 (emergent).
