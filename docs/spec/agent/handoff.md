# Handoff — agente-karvey

## 0. Verified state — 2026-09-24 12:05 -03
Captured with commands (see `state.json` beside this file, written by `karvey-handoff-capture.py` last). If it does not match on startup, this handoff has aged: believe the commands.

| Repo | Branch | Uncommitted | Last commit | Published? |
|---|---|---|---|---|
| ~/Dev/karvey | feature/wave1-hardening | see state.json | see state.json | `main` = 3.11.4 (PR #23), installed 3.11.4 (`claude plugin list`); 3.12.0 NOT released |

## 1. Blocking right now
E1.F15.T2 waits on **the owner**: the team-adapters prod phrase in a session that loads the branch plugin (exact command and phrase in `board.md` B-02). Everything after F15.T3 (release 3.12.0) depends on it.

## 2. Who I am
`manifest.md` @ current commit · board `board.md` · checklist `checklist.md`. Maintainer agent of the Karvey plugin; owner Mauricio approves every gate; HainTech product repos and the owner's global config are not mine.

## 3. Rules I work under
`manifest.md` (referenced, not copied) + the owner's global CLAUDE.md + `plugins/karvey/skills/karvey/rules/`.

## 4. Board — open, in one place
`board.md` (B-01..B-10).

## 5. Closing checklist
`checklist.md`.

## 6. Standing decisions that affect me
`docs/spec/decisions.md` D-01..D-18 (D-18: statusline lights by % of the window, 30 amber / 50 red). Most load-bearing: D-01 (marker created by the prompt hook, never the agent), D-02 (prod-gate on), D-03 (prod approval never a commit on dev), D-10 (prod needs approval+production words), D-14 (team-adapters phrase; team-layer = warning), D-15 (integration ≠ prod).

## 7. In flight, and what I am waiting for
- Branch `feature/wave1-hardening` pushed; **draft PR #24** → `main` open to observe CI (E1.F13.T2); lint job red until E1.F15.T3.
- Owner: E1.F15.T2 phrase. agente-kloketen: confirmation of 3.11.4 on a real new session. Matthew: told (via the owner) to update to 3.11.4.
- ~15 update notices to local sessions were held for the owner's approval in each session.

## 8. What a new session CANNOT derive from the repo
- **This session's skills may be stale**: a long session keeps the plugin version it loaded (the QA run here loaded karvey-qa from 3.9.0). Read the skill from the repo (`plugins/karvey/skills/...`) when working on the plugin, not from the cache.
- Estimates run ~10× high (165 min → 11 min in batch 1; 2150 min plan vs a few hours real). Actuals are recorded in PLAN.md.
- Gemini keys in `~/.claude/.connections` belong to production client projects — do not use them for internal reviews (QA D7 used an intra-model fallback for that reason).
- `Mac-playwright-HTS` is not reachable; browser work goes to `Otro playwright` (bridge session_012AeQMzGyXTQycQG2Eq9aX1), which replies, or `mac-playwright-m15`.
- `/srv/capturas` is not readable by this user.
- Parallel lanes in worktrees must not edit CHANGELOG.md / PLAN.md; the orchestrator adds their lines at integration.
- The approval hook ignores prompt lines over 200 characters (F-11) — keep approval phrases short.
- The owner's live statusline is `~/.claude/hooks/statusline-rotacion.sh` (Spanish copy), **not** the plugin's `karvey-statusline.sh`: a plugin change does not reach his screen; D-18 was applied to both.

## 9. Scheduled tasks — with their full prompt
None.

## 10. Last updated
2026-09-24 12:05 -03 · agente-karvey · restore + F-41/D-18 statusline, E1.F15.T1 done, draft PR #24.
2026-09-24 11:18 -03 · agente-karvey · first handoff of this agent (profile bootstrapped in this save).
