# Manual script: init-not-now — 2026-09-25

**Script:** `plugins/karvey/tests/manual/init-not-now.md` (REQ-W1-095) · **Result: PASS**

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

- `project.json` with `project`, `repos`, `spec_repo`, `branch_flow` (`main`/`main`), `enforcement` and
  `management: markdown` (fixed markers); **no** `notifications` block. Committed on `main`, pushed.

## Prompts

- Run 1: `/karvey:karvey-init fixture-07` → resumed with `1. The service has no health check, so the load
  balancer cannot tell when it is down. 2. Use fixture-07 exactly. 3. Notifications: not now.` → resumed with
  `Liveness only, path /health. All proposals accepted as written.`
- Run 2 (new session, same repo): `/karvey:karvey-init fixture-08`

## Transcript excerpt

Run 1, turn 1: `docs/spec/project.json exists and already has management (Markdown / PLAN.md) and enforcement,
so I'm keeping those as they are. It has no notifications block, so first-use setup has to ask about that`
followed by the notifications options including `Not now`.

Run 1, final output:

```
✅ Spec initialized: docs/spec/changes/fixture-07/   (phase init, via karvey-state.py)
Project config: docs/spec/project.json (read)
Settings: notifications deferred · management markdown PLAN.md (unchanged)
Files: spec.json · prd.md · PLAN.md · docs/spec/specs/service-health/spec.md (new)
Management: PLAN.md
```

Run 2:

```
- **Team settings:** already filled in, so there are no settings questions this time. Notifications are set to
  "not now" (you can change that later with `/karvey-init --settings`) …
```

## Evidence

`git diff main -- docs/spec/project.json` after run 1 (on `docs/karvey-settings`, from `origin/main`):

```
+  },
+  "notifications": {
+    "deferred": true
   }
```

Epic line of `PLAN.md`: `**Created:** 2026-09-25 | **Status:** ⬜ todo` (Epic `## Epic: Service liveness health check`).
`python3 <repo>/plugins/karvey/scripts/lint-plugin.py --only L-28` → `0 errors, 0 warnings (1 checks)`.

## Expected lines

| Expected | Result |
|---|---|
| Run 1: the final output has a `Settings:` line | PASS |
| Run 1: `project.json` records the answer (`notifications.deferred: true`) | PASS |
| Run 1: the Epic in `PLAN.md` starts in the one initial state the skill states for every tool (`todo`) | PASS: `⬜ todo` |
| Run 1: Step 3 does not re-ask fields that `project.json` already has | PASS: only notifications (Step 3.2) and change metadata were asked |
| Run 2: the notifications question is **not** asked again | PASS |
| Run 2: the output says how to set them later (`/karvey:karvey-init --settings`) | PASS |

**Overall: PASS.** Run 2 stopped at the change description (Step 1), which is outside the script's Expected lines.
