# Tasks: project-upgrade

> PHASE 7 (`karvey-tasks`, skill text read from `plugins/karvey/skills/karvey-tasks/SKILL.md` in this worktree) · Security Tier 2 · Tracker: Markdown (`project.json:management.tool = markdown`) — this file + `PLAN.md`, no external tracker.
> Inputs: `architecture.md` (approved, D-21), `requirements.md` (REQ-UP-001..032, approved, D-21), `prd.md`, `spec.json`, `checkpoint.md`, the house style of `wave1-hardening/tasks.md`, and the code on `feature/project-upgrade`.
>
> **Estimates are calibrated.** In this repo the method's 10–30 min scale ran about 10× high (for example 165 min estimated → 11 min real across a wave1 feature). The minutes below are realistic **AI execution + human review** for one task (typically 3–8 min AI + 3–8 min review), not the skill's default band. `karvey-impl` records the actuals next to them in `PLAN.md` and never edits an estimate.

## Summary

| Item | Value |
|---|---|
| Features | 8 |
| Tasks | 25 (20 Backend, 3 Test, 2 human) |
| Agent tasks / `[human]` tasks | 23 / 2 |
| Total estimate (agent tasks, AI + human review, calibrated) | **262 min** (≈ 4.4 h) |
| Critical path (agent minutes; `[human]` waits not counted) | **144 min** (≈ 2.4 h), 12 agent tasks + 2 human waits |
| REQ-UP coverage | 32/32 |
| Largest task | 15 min (cap 60) |

## Conventions

