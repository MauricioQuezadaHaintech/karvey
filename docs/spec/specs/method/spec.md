# Living spec — capability `method`

Cumulative requirements of the Karvey Method itself. Each block records the change that ADDED it.

## ADDED by `team-layer` (3.8.0, archived 2026-09-23)

Traced to `prd.md`.

### Optionality (PRD §3, §5)

- **REQ-TEAM-001** — WHERE no team configuration exists (`docs/spec/team.json` or a legacy
  `.ceo-agentes`), THE method SHALL behave exactly as before this change, and no phase or gate SHALL
  require the team layer.
- **REQ-TEAM-002** — WHEN the session hook runs on a project with no agent profile and no team configuration,
  THE hook SHALL print nothing and exit 0, except the one-line settings notice of REQ-W1-050 when that
  requirement's conditions hold.
- **REQ-TEAM-003** — WHEN `karvey-team init` is invoked, THE skill SHALL present the measured cost of
  the reference run and obtain confirmation BEFORE writing any file.
- **REQ-TEAM-004** — THE team rule SHALL state, before its configuration section, the conditions under
  which a team SHALL NOT be used.

### Handoff (PRD §4)

- **REQ-TEAM-010** — WHEN `karvey-checkpoint save` runs, THE skill SHALL write the change checkpoint
  AND the agent handoff, **whether or not a team is configured**: at `docs/spec/agent/handoff.md` for a
  single agent, or at `{ops_repo}/agents/<role>/handoff.md` when a team is.
- **REQ-TEAM-010b** — WHERE no agent profile exists yet, THE skill SHALL create it during the save
  (manifest, board, checklist, handoff) rather than failing or skipping the handoff.
- **REQ-TEAM-010c** — THE handoff SHALL carry, besides repository state: who the agent is and what is
  not theirs, the standing rules **referenced with their commit** rather than copied, the board of open
  items, and the closing checklist.
- **REQ-TEAM-010d** — WHEN the handoff is written, THE method SHALL write `state.json` beside it by running
  the handoff capture, which measures the branch, commit and uncommitted count of each owned repo; a repo
  that cannot be measured SHALL be recorded as "not measured" with its reason; the agent SHALL NOT write
  `state.json` by hand.
- **REQ-TEAM-011** — THE handoff's state section SHALL be the output of commands; IF a claim of "done"
  cannot be verified in that session, THEN it SHALL be recorded as unverified with its reason.
- **REQ-TEAM-012** — THE handoff SHALL record every scheduled task with its full prompt.
- **REQ-TEAM-013** — WHEN the handoff is committed to a shared ops repo, THE skill SHALL commit by
  explicit path (`git commit -- <paths>`) and SHALL NOT stage other paths.
- **REQ-TEAM-014** — WHEN `karvey-checkpoint restore` runs, THE skill SHALL contrast the handoff
  against the real repository state and SHALL report that the handoff has aged BEFORE presenting its
  content as current.
- **REQ-TEAM-014b** — WHEN a session starts, resumes, compacts or is cleared AND an agent profile exists, THE
  session hook SHALL reinject identity, the compact **or** the full manifest (never both), at most 40 open
  board rows, the checklist and at most 6 KB of handoff (saying what was truncated), through the harness's
  structured context channel; SHALL compare `state.json` against the live repositories; and SHALL instruct
  the session to run `/karvey-checkpoint restore` before anything else when there is an active change —
  excluding `changes/archive/` and changes with `IMPLEMENTED` — drift, or no handoff.
- **REQ-TEAM-014c** — WHERE `state.json` is absent or unreadable, THE hook SHALL state that nothing was
  measured and that the handoff's claims are unverified.
- **REQ-TEAM-015** — THE method SHALL NOT allow an agent to rotate itself or another agent; on reaching the
  rotation threshold — one value defined in one place and read by the statusline, the team rule, the
  checkpoint skill and the hooks README — THE agent SHALL write the handoff, commit it, report readiness,
  and continue working normally.
- **REQ-TEAM-016** — IF the checkpoint skill is unavailable in a session, THEN a handoff written by
  hand SHALL satisfy the method, and THE agent SHALL NOT simulate the skill.

### Decisions (PRD §2, §4)

- **REQ-TEAM-020** — BEFORE a deliverable declares an item blocked on a decision, THE author SHALL
  cross it against the decision log and the product/offer material; a block SHALL be written as
  "searched, no answer exists" or not written.
- **REQ-TEAM-021** — THE decision entry SHALL record what, who and when (quoted where available), why,
  and **what the decision does not say**.
- **REQ-TEAM-022** — WHEN a decision supersedes another, THE registry SHALL cite it in both directions
  and the superseded body SHALL be corrected rather than annotated at the end.

### Cost (PRD §2, §6)

- **REQ-TEAM-030** — WHEN `karvey-team cost` runs, THE skill SHALL report spend per agent, the share of
  turns against the share of spend, and context size at the most expensive turns.
- **REQ-TEAM-031** — IF the measured trend indicates the team is not paying for itself, THEN the report
  SHALL state so explicitly, with the figure.

### Verification (PRD §4)

- **REQ-TEAM-040** — THE method SHALL ship the verification failure modes as a rule applied at every
  phase close and as a read-only checklist (`karvey-guard --verify`).
- **REQ-TEAM-041** — THE statusline SHALL print its failure reason when it cannot compute its line,
  and SHALL NOT print an empty line.

## ADDED by `wave1-hardening` (3.12.0, merged 2026-09-26)

Traced to `docs/spec/changes/wave1-hardening/prd.md`.

### Single phase state machine (R-01)

