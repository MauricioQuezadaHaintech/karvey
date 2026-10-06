# PRD: prod-gate-scope (hotfix 3.12.1)

## Executive summary

Real use of 3.12.0 found three ways a production approval misses its target: the approval hook binds the
human's prod OK to whatever change is "active" in the working tree where the hook runs, not to the change the
phrase names; a change that spans several repos cannot be released from the repos it does not live in; and the
prod-gate does not see a PR completed or a production pipeline approved through the REST API, nor commands run
from outside a repository. A fourth, smaller defect (BL-64) blocks a read-only listing of the state paths.
The owner decided (D-43) to ship these fixes as 3.12.1 before the rest of the release chain, and widened the
hotfix (D-45) with five more defects found in use: the session hook injects another agent's profile, the
prod-gate decides by the session's directory instead of the PR's repo, a prod OK answered through a question
tool never reaches the approval hook, a production-shaped phrase that records nothing prints nothing, and the
`approve … prod` error does not say which marker it found.

## Goal (the change's north star)

A production approval reaches exactly the change and the commits the human approved, whatever repo, working
tree or command form the release goes through.

## Problem and context

1. **Wrong scope (bug).** The phrase «aprobado para producción project-upgrade 3.13.0» was typed in a checkout
   where only another change (`team-adapters`) was open. `project-upgrade` did not exist in that tree, so the
   hook fell back to the active change and recorded `(prod, team-adapters)`: an approval of a change the human
   did not name.
2. **Multi-repo (gap).** A change owned by repo A declares that it releases A, B and C. The owner approves in
   A. The PR `[Deploy] <id>` in B is blocked with "cannot determine the change being released": B does not
   hold the change and the gate has no way to read A's approval.
3. **Coverage (gap).** `curl … /pullrequests/<n> -X PATCH` with `status: completed`, `…/pipelines/approvals`,
   a GitHub `…/pulls/<n>/merge` through a plain HTTP client, and any command run after `cd /tmp` that targets
   a Karvey repo by name or URL pass the gate unseen.
4. **BL-64 (bug).** `ls` of the state or compat-marker paths is blocked when the list also holds an `echo`,
   a pipe into a formatter, or a read-only command substitution, although nothing is written.
5. **Identity (bug, D-45).** The session hook resolves the agent profile from the session's starting directory
   and walks up the folder tree, so a session started or resumed in another agent's folder received that
   agent's manifest, board and handoff — one of them a sensitive handoff about access management.
6. **Gate target (bug, D-45).** `gh pr merge <n> --repo <owner/repo>` and PR URLs are evaluated against the
   repo of the session's directory, not the PR's repo; a merge into the target's integration branch was
   blocked as if it were production.
7. **Question tool (bug, D-45).** The deploy skill asks for the production OK through a question tool, whose
   answer never reaches the prompt hook, so no prod marker can be recorded from it.
8. **Silent hook (bug, D-45).** A phrase with approval and production words that resolves to no change prints
   nothing; the later error says "kind plan does not satisfy prod".
9. **Opaque error (bug, D-45).** The `approve … prod` error does not name the markers it found nor what is
   missing. In the same decision, a production REST call to a repo that is not a Karvey repo passes with a
   warning line instead of being blocked.

## Objectives and success metrics

- O-1: every prod marker names the change the human's phrase names, or no marker is written and the hook says
  how to fix it. Metric: 0 prod markers scoped to an unnamed change when the phrase names one.
- O-2: a `[Deploy] <id>` PR in a declared repo is released under the owning repo's approval, bound to that
  repo's PR head commit, with the 24 h expiry (D-35). Metric: the multi-repo guard table passes; a PR in an
  undeclared repo or with another commit is blocked.
- O-3: the REST and outside-a-repo forms listed in the problem need the same SHA-bound approval; what the gate
  cannot resolve is blocked with the reason. Metric: guard tables for each form; read-only GETs pass.
- O-4: a read-only listing of the protected paths passes; every write form stays blocked (BL-64).
- O-5: a session receives only the profile of the repo it works in; when that is ambiguous it receives
  nothing and is told how to restore explicitly; a sensitive handoff never leaves its repo. Metric: 0
  profiles injected from an ancestor folder or another repo in the session-hook tables.
