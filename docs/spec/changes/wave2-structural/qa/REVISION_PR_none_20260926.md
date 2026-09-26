# Code Review — wave2-structural: feature/wave2-structural → main

> Revision 2 (2026-09-26): the fiscal judge failed revision 1 (its cited evidence lines were not committed, no
> tool ran over the diff, several claims uncited — F-46 .. F-60); the security judge added F-61 .. F-70. This
> revision cites every claim below by `evidence.jsonl:{line}`, a `file:line` or a file of `qa/`.
> Revision 3: the fiscal's re-check of revision 2 (F-72 .. F-81) — the missing runs recorded (`evidence.jsonl:44`–`48`),
> the red run transcribed (`qa/red-run-2026-09-26.md`); `evidence.jsonl` stores hashes, not output, and no commit SHA
> (F-32, deferred), so the counts quoted from a run are transcribed from its output.

## General Information
- Repository: karvey (Karvey Method plugin)
- Stack: Python 3 stdlib scripts, bash hooks, static HTML/JS page
- Source branch: `feature/wave2-structural` · reviewed commit `9cb18d4` (the suites of
  `evidence.jsonl:34`–`43` ran on it)
- Target branch: `main` (trunk); diff base for this review: `origin/feature/wave1-hardening` with three-dot
  semantics (`git diff origin/feature/wave1-hardening...HEAD`): this branch was cut before the newest Wave 1
  commits, so a two-dot diff would show those reversed
- Date: 2026-09-26
- Commits included: 87 up to `44169ec`; every one carries `Karvey-Change: wave2-structural` (`evidence.jsonl:45`,
  a loop over `merge-base..HEAD` that exits 1 on the first commit without it; the release gate re-checks at deploy)
- No PR yet: the file name carries `none`

## Executive Summary
All 88 requirements of the change are green (`test_evidence.md`, "88 PASS · 0 FAIL · 0 PENDING"; the five
manual-only ones closed by the headless agent runs under `qa/manual/`) and the trace reads `coverage: 97/97`
(`evidence.jsonl:44`, `--write --check`, which regenerated the committed `traceability.md`). This QA — the manual runs, subagent reviewers for dimensions 1–4, the second opinion and the
two QA judges — found **30 defects** in the change (bugs and spec-gaps); **29 are fixed** with regression tests
that were red on the pre-QA scripts (`evidence.jsonl:30`, transcribed in `qa/red-run-2026-09-26.md`: 66 of 69 red, the other three
guard against over-matching) — 28 incidents, BUG-49 .. BUG-77 except BUG-66 (the impl finding F-05). **One High stays open for the owner: F-61** (whether one project-wide
production approval may cover every change of a release manifest, against the Wave 1 rule that a production
approval is of one change). Sixteen emergent items are deferred as backlog candidates with their reasons.
**Security gate: NOT passed while F-61 is open.** Second opinion: same model family (declared), FAIL on its first
pass (`qa/second-opinion-2026-09-26.md`).

## Findings by Dimension

### 1. Security
*Tools first* — `karvey-security-scan.py run wave2-structural` over the repository at the reviewed commit:

| Category | Tool | Command | Findings | Evidence | Status |
|---|---|---|---|---|---|
| secrets | gitleaks 8.30.1 | `gitleaks detect --no-banner --source . --report-format json --report-path docs/spec/changes/wave2-structural/qa/security-secrets.json --exit-code 1` | 0 | `evidence.jsonl:42` | evaluated |
| sast | bandit 1.9.4 | `bandit -r . -f json -o docs/spec/changes/wave2-structural/qa/security-sast.json -q` | medium 6 · low 78 | `evidence.jsonl:43` | evaluated |
| sca | — | — | — | — | not applicable (no manifest of a dependency ecosystem) |
| iac | — | — | — | — | not applicable (no IaC file) |

Triage of the SAST findings (`qa/security-sast.json`): all false positives or accepted patterns, each recorded in
`qa/suppressions.json` with its reason and scope (`validate-suppressions`: 8 entries, 0 problems — `evidence.jsonl:46`) — B404/B603/B607
(subprocess with an argv list, tools from PATH), B105 (names containing "token" that are not secrets:
`karvey_hooks.py:54`, `lint-plugin.py:651`, four test fixtures), B110 (audit logging that must not change a guard
decision: `guards.py:1235`, `karvey_hooks.py:227`, `:239`), B314/B405 (the size-capped JUnit parse of
`karvey-trace.py:269`), B108 (fake `/tmp/…` strings in unit tests). Running the catalogue here exposed BUG-77: the
tools received absolute user paths; fixed before the runs cited above.

Personal data: `git diff <merge-base> -- plugins docs/karvey.html` searched for home paths, organisation names and
e-mail addresses — the only hit is the licence footer every skill carries (`evidence.jsonl:31`); without it,
none (`evidence.jsonl:32`). The search covers the plugin and the page; the responsible human's e-mail in
`CHANGELOG.md` lines is F-70 (deferred).

*Model review (OWASP Top 10 + STRIDE)* — subagent D1, the manual runs, the second opinion and the security judge:

