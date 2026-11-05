# Manual script: find-or-create — 2026-09-25

**Script:** `plugins/karvey/tests/manual/find-or-create.md` (REQ-W1-089) · **Result: PASS**

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

- `project.json`: `management {tool: clickup, location: <sandbox-list>, statuses: {todo: "to do", in_progress: "in progress", review: "complete", done: "complete", blocked: null}}`.
- Change `fixture-06` at phase `tasks` (`tasks.md` generated, not yet approved). The items a previous
  `karvey-tasks` run would have created were created in the list: `E1 …`, `E1.F1 …`, `E1.F1.T1 …`,
  `E1.F1.T2 …`, `E1.F1.T3 …`, their ids written to `spec.json:clickup` (`epic_id`, `feature_ids`, `task_ids`).
- `jq -S .clickup docs/spec/changes/fixture-06/spec.json > "$SCRATCH/ids-before.json"`; list item count **5**.
- Variant B: a second item named exactly `E1.F1.T1 [DB] Table heartbeat and insert SP` created by hand
  (count **6**).

## Prompts

- A: `/karvey:karvey-tasks fixture-06` → resumed with `Aprobado. Approver: Fixture Tester, ref D-02. Leave feature_ids as it is.`
- B (new session): `/karvey:karvey-tasks fixture-06`

## Transcript excerpt

A, turn 1 (read-only check before any create; the agent read each stored id and listed the list by name):

```
**ClickUp check (read-only, list `<sandbox-list>`)**
| Key | ClickUp id | Found | Status | Estimate | Dependencies |
| E1 (Epic) | <item> | ✅ one | to do | — | ❌ none |
| E1.F1 | <item> | ✅ one | to do | — | ❌ none |
| E1.F1.T1 [DB] | <item> | ✅ one | to do | ❌ null | — |
| E1.F1.T2 [Backend] | <item> | ✅ one | to do | ❌ null | ❌ none (should wait on T1) |
| E1.F1.T3 [Test] | <item> | ✅ one | to do | ❌ null | ❌ none (should wait on T2) |
… Once you approve, I'll fill in only what's missing and create nothing new
```

A, turn 2: `**ClickUp:** I created nothing new. The 3 tasks already existed, so I filled in what the earlier run left out` (estimates and dependencies only).

B:

```
I've stopped before creating or changing anything, because ClickUp has two tasks with the same key and the
method's rules say to ask you which one is the real one.
**Two tasks are named `E1.F1.T1 [DB] Table heartbeat and insert SP`:** | `<item>` | … | ✅ in spec.json | `<item>` | … | ❌ |
**Which one should be canonical?** I recommend keeping … I won't do it unless you tell me to.
```

## Evidence

| Measure | Before | After |
|---|---|---|
| A: list item count | 5 | 5 |
| A: `diff ids-before.json <(jq -S .clickup …)` | — | empty (equal) |
| B: list item count | 6 (with the duplicate) | 6 |
| B: `diff` of the id dumps | — | empty (equal) |

## Expected lines

| Expected | Result |
|---|---|
| A: the agent searches for each natural key (`E1`, `E1.F1`, `E1.F1.T1`, …) before creating | PASS: read-only lookup of every key (stored ids + list by name) before any write |
| A: no new item is created; the list's item count is unchanged | PASS: 5 → 5 |
| A: `jq -S .clickup …` equals `ids-before.json` | PASS: diff empty |
| B: the agent stops at the duplicated key and asks which item is canonical | PASS: question printed above |
| B: it creates nothing for that key | PASS: 6 → 6, ids unchanged |

**Overall: PASS.** Observation (not an Expected line): the agent flagged that `spec.json:clickup.feature_ids` is
an array in `spec.schema.json`, so a Feature id loses its natural key (logged as F-54).
