# Board — agente-karvey

| id | priority | task | state | updated | note |
|---|---|---|---|---|---|
| B-01 | high | Wave 1 `wave1-hardening` → Karvey 3.12.0 | in_progress (iteration 1 reopened at architecture rev 1, D-19; E1.F17 open) | 2026-09-25 | worked by ANOTHER session in ~/Dev/karvey (last commit 24-09 22:08; idle since); remaining: architecture rev 1 approval (owner), E1.F17, qa, E1.F16 |
| B-02 | high | Owner: team-adapters prod phrase (E1.F15.T2) | done | 2026-09-25 | recorded in febcf59 (D-08); lint 0 errors (E1.F15.T3) |
| B-03 | medium | Converge + archive `team-adapters` (QA NOT approved; BUG-05..17 now RESUELTO on the wave1 branch) | in_progress | 2026-09-24 11:17 -03 | archives after 3.12.0 merges |
| B-04 | medium | Wave 2 (3.13 → 4.0): lanes, fewer gates, judges R-11, release per change, metrics | todo | 2026-09-24 11:17 -03 | needs owner decisions (panel §6) |
| B-05 | low | Wave 3 (4.1) | todo | 2026-09-24 11:17 -03 | |
| B-06 | low | HTML: add it / ja / fr / ko — **last, after all changes** (owner) | todo | 2026-09-24 11:17 -03 | |
| B-07 | low | graphify `--update` — deferred to the wave1 archive (REQ-W1-062) | todo | 2026-09-24 11:17 -03 | 3.11.3/3.11.4 hotfix docs not yet in the graph |
| B-08 | info | Matthew reported BUG-18 on 3.11.2 | done | 2026-09-24 11:17 -03 | already fixed in 3.11.3; owner given a message to forward (update to 3.11.4) |
| B-09 | info | agente-kloketen: verify 3.11.4 on a real new session | awaiting-human | 2026-09-24 11:17 -03 | read-only check passed; real-session check pending the owner |
| B-10 | info | Owner's local statusline `~/.claude/hooks/statusline-rotacion.sh` changed to 30/50 % on his explicit request (D-18) | done | 2026-09-24 12:05 -03 | not the plugin script; backup in session scratchpad; env ROTAR_CTX_{AMARILLO,ROJO}_PCT |
| B-11 | high | New change `project-upgrade` (D-20): once-per-version ask → project upgrade plan | requirements generated; **awaiting owner approval** | 2026-09-25 12:07 | worktree ~/Dev/karvey-wt-project-upgrade, branch feature/project-upgrade @877f82b; 32 REQ-UP; D-20 + BL-51 recorded; REQ-UP-005 (no offer when plan empty) to confirm |
| B-12 | medium | AG-12 cheap pieces (evidence wrapper, clean-context "fiscal" before qa.approved/done) | proposed, not decided | 2026-09-25 | owner asked about agent autonomy; propose as backlog after 3.12.0 |
| B-13 | low | F-51 statusline stable launcher (README suggests a versioned path that goes stale) | folded into project-upgrade | 2026-09-25 | |
