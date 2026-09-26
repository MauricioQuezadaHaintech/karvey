# Tasks: wave3-optimization

> PHASE 7 (`karvey-tasks`, skill text read from `plugins/karvey/skills/karvey-tasks/SKILL.md` in this worktree) · Security Tier 2 · Lane `feature-ui` · Tracker: Markdown (`project.json:management.tool = markdown`): this file + `PLAN.md`, no external tracker.
> Inputs: `architecture.md` (generated, merged *how* gate pending; revised after its judges), `requirements.md` (REQ-W3-001..080, approved under D-21), `design-spec.md` and `mockup/` (approved), `prd.md`, `spec.json`, `risks.md`, the house style of `wave2-structural/tasks.md`, and the code on `feature/wave3-optimization`.
>
> **Estimates are calibrated.** In this repo the skill's 10–30 min band ran about 10× high. The minutes below are realistic **AI execution + human review** for one task (typically 3–8 min AI + 2–7 min review), as in Wave 2 (706 min estimated for 71 tasks). `karvey-impl` records the actuals next to them in `PLAN.md` and never edits an estimate.

## Summary

| Item | Value |
|---|---|
| Features | 12 (the PLAN.md features F1..F12, same numbering) + `E1.DEPLOY` |
| Tasks | 101 (75 Backend, 16 Frontend, 1 Infra, 8 Test, 1 human) |
| Agent tasks / `[human]` tasks | 100 / 1 |
| Total estimate (agent tasks, AI + review, calibrated) | **1,059 min** (≈ 17.7 h) |
| Critical path by dependencies (agent minutes; the `[human]` wait not counted) | **242 min** (≈ 4.0 h), 21 tasks |
| REQ-W3 coverage | 80/80 |
| Largest task | 15 min (cap 60) |

## Conventions

- **IDs** `E1.F{n}.T{n}`; E1 = this change, F{n} = the PLAN.md feature of the same number (the architecture's components C-01..C-26 map to them in `architecture.md` §7.1). The production OK is `E1.DEPLOY.T1`: deploy work belongs to the Epic, not to a Feature (REQ-W3-041, applied to this plan).
- **Layers:** `[Backend]` = plugin scripts, library, schemas, hooks and skill/rule text; `[Frontend]` = the two self-contained HTML pages (sponsor template, method page); `[Infra]` = the existing CI workflow; `[Test]` = test-only work (integration, manual scripts, the whole-repo gates); `[human]` = a step only a person may run (`rules/multi-agent.md` §5). No DB task. No cloud (infra skipped, architecture A-16).
- **Estimate** = AI execution + review, minutes, calibrated (header). The `[human]` task carries no estimate; it declares the executor.
- **(P)** = can run in parallel with other (P) tasks whose dependencies are met, because the files differ. Tasks that share `karvey-state.py`, `karvey-context.py`, `lint-plugin.py`, `rules/gates.md` or `docs/karvey.html` run in sequence even when marked (P); `karvey-impl` picks the order.
- **Test first** (REQ-W2-057): each task's **Tests added** are written before its code and fail until the code lands; tests are tagged `@req REQ-W3-NNN` in their docstring or named `test_REQ_W3_NNN_*`. Manual scripts are named in `[Test]` tasks with `manual:` reasons in their files.
- **Every impl commit** carries `Karvey-Change: wave3-optimization` (REQ-W3-065), adds one line under `## [Unreleased]` in `CHANGELOG.md`, and changes no version. The version number is fixed at release by `karvey-deploy`.
- **Done criterion** is a command, run from the repo root. Unit tests: `python3 -m unittest discover -s plugins/karvey/tests/unit -p '<file>' -v`. Tables: `python3 plugins/karvey/tests/hooks/run_tables.py --only <table>`. Page: `node --test plugins/karvey/tests/page/`. Lint: `python3 plugins/karvey/scripts/lint-plugin.py [--only L-NN]` — 0 errors after every task.
- **Neutral text:** no organisation, product, client or person names, no ids, no home paths, no secrets in any new file (PRD §9). Fixtures are anonymised (`test_fixtures_anonymous.py`).
- **Nothing outside the repository is written** by an agent task. The runtime's files are only read (C-22, REQ-W3-058).
- **One requirement, one Feature** (REQ-W3-043, applied to this plan): every requirement's tasks sit in its PLAN.md Feature; the one exception carries a `Split:` line.

## Execution order

1. **F1 first**: the size tool and the **baseline of the 4.0.0 content** (E1.F1.T4) in a commit of its own, before any commit that moves a skill or rule (REQ-W3-002). **E1.F11.T1** (the check-mode rows) runs early too: every later check reads its mode from it (L-73).
2. **F3..F10** add data, scripts and text **in place** (no move). F3 comes first so that effort is recorded from the earliest possible gate of this change (REQ-W3-074). F4..F10 run as their dependencies land.
3. **F2 last among the functional features**: the reorganisation runs on the final Wave 3 text (E1.F2.T2 depends on the last task of F3..F10), so no skill is restructured twice.
4. **F11**: fix, compatibility, dogfooding, hand-off, the whole-repo gate, release docs.
5. **F12 last** (REQ-W3-070, B-06): its first task depends on the last task of F11, which depends on every other feature.
6. `E1.DEPLOY.T1` (`[human]`) is the production OK at release; QA and archive are phases, not tasks here.

## Feature E1.F1: Context measurement (first: the baseline precedes every move)

Architecture §1.3, §1.23 (CI), §1.25 (L-62).  
Requirements covered: 001, 002, 010, 011, 071, 072  
Total estimated time: 52 min (6 tasks)

### E1.F1.T1 [Backend] `karvey_lib/loadlist.py`: `declared`, `cited` (fences and footnote definitions excluded), `graph`, `closure`, `size`; `adapters/{tool}` and `?` references → `closure_min` / `closure_max`

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/loadlist.py` (NEW); `plugins/karvey/tests/unit/test_context_budget.py` (NEW, library section); `plugins/karvey/tests/unit/fixtures/budget/` (NEW: a skill tree with a footnote, a fenced path, a cycle, two adapters)  
**Requirements:** REQ-W3-001  
**Tests added:** closure of the fixture = expected sorted list; a footnote citation and a fenced path are not counted; a rule cycle terminates; `{tool}` gives min = smallest adapter and max = largest; `words` excludes frontmatter; `tokens_est = ceil(bytes/4)` marked estimated  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_budget.py' -v` passes

### E1.F1.T2 [Backend] `karvey-context-budget.py measure [--label --json]`: rows per phase skill + orchestrator + `session_hook` row, sorted, no clock, missing `Load:` file → exit 1 with skill, line, file — _Depends: E1.F1.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-context-budget.py` (NEW); `plugins/karvey/tests/fixtures/budget-project/` (NEW: a small Karvey project for the session-hook row); `plugins/karvey/tests/unit/test_context_budget.py` (CLI section)  
**Requirements:** REQ-W3-001, REQ-W3-071, REQ-W3-072  
**Tests added:** two runs on the same tree → identical bytes (`test_REQ_W3_071_*`), and the first differing line is named when a fixture injects a timestamp; `git status --porcelain` empty after the run; a `Load:` entry naming a deleted reference → exit 1, the message has skill, line and file; JSON has sorted keys and no absolute path  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_budget.py' -v` passes and `python3 plugins/karvey/scripts/karvey-context-budget.py measure --label check --json | python3 -m json.tool > /dev/null` exits 0

### E1.F1.T3 [Backend] `compare BASE [AFTER|--live] [--target-median 40] [--warn-growth 10]`: median `closure_max` reduction, per-phase reason or `unexplained`, exit 1 below target; `::warning::` on growth, exit 0 — _Depends: E1.F1.T2_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-context-budget.py`; `plugins/karvey/tests/unit/test_context_budget.py` (compare section)  
**Requirements:** REQ-W3-010, REQ-W3-011  
**Tests added:** fixture pair with median −35% → exit 1 naming the median; median −45% with one phase at −20% → exit 0, that phase listed with its reason, or `unexplained` without one; a phase +15% under `--warn-growth 10` → one warning line with the phase and `15%`, exit 0  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_budget.py' -v` passes

### E1.F1.T4 [Backend] Baseline `docs/spec/retros/context-size-4.0.0.json` in a commit of its own + the order test — _Depends: E1.F1.T2_

**Estimate:** 6 min  
**Files:** `docs/spec/retros/context-size-4.0.0.json` (NEW, from `karvey-context-budget.py measure --label 4.0.0 --json` on the fork point content, architecture A-01); `plugins/karvey/tests/unit/test_context_budget.py` (`test_REQ_W3_002_baseline_precedes_moves`)  
**Requirements:** REQ-W3-002, REQ-W3-071  
**Tests added:** the commit that adds the baseline precedes, in `git log`, every commit of this change touching `plugins/karvey/skills/**/SKILL.md` moves, `skills/karvey/rules/**` moves or `skills/*/references/**`; else `baseline missing or taken after the reorganisation`  
**Done when:** `ls docs/spec/retros/context-size-4.0.0.json` succeeds, re-running the command gives the same bytes (`cmp`), and the order test passes

- The commit holds only the snapshot (and the test). If `wave2-structural` changes skill or rule text before it merges, the baseline is re-taken in a new commit of its own, still before the first move (risk R-6).

### E1.F1.T5 [Backend] L-62: a `Load:` entry names an existing file (blocking) — _Depends: E1.F1.T1_ (P)

**Estimate:** 6 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-62); `plugins/karvey/tests/unit/test_lint_w3.py` (NEW)  
**Requirements:** REQ-W3-072  
**Tests added:** mutation: a skill with `Load: references/gone.md` → error naming skill, line and file  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-62` exits 0 and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_w3.py' -v` passes

### E1.F1.T6 [Infra] CI: `compare … --live --warn-growth 10` step in the `lint` job — _Depends: E1.F1.T3, E1.F1.T4_

**Estimate:** 6 min  
**Files:** `.github/workflows/lint.yml`; `plugins/karvey/tests/unit/test_ci_workflow.py` (a case)  
**Requirements:** REQ-W3-011  
**Tests added:** the `lint` job has the size step after the linter; no secret, no write permission, actions still pinned by SHA  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_ci_workflow.py' -v` passes


## Feature E1.F3: Cost per change with a single agent

Architecture §1.9, §1.10, §1.11, §2.1.  
Requirements covered: 014, 015, 016, 017, 018, 019, 077  
Total estimated time: 85 min (8 tasks)

### E1.F3.T1 [Backend] Schema: `effort[]`, `judge_runs[].tokens_total / usd_estimated / source`

