---
name: karvey-init
description: Initialize a new Karvey spec. Creates the directory structure, spec.json, and registers the Epic in the team's tracker (ClickUp, Jira, Linear, Azure Boards, GitHub Projects, a spreadsheet or PLAN.md). On first use it asks the team settings (notification channel, task tool, status flow); `--settings` changes them later. Use after karvey-grill or when starting a new feature. Triggers include "karvey init", "iniciar spec", "init spec", "nueva feature", "new feature", "nuevo cambio", "new change", "karvey settings", "configurar equipo", "team settings", "spec-driven", "SDD", "kiro", "cc-sdd", "gstack", "Garry Tan", "PRD", "iniciar proyecto spec-driven", "start spec-driven project", "nuevo método", "new method", "scaffolding".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id> [--capability <nombre>] | --settings
---

# Karvey Init

## Purpose

Initialize the structure of a new specification and register the Epic in the team's management tool (`karvey/rules/management-adapters.md`). The first time Karvey is used in a project it also asks the **team settings** — notification channel, task-management tool and its status flow — because a plugin cannot run anything at install time (Step 3.2).

## Execution steps

### Step 0 — Settings-only mode (`--settings`) — STOP after it

If invoked as `/karvey-init --settings` (or the user only asks to configure the team — "karvey settings",
"configurar equipo"), this is **settings-only mode**:
1. Read `docs/spec/project.json`. If it does not exist, say so and ask whether to create a minimal one
   (Step 3 fields) — do not create anything else.
2. Run **Step 3.2 only**, pre-filling every question with the **current values** and changing only what the
   user changes. Merge the answers into the existing blocks — never drop keys the user did not touch
   (`events`, `location`, custom keys).
3. Write `project.json`, report the one-line summary of Step 3.2, and **STOP**.

In settings-only mode **do NOT** generate a change-id, create `docs/spec/changes/…`, write `spec.json` or
`prd.md`, create an Epic/Feature/Task in any tracker, or advance to any phase. Configuring the team is
not starting a change.

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

### Step 3.2 — Team settings (first use, or `--settings`)

A plugin cannot run anything at install time, so the team's settings are asked **here, the first time**
Karvey is used in the project. Run this step when `project.json` lacks `notifications` or `management`, or
when invoked as `/karvey-init --settings` (to change them later — see Step 0: in that mode it is the ONLY
step that runs). If both blocks exist and there is no `--settings`, skip it and ask nothing.

Ask with `AskUserQuestion`, one block at a time, showing examples — never assume the answer:

1. **Notifications** (`karvey/rules/notifications.md`) — *Where does the team get QA and deploy notices?*
   `Google Chat` · `Slack` · `Microsoft Teams` · `E-mail` · `Webhook` · `None`.
   Then: the **target** (space id, `#channel`, team/channel, list, or the *name* of the secret holding the
   webhook — never the URL itself), **how** this session reaches it (`mcp` · `cli` · `webhook` · `api`,
   checking what is actually available), and the **events** (default `qa`, `deploy`).
2. **Task management** (`karvey/rules/management-adapters.md`) — *Where does the team track its work?*
   `ClickUp` · `Jira` · `Linear` · `Azure Boards` · `GitHub Projects` · `Spreadsheet (Excel/Sheets/CSV)` ·
   `Markdown (PLAN.md)` · `Other`. Then the **location** (list id, project key, team, file path) and **via**.
3. **Status flow** — map the team's real statuses to the 5 logical states `todo · in_progress · review ·
   done · blocked`. For a tracker, **read the statuses from the tool** (list/project/workflow) and propose
   the mapping; the user confirms or corrects it. For a spreadsheet or `Other`, ask the names. For
   `Markdown`, the markers are fixed (`⬜ 🔄 👀 ✅ ⛔`).

Write both blocks into `project.json`. Credentials go to `.connections.json` (git-ignored) or the team's
vault — never into `project.json`. Report the result in one line, e.g.
`Settings: notifications slack #dev-releases (webhook) · management jira PAY (5 states mapped)`.

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

### Step 4 — Management for this change

