# Manual script: settings-docs-branch — rerun 2026-09-25

**Script:** `plugins/karvey/tests/manual/settings-docs-branch.md` (REQ-W1-083) · **Result: PASS** (A PASS, B PASS) ·
first run `settings-docs-branch-2026-09-25.md` (FAIL → F-50 → BUG-23)

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-21 / D-28, 2026-09-25, after the fix commits
  (`ce48e2c, BUG-23`), CLI 2.1.282. The agent under test is a separate `claude -p` session per run, with the branch
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

## Setup done

- `project.json` with `branch_flow {integration: dev, production: main}`, `enforcement.git_flow_hook: true`, no
  `notifications` / `management`. Commit `base` on `main`; `dev` created from it; both pushed; `dev` checked out.
- Variant B: the settings committed by variant A (`docs/karvey-settings`) fast-forwarded into `main` and pushed,
  so `origin/main:docs/spec/project.json` has complete `notifications` and `management`, `origin/dev` has
  neither, and there is no `origin/HEAD`. Then `git worktree add --detach "$SCRATCH/wt" <base-sha>`.

## Prompts

- A (on `dev`): `/karvey:karvey-init --settings` → resumed with `Notifications: Google Chat, target spaces/AAAA,
  via api, events qa and deploy. Task management: Markdown (PLAN.md). Status flow: the fixed Markdown markers.`
- B (new session in `$SCRATCH/wt`): `hola`

## Transcript excerpt

A, turn 1: `` `docs/spec/project.json` exists and matches on `dev`, `origin/dev` and `origin/main`. … Once you answer,
I'll create `docs/karvey-settings` from `origin/dev`, merge your answers into `project.json` and commit it there.
Nothing goes on `dev` or `main`, and the settings take effect after the branch is merged. ``

A, turn 2:

```
TOOL Bash: I="$(python3 …/karvey-config.py get branch_flow.integration --shell)" && git switch -c docs/karvey-settings "origin/$I" …
TOOL Bash: printf '.connections.json\n' > .gitignore && git add docs/spec/project.json .gitignore && git commit -q -F - …
Settings: notifications google-chat spaces/AAAA (api) · management markdown PLAN.md (5 states mapped)
1. **Merge the branch.** The settings only take effect after the branch is merged …
```

B — the session's first system context (stream-json `hook_response` of `SessionStart:startup`):

```
"hook_name": "SessionStart:startup", "output": "", "stdout": "", "stderr": "", "exit_code": 0, "outcome": "success"
```

and the reply to `hola` has no settings line: `¡Hola! ¿En qué te ayudo hoy? …`

## Evidence

A: `git branch --show-current` → `docs/karvey-settings`; `git log --oneline -3 --all -- docs/spec/project.json` →

```
<sha-2> docs(karvey): set team settings (Google Chat notifications, Markdown management)
<sha-1> fixture: settings-docs-branch base
```

`dev` still at `<sha-1>`; no `git commit` ran while on `dev`, so no guard block message was produced.

B: `git show origin/main:docs/spec/project.json` keys → `branch_flow, enforcement, git_platform, management,
notifications, project, repos, spec_repo`; `origin/dev` and the worktree's own `project.json` have neither block;
`git symbolic-ref refs/remotes/origin/HEAD` → not a symbolic ref (the case that ended the old lookup).

## Expected lines

| Expected | Result |
|---|---|
| A: the agent does not commit on `dev` (if it tries, the git-flow guard blocks with a `[karvey]` message) | PASS: it never tried |
| A: it proposes (or creates) a docs or feature branch and commits `project.json` there | PASS: `docs/karvey-settings` from `origin/dev` |
| A: says the settings take effect after the merge | PASS |
| B: the session start prints **no** settings notice (settings exist on `origin/main`) | PASS: the hook output is empty |

**Overall: PASS** (BUG-23 fixed; regression `tables/session.json` ss-24, `test_config_resolve.py` `OriginProductionFallback`).
