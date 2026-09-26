# Plan: living-docs

**Capability:** method | **Security Tier:** 3 | **Layers:** Backend
**Created:** 2026-09-26 | **Status:** 🔄 tasks (merged *how* gate pending)
**Lane:** standard (no UI: sheets and READMEs are documents; mockup and design-graphic skipped by the lane)
**Release target:** 4.2.0 (minor, backward compatible with 4.1.0)
**Flow:** trunk (`feature/living-docs` → PR → `main`) · **Decision:** D-38 (D-01, D-20, D-21, D-24, D-30 hold)
**Sequencing:** spec phases now; implementation after `wave3-optimization`'s implementation (REQ-LD-057)

---

## Epic: Living documentation — captured instructions, component sheets, current READMEs

### Description
While a change is in flight the owner's instructions stay in the conversation and never reach the specs; the
project has no technical sheet per component (data shapes of a document store, service contracts, frontend
routes and permissions, infrastructure runbooks), so agents learn them from code or from failures; READMEs drift.
This Epic captures the owner's instructions through the prompt hook and gates every phase on their
classification, adds living component sheets mapped to code paths with a read-only schema check for document
stores, keeps each repository's README to a minimal section set, and brings all three to existing projects through
the upgrade plan.

North star: *no instruction the owner gives during an active change is lost — each is captured verbatim by the hook
and classified before its gate closes — and every component and repository of a project has a technical sheet and
a README that change in the same change as the code they describe.*

### Strategic value
Instructions repeated or lost between sessions cost the owner's time and produce specs that diverge from what was
asked; undocumented data shapes cause production failures; a repository nobody can start from its README costs
every newcomer. Documentation checked at the moment the code or the conversation changes stays true without a
documentation sprint.

### Design decisions
| Topic | Decision |
|------|----------|
| Scope | D-38 — instruction capture by the hook (agent never writes the rows) + classification gated by the state tool; component sheets per kind with lifecycle like living specs and a read-only NoSQL sampler; README section set; upgrade steps |
| Trust model | D-01 — rows written only by the hook, verified against a store the agent cannot write; review of generated sheets and removal of a row need the owner's own message |
| Architecture | `architecture.md` — capture as a prompt-hook guard with a protected two-phase store and clone-bound row hashes; one `gate_blockers` function in the state tool; `karvey-docs.py` for sheets, schema sampler (read-only, reviewed-line settings, development allow-lists, value-free), bootstrap and README; check modes 4.2; upgrade steps `ld-1-capture`, `ld-2-components`, `ld-3-readme`; architect decisions A-01..A-22 for the owner to confirm at the *how* gate; infra skipped (no cloud) |

---

## Features

| Feature | Area | Requirements covered | Status |
|---------|------|----------------------|--------|
| F1 | Instruction capture: detection, multilingual vocabulary, measured detector, off the record, only the human's text, redaction, tamper evidence, project inbox, never blocks, owner's setting, removal on request | REQ-LD-001..012, 058, 059, 060, 063 | ⬜ |
| F2 | Instruction classification: four classes with evidence, revision linkage, state-tool only, phase/gate refusal, gate summary, session/dashboard counts | REQ-LD-013..018 | ⬜ |
| F3 | Component map and sheet templates (data store, backend service, frontend module, infra resource), section check, no secrets, references resolve | REQ-LD-019..025 | ⬜ |
| F4 | Sheet lifecycle: component delta at architecture, tasks pair code and sheet, same-commit check, archive reconciliation, parallel deltas, judges read sheets, lanes without architecture, archive stamps and retires | REQ-LD-026..032, 062 | ⬜ |
| F5 | Document-schema check: example vs schema, read-only adapter, development targets by reference, bounded sample, value-free output, drift reported, relational sheets vs schema files | REQ-LD-033..038, 061 | ⬜ |
| F6 | Bootstrap for existing repositories: proposed map, draft sheets, leak check, human review, safe re-run | REQ-LD-039..043 | ⬜ |
| F7 | README kept current: section set, trigger check, undocumented settings, bootstrap/update, every repository | REQ-LD-044..048 | ⬜ |
| F8 | Integration: upgrade steps LD-1..LD-3, lanes and gates, load lists and size, core contract, check modes, backward compatibility, documentation | REQ-LD-049..055 | ⬜ |
| F9 | Change-scoped: dogfooding on this repository, implementation after Wave 3 | REQ-LD-056, 057 | ⬜ |

