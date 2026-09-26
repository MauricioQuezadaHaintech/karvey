# Portability guide — what depends on the runtime

**Claude Code is the only supported runtime (D-32).** The method's text (phases, rules, artifacts) is plain Markdown
and JSON, and its scripts are Python 3.9+ with the standard library only, so most of it runs anywhere. A few
behaviours rely on the agent runtime itself. This guide lists each one and what a team adapting the method to another
runtime would have to replace. It is information, not a support promise: nothing here is tested outside Claude Code.

Lint L-69 keeps this guide complete: every hook event registered in `plugins/karvey/hooks/hooks.json` and every tool
name used in a skill's `allowed-tools` must have an entry below.

## Tools named in `allowed-tools`

| Tool | What the method uses it for | Adaptation note |
|---|---|---|
| `Read` | read artifacts, rules and code | any file-read tool; judges get Read, Grep and Glob only |
| `Write` | create an artifact (a spec file, a mockup) | any file-write tool |
| `Edit` | change part of an artifact | a write tool plus a diff; keep the change small |
| `Bash` | run the method's scripts (`karvey-state.py`, `karvey-close.py`, …) and git | any shell tool; the scripts need `python3` |
| `Glob` | find files by pattern | a file-listing tool |
| `Grep` | search text | a search tool or `grep` through the shell |
| `Agent` | start a clean-context subagent (judges, parallel tasks) | a sub-session with its own context and a closed tool list; without one, judges cannot run (`judges: disabled`) |
| `AskUserQuestion` | the gate question and other choices put to the human | a prompt to the user that waits for the answer; never let the agent answer it |
| `WebSearch` | research in grill and discovery | any search tool, or skip the step and say so |

## Hook events of `hooks.json`

| Event | What runs | Adaptation note |
|---|---|---|
| `SessionStart` | `karvey-session-context.sh`: identity, handoff, live state, open questions and risks | a start-of-session hook that can add text to the context; without it, run `/karvey-checkpoint restore` by hand |
| `UserPromptSubmit` | the approval hook: records an approval marker from the human's own words | a hook that sees the user's prompt before the model; without it approvals are recorded by the state tool only |
| `PreToolUse` | the guards (protect-paths, prod-gate, git-flow, plan-gate, trailer) | a hook that can block a tool call before it runs; without it the guards are advice, not enforcement |
| `PostToolUse` | the spec-write validator and the pending knowledge sync | a hook after a file write; without it run `karvey-state.py validate` yourself |

## Other runtime-dependent behaviours

| Behaviour | Where | Adaptation note |
|---|---|---|
| Statusline input | `hooks/karvey-statusline.sh` reads the runtime's JSON on stdin (model, context, `cost.total_cost_usd`, transcript path) | the effort record (`karvey-state.py effort`) needs the session's cost and transcript; without them effort reads `n/a — statusline not installed`, never 0 |
| Session transcript | judge cost `--transcript auto` reads per-message `usage` | without a transcript the judge cost is an estimate (`source: estimate`) |
| Plugin install and `CLAUDE_PLUGIN_ROOT` | every skill calls `"${CLAUDE_PLUGIN_ROOT}/scripts/…"` | set the variable to the plugin folder, or replace it with the path |
| Loaded plugin version | `karvey_lib/runtime.py` reads the runtime's installed-plugins record | without one, health says `loaded version unknown` |
| Slash commands | `/karvey-…` triggers a skill | any way to load a skill's instructions into the session |
| Browser work | `project.json:browse.via` (`local`, `agent:<name>`, `none`) | `none` makes the visual checks `not evaluated`, said so in QA |

## What does not depend on the runtime

The state machine (`schemas/state-machine.json`), the gates, the artifacts under `docs/spec/`, the check modes, the
linter and every script under `plugins/karvey/scripts/` — they read and write files and call `git`, nothing else.