- **IDs** `E1.F{n}.T{n}`; E1 = this change. Features follow the build order of the architecture (§1.1–§1.9), not the requirement areas; the PLAN.md feature table maps both.
- **Layers:** `[Backend]` = plugin scripts, hook, skill/rule text and docs (the plugin is this change's backend, `spec.json:layers`); `[Test]` = test-only work (fixtures, tables, manual scripts); `[human]` = a step only a person may run (`rules/multi-agent.md` §5). No DB, Frontend or Infra layer: no cloud, CI is the existing `lint.yml` (infra skipped).
- **Estimate** = AI execution + human review, in minutes, calibrated as stated above. `[human]` tasks carry no estimate; they declare the executor.
- **(P)** = can run in parallel with the other (P) tasks whose dependencies are met, because the files differ. Tasks sharing `karvey_lib/upgrade.py`, `karvey_lib/upgrade_steps.py` + `upgrade-steps.json`, `karvey-upgrade.py` or `lint-plugin.py` run in sequence.
- **Every impl commit** adds one line under `## [Unreleased]` in `CHANGELOG.md` and changes no version. The version number and the fingerprint's `release` are fixed at release by `karvey-deploy` (architecture §1.6, A-12).
- **PLAN.md row** holds `estimate_min · actual_ai_min · actual_review_min` per task.
- **Done criterion** is a command, run from the repo root. Unit tests: `python3 -m unittest discover -s plugins/karvey/tests/unit -p '<file>' -v`. Tables: `python3 plugins/karvey/tests/hooks/run_tables.py --only session`. `$SCR` = the session scratch directory, never the repo or the user's home.
- **Nothing under the user's home is written** by any agent task. Tests use the fixture home `tests/fixtures/upgrade/fake-home/` through `HOME=` in the test process.

## Execution order

1. **Engine foundation** (E1.F1): catalogue contract, read-only `Probe`, fixtures, `plan`, seen record.
2. Two lanes once E1.F1.T4 is done:
   - **writes** (E1.F2 → E1.F4): apply, write phase and journal, branch and commit, then the CLI;
   - **steps** (E1.F3): the 8 initial steps, one catalogue file, in sequence.
3. **Session hook** (E1.F5.T1) as soon as the seen record exists; its tables (E1.F5.T2) once the catalogue and CLI are complete.
4. **Skill** (E1.F6) after the CLI.
5. **Linter and docs** (E1.F7): L-38 after the catalogue; L-37 + `surface` after the CLI; L-39 and the docs last.
6. **Verification and release docs** (E1.F8): whole-repo gate, the owner's E2E, release docs, then the prod OK inside `karvey-deploy`. Archive is the next phase, not a task here.

## Feature E1.F1: Engine foundation — catalogue, Probe, plan, seen record

Architecture §1.3, §1.4 (`load_catalogue`, `Probe`, `StepResult`, `Edit`, `plan`), §2.1, §2.3, §6.3.  
Requirements covered: 001, 004, 005, 007, 008, 009, 010, 016, 022, 024  
Total estimated time: 52 min (5 tasks)

### E1.F1.T1 [Backend] Catalogue contract: `upgrade-steps.schema.json`, `load_catalogue`, `CatalogueError`, empty `REGISTRY`

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/upgrade-steps.schema.json` (NEW, §2.1); `plugins/karvey/scripts/karvey_lib/upgrade.py` (NEW: `load_catalogue`, `CatalogueError`); `plugins/karvey/scripts/karvey_lib/upgrade_steps.py` (NEW: `REGISTRY = {}`); `plugins/karvey/scripts/karvey_lib/upgrade-steps.json` (NEW: `catalogue_version: 1`, one test-only placeholder removed in E1.F3.T1); `plugins/karvey/tests/unit/test_upgrade_catalogue.py` (NEW)  
**Requirements:** REQ-UP-008  
**Tests added:** `test_upgrade_catalogue.py`: each required field removed in turn → `step <id>: missing field <f>` and nothing evaluated; duplicate id; unknown `check`/`fix` name; `human ⇒ fix null`; `report_only ⇒ fix null`; `fix null ∧ ¬human ⇒ report_only`; `writes` outside {`project`,`git_dir`} on a non-human step  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_catalogue.py' -v` passes, and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_schemas.py' -v` still passes (L-17 subset).
- `schema_lite` validation first, then the semantic invariants of §2.1; stdlib only.

### E1.F1.T2 [Backend] Read-only `Probe`, `StepResult`, `Edit` and the overlay — _Depends: E1.F1.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade.py` (`Probe`, dataclasses); `plugins/karvey/tests/unit/test_upgrade_plan.py` (NEW: Probe section)  
**Requirements:** REQ-UP-010, REQ-UP-016  
**Tests added:** `Probe` reads only under the root; `git_read` refuses a sub-command outside the allow-list (`rev-parse`, `symbolic-ref`, `show`, `status --porcelain`, `ls-files`, `config --get`) and never uses a shell; `home_read` accepts only the three fixed paths, caps at 1 MB; the overlay makes a pending edit visible to a later read; `state`/`config` modules load via importlib  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_plan.py' -v` passes, and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_no_shell_true.py' -v` passes.

### E1.F1.T3 [Test] Fixture project `legacy-project` and fixture home `fake-home` (anonymised) (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/tests/fixtures/upgrade/legacy-project/` (NEW: string `management`, `approvals: null`, copied `.claude/hooks/plan-gate.sh` + its `settings.json` entry, no `notifications`, one change in `impl` without a tasks approval, one archived change in the same state); `plugins/karvey/tests/fixtures/upgrade/fake-home/.claude/settings.json` (NEW: a versioned Karvey statusline); `plugins/karvey/tests/unit/test_fixtures_anonymous.py` (covers the new tree)  
**Requirements:** REQ-UP-022, REQ-UP-024 (fixture side)  
**Tests added:** the fixtures; `test_fixtures_anonymous.py` extended to `tests/fixtures/upgrade/`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_fixtures_anonymous.py' -v` passes, and `python3 plugins/karvey/scripts/karvey-state.py validate --all --root plugins/karvey/tests/fixtures/upgrade/legacy-project --json` exits non-zero with legacy-shape findings (the fixture really is legacy).
- Derived from `tests/fixtures/legacy/*`; no organisation, person or product names; no absolute paths.

### E1.F1.T4 [Backend] `plan(root)` and `any_applicable(root, deadline)` — _Depends: E1.F1.T2, E1.F1.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade.py` (`plan`, `Plan`, `any_applicable`); `plugins/karvey/tests/unit/test_upgrade_plan.py`  
**Requirements:** REQ-UP-005, REQ-UP-007, REQ-UP-009, REQ-UP-010  
**Tests added:** with test-only steps registered in the test: all `nothing` → "nothing to do", exit 0; a raising check → `check-failed: <reason>`, others still evaluated, exit 1; `any_applicable` stops at the first non-`nothing` step, evaluates `cost: low` before `scan`, returns `timeout` past the deadline; the plan is the same for seen 3.0.0 and 3.11.4 (state-based); sha256 of tree + git dir + fixture home identical before and after `plan` (no lock, journal or audit write)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_plan.py' -v` passes.

### E1.F1.T5 [Backend] Seen record: `read_seen`, `write_seen`, `VERSION_RE`, audit line — _Depends: E1.F1.T4_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade.py` (`read_seen`, `write_seen`, `VERSION_RE`); `plugins/karvey/tests/unit/test_upgrade_seen.py` (NEW: library part)  
**Requirements:** REQ-UP-001, REQ-UP-004  
**Tests added:** record at `<git-common-dir>/karvey/seen-version`, 0600 in a 0700 dir, atomic under `atomicio.lock`; malformed or unknown-`v` record → absent; a worktree reads the main copy's record (common dir); read-only git dir → the one-line "the offer will repeat next session" error; `audit.log` gets `upgrade.seen <resolution> <version>`; `VERSION_RE` rejects a non-semver version  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_seen.py' -v` passes.

## Feature E1.F2: Apply engine — selection, confinement, preview, writes, branch, commit

Architecture §1.4 apply flow (steps 1–11), §1.5 `branch`/`commit`, §3.2, §5 E-10..E-17.  
Requirements covered: 011, 012, 013, 014, 015, 016, 017, 018, 019, 028  
Total estimated time: 39 min (3 tasks)

### E1.F2.T1 [Backend] `apply` planning half: ids, values as data, selection rule, catalogue order, human/report, confinement, dry-run diff and preview id — _Depends: E1.F1.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade.py` (`apply` steps 1–2, 5–9); `plugins/karvey/tests/unit/test_upgrade_apply.py` (NEW)  
**Requirements:** REQ-UP-011, REQ-UP-012, REQ-UP-014, REQ-UP-015, REQ-UP-016, REQ-UP-019  
**Tests added:** unknown id → exit 3 before any change; mixed selection (some satisfied) → exit 3 naming them, all satisfied → "nothing to do" exit 0 (A-07); `needs-input` without `--values` → exit 3 naming the input; steps run in catalogue order whatever the argument order; a `human` step is never performed and no flag overrides it; symlinked `.claude` pointing outside the tree → refused before any write; an edit naming `.git/karvey/approvals` or the ledger → refused; `branch_flow.integration = "dev; rm -rf ~"` → refused naming `project.json:branch_flow.integration`; `--dry-run` prints unified diffs, writes nothing, and returns the preview id; apply without / with a stale preview → exit 3; a `dry_run: false` step needs `--confirm-no-preview`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_apply.py' -v` passes.

### E1.F2.T2 [Backend] `apply` write half: clean tree, CAS atomic writes, stop at first failure, journal, audit — _Depends: E1.F2.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade.py` (`apply` steps 3, 10–11; journal); `plugins/karvey/tests/unit/test_upgrade_apply.py`  
**Requirements:** REQ-UP-013, REQ-UP-014, REQ-UP-017  
**Tests added:** dirty tree → refused naming the paths, except files listed in the current upgrade branch's journal; every file fully old or fully new (`write_text_atomic` with `expected_sha256`, `os.remove` after a sha check); step 2 of 3 fails → report `applied` / `failed{id: reason}` / `not_run`, step 1 kept, journal right, a re-`plan` lists only steps 2 and 3; a second apply → "nothing to do", no file changed; `audit.log` gets `upgrade.apply <id> <files>`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_apply.py' -v` passes.

### E1.F2.T3 [Backend] `ensure_branch` and `commit`: upgrade branch, exact paths, deterministic message, PR text — _Depends: E1.F2.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade.py` (`ensure_branch`, `commit`); `plugins/karvey/tests/unit/test_upgrade_apply.py` (branch cases); `plugins/karvey/tests/unit/test_upgrade_cli.py` (NEW: commit cases, library level)  
**Requirements:** REQ-UP-013, REQ-UP-018, REQ-UP-028  
**Tests added:** on `dev` → changes land on `chore/karvey-upgrade-<v>` and `dev` has no new commit; base is `refs/remotes/origin/<integration>` when present, else `refs/heads/<integration>`, never a fetch; an existing upgrade branch → switch only; no integration branch and no `origin/HEAD` → refuse naming `project.json:branch_flow.integration`; integration == production (trunk) → branch from it; `commit` refuses on integration/production or on a branch not in the journal; stages exactly the journal files; message `chore(karvey): project upgrade <from> → <to>` with `Steps`, `Picked-by`, `Picked-at`, `Answer` (≤ 200 chars, control characters stripped, via `-F` file) and the passed trailers; returns `pr_title`/`pr_body`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_apply.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_cli.py' -v` pass.

## Feature E1.F3: The initial step catalogue (8 steps)

Architecture §1.6 (table, order 1–8), §1.9 (`STABLE_STATUSLINE`), §5 E-08, E-09, E-18..E-22. Every task adds its function(s) to `upgrade_steps.REGISTRY` and its entry to `upgrade-steps.json` (`since` = 3.13.0, the working number), so the tasks run in sequence.  
Requirements covered: 015, 020, 021, 022, 023, 024, 025, 026  
Total estimated time: 50 min (5 tasks)

### E1.F3.T1 [Backend] Steps `schema-migrate` and `schema-migrate-proposed` — _Depends: E1.F1.T4, E1.F1.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade_steps.py`; `plugins/karvey/scripts/karvey_lib/upgrade-steps.json`; `plugins/karvey/tests/unit/test_upgrade_steps.py` (NEW)  
**Requirements:** REQ-UP-020  
**Tests added:** `fix_spec`/`fix_project` called in-process (exact tier) on `approvals: null` + string `management` → migrated edits, format preserved; an unmappable phase (`42`) → that file left out with the state tool's reason and the step listed as "1 file needs a human"; `schema-migrate-proposed` applies only with its own id and only for what the proposed tier adds; the state tool's migration code is imported, not duplicated  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_steps.py' -v` passes.

### E1.F3.T2 [Backend] Step `legacy-shims` — _Depends: E1.F3.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade_steps.py`; `plugins/karvey/scripts/karvey_lib/upgrade-steps.json` (`params.known_sha256` of the shipped shims and the 3.11.x templates); `plugins/karvey/tests/unit/test_upgrade_steps.py`  
**Requirements:** REQ-UP-022  
**Tests added:** a byte-identical copy → delete edit + the `settings.json` hook entry removed (empty `hooks` drops the key) + `enforcement.plan_gate_hook` / `git_flow_hook: true`; a locally edited copy → `human` with the diff against the shipped shim, nothing deleted; after applying on a temp copy of the fixture, `python3 plugins/karvey/tests/hooks/run_tables.py --only plan-gate --only git-flow` still passes  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_steps.py' -v` passes.

### E1.F3.T3 [Backend] Steps `team-settings` and `enforcement-defaults` — _Depends: E1.F3.T2_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade_steps.py`; `plugins/karvey/scripts/karvey_lib/upgrade-steps.json`; `plugins/karvey/tests/unit/test_upgrade_steps.py`  
**Requirements:** REQ-UP-021, REQ-UP-026  
**Tests added:** missing `notifications`/`management` → preview from `propose_settings(..., from_legacy=True)`; `<…>` placeholders → `needs-input`; each `--values` entry checked through `safe_values.check_target` / `check_location`; `enforcement-defaults` lists `prod_gate_hook` (a key with `x-karvey-default` not declared) and skips any explicit value; no `standards` block → the informational line naming `/karvey:karvey-standards`; no `project.json` but `changes/` exists → `needs-input` handed to `/karvey:karvey-init --settings`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_steps.py' -v` passes.

### E1.F3.T4 [Backend] Human steps `statusline-launcher` and `global-config`; `STABLE_STATUSLINE` constant — _Depends: E1.F3.T3_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade_steps.py` (`STABLE_STATUSLINE`, §1.9); `plugins/karvey/scripts/karvey_lib/upgrade-steps.json` (`human: true`, `fix: null`, `params.recommend`); `plugins/karvey/tests/unit/test_upgrade_steps.py`  
**Requirements:** REQ-UP-015, REQ-UP-023, REQ-UP-025  
**Tests added:** fake-home versioned statusline → `human` with the stable command; no statusline → `human`; an own (non-Karvey) command → `nothing`, note "own statusline, left as is"; `global-config` shows a unified diff of only the Karvey-related keys; unreadable or invalid home JSON → `check-failed: unreadable`, the rest computed; the fake home is byte-identical after `plan` and `apply`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_steps.py' -v` passes.

### E1.F3.T5 [Backend] Report step `changes-in-flight`; the shipped catalogue is complete — _Depends: E1.F3.T4_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade_steps.py`; `plugins/karvey/scripts/karvey_lib/upgrade-steps.json` (8 steps in §1.6 order); `plugins/karvey/tests/unit/test_upgrade_steps.py`; `plugins/karvey/tests/unit/test_upgrade_catalogue.py` (shipped catalogue loads, ids in §1.6 order)  
**Requirements:** REQ-UP-024  
**Tests added:** the fixture's `impl` change without a tasks approval is listed with its unmet gate; the archived change is not; `apply --steps changes-in-flight` writes nothing; the shipped catalogue has exactly the 8 ids  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_*.py' -v` passes.

## Feature E1.F4: The upgrade tool `karvey-upgrade.py`

Architecture §1.5 (`plan`, `branch`, `apply`, `commit`, `seen`; `surface` is added in E1.F7.T2).  
Requirements covered: 001, 004, 007, 009, 013, 018, 019  
Total estimated time: 15 min (1 task)

### E1.F4.T1 [Backend] CLI `plan | branch | apply | commit | seen` with `--root`, `--json` envelope and `karvey_lib` exit codes — _Depends: E1.F2.T3, E1.F1.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-upgrade.py` (NEW); `plugins/karvey/tests/unit/test_upgrade_cli.py` (subprocess cases); `plugins/karvey/tests/unit/test_upgrade_seen.py` (CLI cases)  
**Requirements:** REQ-UP-001, REQ-UP-004, REQ-UP-007, REQ-UP-009, REQ-UP-013, REQ-UP-018, REQ-UP-019  
**Tests added:** `plan --json` rows == the table rows, keys as §1.5; `seen --decline/--accept/--empty/--show`; `seen` outside a Karvey project → exit 3, nothing written; decline → no offer for the same version and an offer on the next (library check); `apply --values FILE` validated per key; `commit --json` prints `pr_title`/`pr_body`; every subprocess is an argv list  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_cli.py' -v`, `… -p 'test_upgrade_seen.py' -v` and `… -p 'test_no_shell_true.py' -v` pass, and `python3 plugins/karvey/scripts/karvey-upgrade.py plan --root plugins/karvey/tests/fixtures/upgrade/legacy-project --json` exits 0 or 1 with a valid envelope.

## Feature E1.F5: The once-per-version offer (session hook)

Architecture §1.2, §2.4, §5 E-01..E-07, E-23, E-24, E-26, E-27, §6.1.  
Requirements covered: 001, 002, 003, 004, 005, 006  
Total estimated time: 30 min (2 tasks)

### E1.F5.T1 [Backend] `upgrade_offer()` in `session_text()`, `defaults.json` keys, bash degraded line — _Depends: E1.F1.T5_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (`upgrade_offer`, both branches of `session_text`, "First action" second item); `plugins/karvey/scripts/karvey_lib/defaults.json` (`session.upgrade_probe_ms: 1500`, `session.offer_line_max: 300`); `plugins/karvey/hooks/karvey-session-context.sh` (no-python path: one `upgrade offer unavailable: python 3 not found` line on `startup` in a Karvey project); `plugins/karvey/tests/unit/test_karvey_hooks.py`  
**Requirements:** REQ-UP-002, REQ-UP-003, REQ-UP-005, REQ-UP-006  
**Tests added:** only `startup`; not a Karvey project → silent and no record created (`state_dir(create=False)`); seen == installed → silent; `none` → record `empty`, silent; `found`/`timeout`/raised check → the two lines, each ≤ 300 chars, `<plugin>` quoted with `shlex.quote`; invalid catalogue or non-semver version → one line, record unchanged; `KARVEY_TEST_UPGRADE_PROBE_MS` override honoured only by tests; any exception → one line, session text still produced  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_karvey_hooks.py' -v` passes.

### E1.F5.T2 [Test] Session table cases ss-24..ss-35 and the runner's `given.seen_version` — _Depends: E1.F5.T1, E1.F3.T5, E1.F4.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/tests/hooks/run_tables.py` (`given.seen_version`; default: seeded equal to the installed version, `null` = absent); `plugins/karvey/tests/hooks/tables/session.json` (ss-24..ss-35, §6.1)  
**Requirements:** REQ-UP-001, REQ-UP-002, REQ-UP-003, REQ-UP-004, REQ-UP-005, REQ-UP-006  
**Tests added:** ss-24 offer on version change · ss-25 absent record · ss-26 no offer on resume · ss-27 silent outside Karvey (no `karvey/seen-version`) · ss-28 bare `docs/spec/` · ss-29 declined · ss-30 empty plan records `empty` · ss-31 budget exceeded offers · ss-32 bad catalogue one line · ss-33 bounds unchanged with the offer · ss-34 worktree shares the record, `git status` clean · ss-35 `nopy` degraded line; ss-01..ss-23 unchanged  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only session` passes all cases, and `bash plugins/karvey/tests/test-hooks.sh` passes.

## Feature E1.F6: The upgrade skill `/karvey-upgrade`

Architecture §1.7, §6.4, §8 (orchestrator line and counts).  
Requirements covered: 004, 012, 018, 027, 028, 029  
Total estimated time: 18 min (2 tasks)

### E1.F6.T1 [Backend] `skills/karvey-upgrade/SKILL.md`, orchestrator line, support-skill counts 18 → 19 — _Depends: E1.F4.T1_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/skills/karvey-upgrade/SKILL.md` (NEW, §1.7 steps 1–10; `allowed-tools: Read, Bash, AskUserQuestion`); `plugins/karvey/skills/karvey/SKILL.md` (support-skills list); `plugins/karvey/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` (description count only, no version); `README.md` and `plugins/karvey/README.md` (count only)  
**Requirements:** REQ-UP-004, REQ-UP-012, REQ-UP-018, REQ-UP-027, REQ-UP-028, REQ-UP-029  
**Tests added:** L-02, L-03, L-11, L-14 on the new skill  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-02,L-03,L-11,L-14` exits 0.
- The skill relays the tool only: it never computes, adds or skips a step; missing tool → say so and stop; never merges; values for `--values` go to a temp file outside the repo.

### E1.F6.T2 [Test] Manual script `tests/manual/upgrade-skill.md` — _Depends: E1.F6.T1_

**Estimate:** 8 min  
**Files:** `plugins/karvey/tests/manual/upgrade-skill.md` (NEW)  
**Requirements:** REQ-UP-027, REQ-UP-028, REQ-UP-029  
**Tests added:** manual cases in the shape of the existing `tests/manual/*.md`: rows == `plan --json`; missing tool → stop; picks none → `seen --decline`, no branch; invocable with seen == installed; not a Karvey project → stop without writing; a headless session in a throw-away clone under `$SCR`  
**Done when:** `test -f plugins/karvey/tests/manual/upgrade-skill.md && grep -c '^## ' plugins/karvey/tests/manual/upgrade-skill.md` ≥ 5, and `python3 plugins/karvey/scripts/lint-plugin.py --paths 'plugins/karvey/tests/manual/*'` reports 0 errors.

## Feature E1.F7: Linter L-37, L-38, L-39, `--list`, fingerprint and docs

Architecture §1.8, §2.2, §7 item 2, §8.  
Requirements covered: 008, 010, 016, 023, 030, 031, 032  
Total estimated time: 42 min (3 tasks)

### E1.F7.T1 [Backend] L-38 (catalogue valid, AST scan of step functions) and `--list` accepting `REQ-UP` claims — _Depends: E1.F3.T5_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-38; `requirement_ids` collects `REQ-(W1|UP)-\d{3}`, `"UP-030"` → `REQ-UP-030`, bare `"055"` still → `REQ-W1-055`); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-UP-008, REQ-UP-010, REQ-UP-016, REQ-UP-031  
**Tests added:** mutations: missing `risk`; a `fix` with `open(..., 'w')`, `os.remove`, `shutil.*`, `subprocess.*` or `atomicio.write_*`; a non-human step reading `probe.home_read`; `writes` outside the allowed scopes; `since` > plugin version — each fails naming the step; the shipped catalogue passes; existing W1 claims unchanged in `--list`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes, and `python3 plugins/karvey/scripts/lint-plugin.py --only L-38` exits 0.

### E1.F7.T2 [Backend] Fingerprint `upgrade-surface.json`, `karvey-upgrade.py surface [--write]`, L-37 — _Depends: E1.F7.T1, E1.F4.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade-surface.json` (NEW, §2.2, initial globs of §1.8, `release` = the current top CHANGELOG release); `plugins/karvey/scripts/karvey-upgrade.py` (`surface`, refuses `--write` outside the plugin repo); `plugins/karvey/scripts/lint-plugin.py` (L-37); `plugins/karvey/tests/unit/test_lint_plugin.py`; `plugins/karvey/tests/unit/test_upgrade_cli.py` (`surface`)  
**Requirements:** REQ-UP-030  
**Tests added:** surface unchanged → pass; changed under `[Unreleased]` → warning listing the files; a newer top release without a step whose `since` equals it and without `^- No project upgrade needed: .{10,}` → error naming release and files; with either + refreshed fingerprint → pass; top release older than the fingerprint → error; normalisation (BOM stripped, LF) makes the hash platform-stable  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes, and `python3 plugins/karvey/scripts/lint-plugin.py --only L-37` exits 0 (a warning is allowed while `[Unreleased]` holds this change).

### E1.F7.T3 [Backend] L-39 and the docs: root README upgrade section, plugin README pointer, hooks README offer + stable statusline, release line in versioning and deploy — _Depends: E1.F7.T2, E1.F5.T2, E1.F6.T1, E1.F3.T4_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-39, including the `STABLE_STATUSLINE` == hooks README comparison); `README.md` ("### Upgrading your project" under "## Update to the latest version": when you are asked, "Not for this version", `/karvey:karvey-upgrade`, `karvey-upgrade.py plan`); `plugins/karvey/README.md` (one-line pointer); `plugins/karvey/hooks/README.md` ("## The upgrade offer" with `<!-- guard-case: ss-24… -->` anchors; statusline example replaced by the stable command); `plugins/karvey/skills/karvey/rules/versioning.md` and `plugins/karvey/skills/karvey-deploy/SKILL.md` (release line of §7 item 2); `plugins/karvey/tests/unit/test_lint_plugin.py`  
**Requirements:** REQ-UP-023, REQ-UP-032  
**Tests added:** L-39 mutations: README section removed, hooks README section removed, stable command drifted → each an error; L-16 checks the new anchors against ss-24..ss-35; L-19/L-20 keep versioning consistent  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes, and `python3 plugins/karvey/scripts/lint-plugin.py --only L-16,L-19,L-20,L-39` exits 0.

## Feature E1.F8: Verification, release docs and the prod OK

Architecture §6.4, §6.5, §7, §8. The prod OK runs inside `karvey-deploy` (D-10).  
Requirements covered: 002, 018, 030, 032 (plus the whole-repo gate over all 32)  
Total estimated time: 16 min (2 agent tasks + 2 `[human]`)

### E1.F8.T1 [Backend] Whole-repo gate and read-only dogfood plan on this repo — _Depends: E1.F7.T3, E1.F6.T2, E1.F5.T2_

**Estimate:** 8 min  
**Files:** none changed (evidence in the PLAN.md row notes)  
**Requirements:** all REQ-UP (regression gate)  
**Tests added:** none new; runs every suite  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0 with 0 errors; `python3 -m unittest discover -s plugins/karvey/tests/unit -v` passes; `python3 plugins/karvey/tests/hooks/run_tables.py` passes; `python3 plugins/karvey/scripts/karvey-upgrade.py plan --json` on this repo lists `enforcement-defaults` and the human `statusline-launcher` / `global-config` (architecture §7 item 1) and `git status --porcelain` is empty afterwards.

### E1.F8.T2 [human] E2E: offer → accept → PR on a throw-away repo, and the manual skill script — _Depends: E1.F8.T1_

**Executor:** the owner (repo maintainer)  
**Command:** In `$SCR`, create a throw-away Git repository with a remote you own, copy `plugins/karvey/tests/fixtures/upgrade/legacy-project/` into it, commit, push. Start `claude --plugin-dir <this repo>/plugins/karvey` there with an older seen record (`python3 <this repo>/plugins/karvey/scripts/karvey-upgrade.py seen --show` shows none). Answer "Yes" to the offer, pick the recommended steps, confirm the dry-run. Then run the cases of `plugins/karvey/tests/manual/upgrade-skill.md` in the same clone.  
**Verification:** `gh pr list --state open --json headRefName --jq '.[].headRefName'` in the throw-away repo → `chore/karvey-upgrade-<v>`; `git log -1 --format=%B origin/chore/karvey-upgrade-<v>` shows `Steps:`, `Picked-by:`, `Picked-at:`; a second session in the same clone shows no offer; each manual case marked PASS in the script.  
**Rollback:** delete the throw-away repository and `rm -rf "$SCR"`; nothing in this repo or the user's home changed.  
**Requirements:** REQ-UP-002, REQ-UP-018, REQ-UP-027, REQ-UP-028, REQ-UP-029  
**Executed:** maintainer agent, headless under D-21 · 2026-09-25 13:28–13:43 UTC · evidence `qa/manual/e2e-2026-09-25.md` and `qa/manual/upgrade-skill-2026-09-25.md` — PASS after F-05/F-06/F-07 were fixed; the origin was a bare local repository, so the PR was offered as the exact `gh pr create` command (no PR host), and the `gh pr list` check does not apply

### E1.F8.T3 [Backend] Release docs: the `[Unreleased]` block declares the project upgrade — _Depends: E1.F8.T2_

**Estimate:** 8 min  
**Files:** `CHANGELOG.md` (the `[Unreleased]` block already holds one line per task: add the summary that lists the 8 step ids and the behaviour change "first startup after an update asks once per clone"; no version, no date); `docs/spec/changes/project-upgrade/PLAN.md` (feature states)  
**Requirements:** REQ-UP-030, REQ-UP-032  
**Tests added:** L-37 and L-39 on the release block  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0, and `sed -n '/## \[Unreleased\]/,/## \[/p' CHANGELOG.md | grep -c -E 'schema-migrate|legacy-shims|team-settings|enforcement-defaults|statusline-launcher|global-config|changes-in-flight'` ≥ 7.
- The version number, the release date and `karvey-upgrade.py surface --write` belong to `karvey-deploy` at the release (A-12), not to this task.

### E1.F8.T4 [human] The prod OK for the release that ships this change (D-10) — _Depends: E1.F8.T3_

**Executor:** the owner — never delegated  
**Command:** inside `karvey-deploy`, after reading the release PR and its evidence, type your own words with an approval **and** a production term (for example «ok, merge a prod project-upgrade <version>»), and answer the structured question that records the D-NN.  
**Verification:** the session shows `[karvey] approval recorded (prod, project-upgrade, expires hh:mm)`; `python3 plugins/karvey/scripts/karvey-state.py check-prod project-upgrade --json` → `ok: true` after `approve prod`.  
**Rollback:** before the merge: do nothing, the marker expires. After the merge: a revert PR, as a new change through the method.  
**Requirements:** release gate (D-10); no REQ-UP of its own  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

## Traceability matrix (REQ-UP → tasks)

| REQ-UP | Tasks |
|---|---|
| 001 | E1.F1.T5, E1.F4.T1, E1.F5.T2 |
| 002 | E1.F5.T1, E1.F5.T2, E1.F8.T2 |
| 003 | E1.F5.T1, E1.F5.T2 |
| 004 | E1.F1.T5, E1.F4.T1, E1.F5.T2, E1.F6.T1 |
| 005 | E1.F1.T4, E1.F5.T1, E1.F5.T2 |
| 006 | E1.F5.T1, E1.F5.T2 |
| 007 | E1.F1.T4, E1.F4.T1 |
| 008 | E1.F1.T1, E1.F7.T1 |
| 009 | E1.F1.T4, E1.F4.T1 |
| 010 | E1.F1.T2, E1.F1.T4, E1.F7.T1 |
| 011 | E1.F2.T1 |
| 012 | E1.F2.T1, E1.F6.T1 |
| 013 | E1.F2.T2, E1.F2.T3, E1.F4.T1 |
| 014 | E1.F2.T1, E1.F2.T2 |
| 015 | E1.F2.T1, E1.F3.T4 |
| 016 | E1.F1.T2, E1.F2.T1, E1.F7.T1 |
| 017 | E1.F2.T2 |
| 018 | E1.F2.T3, E1.F4.T1, E1.F6.T1, E1.F8.T2 |
| 019 | E1.F2.T1, E1.F4.T1 |
| 020 | E1.F3.T1 |
| 021 | E1.F3.T3 |
| 022 | E1.F1.T3, E1.F3.T2 |
| 023 | E1.F3.T4, E1.F7.T3 |
| 024 | E1.F1.T3, E1.F3.T5 |
| 025 | E1.F3.T4 |
| 026 | E1.F3.T3 |
| 027 | E1.F6.T1, E1.F6.T2, E1.F8.T2 |
| 028 | E1.F2.T3, E1.F6.T1, E1.F6.T2, E1.F8.T2 |
| 029 | E1.F6.T1, E1.F6.T2, E1.F8.T2 |
| 030 | E1.F7.T2, E1.F8.T3 |
| 031 | E1.F7.T1 |
| 032 | E1.F7.T3, E1.F8.T3 |

**Coverage:** 32/32. No REQ-UP is left without a task. Every component of the architecture's file plan (§1.1) has a task: schema, engine, steps, catalogue, fingerprint, CLI, `defaults.json`, `karvey_hooks.py`, bash hook, skill, linter, fixtures, runner and tables, unit suites, manual script, READMEs, versioning rule, deploy skill, CHANGELOG.

## Totals and critical path

- **Tasks:** 25, of which 2 `[human]` and 23 agent tasks (20 Backend, 3 Test).
- **Total estimate:** 262 min ≈ 4.4 h of AI + review, calibrated (see the header). Per feature: F1 52 · F2 39 · F3 50 · F4 15 · F5 30 · F6 18 · F7 42 · F8 16.
- **Critical path:** 144 min ≈ 2.4 h:
  E1.F1.T1 → E1.F1.T2 → E1.F1.T4 → E1.F1.T5 → E1.F2.T1 → E1.F2.T2 → E1.F2.T3 → E1.F4.T1 → E1.F7.T2 → E1.F7.T3 → E1.F8.T1 → [E1.F8.T2 human] → E1.F8.T3 → [E1.F8.T4 human].
  The `[human]` waits and CI queue time are not counted. E1.F5.T2 ties with E1.F7.T2 at minute 113, so a slip in the step lane (E1.F3, ends at minute 86) or the hook (E1.F5.T1) does not move the path unless it exceeds about 27 min.
- **Parallel potential:** total ÷ critical path ≈ 1.8×. The serial spine is `karvey_lib/upgrade.py`, which six tasks share.

## What proved impractical when breaking the architecture into tasks

1. **One engine file serialises the spine.** `upgrade.py` carries the catalogue loader, `Probe`, `plan`, the seen record, `apply`, the journal, `ensure_branch` and `commit` (§1.1). Six tasks touch it, so they cannot run (P). Splitting it (`upgrade_seen.py`, `upgrade_apply.py`) would let the hook lane and the write lane start earlier; it is left as in the approved file plan, and `karvey-impl` may propose it as an implementation detail.
2. **The catalogue grows with the steps.** Each step task adds its entry to `upgrade-steps.json`, so E1.F1.T1 ships a placeholder entry that E1.F3.T1 removes. The alternative (ship all 8 entries at once) would fail `load_catalogue` until every registry function exists.
3. **The tables need the full catalogue.** ss-30 ("nothing applies → record `empty`") is only meaningful when all 8 steps exist and the fixture home is clean, so E1.F5.T2 waits for E1.F3.T5 even though the hook code (E1.F5.T1) can land early.
4. **L-37 is a warning for the whole of impl.** Every task that touches a surface file (the hook, `defaults.json`, `karvey_hooks.py`, a new schema) makes L-37 warn under `[Unreleased]`. That is by design (§1.8); the whole-repo gate accepts warnings, and the error only appears once a release header exists without the declaration or the refreshed fingerprint.
5. **`since` = 3.13.0 is a working number.** If the release that ships this change gets another number, `karvey-deploy` updates the 8 `since` values and the fingerprint in the release commit; L-38 (`since` ≤ plugin version) and L-37 check both.
6. **Fixture home directory name.** §6.3 calls the directory `home`; these tasks name it `tests/fixtures/upgrade/fake-home/` so that scans for home-directory paths in this public repo (and `test_fixtures_anonymous.py`) never match a fixture. Same content, different name (spec-gap, low).
7. **The E2E needs a remote the owner controls.** The PR half of REQ-UP-018 cannot be proven headless in this repo (the agent must not open PRs on another repo on its own), so it is a `[human]` task (E1.F8.T2) with exact verification commands.

---
*Generated by `karvey-tasks` (PHASE 7) on 2026-09-25 for `project-upgrade`. Not approved by this document.*
