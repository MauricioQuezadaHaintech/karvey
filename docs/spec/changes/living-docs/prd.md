# PRD: living-docs

## 1. Executive summary
While a change is in flight, the owner keeps giving instructions — a new detail, a modified requirement, a rule
the agent must respect — and the agents keep working without writing them into the specs. And outside the
change's own artifacts, the project has no technical sheet per component: the shape of the documents in a
document store, the contract of a service, the settings a module reads or the runbook of an infrastructure
resource exist only in the code, if anywhere; failures have come from an undocumented document shape. Each
repository's README drifts in the same way. This change (D-38) makes three kinds of documentation *living*:
**captured instructions**, **component sheets** and **READMEs**, each checked by a tool at the moment the code or
the conversation changes, and brings them to existing projects through the upgrade plan. Target release
**4.2.0**, a backward-compatible minor on top of 4.1.0; implementation starts after `wave3-optimization`'s
implementation, so that the two changes never edit the same skill at the same time.

## 2. 🎯 Goal (the change's north star)
> **No instruction the owner gives during an active change is lost — each is captured verbatim by the hook and
> classified before its gate closes — and every component and repository of a project has a technical sheet and
> a README that change in the same change as the code they describe, so that an agent or a person can learn a
> data shape, a contract, a setting or a runbook from the documents instead of from the code or from a failure.**

This goal is the north star that all Karvey phases pursue: each phase re-reads it on start to advance toward the
result without stopping until it is achieved, respecting the plan and security gates.

## 3. Problem and context
- **Who has it:** the owner of a change (instructions given in conversation do not reach the specs), the agents
  that pick up the work later (they learn shapes and contracts by reading code or by failing), the reviewers and
  judges (they cannot check code against a document that does not exist), and every newcomer to a repository
  (the README does not say how to run it).
- **Current situation:**
  - **Instructions** (D-38, part 1): the approval hook already reads every prompt of the human, but only to
    recognise approvals. Any other instruction lives only in the transcript; nothing makes the agent turn it into
    a requirement revision or a finding, and nothing stops a gate from closing while it is pending.
    `findings.md` is written only by test, qa, browse and judges.
  - **Component documentation** (D-38, part 2): the method has living *behaviour* specs
    (`docs/spec/specs/{capability}/spec.md`) and a per-change architecture, but no document per component that
    outlives the change: no data-store sheet (containers or tables, keys, document shapes, indexes, expiry,
    writers and readers, invariants, migrations), no service sheet (endpoints, settings, dependencies, errors,
    idempotency), no frontend module sheet (routes, state, APIs consumed, permissions) and no infrastructure sheet
    (infrastructure-as-code reference, sizing, network, secret references, runbook). A document store has no
    enforced schema, so an undocumented shape is discovered only when two writers disagree.
  - **READMEs** (D-38, part 3): `karvey-docs` generates Diataxis documentation on demand, but nothing checks that a
    repository's README still says how to install, run, test and configure it after setup files, commands,
    settings or components change.
  - **Existing projects:** a new check that no project has configured helps nobody; the project-upgrade plan
    (D-20) is the path by which new method features reach a project.
- **Impact:** decisions repeated or lost between sessions; requirements that silently diverge from what the owner
  asked; production failures from undocumented data shapes; onboarding by reading code; reviews that cannot
  compare code with an intended shape.

## 4. Objectives and success metrics
| # | Objective | Metric |
|---|---|---|
| O-1 | No lost instruction | 100% of the owner's prompts that the detector classifies as instructions, or that the owner marks for capture, during an active change are captured as `instruction` rows by the hook (0 written by the agent) and acknowledged to the owner, so a missed one is visible at once; 0 gates approved with an unclassified instruction row or an unassigned inbox entry |
| O-2 | Few false captures, visible dismissals | every row the agent marks `not-instruction` or `no spec impact` carries a reason and is listed at the gate the human approves; the detector's precision and recall are measured on a labelled table of prompts in at least three languages |
| O-3 | Nothing private leaks through capture | 0 secret-shaped values in captured rows (redacted before write); only the human's own prompt text is captured, never tool output |
| O-4 | Every component has a sheet | every component declared in the project map has a sheet of its kind, with every mandatory section present or marked `n/a` with a reason |
| O-5 | Sheets move with the code | every commit of a change that touches a component's code paths also touches its sheet, or the check reports it (warn by default; blocking where the project opts in) |
| O-6 | Document shapes match reality | a document-store component's declared schema is compared with a bounded, read-only sample of development documents; drift is reported with field paths and counts only |
| O-7 | Existing repositories are covered | a bootstrap proposes the component map and draft sheets from the code; drafts are marked until a human reviews them |
| O-8 | READMEs stay current | with the README setting on, every repository's README has the minimal section set; a change that touches setup files, commands, settings or components without touching the README is reported |
| O-9 | Existing projects get it | the upgrade catalogue has one step per part; each is dry-run first and applied only when picked |
| O-10 | Cheap to carry | each new rule is loaded only by the phases that declare it; the per-phase closure growth is measured with the size tool, and no phase grows by more than 10% |