**Estimate:** 8 min  
**Files:** `plugins/karvey/schemas/spec.schema.json`; `plugins/karvey/tests/unit/test_schema_w3.py` (NEW)  
**Requirements:** REQ-W3-014, REQ-W3-016  
**Tests added:** a valid `effort` entry passes; a quality outside `exact|estimated|n/a` fails; a 4.0 `spec.json` without the fields still passes `--strict`; every keyword in the `schema_lite` subset  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_schema_w3.py' -v` and `-p 'test_schemas.py'` pass

### E1.F3.T2 [Backend] Statusline cost capture: `{root_key, usd, transcript, context_pct, context_tokens, at}` in `{state_dir}/cost/{session-hash}.json`, no model turn, no repo write

**Estimate:** 10 min  
**Files:** `plugins/karvey/hooks/karvey-statusline.sh`; `plugins/karvey/tests/hooks/tables/statusline.json` (cases); `plugins/karvey/hooks/README.md` (the capture, one paragraph)  
**Requirements:** REQ-W3-015  
**Tests added:** table cases: input with `cost.total_cost_usd` → capture file written with the fields, repository tree unchanged; input without `cost` → no capture, statusline output unchanged; the session id never appears in clear  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only statusline` passes

### E1.F3.T3 [Backend] `karvey_lib/effort.py`: capture pick (latest, two within 120 s → `estimated`), transcript cumulative usage, separate charged file, first close, several changes, gap, new transcript — _Depends: E1.F3.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/effort.py` (NEW); `plugins/karvey/tests/unit/test_effort.py` (NEW, library section); `plugins/karvey/tests/unit/fixtures/effort/` (NEW: captures and two transcripts)  
**Requirements:** REQ-W3-015  
**Tests added:** first close counts from session start; a statusline rewrite does not reset the charged file (F-42); two changes in one session each get their own interval; unreadable capture → `n/a` + reason and the next readable close charges the gap once; a new, shorter transcript starts a new interval; context-window figures are never used for tokens (F-43)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_effort.py' -v` passes

### E1.F3.T4 [Backend] `karvey-state.py effort {change} {phase} [--review-min N]` + `validate` reports a non-`phase` kind or a judge figure inside effort — _Depends: E1.F3.T1, E1.F3.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (new `cmd_effort`, `cmd_validate`); `plugins/karvey/tests/unit/test_effort.py` (CLI section)  
**Requirements:** REQ-W3-014, REQ-W3-016  
**Tests added:** runtime with cost → entry with US$ and tokens `exact` and `review_min` `exact` from the flag; without the flag → `review_min` `n/a`; no capture → `n/a — statusline not installed`, never 0; an entry equal to a `judge_runs` record → `mixed entry`; `spec.json` written under the lock (CAS)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_effort.py' -v` and `-p 'test_state_approve.py'` pass

### E1.F3.T5 [Backend] `validate`: cost-limit keys reported `unsupported (D-30)` as a warning that never changes the exit code (`--strict` too) + L-63 — _Depends: E1.F3.T1_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`cmd_validate`); `plugins/karvey/scripts/lint-plugin.py` (L-63); `plugins/karvey/tests/unit/test_effort.py` (cap section); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-017  
**Tests added:** `project.json` with `judges.budget` or `cost_limit` → warning line citing D-30, exit 0 under `--strict` (F-62); L-63 mutation: a skill line "stop when the cost exceeds" → error  
**Done when:** the two suites pass and `python3 plugins/karvey/scripts/lint-plugin.py --only L-63` exits 0

### E1.F3.T6 [Backend] Judge cost: `usage.total_tokens` → `exact`; estimate over prompt + every closed input; `collect --transcript auto` (runtime source), agent-reported value kept `estimated`; judges SKILL step 2 text — _Depends: E1.F3.T3_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/judges.py` (`cost`, `collect`); `plugins/karvey/scripts/karvey-judges.py` (`--transcript`); `plugins/karvey/skills/karvey-judges/SKILL.md`; `plugins/karvey/tests/unit/test_judges.py` (cases)  
**Requirements:** REQ-W3-077 (MODIFIES REQ-W2-030)  
**Tests added:** transcript with a subagent result usage → `source: runtime`, `exact`; only a model-written `usage` → `agent-reported`, `estimated`; neither → estimate whose `chars_in` includes every file of the input list (larger than the prompt-only figure of the Wave 2 fixture)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_judges.py' -v` passes

### E1.F3.T7 [Backend] Metrics: `cost_per_change`, aggregates per lane, client and period with the estimated share, `phases_per_session`; `--metrics` table and JSON — _Depends: E1.F3.T4_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/metrics.py`; `plugins/karvey/scripts/karvey-context.py` (`metrics_view`, `render_metrics`); `plugins/karvey/tests/unit/test_metrics.py` (cost section); `plugins/karvey/tests/unit/fixtures/metrics/` (two clients, three changes with effort)  
**Requirements:** REQ-W3-018 (MODIFIES REQ-W2-003)  
**Tests added:** three archived changes of two clients → each client's total and estimated share; a change without effort → `n/a (no effort)` and excluded from cost only; output byte-identical across two runs  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_metrics.py' -v` passes

### E1.F3.T8 [Backend] `cost_outliers` (3× the lane median, ≥ 3 measured) + retro skill text (input, not verdict) — _Depends: E1.F3.T7_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/metrics.py`; `plugins/karvey/skills/karvey-retro/SKILL.md`; `plugins/karvey/tests/unit/test_metrics.py` (outliers)  
**Requirements:** REQ-W3-019 (MODIFIES REQ-W2-008)  
**Tests added:** one change at 4× → listed with the phase that cost most; a lane with two measured changes → `too few changes in lane`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_metrics.py' -v` passes and `grep -c 'cost_outliers\|outlier' plugins/karvey/skills/karvey-retro/SKILL.md` ≥ 1


## Feature E1.F4: Sponsor page, report, "your turn" events, deduplication

Architecture §1.12..§1.15, §1.22-bis (C-26), §3.  
Requirements covered: 020, 021, 022, 023, 024, 025, 026, 027, 080  
Total estimated time: 131 min (11 tasks)

### E1.F4.T1 [Backend] `stakeholders` in project and spec schemas (+ `leak.deny_terms`), `validate` through `check_target`, init pre-fills the PRD Stakeholders section

**Estimate:** 10 min  
**Files:** `plugins/karvey/schemas/project.schema.json`, `spec.schema.json`; `plugins/karvey/scripts/karvey-state.py` (`cmd_validate`); `plugins/karvey/skills/karvey-init/SKILL.md`; `plugins/karvey/tests/unit/test_stakeholders.py` (NEW)  
**Requirements:** REQ-W3-020  
**Tests added:** sponsor with a webhook secret name passes; `https://…` refused asking for the secret's name; `hooks.example.org/x/y` on `webhook` refused by the pattern (F-71); change override wins per role  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_stakeholders.py' -v` passes

### E1.F4.T2 [Backend] `schemas/wording.json` (en, es: phases, lanes, risk states, labels) + L-65 (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/schemas/wording.json` (NEW); `plugins/karvey/scripts/lint-plugin.py` (L-65); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-080  
**Tests added:** English risk wording equals REQ-W3-080's five strings; L-65 mutation: a state removed from `es` → error naming state and language  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-65` exits 0 and `test_lint_w3.py` passes

