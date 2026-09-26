---
name: karvey-health
description: Karvey support — 0-10 code health score (types, lint, tests, dead code) plus method readiness (python3, skills, pinned inputs) — before a phase or periodically. Triggers include "karvey health", "salud del código karvey".
allowed-tools: Read, Write, Bash, Glob, Grep
argument-hint: [<repo or path>]
---

# karvey-health — Code quality dashboard

A **cross-cutting** skill of the Karvey Method. It is a **support layer, NOT a phase**: it can be invoked at any point in the cycle and **does NOT modify** `spec.json:phase` nor advance the method. Inspired by gstack's `/health`.

## Purpose

Deliver a **continuous and comparable code-health metric** per repo: a single 0–10 score that summarizes the state of the type checker, the linter, the tests and dead-code detection, together with its **trend over time** and prioritized recommendations to raise the score.

The goal is that anyone on the team can ask "how is the repo's health?" and get an objective, repeatable answer that is comparable across runs.

## When it is used

- On demand (`karvey health`).
- As a support check before or after any phase (requirements, design, implementation, test, deploy), without altering the phase state.
- In any repo, **stack-agnostic**.

## Steps

### 1. Detect the stack and the available tools

Inspect the repo (or the path from the `[<repo or path>]` argument; if none is passed, use the current repo) to identify language, package manager and the available quality tools. **Stack-agnostic** — detect by configuration files and manifests, do not assume a language:

- **Type checker**: `tsc`/TypeScript (`tsconfig.json`), `mypy`/`pyright` (Python), `go vet`/compiler (Go), `flow`, etc.
- **Linter**: `eslint`, `biome`, `ruff`/`flake8`/`pylint` (Python), `golangci-lint`, `clippy` (Rust), etc.
- **Test runner**: `vitest`/`jest` (JS/TS), `pytest` (Python), `go test`, `cargo test`, etc.
- **Dead-code detector**: `knip`/`ts-prune` (JS/TS), `vulture` (Python), `deadcode`/`staticcheck` (Go), `cargo-udeps` (Rust), etc.

Record which tools actually exist. A missing tool **does not penalize** the score: it is excluded and its weight is redistributed among the available dimensions.

### 2. Run the tools

Run each available tool in non-destructive mode (read/analysis only, no auto-fix), capturing:

- **Type checker**: number of type errors.
- **Linter**: number of errors and warnings.
- **Tests**: passed/failed and, if available, coverage.
- **Dead-code**: count of unused symbols/exports/files.

Use reasonable timeouts and degrade gracefully: if a tool fails due to configuration (not due to the code), mark it as "not assessable" and exclude it from the computation instead of assigning 0.

### 3. Compute a weighted 0–10 score

