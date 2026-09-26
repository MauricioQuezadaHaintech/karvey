# Requirements: project-upgrade

## Project description

Updating the Karvey plugin changes skills, rules and hooks, but nothing brings an existing **project** up to
the new method: legacy `spec.json` / `project.json` shapes, hook shims copied into the repo, a statusline on a
versioned path and new standards stay behind unless someone knows which command to run (PRD §Problem). This
change makes every update end in an offer: the first session after a version change, in a Karvey project,
asks **once per clone** whether the person wants a **project upgrade plan**; the plan is computed from the
project's state, shown dry-run first, and only the steps the person picks are applied, on a branch, through
one PR (PRD §Goal, D-20).

## Conventions

- **IDs.** `REQ-UP-NNN`, numbered contiguously; the heading also carries the numeric EARS id (`1.1`…).
- **Trace line.** PRD section (`§Problem`, `§Goal`, `§Owner's decisions`, `§Key idea`, `§Out of scope`),
  decision `D-NN`, finding `F-NN`, backlog `BL-NN`, and the wave1 requirement it builds on (`REQ-W1-NNN`).
- **Technology.** SHALL texts name roles; public names the owner already fixed are in the glossary. The
  file formats, languages and hook mechanics are architecture decisions.
- **Security Tier 2** (`spec.json:security_tier_reason`): clone-local state is written by a hook and project
  files are rewritten by a script; Requirement 3.9 and 1.6 carry the tier's controls.

### Glossary — roles and their public names

| Role in the requirements | Public name (fixed by D-20 / the init plan) |
|---|---|
| the **session hook** | `hooks/karvey-session-context.sh` (existing, REQ-W1-045..047) |
| the **seen-version record** | `<git-common-dir>/karvey/seen-version` (clone-local, never committed) |
| the **upgrade tool** | `scripts/karvey-upgrade` (`plan`, `apply`, `--json`, `--dry-run`) |
| the **step catalogue** | `scripts/karvey_lib/upgrade-steps.json` |
| the **upgrade skill** | `/karvey-upgrade` |
| the **upgrade branch** | `chore/karvey-upgrade-<version>` |
| the **plugin linter** | `scripts/lint-plugin` (existing, new check `L-37`) |
| the **installed version** | `version` of the loaded plugin's `plugin.json` |
| **Karvey project** | the existing test: `docs/spec/project.json` file or `docs/spec/changes/` directory under the git top level |

---

## Requirement 1: The once-per-version offer

### 1.1 REQ-UP-001 — Seen version is recorded per clone
The session hook SHALL keep, per clone, the last installed version for which the offer was resolved (accepted,
declined or found empty — an offer shown but unanswered is not resolved) in the seen-version record, which SHALL live outside the working tree and
SHALL be shared by every worktree of the clone.

Traces to PRD: §Goal · Decision: D-20 («A cada persona, por clon»)

#### Scenario: Success
GIVEN a clone where the offer for 3.13.0 was resolved in the main working copy
WHEN a session starts on 3.13.0 in a worktree of the same clone
THEN no offer is shown and `git status` shows no new file.

#### Scenario: Error
GIVEN the seen-version record cannot be written (read-only git dir)
WHEN the session hook resolves the offer
THEN the session starts normally and the hook's output says in one line that the offer will repeat next session.

### 1.2 REQ-UP-002 — Offer on a version change
WHEN a session **starts** (not resume/compact/clear) in a Karvey project, IF the installed version differs from
the seen-version record or the record is absent, THEN the session hook SHALL instruct the agent to ask the
person, as a single question with a recommended option, whether they want a project upgrade plan for
`<seen> → <installed>` (or `→ <installed>` when absent), and SHALL NOT itself change any project file.

Traces to PRD: §Goal · Decision: D-20 (verbatim: «cada vez que alguien actualiza, que le pregunte si quiere refrescar su proyecto con un plan de actualización»)

#### Scenario: Success
GIVEN seen-version `3.12.0` and installed `3.13.0` in a Karvey project with applicable steps
WHEN a session starts
THEN the hook's context contains exactly one upgrade-offer instruction naming `3.12.0 → 3.13.0`.

#### Scenario: Error
GIVEN the same project
WHEN the session is a `resume` or `compact`
THEN no offer instruction is emitted and the seen-version record is unchanged.

