# Requirements: living-docs

## Project description

Documentation that stays true while the work moves (D-38, release 4.2.0). Three parts: (1) the owner's
instructions during an active change are captured verbatim by the prompt hook — never by the agent — into the
change's findings as `instruction` rows, and each must be classified before the change moves past a phase or a
gate; (2) every component of a project — data store (relational and document), backend service, frontend module,
infrastructure resource — has a living technical sheet mapped to its code paths, declared as a delta by
architecture, updated in the same commit as the code, reconciled at archive, with a read-only check of
document-store schemas against development documents and a bootstrap for existing repositories; (3) each
repository's README keeps a minimal section set, checked when setup files, commands, settings or components
change. Existing projects receive all three through the project-upgrade plan. North star (PRD §2): *no
instruction the owner gives during an active change is lost — each is captured verbatim by the hook and
classified before its gate closes — and every component and repository of a project has a technical sheet and a
README that change in the same change as the code they describe.*

## Conventions

- **IDs.** `REQ-LD-NNN`, numbered contiguously. The heading also carries the numeric EARS id (`1.1`, `1.2`…).
- **Trace line.** Each requirement cites the PRD (`PRD §n`, scope `S-n`, objective `O-n`, acceptance `AC-n`) and
  its decisions (`D-NN`) and the living requirements it builds on (`REQ-W1-*`, `REQ-W2-*`, `REQ-W3-*`, `REQ-UP-*`).
- **Living spec baseline.** The REQ-W1-*, REQ-W2-*, REQ-W3-* blocks of the three waves and the REQ-UP-* blocks of
  `project-upgrade` are treated as already part of the living spec. A requirement that changes one of them says
  **MODIFIES REQ-…**; `spec-delta.md` lists it under MODIFIED.
- **Modes.** As in Waves 2 and 3: **advisory** (reported only), **warn** (reported on the gate summary and in the
  dashboard, never refuses) or **blocking** (refuses). "In 4.2" means the default of release 4.2.0 in the
  check-mode registry (REQ-LD-053). A project can always choose a stricter mode.
- **Actors.** "the human" = the person who owns the change's approvals (`role: human`) — the owner whose
  instructions are captured; "the agent" = any model session working on the change; "the hook" = the method's
  prompt hook, which runs outside the model (the same trust model as the approval marker, D-01); "the state tool"
  = the only writer of `spec.json` state; "a phase skill" = any skill that owns a phase.
- **Technology.** SHALL text names roles of the method. Public names the user types or reads are in the glossary;
  languages, parsers and adapters are architecture decisions. Data-store examples name families (relational,
  document, key-value), never a vendor as a requirement.
- **Neutrality.** No requirement, rule, template or example names an organisation, product, client, person,
  internal URL or personal path; examples are fictional.

### Glossary — roles and their public names

| Role in the requirements | Public name (final at architecture) | Source |
|---|---|---|
| the **capture setting** | `project.json:instructions.capture` (`on` \| `off`) | D-38 |
| the **instruction row** | a row of `findings.md` with type `instruction`, origin `hook:prompt` | D-38 |
| the **capture store** | `<state dir>/instructions/<scope>.jsonl`, next to the approval markers | D-01, REQ-W1-017 |
| the **directive and question vocabulary** | `directive` and `question` lists in the approval vocabulary file | REQ-W1-019 |
| the **off-the-record marker** | a prompt starting with `#off` (overridable) | D-38 |
| the **force-capture marker** | a prompt starting with `#note` (overridable) | D-38 |
| the **confirm phrases** | `remove instruction F-NN`, `reviewed sheet <component-id>` (and their translations) | D-38, D-16 |
| the **project inbox** | the `_project` scope of the capture store | D-38 |
| the **classification command** | `karvey-state.py instruction classify <change> <F-NN> --as …` | D-38 |
| the **component map** | `project.json:components[]` | D-38 |
| a **component sheet** | `docs/spec/components/<component-id>.md` | D-38 |
| the **sheet templates** | `templates/components/{data-store,backend-service,frontend-module,infra-resource}.md` | D-38 |
| the **component delta** | the `## Component delta` section of `architecture.md` | D-38 |
| the **sheet check** | `karvey-docs components --check` (also run by impl, qa and CI) | D-38 |
| the **sheet-skip trailer** | `Karvey-Sheet-Skip: <component-id> — <reason>` | D-38 |
| the **schema sampler** | `karvey-docs components --check-schema <component-id>` | D-38 |
| the **bootstrap** | `karvey-docs components --bootstrap`, `karvey-docs readme --bootstrap` | D-38 |
| the **README setting** | `project.json:readme.check` (`on` \| `off`) | D-38 |
| the **README check** | `karvey-docs readme --check` | D-38 |
| the **upgrade steps** | `LD-1`, `LD-2`, `LD-3` in the project-upgrade step catalogue | D-20, REQ-UP-008 |

---

## Requirement 1: Instruction capture (D-38 part 1)

### 1.1 REQ-LD-001 — The hook captures the owner's instructions
WHEN the human submits a prompt WHILE the capture setting is `on` and exactly one change is active, the hook
SHALL decide with the detection rules (REQ-LD-002) whether the prompt is an instruction and, if it is, SHALL
record it verbatim (after REQ-LD-006 and REQ-LD-007) in the capture store and append it as an `instruction` row to
that change's `findings.md`, with status `unclassified`, the change's current phase and the capture time.

Traces to PRD: §6 S-1, O-1, AC-1 · Decision: D-38

**Scenario — success:** GIVEN capture on and one active change in `impl` WHEN the human writes "the export must
also include the closing date" THEN `findings.md` gains one `instruction` row with that text, origin
`hook:prompt`, phase `impl`, status `unclassified`, and the capture store holds the same entry.
**Scenario — error:** GIVEN capture on and one active change WHEN the agent appends an `instruction` row itself
THEN the next state-tool call reports that row as not written by the hook (REQ-LD-008) and it counts as tampered.

### 1.2 REQ-LD-002 — Detection rules keep questions and chit-chat out
The hook SHALL capture a prompt only when, after the normalisation of the approval vocabulary, it contains a
directive term or a requirement modal from the directive vocabulary, or it has more than 40 words and is not a
question; it SHALL NOT capture a prompt that is only an approval or negation term (REQ-W1-019), a prompt that is a
question (it ends with a question mark or opens with a question term) and contains no directive term, a prompt of
fewer than 4 words without a directive term, or a prompt that is only a method command with its arguments.

Traces to PRD: §6 S-1, O-2, AC-1 · Decision: D-38 · Builds on: REQ-W1-019

**Scenario — success:** GIVEN capture on WHEN the human writes "why does the export fail?" or "ok" or "thanks!" or
"/karvey-qa living-docs" THEN no row is written; WHEN the human writes "why does it fail? it must retry twice"
THEN one row is written (a directive term wins over the question form).
**Scenario — error:** GIVEN capture on WHEN the human writes "export monthly from now on" (no directive term, fewer
than 40 words) THEN no row is written and no capture acknowledgement (REQ-LD-058) is shown, so the human sees that it
was not captured; the hook never asks the model to decide.

