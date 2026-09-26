# Spec Delta: wave3-optimization

Against the living spec `docs/spec/specs/method/spec.md` (capability `method`). Baseline: the REQ-TEAM-* blocks already
there **plus** the REQ-W1-* (and carried REQ-ADP-*) blocks of `wave1-hardening`'s `spec-delta.md` and the REQ-W2-* blocks
of `wave2-structural`'s `spec-delta.md`, treated as already merged (those changes ship first, as 3.12.0 and 3.13.0/4.0.0).
Where a MODIFIED block below replaces a requirement that Wave 2 already modified, it replaces the Wave 2 text. Single
spec-delta path: this file, at the change root. Merge order: wave1, then wave2, then this delta — `karvey-spec-merge --dry-run
wave3-optimization` (run 2026-09-26) parses this file and refuses it only because the six MODIFIED blocks are not in the
living spec yet.
Scenarios for every block are in `requirements.md`; the living spec keeps the compact form it already uses.

Summary: **ADDED 70** (REQ-W3-001..070) · **MODIFIED 6** (REQ-ADP-031, REQ-W1-009, REQ-W1-068, REQ-W2-003,
REQ-W2-008, REQ-W2-022) · **REMOVED 0**.

## ADDED Requirements

### ADDED by `wave3-optimization` (4.1.0)

Traced to `docs/spec/changes/wave3-optimization/prd.md`.

### Context budget and progressive loading (R-15)
- **REQ-W3-001** — Per-phase instruction size is measured. WHEN the size tool runs on the plugin, it SHALL report, per phase skill, the size of the skill, of the rules it loads directly and of the transitive closure of the rules it loads, in bytes and in estimated tokens (marked estimated), and SHALL offer a structured (JSON) form. *(Traces: PRD §6 S-1, O-1, AC-1 · Sources: R-15, AG-04, AG §2.4, H-34 · BL-18)*
- **REQ-W3-002** — Baseline before the reorganisation, reproducible. BEFORE any skill or rule is moved by this change, the method SHALL store the size snapshot of the 4.0.0 content with the date and the method version, and the size tool SHALL produce byte-identical output for the same input. *(Traces: PRD §6 S-1, O-1, AC-1 · Sources: R-15 ("hay que re-probar"), Wave 2 baseline pattern (REQ-W2-006) · BL-18)*
- **REQ-W3-003** — A core of hard contracts. The method SHALL ship one core rule, loaded by every phase skill, that states the hard contracts every phase must honour — state changes only through the state tool, the gate and approval contract, the production gate, the branch and commit contract including the change trailer, the verification failure modes, the finding router, the neutrality of public text — each with a stable contract id, and SHALL keep it at or below 1,000 words. *(Traces: PRD §6 S-2, O-2 · Sources: R-15 (`_core.md` ~800 palabras), AG-04 · BL-18)*
- **REQ-W3-004** — Each skill declares a closed load list. Each phase skill SHALL declare near its top a closed list of the rules and references it loads; the skill SHALL NOT instruct the agent to open any rule outside that list; a citation of another rule for context SHALL be a footnote that is not opened. *(Traces: PRD §6 S-2, O-2 · Sources: R-15 ("cada skill declare `Load:` como una lista cerrada"), AG-04 · BL-18)*
- **REQ-W3-005** — Rules do not load each other. A rule SHALL NOT require loading another rule; cross-references between rules SHALL be footnotes, so that the closure of a load list equals the list plus the core. *(Traces: PRD §6 S-2, O-2 · Sources: R-15 (`phase-close.md` cita 7, `project-config.md` cita 8), AG-04 · BL-18)*
- **REQ-W3-006** — Tracker detail loaded only for the team's tool. The method SHALL keep the tool-specific detail of each tracker in its own adapter file and SHALL load only the adapter of the tool resolved from the project's management settings; no phase skill body SHALL carry tool-specific examples of one tracker. *(Traces: PRD §6 S-2, O-2 · Sources: R-15 ("adaptadores a `adapters/{tool}.md`"), AG-04 (ejemplos de un tracker en init, tasks, impl) · BL-18)*
- **REQ-W3-007** — Rare paths move to references. The method SHALL move the paths a phase takes rarely — the first-use team settings of init, the documentation-only, hotfix, verification and branch-hygiene paths of deploy, and every other section the architecture lists — into references of that skill, loaded only when that path is taken; the skill SHALL keep a one-line pointer that says when to load each reference. *(Traces: PRD §6 S-2, O-2 · Sources: R-15 ("partir deploy en núcleo + `references/`", "mover `init --settings`"), AG-04 · BL-18)*
- **REQ-W3-008** — The orchestrator only routes. The orchestrator skill SHALL contain only routing — the state tool's next phase, the lane and the skill to run — and pointers; feature lists, per-phase descriptions, equivalence tables and authorship SHALL move to the README or references. *(Traces: PRD §6 S-2, O-2 · Sources: R-15 ("el orquestador queda solo con el ruteo"), AG-04 (≈2,9k tokens que no rutean) · BL-18)*
- **REQ-W3-009** — No hard contract is lost. WHEN the context reorganisation is complete, a contract coverage check SHALL prove, for every phase skill, that every hard contract that applied to it before the move is still reachable through the core or its load list, and SHALL fail naming the contract and the phase otherwise. *(Traces: PRD §6 S-2, O-2, AC-2 · Sources: R-15 (riesgo: "re-probar que ninguna fase pierda una regla que necesita"), AG-04 · BL-18)*
- **REQ-W3-010** — The budget is a target, measured after. WHEN the reorganisation is complete, the size tool SHALL report the per-phase closure against the baseline, and the change SHALL meet a median reduction of at least 40% or record, per phase that misses it, the reason. *(Traces: PRD §6 S-2, O-2, AC-2 · Sources: R-15 (−45–55% estimado por AG), AG-04 · BL-18)*
- **REQ-W3-011** — Size checked in CI. The plugin's CI SHALL run the size tool, SHALL warn when a phase's closure grows more than 10% over the last released snapshot, and SHALL fail when a load list names a missing file. *(Traces: PRD §6 S-1, S-2, AC-12 · Sources: R-15, AG-13 (drift that reappears every release) · BL-18)*
- **REQ-W3-012** — Per-phase rule lists are generated, not hand-kept. The orchestrator's "applies in" column, the adapters' "used by" column and every per-phase list of rules in the README SHALL be generated from the load lists, and the linter SHALL fail when a generated block drifts. *(Traces: PRD §6 S-2 · Sources: R-15, F-42 · BL-39)*
- **REQ-W3-013** — One phase per session is the declared pattern. The method SHALL declare "one phase per session" as its default working pattern: at each gate close it SHALL offer a checkpoint save and state that the next phase can start in a fresh session, which the session hook resumes; continuing in the same session SHALL remain allowed. *(Traces: PRD §6 S-2, O-2 · Sources: R-15 ("declarar el patrón una fase por sesión con `checkpoint`"), AG-04, AG §2.4 · BL-18)*

