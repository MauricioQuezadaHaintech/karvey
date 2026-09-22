# Requirements (EARS) — `team-layer`

Traced to `prd.md`.

## Optionality (PRD §3, §5)

- **REQ-TEAM-001** — WHERE no team configuration exists (`docs/spec/team.json` or a legacy
  `.ceo-agentes`), THE method SHALL behave exactly as before this change, and no phase or gate SHALL
  require the team layer.
- **REQ-TEAM-002** — WHEN the session hook runs on a project with no agent profile and no team
  configuration, THE hook SHALL print nothing and exit 0.
- **REQ-TEAM-003** — WHEN `karvey-team init` is invoked, THE skill SHALL present the measured cost of
  the reference run and obtain confirmation BEFORE writing any file.
- **REQ-TEAM-004** — THE team rule SHALL state, before its configuration section, the conditions under
  which a team SHALL NOT be used.

## Handoff (PRD §4)

- **REQ-TEAM-010** — WHEN `karvey-checkpoint save` runs, THE skill SHALL write the change checkpoint
  AND the agent handoff, **whether or not a team is configured**: at `docs/spec/agent/handoff.md` for a
  single agent, or at `{ops_repo}/agents/<role>/handoff.md` when a team is.
- **REQ-TEAM-010b** — WHERE no agent profile exists yet, THE skill SHALL create it during the save
  (manifest, board, checklist, handoff) rather than failing or skipping the handoff.
- **REQ-TEAM-010c** — THE handoff SHALL carry, besides repository state: who the agent is and what is
  not theirs, the standing rules **referenced with their commit** rather than copied, the board of open
  items, and the closing checklist.
- **REQ-TEAM-010d** — WHEN the handoff is written, THE skill SHALL also write `state.json` beside it
  with the measured branch, commit and uncommitted count of each owned repo.
- **REQ-TEAM-011** — THE handoff's state section SHALL be the output of commands; IF a claim of "done"
  cannot be verified in that session, THEN it SHALL be recorded as unverified with its reason.
- **REQ-TEAM-012** — THE handoff SHALL record every scheduled task with its full prompt.
- **REQ-TEAM-013** — WHEN the handoff is committed to a shared ops repo, THE skill SHALL commit by
  explicit path (`git commit -- <paths>`) and SHALL NOT stage other paths.
- **REQ-TEAM-014** — WHEN `karvey-checkpoint restore` runs, THE skill SHALL contrast the handoff
  against the real repository state and SHALL report that the handoff has aged BEFORE presenting its
  content as current.
- **REQ-TEAM-014b** — WHEN a session starts, resumes, compacts or is cleared AND an agent profile
  exists, THE session hook SHALL reinject identity, manifest, board, checklist and handoff, SHALL
  compare `state.json` against the live repositories, and SHALL instruct the session to run
  `/karvey-checkpoint restore` before anything else when there is an active change, drift, or no
  handoff.
- **REQ-TEAM-014c** — WHERE `state.json` is absent or unreadable, THE hook SHALL state that nothing was
  measured and that the handoff's claims are unverified.
- **REQ-TEAM-015** — THE method SHALL NOT allow an agent to rotate itself or another agent; on reaching
  a rotation threshold THE agent SHALL write the handoff, commit it, report readiness, and continue
  working normally.
- **REQ-TEAM-016** — IF the checkpoint skill is unavailable in a session, THEN a handoff written by
  hand SHALL satisfy the method, and THE agent SHALL NOT simulate the skill.

## Decisions (PRD §2, §4)

- **REQ-TEAM-020** — BEFORE a deliverable declares an item blocked on a decision, THE author SHALL
  cross it against the decision log and the product/offer material; a block SHALL be written as
  "searched, no answer exists" or not written.
- **REQ-TEAM-021** — THE decision entry SHALL record what, who and when (quoted where available), why,
  and **what the decision does not say**.
- **REQ-TEAM-022** — WHEN a decision supersedes another, THE registry SHALL cite it in both directions
  and the superseded body SHALL be corrected rather than annotated at the end.

## Cost (PRD §2, §6)

- **REQ-TEAM-030** — WHEN `karvey-team cost` runs, THE skill SHALL report spend per agent, the share of
  turns against the share of spend, and context size at the most expensive turns.
- **REQ-TEAM-031** — IF the measured trend indicates the team is not paying for itself, THEN the report
  SHALL state so explicitly, with the figure.

## Verification (PRD §4)

- **REQ-TEAM-040** — THE method SHALL ship the verification failure modes as a rule applied at every
  phase close and as a read-only checklist (`karvey-guard --verify`).
- **REQ-TEAM-041** — THE statusline SHALL print its failure reason when it cannot compute its line,
  and SHALL NOT print an empty line.
