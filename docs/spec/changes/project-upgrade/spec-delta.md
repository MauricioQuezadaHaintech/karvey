# Spec Delta: project-upgrade

Against the living spec `docs/spec/specs/method/spec.md` (capability `method`). Scenarios for every block are
in `requirements.md`; the living spec keeps the compact form it already uses. `karvey-archive` merges this
file with `karvey-spec-merge`.

Summary: **ADDED 32** (REQ-UP-001..032) · **MODIFIED 0** · **REMOVED 0**. The existing settings notice and
REQ-W1-045..047 (session bounds) are unchanged: the offer lives inside those bounds (REQ-UP-006).

## ADDED Requirements

### ADDED by `project-upgrade` (release after 3.12.0)

Traced to `docs/spec/changes/project-upgrade/prd.md` · Decision D-20.

### The once-per-version offer
- **REQ-UP-001** — Seen version is recorded per clone. The session hook SHALL keep, per clone, the last installed version for which the offer was resolved (accepted, declined or found empty — an offer shown but unanswered is not resolved) in the seen-version record, which SHALL live outside the working tree and SHALL be shared by every worktree of the clone. *(Traces: PRD §Goal · Decision: D-20 («A cada persona, por clon»))*
- **REQ-UP-002** — Offer on a version change. WHEN a session **starts** (not resume/compact/clear) in a Karvey project, IF the installed version differs from the seen-version record or the record is absent, THEN the session hook SHALL instruct the agent to ask the person, as a single question with a recommended option, whether they want a project upgrade plan for `<seen> → <installed>` (or `→ <installed>` when absent), and SHALL NOT itself change any project file. *(Traces: PRD §Goal · Decision: D-20 (verbatim: «cada vez que alguien actualiza, que le pregunte si quiere refrescar su proyecto con un plan de actualización»))*
- **REQ-UP-003** — Silent outside Karvey projects. IF the start directory is not inside a Karvey project, THEN the session hook SHALL emit no upgrade offer and SHALL NOT create a seen-version record. *(Traces: PRD §Goal · REQ-TEAM-002, REQ-W1-050 (same project test as the settings notice))*
- **REQ-UP-004** — A decline lasts until the next version. WHEN the person declines the offer, the method SHALL record the installed version as seen, and the session hook SHALL NOT offer again until the installed version changes. *(Traces: PRD §Goal · Decision: D-20)*
- **REQ-UP-005** — No offer when nothing applies. IF the plan for the project has no applicable step, THEN the session hook SHALL NOT show the offer and SHALL record the installed version as seen. *(Traces: PRD §Goal, §Key idea · Interpretation of D-20 to be confirmed at this gate (an offer with an empty plan is noise))*
- **REQ-UP-006** — The offer never costs the session. The session hook SHALL keep the upgrade offer within its existing output and time bounds (one offer line plus one instruction; REQ-W1-045..047), SHALL NOT fetch from any remote to decide it, and IF anything in the offer path fails, THEN it SHALL still start the session and report the failure in at most one line. *(Traces: PRD §Goal · REQ-W1-045..047 · Tier 2)*

### The plan
- **REQ-UP-007** — The plan is computed from the project's state. WHEN the upgrade tool computes a plan, it SHALL evaluate every step of the step catalogue against the current state of the project and list exactly the steps whose check finds something to do, regardless of which version the project came from. *(Traces: PRD §Key idea)*
- **REQ-UP-008** — Every step is declared, not improvised. Each step in the step catalogue SHALL declare an id, the version that introduced it, its check, its fix (or that it has none), whether it can dry-run, whether it needs a human, and its risk (`low` | `medium` | `high`); IF a step lacks any of them, THEN the upgrade tool SHALL refuse to load the catalogue and name the step and the field. *(Traces: PRD §Goal · checkpoint plan item 2 (AG-10: deterministic, the skill only relays))*
- **REQ-UP-009** — Plan output for people and for the agent. The upgrade tool SHALL print the plan as a table (step · what changes · dry-run · risk · needs human) and, with `--json`, as one machine-readable document carrying the same information plus the from/to versions. *(Traces: PRD §Goal)*
- **REQ-UP-010** — Computing a plan writes nothing. The upgrade tool SHALL NOT write, move or delete any file (in the project, in the clone's git dir, or under the user's home) when computing a plan. *(Traces: PRD §Goal ("dry-run first"))*