### Cost per change with a single agent (R-25)
- **REQ-W3-014** — Effort recorded at each phase close. WHEN a phase closes, the method SHALL add to the change's effort record the AI cost in US$, the tokens and the human review minutes of the interval since the previous close, per phase, marking each value as `exact`, `estimated` or `n/a` with its source. *(Traces: PRD §6 S-3, O-6, AC-6 · Sources: R-25 (`spec.json:effort{ai_usd, tokens, human_review_min}`), PM-08 · Decision: D-30 · BL-28)*
- **REQ-W3-015** — Cost source captured outside the model. The method SHALL capture the session cost from a runtime source that does not rely on the model's own account (the statusline input or the session transcript), SHALL keep the last captured value per session so that the interval can be computed, and SHALL NOT spend model turns to collect it. *(Traces: PRD §6 S-3, O-6 · Sources: R-25 (la statusline ya recibe el costo y no se guarda), PM-08, team-layer F-03 · BL-28, BL-37)*
- **REQ-W3-016** — Judge cost kept apart. The effort record SHALL keep the judges' cost (REQ-W2-030) apart from the phase work, so that the cost of the judges can be judged on its own. *(Traces: PRD §6 S-3, O-6 · Sources: R-25 ("el costo de los jueces se registra aparte"), R-11 · Decision: D-30)*
- **REQ-W3-017** — Cost is never a cap. No setting SHALL stop, shorten, skip or ask to confirm any phase, judge or task because of its measured or estimated cost. *(Traces: PRD §6 S-3, §7 · Sources: R-25 · Decision: D-30)*
- **REQ-W3-018** — Cost per lane, client and period. MODIFIES REQ-W2-003. WHEN the metrics view is requested, it SHALL also compute the cost per change (US$, tokens, human review minutes) and aggregate it per lane, per client and per period, reporting how much of each figure is estimated. *(Traces: PRD §6 S-3, O-6, AC-6 · Sources: R-25 ("agregarlo por `client_tag`"), PM-08 · Decision: D-30 · BL-28)*
- **REQ-W3-019** — Outliers in the retro. MODIFIES REQ-W2-008. WHEN the retro runs, it SHALL flag every change whose cost exceeds three times the median of the period for its lane, with its phases' share, as an input for the discussion, not as a verdict. *(Traces: PRD §6 S-3, O-6 · Sources: R-25, PM-08 ("un cambio cuyo costo supere X veces la mediana se señala en la retro") · Decision: D-30)*