| # | File | Sev | Finding | Status |
|---|---|---|---|---|
| 1 | `scripts/karvey-postdeploy.py` | High | `pass` with every probe refused (STRIDE-D / A09) | fixed, BUG-52 |
| 2 | `scripts/karvey-evidence.py` | High | argv secrets committed to `evidence.jsonl` (A02) | fixed, BUG-55; query / header secrets BUG-75 |
| 3 | `scripts/karvey-state.py` (`lane raise`) | High | `docs` → `ops` counted as a raise, QA optional without the human (STRIDE-E) | fixed, REQ-W2-016 rev. 1 + BUG-62 |
| 4 | `scripts/karvey_lib/judges.py` | High | forgeable `findings.md` rows through the lens (STRIDE-T) | fixed, BUG-56 |
| 5 | `scripts/karvey-state.py` (`approve-gate … release`, `approve prod`) | High | a project-wide prod marker approved production of any change and stayed live | fixed, BUG-70 |
| 6 | `scripts/karvey-state.py` (`approve prod --manifest`) | High | one project-wide prod marker records production for every change of the manifest | **open, F-61 — owner decision** |
| 7 | `scripts/karvey-state.py` (`lane lower`) | Medium | project-wide plan marker lowered any lane, not consumed | fixed, BUG-74 |
| 8 | `scripts/karvey-state.py` (manifest) | Medium | a failed marker consume was swallowed | fixed, BUG-73 |
| 9 | `scripts/karvey_lib/judges.py` | Medium | a judge could declare itself cross-model | fixed, BUG-76 |
| 10 | `scripts/karvey-postdeploy.py`, `karvey-evidence.py`, `karvey-security-scan.py` | Medium | URL credentials, the home path, absolute user paths in committed evidence | fixed, BUG-52, BUG-69, BUG-75, BUG-77 |
| 11 | `scripts/karvey-release-gate.py` | Medium | manifest mode from the working copy only | fixed, BUG-59 |
| 12 | `scripts/karvey-id.py` | Medium | unsafe stale-lock takeover | fixed, BUG-60 (a narrow window left: F-45) |
| 13 | `scripts/karvey_lib/guards.py` | Medium | `git commit -am` bypassed a blocking trailer guard | fixed, BUG-63 |
| 14 | `manifest.py`, `karvey-state.py` (`deployed --attested`), evidence files | Medium | trust in files anyone can edit (QA state from the working tree, any D-NN for an attested deploy, stale probe files, argv name matching) | deferred F-31, F-32, F-44 |
| 15 | `karvey-state.py` (`lane set`) | Medium | `hotfix` / `ops` at init without admission criteria | deferred F-35 (with F-64) |
| 16 | `karvey-judges.py`, trailer guard, CHANGELOG | Low | diff to judges unredacted; abbreviated long options; e-mail in CHANGELOG lines | deferred F-36, F-68, F-70 |

Read without a tool: prod stays human-only (`karvey-state.py` refuses `--role auto` for prod in `approve`, the
release gate and the manifest — `test_state_gates.py` `Release.test_REQ_W2_040_auto_refused_when_prod_would_be_written`,
`ProdManifest.test_auto_refused`); no `shell=True` anywhere (`test_no_shell_true.py`, in the unit run at
`evidence.jsonl:34`); the post-deploy probe follows redirects only to the same origin
(`test_postdeploy.py`, same run).

### 2. Code errors
All fixed with red-first tests (`evidence.jsonl:30`, `qa/red-run-2026-09-26.md`): zone lost on fractional seconds (BUG-54); tracebacks with
the tools' "refused" / "regression" exit codes in `karvey-trace.py` and `karvey-postdeploy.py`, and crashes of
`--metrics` (BUG-58, BUG-52, BUG-57); negative lead time and hidden zone-less deploys (BUG-57); wrong
`evidence.jsonl:{line}` citations (BUG-59, BUG-55); non-ASCII digit cites (BUG-56); `karvey-id` numbers inflated
or burnt (BUG-60); NaN costs (BUG-61); a merged gate that passed a phase the human sent back (BUG-51, a regression
of BUG-48). Deferred: an unknown lane gives exit 5 in `karvey-judges.py` (F-38).

### 3. Consistency
Fixed: lint L-47 declared in the architecture but missing (BUG-64); `schema.strict` from the registry ignored and a
missing lane never an error under strict (BUG-61, remedy text BUG-72); the requirements template gave ids the trace
cannot read, so `0/0` read as a pass (BUG-53); the incident rule's `### Regression` heading unread (BUG-68); the
impl skill silent on `Karvey-Change` (BUG-67); the deploy skill's regression item against REQ-W2-078 (BUG-49); the
retro skill without a place for the owner (BUG-50); a false contract gap on the *how* gate (BUG-65). Lint is green
over all 51 checks (`evidence.jsonl:36`; the 51 are listed by `lint-plugin.py --list`, `evidence.jsonl:48`). The D3 reviewer also compared every script command a skill names with
the scripts' `--help` and found no mismatch — that check is the reviewer's report, not a recorded run. Deferred:
helpers duplicated in 3–4 scripts (F-33).

