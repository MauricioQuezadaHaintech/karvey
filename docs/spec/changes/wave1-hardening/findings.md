# Findings: wave1-hardening

Triage inbox of this change (`plugins/karvey/skills/karvey/rules/iteration-loop.md`). `karvey-test`,
`karvey-qa` and `karvey-browse` append observations here with a type guess; only `karvey-iterate` routes them.
Types: `bug` → incident `BUG-NN` in `docs/bugs_dev_testing.md` (continue from BUG-18) · `spec-gap` → re-open
requirements · `emergent` → `docs/spec/backlog.md` (continue from BL-44).

Status: `open` → `routed` → `closed`. Convergence needs no `open`/`routed` `bug` or `spec-gap`.

The open work inherited from `team-adapters` is **not** re-logged here: it lives in
`docs/spec/changes/team-adapters/findings.md` and `docs/bugs_dev_testing.md`, and is covered by
REQ-W1-080..106 (traceability in `requirements.md`; convergence rule REQ-W1-107, REQ-W1-108).

| # | Date | Source phase | Type | Severity | Title | Status | Routed to |
|---|------|--------------|------|----------|-------|--------|-----------|
| F-01 | 2026-09-23 | architecture | bug | medium | Session hook checks for a `.git` *directory*, so every git worktree is reported as "NOT FOUND" (worktrees have a `.git` file). Fixed by design with `git rev-parse --git-dir`. | open |
| F-02 | 2026-09-23 | architecture | spec-gap | medium | Hook payload field names are unconfirmed (installed CLI 2.1.281 vs local docs: `prompt` vs `user_prompt`, …). Tolerant parser designed (assumptions A-1..A-10); first test task captures one real payload per event. | open |