The score is computed by a script, never by hand, so two runs over the same results give the same number. Write the raw results to a temporary JSON (`types.errors`, `lint.errors_per_kloc` / `warnings_per_kloc`, `tests.passed` / `failed` / `coverage_pct`, `deadcode.items`; leave a dimension out when it had no tool) and run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-health-score.py" --inputs "$TMP/health-inputs.json" --json
```

Relay its score, band, sub-scores and effective weights. The report time uses `KARVEY_TZ`; an invalid zone is reported as `fallback zone: …`, never silently. The table below is what the script implements (`defaults.json:health_weights`):

Each dimension produces a 0–10 sub-score. Default weights (adjustable according to the tools present):

| Dimension        | Weight | Sub-score 10 when… |
|------------------|------|----------------------|
| Type checker     | 0.30 | 0 type errors   |
| Tests            | 0.30 | 100% pass (bonus for coverage) |
| Linter           | 0.25 | 0 errors; warnings discount little |
| Dead-code        | 0.15 | 0 dead code      |

`score_global = Σ (sub_score_i × weight_i) / Σ available_weights`, rounded to 1 decimal.

If a dimension has no tool, its weight is distributed proportionally among the others (renormalize). Document in the report which effective weights were used.

Interpretation bands: **9–10** excellent · **7–8.9** healthy · **5–6.9** attention · **<5** critical.

### 4. Record the result for trend tracking

Save a **small history** (append-only) of the score and its breakdown, to be able to compare across runs. Preferred location, in order:

1. `docs/spec/health-history.json` (or `.jsonl`) inside the repo, if the method's `docs/spec/` structure exists.
2. Otherwise, a repo metrics file: `.karvey/health-history.jsonl`.

Each record includes: timestamp (the script's `at`, in `KARVEY_TZ`), global score, sub-scores per dimension, raw counts (type errors, lint errors/warnings, tests pass/fail, coverage, dead-code), commit/branch if available, and the effective weights used. Append, never overwrite, to preserve the historical series.

### 5. Report score + breakdown + trend + recommendations

Deliver a clear dashboard:

- **Global score 0–10** with its interpretation band.
- **Breakdown per dimension**: sub-score, effective weight and raw count.
- **Trend**: comparison against the previous run (score Δ) and a mini-series of the last N records (arrow ↑/↓/→).
- **Prioritized recommendations**: the highest-impact actions first (e.g. "resolving 12 type errors raises the score ~1.2 pts"), ordered by expected gain vs. effort.

### 6. Method readiness checks (multi-agent / multi-repo)

Reported in a separate **Method readiness** block; they do **not** change the 0–10 code score. See `../karvey/rules/multi-agent.md` §3 and §9.

**6a. The method's runtime.** `python3 --version` must report ≥ 3.9 (the state tool, the hooks'
dispatcher and the linter need it). Missing or older → **FAIL**: without it the hooks run only their bash
fail modes and no phase write can go through `karvey-state.py`.

**6b. Karvey skills installed in this agent's environment.** Each agent (lab server, laptop, CI runner, remote sandbox) must be able to load the method:
- Look for the skills where the harness loads them — the plugin install (e.g. `~/.claude/plugins/marketplaces/*/plugins/karvey/`) or user/project skill folders (`~/.claude/skills/karvey*`, `.claude/skills/karvey*`) — and read the installed version from its `plugin.json`.
- **Loaded vs available:** a running session keeps the plugin version it loaded at start. Report it with
  `cd "${CLAUDE_PLUGIN_ROOT}/scripts" && python3 -m karvey_lib.runtime` — it reads the runtime's installed-plugins
  record read-only and prints `loaded X, available Y` (a difference → update the plugin and start a new session) or
  `loaded version unknown` when there is no record; never guess the loaded version from the files on disk.
- Compare with the version the project expects (`project.json:karvey_version`, if declared) and verify the skills the project's changes will need are present (at least `karvey`, the phase skills in use, and `karvey-iterate`).
- Missing or outdated → **FAIL** with the install/update instructions **for this environment** (plugin marketplace install/update for Claude Code; copying the `${CLAUDE_PLUGIN_ROOT}/skills/` folder for harnesses without plugins; re-starting the agent session so the skills load). Never report a phase as runnable in an environment where its skill is not installed.

**6c. Pinned inputs still exist and are current.** For every active change (`docs/spec/changes/*/spec.json`) and every `inputs.*` entry (`"{repo} {path} @{commit}"`), plus `links.parent`/`links.children` and `decisions`:
- The repo is reachable, the commit exists (`git -C {repo} cat-file -e {commit}`) and the path exists at that commit (`git -C {repo} cat-file -e {commit}:{path}`). Missing → **FAIL** (the pin is broken; the change is reading something that cannot be reproduced).
- The source advanced: `git -C {repo} log --oneline {commit}..origin/{default-branch} -- {path}` not empty → **WARN · input drift**, listing the new commits. Recommend `/karvey-iterate {change-id}` (input-drift routing).
- Linked parent/children changes and `D-NN` decisions exist in their repos → otherwise **WARN**.
- If a repo is out of reach, say so and name it — never report the check as passed.

This check can also run in CI (read-only) so drift is flagged on every PR.

## Multi-repo

If a `project.json` with a `repos` list exists, run the evaluation **for each repo** and deliver:

- A dashboard per repo (score, breakdown, trend, recommendations).
- A **consolidated project summary**: average (or weighted) of scores, repos in the critical band highlighted first, and aggregate trend.

Keep an independent history per repo (step 4) so the trends do not get mixed.

## Limits

- It does **NOT** advance or modify the phase: it does not touch `spec.json:phase`.
- It does **NOT** apply auto-fix nor modify code: it is only measurement and reporting. It does not re-pin inputs or install skills — it reports and gives the instructions.
- It is not a phase of the method; it is a support layer invocable at any time.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
