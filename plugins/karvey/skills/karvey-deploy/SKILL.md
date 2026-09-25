---
name: karvey-deploy
description: Karvey phase 11 — pipeline-triggered release (feature → integration → PR to production), PR gates, prod OK in the release ledger, canary. After karvey-qa. Triggers include "karvey deploy", "karvey release", "desplegar con karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: <change-id>
---

# Karvey Deploy

## Purpose

PHASE 11 of the Karvey Method, between `karvey-qa` (PHASE 10) and `karvey-archive` (PHASE 12). It runs the **ordered deployment flow** (feature branch → integration → PR to production) by the team's hard rules: never commit directly on the integration or production branch, never deploy manually (the pipeline deploys), `pull` before starting and before each merge/PR, and **prod never without the human's explicit OK**.

It runs **only after** `karvey-qa` passed with no open critical/high findings. The central rules are `../karvey/rules/deploy-workflow.md` and `../karvey/rules/state-machine.md`; follow them exactly.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py"
C="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py"
I="$(python3 "$C" get branch_flow.integration --shell)"
P="$(python3 "$C" get branch_flow.production --shell)"
```

## Execution steps

### Step 0 — Pre-checks (release gate)

BEFORE touching git, run `python3 "$S" next "{change-id}" --json` and read `docs/spec/project.json`. No `project.json` → stop and run `karvey-init` first (`../karvey/rules/project-config.md`). `next` must report `qa` approved; `invalid` → show its errors and stop.

If **anything below fails, STOP and report what is missing. Do not deploy.**

1. **QA approved, no open critical/high.** Read the review from `docs/spec/changes/{change-id}/qa/` (`REVISION_PR_*.md`, the one QA wrote for this change — never the newest file at a repo root). Its security gate must show **0 critical and 0 unresolved high**.
2. **Tests PASS** for `{change-id}` in `docs/test_evidence.md`.
3. **CHANGELOG `[Unreleased]`** in each affected repo (`../karvey/rules/changelog-policy.md`): one line per commit of the change, with the **responsible human** (never empty nor "AI"), the **AI model** and the **why**. It becomes the release entry in Step 2.4.
4. **Hotfix lane** (`spec.json:type = "hotfix"`, `../karvey/rules/multi-agent.md` §7): the PR carries **fix + `BUG-NN` (tracker + `findings.md`) + regression test**, all three, the test green in CI. Missing any → stop.
5. **Parent/child** (`links`): a **child** deploys only its repo and reports to the parent; a **parent** has no deploy of its own — verify every child is deployed.

### Step 0-bis — Documentation-only PRs

If the diff touches only docs/specs (`git diff --name-only "origin/$I"...HEAD`), it follows the **docs-only lane** (`../karvey/rules/multi-agent.md` §8): light CI only (the plugin linter / spec validation), merged by `project.json:docs_pr.merged_by`, no version bump, no deploy, no prod approval. If code sneaks in, it is not docs-only.

### Step 1 — Repos, order, platform, git host

- **Repos and order:** `project.json:repos`; honor the dependency order of `architecture.md` (e.g. **DB → backend → frontend**) and apply Step 2 per repo in that order.
- **Deploy platform** (only to know **where to monitor**, never to deploy): use `project.json:deploy` (`platform`, `prod_url`, `dev_url`, `health_check`) or detect it from evidence — `fly.toml`, `render.yaml`, `vercel.json`, `netlify.toml`, `host.json` + pipeline, `.github/workflows/`, `azure-pipelines.yml`, `Dockerfile` + `k8s/`/`helm/`. Health: `/health`, `/healthz`, the root page, or the target's runtime equivalent (`../karvey/rules/targets.md`). Unknown URL → do not invent it; ask before the prod canary.
- **Git host** (`project.json:git_platform`, else from `git remote get-url origin`): `github.com` → `gh pr` · `dev.azure.com`/`visualstudio.com` → `az repos pr` · `gitlab.com` → `glab mr` · other → ask. The remote wins over a stale config, and it is reported.

Propose any detected value as a settings change on a docs branch (`project-config.md`); do not write `project.json` on the integration branch.

### Step 1.9 — 6-step pre-deploy checklist (before the first push)

From `../karvey/rules/deploy-workflow.md`. Show it and verify each item **before any `git push`**:

1. On the feature branch `feature/{change-id}` (not integration, not production)?
2. `CHANGELOG.md` `[Unreleased]` complete (Step 0.3)?
3. Everything pending committed?
4. Feature branch pushed?
5. Merged to integration?
6. Integration pushed?

Items 4–6 are done in Step 2; the pipeline deploys integration only after all six. **Trunk flow** (`$I` = `$P`): items 5–6 become "one PR feature → production".

### Step 2 — Ordered deployment flow (FOR EACH repo)

**2.1 — Pull and check the branch.** `feature/{change-id}` must exist (created by `karvey-impl`); do not create it here.
```bash
git pull
git branch --show-current          # must be feature/{change-id}
python3 "$S" advance "{change-id}" deploying
```

**2.2 — Pull integration before the merge.**
```bash
git pull origin "$I"
```

**2.3 — Release step: one bump per release** (`../karvey/rules/versioning.md`). On the feature branch, turn `## [Unreleased]` into `## [x.y.z] - YYYY-MM-DD` and bump the version file once (`package.json`, `pyproject.toml`, `*.csproj`, `VERSION`, …): **major** = breaking, **minor** = backward-compatible feature, **rev** = fix. Commit it as `release: x.y.z` with the rest of the change.