- **REQ-W1-001** — Closed phase enum. The method SHALL store in `spec.json:phase` only one of `init | requirements | mockup | design_graphic | architecture | infra | tasks | impl | test | qa | deploying | deployed | archived`, and SHALL record "generated" and "approved" only under `approvals.*`. *(Traces: PRD §6 S-1, O-1 · Sources: R-01, H-01, H-22 · BL-04)*
- **REQ-W1-002** — Published schemas. The method SHALL ship a machine-readable schema for `spec.json` and one for `project.json` that together cover every field documented in `rules/living-specs.md` and `rules/project-config.md`, including `lane`, `skipped`, `phase_history`, `seed_backlog_id` as a string **or** a list, and the legacy aliases of REQ-W1-009 and REQ-W1-088. *(Traces: PRD §6 S-1, O-1 · Sources: R-01, R-07 · BL-04)*
- **REQ-W1-003** — Validate. WHEN the state tool validates a change or a project, the state tool SHALL report every violation with the file, the field path and the expected value, SHALL exit with a non-zero status when any violation is an error, and WHILE the project runs in Wave 1 warning mode SHALL report legacy shapes as warnings with exit 0. *(Traces: PRD §6 S-1, O-1, AC-1 · Sources: R-01 (Ola 1: "validate corre en modo advertencia") · BL-04)*
- **REQ-W1-004** — Transition only along allowed edges. WHEN a phase transition is requested, the state tool SHALL apply it only if the edge exists in the state-machine rule and every preceding phase is `approved` or `skipped`; IF not, THEN it SHALL refuse, leave `spec.json` unchanged and name the unmet precondition. *(Traces: PRD §6 S-1, O-1 · Sources: R-01 ("toda precondición acepta approved || skipped"), H-03 · BL-04)*
- **REQ-W1-005** — Next phase is computed, not interpreted. WHEN the orchestrator is asked what comes next for a change, the method SHALL answer from the state tool's computed next phase, and the orchestrator SHALL NOT contain a second phase table that can disagree with the state-machine rule. *(Traces: PRD §6 S-1, O-1 · Sources: R-01, H-01 · BL-04)*
- **REQ-W1-006** — Approvals carry who, role, time and reference. WHEN an approval is recorded, the state tool SHALL write `by`, `role` (`human` | `ceo-delegate`), `date` as an ISO 8601 timestamp with time and zone, and `ref`; IF any of them is missing, THEN it SHALL refuse; IF the approval is `prod` and `role` is not `human`, THEN it SHALL refuse. *(Traces: PRD §6 S-1, O-3 · Sources: R-01 (`approve --by --role --ref`), R-14 (fecha con hora), H-22 · Decision: D-03)*
- **REQ-W1-007** — Skipped phases are recorded. WHEN a phase is skipped, the state tool SHALL record it in `spec.json:skipped` as `{phase: reason}` with a non-empty reason, and SHALL treat a skipped phase as satisfying the preconditions of the next phase; IF the reason is empty, THEN it SHALL refuse. *(Traces: PRD §6 S-1, §9 (no lanes yet) · Sources: R-01, H-03, D-04 · BL-04)*
- **REQ-W1-008** — Phase history. WHEN a phase transition is applied, the state tool SHALL close the current entry of `spec.json:phase_history` with `exited_at` and append `{phase, entered_at}` for the new phase, both ISO 8601 with time; it SHALL NOT rewrite or delete earlier entries. *(Traces: PRD §6 S-1, O-1 · Sources: R-01, R-14 (base for Wave 2 metrics) · BL-04)*
- **REQ-W1-009** — Migration of legacy `spec.json` (`--fix`). WHEN the state tool runs `validate --fix` on a legacy `spec.json`, the state tool SHALL map the legacy phase values (`requirements-generated`, `mockup-generated`, `design-graphic-approved`, `architecture-generated|-approved`, `infra-generated|-approved`, `tasks-generated|-approved`, `deploy`) to the enum, SHALL convert `gates_skipped` into `skipped`, SHALL map `management: "none"` to `markdown`, SHALL show the diff before writing, SHALL NOT create or flip any approval, and SHALL produce the same file when run twice. *(Traces: PRD §6 S-1, O-1, AC-1 · Sources: R-01 (migrar con `--fix`), H-01, H-22, F-40 (I-11) · BL-04)*
- **REQ-W1-010** — Migration of legacy `project.json:management` (`--fix`). WHEN the state tool runs `validate --fix` on a `project.json` whose `management` is a string, the state tool SHALL rewrite it as `{"tool": "<string>"}`, SHALL move a top-level `clickup.backlog_list_id` into `management.location` when present, SHALL keep every other key unchanged, and SHALL leave `statuses` absent so the missing-map path (REQ-W1-080) resolves it. *(Traces: PRD §6 S-1, S-13, O-11 · Sources: R-01, BUG-06 / F-08 (I-02, C-03; 16 HainTech repos: 15 `"markdown"`, 1 `"clickup"`) · BL-04)*
- **REQ-W1-011** — impl, deploy and archive write real states. WHEN impl starts, the method SHALL set `phase = impl`; WHEN deploy opens the production release, it SHALL set `deploying`; it SHALL set `deployed` only after the production pipeline is green and the post-deploy check passed; WHEN archive is requested, the state tool SHALL refuse unless `phase = deployed` and `approvals.prod.by` is set with `role: human`. *(Traces: PRD §6 S-1, O-3 · Sources: R-01, H-02, H-07 · BL-04)*
- **REQ-W1-012** — One product document and one spec-delta path. The method SHALL use `prd.md` as the only product document of a change and `spec-delta.md` at the change root as the only spec-delta path; no skill SHALL read `proposal.md` or `specs/{capability}/spec-delta.md`. *(Traces: PRD §6 S-1, S-7 · Sources: R-01, H-24, H-25 · BL-04)*
- **REQ-W1-013** — Every phase write goes through the state tool. The phase skills SHALL change `phase`, `approvals`, `skipped` and `phase_history` only by invoking the state tool; no skill text SHALL instruct the agent to edit those fields by hand. *(Traces: PRD §6 S-1, O-1 · Sources: R-01 ("cada skill cambia su Update spec.json: phase… por una llamada al script"), H-01 (14 writers, 12 formats) · BL-04)*

### Guards that do what the rule says (R-02)

