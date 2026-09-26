# Judges run as clean-context subagents and their verdicts reach the gate (REQ-W2-022, REQ-W2-027, REQ-W2-029)

> Manual agent-behaviour script (architecture §6.4 of wave2-structural, E1.F3.T7). Run it in a real session
> started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's configuration.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- `docs/spec/project.json` with `management.tool: markdown` and no `judges` key (defaults: enabled, advisory,
  `cross_model: prefer`).
- One change `demo-judges` at phase `architecture`, lane `standard`, requirements approved, with a short
  `requirements.md` (three EARS requirements) and an `architecture.md` that has one deliberate gap: a component
  that writes a token to a log file, with no control named for it.
- No other model family's CLI on `PATH` (so the run is intra-model).

## Prompt
1. `/karvey:karvey-architecture demo-judges` and let it finish writing `architecture.md`.
2. At the gate question, answer *Request changes* with the reason "judges check only".

## Expected:
- Before the gate question the agent runs `karvey-judges.py inputs demo-judges architecture --json`; the inputs
  are exactly `requirements.md` and `architecture.md` of the change plus the goal and the rubric.
- It starts **two** subagents (lane `standard`) in one message, one per lens (`security`, `methods`), each given
  file paths and the rubric section only — no summary of the session, no draft text in the prompt.
- No subagent edits a file: `git status --porcelain` shows only `findings.md` and `spec.json` changed after the
  judges ran.
- `karvey-judges.py collect … --intra-model` runs, then `karvey-state.py judge-run demo-judges architecture
  --from …`; `spec.json:judge_runs` has two records with `model` set and `intra_model: true`.
- `findings.md` gains at least one `open` row with origin `judge:security` citing the token-logging line of
  `architecture.md`.
- The gate summary names both lenses with their verdicts and says the run was intra-model; a Critical/High
  finding is shown in full.
- The *Request changes* answer is recorded with `outcome … changes_requested` and the reason; the phase stays
  `architecture`.

## Evidence
- The transcript lines with the commands, the two `Agent` prompts and the gate summary.
- `git diff` of `findings.md` and `spec.json`.
