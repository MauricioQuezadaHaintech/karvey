# Checkpoint — wave1-hardening

> Cross-cutting skill karvey-checkpoint. It is NOT a phase. It does NOT modify spec.json:phase.

- **Date:** 2026-09-24 11:17 -03
- **Author:** agente-karvey (Claude Opus 5.5) for Mauricio Quezada Ibáñez
- **Repo:** ~/Dev/karvey

## Git state
- **Branch:** feature/wave1-hardening
- **Last commit:** d2d8b68 2026-09-24 fix(wave1): F-38 — legacy management.status_flow proposed as statuses
- **Working tree:** 1 changed paths before this checkpoint (only the checkpoint/handoff files written by this save)
- **Ahead of origin/main:** 87 commits · origin/main @663d496 (3.11.4)

## Decisions made
- D-01..D-17 in `docs/spec/decisions.md`, all quoting the owner verbatim. Latest: D-14 (owner types the team-adapters prod phrase; team-layer = warning history), D-15 (integration is not prod), D-16 (close F-15 now), D-17 (minor impl decisions; F-26..F-33 → Wave 2 backlog).
- Gates approved: requirements (D-05), architecture (D-09), tasks (D-13); infra skipped (D-12).

## Done in impl (60 of 73 tasks)
E1.F1–E1.F12, E1.F13.T1, E1.F14.T1–T4 and the pre-F15 fixes (BUG-05, F-12, F-15, F-35, F-36, F-37, F-38). BUG-05..17 RESUELTO with regression checks. Suite: 694 unit · 10 regression · 58 test-hooks · 375 table runs · 22 page — all green. Lint: 3 errors (team-adapters `approvals.prod`, cleared by E1.F15.T2/T3), 3 warnings.

## Pending work
- [ ] **E1.F15.T2 [human]** — owner types «ok, registra la aprobación de prod de team-adapters con D-08» in `claude --plugin-dir ~/Dev/karvey/plugins/karvey --setting-sources project,local` (cwd ~/Dev/karvey).
- [ ] E1.F15.T1 — this repo through `validate --fix` (dry-run shown, then applied).
- [ ] E1.F15.T3 — `approve … --write-spec` for team-adapters (D-08); `validate --all` → 0 errors; lint → 0 errors.
- [ ] E1.F13.T2 — observe CI on a draft PR `feature/wave1-hardening → main`.
- [ ] Then `karvey-qa` of wave1-hardening (retro QA lesson: QA before prod), E1.F16.T1 (one version bump → 3.12.0, `pre_3_12_history.released_on`), T2 (global-config diffs, never applied), T3 [human] branch protection, T4–T6 release through the prod-gate with the owner's prod OK (T5), T7 [human] apply diffs.
- [ ] Archive wave1-hardening (graphify `--update` there) and team-adapters.

## Next step
Wait for the owner's E1.F15.T2 phrase; meanwhile run E1.F15.T1 (`--fix` dry-run) and E1.F13.T2 (draft PR to see CI).

Installed plugin at checkpoint: Version: 3.11.4 (3.12 not released).