- **REQ-W1-014** — Stream redirections are not writes. WHEN the plan gate classifies a shell command, the plan gate SHALL NOT classify a redirection to a file descriptor or to the null device (`2>/dev/null`, `2>&1`, `>&2`, `&>/dev/null`) as a file write. *(Traces: PRD §6 S-2, O-2 · Sources: R-02, H-10 (false positive `ls 2>/dev/null` → rc=2) · BL-05)*
- **REQ-W1-015** — Destructive command classes are gated. WHILE no valid approval marker exists, the plan gate SHALL block `git clean`, `find … -delete`, in-place `sed -i`, `truncate`, a `DELETE FROM` without `WHERE`, `terraform destroy`, cloud-CLI `… delete` verbs and `rm -r`/`rm -rf`, in addition to the classes it blocks today. *(Traces: PRD §6 S-2, O-2 · Sources: R-02, H-10 (`git clean -fdx`, `find . -delete`, `sed -i` → rc=0) · BL-05)*
- **REQ-W1-016** — Marker scoped to project and change, with expiry. The plan gate SHALL honour only an approval marker scoped to the current project (and change, when one is active), SHALL treat a marker older than its TTL (default 120 minutes, configurable per project) as absent, and SHALL treat the marker as consumed when the phase that it approved closes. *(Traces: PRD §6 S-2, O-2, §11 A-1 · Sources: R-02, H-11 (fixed global `/tmp` path, no TTL, never consumed; `enforcement.md:25` promises expiry) · BL-05)*
- **REQ-W1-017** — The approval hook creates the marker from the human's words. WHEN the human submits a prompt that matches the project's approval vocabulary and contains none of its negation terms, the approval hook SHALL create the approval marker and record the time and the first 80 characters of that prompt beside it, and SHALL write an audit record of that marker carrying the prompt's hash, the session and the marker's creation time. *(Traces: PRD §6 S-2, O-2 · Sources: R-02 (tensión con la regla global), H-11, F-76 · Decision: D-01, D-34 · BL-05)*
- **REQ-W1-018** — The agent never creates the marker. IF a tool call of the agent would create, touch, copy, move or edit the approval marker, THEN the plan gate SHALL block it and say that approval comes only from the human's message. *(Traces: PRD §6 S-2, O-2 · Sources: R-02, H-11 · Decision: D-01 · BL-05)*
- **REQ-W1-019** — Approval vocabulary declared in one place. The method SHALL declare the approval vocabulary and the negation terms in one place per project, with a documented default list, and the guard tables SHALL include at least 5 approval phrases, 5 negations or questions, and 2 cases of quoted or pasted text that contains an approval word. *(Traces: PRD §6 S-2, O-2 · Sources: R-02 · Decision: D-01 · BL-05)*
- **REQ-W1-020** — git-flow resolves the target repository. WHEN the git-flow guard evaluates a `git commit` or `git push`, the guard SHALL resolve the branch of the repository the command acts on, including `git -C <path> …` and `cd <path> && git …`, not the branch of the session's working directory. *(Traces: PRD §6 S-2, O-2 · Sources: R-02, H-12 (`git -C <repo-en-master> commit` → rc=0) · BL-05)*
- **REQ-W1-021** — Bare push on production and branch-name precision. WHEN HEAD of the target repository is the production branch, the git-flow guard SHALL block a bare `git push`; the guard SHALL match production and integration branch names as whole names, so that `git push origin master-notes` is allowed. *(Traces: PRD §6 S-2, O-2 · Sources: R-02, H-12 (bare push passes; `master-notes` false positive) · BL-05)*
- **REQ-W1-022** — Integration push: implemented or not promised. The enforcement rule SHALL describe only protections the git-flow guard implements and the guard tables test; WHERE integration and production are different branches, the guard SHALL block a direct `git push` to integration from a branch that is not integration itself, or the rule SHALL NOT claim that protection. *(Traces: PRD §6 S-2, O-2 · Sources: R-02, H-13 (`enforcement.md:16` vs guard) · BL-05)*
- **REQ-W1-023** — Merge to production requires a human approval. WHEN a command would merge into the production branch (`gh pr merge`, including `--admin`; `az repos pr update --status completed`; `glab mr merge`; a `git push` to production, in every form the prod gate recognises), the prod gate SHALL allow it only if the state tool confirms, for the change being released, a production approval with `by` set, `role: human` and `ref` non-empty, whose evidence is the approval hook's audit record of the prod marker it names (prompt hash, session and time), which names the head commit the human approved and is less than 24 hours old, and only if the commit being released is that commit; otherwise it SHALL block and name the missing field. The prod gate SHALL also block when it cannot tell which single commit reaches production. WHEN a change is reopened, the state tool SHALL supersede its production approval, so the human gives it again after the rework. *(Traces: PRD §6 S-2, O-3, AC-3 · Sources: R-02, H-12 (`gh pr merge 12 --merge --admin` → rc=0), H-15, F-76, F-77, F-79 · Decision: D-02, D-03, D-34, D-35, D-36 · BL-05)*
- **REQ-W1-024** — The prod gate fails closed. IF the prod gate cannot determine the change being released, cannot read or validate its `spec.json`, or the state tool errors, THEN the prod gate SHALL block the merge and state the reason. *(Traces: PRD §6 S-2, O-3, §9 (Security Tier 2) · Sources: R-02 · Decision: D-02)*
- **REQ-W1-025** — Every prod-gate decision is logged. WHEN the prod gate allows or blocks a merge, the prod gate SHALL print one line with the decision, the change-id, the approver and the approval `ref`. *(Traces: PRD §6 S-2, O-3, §9 (Tier 2 access logging) · Sources: R-02 · Decision: D-02, D-03)*
- **REQ-W1-026** — The prod gate is on by default. WHERE Karvey's hooks are installed in a project and `project.json` does not switch the prod gate off, the prod gate SHALL be active. *(Traces: PRD §6 S-2, O-3 · Sources: R-02 · Decision: D-02)*
- **REQ-W1-027** — Per-project switch-off. WHERE `project.json:enforcement.prod_gate_hook` is `false`, the prod gate SHALL allow the command and print one line saying the production gate is disabled for this project. *(Traces: PRD §6 S-2 · Sources: R-02 · Decision: D-02)*
- **REQ-W1-028** — `spec.json` is validated when written. WHEN any tool call writes a file named `spec.json` under `docs/spec/`, the spec-write validator SHALL validate it and return the violations to the session. *(Traces: PRD §6 S-2, O-1 · Sources: R-02 (PostToolUse sobre `**/spec.json`) · BL-05)*
- **REQ-W1-029** — No described-but-missing hooks. The method SHALL NOT cite a hook that the plugin does not ship; `clickup-sync-guard` and `standards-guard` SHALL either be shipped with guard-table cases or removed from `rules/phase-close.md` and `rules/engineering-standards.md`. *(Traces: PRD §6 S-2, O-2, O-11 · Sources: R-02, H-14, BUG-15 / F-29 (C-10) · BL-05)*
- **REQ-W1-030** — Guard tables in CI. The method SHALL ship table tests for every guard — plan gate, git-flow guard, prod gate, approval hook, spec-write validator and session hook — containing at least every case measured in H-10 and H-12 plus the plan-gate false positives and false negatives, and the CI SHALL fail the PR when any case fails. *(Traces: PRD §6 S-2, O-2, AC-2 · Sources: R-02 (`tests/hooks/*`), H-10, H-12 · BL-05)*

### Deploy and archive never commit on integration or production (R-03)

