# Manual script: impl-resume — 2026-09-25

**Script:** `plugins/karvey/tests/manual/impl-resume.md` (REQ-W1-085, BUG-05) · **Result: PASS**

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-28, 2026-09-25. The agent under test is a separate
  `claude -p` session per run, with the branch plugin and without the user settings.
- **Throw-away repo:** `git init -q --bare "$SCRATCH/<name>.git"`, `git init -q -b main "$SCRATCH/<name>"` with
  `origin` pointing at the bare repo. The fixture change state was written only through
  `plugins/karvey/scripts/karvey-state.py` (`init`, `advance`, `generated`, `approve --role human --ref D-01`,
  `skip`), never by hand. `$SCRATCH` is a `mktemp -d` directory, deleted after the run.
- **Agent-under-test command** (every turn; multi-turn scripts add `--resume <session>`):

```bash
cd "$SCRATCH/<name>" && claude -p [--resume <session>] \
  --plugin-dir <repo>/plugins/karvey --setting-sources project,local \
  --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent,Skill,TodoWrite,WebFetch" \
  --output-format stream-json --verbose "<prompt>"
```

## Setup done

- Variant A: Markdown tracking. Change `fixture-05` at phase `impl`; `PLAN.md` task table:
  `E1.F1.T1 [DB]` and `E1.F1.T2 [DB]` at `👀 review`, `E1.F2.T1 [Backend]` (depends on both) at `⬜ todo`,
  `E1.F2.T2 [Backend]` at `⬜ todo`; the two `[DB]` artifacts committed; `feature/fixture-05` checked out.
- Variant B: same change in a new repo, `E1.F2.T1` at `🔄 in_progress` in `PLAN.md`; tracker configured
  (`management.tool: clickup`, status map `to do / in progress / complete / complete / null`);
  `resolve management --change fixture-05 --json` → `"external": true`. Tracker items: the two `[DB]` tasks
  at `complete` (mapped `review`), `E1.F2.T1` and `E1.F2.T2` at `to do`, ids in `spec.json:clickup`.
- **Tracker:** a throw-away sandbox ClickUp list (statuses `to do`, `in progress`, `complete`), created for
  this run and deleted afterwards (D-28). The API key was written to the scratch repo's git-ignored
  `.connections.json`, the location `clickup-protocol.md` names. It is not reproduced here: key, list and
  item ids are redacted in every excerpt.

## Prompts

- A: `/karvey:karvey-impl fixture-05`
- B (new session, new repo): `/karvey:karvey-impl fixture-05`

## Transcript excerpt

A:

```
Resuming from `PLAN.md` (management is markdown, `external: false`). E1.F1.T1/T2 are at `review` and their
SQL still verifies; next selectable is **E1.F2.T1**.
TOOL Edit PLAN.md: "| E1.F2.T1 [Backend] | ⬜ todo |" → "| E1.F2.T1 [Backend] | 🔄 in_progress |"
```

B:

```
**How I picked tasks.** The team tracks work in ClickUp, so I took task status from there rather than from `PLAN.md`.
**The two sources disagreed** when I started, and I'm reporting it rather than fixing it quietly:
- **E1.F2.T1:** `PLAN.md` had it as in progress (a previous session died partway through), but ClickUp had it
  as `to do`. Nothing had been written for it (no `app/` folder existed), so I built it from scratch.
```

## Evidence

A — `git diff` of `PLAN.md` in the first task's commit (the `🔄 in_progress` edit happened before the work,
the commit records the task at review):

```
-| E1.F2.T1 [Backend] | ⬜ todo | 15 | — | — | depends E1.F1.T1, E1.F1.T2 |
+| E1.F2.T1 [Backend] | 👀 review | 15 | 3 | — | depends E1.F1.T1, E1.F1.T2 |
+| 2026-09-25 | impl | E1.F2.T1 health() handler implemented (review) |
```

B — tracker after the run: both `[Backend]` tasks moved `to do` → `complete` (mapped `review`); `PLAN.md`
updated by the normal impl steps after the drift was reported.

## Expected lines

| Expected | Result |
|---|---|
| A: the agent says which source it reads task state from (`PLAN.md`) | PASS |
| A: treats the `[DB]` tasks at `👀 review` as satisfied dependencies and starts `E1.F2.T1 [Backend]` | PASS |
| A: it does **not** wait for the `[DB]` tasks to reach `done` | PASS |
| B: the agent declares the tracker as its source | PASS |
| B: reports the drift (`E1.F2.T1` `in_progress` in `PLAN.md`, `todo` in the tracker) | PASS |
| B: resumes from the tracker's state without silently reconciling `PLAN.md` | PASS: drift stated before the work; `PLAN.md` changed only by the task's own status steps |

**Overall: PASS.** Side note from B, a fixture artefact: the sandbox list has no review status, so the fixture
mapped `review` and `done` to the same `complete`; the agent pointed out that the Epic then looks done.