### 1.3 REQ-LD-003 — Multilingual vocabulary, one place, reviewed line
The directive and question vocabulary SHALL live in the same file as the approval vocabulary, SHALL be matched
with the same normalisation (compatibility decomposition, accent stripping, case folding, word boundaries), SHALL
ship terms for at least English, Spanish, Portuguese, German and French, and a project SHALL be able to override
either list only from the reviewed line of its settings (`origin/{production}`); an uncommitted override SHALL be
ignored and recorded in the audit log as `vocabulary override ignored (not reviewed)`.

Traces to PRD: §6 S-1, O-2 · Decision: D-38, D-01 · Builds on: REQ-W1-019

**Scenario — success:** GIVEN the shipped vocabulary WHEN the human writes "el reporte debe incluir la fecha de
cierre" or "o relatório deve incluir a data" THEN each is captured.
**Scenario — error:** GIVEN an override of the directive list edited in the working copy only WHEN the hook runs
THEN it uses the shipped or reviewed list and records `vocabulary override ignored (not reviewed)` in the audit log.

### 1.4 REQ-LD-004 — The detector is measured, not assumed
The method SHALL keep a labelled table of prompts — at least 30 per language for each language the vocabulary ships (REQ-LD-003),
including questions, approvals, chit-chat, mixed prompts and instructions — and its tests SHALL compute the
detector's recall and precision on instructions; the tests SHALL fail when recall is below 0.90 or precision is
below 0.80.

Traces to PRD: §4 O-2 · Decision: D-38

**Scenario — success:** GIVEN the table WHEN the tests run THEN they print recall and precision per language and
overall, both above their thresholds.
**Scenario — error:** GIVEN a vocabulary change that drops a common directive term WHEN the tests run THEN recall
falls below 0.90 and the test fails naming the missed prompts.

### 1.5 REQ-LD-005 — Off the record
IF a prompt starts with the off-the-record marker, THEN the hook SHALL NOT capture it, SHALL NOT store its text or
a hash of it, and SHALL record only that one prompt was skipped (a count with the time) in the audit log.

Traces to PRD: §5, §6 S-1, O-3, AC-1 · Decision: D-38

**Scenario — success:** GIVEN capture on WHEN the human writes "#off between us, the client may cancel" THEN no row,
no store entry and no hash exist; the audit log holds one `skipped: off-the-record` line.
**Scenario — error:** GIVEN the marker in the middle of a prompt ("please #off …") WHEN the hook runs THEN the
marker is not honoured (it must open the prompt) and the detection rules apply to the whole text.

### 1.6 REQ-LD-006 — Only the human's own text
The hook SHALL capture only the prompt text the human submitted in the prompt event; it SHALL NOT capture tool
output, file contents or attachments the runtime adds, or text from another agent; a pasted block inside the
prompt — a fenced block or a line longer than 200 characters (the vocabulary's pasted-line length, overridable like the
lists) — SHALL be replaced by a marker
with its line count, and a prompt longer than 4,000 characters after that SHALL be truncated with a marker.

Traces to PRD: §6 S-1, §7, O-3 · Decision: D-38, D-01

**Scenario — success:** GIVEN a prompt with one sentence and a 60-line pasted log WHEN it is captured THEN the row
holds the sentence and `[pasted block: 60 lines omitted]`.
**Scenario — error:** GIVEN a message delivered by another agent (not a human prompt event) WHEN it reaches the
session THEN nothing is captured, because the hook reads only the human prompt event.

### 1.7 REQ-LD-007 — Redaction before any write
Before writing a capture anywhere, the hook SHALL replace every value that matches the method's secret patterns,
every e-mail address and every phone number in international form (a `+` followed by 8 to 15 digits, spaces,
dots or hyphens allowed between them) with a typed redaction marker (`[redacted:secret]`,
`[redacted:email]`, `[redacted:phone]`), and SHALL record the number of redactions; IF the redaction step cannot
run, THEN the hook SHALL capture nothing and record why.

Traces to PRD: §6 S-1, §9, O-3, AC-4 · Decision: D-38 · Builds on: REQ-W3-023 (secret patterns)

**Scenario — success:** GIVEN a prompt "use key token=abc123XYZ and tell ana@example.org" WHEN it is captured THEN
the row reads "use key [redacted:secret] and tell [redacted:email]"; GIVEN "retry 3 times within 30000 ms" THEN
nothing is redacted (numbers without the international form are kept verbatim).
**Scenario — error:** GIVEN a corrupt pattern file WHEN a prompt arrives THEN no row and no store entry are written,
the audit log records `capture skipped: redaction unavailable`, and the prompt passes.

### 1.8 REQ-LD-008 — Tamper evidence: the agent never writes these rows
The hook SHALL store each capture — id, change, time, redacted text and its SHA-256 — in the capture store under
the method's state directory, which is never tracked by git and which the protect-paths guard keeps the agent from
writing (as for approval markers), and SHALL write the same hash in the row. (Verification is REQ-LD-059.)

Traces to PRD: §6 S-1, §9, O-1, AC-2 · Decision: D-38, D-01 · Builds on: REQ-W1-017

**Scenario — success:** GIVEN one captured instruction WHEN the store is listed THEN it holds id, change, time,
redacted text and a hash equal to the hash in the row.
**Scenario — error:** GIVEN the agent tries to write into the capture store with a file tool or a shell command WHEN
the protect-paths guard runs THEN it blocks the write, as for an approval marker.

### 1.9 REQ-LD-009 — No change, or several: the project inbox
IF capture is on and no change or more than one change is active when an instruction is detected, THEN the hook
SHALL store it in the project scope of the capture store only (no tracked file), the session hook and the
dashboard SHALL list the pending inbox entries, and the state tool SHALL let the agent assign an entry to a change
— the row is then written from the stored text — or classify it `not-instruction` with a reason.

Traces to PRD: §6 S-1, O-1 · Decision: D-38 · Builds on: REQ-W1-045 (session context)

**Scenario — success:** GIVEN two active changes WHEN the human gives an instruction THEN it waits in the inbox; the
next session start shows `1 instruction waiting for a change`; `instruction assign <id> <change>` writes the row.
**Scenario — error:** GIVEN an inbox entry WHEN the agent tries to assign it with edited text THEN the state tool
refuses: the row is always written from the store, never from an argument.

### 1.10 REQ-LD-010 — Capture never blocks the human
The hook SHALL never block a prompt because of capture and SHALL give up capturing after 1 second, treating that
as a failure; on any failure it SHALL let the prompt pass, record the reason in the audit log when it can, show the
human at once a one-line notice that the prompt was not captured, and add the same line to the session context; the
next session start SHALL report `instruction capture unavailable` while the cause persists, and the next gate
summary SHALL list the recorded failures of the change.

Traces to PRD: §6 S-1, O-1 · Decision: D-38 · Builds on: REQ-W1-017

**Scenario — success:** GIVEN the store's directory is not writable WHEN the human writes an instruction THEN the
prompt reaches the model, and both the human and the model see `instruction not captured (store not writable)`.
**Scenario — error:** GIVEN no interpreter for the hook's helper WHEN a prompt arrives THEN the prompt passes, the
human sees `instruction capture unavailable`, and the next session start reports the same.