### 1.3 REQ-UP-003 — Silent outside Karvey projects and outside git
IF the start directory is not inside a Karvey project, or the Karvey project is not in a git repository, THEN
the session hook SHALL emit no upgrade offer and SHALL NOT create a seen-version record.

Traces to PRD: §Goal · REQ-TEAM-002, REQ-W1-050 (same project test as the settings notice) · F-27 (rev. 2:
outside git there is no clone to record the answer in, and the upgrade needs a branch — REQ-UP-013)

#### Scenario: Success
GIVEN a git repo with no `docs/spec/project.json` and no `docs/spec/changes/`
WHEN a session starts on a new version
THEN the hook output is identical to today's and no `karvey/seen-version` exists in its git dir.

#### Scenario: Error
GIVEN a directory with a bare `docs/spec/` (no project.json, no changes/), or a Karvey project that is not in a
git repository
WHEN a session starts
THEN no offer is emitted and nothing is written, neither in the directory nor under the user's home.

### 1.4 REQ-UP-004 — A decline lasts until the next version
WHEN the person declines the offer, the method SHALL record the installed version as seen, and the session
hook SHALL NOT offer again until the installed version changes.

Traces to PRD: §Goal · Decision: D-20

#### Scenario: Success
GIVEN the person answered "no" on 3.13.0
WHEN they start ten more sessions on 3.13.0
THEN none of them shows the offer; the first session on 3.13.1 shows it.

#### Scenario: Error
GIVEN the session ended before the person answered (no answer recorded)
WHEN the next session starts on 3.13.0
THEN the offer is shown again (an unanswered offer is not a decline).

### 1.5 REQ-UP-005 — No offer when nothing applies
IF the plan for the project has no applicable step, THEN the session hook SHALL NOT show the offer and SHALL
record the installed version as seen.

Traces to PRD: §Goal, §Key idea · Interpretation of D-20 to be confirmed at this gate (an offer with an empty plan is noise) ·
reachable for a project without a statusline (REQ-UP-023 rev. 2, F-21) and for one created by the project
initialisation (REQ-UP-026 rev. 2, F-23)

#### Scenario: Success
GIVEN a project created with `karvey-init` on the installed version
WHEN the first session starts
THEN no offer is shown and seen-version equals the installed version.

#### Scenario: Error
GIVEN the plan cannot be computed within the hook's time bound
WHEN the session starts
THEN the offer is shown (the hook does not guess "nothing applies") and the plan is computed when the person accepts.