### E1.F4.T3 [Backend] `karvey_lib/leakcheck.py` + `leak_patterns.json`: `secret`, `path`, `host`, `email`, `pii`, `client` (+ `deny_terms`); exception = refusal; report without the value (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/leakcheck.py` (NEW); `plugins/karvey/scripts/karvey_lib/leak_patterns.json` (NEW, public formats only); `plugins/karvey/tests/unit/test_leakcheck.py` (NEW, synthetic values)  
**Requirements:** REQ-W3-023  
**Tests added:** one case per rule family (connection string, an absolute home-directory path, `db.internal`, `10.0.0.5`, a non-declared address, a phone shape, another client's name, a deny term); the refusal report never contains the matched value; an e-mail target of a declared stakeholder passes (F-81); no portfolio and no deny terms → `other-client names not checked` and the other rules still run; an exception inside a rule → `check-error` refusal  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_leakcheck.py' -v` passes

### E1.F4.T4 [Backend] `karvey_lib/sponsor.py`: allow-listed model (scope, state, cost, risks, questions for the sponsor, gates awaiting the sponsor as approver, released), id/path/command normaliser, `as_of` per figure — _Depends: E1.F4.T1, E1.F4.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/sponsor.py` (NEW); `plugins/karvey/tests/unit/test_sponsor.py` (NEW, model section); `plugins/karvey/tests/unit/fixtures/sponsor/` (NEW: a change at the architecture gate)  
**Requirements:** REQ-W3-021  
**Tests added:** the fixture yields scope, phase, cost to date, open risks and the sponsor's questions, each dated; owner matched by role or name case-insensitively; sponsor = approver → pending gate listed; no effort → `not measured`; `REQ-…`, `F-NN`, paths and backticked commands removed from the body; risk state shown through the wording table  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sponsor.py' -v` passes

### E1.F4.T5 [Frontend] `templates/sponsor.html`: design-spec tokens, `prefers-color-scheme`, print style, CSP meta, no script needed, 360–1440 px without horizontal scroll + L-64 (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/templates/sponsor.html` (NEW, from the approved `mockup/sponsor.html` without the mockup chrome); `plugins/karvey/scripts/lint-plugin.py` (L-64, also over `docs/karvey.html`); `plugins/karvey/tests/page/test_sponsor_page.mjs` (NEW)  
**Requirements:** REQ-W3-024  
**Tests added:** page test: no `http(s)://` in `src`, `link href`, `@import` or `url()`; the print stylesheet shows every section and hides navigation; computed widths at 360 and 1440 do not exceed the viewport; L-64 mutation: a remote font → error  
**Done when:** `node --test plugins/karvey/tests/page/` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-64` exits 0

### E1.F4.T6 [Backend] `karvey-sponsor.py build|deliver`: leak check before writing, `sponsor-history.jsonl`, `sponsor-refusals.jsonl`, `no sponsor declared` once; `deliver` builds the payload from the checked model and leak-checks it — _Depends: E1.F4.T3, E1.F4.T4, E1.F4.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-sponsor.py` (NEW); `plugins/karvey/tests/unit/test_sponsor.py` (CLI section)  
**Requirements:** REQ-W3-022, REQ-W3-023  
**Tests added:** clean change → page written, history line with sha256; a risk quoting a connection string → exit 3, no file written, the previous page byte-identical, refusal line with field and rule and without the string; no sponsor → one `no sponsor declared` line per change; payload with a leaked value → not printed (F-74)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sponsor.py' -v` passes

### E1.F4.T7 [Backend] `karvey-context.py --report [--from --to --as-of] [--client]`: released, in progress with phase and age, blocked and who unblocks, open risks, decisions awaited per stakeholder; read-only — _Depends: E1.F4.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (`report_view`, parser); `plugins/karvey/tests/unit/test_context_report.py` (NEW)  
**Requirements:** REQ-W3-025  
**Tests added:** one release and two changes in progress → both sections; unknown client → `no changes for client`, exit 0; `git status --porcelain` empty after the run; wording from the table  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_report.py' -v` passes

### E1.F4.T8 [Backend] Events `approval_requested`, `awaiting_human`, `blocked`: schema enum, `resolve notifications --event` → stakeholder of the acting role, else team + `no executor declared`; judge verdict on `blocked`; `rules/notifications.md` — _Depends: E1.F4.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/project.schema.json`; `plugins/karvey/scripts/karvey-config.py` (`resolve_notifications`); `plugins/karvey/skills/karvey/rules/notifications.md`; `plugins/karvey/tests/unit/test_notify_events.py` (NEW)  
**Requirements:** REQ-W3-026 (MODIFIES REQ-ADP-011)  
**Tests added:** `approval_requested` with an approver declared → the approver's destination and a payload naming change and gate; `awaiting_human` without executor → team destination + `no executor declared`; a judge-raised `blocked` carries the verdict line  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_notify_events.py' -v` and `-p 'test_config_resolve.py'` pass

### E1.F4.T9 [Backend] Sent-log `changes/{id}/notifications.jsonl` + `karvey-config.py notify-sent --key`; `qa` first run and verdict change, `deploy` once per version/env, "your turn" once per state; run id + timestamp; qa and deploy text — _Depends: E1.F4.T8_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-config.py` (`cmd_notify_sent`); `plugins/karvey/skills/karvey-qa/SKILL.md`, `karvey-deploy/SKILL.md` (one line each); `plugins/karvey/tests/unit/test_notify_events.py` (dedup section)  
**Requirements:** REQ-W3-027  
**Tests added:** three QA runs, same verdict → one `new`, two `sent`; deploy retry same version/env → `sent`, the retry's run id carried; `notifications.qa_every_run: true` → every run `new`; the log holds hashes and no destination  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_notify_events.py' -v` passes

### E1.F4.T10 [Backend] `karvey-close.py` (C-26): sponsor build/deliver → due events (sent-log) → `effort` last; each failure reported and the next step runs; `rules/gates.md` closing block = one call + send the payloads — _Depends: E1.F4.T6, E1.F4.T9, E1.F3.T4_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-close.py` (NEW); `plugins/karvey/skills/karvey/rules/gates.md` (closing block); `plugins/karvey/tests/unit/test_close.py` (NEW)  
**Requirements:** REQ-W3-022  
**Tests added:** order of steps in the JSON result; `effort` is the last write; a failing sponsor build → reported, events and effort still run; `changes_requested` also regenerates the page; the gate outcome is never changed by the script  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_close.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-41` exits 0

### E1.F4.T11 [Test] Manual script `sponsor-at-gate.md`: a real gate on a fixture change with a sponsor, page opened offline, refusal case, delivery failure → outbox — _Depends: E1.F4.T10_ (P)

**Estimate:** 5 min  
**Files:** `plugins/karvey/tests/manual/sponsor-at-gate.md` (NEW, `manual:` a real gate question and a real channel adapter cannot run in unit tests)  
**Requirements:** REQ-W3-022  
**Tests added:** the manual script  
**Done when:** `test -f plugins/karvey/tests/manual/sponsor-at-gate.md` and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0


## Feature E1.F5: Open questions `Q-NN` and the risk register

Architecture §1.16, §1.17, §2.1 (`risk_log`).  
Requirements covered: 028, 029, 030, 031, 032, 033, 034  
Total estimated time: 82 min (8 tasks)

### E1.F5.T1 [Backend] `karvey_lib/questions.py` + `docs/spec/questions.md` format; decisions skill `ask` (id from `karvey-id.py next Q`, owner and needed-by required, optional context), `cross` offers `ask`, answer → `D-NN` citing the `Q-NN`, question kept `resolved → D-NN`

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/questions.py` (NEW); `plugins/karvey/skills/karvey-decisions/SKILL.md`; `plugins/karvey/tests/unit/test_questions.py` (NEW)  
**Requirements:** REQ-W3-028, REQ-W3-029  
**Tests added:** parse a table with an open and a resolved question; missing owner or needed-by → refusal naming the field; resolving keeps the row and sets `resolved → D-40`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_questions.py' -v` passes

### E1.F5.T2 [Backend] `validate --all`: a `D-NN` that resolves a missing `Q-NN` is reported — _Depends: E1.F5.T1_

**Estimate:** 6 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`cmd_validate`); `plugins/karvey/tests/unit/test_questions.py` (validate case)  
**Requirements:** REQ-W3-029  
**Tests added:** decisions log citing `Q-99` absent → `dangling reference Q-99`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_questions.py' -v` passes

### E1.F5.T3 [Backend] `karvey_lib/risks.py` + `rules/risks.md` (format, states, who creates it) + `validate` reports a risk without owner + architecture skill creates the register (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/risks.py` (NEW); `plugins/karvey/skills/karvey/rules/risks.md` (NEW); `plugins/karvey/skills/karvey-architecture/SKILL.md`; `plugins/karvey/scripts/karvey-state.py` (`cmd_validate`); `plugins/karvey/tests/unit/test_risks.py` (NEW)  
**Requirements:** REQ-W3-031  
**Tests added:** this change's own `risks.md` parses (nine rows); a row without owner → `R-2: owner missing`; no file → no risks  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_risks.py' -v` passes

### E1.F5.T4 [Backend] `karvey-state.py risk {change} R-N review|close|move|mitigate|accept` + `spec.json:risk_log[]`; `move` reserves `BL-NN` and writes the backlog row — _Depends: E1.F5.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (new `cmd_risk`); `plugins/karvey/schemas/spec.schema.json` (`risk_log`); `plugins/karvey/tests/unit/test_risks.py` (command section)  
**Requirements:** REQ-W3-031, REQ-W3-034  
**Tests added:** `review` updates `Last review` and logs; `move` → `moved → BL-NN` and the backlog row cites the risk; unknown risk id → exit 4; `risks.md` and `spec.json` written atomically under the change lock  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_risks.py' -v` passes

### E1.F5.T5 [Backend] Dashboard open-work: open `Q-NN` (owner, needed-by, `overdue`, `date invalid`) + open risks of active changes; session hook lists capped at five lines + `+N more` — _Depends: E1.F5.T1, E1.F5.T3_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (`open_work`, `render`); `plugins/karvey/hooks/karvey-session-context.sh`; `plugins/karvey/tests/unit/test_questions.py` (dashboard section); `plugins/karvey/tests/hooks/tables/session.json` (cap case)  
**Requirements:** REQ-W3-030 (MODIFIES REQ-W1-068)  
**Tests added:** Q-05 needed yesterday → `overdue` with owner; malformed date → `date invalid`, still listed; eight open items → five lines + `+3 more`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_questions.py' -v` and `python3 plugins/karvey/tests/hooks/run_tables.py --only session` pass

### E1.F5.T6 [Backend] Gate summary at *qa* and *release*: open risks with owner, trigger, last review; `risk R-N unreviewed` (warn); `karvey-close.py` step 3 lists the owners to ask — _Depends: E1.F5.T4, E1.F4.T10_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (`gate_summary`); `plugins/karvey/scripts/karvey-close.py` (step 3); `plugins/karvey/tests/unit/test_risks.py` (gate section); `plugins/karvey/tests/unit/test_close.py` (step 3 case)  
**Requirements:** REQ-W3-033  
**Tests added:** two open risks at the release gate → both with owner and trigger; last review before the qa phase entry → `risk R-2 unreviewed`; the close result lists the owners in order  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_risks.py' -v` and `-p 'test_close.py'` pass

### E1.F5.T7 [Backend] `advance archived` refuses an `open` risk and a state without a `risk_log` record; archive skill closes or moves through `risk` — _Depends: E1.F5.T4_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`cmd_advance` precondition); `plugins/karvey/skills/karvey-archive/SKILL.md`; `plugins/karvey/tests/unit/test_risks.py` (archive section)  
**Requirements:** REQ-W3-034  
**Tests added:** one open risk → exit 3 naming it; a hand edit to `closed` without log → `R-1: state without record`; all closed or moved through the command → archive proceeds  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_risks.py' -v` passes

### E1.F5.T8 [Backend] Judges: `"kind": "risk"` → `emergent` row `Routed to: proposed risk`; register-targeting output dropped and reported; iterate accepts into the register — _Depends: E1.F5.T3_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/judges.py` (`collect`); `plugins/karvey/skills/karvey/rules/judges.md` (output contract line); `plugins/karvey/skills/karvey-iterate/SKILL.md`; `plugins/karvey/tests/unit/test_judges.py` (cases)  
**Requirements:** REQ-W3-032  
**Tests added:** a finding with `kind: risk` → row proposed as risk; a result carrying `register_edit` → dropped, `dropped: register edit` reported; `risks.md` untouched by `collect`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_judges.py' -v` passes


## Feature E1.F6: Project design system, design delta, contrast tool, design judge

Architecture §1.18.  
Requirements covered: 035, 036, 037, 038, 039, 076  
Total estimated time: 71 min (7 tasks)

### E1.F6.T1 [Backend] `karvey_lib/designsys.py`: `design-system.md` and `design-delta.md` parsers (tokens, pairs with level, components), colour parsing `#rgb`, `#rrggbb`, `rgb()`, `oklch()`

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/designsys.py` (NEW); `plugins/karvey/tests/unit/test_design_delta.py` (NEW, parser section); `plugins/karvey/tests/unit/fixtures/design/` (NEW: this change's design-spec tokens as a seed system)  
**Requirements:** REQ-W3-035  
**Tests added:** the seed parses into tokens light/dark and pairs; `oklch(50.2% 0.108 61)` converts to within 1/255 of `#8f5312`; an unknown colour syntax → named error  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_design_delta.py' -v` passes

