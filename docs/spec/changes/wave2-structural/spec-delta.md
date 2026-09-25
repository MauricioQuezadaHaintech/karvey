# Spec Delta: wave2-structural

Against the living spec `docs/spec/specs/method/spec.md` (capability `method`). Baseline: the REQ-TEAM-* blocks
already there **plus** the REQ-W1-* (and carried REQ-ADP-*) blocks of `wave1-hardening`'s `spec-delta.md`, treated
as already merged (that change ships first, as 3.12.0). Single spec-delta path: this file, at the change root.
Merge order: `karvey-spec-merge --dry-run wave2-structural` (run 2026-09-25) parses this file and refuses it only because
the nine MODIFIED REQ-W1 blocks are not in the living spec yet — wave1's delta must merge first.
Scenarios for every block are in `requirements.md`; the living spec keeps the compact form it already uses.

Summary: **ADDED 88** (REQ-W2-001..088) · **MODIFIED 9** (REQ-W1-006, REQ-W1-007, REQ-W1-009, REQ-W1-034,
REQ-W1-035, REQ-W1-042, REQ-W1-051, REQ-W1-061, REQ-W1-067) · **REMOVED 0**.

## ADDED Requirements

### ADDED by `wave2-structural` (3.13.0 advisory; D-24 defaults blocking in 4.0.0)

Traced to `docs/spec/changes/wave2-structural/prd.md`.

### Flow metrics and a retro on the method's artifacts (R-14) — first
- **REQ-W2-001** — Gate outcomes are recorded. WHEN a gate question is answered, the state tool SHALL append to `spec.json` the outcome (`approved` or `changes_requested`), the phase or phases it covered, who answered, the role, the reference and an ISO 8601 timestamp with time and zone, and SHALL record the time each approval was first marked generated; it SHALL NOT rewrite earlier outcomes. *(Traces: PRD §6 S-1, O-2 · Sources: R-14, R-10 (tasa de rechazo por gate), PM-05 (espera de aprobación), DM-11 · BL-17)*
- **REQ-W2-002** — Deploy records. WHEN a deploy to an environment finishes, the method SHALL append to `spec.json:deploys` an entry with the environment, the version, the time, the post-deploy verification result (REQ-W2-076) and the rollback taken, if any; entries SHALL be append-only. *(Traces: PRD §6 S-1, S-10, O-2, O-10 · Sources: R-14 (`deploys[{env, version, canary, rollback}]`), PM-05 · BL-17, BL-26)*
- **REQ-W2-003** — Metrics per lane and period. WHEN the metrics view is requested for a project and a period, the method SHALL compute, per lane and for all lanes: lead time (change created → production approval), cycle time per phase, human approval wait per gate, throughput (archived changes per week), deploy frequency, change failure rate, time to restore, spec-gap rate and ripple per change, gate rejection rate, estimate accuracy, judge finding acceptance rate and judge cost. *(Traces: PRD §6 S-1, O-2 · Sources: R-14, DM-11, PM-05 · Decision: D-30 (judge cost measured) · BL-17)*
- **REQ-W2-004** — Missing data is stated, never zero. IF a metric cannot be computed for a change because its data is missing or legacy (no `phase_history`, date without time, no outcome entries), THEN the metrics view SHALL report that metric as "n/a" with the reason and the change-id, and SHALL exclude the change from that metric's aggregate only. *(Traces: PRD §6 S-1, O-2 · Sources: R-14, verification rule (state what you did not verify) · BL-17)*
- **REQ-W2-005** — Read-only, reproducible, machine-readable. The metrics view SHALL be read-only, SHALL produce the same output for the same repository state and period, and SHALL offer a structured (JSON) form besides the human-readable table. *(Traces: PRD §6 S-1, AC-1 · Sources: R-14, PM-05 (solo lectura), AG-10 · BL-17)*
- **REQ-W2-006** — Baseline before the process changes. BEFORE any lane, gate or judge default of this change is enabled on this repository, the method SHALL store a metrics snapshot of the repository (baseline) with the date and the method version, and the retro SHALL compare later periods against it. *(Traces: PRD §6 S-1, O-1, AC-1 · Sources: R-14 ("para tener la línea base antes de cambiar el proceso") · Decision: D-24 · BL-17)*
- **REQ-W2-007** — Actual time through the tracker adapter. WHEN a task finishes, the method SHALL record the actual time through a `log_time` operation of the team's tracker adapter (time entry, worklog or equivalent), declared per tool with `none` for tools that have no such object, and SHALL fall back to the task record's actual columns when the operation is `none`. *(Traces: PRD §6 S-1, O-2 · Sources: R-05 (Wave 1), F-27 · MODIFIES REQ-W1-042 · BL-45)*
- **REQ-W2-008** — The retro works on the method's artifacts. WHEN the retro runs for a period, it SHALL present the metrics of REQ-W2-003, the findings by type and by the phase that found them, the estimate accuracy and the judge cost; SHALL store the result in `docs/spec/retros/retro-{date}.md`; and SHALL record each agreed action as a `BL-NN` of type `process` with an owner. *(Traces: PRD §6 S-1, O-2 · Sources: R-14, PM-12, DM-11 · BL-17)*
- **REQ-W2-009** — Actions are followed up; per-person analysis is optional. WHEN a retro runs and a previous retro exists, it SHALL report the state of each previous action; the per-author commit analysis SHALL run only when explicitly requested. *(Traces: PRD §6 S-1 · Sources: R-14, PM-12 ("el análisis por persona queda como opcional") · BL-17)*
- **REQ-W2-010** — 4.0 readiness report. WHEN the metrics view is asked for readiness, it SHALL report the number of changes measured under 3.13 modes, and, per Wave 2 check, how many times it would have refused had it been blocking and how many of those were confirmed defects. *(Traces: PRD §6 S-1, S-13, O-12 · Sources: panel Ola 2 plan ("después de 4–6 cambios medidos") · Decision: D-24)*

