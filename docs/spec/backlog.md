# Discovery Backlog — Karvey Method

| ID | Date | Origin | Type | Priority | Title | Status | ClickUp | Promoted to change-id |
|----|------|--------|------|----------|-------|--------|---------|-----------------------|
| BL-01 | 2026-09-22 | session 3.8.0 → 3.9.1 (owner request) | tech-debt | high | Run graphify over the repo at the end of all the changes | open | — | — |

## BL-01 — Run graphify over the repo at the end of all the changes
- **Origin:** owner request (Mauricio Quezada Ibáñez), 2026-09-22, after publishing 3.8.0 / 3.9.0 and during the 3.9.1 docs sync.
- **Why:** `project.json:knowledge_sync = "graphify"` — the method's own knowledge-sync step (`rules/knowledge-sync.md`) was never run on this repo, so there is no `graphify-out/` reflecting skills, rules and their relations. The owner wants the repo left ordered once the pending changes land.
- **Rough scope:** after the last merge to `main`, run `/graphify` on the repo root (then `--update` on later changes); review `GRAPH_REPORT.md` for orphan rules, skills not referenced by the orchestrator, and broken cross-references; decide whether `graphify-out/` is versioned or ignored.
- **Status:** open
