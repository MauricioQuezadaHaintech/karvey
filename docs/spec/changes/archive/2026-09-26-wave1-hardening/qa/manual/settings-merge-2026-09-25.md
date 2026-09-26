# Manual script: settings-merge — 2026-09-25

**Script:** `plugins/karvey/tests/manual/settings-merge.md` (REQ-W1-096, BUG-01) · **Result: PASS**

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

- `project.json` with `"notifications": {"channel": "slack", "target": "#dev", "events": ["qa", "deploy", "incident"], "x_custom": 1}`
  and `"management": {"tool": "markdown", "location": "docs/spec/changes/{change-id}/PLAN.md"}`; committed on `main`, pushed.
- `docs/spec/changes/` holds only `.gitkeep`; `ls docs/spec/changes/ > "$SCRATCH/changes-before.txt"`.

## Prompts

- `/karvey:karvey-init --settings` → resumed with `Change only the channel: google-chat, with target spaces/AAAA. Keep everything else exactly as it is.`

## Transcript excerpt

Turn 1 (questions pre-filled):

```
**1. Notifications** (currently set)
- Channel: `slack` · Target: `#dev` · **Via:** not set … · Events: `qa`, `deploy`, `incident` · `x_custom: 1` is a custom key and will be kept.
**2. Task management** (currently set)
- Tool: `markdown` (PLAN.md) · Location: `docs/spec/changes/{change-id}/PLAN.md` …
**3. Status flow** — With Markdown the markers are fixed …
This is settings-only mode, so I won't create a change-id, `spec.json` or tracker item.
```

Turn 2, final line printed: `Settings: notifications google-chat spaces/AAAA (via not set) · management markdown PLAN.md (fixed markers)`

## Evidence

`git diff main docs/karvey-settings -- docs/spec/project.json` (commit on the new `docs/karvey-settings` branch):

```
   "notifications": {
-    "channel": "slack",
-    "target": "#dev",
+    "channel": "google-chat",
+    "target": "spaces/AAAA",
     "events": [
       "qa",
       "deploy",
```

`ls docs/spec/changes/ | diff changes-before.txt -` → empty. No tracker is configured (`markdown`), so no
tracker item can exist. `bash <repo>/plugins/karvey/hooks/tests/test-hooks.sh` → `ok   notice says settings-only (BUG-01 guard)` · `result: 66 passed, 0 failed`.

## Expected lines

| Expected | Result |
|---|---|
| Every question is pre-filled with the current value | PASS (via had no current value and was shown as not set) |
| `notifications.events` still `["qa", "deploy", "incident"]`, `x_custom` still `1`, `management` unchanged; only `channel` and `target` differ | PASS: the diff has those two lines only |
| The skill prints one summary line and stops | PASS: one `Settings:` line, no further phase |
| `ls docs/spec/changes/` equals `changes-before.txt` and no tracker item exists | PASS |

**Overall: PASS.**