### Lanes by size and risk (R-09)
- **REQ-W2-011** — Lanes as data. The method SHALL define the lanes `patch`, `standard`, `feature-ui`, `ops`, `hotfix` and `docs` in one lane table that states, for each lane and phase, whether the phase is mandatory, optional or skipped and how many human gates apply, and the state tool SHALL compute the next phase of a change from its lane. *(Traces: PRD §6 S-2, O-3 · Sources: R-09, DM-01, PM-09, H-03, H-04 · BL-12)*
- **REQ-W2-012** — Lane chosen at init with objective questions. WHEN a change is initialised, the init skill SHALL decide the lane from objective answers — does it touch UI, does it change a data schema or an API contract, does it change permissions or a trust boundary, which Security Tier, how many code files — SHALL record it in `spec.json:lane`, and SHALL propose `standard` when an answer is unknown. *(Traces: PRD §6 S-2, O-3 · Sources: R-09 ("3 preguntas objetivas"), DM-01 · Decision: D-29 · BL-12)*
- **REQ-W2-013** — Objective criterion of the `patch` lane. The method SHALL admit a change to the `patch` lane only if it touches at most 3 code files, changes no data schema, no API contract and no permissions, and its Security Tier is below 3; IF any criterion fails, THEN the method SHALL refuse the lane and propose `standard`. *(Traces: PRD §6 S-2, O-3, AC-2 · Sources: R-09 (riesgo de abuso del carril `patch`), DM-01 · Decision: D-29, D-25 · BL-12)*
- **REQ-W2-014** — The `patch` path. WHERE a change is in the `patch` lane, the method SHALL require, in the same PR, a `BUG-NN` incident, a finding, the fix and a regression test that fails without the fix; SHALL skip requirements, mockup, design, architecture, infra and tasks; and SHALL keep QA-lite and the production gate as its only human gate. *(Traces: PRD §6 S-2, O-3, AC-2 · Sources: R-09 (`iterate/init-lite → impl test-first → qa-lite → deploy`), DM-01 · Decision: D-25 · BL-12)*
- **REQ-W2-015** — Lane-skipped phases are recorded automatically. WHEN the state tool advances a change past a phase its lane skips, it SHALL record the phase in `spec.json:skipped` with the reason `lane:{lane}`, without the agent running a separate skip. *(Traces: PRD §6 S-2 · Sources: R-09 ("las fases omitidas quedan como skipped"), R-01 · MODIFIES REQ-W1-007 · BL-12)*
- **REQ-W2-016** — Lane changes: up freely, down only by the human. WHEN a change's lane is raised, the state tool SHALL record the old lane, the new lane, the time and the reason; IF a lane would be lowered, THEN it SHALL refuse unless the human's approval and a reason are given; the phases the new lane requires and the old one skipped SHALL become pending. *(Traces: PRD §6 S-2 · Sources: R-09 ("se puede subir de carril, pero nunca bajar sin registro"), DM-01 · BL-12)*
- **REQ-W2-017** — The diff is checked against its lane. WHEN QA (or QA-lite) runs, the method SHALL measure the change's diff against its lane's criteria and SHALL report every exceeded criterion as a finding with a lane-raise proposal; in 3.13 the check is warn; the prod gate SHALL show its result. *(Traces: PRD §6 S-2, O-3 · Sources: R-09 ("QA-lite verifica que el tamaño del diff respete el carril"), DM-01 · Decision: D-29, D-24 · BL-12)*
- **REQ-W2-018** — Hotfix lane preconditions are consistent. WHERE a change is in the `hotfix` lane, the state tool SHALL let impl start without a tasks approval and deploy proceed without a full QA review document, and SHALL still require the BUG-NN, the regression test in the same PR and the human production approval. *(Traces: PRD §6 S-2 · Sources: R-09, H-04, DM-01 (hotfix choca con las precondiciones) · BL-12)*
- **REQ-W2-019** — A change without a lane keeps today's pipeline. WHERE a `spec.json` has no `lane`, the state tool SHALL treat it as the full pipeline of 3.12.0 (every phase mandatory unless recorded as skipped), SHALL report the missing lane as a warning in 3.13, and as an error in 4.0. *(Traces: PRD §6 S-2, S-13, O-12 · Sources: R-09, panel Ola 2 ("el esquema de spec.json pasa a ser obligatorio (lane…)") · Decision: D-24 · BL-12)*
- **REQ-W2-020** — The owner's global instruction diff for the `patch` lane. The change SHALL deliver, as a file inside the change folder, the proposed diff to the owner's personal global instructions that makes the `patch` lane the official path for a small bug, and SHALL NOT write to the owner's personal configuration. *(Traces: PRD §6 S-2, §7 · Sources: panel §6.4 · Decision: D-25, D-01, D-11)*
- **REQ-W2-021** — Lane is visible. The dashboard, the metrics view and the gate summaries SHALL show each change's lane and its lane-skipped phases as "skipped (lane)", distinct from pending phases. *(Traces: PRD §6 S-2, O-2 · Sources: R-09 ("dashboards honestos"), DM-01 · BL-12)*

