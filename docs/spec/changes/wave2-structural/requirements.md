# Requirements: wave2-structural

## Project description

Wave 1 (3.12.0) made the method's guarantees real; Wave 2 changes the shape of the process so that its cost
scales with the change: lanes with an official `patch` path, three merged human gates backed by advisory
judges, release per change with a manifest, test-first traceability, deterministic security tools and
scripts, a post-deploy verification with thresholds, the living spec merged before production — and flow
metrics first, so every one of these is measured. It ships as 3.13.0 advisory / opt-in and becomes 4.0.0 when
the D-24 defaults turn blocking (panel review 2026-09-23, Ola 2). North star (PRD §2): *the cost of the
process scales with the size and risk of the change, and every gate, lane and judge the method adds is
measured from the change's own artifacts — so that turning the 3.13 advisory defaults into 4.0 blocking ones
is decided on data from 4–6 measured changes, not on opinion.*

## Conventions

- **IDs.** `REQ-W2-NNN`, numbered contiguously. The heading also carries the numeric EARS id (`1.1`, `1.2`…)
  required by `rules/ears-format.md`.
- **Trace line.** Each requirement cites the PRD (`PRD §n` / scope `S-n` / objective `O-n` / acceptance
  `AC-n`) and its sources: panel recommendation `R-xx`, verified panel finding `H-xx`, judge item
  `DM-xx`/`PM-xx`/`AG-xx`, owner proposal `JU-01`, wave1 finding `F-xx`, board item `B-xx`, backlog item
  `BL-NN`, and decision `D-NN`.
- **Living spec baseline.** The REQ-W1-* requirements of `wave1-hardening` (its `spec-delta.md`) are treated
  as already part of the living spec. Where a Wave 2 requirement changes one of them, it says **MODIFIES
  REQ-W1-0xx**; `spec-delta.md` lists it under MODIFIED.
- **Modes.** Every new check carries a mode: **advisory** (reported, never refuses), **warn** (reported as a
  warning on the gate summary and in the dashboard, never refuses) or **blocking** (refuses). "In 3.13" means
  the default of release 3.13.0; "in 4.0" the default of 4.0.0 (D-24). A project can always choose a stricter
  mode than the default.
- **Technology.** The SHALL text names *roles* of the method. Where the panel or the owner fixed a public name
  (a command, file or field the user types or reads), the glossary maps the role to that name; languages,
  frameworks and runners are architecture decisions.
- **Actors.** "the method" = the skills and rules as shipped; "a phase skill" = any skill that owns a phase;
  "the human" = the person who owns the change's approvals (`role: human`); "a judge" = an independent
  reviewing subagent of R-11.
- **Neutrality.** No requirement, rule or example names an organisation, product, client, internal URL,
  person's e-mail or personal path (PRD §9).

### Glossary — roles and their public names

| Role in the requirements | Public name fixed by the panel / owner | Source |
|---|---|---|
| the **state tool** | `scripts/karvey-state` (Wave 1) | R-01 |
| the **metrics view** | `karvey-context --metrics` backed by `scripts/karvey-context` | R-14 |
| the **retro** | `karvey-retro`, output `docs/spec/retros/retro-{date}.md` | R-14, PM-12 |
| the **lanes rule** | `rules/lanes.md` + a lane table the state tool reads | R-09 |
| the **judges** | skill `karvey-judges`, rule `rules/judges.md`, rubrics `rules/judges/{phase}.md` | R-11 |
| the **judge settings** | `project.json:judges` | R-11, D-23, D-30 |
| the **gate settings** | `project.json:gates` (`merged` \| `granular`), flag `--granular-gates` | R-10, D-22 |
| the **change trailer** | commit trailer `Karvey-Change: <change-id>` | R-08, D-26 |
| the **release manifest** | deploy step "release manifest" (2.8-bis) | R-08 |
| the **branch mode** | `project.json:branch_flow.mode` (`trunk` \| `env-branches`) | R-08, D-26 |
| the **trace** | `changes/{id}/traceability.md` | R-12 |
| the **release gate** | `scripts/karvey-release-gate` | R-20, AG-10 |
| the **id tool** | `scripts/karvey-id` (`next {BUG\|D\|BL\|F\|Q}`) | R-20, AG-07 |
| the **health score** | `scripts/karvey-health-score` | R-20 |
| the **evidence wrapper** | `scripts/karvey-evidence -- <cmd>` → `changes/{id}/evidence.jsonl` | R-20, AG-12 |
| the **post-deploy contract** | section of `infra.md`; evidence `changes/{id}/deploy_evidence.md` | R-23 |
| the **spec-merge tool** | `scripts/karvey-spec-merge` (Wave 1) | R-17 |

---

## Requirement 1: Flow metrics and a retro on the method's artifacts (R-14) — first

### 1.1 REQ-W2-001 — Gate outcomes are recorded
WHEN a gate question is answered, the state tool SHALL append to `spec.json` the outcome (`approved` or
`changes_requested`), the phase or phases it covered, who answered, the role, the reference and an ISO 8601
timestamp with time and zone, and SHALL record the time each approval was first marked generated; it SHALL NOT
rewrite earlier outcomes.

Traces to PRD: §6 S-1, O-2 · Sources: R-14, R-10 (tasa de rechazo por gate), PM-05 (espera de aprobación), DM-11 · BL-17

**Scenario — success:** GIVEN requirements generated at 10:00 and the human answers "Request changes" at 10:40
and "Approve" at 11:30 WHEN the outcomes are read THEN two entries exist and the approval wait is computable
from `generated` to each answer.
**Scenario — error:** GIVEN an outcome without a role or reference WHEN it is recorded THEN the state tool
refuses and `spec.json` is byte-identical.

### 1.2 REQ-W2-002 — Deploy records
WHEN a deploy to an environment finishes, the method SHALL append to `spec.json:deploys` an entry with the
environment, the version, the time, the post-deploy verification result (REQ-W2-076) and the rollback taken, if
any; entries SHALL be append-only.

Traces to PRD: §6 S-1, S-10, O-2, O-10 · Sources: R-14 (`deploys[{env, version, canary, rollback}]`), PM-05 · BL-17, BL-26

**Scenario — success:** GIVEN a production deploy whose verification passed WHEN it finishes THEN
`deploys` gains `{env: "prod", version, at, verification: "pass", rollback: null}`.
**Scenario — error:** GIVEN a deploy entry without an environment WHEN `spec.json` is validated THEN the
validation names `deploys[n].env` as missing.

### 1.3 REQ-W2-003 — Metrics per lane and period
WHEN the metrics view is requested for a project and a period, the method SHALL compute, per lane and for all
lanes: lead time (change created → production approval), cycle time per phase, human approval wait per gate,
throughput (archived changes per week), deploy frequency, change failure rate, time to restore, spec-gap rate
and ripple per change, gate rejection rate, estimate accuracy, judge finding acceptance rate and judge cost.

Traces to PRD: §6 S-1, O-2 · Sources: R-14, DM-11, PM-05 · Decision: D-30 (judge cost measured) · BL-17

**Scenario — success:** GIVEN three archived changes with `phase_history`, outcomes and deploys WHEN the view
runs for the period THEN every metric is printed per lane and in total.
**Scenario — error:** GIVEN a period with no archived change WHEN the view runs THEN it prints the metrics as
"n/a — no archived change in period", not as zero.

### 1.4 REQ-W2-004 — Missing data is stated, never zero
IF a metric cannot be computed for a change because its data is missing or legacy (no `phase_history`, date
without time, no outcome entries), THEN the metrics view SHALL report that metric as "n/a" with the reason and
the change-id, and SHALL exclude the change from that metric's aggregate only.

Traces to PRD: §6 S-1, O-2 · Sources: R-14, verification rule (state what you did not verify) · BL-17

**Scenario — success:** GIVEN a legacy change with date-only approvals WHEN the approval wait is computed THEN
it shows "n/a — approvals without time ({id})" and the other changes still aggregate.
**Scenario — error:** GIVEN the same change WHEN the view runs THEN it SHALL NOT print an approval wait of 0.

### 1.5 REQ-W2-005 — Read-only, reproducible, machine-readable
The metrics view SHALL be read-only, SHALL produce the same output for the same repository state and period,
and SHALL offer a structured (JSON) form besides the human-readable table.

Traces to PRD: §6 S-1, AC-1 · Sources: R-14, PM-05 (solo lectura), AG-10 · BL-17

**Scenario — success:** GIVEN no change to the repository WHEN the view runs twice with the same period THEN
the two JSON outputs are byte-identical.
**Scenario — error:** GIVEN the view is run WHEN it finishes THEN `git status` shows no modified file; any
write attempt is a defect.

### 1.6 REQ-W2-006 — Baseline before the process changes
BEFORE any lane, gate or judge default of this change is enabled on this repository, the method SHALL store a
metrics snapshot of the repository (baseline) with the date and the method version, and the retro SHALL
compare later periods against it.

