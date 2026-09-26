---
name: karvey-deploy
description: Karvey phase 11 — pipeline-triggered release (feature → integration → PR to production), PR gates, prod OK in the release ledger, post-deploy verification. After karvey-qa. Triggers include "karvey deploy", "karvey release", "desplegar con karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: <change-id>
---

# Karvey Deploy

## Purpose

PHASE 11 of the Karvey Method, between `karvey-qa` (PHASE 10) and `karvey-archive` (PHASE 12). It runs the **ordered deployment flow** (feature branch → living spec on the branch → PR to integration → release manifest and release gate → PR to production) by the team's hard rules: never commit directly on the integration or production branch, never deploy manually (the pipeline deploys), `pull` before starting and before each merge/PR, and **prod never without the human's explicit OK**.

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

The pre-checks are one script — the **release gate** (REQ-W2-069). Run it and **explain its JSON; never recompute an item by hand**:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-release-gate.py" check "{change-id}" --json
```
Items: `qa_gate` · `tests` · `changelog` · `version_match` · `lane_triplet` · `manifest` · `spec_merged` · `pr_body` — each `pass`, `warn` (a check in warn mode, 3.13), `fail` or `not-applicable`. Exit 1 = an item failed: stop and name it. Here `spec_merged` may still read `unmerged` (2.4-bis merges it) and `pr_body` is `not-applicable` (2.8-bis passes the body).

1. **QA approved, no open critical/high** (`qa_gate`). Read the review from `docs/spec/changes/{change-id}/qa/` (`REVISION_PR_*.md`, the one QA wrote for this change — never the newest file at a repo root). Its security gate must show **0 critical and 0 unresolved high**.
2. **Tests PASS** (`tests`): the latest run in `docs/spec/changes/{change-id}/evidence.jsonl` is green and the coverage line is shown; the evidence of the test phase is `docs/spec/changes/{change-id}/test_evidence.md`. No run → `not evaluated`, never "pass".
3. **CHANGELOG `[Unreleased]`** in each affected repo (`changelog`, `../karvey/rules/changelog-policy.md`): one line per commit of the change, with the **responsible human** (never empty nor "AI"), the **AI model** and the **why**. It becomes the release entry in Step 2.3.
4. **`patch` / `hotfix` lane** (`lane_triplet`, `spec.json:lane`, `../karvey/rules/lanes.md`): the PR carries **fix + `BUG-NN` (tracker + `findings.md`) + regression test**, all three, recorded with `karvey-state.py lane-evidence`, the test green in CI. Missing any → stop.
5. **Parent/child** (`links`): a **child** deploys only its repo and reports to the parent; a **parent** has no deploy of its own — verify every child is deployed.

### Step 0-bis — Documentation-only PRs

If the diff touches only docs/specs (`git diff --name-only "origin/$I"...HEAD`), it follows the **docs-only lane** (`../karvey/rules/multi-agent.md` §8): light CI only (the plugin linter / spec validation), merged by `project.json:docs_pr.merged_by`, no version bump, no deploy, no prod approval. If code sneaks in, it is not docs-only.

### Step 1 — Repos, order, platform, git host

- **Repos and order:** `project.json:repos`; honor the dependency order of `architecture.md` (e.g. **DB → backend → frontend**) and apply Step 2 per repo in that order.
- **Deploy platform** (only to know **where to monitor**, never to deploy): use `project.json:deploy` (`platform`, `prod_url`, `dev_url`, `health_check`) or detect it from evidence — `fly.toml`, `render.yaml`, `vercel.json`, `netlify.toml`, `host.json` + pipeline, `.github/workflows/`, `azure-pipelines.yml`, `Dockerfile` + `k8s/`/`helm/`. Health: `/health`, `/healthz`, the root page, or the target's runtime equivalent (`../karvey/rules/targets.md`). Unknown URL → do not invent it; ask before the production post-deploy verification.
- **Git host** (`project.json:git_platform`, else from `git remote get-url origin`): `github.com` → `gh pr` · `dev.azure.com`/`visualstudio.com` → `az repos pr` · `gitlab.com` → `glab mr` · other → ask. The remote wins over a stale config, and it is reported.

Propose any detected value as a settings change on a docs branch (`project-config.md`); do not write `project.json` on the integration branch.

### Step 1.9 — 6-step pre-deploy checklist (before the first push)

From `../karvey/rules/deploy-workflow.md`. Show it and verify each item **before any `git push`**:

1. On the feature branch `feature/{change-id}` (not integration, not production)?
2. `CHANGELOG.md` `[Unreleased]` complete (Step 0.3)?
3. Everything pending committed?
4. Feature branch pushed?
5. PR to integration opened, its CI green (the DEV gate)?
6. That PR merged by the git host (never a local merge pushed into integration)?

Items 4–6 are done in Step 2; the pipeline deploys integration only after all six. **Trunk flow** (`branch_flow.mode: trunk`, `$I` = `$P`): items 5–6 become "one PR feature → production".

### Step 2 — Ordered deployment flow (FOR EACH repo)

**2.1 — Pull and check the branch.** `feature/{change-id}` must exist (created by `karvey-impl`); do not create it here. Check the trailers of the branch through the manifest: a commit without `Karvey-Change: {change-id}` is listed as `unmapped` — fix it on the branch before any PR.
```bash
git pull
git branch --show-current          # must be feature/{change-id}
python3 "$S" advance "{change-id}" deploying
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-release-gate.py" manifest --base "origin/$P" --no-record
```

**2.2 — Pull integration before the merge.**
```bash
git pull origin "$I"
```

**2.3 — Release step: one bump per release** (`../karvey/rules/versioning.md`). On the feature branch, turn `## [Unreleased]` into `## [x.y.z] - YYYY-MM-DD` and bump the version file once (`package.json`, `pyproject.toml`, `*.csproj`, `VERSION`, …): **major** = breaking, **minor** = backward-compatible feature, **rev** = fix. Commit it as `release: x.y.z` with the rest of the change.