### Advisory judges before the human gates (R-11, JU-01)
- **REQ-W2-022** — Where judges run. WHERE judges are enabled, the method SHALL run the judges before the human gate of the requirements, the architecture and the qa phases, and SHALL allow a project to add or remove phases in the judge settings. *(Traces: PRD §6 S-3, O-4, AC-3 · Sources: R-11, JU-01, DM-06, AG-12 · Decision: D-23 · BL-14)*
- **REQ-W2-023** — Clean context and closed inputs. WHEN a judge runs, it SHALL receive only the artifacts of the phase under review, the artifacts that phase reads, the PRD goal and the rubric of that phase, and SHALL NOT receive the author's conversation or reasoning. *(Traces: PRD §6 S-3, §9 · Sources: R-11 ("contexto limpio"), AG-12 · Decision: D-23 · BL-14)*
- **REQ-W2-024** — One rubric and lenses per phase. The method SHALL ship one rubric per judged phase and SHALL assign default lenses per phase — requirements: domain and methods; architecture: security, methods and agents/cost; qa: fiscal (evidence) and security. *(Traces: PRD §6 S-3 · Sources: R-11 (lentes según la fase), DM-06, DM-08 · Decision: D-23 · BL-14)*
- **REQ-W2-025** — A finding without a citation is discarded. WHEN a judge reports a finding, it SHALL cite `file:line` of the reviewed artifacts; IF a finding has no resolvable citation, THEN the judges skill SHALL discard it and count it as discarded. *(Traces: PRD §6 S-3 · Sources: R-11 ("un hallazgo sin cita se descarta") · BL-14)*
- **REQ-W2-026** — Judges observe; the iterate skill routes. WHEN a judge finding is kept, the judges skill SHALL append it to the change's `findings.md` with origin `judge:{lens}`, a type guess and a severity, and SHALL NOT route it, edit the artifact or change `spec.json`. *(Traces: PRD §6 S-3 · Sources: R-11, panel §5 ("quien observa no enruta") · BL-14)*
- **REQ-W2-027** — The gate summary carries the verdicts. WHEN a judged gate is presented, the method SHALL show per judge its lens, verdict, number of findings by severity and model used, the blocking-severity findings in full, and any disagreement between judges. *(Traces: PRD §6 S-3, O-4 · Sources: R-11 ("el gate humano muestra un resumen") · BL-14)*
- **REQ-W2-028** — Advisory by default; blocking is opt-in. WHILE the judge mode is advisory, no judge finding SHALL prevent an approval; WHERE a project sets the judge mode to blocking, the state tool SHALL refuse the approval of a judged phase while a Critical or High judge finding of that phase is `open`. *(Traces: PRD §6 S-3, O-4, AC-3 · Sources: R-11 (`mode: advisory`, `blocking` opcional) · Decision: D-23 · BL-14)*
- **REQ-W2-029** — Cross-model preferred, intra-model declared. WHEN a judge runs, the method SHALL use a different model family when one is available in the session and SHALL otherwise run an intra-model judge, recording in every case the model used and whether it was intra-model. *(Traces: PRD §6 S-3 · Sources: R-11 (`cross_model: prefer`), DM-08, AG-12 · Decision: D-23 · BL-14)*
- **REQ-W2-030** — Judge cost is measured, never capped. WHEN a judge run finishes, the method SHALL record its tokens and US$ per judge, per gate and per change, marking values as estimated when the runtime does not expose them; no budget setting SHALL stop, shorten or skip a judge run. *(Traces: PRD §6 S-3, S-1, O-4, AC-3 · Sources: R-11 (costo en tokens), R-25 (costo de jueces aparte) · Decision: D-30 (replaces the cap part of D-23) · BL-14)*
- **REQ-W2-031** — Judges per lane. The method SHALL run by default no judges in the `patch` lane, two lenses per judged phase in `standard` and three in `feature-ui`, and SHALL let a project override the count per lane. *(Traces: PRD §6 S-3, S-2 · Sources: R-11 ("patch sin jueces, standard con 2, feature-ui con 3") · BL-14)*
- **REQ-W2-032** — The fiscal before `qa.approved`. BEFORE `qa.approved` is recorded, a clean-context judge with the `fiscal` lens SHALL receive the diff and the QA review document and SHALL list every claim of the review that has no evidence (command output, test run, file citation); its findings follow REQ-W2-026. *(Traces: PRD §6 S-3 · Sources: AG-12 ("fiscal antes de qa.approved"), B-12 (proposal, cheap piece) · Decision: D-23 (qa phase) · BL-14)*
- **REQ-W2-033** — Acceptance of judge findings is recorded. WHEN the iterate skill routes a judge finding, it SHALL record whether it was accepted (routed as bug, spec-gap or emergent) or rejected with a reason, so that the acceptance rate per lens is computable. *(Traces: PRD §6 S-3, S-1, O-2 · Sources: R-11 ("tasa de hallazgos de juez aceptados") · BL-14)*

