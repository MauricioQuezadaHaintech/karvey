# Board — agente-karvey

| id | priority | task | state | updated | note |
|---|---|---|---|---|---|
| B-01 | high | Wave 1 `wave1-hardening` → Karvey 3.12.0 | in_progress (impl, 60/73 tasks) | 2026-09-24 11:17 -03 | remaining: E1.F13.T2, E1.F15.T1..T3, E1.F16.T1..T7 |
| B-02 | high | **Owner:** type the team-adapters prod phrase (E1.F15.T2) | awaiting-human | 2026-09-24 11:17 -03 | session: `cd ~/Dev/karvey && claude --plugin-dir ~/Dev/karvey/plugins/karvey --setting-sources project,local`; phrase: «ok, registra la aprobación de prod de team-adapters con D-08»; expect `[karvey] approval recorded (prod, team-adapters, …)`; valid 120 min |
| B-03 | medium | Converge + archive `team-adapters` (QA NOT approved; BUG-05..17 now RESUELTO on the wave1 branch) | in_progress | 2026-09-24 11:17 -03 | archives after 3.12.0 merges |
| B-04 | medium | Wave 2 (3.13 → 4.0): lanes, fewer gates, judges R-11, release per change, metrics | todo | 2026-09-24 11:17 -03 | needs owner decisions (panel §6) |
| B-05 | low | Wave 3 (4.1) | todo | 2026-09-24 11:17 -03 | |
| B-06 | low | HTML: add it / ja / fr / ko — **last, after all changes** (owner) | todo | 2026-09-24 11:17 -03 | |
| B-07 | low | graphify `--update` — deferred to the wave1 archive (REQ-W1-062) | todo | 2026-09-24 11:17 -03 | 3.11.3/3.11.4 hotfix docs not yet in the graph |
| B-08 | info | Matthew reported BUG-18 on 3.11.2 | done | 2026-09-24 11:17 -03 | already fixed in 3.11.3; owner given a message to forward (update to 3.11.4) |
| B-09 | info | agente-kloketen: verify 3.11.4 on a real new session | awaiting-human | 2026-09-24 11:17 -03 | read-only check passed; real-session check pending the owner |