### Sponsor page and "your turn" events (R-19)
- **REQ-W3-020** — Stakeholders declared in the project. The project settings SHALL declare the stakeholders of the project — at least the sponsor — each with a role, a display name and a destination resolved through the notification adapters; a change MAY override the sponsor. *(Traces: PRD §6 S-4, O-3 · Sources: R-19, PM-07 ("usar la sección Stakeholders del PRD") · Decision: D-31 · BL-22)*
- **REQ-W3-021** — One page per change, from the artifacts. WHEN the sponsor page is produced, it SHALL be generated only from the change's artifacts and state — scope from the PRD and requirements, state and lane from the phase history, cost from the effort record, risks from the risk register, pending decisions from the open questions owned by the sponsor, and what reached production from the release manifest — in business language, with the date of every figure. *(Traces: PRD §6 S-4, O-3, AC-3 · Sources: R-19 (reporte en lenguaje de negocio), PM-07 · Decision: D-31 · BL-22)*
- **REQ-W3-022** — Published at every gate close. WHEN a gate of a change with a declared sponsor closes (approved or changes requested), the method SHALL regenerate the sponsor page and SHALL deliver it to the sponsor's destination; WHERE no sponsor is declared, it SHALL produce nothing and say so once. *(Traces: PRD §6 S-4, O-3, AC-3 · Decision: D-31 · Sources: R-19 · BL-22)*
- **REQ-W3-023** — Nothing internal leaves. The sponsor page SHALL contain only fields on an allow-list and SHALL pass a leak check that fails closed on secret-shaped values, file-system paths, internal hostnames, personal e-mail addresses and the name of any client other than the change's own; a failing page SHALL NOT be delivered. *(Traces: PRD §6 S-4, §9, O-3, AC-3 · Sources: R-19 (riesgo: fuga de información entre tenants), PM-07 · Decision: D-31 · BL-22)*
- **REQ-W3-024** — Self-contained, readable page. The sponsor page SHALL be a single self-contained HTML file with no external requests, readable on a phone and a desktop, in light and dark schemes, in the change's language, and printable. *(Traces: PRD §6 S-4, O-3 · Sources: R-19 · Decision: D-31 · BL-22)*
- **REQ-W3-025** — The report command. WHEN `karvey-context --report` runs, the method SHALL print, for a period and optionally one client, a business-language status of what was released, what is in progress with its phase and age, what is blocked and who unblocks it, the open risks and the decisions awaited from each stakeholder; it SHALL be read-only. *(Traces: PRD §6 S-4, O-3 · Sources: R-19 (`karvey-context --report [--since] [--client]`), PM-07 · BL-22)*
- **REQ-W3-026** — "Your turn" events. The notification settings SHALL accept the events `approval_requested`, `awaiting_human` and `blocked`; WHEN one of them occurs and is enabled, the method SHALL notify the person who must act — the approver, the declared executor, or whoever unblocks — with the change, the item and what is expected; a `blocked` event raised by a judge's verdict SHALL carry that verdict. *(Traces: PRD §6 S-4, O-4, AC-4 · Sources: R-19 ("eventos `approval_requested`, `awaiting_human` y `blocked`"), PM-07, R-11 · BL-22)*
- **REQ-W3-027** — Notifications are not duplicated. Every notification payload SHALL carry a run or iteration id and a timestamp; the method SHALL notify `qa` on the first run and on a verdict change only (unless the project asks for every run), and SHALL NOT re-send a "your turn" event for a state that has not changed. *(Traces: PRD §6 S-4, O-4, AC-4 · Sources: F-48 · BL-43)*

