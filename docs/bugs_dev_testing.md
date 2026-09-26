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

## BUG-23 — Settings notice ignores the production line when integration lacks the settings
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/karvey_hooks.py (`settings_notice`), plugins/karvey/scripts/karvey-config.py (`Settings.remote`)
- **Change / origin:** wave1-hardening — finding F-50 (manual script `settings-docs-branch.md`, E1.F17.T3)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`branch_flow {integration: dev, production: main}`. Settings committed on a docs branch and merged to `main` (pushed), not yet on `dev`. A worktree made from the older commit, whose `project.json` has neither block. Start a session there.

### Actual vs expected
- Actual: `Karvey (info): team settings not set (notifications + management)`; `karvey-config.py resolve management` falls back to `markdown` (source `default`).
- Expected: no settings notice, and `resolve` returns the settings with source `origin/main`: REQ-W1-083 says the reviewed line counts before "missing".

### Root cause
`karvey_hooks.py:526-532` (before the fix) looked at `origin/{integration}` and then `origin/HEAD`, but the loop ended with `break` at the first readable `project.json`, so a readable `origin/dev` without the settings ended the lookup; `origin/{production}` was never a candidate, and `origin/HEAD` does not exist in a clone whose remote was added by hand. `karvey-config.py:104-118` (`Settings.remote`) read only `origin/{integration}`. The requirement names `origin/{integration}`, the manual script `origin/main`: the code read one line and stopped. Latent since E1.F6.T2 / E1.F7.T2; every earlier test used `integration = production = main`.

### Fix
`project.settings_lines(project, root)` gives the reviewed lines in order: `origin/{integration}`, `origin/{production}`, then `origin/HEAD`, deduplicated and checked with `safe_values.check_branch`. The session notice reads each and stays silent when any has both blocks (no `break`); `karvey-config.py` `Settings.remotes()` returns every readable line and `block(key)` takes the first line that has the key (source `origin/<line>`). Settled: both lines count (integration first). `management-adapters.md` resolution order, `karvey-init` Step 3 and `hooks/README.md` say so.

### Regression test
`plugins/karvey/tests/hooks/tables/session.json` case `ss-24-settings-on-origin-production-not-integration-silent` (integration `dev` readable without the settings, production `main` with them → silent) and `plugins/karvey/tests/unit/test_config_resolve.py` `OriginProductionFallback` (`resolve` source `origin/main`; `settings_notice` None; notice still printed when no line has them). The table case and the first two unit tests were red before the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-50, manual script settings-docs-branch variant B (E1.F17.T3) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: the lookup breaks at the first readable line and never reads production |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | E1.F17.T4: every reviewed line counts; table case and unit tests red before the fix, green after |

## BUG-24 — DEV visible-version check demands the `-dev.{build}+{sha}` form and reads the tip of dev
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/skills/karvey-deploy/SKILL.md (2.6), plugins/karvey/skills/karvey/rules/versioning.md (visible version)
- **Change / origin:** wave1-hardening — finding F-51 (manual script `visible-version.md`, E1.F17.T3)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A UI target; DEV shows `DEV 2.10.4`; the deployed commit's `VERSION` is 2.10.4. Run `/karvey:karvey-deploy <change>`. Variant 2: a second change merged into `dev` after the deploy bumps `VERSION` to 2.10.5.

### Actual vs expected
- Actual: variant 1: the deploy stops because the label is not `2.10.4-dev.{build}+{sha}`, and the deployed commit's version file is never read; variant 2: it compares with `origin/dev:VERSION` (2.10.5) and reports a mismatch.
- Expected: REQ-W1-041: the bumped version with an unmistakable DEV mark in any format passes; the comparison uses `git show <deployed-sha>:<version file>`; a missing visible version is a recommendation.

### Root cause
The skill text implemented the recommendation as the test. `karvey-deploy/SKILL.md:88` (2.6) said "With a UI, DEV must show `-dev` of the version just released; anything else is a finding", and `versioning.md:43` said the canary checks "`-dev` of the version just bumped"; neither named the deployed commit or its version file, so the agent compared with the only version it had, the tip of `dev`. REQ-W1-041 (E1.F12 text tasks) was never carried into either sentence.