- O-6: the prod-gate decides on the PR's own repo and base branch; merges into a non-production branch pass.
  Metric: guard tables with `--repo`, PR URLs and integration-branch bases.
- O-7: every production OK reaches the approval hook as typed text, and every production-shaped phrase gets
  exactly one answer line. Metric: 0 skills or rules that ask for the prod OK through a question tool (lint);
  hook tables for recorded / not-recorded lines.
- O-8: every `approve … prod` refusal names the markers found and what is missing.

## User stories / main use cases

- As the owner, I approve production of a change by naming it, from any checkout, and the approval is either
  recorded for that change or refused with instructions.
- As an agent releasing a multi-repo change, I record the per-repo head commits from the owning repo and merge
  each `[Deploy] <id>` PR in its own repo.
- As the owner, I trust that no REST call, wrapper directory or HTTP client lets an agent merge to production
  without my OK.

## Scope (in scope)

- S-1: approval-hook scope for prod approvals (named change, unknown change, single active change, several).
- S-2: `spec.json:repos`, `approve … prod --repo … --sha …`, `check-prod … --repo …`, prod-gate lookup of the
  owning repo from a declared repo, and the BLOCK text.
- S-3: prod-gate recognition of REST PR completions, production pipeline approvals, branch writes, and of
  commands that name a repository while running outside one.
- S-4: protect-paths read-only listings (BL-64).
- S-5: BUG-NN entries with regression tests, release 3.12.1.
- S-6: session-hook profile resolution, ambiguity line, sensitive handoffs, explicit restore (D-45).
- S-7: prod-gate target repo and base resolution; non-Karvey targets warn (D-45).
- S-8: the production OK asked as a typed phrase; lint rule against a question tool for it; the approval
  hook's one-line answer (D-45).
- S-9: the `approve … prod` refusal text (D-45).

## Out of scope

- Plan-kind (non-production) approvals keep their scope rule.
- The release manifest (D-37, Wave 2) is unchanged.
- No new network credentials: the gate uses the host CLIs' own login and never a token found in the command.
- Lanes as enforced data (Wave 2): this hotfix records `type`/`lane: hotfix` only.

## Stakeholders

The owner (approves requirements, architecture, tasks, QA and production); agents that release changes.

## Constraints

- Hotfix lane: fix + `BUG-NN` + regression test in the same PR (`rules/multi-agent.md` §7); the prod gate
  still applies.
- The pre-bash hook budget (15 s; network budget 6 s) and the prompt hook budget hold.
- Fail closed for the prod-gate and protect-paths; fail open (record nothing) for the approval hook.
- Company-neutral public text; fictional repo names in examples.

## Acceptance criteria

- AC-1: the incident phrase in a tree without the named change records no marker and prints the fix,
  naming the worktree that holds the change when there is one.
- AC-2: the multi-repo release passes with bound SHAs and is blocked otherwise, with a message that names
  where to approve and which command to run.
- AC-3: each REST form in the guard tables is blocked without approval and allowed with a bound one; GETs
  pass.
- AC-4: BL-64 listing forms pass; write forms stay blocked.
- AC-5: full gate green (unit, regression, hook tests, guard tables, page tests, lint, validate), CI green on
  the PR to `main`.
- AC-6: a session started or resumed in another agent's folder, in a parent folder or in a second repo gets
  no profile and one line naming the candidates; a sensitive handoff is withheld outside its repo.
- AC-7: `gh pr merge <n> --repo <other>` into the other repo's integration branch passes; into its
  production branch it is checked against that repo's approval; a non-Karvey target passes with a warning.
- AC-8: lint fails on a skill that asks for the prod OK through a question tool; the deploy skill shows the
  phrase to type; the hook prints exactly one line for each production-shaped phrase.
- AC-9: the `approve … prod` refusal lists each marker found (kind, change, age) and the missing piece.

## Revision history

| Rev | Date | Ref | Change | Why |
|---|---|---|---|---|
| 1 | 2026-10-05 | D-45 · F-05..F-10 | Problems 5-9, O-5..O-8, S-6..S-9, AC-6..AC-9 | Owner widened the hotfix with the defects found in use (D-45). |
