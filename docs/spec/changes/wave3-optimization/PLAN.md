# Plan: wave3-optimization

**Capability:** method | **Security Tier:** 2 | **Layers:** Backend, Frontend, Infra
**Created:** 2026-09-26 | **Status:** 🔄 architecture + tasks generated (infra skipped) — awaiting the merged *how* gate
**Lane:** feature-ui (the sponsor page and the method page are UI: mockup and design-graphic run)
**Release target:** 4.1.0 (minor, backward compatible with 4.0.0)
**Flow:** trunk (`feature/wave3-optimization` → PR → `main`) · **Decisions:** D-30, D-31, D-32 (D-01..D-29 hold)
**Depends on:** `wave2-structural` (3.13.0 / 4.0.0) merged first

---

## Epic: Wave 3 optimisation — smaller phases, informed sponsors, one portfolio

### Description
Every phase still loads most of the rules transitively; the sponsor learns a change's state only by asking; open
questions and risks have no owner or date; the cost of a change is measured only for judges and teams; each UI change
redesigns the palette; "Feature" means two things; nobody sees all the organisation's repositories at once; the backlog
does not rank; several steps assume one OS, country, language and runtime (panel review 2026-09-23, Ola 3: R-15, R-19,
R-24..R-30). This Epic measures the per-phase context first, adds the data areas, reorganises the skills on top of the
final text, and — last, by the owner's request — adds four languages to the method page (B-06).

North star: *every phase loads only the instructions it declares, and the sponsor of any change can read — from one page
produced from the change's own artifacts — its scope, state, measured cost, open risks and the decisions it waits for,
while the organisation sees every Karvey repo in one read-only portfolio; the per-phase instruction size and the cost per
change are measured before and after, never capped.*

### Strategic value
Instructions a phase does not use cost money and attention on every turn; a sponsor who is not told waits or escalates;
an unowned risk reaches production; an unmeasured change cannot be priced. Wave 3 turns the data Wave 2 started to
record into views for the people who decide, and makes the method cheaper to run and easier to adopt outside the
author's environment.

