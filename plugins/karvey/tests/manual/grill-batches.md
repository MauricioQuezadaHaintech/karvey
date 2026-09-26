# Grill asks in batches of at most four, recommended first, and infers the stack (REQ-W2-041)

> Manual agent-behaviour script (architecture §6.4 of wave2-structural, E1.F4.T6). Run it in a real session
> started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's configuration.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- A small web service in the scratch repo: `package.json` + `package-lock.json` (an HTTP framework and a
  PostgreSQL client), a `.github/workflows/ci.yml`, and a `main.tf`. Commit it.

## Prompt
1. `/karvey:karvey-grill add a CSV export of the orders list for the support role`
2. Answer every batch with its recommended options, except: in the stack confirmation choose *Correct it* and say
   the database is MySQL.

## Expected:
- Every question message is one `AskUserQuestion` call with **at most four** questions; no message carries a
  fifth question in prose.
- In every question the first option is the recommended one, marked *(recommended)*.
- Before the stack branch the agent reads the lockfile, the manifest and the CI file (visible tool calls), then
  asks **one** confirmation question listing the inferred stack (Node, the HTTP framework, PostgreSQL, GitHub
  Actions, Terraform).
- After *Correct it*, only the corrected item (the database) is asked or recorded again; the other stack items are
  not asked one by one.
- The final synthesis shows MySQL under **Detected stack**, and the closing asks no "shall we advance?" question
  (it states the next step per `rules/gates.md`).

## Evidence
- The transcript of every question batch (count the questions per call) and the synthesis.
