# PRD: wave3-optimization

## 1. Executive summary
Wave 1 (3.12.0) made the method's guarantees real and Wave 2 (3.13.0 → 4.0.0) made the cost of the process
scale with the change and measured it. What neither wave changed is **what the method costs to read and what it
tells the people outside the session**: every phase still loads most of the rules transitively, the sponsor of a
change learns its state only by asking, open questions and risks have no owner or date, the cost of a change is
measured only for judges and teams, each UI change redesigns the palette, "Feature" means two things in the
tracker, nobody sees all the repositories of an organisation at once, the backlog captures but does not rank, and
several steps silently assume one operating system, one country and one runtime (expert panel 2026-09-23, Ola 3:
R-15, R-19, R-24..R-30). Wave 3 ships as **4.1.0**, a backward-compatible minor release on top of 4.0.0. The
method page in four more languages (board item B-06) is its last feature, by the owner's request.

## 2. 🎯 Goal (the change's north star)
> **Every phase loads only the instructions it declares, and the sponsor of any change can read — from one page
> produced from the change's own artifacts — its scope, state, measured cost, open risks and the decisions it
> waits for, while the organisation sees every Karvey repo in one read-only portfolio; the per-phase instruction
> size and the cost per change are measured before and after, never capped.**

This goal is the north star that all Karvey phases pursue: each phase re-reads it on start to advance toward
the result without stopping until it is achieved, respecting the plan and security gates.

## 3. Problem and context
- **Who has it:** the agent that runs the skills (context it pays for and does not use), the human approver
  (waits nobody is told about), the sponsor who pays for a change (no view without asking), whoever runs several
  repositories or clients (no aggregate view), and teams outside the author's environment (hidden assumptions).
- **Current situation** (`docs/spec/reviews/2026-09-23-panel-review.md` §3, judge reports DM/PM/AG):
  - **Context budget** (R-15, AG-04, H-34): a phase loads 3k–27k tokens; the rule graph is almost complete
    (`phase-close` and `project-config` cite 7–8 rules each), so any phase reaches 11–17 of the rules. After
    Wave 2 the skills total ≈335 KB and the rules ≈143 KB — larger than when the panel measured. Tracker
    examples of one tool sit in skills used with another; first-use settings are loaded on every init; the
    orchestrator carries text that does not route. Per-phase rule lists drift from what skills cite (BL-39).
  - **Stakeholders** (R-19, PM-07): notifications cover only qa, deploy and incident, all to the team channel; a
    pending approval, a `[human]` task in `awaiting-human` or a blocked task reaches nobody; the PRD's
    Stakeholders section is never used again; a retried run posts the whole summary again (BL-43). Wave 2
    produces a release manifest that no report reads yet.
  - **Open questions and risks** (R-24, PM-11): `decisions cross` ends in "no answer exists" with no owner or
    date; architecture's risk table is never reviewed by qa, deploy or archive.
  - **Cost per change** (R-25, PM-08, BL-37): cost is recorded for judges (Wave 2) and for the team layer, not
    for the default single agent; the statusline receives the session cost and throws it away; nothing adds
    cost per client.
  - **Design system** (R-26, DM-13, AG-12): design-graphic redefines palette, type, spacing and motion on every
    change, builds an exhaustive art catalogue and scores itself (≥ 8) — contrast, which is computable, is
    judged by the same model.
  - **WBS** (R-27, PM-10): "Feature" is both a functional area and a pipeline phase; QA Review and Deploy items
    hang outside the E.F.T hierarchy; dependencies duplicate the parent/child relation.
  - **Portfolio** (R-28, PM-14): configuration and dashboard are per project; the client exists only as
    `clickup.client_tag`; repositories that keep specs under `spec/` are invisible (BL-40).
  - **Backlog** (R-29, PM-15): only high/med/low; no value, effort or cost of delay; an undefined `done` state
    for direct work; items reviewed only by the change that produced them.
  - **Portability** (R-30, AG-14, BL-38): the file opener used is available on one OS only; one country's time zone is written into a rule;
    incident states are in one human language inside an English body; browsing assumes a local browser; the
    health check reads the version of the marketplace clone, not the one the runtime loaded; team settings with a
    drifted key look configured.
  - **Method page** (B-06, BL-42): five languages; the owner wants Italian, Japanese, French and Korean added,
    after every other change; 12 anchors renamed after 3.10.0 no longer resolve.
- **Impact:** a cycle that needs 2–3 sessions because of instructions it does not use; approvals that wait
  because nobody was told; sponsors who learn the state by asking; risks that reach production unreviewed; no
  margin per client; inconsistent UI across changes; boards whose sums do not add up; priorities decided by who
  complains loudest; and steps a team outside the author's setup cannot run.