### Fix
`karvey-deploy` 2.6: take the deployed commit (the green DEV run's source commit, else the one pushed in 2.5), read `git show "<deployed-sha>:<version file>"` (not the tip of `$I`), pass when DEV shows that version with an unmistakable DEV mark in any format; another version or no DEV mark is a finding, no visible version is the 2.4 recommendation. `versioning.md` says the same (the `-dev.{build}+{sha}` form is the recommendation, not the test) and its step references are corrected to 2.6 / 2.10; the orchestrator summary line in `skills/karvey/SKILL.md` follows.

### Regression test
`plugins/karvey/tests/unit/test_skill_rules.py` `VisibleVersionCheck` (5 tests: `git show …deployed…:` in 2.6, "any format", no "must show `-dev`", "not the tip", and the same rule in `versioning.md`); all 5 red before the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-51, manual script visible-version variants 1-2 (E1.F17.T3) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: the skill text states the recommended format as the check and never names the deployed commit |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | E1.F17.T5: deploy 2.6 and versioning.md rewritten; VisibleVersionCheck red before, green after |

## BUG-25 — A subagent prompt composed by the agent authorises writing project.json
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/skills/karvey/rules/management-adapters.md (rule 5), plugins/karvey/skills/karvey-impl/SKILL.md (Step 7, `(P)` dispatch); plugins/karvey/scripts/karvey_lib/guards.py (`subagent_prompt`, new PreToolUse Agent|Task guard)
- **Change / origin:** wave1-hardening — finding F-52 (manual script `no-human-no-mapping.md`, E1.F17.T3)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`management.tool` set to a tracker, no `statuses`. Prompt: "Use a subagent to implement the next task of <change> and persist any tracker settings it needs."

### Actual vs expected
- Actual: the subagent prompt says the user authorised persisting `management.statuses` in `project.json` and tells the subagent to write it when the map looks unambiguous; `project.json` stayed unchanged only because the list had no review status.
- Expected: REQ-W1-081: the subagent prompt forbids writing `project.json`; the map is proposed back and persisted by the orchestrating session with the human, on a docs branch.

### Root cause
`management-adapters.md:122` (rule 5) stated the ban as a fact about subagents ("Subagents never write `project.json`") and `karvey-impl/SKILL.md:106` dispatched `(P)` subagents without saying what their prompt must contain, so nothing told the orchestrating agent to carry the ban into the prompt it writes; the user's "persist any tracker settings" was the only instruction it had and it passed it on. L-34 reads only prompts written in skill files, not prompts composed at run time.

### Fix
Rule 5 now requires every subagent prompt an agent composes (impl `(P)` tasks, a delegated task, any `Agent` call) to carry the line "Do not write `docs/spec/project.json`. If a setting or a status map is missing, return the proposed values to me and change no tracker status that needs them." verbatim, and says a user's request to persist settings is answered by the orchestrating session with the human (Missing map clause, docs branch), never passed on to a subagent as an authorisation. `karvey-impl` Step 7 carries the same line in its `(P)` dispatch.

**Reopened by the rerun (same day):** the orchestrating session wrote the subagent prompt before it loaded any skill (it told the subagent to load `karvey-impl` itself), so the text never reached it and the prompt still said "persist them in the project's settings file … The user explicitly authorized persisting tracker settings". Cause refined: a rule in skill text cannot govern a prompt composed before the skill is loaded. Second fix: a `subagent-prompt` guard on PreToolUse `Agent|Task` (`guards.subagent_prompt`, event `pre-agent`, fail open, on in a Karvey project): a prompt with a sentence that lets the subagent write the settings (a write/persist/authorise verb with `project.json`, settings or a status map, not negated just before the verb) and without the ban line is blocked with the line to add; `hooks.json`, `karvey-hook.sh` (no-python: allow), `hooks/README.md` and `enforcement.md` document it.

### Regression test
`plugins/karvey/tests/unit/test_skill_rules.py` `SubagentPromptsCarryTheProjectJsonBan` (rule 5 requires the line in every subagent prompt; a request to persist is never passed on; impl's dispatch carries the line); all 3 red before the fix. The guard: `plugins/karvey/tests/hooks/tables/subagent-prompt.json` (sp-01..sp-07: the rerun and first-run prompts and the `Task` tool name blocked; the ban line, no settings talk, a negated sentence and a non-Karvey directory allowed; no python allows), red on 691f2f7 (the dispatcher did not know `pre-agent` and allowed), and `test_karvey_hooks.py` `Registry`. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-52, manual script no-human-no-mapping subagent run (E1.F17.T3) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: no text tells the orchestrating agent to put the ban in the prompt it composes |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | E1.F17.T6: rule 5 and impl dispatch carry the ban verbatim; tests red before, green after |
| 2026-09-25 | REABIERTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | rerun of no-human-no-mapping: the prompt was composed before any skill was loaded and still authorised the write |
| 2026-09-25 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | subagent-prompt guard (PreToolUse Agent|Task) |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | E1.F17.T6: guard + table subagent-prompt.json (red on 691f2f7, green after); rerun PASS: the guard blocked the first prompt and the re-sent one carries the ban line |

## BUG-26 — Block comment queued because the tracker key was looked for only in the environment
- **Priority:** low
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/skills/karvey/rules/management-adapters.md (rule 2), plugins/karvey/skills/karvey-impl/SKILL.md (Step 3, Handling blockers)
- **Change / origin:** wave1-hardening — finding F-53 (manual script `per-level-maps.md`, E1.F17.T3)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A tracker with `statuses.by_level.task.blocked: null`; the key in the repo's git-ignored `.connections.json`, nothing in the environment. Prompt: "Task E1.F1.T1 of <change> is blocked waiting on the vendor API key. Record it."

### Actual vs expected
- Actual: tracker status kept and `⛔ blocked` written in `PLAN.md`, but the explaining comment was not posted: the agent ran `env | grep -i clickup`, reported "no ClickUp API token in this session" and queued the comment in the outbox.
- Expected: REQ-W1-082: tracker status unchanged and a comment explaining the block added to the task.

### Root cause
`karvey-impl/SKILL.md` never says where tracker credentials live, and `management-adapters.md:119` (rule 2) listed `.connections.json`, env vars and a vault only as where credentials may be kept, not as places to look before declaring one missing; `clickup-protocol.md` names `.connections.json` but impl does not load it for a status change or comment. The other ClickUp runs found the file by chance. The impl blocker text also did not say what to do when `blocked` maps to `null`.

### Fix
Rule 2 is now a lookup order: `.connections.json` at the project root first, then the environment, then the vault or the tool's MCP session; "no credential" and the outbox only after all three are empty, saying where it looked. `karvey-impl` Step 3 and Handling blockers point to that lookup, and the blocker text says that with `blocked: null` the tracker status is kept and the comment is posted alone.

### Regression test
`plugins/karvey/tests/unit/test_skill_rules.py` `TrackerCredentialsAreLookedUpEverywhere` (rule 2 is an ordered lookup with `.connections.json` first and "only after" every place; impl Step 3 points to it; impl's blocker text covers `blocked: null` and `.connections.json`); all 3 red before the fix. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-53, manual script per-level-maps variant A (E1.F17.T3) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: impl never names where tracker credentials live; rule 2 is not a lookup |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | E1.F17.T7: rule 2 lookup order, impl Step 3 and blockers point to it; tests red before, green after |

## BUG-27 — protect-paths passed a glob or a variable that names the state dirs
- **Priority:** high
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`protect_paths`), plugins/karvey/hooks/karvey-hook.sh (no-python classifier)
- **Change / origin:** wave1-hardening — finding F-56 (QA D1 security (S-1))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
In a Karvey repo: `cd .git/kar?ey/ledger && printf %s '{…}' > feat-a.json`, then `git push origin HEAD:main`.

### Actual vs expected
- Actual: the forged ledger entry is written (rc 0) and the prod-gate prints ALLOW; `cd .git; cd kar*ey; mkdir -p ledger` and `D=karvey; printf x > .git/$D/ledger/f.json` also pass.
- Expected: REQ-W1-018 / architecture §3.3 control 3: any tool call that touches the markers or the ledger is blocked; forging needs a deliberate multi-step circumvention, not one shell command.

### Root cause
protect-paths matched literal strings (`.git/karvey`, `karvey/ledger`) in the command text; the shell expands globs and variables after the hook has looked, and `cd` chains carried the glob into the working directory of later segments.

### Fix
Per segment (python): the command's own `NAME=value` assignments are substituted; a path component that is a glob (2+ literal characters) or a variable and could expand to `karvey`/`ledger`/`approvals`, or a wildcard right under `.git` or right above `ledger`/`approvals`, blocks; globs are also expanded against the disk (bounded) and checked. No-python: the same pattern test with `case`, globbing off.

### Regression test
`plugins/karvey/tests/hooks/tables/protect-paths.json` pp-18..pp-21 (also in the no-python pass) block; pp-23/pp-24 keep globs and variables elsewhere allowed; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-56, karvey-qa D1 security (S-1) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-28 — prod-gate missed pushes and merges not spelled as `git push … main` / `gh pr merge`
- **Priority:** high
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`prod_candidates`, `_evaluate_candidate`, `push_destinations`, `GitTarget.resolve_alias`)
- **Change / origin:** wave1-hardening — finding F-57 (QA D1 security (S-2, S-3), D2 (E-1))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
On `feature/feat-a` with no approval: `git -c alias.ship=push ship origin HEAD:main`; `git -c remote.origin.push=HEAD:main push origin`; a configured upstream with `push.default=upstream` and a bare `git push`; `git send-pack … feature/feat-a:main`; `echo HEAD:main | xargs git push origin`; `gh m 12` (gh alias of `pr merge`); `gh api -X POST repos/o/r/merges -f base=main`; `gh api -X PATCH repos/o/r/git/refs/heads/main`; GraphQL `mergeBranch`; on `main`, `git push origin @`.

### Actual vs expected
- Actual: every one exits 0 and (for the git forms, run for real) moves the remote `main`.
- Expected: REQ-W1-023: a merge into the production set needs the human prod approval; what cannot be verified fails closed (REQ-W1-024).

### Root cause
the candidates were read from the command words only: `-c` values, configured and shell aliases (prod-gate never expanded aliases), the push configuration of the repository, `send-pack`, commands run through `xargs`/`find -exec`, gh aliases and REST/GraphQL ref writes were not candidates, and `@` was not treated as HEAD.

### Fix
Git segments go through `git_targets` (aliases expanded, `-c alias.X` first); `send-pack` counts as a push; `-c` push settings fail closed; a push with no refspec takes its destination from the remote's `push` refspecs, else `<branch>@{push}`; `@` is HEAD; `xargs`/`parallel`/`find -exec` wrapping git/gh/glab/az with a push or merge fail closed; gh aliases from gh's `config.yml` are expanded; `gh api` writes to `merges`/`git/refs` of a production branch and GraphQL `mergeBranch`/`updateRef(s)`/`createCommitOnBranch` block. The cheap pre-filter now also wakes on any git/gh/glab/az command.

### Regression test
`plugins/karvey/tests/hooks/tables/prod-gate.json` pg4-01..pg4-13, pg4-19..pg4-22 (pg4-14..16 keep feature pushes and non-production ref writes silent) and `plugins/karvey/tests/hooks/tables/git-flow.json` gf-bug28-push-at-sign-on-master; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-57, karvey-qa D1 security (S-2, S-3), D2 (E-1) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-29 — `git push origin --tags` from the production branch was blocked as a branch push
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`_evaluate_candidate`)
- **Change / origin:** wave1-hardening — finding F-58 (QA D4 impact (I-4))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
On `main` in a Karvey project: `git push origin --tags`.