**2.4 — Visible version (recommendation).** If a `target` has a UI, recommend a version visible in it, differentiated by environment (`versioning.md`): DEV `{version}-dev.{build}+{sha}` with a `DEV` mark, PROD `{version}`, read from the version file at build time. A missing visible version is a recommendation, not a blocker.

**2.5 — Push the branch, merge to integration, push ⇒ DEV pipeline** (skip in trunk flow):
```bash
git push origin "feature/{change-id}"
git checkout "$I"
git merge "feature/{change-id}"
git push origin "$I"               # ⇒ DEV pipeline
```

**2.6 — DEV canary (Step 2-bis).** Wait for the green pipeline and run the canary over the real DEV runtime. No advance to prod if DEV is unhealthy. With a UI, check the visible version against the commit DEV actually runs: take the deployed commit (the source commit of the green DEV run; the one pushed in 2.5 if the run does not name it) and read its version file with `git show "<deployed-sha>:<version file>"` — not the tip of `$I`, which another change may have bumped since. The check passes when DEV shows that version with an unmistakable DEV mark, in any format (`DEV 2.10.4`, `2.10.4-dev.42+74571ae`, a `DEV` badge beside `2.10.4`). Another version, or no DEV mark, is a finding; a UI with no visible version at all is the 2.4 recommendation, not a finding and not a blocker.

**2.7 — Pull production and open the PR** (integration → production; trunk: feature → production). Use the host from Step 1:
```bash
git pull origin "$P"
gh pr create --base "$P" --head "$I" --title "[Deploy] {change-id}" \
  --body "Deploy of {change-id}. QA OK, tests PASS, CHANGELOG released. Needs the human's prod OK."
az repos pr create --source-branch "$I" --target-branch "$P" --title "[Deploy] {change-id}" \
  --description "Deploy of {change-id}. QA OK, tests PASS, CHANGELOG released. Needs the human's prod OK."
```

**2.8 — Verify the PR's own gates; do NOT skip to 2.9.** CI, required reviewers and branch policies run on this PR's merge commit and can fail for reasons Step 0 could not see. Wait for them to settle:
```bash
gh pr checks "{pr}"                            # GitHub
az repos pr policy list --id "{pr}" -o table   # Azure Repos
```

| Gate state | Action |
|---|---|
| ✅ all required passed | Continue to 2.9. |
| ⏳ running/queued | Wait and re-check. Never request the OK on an unresolved gate. |
| ❌ a required one failed | **STOP**, report which and why; it goes to `karvey-iterate`, not to the merge. |
| ⚪ none configured | Report that production has **no gate**; continue only if the user accepts, and log it as a finding. |

Bypassing a policy is the human's call and responsibility — never the agent's initiative to unblock itself.

**2.9 — Prod OK from the human ⇒ merge ⇒ PROD pipeline.** Ask with `AskUserQuestion`; the human answers in their own words, with an approval word **and** a production word (D-10), so the approval hook records a prod marker. Then:
1. Allocate the decision `D-NN` and put its text (who, when, the words verbatim) in the PR body or a PR comment. It is written into `docs/spec/decisions.md` at archive, on `chore/archive-{change-id}` (D-03).
2. Record it in the release ledger — never in a commit on the integration branch:
   ```bash
   python3 "$S" approve "{change-id}" prod --by "{human name}" --role human --ref "D-NN"
   python3 "$S" check-prod "{change-id}"      # what the prod-gate reads
   ```
   Refused (no prod marker, missing `--by`/`--ref`) → do not merge; ask the human again. The prod approval is never delegated (`role` is always `human`).
3. Merge (the prod-gate hook lets it through only with the ledger entry):
   ```bash
   gh pr merge "{pr}" --merge                          # GitHub      ⇒ PROD pipeline
   az repos pr update --id "{pr}" --status completed   # Azure Repos ⇒ PROD pipeline
   ```