### 1.11 REQ-LD-011 — The capture setting is the owner's
The capture setting SHALL be read from the reviewed line of the project settings, except that a working-copy
value of `on` SHALL take effect at once when the reviewed line is absent or says otherwise (the working copy can
only turn capture on, never off — so a new project or an upgrade branch captures before its first merge); a
working-copy `off` against a reviewed `on` SHALL be ignored and recorded in the audit log; `karvey-init` SHALL ask
the setting for a new project with `on` as the recommended answer; WHERE the effective value is `off` or absent, no
prompt SHALL be captured and no classification check SHALL apply.

Traces to PRD: §6 S-1, §9, O-1 · Decision: D-38

**Scenario — success:** GIVEN `instructions.capture: on` on the reviewed line WHEN a session starts THEN the session
hook states `instruction capture on`; GIVEN a new project whose production branch has no settings yet and a
working copy with `on` THEN capture is on from the first prompt.
**Scenario — error:** GIVEN the working copy sets `off` while the reviewed line says `on` WHEN a prompt arrives THEN
capture stays on and the audit log records the ignored local value.

### 1.12 REQ-LD-012 — Removal at the owner's request
WHEN the human asks to remove a captured row with the removal phrase of REQ-LD-063, the state tool SHALL — only
with the marker the hook wrote for that phrase — replace the row's text and the store entry's text with
`[removed at the owner's request]`, keep the id, time and classification, and record the removal in the audit log;
the tamper check SHALL accept a removed row.

Traces to PRD: §6 S-1, §9, O-3 · Decision: D-38, D-01

**Scenario — success:** GIVEN row F-14 and the human's message "remove instruction F-14" WHEN the agent runs the
removal THEN the row reads `[removed at the owner's request]` and `validate` reports it as removed, not tampered.
**Scenario — error:** GIVEN no removal marker for F-14 WHEN the agent runs the removal THEN the state tool refuses
`removal needs the owner's own message (D-01)`.

### 1.13 REQ-LD-058 — The human sees each capture, and can force one
WHEN the hook captures a prompt, it SHALL show the human, in the session, a one-line acknowledgement with the row id
(`captured as instruction F-NN`); IF a prompt starts with the force-capture marker (`#note` by default), THEN the hook
SHALL capture it whatever the detection rules decide (REQ-LD-005 to REQ-LD-007 still apply), so that a missed
instruction can be recorded by the human without the agent.

Traces to PRD: §6 S-1, O-1, O-2, AC-1 · Decision: D-38 (judge F-04)

**Scenario — success:** GIVEN capture on WHEN the human writes "#note export monthly from now on" THEN a row is
written and the human sees `captured as instruction F-15`.
**Scenario — error:** GIVEN capture off WHEN the human writes "#note …" THEN nothing is captured and the human sees
`instruction capture is off for this project`.

### 1.14 REQ-LD-059 — Tampered rows are found and refused
The state tool SHALL verify, on every `validate`, `advance`, `approve` and `approve-gate` of a change, that each
`instruction` row matches a capture-store entry by id and hash and that each store entry of the change has its row,
and SHALL refuse `advance`, `approve` and `approve-gate` while a row is missing, extra or altered (tampered),
naming it; a row whose store entry is in another clone SHALL be reported `not verifiable here` and SHALL NOT be
refused when the hash in the row matches its text, and SHALL be refused as tampered when it does not.

Traces to PRD: §6 S-1, §9, O-1, AC-2 · Decision: D-38, D-01 (judges F-06, F-17, F-24)

**Scenario — success:** GIVEN three rows captured in this clone and one captured in another clone with a matching
hash WHEN `validate` runs THEN it reports `instructions: 3 verified, 1 not verifiable here` and approvals proceed.
**Scenario — error:** GIVEN a row whose text the agent shortened WHEN `approve` runs THEN it refuses with
`instruction F-12 tampered (text does not match the capture)`.

### 1.15 REQ-LD-060 — Inbox entries hold every gate of the project
WHILE the project inbox (REQ-LD-009) holds an entry captured before the call, the state tool SHALL refuse
`advance`, `approve` and `approve-gate` of every change of the project, naming the entry, until it is assigned to a
change or classified `not-instruction` with a reason; an inbox entry dismissed that way SHALL be listed in the next
gate summary of any change of the project.

Traces to PRD: §6 S-1, S-2, O-1, O-2 · Decision: D-38 (judges F-01, F-02, F-15)

**Scenario — success:** GIVEN one inbox entry assigned to `add-refunds` WHEN `approve add-export requirements` runs
THEN it is recorded.
**Scenario — error:** GIVEN one unassigned inbox entry WHEN `approve add-export requirements` runs THEN it refuses
`1 instruction waiting in the project inbox: I-3 — assign it or classify it`.

### 1.16 REQ-LD-063 — The owner's confirm phrases
The hook SHALL recognise two confirm phrases in the human's own prompt — a removal (`remove instruction F-NN`) and a
sheet review (`reviewed sheet <component-id>`), with verbs and nouns taken from the vocabulary in the shipped
languages — and SHALL write, for each, a one-use marker naming the row or the component, like the approval marker
(D-01); a prompt that is a confirm phrase SHALL NOT be captured as an instruction.

Traces to PRD: §6 S-1, S-6, §9 · Decision: D-38, D-01, D-16 (confirm-phrase pattern) (judge F-09)

**Scenario — success:** GIVEN the human writes "remove instruction F-14" WHEN the hook runs THEN a removal marker for
F-14 exists and no new row is written.
**Scenario — error:** GIVEN the human writes "remove F-14, it said the client may cancel" (no noun `instruction`)
WHEN the hook runs THEN no removal marker is written, and the detection rules apply to the prompt.

## Requirement 2: Instruction classification (D-38 part 1)

### 2.1 REQ-LD-013 — Four classifications, each with its evidence
The state tool SHALL record for an `instruction` row exactly one classification: `requirement-revision` with the
requirement ids it added or changed, `finding` with the finding id it became (then routed by `/karvey-iterate`),
`no-spec-impact` with a reason, or `not-instruction` with a reason; IF the evidence is missing or does not
resolve (a requirement id not in the change's `requirements.md`, a finding id not in `findings.md`, a reason
shorter than 10 characters), THEN it SHALL refuse and name what is missing.

Traces to PRD: §6 S-2, O-1, O-2, AC-3 · Decision: D-38 · Builds on: the iteration-loop rule (finding router, `/karvey-iterate`)

**Scenario — success:** GIVEN row F-12 WHEN the agent runs `instruction classify living-docs F-12 --as
requirement-revision --ref REQ-LD-021` THEN the row shows `requirement-revision → REQ-LD-021`.
**Scenario — error:** GIVEN row F-12 WHEN the agent runs `--as no-spec-impact` without a reason THEN the state tool
refuses `no-spec-impact needs --reason`.

### 2.2 REQ-LD-014 — A requirement revision is a real revision
IF a row is classified `requirement-revision` after the requirements phase was first approved, THEN the state tool
SHALL also require a `revision_history` entry in `spec.json` that cites the row's finding id (the spec-revision
sub-cycle of the iteration loop); before that first approval, the requirement ids alone SHALL suffice.

