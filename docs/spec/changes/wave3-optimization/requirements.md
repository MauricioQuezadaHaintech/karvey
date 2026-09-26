# Requirements: wave3-optimization

## Project description

Wave 3 (4.1.0) optimises what the method costs to read and what it tells the people outside the session: a
per-phase context budget with a core of hard contracts and closed load lists, measured before and after; the cost
of every change with a single agent; one page per change for its sponsor and "your turn" events; open questions
and risks with owner and date; a project design system; one meaning of Feature in the tracker; a read-only
portfolio across the organisation's repositories; a ranked backlog; fewer hidden assumptions about OS, country,
language and runtime — and, last, the method page in four more languages (panel review 2026-09-23, Ola 3; board
item B-06). North star (PRD §2): *every phase loads only the instructions it declares, and the sponsor of any
change can read — from one page produced from the change's own artifacts — its scope, state, measured cost, open
risks and the decisions it waits for, while the organisation sees every Karvey repo in one read-only portfolio;
the per-phase instruction size and the cost per change are measured before and after, never capped.*

## Conventions

- **IDs.** `REQ-W3-NNN`, numbered contiguously. The heading also carries the numeric EARS id (`1.1`, `1.2`…)
  required by `rules/ears-format.md`.
- **Trace line.** Each requirement cites the PRD (`PRD §n` / scope `S-n` / objective `O-n` / acceptance `AC-n`)
  and its sources: panel recommendation `R-xx`, verified panel finding `H-xx`, judge item `DM-xx`/`PM-xx`/`AG-xx`,
  board item `B-xx`, backlog item `BL-NN`, and decision `D-NN`.
- **Living spec baseline.** The REQ-W1-* (and carried REQ-ADP-*) blocks of `wave1-hardening` and the REQ-W2-*
  blocks of `wave2-structural` are treated as already part of the living spec. Where a Wave 3 requirement changes
  one of them, it says **MODIFIES REQ-…**; `spec-delta.md` lists it under MODIFIED.
- **Modes.** As in Wave 2: **advisory** (reported, never refuses), **warn** (reported on the gate summary and in
  the dashboard, never refuses) or **blocking** (refuses). "In 4.1" means the default of release 4.1.0. A project
  can always choose a stricter mode.
- **Technology.** The SHALL text names *roles* of the method. Where the panel or the owner fixed a public name (a
  command, file or field the user types or reads), the glossary maps the role to that name; languages and
  runners are architecture decisions.
- **Actors.** "the method" = the skills and rules as shipped; "a phase skill" = any skill that owns a phase; "the
  human" = the person who owns the change's approvals (`role: human`); "the sponsor" = the stakeholder declared
  for the project or change who pays for or commissions it; "a judge" = an independent reviewing subagent (R-11).
- **Measure, never cap.** "Never capped" in the north star applies to cost (D-30): nothing stops, shortens or skips
  work because of cost. The size limits (REQ-W3-003, REQ-W3-008, REQ-W3-011) bound the method's own text through the
  linter and never stop a change's work. Single-agent cost is first recorded by 4.1, so its "before" is stated as not
  measured and this change's own record is the first figure later changes compare against (REQ-W3-064).
- **Neutrality.** No requirement, rule or example names an organisation, product, client, internal URL, person's
  e-mail or personal path (PRD §9).

### Glossary — roles and their public names

| Role in the requirements | Public name fixed by the panel / owner | Source |
|---|---|---|
| the **core** | `rules/_core.md` | R-15, AG-04 |
| the **load list** | a `Load:` line in each SKILL.md | R-15, AG-04 |
| the **size tool** | `scripts/karvey-context-budget` (name final at architecture) | R-15 |
| the **tracker adapters** | `rules/adapters/{tool}.md` | R-15, AG-04 |
| the **references** | `skills/{skill}/references/*.md` | R-15, AG-04 |
| the **effort record** | `spec.json:effort` | R-25, PM-08 |
| the **sponsor page** | `changes/{id}/sponsor.html` | R-19, D-31 |
| the **stakeholder settings** | `project.json:stakeholders` | R-19, D-31 |
| the **report** | `karvey-context --report` | R-19, PM-07 |
| the **open question** | `Q-NN`, `karvey-decisions ask` | R-24, PM-11 |
| the **risk register** | `changes/{id}/risks.md` | R-24, PM-11 |
| the **design system** | `docs/spec/design-system.md` | R-26, DM-13 |
| the **contrast tool** | `scripts/contrast-check` | R-26, AG-12 |
| the **client** | `project.json:client`, `spec.json:client` | R-28, PM-14 |
| the **portfolio file / view** | `portfolio.json`, `karvey-context --portfolio` | R-28, D-32 |
| the **backlog view** | `karvey-context --backlog` | R-29, PM-15 |
| the **browse settings** | `project.json:browse.via` (`local` \| `agent:<name>` \| `none`) | R-30, AG-14 |
| the **portability guide** | `docs/portability.md` | R-30, D-32 |
| the **method page** | `docs/karvey.html` | B-06, REQ-ADP-031 |

---

## Requirement 1: Context budget and progressive loading (R-15)

### 1.1 REQ-W3-001 — Per-phase instruction size is measured
WHEN the size tool runs on the plugin, it SHALL report, per phase skill, the size of the skill, of the rules it
loads directly and of the transitive closure of the rules it loads, in bytes and in estimated tokens (marked
estimated), and SHALL offer a structured (JSON) form.

Traces to PRD: §6 S-1, O-1, AC-1 · Sources: R-15, AG-04, AG §2.4, H-34 · BL-18

**Scenario — success:** GIVEN the plugin at 4.0.0 WHEN the size tool runs THEN every phase skill has a row with
skill, direct and closure sizes, and the JSON form holds the same numbers.
**Scenario — error:** GIVEN a skill whose load list names a rule that does not exist WHEN the size tool runs THEN
it reports the missing rule with the skill and line, and exits non-zero.