**2.4 — Visible version (recommendation).** If a `target` has a UI, recommend a version visible in it, differentiated by environment (`versioning.md`): DEV `{version}-dev.{build}+{sha}` with a `DEV` mark, PROD `{version}`, read from the version file at build time. A missing visible version is a recommendation, not a blocker.

**2.4-bis — Living spec on the change branch** (REQ-W2-054). Merge the change's `spec-delta.md` into the living spec **on `feature/{change-id}`**, so the update travels in the change's own PRs. Show the dry run first, then apply and commit with the trailer:
```bash
M="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-spec-merge.py"
python3 "$M" "{change-id}" --dry-run          # show the diff to the human
python3 "$M" "{change-id}"                    # apply
git add docs/spec/specs/ && git commit -m "docs(spec): merge {change-id} into the living spec" \
  --trailer "Karvey-Change: {change-id}"
python3 "$M" "{change-id}" --check            # must print: merged
```
A conflict exits 1 and prints the diff: **stop before any PR** and route it through `karvey-iterate`. A change with no `spec-delta.md` (a `patch` lane) skips this step.

**2.5 — Integration by PR** (`branch_flow.mode: env-branches` only; skip in trunk flow) (REQ-W2-048). Push the branch and open a PR to integration with the host CLI; that PR's CI is the DEV gate. It is merged **by the host** once its checks pass — never merged locally and pushed into integration:
```bash
git push origin "feature/{change-id}"
gh pr create --base "$I" --head "feature/{change-id}" --title "[Integrate] {change-id}" \
  --body "Integration of {change-id} (Karvey-Change: {change-id})."
az repos pr create --source-branch "feature/{change-id}" --target-branch "$I" --title "[Integrate] {change-id}"
gh pr checks "{pr}"                  # wait: green before the merge
gh pr merge "{pr}" --merge           # ⇒ DEV pipeline (Azure Repos: az repos pr update --id "{pr}" --status completed)
```

**2.6 — DEV post-deploy verification (Step 2-bis).** Wait for the green pipeline and run the post-deploy verification over the real DEV runtime with `--env dev`. No advance to prod unless it is `pass` (or `not-evaluated`, stated as such, when DEV has no contract). With a UI, DEV must show `-dev` of the version just released; anything else is a finding.

**2.7 — Pull production and draft the PR body.** The production PR carries **every change of the release manifest** (REQ-W2-045, 047), not only this one. Compute the manifest of `origin/$P..{head}` (`{head}` = `$I`, or the feature branch in trunk flow) and write the body to a file: one line per change with its id, version, lane and QA state, the unmapped commits (if any) named, and a line for the production OK, which is filled in 2.9.
```bash
git pull origin "$P"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-release-gate.py" manifest --base "origin/$P" --head "{head}" --json
#   → write "$PR_BODY" (e.g. docs/spec/changes/{change-id}/qa/pr-body.md): - {id} {version} (lane, QA)
```

**2.8-bis — Release manifest + release gate, before the PR opens.** Run the release gate on the drafted body and explain its verdict:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-release-gate.py" check "{change-id}" --head "{head}" \
  --pr-body "$PR_BODY" --json
```
- `pass` → open the PR (2.8).
- `warn` (3.13: an unmapped commit or a change without QA in the manifest) or `fail` → show every item and offer the two ways out, recommended first: **wait** until every change of the manifest has QA, or build a **`release/{version}` branch** from production with only the changes whose QA passed (REQ-W2-050). The plan is read-only:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-release-gate.py" release-branch --version "{version}" \
    --base "origin/$P" --head "{head}" --json
  ```
  Show the commits it would cherry-pick and the changes it leaves out. Only after the human's OK run the `git switch -c` and `git cherry-pick -x` lines it printed, one by one. **On a conflict stop**: report the commit, run `git cherry-pick --abort`, and never resolve it yourself. The PR then goes from `release/{version}` to production.