### Applying the plan
- **REQ-UP-011** — Only the steps the person picked. WHEN the upgrade tool applies a plan, it SHALL apply only the step ids passed to it; IF an id is unknown or not applicable, THEN it SHALL refuse before changing anything and name the id. *(Traces: PRD §Goal ("applies only what the person approves"))*
- **REQ-UP-012** — Dry-run before every apply. WHEN a step that supports dry-run is applied, the method SHALL show its dry-run result to the person before the write; `apply --dry-run` SHALL show every selected step's result and write nothing. *(Traces: PRD §Goal)*
- **REQ-UP-013** — On the upgrade branch, never on integration or production. WHEN the upgrade tool applies steps, it SHALL do so on the upgrade branch created from the project's integration branch; IF the current branch is the integration or the production branch, THEN it SHALL switch to the upgrade branch before writing, and it SHALL NOT commit on integration or production. *(Traces: PRD §Goal ("on a branch, through one PR") · owner's global rules · D-03, D-15)*
- **REQ-UP-014** — Idempotent. WHEN `apply` runs twice with the same steps on the same project, the second run SHALL report "nothing to do" for every step and SHALL change no file. *(Traces: PRD §Key idea)*
- **REQ-UP-015** — Human steps are shown, never done. IF a step is declared as needing a human, THEN the upgrade tool SHALL print what the person must do (and the diff, when there is one) and SHALL NOT perform it; the step SHALL stay in the plan until its check passes. *(Traces: PRD §Out of scope · Decisions: D-01, D-11)*
- **REQ-UP-016** — Nothing under the user's home is written. The upgrade tool SHALL NOT write any file outside the project's working tree and the clone's git dir. *(Traces: PRD §Out of scope · Decisions: D-01, D-11)*
- **REQ-UP-017** — A failure stops cleanly. IF a step fails while applying, THEN the upgrade tool SHALL stop, leave every file it was writing either fully old or fully new, and report which steps were applied, which failed (with the reason) and which were not run. *(Traces: PRD §Goal)*
- **REQ-UP-018** — One PR per upgrade. WHEN the upgrade skill finishes applying, it SHALL commit the applied steps on the upgrade branch naming each step id, and SHALL open (or offer to open, where the project has no PR tooling) one PR to the integration branch; it SHALL NOT merge it. *(Traces: PRD §Goal ("through one PR"))*
- **REQ-UP-019** — Project values are data. The upgrade tool SHALL treat every value read from the project (branch names, paths, settings) as data and SHALL NOT evaluate it as a command; IF a value used to build a branch name or path fails validation, THEN it SHALL refuse the step and name the value's source. *(Traces: PRD §Goal · Security Tier 2 (`spec.json:security_tier_reason`))*

### The initial step catalogue
- **REQ-UP-020** — Schema migration. The step catalogue SHALL contain a step that applies the state tool's existing migration of `spec.json` and `project.json` legacy shapes, and applies the proposed-tier migrations only when the person selects them separately. *(Traces: PRD §Problem · REQ-W1-003 (`validate --fix`), D-09)*
- **REQ-UP-021** — Missing team settings. The step catalogue SHALL contain a step that detects missing or legacy team settings (management, notifications) and proposes the settings block, applied to `project.json` only with the person's values. *(Traces: PRD §Problem · existing settings notice (`propose-settings`), REQ-W1-083)*
- **REQ-UP-022** — Legacy hook shims copied into the repo. The step catalogue SHALL contain a step that detects copies of the deprecated `plan-gate` / `git-flow-guard` shims and their `.claude/settings.json` entries in the project, and replaces them with the equivalent `project.json:enforcement` flags. *(Traces: PRD §Problem · wave1 architecture §7.4, `rules/enforcement.md`)*
- **REQ-UP-023** — Statusline on a stable path. The step catalogue SHALL contain a human step that detects a statusline command pointing to a versioned plugin path (or to no Karvey statusline) and shows the stable command to use instead. *(Traces: PRD §Problem · F-51, BL-36, BL-41)*
- **REQ-UP-024** — Changes in flight are reported, never reprocessed. The step catalogue SHALL contain a report-only step that lists changes in flight whose recorded phases do not satisfy the installed version's gates, and SHALL NOT modify those changes; archived changes SHALL NOT be reported. *(Traces: PRD §Out of scope ("re-running gates of changes in flight") · D-14)*
- **REQ-UP-025** — Global configuration as diffs. The step catalogue SHALL contain a human step that compares the Karvey-related parts of the user's global configuration with what the installed version recommends and shows the diff. *(Traces: PRD §Out of scope · D-01, D-11)*
- **REQ-UP-026** — New standards and enforcement. The step catalogue SHALL contain a step that lists the `project.json:enforcement` keys and project standards the installed version adds and the project does not declare, proposing the version's defaults. *(Traces: PRD §Problem ("new standards/controls never reach the project"))*

### The upgrade skill
- **REQ-UP-027** — The skill relays the tool. The upgrade skill SHALL obtain the plan and every apply result from the upgrade tool and SHALL NOT compute, add or skip steps itself. *(Traces: PRD §Goal · checkpoint plan item 2 (AG-10))*
- **REQ-UP-028** — The person picks, the method records. WHEN the upgrade skill presents a non-empty plan, it SHALL let the person pick the steps (with the low-risk ones recommended) and SHALL record who picked them, when, and the selected ids in the upgrade commit. *(Traces: PRD §Goal · checklist (approvals recorded verbatim))*
- **REQ-UP-029** — Reachable without the offer. The upgrade skill SHALL be invocable at any time, independently of the offer, and SHALL behave the same way. *(Traces: PRD §Goal)*

### Every release declares its upgrade
- **REQ-UP-030** — Linter check L-37. WHEN a release changes a schema, a rule, a hook, a default or a project setting's meaning, the plugin linter SHALL fail unless the step catalogue has a step whose introducing version is that release, or the release's CHANGELOG entry declares "no project upgrade needed" with a reason. *(Traces: PRD §Goal ("every time") · checkpoint plan item 5 · REQ-W1 plugin linter)*
- **REQ-UP-031** — The catalogue is linted. The plugin linter SHALL validate the step catalogue against REQ-UP-008 (fields), REQ-UP-010 (read-only checks) and REQ-UP-016 (no non-human writes outside the project). *(Traces: PRD §Goal)*
- **REQ-UP-032** — Documented where people look. The method SHALL document the offer, the upgrade skill and the release rule in the plugin README (upgrade section), the hooks README (the offer) and the release's CHANGELOG entry. *(Traces: PRD §Goal)*

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