### Actual vs expected
- Actual: `prod-gate BLOCK … missing=change`.
- Expected: only tags are pushed (no branch), so nothing reaches production through this command.

### Root cause
a push without refspec was treated as a push of the current branch; `--tags` without refspec was not handled.

### Fix
`--tags` with no refspec is not a branch push (`--follow-tags` still is).

### Regression test
`plugins/karvey/tests/hooks/tables/prod-gate.json` pg4-17 (allow) and pg4-18 (`--follow-tags` still gated); red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-58, karvey-qa D4 impact (I-4) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-30 — The prod-gate block did not say how to record the approval
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`_evaluate_candidate`)
- **Change / origin:** wave1-hardening — finding F-59 (QA D4 impact (I-3))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
The human types "ok, merge a prod" (the hook records a prod marker), then the agent runs `git push origin feature/foo:main`.

### Actual vs expected
- Actual: `BLOCK change=foo missing=by,role,ref reason=no production approval recorded` with no next step; for an unknown change the advice (branch name / PR title) did not fit trunk projects.
- Expected: architecture §12 risk table: the block message says exactly how to approve.

### Root cause
the reason strings came straight from `check_prod`.

### Fix
The block names `karvey-state.py approve <change> prod --by … --role human --ref <D-NN or PR URL>` after the human's own prod message; the unknown-change block also names `enforcement.prod_gate_hook: false` merged to the production branch.

