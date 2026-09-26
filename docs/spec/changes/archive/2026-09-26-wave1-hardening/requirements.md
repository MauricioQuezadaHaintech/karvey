# Requirements: wave1-hardening

## Project description

Karvey 3.11.2 declares guarantees in prose that no script or hook enforces, and its own repo skipped its
gates (panel review 2026-09-23, H-01..H-34). Wave 1 (→ 3.12.0) replaces the deterministic prose with a
validated phase state, guards backed by table tests, a production gate, one versioning moment and a CI
linter, and converges the open bugs and spec-gaps of `team-adapters` (D-04). North star (PRD §2):
*everything the method claims to guarantee is either enforced by a script or hook with a test, or stated
as a recommendation — never promised in prose and silently skipped.*

## Conventions

- **IDs.** `REQ-W1-NNN`, numbered contiguously. The heading also carries the numeric EARS id (`1.1`,
  `1.2`…) required by `rules/ears-format.md`.
- **Trace line.** Each requirement cites the PRD section (`PRD §n` / objective `O-n` / scope `S-n` /
  acceptance `AC-n`) and its sources: panel recommendation `R-xx`, verified panel finding `H-xx`, incident
  `BUG-NN`, team-adapters finding `F-xx` (with its review source `N-xx`/`C-xx`/`I-xx`/`S-xx`/`E-xx` where it
  matters), backlog item `BL-NN`, and decision `D-NN`.
- **AMENDS.** A requirement marked **AMENDS REQ-ADP-0xx** replaces (fully or in the stated part) that
  `team-adapters` requirement. `team-adapters` was never archived, so its requirements reach the living spec
  through this change's `spec-delta.md` (D-04).
- **Technology.** The SHALL text names *roles* of the method, not implementations. Where the panel or the
  owner fixed a public name (a command or file the user types or reads), the glossary maps the role to that
  name; the language, framework and test runner are architecture decisions.
- **Actors.** "the method" = the skills and rules as shipped; "a phase skill" = any of the 13 phase skills;
  "the human" = the person who owns the change's approvals (`role: human`).

### Glossary — roles and their public names

| Role in the requirements | Public name fixed by the panel / owner | Source |
|---|---|---|
| the **state tool** | `scripts/karvey-state` (`next`, `advance`, `approve`, `skip`, `validate [--fix]`) | R-01 |
| the **spec schema** / **project schema** | `schemas/spec.schema.json`, `schemas/project.schema.json` | R-01 |
| the **state-machine rule** | `rules/state-machine.md` | R-01 |
| the **plan gate** | `plan-gate` hook (pre-execution guard) | R-02 |
| the **git-flow guard** | `git-flow-guard` hook (pre-execution guard) | R-02 |
| the **prod gate** | `prod-gate` hook (pre-execution guard) | R-02, D-02 |
| the **approval hook** | hook on the human's prompt submission (`UserPromptSubmit`) | D-01 |
| the **spec-write validator** | post-write hook on `**/spec.json` | R-02 |
| the **guard tables** | table tests of the guards | R-02 |
| the **session hook** | `hooks/karvey-session-context.sh` | R-06 |
| the **handoff capture** | `scripts/karvey-handoff-capture` | R-06 |
| the **plugin linter** | `scripts/lint-plugin` + CI workflow | R-07 |
| the **spec-merge tool** | `scripts/karvey-spec-merge` (`--dry-run`) | R-17 |
| the **dashboard** | `karvey-context` backed by `scripts/karvey-context` | R-18 |

---

## Requirement 1: Single phase state machine (R-01)

### 1.1 REQ-W1-001 — Closed phase enum
The method SHALL store in `spec.json:phase` only one of `init | requirements | mockup | design_graphic |
architecture | infra | tasks | impl | test | qa | deploying | deployed | archived`, and SHALL record
"generated" and "approved" only under `approvals.*`.

Traces to PRD: §6 S-1, O-1 · Sources: R-01, H-01, H-22 · BL-04

**Scenario — success:** GIVEN a change whose requirements were just written WHEN the requirements skill
records its progress THEN `phase` is `requirements` and `approvals.requirements.generated` is `true`.
**Scenario — error:** GIVEN a `spec.json` with `phase: "requirements-generated"` WHEN it is validated THEN
the validation reports the value as outside the enum and names the field.

### 1.2 REQ-W1-002 — Published schemas
The method SHALL ship a machine-readable schema for `spec.json` and one for `project.json` that together
cover every field documented in `rules/living-specs.md` and `rules/project-config.md`, including `lane`,
`skipped`, `phase_history`, `seed_backlog_id` as a string **or** a list, and the legacy aliases of
REQ-W1-009 and REQ-W1-088.

Traces to PRD: §6 S-1, O-1 · Sources: R-01, R-07 · BL-04

**Scenario — success:** GIVEN every field named in the two rules WHEN the plugin linter compares them with
the schemas THEN every field is present in a schema.
**Scenario — error:** GIVEN a rule that documents a field the schema lacks WHEN the linter runs THEN it fails
and names the field and the rule.

### 1.3 REQ-W1-003 — Validate
WHEN the state tool validates a change or a project, the state tool SHALL report every violation with the
file, the field path and the expected value, SHALL exit with a non-zero status when any violation is an
error, and WHILE the project runs in Wave 1 warning mode SHALL report legacy shapes as warnings with exit 0.

Traces to PRD: §6 S-1, O-1, AC-1 · Sources: R-01 (Ola 1: "validate corre en modo advertencia") · BL-04

**Scenario — success:** GIVEN a valid `spec.json` WHEN it is validated THEN the tool prints no violation and
exits 0.
**Scenario — error:** GIVEN a `spec.json` whose `approvals.prod.by` is set but `approvals.prod.ref` is empty
WHEN it is validated THEN the tool reports `approvals.prod.ref` as missing and exits non-zero.

### 1.4 REQ-W1-004 — Transition only along allowed edges
WHEN a phase transition is requested, the state tool SHALL apply it only if the edge exists in the
state-machine rule and every preceding phase is `approved` or `skipped`; IF not, THEN it SHALL refuse,
leave `spec.json` unchanged and name the unmet precondition.

Traces to PRD: §6 S-1, O-1 · Sources: R-01 ("toda precondición acepta approved || skipped"), H-03 · BL-04

**Scenario — success:** GIVEN `requirements` approved and `mockup`, `design_graphic` skipped WHEN
`architecture` is requested THEN the transition is applied.
**Scenario — error:** GIVEN `requirements.approved = false` WHEN `architecture` is requested THEN the tool
refuses with "requirements not approved or skipped" and `spec.json` is byte-identical.

### 1.5 REQ-W1-005 — Next phase is computed, not interpreted
WHEN the orchestrator is asked what comes next for a change, the method SHALL answer from the state tool's
computed next phase, and the orchestrator SHALL NOT contain a second phase table that can disagree with the
state-machine rule.

Traces to PRD: §6 S-1, O-1 · Sources: R-01, H-01 · BL-04

**Scenario — success:** GIVEN a change at `tasks` with tasks approved WHEN `/karvey {id}` runs THEN it
proposes `impl`, the value the state tool returns.
**Scenario — error:** GIVEN a `spec.json` that fails validation WHEN `/karvey {id}` runs THEN it reports the
validation errors instead of guessing a phase.

### 1.6 REQ-W1-006 — Approvals carry who, role, time and reference
WHEN an approval is recorded, the state tool SHALL write `by`, `role` (`human` | `ceo-delegate`), `date` as
an ISO 8601 timestamp with time and zone, and `ref`; IF any of them is missing, THEN it SHALL refuse; IF
the approval is `prod` and `role` is not `human`, THEN it SHALL refuse.

Traces to PRD: §6 S-1, O-3 · Sources: R-01 (`approve --by --role --ref`), R-14 (fecha con hora), H-22 ·
Decision: D-03

**Scenario — success:** GIVEN a human approval with a D-NN ref WHEN `approve prod` runs THEN
`approvals.prod` holds the four fields.
**Scenario — error:** GIVEN `role: ceo-delegate` WHEN `approve prod` runs THEN it is refused with
"production approval is never delegated".

### 1.7 REQ-W1-007 — Skipped phases are recorded
WHEN a phase is skipped, the state tool SHALL record it in `spec.json:skipped` as `{phase: reason}` with a
non-empty reason, and SHALL treat a skipped phase as satisfying the preconditions of the next phase; IF the
reason is empty, THEN it SHALL refuse.

Traces to PRD: §6 S-1, §9 (no lanes yet) · Sources: R-01, H-03, D-04 · BL-04

**Scenario — success:** GIVEN this change (no UI) WHEN `skip mockup --reason "no UI"` runs THEN
`skipped.mockup = "no UI"` and `design_graphic` may be skipped next.
**Scenario — error:** GIVEN no reason WHEN `skip mockup` runs THEN the tool refuses and records nothing.

### 1.8 REQ-W1-008 — Phase history
WHEN a phase transition is applied, the state tool SHALL close the current entry of
`spec.json:phase_history` with `exited_at` and append `{phase, entered_at}` for the new phase, both ISO 8601
with time; it SHALL NOT rewrite or delete earlier entries.

Traces to PRD: §6 S-1, O-1 · Sources: R-01, R-14 (base for Wave 2 metrics) · BL-04

**Scenario — success:** GIVEN a change at `requirements` WHEN it moves to `architecture` THEN the
`requirements` entry gets `exited_at` and a new `architecture` entry is appended.
**Scenario — error:** GIVEN a `phase_history` whose last entry has no `entered_at` WHEN a transition is
requested THEN the tool refuses and reports the corrupt entry.

### 1.9 REQ-W1-009 — Migration of legacy `spec.json` (`--fix`)
WHEN the state tool runs `validate --fix` on a legacy `spec.json`, the state tool SHALL map the legacy phase
values (`requirements-generated`, `mockup-generated`, `design-graphic-approved`,
`architecture-generated|-approved`, `infra-generated|-approved`, `tasks-generated|-approved`, `deploy`) to
the enum, SHALL convert `gates_skipped` into `skipped`, SHALL map `management: "none"` to `markdown`, SHALL
show the diff before writing, SHALL NOT create or flip any approval, and SHALL produce the same file when run
twice.

Traces to PRD: §6 S-1, O-1, AC-1 · Sources: R-01 (migrar con `--fix`), H-01, H-22, F-40 (I-11) · BL-04

**Scenario — success:** GIVEN `team-adapters/spec.json` and the archived `team-layer/spec.json` WHEN
`--fix` runs THEN both validate with no error and no `approvals.*.approved` value changed.
**Scenario — error:** GIVEN an unknown phase value `"shipping"` WHEN `--fix` runs THEN the file is not
written and the value is reported as unmappable.