### 1.2 REQ-W3-002 — Baseline before the reorganisation
The method SHALL store the size snapshot of the 4.0.0 content, with the date and the method version, in a commit that
precedes every commit of this change that moves a skill or rule. (Reproducibility of the tool's output is REQ-W3-071.)

Traces to PRD: §6 S-1, O-1, AC-1 · Sources: R-15 ("hay que re-probar"), Wave 2 baseline pattern (REQ-W2-006) · BL-18

**Scenario — success:** GIVEN the baseline stored at the first reorganisation commit's parent WHEN the change's test
phase checks the order THEN the snapshot's commit precedes every commit that moves a skill or rule.
**Scenario — error:** GIVEN a reorganisation commit with no baseline stored before it WHEN the change's test
phase checks the order THEN it reports "baseline missing or taken after the reorganisation".

### 1.3 REQ-W3-003 — A core of hard contracts
The method SHALL ship one core rule, loaded by every phase skill, that states the hard contracts every phase
must honour — state changes only through the state tool, the gate and approval contract, the production gate,
the branch and commit contract including the change trailer, the verification failure modes, the finding
router, the neutrality of public text — each with a stable contract id, and SHALL keep it at or below 1,000
words.

Traces to PRD: §6 S-2, O-2 · Sources: R-15 (`_core.md` ~800 palabras), AG-04 · BL-18

**Scenario — success:** GIVEN the core rule WHEN counted THEN it has at most 1,000 words and every contract
carries an id.
**Scenario — error:** GIVEN a core rule of 1,200 words WHEN the linter runs THEN it reports the count against the
limit.

### 1.4 REQ-W3-004 — Each skill declares a closed load list
Each phase skill SHALL declare near its top a closed list of the rules and references it loads; the skill SHALL
NOT instruct the agent to open any rule outside that list; a citation of another rule for context SHALL be a
footnote that is not opened.

Traces to PRD: §6 S-2, O-2 · Sources: R-15 ("cada skill declare `Load:` como una lista cerrada"), AG-04 · BL-18

**Scenario — success:** GIVEN a phase skill WHEN the linter compares the rules it tells the agent to read with its
load list THEN every one is in the list.
**Scenario — error:** GIVEN a skill whose body says "read `rules/x.md`" and whose load list omits it WHEN the
linter runs THEN it reports the skill, the line and the rule.

### 1.5 REQ-W3-005 — Rules do not load each other
A rule SHALL NOT require loading another rule; cross-references between rules SHALL be footnotes, so that the
closure of a load list equals the list plus the core.

Traces to PRD: §6 S-2, O-2 · Sources: R-15 (`phase-close.md` cita 7, `project-config.md` cita 8), AG-04 · BL-18

**Scenario — success:** GIVEN every rule WHEN the size tool computes closures THEN each phase's closure equals its
load list plus the core.
**Scenario — error:** GIVEN a rule that says "load `rules/y.md` before continuing" WHEN the linter runs THEN it
reports it as a load instruction inside a rule.

### 1.6 REQ-W3-006 — Tracker detail loaded only for the team's tool
The method SHALL keep the tool-specific detail of each tracker in its own adapter file and SHALL load only the
adapter of the tool resolved from the project's management settings; no phase skill body SHALL carry
tool-specific examples of one tracker.

Traces to PRD: §6 S-2, O-2 · Sources: R-15 ("adaptadores a `adapters/{tool}.md`"), AG-04 (ejemplos de un tracker en init, tasks, impl) · BL-18

**Scenario — success:** GIVEN a project whose tracker is Markdown WHEN a phase runs THEN no tracker adapter other
than Markdown's is loaded.
**Scenario — error:** GIVEN a phase skill that embeds an API call of one tracker WHEN the linter runs THEN it
reports the tool-specific example outside the adapters.

### 1.7 REQ-W3-007 — Rare paths move to references
The method SHALL move exactly these rare paths into references of their skill, loaded only when that path is taken:
the first-use team settings and the `--settings` path of init, and the documentation-only, hotfix, post-deploy
verification and branch-hygiene paths of deploy; the skill SHALL keep a one-line pointer that says when to load each
reference. Any further section moves only by adding it to this list through a spec revision.

Traces to PRD: §6 S-2, O-2 · Sources: R-15 ("partir deploy en núcleo + `references/`", "mover `init --settings`"), AG-04 · BL-18

**Scenario — success:** GIVEN a project that already has its team settings WHEN init runs THEN the settings
reference is not loaded.
**Scenario — error:** GIVEN a reference that no skill points to WHEN the linter runs THEN it reports it as
orphaned.

### 1.8 REQ-W3-008 — The orchestrator only routes
The orchestrator skill SHALL contain only routing — the state tool's next phase, the lane and the skill to run — and
pointers, in at most 1,200 words counted as for the core (the 4.0.0 file holds about 3,100); feature lists, per-phase
descriptions, equivalence tables and authorship SHALL move to the README or references.

Traces to PRD: §6 S-2, O-2 · Sources: R-15 ("el orquestador queda solo con el ruteo"), AG-04 (≈2,9k tokens que no rutean) · BL-18

**Scenario — success:** GIVEN the orchestrator WHEN the size tool counts it THEN it has at most 1,200 words and it
routes every phase of every lane.
**Scenario — error:** GIVEN a phase that the orchestrator can no longer route after the move WHEN the routing
table test runs THEN it fails naming the phase and lane.

### 1.9 REQ-W3-009 — No hard contract is lost
WHEN the context reorganisation is complete, a contract coverage check SHALL prove, for every phase skill, that
every hard contract that applied to it before the move is still reachable through the core or its load list, and
SHALL fail naming the contract and the phase otherwise.

Traces to PRD: §6 S-2, O-2, AC-2 · Sources: R-15 (riesgo: "re-probar que ninguna fase pierda una regla que necesita"), AG-04 · BL-18

**Scenario — success:** GIVEN the reorganised plugin WHEN the check runs THEN every (phase, contract) pair of the
baseline map is covered.
**Scenario — error:** GIVEN the deploy skill with the production-gate contract removed from its load path WHEN the
check runs THEN it fails with "deploy: contract prod-gate not loaded".

### 1.10 REQ-W3-010 — The budget is a target, measured after
WHEN the reorganisation is complete, the size tool SHALL report the per-phase closure against the baseline; the change
SHALL meet a median reduction of at least 40%, and the test phase SHALL fail otherwise; every phase whose own
reduction is below 40% SHALL carry a recorded reason, which never excuses the median.

Traces to PRD: §6 S-2, O-2, AC-2 · Sources: R-15 (−45–55% estimado por AG), AG-04 · BL-18

**Scenario — success:** GIVEN baseline and after snapshots WHEN compared THEN the median closure reduction is
reported and is ≥ 40%.
**Scenario — error:** GIVEN a median reduction of 35% WHEN the test phase compares THEN it fails naming the median; a
phase below 40% while the median passes is listed with its reason, or flagged as unexplained.

### 1.11 REQ-W3-011 — Size checked in CI
The plugin's CI SHALL run the size tool and SHALL warn when a phase's closure grows more than 10% over the last
released snapshot. (A load list naming a missing file is REQ-W3-072.)

Traces to PRD: §6 S-1, S-2, AC-12 · Sources: R-15, AG-13 (drift that reappears every release) · BL-18

**Scenario — success:** GIVEN a PR that shrinks a skill WHEN CI runs THEN the size step passes and prints the delta.
**Scenario — error:** GIVEN a PR that makes the deploy closure 15% larger WHEN CI runs THEN it prints a warning with
the phase and the percentage.

### 1.12 REQ-W3-012 — Per-phase rule lists are generated, not hand-kept
The orchestrator's "applies in" column, the adapters' "used by" column and every per-phase list of rules in the
README SHALL be generated from the load lists, and the linter SHALL fail when a generated block drifts.

Traces to PRD: §6 S-2 · Sources: R-15, F-42 · BL-39

**Scenario — success:** GIVEN a load list changed in one skill WHEN the generator runs THEN the three tables change
accordingly.
**Scenario — error:** GIVEN a hand edit of a generated block WHEN the linter runs THEN it reports the drift.

### 1.13 REQ-W3-013 — One phase per session is the declared pattern
The method SHALL declare "one phase per session" as its default working pattern: at each gate close it SHALL
offer a checkpoint save and state that the next phase can start in a fresh session, which the session hook
resumes; continuing in the same session SHALL remain allowed.

Traces to PRD: §6 S-2, O-2 · Sources: R-15 ("declarar el patrón una fase por sesión con `checkpoint`"), AG-04, AG §2.4 · BL-18

**Scenario — success:** GIVEN a gate just approved WHEN the phase closes THEN the output offers the checkpoint save
and the fresh-session option.
**Scenario — error:** GIVEN a session that is already above the context threshold `karvey-checkpoint` declares for
rotating a session WHEN a new phase is about to start THEN the method recommends the checkpoint and a fresh session
before loading the next skill.

### 1.14 REQ-W3-071 — The size tool is reproducible
The size tool SHALL produce byte-identical output for the same input (split from REQ-W3-002).

Traces to PRD: §6 S-1, O-1, AC-1 · Sources: R-15, Wave 2 baseline pattern (REQ-W2-006), judge F-26 · BL-18

**Scenario — success:** GIVEN the baseline commit WHEN the tool reruns on it THEN the output equals the stored snapshot
byte for byte.
**Scenario — error:** GIVEN two runs on the same commit that differ (for instance by a timestamp or a file-order
dependence) WHEN the test phase compares them THEN it fails naming the first differing line.

### 1.15 REQ-W3-072 — A missing load-list file fails CI
The plugin's CI SHALL fail when a load list names a file that does not exist (split from REQ-W3-011).

Traces to PRD: §6 S-1, S-2, AC-12 · Sources: R-15, AG-13, judge F-26 · BL-18

**Scenario — success:** GIVEN every load list naming existing files WHEN CI runs THEN the step passes.
**Scenario — error:** GIVEN a load list that names a deleted reference WHEN CI runs THEN it fails naming the skill, the
line and the file.

---

## Requirement 2: Cost per change with a single agent (R-25)

### 2.1 REQ-W3-014 — Effort recorded at each phase close
WHEN a phase closes, the method SHALL add to the change's effort record the AI cost in US$, the tokens and the human
review minutes of the interval since the previous close, per phase, marking each value as `exact`, `estimated` or
`n/a` with its source; the human review minutes SHALL be those the human states at the gate (`exact`), otherwise `n/a`
— the gate wait is not review time and the metrics report it apart (REQ-W2-003).

Traces to PRD: §6 S-3, O-6, AC-6 · Sources: R-25 (`spec.json:effort{ai_usd, tokens, human_review_min}`), PM-08 · Decision: D-30 · BL-28

**Scenario — success:** GIVEN a session whose runtime exposes the session cost WHEN requirements closes THEN the
effort record holds the interval's US$ and tokens marked `exact` and the review minutes.
**Scenario — error:** GIVEN a runtime that exposes no cost WHEN a phase closes THEN the values are recorded as `n/a`
with the reason "runtime exposes no cost", never as zero.

### 2.2 REQ-W3-015 — Cost source captured outside the model
The method SHALL capture the session cost from a runtime source that does not rely on the model's own account (the
statusline input or the session transcript), SHALL keep the last captured value per session so that the interval can
be computed — a session's first close counting from the session's start, and a session that works on several changes
charging each interval to the change whose phase closes — and SHALL NOT spend model turns to collect it.

