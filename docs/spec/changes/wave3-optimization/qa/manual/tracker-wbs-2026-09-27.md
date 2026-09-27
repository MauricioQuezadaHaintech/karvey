# Manual run: tracker-wbs — 2026-09-27

- **Script:** `plugins/karvey/tests/manual/tracker-wbs.md` (REQ-W3-040, REQ-W3-041, REQ-W3-042)
- **Run by:** the maintainer agent, headless (`claude -p` with the branch plugin, `--setting-sources project,local`),
  one fresh session per step, owner-authorised pattern (D-19, D-21, D-28). Markdown tracker only.
- **Setup:** a throw-away repo under the scratch dir (`git init -b main` + a bare origin); `project.json` with
  `management.tool: markdown`, `notifications.channel: none`; change `sample-wbs` (lane `standard`) with an
  approved architecture naming two functional areas, *Sign-in* and *Reports*, and REQ-WBS-004 (an audit line)
  belonging to both. Between steps the setup moved the state forward by hand (tasks/impl/test approved before step
  2; `qa` approved before step 4) and a feature branch carried a small report module with a string-built SQL query so
  the review had a High finding.
- **Overall verdict:** **PASS** on the rerun (BUG-97, BUG-98 fixed): step 2 PASS, step 4 PASS (twice), every-step line PASS; step 1 re-passed; step 3 passed in the first run.
- **First run:** FAIL (step 1 PASS; step 2 FAIL; step 3 PASS; step 4 FAIL; the "every step" line FAIL).

## Step 1 — "Generate the tasks of sample-wbs."

| Expected | Observed | Verdict |
|---|---|---|
| one `### Feature` per functional area, none named after a phase | `### Feature E1.F1: Sign-in`, `### Feature E1.F2: Reports (depends E1.F1)` | PASS |
| phases as a checklist on the Epic | `Phases: [x] init · [x] requirements · [-] mockup · … · [ ] archive` under `## Epic E1` | PASS |
| the shared requirement carries a `Split:` line in the later Feature | `tasks.md`, Feature E1.F2: `Split: REQ-WBS-004 — the audit writer (C-04) is shared and built in E1.F1; …` | PASS |
| `karvey-trace.py sample-wbs --wbs` → `0 issue(s)` | `13 task(s) under 2 Feature(s) + E1.QA, E1.DEPLOY · 0 issue(s)` | PASS |

The tasks step also wrote empty `### Epic item E1.QA` and `### Epic item E1.DEPLOY` sections under the Epic.

## Step 2 — "Run QA on sample-wbs." (one High finding)

| Expected | Observed | Verdict |
|---|---|---|
| the QA item is `E1.QA` under the Epic (an `### Epic item E1.QA` section) with the High finding's fix task as its child, not at the root | the review found 2 Critical + 4 High. `PLAN.md` gained a **new root-level `## QA Review — E1.QA (…)` section** after `## History`, with the fix tasks `E1.QA.1 … E1.QA.6` as **table rows**; the existing `### Epic item E1.QA` section under the Epic stayed empty | **FAIL** |

## Step 3 — "Run QA on sample-wbs again." (same findings open)

| Expected | Observed | Verdict |
|---|---|---|
| `E1.QA` found and reused; exactly one QA section, no second QA item | the step-2 `## QA Review — E1.QA` section was reused (one history row, one new fix row `E1.QA.7`); `diff` of `PLAN.md` step 2 → 3 shows no new QA section. The two E1.QA headings created in steps 1–2 remain | PASS (the duplication comes from step 2) |

## Step 4 — "Prepare the deploy of sample-wbs." (stop before any push)

| Expected | Observed | Verdict |
|---|---|---|
| deploy record `E1.DEPLOY` under the Epic with `[Deploy] sample-wbs@{version}` as its child | the agent correctly refused to deploy (release gate `fail`: no CHANGELOG, the QA reviews still failing — it did not trust the hand-set `qa` approval). It wrote a **new root-level `## Deploy — sample-wbs (E1.DEPLOY, …)` section** with tables; **no `[Deploy] sample-wbs@…` item** and nothing under `### Epic item E1.DEPLOY`. Nothing pushed | **FAIL** |
| a second run of step 4 finds it and creates nothing new | — | not run: the record's shape already failed; rerun after the fix |

