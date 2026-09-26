# Findings: team-adapters

Retroactive QA, 2026-09-23, range `ffb6df9..e3bc6f3` (PRs #17-#19, 3.10.0 -> 3.11.1). Review document:
`qa/REVISION_PR_17-19_20260923.md` (in this change; moved from the repo root by wave1-hardening E1.F12.T12).

Source ids: `S-NN` = D1 security, `E-NN` = D2 code errors, `C-NN` = D3 consistency, `I-NN` = D4 impact,
`N-NN` = D7 second opinion (intra-model fallback), `D6` = versioning (reviewed by the orchestrator).
Findings were deduplicated across dimensions: one row per real problem, with every source id listed.

Routing (`rules/iteration-loop.md`):
- `bug` -> incident `BUG-NN` in `docs/bugs_dev_testing.md` -> fixed in `wave1-hardening` (BUG-01..04 already fixed by hotfix 3.11.2).
- `spec-gap` -> re-open requirements; the amendment is handled inside the `wave1-hardening` change (team-adapters is already released, so its REQ-ADP-* are amended there, with a ripple set).
- `emergent` -> discovery backlog (`docs/spec/backlog.md`).

| # | Date | Source phase | Type | Severity | Title | Status | Routed to |
|---|------|--------------|------|----------|-------|--------|-----------|
| F-01 | 2026-09-23 | qa (D7) | bug | high | `karvey-init --settings` does not stop after Step 3.2: phantom change + real tracker Epic | closed | BUG-01 (RESUELTO, hotfix 3.11.2) |
| F-02 | 2026-09-23 | qa (D1, D2, D4, D7) | bug | medium | Session-hook settings nudge: wrong scope, wrong project.json, fragile parsing, hang, imperative wording | closed | BUG-02 (RESUELTO, hotfix 3.11.2) |
| F-03 | 2026-09-23 | qa (D1, D2, D4) | bug | medium | An odd `resets_at` takes the whole statusline down; time left truncated | closed | BUG-03 (RESUELTO, hotfix 3.11.2) |
| F-04 | 2026-09-23 | qa (D1) | bug | medium | Statusline debug copy at a fixed, shared, world-readable /tmp path | closed | BUG-04 (RESUELTO, hotfix 3.11.2) |
| F-05 | 2026-09-23 | qa (D4, D7) | spec-gap | high | "Missing status map -> read, confirm once" exists only in the rule; tasks/impl/qa/deploy/iterate lack it | routed | spec revision REQ-ADP-022 in wave1-hardening |
| F-06 | 2026-09-23 | qa (D3, D4, D7) | spec-gap | high | No skill moves Tasks/Features to `done`; PLAN.md rows stay `review` forever | routed | spec revision REQ-ADP-021 in wave1-hardening |
| F-07 | 2026-09-23 | qa (D7) | bug | high | impl decides dependencies and resume with non-logical states (`pending`, `completed`): deadlock risk | routed | BUG-05 |
| F-08 | 2026-09-23 | qa (D3, D4) | bug | high | `project.json:management` already exists as a string in 16 repos; the `!= markdown` guard sends Markdown repos to a tracker | routed | BUG-06 |
| F-09 | 2026-09-23 | qa (D3) | bug | medium | README and plugin.json still describe ClickUp as the tracker | routed | BUG-07 |
| F-10 | 2026-09-23 | qa (D1) | spec-gap | medium | `project.json` values (`target`, `location`, status names) interpolated into `via: cli` shell commands with no validation | routed | spec revision REQ-ADP-010/020 in wave1-hardening |
| F-11 | 2026-09-23 | qa (D4, D7) | spec-gap | medium | Notifications rollout: 20 of 22 HainTech repos go silent; the migration aid conflicts with REQ-ADP-012 as written | routed | spec revision REQ-ADP-012 in wave1-hardening |
| F-12 | 2026-09-23 | qa (D7) | spec-gap | medium | "Confirm once" has no path when no human can be asked (subagents, headless) | routed | spec revision REQ-ADP-022 in wave1-hardening |
| F-13 | 2026-09-23 | qa (D7) | spec-gap | medium | "Once" means once per checkout: settings written to the working copy with no branch/lane | routed | spec revision REQ-ADP-001/022 in wave1-hardening |
| F-14 | 2026-09-23 | qa (D7) | spec-gap | medium | One `statuses` map per project cannot represent per-list / per-workflow states or missing states | routed | spec revision REQ-ADP-022 in wave1-hardening |
| F-15 | 2026-09-23 | qa (D3, D7) | spec-gap | medium | No single resolution order for tracker settings (tool, location) between project.json and spec.json | routed | spec revision REQ-ADP-023 in wave1-hardening |
| F-16 | 2026-09-23 | qa (D7) | spec-gap | medium | Tracker down mid-phase: the fallback to PLAN.md is never reconciled | routed | spec revision (management-adapters rule 4) in wave1-hardening |
| F-17 | 2026-09-23 | qa (D7) | spec-gap | medium | No create operation is idempotent: every re-run duplicates tracker items | routed | spec revision (management-adapters operations) in wave1-hardening |
| F-18 | 2026-09-23 | qa (D3) | spec-gap | medium | Epic cascade target contradicts itself (`review` vs `done`) | routed | spec revision REQ-ADP-021 in wave1-hardening |
| F-19 | 2026-09-23 | qa (D3) | spec-gap | medium | `awaiting-human` / 🙋 is a sixth marker missing from every marker list | routed | spec revision REQ-ADP-021 in wave1-hardening |
| F-20 | 2026-09-23 | qa (D4, D7) | spec-gap | medium | Canary visible-version check: one rigid DEV format, contradicts 2.4-bis, false positives with several changes in dev | routed | spec revision (versioning.md, deploy 2.7) in wave1-hardening |
| F-21 | 2026-09-23 | qa (D4) | emergent | medium | Team settings are not validated (keys, enums); Tarien already drifted | routed | backlog BL-38 |
| F-22 | 2026-09-23 | qa (D1, D2) | bug | low | Invalid `KARVEY_TZ` silently falls back to the system zone | routed | BUG-08 |
| F-23 | 2026-09-23 | qa (D2) | bug | low | Stray separator when only the 7-day window is present | routed | BUG-09 |
| F-24 | 2026-09-23 | qa (D1, D2) | bug | low | `docs/karvey.html`: a malformed hash throws `URIError` before the switcher binds | routed | BUG-10 |
| F-25 | 2026-09-23 | qa (D2) | bug | low | An invalid `?lang=` saves the browser language as the viewer's choice | routed | BUG-11 |
| F-26 | 2026-09-23 | qa (D2) | bug | low | Switching language drops the other query parameters | routed | BUG-12 |
| F-27 | 2026-09-23 | qa (D2) | bug | low | No `hashchange` handling on the method page | routed | BUG-13 |
| F-28 | 2026-09-23 | qa (D7) | bug | low | Without JS the language switch is shown but does nothing | routed | BUG-14 |
| F-29 | 2026-09-23 | qa (D3) | bug | low | `clickup-sync-guard` hook referenced, but nothing installs it | routed | BUG-15 |
| F-30 | 2026-09-23 | qa (D2, D3) | bug | low | hooks/README still says the session hook prints nothing without team/agent files | routed | BUG-16 |
| F-31 | 2026-09-23 | qa (D3, D6) | bug | low | 3.11.1 release docs incomplete: CHANGELOG entry without "Why"; page history stops at 3.11.0 | routed | BUG-17 (EN FIX: fixed in 3.11.2, no regression check yet) |
| F-32 | 2026-09-23 | qa (D1, D7) | spec-gap | low | The notification destination can be redirected by whoever writes `project.json` | routed | spec revision REQ-ADP-011 in wave1-hardening |
| F-33 | 2026-09-23 | qa (D1) | spec-gap | low | QA notifications carry security findings to a team channel with no redaction rule | routed | spec revision REQ-ADP-011 in wave1-hardening |
| F-34 | 2026-09-23 | qa (D1, D2, D4, D7) | spec-gap | low | REQ-ADP-003 text no longer matches the fixed nudge (marker, degraded mode, `{}`, startup-only) | routed | spec revision REQ-ADP-003 in wave1-hardening |
| F-35 | 2026-09-23 | qa (D2) | spec-gap | low | A shared `?lang=` link overwrites the viewer's saved language | routed | spec revision REQ-ADP-031 in wave1-hardening |
| F-36 | 2026-09-23 | qa (D3) | spec-gap | low | The `clickup` ids block is undocumented in management-adapters; no key for task ids | routed | spec revision REQ-ADP-023 in wave1-hardening |
| F-37 | 2026-09-23 | qa (D3) | spec-gap | low | phase-close says "every phase", but only 3 phase skills cite it | routed | spec revision (phase-close.md) in wave1-hardening |
| F-38 | 2026-09-23 | qa (D3) | spec-gap | low | QA Dimension 6 does not verify what versioning.md says it verifies | routed | spec revision (versioning.md, karvey-qa D6) in wave1-hardening |
| F-39 | 2026-09-23 | qa (D3, D4) | spec-gap | low | karvey-init contradicts itself around Step 3.2; no persisted "not now" answer | routed | spec revision REQ-ADP-001/002 in wave1-hardening |
| F-40 | 2026-09-23 | qa (D4) | spec-gap | low | `spec.json:management = "none"` exists in 9 files and is not in the enum | routed | spec revision REQ-ADP-020/023 in wave1-hardening |
| F-41 | 2026-09-23 | qa (D4) | spec-gap | low | No setting holds the team's sprint folder/iteration | routed | spec revision REQ-ADP-020 in wave1-hardening |
| F-42 | 2026-09-23 | qa (D3) | emergent | low | Documentation drift: rule-citation tables, per-phase rule lists, status notations, command spellings | routed | backlog BL-39 |
| F-43 | 2026-09-23 | qa (D3) | emergent | low | When the version bump happens: per task/commit (impl) vs per deploy | routed | backlog BL-07 (existing, promoted to wave1-hardening) |
| F-44 | 2026-09-23 | qa (D3) | emergent | low | Local rule copies reference sibling rules that do not exist next to them | routed | backlog BL-10 (existing, promoted to wave1-hardening) |
| F-45 | 2026-09-23 | qa (D4) | emergent | low | Karvey repos with specs under `spec/` (not `docs/spec/`) get no nudge | routed | backlog BL-40 |
| F-46 | 2026-09-23 | qa (D4) | emergent | low | The statusline is 34 chars longer; the rotate warning moves to column 158 | routed | backlog BL-41 |
| F-47 | 2026-09-23 | qa (D4) | emergent | low | 12 of the 59 anchors published in 3.10.0 no longer resolve | routed | backlog BL-42 |
| F-48 | 2026-09-23 | qa (D7) | emergent | low | Notifications have no deduplication across micro-loop runs and deploy retries | routed | backlog BL-43 |

Totals: 48 findings. bug 17 (high 3, medium 4, low 10), spec-gap 23 (high 2, medium 11, low 10),
emergent 8 (medium 1, low 7). Critical: 0. Closed: 4 (F-01..F-04). Open high: F-05, F-06, F-07, F-08.

## Rating adjustments and re-typing (deduplication decisions)

| Finding | Source ratings | Consolidated | Why |
|---|---|---|---|
| F-03 | S-03 low, E-01 medium, I-07 medium | medium | Agreed with D7: one decorative field removed the context, limits and rotate readout. |
| F-06 | C-02 medium, I-12 low | high | Agreed with D7: without a `done` step, impl's dependency rule becomes ambiguous (F-07 / N-08). Kept separate from F-07: F-06 is missing spec (who moves leaves to `done`), F-07 is skill text that violates REQ-ADP-021 as written. |
| F-07 | N-08 "major" | high | Raised together with F-06: a literal reading ("dependency completed" = `done`) never starts a dependent task. |
| F-08 | I-02 high, C-03 medium | high | Kept high only for the `!= markdown` guard, which is true on a string and routes 15 Markdown repos to a tracker. The re-asking part alone would be low. C-03 absorbed. |
| F-11 | I-06 high (emergent) | medium, spec-gap | Agreed with D7: it is what REQ-ADP-011/012 require, i.e. a rollout/migration risk, not a defect against the spec. Re-typed to spec-gap because its fix (pre-filling from the CLAUDE.md space table) needs REQ-ADP-012 amended (N-14 merged here). |
| F-10 / F-32 | S-01 medium | split: medium + low | Agreed with D7: redirecting the QA summary adds little marginal risk (whoever writes `project.json` already controls the repo's CI and skills), so low. Interpolating values into shell commands with `via: cli` stays medium. |
| F-12, F-13 | N-02, N-03 typed emergent | spec-gap | Disagreement with D7: the reviewer itself marks REQ-ADP-022 FAIL because of them. A requirement this change owns that fails in practice is not "a different change"; by the litmus test it is a spec-gap. |
| F-17 | N-05 typed bug | spec-gap | Disagreement with D7: no requirement asks for find-or-create; the skills do what the spec says. "If we had specified idempotency, impl would differ" -> spec-gap. Severity kept medium. |
| F-01 | N-01 blocker, N-09 major | high | N-09 (re-running `--settings` overwrites the blocks) merged into F-01: the same Step 0 fix (pre-fill current values, merge by key, stop) closes both. |
| F-02 | S-06/E-10/I-04, S-05/E-07, E-02, E-08, E-09, E-11, E-12, E-13, N-11 | medium | The code side is fixed by BUG-02. The requirement-text side (REQ-ADP-003 still says "has docs/spec/") and the parts not fixed in code (startup-only emission, walk up to `/`) stay open as F-34. The README part of E-12 stays open as F-30. |
| F-20 | I-10 medium, N-10 minor | medium | Merged: same step (deploy 2.7), same fix direction. |
| F-43, F-44 | C-16, C-19 | low | Routed to existing backlog items (BL-07, BL-10) already promoted to wave1-hardening, instead of opening duplicates. |

## F-01 — `karvey-init --settings` does not stop after Step 3.2
- **Type:** bug · **Severity:** high · **Source:** D7 N-01 (blocker), N-09
- **Detail:** the skill was a linear sequence 1->10 and `--settings` was only mentioned inside Step 3.2, so an agent kept going: change-id, `docs/spec/changes/...`, `spec.json`, `prd.md` and a real Epic in the team's tracker. The session hook recommended exactly that command in ~60 `docs/spec` folders. Re-running it also overwrote both blocks without pre-filling or merging (N-09).
- **Routed to:** BUG-01 -> fixed in hotfix 3.11.2 (Step 0 "settings-only mode — STOP"). RESUELTO.

## F-02 — Session-hook settings nudge
- **Type:** bug · **Severity:** medium · **Source:** S-06 = E-10 = I-04, S-05 = E-07, E-02, E-08, E-09, E-11, E-12 (script header), E-13, N-11 (wording)
- **Detail:** fired on any `docs/spec/` (60 of 64 folders measured, most not Karvey); read the nearest `docs/spec` instead of the resolved root in nested layouts; a BOM made the file "unreadable"; a non-object JSON or a missing python3 suppressed it; empty blocks counted as configured; a relative `CLAUDE_PROJECT_DIR` hung the hook; the text read as an order to the agent.
- **Routed to:** BUG-02 -> fixed in hotfix 3.11.2. RESUELTO. Spec side -> F-34.

## F-03 — An odd `resets_at` takes the statusline down
- **Type:** bug · **Severity:** medium · **Source:** S-03 = E-01 = I-07, E-03, E-04
- **Detail:** `float(ts)` / `fromtimestamp` were outside any `try`: milliseconds, ISO strings, NaN, 1e400 and lists all printed `karvey statusline down`. Past or sub-minute resets showed a stale clock and `(0m)`; the countdown truncated (`4h59m` for 5 h).
- **Routed to:** BUG-03 -> fixed in hotfix 3.11.2. RESUELTO.

## F-04 — Statusline debug copy shared across OS users
- **Type:** bug · **Severity:** medium · **Source:** S-02 (pre-existing; reproduced live: the file was owned by another OS user, mode 664, exposing that user's session metadata)
- **Routed to:** BUG-04 -> fixed in hotfix 3.11.2 (`$TMPDIR/.karvey-statusline-last.<uid>.json`, umask 077). RESUELTO.

## F-05 — The missing-map path exists only in the rule
- **Type:** spec-gap · **Severity:** high · **Source:** I-01 (confirmed and widened by D7)
- **Detail:** `management-adapters.md` "Missing map" is reached only from phase-close and archive. tasks 6A, impl Step 3, qa 3A, deploy Step 5, iterate 3a.5 and init Step 4 call `create_task` / `set_status` with no such clause. No skill says which list to read the statuses from when `management.location` is missing. The CHANGELOG 3.10.0 claim overstates it.
- **Routed to:** re-open REQ-ADP-022 inside wave1-hardening: one shared resolution clause, cited by every skill that changes a status, applied before the first status change.

## F-06 — No skill moves leaf items to `done`
- **Type:** spec-gap · **Severity:** high · **Source:** C-02 ≈ I-12
- **Detail:** impl leaves tasks at `review` "until validated by test/qa", but neither test nor qa has a `set_status(..., done)`. Only `[Deploy]` items and the Epic reach `done`. 35 existing PLAN.md files use the old labels, so the vocabulary is now mixed.
- **Routed to:** re-open REQ-ADP-021 inside wave1-hardening: define who flips `review -> done` (test/qa convergence or an archive cascade) and list it under `set_status` "Used by".

## F-07 — impl dependencies and resume in non-logical states
- **Type:** bug · **Severity:** high · **Source:** N-08
- **Detail:** `karvey-impl/SKILL.md:31,35-37` ("first pending task", "until its dependent [DB] is completed") while tasks now end at `review` (F-06). Read as `done`, no [Backend] task ever starts. An orphan `in_progress` after a crash is neither pending nor completed. The source of truth for resuming (tracker, PLAN.md, tasks.md) is not stated. This violates REQ-ADP-021 as written.
- **Routed to:** BUG-05.

## F-08 — `project.json:management` string collision
- **Type:** bug · **Severity:** high · **Source:** I-02, C-03
- **Detail:** 16 HainTech `project.json` files carry `"management": "markdown"` or `"clickup"` (added ad hoc before 3.10). The new schema reuses the key as an object. `iterate:61` and `backlog.md:10` guard with "`management.tool` != markdown", which is true on a string, so Markdown repos are sent to "create/link the item in the tracker". The rule's compatibility example describes a state `project.json` never had.
- **Routed to:** BUG-06.

## F-09 — README and plugin.json still say ClickUp
- **Type:** bug · **Severity:** medium · **Source:** C-05, C-06
- **Detail:** README:52,117,118,119 and plugin.json:4 ("discovery backlog (Markdown + ClickUp)") contradict README:95-99 and the rules. plugin.json is the text shown in the plugin listing.
- **Routed to:** BUG-07.

## F-10 — `project.json` values into shell commands
- **Type:** spec-gap · **Severity:** medium · **Source:** S-01 (command-injection half)
- **Detail:** with `via: cli` the agent builds `curl`, `az boards` or `gh project item-edit` commands that interpolate `target`, `location` and status names. No rule says to validate them per channel, refuse shell metacharacters, pass them as quoted arguments, or confine a `spreadsheet` path to the repo.
- **Routed to:** re-open REQ-ADP-010/020 inside wave1-hardening: a "Validation" rule in notifications.md and management-adapters.md.

## F-11 — Notifications rollout and REQ-ADP-012
- **Type:** spec-gap · **Severity:** medium · **Source:** I-06, N-14
- **Detail:** 20 of 22 primary HainTech Karvey repos stop posting QA/deploy notices (they relied on the CLAUDE.md space table). The CHANGELOG gives no snippet or repo->space map, and the new `deploy` event is on by default. The natural migration aid (propose a space seen in context, persist it after confirmation) is forbidden by REQ-ADP-012 as written.
- **Routed to:** amend REQ-ADP-012 inside wave1-hardening ("SHALL NOT use at send time a destination that is not in project.json; MAY propose one in Step 3.2, persisted only after explicit confirmation"), then the per-repo migration as docs PRs, plus a CHANGELOG compatibility line.

## F-12 — "Confirm once" without a human
- **Type:** spec-gap · **Severity:** medium · **Source:** N-02 (re-typed from emergent)
- **Routed to:** REQ-ADP-022 amendment: resolve the map as a precondition of the tasks gate; with no human available, never persist a mapping; subagents never write `project.json`.

## F-13 — Settings written per checkout
- **Type:** spec-gap · **Severity:** medium · **Source:** N-03 (re-typed from emergent)
- **Routed to:** REQ-ADP-001/022 amendment: settings travel as a docs change through the `docs_pr` lane (or a feature-branch commit with a merge notice); hook and skills check `origin/{integration}` before declaring "missing".

## F-14 — One status map per project
- **Type:** spec-gap · **Severity:** medium · **Source:** N-06
- **Routed to:** REQ-ADP-022 amendment: per-level / per-list maps, `null` = unsupported, re-map a single entry when a mapped status disappears, never create or edit the team's workflow states.

## F-15 — No single resolution order for tracker settings
- **Type:** spec-gap · **Severity:** medium · **Source:** C-04, N-07
- **Detail:** `backlog_list_id` lives in project.json, spec.json and init with a different precedence per tool; the per-change override offered by init is honoured only by deploy, which then uses the project's location and statuses.
- **Routed to:** REQ-ADP-023 amendment: one resolution order in management-adapters.md (`spec.json` override {tool, location, statuses} -> `project.json:management`), cited by every skill.

## F-16 — Tracker fallback is never reconciled
- **Type:** spec-gap · **Severity:** medium · **Source:** N-04
- **Routed to:** management-adapters amendment: a `tracker_pending` outbox retried at the next phase-close and shown by karvey-context; no `create_task` under an empty parent.

## F-17 — Create operations are not idempotent
- **Type:** spec-gap · **Severity:** medium · **Source:** N-05 (re-typed from bug)
- **Routed to:** management-adapters amendment: find-or-create by natural key (`E{n}.F{n}.T{n}`, `F-NN`/`BUG-NN`, `[Deploy] {change-id}@{version}`), ids stored in spec.json (see F-36).

## F-18 — Epic cascade contradiction
- **Type:** spec-gap · **Severity:** medium · **Source:** C-01
- **Routed to:** REQ-ADP-021 amendment: one cascade in management-adapters.md (Features `review` -> Epic `review` at impl; Epic `done` only at archive), cited by phase-close.

## F-19 — `awaiting-human` marker
- **Type:** spec-gap · **Severity:** medium · **Source:** C-07
- **Routed to:** REQ-ADP-021 amendment: declare 🙋 a qualifier (a tag, not a state), pick its logical state (recommended `blocked`), add it to the legends.

## F-20 — Canary visible-version check
- **Type:** spec-gap · **Severity:** medium · **Source:** I-10, N-10
- **Detail:** front-vue-paautin-1 labels DEV as `DEV 2.10.4` (it meets the intent, not the format) and would raise a blocking finding on every DEV canary; 2.4-bis says "recommend" while 2.7 says "finding"; with two changes in `dev`, the first one's canary flags the second one's bump.
- **Routed to:** versioning.md / deploy 2.7 amendment: accept "bumped version + unmistakable DEV mark", compare against the version file of the deployed commit, not visible = recommendation. Related: BL-26 (Wave 2 canary).

## F-21 — Team settings are not validated
- **Type:** emergent · **Severity:** medium · **Source:** I-03
- **Detail:** Tarien stores `status_flow` instead of `statuses` and `google_chat` instead of `google-chat`; the hook only checks `isinstance(dict)`.
- **Routed to:** backlog BL-38 (can reuse `project.schema.json` from BL-04). Fixing Tarien's own `project.json` belongs to Tarien's repo.

## F-22 — An invalid `KARVEY_TZ` is silent
- **Type:** bug · **Severity:** low · **Source:** S-04 = E-05 · **Routed to:** BUG-08.

## F-23 — Stray separator with only the 7-day window
- **Type:** bug · **Severity:** low · **Source:** E-06 · **Routed to:** BUG-09.

## F-24 — A malformed hash aborts the page script
- **Type:** bug · **Severity:** low · **Source:** S-07 = E-15 · **Routed to:** BUG-10.

## F-25 — An invalid `?lang=` is remembered
- **Type:** bug · **Severity:** low · **Source:** E-14 · **Routed to:** BUG-11.

## F-26 — The language switch drops query parameters
- **Type:** bug · **Severity:** low · **Source:** E-16 · **Routed to:** BUG-12.

## F-27 — No `hashchange` handling
- **Type:** bug · **Severity:** low · **Source:** E-18 · **Routed to:** BUG-13.

## F-28 — The language switch is inert without JS
- **Type:** bug · **Severity:** low · **Source:** N-12 · **Routed to:** BUG-14.

## F-29 — Phantom `clickup-sync-guard` hook
- **Type:** bug · **Severity:** low · **Source:** C-10 · **Routed to:** BUG-15.

## F-30 — hooks/README out of date on the nudge
- **Type:** bug · **Severity:** low · **Source:** C-18, E-12 (README part; the script header part was fixed by BUG-02) · **Routed to:** BUG-16.

## F-31 — 3.11.1 release docs incomplete
- **Type:** bug · **Severity:** low · **Source:** D6 (CHANGELOG 3.11.1 without "Why", policy `changelog-policy.md`), C-21 (page history stops at 3.11.0 on a page stamped v3.11.1)
- **Routed to:** BUG-17. Both parts are already fixed in the 3.11.2 working tree (CHANGELOG "Why" added with a note; 3.11.1 and 3.11.2 entries added to the page history in the 5 languages). It stays EN FIX because there is no automated check yet (planned with the CI linter, BL-10).

## F-32 — The notification destination can be redirected
- **Type:** spec-gap · **Severity:** low · **Source:** S-01 (redirection half)
- **Routed to:** REQ-ADP-011 amendment: validate `target` per channel, refuse `://` in `target`, show and confirm the destination when `project.json` changed since the last send.

## F-33 — Security findings in team notifications
- **Type:** spec-gap · **Severity:** low · **Source:** S-08
- **Routed to:** REQ-ADP-011 amendment: the `qa` event sends counts per severity + a link by default (`notifications.detail: counts | full`).

## F-34 — REQ-ADP-003 text vs the fixed nudge
- **Type:** spec-gap · **Severity:** low · **Source:** S-06, E-10, I-04 (spec side), E-09, E-11, N-11 (residual)
- **Detail:** REQ-ADP-003 still defines a Karvey project as "has `docs/spec/`". The degraded behaviour without python3 and the meaning of `{}` are now decided in code but not in the requirement. Still open in code: the notice is emitted on `resume|compact|clear` too, sits next to "First action", and the walk goes up to `/` instead of stopping at the git top level.
- **Routed to:** REQ-ADP-003 amendment inside wave1-hardening (marker definition, degraded mode, `{}`, startup-only, stop at the git top level).

## F-35 — A shared `?lang=` overwrites the saved language
- **Type:** spec-gap · **Severity:** low · **Source:** E-17 · **Routed to:** REQ-ADP-031 amendment (one-off vs saved choice; `zh-TW` / `zh-HK`).

## F-36 — Tracker ids block undocumented
- **Type:** spec-gap · **Severity:** low · **Source:** C-09 · **Routed to:** REQ-ADP-023 amendment (document the historical `clickup` block in management-adapters; add `task_ids` or write them to tasks.md).

## F-37 — phase-close cited by only 3 phase skills
- **Type:** spec-gap · **Severity:** low · **Source:** C-11 · **Routed to:** phase-close.md amendment (add the step to the 9 skills or narrow the rule's scope).

## F-38 — D6 does not check versioning.md
- **Type:** spec-gap · **Severity:** low · **Source:** C-15 · **Routed to:** karvey-qa D6 amendment (front reads the version file; DEV `-dev.N+sha` / PROD clean).

## F-39 — karvey-init inconsistencies around Step 3.2
- **Type:** spec-gap · **Severity:** low · **Source:** C-20 ≈ I-14
- **Detail:** Step 3 "don't ask anything again" vs Step 3.2 asking; Spreadsheet Epic `todo` vs PLAN.md Epic `in_progress`; Step 10 lacks the `Settings:` line; no persisted "not now" answer.
- **Routed to:** REQ-ADP-001/002 amendment.

## F-40 — `management = "none"` not in the enum
- **Type:** spec-gap · **Severity:** low · **Source:** I-11 · **Routed to:** REQ-ADP-020/023 amendment (legacy alias).

## F-41 — No sprint folder setting
- **Type:** spec-gap · **Severity:** low · **Source:** I-13 · **Routed to:** REQ-ADP-020 amendment (optional `management.sprints`).

## F-42 — Documentation drift in tables and spellings
- **Type:** emergent · **Severity:** low · **Source:** C-08, C-12, C-13, C-14, C-17
- **Routed to:** backlog BL-39 (generate the "Applies in" / "Used by" columns and per-phase rule lists from actual citations; one spelling `/karvey:karvey-init --settings`; one status notation). Complements BL-10.

## F-43 — Version bump timing
- **Type:** emergent · **Severity:** low · **Source:** C-16 · **Routed to:** backlog BL-07 (existing, promoted to wave1-hardening).

## F-44 — Local rule copies with dangling sibling references
- **Type:** emergent · **Severity:** low · **Source:** C-19 · **Routed to:** backlog BL-10 (existing, promoted to wave1-hardening: no copies, resolvable paths).

## F-45 — `spec/` layouts get no nudge
- **Type:** emergent · **Severity:** low · **Source:** I-05 · **Routed to:** backlog BL-40.

## F-46 — A longer statusline pushes the rotate warning right
- **Type:** emergent · **Severity:** low · **Source:** I-08 · **Routed to:** backlog BL-41.

## F-47 — Old page anchors no longer resolve
- **Type:** emergent · **Severity:** low · **Source:** I-09 · **Routed to:** backlog BL-42.

## F-48 — Notifications without deduplication
- **Type:** emergent · **Severity:** low · **Source:** N-13 · **Routed to:** backlog BL-43.