Traces to PRD: §6 S-1, O-1, AC-1 · Sources: R-14 ("para tener la línea base antes de cambiar el proceso") · Decision: D-24 · BL-17

**Scenario — success:** GIVEN the metrics view is implemented WHEN the baseline is taken THEN
`docs/spec/retros/baseline-{date}.json` exists before the first lane default is enabled.
**Scenario — error:** GIVEN no baseline file WHEN the lanes default is enabled in this repo's `project.json`
THEN the linter reports the missing baseline.

### 1.7 REQ-W2-007 — Actual time through the tracker adapter
WHEN a task finishes, the method SHALL record the actual time through a `log_time` operation of the team's
tracker adapter (time entry, worklog or equivalent), declared per tool with `none` for tools that have no such
object, and SHALL fall back to the task record's actual columns when the operation is `none`.

Traces to PRD: §6 S-1, O-2 · Sources: R-05 (Wave 1), F-27 · MODIFIES REQ-W1-042 · BL-45

**Scenario — success:** GIVEN a tracker whose adapter declares `log_time` WHEN a task finishes THEN the actual
is logged through that operation and the estimate field is untouched.
**Scenario — error:** GIVEN a tool whose adapter row has no `log_time` entry at all WHEN the linter runs THEN
it reports the adapter row as incomplete.

### 1.8 REQ-W2-008 — The retro works on the method's artifacts
WHEN the retro runs for a period, it SHALL present the metrics of REQ-W2-003, the findings by type and by the
phase that found them, the estimate accuracy and the judge cost; SHALL store the result in
`docs/spec/retros/retro-{date}.md`; and SHALL record each agreed action as a `BL-NN` of type `process` with an
owner.

Traces to PRD: §6 S-1, O-2 · Sources: R-14, PM-12, DM-11 · BL-17

**Scenario — success:** GIVEN a period with two archived changes WHEN the retro runs and one action is agreed
THEN the retro file exists and `backlog.md` gains one `process` item with its owner.
**Scenario — error:** GIVEN an action without an owner WHEN the retro records it THEN it asks for the owner
and does not write the backlog item without one.

### 1.9 REQ-W2-009 — Actions are followed up; per-person analysis is optional
WHEN a retro runs and a previous retro exists, it SHALL report the state of each previous action; the per-author
commit analysis SHALL run only when explicitly requested.

Traces to PRD: §6 S-1 · Sources: R-14, PM-12 ("el análisis por persona queda como opcional") · BL-17

**Scenario — success:** GIVEN a previous retro with two actions, one done WHEN the new retro runs THEN it lists
both with their current state.
**Scenario — error:** GIVEN no request for the per-person view WHEN the retro runs THEN no per-author ranking is
printed.

### 1.10 REQ-W2-010 — 4.0 readiness report
WHEN the metrics view is asked for readiness, it SHALL report the number of changes measured under 3.13 modes,
and, per Wave 2 check, how many times it would have refused had it been blocking and how many of those were
confirmed defects.

Traces to PRD: §6 S-1, S-13, O-12 · Sources: panel Ola 2 plan ("después de 4–6 cambios medidos") · Decision: D-24

**Scenario — success:** GIVEN five changes measured in advisory mode WHEN readiness is requested THEN it prints
"5 measured" and a would-refuse / confirmed count per check.
**Scenario — error:** GIVEN a check that records no hit data WHEN readiness is requested THEN it is listed as
"no data" rather than omitted.

---

## Requirement 2: Lanes by size and risk (R-09)

### 2.1 REQ-W2-011 — Lanes as data
The method SHALL define the lanes `patch`, `standard`, `feature-ui`, `ops`, `hotfix` and `docs` in one lane
table that states, for each lane and phase, whether the phase is mandatory, optional or skipped and how many
human gates apply, and the state tool SHALL compute the next phase of a change from its lane.

Traces to PRD: §6 S-2, O-3 · Sources: R-09, DM-01, PM-09, H-03, H-04 · BL-12

**Scenario — success:** GIVEN a `standard` change with requirements approved WHEN `next` runs THEN it proposes
`architecture` (mockup and design skipped by the lane).
**Scenario — error:** GIVEN a lane name not in the table WHEN `spec.json` is validated THEN the validation names
the value and lists the valid lanes.

### 2.2 REQ-W2-012 — Lane chosen at init with objective questions
WHEN a change is initialised, the init skill SHALL decide the lane from objective answers — does it touch UI,
does it change a data schema or an API contract, does it change permissions or a trust boundary, which Security
Tier, how many code files — SHALL record it in `spec.json:lane`, and SHALL propose `standard` when an answer is
unknown.

Traces to PRD: §6 S-2, O-3 · Sources: R-09 ("3 preguntas objetivas"), DM-01 · Decision: D-29 · BL-12

**Scenario — success:** GIVEN no UI, no schema/contract change and new logic across six files WHEN init runs
THEN it records `lane: "standard"`.
**Scenario — error:** GIVEN the human cannot say whether the change touches an API contract WHEN init runs THEN
it records `standard`, not `patch`, and says why.

### 2.3 REQ-W2-013 — Objective criterion of the `patch` lane
The method SHALL admit a change to the `patch` lane only if it touches at most 3 code files, changes no data
schema, no API contract and no permissions, and its Security Tier is below 3; IF any criterion fails, THEN the
method SHALL refuse the lane and propose `standard`.

Traces to PRD: §6 S-2, O-3, AC-2 · Sources: R-09 (riesgo de abuso del carril `patch`), DM-01 · Decision: D-29, D-25 · BL-12

**Scenario — success:** GIVEN a fix in 2 code files, no schema, API or permission change, Tier 2 WHEN `patch` is
requested THEN it is recorded.
**Scenario — error:** GIVEN the same fix plus a column added to a table WHEN `patch` is requested THEN it is
refused with "patch: schema change — use standard".

### 2.4 REQ-W2-014 — The `patch` path
WHERE a change is in the `patch` lane, the method SHALL require, in the same PR, a `BUG-NN` incident, a finding,
the fix and a regression test that fails without the fix; SHALL skip requirements, mockup, design, architecture,
infra and tasks; and SHALL keep QA-lite and the production gate as its only human gate.

Traces to PRD: §6 S-2, O-3, AC-2 · Sources: R-09 (`iterate/init-lite → impl test-first → qa-lite → deploy`), DM-01 · Decision: D-25 · BL-12

**Scenario — success:** GIVEN a `patch` change with BUG-NN, finding, fix and a failing-then-passing test WHEN it
reaches the prod gate THEN one human approval releases it.
**Scenario — error:** GIVEN a `patch` change without a regression test WHEN QA-lite runs THEN it reports "patch
without regression test" and the incident cannot reach RESUELTO.

### 2.5 REQ-W2-015 — Lane-skipped phases are recorded automatically
WHEN the state tool advances a change past a phase its lane skips, it SHALL record the phase in
`spec.json:skipped` with the reason `lane:{lane}`, without the agent running a separate skip.

Traces to PRD: §6 S-2 · Sources: R-09 ("las fases omitidas quedan como skipped"), R-01 · MODIFIES REQ-W1-007 · BL-12

**Scenario — success:** GIVEN a `standard` change WHEN it advances from requirements to architecture THEN
`skipped.mockup` and `skipped.design_graphic` read `lane:standard`.
**Scenario — error:** GIVEN a `feature-ui` change WHEN architecture is requested without mockup approved THEN it
is refused; mockup is not auto-skipped.

### 2.6 REQ-W2-016 — Lane changes: up freely, down only by the human
WHEN a change's lane is raised, the state tool SHALL record the old lane, the new lane, the time and the reason;
IF a lane would be lowered, THEN it SHALL refuse unless the human's approval and a reason are given; the phases
the new lane requires and the old one skipped SHALL become pending. A change is a raise only when every phase keeps
at least its mode in the new lane (mandatory stays mandatory, optional stays at least optional); any other change
is a lowering, even when the new lane runs more phases.

