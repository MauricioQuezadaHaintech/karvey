# Settings travel as a reviewed change (REQ-W1-083)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Scratch repo with `branch_flow: {"integration": "dev", "production": "main"}`, `enforcement.git_flow_hook: true`,
  and no `notifications` / `management` in `project.json`. Check out `dev`.
- Second variant: commit complete settings on `origin/main`, then create a worktree from an older commit
  (`git worktree add ../wt <older-sha>`) and start the session inside `../wt`.

## Prompt
Variant A (on `dev`): `/karvey:karvey-init --settings`, answer every question.
Variant B: start a session in the worktree and type `hola`.

## Expected:
- A: the agent does not commit on `dev`; if it tries, the git-flow guard blocks the commit with a
  `[karvey]` message. It proposes (or creates) a docs or feature branch, commits `project.json` there, and
  says the settings take effect after the merge.
- B: the session start prints **no** settings notice (the settings exist on `origin/main`), even though the
  worktree's own `project.json` lacks them.

## Evidence
- A: `git branch --show-current`, `git log --oneline -2 --all -- docs/spec/project.json`, and any guard block
  message.
- B: the session's first system context (no `settings` line), plus `git show origin/main:docs/spec/project.json`.
