# Incident tracker — karvey

`BUG-NN` incidents with state history (`plugins/karvey/skills/karvey/rules/incident-tracking.md`). The
sequence never resets: read this file before adding one and continue the counter. Global index:
`docs/spec/incidents-index.md`.

Tracker: none (`project.json:management.tool = markdown`); the per-change inbox is `findings.md`.
State history times are Chile time (UTC-3), taken from the QA reports and the file timestamps of the fix.

## BUG-01 — `karvey-init --settings` created a phantom change and a real tracker Epic
- **Priority:** high
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/skills/karvey-init/SKILL.md (Step 3.2, argument-hint)
- **Change / origin:** team-adapters (F-01; sources N-01, N-09; retroactive QA D7)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Run `/karvey:karvey-init --settings` in a project whose `project.json` lacks `notifications`/`management` (the command the session hook recommended). With no grill summary, Step 1 asks for the problem; any answer leads Step 2 to a change-id and Steps 6-9A to create `docs/spec/changes/<id>/`, `spec.json`, `prd.md` and an Epic in the configured tracker.

### Actual vs expected
- Actual: a phantom change and a real Epic in the team's tracker, on every run; re-running also overwrote both blocks without the current values (N-09).
- Expected: settings only; nothing created under `docs/spec/changes/` or in any tracker; current values pre-filled and merged.

### Root cause
The skill is a linear sequence 1->10 and `--settings` was only mentioned inside Step 3.2; there was no instruction to stop after it. The argument-hint (`<change-id> ... | --settings`) implied exclusivity that the steps never enforced.

### Fix
Hotfix 3.11.2, branch `hotfix/karvey-3.11.2-settings-nudge`: new **Step 0 — settings-only mode — STOP** in `karvey-init/SKILL.md` (read project.json, run Step 3.2 pre-filled with current values, merge by key keeping untouched keys, write, report, stop; never a change-id, spec.json, prd.md or tracker item). Step 3.2 points to Step 0. The session notice now says "settings only, it creates no change and nothing in any tracker".

### Regression test
`plugins/karvey/hooks/tests/test-hooks.sh`, case "notice says settings-only (BUG-01 guard)". The skill itself is agent instructions and has no executable test; the guard covers the entry point that recommended the command.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:34 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D7 (N-01, blocker) |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | no stop condition after Step 3.2 (read of SKILL.md:5,16-27,47-52,133-262) |
| 2026-09-23 18:59 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | Step 0 settings-only mode on hotfix/karvey-3.11.2-settings-nudge |
| 2026-09-23 19:01 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | test-hooks.sh 21/21 on the fix; fails against the 3.11.1 hooks |

## BUG-02 — The session-hook settings nudge fired where it should not and mis-read project.json
- **Priority:** medium
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-session-context.sh (`settings_nudge`)
- **Change / origin:** team-adapters (F-02; sources S-06 = E-10 = I-04, S-05 = E-07, E-02, E-08, E-09, E-11, E-12, E-13, N-11)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
- `CLAUDE_PROJECT_DIR` = any repo with a bare `docs/spec/` (OpenAPI, RFCs, an STT study): the notice fired (60 of 64 folders measured).
- Nested layout: team root with a complete `project.json`, session in `team/repoA` with its own `docs/spec/`: "settings missing".
- `project.json` with a UTF-8 BOM: "unreadable". `[]` / `"x"`: no notice (AttributeError swallowed). `{"notifications":{},"management":{}}`: silent. No python3: silent.
- `CLAUDE_PROJECT_DIR=bare` (relative): the hook hangs (rc=124 under `timeout 3`).

### Actual vs expected
- Actual: wrong scope, wrong file, fragile parsing, a hang, and a line worded as an order to the agent ("run `/karvey:karvey-init --settings`").
- Expected: a notice only in a Karvey project, about the project root already resolved, robust to BOM / non-object / empty blocks / missing python3, never hanging, worded as information for the user.

### Root cause
`settings_nudge` treated any `docs/spec/` as a Karvey project (REQ-ADP-003 wording), always walked from `$START` ignoring `$ROOT`, only wrapped `json.load` in the `try`, used `encoding='utf-8'`, checked `isinstance(dict)` without emptiness, and copied the `dirname` loop that never reaches `/` from a relative path.

### Fix
Hotfix 3.11.2: Karvey marker required (`docs/spec/project.json` or `docs/spec/changes/`); `${ROOT:-$START}`; `utf-8-sig`; non-object and empty blocks reported; explicit "python3 not available" line; `START` normalised with `cd && pwd -P`; informational wording. Script header comment updated (E-12 header part). Not in this fix: hooks/README paragraph (BUG-16) and the REQ-ADP-003 text / startup-only emission (spec-gap F-34).

### Regression test
`plugins/karvey/hooks/tests/test-hooks.sh`, section "session-context: settings nudge (BUG-02)" (10 cases).

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D1/D2/D4 (S-05, S-06, E-02, E-07..E-13, I-04), D7 N-11 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | reproduced in the scratchpad copies; causes above |
| 2026-09-23 18:59 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | settings_nudge rewritten on hotfix/karvey-3.11.2-settings-nudge |
| 2026-09-23 19:01 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | test-hooks.sh 21/21 on the fix; the 7 BUG-02 cases that exercise the defects fail on 3.11.1 |

## BUG-03 — An odd `resets_at` took the whole statusline down; time left was truncated
- **Priority:** medium
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-statusline.sh (`_reset`)
- **Change / origin:** team-adapters (F-03; sources S-03 = E-01 = I-07, E-03, E-04)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Pipe a statusline payload whose `rate_limits.five_hour.resets_at` is milliseconds, an ISO string, `"abc"`, `1e400`, `"nan"` or `[1]`. For truncation: `resets_at = now + 5400`.

### Actual vs expected
- Actual: `⚠️ karvey statusline down (rc=1): ValueError ...` — context, limits and the TIME TO ROTATE warning disappear; past/sub-minute resets show a stale clock and `(0m)`; `now+5400` shows `1h29m`/`1h30m` depending on the second, `now+18000` shows `4h59m`.
- Expected: a decorative suffix never breaks the line; ms and ISO accepted; odd values omitted; time left rounded.

### Root cause
Only the `ZoneInfo` lookup was inside a `try`; `float(ts)` and `fromtimestamp` were not. The countdown used floor division on seconds.

### Fix
Hotfix 3.11.2: whole `_reset` body in `try/except -> ''`; string -> float or `fromisoformat`; NaN/inf rejected; `> 1e11` treated as ms; past or `> 400 d` omitted; minutes rounded, minimum `1m`. Noted in the CHANGELOG for hand-installed copies.

### Regression test
`plugins/karvey/hooks/tests/test-hooks.sh`, section "statusline: reset time (BUG-03 ...)" (9 input cases + rounding).

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:24 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D1 S-03, D2 E-01/E-03/E-04, D4 I-07 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | reproduced; `try` scope too narrow, floor division |
| 2026-09-23 19:00 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | `_reset` rewritten on hotfix/karvey-3.11.2-settings-nudge |
| 2026-09-23 19:01 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | test-hooks.sh 21/21 on the fix; 7 BUG-03 cases fail on 3.11.1 |

## BUG-04 — The statusline debug copy used a fixed /tmp path, shared across OS users and world-readable
- **Priority:** medium
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-statusline.sh (debug dump, line ~18)
- **Change / origin:** team-adapters (F-04; source S-02 — pre-existing, outside the range, but the range edited this file)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
On a multi-user Linux host with `TMPDIR` unset, run the statusline as two OS users. `/tmp/.karvey-statusline-last.json` is created by the first (mode 664) and holds its session id, transcript path and cwd; the second user's write fails silently and its error pointer references the other user's data. Reproduced live on haintech-lab (file owned by another OS user).

### Actual vs expected
- Actual: cross-user information disclosure; whoever creates the file first owns the path.
- Expected: a per-user, private debug copy.

### Root cause
`DBG="${TMPDIR:-/tmp}/.karvey-statusline-last.json"` with the default umask (CWE-377).

### Fix
Hotfix 3.11.2: `DBG="${TMPDIR:-/tmp}/.karvey-statusline-last.$(id -u).json"` written under `umask 077`; hooks/README updated.

### Regression test
`plugins/karvey/hooks/tests/test-hooks.sh`, case "debug copy is per user and mode 600". Caveat found while verifying (fixed before merge: the test now isolates TMPDIR): the case only checks the file exists with mode 600, so on a machine where an earlier run of the fixed hook left that file it passes even against the old hook (that is why the suite fails 15/21 on 3.11.1 in a used TMPDIR and 15/21 in a clean one). The test should delete the file before running the statusline; to be tightened in wave1-hardening (plugins/ was out of scope for this documentation task).

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:24 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D1 S-02, reproduced live |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fixed name + default umask |
| 2026-09-23 19:00 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | per-uid path + umask 077 on hotfix/karvey-3.11.2-settings-nudge |
| 2026-09-23 19:01 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | test-hooks.sh 21/21 on the fix; case fails on 3.11.1 in a clean TMPDIR (see caveat) |

