# Findings: approval-by-name

Triage inbox of this change (`plugins/karvey/skills/karvey/rules/iteration-loop.md`). Types: `bug` → incident
`BUG-NN` in `docs/bugs_dev_testing.md` · `spec-gap` → requirements · `emergent` → `docs/spec/backlog.md`.
Status: `open` → `routed` → `closed`.

| # | Date | Source phase | Type | Severity | Title | Status | Routed to |
|---|------|--------------|------|----------|-------|--------|-----------|
| F-01 | 2026-10-07 | real use (owner, D-47) | bug | high | The owner typed «aprobado para producción change-a» in a session whose directory was another repo holding `change-b`; the hook answered "prod approval NOT recorded: change-a is not a change of this working tree and no worktree or branch holds it … type: «aprobado para producción change-b»": it discarded the change the human named and suggested approving another one. Root cause: `approval.resolve_prod_scope` searches only the working tree, its clone's worktrees and branches, never the other local clones (the prod-gate's clone discovery, `clones.search_dirs`), and its unknown-word branch suggests the active change. | routed | BUG-158 · REQ-AN-001..007 |
| F-02 | 2026-10-07 | real use (owner, D-47) | bug | medium | The suggested phrase «aprobado para producción <id> PR #<n> v<version>» (state tool refusal, `karvey-deploy` step 2.9) reads as a mandatory format; only the approval word, the production word and the change id are required (D-10) and the approval binds to the commit passed with `approve … --sha` (D-35). | routed | BUG-159 · REQ-AN-010..012 |
