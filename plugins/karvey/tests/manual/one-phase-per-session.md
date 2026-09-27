# One phase per session: checkpoint offer at the gate close, fresh-session advice at the threshold, resume by the session hook (REQ-W3-013)

> Manual agent-behaviour script (architecture §1.8 C-08 of wave3-optimization, E1.F2.T12).
> `manual:` a real fresh session, a real statusline capture and what the model loads next cannot run in the unit
> tests; `test_close.py` covers step 5 of the close script and `observed` itself.
> Run it in a real session started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a
> throw-away repo under `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's
> configuration. It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding; never edit
> the script to match what happened.

## Setup
- Copy `plugins/karvey/tests/unit/fixtures/sponsor/` into the throw-away repo and commit it: one change
  `sample-change` at the architecture gate.
- Install the statusline for the session (hooks/README.md) so the close has a context reading.
- Keep the session transcript path the runtime shows (for the `observed` step).

## Prompt
1. In a new session: "Close the how gate of sample-change: I approve the architecture." (the context is low).
2. In the same session, read enough files to take the context above the red threshold (`context_pct.red` in
   `scripts/karvey_lib/defaults.json`), then: "Re-run the close of the how gate of sample-change with changes
   requested."
3. Save the checkpoint the close offered, end the session and open a new one in the same repo; ask: "What's next in
   karvey?"
4. After the next phase skill has run in that new session, run
   `python3 <plugin>/scripts/karvey-context-budget.py observed --transcript <that session's transcript> --skill <the
   phase skill>`.
5. Repeat step 2 with the statusline removed.

## Expected:
- Step 1: `karvey-close.py` step 5 prints the offer (`/karvey-checkpoint save`, "the next phase can start in a fresh
  session") and `continuing in this session is allowed`; the agent relays the offer and does not end the session
  on its own.
- Step 2: step 5 prints `recommend: checkpoint + fresh session before the next skill` with the reading and the
  threshold; the agent recommends saving and starting the next phase in a new session **before** loading the next
  skill, and still proceeds if the user says to continue here.
- Step 3: the session hook's context names the change and its next skill (from `karvey-state.py next`), and the agent
  resumes from the checkpoint without re-asking decisions it holds.
- Step 4: `opened:` lists the phase skill and the rules of its `Load:` line; `outside the load list:` is empty (a rule
  cited only in a footnote was not opened). Any line there is a finding.
- Step 5: step 5 prints `context reading unavailable` and still offers the checkpoint.