### E1.F6.T2 [Backend] `karvey-contrast-check.py [--file|--delta] [--json]`: WCAG 2.x ratio per declared pair vs its level (AA normal default); unparseable → exit 1 naming the token — _Depends: E1.F6.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-contrast-check.py` (NEW); `plugins/karvey/tests/unit/test_contrast.py` (NEW)  
**Requirements:** REQ-W3-038  
**Tests added:** text-primary on background (light) = 12.96 ± 0.01 (design-spec table); a 7:1 pair → AA and AAA passed; a pair declared AAA at 5.8 → reported; `--color-x: foo` → exit 1 naming `--color-x`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_contrast.py' -v` passes

### E1.F6.T3 [Backend] `karvey-design.py diff {change}`: delta format (Added / Modified with base value / components / `empty`), undeclared modification reported — _Depends: E1.F6.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-design.py` (NEW); `plugins/karvey/tests/unit/test_design_delta.py` (diff section)  
**Requirements:** REQ-W3-036  
**Tests added:** one new component → delta lists it only; primary colour changed in design-spec but not in the delta → `undeclared modification: --color-primary`; no change → `empty`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_design_delta.py' -v` passes

### E1.F6.T4 [Backend] `karvey-design.py apply {change} [--dry-run]`: added tokens written with `Changed by`; a modified token whose current value ≠ base value stops (exit 3) with both values and the last change; archive text asks the human — _Depends: E1.F6.T3_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-design.py`; `plugins/karvey/skills/karvey-archive/SKILL.md` (design step); `plugins/karvey/tests/unit/test_design_delta.py` (apply section)  
**Requirements:** REQ-W3-076  
**Tests added:** untouched token → written, no question; two changes modifying the primary colour, the first archived → second apply exits 3 naming the token, both values and the first change; `--dry-run` writes nothing  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_design_delta.py' -v` passes

### E1.F6.T5 [Backend] Design judge: `rules/judges/design_graphic.md` (lens `design`), `defaults.json` judges phases/lenses, `build_inputs` = delta + "Applies to" mockups (≤ 200 KB each) + rubric + contrast JSON — _Depends: E1.F6.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/skills/karvey/rules/judges/design_graphic.md` (NEW); `plugins/karvey/scripts/karvey_lib/defaults.json`; `plugins/karvey/scripts/karvey_lib/judges.py` (`PHASES_WITH_RUBRIC`, `build_inputs`); `plugins/karvey/tests/unit/test_judges.py` (design cases)  
**Requirements:** REQ-W3-039 (MODIFIES REQ-W2-022)  
**Tests added:** `inputs {change} design_graphic` on a `feature-ui` fixture → one lens `design`, the contrast JSON among the inputs; a 300 KB mockup → `dropped:` line; `standard` lane → `judges: phase not judged`; L-51 still passes with the new rubric  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_judges.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-51` exits 0

### E1.F6.T6 [Backend] design-graphic skill: read the design system, write the delta, art catalogue only on an asset request, the self-score section removed, the design judge before the gate + L-66, L-67 — _Depends: E1.F6.T3, E1.F6.T5_

**Estimate:** 12 min  
**Files:** `plugins/karvey/skills/karvey-design-graphic/SKILL.md`; `plugins/karvey/scripts/lint-plugin.py` (L-66, L-67); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-035, REQ-W3-036, REQ-W3-037, REQ-W3-039  
**Tests added:** L-66 mutation: a template with a country-specific identifier example → error; L-67 mutation: a "Score (0-10)" table in the skill's output instructions → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-66,L-67` exits 0 and `grep -c 'karvey-contrast-check.py' plugins/karvey/skills/karvey-design-graphic/SKILL.md` ≥ 1

### E1.F6.T7 [Test] Manual script `design-judge-gate.md`: a `feature-ui` fixture change without an asset request → no art catalogue; the judge verdict and the contrast result in the gate summary — _Depends: E1.F6.T6_ (P)

**Estimate:** 5 min  
**Files:** `plugins/karvey/tests/manual/design-judge-gate.md` (NEW, `manual:` a real subagent judge)  
**Requirements:** REQ-W3-037, REQ-W3-039  
**Tests added:** the manual script  
**Done when:** `test -f plugins/karvey/tests/manual/design-judge-gate.md` and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0


## Feature E1.F7: One work breakdown (WBS)

Architecture §1.19.  
Requirements covered: 040, 041, 042, 043  
Total estimated time: 35 min (4 tasks)

### E1.F7.T1 [Backend] Text: Feature = functional area; phases as an Epic checklist/field; `E{n}.QA` / `E{n}.DEPLOY` natural keys under the Epic; parent/child, dependencies only between siblings; a tool without parent/child records the parent in a field + L-68

**Estimate:** 12 min  
**Files:** `plugins/karvey/skills/karvey/rules/management-adapters.md`; `plugins/karvey/skills/karvey/rules/clickup-protocol.md` (the `:191` paragraph); `plugins/karvey/skills/karvey-tasks/SKILL.md`, `karvey-qa/SKILL.md`, `karvey-deploy/SKILL.md`; `plugins/karvey/scripts/lint-plugin.py` (L-68); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-040, REQ-W3-041 (MODIFIES REQ-W1-089), REQ-W3-042  
**Tests added:** L-68 mutation: "each pipeline phase maps to a Feature" → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-68` exits 0 and `grep -c 'E{n}.QA' plugins/karvey/skills/karvey/rules/management-adapters.md` ≥ 1

### E1.F7.T2 [Backend] `karvey-trace.py --wbs {change}`: every task under exactly one Feature (or `E{n}.QA` / `E{n}.DEPLOY`); a requirement across two Features needs `Split:` (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-trace.py` (`--wbs`); `plugins/karvey/tests/unit/test_wbs.py` (NEW)  
**Requirements:** REQ-W3-043  
**Tests added:** a task outside any Feature → reported with its id; a requirement in two Features without `Split:` → reported; this file (`wave3-optimization/tasks.md`) → no issue  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_wbs.py' -v` passes and `python3 plugins/karvey/scripts/karvey-trace.py wave3-optimization --wbs` exits 0

### E1.F7.T3 [Backend] Tracker reconciliation: 4.0 items reported `legacy shape`, root-level QA/deploy items `outside the hierarchy`, never rewritten — _Depends: E1.F7.T1, E1.F7.T2_

**Estimate:** 8 min  
**Files:** `plugins/karvey/skills/karvey/rules/phase-close.md` (reconciliation step); `plugins/karvey/scripts/karvey-trace.py` (`--wbs` over `PLAN.md`); `plugins/karvey/tests/unit/test_wbs.py` (legacy section)  
**Requirements:** REQ-W3-040, REQ-W3-041  
**Tests added:** a Wave 2-shaped PLAN with a phase Feature → `legacy shape`, file unchanged; a QA item at the root → `outside the hierarchy`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_wbs.py' -v` passes

### E1.F7.T4 [Test] Manual script `tracker-wbs.md` on the Markdown tracker: Features = areas, phases on the Epic, `E1.QA` / `E1.DEPLOY` found or created once — _Depends: E1.F7.T3_ (P)

**Estimate:** 5 min  
**Files:** `plugins/karvey/tests/manual/tracker-wbs.md` (NEW, `manual:` needs a tracker session)  
**Requirements:** REQ-W3-042  
**Tests added:** the manual script  
**Done when:** `test -f plugins/karvey/tests/manual/tracker-wbs.md` and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0


## Feature E1.F8: Organisation portfolio

Architecture §1.20, §3 (S-4, S-5, S-12).  
Requirements covered: 044, 045, 046, 047, 048, 078, 079  
Total estimated time: 63 min (6 tasks)

### E1.F8.T1 [Backend] `client` first-level in project and spec schemas; a change inherits it at init; `validate` warns on a differing tracker tag naming both

**Estimate:** 10 min  
**Files:** `plugins/karvey/schemas/project.schema.json`, `spec.schema.json`; `plugins/karvey/scripts/karvey-state.py` (`cmd_init`, `cmd_validate`); `plugins/karvey/skills/karvey-init/SKILL.md`; `plugins/karvey/tests/unit/test_stakeholders.py` (client section)  
**Requirements:** REQ-W3-044  
**Tests added:** project `client` → new change inherits it; `client: a` with tag `b` → warning naming both, exit 0  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_stakeholders.py' -v` passes

### E1.F8.T2 [Backend] Both spec layouts (`docs/spec/`, `spec/`) in `project.py`, the session hook and the dashboard; `two spec roots` uses `docs/spec/` (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/project.py` (`is_karvey_project`, `list_changes`); `plugins/karvey/hooks/karvey-session-context.sh`; `plugins/karvey/scripts/karvey-context.py`; `plugins/karvey/tests/unit/test_context.py` (layout cases); `plugins/karvey/tests/hooks/tables/session.json` (case)  
**Requirements:** REQ-W3-048 (MODIFIES REQ-W1-045)  
**Tests added:** a repo with `spec/project.json` → found, layout `spec/`; both → `two spec roots`, `docs/spec/` read; archive and implemented changes excluded under either root  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context.py' -v` and `python3 plugins/karvey/tests/hooks/run_tables.py --only session` pass

### E1.F8.T3 [Backend] `schemas/portfolio.schema.json` + `karvey_lib/portfolio.py`: entry validation before any read, file reads only, 2 MB per read, `sanitise` on foreign text, `clone` never used — _Depends: E1.F8.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/schemas/portfolio.schema.json` (NEW); `plugins/karvey/scripts/karvey_lib/portfolio.py` (NEW); `plugins/karvey/tests/unit/test_portfolio.py` (NEW, reader section)  
**Requirements:** REQ-W3-045, REQ-W3-047  
**Tests added:** five valid entries → five validated; a path with `;` or `$(` → refused and named before any read; permission denied → `not read: permission denied`; `clone` without local path → `not read: no local clone`; a 3 MB file → `not read: file too large`; an ESC sequence in a risk text → stripped  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_portfolio.py' -v` passes

### E1.F8.T4 [Backend] `karvey-context.py --portfolio [--file --from --to --as-of]`: per client and repository — active changes (phase, lane, age), questions and approvals awaited, releases, cost; `not a Karvey project` — _Depends: E1.F8.T3, E1.F3.T7_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (`portfolio_view`, parser); `plugins/karvey/tests/unit/test_portfolio.py` (view section); `plugins/karvey/tests/unit/fixtures/portfolio/` (NEW: three repos of two clients, one `spec/`, one non-Karvey)  
**Requirements:** REQ-W3-046  
**Tests added:** grouped by client with the four column groups; the non-Karvey repo shown as such and the rest rendered; byte-identical output across runs  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_portfolio.py' -v` passes