Traces to PRD: §6 S-3, O-6 · Sources: R-25 (la statusline ya recibe el costo y no se guarda), PM-08, team-layer F-03 · BL-28, BL-37

**Scenario — success:** GIVEN the statusline receives a session cost WHEN it runs THEN the value is stored where the
phase-close step reads it, with no model turn.
**Scenario — error:** GIVEN a runtime cost source that cannot be read WHEN a phase closes THEN the interval is
recorded `n/a` with the reason, and the next readable value starts a new interval instead of charging the gap twice.

### 2.3 REQ-W3-016 — Judge cost kept apart
The effort record SHALL keep the judges' cost (REQ-W2-030) apart from the phase work — judge cost is read only from
the judge run records, and every effort entry carries its kind (`phase`) — so that the cost of the judges can be
judged on its own. (How a judge run's figure is measured is REQ-W3-077.)

Traces to PRD: §6 S-3, O-6 · Sources: R-25 ("el costo de los jueces se registra aparte"), R-11 · Decision: D-30

**Scenario — success:** GIVEN a gate with two judge runs WHEN the effort is read THEN phase cost and judge cost are
two separate figures.
**Scenario — error:** GIVEN an effort entry whose kind is not `phase`, or that repeats a judge run's figure, WHEN the
state tool validates THEN it reports the mixed entry.

### 2.4 REQ-W3-017 — Cost is never a cap
No setting SHALL stop, shorten, skip or ask to confirm any phase, judge or task because of its measured or estimated
cost.

Traces to PRD: §6 S-3, §7 · Sources: R-25 · Decision: D-30

**Scenario — success:** GIVEN a change that costs ten times the median WHEN it continues THEN nothing interrupts it
and the retro flags it.
**Scenario — error:** GIVEN a project setting that declares a cost limit WHEN `validate` runs THEN it reports the key
as unsupported, citing D-30.

### 2.5 REQ-W3-018 — Cost per lane, client and period
MODIFIES REQ-W2-003. WHEN the metrics view is requested, it SHALL also compute the cost per change (US$, tokens,
human review minutes) and aggregate it per lane, per client and per period, reporting how much of each figure is
estimated.

Traces to PRD: §6 S-3, O-6, AC-6 · Sources: R-25 ("agregarlo por `client_tag`"), PM-08 · Decision: D-30 · BL-28

**Scenario — success:** GIVEN three archived changes of two clients WHEN metrics run THEN each client's total and the
estimated share are shown.
**Scenario — error:** GIVEN a change with no effort record WHEN metrics run THEN it appears as "n/a (no effort)" and is
excluded from the cost aggregate only.

### 2.6 REQ-W3-019 — Outliers in the retro
MODIFIES REQ-W2-008. WHEN the retro runs, it SHALL flag every change whose cost exceeds three times the median of the
period for its lane (with at least three measured changes in the lane), with its phases' share, as an input for the
discussion, not as a verdict.

Traces to PRD: §6 S-3, O-6 · Sources: R-25, PM-08 ("un cambio cuyo costo supere X veces la mediana se señala en la retro") · Decision: D-30

**Scenario — success:** GIVEN one change at 4× the lane median WHEN the retro runs THEN it is listed with the phase that
cost most.
**Scenario — error:** GIVEN a lane with fewer than three measured changes WHEN the retro runs THEN no outlier is claimed
and it says "too few changes in lane".

### 2.7 REQ-W3-077 — Judge cost measured from the runtime
MODIFIES REQ-W2-030. WHEN a judge run finishes, the method SHALL record the token usage the runtime reports for that
judge's subagent, marked `exact`; WHERE the runtime reports none, the estimate SHALL count every input the judge read (the
prompt and the files it opened), not only the prompt, and SHALL be marked `estimated`.

Traces to PRD: §6 S-3, O-6 · Sources: R-25, R-11, finding F-34 (a prompt-only estimate understated the runtime figure
about four times) · Decision: D-30 · BL-28

**Scenario — success:** GIVEN a judge subagent whose result reports its token total WHEN the run is recorded THEN that total
is stored as `exact`.
**Scenario — error:** GIVEN a runtime that reports no usage WHEN the run is recorded THEN the estimate includes the files the
judge opened and is marked `estimated`, never `exact`.

---

## Requirement 3: Sponsor page and "your turn" events (R-19)

### 3.1 REQ-W3-020 — Stakeholders declared in the project
The project settings SHALL declare the stakeholders of the project — at least the sponsor, and optionally the approver
and the executor — each with a role, a display name and a destination resolved through the notification adapters; a
change MAY override any of them.

Traces to PRD: §6 S-4, O-3 · Sources: R-19, PM-07 ("usar la sección Stakeholders del PRD") · Decision: D-31 · BL-22

**Scenario — success:** GIVEN a project with a sponsor declared WHEN a change starts THEN its PRD Stakeholders section is
pre-filled from it.
**Scenario — error:** GIVEN a sponsor destination that is a literal webhook URL WHEN `validate` runs THEN it refuses and
asks for the name of the secret instead.

### 3.2 REQ-W3-021 — One page per change, from the artifacts
WHEN the sponsor page is produced, it SHALL be generated only from the change's artifacts and state — scope from the
PRD and requirements, state and lane from the phase history, cost from the effort record, risks from the risk
register, pending decisions from the open questions whose owner matches the sponsor's role or display name
(case-insensitive) and, WHERE the sponsor is also the change's declared approver (matched the same way), from the gates
of the change waiting for that human approval, and what reached production from the release manifest — in business language (no requirement,
finding or decision ids other than the change id, no file paths and no command names in the body), with the date of
every figure.

Traces to PRD: §6 S-4, O-3, AC-3 · Sources: R-19 (reporte en lenguaje de negocio), PM-07 · Decision: D-31 · BL-22

**Scenario — success:** GIVEN a change at the architecture gate WHEN the page is produced THEN it shows scope, phase,
cost to date, open risks and questions for the sponsor, each dated.
**Scenario — error:** GIVEN a change with no effort record WHEN the page is produced THEN the cost section says "not
measured" instead of a number.

### 3.3 REQ-W3-022 — Published at every gate close
WHEN a gate of a change with a declared sponsor closes (approved or changes requested), the method SHALL regenerate
the sponsor page and SHALL deliver it to the sponsor's destination; WHERE no sponsor is declared, it SHALL produce
nothing and say so once.

Traces to PRD: §6 S-4, O-3, AC-3 · Decision: D-31 · Sources: R-19 · BL-22

**Scenario — success:** GIVEN the *what* gate approved WHEN it closes THEN the page is regenerated and delivered once.
**Scenario — error:** GIVEN the delivery fails WHEN the gate closes THEN the gate still closes, the failure is recorded
for reconciliation and the page — which passed the leak check — stays in the change folder.

### 3.4 REQ-W3-023 — Nothing internal leaves
The sponsor page SHALL contain only fields on an allow-list and SHALL pass a leak check that fails closed on values
matching the method's secret patterns, absolute or home-relative file-system paths, hostnames under non-public
suffixes or in private address ranges, e-mail addresses other than a declared stakeholder destination, and the names
of other clients taken from the portfolio file where it is readable (WHERE it is not, the check SHALL say
"other-client names not checked" and still run the rest); the check SHALL run before the page is written, and a failing
page SHALL NOT be delivered nor written to any path — the page last written stays unchanged and only a refusal report
naming each failing field and rule, never the matched value, is recorded.

Traces to PRD: §6 S-4, §9, O-3, AC-3 · Sources: R-19 (riesgo: fuga de información entre tenants), PM-07 · Decision: D-31 · BL-22

**Scenario — success:** GIVEN a page built from clean artifacts WHEN the leak check runs THEN it passes and the page is
delivered.
**Scenario — error:** GIVEN a risk text that quotes a connection string WHEN the leak check runs THEN delivery is
refused naming the field and the rule, the page is neither sent nor written, and the refusal report does not contain the
string.

### 3.5 REQ-W3-024 — Self-contained, readable page
The sponsor page SHALL be a single self-contained HTML file with no external requests, readable on a phone and a
desktop (no horizontal scroll from 360 to 1440 CSS px wide), in light and dark schemes, in the change's language, and
printable (a print style that shows every section and hides only navigation).

Traces to PRD: §6 S-4, O-3 · Sources: R-19 · Decision: D-31 · BL-22