Traces to PRD: §6 S-2, O-1 · Decision: D-38 · Builds on: living specs (revision_history, ripple set)

**Scenario — success:** GIVEN requirements approved and REQ-LD-021 edited WHEN the agent classifies F-12 with the
revision entry citing F-12 THEN the classification is recorded.
**Scenario — error:** GIVEN requirements approved WHEN the agent classifies F-12 as `requirement-revision` with no
revision entry citing it THEN the state tool refuses `requirement-revision after approval needs revision_history
citing F-12`.

### 2.3 REQ-LD-015 — Classification only through the state tool; history kept
The classification of an `instruction` row SHALL change only through the state tool, which SHALL keep every
classification with its time in an append-only history of the row; the row's text SHALL never change except by
REQ-LD-012.

Traces to PRD: §6 S-2, O-1, AC-2 · Decision: D-38

**Scenario — success:** GIVEN F-12 classified `no-spec-impact` WHEN the human asks to reconsider and the agent
reclassifies it as `finding` THEN both entries appear in the row's history.
**Scenario — error:** GIVEN F-12 WHEN its status cell is edited by hand THEN the state tool reports
`instruction F-12 classification not recorded by the state tool` and treats the row as unclassified.

### 2.4 REQ-LD-016 — No phase closes over an unclassified instruction
WHILE an `instruction` row of a change captured before the call is unclassified, the state tool SHALL refuse
`advance`, `approve` and `approve-gate` for that change — in every lane and at every gate, the production gate and
QA's pass included — naming each unclassified row, and SHALL refuse them as well when capture is on and the
change's `findings.md` cannot be read; this check SHALL be blocking in 4.2 wherever capture is on.

Traces to PRD: §6 S-2, O-1, AC-3 · Decision: D-38 (enforced by the state tool, not prose)

**Scenario — success:** GIVEN every row classified WHEN `approve living-docs architecture` runs THEN it is recorded.
**Scenario — error:** GIVEN F-12 unclassified WHEN `advance living-docs test` runs THEN it refuses `1 instruction
unclassified: F-12 — classify it first (karvey-state.py instruction classify)`.

### 2.5 REQ-LD-017 — The human sees every classification at the gate
WHEN a gate is presented, the gate summary SHALL list every `instruction` row captured or (re)classified since the
previous gate, and every project-inbox entry dismissed since then (REQ-LD-060), each with its text excerpt and
classification, the `not-instruction` and `no-spec-impact` ones first with their reasons.

Traces to PRD: §6 S-2, O-2, AC-3 · Decision: D-38 · Builds on: gate summary (`karvey-context --section gate`)

**Scenario — success:** GIVEN two rows since the last gate, one dismissed WHEN the gate is presented THEN the summary
shows `Instructions since the last gate: 2 — 1 not-instruction ("a thank-you"), 1 requirement-revision → REQ-LD-021`.
**Scenario — error:** GIVEN a row captured before the previous gate and reclassified `no-spec-impact` after it WHEN
the next gate is presented THEN the row is listed with its new classification and reason.

### 2.6 REQ-LD-018 — Visible between gates
The session hook and the dashboard SHALL show, per active change, the number of unclassified instruction rows and
the number of inbox entries waiting for a change.

Traces to PRD: §6 S-2, O-1 · Decision: D-38 · Builds on: REQ-W1-045

**Scenario — success:** GIVEN two unclassified rows WHEN a session starts THEN its context line includes
`2 instructions unclassified`.
**Scenario — error:** GIVEN the capture store is unreadable WHEN the dashboard runs THEN it shows
`instructions: store unreadable` instead of a count.

## Requirement 3: Component map and sheets (D-38 part 2)

### 3.1 REQ-LD-019 — The component map
The project settings SHALL be able to declare components, each with a unique id, a kind (`data-store`,
`backend-service`, `frontend-module`, `infra-resource`), the repository that holds it (WHERE the project has
several), one or more code-path patterns relative to that repository, and its sheet path, by default
`docs/spec/components/<id>.md`; `validate` SHALL refuse an unknown kind, a duplicate id, a sheet outside
`docs/spec/components/` and a code-path pattern that is absolute or leaves the repository.

Traces to PRD: §6 S-3, O-4, AC-5 · Decision: D-38

**Scenario — success:** GIVEN four components of the four kinds WHEN `validate` runs THEN it passes and lists them.
**Scenario — error:** GIVEN a component with kind `database` WHEN `validate` runs THEN it refuses `components[2].kind:
database is not one of data-store, backend-service, frontend-module, infra-resource`.

### 3.2 REQ-LD-020 — Data-store sheet
The data-store template SHALL require these sections: purpose; engine family (relational, document, key-value,
other); containers — tables, collections or containers — each with its keys (primary, partition and sort keys as
the family has them); per document container, the document shape as a JSON Schema and one fictional example that
validates against it; per relational table, its columns and constraints; indexes; expiry (time-to-live) rules;
writers and readers (component ids or `external`); invariants; migrations (where they live and how they run).

Traces to PRD: §6 S-3, O-4, O-6 · Decision: D-38

**Scenario — success:** GIVEN a document-store sheet with one container, its partition key, schema, example,
indexes, expiry, writers, readers, invariants and migrations WHEN the section check runs THEN it passes.
**Scenario — error:** GIVEN a document container without a schema WHEN the section check runs THEN it reports
`orders-store: container events: document schema missing`.

### 3.3 REQ-LD-021 — Backend-service sheet
The backend-service template SHALL require: purpose; endpoints or operations with their contract (operation, input,
output, errors) or a link to a contract file in the repository; settings — every environment variable or setting
name with meaning, whether required, and default (a default only for a setting that is not a secret) — never a
current or environment value, and the section check SHALL report a settings table with a value column; dependencies (component ids or external
services by role); error behaviour; idempotency and retries; observability pointer.

Traces to PRD: §6 S-3, O-4 · Decision: D-38

**Scenario — success:** GIVEN a service sheet whose endpoints link to a contract file WHEN the section check runs THEN
it passes.
**Scenario — error:** GIVEN a settings table with a value column filled WHEN the leak check runs THEN REQ-LD-024
applies to any secret-shaped value and the section check reports `settings: values are not allowed, names only`.

### 3.4 REQ-LD-022 — Frontend-module and infra-resource sheets
The frontend-module template SHALL require: purpose; routes; state (what it keeps and where); APIs consumed
(component ids); permissions per route or action; settings names. The infra-resource template SHALL require:
purpose; infrastructure-as-code reference (file path in the repository, or `manual` with a reason); sizing;
network (exposure, inbound and outbound); secret references by name; runbook (start, stop, scale, restore, rotate a
secret); dependencies.

Traces to PRD: §6 S-3, O-4 · Decision: D-38

**Scenario — success:** GIVEN an infra sheet with a runbook of the five operations WHEN the section check runs THEN it
passes.
**Scenario — error:** GIVEN an infra sheet without a runbook WHEN the section check runs THEN it reports
`queue-infra: runbook missing`.

