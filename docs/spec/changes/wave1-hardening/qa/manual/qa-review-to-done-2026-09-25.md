# Manual script: qa-review-to-done — 2026-09-25

**Script:** `plugins/karvey/tests/manual/qa-review-to-done.md` (REQ-W1-084) · **Result: PASS**

## Execution

- **Executor:** maintainer agent, headless under D-19 / D-28, 2026-09-25. The agent under test is a separate
  `claude -p` session per run, with the branch plugin and without the user settings.
- **Throw-away repo:** `git init -q --bare "$SCRATCH/<name>.git"`, `git init -q -b main "$SCRATCH/<name>"` with
  `origin` pointing at the bare repo. The fixture change state was written only through
  `plugins/karvey/scripts/karvey-state.py` (`init`, `advance`, `generated`, `approve --role human --ref D-01`,
  `skip`), never by hand. `$SCRATCH` is a `mktemp -d` directory, deleted after the run.
- **Agent-under-test command** (every turn; multi-turn scripts add `--resume <session>`):

```bash
cd "$SCRATCH/<name>" && claude -p [--resume <session>] \
  --plugin-dir <repo>/plugins/karvey --setting-sources project,local \
  --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent,Skill,TodoWrite,WebFetch" \
  --output-format stream-json --verbose "<prompt>"
```

## Setup done

- Markdown tracking, trunk flow (`main`/`main`). Change `fixture-04` at phase `qa` on `feature/fixture-04`:
  requirements, architecture and tasks consistent with a small `app/strutil.py` (4 helpers, 5 unit tests
  passing), `docs/test_evidence.md` PASS, CHANGELOG `[Unreleased]` line, empty `findings.md`.
- `PLAN.md`: 8 tasks at `👀 review`, both Features at `👀 review`, Epic at `👀 review`.
  `grep -c '👀 review' PLAN.md` → **12** (8 tasks + 2 Features + Epic + the legend line).
- A first attempt used a fixture whose requirements did not match its code; QA correctly refused it. That
  attempt is discarded (fixture error, not a script result); the fixture above is the one evaluated.
- Variant B: after A, the QA result committed; `advance fixture-04 deploying` through the state tool;
  `E1.F2.T3` put back at `👀 review` by hand; the feature branch merged into `main` and pushed.

## Prompts

- A: `/karvey:karvey-qa fixture-04` → resumed with `aprobado — approve QA as is. Approver: Fixture Tester, ref D-03.`
- B (new session): `/karvey:karvey-archive fixture-04`

## Transcript excerpt

A, turn 2:

```
TOOL Bash: python3 <repo>/plugins/karvey/scripts/karvey-state.py approve fixture-04 qa --by "Fixture Tester" --role human --ref "D-03"
  fixture-04: approvals.qa approved by Fixture Tester (human, ref D-03)
Approval recorded. Now I'll flip the Tasks and Features from 👀 to ✅ in PLAN.md. The Epic stays 👀, because it only reaches done at archive.
```

B:

```
**What blocks the archive**
1. **A task is still in review.** In `docs/spec/changes/fixture-04/PLAN.md`, E1.F2.T3 is `👀 review`. Commit `<sha>` put it back by hand after QA approval. QA has to move it to done, or say why it's in review.
2. **Findings haven't converged.** …
3. **There's no record of the release.** …
```

## Evidence

| Measure | Value |
|---|---|
| A: `grep -c '👀 review' PLAN.md` before / after | 12 / 2 (after: the Epic line and the legend only) |
| A: tasks and Features at `✅ done` after | 8 tasks + 2 Features |
| A: `karvey-state.py validate docs/spec/changes/fixture-04/spec.json` | `OK … (0 errors, 0 warnings)` |
| B: Epic line of `PLAN.md` before / after | `## Epic: E1 String helpers — 👀 review` / unchanged |
| B: change directory | not moved to `archive/` |

## Expected lines

| Expected | Result |
|---|---|
| A: after `approvals.qa.approved` becomes true (via `karvey-state.py approve fixture-04 qa …`), all 8 tasks and their Features are `✅ done`; none stays at `👀 review` | PASS |
| B: archive lists the one task still at `👀 review` by its id | PASS: `E1.F2.T3` named |
| B: does **not** mark the Epic done | PASS |

**Overall: PASS.** QA also left four Low findings open in the fixture; archive listed them as a second blocker,
which the Expected lines do not cover.
