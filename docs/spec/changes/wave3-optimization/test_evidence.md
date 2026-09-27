# Test Evidence: wave3-optimization

**Date:** 2026-09-27 (UTC)
**Environment:** local (Linux 6.8, Python 3, node)
**Stack:** Python stdlib scripts, bash hooks, static HTML/JS pages
**Targets:** `cli`
**Runtime:** terminal (the method page and the sponsor page are checked by node:test and html.parser, no browser — D-09)
**Commit under test:** `3448259` (feature/wave3-optimization; 114 commits of this change, every one with `Karvey-Change: wave3-optimization`)
**Plan:** `test_plan.md` (contract: `architecture.md` §6) · **Trace:** `traceability.md` · **Evidence lines:** `evidence.jsonl` (hashes only, no output stored)

## Suite runs (each through `karvey-evidence.py`, after the BUG-84 fix)

| ID | Command | Output (tail) | Evidence | Result |
|----|---------|---------------|----------|--------|
| UT-01 | `python3 -m unittest discover -s plugins/karvey/tests/unit` | `Ran 1360 tests` · `OK` | `evidence.jsonl:34` | ✅ PASS |
| UT-02 | `python3 -m unittest discover -s plugins/karvey/tests/regression` | `Ran 10 tests` · `OK` | `evidence.jsonl:35` | ✅ PASS |
| TB-01 | `python3 plugins/karvey/tests/hooks/run_tables.py --junit …/test-results/tables.xml` | `guard tables: 482 cases, 550 runs (68 nopy), 550 passed, 0 failed` (incl. 70 `compat41-` replays) | `evidence.jsonl:36` | ✅ PASS |
| HK-01 | `KARVEY_SKIP_TABLES=1 bash plugins/karvey/hooks/tests/test-hooks.sh` | `result: 71 passed, 0 failed` | `evidence.jsonl:37` | ✅ PASS |
| PG-01 | `node --test plugins/karvey/tests/page/` | `# pass 35` · `# fail 0` | `evidence.jsonl:38` | ✅ PASS |
| LT-01 | `python3 plugins/karvey/scripts/lint-plugin.py` | `0 errors, 3 warnings (72 checks)` — the warnings are L-18 advisory counts on older changes | `evidence.jsonl:39` | ✅ PASS |
| VD-01 | `python3 plugins/karvey/scripts/karvey-state.py validate --all` | `mode: advisory · 6 files · 0 errors · 27 warnings` | `evidence.jsonl:40` | ✅ PASS |
| CS-01 | `karvey-context-budget.py compare context-size-4.0.0.json context-size-4.1.0.json --target-median 40` | `median reduction: 56.1% (target 40%)` | `evidence.jsonl:41` | ✅ PASS |
| CS-02 | `karvey-context-budget.py compare context-size-4.0.0.json --live --target-median 40` | `median reduction: 56.1%` (the tree matches the snapshot) | `evidence.jsonl:42` | ✅ PASS |
| CS-03 | `karvey-context-budget.py contracts` | `79 of 79 (phase, contract) pairs covered` | `evidence.jsonl:43` | ✅ PASS |
| CS-04 | `karvey-context-budget.py render --check` | `10 generated block(s) current` | `evidence.jsonl:44` | ✅ PASS |
| CS-05 | `karvey-context-budget.py order --baseline docs/spec/retros/context-size-4.0.0.json --change wave3-optimization` | baseline `a9b4828773` precedes the 4 reorganisation commits | `evidence.jsonl:45` | ✅ PASS |
| RG-01 | `karvey-release-gate.py manifest` | every commit mapped; `QA missing` for this change (expected before QA; mode warn) | `evidence.jsonl:46` | ✅ PASS |
| WB-01 | `karvey-trace.py wave3-optimization --wbs` | `101 task(s) under 12 Feature(s) + E1.DEPLOY · 0 issue(s)` | `evidence.jsonl:47` | ✅ PASS |
| SP-01 | `karvey-sponsor.py deliver wave3-optimization` | `not delivered: no destination declared` | `evidence.jsonl:48` | ✅ PASS |
| TR-01 | `karvey-trace.py wave3-optimization --write --check` | `90 requirement(s), 90 covered, 0 uncovered, 0 without commit` · `coverage: 87/90 (warn)` — the three not green are the change-scoped 064, 065, 073, verified by inspection below | `evidence.jsonl:49` | ✅ PASS |

