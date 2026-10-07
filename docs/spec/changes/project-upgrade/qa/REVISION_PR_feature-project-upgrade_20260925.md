# Code Review — project-upgrade: feature/project-upgrade → main

## General Information
- Repository: karvey (the Karvey plugin; public)
- Stack: Claude Code plugin: Python 3 stdlib (`karvey_lib`, scripts), bash hooks, Markdown skills and rules
- Source branch: `feature/project-upgrade`
- Target branch: `main` (trunk: integration = production; the change branched from `feature/wave1-hardening`,
  so the range reviewed is the change's own: `390e6cb..1e151b6`, the merge base with `origin/feature/wave1-hardening`)
- Date: 2026-09-25
- Commits included: 33
- Files modified: 55 (+8348 / −30)
- Reviewer: maintainer agent (Claude Opus 5.5), headless under D-21 · human owner: Mauricio Quezada Ibáñez
- Method: dimensions 1–4 by four parallel read-only reviewer subagents (each reproduced its findings in
  throw-away repositories under the scratch dir), 5, 6 and 9 in the main context, 7 by an adversarial subagent
  (intra-model fallback), 8 not applicable. Consolidated inbox: `../findings.md` (F-11..F-30).

## Executive Summary

The change adds a once-per-version, per-clone offer at session start and a deterministic upgrade engine, tool and
skill. The engine's security controls held under review: argv-only git, `check_branch` on every project value,
path confinement with realpath and symlink checks, compare-and-swap atomic writes, a preview digest covering every
planned edit, no writes under the home, and an audit log without targets. **No critical or high security
finding: the security gate passes.**

After deduplication across dimensions there are **20 QA findings: 0 critical, 3 high, 8 medium, 9 low**
(11 bug, 7 spec-gap, 2 emergent). The three highs were data and workflow bugs in `legacy-shims` and the
journal:
- it deleted a nested worktree's shim (F-11);
- it rewrote a git-ignored `settings.local.json`, which then could not be committed (F-12);
- a stale journal broke every second commit after a deletion (F-13).

They were reproduced by two independent reviewers. All 11 bugs were routed through the iterate micro-loop
(fix → regression test → full gate) in this phase, each with a regression test that fails on the reviewed code
(13 of 13 new tests failed before the fix).

**Verdict: NOT APPROVED yet.** QA itself is not approved here (the owner approves QA). Convergence is not
reached either: 7 spec-gaps (F-21..F-27, plus F-08 from test) are open for `/karvey-iterate`. The most visible
is F-21: a person without any statusline gets the offer on every version, because REQ-UP-023 and REQ-UP-005
contradict each other.

## Findings by Dimension

Each finding is listed once, under its primary dimension. Full text, reproduction and routing: `../findings.md`.

### 1. Security (OWASP Top 10 2021 + STRIDE)

Security findings: 0 critical, 0 high, 3 medium, 6 low (they overlap with other dimensions).

| # | Where | Severity | Type | OWASP / STRIDE | Problem | Resolution |
|---|---|---|---|---|---|---|
| F-20 | `skills/karvey-upgrade/SKILL.md` steps 5, 9, 10 | medium | bug | A03 Injection / Tampering | The person's words reached bash through `--answer "…"`, `printf '…' > "$VALUES"` and a double-quoted `--body` (the PR body contains backticks) | fixed: `--values -`, `--answer-file -` quoted heredocs, `--pr-body-file` + `--body-file`; `RegressionProjectUpgradeStdinValues` |
| F-19 | `upgrade_steps.py` `_strip_hook_entries`; `upgrade.py` `GIT_READ_ALLOW` | medium | bug | Tampering (removes a guard) / Elevation (latent) | Any command containing `plan-gate.sh` was removed (a person's own hook); `git show --output=<file>` was an allowed read | fixed: exact project-copy match; `show` dropped, `--output`/`--exec`/`-c` refused |
| F-16 | `upgrade_steps.py` `_set_value`, `_check_block_values` | low | bug | A03 / Tampering | Any `notifications.*`/`management.*` key could be set; a `{change-id}` location skipped its check | fixed: proposal keys only, strings only, location checked with a sample id |
| F-25 | `upgrade.py` Probe; `karvey_hooks.upgrade_offer` | low | spec-gap | A04 / DoS | No size cap on project reads; the glob is not deadline-bound; the hook has no watchdog | open → iterate |
| F-26 | `lint-plugin.py` L-38 | low | spec-gap | Tampering (defense in depth) | The AST scan misses `Path.open("w")`, `os.open`, aliases and `probe.state` writers | open → iterate |
| F-27 | `project.state_dir` fallback | low | spec-gap | REQ-UP-016 | Outside git, the seen record goes to the XDG state dir under `$HOME` | open → iterate |
| F-28 | plan/apply text | low | emergent | prompt injection (relay) | Repository strings are relayed without control-character stripping | backlog |

Verified clean: argv-only subprocesses (no `shell=True`); `check_branch` + `git check-ref-format` on every branch;
fixed `refs/remotes/origin/` / `refs/heads/` bases; the commit message through a 0600 `-F` file with `--`
pathspecs; `confine()` (realpath, `..`, absolute, symlink escape, `FORBIDDEN_STATE` for approvals, ledger, seen,
journal and audit); the preview digest covering step, op, scope, path and both hashes; the hook's
`additionalContext` built only from `VERSION_RE` versions, a `shlex.quote`d path and fixed text, lines capped
at 300; the seen record 0600 in 0700 under the git dir, covered by protect-paths; audit lines without targets or
home content; home reads limited to 3 files and 1 MB, never written.

STRIDE summary: **S** none (no identity is claimed; `Picked-by` is an attribution the commit review sees);
**T** F-16, F-19, F-20 fixed; **R** audit `upgrade.seen/apply/commit`, and the commit body names the steps and
who picked them; **I** no secret or target logged; **D** F-25 open (low); **E** F-19 (`git show --output`) fixed.

### 2. Code errors

| # | Where | Severity | Type | Problem | Resolution |
|---|---|---|---|---|---|
| F-12 | `upgrade_steps.py` `SETTINGS_FILES`; `upgrade.py` `commit` | high | bug | A git-ignored `settings.local.json` was rewritten; `git add` refused it every time and left the index half staged | fixed (`test_f12_…`) |
| F-13 | `upgrade.py` `commit`, `_write`, `ensure_branch` | high | bug | The journal was never trimmed and outlived its branch: the second commit failed after a deletion and repeated earlier steps | fixed (`test_f13_…` ×2) |
| F-14 | `upgrade_steps.py` `legacy_shims_check` | medium | bug | A partial failure left the gate off and the re-plan said "satisfied" | fixed: flag → settings → delete, dangling entry = work (`test_f14_…`) |
| F-15 | `upgrade.py` `read_journal`, `_write_journal` | medium | bug | KeyError after files were written; an unwritable journal gave a traceback | fixed (`test_f15_…`) |
| F-17 | `upgrade.py` `apply` | low | bug | The branch was created and switched before the refusals | fixed: refuse first, roll back after a late refusal (`test_f17_…`) |

Verified clean: the exit codes (0/1/2/3/4) match the docstring and the skill; E-10, E-12, E-13, E-15, E-16, E-17
are handled as the architecture says; the seen write is locked and atomic (E-04); a malformed record counts as
absent (E-02); the hook's broad except gives one line; the degraded bash path is correct; the runner seeds the
record (E-27).

### 3. Consistency

| # | Where | Severity | Type | Problem | Resolution |
|---|---|---|---|---|---|
| F-30 | `architecture.md` §7, §12; `README.md`; `hooks/README.md`; `CHANGELOG.md` | low | bug | Company names in new public text; a README command that works only inside the plugin repository; the "any error" wording; a CHANGELOG line without Responsible and AI | fixed in the text |
| F-10 | `tests/unit/test_lint_plugin.py` | low | bug | `L39(L38)` ran the L-38 tests twice (found in test) | fixed |
| F-29 | `upgrade.py`, `karvey_hooks.py` | low | emergent | Duplicated git helpers, normalisers and version checks | backlog |

Verified clean: the CLI follows the shared `kl.EXIT_*` + `--json` envelope contract; every write goes through
`atomicio` and `pj.state_dir`; values go through `safe_values`; the catalogue goes through `schema_lite`;
the skill counts (33 = 1 + 13 + 19) agree in README, plugin README, `plugin.json`, `marketplace.json`, the
orchestrator and `support-skills.md`.

### 4. Impact on existing modules

| # | Where | Severity | Type | Problem | Resolution |
|---|---|---|---|---|---|
| F-18 | `upgrade_steps.py` `changes_in_flight_check` | medium | bug | The current phase's own pending approval counted as unmet, so every active project was offered every version | fixed (`test_f18_…`) |
| F-11 | `upgrade_steps.py` shim glob; `Probe.glob` | high | bug | It walked into nested worktrees and deleted another branch's file | fixed (`test_f11_…`) |
| F-21 | REQ-UP-023 vs REQ-UP-005 | medium | spec-gap | "No statusline" is `human`, so the plan is never empty | open → iterate |
| F-23 | `karvey-init` vs `enforcement-defaults` | medium | spec-gap | A fresh project gets an offer on its first session | open → iterate |

Verified clean: ss-01..23 keep their meaning (the runner seeds the record); `defaults.json` only gains keys;
protect-paths covers the new files; after `legacy-shims` the dispatcher's plan-gate is on at once (working
copy OR reviewed line); git-flow and prod-gate pass the literal upgrade push (after F-06); the hook never fetches
and writes only the `empty` record.

### 5. Environment variables

| Variable | Where | Fallback | Status |
|---|---|---|---|
| `KARVEY_TEST_UPGRADE_PROBE_MS` | `karvey_hooks.upgrade_offer` | `session.upgrade_probe_ms` = 1500 | tests only; it can only lower the budget (an offer, never silence) ✅ |
| `HOME` | Probe home reads | `os.path.expanduser("~")` | read only ✅ |
| `CLAUDE_PLUGIN_ROOT` / `CLAUDE_PROJECT_DIR` | skill, hook | the script's own tree / `$PWD` | as the existing hooks ✅ |
| `XDG_STATE_HOME` | `pj.state_dir` outside git (existing) | `~/.local/state` | existing behaviour; F-27 |

No Dockerfile or pipeline is involved (a local plugin; CI is the existing `lint.yml`, which needs no new variable).

### 6. Versioning

- `unreleased-section`: ✅ one `[Unreleased]` line per task commit, plus the test fix line and the QA fix line.
- `one-bump-per-release`: ✅ `plugin.json` stays 3.11.4 (only the description's skill count changed). The number
  moves at `karvey-deploy`; F-01 and F-04 track the `since` / fingerprint follow-ups for the release.
- `versions-agree`: ✅ L-12 passes (`plugin.json`, `marketplace.json`, `project.json:karvey_version`, top CHANGELOG
  release).
- `changelog-why`: ✅ every line of the change names the why; the test-phase line lacked "Responsible · AI" (fixed,
  F-30).

### 7. Second opinion cross-model

- **Mode:** Challenge (adversarial). **Model:** intra-model fallback (a Claude Opus 5.5 subagent with an
  adversarial prompt). No external model CLI (`codex`, `gemini`, `llm`) is installed and no external API key was
  used (as instructed), so the real model diversity is lower.
- **Verdict on the reviewed code: FAIL**, with 3 blocking, 3 major and 3 minor findings.
- **Agreements (high confidence):**
  - blocking #1 = D2 #4 → F-11;
  - blocking #2 = D2 #1 → F-12;
  - major #4 = D2 #2/#3 → F-13;
  - minor #7 = D1 #5 → F-17;
  - minor #9 ≈ D1 #3 → F-25.
- **New from the second opinion:**
  - blocking #3 → F-14;
  - major #5 (archived specs migrated) → F-22;
  - major #6 (a karvey-init project offered on its first session) → F-23;
  - minor #8 (dry-run base vs branch base) → F-24.
- **Discrepancies:** D3/D4 rated the statusline case (F-21) low/emergent and D2 rated it a medium spec-gap. It is
  recorded as a medium spec-gap, because REQ-UP-005's success scenario is unreachable for the common setup.
- **After the fixes:** every blocking item and major #4 is fixed with a regression test. Majors #5 and #6 are
  spec-gaps, because the spec itself must decide.

### 8. Visual audit (implemented vs design-spec)

Not applicable: no UI. Mockup and design-graphic were skipped ("no UI", `spec.json:skipped`), and there is no
`design-spec.md`. The session hook's text output is covered by the session tables and the E2E transcripts.

### 9. Standards conformance (golden path)

**Not evaluated:** `docs/spec/project.json` declares no `standards` and `docs/spec/standards/` does not exist, so
there is no `MUST` to check against. That is not conformance. As the architecture's Step 4B note records, the design
declares the wave1 conventions (stdlib only, `kl` exit codes and envelope, `atomicio`, `safe_values`,
`schema_lite`, the table runner). D3 verified them: they are followed, except for the duplicated helpers in F-29
(emergent).

## Summary Table by Severity

| Severity | Count | Fixed in this phase | Open |
|---|---|---|---|
| Critical | 0 | — | 0 |
| High | 3 | 3 (F-11, F-12, F-13) | 0 |
| Medium | 8 | 5 (F-14, F-15, F-18, F-19, F-20) | 3 spec-gaps (F-21, F-22, F-23) |
| Low | 9 | 3 (F-16, F-17, F-30) | 4 spec-gaps (F-24..F-27) + 2 emergent (F-28, F-29) |

Plus the test-phase findings: F-05, F-06, F-07, F-10 fixed; F-08 (spec-gap) and F-09 (emergent) open.

## Pre-merge checklist
- [x] All critical findings resolved (none)
- [x] All high findings resolved (F-11, F-12, F-13, with regression tests)
- [x] Security gate passed (OWASP Top 10 + STRIDE: no critical or high)
- [x] Second opinion executed and integrated (intra-model fallback, declared)
- [x] Visual audit: not applicable (no UI)
- [x] Standards conformance recorded as not evaluated (no standards declared)
- [x] Environment variables verified
- [x] Tests pass after the fixes: unit 870, regression 10, test-hooks 66, guard tables 396 runs, page 22,
  lint 0 errors (5 expected warnings), validate 0 errors
- [ ] Open spec-gaps routed by `/karvey-iterate` (F-08, F-21..F-27), then QA re-run
- [ ] QA approval by the owner (not recorded by the agent)

## Areas requiring manual testing
- **The offer's wording in an interactive session** (F-09): whether the model treats it as the plugin's notice
  and asks with AskUserQuestion. It was checked only headless, where AskUserQuestion is unavailable.
- **The PR step on a real host** (`gh` / `az` / `glab` authenticated): the E2E used a bare local origin, so the PR
  was offered as a command, not opened.
- **Two clones upgrading to the same version** (F-08): the second push is rejected. The recovery the person
  chooses is not specified.

---

## Re-run after karvey-iterate (2026-09-26) — dimensions D1–D4 on the new diff

- **Scope:** `cecab37..HEAD` on `feature/project-upgrade`: requirements rev. 2 (F-08, F-21..F-27; REQ-UP-003, 006,
  012, 013, 016, 020, 023, 026, 031 rewritten in place, the recommended option of each listed in `requirements.md`
  § Revision history for the owner), architecture rev. 2, tasks E1.F9.T1..T5, and the emergent F-09 and F-28 fixed.
  F-29 (duplicated helpers) and F-04 (fingerprint at the release) are deferred with their reason.
- **Method:** two read-only reviewer subagents in parallel, D1 + D2 and D3 + D4. Each reproduced its cases in
  throw-away repositories under the scratch directory, with an isolated HOME and git config. D5–D9 were not re-run:
  there is no new variable, no version change beyond `[Unreleased]`, no UI and no standards; the second opinion of
  the first review stands.
- **Result:** 9 new findings (F-31..F-39): 0 critical, 0 high, 3 medium, 6 low (8 bugs, 1 spec-gap). Every one is
  fixed in this iteration, each with a regression test that fails on the reviewed code where the defect is
  behavioural (verified by swapping the previous file back in for the L-38 and skill-fetch cases).

| # | Dim. | Severity | Problem | Resolution |
|---|---|---|---|---|
| F-31 | D1 | medium | F-28 covered only the plan; dry-run summaries, diff headers and report lines still printed project paths raw | `one_line` / `printable_block` at the report boundary |
| F-32 | D1 | medium | any `origin/chore/karvey-upgrade-<v>` became the base, even an unrelated branch, checked out silently | only when it builds on the integration branch, else refused; commits and files listed to the person |
| F-35 | D1/D3 | medium | L-38 gaps: `io.open`/`codecs.open`, `Path.rename`, `os.exec*`, star imports, `p = probe`, `getattr(probe.state, …)` | caught (6 more test cases); residual `.replace()` and computed `getattr` names are accepted limits of a static scan |
| F-33 | D1/D4 | low | the skill's fetch did not follow a force-push nor drop a deleted remote branch | pattern refspec with `+` and `--prune` |
| F-34 | D2 | low | the new walk skipped symlinked directories that the old `Path.glob` followed | followed while inside the root, once each |
| F-36 | D4 | low | a local upgrade branch behind the pushed one was not fast-forwarded (non-fast-forward push again) | fast-forward when strictly behind |
| F-37 | D4 | low | no tool signal for "outside git" in the skill | `plan --json` carries `in_git` |
| F-38 | D4 | low | `test-hooks.sh` called `write_seen` outside git (traceback); a `[karvey]` prefix on one refusal | helper tolerant; prefix removed |
| F-39 | D3 | low | stale sentences in the init skill, architecture (Probe allow-list, A-08, E-11), tasks, spec-delta, hooks README, a docstring | fixed in the text |

**Verified clean (re-run):**
- the rewritten requirements match `spec-delta.md` word for word, and match architecture rev. 2 and the code;
- "Ask ONE question", "no statusline → human", "archive included" (for the step) and the XDG seen record outside
  git are gone from the method text;
- the three `Probe.glob` patterns give the same results as before, and `.git`, `node_modules` and nested work
  trees are pruned;
- `PROJECT_READ_MAX` refuses without reading;
- the watchdog never lets a late probe record anything, and daemon threads do not block the exit;
- `write_seen` and the hook write nothing outside git;
- `ensure_branch`'s new keys have two consumers only (`branch`, `apply`);
- the F-24 refusal does not break the skill flow (branch before dry-run) or the manual script;
- exit codes and the envelope are reused;
- no organisation, person, id, home path or secret appears in the new public text.

**STRIDE delta:**
- **T** (Tampering): F-32 (content from another clone) and F-31 (relayed text) are fixed.
- **D** (Denial of service): F-25 is closed by the read cap, the pruned deadline-checked walk and the watchdog.
- **I** (Information disclosure): no change.
- **E** (Elevation of privilege): L-38 is stronger (F-26, F-35).

**Security gate: PASS** (no critical or high).

**Gate after the fixes:**

| Suite | Result |
|---|---|
| unit | 888 OK |
| regression | 10 OK |
| test-hooks | 66/66 |
| guard tables | 396/396 runs |
| page | 22/22 |
| lint | 0 errors (5 expected warnings) |
| validate --all | 0 errors |

One guard-table run failed once on the time limit of `pg-26` / `pg-27` while the machine was loaded (load average
7). The re-run was green, and the code under those cases is unchanged.

**Convergence:**
- no `bug` or `spec-gap` in `findings.md` is `open` or `routed`;
- the emergent F-04 and F-29 are `deferred` with their reason, for the backlog;
- the security gate passes.

The change is ready for the owner's QA approval. The approval is not recorded by the agent.

### Pre-merge checklist (update)
- [x] Open spec-gaps routed by `/karvey-iterate` (F-08, F-21..F-27), then QA re-run (D1–D4)
- [ ] QA approval by the owner (not recorded by the agent)