## 4. Objectives and success metrics
| # | Objective | Metric |
|---|---|---|
| O-1 | Measure before reorganising | a per-phase instruction-size snapshot (bytes and estimated tokens, minimum and closure) of the 4.0.0 content exists before any skill is reorganised; the same tool measures 4.1.0 |
| O-2 | Smaller phases | median per-phase closure size falls by at least 40% against the O-1 snapshot, with 0 hard contracts lost (contract coverage check green) |
| O-3 | The sponsor is informed without asking | 100% of gate closes of a change with a declared sponsor produce the sponsor page; 0 internal-only fields in it (leak check green) |
| O-4 | "Your turn" reaches whoever must act | `approval_requested`, `awaiting_human` and `blocked` notify when enabled; human approval wait (Wave 2 metric) reported before/after |
| O-5 | Open questions and risks have owners | every Q-NN and every open risk has an owner and a date; overdue ones visible in the dashboard; 0 open risks unreviewed at the qa and release gates |
| O-6 | Cost per change measured | every phase close records the change's effort (US$, tokens, human review minutes) or "n/a + reason"; metrics add it per lane, client and period; nothing caps it (D-30) |
| O-7 | One design system per project | a UI change records only its token/component delta; its contrast is computed, not self-scored |
| O-8 | One meaning of Feature | the tracker holds Features = functional areas, phases on the Epic, QA and deploy items under the Epic |
| O-9 | The organisation in one view | one read-only command answers "how are we doing with client X" across every listed repository |
| O-10 | A backlog that ranks | every open backlog item has a WSJF score or "unscored"; direct work recorded as `done-direct` with its commit |
| O-11 | Fewer hidden assumptions | 0 OS-only commands, 0 fixed country time, neutral incident states with aliases, browse delegable, loaded version read correctly; a portability guide (Claude Code the only supported runtime, D-32) |
| O-12 | Safe minor release | no project that passes under 4.0.0 fails because of a Wave 3 check; migrations are dry-run first |
| O-13 | Method page in nine languages | `docs/karvey.html` offers en, es, pt, de, zh, it, ja, fr, ko with every string translated; renamed anchors resolve |

## 5. User stories / main use cases
- As the **agent running a phase**, I want to load a small core plus the list of rules my phase declares, so that
  the context I pay for is the context I use and a cycle fits in fewer sessions.
- As the **sponsor of a change**, I want one page, refreshed at every gate, that says in business language what is
  being built, where it is, what it has cost, what could go wrong and what is waiting for me.
- As the **human approver or executor of a `[human]` task**, I want to be told when it is my turn.
- As **whoever owns a decision**, I want each open question recorded with me as its owner and the date it starts
  blocking, so that it is answered in time.
- As the **person accountable for margin**, I want the cost of every change, summed per client and period.
- As a **designer**, I want the project's design system defined once and each change to declare only its delta,
  with contrast computed by a tool.
- As a **project manager**, I want the tracker to hold one hierarchy — Epic, functional Features, Tasks, plus QA
  and deploy under the Epic — so that its sums add up.
- As **whoever leads several repositories or clients**, I want one read-only portfolio across all of them.
- As the **backlog owner**, I want items ranked by an explicit score and direct work recorded.
- As a **team outside the author's environment**, I want no step to assume a particular OS, country, language or
  local browser, and a guide that says what depends on the runtime.
- As a **reader of the method page**, I want it in my language.

## 6. Scope (in scope)
Internal order: measure first (S-1 baseline), then the areas that add data (S-3..S-9), then the context
reorganisation over the final Wave 3 text (S-1..S-2, so that no skill is restructured twice), then rollout (S-11)
and, **last**, the method page languages (S-12, B-06).

| # | Area | Panel item | Backlog / board | Decisions |
|---|---|---|---|---|
| S-1 | Context measurement: per-phase instruction size (min, closure), baseline and after, in CI | R-15 | BL-18 | — |
| S-2 | Context budget: `_core.md` hard contracts, closed `Load:` lists, tracker adapters per tool, deploy and init split into core + references, routing-only orchestrator, one phase per session, contract coverage check, generated per-phase rule lists | R-15 | BL-18, BL-39 | — |
| S-3 | Cost per change with a single agent: `effort` per phase close, estimated flag, per lane/client/period, outliers in the retro | R-25 | BL-28, BL-37 | D-30 |
| S-4 | Sponsor page per change (scope, state, cost, risks, pending decisions, release) published at each gate close to the declared stakeholder; `karvey-context --report`; "your turn" events; notification deduplication | R-19 | BL-22, BL-43 | D-31 |
| S-5 | Open questions `Q-NN` with owner and needed-by; per-change `risks.md` reviewed at qa and release, closed or moved at archive | R-24 | BL-27 | — |
| S-6 | Project design system; design-graphic as a delta; art catalogue opt-in; design judge with a contrast tool | R-26 | BL-29 | D-23, D-30 |
| S-7 | WBS: Feature = functional area; phases on the Epic; `E{n}.QA`, `E{n}.DEPLOY`; parent/child | R-27 | BL-30 | — |
| S-8 | Organisation portfolio: `client` first-level, portfolio file, `karvey-context --portfolio`, read-only, both spec layouts | R-28 | BL-31, BL-40 | D-32 |
| S-9 | Backlog WSJF, `done-direct`, `karvey-context --backlog`, refinement cadence | R-29 | BL-32 | — |
| S-10 | Portability: guide (Claude Code only), `browse.via`, OS-neutral open, time zone, neutral incident states with aliases, loaded-version read, team settings validated | R-30 | BL-33, BL-38 | D-32 |
| S-11 | Rollout 4.1.0: advisory defaults, migrations dry-run, before/after measurement, dogfooding | Ola 3 plan | — | D-24, D-26 |
| S-12 | **Last:** method page in it / ja / fr / ko; alias table for renamed anchors | — | B-06, BL-42 | — |

