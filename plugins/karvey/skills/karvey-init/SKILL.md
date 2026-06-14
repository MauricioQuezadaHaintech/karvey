---
name: karvey-init
description: Initialize a new Karvey spec. Creates the directory structure, spec.json, and registers the Epic in ClickUp (or PLAN.md if not using ClickUp). Use after karvey-grill or when starting a new feature. Triggers include "karvey init", "iniciar spec", "init spec", "nueva feature", "new feature", "nuevo cambio", "new change", "spec-driven", "SDD", "kiro", "cc-sdd", "gstack", "Garry Tan", "PRD", "iniciar proyecto spec-driven", "start spec-driven project", "nuevo método", "new method", "scaffolding".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id> [--capability <nombre>]
---

# Karvey Init

## Purpose

Initialize the structure of a new specification and register the Epic in the management system (ClickUp or Markdown).

## Execution steps

### Step 1 — Verify pre-spec context

If a `karvey-grill` summary exists in the conversation, use it to pre-populate the fields.
If not, ask the user: "Briefly describe the problem this change solves."

### Step 2 — Generate change-id

If `$ARGUMENTS` includes the change-id, use it. If not, generate it from the description:
- Format: `{add|fix|update|remove}-{descriptive-url-safe-name}`
- Examples: `add-call-transfer`, `fix-webhook-retry`, `update-tenant-config`
- Verify it doesn't already exist in `docs/spec/changes/`: `find docs/spec/changes -maxdepth 1 -type d -name "{change-id}"`
- If there's a conflict, add a numeric suffix: `add-call-transfer-2`

### Step 3 — Project config (project.json)

Check whether `docs/spec/project.json` exists.

**If it ALREADY exists:** read it and reuse its values. Don't ask anything about this config again.

**If it does NOT exist:** create it. Pre-populate from the `karvey-grill` synthesis if it's available in the conversation; ask for or infer the missing fields. The complete schema is in `karvey/rules/project-config.md` (cite that rule). Fields:

- **`git_platform`**: `github` | `azure_devops`.
- **`cloud.provider`**: `azure` | `gcp` | `aws` | `mixed` | `none`.
- **`iac_tool`**: `terraform` | `bicep` | `pulumi` | `none`.
- **`knowledge_sync`**: decide based on `karvey/rules/knowledge-sync.md` — if an Obsidian MCP is available in the session → `"obsidian"`; if not → `"graphify"`.
- **`repos`**: array of the project's repos. MINIMUM 1 element, never empty.
- **`spec_repo`**: if `repos` has 1 → that same one; if there are several → ask which is the main repo where `docs/spec/` lives.
- **`branch_flow`**: by default `{ "feature_prefix": "feature/", "integration": "dev", "production": "master" }`.

Write `docs/spec/project.json` with these values (see the schema in `karvey/rules/project-config.md`).

### Step 3.5 — Enforcement opt-in (hooks)

After creating `project.json`, ask the user whether they want to enable the Karvey method's **enforcement hooks**. See the detail in `karvey/rules/enforcement.md`.

```
Do you want to enable Karvey's enforcement hooks? (OPT-IN, you can enable them later)
  - git-flow hook: blocks direct commits to the integration/production branches and enforces the feature-branch flow (reads branch_flow).
  - plan-gate hook: blocks modifications without an approved plan.
```

**If they accept** one or both: set the `enforcement` block in `project.json`:
```json
"enforcement": {
  "git_flow_hook": true,
  "plan_gate_hook": true
}
```
(set `true` only on the ones the user accepted). Tell the user the hooks are installed by running:
```
/karvey-guard --install
```
`karvey-guard --install` writes the hooks into the project's `settings.json`, reading `branch_flow` from `project.json`.

**If they do NOT accept:** leave both flags at `false`. Enforcement is OPT-IN — never force it.
```json
"enforcement": {
  "git_flow_hook": false,
  "plan_gate_hook": false
}
```

### Step 4 — Ask about the management system

```
Does this project use ClickUp for management?
```

**If YES (ClickUp):**
- Ask: Which project/backlog does it belong to? (get the ClickUp `backlog_list_id`)
- Read the rule: `rules/clickup-protocol.md`

**If NO (Markdown):**
- A `PLAN.md` will be created in the change's directory
- No additional configuration is required

### Step 5 — Collect metadata

Ask (or infer from the pre-spec context):

