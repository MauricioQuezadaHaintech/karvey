# Handoff — agente-karvey

## 0. Verified state — 2026-09-25 12:07 UTC
Captured with commands (see `state.json` beside this file, written by `karvey-handoff-capture.py` last). If it does not match on startup, this handoff has aged: believe the commands.

| Repo | Branch | Uncommitted | Last commit | Published? |
|---|---|---|---|---|
| ~/Dev/karvey | feature/wave1-hardening | 0 | 8188ab3 handoff: state.json captured | `main` = 3.11.4 (PR #23), installed 3.11.4 (`claude plugin list`); 3.12.0 NOT released; PR #24 CI green on 8188ab3 (all 7 jobs) |
| ~/Dev/karvey-wt-project-upgrade | feature/project-upgrade | 0 | 877f82b requirements (REQ-UP-001..032) | pushed; not merged |

## 1. Blocking right now
Nothing blocks this agent. Two lines of work:
- **`project-upgrade`** (mine, D-20): requirements generated in worktree `~/Dev/karvey-wt-project-upgrade` (branch `feature/project-upgrade` @877f82b): 32 EARS REQ-UP-001..032, spec-delta ADDED 32, D-20 + BL-51 recorded. **Waiting on the owner's requirements approval** (confirm REQ-UP-005: no offer when the plan is empty). Next after approval: skip mockup/design_graphic (no UI) → `/karvey-architecture project-upgrade`.
- **`wave1-hardening`**: driven by another session in `~/Dev/karvey` (idle since 24-09 22:08). `spec.json:phase` = architecture (iteration 1 reopened, rev 1, D-19) — waits on the owner's approval of architecture rev 1. Do not edit wave1 files from the worktree; coordinate first.

## 2. Who I am
`manifest.md` @ current commit · board `board.md` · checklist `checklist.md`. Maintainer agent of the Karvey plugin; owner Mauricio approves every gate; HainTech product repos and the owner's global config are not mine.

## 3. Rules I work under
`manifest.md` (referenced, not copied) + the owner's global CLAUDE.md + `plugins/karvey/skills/karvey/rules/`.

## 4. Board — open, in one place
`board.md` (B-01..B-13).

## 5. Closing checklist
`checklist.md`.

## 6. Standing decisions that affect me
`docs/spec/decisions.md` D-01..D-19 on the wave1 branch; D-20 recorded on `feature/project-upgrade` (877f82b) — merge order: whichever lands second resolves the append conflict (D-18: statusline lights by % of the window, 30 amber / 50 red). Most load-bearing: D-01 (marker created by the prompt hook, never the agent), D-02 (prod-gate on), D-03 (prod approval never a commit on dev), D-10 (prod needs approval+production words), D-14 (team-adapters phrase; team-layer = warning), D-15 (integration ≠ prod).

## 7. In flight, and what I am waiting for
- Branch `feature/wave1-hardening` pushed; **draft PR #24** → `main`, MERGEABLE, CI green on all 7 jobs @8188ab3 (lint included: the team-adapters prod approval was recorded in febcf59, D-08).
- agente-kloketen: confirmation of 3.11.4 on a real new session. Matthew: told (via the owner) to update to 3.11.4.
- ~15 update notices to local sessions were held for the owner's approval in each session.

## 8. What a new session CANNOT derive from the repo
- **This session's skills may be stale**: a long session keeps the plugin version it loaded (the QA run here loaded karvey-qa from 3.9.0). Read the skill from the repo (`plugins/karvey/skills/...`) when working on the plugin, not from the cache.
- Estimates run ~10× high (165 min → 11 min in batch 1; 2150 min plan vs a few hours real). Actuals are recorded in PLAN.md.
- Gemini keys in `~/.claude/.connections` belong to production client projects — do not use them for internal reviews (QA D7 used an intra-model fallback for that reason).
- `Mac-playwright-HTS` is not reachable; browser work goes to `Otro playwright` (bridge session_012AeQMzGyXTQycQG2Eq9aX1), which replies, or `mac-playwright-m15`.
- `/srv/capturas` is not readable by this user.
- Parallel lanes in worktrees must not edit CHANGELOG.md / PLAN.md; the orchestrator adds their lines at integration.
- The approval hook ignores prompt lines over 200 characters (F-11) — keep approval phrases short.
- First Windows/macOS CI runs exposed test-runner portability only (F-42..F-46): Windows `"bash"` resolves to WSL's bash.exe, symlinks need privilege, process start-up ~2x (KARVEY_TABLES_TIME_FACTOR); macOS has no `timeout` and /var → /private/var. Each push cancels the previous run: wait for macOS before pushing again.
- The owner's live statusline is `~/.claude/hooks/statusline-rotacion.sh` (Spanish copy), **not** the plugin's `karvey-statusline.sh`: a plugin change does not reach his screen; D-18 was applied to both.

## 9. Scheduled tasks — with their full prompt
None.

## 10. Last updated
2026-09-25 12:07 UTC · agente-karvey · restore; corrected aged §0/§1/§6/§7 (E1.F15.T2 already done, lint green); project-upgrade requirements generated, awaiting owner gate. Statusline question answered: D-18 already live (30/50 %), no change.
2026-09-25 · agente-karvey · rotation requested by the owner: project-upgrade planned (D-20), board B-11..B-13; answered owner questions on waves, upgrade behaviour, agent-autonomy judge (AG-01..AG-14).
2026-09-24 16:40 -03 · agente-karvey · PR #24 CI green except lint (F-42..F-46).
2026-09-24 12:05 -03 · agente-karvey · restore + F-41/D-18 statusline, E1.F15.T1 done, draft PR #24.
2026-09-24 11:18 -03 · agente-karvey · first handoff of this agent (profile bootstrapped in this save).
