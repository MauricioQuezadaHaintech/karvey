# Manual script: security-tools-present — 2026-09-26

**Script:** `plugins/karvey/tests/manual/security-tools-present.md` (REQ-W2-064, 068) · **Result: PASS on the
QA half; the infra half could not run on the script's fixture (change at `qa`) and PASSED on a variant fixture**

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

- Real scanners on `PATH`: gitleaks 8.30.1 and bandit 1.9.4 (a scratch virtualenv); no IaC and no dependency
  scanner (`semgrep`, `osv-scanner`, `pip-audit`, `trivy`, `checkov` absent).
- Python project: `requirements.txt` (`requests==2.31.0`), `app/orders.py` with an `assert`-based admin check,
  `tests/fixtures/fake_key.pem` (a truncated, obviously fake RSA key), no IaC files. `project.json` markdown; change
  `demo-sec` (lane standard) walked to `qa`; `architecture.md` names a GitHub Actions pipeline.
- Variant for the infra half (new repo `security2`): same code; `project.json` adds `git_platform: github`, `cloud.provider:
  azure`, `iac_tool: bicep`; `demo-sec` walked to `infra` (architecture approved) and `architecture.md` adds a
  `## Cloud Infrastructure` section.

## Prompts

1. `/karvey:karvey-qa demo-sec` · 2. "that key is a test fixture, suppress it" · 3. `/karvey:karvey-infra demo-sec`
   (script fixture: refused, see below) · variant: `/karvey:karvey-infra demo-sec` → "Request changes: throw-away run,
   infra review only." · then, by hand, `security-scan` renamed away in `infra.md` and the gate summary run.

## Transcript excerpt

```
TOOL Bash: for f in requirements.txt app/orders.py … ; do cat -n $f; done        (Step 0: the change's files)
TOOL Bash: … lane-check …; python3 $K/karvey-security-scan.py run demo-sec --json; … validate-suppressions demo-sec --json
| secrets | gitleaks 8.30.1 | `gitleaks detect --no-banner --source . --report-format json …` | high: 1 | `evidence.jsonl:1` | evaluated |
| sast | bandit 1.9.4 | `bandit -r . -f json -o …/qa/security-sast.json -q` | low: 1 | `evidence.jsonl:2` | evaluated |
- **Dependency scan:** not evaluated, because no scanner is installed. … - **Infrastructure-as-code scan:** not applicable
**Model review of what the tools cannot see:** IDOR / object-level authorization … Tenant/user isolation … Business-logic abuse …
(3, script fixture) I stopped before running `advance demo-sec infra` … The change is past infra. … Moving back is `reopen`
```

## Evidence

`evidence.jsonl`: one line per tool run, labels `security:secrets:gitleaks` and `security:sast:bandit`, argv, exit,
hashes, byte counts — no output text. `qa/suppressions.json`: `{tool: gitleaks, rule: private-key, path:
tests/fixtures/fake_key.pem, reason: …, scope: "this file only …"}`; `validate-suppressions` → 1 entry, 0 problems
(exit 0). The agent triaged the key as a false positive on its own (REQ-W2-066 has the model triage) and recorded the
human's confirmation in turn 2. Variant `infra.md`: `### \`security-scan\` stage (REQ-W2-068)` with secrets / sast /
sca / iac rows. After renaming the stage away: `karvey-context.py --section gate --change demo-sec --gate how` →
`deviations: pipeline without a security-scan stage (infra.md; REQ-W2-068)`.

## Expected lines

| Expected | Result |
|---|---|
| `karvey-security-scan.py run demo-sec --json` before any model reading of the code | PASS in substance: the scan was the first analysis step; the change's files were read before it by Step 0 of `karvey-qa` (it reads the diff by design), so the literal "before any reading" cannot hold — F-30 |
| per category: tool, version, command, findings by severity, `evidence.jsonl:{line}`; one `security:{category}:{tool}` line per tool, hashes, no output | PASS |
| `sca` = `not evaluated (no tool)`, `iac` = `not applicable`; neither "pass" | PASS |
| fixture key → `qa/suppressions.json` entry with path, reason, scope; `validate-suppressions` exits 0 | PASS |
| states what tools cannot cover and reviews it by reading | PASS |
| infra run writes `infra.md` with a `security-scan` stage (four categories); without it the *how* gate lists the deviation | script fixture: not runnable (infra is behind `qa`; the agent rightly refused); variant: PASS |

**Overall: PASS with two script defects logged as F-30 (emergent, Low):** the infra half needs a change at `infra`, not
`qa`, and the "before any model reading" wording conflicts with `karvey-qa` Step 0. Two plugin defects surfaced here
too: the *how* gate listed "post-deploy verification contract: missing / rollback: missing" although `infra.md` held
complete `karvey-postdeploy` blocks (F-26 / BUG-65, fixed), and QA's `coverage: 0/0` read as a pass (F-14 / BUG-53, fixed).
