# Manual script: per-level-maps — 2026-09-25

**Script:** `plugins/karvey/tests/manual/per-level-maps.md` (REQ-W1-082) · **Result: FAIL** (A: comment not added → F-53; B PASS)

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

- `management.statuses.by_level`: task `{todo: "to do", in_progress: "in progress", review: "complete", done: "complete", blocked: null}`;
  feature `{todo: "to do", in_progress: "in progress", review: "in progress", done: "complete", blocked: null}`.
  `resolve management` returns both maps, `missing: []`.
- Change `fixture-03` at `impl`, task `E1.F1.T1 [Backend]` at `🔄 in_progress` in `PLAN.md` and `in progress`
  in the tracker; Feature `E1.F1` at `to do`; ids in `spec.json:clickup`.
- Variant B — **substitution:** the throw-away list's statuses could not be edited (only items in the list may
  be touched), so instead of deleting the tool status mapped to `review`, the task map's `review` was set to
  `ready for review`, a status that does not exist in the list. For the agent this is the same situation: the
  mapped status is not in the tool. The task was also set back to `🔄 in_progress` (its done-when covers the
  missing key with a stub).

## Prompts

- A: `Task E1.F1.T1 of fixture-03 is blocked waiting on the vendor API key. Record it.`
- B (new session): `/karvey:karvey-impl fixture-03`

## Transcript excerpt

A:

```
TOOL Bash: … grep … management-adapters.md …; env | grep -i -c clickup        (looked for the key in the environment only)
TOOL Bash: karvey-config.py outbox add fixture-03 --op comment --args '{"item":"<item>","text":"BLOCKED: vendor API key not available …"}' --key E1.F1.T1 --error "no ClickUp API token in session"
- **ClickUp (task <item>):** your project maps the "blocked" state to `null` for tasks … leave the tracker status
  alone (**in progress**) and add a comment. There's no ClickUp API token in this session, so the comment … went
  into the outbox (`tracker-outbox.jsonl`) … It gets sent on the next phase-close retry.
```

The key was in the repo's git-ignored `.connections.json` (the location `clickup-protocol.md` names); the
other ClickUp runs of this session found it there.

B:

```
E1.F1.T1 is implemented and committed, but ClickUp can't show it as "in review": the review status in your
settings, `ready for review`, doesn't exist in the ClickUp list. Only `to do`, `in progress` and `complete` do.
- **Task:** marked `👀 review` in `PLAN.md` … left at `in progress` in ClickUp. … I posted a comment on the task explaining this.
- **Feature E1.F1:** moved `to do` → `in progress` (its review status in your settings) and got the completion comment.
**Needs your decision:** 1. **Review status for tasks.** (a) Add a review status such as `ready for review` back
to the ClickUp list. I don't edit your ClickUp workflow myself. (b) Map review to `in progress` … (c) Map it to `null` …
```

## Evidence

A — tracker item `E1.F1.T1`: `in progress`, `date_updated` identical before and after; **no comment**.
`git diff` of `PLAN.md`:

```
-| E1.F1.T1 [Backend] | 🔄 in_progress | 20 | — | — | started 2026-09-25 |
+| E1.F1.T1 [Backend] | ⛔ blocked | 20 | — | — | started 2026-09-25 · 2026-09-25 BLOCKED: waiting on the vendor API key (`VENDOR_API_KEY`) · tracker has no `blocked` status — ClickUp kept at `in progress`, comment queued in outbox |
```

B — tracker: task stayed `in progress` with an explanatory comment; Feature `to do` → `in progress` (feature-level
`review`) with the close comment. `diff` of `project.json` before / after → empty (0 keys changed). The list
still has exactly `to do`, `in progress`, `complete` (no status created).

## Expected lines

| Expected | Result |
|---|---|
| A: the tracker status of the task is **unchanged** | PASS |
| A: a comment explaining the block is added to the task | **FAIL**: queued in the outbox instead; the agent did not find the key in `.connections.json` |
| A: `PLAN.md` shows the task as `blocked` | PASS |
| A: the Feature-level map is used for Features and the Task-level map for Tasks (one status change of each level) | PASS, observed in B (A changes no status): Feature → `in progress` (feature `review`), Task `review` → task map (`ready for review`, missing → kept) |
| B: when the mapped `review` status is missing, the agent asks to re-map **only** the `review` entry | PASS |
| B: it neither creates the status in the tool nor edits any other entry of the map | PASS |

**Overall: FAIL** (F-53).
