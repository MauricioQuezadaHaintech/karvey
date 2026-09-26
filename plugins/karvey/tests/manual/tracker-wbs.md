# One work breakdown on the Markdown tracker: Features are areas, phases on the Epic, E1.QA / E1.DEPLOY found or created once (REQ-W3-040, REQ-W3-041, REQ-W3-042)

> Manual agent-behaviour script (architecture §1.19 of wave3-optimization, E1.F7.T4).
> `manual:` the tasks, qa and deploy skills writing a tracker in a real session cannot run in the unit tests;
> `test_wbs.py` and lint L-68 cover `karvey-trace.py --wbs`, the reconciliation and the rule text.
> Run it in a real session started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a
> throw-away repo under `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's
> configuration. It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding; never edit
> the script to match what happened.

## Setup
- A `project.json` with `management.tool: markdown`, `notifications.channel: none`, lane `standard`.
- A change `sample-wbs` with an approved architecture naming two functional areas (for example *Sign-in* and
  *Reports*) and one requirement that belongs to both.

## Prompt
1. "Generate the tasks of sample-wbs."
2. "Run QA on sample-wbs." (let the review produce one High finding)
3. "Run QA on sample-wbs again." (the same finding still open)
4. "Prepare the deploy of sample-wbs." (stop before any push; the deploy record only)

## Expected:
- Step 1: `PLAN.md` has one `### Feature` per functional area (*Sign-in*, *Reports*) — no Feature named after a
  pipeline phase; the pipeline phases appear as a checklist on the Epic; the shared requirement carries a
  `Split:` line in the later Feature; `karvey-trace.py sample-wbs --wbs` reports `0 issue(s)`.
- Step 2: the QA review item is created as `E1.QA` under the Epic (an `### Epic item E1.QA` section), with the High
  finding's fix task as its child — not at the root of the plan.
- Step 3: `E1.QA` is found and reused: there is still exactly one `E1.QA` section, and no second QA item anywhere.
- Step 4: the deploy record is `E1.DEPLOY` under the Epic with `[Deploy] sample-wbs@{version}` as its child; a second
  run of step 4 finds it and creates nothing new.
- Every step: `karvey-trace.py sample-wbs --wbs` shows no `legacy shape` and no `outside the hierarchy` line.

## Evidence
- `PLAN.md` after each step (a `diff` between steps 2 and 3 shows no new QA section).
- The `karvey-trace.py sample-wbs --wbs` output after steps 1 and 4.
