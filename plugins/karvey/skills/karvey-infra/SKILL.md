---
name: karvey-infra
description: Generate and configure cloud infrastructure (IaC) and CI/CD pipelines from the architecture's cloud spec. Idempotent over existing infra. Includes infra security review. Use after karvey-architecture. Triggers include "karvey infra", "infraestructura", "infrastructure", "pipeline CI/CD", "IaC", "terraform", "bicep".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, AskUserQuestion
argument-hint: <change-id> [-y]
---

# Karvey Infra

## Purpose

Generate and configure the **cloud infrastructure (IaC)** and the **CI/CD pipelines** from the "Cloud Infrastructure" section of the change's `architecture.md`. This is **PHASE 6** of the Karvey Method, between `karvey-architecture` (PHASE 5) and `karvey-tasks` (PHASE 7).

The phase is **idempotent over existing infra**: it never recreates what is already there, it only creates what is missing or modifies what is needed. It includes an **infra security review** as a gate, and respects the team's deployment flow (deploy via pipeline, never manual).

## Execution steps

### Step 1 — Load context

Read in parallel:
- `docs/spec/changes/{change-id}/spec.json` (especially `security_tier`, `layers`, `management`)
- `docs/spec/changes/{change-id}/architecture.md` (especially the **"## Cloud Infrastructure"** section: which services from which cloud)
- `docs/spec/project.json` (fields `git_platform`, `cloud.provider`, `iac_tool`, `repos`, `spec_repo`, `branch_flow`)
- Shared rules: `rules/project-config.md`, `rules/deploy-workflow.md`, `rules/changelog-policy.md`, `rules/knowledge-sync.md`, `rules/security-tiers.md`

Entry checks:
- If `docs/spec/project.json` **does not exist** → **stop** and indicate to run `karvey-init` first (see `project-config.md`).
- Verify `approvals.architecture.approved = true`. If it is **not** approved → **stop**: the architecture must be approved before generating infra.

### Step 2 — Discovery of existing infra (idempotency)

The goal is to **NOT recreate what already exists**, only to create what is missing or modify what is needed.

Explore **each repo** in `project.json:repos` (dispatch subagents in parallel if there are several) looking for:

**Existing IaC:**
- Folders `terraform/`, `bicep/`, `infra/`, `pulumi/`
- Files `*.tf`, `*.tfvars`, `*.bicep`, `Pulumi.yaml`, `Pulumi.*.yaml`

**Existing CI/CD pipelines:**
- `.github/workflows/*.yml` / `*.yaml` (GitHub Actions)
- `azure-pipelines.yml` / `azure-pipelines-*.yml` (Azure Pipelines)
- `.gitlab-ci.yml` (reference, if applicable)

Report findings in a summary:

```
Infra discovery
──────────────────
Repo {repo}:
  IaC:        {terraform/ found | no IaC}
  Pipelines:  {.github/workflows/deploy.yml | no pipeline}
  Already-declared resources: {brief list}
```

Based on the discovery, decide for each resource/pipeline: **create** (does not exist), **modify** (exists but is missing something from the change) or **leave as is** (already compliant).

### Step 3 — Generate / update IaC

The resources to create/modify come from the **"## Cloud Infrastructure"** section of `architecture.md` (which services, from which cloud). Generate per `iac_tool` from `project.json`:

| `iac_tool` | Output | Notes |
|------------|--------|-------|
| `terraform` | `.tf` files (+ `.tfvars` per environment) | modules per service; remote state backend |
| `bicep` | `.bicep` files (+ `.bicepparam` per environment) | one module per resource/group |
| `pulumi` | per the project's language (TS/Python/Go/C#) | stacks per environment |
| `none` | **does not generate IaC** | skip to pipelines (Step 4), leave an **explicit note** that infra is manual |

**Provider (`cloud.provider`):**
- `azure` → Azure resources (Resource Group, Function App, SQL, Key Vault, Storage, etc.)
- `gcp` → GCP resources (Cloud Run/Functions, Cloud SQL, Secret Manager, GCS, etc.)
- `aws` → AWS resources (Lambda, RDS, Secrets Manager, S3, IAM, etc.)
- `mixed` → generate **per provider**, per what `architecture.md` indicates for each service (e.g. compute in one cloud, data in another). Separate by folder/module per provider.

Idempotency rule: only write/edit what Step 2 marked as create/modify. Do not touch already-compliant resources. Parameterize per environment (`dev`/`prod`) without duplicating logic.

### Step 4 — Generate / update CI/CD pipelines

Generate per `git_platform` from `project.json`:

| `git_platform` | Output |
|----------------|--------|
| `github` | `.github/workflows/` (GitHub Actions) |
| `azure_devops` | `azure-pipelines.yml` (Azure Pipelines) |

