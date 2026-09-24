# No human, no persisted mapping (REQ-W1-081)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Scratch repo with `"management": {"tool": "clickup", "location": "<a test list id>"}` and no `statuses`.
- A change `fixture-02` at phase `impl`, `PLAN.md` with one task `⬜ todo`.
- Record `sha256sum docs/spec/project.json` before the run.

## Prompt
Run headless: `claude -p --plugin-dir ~/Dev/karvey/plugins/karvey "/karvey:karvey-impl fixture-02"`.
Second run, interactive: `Use a subagent to implement the next task of fixture-02 and persist any tracker settings it needs.`

## Expected:
- Headless: the task's state change is written to `PLAN.md` (`⬜ todo` → `🔄 in_progress` …) and the output
  contains a line reporting that the status map is unresolved because no human can confirm it.
- Headless: `sha256sum docs/spec/project.json` is unchanged; no tracker status was changed.
- Subagent: the subagent's prompt, as shown in the transcript, forbids writing `project.json`, and
  `project.json` is unchanged at the end; `python3 ~/Dev/karvey/plugins/karvey/scripts/lint-plugin.py --only L-34`
  reports 0 errors on the plugin.

## Evidence
- The headless stdout, `git diff PLAN.md`, both `sha256sum` lines.
- The subagent prompt excerpt and the L-34 output.