**2.8 — Open the production PR and verify its own gates; do NOT skip to 2.9.** Open it with the drafted body (integration → production; trunk: feature → production; a release branch → production), using the host from Step 1:
```bash
gh pr create --base "$P" --head "{head}" --title "[Deploy] {version}" --body-file "$PR_BODY"
az repos pr create --source-branch "{head}" --target-branch "$P" --title "[Deploy] {version}" \
  --description "$(cat "$PR_BODY")"
```
CI, required reviewers and branch policies run on this PR's merge commit and can fail for reasons Step 0 could not see. CI, required reviewers and branch policies run on this PR's merge commit and can fail for reasons Step 0 could not see. Wait for them to settle:
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

**2.9 — Prod OK from the human ⇒ merge ⇒ PROD pipeline.** Ask with `AskUserQuestion`; the human answers in their own words, with an approval word **and** a production word (D-10), so the approval hook records a prod marker. The production OK lives, in this order (REQ-W2-052):
1. **At deploy — in the PR.** Reserve the decision number with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-id.py" next D` and put its text (who, when, the words verbatim) in the PR body or the PR approval. Nothing is committed on the integration or production branch for it.
2. **At deploy — in the release ledger**, for every change of the manifest (`--manifest` records the same record for each one with the one prod marker):
   ```bash
   python3 "$S" approve "{change-id}" prod --by "{human name}" --role human --ref "D-NN" --manifest
   python3 "$S" check-prod "{change-id}"      # what the prod-gate reads
   ```
3. **At archive — in the decision log.** `karvey-archive` writes the `D-NN` into `docs/spec/decisions.md` on `chore/archive-{change-id}` and `approve … prod --write-spec` copies it into `spec.json:approvals.prod` (D-03).
   Refused (no prod marker, missing `--by`/`--ref`) → do not merge; ask the human again. The prod approval is never delegated (`role` is always `human`).
3. Merge (the prod-gate hook lets it through only with the ledger entry):
   ```bash
   gh pr merge "{pr}" --merge                          # GitHub      ⇒ PROD pipeline
   az repos pr update --id "{pr}" --status completed   # Azure Repos ⇒ PROD pipeline
   ```

**2.10 — PROD post-deploy verification (Step 2-bis).** Wait for the PROD pipeline and run the post-deploy verification over production with `--env prod`, then record its result in `deploys` with the `deploy-record` command the tool prints. A `regression` → the rollback path of Step 2-bis. With a UI, PROD shows exactly `{version}`. Keep the green pipeline run URL and the result: archive records them (`advance … deployed --pipeline-run <url> --post-deploy-check pass`). **Another clone** than the one that deployed has no release ledger: it records the deploy as attested, with the decision and the run (REQ-W2-053):
```bash
python3 "$S" advance "{change-id}" deployed --attested --ref "D-NN" --pipeline-run "{url}"
```

**2.11 — Branch hygiene** (`deploy-workflow.md` → *Branch hygiene*). Delete what production absorbed; never delete what it did not:
```bash
git fetch origin --prune
git branch -r --merged "origin/$P"             # + the cherry / tree checks of the rule
git push origin --delete "feature/{change-id}"   # only if absorbed
git branch -d "feature/{change-id}"
```
Absorbed non-protected branches are deleted (closing their PR with a comment); **not absorbed ones are listed** with their unique commits and PR for the human. Report the counts.

### Step 2-bis — Post-deploy verification

After each deploy (DEV in 2.6, PROD in 2.10), against the post-deploy contract `karvey-infra` wrote in `infra.md` (REQ-W2-075..078). The word "canary" is kept only where the platform really splits traffic between two versions; everything else is **post-deploy verification**.
```bash
PD="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-postdeploy.py"
python3 "$PD" probe "{change-id}" --env "{env}" --json        # health + routes, spread over the window
# gather error rate, p95, the production baseline p95 and new 5xx from the contract's metrics_source into
# observed.json — a presented command, under the plan gate (platform-specific; the script only compares numbers)
python3 "$PD" evaluate "{change-id}" --env "{env}" --observed observed.json --version "{version}" --json
```
1. The result is `pass`, `regression` or `not-evaluated` — **say it as the tool says it**. The probe table and the thresholds go to `docs/spec/changes/{change-id}/deploy_evidence.md`.
2. **No contract, or no thresholds** → `not-evaluated`, with the recommendation to add the contract to `infra.md`; it is never reported as a pass.
3. Record every result with the printed command: `python3 "$S" deploy-record "{change-id}" --env "{env}" --version "{version}" --verification {result} --evidence docs/spec/changes/{change-id}/deploy_evidence.md`.
4. **`regression`** (REQ-W2-078):
   - DEV → stop before prod.
   - PROD → show the contract's `rollback.command` and **ask the human** with `AskUserQuestion` (*Roll back now (recommended)* / *Keep and investigate*). The rollback affects production: it runs only after that answer, through the plan gate, never on the agent's initiative. Then record it: `python3 "$S" deploy-record "{change-id}" --env prod --version "{version}" --verification regression --rollback "{what was run}" --evidence …`.
   - Open the incident with a reserved number: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-id.py" next BUG`, then the `BUG-NN` row in `docs/bugs_dev_testing.md` and a finding in the change's `findings.md` (`../karvey/rules/incident-tracking.md`).

