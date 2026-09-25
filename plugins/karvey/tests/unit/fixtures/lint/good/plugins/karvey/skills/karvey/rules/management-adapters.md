# Rule: management adapters

## Cascade

The one cascade: Features to `review` move the Epic to `review` at impl; the Epic reaches `done` only at archive.

## Adapters

| Tool | How the session does it | log_time | Notes |
|---|---|---|---|
| **Jira** | REST | worklog | transition |
| **Markdown** | `PLAN.md` | none | fallback |

Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked · 🙋 awaiting-human`.
