# A `standard` change with merged gates asks three gate questions (AC-4; REQ-W2-034, REQ-W2-035, REQ-W2-038)

> Manual agent-behaviour script (architecture §6.4 of wave2-structural, E1.F4.T7). Run it in a real session
> started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's configuration.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- A small CLI project in the scratch repo (one module, one unit test, `CHANGELOG.md` with `## [Unreleased]`).
- `docs/spec/project.json` with `management.tool: markdown`, `gates: merged`, `branch_flow` integration =
  production = `main`, no cloud.
- No other model family's CLI on `PATH` (judges run intra-model).

## Prompt
1. `/karvey:karvey-init add a --version flag` and answer the lane questions so the lane is `standard` (no UI,
   no schema, no API contract, no permissions, Tier 1, one code file).
2. At every gate question answer *Approve and advance (recommended)*, as the human, with ref `D-1`.
3. Let the run continue through requirements, architecture, tasks, impl, test and qa; stop before deploy.

## Expected:
- Exactly **three** gate questions are asked in the whole run: *what* (after requirements), *how* (after tasks)
  and *release* (after qa). Count every `AskUserQuestion` whose options include *Approve and advance*.
- No "shall we advance?" question appears anywhere, before or after an approval.
- Architecture records `generated` and continues to tasks with no question (`karvey-state.py gate … architecture`
  says it does not close *how*); infra is skipped with a reason, mockup and design_graphic are `lane:standard`.
- Each gate question is preceded by `karvey-context.py --section gate --change … --gate {what|how|release}`, and
  the judges ran before *what* (2 lenses), *how* (architecture, 2 lenses) and *release* (fiscal + 1).
- `spec.json:gate_outcomes` has three `approved` entries with `gate` `what`, `how`, `release`; `architecture` and
  `tasks` carry the same approval record; `approvals.prod` is absent (the *release* gate says prod is pending).
- Plan-rule questions, if any arose, are recorded with `--kind plan-exception` and are not among the three.

## Evidence
- The transcript lines of the three gate questions and of the `approve-gate` commands.
- `spec.json` (`approvals`, `gate_outcomes`, `skipped`) after the run.