## Every step — `karvey-trace.py sample-wbs --wbs`

| Expected | Observed | Verdict |
|---|---|---|
| no `legacy shape` and no `outside the hierarchy` line | `0 issue(s)` after every step, **including after steps 2 and 4** where QA fix tasks and the deploy record sit in root-level sections outside the Epic items | **FAIL** (the check does not see them) |

## Defects (plugin)

**D3 — QA and deploy write their items outside the Epic on the Markdown tracker.** `skills/karvey-qa/SKILL.md:259`
says "Find or create the QA item `E{n}.QA` under the change's Epic", and `rules/management-adapters.md:104-106` says
the same for `E{n}.DEPLOY`, but neither states the Markdown shape: fill the existing `### Epic item E{n}.QA` /
`### Epic item E{n}.DEPLOY` section with checkbox children (`- [ ] E1.QA.1 …`, `- [ ] [Deploy] {change}@{version}`).
The agent created its own root-level sections instead. Proposed fix: a sentence in the Markdown adapter
(`rules/adapters/markdown.md`) and in the qa/deploy skills naming that shape; lint the guard phrase.

**D4 — `karvey-trace.py --wbs` misses those items.** `plugins/karvey/scripts/karvey-trace.py` `wbs_plan` (lines
505-535) inspects only checkbox list items and resets the section on any `## ` heading, so table rows under a
root-level `## QA Review — E1.QA` or `## Deploy — … (E1.DEPLOY …)` heading, and a second section carrying the same
`E{n}.QA` key, pass as `0 issue(s)`. Proposed fix: report a heading outside `### Epic item E{n}.QA|DEPLOY` that
carries `E{n}.QA`/`E{n}.DEPLOY`/`QA Review`/`Deploy` as `outside the hierarchy`, and a key present in two sections as
`duplicate`. Regression test idea (`test_wbs.py`): the step-2/step-4 `PLAN.md` shapes above → one
`outside the hierarchy` line each.

## Rerun after the fixes (2026-09-27)

Fresh throw-away repo (Markdown tracker, lane `standard`, architecture with the areas *Sign-in* and *Reports* and a
shared audit requirement). Step 1 was re-run by the agent (`### Feature E1.F1: Sign-in`, `### Feature E1.F2:
Reports`, empty `### Epic item E1.QA` / `E1.DEPLOY`; `--wbs` 0 issues). The setup then moved the state to test and
added a feature branch with a string-built SQL query, as in the first run.

| Expected | Observed | Verdict |
|---|---|---|
| step 2: the QA item is `E1.QA` under the Epic with the fix tasks as children, not at the root | the review (1 Critical, 6 High) filled the existing `### Epic item E1.QA` section: a one-line review reference and `- [ ] E1.QA.1 … E1.QA.10` checkbox children; no root-level section, no table; one History row | PASS |
| step 4: `E1.DEPLOY` under the Epic with `[Deploy] sample-wbs@{version}` as its child | first two runs ("Prepare the deploy … write the deploy record only"): the agent stopped at the failing release gate and wrote **no** record at all. With the prompt naming Step 4's `blocked` state: `### Epic item E1.DEPLOY` gained `- [ ] [Deploy] sample-wbs@unversioned — ⛔ blocked: release gate failed …` with the per-repo line as its child | PASS (see note) |
| a second run of step 4 finds it and creates nothing new | the same item was updated in place (its reason text), no second item, one more History row | PASS |
| every step: `karvey-trace.py sample-wbs --wbs` shows no `legacy shape` and no `outside the hierarchy` | `0 issue(s)` after steps 1, 2 and 4; the plan is in the Epic-item shape (the detector itself is covered by `test_wbs.py`, BUG-97) | PASS |

Note: without the explicit "record it as blocked", the deploy skill's agent does not write a deploy record when the
release gate fails before Step 4 (Step 4 runs after the gate). Reported to the parent as a wording question, not a
shape defect. Nothing was pushed or merged in any run.