### 1.10 REQ-W1-010 — Migration of legacy `project.json:management` (`--fix`)
WHEN the state tool runs `validate --fix` on a `project.json` whose `management` is a string, the state tool
SHALL rewrite it as `{"tool": "<string>"}`, SHALL move a top-level `clickup.backlog_list_id` into
`management.location` when present, SHALL keep every other key unchanged, and SHALL leave `statuses` absent
so the missing-map path (REQ-W1-080) resolves it.

Traces to PRD: §6 S-1, S-13, O-11 · Sources: R-01, BUG-06 / F-08 (I-02, C-03; 16 HainTech repos: 15
`"markdown"`, 1 `"clickup"`) · BL-04

**Scenario — success:** GIVEN `"management": "markdown"` WHEN `--fix` runs THEN `management` becomes
`{"tool": "markdown"}` and nothing else changes.
**Scenario — error:** GIVEN `"management": 42` WHEN `--fix` runs THEN the file is not written and the value is
reported as not migratable.

### 1.11 REQ-W1-011 — impl, deploy and archive write real states
WHEN impl starts, the method SHALL set `phase = impl`; WHEN deploy opens the production release, it SHALL
set `deploying`; it SHALL set `deployed` only after the production pipeline is green and the post-deploy
check passed; WHEN archive is requested, the state tool SHALL refuse unless `phase = deployed` and
`approvals.prod.by` is set with `role: human`.

Traces to PRD: §6 S-1, O-3 · Sources: R-01, H-02, H-07 · BL-04

**Scenario — success:** GIVEN a merged production PR with a green pipeline and a passing check WHEN deploy
finishes THEN `phase = deployed`.
**Scenario — error:** GIVEN `phase = deploying` (production PR still open) WHEN archive runs THEN it refuses
and creates no `IMPLEMENTED` file.

### 1.12 REQ-W1-012 — One product document and one spec-delta path
The method SHALL use `prd.md` as the only product document of a change and `spec-delta.md` at the change
root as the only spec-delta path; no skill SHALL read `proposal.md` or `specs/{capability}/spec-delta.md`.

Traces to PRD: §6 S-1, S-7 · Sources: R-01, H-24, H-25 · BL-04

**Scenario — success:** GIVEN every skill WHEN the linter lists the change artifacts they read THEN only
`prd.md` and `<change>/spec-delta.md` appear for those roles.
**Scenario — error:** GIVEN a skill that still reads `proposal.md` WHEN the linter runs THEN it fails naming
the skill and line.

### 1.13 REQ-W1-013 — Every phase write goes through the state tool
The phase skills SHALL change `phase`, `approvals`, `skipped` and `phase_history` only by invoking the state
tool; no skill text SHALL instruct the agent to edit those fields by hand.

