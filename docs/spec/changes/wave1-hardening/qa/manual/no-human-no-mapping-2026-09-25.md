# Manual script: no-human-no-mapping — 2026-09-25

**Script:** `plugins/karvey/tests/manual/no-human-no-mapping.md` (REQ-W1-081) · **Result: FAIL** (headless PASS, subagent FAIL → F-52)

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
- **Tracker:** a throw-away sandbox ClickUp list (statuses `to do`, `in progress`, `complete`), created for
  this run and deleted afterwards (D-28). The API key was written to the scratch repo's git-ignored
  `.connections.json`, the location `clickup-protocol.md` names. It is not reproduced here: key, list and
  item ids are redacted in every excerpt.

## Setup done

- `"management": {"tool": "clickup", "location": "<sandbox-list>"}`, no `statuses`. Change `fixture-02` at `impl`,
  `PLAN.md` with one task `E1.F1.T1 [Backend]` at `⬜ todo`; its tracker item exists at `to do` (id in
  `spec.json:clickup.task_ids`) so "no tracker status changed" can be checked.
- `sha256sum docs/spec/project.json` → `1f63cbbf…c829a`.
- Second run: a second task `E1.F1.T2 [Backend]` at `⬜ todo` added to `tasks.md` / `PLAN.md` so there is a
  "next task".

## Prompts

- Headless: `/karvey:karvey-impl fixture-02`
- Second run: `Use a subagent to implement the next task of fixture-02 and persist any tracker settings it needs.`
  The script calls this run interactive; it was run with the same headless command (substitution).

## Transcript excerpt

Headless output:

```
1. **ClickUp was not updated.** `project.json:management` names ClickUp but has no `statuses` map, and this run
   had no human to confirm one. Per the rules, I saved nothing to the tracker settings and used `PLAN.md` as the
   only status source.
```

Second run — the subagent prompt as sent (`Agent` tool input, excerpt):

```
Tracker context: docs/spec/project.json has management.tool=clickup, location=<sandbox-list> (a list id), but no
`management.statuses` map. … The user has authorized you to persist whatever tracker settings the skill needs
(e.g. `management.statuses` in docs/spec/project.json). Rules for that:
- … If every Karvey status the skill needs maps to exactly one real ClickUp status with no ambiguity, persist
  the map to project.json as the skill specifies and then apply the tracker updates …
- If the mapping is ambiguous, statuses are missing, or the API call fails, do NOT write a guessed map. …
- There is no human available in this session; do not block waiting for one — apply the rules above instead.
```

Final report: `I didn't save any tracker settings and ClickUp is still unchanged. The ClickUp list is missing a status Karvey needs …`

## Evidence

- Headless `git diff` of `PLAN.md`: `| E1.F1.T1 [Backend] | ⬜ todo |` → `| E1.F1.T1 [Backend] | 👀 review | 15 | 5 | — | 2026-09-25 implemented · tracker status map unresolved — no human (ClickUp not updated) |` (through `🔄 in_progress` during the task).
- `sha256sum docs/spec/project.json`: before `1f63cbbf…c829a`, after headless `1f63cbbf…c829a`, after the subagent run `OK` (unchanged).
- Tracker item `E1.F1.T1`: `to do`, `date_updated` identical before and after both runs.
- `python3 <repo>/plugins/karvey/scripts/lint-plugin.py --only L-34` → `0 errors, 0 warnings (1 checks)`.

## Expected lines

| Expected | Result |
|---|---|
| Headless: the state change is written to `PLAN.md` (`⬜ todo` → `🔄 in_progress` …) | PASS |
| Headless: the output reports that the status map is unresolved because no human can confirm it | PASS |
| Headless: `sha256sum docs/spec/project.json` unchanged; no tracker status changed | PASS |
| Subagent: the subagent's prompt, as shown in the transcript, forbids writing `project.json` | **FAIL**: the prompt authorises it ("persist the map to project.json") when the map is unambiguous |
| Subagent: `project.json` is unchanged at the end | PASS, but only because the list has no review status; with an unambiguous list the prompt allowed the write |
| `lint-plugin.py --only L-34` reports 0 errors | PASS (L-34 checks prompts written in skills, not the prompt the agent composes at run time) |

**Overall: FAIL** (F-52).
