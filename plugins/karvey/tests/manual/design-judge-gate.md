# Design judge at the what gate: no art catalogue without an asset request, the verdict and the contrast result in the gate summary (REQ-W3-037, REQ-W3-039)

> Manual agent-behaviour script (architecture §1.18 of wave3-optimization, E1.F6.T7).
> `manual:` a real clean-context judge subagent and the design phase's own conduct cannot run in the unit tests;
> `test_design_delta.py`, `test_contrast.py` and `test_judges.py` (`DesignJudge`) cover the scripts themselves.
> Run it in a real session started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a
> throw-away repo under `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's
> configuration. It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding; never edit
> the script to match what happened.

## Setup
- In the throw-away repo, a `project.json` with `targets: ["web"]`, `notifications.channel: none`,
  `management.tool: markdown`, and judges left at their defaults (advisory).
- Copy `plugins/karvey/tests/unit/fixtures/design/design-system.md` to `docs/spec/design-system.md` and commit it.
- Create a change `sample-ui` with lane `feature-ui` whose PRD asks for one new status tag on an existing list
  screen and **no illustrations or assets**; take it through requirements and an approved mockup
  (`mockup/index.html`) with the method's own skills.

## Prompt
1. "Run design-graphic for sample-ui."
2. "Show me the what-gate summary before I answer."

## Expected:
- Step 1: the agent reads `docs/spec/design-system.md` and does not redefine its tokens; it writes `design-spec.md`
  (first sentence `Applies to … mockup/index.html`) and `design-delta.md` listing only the new tag (a component, and a
  token only if one is new — with `Base value` for any token it modifies); it runs `karvey-design.py diff sample-ui`
  and it reports no `undeclared modification`.
- Step 1: it runs `karvey-contrast-check.py --delta sample-ui --json` into `contrast.json` and cites the result in
  the design-spec; it writes **no** score table and **no** `design-components.md` (no asset was requested) and says
  `Art catalogue: not requested`.
- Step 1: it builds the judge inputs with `karvey-judges.py inputs sample-ui design_graphic --json` (one lens,
  `design`; inputs = the delta, `mockup/index.html`, `contrast.json`), runs one clean-context judge with Read, Grep
  and Glob only, and collects it with `karvey-judges.py collect … --transcript auto`; kept findings appear in
  `findings.md` with origin `judge:design`.
- Step 2: `karvey-context.py --section gate --change sample-ui --gate what` shows the judge line for
  `design_graphic` (verdict, kept and discarded counts, model, tokens with their source) and a `contrast:` section
  with the pair count and every pair below level (or `0 below level`); the agent asks the one gate question and
  records nothing before the answer.

## Evidence
- The transcript lines with `karvey-design.py diff`, `karvey-contrast-check.py`, `karvey-judges.py inputs` and
  `collect`, and the gate question.
- `design-delta.md`, `contrast.json`, the new `findings.md` rows, and `ls` of the change directory showing no
  `design-components.md`.
- The gate summary output.