### Design decisions
| Topic | Decision |
|------|----------|
| Client report | D-31 — one HTML page per change for the sponsor (scope, state, cost, risks), at every gate close, to the stakeholder declared in `project.json` |
| Portfolio and runtimes | D-32 — one portfolio over every Karvey repo of the organisation; Claude Code only; R-30 = portability guide |
| Cost | D-30 — measured, never capped |
| Architecture | `architecture.md` — size tool + one measure before/after; core of seven contracts, closed `Load:` lists, adapters, references, routing-only orchestrator; effort from the statusline capture + transcript usage; sponsor page by allow-list + fail-closed leak check; gate-close script; risk register with `risk_log`; read-only offline portfolio; L-55..L-75 (architect's defaults A-01..A-19, D-21); infra skipped (no cloud) |

---

## Features

Internal order: F1 (baseline) first; F3..F10 add data and views; F2 (reorganisation) runs over the final Wave 3 text;
F11 rollout; **F12 last** (B-06).

| Feature | Area | Requirements covered | Panel / sources | Status |
|---------|------|----------------------|-----------------|--------|
| F1 | Context measurement: size tool, baseline, CI | REQ-W3-001, 002, 010, 011, 071, 072 | R-15 · AG-04, H-34 · BL-18 | ⬜ |
| F2 | Context budget: core, load lists, adapters, references, routing-only orchestrator, contract coverage, generated lists, one phase per session | REQ-W3-003..009, 012, 013 | R-15 · AG-04 · BL-18, BL-39 | ⬜ |
| F3 | Cost per change with a single agent | REQ-W3-014..019, 077 | R-25 · PM-08 · D-30 · BL-28, BL-37 | ⬜ |
| F4 | Sponsor page, report, "your turn" events, deduplication | REQ-W3-020..027, 080 | R-19 · PM-07 · D-31 · BL-22, BL-43 | ⬜ |
| F5 | Open questions Q-NN and risk register | REQ-W3-028..034 | R-24 · PM-11 · BL-27 | ⬜ |
| F6 | Project design system, design delta, contrast tool, design judge | REQ-W3-035..039, 076 | R-26 · DM-13, AG-12 · D-23, D-30 · BL-29 | ⬜ |
| F7 | One work breakdown (WBS) | REQ-W3-040..043 | R-27 · PM-10 · BL-30 | ⬜ |
| F8 | Organisation portfolio | REQ-W3-044..048, 078, 079 | R-28 · PM-14 · D-32 · BL-31, BL-40 | ⬜ |
| F9 | Backlog ranked by WSJF, `done-direct` | REQ-W3-049..052 | R-29 · PM-15 · BL-32 | ⬜ |
| F10 | Portability (guide, browse.via, OS/time neutrality, neutral states, loaded version, settings validation) | REQ-W3-053..060 | R-30 · AG-14 · D-32 · BL-33, BL-38 | ⬜ |
| F11 | Rollout 4.1.0 and dogfooding | REQ-W3-061..065, 073, 074, 075 (064, 065, 073..075 change-scoped) | Ola 3 plan · D-24, D-26, D-31 | ⬜ |
| F12 | **Last:** method page in it / ja / fr / ko, alias table | REQ-W3-066..070 | B-06 · BL-42 | ⬜ |

Coverage: 80 of 80 REQ-W3 in exactly one Feature.

## Tasks

Detail per task (files, requirements, tests, done-when command) in `tasks.md`. Estimates are calibrated to realistic AI execution + review (the default scale ran ~10× high in this repo). 101 tasks (100 agent, 1 `[human]`), 1,059 min total, critical path 242 min. Execution order: F1 (+ E1.F11.T1) → F3..F10 → F2 → F11 → F12 (last) → E1.DEPLOY.

### Feature E1.F1: Context measurement (first: the baseline precedes every move)

- [ ] E1.F1.T1 [Backend] `karvey_lib/loadlist.py`: `declared`, `cited` (fences and footnote definitions excluded), `graph`, `closure`, `size`; `adapters/{tool}` and `?` references → `closure_min` / `closure_max` — est: 12min
- [ ] E1.F1.T2 [Backend] `karvey-context-budget.py measure [--label --json]`: rows per phase skill + orchestrator + `session_hook` row, sorted, no clock, missing `Load:` file → exit 1 with skill, line, file — est: 12min (depends E1.F1.T1)
- [ ] E1.F1.T3 [Backend] `compare BASE [AFTER|--live] [--target-median 40] [--warn-growth 10]`: median `closure_max` reduction, per-phase reason or `unexplained`, exit 1 below target; `::warning::` on growth, exit 0 — est: 10min (depends E1.F1.T2)
- [ ] E1.F1.T4 [Backend] Baseline `docs/spec/retros/context-size-4.0.0.json` in a commit of its own + the order test — est: 6min (depends E1.F1.T2)
- [ ] E1.F1.T5 [Backend] L-62: a `Load:` entry names an existing file (blocking) — est: 6min (depends E1.F1.T1) (P)
- [ ] E1.F1.T6 [Infra] CI: `compare … --live --warn-growth 10` step in the `lint` job — est: 6min (depends E1.F1.T3, E1.F1.T4)

### Feature E1.F3: Cost per change with a single agent

- [ ] E1.F3.T1 [Backend] Schema: `effort[]`, `judge_runs[].tokens_total / usd_estimated / source` — est: 8min
- [ ] E1.F3.T2 [Backend] Statusline cost capture: `{root_key, usd, transcript, context_pct, context_tokens, at}` in `{state_dir}/cost/{session-hash}.json`, no model turn, no repo write — est: 10min
- [ ] E1.F3.T3 [Backend] `karvey_lib/effort.py`: capture pick (latest, two within 120 s → `estimated`), transcript cumulative usage, separate charged file, first close, several changes, gap, new transcript — est: 15min (depends E1.F3.T2)
- [ ] E1.F3.T4 [Backend] `karvey-state.py effort {change} {phase} [--review-min N]` + `validate` reports a non-`phase` kind or a judge figure inside effort — est: 12min (depends E1.F3.T1, E1.F3.T3)
- [ ] E1.F3.T5 [Backend] `validate`: cost-limit keys reported `unsupported (D-30)` as a warning that never changes the exit code (`--strict` too) + L-63 — est: 8min (depends E1.F3.T1) (P)
- [ ] E1.F3.T6 [Backend] Judge cost: `usage.total_tokens` → `exact`; estimate over prompt + every closed input; `collect --transcript auto` (runtime source), agent-reported value kept `estimated`; judges SKILL step 2 text — est: 12min (depends E1.F3.T3) (P)
- [ ] E1.F3.T7 [Backend] Metrics: `cost_per_change`, aggregates per lane, client and period with the estimated share, `phases_per_session`; `--metrics` table and JSON — est: 12min (depends E1.F3.T4)
- [ ] E1.F3.T8 [Backend] `cost_outliers` (3× the lane median, ≥ 3 measured) + retro skill text (input, not verdict) — est: 8min (depends E1.F3.T7)

### Feature E1.F4: Sponsor page, report, "your turn" events, deduplication

- [ ] E1.F4.T1 [Backend] `stakeholders` in project and spec schemas (+ `leak.deny_terms`), `validate` through `check_target`, init pre-fills the PRD Stakeholders section — est: 10min
- [ ] E1.F4.T2 [Backend] `schemas/wording.json` (en, es: phases, lanes, risk states, labels) + L-65 — est: 8min (P)
- [ ] E1.F4.T3 [Backend] `karvey_lib/leakcheck.py` + `leak_patterns.json`: `secret`, `path`, `host`, `email`, `pii`, `client` (+ `deny_terms`); exception = refusal; report without the value — est: 15min (P)
- [ ] E1.F4.T4 [Backend] `karvey_lib/sponsor.py`: allow-listed model (scope, state, cost, risks, questions for the sponsor, gates awaiting the sponsor as approver, released), id/path/command normaliser, `as_of` per figure — est: 15min (depends E1.F4.T1, E1.F4.T2)
- [ ] E1.F4.T5 [Frontend] `templates/sponsor.html`: design-spec tokens, `prefers-color-scheme`, print style, CSP meta, no script needed, 360–1440 px without horizontal scroll + L-64 — est: 15min (P)
- [ ] E1.F4.T6 [Backend] `karvey-sponsor.py build|deliver`: leak check before writing, `sponsor-history.jsonl`, `sponsor-refusals.jsonl`, `no sponsor declared` once; `deliver` builds the payload from the checked model and leak-checks it — est: 15min (depends E1.F4.T3, E1.F4.T4, E1.F4.T5)
- [ ] E1.F4.T7 [Backend] `karvey-context.py --report [--from --to --as-of] [--client]`: released, in progress with phase and age, blocked and who unblocks, open risks, decisions awaited per stakeholder; read-only — est: 12min (depends E1.F4.T2)
- [ ] E1.F4.T8 [Backend] Events `approval_requested`, `awaiting_human`, `blocked`: schema enum, `resolve notifications --event` → stakeholder of the acting role, else team + `no executor declared`; judge verdict on `blocked`; `rules/notifications.md` — est: 12min (depends E1.F4.T1)
- [ ] E1.F4.T9 [Backend] Sent-log `changes/{id}/notifications.jsonl` + `karvey-config.py notify-sent --key`; `qa` first run and verdict change, `deploy` once per version/env, "your turn" once per state; run id + timestamp; qa and deploy text — est: 12min (depends E1.F4.T8)
- [ ] E1.F4.T10 [Backend] `karvey-close.py` (C-26): sponsor build/deliver → due events (sent-log) → `effort` last; each failure reported and the next step runs; `rules/gates.md` closing block = one call + send the payloads — est: 12min (depends E1.F4.T6, E1.F4.T9, E1.F3.T4)
- [ ] E1.F4.T11 [Test] Manual script `sponsor-at-gate.md`: a real gate on a fixture change with a sponsor, page opened offline, refusal case, delivery failure → outbox — est: 5min (depends E1.F4.T10) (P)

### Feature E1.F5: Open questions `Q-NN` and the risk register

- [ ] E1.F5.T1 [Backend] `karvey_lib/questions.py` + `docs/spec/questions.md` format; decisions skill `ask` (id from `karvey-id.py next Q`, owner and needed-by required, optional context), `cross` offers `ask`, answer → `D-NN` citing the `Q-NN`, question kept `resolved → D-NN` — est: 12min
- [ ] E1.F5.T2 [Backend] `validate --all`: a `D-NN` that resolves a missing `Q-NN` is reported — est: 6min (depends E1.F5.T1)
- [ ] E1.F5.T3 [Backend] `karvey_lib/risks.py` + `rules/risks.md` (format, states, who creates it) + `validate` reports a risk without owner + architecture skill creates the register — est: 12min (P)
- [ ] E1.F5.T4 [Backend] `karvey-state.py risk {change} R-N review|close|move|mitigate|accept` + `spec.json:risk_log[]`; `move` reserves `BL-NN` and writes the backlog row — est: 12min (depends E1.F5.T3)
- [ ] E1.F5.T5 [Backend] Dashboard open-work: open `Q-NN` (owner, needed-by, `overdue`, `date invalid`) + open risks of active changes; session hook lists capped at five lines + `+N more` — est: 10min (depends E1.F5.T1, E1.F5.T3)
- [ ] E1.F5.T6 [Backend] Gate summary at *qa* and *release*: open risks with owner, trigger, last review; `risk R-N unreviewed` (warn); `karvey-close.py` step 3 lists the owners to ask — est: 10min (depends E1.F5.T4, E1.F4.T10)
- [ ] E1.F5.T7 [Backend] `advance archived` refuses an `open` risk and a state without a `risk_log` record; archive skill closes or moves through `risk` — est: 10min (depends E1.F5.T4)
- [ ] E1.F5.T8 [Backend] Judges: `"kind": "risk"` → `emergent` row `Routed to: proposed risk`; register-targeting output dropped and reported; iterate accepts into the register — est: 10min (depends E1.F5.T3) (P)

### Feature E1.F6: Project design system, design delta, contrast tool, design judge

- [ ] E1.F6.T1 [Backend] `karvey_lib/designsys.py`: `design-system.md` and `design-delta.md` parsers (tokens, pairs with level, components), colour parsing `#rgb`, `#rrggbb`, `rgb()`, `oklch()` — est: 12min
- [ ] E1.F6.T2 [Backend] `karvey-contrast-check.py [--file|--delta] [--json]`: WCAG 2.x ratio per declared pair vs its level (AA normal default); unparseable → exit 1 naming the token — est: 10min (depends E1.F6.T1)
- [ ] E1.F6.T3 [Backend] `karvey-design.py diff {change}`: delta format (Added / Modified with base value / components / `empty`), undeclared modification reported — est: 10min (depends E1.F6.T1)
- [ ] E1.F6.T4 [Backend] `karvey-design.py apply {change} [--dry-run]`: added tokens written with `Changed by`; a modified token whose current value ≠ base value stops (exit 3) with both values and the last change; archive text asks the human — est: 10min (depends E1.F6.T3)
- [ ] E1.F6.T5 [Backend] Design judge: `rules/judges/design_graphic.md` (lens `design`), `defaults.json` judges phases/lenses, `build_inputs` = delta + "Applies to" mockups (≤ 200 KB each) + rubric + contrast JSON — est: 12min (depends E1.F6.T2)
- [ ] E1.F6.T6 [Backend] design-graphic skill: read the design system, write the delta, art catalogue only on an asset request, the self-score section removed, the design judge before the gate + L-66, L-67 — est: 12min (depends E1.F6.T3, E1.F6.T5)
- [ ] E1.F6.T7 [Test] Manual script `design-judge-gate.md`: a `feature-ui` fixture change without an asset request → no art catalogue; the judge verdict and the contrast result in the gate summary — est: 5min (depends E1.F6.T6) (P)

### Feature E1.F7: One work breakdown (WBS)

- [ ] E1.F7.T1 [Backend] Text: Feature = functional area; phases as an Epic checklist/field; `E{n}.QA` / `E{n}.DEPLOY` natural keys under the Epic; parent/child, dependencies only between siblings; a tool without parent/child records the parent in a field + L-68 — est: 12min
- [ ] E1.F7.T2 [Backend] `karvey-trace.py --wbs {change}`: every task under exactly one Feature (or `E{n}.QA` / `E{n}.DEPLOY`); a requirement across two Features needs `Split:` — est: 10min (P)
- [ ] E1.F7.T3 [Backend] Tracker reconciliation: 4.0 items reported `legacy shape`, root-level QA/deploy items `outside the hierarchy`, never rewritten — est: 8min (depends E1.F7.T1, E1.F7.T2)
- [ ] E1.F7.T4 [Test] Manual script `tracker-wbs.md` on the Markdown tracker: Features = areas, phases on the Epic, `E1.QA` / `E1.DEPLOY` found or created once — est: 5min (depends E1.F7.T3) (P)

### Feature E1.F8: Organisation portfolio

- [ ] E1.F8.T1 [Backend] `client` first-level in project and spec schemas; a change inherits it at init; `validate` warns on a differing tracker tag naming both — est: 10min
- [ ] E1.F8.T2 [Backend] Both spec layouts (`docs/spec/`, `spec/`) in `project.py`, the session hook and the dashboard; `two spec roots` uses `docs/spec/` — est: 12min (P)
- [ ] E1.F8.T3 [Backend] `schemas/portfolio.schema.json` + `karvey_lib/portfolio.py`: entry validation before any read, file reads only, 2 MB per read, `sanitise` on foreign text, `clone` never used — est: 15min (depends E1.F8.T2)
- [ ] E1.F8.T4 [Backend] `karvey-context.py --portfolio [--file --from --to --as-of]`: per client and repository — active changes (phase, lane, age), questions and approvals awaited, releases, cost; `not a Karvey project` — est: 12min (depends E1.F8.T3, E1.F3.T7)
- [ ] E1.F8.T5 [Backend] `--client NAME` (case-insensitive, `other clients: not shown`, `no repositories for client` exit 0) + the printed dashboard command per change (valid id only, `shlex.quote`d path; none for `not read`) — est: 8min (depends E1.F8.T4)
- [ ] E1.F8.T6 [Test] Offline proof in `test_portfolio.py`: `subprocess.Popen` and `socket.socket` patched to fail, every listed repo's file mtimes unchanged, nothing written — est: 6min (depends E1.F8.T4) (P)

### Feature E1.F9: Backlog ranked by WSJF, `done-direct`

- [ ] E1.F9.T1 [Backend] `rules/backlog.md` columns (`Value | Effort | CoD | Needed by | Client | Reviewed | Commit`), formula, `done-direct`; `karvey_lib/backlog.py` (`urgency`, `effort`, `wsjf`, `unscored`) — est: 12min
- [ ] E1.F9.T2 [Backend] `validate` refuses `done-direct` without a commit — est: 6min (depends E1.F9.T1)
- [ ] E1.F9.T3 [Backend] `karvey-context.py --backlog`: open items by score, unscored apart, `stale` > 30 days, `invalid row` with id; read-only — est: 10min (depends E1.F9.T1)
- [ ] E1.F9.T4 [Backend] Refinement cadence: `project.json:backlog.refine_days` (default 14), `Last refinement:` header, dashboard overview line (`overdue`, `never refined`) — est: 8min (depends E1.F9.T1)

### Feature E1.F10: Portability

- [ ] E1.F10.T1 [Backend] `docs/portability.md` (runtime-dependent behaviours, adaptation notes, "Claude Code is the only supported runtime", D-32) + L-69 — est: 12min (P)
- [ ] E1.F10.T2 [Backend] `browse.via` (`local` \| `agent:<name>` \| `none`): schema, `karvey-config.py resolve browse`, browse skill (self-contained instruction with declared URLs only, navigate/read/capture), QA visual dimension `not evaluated` + manual `browse-via-agent.md` — est: 12min (P)
- [ ] E1.F10.T3 [Backend] OS-neutral open in the mockup skill (path + `python3 -m webbrowser <path>`) + L-70 — est: 6min (P)
- [ ] E1.F10.T4 [Backend] No fixed country time: `changelog-policy.md:29` → project `time_zone` or environment, ISO 8601 with offset; `time_zone` in the project schema; statusline comment example `Area/City` + L-71 — est: 8min (P)
- [ ] E1.F10.T5 [Backend] `schemas/incident-states.json` (neutral + localized aliases) in `read_bugs`, L-32 and `rules/incident-tracking.md` — est: 12min (P)
- [ ] E1.F10.T6 [Backend] `karvey_lib/runtime.py loaded_version()` (read-only record) + health skill `loaded X, available Y` / `loaded version unknown` — est: 10min (P)
- [ ] E1.F10.T7 [Backend] `settings invalid ({key} …)` in the session hook and the dashboard from `karvey-config.py resolve`; aliases shown normalised — est: 10min (P)
- [ ] E1.F10.T8 [Backend] L-72: example actors are placeholders or roles; model ids are not actors; existing violations fixed — est: 10min (P)

### Feature E1.F2: Context budget — core, load lists, adapters, references, routing-only orchestrator (after F3..F10)

- [ ] E1.F2.T1 [Backend] `schemas/contracts.json` baseline map (phase → contract, from the 4.0 closure in `context-size-4.0.0.json`) + `contracts` sub-command + CI step + `test_ci_workflow.py` case — est: 12min (depends E1.F1.T4, E1.F1.T6)
- [ ] E1.F2.T2 [Backend] `rules/_core.md`: seven contracts with `{#contract-<id>}` headings, ≤ 1,000 words; `contracts.json` anchors → the core; "footnotes are never opened" + L-55 — est: 12min (depends E1.F2.T1, E1.F3.T8, E1.F4.T11, E1.F5.T6, E1.F5.T7, E1.F5.T8, E1.F6.T7, E1.F7.T4, E1.F8.T5, E1.F8.T6, E1.F9.T4, E1.F10.T1, E1.F10.T2, E1.F10.T3, E1.F10.T4, E1.F10.T5, E1.F10.T6, E1.F10.T7, E1.F10.T8)
- [ ] E1.F2.T3 [Backend] Tracker adapters: `rules/adapters/{markdown,clickup,jira,linear,azure-boards,github-projects,spreadsheet}.md` from `management-adapters.md` + `clickup-protocol.md`; per-tool examples moved out of init, tasks, impl, qa, deploy, archive + L-58 — est: 15min (depends E1.F2.T2)
- [ ] E1.F2.T4 [Backend] `Load:` lines + rule citations → footnotes, batch 1: init, requirements, mockup, design-graphic, architecture, infra, tasks — est: 15min (depends E1.F2.T3)
- [ ] E1.F2.T5 [Backend] `Load:` lines + footnotes, batch 2: impl, test, qa, deploy, archive, iterate, judges, decisions, context, checkpoint — est: 15min (depends E1.F2.T4)
- [ ] E1.F2.T6 [Backend] Rules cite rules only in footnotes (the 26 rules and the adapters) + L-57 — est: 15min (depends E1.F2.T2) (P)
- [ ] E1.F2.T7 [Backend] L-56: every rule or reference path in a skill body (outside footnotes and fences) is in its `Load:` list — est: 8min (depends E1.F2.T5, E1.F2.T6)
- [ ] E1.F2.T8 [Backend] Init references `team-settings.md`, `settings.md` with one-line pointers (load condition) — est: 10min (depends E1.F2.T5)
- [ ] E1.F2.T9 [Backend] Deploy references `docs-only.md`, `hotfix.md`, `postdeploy.md`, `branch-hygiene.md` with pointers + L-59 (orphans; the set equals the closed list) — est: 12min (depends E1.F2.T8)
- [ ] E1.F2.T10 [Backend] Orchestrator routing-only ≤ 1,200 words; feature lists, per-phase descriptions, equivalences, authorship → README and `skills/karvey/references/{overview,equivalences}.md` + L-60 + `test_orchestrator_routing.py` — est: 15min (depends E1.F2.T5)
- [ ] E1.F2.T11 [Backend] `karvey-context-budget.py render [--check]`: the orchestrator's "applies in" column, the adapters' "used by" lines, the README per-phase list between `karvey:generated load-lists` markers + L-61 — est: 10min (depends E1.F2.T10, E1.F2.T3)
- [ ] E1.F2.T12 [Backend] One phase per session: `karvey-close.py` step 5 (checkpoint line; the script compares the capture's context reading with the checkpoint threshold) + checkpoint skill text + `observed --transcript` + manual `one-phase-per-session.md` — est: 10min (depends E1.F4.T10) (P)
- [ ] E1.F2.T13 [Test] After snapshot `docs/spec/retros/context-size-4.1.0.json`; `compare` ≥ 40% median; `contracts` green; per-phase reasons recorded in `contracts.json` — est: 8min (depends E1.F2.T7, E1.F2.T9, E1.F2.T11, E1.F2.T12)

### Feature E1.F11: Rollout 4.1.0 and dogfooding

- [ ] E1.F11.T1 [Backend] `check-modes.json`: `"4.1"` default in every row + the sixteen Wave 3 rows (two blocking); `modes.release_line` maps 4.1.x; L-73 (scheduled first, with F1) — est: 10min (P)
- [ ] E1.F11.T2 [Backend] `validate --fix` proposes `clickup.client_tag` → `client` (diff first, idempotent, never an approval; nothing when `client` is set) — est: 8min (depends E1.F8.T1)
- [ ] E1.F11.T3 [Test] Compatibility 4.0 → 4.1: `compat.json` cases + `test_compat_w3.py` (the 4.0 fixtures pass `validate --strict`, the linter over a fixture project and the guard tables with 4.1 defaults) — est: 12min (depends E1.F2.T13, E1.F11.T1, E1.F11.T2)
- [ ] E1.F11.T4 [Backend] Dogfooding: `spec.json:stakeholders.sponsor` (role "method owner", `channel: none`), effort from the next gate, `sponsor-history.jsonl` with `no page (generator not built yet)` for the gates closed before C-13; the design judge once on this change's design (F-68) — est: 10min (depends E1.F4.T10, E1.F6.T5)
- [ ] E1.F11.T5 [Backend] Hand-off `upgrade-steps.handoff.json`: the fourteen §7.3 rows in the catalogue's field shape, `status: declared` — est: 8min (depends E1.F8.T1, E1.F9.T1, E1.F10.T5, E1.F3.T5) (P)
- [ ] E1.F11.T6 [Test] Whole-repo gate: lint 0, every unit and regression suite, every table, the page tests, `validate --all`, `karvey-trace.py wave3-optimization --check` 80/80 and `--wbs`, `contracts`, `compare`, release manifest maps every commit — est: 10min (depends every agent task of F1..F11 (E1.F11.T5 and E1.F11.T4 included))
- [ ] E1.F11.T7 [Backend] Release docs: `[Unreleased]` summary — context size before/after (both snapshots, median), this change's cost with "single-agent cost before 4.1 not measured", the manual Upgrade list from the hand-off, the 4.0 → 4.1 note; no version or date — est: 6min (depends E1.F11.T6)

### Feature E1.F12: Method page in nine languages — last (B-06)

- [ ] E1.F12.T1 [Frontend] Nine-language scaffold: `LANGS`, head `ok()` list, CSS selectors, language list + `select` under 720 px, `I18N` entries (it, ja, fr, ko), `--font-cjk` stack, `html[lang]` per selection; `test_page_static.py` and `test_page.mjs` for nine — est: 12min (depends E1.F11.T7)
- [ ] E1.F12.T2 [Frontend] Wave 3 section (load lists, sponsor page, questions and risks, cost, design system, portfolio, WSJF, portability guide) with counts, in en, es, pt, de, zh — est: 15min (depends E1.F12.T1)
- [ ] E1.F12.T3 [Frontend] Italian block, part 1 of 3 (the first third of the English block's sections, in `<section id>` order) — est: 12min (depends E1.F12.T2)
- [ ] E1.F12.T4 [Frontend] Italian block, part 2 of 3 — est: 12min (depends E1.F12.T3)
- [ ] E1.F12.T5 [Frontend] Italian block, part 3 of 3 (incl. the Wave 3 section) — est: 12min (depends E1.F12.T4)
- [ ] E1.F12.T6 [Frontend] Japanese block, part 1 of 3 — est: 12min (depends E1.F12.T2) (P)
- [ ] E1.F12.T7 [Frontend] Japanese block, part 2 of 3 — est: 12min (depends E1.F12.T6)
- [ ] E1.F12.T8 [Frontend] Japanese block, part 3 of 3 — est: 12min (depends E1.F12.T7)
- [ ] E1.F12.T9 [Frontend] French block, part 1 of 3 — est: 12min (depends E1.F12.T2) (P)
- [ ] E1.F12.T10 [Frontend] French block, part 2 of 3 — est: 12min (depends E1.F12.T9)
- [ ] E1.F12.T11 [Frontend] French block, part 3 of 3 — est: 12min (depends E1.F12.T10)
- [ ] E1.F12.T12 [Frontend] Korean block, part 1 of 3 — est: 12min (depends E1.F12.T2) (P)
- [ ] E1.F12.T13 [Frontend] Korean block, part 2 of 3 — est: 12min (depends E1.F12.T12)
- [ ] E1.F12.T14 [Frontend] Korean block, part 3 of 3 — est: 12min (depends E1.F12.T13)
- [ ] E1.F12.T15 [Backend] L-74: every translatable key and section in nine languages, none empty — est: 8min (depends E1.F12.T5, E1.F12.T8, E1.F12.T11, E1.F12.T14)
- [ ] E1.F12.T16 [Frontend] Anchor aliases: `ANCHOR_ALIASES` (the anchors renamed after 3.10.0, from `git log -p docs/karvey.html`) on load and `hashchange`, every language + L-75 + page test — est: 10min (depends E1.F12.T1) (P)
- [ ] E1.F12.T17 [Backend] L-11 extended: the page's Wave 3 counts (skills, rules, scripts) match the plugin in every language — est: 6min (depends E1.F12.T2) (P)
- [ ] E1.F12.T18 [Test] Final gate: lint 0, page and unit suites, `karvey-trace.py wave3-optimization --check` 80/80, and the plan-order check (every F12 task after the last task of every other feature) — est: 8min (depends E1.F12.T15, E1.F12.T16, E1.F12.T17)

### Epic item E1.DEPLOY

- [ ] E1.DEPLOY.T1 [human] The prod OK for the release that ships this change (D-10) — executor: the owner (depends E1.F12.T18)

## Task status
> Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked · 🙋 awaiting-human (blocked on a person)`

| Task | Status | estimate_min | actual_ai_min | actual_review_min | Notes |
|------|--------|--------------|---------------|-------------------|-------|
| E1.F1.T1 [Backend] | ✅ done | 12 | 10 | 0 |  |
| E1.F1.T2 [Backend] | ✅ done | 12 | 12 | 0 |  |
| E1.F1.T3 [Backend] | ✅ done | 10 | 6 | 0 |  |
| E1.F1.T4 [Backend] | ✅ done | 6 | 8 | 0 |  |
| E1.F1.T5 [Backend] | ✅ done | 6 | 5 | 0 |  |
| E1.F1.T6 [Infra] | ✅ done | 6 | 5 | 0 |  |
| E1.F3.T1 [Backend] | ✅ done | 8 | 6 | 0 |  |
| E1.F3.T2 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F3.T3 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F3.T4 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F3.T5 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F3.T6 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F3.T7 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F3.T8 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F4.T1 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F4.T2 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F4.T3 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T4 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T5 [Frontend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T6 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T7 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T8 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T9 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T10 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T11 [Test] | ⬜ todo | 5 | — | — |  |
| E1.F5.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F5.T2 [Backend] | ⬜ todo | 6 | — | — |  |
| E1.F5.T3 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F5.T4 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F5.T5 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F5.T6 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F5.T7 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F5.T8 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F6.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F6.T2 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F6.T3 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F6.T4 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F6.T5 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F6.T6 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F6.T7 [Test] | ⬜ todo | 5 | — | — |  |
| E1.F7.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F7.T2 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F7.T3 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F7.T4 [Test] | ⬜ todo | 5 | — | — |  |
| E1.F8.T1 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F8.T2 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F8.T3 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F8.T4 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F8.T5 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F8.T6 [Test] | ⬜ todo | 6 | — | — |  |
| E1.F9.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F9.T2 [Backend] | ⬜ todo | 6 | — | — |  |
| E1.F9.T3 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F9.T4 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F10.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F10.T2 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F10.T3 [Backend] | ⬜ todo | 6 | — | — |  |
| E1.F10.T4 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F10.T5 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F10.T6 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F10.T7 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F10.T8 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F2.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F2.T2 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F2.T3 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F2.T4 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F2.T5 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F2.T6 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F2.T7 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F2.T8 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F2.T9 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F2.T10 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F2.T11 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F2.T12 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F2.T13 [Test] | ⬜ todo | 8 | — | — |  |
| E1.F11.T1 [Backend] | ✅ done | 10 | 12 | 0 |  |
| E1.F11.T2 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F11.T3 [Test] | ⬜ todo | 12 | — | — |  |
| E1.F11.T4 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F11.T5 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F11.T6 [Test] | ⬜ todo | 10 | — | — |  |
| E1.F11.T7 [Backend] | ⬜ todo | 6 | — | — |  |
| E1.F12.T1 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T2 [Frontend] | ⬜ todo | 15 | — | — |  |
| E1.F12.T3 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T4 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T5 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T6 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T7 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T8 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T9 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T10 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T11 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T12 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T13 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T14 [Frontend] | ⬜ todo | 12 | — | — |  |
| E1.F12.T15 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F12.T16 [Frontend] | ⬜ todo | 10 | — | — |  |
| E1.F12.T17 [Backend] | ⬜ todo | 6 | — | — |  |
| E1.F12.T18 [Test] | ⬜ todo | 8 | — | — |  |
| E1.DEPLOY.T1 [human] | ⬜ todo | — | — | — | human: the owner |

`estimate_min` is written here once; impl fills the two actual columns and never edits the estimate.

## History
| Date | Phase | Action |
|-------|------|--------|
| 2026-09-26 | init | Change initialised (state tool), lane `feature-ui`; prd.md; spec.json validated `--strict` |
| 2026-09-26 | requirements | requirements.md (70 REQ-W3, 11 areas), spec-delta.md (ADDED 70, MODIFIED 6, REMOVED 0), Features F1..F12; generated — awaiting the *what* gate |
| 2026-09-26 | iterate | Second iteration, pre-approval (D-21): mockup spec-gaps F-35..F-41 and judge findings F-11, F-20, F-22, F-26, F-32, F-34 amended in place — REQ-W3-071..080 added (splits of 002, 011, 065; design-system conflict; judge cost source; portfolio client filter and drill-down; state wording), spec-delta ADDED 75 · MODIFIED 10 · change-scoped 5; mockup and design-spec rippled — awaiting the *what* gate |
| 2026-09-26 | architecture | architecture.md (26 components, REQ-W3 80/80 → component and test), risks.md (R-1..R-9); judges security, methods, agents-cost (intra-model, all `concerns`; 40 findings F-42..F-81, 4 High) — 39 fixed in place, F-71 rejected (already held by the per-channel target pattern); judge cost recorded US$ 0.65 `estimated` by the 4.0 tool (≈ 43k input tokens per lens) while the runtime reported ≈ 102k tokens per lens (≈ 306k), the gap REQ-W3-077 closes; generated |
| 2026-09-26 | infra | skipped — no cloud resources (`cloud.provider: none`); the one CI step is an impl task (A-16) |
| 2026-09-26 | tasks | tasks.md: 101 tasks (100 agent, 1 `[human]`), 1,059 min calibrated, critical path 242 min; REQ-W3 80/80 (`karvey-trace.py`: 0 uncovered); method-page translations last (F12); generated — awaiting the merged *how* gate |