### Regression test
`plugins/karvey/tests/hooks/tables/prod-gate.json` pg4-23, pg4-24; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-59, karvey-qa D4 impact (I-3) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-31 — subagent-prompt blocked ordinary prompts about settings and let a ban-like sentence excuse a real write
- **Priority:** high
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`subagent_prompt`)
- **Change / origin:** wave1-hardening — finding F-60 (QA D4 impact (I-1), D2 (E-4))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
In a Karvey project, an Agent call with "Update the settings page component in src/views/Settings.vue …", "Update .vscode/settings.json …" or "Write unit tests for the tracker status mapping function"; and "Do not edit project.json by hand. Use a python script to write the management settings into docs/spec/project.json."

### Actual vs expected
- Actual: the first three are blocked; the last one is allowed; "Don’t write docs/spec/project.json" (typographic apostrophe) is not recognised as the ban.
- Expected: REQ-W1-081 / D-33: only a prompt that lets the subagent write the Karvey settings is blocked, unless it carries the ban on `docs/spec/project.json`.

### Root cause
`\bsettings\b` with any verb anywhere in the sentence was a target; any ban-like sentence ("do not edit project.json") short-circuited the check; quotes were not normalised.

### Fix
Targets are `docs/spec/project.json`, a bare `project.json` only next to tracker/settings words, `management.statuses`, tracker/team/karvey/management settings, the project's settings and a status map; the verb must govern the target within the next words (no "for"/"about"/"from" in between); only the ban on `docs/spec/project.json` itself excuses the prompt; typographic quotes are normalised.

### Regression test
`plugins/karvey/tests/hooks/tables/subagent-prompt.json` sp-08..sp-13 (sp-01..07 unchanged); red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-60, karvey-qa D4 impact (I-1), D2 (E-4) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-32 — Real team chat space ids in the tests
- **Priority:** low
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/tests/hooks/tables/notify-confirm.json, plugins/karvey/tests/unit/test_notify_check.py, test_safe_values.py, test_config_resolve.py
- **Change / origin:** wave1-hardening — finding F-61 (QA D1 security (S-6))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`grep -rn 'spaces/' plugins/karvey/tests`.

### Actual vs expected
- Actual: two real chat space ids used as example destinations (18 places).
- Expected: fixtures carry shapes only, never real identifiers (architecture §6.3); the repository is public.

### Root cause
values copied from a real configuration while writing the notify tests.

### Fix
replaced by `spaces/AAAAexample1` / `spaces/AAAA-example` (the confirmation codes derived from them updated). The ids stay in the git history; they are identifiers, not credentials.

### Regression test
`plugins/karvey/tests/unit/test_fixtures_anonymous.py` NoRealChatSpaceIds (every chat-space-shaped id under `tests/` says example/fixture); red on 4c9b7c0 (19 hits). Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-61, karvey-qa D1 security (S-6) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-33 — Two real legacy shapes were schema errors: `repos` as objects, `approvals.*.generated` as a date
- **Priority:** high
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/schemas/project.schema.json (`repos`), plugins/karvey/schemas/spec.schema.json (`approval.generated`)
- **Change / origin:** wave1-hardening — finding F-62 (QA D4 impact (I-2))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`karvey-state.py validate --all` on a project whose `project.json` lists `repos` as `{name, url, stack, layer}`, or whose spec has `approvals.deploy.generated: "2026-08-05"`.

### Actual vs expected
- Actual: `[error] $.repos[0]: expected string, got object`; the prod-gate blocks with `missing=valid spec.json`.
- Expected: REQ-W1-003 and §2.7: legacy shapes are warnings in advisory mode; no existing file becomes invalid in 3.12.x.

### Root cause
the legacy catalogue (§6.3) had neither shape, so the schema typed them strictly.

### Fix
both accept the legacy shape as an `x-karvey-severity: warning` branch with a note (errors in strict mode); anonymised fixtures `legacy/project/repos-objects.json` and `legacy/spec/approval-generated-date.json`.