### Three merged human gates (R-10)
- **REQ-W2-034** — Three gates per feature. WHERE merged gates are enabled, the method SHALL ask the human three gate questions per `feature-ui` or `standard` change: (1) *what* — requirements, mockup and design; (2) *how* — architecture, infra and tasks; (3) *release* — qa and production; phases a lane skips are left out of their gate. *(Traces: PRD §6 S-4, O-5, AC-4 · Sources: R-10, DM-06 · Decision: D-22 · BL-13)*
- **REQ-W2-035** — One question per gate. WHEN a gate is presented, the method SHALL ask one question with the options *Approve and advance (recommended)*, *Approve and stop* and *Request changes*, and SHALL NOT ask a separate "shall we advance" after it. *(Traces: PRD §6 S-4, O-5 · Sources: R-10, AG-08, DM-06 · Decision: D-22 · BL-13)*
- **REQ-W2-036** — A merged gate records every phase's approval. WHEN a merged gate is approved, the state tool SHALL record an approval for each non-skipped phase it covers, with the same `by`, `role`, `ref` and time, and SHALL NOT merge the phases' artifacts. *(Traces: PRD §6 S-4 · Sources: R-10 · Decision: D-22 ("merging gates does not merge their artifacts") · BL-13)*
- **REQ-W2-037** — The *how* gate carries a one-page summary. WHEN the *how* gate is presented, the method SHALL show a one-page summary of decisions, deviations from the requirements, risks, estimated cost, `[human]` tasks and the judges' verdicts. *(Traces: PRD §6 S-4, O-5 · Sources: R-10 ("con un resumen de una página"), DM-06 · BL-13)*
- **REQ-W2-038** — Continuous execution between gates. WHILE a change is between two gates, the phase skills SHALL advance without asking the human, except for the exceptions the plan rule allows (an action outside the approved plan, a change to production data). *(Traces: PRD §6 S-4, O-5 · Sources: R-10, DM-06 ("modo de ejecución continua entre ellos") · Decision: D-22 · BL-13)*
- **REQ-W2-039** — Granular gates remain available. The method SHALL keep the seven per-phase gates available through the gate settings and a `--granular-gates` flag; in 3.13 the default SHALL be granular with merged gates opt-in; in 4.0 the default SHALL be merged. *(Traces: PRD §6 S-4, S-13, O-12 · Sources: R-10 (`--granular-gates`) · Decision: D-22, D-24 · BL-13)*
- **REQ-W2-040** — `-y` is an automatic approval, never production. WHEN a phase skill is invoked with `-y`, the state tool SHALL record the approval with `role: auto`; IF `-y` is used for the production approval, THEN it SHALL refuse; the dashboard and the metrics SHALL show automatic approvals apart from human ones. *(Traces: PRD §6 S-4 · Sources: R-10 ("-y registra role auto y queda prohibido en prod"), H-06, DM-06 · MODIFIES REQ-W1-006 · BL-13)*
- **REQ-W2-041** — Grill asks in batches. WHEN the grill skill interviews the human, it SHALL ask up to four questions per question batch, each with its recommended option first, and SHALL infer the stack questions from the repository and only ask to confirm them. *(Traces: PRD §6 S-4, O-5 · Sources: R-10, AG-08 · BL-13)*
- **REQ-W2-042** — *Request changes* keeps the phase and records why. WHEN the human answers *Request changes* at a gate, the method SHALL record the outcome with the human's reason (REQ-W2-001), keep the change in its current phase and return to the phase skill that owns the requested change. *(Traces: PRD §6 S-4, S-1 · Sources: R-10 (tasa de rechazo por gate) · BL-13)*

### Release per change (R-08)
- **REQ-W2-043** — Every commit carries the change trailer. WHEN the impl skill (or any phase skill) commits for a change, it SHALL add the trailer `Karvey-Change: <change-id>` to the commit message. *(Traces: PRD §6 S-5, O-6 · Sources: R-08, DM-03 · Decision: D-26 · BL-11)*
- **REQ-W2-044** — Missing trailers are detected at commit time. WHERE the optional commit-message guard is enabled, WHEN a commit on a feature branch of an active change lacks the change trailer, the guard SHALL warn in 3.13 and block when the project sets it blocking. *(Traces: PRD §6 S-5 · Sources: DM-03 ("commit-msg hook opcional") · Decision: D-26, D-24 · BL-11)*
- **REQ-W2-045** — The release manifest. BEFORE the production PR is opened, the deploy skill SHALL compute the release manifest: every commit between production and the release head, mapped to its change-id by trailer, with each change's version, lane and QA state. *(Traces: PRD §6 S-5, O-6, AC-5 · Sources: R-08 (paso 2.8-bis), DM-03, PM-04, H-21 · Decision: D-26 · BL-11)*
- **REQ-W2-046** — Manifest verdict. WHEN the manifest contains an unmapped commit or a change without `qa.approved` (or QA skipped by its lane), the deploy skill SHALL warn in 3.13, SHALL refuse in 4.0, and the prod gate SHALL apply the same verdict when the manifest is blocking. *(Traces: PRD §6 S-5, S-13, O-6, AC-5 · Sources: R-08 ("empezar en modo advertir"), PM-04 · Decision: D-24, D-26 · BL-11)*
- **REQ-W2-047** — The PR lists every change; each gets its approval. WHEN the production PR is opened, its body SHALL list every change-id and version of the manifest, and WHEN the human approves production the approval SHALL be recorded for every change of the manifest. *(Traces: PRD §6 S-5, O-6 · Sources: R-08, PM-04 · Decision: D-26, D-03, D-10 · BL-11)*
- **REQ-W2-048** — Integration by PR. WHERE the integration branch differs from production, the method SHALL integrate a feature branch through a PR to the integration branch and SHALL NOT instruct a local merge followed by a direct push to it. *(Traces: PRD §6 S-5 · Sources: R-08 ("la integración a dev pasa por PR"), DM-03 · Decision: D-26 · MODIFIES REQ-W1-034 · BL-11)*
- **REQ-W2-049** — Branch mode, trunk recommended. The method SHALL support `branch_flow.mode` with `trunk` and `env-branches`, SHALL derive `trunk` when integration equals production, and SHALL recommend `trunk` when a project is set up. *(Traces: PRD §6 S-5 · Sources: R-08 (`branch_flow.mode`), DM-03 · Decision: D-26 · MODIFIES REQ-W1-035 · BL-11)*
- **REQ-W2-050** — A release branch as the way out. WHEN the manifest verdict is not `pass`, the deploy skill SHALL offer a `release/*` branch from production with only the approved changes cherry-picked, besides waiting. *(Traces: PRD §6 S-5 · Sources: R-08 ("ofrecer release/* + cherry-pick"), PM-04 · BL-11)*
- **REQ-W2-051** — `approvals.deploy` is retired. The method SHALL record deploys only in `spec.json:deploys` (REQ-W2-002), SHALL treat `approvals.deploy` as a legacy key reported as a warning, and the migration SHALL remove it showing the diff. *(Traces: PRD §6 S-5 · Sources: F-28 · BL-46)*
- **REQ-W2-052** — Where the production OK is written, in order. The deploy rule SHALL state that at deploy the production OK text lives in the PR body or PR approval, and that at archive it is written as `D-NN` into the decision log on the archive branch and copied into `approvals.prod`. *(Traces: PRD §6 S-5 · Sources: F-29 · Decision: D-03 · BL-47)*
- **REQ-W2-053** — Deployed without the local ledger. WHERE the release ledger of the clone is absent, the state tool SHALL accept `advance {id} deployed` with a `D-NN` reference and a pipeline-run URL, and SHALL record the transition as attested rather than measured. *(Traces: PRD §6 S-5 · Sources: F-30 · BL-48)*