## 5. User stories / main use cases
- As the **owner of a change**, I want every instruction I give while the change is open to be recorded as I said
  it and classified, so that I never have to repeat it and I see how each one was handled before I approve.
- As the **owner**, I want to say something off the record (a question, a remark, private context) without it
  being written into the repository.
- As an **agent resuming a change**, I want the captured instructions and their classification in the change's
  findings, so that I start from what was asked, not from a summary.
- As a **developer or agent touching a data store**, I want its sheet — containers, keys, document shapes with an
  example, indexes, expiry, writers and readers, invariants — so that I write documents every reader expects.
- As a **reviewer or judge**, I want the architecture to declare which sheets a change modifies and the commit
  that changes the code to change the sheet, so that I can check one against the other.
- As an **operator**, I want an infrastructure sheet with its sizing, network, secret references and runbook.
- As a **team adopting Karvey on an existing repository**, I want the sheets and the README generated as drafts
  from the code, for a person to review, instead of written from nothing.
- As a **newcomer to a repository**, I want its README to say what it is for, how to start, test and configure it,
  which components it holds and where deploy and operation are described.

## 6. Scope (in scope)
| # | Area | Part of D-38 |
|---|---|---|
| S-1 | Instruction capture: detection (multilingual vocabulary, false-positive rules), the off-the-record and force-capture markers, acknowledgement to the owner, confirm phrases for removal and review, verbatim storage by the hook with redaction, `instruction` rows in `findings.md`, tamper evidence | 1 |
| S-2 | Instruction classification: `requirement-revision` · `finding` · `no-spec-impact` + reason · `not-instruction` + reason; enforced by the state tool at every gate; shown at the gate and in the dashboard | 1 |
| S-3 | Component map in the project settings (component → kind → code paths → sheet) and sheet templates per kind: data store (relational and document), backend service, frontend module, infra resource | 2 |
| S-4 | Sheet lifecycle: component delta declared by architecture, sheet updated in the same commit as the code, check at impl and qa, reconciliation at archive | 2 |
| S-5 | Document-schema check: read-only, bounded sampler comparing development documents with the declared schema, output without values | 2 |
| S-6 | Bootstrap of the component map and draft sheets from code (`karvey-docs components --bootstrap`), human-reviewed | 2 |
| S-7 | README setting, minimal section set, the trigger check, bootstrap and update through `karvey-docs` | 3 |
| S-8 | Integration: upgrade steps per part; lanes and gates of Wave 2; closed load lists and size budget of Wave 3; check-mode registry defaults; dogfooding on this repository | all |

## 7. Out of scope
- **Capturing anything other than the human's own prompt text** — tool output, transcripts of other people,
  attachments, or messages from other agents (an agent's message is never the owner's instruction).
- **Automatic classification without the agent**: the detector only decides whether to capture; classifying a row
  is the agent's work, visible to the human at the gate.
- **Writing to any data store**, reading a production data store, or sampling relational tables (a relational
  store's sheet is built from its migrations and schema files, which are in the repository).
- **Generating API reference documentation from code annotations** (Diataxis reference pages stay with
  `karvey-docs generate`); the sheet links to them.
- **Enforcing a documentation style or language** beyond the required sections.
- **Retroactively capturing instructions from past sessions**; changes already in flight get capture from the
  moment the project enables it.
- **Editing the owner's personal global instructions** or anything under the user's home (D-01, D-11).

## 8. Stakeholders
- **Requests and approves:** the method's owner (approves the three gates of this change and production —
  `role: human`); D-38 records the request verbatim, D-21 the standing instruction to proceed with recommended
  defaults, listed as open points.