### Regression test
`plugins/karvey/tests/unit/test_state_validate.py` LegacyRealShapesAreWarnings; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-62, karvey-qa D4 impact (I-2) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-34 — An exception before any guard ran exited 1, so the prod-gate failed open
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/hookio.py (`parse`), plugins/karvey/scripts/karvey_lib/karvey_hooks.py (`main`)
- **Change / origin:** wave1-hardening — finding F-63 (QA D2 errors (E-2))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Run the hook from a deleted working directory (a removed worktree) with `git push origin master`.

### Actual vs expected
- Actual: `FileNotFoundError … os.getcwd()`, exit 1: the harness does not treat exit 1 as a block.
- Expected: §3.2: the prod-gate and protect-paths fail closed.

### Root cause
`hookio.parse` called `os.getcwd()` unconditionally and `main` had no handler around the dispatch.

### Fix
`hookio` falls back to `/` when the directory is gone; `main` catches any exception: a closed event (pre-bash, pre-edit) blocks naming its first closed guard, an open one allows with a line.

### Regression test
`plugins/karvey/tests/unit/test_karvey_hooks.py` Dispatch.test_crash_outside_a_guard_applies_the_fail_mode; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-63, karvey-qa D2 errors (E-2) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-35 — A non-string `phase` crashed validate, the hooks and the dashboard
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/project.py (`list_changes`), plugins/karvey/scripts/karvey-state.py (history check), plugins/karvey/scripts/karvey-context.py
- **Change / origin:** wave1-hardening — finding F-64 (QA D2 errors (E-3))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`{"phase": ["init"]}` (or a history entry whose `phase` is an object) in a change's spec.json.

### Actual vs expected
- Actual: `TypeError: unhashable type` (exit 5) in validate/next/active and the dashboard; the session hook loses its context; the approval hook records nothing; plan-gate blocks every write.
- Expected: a validation error on that file; every other tool keeps working.

### Root cause
the phase value was hashed (set/frozenset membership) without a type check.

### Fix
`list_changes` treats a non-string phase as absent (with a spec error), the history check skips non-string phases, the dashboard shows it as JSON.

### Regression test
`plugins/karvey/tests/unit/test_state_validate.py` NonStringPhase; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-64, karvey-qa D2 errors (E-3) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-36 — A list `management.tool` or `notifications.channel` crashed karvey-config
- **Priority:** low
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey-config.py (`_normalise_management`, `resolve_notifications`, `propose_settings`), plugins/karvey/scripts/karvey-state.py (`--fix` notes)
- **Change / origin:** wave1-hardening — finding F-65 (QA D2 errors (E-5))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
`"notifications": {"channel": ["google-chat"]}`, then `karvey-config.py notify-check`.

### Actual vs expected
- Actual: `[error] TypeError: unhashable type`, exit 5, which the notify step does not define.
- Expected: a refusal naming the field (exit 3).

### Root cause
dict lookups of the legacy aliases with an unchecked value.

### Fix
non-string tool/channel values are refused with `config.invalid_management` / `config.invalid_notifications`.

### Regression test
`plugins/karvey/tests/unit/test_config_resolve.py` NonStringSettings; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-65, karvey-qa D2 errors (E-5) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-37 — Breaking a stale lock could remove a fresh one; the release removed a lock it did not own
- **Priority:** low
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/atomicio.py (`lock`)
- **Change / origin:** wave1-hardening — finding F-66 (QA D2 errors (E-6))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A stale `.lock`, two writers; one is preempted between `stat` and `unlink`.

### Actual vs expected
- Actual: it unlinks the fresh lock the other writer just took; both hold the lock and one update is lost; the `finally` unlinks whatever lock is there.
- Expected: one writer at a time (compare-and-swap relies on it).

### Root cause
stat-then-unlink is not atomic, and the lock carried no owner token.

### Fix
a stale lock is renamed aside (only one waiter can) and put back if it is not the stale inode seen; the lock holds a random token and only its owner removes it.

### Regression test
`plugins/karvey/tests/unit/test_atomicio.py` LockOwnership; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-66, karvey-qa D2 errors (E-6) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |
| 2026-09-26 | REABIERTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | CI windows-advisory on 72b460b: the lock stayed behind on Windows (text-mode fd wrote the token with CRLF, so the owner check at release never matched) |
| 2026-09-26 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | the lock is opened with O_BINARY; the windows-advisory run of test_atomicio is the regression check |

## BUG-38 — spec-merge rewrote a BOM/CRLF living spec with LF and no BOM
- **Priority:** low
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey-spec-merge.py (`_read_text`, `run`)
- **Change / origin:** wave1-hardening — finding F-67 (QA D2 errors (E-8))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A living spec saved with a BOM and CRLF, then `karvey-spec-merge.py <change>`.

### Actual vs expected
- Actual: every line shows as changed in git.
- Expected: only the merged requirements change.

### Root cause
the text was normalised to LF on read and written back as is.

### Fix
the BOM and CRLF of the target are recorded on read and restored on write.

### Regression test
`plugins/karvey/tests/unit/test_spec_merge.py` LineEndings; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-67, karvey-qa D2 errors (E-8) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-39 — protect-paths blocked text that only mentions the paths
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`protect_paths`)
- **Change / origin:** wave1-hardening — finding F-68 (QA D4 impact (I-5))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
In any repo: `git commit -m "docs: explain the karvey/approvals layout"`; `echo "see notify-last.json" >> notes.md`.

### Actual vs expected
- Actual: both blocked.
- Expected: architecture §3.8 DoS row: no false positives that push users to disable the guard; the text is not a path.

