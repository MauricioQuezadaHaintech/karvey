# Findings: prod-gate-scope

Triage inbox of this change (`plugins/karvey/skills/karvey/rules/iteration-loop.md`). Types: `bug` → incident
`BUG-NN` in `docs/bugs_dev_testing.md` · `spec-gap` → requirements · `emergent` → `docs/spec/backlog.md`.
Status: `open` → `routed` → `closed`.

| # | Date | Source phase | Type | Severity | Title | Status | Routed to |
|---|------|--------------|------|----------|-------|--------|-----------|
| F-01 | 2026-09-29 | real use | bug | high | The approval hook took the prod marker's scope from the active change of the working tree where it ran, not from the change the phrase named: «aprobado para producción project-upgrade 3.13.0» typed in a tree where only `team-adapters` was open recorded `(prod, team-adapters)`. Root cause: `approval.scope_for` only looks for ids of changes present in that tree; an id that is not there is ignored and the active change is used. | routed | BUG-53 · REQ-HF-001..004 |
| F-02 | 2026-09-29 | real use | spec-gap | high | A change owned by repo A that releases A, B and C: the owner approves in A, the PR `[Deploy] <id>` in B is blocked ("cannot determine the change being released"). The gate only reads the ledger of the repo where the merge runs, and nothing declares which repos a change releases. | routed | REQ-HF-005..009 |
| F-03 | 2026-09-29 | real use | spec-gap | high | The prod-gate does not see REST calls that complete a PR (`curl … /pullrequests/<n> -X PATCH` with `status: completed`, `…/pulls/<n>/merge` through an HTTP client), production pipeline approvals (`…/pipelines/approvals`, `…/pending_deployments`), nor commands run outside a repo (`cd /tmp && …`) that target a Karvey repo by name or URL. | routed | REQ-HF-010..015 |
| F-04 | 2026-09-29 | real use | bug | low | BL-64: protect-paths blocks read-only listings such as `ls <state dir> 2>/dev/null; echo done`, `cat <ledger> \| python3 -m json.tool` and `ls "$(git rev-parse --git-common-dir)/karvey/approvals/"`. Root cause: the last check (a needle split by quoting) requires *every* segment of the command to be read-only, and a read-only `git` subcommand is not in the read-only set. | routed | BUG-54 · REQ-HF-016 |
