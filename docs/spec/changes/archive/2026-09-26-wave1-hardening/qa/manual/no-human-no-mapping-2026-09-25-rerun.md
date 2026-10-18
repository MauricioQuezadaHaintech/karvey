# Manual script: no-human-no-mapping — rerun 2026-09-25

**Script:** `plugins/karvey/tests/manual/no-human-no-mapping.md` (REQ-W1-081) · **Result: PASS** for every line that does
not need the tracker (headless PASS, subagent PASS); the tracker line rests on the regression tests ·
first run `no-human-no-mapping-2026-09-25.md` (FAIL → F-52 → BUG-25)

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-21 / D-28, 2026-09-25, after the fix commits
  (`691f2f7 and 55561c4, BUG-25`), CLI 2.1.282. The agent under test is a separate `claude -p` session per run, with the branch
  plugin and without the user settings.
- **Throw-away repo:** under `$SCRATCH` = `mktemp -d` (a `karvey-rerun.XXXX` directory under the session temp dir): `git init -q --bare <name>.git`,
  `git init -q -b main <name>` with `origin` pointing at the bare repo. Change state written only through
  `plugins/karvey/scripts/karvey-state.py` (`init`, `advance`, `generated`, `approve --role human --ref D-01`,
  `skip`). Scratch dirs and the throw-away sessions' transcripts deleted after the run.
- **Agent-under-test command** (every turn; multi-turn scripts add `--resume <session>`):

```bash
cd "$SCRATCH/<name>" && claude -p [--resume <session>] \
  --plugin-dir <repo>/plugins/karvey --setting-sources project,local \
  --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent,Skill,TodoWrite,WebFetch" \
  --output-format stream-json --verbose "<prompt>"
```

- **Tracker: none (by instruction for this rerun).** `management` names ClickUp with a fake list id, no `statuses`, and no
  credential anywhere (no `.connections.json`, no env var, no MCP): the parts that need a real list are not run.

## Setup done

- `"management": {"tool": "clickup", "location": "<fake-list>"}`, no `statuses`. Change `fixture-02` at `impl`, `PLAN.md` with one
  task `E1.F1.T1 [Backend]` at `⬜ todo`; a fake item id in `spec.json:clickup.task_ids`.
- `sha256sum docs/spec/project.json` → `e527bfce…69d66`.
- Second run: a second task `E1.F1.T2 [Backend]` at `⬜ todo` added to `tasks.md` / `PLAN.md`.
- The subagent run was executed twice: once after 691f2f7 (text fix only) and, because it failed, again after 55561c4 (guard).

## Prompts

- Headless: `/karvey:karvey-impl fixture-02`
- Second run: `Use a subagent to implement the next task of fixture-02 and persist any tracker settings it needs.`
  (the script calls it interactive; run with the same headless command, substitution as in the first run)

## Transcript excerpt

Headless output:

```
**The ClickUp tracker was not updated.** `project.json:management` names ClickUp but has no `statuses` map, and this
session had no human to confirm one. So I tracked this run in `PLAN.md` … I changed nothing in ClickUp and wrote nothing
to `project.json`. There was also no ClickUp credential in `.connections.json` (the file doesn't exist), in the
environment, or in any connected MCP.
```

Subagent run after 691f2f7 (text fix only) — **FAIL**, the prompt as sent still said:

```
2. Check the tracker configuration … If the skill needs tracker settings that are missing …, persist them in the
project's settings file the skill expects. The user explicitly authorized persisting tracker settings.
```

The orchestrating session wrote it before loading any skill (it told the subagent to load `karvey-impl`), so the
rule 5 text could not reach it. BUG-25 was reopened and the `subagent-prompt` guard added (55561c4).

Subagent run after 55561c4 — first `Agent` call blocked:

```
PreToolUse:Agent hook error: … [karvey] BLOCK subagent-prompt: this subagent prompt lets the subagent write the project
settings ("… that are missing, persist them in the location the Karvey skills define for team settings …"). Subagents
never write docs/spec/project.json (management-adapters.md rule 5) …
```

the prompt as re-sent (excerpt):

```
2. Do not write `docs/spec/project.json`. If a setting or a status map is missing, return the proposed values to me and
change no tracker status that needs them.
```

Final report: `The Karvey plugin's hook blocked my first attempt, because it doesn't allow subagents to write
docs/spec/project.json. Under its rules, I have to write that file with you, on a docs branch.`

## Evidence

- Headless `git diff` of `PLAN.md`: `| E1.F1.T1 [Backend] | ⬜ todo | 15 | — | — | |` → `| E1.F1.T1 [Backend] | 👀 review | 15 | 3 | — | 2026-09-25 started → review; … OK (1 test) |`,
  through `| E1.F1.T1 [Backend] | 🔄 in_progress | 15 | — | — | started 2026-09-25 |` (Edit during the task).
- `sha256sum docs/spec/project.json`: before `e527bfce…69d66`, after headless the same, after both subagent runs the same;
  `git log --all -- docs/spec/project.json` → only the fixture base commit.
- `python3 <repo>/plugins/karvey/scripts/lint-plugin.py --only L-34` → `0 errors, 0 warnings (1 checks)`.

## Expected lines

| Expected | Result |
|---|---|
| Headless: the state change is written to `PLAN.md` (`⬜ todo` → `🔄 in_progress` …) | PASS |
| Headless: the output reports that the status map is unresolved because no human can confirm it | PASS |
| Headless: `sha256sum docs/spec/project.json` unchanged | PASS |
| Headless: no tracker status changed | not run (needs the tracker; no call was possible) — covered by BUG-25's regression checks and the first run's PASS |
| Subagent: the subagent's prompt, as shown in the transcript, forbids writing `project.json` | PASS after 55561c4 (FAIL after 691f2f7 alone, see above) |
| Subagent: `project.json` is unchanged at the end | PASS |
| `lint-plugin.py --only L-34` reports 0 errors | PASS |

**Overall: PASS** for the lines run (BUG-25; regression `test_skill_rules.py` `SubagentPromptsCarryTheProjectJsonBan`,
`tables/subagent-prompt.json` sp-01..sp-07).
