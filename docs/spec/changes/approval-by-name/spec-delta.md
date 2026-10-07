# Spec Delta: approval-by-name

Against the living spec `docs/spec/specs/method/spec.md` (capability `method`). Scenarios are in
`requirements.md`. The 3.12.1 requirements this change amends (REQ-HF-001..004, 018, 029) reach the living spec
through `prod-gate-scope`'s spec-delta; they are cited as *amends* and the amendment is ADDED, so the merge order
of the two changes does not matter.

Summary: **ADDED 10** (REQ-AN-001..007, REQ-AN-010..012) · **MODIFIED 0** · **REMOVED 0**.

## ADDED Requirements

### ADDED by `approval-by-name` (3.13.1)

Traced to `docs/spec/changes/approval-by-name/prd.md`.

### A production approval is recorded in the clone that owns the named change (F-01, BUG-158)
- **REQ-AN-001** — WHEN a production approval names a change id that is not in the working tree, the approval hook SHALL look for it in the clones found by the prod-gate's clone discovery, counting a clone once whatever number of its worktrees hold it. *(Traces: O-1, S-1, AC-1 · F-01 · BUG-158 · D-47 · amends REQ-HF-002)*
- **REQ-AN-002** — WHEN exactly one clone owns it, the approval hook SHALL write the production marker and its audit line in that clone, none in the working tree's clone, and print the owning clone's path. *(Traces: O-1, S-1, AC-1 · F-01 · BUG-158 · D-34, D-47)*
- **REQ-AN-003** — IF two or more clones own it, THEN the approval hook SHALL record nothing and list every owning clone. *(Traces: O-1, AC-2 · F-01 · BUG-158)*
- **REQ-AN-004** — The suggested phrase SHALL name the change the prompt named (or `<change-id>`), never the active change nor another change. *(Traces: O-2, AC-3 · F-01 · BUG-158 · amends REQ-HF-029)*
- **REQ-AN-005** — The working tree keeps precedence for an id it holds; with no change named the single active change is used, said out loud; several named record nothing; a branch-only id keeps its message. *(Traces: O-1, AC-4 · amends REQ-HF-001..004)*
- **REQ-AN-006** — Outside a Karvey project, a production approval naming a change owned by exactly one discovered clone is recorded there; two or more owners print the not-recorded line; otherwise silent. *(Traces: O-1, S-1 · F-01 · BUG-158)*
- **REQ-AN-007** — The clone search runs only for a production approval whose named id is not in the working tree, uses the bounded discovery, and fails open with the not-recorded line. *(Traces: O-1 · amends REQ-HF-018)*

### The phrase asks only for what counts (F-02, BUG-159)
- **REQ-AN-010** — The hook, the state tool refusal and `karvey-deploy` show «aprobado para producción <change-id>» with no PR number and no version. *(Traces: O-3, S-2, AC-5 · F-02 · BUG-159 · D-10)*
- **REQ-AN-011** — The rules, the hooks README and `karvey-deploy` state that only the approval word, the production word and the change id are required, PR and version are informational, and the approval binds to the commit passed with `approve … prod --sha`. *(Traces: O-3, S-2 · F-02 · BUG-159 · D-10, D-35)*
- **REQ-AN-012** — Lint check L-82 fails a skill or rule that shows the production phrase with a PR number or a version inside it. *(Traces: O-3, S-2, AC-5 · F-02 · BUG-159)*
