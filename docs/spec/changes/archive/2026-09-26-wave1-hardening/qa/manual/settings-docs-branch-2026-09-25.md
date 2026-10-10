# Manual script: settings-docs-branch — 2026-09-25

**Script:** `plugins/karvey/tests/manual/settings-docs-branch.md` (REQ-W1-083) · **Result: FAIL** (A PASS, B FAIL → F-50)

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

- `project.json` with `branch_flow {integration: dev, production: main}`, `enforcement.git_flow_hook: true`, no
  `notifications` / `management`. Commit `base` on `main`; `dev` created from it; both pushed; `dev` checked out.
- Variant B: the settings committed by variant A (`docs/karvey-settings`) fast-forwarded into `main` and pushed,
  so `origin/main:docs/spec/project.json` has complete `notifications` and `management`. Then
  `git worktree add --detach "$SCRATCH/wt" <base-sha>` (the older commit, whose `project.json` has neither block).

## Prompts

- A (on `dev`): `/karvey:karvey-init --settings` → resumed with `Notifications: Google Chat, target spaces/AAAA,
  via api, events qa and deploy. Task management: Markdown (PLAN.md). Status flow: the fixed Markdown markers.`
- B (new session in `$SCRATCH/wt`): `hola`

## Transcript excerpt

A, turn 1: `I'll commit it on a new docs/karvey-settings branch from origin/dev, not on dev itself. The settings take effect after that branch is merged.`

A, turn 2:

```
TOOL Bash: git add docs/spec/project.json && git commit -q -m "docs(karvey): set team settings (notifications google-chat, management markdown) …"
  ## docs/karvey-settings...origin/dev [ahead 1]
Settings: notifications google-chat spaces/AAAA (api) · management markdown PLAN.md (5 states mapped)
- **When it takes effect:** Karvey's hooks read settings from the merged version on `origin/main`, so they only
  apply after this branch is merged through `dev`. To finish, push `docs/karvey-settings` and open a pull request into `dev`.
```

B — the session's first system context (stream-json `hook_response` of `SessionStart:startup`):

```
"additionalContext": "Karvey (info): team settings not set (notifications + management). To set them, the user
can run `/karvey:karvey-init --settings` — settings only, it creates no change and nothing in any tracker."
```

and the agent's reply to `hola` relayed it: `la configuración del equipo en Karvey (notificaciones y gestión) todavía no está hecha. Si quieres dejarla lista, ejecuta /karvey:karvey-init --settings`.

## Evidence

A: `git branch --show-current` → `docs/karvey-settings`; `git log --oneline -2 --all -- docs/spec/project.json` →

```
<sha-2> docs(karvey): set team settings (notifications google-chat, management markdown)
<sha-1> fixture: settings-docs-branch base
```

`dev` still at `<sha-1>`; no commit was attempted on `dev`, so no guard block message was produced.

B: `git show origin/main:docs/spec/project.json` has `notifications {channel: google-chat, target: spaces/AAAA, via: api, events: [qa, deploy], …}` and `management {tool: markdown, …}`; the worktree's own `project.json` has neither.

Cause (read, not fixed): `settings_nudge` in `plugins/karvey/hooks/karvey-session-context.sh` reads only
`$ROOT/docs/spec/project.json` of the working copy; nothing reads `origin/{integration}` or `origin/{production}`.
Note for the fix: the script says `origin/main` (production) while REQ-W1-083 says `origin/{integration}`
(here `dev`, which does not have the settings yet); neither is read today.

## Expected lines

| Expected | Result |
|---|---|
| A: the agent does not commit on `dev` (if it tries, the git-flow guard blocks with a `[karvey]` message) | PASS: it never tried |
| A: it proposes (or creates) a docs or feature branch and commits `project.json` there | PASS: `docs/karvey-settings` from `origin/dev` |
| A: says the settings take effect after the merge | PASS |
| B: the session start prints **no** settings notice (settings exist on `origin/main`) | **FAIL**: the notice was printed |

**Overall: FAIL** (F-50).