**Scenario — success:** GIVEN the page opened offline WHEN rendered THEN every section displays.
**Scenario — error:** GIVEN a template edit that adds a remote font WHEN the linter runs THEN it reports the external
request.

### 3.6 REQ-W3-025 — The report command
WHEN `karvey-context --report` runs, the method SHALL print, for a period and optionally one client, a business-language
status of what was released, what is in progress with its phase and age, what is blocked and who unblocks it, the open
risks and the decisions awaited from each stakeholder; it SHALL be read-only.

Traces to PRD: §6 S-4, O-3 · Sources: R-19 (`karvey-context --report [--since] [--client]`), PM-07 · BL-22

**Scenario — success:** GIVEN a period with one release and two changes in progress WHEN the report runs THEN both
sections list them.
**Scenario — error:** GIVEN a client that has no changes WHEN the report runs for it THEN it says "no changes for
client" and exits zero.

### 3.7 REQ-W3-026 — "Your turn" events
MODIFIES REQ-ADP-011. The notification settings SHALL accept the events `approval_requested`, `awaiting_human` and `blocked`; WHEN one of
them occurs and is enabled, the method SHALL notify the person who must act — the approver, the declared executor, or
whoever unblocks — at the destination of the stakeholder with that role, else the team destination, with the change,
the item and what is expected; a `blocked` event raised by a judge's verdict SHALL carry that verdict.

Traces to PRD: §6 S-4, O-4, AC-4 · Sources: R-19 ("eventos `approval_requested`, `awaiting_human` y `blocked`"), PM-07, R-11 · BL-22

**Scenario — success:** GIVEN `approval_requested` enabled WHEN the *how* gate asks its question THEN the approver's
destination receives one message naming the change and the gate.
**Scenario — error:** GIVEN an `awaiting_human` task with no declared executor WHEN the event fires THEN it goes to the
team destination and says "no executor declared".

### 3.8 REQ-W3-027 — Notifications are not duplicated
Every notification payload SHALL carry a run or iteration id and a timestamp; the method SHALL notify `qa` on the
first run and on a verdict change only (unless the project asks for every run), SHALL NOT re-send a deploy
notification for the same version and environment, and SHALL NOT re-send a "your turn" event for a state that has not
changed.

Traces to PRD: §6 S-4, O-4, AC-4 · Sources: F-48 · BL-43

**Scenario — success:** GIVEN a QA micro-loop that runs three times with the same verdict WHEN it notifies THEN one
message is sent.
**Scenario — error:** GIVEN a deploy retry of the same version WHEN it notifies THEN the message carries the retry's
run id and no second "deployed" is sent.

### 3.9 REQ-W3-080 — Business wording for states
The sponsor page SHALL show phases, the lane and risk states only through a wording table shipped with the method for
each supported language — for risks: `open` → "being watched", `mitigated` → "reduced", `accepted` → "accepted as is",
`closed` → "no longer a risk", `moved` → "carried to later work" — and the linter SHALL fail when a state has no wording
in a supported language.

Traces to PRD: §6 S-4, O-3, AC-3 · Sources: R-19 (lenguaje de negocio), mockup finding F-40 · Decision: D-31 · BL-22

**Scenario — success:** GIVEN a risk in state `mitigated` WHEN the page is produced in English THEN its state reads
"reduced".
**Scenario — error:** GIVEN a state added without a wording in one language WHEN the linter runs THEN it names the state
and the language.

---

## Requirement 4: Open questions and risks with owner and date (R-24)

### 4.1 REQ-W3-028 — Open questions are recorded
WHEN `karvey-decisions ask` runs, the method SHALL record a `Q-NN` (reserved by the id tool) with the question, its
owner (who decides — a stakeholder role or name), the date from which it blocks (needed-by) and the changes it
affects, and MAY record a context in business words (the options seen and the effect of waiting), which the sponsor
page shows under the question; `decisions cross` ending with no answer SHALL offer to record one.

Traces to PRD: §6 S-5, O-5, AC-5 · Sources: R-24 (`decisions ask`), PM-11 · BL-27

**Scenario — success:** GIVEN an unanswered question WHEN `ask` runs with owner and needed-by THEN a Q-NN is recorded
with both.
**Scenario — error:** GIVEN `ask` without an owner or a needed-by date WHEN it runs THEN it refuses and names the missing
field.

### 4.2 REQ-W3-029 — A question becomes a decision
WHEN an open question is answered, the method SHALL record the answer as a `D-NN` that cites the `Q-NN`, SHALL mark the
question resolved with that reference, and SHALL NOT delete the question.

Traces to PRD: §6 S-5, O-5 · Sources: R-24 ("pasa a `D-NN` cuando se resuelve"), PM-11, REQ-TEAM-022 · BL-27

**Scenario — success:** GIVEN Q-03 answered WHEN recorded THEN D-40 cites Q-03 and Q-03 shows "resolved → D-40".
**Scenario — error:** GIVEN a D-NN that claims to resolve a Q-NN that does not exist WHEN `validate` runs THEN it reports
the dangling reference.

### 4.3 REQ-W3-030 — Overdue questions are visible
MODIFIES REQ-W1-068. The dashboard's open-work section SHALL also list every open question with its owner and
needed-by, flagging as overdue those past their date, and every open risk of an active change.

Traces to PRD: §6 S-5, O-5, AC-5 · Sources: R-24, PM-11 ("`karvey-context` lista las `Q-NN` vencidas"), R-18 · BL-27

**Scenario — success:** GIVEN Q-05 needed by yesterday WHEN the dashboard runs THEN Q-05 is listed as overdue with its
owner.
**Scenario — error:** GIVEN a question with a malformed date WHEN the dashboard runs THEN it is listed as "date invalid"
rather than skipped.

### 4.4 REQ-W3-031 — A risk register per change
The method SHALL keep a risk register per change in which each risk has an id, a description, a probability and an
impact, an owner, a trigger, a mitigation, a state (`open`, `mitigated`, `accepted`, `closed`, `moved`) and its last
review (date and reviewer); architecture SHALL create it from its risk analysis and any phase or judge MAY add to it;
WHERE the lane skips architecture, the first phase that adds a risk SHALL create it, and a change without a register
SHALL be read as having no risks.

Traces to PRD: §6 S-5, O-5 · Sources: R-24 (`risks.md` por cambio), PM-11 · BL-27

**Scenario — success:** GIVEN architecture with two identified risks WHEN it closes THEN the register holds both with an
owner and a trigger.
**Scenario — error:** GIVEN a risk without an owner WHEN the state tool validates the change THEN it reports the risk id
and the missing owner.

### 4.5 REQ-W3-032 — The security judge feeds the register
WHEN a security judge reports a finding that is a risk rather than a defect, the finding SHALL be proposed as a risk
entry for the router to accept; judges SHALL NOT write the register directly.

Traces to PRD: §6 S-5 · Sources: R-24 ("el juez de seguridad de R-11 alimenta `risks.md`"), panel §5 (quien observa no enruta) · BL-27

**Scenario — success:** GIVEN a judge finding tagged risk WHEN iterate routes it THEN a risk entry is added citing the
finding.
**Scenario — error:** GIVEN a judge output that edits the register WHEN the judge run is collected THEN the edit is
refused and reported.

### 4.6 REQ-W3-033 — Risks reviewed before the qa and release gates
WHEN the qa gate or the release gate is asked, the method SHALL list every `open` risk of the change with its owner,
trigger and last review in the gate summary and ask its owner for a state; in 4.1 an open risk whose last review
predates the start of that phase SHALL warn.

Traces to PRD: §6 S-5, O-5, AC-5 · Sources: R-24 ("revisado en QA y deploy"), PM-11 · BL-27

**Scenario — success:** GIVEN two open risks WHEN the release gate is asked THEN both appear with owner and trigger.
**Scenario — error:** GIVEN an open risk not reviewed since architecture WHEN the qa gate summary is built THEN it carries
the warning "risk R-2 unreviewed".

### 4.7 REQ-W3-034 — Archive closes or moves every risk
WHEN a change is archived, every risk still `open` SHALL be closed with a reason or moved to the backlog as a `BL-NN`
that cites it; none SHALL remain open in an archived change.

Traces to PRD: §6 S-5, O-5 · Sources: R-24, PM-11 ("`karvey-archive` los cierra o los traspasa al backlog") · BL-27

**Scenario — success:** GIVEN one open risk at archive WHEN archive runs THEN it is moved to BL-NN and marked `moved`.
**Scenario — error:** GIVEN an open risk the human neither closes nor moves WHEN archive runs THEN archive stops and names
the risk.

---

## Requirement 5: Project design system; design-graphic as a delta (R-26)