### Living spec merged before production (R-17 timing)
- **REQ-W2-054** — Merge on the change branch, before the production PR. BEFORE the production PR of a change is opened, the method SHALL merge the change's `spec-delta.md` into the living spec on the change branch with the spec-merge tool, showing the dry-run first. *(Traces: PRD §6 S-6, O-11, AC-6 · Sources: R-17 (momento de DM, script de AG), DM-09 · MODIFIES REQ-W1-067 · BL-20)*
- **REQ-W2-055** — Archive only moves and closes. WHEN a change is archived, the archive skill SHALL move the change folder and close its Epic, and SHALL NOT merge the spec-delta again; IF the delta is not yet merged, THEN it SHALL report it and merge it on the archive branch. *(Traces: PRD §6 S-6 · Sources: R-17 ("archive queda en mover la carpeta y cerrar la Epic") · MODIFIES REQ-W1-067 · BL-20)*
- **REQ-W2-056** — A deployed change without its delta is visible. The linter SHALL fail when a change in `deployed` or later has an unmerged spec-delta, and the dashboard SHALL flag a change `deployed` without archive for more than 7 days. *(Traces: PRD §6 S-6, O-11 · Sources: R-17 (`karvey-context` avisa), DM-09 · BL-20)*

### Test-first and traceability (R-12)
- **REQ-W2-057** — A test task before each implementation task. WHEN tasks are generated, the tasks skill SHALL create, for each requirement the task set covers, a test task that precedes its implementation task and states the failing result expected before the implementation. *(Traces: PRD §6 S-7, O-7 · Sources: R-12, DM-07 · BL-15)*
- **REQ-W2-058** — Tests name their requirement. The method SHALL require every automated test written for a change to reference the requirement it verifies by ID in its name or in a tag. *(Traces: PRD §6 S-7, O-7 · Sources: R-12 (`test_REQ_1_2_*` o `@req 1.2`), DM-07 · BL-15)*
- **REQ-W2-059** — The test phase starts from the architecture's coverage plan. WHEN the test phase starts, it SHALL read the test coverage plan of `architecture.md` and SHALL report every planned item it did not execute. *(Traces: PRD §6 S-7 · Sources: R-12 ("karvey-test no consume el Test coverage plan"), DM-07 · BL-15)*
- **REQ-W2-060** — Trace generated by a script. WHEN the test phase closes, the method SHALL generate `changes/{id}/traceability.md` by script, mapping each requirement to its tasks, the commits carrying the change trailer, its tests and their last result. *(Traces: PRD §6 S-7, O-7, AC-7 · Sources: R-12, DM-07 · Decision: D-26 (trailer) · BL-15)*
- **REQ-W2-061** — Evidence lives inside the change. The test and QA phases SHALL write their plan and evidence under `changes/{id}/`, not in a file shared across changes. *(Traces: PRD §6 S-7 · Sources: R-12 ("mover la evidencia a changes/{id}/"), DM-07 · BL-15)*
- **REQ-W2-062** — Coverage gate. WHEN QA or archive runs, the method SHALL check that every ADDED or MODIFIED requirement has at least one green automated test or a `manual` exception with its reason; the check SHALL be warn in 3.13. *(Traces: PRD §6 S-7, O-7 · Sources: R-12 ("gate: todo requisito ADDED/MODIFIED tiene un test verde o una excepción manual") · Decision: D-24 · BL-15)*
- **REQ-W2-063** — QA runs the suite or cites the exact run. WHEN QA states that tests or the build pass, it SHALL either run them or cite the CI run of the exact commit reviewed; IF neither exists, THEN the statement SHALL read "not evaluated". *(Traces: PRD §6 S-7, S-3 · Sources: R-12 ("QA ejecuta la suite o cita el run de CI"), DM-07, H-28 context · BL-15)*