- **Impacted:** every project using Karvey (owners, agents, reviewers, operators, newcomers).
- **Sources:** D-38; the approval hook and vocabulary (D-01, REQ-W1-017/019); living specs and archive merge;
  the project-upgrade catalogue (D-20, REQ-UP-008); Wave 2 lanes and gates; Wave 3 load lists and size tool.

## 9. Constraints
- **Security Tier: 3** — the hook writes the owner's verbatim text into tracked files of a repository that may be
  public; the sampler reads a real data store with credentials held outside the repository; the bootstrap reads
  code and configuration into generated documents; the classification check gates approvals. Controls required:
  capture only the human's prompt, redact secret-shaped values before any write, an off-the-record marker, rows
  written only by the hook and verified against a store the agent cannot write (same trust model as the approval
  marker, D-01); the sampler performs read operations only, refuses a target declared as production, bounds the
  sample, never prints or stores a value; credentials only by reference (environment variable or vault name),
  never literal; bootstrap output passes the method's leak check.
- **Backward compatible** (minor release 4.2.0): every new check starts advisory or warn except the ones the
  owner's decision makes a gate (instruction classification) and the integrity checks; `validate` accepts every
  4.1.0 shape; a project without a component map or with capture disabled behaves as in 4.1.0.
- **Public, organisation-neutral text:** no rule, skill, template or example names a company, product, client,
  cloud vendor as a requirement, person, internal URL or personal path; vendors appear only as one example among
  several; examples are fictional.
- **Sequencing:** requirements through tasks now; implementation after `wave3-optimization`'s implementation
  (both edit skills, hooks and the linter).
- **Dogfooding:** built through the method on this repository in the `standard` lane (no UI), trunk flow,
  Markdown tracker; every commit carries `Karvey-Change: living-docs`.
- **Decisions this change depends on:** D-38; D-01 (approval only from the human's message), D-20
  (project-upgrade), D-21, D-24 (strictness per release), D-30 (cost measured, never capped).

## 10. Acceptance criteria
- **AC-1** With capture enabled and an active change, a prompt such as "the export must also include the closing
  date" appears as an `instruction` row in that change's `findings.md`, verbatim, written by the hook, and the owner
  sees `captured as instruction F-NN`; a prompt opening with the force-capture marker is always captured; a question
  ("why does the export fail?") and an approval ("ok") produce no row; a prompt with the off-the-record marker
  produces no row and no stored text.
- **AC-2** An agent edit of an instruction row's text, or a row the hook did not write, is reported by the state
  tool as tampered and blocks the gate.
- **AC-3** `advance`, `approve` and `approve-gate` refuse while an `instruction` row of the change is unclassified or
  an entry waits in the project inbox, naming them; a `no-spec-impact` or `not-instruction` classification without a reason is refused; the gate summary
  lists every row with its classification.
- **AC-4** A prompt carrying a secret-shaped value is captured with the value replaced by a redaction marker.
- **AC-5** A project with a component map of four kinds validates; each sheet created from its template has every
  mandatory section; a sheet missing a mandatory section without `n/a` + reason is reported.
- **AC-6** A commit that changes a mapped code path without the component's sheet is reported by the sheet check
  (warn by default; refused under the project's blocking opt-in); archive reports a declared delta item missing
  from the sheet and a sheet change the architecture did not declare.
- **AC-7** The schema check over a fixture document store reports a missing required field, an unexpected field
  and a type mismatch with counts and field paths, prints no value, performs only reads and refuses a target
  declared as production.
- **AC-8** The bootstrap over a fixture repository proposes a component map and draft sheets marked `draft`, with
  environment variable names and no values, and the leak check green.
- **AC-9** A change that adds an environment variable read without touching the README is reported; a README
  without one of the required sections is reported with the missing section.
- **AC-10** The upgrade plan lists one step per part with its seven fields; dry-run writes nothing.
- **AC-11** The size tool shows each phase's closure growth; no phase grows more than 10%; the plugin linter and
  guard tables are green; a project that passes under 4.1.0 passes under 4.2.0 while the new checks keep their
  defaults.
