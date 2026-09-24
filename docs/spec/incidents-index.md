# Incidents index — Karvey (global)

Project-wide view of every `BUG-NN` (`plugins/karvey/skills/karvey/rules/incident-tracking.md`). This
project has a single repo, so every incident lives in `docs/bugs_dev_testing.md` (repo `karvey`). Update
the state here on every transition recorded there.

Last updated: 2026-09-24 (wave1-hardening E1.F14.T3: BUG-06..17 RESUELTO with their regression checks; BUG-05 still DETECTADO).

| BUG | Repo | Priority | Title | Change / finding | Current state | Regression test | Fix planned in |
|-----|------|----------|-------|------------------|---------------|-----------------|----------------|
| BUG-01 | karvey | high | `karvey-init --settings` created a phantom change and a real tracker Epic | team-adapters / F-01 | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | hotfix 3.11.2 (done) |
| BUG-02 | karvey | medium | Session-hook settings nudge: wrong scope and project.json, fragile parsing, hang, imperative wording | team-adapters / F-02 | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | hotfix 3.11.2 (done) |
| BUG-03 | karvey | medium | An odd `resets_at` took the statusline down; time left truncated | team-adapters / F-03 | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | hotfix 3.11.2 (done) |
| BUG-04 | karvey | medium | Statusline debug copy at a fixed, shared, world-readable /tmp path | team-adapters / F-04 | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh (case to tighten) | hotfix 3.11.2 (done) |
| BUG-05 | karvey | high | impl decides dependencies and resume with non-logical states | team-adapters / F-07 | DETECTADO | — | wave1-hardening |
| BUG-06 | karvey | high | `project.json:management` legacy string breaks the `!= markdown` guards | team-adapters / F-08 | RESUELTO | L-28; plugins/karvey/tests/unit/test_config_resolve.py, test_state_fix.py (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-07 | karvey | medium | README and plugin.json still describe ClickUp as the tracker | team-adapters / F-09 | RESUELTO | L-31 (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-08 | karvey | low | Invalid `KARVEY_TZ` silently falls back to the system zone | team-adapters / F-22 | RESUELTO | plugins/karvey/tests/hooks/tables/statusline.json (statusline-01..03) (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-09 | karvey | low | Stray separator with only the 7-day window | team-adapters / F-23 | RESUELTO | plugins/karvey/tests/hooks/tables/statusline.json (statusline-04..06) (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-10 | karvey | low | Malformed hash throws `URIError` before the language switch binds | team-adapters / F-24 | RESUELTO | plugins/karvey/tests/page/test_page.mjs (safeDecodeHash, init) (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-11 | karvey | low | Invalid `?lang=` saves the browser language as the viewer's choice | team-adapters / F-25 | RESUELTO | plugins/karvey/tests/page/test_page.mjs (pickLang, init) (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-12 | karvey | low | Switching language drops the other query parameters | team-adapters / F-26 | RESUELTO | plugins/karvey/tests/page/test_page.mjs (withLang, init) (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-13 | karvey | low | No `hashchange` handling on the method page | team-adapters / F-27 | RESUELTO | plugins/karvey/tests/page/test_page.mjs (init binds hashchange) (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-14 | karvey | low | Without JS the language switch is shown but does nothing | team-adapters / F-28 | RESUELTO | plugins/karvey/tests/unit/test_page_static.py (NoInertSwitch); test_page.mjs (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-15 | karvey | low | `clickup-sync-guard` hook referenced but nothing installs it | team-adapters / F-29 | RESUELTO | L-15 (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-16 | karvey | low | hooks/README says the session hook prints nothing without team/agent files | team-adapters / F-30 | RESUELTO | L-16; plugins/karvey/tests/hooks/tables/session.json (ss-13, ss-15, ss-20) (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-17 | karvey | low | 3.11.1 release docs incomplete (CHANGELOG "Why", page history) | team-adapters / F-31 | RESUELTO | L-13 (indexed in plugins/karvey/tests/regression/test_incidents.py) | wave1-hardening (done on feature/wave1-hardening, ships in 3.12.0) |
| BUG-18 | karvey | high | SessionStart hook never ran (single-quoted ${CLAUDE_PLUGIN_ROOT}) | team-layer / agente-kloketen | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | 3.11.3 |
| BUG-19 | karvey | high | team.json inside the repo: profile path did not exist | team-layer / agente-kloketen | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | 3.11.3 |
| BUG-20 | karvey | medium | False NOT FOUND drift when state.json names the repo itself | team-layer / agente-kloketen | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | 3.11.4 |
| BUG-21 | karvey | medium | Git worktrees reported NOT FOUND in the live-state check | team-layer / wave1 F-01 | RESUELTO | plugins/karvey/hooks/tests/test-hooks.sh | 3.11.4 |

## Summary by state

| State | Count | BUGs |
|-------|-------|------|
| DETECTADO | 1 | BUG-05 |
| DIAGNOSTICADO | 0 | — |
| EN FIX | 0 | — |
| RESUELTO | 20 | BUG-01 .. BUG-04, BUG-06 .. BUG-21 |
| REABIERTO | 0 | — |

Next number: **BUG-22**.