**2.10 — PROD canary (Step 2-bis).** Wait for the PROD pipeline and run the canary over production. A regression → **alert and recommend an immediate rollback** (via pipeline). With a UI, PROD shows exactly `{version}`. Keep the green pipeline run URL and the canary result: archive records them (`advance … deployed --pipeline-run <url> --post-deploy-check pass`).

**2.11 — Branch hygiene** (`deploy-workflow.md` → *Branch hygiene*). Delete what production absorbed; never delete what it did not:
```bash
git fetch origin --prune
git branch -r --merged "origin/$P"             # + the cherry / tree checks of the rule
git push origin --delete "feature/{change-id}"   # only if absorbed
git branch -d "feature/{change-id}"
```
Absorbed non-protected branches are deleted (closing their PR with a comment); **not absorbed ones are listed** with their unique commits and PR for the human. Report the counts.

### Step 2-bis — Post-deploy canary loop

After each deploy (DEV in 2.6, PROD in 2.10), over the just-deployed environment and the target's real runtime (`targets.md`, eyes via `karvey-browse`: browser, simulator, HTTP client or terminal). Several spaced iterations, not one shot, each recorded:
1. **Console/log errors** new since the deploy.
2. **Performance** of health and key endpoints against the pre-deploy baseline.
3. **Page/endpoint failures** on the change's critical routes and the product's main ones (5xx, timeout, broken page).

Result: OK, or REGRESSION with what failed. DEV regression → stop before prod. PROD regression → alert and recommend a rollback (always via pipeline).

### Step 3 — Hard rules (NEVER skip)

- **NEVER commit directly on the integration or production branch**; always a feature branch.
- **NEVER deploy manually** — `func azure functionapp publish` and equivalents are forbidden; the pipeline deploys.
- **`pull` before starting and before each merge/PR.**
- **Prod NEVER without the human's explicit OK**, recorded as D-NN + PR + ledger (`approve … prod`); never as a commit.
- **NEVER request the prod OK with the PR's gates red or unresolved.**
- **NEVER assume the git host** — detect it from the remote.
- **Hotfix = fix + BUG-NN + regression test in the same PR.**
- **One version bump per release**, from `[Unreleased]`, in Step 2.3.
- **Branches:** absorbed → deleted; not absorbed → never deleted, reported.
- **Zero downtime**: the canary reinforces it; a prod regression → rollback recommended.
- In multi-repo, the dependency order of `architecture.md`.

### Step 4 — Record in the tracker

Resolve the tracker with `python3 "$C" resolve management --change "{change-id}" --json` (`../karvey/rules/management-adapters.md`, including its missing-map clause). If `external` is true: `create_task("[Deploy] {change-id}")` with the checklist as subtasks, `set_status(…, in_progress)` while it runs, `link(…, PR)`, `set_status(…, done)` on the PROD confirmation, `blocked` if the gate or the canary stops it; a failed call goes to the outbox (`karvey-config.py outbox add`). Otherwise add to `PLAN.md` the deploy status per repo and environment:

```markdown
## Deploy — {change-id}
| Repo | DEV | PROD |
|------|-----|------|
| {repo1} | ✅ deployed | 👀 PR open / ✅ merged |
```

### Step 5 — Notify the team + final output

Send the `deploy` notification per `../karvey/rules/notifications.md`: `python3 "$C" resolve notifications --json`; `none` or `deploy` not in `events` → skip and say so. Run `python3 "$C" notify-check` first: exit 10 (destination changed) → show old and new destination and ask the human before sending. Post in the channel's own markup: repos + versions, DEV/PROD state, canary, branches. A failed send is reported, not swallowed.

```
✅ Deploy complete — {change-id}

Repos (dependency order):
  - {repo1}: v{version} · DEV ✅ canary OK | PROD {✅ merged, canary OK / 👀 PR open, awaiting the human's OK}
Checklist: verified · QA: OK (0 critical, 0 high) · Tests: PASS · Release: [Unreleased] → [x.y.z]
Prod approval: {by} · {D-NN} · ledger ✅ (check-prod)   Type: {feature | ops | hotfix (BUG-NN)}
Platform: {…} · Prod URL: {prod_url} · Pipeline run: {url}
Canary: DEV {OK / REGRESSION} · PROD {OK / REGRESSION → rollback recommended}
Branches: deleted {N} ({list}) · kept {N} ({branch}: not absorbed, PR #{n})
{UI} Visible version: {yes / recommended}
Management: {[Deploy] in {tool} → {status} | PLAN.md updated} · Notification: {channel → target | skipped}

Next step: /karvey-archive {change-id}
```

## Advance to the next phase

Ask the user: "Shall we advance to the Archive (closure) phase now?" Confirm → `/karvey-archive {change-id}`; otherwise wait. In another session, `/karvey {change-id}` (it calls `karvey-state.py next`) says where the change is.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