## Tasks

Detail per task (files, requirements, tests, done-when command) in `tasks.md`. Estimates are calibrated to realistic AI execution + review (the default scale ran ~10× high in this repo). 71 tasks (69 agent, 2 `[human]`), 794 min total, critical path 169 min. Execution order: E1.F9.T1 (base) → E1.F9.T2 (size base) + E1.F8.T1 → F1 → F2 and F3 → F4..F7 → F8 → F9 dogfooding → E1.DEPLOY.

### Feature E1.F1: Instruction capture: vocabulary, detector, redaction, store and rows, guard, confirm phrases, inbox, removal, tamper refusal

- [ ] E1.F1.T1 [Backend] Vocabulary: `directive`, `question` (per language en, es, pt, de, fr), `markers` (`#off`, `#note`), `confirm` (remove / review verbs and nouns), `rules.capture_*`; override key `enforcement.instruction_vocabulary` read from the reviewed line; L-80 — est: 12min (depends E1.F9.T1) (P)
- [ ] E1.F1.T2 [Test] Labelled detector table `tests/hooks/tables/instructions-detect.json` (≥ 30 prompts per shipped language: questions, approvals, chit-chat, mixed, commands, instructions) + `test_instructions_detect.py` printing recall / precision per language and overall — est: 15min (depends E1.F1.T1)
- [ ] E1.F1.T3 [Backend] `karvey_lib/instructions.py` `detect()`: `#off` → skip, confirm phrase → no capture, `#note` → forced, strip + normalise, command / approval-only / < 4 words → no, directive wins over question, > 40 words → yes — est: 12min (depends E1.F1.T2)
- [ ] E1.F1.T4 [Backend] `karvey_lib/redact.py`: pasted fenced blocks and long lines → markers with counts; 4,000-char cap; `[redacted:secret|email|phone]` (leak `secret` patterns + the new capture-only `capture` group — assignment and `is` forms, Luhn-valid card numbers — e-mail, international phone); `RedactionUnavailable` fails closed — est: 12min (depends E1.F9.T1) (P)
- [ ] E1.F1.T5 [Backend] Capture store `<state>/instructions/<scope>.jsonl` (two-phase `pending` → `written`, sha256, clone id, 0700/0600) + findings lock in `instructions/locks/` (pid, time, stale after 5 s) + row writer (next `F-NN`, header of `judges.py`, escaping incl. comment delimiters, `clone=… sha256=…` comment); `judges collect` takes the same lock — est: 15min (depends E1.F9.T1) (P)
- [ ] E1.F1.T6 [Backend] Protect-paths: needle `karvey/instructions` in `STATE_NEEDLES` and in the no-python `needles=` of `karvey-hook.sh`; guard table cases (Edit, Write, Bash with `$(git rev-parse …)`) — est: 8min (depends E1.F1.T5) (P)
- [ ] E1.F1.T7 [Backend] `instructions.verify(change)`: verified, `not verifiable here` (another clone, own hash matches, listed with its clone id), tampered, missing, extra (incl. a row claiming this clone without an entry), pending-without-row (failure), removed — est: 10min (depends E1.F1.T5)
- [ ] E1.F1.T8 [Backend] Capture guard `instruction_capture` + registry row after `approval`: effective setting (reviewed line; the working copy only turns it on; ignored `off` audited), scope (one active change → row; none/several → inbox `I-N`), 1 s deadline, fail open with `failed` entry, health file, audit records without text — est: 15min (depends E1.F1.T3, E1.F1.T4, E1.F1.T5, E1.F3.T1)
- [ ] E1.F1.T9 [Backend] Prompt-event output where capture is on: `dispatch` prints one JSON object (`systemMessage` + `additionalContext`) with every guard's lines (acknowledgement, not-captured notice, approval line); plain text, byte-identical to 4.1, where capture is off; no-python notice in `karvey-hook.sh` — est: 12min (depends E1.F1.T8)
- [ ] E1.F1.T10 [Backend] Confirm phrases: `classify_confirm` on the stripped text (remove / review, every shipped language) → one-use markers under `approvals/confirm/`; a confirm phrase is never captured — est: 10min (depends E1.F1.T3) (P)
- [ ] E1.F1.T11 [Backend] State tool: `instruction list` + `instructions.gate_blockers` (tamper, inbox hold) wired in `advance`, `approve`, `approve-gate` and `next`; `validate` prints the verification summary; `spec.schema.json:instruction_log[]` — est: 15min (depends E1.F1.T7, E1.F8.T1)
- [ ] E1.F1.T12 [Backend] `instruction assign <I-N> <change>` (row from the stored text, never an argument) and `instruction classify _project <I-N> --as not-instruction --reason` — est: 10min (depends E1.F1.T11)
- [ ] E1.F1.T13 [Backend] `instruction remove <change> <F-NN>` with the removal marker: row and store text → `[removed at the owner's request]`, id / time / class kept, audit record; verify accepts it — est: 8min (depends E1.F1.T10, E1.F1.T11)
- [ ] E1.F1.T14 [Test] Capture end-to-end: `capture.json` full cases (off-the-record keeps no text and no hash, pasted block, redaction, force with capture off, inbox, reviewed vs working copy, deadline, unwritable store, JSON output) + manual `tests/manual/capture-visible.md` — est: 12min (depends E1.F1.T9, E1.F1.T10, E1.F1.T12)