### 5.1 REQ-W3-035 — One design system per project
The method SHALL keep one design system per project (tokens for colour, type, spacing, radius and motion, and the
component inventory), created once — by the first UI change or by importing an existing system — and read by every
later UI change.

Traces to PRD: §6 S-6, O-7 · Sources: R-26 (`docs/spec/design-system.md`), DM-13 · BL-29

**Scenario — success:** GIVEN a project with a design system WHEN a new UI change reaches design THEN the phase reads it
and does not redefine it.
**Scenario — error:** GIVEN a project without one WHEN the first UI change reaches design THEN it proposes creating it
from the change's work or from a pinned `inputs.design_system`.

### 5.2 REQ-W3-036 — The change declares only its delta
WHEN design-graphic runs for a change, it SHALL record only the tokens and components the change adds or modifies and
the screens it scores; an empty delta SHALL be recorded as such, and the design system SHALL be updated with the
delta when the change is archived (a token another change modified meanwhile is REQ-W3-076).

Traces to PRD: §6 S-6, O-7, AC-7 · Sources: R-26 ("por cambio, solo el delta"), DM-13 · BL-29

**Scenario — success:** GIVEN a change with one new component WHEN design closes THEN the delta lists that component only.
**Scenario — error:** GIVEN a change that redefines the primary colour without saying so WHEN design closes THEN the
difference against the design system is reported as an undeclared modification.

### 5.3 REQ-W3-037 — Art catalogue is opt-in
The per-component art catalogue SHALL be produced only when the change asks for illustrations or assets; no template
SHALL carry country-specific field examples as defaults.

Traces to PRD: §6 S-6 · Sources: R-26 ("el catálogo de arte pasa a opt-in"), DM-13 (plantilla con referencias locales) · BL-29

**Scenario — success:** GIVEN a change with no asset request WHEN design runs THEN no art catalogue is produced.
**Scenario — error:** GIVEN a template with a country-specific identifier field as its example WHEN the linter runs THEN
it reports it.

### 5.4 REQ-W3-038 — Contrast is computed
The method SHALL ship a contrast tool that computes the WCAG contrast ratio of each declared text/background token
pair against the pair's target level declared in the design system (AA or AAA, normal or large text; AA normal text,
4.5:1, when undeclared) and reports every pair below it; design SHALL cite its output.

Traces to PRD: §6 S-6, O-7, AC-7 · Sources: R-26 ("con `contrast-check.py`"), AG-12 · BL-29

**Scenario — success:** GIVEN a palette whose body text reaches 7:1 WHEN the tool runs THEN it reports AA and AAA passed.
**Scenario — error:** GIVEN a token value the tool cannot parse WHEN it runs THEN it names the token and exits non-zero
instead of assuming a value.

### 5.5 REQ-W3-039 — The design score comes from a judge
MODIFIES REQ-W2-022. WHERE judges are enabled and the lane runs design-graphic, the method SHALL run a design judge
before the design approval, with a clean context holding only the design delta, the mockup and the rubric, and with
the contrast tool's output as a deterministic sub-score; design-graphic SHALL NOT score itself.

Traces to PRD: §6 S-6, O-7, AC-7 · Sources: R-26 ("el puntaje lo pone el juez UX de R-11"), AG-12, DM-13 · Decision: D-23, D-30 · BL-29

**Scenario — success:** GIVEN a `feature-ui` change WHEN design is ready THEN the gate summary shows the design judge's
verdict and the contrast result.
**Scenario — error:** GIVEN a design-graphic output that contains a self-assigned score WHEN the linter runs THEN it
reports the self-score.

### 5.6 REQ-W3-076 — Design-system conflicts stop the apply
The design delta SHALL record, for each token it modifies, the design system's value when design-graphic ran; WHEN the
delta is applied at archive and the design system's current value of such a token differs from that base value, the
method SHALL NOT overwrite it, SHALL report the token, both values and the change that last modified it, and SHALL ask
the human which value to keep.

Traces to PRD: §6 S-6, O-7 · Sources: R-26, DM-13, judge F-11 (two UI changes in flight modifying one token) · BL-29

**Scenario — success:** GIVEN a delta that modifies a token nobody else changed WHEN archive applies it THEN the value is
written with no question.
**Scenario — error:** GIVEN two changes in flight that both modify the primary colour, the first already archived WHEN the
second is archived THEN the apply stops for that token, shows both values and the first change, and waits for the human.

---

## Requirement 6: One work breakdown (R-27)

### 6.1 REQ-W3-040 — Feature means a functional area
The method SHALL define a Feature only as a functional area of the change (a unit of value) in every rule and skill;
pipeline phases SHALL be recorded as a checklist or a field of the Epic, never as Features; tracker items created
under 4.0 in the old shape SHALL be left as they are and reported by the tracker reconciliation as `legacy shape`,
never rewritten.

Traces to PRD: §6 S-7, O-8 · Sources: R-27 ("Feature = área funcional"), PM-10 · BL-30

**Scenario — success:** GIVEN requirements with four areas WHEN Features are created THEN four exist and the phases
appear on the Epic.
**Scenario — error:** GIVEN a rule text that maps a phase to a Feature WHEN the linter runs THEN it reports the text.

### 6.2 REQ-W3-041 — QA and deploy belong to the Epic
MODIFIES REQ-W1-089. The method SHALL create the QA review and the deploy work as `E{n}.QA` and `E{n}.DEPLOY` items under the Epic,
found or created by those natural keys, so that
the Epic's totals include QA rework and deploy effort.

Traces to PRD: §6 S-7, O-8 · Sources: R-27 ("agregar `E{n}.QA` y `E{n}.DEPLOY`"), PM-10 · BL-30

**Scenario — success:** GIVEN a change reaching QA WHEN QA creates its item THEN it is `E{n}.QA` under the Epic.
**Scenario — error:** GIVEN a QA item created at the root of the list WHEN the tracker reconciliation runs THEN it is
reported as outside the hierarchy.

### 6.3 REQ-W3-042 — Hierarchy by parent and child
The method SHALL express the hierarchy Epic → Feature → Task through the tracker's parent/child relation (or the
Markdown nesting) and SHALL use dependencies only for order between siblings.

Traces to PRD: §6 S-7, O-8 · Sources: R-27 ("parent/child en vez de dependencias"), PM-10 · BL-30

**Scenario — success:** GIVEN a tracker with sub-items WHEN tasks are created THEN each is a child of its Feature and no
dependency duplicates it.
**Scenario — error:** GIVEN a tool with no parent/child relation WHEN tasks are created THEN the adapter records the
parent in a field and says so, rather than creating a dependency.

### 6.4 REQ-W3-043 — Every task belongs to exactly one Feature
Every task SHALL belong to exactly one Feature or to `E{n}.QA` / `E{n}.DEPLOY`, and the tasks skill SHALL refuse a plan
where a requirement's work is split across two Features without a stated reason.

Traces to PRD: §6 S-7, O-8 · Sources: R-27 (regla del 100%), PM-10 · BL-30

**Scenario — success:** GIVEN a plan WHEN checked THEN every task has one parent.
**Scenario — error:** GIVEN a task with no parent WHEN the plan is checked THEN it is reported with its id.

---

## Requirement 7: Organisation portfolio (R-28)

### 7.1 REQ-W3-044 — Client as a first-level field
The project and change settings SHALL carry `client` as a first-level field; the tracker-ids block SHALL keep its
historical tag only as a read fallback.

Traces to PRD: §6 S-8, O-9 · Sources: R-28 ("subir `client` a campo de primer nivel"), PM-14 · BL-31

**Scenario — success:** GIVEN a project with `client` set WHEN a change starts THEN the change inherits it.
**Scenario — error:** GIVEN a change whose `client` differs from its tracker tag WHEN `validate` runs THEN it warns and
names both values.

### 7.2 REQ-W3-045 — A portfolio file lists the repositories
The method SHALL read a portfolio file that lists the organisation's Karvey repositories by local path, with an
optional clone location (information only), client and owner per entry; paths SHALL be validated before any read.

Traces to PRD: §6 S-8, O-9 · Sources: R-28 (`portfolio.json`), PM-14 · Decision: D-32 · BL-31

**Scenario — success:** GIVEN a portfolio file with five repositories WHEN it is read THEN five entries are validated.
**Scenario — error:** GIVEN an entry whose path contains a shell metacharacter WHEN it is read THEN it is refused and
named.

### 7.3 REQ-W3-046 — The portfolio view
WHEN `karvey-context --portfolio` runs, it SHALL show, per client and per repository, the active changes by phase and
lane with their age, the open questions owned by the client's stakeholders and the gates waiting for a human approval,
the releases of the period and the cost of the period.

