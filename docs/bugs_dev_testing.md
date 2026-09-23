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
- **Current state:** DIAGNOSTICADO

### Reproduction
A repo whose `project.json` has `"management": "markdown"` (15 HainTech repos; `"clickup"` in qcheck-v3). Route a finding with karvey-iterate or add a backlog item.

### Actual vs expected
- Actual: `project.json:management.tool` is undefined on a string; "undefined != markdown" is true, so a Markdown-only repo is sent to "create/link the item in the tracker". init Step 3.2 re-asks from zero and does not offer the known ClickUp list.
- Expected: a legacy string is read as `{"tool": "<string>"}` (and `project.json:clickup.backlog_list_id` as `location`), init pre-fills and confirms, and the guards test "a tracker tool is resolved and it is not markdown".

### Root cause
The pre-3.10 schema never defined `project.json:management`; sessions added it ad hoc as a string. 3.10 reused the key as an object with no migration; the compatibility text in management-adapters.md describes a state project.json never had (the string lived in spec.json).

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:28 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D4 I-02, D3 C-03 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | 16 files measured; schema collision confirmed against ffb6df9 project-config.md |

## BUG-07 — README and plugin.json still describe ClickUp as the tracker
- **Priority:** medium
- **Detected:** 2026-09-23 · **Component:** README.md:52,117-119; plugins/karvey/.claude-plugin/plugin.json:4
- **Change / origin:** team-adapters (F-09; sources C-05, C-06)
- **Tracker:** —
- **Current state:** DIAGNOSTICADO

### Reproduction
Read README:52 ("Epic (ClickUp) or PLAN.md"), :117-119 and the plugin.json description ("discovery backlog (Markdown + ClickUp)").

### Actual vs expected
- Actual: public text says ClickUp; README:95-99 and the rules say "the team's tracker".
- Expected: "the team's tracker" everywhere.

### Root cause
The 3.10 sweep replaced ClickUp wording in skills and rules but not in README and plugin.json.

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:28 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D3 C-05/C-06 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | lines located |

## BUG-08 — An invalid `KARVEY_TZ` silently falls back to the system zone
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-statusline.sh (`_reset`, zone lookup)
- **Change / origin:** team-adapters (F-22; sources S-04 = E-05)
- **Tracker:** —
- **Current state:** DIAGNOSTICADO

### Reproduction
`KARVEY_TZ=Mars/Olympus` (or a typo) and a valid `resets_at`.

### Actual vs expected
- Actual: the system-zone time with no hint (still true after hotfix 3.11.2).
- Expected: fallback with a visible marker, e.g. `↻18:52 (TZ?)`; the zone computed once.

### Root cause
`except Exception: tz = None` with no signal. Security side verified: `zoneinfo` rejects traversal; the value never reaches a shell.

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:24 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D1 S-04, D2 E-05 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | silent except branch |

## BUG-09 — Stray separator when only the 7-day window is present
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/karvey-statusline.sh (limit line)
- **Change / origin:** team-adapters (F-23; source E-06)
- **Tracker:** —
- **Current state:** DIAGNOSTICADO

### Reproduction
`rate_limits` with only `seven_day`.

### Actual vs expected
- Actual: `limit · 7d 29% ↻Thu 17:23 (1d0h)`.
- Expected: `limit 7d 29% ...`.

### Root cause
The ` · ` prefix is hard-coded on the 7-day part instead of joining the present windows.

### Fix
Planned in wave1-hardening (collect the parts and `' · '.join`).

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-06 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | still present after hotfix 3.11.2 |

## BUG-10 — `docs/karvey.html`: a malformed hash throws `URIError` before the language switch binds
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (`mapHash`, `decodeURIComponent`)
- **Change / origin:** team-adapters (F-24; sources S-07 = E-15)
- **Tracker:** —
- **Current state:** DIAGNOSTICADO

### Reproduction
Open `karvey.html?lang=es#%E0%A4%A`, then click DE.

### Actual vs expected
- Actual: `Uncaught URIError: URI malformed`; the switcher handlers are never attached; the click falls back to a full reload and the section is lost. No XSS.
- Expected: a malformed hash is ignored.

### Root cause
`decodeURIComponent` without `try/catch`, called before `switcher.forEach`.

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:24 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D1 S-07, D2 E-15 (reproduced in node / jsdom) |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | unguarded decode |

## BUG-11 — An invalid `?lang=` saves the browser language as the viewer's choice
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (main script `remember` test vs early pick)
- **Change / origin:** team-adapters (F-25; source E-14)
- **Tracker:** —
- **Current state:** DIAGNOSTICADO

### Reproduction
jsdom with `?lang=xx` and navigator `es`; `?lang=es-CL` and navigator `de`.

### Actual vs expected
- Actual: es / de shown and saved to `localStorage['karvey-lang']`, a language the viewer never chose; `es-CL` ignored silently.
- Expected: remember only a valid URL value; optionally accept `xx-YY` by its first 2 letters in both scripts.

### Root cause
The main script's `/[?&]lang=/` is looser than the early script's `[a-zA-Z]{2}(?:&|$)`.

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-14 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | regex mismatch between the two scripts |

## BUG-12 — Switching language drops the other query parameters
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (switcher `replaceState`)
- **Change / origin:** team-adapters (F-26; source E-16)
- **Tracker:** —
- **Current state:** DIAGNOSTICADO

