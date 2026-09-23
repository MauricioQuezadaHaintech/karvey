# Incidents index — Karvey (global)

Project-wide view of every `BUG-NN` (`plugins/karvey/skills/karvey/rules/incident-tracking.md`). This
project has a single repo, so every incident lives in `docs/bugs_dev_testing.md` (repo `karvey`). Update
the state here on every transition recorded there.

Last updated: 2026-09-23 (retroactive QA of `team-adapters`, hotfix 3.11.2).

| BUG | Repo | Priority | Title | Change / finding | Current state | Regression test | Fix planned in |
|-----|------|----------|-------|------------------|---------------|-----------------|----------------|
| BUG-01 | karvey | high | `karvey-init --settings` created a phantom change and a real tracker Epic | team-adapters / F-01 | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | hotfix 3.11.2 (done) |
| BUG-02 | karvey | medium | Session-hook settings nudge: wrong scope and project.json, fragile parsing, hang, imperative wording | team-adapters / F-02 | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | hotfix 3.11.2 (done) |
| BUG-03 | karvey | medium | An odd `resets_at` took the statusline down; time left truncated | team-adapters / F-03 | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | hotfix 3.11.2 (done) |
| BUG-04 | karvey | medium | Statusline debug copy at a fixed, shared, world-readable /tmp path | team-adapters / F-04 | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh (case to tighten) | hotfix 3.11.2 (done) |
| BUG-05 | karvey | high | impl decides dependencies and resume with non-logical states | team-adapters / F-07 | DETECTADO | — | wave1-hardening |
| BUG-06 | karvey | high | `project.json:management` legacy string breaks the `!= markdown` guards | team-adapters / F-08 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-07 | karvey | medium | README and plugin.json still describe ClickUp as the tracker | team-adapters / F-09 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-08 | karvey | low | Invalid `KARVEY_TZ` silently falls back to the system zone | team-adapters / F-22 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-09 | karvey | low | Stray separator with only the 7-day window | team-adapters / F-23 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-10 | karvey | low | Malformed hash throws `URIError` before the language switch binds | team-adapters / F-24 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-11 | karvey | low | Invalid `?lang=` saves the browser language as the viewer's choice | team-adapters / F-25 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-12 | karvey | low | Switching language drops the other query parameters | team-adapters / F-26 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-13 | karvey | low | No `hashchange` handling on the method page | team-adapters / F-27 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-14 | karvey | low | Without JS the language switch is shown but does nothing | team-adapters / F-28 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-15 | karvey | low | `clickup-sync-guard` hook referenced but nothing installs it | team-adapters / F-29 | DIAGNOSTICADO | — | wave1-hardening |
| BUG-16 | karvey | low | hooks/README says the session hook prints nothing without team/agent files | team-adapters / F-30 | EN FIX | — | wave1-hardening |
| BUG-17 | karvey | low | 3.11.1 release docs incomplete (CHANGELOG "Why", page history) | team-adapters / F-31 | EN FIX | — (CI linter, BL-10) | wave1-hardening |
| BUG-18 | karvey | high | SessionStart hook never ran (single-quoted ${CLAUDE_PLUGIN_ROOT}) | team-layer / agente-kloketen | RESUELTO | — | 3.11.3 |
| BUG-19 | karvey | high | team.json inside the repo: profile path did not exist | team-layer / agente-kloketen | RESUELTO | — | 3.11.3 |

## Summary by state

| State | Count | BUGs |
|-------|-------|------|
| DETECTADO | 1 | BUG-05 |
| DIAGNOSTICADO | 10 | BUG-06 .. BUG-15 |
| EN FIX | 2 | BUG-16, BUG-17 |
| RESUELTO | 4 | BUG-01 .. BUG-04 |
| REABIERTO | 0 | — |

Next number: **BUG-18**.