Traces to PRD: §6 S-8, O-9, AC-8 · Sources: R-28, PM-14 · Decision: D-32 · BL-31

**Scenario — success:** GIVEN three repositories of two clients WHEN the view runs THEN it groups them by client with
the four column groups (active changes with phase, lane and age; questions and approvals awaited; releases; cost).
**Scenario — error:** GIVEN a repository with no Karvey project WHEN the view runs THEN it is shown as "not a Karvey
project" and the rest still render.

### 7.4 REQ-W3-047 — Read-only and within the reader's access
The portfolio view SHALL be read-only (it SHALL NOT write, fetch, pull or clone, and SHALL open no network
connection), SHALL read only what the person running it can already read in a local clone, SHALL mark an unreachable repository
(no local clone included) as "not read" with the reason, and SHALL NOT publish its output anywhere.

Traces to PRD: §6 S-8, §7, §9, AC-8 · Sources: R-28 (riesgo: controlar quién ve el portafolio), PM-14 · Decision: D-32 · BL-31

**Scenario — success:** GIVEN every repository readable WHEN the view runs THEN no file changes in any of them and no
network request is made.
**Scenario — error:** GIVEN one repository without read permission and one entry with a clone location but no local
clone WHEN the view runs THEN it shows "not read: permission denied" and "not read: no local clone" for those two only,
and nothing is fetched.

### 7.5 REQ-W3-048 — Both spec layouts are found
MODIFIES REQ-W1-045. The session hook, the dashboard and the portfolio SHALL find a Karvey project whose specs live under
`docs/spec/` or under `spec/` (excluding the archive and implemented changes under either root), and SHALL report which layout was found.

Traces to PRD: §6 S-8, AC-8 · Sources: F-45 · BL-40

**Scenario — success:** GIVEN a repository with `spec/project.json` WHEN the portfolio runs THEN it is read and marked
layout `spec/`.
**Scenario — error:** GIVEN a repository with both layouts WHEN it is read THEN it reports "two spec roots" and uses
`docs/spec/`.

### 7.6 REQ-W3-078 — The portfolio for one client
WHEN `karvey-context --portfolio --client <name>` runs, the view SHALL show only the entries of that client (matched
case-insensitively) and SHALL say that other clients are not shown.

Traces to PRD: §6 S-8, O-9, AC-8 · Sources: R-28, PM-14, mockup finding F-35 ("how are we doing with client X") · Decision:
D-32 · BL-31

**Scenario — success:** GIVEN six repositories of two clients WHEN the view runs for one client THEN only its three
repositories and its totals appear, with "other clients: not shown".
**Scenario — error:** GIVEN a client name that no entry carries WHEN the view runs THEN it says "no repositories for client"
and exits zero.

### 7.7 REQ-W3-079 — From the portfolio to one change
For every active change it lists, the portfolio view SHALL print the read-only dashboard command that opens that change
in its repository's local clone; it SHALL NOT open it by itself.

Traces to PRD: §6 S-8, O-9 · Sources: R-28, REQ-W1-072 (dashboard read-only), mockup finding F-36 · Decision: D-32 · BL-31

**Scenario — success:** GIVEN an active change in a listed repository WHEN the view runs THEN its row carries the command
that opens that change's dashboard in that repository.
**Scenario — error:** GIVEN a repository shown as "not read" WHEN the view runs THEN no command is printed for its changes.

---

## Requirement 8: Backlog ranked by WSJF (R-29)

### 8.1 REQ-W3-049 — Scoring columns
The backlog SHALL accept for each item a value (1–5), an effort (S/M/L or minutes), a cost of delay (1–5) or needed-by
date, and a client, and SHALL compute a WSJF score as (value + urgency) / effort, where urgency is the cost of delay,
or else derives from the days left to needed-by (past or ≤ 14 → 5, ≤ 30 → 4, ≤ 60 → 3, ≤ 90 → 2, otherwise 1), and
effort is S = 1, M = 2, L = 3 (minutes: ≤ 60 → 1, ≤ 240 → 2, otherwise 3), with the formula written in the backlog
rule.

Traces to PRD: §6 S-9, O-10, AC-9 · Sources: R-29, PM-15 · BL-32

**Scenario — success:** GIVEN an item with value 4, cost of delay 3 and effort S WHEN scored THEN its score is 7.0.
**Scenario — error:** GIVEN an item without effort WHEN scored THEN it is "unscored", never zero.

### 8.2 REQ-W3-050 — `done-direct` state
The backlog lifecycle SHALL include the state `done-direct` for small work done without a change, and SHALL require the
commit that did it as its reference.

Traces to PRD: §6 S-9, O-10 · Sources: R-29, PM-15 (BL-01 `done` sin definir) · BL-32

**Scenario — success:** GIVEN an item closed by commit abc123 WHEN marked `done-direct` THEN the commit is recorded.
**Scenario — error:** GIVEN `done-direct` without a commit WHEN `validate` runs THEN it refuses the state.

### 8.3 REQ-W3-051 — The backlog view
WHEN `karvey-context --backlog` runs, it SHALL list open items ordered by score, unscored items apart, and flag items not
reviewed for more than 30 days; it SHALL be read-only.

Traces to PRD: §6 S-9, O-10, AC-9 · Sources: R-29, PM-15 · BL-32

**Scenario — success:** GIVEN ten open items WHEN the view runs THEN they are ordered by score with the stale ones flagged.
**Scenario — error:** GIVEN a backlog row with a malformed column WHEN the view runs THEN that row is listed as "invalid
row" with its id and the others still render.

### 8.4 REQ-W3-052 — Refinement cadence
The method SHALL recommend a backlog refinement every 14 days, configurable per project, and the dashboard SHALL show the
date of the last refinement and flag it when overdue.

Traces to PRD: §6 S-9, O-10 · Sources: R-29 ("refinar el backlog cada 2 semanas"), PM-15 · BL-32

**Scenario — success:** GIVEN a refinement 5 days ago WHEN the dashboard runs THEN it shows the date without a flag.
**Scenario — error:** GIVEN no refinement ever recorded WHEN the dashboard runs THEN it says "never refined".

---

## Requirement 9: Portability (R-30)

### 9.1 REQ-W3-053 — A portability guide, one supported runtime
The repository SHALL ship a portability guide that lists every behaviour that depends on the runtime (tool names, the
question tool, subagents, session hooks, statusline, plugin install) and how a team could adapt it, and SHALL state that
Claude Code is the only supported runtime.

Traces to PRD: §6 S-10, §7, O-11 · Sources: R-30, AG-14 · Decision: D-32 · BL-33

**Scenario — success:** GIVEN the guide WHEN compared with the runtime-dependent features found by the linter THEN each
one is listed.
**Scenario — error:** GIVEN a new hook event added without a guide entry WHEN the linter runs THEN it reports the missing
entry.

### 9.2 REQ-W3-054 — Browsing can be delegated
The project settings SHALL accept `browse.via` as `local`, `agent:<name>` or `none`; the browse skill SHALL run locally,
send a self-contained instruction to the named agent, or report "not evaluated", accordingly.

Traces to PRD: §6 S-10, O-11 · Sources: R-30 (`project.json:browse.via`), AG-14 · BL-33

**Scenario — success:** GIVEN `browse.via: agent:<name>` WHEN a visual check is needed THEN the instruction is sent to that
agent with the URL, steps and evidence expected.
**Scenario — error:** GIVEN `browse.via: none` WHEN QA's visual dimension runs THEN it is "not evaluated" with that reason.

### 9.3 REQ-W3-055 — No OS-only commands
No skill SHALL instruct an OS-specific command to open a file; it SHALL detect the platform's opener or ask the user to
open the path, and the linter SHALL report OS-only commands.

Traces to PRD: §6 S-10, O-11, AC-10 · Sources: R-30 (`open` de un solo sistema operativo), AG-14 · BL-33

**Scenario — success:** GIVEN mockup's comparison board WHEN offered THEN the text gives the path and a detected opener.
**Scenario — error:** GIVEN a skill line with a bare single-OS opener command WHEN the linter runs THEN it is reported.

### 9.4 REQ-W3-056 — No fixed country time
No rule or skill SHALL fix a country's time zone; dates SHALL use the project's declared time zone or the
environment's, in ISO 8601 with the offset.

Traces to PRD: §6 S-10, O-11, AC-10 · Sources: R-30 (hora de un país fija), AG-14 · BL-33

**Scenario — success:** GIVEN a project time zone declared WHEN a changelog date is written THEN it uses that zone.
**Scenario — error:** GIVEN a rule naming a country's time WHEN the linter runs THEN it reports it.

