# QA moves review to done; archive checks none is left (REQ-W1-084)

> Manual agent-behaviour script (AC-7, architecture §6.5, E1.F14.T4). Run it in a real session started with
> the branch plugin, `claude --plugin-dir ~/Dev/karvey/plugins/karvey`, inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"` plus a bare `origin`), never in this repo or `~/.claude/`.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Scratch repo with Markdown tracking (`management.tool: markdown`). A change `fixture-04` at phase `qa`
  whose `PLAN.md` has 8 tasks at `👀 review` and their Features at `👀 review`.
- Second variant: same change after QA approval, but put one task back at `👀 review` by hand, then move
  the change to archive.

## Prompt
Variant A: `/karvey:karvey-qa fixture-04`, and approve the review when asked (`aprobado`).
Variant B: `/karvey:karvey-archive fixture-04`.

## Expected:
- A: after `approvals.qa.approved` becomes true (via `karvey-state.py approve fixture-04 qa …`), all 8 tasks and
  their Features are `✅ done` in `PLAN.md`; none stays at `👀 review`.
- B: archive lists the one task still at `👀 review` by its id and does **not** mark the Epic done.

## Evidence
- `grep -c '👀 review' PLAN.md` before and after A; `python3 ~/Dev/karvey/plugins/karvey/scripts/karvey-state.py validate docs/spec/changes/fixture-04/spec.json` output after A.
- B: the archive output naming the task, and the Epic line of `PLAN.md` unchanged.
