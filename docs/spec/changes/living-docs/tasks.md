# Tasks: living-docs

> PHASE 7 (`karvey-tasks`, skill text read from `plugins/karvey/skills/karvey-tasks/SKILL.md` in this worktree) · Security Tier 3 · Lane `standard` · Tracker: Markdown (`project.json:management.tool = markdown`): this file + `PLAN.md`, no external tracker.
> Inputs: `architecture.md` (generated for the merged *how* gate; revised after its judges, F-32..F-59), `requirements.md` (REQ-LD-001..063, approved under D-21), `prd.md`, `spec.json`, `risks.md`, the house style of `wave3-optimization/tasks.md`, and the code on `feature/living-docs` at `b50d34c`.
>
> **Estimates are calibrated.** In this repo the skill's 10–30 min band ran about 10× high. The minutes below are realistic **AI execution + human review** for one task (typically 3–8 min AI + 2–7 min review), as in Waves 2 and 3. `karvey-impl` records the actuals next to them in `PLAN.md` and never edits an estimate.

## Summary

| Item | Value |
|---|---|
| Features | 9 (the PLAN.md features F1..F9, same numbering) + `E1.DEPLOY` |
| Tasks | 71 (64 Backend, 5 Test, 2 human) |
| Agent tasks / `[human]` tasks | 69 / 2 |
| Total estimate (agent tasks, AI + review, calibrated) | **794 min** (≈ 13.2 h) |
| Critical path by dependencies (agent minutes; the `[human]` waits not counted) | **169 min** (≈ 2.8 h), 14 tasks |
| REQ-LD coverage | 63/63 |
| Largest task | 15 min (cap 60) |

## Conventions