Traces to PRD: §6 S-1, O-1 · Sources: R-01 ("cada skill cambia su Update spec.json: phase… por una
llamada al script"), H-01 (14 writers, 12 formats) · BL-04

**Scenario — success:** GIVEN the 13 phase skills WHEN the linter searches for instructions to write those
fields THEN every hit is an invocation of the state tool.
**Scenario — error:** GIVEN a skill that says "Update spec.json: `phase: tasks-approved`" WHEN the linter
runs THEN it fails.

## Requirement 2: Guards that do what the rule says (R-02)

### 2.1 REQ-W1-014 — Stream redirections are not writes
WHEN the plan gate classifies a shell command, the plan gate SHALL NOT classify a redirection to a file
descriptor or to the null device (`2>/dev/null`, `2>&1`, `>&2`, `&>/dev/null`) as a file write.

Traces to PRD: §6 S-2, O-2 · Sources: R-02, H-10 (false positive `ls 2>/dev/null` → rc=2) · BL-05

**Scenario — success:** GIVEN no approval marker WHEN `ls 2>/dev/null` is run THEN the gate allows it.
**Scenario — error:** GIVEN no approval marker WHEN `echo x > notes.txt` is run THEN the gate blocks it.

### 2.2 REQ-W1-015 — Destructive command classes are gated
WHILE no valid approval marker exists, the plan gate SHALL block `git clean`, `find … -delete`, in-place
`sed -i`, `truncate`, a `DELETE FROM` without `WHERE`, `terraform destroy`, cloud-CLI `… delete` verbs and
`rm -r`/`rm -rf`, in addition to the classes it blocks today.

Traces to PRD: §6 S-2, O-2 · Sources: R-02, H-10 (`git clean -fdx`, `find . -delete`, `sed -i` → rc=0) ·
BL-05

**Scenario — success:** GIVEN a valid marker WHEN `git clean -fdx` runs THEN it is allowed.
**Scenario — error:** GIVEN no marker WHEN `find . -name '*.tmp' -delete` runs THEN it is blocked with the
"plan not approved" message.

### 2.3 REQ-W1-016 — Marker scoped to project and change, with expiry
The plan gate SHALL honour only an approval marker scoped to the current project (and change, when one is
active), SHALL treat a marker older than its TTL (default 120 minutes, configurable per project) as absent,
and SHALL treat the marker as consumed when the phase that it approved closes.

Traces to PRD: §6 S-2, O-2, §11 A-1 · Sources: R-02, H-11 (fixed global `/tmp` path, no TTL, never
consumed; `enforcement.md:25` promises expiry) · BL-05

**Scenario — success:** GIVEN a marker created 10 minutes ago for project A WHEN an edit runs in project A
THEN it is allowed.
**Scenario — error:** GIVEN a marker for project A WHEN an edit runs in project B, or in A after 121
minutes THEN it is blocked.

### 2.4 REQ-W1-017 — The approval hook creates the marker from the human's words
WHEN the human submits a prompt that matches the project's approval vocabulary and contains none of its
negation terms, the approval hook SHALL create the approval marker and record the time and the first 80
characters of that prompt beside it, and SHALL write an audit record of that marker carrying the prompt's
hash, the session and the marker's creation time (revision 4, D-34).

Traces to PRD: §6 S-2, O-2 · Sources: R-02 (tensión con la regla global), H-11, F-76 · Decision: D-01, D-34 · BL-05

**Scenario — success:** GIVEN a plan was presented WHEN the human writes "aprobado, ejecuta" THEN the marker
exists and names that prompt, and the audit log holds its record with the prompt hash, session and time.
**Scenario — error:** GIVEN the human writes "no apruebo todavía" or "¿está aprobado?" WHEN the prompt is
submitted THEN no marker is created.

### 2.5 REQ-W1-018 — The agent never creates the marker
IF a tool call of the agent would create, touch, copy, move or edit the approval marker, THEN the plan gate
SHALL block it and say that approval comes only from the human's message.

Traces to PRD: §6 S-2, O-2 · Sources: R-02, H-11 · Decision: D-01 · BL-05

**Scenario — success:** GIVEN the human approved WHEN the agent proceeds to edit a file THEN the edit is
allowed without the agent touching the marker.
**Scenario — error:** GIVEN no approval WHEN the agent runs `touch <marker path>` THEN it is blocked.

### 2.6 REQ-W1-019 — Approval vocabulary declared in one place
The method SHALL declare the approval vocabulary and the negation terms in one place per project, with a
documented default list, and the guard tables SHALL include at least 5 approval phrases, 5 negations or
questions, and 2 cases of quoted or pasted text that contains an approval word.

Traces to PRD: §6 S-2, O-2 · Sources: R-02 · Decision: D-01 · BL-05

**Scenario — success:** GIVEN the default list WHEN the guard tables run THEN every listed approval creates
the marker and every negation does not.
**Scenario — error:** GIVEN a pasted log line "status: approved" inside a code block WHEN submitted THEN no
marker is created.

### 2.7 REQ-W1-020 — git-flow resolves the target repository
WHEN the git-flow guard evaluates a `git commit` or `git push`, the guard SHALL resolve the branch of the
repository the command acts on, including `git -C <path> …` and `cd <path> && git …`, not the branch of the
session's working directory.

Traces to PRD: §6 S-2, O-2 · Sources: R-02, H-12 (`git -C <repo-en-master> commit` → rc=0) · BL-05

**Scenario — success:** GIVEN the session in a feature branch and `<path>` on `master` WHEN
`git -C <path> commit -m x` runs THEN it is blocked.
**Scenario — error:** GIVEN `<path>` on `feature/x` WHEN `git -C <path> commit -m x` runs THEN it is allowed.

### 2.8 REQ-W1-021 — Bare push on production and branch-name precision
WHEN HEAD of the target repository is the production branch, the git-flow guard SHALL block a bare
`git push`; the guard SHALL match production and integration branch names as whole names, so that
`git push origin master-notes` is allowed.

Traces to PRD: §6 S-2, O-2 · Sources: R-02, H-12 (bare push passes; `master-notes` false positive) · BL-05

**Scenario — success:** GIVEN HEAD on `feature/x` WHEN `git push origin master-notes` runs THEN it is
allowed.
**Scenario — error:** GIVEN HEAD on `master` WHEN `git push` runs THEN it is blocked.

### 2.9 REQ-W1-022 — Integration push: implemented or not promised
The enforcement rule SHALL describe only protections the git-flow guard implements and the guard tables
test; WHERE integration and production are different branches, the guard SHALL block a direct `git push` to
integration from a branch that is not integration itself, or the rule SHALL NOT claim that protection.

Traces to PRD: §6 S-2, O-2 · Sources: R-02, H-13 (`enforcement.md:16` vs guard) · BL-05

**Scenario — success:** GIVEN integration `dev` ≠ production `master` WHEN `git push origin feature/x:dev`
runs THEN it is blocked (or the rule no longer promises it and the linter confirms the wording).
**Scenario — error:** GIVEN a rule sentence promising a block that no guard-table case covers WHEN the linter
runs THEN it fails.

### 2.10 REQ-W1-023 — Merge to production requires a human approval
WHEN a command would merge into the production branch (`gh pr merge`, including `--admin`;
`az repos pr update --status completed`; `glab mr merge`; a `git push` to production, in every form the
prod gate recognises), the prod gate SHALL allow it only if the state tool confirms, for the change being
released, a production approval with `by` set, `role: human` and `ref` non-empty, whose evidence is the
approval hook's audit record of the prod marker it names (prompt hash, session and time, D-34), which names
the head commit the human approved and is less than 24 hours old (D-35), and only if the commit being
released is that commit; otherwise it SHALL block and name the missing field. The prod gate SHALL also block
when it cannot tell which single commit reaches production. WHEN a change is reopened, the state tool SHALL
supersede its production approval, so the human gives it again after the rework (D-36).

Traces to PRD: §6 S-2, O-3, AC-3 · Sources: R-02, H-12 (`gh pr merge 12 --merge --admin` → rc=0), H-15,
F-76, F-77, F-79 · Decision: D-02, D-03, D-34, D-35, D-36 · BL-05

**Scenario — success:** GIVEN a production approval recorded from the human's own message for head `abc123`,
1 hour ago, with its audit record WHEN `gh pr merge 30 --merge` runs on a PR whose head is `abc123` THEN it
is allowed.
**Scenario — error:** GIVEN `approvals.prod.by` empty WHEN `gh pr merge 30 --merge --admin` runs THEN it is
blocked.
**Scenario — error (other commit):** GIVEN an approval for head `abc123` WHEN a new commit is pushed to the
PR, or another branch is pushed to production as the change, THEN the merge or push is blocked with
"not the approved commit".
**Scenario — error (evidence, expiry, reopen):** GIVEN a ledger entry with no matching audit record, or an
approval older than 24 hours, or a change reopened after its approval WHEN the merge runs THEN it is
blocked.

### 2.11 REQ-W1-024 — The prod gate fails closed
IF the prod gate cannot determine the change being released, cannot read or validate its `spec.json`, or the
state tool errors, THEN the prod gate SHALL block the merge and state the reason.

Traces to PRD: §6 S-2, O-3, §9 (Security Tier 2) · Sources: R-02 · Decision: D-02

**Scenario — success:** GIVEN a readable, valid `spec.json` with a human prod approval WHEN the merge runs
THEN it is allowed.
**Scenario — error:** GIVEN a corrupted `spec.json` WHEN the merge runs THEN it is blocked with "cannot
verify the production approval".

### 2.12 REQ-W1-025 — Every prod-gate decision is logged
WHEN the prod gate allows or blocks a merge, the prod gate SHALL print one line with the decision, the
change-id, the approver and the approval `ref`.

Traces to PRD: §6 S-2, O-3, §9 (Tier 2 access logging) · Sources: R-02 · Decision: D-02, D-03

**Scenario — success:** GIVEN an allowed merge WHEN it runs THEN the line shows `allow`, the change-id and
`ref`.
**Scenario — error:** GIVEN a blocked merge WHEN it runs THEN the line shows `block` and the missing field.

### 2.13 REQ-W1-026 — The prod gate is on by default
WHERE Karvey's hooks are installed in a project and `project.json` does not switch the prod gate off, the
prod gate SHALL be active.

Traces to PRD: §6 S-2, O-3 · Sources: R-02 · Decision: D-02

**Scenario — success:** GIVEN a project with no `enforcement.prod_gate_hook` key WHEN a production merge
without approval runs THEN it is blocked.
**Scenario — error:** GIVEN the key absent WHEN the dashboard shows the enforcement state THEN it shows the
prod gate as `on (default)`, never as `off`.

### 2.14 REQ-W1-027 — Per-project switch-off
WHERE `project.json:enforcement.prod_gate_hook` is `false`, the prod gate SHALL allow the command and print
one line saying the production gate is disabled for this project.

Traces to PRD: §6 S-2 · Sources: R-02 · Decision: D-02

**Scenario — success:** GIVEN `prod_gate_hook: false` WHEN a production merge runs THEN it is allowed with the
disabled notice.
**Scenario — error:** GIVEN `prod_gate_hook: "no"` (not a boolean) WHEN a production merge runs THEN the
value is treated as invalid and the gate stays on.

### 2.15 REQ-W1-028 — `spec.json` is validated when written
WHEN any tool call writes a file named `spec.json` under `docs/spec/`, the spec-write validator SHALL
validate it and return the violations to the session.

Traces to PRD: §6 S-2, O-1 · Sources: R-02 (PostToolUse sobre `**/spec.json`) · BL-05

**Scenario — success:** GIVEN a valid write WHEN it completes THEN nothing is reported.
**Scenario — error:** GIVEN a write that sets `phase: "qa-approved"` WHEN it completes THEN the session
receives the enum violation.

### 2.16 REQ-W1-029 — No described-but-missing hooks
The method SHALL NOT cite a hook that the plugin does not ship; `clickup-sync-guard` and `standards-guard`
SHALL either be shipped with guard-table cases or removed from `rules/phase-close.md` and
`rules/engineering-standards.md`.

Traces to PRD: §6 S-2, O-2, O-11 · Sources: R-02, H-14, BUG-15 / F-29 (C-10) · BL-05

**Scenario — success:** GIVEN every hook named in skills and rules WHEN the linter checks the plugin THEN each
one exists with table cases.
**Scenario — error:** GIVEN `phase-close.md` naming `clickup-sync-guard` WHEN the linter runs THEN it fails.

### 2.17 REQ-W1-030 — Guard tables in CI
The method SHALL ship table tests for every guard — plan gate, git-flow guard, prod gate, approval hook,
spec-write validator and session hook — containing at least every case measured in H-10 and H-12 plus the
plan-gate false positives and false negatives, and the CI SHALL fail the PR when any case fails.

Traces to PRD: §6 S-2, O-2, AC-2 · Sources: R-02 (`tests/hooks/*`), H-10, H-12 · BL-05

**Scenario — success:** GIVEN the guards at 3.12.0 WHEN CI runs THEN every table case passes.
**Scenario — error:** GIVEN a regex change that makes `ls 2>/dev/null` block again WHEN CI runs THEN the PR
fails on that case.

## Requirement 3: Deploy and archive never commit on integration or production (R-03)

### 3.1 REQ-W1-031 — Production approval as D-NN and in the PR
WHEN the human gives the production OK, the deploy skill SHALL record it as a `D-NN` in the decision log and
in the PR body or PR approval, and SHALL NOT create a commit on the integration or production branch to
record it.

Traces to PRD: §6 S-3, O-4 · Sources: R-03, H-18 · Decision: D-03 · BL-06

**Scenario — success:** GIVEN a deploy awaiting prod OK WHEN the human approves THEN a D-NN entry exists and
the PR references it, and `git log --first-parent {integration}` shows no new commit.
**Scenario — error:** GIVEN the deploy text instructed "commit it on the branch that goes to master" WHEN the
linter checks deploy THEN it fails.

### 3.2 REQ-W1-032 — `approvals.prod` written at archive
WHEN a change is archived, the archive skill SHALL copy the production approval into
`spec.json:approvals.prod` with `ref` set to the `D-NN` or the PR approval URL.

Traces to PRD: §6 S-3, O-3 · Sources: R-03 (AG's variant, PM-11) · Decision: D-03 · BL-06

**Scenario — success:** GIVEN D-07 recorded for the prod OK WHEN archive runs THEN `approvals.prod.ref =
"D-07"`.
**Scenario — error:** GIVEN no D-NN and no PR approval exist WHEN archive runs THEN it stops and reports that
the production approval is not recorded.

### 3.3 REQ-W1-033 — Archive on its own branch, by PR
WHEN archive starts, the archive skill SHALL create a branch from production named
`chore/archive-{change-id}`, SHALL commit only there, and SHALL merge it through a docs-only PR.

Traces to PRD: §6 S-3, O-4 · Sources: R-03, H-19 · Decision: D-03 · BL-06

**Scenario — success:** GIVEN HEAD on `dev` after a deploy WHEN archive runs THEN its commits are on
`chore/archive-{id}` and reach production only through the PR.
**Scenario — error:** GIVEN HEAD on `dev` WHEN archive would commit THEN the git-flow guard blocks it and the
skill does not fall back to committing on `dev`.

### 3.4 REQ-W1-034 — Checklist before the first push
The deploy skill SHALL run the 6-step pre-deploy checklist (feature branch, CHANGELOG, everything committed,
branch pushed, merged to integration, integration pushed) before its first `git push`.

Traces to PRD: §6 S-3, O-4 · Sources: R-03 (Step 1.9), H-20 · BL-06

**Scenario — success:** GIVEN the deploy skill WHEN the linter compares the positions of the checklist and the
first push step THEN the checklist comes first.
**Scenario — error:** GIVEN a checklist item fails WHEN deploy runs THEN no push is executed.

### 3.5 REQ-W1-035 — Trunk projects (integration = production)
WHERE `branch_flow.integration` equals `branch_flow.production`, the deploy skill, the archive skill and the
guards SHALL use the single PR from the feature branch as both the integration and the production gate, and
SHALL NOT require a separate integration merge.

Traces to PRD: §6 S-3, O-4 · Sources: R-03, R-08 ("el propio repo usa trunk", `project.json:16-20`) ·
Decision: D-04

**Scenario — success:** GIVEN this repo (`main` / `main`) WHEN deploy runs THEN it opens one PR
`feature/wave1-hardening → main` and the prod gate evaluates it.
**Scenario — error:** GIVEN a trunk project WHEN deploy would push directly to `main` THEN the git-flow guard
blocks it.

## Requirement 4: One versioning moment (R-04)

### 4.1 REQ-W1-036 — impl adds to Unreleased, no bump
WHEN impl commits a task, the impl skill SHALL add its line under `## [Unreleased]` in the CHANGELOG and
SHALL NOT change the version in any manifest.

Traces to PRD: §6 S-4, O-5 · Sources: R-04, H-17, F-43 (C-16) → BL-07 · BL-07

**Scenario — success:** GIVEN three tasks committed WHEN the manifests are read THEN the version is unchanged
and `[Unreleased]` has three lines.
**Scenario — error:** GIVEN impl text instructing a bump per commit WHEN the linter runs THEN it fails.

### 4.2 REQ-W1-037 — Bump only at the release step
WHEN deploy reaches its release step, the deploy skill SHALL turn `[Unreleased]` into `[x.y.z] - date` and
bump every version manifest once; a release SHALL contain exactly one bump.

Traces to PRD: §6 S-4, O-5 · Sources: R-04, H-17 · BL-07

**Scenario — success:** GIVEN a release WHEN `git log` of the release range is read THEN exactly one commit
changes the manifests' version.
**Scenario — error:** GIVEN `[Unreleased]` is empty WHEN the release step runs THEN it stops: there is
nothing to release.

### 4.3 REQ-W1-038 — QA and deploy pre-check validate Unreleased
The QA versioning dimension and the deploy pre-check SHALL verify the `[Unreleased]` section, not a numbered
entry that only the release step creates.

Traces to PRD: §6 S-4, O-5 · Sources: R-04 (circular order QA-D6 / pre-check 3) · BL-07

**Scenario — success:** GIVEN an `[Unreleased]` section with the change's lines WHEN QA D6 runs THEN it passes.
**Scenario — error:** GIVEN an empty `[Unreleased]` WHEN the deploy pre-check runs THEN it fails naming it.

### 4.4 REQ-W1-039 — The versioning rule says "per release"
The versioning rule SHALL state that each release increments the version, and the orchestrator SHALL NOT
describe a version bump per commit.

Traces to PRD: §6 S-4 · Sources: R-04 (`versioning.md:15`, `karvey/SKILL.md:191`) · BL-07

**Scenario — success:** GIVEN the rule and the orchestrator WHEN read THEN both say "per release".
**Scenario — error:** GIVEN any skill saying "bump + CHANGELOG per commit" WHEN the linter runs THEN it fails.

### 4.5 REQ-W1-040 — QA D6 checks what the versioning rule says it checks
The QA versioning dimension SHALL verify every item the versioning rule assigns to QA, including that the
front reads its version from the version file and the DEV/PROD version formats.

Traces to PRD: §6 S-4, S-13, O-11 · Sources: F-38 (C-15) · Amends: `versioning.md`, `karvey-qa` D6

**Scenario — success:** GIVEN the rule's QA list WHEN compared with D6 THEN every item appears in D6.
**Scenario — error:** GIVEN a rule item absent from D6 WHEN the linter compares them THEN it fails.

### 4.6 REQ-W1-041 — Visible-version check on the post-deploy step
WHEN the deploy post-deploy step checks the visible version on DEV, the deploy skill SHALL accept the bumped
version together with an unmistakable DEV mark in any format, SHALL compare it with the version file of the
deployed commit, and SHALL report a missing visible version as a recommendation, not as a finding.

Traces to PRD: §6 S-4, S-13, O-11 · Sources: F-20 (I-10, N-10; `front-vue-paautin-1` shows `DEV 2.10.4`) ·
Amends: `versioning.md`, deploy 2.4-bis / 2.7 · Related: BL-26 (Wave 2)

**Scenario — success:** GIVEN DEV shows `DEV 2.10.4` and the deployed commit's version file says `2.10.4`
WHEN the check runs THEN it passes.
**Scenario — error:** GIVEN two changes in `dev` WHEN the first one's check sees the second one's bump THEN it
compares against the deployed commit's version file and does not report a mismatch.

## Requirement 5: The estimate is never overwritten (R-05)

### 5.1 REQ-W1-042 — Estimate and actual are separate fields
WHEN a task finishes, the impl skill SHALL record the actual time as a time entry, worklog or actual field
of the team's tracker, and SHALL NOT write the actual into the estimate field.

Traces to PRD: §6 S-5, O-6 · Sources: R-05, H-16 (`curl … time_estimate: {actual_time_ms}`) · BL-08

**Scenario — success:** GIVEN a task estimated at 20 min that took 35 WHEN it closes THEN the tracker shows
estimate 20 and actual 35.
**Scenario — error:** GIVEN impl text that writes `time_estimate` with the actual WHEN the linter runs THEN it
fails.

### 5.2 REQ-W1-043 — Three numbers per task
The method SHALL keep, per task, `estimate_min`, `actual_ai_min` and `actual_review_min` in the change's task
record, whichever tracker is used, including Markdown.

Traces to PRD: §6 S-5, O-6 · Sources: R-05 · BL-08

**Scenario — success:** GIVEN a Markdown change WHEN a task closes THEN its PLAN.md row holds the three numbers.
**Scenario — error:** GIVEN a task closed without an actual WHEN the phase closes THEN the close report lists
the task as "actual missing".

### 5.3 REQ-W1-044 — Calibration at archive
WHEN a change is archived, the archive skill SHALL compute actual/estimate per work type of the estimation
table and SHALL propose a recalibration for a type whose deviation exceeds ±30% in each of the last 3
archived changes.

Traces to PRD: §6 S-5, O-6, §11 A-3 · Sources: R-05 (`clickup-protocol.md:139-150`) · BL-08

**Scenario — success:** GIVEN a type at +45%, +38% and +40% in the last 3 changes WHEN archive runs THEN a
recalibration is proposed.
**Scenario — error:** GIVEN fewer than 3 archived changes with data WHEN archive runs THEN it reports the
ratios and says there is not enough history to propose.

## Requirement 6: Session hook (R-06)

### 6.1 REQ-W1-045 — Archived and implemented changes are not active
WHEN the session hook selects the active change, the session hook SHALL exclude `changes/archive/` and every
change directory that contains `IMPLEMENTED`.

Traces to PRD: §6 S-6, O-7 · Sources: R-06, H-08 (reproduced: "active change: archive") · BL-09

**Scenario — success:** GIVEN `changes/feat-a` and a newer `changes/archive/…` WHEN the hook runs THEN the
active change is `feat-a`.
**Scenario — error:** GIVEN only archived changes WHEN the hook runs THEN it reports no active change and does
not ask for a restore.

### 6.2 REQ-W1-046 — Compact or full manifest, never both
WHEN the session hook injects the agent manifest, the session hook SHALL inject the compact form or the full
form, never both.

Traces to PRD: §6 S-6, O-7 · Sources: R-06, H-09 · Modifies: REQ-TEAM-014b · BL-09

**Scenario — success:** GIVEN a compact manifest exists WHEN the hook runs THEN only the compact one is
injected.
**Scenario — error:** GIVEN both exist WHEN the guard table runs THEN a case asserting both are present fails.

### 6.3 REQ-W1-047 — Bounded injection
WHEN the session hook injects the board and the handoff, the session hook SHALL inject only open board rows,
at most 40, and at most 6 KB of handoff, and SHALL say what was truncated and where the full file is; the
context SHALL be emitted through the harness's structured additional-context channel.

Traces to PRD: §6 S-6, O-7 · Sources: R-06 · Modifies: REQ-TEAM-014b · BL-09

**Scenario — success:** GIVEN a board with 120 rows (70 open) WHEN the hook runs THEN 40 open rows are
injected with a "30 more open rows in {path}" line.
**Scenario — error:** GIVEN a 20 KB handoff WHEN the hook runs THEN it injects 6 KB and the truncation
notice, never the whole file.

### 6.4 REQ-W1-048 — `state.json` written by the handoff capture
WHEN `karvey-checkpoint save` runs, the method SHALL write `state.json` by running the handoff capture, which
measures branch, commit and uncommitted count of each owned repository; the agent SHALL NOT write
`state.json` by hand.

Traces to PRD: §6 S-6, O-7 · Sources: R-06 (`karvey-checkpoint/SKILL.md:259` "never by hand") · Modifies:
REQ-TEAM-010d · BL-09

**Scenario — success:** GIVEN a save WHEN it finishes THEN `state.json` matches `git rev-parse` and
`git status --porcelain` of each repo.
**Scenario — error:** GIVEN the capture fails for one repo WHEN save runs THEN `state.json` marks that repo
"not measured" with the reason instead of inventing values.

### 6.5 REQ-W1-049 — One rotation threshold
The method SHALL define the rotation threshold in one place, and the statusline, the team rule, the
checkpoint skill and the hooks README SHALL read or cite that one value.

Traces to PRD: §6 S-6, O-7, §11 Q-01 · Sources: R-06, H-32 (24 h vs 8 h) · Modifies: REQ-TEAM-015 · BL-09

**Scenario — success:** GIVEN the threshold changed in its one place WHEN the statusline and the rule are read
THEN both show the new value.
**Scenario — error:** GIVEN a second literal threshold anywhere in the plugin WHEN the linter runs THEN it
fails.

### 6.6 REQ-W1-050 — Settings notice: definition and scope — AMENDS REQ-ADP-003
WHEN a session **starts** (not on resume, compact or clear) in a Karvey project — one with
`docs/spec/project.json` or `docs/spec/changes/`, found by walking up no further than the git top level —
AND `project.json` lacks non-empty `notifications` or `management` blocks (an empty object `{}` counts as
missing), the session hook SHALL print one informational line pointing to `/karvey:karvey-init --settings`;
WHERE the project is not a Karvey project, or the settings are present, the hook SHALL print nothing about
settings and exit 0; IF no interpreter is available to read `project.json`, THEN the hook SHALL print the
line in degraded form ("settings could not be read") rather than stay silent.

Traces to PRD: §6 S-6, S-13, O-11 · Sources: F-34 (S-06, E-10, I-04 spec side; E-09, E-11, N-11), BUG-02
code side already RESUELTO in 3.11.2 · **AMENDS REQ-ADP-003** · Modifies: REQ-TEAM-002

**Scenario — success:** GIVEN a repo with `docs/spec/changes/` and `"notifications": {}` WHEN a session starts
THEN one line is printed; on `resume` nothing is printed.
**Scenario — error:** GIVEN a non-Karvey repo with a bare `docs/spec/openapi.yaml` inside a parent that is a
Karvey project above the git top level WHEN a session starts THEN nothing is printed.

### 6.7 REQ-W1-051 — Hooks README matches hook behaviour
The hooks README SHALL describe each hook's output conditions as the hook implements them, and the plugin
linter SHALL check the documented silent/printing conditions against the guard tables.

Traces to PRD: §6 S-6, S-7, O-11 · Sources: BUG-16 / F-30 (C-18, E-12; text fixed in 3.11.2, no regression
check) · BL-09, BL-10

**Scenario — success:** GIVEN the 3.11.2 README exception sentence WHEN the linter compares it with the table
case "Karvey project without settings prints one line" THEN it passes.
**Scenario — error:** GIVEN README says "prints nothing" while a table case expects output WHEN the linter runs
THEN it fails.

## Requirement 7: The plugin as code (R-07)

### 7.1 REQ-W1-052 — No hand-kept rule copies
The plugin SHALL NOT contain hand-maintained copies of rule files; WHERE packaging requires copies, they
SHALL be generated at build time and the plugin linter SHALL fail when any copy differs from its source.

Traces to PRD: §6 S-7, O-8 · Sources: R-07, H-26 (9 copies), F-44 (C-19) → BL-10 · BL-10

**Scenario — success:** GIVEN no copies, or generated ones WHEN the linter runs THEN it passes.
**Scenario — error:** GIVEN a copy edited by hand WHEN the linter runs THEN it fails naming both paths.

### 7.2 REQ-W1-053 — Every referenced path resolves
Every file path cited by a skill, rule, hook or README SHALL resolve from the citing file's location or from
a declared plugin root, and the plugin linter SHALL fail on any unresolved reference.

Traces to PRD: §6 S-7, O-8 · Sources: R-07 (109 `karvey/rules/x.md` references; checkpoint/team/decisions
cite `rules/` without the folder), F-44 · BL-10

**Scenario — success:** GIVEN `karvey-checkpoint` citing a rule WHEN the linter resolves it THEN the file
exists.
**Scenario — error:** GIVEN a citation `rules/team.md` from a skill with no `rules/` folder and no declared
root WHEN the linter runs THEN it fails.

### 7.3 REQ-W1-054 — Linter in CI on every PR
WHEN a PR is opened or updated, the CI SHALL run the plugin linter and the guard tables and SHALL block the
merge when either fails.

Traces to PRD: §6 S-7, O-8, AC-4 · Sources: R-07, H-27 (only `close-external-prs.yml` today) · BL-10

**Scenario — success:** GIVEN a clean PR WHEN CI runs THEN the lint job passes.
**Scenario — error:** GIVEN a PR adding a skill without frontmatter WHEN CI runs THEN the PR is blocked.

### 7.4 REQ-W1-055 — Structural checks of the linter
The plugin linter SHALL check: frontmatter present and description length (REQ-W1-077); phase values in
skill text against the enum (REQ-W1-001); skill and rule counts in README and `plugin.json` against the
files; that `plugin.json`, `marketplace.json`, `project.json:karvey_version` and the top CHANGELOG release
agree; and `docs/spec/**/*.json` against the schemas.

Traces to PRD: §6 S-7, O-8 · Sources: R-07 · BL-10

**Scenario — success:** GIVEN 3.12.0 in all four places WHEN the linter runs THEN the version check passes.
**Scenario — error:** GIVEN README saying 32 skills while 33 exist WHEN the linter runs THEN it fails.

### 7.5 REQ-W1-056 — Tools used are declared
The plugin linter SHALL fail when a skill instructs an action whose tool is absent from that skill's
`allowed-tools` (at least `Write`, `Edit`, `AskUserQuestion`, `Bash`, `Agent`).

Traces to PRD: §6 S-7, O-8 · Sources: R-07, H-33 (`karvey-browse`, `karvey-health` lack `Write`; the
orchestrator lacks `Write`, `AskUserQuestion`) · BL-10

**Scenario — success:** GIVEN `karvey-health` with `Write` declared WHEN the linter runs THEN it passes.
**Scenario — error:** GIVEN a skill that writes `findings.md` without `Write` WHEN the linter runs THEN it fails.

### 7.6 REQ-W1-057 — Every artifact read is produced upstream
The plugin linter SHALL fail when a skill reads a change artifact that no earlier phase (per the
state-machine rule) produces.

Traces to PRD: §6 S-7, O-8 · Sources: R-07 (would have caught `proposal.md`), H-24 · BL-10

**Scenario — success:** GIVEN requirements reading `prd.md`, produced by init WHEN the linter runs THEN it passes.
**Scenario — error:** GIVEN a skill reading `proposal.md` WHEN the linter runs THEN it fails.

### 7.7 REQ-W1-058 — Release documentation in step with the version
The plugin linter SHALL fail when the top CHANGELOG release lacks its "Why" section (per
`changelog-policy.md`) or when the method page's version history does not include the plugin version marked
as current in every language block.

Traces to PRD: §6 S-7, S-13, O-11 · Sources: BUG-17 / F-31 (D6, C-21; fixed in 3.11.2, stays EN FIX until
this check exists) · BL-10

**Scenario — success:** GIVEN 3.12.0 with "Why" and the page history at 3.12.0 in 5 languages WHEN the linter
runs THEN it passes.
**Scenario — error:** GIVEN the page history topped at 3.11.2 while the badge says 3.12.0 WHEN the linter runs
THEN it fails naming the language block.

### 7.8 REQ-W1-059 — Minor consistency defects of H-33
The method SHALL have: one decision-log path cited by `rules/multi-agent.md` and `karvey-decisions`; no
`E{1..99}` literal in `karvey-init`; one copy of the "For each E2E flow step" block in `karvey-test`; the
README naming skills as `/karvey:karvey-<name>`; and each of these SHALL be a linter check.

Traces to PRD: §6 S-7, O-8 · Sources: R-07, H-33 · BL-10

**Scenario — success:** GIVEN the fixed texts WHEN the linter runs THEN the five checks pass.
**Scenario — error:** GIVEN README reintroducing `/karvey:grill` WHEN the linter runs THEN it fails.

### 7.9 REQ-W1-060 — Public text names the team's tracker
The README and the `plugin.json` description SHALL describe task tracking as the team's configured tracker,
naming ClickUp only as one of the supported tools.

Traces to PRD: §6 S-7, S-13, O-11 · Sources: BUG-07 / F-09 (C-05, C-06; README:52,117-119, plugin.json:4)

**Scenario — success:** GIVEN the 3.12.0 README and plugin.json WHEN read THEN no sentence presents ClickUp as
the default tracker.
**Scenario — error:** GIVEN "discovery backlog (Markdown + ClickUp)" in plugin.json WHEN the linter runs THEN it
fails.

## Requirement 8: Graphify and the tracker ritual out of the hot path (R-16)

### 8.1 REQ-W1-061 — `knowledge_sync: none` is valid and the default without graphify
The method SHALL accept `project.json:knowledge_sync` values `none | graphify | obsidian`, and WHERE the key
is absent and graphify is not detected, the method SHALL behave as `none` and say so once at init.

Traces to PRD: §6 S-8, O-9 · Sources: R-16 · BL-19

**Scenario — success:** GIVEN no graphify installed and no key WHEN init runs THEN it reports
`knowledge sync: none (graphify not detected)` and continues.
**Scenario — error:** GIVEN `knowledge_sync: "graph"` WHEN validated THEN the value is rejected.

### 8.2 REQ-W1-062 — Knowledge sync only at archive and on demand
The method SHALL run the knowledge sync only in archive and when the user asks for it; no other phase, and no
mockup iteration, SHALL run it.

Traces to PRD: §6 S-8, O-9 · Sources: R-16 (AG's option), H-31 · BL-19

**Scenario — success:** GIVEN a full cycle WHEN the skills are read by the linter THEN only archive (and an
explicit on-demand path) invokes the sync.
**Scenario — error:** GIVEN `karvey-mockup` still calling graphify per iteration WHEN the linter runs THEN it
fails.

### 8.3 REQ-W1-063 — Pending paths recorded between syncs
WHEN a file under `docs/spec/` is written, the method SHALL append its path to a pending-sync list, and the
next sync SHALL consume and empty that list.

Traces to PRD: §6 S-8, O-9 · Sources: R-16 (`.graph-pending`) · BL-19

**Scenario — success:** GIVEN three spec files written during impl WHEN archive syncs THEN those three paths
are synced and the list is empty.
**Scenario — error:** GIVEN the sync fails WHEN archive finishes THEN the list is kept and archive reports the
failure.

### 8.4 REQ-W1-064 — Tracker ritual per Feature
The method SHALL update the tracker status per task, and SHALL post the close comment and run the cascade
per Feature, not per task.

Traces to PRD: §6 S-8, O-9 · Sources: R-16 (4–6 calls per task, ~150 per Epic; `phase-close.md:10`) · BL-19

**Scenario — success:** GIVEN a Feature with 6 tasks WHEN they close THEN 6 status updates and 1 comment +
cascade are made.
**Scenario — error:** GIVEN phase-close text requiring a comment per task WHEN the linter runs THEN it fails.

## Requirement 9: Spec-delta merge tool (R-17, script only)

### 9.1 REQ-W1-065 — Deterministic spec-delta merge
WHEN the spec-merge tool runs on a change, the tool SHALL append every ADDED block to the capability's living
spec, replace every MODIFIED block by requirement id, remove every REMOVED block leaving a deprecation line,
and SHALL produce the same living spec when run twice.

Traces to PRD: §6 S-9 · Sources: R-17 (script of AG), BL-20

**Scenario — success:** GIVEN this change's delta WHEN the tool runs THEN the living spec contains the
REQ-W1-* blocks and the modified REQ-TEAM-* blocks.
**Scenario — error:** GIVEN a MODIFIED id not present in the living spec WHEN the tool runs THEN it writes
nothing and names the id.

### 9.2 REQ-W1-066 — Dry run
WHEN the spec-merge tool runs in dry-run mode, the tool SHALL print the resulting diff and SHALL NOT write any
file.

Traces to PRD: §6 S-9 · Sources: R-17 (`--dry-run`) · BL-20

**Scenario — success:** GIVEN a delta WHEN `--dry-run` runs THEN a diff is printed and the living spec is
unchanged.
**Scenario — error:** GIVEN a delta with an unparsable section WHEN `--dry-run` runs THEN it reports the line
and exits non-zero.

### 9.3 REQ-W1-067 — Archive uses the tool
WHEN archive merges a change's spec-delta, the archive skill SHALL do it with the spec-merge tool (dry run
shown first), not by hand.

Traces to PRD: §6 S-9 · Sources: R-17 (moment unchanged in Wave 1; "before prod" is Wave 2) · BL-20

**Scenario — success:** GIVEN archive WHEN it merges THEN the dry-run diff is shown and then applied.
**Scenario — error:** GIVEN the tool fails WHEN archive runs THEN archive stops before moving the folder.

## Requirement 10: Dashboard with open work, age and WIP (R-18)

### 10.1 REQ-W1-068 — Open work section
WHEN the dashboard runs, the dashboard SHALL show an OPEN WORK section with: findings by type and status per
change, every `BUG-NN` not `RESUELTO`, every `[human]` task in `awaiting-human` with its executor and since
when, every backlog item `open`, and every tracker operation pending reconciliation (REQ-W1-090).

Traces to PRD: §6 S-10, O-10 · Sources: R-18, H-30 · BL-21

**Scenario — success:** GIVEN this repo WHEN the dashboard runs THEN it lists BUG-05..BUG-17 not RESUELTO and
the team-adapters findings by type.
**Scenario — error:** GIVEN an unreadable `findings.md` WHEN the dashboard runs THEN it shows that file as
"unreadable" and still renders the rest.

### 10.2 REQ-W1-069 — Age and stalled flag
The dashboard SHALL show, per active change, the days in the current phase (from `phase_history`) and SHALL
flag it "stalled" when that exceeds the project's stall threshold (default 7 days).

Traces to PRD: §6 S-10, O-10, §11 A-2 · Sources: R-18 · BL-21

**Scenario — success:** GIVEN a change 9 days in `qa` WHEN the dashboard runs THEN it shows `9d stalled`.
**Scenario — error:** GIVEN a legacy change with no `phase_history` WHEN the dashboard runs THEN it shows the
age as unknown instead of 0.

### 10.3 REQ-W1-070 — All approvals, with who
The dashboard SHALL show every approval of every active change, from `requirements` to `prod`, with its
approver, role and date, or `skipped` with its reason.

Traces to PRD: §6 S-10, O-10 · Sources: R-18 (line ends at `tasks` today) · BL-21

**Scenario — success:** GIVEN this change WHEN the dashboard runs THEN it shows mockup and design_graphic as
`skipped: no UI`.
**Scenario — error:** GIVEN an approval with `approved: true` and no `by` WHEN the dashboard runs THEN it marks
it "approver missing".

### 10.4 REQ-W1-071 — WIP limit
WHERE `project.json:wip_limit` is set, the dashboard SHALL show the count of active changes against it and
SHALL warn when the count exceeds it.

Traces to PRD: §6 S-10, O-10 · Sources: R-18 · BL-21

**Scenario — success:** GIVEN `wip_limit: 3` and 2 active changes WHEN the dashboard runs THEN it shows `2/3`.
**Scenario — error:** GIVEN `wip_limit: 3` and 4 active WHEN the dashboard runs THEN it warns `WIP 4/3`.

### 10.5 REQ-W1-072 — Structured, read-only
The dashboard SHALL read JSON files as structured data (not by text matching) and SHALL NOT modify any file.

Traces to PRD: §6 S-10 · Sources: R-18 (`grep -o` parsing, `karvey-context/SKILL.md:75-77`) · BL-21

**Scenario — success:** GIVEN a `spec.json` with fields reordered and pretty-printed differently WHEN the
dashboard runs THEN it shows the same values.
**Scenario — error:** GIVEN the dashboard run WHEN `git status` is checked afterwards THEN no file changed.

## Requirement 11: QA observes without fixing; artifacts inside the change (R-21)

### 11.1 REQ-W1-073 — QA never commits
The QA skill SHALL NOT commit or edit product files; every defect it finds, including visual ones, SHALL be
appended to `findings.md` as a finding for `karvey-iterate` to route.

Traces to PRD: §6 S-11 · Sources: R-21, H-28 (`karvey-qa/SKILL.md:121` vs `:268`) · BL-24

**Scenario — success:** GIVEN a visual deviation WHEN QA runs THEN a `bug` finding is appended and no commit is
made.
**Scenario — error:** GIVEN QA text "apply atomic commits" WHEN the linter runs THEN it fails.

### 11.2 REQ-W1-074 — Review document inside the change
The QA skill SHALL write its review document to `docs/spec/changes/{change-id}/qa/REVISION_PR_*.md`, and the
deploy skill SHALL read the review of the change being deployed from that directory, never the newest file
in the repo root.

Traces to PRD: §6 S-11, AC-6 · Sources: R-21, H-29 (`ls -t` at root) · BL-24

**Scenario — success:** GIVEN two changes in QA WHEN deploy of change A runs THEN it reads
`changes/A/qa/REVISION_PR_*.md`.
**Scenario — error:** GIVEN no review under `changes/A/qa/` WHEN deploy of A runs THEN it stops with "no QA
review for A".

### 11.3 REQ-W1-075 — This repo's review moves into its change
The retroactive review `REVISION_PR_17-19_20260923.md` SHALL live under
`docs/spec/changes/team-adapters/qa/`, with every reference to it updated.

Traces to PRD: §6 S-11, S-13, AC-6 · Sources: R-21, H-29 · Decision: D-04

**Scenario — success:** GIVEN the moved file WHEN references are resolved by the linter THEN all resolve.
**Scenario — error:** GIVEN a leftover `REVISION_PR_*.md` at the repo root WHEN the linter runs THEN it fails.

### 11.4 REQ-W1-076 — Stack rules out of QA
The QA skill SHALL NOT contain rules specific to one team's stack (Axios/apiService, `v-html`, RUT); those
SHALL live in the standards and be evaluated in the standards-conformance dimension.

Traces to PRD: §6 S-11 · Sources: R-21 (`karvey-qa/SKILL.md:38-40,78`) · BL-24

**Scenario — success:** GIVEN a project whose standards declare the Axios rule WHEN QA D9 runs THEN the rule is
evaluated there.
**Scenario — error:** GIVEN a project with no standards WHEN QA runs THEN no Axios/RUT check appears and D9
says "not evaluated".

## Requirement 12: Short frontmatter descriptions, no generic triggers (R-22)

### 12.1 REQ-W1-077 — Description length and shape
Every skill description SHALL be at most 250 characters and SHALL state the phase or role, what it produces
and when to use it.

Traces to PRD: §6 S-12, O-12 · Sources: R-22, H-23 (12 skills listed without description; 13,907 chars total)
· BL-25

**Scenario — success:** GIVEN 32 skills WHEN the linter measures them THEN each is ≤250 characters.
**Scenario — error:** GIVEN a 273-character description WHEN the linter runs THEN it fails naming the skill.

### 12.2 REQ-W1-078 — No generic or third-party triggers
Skill trigger phrases SHALL carry the method context (e.g. "karvey deploy", "karvey qa") and SHALL NOT include
bare generic words (`deploy`, `QA`, `code review`) or third-party product names.

Traces to PRD: §6 S-12, O-12 · Sources: R-22 (collisions with the user's `deploy` skill and built-in
`code-review`; 10 repeated phrases in karvey/grill/init) · BL-25

**Scenario — success:** GIVEN the triggers WHEN the linter checks them against the deny list THEN none match.
**Scenario — error:** GIVEN a trigger "gstack" or "Garry Tan" WHEN the linter runs THEN it fails.

### 12.3 REQ-W1-079 — Rarely used skills are not model-invoked
The skills `karvey-guard`, `karvey-team`, `karvey-benchmark-models`, `karvey-scrape`, `karvey-import` and
`karvey-retro` SHALL be invocable only by the user, not selected by the model.

Traces to PRD: §6 S-12, O-12 · Sources: R-22 (`disable-model-invocation: true`) · BL-25

**Scenario — success:** GIVEN the six skills WHEN their frontmatter is linted THEN each disables model
invocation.
**Scenario — error:** GIVEN one of them without the flag WHEN the linter runs THEN it fails.

## Requirement 13: Tracker adapters converged from team-adapters

### 13.1 REQ-W1-080 — Missing status map resolved wherever a status changes — AMENDS REQ-ADP-022
WHEN a run is about to make its first status change, every skill that creates tracker items or changes a status
(`init`, `tasks`, `impl`, `qa`, `deploy`, `iterate`, `archive`, phase-close) SHALL apply the one
missing-map resolution clause of the management-adapters rule: resolve the tool and location (REQ-W1-086),
read the real statuses of that location from the tool, propose the mapping, confirm it with the human and
persist it; IF the location itself is missing, THEN the skill SHALL ask for it and SHALL NOT pick one.

Traces to PRD: §6 S-13, O-11 · Sources: F-05 (I-01, widened by N-02, N-03, N-06) · **AMENDS REQ-ADP-022** ·
Relates: CHANGELOG 3.10.0 claim toned down

**Scenario — success:** GIVEN `management: {tool: clickup, location: 901…}` without `statuses` WHEN tasks runs
THEN it reads the list's statuses, proposes the map, confirms and persists before creating the first task.
**Scenario — error:** GIVEN `tool: jira` and no `location` WHEN impl would set a status THEN it asks for the
project key and changes no status meanwhile.

### 13.2 REQ-W1-081 — No human, no persisted mapping — AMENDS REQ-ADP-022
IF the missing-map resolution runs where no human can answer (a subagent, a headless run), THEN the skill
SHALL NOT persist any mapping, SHALL fall back to `PLAN.md` for that run and SHALL report it; subagents SHALL
NOT write `project.json`; the map SHALL be resolved as a precondition of the tasks gate.

Traces to PRD: §6 S-13, O-11 · Sources: F-12 (N-02) · **AMENDS REQ-ADP-022**

**Scenario — success:** GIVEN a headless impl run with no map WHEN it would set a status THEN it writes
`PLAN.md`, reports "status map unresolved — no human", and `project.json` is unchanged.
**Scenario — error:** GIVEN a subagent that tries to write `project.json` WHEN it runs THEN the instruction set
forbids it and the linter finds no subagent prompt that allows it.

### 13.3 REQ-W1-082 — Per-level maps, unsupported states, no workflow edits — AMENDS REQ-ADP-022
The status map SHALL allow one map per level or per list, SHALL accept `null` for a logical state the
tracker cannot represent, SHALL re-map a single entry when a mapped status disappears, and the method SHALL
NOT create or edit the team's workflow states.

Traces to PRD: §6 S-13, O-11 · Sources: F-14 (N-06) · **AMENDS REQ-ADP-022**

**Scenario — success:** GIVEN `blocked: null` WHEN a task becomes blocked THEN the skill keeps the tracker
status, adds a comment and records `blocked` in `PLAN.md`.
**Scenario — error:** GIVEN a mapped status deleted in the tool WHEN a skill sets it THEN it asks to re-map only
that entry and does not create the status.

### 13.4 REQ-W1-083 — Settings travel as a reviewed change — AMENDS REQ-ADP-001, REQ-ADP-022
WHEN settings or a status map are persisted, the method SHALL commit them on a feature or docs branch
(docs-PR lane) and say that they take effect after merge; BEFORE declaring settings missing, the session hook
and the skills SHALL check `project.json` on `origin/{integration}` as well as the working copy.

Traces to PRD: §6 S-13, O-11 · Sources: F-13 (N-03) · **AMENDS REQ-ADP-001, REQ-ADP-022**

**Scenario — success:** GIVEN settings merged on `origin/main` but a worktree created earlier WHEN a session
starts in the worktree THEN no settings notice is printed.
**Scenario — error:** GIVEN HEAD on the integration branch WHEN settings would be committed THEN the git-flow
guard blocks it and the skill proposes a docs branch.

### 13.5 REQ-W1-084 — Who moves leaf items to `done` — AMENDS REQ-ADP-021
WHEN `approvals.qa.approved` becomes `true`, the QA skill SHALL set to `done` every Task and Feature of the
change that is in `review`; WHEN archive runs, it SHALL verify that none remains in `review` and SHALL list any
that does; the management-adapters rule SHALL list QA and archive under `set_status` "Used by".

Traces to PRD: §6 S-13, O-11 · Sources: F-06 (C-02, I-12) · **AMENDS REQ-ADP-021**

**Scenario — success:** GIVEN 8 tasks in `review` WHEN QA approves THEN all 8 are `done` in the tracker (or ✅ in
PLAN.md).
**Scenario — error:** GIVEN one task still `review` at archive WHEN archive runs THEN it lists that task and does
not mark the Epic `done`.

### 13.6 REQ-W1-085 — impl selects and resumes in logical states
WHEN impl selects the next task, the impl skill SHALL pick the first `todo` task or an orphan `in_progress`
task whose dependencies are all at `review` or `done`, SHALL read task state from one declared source (the
team's tracker, or `PLAN.md` for Markdown) and SHALL report any drift between that source and `tasks.md`.

Traces to PRD: §6 S-13, O-11 · Sources: BUG-05 / F-07 (N-08) · Satisfies REQ-ADP-021 as written

**Scenario — success:** GIVEN [DB] tasks at `review` WHEN impl resumes THEN the first [Backend] `todo` task
starts.
**Scenario — error:** GIVEN a task `in_progress` in `PLAN.md` and `todo` in the tracker WHEN impl resumes THEN it
reports the drift and uses the declared source.

### 13.7 REQ-W1-086 — One resolution order for tracker settings — AMENDS REQ-ADP-023
The method SHALL resolve the tracker tool, location and statuses in one order, stated once in the
management-adapters rule and cited by every skill: the change's `spec.json` override `{tool, location,
statuses}` first, then `project.json:management`; the tracker-ids block (`spec.json:clickup`, kept under its
historical name) SHALL be documented there and SHALL include `task_ids`.

Traces to PRD: §6 S-13, O-11 · Sources: F-15 (C-04, N-07), F-36 (C-09) · **AMENDS REQ-ADP-023**

**Scenario — success:** GIVEN a change tracked on a client's board via its `spec.json` override WHEN tasks,
impl, qa and deploy run THEN all four use the override's location and statuses.
**Scenario — error:** GIVEN a skill that reads `project.json:clickup.backlog_list_id` directly WHEN the linter
runs THEN it fails.

### 13.8 REQ-W1-087 — "Is there a tracker" is one test on both shapes
WHEN a skill decides whether to create or link a tracker item, the skill SHALL use the resolved tool of
REQ-W1-086, accepting a legacy string or an object, and SHALL treat `markdown` (and its alias `none`) as "no
external tracker".

Traces to PRD: §6 S-13, O-11 · Sources: BUG-06 / F-08 (`karvey-iterate:61`, `rules/backlog.md:10`) · Relates:
REQ-W1-010

**Scenario — success:** GIVEN `"management": "markdown"` (legacy string) WHEN iterate routes a finding THEN no
tracker item is attempted.
**Scenario — error:** GIVEN the text "`management.tool` != markdown" in any skill or rule WHEN the linter runs
THEN it fails.

### 13.9 REQ-W1-088 — Legacy `none` and optional sprints — AMENDS REQ-ADP-020, REQ-ADP-023
The management tool enum SHALL keep `clickup | jira | linear | azure-boards | github-projects | spreadsheet |
markdown | other` and SHALL accept `none` as a documented legacy alias of `markdown`; `management` SHALL
accept an optional `sprints` value (folder, iteration or cycle) used by the skills that file work into a
sprint.

Traces to PRD: §6 S-13, O-11 · Sources: F-40 (I-11; 9 files), F-41 (I-13) · **AMENDS REQ-ADP-020,
REQ-ADP-023**

**Scenario — success:** GIVEN `spec.json:management = "none"` WHEN validated THEN it passes with a "legacy alias"
warning.
**Scenario — error:** GIVEN `management.sprints` absent WHEN QA files a task THEN it files it in `location`
without guessing a sprint.

### 13.10 REQ-W1-089 — Idempotent creation (find-or-create)
WHEN a skill creates a tracker item, the skill SHALL first search for an item with the same natural key
(`E{n}`, `E{n}.F{n}`, `E{n}.F{n}.T{n}`, `F-NN`, `BUG-NN`, `[Deploy] {change-id}@{version}`) and reuse it, and
SHALL store the item's id in `spec.json`; a re-run SHALL create no duplicate.

Traces to PRD: §6 S-13, O-11 · Sources: F-17 (N-05, re-typed from bug to spec-gap) · Amends:
management-adapters operations

**Scenario — success:** GIVEN tasks already created WHEN `karvey-tasks` is re-run THEN no new task is created and
the ids are unchanged.
**Scenario — error:** GIVEN two items with the same key in the tracker WHEN a skill searches THEN it stops and
asks which one is canonical.

### 13.11 REQ-W1-090 — Tracker outbox reconciled
IF a tracker operation fails and the skill falls back to `PLAN.md`, THEN the skill SHALL record the operation
in a pending outbox of the change, the next phase-close SHALL retry it, and the skill SHALL NOT create a child
item under a parent that does not exist in the tracker.

Traces to PRD: §6 S-13, O-11 · Sources: F-16 (N-04) · Amends: management-adapters rule 4

**Scenario — success:** GIVEN a failed `set_status` WHEN the next phase-close runs with the tracker reachable
THEN it is applied and removed from the outbox.
**Scenario — error:** GIVEN the Epic creation failed WHEN tasks would create Features THEN it queues them instead
of creating them without a parent.

### 13.12 REQ-W1-091 — One cascade — AMENDS REQ-ADP-021
The management-adapters rule SHALL define the one cascade — Features to `review` move the Epic to `review` at
impl; the Epic reaches `done` only at archive — and phase-close, the ClickUp protocol and impl SHALL cite it
instead of restating it.

Traces to PRD: §6 S-13, O-11 · Sources: F-18 (C-01) · **AMENDS REQ-ADP-021**

**Scenario — success:** GIVEN all Features at `review` WHEN impl closes THEN the Epic is `review`, not `done`.
**Scenario — error:** GIVEN a rule saying "Epic → done when all features are" WHEN the linter compares cascade
statements THEN it fails.

### 13.13 REQ-W1-092 — `awaiting-human` is a qualifier — AMENDS REQ-ADP-021
The method SHALL define `awaiting-human` (🙋) as a qualifier of a task, mapped to the logical state `blocked`,
and every marker legend SHALL list it.

Traces to PRD: §6 S-13, O-11 · Sources: F-19 (C-07) · **AMENDS REQ-ADP-021**

**Scenario — success:** GIVEN a `[human]` task waiting WHEN its status is set THEN the tracker shows `blocked`
plus the `awaiting-human` tag, and dependents only are held.
**Scenario — error:** GIVEN a legend with the five markers and no 🙋 WHEN the linter runs THEN it fails.

### 13.14 REQ-W1-093 — Values validated before use in commands — AMENDS REQ-ADP-010, REQ-ADP-020
WHEN a value from `project.json` (`notifications.target`, `management.location`, status names) is about to
be used in a command, the method SHALL validate it against the channel's or tool's pattern, SHALL refuse shell
metacharacters, SHALL pass it as a quoted argument, and SHALL refuse a spreadsheet path outside `docs/spec/`.

Traces to PRD: §6 S-13, O-11, §9 (Tier 2) · Sources: F-10 (S-01, command-injection half) · **AMENDS
REQ-ADP-010, REQ-ADP-020**

**Scenario — success:** GIVEN `location: "PAY"` for Jira WHEN a command is built THEN it passes validation and is
quoted.
**Scenario — error:** GIVEN `target: "spaces/AAA; rm -rf ~"` WHEN QA would notify THEN it refuses and reports the
invalid target.

### 13.15 REQ-W1-094 — phase-close scope matches its citations
The phase-close rule SHALL name exactly the phase skills that run it, and every phase skill it names SHALL
cite it at its close.

Traces to PRD: §6 S-13, O-11 · Sources: F-37 (C-11; "every phase" vs 3 skills citing it)

**Scenario — success:** GIVEN the rule's list WHEN compared with the skills' citations THEN they are equal.
**Scenario — error:** GIVEN a skill named by the rule without the close step WHEN the linter runs THEN it fails.

### 13.16 REQ-W1-095 — init consistency around the settings step — AMENDS REQ-ADP-001, REQ-ADP-002
`karvey-init` SHALL state that Step 3 does not re-ask `project.json` fields while Step 3.2 may still ask the
team settings; SHALL use one initial Epic state for every tool; SHALL print a `Settings:` line in its final
output; and SHALL persist a "not now" answer (as `notifications.channel: "none"` or an explicit deferred
marker) so the question is not repeated.

Traces to PRD: §6 S-13, O-11 · Sources: F-39 (C-20, I-14) · **AMENDS REQ-ADP-001, REQ-ADP-002**

**Scenario — success:** GIVEN the user answers "not now" to notifications WHEN init runs again THEN it does not ask
notifications again and says how to set them.
**Scenario — error:** GIVEN init creating the Spreadsheet Epic as `todo` and the PLAN.md Epic as `in_progress`
WHEN the linter compares them THEN it fails.

### 13.17 REQ-W1-096 — `--settings` merge semantics (verification of 3.11.2) — AMENDS REQ-ADP-002
WHEN `karvey-init --settings` runs, the skill SHALL run only the team-settings step, pre-fill every question
with the current values, merge the answers without dropping untouched keys (`events`, `location`, custom
keys), write `project.json`, report one line and stop, creating no change and no tracker item.

Traces to PRD: §6 S-13, O-11 · Sources: F-01 (N-01, N-09) → BUG-01 **RESUELTO in 3.11.2** (verified:
`plugins/karvey/skills/karvey-init/SKILL.md` Step 0, lines 16-25; `CHANGELOG.md` [3.11.2] line 8;
regression `plugins/karvey/hooks/tests/test-hooks.sh`) · **AMENDS REQ-ADP-002** (records the implemented
behaviour in the requirement; no new work beyond a manual test of agent behaviour)

**Scenario — success:** GIVEN `notifications.events = ["qa","deploy","incident"]` WHEN the user changes only the
channel THEN `events` is unchanged.
**Scenario — error:** GIVEN `--settings` WHEN it finishes THEN `docs/spec/changes/` has no new directory and no
tracker item exists.

## Requirement 14: Notifications converged from team-adapters

### 14.1 REQ-W1-097 — Destination changes are confirmed — AMENDS REQ-ADP-011
The method SHALL refuse a `notifications.target` containing `://`, and WHEN `project.json:notifications`
changed since the last send, the skill SHALL show the destination and ask for confirmation before sending.

Traces to PRD: §6 S-13, O-11, §9 (Tier 2) · Sources: F-32 (S-01 redirection half, N-07) · **AMENDS
REQ-ADP-011**

**Scenario — success:** GIVEN an unchanged destination WHEN QA notifies THEN it sends without asking.
**Scenario — error:** GIVEN `target` changed in the last commit WHEN QA would notify THEN it shows the new
destination and waits for confirmation.

### 14.2 REQ-W1-098 — QA notices carry counts by default — AMENDS REQ-ADP-011
The `qa` notification SHALL carry, by default, the count of findings per severity and a link to the review;
WHERE `notifications.detail` is `full`, it SHALL carry the findings' titles.

Traces to PRD: §6 S-13, O-11, §9 (Tier 2) · Sources: F-33 (S-08) · **AMENDS REQ-ADP-011**

**Scenario — success:** GIVEN no `detail` key WHEN QA notifies THEN the message has counts and a link only.
**Scenario — error:** GIVEN `detail: "verbose"` WHEN validated THEN the value is rejected and `counts` is used.

### 14.3 REQ-W1-099 — Destinations only from project.json; migration aid allowed — AMENDS REQ-ADP-012
The method SHALL NOT use at send time a notification destination that is not in `project.json`; during the
team-settings step it MAY propose a destination seen in the session's context, and SHALL persist it only
after the human's explicit confirmation; the 3.12.0 CHANGELOG SHALL carry a compatibility line for projects
that relied on `CLAUDE.md` tables.

Traces to PRD: §6 S-13, O-11 · Sources: F-11 (I-06, N-14; 20 of 22 HainTech repos silent) · **AMENDS
REQ-ADP-012**

**Scenario — success:** GIVEN a space id visible in context WHEN `--settings` runs THEN it is proposed and, once
confirmed, written to `project.json`.
**Scenario — error:** GIVEN no `notifications` block WHEN QA would notify THEN it skips the notice, says so, and
does not read any `CLAUDE.md` table.

## Requirement 15: Statusline and method-page defects converged from team-adapters

### 15.1 REQ-W1-100 — Invalid time zone is visible
IF `KARVEY_TZ` is not a valid zone, THEN the statusline SHALL show the reset time in the system zone with a
visible `(TZ?)` marker, and SHALL resolve the zone once per run.

Traces to PRD: §6 S-13, O-11 · Sources: BUG-08 / F-22 (S-04, E-05)

**Scenario — success:** GIVEN `KARVEY_TZ=America/Santiago` WHEN the statusline runs THEN no marker is shown.
**Scenario — error:** GIVEN `KARVEY_TZ=Mars/Olympus` WHEN it runs THEN the time carries `(TZ?)`.

### 15.2 REQ-W1-101 — Limit windows joined without stray separators
The statusline SHALL join the present rate-limit windows with ` · ` and SHALL print no separator before the
first one.

Traces to PRD: §6 S-13, O-11 · Sources: BUG-09 / F-23 (E-06)

**Scenario — success:** GIVEN only the 7-day window WHEN it runs THEN the text is `limit 7d 29% …`.
**Scenario — error:** GIVEN both windows WHEN it runs THEN exactly one ` · ` separates them.

### 15.3 REQ-W1-102 — Malformed hash is ignored
IF the method page's URL hash cannot be decoded, THEN the page SHALL ignore it and still bind the language
switch.

Traces to PRD: §6 S-13, O-11 · Sources: BUG-10 / F-24 (S-07, E-15)

**Scenario — success:** GIVEN `#en-phases` WHEN the page loads THEN it scrolls to the section.
**Scenario — error:** GIVEN `#%E0%A4%A` WHEN the page loads and DE is clicked THEN the language changes without a
reload and no error is thrown.

### 15.4 REQ-W1-103 — Only a valid `?lang=` is remembered; one-off vs saved — AMENDS REQ-ADP-031
The method page SHALL remember a language only when the URL value is one of the five supported ones (a
`xx-YY` value is read by its first two letters in both scripts), and a `?lang=` from a shared link SHALL apply
to that visit without overwriting a language the viewer saved before; `zh-TW` and `zh-HK` SHALL resolve to the
Chinese block with the page stating it is Simplified.

Traces to PRD: §6 S-13, O-11 · Sources: BUG-11 / F-25 (E-14), F-35 (E-17) · **AMENDS REQ-ADP-031**

**Scenario — success:** GIVEN a viewer who saved `de` WHEN they open a link with `?lang=es` THEN the page shows
Spanish and the saved choice stays `de`.
**Scenario — error:** GIVEN `?lang=xx` WHEN the page loads THEN nothing is saved and the browser language rule
applies.

### 15.5 REQ-W1-104 — Other query parameters preserved
WHEN the viewer switches language, the method page SHALL change only the `lang` parameter and SHALL keep every
other query parameter.

Traces to PRD: §6 S-13, O-11 · Sources: BUG-12 / F-26 (E-16)

**Scenario — success:** GIVEN `?foo=1&lang=es` WHEN DE is clicked THEN the URL is `?foo=1&lang=de`.
**Scenario — error:** GIVEN no query WHEN DE is clicked THEN the URL is `?lang=de` with no empty parameter.

### 15.6 REQ-W1-105 — Hash changes after load
WHEN the URL hash changes after load, the method page SHALL map it to the visible language block and jump to
it, as it does at load.

Traces to PRD: §6 S-13, O-11 · Sources: BUG-13 / F-27 (E-18)

**Scenario — success:** GIVEN Spanish shown WHEN `#en-foo` is clicked THEN the page jumps to the Spanish
equivalent.
**Scenario — error:** GIVEN a hash with no equivalent WHEN it changes THEN the page stays where it is without an
error.

### 15.7 REQ-W1-106 — No inert language switch without JavaScript
WHERE JavaScript is disabled, the method page SHALL NOT show a language switch that does nothing; English SHALL
still render.

Traces to PRD: §6 S-13, O-11 · Sources: BUG-14 / F-28 (N-12)

**Scenario — success:** GIVEN JavaScript disabled WHEN the page loads THEN English renders and the switch is
hidden (or replaced by a note).
**Scenario — error:** GIVEN JavaScript disabled WHEN the guard table inspects the static markup THEN no visible
switch link is present.

## Requirement 16: Convergence and dogfooding (D-04)

### 16.1 REQ-W1-107 — Every routed incident reaches RESUELTO with a regression test
WHEN this change reaches QA convergence, every incident BUG-05..BUG-17 SHALL be `RESUELTO` in
`docs/bugs_dev_testing.md` and `docs/spec/incidents-index.md`, each with a regression test or linter check
named in its entry.

Traces to PRD: §6 S-13, O-11, AC-5 · Sources: `rules/incident-tracking.md` (RESUELTO needs a regression
test), BUG-05..BUG-17 · Decision: D-04

**Scenario — success:** GIVEN BUG-17 WHEN the linter check of REQ-W1-058 exists and passes THEN BUG-17 moves to
RESUELTO citing it.
**Scenario — error:** GIVEN BUG-16 fixed in text but with no check WHEN convergence is evaluated THEN it stays
EN FIX and convergence is not reached.

### 16.2 REQ-W1-108 — team-adapters converges here
WHEN this change reaches QA convergence, `docs/spec/changes/team-adapters/findings.md` SHALL have no `open` or
`routed` item of type `bug` or `spec-gap`, and the amended REQ-ADP-* SHALL be in this change's spec-delta.

Traces to PRD: §6 S-13, O-11, AC-5 · Sources: `rules/iteration-loop.md` (convergence) · Decision: D-04

**Scenario — success:** GIVEN every F-05..F-41 bug/spec-gap closed against a REQ-W1 WHEN convergence is evaluated
THEN it passes.
**Scenario — error:** GIVEN F-14 still `routed` WHEN convergence is evaluated THEN it fails naming F-14.

### 16.3 REQ-W1-109 — The method's own specs validate
WHEN 3.12.0 is released, every `spec.json` and `project.json` under this repo's `docs/spec/` SHALL pass
validation with no error, and this change's own phases SHALL have been recorded by the state tool from the
moment it exists.

Traces to PRD: §6 S-1, O-1, AC-1 · Sources: R-01, H-22 · Decision: D-04

**Scenario — success:** GIVEN the release commit WHEN `validate` runs on `docs/spec/` THEN 0 errors.
**Scenario — error:** GIVEN this change's `phase_history` missing a phase it went through WHEN validated THEN it
reports the gap.

---

## Explicit exclusions

- **Lanes** (R-09), **fused gates** and `-y` recorded as `role: auto` (R-10), **judges** (R-11), **release per
  change** with a `Karvey-Change` trailer (R-08), **test-first traceability** (R-12), **security tools**
  (R-13), **metrics/DORA** beyond writing `phase_history` (R-14), **release-gate / id / health scripts**
  (R-20), **post-deploy thresholds** (R-23): Wave 2 (BL-11..BL-17, BL-23, BL-26). This change only records
  `lane` and `skipped` as data (REQ-W1-007) — it does not decide lanes.
- **Moving the spec-delta merge before prod** (R-17 timing): Wave 2. Wave 1 ships the tool only.
- **Design-graphic self-approval (H-05) and `-y` without `by/role/ref` (H-06)**: R-10, Wave 2. REQ-W1-006
  refuses an approval without those fields when recorded through the state tool; the flag's semantics change
  in Wave 2.
- **Hotfix lane preconditions (H-04)**: R-09, Wave 2.
- **Emergent team-adapters findings** F-21, F-42, F-45..F-48 → BL-38..BL-43 stay in the backlog. F-43 and F-44
  are covered through BL-07 / BL-10 (REQ-W1-036, REQ-W1-052/053).
- **ID collisions (H-35)**: not reproduced; R-20, Wave 2.
- **The owner's global `~/.claude/CLAUDE.md`**: its plan-marker rule changes because of D-01, but that edit is
  outside this repo, shown to the owner as a diff, and not a requirement of this change.
- **Migrating other repos' `project.json`** (the 16 HainTech repos, Tarien): the state tool provides `--fix`
  (REQ-W1-010); running it in each repo belongs to each repo's own docs PR.
- **Behaviour that does not change:** the bug/spec-gap/emergent router, the Iron Law, "prod never delegated",
  the logical states and adapters, EARS + PRD traceability, and every item of the panel's §5 "do not change".

## Revision history

| Rev | Date | Ref | Requirements | Why |
|---|---|---|---|---|
| 1 | 2026-09-26 | D-34, D-35, D-36 · F-76, F-77, F-79 (QA spec-gaps) | REQ-W1-017 (audit record of the marker), REQ-W1-023 (evidence = the hook's audit record; approval bound to the approved head commit, valid 24 h; reopen supersedes it) | QA of PR #24 found that the prod gate accepted any `approvals/…` string as evidence, that one approval released any later commit forever, and that a reopen left the prod approval standing. Rewritten in place; ripple: spec-delta, architecture revision 4 (§3.3, §3.4), tasks E1.F18. Done without a state `reopen` because the change stays in `qa` and the owner decided the three gaps directly (D-21 standing instruction). |
