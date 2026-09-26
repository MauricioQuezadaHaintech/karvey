# QA runs the real security tools and cites them; the pipeline gets a security-scan stage (REQ-W2-064, REQ-W2-068)

> Manual agent-behaviour script (architecture §6.4 of wave2-structural, E1.F8.T3). Run it in a real session
> started with the branch plugin (`claude --plugin-dir <worktree>/plugins/karvey`), inside a throw-away repo under
> `$SCRATCH` (`git init -q -b main "$SCRATCH/<name>"`), never in this repo or in the user's configuration.
> It FAILS if any line under **Expected:** is not observed: file the evidence under
> `docs/spec/changes/<change>/qa/manual/<script>-<date>.md` with PASS/FAIL and log a failure as a finding;
> never edit the script to match what happened.

## Setup
- Real scanners installed on `PATH` (not the unit-test stubs): at least one secrets scanner of the catalogue
  (e.g. gitleaks) and one static analyser (e.g. bandit or semgrep). **No** IaC scanner and **no** dependency
  scanner on `PATH`.
- A small Python project with `requirements.txt`, one module with an `assert`-based check (a static-analysis
  finding), a `tests/fixtures/fake_key.pem` holding an obviously fake key, and **no** IaC files.
- `docs/spec/project.json` with `management.tool: markdown`; one change `demo-sec` at phase `qa`, lane
  `standard`, with `architecture.md` that names a CI pipeline.

## Prompt
1. `/karvey:karvey-qa demo-sec` and let it run Dimension 1.
2. When it reports the fixture key, answer "that key is a test fixture, suppress it".
3. `/karvey:karvey-infra demo-sec` (a throw-away run: answer *Request changes* at the gate).

## Expected:
- Before any model reading of the code, the agent runs `karvey-security-scan.py run demo-sec --json`.
- The review cites, per category, the tool, its version, the exact command and the findings by severity, plus
  an `evidence.jsonl:{line}`; `evidence.jsonl` holds one `security:{category}:{tool}` line per tool run, with
  hashes and no output text.
- `sca` reads `not evaluated (no tool)` in the review (a `requirements.txt` exists, no scanner) and `iac` reads
  `not applicable`; neither is written as "pass" or "no issues".
- The fixture key becomes an entry of `qa/suppressions.json` with the file path, a reason and a scope, and
  `karvey-security-scan.py validate-suppressions demo-sec` exits 0.
- The review states what the tools cannot cover (authorisation per object, tenant isolation, business logic)
  and reviews those by reading the code.
- The infra run writes an `infra.md` whose pipeline has a stage named `security-scan` with the four categories.
  Removing that stage from `infra.md` by hand makes `karvey-context.py --section gate --change demo-sec
  --gate how` list `pipeline without a security-scan stage` under deviations.

## Evidence
- The transcript lines with the scan command and the Dimension 1 citations.
- `evidence.jsonl`, `qa/suppressions.json`, the `infra.md` stage and the gate summary line.
