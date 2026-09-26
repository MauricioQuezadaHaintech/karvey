# Sponsor page at a real gate: built, opened offline, refused on a leak, delivery failure to the outbox (REQ-W3-022, REQ-W3-023, REQ-W3-024)

> Manual agent-behaviour script (architecture §6.3 of wave3-optimization, E1.F4.T11).
> `manual:` a real gate question answered by a person, a real channel adapter and a real browser cannot run in the
> unit tests; `test_sponsor.py`, `test_close.py` and `test_sponsor_page.mjs` cover the scripts themselves.
> Run it in a real session started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a
> throw-away repo under `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's
> configuration. It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding; never edit
> the script to match what happened.

## Setup
- Copy `plugins/karvey/tests/unit/fixtures/sponsor/` into the throw-away repo and commit it: one change
  `sample-change` at the architecture gate, a sponsor who is also the approver (`destination: email`), open
  questions, a risk register and an effort record.
- Keep the statusline installed for the session (hooks/README.md) so the close records a measured effort.
- For the delivery-failure step, point `project.json:stakeholders.sponsor.destination` at a channel the session
  cannot reach (for example `webhook` with a secret name that is not defined in the environment).

## Prompt
1. "Close the how gate of sample-change: I approve the architecture."
2. Open `docs/spec/changes/sample-change/sponsor.html` in a browser with the network disabled, at 360 px and at
   1440 px wide, in the light and the dark scheme, and in the print preview.
3. Edit one risk of `risks.md` so its text quotes a connection string (a made-up one), then: "Re-run the close of
   the how gate with changes requested: the risk text changed."
4. Restore the risk text, switch the sponsor destination to the unreachable one and: "Close the how gate again."

## Expected:
- Step 1: the agent records the approval first (`approve-gate … how`), then runs `karvey-close.py sample-change
  architecture --outcome approved` **once**; it sends the sponsor payload as printed and composes no message of its
  own; `sponsor-history.jsonl` gains one line with `outcome: approved` and a sha256; `spec.json:effort` gains one
  `architecture` entry.
- Step 2: every section shows (Waiting for you first, with the pending approval and the overdue question), no
  horizontal scroll at 360 or 1440 px, both schemes readable, the print preview shows every section with the
  `details` open and hides only the section navigation; the browser's network panel shows zero requests.
- Step 3: the close reports `leak check: FAIL — page not written, not delivered`, naming the field
  (`risks.items[…].description`) and the rule `secret` **without the value**; `sponsor.html` is byte-identical to
  the one from step 1; `sponsor-refusals.jsonl` has the field and rule and not the string; the effort step still
  ran.
- Step 4: the page is regenerated, the send fails, the agent says so, records it with
  `karvey-config.py outbox add sample-change --op deliver_sponsor …`, and the gate stays closed.

## Evidence
- The transcript lines with `approve-gate`, `karvey-close.py`, the payload sent, the refusal lines and the outbox
  entry.
- Screenshots at 360 px, 1440 px, dark scheme and print preview; the network panel with zero requests.
- `sponsor-history.jsonl`, `sponsor-refusals.jsonl`, `cmp` of the page before and after step 3.