### Open questions and risks with owner and date (R-24)
- **REQ-W3-028** — Open questions are recorded. WHEN `karvey-decisions ask` runs, the method SHALL record a `Q-NN` (reserved by the id tool) with the question, its owner (who decides — a stakeholder role or name), the date from which it blocks (needed-by) and the changes it affects; `decisions cross` ending with no answer SHALL offer to record one. *(Traces: PRD §6 S-5, O-5, AC-5 · Sources: R-24 (`decisions ask`), PM-11 · BL-27)*
- **REQ-W3-029** — A question becomes a decision. WHEN an open question is answered, the method SHALL record the answer as a `D-NN` that cites the `Q-NN`, SHALL mark the question resolved with that reference, and SHALL NOT delete the question. *(Traces: PRD §6 S-5, O-5 · Sources: R-24 ("pasa a `D-NN` cuando se resuelve"), PM-11, REQ-TEAM-022 · BL-27)*
- **REQ-W3-030** — Overdue questions are visible. MODIFIES REQ-W1-068. The dashboard's open-work section SHALL also list every open question with its owner and needed-by, flagging as overdue those past their date, and every open risk of an active change. *(Traces: PRD §6 S-5, O-5, AC-5 · Sources: R-24, PM-11 ("`karvey-context` lista las `Q-NN` vencidas"), R-18 · BL-27)*
- **REQ-W3-031** — A risk register per change. The method SHALL keep a risk register per change in which each risk has an id, a description, a probability and an impact, an owner, a trigger, a mitigation and a state (`open`, `mitigated`, `accepted`, `closed`, `moved`); architecture SHALL create it from its risk analysis and any phase or judge MAY add to it. *(Traces: PRD §6 S-5, O-5 · Sources: R-24 (`risks.md` por cambio), PM-11 · BL-27)*
- **REQ-W3-032** — The security judge feeds the register. WHEN a security judge reports a finding that is a risk rather than a defect, the finding SHALL be proposed as a risk entry for the router to accept; judges SHALL NOT write the register directly. *(Traces: PRD §6 S-5 · Sources: R-24 ("el juez de seguridad de R-11 alimenta `risks.md`"), panel §5 (quien observa no enruta) · BL-27)*
- **REQ-W3-033** — Risks reviewed before the qa and release gates. BEFORE the qa gate and the release gate, the method SHALL list every `open` risk of the change with its owner and trigger in the gate summary and ask its owner for a state; in 4.1 an open risk without a reviewed state SHALL warn. *(Traces: PRD §6 S-5, O-5, AC-5 · Sources: R-24 ("revisado en QA y deploy"), PM-11 · BL-27)*
- **REQ-W3-034** — Archive closes or moves every risk. WHEN a change is archived, every risk still `open` SHALL be closed with a reason or moved to the backlog as a `BL-NN` that cites it; none SHALL remain open in an archived change. *(Traces: PRD §6 S-5, O-5 · Sources: R-24, PM-11 ("`karvey-archive` los cierra o los traspasa al backlog") · BL-27)*

### Project design system; design-graphic as a delta (R-26)
- **REQ-W3-035** — One design system per project. The method SHALL keep one design system per project (tokens for colour, type, spacing, radius and motion, and the component inventory), created once — by the first UI change or by importing an existing system — and read by every later UI change. *(Traces: PRD §6 S-6, O-7 · Sources: R-26 (`docs/spec/design-system.md`), DM-13 · BL-29)*
- **REQ-W3-036** — The change declares only its delta. WHEN design-graphic runs for a change, it SHALL record only the tokens and components the change adds or modifies and the screens it scores; an empty delta SHALL be recorded as such, and the design system SHALL be updated with the delta when the change is archived. *(Traces: PRD §6 S-6, O-7, AC-7 · Sources: R-26 ("por cambio, solo el delta"), DM-13 · BL-29)*
- **REQ-W3-037** — Art catalogue is opt-in. The per-component art catalogue SHALL be produced only when the change asks for illustrations or assets; no template SHALL carry country-specific field examples as defaults. *(Traces: PRD §6 S-6 · Sources: R-26 ("el catálogo de arte pasa a opt-in"), DM-13 (plantilla con referencias locales) · BL-29)*
- **REQ-W3-038** — Contrast is computed. The method SHALL ship a contrast tool that computes the WCAG contrast ratio of each declared text/background token pair and reports every pair below its level; design SHALL cite its output. *(Traces: PRD §6 S-6, O-7, AC-7 · Sources: R-26 ("con `contrast-check.py`"), AG-12 · BL-29)*
- **REQ-W3-039** — The design score comes from a judge. MODIFIES REQ-W2-022. WHERE judges are enabled and the lane runs design-graphic, the method SHALL run a design judge before the design approval, with a clean context holding only the design delta, the mockup and the rubric, and with the contrast tool's output as a deterministic sub-score; design-graphic SHALL NOT score itself. *(Traces: PRD §6 S-6, O-7, AC-7 · Sources: R-26 ("el puntaje lo pone el juez UX de R-11"), AG-12, DM-13 · Decision: D-23, D-30 · BL-29)*