### 3.5 REQ-LD-023 — Sections complete or explicitly not applicable
The section check SHALL report every mandatory section of a sheet's kind that is absent or empty; a section whose
content is `n/a — {reason}` SHALL count as complete; the sheet SHALL carry front matter with its component id,
kind, status (`draft` or `reviewed`) and last change; the check SHALL be warn in 4.2.

Traces to PRD: §6 S-3, O-4, AC-5 · Decision: D-38

**Scenario — success:** GIVEN a key-value store sheet with `Indexes: n/a — the family has none` WHEN the check runs
THEN the section counts as complete.
**Scenario — error:** GIVEN a sheet whose front matter id differs from the map WHEN the check runs THEN it reports
`sheet docs/spec/components/a.md declares id b; the map says a`.

### 3.6 REQ-LD-024 — Sheets hold no secrets
The method's leak check (secret patterns) SHALL run over every sheet at the section check and in the plugin's
project CI check; a sheet with a secret-shaped value SHALL be refused (blocking in 4.2), naming the sheet, line and
rule, never the value; setting and secret names SHALL be allowed.

Traces to PRD: §6 S-3, §9 · Decision: D-38 · Builds on: REQ-W3-023

**Scenario — success:** GIVEN a sheet listing `ORDERS_STORE_KEY` as a secret reference WHEN the check runs THEN it
passes.
**Scenario — error:** GIVEN a sheet containing `api_key=4f9c…` WHEN the check runs THEN it fails
`orders-store.md:41 secret pattern` without printing the value.

### 3.7 REQ-LD-025 — References between sheets resolve
The section check SHALL report every writer, reader, dependency or consumed API that names neither a component id
of the map nor `external: {role}`.

Traces to PRD: §6 S-3, O-4 · Decision: D-38

**Scenario — success:** GIVEN a store whose writers are `orders-api` and `external: payment provider` WHEN the check
runs THEN both resolve.
**Scenario — error:** GIVEN a reader `order-api` (a typo) WHEN the check runs THEN it reports `unknown component
order-api (did you mean orders-api?)`.

## Requirement 4: Sheet lifecycle (D-38 part 2)

### 4.1 REQ-LD-026 — Architecture declares the component delta
WHERE a change's lane runs architecture, `architecture.md` SHALL contain a component-delta section that lists each
component the change adds, modifies or removes with the sheet sections it changes, or states `none` with a reason;
`generated architecture` SHALL report a missing section (warn in 4.2).

Traces to PRD: §6 S-4, O-5, AC-6 · Decision: D-38

**Scenario — success:** GIVEN a delta `MODIFIED orders-store: containers.events (new field closedAt), invariants`
WHEN architecture is generated THEN the section is accepted and tasks can cite it.
**Scenario — error:** GIVEN an architecture without the section WHEN `generated architecture` runs THEN it warns
`component delta missing — declare it or write none with a reason`.

### 4.2 REQ-LD-027 — Tasks pair code and sheet
WHEN tasks are generated for a change with a component delta, each task that changes a component's code SHALL name
that component's sheet sections in its own acceptance, and every item of the component delta SHALL be named by at
least one task; the tasks review gate SHALL report each delta item no task names.

Traces to PRD: §6 S-4, O-5 · Decision: D-38

**Scenario — success:** GIVEN a delta on `orders-store` WHEN tasks are generated THEN the task that adds `closedAt`
lists `sheet orders-store: containers.events schema + example` in its acceptance.
**Scenario — error:** GIVEN a delta item that no task names WHEN the tasks review gate runs THEN it reports
`delta item orders-store/invariants has no task`.

### 4.3 REQ-LD-028 — Same commit: the sheet check
The sheet check SHALL report every commit in the change's range that modifies a file matching a component's code
paths without modifying that component's sheet in the same commit, unless the commit carries a sheet-skip trailer
for that component with a reason; WHERE the component's repository is not the one that holds its sheet, the pairing
SHALL be by change instead of by commit — the change's range in the component's repository and in the sheet's
repository, matched by the change trailer, must both touch it; it SHALL run at each impl task close, at QA (and QA-lite) over the change's
range, and on demand; it SHALL be warn in 4.2 and blocking WHERE the project opts in.

Traces to PRD: §6 S-4, O-5, AC-6 · Decision: D-38

**Scenario — success:** GIVEN a commit touching `services/orders/**` and `docs/spec/components/orders-api.md` WHEN the
check runs THEN it passes; GIVEN a refactor commit with `Karvey-Sheet-Skip: orders-api — rename only` THEN it passes
and lists the skip.
**Scenario — error:** GIVEN the project opted in to blocking and a commit touching `services/orders/**` alone WHEN QA
runs the check THEN QA fails `commit 1a2b3c4 changes orders-api without its sheet`.

### 4.4 REQ-LD-029 — Archive reconciles the delta with the sheets
WHEN a change is archived, the method SHALL compare the declared component delta with the sheets changed in the
change's range and SHALL report each declared item whose sheet did not change and each sheet change the delta did not
declare; the report SHALL be warn in 4.2. (What archive writes is REQ-LD-062.)

Traces to PRD: §6 S-4, O-5, AC-6 · Decision: D-38 · Builds on: living-spec archive merge

**Scenario — success:** GIVEN a delta on `orders-store` and its sheet changed WHEN archive runs THEN the reconciliation
reports `orders-store: applied`.
**Scenario — error:** GIVEN the delta declares `orders-api` but its sheet never changed WHEN archive runs THEN it
reports `declared but not applied: orders-api` in the archive summary.

### 4.5 REQ-LD-030 — Changes in parallel on the same component
WHEN architecture declares a delta on a component that another active change of the project also declares, the
method SHALL report the other change and the component at the architecture gate and in the archive reconciliation.

Traces to PRD: §6 S-4, O-5 · Decision: D-38

**Scenario — success:** GIVEN two changes declaring `orders-store` WHEN the second architecture gate is presented THEN
it shows `also modified by change add-refunds (architecture)`.
**Scenario — error:** GIVEN the other change's `architecture.md` cannot be read WHEN the gate is presented THEN it
shows `parallel deltas: not checked (add-refunds unreadable)`.

### 4.6 REQ-LD-031 — Judges read the sheets
The closed inputs of the architecture judges SHALL include the sheets named in the component delta, and the closed
inputs of the QA judges SHALL include the sheets of the components whose code paths the diff touches.

Traces to PRD: §6 S-4, O-5 · Decision: D-38 · MODIFIES REQ-W2-023 (closed inputs)

**Scenario — success:** GIVEN a delta on `orders-store` WHEN `karvey-judges.py inputs <change> architecture` runs
THEN `docs/spec/components/orders-store.md` is in the list.
**Scenario — error:** GIVEN a delta naming a component without a sheet WHEN inputs are built THEN the line
`missing sheet: orders-store` is printed and the judges run without it.

### 4.7 REQ-LD-032 — Lanes without architecture
WHERE a change's lane skips architecture (`patch`, `hotfix`, `ops`, `docs`), no component delta SHALL be required;
the sheet check (REQ-LD-028) and the section check SHALL still apply to its commits and be reported by QA-lite.

Traces to PRD: §6 S-8 · Decision: D-38 · Builds on: REQ-W2-011 (lanes), REQ-W2-017 (QA-lite)

