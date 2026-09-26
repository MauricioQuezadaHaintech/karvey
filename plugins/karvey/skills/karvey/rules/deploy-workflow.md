# Rule: Deployment flow (git + pipeline)

Defines the ordered deployment flow the method uses. It is applied by `karvey-impl` (during development) and `karvey-deploy` (PHASE 11). Aligned with the team's hard deploy rules.

## Principles (NEVER skip)

1. **Never commit directly to `dev` or `master`.** Always a feature branch.
2. **Never deploy manually.** The deploy is triggered by the pipeline: push to `dev` → deploy dev; merge to `master` → deploy prod. Manual `func azure functionapp publish` or equivalents are forbidden.
3. **`pull` before starting and `pull` before each merge/PR.** Avoid working on a stale base.
4. **Prod requires explicit human OK, recorded without a commit (D-03).** Where it lives, in order (REQ-W2-052): **at deploy**, its text (who, when, the words verbatim, the reserved `D-NN`) is in the production PR body or the PR approval, and it is written to the release ledger with `karvey-state.py approve {change-id} prod --by … --role human --ref D-NN` (`--sha` the PR head the human approved: valid for that commit only, 24 h, D-35; on the release-manifest path `--manifest --pr-body FILE`: ONE OK covers every change the manifest and the PR body list, consumed once, D-37 — every other path is one OK per change); prod-gate reads that ledger before the merge (`enforcement.md`). **At archive**, the `D-NN` is written into the decision log on `chore/archive-{change-id}` and copied into `spec.json:approvals.prod` (`--write-spec`). The approval is never a commit on the integration or production branch. A clone without the ledger records the deploy as attested: `advance {change-id} deployed --attested --ref D-NN --pipeline-run URL` (REQ-W2-053).
5. **The PR's gates are verified before requesting that OK.** CI and branch policies (build validation,
   required reviewers, status checks) are not the same as the release gate: they run on this PR, over the
   merge commit, and catch what the local pre-check could not see. Never ask a human to approve over a red
   or unresolved gate — that turns the approval into a rubber stamp. Bypassing a policy is the human's
   decision and their explicit responsibility, never the agent's initiative to unblock itself.
6. **Zero downtime**: the deployment must not cause a service outage.
7. **No branch is left behind.** Once a feature branch is absorbed into `{production}` (it already went through `{integration}`), it is deleted — remote and local — in the same deploy. Only an **absorbed** branch is deleted; one that still carries unreleased work is never deleted, it is reported. See *Branch hygiene* below.
8. **Integration by PR** (REQ-W2-048). Where integration differs from production, a feature branch reaches `{integration}` through a PR whose CI is the DEV gate, merged by the git host — never a local merge followed by a push into `{integration}`.
9. **One release, one manifest** (REQ-W2-045..047). Before the production PR, the living spec is merged on the change branch (`karvey-spec-merge.py`, dry run first) and the release gate runs on the drafted PR body (`karvey-release-gate.py check {change-id} --pr-body FILE`); the body lists every change-id and version of the manifest. A manifest that is not `pass` offers a `release/{version}` branch with only the changes whose QA passed (`release-branch`, read-only plan; cherry-picks only after the human's OK; a conflict stops and is reported, never resolved by the agent).

## Step-by-step flow

For each affected repo (`project.json:repos`). Branch names come from `project.json:branch_flow`, validated
for the shell:

```bash
C="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py"
I="$(python3 "$C" get branch_flow.integration --shell)"
P="$(python3 "$C" get branch_flow.production --shell)"
```

**6-step checklist — before the first push:**

1. Am I on a feature branch (not `$I`/`$P`)?
2. Does `CHANGELOG.md` carry this change's lines under `## [Unreleased]`? (`changelog-policy.md`)
3. Is everything committed?
4. Is the branch pushed?
5. Is the PR to `$I` open and its CI green (the DEV gate)?
6. Is that PR merged by the git host (never a local merge pushed into `$I`)?

Only after all six does the integration pipeline deploy. Then:

```bash
git pull                                   # 0. before starting
git checkout -b "feature/{change-id}"      # 1. or project.json:branch_flow.feature_prefix
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" advance "{change-id}" deploying   # on the feature branch
git pull origin "$I"                       # 2. before the integration PR
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-spec-merge.py" "{change-id}" --dry-run   # 2.4-bis, then apply + commit
git push origin "feature/{change-id}"      # 3. PR feature → "$I" (gh pr / az repos pr / glab mr); its CI = DEV gate
#                                            4. the host merges the PR ⇒ integration pipeline
#                                            5. post-deploy verification of the integration deploy
git pull origin "$P"                       # 6. before the production PR
#                                            7. manifest + PR body; release gate (2.8-bis) on that body
#                                            8. PR "$I" → "$P"; wait for its gates (CI + branch policies) to settle
#                                            9. human OK → PR body + ledger (principle 4); merge ⇒ prod pipeline
#                                           10. delete the absorbed branches (Branch hygiene)
```

The release step (one per release, `versioning.md`) turns `[Unreleased]` into `[x.y.z]` and bumps the version
once, on the feature branch, before step 3.

**Trunk flow** (`branch_flow.mode: trunk`, the recommended flow; derived when `integration == production`): one PR
from the feature branch into `$P`; steps 3–5 disappear, the checklist ends at "branch pushed", and the PR carries
the D-NN.

## Branch hygiene

A branch that outlives its merge is noise at best and a trap at worst: someone rebases on it, reopens it, or
reads it as pending work. The method closes that loop explicitly instead of leaving it to discipline.

**When:** right after the merge to `{production}` and its post-deploy verification (`karvey-deploy` 2.11), and again as a
sweep at `karvey-archive` (Step 7F). Long-lived branches (`{integration}`, `{production}`, and any listed
in `project.json:branch_flow.protected_branches`) are never candidates.

**Absorbed = its content is already in `{production}`.** Check it, never assume it:

```bash
git fetch origin --prune
B="{branch}"                                          # the candidate branch
git branch -r --merged "origin/$P"                   # merged by merge commit / fast-forward
git cherry "origin/$P" "origin/$B"                   # all lines '-' ⇒ absorbed by cherry-pick / rebase
# squash merges hide from both: the tree test catches them (git ≥ 2.38)
[ "$(git merge-tree --write-tree "origin/$P" "origin/$B")" = "$(git rev-parse "origin/$P^{tree}")" ] && echo absorbed
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