Earlier runs of the same commands (`evidence.jsonl:17..33`, before the fix) were all exit 0 except
`karvey-sponsor.py build wave3-optimization --gate how` (`evidence.jsonl:32`, exit 1) — BUG-84 below.

## Context size: 4.0.0 baseline vs 4.1.0 (REQ-W3-001, 002, 009, 010)

`docs/spec/retros/context-size-4.0.0.json` (committed in `a9b4828`, before any move) against
`docs/spec/retros/context-size-4.1.0.json` (`closure_max` bytes per phase skill; tokens are estimated as bytes ÷ 4):

```
skill                       before B     after B    change  reason (below target)
karvey                        170975       30870    -81.9%  
karvey-architecture           132127       45667    -65.4%  
karvey-archive                 95938       55415    -42.2%  
karvey-deploy                 128318       76156    -40.7%  
karvey-design-graphic          99645       36777    -63.1%  
karvey-impl                   116823       57645    -50.7%  
karvey-infra                  128534       43720      -66%  
karvey-init                   130994       60211      -54%  
karvey-mockup                  95911       25834    -73.1%  
karvey-qa                     128914       71620    -44.4%  
karvey-requirements           109114       56290    -48.4%  
karvey-tasks                   92550       40605    -56.1%  
karvey-test                    99686       38612    -61.3%  
median reduction: 56.1% (target 40%)
```

**Median reduction 56.1%** (target 40%); every phase is above the target, so no per-phase reason is needed
(`contracts.json:reasons` is empty); the session hook is unchanged (879 bytes before and after). **PASS.**

## Results per requirement (REQ-W3-001..080)