### Step 3 — Hard rules (NEVER skip)

- **NEVER commit directly on the integration or production branch**; always a feature branch.
- **Integration by PR** (env-branches): never a local merge pushed into integration.
- **Living spec on the change branch (2.4-bis) and the release gate (2.8-bis) before the production PR**; the PR body lists every change of the manifest.
- **NEVER deploy manually** — `func azure functionapp publish` and equivalents are forbidden; the pipeline deploys.
- **`pull` before starting and before each merge/PR.**
- **Prod NEVER without the human's explicit OK**, recorded as D-NN + PR + ledger (`approve … prod`); never as a commit.
- **NEVER request the prod OK with the PR's gates red or unresolved.**
- **NEVER assume the git host** — detect it from the remote.
- **`patch` / `hotfix` = fix + BUG-NN + finding + regression test in the same PR** (`lane_triplet`).
- **One version bump per release**, from `[Unreleased]`, in Step 2.3.
- **Branches:** absorbed → deleted; not absorbed → never deleted, reported.
- **Zero downtime**: the post-deploy verification reinforces it; a prod regression → the rollback is proposed to the human, never run without the answer.
- In multi-repo, the dependency order of `architecture.md`.

### Step 4 — Record in the tracker

Resolve the tracker with `python3 "$C" resolve management --change "{change-id}" --json` (`../karvey/rules/management-adapters.md`, including its missing-map clause). If `external` is true: `create_task("[Deploy] {change-id}")` with the checklist as subtasks, `set_status(…, in_progress)` while it runs, `link(…, PR)`, `set_status(…, done)` on the PROD confirmation, `blocked` if the gate or the post-deploy verification stops it; a failed call goes to the outbox (`karvey-config.py outbox add`). Otherwise add to `PLAN.md` the deploy status per repo and environment:

```markdown
## Deploy — {change-id}
| Repo | DEV | PROD |
|------|-----|------|
| {repo1} | ✅ deployed | 👀 PR open / ✅ merged |
```

### Step 5 — Notify the team + final output

Send the `deploy` notification per `../karvey/rules/notifications.md`: `python3 "$C" resolve notifications --json`; `none` or `deploy` not in `events` → skip and say so. Run `python3 "$C" notify-check` first: exit 10 (destination changed) → show old and new destination and ask the human before sending. Post in the channel's own markup: repos + versions, DEV/PROD state, post-deploy verification, branches. A failed send is reported, not swallowed.
Send once per version and environment: `python3 "$C" notify-sent {change-id} --event deploy --version {version} --env {env} --run-id {pipeline run}` must say `new` (a retry of the same version says `sent`: report the retry's run id, send nothing), then re-run it with `--record`.

```
✅ Deploy complete — {change-id}

Repos (dependency order):
  - {repo1}: v{version} · DEV ✅ verification pass | PROD {✅ merged, verification pass / 👀 PR open, awaiting the human's OK}
Checklist: verified · QA: OK (0 critical, 0 high) · Tests: PASS · Release: [Unreleased] → [x.y.z]
Prod approval: {by} · {D-NN} · ledger ✅ (check-prod)   Type: {feature | ops | hotfix (BUG-NN)}
Platform: {…} · Prod URL: {prod_url} · Pipeline run: {url}
Post-deploy verification: DEV {pass / regression / not-evaluated} · PROD {pass / regression → rollback asked / not-evaluated} · deploy_evidence.md
Branches: deleted {N} ({list}) · kept {N} ({branch}: not absorbed, PR #{n})
{UI} Visible version: {yes / recommended}
Management: {[Deploy] in {tool} → {status} | PLAN.md updated} · Notification: {channel → target | skipped}

Next step: /karvey-archive {change-id}
```

## Advance to the next phase

Close the phase per `../karvey/rules/gates.md` (§ Phases without a gate): this phase has no approval of its own; state the next step — `/karvey-archive`, as `karvey-state.py next {change-id}` names it — and continue into it only when the user's request already covered the chain. In a new session, `karvey-state.py next {change-id}` says where the change is.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
