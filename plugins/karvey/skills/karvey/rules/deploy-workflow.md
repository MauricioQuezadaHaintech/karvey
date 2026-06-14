# Rule: Deployment flow (git + pipeline)

Defines the ordered deployment flow the method uses. It is applied by `karvey-impl` (during development) and `karvey-deploy` (PHASE 11). Aligned with the team's hard deploy rules.

## Principles (NEVER skip)

1. **Never commit directly to `dev` or `master`.** Always a feature branch.
2. **Never deploy manually.** The deploy is triggered by the pipeline: push to `dev` → deploy dev; merge to `master` → deploy prod. Manual `func azure functionapp publish` or equivalents are forbidden.
3. **`pull` before starting and `pull` before each merge/PR.** Avoid working on a stale base.
4. **Prod requires explicit human OK.** The PR to `master` is not merged without approval.
5. **Zero downtime**: the deployment must not cause a service outage.

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
7. PR dev → master
8. Merge to master ONLY with human OK     # ⇒ triggers PROD pipeline
```

## 6-step checklist (before any deploy)

1. Am I on a feature branch? (not dev/master)
2. Did I update `CHANGELOG.md`? (see `changelog-policy.md`)
3. Did I commit everything pending?
4. Did I push the branch?
5. Did I merge to `dev`?
6. Did I push `dev`?

Only after all 6 → the pipeline deploys dev. For prod, repeat the verification and PR to master with approval.

## Multi-repo

If the change touches several repos, apply the flow in **each one**, respecting the dependency order declared in `architecture.md` (e.g. DB before backend before frontend). Record the progress per repo in the management tool (ClickUp/`PLAN.md`).

## Management

`karvey-deploy` records the deployment in the project's management tool:
- ClickUp: task `[Deploy] {change-id}` with the 6-step checklist as subtasks/comment and closure once prod is confirmed.
- Markdown: entry in `PLAN.md` with the deploy status per repo and environment.