Use the team's tool from `project.json:management` (Step 3.2) — do not ask "ClickUp or not?". Set
`spec.json:management` to that tool name. Only ask if this change must be tracked somewhere else than the
project default (rare: e.g. a client's board).

- **ClickUp:** the Epic goes to `management.location` (the `backlog_list_id`); protocol in `rules/clickup-protocol.md`.
- **Jira / Linear / Azure Boards / GitHub Projects / Spreadsheet / Other:** the logical operations of
  `karvey/rules/management-adapters.md`, resolved for that tool.
- **Markdown:** a `PLAN.md` is created in the change's directory; nothing else to configure.

### Step 5 — Collect metadata

Ask (or infer from the pre-spec context):

1. **Capability**: the functional domain it belongs to (e.g., `call-management`, `authentication`, `notifications`). If it doesn't exist in `docs/spec/specs/`, it will be created.
2. **Security Tier**: 1-4. Read `rules/security-tiers.md` to guide the user.
3. **Layers involved**: DB / Backend / Frontend / Infra (can be multiple)
4. **Brief description**: 1-2 lines of the problem it solves
5. **Goal (the change's north star)**: the concrete objective being pursued — what observable, verifiable result defines the success of this change. Ask: "What is this change's north star? What concrete result do we want to achieve?". Save it verbatim in `spec.json` (`goal`) and reflect it as a highlighted section in `prd.md`.

6. **Change type**: `feature` (default) · `ops` (no application code: IAM, DNS, secrets, console config) · `hotfix` (urgent production fix). See `karvey/rules/multi-agent.md` §6–7.
7. **Multi-repo / multi-agent links** (ask only if `project.json:repos` has more than one repo or an operations repo exists):
   - Does this change belong to a **parent change** in another repo? → `links.parent = "{change-id}@{repo}"`, and append this change as `"{change-id}@{this-repo}"` to the parent's `links.children` (if the parent repo is out of reach, say so and leave the instruction for its owner). If this change **is** the parent, fill `links.children` as the children are created.
   - Which **business decisions** (`D-NN`) is it based on? → `decisions: ["D-NN@{ops-repo}"]`.
   - Does it consume work from other agents (design, design system, copy, legal)? → `inputs.{design|design_system|copy|legal} = "{repo} {path} @{commit}"`, pinning the commit actually read.

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
  "management": "{project.json:management.tool — clickup|jira|linear|azure-boards|github-projects|spreadsheet|markdown|other}",
  "security_tier": {1-4},
  "phase": "init",
  "type": "{feature|ops|hotfix}",
  "links": { "parent": "{change-id@repo or empty}", "children": [] },
  "decisions": ["{D-NN@repo}"],
  "inputs": {
    "design": "{repo path @commit — only the keys that apply}"
  },
  "iteration_count": 0,
  "revision_history": [],
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
    "deploy": { "generated": false, "approved": false },
    "prod": { "by": "", "date": "", "ref": "" }
  }
}
```

Each approval, when granted, also records `by`, `role` (`human` | `ceo-delegate`), `date` and `ref` (`D-NN`) — see `karvey/rules/multi-agent.md` §4. Omit `links`/`decisions`/`inputs` values that don't apply (keep the keys empty), and the full schema is in `karvey/rules/living-specs.md`.

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

### Step 9A — Create the Epic in the team's tracker

`create_epic(change)` in the tool of `project.json:management.tool` (`karvey/rules/management-adapters.md`),
at `management.location`. Credentials from `.connections.json` (git-ignored), env vars or a vault — never in the repo.
The Epic description format below is the same for every tool.

**ClickUp adapter example** (protocol in `rules/clickup-protocol.md`):

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

Update `spec.json` with `clickup.epic_id` (the tracker-ids block keeps this historical key for every tool).

**Other tools** — same operation, per `management-adapters.md` → Adapters:
- **Jira:** create an issue of type Epic in the project key (Atlassian MCP, `jira` CLI or REST); store the issue key.
- **Linear:** create a project/parent issue in the team (Linear MCP or GraphQL); store its id.
- **Azure Boards:** `az boards work-item create --type Epic` in the project/area; store the work-item id.
- **GitHub Projects:** create an issue and `gh project item-add` it to the project; store the item id.
- **Spreadsheet:** append an `epic` row (`id, level, title, layer, estimate_min, status=todo, updated_at, link`).
- **Other:** as recorded in `management.location` + `via`; with no programmatic path, create `PLAN.md` (9B) and tell the user what to copy.

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

### Step 9B — Create PLAN.md (Markdown)

Write `docs/spec/changes/{change-id}/PLAN.md`:
```markdown
# Plan: {change-id}

**Capability:** {capability} | **Security Tier:** {N} | **Layers:** {list}
**Created:** {date} | **Status:** 🔄 in_progress

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
> Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked`

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
  - docs/spec/changes/{change-id}/PLAN.md (if Markdown)
  - docs/spec/specs/{capability}/spec.md (if new capability)

Management: {Epic E{n} created in {tool} ({location}) | PLAN.md created}
Security Tier: {N}

Type: {feature | ops | hotfix}   Links: {parent → … | children: … | none}

Next step:
/karvey-requirements {change-id}      (feature, ops — lite requirements)
/karvey-iterate {change-id}           (hotfix — register BUG-NN + finding first)
```

## Safety

- If `docs/spec/changes/{change-id}` already exists with a `spec.json`, ask before overwriting
- If the tracker fails, offer to continue with `PLAN.md` as a fallback (and say so)
- Validate that the `change-id` is URL-safe (only lowercase letters, numbers, and hyphens)


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Requirements phase now?"
- If they confirm → run `/karvey-requirements {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (a gate of the method).
- If you resume in another session, `/karvey {change-id}` indicates which phase you're on and which one comes next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`. Karvey = Afán, an ona/selknam word.*