### Deterministic security tools (R-13)
- **REQ-W2-064** — QA runs the available tools per category. WHEN the QA security dimension runs, it SHALL run the tools available in the environment for secrets, static analysis, dependency vulnerabilities and infrastructure-as-code, and SHALL cite each tool's command, version and result summary. *(Traces: PRD §6 S-8, O-8 · Sources: R-13, DM-08 · BL-16)*
- **REQ-W2-065** — A missing tool is "not evaluated". IF no tool is available for a category, THEN the QA review SHALL mark that category "not evaluated" and the dashboard SHALL count it; the model's reading SHALL NOT turn it into "pass". *(Traces: PRD §6 S-8, O-8 · Sources: R-13, DM-08, engineering-standards "not evaluated ≠ conformant" · BL-16)*
- **REQ-W2-066** — Triage and suppressions carry a reason. WHEN a tool finding is judged a false positive, the QA review SHALL record the suppression with its reason and scope; the model SHALL additionally review what tools do not cover (authorisation per object, tenant isolation, business logic). *(Traces: PRD §6 S-8 · Sources: R-13 ("el LLM tría falsos positivos y cubre lo que las herramientas no ven") · BL-16)*
- **REQ-W2-067** — Tool invocation is safe. The security tools SHALL be run with fixed command templates, and no value read from `project.json` or the change SHALL reach a tool command without the validation of REQ-W1-093. *(Traces: PRD §6 S-8, §9 (Security Tier 2) · Sources: R-13 · BL-16)*
- **REQ-W2-068** — The tools move into the PR pipeline. WHEN the infra phase designs the CI/CD pipeline, it SHALL propose running the same security tool categories in the PR pipeline, so that the security verdict belongs to CI rather than to a session. *(Traces: PRD §6 S-8 · Sources: R-13 ("karvey-infra propone llevar estas herramientas al pipeline de PR"), DM-08 · BL-16)*

### Deterministic scripts (R-20)
- **REQ-W2-069** — Release gate as a script. WHEN deploy runs its pre-checks, it SHALL run the release gate, which SHALL return a structured verdict (QA gate, tests, CHANGELOG, version match, hotfix triplet, manifest) and a non-zero exit when any item fails; the skill SHALL explain the verdict, not recompute it. *(Traces: PRD §6 S-9, O-9 · Sources: R-20, AG-10 · BL-23)*
- **REQ-W2-070** — IDs reserved by a tool. WHEN a new `BUG`, `D`, `BL`, `F` or `Q` identifier is needed, the method SHALL obtain it from the id tool, which SHALL take a lock, scan every source including remote branches, and reserve the number before returning it. *(Traces: PRD §6 S-9, O-9 · Sources: R-20, AG-07, PM-13, H-35 · BL-23)*
- **REQ-W2-071** — Qualified and unbounded IDs. The id tool SHALL emit repository-qualified IDs (`BUG-NN@{repo}`) for cross-repo indexes, and no skill SHALL bound Epic numbers to a fixed range. *(Traces: PRD §6 S-9 · Sources: R-20 (`BUG-NN@repo`, `E{1..99}`), AG-07, H-33 · BL-23)*
- **REQ-W2-072** — Health score as a script. WHEN the health skill computes its score, it SHALL use the health score script with explicit sub-score functions and the time zone of `KARVEY_TZ`, so that the same inputs produce the same score. *(Traces: PRD §6 S-9, O-9 · Sources: R-20, AG-10 · BL-23)*
- **REQ-W2-073** — Evidence wrapper. The method SHALL provide an evidence wrapper that runs a command and appends its command line, exit code, duration, output hash and time to `changes/{id}/evidence.jsonl`, and phase-close claims SHALL cite lines of that file where a command proves them. *(Traces: PRD §6 S-9, S-3 · Sources: R-20, AG-12, B-12 (proposal, cheap piece) · BL-23)*
- **REQ-W2-074** — Cross-repo decision references validate. The spec schema SHALL accept decision references of the form `D-NN@{repo}` as the multi-agent rule prescribes, and the state tool's `next` SHALL print each blocker once. *(Traces: PRD §6 S-9 · Sources: F-26 · BL-44)*

### Post-deploy verification with thresholds (R-23)
- **REQ-W2-075** — A post-deploy contract per service. WHEN the infra phase runs for a deployable service, it SHALL write in `infra.md` a post-deploy contract with health endpoints, critical routes, thresholds (error rate, latency against the production baseline, new server errors), the observation window, the metrics source and the rollback command. *(Traces: PRD §6 S-10, O-10 · Sources: R-23, DM-10 · BL-26)*
- **REQ-W2-076** — Deploy runs the contract and keeps evidence. WHEN a production deploy finishes, the deploy skill SHALL run the post-deploy contract, SHALL write the probe results to `changes/{id}/deploy_evidence.md`, SHALL record the result in `deploys` (REQ-W2-002), and SHALL call the step "post-deploy verification", keeping "canary" only where the platform splits traffic. *(Traces: PRD §6 S-10, O-10 · Sources: R-23, DM-10, PM-05 · BL-26)*
- **REQ-W2-077** — No contract is "not evaluated". IF a deployed service has no post-deploy contract or no thresholds, THEN the verification SHALL be recorded as "not evaluated" with a recommendation to add the contract, never as `pass`. *(Traces: PRD §6 S-10, O-10 · Sources: R-23 ("no hay umbrales"), DM-10 · BL-26)*
- **REQ-W2-078** — A regression proposes the rollback and opens the incident. WHEN the verification is `regression`, the deploy skill SHALL present the contract's rollback command for the human's approval, SHALL record the rollback taken in `deploys`, and SHALL open a `BUG-NN` incident. *(Traces: PRD §6 S-10, S-1 · Sources: R-23, DM-10 (rollback definido), incident rule · BL-26)*