### 9.5 REQ-W3-057 — Neutral incident states with aliases
MODIFIES REQ-W1-068 (its "not resolved" test). The incident lifecycle SHALL use neutral English state names and SHALL
accept the existing localized names as aliases,
so that trackers already written in them remain valid.

Traces to PRD: §6 S-10, O-11, AC-10 · Sources: R-30 ("estados neutrales con alias localizados"), AG-14 · BL-33

**Scenario — success:** GIVEN an incident history written with the localized names WHEN validated THEN it passes, each state
mapped to its neutral name.
**Scenario — error:** GIVEN a state that is neither neutral nor an alias WHEN validated THEN it is reported with the
accepted list.

### 9.6 REQ-W3-058 — The loaded version is the one checked
WHEN the health skill checks method readiness, it SHALL read the version the runtime actually loaded (from the runtime's
installed-plugins record), SHALL report the marketplace clone's version only as "available", and SHALL say which it
could not read.

Traces to PRD: §6 S-10, O-11 · Sources: R-30 ("leer la versión desde `installed_plugins.json`"), AG-14 · BL-33

**Scenario — success:** GIVEN loaded 4.0.0 and a clone at 4.1.0 WHEN health runs THEN it reports "loaded 4.0.0, available
4.1.0".
**Scenario — error:** GIVEN no installed-plugins record WHEN health runs THEN it reports "loaded version unknown" instead of
the clone's.

### 9.7 REQ-W3-059 — Team settings are validated
WHEN the session hook or the dashboard reads the team settings, it SHALL validate the tool, the five logical statuses,
the channel, the target and the via against their enums and documented aliases, and SHALL print "settings invalid (…)"
naming each failing key rather than treating the project as configured.

Traces to PRD: §6 S-10, O-11 · Sources: F-21 · BL-38

**Scenario — success:** GIVEN settings using a documented alias WHEN validated THEN they pass and the alias is shown
normalised.
**Scenario — error:** GIVEN settings with a status map under an unknown key WHEN the session starts THEN it prints
"settings invalid (management.statuses missing)".

### 9.8 REQ-W3-060 — Method text names no one environment
No skill or rule SHALL carry a person's name, an organisation's stack-specific check or a runtime model name as an example
actor; examples SHALL use roles and placeholders.

Traces to PRD: §6 S-10, §9, O-11 · Sources: R-30, AG-14 (rastros de un stack y entorno particulares), REQ-W1-078 · BL-33

**Scenario — success:** GIVEN the incident example WHEN read THEN its actor is a role placeholder.
**Scenario — error:** GIVEN an example row with a person's name WHEN the linter runs THEN it reports it.

---

## Requirement 10: Rollout 4.1.0 and dogfooding

### 10.1 REQ-W3-061 — Every new check has a mode
Every check this change adds over a project's existing artifacts SHALL declare its mode in the check-modes table, and
in 4.1 SHALL default to advisory or warn, except the leak check of the sponsor page (REQ-W3-023) and the missing-file check of load lists (REQ-W3-072), which are
blocking; checks of the plugin's own sources (REQ-W3-011, 012, 067, 069, 072, 080) and refusals of input to a field,
state or register this change introduces (REQ-W3-020, 028, 034, 050, 076) are not project checks — no 4.0 project
holds that input — and keep the refusal their requirement states.

Traces to PRD: §6 S-11, §9, O-12, AC-12 · Sources: Ola 3 plan, REQ-W2-083 · Decision: D-24

**Scenario — success:** GIVEN the check-modes table WHEN linted THEN every Wave 3 check has a mode.
**Scenario — error:** GIVEN a new check absent from the table WHEN the linter runs THEN it reports it.

### 10.2 REQ-W3-062 — Nothing that passed under 4.0 fails
A project that passes `validate --strict` and the linter under 4.0.0 SHALL still pass under 4.1.0 with the default modes.

Traces to PRD: §6 S-11, O-12, AC-12 · Sources: Ola 3 plan · Decision: D-24

**Scenario — success:** GIVEN the 4.0.0 fixtures WHEN validated under 4.1.0 THEN they pass.
**Scenario — error:** GIVEN a 4.0.0 fixture that fails under 4.1.0 WHEN the compatibility test runs THEN it fails naming the
check.

### 10.3 REQ-W3-063 — Migration to the Wave 3 shape
MODIFIES REQ-W1-009. WHEN `validate --fix` runs, the state tool SHALL also propose moving a non-empty tracker client tag to
`client`, under the constraints REQ-W1-009 already sets for every `--fix` move (diff shown first, no approval created or
flipped, same file when run twice).

Traces to PRD: §6 S-11, S-8, O-12 · Sources: R-28, R-01 (`--fix`) · BL-31

**Scenario — success:** GIVEN a change with a client tag WHEN `--fix` runs THEN it proposes `client` and shows the diff.
**Scenario — error:** GIVEN a change whose `client` is already set and differs from its tracker tag WHEN `--fix` runs THEN
it proposes nothing for `client` and reports both values (REQ-W3-044).

### 10.4 REQ-W3-064 — Measured before and after
*Change-scoped: verified in this change and not merged into the living spec (spec-delta.md, change-scoped section).*
The release of 4.1.0 SHALL carry the context size before and after (REQ-W3-010) and the cost of this change
(REQ-W3-014) in its release notes, stating that single-agent cost before 4.1 was not measured, so that later changes
compare against the 4.1 figures.

Traces to PRD: §6 S-11, O-1, O-2, O-6 · Sources: R-15, R-25 · Decision: D-30

**Scenario — success:** GIVEN the release notes WHEN read THEN both measurements are present with their dates.
**Scenario — error:** GIVEN a measurement that could not be taken WHEN the notes are written THEN it is stated "not
measured" with the reason.

### 10.5 REQ-W3-065 — Built with itself: the trailer
*Change-scoped: verified in this change and not merged into the living spec.*
Every commit of this change SHALL carry the change trailer. (Its lane is REQ-W3-073, its effort REQ-W3-074 and its
sponsor page REQ-W3-075.)

Traces to PRD: §6 S-11, §9, AC-6 · Sources: panel Ola 1 (dogfooding), H-22 · Decision: D-04, D-26, D-31

**Scenario — success:** GIVEN this change's production PR WHEN its manifest is computed THEN every commit maps to
`wave3-optimization`.
**Scenario — error:** GIVEN a commit of this change without the trailer WHEN the manifest runs THEN it is listed as unmapped
and fixed before the production gate.

### 10.6 REQ-W3-073 — Built with itself: the lane
*Change-scoped: verified in this change and not merged into the living spec.*
This change SHALL run in the `feature-ui` lane on this repository in trunk mode (split from REQ-W3-065).

Traces to PRD: §6 S-11, §9 · Sources: panel Ola 1 (dogfooding), judge F-26 · Decision: D-04, D-26

**Scenario — success:** GIVEN this change's `spec.json` WHEN validated THEN its lane is `feature-ui` and mockup and
design-graphic are not skipped.
**Scenario — error:** GIVEN a lane lowered without a recorded human decision WHEN the lane check runs THEN it reports the
change.

### 10.7 REQ-W3-074 — Built with itself: its own effort
*Change-scoped: verified in this change and not merged into the living spec.*
This change SHALL record its own effort (REQ-W3-014) at every phase close (split from REQ-W3-065).

Traces to PRD: §6 S-11, AC-6 · Sources: R-25, judge F-26 · Decision: D-30

**Scenario — success:** GIVEN this change at archive WHEN its effort record is read THEN every closed phase has an entry.
**Scenario — error:** GIVEN a phase closed before the effort record existed WHEN archive checks THEN that phase is listed as
"not measured" with the reason, never as zero.

### 10.8 REQ-W3-075 — Built with itself: its own sponsor page
*Change-scoped: verified in this change and not merged into the living spec.*
This change SHALL produce its own sponsor page at each gate close once the page generator exists, with the method's owner
declared as the change's sponsor (the change override of REQ-W3-020) (split from REQ-W3-065).

Traces to PRD: §6 S-11, AC-3 · Sources: R-19, judge F-05, judge F-26 · Decision: D-31

**Scenario — success:** GIVEN the release gate of this change WHEN it closes THEN its sponsor page is regenerated and
passes the leak check.
**Scenario — error:** GIVEN a gate that closed before the generator existed WHEN the page history is read THEN that gate is
listed as "no page (generator not built yet)".

---

## Requirement 11: Method page in nine languages — last (B-06)