### One work breakdown (R-27)
- **REQ-W3-040** — Feature means a functional area. The method SHALL define a Feature only as a functional area of the change (a unit of value) in every rule and skill; pipeline phases SHALL be recorded as a checklist or a field of the Epic, never as Features. *(Traces: PRD §6 S-7, O-8 · Sources: R-27 ("Feature = área funcional"), PM-10 · BL-30)*
- **REQ-W3-041** — QA and deploy belong to the Epic. The method SHALL create the QA review and the deploy work as `E{n}.QA` and `E{n}.DEPLOY` items under the Epic, so that the Epic's totals include QA rework and deploy effort. *(Traces: PRD §6 S-7, O-8 · Sources: R-27 ("agregar `E{n}.QA` y `E{n}.DEPLOY`"), PM-10 · BL-30)*
- **REQ-W3-042** — Hierarchy by parent and child. The method SHALL express the hierarchy Epic → Feature → Task through the tracker's parent/child relation (or the Markdown nesting) and SHALL use dependencies only for order between siblings. *(Traces: PRD §6 S-7, O-8 · Sources: R-27 ("parent/child en vez de dependencias"), PM-10 · BL-30)*
- **REQ-W3-043** — Every task belongs to exactly one Feature. Every task SHALL belong to exactly one Feature or to `E{n}.QA` / `E{n}.DEPLOY`, and the tasks skill SHALL refuse a plan where a requirement's work is split across two Features without a stated reason. *(Traces: PRD §6 S-7, O-8 · Sources: R-27 (regla del 100%), PM-10 · BL-30)*

### Organisation portfolio (R-28)
- **REQ-W3-044** — Client as a first-level field. The project and change settings SHALL carry `client` as a first-level field; the tracker-ids block SHALL keep its historical tag only as a read fallback. *(Traces: PRD §6 S-8, O-9 · Sources: R-28 ("subir `client` a campo de primer nivel"), PM-14 · BL-31)*
- **REQ-W3-045** — A portfolio file lists the repositories. The method SHALL read a portfolio file that lists the organisation's Karvey repositories by path or clone location, with an optional client and owner per entry; paths SHALL be validated before any read. *(Traces: PRD §6 S-8, O-9 · Sources: R-28 (`portfolio.json`), PM-14 · Decision: D-32 · BL-31)*
- **REQ-W3-046** — The portfolio view. WHEN `karvey-context --portfolio` runs, it SHALL show, per client and per repository, the active changes by phase and lane with their age, the open questions and pending approvals awaited from the client, the releases of the period and the cost of the period. *(Traces: PRD §6 S-8, O-9, AC-8 · Sources: R-28, PM-14 · Decision: D-32 · BL-31)*
- **REQ-W3-047** — Read-only and within the reader's access. The portfolio view SHALL be read-only, SHALL read only what the person running it can already read, SHALL mark an unreachable repository as "not read" with the reason, and SHALL NOT publish its output anywhere. *(Traces: PRD §6 S-8, §7, §9, AC-8 · Sources: R-28 (riesgo: controlar quién ve el portafolio), PM-14 · Decision: D-32 · BL-31)*
- **REQ-W3-048** — Both spec layouts are found. The session hook, the dashboard and the portfolio SHALL find a Karvey project whose specs live under `docs/spec/` or under `spec/`, and SHALL report which layout was found. *(Traces: PRD §6 S-8, AC-8 · Sources: F-45 · BL-40)*

