# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/) + human/AI traceability (Karvey policy).

## [Unreleased]

### Added
- E1.F1.T1 — real hook payloads captured headless from CLI 2.1.281 into `plugins/karvey/tests/fixtures/payloads/` (9 sanitised fixtures); F-02 closed with a result per assumption A-1..A-10, A-8 nuance logged as F-04. Why: freeze the parser and guard tables on the real contract, not on docs.
- E1.F2.T1 — `karvey_lib` package: exit codes, `--json` envelope and `defaults.json` (8 h rotation, 120 min marker, 7 days stalled, ±30 % over 3 changes). Why: one contract and one place for the D-06/D-07 values (REQ-W1-049).
- E1.F2.T2 — `atomicio`: BOM-tolerant read, format-preserving atomic write, `O_EXCL` lock (stale after 30 s) and compare-and-swap (exit 3). Why: concurrent sessions must never half-write or silently overwrite a `spec.json`.
- E1.F2.T3 — `schema_lite`: stdlib JSON-Schema subset validator with `x-karvey-severity: warning` and `x-karvey-format: datetime-tz`; unsupported keywords are an error. Why: validate `spec.json`/`project.json` without pip dependencies (REQ-W1-002).
- E1.F2.T4 — `project` (root discovery bounded by the git top level, the active-change rule, the reviewed `origin/<production>` config read, state dir under `--git-common-dir`) and `audit` (JSONL, 0600, 1 MB rotation, no tokens). Why: hooks and tools must agree on which project and change they act on, and weakening settings must come from the reviewed line.
- E1.F2.T5 — `schemas/spec.schema.json` and `schemas/project.schema.json` (architecture §2.2/§2.6). Why: one machine-readable contract for both files, so validation, migration and the linter read the same rules (REQ-W1-002).
- E1.F2.T6 — `schemas/state-machine.json` (the phase graph as data) and `schemas/legacy-phase-map.json` (exact / proposed / unmappable tiers). Why: the tool, the rule text and the linter read one graph instead of 14 hand-kept phase lists (REQ-W1-005, REQ-W1-009).

- E1.F3.T1 — `karvey-state.py validate [PATH…|--all] [--strict] [--json]`: schema + §2.3 semantic checks (gates past unapproved phases, history gaps and order, embedded skips, legacy phase / history / `approvals: null` as warnings in advisory mode, errors in strict), exit 4 for a newer `schema_version`. Why: one validator every skill, hook and CI job calls (REQ-W1-001, REQ-W1-003, REQ-W1-109).
- E1.F3.T2 — `validate --fix [--dry-run] [--accept-proposed]`: exact-tier phases, proposed tier only with the flag, `gates_skipped` and embedded skips → `skipped`, `management` string/`none` and `clickup.backlog_list_id` → `management.location`, `approvals: null` → `{}`, hand-written `{from,to,at}` history normalised; the unified diff is printed first; unmappable (`shipping`, `iterate`, null) or unmigratable (`42`) values exit 3 and write nothing; idempotent. Why: migrate legacy files without inventing or flipping an approval (REQ-W1-009, REQ-W1-010).
### Fixed
- F-06/F-05 — a legacy date-only `approvals.*.date` is a warning in advisory mode (error in strict); `approvals.prod.date` stays strict; architecture §2.2 documents `maxLength`, the annotations and `schema.legacy`. Why: REQ-W1-003 says legacy shapes warn, and every existing `spec.json` holds date-only approvals.

## [3.11.4] - 2026-09-23 — hotfix

### Fixed
- **BUG-20 — false "NOT FOUND" drift for in-repo teams.** `state.json` writes `repos[].path` as the repo's name; with `team.json` inside that repo the hook resolved `<repo>/<repo>` and announced, on every session start, that the handoff described a tree that is not there. A path equal to the root's name, `.` or empty now resolves to the root.
- **BUG-21 — git worktrees reported as NOT FOUND.** The live-state check looked for a `.git/` directory; worktrees have a `.git` file. It now asks git (`rev-parse --git-dir`).

### Added
- Regression tests for both (test-hooks.sh 32 cases; 2 fail on 3.11.3). Verified read-only against paautin-kloketen: the section now compares for real and reports actual drift instead of NOT FOUND.

### Why
`agente-kloketen` verified 3.11.3 in its repo and found this residue of BUG-19 in the one section meant to detect real drift; a false alarm there on every start trains agents to ignore it. BUG-21 was found independently as finding F-01 of the `wave1-hardening` architecture and shares the same function. Knowledge sync deferred to the `wave1-hardening` archive.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5.5 (1M context)
> 🔗 Karvey phase: hotfix lane (BUG-20, BUG-21 + regression tests) · Apache 2.0

## [3.11.3] - 2026-09-23 — hotfix

