---
name: karvey-context
description: Read-only dashboard of the current project spec state: project config (project.json), capabilities, active/archived changes, sprint status, and a deploy-queue / landing report (which changes are in dev, in prod, ready to release, and versions per repo). Use at any point in the Karvey pipeline. Triggers include "karvey context", "estado del proyecto", "project status", "qué specs hay", "what specs exist", "cambios activos", "active changes", "cola de despliegue", "deploy queue", "landing report", "qué hay en dev", "what's in dev", "qué falta liberar", "what's left to release".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [--capability <name>] [--change <change-id>]
---

# Karvey Context

## Purpose

Quick view of the project's complete state: project config (`project.json`), documented capabilities, in-progress changes, archived changes, current sprint, spec coverage, and the **deploy queue / landing report** (deploy status per change and versions per component/repo).

> **Read-only.** This dashboard NEVER writes, modifies, deploys, or runs git that alters state (no `commit`, `push`, `merge`, `fetch`, `pull`). It only reads repo files (`project.json`, `spec.json`, `CHANGELOG.md`) and, optionally, local `git log`. To deploy, use `karvey-deploy`.

## Execution steps

### If --capability is specified

Show the capability detail:
```bash
cat docs/spec/specs/{capability}/spec.md
grep -c "### Requirement:" docs/spec/specs/{capability}/spec.md
grep -c "#### Scenario:" docs/spec/specs/{capability}/spec.md
```

### If --change is specified

Show the change detail:
```bash
cat docs/spec/changes/{change-id}/spec.json
cat docs/spec/changes/{change-id}/proposal.md
# Approval status
```

### If nothing is specified — Full dashboard

#### Project config (if `docs/spec/project.json` exists)

```bash
# Read project-level config
cat docs/spec/project.json 2>/dev/null
```

If it exists, show a header with its content (see format below). If it does NOT exist, indicate "no project.json (run karvey-init)" and continue with the rest of the dashboard anyway. This view is **read-only**: never write or modify `project.json`.

```bash
# Capabilities
find docs/spec/specs -mindepth 1 -maxdepth 1 -type d 2>/dev/null

# Requirements per capability
for cap in docs/spec/specs/*/; do
  name=$(basename "$cap")
  reqs=$(grep -c "### Requirement:" "$cap/spec.md" 2>/dev/null || echo "0")
  echo "$name: $reqs requirements"
done

# Active changes
find docs/spec/changes -maxdepth 1 -type d -not -path "docs/spec/changes" -not -path "*/archive" 2>/dev/null

# Archived changes
ls docs/spec/changes/archive/ 2>/dev/null | wc -l
```

#### Deploy queue / Landing report (read-only)

Snapshot of the deploy status per change. **It does not run git, does not deploy, does not write anything** — it only reads the main repo and the `repos` from `project.json` to infer the status. It is the Karvey equivalent of the "landing report".

For each active change, derive its deploy status from `spec.json` (`phase` and `approvals.deploy` fields):

```bash
# Phase/deploy status per active change
for ch in $(find docs/spec/changes -maxdepth 1 -mindepth 1 -type d -not -name archive 2>/dev/null); do
  id=$(basename "$ch")
  phase=$(grep -o '"phase"[^,]*' "$ch/spec.json" 2>/dev/null | head -1)
  dep=$(grep -o '"deploy"[^}]*}' "$ch/spec.json" 2>/dev/null | head -1)
  qa=$(grep -o '"qa"[^}]*}' "$ch/spec.json" 2>/dev/null | head -1)
  echo "$id | $phase | qa=$qa | deploy=$dep"
done
```

Status mapping (read-only, inferred — **it is not the cloud's truth, it is what the spec says**):
- **Ready to release**: `approvals.qa.approved=true` and `approvals.deploy.approved=false` (QA OK, not yet deployed).
- **In dev**: `phase` indicates an in-progress deploy to integration, or `approvals.deploy.generated=true` with the merge to `integration` done and the PR to `production` still open/unmerged.
- **In prod**: `approvals.deploy.approved=true` (merge to `production` with human OK) or the change is already archived.
- **Not ready**: any other state (QA pending or incomplete release gate).

Deployed versions per component/repo — read the `CHANGELOG.md` of each repo in `project.json:repos` (the top version of the changelog is the last released for that component). **Read-only, no `git`:**

```bash
# Current version per repo (from its CHANGELOG.md)
# REPOS comes from project.json:repos
for repo in $REPOS; do
  ver=$(grep -m1 -oE '\[?[0-9]+\.[0-9]+\.[0-9]+\]?' "$repo/CHANGELOG.md" 2>/dev/null)
  echo "$repo: ${ver:-no CHANGELOG}"
done
```

If `git` is available and you want to refine what is in dev vs prod per repo (optional, **read-only**, no `fetch`/`pull`):

```bash
# dev↔prod difference already known locally (does not fetch)
# integration/production come from project.json:branch_flow
git -C "$repo" log --oneline {production}..{integration} 2>/dev/null | wc -l
# >0 ⇒ there are commits in integration not yet released to production
```

Show to the user:

```
📊 Karvey Context — {date}

PROJECT  (docs/spec/project.json)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{project name}
  Targets: {targets}            Cloud: {cloud.provider} / IaC: {iac_tool}
  Git: {git_platform}           Knowledge sync: {knowledge_sync}
  Repos ({N}): {repo1, repo2, …}  (main: {spec_repo})
  Branch flow: {feature_prefix} → {integration} → {production}
  Enforcement: git_flow_hook={on|off}  plan_gate_hook={on|off}
  (if no project.json → "no project.json — run karvey-init")

CAPABILITIES ({N} total)
━━━━━━━━━━━━━━━━━━━━━━━━
{capability-1}: {N} requirements, {N} scenarios
{capability-2}: {N} requirements, {N} scenarios

ACTIVE CHANGES ({N})
━━━━━━━━━━━━━━━━━━━━
{change-id-1}
  Phase: {phase}
  Capability: {capability}
  Security Tier: {N}
  Management: {ClickUp Epic E{n} | Markdown}
  Approvals: requirements={✅|⬜} mockup={✅|⬜} design={✅|⬜} arch={✅|⬜} tasks={✅|⬜}

{change-id-2}
  ...

ARCHIVED CHANGES: {N}
Last archived: {date-change-id}

DEPLOY QUEUE / LANDING REPORT  (read-only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deploy status per change (inferred from spec.json — it is not the cloud's truth):

  🟢 READY TO RELEASE ({N})
    {change-id}  — QA OK, deploy pending  (capability: {capability})

  🟡 IN DEV ({N})
    {change-id}  — deployed to {integration}, PR to {production} pending

  🔵 IN PROD ({N})
    {change-id}  — released to {production}  ({date})

  ⬜ NOT READY ({N})
    {change-id}  — {QA pending | incomplete release gate}

Deployed versions per component/repo (top of CHANGELOG.md):
    {repo1}: {x.y.z}   {repo2}: {x.y.z}   {repo3}: {no CHANGELOG}
    (if local git is available: "{repo}: {N} commits in {integration} not released to {production}")

ACTIVE SPRINT
━━━━━━━━━━━━
{verify with clickup_get_workspace_hierarchy or indicate "not applicable (markdown)"}
```

### For the active sprint (if ClickUp is available)

```
clickup_get_workspace_hierarchy
  max_depth: 2
```

Look for the "Dev Sprints Metodo Karvey" folder and the active sprint.

Show:
```
Active sprint: Sprint {N} (until {date})
Sprint tasks: {total} | In progress: {N} | Ready for PAP: {N} | Blocked: {N}
```

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
