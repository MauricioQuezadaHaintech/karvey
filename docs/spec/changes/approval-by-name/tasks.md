# Tasks: approval-by-name (hotfix 3.13.1)

> PHASE 7 (`karvey-tasks`) · Security Tier 2 · Tracker: Markdown (this file + `PLAN.md`).
> Inputs: `architecture.md`, `requirements.md` (REQ-AN-001..007, 010..012), `findings.md` F-01, F-02.

## Summary

| Item | Value |
|---|---|
| Features | 3 (E1.F1..F3) |
| Tasks | 7 (3 Backend, 3 Test, 1 release) |
| Total estimate (AI + review) | 190 min |
| REQ-AN coverage | 10/10 |
| Largest task | 45 min |

## Conventions

- IDs `E1.F{n}.T{n}`. Layers: `[Backend]` plugin scripts, hooks and skill text; `[Test]` tests only.
- Hotfix lane: each BUG fix ships with its regression test, written red first (fails on 3.13.0), in the same PR.
- Each impl commit adds one line under `## [Unreleased]`; the version moves once, in E1.F3.T1.

## E1.F1 — Approval by named change across clones (REQ-AN-001..007 · BUG-158)

- **E1.F1.T1 [Test] 30 min** — Red unit `test_approval_by_name.py` (sibling clone records there; two clones
  refuse and list; unknown word → `<change-id>`; negated phrase never suggests the active change; worktree of the
  same clone; outside a Karvey project; search error fails open; `approve … prod --sha` in the owner) and table
  rows `ap-an-01`, `ap-an-02`. Done: they fail on 3.13.0.
- **E1.F1.T2 [Backend] 45 min** — `approval.clones_holding`, `resolve_prod_scope(anchors=)`, `phrase_change`,
  `resolve_named_elsewhere`; `guards.approval_hook` writes in the owner and handles the non-Karvey session.
  Done: the unit file, `test_approval_scope.py` and `run_tables.py --only approval` pass.

## E1.F2 — Minimal phrase (REQ-AN-010..012 · BUG-159)

- **E1.F2.T1 [Test] 20 min** — Red: `test_state_repos.py` expects «aprobado para producción feat-a» without PR /
  version; `test_lint_plugin.py` L-82 pass/fail cases and the registry list. Done: they fail on 3.13.0.
- **E1.F2.T2 [Backend] 30 min** — `marker_report` text; `karvey-deploy` 2.9; `rules/enforcement.md`;
  `hooks/README.md`; L-82 in `lint-plugin.py`. Done: unit tests and `lint-plugin.py` pass.

## E1.F3 — Regression, records and release 3.13.1

- **E1.F3.T0 [Test] 15 min** — BUG-158/159 in `docs/bugs_dev_testing.md` and the incidents index; regression
  index `tests/regression/test_incidents.py`. Done: regression suite passes.
- **E1.F3.T1 [Backend] 25 min** — Release 3.13.1: `[Unreleased]` → `[3.13.1]` with its Why, `plugin.json`,
  `marketplace.json`, `project.json:karvey_version`, `docs/karvey.html` version lines, upgrade-surface line /
  fingerprint (L-37). Done: whole-repo gate green (unit, regression, tables, test-hooks, page, lint, validate).
- **E1.F3.T2 [Test] 25 min** — `test_plan.md` / `test_evidence.md` entries. Done: evidence recorded.

## Coverage

| REQ | Tasks |
|---|---|
| AN-001..007 | E1.F1.T1, E1.F1.T2 |
| AN-010..012 | E1.F2.T1, E1.F2.T2 |