### Backlog ranked by WSJF (R-29)
- **REQ-W3-049** — Scoring columns. The backlog SHALL accept for each item a value (1–5), an effort (S/M/L or minutes), a cost of delay or needed-by date, and a client, and SHALL compute a WSJF score as (value + urgency) / effort, with the formula written in the backlog rule. *(Traces: PRD §6 S-9, O-10, AC-9 · Sources: R-29, PM-15 · BL-32)*
- **REQ-W3-050** — `done-direct` state. The backlog lifecycle SHALL include the state `done-direct` for small work done without a change, and SHALL require the commit that did it as its reference. *(Traces: PRD §6 S-9, O-10 · Sources: R-29, PM-15 (BL-01 `done` sin definir) · BL-32)*
- **REQ-W3-051** — The backlog view. WHEN `karvey-context --backlog` runs, it SHALL list open items ordered by score, unscored items apart, and flag items not reviewed for more than 30 days; it SHALL be read-only. *(Traces: PRD §6 S-9, O-10, AC-9 · Sources: R-29, PM-15 · BL-32)*
- **REQ-W3-052** — Refinement cadence. The method SHALL recommend a backlog refinement every 14 days, configurable per project, and the dashboard SHALL show the date of the last refinement and flag it when overdue. *(Traces: PRD §6 S-9, O-10 · Sources: R-29 ("refinar el backlog cada 2 semanas"), PM-15 · BL-32)*

