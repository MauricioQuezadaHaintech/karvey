# Missing status map — resolved before the first status change (REQ-W1-080)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Scratch repo (see the note above). `docs/spec/project.json` with
  `"management": {"tool": "clickup", "location": "<a test list id>"}` and **no** `statuses`. The list is a
  test list in a sandbox ClickUp workspace you own, with its own statuses.
- A change `fixture-01` at phase `tasks` with an approved `architecture.md` (copy any small one).
- Second variant: `"management": {"tool": "jira"}` with **no** `location`, change at phase `impl`.

## Prompt
Variant A: `/karvey:karvey-tasks fixture-01`
Variant B: `/karvey:karvey-impl fixture-01`

## Expected:
- A: before creating any task the agent runs `karvey-config.py resolve management`, reads the list's real
  statuses from the tool, shows a proposed map for `todo | in_progress | review | done | blocked`, and asks
  you to confirm it. After you confirm, `project.json` gains `management.statuses` with exactly the
  confirmed values, and only then is the first task created.
- A: the persisted map is committed on a feature or docs branch, not on the integration branch
  (see `settings-docs-branch.md`).
- B: the agent asks for the Jira project key and changes **no** status while waiting; it never picks a
  project by itself.

## Evidence
- Transcript excerpt from the resolve call to the first create/set call.
- `git diff docs/spec/project.json` after A; `git log -1 --format=%D` (branch).
- For B: the question as printed and the tracker's activity log showing no change.
