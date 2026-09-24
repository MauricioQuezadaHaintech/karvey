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
- **Current state:** DETECTADO

### Reproduction
Resume `karvey-impl` on a change whose [DB] tasks are done: they sit at `👀 review` (impl's new end state, and no skill moves them to `done`, F-06). The skill picks the "first pending task" and waits "until its dependent [DB] is completed".

### Actual vs expected
- Actual: "completed" read as `done` -> no [Backend] task ever starts (deadlock); an orphan `in_progress` after a crash is skipped or re-run depending on the reading; the source for "pending" (tracker, PLAN.md, tasks.md) is unstated.
- Expected: logical states only (REQ-ADP-021): next = first `todo` or orphan `in_progress`; a dependency is satisfied at `review` or `done`; one declared source for resuming, drift reported.

### Root cause
Not yet confirmed by execution (found by reading; a skill is agent instructions). Hypothesis: the 3.10 rewrite changed impl's end state to `review` but left the pre-3.10 words `pending`/`completed` in the selection and dependency rules.

### Fix
Planned in wave1-hardening, together with the F-06 spec revision (who moves leaves to `done`).

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:34 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D7 N-08; raised to high with C-02/I-12 |

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