### Portability (R-30)
- **REQ-W3-053** — A portability guide, one supported runtime. The repository SHALL ship a portability guide that lists every behaviour that depends on the runtime (tool names, the question tool, subagents, session hooks, statusline, plugin install) and how a team could adapt it, and SHALL state that Claude Code is the only supported runtime. *(Traces: PRD §6 S-10, §7, O-11 · Sources: R-30, AG-14 · Decision: D-32 · BL-33)*
- **REQ-W3-054** — Browsing can be delegated. The project settings SHALL accept `browse.via` as `local`, `agent:<name>` or `none`; the browse skill SHALL run locally, send a self-contained instruction to the named agent, or report "not evaluated", accordingly. *(Traces: PRD §6 S-10, O-11 · Sources: R-30 (`project.json:browse.via`), AG-14 · BL-33)*
- **REQ-W3-055** — No OS-only commands. No skill SHALL instruct an OS-specific command to open a file; it SHALL detect the platform's opener or ask the user to open the path, and the linter SHALL report OS-only commands. *(Traces: PRD §6 S-10, O-11, AC-10 · Sources: R-30 (`open` de un solo sistema operativo), AG-14 · BL-33)*
- **REQ-W3-056** — No fixed country time. No rule or skill SHALL fix a country's time zone; dates SHALL use the project's declared time zone or the environment's, in ISO 8601 with the offset. *(Traces: PRD §6 S-10, O-11, AC-10 · Sources: R-30 (hora de un país fija), AG-14 · BL-33)*
- **REQ-W3-057** — Neutral incident states with aliases. The incident lifecycle SHALL use neutral English state names and SHALL accept the existing localized names as aliases, so that trackers already written in them remain valid. *(Traces: PRD §6 S-10, O-11, AC-10 · Sources: R-30 ("estados neutrales con alias localizados"), AG-14 · BL-33)*
- **REQ-W3-058** — The loaded version is the one checked. WHEN the health skill checks method readiness, it SHALL read the version the runtime actually loaded (from the runtime's installed-plugins record), SHALL report the marketplace clone's version only as "available", and SHALL say which it could not read. *(Traces: PRD §6 S-10, O-11 · Sources: R-30 ("leer la versión desde `installed_plugins.json`"), AG-14 · BL-33)*
- **REQ-W3-059** — Team settings are validated. WHEN the session hook or the dashboard reads the team settings, it SHALL validate the tool, the five logical statuses, the channel, the target and the via against their enums and documented aliases, and SHALL print "settings invalid (…)" naming each failing key rather than treating the project as configured. *(Traces: PRD §6 S-10, O-11 · Sources: F-21 · BL-38)*
- **REQ-W3-060** — Method text names no one environment. No skill or rule SHALL carry a person's name, an organisation's stack-specific check or a runtime model name as an example actor; examples SHALL use roles and placeholders. *(Traces: PRD §6 S-10, §9, O-11 · Sources: R-30, AG-14 (rastros de un stack y entorno particulares), REQ-W1-078 · BL-33)*

### Rollout 4.1.0 and dogfooding
- **REQ-W3-061** — Every new check has a mode. Every check this change adds SHALL declare its mode in the check-modes table, and in 4.1 SHALL default to advisory or warn, except the leak check of the sponsor page and the missing-file check of load lists, which are blocking. *(Traces: PRD §6 S-11, §9, O-12, AC-12 · Sources: Ola 3 plan, REQ-W2-083 · Decision: D-24)*
- **REQ-W3-062** — Nothing that passed under 4.0 fails. A project that passes `validate --strict` and the linter under 4.0.0 SHALL still pass under 4.1.0 with the default modes. *(Traces: PRD §6 S-11, O-12, AC-12 · Sources: Ola 3 plan · Decision: D-24)*
- **REQ-W3-063** — Migration to the Wave 3 shape. MODIFIES REQ-W1-009. WHEN `validate --fix` runs, the state tool SHALL also propose moving a non-empty tracker client tag to `client`, SHALL show the diff before writing, SHALL NOT create or flip any approval, and SHALL produce the same file when run twice. *(Traces: PRD §6 S-11, S-8, O-12 · Sources: R-28, R-01 (`--fix`) · BL-31)*
- **REQ-W3-064** — Measured before and after. The release of 4.1.0 SHALL carry the context size before and after (REQ-W3-010) and the cost of this change (REQ-W3-014) in its release notes. *(Traces: PRD §6 S-11, O-1, O-2, O-6 · Sources: R-15, R-25 · Decision: D-30)*
- **REQ-W3-065** — Built with itself. This change SHALL run in the `feature-ui` lane on this repository in trunk mode, SHALL carry the change trailer on every commit, SHALL record its own effort at every phase close, and SHALL produce its own sponsor page at each gate close. *(Traces: PRD §6 S-11, §9, AC-6 · Sources: panel Ola 1 (dogfooding), H-22 · Decision: D-04, D-26, D-31)*

### Method page in nine languages — last (B-06)
- **REQ-W3-066** — Four more languages. MODIFIES REQ-ADP-031. The method page SHALL offer, besides English, Spanish, Portuguese, German and Chinese (Simplified), Italian, Japanese, French and Korean, embedded in the same file, with the same selection, memory, `?lang=` and browser-language behaviour for all nine. *(Traces: PRD §6 S-12, O-13, AC-11 · Sources: B-06 (owner: last, after all changes))*
- **REQ-W3-067** — Every string in every language. Every translatable string of the method page SHALL exist in all nine languages, and the linter SHALL fail when a key is missing or empty in any of them. *(Traces: PRD §6 S-12, O-13, AC-11 · Sources: B-06)*
- **REQ-W3-068** — Self-contained scripts render. The method page SHALL remain self-contained (no external requests), SHALL set the document language for each selection, and SHALL render Japanese, Korean and Chinese text with system font fallbacks only. *(Traces: PRD §6 S-12, O-13 · Sources: B-06, REQ-ADP-030)*
- **REQ-W3-069** — Renamed anchors resolve. The method page SHALL resolve every anchor id published since 3.10.0 that was later renamed, through an alias table, in every language. *(Traces: PRD §6 S-12, O-13, AC-11 · Sources: F-47 · BL-42)*
- **REQ-W3-070** — The page reflects 4.1. The method page SHALL describe the Wave 3 additions (load lists, sponsor page, open questions and risks, cost per change, design system, portfolio, WSJF backlog, portability guide) with counts that match the plugin, in every language, and SHALL be the last feature implemented in this change. *(Traces: PRD §6 S-12, O-13 · Sources: B-06 (owner: last), REQ-W1-058)*

## MODIFIED Requirements

### Requirement: REQ-ADP-031
<!-- COMPLETELY replaces REQ-ADP-031 (as amended by REQ-W1-102..REQ-W1-106). Reason: four more languages (B-06, REQ-W3-066). -->
- **REQ-ADP-031** *(amended: REQ-W1-102..REQ-W1-106, REQ-W3-066..REQ-W3-069)* — THE page `docs/karvey.html` SHALL be
  authored in English by default (what renders with JavaScript disabled, with no inert language switch) AND SHALL offer
  a language switch to Spanish, Portuguese, German, Chinese (Simplified), Italian, Japanese, French and Korean, embedded
  in the same file; the chosen language SHALL be remembered per viewer when the browser allows it, and only when the
  value is valid; `?lang=en|es|pt|de|zh|it|ja|fr|ko` (and `xx-YY` by its first two letters) SHALL select a language for
  that visit without overwriting a saved choice; ON a first visit with neither, THE page SHALL select the browser's
  primary language when it is one of the nine, and English otherwise; THE tab title and the document language SHALL
  follow the selected language; every translatable string SHALL exist in all nine; switching SHALL keep other query
  parameters; a malformed or changed hash SHALL be handled without error, and an anchor renamed since 3.10.0 SHALL
  resolve through an alias table. *(Traces: team-adapters PRD; wave1 PRD; wave3 PRD §6 S-12, O-13 · Sources: B-06,
  F-47 · BL-42)*

### Requirement: REQ-W1-009
<!-- Replaces REQ-W1-009 (as modified by wave2-structural) by adding the client move (REQ-W3-063). -->
- **REQ-W1-009** — Migration of legacy `spec.json` (`--fix`). WHEN the state tool runs `validate --fix` on a
  legacy `spec.json`, the state tool SHALL map the legacy phase values to the enum, SHALL convert `gates_skipped`
  into `skipped`, SHALL map `management: "none"` to `markdown`, SHALL propose a `lane` inferred from the recorded
  skipped phases, SHALL move a non-empty `approvals.deploy` into `deploys` and drop an empty one, SHALL propose
  moving a non-empty tracker client tag to the first-level `client`, SHALL show the diff before writing, SHALL NOT
  create or flip any approval, and SHALL produce the same file when run twice. *(Traces: wave1 PRD §6 S-1, AC-1;
  wave2 PRD §6 S-13; wave3 PRD §6 S-11, S-8 · Sources: R-01, R-09, R-28, F-28 · BL-04, BL-46, BL-31)*

### Requirement: REQ-W1-068
<!-- Replaces REQ-W1-068 by adding open questions and risks (REQ-W3-030). -->
- **REQ-W1-068** — Open work section. WHEN the dashboard runs, the dashboard SHALL show an OPEN WORK section with:
  findings by type and status per change, every `BUG-NN` not resolved, every `[human]` task in `awaiting-human` with
  its executor and since when, every backlog item `open`, every tracker operation pending reconciliation
  (REQ-W1-090), every open question `Q-NN` with its owner and needed-by (flagging the overdue ones), and every open
  risk of an active change with its owner. *(Traces: wave1 PRD §6 S-10, O-10; wave3 PRD §6 S-5, O-5, AC-5 · Sources:
  R-18, R-24, H-30, PM-11 · BL-21, BL-27)*

### Requirement: REQ-W2-003
<!-- Replaces REQ-W2-003 by adding the cost per change (REQ-W3-018). -->
- **REQ-W2-003** — Metrics per lane and period. WHEN the metrics view is requested for a project and a period, the
  method SHALL compute, per lane and for all lanes: lead time (change created → production approval), cycle time per
  phase, human approval wait per gate, throughput (archived changes per week), deploy frequency, change failure rate,
  time to restore, spec-gap rate and ripple per change, gate rejection rate, estimate accuracy, judge finding
  acceptance rate, judge cost, and the cost per change (US$, tokens, human review minutes) aggregated per lane, per
  client and per period with the share that is estimated. *(Traces: wave2 PRD §6 S-1, O-2; wave3 PRD §6 S-3, O-6,
  AC-6 · Sources: R-14, R-25, DM-11, PM-05, PM-08 · Decision: D-30 · BL-17, BL-28)*

### Requirement: REQ-W2-008
<!-- Replaces REQ-W2-008 by adding cost outliers (REQ-W3-019). -->
- **REQ-W2-008** — The retro works on the method's artifacts. WHEN the retro runs for a period, it SHALL present the
  metrics of REQ-W2-003, the findings by type and by the phase that found them, the estimate accuracy, the judge
  cost and every change whose cost exceeds three times its lane's median for the period (with at least three
  measured changes in the lane); SHALL store the result in `docs/spec/retros/retro-{date}.md`; and SHALL record each
  agreed action as a `BL-NN` of type `process` with an owner. *(Traces: wave2 PRD §6 S-1, O-2; wave3 PRD §6 S-3, O-6 ·
  Sources: R-14, R-25, PM-08, PM-12, DM-11 · Decision: D-30 · BL-17)*

### Requirement: REQ-W2-022
<!-- Replaces REQ-W2-022 by adding the design judge (REQ-W3-039). -->
- **REQ-W2-022** — Where judges run. WHERE judges are enabled, the method SHALL run the judges before the human gate
  of the requirements, the architecture and the qa phases, and of the design-graphic phase when the lane runs it
  (design judge with the contrast tool's output as a deterministic sub-score), and SHALL allow a project to add or
  remove phases in the judge settings. *(Traces: wave2 PRD §6 S-3, O-4, AC-3; wave3 PRD §6 S-6, O-7, AC-7 · Sources:
  R-11, R-26, JU-01, DM-06, AG-12 · Decision: D-23 · BL-14, BL-29)*

## REMOVED Requirements

None.
