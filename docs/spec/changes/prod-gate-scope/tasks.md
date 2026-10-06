# Tasks: prod-gate-scope (hotfix 3.12.1)

> PHASE 7 (`karvey-tasks`) · Security Tier 2 · Tracker: Markdown (this file + `PLAN.md`).
> Inputs: `architecture.md` (approved, D-21), `requirements.md` (REQ-HF-001..030, approved, D-45), `findings.md`
> F-01..F-11, `docs/bugs_dev_testing.md` (BUG-138..144 to be added).

## Summary

| Item | Value |
|---|---|
| Features | 9 (E1.F1..F9) |
| Tasks | 24 (19 Backend, 4 Test, 1 release) |
| Total estimate (AI + review) | 690 min |
| REQ-HF coverage | 30/30 |
| Largest task | 50 min |

## Conventions

- IDs `E1.F{n}.T{n}`. Layers: `[Backend]` plugin scripts, hooks and skill text; `[Test]` tests only.
- Hotfix lane: each BUG fix ships with its regression test, written red first (fails on 3.12.0), in the same PR.
- Tasks that share a file run in sequence (`guards.py`, `karvey-state.py`, `karvey_hooks.py`).
- Each impl commit adds one line under `## [Unreleased]`; the version moves once, in E1.F9.T1.
- Done = the command in the task passes.

## E1.F1 — Approval hook scope and one line (REQ-HF-001..004, 029 · BUG-138, BUG-143)

- **E1.F1.T1 [Test] 30 min** — Red rows in `tables/approval.json` (named change wins, named change elsewhere →
  worktree path, typo, single active said out loud, several active, several named, silent cases with approval +
  prod words) and unit `test_approval_scope.py` (worktree/branch lookup). Done: they fail on 3.12.0.
- **E1.F1.T2 [Backend] 50 min** — `approval.resolve_prod_scope`, `approval.answer_line`, hook wiring in
  `guards.approval_hook`. Done: `run_tables.py --only approval` and the unit file pass.

## E1.F2 — State tool: repos, binding, refusal text (REQ-HF-005, 006, 009, 030 · BUG-144)

- **E1.F2.T1 [Test] 25 min** — Red unit tests: `repos` schema; `approve --repo --sha` (success, undeclared,
  expired, short sha, rebinding); `check-prod --repo`; refusal lists markers and the missing piece.
- **E1.F2.T2 [Backend] 25 min** — `spec.schema.json` `repos`; semantic check.
- **E1.F2.T3 [Backend] 40 min** — `approve … prod --repo`, `check_prod(repo=)`, `check-prod --repo`,
  `approval.describe_markers` and the refusal text. Done: `test_state_approve.py` passes.

## E1.F3 — Prod-gate target repo (REQ-HF-014, 024..026 · BUG-141)

- **E1.F3.T1 [Test] 30 min** — Red unit `test_prodgate_target.py`: `--repo` other clone into integration base
  passes; into production checked on the target's ledger; non-Karvey target warns; named Karvey repo without a
  clone blocks; host URL mismatch blocks.
- **E1.F3.T2 [Backend] 40 min** — `karvey_lib/clones.py` (names, search roots, find clone, karvey_named).
- **E1.F3.T3 [Backend] 40 min** — Target step in `_evaluate_candidate`; PR URL selectors; `gh --json url`.

## E1.F4 — Multi-repo release (REQ-HF-007, 008)

- **E1.F4.T1 [Test] 20 min** — Red unit `test_prodgate_multirepo.py` (owner bound / not bound / undeclared /
  owner not found message).
- **E1.F4.T2 [Backend] 35 min** — `find_owner`, owner check and BLOCK text.

## E1.F5 — REST and outside-a-repo (REQ-HF-010..013, 015)

- **E1.F5.T1 [Test] 30 min** — Red unit `test_restcalls.py` (parser, endpoint table, reads, variables, unreadable
  body, inline scripts) and `tables/prod-gate.json` REST rows.
- **E1.F5.T2 [Backend] 50 min** — `karvey_lib/restcalls.py`; candidates in `prod_candidates`; cheap pre-filter.
- **E1.F5.T3 [Backend] 40 min** — Pipeline approvals: run lookup, production branch, merge-parent rule
  (unit `test_prodgate_pipeline.py`).

## E1.F6 — Protect-paths listings (REQ-HF-016 · BUG-139)

- **E1.F6.T1 [Test] 10 min** — Red rows in `tables/protect-paths.json` (four listings pass, three writes block).
- **E1.F6.T2 [Backend] 20 min** — Final check accepts text, formatter and read-only git segments.

## E1.F7 — Session identity (REQ-HF-020..023 · BUG-140)

- **E1.F7.T1 [Test] 30 min** — Red rows in `tables/session.json` and unit `test_session_profile.py` (ancestor
  folder, unmapped repo, team root, cwd change, two candidates, sensitive handoff, explicit restore).
- **E1.F7.T2 [Backend] 45 min** — `livestate.resolve_session_profile`, `profile_repos`, sensitive front matter;
  `session_text` rewired; `restore-profile` entry point.
- **E1.F7.T3 [Backend] 25 min** — Bash degraded path in `karvey-session-context.sh`.
- **E1.F7.T4 [Backend] 15 min** — `karvey-checkpoint` skill: `restore --profile`, `save --sensitive`.

## E1.F8 — Typed production OK (REQ-HF-027, 028 · BUG-142)

- **E1.F8.T1 [Test] 15 min** — Red lint fixture and unit test for L-80.
- **E1.F8.T2 [Backend] 25 min** — L-80 in `lint-plugin.py`; `karvey-deploy` 2.9 rewritten; any other text that
  trips L-80 fixed.

## E1.F9 — Regression, docs and release 3.12.1 (REQ-HF-017..019)

- **E1.F9.T1 [Backend] 40 min** — BUG-138..144 in `docs/bugs_dev_testing.md` and `incidents-index.md`; index in
  `tests/regression/test_incidents.py`; hooks README; versions 3.12.1; CHANGELOG `[3.12.1]` + empty
  `[Unreleased]`. Done: full gate green (unit, regression, `test-hooks.sh`, `run_tables.py`, node page tests,
  lint 0 errors, validate --all 0 errors).

## Coverage

| REQ-HF | Tasks |
|---|---|
| 001..004, 029 | E1.F1 |
| 005, 006, 009, 030 | E1.F2 |
| 007, 008 | E1.F4 |
| 010..013, 015 | E1.F5 |
| 014, 024..026 | E1.F3 |
| 016 | E1.F6 |
| 017..019 | E1.F9 |
| 020..023 | E1.F7 |
| 027, 028 | E1.F8 |