## BUG-05 — impl decides dependencies and resume with states that no longer exist
- **Priority:** high
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/skills/karvey-impl/SKILL.md:31,35-37,137,143
- **Change / origin:** team-adapters (F-07; source N-08)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Resume `karvey-impl` on a change whose [DB] tasks are done: they sit at `👀 review` (impl's new end state, and no skill moves them to `done`, F-06). The skill picks the "first pending task" and waits "until its dependent [DB] is completed".

### Actual vs expected
- Actual: "completed" read as `done` -> no [Backend] task ever starts (deadlock); an orphan `in_progress` after a crash is skipped or re-run depending on the reading; the source for "pending" (tracker, PLAN.md, tasks.md) is unstated.
- Expected: logical states only (REQ-ADP-021): next = first `todo` or orphan `in_progress`; a dependency is satisfied at `review` or `done`; one declared source for resuming, drift reported.

### Root cause
Confirmed by reading the text (a skill is agent instructions; there is no task-picker code to execute): the 3.10 rewrite changed impl's end state to `review` but left the pre-3.10 words `pending`/`completed` in the selection and dependency rules. The E1.F12 text work rewrote the selection rule (`karvey-impl/SKILL.md:39`, logical states, one declared source, drift reported) but left the two dependency bullets saying "until its dependent [DB] is completed" (F-39).

### Fix
On `feature/wave1-hardening` (F-39): the dependency bullets now read "Start a [Backend] task only when the [DB] tasks it depends on are at `review` or `done`" (same for [Frontend]); the Step 2 lead-in states the rule once (a dependency is satisfied at `review` or `done`, never only at `done`); Steps 5 and 7 no longer speak of "completed" tasks. New lint check **L-36** fails when karvey-impl's selection/dependency/resume text uses a state no skill writes (`pending`, `completed`, `finished`), waits for `done` only, or does not state the `review`-or-`done` rule.

### Regression test
L-36 (karvey-impl selects and resumes in logical states) in `plugins/karvey/scripts/lint-plugin.py`: red on `main` (5 errors: "first pending task", "next pending task", both "is completed" dependency bullets, rule not stated), green here. Unit: `plugins/karvey/tests/unit/test_lint_plugin.py` (`L36`: completed dependency, first pending task, done-only dependency, rule not stated fail; "completed" outside the rule and code blocks pass). Indexed in `plugins/karvey/tests/regression/test_incidents.py`; the agent-behaviour script `plugins/karvey/tests/manual/impl-resume.md` stays as QA evidence.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:34 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D7 N-08; raised to high with C-02/I-12 |
| 2026-09-24 08:20 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | residue at karvey-impl/SKILL.md:40-41 confirmed (F-39) |
| 2026-09-24 08:20 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | dependency bullets rewritten to `review` or `done`; L-36 added |
| 2026-09-24 08:25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | L-36 red on main (5), green here; test_lint_plugin.py L36 and test_incidents.py pass |

## BUG-06 — `project.json:management` as a legacy string breaks the `!= markdown` guards
- **Priority:** high
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/skills/karvey-iterate/SKILL.md:61, karvey/rules/backlog.md:10, karvey/rules/management-adapters.md:43-47, karvey-init Step 3.2
- **Change / origin:** team-adapters (F-08; sources I-02, C-03)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A repo whose `project.json` has `"management": "markdown"` (15 HainTech repos; `"clickup"` in qcheck-v3). Route a finding with karvey-iterate or add a backlog item.

### Actual vs expected
- Actual: `project.json:management.tool` is undefined on a string; "undefined != markdown" is true, so a Markdown-only repo is sent to "create/link the item in the tracker". init Step 3.2 re-asks from zero and does not offer the known ClickUp list.
- Expected: a legacy string is read as `{"tool": "<string>"}` (and `project.json:clickup.backlog_list_id` as `location`), init pre-fills and confirms, and the guards test "a tracker tool is resolved and it is not markdown".

### Root cause
The pre-3.10 schema never defined `project.json:management`; sessions added it ad hoc as a string. 3.10 reused the key as an object with no migration; the compatibility text in management-adapters.md describes a state project.json never had (the string lived in spec.json).

### Fix
On `feature/wave1-hardening`: `karvey-config.py resolve management` reads a legacy string as `{"tool": "<string>"}` and `project.json:clickup.backlog_list_id` as `location` (E1.F7.T2, 9c1a5cb); `karvey-state.py validate --fix` migrates the file (E1.F3.T2, aba6752); every skill and rule tests `external` from the resolver instead of `!= markdown` (E1.F12.T3, T6, T10). L-28 (E1.F10.T5, 165795e) forbids the `!= markdown` test.

### Regression test
L-28 (no `!= markdown` test, no direct `clickup.backlog_list_id` read) fails on `main` (14 errors) and passes on this branch; unit: `plugins/karvey/tests/unit/test_config_resolve.py` (`LegacyShapes`: string, `none`, clickup string with `backlog_list_id`; `LegacyProjectFixtures.test_resolve_management` over the anonymised project.json fixtures) and `plugins/karvey/tests/unit/test_state_fix.py` (`Management.test_project_string`, `Management.test_spec_none_to_markdown_and_string_kept`). `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:28 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D4 I-02, D3 C-03 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | 16 files measured; schema collision confirmed against ffb6df9 project-config.md |
| 2026-09-24 04:09 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | resolver `karvey-config.py resolve management` reads a string as `{"tool": …}` and `clickup.backlog_list_id` as `location` (E1.F7.T2, 9c1a5cb); `validate --fix` migrates it (E1.F3.T2, aba6752); the `!= markdown` tests replaced by `external` in iterate, backlog, management-adapters and init (E1.F12.T3/T6/T10, 481503c, 122223d, 43e6f7d) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | L-28 red on main (14), green here; test_config_resolve.py and test_state_fix.py pass; test_incidents.py 10/10 |

## BUG-07 — README and plugin.json still describe ClickUp as the tracker
- **Priority:** medium
- **Detected:** 2026-09-23 · **Component:** README.md:52,117-119; plugins/karvey/.claude-plugin/plugin.json:4
- **Change / origin:** team-adapters (F-09; sources C-05, C-06)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Read README:52 ("Epic (ClickUp) or PLAN.md"), :117-119 and the plugin.json description ("discovery backlog (Markdown + ClickUp)").

### Actual vs expected
- Actual: public text says ClickUp; README:95-99 and the rules say "the team's tracker".
- Expected: "the team's tracker" everywhere.

### Root cause
The 3.10 sweep replaced ClickUp wording in skills and rules but not in README and plugin.json.

### Fix
On `feature/wave1-hardening`, E1.F12.T11 (842f8b8): README.md, plugins/karvey/README.md and the plugin.json / marketplace.json descriptions name the team's configured tracker; ClickUp appears only as one option.

### Regression test
L-31 (README and plugin.json present the tracker as the team's configured one; E1.F10.T6, 2bed707): 5 errors on `main`, 0 on this branch. `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:28 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D3 C-05/C-06 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | lines located |
| 2026-09-24 04:07 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | README.md and plugin.json descriptions present the team's configured tracker (E1.F12.T11, 842f8b8) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | L-31 red on main (5), green here; test_incidents.py 10/10 |

## BUG-08 — An invalid `KARVEY_TZ` silently falls back to the system zone
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-statusline.sh (`_reset`, zone lookup)
- **Change / origin:** team-adapters (F-22; sources S-04 = E-05)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`KARVEY_TZ=Mars/Olympus` (or a typo) and a valid `resets_at`.

### Actual vs expected
- Actual: the system-zone time with no hint (still true after hotfix 3.11.2).
- Expected: fallback with a visible marker, e.g. `↻18:52 (TZ?)`; the zone computed once.

### Root cause
`except Exception: tz = None` with no signal. Security side verified: `zoneinfo` rejects traversal; the value never reaches a shell.

### Fix
On `feature/wave1-hardening`, E1.F11.T1 (9165be1): `karvey-statusline.sh` falls back to the system zone with a visible `(TZ?)` marker and computes the zone once.

### Regression test
`plugins/karvey/tests/hooks/tables/statusline.json` cases `statusline-01-valid-tz-no-marker`, `statusline-02-invalid-tz-marked`, `statusline-03-no-tz-no-marker` (run by `run_tables.py` and `test-hooks.sh`). `statusline-02` fails with the `main` statusline script and passes on this branch. `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:24 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D1 S-04, D2 E-05 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | silent except branch |
| 2026-09-24 02:53 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | statusline marks an invalid zone `(TZ?)`, zone computed once (E1.F11.T1, 9165be1) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | statusline.json 8/8; statusline-02 fails against the main script; test_incidents.py 10/10 |

## BUG-09 — Stray separator when only the 7-day window is present
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-statusline.sh (limit line)
- **Change / origin:** team-adapters (F-23; source E-06)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`rate_limits` with only `seven_day`.

### Actual vs expected
- Actual: `limit · 7d 29% ↻Thu 17:23 (1d0h)`.
- Expected: `limit 7d 29% ...`.

### Root cause
The ` · ` prefix is hard-coded on the 7-day part instead of joining the present windows.

### Fix
On `feature/wave1-hardening`, E1.F11.T1 (9165be1): the limit parts are collected and joined with `' · '`, so a lone 7-day window has no leading separator.

### Regression test
`plugins/karvey/tests/hooks/tables/statusline.json` cases `statusline-04-only-7d-no-leading-separator`, `statusline-05-both-windows-one-separator`, `statusline-06-only-5h`. `statusline-04` fails with the `main` statusline script (`limit ·`) and passes on this branch. `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-06 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | still present after hotfix 3.11.2 |
| 2026-09-24 02:53 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | statusline joins the present windows with ' · ' (E1.F11.T1, 9165be1) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | statusline.json 8/8; statusline-04 fails against the main script; test_incidents.py 10/10 |

## BUG-10 — `docs/karvey.html`: a malformed hash throws `URIError` before the language switch binds
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (`mapHash`, `decodeURIComponent`)
- **Change / origin:** team-adapters (F-24; sources S-07 = E-15)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Open `karvey.html?lang=es#%E0%A4%A`, then click DE.

### Actual vs expected
- Actual: `Uncaught URIError: URI malformed`; the switcher handlers are never attached; the click falls back to a full reload and the section is lost. No XSS.
- Expected: a malformed hash is ignored.

### Root cause
`decodeURIComponent` without `try/catch`, called before `switcher.forEach`.

### Fix
On `feature/wave1-hardening`, E1.F11.T2 (9f0e1d9): the page script is split into pure functions; `safeDecodeHash` returns null on a malformed hash, and `init` binds the switch regardless.

### Regression test
`plugins/karvey/tests/page/test_page.mjs`: "safeDecodeHash returns null for a malformed or empty hash, never throws (BUG-10)" and "init with a malformed hash still binds the switch; DE changes language with no reload (BUG-10, REQ-W1-102)" (`node --test plugins/karvey/tests/page/`). Against the `main` page the file fails: the script has none of these functions. `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:24 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D1 S-07, D2 E-15 (reproduced in node / jsdom) |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | unguarded decode |
| 2026-09-24 02:57 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | `safeDecodeHash` never throws; the switch binds first (E1.F11.T2, 9f0e1d9) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | node --test 22/22; fails against the main page; test_incidents.py 10/10 |

## BUG-11 — An invalid `?lang=` saves the browser language as the viewer's choice
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (main script `remember` test vs early pick)
- **Change / origin:** team-adapters (F-25; source E-14)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
jsdom with `?lang=xx` and navigator `es`; `?lang=es-CL` and navigator `de`.

### Actual vs expected
- Actual: es / de shown and saved to `localStorage['karvey-lang']`, a language the viewer never chose; `es-CL` ignored silently.
- Expected: remember only a valid URL value; optionally accept `xx-YY` by its first 2 letters in both scripts.

### Root cause
The main script's `/[?&]lang=/` is looser than the early script's `[a-zA-Z]{2}(?:&|$)`.

### Fix
On `feature/wave1-hardening`, E1.F11.T2 (9f0e1d9): one language rule (`langOf`, `pickLang`) in both scripts; an invalid `?lang=` is ignored and nothing is saved; `xx-YY` is read by its first two letters.

### Regression test
`plugins/karvey/tests/page/test_page.mjs`: "pickLang: a ?lang= link is one-off when a choice was saved (BUG-11, REQ-W1-103)", "pickLang: an invalid ?lang= is ignored and nothing is saved; the browser rule applies", "init: ?lang=xx saves nothing (BUG-11)", and "the early head script follows the same language rule". `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-14 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | regex mismatch between the two scripts |
| 2026-09-24 02:57 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | `pickLang`: only a valid `?lang=` is remembered, and only when nothing was saved (E1.F11.T2, 9f0e1d9) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | node --test 22/22; fails against the main page; test_incidents.py 10/10 |

## BUG-12 — Switching language drops the other query parameters
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (switcher `replaceState`)
- **Change / origin:** team-adapters (F-26; source E-16)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Open `?foo=1&lang=es`, click DE.

### Actual vs expected
- Actual: URL becomes `?lang=de`.
- Expected: `?foo=1&lang=de`.

### Root cause
The URL is rebuilt as `'?lang=' + req` instead of editing `URLSearchParams`.

### Fix
On `feature/wave1-hardening`, E1.F11.T2 (9f0e1d9): `withLang` changes only the `lang` parameter and keeps the others.

### Regression test
`plugins/karvey/tests/page/test_page.mjs`: "withLang changes only lang and keeps the other parameters (BUG-12, REQ-W1-104)" and "init: switching keeps the other query parameters (BUG-12)". `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-16 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | query string rebuilt from scratch |
| 2026-09-24 02:57 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | `withLang` edits only `lang` in `URLSearchParams` (E1.F11.T2, 9f0e1d9) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | node --test 22/22; fails against the main page; test_incidents.py 10/10 |

## BUG-13 — No `hashchange` handling on the method page
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (hash mapping at load only)
- **Change / origin:** team-adapters (F-27; source E-18)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
With es shown, paste or click `#en-foo` in the same document.

### Actual vs expected
- Actual: no scroll; the target is in a hidden block.
- Expected: the same `mapHash` + `replaceState` + jump logic as at load.

### Root cause
The mapping runs only once at load; there is no `hashchange` listener.

### Fix
On `feature/wave1-hardening`, E1.F11.T2 (9f0e1d9): `init` binds `hashchange` and reuses `hashToBlock` + `replaceState` + jump.

### Regression test
`plugins/karvey/tests/page/test_page.mjs`: "init binds hashchange and jumps to the shown block (BUG-13, REQ-W1-105)" and "hashchange to a hash with no equivalent stays put without error". `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-18 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | missing listener |
| 2026-09-24 02:57 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | `init` binds `hashchange` to the same mapping as at load (E1.F11.T2, 9f0e1d9) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | node --test 22/22; fails against the main page; test_incidents.py 10/10 |

## BUG-14 — Without JS the language switch is shown but does nothing
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (CSS blocks ~105-112, switch links ~309-315)
- **Change / origin:** team-adapters (F-28; source N-12)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Disable JavaScript, click ES.

### Actual vs expected
- Actual: reloads with `?lang=es`, still English, EN still marked current.
- Expected: the control hidden without JS (`html:not([data-lang]) .langs{display:none}`) or a `<noscript>` note. English without JS (REQ-ADP-031) is already met.

### Root cause
Language selection depends on JS setting `data-lang`; the links are always rendered.

### Fix
On `feature/wave1-hardening`, E1.F11.T2 (9f0e1d9): the switch links sit in a container hidden by CSS until the scripts add the `js` class to `<html>`; English still renders without JS.

### Regression test
`plugins/karvey/tests/unit/test_page_static.py` (`NoInertSwitch`: `test_switch_links_are_inside_a_hidden_container`, `test_css_hides_the_switch_until_js`, `test_scripts_add_the_js_class`; 3 failures against the `main` page) and `plugins/karvey/tests/page/test_page.mjs` "init shows the switch (hidden without JS, BUG-14) and marks html.js". `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:34 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D7 N-12 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | control rendered without its JS dependency |
| 2026-09-24 02:57 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | switch hidden until the script sets `html.js` (E1.F11.T2, 9f0e1d9) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | test_page_static.py 10/10 here, 3 failures against the main page; node --test 22/22; test_incidents.py 10/10 |

## BUG-15 — `clickup-sync-guard` hook referenced but nothing installs it
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/skills/karvey/rules/phase-close.md:41
- **Change / origin:** team-adapters (F-29; source C-10)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Read phase-close.md:41; `karvey-guard` manages only git-flow and plan-gate; `hooks/` has no such script.

### Actual vs expected
- Actual: the rule promises a hook that does not exist (the diff edited the line to add "tracker-agnostic" instead of resolving it).
- Expected: rename to `tracker-sync-guard` and mark it described-only, or drop the sentence.

### Root cause
Leftover reference to a planned hook.

### Fix
On `feature/wave1-hardening`: the sentence is gone from `rules/phase-close.md` (E1.F12.T10, 43e6f7d); `hooks/README.md` names `clickup-sync-guard` / `standards-guard` only as not shipped (E1.F12.T11, 842f8b8).

### Regression test
L-15 (every hook named in skills or rules exists in hooks.json or the dispatcher and has guard-table cases; E1.F10.T4, 91758e0): it reports `phase-close.md:41 … clickup-sync-guard is cited but the plugin does not ship it` on `main` (9 errors) and 0 on this branch. `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:28 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D3 C-10 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | no installer anywhere in the plugin |
| 2026-09-24 04:09 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | phase-close.md no longer promises `clickup-sync-guard`; hooks/README names it as not shipped (E1.F12.T10/T11, 43e6f7d, 842f8b8) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | L-15 red on main (9, incl. phase-close.md:41), green here; test_incidents.py 10/10 |

## BUG-16 — hooks/README says the session hook prints nothing without team/agent files
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/README.md:18-19
- **Change / origin:** team-adapters (F-30; sources C-18, E-12 README part)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Read hooks/README.md:18-19 ("With none of them it prints nothing and exits 0.") and run the hook in a Karvey project without settings.

### Actual vs expected
- Actual: README says nothing is printed; the hook prints the one-line settings notice. Still true after hotfix 3.11.2 (only the script header was updated).
- Expected: "...except, inside a Karvey project lacking team settings, a one-line notice."

### Root cause
The 3.10 diff touched hooks/README but not this paragraph.

### Fix
Text fixed in hotfix 3.11.2 (hooks/README.md states the Karvey-project exception). On `feature/wave1-hardening`, E1.F12.T11 (842f8b8) anchors every behaviour promise of hooks/README.md to a guard-table case (`<!-- guard-case: ID -->`).

### Regression test
L-16 (every behaviour promise in rules/enforcement.md and hooks/README.md carries a guard-case anchor whose table case matches; E1.F10.T4, 91758e0): 18 errors on `main`, 0 on this branch; `plugins/karvey/tests/hooks/tables/session.json` cases `ss-13-empty-notifications-startup-one-line`, `ss-15-bare-openapi-under-karvey-parent-silent`, `ss-20-non-karvey-dir-silent` prove the behaviour the README now states. `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-12, D3 C-18 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | confirmed on the 3.11.2 working tree |
| 2026-09-23 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fixed in hotfix 3.11.2: hooks/README.md now states the Karvey-project exception; stays EN FIX until the wave1 plugin linter checks docs vs hook behaviour (no automated regression test yet) |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | L-16 red on main (18), green here; session.json 23/23; test_incidents.py 10/10 |

## BUG-17 — 3.11.1 release docs incomplete (CHANGELOG without "Why"; page history stops at 3.11.0)
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** CHANGELOG.md ([3.11.1]); docs/karvey.html (version history, 5 blocks)
- **Change / origin:** team-adapters (F-31; sources D6, C-21)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
At e3bc6f3: the [3.11.1] CHANGELOG entry has no "Why" section (policy `changelog-policy.md`); the page is stamped v3.11.1 but its history tops at 3.11.0 with `class="now"`.

### Actual vs expected
- Actual: incomplete release documentation for 3.11.1.
- Expected: every entry with its "Why"; the page history in step with the badge.

### Root cause
No automated check ties the CHANGELOG sections and the page history to the version bump.

### Fix
Docs fixed in hotfix 3.11.2 ("Why" added to [3.11.1]; page history in the 5 languages). The missing check is L-13 on `feature/wave1-hardening` (E1.F10.T3, 20d84b6).

### Regression test
L-13 (the top CHANGELOG release has a "Why" section and docs/karvey.html lists that version as current in every language block): 6 errors at e3bc6f3 (3.11.1, page marks 3.11.0 as current), 0 on this branch. `plugins/karvey/tests/regression/test_incidents.py` (E1.F14.T3) indexes it and fails if a named check disappears.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:28 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D3 C-21; D6 by the orchestrator |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | no release-doc check |
| 2026-09-23 19:01 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fixed in CHANGELOG.md and docs/karvey.html on hotfix/karvey-3.11.2-settings-nudge; awaiting a regression check |
| 2026-09-24 04:44 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | L-13 red at 3.11.1 e3bc6f3 (6), green here; test_incidents.py 10/10 |

## BUG-18 — SessionStart hook never ran: `${CLAUDE_PLUGIN_ROOT}` inside single quotes
- **Priority:** high
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/hooks.json
- **Change / origin:** team-layer (3.8.0, commit 76905fa) — reported by agente-kloketen (paautin-kloketen), relayed at the owner's request
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`CLAUDE_PLUGIN_ROOT=<plugin> bash -c "bash '\${CLAUDE_PLUGIN_ROOT}/hooks/karvey-session-context.sh'"` → `No such file or directory`, rc 127. Every session start showed `SessionStart:startup hook error`.

### Actual vs expected
- Actual: the command in hooks.json wrapped the placeholder in single quotes; bash does not expand it and Claude Code 2.1.281 does not substitute it in the text, so the script never ran — no handoff reinjection, no drift check, no settings notice, since 3.8.0.
- Expected: the hook runs on startup / resume / compact / clear.

### Root cause
Quoting: single quotes suppress expansion. The CLI's own guidance is to wrap the placeholder in double quotes. The 3.11.2 tests executed the script directly, never the `command` as declared, so they could not see it.

### Fix
`"command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/karvey-session-context.sh\""` (double quotes; paths with spaces stay one word).

### Regression test
`plugins/karvey/hooks/tests/test-hooks.sh`, section "hooks.json: the declared command runs as written" — extracts the command from hooks.json and runs it with `bash -c`, plus a path with spaces. Fails on 3.11.2, passes on 3.11.3.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 | DETECTADO | agente-kloketen / Claude | reported with repro; local patch applied on the owner's OK in the plugin cache only |
| 2026-09-23 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | reproduced: rc 127 with single quotes, rc 0 with double |
| 2026-09-23 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | hotfix/karvey-3.11.3-session-hook |
| 2026-09-23 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | 3.11.3 + regression test |

## BUG-19 — team.json inside the repo: the hook resolved a profile path that does not exist
- **Priority:** high
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-session-context.sh (profile resolution)
- **Change / origin:** team-layer (3.8.0) — reported by agente-kloketen (paautin-kloketen)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Repo with `docs/spec/team.json` = `{"ops_repo": "<this repo>", "roles": {"<this repo>": "ceo"}}` and the files `karvey-checkpoint save` writes: `docs/spec/agents/ceo/{handoff,manifest,manifest-compact,checklist}.md`, `state.json`, `docs/spec/board/ceo.md`.

### Actual vs expected
- Actual: `PROFILE=$ROOT/$OPS/agents/$ROLE` → `<repo>/<repo>/agents/ceo`, which does not exist; nothing reinjected and nothing said. The role came out `ceo` only by default (TOP empty at the root); `manifest-compact` was looked for in `$PROFILE/..`.
- Expected: the same layout the save writes; a clear message when the profile or handoff is missing.

### Root cause
The hook only knew the sibling-ops-repo layout; `karvey-checkpoint` and `rules/team.md` did not state the in-repo layout, so save and hook diverged.

### Fix
`OPSDIR` = `$ROOT/$OPS` when it is a sibling repo that exists, else the folder holding `team.json` (`docs/spec/`); role looked up by the root's own name when the session starts at the root; `manifest-compact` looked for inside the profile first; explicit messages for a missing profile or handoff. `karvey-checkpoint` and `rules/team.md` now document both layouts.

### Regression test
`plugins/karvey/hooks/tests/test-hooks.sh`, section "team.json inside the repo" (in-repo profile, reinjection, role at root, missing handoff said, sibling layout still works). Fails on 3.11.2, passes on 3.11.3. Verified read-only against the real paautin-kloketen layout.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 | DETECTADO | agente-kloketen / Claude | session started without identity; restore found no handoff |
| 2026-09-23 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | reproduced against paautin-kloketen (read-only) |
| 2026-09-23 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | hotfix/karvey-3.11.3-session-hook |
| 2026-09-23 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | 3.11.3 + regression test |

## BUG-20 — False "NOT FOUND" drift when state.json names the repo itself
- **Priority:** medium
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-session-context.sh (live state vs handoff)
- **Change / origin:** team-layer (3.8.0) — residue of BUG-19, reported by agente-kloketen after verifying 3.11.3
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
In-repo team layout; `state.json` `repos[].path = "<repo name>"` (as the save writes it) → the hook resolved `$ROOT/<repo name>`.

### Actual vs expected
- Actual: `<repo>: NOT FOUND at <repo>/<repo> — the handoff describes a tree that is not here` on every session start, a false "your handoff aged" alarm in the section that exists to detect real drift.
- Expected: the repo is found and branch / commit / uncommitted are compared.

### Root cause
same class as BUG-19: the state comparison only knew the sibling layout (`$ROOT/<path>`).

### Fix
a path equal to the root's own name, `.` or empty resolves to `$ROOT` (the joined path is still tried as a fallback).

### Regression test
`plugins/karvey/hooks/tests/test-hooks.sh`, section "state.json paths (BUG-20) and worktrees (BUG-21)" — fails on 3.11.3, passes on 3.11.4.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 | DETECTADO | agente-kloketen / Claude | measured on paautin-kloketen with 3.11.3 |
| 2026-09-23 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | reproduced in a fixture |
| 2026-09-23 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | hotfix/karvey-3.11.4-state-paths |
| 2026-09-23 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | 3.11.4 + regression test; verified read-only against paautin-kloketen |

## BUG-21 — Git worktrees reported as NOT FOUND in the live-state comparison
- **Priority:** medium
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-session-context.sh (live state vs handoff)
- **Change / origin:** team-layer (3.8.0) — finding F-01 of the wave1-hardening architecture
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A handoff whose `repos[].path` is a git worktree (it has a `.git` file, not a `.git/` directory).

### Actual vs expected
- Actual: `NOT FOUND` for every worktree, although the tree exists.
- Expected: the worktree is recognised as a repo.

### Root cause
the hook tested `os.path.isdir(<repo>/.git)`.

### Fix
ask git: `git -C <path> rev-parse --git-dir`.

### Regression test
`plugins/karvey/hooks/tests/test-hooks.sh`, section "state.json paths (BUG-20) and worktrees (BUG-21)" — fails on 3.11.3, passes on 3.11.4.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | architecture review of wave1-hardening (F-01) |
| 2026-09-23 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | reproduced in a fixture |
| 2026-09-23 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | hotfix/karvey-3.11.4-state-paths |
| 2026-09-23 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | 3.11.4 + regression test; verified read-only against paautin-kloketen |

## BUG-22 — Committing state.json after a save is reported as drift
- **Priority:** medium
- **Detected:** 2026-09-24 · **Component:** plugins/karvey/hooks/karvey-session-context.sh (live state vs handoff)
- **Change / origin:** wave1-hardening — finding F-40 (checkpoint dogfood); seen again on this session's start (`c793a5f -> 1dbd98e · uncommitted 1 -> 0`)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A profile inside the repo it measures (`docs/spec/agent/`). `karvey-checkpoint save`: commit the handoff, run `karvey-handoff-capture.py`, then commit `state.json`. Start a new session.

### Actual vs expected
- Actual: `karvey: DRIFT — commit X -> Y · uncommitted 1 -> 0`, and the session is told the handoff has aged.
- Expected: `matches (…; profile-only commits since the save)` when the only commits since the save touch the profile's own files.

### Root cause
The capture records HEAD and the uncommitted count before `state.json` is committed; the comparison checks commit and count for equality, so the commit that stores `state.json` itself always reads as drift.

### Fix
Architecture §1.4 revision 1 (D-19): a changed commit matches when the recorded commit is an ancestor of HEAD and every path in `git log <recorded>..HEAD` is a profile file; then a lower uncommitted count also matches. Task E1.F17.T1.

### Regression test
`plugins/karvey/hooks/tests/test-hooks.sh`, section "session-context: profile-only commits since the save (BUG-22)": four cases (state.json alone → matches; state.json plus another file → DRIFT; amended, non-descendant HEAD → DRIFT; higher uncommitted count → DRIFT), each run on the python path (`karvey_hooks.live_state` → `livestate.profile_only_since`) and on the degraded path's live-state block. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-24 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-40, first agente-karvey save (da3d70a → cb3946e) |
| 2026-09-24 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate (D-19): cause read in the hook's live-state block |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | E1.F17.T1 (D-21): profile-only commits since the save match on both the python and the degraded path; case 1 red before the fix, cases 2-4 guard against over-matching |

## BUG-84 — The sponsor page is not rebuilt at the second gate close
- **Priority:** high
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-sponsor.py (`build`)
- **Change / origin:** wave3-optimization — finding F-104 (test phase, the change's own sponsor page)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A change with a declared sponsor. Close one gate (`karvey-sponsor.py build {change} --gate what`), then close the next one (`--gate how`), directly or through `karvey-close.py`.

### Actual vs expected
- Actual: the second build stops with `CASConflict: changed by another writer, re-run: …/sponsor.html` (a traceback; through `karvey-close.py` the sponsor step is reported failed), the page keeps the first gate's content and no history line is added.
- Expected: the page is regenerated at every gate close (REQ-W3-022) and `sponsor-history.jsonl` gains one line per build.

### Root cause
`cmd_build` called `atomicio.write_text_atomic(path, page)` without `expected_sha256`; its default (`None`) means "the file must not exist yet", so only the first page could ever be written. The unit tests and the close tests each built one page on a fresh fixture.

### Fix
`cmd_build` reads the page's hash before building the model and passes it as `expected_sha256`: a later gate rewrites the page, while a page changed by another writer in between is still refused (exit 3, `sponsor page: not written — …`), never overwritten and never a traceback.

### Regression test
`plugins/karvey/tests/unit/test_sponsor.py`, `Cli.test_BUG_84_the_page_is_rebuilt_at_a_later_gate` and `Cli.test_BUG_84_a_page_changed_by_another_writer_is_refused_not_overwritten` — both fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | wave3-optimization test phase: rebuilding this change's own sponsor page (evidence.jsonl:32, exit 1) |
| 2026-09-27 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | `write_text_atomic` called without the hash it read |
| 2026-09-27 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix + two regression tests, red before and green after |

## BUG-86 — On a phone the overdue tag squeezes the question text of the sponsor page
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/templates/sponsor.html (`.ask`)
- **Change / origin:** wave3-optimization — finding F-95 (design judge, design_graphic dogfooding)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Render a sponsor page with a question overdue since a date and open it 360 px wide (or the mockup's Phone 360 preview).

### Actual vs expected
- Actual: the tag (`white-space:nowrap`) keeps its full width and the question block shrinks to its longest word; in the mockup preview the progress steps also kept 4 columns because `body.phone` narrowed only the page.
- Expected: the question takes its own line under the tag when both do not fit, and the steps drop to 2 columns under 520 px (design-spec §Layout).

### Root cause
The `.ask` flex row wrapped, but its text block had no flex basis, so it shrank instead of wrapping; the mockup preview simulated the phone by width only, which does not trigger the 520 px media query.

### Fix
`.ask>div{flex:1 1 16rem;min-width:0}` in the template (and the mockup); the mockup's phone preview also sets the steps to 2 columns.

### Regression test
`plugins/karvey/tests/page/test_sponsor_page.mjs`, test `BUG-86: at 360 px the question text wraps under a wide tag instead of being squeezed` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-95: design judge, design_graphic dogfooding |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | text block of `.ask` had no flex basis |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-87 — Sponsor page progress steps show done by colour only
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/sponsor.py (`render`, progress)
- **Change / origin:** wave3-optimization — finding F-98 (design judge, design_graphic dogfooding)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Build a sponsor page for a change past its first gates and read the Progress steps without colour (screen reader, greyscale print).

### Actual vs expected
- Actual: a done step shows only its date; only the border colour says it is done. The current step says "since {date}" with no state word.
- Expected: every state is a word (design-spec: no colour-only meaning, WCAG 1.4.1): "done {date}", "in progress since {date}", "planned".

### Root cause
The step caption was built from the date alone for every state but the current one; the state lived in the CSS class.

### Fix
`render` writes the state word from the wording table (`step_done`, `in_progress`, English and Spanish) before the date.

### Regression test
`plugins/karvey/tests/unit/test_sponsor.py`, `Page.test_BUG_87_every_step_state_is_a_word_not_only_a_colour` and `Page.test_BUG_87_spanish_step_words` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-98: design judge, design_graphic dogfooding |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | step caption built from the date only |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-88 — Touch targets under 44 px on the phone surfaces
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/templates/sponsor.html (`summary`), docs/karvey.html (`.lang-select`)
- **Change / origin:** wave3-optimization — finding F-100 (design judge, design_graphic dogfooding)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Open the sponsor page or the method page 360 px wide and measure the expanders and the language select.

### Actual vs expected
- Actual: `min-height:32px` on the sponsor page's summaries and on the method page's phone language select.
- Expected: at least 44 px (`--size-touch`) on the surfaces a sponsor reads on a phone.

### Root cause
The 32 px control height of the desktop mockup was reused on the phone surfaces.

### Fix
`--size-touch:44px` token; the sponsor page's `summary` and the method page's `.lang-select` use it (44 px).

### Regression test
`plugins/karvey/tests/page/test_sponsor_page.mjs`, test `BUG-88: summaries meet the 44 px touch target`, and `plugins/karvey/tests/page/test_page.mjs`, test `BUG-88: the phone language select meets the 44 px touch target` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-100: design judge, design_graphic dogfooding |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | desktop control height reused on phone |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-89 — The sponsor page prints light-grey text on white in the dark scheme
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/templates/sponsor.html (`@media print`, dark scheme)
- **Change / origin:** wave3-optimization — finding F-92 (design judge, design_graphic dogfooding; found while declaring the print pair)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Set the system to dark and print the sponsor page.

### Actual vs expected
- Actual: the print style whitens the page but the dark-scheme tokens still apply, so secondary text (#a8b1ba) and links print at about 2:1 on white; the print colours were literals, outside the design delta.
- Expected: print always uses the light scheme and the print tokens (`--color-print-paper`, `--color-print-ink`, 21:1).

### Root cause
The dark scheme was `@media (prefers-color-scheme: dark)`, which also matches print; the print style only reset the body colours.

### Fix
The dark scheme is `@media screen and (prefers-color-scheme: dark)`; the print style uses `var(--color-print-paper)` and `var(--color-print-ink)`.

### Regression test
`plugins/karvey/tests/page/test_sponsor_page.mjs`, test `BUG-89: print keeps the light scheme and uses the print tokens, no literal colour` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-92: design judge, design_graphic dogfooding; found while declaring the print pair |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | dark-scheme media query also matched print |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-90 — Sponsor page landmarks carry the wrong accessible names
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/sponsor.py (`render`, slots)
- **Change / origin:** wave3-optimization — finding F-105 (QA dimension 8, static audit of the implemented page)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Build a sponsor page and list its landmarks with a screen reader.

### Actual vs expected
- Actual: the section navigation is announced as "Progress" and the four-fact summary as "Step".
- Expected: "Sections" and "Summary" (English and Spanish wording).

### Root cause
The two slots reused the labels of other elements (`progress`, `step`).

### Fix
New wording labels `sections` and `summary`; the slots use them.

### Regression test
`plugins/karvey/tests/unit/test_sponsor.py`, `Page.test_BUG_90_landmarks_are_named_for_what_they_hold` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-105: QA dimension 8, static audit of the implemented page |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | slots reused other labels |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-91 — Accepted and carried risks shown with the success fill
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/sponsor.py (`render`, risks)
- **Change / origin:** wave3-optimization — finding F-106 (QA dimension 8, static audit vs design-spec (Risk state tag))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A risk register with a row in state `accepted` or `moved`; build the sponsor page.

### Actual vs expected
- Actual: every state but `open` gets the success-soft tag, so "accepted as is" looks like "no longer a risk".
- Expected: design-spec: accent-soft for being watched, success-soft for reduced or gone, a plain surface-2 tag for accepted as is and carried to later work.

### Root cause
A two-way `open` / other test instead of a per-state map.

### Fix
`RISK_TAG` maps each of the five states to its fill.

### Regression test
`plugins/karvey/tests/unit/test_sponsor.py`, `Page.test_BUG_91_risk_state_tag_fill_follows_the_design_spec` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-106: QA dimension 8, static audit vs design-spec (Risk state tag) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | two-way test instead of a per-state map |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-92 — A long change goal is cut mid-word in the sponsor page title
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/sponsor.py (`_title`)
- **Change / origin:** wave3-optimization — finding F-107 (QA dimension 8, this change's own sponsor page)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A change whose goal's first sentence is longer than 120 characters; build the sponsor page.

### Actual vs expected
- Actual: the heading ends in the middle of a word ("… produced fro") with no mark that it was shortened.
- Expected: cut at a word boundary with an ellipsis, at most 120 characters.

### Root cause
A plain slice `[:120]`.

### Fix
`_title` cuts at the last space before the limit and adds "…" (`TITLE_MAX`).

### Regression test
`plugins/karvey/tests/unit/test_sponsor.py`, `Page.test_BUG_92_a_long_goal_is_cut_at_a_word_with_an_ellipsis` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-107: QA dimension 8, this change's own sponsor page |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | plain slice |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-93 — The portfolio view does not say it is read-only and offline
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-context.py (`render_portfolio`)
- **Change / origin:** wave3-optimization — finding F-108 (QA dimension 8, static audit vs design-spec (F-37))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`karvey-context.py --portfolio --file {portfolio.json}`.

### Actual vs expected
- Actual: the view ends after the last client's totals.
- Expected: design-spec F-37: a footer states that nothing was written and no network request was made.

### Root cause
The footer of the mockup was not carried into the renderer.

### Fix
`render_portfolio` ends with `PORTFOLIO_FOOTER`.

### Regression test
`plugins/karvey/tests/unit/test_portfolio.py`, `View.test_BUG_93_the_text_view_ends_with_the_read_only_footer` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-108: QA dimension 8, static audit vs design-spec (F-37) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | mockup footer not implemented |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-94 — The security scan records absolute local paths in committed evidence
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-security-scan.py (`run_tool`)
- **Change / origin:** wave3-optimization — finding F-110 (QA dimension 1, running the tool catalogue on this change)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`karvey-security-scan.py run {change}` and read the new `evidence.jsonl` lines.

### Actual vs expected
- Actual: the recorded argv holds the absolute repository path and report path (the local home directory), and the reports repeat it for every file; the evidence file is committed, so a public repository publishes the path.
- Expected: paths relative to the repository, which is the tool's working directory.

### Root cause
`build_argv` was filled with the absolute repository and report paths although the tool already runs with `cwd` = the repository.

### Fix
`{repo}` is `.` and `{out}` the report path relative to the repository.

### Regression test
`plugins/karvey/tests/unit/test_security_scan.py`, `Run.test_BUG_94_the_recorded_command_carries_no_absolute_path` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-110: QA dimension 1, running the tool catalogue on this change |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | absolute placeholders although cwd is the repository |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-95 — The gate summary's judge line omits the discarded count and the tokens
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-context.py (`judge_lines`)
- **Change / origin:** wave3-optimization — finding F-112 (manual script design-judge-gate, step 2)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A design judge run recorded with `discarded` and `tokens_total`/`source`; `karvey-context.py --section gate --change {id} --gate what`.

### Actual vs expected
- Actual: `judge design: concerns · High 1, Medium 1, Low 1 · model … (intra-model)` — no discarded count, no tokens.
- Expected: verdict, kept and discarded counts, model and tokens with their source (the script's Expected line, REQ-W3-039).

### Root cause
The line formatter printed only verdict, severity counts and model.

### Fix
The line adds `{n} discarded` and `{tokens} tokens ({source})` (`tokens n/a` when the record has none).

### Regression test
`plugins/karvey/tests/unit/test_context_gate.py`, `GateSummary.test_BUG_95_judge_line_has_discarded_and_tokens_with_their_source` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-112: manual script design-judge-gate, step 2 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | formatter omitted two fields |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-96 — The gate close drops the leak check's field and rule
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-close.py (`step_sponsor`)
- **Change / origin:** wave3-optimization — finding F-111 (manual script sponsor-at-gate, step 3)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A risk text quoting a made-up connection string; `karvey-close.py {change} architecture --outcome changes_requested --json`.

### Actual vs expected
- Actual: the sponsor step says only `leak check: FAIL — page not written, not delivered`; the agent, lacking the field and rule, re-read the risk and quoted the value itself.
- Expected: the close names each field and rule, never the value (REQ-W3-023).

### Root cause
On a non-zero build exit the step kept only the first error message and dropped `result.hits`.

### Fix
On a refusal the step carries `refused: [{field, rule}]` and one line per hit, plus "the last written page is unchanged".

### Regression test
`plugins/karvey/tests/unit/test_close.py`, `Close.test_BUG_96_a_leak_refusal_names_each_field_and_rule_never_the_value` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-111: manual script sponsor-at-gate, step 3 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | only the first error message kept |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-97 — `karvey-trace.py --wbs` misses root-level QA and deploy sections
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-trace.py (`wbs_plan`)
- **Change / origin:** wave3-optimization — finding F-114 (manual script tracker-wbs, every step)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A `PLAN.md` with `## QA Review — E1.QA …` and `## Deploy — … (E1.DEPLOY …)` sections holding table rows; `karvey-trace.py {change} --wbs`.

### Actual vs expected
- Actual: `0 issue(s)`: only checkbox items were inspected, and a second section with the same key passed.
- Expected: each such section and row reported `outside the hierarchy`; an Epic item key twice reported `duplicate` (REQ-W3-041).

### Root cause
The reconciliation looked only at `- [ ]` items and ignored headings and table rows.

### Fix
Headings naming QA Review / Deploy / `E{n}.QA|DEPLOY` outside the Epic items, and `E{n}.QA.{k}` / `[Deploy]` table rows outside them, are `outside the hierarchy`; a repeated Epic item key is `duplicate`.

### Regression test
`plugins/karvey/tests/unit/test_wbs.py`, `Legacy.test_BUG_97_root_qa_and_deploy_sections_with_table_rows_are_outside` and `Legacy.test_BUG_97_an_epic_item_twice_is_a_duplicate_and_children_inside_are_fine` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-114: manual script tracker-wbs, every step |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | headings and table rows not inspected |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-98 — QA and deploy write root-level sections on the Markdown tracker
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/skills/karvey-qa/SKILL.md (Step 3B), karvey-deploy/SKILL.md (Step 4), rules/adapters/markdown.md
- **Change / origin:** wave3-optimization — finding F-113 (manual script tracker-wbs, steps 2 and 4)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A change on the Markdown tracker: "Run QA on {change}", then "Prepare the deploy of {change}".

### Actual vs expected
- Actual: QA added a root-level `## QA Review` section with table rows and deploy a root-level `## Deploy` table; the `### Epic item E1.QA` / `E1.DEPLOY` sections stayed empty and no `[Deploy] {change}@{version}` item was written.
- Expected: the fix tasks as children of `### Epic item E{n}.QA` and `[Deploy] {change}@{version}` under `### Epic item E{n}.DEPLOY` (REQ-W3-041, REQ-W3-042).

### Root cause
The QA skill's Step 3B still said "Add a QA Review section at the end of PLAN.md" and the deploy skill showed a root-level `## Deploy` table; the Markdown adapter did not state the shape.

### Fix
QA Step 3B, deploy Step 4 and the Markdown adapter name the Epic-item shape (checkbox children, never a root section or table).

### Regression test
`plugins/karvey/tests/unit/test_wbs.py`, `SkillText.test_BUG_98_qa_deploy_and_the_markdown_adapter_name_the_epic_item_shape` (and BUG-97 detects the old shape) — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-113: manual script tracker-wbs, steps 2 and 4 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | skill text still prescribed the 4.0 shape |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-99 — With browse.via agent the session fetched an undeclared URL itself
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/skills/karvey-browse/SKILL.md (Where it runs)
- **Change / origin:** wave3-optimization — finding F-115 (manual script browse-via-agent, step 2 (reproduced on a retry))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`browse.via: agent:{name}`; "Also check the page in notes.md" where the page is an undeclared internal URL.

### Actual vs expected
- Actual: the agent ran `curl` on the undeclared URL, then declined to send it to the browser agent.
- Expected: the undeclared URL is declined and never tried; this session makes no request of its own (REQ-W3-054).

### Root cause
The skill limited what may be sent to the named agent but did not forbid the session's own request.

### Fix
The `agent:` paragraph says the session opens no URL itself (no fetch, no curl) and an undeclared URL is declined, never tried; `none` says do not browse or fetch.

### Regression test
`plugins/karvey/tests/unit/test_browse_via.py`, `SkillText.test_BUG_99_the_session_opens_no_url_itself` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-115: manual script browse-via-agent, step 2 (reproduced on a retry) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | skill silent on the session's own requests |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-100 — Changes requested after an approval leave the phase approved
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-state.py (`cmd_outcome`)
- **Change / origin:** wave3-optimization — finding F-116 (manual scripts one-phase-per-session step 2 and sponsor-at-gate step 3)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`approve {change} architecture …`, then `outcome {change} architecture changes_requested …`; `next {change}`.

### Actual vs expected
- Actual: the outcome is appended, `approvals.architecture.approved` stays true and `next` says `ready`.
- Expected: the phase is not both approved and sent back: the outcome is refused on an approved phase with the way out (`reopen`, which moves the approval to revision_history).

### Root cause
`outcome` appended to `gate_outcomes` without looking at the phase's approval.

### Fix
`outcome … changes_requested` (kind gate) on an approved phase exits 3 naming `karvey-state.py reopen`; nothing is written.

### Regression test
`plugins/karvey/tests/unit/test_state_outcomes.py`, `Outcomes.test_BUG_100_changes_requested_on_an_approved_phase_is_refused_with_the_way_out` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-116: manual scripts one-phase-per-session step 2 and sponsor-at-gate step 3 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | outcome ignored the existing approval |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-101 — `observed` is blind to Skill loads and shell reads
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-context-budget.py (`opened_files`)
- **Change / origin:** wave3-optimization — finding F-117 (manual script one-phase-per-session, step 4)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A session that loads a phase skill through the Skill tool and reads rules with `sed`/`grep`; `karvey-context-budget.py observed --transcript {t} --skill {s}`.

### Actual vs expected
- Actual: `opened: no plugin text`, so a rule opened outside the load list is never flagged.
- Expected: `opened` lists the skill and every plugin markdown file the session read (REQ-W3-013 / C-08).

### Root cause
Only `Read` tool calls were counted.

### Fix
`Skill` calls count as `skills/{name}/SKILL.md`; `Bash` commands with a read verb (cat, sed, head, grep…) count the plugin `skills/**.md` paths they name, with the variables they assign expanded; globs name no file.

### Regression test
`plugins/karvey/tests/unit/test_close.py`, `Observed.test_BUG_101_skill_loads_and_shell_reads_count_as_opened` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-117: manual script one-phase-per-session, step 4 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | only Read tool calls counted |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-102 — The sponsor fixture fails validation with an "expected = got" message
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-state.py (skip validation); tests/unit/fixtures/sponsor
- **Change / origin:** wave3-optimization — finding F-118 (manual scripts sponsor-at-gate and one-phase-per-session (setup))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`karvey-state.py validate tests/unit/fixtures/sponsor/docs/spec/changes/sample-change/spec.json`.

### Actual vs expected
- Actual: INVALID: `skipped.infra = "lane:feature-ui"` is refused with `expected lane:feature-ui, got lane:feature-ui`.
- Expected: the fixture validates; a lane reason for a phase the lane makes optional says so and asks for a plain reason.

### Root cause
The fixture used a lane reason for an optional phase, and the message shared one branch with the wrong-lane case.

### Fix
Own branch and message ("lane … does not skip phase …: it is optional there — record a plain reason"); the fixture records `no cloud resources`.

### Regression test
`plugins/karvey/tests/unit/test_schema_w2.py`, `SkippedLane.test_BUG_102_a_lane_reason_for_a_phase_the_lane_makes_optional_says_so`, and `plugins/karvey/tests/unit/test_sponsor.py`, `FixtureValid.test_BUG_102_the_sponsor_fixture_validates_without_errors` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-118: manual scripts sponsor-at-gate and one-phase-per-session (setup) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | optional phase given a lane reason; shared message branch |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-103 — The gate close is skipped after an approval
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/skills/karvey-{requirements,mockup,design-graphic,architecture,infra,tasks,qa}/SKILL.md (Advance to the next phase)
- **Change / origin:** wave3-optimization — finding F-121 (manual script one-phase-per-session, step 1 (2 of 3 fresh attempts))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A fresh session: "Close the how gate of {change}: I approve the architecture."

### Actual vs expected
- Actual: the agent records the approval and stops; `karvey-close.py` never runs, so no sponsor page, no effort entry and no checkpoint offer.
- Expected: the close steps run once after every gate answer (REQ-W3-013, REQ-W3-014, REQ-W3-022).

### Root cause
The phase skills' Advance paragraph named approve/outcome but not the close script; only rules/gates.md and _core.md did, which a phase skill cites without opening.

### Fix
Each gated phase skill's Advance paragraph says "then run the close steps once — `karvey-close.py \"{change-id}\" {phase} --outcome …` (never skipped)".

### Regression test
`plugins/karvey/tests/unit/test_close.py`, `AdvanceText.test_BUG_103_every_gated_phase_skill_names_karvey_close` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-121: manual script one-phase-per-session, step 1 (2 of 3 fresh attempts) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | close step absent from the phase skills' Advance paragraph |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-104 — `observed` reads a shell brace list as one file
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-context-budget.py (`_bash_paths`)
- **Change / origin:** wave3-optimization — finding F-122 (manual script one-phase-per-session, step 4 (rerun))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A transcript with `wc -l $R/{_core,gates}.md` (R = the rules folder); `karvey-context-budget.py observed --transcript {t} --skill karvey-tasks`.

### Actual vs expected
- Actual: the literal `rules/{_core,gates}.md` is listed as opened and flagged outside the load list.
- Expected: each file of the brace list is listed; nothing outside the load list.

### Root cause
The path pattern accepted braces and no expansion was done.

### Fix
A `{a,b}` list is expanded into one path per name; a token still holding a brace names no file.

### Regression test
`plugins/karvey/tests/unit/test_close.py`, `Observed.test_BUG_101_skill_loads_and_shell_reads_count_as_opened` (brace-list case, BUG-104) — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-122: manual script one-phase-per-session, step 4 (rerun) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | no brace expansion |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-105 — Writing tools on a spec/ project create a second spec root
- **Priority:** high
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/project.py (`find_root`, `is_karvey_project`) and every writing script
- **Change / origin:** wave3-optimization — finding F-123 (QA dimension 4 (impact on existing modules))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A repository with only `spec/project.json` and `spec/changes/foo/`; `karvey-state.py active`, `next foo`, `init bar`.

### Actual vs expected
- Actual: `active` names foo, `next foo` exits 4 (the writers look under docs/spec/), and `init bar` creates `docs/spec/changes/bar`, a second spec root beside `spec/`.
- Expected: REQ-W3-048: the session hook, the dashboard and the portfolio read either layout; nothing writes a second root.

### Root cause
Root discovery accepted `spec/` for every caller while about forty writing call sites still build `docs/spec/` paths.

### Fix
`find_root` / `is_karvey_project` accept `spec/` only with `read_only=True` (dashboard, session hook, portfolio); the state tool refuses a `spec/` project with "move spec/ to docs/spec/" and writes nothing.

### Regression test
`plugins/karvey/tests/unit/test_context.py`, `SpecLayoutIsReadOnly.test_BUG_105_writers_refuse_the_spec_layout_and_create_no_second_root` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-123: QA dimension 4 (impact on existing modules) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | spec/ accepted by writers that only know docs/spec/ |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-126 — `observed` flags the tracker adapter in use as outside the load list
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-context-budget.py (`cmd_observed`)
- **Change / origin:** wave3-optimization — finding F-124 (manual script one-phase-per-session, step 4 (second rerun))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A session on the Markdown tracker runs `/karvey-tasks` and reads `rules/adapters/markdown.md`; `observed --skill karvey-tasks`.

### Actual vs expected
- Actual: `outside the load list: skills/karvey/rules/adapters/markdown.md`, although the skill's `Load:` names `adapters/{tool}.md`.
- Expected: any alternative of a `{tool}` entry is inside the load list.

### Root cause
The allowed set came from the size closure, which keeps only the largest alternative of each entry.

### Fix
`_allowed_files` walks the load list with every alternative of each entry.

### Regression test
`plugins/karvey/tests/unit/test_close.py`, `ObservedAlternatives.test_BUG_126_any_tracker_adapter_of_the_load_list_is_inside_it` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-124: manual script one-phase-per-session, step 4 (second rerun) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | allowed set kept one alternative |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-106 — Sponsor delivery sends a page other than the one the leak check passed
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-sponsor.py (`cmd_deliver`)
- **Change / origin:** wave3-optimization — finding F-125 (QA dimension 1, finding 1)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: deliver attached `sponsor.html` from disk while the leak check ran on a freshly rendered page, so a page edited after the build left unchecked.

### Actual vs expected
- Actual: deliver attached `sponsor.html` from disk while the leak check ran on a freshly rendered page, so a page edited after the build left unchecked.
- Expected: the bytes sent are the bytes checked and recorded in `sponsor-history.jsonl`.

### Root cause
two sources for one payload.

### Fix
exit 3 when the page is missing, unbuilt or its sha256 differs from the last history entry; the on-disk text is leak-checked before sending.

### Regression test
`plugins/karvey/tests/unit/test_sponsor.py`, `Security.test_BUG_106_deliver_refuses_a_page_changed_after_the_checked_build` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-125: QA dimension 1, finding 1 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | two sources for one payload |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-107 — Stakeholder destination not checked where it is used
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-sponsor.py (`safe_destination`), karvey-config.py (`resolve_event`)
- **Change / origin:** wave3-optimization — finding F-126 (QA dimension 1, finding 2)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: a `spec.json` stakeholder override such as `x@evil.test.

### Actual vs expected
- Actual: a `spec.json` stakeholder override such as `x@evil.test; rm -rf ~` was printed as the destination with exit 0.
- Expected: every destination passes `check_target` at the point of use.

### Root cause
validation only when project.json was written.

### Fix
`check_target` at use: deliver exits 3 without the value; the event resolves to `none`.

### Regression test
`plugins/karvey/tests/unit/test_notify_events.py`, `Events.test_BUG_107_an_unsafe_stakeholder_destination_is_refused_at_use`, `plugins/karvey/tests/unit/test_sponsor.py`, `Security.test_BUG_107_a_change_override_with_an_unsafe_destination_is_refused_at_use` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-126: QA dimension 1, finding 2 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | validation only when project.json was written |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-108 — Portfolio follows symlinks out of a listed repository
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/portfolio.py
- **Change / origin:** wave3-optimization — finding F-127 (QA dimension 1, finding 3)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: only the repository root was resolved, so a symlinked change or `questions.md` read another client's data under `--client`.

### Actual vs expected
- Actual: only the repository root was resolved, so a symlinked change or `questions.md` read another client's data under `--client`.
- Expected: every file read stays inside the repository and is a regular file.

### Root cause
containment checked for the root only.

### Fix
`read_text`/`read_json` take `within=`; symlinked change folders are skipped.

### Regression test
`plugins/karvey/tests/unit/test_portfolio.py`, `Containment.test_BUG_108_symlinks_out_of_the_repository_are_not_read` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-127: QA dimension 1, finding 3 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | containment checked for the root only |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-109 — Hex secrets pass the leak check
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/leakcheck.py, leak_patterns.json
- **Change / origin:** wave3-optimization — finding F-128 (QA dimension 1, finding 4)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: a 40-character hex token never reaches the 4.2 bits/char entropy threshold.

### Actual vs expected
- Actual: a 40-character hex token never reaches the 4.2 bits/char entropy threshold.
- Expected: hex secrets are caught; short commit ids are not.

### Root cause
one entropy threshold for every alphabet.

### Fix
a hex rule for 32+ characters at 3.0 bits/char.

### Regression test
`plugins/karvey/tests/unit/test_leakcheck.py`, `QaDimension1.test_BUG_109_a_hex_secret_is_caught_and_short_commit_ids_are_not` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-128: QA dimension 1, finding 4 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | one entropy threshold for every alphabet |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-110 — Unreadable declared portfolio disables the other-clients rule
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-sponsor.py (`other_clients`, `checked`)
- **Change / origin:** wave3-optimization — finding F-129 (QA dimension 1, finding 5)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: the page was written with other clients' names unchecked.

### Actual vs expected
- Actual: the page was written with other clients' names unchecked.
- Expected: fail closed: page not written, reason stated.

### Root cause
read errors returned an empty client list.

### Fix
`PortfolioUnreadable` refuses with the hit `portfolio.file` / `client-unchecked`.

### Regression test
`plugins/karvey/tests/unit/test_sponsor.py`, `Security.test_BUG_110_an_unreadable_declared_portfolio_fails_closed` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-129: QA dimension 1, finding 5 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | read errors returned an empty client list |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-111 — Braces in free text crash the sponsor render
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/sponsor.py (`_e`)
- **Change / origin:** wave3-optimization — finding F-130 (QA dimension 1, finding 8)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: `{{word}}` in a question or risk text raised ValueError (no page) or could fill a slot.

### Actual vs expected
- Actual: `{{word}}` in a question or risk text raised ValueError (no page) or could fill a slot.
- Expected: free text renders as text.

### Root cause
slot filling ran after escaping without escaping braces.

### Fix
braces are escaped as HTML entities.

### Regression test
`plugins/karvey/tests/unit/test_sponsor.py`, `Security.test_BUG_111_braces_in_free_text_neither_crash_nor_fill_a_slot` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-130: QA dimension 1, finding 8 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | slot filling ran after escaping without escaping braces |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-112 — Leak check misses some paths and exempts formatted ids
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/leakcheck.py, leak_patterns.json
- **Change / origin:** wave3-optimization — finding F-131 (QA dimension 1, findings 6 and 7)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: `C:/Users/…`, `file:///home/…` and home paths inside URLs passed.

### Actual vs expected
- Actual: `C:/Users/…`, `file:///home/…` and home paths inside URLs passed; any 8-digit number was exempt as a date and dotted ids passed as amounts.
- Expected: those paths refused; only plausible YYYYMMDD dates and real amounts exempt.

### Root cause
patterns written for back-slash drives and bare paths.

### Fix
new path rules; date and amount exemptions narrowed.

### Regression test
`plugins/karvey/tests/unit/test_leakcheck.py`, `QaDimension1.test_BUG_112_paths_in_urls_and_forward_slash_drives_are_caught`, `plugins/karvey/tests/unit/test_leakcheck.py`, `QaDimension1.test_BUG_112_only_a_plausible_date_exempts_eight_digits_and_dotted_ids_are_pii` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-131: QA dimension 1, findings 6 and 7 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | patterns written for back-slash drives and bare paths |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-113 — Event change id and foreign text not constrained
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-config.py (`resolve_event`), karvey_lib/portfolio.py (`sanitise`)
- **Change / origin:** wave3-optimization — finding F-132 (QA dimension 1, finding 9 (and dimension 3, finding 13))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: `resolve_event --change ../..` accepted.

### Actual vs expected
- Actual: `resolve_event --change ../..` accepted; bidi and zero-width characters kept in foreign text; "at the the gate" with no item.
- Expected: a plain change id; invisible controls stripped; natural wording.

### Root cause
no id check; incomplete sanitiser; one message template.

### Fix
exit 2 on a non-id; `sanitise` strips bidi/zero-width; `EVENT_NO_ITEM` default word.

### Regression test
`plugins/karvey/tests/unit/test_portfolio.py`, `Containment.test_BUG_113_sanitise_strips_bidi_and_zero_width`, `plugins/karvey/tests/unit/test_notify_events.py`, `Events.test_BUG_113_change_must_be_an_id_and_no_item_reads_naturally` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-132: QA dimension 1, finding 9 (and dimension 3, finding 13) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | no id check; incomplete sanitiser; one message template |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-114 — Moving a risk half-applies when the backlog exists
- **Priority:** high
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-state.py (`_backlog_row`, `cmd_risk`)
- **Change / origin:** wave3-optimization — finding F-133 (QA dimension 2, finding 2)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: `risk … move` wrote spec.json:risk_log and risks.md, then always failed the backlog write (compare-and-swap expecting no file).

### Actual vs expected
- Actual: `risk … move` wrote spec.json:risk_log and risks.md, then always failed the backlog write (compare-and-swap expecting no file); a rerun duplicated risk_log.
- Expected: all three files written once, or none.

### Root cause
no read-time hash for the backlog and spec.json written first.

### Fix
hash at read; register, backlog, then spec.json last; a failure restores the earlier files and exits 3.

### Regression test
`plugins/karvey/tests/unit/test_risks.py`, `Command.test_BUG_114_move_with_an_existing_backlog_writes_everything_once`, `plugins/karvey/tests/unit/test_risks.py`, `Command.test_BUG_114_a_failed_spec_write_puts_register_and_backlog_back` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-133: QA dimension 2, finding 2 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | no read-time hash for the backlog and spec.json written first |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-115 — A row-less table hides the risk register, questions or backlog
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/risks.py, questions.py, backlog.py (`parse`)
- **Change / origin:** wave3-optimization — finding F-134 (QA dimension 2, finding 3)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: a previous table's header was kept, so the register read empty and `advance archived` passed with open risks.

### Actual vs expected
- Actual: a previous table's header was kept, so the register read empty and `advance archived` passed with open risks.
- Expected: the archive sees every open risk.

### Root cause
the header was reset only after a data row.

### Fix
any non-table line ends the table.

### Regression test
`plugins/karvey/tests/unit/test_risks.py`, `Archive.test_BUG_115_a_row_less_table_before_the_register_does_not_hide_an_open_risk`, `plugins/karvey/tests/unit/test_backlog_wsjf.py`, `StaleHeader.test_BUG_115_a_row_less_table_before_does_not_hide_the_backlog`, `plugins/karvey/tests/unit/test_questions.py`, `Parse.test_BUG_115_a_row_less_table_before_does_not_hide_the_questions` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-134: QA dimension 2, finding 3 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | the header was reset only after a data row |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-116 — The qa notification is re-sent: two sources for its state
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-close.py, skills/karvey-qa/SKILL.md, rules/gates.md
- **Change / origin:** wave3-optimization — finding F-135 (QA dimension 3, finding 4)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: the close keyed the sent-log on the outcome, the skill on the verdict, so the same verdict was sent twice.

### Actual vs expected
- Actual: the close keyed the sent-log on the outcome, the skill on the verdict, so the same verdict was sent twice.
- Expected: one key: the verdict.

### Root cause
two call paths with different state fields.

### Fix
the close uses `--verdict` only; the skill defers to the close; gates.md shows `--verdict`.

### Regression test
`plugins/karvey/tests/unit/test_close.py`, `Close.test_BUG_116_the_qa_notification_state_is_the_verdict_only` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-135: QA dimension 3, finding 4 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | two call paths with different state fields |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-117 — Four new validate warnings ignore their check modes
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-state.py (validate)
- **Change / origin:** wave3-optimization — finding F-136 (QA dimension 4, finding 5)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: effort.mixed, cost.cap_key, client.mismatch and risks.owner always warned.

### Actual vs expected
- Actual: effort.mixed, cost.cap_key, client.mismatch and risks.owner always warned.
- Expected: each follows its registry mode (off, advisory/warn, blocking).

### Root cause
fixed-severity issues.

### Fix
resolved through `modes.resolve` like design.undeclared.

### Regression test
`plugins/karvey/tests/unit/test_stakeholders.py`, `Client.test_BUG_117_the_mismatch_warning_follows_its_check_mode` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-136: QA dimension 4, finding 5 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | fixed-severity issues |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-118 — Applying a design delta can traceback or half-write
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-design.py (`cmd_apply`)
- **Change / origin:** wave3-optimization — finding F-137 (QA dimension 2, finding 6)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: hash taken at write time.

### Actual vs expected
- Actual: hash taken at write time; an empty design-system.md raised CASConflict (traceback, exit 1); a conflict still wrote the additions.
- Expected: hash at read; exit 3 and nothing written on a conflict.

### Root cause
hash read late, `is None` confusion, exceptions uncaught.

### Fix
hash at read, empty file handled, CAS/LockBusy → exit 3, nothing written.

### Regression test
`plugins/karvey/tests/unit/test_design_delta.py`, `Apply.test_BUG_118_an_empty_design_system_file_is_applied_not_a_traceback`, `plugins/karvey/tests/unit/test_design_delta.py`, `Apply.test_BUG_118_a_conflict_stops_and_writes_nothing_not_even_the_additions` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-137: QA dimension 2, finding 6 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | hash read late, `is None` confusion, exceptions uncaught |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-119 — New scripts end in a traceback on an unexpected error
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-design.py, karvey-close.py (`main`)
- **Change / origin:** wave3-optimization — finding F-138 (QA dimension 2, finding 7)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: exit 1 with a Python traceback.

### Actual vs expected
- Actual: exit 1 with a Python traceback.
- Expected: the JSON envelope with exit 5.

### Root cause
no catch-all.

### Fix
catch-all to the envelope, exit 5 (karvey-sponsor.py already reports through its own handlers).

### Regression test
`plugins/karvey/tests/unit/test_design_delta.py`, `Apply.test_BUG_119_an_internal_error_is_an_envelope_exit_5`, `plugins/karvey/tests/unit/test_close.py`, `Close.test_BUG_119_an_internal_error_is_an_envelope_exit_5` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-138: QA dimension 2, finding 7 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | no catch-all |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-120 — A malformed deploys entry crashes the report
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-context.py (`report_view`)
- **Change / origin:** wave3-optimization — finding F-139 (QA dimension 2, finding 8)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: a non-object `deploys` entry → exit 5.

### Actual vs expected
- Actual: a non-object `deploys` entry → exit 5.
- Expected: skipped.

### Root cause
no type check.

### Fix
non-dict entries skipped.

### Regression test
`plugins/karvey/tests/unit/test_context_report.py`, `Report.test_BUG_120_a_non_object_deploys_entry_is_skipped_not_a_crash` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-139: QA dimension 2, finding 8 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | no type check |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-121 — Concurrent closes can charge the same interval twice
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-state.py (`cmd_effort`), karvey_lib/effort.py
- **Change / origin:** wave3-optimization — finding F-140 (QA dimension 2, finding 10)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: two effort writes read the same uncharged interval.

### Actual vs expected
- Actual: two effort writes read the same uncharged interval.
- Expected: each interval charged once.

### Root cause
no lock around compute/store/charge.

### Fix
one lock per project root.

### Regression test
`plugins/karvey/tests/unit/test_effort.py`, `Command.test_BUG_121_the_interval_is_read_stored_and_charged_under_one_lock` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-140: QA dimension 2, finding 10 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | no lock around compute/store/charge |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-123 — Risk rewrite fails on a differently cased header
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/risks.py (`rewrite`)
- **Change / origin:** wave3-optimization — finding F-141 (QA dimension 2, finding 9)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: StopIteration with an "Id" header.

### Actual vs expected
- Actual: StopIteration with an "Id" header.
- Expected: any case accepted.

### Root cause
literal "ID"/"Owner" match.

### Fix
the row's own table header, any case.

### Regression test
`plugins/karvey/tests/unit/test_risks.py`, `Command.test_BUG_123_rewrite_finds_its_header_whatever_the_case` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-141: QA dimension 2, finding 9 |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | literal "ID"/"Owner" match |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-127 — `observed` misses files read relative to a `cd`
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-context-budget.py (`_bash_paths`)
- **Change / origin:** wave3-optimization — finding F-144 (manual script one-phase-per-session, step 4 (third rerun))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A session reads rules with `cd {plugin}/skills/karvey/rules; cat _core.md gates.md`; `observed --skill karvey-tasks`.

### Actual vs expected
- Actual: `opened:` lists only the skill; the rules read after the `cd` are not counted.
- Expected: every plugin markdown file the session read is listed.

### Root cause
Only paths naming `skills/` were matched; relative names after a `cd` were ignored.

### Fix
The command is split into segments; a `cd DIR` segment sets the directory and relative `*.md` read targets are resolved against it.

### Regression test
`plugins/karvey/tests/unit/test_close.py`, `Observed.test_BUG_101_skill_loads_and_shell_reads_count_as_opened` (the `cd` case, BUG-127) — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-144: manual script one-phase-per-session, step 4 (third rerun) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | relative paths after cd ignored |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-128 — Contract coverage passes with a contract gone
- **Priority:** high
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-context-budget.py (`_anchored`)
- **Change / origin:** wave3-optimization — finding F-145 (QA dimension 7 (second opinion, intra-model))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: an anchor in `_core.md` counted for every phase even when the phase no longer loads `_core.md`, and only the heading was checked (79/79 with the section emptied).

### Actual vs expected
- Actual: an anchor in `_core.md` counted for every phase even when the phase no longer loads `_core.md`, and only the heading was checked (79/79 with the section emptied).
- Expected: a contract counts only where its file is in the phase closure and its section still has a body.

### Root cause
anchor presence checked, not reachability or content.

### Fix
the anchor file must be in the phase closure and the section keep at least 12 words (`CONTRACT_MIN_WORDS`).

### Regression test
`plugins/karvey/tests/unit/test_contracts.py`, `Coverage.test_BUG_128_the_core_counts_only_for_a_phase_that_loads_it`, `plugins/karvey/tests/unit/test_contracts.py`, `Coverage.test_BUG_128_an_emptied_contract_section_is_not_loaded` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-145: QA dimension 7 (second opinion, intra-model) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | anchor presence checked, not reachability or content |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-129 — Webhook URLs with the secret in the path pass the leak check
- **Priority:** high
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/leak_patterns.json
- **Change / origin:** wave3-optimization — finding F-146 (QA dimension 7 (second opinion, intra-model))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: a chat webhook URL (`/services/T…/B…/…`) passed with ok=True.

### Actual vs expected
- Actual: a chat webhook URL (`/services/T…/B…/…`) passed with ok=True.
- Expected: any webhook URL or random 24+ character URL segment is a secret.

### Root cause
no rule for secrets in URL paths.

### Fix
rules `webhook-url`, `chat-webhook-path`, `url-random-segment`.

### Regression test
`plugins/karvey/tests/unit/test_leakcheck.py`, `QaDimension1.test_BUG_129_webhook_urls_and_random_url_segments_are_secrets` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-146: QA dimension 7 (second opinion, intra-model) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | no rule for secrets in URL paths |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-130 — Phone-like numbers exempt as versions
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/leakcheck.py (`_pii`)
- **Change / origin:** wave3-optimization — finding F-147 (QA dimension 7 (second opinion, intra-model))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: "9.8765.4321" passed as a version.

### Actual vs expected
- Actual: "9.8765.4321" passed as a version.
- Expected: a version only after `v` or a version word.

### Root cause
any dotted number exempt.

### Fix
version context required.

### Regression test
`plugins/karvey/tests/unit/test_leakcheck.py`, `QaDimension1.test_BUG_130_a_version_needs_a_v_or_version_context` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-147: QA dimension 7 (second opinion, intra-model) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | any dotted number exempt |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-131 — Secret assignments in Spanish or Portuguese pass
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/leak_patterns.json
- **Change / origin:** wave3-optimization — finding F-148 (QA dimension 7 (second opinion, intra-model))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: "clave: …" or "senha: …" with a secret value passed.

### Actual vs expected
- Actual: "clave: …" or "senha: …" with a secret value passed.
- Expected: caught as in English.

### Root cause
English keywords only.

### Fix
keywords contraseña, clave, secreto, senha, segredo, chave, credencial.

### Regression test
`plugins/karvey/tests/unit/test_leakcheck.py`, `QaDimension1.test_BUG_131_spanish_and_portuguese_assignments_are_secrets` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-148: QA dimension 7 (second opinion, intra-model) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | English keywords only |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-132 — Other-client names missed with other accents or case
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/leakcheck.py (`_client`)
- **Change / origin:** wave3-optimization — finding F-149 (QA dimension 7 (second opinion, intra-model))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: a client name written without its accents or in another case passed.

### Actual vs expected
- Actual: a client name written without its accents or in another case passed.
- Expected: accent- and case-insensitive match at a word start.

### Root cause
exact-text match.

### Fix
`fold()` (NFKD, casefold), word-start match, prefix for terms of 4+ characters.

### Regression test
`plugins/karvey/tests/unit/test_leakcheck.py`, `QaDimension1.test_BUG_132_client_names_ignore_accents_and_case_and_match_as_prefix` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-149: QA dimension 7 (second opinion, intra-model) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | exact-text match |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-133 — A phase dropped from the snapshot leaves the median silently
- **Priority:** low
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-context-budget.py (`cmd_compare`)
- **Change / origin:** wave3-optimization — finding F-150 (QA dimension 7 (second opinion, intra-model))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: a skill only in the baseline was left out of the median (renaming a low-reduction skill raised it).

### Actual vs expected
- Actual: a skill only in the baseline was left out of the median (renaming a low-reduction skill raised it).
- Expected: reported; an error when compare is the gate.

### Root cause
only common skills compared.

### Fix
`budget.only_in_base` error in gate mode (CI warn step unchanged).

### Regression test
`plugins/karvey/tests/unit/test_context_budget.py`, `Compare.test_BUG_133_a_phase_only_in_the_baseline_fails_the_gate` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-150: QA dimension 7 (second opinion, intra-model) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | only common skills compared |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-134 — Effort charges another session capture as exact
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/effort.py (`pick_capture`), karvey-state.py (`cmd_effort`)
- **Change / origin:** wave3-optimization — finding F-151 (QA dimension 7 (second opinion, intra-model))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: the latest capture of the project was charged as "exact" even from another session; agent-passed review minutes marked "exact".

### Actual vs expected
- Actual: the latest capture of the project was charged as "exact" even from another session; agent-passed review minutes marked "exact".
- Expected: only the closing session is exact; stated minutes never exact.

### Root cause
capture chosen by time, not by session.

### Fix
closing session from `--session` or the runtime session variable; otherwise "estimated"; review minutes "estimated", source "stated at the gate".

### Regression test
`plugins/karvey/tests/unit/test_effort.py`, `Lib.test_BUG_134_only_the_closing_sessions_capture_is_exact`, `plugins/karvey/tests/unit/test_effort.py`, `Lib.test_BUG_134_review_minutes_are_never_exact` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-151: QA dimension 7 (second opinion, intra-model) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | capture chosen by time, not by session |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-135 — done-direct accepts a commit that does not exist
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey_lib/backlog.py, karvey-state.py, karvey-context.py
- **Change / origin:** wave3-optimization — finding F-152 (QA dimension 7 (second opinion, intra-model))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: "0000000" accepted as the done-direct commit; states unvalidated; "open (blocked)" dropped from the view.

### Actual vs expected
- Actual: "0000000" accepted as the done-direct commit; states unvalidated; "open (blocked)" dropped from the view.
- Expected: the commit exists in git; states valid; one state reading everywhere.

### Root cause
regex only; two status comparisons.

### Fix
`git cat-file -e` (format only without git); `state_of` shared; unknown states warned, never dropped.

### Regression test
`plugins/karvey/tests/unit/test_backlog_wsjf.py`, `DoneDirectInGit.test_BUG_135_a_done_direct_commit_that_is_not_in_git_is_refused`, `plugins/karvey/tests/unit/test_backlog_wsjf.py`, `DoneDirectInGit.test_BUG_135_a_real_commit_is_accepted`, `plugins/karvey/tests/unit/test_backlog_wsjf.py`, `DoneDirectInGit.test_BUG_135_an_unknown_state_is_a_warning_not_dropped`, `plugins/karvey/tests/unit/test_backlog_wsjf.py`, `View.test_BUG_135_open_with_a_note_is_listed_and_an_unknown_state_is_invalid` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-152: QA dimension 7 (second opinion, intra-model) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | regex only; two status comparisons |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |

## BUG-136 — A risk can be moved to an unrelated item or moved twice
- **Priority:** medium
- **Detected:** 2026-09-27 · **Component:** plugins/karvey/scripts/karvey-state.py (`cmd_risk`, `_backlog_row`)
- **Change / origin:** wave3-optimization — finding F-153 (QA dimension 7 (second opinion, intra-model))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
See the finding: `--to BL-N` naming an unrelated item exited 0; a second move logged moved → moved.

### Actual vs expected
- Actual: `--to BL-N` naming an unrelated item exited 0; a second move logged moved → moved.
- Expected: both refused, nothing written.

### Root cause
no check of the target item or the current state.

### Fix
exit 3 unless the item cites the risk; from == to refused.

### Regression test
`plugins/karvey/tests/unit/test_risks.py`, `Command.test_BUG_136_move_to_an_unrelated_backlog_item_is_refused`, `plugins/karvey/tests/unit/test_risks.py`, `Command.test_BUG_136_a_second_move_is_refused` — fail on the previous code, pass on the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-27 | DETECTADO | maintainer agent (D-21) / Claude Opus 5.5 | F-153: QA dimension 7 (second opinion, intra-model) |
| 2026-09-27 | DIAGNOSTICADO | maintainer agent (D-21) / Claude Opus 5.5 | no check of the target item or the current state |
| 2026-09-27 | EN FIX | maintainer agent (D-21) / Claude Opus 5.5 | feature/wave3-optimization |
| 2026-09-27 | RESUELTO | maintainer agent (D-21) / Claude Opus 5.5 | fix + regression test, red before and green after |
