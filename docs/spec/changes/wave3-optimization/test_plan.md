# Test Plan: wave3-optimization

**Contract:** `architecture.md` §6 (test coverage plan) · **Targets:** `cli` (runtime: terminal) · **Layers:** Backend
(scripts, library, schemas, hooks, skill and rule text), Frontend (the sponsor template and the method page), Infra
(the CI step).

## Scope
Requirements: REQ-W3-001..080 (80) plus the living requirements they modify (REQ-ADP-011, REQ-ADP-031, REQ-W1-009,
REQ-W1-045, REQ-W1-068, REQ-W1-089, REQ-W2-003, REQ-W2-008, REQ-W2-022, REQ-W2-030). Every row below ends the phase
`executed` (with its evidence line in `test_evidence.md`) or `planned, not executed` (with the reason).

## 6.1 Unit suites (`plugins/karvey/tests/unit/`, run as one discover: UT-01)

| Suite | Covers | Status |
|---|---|---|
| `test_context_budget.py` | 001, 002, 010, 011, 012, 071, 072 | executed (UT-01) |
| `test_ci_workflow.py` | 009, 011 | executed (UT-01) |
| `test_contracts.py` | 003, 009 | executed (UT-01) |
| `test_lint_w3.py` (mutation per L-55..L-75) | 004..008, 012, 017, 024, 037, 039, 040, 053, 055, 056, 060, 061, 067..069, 080 | executed (UT-01) |
| `test_orchestrator_routing.py` | 008 | executed (UT-01) |
| `test_effort.py` | 014..017, 074 | executed (UT-01) |
| `test_judges.py` | 032, 039, 077 | executed (UT-01) |
| `test_metrics.py` | 018, 019 | executed (UT-01) |
| `test_stakeholders.py` | 020, 044 | executed (UT-01) |
| `test_sponsor.py`, `test_leakcheck.py` | 021..024, 075, 080 (+ BUG-84 regression) | executed (UT-01) |
| `test_context_report.py` | 025 | executed (UT-01) |
| `test_notify_events.py` | 026, 027, REQ-ADP-011 | executed (UT-01) |
| `test_questions.py` | 028..030 | executed (UT-01) |
| `test_risks.py` | 031, 033, 034 | executed (UT-01) |
| `test_contrast.py`, `test_design_delta.py` | 035, 036, 038, 076 | executed (UT-01) |
| `test_wbs.py` | 040..043 | executed (UT-01) |
| `test_portfolio.py` (no subprocess, no socket, mtimes unchanged, 2 MB cap, sanitised text) | 045..048, 078, 079 | executed (UT-01) |
| `test_context.py` (`spec/` layout, `two spec roots`) | 048, REQ-W1-045 | executed (UT-01) |
| `test_close.py` (step order, effort last, failures reported, step 5 context check, `observed`) | 013, 014, 022, 033 | executed (UT-01) |
| `test_browse_via.py` | 054 | executed (UT-01) |
| `test_state_fix.py` | 044, 063 | executed (UT-01) |
| `test_backlog_wsjf.py` | 049..052 | executed (UT-01) |
| `test_runtime_version.py`, `test_incident_states.py` | 057, 058, REQ-W1-068 | executed (UT-01) |
| `test_settings_line.py` | 059 | executed (UT-01) |
| `test_modes.py` | 061 | executed (UT-01) |
| `test_compat_w3.py` (integration) | 062 | executed (UT-01) |
| `test_page_static.py` (nine languages) | 066..070 | executed (UT-01) |
| `tests/regression/test_incidents.py` (BUG index incl. BUG-84) | REQ-W1-107 | executed (UT-02) |

## 6.2 Tables and page tests

| Suite | Covers | Status |
|---|---|---|
| `tests/hooks/tables/*.json` (statusline capture, session `spec/` layout and `settings invalid`, `compat41-` replays) | 015, 048, 059, 062 | executed (TB-01, JUnit `test-results/tables.xml`) |
| `hooks/tests/test-hooks.sh` | hooks, session context | executed (HK-01) |
| `tests/page/test_page.mjs` (`?lang=ko`, `ko-KR`, `?lang=xx`, `?lang=ja`, alias hash) | 066, 068, 069, REQ-ADP-031 | executed (PG-01) |
| `tests/page/test_sponsor_page.mjs` (no external request, 360/1440 px, print) | 024 | executed (PG-01) |

## 6.3 Manual / E2E (`tests/manual/`)

| Script | Covers | Status |
|---|---|---|
| `one-phase-per-session.md` | 013 | executed in QA 2026-09-27, PASS on the rerun (`qa/manual/one-phase-per-session-2026-09-27.md`; browser-only parts not run: no browser here) |
| `sponsor-at-gate.md` | 022, 023, 024, 075 | executed in QA 2026-09-27, PASS on the rerun (`qa/manual/sponsor-at-gate-2026-09-27.md`; browser-only parts not run: no browser here) |
| `browse-via-agent.md` | 054 | executed in QA 2026-09-27, PASS on the rerun (`qa/manual/browse-via-agent-2026-09-27.md`; browser-only parts not run: no browser here) |
| `design-judge-gate.md` | 037, 039 | executed in QA 2026-09-27, PASS on the rerun (`qa/manual/design-judge-gate-2026-09-27.md`; browser-only parts not run: no browser here) |
| `tracker-wbs.md` | 040, 041, 042 | executed in QA 2026-09-27, PASS on the rerun (`qa/manual/tracker-wbs-2026-09-27.md`; browser-only parts not run: no browser here) |
| `portability-guide-review.md` | 053 | planned, not executed — the script was not written; 053 is covered by L-69 (`test_lint_w3.py`) |

## 6.4 Change-scoped verification

| Check | Covers | Status |
|---|---|---|
| `karvey-context-budget.py order` on this branch's history | 002 | executed (CS-05) |
| `compare` of the two snapshots ≥ 40% | 010 | executed (CS-01, CS-02) |
| `contracts` green | 009 | executed (CS-03) |
| `render --check` | 012 | executed (CS-04) |
| release manifest maps every commit; 114/114 commits carry the trailer | 065 | executed (RG-01 + `git log --grep`) |
| `validate` shows lane `feature-ui`, trunk flow | 073 | executed (VD-01) |
| `spec.json:effort[]` per closed phase | 074 | executed in QA 2026-09-27: first entry at the test close (`n/a`, reason stated); earlier phases `not measured` |
| `sponsor-history.jsonl`, page built with leak check PASS, delivery `no destination declared` | 075 | executed (SP-01) |
| `[Unreleased]` release summary | 064 | executed (inspection; version and date at deploy) |
| trace coverage gate | all | executed (TR-01: 90/90 covered, 87 green + 3 by inspection) |