**Scenario — success:** GIVEN a patch that changes a service and its sheet in one commit WHEN QA-lite runs THEN the
check passes without a delta.
**Scenario — error:** GIVEN a hotfix commit that changes a service without its sheet WHEN QA-lite runs THEN it
reports the commit (warn), and the release gate summary lists it.

### 4.8 REQ-LD-062 — Archive stamps the sheets and retires removed components
WHEN a change is archived, the method SHALL set the last change of each sheet changed in the change's range to the
change id and date, and SHALL move the sheet of each component the delta declares REMOVED to
`docs/spec/components/archive/` and drop that component from the map.

Traces to PRD: §6 S-4, O-5 · Decision: D-38 (split from REQ-LD-029, judge F-24)

**Scenario — success:** GIVEN a change that modified `orders-store` and removed `legacy-queue` WHEN archive runs THEN
`orders-store.md` reads `last_change: add-export (2026-10-02)` and `legacy-queue.md` is under `archive/` and gone from
the map.
**Scenario — error:** GIVEN a REMOVED component whose code paths still match files in the repository WHEN archive runs
THEN it keeps the sheet and the map entry and reports `legacy-queue removed but its code paths still match 4 files`.

## Requirement 5: Document-schema check (D-38 part 2)

### 5.1 REQ-LD-033 — The declared example matches its schema
The section check SHALL validate each document container's example against its declared JSON Schema without any
data-store access, and SHALL report the schema paths that fail.

Traces to PRD: §6 S-5, O-6 · Decision: D-38

**Scenario — success:** GIVEN a schema requiring `id`, `status`, `closedAt` and an example with the three WHEN the
check runs THEN it passes.
**Scenario — error:** GIVEN an example without `closedAt` WHEN the check runs THEN it reports `events example:
/closedAt required`.

### 5.2 REQ-LD-034 — The sampler only reads
The schema sampler SHALL call only read or query operations of the data store through an adapter whose allowed
operations are declared; the plugin's tests SHALL fail if an adapter can call a write, update, delete or
administrative operation; `--dry-run` SHALL list the operations and the containers it would read.

Traces to PRD: §6 S-5, §9, O-6, AC-7 · Decision: D-38

**Scenario — success:** GIVEN a document-store adapter declaring `query` and `read` WHEN the sampler runs THEN only
those operations are called (the fixture adapter records the calls).
**Scenario — error:** GIVEN an adapter that exposes a `delete` call WHEN the plugin tests run THEN they fail naming
the adapter and the operation.

### 5.3 REQ-LD-035 — Development targets only, credentials by reference
The sampler SHALL read the connection only through a reference declared on the component — the name of an
environment variable or of a vault secret — for an environment declared as non-production; it SHALL refuse a
literal connection value in the settings, an environment declared as production, and a resolved host equal to a
host the project declares for production.

Traces to PRD: §6 S-5, §9, AC-7 · Decision: D-38

**Scenario — success:** GIVEN `sample: {environment: dev, connection_ref: env:ORDERS_STORE_DEV_URL}` WHEN the sampler
runs THEN it reads that variable at run time and never prints it.
**Scenario — error:** GIVEN `environment: prod` WHEN the sampler runs THEN it refuses `schema check reads development
data only`.

### 5.4 REQ-LD-036 — A bounded sample
The sampler SHALL read at most 100 documents per container by default and at most 1,000 when asked, SHALL stop a
container after 30 seconds, and SHALL report the sample size and whether a limit was hit.

Traces to PRD: §6 S-5, O-6 · Decision: D-38

**Scenario — success:** GIVEN a container of 50,000 documents WHEN the sampler runs THEN it reads 100 and says
`sample 100 of an unknown total (limit)`.
**Scenario — error:** GIVEN `--sample 5000` WHEN the sampler starts THEN it refuses `sample above 1000`.

### 5.5 REQ-LD-037 — The output carries no value
The sampler's output SHALL contain, per container, only the sample size and, per field path, the declared type, the
observed types with counts, the count of documents missing a required field and the count of documents with an
undeclared field path; it SHALL NOT contain any field value, document id or key value; a level with more than 20
distinct keys, and any path segment that matches a personal-data pattern (an e-mail address or a phone number),
SHALL be collapsed to `{key}`; the output SHALL then pass the leak check, and IF it does not, THEN nothing SHALL be
printed or written except the refusal naming the container and rule.

Traces to PRD: §6 S-5, §9, O-6, AC-7 · Decision: D-38

**Scenario — success:** GIVEN documents with a map keyed by customer id WHEN the sampler reports THEN the path reads
`/balances/{key}/amount: number (100)`.
**Scenario — error:** GIVEN an output line that would contain an e-mail address as a field name WHEN the leak check
runs THEN the path segment is replaced by `{key}` and the report states one path segment was masked.

### 5.6 REQ-LD-038 — Drift is reported, never repaired
WHEN the sample differs from the declared schema, the sampler SHALL report the drift as advisory with a proposal
(update the sheet or open a finding) and a distinct exit code, and SHALL NOT modify the sheet or the data; IF no
adapter exists for the component's engine family, THEN it SHALL read nothing and exit non-zero naming the family.

Traces to PRD: §6 S-5, O-6 · Decision: D-38

**Scenario — success:** GIVEN 12 of 100 documents without `closedAt` WHEN the sampler runs THEN it reports
`/closedAt required: missing in 12/100` and exits with the drift code.
**Scenario — error:** GIVEN a store with no adapter for its engine family WHEN the sampler runs THEN it exits
non-zero `no adapter for engine family graph` and reads nothing.

### 5.7 REQ-LD-061 — Relational sheets checked against the repository's schema files
WHERE a data-store sheet's engine family is relational and the component's code paths include migration or schema
files in a format the method can read, the section check SHALL compare the tables and columns the sheet declares
with those the files define and SHALL report each one declared only in the sheet or only in the files, as
advisory in 4.2; IF no readable format is found, THEN it SHALL say `relational check: no readable schema files`.

Traces to PRD: §2 (goal), §6 S-5, O-6 · Decision: D-38 (judge F-10)

**Scenario — success:** GIVEN a sheet declaring `orders(id, status, closed_at)` and a migration creating the same WHEN
the check runs THEN it reports no difference.
**Scenario — error:** GIVEN a migration that adds `orders.refund_id` and a sheet without it WHEN the check runs THEN
it reports `orders.refund_id: in the schema files, not in the sheet`.

## Requirement 6: Bootstrap for existing repositories (D-38 part 2)

### 6.1 REQ-LD-039 — The bootstrap proposes a map
WHEN `karvey-docs components --bootstrap` runs, it SHALL scan the repository — infrastructure-as-code files,
migration and schema files, container and service manifests, route definitions, environment-variable reads and
frontend route tables — and SHALL propose components with kind and code paths, showing the proposal before
writing anything.

Traces to PRD: §6 S-6, O-7, AC-8 · Decision: D-38

**Scenario — success:** GIVEN a fixture repository with a service, a migrations folder and an IaC file WHEN the
bootstrap runs THEN it proposes three components of the right kinds.
**Scenario — error:** GIVEN a repository where nothing is recognised WHEN the bootstrap runs THEN it says `no
component recognised — declare them by hand` and writes nothing.

