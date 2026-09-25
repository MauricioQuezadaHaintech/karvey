# PRD: wave2-structural

## 1. Executive summary
Wave 1 (3.12.0) made the method's guarantees real: a validated phase state, guards with table tests, a
production gate. What it did not change is the *shape* of the process: one pipeline for every change, seven
human gates per feature, no independent review before QA, a release unit (the integration branch) that is not
the approved unit (the change), tests written after the code, a security gate judged by the model alone, and
no metric that says which gate or phase earns its cost (expert panel 2026-09-23, R-08..R-14, R-17, R-20, R-23).
Wave 2 ships as **3.13.0** with every new behaviour advisory or opt-in, and becomes **4.0.0** when its defaults
turn blocking after 4–6 measured changes (D-24).

## 2. 🎯 Goal (the change's north star)
> **The cost of the process scales with the size and risk of the change, and every gate, lane and judge the
> method adds is measured from the change's own artifacts — so that turning the 3.13 advisory defaults into
> 4.0 blocking ones is decided on data from 4–6 measured changes, not on opinion.**

This goal is the north star that all Karvey phases pursue: each phase re-reads it on start to advance toward
the result without stopping until it is achieved, respecting the plan and security gates.

## 3. Problem and context
- **Who has it:** every team using Karvey — the human who approves gates, the agent that runs the skills,
  and whoever has to explain to a client what reached production and why.
- **Current situation** (`docs/spec/reviews/2026-09-23-panel-review.md` §3, judge reports DM/PM/AG):
  - **One lane for everything** (R-09, DM-01, PM-09): a one-line bug fix walks the same pipeline as a new
    UI feature, and the hotfix lane collides with the impl/deploy preconditions (H-04). When the method has no
    cheap legitimate path, teams take an illegitimate one — the method's own repo did (H-22).
  - **Seven human gates, doubled questions** (R-10, DM-06, AG-08): ≈50–70 interruptions per cycle; 13 skills
    still end with "Shall we advance" after asking for the approval; `-y` has no recorded meaning.
  - **No independent review before QA** (R-11 / JU-01, AG-12): the only independent look is QA's second
    opinion on the diff, at the end, where a spec defect is most expensive; QA sets `qa.approved` on its own
    findings.
  - **The approved unit is not the released unit** (R-08, DM-03, PM-04, H-21): the production PR carries
    whatever sits on the integration branch; nothing maps commits to changes; the integration merge is a local
    merge + push with no CI.
  - **Tests after code, evidence shared across changes** (R-12, DM-07): no requirement → test trace; QA ticks
    "tests pass" without running them.
  - **Security gate judged by the model** (R-13, DM-08): no secret scan, SAST, SCA or IaC scan is run.
  - **Deterministic work done by the model** (R-20, AG-07, AG-10, PM-13): release gate read by the LLM, IDs
    by "read and add 1", a health formula that cannot be reproduced, closing claims without machine evidence.
  - **"Canary" without thresholds** (R-23, DM-10): regression is an opinion; rollback undefined.
  - **Living spec merged after prod** (R-17 timing, DM-09): the Wave 1 merge tool runs at archive, which may
    never happen.
  - **No flow metric** (R-14, DM-11, PM-05, PM-12): `phase_history` exists since 3.12.0 but nothing reads it;
    the retro counts commits per author.
  - Backlog items deferred to this wave by D-17: BL-44..BL-50 (F-26..F-32) and the rest of F-33.
- **Impact:** without lanes the method is skipped for small work; without merged gates plus judges the human
  becomes a rubber stamp; without a release manifest an unapproved change reaches production by drag; and
  without metrics none of these fixes can be shown to work.