### Feature E1.F2: Instruction classification: four classes, revision linkage, state tool only, gate refusal, gate summary, session and dashboard

- [ ] E1.F2.T1 [Backend] `instruction classify` with the four classes and resolvable evidence (REQ ids in `requirements.md`, F ids in `findings.md`, reasons ≥ 10 chars); rewrites the class cells under the findings lock; appends a `classified` line to the protected store (the authority) and to `instruction_log` (lock + CAS) — est: 15min (depends E1.F1.T11)
- [ ] E1.F2.T2 [Backend] Revision linkage: `requirement-revision` after the first requirements approval needs a `revision_history` entry citing the row id — est: 8min (depends E1.F2.T1)
- [ ] E1.F2.T3 [Backend] Hand-edited class cell (or cell and `instruction_log` edited together) → `classification not recorded by the state tool` against the store's `classified` lines, in `validate` and verify; the row counts as unclassified — est: 8min (depends E1.F2.T1)
- [ ] E1.F2.T4 [Backend] Blockers: unclassified rows captured before the call and an unreadable `findings.md` (capture on) refuse `advance`, `approve` (every phase, `prod` and QA's pass included) and `approve-gate`, in every lane — est: 10min (depends E1.F2.T1)
- [ ] E1.F2.T5 [Backend] Gate summary block "Instructions since the last gate": captured or (re)classified since the previous outcome, `not-instruction` / `no-spec-impact` first with reasons; dismissed inbox entries; capture failures of the change — est: 12min (depends E1.F2.T1, E1.F1.T12)
- [ ] E1.F2.T6 [Backend] Session hook and dashboard: per active change `N instructions unclassified`; `N instruction(s) waiting for a change`; `instruction capture on|off|unavailable`; `instructions: store unreadable` (≤ 4 lines, counts only) — est: 12min (depends E1.F2.T1, E1.F1.T8) (P)

### Feature E1.F3: Component map, sheet templates, section / reference / leak checks, the `karvey-docs.py` CLI

- [ ] E1.F3.T1 [Backend] `project.schema.json`: `instructions`, `components[]` (id, kind, repo, paths, exclude, sheet, sample), `components_settings`, `environments`, `readme`; `validate` refuses unknown kind, duplicate id, sheet outside `docs/spec/components/`, absolute or `..` path, literal connection, undeclared environment — est: 12min (depends E1.F9.T1) (P)
- [ ] E1.F3.T2 [Backend] `schemas/component-kinds.json` (sections, aliases in five languages, reference sections, structural rules) + the four templates under `templates/components/` + L-79 (templates equal the data) — est: 15min (depends E1.F3.T1)
- [ ] E1.F3.T3 [Backend] `karvey_lib/components.py`: map load (globs, `exclude`), sheet parse (front matter, sections by alias, containers), section check (absent / empty, `n/a — reason`, front-matter id vs map, document container without schema) — est: 15min (depends E1.F3.T2)
- [ ] E1.F3.T4 [Backend] Settings tables hold names only (value column reported) and references resolve (`external: {role}` or a map id, `did you mean` by edit distance ≤ 2) — est: 10min (depends E1.F3.T3) (P)
- [ ] E1.F3.T5 [Backend] `karvey-docs.py` CLI (envelope, exit codes) with `components --check [--sections] [--leak]`; leak check over every sheet (sheet:line rule, never the value); CI step in `lint.yml` — est: 12min (depends E1.F3.T3)

### Feature E1.F4: Sheet lifecycle: delta, tasks pairing, commit and change pairing, archive reconcile / stamp / retire, parallel deltas, judges

- [ ] E1.F4.T1 [Backend] Component delta: `components.parse_delta`; `generated architecture` warns when the section is missing (check `components.delta`); `karvey-architecture` template and review gate gain `## Component delta` — est: 12min (depends E1.F3.T3, E1.F8.T1)
- [ ] E1.F4.T2 [Backend] `components --delta-coverage <change>`: each delta item named by a task's `Sheet:` line; `karvey-tasks` gains the `Sheet:` line and runs it in its review gate — est: 10min (depends E1.F4.T1)
- [ ] E1.F4.T3 [Backend] `karvey_lib/sheetcheck.py`: per commit of the range, a mapped path without its sheet is reported unless `Karvey-Sheet-Skip: <id> — <reason>` (listed); `components --check --commits` — est: 15min (depends E1.F3.T5)
- [ ] E1.F4.T4 [Backend] Multi-repository pairing by change: commits selected by `Karvey-Change: <id>` in the component's repository and in the spec repository must both touch it; unreachable repository → `not checked (repository not reachable)` — est: 12min (depends E1.F4.T3)
- [ ] E1.F4.T5 [Backend] Wiring: `karvey-impl` runs the pairing at each task close; `karvey-qa` and QA-lite over the change range (no delta needed in lanes without architecture); blocking by `components_settings.sheet_check: blocking` — est: 10min (depends E1.F4.T4, E1.F8.T1)
- [ ] E1.F4.T6 [Backend] `components --reconcile <change>` (applied / declared but not applied / changed but not declared) and `--parallel <change>`; the architecture gate summary shows parallel deltas — est: 12min (depends E1.F4.T1, E1.F4.T3)
- [ ] E1.F4.T7 [Backend] `--reconcile --apply`: stamp `last_change: <change> (<date>)`, move REMOVED sheets to `archive/` and drop them from the map (kept when paths still match files); `karvey-archive` runs it on its branch — est: 12min (depends E1.F4.T6)
- [ ] E1.F4.T8 [Backend] Judges' closed inputs: architecture adds the delta's sheets, QA the sheets of the components the diff touchesafter the phase's own inputs; `missing sheet: <id>` and budget `dropped:` lines printed and repeated in the gate summary's judges block — est: 8min (depends E1.F4.T1) (P)

### Feature E1.F5: Document-schema check: example vs schema, read-only development-only sampler, value-free output, drift, relational files

- [ ] E1.F5.T1 [Backend] Example vs schema in the section check (`schema_lite`), failing paths listed, unsupported keywords reported `unchecked keyword` — est: 10min (depends E1.F3.T3) (P)
- [ ] E1.F5.T2 [Backend] Sampler core `karvey_lib/sampler/`: adapter contract, allowed-operations proxy, bounds (100 default, ≤ 1,000, 30 s per container), `--dry-run` (operations and containers), `components --check-schema <id>` — est: 15min (depends E1.F3.T5)
- [ ] E1.F5.T3 [Backend] Adapters `fixture` (records calls) and `jsonl_export` (development export directory); AST test over every shipped adapter + L-81 — est: 12min (depends E1.F5.T2)
- [ ] E1.F5.T4 [Backend] Target guard: sampler settings from the reviewed line only; `env:` reference, or `vault:` through a resolver from `sampler/resolvers.json` (argv templates, NAME pattern, no shell); development host and export-path allow-lists; production refusals — est: 15min (depends E1.F5.T2, E1.F3.T1) (P)
- [ ] E1.F5.T5 [Backend] Value-free model: per path declared type, observed types with counts, missing-required and undeclared counts; only schema-declared or identifier-shaped segments printed, everything else `{key}`; leak check over the output, refusal prints only container and rule — est: 15min (depends E1.F5.T2) (P)
- [ ] E1.F5.T6 [Backend] Drift report with a proposal (update the sheet / open a finding), exit 1, sheet and data untouched; no adapter for the family → exit 4, nothing read; manual `sampler-dev-store.md` — est: 10min (depends E1.F5.T3, E1.F5.T4, E1.F5.T5)
- [ ] E1.F5.T7 [Backend] `karvey_lib/relational.py`: `.sql` DDL (CREATE / ALTER ADD / DROP COLUMN / DROP TABLE, file-name order) vs the sheet's tables and columns; `components --check --relational` — est: 15min (depends E1.F3.T3) (P)

### Feature E1.F6: Bootstrap for existing repositories: scanners, proposal, draft sheets, leak check, review, safe re-run

- [ ] E1.F6.T1 [Backend] `karvey_lib/codescan.py`: read-only bounded scanners (IaC, migrations, manifests, routes, environment reads, frontend route tables), each hit with `file:line`; fixture repository — est: 15min (depends E1.F9.T1) (P)
- [ ] E1.F6.T2 [Backend] `bootstrap.propose` (pure): map + draft sheets from the templates, `source: file:line`, `unknown — to fill`, setting names without values, draft schemas from typed models — est: 15min (depends E1.F6.T1, E1.F3.T2)
- [ ] E1.F6.T3 [Backend] `components --bootstrap [--dry-run]`: proposal shown first; refused on integration or production naming `docs/<id>`; leak check over every file, all-or-nothing — est: 10min (depends E1.F6.T2, E1.F3.T5)
- [ ] E1.F6.T4 [Backend] `karvey-docs.py review <id>` with the review marker (draft → reviewed, `review` block, protected review log); a hand-set `reviewed` without the block is reported and treated as draft; dashboard lists draft sheets — est: 12min (depends E1.F6.T3, E1.F1.T10)
- [ ] E1.F6.T5 [Backend] Re-run safety: reviewed sheets never overwritten (additions as a unified diff), drafts regenerated, unparsable front matter kept — est: 10min (depends E1.F6.T3) (P)

### Feature E1.F7: README kept current: sections, trigger, undocumented settings, bootstrap / update, every repository

- [ ] E1.F7.T1 [Backend] `schemas/readme-sections.json` (six sections, aliases in five languages, section marker, trigger patterns) + `karvey_lib/readme.py` section check + `readme --check` — est: 12min (depends E1.F3.T5)
- [ ] E1.F7.T2 [Backend] Trigger check over a change range per repository: setup file, command definition, newly read environment variable, map change — without that repository's README — est: 12min (depends E1.F7.T1, E1.F6.T1)
- [ ] E1.F7.T3 [Backend] Undocumented settings: names read in code that are in neither the README configuration section nor a sheet of that repository — est: 10min (depends E1.F7.T1, E1.F6.T1) (P)
- [ ] E1.F7.T4 [Backend] `readme --bootstrap|--update`: missing sections as generated blocks with a content hash; update refreshes only the components list and settings table; hand-edited block reported, not overwritten; leak check; docs branch — est: 15min (depends E1.F7.T1)
- [ ] E1.F7.T5 [Backend] Every repository: `readme --check` per reachable repository in `project.json:repos`; the QA skill's summary prints one line per repository — est: 8min (depends E1.F7.T2)

### Feature E1.F8: Integration: check modes 4.2, upgrade steps LD-1..LD-3, lanes, rules and load lists, core contract, compatibility, documentation, size gate

- [ ] E1.F8.T1 [Backend] `check-modes.json`: `"4.2"` default in every row + the 19 rows of architecture §1.17 (three instruction checks `enabled_when` capture on; three secret checks blocking); `modes.release_line` maps 4.2.x; L-76 (scheduled first) — est: 10min (depends E1.F9.T1) (P)
- [ ] E1.F8.T2 [Backend] Upgrade step `ld-1-capture` (LD-1): read-only check, no fix (`human: true`), prints the one-line diff and why; idempotent — est: 10min (depends E1.F1.T8)
- [ ] E1.F8.T3 [Backend] Upgrade steps `ld-2-components` (bootstrap proposal as planned edits, dry-run) and `ld-3-readme` (missing sections + `readme.check: on`, dry-run); idempotent; upgrade branch only — est: 12min (depends E1.F8.T2, E1.F6.T2, E1.F7.T4)
- [ ] E1.F8.T4 [Backend] Lanes and gates: one sentence in `rules/lanes.md`; tests that the blockers apply at every lane's human gates and that the `docs` lane runs sections and README on its own documents — est: 10min (depends E1.F2.T4, E1.F4.T5, E1.F7.T1)
- [ ] E1.F8.T5 [Backend] Rules `instructions.md` (in no `Load:` list; a footnote of the core contract), `components.md`, `readme.md` (≤ 700 words each) + `schemas/rule-loaders.json` + `Load:` entries of the acting skills + L-77; findings header aligned in `iteration-loop.md`; `karvey-iterate` names `instruction classify` without loading the rule — est: 15min (depends E1.F2.T4, E1.F4.T7, E1.F5.T6, E1.F6.T5, E1.F7.T5)
- [ ] E1.F8.T6 [Backend] Core contract `instruction` in `rules/_core.md` + its row in `schemas/contracts.json` (enforcement: the state tool's blockers); the core stays ≤ 1,000 words — est: 8min (depends E1.F8.T5)
- [ ] E1.F8.T7 [Backend] Skill text: `karvey-init` settings reference asks `instructions.capture` and `readme.check` (`on` recommended); `karvey-docs` gains the `components` and `readme` modes, bootstrap and review phrase — est: 12min (depends E1.F8.T5)
- [ ] E1.F8.T8 [Backend] Documentation: README sections "Captured instructions", "Component sheets", "README kept current" (setting, commands, LD step each) + `hooks/README.md` (guard, JSON output, failure notice) + L-78 (also: the init settings text asks both settings with `on` recommended) — est: 12min (depends E1.F8.T7, E1.F8.T3)
- [ ] E1.F8.T9 [Test] Compatibility 4.1 → 4.2: `test_compat_ld.py` replays the 4.1 fixtures (no map, capture off, README check off) — `validate --strict`, the linter over a fixture project, guard tables, gates unchanged; an old change is not refused after capture turns on — est: 12min (depends E1.F8.T1, E1.F8.T5, E1.F2.T4)
- [ ] E1.F8.T10 [Backend] Size tool: `compare … --fail-growth PCT` (exit 1 naming each phase above PCT); CI keeps `--warn-growth` — est: 8min (depends E1.F9.T2) (P)

### Feature E1.F9: Change-scoped: base after Wave 3 and size base (first); dogfooding on this repository (last)

- [ ] E1.F9.T1 [Test] Base check: `wave3-optimization`'s implementation and the project-upgrade engine are in this branch's base (Wave 3's last task's commit is an ancestor; `rules/_core.md`, `schemas/contracts.json`, the `Load:` lines, `karvey_lib/upgrade.py` and `upgrade-steps.json` exist); rebase; re-verify the architecture §13 list — est: 6min
- [ ] E1.F9.T2 [Backend] Size base snapshot `docs/spec/retros/context-size-4.2.0-base.json` in a commit of its own, before any rule or skill edit of this change — est: 6min (depends E1.F9.T1)
- [ ] E1.F9.T3 [Backend] Capture on for this repository: `instructions.capture: on` in `docs/spec/project.json` (the working copy turns it on at once); PLAN history notes that earlier impl commits predate the guard — est: 4min (depends E1.F1.T9)
- [ ] E1.F9.T4 [Backend] This repository's map (the eight components of the architecture's Component delta) + draft sheets from the bootstrap on a docs branch — est: 12min (depends E1.F6.T3, E1.F9.T3)
- [ ] E1.F9.T5 [Backend] Fill the sheets `hooks`, `state-tool`, `docs-tool`, `method-scripts` (operations, settings names, errors, idempotency, observability) — est: 15min (depends E1.F9.T4)
- [ ] E1.F9.T6 [Backend] Fill the sheets `method-text`, `spec-store` (containers with schema and a fictional example that validates), `method-page`, `ci` (runbook) — est: 15min (depends E1.F9.T4) (P)
- [ ] E1.F9.T7 [human] The owner reviews the eight sheets of this repository (REQ-LD-042: only the owner's own message turns a sheet `reviewed`) — executor: the owner (depends E1.F9.T5, E1.F9.T6)
- [ ] E1.F9.T8 [Backend] This repository's README to the six sections (`readme --bootstrap`, generated blocks for components and settings) + `readme.check: on` — est: 10min (depends E1.F7.T4, E1.F8.T8, E1.F9.T4)
- [ ] E1.F9.T9 [Test] Whole-repo gate: lint 0, every unit and regression suite, every table, `validate --all`, `karvey-trace.py living-docs --check` 63/63, `compare … --fail-growth 10`, `components --check` (sections, commits of the change range, leak) and `readme --check` green on this repository — est: 12min (depends E1.F9.T7, E1.F9.T8, E1.F8.T9, E1.F8.T10, E1.F8.T6, E1.F1.T14, E1.F2.T5, E1.F2.T6, E1.F4.T2, E1.F4.T8, E1.F5.T1, E1.F5.T7, E1.F6.T4, E1.F7.T3)
- [ ] E1.F9.T10 [Backend] Release docs: `[Unreleased]` summary (three parts, settings, LD-1..LD-3 in the manual Upgrade list, size before/after against the base snapshot); no version or date — est: 8min (depends E1.F9.T9)

### Epic item E1.DEPLOY

- [ ] E1.DEPLOY.T1 [human] The prod OK for the release that ships this change (D-10) — executor: the owner (depends E1.F9.T10)

## Task status
> Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked · 🙋 awaiting-human (blocked on a person)`

| Task | Status | estimate_min | actual_ai_min | actual_review_min | Notes |
|------|--------|--------------|---------------|-------------------|-------|
| E1.F1.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F1.T2 [Test] | ⬜ todo | 15 | — | — |  |
| E1.F1.T3 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F1.T4 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F1.T5 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F1.T6 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F1.T7 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F1.T8 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F1.T9 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F1.T10 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F1.T11 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F1.T12 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F1.T13 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F1.T14 [Test] | ⬜ todo | 12 | — | — |  |
| E1.F2.T1 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F2.T2 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F2.T3 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F2.T4 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F2.T5 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F2.T6 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F3.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F3.T2 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F3.T3 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F3.T4 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F3.T5 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T2 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F4.T3 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F4.T4 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T5 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F4.T6 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T7 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F4.T8 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F5.T1 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F5.T2 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F5.T3 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F5.T4 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F5.T5 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F5.T6 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F5.T7 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F6.T1 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F6.T2 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F6.T3 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F6.T4 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F6.T5 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F7.T1 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F7.T2 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F7.T3 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F7.T4 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F7.T5 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F8.T1 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F8.T2 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F8.T3 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F8.T4 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F8.T5 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F8.T6 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F8.T7 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F8.T8 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F8.T9 [Test] | ⬜ todo | 12 | — | — |  |
| E1.F8.T10 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.F9.T1 [Test] | ⬜ todo | 6 | — | — |  |
| E1.F9.T2 [Backend] | ⬜ todo | 6 | — | — |  |
| E1.F9.T3 [Backend] | ⬜ todo | 4 | — | — |  |
| E1.F9.T4 [Backend] | ⬜ todo | 12 | — | — |  |
| E1.F9.T5 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F9.T6 [Backend] | ⬜ todo | 15 | — | — |  |
| E1.F9.T7 [human] | ⬜ todo | — | — | — | human |
| E1.F9.T8 [Backend] | ⬜ todo | 10 | — | — |  |
| E1.F9.T9 [Test] | ⬜ todo | 12 | — | — |  |
| E1.F9.T10 [Backend] | ⬜ todo | 8 | — | — |  |
| E1.DEPLOY.T1 [human] | ⬜ todo | — | — | — | human |

`estimate_min` is written here once; impl fills the two actual columns and never edits the estimate.


## History
| Date | Phase | Action |
|-------|------|--------|
| 2026-09-26 | init | Change initialised (lane standard, Tier 3, D-38) |
| 2026-09-26 | requirements | 63 EARS requirements (61 ADDED, 2 MODIFIED living blocks, 2 change-scoped); judges domain + methods (intra-model, concerns) — 30 findings accepted and fixed in place, 1 rejected with reason |
| 2026-09-26 | mockup, design_graphic | skipped by the lane (standard: no UI — sheets and READMEs are documents) |
| 2026-09-26 | architecture | `architecture.md` + `risks.md` (R-1..R-13) generated; 21 components, 63/63 REQ-LD covered, component delta of this repository (8 ADDED); judges security + methods (intra-model, both concerns; 28 findings F-32..F-59, all accepted and fixed in place or carried as risks R-10..R-13; estimated cost US$ 0.27) |
| 2026-09-26 | infra | skipped: no cloud (`cloud.provider = none`); one CI step joins the existing lint job (architecture A-18) |
| 2026-09-26 | tasks | `tasks.md`: 71 tasks (69 agent, 2 `[human]`), 794 min calibrated, critical path 169 min; 65/65 requirements traced (63 REQ-LD + 2 MODIFIED); merged *how* gate pending |