- **REQ-W1-031** — Production approval as D-NN and in the PR. WHEN the human gives the production OK, the deploy skill SHALL record it as a `D-NN` in the decision log and in the PR body or PR approval, and SHALL NOT create a commit on the integration or production branch to record it. *(Traces: PRD §6 S-3, O-4 · Sources: R-03, H-18 · Decision: D-03 · BL-06)*
- **REQ-W1-032** — `approvals.prod` written at archive. WHEN a change is archived, the archive skill SHALL copy the production approval into `spec.json:approvals.prod` with `ref` set to the `D-NN` or the PR approval URL. *(Traces: PRD §6 S-3, O-3 · Sources: R-03 (AG's variant, PM-11) · Decision: D-03 · BL-06)*
- **REQ-W1-033** — Archive on its own branch, by PR. WHEN archive starts, the archive skill SHALL create a branch from production named `chore/archive-{change-id}`, SHALL commit only there, and SHALL merge it through a docs-only PR. *(Traces: PRD §6 S-3, O-4 · Sources: R-03, H-19 · Decision: D-03 · BL-06)*
- **REQ-W1-034** — Checklist before the first push. The deploy skill SHALL run the 6-step pre-deploy checklist (feature branch, CHANGELOG, everything committed, branch pushed, merged to integration, integration pushed) before its first `git push`. *(Traces: PRD §6 S-3, O-4 · Sources: R-03 (Step 1.9), H-20 · BL-06)*
- **REQ-W1-035** — Trunk projects (integration = production). WHERE `branch_flow.integration` equals `branch_flow.production`, the deploy skill, the archive skill and the guards SHALL use the single PR from the feature branch as both the integration and the production gate, and SHALL NOT require a separate integration merge. *(Traces: PRD §6 S-3, O-4 · Sources: R-03, R-08 ("el propio repo usa trunk", `project.json:16-20`) · Decision: D-04)*

### One versioning moment (R-04)

- **REQ-W1-036** — impl adds to Unreleased, no bump. WHEN impl commits a task, the impl skill SHALL add its line under `## [Unreleased]` in the CHANGELOG and SHALL NOT change the version in any manifest. *(Traces: PRD §6 S-4, O-5 · Sources: R-04, H-17, F-43 (C-16) → BL-07 · BL-07)*
- **REQ-W1-037** — Bump only at the release step. WHEN deploy reaches its release step, the deploy skill SHALL turn `[Unreleased]` into `[x.y.z] - date` and bump every version manifest once; a release SHALL contain exactly one bump. *(Traces: PRD §6 S-4, O-5 · Sources: R-04, H-17 · BL-07)*
- **REQ-W1-038** — QA and deploy pre-check validate Unreleased. The QA versioning dimension and the deploy pre-check SHALL verify the `[Unreleased]` section, not a numbered entry that only the release step creates. *(Traces: PRD §6 S-4, O-5 · Sources: R-04 (circular order QA-D6 / pre-check 3) · BL-07)*
- **REQ-W1-039** — The versioning rule says "per release". The versioning rule SHALL state that each release increments the version, and the orchestrator SHALL NOT describe a version bump per commit. *(Traces: PRD §6 S-4 · Sources: R-04 (`versioning.md:15`, `karvey/SKILL.md:191`) · BL-07)*
- **REQ-W1-040** — QA D6 checks what the versioning rule says it checks. The QA versioning dimension SHALL verify every item the versioning rule assigns to QA, including that the front reads its version from the version file and the DEV/PROD version formats. *(Traces: PRD §6 S-4, S-13, O-11 · Sources: F-38 (C-15) · Amends: `versioning.md`, `karvey-qa` D6)*
- **REQ-W1-041** — Visible-version check on the post-deploy step. WHEN the deploy post-deploy step checks the visible version on DEV, the deploy skill SHALL accept the bumped version together with an unmistakable DEV mark in any format, SHALL compare it with the version file of the deployed commit, and SHALL report a missing visible version as a recommendation, not as a finding. *(Traces: PRD §6 S-4, S-13, O-11 · Sources: F-20 (I-10, N-10; `front-vue-paautin-1` shows `DEV 2.10.4`) · Amends: `versioning.md`, deploy 2.4-bis / 2.7 · Related: BL-26 (Wave 2))*

### The estimate is never overwritten (R-05)

- **REQ-W1-042** — Estimate and actual are separate fields. WHEN a task finishes, the impl skill SHALL record the actual time as a time entry, worklog or actual field of the team's tracker, and SHALL NOT write the actual into the estimate field. *(Traces: PRD §6 S-5, O-6 · Sources: R-05, H-16 (`curl … time_estimate: {actual_time_ms}`) · BL-08)*
- **REQ-W1-043** — Three numbers per task. The method SHALL keep, per task, `estimate_min`, `actual_ai_min` and `actual_review_min` in the change's task record, whichever tracker is used, including Markdown. *(Traces: PRD §6 S-5, O-6 · Sources: R-05 · BL-08)*
- **REQ-W1-044** — Calibration at archive. WHEN a change is archived, the archive skill SHALL compute actual/estimate per work type of the estimation table and SHALL propose a recalibration for a type whose deviation exceeds ±30% in each of the last 3 archived changes. *(Traces: PRD §6 S-5, O-6, §11 A-3 · Sources: R-05 (`clickup-protocol.md:139-150`) · BL-08)*

### Session hook (R-06)

- **REQ-W1-045** — Archived and implemented changes are not active. WHEN the session hook selects the active change, the session hook SHALL exclude `changes/archive/` and every change directory that contains `IMPLEMENTED`. *(Traces: PRD §6 S-6, O-7 · Sources: R-06, H-08 (reproduced: "active change: archive") · BL-09)*
- **REQ-W1-046** — Compact or full manifest, never both. WHEN the session hook injects the agent manifest, the session hook SHALL inject the compact form or the full form, never both. *(Traces: PRD §6 S-6, O-7 · Sources: R-06, H-09 · Modifies: REQ-TEAM-014b · BL-09)*
- **REQ-W1-047** — Bounded injection. WHEN the session hook injects the board and the handoff, the session hook SHALL inject only open board rows, at most 40, and at most 6 KB of handoff, and SHALL say what was truncated and where the full file is; the context SHALL be emitted through the harness's structured additional-context channel. *(Traces: PRD §6 S-6, O-7 · Sources: R-06 · Modifies: REQ-TEAM-014b · BL-09)*
- **REQ-W1-048** — `state.json` written by the handoff capture. WHEN `karvey-checkpoint save` runs, the method SHALL write `state.json` by running the handoff capture, which measures branch, commit and uncommitted count of each owned repository; the agent SHALL NOT write `state.json` by hand. *(Traces: PRD §6 S-6, O-7 · Sources: R-06 (`karvey-checkpoint/SKILL.md:259` "never by hand") · Modifies: REQ-TEAM-010d · BL-09)*
- **REQ-W1-049** — One rotation threshold. The method SHALL define the rotation threshold in one place, and the statusline, the team rule, the checkpoint skill and the hooks README SHALL read or cite that one value. *(Traces: PRD §6 S-6, O-7, §11 Q-01 · Sources: R-06, H-32 (24 h vs 8 h) · Modifies: REQ-TEAM-015 · BL-09)*
- **REQ-W1-050** — Settings notice: definition and scope — AMENDS REQ-ADP-003. WHEN a session **starts** (not on resume, compact or clear) in a Karvey project — one with `docs/spec/project.json` or `docs/spec/changes/`, found by walking up no further than the git top level — AND `project.json` lacks non-empty `notifications` or `management` blocks (an empty object `{}` counts as missing), the session hook SHALL print one informational line pointing to `/karvey:karvey-init --settings`; WHERE the project is not a Karvey project, or the settings are present, the hook SHALL print nothing about settings and exit 0; IF no interpreter is available to read `project.json`, THEN the hook SHALL print the line in degraded form ("settings could not be read") rather than stay silent. *(Traces: PRD §6 S-6, S-13, O-11 · Sources: F-34 (S-06, E-10, I-04 spec side; E-09, E-11, N-11), BUG-02 code side already RESUELTO in 3.11.2 · **AMENDS REQ-ADP-003** · Modifies: REQ-TEAM-002)*
- **REQ-W1-051** — Hooks README matches hook behaviour. The hooks README SHALL describe each hook's output conditions as the hook implements them, and the plugin linter SHALL check the documented silent/printing conditions against the guard tables. *(Traces: PRD §6 S-6, S-7, O-11 · Sources: BUG-16 / F-30 (C-18, E-12; text fixed in 3.11.2, no regression check) · BL-09, BL-10)*

### The plugin as code (R-07)

- **REQ-W1-052** — No hand-kept rule copies. The plugin SHALL NOT contain hand-maintained copies of rule files; WHERE packaging requires copies, they SHALL be generated at build time and the plugin linter SHALL fail when any copy differs from its source. *(Traces: PRD §6 S-7, O-8 · Sources: R-07, H-26 (9 copies), F-44 (C-19) → BL-10 · BL-10)*
- **REQ-W1-053** — Every referenced path resolves. Every file path cited by a skill, rule, hook or README SHALL resolve from the citing file's location or from a declared plugin root, and the plugin linter SHALL fail on any unresolved reference. *(Traces: PRD §6 S-7, O-8 · Sources: R-07 (109 `karvey/rules/x.md` references; checkpoint/team/decisions cite `rules/` without the folder), F-44 · BL-10)*
- **REQ-W1-054** — Linter in CI on every PR. WHEN a PR is opened or updated, the CI SHALL run the plugin linter and the guard tables and SHALL block the merge when either fails. *(Traces: PRD §6 S-7, O-8, AC-4 · Sources: R-07, H-27 (only `close-external-prs.yml` today) · BL-10)*
- **REQ-W1-055** — Structural checks of the linter. The plugin linter SHALL check: frontmatter present and description length (REQ-W1-077); phase values in skill text against the enum (REQ-W1-001); skill and rule counts in README and `plugin.json` against the files; that `plugin.json`, `marketplace.json`, `project.json:karvey_version` and the top CHANGELOG release agree; and `docs/spec/**/*.json` against the schemas. *(Traces: PRD §6 S-7, O-8 · Sources: R-07 · BL-10)*
- **REQ-W1-056** — Tools used are declared. The plugin linter SHALL fail when a skill instructs an action whose tool is absent from that skill's `allowed-tools` (at least `Write`, `Edit`, `AskUserQuestion`, `Bash`, `Agent`). *(Traces: PRD §6 S-7, O-8 · Sources: R-07, H-33 (`karvey-browse`, `karvey-health` lack `Write`; the orchestrator lacks `Write`, `AskUserQuestion`) · BL-10)*
- **REQ-W1-057** — Every artifact read is produced upstream. The plugin linter SHALL fail when a skill reads a change artifact that no earlier phase (per the state-machine rule) produces. *(Traces: PRD §6 S-7, O-8 · Sources: R-07 (would have caught `proposal.md`), H-24 · BL-10)*
- **REQ-W1-058** — Release documentation in step with the version. The plugin linter SHALL fail when the top CHANGELOG release lacks its "Why" section (per `changelog-policy.md`) or when the method page's version history does not include the plugin version marked as current in every language block. *(Traces: PRD §6 S-7, S-13, O-11 · Sources: BUG-17 / F-31 (D6, C-21; fixed in 3.11.2, stays EN FIX until this check exists) · BL-10)*
- **REQ-W1-059** — Minor consistency defects of H-33. The method SHALL have: one decision-log path cited by `rules/multi-agent.md` and `karvey-decisions`; no `E{1..99}` literal in `karvey-init`; one copy of the "For each E2E flow step" block in `karvey-test`; the README naming skills as `/karvey:karvey-<name>`; and each of these SHALL be a linter check. *(Traces: PRD §6 S-7, O-8 · Sources: R-07, H-33 · BL-10)*
- **REQ-W1-060** — Public text names the team's tracker. The README and the `plugin.json` description SHALL describe task tracking as the team's configured tracker, naming ClickUp only as one of the supported tools. *(Traces: PRD §6 S-7, S-13, O-11 · Sources: BUG-07 / F-09 (C-05, C-06; README:52,117-119, plugin.json:4))*

### Graphify and the tracker ritual out of the hot path (R-16)

- **REQ-W1-061** — `knowledge_sync: none` is valid and the default without graphify. The method SHALL accept `project.json:knowledge_sync` values `none | graphify | obsidian`, and WHERE the key is absent and graphify is not detected, the method SHALL behave as `none` and say so once at init. *(Traces: PRD §6 S-8, O-9 · Sources: R-16 · BL-19)*
- **REQ-W1-062** — Knowledge sync only at archive and on demand. The method SHALL run the knowledge sync only in archive and when the user asks for it; no other phase, and no mockup iteration, SHALL run it. *(Traces: PRD §6 S-8, O-9 · Sources: R-16 (AG's option), H-31 · BL-19)*
- **REQ-W1-063** — Pending paths recorded between syncs. WHEN a file under `docs/spec/` is written, the method SHALL append its path to a pending-sync list, and the next sync SHALL consume and empty that list. *(Traces: PRD §6 S-8, O-9 · Sources: R-16 (`.graph-pending`) · BL-19)*
- **REQ-W1-064** — Tracker ritual per Feature. The method SHALL update the tracker status per task, and SHALL post the close comment and run the cascade per Feature, not per task. *(Traces: PRD §6 S-8, O-9 · Sources: R-16 (4–6 calls per task, ~150 per Epic; `phase-close.md:10`) · BL-19)*

### Spec-delta merge tool (R-17, script only)

- **REQ-W1-065** — Deterministic spec-delta merge. WHEN the spec-merge tool runs on a change, the tool SHALL append every ADDED block to the capability's living spec, replace every MODIFIED block by requirement id, remove every REMOVED block leaving a deprecation line, and SHALL produce the same living spec when run twice. *(Traces: PRD §6 S-9 · Sources: R-17 (script of AG), BL-20)*
- **REQ-W1-066** — Dry run. WHEN the spec-merge tool runs in dry-run mode, the tool SHALL print the resulting diff and SHALL NOT write any file. *(Traces: PRD §6 S-9 · Sources: R-17 (`--dry-run`) · BL-20)*
- **REQ-W1-067** — Archive uses the tool. WHEN archive merges a change's spec-delta, the archive skill SHALL do it with the spec-merge tool (dry run shown first), not by hand. *(Traces: PRD §6 S-9 · Sources: R-17 (moment unchanged in Wave 1; "before prod" is Wave 2) · BL-20)*

### Dashboard with open work, age and WIP (R-18)

- **REQ-W1-068** — Open work section. WHEN the dashboard runs, the dashboard SHALL show an OPEN WORK section with: findings by type and status per change, every `BUG-NN` not `RESUELTO`, every `[human]` task in `awaiting-human` with its executor and since when, every backlog item `open`, and every tracker operation pending reconciliation (REQ-W1-090). *(Traces: PRD §6 S-10, O-10 · Sources: R-18, H-30 · BL-21)*
- **REQ-W1-069** — Age and stalled flag. The dashboard SHALL show, per active change, the days in the current phase (from `phase_history`) and SHALL flag it "stalled" when that exceeds the project's stall threshold (default 7 days). *(Traces: PRD §6 S-10, O-10, §11 A-2 · Sources: R-18 · BL-21)*
- **REQ-W1-070** — All approvals, with who. The dashboard SHALL show every approval of every active change, from `requirements` to `prod`, with its approver, role and date, or `skipped` with its reason. *(Traces: PRD §6 S-10, O-10 · Sources: R-18 (line ends at `tasks` today) · BL-21)*
- **REQ-W1-071** — WIP limit. WHERE `project.json:wip_limit` is set, the dashboard SHALL show the count of active changes against it and SHALL warn when the count exceeds it. *(Traces: PRD §6 S-10, O-10 · Sources: R-18 · BL-21)*
- **REQ-W1-072** — Structured, read-only. The dashboard SHALL read JSON files as structured data (not by text matching) and SHALL NOT modify any file. *(Traces: PRD §6 S-10 · Sources: R-18 (`grep -o` parsing, `karvey-context/SKILL.md:75-77`) · BL-21)*

### QA observes without fixing; artifacts inside the change (R-21)

- **REQ-W1-073** — QA never commits. The QA skill SHALL NOT commit or edit product files; every defect it finds, including visual ones, SHALL be appended to `findings.md` as a finding for `karvey-iterate` to route. *(Traces: PRD §6 S-11 · Sources: R-21, H-28 (`karvey-qa/SKILL.md:121` vs `:268`) · BL-24)*
- **REQ-W1-074** — Review document inside the change. The QA skill SHALL write its review document to `docs/spec/changes/{change-id}/qa/REVISION_PR_*.md`, and the deploy skill SHALL read the review of the change being deployed from that directory, never the newest file in the repo root. *(Traces: PRD §6 S-11, AC-6 · Sources: R-21, H-29 (`ls -t` at root) · BL-24)*
- **REQ-W1-075** — This repo's review moves into its change. The retroactive review `REVISION_PR_17-19_20260923.md` SHALL live under `docs/spec/changes/team-adapters/qa/`, with every reference to it updated. *(Traces: PRD §6 S-11, S-13, AC-6 · Sources: R-21, H-29 · Decision: D-04)*
- **REQ-W1-076** — Stack rules out of QA. The QA skill SHALL NOT contain rules specific to one team's stack (Axios/apiService, `v-html`, RUT); those SHALL live in the standards and be evaluated in the standards-conformance dimension. *(Traces: PRD §6 S-11 · Sources: R-21 (`karvey-qa/SKILL.md:38-40,78`) · BL-24)*

### Short frontmatter descriptions, no generic triggers (R-22)

- **REQ-W1-077** — Description length and shape. Every skill description SHALL be at most 250 characters and SHALL state the phase or role, what it produces and when to use it. *(Traces: PRD §6 S-12, O-12 · Sources: R-22, H-23 (12 skills listed without description; 13,907 chars total) · BL-25)*
- **REQ-W1-078** — No generic or third-party triggers. Skill trigger phrases SHALL carry the method context (e.g. "karvey deploy", "karvey qa") and SHALL NOT include bare generic words (`deploy`, `QA`, `code review`) or third-party product names. *(Traces: PRD §6 S-12, O-12 · Sources: R-22 (collisions with the user's `deploy` skill and built-in `code-review`; 10 repeated phrases in karvey/grill/init) · BL-25)*
- **REQ-W1-079** — Rarely used skills are not model-invoked. The skills `karvey-guard`, `karvey-team`, `karvey-benchmark-models`, `karvey-scrape`, `karvey-import` and `karvey-retro` SHALL be invocable only by the user, not selected by the model. *(Traces: PRD §6 S-12, O-12 · Sources: R-22 (`disable-model-invocation: true`) · BL-25)*

### Tracker adapters converged from team-adapters

- **REQ-W1-080** — Missing status map resolved wherever a status changes — AMENDS REQ-ADP-022. WHEN a run is about to make its first status change, every skill that creates tracker items or changes a status (`init`, `tasks`, `impl`, `qa`, `deploy`, `iterate`, `archive`, phase-close) SHALL apply the one missing-map resolution clause of the management-adapters rule: resolve the tool and location (REQ-W1-086), read the real statuses of that location from the tool, propose the mapping, confirm it with the human and persist it; IF the location itself is missing, THEN the skill SHALL ask for it and SHALL NOT pick one. *(Traces: PRD §6 S-13, O-11 · Sources: F-05 (I-01, widened by N-02, N-03, N-06) · **AMENDS REQ-ADP-022** · Relates: CHANGELOG 3.10.0 claim toned down)*
- **REQ-W1-081** — No human, no persisted mapping — AMENDS REQ-ADP-022. IF the missing-map resolution runs where no human can answer (a subagent, a headless run), THEN the skill SHALL NOT persist any mapping, SHALL fall back to `PLAN.md` for that run and SHALL report it; subagents SHALL NOT write `project.json`; the map SHALL be resolved as a precondition of the tasks gate. *(Traces: PRD §6 S-13, O-11 · Sources: F-12 (N-02) · **AMENDS REQ-ADP-022**)*
- **REQ-W1-082** — Per-level maps, unsupported states, no workflow edits — AMENDS REQ-ADP-022. The status map SHALL allow one map per level or per list, SHALL accept `null` for a logical state the tracker cannot represent, SHALL re-map a single entry when a mapped status disappears, and the method SHALL NOT create or edit the team's workflow states. *(Traces: PRD §6 S-13, O-11 · Sources: F-14 (N-06) · **AMENDS REQ-ADP-022**)*
- **REQ-W1-083** — Settings travel as a reviewed change — AMENDS REQ-ADP-001, REQ-ADP-022. WHEN settings or a status map are persisted, the method SHALL commit them on a feature or docs branch (docs-PR lane) and say that they take effect after merge; BEFORE declaring settings missing, the session hook and the skills SHALL check `project.json` on `origin/{integration}` as well as the working copy. *(Traces: PRD §6 S-13, O-11 · Sources: F-13 (N-03) · **AMENDS REQ-ADP-001, REQ-ADP-022**)*
- **REQ-W1-084** — Who moves leaf items to `done` — AMENDS REQ-ADP-021. WHEN `approvals.qa.approved` becomes `true`, the QA skill SHALL set to `done` every Task and Feature of the change that is in `review`; WHEN archive runs, it SHALL verify that none remains in `review` and SHALL list any that does; the management-adapters rule SHALL list QA and archive under `set_status` "Used by". *(Traces: PRD §6 S-13, O-11 · Sources: F-06 (C-02, I-12) · **AMENDS REQ-ADP-021**)*
- **REQ-W1-085** — impl selects and resumes in logical states. WHEN impl selects the next task, the impl skill SHALL pick the first `todo` task or an orphan `in_progress` task whose dependencies are all at `review` or `done`, SHALL read task state from one declared source (the team's tracker, or `PLAN.md` for Markdown) and SHALL report any drift between that source and `tasks.md`. *(Traces: PRD §6 S-13, O-11 · Sources: BUG-05 / F-07 (N-08) · Satisfies REQ-ADP-021 as written)*
- **REQ-W1-086** — One resolution order for tracker settings — AMENDS REQ-ADP-023. The method SHALL resolve the tracker tool, location and statuses in one order, stated once in the management-adapters rule and cited by every skill: the change's `spec.json` override `{tool, location, statuses}` first, then `project.json:management`; the tracker-ids block (`spec.json:clickup`, kept under its historical name) SHALL be documented there and SHALL include `task_ids`. *(Traces: PRD §6 S-13, O-11 · Sources: F-15 (C-04, N-07), F-36 (C-09) · **AMENDS REQ-ADP-023**)*
- **REQ-W1-087** — "Is there a tracker" is one test on both shapes. WHEN a skill decides whether to create or link a tracker item, the skill SHALL use the resolved tool of REQ-W1-086, accepting a legacy string or an object, and SHALL treat `markdown` (and its alias `none`) as "no external tracker". *(Traces: PRD §6 S-13, O-11 · Sources: BUG-06 / F-08 (`karvey-iterate:61`, `rules/backlog.md:10`) · Relates: REQ-W1-010)*
- **REQ-W1-088** — Legacy `none` and optional sprints — AMENDS REQ-ADP-020, REQ-ADP-023. The management tool enum SHALL keep `clickup | jira | linear | azure-boards | github-projects | spreadsheet | markdown | other` and SHALL accept `none` as a documented legacy alias of `markdown`; `management` SHALL accept an optional `sprints` value (folder, iteration or cycle) used by the skills that file work into a sprint. *(Traces: PRD §6 S-13, O-11 · Sources: F-40 (I-11; 9 files), F-41 (I-13) · **AMENDS REQ-ADP-020, REQ-ADP-023**)*
- **REQ-W1-089** — Idempotent creation (find-or-create). WHEN a skill creates a tracker item, the skill SHALL first search for an item with the same natural key (`E{n}`, `E{n}.F{n}`, `E{n}.F{n}.T{n}`, `F-NN`, `BUG-NN`, `[Deploy] {change-id}@{version}`) and reuse it, and SHALL store the item's id in `spec.json`; a re-run SHALL create no duplicate. *(Traces: PRD §6 S-13, O-11 · Sources: F-17 (N-05, re-typed from bug to spec-gap) · Amends: management-adapters operations)*
- **REQ-W1-090** — Tracker outbox reconciled. IF a tracker operation fails and the skill falls back to `PLAN.md`, THEN the skill SHALL record the operation in a pending outbox of the change, the next phase-close SHALL retry it, and the skill SHALL NOT create a child item under a parent that does not exist in the tracker. *(Traces: PRD §6 S-13, O-11 · Sources: F-16 (N-04) · Amends: management-adapters rule 4)*
- **REQ-W1-091** — One cascade — AMENDS REQ-ADP-021. The management-adapters rule SHALL define the one cascade — Features to `review` move the Epic to `review` at impl; the Epic reaches `done` only at archive — and phase-close, the ClickUp protocol and impl SHALL cite it instead of restating it. *(Traces: PRD §6 S-13, O-11 · Sources: F-18 (C-01) · **AMENDS REQ-ADP-021**)*
- **REQ-W1-092** — `awaiting-human` is a qualifier — AMENDS REQ-ADP-021. The method SHALL define `awaiting-human` (🙋) as a qualifier of a task, mapped to the logical state `blocked`, and every marker legend SHALL list it. *(Traces: PRD §6 S-13, O-11 · Sources: F-19 (C-07) · **AMENDS REQ-ADP-021**)*
- **REQ-W1-093** — Values validated before use in commands — AMENDS REQ-ADP-010, REQ-ADP-020. WHEN a value from `project.json` (`notifications.target`, `management.location`, status names) is about to be used in a command, the method SHALL validate it against the channel's or tool's pattern, SHALL refuse shell metacharacters, SHALL pass it as a quoted argument, and SHALL refuse a spreadsheet path outside `docs/spec/`. *(Traces: PRD §6 S-13, O-11, §9 (Tier 2) · Sources: F-10 (S-01, command-injection half) · **AMENDS REQ-ADP-010, REQ-ADP-020**)*
- **REQ-W1-094** — phase-close scope matches its citations. The phase-close rule SHALL name exactly the phase skills that run it, and every phase skill it names SHALL cite it at its close. *(Traces: PRD §6 S-13, O-11 · Sources: F-37 (C-11; "every phase" vs 3 skills citing it))*
- **REQ-W1-095** — init consistency around the settings step — AMENDS REQ-ADP-001, REQ-ADP-002. `karvey-init` SHALL state that Step 3 does not re-ask `project.json` fields while Step 3.2 may still ask the team settings; SHALL use one initial Epic state for every tool; SHALL print a `Settings:` line in its final output; and SHALL persist a "not now" answer (as `notifications.channel: "none"` or an explicit deferred marker) so the question is not repeated. *(Traces: PRD §6 S-13, O-11 · Sources: F-39 (C-20, I-14) · **AMENDS REQ-ADP-001, REQ-ADP-002**)*
- **REQ-W1-096** — `--settings` merge semantics (verification of 3.11.2) — AMENDS REQ-ADP-002. WHEN `karvey-init --settings` runs, the skill SHALL run only the team-settings step, pre-fill every question with the current values, merge the answers without dropping untouched keys (`events`, `location`, custom keys), write `project.json`, report one line and stop, creating no change and no tracker item. *(Traces: PRD §6 S-13, O-11 · Sources: F-01 (N-01, N-09) → BUG-01 **RESUELTO in 3.11.2** (verified: `plugins/karvey/skills/karvey-init/SKILL.md` Step 0, lines 16-25; `CHANGELOG.md` [3.11.2] line 8; regression `plugins/karvey/hooks/tests/test-hooks.sh`) · **AMENDS REQ-ADP-002** (records the implemented behaviour in the requirement; no new work beyond a manual test of agent behaviour))*

### Notifications converged from team-adapters

- **REQ-W1-097** — Destination changes are confirmed — AMENDS REQ-ADP-011. The method SHALL refuse a `notifications.target` containing `://`, and WHEN `project.json:notifications` changed since the last send, the skill SHALL show the destination and ask for confirmation before sending. *(Traces: PRD §6 S-13, O-11, §9 (Tier 2) · Sources: F-32 (S-01 redirection half, N-07) · **AMENDS REQ-ADP-011**)*
- **REQ-W1-098** — QA notices carry counts by default — AMENDS REQ-ADP-011. The `qa` notification SHALL carry, by default, the count of findings per severity and a link to the review; WHERE `notifications.detail` is `full`, it SHALL carry the findings' titles. *(Traces: PRD §6 S-13, O-11, §9 (Tier 2) · Sources: F-33 (S-08) · **AMENDS REQ-ADP-011**)*
- **REQ-W1-099** — Destinations only from project.json; migration aid allowed — AMENDS REQ-ADP-012. The method SHALL NOT use at send time a notification destination that is not in `project.json`; during the team-settings step it MAY propose a destination seen in the session's context, and SHALL persist it only after the human's explicit confirmation; the 3.12.0 CHANGELOG SHALL carry a compatibility line for projects that relied on `CLAUDE.md` tables. *(Traces: PRD §6 S-13, O-11 · Sources: F-11 (I-06, N-14; 20 of 22 HainTech repos silent) · **AMENDS REQ-ADP-012**)*

### Statusline and method-page defects converged from team-adapters

- **REQ-W1-100** — Invalid time zone is visible. IF `KARVEY_TZ` is not a valid zone, THEN the statusline SHALL show the reset time in the system zone with a visible `(TZ?)` marker, and SHALL resolve the zone once per run. *(Traces: PRD §6 S-13, O-11 · Sources: BUG-08 / F-22 (S-04, E-05))*
- **REQ-W1-101** — Limit windows joined without stray separators. The statusline SHALL join the present rate-limit windows with ` · ` and SHALL print no separator before the first one. *(Traces: PRD §6 S-13, O-11 · Sources: BUG-09 / F-23 (E-06))*
- **REQ-W1-102** — Malformed hash is ignored. IF the method page's URL hash cannot be decoded, THEN the page SHALL ignore it and still bind the language switch. *(Traces: PRD §6 S-13, O-11 · Sources: BUG-10 / F-24 (S-07, E-15))*
- **REQ-W1-103** — Only a valid `?lang=` is remembered; one-off vs saved — AMENDS REQ-ADP-031. The method page SHALL remember a language only when the URL value is one of the five supported ones (a `xx-YY` value is read by its first two letters in both scripts), and a `?lang=` from a shared link SHALL apply to that visit without overwriting a language the viewer saved before; `zh-TW` and `zh-HK` SHALL resolve to the Chinese block with the page stating it is Simplified. *(Traces: PRD §6 S-13, O-11 · Sources: BUG-11 / F-25 (E-14), F-35 (E-17) · **AMENDS REQ-ADP-031**)*
- **REQ-W1-104** — Other query parameters preserved. WHEN the viewer switches language, the method page SHALL change only the `lang` parameter and SHALL keep every other query parameter. *(Traces: PRD §6 S-13, O-11 · Sources: BUG-12 / F-26 (E-16))*
- **REQ-W1-105** — Hash changes after load. WHEN the URL hash changes after load, the method page SHALL map it to the visible language block and jump to it, as it does at load. *(Traces: PRD §6 S-13, O-11 · Sources: BUG-13 / F-27 (E-18))*
- **REQ-W1-106** — No inert language switch without JavaScript. WHERE JavaScript is disabled, the method page SHALL NOT show a language switch that does nothing; English SHALL still render. *(Traces: PRD §6 S-13, O-11 · Sources: BUG-14 / F-28 (N-12))*

### Convergence and dogfooding (D-04)

- **REQ-W1-107** — Every routed incident reaches RESUELTO with a regression test. WHEN this change reaches QA convergence, every incident BUG-05..BUG-17 SHALL be `RESUELTO` in `docs/bugs_dev_testing.md` and `docs/spec/incidents-index.md`, each with a regression test or linter check named in its entry. *(Traces: PRD §6 S-13, O-11, AC-5 · Sources: `rules/incident-tracking.md` (RESUELTO needs a regression test), BUG-05..BUG-17 · Decision: D-04)*
- **REQ-W1-108** — team-adapters converges here. WHEN this change reaches QA convergence, `docs/spec/changes/team-adapters/findings.md` SHALL have no `open` or `routed` item of type `bug` or `spec-gap`, and the amended REQ-ADP-* SHALL be in this change's spec-delta. *(Traces: PRD §6 S-13, O-11, AC-5 · Sources: `rules/iteration-loop.md` (convergence) · Decision: D-04)*
- **REQ-W1-109** — The method's own specs validate. WHEN 3.12.0 is released, every `spec.json` and `project.json` under this repo's `docs/spec/` SHALL pass validation with no error, and this change's own phases SHALL have been recorded by the state tool from the moment it exists. *(Traces: PRD §6 S-1, O-1, AC-1 · Sources: R-01, H-22 · Decision: D-04)*

### Carried from `team-adapters` (3.10.0–3.11.2), amended in `wave1-hardening`

`team-adapters` was released without a spec-delta and never archived; per **D-04** its requirements reach the
living spec through this change, in their amended form. Traced to
`docs/spec/changes/team-adapters/prd.md`. Amendments cite the REQ-W1 that carries the detail.

- **REQ-ADP-001** *(amended: REQ-W1-083, REQ-W1-095)* — WHEN `karvey-init` runs AND `project.json` lacks
  `notifications` or `management`, THE skill SHALL ask the team-settings block and write the answers to
  `project.json` on a feature or docs branch, stating that they take effect after merge; a "not now" answer
  SHALL be persisted so it is not asked again.
- **REQ-ADP-002** *(amended: REQ-W1-095, REQ-W1-096)* — WHERE `project.json` already holds both blocks
  (checked in the working copy and on `origin/{integration}`), THE skill SHALL NOT ask them again, unless
  invoked with `--settings`; WHEN invoked with `--settings`, it SHALL run only the settings step, pre-fill the
  current values, merge without dropping untouched keys, and stop without creating a change or tracker item.
- **REQ-ADP-003** *(replaced by REQ-W1-050)* — WHEN a session **starts** in a Karvey project (one with
  `docs/spec/project.json` or `docs/spec/changes/`, searched up to the git top level) AND `project.json`
  lacks non-empty `notifications` or `management` blocks (`{}` counts as missing), THE session hook SHALL
  print one informational line pointing to `/karvey:karvey-init --settings`; WHERE the project is not a
  Karvey project or the settings are present, THE hook SHALL print nothing about settings and exit 0; IF
  `project.json` cannot be read for lack of an interpreter, THEN it SHALL print the line in degraded form.
- **REQ-ADP-010** *(amended: REQ-W1-093)* — THE notification channel SHALL be one of `google-chat | slack |
  teams | email | webhook | none`, with a `target` and a `via` (`mcp | cli | webhook | api`); the `target`
  SHALL be validated against the channel's pattern and passed as a quoted argument, never interpolated
  unvalidated into a command.
- **REQ-ADP-011** *(amended: REQ-W1-097, REQ-W1-098)* — WHEN a skill notifies (QA summary, deploy result),
  THE skill SHALL use the configured channel; IF the channel is `none` or unset, THEN it SHALL skip the
  notification and SAY so; a `target` containing `://` SHALL be refused; WHEN `notifications` changed since
  the last send, THE skill SHALL show the destination and ask for confirmation; the `qa` notice SHALL carry
  counts per severity and a link unless `notifications.detail` is `full`.
- **REQ-ADP-012** *(replaced by REQ-W1-099)* — THE method SHALL NOT use at send time a notification
  destination that is not in `project.json`, and SHALL NOT read notification targets from a project's
  `CLAUDE.md` tables; during the team-settings step it MAY propose a destination seen in context, persisted
  only after the human's explicit confirmation.
- **REQ-ADP-020** *(amended: REQ-W1-088, REQ-W1-093)* — THE management tool SHALL be one of `clickup | jira |
  linear | azure-boards | github-projects | spreadsheet | markdown | other`, with `none` accepted as a
  legacy alias of `markdown`; `management` MAY hold `sprints`; `location` and status names SHALL be
  validated before use in commands, and a spreadsheet path SHALL stay under `docs/spec/`.
- **REQ-ADP-021** *(amended: REQ-W1-084, REQ-W1-085, REQ-W1-091, REQ-W1-092)* — Phase skills SHALL express
  state changes as the logical states `todo | in_progress | review | done | blocked`, resolved through the
  status map; impl SHALL select and resume by those states only; QA SHALL move `review` items to `done` at
  QA approval and archive SHALL verify none remains in `review`; the one cascade is Features `review` → Epic
  `review` at impl and Epic `done` only at archive; `awaiting-human` is a qualifier mapped to `blocked`.
- **REQ-ADP-022** *(replaced by REQ-W1-080, REQ-W1-081, REQ-W1-082, REQ-W1-083)* — WHEN a run is about to
  make its first status change, every skill that creates tracker items or changes a status SHALL apply the
  one missing-map clause (resolve tool and location, read the real statuses, propose, confirm with the human,
  persist on a branch); with no human available it SHALL NOT persist and SHALL fall back to `PLAN.md`;
  subagents SHALL NOT write `project.json`; maps MAY be per level or per list, a state MAY be `null`
  (unsupported), a vanished status is re-mapped alone, and the method SHALL NOT edit the team's workflow.
- **REQ-ADP-023** *(amended: REQ-W1-086, REQ-W1-088)* — `spec.json:management` SHALL keep naming the tool,
  so existing changes with `"clickup"`, `"markdown"` or the legacy `"none"` remain valid; the tracker tool,
  location and statuses SHALL be resolved in one order (`spec.json` override → `project.json:management`),
  and the tracker-ids block (`spec.json:clickup`, historical name) SHALL be documented and include `task_ids`.
- **REQ-ADP-030** *(unchanged)* — THE repo SHALL ship a self-contained `docs/karvey.html` (no external
  requests) explaining the method, the meaning and origin of the name, and a map of every skill, phase,
  rule, hook and artifact; linked from the README.
- **REQ-ADP-031** *(amended: REQ-W1-102..REQ-W1-106)* — THE page `docs/karvey.html` SHALL be authored in
  English by default (what renders with JavaScript disabled, with no inert language switch) AND SHALL offer a
  language switch to Spanish, Portuguese, German and Chinese (Simplified), embedded in the same file; the
  chosen language SHALL be remembered per viewer when the browser allows it, and only when the value is
  valid; `?lang=en|es|pt|de|zh` (and `xx-YY` by its first two letters) SHALL select a language for that
  visit without overwriting a saved choice; ON a first visit with neither, THE page SHALL select the
  browser's primary language when it is one of the five, and English otherwise; THE tab title SHALL follow
  the selected language; switching SHALL keep other query parameters; a malformed or changed hash SHALL be
  handled without error.
