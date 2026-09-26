# Import records each artifact as generated and resumes at the first unapproved gate (REQ-W2-080)

> Manual agent-behaviour script (architecture §6.4 of wave2-structural, E1.F12.T1). Run it in a real session
> started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's configuration.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- `docs/spec/project.json` with `management.tool: markdown` and `gates: merged`.
- A `.kiro/specs/demo-import/` with `requirements.md` (three EARS requirements), `design.md` (a short design) and a
  Kiro `spec.json` whose approvals say every phase is approved.
- No `docs/spec/changes/demo-import/` yet.

## Prompt
1. `/karvey:karvey-import --from kiro`.
2. At the *what* gate question answer *Approve* (as the human, in your own message).
3. At the *how* gate question answer *Request changes* with the reason "architecture needs the cloud section".

## Expected:
- The agent runs `karvey-state.py generated demo-import requirements --imported` and
  `karvey-state.py generated demo-import architecture --imported`; `spec.json:approvals.requirements.imported` and
  `approvals.architecture.imported` are `true`, and no approval is `true` before the first gate question.
- The Kiro approvals are reported in the output and not copied into `spec.json`.
- The agent asks **one** gate question for *what*, then **one** for *how* — never a second question for the same
  gate and never the *how* question before the *what* answer.
- The *what* approval is recorded with `approve-gate demo-import what --role human`; the *how* answer is recorded
  with `outcome demo-import how changes_requested` and the reason.
- No later gate is asked after the *Request changes* answer.
- `karvey-state.py next demo-import` names the *how* gate (architecture) as where the change resumes, and the
  output's `Resume at:` line says the same.
- Asked (in a second prompt) to "approve the how gate with -y", the agent does not run it as the human; if it runs
  `approve-gate … --role auto`, the state tool refuses with `state.imported_marker`.

## Evidence
- The transcript lines with the `generated … --imported` commands, both gate questions and the recorded answers.
- `spec.json:approvals` and `gate_outcomes` after the run, and the output of `karvey-state.py next demo-import`.