### Knowledge sync optional (D-27)
- **REQ-W2-079** — No text requires graphify. No skill, rule or README SHALL describe graphify (or any knowledge-sync tool) as required; a project without `knowledge_sync`, or with `none`, SHALL run every phase without a sync step, and the linter SHALL check it. *(Traces: PRD §6 S-11 · Sources: R-16, panel §6.8 · Decision: D-27 · MODIFIES REQ-W1-061)*

### Deferred Wave 1 backlog
- **REQ-W2-080** — Import resumes through recorded gates. WHEN the import skill brings existing artifacts into a change, it SHALL record each imported artifact as generated, SHALL ask the human the gate question of each imported gate in order (merged gates when enabled), and SHALL resume at the first gate the human did not approve. *(Traces: PRD §6 S-12 · Sources: F-31 · BL-49)*
- **REQ-W2-081** — One decision-log shape. The method SHALL use `{ops_repo}/docs/spec/decisions.md` as the one decision log, SHALL read per-period decision files where they exist, and SHALL document a migration note for them. *(Traces: PRD §6 S-12 · Sources: F-32, L-30 · BL-50)*
- **REQ-W2-082** — The statusline failure line has a table case. The guard tables SHALL include a case for the statusline's failure line, and the hooks README SHALL anchor it. *(Traces: PRD §6 S-12 · Sources: F-33 (rest) · MODIFIES REQ-W1-051)*

### Rollout 3.13 → 4.0 and dogfooding (D-24)
- **REQ-W2-083** — Every new check has a mode. Every check this change introduces SHALL declare its mode in one place (advisory, warn or blocking), SHALL default to advisory or warn in 3.13, and SHALL be switchable per project. *(Traces: PRD §6 S-13, O-12 · Sources: panel Ola 2 plan · Decision: D-24)*
- **REQ-W2-084** — Nothing that passed in 3.12 fails in 3.13. WHILE a project uses the 3.13 defaults, no Wave 2 check SHALL refuse an operation that 3.12.0 allowed. *(Traces: PRD §6 S-13, O-12, AC-8 · Sources: R-01 (modo advertencia), panel Ola 2 · Decision: D-24)*
- **REQ-W2-085** — 4.0 flips exactly the D-24 defaults. WHEN 4.0.0 is released, the defaults that become blocking SHALL be exactly: the spec schema strict (with `lane`, `phase_history` and `skipped` required), merged gates, and the blocking release manifest; every other Wave 2 check SHALL keep its 3.13 default unless a later decision changes it. *(Traces: PRD §6 S-13, O-12 · Sources: panel Ola 2 ("es breaking porque…") · Decision: D-24, D-23)*
- **REQ-W2-086** — 4.0 only on measured data. The 4.0.0 release SHALL be proposed only when the readiness report (REQ-W2-010) shows at least 4 changes measured under 3.13, and its approval SHALL be recorded as its own decision. *(Traces: PRD §6 S-13, O-1, O-12 · Sources: panel Ola 2 ("después de 4–6 cambios medidos") · Decision: D-24)*
- **REQ-W2-087** — Migration to the Wave 2 shape. WHEN `validate --fix` runs on a pre-3.13 `spec.json`, the state tool SHALL propose a lane inferred from the recorded skipped phases, SHALL remove `approvals.deploy` into `deploys` only when it holds data, SHALL show the diff before writing, and SHALL NOT create or flip any approval. *(Traces: PRD §6 S-13 · Sources: R-01 (`--fix`), R-09 · Decision: D-24 · MODIFIES REQ-W1-009 · BL-46)*
- **REQ-W2-088** — Built with itself. This change SHALL run in the `standard` lane on this repository in trunk mode, SHALL carry the change trailer on every commit, SHALL take the metrics baseline before enabling its own lane and gate defaults, and SHALL be the first change counted by the readiness report. *(Traces: PRD §6 S-13, §9, AC-1, AC-5 · Sources: panel Ola 1 (dogfooding), H-22 · Decision: D-04, D-26)*

## MODIFIED Requirements

### Requirement: REQ-W1-006
<!-- COMPLETELY replaces REQ-W1-006. Reason: `-y` records an automatic approval (R-10, REQ-W2-040). -->
- **REQ-W1-006** — Approvals carry who, role, time and reference. WHEN an approval is recorded, the state tool
  SHALL write `by`, `role` (`human` | `ceo-delegate` | `auto`), `date` as an ISO 8601 timestamp with time and
  zone, and `ref`; IF any of them is missing, THEN it SHALL refuse; IF the approval is `prod` and `role` is not
  `human`, THEN it SHALL refuse; `role: auto` SHALL be written only for a `-y` invocation. *(Traces: wave1 PRD §6
  S-1, O-3; wave2 PRD §6 S-4 · Sources: R-01, R-10, R-14 · Decision: D-03, D-22)*