- **IDs** `E1.F{n}.T{n}`; E1 = this change, F{n} = the PLAN.md feature of the same number (the architecture's components C-01..C-21 map to them in the feature headers). The production OK is `E1.DEPLOY.T1`: deploy work belongs to the Epic, not to a Feature.
- **Layers:** `[Backend]` = plugin hooks, scripts, library, schemas, templates and skill/rule text; `[Test]` = test-only work (the labelled detector table, end-to-end tables, compatibility, the base check, the whole-repo gate); `[human]` = a step only a person may run (`rules/multi-agent.md` §5). No DB, Frontend or Infra task: no database, no UI, no cloud (infra skipped, architecture A-18); the one CI step sits in E1.F3.T5.
- **Estimate** = AI execution + review, minutes, calibrated (header). A `[human]` task carries no estimate; it declares the executor.
- **(P)** = can run in parallel with other (P) tasks whose dependencies are met, because the files differ. Tasks that share `karvey-state.py`, `karvey-docs.py`, `instructions.py`, `components.py`, `lint-plugin.py` or `karvey-context.py` run in sequence even when marked (P); `karvey-impl` picks the order.
- **Test first** (REQ-W2-057): each task's **Tests added** are written before its code and fail until the code lands; tests are tagged `@req REQ-LD-NNN` in their docstring or named `test_REQ_LD_NNN_*`. Manual scripts are named in their tasks with `manual:` reasons in their files.
- **Sheet line** (REQ-LD-027, applied to this plan): this repository has no component map until E1.F9.T4, so no task before it carries a `Sheet:` line; the map's own sheets are written by E1.F9.T4..T6 and reviewed by E1.F9.T7. From E1.F9.T4 on, a task that changes a mapped path updates the component's sheet in the same commit (the sheet check runs at every task close).
- **Every impl commit** carries `Karvey-Change: living-docs`, adds one line under `## [Unreleased]` in `CHANGELOG.md`, and changes no version. The version number (4.2.0) is fixed at release by `karvey-deploy`.
- **Done criterion** is a command, run from the repo root. Unit tests: `python3 -m unittest discover -s plugins/karvey/tests/unit -p '<file>' -v`. Tables: `python3 plugins/karvey/tests/hooks/run_tables.py --only <table>`. Lint: `python3 plugins/karvey/scripts/lint-plugin.py [--only L-NN]` — 0 errors after every task.
- **Neutral text:** no organisation, product, client or person names, no ids, no home paths, no secrets in any new file (PRD §9). Fixtures are fictional and anonymised (`test_fixtures_anonymous.py`); data-store examples name families, never a vendor as a requirement.
- **Nothing outside the repository is written** by an agent task, except the machine-local state directory inside the git common dir, which the hook and the tools own.
- **Line numbers** in the architecture are from `b50d34c`; E1.F9.T1 re-verifies the architecture §13 list after the rebase onto Wave 3's final head, and each task re-reads the lines it edits.
- **One requirement, one Feature**: every requirement's tasks sit in its PLAN.md Feature; the exceptions carry a `Split:` line.

## Execution order

1. **E1.F9.T1 first**: Wave 3's implementation and the project-upgrade engine are in the base, or impl waits (REQ-LD-057). Then **E1.F9.T2**: the size base snapshot in a commit of its own, before any rule or skill edit (REQ-LD-051). **E1.F8.T1** (the check-mode rows) runs early too: every later check reads its mode from it (L-76).
2. **F1 → F2** (capture, then classification) and **F3 → F4, F5, F6, F7** (map and sheets, then lifecycle, schema check, bootstrap, README) run as their dependencies land; the two chains meet only at E1.F1.T8 (it reads the setting schema of E1.F3.T1) and in F8.
3. **F8** wires the parts into lanes, rules, load lists, the core and the documentation, and proves 4.1 compatibility.
4. **F9 dogfooding**: capture on for this repository as soon as the guard exists (E1.F9.T3), then the map, the eight sheets, the owner's review (`[human]`), the README, the whole-repo gate and the release docs.
5. `E1.DEPLOY.T1` (`[human]`) is the production OK at release; QA and archive are phases, not tasks here.

## Feature E1.F1: Instruction capture: vocabulary, detector, redaction, store and rows, guard, confirm phrases, inbox, removal, tamper refusal

Architecture §1.3–§1.7, §3 (S-1..S-5), §4.2.  
Requirements covered: 001..012, 058, 059, 060, 063  
Total estimated time: 166 min (14 tasks)

### E1.F1.T1 [Backend] Vocabulary: `directive`, `question` (per language en, es, pt, de, fr), `markers` (`#off`, `#note`), `confirm` (remove / review verbs and nouns), `rules.capture_*`; override key `enforcement.instruction_vocabulary` read from the reviewed line; L-80 — _Depends: E1.F9.T1_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/vocabulary.json`; `plugins/karvey/scripts/karvey_lib/approval.py` (`vocabulary()` merges the new keys); `plugins/karvey/scripts/lint-plugin.py` (L-80); `plugins/karvey/tests/unit/test_approval_vocab.py` (cases); `plugins/karvey/tests/unit/test_lint_ld.py`  
**Requirements:** REQ-LD-003  
**Tests added:** the approval, negation and prod lists are byte-identical to before; a working-copy override is ignored and audited `vocabulary override ignored (not reviewed)`; L-80 mutation: an empty `question.fr` → error  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_approval_vocab.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-80` exits 0

### E1.F1.T2 [Test] Labelled detector table `tests/hooks/tables/instructions-detect.json` (≥ 30 prompts per shipped language: questions, approvals, chit-chat, mixed, commands, instructions) + `test_instructions_detect.py` printing recall / precision per language and overall — _Depends: E1.F1.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/tests/hooks/tables/instructions-detect.json` (NEW, fictional prompts); `plugins/karvey/tests/unit/test_instructions_detect.py` (NEW)  
**Requirements:** REQ-LD-004  
**Tests added:** `test_REQ_LD_004_recall_precision` fails with `ImportError: detect` until E1.F1.T3; thresholds 0.90 / 0.80; the failure names the missed prompts  
**Done when:** the suite runs and fails for the expected reason before E1.F1.T3 (`python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_detect.py' -v`)

### E1.F1.T3 [Backend] `karvey_lib/instructions.py` `detect()`: `#off` → skip, confirm phrase → no capture, `#note` → forced, strip + normalise, command / approval-only / < 4 words → no, directive wins over question, > 40 words → yes — _Depends: E1.F1.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/instructions.py` (NEW, detector section); `plugins/karvey/tests/unit/test_instructions_detect.py` (cases)  
**Requirements:** REQ-LD-002, REQ-LD-005, REQ-LD-058  
**Tests added:** the REQ-LD-002 scenarios ("why does the export fail?", "ok", "thanks!", "/karvey-qa x" → no; "why does it fail? it must retry twice" → yes; "export monthly from now on" → no); `#off` mid-prompt is text; `#note` forces  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_detect.py' -v` passes: recall ≥ 0.90 and precision ≥ 0.80 in every language and overall

### E1.F1.T4 [Backend] `karvey_lib/redact.py`: pasted fenced blocks and long lines → markers with counts; 4,000-char cap; `[redacted:secret|email|phone]` (leak `secret` patterns + the new capture-only `capture` group — assignment and `is` forms, Luhn-valid card numbers — e-mail, international phone); `RedactionUnavailable` fails closed — _Depends: E1.F9.T1_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/redact.py` (NEW); `plugins/karvey/scripts/karvey_lib/leak_patterns.json` (`capture` group); `plugins/karvey/tests/unit/test_redact.py` (NEW); `plugins/karvey/tests/unit/test_leakcheck.py` (one case: the sponsor leak check does **not** read the `capture` group)  
**Requirements:** REQ-LD-006, REQ-LD-007  
**Tests added:** "use key token=abc123XYZ and tell ana@example.org" → both redacted; "the password is hunter22" → redacted; a Luhn-valid 16-digit number → redacted, a 16-digit non-Luhn id kept; "retry 3 times within 30000 ms" unchanged; `+1 555 010 0199` redacted; a sponsor page that passed under 4.1 still passes; a 60-line fenced log → `[pasted block: 60 lines omitted]`; a corrupt pattern file raises `RedactionUnavailable`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_redact.py' -v` and `-p 'test_leakcheck.py'` pass

### E1.F1.T5 [Backend] Capture store `<state>/instructions/<scope>.jsonl` (two-phase `pending` → `written`, sha256, clone id, 0700/0600) + findings lock in `instructions/locks/` (pid, time, stale after 5 s) + row writer (next `F-NN`, header of `judges.py`, escaping incl. comment delimiters, `clone=… sha256=…` comment); `judges collect` takes the same lock — _Depends: E1.F9.T1_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/instructions.py` (store and rows); `plugins/karvey/scripts/karvey_lib/judges.py` (lock in collect); `plugins/karvey/tests/unit/test_instructions_store.py` (NEW); `plugins/karvey/tests/unit/test_judges.py` (lock case)  
**Requirements:** REQ-LD-001, REQ-LD-008  
**Tests added:** entry has id, change, time, clone, redacted text and a hash equal to the row's; `|`, newlines and a pasted `<!-- karvey:capture … -->` round-trip without adding a second comment; a 6-second-old lock is broken and audited; two concurrent writers get F-12 and F-13; a crash after `pending` leaves a verifiable state; no file under the repository tree changes except `findings.md`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_store.py' -v` and `-p 'test_judges.py'` pass

### E1.F1.T6 [Backend] Protect-paths: needle `karvey/instructions` in `STATE_NEEDLES` and in the no-python `needles=` of `karvey-hook.sh`; guard table cases (Edit, Write, Bash with `$(git rev-parse …)`) — _Depends: E1.F1.T5_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/guards.py`; `plugins/karvey/hooks/karvey-hook.sh`; `plugins/karvey/tests/hooks/tables/` (protect-paths cases)  
**Requirements:** REQ-LD-008  
**Tests added:** a Write to `<common dir>/karvey/instructions/x.jsonl` and `echo >> …/karvey/instructions/…` are blocked with the D-01 message, with and without python  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only protect-paths` passes and `bash plugins/karvey/hooks/tests/test-hooks.sh` passes

### E1.F1.T7 [Backend] `instructions.verify(change)`: verified, `not verifiable here` (another clone, own hash matches, listed with its clone id), tampered, missing, extra (incl. a row claiming this clone without an entry), pending-without-row (failure), removed — _Depends: E1.F1.T5_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/instructions.py` (verify); `plugins/karvey/tests/unit/test_instructions_store.py` (verify section)  
**Requirements:** REQ-LD-059  
**Tests added:** three local rows + one from another clone → `3 verified, 1 not verifiable here`; a shortened text → tampered; a deleted row → missing; a hand-added row naming this clone → extra; a hand-added row naming an unknown clone with a matching hash → `not verifiable here`, listed with its clone id  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_store.py' -v` passes

### E1.F1.T8 [Backend] Capture guard `instruction_capture` + registry row after `approval`: effective setting (reviewed line; the working copy only turns it on; ignored `off` audited), scope (one active change → row; none/several → inbox `I-N`), 1 s deadline, fail open with `failed` entry, health file, audit records without text — _Depends: E1.F1.T3, E1.F1.T4, E1.F1.T5, E1.F3.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/guards.py`; `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (registry); `plugins/karvey/tests/hooks/tables/capture.json` (NEW, guard cases)  
**Requirements:** REQ-LD-001, REQ-LD-009, REQ-LD-010, REQ-LD-011  
**Tests added:** capture on + one active change → row + store; two active → inbox only, no tracked file; reviewed `on` + working copy `off` → still on, audited; unwritable store → prompt passes, `failed` recorded; deadline → same; capture off → silent  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only capture` passes

### E1.F1.T9 [Backend] Prompt-event output where capture is on: `dispatch` prints one JSON object (`systemMessage` + `additionalContext`) with every guard's lines (acknowledgement, not-captured notice, approval line); plain text, byte-identical to 4.1, where capture is off; no-python notice in `karvey-hook.sh` — _Depends: E1.F1.T8_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (`dispatch`); `plugins/karvey/hooks/karvey-hook.sh`; `plugins/karvey/tests/hooks/tables/` (approval and capture cases); `plugins/karvey/hooks/tests/test-hooks.sh`  
**Requirements:** REQ-LD-010, REQ-LD-058  
**Tests added:** the output parses as JSON with both fields holding `captured as instruction F-12`; the approval guard's `approval recorded` line keeps its text; with capture off every existing prompt table case passes unchanged; without python and with `"capture": "on"` → `instruction capture unavailable (no python)`  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only capture`, `python3 plugins/karvey/tests/hooks/run_tables.py --only approval` and `bash plugins/karvey/hooks/tests/test-hooks.sh` pass

### E1.F1.T10 [Backend] Confirm phrases: `classify_confirm` on the stripped text (remove / review, every shipped language) → one-use markers under `approvals/confirm/`; a confirm phrase is never captured — _Depends: E1.F1.T3_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/instructions.py` (confirm); `plugins/karvey/scripts/karvey_lib/approval.py` (marker path helper); `plugins/karvey/scripts/karvey_lib/guards.py`; `plugins/karvey/tests/unit/test_instructions_detect.py` (confirm cases)  
**Requirements:** REQ-LD-063  
**Tests added:** "remove instruction F-14" → marker for F-14 and no row; `> remove instruction F-14` quoted or inside a pasted block → no marker; "remove F-14, it said …" → no marker, detection applies; "reviewed sheet orders-api" → review marker; markers expire with the approval TTL  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_detect.py' -v` passes

### E1.F1.T11 [Backend] State tool: `instruction list` + `instructions.gate_blockers` (tamper, inbox hold) wired in `advance`, `approve`, `approve-gate` and `next`; `validate` prints the verification summary; `spec.schema.json:instruction_log[]` — _Depends: E1.F1.T7, E1.F8.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/scripts/karvey_lib/instructions.py` (gate_blockers); `plugins/karvey/schemas/spec.schema.json`; `plugins/karvey/tests/unit/test_instructions_state.py` (NEW); `plugins/karvey/tests/unit/test_schema_ld.py` (NEW)  
**Requirements:** REQ-LD-059, REQ-LD-060  
**Tests added:** a tampered row → `approve` refuses `instruction F-12 tampered (…)`; one unassigned inbox entry → every change's `approve` refuses naming `I-3`; entries captured after the call do not count; capture off → silent; a 4.1 `spec.json` still validates `--strict`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_state.py' -v` and `-p 'test_schema_ld.py'` pass

### E1.F1.T12 [Backend] `instruction assign <I-N> <change>` (row from the stored text, never an argument) and `instruction classify _project <I-N> --as not-instruction --reason` — _Depends: E1.F1.T11_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/scripts/karvey_lib/instructions.py`; `plugins/karvey/tests/unit/test_instructions_state.py` (inbox section)  
**Requirements:** REQ-LD-009, REQ-LD-060  
**Tests added:** assign writes the row with the stored text and a `written` entry `from: _project/I-3`; a text argument is refused; an inbox classification other than `not-instruction`, or without a 10-char reason, is refused; after either, the gates pass  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_state.py' -v` passes

### E1.F1.T13 [Backend] `instruction remove <change> <F-NN>` with the removal marker: row and store text → `[removed at the owner's request]`, id / time / class kept, audit record; verify accepts it — _Depends: E1.F1.T10, E1.F1.T11_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/scripts/karvey_lib/instructions.py`; `plugins/karvey/tests/unit/test_instructions_state.py` (removal section)  
**Requirements:** REQ-LD-012  
**Tests added:** with the marker → removed and `validate` says removed, not tampered; a row already committed → also prints `the text remains in commit <sha>; rewriting history is the owner's decision`; without → refused `removal needs the owner's own message (D-01)`; the marker is single-use  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_state.py' -v` passes

### E1.F1.T14 [Test] Capture end-to-end: `capture.json` full cases (off-the-record keeps no text and no hash, pasted block, redaction, force with capture off, inbox, reviewed vs working copy, deadline, unwritable store, JSON output) + manual `tests/manual/capture-visible.md` — _Depends: E1.F1.T9, E1.F1.T10, E1.F1.T12_

**Estimate:** 12 min  
**Files:** `plugins/karvey/tests/hooks/tables/capture.json`; `plugins/karvey/tests/manual/capture-visible.md` (NEW, `manual:` the runtime display is not scriptable)  
**Requirements:** REQ-LD-001, REQ-LD-005, REQ-LD-006, REQ-LD-010, REQ-LD-011, REQ-LD-058  
**Tests added:** every REQ-LD-001/005/006/010/011/058 scenario as a table case  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only capture` passes; `python3 plugins/karvey/scripts/lint-plugin.py` 0 errors

## Feature E1.F2: Instruction classification: four classes, revision linkage, state tool only, gate refusal, gate summary, session and dashboard

Architecture §1.7, §1.8.  
Requirements covered: 013..018  
Total estimated time: 65 min (6 tasks)

### E1.F2.T1 [Backend] `instruction classify` with the four classes and resolvable evidence (REQ ids in `requirements.md`, F ids in `findings.md`, reasons ≥ 10 chars); rewrites the class cells under the findings lock; appends a `classified` line to the protected store (the authority) and to `instruction_log` (lock + CAS) — _Depends: E1.F1.T11_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey-state.py`; `plugins/karvey/scripts/karvey_lib/instructions.py` (classify); `plugins/karvey/tests/unit/test_instructions_state.py` (classify section)  
**Requirements:** REQ-LD-013, REQ-LD-015  
**Tests added:** `--as requirement-revision --ref REQ-LD-021` recorded; `--as no-spec-impact` without reason → `no-spec-impact needs --reason`; unknown REQ id → refused naming it; reclassification keeps both entries in the log  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_state.py' -v` passes

### E1.F2.T2 [Backend] Revision linkage: `requirement-revision` after the first requirements approval needs a `revision_history` entry citing the row id — _Depends: E1.F2.T1_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/instructions.py`; `plugins/karvey/tests/unit/test_instructions_state.py`  
**Requirements:** REQ-LD-014  
**Tests added:** before approval: REQ ids suffice; after: refused `requirement-revision after approval needs revision_history citing F-12` until the entry exists  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_state.py' -v` passes

### E1.F2.T3 [Backend] Hand-edited class cell (or cell and `instruction_log` edited together) → `classification not recorded by the state tool` against the store's `classified` lines, in `validate` and verify; the row counts as unclassified — _Depends: E1.F2.T1_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/instructions.py`; `plugins/karvey/scripts/karvey-state.py` (`cmd_validate`); `plugins/karvey/tests/unit/test_instructions_state.py`  
**Requirements:** REQ-LD-015  
**Tests added:** a Status cell changed by hand → reported and treated as unclassified; the cell and `spec.json:instruction_log` edited consistently → still reported; the state tool's own write passes  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_state.py' -v` passes

### E1.F2.T4 [Backend] Blockers: unclassified rows captured before the call and an unreadable `findings.md` (capture on) refuse `advance`, `approve` (every phase, `prod` and QA's pass included) and `approve-gate`, in every lane — _Depends: E1.F2.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/instructions.py` (gate_blockers); `plugins/karvey/tests/unit/test_instructions_state.py` (lanes section)  
**Requirements:** REQ-LD-016  
**Tests added:** `advance living-docs test` with F-12 unclassified → `1 instruction unclassified: F-12 — classify it first (…)`; the same in lanes `patch`, `hotfix`, `docs`, merged and granular gates, `approve prod`; unreadable findings → refused  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_instructions_state.py' -v` passes

### E1.F2.T5 [Backend] Gate summary block "Instructions since the last gate": captured or (re)classified since the previous outcome, `not-instruction` / `no-spec-impact` first with reasons; dismissed inbox entries; capture failures of the change — _Depends: E1.F2.T1, E1.F1.T12_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-context.py` (`gate_summary`); `plugins/karvey/tests/unit/test_context_instructions.py` (NEW)  
**Requirements:** REQ-LD-017, REQ-LD-010  
**Tests added:** two rows since the last gate, one dismissed → `Instructions since the last gate: 2 — 1 not-instruction ("a thank-you"), 1 requirement-revision → REQ-LD-021`; a row reclassified after the previous gate is listed; a `failed` entry is listed  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_instructions.py' -v` and `-p 'test_context_gate.py'` pass

- **Split:** REQ-LD-010's gate-summary listing lands here with the block it belongs to; the rest of REQ-LD-010 is F1.

### E1.F2.T6 [Backend] Session hook and dashboard: per active change `N instructions unclassified`; `N instruction(s) waiting for a change`; `instruction capture on|off|unavailable`; `instructions: store unreadable` (≤ 4 lines, counts only) — _Depends: E1.F2.T1, E1.F1.T8_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/karvey_hooks.py` (`open_work_block`); `plugins/karvey/scripts/karvey-context.py` (`open_work`); `plugins/karvey/tests/hooks/tables/session.json` (cases); `plugins/karvey/tests/unit/test_context_instructions.py`  
**Requirements:** REQ-LD-018, REQ-LD-009  
**Tests added:** two unclassified rows → `2 instructions unclassified`; one inbox entry → `1 instruction waiting for a change`; health file with a failure → `instruction capture unavailable`; unreadable store → `instructions: store unreadable`  
**Done when:** `python3 plugins/karvey/tests/hooks/run_tables.py --only session` and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_instructions.py' -v` pass

## Feature E1.F3: Component map, sheet templates, section / reference / leak checks, the `karvey-docs.py` CLI

Architecture §1.9–§1.11, §2.  
Requirements covered: 019..025  
Total estimated time: 64 min (5 tasks)

### E1.F3.T1 [Backend] `project.schema.json`: `instructions`, `components[]` (id, kind, repo, paths, exclude, sheet, sample), `components_settings`, `environments`, `readme`; `validate` refuses unknown kind, duplicate id, sheet outside `docs/spec/components/`, absolute or `..` path, literal connection, undeclared environment — _Depends: E1.F9.T1_ (P)

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/project.schema.json`; `plugins/karvey/scripts/karvey-state.py` (`cmd_validate`); `plugins/karvey/tests/unit/test_schema_ld.py`  
**Requirements:** REQ-LD-019  
**Tests added:** four components of four kinds validate; `kind: database` → `components[2].kind: database is not one of …`; `connection_ref: "proto://host/…"` → refused without echoing the value; a 4.1 `project.json` validates unchanged; every keyword in the `schema_lite` subset  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_schema_ld.py' -v` and `-p 'test_schemas.py'` pass

- **Split:** The schema also carries the fields REQ-LD-011, 035 and 044 read; their behaviour is tested in F1, F5 and F7.

### E1.F3.T2 [Backend] `schemas/component-kinds.json` (sections, aliases in five languages, reference sections, structural rules) + the four templates under `templates/components/` + L-79 (templates equal the data) — _Depends: E1.F3.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/schemas/component-kinds.json` (NEW); `plugins/karvey/templates/components/{data-store,backend-service,frontend-module,infra-resource}.md` (NEW); `plugins/karvey/scripts/lint-plugin.py` (L-79); `plugins/karvey/tests/unit/test_lint_ld.py`  
**Requirements:** REQ-LD-020, REQ-LD-021, REQ-LD-022  
**Tests added:** each template has exactly its kind's mandatory sections with fictional examples; removing `runbook` from the infra template → L-79 error  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-79` exits 0 and `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_lint_ld.py' -v` passes

### E1.F3.T3 [Backend] `karvey_lib/components.py`: map load (globs, `exclude`), sheet parse (front matter, sections by alias, containers), section check (absent / empty, `n/a — reason`, front-matter id vs map, document container without schema) — _Depends: E1.F3.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/components.py` (NEW); `plugins/karvey/tests/unit/test_components.py` (NEW); `plugins/karvey/tests/unit/fixtures/components/` (NEW: four fictional sheets)  
**Requirements:** REQ-LD-023  
**Tests added:** a complete document-store sheet passes; `Indexes: n/a — the family has none` counts; `events: document schema missing`; `sheet docs/spec/components/a.md declares id b; the map says a`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_components.py' -v` passes

### E1.F3.T4 [Backend] Settings tables hold names only (value column reported) and references resolve (`external: {role}` or a map id, `did you mean` by edit distance ≤ 2) — _Depends: E1.F3.T3_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/components.py`; `plugins/karvey/tests/unit/test_components.py`  
**Requirements:** REQ-LD-021, REQ-LD-025  
**Tests added:** a settings table with a value column → `settings: values are not allowed, names only`; reader `order-api` → `unknown component order-api (did you mean orders-api?)`; `external: payment provider` resolves  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_components.py' -v` passes

### E1.F3.T5 [Backend] `karvey-docs.py` CLI (envelope, exit codes) with `components --check [--sections] [--leak]`; leak check over every sheet (sheet:line rule, never the value); CI step in `lint.yml` — _Depends: E1.F3.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-docs.py` (NEW); `.github/workflows/lint.yml`; `plugins/karvey/tests/unit/test_components.py` (CLI section); `plugins/karvey/tests/unit/test_ci_workflow.py` (case)  
**Requirements:** REQ-LD-024  
**Tests added:** `api_key=4f9c…` in a sheet → exit 1 `orders-store.md:41 secret pattern`, the value absent from stdout, stderr and JSON; `ORDERS_STORE_KEY` as a reference passes; the CI step is read-only and has no secret  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_components.py' -v` and `-p 'test_ci_workflow.py'` pass; `python3 plugins/karvey/scripts/karvey-docs.py components --check --json | python3 -m json.tool > /dev/null` exits 0

## Feature E1.F4: Sheet lifecycle: delta, tasks pairing, commit and change pairing, archive reconcile / stamp / retire, parallel deltas, judges

Architecture §1.12.  
Requirements covered: 026..032, 062  
Total estimated time: 91 min (8 tasks)

### E1.F4.T1 [Backend] Component delta: `components.parse_delta`; `generated architecture` warns when the section is missing (check `components.delta`); `karvey-architecture` template and review gate gain `## Component delta` — _Depends: E1.F3.T3, E1.F8.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/components.py`; `plugins/karvey/scripts/karvey-state.py` (`cmd_generated`); `plugins/karvey/skills/karvey-architecture/SKILL.md`; `plugins/karvey/tests/unit/test_component_lifecycle.py` (NEW)  
**Requirements:** REQ-LD-026  
**Tests added:** `MODIFIED orders-store: containers.events, invariants` parsed; missing section → warning `component delta missing — declare it or write none with a reason`; `none — docs only` accepted  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_component_lifecycle.py' -v` passes

### E1.F4.T2 [Backend] `components --delta-coverage <change>`: each delta item named by a task's `Sheet:` line; `karvey-tasks` gains the `Sheet:` line and runs it in its review gate — _Depends: E1.F4.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/scripts/karvey_lib/components.py`; `plugins/karvey/skills/karvey-tasks/SKILL.md`; `plugins/karvey/tests/unit/test_component_lifecycle.py`  
**Requirements:** REQ-LD-027  
**Tests added:** a delta item no task names → `delta item orders-store/invariants has no task`; all named → clean  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_component_lifecycle.py' -v` passes

### E1.F4.T3 [Backend] `karvey_lib/sheetcheck.py`: per commit of the range, a mapped path without its sheet is reported unless `Karvey-Sheet-Skip: <id> — <reason>` (listed); `components --check --commits` — _Depends: E1.F3.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/sheetcheck.py` (NEW); `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/tests/unit/test_sheetcheck.py` (NEW, temporary git repos via `_gitrepo.py`)  
**Requirements:** REQ-LD-028  
**Tests added:** code + sheet in one commit → pass; code alone → `commit 1a2b3c4 changes orders-api without its sheet`; skip trailer with reason → pass and listed; skip without reason → reported  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sheetcheck.py' -v` passes

### E1.F4.T4 [Backend] Multi-repository pairing by change: commits selected by `Karvey-Change: <id>` in the component's repository and in the spec repository must both touch it; unreachable repository → `not checked (repository not reachable)` — _Depends: E1.F4.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/sheetcheck.py`; `plugins/karvey/tests/unit/test_sheetcheck.py` (two-repo section)  
**Requirements:** REQ-LD-028  
**Tests added:** code in repo B and sheet in repo A under one change trailer → pass; sheet never touched → reported by change; missing path → not checked  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sheetcheck.py' -v` passes

### E1.F4.T5 [Backend] Wiring: `karvey-impl` runs the pairing at each task close; `karvey-qa` and QA-lite over the change range (no delta needed in lanes without architecture); blocking by `components_settings.sheet_check: blocking` — _Depends: E1.F4.T4, E1.F8.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/skills/karvey-impl/SKILL.md`; `plugins/karvey/skills/karvey-qa/SKILL.md`; `plugins/karvey/scripts/karvey_lib/sheetcheck.py` (mode); `plugins/karvey/tests/unit/test_sheetcheck.py` (modes, patch lane)  
**Requirements:** REQ-LD-028, REQ-LD-032  
**Tests added:** default → warn, exit 0; opt-in → exit 1; a `patch` change with code + sheet → pass without delta; a `hotfix` commit without the sheet → reported (warn) and listed by the release gate summary  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sheetcheck.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py` 0 errors

### E1.F4.T6 [Backend] `components --reconcile <change>` (applied / declared but not applied / changed but not declared) and `--parallel <change>`; the architecture gate summary shows parallel deltas — _Depends: E1.F4.T1, E1.F4.T3_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/scripts/karvey_lib/components.py`; `plugins/karvey/scripts/karvey-context.py` (`gate_summary`); `plugins/karvey/tests/unit/test_component_lifecycle.py`  
**Requirements:** REQ-LD-029, REQ-LD-030  
**Tests added:** delta on orders-store and its sheet changed → `orders-store: applied`; declared orders-api unchanged → `declared but not applied: orders-api`; two changes on orders-store → `also modified by change add-refunds (architecture)`; unreadable other change → `parallel deltas: not checked (…)`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_component_lifecycle.py' -v` and `-p 'test_context_gate.py'` pass

### E1.F4.T7 [Backend] `--reconcile --apply`: stamp `last_change: <change> (<date>)`, move REMOVED sheets to `archive/` and drop them from the map (kept when paths still match files); `karvey-archive` runs it on its branch — _Depends: E1.F4.T6_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/scripts/karvey_lib/components.py`; `plugins/karvey/skills/karvey-archive/SKILL.md`; `plugins/karvey/tests/unit/test_component_lifecycle.py`  
**Requirements:** REQ-LD-062  
**Tests added:** orders-store stamped `last_change: add-export (2026-10-02)`; legacy-queue moved and removed from the map; with 4 matching files → kept and reported; a second run changes nothing  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_component_lifecycle.py' -v` passes

### E1.F4.T8 [Backend] Judges' closed inputs: architecture adds the delta's sheets, QA the sheets of the components the diff touchesafter the phase's own inputs; `missing sheet: <id>` and budget `dropped:` lines printed and repeated in the gate summary's judges block — _Depends: E1.F4.T1_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/judges.py` (`build_inputs`); `plugins/karvey/tests/unit/test_judges.py` (cases)  
**Requirements:** REQ-LD-031, REQ-W2-023 (MODIFIED by this change)  
**Tests added:** `karvey-judges.py inputs <change> architecture` lists `docs/spec/components/orders-store.md`; a delta naming a component without a sheet prints `missing sheet: orders-store` and the run continues  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_judges.py' -v` passes

## Feature E1.F5: Document-schema check: example vs schema, read-only development-only sampler, value-free output, drift, relational files

Architecture §1.13, §1.14, §3 (S-6, S-7, S-11), §4.3.  
Requirements covered: 033..038, 061  
Total estimated time: 92 min (7 tasks)

### E1.F5.T1 [Backend] Example vs schema in the section check (`schema_lite`), failing paths listed, unsupported keywords reported `unchecked keyword` — _Depends: E1.F3.T3_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/components.py`; `plugins/karvey/tests/unit/test_components.py` (example section)  
**Requirements:** REQ-LD-033  
**Tests added:** schema requiring `id`, `status`, `closedAt` + a complete example → pass; example without `closedAt` → `events example: /closedAt required`; `format` keyword → `unchecked keyword format`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_components.py' -v` passes

### E1.F5.T2 [Backend] Sampler core `karvey_lib/sampler/`: adapter contract, allowed-operations proxy, bounds (100 default, ≤ 1,000, 30 s per container), `--dry-run` (operations and containers), `components --check-schema <id>` — _Depends: E1.F3.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/sampler/__init__.py` (NEW); `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/tests/unit/test_sampler.py` (NEW)  
**Requirements:** REQ-LD-034, REQ-LD-036  
**Tests added:** an adapter call outside `ALLOWED` raises and nothing is read; 50,000 fixture docs → 100 read, `sample 100 of an unknown total (limit)`; `--sample 5000` → refused `sample above 1000`; a slow container stops at the deadline  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sampler.py' -v` passes

### E1.F5.T3 [Backend] Adapters `fixture` (records calls) and `jsonl_export` (development export directory); AST test over every shipped adapter + L-81 — _Depends: E1.F5.T2_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/sampler/adapters/{__init__,fixture,jsonl_export}.py` (NEW); `plugins/karvey/tests/unit/test_sampler_adapters_readonly.py` (NEW); `plugins/karvey/scripts/lint-plugin.py` (L-81)  
**Requirements:** REQ-LD-034  
**Tests added:** the fixture adapter records only `query`/`read`; a mutated adapter with a `delete_many` call → the test and L-81 fail naming adapter and operation  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sampler_adapters_readonly.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-81` exits 0

### E1.F5.T4 [Backend] Target guard: sampler settings from the reviewed line only; `env:` reference, or `vault:` through a resolver from `sampler/resolvers.json` (argv templates, NAME pattern, no shell); development host and export-path allow-lists; production refusals — _Depends: E1.F5.T2, E1.F3.T1_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/sampler/__init__.py`; `plugins/karvey/scripts/karvey_lib/sampler/resolvers.json` (NEW); `plugins/karvey/tests/unit/test_sampler.py` (target section)  
**Requirements:** REQ-LD-035  
**Tests added:** `environment: prod` → `schema check reads development data only`; a working-copy-only `sample` → ignored, `schema check needs its settings on origin/<production>`; a host outside the development hosts, or unparsable → refused naming only environments; an export directory outside `export_paths` (or escaping by symlink) → refused; a resolver id not in the plugin list → refused; the resolver runs as an argv list (a stub CLI in the test); an unset variable → `connection reference not set: env:NAME`; the resolved value never appears in any output or the audit log  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sampler.py' -v` passes

### E1.F5.T5 [Backend] Value-free model: per path declared type, observed types with counts, missing-required and undeclared counts; only schema-declared or identifier-shaped segments printed, everything else `{key}`; leak check over the output, refusal prints only container and rule — _Depends: E1.F5.T2_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/sampler/__init__.py`; `plugins/karvey/tests/unit/test_sampler.py` (model section)  
**Requirements:** REQ-LD-037  
**Tests added:** a map keyed by customer ids → `/balances/{key}/amount: number (100)`; a map of only three id-like keys → masked too; an e-mail used as a key → masked and counted; an undeclared `closedAt` → printed and counted as undeclared; a fixture value planted in a field name that is not personal data → refusal, nothing else printed; no fixture value appears in any output  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sampler.py' -v` passes

### E1.F5.T6 [Backend] Drift report with a proposal (update the sheet / open a finding), exit 1, sheet and data untouched; no adapter for the family → exit 4, nothing read; manual `sampler-dev-store.md` — _Depends: E1.F5.T3, E1.F5.T4, E1.F5.T5_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/sampler/__init__.py`; `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/tests/unit/test_sampler.py` (drift section); `plugins/karvey/tests/manual/sampler-dev-store.md` (NEW, `manual:` needs a real development export)  
**Requirements:** REQ-LD-038  
**Tests added:** 12 of 100 without `closedAt` → `/closedAt required: missing in 12/100`, exit 1, sheet bytes unchanged; family `graph` → `no adapter for engine family graph`, exit 4, adapter never opened  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_sampler.py' -v` passes

### E1.F5.T7 [Backend] `karvey_lib/relational.py`: `.sql` DDL (CREATE / ALTER ADD / DROP COLUMN / DROP TABLE, file-name order) vs the sheet's tables and columns; `components --check --relational` — _Depends: E1.F3.T3_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/relational.py` (NEW); `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/tests/unit/test_relational.py` (NEW); `plugins/karvey/tests/unit/fixtures/relational/` (NEW)  
**Requirements:** REQ-LD-061  
**Tests added:** sheet `orders(id, status, closed_at)` = migration → no difference; a migration adding `orders.refund_id` → `orders.refund_id: in the schema files, not in the sheet`; no `.sql` → `relational check: no readable schema files`; comments and strings ignored  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_relational.py' -v` passes

## Feature E1.F6: Bootstrap for existing repositories: scanners, proposal, draft sheets, leak check, review, safe re-run

Architecture §1.15.  
Requirements covered: 039..043  
Total estimated time: 62 min (5 tasks)

### E1.F6.T1 [Backend] `karvey_lib/codescan.py`: read-only bounded scanners (IaC, migrations, manifests, routes, environment reads, frontend route tables), each hit with `file:line`; fixture repository — _Depends: E1.F9.T1_ (P)

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/codescan.py` (NEW); `plugins/karvey/tests/unit/test_bootstrap.py` (NEW, scanner section); `plugins/karvey/tests/fixtures/bootstrap-repo/` (NEW, fictional service, migrations folder, IaC file, frontend routes)  
**Requirements:** REQ-LD-039  
**Tests added:** the fixture yields the service, the migrations and the IaC resource, and `ORDERS_TIMEOUT_MS` at its line; `.git` and vendored dirs skipped; the 5,000-file cap reported  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_bootstrap.py' -v` passes

### E1.F6.T2 [Backend] `bootstrap.propose` (pure): map + draft sheets from the templates, `source: file:line`, `unknown — to fill`, setting names without values, draft schemas from typed models — _Depends: E1.F6.T1, E1.F3.T2_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/bootstrap.py` (NEW); `plugins/karvey/tests/unit/test_bootstrap.py` (proposal section)  
**Requirements:** REQ-LD-039, REQ-LD-040  
**Tests added:** three components of the right kinds; the service sheet lists `ORDERS_TIMEOUT_MS` with its source line and no value; nothing recognised → `no component recognised — declare them by hand`; `propose` performs no write (AST check as in L-38)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_bootstrap.py' -v` passes

### E1.F6.T3 [Backend] `components --bootstrap [--dry-run]`: proposal shown first; refused on integration or production naming `docs/<id>`; leak check over every file, all-or-nothing — _Depends: E1.F6.T2, E1.F3.T5_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/tests/unit/test_bootstrap.py` (CLI section)  
**Requirements:** REQ-LD-040, REQ-LD-041  
**Tests added:** on `main` → refused naming the docs branch; a literal token in `config/app.yaml` → nothing written, `service-a.md: secret pattern (source config/app.yaml:7)`; clean fixture → files written, `--dry-run` writes nothing  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_bootstrap.py' -v` passes

### E1.F6.T4 [Backend] `karvey-docs.py review <id>` with the review marker (draft → reviewed, `review` block, protected review log); a hand-set `reviewed` without the block is reported and treated as draft; dashboard lists draft sheets — _Depends: E1.F6.T3, E1.F1.T10_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/scripts/karvey-context.py` (`open_work`); `plugins/karvey/tests/unit/test_bootstrap.py` (review section)  
**Requirements:** REQ-LD-042  
**Tests added:** with the marker → `status: reviewed` + `review: {at, marker}` + a review-log line; `status: reviewed` typed by hand → `review not recorded by the command`; without → `review needs the owner's own message (D-01)`; the marker is single-use; the dashboard shows `2 draft sheet(s)`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_bootstrap.py' -v` passes

### E1.F6.T5 [Backend] Re-run safety: reviewed sheets never overwritten (additions as a unified diff), drafts regenerated, unparsable front matter kept — _Depends: E1.F6.T3_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/bootstrap.py`; `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/tests/unit/test_bootstrap.py` (re-run section)  
**Requirements:** REQ-LD-043  
**Tests added:** one reviewed + one draft → draft refreshed, reviewed unchanged with a diff printed; broken front matter → `orders-api.md: front matter unreadable — kept`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_bootstrap.py' -v` passes

## Feature E1.F7: README kept current: sections, trigger, undocumented settings, bootstrap / update, every repository

Architecture §1.16.  
Requirements covered: 044..048  
Total estimated time: 57 min (5 tasks)

### E1.F7.T1 [Backend] `schemas/readme-sections.json` (six sections, aliases in five languages, section marker, trigger patterns) + `karvey_lib/readme.py` section check + `readme --check` — _Depends: E1.F3.T5_

**Estimate:** 12 min  
**Files:** `plugins/karvey/schemas/readme-sections.json` (NEW); `plugins/karvey/scripts/karvey_lib/readme.py` (NEW); `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/tests/unit/test_readme.py` (NEW)  
**Requirements:** REQ-LD-044  
**Tests added:** English and Spanish headings pass; a `<!-- karvey:section configuration -->` marker counts; no configuration section → `README: configuration section missing`; `readme.check` absent → silent  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_readme.py' -v` passes

### E1.F7.T2 [Backend] Trigger check over a change range per repository: setup file, command definition, newly read environment variable, map change — without that repository's README — _Depends: E1.F7.T1, E1.F6.T1_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/readme.py`; `plugins/karvey/tests/unit/test_readme.py` (trigger section)  
**Requirements:** REQ-LD-045  
**Tests added:** dependency added, README untouched → `README not updated: setup file package manifest changed`; `ORDERS_TIMEOUT_MS` added and listed → nothing; overridden trigger patterns honoured  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_readme.py' -v` passes

### E1.F7.T3 [Backend] Undocumented settings: names read in code that are in neither the README configuration section nor a sheet of that repository — _Depends: E1.F7.T1, E1.F6.T1_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/readme.py`; `plugins/karvey/tests/unit/test_readme.py` (settings section)  
**Requirements:** REQ-LD-046  
**Tests added:** `ORDERS_RETRY` read at `services/orders/config.py:12` and documented nowhere → `undocumented setting ORDERS_RETRY (services/orders/config.py:12)`; documented in a sheet → clean  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_readme.py' -v` passes

### E1.F7.T4 [Backend] `readme --bootstrap|--update`: missing sections as generated blocks with a content hash; update refreshes only the components list and settings table; hand-edited block reported, not overwritten; leak check; docs branch — _Depends: E1.F7.T1_

**Estimate:** 15 min  
**Files:** `plugins/karvey/scripts/karvey_lib/readme.py`; `plugins/karvey/scripts/karvey-docs.py`; `plugins/karvey/tests/unit/test_readme.py` (blocks section)  
**Requirements:** REQ-LD-047  
**Tests added:** a purpose-only README → five blocks added, purpose paragraph byte-identical; an edited block → `generated block edited by hand: configuration — …`; a secret in a generated value → nothing written  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_readme.py' -v` passes

### E1.F7.T5 [Backend] Every repository: `readme --check` per reachable repository in `project.json:repos`; the QA skill's summary prints one line per repository — _Depends: E1.F7.T2_

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey_lib/readme.py`; `plugins/karvey/skills/karvey-qa/SKILL.md`; `plugins/karvey/tests/unit/test_readme.py` (multi-repo section)  
**Requirements:** REQ-LD-048  
**Tests added:** two repositories → two lines; an unreachable one → `README: not checked (repository not reachable)`  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_readme.py' -v` passes

## Feature E1.F8: Integration: check modes 4.2, upgrade steps LD-1..LD-3, lanes, rules and load lists, core contract, compatibility, documentation, size gate

Architecture §1.17–§1.20, §7.3, §8.  
Requirements covered: 049..055  
Total estimated time: 109 min (10 tasks)

### E1.F8.T1 [Backend] `check-modes.json`: `"4.2"` default in every row + the 19 rows of architecture §1.17 (three instruction checks `enabled_when` capture on; three secret checks blocking); `modes.release_line` maps 4.2.x; L-76 (scheduled first) — _Depends: E1.F9.T1_ (P)

**Estimate:** 10 min  
**Files:** `plugins/karvey/schemas/check-modes.json`; `plugins/karvey/scripts/karvey_lib/modes.py`; `plugins/karvey/scripts/lint-plugin.py` (L-76); `plugins/karvey/tests/unit/test_modes.py` (cases); `plugins/karvey/tests/unit/test_lint_ld.py` (NEW)  
**Requirements:** REQ-LD-053  
**Tests added:** each new id resolves to its 4.2 default; the instruction checks resolve `off` with capture off; a code-used id missing from the registry → L-76 error naming it  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_modes.py' -v` and `-p 'test_lint_ld.py'` pass; `python3 plugins/karvey/scripts/lint-plugin.py --only L-76` exits 0

### E1.F8.T2 [Backend] Upgrade step `ld-1-capture` (LD-1): read-only check, no fix (`human: true`), prints the one-line diff and why; idempotent — _Depends: E1.F1.T8_

**Estimate:** 10 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade-steps.json`; `plugins/karvey/scripts/karvey_lib/upgrade_steps.py`; `plugins/karvey/tests/unit/test_upgrade_ld.py` (NEW)  
**Requirements:** REQ-LD-049  
**Tests added:** a 4.1 fixture lists LD-1 with its seven fields; capture already on → not listed; L-38 accepts the row (`human ⇒ fix null`)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_ld.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-38` exits 0

- The engine is in the base by E1.F9.T1 (architecture §7.3: no hand-off fallback).

### E1.F8.T3 [Backend] Upgrade steps `ld-2-components` (bootstrap proposal as planned edits, dry-run) and `ld-3-readme` (missing sections + `readme.check: on`, dry-run); idempotent; upgrade branch only — _Depends: E1.F8.T2, E1.F6.T2, E1.F7.T4_

**Estimate:** 12 min  
**Files:** `plugins/karvey/scripts/karvey_lib/upgrade-steps.json`; `plugins/karvey/scripts/karvey_lib/upgrade_steps.py`; `plugins/karvey/tests/unit/test_upgrade_ld.py`  
**Requirements:** REQ-LD-049  
**Tests added:** dry-run of LD-2/LD-3 writes nothing; apply twice → `nothing to do`; a project with a complete map does not list LD-2; the fix functions pass L-38's no-write scan  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_upgrade_ld.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py --only L-38` exits 0

### E1.F8.T4 [Backend] Lanes and gates: one sentence in `rules/lanes.md`; tests that the blockers apply at every lane's human gates and that the `docs` lane runs sections and README on its own documents — _Depends: E1.F2.T4, E1.F4.T5, E1.F7.T1_

**Estimate:** 10 min  
**Files:** `plugins/karvey/skills/karvey/rules/lanes.md`; `plugins/karvey/tests/unit/test_instructions_state.py` (lane matrix); `plugins/karvey/tests/unit/test_sheetcheck.py` (docs lane)  
**Requirements:** REQ-LD-050  
**Tests added:** a `patch` change's prod gate refused while a row is unclassified, QA-lite lists the sheet check; a `docs` change breaking a sheet section → reported  
**Done when:** both suites pass and `python3 plugins/karvey/scripts/lint-plugin.py` 0 errors

### E1.F8.T5 [Backend] Rules `instructions.md` (in no `Load:` list; a footnote of the core contract), `components.md`, `readme.md` (≤ 700 words each) + `schemas/rule-loaders.json` + `Load:` entries of the acting skills + L-77; findings header aligned in `iteration-loop.md`; `karvey-iterate` names `instruction classify` without loading the rule — _Depends: E1.F2.T4, E1.F4.T7, E1.F5.T6, E1.F6.T5, E1.F7.T5_

**Estimate:** 15 min  
**Files:** `plugins/karvey/skills/karvey/rules/{instructions,components,readme}.md` (NEW); `plugins/karvey/schemas/rule-loaders.json` (NEW); `plugins/karvey/skills/karvey-{architecture,tasks,impl,qa,archive,docs}/SKILL.md` (`Load:`); `plugins/karvey/skills/karvey-iterate/SKILL.md` (text); `plugins/karvey/skills/karvey/rules/iteration-loop.md`; `plugins/karvey/scripts/lint-plugin.py` (L-77)  
**Requirements:** REQ-LD-051  
**Tests added:** `karvey-mockup` naming `components.md`, or any skill naming `instructions.md`, in its `Load:` → L-77 error; each rule ≤ 700 words; the Wave 3 load-list lints (L-56, L-61, L-62) stay green  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-77` exits 0 and `python3 plugins/karvey/scripts/lint-plugin.py` 0 errors

### E1.F8.T6 [Backend] Core contract `instruction` in `rules/_core.md` + its row in `schemas/contracts.json` (enforcement: the state tool's blockers); the core stays ≤ 1,000 words — _Depends: E1.F8.T5_

**Estimate:** 8 min  
**Files:** `plugins/karvey/skills/karvey/rules/_core.md`; `plugins/karvey/schemas/contracts.json`; `plugins/karvey/tests/unit/test_contracts.py` (case)  
**Requirements:** REQ-LD-052, REQ-W3-003 (MODIFIED by this change)  
**Tests added:** every phase skill reaches the contract through the core; over the limit → L-55 fails with the word count (the text is shortened, never the limit)  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_contracts.py' -v` passes, `python3 plugins/karvey/scripts/lint-plugin.py --only L-55` exits 0 and `python3 plugins/karvey/scripts/karvey-context-budget.py contracts` exits 0

### E1.F8.T7 [Backend] Skill text: `karvey-init` settings reference asks `instructions.capture` and `readme.check` (`on` recommended); `karvey-docs` gains the `components` and `readme` modes, bootstrap and review phrase — _Depends: E1.F8.T5_

**Estimate:** 12 min  
**Files:** `plugins/karvey/skills/karvey-init/` (its settings reference after Wave 3); `plugins/karvey/skills/karvey-docs/SKILL.md`  
**Requirements:** REQ-LD-055, REQ-LD-011, REQ-LD-044  
**Tests added:** none new (text); the linter and the size compare cover it  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` 0 errors and `python3 plugins/karvey/scripts/karvey-context-budget.py compare docs/spec/retros/context-size-4.2.0-base.json --live --warn-growth 10` prints no phase above 10%

- **Split:** The init question of REQ-LD-011 and REQ-LD-044 is text in the same file as the docs skill's modes (REQ-LD-055).

### E1.F8.T8 [Backend] Documentation: README sections "Captured instructions", "Component sheets", "README kept current" (setting, commands, LD step each) + `hooks/README.md` (guard, JSON output, failure notice) + L-78 (also: the init settings text asks both settings with `on` recommended) — _Depends: E1.F8.T7, E1.F8.T3_

**Estimate:** 12 min  
**Files:** `README.md`; `plugins/karvey/hooks/README.md`; `plugins/karvey/scripts/lint-plugin.py` (L-78); `plugins/karvey/tests/unit/test_lint_ld.py`  
**Requirements:** REQ-LD-055, REQ-LD-011, REQ-LD-044  
**Tests added:** removing `LD-2` from the README → L-78 error; an init settings text without `readme.check`, or without `on` recommended → L-78 error; the neutrality checks (L-66, L-72, `test_fixtures_anonymous.py`) pass over every new file  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py --only L-78` exits 0, `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_fixtures_anonymous.py' -v` passes and `python3 plugins/karvey/scripts/lint-plugin.py` 0 errors

### E1.F8.T9 [Test] Compatibility 4.1 → 4.2: `test_compat_ld.py` replays the 4.1 fixtures (no map, capture off, README check off) — `validate --strict`, the linter over a fixture project, guard tables, gates unchanged; an old change is not refused after capture turns on — _Depends: E1.F8.T1, E1.F8.T5, E1.F2.T4_

**Estimate:** 12 min  
**Files:** `plugins/karvey/tests/unit/test_compat_ld.py` (NEW); `plugins/karvey/tests/hooks/tables/compat.json` (cases)  
**Requirements:** REQ-LD-054  
**Tests added:** every 4.1 fixture result byte-identical under 4.2 defaults; turning capture on leaves a change without rows approvable  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_compat_ld.py' -v` passes and `python3 plugins/karvey/tests/hooks/run_tables.py --only compat` passes

### E1.F8.T10 [Backend] Size tool: `compare … --fail-growth PCT` (exit 1 naming each phase above PCT); CI keeps `--warn-growth` — _Depends: E1.F9.T2_ (P)

**Estimate:** 8 min  
**Files:** `plugins/karvey/scripts/karvey-context-budget.py`; `plugins/karvey/tests/unit/test_context_budget.py` (cases)  
**Requirements:** REQ-LD-051  
**Tests added:** a fixture pair with one phase +15% under `--fail-growth 10` → exit 1 naming it; +8% → exit 0  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_context_budget.py' -v` passes

## Feature E1.F9: Change-scoped: base after Wave 3 and size base (first); dogfooding on this repository (last)

Architecture §7.1, §1.18 (size), §13.  
Requirements covered: 056, 057  
Total estimated time: 88 min (10 tasks, 1 `[human]`)

### E1.F9.T1 [Test] Base check: `wave3-optimization`'s implementation and the project-upgrade engine are in this branch's base (Wave 3's last task's commit is an ancestor; `rules/_core.md`, `schemas/contracts.json`, the `Load:` lines, `karvey_lib/upgrade.py` and `upgrade-steps.json` exist); rebase; re-verify the architecture §13 list

**Estimate:** 6 min  
**Files:** `plugins/karvey/tests/unit/test_base_wave3.py` (NEW, change-scoped); `docs/spec/changes/living-docs/PLAN.md` (history line with the base commit)  
**Requirements:** REQ-LD-057  
**Tests added:** `test_REQ_LD_057_base_holds_wave3`: fails naming the missing file or commit while Wave 3 is not merged  
**Done when:** `python3 -m unittest discover -s plugins/karvey/tests/unit -p 'test_base_wave3.py' -v` passes; `git merge-base --is-ancestor <wave3 last task commit> HEAD` exits 0

- If it fails, impl waits: no other task starts (REQ-LD-057). The §13 table is walked and each moved line number noted in the PLAN history, not in the architecture.

### E1.F9.T2 [Backend] Size base snapshot `docs/spec/retros/context-size-4.2.0-base.json` in a commit of its own, before any rule or skill edit of this change — _Depends: E1.F9.T1_

**Estimate:** 6 min  
**Files:** `docs/spec/retros/context-size-4.2.0-base.json` (NEW, from `karvey-context-budget.py measure --label 4.2.0-base --json`)  
**Requirements:** REQ-LD-051  
**Tests added:** none new (the Wave 3 `order` check proves the snapshot precedes the edits: `karvey-context-budget.py order`)  
**Done when:** the file exists, re-running `measure` gives the same bytes (`cmp`), and `python3 plugins/karvey/scripts/karvey-context-budget.py order --json` names no later-edited skill

- **Split:** REQ-LD-051 sits in F8; its base snapshot must precede every edit, so it runs here (the plan's one ordering split).

### E1.F9.T3 [Backend] Capture on for this repository: `instructions.capture: on` in `docs/spec/project.json` (the working copy turns it on at once); PLAN history notes that earlier impl commits predate the guard — _Depends: E1.F1.T9_

**Estimate:** 4 min  
**Files:** `docs/spec/project.json`; `docs/spec/changes/living-docs/PLAN.md` (history)  
**Requirements:** REQ-LD-056  
**Tests added:** none new; the session hook prints `instruction capture on`  
**Done when:** `python3 plugins/karvey/scripts/karvey-state.py validate --all` exits 0 and a session start in this repo prints `instruction capture on`

### E1.F9.T4 [Backend] This repository's map (the eight components of the architecture's Component delta) + draft sheets from the bootstrap on a docs branch — _Depends: E1.F6.T3, E1.F9.T3_

**Estimate:** 12 min  
**Files:** `docs/spec/project.json` (`components`); `docs/spec/components/{hooks,state-tool,docs-tool,method-scripts,method-text,spec-store,method-page,ci}.md` (NEW, draft)  
**Requirements:** REQ-LD-056  
**Tests added:** none new  
**Done when:** `python3 plugins/karvey/scripts/karvey-docs.py components --check --sections --leak --json` lists the eight components with no leak hit

### E1.F9.T5 [Backend] Fill the sheets `hooks`, `state-tool`, `docs-tool`, `method-scripts` (operations, settings names, errors, idempotency, observability) — _Depends: E1.F9.T4_

**Estimate:** 15 min  
**Files:** `docs/spec/components/{hooks,state-tool,docs-tool,method-scripts}.md`  
**Requirements:** REQ-LD-056  
**Tests added:** none new  
**Done when:** `python3 plugins/karvey/scripts/karvey-docs.py components --check --sections --json` reports no missing section for the four

### E1.F9.T6 [Backend] Fill the sheets `method-text`, `spec-store` (containers with schema and a fictional example that validates), `method-page`, `ci` (runbook) — _Depends: E1.F9.T4_ (P)

**Estimate:** 15 min  
**Files:** `docs/spec/components/{method-text,spec-store,method-page,ci}.md`  
**Requirements:** REQ-LD-056  
**Tests added:** none new  
**Done when:** `python3 plugins/karvey/scripts/karvey-docs.py components --check --sections --json` reports no missing section and no example failure for the four

### E1.F9.T7 [human] The owner reviews the eight sheets of this repository (REQ-LD-042: only the owner's own message turns a sheet `reviewed`) — _Depends: E1.F9.T5, E1.F9.T6_

**Executor:** the owner (the person with `role: human` for this change) — an agent cannot, by REQ-LD-042  
**Command:** read each of `docs/spec/components/{hooks,state-tool,docs-tool,method-scripts,method-text,spec-store,method-page,ci}.md`; for each one you accept, type in the session `reviewed sheet <component-id>`; the agent then runs `python3 plugins/karvey/scripts/karvey-docs.py review <component-id>` once per sheet. For a sheet you do not accept, say what to change instead (it stays `draft`).  
**Verification:** `grep -l '^status: reviewed' docs/spec/components/*.md | wc -l` → 8  
**Rollback:** a sheet can go back to `draft` by an ordinary edit in a later commit; the review markers are single-use and expire  
**Requirements:** REQ-LD-056, REQ-LD-042  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

### E1.F9.T8 [Backend] This repository's README to the six sections (`readme --bootstrap`, generated blocks for components and settings) + `readme.check: on` — _Depends: E1.F7.T4, E1.F8.T8, E1.F9.T4_

**Estimate:** 10 min  
**Files:** `README.md`; `docs/spec/project.json` (`readme`)  
**Requirements:** REQ-LD-056  
**Tests added:** none new  
**Done when:** `python3 plugins/karvey/scripts/karvey-docs.py readme --check --json` reports no missing section

### E1.F9.T9 [Test] Whole-repo gate: lint 0, every unit and regression suite, every table, `validate --all`, `karvey-trace.py living-docs --check` 63/63, `compare … --fail-growth 10`, `components --check` (sections, commits of the change range, leak) and `readme --check` green on this repository — _Depends: E1.F9.T7, E1.F9.T8, E1.F8.T9, E1.F8.T10, E1.F8.T6, E1.F1.T14, E1.F2.T5, E1.F2.T6, E1.F4.T2, E1.F4.T8, E1.F5.T1, E1.F5.T7, E1.F6.T4, E1.F7.T3_

**Estimate:** 12 min  
**Files:** none (runs the suites); `docs/spec/changes/living-docs/PLAN.md` (history line with the results)  
**Requirements:** REQ-LD-056, REQ-LD-051  
**Tests added:** none new (runs every suite)  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` 0 errors; `python3 -m unittest discover -s plugins/karvey/tests/unit` and `-s plugins/karvey/tests/regression` pass; `python3 plugins/karvey/tests/hooks/run_tables.py` passes; `python3 plugins/karvey/scripts/karvey-trace.py living-docs --check` exits 0; `python3 plugins/karvey/scripts/karvey-context-budget.py compare docs/spec/retros/context-size-4.2.0-base.json --live --fail-growth 10` exits 0

### E1.F9.T10 [Backend] Release docs: `[Unreleased]` summary (three parts, settings, LD-1..LD-3 in the manual Upgrade list, size before/after against the base snapshot); no version or date — _Depends: E1.F9.T9_

**Estimate:** 8 min  
**Files:** `CHANGELOG.md` (`[Unreleased]` only)  
**Requirements:** REQ-LD-055  
**Tests added:** none new  
**Done when:** `python3 plugins/karvey/scripts/lint-plugin.py` 0 errors (changelog checks)

## Epic item E1.DEPLOY

### E1.DEPLOY.T1 [human] The prod OK for the release that ships this change (D-10) — _Depends: E1.F9.T10_

**Executor:** the owner — never delegated (D-10)  
**Command:** inside `karvey-deploy`, after reading the release PR (its manifest lists every change and commit), type your own words with an approval **and** a production term, and answer the structured question that records the D-NN  
**Verification:** `python3 plugins/karvey/scripts/karvey-state.py check-prod living-docs --json` → `ok: true` after `approve prod`  
**Rollback:** before the merge: nothing, the marker expires; after it: a revert PR, as a new change through the method  
**Executed:** (filled when done: name · YYYY-MM-DD HH:MM · evidence)

## Traceability matrix (REQ-LD → tasks)

| REQ-LD | Tasks |
|---|---|
| 001 | E1.F1.T5, E1.F1.T8, E1.F1.T14 |
| 002 | E1.F1.T3 |
| 003 | E1.F1.T1 |
| 004 | E1.F1.T2 |
| 005 | E1.F1.T3, E1.F1.T14 |
| 006 | E1.F1.T4, E1.F1.T14 |
| 007 | E1.F1.T4 |
| 008 | E1.F1.T5, E1.F1.T6 |
| 009 | E1.F1.T8, E1.F1.T12, E1.F2.T6 |
| 010 | E1.F1.T8, E1.F1.T9, E1.F1.T14, E1.F2.T5 |
| 011 | E1.F1.T8, E1.F1.T14, E1.F8.T7, E1.F8.T8 |
| 012 | E1.F1.T13 |
| 013 | E1.F2.T1 |
| 014 | E1.F2.T2 |
| 015 | E1.F2.T1, E1.F2.T3 |
| 016 | E1.F2.T4 |
| 017 | E1.F2.T5 |
| 018 | E1.F2.T6 |
| 019 | E1.F3.T1 |
| 020 | E1.F3.T2 |
| 021 | E1.F3.T2, E1.F3.T4 |
| 022 | E1.F3.T2 |
| 023 | E1.F3.T3 |
| 024 | E1.F3.T5 |
| 025 | E1.F3.T4 |
| 026 | E1.F4.T1 |
| 027 | E1.F4.T2 |
| 028 | E1.F4.T3, E1.F4.T4, E1.F4.T5 |
| 029 | E1.F4.T6 |
| 030 | E1.F4.T6 |
| 031 | E1.F4.T8 |
| 032 | E1.F4.T5 |
| 033 | E1.F5.T1 |
| 034 | E1.F5.T2, E1.F5.T3 |
| 035 | E1.F5.T4 |
| 036 | E1.F5.T2 |
| 037 | E1.F5.T5 |
| 038 | E1.F5.T6 |
| 039 | E1.F6.T1, E1.F6.T2 |
| 040 | E1.F6.T2, E1.F6.T3 |
| 041 | E1.F6.T3 |
| 042 | E1.F6.T4, E1.F9.T7 |
| 043 | E1.F6.T5 |
| 044 | E1.F7.T1, E1.F8.T7, E1.F8.T8 |
| 045 | E1.F7.T2 |
| 046 | E1.F7.T3 |
| 047 | E1.F7.T4 |
| 048 | E1.F7.T5 |
| 049 | E1.F8.T2, E1.F8.T3 |
| 050 | E1.F8.T4 |
| 051 | E1.F8.T5, E1.F8.T10, E1.F9.T2, E1.F9.T9 |
| 052 | E1.F8.T6 |
| 053 | E1.F8.T1 |
| 054 | E1.F8.T9 |
| 055 | E1.F8.T7, E1.F8.T8, E1.F9.T10 |
| 056 | E1.F9.T3, E1.F9.T4, E1.F9.T5, E1.F9.T6, E1.F9.T7, E1.F9.T8, E1.F9.T9 |
| 057 | E1.F9.T1 |
| 058 | E1.F1.T3, E1.F1.T9, E1.F1.T14 |
| 059 | E1.F1.T7, E1.F1.T11 |
| 060 | E1.F1.T11, E1.F1.T12 |
| 061 | E1.F5.T7 |
| 062 | E1.F4.T7 |
| 063 | E1.F1.T10 |

MODIFIED living requirements: **REQ-W2-023** (closed judge inputs) → E1.F4.T8 (with REQ-LD-031); **REQ-W3-003** (the core of hard contracts) → E1.F8.T6 (with REQ-LD-052). `karvey-trace.py living-docs` counts 65 requirements: 63 REQ-LD + these two.

**Coverage:** 63/63. No REQ-LD is left without a task. Every component of the architecture's file plan (§1.2) has a task: `karvey-docs.py`; the new `karvey_lib` modules `instructions`, `redact`, `components`, `sheetcheck`, `relational`, `codescan`, `bootstrap`, `readme` and the `sampler` package with its two adapters and `resolvers.json`; `component-kinds.json`, `readme-sections.json`, `rule-loaders.json`; the vocabulary, leak-pattern and check-mode rows; both schemas; the four templates; `karvey-state.py` (`instruction …`, blockers, validate, delta warning), `karvey-context.py` (gate summary, dashboard), `karvey_hooks.py` / `guards.py` / `karvey-hook.sh` (guard, JSON output, session lines, needle), `judges.py` (inputs, lock), `karvey-context-budget.py` (`--fail-growth`), `lint-plugin.py` (L-76..L-81), `lint.yml`, the upgrade catalogue rows, the three rules, the core contract, the §8 skill texts, the READMEs, and the dogfooding artifacts (§7.1, the Component delta).

## Totals and critical path

- **Tasks:** 71, of which 2 `[human]` and 69 agent tasks (64 Backend, 5 Test).
- **Total estimate:** 794 min ≈ 13.2 h of AI + review, calibrated. Per feature: F1 166 · F2 65 · F3 64 · F4 91 · F5 92 · F6 62 · F7 57 · F8 109 · F9 88.
- **Critical path by dependencies:** 169 min ≈ 2.8 h:
  E1.F9.T1 → E1.F3.T1 → E1.F3.T2 → E1.F3.T3 → E1.F3.T5 → E1.F5.T2 → E1.F5.T4 → E1.F5.T6 → E1.F8.T5 → E1.F8.T7 → E1.F8.T8 → E1.F9.T8 → E1.F9.T9 → E1.F9.T10 → [E1.DEPLOY.T1 human].
  The `[human]` waits (the sheet review, the prod OK) and CI queue time are not counted.
- **Serial file spines** (not dependencies, but they serialise work): `karvey-state.py` (7 tasks), `karvey-docs.py` (13), `instructions.py` (13), `components.py` (8), `lint-plugin.py` (6). With one agent the realistic wall time is the total; with parallel agents the floor is the critical path plus the `karvey-docs.py` spine.

## What proved impractical when breaking the architecture into tasks

1. **Nothing starts before Wave 3.** E1.F9.T1 is a hard gate (REQ-LD-057): every task edits files Wave 3's F2 is still reorganising (core, load lists, skill text). The plan cannot be parallelised with Wave 3; it can only be made ready.
2. **The size base belongs to F8 but must run first.** REQ-LD-051's snapshot is taken in F9 (E1.F9.T2) before any edit; its `Split:` line says so. Measuring after the first rule edit would hide this change's own growth.
3. **Dogfooding cannot capture the first commits.** Capture exists only after E1.F1.T9; E1.F9.T3 turns it on then, and the PLAN history says that earlier impl commits predate the guard (architecture A-14).
4. **Sheets are not paired before the map exists.** REQ-LD-027's `Sheet:` line applies from E1.F9.T4 on; before it, this repository has no component map, so no task can name a sheet. The whole-repo gate (E1.F9.T9) runs the pairing over the change range with the map in place and reports the earlier commits, which carry no sheet by construction.
5. **The owner's review is the one agent-proof step inside the plan.** REQ-LD-042 makes `reviewed` reachable only from the owner's own words; E1.F9.T7 is `[human]` and the whole-repo gate waits for it.
6. **The detector's quality is measured, not designed.** E1.F1.T3 may need a second pass on the vocabulary if the labelled table (E1.F1.T2) shows recall below 0.90 in one language; the estimate assumes one pass, and a miss is iterated as a finding, not by lowering the threshold.
7. **Two spines serialise most of F3–F7.** `karvey-docs.py` and `components.py` are touched by most tasks of those features; their (P) marks are true by dependency but not in practice for one agent.

---
*Generated by `karvey-tasks` (PHASE 7) on 2026-09-26 for `living-docs`. Not approved by this document.*