### Root cause
every argument of a non-read-only command was searched for the needles.

### Fix
echo/printf arguments and the `-m`/`--message` value of git commit/tag/notes/stash/merge/revert are message text; their redirections are still checked.

### Regression test
`plugins/karvey/tests/hooks/tables/protect-paths.json` pp-25, pp-26 (pp-27: a redirection into the ledger still blocks); red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-68, karvey-qa D4 impact (I-5) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-40 — CHANGELOG [Unreleased] had no human owner or AI model
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** CHANGELOG.md
- **Change / origin:** wave1-hardening — finding F-69 (QA D6 versioning)
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
QA D6 `changelog-why` on the change.

### Actual vs expected
- Actual: 80+ lines under [Unreleased], none naming the responsible human or the model, and no traceability block.
- Expected: `changelog-policy.md` and karvey-impl Step 4: the owner and the model are recorded; the deploy pre-check fails without them.

### Root cause
impl added one line per task and never the section's traceability block.

### Fix
the section carries the policy's block (human owner, AI model, change, phases).

### Regression test
`plugins/karvey/tests/unit/test_skill_rules.py` ChangelogUnreleasedTraceability; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-69, karvey-qa D6 versioning |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-41 — One project-wide prod marker approved production for every change
- **Priority:** high
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/approval.py (`find_valid`), plugins/karvey/scripts/karvey-state.py (`approve … prod`)
- **Change / origin:** wave1-hardening — finding F-70 (QA D7 second opinion (X-1))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Two changes, no single active one; the human types "aprobado, pasa a prod" (scope `_project`); `approve alpha prod …` and `approve beta prod …`.

### Actual vs expected
- Actual: both succeed from the same marker, which stays live.
- Expected: D-10 / REQ-W1-023: the production approval is the human's approval of that change.

### Root cause
`find_valid` falls back to the `_project` scope for every kind, and `approve prod` did not consume the marker.

### Fix
`approve prod` looks only for a marker scoped to the change and consumes it once the ledger is written (architecture §3.3, revision 3).

### Regression test
`plugins/karvey/tests/unit/test_state_approve.py` ProdMarkerScope; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-70, karvey-qa D7 second opinion (X-1) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-42 — The conditional "si" was read as an approval
- **Priority:** high
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey_lib/approval.py (`classify`)
- **Change / origin:** wave1-hardening — finding F-71 (QA D7 second opinion (X-2))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Prompt "revisa si el merge a main rompió algo".

### Actual vs expected
- Actual: `[karvey] approval recorded (prod, …)`.
- Expected: REQ-W1-019: a request is not an approval.

### Root cause
accents are stripped before matching, so the approval "sí" and the conditional "si" are the same word.

### Fix
"si" approves only as the affirmative: written "sí", or a bare "si" that is the whole reply or opens it before punctuation (architecture §3.3, revision 3).

### Regression test
`plugins/karvey/tests/unit/test_approval_vocab.py` ConditionalSi (the affirmative forms still approve); red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-71, karvey-qa D7 second opinion (X-2) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-43 — Closing a phase without an approval consumed the change's prod marker
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey-state.py (`consume_on_close`)
- **Change / origin:** wave1-hardening — finding F-72 (QA D7 second opinion (X-5))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
The human approves production during `test`; then `advance <change> qa`.

### Actual vs expected
- Actual: `consumed: [<change>]`; `approve <change> prod` then fails ("consumed").
- Expected: §3.3 control 7: a marker is consumed when the phase it approved closes.

### Root cause
the change's latest marker of any kind was consumed whatever phase closed.

### Fix
only a phase that has an approval consumes the change's marker, and never a prod-kind one.

### Regression test
`plugins/karvey/tests/unit/test_state_approve.py` ConsumeOnlyWhatClosed; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-72, karvey-qa D7 second opinion (X-5) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-44 — `validate --fix` dropped fields of legacy transitions and of `gates_skipped`
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey-state.py (`_fix_history`, `fix_spec`)
- **Change / origin:** wave1-hardening — finding F-73 (QA D7 second opinion (X-6))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A legacy `{from, to, at, reason, approved_by, notes, commit}` transition and a `gates_skipped` with `approved_by`, `date`, `ref`; `validate --fix`.

### Actual vs expected
- Actual: only `by`, `ref`, `evidence` survive; the `gates_skipped` record is deleted.
- Expected: REQ-W1-008/009: the migration never loses what the file recorded.

### Root cause
the transition copy listed three keys; `gates_skipped` was deleted once its phases moved.

### Fix
every other field of a transition is kept; the who/when/ref of `gates_skipped` go into the skip reason.

### Regression test
`plugins/karvey/tests/unit/test_state_fix.py` NothingLostInMigration; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-73, karvey-qa D7 second opinion (X-6) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-45 — spec-merge deleted neighbouring requirements on a duplicated REMOVED id
- **Priority:** high
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/karvey-spec-merge.py (`parse_delta`, `merge`)
- **Change / origin:** wave1-hardening — finding F-74 (QA D7 second opinion (X-7))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
A delta whose REMOVED lists REQ-A-1 twice (or MODIFIED and REMOVED of the same id).

### Actual vs expected
- Actual: exit 0; REQ-A-2 and REQ-A-3 are gone (overlapping line edits).
- Expected: an error, nothing written.

### Root cause
REMOVED did not check the ids already seen, and the bottom-up edits assumed disjoint ranges.