### E1.F8.T5 [Backend] `--client NAME` (case-insensitive, `other clients: not shown`, `no repositories for client` exit 0) + the printed dashboard command per change (valid id only, `shlex.quote`d path; none for `not read`) — _Depends: E1.F8.T4_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey-context.py`; `plugins/karvey/tests/unit/test_portfolio.py` (client and command sections)  
**Requirements:** REQ-W3-078, REQ-W3-079  
**Tests added:** six repos of two clients, one client → its three and its totals; unknown client → exit 0 with the line; change id `x;rm` → `invalid change id`, no command (F-69); a path with a space → quoted  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_portfolio.py' -v` passes

### E1.F8.T6 [Test] Offline proof in `test_portfolio.py`: `subprocess.Popen` and `socket.socket` patched to fail, every listed repo's file mtimes unchanged, nothing written — _Depends: E1.F8.T4_ (P)

**Estimate:** 6 min  
**Files:** `plugins/karvey/tests/unit/test_portfolio.py` (offline section)  
**Requirements:** REQ-W3-047  
**Tests added:** the view runs with process and socket creation patched to raise; the mtimes of every file under the fixture repos are identical before and after  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_portfolio.py' -v` passes


## Feature E1.F9: Backlog ranked by WSJF, `done-direct`

Architecture §1.21.  
Requirements covered: 049, 050, 051, 052  
Total estimated time: 36 min (4 tasks)

### E1.F9.T1 [Backend] `rules/backlog.md` columns (`Value | Effort | CoD | Needed by | Client | Reviewed | Commit`), formula, `done-direct`; `karvey_lib/backlog.py` (`urgency`, `effort`, `wsjf`, `unscored`)

**Estimate:** 12 min  
**Files:** `plugins/karvey/skills/karvey/rules/backlog.md`; `plugins/karvey/scripts/karvey_lib/backlog.py` (NEW); `plugins/karvey/tests/unit/test_backlog_wsjf.py` (NEW)  
**Requirements:** REQ-W3-049  
**Tests added:** value 4, CoD 3, effort S → 7.0; needed-by in 20 days, value 2, effort 90 min → (2+4)/2 = 3.0; no effort → `unscored`, never 0  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_backlog_wsjf.py' -v` passes

### E1.F9.T2 [Backend] `validate` refuses `done-direct` without a commit — _Depends: E1.F9.T1_

**Estimate:** 6 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`cmd_validate`); `plugins/karvey/tests/unit/test_backlog_wsjf.py` (validate case)  
**Requirements:** REQ-W3-050  
**Tests added:** `done-direct` with `abc1234` → valid; without → refused naming the row  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_backlog_wsjf.py' -v` passes

### E1.F9.T3 [Backend] `karvey-context.py --backlog`: open items by score, unscored apart, `stale` > 30 days, `invalid row` with id; read-only — _Depends: E1.F9.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (`backlog_view`, parser); `plugins/karvey/tests/unit/test_backlog_wsjf.py` (view section)  
**Requirements:** REQ-W3-051  
**Tests added:** ten items → ordered, stale ones flagged; a malformed row → `invalid row BL-07`, others rendered; `git status --porcelain` empty after the run  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_backlog_wsjf.py' -v` passes

### E1.F9.T4 [Backend] Refinement cadence: `project.json:backlog.refine_days` (default 14), `Last refinement:` header, dashboard overview line (`overdue`, `never refined`) — _Depends: E1.F9.T1_

**Estimate:** 8 min  
**Files:** `plugins/karvey/schemas/project.schema.json`; `plugins/karvey/scripts/karvey-context.py` (`overview`); `plugins/karvey/tests/unit/test_backlog_wsjf.py` (cadence section)  
**Requirements:** REQ-W3-052  
**Tests added:** refined 5 days ago → date without flag; 20 days → `overdue`; no header → `never refined`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_backlog_wsjf.py' -v` passes


## Feature E1.F10: Portability

Architecture §1.22.  
Requirements covered: 053, 054, 055, 056, 057, 058, 059, 060  
Total estimated time: 80 min (8 tasks)

### E1.F10.T1 [Backend] `docs/portability.md` (runtime-dependent behaviours, adaptation notes, "Claude Code is the only supported runtime", D-32) + L-69 (P)

**Estimate:** 12 min  
**Files:** `docs/portability.md` (NEW); `plugins/karvey/scripts/lint-plugin.py` (L-69); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-053  
**Tests added:** L-69 mutation: a hook event added to `hooks.json` without a guide entry → error; an `allowed-tools` name absent from the guide → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-69` exits 0

### E1.F10.T2 [Backend] `browse.via` (`local` \| `agent:<name>` \| `none`): schema, `karvey-config.py resolve browse`, browse skill (self-contained instruction with declared URLs only, navigate/read/capture), QA visual dimension `not evaluated` + manual `browse-via-agent.md` (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/project.schema.json`; `plugins/karvey/scripts/karvey-config.py`; `plugins/karvey/skills/karvey-browse/SKILL.md`, `karvey-qa/SKILL.md`; `plugins/karvey/tests/unit/test_browse_via.py` (NEW); `plugins/karvey/tests/manual/browse-via-agent.md` (NEW, `manual:` a second agent session)  
**Requirements:** REQ-W3-054  
**Tests added:** `agent:qa-browser` valid; `agent:` empty or with a space refused; `none` → `not evaluated (browse.via: none)`; default `local`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_browse_via.py' -v` passes

### E1.F10.T3 [Backend] OS-neutral open in the mockup skill (path + `python3 -m webbrowser <path>`) + L-70 (P)

**Estimate:** 6 min  
**Files:** `plugins/karvey/skills/karvey-mockup/SKILL.md` (`:152`, `:181`, `:189`); `plugins/karvey/scripts/lint-plugin.py` (L-70); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-055  
**Tests added:** L-70 mutation: `open docs/x.html` and `xdg-open x` → errors  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-70` exits 0

### E1.F10.T4 [Backend] No fixed country time: `changelog-policy.md:29` → project `time_zone` or environment, ISO 8601 with offset; `time_zone` in the project schema; statusline comment example `Area/City` + L-71 (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/skills/karvey/rules/changelog-policy.md`; `plugins/karvey/schemas/project.schema.json`; `plugins/karvey/hooks/karvey-statusline.sh` (comment); `plugins/karvey/scripts/lint-plugin.py` (L-71); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-056  
**Tests added:** L-71 mutation: a rule naming a country's time or an IANA zone literal → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-71` exits 0

### E1.F10.T5 [Backend] `schemas/incident-states.json` (neutral + localized aliases) in `read_bugs`, L-32 and `rules/incident-tracking.md` (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/incident-states.json` (NEW); `plugins/karvey/scripts/karvey-context.py` (`read_bugs`); `plugins/karvey/scripts/lint-plugin.py` (L-32); `plugins/karvey/skills/karvey/rules/incident-tracking.md`; `plugins/karvey/tests/unit/test_incident_states.py` (NEW)  
**Requirements:** REQ-W3-057 (MODIFIES REQ-W1-068)  
**Tests added:** a history in the localized names validates, each mapped; neutral names validate; an unknown state → reported with the accepted list; `docs/bugs_dev_testing.md` of this repo still passes L-32  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_incident_states.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-32` exits 0

### E1.F10.T6 [Backend] `karvey_lib/runtime.py loaded_version()` (read-only record) + health skill `loaded X, available Y` / `loaded version unknown` (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/runtime.py` (NEW); `plugins/karvey/skills/karvey-health/SKILL.md` (`:100`); `plugins/karvey/tests/unit/test_runtime_version.py` (NEW, temp config dir)  
**Requirements:** REQ-W3-058  
**Tests added:** record with 4.0.0 and clone 4.1.0 → `loaded 4.0.0, available 4.1.0`; no record → `loaded version unknown`; the record file's mtime unchanged  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_runtime_version.py' -v` passes

### E1.F10.T7 [Backend] `settings invalid ({key} …)` in the session hook and the dashboard from `karvey-config.py resolve`; aliases shown normalised (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/hooks/karvey-session-context.sh`; `plugins/karvey/scripts/karvey-context.py` (`settings`); `plugins/karvey/tests/unit/test_settings_line.py` (NEW); `plugins/karvey/tests/hooks/tables/session.json` (case)  
**Requirements:** REQ-W3-059  
**Tests added:** status map under an unknown key → `settings invalid (management.statuses missing)`; a documented alias → passes, shown normalised  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_settings_line.py' -v` and `python3 plugins/karvey/tests/hooks/run_tables.py --only session` pass

### E1.F10.T8 [Backend] L-72: example actors are placeholders or roles; model ids are not actors; existing violations fixed (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-72); the skill and rule lines it reports; `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-060  
**Tests added:** L-72 mutation: `Executor:` followed by a person's name and `--by "claude-x"` in an example → errors; `Executor: {name / role}` → passes  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-72` exits 0


## Feature E1.F2: Context budget — core, load lists, adapters, references, routing-only orchestrator (after F3..F10)

Architecture §1.4..§1.8, §1.22-bis (step 5).  
Requirements covered: 003, 004, 005, 006, 007, 008, 009, 012, 013  
Total estimated time: 157 min (13 tasks)