### 4. Impact on existing modules
A Wave 1 `spec.json` and `project.json` (`git show origin/feature/wave1-hardening:` of both, into a scratch
root) validate unchanged in advisory mode: 0 errors, 2 warnings (`evidence.jsonl:33`, counts transcribed). A spec without `lane` stays `legacy` with granular gates in 3.13; under strict (4.0) it is
an error whose remedy (`validate --fix --accept-proposed`) works at any phase (`test_state_validate.py`
`StrictModeFromRegistry`). The prod-gate hook now evaluates the manifest in `warn` mode on production merges and may
print a "not evaluated" line (F-34, deferred). The trailer guard stays `off` by default.

### 5. Environment variables
New in the diff: `KARVEY_ID_LOCK_WAIT_S` (lock wait of `karvey-id.py`, default from `defaults.json`). Outside
`karvey-id.py`, its tests and the records, nothing names it (`evidence.jsonl:47`); it has a fallback.

### 6. Versioning
- `unreleased-section`: `CHANGELOG.md` `[Unreleased]` carries one line per task / fix, the last one for this
  test/QA iteration (BUG-49 .. BUG-77).
- `one-bump-per-release`: no bump in the diff (3.11.4 everywhere); the number is set at release.
- `versions-agree`: lint L-12 checks the version files (green in the lint run, `evidence.jsonl:36`). For the
  release: the bump must also cover Wave 1's unreleased 3.12.0 and set `defaults.json:pre_3_12_history.released_on`.
- `changelog-why`: each line names the responsible human, the AI model and the why (lint L-13, same run).

### 7. Second opinion cross-model
Same model family, clean context, adversarial (declared; lower diversity) — full record in
`qa/second-opinion-2026-09-26.md`. First pass FAIL: its High became BUG-70 (release gate, `approve prod`) and its
manifest half is **F-61, open for the owner**; two Mediums fixed (BUG-71, BUG-72); the rest deferred (F-44, F-45).

### 8. Visual audit (implemented vs design-spec)
Static audit of `docs/karvey.html`, the only UI in the diff: the English, Spanish and Portuguese blocks carry the
same counts (33 skills = 1 + 13 + 19 support, 26 rules), each with 26 rule rows and 19 support cards; the counts
are pinned by `test_page_static.py` `CurrentCounts` (unit run `evidence.jsonl:34`) and the page tests pass 22/22
(`evidence.jsonl:38`). No deviation.

### 9. Standards conformance (golden path)
The project declares no engineering standards (`docs/spec/project.json` has no `standards`; there is no
`docs/spec/standards/`): **not evaluated**.

## QA judges (advisory)
`karvey-judges.py inputs wave2-structural qa --base origin/feature/wave1-hardening` → lenses `fiscal`, `security`;
both intra-model, recorded in `spec.json:judge_runs` (US$ 2.50 for the change so far, estimated).
- **fiscal: fail** on revision 1 — 15 rows (F-46 .. F-60): 14 accepted and resolved by revision 2, 1 rejected
  (F-60: the review never claimed a CI run). **fiscal: concerns** on revision 2 — 10 rows (F-72 .. F-81): 7
  resolved by revision 3, 3 accepted as the evidence design's limits (no SHA, hash-only lines: F-32 deferred) or
  an unrecorded reviewer report stated as such.
- **security: concerns** — 10 rows (F-61 .. F-70): F-62, F-63, F-65, F-66, F-67 fixed (BUG-73 .. BUG-76); F-69
  resolved by running the tools; F-64, F-68, F-70 deferred; **F-61 open**.

## Summary Table by Severity (defects of the change found at test and QA)
| Severity | Found | Fixed | Deferred | Open |
|-----------|---------|---------|---------|---------|
| Critical | 0 | 0 | 0 | 0 |
| High | 10 | 9 | 0 | 1 (F-61) |
| Medium | 23 | 18 | 5 | 0 |
| Low | 13 | 2 | 11 | 0 |

## Pre-merge checklist
- [x] All critical findings resolved (none)
- [ ] All high findings resolved — **F-61 open** (owner decision)
- [ ] Security gate passed — blocked by F-61
- [x] Second opinion executed and integrated (intra-model, declared)
- [x] Visual audit: no deviation
- [x] Standards conformance: not evaluated (no standards declared)
- [x] Environment variables verified
- [x] Tests: pass — unit `evidence.jsonl:34`, regression `:35`, guard tables `:40`, hook commands `:41`, page `:38`, run on the clean tree of `9cb18d4` (the evidence line has no SHA: F-32); red on the pre-QA scripts `:30`
- [x] Coverage: 97/97 (pass, mode warn) — `evidence.jsonl:44` (`traceability.md` regenerated)
- [x] Lint 0 errors (`:36`) · validate --all 0 errors (`:37`)
- [ ] Production build: not evaluated (no build step; the plugin ships as source)
- [ ] CI for the reviewed commit: not run (no PR yet)

## Areas requiring manual testing
- The seven agent-behaviour scripts: run headless, evidence under `qa/manual/`; two script fixtures need rework
  (F-29, F-30).
- CI on the PR (ubuntu / macOS × 3.9 / 3.12, page, windows-advisory).
