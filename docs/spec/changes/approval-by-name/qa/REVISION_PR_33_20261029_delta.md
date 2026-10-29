# Code Review (delta) — approval-by-name: e68c6d1 → 2a9662a (PR #33)

## General Information
- Repository: karvey
- Range: e68c6d19dd6b1014fc2c84722ed02e759475aafd..2a9662a7a0a81f602128fab3d94cea9e46feb202
- Date: 2026-10-29
- Reviewed commit: 2a9662a7a0a81f602128fab3d94cea9e46feb202
- Open blocking findings (critical/high): 0
- Scope: delta review, hotfix scope (D-55)

## Executive Summary
BUG-168 (31cfc9b): `check_prod` accepts a project-wide plan approval as the evidence of a production approval. An
independent reviewer found no critical or high findings and two medium ones, both fixed in 2a9662a with tests:

- **M1 · Medium · fixed.** A project plan the human had stopped («detente») could still back a production approval,
  since only its audit line was checked. Now a `withdrawn` audit line naming `_project` after the plan's creation
  refuses it. Test: `test_a_stop_after_the_project_plan_withdraws_it`. Also closes L1 for project plans.
- **M2 · Medium · fixed.** A project plan approved before the change existed could release it. Now a plan older than
  the change's first phase entry is refused. Test: `test_a_project_plan_older_than_the_change_does_not_release_it`.

Verified by the reviewer: forged evidence is still refused (audit line needs the same scope, prompt hash, session and
time); evidence of another change cannot be borrowed; no `_project` prod-kind marker exists; other `check_prod` callers
are unaffected.

## Summary Table by Severity
| Severity | Count |
|-----------|---------|
| Critical | 0 |
| High | 0 |
| Medium | 2 (fixed) |
| Low | 1 (fixed for project plans) |

## Pre-merge checklist
- [x] No critical or high findings
- [x] Tests pass on 2a9662a (unit 1153, regression, tables 624/624, hooks 68, lint 0 errors)