### E1.F2.T1 [Backend] `schemas/contracts.json` baseline map (phase → contract, from the 4.0 closure in `context-size-4.0.0.json`) + `contracts` sub-command + CI step + `test_ci_workflow.py` case — _Depends: E1.F1.T4, E1.F1.T6_

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/contracts.json` (NEW, anchors still in the 4.0 rules); `plugins/karvey/scripts/karvey-context-budget.py` (`contracts`); `.github/workflows/lint.yml` (contracts step); `plugins/karvey/tests/unit/test_contracts.py` (NEW); `plugins/karvey/tests/unit/test_ci_workflow.py`  
**Requirements:** REQ-W3-009  
**Tests added:** on the current tree every `(phase, contract)` is covered; a fixture with the prod-gate anchor removed from deploy's path → `deploy: contract prod-gate not loaded`, exit 1; the CI job runs the step  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_contracts.py' -v` and `-p 'test_ci_workflow.py'` pass and `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0

### E1.F2.T2 [Backend] `rules/_core.md`: seven contracts with `{#contract-<id>}` headings, ≤ 1,000 words; `contracts.json` anchors → the core; "footnotes are never opened" + L-55 — _Depends: E1.F2.T1, E1.F3.T8, E1.F4.T11, E1.F5.T6, E1.F5.T7, E1.F5.T8, E1.F6.T7, E1.F7.T4, E1.F8.T5, E1.F8.T6, E1.F9.T4, E1.F10.T1, E1.F10.T2, E1.F10.T3, E1.F10.T4, E1.F10.T5, E1.F10.T6, E1.F10.T7, E1.F10.T8_

**Estimate:** 12 min  
**Files:** `plugins/karvey/skills/karvey/rules/_core.md` (NEW); `plugins/karvey/schemas/contracts.json`; `plugins/karvey/scripts/lint-plugin.py` (L-55); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-003  
**Tests added:** L-55 mutations: the core at 1,200 words → error with the count; a contract heading without an id → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-55` exits 0 and `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0

- The dependency on the last task of every feature F3..F10 is the "reorganise the final text" rule (PRD §6 internal order): no skill is restructured twice.

### E1.F2.T3 [Backend] Tracker adapters: `rules/adapters/{markdown,clickup,jira,linear,azure-boards,github-projects,spreadsheet}.md` from `management-adapters.md` + `clickup-protocol.md`; per-tool examples moved out of init, tasks, impl, qa, deploy, archive + L-58 — _Depends: E1.F2.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/skills/karvey/rules/adapters/*.md` (NEW, 7); `plugins/karvey/skills/karvey/rules/management-adapters.md` (tool-neutral part kept); `plugins/karvey/skills/karvey/rules/clickup-protocol.md` (removed, content in `adapters/clickup.md`); the six skills; `plugins/karvey/scripts/lint-plugin.py` (L-58, and L-31 paths); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-006  
**Tests added:** L-58 mutation: an `api.clickup.com` call in `karvey-tasks/SKILL.md` → error; the size tool on a Markdown-tracker project loads only `adapters/markdown.md`  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0 and `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0

### E1.F2.T4 [Backend] `Load:` lines + rule citations → footnotes, batch 1: init, requirements, mockup, design-graphic, architecture, infra, tasks — _Depends: E1.F2.T3_

**Estimate:** 15 min  
**Files:** the seven `SKILL.md` files  
**Requirements:** REQ-W3-004  
**Tests added:** none new (L-56 lands in T7); `contracts` must stay green  
**Done when:** `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0, `python3 plugins/karvey/scripts/lint-plugin.py` exits 0, and `grep -c '^Load:' plugins/karvey/skills/karvey-{init,requirements,mockup,design-graphic,architecture,infra,tasks}/SKILL.md` gives 1 per file

### E1.F2.T5 [Backend] `Load:` lines + footnotes, batch 2: impl, test, qa, deploy, archive, iterate, judges, decisions, context, checkpoint — _Depends: E1.F2.T4_

**Estimate:** 15 min  
**Files:** the ten `SKILL.md` files  
**Requirements:** REQ-W3-004  
**Tests added:** none new (L-56 in T7)  
**Done when:** `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0 and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F2.T6 [Backend] Rules cite rules only in footnotes (the 26 rules and the adapters) + L-57 — _Depends: E1.F2.T2_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/skills/karvey/rules/*.md`, `rules/adapters/*.md`; `plugins/karvey/scripts/lint-plugin.py` (L-57); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-005  
**Tests added:** L-57 mutation: "load `rules/y.md` before continuing" in a rule → error; the size tool: closure of every phase = its `Load:` list + core  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-57` exits 0 and `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0

### E1.F2.T7 [Backend] L-56: every rule or reference path in a skill body (outside footnotes and fences) is in its `Load:` list — _Depends: E1.F2.T5, E1.F2.T6_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-56); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-004  
**Tests added:** L-56 mutation: "read `rules/x.md`" with `x` absent from `Load:` → error naming skill, line and rule  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-56` exits 0

### E1.F2.T8 [Backend] Init references `team-settings.md`, `settings.md` with one-line pointers (load condition) — _Depends: E1.F2.T5_

**Estimate:** 10 min  
**Files:** `plugins/karvey/skills/karvey-init/references/{team-settings,settings}.md` (NEW); `plugins/karvey/skills/karvey-init/SKILL.md`  
**Requirements:** REQ-W3-007  
**Tests added:** the size tool: init's `closure_min` excludes both references, `closure_max` includes them  
**Done when:** `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0 and `python3 plugins/karvey/scripts/lint-plugin.py` exits 0

### E1.F2.T9 [Backend] Deploy references `docs-only.md`, `hotfix.md`, `postdeploy.md`, `branch-hygiene.md` with pointers + L-59 (orphans; the set equals the closed list) — _Depends: E1.F2.T8_

**Estimate:** 12 min  
**Files:** `plugins/karvey/skills/karvey-deploy/references/*.md` (NEW, 4); `plugins/karvey/skills/karvey-deploy/SKILL.md`; `plugins/karvey/scripts/lint-plugin.py` (L-59); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-007  
**Tests added:** L-59 mutations: a reference no skill points to → `orphaned`; a reference outside the closed list → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-59,L-53` exits 0 and `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0

### E1.F2.T10 [Backend] Orchestrator routing-only ≤ 1,200 words; feature lists, per-phase descriptions, equivalences, authorship → README and `skills/karvey/references/{overview,equivalences}.md` + L-60 + `test_orchestrator_routing.py` — _Depends: E1.F2.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/skills/karvey/SKILL.md`; `plugins/karvey/skills/karvey/references/{overview,equivalences}.md` (NEW); `plugins/karvey/README.md`; `plugins/karvey/scripts/lint-plugin.py` (L-60); `plugins/karvey/tests/unit/test_orchestrator_routing.py` (NEW)  
**Requirements:** REQ-W3-008  
**Tests added:** every `(lane, phase)` with a non-`s` rule is routed to the skill `state-machine.json` names; a removed routing row → fails naming phase and lane; L-60 mutation at 1,300 words → error  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_orchestrator_routing.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-60,L-11` exits 0

### E1.F2.T11 [Backend] `karvey-context-budget.py render [--check]`: the orchestrator's "applies in" column, the adapters' "used by" lines, the README per-phase list between `karvey:generated load-lists` markers + L-61 — _Depends: E1.F2.T10, E1.F2.T3_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-context-budget.py` (`render`); the three files' generated blocks; `plugins/karvey/scripts/lint-plugin.py` (L-61); `plugins/karvey/tests/unit/test_context_budget.py` (render section)  
**Requirements:** REQ-W3-012  
**Tests added:** a `Load:` change → the three blocks change on `render`; a hand edit inside a block → L-61 drift error  
**Done when:** `python3 plugins/karvey/scripts/karvey-context-budget.py render --check` exits 0 and `python3 plugins/karvey/scripts/lint-plugin.py --only L-61` exits 0

### E1.F2.T12 [Backend] One phase per session: `karvey-close.py` step 5 (checkpoint line; the script compares the capture's context reading with the checkpoint threshold) + checkpoint skill text + `observed --transcript` + manual `one-phase-per-session.md` — _Depends: E1.F4.T10_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-close.py` (step 5); `plugins/karvey/scripts/karvey-context-budget.py` (`observed`); `plugins/karvey/skills/karvey-checkpoint/SKILL.md`; `plugins/karvey/tests/unit/test_close.py` (step 5 cases); `plugins/karvey/tests/manual/one-phase-per-session.md` (NEW, `manual:` a real fresh session)  
**Requirements:** REQ-W3-013  
**Tests added:** reading at `context_pct.red` → `recommend: checkpoint + fresh session before the next skill`; below → offer only; no reading → `context reading unavailable`; `observed` on a fixture transcript lists a footnote-only rule that was opened  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_close.py' -v` passes

### E1.F2.T13 [Test] After snapshot `docs/spec/retros/context-size-4.1.0.json`; `compare` ≥ 40% median; `contracts` green; per-phase reasons recorded in `contracts.json` — _Depends: E1.F2.T7, E1.F2.T9, E1.F2.T11, E1.F2.T12_

**Estimate:** 8 min  
**Files:** `docs/spec/retros/context-size-4.1.0.json` (NEW); `plugins/karvey/schemas/contracts.json` (`reasons`)  
**Requirements:** REQ-W3-009  
**Split:** it also runs REQ-W3-010's comparison (built in E1.F1.T3) on the final text; the check belongs to F1, the text it measures to F2.  
**Tests added:** none new; the measured result is evidence  
**Done when:** `python3 plugins/karvey/scripts/karvey-context-budget.py compare docs/spec/retros/context-size-4.0.0.json docs/spec/retros/context-size-4.1.0.json --target-median 40` exits 0 and `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0

- If the median misses 40%, the task stops and the finding goes to `findings.md` (risk R-2); the test phase fails by REQ-W3-010, it is not waived here.


## Feature E1.F11: Rollout 4.1.0 and dogfooding

Architecture §1.23, §7, §7.3.  
Requirements covered: 061, 062, 063, 064, 065, 073, 074, 075  
Total estimated time: 64 min (7 tasks)

### E1.F11.T1 [Backend] `check-modes.json`: `"4.1"` default in every row + the sixteen Wave 3 rows (two blocking); `modes.release_line` maps 4.1.x; L-73 (scheduled first, with F1) (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/schemas/check-modes.json`; `plugins/karvey/scripts/karvey_lib/modes.py`; `plugins/karvey/scripts/lint-plugin.py` (L-73); `plugins/karvey/tests/unit/test_modes.py` (cases)  
**Requirements:** REQ-W3-061  
**Tests added:** no Wave 3 `4.1` default is blocking except `sponsor.leak` and `loadlist.missing`; Wave 2 rows keep their `4.0` values under `4.1`; L-73 mutation: a check id used in code and absent from the registry → error  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_modes.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-73,L-47` exits 0

### E1.F11.T2 [Backend] `validate --fix` proposes `clickup.client_tag` → `client` (diff first, idempotent, never an approval; nothing when `client` is set) — _Depends: E1.F8.T1_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey-state.py` (`fix_spec`, `:625`); `plugins/karvey/tests/unit/test_state_fix.py` (cases); `plugins/karvey/tests/fixtures/legacy/spec/` (one fixture with a tag)  
**Requirements:** REQ-W3-063 (MODIFIES REQ-W1-009)  
**Tests added:** tag set, no `client` → proposal with diff; second run → no change; `client` set and different → no proposal, both values reported  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_state_fix.py' -v` passes

### E1.F11.T3 [Test] Compatibility 4.0 → 4.1: `compat.json` cases + `test_compat_w3.py` (the 4.0 fixtures pass `validate --strict`, the linter over a fixture project and the guard tables with 4.1 defaults) — _Depends: E1.F2.T13, E1.F11.T1, E1.F11.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/tests/hooks/tables/compat.json`; `plugins/karvey/tests/unit/test_compat_w3.py` (NEW)  
**Requirements:** REQ-W3-062  
**Tests added:** every 4.0 fixture passes; a fixture with `judges.budget` passes with a warning; a fixture failing under 4.1 would name the check  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_compat_w3.py' -v` and `python3 plugins/karvey/tests/hooks/run_tables.py --only compat` pass

### E1.F11.T4 [Backend] Dogfooding: `spec.json:stakeholders.sponsor` (role "method owner", `channel: none`), effort from the next gate, `sponsor-history.jsonl` with `no page (generator not built yet)` for the gates closed before C-13; the design judge once on this change's design (F-68) — _Depends: E1.F4.T10, E1.F6.T5_

**Estimate:** 10 min  
**Files:** `docs/spec/changes/wave3-optimization/spec.json` (through the state tool and `karvey-sponsor.py`); `docs/spec/changes/wave3-optimization/sponsor.html`, `sponsor-history.jsonl` (generated); `docs/spec/changes/wave3-optimization/findings.md` (design-judge rows, if any)  
**Requirements:** REQ-W3-073, REQ-W3-074, REQ-W3-075  
**Tests added:** none new — manual: REQ-W3-074 and REQ-W3-075 are change-scoped; their evidence is this change's own `effort[]` and `sponsor-history.jsonl`, read by the test phase (architecture §6.4)  
**Done when:** `python3 plugins/karvey/scripts/karvey-state.py validate wave3-optimization` exits 0 with lane `feature-ui`, and `python3 plugins/karvey/scripts/karvey-sponsor.py build wave3-optimization --gate how` exits 0 (leak check passed)

### E1.F11.T5 [Backend] Hand-off `upgrade-steps.handoff.json`: the fourteen §7.3 rows in the catalogue's field shape, `status: declared` — _Depends: E1.F8.T1, E1.F9.T1, E1.F10.T5, E1.F3.T5_ (P)

**Estimate:** 8 min  
**Files:** `docs/spec/changes/wave3-optimization/upgrade-steps.handoff.json` (NEW)  
**Requirements:** REQ-W3-062  
**Tests added:** the shape check below  
**Done when:** `python3 -c "import json;d=json.load(open('docs/spec/changes/wave3-optimization/upgrade-steps.handoff.json'));r={'id','since','check','fix','dry_run','human','risk'};assert len(d['steps'])==14 and all(r<=set(s) for s in d['steps']);print('ok')"` prints `ok`

### E1.F11.T6 [Test] Whole-repo gate: lint 0, every unit and regression suite, every table, the page tests, `validate --all`, `karvey-trace.py wave3-optimization --check` 80/80 and `--wbs`, `contracts`, `compare`, release manifest maps every commit — _Depends: every agent task of F1..F11 (E1.F11.T5 and E1.F11.T4 included)_

**Estimate:** 10 min  
**Files:** `docs/spec/changes/wave3-optimization/traceability.md` (generated); `test_evidence.md`; `evidence.jsonl`  
**Requirements:** REQ-W3-061, REQ-W3-062, REQ-W3-065, REQ-W3-073  
**Tests added:** none new; runs everything through `karvey-evidence.py`  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0; `python3 -m unittest discover -s plugins/karvey/tests/unit` and `-s plugins/karvey/tests/regression` pass; `python3 plugins/karvey/tests/hooks/run_tables.py` passes; `node --test plugins/karvey/tests/page/` passes; `python3 plugins/karvey/scripts/karvey-trace.py wave3-optimization --check` prints `80/80`; `python3 plugins/karvey/scripts/karvey-release-gate.py manifest --json` lists no `unmapped` commit of this change

### E1.F11.T7 [Backend] Release docs: `[Unreleased]` summary — context size before/after (both snapshots, median), this change's cost with "single-agent cost before 4.1 not measured", the manual Upgrade list from the hand-off, the 4.0 → 4.1 note; no version or date — _Depends: E1.F11.T6_

**Estimate:** 6 min  
**Files:** `CHANGELOG.md` (the `[Unreleased]` block; each impl task already added its own line); `docs/spec/changes/wave3-optimization/PLAN.md` (feature states)  
**Requirements:** REQ-W3-064  
**Tests added:** L-12, L-13, L-19 (existing) on the block  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0 and `sed -n '/## \[Unreleased\]/,/## \[/p' CHANGELOG.md | grep -c -E 'not measured|context-size-4.1.0|client-from-tag'` ≥ 3

- The version number and date belong to `karvey-deploy` at release; the final cost figure is completed there from `effort[]`.


## Feature E1.F12: Method page in nine languages — last (B-06)

Architecture §1.24.  
Requirements covered: 066, 067, 068, 069, 070  
Total estimated time: 203 min (18 tasks)

### E1.F12.T1 [Frontend] Nine-language scaffold: `LANGS`, head `ok()` list, CSS selectors, language list + `select` under 720 px, `I18N` entries (it, ja, fr, ko), `--font-cjk` stack, `html[lang]` per selection; `test_page_static.py` and `test_page.mjs` for nine — _Depends: E1.F11.T7_

**Estimate:** 12 min  
**Files:** `docs/karvey.html` (`:10-19`, `:113-119`, `:316-320`, `:4515-4523`); `plugins/karvey/tests/unit/test_page_static.py` (`LANGS`); `plugins/karvey/tests/page/test_page.mjs`  
**Requirements:** REQ-W3-066 (MODIFIES REQ-ADP-031), REQ-W3-068  
**Tests added:** `navigator.language = ko-KR` → Korean, tab title in Korean; `?lang=xx` → English and nothing saved; `?lang=ja` → `document.documentElement.lang === 'ja'`; no external request  
**Done when:** `node --test plugins/karvey/tests/page/` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` pass

- The four new `lang-block`s are added by T3..T14; until then the scaffold test skips their content check (not their selection).

### E1.F12.T2 [Frontend] Wave 3 section (load lists, sponsor page, questions and risks, cost, design system, portfolio, WSJF, portability guide) with counts, in en, es, pt, de, zh — _Depends: E1.F12.T1_

**Estimate:** 15 min  
**Files:** `docs/karvey.html` (the five existing blocks)  
**Requirements:** REQ-W3-070  
**Tests added:** L-11 (T17) counts; the section id present in each block  
**Done when:** `node --test plugins/karvey/tests/page/` passes and `grep -c 'id="wave3' docs/karvey.html` ≥ 5

### E1.F12.T3 [Frontend] Italian block, part 1 of 3 (the first third of the English block's sections, in `<section id>` order) — _Depends: E1.F12.T2_

**Estimate:** 12 min  
**Files:** `docs/karvey.html` (`lang-block data-lang="it"`)  
**Requirements:** REQ-W3-066  
**Tests added:** none new (L-74 in T15)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes

### E1.F12.T4 [Frontend] Italian block, part 2 of 3 — _Depends: E1.F12.T3_

**Estimate:** 12 min  
**Files:** `docs/karvey.html`  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes

### E1.F12.T5 [Frontend] Italian block, part 3 of 3 (incl. the Wave 3 section) — _Depends: E1.F12.T4_

**Estimate:** 12 min  
**Files:** `docs/karvey.html`  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes and every section id of the `en` block exists in the `it` block

### E1.F12.T6 [Frontend] Japanese block, part 1 of 3 — _Depends: E1.F12.T2_ (P)

**Estimate:** 12 min  
**Files:** `docs/karvey.html` (`lang-block data-lang="ja"`)  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes

### E1.F12.T7 [Frontend] Japanese block, part 2 of 3 — _Depends: E1.F12.T6_

**Estimate:** 12 min  
**Files:** `docs/karvey.html`  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes

### E1.F12.T8 [Frontend] Japanese block, part 3 of 3 — _Depends: E1.F12.T7_

**Estimate:** 12 min  
**Files:** `docs/karvey.html`  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes and every section id of the `en` block exists in the `ja` block

### E1.F12.T9 [Frontend] French block, part 1 of 3 — _Depends: E1.F12.T2_ (P)

**Estimate:** 12 min  
**Files:** `docs/karvey.html` (`lang-block data-lang="fr"`)  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes

### E1.F12.T10 [Frontend] French block, part 2 of 3 — _Depends: E1.F12.T9_

**Estimate:** 12 min  
**Files:** `docs/karvey.html`  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes

### E1.F12.T11 [Frontend] French block, part 3 of 3 — _Depends: E1.F12.T10_

**Estimate:** 12 min  
**Files:** `docs/karvey.html`  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes and every section id of the `en` block exists in the `fr` block

### E1.F12.T12 [Frontend] Korean block, part 1 of 3 — _Depends: E1.F12.T2_ (P)

**Estimate:** 12 min  
**Files:** `docs/karvey.html` (`lang-block data-lang="ko"`)  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes

### E1.F12.T13 [Frontend] Korean block, part 2 of 3 — _Depends: E1.F12.T12_

**Estimate:** 12 min  
**Files:** `docs/karvey.html`  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes

### E1.F12.T14 [Frontend] Korean block, part 3 of 3 — _Depends: E1.F12.T13_

**Estimate:** 12 min  
**Files:** `docs/karvey.html`  
**Requirements:** REQ-W3-066  
**Tests added:** none new  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_page_static.py' -v` passes and every section id of the `en` block exists in the `ko` block

### E1.F12.T15 [Backend] L-74: every translatable key and section in nine languages, none empty — _Depends: E1.F12.T5, E1.F12.T8, E1.F12.T11, E1.F12.T14_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-74); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-067  
**Tests added:** L-74 mutation: one Japanese key removed → error naming key and language; an empty value → error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-74` exits 0

### E1.F12.T16 [Frontend] Anchor aliases: `ANCHOR_ALIASES` (the anchors renamed after 3.10.0, from `git log -p docs/karvey.html`) on load and `hashchange`, every language + L-75 + page test — _Depends: E1.F12.T1_ (P)

**Estimate:** 10 min  
**Files:** `docs/karvey.html` (script); `plugins/karvey/scripts/lint-plugin.py` (L-75); `plugins/karvey/tests/page/test_page.mjs` (hash case); `plugins/karvey/tests/unit/test_lint_w3.py`  
**Requirements:** REQ-W3-069  
**Tests added:** page test: an old anchor → scrolls to its renamed id in `en` and `ko`; L-75 mutation: an alias to a missing id → error  
**Done when:** `node --test plugins/karvey/tests/page/` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-75` exits 0

### E1.F12.T17 [Backend] L-11 extended: the page's Wave 3 counts (skills, rules, scripts) match the plugin in every language — _Depends: E1.F12.T2_ (P)

**Estimate:** 6 min  
**Files:** `plugins/karvey/scripts/lint-plugin.py` (L-11); `plugins/karvey/tests/unit/test_lint_plugin.py` (case)  
**Requirements:** REQ-W3-070  
**Tests added:** mutation: a script count off by one in the `ja` block → error naming the language  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-11` exits 0

### E1.F12.T18 [Test] Final gate: lint 0, page and unit suites, `karvey-trace.py wave3-optimization --check` 80/80, and the plan-order check (every F12 task after the last task of every other feature) — _Depends: E1.F12.T15, E1.F12.T16, E1.F12.T17_

**Estimate:** 8 min  
**Files:** `docs/spec/changes/wave3-optimization/traceability.md` (regenerated); `test_evidence.md`; `evidence.jsonl`  
**Requirements:** REQ-W3-070  
**Tests added:** none new  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` exits 0, `node --test plugins/karvey/tests/page/` passes, `python3 plugins/karvey/scripts/karvey-trace.py wave3-optimization --check` prints `80/80`, and `git log --format=%s` shows no F12 task commit before the F11.T7 commit


## Epic item E1.DEPLOY

### E1.DEPLOY.T1 [human] The prod OK for the release that ships this change (D-10) — _Depends: E1.F12.T18_

**Executor:** the owner — never delegated  
**Command:** inside `karvey-deploy`, after reading the release PR (its manifest lists every change and commit; the sponsor page and the release notes carry the size before/after and the cost), type your own words with an approval **and** a production term, and answer the structured question that records the D-NN  
**Verification:** `python3 plugins/karvey/scripts/karvey-state.py check-prod wave3-optimization --json` → `ok: true` after `approve prod`  
**Rollback:** before the merge: nothing, the marker expires; after it: a revert PR, as a new change through the method  
**Requirements:** REQ-W3-065  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)


