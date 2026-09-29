# PRD: prod-gate-scope (hotfix 3.12.1)

## Executive summary

Real use of 3.12.0 found three ways a production approval misses its target: the approval hook binds the
human's prod OK to whatever change is "active" in the working tree where the hook runs, not to the change the
phrase names; a change that spans several repos cannot be released from the repos it does not live in; and the
prod-gate does not see a PR completed or a production pipeline approved through the REST API, nor commands run
from outside a repository. A fourth, smaller defect (BL-64) blocks a read-only listing of the state paths.
The owner decided (D-43) to ship these fixes as 3.12.1 before the rest of the release chain.

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

## Objectives and success metrics

- O-1: every prod marker names the change the human's phrase names, or no marker is written and the hook says
  how to fix it. Metric: 0 prod markers scoped to an unnamed change when the phrase names one.
- O-2: a `[Deploy] <id>` PR in a declared repo is released under the owning repo's approval, bound to that
  repo's PR head commit, with the 24 h expiry (D-35). Metric: the multi-repo guard table passes; a PR in an
  undeclared repo or with another commit is blocked.
- O-3: the REST and outside-a-repo forms listed in the problem need the same SHA-bound approval; what the gate
  cannot resolve is blocked with the reason. Metric: guard tables for each form; read-only GETs pass.
- O-4: a read-only listing of the protected paths passes; every write form stays blocked (BL-64).

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