## 7. Out of scope
- **Official support for other runtimes** (D-32): the portability guide says what depends on Claude Code and how a
  team could adapt it; no other runtime is tested or supported, and no generated `AGENTS.md` ships as a supported
  artifact.
- **Caps on cost** (D-30): cost is measured and reported, never used to stop, shorten or skip work.
- **Sending the sponsor page by e-mail or any channel the project did not declare**; hosting it on a public URL.
- **A portfolio that writes**: the portfolio never modifies a repository, tracker or setting.
- **Allowing a PR URL alone as the production approval reference** (PM-11 item 5): D-03 keeps the D-NN + PR +
  `spec.json` record.
- **Emergent backlog outside this wave's areas:** BL-34, BL-35, BL-36 (team layer), BL-41 (statusline width),
  BL-51 (`project-upgrade`, its own change).
- **Rewriting skill content that is not about loading** during the context reorganisation: text moves, it is not
  redesigned.
- **Editing the owner's personal global instructions** or anything outside this repository.

## 8. Stakeholders
- **Requests and approves:** the method's owner (approves the three gates of this change and production —
  `role: human`).
- **Impacted:** every project using Karvey, the agents running its skills, and the sponsors who will receive the
  new page.
- **Sources:** the expert panel (DM, PM, AG judges), the owner's decisions D-30..D-32, the emergent backlog and
  the agent board (B-06).

## 9. Constraints
- **Security Tier: 2** — the sponsor page and the portfolio read several repositories and produce a summary for
  people outside the team; new scripts read `project.json` values (stakeholder destination, portfolio paths) into
  file reads and commands; the reorganisation could drop a hard rule from a phase. Controls required: the page
  and the portfolio exclude secrets, internal paths, personal e-mail addresses and other clients' data by an
  allow-list of fields and a leak check that fails closed; paths and destinations are validated before use; the
  portfolio reads only what the reader can already read; a contract coverage check proves every hard contract is
  still loaded by the phases that need it.
- **Backward compatible** (minor release): every new check starts advisory or warn; `validate` accepts the 4.0.0
  shapes; migrations are shown dry-run and never create or flip an approval.
- **Public, organisation-neutral text:** no rule, skill or example names a company, product, client, internal
  URL, person's e-mail or personal path; actors are roles.
- **Dogfooding:** built through the method on this repo in the `feature-ui` lane (the sponsor page and the method
  page are UI), trunk flow, Markdown tracker (`PLAN.md`); every commit carries `Karvey-Change: wave3-optimization`.
- **Prerequisite:** `wave2-structural` merged (this branch is forked from it).
- **Decisions this change depends on:** D-30, D-31, D-32; D-01..D-29 still hold.

## 10. Acceptance criteria
- **AC-1** The per-phase size snapshot of 4.0.0 is stored before any skill moves, and the same tool reproduces it
  byte-identically on the same input.
- **AC-2** After the reorganisation the median per-phase closure is at least 40% smaller, and the contract
  coverage check is green for every phase.
- **AC-3** Closing a gate of a change with a declared sponsor writes the sponsor page; the leak check refuses a
  page that contains a secret-shaped value, an internal path, a personal e-mail or another client's name.
- **AC-4** With the events enabled, a pending approval, an `awaiting-human` task and a blocked task each notify
  once per state change (a retry does not duplicate).
- **AC-5** `decisions ask` records a Q-NN with owner and needed-by; an overdue Q-NN and every open risk show in
  the dashboard; the qa and release gates list the open risks.
- **AC-6** This change's own `spec.json` carries its `effort` per phase; `--metrics` sums it per lane and client.
- **AC-7** A UI change with no new tokens records an empty design delta; the contrast tool's result appears in the
  design judge's verdict.
- **AC-8** `karvey-context --portfolio` over a file listing several repositories (one with `spec/`, one
  unreachable) shows per client active changes, age, pending decisions, releases and cost, and marks the
  unreachable one as not read.
- **AC-9** `karvey-context --backlog` ranks open items by WSJF and flags unscored and stale ones.
- **AC-10** The linter finds 0 OS-only commands and 0 fixed country times; incident states validate in neutral
  form and via their aliases.
- **AC-11** The method page renders in nine languages, every translation key is complete, and each renamed anchor
  resolves.
- **AC-12** The plugin linter and guard tables are green; no Wave 3 check fails a project that passes under
  4.0.0 while its mode is advisory.