## Traceability matrix (REQ-W3 → tasks)

| REQ-W3 | Tasks |
|---|---|
| 001 | E1.F1.T1, E1.F1.T2 |
| 002 | E1.F1.T4 |
| 003 | E1.F2.T2 |
| 004 | E1.F2.T4, E1.F2.T5, E1.F2.T7 |
| 005 | E1.F2.T6 |
| 006 | E1.F2.T3 |
| 007 | E1.F2.T8, E1.F2.T9 |
| 008 | E1.F2.T10 |
| 009 | E1.F2.T1, E1.F2.T13 |
| 010 | E1.F1.T3 (run on the final text by E1.F2.T13, `Split:`) |
| 011 | E1.F1.T3, E1.F1.T6 |
| 012 | E1.F2.T11 |
| 013 | E1.F2.T12 |
| 014 | E1.F3.T1, E1.F3.T4 |
| 015 | E1.F3.T2, E1.F3.T3 |
| 016 | E1.F3.T1, E1.F3.T4 |
| 017 | E1.F3.T5 |
| 018 | E1.F3.T7 |
| 019 | E1.F3.T8 |
| 020 | E1.F4.T1 |
| 021 | E1.F4.T4 |
| 022 | E1.F4.T6, E1.F4.T10, E1.F4.T11 |
| 023 | E1.F4.T3, E1.F4.T6 |
| 024 | E1.F4.T5 |
| 025 | E1.F4.T7 |
| 026 | E1.F4.T8 |
| 027 | E1.F4.T9 |
| 028 | E1.F5.T1 |
| 029 | E1.F5.T1, E1.F5.T2 |
| 030 | E1.F5.T5 |
| 031 | E1.F5.T3, E1.F5.T4 |
| 032 | E1.F5.T8 |
| 033 | E1.F5.T6 |
| 034 | E1.F5.T4, E1.F5.T7 |
| 035 | E1.F6.T1, E1.F6.T6 |
| 036 | E1.F6.T3, E1.F6.T6 |
| 037 | E1.F6.T6, E1.F6.T7 |
| 038 | E1.F6.T2 |
| 039 | E1.F6.T5, E1.F6.T6, E1.F6.T7 |
| 040 | E1.F7.T1, E1.F7.T3 |
| 041 | E1.F7.T1, E1.F7.T3 |
| 042 | E1.F7.T1, E1.F7.T4 |
| 043 | E1.F7.T2 |
| 044 | E1.F8.T1 |
| 045 | E1.F8.T3 |
| 046 | E1.F8.T4 |
| 047 | E1.F8.T3, E1.F8.T6 |
| 048 | E1.F8.T2 |
| 049 | E1.F9.T1 |
| 050 | E1.F9.T2 |
| 051 | E1.F9.T3 |
| 052 | E1.F9.T4 |
| 053 | E1.F10.T1 |
| 054 | E1.F10.T2 |
| 055 | E1.F10.T3 |
| 056 | E1.F10.T4 |
| 057 | E1.F10.T5 |
| 058 | E1.F10.T6 |
| 059 | E1.F10.T7 |
| 060 | E1.F10.T8 |
| 061 | E1.F11.T1, E1.F11.T6 |
| 062 | E1.F11.T3, E1.F11.T5, E1.F11.T6 |
| 063 | E1.F11.T2 |
| 064 | E1.F11.T7 |
| 065 | E1.F11.T6, E1.DEPLOY.T1 |
| 066 | E1.F12.T1, E1.F12.T3..E1.F12.T14 |
| 067 | E1.F12.T15 |
| 068 | E1.F12.T1 |
| 069 | E1.F12.T16 |
| 070 | E1.F12.T2, E1.F12.T17, E1.F12.T18 |
| 071 | E1.F1.T2, E1.F1.T4 |
| 072 | E1.F1.T2, E1.F1.T5 |
| 073 | E1.F11.T4, E1.F11.T6 |
| 074 | E1.F11.T4 |
| 075 | E1.F11.T4 |
| 076 | E1.F6.T4 |
| 077 | E1.F3.T6 |
| 078 | E1.F8.T5 |
| 079 | E1.F8.T5 |
| 080 | E1.F4.T2 |

