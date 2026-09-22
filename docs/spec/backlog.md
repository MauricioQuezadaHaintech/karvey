# Discovery Backlog — Karvey Method

| ID | Date | Origin | Type | Priority | Title | Status | Tracker | Promoted to change-id |
|----|------|--------|------|----------|-------|--------|---------|-----------------------|
| BL-01 | 2026-09-22 | session 3.8.0 → 3.9.1 (owner request) | tech-debt | high | Run graphify over the repo at the end of all the changes | done | — | — |
| BL-02 | 2026-09-22 | graphify review (owner) | feature | high | Notifications configurable per team (not Google Chat hard-coded in karvey-qa) | promoted | — | team-adapters |
| BL-03 | 2026-09-22 | graphify review (owner) | feature | high | Task-management tool + status flow configurable (not ClickUp `listo! para pap` hard-coded) | promoted | — | team-adapters |

## BL-01 — Run graphify over the repo at the end of all the changes
- **Origin:** owner request (Mauricio Quezada Ibáñez), 2026-09-22, after publishing 3.8.0 / 3.9.0 and during the 3.9.1 docs sync.
- **Why:** `project.json:knowledge_sync = "graphify"` — the method's own knowledge-sync step (`rules/knowledge-sync.md`) was never run on this repo, so there is no `graphify-out/` reflecting skills, rules and their relations. The owner wants the repo left ordered once the pending changes land.
- **Rough scope:** after the last merge to `main`, run `/graphify` on the repo root (then `--update` on later changes); review `GRAPH_REPORT.md` for orphan rules, skills not referenced by the orchestrator, and broken cross-references; decide whether `graphify-out/` is versioned or ignored.
- **Status:** done — 2026-09-22, resolved directly (no change-id): `graphify-out/` built over the repo (82 files → 399 nodes, 753 edges, 21 communities) and versioned with repo-relative paths; only `graphify-out/.graphify_python` (machine-specific interpreter path) is ignored. Refresh with `graphify . --update` after later changes.

## BL-02 — Notifications configurable per team
- **Origin:** graphify review of the repo, 2026-09-22 — `karvey-qa` Step 4 always notified Google Chat via a `CLAUDE.md` table.
- **Why:** another team uses Slack, Teams, e-mail or nothing; the step failed or did not apply.
- **Status:** promoted → `team-adapters`

## BL-03 — Task-management tool and status flow configurable
- **Origin:** graphify review of the repo, 2026-09-22 — `listo! para pap` hard-coded in clickup-protocol, phase-close, karvey-impl, karvey-tasks.
- **Why:** teams use Jira, Linear, Azure Boards, a spreadsheet… and their own status names.
- **Status:** promoted → `team-adapters`