### 6.2 REQ-LD-040 — Draft sheets, sourced and without values
The bootstrap SHALL write each sheet from its kind's template with status `draft`, a source reference (file and
line) for each filled section, `unknown — to fill` where the code does not say, setting names without values, and
document shapes inferred from code types as draft schemas; it SHALL write on a docs branch, never on integration or
production.

Traces to PRD: §6 S-6, O-7, AC-8 · Decision: D-38

**Scenario — success:** GIVEN a service reading `ORDERS_TIMEOUT_MS` WHEN the bootstrap writes its sheet THEN the
settings table lists the name with its source line and no value.
**Scenario — error:** GIVEN the current branch is the integration branch WHEN the bootstrap would write THEN it
refuses and names the docs branch to create.

### 6.3 REQ-LD-041 — Bootstrap output passes the leak check
The bootstrap SHALL run the leak check over everything it would write and SHALL write nothing if any file fails,
naming the file and rule, never the value.

Traces to PRD: §6 S-6, §9, AC-8 · Decision: D-38

**Scenario — success:** GIVEN a fixture without secrets WHEN the bootstrap runs THEN the leak check is green and the
files are written.
**Scenario — error:** GIVEN a configuration file with a literal token that would be quoted WHEN the bootstrap runs
THEN it writes nothing and reports `service-a.md: secret pattern (source config/app.yaml:7)`.

### 6.4 REQ-LD-042 — Reviewed only by a human
A sheet's status SHALL change from `draft` to `reviewed` only through the method's command with the review marker
the hook wrote for the human's confirm phrase (REQ-LD-063, D-01); the dashboard SHALL list draft sheets.

Traces to PRD: §6 S-6, O-7 · Decision: D-38, D-01

**Scenario — success:** GIVEN the human writes "reviewed sheet orders-api" WHEN the agent runs the review command
THEN the front matter reads `status: reviewed`.
**Scenario — error:** GIVEN no review marker for `orders-api` WHEN the agent runs the review command THEN it refuses
`review needs the owner's own message (D-01)`.

### 6.5 REQ-LD-043 — Re-running the bootstrap is safe
WHEN the bootstrap runs again, it SHALL NOT overwrite a `reviewed` sheet; it SHALL regenerate only `draft` sheets and
show additions for reviewed ones as a proposed diff.

Traces to PRD: §6 S-6, O-7 · Decision: D-38

**Scenario — success:** GIVEN one reviewed and one draft sheet WHEN the bootstrap runs THEN the draft is refreshed and
the reviewed one gets a proposed diff.
**Scenario — error:** GIVEN a sheet whose front matter cannot be parsed WHEN the bootstrap runs THEN it treats the sheet
as reviewed, leaves it untouched and reports `orders-api.md: front matter unreadable — kept`.

## Requirement 7: README kept current (D-38 part 3)

### 7.1 REQ-LD-044 — The minimal section set
WHERE the README setting is `on` (`project.json:readme.check`, read like the capture setting; `karvey-init` asks it
for a new project with `on` recommended; upgrade step LD-3 sets it; absent means `off`), each repository of the
project SHALL have a README with these sections: purpose; quick start; how to run the tests;
configuration (setting and environment-variable names, required or not, defaults — never values); components (a
link to each component sheet of that repository); deploy and operation (a pointer); a section SHALL be recognised
by its heading through a multilingual alias list or by an explicit section marker.

Traces to PRD: §6 S-7, O-8, AC-9 · Decision: D-38

**Scenario — success:** GIVEN a README with the headings "Purpose", "Quick start", "Tests", "Configuration",
"Components", "Deploy" WHEN the README check runs THEN it passes; GIVEN the same headings in Spanish THEN it passes.
**Scenario — error:** GIVEN a README without a configuration section WHEN the check runs THEN it reports `README:
configuration section missing`.

### 7.2 REQ-LD-045 — Checked when what it describes changes
WHEN QA (or QA-lite) runs WHERE the README setting is `on`, the README check SHALL report a change whose range touches, in a repository, a setup
file (dependency manifest, container file, task-runner file; patterns overridable), a command definition, a newly
read environment variable name or that repository's components in the map, without touching that repository's
README; it SHALL be warn in 4.2.

Traces to PRD: §6 S-7, O-8, AC-9 · Decision: D-38

**Scenario — success:** GIVEN a change that adds `ORDERS_TIMEOUT_MS` and lists it in the README configuration WHEN QA
runs THEN nothing is reported.
**Scenario — error:** GIVEN a change that adds a dependency to the manifest and leaves the README alone WHEN QA runs
THEN it reports `README not updated: setup file package manifest changed`.

### 7.3 REQ-LD-046 — Settings documented somewhere
WHERE the README setting is `on`, the README check SHALL report every environment-variable name read in the repository's code that appears neither
in the README configuration section nor in a component sheet's settings of that repository.

Traces to PRD: §6 S-7, O-8, AC-9 · Decision: D-38

**Scenario — success:** GIVEN every read name in the README or a sheet WHEN the check runs THEN it passes.
**Scenario — error:** GIVEN `ORDERS_RETRY` read in code and documented nowhere WHEN the check runs THEN it reports
`undocumented setting ORDERS_RETRY (services/orders/config.py:12)`.

### 7.4 REQ-LD-047 — Bootstrap and update through karvey-docs
`karvey-docs readme --bootstrap` SHALL add each missing section, as a generated block between markers, filled from
the code and the component map; `--update` SHALL refresh only generated blocks (components list, settings table)
and SHALL never change text outside them; both SHALL run the leak check and write on a docs branch.

Traces to PRD: §6 S-7, O-8 · Decision: D-38 · Changes the `karvey-docs` skill text (it now writes README blocks; no living requirement states its scope)

**Scenario — success:** GIVEN a README with only a purpose paragraph WHEN `--bootstrap` runs THEN the five missing
sections appear as generated blocks and the purpose paragraph is unchanged.
**Scenario — error:** GIVEN a human edit inside a generated block WHEN `--update` runs THEN it does not overwrite the
block and reports `generated block edited by hand: configuration — move the text out or accept regeneration`.

### 7.5 REQ-LD-048 — Every repository of the project
WHERE the project declares several repositories, the README check SHALL run in each repository for that
repository's README, and the spec repository's QA summary SHALL list the result per repository.

Traces to PRD: §6 S-7, O-8 · Decision: D-38

**Scenario — success:** GIVEN a project with two repositories WHEN QA runs THEN the summary shows one README line per
repository.
**Scenario — error:** GIVEN a repository not reachable from the session WHEN QA runs THEN its line reads `README:
not checked (repository not reachable)`.

## Requirement 8: Integration with the method

