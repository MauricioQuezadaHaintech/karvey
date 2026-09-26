# Manual script: judges-gate — 2026-09-26

**Script:** `plugins/karvey/tests/manual/judges-gate.md` (REQ-W2-022, 027, 029) · **Result: FAIL (one line; the
fixture's deliberate gap did not survive to the judges) — every other line PASS**

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

- `project.json` markdown, no `judges` key. Change `demo-judges` (lane standard) at `architecture`, requirements
  approved; `requirements.md` (three EARS requirements) and an `architecture.md` whose `audit-writer` appends the
  issued session token to `logs/audit.log`, with no control named. No other model family's CLI on `PATH`.

## Prompts

1. `/karvey:karvey-architecture demo-judges`
2. `Request changes. Reason: "judges check only". Accept G-1..G-4 as proposed.`

## Transcript excerpt

```
**I changed one thing from the draft that was already there.** It had `audit-writer` writing the issued session
token into `logs/audit.log`. That breaks the Karvey security rules … The audit line now holds {event, user_id, jti, …}
TOOL Bash: python3 $P/karvey-state.py generated demo-judges architecture; python3 $P/karvey-judges.py inputs demo-judges architecture --json
TOOL Agent (Explore): "You are an independent reviewer … lens: security … Inputs (read only these files): …/architecture.md, …/requirements.md … Do not edit any file."
TOOL Agent (Explore): "… lens: methods …"          (both in one assistant message)
python3 $P/karvey-judges.py collect demo-judges architecture --results $T --model <model> --intra-model --json && python3 $P/karvey-state.py judge-run demo-judges architecture --from $T/runs.json
## Judges (advisory, both on this model because no other model's CLI was available)
| security | concerns | 1 High … | methods | concerns | 2 High …   — the three Highs shown in full
```

## Evidence

`inputs` → `lenses: [security, methods]`, inputs `architecture.md`, `requirements.md` (plus goal and rubric). The two
`Agent` prompts carry the rubric section, the two paths and the read-only rule — no session summary, no draft text.
`spec.json:judge_runs`: two records (`methods`, `security`) with `model` set, `intra_model: true`, `estimated: true`.
`findings.md`: F-01..F-18, origins `judge:security` / `judge:methods`, all `open`; F-13 (`judge:security`) reads "REQ-03
does not forbid tokens … An earlier draft logged the token" citing `requirements.md:5`. `gate_outcomes`:
`changes_requested` for architecture with reason `judges check only`; phase stays `architecture`. The judges were
read-only subagents; the only files written after they ran were `findings.md` and `spec.json`.

## Expected lines

| Expected | Result |
|---|---|
| `karvey-judges.py inputs demo-judges architecture --json` before the gate; inputs exactly requirements + architecture + goal + rubric | PASS |
| **two** subagents in one message, one per lens, given paths and the rubric only | PASS |
| no subagent edits a file; only `findings.md` and `spec.json` change after the judges ran | PASS |
| `collect … --intra-model` then `judge-run … --from …`; two `judge_runs` with `model` and `intra_model: true` | PASS |
| an `open` `judge:security` row citing the token-logging line of `architecture.md` | **FAIL**: the architecture skill removed the token from the audit line while writing the document, before the judges ran; the nearest row (F-13) cites `requirements.md:5` |
| gate summary names both lenses, verdicts, intra-model; Critical/High shown in full | PASS |
| *Request changes* recorded with `outcome … changes_requested` and the reason; phase stays `architecture` | PASS |

**Overall: FAIL on one line, a fixture defect, not a method defect:** the architecture skill is told to apply the
security rules while writing, so a gap planted in the draft it rewrites is fixed before any judge reads it. Logged as
F-29 (emergent, Low): the script needs a gap the author cannot fix silently (e.g. a requirement that asks for it),
deferred to the backlog. The judge mechanics this script exists for (REQ-W2-022/027/029) all passed.