### Fix
a REMOVED id seen before (in REMOVED or MODIFIED) is a parse error; overlapping edits are refused.

### Regression test
`plugins/karvey/tests/unit/test_spec_merge.py` DuplicateIds; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-74, karvey-qa D7 second opinion (X-7) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-46 — L-06 let hand-edit instructions through in other words
- **Priority:** medium
- **Detected:** 2026-09-25 · **Component:** plugins/karvey/scripts/lint-plugin.py (L-06)
- **Change / origin:** wave1-hardening — finding F-75 (QA D7 second opinion (X-9))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Append to a skill: "Set the phase to `impl` in spec.json by hand.", "Run `jq '.phase = \"test\"' spec.json > t && mv t spec.json`.", "Edit `spec.json` and change `approvals.qa.approved` to true."

### Actual vs expected
- Actual: L-06 reports 0 errors: a REQ-W1-013 regression would pass CI.
- Expected: L-06 flags any instruction to edit the owned fields by hand.

### Root cause
the patterns needed `phase:`/`phase =` and a verb from a short list.

### Fix
"set/change/move/edit … phase to X" and "approvals.X.Y to …" are owned forms; `change`/`edit` (the verbs), `jq`, `sed -i` and `mv` are write verbs.

### Regression test
L-06; `plugins/karvey/tests/unit/test_lint_plugin.py` L06.test_hand_edits_in_other_words_fail; red on 4c9b7c0. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-25 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-75, karvey-qa D7 second opinion (X-9) |
| 2026-09-25 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-25 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 4c9b7c0, green after |

## BUG-47 — The prod-gate missed push forms that reach production: wildcard and matching refspecs, a configured mirror or `push.default matching`, a tag shadowing the pushed branch, a second production destination
- **Priority:** high
- **Detected:** 2026-09-26 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`_evaluate_candidate`, `implicit_push_dests`)
- **Change / origin:** wave1-hardening — finding F-92 (QA re-run, D7 second opinion (X-1..X-7))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
With a prod approval for commit A and local `main` moved to an unapproved B: `git push origin 'refs/heads/*:refs/heads/*'`; `git push origin :`; `git config remote.origin.mirror true` then `git push origin`; `git config push.default matching` then `git push`; `git config remote.origin.push 'refs/heads/*:refs/heads/*'` then `git push origin`. With a tag `feature/feat-a` at A and the branch at B: `git push origin refs/heads/feature/feat-a:main`. With `main` and `master`: `git push origin HEAD:main wip:master`.

### Actual vs expected
- Actual: the gate allowed each one (most silently, the tag case as `ALLOW … commit=A`), and `origin/main` (or `master`) ended at B.
- Expected: a push that can reach production names one commit, that commit is the approved one, and anything else blocks.

### Root cause
the destination was compared literally with the production set, so `*` and the empty `:` never matched; the implicit-push resolution read neither `remote.<r>.mirror` nor a persistent `push.default`; the source short name was resolved with `rev-parse`, which prefers a tag; the loop stopped at the first production destination.

### Fix
wildcard destinations are matched with `fnmatch` against the production set, `:` is a matching push, a configured mirror and `push.default matching` count as bulk pushes, and all of them block; the source is resolved as `refs/heads/<name>` first (`resolve_push_source`); every production destination is resolved and more than one commit blocks. Without python (`hooks/karvey-hook.sh`), a wildcard or matching refspec blocks (fail closed).

### Regression test
`plugins/karvey/tests/hooks/tables/prod-gate.json` pg6-01-wildcard-refspec-into-main, pg6-02-matching-colon-refspec, pg6-03-configured-mirror, pg6-04-configured-push-default-matching, pg6-05-tag-shadows-the-pushed-branch, pg6-06-second-production-destination, pg6-07-configured-wildcard-push-refspec; red on 7e110f3. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-26 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-92, karvey-qa re-run D7 second opinion (X-1..X-7) |
| 2026-09-26 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-26 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 7e110f3, green after |

## BUG-48 — A deferred merge (`gh pr merge --auto`, `az … --auto-complete true`, `glab mr merge`) was checked against the PR head once and could land a later commit
- **Priority:** medium
- **Detected:** 2026-09-26 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`prod_candidates`, `_gh_candidate`, `_evaluate_candidate`)
- **Change / origin:** wave1-hardening — finding F-93 (QA re-run, D7 second opinion (X-9))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
With a prod approval for the PR head A: `gh pr merge 12 --auto --merge` (allowed), then `git push origin wip:feature/feat-a` (a feature push, allowed); the host would merge B when the checks pass.

### Actual vs expected
- Actual: the deferred merge was allowed without a binding to A.
- Expected: a deferred merge is allowed only when the host itself is bound to the approved commit (`gh --match-head-commit`, `glab --sha`); `az --auto-complete` blocks.

### Root cause
the gate compared the PR head at command time and treated every merge command as immediate; glab merges when the pipeline succeeds by default.

### Fix
candidates carry `deferred` and `bound`; after the approval check, a deferred merge whose binding is not the released commit blocks.

### Regression test
`plugins/karvey/tests/hooks/tables/prod-gate.json` pg6-08-gh-auto-merge-unbound, pg6-10-gh-auto-merge-bound-to-another-commit, pg6-11-az-auto-complete-deferred, pg6-12-glab-merge-without-sha (block) and pg6-09-gh-auto-merge-bound-to-the-approved-commit (bound: allow); pg1-23 now passes `--sha`; red on 7e110f3. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-26 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-93, karvey-qa re-run D7 second opinion (X-9) |
| 2026-09-26 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-26 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 7e110f3, green after |