### 11.1 REQ-W3-066 — Four more languages
MODIFIES REQ-ADP-031. The method page SHALL offer, besides English, Spanish, Portuguese, German and Chinese (Simplified),
Italian, Japanese, French and Korean, embedded in the same file, with the same selection, memory, `?lang=` and
browser-language behaviour for all nine.

Traces to PRD: §6 S-12, O-13, AC-11 · Sources: B-06 (owner: last, after all changes)

**Scenario — success:** GIVEN a browser whose primary language is Korean WHEN the page is first opened THEN it renders in
Korean and the tab title follows.
**Scenario — error:** GIVEN `?lang=xx` for an unsupported language WHEN opened THEN the page renders in English and no choice
is saved.

### 11.2 REQ-W3-067 — Every string in every language
Every translatable string of the method page SHALL exist in all nine languages, and the linter SHALL fail when a key is
missing or empty in any of them.

Traces to PRD: §6 S-12, O-13, AC-11 · Sources: B-06

**Scenario — success:** GIVEN the page WHEN the completeness check runs THEN every key has nine values.
**Scenario — error:** GIVEN one Japanese key missing WHEN the linter runs THEN it names the key and the language.

### 11.3 REQ-W3-068 — Self-contained scripts render
The method page SHALL remain self-contained (no external requests), SHALL set the document language for each selection,
and SHALL render Japanese, Korean and Chinese text with system font fallbacks only.

Traces to PRD: §6 S-12, O-13 · Sources: B-06, REQ-ADP-030

**Scenario — success:** GIVEN the page offline in Japanese WHEN rendered THEN the text displays with a system font and the
document language is `ja`.
**Scenario — error:** GIVEN a remote font added for CJK WHEN the linter runs THEN it reports the external request.

### 11.4 REQ-W3-069 — Renamed anchors resolve
The method page SHALL resolve every anchor id published since 3.10.0 that was later renamed, through an alias table, in
every language.

Traces to PRD: §6 S-12, O-13, AC-11 · Sources: F-47 · BL-42

**Scenario — success:** GIVEN an old anchor from 3.10.0 WHEN opened THEN the page scrolls to its renamed section.
**Scenario — error:** GIVEN an alias pointing to a missing id WHEN the linter runs THEN it reports the alias.

### 11.5 REQ-W3-070 — The page reflects 4.1
The method page SHALL describe the Wave 3 additions (load lists, sponsor page, open questions and risks, cost per change,
design system, portfolio, WSJF backlog, portability guide) with counts that match the plugin, in every language, and SHALL be
the last feature implemented in this change.

Traces to PRD: §6 S-12, O-13 · Sources: B-06 (owner: last), REQ-W1-058

**Scenario — success:** GIVEN the page and the plugin WHEN the count check runs THEN skills, rules and scripts match.
**Scenario — error:** GIVEN a task of this feature scheduled before another feature's last task WHEN the plan is checked THEN
it is reported as out of order.

---

## Explicit exclusions

- **Official support for other runtimes** (D-32): the portability guide only documents; no generated `AGENTS.md` ships as a
  supported artifact and no other runtime is tested.
- **Any cap, budget stop or confirmation driven by cost** (D-30).
- **Delivering the sponsor page to a destination the project did not declare**, hosting it publicly, or sending other
  clients' data in it.
- **A portfolio that writes** to any repository, tracker or setting, or that publishes its output.
- **A PR URL alone as the production approval reference** (PM-11 item 5): D-03 stands.
- **Redesigning skill content** during the context reorganisation: text moves; behaviour changes only where a requirement
  above says so.
- **Emergent backlog outside these areas:** BL-34, BL-35, BL-36 (team layer), BL-41 (statusline width), BL-51
  (`project-upgrade`, its own change). BL-44..BL-50 were handled in Wave 2.
- **Turning Wave 2 checks blocking**: that is the 4.0 decision (D-24), not this change.
- **Behaviour that does not change:** the finding router and "who observes does not route" (judges and the risk register
  included), the Iron Law, the production approval never delegated and never automatic (D-10 words), the prod gate on by
  default (D-02), `verification.md`, one agent by default with the team layer opt-in, EARS with PRD traceability, the
  spec↔mockup validation in `feature-ui`, lanes and merged gates of Wave 2, and every item of the panel's §5.

## Open points for the owner

Decided while writing and applied as the recommended default (D-21 standing instruction); each can be changed at the *what*
gate. D-30, D-31 and D-32 are not open.

1. **Lane `feature-ui`** for this change: the sponsor page and the method page are UI, so mockup and design-graphic run
   (REQ-W3-065). Lowering it needs the owner.
2. **Budget target: median −40%** of per-phase closure (the panel estimated −45–55%) (REQ-W3-010).
3. **Core limit: 1,000 words** (panel: ~800) (REQ-W3-003).
4. **Sponsor page delivered at every gate close**, both approved and changes-requested outcomes (REQ-W3-022).
5. **Leak check and missing-load-file check blocking in 4.1**; every other Wave 3 check advisory or warn (REQ-W3-061).
6. **Cost outlier = 3× the lane median**, with at least 3 measured changes in the lane (REQ-W3-019).
7. **WSJF = (value + urgency) / effort**; stale backlog item = 30 days; refinement every 14 days (REQ-W3-049, 051, 052).
8. **Risk states** `open | mitigated | accepted | closed | moved`; unreviewed open risk warns (REQ-W3-031, 033).
9. **Neutral incident states** in English with the current localized names as permanent aliases (REQ-W3-057).
10. **Portfolio file lives in the operations repository** (or the spec repository when there is none), not in each project
    (REQ-W3-045).
11. **WSJF mapping** (judges F-06, F-18): urgency = cost of delay 1–5, else days to needed-by (≤ 14 → 5, ≤ 30 → 4, ≤ 60
    → 3, ≤ 90 → 2, else 1); effort S/M/L = 1/2/3, minutes ≤ 60 / ≤ 240 / more = 1/2/3 (REQ-W3-049).
12. **Human review minutes** are what the human states at the gate, else `n/a`; gate wait stays a separate metric
    (REQ-W3-014, judge F-07).
13. **Other-client names** for the leak check come from the portfolio file; when it is unreadable the page says "other-client
    names not checked" and the rest of the check still runs (REQ-W3-023, judge F-10).
14. **This change's sponsor** is the method's owner, declared as a change-level override, so its own sponsor page is produced
    (REQ-W3-065, judge F-05).

Resolved by the second iteration (2026-09-26, pre-approval; recommended option taken under D-21 — each can be changed at
the *what* gate):

15. **Orchestrator limit: 1,200 words** (about 40% of the 4.0.0 file); the rare paths moved to references are a closed
    list in the requirement, not left to architecture — a number and a list a test can check (REQ-W3-007, 008; judge
    F-22).
16. **Bundled requirements split, ids kept**: 002 → 002 + 071, 011 → 011 + 072, 065 → 065 + 073 + 074 + 075; 063 keeps
    only its one addition and cites REQ-W1-009 for the rest — one behaviour per requirement, one success and one error
    scenario each (judge F-26).
17. **Change-scoped obligations**: REQ-W3-064, 065, 073, 074 and 075 bind this release only and are not merged into the
    living spec — they would not hold for later changes (judge F-32).
18. **MODIFIES made explicit** where a living requirement's text changes: REQ-W3-026 → REQ-ADP-011, 041 → REQ-W1-089,
    048 → REQ-W1-045, 057 → REQ-W1-068, 077 → REQ-W2-030. REQ-W3-040, 050 and 058 stay ADDED: the behaviour they change
    lives only in rule text, which no living requirement states (judge F-20).
19. **Design-system conflicts** stop the apply at archive and ask the human, comparing each modified token with the base
    value the delta recorded — the conflict belongs to the delta this change introduces, so it is a requirement here, not
    a backlog item (REQ-W3-076; judge F-11, re-typed from emergent to spec-gap).
20. **Judge cost** is the runtime's reported usage (`exact`); an estimate counts every input the judge read — cost is this
    change's area (REQ-W3-077; F-34, routed instead of deferred).
21. **Portfolio**: a `--client` filter (REQ-W3-078); a printed dashboard command per change, never opened by the view
    (REQ-W3-079); it never fetches, pulls or clones — a clone location is information only (REQ-W3-045, 047) — so the
    view needs no network and no credentials (mockup F-35, F-36, F-37).
22. **Sponsor page**: an optional business context on a question (REQ-W3-028, F-38); gates waiting for the sponsor's
    approval appear under *Waiting for you* when the sponsor is also the approver (REQ-W3-021, F-39); a fixed wording
    table for phases, lane and risk states (REQ-W3-080, F-40); a refused page is never written — only a refusal report
    with field and rule, never the value (REQ-W3-023, F-41).