### Requirement: REQ-W1-007
<!-- COMPLETELY replaces REQ-W1-007. Reason: lanes skip phases automatically (R-09, REQ-W2-015). -->
- **REQ-W1-007** — Skipped phases are recorded. WHEN a phase is skipped, the state tool SHALL record it in
  `spec.json:skipped` as `{phase: reason}` with a non-empty reason — `lane:{lane}` when the change's lane skips it,
  a human reason otherwise — and SHALL treat a skipped phase as satisfying the preconditions of the next phase; IF
  a manual skip has an empty reason, THEN it SHALL refuse. *(Traces: wave1 PRD §6 S-1; wave2 PRD §6 S-2 · Sources:
  R-01, R-09, H-03 · BL-04, BL-12)*

### Requirement: REQ-W1-009
<!-- Replaces REQ-W1-009 by adding the Wave 2 migration steps (REQ-W2-087). -->
- **REQ-W1-009** — Migration of legacy `spec.json` (`--fix`). WHEN the state tool runs `validate --fix` on a
  legacy `spec.json`, the state tool SHALL map the legacy phase values to the enum, SHALL convert `gates_skipped`
  into `skipped`, SHALL map `management: "none"` to `markdown`, SHALL propose a `lane` inferred from the recorded
  skipped phases, SHALL move a non-empty `approvals.deploy` into `deploys` and drop an empty one, SHALL show the
  diff before writing, SHALL NOT create or flip any approval, and SHALL produce the same file when run twice.
  *(Traces: wave1 PRD §6 S-1, AC-1; wave2 PRD §6 S-13 · Sources: R-01, R-09, F-28 · BL-04, BL-46)*

### Requirement: REQ-W1-034
<!-- COMPLETELY replaces REQ-W1-034. Reason: integration by PR (R-08, D-26, REQ-W2-048). -->
- **REQ-W1-034** — Checklist before the first push. The deploy skill SHALL run the pre-deploy checklist (feature
  branch, CHANGELOG `[Unreleased]` line, everything committed, change trailer on every commit, branch pushed,
  integrated through a PR to the integration branch where it differs from production) before its first
  `git push`, and SHALL NOT instruct a local merge followed by a direct push to integration. *(Traces: wave1 PRD §6
  S-3, O-4; wave2 PRD §6 S-5 · Sources: R-03, R-08, H-20 · Decision: D-26 · BL-06, BL-11)*

### Requirement: REQ-W1-035
<!-- COMPLETELY replaces REQ-W1-035. Reason: the branch mode becomes an explicit setting (R-08, REQ-W2-049). -->
- **REQ-W1-035** — Trunk projects. WHERE `branch_flow.mode` is `trunk` — explicitly, or derived because
  `branch_flow.integration` equals `branch_flow.production` — the deploy skill, the archive skill and the guards
  SHALL use the single PR from the feature branch as both the integration and the production gate, and SHALL NOT
  require a separate integration merge; the method SHALL recommend `trunk` at setup. *(Traces: wave1 PRD §6 S-3;
  wave2 PRD §6 S-5 · Sources: R-03, R-08 · Decision: D-04, D-26)*

### Requirement: REQ-W1-042
<!-- COMPLETELY replaces REQ-W1-042. Reason: the actual time goes through an adapter operation (F-27, REQ-W2-007). -->
- **REQ-W1-042** — Estimate and actual are separate fields. WHEN a task finishes, the impl skill SHALL record the
  actual time through the tracker adapter's `log_time` operation, or in the task record's actual columns when the
  adapter declares `none`, and SHALL NOT write the actual into the estimate field. *(Traces: wave1 PRD §6 S-5, O-6;
  wave2 PRD §6 S-1 · Sources: R-05, H-16, F-27 · BL-08, BL-45)*

### Requirement: REQ-W1-051
<!-- Replaces REQ-W1-051 by adding the statusline failure-line case (F-33, REQ-W2-082). -->
- **REQ-W1-051** — Hooks README matches hook behaviour. The hooks README SHALL describe each hook's output
  conditions as the hook implements them, including the statusline's failure line, and the plugin linter SHALL
  check the documented silent/printing conditions against the guard tables, each of which SHALL have a case.
  *(Traces: wave1 PRD §6 S-6, S-7; wave2 PRD §6 S-12 · Sources: BUG-16 / F-30 (wave1 numbering), F-33 · BL-09, BL-10)*

### Requirement: REQ-W1-061
<!-- COMPLETELY replaces REQ-W1-061. Reason: knowledge sync optional everywhere (D-27, REQ-W2-079). -->
- **REQ-W1-061** — `knowledge_sync: none` is valid and the default. The method SHALL accept
  `project.json:knowledge_sync` values `none | graphify | obsidian`; WHERE the key is absent the method SHALL
  behave as `none`; no skill, rule or README SHALL describe a knowledge-sync tool as required. *(Traces: wave1 PRD §6
  S-8; wave2 PRD §6 S-11 · Sources: R-16 · Decision: D-27 · BL-19)*

### Requirement: REQ-W1-067
<!-- COMPLETELY replaces REQ-W1-067. Reason: the merge moves before the production PR (R-17 timing, REQ-W2-054/055). -->
- **REQ-W1-067** — The spec-merge tool merges before production. WHEN a change's production PR is prepared, the
  method SHALL merge its spec-delta with the spec-merge tool on the change branch (dry run shown first); WHEN the
  change is archived, the archive skill SHALL only verify the merge, and merge on the archive branch a legacy delta
  that was never merged. *(Traces: wave1 PRD §6 S-9; wave2 PRD §6 S-6 · Sources: R-17, DM-09 · BL-20)*

## REMOVED Requirements

None.