## 4. Objectives and success metrics
| # | Objective | Metric |
|---|---|---|
| O-1 | Baseline before changing the process | a metrics snapshot of the method's own repo exists before any lane/gate default changes (R-14 first) |
| O-2 | Flow metrics from the artifacts | lead time, cycle time per phase, human approval wait, throughput, deploy frequency, CFR, MTTR, spec-gap/ripple rate, gate rejection rate, estimate accuracy, judge acceptance and judge cost computed per lane and period; "n/a + reason" where data is missing |
| O-3 | Process cost proportional to the change | a `patch`-lane change passes 1 human gate (prod); lead time per lane reported |
| O-4 | Independent review before the human gate | judge verdicts shown at the requirements, architecture and qa gates of every `standard`/`feature-ui` change; judge cost recorded per gate and per change |
| O-5 | Fewer, heavier gates | with merged gates: 3 human gate questions per feature (vs 7), 0 "Shall we advance" after an approval question |
| O-6 | Approved unit = released unit | 100% of production releases carry a manifest that maps every commit to a change-id with `qa.approved` or lane-skipped QA |
| O-7 | Every requirement has a verifier | % of ADDED/MODIFIED requirements with an automated green test or a justified `manual` exception, per change |
| O-8 | Reproducible security verdict | every QA security dimension cites tool output or says "not evaluated" |
| O-9 | Deterministic gates and IDs | release gate, IDs, health score and closing evidence produced by scripts; 0 duplicated IDs |
| O-10 | Measurable post-deploy | every production deploy records a verification against declared thresholds, or "not evaluated" |
| O-11 | spec == prod | 0 changes deployed with an unmerged spec-delta |
| O-12 | Safe rollout | in 3.13.0 no project that passed under 3.12.0 fails because of a Wave 2 check; 4.0.0 flips only the D-24 defaults |

## 5. User stories / main use cases
- As the **human approver**, I want three gates with an independent verdict attached, so that each approval
  is informed rather than a rubber stamp.
- As a **developer fixing a small bug**, I want an official `patch` lane — BUG-NN, finding, fix, regression
  test — so that I stay inside the method without writing requirements and architecture for one line.
- As a **release manager**, I want the production PR to list exactly which changes it carries and whether
  each passed QA, so that nothing unapproved reaches production by drag.
- As the **method's owner**, I want metrics per lane and gate, so that I decide the 4.0 defaults on data.
- As a **QA reviewer**, I want tool output for secrets, SAST, SCA and IaC and a trace from each requirement to
  its test, so that my verdict is reproducible.
- As a **team running several agents in parallel**, I want IDs reserved by a script, so that two sessions
  never create the same BUG-NN or D-NN.

## 6. Scope (in scope)
Internal order follows the panel's Wave 2 plan: R-14 first, then R-09 + R-11 advisory, then R-10 + R-08 in
warn mode, then 4.0 after 4–6 measured changes.

| # | Area | Panel item | Backlog | Decisions |
|---|---|---|---|---|
| S-1 | Flow metrics, gate outcomes, deploy records, time entries, data-driven retro | R-14 | BL-17, BL-45 | D-24, D-30 |
| S-2 | Lanes (`patch`, `standard`, `feature-ui`, `ops`, `hotfix`, `docs`) with objective criteria | R-09 | BL-12 | D-25, D-29 |
| S-3 | Advisory judges at requirements, architecture, qa (incl. the clean-context "fiscal" before `qa.approved`, AG-12 / B-12) | R-11 (JU-01) | BL-14 | D-23, D-30 |
| S-4 | Three merged human gates, one question per gate, `-y` as `role: auto`, `--granular-gates` | R-10 | BL-13 | D-22 |
| S-5 | Release per change: `Karvey-Change` trailer, release manifest, integration by PR, trunk mode; prod-record order and ledger fallback | R-08 | BL-11, BL-46, BL-47, BL-48 | D-26 |
| S-6 | Spec-delta merged on the change branch before the production PR | R-17 (timing) | BL-20 (rest) | — |
| S-7 | Test-first tasks and a REQ → task → commit → test trace | R-12 | BL-15 | — |
| S-8 | Deterministic security tools in QA and a proposal for the PR pipeline | R-13 | BL-16 | — |
| S-9 | Scripts: release gate, IDs, health score, evidence wrapper; cross-repo decision refs | R-20 | BL-23, BL-44 | — |
| S-10 | Post-deploy verification with thresholds and a defined rollback | R-23 | BL-26 | — |
| S-11 | Knowledge sync optional everywhere | R-16 (rest) | — | D-27 |
| S-12 | Import resumes through recorded gates; one decision-log shape; statusline-down table case | — | BL-49, BL-50, F-33 (rest) | — |
| S-13 | Rollout: advisory in 3.13.0, D-24 defaults blocking in 4.0.0; migration; dogfooding | Ola 2 plan | — | D-24 |