### 1.6 REQ-UP-006 — The offer never costs the session
The session hook SHALL keep the upgrade offer within its existing output and time bounds (one offer line plus
one instruction; REQ-W1-045..047), SHALL NOT fetch from any remote to decide it, and SHALL bound the probe
that decides it: project files above a size cap are not read, directory walks skip dependency and nested
repository trees and check the time bound as they go, and the hook stops waiting for the probe at the bound
(the offer is then shown, as in REQ-UP-005's error scenario). IF anything in the offer path fails, THEN it
SHALL still start the session and report the failure in at most one line.

Traces to PRD: §Goal · REQ-W1-045..047 · Tier 2 · F-25 (rev. 2: a huge file or tree could cost the whole
startup context up to the hook timeout)

#### Scenario: Success
GIVEN a Karvey project with a board of 40 rows and a handoff at its byte limit
WHEN a session starts on a new version
THEN the offer is present and the other sections are bounded exactly as before.

#### Scenario: Error
GIVEN the step catalogue is missing or malformed in the installed plugin, or a check that blocks past the time
bound
WHEN a session starts
THEN the session starts within the bound plus a fixed grace; a bad catalogue gives one line `[karvey] upgrade offer unavailable: <reason>`, a blocked check gives the offer, and seen-version is unchanged.

---

## Requirement 2: The plan

### 2.1 REQ-UP-007 — The plan is computed from the project's state
WHEN the upgrade tool computes a plan, it SHALL evaluate every step of the step catalogue against the current
state of the project and list exactly the steps whose check finds something to do, regardless of which
version the project came from.

Traces to PRD: §Key idea

#### Scenario: Success
GIVEN two copies of the same legacy fixture, one with seen-version 3.0.0 and one with 3.11.4
WHEN `plan` runs on each
THEN both plans list the same steps.

#### Scenario: Error
GIVEN a project where every check passes
WHEN `plan` runs
THEN it reports "nothing to do" and exits 0.

### 2.2 REQ-UP-008 — Every step is declared, not improvised
Each step in the step catalogue SHALL declare an id, the version that introduced it, its check, its fix (or
that it has none), whether it can dry-run, whether it needs a human, and its risk (`low` | `medium` |
`high`); IF a step lacks any of them, THEN the upgrade tool SHALL refuse to load the catalogue and name the
step and the field.

Traces to PRD: §Goal · checkpoint plan item 2 (AG-10: deterministic, the skill only relays)

#### Scenario: Success
GIVEN a catalogue where every step has the seven fields
WHEN `plan` runs
THEN each listed step shows id, what changes, dry-run availability and risk.

#### Scenario: Error
GIVEN a step without `risk`
WHEN `plan` runs
THEN it exits non-zero with `step <id>: missing field risk` and evaluates nothing.

### 2.3 REQ-UP-009 — Plan output for people and for the agent
The upgrade tool SHALL print the plan as a table (step · what changes · dry-run · risk · needs human) and,
with `--json`, as one machine-readable document carrying the same information plus the from/to versions.

Traces to PRD: §Goal

#### Scenario: Success
GIVEN a plan with three applicable steps
WHEN `plan --json` runs
THEN the document has three entries whose ids match the table rows.

#### Scenario: Error
GIVEN a check that raises an unexpected error
WHEN `plan` runs
THEN that step is listed with state `check failed: <reason>`, the other steps are still evaluated, and the exit status is non-zero.

### 2.4 REQ-UP-010 — Computing a plan writes nothing
The upgrade tool SHALL NOT write, move or delete any file (in the project, in the clone's git dir, or under
the user's home) when computing a plan.

Traces to PRD: §Goal ("dry-run first")

#### Scenario: Success
GIVEN a legacy fixture
WHEN `plan` runs
THEN a checksum of the working tree, the git dir and the fixture home is unchanged.

#### Scenario: Error
GIVEN a step whose check would need to write to decide
WHEN the catalogue is linted
THEN the linter rejects the step (checks are read-only by contract).

---

## Requirement 3: Applying the plan

### 3.1 REQ-UP-011 — Only the steps the person picked
WHEN the upgrade tool applies a plan, it SHALL apply only the step ids passed to it; IF an id is unknown or
not applicable, THEN it SHALL refuse before changing anything and name the id.

Traces to PRD: §Goal ("applies only what the person approves")

#### Scenario: Success
GIVEN a plan listing `schema-migrate`, `legacy-shims`, `statusline-launcher`
WHEN `apply --steps schema-migrate,legacy-shims` runs
THEN only those two steps change files.

#### Scenario: Error
GIVEN the same plan
WHEN `apply --steps schema-migrate,no-such-step` runs
THEN nothing changes and the output names `no-such-step`.

### 3.2 REQ-UP-012 — Dry-run before every apply
WHEN a step that supports dry-run is applied, the method SHALL show its dry-run result to the person before
the write; `apply --dry-run` SHALL show every selected step's result and write nothing, and SHALL preview the
tree `apply` writes: off the upgrade branch, IF the current tree differs from the tree the upgrade branch
starts from, THEN it SHALL refuse and name the command that creates the upgrade branch.

Traces to PRD: §Goal · F-24 (rev. 2: a dry-run on a local integration branch ahead of its remote previewed a
tree `apply` never writes)

#### Scenario: Success
GIVEN `schema-migrate` selected
WHEN `apply --dry-run --steps schema-migrate` runs
THEN the unified diff of every file it would change is printed and no file changes.

#### Scenario: Error
GIVEN a step declared `dry-run: no`
WHEN it is selected
THEN the plan and the skill mark it "no preview" and the skill asks for a separate confirmation before applying it.

### 3.3 REQ-UP-013 — On the upgrade branch, never on integration or production
WHEN the upgrade tool applies steps, it SHALL do so on the upgrade branch created from the project's
integration branch — or, IF another clone already pushed the upgrade branch of the same version (known from
local refs), from that remote upgrade branch, saying that a PR for it may already be open; IF the current
branch is the integration or the production branch, THEN it SHALL switch to the upgrade branch before writing,
and it SHALL NOT commit on integration or production.

Traces to PRD: §Goal ("on a branch, through one PR") · owner's global rules · D-03, D-15 · F-08 (rev. 2: the
offer is per clone, the branch per version; a second clone's push was rejected as non-fast-forward)

#### Scenario: Success
GIVEN a project on `dev` with integration `dev`
WHEN `apply` runs for 3.13.0
THEN the changes are on `chore/karvey-upgrade-3.13.0` and `dev` has no new commit.

GIVEN a second clone where `origin/chore/karvey-upgrade-3.13.0` (pushed by the first clone) is fetched
WHEN `branch` and `apply` run there
THEN the branch starts from the remote upgrade branch, the steps the first clone applied are "nothing to do",
and the push of the new commit is a fast-forward.

#### Scenario: Error
GIVEN the working tree has uncommitted changes
WHEN `apply` runs
THEN it refuses, names the dirty paths, and changes nothing.

### 3.4 REQ-UP-014 — Idempotent
WHEN `apply` runs twice with the same steps on the same project, the second run SHALL report "nothing to do"
for every step and SHALL change no file.

Traces to PRD: §Key idea

#### Scenario: Success
GIVEN a legacy fixture after one full apply
WHEN `plan` runs
THEN it lists none of the applied steps.

#### Scenario: Error
GIVEN a step that would change a file on the second run
WHEN the unit suite runs
THEN the idempotency test for that step fails.

### 3.5 REQ-UP-015 — Human steps are shown, never done
IF a step is declared as needing a human, THEN the upgrade tool SHALL print what the person must do (and the
diff, when there is one) and SHALL NOT perform it; the step SHALL stay in the plan until its check passes.

Traces to PRD: §Out of scope · Decisions: D-01, D-11

#### Scenario: Success
GIVEN the global-config step applies
WHEN it is selected
THEN the output shows the diff for `~/.claude/settings.json` and the file is byte-identical afterwards.

#### Scenario: Error
GIVEN a human step selected with `--yes`
WHEN `apply` runs
THEN it is still not performed and the output says it needs the person.

### 3.6 REQ-UP-016 — Nothing under the user's home is written
The upgrade tool SHALL NOT write any file outside the project's working tree and the clone's git dir; for a
project outside git it SHALL record nothing (the seen-version record lives only in a clone's git dir).

Traces to PRD: §Out of scope · Decisions: D-01, D-11 · F-27 (rev. 2: outside git the record fell back to a
state directory under the home)

#### Scenario: Success
GIVEN every step selected on a fixture with a fixture home
WHEN `apply` runs
THEN the fixture home is byte-identical afterwards.

#### Scenario: Error
GIVEN a catalogue step whose fix targets a path under the home
WHEN the catalogue is loaded
THEN it is refused as a non-human step writing outside the project.

### 3.7 REQ-UP-017 — A failure stops cleanly
IF a step fails while applying, THEN the upgrade tool SHALL stop, leave every file it was writing either fully
old or fully new, and report which steps were applied, which failed (with the reason) and which were not run.

Traces to PRD: §Goal

#### Scenario: Success
GIVEN three steps where the second one fails
WHEN `apply` runs
THEN step 1 is applied, step 2 is reported failed with its reason, step 3 is reported not run, and no file is half-written.

#### Scenario: Error
GIVEN the failure happens after step 1 wrote files
WHEN the person re-runs `plan`
THEN step 1 is no longer listed and steps 2 and 3 are.

### 3.8 REQ-UP-018 — One PR per upgrade
WHEN the upgrade skill finishes applying, it SHALL commit the applied steps on the upgrade branch naming each
step id, and SHALL open (or offer to open, where the project has no PR tooling) one PR to the integration
branch; it SHALL NOT merge it.

Traces to PRD: §Goal ("through one PR")

#### Scenario: Success
GIVEN two steps applied
WHEN the skill finishes
THEN one commit lists both step ids and one PR targets the integration branch.

#### Scenario: Error
GIVEN the push is rejected
WHEN the skill finishes
THEN the commit stays on the local branch and the skill reports the push failure and the exact command to retry.

### 3.9 REQ-UP-019 — Project values are data
The upgrade tool SHALL treat every value read from the project (branch names, paths, settings) as data and
SHALL NOT evaluate it as a command; IF a value used to build a branch name or path fails validation, THEN it
SHALL refuse the step and name the value's source.

Traces to PRD: §Goal · Security Tier 2 (`spec.json:security_tier_reason`)

#### Scenario: Success
GIVEN `branch_flow.integration` = `dev`
WHEN `apply` runs
THEN the upgrade branch is created from `dev`.

#### Scenario: Error
GIVEN `branch_flow.integration` = `dev; rm -rf ~`
WHEN `apply` runs
THEN it refuses with `invalid branch name in project.json:branch_flow.integration` and nothing runs.

---

## Requirement 4: The initial step catalogue

### 4.1 REQ-UP-020 — Schema migration
The step catalogue SHALL contain a step that applies the state tool's existing migration of `spec.json` and
`project.json` legacy shapes, and applies the proposed-tier migrations only when the person selects them
separately; archived changes SHALL NOT be migrated (they are history, D-14).

Traces to PRD: §Problem · REQ-W1-003 (`validate --fix`), D-09 · D-14 · F-22 (rev. 2: the migration rewrote
archived `spec.json` files while REQ-UP-024 and the exclusions keep the archive untouched)

#### Scenario: Success
GIVEN a fixture with `approvals: null` and a string `management`, and an archived change with legacy shapes
WHEN the step is applied
THEN both are migrated, the archived `spec.json` is byte-identical, and a second `plan` no longer lists it.

#### Scenario: Error
GIVEN a `spec.json` with an unmappable phase
WHEN the step is applied
THEN it fails for that file with the state tool's reason, and the other files are migrated.

### 4.2 REQ-UP-021 — Missing team settings
The step catalogue SHALL contain a step that detects missing or legacy team settings (management,
notifications) and proposes the settings block, applied to `project.json` only with the person's values.

Traces to PRD: §Problem · existing settings notice (`propose-settings`), REQ-W1-083

#### Scenario: Success
GIVEN a `project.json` without `notifications`
WHEN `plan` runs
THEN the step is listed with the proposed block as its preview.

#### Scenario: Error
GIVEN a proposal that still holds a `<tool location>` placeholder
WHEN apply is attempted
THEN it refuses until the person supplies the value.

### 4.3 REQ-UP-022 — Legacy hook shims copied into the repo
The step catalogue SHALL contain a step that detects copies of the deprecated `plan-gate` / `git-flow-guard`
shims and their `.claude/settings.json` entries in the project, and replaces them with the equivalent
`project.json:enforcement` flags.

Traces to PRD: §Problem · wave1 architecture §7.4, `rules/enforcement.md`

#### Scenario: Success
GIVEN `.claude/hooks/plan-gate.sh` and its settings entry in the project
WHEN the step is applied
THEN both are removed, `enforcement.plan_gate_hook` is `true`, and the guard tables still pass on the fixture.

#### Scenario: Error
GIVEN a shim copy that differs from any shipped version (locally edited)
WHEN `plan` runs
THEN the step is listed as needing a human, with the diff against the shipped shim.

### 4.4 REQ-UP-023 — Statusline on a stable path
The step catalogue SHALL contain a human step that detects a Karvey statusline command pointing to a versioned
plugin path and shows the stable command to use instead. A project without any statusline, or with the
person's own, SHALL NOT make the step applicable: the plan only notes that the stable command is available.

Traces to PRD: §Problem · F-51, BL-36, BL-41 · F-21 (rev. 2: "no statusline" was a human result, so the
usual person got the offer on every version and REQ-UP-005 was unreachable)

#### Scenario: Success
GIVEN a user settings statusline `…/karvey/3.11.2/hooks/karvey-statusline.sh`
WHEN `plan` runs
THEN the step is listed with the stable replacement command.

#### Scenario: Error
GIVEN a statusline that is not Karvey's (e.g. the person's own script), or no statusline at all
WHEN `plan` runs
THEN the step is reported as "own statusline, left as is" (or "no statusline: optional …") and not listed as applicable.

### 4.5 REQ-UP-024 — Changes in flight are reported, never reprocessed
The step catalogue SHALL contain a report-only step that lists changes in flight whose recorded phases do not
satisfy the installed version's gates, and SHALL NOT modify those changes; archived changes SHALL NOT be
reported.

Traces to PRD: §Out of scope ("re-running gates of changes in flight") · D-14

#### Scenario: Success
GIVEN one change in `impl` with no `approvals.tasks` and one archived change in the same state
WHEN `plan` runs
THEN only the first is listed, with the unmet gate.

#### Scenario: Error
GIVEN the report-only step selected for apply
WHEN `apply` runs
THEN no `spec.json` changes and the step prints its report again.

### 4.6 REQ-UP-025 — Global configuration as diffs
The step catalogue SHALL contain a human step that compares the Karvey-related parts of the user's global
configuration with what the installed version recommends and shows the diff.

Traces to PRD: §Out of scope · D-01, D-11

#### Scenario: Success
GIVEN a global settings file without the recommended `KARVEY_COMPAT_MARKER`
WHEN `plan` runs
THEN the step shows the one-line diff.

#### Scenario: Error
GIVEN the global settings file is unreadable
WHEN `plan` runs
THEN the step is reported `check failed: unreadable` and the rest of the plan is computed.

### 4.7 REQ-UP-026 — New standards and enforcement
The step catalogue SHALL contain a step that lists the `project.json:enforcement` keys and project standards
the installed version adds and the project does not declare, proposing the version's defaults. The project
initialisation SHALL declare every enforcement default of the installed version, so that a project created on
that version does not list this step.

Traces to PRD: §Problem ("new standards/controls never reach the project") · F-23 (rev. 2: a project created by
the initialisation got the offer on its first session, contradicting REQ-UP-005's success scenario)

#### Scenario: Success
GIVEN a project without `enforcement.prod_gate`
WHEN `plan` runs
THEN the step lists `prod_gate` with its default.

#### Scenario: Error
GIVEN a project that set a key explicitly to a non-default value
WHEN `plan` runs
THEN that key is not listed (an explicit choice is not overwritten).

---

## Requirement 5: The upgrade skill

### 5.1 REQ-UP-027 — The skill relays the tool
The upgrade skill SHALL obtain the plan and every apply result from the upgrade tool and SHALL NOT compute,
add or skip steps itself.

Traces to PRD: §Goal · checkpoint plan item 2 (AG-10)

#### Scenario: Success
GIVEN `plan --json` lists four steps
WHEN the skill presents the plan
THEN it shows exactly those four rows.

#### Scenario: Error
GIVEN the upgrade tool is not found in the installed plugin
WHEN the skill runs
THEN it stops and says so; it does not attempt the steps by hand.

### 5.2 REQ-UP-028 — The person picks, the method records
WHEN the upgrade skill presents a non-empty plan, it SHALL let the person pick the steps (with the low-risk
ones recommended) and SHALL record who picked them, when, and the selected ids in the upgrade commit.

Traces to PRD: §Goal · checklist (approvals recorded verbatim)

#### Scenario: Success
GIVEN the person picks two of four steps
WHEN the commit is created
THEN its message names the two ids and the person.

#### Scenario: Error
GIVEN the person picks none
WHEN the skill ends
THEN no branch or commit is created and seen-version is recorded (a decline).

### 5.3 REQ-UP-029 — Reachable without the offer
The upgrade skill SHALL be invocable at any time, independently of the offer, and SHALL behave the same way.

Traces to PRD: §Goal

#### Scenario: Success
GIVEN seen-version equals the installed version
WHEN `/karvey-upgrade` runs
THEN the plan is computed and presented.

#### Scenario: Error
GIVEN a directory that is not a Karvey project
WHEN `/karvey-upgrade` runs
THEN it says so and exits without writing.

---

## Requirement 6: Every release declares its upgrade

### 6.1 REQ-UP-030 — Linter check L-37
WHEN a release changes a schema, a rule, a hook, a default or a project setting's meaning, the plugin linter
SHALL fail unless the step catalogue has a step whose introducing version is that release, or the release's
CHANGELOG entry declares "no project upgrade needed" with a reason.

Traces to PRD: §Goal ("every time") · checkpoint plan item 5 · REQ-W1 plugin linter

#### Scenario: Success
GIVEN a release that changes `schemas/project.schema.json` and adds a step with `since` equal to it
WHEN CI runs the linter
THEN L-37 passes.

#### Scenario: Error
GIVEN a release that changes a hook and neither adds a step nor declares "no project upgrade needed"
WHEN CI runs the linter
THEN L-37 fails naming the changed files and the release.

### 6.2 REQ-UP-031 — The catalogue is linted
The plugin linter SHALL validate the step catalogue against REQ-UP-008 (fields), REQ-UP-010 (read-only
checks) and REQ-UP-016 (no non-human writes outside the project); the read-only check SHALL hold under import
aliases, method-style file opens and the tools a step reaches through the read-only view.

Traces to PRD: §Goal · F-26 (rev. 2: the scan missed `Path.open("w")`, `os.open`, aliases and the state /
config tools' writers)

#### Scenario: Success
GIVEN the shipped catalogue
WHEN the linter runs
THEN it reports 0 errors for the catalogue.

#### Scenario: Error
GIVEN a step whose fix writes under the home and is not marked human
WHEN the linter runs
THEN it fails naming the step.

### 6.3 REQ-UP-032 — Documented where people look
The method SHALL document the offer, the upgrade skill and the release rule in the plugin README (upgrade
section), the hooks README (the offer) and the release's CHANGELOG entry.

Traces to PRD: §Goal

#### Scenario: Success
GIVEN the release
WHEN a person reads the README's upgrade section
THEN it states when they are asked, how to decline, and how to run the plan by hand.

#### Scenario: Error
GIVEN the release omits the hooks README text
WHEN the linter's doc checks run
THEN the missing section is reported.

---

## Explicit exclusions

- **Upgrading the plugin itself** (`claude plugin update`) — out of scope (PRD §Out of scope).
- **Re-running gates of changes in flight** — reported only (REQ-UP-024); archived changes are history (D-14).
- **Writing anything under `~/.claude/`** — diffs only, the owner applies (D-01, D-11; REQ-UP-015/016).
- **Shipping in 3.12.0** — this change ships in the release right after 3.12.0 (D-20); 3.12.0 does not wait for it.
- **Committed "seen" state** — the seen-version record is per clone and never committed (D-20).
- **Merging the upgrade PR** — the skill opens it; merging stays with the project's normal review.
- **Fetching remotes to decide the offer** — the hook decides from local state only (REQ-UP-006).
- **Behaviour of the existing settings notice** — unchanged; the offer is additional to it.

---

## Revision history

Revisions are made by `karvey-iterate` from `findings.md`; each rewrites the affected requirement in place (no
contradicting text is appended). Under D-21 the recommended option of each spec-gap was taken without asking; the
owner reviews this list.

| Date | Rev. | Finding | Requirements | Option taken | Reason |
|---|---|---|---|---|---|
| 2026-09-25 | 1 | — | REQ-UP-001..032 | — | First version (D-21). |
| 2026-09-26 | 2 | F-21 | REQ-UP-023 (REQ-UP-005 trace) | "no statusline" is `nothing` with a note (not: optional human hints ignored by the hook only) | One rule for plan and hook; a missing statusline is a choice, not debt, so an empty plan is reachable. |
| 2026-09-26 | 2 | F-22 | REQ-UP-020 | the migration leaves `docs/spec/changes/archive/` out | D-14 and E-22 already say archived history is untouched; the step was the one contradiction. |
| 2026-09-26 | 2 | F-23 | REQ-UP-026 (REQ-UP-005 trace) | the initialisation writes every enforcement default (not: the step ignores absent keys) | Keeps the step useful for real gaps and makes a new project current; a test ties the init block to the schema defaults. |
| 2026-09-26 | 2 | F-24 | REQ-UP-012 | off the upgrade branch, a dry-run whose tree differs from the branch's base is refused, naming `branch` (not: dry-run on a temporary checkout of the base) | Cheapest way to keep "the preview is what apply writes" without touching the working tree. |
| 2026-09-26 | 2 | F-25 | REQ-UP-006 | size cap on project reads, pruned and deadline-checked walks, a watchdog thread in the hook | Bounds the worst case at the budget plus a fixed grace instead of the 10 s hook timeout. |
| 2026-09-26 | 2 | F-26 | REQ-UP-031 | extend the scan: aliases, `.open()` write modes, `os.open`, and an allow-list of the state / config tools' read functions | Makes "read-only by construction" hold for the cases the review found. |
| 2026-09-26 | 2 | F-27 | REQ-UP-003, REQ-UP-016 | outside git: no offer and no record (not: allow the home state dir and guard it) | The record is per clone and the upgrade needs a branch (E-12); nothing is written under the home. |
| 2026-09-26 | 2 | F-08 | REQ-UP-013 | base the branch on the remote upgrade branch when it exists locally, and say a PR may be open (not: a clone-unique suffix) | One PR per upgrade (REQ-UP-018) instead of one per clone; the second push becomes a fast-forward. |
