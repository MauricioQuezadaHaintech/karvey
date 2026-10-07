# Manual script `tests/manual/upgrade-skill.md` — run 2026-09-25

- **Executed by:** maintainer agent, headless under D-21 (E1.F8.T2), 13:32–13:36 UTC.
- **Runtime:** `claude -p --plugin-dir <worktree>/plugins/karvey --setting-sources project,local` (CLI 2.1.282),
  `HOME` = a copy of `tests/fixtures/upgrade/fake-home` under the scratch dir `$SCR`.
- **Setup:** exactly the script's: `$SCR/up/proj` from `tests/fixtures/upgrade/legacy-project`, `git init -b dev`,
  one commit, bare origin `$SCR/up/origin.git`, `dev` pushed; reference `$SCR/up/plan.json` =
  `schema-migrate` applies, `legacy-shims` applies, `team-settings` applies, `enforcement-defaults` applies,
  `statusline-launcher` human, `changes-in-flight` report (`schema-migrate-proposed`, `global-config` nothing).
- A headless session has no AskUserQuestion; the agent asks in text and the answer is sent with `--resume`.

| Case | Prompt | Observed | Status |
|---|---|---|---|
| 1 — the table is the tool's rows (027) | `/karvey:karvey-upgrade` | 6 rows = the 6 non-`nothing` rows of `plan.json`, same order and summaries; satisfied steps on one line; the three low-risk writable steps Recommended, `legacy-shims` not; `statusline-launcher`, `changes-in-flight` "shown, not applied". `git status --porcelain` empty, no upgrade branch, `seen --show` → none | ✅ PASS |
| 2 — the tool is missing (027 error) | `/karvey:karvey-upgrade` with a plugin copy without `scripts/karvey-upgrade.py` | `karvey-upgrade.py not found in this plugin: stop, nothing is done by hand`; the agent says the tool is not in this install and stops; tree clean, no branch | ✅ PASS |
| 3 — picks none (028 error) | resume Case 1: "none" | `seen --decline` → `recorded: declined 3.11.4`; no `chore/karvey-upgrade-*` branch, still 1 commit; the startup hook in the same clone prints no `Karvey (upgrade)` line. The agent said "the offer will come back next session" — wrong, it comes back with the next version (F-07, skill text fixed) | ✅ PASS (F-07) |
| 4 — invocable when resolved (029) | `seen --accept`, then a new session with `/karvey:karvey-upgrade` | the startup context has only the settings notice (no offer); the skill shows the same 6 rows as Case 1 and stops at the pick question. The plan header read `3.11.4 → 3.11.4` (F-05, fixed) | ✅ PASS (F-05) |
| 5 — not a Karvey project (029 error) | `/karvey:karvey-upgrade` in `$SCR/plain` (`git init -b main`) | startup context empty; `plan --json` exit 3 `not a Karvey project (no docs/spec/project.json or docs/spec/changes/) … nothing written`; the agent relays it and stops; no `docs/spec/`, no `.git/karvey/` | ✅ PASS |
| 6 — headless run (028) | `claude -p … "/karvey:karvey-upgrade"` in `$SCR/up/proj` (the Case 1 run) | the plan table is shown; the agent cannot ask with the tool, asks in text and stops; `seen --show` → no record, no branch, no commit | ✅ PASS |

**Result: 6/6 PASS.** Findings logged in `../../findings.md`: F-05, F-07.
