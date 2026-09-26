# Manual script: grill-batches — 2026-09-26

**Script:** `plugins/karvey/tests/manual/grill-batches.md` (REQ-W2-041) · **Result: PASS**

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-28 (the owner's authorisation for this change's scripts),
  2026-09-26. The agent under test is a separate `claude -p` session per turn, with the branch plugin and without
  the user settings; multi-turn scripts resume the same session.
- **Throw-away repo:** `git init -q --bare "$SCRATCH/<name>.git"`, `git init -q -b main "$SCRATCH/<name>"` with
  `origin` pointing at the bare repo; fixture state written only through `plugins/karvey/scripts/karvey-state.py`
  (`init`, `lane set`, `advance`, `generated`, `approve --role human --ref D-01`, `skip`). `$SCRATCH` is a
  `mktemp -d` directory, deleted after the run, and the sessions' transcript directories were deleted with it.
- **Agent-under-test command** (every turn; later turns add `--resume <session>`):

```bash
cd "$SCRATCH/<name>" && claude -p [--resume <session>] \
  --plugin-dir <worktree>/plugins/karvey --setting-sources project,local \
  --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent,Skill,TodoWrite,WebFetch" \
  --output-format stream-json --verbose "<prompt>"
```

- **Harness limit:** a `-p` session has no `AskUserQuestion` tool (its init event lists the tools), so every
  question arrives as one prose message and the answer is the next turn's prompt. Where a script counts questions
  per `AskUserQuestion` call, the count is taken per question message.

## Setup done

- `package.json` + `package-lock.json` (express 4.19.2, pg 8.11.5), `src/server.js` (`GET /orders` over `pg`),
  `.github/workflows/ci.yml` (Node 20, `npm ci && npm test`), `main.tf` (`aws_db_instance`, engine postgres),
  `docs/spec/project.json` (markdown, trunk). Committed.

## Prompts

1. `/karvey:karvey-grill add a CSV export of the orders list for the support role`
2. Every later turn: the recommended option of every question, except the stack question: *Correct it — the
   database is MySQL*; to the agent's follow-up on the contradiction: "production already runs MySQL; this repo is
   out of date".

## Transcript excerpt

```
TOOL Bash: for f in .github/workflows/ci.yml docs/spec/project.json main.tf package.json package-lock.json src/server.js; do … cat "$f"; done
**Batch 1 — Step 0 + Branch A: The problem** (4 questions)
**0. 10-star reframe or go straight to the questions?**
- *Go straight to the questions (recommended).* …
**Batch 4 — Branch F: Technology stack** (2 questions; the rest I read from the repo)
**1. Is this the stack I found?**
| Backend | Node 20 + Express 4.19 … | Database | PostgreSQL (AWS RDS) … pg 8.11 | Code/CI platform | GitHub (GitHub Actions) | IaC | Terraform |
- *Confirm the stack (recommended).* …   - Correct something. Tell me what.
**Batch 5 — Branch F: follow-up on the database** (2 questions)
### Detected stack
- **Database:** **MySQL** on AWS RDS, per the user. ⚠️ This repo still shows PostgreSQL …
✅ Interrogation complete. Next step:  /karvey-init add-orders-csv-export
```

## Evidence

Questions per message: batch 1 = 4, 2 = 4, 3 = 4, 4 = 2, 5 = 2, 6 = 3, 7 = 3; no message carries a fifth question.
In every batch the first option is the one marked *(recommended)*. The lockfile, the manifest and the CI file were
read (turn 1, visible `cat`) before the stack batch. After *Correct it*, only the database was asked again
(batch 5); the other stack items were not re-asked. No transcript turn contains an "advance?" question.

## Expected lines

| Expected | Result |
|---|---|
| each question message holds at most four questions; none carries a fifth in prose | PASS (per message; the `-p` session has no `AskUserQuestion` tool) |
| first option of every question is the recommended one, marked *(recommended)* | PASS |
| lockfile, manifest and CI read before the stack branch; **one** confirmation question listing Node, the HTTP framework, PostgreSQL, GitHub Actions, Terraform | PASS |
| after *Correct it*, only the database is asked again | PASS |
| the synthesis shows MySQL under **Detected stack**; the closing asks no "shall we advance?" | PASS |

**Overall: PASS.**