Traces to PRD: §6 S-2 · Sources: R-09 ("se puede subir de carril, pero nunca bajar sin registro"), DM-01 · BL-12 ·
Revision 1 (2026-09-26, F-23 / BUG-62, QA): "raise" was undefined and the tool ranked lanes by phase count, so
`docs` → `ops` passed as a raise while making QA optional; rewritten in place with the recommended option (a raise
keeps every phase's mode; alternative rejected: keep the phase-count order and add a QA-only exception).

**Scenario — success:** GIVEN a `patch` change whose fix turns out to need a contract change WHEN the lane is
raised to `standard` THEN `requirements` becomes the next pending phase and the change is recorded.
**Scenario — error:** GIVEN a `standard` change WHEN the agent lowers it to `patch` without a human approval THEN
the state tool refuses.
**Scenario — error (revision 1):** GIVEN a `docs` change WHEN the agent "raises" it to `ops`, which makes QA optional,
THEN the state tool refuses it as a raise and names `qa`.

### 2.7 REQ-W2-017 — The diff is checked against its lane
WHEN QA (or QA-lite) runs, the method SHALL measure the change's diff against its lane's criteria and SHALL
report every exceeded criterion as a finding with a lane-raise proposal; in 3.13 the check is warn; the prod gate
SHALL show its result.

Traces to PRD: §6 S-2, O-3 · Sources: R-09 ("QA-lite verifica que el tamaño del diff respete el carril"), DM-01 · Decision: D-29, D-24 · BL-12

**Scenario — success:** GIVEN a `patch` change touching 2 code files WHEN QA-lite runs THEN the lane check passes.
**Scenario — error:** GIVEN a `patch` change whose diff touches 5 code files WHEN QA-lite runs THEN a finding
"lane exceeded: 5 > 3 code files" is appended and `standard` is proposed.

### 2.8 REQ-W2-018 — Hotfix lane preconditions are consistent
WHERE a change is in the `hotfix` lane, the state tool SHALL let impl start without a tasks approval and deploy
proceed without a full QA review document, and SHALL still require the BUG-NN, the regression test in the same
PR and the human production approval.

Traces to PRD: §6 S-2 · Sources: R-09, H-04, DM-01 (hotfix choca con las precondiciones) · BL-12

**Scenario — success:** GIVEN a hotfix with BUG-NN and regression test WHEN impl is requested THEN it starts
without `tasks.approved`.
**Scenario — error:** GIVEN a hotfix without a human prod approval WHEN the merge to production is attempted THEN
the prod gate blocks it.

### 2.9 REQ-W2-019 — A change without a lane keeps today's pipeline
WHERE a `spec.json` has no `lane`, the state tool SHALL treat it as the full pipeline of 3.12.0 (every phase
mandatory unless recorded as skipped), SHALL report the missing lane as a warning in 3.13, and as an error in 4.0.

Traces to PRD: §6 S-2, S-13, O-12 · Sources: R-09, panel Ola 2 ("el esquema de spec.json pasa a ser obligatorio (lane…)") · Decision: D-24 · BL-12

**Scenario — success:** GIVEN a legacy change without `lane` in 3.13 WHEN `next` runs THEN it behaves as in 3.12.0
and prints one warning.
**Scenario — error:** GIVEN the same change in a project on 4.0 strict schema WHEN it is validated THEN `lane` is
reported as a missing required field.

### 2.10 REQ-W2-020 — The owner's global instruction diff for the `patch` lane
The change SHALL deliver, as a file inside the change folder, the proposed diff to the owner's personal global
instructions that makes the `patch` lane the official path for a small bug, and SHALL NOT write to the owner's
personal configuration.

Traces to PRD: §6 S-2, §7 · Sources: panel §6.4 · Decision: D-25, D-01, D-11

**Scenario — success:** GIVEN the lanes are implemented WHEN the change reaches QA THEN
`changes/wave2-structural/global-instructions.diff` exists and names the lines it replaces.
**Scenario — error:** GIVEN any step of this change WHEN it would write outside the repository into the user's
personal configuration THEN the plan and protect-path guards block it.

### 2.11 REQ-W2-021 — Lane is visible
The dashboard, the metrics view and the gate summaries SHALL show each change's lane and its lane-skipped phases
as "skipped (lane)", distinct from pending phases.

Traces to PRD: §6 S-2, O-2 · Sources: R-09 ("dashboards honestos"), DM-01 · BL-12

**Scenario — success:** GIVEN a `standard` change WHEN the dashboard runs THEN it shows `lane standard` and mockup
as "skipped (lane)".
**Scenario — error:** GIVEN a lane-skipped phase WHEN the dashboard runs THEN it SHALL NOT be listed as pending or
awaiting approval.

---

## Requirement 3: Advisory judges before the human gates (R-11, JU-01)

### 3.1 REQ-W2-022 — Where judges run
WHERE judges are enabled, the method SHALL run the judges before the human gate of the requirements, the
architecture and the qa phases, and SHALL allow a project to add or remove phases in the judge settings.

Traces to PRD: §6 S-3, O-4, AC-3 · Sources: R-11, JU-01, DM-06, AG-12 · Decision: D-23 · BL-14

**Scenario — success:** GIVEN a `standard` change with default judge settings WHEN requirements are generated THEN
the judges run before the human is asked.
**Scenario — error:** GIVEN judges disabled in `project.json` WHEN the gate is presented THEN the summary says
"judges: disabled by project setting" rather than showing nothing.

### 3.2 REQ-W2-023 — Clean context and closed inputs
WHEN a judge runs, it SHALL receive only the artifacts of the phase under review, the artifacts that phase reads,
the PRD goal and the rubric of that phase, and SHALL NOT receive the author's conversation or reasoning.

Traces to PRD: §6 S-3, §9 · Sources: R-11 ("contexto limpio"), AG-12 · Decision: D-23 · BL-14

**Scenario — success:** GIVEN an architecture judge WHEN it starts THEN its input list is `requirements.md`,
`architecture.md`, the goal and the architecture rubric.
**Scenario — error:** GIVEN a judge invocation that passes the session transcript WHEN the judges skill builds the
input THEN it drops it and logs that it did.

### 3.3 REQ-W2-024 — One rubric and lenses per phase
The method SHALL ship one rubric per judged phase and SHALL assign default lenses per phase — requirements:
domain and methods; architecture: security, methods and agents/cost; qa: fiscal (evidence) and security.

Traces to PRD: §6 S-3 · Sources: R-11 (lentes según la fase), DM-06, DM-08 · Decision: D-23 · BL-14

**Scenario — success:** GIVEN default settings WHEN the qa judges run THEN the lenses are `fiscal` and `security`.
**Scenario — error:** GIVEN a lens configured in `project.json` with no rubric WHEN validated THEN the lens is named
as unknown.

### 3.4 REQ-W2-025 — A finding without a citation is discarded
WHEN a judge reports a finding, it SHALL cite `file:line` of the reviewed artifacts; IF a finding has no
resolvable citation, THEN the judges skill SHALL discard it and count it as discarded.

Traces to PRD: §6 S-3 · Sources: R-11 ("un hallazgo sin cita se descarta") · BL-14

**Scenario — success:** GIVEN a finding citing `requirements.md:120` WHEN it is collected THEN it is kept.
**Scenario — error:** GIVEN a finding citing a line that does not exist WHEN it is collected THEN it is discarded
and the gate summary shows "1 discarded (no citation)".

### 3.5 REQ-W2-026 — Judges observe; the iterate skill routes
WHEN a judge finding is kept, the judges skill SHALL append it to the change's `findings.md` with origin
`judge:{lens}`, a type guess and a severity, and SHALL NOT route it, edit the artifact or change `spec.json`.

Traces to PRD: §6 S-3 · Sources: R-11, panel §5 ("quien observa no enruta") · BL-14

**Scenario — success:** GIVEN two kept findings WHEN the judges finish THEN `findings.md` gains two `open` rows with
origin `judge:methods`.
**Scenario — error:** GIVEN a judge output that proposes a patch to the artifact WHEN collected THEN the patch is not
applied and the finding keeps only its text.

### 3.6 REQ-W2-027 — The gate summary carries the verdicts
WHEN a judged gate is presented, the method SHALL show per judge its lens, verdict, number of findings by
severity and model used, the blocking-severity findings in full, and any disagreement between judges.

Traces to PRD: §6 S-3, O-4 · Sources: R-11 ("el gate humano muestra un resumen") · BL-14

**Scenario — success:** GIVEN two judges with verdicts `pass` and `concerns` WHEN the gate is shown THEN both appear
and the disagreement is stated.
**Scenario — error:** GIVEN one judge failed to return WHEN the gate is shown THEN it reads "judge {lens}: not run
({reason})".

### 3.7 REQ-W2-028 — Advisory by default; blocking is opt-in
WHILE the judge mode is advisory, no judge finding SHALL prevent an approval; WHERE a project sets the judge mode to
blocking, the state tool SHALL refuse the approval of a judged phase while a Critical or High judge finding of that
phase is `open`.

Traces to PRD: §6 S-3, O-4, AC-3 · Sources: R-11 (`mode: advisory`, `blocking` opcional) · Decision: D-23 · BL-14

**Scenario — success:** GIVEN advisory mode and an open High judge finding WHEN the human approves THEN the
approval is recorded and the summary lists the finding.
**Scenario — error:** GIVEN blocking mode and an open Critical judge finding WHEN `approve` runs THEN it refuses and
names the finding.

### 3.8 REQ-W2-029 — Cross-model preferred, intra-model declared
WHEN a judge runs, the method SHALL use a different model family when one is available in the session and SHALL
otherwise run an intra-model judge, recording in every case the model used and whether it was intra-model.

Traces to PRD: §6 S-3 · Sources: R-11 (`cross_model: prefer`), DM-08, AG-12 · Decision: D-23 · BL-14

**Scenario — success:** GIVEN no other model available WHEN the judges run THEN they run and the summary says
"intra-model".
**Scenario — error:** GIVEN a judge record without the model field WHEN validated THEN the record is reported
incomplete.

### 3.9 REQ-W2-030 — Judge cost is measured, never capped
WHEN a judge run finishes, the method SHALL record its tokens and US$ per judge, per gate and per change, marking
values as estimated when the runtime does not expose them; no budget setting SHALL stop, shorten or skip a judge
run.

Traces to PRD: §6 S-3, S-1, O-4, AC-3 · Sources: R-11 (costo en tokens), R-25 (costo de jueces aparte) · Decision: D-30 (replaces the cap part of D-23) · BL-14

**Scenario — success:** GIVEN three judges at the architecture gate WHEN they finish THEN `spec.json` holds their
tokens and US$ and the per-change total.
**Scenario — error:** GIVEN a `project.json:judges.budget` value WHEN judges run THEN it is reported as ignored
("measure only, D-30") and no judge is skipped.

### 3.10 REQ-W2-031 — Judges per lane
The method SHALL run by default no judges in the `patch` lane, two lenses per judged phase in `standard` and three
in `feature-ui`, and SHALL let a project override the count per lane.

Traces to PRD: §6 S-3, S-2 · Sources: R-11 ("patch sin jueces, standard con 2, feature-ui con 3") · BL-14

**Scenario — success:** GIVEN a `patch` change WHEN it reaches QA-lite THEN no judge runs and the summary says
"judges: none for lane patch".
**Scenario — error:** GIVEN an override of −1 judges WHEN validated THEN the value is refused.

### 3.11 REQ-W2-032 — The fiscal before `qa.approved`
BEFORE `qa.approved` is recorded, a clean-context judge with the `fiscal` lens SHALL receive the diff and the QA
review document and SHALL list every claim of the review that has no evidence (command output, test run, file
citation); its findings follow REQ-W2-026.

Traces to PRD: §6 S-3 · Sources: AG-12 ("fiscal antes de qa.approved"), B-12 (proposal, cheap piece) · Decision: D-23 (qa phase) · BL-14

**Scenario — success:** GIVEN a review that claims "tests pass" and cites a CI run WHEN the fiscal runs THEN it reports
no unsupported claim.
**Scenario — error:** GIVEN a review that claims "tests pass" with no run cited WHEN the fiscal runs THEN a finding
"claim without evidence" is appended.

### 3.12 REQ-W2-033 — Acceptance of judge findings is recorded
WHEN the iterate skill routes a judge finding, it SHALL record whether it was accepted (routed as bug, spec-gap or
emergent) or rejected with a reason, so that the acceptance rate per lens is computable.

Traces to PRD: §6 S-3, S-1, O-2 · Sources: R-11 ("tasa de hallazgos de juez aceptados") · BL-14

**Scenario — success:** GIVEN three judge findings, two routed and one rejected WHEN metrics run THEN the lens shows
2/3 accepted.
**Scenario — error:** GIVEN a judge finding closed without routing or reason WHEN convergence is checked THEN it is
reported as unresolved.

---

## Requirement 4: Three merged human gates (R-10)

### 4.1 REQ-W2-034 — Three gates per feature
WHERE merged gates are enabled, the method SHALL ask the human three gate questions per `feature-ui` or `standard`
change: (1) *what* — requirements, mockup and design; (2) *how* — architecture, infra and tasks; (3) *release* — qa
and production; phases a lane skips are left out of their gate.

Traces to PRD: §6 S-4, O-5, AC-4 · Sources: R-10, DM-06 · Decision: D-22 · BL-13

**Scenario — success:** GIVEN a `standard` change with merged gates WHEN it goes from init to production THEN the
human answers exactly three gate questions.
**Scenario — error:** GIVEN merged gates WHEN a phase skill tries to ask its own approval between gates THEN the
linter flags the skill text as a second gate question.

### 4.2 REQ-W2-035 — One question per gate
WHEN a gate is presented, the method SHALL ask one question with the options *Approve and advance (recommended)*,
*Approve and stop* and *Request changes*, and SHALL NOT ask a separate "shall we advance" after it.

Traces to PRD: §6 S-4, O-5 · Sources: R-10, AG-08, DM-06 · Decision: D-22 · BL-13

**Scenario — success:** GIVEN the *how* gate WHEN the human picks *Approve and advance* THEN impl starts with no
further question.
**Scenario — error:** GIVEN any phase skill text WHEN the linter runs THEN a closing "shall we advance" after an
approval question is reported.

### 4.3 REQ-W2-036 — A merged gate records every phase's approval
WHEN a merged gate is approved, the state tool SHALL record an approval for each non-skipped phase it covers, with
the same `by`, `role`, `ref` and time, and SHALL NOT merge the phases' artifacts.

Traces to PRD: §6 S-4 · Sources: R-10 · Decision: D-22 ("merging gates does not merge their artifacts") · BL-13

**Scenario — success:** GIVEN the *how* gate of a change with infra skipped WHEN approved THEN
`approvals.architecture` and `approvals.tasks` hold the same record and `infra` stays skipped.
**Scenario — error:** GIVEN the *how* gate WHEN `tasks.md` was not generated THEN the gate is not presented and the
missing artifact is named.

### 4.4 REQ-W2-037 — The *how* gate carries a one-page summary
WHEN the *how* gate is presented, the method SHALL show a one-page summary of decisions, deviations from the
requirements, risks, estimated cost, `[human]` tasks and the judges' verdicts.

Traces to PRD: §6 S-4, O-5 · Sources: R-10 ("con un resumen de una página"), DM-06 · BL-13

**Scenario — success:** GIVEN architecture and tasks generated WHEN the gate opens THEN the summary lists the `[human]`
tasks with their executor.
**Scenario — error:** GIVEN a deviation from a requirement recorded in architecture WHEN the summary omits it THEN the
gate check reports the omission.

### 4.5 REQ-W2-038 — Continuous execution between gates
WHILE a change is between two gates, the phase skills SHALL advance without asking the human, except for the
exceptions the plan rule allows (an action outside the approved plan, a change to production data).

Traces to PRD: §6 S-4, O-5 · Sources: R-10, DM-06 ("modo de ejecución continua entre ellos") · Decision: D-22 · BL-13

**Scenario — success:** GIVEN the *what* gate approved WHEN architecture and tasks are generated THEN no question is
asked until the *how* gate.
**Scenario — error:** GIVEN a step outside the approved plan WHEN it is reached THEN the agent asks, and the question is
recorded as a plan exception, not a gate.

### 4.6 REQ-W2-039 — Granular gates remain available
The method SHALL keep the seven per-phase gates available through the gate settings and a `--granular-gates` flag;
in 3.13 the default SHALL be granular with merged gates opt-in; in 4.0 the default SHALL be merged.

Traces to PRD: §6 S-4, S-13, O-12 · Sources: R-10 (`--granular-gates`) · Decision: D-22, D-24 · BL-13

**Scenario — success:** GIVEN a 3.13 project without gate settings WHEN a change runs THEN it asks the seven gates as
in 3.12.
**Scenario — error:** GIVEN a gate setting other than `merged` or `granular` WHEN validated THEN the value is refused.

### 4.7 REQ-W2-040 — `-y` is an automatic approval, never production
WHEN a phase skill is invoked with `-y`, the state tool SHALL record the approval with `role: auto`; IF `-y` is used for
the production approval, THEN it SHALL refuse; the dashboard and the metrics SHALL show automatic approvals apart from
human ones.

Traces to PRD: §6 S-4 · Sources: R-10 ("-y registra role auto y queda prohibido en prod"), H-06, DM-06 · MODIFIES REQ-W1-006 · BL-13

**Scenario — success:** GIVEN `-y` on requirements WHEN recorded THEN `approvals.requirements.role` is `auto`.
**Scenario — error:** GIVEN `-y` at the release gate WHEN production would be approved THEN the state tool refuses with
"production approval is never automatic".

### 4.8 REQ-W2-041 — Grill asks in batches
WHEN the grill skill interviews the human, it SHALL ask up to four questions per question batch, each with its
recommended option first, and SHALL infer the stack questions from the repository and only ask to confirm them.

Traces to PRD: §6 S-4, O-5 · Sources: R-10, AG-08 · BL-13

**Scenario — success:** GIVEN a repository with a lockfile and a CI file WHEN grill reaches the stack branch THEN it
shows the inferred stack and asks one confirmation.
**Scenario — error:** GIVEN a branch with six open questions WHEN grill asks THEN no batch holds more than four.

### 4.9 REQ-W2-042 — *Request changes* keeps the phase and records why
WHEN the human answers *Request changes* at a gate, the method SHALL record the outcome with the human's reason
(REQ-W2-001), keep the change in its current phase and return to the phase skill that owns the requested change.

Traces to PRD: §6 S-4, S-1 · Sources: R-10 (tasa de rechazo por gate) · BL-13

**Scenario — success:** GIVEN the *what* gate WHEN the human requests a change to one requirement THEN the outcome is
recorded and requirements are regenerated.
**Scenario — error:** GIVEN *Request changes* with no reason WHEN recorded THEN the method asks for the reason once and
records "no reason given" if none is given.

---

## Requirement 5: Release per change (R-08)

### 5.1 REQ-W2-043 — Every commit carries the change trailer
WHEN the impl skill (or any phase skill) commits for a change, it SHALL add the trailer `Karvey-Change:
<change-id>` to the commit message.

Traces to PRD: §6 S-5, O-6 · Sources: R-08, DM-03 · Decision: D-26 · BL-11

**Scenario — success:** GIVEN a task of `wave2-structural` WHEN it is committed THEN the message ends with
`Karvey-Change: wave2-structural`.
**Scenario — error:** GIVEN a skill text that shows a commit command without the trailer WHEN the linter runs THEN
it is reported.

### 5.2 REQ-W2-044 — Missing trailers are detected at commit time
WHERE the optional commit-message guard is enabled, WHEN a commit on a feature branch of an active change lacks the
change trailer, the guard SHALL warn in 3.13 and block when the project sets it blocking.

Traces to PRD: §6 S-5 · Sources: DM-03 ("commit-msg hook opcional") · Decision: D-26, D-24 · BL-11

**Scenario — success:** GIVEN the guard enabled and a trailer present WHEN committing THEN nothing is printed.
**Scenario — error:** GIVEN the guard in blocking mode and no trailer WHEN committing THEN the commit is blocked with
the trailer to add.

### 5.3 REQ-W2-045 — The release manifest
BEFORE the production PR is opened, the deploy skill SHALL compute the release manifest: every commit between
production and the release head, mapped to its change-id by trailer, with each change's version, lane and QA state.

Traces to PRD: §6 S-5, O-6, AC-5 · Sources: R-08 (paso 2.8-bis), DM-03, PM-04, H-21 · Decision: D-26 · BL-11

**Scenario — success:** GIVEN two changes on the integration branch WHEN the manifest runs THEN it lists both with
their commits.
**Scenario — error:** GIVEN a commit with no trailer WHEN the manifest runs THEN it is listed under "unmapped".

### 5.4 REQ-W2-046 — Manifest verdict
WHEN the manifest contains an unmapped commit or a change without `qa.approved` (or QA skipped by its lane), the
deploy skill SHALL warn in 3.13, SHALL refuse in 4.0, and the prod gate SHALL apply the same verdict when the
manifest is blocking.

Traces to PRD: §6 S-5, S-13, O-6, AC-5 · Sources: R-08 ("empezar en modo advertir"), PM-04 · Decision: D-24, D-26 · BL-11

**Scenario — success:** GIVEN every change in the manifest QA-approved WHEN the verdict runs THEN it is `pass`.
**Scenario — error:** GIVEN a blocking manifest and one change without QA WHEN the merge to production is attempted
THEN the prod gate blocks and names the change.

### 5.5 REQ-W2-047 — The PR lists every change; each gets its approval
WHEN the production PR is opened, its body SHALL list every change-id and version of the manifest, and WHEN the
human approves production the approval SHALL be recorded for every change of the manifest.

Traces to PRD: §6 S-5, O-6 · Sources: R-08, PM-04 · Decision: D-26, D-03, D-10 · BL-11

**Scenario — success:** GIVEN a manifest of two changes WHEN production is approved THEN both changes hold the same
production approval record.
**Scenario — error:** GIVEN a PR body that lists one change while the manifest has two WHEN the release gate runs THEN
it reports the mismatch.

### 5.6 REQ-W2-048 — Integration by PR
WHERE the integration branch differs from production, the method SHALL integrate a feature branch through a PR to
the integration branch and SHALL NOT instruct a local merge followed by a direct push to it.

Traces to PRD: §6 S-5 · Sources: R-08 ("la integración a dev pasa por PR"), DM-03 · Decision: D-26 · MODIFIES REQ-W1-034 · BL-11

**Scenario — success:** GIVEN `integration: dev`, `production: master` WHEN a change integrates THEN a PR to `dev` is
opened.
**Scenario — error:** GIVEN a skill text that says to merge locally into integration and push WHEN the linter runs
THEN it is reported.

### 5.7 REQ-W2-049 — Branch mode, trunk recommended
The method SHALL support `branch_flow.mode` with `trunk` and `env-branches`, SHALL derive `trunk` when integration
equals production, and SHALL recommend `trunk` when a project is set up.

Traces to PRD: §6 S-5 · Sources: R-08 (`branch_flow.mode`), DM-03 · Decision: D-26 · MODIFIES REQ-W1-035 · BL-11

**Scenario — success:** GIVEN integration = production = `main` WHEN the mode is read THEN it is `trunk`.
**Scenario — error:** GIVEN `mode: trunk` with integration ≠ production WHEN validated THEN the contradiction is
reported.

### 5.8 REQ-W2-050 — A release branch as the way out
WHEN the manifest verdict is not `pass`, the deploy skill SHALL offer a `release/*` branch from production with only
the approved changes cherry-picked, besides waiting.

Traces to PRD: §6 S-5 · Sources: R-08 ("ofrecer release/* + cherry-pick"), PM-04 · BL-11

**Scenario — success:** GIVEN one unapproved change in the manifest WHEN the verdict is shown THEN the option lists the
commits it would cherry-pick.
**Scenario — error:** GIVEN a cherry-pick conflict WHEN the release branch is built THEN the deploy skill stops and
reports the conflicting commit, without resolving it itself.

### 5.9 REQ-W2-051 — `approvals.deploy` is retired
The method SHALL record deploys only in `spec.json:deploys` (REQ-W2-002), SHALL treat `approvals.deploy` as a legacy
key reported as a warning, and the migration SHALL remove it showing the diff.

Traces to PRD: §6 S-5 · Sources: F-28 · BL-46

**Scenario — success:** GIVEN a new change WHEN it deploys THEN no `approvals.deploy` is written.
**Scenario — error:** GIVEN a legacy `approvals.deploy` WHEN validated THEN a warning names the key and the migration.

### 5.10 REQ-W2-052 — Where the production OK is written, in order
The deploy rule SHALL state that at deploy the production OK text lives in the PR body or PR approval, and that at
archive it is written as `D-NN` into the decision log on the archive branch and copied into `approvals.prod`.

Traces to PRD: §6 S-5 · Sources: F-29 · Decision: D-03 · BL-47

**Scenario — success:** GIVEN a change archived WHEN the decision log is read THEN the D-NN of its production OK was
committed on `chore/archive-{id}`.
**Scenario — error:** GIVEN a deploy step that commits the decision log on integration or production WHEN the guard
runs THEN it is blocked.

Revision 1 (2026-09-26, F-61, D-37, QA): the release-manifest path had no rule for how many human OKs it needs, and
the tool let one project-wide prod marker approve every change of the manifest without a binding. ON the
release-manifest path only, one production OK SHALL cover every change the release manifest of
`origin/{production}..{head}` lists, and only when the production PR body the human approved names exactly those
changes; that OK SHALL be the approving change's own prod marker or the project-wide one, SHALL be consumed once,
and each change's release-ledger record SHALL be bound to the reviewed head commit for 24 h (D-35), name the
manifest it covers, and match the approving change's own record. Every other production path SHALL stay one OK
per change (BUG-41), and a reopen SHALL supersede the reopened change's record (D-36).

**Scenario — success (revision 1):** GIVEN a manifest of two changes and a PR body that lists both WHEN the human
gives one production OK and `approve prod --manifest` runs THEN both ledger records name the same head commit and
manifest, the one marker is consumed, and `check-prod` passes for each at that commit.
**Scenario — error (revision 1):** GIVEN a PR body that omits a change of the manifest, or names a change outside
it, or a new commit after the OK WHEN the approval is recorded or the merge is checked THEN it is refused and names
the difference or the commit.

### 5.11 REQ-W2-053 — Deployed without the local ledger
WHERE the release ledger of the clone is absent, the state tool SHALL accept `advance {id} deployed` with a `D-NN`
reference and a pipeline-run URL, and SHALL record the transition as attested rather than measured.

Traces to PRD: §6 S-5 · Sources: F-30 · BL-48

**Scenario — success:** GIVEN another clone than the one that deployed WHEN `advance deployed --ref D-NN --pipeline-run
URL` runs THEN the phase is `deployed` with `attested: true`.
**Scenario — error:** GIVEN no ledger and no pipeline-run URL WHEN `advance deployed` runs THEN it refuses and names
both accepted evidences.

---

## Requirement 6: Living spec merged before production (R-17 timing)

### 6.1 REQ-W2-054 — Merge on the change branch, before the production PR
BEFORE the production PR of a change is opened, the method SHALL merge the change's `spec-delta.md` into the living
spec on the change branch with the spec-merge tool, showing the dry-run first.

Traces to PRD: §6 S-6, O-11, AC-6 · Sources: R-17 (momento de DM, script de AG), DM-09 · MODIFIES REQ-W1-067 · BL-20

**Scenario — success:** GIVEN a change at qa approved WHEN deploy prepares the production PR THEN the living spec
update is a commit of the change branch in that PR.
**Scenario — error:** GIVEN a merge conflict in the living spec WHEN the tool runs THEN it stops, prints the dry-run
diff and the deploy does not open the PR.

### 6.2 REQ-W2-055 — Archive only moves and closes
WHEN a change is archived, the archive skill SHALL move the change folder and close its Epic, and SHALL NOT merge the
spec-delta again; IF the delta is not yet merged, THEN it SHALL report it and merge it on the archive branch.

Traces to PRD: §6 S-6 · Sources: R-17 ("archive queda en mover la carpeta y cerrar la Epic") · MODIFIES REQ-W1-067 · BL-20

**Scenario — success:** GIVEN the delta merged before production WHEN archive runs THEN the spec-merge tool reports
"already merged" and changes nothing.
**Scenario — error:** GIVEN a legacy change whose delta was never merged WHEN archive runs THEN it reports it and merges
it on `chore/archive-{id}`.

### 6.3 REQ-W2-056 — A deployed change without its delta is visible
The linter SHALL fail when a change in `deployed` or later has an unmerged spec-delta, and the dashboard SHALL flag a
change `deployed` without archive for more than 7 days.

Traces to PRD: §6 S-6, O-11 · Sources: R-17 (`karvey-context` avisa), DM-09 · BL-20

**Scenario — success:** GIVEN every deployed change merged WHEN the linter runs THEN the check passes.
**Scenario — error:** GIVEN a change deployed 9 days ago and not archived WHEN the dashboard runs THEN it shows
"deployed 9 d, not archived".

---

## Requirement 7: Test-first and traceability (R-12)

### 7.1 REQ-W2-057 — A test task before each implementation task
WHEN tasks are generated, the tasks skill SHALL create, for each requirement the task set covers, a test task that
precedes its implementation task and states the failing result expected before the implementation.

Traces to PRD: §6 S-7, O-7 · Sources: R-12, DM-07 · BL-15

**Scenario — success:** GIVEN requirement 2.3 WHEN tasks are generated THEN a test task for 2.3 is a dependency of its
implementation task.
**Scenario — error:** GIVEN a requirement with no test task and no `manual` exception WHEN the *how* gate summary is
built THEN the requirement is listed as uncovered.

### 7.2 REQ-W2-058 — Tests name their requirement
The method SHALL require every automated test written for a change to reference the requirement it verifies by ID in
its name or in a tag.

Traces to PRD: §6 S-7, O-7 · Sources: R-12 (`test_REQ_1_2_*` o `@req 1.2`), DM-07 · BL-15

**Scenario — success:** GIVEN a test tagged `@req REQ-W2-013` WHEN the trace is built THEN it maps to REQ-W2-013.
**Scenario — error:** GIVEN a new test with no requirement reference WHEN the trace is built THEN it is listed as
"unmapped test".

### 7.3 REQ-W2-059 — The test phase starts from the architecture's coverage plan
WHEN the test phase starts, it SHALL read the test coverage plan of `architecture.md` and SHALL report every planned
item it did not execute.

Traces to PRD: §6 S-7 · Sources: R-12 ("karvey-test no consume el Test coverage plan"), DM-07 · BL-15

**Scenario — success:** GIVEN a coverage plan of 12 items WHEN the test phase finishes THEN it reports 12 executed.
**Scenario — error:** GIVEN a planned item not run WHEN the phase closes THEN it lists "planned, not executed" with the
item.

### 7.4 REQ-W2-060 — Trace generated by a script
WHEN the test phase closes, the method SHALL generate `changes/{id}/traceability.md` by script, mapping each
requirement to its tasks, the commits carrying the change trailer, its tests and their last result.

Traces to PRD: §6 S-7, O-7, AC-7 · Sources: R-12, DM-07 · Decision: D-26 (trailer) · BL-15

**Scenario — success:** GIVEN the trailer on every commit WHEN the trace is generated THEN each requirement row has at
least one commit.
**Scenario — error:** GIVEN a requirement with no commit WHEN the trace is generated THEN its row reads "no commit".

### 7.5 REQ-W2-061 — Evidence lives inside the change
The test and QA phases SHALL write their plan and evidence under `changes/{id}/`, not in a file shared across changes.

Traces to PRD: §6 S-7 · Sources: R-12 ("mover la evidencia a changes/{id}/"), DM-07 · BL-15

**Scenario — success:** GIVEN a test run WHEN evidence is written THEN it is `changes/{id}/test_evidence.md`.
**Scenario — error:** GIVEN a skill text pointing to `docs/test_evidence.md` WHEN the linter runs THEN it is reported.

### 7.6 REQ-W2-062 — Coverage gate
WHEN QA or archive runs, the method SHALL check that every ADDED or MODIFIED requirement has at least one green automated
test or a `manual` exception with its reason; the check SHALL be warn in 3.13.

Traces to PRD: §6 S-7, O-7 · Sources: R-12 ("gate: todo requisito ADDED/MODIFIED tiene un test verde o una excepción manual") · Decision: D-24 · BL-15

**Scenario — success:** GIVEN every requirement covered WHEN QA runs THEN the coverage line reads "N/N".
**Scenario — error:** GIVEN two uncovered requirements WHEN QA runs THEN they are listed and the gate summary shows the
warning.

### 7.7 REQ-W2-063 — QA runs the suite or cites the exact run
WHEN QA states that tests or the build pass, it SHALL either run them or cite the CI run of the exact commit reviewed;
IF neither exists, THEN the statement SHALL read "not evaluated".

Traces to PRD: §6 S-7, S-3 · Sources: R-12 ("QA ejecuta la suite o cita el run de CI"), DM-07, H-28 context · BL-15

**Scenario — success:** GIVEN a CI run for the reviewed commit WHEN QA writes the result THEN it cites the run.
**Scenario — error:** GIVEN no run and no execution WHEN QA writes the checklist THEN "tests pass" is replaced by "not
evaluated".

---

## Requirement 8: Deterministic security tools (R-13)

### 8.1 REQ-W2-064 — QA runs the available tools per category
WHEN the QA security dimension runs, it SHALL run the tools available in the environment for secrets, static
analysis, dependency vulnerabilities and infrastructure-as-code, and SHALL cite each tool's command, version and
result summary.

Traces to PRD: §6 S-8, O-8 · Sources: R-13, DM-08 · BL-16

**Scenario — success:** GIVEN a secrets scanner installed WHEN QA runs THEN the review cites its command and "0 findings".
**Scenario — error:** GIVEN a tool that exits with an execution error WHEN QA runs THEN the category is "not evaluated
(tool error)", not "pass".

### 8.2 REQ-W2-065 — A missing tool is "not evaluated"
IF no tool is available for a category, THEN the QA review SHALL mark that category "not evaluated" and the dashboard
SHALL count it; the model's reading SHALL NOT turn it into "pass".

Traces to PRD: §6 S-8, O-8 · Sources: R-13, DM-08, engineering-standards "not evaluated ≠ conformant" · BL-16

**Scenario — success:** GIVEN no IaC in the change WHEN QA runs THEN the IaC category is "not applicable".
**Scenario — error:** GIVEN IaC in the change and no IaC scanner WHEN QA runs THEN the category is "not evaluated".

### 8.3 REQ-W2-066 — Triage and suppressions carry a reason
WHEN a tool finding is judged a false positive, the QA review SHALL record the suppression with its reason and scope;
the model SHALL additionally review what tools do not cover (authorisation per object, tenant isolation, business logic).

Traces to PRD: §6 S-8 · Sources: R-13 ("el LLM tría falsos positivos y cubre lo que las herramientas no ven") · BL-16

**Scenario — success:** GIVEN a test fixture key flagged as a secret WHEN QA triages it THEN the suppression names the
file and why.
**Scenario — error:** GIVEN a suppression without a reason WHEN the review is validated THEN it is reported.

### 8.4 REQ-W2-067 — Tool invocation is safe
The security tools SHALL be run with fixed command templates, and no value read from `project.json` or the change
SHALL reach a tool command without the validation of REQ-W1-093.

Traces to PRD: §6 S-8, §9 (Security Tier 2) · Sources: R-13 · BL-16

**Scenario — success:** GIVEN a repository path from `project.json` WHEN a scanner runs THEN the path was validated.
**Scenario — error:** GIVEN a `project.json` value containing `;` WHEN a scanner command is built THEN it is refused.

### 8.5 REQ-W2-068 — The tools move into the PR pipeline
WHEN the infra phase designs the CI/CD pipeline, it SHALL propose running the same security tool categories in the PR
pipeline, so that the security verdict belongs to CI rather than to a session.

Traces to PRD: §6 S-8 · Sources: R-13 ("karvey-infra propone llevar estas herramientas al pipeline de PR"), DM-08 · BL-16

**Scenario — success:** GIVEN an infra phase WHEN `infra.md` is generated THEN it contains a security-scan stage.
**Scenario — error:** GIVEN a pipeline without the stage WHEN the *how* gate summary is built THEN it lists the missing
stage as a deviation.

---

## Requirement 9: Deterministic scripts (R-20)

### 9.1 REQ-W2-069 — Release gate as a script
WHEN deploy runs its pre-checks, it SHALL run the release gate, which SHALL return a structured verdict (QA gate, tests,
CHANGELOG, version match, hotfix triplet, manifest) and a non-zero exit when any item fails; the skill SHALL explain the
verdict, not recompute it.

Traces to PRD: §6 S-9, O-9 · Sources: R-20, AG-10 · BL-23

**Scenario — success:** GIVEN every item passing WHEN the gate runs THEN it exits 0 with `verdict: pass`.
**Scenario — error:** GIVEN a CHANGELOG without an `[Unreleased]` line for the change WHEN the gate runs THEN it exits
non-zero naming the item.

### 9.2 REQ-W2-070 — IDs reserved by a tool
WHEN a new `BUG`, `D`, `BL`, `F` or `Q` identifier is needed, the method SHALL obtain it from the id tool, which SHALL
take a lock, scan every source including remote branches, and reserve the number before returning it.

Traces to PRD: §6 S-9, O-9 · Sources: R-20, AG-07, PM-13, H-35 · BL-23

**Scenario — success:** GIVEN two sessions requesting a `BUG` id at the same time WHEN both finish THEN they hold
different numbers.
**Scenario — error:** GIVEN the lock cannot be taken WHEN an id is requested THEN the tool fails with the reason and
returns no number.

### 9.3 REQ-W2-071 — Qualified and unbounded IDs
The id tool SHALL emit repository-qualified IDs (`BUG-NN@{repo}`) for cross-repo indexes, and no skill SHALL bound
Epic numbers to a fixed range.

Traces to PRD: §6 S-9 · Sources: R-20 (`BUG-NN@repo`, `E{1..99}`), AG-07, H-33 · BL-23

**Scenario — success:** GIVEN two repos each with BUG-12 WHEN the global index is written THEN the rows read
`BUG-12@a` and `BUG-12@b`.
**Scenario — error:** GIVEN a skill text with `E{1..99}` WHEN the linter runs THEN it is reported.

### 9.4 REQ-W2-072 — Health score as a script
WHEN the health skill computes its score, it SHALL use the health score script with explicit sub-score functions and
the time zone of `KARVEY_TZ`, so that the same inputs produce the same score.

Traces to PRD: §6 S-9, O-9 · Sources: R-20, AG-10 · BL-23

**Scenario — success:** GIVEN the same inputs twice WHEN the score is computed THEN it is identical.
**Scenario — error:** GIVEN an invalid `KARVEY_TZ` WHEN the score runs THEN it prints the fallback zone used, not a
silent default.

### 9.5 REQ-W2-073 — Evidence wrapper
The method SHALL provide an evidence wrapper that runs a command and appends its command line, exit code, duration,
output hash and time to `changes/{id}/evidence.jsonl`, and phase-close claims SHALL cite lines of that file where a
command proves them.

Traces to PRD: §6 S-9, S-3 · Sources: R-20, AG-12, B-12 (proposal, cheap piece) · BL-23

**Scenario — success:** GIVEN `karvey-evidence -- <test command>` WHEN it finishes THEN one JSON line is appended and the
command's exit code is returned.
**Scenario — error:** GIVEN no active change WHEN the wrapper runs THEN it still runs the command and says the evidence
was not recorded and why.

### 9.6 REQ-W2-074 — Cross-repo decision references validate
The spec schema SHALL accept decision references of the form `D-NN@{repo}` as the multi-agent rule prescribes, and the
state tool's `next` SHALL print each blocker once.

Traces to PRD: §6 S-9 · Sources: F-26 · BL-44

**Scenario — success:** GIVEN `decisions: ["D-12@ops"]` WHEN validated THEN no error.
**Scenario — error:** GIVEN `decisions: ["D12"]` WHEN validated THEN the value is reported with the accepted patterns.

---

## Requirement 10: Post-deploy verification with thresholds (R-23)

### 10.1 REQ-W2-075 — A post-deploy contract per service
WHEN the infra phase runs for a deployable service, it SHALL write in `infra.md` a post-deploy contract with health
endpoints, critical routes, thresholds (error rate, latency against the production baseline, new server errors), the
observation window, the metrics source and the rollback command.

Traces to PRD: §6 S-10, O-10 · Sources: R-23, DM-10 · BL-26

**Scenario — success:** GIVEN a web service WHEN infra is generated THEN its contract lists thresholds and a rollback
command.
**Scenario — error:** GIVEN a contract without a rollback command WHEN the *how* gate summary is built THEN it is listed
as incomplete.

### 10.2 REQ-W2-076 — Deploy runs the contract and keeps evidence
WHEN a production deploy finishes, the deploy skill SHALL run the post-deploy contract, SHALL write the probe results to
`changes/{id}/deploy_evidence.md`, SHALL record the result in `deploys` (REQ-W2-002), and SHALL call the step
"post-deploy verification", keeping "canary" only where the platform splits traffic.

Traces to PRD: §6 S-10, O-10 · Sources: R-23, DM-10, PM-05 · BL-26

**Scenario — success:** GIVEN all probes inside thresholds WHEN the window ends THEN the verification is `pass`.
**Scenario — error:** GIVEN error rate above the threshold WHEN a probe runs THEN the verification is `regression`.

### 10.3 REQ-W2-077 — No contract is "not evaluated"
IF a deployed service has no post-deploy contract or no thresholds, THEN the verification SHALL be recorded as "not
evaluated" with a recommendation to add the contract, never as `pass`.

Traces to PRD: §6 S-10, O-10 · Sources: R-23 ("no hay umbrales"), DM-10 · BL-26

**Scenario — success:** GIVEN a contract WHEN deploy verifies THEN the result is `pass` or `regression`.
**Scenario — error:** GIVEN no contract WHEN deploy verifies THEN the result is "not evaluated".

### 10.4 REQ-W2-078 — A regression proposes the rollback and opens the incident
WHEN the verification is `regression`, the deploy skill SHALL present the contract's rollback command for the human's
approval, SHALL record the rollback taken in `deploys`, and SHALL open a `BUG-NN` incident.

Traces to PRD: §6 S-10, S-1 · Sources: R-23, DM-10 (rollback definido), incident rule · BL-26

**Scenario — success:** GIVEN a regression WHEN the human approves the rollback THEN it runs and `deploys[n].rollback`
records it.
**Scenario — error:** GIVEN a regression WHEN the agent would run the rollback without the human's approval THEN the plan
gate blocks it.

---

## Requirement 11: Knowledge sync optional (D-27)

### 11.1 REQ-W2-079 — No text requires graphify
No skill, rule or README SHALL describe graphify (or any knowledge-sync tool) as required; a project without
`knowledge_sync`, or with `none`, SHALL run every phase without a sync step, and the linter SHALL check it.

Traces to PRD: §6 S-11 · Sources: R-16, panel §6.8 · Decision: D-27 · MODIFIES REQ-W1-061

**Scenario — success:** GIVEN `knowledge_sync` absent WHEN archive runs THEN no sync step is attempted or mentioned as
missing.
**Scenario — error:** GIVEN a skill text stating "graphify is required" WHEN the linter runs THEN it is reported.

---

## Requirement 12: Deferred Wave 1 backlog

### 12.1 REQ-W2-080 — Import resumes through recorded gates
WHEN the import skill brings existing artifacts into a change, it SHALL record each imported artifact as generated,
SHALL ask the human the gate question of each imported gate in order (merged gates when enabled), and SHALL resume at
the first gate the human did not approve.

Traces to PRD: §6 S-12 · Sources: F-31 · BL-49

**Scenario — success:** GIVEN imported requirements and architecture WHEN the human approves the *what* gate only THEN the
change resumes at the *how* gate.
**Scenario — error:** GIVEN imported artifacts WHEN the import would mark any gate approved without the human THEN the
state tool refuses.

### 12.2 REQ-W2-081 — One decision-log shape
The method SHALL use `{ops_repo}/docs/spec/decisions.md` as the one decision log, SHALL read per-period decision files
where they exist, and SHALL document a migration note for them.

Traces to PRD: §6 S-12 · Sources: F-32, L-30 · BL-50

**Scenario — success:** GIVEN a project with per-period files WHEN a decision is looked up THEN it is found and the
migration note is shown once.
**Scenario — error:** GIVEN both shapes with the same D-NN WHEN the decisions skill reads them THEN it reports the
duplicate.

### 12.3 REQ-W2-082 — The statusline failure line has a table case
The guard tables SHALL include a case for the statusline's failure line, and the hooks README SHALL anchor it.

Traces to PRD: §6 S-12 · Sources: F-33 (rest) · MODIFIES REQ-W1-051

**Scenario — success:** GIVEN the case WHEN the tables run THEN the failure line is asserted.
**Scenario — error:** GIVEN the README describes the line and no case exists WHEN the linter runs THEN it is reported.

---

## Requirement 13: Rollout 3.13 → 4.0 and dogfooding (D-24)

### 13.1 REQ-W2-083 — Every new check has a mode
Every check this change introduces SHALL declare its mode in one place (advisory, warn or blocking), SHALL default to
advisory or warn in 3.13, and SHALL be switchable per project.

Traces to PRD: §6 S-13, O-12 · Sources: panel Ola 2 plan · Decision: D-24

**Scenario — success:** GIVEN a fresh 3.13 project WHEN the checks are listed THEN none is blocking by default.
**Scenario — error:** GIVEN a check without a declared mode WHEN the linter runs THEN it is reported.

### 13.2 REQ-W2-084 — Nothing that passed in 3.12 fails in 3.13
WHILE a project uses the 3.13 defaults, no Wave 2 check SHALL refuse an operation that 3.12.0 allowed.

Traces to PRD: §6 S-13, O-12, AC-8 · Sources: R-01 (modo advertencia), panel Ola 2 · Decision: D-24

**Scenario — success:** GIVEN a 3.12 project upgraded to 3.13 WHEN a change runs its whole pipeline THEN every step it
passed before still passes, with warnings.
**Scenario — error:** GIVEN a 3.13 default that refuses a 3.12-valid operation WHEN the guard tables run THEN the
compatibility case fails.

### 13.3 REQ-W2-085 — 4.0 flips exactly the D-24 defaults
WHEN 4.0.0 is released, the defaults that become blocking SHALL be exactly: the spec schema strict (with `lane`,
`phase_history` and `skipped` required), merged gates, and the blocking release manifest; every other Wave 2 check SHALL
keep its 3.13 default unless a later decision changes it.

Traces to PRD: §6 S-13, O-12 · Sources: panel Ola 2 ("es breaking porque…") · Decision: D-24, D-23

**Scenario — success:** GIVEN 4.0.0 WHEN the defaults are listed THEN the three are blocking and judges stay advisory.
**Scenario — error:** GIVEN a 4.0 default outside the three with no decision reference WHEN the linter runs THEN it is
reported.

### 13.4 REQ-W2-086 — 4.0 only on measured data
The 4.0.0 release SHALL be proposed only when the readiness report (REQ-W2-010) shows at least 4 changes measured under
3.13, and its approval SHALL be recorded as its own decision.

Traces to PRD: §6 S-13, O-1, O-12 · Sources: panel Ola 2 ("después de 4–6 cambios medidos") · Decision: D-24

**Scenario — success:** GIVEN 4 measured changes WHEN 4.0 is proposed THEN the readiness report is attached.
**Scenario — error:** GIVEN 2 measured changes WHEN 4.0 is proposed THEN the proposal states "not ready: 2 of 4".

### 13.5 REQ-W2-087 — Migration to the Wave 2 shape
WHEN `validate --fix` runs on a pre-3.13 `spec.json`, the state tool SHALL propose a lane inferred from the recorded
skipped phases, SHALL remove `approvals.deploy` into `deploys` only when it holds data, SHALL show the diff before
writing, and SHALL NOT create or flip any approval.

Traces to PRD: §6 S-13 · Sources: R-01 (`--fix`), R-09 · Decision: D-24 · MODIFIES REQ-W1-009 · BL-46

**Scenario — success:** GIVEN a legacy change with mockup and design skipped WHEN `--fix` runs THEN it proposes
`lane: standard` and shows the diff.
**Scenario — error:** GIVEN `--fix` run twice WHEN compared THEN the second run changes nothing.

### 13.6 REQ-W2-088 — Built with itself
This change SHALL run in the `standard` lane on this repository in trunk mode, SHALL carry the change trailer on every
commit, SHALL take the metrics baseline before enabling its own lane and gate defaults, and SHALL be the first change
counted by the readiness report.

Traces to PRD: §6 S-13, §9, AC-1, AC-5 · Sources: panel Ola 1 (dogfooding), H-22 · Decision: D-04, D-26

**Scenario — success:** GIVEN this change's production PR WHEN its manifest is computed THEN every commit maps to
`wave2-structural` (or to another change with its own trailer).
**Scenario — error:** GIVEN a commit of this change without the trailer WHEN the manifest runs THEN it is listed as
unmapped and fixed before the production gate.

---

## Explicit exclusions

- **Wave 3** (R-15, R-19, R-24..R-30): context budget and `_core.md`, stakeholder reports and "your turn" events,
  Q-NN and risks, cost per change beyond the judges' cost, project design system, WBS, portfolio, WSJF, portability.
  The release manifest is produced here; the client-facing report that reads it is Wave 3.
- **Judges blocking by default:** D-23 keeps judges advisory; `mode: blocking` exists as an opt-in only. The design
  judge with a contrast checker (R-26/AG-12) is Wave 3 — the default judged phases are requirements, architecture and
  qa.
- **A judge budget that cuts runs:** excluded by D-30; cost is measured only.
- **Writing the owner's personal global instructions:** the change delivers the diff (REQ-W2-020); the owner applies it
  (D-01, D-11, D-25).
- **Running `--fix` or the lane migration in other repositories:** each repository's own docs PR.
- **Emergent backlog** BL-34..BL-43 and **BL-51** (`project-upgrade`, D-20): not in this change.
- **ID collisions already present** in other repositories: the id tool prevents new ones; renumbering existing IDs is
  not in scope.
- **Behaviour that does not change:** the bug/spec-gap/emergent router and "who observes does not route" (judges
  included), the Iron Law, production approval never delegated and never automatic (D-10 words still required at the
  release gate), the prod gate on by default (D-02), `verification.md`, one agent by default with the team layer
  opt-in, EARS with PRD traceability, the spec↔mockup validation in `feature-ui`, estimates in AI minutes + review
  (REQ-W1-042..044), `[human]` tasks, logical tracker states with adapters, and every item of the panel's §5.

## Open points for the owner

Decided while writing and applied as the recommended default (D-21 standing instruction); each can be changed at
the *what* gate. D-29 (patch criterion) and D-30 (judge budget) are no longer open.

1. **Merged gates in 3.13.0 are opt-in** (granular default), merged default in 4.0.0 — the reading of D-22 + D-24
   (REQ-W2-039). *Recommended.*
2. **Release gate (gate 3) = qa + prod in one question**; the production part is recorded only when the human's prompt
   also carries D-10's production word, otherwise only `qa` is recorded (REQ-W2-034, REQ-W2-047).
3. **Default judge lenses**: requirements = domain + methods; architecture = security + methods + agents/cost; qa =
   fiscal + security; per lane 0 / 2 / 3 (REQ-W2-024, REQ-W2-031).
4. **The AG-12 / B-12 cheap pieces are in scope**: the clean-context fiscal as the qa judge's lens (REQ-W2-032) and the
   evidence wrapper (REQ-W2-073), both advisory. B-12 was "proposed, not decided".
5. **Judge cost when the runtime exposes none**: recorded as an estimate from input/output size, marked `estimated`
   (REQ-W2-030).
6. **`approvals.deploy` is retired** in favour of `deploys[]` (BL-46, REQ-W2-051).
7. **Ledger fallback**: `advance deployed --ref D-NN --pipeline-run URL`, recorded as attested (BL-48, REQ-W2-053).
8. **Import**: artifacts recorded as generated, the human is asked per gate (BL-49, REQ-W2-080).
9. **Decision log**: the single `docs/spec/decisions.md` wins; per-period files are read with a migration note (BL-50,
   REQ-W2-081).
10. **Stall threshold** for "deployed, not archived": 7 days, the same as Wave 1's stall default (REQ-W2-056).
11. **Readiness threshold for 4.0**: at least 4 measured changes (the low end of the panel's 4–6) (REQ-W2-086).
12. **Checks beyond D-24's three stay advisory/warn in 4.0** (lane-size check, coverage gate, commit-message trailer
    guard, judges) until a later decision reads the readiness data (REQ-W2-085).
13. **`-y` = `role: auto`** is accepted at non-production gates and counted apart in the metrics; it never satisfies
    the production gate (REQ-W2-040).
