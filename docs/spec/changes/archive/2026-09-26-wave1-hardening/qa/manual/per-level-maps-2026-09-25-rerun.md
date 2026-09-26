# Manual script: per-level-maps — rerun 2026-09-25

**Script:** `plugins/karvey/tests/manual/per-level-maps.md` (REQ-W1-082) · **Result: PASS** for the lines that do not need
the tracker; the tracker lines rest on the regression tests · first run `per-level-maps-2026-09-25.md` (FAIL → F-53 → BUG-26)

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-21 / D-28, 2026-09-25, after the fix commits
  (`7153c9f, BUG-26`), CLI 2.1.282. The agent under test is a separate `claude -p` session per run, with the branch
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

- **Tracker: none (by instruction for this rerun).** ClickUp with a fake list id and no credential in any place
  (no `.connections.json`, no env var, no MCP). Variant B needs the tool's real statuses and is not run.

## Setup done

- `management.statuses.by_level`: task `{todo: "to do", in_progress: "in progress", review: "complete", done: "complete", blocked: null}`;
  feature `{todo: "to do", in_progress: "in progress", review: "in progress", done: "complete", blocked: null}`.
  `resolve management` returns `by_level`, `missing: []`.
- Change `fixture-03` at `impl`, task `E1.F1.T1 [Backend]` at `🔄 in_progress` in `PLAN.md`; fake item ids in `spec.json:clickup`.

## Prompts

- A: `Task E1.F1.T1 of fixture-03 is blocked waiting on the vendor API key. Record it.`
- B: not run (needs the tracker).

## Transcript excerpt

A:

```
TOOL Bash: …; ls -a; cat .gitignore; env | grep -i clickup | sed 's/=.*/=<set>/'; … resolve management …; grep … management-adapters.md …
TOOL Bash: …; ls -la .connections.json …; grep -n -i "api_key\|env\|CLICKUP_\|vault\|comment" …/clickup-protocol.md …
- **ClickUp (task <item>):** the project's settings have no ClickUp status for "blocked", so the rule is to leave the
  status alone and post a `BLOCKED: … · I need: the vendor API key` comment. I couldn't post it because I found no
  ClickUp credential:
  - there's no `.connections.json` at the project root;
  - there are no `CLICKUP_*` environment variables;
  - there's no ClickUp connection or vault available in this session.
```

(First run: the agent looked only in the environment, `env | grep -i -c clickup`, while the key was in `.connections.json`.)

## Evidence

A — `git diff` of `PLAN.md`:

```
-| E1.F1.T1 [Backend] | 🔄 in_progress | 15 | — | — | |
+| E1.F1.T1 [Backend] | ⛔ blocked | 15 | — | — | 2026-09-25 BLOCKED: waiting on the vendor API key · I need: the vendor API key |
```

`tracker-outbox.jsonl`: one `comment` for `E1.F1.T1`, `last_error` = `no ClickUp credential: .connections.json absent at
project root, no CLICKUP_* env var, no ClickUp MCP session or vault available` (every place of rule 2 named). No status
call was made.

## Expected lines

| Expected | Result |
|---|---|
| A: the tracker status of the task is **unchanged** | PASS (the map's `blocked: null` read as "keep the status"; no status call) |
| A: a comment explaining the block is added to the task | not run (needs the tracker). The part BUG-26 fixed — the credential lookup — PASS: `.connections.json` checked first, then the environment, then MCP/vault, each named before queuing; with the key in `.connections.json` the lookup finds it. Regression: `test_skill_rules.py` `TrackerCredentialsAreLookedUpEverywhere` |
| A: `PLAN.md` shows the task as `blocked` | PASS |
| A: the Feature-level map for Features and the Task-level map for Tasks | not run (needs the tracker; first run PASS) |
| B: when the mapped `review` status is missing, the agent asks to re-map **only** the `review` entry | not run (needs the tracker; first run PASS) |
| B: it neither creates the status in the tool nor edits any other entry of the map | not run (needs the tracker; first run PASS) |

**Overall: PASS** for the lines run (BUG-26).