**80 PASS · 0 FAIL · 0 PENDING** (REQ-W3-042 and 074 closed in QA, 2026-09-27). "Verified by" names the test files that tag the requirement
(`@req` / `test_REQ_*`, or a guard table's case tags) and the evidence line of the run; the change-scoped
requirements are verified by inspection of this change's own artifacts.

| Requirement | Title | Verified by | Result |
|---|---|---|---|
| REQ-W3-001 | Per-phase instruction size is measured | `test_context_budget.py` · evidence.jsonl:34 | PASS |
| REQ-W3-002 | Baseline before the reorganisation | `test_context_budget.py` · evidence.jsonl:34 | PASS |
| REQ-W3-003 | A core of hard contracts | `test_contracts.py`, `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-004 | Each skill declares a closed load list | `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-005 | Rules do not load each other | `test_context_budget.py`, `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-006 | Tracker detail loaded only for the team's tool | `test_context_budget.py`, `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-007 | Rare paths move to references | `test_context_budget.py`, `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-008 | The orchestrator only routes | `test_lint_w3.py`, `test_orchestrator_routing.py` · evidence.jsonl:34 | PASS |
| REQ-W3-009 | No hard contract is lost | `test_ci_workflow.py`, `test_contracts.py` · evidence.jsonl:34 | PASS |
| REQ-W3-010 | The budget is a target, measured after | `test_context_budget.py` · evidence.jsonl:34 | PASS |
| REQ-W3-011 | Size checked in CI | `test_ci_workflow.py`, `test_context_budget.py` · evidence.jsonl:34 | PASS |
| REQ-W3-012 | Per-phase rule lists are generated, not hand-kept | `test_context_budget.py`, `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-013 | One phase per session is the declared pattern | `test_close.py` · evidence.jsonl:34 · + manual `one-phase-per-session.md` PASS (`qa/manual/one-phase-per-session-2026-09-27.md`) | PASS |
| REQ-W3-014 | Effort recorded at each phase close | `test_close.py`, `test_effort.py`, `test_schema_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-015 | Cost source captured outside the model | `statusline.json`, `test_effort.py` · evidence.jsonl:34,36 | PASS |
| REQ-W3-016 | Judge cost kept apart | `test_effort.py`, `test_schema_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-017 | Cost is never a cap | `test_effort.py`, `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-018 | Cost per lane, client and period | `test_metrics.py` · evidence.jsonl:34 | PASS |
| REQ-W3-019 | Outliers in the retro | `test_metrics.py` · evidence.jsonl:34 | PASS |
| REQ-W3-020 | Stakeholders declared in the project | `test_stakeholders.py` · evidence.jsonl:34 | PASS |
| REQ-W3-021 | One page per change, from the artifacts | `test_sponsor.py` · evidence.jsonl:34 | PASS |
| REQ-W3-022 | Published at every gate close | `test_close.py`, `test_sponsor.py` · evidence.jsonl:34 · + manual `sponsor-at-gate.md` PASS (`qa/manual/sponsor-at-gate-2026-09-27.md`) | PASS |
| REQ-W3-023 | Nothing internal leaves | `test_leakcheck.py`, `test_sponsor.py` · evidence.jsonl:34 · + manual `sponsor-at-gate.md` PASS (`qa/manual/sponsor-at-gate-2026-09-27.md`) | PASS |
| REQ-W3-024 | Self-contained, readable page | `test_lint_w3.py` · evidence.jsonl:34 · + manual `sponsor-at-gate.md` PASS (`qa/manual/sponsor-at-gate-2026-09-27.md`) | PASS |
| REQ-W3-025 | The report command | `test_context_report.py` · evidence.jsonl:34 | PASS |
| REQ-W3-026 | "Your turn" events | `test_notify_events.py` · evidence.jsonl:34 | PASS |
| REQ-W3-027 | Notifications are not duplicated | `test_notify_events.py` · evidence.jsonl:34 | PASS |
| REQ-W3-028 | Open questions are recorded | `test_questions.py` · evidence.jsonl:34 | PASS |
| REQ-W3-029 | A question becomes a decision | `test_questions.py` · evidence.jsonl:34 | PASS |
| REQ-W3-030 | Overdue questions are visible | `session.json`, `test_questions.py` · evidence.jsonl:34,36 | PASS |
| REQ-W3-031 | A risk register per change | `test_risks.py` · evidence.jsonl:34 | PASS |
| REQ-W3-032 | The security judge feeds the register | `test_judges.py` · evidence.jsonl:34 | PASS |
| REQ-W3-033 | Risks reviewed before the qa and release gates | `test_close.py`, `test_risks.py` · evidence.jsonl:34 | PASS |
| REQ-W3-034 | Archive closes or moves every risk | `test_risks.py` · evidence.jsonl:34 | PASS |
| REQ-W3-035 | One design system per project | `test_design_delta.py` · evidence.jsonl:34 | PASS |
| REQ-W3-036 | The change declares only its delta | `test_design_delta.py` · evidence.jsonl:34 | PASS |
| REQ-W3-037 | Art catalogue is opt-in | `test_lint_w3.py` · evidence.jsonl:34 · + manual `design-judge-gate.md` PASS (`qa/manual/design-judge-gate-2026-09-27.md`) | PASS |
| REQ-W3-038 | Contrast is computed | `test_contrast.py`, `test_design_delta.py` · evidence.jsonl:34 | PASS |
| REQ-W3-039 | The design score comes from a judge | `test_contrast.py`, `test_judges.py`, `test_lint_w3.py` · evidence.jsonl:34 · + manual `design-judge-gate.md` PASS (`qa/manual/design-judge-gate-2026-09-27.md`) | PASS |
| REQ-W3-040 | Feature means a functional area | `test_lint_w3.py`, `test_wbs.py` · evidence.jsonl:34 · + manual `tracker-wbs.md` PASS (`qa/manual/tracker-wbs-2026-09-27.md`) | PASS |
| REQ-W3-041 | QA and deploy belong to the Epic | `test_lint_w3.py`, `test_wbs.py` · evidence.jsonl:34 · + manual `tracker-wbs.md` PASS (`qa/manual/tracker-wbs-2026-09-27.md`) | PASS |
| REQ-W3-042 | Hierarchy by parent and child | `test_wbs.py` (BUG-97, BUG-98) · manual `tracker-wbs.md` PASS on the rerun (`qa/manual/tracker-wbs-2026-09-27.md`: QA fix tasks as children of `E1.QA`, `[Deploy] sample-wbs@…` under `E1.DEPLOY`, found and reused on a second run) | PASS |
| REQ-W3-043 | Every task belongs to exactly one Feature | `test_wbs.py` · evidence.jsonl:34 | PASS |
| REQ-W3-044 | Client as a first-level field | `test_stakeholders.py` · evidence.jsonl:34 | PASS |
| REQ-W3-045 | A portfolio file lists the repositories | `test_portfolio.py` · evidence.jsonl:34 | PASS |
| REQ-W3-046 | The portfolio view | `test_portfolio.py` · evidence.jsonl:34 | PASS |
| REQ-W3-047 | Read-only and within the reader's access | `test_portfolio.py` · evidence.jsonl:34 | PASS |
| REQ-W3-048 | Both spec layouts are found | `session.json`, `test_context.py`, `test_portfolio.py` · evidence.jsonl:34,36 | PASS |
| REQ-W3-049 | Scoring columns | `test_backlog_wsjf.py` · evidence.jsonl:34 | PASS |
| REQ-W3-050 | `done-direct` state | `test_backlog_wsjf.py` · evidence.jsonl:34 | PASS |
| REQ-W3-051 | The backlog view | `test_backlog_wsjf.py` · evidence.jsonl:34 | PASS |
| REQ-W3-052 | Refinement cadence | `test_backlog_wsjf.py` · evidence.jsonl:34 | PASS |
| REQ-W3-053 | A portability guide, one supported runtime | `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-054 | Browsing can be delegated | `test_browse_via.py` · evidence.jsonl:34 · + manual `browse-via-agent.md` PASS (`qa/manual/browse-via-agent-2026-09-27.md`) | PASS |
| REQ-W3-055 | No OS-only commands | `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-056 | No fixed country time | `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-057 | Neutral incident states with aliases | `test_incident_states.py` · evidence.jsonl:34 | PASS |
| REQ-W3-058 | The loaded version is the one checked | `test_runtime_version.py` · evidence.jsonl:34 | PASS |
| REQ-W3-059 | Team settings are validated | `session.json`, `test_settings_line.py` · evidence.jsonl:34,36 | PASS |
| REQ-W3-060 | Method text names no one environment | `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-061 | Every new check has a mode | `test_lint_w3.py`, `test_modes.py` · evidence.jsonl:34 | PASS |
| REQ-W3-062 | Nothing that passed under 4.0 fails | `compat.json`, `test_compat_w3.py`, `test_effort.py`, `test_schema_w3.py` · evidence.jsonl:34,36 | PASS |
| REQ-W3-063 | Migration to the Wave 3 shape | `test_state_fix.py` · evidence.jsonl:34 | PASS |
| REQ-W3-064 | Measured before and after | inspection: the `[Unreleased]` Wave 3 summary (context size before/after, cost with "not measured", Upgrade list, 4.0 → 4.1 note; `grep -c -E 'not measured|context-size-4.1.0|client-from-tag'` = 8) · lint L-12/L-13/L-19 evidence.jsonl:39 | PASS |
| REQ-W3-065 | Built with itself: the trailer | inspection: 114 of 114 commits of this change carry `Karvey-Change: wave3-optimization` (`git log --grep`); release manifest maps every commit (no `unmapped`) · evidence.jsonl:46 | PASS |
| REQ-W3-066 | Four more languages | `test_page.mjs`, `test_page_static.py` · evidence.jsonl:34,38 | PASS |
| REQ-W3-067 | Every string in every language | `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-068 | Self-contained scripts render | `test_page.mjs` · evidence.jsonl:38 | PASS |
| REQ-W3-069 | Renamed anchors resolve | `test_page.mjs`, `test_lint_w3.py` · evidence.jsonl:34,38 | PASS |
| REQ-W3-070 | The page reflects 4.1 | `test_lint_plugin.py` · evidence.jsonl:34 | PASS |
| REQ-W3-071 | The size tool is reproducible | `test_context_budget.py` · evidence.jsonl:34 | PASS |
| REQ-W3-072 | A missing load-list file fails CI | `test_context_budget.py`, `test_lint_w3.py` · evidence.jsonl:34 | PASS |
| REQ-W3-073 | Built with itself: the lane | inspection: `spec.json:lane` = `feature-ui`, `project.json:branch_flow.mode` = `trunk`; `validate` 0 errors · evidence.jsonl:40 | PASS |
| REQ-W3-074 | Built with itself: its own effort | `spec.json:effort` gained its first entry at the close of the test phase (`karvey-state.py effort wave3-optimization test`, 2026-09-27): `usd`/`tokens` `n/a — statusline not installed` (the agent sessions of this change run without the statusline), review minutes `n/a` — recorded with the reason, never as zero; the phases init … tasks closed before the capture existed and read `not measured (effort record did not exist)` (the error scenario) | PASS |
| REQ-W3-075 | Built with itself: its own sponsor page | inspection: `sponsor-history.jsonl` records the *what* and *how* gates as `no page (generator not built yet)` and the pages built since (sha256); `deliver` → `not delivered: no destination declared` (`channel: none`) · evidence.jsonl:48 | PASS |
| REQ-W3-076 | Design-system conflicts stop the apply | `test_design_delta.py` · evidence.jsonl:34 | PASS |
| REQ-W3-077 | Judge cost measured from the runtime | `test_judges.py` · evidence.jsonl:34 | PASS |
| REQ-W3-078 | The portfolio for one client | `test_portfolio.py` · evidence.jsonl:34 | PASS |
| REQ-W3-079 | From the portfolio to one change | `test_portfolio.py` · evidence.jsonl:34 | PASS |
| REQ-W3-080 | Business wording for states | `test_lint_w3.py`, `test_sponsor.py` · evidence.jsonl:34 | PASS |

### Living requirements this change modifies

| Requirement | Verified by | Result |
|---|---|---|
| REQ-ADP-011 | `test_notify_events.py` | PASS |
| REQ-W1-045 | `session.json`, `test_context.py` | PASS |
| REQ-W1-089 | manual | PASS |
| REQ-ADP-031 | `test_page.mjs` | PASS |
| REQ-W1-009 | `test_state_fix.py` | PASS |
| REQ-W1-068 | `test_incident_states.py` | PASS |
| REQ-W2-003 | `test_metrics.py` | PASS |
| REQ-W2-008 | manual | PASS |
| REQ-W2-022 | `test_judges.py` | PASS |
| REQ-W2-030 | `test_judges.py`, `test_state_judges.py` | PASS |

## Manual agent-behaviour scripts — run in QA (2026-09-27)

Run headless as the maintainer agent (owner-authorised pattern, D-19/D-21/D-28): a throw-away repository with a bare
origin, the branch plugin, `--resume` for multi-turn; the person's answers are the ones each script prescribes. This
host has no browser: the rendered checks are recorded as "not run: no browser here". Each has automated coverage of its scripts (above); the script
checks what the agent does with them. Run each per its header (a throw-away repo, the branch plugin), file the
evidence under `docs/spec/changes/wave3-optimization/qa/manual/<script>-<date>.md` with PASS/FAIL.

| Script | Requirements | What it proves | Status |
|---|---|---|---|
| `plugins/karvey/tests/manual/sponsor-at-gate.md` | 022, 023, 024, 075 | a real gate builds the page once, it opens offline at 360/1440 px and in print, a leak is refused without the value, a failed delivery goes to the outbox | PASS on the rerun (first run FAIL → BUG-96, BUG-100, BUG-102); step 2 rendered checks not run: no browser here |
| `plugins/karvey/tests/manual/design-judge-gate.md` | 037, 039 | a `feature-ui` change without an asset request gets no art catalogue; the judge verdict and the contrast result are in the gate summary | PASS on the rerun (first run FAIL → BUG-95) |
| `plugins/karvey/tests/manual/tracker-wbs.md` | 040, 041, 042 | on the Markdown tracker: Features are areas, phases on the Epic, `E1.QA` / `E1.DEPLOY` found or created once | PASS on the rerun (first run FAIL → BUG-97, BUG-98) |
| `plugins/karvey/tests/manual/browse-via-agent.md` | 054 | `browse.via: agent:<name>` sends a self-contained instruction with declared URLs only; `none` → visual dimension `not evaluated` | PASS on the rerun (first run FAIL → BUG-99); the sending and capture parts not run: no browser or browser agent here |
| `plugins/karvey/tests/manual/one-phase-per-session.md` | 013 | the close offers the checkpoint, recommends a fresh session at the threshold, the hook resumes; `observed` shows no footnote-only rule opened | PASS on the fourth rerun (earlier FAIL → BUG-100, BUG-101, BUG-103, BUG-104, BUG-126, BUG-127) |

## Regression

| Regression test ID | Covers bug | Layer | File | Status |
|---|---|---|---|---|
| `regression_wave3-optimization_sponsor_page_rebuilt` (`Cli.test_BUG_84_the_page_is_rebuilt_at_a_later_gate`) | BUG-84 (SP build, `evidence.jsonl:32`) | Backend | `plugins/karvey/tests/unit/test_sponsor.py` | ✅ PASS (red on the previous code) |
| `Cli.test_BUG_84_a_page_changed_by_another_writer_is_refused_not_overwritten` | BUG-84 | Backend | `plugins/karvey/tests/unit/test_sponsor.py` | ✅ PASS (red on the previous code) |

**BUG-84** — the sponsor page was never rebuilt after the first gate: `karvey-sponsor.py build` wrote it with a
compare-and-swap that expected no file. Found while rebuilding this change's own page (the dogfooding of REQ-W3-075);
fixed in this phase (`3448259`), finding F-104 closed, tracker and indexes updated, RESUELTO with its regression
tests (indexed in `tests/regression/test_incidents.py`). This change's page was rebuilt once after the fix to verify
it on the real change (`sponsor-history.jsonl`, 2026-09-27T13:26 — a rebuild, not a gate close).

## Performance benchmark (baseline)

Target `cli`: the measured figure of this change is the per-phase instruction size above (the 4.1.0 snapshot is the
baseline for the next change); suite durations are in `evidence.jsonl` (`duration_ms`).

## Findings from this phase

- F-104 (`bug`, High) → BUG-84, fixed and closed in this phase.
- The design judge's 18 findings on this change's mockups (F-86..F-103) were routed by `/karvey-iterate` on
  2026-09-27: the delta declares every page value, contrast.json covers 27 pairs (0 below), BUG-86..BUG-89 fixed,
  F-93 and F-96 deferred with reason.
- QA and the manual scripts (2026-09-27): BUG-90..BUG-121, BUG-123, BUG-126, BUG-127 fixed, each with its regression
  test indexed in `tests/regression/test_incidents.py`; see `qa/REVISION_PR_wave3_20260927.md`.
- `karvey-id.py next BUG` reserves on every call: BUG-85 was reserved by a second call and left unused.

## Summary

| Category | Total | PASS | FAIL | PENDING |
|---|---|---|---|---|
| Suite runs | 16 | 16 | 0 | 0 |
| REQ-W3 | 80 | 80 | 0 | 0 |
| Manual scripts | 5 | 5 | 0 | 0 (browser-only parts not run: no browser here) |
| Regression | 44 incidents (BUG-84, BUG-86..121, 123, 126, 127) | all | 0 | 0 |