### 8.1 REQ-LD-049 — Upgrade steps for existing projects
The project-upgrade step catalogue SHALL contain three steps, each with the seven declared fields: `LD-1` turns
capture on (needs a human: yes, since it records the owner's words; risk medium); `LD-2` proposes the component map
and draft sheets through the bootstrap (dry-run: yes; risk medium); `LD-3` adds the README's missing sections
(dry-run: yes; risk low); each SHALL be idempotent and applied on the upgrade branch only.

Traces to PRD: §6 S-8, O-9, AC-10 · Decision: D-38, D-20 · Builds on: REQ-UP-008, REQ-UP-011..014

**Scenario — success:** GIVEN a 4.1 project WHEN the upgrade plan is computed THEN it lists LD-1, LD-2 and LD-3 with
their fields, and dry-run writes nothing.
**Scenario — error:** GIVEN a project with capture already on and a complete map WHEN the plan is computed THEN LD-1
and LD-2 are not listed (nothing applies).

### 8.2 REQ-LD-050 — Lanes and gates
The classification check (REQ-LD-016) SHALL apply at every human gate each lane has (merged or granular), the
component delta (REQ-LD-026) only where architecture runs, and the sheet, section and README checks in every lane
whose change touches code, reported by QA or QA-lite; the `docs` lane SHALL run the section and README checks on
its own documents.

Traces to PRD: §6 S-8 · Decision: D-38, D-22, D-24 · Builds on: REQ-W2-011, REQ-W2-034, REQ-W2-039

**Scenario — success:** GIVEN a `patch` change WHEN its production gate is approved THEN REQ-LD-016 was checked and
QA-lite listed the sheet check.
**Scenario — error:** GIVEN a `docs` change that breaks a sheet's mandatory section WHEN QA-lite runs THEN it reports
the section.

### 8.3 REQ-LD-051 — Loaded only by the phases that act on it
Each new rule (instructions, components, README) SHALL be named only in the load lists of the skills that act on
it — the instruction contract through the core, components by architecture, tasks, impl, qa, archive and docs,
the README by qa, archive and docs; the size tool SHALL store a snapshot of the implementation's base (with
`wave3-optimization`'s implementation merged, REQ-LD-057) before the first implementation commit, and WHEN this
change's implementation is complete it SHALL report every phase's closure against that snapshot; the test phase SHALL
fail if any phase's closure grows by more than 10%.

Traces to PRD: §6 S-8, O-10, AC-11 · Decision: D-38 · Builds on: REQ-W3-001, 004, 011

**Scenario — success:** GIVEN the implementation WHEN the size tool runs THEN it prints the growth per phase, each at
or below 10%.
**Scenario — error:** GIVEN `karvey-mockup` naming the components rule in its load list WHEN the size tool runs THEN
its growth is reported and the linter flags a rule loaded by a phase that does not act on it.

### 8.4 REQ-LD-052 — The core names the instruction contract
The core of hard contracts SHALL gain one contract — "an instruction captured by the hook is classified before its
phase closes; the agent never writes or edits an instruction row" — with a stable contract id, and the core SHALL
remain within its word limit.

Traces to PRD: §6 S-8, O-1 · Decision: D-38 · MODIFIES REQ-W3-003

**Scenario — success:** GIVEN the new contract WHEN the contract coverage check runs THEN every phase skill reaches it
through the core.
**Scenario — error:** GIVEN the core above its limit after the addition WHEN the linter runs THEN it fails with the
word count, and the text is shortened, not the limit raised.

### 8.5 REQ-LD-053 — Registered modes
Every check of this change SHALL be registered in the check-mode registry with its 4.2 default: instruction
classification, project-inbox hold and instruction tamper — blocking where capture is on (D-38); secret in a sheet, in bootstrap or in
README output — blocking; sheet check, section check, component delta, README sections, README trigger and
undocumented settings — warn (the sheet check blocking by project opt-in); schema drift and the relational check
— advisory.

Traces to PRD: §6 S-8, §9, AC-11 · Decision: D-38, D-24 · Builds on: REQ-W3-061

**Scenario — success:** GIVEN the registry WHEN `validate` resolves the modes of a 4.2 project THEN each check has the
default above.
**Scenario — error:** GIVEN a check used by a script but absent from the registry WHEN the linter runs THEN it fails
naming the check.

### 8.6 REQ-LD-054 — Backward compatible
WHERE a project has no component map, capture off and the README setting off or absent, every check of this change SHALL be silent
and `validate` SHALL accept every 4.1.0 shape; a project that passes under 4.1.0 SHALL pass under 4.2.0 with the
defaults.

Traces to PRD: §9, O-9, AC-11 · Decision: D-38, D-24

**Scenario — success:** GIVEN a 4.1.0 fixture project WHEN the 4.2.0 validate, lint and gates run THEN the results are
unchanged.
**Scenario — error:** GIVEN a 4.1.0 project that turns capture on WHEN an old change has no instruction rows THEN
nothing is refused: only rows captured after the setting took effect count.

### 8.7 REQ-LD-055 — Documented where people look
The method SHALL document each of the three parts in its rule, in a section of the plugin README that names the
part's setting, its commands and its upgrade step, and in the `karvey-docs` skill; the method's existing neutrality
lint SHALL pass over every new or changed file.

Traces to PRD: §6 S-8, §9 · Decision: D-38

**Scenario — success:** GIVEN the release WHEN the linter checks the README THEN it finds three sections, each naming
`instructions.capture` / `components` / `readme.check`, its commands and `LD-1` / `LD-2` / `LD-3`.
**Scenario — error:** GIVEN a rule example naming a real organisation or vendor as a requirement WHEN the neutrality
lint runs THEN it fails naming the line.

## Requirement 9: Change-scoped obligations (not merged into the living spec)

### 9.1 REQ-LD-056 — Dogfooding on this repository
This change SHALL declare the method repository's own components in its map, give each a reviewed sheet, bring its
README to the section set, and run with capture on from the start of its implementation.

Traces to PRD: §9 (dogfooding) · Decision: D-38

**Scenario — success:** GIVEN the implementation done WHEN the sheet, section and README checks run on this repository
THEN they are green.
**Scenario — error:** GIVEN a component of this repository without a sheet WHEN QA runs THEN it reports the component
and QA does not pass until it has one.

### 9.2 REQ-LD-057 — Implementation after Wave 3
This change's implementation SHALL start only after `wave3-optimization`'s implementation is merged into this
branch's base, and SHALL rebase the load lists and the core it modifies onto the Wave 3 text.

Traces to PRD: §9 (sequencing) · Decision: D-38

**Scenario — success:** GIVEN Wave 3's implementation merged WHEN `advance living-docs impl` runs THEN the base holds
the Wave 3 core and load lists.
**Scenario — error:** GIVEN Wave 3's implementation not merged WHEN impl would start THEN the tasks' first item
(verify the base) fails and impl waits.

## Explicit exclusions
- Capturing tool output, attachments, other people's messages or other agents' messages (PRD §7).
- Classifying rows automatically: the hook only decides whether to capture; the agent classifies, the human sees it.
- Writing to any data store, reading a production store, sampling relational tables live (relational sheets come
  from the repository's migration and schema files).
- Generating API reference pages; a sheet links to them.
- Enforcing a documentation language or style beyond the required sections.
- Capturing instructions retroactively from past sessions.
- Anything under the user's home directory or the owner's global configuration.
- Behaviour that does not change: the approval vocabulary's approval, negation and production lists; the finding
  types of the iteration loop (bug, spec-gap, emergent); the existing `karvey-docs` Diataxis modes.
