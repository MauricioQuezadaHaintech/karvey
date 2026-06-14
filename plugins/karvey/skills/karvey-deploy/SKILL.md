---
name: karvey-deploy
description: Execute the ordered deployment flow (feature branch → dev → PR master) honoring the team's hard rules. Pull before start and before merge. Pipeline-triggered, never manual. Prod requires explicit human OK. Bumps semver + changelog before push, auto-detects the deploy platform, and runs a post-deploy canary loop (dev and prod) to guard zero-downtime. Use after karvey-qa passes. Triggers include "karvey deploy", "desplegar", "deploy", "liberar", "release", "subir a dev", "push to dev", "pasar a prod", "promote to prod".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: <change-id>
---

# Karvey Deploy

## Purpose

PHASE 11 of the Karvey Method, between `karvey-qa` (PHASE 10) and `karvey-archive` (PHASE 12). It executes the **ordered deployment flow** (feature branch → `dev` → PR to `master`) honoring the team's hard rules to the letter: never commit directly to `dev`/`master`, never deploy manually (the deploy is triggered by the pipeline), `pull` before starting and before each merge/PR, and **prod never without explicit human OK**.

It runs **only after** `karvey-qa` has passed with no open critical/high findings. The central rule is `karvey/rules/deploy-workflow.md`; follow it exactly.

## Execution steps

### Step 0 — Pre-checks (release gate)