### Fixed
- **BUG-18 — the SessionStart hook never ran, since 3.8.0.** `hooks.json` wrapped `${CLAUDE_PLUGIN_ROOT}` in single quotes; bash does not expand it and the CLI does not substitute it, so every session start failed with `No such file or directory` — no handoff reinjection, no drift check, no settings notice. Now double-quoted (the CLI's own guidance), and paths with spaces stay one word.
- **BUG-19 — `team.json` inside the repo resolved a profile that did not exist.** The hook built `<repo>/<ops_repo>/agents/<role>` while `karvey-checkpoint save` writes `docs/spec/agents/<role>/` and `docs/spec/board/<role>.md`. The hook now resolves both layouts (sibling ops repo, or the folder that holds `team.json`), looks the role up by the root's name when the session starts at the root, finds `manifest-compact` inside the profile, and says so when the profile or the handoff is missing. `karvey-checkpoint` and `rules/team.md` document both layouts.

### Added
- Regression tests in `plugins/karvey/hooks/tests/test-hooks.sh` (28 cases): the SessionStart `command` is now executed **exactly as declared in `hooks.json`** — the gap that let BUG-18 through — and the in-repo team layout. 5 of them fail on 3.11.2.

### Why
Reported by `agente-kloketen` (paautin-kloketen), relayed at the owner's request, both reproduced: its session started without identity and `/karvey-checkpoint restore` found no handoff. The 3.11.2 tests ran the script directly and never the declared command, so a quoting error that disabled the hook for every user since 3.8.0 went unseen. Bug-now protocol: hotfix. Knowledge sync (graphify) for this hotfix is deferred to the `wave1-hardening` archive, which moves graphify to archive only (REQ-W1-062).

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5.5 (1M context)
> 🔗 Karvey phase: hotfix lane (BUG-18, BUG-19 + regression tests) · Apache 2.0

## [3.11.2] - 2026-09-23 — hotfix

### Fixed
- **BUG-01 — `karvey-init --settings` created a phantom change and a real tracker Epic.** The settings step had no end: after asking the team settings the skill kept going through Step 1…9 (change-id, `spec.json`, `prd.md`, Epic in ClickUp/Jira…). New **Step 0 — settings-only mode**: it reads `project.json`, runs Step 3.2 with the current values pre-filled, merges the answers without dropping untouched keys, writes, reports and **stops**; it never creates a change or any tracker item.
- **BUG-02 — the session-hook settings notice fired where it should not.** It now appears only in a Karvey project (`docs/spec/project.json` or `docs/spec/changes/`) — not in a bare `docs/spec/` (OpenAPI, RFCs, studies) — checks the project root the hook already found instead of the nearest `docs/spec` (nested repos), treats a BOM, a non-object JSON and empty blocks correctly, no longer hangs on a relative `CLAUDE_PROJECT_DIR`, and is worded as information for the user ("settings only, creates nothing"), not as an order to the agent.
- **BUG-03 — an odd `resets_at` took the whole statusline down** (and with it the TIME TO ROTATE warning). The reset clock now accepts seconds, milliseconds and ISO strings, ignores NaN/inf/absurd/past values, and rounds the time left instead of truncating it. Applied to the plugin script and noted for hand-installed copies.
- **BUG-04 — the statusline debug copy was shared across OS users** (`/tmp/.karvey-statusline-last.json`, world-readable, exposing another user's session id). It is now per user and private: `$TMPDIR/.karvey-statusline-last.<uid>.json`, mode 600.

### Added
- **`plugins/karvey/hooks/tests/test-hooks.sh`** — regression tests for BUG-01…04 (21 cases). Passes 21/21 on this release and fails 15/21 against the 3.11.1 hooks (clean, isolated `TMPDIR`).
- **Retroactive QA of `team-adapters`** (`REVISION_PR_17-19_20260923.md`): NOT approved (open highs; security gate passes). Its remaining bugs are tracked as BUG-05+ in `docs/bugs_dev_testing.md` and fixed inside `wave1-hardening`.

### Why
The retroactive QA that the expert panel asked for (the change had reached prod without `approvals.qa`) found a live risk: the notice shown on every session in ~60 `docs/spec` folders recommended a command that could create junk Epics in a client's tracker. Following the bug-now / change-later protocol, the four defects with active impact ship as a hotfix; the structural fixes wait for Wave 1.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5.5 (1M context)
> 🔗 Karvey phase: hotfix lane (BUG-01…04 + regression test) from the retroactive QA of `team-adapters` · Apache 2.0

## [3.11.1] - 2026-09-23

### Fixed
- **`docs/karvey.html` picks the browser's language** on a first visit: order `?lang=` → saved choice → the browser's primary language (`navigator.languages[0]`) if it is `en/es/pt/de/zh` → English. A browser in French or Japanese gets English. Tested in 9 cases (explicit param, saved choice, `es-CL`, `pt-BR`, `zh-CN`, `de-AT`, unsupported language, empty, `localStorage` throwing).
- **The tab title follows the language** (`Karvey Method` · `Método Karvey` · `Karvey-Methode` · `Karvey 方法`) instead of staying in English — reported by the Mac review.
- **The hero's decorative wind lines no longer cross the figure cards** (32 / 13 / 22 / 1+2): the SVG now sits behind the content (`z-index`) — reported by the Mac review.

### Why
The real-browser review on the Mac found that the multilingual page still showed an English tab title in every language and that the hero decoration crossed the figures; the owner also asked for the browser's language to be picked on a first visit. (Section added in 3.11.2: the 3.11.1 entry shipped without its "Why", flagged by QA Dimension 6.)

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5.5 (1M context)
> 🔗 Karvey phase: change `team-adapters` iteration (QA findings on REQ-ADP-031, browser review) · Apache 2.0

## [3.11.0] - 2026-09-22

### Added
- **Visible version by environment** (`rules/versioning.md`, `karvey-deploy` 2.4-bis): a front shows the **dev version in DEV** — the bumped version as a semver pre-release + build metadata, `v3.10.1-dev.42+74571ae`, with a visible `DEV` mark — and the **release version in PROD**, clean `v3.10.1`. The version is read from the **version file** at build time, never from a pipeline variable (it goes stale silently: the label lies while the code is current); the pipeline stage only provides environment, build number and commit.
- **The canary checks the visible version** (`karvey-deploy` 2.7 / 2.11): DEV must show `-dev` of the version just bumped, PROD exactly the released one; a mismatch is a finding (stale build, wrong stage variable, wrong version source).
- **`docs/karvey.html` is multilingual** (REQ-ADP-031): **English by default** (what renders without JavaScript) with a switch to **Español · Português · Deutsch · 中文**, all in the same self-contained file; `?lang=xx` selects a language and the choice is remembered per browser. Ids are namespaced per language (`en-…`, `es-…`), filters and table-of-contents highlighting work per block, CJK font fallbacks for Chinese. New card on version bump + visible version, in every language. The version history now opens by explaining why it starts at 3.0.0: pure whim — Paáutin, HainTech's flagship software, was at version 3 when the plugin was built; there never was a 1.x or 2.x.

### Why
Owner feedback on 3.10.0: the page had to be consistently in English with a language switch, and the method's "show the version in the front" recommendation did not say that DEV and PROD must show different things — which is exactly how a stuck pipeline variable once made a production front display an old version while running new code.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5.5 (1M context)
> 🔗 Karvey phase: change `team-adapters` iteration 1 (spec revision REQ-ADP-031 + versioning rule) · Apache 2.0

## [3.10.0] - 2026-09-22

### Added — team settings on first use (`team-adapters`)
- **A plugin cannot run anything at install time**, so `karvey-init` now asks the team's settings **the first time Karvey is used** in a project (new Step 3.2) and stores them in `project.json`; `/karvey:karvey-init --settings` changes them later. The session hook prints a one-line reminder when a Karvey project (one with `docs/spec/`) lacks them — and stays silent everywhere else.
- **New rule `rules/notifications.md`** — the team's channel: `google-chat | slack | teams | email | webhook | none`, with `target`, `via` (`mcp | cli | webhook | api`) and `events` (`qa`, `deploy`, opt-in `incident`). Same content in each channel's own markup; unset or `none` → skipped **and said**; destinations are never read from a `CLAUDE.md` table; no webhook URL or token in the repo.
- **New rule `rules/management-adapters.md`** — the team's tracker: `clickup | jira | linear | azure-boards | github-projects | spreadsheet | markdown | other`, the logical operations (`create_epic`, `create_feature`, `create_task`, `set_status`, `comment`, `cascade`, `link`, `mirror_backlog`) and how each tool does them, and **5 logical states** — `todo · in_progress · review · done · blocked` — mapped to the team's real statuses in `project.json:management.statuses`.
- `karvey-context` shows the team settings (channel, tool, whether the statuses are mapped).
- **Statusline:** each account window now shows **when it resets and how long is left** — `5h 29% ↻18:05 (1h31m) · 7d 35% ↻Thu 21:20 (2d4h)` — from `rate_limits.*.resets_at`, which the CLI already provided and the script ignored; clock zone via `KARVEY_TZ`.
- **`docs/karvey.html`** — self-contained explainer complementary to the README: what the method is, the name (*Karvey* = **Afán**, Ona language of the Selknam people of Patagonia), and a map of the whole plugin.

### Changed
- **No skill assumes a tool or a status name any more.** ~20 skills and rules that branched on "ClickUp or Markdown" or wrote `listo! para pap` literally now use the logical operations/states; ClickUp commands survive only as the ClickUp adapter (`clickup-protocol.md`) or labeled examples. `karvey-qa` Step 4 notifies the configured channel instead of Google Chat via `CLAUDE.md`; `karvey-deploy` notifies the `deploy` event; `karvey-iterate` the opt-in `incident` event. `PLAN.md` gains the `👀 review` marker. Rule copies re-synced byte-identical.

### Compatibility
- `spec.json:management` still names the tool, so existing changes (`"clickup"`, `"markdown"`) stay valid. A project with only `"management": "clickup"` and no status map keeps working: the statuses are read from the list and the mapping is confirmed once. **HainTech repos must declare `notifications` (Google Chat) in their `project.json`** — until then QA skips the notice and says so.

### Repo maintenance (no plugin change)
- **`graphify-out/`** — knowledge graph of the method's own repo (82 files → 399 nodes, 753 edges, 21 communities), versioned with repo-relative paths; `.graphify_python` (machine-specific) is git-ignored. Closes backlog **BL-01**. It lives outside `plugins/karvey/`, so the installed plugin is unchanged and no version bump applies. README documents how to refresh it (`graphify . --update`).

### Why
A graphify review of the repo showed the "stack-agnostic" plugin hard-coded one team's tooling: QA always notified Google Chat through a HainTech `CLAUDE.md` table, and every status update used ClickUp with a HainTech status name. Another team hit steps that failed or did not apply. The owner asked for both to be asked when the plugin is first used, for any tool (Slack, Jira, a spreadsheet…). Backlog BL-02 and BL-03, promoted to `team-adapters`.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5.5 (1M context)
> 🔗 Karvey phase: change `team-adapters` (requirements → impl) · Apache 2.0

## [3.9.1] - 2026-09-22

### Fixed — documentation drift
- **Counts were wrong across the docs.** README said "12-phase pipeline" (it is **13 phases, 0–12**); `plugin.json` / `marketplace.json` said "16 support skills" (it is **18**); `plugins/karvey/README.md` said "12 phases + 12 support"; `rules/support-skills.md` said "12 pipeline phases". All corrected against the 32 skills actually shipped (1 orchestrator + 13 phases + 18 support).
- **`plugins/karvey/README.md` claimed no hook activates on install.** False since 3.8.0: the plugin registers a `SessionStart` hook. The README now separates the hooks **active on install** (session context, inert without a handoff; statusline installed by hand) from the **opt-in** enforcement hooks (`git-flow-guard`, `plan-gate`, via `karvey-guard`).
- **Orchestrator (`skills/karvey/SKILL.md`)** still described an 8-dimension QA and a deploy without PR gates or branch hygiene; now 9 dimensions (standards conformance), deploy phase with PR-gate verification, git-host detection and branch hygiene, and the features list includes branch hygiene. `deploy-workflow.md` is listed as applying to archive and context too.
- **`karvey-context` was missing from the support-skills catalog** (`rules/support-skills.md`) and from the README's support list.
- **Stale local copies of shared rules.** `karvey-init` and `karvey-tasks` carried an old `clickup-protocol.md` that still estimated in **hours** (the 3.4.0 minutes-based AI estimation never reached them), and `karvey-init` / `karvey-requirements` carried an old `living-specs.md` without `findings.md`, `backlog.md`, `incidents-index.md` or the 3.7 `spec.json` fields. Re-synced from `skills/karvey/rules/`; every local copy is now byte-identical to its canonical rule.
- `deploy-workflow.md` referenced `project.json:protected_branches`; the field lives in `branch_flow.protected_branches`.

### Added
- **Skills catalog** in the README: the 32 skills in tables — orchestrator, the 13 phases (what each produces + key rules) and the 18 support skills (role).
- **`docs/spec/backlog.md`** for the method's own repo, with **BL-01**: run graphify (`project.json:knowledge_sync`) over the repo once the pending changes land.

### Why
The owner asked whether the whole plugin documentation reflected what shipped. It did not: counts had drifted over several releases, one README described the hooks incorrectly, and three phase skills were reading outdated copies of shared rules — a silent behavior bug, not just a docs one.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5.5 (1M context)
> 🔗 Karvey phase: docs sync (karvey-docs scope) + rule-copy re-sync · Apache 2.0

## [3.9.0] - 2026-09-22

### Added — Branch hygiene (nothing left in branches)
- **New principle 7 + section *Branch hygiene* in `rules/deploy-workflow.md`.** Once a feature branch is absorbed into `{production}` (it already went through `{integration}`), it is deleted — remote and local — in the same deploy. **Absorption is verified, never assumed**: `git branch --merged` (merge commit / fast-forward), `git cherry` (cherry-pick / rebase) and a tree test with `git merge-tree --write-tree` (squash merges, which hide from the other two). Absorbed + open PR → the PR is closed naming what absorbed it. **A branch that is not absorbed is never deleted**: it is reported with its unique commits and PR, and the human decides (rescue / keep / discard). Rescued branches whose patches changed during conflict resolution are closed as *superseded by* the release, with the human's approval. Local deletion uses `git branch -d`, never `-D`, so git's refusal stays a signal. Counts are reported, never cleaned silently.
- **`karvey-deploy` step 2.12** — branch cleanup after the PROD merge and canary, extended to every non-protected branch of the repo; new hard rule and a `Branches:` line in the final output.
- **`karvey-archive` Step 7F — branch sweep**: the change is not closed while one of its branches is alive; the final output reports deleted / kept.
- **`karvey-context`** dashboard: new *LIVE BRANCHES* section (absorbed-but-alive vs carrying unreleased work).
- **`project.json:branch_flow.protected_branches`** (optional globs) — long-lived branches the cleanup never touches, besides `integration`/`production`.

### Added — Standards conformance in QA (rescued from PR #6, originally drafted as 3.6.0)
- **Dimension 9 — Standards conformance (golden path)** in `karvey-qa`. QA now verifies the diff against the engineering standards of the layers it touches (`standards/{layer}.md`), citing the concrete rule breached, and checks that **every departure has an approved entry in `deviations.md`**. A departure with no entry is a **High**, blocking finding; a gray zone the standard does not cover is Medium tagged `gray-zone` and escalates to design mode, never Critical by the reviewer's own reading. A standard in `draft` does not by itself produce Critical/High findings, and with no standards for the project the dimension is recorded as **not evaluated** — which is not the same as conformant. Wired into the review document, the pre-merge checklist and the `approvals.qa` gate.

#### Fixed
- `rules/engineering-standards.md` claimed that "`karvey-qa` (the **Consistency** dimension) checks conformance". It did not: Consistency measures coherence *internal* to the module (patterns, naming, duplication), not agreement with the documented standard. The rule now points at Dimension 9 and says so explicitly, and the conformance gate is described as **three** phases — design decides (`karvey-architecture`), implementation obeys (`karvey-impl`), **QA verifies** (`karvey-qa`) — with its own outcome table.

#### Why
`karvey-impl` already loaded the standards as a hard constraint and required a Deviation Request before departing from them, but **nothing ever verified that it happened**. The method only trusted: an implementation that skipped the golden path without raising the request reached production with no phase having checked. A gate that is never verified is not a gate. Surfaced while adding the same missing dimension to a team's own QA standard, where the identical hole existed.

### Added — PR gates + git host in deploy (rescued from PR #7, originally drafted as 3.7.0)
- **`karvey-deploy` verifies the PR's own gates before requesting the prod OK** (new step 2.9-bis). After opening the PR to `master` the skill retrieved nothing: it went straight to asking for approval. But the PR carries checks the repo enforces — CI and branch policies (build validation, required reviewers, status checks) — that are **not** the release gate of Step 0: they run on *this* PR over the *merge commit*, and fail for reasons the local pre-check cannot see (a conflict with what advanced on production, a policy added since). Now it retrieves them (`gh pr checks` / `az repos pr policy list`), **waits for them to settle** instead of reading the queued state as passed, and routes the outcome: green → continue; running → wait; red → **stop**, back to `karvey-iterate`; none configured → report that production has no gate. New hard rule: **never request the prod OK over a red or unresolved gate** — that turns the human into a rubber stamp, which is what the gate exists to prevent. Bypassing a policy stays the human's explicit decision, never the agent's initiative to unblock itself.
- **Git host detection** (new step 1.5-bis). The deploy platform and the git host are different things — a repo can deploy to Azure and live on GitHub. The skill hardcoded `gh pr create` / `gh pr merge`, so on Azure Repos or GitLab it failed at the worst moment: with the branch already merged into `dev`. It now resolves `project.json:git_platform` (falling back to detection from the remote, and the remote wins if the config is stale) and issues the right CLI: `gh pr` · `az repos pr` · `glab mr`.

#### Changed
- `rules/deploy-workflow.md`: gate verification added as principle 5 and as step 8 of the flow. `rules/project-config.md`: `git_platform` now also documents that it picks `karvey-deploy`'s PR CLI, not only the pipelines `karvey-infra` generates.

#### Why
The method took you to the door of production and never checked whether it opened. Everything a team places on the PR to protect `master` — tests, policies, reviewers — was invisible to the phase whose whole job is crossing that door.

### Why
Merged branches were piling up in the repos — four already-absorbed ones in this very repository, plus two open PRs whose work had never reached `main`. No phase of the method deleted anything after a merge, so cleanup depended on memory. A branch that outlives its merge reads as pending work, invites rebasing on stale code, and hides the branches that *do* carry unreleased work. The two stranded PRs (#6, #7) were rebuilt on top of 3.8 and shipped here instead of being discarded.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5.5 (1M context)
> 🔗 Karvey phase: method extension (deploy-workflow branch hygiene) + rescue of PRs #6/#7 · Apache 2.0

## [3.8.0] - 2026-09-22

### Added
- **The agent handoff, for one agent or many** — see the `karvey-checkpoint` entry below. Previously this lived outside the method, in a separate skill and one project's operations repo.
- **New shared rule `rules/team.md` — the OPTIONAL team layer.** Karvey carried the axis of the *work*; this adds the axis of the *worker*: roles, rotation, addressing, minimal communication and the shared-index trap. **It is opt-in and explicitly not the default**, and the rule opens with *When NOT to use a team*, written from a measured failure rather than from theory: 6 agents, 3 days, **≈US$1,000**, ending back on a single agent — because every hop between sessions is new context for the receiver, there is no shared cache, and at 588k a turn costs **7×** what it costs at 80k. A project that never writes `docs/spec/team.json` never sees this layer, and no phase or gate depends on it (team-layer).
- **New shared rule `rules/verification.md`** — the 18 failure modes that make a green report false, each one from a real incident: a citation is not the thing cited · exit 0 is not success · a green test over code nobody calls · "it failed" vs "it never ran" (the discriminator is duration) · a pipe whose first link fails silently returns a *false answer*, not an error · a filename does not identify a version · a versioned file does not prove what is applied · a switch is not a permission · merging onto someone else's file without bringing their branch reverts their fix **without a conflict** · a frozen baseline ages · sweeping by word leaves the promise intact. Registered for every phase close and shipped as a checklist by `karvey-guard --verify` (team-layer).
- **New skill `karvey-team`** (`init` · `census` · `relay` · `cost`) — sets up and runs a team of agent sessions, and **measures what it spends**. `init` shows the cost table and confirms before writing anything; `census` is an inventory that states in the file that it is **not** an address book; `relay` produces the list of sessions ready to rotate and stops there, because no agent can rotate another or itself; `cost` writes spend per agent against the single-agent counterfactual and **says so in the report** when the team is not paying for itself (team-layer).
- **New skill `karvey-decisions`** (`log` · `cross` · `show`) — one numbered, cross-cutting registry (`D-NN` business, `C-NN` direction) that changes cite via `spec.json:decisions`, so a decision taken in one change is visible to the next. Every entry carries **what it does NOT say**, the field that prevents over-applying a decision. **`cross` is mandatory before any deliverable claims to be blocked on a decision**: in the run behind this release, 14 items were escalated as blocked and **13 were already answered** (team-layer).
- **Plugin `hooks/`** — `hooks.json` with a `SessionStart` hook (`startup|resume|compact|clear`) that **brings the session back to being that agent**: it reinjects identity, manifest, board, checklist and handoff, then **measures** — comparing each repo's branch, last commit and uncommitted count against `state.json` and printing `matches` or `DRIFT — branch X -> Y` — and finally **instructs the session to run `/karvey-checkpoint restore` before anything else** when there is an active change, drift, or no handoff. A hook cannot invoke a skill, so it stops there: crossing decisions, recreating scheduled tasks and proposing the next step remain the skill's job, but the session now starts knowing it must ask, and which claims are already suspect. It resolves a single-agent profile (`docs/spec/agent/`) as well as a team, and **with neither it prints nothing and exits 0**. Plus `karvey-statusline.sh`, the rotation statusline (context, account limits, hours, cost, "TIME TO ROTATE"), which **a plugin cannot declare** — only `agent` and `subagentStatusLine` are accepted — so it ships with the three lines the user pastes once, documented rather than installed behind their back (team-layer).

### Changed
- **`karvey-checkpoint` now saves two faces instead of one, and the second one does not depend on having a team.** `save` keeps writing the change's checkpoint and **always** writes the agent's handoff: `docs/spec/agent/handoff.md` for a single agent, `{ops_repo}/agents/<role>/handoff.md` when a team is configured. A lone agent rotates too, and it is the case with the least safety net — nobody else holds the context. If no profile exists, the save **creates it** (manifest, board, checklist) instead of skipping the handoff. Beyond repository state, the handoff carries **who the agent is and what is not theirs, the standing rules referenced by commit rather than copied, the board of open items, and the closing checklist**. It is **produced, not composed**: its state section is command output, every "done" runs the check that measures it, and scheduled tasks are recorded with their full prompt because they die with a context reset in silence. `save` also writes **`state.json`**, the handoff's machine-readable twin. `restore` contrasts the handoff the same way it already contrasted git — **if the branch it declares no longer exists, it says so before anything in it is believed** — and crosses open questions against the decision log before repeating them (team-layer).
- **`karvey-guard` gains `--verify`**, a read-only checklist over `rules/verification.md` for any deliverable before it reports "done". It is a checklist, not a gate: it does not approve `karvey-qa` on its own (team-layer).
- **Orchestrator, support-skills catalog and README** updated with the two new skills, the two new rules and the optional team layer, stating in each place that **one agent is the default**.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5 (1M context) — as `agente-M5D-arquitecto`
> 🔗 Change: team-layer · Karvey phase: impl
> 📌 Origin: the proposal written on 2026-09-21 after running a 6-agent team on a real product, and the decision to keep teams available **as an option, never as an obligation**.

## [3.7.0] - 2026-09-18

### Added
- **New shared rule `rules/multi-agent.md`** — the minimum contract for work split across several agents and repos. Every cross-agent or cross-repo dependency becomes a pinned, verifiable reference in `spec.json`. Registered in the orchestrator's rules table.
- **Parent / child changes** (`spec.json:links.parent` / `links.children`, `"{change-id}@{repo}"`): a change that spans repos (web + app + DNS + cloud) has a parent in the operations repo and one child per repo. `karvey-init` asks for and fills both sides; the orchestrator shows the children's phases and closes the parent only when every child is deployed (#1).
- **Business decisions linked to changes** (`spec.json:decisions: ["D-NN@repo"]`): requirements cite the decision they come from, and contradicting a linked decision is a blocking review-gate failure in `karvey-requirements` (#2).
- **`[human]` tasks** in `karvey-tasks` with executor, exact command, read-only verification, rollback and an **Executed** record; new **`awaiting-human`** state in `karvey-impl` — the agent prepares and verifies, the human executes, only dependents wait (#3).
- **Pinned inputs from non-programmer agents** (`spec.json:inputs.design | design_system | copy | legal`, `"{repo} {path} @{commit}"`): read at the pinned commit by `karvey-requirements`, `karvey-design-graphic` and `karvey-impl`; input drift is routed by `karvey-iterate` as an automatic ripple candidate (#4, #11).
- **`approvals.prod = { by, date, ref: D-NN }`** — mandatory in `karvey-deploy` before the merge to the production branch, committed in the repo, never delegated to an agent. Keeps the prod approval in git history where the platform cannot enforce required reviewers (#5).
- **Change type `ops`** (`spec.json:type`) for changes without application code (IAM, DNS, secrets, console config): lite requirements → command plan in `karvey-infra` (Step 5-bis) → `[human]`/`[Infra]` tasks → execution → verification → archive (#6).
- **Hotfix lane** (`type: "hotfix"`) in `karvey-iterate` and `karvey-deploy`: **fix + `BUG-NN` + regression test in the same PR**, each chained same-day hotfix its own release, recorded in `revision_history` with `bug` and `release`; an interrupted production E2E run is re-run in full after the hotfix (#7, #13).
- **Documentation-only PR lane** in `karvey-deploy` Step 0-bis + `deploy-workflow.md`: light CI (spec lint) instead of build/test/deploy, merger declared in `project.json:docs_pr.merged_by`, never triggers a deploy (#8).
- **Method readiness checks in `karvey-health`** (Step 6, separate from the 0–10 code score): Karvey skills installed in the agent's environment at the expected `project.json:karvey_version`, with install instructions per environment (#9); every `inputs.* @commit`, `links` and `decisions` reference exists, and drift of the source repo is flagged (#11).
- **IAM binding verification as an infrastructure test**: `karvey-infra` requires a versioned, idempotent script for human-executed IAM plus a read-only `.verify.sh` that asserts the binding itself (member · role · resource); `karvey-test` Step 4-bis runs it and records it in `test_evidence.md` (#12).

### Changed
- **Approvals record who and where** (`approvals.<phase>.by`, `role: human | ceo-delegate`, `date`, `ref: D-NN`) — applied at every gate through `phase-close.md` and `karvey-requirements` (#10).
- `spec.json` schema (`living-specs.md`, `karvey-init`) gains `type`, `links`, `decisions`, `inputs`, `approvals.prod`; `project.json` (`project-config.md`) gains optional `ops_repo`, `karvey_version`, `docs_pr`.
- Orchestrator: "Method directory structure" documents where parent changes and the decision log live and the cross-repo reference formats; the status view shows type, links, decisions, inputs, `awaiting-human` tasks and prod approval; routing notes for `ops`, `hotfix` and parent changes.
- `enforcement.md`: a note — **outside the method** — on approval markers with expiry in the user's own hooks (how a human delegates approvals to a coordinating agent or extends a marker is the user's environment, not Karvey) (#14).

### Why
A real project ran with **four specialist agents in four repos** (designer, web, app, operations), **a browser-operator agent**, and **a human who runs the IAM** grants the agents must not run. Audit D-47 found the code itself in good shape — every web change had its test in CI — but the method had no place for what crossed agent and repo boundaries: a change spanning web + app + DNS + cloud had no parent; business decisions (`D-NN`) were not linked to requirements; design, copy and legal arrived as "the latest file" instead of a pinned commit; human-executed steps lived in chat; prod approvals were not recorded in the repo (no GitHub Enterprise to enforce reviewers); chained same-day hotfixes and a hotfix during a production E2E run had no lane; docs-only PRs had no defined CI or merger; and one agent environment did not even have the skills installed. The records drifted as a result (`revision_history` stopped at 1.0.9, ripple out of date). This release makes each of those dependencies an explicit, verifiable field.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5
> 🔗 Karvey phase: method refinement (multi-agent/multi-repo) · Apache 2.0

## [3.6.0] - 2026-09-08

### Added
- **Causal discipline in `karvey-investigate`** — the skill went from 6 steps to 9, with three new ones placed *before* reading any code:
  - **Step 1 now dates the symptom.** The report timestamp and, where possible, the first occurrence, define the **incident window**. Without it the following steps are inert.
  - **New Step 2 — check what is already known:** incident tracker (`docs/bugs_dev_testing.md` / `incidents-index.md`), engineering standards for the layer, and the `CHANGELOG.md` of the window. The team's accumulated knowledge is evidence, not background reading.
  - **New Step 3 — "what CHANGED?" before "what is WRONG?":** for a new symptom the causal question is historical. Inspect the window with `CHANGELOG`, `git log` / `git log -S`, merges to deploy branches, **and non-code changes** — configuration, CSP/security headers, secrets and rotations, infra, flags, provider or quota changes.
  - **New Step 7 — causal-coherence gate:** a cause that predates the incident window cannot explain a symptom that started inside it. A pre-existing finding is **latent fragility, not the cause**; the investigation continues until the trigger appears. The report must label each finding as *cause* or *contributing fragility*.
- **Trace across repo boundaries** (Step 4): follow the path into the component that holds the next hop. If a repo is out of reach, say so and name what you would inspect — never silently downgrade the conclusion to what happened to be reachable.
- **"Never state what a symbol does without opening it"** (Step 6): project-local helpers, wrappers and loggers behave by project decision, not language default. Claims that depend on them are cited by file and line or they are not evidence.
- **Reuse before invention** (Step 9): before recommending retry/backoff, reconnection or degraded-state indicators, check whether a sibling module already implements it, and cite that as the pattern.
- Three new hard **Constraints**: no undated investigation, no pre-existing finding reported as the cause of a new symptom, no claim about a symbol without having read its definition.

### Why
Post-mortem of a real investigation: an engineer correctly found a fragile reconnection path in a frontend and reported it as the root cause of an incident reported that week. Their own evidence said the code had been unchanged since the first commit — which refuted the causal claim, and went unnoticed. The actual cause was a security header (CSP) put in enforce six days earlier, visible in the `CHANGELOG` and in `git log`, and the decisive corroborating detail lived in a **different repo** (a token TTL). Three of the four gaps were method, not skill: nobody dated the incident, nobody asked what changed, and a pre-existing finding was allowed to stand as a cause. The fourth — asserting a project-local `logger.error` was a no-op without opening it — is now a constraint.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 5
> 🔗 Karvey phase: skill refinement (investigate → causal discipline) · Apache 2.0

## [3.5.0] - 2026-07-05

### Added
- **Visual components catalog** in `karvey-design-graphic` (new Step 9B → `design-components.md`): the design-graphic phase now produces, besides the token-level `design-spec.md`, an **art brief per component** for illustrators / AI art agents. It is **derived exhaustively** from the approved `mockup.html` + `design-spec.md` + requirements (nothing invented, nothing omitted), with a mandatory template: cross-cutting base (style, palette hex light+dark, character/brand, asset format @1x/2x/3x + safe zone), Screens table, Modals/bottom-sheets table, UI components (per component: description · states · required background/fill art), Push notifications table, an optional section per additional surface, and a prioritized deliverable list (1 base illustration + state variants, light+dark, safe zone). **Target-agnostic** per `rules/targets.md` — the component inventory adapts to the declared target(s) (mobile/web/CLI/…), it does not assume web. The knowledge-sync step (renamed 9C) and the phase Output now include `design-components.md`; the orchestrator's PHASE 4 description was updated accordingly.

### Why
Working with designers or illustration agents needs a document that lists **all** visual components (screens, modals, notifications, buttons, inputs, chips, cards, tiles, avatars, bars, badges, bottom-nav, maps, states) with description, states, and a per-component art/background brief in light and dark with a safe zone for text. `design-spec.md` stops at token level and did not fill that gap. Calibrated against a real hand-made catalog (Paáutin wisn mascotas).

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: skill refinement (design-graphic → design-components deliverable) · Apache 2.0

## [3.4.0] - 2026-06-23

### Added
- **AI-time estimation in `clickup-protocol.md`**: estimates are expressed in **minutes** (AI execution + human review), not human coding hours. Typical task 10–30 min, **cap ~60 min → split if it exceeds**. Added a per-work-type reference table (SP/endpoint/service/UI/parser/test) and Feature/Epic aggregation. The legacy "6-hour rule" is reframed: it assumed human time; under AI-driven dev the effective cap is ~60 min.

### Why
Reconciliation of the team's `GESTION_PROYECTOS_IA` governance doc into Karvey: that doc was the Paáutin-specific, prior form of the same method (its ClickUp folder is literally "Dev Sprints Metodo Karvey"). The clickup-protocol already covered WBS/naming/dependencies/status; the missing piece was the AI-time estimation model. Project-specific bits (2026 sprint calendar, workspace IDs, client tags) go to the team's `paautin-standards`, not here.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: rule refinement (clickup-protocol estimation) · Apache 2.0

## [3.3.0] - 2026-06-23

### Added
- **Engineering Standards layer** (`rules/engineering-standards.md`): a third source of truth beside living specs and `project.json` — the **golden paths** ("how we build here") per layer/target, living in `docs/spec/standards/` (`db.md`, `backend.md`, `frontend.md`, `_index.md`). Fixed file structure (Golden path · MUST · MUST NOT · Gray zones · Migration `current`/`target`) so they are consumed as hard constraints, not prose.
- **Conformance gate (design mode)** in `karvey-architecture` (new Step 4B) and `karvey-impl` (Step 4 execution rules): both load the relevant standards as a **hard input** and validate against them. Conforms → proceed citing the standard; gray zone / outside the standard → **Deviation Request** asked to the user in design mode (never resolved silently); MUST/MUST NOT violation without justification → blocked.
- **`deviations.md`** per change: approved departures from a standard, with rationale + human/AI traceability. Recurring deviations feed back into the standard at `karvey-archive` (mirrors the spec-gap → requirements loop).
- **`karvey-standards`** support skill: lifts the team's engineering golden paths (db/backend/frontend…) from the **real system** into the team's standards repo, in the standard template format. Discovery subagents per layer, picks a golden path where repos diverge, marks undefined things as gray zones, human-approved, re-runnable (`--refresh` promotes recurring deviations into the standard). Registered in the orchestrator + support-skills rule.
- **Method/standards separation (two planes):** the public plugin stays generic and **never** holds a team's concrete standards; those live in the team's own repo. `project.json:standards` gains `source: "local" | "git"` (+ `repo`/`ref`/`path`) so standards can live in a **separate private repo** (e.g. Azure DevOps) that the team installs, read via a cached checkout (`.karvey/standards/`).
- **`project.json:standards`** field (`source`/`dir`/`repo`/`ref`/`path`/`by_layer`) so phases know which standard to load; fallback chain to `_index.md` and, failing that, to "no standard found → ask".
- Migration support as a first-class concept (`Status: migrating`, `current` vs `target`) — covers the frontend v2→v3 case: new work MUST use `target`, touching `current` is a deviation.
- Optional `standards-guard` enforcement hook (opt-in) and registration of the rule in the orchestrator (rules table + `docs/spec/` structure).

### Why
Closed a real blind spot: the method specified *what* to build (living specs) but had no canonical place for *how* to build it per layer, so `architecture`/`impl` drifted on tribal knowledge. Now the pipeline stays inside the house style and, when something must go outside it, it asks in design mode instead of deciding alone — while keeping the generic method and each team's private standards cleanly decoupled.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: method extension (rules + architecture/impl gate) · Apache 2.0

## [3.2.0] - 2026-06-17

### Added — Iteration loop (Karvey becomes a spiral, not a line)
- **`karvey-iterate`** support skill: the iteration engine. Reads the change's `findings.md` inbox and routes each finding to its feedback edge — `bug` → incident tracker + QA micro-loop · `spec-gap` → re-open `requirements` (rippling only the affected phases) · `emergent` → discovery backlog. The single place loop logic lives; phase skills only observe/classify.
- **`rules/iteration-loop.md`**: the three feedback edges, the `findings.md` triage artifact, the spec-revision sub-cycle, and the convergence gate (a change is done only when no open `bug`/`spec-gap` remains and all `emergent` are captured).
- **`rules/incident-tracking.md`**: a dedicated `BUG-NN` incident tracker (`docs/bugs_dev_testing.md` per repo + global `incidents-index.md`) with a **state-history** machine (DETECTADO → DIAGNOSTICADO → EN FIX → RESUELTO → REABIERTO). Complementary to ClickUp; integrates with `karvey-investigate` and regression tests.
- **`rules/backlog.md`**: a **dual** discovery backlog — `docs/spec/backlog.md` (source of truth) mirrored into the ClickUp `backlog_list_id`. Swept at archive to promote emergent items into new change-ids (`seed_backlog_id`).
- **`rules/phase-close.md`**: a **mandatory** phase-close ritual (comment + status + cascade on ClickUp/PLAN.md, findings/backlog sweep, spec.json + knowledge update) at the end of every phase and every task — fixes stale ClickUp tasks by making the update a numbered step, not a "should".

### Changed
- **`karvey-mockup`**: navigable depth 3 → **3–4 levels** (sub-flows/states where spec-gaps hide) + a **spec↔mockup validation** pass (Step 4C) to catch spec defects before design/architecture/impl.
- **`karvey-test`**: writes classified findings to `findings.md`, logs bugs to the `BUG-NN` tracker, and routes via `karvey-iterate` (Step 5B/5C/5D).
- **`karvey-qa`**: classifies findings (bug/spec-gap/emergent), routes via `karvey-iterate`, convergence gate before deploy (Step 3E/3F).
- **`karvey-impl`**: per-task completion is now the explicit per-task phase-close ritual.
- **`karvey-archive`**: discovery-backlog sweep (Step 7E) that promotes emergent work into future change-ids.
- **`karvey-browse`**: surfaced defects/gaps are recorded as classified findings.
- **Orchestrator + `living-specs.md`**: state machine gains the feedback edges and convergence gate; `spec.json` gains `iteration_count`, `revision_history`, `seed_backlog_id` and explicit `infra`/`qa`/`deploy` approvals; directory structure adds `findings.md`, `backlog.md`, `incidents-index.md`.
- **`clickup-protocol.md`**: ClickUp updates declared mandatory (phase-close), phase-level status mapping, incident/backlog mirroring.
- Support layer now **14** skills (adds `karvey-iterate`).

### Why
Karvey was a waterfall with a single QA micro-loop: findings that were really spec defects had no edge back to `requirements`, and post-cycle discoveries stayed "in the air". ClickUp updates were documented as a "should" and got skipped, leaving tasks stale, and bugs had no dedicated incremental tracker with history. This release makes the method guide **iteration** itself — close the feedback loops, track incidents with state history, capture emergent work, and enforce the close ritual — so nothing gets dropped.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8 (1M context)
> 🔗 Karvey phase: method evolution (iteration loop + incident tracking + backlog + phase-close) · Apache 2.0

## [3.1.0] - 2026-06-14

### Added
- **`karvey-import`** support skill: converts existing **Kiro** (`.kiro/specs/*` + steering) and **gstack** specs into Karvey's `docs/spec/` structure (prd.md, requirements.md, architecture.md, tasks.md, spec.json/project.json). Non-destructive on the source; missing Karvey-required sections become `> TODO` placeholders; all gates imported as not-approved for re-validation. Registered in the orchestrator, support-skills rule and coverage table.

### Why
Let teams already using Kiro or gstack adopt Karvey without rewriting their existing specs by hand.

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: support skill addition · Apache 2.0

## [3.0.0] - 2026-06-14

### Added
- Initial publication of the **Karvey** Method as a Claude Code plugin/marketplace.
- 12-phase pipeline (0–12): grill, init, requirements, mockup, design-graphic, architecture, **infra**, tasks, impl, test, qa, **deploy**, archive.
- Cross-cutting layer of 12 support skills: investigate, second-opinion, health, browse, checkpoint, diagram, docs, guard, devex, retro, scrape, benchmark-models.
- Stack agnosticism (`targets`), PRD base, traceable EARS, blocking security gate (OWASP+STRIDE), ordered deployment with canary, semver versioning, optional hook-based enforcement (git-flow + plan-gate), persistent `goal` field.
- Shared rules: project-config, knowledge-sync, targets, deploy-workflow, changelog-policy, versioning, enforcement, support-skills (+ the previous ones).
- Apache 2.0 license, NOTICE and TRADEMARK.md ("Karvey" trademark = *Afán*, Selknam).
- Skill bodies authored in English with bilingual triggers; generated artifacts follow the project's language.

### Why
Formalize Karvey as HainTech's own stack-agnostic method, absorbing the value of Kiro and gstack, installable/versionable as a plugin (no manual copying of skills).

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: initial publication · Apache 2.0
