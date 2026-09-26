# Manual script: merged-gates-three-questions — 2026-09-26

**Script:** `plugins/karvey/tests/manual/merged-gates-three-questions.md` (AC-4; REQ-W2-034, 035, 038) · **Result:
PASS** — the run also surfaced four plugin defects, fixed in this iteration (BUG-53, BUG-67, BUG-68, BUG-69)

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

- A small Python CLI (`src/greet/__main__.py`, one unit test, `CHANGELOG.md` with `## [Unreleased]`, `VERSION`).
  `project.json` markdown, `gates: merged`, trunk `main`/`main`, no cloud. `git_platform` was missing from the
  fixture; added in turn 2 (said so in the prompt). No other model family's CLI on `PATH`.

## Prompts

1. `/karvey:karvey-init add a --version flag` (no question tool: the agent recorded the lane from its own reading —
   no UI, schema, contract or permissions, Tier 1 — as `standard` and listed the answers for correction).
2. "The metadata is correct … Continue the run: /karvey:karvey-requirements add-version-flag, and keep going phase by
   phase through architecture, tasks, impl, test and qa; stop before deploy. Ask me only the gate questions."
3. `Approve and advance (recommended). Ref D-1.` (at *what*) · 4. the same (at *how*) · 5. "Yes: run
   /karvey:karvey-iterate add-version-flag as you suggest, then continue to the release gate and stop before deploy."
   (QA ended with open findings, so the skill routed to iterate before the gate) · 6. the same approval (at *release*).

## Transcript excerpt

```
(2) python3 …/karvey-context.py --section gate --change add-version-flag --gate what
    **Do you approve the requirements?**  Approve and advance · Approve and stop · Request changes
(3) python3 $S approve-gate add-version-flag what --by "…" --role human --ref D-1
    python3 $S advance add-version-flag architecture; python3 $S gate add-version-flag architecture …   (no question)
    … --section gate … --gate how      **Do you approve the design (with AD-1 = A) and the tasks?**
(4) python3 $S approve-gate add-version-flag how …
(5) … --section gate … --gate release   **Do you approve the release gate?** … Production approval is never recorded here
(6) python3 $K/karvey-state.py approve-gate add-version-flag release --by "…" --role human …
```

## Evidence

`spec.json:gate_outcomes`: `approved what [requirements]`, `approved how [architecture, tasks]`, `approved release [qa]`
— three entries. `approvals`: requirements, architecture, tasks, qa all `approved: true, role: human, ref: D-1`
(architecture and tasks share the *how* record); no `approvals.prod`. `skipped`: `mockup`, `design_graphic` =
`lane:standard`, `infra` = "no cloud resources: local CLI, cloud.provider none". `judge_runs`: requirements (domain,
methods), architecture (methods, security), qa (fiscal, security — twice, first review and the re-review after
iterate). No `--kind plan-exception` outcome was needed.

## Expected lines

| Expected | Result |
|---|---|
| exactly three gate questions: *what* (after requirements), *how* (after tasks), *release* (after qa) | PASS |
| no "shall we advance?" anywhere | PASS — one caveat: after the *release* approval the agent asked before starting deploy, because turn 6's "Approve and advance" contradicted turn 5's "stop before deploy" (a prompt artefact of this run, not a second gate question) |
| architecture records `generated` and continues to tasks with no question; infra skipped with a reason; mockup / design_graphic `lane:standard` | PASS |
| each gate question preceded by `--section gate --gate {what,how,release}`; judges before *what* (2), *how* (architecture, 2), *release* (fiscal + 1) | PASS |
| three `approved` outcomes `what`, `how`, `release`; architecture and tasks share the approval; no `approvals.prod` | PASS |
| plan-rule questions, if any, recorded as `--kind plan-exception`, not among the three | PASS (none arose) |

**Overall: PASS.** Plugin defects the agent reported and this iteration fixed: template requirements without
`REQ-…-NNN` ids made the trace see none (F-14 / BUG-53); `karvey-impl` never named the `Karvey-Change` trailer, so the
commits were rewritten later (F-27 / BUG-67); the incident rule's `### Regression` heading was not read by the
convergence check (F-39 / BUG-68); the evidence wrapper wrote the home path into `evidence.jsonl` (F-40 / BUG-69).