## 7. Out of scope
- Wave 3 items: R-15 (context budget, `_core.md`), R-19 (stakeholder report and "your turn" events — this
  change only produces the manifest they will read), R-24 (Q-NN, risks), R-25 (cost per change beyond the
  judges' cost), R-26 (design system), R-27 (WBS), R-28 (portfolio), R-29 (WSJF), R-30 (portability).
- Turning judges blocking by default: D-23 keeps them advisory; blocking stays an opt-in mode and a later
  decision.
- Editing the owner's personal global instructions: the change prepares the diff for the `patch` lane rule
  (D-25); the owner applies it (D-01, D-11).
- Running migrations in other repositories: each repo's own docs PR.
- Emergent backlog BL-34..BL-43 and BL-51 (`project-upgrade` is its own change, D-20).

## 8. Stakeholders
- **Requests and approves:** the method's owner (approves the three gates of this change and production —
  `role: human`).
- **Impacted:** every project using Karvey and the agents running its skills.
- **Sources:** the expert panel (DM, PM, AG judges), the owner's proposal JU-01, and the Wave 1 findings
  deferred by D-17.

## 9. Constraints
- **Security Tier: 2** — the change extends the guards that gate production (release manifest, per-change
  approvals, trailer check), adds scripts that run external security tools and pass `project.json` values to
  commands, and runs judge subagents over the change's artifacts. Controls required: the manifest check fails
  closed once blocking; tool commands take no unvalidated project values; judges receive only the phase
  artifacts and the rubric; no judge or tool output is ever treated as an approval.
- **Backward compatible in 3.13.0** (D-24): every new check has an advisory/opt-in mode; `validate` keeps
  legacy shapes as warnings; a legacy `spec.json` without `lane` keeps today's pipeline.
- **Public, organisation-neutral text:** the method is for anyone; no rule, skill or example names a company,
  product, client, internal URL, person's e-mail or personal path.
- **Dogfooding:** built through the method on this repo, trunk flow (`main` = integration = production),
  Markdown tracker (`PLAN.md`); its own commits carry the `Karvey-Change` trailer from the first one.
- **Prerequisite:** `wave1-hardening` (3.12.0) merged — this branch is forked from it and depends on the
  state tool, the schemas, the prod gate, the spec-merge tool and the dashboard script.
- **Decisions this change depends on:** D-22..D-27, D-29, D-30 (D-29 and D-30 relayed by the orchestrator on
  2026-09-25, pending entry in `docs/spec/decisions.md`); D-01..D-19 still hold.

## 10. Acceptance criteria
- **AC-1** A metrics snapshot of this repo (baseline) is stored before the lane and gate defaults change, and
  `--metrics` reproduces it byte-identically on the same input.
- **AC-2** A `patch` change that meets D-29 reaches production with BUG-NN, finding, fix, regression test and
  one human gate; one that breaks D-29 is refused the lane and proposed `standard`.
- **AC-3** A `standard` change shows judge verdicts at its requirements, architecture and qa gates, with
  judge tokens and US$ recorded; judges never block an approval in advisory mode.
- **AC-4** With merged gates, a `standard` change asks the human exactly three gate questions.
- **AC-5** The release manifest of this change's own production PR lists every commit with its change-id
  and QA state; a commit without trailer is reported (3.13) and blocks when the manifest is blocking (4.0).
- **AC-6** This change's living spec is merged before its production PR.
- **AC-7** `traceability.md` of this change maps every REQ-W2 to a test or a justified `manual` exception.
- **AC-8** The plugin linter and guard tables are green; no Wave 2 check fails a project that passed under
  3.12.0 while its mode is advisory.