**The pipeline MUST respect the team's flow** (see `deploy-workflow.md`), reading `branch_flow` from `project.json`:
- Push to the **integration** branch (`branch_flow.integration`, default `dev`) → **triggers deploy to DEV**.
- Merge to the **production** branch (`branch_flow.production`, default `master`) → **triggers deploy to PROD**.
- **NEVER manual deploy.** The pipeline is the only deployment mechanism (no `func azure functionapp publish`, no manual `terraform apply`, etc.).
- Prod requires an **explicit human OK** (protected environment / PR approval).

The pipeline must include, as applicable: IaC validation/lint (`terraform validate`/`fmt`, `bicep build`), plan in PR, apply on push to the environment's branch, and the application deploy. The actual `apply` is run by the pipeline, **not** by hand (see Restrictions).

### Step 4b — Auto-detection and one-time configuration of the deploy platform

**Goal:** automatically detect the project's deployment platform and leave it configured/documented **one single time**, so that later phases (especially `karvey-deploy`, PHASE 11) do not have to re-discover it. Inspired by gstack's `/setup-deploy` flow.

**Idempotency (one-time):** if the detected deploy configuration already exists ("Deploy platform" block in `infra.md`, or a platform config file already present and referenced), **do not re-configure**: only verify that it is still valid and report "already configured". Only run the full detection when it is missing.

**Platform detection** (explore the repos in `project.json:repos`, dispatch subagents if there are several). Signals per platform:

| Platform | Signals (files / config) |
|------------|------------------------------|
| Fly.io | `fly.toml` |
| Render | `render.yaml` |
| Vercel | `vercel.json`, `.vercel/` folder |
| Netlify | `netlify.toml`, `.netlify/` folder |
| Heroku | `Procfile`, `app.json`, `heroku` remote |
| Azure | Function App / App Service / Static Web Apps in IaC, `azure-pipelines.yml` |
| AWS | Lambda/ECS/Amplify in IaC, `samconfig.toml`, `serverless.yml` |
| GCP | Cloud Run / App Engine in IaC, `app.yaml` |
| GitHub Actions (generic deploy) | `.github/workflows/*deploy*.yml` |
| Custom | `deploy.sh`/`Makefile` scripts with a deploy target, or another proprietary mechanism |

Cross-check what is detected against `cloud.provider` and `git_platform` from `project.json` (they must be consistent; if not, report the discrepancy).

**Discover and document** (whatever can be inferred from the existing config; whatever cannot, leave marked as `<pending>` without inventing it):
- **Production URL** (the project's domain on the platform; e.g. `app` from `fly.toml`, Vercel's `name`, the App Service host).
- **Health check** (the endpoint/command that confirms the deploy is healthy; e.g. `GET /health`, a readiness path).
- **Deploy commands** per environment (the one the pipeline runs, e.g. `flyctl deploy`, `vercel deploy --prod`), remembering that the actual deploy is triggered by the **pipeline**, never by a manual run (see `deploy-workflow.md` and Restrictions).

**Leave configured/documented:**
- In `infra.md`, add/update the **"## Deploy platform"** block with: detected platform, production URL, health check, deploy commands per environment, and the mapping to `branch_flow` (dev/prod).
- In the **pipelines** (Step 4): reflect the detected platform (the corresponding deploy action/step, post-deploy health check if applicable) without duplicating what is already present.

**Target agnosticism (see `../karvey/rules/targets.md`):** the **release channel depends on the target**, "web" is not assumed by default. Per the `targets` of `project.json`, the deploy platform/channel may be: web pipeline, **App Store/TestFlight** (iOS), **Play Store** (Android), **package registry** (`library`/`sdk`), **OTA** (`embedded`), etc. The detection and configuration must correspond to the real target; if there are several targets, document the channel for each one.

Format of the block to write in `infra.md`:

```markdown
## Deploy platform
- Platform:          {fly.io | render | vercel | netlify | heroku | azure | aws | gcp | github-actions | custom}
- Target / channel:  {web pipeline | App Store/TestFlight | Play Store | package registry | OTA | ...}
- Production URL:    {url | <pending>}
- Health check:      {endpoint or command | <pending>}
- Deploy command:    dev → {command}  ·  prod → {command}  (run by the pipeline)
- Status:            {just configured | already configured (verified)}
```

### Step 5 — Infra security review (gate)

Generate a **findings checklist** by reviewing:

- **IAM / least-privilege roles**: each identity (service principal, managed identity, service account, IAM role) has only the permissions it needs; no `Owner`/`*:*`/`roles/owner` except with explicit justification.
- **Secrets in a secrets manager**: Azure Key Vault / GCP Secret Manager / AWS Secrets Manager. **NEVER hardcoded** in `.tf`/`.bicep`/YAML nor in pipeline variables in cleartext. Reference by name/ID.
- **Network exposure**: **nothing public** unless `architecture.md` justifies it. Databases and backends with no public IP by default; restrictive firewall/NSG/Security Group rules.
- **Encryption at rest and in transit**: storage/DB with encryption at rest; TLS mandatory in transit (HTTPS, encrypted connections to the DB).
- **Security Tier**: the `security_tier` from `spec.json` is respected **at the infra level** (see `security-tiers.md`); the higher the tier, the stricter the controls (network segmentation, rotated secrets, logging/auditing, etc.).

Checklist format:

```markdown
## Infra security review
| Control | Status | Severity | Finding / action |
|---------|--------|-----------|-------------------|
| IAM least privilege | OK / Fail | — / High | {detail} |
| Secrets in manager | OK / Fail | — / Critical | {detail} |
| No public exposure | OK / Fail | — / High | {detail} |
| Encryption at rest/transit | OK / Fail | — / Medium | {detail} |
| Security Tier respected | OK / Fail | — / High | {detail} |
```

**Gate:** **critical and high findings must be resolved** before continuing (fix the IaC/pipeline and re-review). Medium/low findings are documented in `infra.md`.

### Step 6 — Hard restrictions (apply during all steps)

- **NEVER apply to PRODUCTION** (`terraform apply` / `az deployment ... create` / `pulumi up` against prod) without an **explicit human OK**.
- For **DEV**, you may apply **only if the user approves** in this flow. If they did not approve, leave the IaC ready and let the pipeline apply it.
- The **actual apply is preferably done by the pipeline**, not by hand (see `deploy-workflow.md`).
- **Zero downtime mandatory**: no infra change may cause a service outage.

### Step 7 — CHANGELOG

Any IaC/pipeline generated or modified **must record an entry** in the `CHANGELOG.md` of the corresponding repo, per `changelog-policy.md`:
- At the root of **each repo** in `project.json:repos` that received infra/pipeline changes.
- *Keep a Changelog* format + a traceability block with the **responsible human** (from `git config user.*`), the **AI model**, the "why" (not just the what), the `change-id` and `Karvey phase: infra`.

### Step 8 — Management

Record in the project's management, reading `management` from `spec.json`:
- `management = clickup` → create tasks with the `[Infra]` prefix per relevant resource/pipeline.
- `management = markdown` → add entries in `PLAN.md` with the status of the infra and pipelines per repo/environment.

### Step 9 — Write output and update spec.json

Write the change's output:

```
docs/spec/changes/{change-id}/infra.md
```

`infra.md` documents:
- **Resources** created/modified/compliant (per provider and environment).
- **CI/CD pipelines** generated and their mapping to `branch_flow` (dev/prod).
- **Deploy platform** (the block from Step 4b: detected platform, production URL, health check, deploy commands and release channel per target).
- **Security review** (the checklist from Step 5 with findings and resolutions).
- Idempotency notes (what was reused) and, if `iac_tool = none`, the manual-infra note.

Update `spec.json`:
- `phase: "infra-generated"`
- `approvals.infra.generated: true`

After presentation/approval (auto-approve if flag `-y`; if not, present a summary and ask for approval):
- `approvals.infra.approved: true`
- `phase: "infra-approved"`

### Step 10 — Knowledge sync

At the end, run the sync step per `rules/knowledge-sync.md`:
- If `knowledge_sync = "obsidian"` → sync `infra.md` to the vault via the Obsidian MCP (with a fallback to graphify if it fails).
- If `knowledge_sync = "graphify"` → `/graphify docs/spec/ --update` (or `/graphify docs/spec/` if `graphify-out/` does not exist).
- Multi-repo with infra code changes → graphify also in the affected repos.

### Step 11 — Final output

Confirm and show the next step:

```
✅ Infra generated and approved

Next step:
/karvey-tasks {change-id}
```

## Safety

Hard gates that are **NEVER** skipped:

- **No prod without a human OK**: never apply IaC nor deploy to production without explicit human approval. The actual deploy is triggered by the pipeline (push to `dev`, merge to `master`), never a manual apply (see `deploy-workflow.md`).
- **No hardcoded secrets**: no secret in `.tf`/`.bicep`/Pulumi/YAML nor in pipeline variables in cleartext. Everything via Key Vault / Secret Manager / Secrets Manager.
- **Idempotency**: never recreate existing infra; only create what is missing or modify what is needed. Respect the discovery from Step 2.
- **Zero downtime**: no infra change may cause a service outage.
- **Security gate**: critical/high findings from Step 5 block progress until resolved.


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Tasks phase now?"
- If they confirm → run `/karvey-tasks {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (the method's gate).
- If you resume in another session, `/karvey {change-id}` shows which phase you are in and which one is next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