### Reproduction
Open `?foo=1&lang=es`, click DE.

### Actual vs expected
- Actual: URL becomes `?lang=de`.
- Expected: `?foo=1&lang=de`.

### Root cause
The URL is rebuilt as `'?lang=' + req` instead of editing `URLSearchParams`.

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-16 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | query string rebuilt from scratch |

## BUG-13 — No `hashchange` handling on the method page
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (hash mapping at load only)
- **Change / origin:** team-adapters (F-27; source E-18)
- **Tracker:** —
- **Current state:** DIAGNOSTICADO

### Reproduction
With es shown, paste or click `#en-foo` in the same document.

### Actual vs expected
- Actual: no scroll; the target is in a hidden block.
- Expected: the same `mapHash` + `replaceState` + jump logic as at load.

### Root cause
The mapping runs only once at load; there is no `hashchange` listener.

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-18 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | missing listener |

## BUG-14 — Without JS the language switch is shown but does nothing
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** docs/karvey.html (CSS blocks ~105-112, switch links ~309-315)
- **Change / origin:** team-adapters (F-28; source N-12)
- **Tracker:** —
- **Current state:** DIAGNOSTICADO

### Reproduction
Disable JavaScript, click ES.

### Actual vs expected
- Actual: reloads with `?lang=es`, still English, EN still marked current.
- Expected: the control hidden without JS (`html:not([data-lang]) .langs{display:none}`) or a `<noscript>` note. English without JS (REQ-ADP-031) is already met.

### Root cause
Language selection depends on JS setting `data-lang`; the links are always rendered.

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:34 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D7 N-12 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | control rendered without its JS dependency |

## BUG-15 — `clickup-sync-guard` hook referenced but nothing installs it
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/skills/karvey/rules/phase-close.md:41
- **Change / origin:** team-adapters (F-29; source C-10)
- **Tracker:** —
- **Current state:** DIAGNOSTICADO

### Reproduction
Read phase-close.md:41; `karvey-guard` manages only git-flow and plan-gate; `hooks/` has no such script.

### Actual vs expected
- Actual: the rule promises a hook that does not exist (the diff edited the line to add "tracker-agnostic" instead of resolving it).
- Expected: rename to `tracker-sync-guard` and mark it described-only, or drop the sentence.

### Root cause
Leftover reference to a planned hook.

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:28 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D3 C-10 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | no installer anywhere in the plugin |

## BUG-16 — hooks/README says the session hook prints nothing without team/agent files
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** plugins/karvey/hooks/README.md:18-19
- **Change / origin:** team-adapters (F-30; sources C-18, E-12 README part)
- **Tracker:** —
- **Current state:** EN FIX

### Reproduction
Read hooks/README.md:18-19 ("With none of them it prints nothing and exits 0.") and run the hook in a Karvey project without settings.

### Actual vs expected
- Actual: README says nothing is printed; the hook prints the one-line settings notice. Still true after hotfix 3.11.2 (only the script header was updated).
- Expected: "...except, inside a Karvey project lacking team settings, a one-line notice."

### Root cause
The 3.10 diff touched hooks/README but not this paragraph.

### Fix
Planned in wave1-hardening.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:27 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D2 E-12, D3 C-18 |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | confirmed on the 3.11.2 working tree |
| 2026-09-23 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fixed in hotfix 3.11.2: hooks/README.md now states the Karvey-project exception; stays EN FIX until the wave1 plugin linter checks docs vs hook behaviour (no automated regression test yet) |

## BUG-17 — 3.11.1 release docs incomplete (CHANGELOG without "Why"; page history stops at 3.11.0)
- **Priority:** low
- **Detected:** 2026-09-23 · **Component:** CHANGELOG.md ([3.11.1]); docs/karvey.html (version history, 5 blocks)
- **Change / origin:** team-adapters (F-31; sources D6, C-21)
- **Tracker:** —
- **Current state:** EN FIX

### Reproduction
At e3bc6f3: the [3.11.1] CHANGELOG entry has no "Why" section (policy `changelog-policy.md`); the page is stamped v3.11.1 but its history tops at 3.11.0 with `class="now"`.

### Actual vs expected
- Actual: incomplete release documentation for 3.11.1.
- Expected: every entry with its "Why"; the page history in step with the badge.

### Root cause
No automated check ties the CHANGELOG sections and the page history to the version bump.

### Fix
Applied in the 3.11.2 working tree: "Why" added to [3.11.1] (with a note that it was added in 3.11.2); 3.11.1 and 3.11.2 entries added to the page history in the 5 languages, `class="now"` moved. Stays EN FIX: no regression check exists yet; planned with the plugin CI linter (BL-10) in wave1-hardening. This deviates from "BUG-05 onward are DETECTADO/DIAGNOSTICADO" because the fix is already in place.

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-09-23 17:28 | DETECTADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | retroactive QA D3 C-21; D6 by the orchestrator |
| 2026-09-23 17:40 | DIAGNOSTICADO | Mauricio Quezada Ibáñez / Claude Opus 5.5 | no release-doc check |
| 2026-09-23 19:01 | EN FIX | Mauricio Quezada Ibáñez / Claude Opus 5.5 | fixed in CHANGELOG.md and docs/karvey.html on hotfix/karvey-3.11.2-settings-nudge; awaiting a regression check |