BEFORE touching git, read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/project.json`

If `project.json` does not exist, stop and indicate to run `karvey-init` first (see `karvey/rules/project-config.md`).

Verify the release gate. If **anything fails, STOP and report what is missing. Do not deploy.**

1. **QA approved with no open critical/high findings.**
   - Locate the most recent review document: `REVISION_PR_*_{date}.md` at the root of each affected repo (`ls -t REVISION_PR_*.md | head -1`).
   - The `karvey-qa` security gate must be OK: **0 critical findings and 0 unresolved high findings** in the severity table / pre-merge checklist.
   - Confirm QA status in `spec.json` (`approvals.qa` / `phase`).

2. **Tests PASS.** Review `docs/test_evidence.md`: there must be entries for the `{change-id}` with PASS result for the change's tests.

3. **CHANGELOG updated in each affected repo** (see `karvey/rules/changelog-policy.md`). For each repo in `project.json:repos` with changes, verify `CHANGELOG.md`:
   - [ ] Entry for the current version.
   - [ ] **Responsible human** (name + contact) — never empty nor replaced by "AI".
   - [ ] **AI model** that assisted (e.g., `Claude Opus 4.8`).
   - [ ] The **why**, not just the what.
   - [ ] CHANGELOG version matches the project's version file.

If any of these fail, report exactly what is missing and stop. **Do not deploy.**

### Step 1 — Determine repos and order

Read from `project.json`:
- `repos` (array, at least 1).
- `branch_flow`: `feature_prefix` (default `feature/`), `integration` (default `dev`), `production` (default `master`).

If the change touches **multiple repos**, honor the dependency order declared in `architecture.md` (e.g., **DB → backend → frontend**). For each repo, the Step 2 flow is applied in that order.

Record the resolved order before starting.

### Step 1.5 — Auto-detection of the deploy platform

Before deploying, confirm **how and where** each repo is released. If `project.json` already declares it (`deploy.platform`, `deploy.prod_url`, `deploy.health_check` per repo), use that. If it is **not configured**, detect it and record it in `project.json` for future runs.

**Detect the platform** by evidence in the repo (do not assume):

| Signal in the repo | Likely platform |
|------------------|---------------------|
| `fly.toml` | Fly.io |
| `render.yaml` | Render |
| `vercel.json` / `.vercel/` | Vercel |
| `netlify.toml` | Netlify |
| `host.json` + `azure-pipelines.yml` / `.github/workflows/*azure*` | Azure Functions (pipeline) |
| `.github/workflows/*.yml` | GitHub Actions (the workflow target defines the actual destination) |
| `azure-pipelines.yml` / `.azure-pipelines/` | Azure DevOps Pipelines |
| `Dockerfile` + `k8s/` or `helm/` manifests | Kubernetes |

**Discover the production URL and health check:**
- Look for the prod URL in `project.json:deploy`, pipeline variables, `README`/`docs/spec/`, or the platform config (e.g., `fly.toml`, `vercel.json`).
- Determine the health endpoint: `/health`, `/healthz`, `/api/health`, the frontend's root page, or whatever `architecture.md` declares. For non-web targets (CLI/API/mobile), the "health check" is the equivalent in the target's **actual runtime** (see `karvey/rules/targets.md`).

If the prod URL/health cannot be discovered, **do not invent it**: record it as pending and ask the user for the data before the prod canary. The hard rule stands: the deploy is triggered by the pipeline, this detection is **only** to know **where to monitor**, never to deploy manually.

Record what was detected in `project.json:deploy` (`platform`, `prod_url`, `dev_url`, `health_check`) per repo.

### Step 2 — Ordered deployment flow (FOR EACH repo)

Apply following `karvey/rules/deploy-workflow.md` EXACTLY, in the dependency order from Step 1.

**2.1 — `git pull` before starting:**
```bash
git pull
```

**2.2 — Ensure feature branch.** NEVER commit directly to `dev`/`master`. Verify you are working on `feature/{change-id}`:
```bash
git branch --show-current   # must be feature/{change-id}
```
If the `feature/{change-id}` branch does not exist, **stop** — `karvey-impl` should have created it. Do not create it here.

**2.3 — Before the merge, `pull` integration:**
```bash
git pull origin {integration}     # default: dev
```

**2.4 — Version bump + CHANGELOG BEFORE the push (see `karvey/rules/versioning.md` and `karvey/rules/changelog-policy.md`).** This is part of the 6-step checklist (Step 3) and is mandatory: **NEVER deploy without bumping the version.**

1. **Determine the semver segment to increment** (`major.minor.rev`) per the nature of the change:
   - **major** → breaking change (breaks API/contract/schema/behavior compatibility).
   - **minor** → new backward-compatible feature.
   - **rev** → fix/adjustment/minor change with no new feature.
2. **Version bump in each affected component/repo.** Edit the version file per the stack (`package.json`, `pyproject.toml`, `*.csproj`, `VERSION`, git tags, etc.). If a repo has several deployable components, bump the one of the component that changed.
3. **Document in `CHANGELOG.md` per component AND per repository** (`changelog-policy.md` format): an entry for the new version with the **responsible human** (name + contact, never empty nor "AI"), the **AI model** that assisted (e.g., `Claude Opus 4.8`), and the **why** of the change (not just the what). Indicate the incremented semver segment and why.
4. **(If the repo has a frontend) recommend a version visible in the UI** — see Step 2.4-bis.

**2.4-bis — Version visible in the front (recommendation).** If any `target` in `project.json` is `web`/mobile/desktop with a UI (check `project.json:targets`), **recommend to the user** exposing the version in the interface (footer, "About" screen) for visible traceability in production: inject the version at build time (e.g., `VITE_APP_VERSION` or the stack's equivalent) and show it in a discreet but accessible place. If the version is already visible, just confirm it was updated with the bump.

**2.5 — Merge feature → integration:**
```bash
git checkout {integration}        # dev
git merge feature/{change-id}
```

**2.6 — Push to integration ⇒ triggers DEV pipeline** (the deploy is done by the pipeline, NOT manually):
```bash
git push origin {integration}     # dev → triggers DEV pipeline
```

**2.7 — Post-deploy canary in DEV (see Step 2-bis):** wait for the pipeline to deploy and run the **canary loop** over the actual DEV runtime (green pipeline build + health monitoring). Do not advance to prod if DEV did not end up healthy or if the canary detects a regression.

**2.8 — Before the PR, `pull` production:**
```bash
git pull origin {production}      # default: master
```

**2.9 — Create PR `dev` → `master`:**
```bash
gh pr create --base {production} --head {integration} \
  --title "[Deploy] {change-id}" \
  --body "Deploy of {change-id}. QA OK, tests PASS, CHANGELOG updated. Requires human OK to merge to prod."
```

**2.10 — Merge to `master` ONLY with explicit human OK ⇒ triggers PROD pipeline.**
Use `AskUserQuestion` to request explicit prod approval. Without human OK, **do not merge**. With OK:
```bash
gh pr merge --merge          # ⇒ triggers PROD pipeline
```

**2.11 — Post-deploy canary in PROD (see Step 2-bis):** after the merge to `master`, wait for the PROD pipeline and run the **canary loop** over the actual production runtime (`prod_url` / health from Step 1.5). It is the direct reinforcement of zero-downtime: if the canary detects a regression, **alert and recommend an immediate rollback**.

### Step 2-bis — Post-deploy canary loop (zero-downtime reinforcement)

Inspired by gstack's `/canary` and adapted to the target's actual runtime (see `karvey/rules/targets.md`). It runs **after each deploy** (in DEV after 2.7 and in PROD after 2.11), pointing at the just-deployed environment (`dev_url`/`prod_url` and health from Step 1.5). It watches that the deploy did not degrade the service.

**What the loop watches (several iterations, not a single check):**
1. **Console/log errors** — browser console (web, via `karvey-browse`), runtime/platform logs (Functions, container, etc.). Look for new errors that did not exist before the deploy.
2. **Performance regressions** — latency/response time of the health and of key endpoints; compare against the pre-deploy baseline. Noticeable degradation = regression.
3. **Page/endpoint failures** — walk through the change's critical routes/endpoints and the product's main ones; any 5xx, timeout, or broken page counts as a failure.

**How to run it:**
- Rely on **`karvey-browse`** ("get eyes") for the target's runtime: headless browser (web), simulator/device (mobile), HTTP client (API), process/terminal (CLI). It does not assume a browser.
- Repeat the cycle (console → performance → pages/endpoints) over a reasonable window post-deploy (several spaced iterations), not a single shot. Record evidence of each iteration.
- In DEV: if the canary flags a regression, **stop and do not advance to prod**; fix it first.
- In PROD: if the canary flags a regression, **alert immediately and recommend a rollback** (revert the merge / deploy the previous version via pipeline). Never leave prod degraded. The rollback is also executed by the pipeline, never manually.

**Canary result:** OK (no regressions) or REGRESSION (with detail of what failed: console/perf/endpoint). Leave the result recorded for the final output and management.

### Step 3 — 6-step checklist (before the push to dev)

From `karvey/rules/deploy-workflow.md`. Show and verify before the push to `dev`:

1. Am I on a feature branch? (not `dev`/`master`)
2. Did I bump the semver version (major/minor/rev) in each affected component/repo and update `CHANGELOG.md` per component and per repo? (see `versioning.md` and `changelog-policy.md`; if there is a frontend, did I recommend/update the version visible in the UI?) **NEVER deploy without bumping the version.**
3. Is everything pending committed?
4. Pushed the branch?
5. Merged to `dev`?
6. Pushed `dev`?

Only after the 6 → the pipeline deploys dev. For prod, repeat the verification and PR to `master` with human approval.

### Step 4 — Hard rules (NEVER skip)

- **NEVER commit directly to `dev` or `master`.** Always a feature branch.
- **NEVER deploy manually.** The deploy is triggered by the pipeline (push to `dev`, merge to `master`). `func azure functionapp publish` or manual equivalents are FORBIDDEN.
- **`pull` before starting and before each merge/PR.**
- **Prod NEVER without explicit human OK.** The PR to `master` is not merged without approval.
- **NEVER deploy without bumping the version** (semver + CHANGELOG per component and repo).
- **Zero downtime**: the deployment cannot cause a service outage; the post-deploy canary reinforces this and, on a prod regression, recommends a rollback (via pipeline, never manual).

### Step 5 — Record in management

Read `management` from `spec.json`.

**If `management = clickup`:** create task `[Deploy] {change-id}` with the 6-step checklist as subtasks and close it on prod confirmation:
```
clickup_create_task
  name: "[Deploy] {change-id}"
  list_id: "{sprint_list_id}"
  priority: "high"
```
For each repo, record DEV and PROD deploy status. Close the task on confirming the merge to prod (PROD pipeline OK).

**If `management = markdown`:** add an entry in `PLAN.md` with the deploy status **per repo and environment**:
```markdown
## Deploy — {change-id}
| Repo | DEV | PROD |
|------|-----|------|
| {repo1} | ✅ deployed | ⏳ PR open / ✅ merged |
| {repo2} | ... | ... |
```

### Step 6 — Update spec.json

```
spec.json:
  phase: "deployed"
  approvals.deploy.generated: {YYYY-MM-DD}
  approvals.deploy.approved: {YYYY-MM-DD if there was prod human OK, otherwise null}
```

### Step 7 — Knowledge sync

Run the sync step of `karvey/rules/knowledge-sync.md` per `knowledge_sync` in `project.json`:
- `obsidian` → sync the modified documents to the vault via the Obsidian MCP (fallback to graphify if it fails).
- `graphify` → `/graphify docs/spec/ --update` (if `docs/spec/graphify-out/` does not exist, without `--update`).
- Multi-repo with code changes → graphify also in each affected repo.

### Step 8 — Final output

```
✅ Deploy complete — {change-id}

Repos deployed (in dependency order):
  - {repo1}: v{new_version} · DEV ✅ canary OK  |  PROD {✅ merged, canary OK / ⏳ PR open, awaiting human OK}
  - {repo2}: v{new_version} · DEV ✅ canary OK  |  PROD ...

6-step checklist: verified
QA gate: OK (0 critical, 0 high) · Tests: PASS · Version bumped + CHANGELOG: OK
Deploy platform: {Fly | Render | Vercel | Netlify | Azure | GitHub Actions | ...} · Prod URL: {prod_url}
Post-deploy canary: DEV {OK / REGRESSION} · PROD {OK / REGRESSION → rollback recommended / N/A}
{If there is a frontend} Version visible in UI: {yes / recommended to the user}

Management: {[Deploy] {change-id} in ClickUp | PLAN.md updated}
Knowledge sync: {obsidian | graphify} updated

Next step: /karvey-archive {change-id}
```

## Safety

- **NEVER commit directly to `dev` or `master`** — always a feature branch.
- **NEVER deploy manually** — `func azure functionapp publish` and equivalents are forbidden; the deploy is triggered by the pipeline (push `dev`, merge `master`).
- **`pull` before starting and before each merge/PR.**
- **Prod NEVER without explicit human OK** — the PR to `master` is not merged without approval.
- **NEVER deploy without bumping the version** — semver (major/minor/rev) bumped and CHANGELOG per component and per repo (see `versioning.md` and `changelog-policy.md`).
- **Zero downtime** — the deployment cannot cause a service outage; the post-deploy canary (DEV and PROD) reinforces this and, on a prod regression, recommends a rollback (always via pipeline, never manual).
- **Mandatory release gate** — without QA OK (0 critical/high), tests PASS, version bumped, and CHANGELOG complete, no deploy happens.
- In multi-repo, honor the dependency order from `architecture.md` (DB → backend → frontend).


## Advance to the next phase

When finishing this phase and having the corresponding approval, **actively ask the user**: "Shall we advance to the Archive (closure) phase now?"
- If they confirm → run `/karvey-archive {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (the method's gate).
- If you resume in another session, `/karvey {change-id}` indicates which phase you are in and which one follows.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
