# Rule: Deployment flow (git + pipeline)

Defines the ordered deployment flow the method uses. It is applied by `karvey-impl` (during development) and `karvey-deploy` (PHASE 11). Aligned with the team's hard deploy rules.

## Principles (NEVER skip)

1. **Never commit directly to `dev` or `master`.** Always a feature branch.
2. **Never deploy manually.** The deploy is triggered by the pipeline: push to `dev` → deploy dev; merge to `master` → deploy prod. Manual `func azure functionapp publish` or equivalents are forbidden.
3. **`pull` before starting and `pull` before each merge/PR.** Avoid working on a stale base.
4. **Prod requires explicit human OK.** The PR to `master` is not merged without approval, recorded in the repo as `spec.json:approvals.prod = { by, date, ref: D-NN }` (see `multi-agent.md` §4).
5. **The PR's gates are verified before requesting that OK.** CI and branch policies (build validation,
   required reviewers, status checks) are not the same as the release gate: they run on this PR, over the
   merge commit, and catch what the local pre-check could not see. Never ask a human to approve over a red
   or unresolved gate — that turns the approval into a rubber stamp. Bypassing a policy is the human's
   decision and their explicit responsibility, never the agent's initiative to unblock itself.
6. **Zero downtime**: the deployment must not cause a service outage.
7. **No branch is left behind.** Once a feature branch is absorbed into `{production}` (it already went through `{integration}`), it is deleted — remote and local — in the same deploy. Only an **absorbed** branch is deleted; one that still carries unreleased work is never deleted, it is reported. See *Branch hygiene* below.

## Step-by-step flow

For each affected repo (`project.json:repos`):

```
0. git pull                              # before starting
1. git checkout -b feature/{change-id}   # or the feature_prefix from project.json
   (development + commits per task — see karvey-impl)
2. git pull origin {integration}         # before merge (default: dev)
3. merge feature/{change-id} → dev
4. git push origin dev                   # ⇒ triggers DEV pipeline
5. Verify DEV deploy (smoke/healthcheck)
6. git pull origin {production}          # before the PR (default: master)
7. PR dev → master                       # gh pr / az repos pr / glab mr, per git_platform
8. Verify the PR's gates (CI + branch policies) and wait for them to settle
9. Merge to master ONLY with human OK     # ⇒ triggers PROD pipeline
10. Delete the absorbed branches (remote + local) and prune   # see Branch hygiene
```

## 6-step checklist (before any deploy)

1. Am I on a feature branch? (not dev/master)
2. Did I update `CHANGELOG.md`? (see `changelog-policy.md`)
3. Did I commit everything pending?
4. Did I push the branch?
5. Did I merge to `dev`?
6. Did I push `dev`?

Only after all 6 → the pipeline deploys dev. For prod, repeat the verification and PR to master with approval.

## Branch hygiene

A branch that outlives its merge is noise at best and a trap at worst: someone rebases on it, reopens it, or
reads it as pending work. The method closes that loop explicitly instead of leaving it to discipline.

**When:** right after the merge to `{production}` and its canary (`karvey-deploy` 2.12), and again as a
sweep at `karvey-archive` (Step 7F). Long-lived branches (`{integration}`, `{production}`, and any listed
in `project.json:branch_flow.protected_branches`) are never candidates.

**Absorbed = its content is already in `{production}`.** Check it, never assume it:

```bash
git fetch origin --prune
git branch -r --merged origin/{production}          # merged by merge commit / fast-forward
git cherry origin/{production} origin/{branch}      # all lines '-' ⇒ absorbed by cherry-pick / rebase
# squash merges hide from both: the tree test catches them (git ≥ 2.38)
[ "$(git merge-tree --write-tree origin/{production} origin/{branch})" = "$(git rev-parse origin/{production}^{tree})" ] && echo absorbed
```

| Branch state | Action |
|---|---|
| Absorbed, no open PR | Delete remote (`git push origin --delete {branch}`) and local (`git branch -d {branch}`), then `git fetch --prune`. |
| Absorbed, PR still open | Close the PR with a comment naming the commit/release that absorbed it, then delete. |
| **Not absorbed** (carries unreleased commits) | **Never delete.** Report it with its unique commits and PR. The human decides: rescue (bring it into a change), keep, or discard. Discarding unreleased work is the human's call, never the agent's cleanup. |

**Rescued branches.** A branch brought into a change by cherry-pick *with conflict resolution* will not pass the
checks (its patches changed). Before deleting it, show that the only difference is the resolution
(`git diff {production} $(git merge-tree --write-tree {production} origin/{branch})`); the human approves closing
it as *superseded by* the release that absorbed it, and the PR is closed with that reference.

Use `git branch -d` (not `-D`) for local deletion: git refusing it is a signal the check above was wrong.
Report the counts explicitly — deleted / kept (with reason) — never clean silently.

## Multi-repo

If the change touches several repos, apply the flow in **each one**, respecting the dependency order declared in `architecture.md` (e.g. DB before backend before frontend). Record the progress per repo in the team's tracker (`management-adapters.md`) or `PLAN.md`.

## Hotfixes and documentation-only PRs

- **Hotfix:** same flow, faster — but the PR must carry the fix + `BUG-NN` + regression test together (`multi-agent.md` §7).
- **Docs-only PR** (only `docs/**`, `*.md`, `spec.json`): light CI (spec lint) instead of build/test/deploy; merged by `project.json:docs_pr.merged_by`; never triggers a deploy (`multi-agent.md` §8).

## Management

`karvey-deploy` records the deployment in the project's management tool:
- Team's tracker (`management-adapters.md`): task `[Deploy] {change-id}` with the 6-step checklist as subtasks/comment, `set_status(…, done)` once prod is confirmed.
- Markdown: entry in `PLAN.md` with the deploy status per repo and environment.