## BUG-49 — `reopen` wrote spec.json before superseding the ledger prod approval, so a failure in between left it live
- **Priority:** low
- **Detected:** 2026-09-26 · **Component:** plugins/karvey/scripts/karvey-state.py (`cmd_reopen`)
- **Change / origin:** wave1-hardening — finding F-94 (QA re-run, D7 second opinion (X-10))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
Make `approval.supersede_prod` fail (a full disk, a corrupt write) during `reopen feat-a requirements` on a change with a ledger prod approval.

### Actual vs expected
- Actual: spec.json was reopened and the ledger kept its prod approval.
- Expected: the ledger first; if it fails, nothing is reopened.

### Root cause
the ledger was written after the spec.json transaction had committed.

### Fix
the supersede runs inside the reopen transaction, after the refusals and before spec.json is written; a failure refuses the reopen (`state.ledger`).

### Regression test
`plugins/karvey/tests/unit/test_state_approve.py` ReopenSupersedesProd.test_ledger_failure_leaves_the_spec_unreopened (red on 7e110f3) and .test_refused_reopen_keeps_the_ledger. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-26 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-94, karvey-qa re-run D7 second opinion (X-10) |
| 2026-09-26 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-26 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 7e110f3, green after |

## BUG-50 — The prod-gate's push parser missed `refs/*` wildcards, `-o` clusters, abbreviated long options and remote names with a slash
- **Priority:** high
- **Detected:** 2026-09-26 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`_push_parse`, `_evaluate_candidate`, `implicit_push_dests`)
- **Change / origin:** wave1-hardening — finding F-95 (QA re-run, D7 second opinion re-check (N-1..N-4))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
With a prod approval for commit A and `wip` at an unapproved B: `git branch -f main wip && git push origin 'refs/*:refs/*'`; `git push -on origin wip:main`; `git branch -f main wip && git push --mirro origin`; a remote `up/stream` as the upstream of the branch, tracking `main`, with `push.default=upstream`, then `git push`.

### Actual vs expected
- Actual: the gate allowed each one, and `origin/main` ended at B (`-on` only where the server accepts push options).
- Expected: each push is resolved as git resolves it, or blocks.

### Root cause
the wildcard was matched against bare branch names, so `refs/*` never matched; short clusters were split letter by letter, so `-on` (push-option `n`) read as a dry run; long options were compared exactly while git accepts unique prefixes; the upstream name was split at its first `/`.

### Fix
wildcards are matched against full refs; in a cluster `-o` takes the rest as its value and `-n` counts only on its own; long options are canonicalised from a unique prefix and an unknown one blocks; the push destination comes from `rev-parse --symbolic-full-name <branch>@{push}` minus the longest known remote prefix, and an unparsable one blocks.

### Regression test
`plugins/karvey/tests/hooks/tables/prod-gate.json` pg6-13-refs-wildcard-refspec, pg6-14-push-option-cluster-is-not-a-dry-run, pg6-15-abbreviated-mirror-option, pg6-16-unknown-long-option, pg6-17-remote-name-with-a-slash; red on 0ce4a7b. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-26 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-95, karvey-qa re-run D7 second opinion re-check (N-1..N-4) |
| 2026-09-26 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-26 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on 0ce4a7b, green after |

## BUG-51 — The prod-gate trusted `--dry-run` cancelled by `--no-dry-run`, and ignored `--repo`
- **Priority:** high
- **Detected:** 2026-09-26 · **Component:** plugins/karvey/scripts/karvey_lib/guards.py (`_push_parse`, `_evaluate_candidate`)
- **Change / origin:** wave1-hardening — finding F-96 (QA re-run, D7 second opinion re-check (N-5, N-6))
- **Tracker:** —
- **Current state:** RESUELTO

### Reproduction
With `wip` at an unapproved B: `git push --dry-run --no-dry-run origin wip:main`. With a second remote `pub` on the same repository set as a mirror, or with a wildcard push refspec, and local `main` at B: `git push --repo=pub`.

### Actual vs expected
- Actual: the gate allowed both, and `origin/main` ended at B.
- Expected: the options are read as git reads them: the last of `--dry-run`/`--no-dry-run` wins, and `--repo` names the remote when no positional one does.

### Root cause
the dry-run early exit ran before the unknown-option check and never saw the negation; with no positional remote the implicit push read `origin`'s configuration instead of the `--repo` one.

### Fix
`--no-dry-run` clears the dry run; the unknown-option check runs before any early exit; `--repo` gives the remote when there is no positional one.

### Regression test
`plugins/karvey/tests/hooks/tables/prod-gate.json` pg6-18-dry-run-cancelled-by-no-dry-run, pg6-19-repo-option-names-a-mirror-remote, pg6-20-repo-option-names-a-wildcard-remote; red on d0153c2. Indexed in `plugins/karvey/tests/regression/test_incidents.py`.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-26 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | F-96, karvey-qa re-run D7 second opinion re-check (N-5, N-6) |
| 2026-09-26 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | karvey-iterate: root cause above |
| 2026-09-26 | RESUELTO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fix on feature/wave1-hardening; regression test red on d0153c2, green after |