1. **Capability**: the functional domain it belongs to (e.g., `call-management`, `authentication`, `notifications`). If it doesn't exist in `docs/spec/specs/`, it will be created.
2. **Security Tier**: 1-4. Read `rules/security-tiers.md` to guide the user.
3. **Layers involved**: DB / Backend / Frontend / Infra (can be multiple)
4. **Brief description**: 1-2 lines of the problem it solves
5. **Goal (the change's north star)**: the concrete objective being pursued — what observable, verifiable result defines the success of this change. Ask: "What is this change's north star? What concrete result do we want to achieve?". Save it verbatim in `spec.json` (`goal`) and reflect it as a highlighted section in `prd.md`.

> **Note — the goal provides persistence.** The `goal` remains the change's north star across all phases: each Karvey phase re-reads it on start to pursue the result without stopping until it's achieved, always respecting the plan and security gates.

### Step 6 — Create the directory structure

```bash
mkdir -p docs/spec/changes/{change-id}/specs/{capability}
mkdir -p docs/spec/specs/{capability}  # if it doesn't exist
```

If `docs/spec/specs/{capability}/spec.md` doesn't exist, create it:
```markdown
# Spec: {Capability}

<!-- Living spec for the {capability} capability. Updated when each change is archived. -->
```

### Step 7 — Create spec.json

Write `docs/spec/changes/{change-id}/spec.json` with:
```json
{
  "change_id": "{change-id}",
  "capability": "{capability}",
  "description": "{brief description}",
  "goal": "{the change's north star: concrete, verifiable result that defines success}",
  "layers": ["{DB|Backend|Frontend|Infra}"],
  "created_at": "{ISO timestamp}",
  "updated_at": "{ISO timestamp}",
  "language": "es",
  "management": "{clickup|markdown}",
  "security_tier": {1-4},
  "phase": "init",
  "clickup": {
    "epic_id": "",
    "feature_ids": [],
    "backlog_list_id": "{list_id or empty}",
    "client_tag": "{tag or empty}"
  },
  "approvals": {
    "requirements": { "generated": false, "approved": false },
    "mockup": { "generated": false, "approved": false },
    "design_graphic": { "generated": false, "approved": false },
    "architecture": { "generated": false, "approved": false },
    "tasks": { "generated": false, "approved": false },
    "infra": { "generated": false, "approved": false },
    "qa": { "generated": false, "approved": false },
    "deploy": { "generated": false, "approved": false }
  }
}
```

### Step 8 — Create prd.md

Write `docs/spec/changes/{change-id}/prd.md` (formal Product Requirements Document):
```markdown
# PRD: {change-id}

## Executive summary
{2-3 line synthesis: what's being built and what for}

## 🎯 Goal (the change's north star)
> {concrete, verifiable result that defines the success of this change}

This goal is the north star that all Karvey phases pursue: each phase re-reads it on start to advance toward the result without stopping until it's achieved, respecting the plan and security gates.

## Problem and context
- **Who has it:** {affected users/roles}
- **Current situation:** {how it's solved today or why it hurts}
- **Impact:** {cost of not solving it}

## Objectives and success metrics
{measurable objectives, e.g. "reduce X from N to M", "enable Y for Z users"}

## User stories / main use cases
- As a {role}, I want {action} so that {benefit}.
- {…}

## Scope (in scope)
- {what IS part of this change}

## Out of scope
- {what is NOT included and why}

## Stakeholders
{who requests, who approves, who is impacted}

## Constraints
- Security Tier: {N} — {justification}
- Prerequisite dependencies: {list}

## Acceptance criteria
{verifiable conditions to consider the change complete}
```

### Step 9A — Create the Epic in ClickUp (if management=clickup)

Read credentials from `.connections.json` (see `rules/clickup-protocol.md`). If it doesn't exist, create it and add it to `.gitignore` before continuing.
Determine the next Epic number by searching in ClickUp:
```
clickup_search
  keywords: "E{1..99}"
  filters.location.categories: ["{backlog_list_id}"]
```

Create the Epic:
```
clickup_create_task
  name: "E{n} {Epic name}"
  list_id: "{backlog_list_id}"
  task_type: "Epic"
  description: (see format in the rules)
  tags: ["{client_tag}"]
```

Update `spec.json` with `clickup.epic_id`.

Epic description format:
```
E{n}: {Epic name}

Definition:
{2-3 paragraph description: what problem it solves, for whom, why it matters}

Strategic Value:
{business impact}

Security Tier: {N} — {justification}

Design Decisions:
(pending — completed in karvey-architecture)

Features:
(pending — completed in karvey-requirements)

Built with the Karvey Method
```

### Step 9B — Create PLAN.md (if management=markdown)

Write `docs/spec/changes/{change-id}/PLAN.md`:
```markdown
# Plan: {change-id}

**Capability:** {capability} | **Security Tier:** {N} | **Layers:** {list}
**Created:** {date} | **Status:** 🟡 In progress

---

## Epic: {Name}

### Description
{problem, who, impact}

### Strategic value
{business impact}

### Design decisions
| Topic | Decision |
|------|----------|
| (pending — karvey-architecture) | |

---

## Features
(pending — karvey-requirements)

---

## Tasks
(pending — karvey-tasks)

---

## Task status
| Task | Status | Estimated time | Actual time |
|------|--------|----------------|-------------|
| (pending) | | | |

---

## History
| Date | Phase | Action |
|-------|------|--------|
| {date} | init | Spec initialized |
```

### Step 9C — Update the knowledge graph

Sync knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`) to reflect the documents created.
If `docs/spec/graphify-out/` doesn't exist (first time in the project), invoke `/graphify docs/spec/` without `--update`.

### Step 10 — Final output

```
✅ Spec initialized: docs/spec/changes/{change-id}/

Project config: docs/spec/project.json (created | read)

Files created:
  - docs/spec/changes/{change-id}/spec.json
  - docs/spec/changes/{change-id}/prd.md
  - docs/spec/changes/{change-id}/PLAN.md (if markdown)
  - docs/spec/specs/{capability}/spec.md (if new capability)

Management: {ClickUp Epic E{n} created | PLAN.md created}
Security Tier: {N}

Next step:
/karvey-requirements {change-id}
```

## Safety

- If `docs/spec/changes/{change-id}` already exists with a `spec.json`, ask before overwriting
- If ClickUp fails, offer to continue in markdown mode as a fallback
- Validate that the `change-id` is URL-safe (only lowercase letters, numbers, and hyphens)


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Requirements phase now?"
- If they confirm → run `/karvey-requirements {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (a gate of the method).
- If you resume in another session, `/karvey {change-id}` indicates which phase you're on and which one comes next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`. Karvey = Afán, an ona/selknam word.*
