# Tasks: wave1-hardening

> PHASE 7 (`karvey-tasks`, method 3.11.4) · Security Tier 2 · Tracker: Markdown (`project.json:management.tool = markdown`) — this file + `PLAN.md`, no external tracker.
> Inputs: `architecture.md` (approved, D-09), `requirements.md` (REQ-W1-001..109, approved, D-05), `prd.md`, `spec.json`, `findings.md`, `docs/spec/decisions.md` D-01..D-11, `docs/bugs_dev_testing.md` (BUG-05..17 routed here; BUG-18..21 resolved in 3.11.3/3.11.4), and the code on `feature/wave1-hardening` (3.11.4 merged).

## Summary

| Item | Value |
|---|---|
| Features | 16 |
| Tasks | 73 (58 Backend, 1 Frontend, 2 Infra, 7 Test, 5 human) |
| Agent tasks / `[human]` tasks | 68 / 5 (E1.F1.T2 is conditional: only if T-0 cannot run headless) |
| Total estimate (agent tasks, AI + human review) | **2150 min** (35.8 h) |
| Critical path (agent minutes; `[human]` waits not counted) | **550 min** (9.2 h), 18 tasks |
| REQ-W1 coverage | 109/109 |
| Largest task | 50 min (cap 60) |

## Conventions

