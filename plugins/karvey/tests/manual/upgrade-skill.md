# upgrade skill: relays the tool, one pick, decline without a branch, any time (REQ-UP-027..029)

> Manual agent-behaviour script (project-upgrade architecture §6.4, E1.F6.T2). Run it in a real session started
> with the branch plugin, `claude --plugin-dir <this repo>/plugins/karvey`, inside a throw-away clone under
> `$SCR` (the session's scratch directory), never in this repo or the user's home. A headless run is allowed
> (`claude -p` with the same `--plugin-dir`) for the cases that ask no question. It FAILS if any line under
> **Expected:** is not observed: file the evidence under `docs/spec/changes/project-upgrade/qa/manual/upgrade-skill-<date>.md`
> with PASS/FAIL per case and log a failure as a finding; never edit the script to match what happened.

## Setup
- `mkdir -p "$SCR/up" && cp -R <this repo>/plugins/karvey/tests/fixtures/upgrade/legacy-project "$SCR/up/proj"`,
  then in `$SCR/up/proj`: `git init -q -b dev && git add -A && git commit -qm fixture`, and a bare origin
  (`git init -q --bare "$SCR/up/origin.git" && git remote add origin "$SCR/up/origin.git" && git push -q origin dev`).
- `UP=<this repo>/plugins/karvey/scripts/karvey-upgrade.py`; keep `python3 "$UP" plan --json` of this clone as the
  reference output (`$SCR/up/plan.json`).
- Between cases, reset the clone: `git checkout -q dev && git reset -q --hard && git clean -qfd` and remove the
  upgrade branch if a case created it (`git branch -D chore/karvey-upgrade-<version>`).

## Case 1 — the table is the tool's rows (REQ-UP-027)
**Prompt:** `/karvey:karvey-upgrade`, and stop at the pick question (answer nothing yet).

**Expected:**
- The table shows exactly the steps of `$SCR/up/plan.json` whose `status` is not `nothing`, in the same order,
  with the same summaries; no step is added, merged or dropped by the agent.
- Human and report steps (`statusline-launcher`, `global-config`, `changes-in-flight` when listed) are labelled
  "shown, not applied"; the low-risk writable steps are marked recommended; `schema-migrate-proposed` and
  `legacy-shims` are not recommended.
- No file of the clone changed (`git status --porcelain` is empty) and no branch was created.

## Case 2 — the tool is missing: stop (REQ-UP-027 error)
**Setup:** start the session with a copy of the plugin where `scripts/karvey-upgrade.py` was deleted
(`cp -R <this repo>/plugins/karvey "$SCR/plugin-copy" && rm "$SCR/plugin-copy/scripts/karvey-upgrade.py"`,
`claude --plugin-dir "$SCR/plugin-copy"`).

**Prompt:** `/karvey:karvey-upgrade`.

**Expected:**
- The agent says the upgrade tool is not in this install and stops.
- It does not migrate, delete or edit any file by hand: `git status --porcelain` is empty.

## Case 3 — the person picks none: decline, no branch (REQ-UP-028 error)
**Prompt:** `/karvey:karvey-upgrade`, and at the pick question select no step.

**Expected:**
- The agent runs `karvey-upgrade.py seen --decline`; `python3 "$UP" seen --show` reports `declined <version>`.
- No upgrade branch exists (`git branch --list 'chore/karvey-upgrade-*'` is empty) and there is no new commit.
- A new session in the same clone shows no upgrade offer for this version.

## Case 4 — invocable with the version already resolved (REQ-UP-029)
**Setup:** `python3 "$UP" seen --accept` (the clone has resolved the installed version).

**Prompt:** start a new session (no offer is expected), then `/karvey:karvey-upgrade`.

**Expected:**
- The session start shows no `Karvey (upgrade)` line.
- The skill still computes and shows the same table as Case 1: it behaves the same with or without an offer.

## Case 5 — not a Karvey project: stop without writing (REQ-UP-029 error)
**Setup:** `mkdir -p "$SCR/plain" && git -C "$SCR/plain" init -q -b main` and start the session there.

**Prompt:** `/karvey:karvey-upgrade`.

**Expected:**
- The agent relays "not a Karvey project" (the tool's exit 3) and stops.
- Nothing is written: no `docs/spec/`, and no `karvey/` directory under `$SCR/plain/.git`.

## Case 6 — headless run in the throw-away clone (REQ-UP-028)
**Prompt:** `claude -p --plugin-dir <this repo>/plugins/karvey "/karvey:karvey-upgrade"` in `$SCR/up/proj`.

**Expected:**
- The run shows the plan table and, since it cannot ask, records nothing: `python3 "$UP" seen --show` still
  reports no record, and no branch or commit exists.

## Evidence
- The transcript of each case, `$SCR/up/plan.json`, `git status --porcelain`, `git branch --list` and
  `python3 "$UP" seen --show` after each case, filed as described above.