**Coverage:** 80/80. No REQ-W3 is left without a task, and each sits in its own PLAN.md Feature (one `Split:`, E1.F2.T13). Every component of the architecture's file plan (§1.2) has a task: the four new scripts and `karvey-close.py`, the ten new `karvey_lib` modules, `leak_patterns.json`, the four new schemas, `check-modes.json`, both schemas, `karvey-state.py` (`effort`, `risk`, validate, `--fix`, archive), `karvey-context.py` (`--report`, `--portfolio`, `--backlog`, open-work, gate risks, layouts, settings line), `karvey-config.py`, `karvey-judges.py` / `judges.py`, `metrics.py`, `project.py`, `defaults.json`, `karvey-trace.py --wbs`, `lint-plugin.py` (L-55..L-75, L-11, L-32 extended), the statusline and session hooks, `templates/sponsor.html`, `rules/_core.md`, the adapters, the references, `rules/risks.md`, the design rubric, the §8 skill/rule texts, `docs/portability.md`, `docs/karvey.html`, `lint.yml`, the tests and manual scripts, and the dogfooding artifacts (§7.1, §7.3).

## Totals and critical path

- **Tasks:** 101, of which 1 `[human]` and 100 agent tasks (75 Backend, 16 Frontend, 1 Infra, 8 Test).
- **Total estimate:** 1,059 min ≈ 17.7 h of AI + review, calibrated. Per feature: F1 52 · F2 157 · F3 85 · F4 131 · F5 82 · F6 71 · F7 35 · F8 63 · F9 36 · F10 80 · F11 64 · F12 203.
- **Critical path by dependencies:** 242 min ≈ 4.0 h:
  E1.F3.T2 → E1.F3.T3 → E1.F3.T4 → E1.F3.T7 → E1.F8.T4 → E1.F8.T5 → E1.F2.T2 → E1.F2.T3 → E1.F2.T4 → E1.F2.T5 → E1.F2.T10 → E1.F2.T11 → E1.F2.T13 → E1.F11.T3 → E1.F11.T6 → E1.F11.T7 → E1.F12.T1 → E1.F12.T2 → E1.F12.T3 → E1.F12.T15 → E1.F12.T18 → [E1.DEPLOY.T1 human].
  The `[human]` wait and CI queue time are not counted.
- **Serial file spines** (not dependencies, but they serialise work): `docs/karvey.html` (16 tasks, 181 min), `lint-plugin.py` (24 tasks), `karvey-context.py` (12 tasks), `karvey-state.py` (11 tasks), `rules/gates.md` + `karvey-close.py` (4 tasks). With one agent the realistic wall time is the total; with parallel agents the floor is the critical path plus the method page spine, because the four translations share one file (≈ 242 + 144 − 36 ≈ 350 min).

## What proved impractical when breaking the architecture into tasks

1. **"Reorganise last" is a fan-in.** E1.F2.T2 depends on the last task of every feature F3..F10, so the whole of F2 waits for the slowest of them (F8 through the metrics of F3). The alternative — reorganising first — would restructure the same skills twice, which the PRD rules out.
2. **The method page is one file.** Four languages × three parts are twelve tasks on `docs/karvey.html`; they are (P) by dependency but serial in practice (one file, one region per commit). Splitting the page into per-language files would break the self-contained single file REQ-W3-068 and REQ-ADP-030 require.
3. **REQ-W3-010 is measured by F1's tool on F2's text.** It is the one `Split:` of the plan; the alternative (moving the compare tool into F2) would leave F1 unable to produce and check its own baseline.
4. **The gate-close script grows in three features** (F4 builds it, F5 adds the risk step, F2 the checkpoint step). Each step lands with the feature that owns its data, so every intermediate commit leaves a working close with fewer steps.
5. **This change is measured only from C-09 on.** Its requirements, mockup, design and architecture gates predate the effort record; they read `not measured (effort record did not exist)`, never zero (REQ-W3-074). The judge runs of this phase were recorded `estimated` by the Wave 2 tool (≈ 43k input tokens per lens) while the runtime reported ≈ 102k per lens — the gap REQ-W3-077 closes.
6. **Translation quality is not machine-checkable.** L-74 proves completeness, not correctness; risk R-8 carries it, and a reader's report goes through the `patch` lane after release.
7. **The production OK is the only `[human]` task.** It sits under `E1.DEPLOY`, not under a Feature — the WBS this change introduces (REQ-W3-041) applied to its own plan.

---
*Generated by `karvey-tasks` (PHASE 7) on 2026-09-26 for `wave3-optimization`. Not approved by this document.*
