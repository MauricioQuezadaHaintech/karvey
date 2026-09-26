# Manual script: missing-status-map — 2026-09-25

**Script:** `plugins/karvey/tests/manual/missing-status-map.md` (REQ-W1-080) · **Result: PASS** (with a headless note)

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

- Variant A: `project.json` with `branch_flow {integration: dev, production: main}` and
  `"management": {"tool": "clickup", "location": "<sandbox-list>"}`, **no** `statuses`. Change `fixture-01`
  with requirements and architecture approved (state tool), infra skipped; on `dev`, pushed.
  (A first attempt stopped at the tasks gate because the fixture had not recorded the architecture approval;
  discarded as a fixture error.)
- Variant B: new repo, `"management": {"tool": "jira"}` with **no** `location`; change `fixture-01` at `impl`,
  `PLAN.md` with two `⬜ todo` tasks, on `feature/fixture-01`.

## Prompts

- A: `/karvey:karvey-tasks fixture-01`, then resumed three times: (1) `I am the human owner and I am here to
  answer: read the list's real statuses, propose the status map and I will confirm it. The tasks are approved
  (aprobado), approver Fixture Tester, ref D-02 — use ClickUp once the map is confirmed.` (2) `Confirmed map:
  todo 'to do', in_progress 'in progress', review 'in progress', done 'complete', blocked null (unsupported:
  keep the status and add a comment). Persist it and create the tasks in ClickUp in this run with the confirmed
  map.` (3) `Yes, create the Epic and the Feature now and then the queued tasks.`
- B: `/karvey:karvey-impl fixture-01`

## Transcript excerpt

A, turn 1 (headless, no human yet):

```
TOOL Bash: … python3 "$C" resolve management --change fixture-01 --json …
Status map missing. I must apply the missing-map clause of management-adapters.md.
**Status map unresolved — no human.** … This session is non-interactive, so nobody could confirm. As the rule
requires, I saved nothing and am using `PLAN.md` in place of ClickUp for this run. No ClickUp tasks or statuses
were created or changed.
```

A, turn 2 (human declared present):

```
TOOL Bash: curl … https://api.clickup.com/api/v2/list/<sandbox-list> …   (reads the list's statuses)
| 0 | `to do` | open | 1 | `in progress` | custom | 2 | `complete` | closed |
**Proposed status map:** todo `to do` · in_progress `in progress` · done `complete` · review **no match** · blocked **no match**
… Nothing is saved to the status map yet, and nothing has been created in ClickUp.
```

A, turn 3: `**Status map** — committed as <sha> on branch docs/fixture-01-status-map, not merged into dev yet … The
method applies it once that branch is merged`; the task creations were queued in the outbox because the Epic
and Feature did not exist in the list. Turn 4 created Epic, Feature and the 4 tasks (`to do`).

B:

```
`karvey-config.py resolve management` says the tracker is Jira (`external: true`), but two settings are missing:
`location` and `statuses`. … The rule for this case is to ask for the location and change no status until it's set.
1. **Give me the Jira details:** the project key; the Jira status names …
```

## Evidence

A — `git diff dev docs/fixture-01-status-map -- docs/spec/project.json`:

```
-    "location": "<sandbox-list>"
+    "location": "<sandbox-list>",
+    "statuses": {
+      "todo": "to do",
+      "in_progress": "in progress",
+      "review": "in progress",
+      "done": "complete",
+      "blocked": null
+    }
```

`git log -1 --format=%D docs/fixture-01-status-map` → `docs/fixture-01-status-map` (not `dev`, which stayed at
its fixture commit). The first tracker create call came after the commit of the map (turns 3–4).

B — the question as printed (above); `sha256sum -c` of `PLAN.md` → `OK` (unchanged); no Jira exists, so there
is no tracker activity to show; the transcript has no status write of any kind.

## Expected lines

| Expected | Result |
|---|---|
| A: before creating any task the agent runs `karvey-config.py resolve management` | PASS |
| A: reads the list's real statuses from the tool | PASS (turn 2) |
| A: shows a proposed map for `todo · in_progress · review · done · blocked` and asks to confirm | PASS (turn 2) |
| A: after confirmation `project.json` gains `management.statuses` with exactly the confirmed values, and only then is the first task created | PASS |
| A: the persisted map is committed on a feature or docs branch, not on the integration branch | PASS: `docs/fixture-01-status-map` |
| B: the agent asks for the Jira project key and changes **no** status while waiting | PASS |
| B: it never picks a project by itself | PASS |

**Overall: PASS.** Headless note: run headless, turn 1 found no human and applied the no-human clause
(REQ-W1-081: nothing persisted, `PLAN.md`, reported). That is the correct behaviour for a headless run, but
it means the confirm flow the script describes only started once the resume said a human was present.