- **IDs** `E1.F{n}.T{n}`; E1 = this change. Features follow architecture components (§1.1).
- **Layers:** `[Backend]` = plugin scripts, hooks, and skill/rule text (the plugin is this change's backend, `spec.json:layers`); `[Infra]` = CI and repository settings; `[Test]` = test-only work (fixtures, tables, runners, scripts); `[Frontend]` = the method page `docs/karvey.html` only; `[human]` = a step only a person may run (`rules/multi-agent.md` §5).
- **Estimate** = AI execution + human review, in minutes (`clickup-protocol.md` → Estimation). `[human]` tasks carry no estimate; they declare the executor.
- **(P)** = can run in parallel with the other (P) tasks whose dependencies are met, because the files differ. Tasks that share a file (`karvey-state.py`, `guards.py`, `lint-plugin.py`, `karvey_hooks.py`) run in sequence.
- **Every impl commit** adds one line under `## [Unreleased]` in `CHANGELOG.md` and changes no version (REQ-W1-036). The one bump is E1.F16.T1 (REQ-W1-037).
- **PLAN.md row** holds `estimate_min · actual_ai_min · actual_review_min` per task (REQ-W1-043, dogfooded from this phase on).
- **Done criterion** is a command. Unit tests: `python3 -m unittest discover -s plugins/karvey/tests/unit -p '<file>' -v`. Tables: `python3 plugins/karvey/tests/hooks/run_tables.py --only <table>`.
- **Commands in this file** run from the repo root `~/Dev/karvey`. `$SCRATCH` = the session scratch directory, never the repo or `~/.claude/`.

## Preconditions and open points (for the tasks gate)

- **OP-1 — `infra` is neither approved nor skipped.** `karvey-tasks` Step 1 requires `approvals.infra.approved = true`; `spec.json` has `infra.approved: false` and no `skipped.infra`, and `phase_history` went architecture → tasks under D-09. The architecture says there is no cloud (`cloud.provider: none`), and CI is built here as E1.F13. Once the state tool exists, `advance wave1-hardening impl` will refuse (`infra not approved or skipped`). **The owner needs to decide at this gate:** either record `skip wave1-hardening infra --reason "no cloud; CI workflow built as tasks E1.F13"` (run by E1.F15.T1 with the new tool, or by hand now with the D-NN of this gate), or run `/karvey-infra`. Recommended: skip, since the workflow file is already fully specified in §1.11.
- **OP-2 — the skill writes a phase value the new enum rejects.** `karvey-tasks` Step 4 says `phase: "tasks-generated"`. That is a legacy value (REQ-W1-009 maps it). As instructed, `spec.json` keeps `phase: "tasks"`, and E1.F12.T4 fixes the skill text.
- **OP-3 — F-02 stays open until E1.F1.T1.** The hook-payload assumptions A-1..A-10 are not confirmed yet. A correction to A-2/A-3/A-4/A-6 changes E1.F4.T1, E1.F5.T7 and E1.F6.T1 before the tables are frozen.

## Execution order

1. **E1.F1.T1 first:** capture a real payload per event (T-0).
2. **Schemas and the state tool:** E1.F2, E1.F3. Everything writes through them.
3. **Hooks and dispatcher, guards, session hook and handoff capture, config, dashboard, spec-merge, linter, statusline and page:** E1.F4 to E1.F11.
4. **Skill and rule text:** E1.F12, closed by the whole-repo lint gate E1.F12.T13.
5. **CI workflow:** E1.F13.T1. It is observed on a PR in E1.F13.T2, after steps 6–7.
6. **Migration fixtures and regression suite:** E1.F14.
7. **This repo's own `spec.json` files through `--fix`:** E1.F15.
8. **Last, once:** docs, CHANGELOG and the version bump to 3.12.0 (E1.F16.T1). Then the deploy-phase human steps (E1.F16.T3..T7) inside `karvey-deploy`. Archive is the next phase (`karvey-archive`), not a task here.

Parallel lanes once E1.F2.T1 is done, each serial inside itself:
- state (E1.F2.T2..T6 → E1.F3);
- hook runtime (E1.F4 → E1.F5 → E1.F6.T1/T2);
- config (E1.F7);
- linter (E1.F10);
- spec-merge (E1.F9), handoff capture (E1.F6.T3) and page (E1.F11.T2).

## Feature E1.F1: Hook contract capture (T-0)

Confirms or corrects assumptions A-1..A-10 (finding F-02) before any parser or table is frozen.  
Requirements covered: 017, 024, 028, 047, 050  
Total estimated time: 30 min (2 tasks)

### E1.F1.T1 [Test] Capture one real hook payload per event in a throw-away plugin (T-0)

**Estimate:** 30 min  
**Files:** `plugins/karvey/tests/fixtures/payloads/{session-start-startup,session-start-resume,user-prompt-submit,pre-tool-use-bash,pre-tool-use-write,post-tool-use-write}.json` (NEW, sanitised); `docs/spec/changes/wave1-hardening/findings.md` (F-02 row: result per assumption)  
**Requirements:** REQ-W1-017, REQ-W1-024, REQ-W1-028, REQ-W1-047, REQ-W1-050  
**Tests added:** the captured fixtures themselves; consumed by `test_hookio.py` (F4.T1)  
**Done when:** `ls plugins/karvey/tests/fixtures/payloads/*.json | wc -l` ≥ 6, and `python3 -c "import json,glob,sys;[json.load(open(f)) for f in glob.glob('plugins/karvey/tests/fixtures/payloads/*.json')]"` exits 0; the F-02 row in findings.md names a result for each of A-1..A-8; `sha256sum ~/.claude/settings.json ~/.claude/CLAUDE.md` is identical before and after the task (nothing outside the repo and `$SCR` changed).
- Scratch only: `SCR=$(mktemp -d)`; plugin at `$SCR/cap/.claude-plugin/plugin.json` + `$SCR/cap/hooks/hooks.json` registering SessionStart (`startup|resume|compact|clear`), UserPromptSubmit, PreToolUse (`Bash`, `Edit|Write`) and PostToolUse (`Edit|Write`). Each runs `bash "${CLAUDE_PLUGIN_ROOT}/hooks/log.sh" <event>` (double quotes, BUG-18), and `log.sh` does `cat > "$CAP/<event>-$(date +%s%N).json"; exit 0`.
- Probe variants in the same plugin: the SessionStart hook also prints `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"KV-SENTINEL-6"}}` (A-6); PostToolUse on a file named `block-me.txt` exits 2 with stderr `KV-SENTINEL-4` (A-4); PreToolUse on `ls /tmp/kv-slow` sleeps past a 3 s timeout (A-7).
- Project dir `$SCR/proj` (`git init`, not a Karvey project). Run `cd "$SCR/proj" && CAP="$SCR/out" claude -p --setting-sources project,local --plugin-dir "$SCR/cap" --allowedTools "Bash(ls:*) Write" --session-id <uuid> "Run ls, then ls /tmp/kv-slow, then write hi to a.txt and to block-me.txt, then say whether you saw KV-SENTINEL-6 and KV-SENTINEL-4"`, then `claude -p --resume <uuid> --setting-sources project,local --plugin-dir "$SCR/cap" "say done"` for the resume event.
- `--setting-sources project,local` keeps `~/.claude/settings.json` (the owner's hooks) out of the run; nothing under `~/.claude/` is read for writing or edited. If the installed CLI rejects either flag or no file lands in `$SCR/out`, stop and hand over to F1.T2.
- Sanitise into the fixtures: `session_id` → `00000000-…`, `transcript_path`/`cwd` → `/SCRATCH/…`; keep field names and shapes exactly. Record in F-02, per A-1..A-8, `confirmed` or `corrected: <what>`. A correction to A-2/A-3/A-4/A-6 is a delta for F4.T1 / F5.T7 / F6.T1, noted in the F-02 row (routed by karvey-iterate if it changes a requirement).

### E1.F1.T2 [human] (Conditional) capture the payloads interactively if F1.T1 could not — _Depends: E1.F1.T1_

**Executor:** Mauricio Quezada Ibáñez (owner) — only if F1.T1 reports that `claude -p` with `--plugin-dir` produced no capture  
**Command:** The agent prepares `$SCR/cap` and `$SCR/proj` exactly as in F1.T1 and prints the paths. The owner runs, in a separate terminal: `cd <SCR>/proj && CAP=<SCR>/out claude --setting-sources project,local --plugin-dir <SCR>/cap`, types `run ls, then write hi to a.txt`, exits, then runs `claude --resume` in the same dir and exits again.  
**Verification:** `ls <SCR>/out/*.json | wc -l` → ≥ 6 files (one per event); the agent then sanitises them as in F1.T1.  
**Rollback:** `rm -rf <SCR>` (nothing outside the scratch dir was touched).  
**Requirements:** REQ-W1-017, REQ-W1-028, REQ-W1-047, REQ-W1-050  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

## Feature E1.F2: Shared library and schemas

`karvey_lib` foundation (§1.1 shared conventions), `schemas/*.json` (§2.1, §2.2, §2.5, §2.6).  
Requirements covered: 001, 002, 003, 004, 005, 006, 007, 008, 009, 013, 025, 026, 027, 045, 049, 050, 057, 061, 071, 088, 093, 098  
Total estimated time: 135 min (6 tasks)

### E1.F2.T1 [Backend] `karvey_lib` package skeleton, exit codes, JSON envelope and `defaults.json` (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/__init__.py` (NEW); `plugins/karvey/scripts/karvey_lib/defaults.json` (NEW: rotation_hours 8 · plan_marker_ttl_min 120 · stall_days 7 · calibration 30/3 · session caps 40 rows / 6 KB); `plugins/karvey/tests/unit/_path.py` (NEW: sys.path helper); `plugins/karvey/tests/unit/test_envelope.py` (NEW)  
**Requirements:** REQ-W1-049  
**Tests added:** `test_envelope.py` (envelope keys, exit-code constants, defaults.json keys and D-06/D-07 values)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_envelope.py' -v` passes.
- Exit codes 0..5 and the `--json` envelope `{tool,version,ok,exit,result,errors,warnings}` from §1.1.
- `defaults.json` is the one place for D-06/D-07 values (REQ-W1-049).

### E1.F2.T2 [Backend] `atomicio.py`: BOM-tolerant read, format-preserving atomic write, lock and compare-and-swap — _Depends: E1.F2.T1_ (P)

**Estimate:** 20 min  
**Files:** `plugins/karvey/scripts/karvey_lib/atomicio.py` (NEW); `plugins/karvey/tests/unit/test_atomicio.py` (NEW)  
**Requirements:** REQ-W1-008, REQ-W1-013  
**Tests added:** `test_atomicio.py`: utf-8-sig read; key order and 2-space indent kept; `tmp + os.replace`; `O_EXCL` lock stale after 30 s; CAS refusal → exit 3  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_atomicio.py' -v` passes.
- Implements the Writes row of §1.1 shared conventions.

### E1.F2.T3 [Backend] `schema_lite.py`: the JSON-Schema subset validator with the two `x-karvey-*` extensions — _Depends: E1.F2.T1_ (P)

**Estimate:** 25 min  
**Files:** `plugins/karvey/scripts/karvey_lib/schema_lite.py` (NEW); `plugins/karvey/tests/unit/test_schema_lite.py` (NEW)  
**Requirements:** REQ-W1-002  
**Tests added:** `test_schema_lite.py`: every supported keyword of §2.2; `x-karvey-severity: warning`; `x-karvey-format: datetime-tz`; an unsupported keyword → error (L-17 relies on it)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_schema_lite.py' -v` passes.
- Subset exactly as listed in §2.2, local `$ref` to `$defs` and cross-file `karvey:<name>#/$defs/…`.

### E1.F2.T4 [Backend] `project.py` (root discovery, active change, reviewed-config read, state dir) and `audit.py` — _Depends: E1.F2.T1_ (P)

**Estimate:** 30 min  
**Files:** `plugins/karvey/scripts/karvey_lib/project.py` (NEW); `plugins/karvey/scripts/karvey_lib/audit.py` (NEW); `plugins/karvey/tests/unit/test_project.py` (NEW); `plugins/karvey/tests/unit/test_audit.py` (NEW)  
**Requirements:** REQ-W1-025, REQ-W1-027, REQ-W1-045, REQ-W1-050  
**Tests added:** `test_project.py`: walk-up bounded by the git top level; Karvey-project definition (project.json or changes/); `active` rule of §5 (feature branch → single non-archived/non-IMPLEMENTED/non-deployed → none); `git show origin/{prod}:docs/spec/project.json` read; `--git-common-dir` state dir 0700 with XDG fallback; worktree case. `test_audit.py`: JSONL, 0600, 1 MB rotation, no token fields  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_project.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_audit.py' -v` pass.
- Subprocess via argv lists only (§3.1 rule 1).

### E1.F2.T5 [Backend] `schemas/spec.schema.json` and `schemas/project.schema.json` — _Depends: E1.F2.T3_

**Estimate:** 30 min  
**Files:** `plugins/karvey/schemas/spec.schema.json` (NEW); `plugins/karvey/schemas/project.schema.json` (NEW); `plugins/karvey/tests/unit/test_schemas.py` (NEW)  
**Requirements:** REQ-W1-001, REQ-W1-002, REQ-W1-003, REQ-W1-006, REQ-W1-007, REQ-W1-026, REQ-W1-027, REQ-W1-061, REQ-W1-071, REQ-W1-088, REQ-W1-093, REQ-W1-098  
**Tests added:** `test_schemas.py`: this repo's project.json validates; prod `by` with prose `ref` → error (the H-22 shape); `prod_gate_hook: "no"` → error; `knowledge_sync: none`, `detail`, `sprints`, `statuses` null and `by_level` accepted  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_schemas.py' -v` passes.
- Exactly §2.2 and §2.6; `x-karvey-safe` kinds named for `safe_values` (F7.T1).

### E1.F2.T6 [Backend] `schemas/state-machine.json` and `schemas/legacy-phase-map.json` — _Depends: E1.F2.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/schemas/state-machine.json` (NEW); `plugins/karvey/schemas/legacy-phase-map.json` (NEW); `plugins/karvey/tests/unit/test_state_machine_data.py` (NEW)  
**Requirements:** REQ-W1-001, REQ-W1-004, REQ-W1-005, REQ-W1-007, REQ-W1-009, REQ-W1-057  
**Tests added:** `test_state_machine_data.py`: phase ids == `spec.schema.json` phase enum; skippable = {mockup, design_graphic, infra}; reopen targets; every exact- and proposed-tier target is in the enum; `iterate` and null are unmappable  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_machine_data.py' -v` passes.
- §2.1 graph with produces/reads; §2.5 tiers (exact, proposed behind `--accept-proposed` per D-09, unmappable).

## Feature E1.F3: State tool `karvey-state.py`

Owns every write to phase, approvals, skipped, phase_history; marker store and release ledger (§1.2, §2.4, §3.3).  
Requirements covered: 001, 003, 004, 005, 006, 007, 008, 009, 010, 011, 016, 018, 023, 031, 032, 045, 109  
Total estimated time: 195 min (6 tasks)

### E1.F3.T1 [Backend] `karvey-state.py` CLI and `validate` (schema + semantic checks, advisory/strict) — _Depends: E1.F2.T2, E1.F2.T4, E1.F2.T5, E1.F2.T6_

**Estimate:** 30 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (NEW); `plugins/karvey/tests/unit/test_state_validate.py` (NEW)  
**Requirements:** REQ-W1-001, REQ-W1-003, REQ-W1-109  
**Tests added:** `test_state_validate.py`: enum; prod `by` without `ref` → error exit 1; advisory vs strict (`--strict`, `schema_mode`); history gap and out-of-order; §2.3 table; higher `schema_version` → exit 4  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_validate.py' -v` passes and `python3 plugins/karvey/scripts/karvey-state.py validate --all --root . --json` exits 0 or 1 with a well-formed envelope (errors expected until F15).
- Shared CLI contract (§1.1): `--root`, `--json`, exit codes. `validate [PATH…|--all]`.

### E1.F3.T2 [Backend] `validate --fix` migration (exact tier, `--accept-proposed`, `--dry-run`, idempotent) — _Depends: E1.F3.T1_

**Estimate:** 45 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/tests/unit/test_state_fix.py` (NEW)  
**Requirements:** REQ-W1-009, REQ-W1-010  
**Tests added:** `test_state_fix.py` (inline mini files; the full catalogue arrives in F14.T1): exact tier; proposed tier only with the flag; `shipping` unmappable → exit 3, no write; `gates_skipped`; embedded skips; `management` string / `none` / `42`; `approvals: null`; hand-written `{from,to,at}` history; second run is a no-op; no `approvals.*.approved` value changes (asserted by diff)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_fix.py' -v` passes.
- Unified diff to stdout first, then write unless `--dry-run` (§2.5).

### E1.F3.T3 [Backend] `next` and `active` commands — _Depends: E1.F3.T2_

**Estimate:** 20 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/tests/unit/test_state_next.py` (NEW)  
**Requirements:** REQ-W1-005, REQ-W1-045  
**Tests added:** `test_state_next.py`: `next` for every phase; this change's shape (mockup/design_graphic skipped → architecture); invalid file → status `invalid` with errors; `active` over archive/IMPLEMENTED/deployed  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_next.py' -v` passes and `python3 plugins/karvey/scripts/karvey-state.py next wave1-hardening --json` prints a `status` field.
- `next` reads `state-machine.json`; `active` delegates to `project.active` (F2.T4).

### E1.F3.T4 [Backend] `advance`, `generated`, `skip`, `reopen` with history, lock and legacy in-memory mapping — _Depends: E1.F3.T3_

**Estimate:** 40 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/tests/unit/test_state_transitions.py` (NEW)  
**Requirements:** REQ-W1-004, REQ-W1-007, REQ-W1-008, REQ-W1-011  
**Tests added:** `test_state_transitions.py`: allowed edge; refused edge leaves the file byte-identical; skipped satisfies a precondition; non-skippable skip refused; empty reason refused; `reopen` moves downstream approvals to `revision_history`; lock + CAS; `deployed` needs ledger evidence; `archived` preconditions  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_transitions.py' -v` passes.
- Refusal messages name the missing phase (`requirements not approved or skipped`).

### E1.F3.T5 [Backend] Marker store and release ledger in `approval.py` — _Depends: E1.F2.T2, E1.F2.T4_ (P)

**Estimate:** 30 min  
**Files:** `plugins/karvey/scripts/karvey_lib/approval.py` (NEW: marker + ledger half); `plugins/karvey/tests/unit/test_marker.py` (NEW)  
**Requirements:** REQ-W1-016, REQ-W1-018, REQ-W1-023  
**Tests added:** `test_marker.py`: write/read/validate `v:1`; TTL clamp 5..1440 and 121-min expiry; consumed; empty `touch` file ignored and audited; wrong repo; transcript cross-check advisory only; `KARVEY_COMPAT_MARKER` path written as well (D-11); ledger read/write 0600  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_marker.py' -v` passes.
- Location `<git-common-dir>/karvey/{approvals,ledger}` (§2.4).

### E1.F3.T6 [Backend] `approve` (prod → ledger, `--write-spec`), `check-prod`, marker consumption on `advance` — _Depends: E1.F3.T4, E1.F3.T5_

**Estimate:** 30 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/tests/unit/test_state_approve.py` (NEW)  
**Requirements:** REQ-W1-006, REQ-W1-016, REQ-W1-023, REQ-W1-031, REQ-W1-032  
**Tests added:** `test_state_approve.py`: missing by/role/ref → refuse; `ceo-delegate` on prod → refuse; prod without a prod-kind marker → refuse; ledger written, spec.json untouched; `--write-spec` copies ledger or D-NN; `check-prod` envelope; non-prod approval without marker → warning + `evidence.marker: none`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_approve.py' -v` passes.
- D-03 and D-10 literally: prod needs a prod-kind marker and writes the ledger, never spec.json (except `--write-spec`).

## Feature E1.F4: Hook runtime: parser, shell segmentation, dispatcher, table runner

`hookio`, `shellparse`, `karvey-hook.sh`, `karvey_hooks.py`, `hooks.json`, `run_tables.py` (§1.3, §3.4, §3.6, §6.1).  
Requirements covered: 014, 017, 020, 024, 026, 028, 029, 030, 050  
Total estimated time: 130 min (4 tasks)

### E1.F4.T1 [Backend] `hookio.py`: tolerant payload parser and path normalisation — _Depends: E1.F1.T1, E1.F2.T1_ (P)

**Estimate:** 20 min  
**Files:** `plugins/karvey/scripts/karvey_lib/hookio.py` (NEW); `plugins/karvey/tests/unit/test_hookio.py` (NEW); `plugins/karvey/tests/unit/test_paths.py` (NEW)  
**Requirements:** REQ-W1-017, REQ-W1-028, REQ-W1-050  
**Tests added:** `test_hookio.py` against the captured fixtures of F1.T1 plus the alternative field names of A-1..A-3; non-JSON stdin; `test_paths.py`: `C:\…`, `/c/…`, `\\wsl$` (A-10)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_hookio.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_paths.py' -v` pass.
- Field order per A-2/A-3 as corrected by F1.T1.

### E1.F4.T2 [Backend] `shellparse.py`: segmentation, wrappers, recursion, `cd` and git global options — _Depends: E1.F2.T1_ (P)

**Estimate:** 40 min  
**Files:** `plugins/karvey/scripts/karvey_lib/shellparse.py` (NEW); `plugins/karvey/tests/unit/test_shellparse.py` (NEW)  
**Requirements:** REQ-W1-014, REQ-W1-020  
**Tests added:** `test_shellparse.py`: `;` `&&` `||` `|` `&` newline; env prefixes and `command/builtin/exec/time/nohup/env/sudo`; `bash -c`, `eval`, `$(…)`, backticks to depth 3; `cd` chains; `git -C/-c/--git-dir/--work-tree/--no-pager`; unbalanced quotes → `unparsed`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_shellparse.py' -v` passes.
- §3.4 Shell segmentation, nothing more.

### E1.F4.T3 [Backend] Dispatcher `karvey-hook.sh`, `karvey_hooks.py` entry points with the guard registry, new `hooks.json` events — _Depends: E1.F4.T1, E1.F4.T2, E1.F2.T4_

**Estimate:** 35 min  
**Files:** `plugins/karvey/hooks/karvey-hook.sh` (NEW); `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (NEW: events prompt/pre-bash/pre-edit/post-edit/session; guards registered as allow-stubs in the §1.3 order); `plugins/karvey/hooks/hooks.json` (MODIFY: +UserPromptSubmit, +PreToolUse, +PostToolUse); `plugins/karvey/hooks/tests/test-hooks.sh` (MODIFY)  
**Requirements:** REQ-W1-024, REQ-W1-026, REQ-W1-029  
**Tests added:** `test-hooks.sh`: the BUG-18 case generalised — **every** `command` declared in hooks.json is executed with `bash -c` as written, plus a plugin path with spaces; no-python dispatcher path exits by fail mode; the existing 32 cases stay green  
**Done when:** `bash plugins/karvey/hooks/tests/test-hooks.sh` exits 0.
- Commands use **double-quoted** `"${CLAUDE_PLUGIN_ROOT}"` (BUG-18), not the single quotes shown in architecture §1.3.
- Interpreter discovery `python3` → `python` (major 3) → `py -3`; bash-only classifier for the no-python fail modes of §3.2; internal budget below each timeout (A-7).

### E1.F4.T4 [Test] Table runner `run_tables.py` (throw-away repos, bare origin, CLI stubs, `nopy` pass) — _Depends: E1.F4.T3_

**Estimate:** 35 min  
**Files:** `plugins/karvey/tests/hooks/run_tables.py` (NEW); `plugins/karvey/tests/hooks/tables/smoke.json` (NEW); `plugins/karvey/tests/hooks/stubs/{gh,az,glab}` (NEW)  
**Requirements:** REQ-W1-030  
**Tests added:** `smoke.json` (allow + block + nopy); the runner asserts decision, stdout/stderr substrings, `marker_created`, and duration < 1 s per non-network case  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --tag smoke` exits 0 and prints the case count.
- Case format of §6.1; `--tag`, `--junit`; `PATH` stripped of python for `nopy`.

## Feature E1.F5: Guards and the approval hook

protect-paths, approval hook, plan-gate, git-flow, prod-gate, post-edit validator and pending-sync, legacy shims (§1.3, §3.2..§3.5).  
Requirements covered: 014, 015, 016, 017, 018, 019, 020, 021, 022, 023, 024, 025, 026, 027, 028, 029, 035, 063  
Total estimated time: 275 min (8 tasks)

### E1.F5.T1 [Backend] protect-paths guard and its table — _Depends: E1.F4.T4, E1.F3.T5_

**Estimate:** 20 min  
**Files:** `plugins/karvey/scripts/karvey_lib/guards.py` (NEW: protect_paths); `plugins/karvey/tests/hooks/tables/protect-paths.json` (NEW, 13 cases)  
**Requirements:** REQ-W1-018  
**Tests added:** `protect-paths.json`: touch/echo/cp/mv/python on the literal path (6), Write/Edit on the marker (3), plugin root (2), compat marker (2); active with plan-gate **off**  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only protect-paths` exits 0.
- Block message names D-01 and tells the agent to wait for the human.

### E1.F5.T2 [Backend] Approval hook: vocabulary, quote stripping, prod kind (D-10), scope, compat marker (D-11) — _Depends: E1.F3.T5, E1.F4.T4_ (P)

**Estimate:** 45 min  
**Files:** `plugins/karvey/scripts/karvey_lib/approval.py` (MODIFY: vocabulary half); `plugins/karvey/scripts/karvey_lib/vocabulary.json` (NEW); `plugins/karvey/tests/unit/test_approval_vocab.py` (NEW); `plugins/karvey/tests/hooks/tables/approval.json` (NEW, ≥ 28 cases)  
**Requirements:** REQ-W1-016, REQ-W1-017, REQ-W1-019  
**Tests added:** `test_approval_vocab.py` (normalisation, stripping, negation precedence, 12-word/120-char position rule, kind); `approval.json` with the REQ-W1-019 minimums (5 approvals / 5 negations-questions / 2 quoted) plus prod kind (4), scope (4), non-Karvey (1), long prompt (2); 80-char excerpt; fail open with an audit line  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_approval_vocab.py' -v` passes and `python3 plugins/karvey/tests/hooks/run_tables.py --only approval` exits 0.
- Vocabulary from `project.json` read from the reviewed line (§3.5); prints `[karvey] approval recorded (<kind>, <scope>, expires hh:mm)`.

### E1.F5.T3 [Backend] plan-gate classifier and its table — _Depends: E1.F5.T1, E1.F5.T2_

**Estimate:** 45 min  
**Files:** `plugins/karvey/scripts/karvey_lib/guards.py` (MODIFY: plan_gate); `plugins/karvey/tests/hooks/tables/plan-gate.json` (NEW, ~40 cases)  
**Requirements:** REQ-W1-014, REQ-W1-015, REQ-W1-016  
**Tests added:** `plan-gate.json`: redirections (8), writes (6), each of the 12 destructive classes, Edit/Write (4), marker scope/TTL/consumed/forged (6), limitations (2); H-10 set (`ls 2>/dev/null` allow · `git clean -fdx`, `find . -delete`, `sed -i`, `rm -rf build` block); `echo "a > b"` allow  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only plan-gate` exits 0.
- Block message never tells the agent to create anything.

### E1.F5.T4 [Backend] git-flow guard (target repo per segment, aliases, whole-name match, trunk) and its table — _Depends: E1.F5.T3_

**Estimate:** 50 min  
**Files:** `plugins/karvey/scripts/karvey_lib/guards.py` (MODIFY: git_flow); `plugins/karvey/tests/hooks/tables/git-flow.json` (NEW, ~49 cases)  
**Requirements:** REQ-W1-020, REQ-W1-021, REQ-W1-022, REQ-W1-035  
**Tests added:** `git-flow.json`: commit (8), push (14), merge/cherry-pick (6), manual deploy (7), target resolution (8), trunk (6); H-12 set; `git push origin dev` from feature allow (Q-A9, D-09); `git push -f origin dev` block; `git merge` on main in trunk block  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only git-flow` exits 0.
- Rule table of §3.4; unresolvable target → block naming the rewrite.

### E1.F5.T5 [Backend] prod-gate: candidates, production set, base and change resolution, `check-prod` — _Depends: E1.F5.T4, E1.F3.T6_

**Estimate:** 45 min  
**Files:** `plugins/karvey/scripts/karvey_lib/guards.py` (MODIFY: prod_gate); `plugins/karvey/tests/hooks/tables/prod-gate.json` (NEW, first ~30 cases)  
**Requirements:** REQ-W1-023, REQ-W1-024, REQ-W1-035  
**Tests added:** `prod-gate.json` part 1: `gh pr merge` variants (10), `gh api` (4, GraphQL → block), `az repos` (4), `glab` (3), `git push` to production (5), wrappers (6 incl. `bash -c`, env prefix); ALLOW line with ledger; PR into dev allow silent; renamed `production` with `main` as origin/HEAD still gated; gh stub timeout → block  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only prod-gate` exits 0.
- 6 s network budget within the 15 s timeout (A-7).

### E1.F5.T6 [Backend] prod-gate: reviewed-line switch-off, fail-closed reasons, audit lines, `nopy` classifier — _Depends: E1.F5.T5_

**Estimate:** 30 min  
**Files:** `plugins/karvey/scripts/karvey_lib/guards.py` (MODIFY); `plugins/karvey/tests/hooks/tables/prod-gate.json` (MODIFY: +~14 cases)  
**Requirements:** REQ-W1-024, REQ-W1-025, REQ-W1-026, REQ-W1-027  
**Tests added:** `prod-gate.json` part 2: no key → on; `false` in both → DISABLED + allow; `false` only in the working copy → block; `"no"` → block; corrupt spec.json → `cannot verify`; hand-edited `approvals.prod` without ledger → block; non-Karvey repo → silent; several `deploying` → warning; `nopy` pass; one audit line per decision  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only prod-gate` and `python3 plugins/karvey/tests/hooks/run_tables.py --tag nopy` exit 0.
- §3.2 and §3.5 for the prod-gate row.

### E1.F5.T7 [Backend] post-edit: spec-write validator and pending-sync recorder — _Depends: E1.F3.T1, E1.F4.T4_ (P)

**Estimate:** 25 min  
**Files:** `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (MODIFY: post-edit); `plugins/karvey/tests/hooks/tables/spec-write.json` (NEW, 11 cases)  
**Requirements:** REQ-W1-028, REQ-W1-063  
**Tests added:** `spec-write.json`: valid (2), enum violation (2, incl. `phase: "qa-approved"`), prod ref missing (1), non-spec file (2), outside docs/spec (1), invalid JSON (1), nopy (1); `.graph-pending` appended sorted/deduped/LF, never for itself or `graphify-out/**`  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only spec-write` exits 0.
- Exit 2 with the violations on stderr, or the fallback of A-4 if F1.T1 corrected it.

### E1.F5.T8 [Backend] Legacy template shims (`--only <guard> --force-enabled`) — _Depends: E1.F5.T4, E1.F6.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/skills/karvey/hooks/git-flow-guard.sh` (MODIFY → shim); `plugins/karvey/skills/karvey/hooks/plan-gate.sh` (MODIFY → shim); `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (MODIFY: flags); `plugins/karvey/tests/hooks/tables/shims.json` (NEW, 4 cases)  
**Requirements:** REQ-W1-016, REQ-W1-020, REQ-W1-029  
**Tests added:** `shims.json`: each shim run as a 3.11 `settings.json` entry would run it gives the dispatcher's decision with the guard force-enabled  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only shims` exits 0.
- Deprecation note in each shim: removed in 4.0.0.

## Feature E1.F6: Session hook and handoff capture (on the 3.11.4 code)

Bounded, structured SessionStart context and `state.json` written by a script (§1.4, §1.5). Builds on BUG-18..21 fixes; does not redo them.  
Requirements covered: 045, 046, 047, 048, 050, 051, 083  
Total estimated time: 130 min (4 tasks)

### E1.F6.T1 [Backend] `karvey_hooks.py session`: active change, manifest xor, bounded board/handoff, structured output (port of the 3.11.4 logic) — _Depends: E1.F4.T3, E1.F2.T4, E1.F5.T7_

**Estimate:** 45 min  
**Files:** `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (MODIFY: session); `plugins/karvey/hooks/karvey-session-context.sh` (MODIFY: delegate to python when present)  
**Requirements:** REQ-W1-045, REQ-W1-046, REQ-W1-047  
**Tests added:** covered by `session.json` (F6.T4); the 32 existing `test-hooks.sh` cases must stay green after the port  
**Done when:** `bash plugins/karvey/hooks/tests/test-hooks.sh` exits 0 (all 32 legacy cases).
- Replace `ls -1dt changes/*/` with `project.active` (excludes archive/ and IMPLEMENTED — H-08).
- **Port, do not rewrite,** the 3.11.4 live-state code: `resolve()` (BUG-20: `''`, `.` or the root's name = the root) and `is_repo()` via `git rev-parse --git-dir` (BUG-21, finding F-01), and the BUG-19 profile resolution (sibling ops repo or the folder holding team.json). Architecture §1.4's "worktree fix, to log as a finding" is already done: no new work there.
- Compact manifest wins over full (H-09); open board rows ≤ 40 + `… N more`; handoff ≤ 6 KB cut at a line; `hookSpecificOutput.additionalContext` JSON (plain text fallback per A-6 / F1.T1).

### E1.F6.T2 [Backend] Settings notice on `startup` only, `origin/{integration}` check, legacy-shape message; SessionStart split by matcher — _Depends: E1.F6.T1_

**Estimate:** 30 min  
**Files:** `plugins/karvey/hooks/karvey-session-context.sh` (MODIFY); `plugins/karvey/hooks/hooks.json` (MODIFY: startup vs resume|compact|clear, double-quoted); `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (MODIFY)  
**Requirements:** REQ-W1-050, REQ-W1-083  
**Tests added:** covered by `session.json` (F6.T4); the BUG-18 "every declared command runs" case of F4.T3 covers both new SessionStart entries  
**Done when:** `bash plugins/karvey/hooks/tests/test-hooks.sh` exits 0.
- `git show origin/{integration}:docs/spec/project.json`, no fetch (REQ-W1-083); a `management` string counts as present-but-legacy; degraded bash line without python (REQ-W1-050).

### E1.F6.T3 [Backend] `karvey-handoff-capture.py` writes `state.json` in the shape the 3.11.4 resolver reads — _Depends: E1.F2.T2, E1.F2.T4_ (P)

**Estimate:** 25 min  
**Files:** `plugins/karvey/scripts/karvey-handoff-capture.py` (NEW); `plugins/karvey/tests/unit/test_handoff_capture.py` (NEW)  
**Requirements:** REQ-W1-048  
**Tests added:** `test_handoff_capture.py`: values equal `git rev-parse` / `log -1 %h` / `status --porcelain`; unmeasurable repo → `measured:false` + reason; worktree measured; in-repo team writes the repo name (resolved by BUG-20 logic); profile dir missing → exit 4  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_handoff_capture.py' -v` passes.
- `--profile`, `--repos-from`, `--scheduled-tasks`, `--ready-to-rotate`, `--dry-run`, `--json` (§1.5).

### E1.F6.T4 [Test] `session.json` table; `test-hooks.sh` becomes the entry point that also runs the tables — _Depends: E1.F6.T2, E1.F6.T3, E1.F4.T4_

**Estimate:** 30 min  
**Files:** `plugins/karvey/tests/hooks/tables/session.json` (NEW, 23 cases); `plugins/karvey/hooks/tests/test-hooks.sh` (MODIFY)  
**Requirements:** REQ-W1-045, REQ-W1-046, REQ-W1-047, REQ-W1-050, REQ-W1-051, REQ-W1-083  
**Tests added:** `session.json`: active selection (5), manifest (3), bounds (4), settings notice (8: `"notifications": {}` startup → 1 line, resume → none; bare `docs/spec/openapi.yaml` above the git top level → none; settings only on `origin/main` → none; no python → degraded line), structured output (2), worktree (1)  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only session` and `bash plugins/karvey/hooks/tests/test-hooks.sh` exit 0.
- test-hooks.sh keeps its 32 cases and calls `run_tables.py` at the end.

## Feature E1.F7: Settings resolver `karvey-config.py` and safe values

Resolution order, `get --shell`, notify-check, outbox, propose-settings (§1.8, §3.1).  
Requirements covered: 010, 080, 082, 086, 087, 088, 090, 093, 097, 098, 099  
Total estimated time: 85 min (3 tasks)

### E1.F7.T1 [Backend] `safe_values.py` patterns and the no-shell rule — _Depends: E1.F2.T1_ (P)

**Estimate:** 25 min  
**Files:** `plugins/karvey/scripts/karvey_lib/safe_values.py` (NEW); `plugins/karvey/tests/unit/test_safe_values.py` (NEW); `plugins/karvey/tests/unit/test_no_shell_true.py` (NEW)  
**Requirements:** REQ-W1-093, REQ-W1-097  
**Tests added:** `test_safe_values.py`: accept/reject pairs for every §3.1 pattern incl. `spaces/AAA; rm -rf ~`, `://`, leading `-`, spreadsheet `../x.csv`; `test_no_shell_true.py`: grep of `scripts/` for `shell=True|os.system|os.popen` → zero hits  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_safe_values.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_no_shell_true.py' -v` pass.
- Metacharacter and control-character refusal common to every kind.

### E1.F7.T2 [Backend] `karvey-config.py resolve | get --shell | propose-settings` — _Depends: E1.F7.T1, E1.F2.T4, E1.F2.T5_

**Estimate:** 30 min  
**Files:** `plugins/karvey/scripts/karvey-config.py` (NEW); `plugins/karvey/tests/unit/test_config_resolve.py` (NEW)  
**Requirements:** REQ-W1-010, REQ-W1-080, REQ-W1-082, REQ-W1-086, REQ-W1-087, REQ-W1-088, REQ-W1-099  
**Tests added:** `test_config_resolve.py`: spec override → project order; legacy string / object / `none`; `external` false for markdown/none; `missing` lists statuses/location; `statuses` null = unsupported state; `get --shell` exit 3 naming key and rule; `propose-settings` prints and never writes; no CLAUDE.md read (REQ-W1-099)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_config_resolve.py' -v` passes.
- §1.8 table rows 1–3 and 6.

### E1.F7.T3 [Backend] `karvey-config.py notify-check [--confirm]` and `outbox add|list|done` — _Depends: E1.F7.T2_

**Estimate:** 30 min  
**Files:** `plugins/karvey/scripts/karvey-config.py` (MODIFY); `plugins/karvey/tests/unit/test_notify_check.py` (NEW); `plugins/karvey/tests/unit/test_config_resolve.py` (MODIFY: outbox cases)  
**Requirements:** REQ-W1-090, REQ-W1-097, REQ-W1-098  
**Tests added:** `test_notify_check.py`: unchanged → 0; changed → 10 with the new destination; `--confirm` records the hash; `://` → 3; `detail` defaults to counts. Outbox: add/list/done; a child under a pending parent → `blocked_by`, never sent  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_notify_check.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_config_resolve.py' -v` pass.
- Exit 10 = confirmation required.

## Feature E1.F8: Dashboard `karvey-context.py`

Read-only open work, age, approvals, WIP, enforcement, calibration, convergence, close report (§1.7).  
Requirements covered: 026, 043, 044, 068, 069, 070, 071, 072, 090, 107, 108  
Total estimated time: 80 min (2 tasks)

### E1.F8.T1 [Backend] `karvey-context.py`: overview, open work, approvals, WIP, enforcement (read-only) — _Depends: E1.F3.T3, E1.F7.T3, E1.F2.T4_

**Estimate:** 45 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (NEW); `plugins/karvey/tests/unit/test_context.py` (NEW); `plugins/karvey/tests/unit/fixtures/context/` (NEW mini tree)  
**Requirements:** REQ-W1-026, REQ-W1-068, REQ-W1-069, REQ-W1-070, REQ-W1-071, REQ-W1-072, REQ-W1-090  
**Tests added:** `test_context.py` part 1: OPEN WORK from fixtures (findings, non-RESUELTO BUG-NN, 🙋 human tasks, open backlog, outbox); unreadable file shown and the rest renders; age / stalled / `unknown`; approvals incl. `skipped` and `approver missing`; WIP; tree hash before == after (read-only, also under `--json`); tables parsed by header name (column reorder gives same values)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context.py' -v` passes.
- Exit 4 without docs/spec.

### E1.F8.T2 [Backend] `karvey-context.py`: calibration, close report, convergence, audit block counts — _Depends: E1.F8.T1_

**Estimate:** 35 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (MODIFY); `plugins/karvey/tests/unit/test_context.py` (MODIFY)  
**Requirements:** REQ-W1-043, REQ-W1-044, REQ-W1-107, REQ-W1-108  
**Tests added:** `test_context.py` part 2: calibration ≥ 3 changes vs < 3 ("not enough history"), ±30 % over 3 (D-07); close report lists tasks without an actual; convergence exit 1 while a bug/spec-gap is open/routed or a routed BUG-NN is not RESUELTO with a named regression  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context.py' -v` passes and `python3 plugins/karvey/scripts/karvey-context.py --section convergence --change team-adapters` exits 1 today (not converged).
- `--section convergence --change X` is the check REQ-W1-108 uses at QA.

## Feature E1.F9: Spec-delta merge `karvey-spec-merge.py`

Deterministic ADDED/MODIFIED/REMOVED merge with dry run (§1.9).  
Requirements covered: 065, 066  
Total estimated time: 40 min (1 tasks)

### E1.F9.T1 [Backend] `karvey-spec-merge.py` (ADDED / MODIFIED / REMOVED, `--dry-run`) — _Depends: E1.F2.T1, E1.F2.T2_ (P)

**Estimate:** 40 min  
**Files:** `plugins/karvey/scripts/karvey-spec-merge.py` (NEW); `plugins/karvey/tests/unit/test_spec_merge.py` (NEW)  
**Requirements:** REQ-W1-065, REQ-W1-066  
**Tests added:** `test_spec_merge.py`: each section; idempotent second run; missing MODIFIED id → nothing written, id named, exit 1; `--dry-run` writes nothing; unparsable section → line number + exit 3; this change's real `spec-delta.md` against a temp copy of `docs/spec/specs/method/spec.md`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_spec_merge.py' -v` passes and `python3 plugins/karvey/scripts/karvey-spec-merge.py wave1-hardening --dry-run` exits 0 without modifying `docs/spec/specs/method/spec.md` (`git diff --quiet -- docs/spec/specs` → 0).
- Q-A3 / D-09: the name is `karvey-spec-merge.py`.

## Feature E1.F10: Plugin linter `lint-plugin.py`

L-01..L-35 registry, `--list`, `--format github` (§1.6).  
Requirements covered: 001, 002, 005, 012, 013, 022, 029, 031, 033, 034, 036, 038, 039, 040, 042, 049, 051, 052, 053, 055, 056, 057, 058, 059, 060, 062, 064, 073, 074, 075, 076, 077, 078, 079, 081, 084, 085, 086, 087, 091, 092, 093, 094, 095, 099, 107, 109  
Total estimated time: 260 min (6 tasks)

### E1.F10.T1 [Backend] Linter framework (registry, `--list`, `--only`, `--paths`, formats) and L-01..L-04 — _Depends: E1.F2.T1_ (P)

**Estimate:** 45 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (NEW); `plugins/karvey/tests/unit/test_lint_plugin.py` (NEW); `plugins/karvey/tests/unit/fixtures/lint/` (NEW mini plugins, pass + fail per check)  
**Requirements:** REQ-W1-055, REQ-W1-077, REQ-W1-078, REQ-W1-079  
**Tests added:** `test_lint_plugin.py`: pass/fail fixture for L-01..L-04; `--list` fails when a claimed REQ is absent from requirements.md; `--format github` annotations; exit codes 0/1/2  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --list` exits 0.
- `--paths GLOB` limits findings to files (used by the F12 tasks as their done-criterion; an implementation convenience, not a new check).

### E1.F10.T2 [Backend] Linter L-05..L-10 and L-14 (phase literals, no hand phase edits, `next`, produces/reads, paths, rule copies, allowed-tools) — _Depends: E1.F10.T1, E1.F2.T6_

**Estimate:** 50 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (MODIFY); `plugins/karvey/tests/unit/test_lint_plugin.py` (MODIFY); `plugins/karvey/tests/unit/fixtures/lint/`  
**Requirements:** REQ-W1-001, REQ-W1-005, REQ-W1-012, REQ-W1-013, REQ-W1-052, REQ-W1-053, REQ-W1-056, REQ-W1-057  
**Tests added:** pass/fail fixture per check; L-08 fails on `proposal.md` and `specs/*/spec-delta.md`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes.
- Against the real repo these checks report findings until F12 lands; that is expected.

### E1.F10.T3 [Backend] Linter L-11..L-13, L-17, L-18 (counts, versions, release docs, rule JSON vs schema, docs/spec validate) — _Depends: E1.F10.T2, E1.F3.T1, E1.F2.T5_

**Estimate:** 40 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (MODIFY); `plugins/karvey/tests/unit/test_lint_plugin.py` (MODIFY)  
**Requirements:** REQ-W1-002, REQ-W1-055, REQ-W1-058, REQ-W1-109  
**Tests added:** pass/fail fixture per check; L-12 treats `[Unreleased]` as not a release; L-18 calls the state tool's validator in-process  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes.

### E1.F10.T4 [Backend] Linter L-15, L-16 (hooks exist; guard-case anchors match the tables) and L-19..L-24 — _Depends: E1.F10.T3_

**Estimate:** 50 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (MODIFY); `plugins/karvey/tests/unit/test_lint_plugin.py` (MODIFY)  
**Requirements:** REQ-W1-022, REQ-W1-029, REQ-W1-036, REQ-W1-038, REQ-W1-039, REQ-W1-040, REQ-W1-042, REQ-W1-049, REQ-W1-051, REQ-W1-062, REQ-W1-064  
**Tests added:** pass/fail fixture per check; L-16: an unanchored promise fails, an anchor to a missing table id fails, a verb class that contradicts the case's decision fails; L-15 fails on `clickup-sync-guard` / `standards-guard`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes.

### E1.F10.T5 [Backend] Linter L-25..L-30 (QA, stack rules, deploy/archive, management, shell interpolation, H-33) — _Depends: E1.F10.T4_

**Estimate:** 45 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (MODIFY); `plugins/karvey/tests/unit/test_lint_plugin.py` (MODIFY)  
**Requirements:** REQ-W1-031, REQ-W1-033, REQ-W1-034, REQ-W1-059, REQ-W1-073, REQ-W1-074, REQ-W1-075, REQ-W1-076, REQ-W1-084, REQ-W1-085, REQ-W1-086, REQ-W1-087, REQ-W1-091, REQ-W1-092, REQ-W1-093, REQ-W1-094, REQ-W1-095  
**Tests added:** pass/fail fixture per check; L-29 fails an unquoted or unvalidated `project.json` value in a command example  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes.

### E1.F10.T6 [Backend] Linter L-31..L-35 (public tracker text, RESUELTO needs a regression, duplicate ids, subagent project.json writes, CHANGELOG compat line) — _Depends: E1.F10.T5_

**Estimate:** 30 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (MODIFY); `plugins/karvey/tests/unit/test_lint_plugin.py` (MODIFY)  
**Requirements:** REQ-W1-060, REQ-W1-081, REQ-W1-099, REQ-W1-107  
**Tests added:** pass/fail fixture per check; L-33 advisory only; L-35 applies from the 3.12.0 release entry on  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_plugin.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --list` lists L-01..L-35.

## Feature E1.F11: Statusline and method page

BUG-08/09 statusline, BUG-10..14 method page with node tests (§1.10).  
Requirements covered: 049, 100, 101, 102, 103, 104, 105, 106  
Total estimated time: 70 min (2 tasks)

### E1.F11.T1 [Backend] Statusline: visible invalid TZ, clean separators, rotation default from `defaults.json` — _Depends: E1.F2.T1, E1.F4.T4_ (P)

**Estimate:** 25 min  
**Files:** `plugins/karvey/hooks/karvey-statusline.sh` (MODIFY); `plugins/karvey/tests/hooks/tables/statusline.json` (NEW, 8 cases)  
**Requirements:** REQ-W1-049, REQ-W1-100, REQ-W1-101  
**Tests added:** `statusline.json`: TZ (3, invalid → `(TZ?)`), windows (3, `' · '.join`), rotation default (2, `rot?` when defaults.json is missing); the existing BUG-03/04 cases in test-hooks.sh stay green  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only statusline` and `bash plugins/karvey/hooks/tests/test-hooks.sh` exit 0.
- No second literal for the 8 h threshold (D-06).

### E1.F11.T2 [Frontend] Method page `docs/karvey.html`: pure functions + `init(window)`; BUG-10..14 fixed; node and static tests (P)

**Estimate:** 45 min  
**Files:** `docs/karvey.html` (MODIFY: inline script); `plugins/karvey/tests/page/test_page.mjs` (NEW, node:test, no npm); `plugins/karvey/tests/unit/test_page_static.py` (NEW, html.parser)  
**Requirements:** REQ-W1-102, REQ-W1-103, REQ-W1-104, REQ-W1-105, REQ-W1-106  
**Tests added:** `test_page.mjs`: `safeDecodeHash` (BUG-10), `pickLang` one-off vs saved (BUG-11), `withLang` keeps params (BUG-12), `init` binds `hashchange` (BUG-13); `test_page_static.py`: no visible switch without `.js` (BUG-14)  
**Done when:** `node --test plugins/karvey/tests/page/` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` pass.
- Q-A7 / D-09: `node --test`, no npm. The version-history block is **not** touched here (F16.T1).

## Feature E1.F12: Skill and rule text changes

§8: deterministic parts become script calls; rule copies deleted; frontmatter shortened. Ends with the whole-repo lint gate.  
Requirements covered: 001, 002, 004, 005, 006, 007, 011, 012, 013, 016, 017, 018, 022, 026, 027, 029, 031, 032, 033, 034, 035, 036, 037, 038, 039, 040, 041, 042, 043, 044, 046, 048, 049, 051, 052, 053, 055, 056, 057, 059, 060, 061, 062, 063, 064, 065, 066, 067, 068, 069, 070, 071, 072, 073, 074, 075, 076, 077, 078, 079, 080, 081, 082, 083, 084, 085, 086, 087, 088, 089, 090, 091, 092, 093, 094, 095, 097, 098, 099, 107  
Total estimated time: 445 min (13 tasks)

### E1.F12.T1 [Backend] Delete the 9 rule copies; rewrite references to `../karvey/rules/x.md` — _Depends: E1.F10.T2_

**Estimate:** 20 min  
**Files:** `plugins/karvey/skills/{karvey-architecture,karvey-init,karvey-requirements,karvey-tasks}/rules/` (DELETE 9 files); `plugins/karvey/skills/*/SKILL.md` (references only)  
**Requirements:** REQ-W1-052, REQ-W1-053  
**Tests added:** L-09, L-10  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-09,L-10` exits 0.
- Mechanical; no other text change here, so the later text tasks start from a clean base.

### E1.F12.T2 [Backend] New rule `rules/state-machine.md` (generated block) and its agreement test — _Depends: E1.F2.T6_ (P)

**Estimate:** 20 min  
**Files:** `plugins/karvey/skills/karvey/rules/state-machine.md` (NEW); `plugins/karvey/tests/unit/test_state_machine_rule.py` (NEW)  
**Requirements:** REQ-W1-001, REQ-W1-004, REQ-W1-005  
**Tests added:** `test_state_machine_rule.py`: the `<!-- generated:state-machine -->` block equals `state-machine.json`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_machine_rule.py' -v` passes.
- Preconditions, reopen, where each phase is committed (D-03).

### E1.F12.T3 [Backend] Text: orchestrator `karvey/SKILL.md`, `karvey-init`, `karvey-requirements` — _Depends: E1.F12.T1, E1.F3.T6, E1.F7.T2_ (P)

**Estimate:** 45 min  
**Files:** `plugins/karvey/skills/karvey/SKILL.md`; `plugins/karvey/skills/karvey-init/SKILL.md`; `plugins/karvey/skills/karvey-requirements/SKILL.md`  
**Requirements:** REQ-W1-005, REQ-W1-006, REQ-W1-012, REQ-W1-013, REQ-W1-039, REQ-W1-056, REQ-W1-059, REQ-W1-061, REQ-W1-062, REQ-W1-077, REQ-W1-078, REQ-W1-083, REQ-W1-095  
**Tests added:** L-01..L-08, L-14, L-19, L-23, L-28, L-30 on these files  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --paths 'plugins/karvey/skills/{karvey,karvey-init,karvey-requirements}/SKILL.md'` exits 0.
- §8 rows 1–3: `next` replaces the phase table; `[Unreleased]` per commit, one bump per release; init writes through the state tool, `notifications.deferred`, docs-branch writes, one initial Epic state, no `E{1..99}`, no init sync; requirements reads `prd.md`, spec-delta at the change root, no graphify step; descriptions and triggers shortened.

### E1.F12.T4 [Backend] Text: `karvey-mockup`, `karvey-design-graphic`, `karvey-architecture`, `karvey-infra`, `karvey-tasks` — _Depends: E1.F12.T1, E1.F3.T6_ (P)

**Estimate:** 40 min  
**Files:** `plugins/karvey/skills/{karvey-mockup,karvey-design-graphic,karvey-architecture,karvey-infra,karvey-tasks}/SKILL.md`  
**Requirements:** REQ-W1-004, REQ-W1-007, REQ-W1-012, REQ-W1-013, REQ-W1-043, REQ-W1-062, REQ-W1-077, REQ-W1-078, REQ-W1-080, REQ-W1-081, REQ-W1-089  
**Tests added:** L-01..L-08, L-23, L-28 on these files  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --paths 'plugins/karvey/skills/{karvey-mockup,karvey-design-graphic,karvey-architecture,karvey-infra,karvey-tasks}/SKILL.md'` exits 0.
- §8 rows 4–6: state calls, `skip` path, approved-or-skipped precondition, no per-phase sync; tasks: PLAN.md row with `estimate_min · actual_ai_min · actual_review_min`, find-or-create by natural key, missing-map clause cited, status map as a tasks-gate precondition; tasks writes `phase` via the tool (not `tasks-generated`).

### E1.F12.T5 [Backend] Text: `karvey-impl`, `karvey-test`, `karvey-qa` — _Depends: E1.F12.T1, E1.F3.T6, E1.F7.T3_ (P)

**Estimate:** 45 min  
**Files:** `plugins/karvey/skills/{karvey-impl,karvey-test,karvey-qa}/SKILL.md`  
**Requirements:** REQ-W1-011, REQ-W1-036, REQ-W1-038, REQ-W1-040, REQ-W1-042, REQ-W1-043, REQ-W1-059, REQ-W1-073, REQ-W1-074, REQ-W1-076, REQ-W1-077, REQ-W1-078, REQ-W1-084, REQ-W1-085, REQ-W1-091, REQ-W1-097, REQ-W1-098  
**Tests added:** L-06, L-19..L-21, L-25, L-26, L-28, L-30 on these files  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --paths 'plugins/karvey/skills/{karvey-impl,karvey-test,karvey-qa}/SKILL.md'` exits 0.
- §8 rows 7–9: impl advances via the tool, `[Unreleased]` line per commit, actual as time entry / PLAN.md actual, logical-state resume; test consumes architecture §6, duplicate E2E block removed; qa never commits, review into `changes/{id}/qa/`, D6 checks `[Unreleased]`, stack rules out, notify-check + counts, approve moves `review` → `done`.

### E1.F12.T6 [Backend] Text: `karvey-deploy`, `karvey-archive`, `karvey-iterate` — _Depends: E1.F12.T1, E1.F3.T6, E1.F9.T1, E1.F8.T2_ (P)

**Estimate:** 45 min  
**Files:** `plugins/karvey/skills/{karvey-deploy,karvey-archive,karvey-iterate}/SKILL.md`  
**Requirements:** REQ-W1-011, REQ-W1-031, REQ-W1-032, REQ-W1-033, REQ-W1-034, REQ-W1-035, REQ-W1-037, REQ-W1-041, REQ-W1-044, REQ-W1-063, REQ-W1-065, REQ-W1-066, REQ-W1-067, REQ-W1-074, REQ-W1-077, REQ-W1-078, REQ-W1-084, REQ-W1-087  
**Tests added:** L-06, L-19, L-23, L-27, L-28 on these files  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --paths 'plugins/karvey/skills/{karvey-deploy,karvey-archive,karvey-iterate}/SKILL.md'` exits 0.
- §8 rows 10–12: checklist before the first push; `advance deploying` on the feature branch; one bump at the release step; prod OK → D-NN + PR + `approve prod` (ledger), never a commit on integration; trunk = one PR; visible-version check (recommendation when absent); archive on `chore/archive-{id}` with `advance deployed`, `approve prod --write-spec`, `advance archived`, spec-merge dry run then apply, calibration, sync here only; iterate uses `reopen` and `resolve management`.

### E1.F12.T7 [Backend] Text: context, checkpoint, guard, team, benchmark-models, scrape, import, retro, browse, health, decisions + `rules/multi-agent.md` — _Depends: E1.F12.T1, E1.F6.T3, E1.F8.T1_ (P)

**Estimate:** 45 min  
**Files:** `plugins/karvey/skills/{karvey-context,karvey-checkpoint,karvey-guard,karvey-team,karvey-benchmark-models,karvey-scrape,karvey-import,karvey-retro,karvey-browse,karvey-health,karvey-decisions}/SKILL.md`; `plugins/karvey/skills/karvey/rules/multi-agent.md`  
**Requirements:** REQ-W1-013, REQ-W1-017, REQ-W1-018, REQ-W1-046, REQ-W1-048, REQ-W1-049, REQ-W1-056, REQ-W1-059, REQ-W1-068, REQ-W1-069, REQ-W1-070, REQ-W1-071, REQ-W1-072, REQ-W1-077, REQ-W1-078, REQ-W1-079  
**Tests added:** L-01..L-04, L-06, L-14, L-22, L-30 on these files  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --paths 'plugins/karvey/skills/{karvey-context,karvey-checkpoint,karvey-guard,karvey-team,karvey-benchmark-models,karvey-scrape,karvey-import,karvey-retro,karvey-browse,karvey-health,karvey-decisions}/SKILL.md'` exits 0.
- §8 rows 13–18: context relays the script; checkpoint calls handoff-capture and cites `defaults.json`; guard sets `project.json:enforcement.*`, no `touch`, `--override` removed, detects 3.11 template entries; `disable-model-invocation: true` on the six rarely used skills; `Write` added where used; one decision-log path.

### E1.F12.T8 [Backend] Text: frontmatter of the remaining 7 skills (devex, diagram, docs, grill, investigate, second-opinion, standards) — _Depends: E1.F12.T1_ (P)

**Estimate:** 20 min  
**Files:** `plugins/karvey/skills/{karvey-devex,karvey-diagram,karvey-docs,karvey-grill,karvey-investigate,karvey-second-opinion,karvey-standards}/SKILL.md`  
**Requirements:** REQ-W1-077, REQ-W1-078  
**Tests added:** L-01..L-03  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-01,L-02,L-03,L-04` exits 0 (all 32 skills, since T3..T7 did theirs).
- Descriptions ≤ 250 in the `Karvey phase N | support — produces — when` shape; generic and third-party triggers removed.

### E1.F12.T9 [Backend] Rules A: `enforcement.md` (guard-case anchors), `deploy-workflow.md`, `versioning.md`, `knowledge-sync.md`, `engineering-standards.md` — _Depends: E1.F12.T1, E1.F5.T6, E1.F5.T8_ (P)

**Estimate:** 45 min  
**Files:** `plugins/karvey/skills/karvey/rules/{enforcement,deploy-workflow,versioning,knowledge-sync,engineering-standards}.md`  
**Requirements:** REQ-W1-016, REQ-W1-018, REQ-W1-022, REQ-W1-026, REQ-W1-027, REQ-W1-029, REQ-W1-031, REQ-W1-034, REQ-W1-035, REQ-W1-036, REQ-W1-039, REQ-W1-040, REQ-W1-051, REQ-W1-061, REQ-W1-062, REQ-W1-063  
**Tests added:** L-15, L-16, L-19, L-20, L-23, L-27  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-15,L-16,L-19,L-20,L-23,L-27 --paths 'plugins/karvey/skills/karvey/rules/*.md'` exits 0.
- Every behaviour promise in enforcement.md carries `<!-- guard-case: ID -->` pointing at a real table case; the interpreter-write limitation anchored to its case; `standards-guard` removed or marked not shipped.

### E1.F12.T10 [Backend] Rules B: phase-close, management-adapters, notifications, project-config, living-specs, team, clickup-protocol, backlog, incident-tracking — _Depends: E1.F12.T1, E1.F7.T3_ (P)

**Estimate:** 50 min  
**Files:** `plugins/karvey/skills/karvey/rules/{phase-close,management-adapters,notifications,project-config,living-specs,team,clickup-protocol,backlog,incident-tracking}.md`  
**Requirements:** REQ-W1-002, REQ-W1-029, REQ-W1-042, REQ-W1-049, REQ-W1-064, REQ-W1-080, REQ-W1-081, REQ-W1-082, REQ-W1-083, REQ-W1-084, REQ-W1-086, REQ-W1-087, REQ-W1-088, REQ-W1-089, REQ-W1-090, REQ-W1-091, REQ-W1-092, REQ-W1-093, REQ-W1-094, REQ-W1-097, REQ-W1-098, REQ-W1-099, REQ-W1-107  
**Tests added:** L-15, L-17, L-21, L-22, L-24, L-28, L-29, L-32  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --paths 'plugins/karvey/skills/karvey/rules/*.md'` exits 0.
- §8 rows for these rules: one missing-map clause, resolution order, per-level maps + `null`, the one cascade, `awaiting-human` 🙋 → `blocked`, natural keys, outbox, `none` alias, `sprints`, `get --shell`; notifications `://` refused + notify-check + `detail`; project-config/living-specs JSON blocks carry every new field; rotation cites defaults.json; estimate never overwritten; RESUELTO needs a named regression.

### E1.F12.T11 [Backend] `hooks/README.md`, `README.md`, `plugins/karvey/README.md`, descriptions in `plugin.json` / `marketplace.json` — _Depends: E1.F12.T1, E1.F6.T4, E1.F5.T6_ (P)

**Estimate:** 30 min  
**Files:** `plugins/karvey/hooks/README.md`; `README.md`; `plugins/karvey/README.md`; `plugins/karvey/.claude-plugin/plugin.json` (description only, not version); `.claude-plugin/marketplace.json` (description only, not version)  
**Requirements:** REQ-W1-049, REQ-W1-051, REQ-W1-055, REQ-W1-059, REQ-W1-060  
**Tests added:** L-11, L-16, L-22, L-30, L-31  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-11,L-16,L-22,L-30,L-31` exits 0.
- Hooks table with anchored conditions; python ≥ 3.9; tracker as the team's configured one; `/karvey:karvey-<name>`; counts match files.

### E1.F12.T12 [Backend] Move `REVISION_PR_17-19_20260923.md` into `docs/spec/changes/team-adapters/qa/` and update references (P)

**Estimate:** 10 min  
**Files:** `REVISION_PR_17-19_20260923.md → docs/spec/changes/team-adapters/qa/` (git mv); `CHANGELOG.md, docs/spec/backlog.md, docs/spec/decisions.md, docs/spec/changes/team-adapters/findings.md, docs/spec/changes/wave1-hardening/{requirements,prd,spec-delta,architecture}.md` (reference text only)  
**Requirements:** REQ-W1-075  
**Tests added:** L-25 (no `REVISION_PR_*.md` at the repo root)  
**Done when:** `ls REVISION_PR_*.md 2>/dev/null | wc -l` → 0 and `python3 plugins/karvey/scripts/lint-plugin.py --only L-25` exits 0.
- `spec.json:inputs.qa_team_adapters` keeps its `@d38abc9` pin (it names the commit where the file was).

### E1.F12.T13 [Backend] Text gate: the whole-repo lint is green — _Depends: E1.F12.T2, E1.F12.T3, E1.F12.T4, E1.F12.T5, E1.F12.T6, E1.F12.T7, E1.F12.T8, E1.F12.T9, E1.F12.T10, E1.F12.T11, E1.F12.T12, E1.F10.T6, E1.F11.T1_

**Estimate:** 30 min  
**Files:** (any file where the linter reports residue)  
**Requirements:** REQ-W1-001, REQ-W1-013, REQ-W1-053, REQ-W1-055, REQ-W1-057  
**Tests added:** the full linter  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0.
- Fix residue only; a finding that needs a design change goes to `findings.md` as a spec-gap instead of being patched here.

## Feature E1.F13: CI workflow

`.github/workflows/lint.yml` and `.gitattributes` (§1.11); CI observed on a PR.  
Requirements covered: 030, 054, 109  
Total estimated time: 40 min (2 tasks)

### E1.F13.T1 [Infra] `.github/workflows/lint.yml` (4 jobs, pinned SHAs, read-only) and `.gitattributes` — _Depends: E1.F12.T13, E1.F4.T4, E1.F6.T4, E1.F11.T2_

**Estimate:** 25 min  
**Files:** `.github/workflows/lint.yml` (NEW); `.gitattributes` (NEW: `*.sh`/`*.py` eol=lf; `docs/spec/.graph-pending merge=union`)  
**Requirements:** REQ-W1-030, REQ-W1-054, REQ-W1-109  
**Tests added:** each `run:` step executed locally; the regression step is added by F14.T3  
**Done when:** locally: `python3 plugins/karvey/scripts/lint-plugin.py --format github`, `python3 plugins/karvey/scripts/karvey-state.py validate --all --root .` (0 errors after F15 — until then only warnings plus the team-adapters prod.ref error), `python3 -m unittest discover -s plugins/karvey/tests/unit`, `python3 plugins/karvey/tests/hooks/run_tables.py`, `bash plugins/karvey/hooks/tests/test-hooks.sh`, `node --test plugins/karvey/tests/page/` each exit 0 (the validate step excepted until F15); `git check-attr eol -- plugins/karvey/hooks/karvey-hook.sh` → `eol: lf`.
- §1.11 exactly: `pull_request` + `push` on main, `permissions: contents: read`, never `pull_request_target`, `actions/*` pinned by commit SHA (look the SHAs up with `gh api repos/actions/checkout/git/ref/tags/<tag>`), matrix ubuntu/macos × 3.9/3.12, node 20 page job, Windows advisory.

### E1.F13.T2 [Infra] CI observed on a draft PR `feature/wave1-hardening → main` — _Depends: E1.F13.T1, E1.F14.T3, E1.F15.T3_

**Estimate:** 15 min  
**Files:** (no file) draft PR on GitHub  
**Requirements:** REQ-W1-030, REQ-W1-054  
**Tests added:** the CI run itself: jobs `lint`, `tests` (4 matrix legs), `page` green, `windows-advisory` reported; durations non-trivial (verification.md §5)  
**Done when:** `gh pr checks <PR>` shows `lint`, `tests (…)` × 4 and `page` as pass; `gh run view <id> --json jobs --jq '.jobs[].name'` lists them; no job under 5 s.
- Push the feature branch (allowed: feature branch, not main); open the PR as draft; read durations with `gh run view <id> --json jobs`.

## Feature E1.F14: Migration fixtures and regression suite

Anonymised legacy shapes (§6.3), BUG-05..17 regression index (§6.4), agent-behaviour manual scripts (§6.5).  
Requirements covered: 003, 009, 010, 041, 080, 081, 082, 083, 084, 085, 086, 087, 088, 089, 095, 096, 107  
Total estimated time: 115 min (4 tasks)

### E1.F14.T1 [Test] Legacy `spec.json` fixtures (anonymised) and the tests that iterate them — _Depends: E1.F3.T2_ (P)

**Estimate:** 40 min  
**Files:** `plugins/karvey/tests/fixtures/legacy/spec/*.json` (NEW: 31 phase values incl. null, 6 embedded skips, approvals-null, unknown keys, 4 management, 6 multi-type, gates-skipped, team-adapters-like, bom); `plugins/karvey/tests/unit/test_state_validate.py` (MODIFY); `plugins/karvey/tests/unit/test_state_fix.py` (MODIFY); `plugins/karvey/tests/unit/test_fixtures_anonymous.py` (NEW)  
**Requirements:** REQ-W1-003, REQ-W1-009, REQ-W1-010  
**Tests added:** every fixture: `validate` never crashes; `--fix` idempotent; no approval flipped; unmappable → exit 3; `test_fixtures_anonymous.py`: `change_id` = `fixture-NN`, free text `"…"`, no `@`, no digit run ≥ 6, no key outside the catalogue of §6.3  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_*.py' -v` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_fixtures_anonymous.py' -v` pass.
- Hand-written synthetic files per §6.3; the scan itself is never committed.

### E1.F14.T2 [Test] Legacy `project.json` fixtures and config resolution over them — _Depends: E1.F7.T2_ (P)

**Estimate:** 20 min  
**Files:** `plugins/karvey/tests/fixtures/legacy/project/*.json` (NEW: management ×4, notifications ×3, clickup-backlog-list, trunk); `plugins/karvey/tests/unit/test_config_resolve.py` (MODIFY)  
**Requirements:** REQ-W1-010, REQ-W1-086, REQ-W1-087, REQ-W1-088  
**Tests added:** `resolve management` and `propose-settings --from-legacy` over each fixture; `validate --fix` string → object  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_config_resolve.py' -v` passes.

### E1.F14.T3 [Test] Regression index BUG-05..17 (`tests/regression/test_incidents.py`) and its CI step — _Depends: E1.F10.T6, E1.F11.T1, E1.F11.T2, E1.F13.T1, E1.F6.T4_

**Estimate:** 25 min  
**Files:** `plugins/karvey/tests/regression/test_incidents.py` (NEW); `.github/workflows/lint.yml` (MODIFY: + regression step)  
**Requirements:** REQ-W1-107  
**Tests added:** `test_incidents.py`: each BUG-05..17 names its check (§6.4); the test fails if the named L-id, table id or test function disappears; cross-checked by L-32  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/regression -v` passes.
- BUG-18..21 already name their regression in test-hooks.sh (3.11.3/3.11.4): listed, not re-implemented.

### E1.F14.T4 [Test] Agent-behaviour manual scripts under `tests/manual/` — _Depends: E1.F12.T3, E1.F12.T5, E1.F12.T6, E1.F12.T10_ (P)

**Estimate:** 30 min  
**Files:** `plugins/karvey/tests/manual/{missing-status-map,no-human-no-mapping,per-level-maps,settings-docs-branch,qa-review-to-done,impl-resume,find-or-create,init-not-now,settings-merge,visible-version}.md` (NEW)  
**Requirements:** REQ-W1-041, REQ-W1-080, REQ-W1-081, REQ-W1-082, REQ-W1-083, REQ-W1-084, REQ-W1-085, REQ-W1-089, REQ-W1-095, REQ-W1-096  
**Tests added:** each script: setup, exact prompt, expected observable result, evidence to capture (AC-7)  
**Done when:** `ls plugins/karvey/tests/manual/*.md | wc -l` → 10, and `grep -L 'Expected:' plugins/karvey/tests/manual/*.md` prints nothing.
- REQ-W1-096 is a verification of 3.11.2 behaviour: its script plus the existing test-hooks.sh case.

## Feature E1.F15: Dogfood migration of this repo

§7.1: this repo's own `spec.json` files through `--fix`; team-adapters retro prod record (D-08).  
Requirements covered: 003, 009, 013, 023, 032, 108, 109  
Total estimated time: 35 min (3 tasks)

### E1.F15.T1 [Backend] This repo through `validate --fix`: dry-run diff shown, then applied to `wave1-hardening` and `team-adapters` — _Depends: E1.F3.T2, E1.F14.T1_

**Estimate:** 20 min  
**Files:** `docs/spec/changes/wave1-hardening/spec.json` (history normalised); `docs/spec/changes/team-adapters/spec.json` (`deploy` → `deploying`); (read only) docs/spec/project.json, docs/spec/changes/archive/2026-09-22-team-layer/spec.json  
**Requirements:** REQ-W1-009, REQ-W1-013, REQ-W1-109  
**Tests added:** integration row of §6.5; second `--fix` run is a no-op  
**Done when:** `python3 plugins/karvey/scripts/karvey-state.py validate --all --root . --json` reports 0 errors except `team-adapters approvals.prod.ref` (cleared in F15.T3); a second `--fix --dry-run` prints an empty diff.
- `validate --all --fix --dry-run` → the diff goes into the task's close comment for the owner; then `--fix` on the two changes. team-layer stays as recorded history (warnings; D-08, Q-A10). project.json needs no migration.
- From here on every phase write of this change goes through the tool (REQ-W1-109): `generated wave1-hardening tasks` is recorded now, the tasks approval with `approve … tasks --by … --ref D-NN`.

### E1.F15.T2 [human] Owner's prod-kind approval phrase for the retroactive team-adapters record (D-08) — _Depends: E1.F15.T1, E1.F5.T2, E1.F3.T6_

**Executor:** Mauricio Quezada Ibáñez (owner) — prod approval is never delegated  
**Command:** Start a session with the branch's plugin loaded: `cd ~/Dev/karvey && claude --plugin-dir plugins/karvey`. Type your own words with an approval **and** a production term naming the change, e.g. «ok, registra la aprobación de prod de team-adapters con D-08».  
**Verification:** The session shows `[karvey] approval recorded (prod, team-adapters, expires hh:mm)`; `python3 -c "import json,subprocess;d=subprocess.check_output(['git','rev-parse','--git-common-dir'],text=True).strip();print(json.load(open(d+'/karvey/approvals/team-adapters.json'))['kind'])"` → `prod`.  
**Rollback:** Nothing to roll back: an unused marker expires after 120 min (D-07).  
**Requirements:** REQ-W1-023, REQ-W1-108  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

### E1.F15.T3 [Backend] Record the retro prod approval (`--write-spec`, D-08); this repo validates with 0 errors — _Depends: E1.F15.T2_

**Estimate:** 15 min  
**Files:** `docs/spec/changes/team-adapters/spec.json` (approvals.prod)  
**Requirements:** REQ-W1-003, REQ-W1-032, REQ-W1-108, REQ-W1-109  
**Tests added:** integration: `validate --all` = 0 errors (AC-1)  
**Done when:** `python3 plugins/karvey/scripts/karvey-state.py validate --all --root .` exits 0 (warnings allowed, 0 errors).
- `python3 plugins/karvey/scripts/karvey-state.py approve team-adapters prod --by "Mauricio Quezada Ibáñez" --role human --ref D-08 --write-spec`. `approvals.qa` stays false until convergence (REQ-W1-108).

## Feature E1.F16: Release 3.12.0 (one versioning moment) and deploy-phase human steps

The single bump (REQ-W1-037); the owner's global-config diffs (D-01, D-11); branch protection; the prod OK (D-10). T3..T7 run inside `karvey-deploy`.  
Requirements covered: 017, 018, 023, 024, 025, 031, 034, 035, 037, 041, 054, 055, 058, 080, 099  
Total estimated time: 85 min (7 tasks)

### E1.F16.T1 [Backend] Release docs and the single version bump to 3.12.0 — _Depends: E1.F13.T2, E1.F14.T2, E1.F14.T4_

**Estimate:** 30 min  
**Files:** `CHANGELOG.md` (`[Unreleased]` → `[3.12.0] - date`: Why, Behaviour change (prod-gate on + how to switch off via a reviewed project.json), CLAUDE.md-destinations compatibility line, 3.10.0 claim toned down); `docs/karvey.html` (version history: 3.12.0 current, 5 language blocks); `plugins/karvey/.claude-plugin/plugin.json` (version); `.claude-plugin/marketplace.json` (version); `docs/spec/project.json` (karvey_version)  
**Requirements:** REQ-W1-037, REQ-W1-055, REQ-W1-058, REQ-W1-080, REQ-W1-099  
**Tests added:** L-12, L-13, L-35  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0, and `git log --oneline -G'"(version|karvey_version)": "3\.' origin/main..HEAD -- plugins/karvey/.claude-plugin/plugin.json .claude-plugin/marketplace.json docs/spec/project.json | wc -l` → 1.
- One commit changes every version field (REQ-W1-037). If `[Unreleased]` is empty, stop.

### E1.F16.T2 [Backend] Prepare, never apply, the owner's global-config diffs (D-01, D-11) — _Depends: E1.F5.T2_ (P)

**Estimate:** 15 min  
**Files:** `$SCRATCH/owner-diffs/CLAUDE.md.diff` (outside the repo); `$SCRATCH/owner-diffs/settings.json.diff` (outside the repo)  
**Requirements:** REQ-W1-017, REQ-W1-018  
**Tests added:** `patch --dry-run` of each diff against a copy of the current file succeeds  
**Done when:** `patch --dry-run -p0 < $SCRATCH/owner-diffs/CLAUDE.md.diff` on a copy exits 0; `sha256sum ~/.claude/CLAUDE.md ~/.claude/settings.json` equal before and after the task.
- CLAUDE.md: the §7.3 diff (step 3 → approval recorded by the hook; the agent never creates, touches, copies, moves or deletes a marker; prod needs a prod word). settings.json: `env.KARVEY_COMPAT_MARKER` = the path his `require-plan*.sh` read (`${TMPDIR:-/tmp}/claude-plan-approved-$(id -un)`; the session-suffixed variant noted). Read the two files; write nothing under `~/.claude/`.

### E1.F16.T3 [human] Branch protection on `main`: require the CI checks (Q-A8, D-09) — _Depends: E1.F13.T2_

**Executor:** Mauricio Quezada Ibáñez (repo admin)  
**Command:** `gh api -X PUT repos/MauricioQuezadaHaintech/karvey/branches/main/protection --input <SCR>/protection.json` with `{"required_status_checks":{"strict":true,"contexts":["lint","tests (ubuntu-latest, 3.9)","tests (ubuntu-latest, 3.12)","tests (macos-latest, 3.9)","tests (macos-latest, 3.12)","page"]},"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null}` (the agent writes the JSON with the exact check names read from F13.T2). Or GitHub → Settings → Branches → `main` → Require status checks.  
**Verification:** `gh api repos/MauricioQuezadaHaintech/karvey/branches/main/protection --jq '.required_status_checks.contexts'` → the six names.  
**Rollback:** `gh api -X DELETE repos/MauricioQuezadaHaintech/karvey/branches/main/protection/required_status_checks`.  
**Requirements:** REQ-W1-054  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

### E1.F16.T4 [Backend] Release PR ready; `advance deploying` on the feature branch; the unapproved merge is blocked (E2E evidence) — _Depends: E1.F16.T1, E1.F16.T3_

**Estimate:** 20 min  
**Files:** `docs/spec/changes/wave1-hardening/spec.json` (phase deploying, via the tool); `PR body`  
**Requirements:** REQ-W1-023, REQ-W1-024, REQ-W1-025, REQ-W1-034, REQ-W1-035  
**Tests added:** E2E row of §6.5: first blocked without approval  
**Done when:** the PR has all required checks green; the captured BLOCK line and `grep -c 'prod-gate' <git-common-dir>/karvey/audit.log` ≥ 1 are pasted in the PR body; `git branch --show-current` never showed `main` during the task.
- Run inside `karvey-deploy`: the 6-step checklist before the push; `karvey-state.py advance wave1-hardening deploying`; PR title `[Deploy] wave1-hardening`, out of draft.
- In a session started with `claude --plugin-dir plugins/karvey`, attempt `gh pr merge <N> --merge` **before** any prod approval: capture the `[karvey] prod-gate BLOCK change=wave1-hardening missing=…` line and the audit.log entry as evidence in the PR.

### E1.F16.T5 [human] The prod OK for 3.12.0 (D-10) and the D-NN answer — _Depends: E1.F16.T4_

**Executor:** Mauricio Quezada Ibáñez (owner) — never delegated  
**Command:** In the session started with `claude --plugin-dir plugins/karvey`, after reading the PR and its evidence, type your own words with an approval **and** a production term, e.g. «ok, merge a prod wave1-hardening 3.12.0». Answer the structured question that records the D-NN.  
**Verification:** The session shows `[karvey] approval recorded (prod, wave1-hardening, expires hh:mm)`; the D-NN in `docs/spec/decisions.md` quotes your words verbatim.  
**Rollback:** Before the merge: do nothing; the marker expires after 120 min. After the merge: revert PR on GitHub (a new change, through the method).  
**Requirements:** REQ-W1-023, REQ-W1-031  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

### E1.F16.T6 [Backend] `approve prod` (ledger), merge through the prod-gate, release facts in the ledger — _Depends: E1.F16.T5_

**Estimate:** 20 min  
**Files:** `<git-common-dir>/karvey/ledger/wave1-hardening.json`; `PR` (merged)  
**Requirements:** REQ-W1-023, REQ-W1-025, REQ-W1-031, REQ-W1-037, REQ-W1-041  
**Tests added:** E2E row of §6.5: allowed after the human's prod phrase + `approve prod`  
**Done when:** `python3 plugins/karvey/scripts/karvey-state.py check-prod wave1-hardening --json` → `ok: true, source: ledger`; `gh pr view <N> --json state --jq .state` → `MERGED`; the ALLOW line is in audit.log.
- `python3 plugins/karvey/scripts/karvey-state.py approve wave1-hardening prod --by "Mauricio Quezada Ibáñez" --role human --ref D-NN`; `gh pr merge <N> --merge` → `[karvey] prod-gate ALLOW change=wave1-hardening by=… ref=D-NN`.
- Post-merge check: CI on `main` green; `git show origin/main:plugins/karvey/.claude-plugin/plugin.json` → 3.12.0; record pipeline run URL and `post_deploy_check: pass` in the ledger (read by `advance deployed` at archive). No commit on `main` (D-03): `approvals.prod` reaches spec.json only in `karvey-archive`.

### E1.F16.T7 [human] Apply the diffs to `~/.claude/CLAUDE.md` and `~/.claude/settings.json` after seeing them (D-01, D-11) — _Depends: E1.F16.T6, E1.F16.T2_

**Executor:** Mauricio Quezada Ibáñez (owner) — the agent never edits these files  
**Command:** First update the installed plugin to 3.12.0 (`/plugin` → update karvey), so the approval hook exists before the old `touch` rule disappears. Then `cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak-3.12 && cp ~/.claude/settings.json ~/.claude/settings.json.bak-3.12`, read `<SCR>/owner-diffs/*.diff`, and apply them yourself (`patch -p0 < …` or by hand).  
**Verification:** `grep -c 'touch /tmp/claude-plan-approved' ~/.claude/CLAUDE.md` → 0; `python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.claude/settings.json')))['env']['KARVEY_COMPAT_MARKER'])"` → the marker path; in a new session «ok» prints `[karvey] approval recorded` and the file at that path appears.  
**Rollback:** `cp ~/.claude/CLAUDE.md.bak-3.12 ~/.claude/CLAUDE.md && cp ~/.claude/settings.json.bak-3.12 ~/.claude/settings.json`.  
**Requirements:** REQ-W1-017, REQ-W1-018  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

## Traceability matrix (REQ-W1 → tasks)

| REQ-W1 | Tasks |
|---|---|
| 001 | E1.F2.T5, E1.F2.T6, E1.F3.T1, E1.F10.T2, E1.F12.T2, E1.F12.T13 |
| 002 | E1.F2.T3, E1.F2.T5, E1.F10.T3, E1.F12.T10 |
| 003 | E1.F2.T5, E1.F3.T1, E1.F14.T1, E1.F15.T3 |
| 004 | E1.F2.T6, E1.F3.T4, E1.F12.T2, E1.F12.T4 |
| 005 | E1.F2.T6, E1.F3.T3, E1.F10.T2, E1.F12.T2, E1.F12.T3 |
| 006 | E1.F2.T5, E1.F3.T6, E1.F12.T3 |
| 007 | E1.F2.T5, E1.F2.T6, E1.F3.T4, E1.F12.T4 |
| 008 | E1.F2.T2, E1.F3.T4 |
| 009 | E1.F2.T6, E1.F3.T2, E1.F14.T1, E1.F15.T1 |
| 010 | E1.F3.T2, E1.F7.T2, E1.F14.T1, E1.F14.T2 |
| 011 | E1.F3.T4, E1.F12.T5, E1.F12.T6 |
| 012 | E1.F10.T2, E1.F12.T3, E1.F12.T4 |
| 013 | E1.F2.T2, E1.F10.T2, E1.F12.T3, E1.F12.T4, E1.F12.T7, E1.F12.T13, E1.F15.T1 |
| 014 | E1.F4.T2, E1.F5.T3 |
| 015 | E1.F5.T3 |
| 016 | E1.F3.T5, E1.F3.T6, E1.F5.T2, E1.F5.T3, E1.F5.T8, E1.F12.T9 |
| 017 | E1.F1.T1, E1.F1.T2, E1.F4.T1, E1.F5.T2, E1.F12.T7, E1.F16.T2, E1.F16.T7 |
| 018 | E1.F3.T5, E1.F5.T1, E1.F12.T7, E1.F12.T9, E1.F16.T2, E1.F16.T7 |
| 019 | E1.F5.T2 |
| 020 | E1.F4.T2, E1.F5.T4, E1.F5.T8 |
| 021 | E1.F5.T4 |
| 022 | E1.F5.T4, E1.F10.T4, E1.F12.T9 |
| 023 | E1.F3.T5, E1.F3.T6, E1.F5.T5, E1.F15.T2, E1.F16.T4, E1.F16.T5, E1.F16.T6 |
| 024 | E1.F1.T1, E1.F4.T3, E1.F5.T5, E1.F5.T6, E1.F16.T4 |
| 025 | E1.F2.T4, E1.F5.T6, E1.F16.T4, E1.F16.T6 |
| 026 | E1.F2.T5, E1.F4.T3, E1.F5.T6, E1.F8.T1, E1.F12.T9 |
| 027 | E1.F2.T4, E1.F2.T5, E1.F5.T6, E1.F12.T9 |
| 028 | E1.F1.T1, E1.F1.T2, E1.F4.T1, E1.F5.T7 |
| 029 | E1.F4.T3, E1.F5.T8, E1.F10.T4, E1.F12.T9, E1.F12.T10 |
| 030 | E1.F4.T4, E1.F13.T1, E1.F13.T2 |
| 031 | E1.F3.T6, E1.F10.T5, E1.F12.T6, E1.F12.T9, E1.F16.T5, E1.F16.T6 |
| 032 | E1.F3.T6, E1.F12.T6, E1.F15.T3 |
| 033 | E1.F10.T5, E1.F12.T6 |
| 034 | E1.F10.T5, E1.F12.T6, E1.F12.T9, E1.F16.T4 |
| 035 | E1.F5.T4, E1.F5.T5, E1.F12.T6, E1.F12.T9, E1.F16.T4 |
| 036 | E1.F10.T4, E1.F12.T5, E1.F12.T9 |
| 037 | E1.F12.T6, E1.F16.T1, E1.F16.T6 |
| 038 | E1.F10.T4, E1.F12.T5 |
| 039 | E1.F10.T4, E1.F12.T3, E1.F12.T9 |
| 040 | E1.F10.T4, E1.F12.T5, E1.F12.T9 |
| 041 | E1.F12.T6, E1.F14.T4, E1.F16.T6 |
| 042 | E1.F10.T4, E1.F12.T5, E1.F12.T10 |
| 043 | E1.F8.T2, E1.F12.T4, E1.F12.T5 |
| 044 | E1.F8.T2, E1.F12.T6 |
| 045 | E1.F2.T4, E1.F3.T3, E1.F6.T1, E1.F6.T4 |
| 046 | E1.F6.T1, E1.F6.T4, E1.F12.T7 |
| 047 | E1.F1.T1, E1.F1.T2, E1.F6.T1, E1.F6.T4 |
| 048 | E1.F6.T3, E1.F12.T7 |
| 049 | E1.F2.T1, E1.F10.T4, E1.F11.T1, E1.F12.T7, E1.F12.T10, E1.F12.T11 |
| 050 | E1.F1.T1, E1.F1.T2, E1.F2.T4, E1.F4.T1, E1.F6.T2, E1.F6.T4 |
| 051 | E1.F6.T4, E1.F10.T4, E1.F12.T9, E1.F12.T11 |
| 052 | E1.F10.T2, E1.F12.T1 |
| 053 | E1.F10.T2, E1.F12.T1, E1.F12.T13 |
| 054 | E1.F13.T1, E1.F13.T2, E1.F16.T3 |
| 055 | E1.F10.T1, E1.F10.T3, E1.F12.T11, E1.F12.T13, E1.F16.T1 |
| 056 | E1.F10.T2, E1.F12.T3, E1.F12.T7 |
| 057 | E1.F2.T6, E1.F10.T2, E1.F12.T13 |
| 058 | E1.F10.T3, E1.F16.T1 |
| 059 | E1.F10.T5, E1.F12.T3, E1.F12.T5, E1.F12.T7, E1.F12.T11 |
| 060 | E1.F10.T6, E1.F12.T11 |
| 061 | E1.F2.T5, E1.F12.T3, E1.F12.T9 |
| 062 | E1.F10.T4, E1.F12.T3, E1.F12.T4, E1.F12.T9 |
| 063 | E1.F5.T7, E1.F12.T6, E1.F12.T9 |
| 064 | E1.F10.T4, E1.F12.T10 |
| 065 | E1.F9.T1, E1.F12.T6 |
| 066 | E1.F9.T1, E1.F12.T6 |
| 067 | E1.F12.T6 |
| 068 | E1.F8.T1, E1.F12.T7 |
| 069 | E1.F8.T1, E1.F12.T7 |
| 070 | E1.F8.T1, E1.F12.T7 |
| 071 | E1.F2.T5, E1.F8.T1, E1.F12.T7 |
| 072 | E1.F8.T1, E1.F12.T7 |
| 073 | E1.F10.T5, E1.F12.T5 |
| 074 | E1.F10.T5, E1.F12.T5, E1.F12.T6 |
| 075 | E1.F10.T5, E1.F12.T12 |
| 076 | E1.F10.T5, E1.F12.T5 |
| 077 | E1.F10.T1, E1.F12.T3, E1.F12.T4, E1.F12.T5, E1.F12.T6, E1.F12.T7, E1.F12.T8 |
| 078 | E1.F10.T1, E1.F12.T3, E1.F12.T4, E1.F12.T5, E1.F12.T6, E1.F12.T7, E1.F12.T8 |
| 079 | E1.F10.T1, E1.F12.T7 |
| 080 | E1.F7.T2, E1.F12.T4, E1.F12.T10, E1.F14.T4, E1.F16.T1 |
| 081 | E1.F10.T6, E1.F12.T4, E1.F12.T10, E1.F14.T4 |
| 082 | E1.F7.T2, E1.F12.T10, E1.F14.T4 |
| 083 | E1.F6.T2, E1.F6.T4, E1.F12.T3, E1.F12.T10, E1.F14.T4 |
| 084 | E1.F10.T5, E1.F12.T5, E1.F12.T6, E1.F12.T10, E1.F14.T4 |
| 085 | E1.F10.T5, E1.F12.T5, E1.F14.T4 |
| 086 | E1.F7.T2, E1.F10.T5, E1.F12.T10, E1.F14.T2 |
| 087 | E1.F7.T2, E1.F10.T5, E1.F12.T6, E1.F12.T10, E1.F14.T2 |
| 088 | E1.F2.T5, E1.F7.T2, E1.F12.T10, E1.F14.T2 |
| 089 | E1.F12.T4, E1.F12.T10, E1.F14.T4 |
| 090 | E1.F7.T3, E1.F8.T1, E1.F12.T10 |
| 091 | E1.F10.T5, E1.F12.T5, E1.F12.T10 |
| 092 | E1.F10.T5, E1.F12.T10 |
| 093 | E1.F2.T5, E1.F7.T1, E1.F10.T5, E1.F12.T10 |
| 094 | E1.F10.T5, E1.F12.T10 |
| 095 | E1.F10.T5, E1.F12.T3, E1.F14.T4 |
| 096 | E1.F14.T4 |
| 097 | E1.F7.T1, E1.F7.T3, E1.F12.T5, E1.F12.T10 |
| 098 | E1.F2.T5, E1.F7.T3, E1.F12.T5, E1.F12.T10 |
| 099 | E1.F7.T2, E1.F10.T6, E1.F12.T10, E1.F16.T1 |
| 100 | E1.F11.T1 |
| 101 | E1.F11.T1 |
| 102 | E1.F11.T2 |
| 103 | E1.F11.T2 |
| 104 | E1.F11.T2 |
| 105 | E1.F11.T2 |
| 106 | E1.F11.T2 |
| 107 | E1.F8.T2, E1.F10.T6, E1.F12.T10, E1.F14.T3 |
| 108 | E1.F8.T2, E1.F15.T2, E1.F15.T3 |
| 109 | E1.F3.T1, E1.F10.T3, E1.F13.T1, E1.F15.T1, E1.F15.T3 |

**Coverage:** 109/109. No REQ-W1 is left without a task.
Covered only by manual/E2E evidence (AC-7), each with its named script or task: 041 (manual `visible-version.md` + E1.F16.T6), 089 and 096 (manual scripts), the E2E halves of 023/025/031/034/035 (E1.F16.T4..T6).

## Totals and critical path

- **Tasks:** 73, of which 5 `[human]` (one conditional) and 68 agent tasks.
- **Total estimate:** 2150 min ≈ 35.8 h of AI + review. The agent-task minutes per feature are listed in the feature headers.
- **Critical path:** 550 min ≈ 9.2 h:
  E1.F2.T1 → E1.F4.T2 → E1.F4.T3 → E1.F4.T4 → E1.F5.T2 → E1.F5.T3 → E1.F5.T4 → E1.F5.T5 → E1.F5.T6 → E1.F12.T9 → E1.F12.T13 → E1.F13.T1 → E1.F14.T3 → E1.F13.T2 → E1.F16.T1 → E1.F16.T4 → E1.F16.T5 → E1.F16.T6.
  This does not count the `[human]` waits (E1.F15.T2, E1.F16.T3, E1.F16.T5) or CI queue time.
- **Parallel potential:** total ÷ critical path ≈ 3.9×. The serial spine is `karvey-state.py` → `guards.py` → `lint-plugin.py` → text gate.

## What proved impractical when breaking the architecture into tasks

1. **`hooks.json` in §1.3 repeats BUG-18.** Every command there is written `bash '${CLAUDE_PLUGIN_ROOT}/…'`, with single quotes. That is the exact defect fixed in 3.11.3: bash does not expand the placeholder and the hook never runs. E1.F4.T3 and E1.F6.T2 use double quotes, and the BUG-18 regression is generalised to run **every** declared command. The architecture text should be corrected (spec-gap, low).
2. **§1.4's worktree fix is already shipped.** F-01 → BUG-21 was fixed in 3.11.4, together with BUG-20 (a repo-name path resolves to the root) and BUG-19 (in-repo team layout). E1.F6.T1 ports that code into `karvey_hooks.py session` instead of rewriting it, and E1.F6.T3 writes `state.json` paths in the shape that resolver reads. The 32 existing `test-hooks.sh` cases are the guard.
3. **Single-file tools serialise the plan.** `karvey-state.py` (6 tasks), `guards.py` (6), `lint-plugin.py` (6) and `karvey_hooks.py` (5) cannot be split into parallel tasks without file conflicts. That is most of the critical path. Splitting command logic into `karvey_lib` modules (e.g. `migrate.py`, per-guard modules, per-check-family lint modules) would allow (P). It is left as in the approved file plan; `karvey-impl` may propose it as an implementation detail.
4. **REQ-W1-036 conflicts with parallel tasks.** It requires one `[Unreleased]` line per task commit, so every (P) task touches `CHANGELOG.md`, and parallel branches conflict in the same section. Practical rule for impl: merge (P) branches one at a time, and resolve an `[Unreleased]` conflict by keeping both lines. `merge=union` on CHANGELOG.md is not recommended (it can interleave outside the section).
5. **The prod path needs the branch plugin loaded.** The E2E release proof and the team-adapters retro record (D-08) need the *new* approval hook and prod-gate active in the owner's session. The installed plugin is 3.11.4, so the session must be started with `claude --plugin-dir plugins/karvey` (E1.F15.T2, E1.F16.T4..T5). The owner's `~/.claude/CLAUDE.md` / `settings.json` diffs must be applied only **after** 3.12.0 is installed (E1.F16.T7). Before that, nothing would create his legacy marker, and his `require-plan*.sh` would block every edit.
6. **Retroactive prod approval needs a fresh human phrase.** Under Q-A1/D-10, `approve prod` refuses without a prod-kind marker. So D-08 alone cannot clear the `team-adapters approvals.prod.ref` error; the owner must type a prod phrase once (E1.F15.T2).
7. **The CI regression step moves.** §1.11 lists `unittest discover -s tests/regression`. The requested order puts CI (F13) before the regression suite (F14), and `unittest` exits non-zero when it finds no tests (Python ≥ 3.12). So E1.F14.T3 adds that step. Likewise the CI `validate --all` step can only be green after E1.F15.T3, which is why the CI observation (E1.F13.T2) waits for F14/F15.
8. **The linter needs a scope flag.** The text tasks need a per-file done-criterion while the rest of the repo is still red, so E1.F10.T1 adds `--paths GLOB`. It is a CLI convenience, not a new check.
9. **Linter vs text ordering (risk in §12).** The linter checks land in F10 and are expected to report findings on the real repo until F12 is done. Their done-criteria use pass/fail mini-plugin fixtures; the whole-repo `lint-plugin.py` exit 0 is asserted once, at E1.F12.T13.

---
*Generated by `karvey-tasks` (PHASE 7) on 2026-09-23 for `wave1-hardening`. Knowledge sync (Step 4B) deliberately not run: this change moves the sync to archive only (REQ-W1-062), as recorded in `PLAN.md`.*
