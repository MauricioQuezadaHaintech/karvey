---
name: karvey-requirements
description: Generate EARS-format requirements and spec-delta for a Karvey spec. Creates Features in the team's tracker or updates PLAN.md. Use after karvey-init. Triggers include "karvey requirements", "generar requisitos", "generate requirements", "especificar requisitos", "specify requirements".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, AskUserQuestion
argument-hint: <change-id> [-y]
---

# Karvey Requirements

## Purpose

Generate requirements in EARS format for the change, produce the spec-delta with ADDED/MODIFIED/REMOVED operations, and register the Features in the team's tracker (`karvey/rules/management-adapters.md`) or PLAN.md.

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/prd.md` (PRD generated in karvey-init)
- `docs/spec/changes/{change-id}/proposal.md`
- `docs/spec/specs/{capability}/spec.md` (current living spec)
- `rules/ears-format.md`
- `rules/living-specs.md`
- `rules/security-tiers.md`

The requirements must derive from the PRD and cover its objectives and acceptance criteria.

**Multi-agent / multi-repo context** (see `karvey/rules/multi-agent.md`):
- If `links.parent` is set, also read the **parent change's** `prd.md` and acceptance criteria in its repo: this child's requirements trace to the parent PRD.
- For each `decisions` entry (`D-NN@{repo}`), read the decision in the operations repo's decision log.
- For each `inputs.*` entry (`design`, `design_system`, `copy`, `legal`), read the file **at the pinned commit** (`git -C {repo} show {commit}:{path}`), not the working copy. If an input the requirements need is missing or unpinned, ask for it — never assume "the latest version".

If there's a `karvey-grill` brief in the conversation, incorporate it.

If the codebase is brownfield: dispatch a subagent to explore existing implementations:
> "Explore the codebase looking for functionality related to {capability}. Summarize: (1) what exists, (2) relevant interfaces/endpoints, (3) patterns the new requirements must respect. Less than 100 lines."

### Step 2 — Clarify scope before generating

For each functional area identified in `proposal.md`, ask whether there's any scope ambiguity or edge-case behavior. Ask only the necessary questions — don't ask about what's already clear.

**Don't ask about**: technology, architecture, implementation patterns (that goes in karvey-architecture).

### Step 3 — Generate a draft of requirements.md

Generate it grouping requirements by functional area. Apply strict EARS format.
Keep it as a draft in memory — do NOT write it yet.

Document structure:
```markdown
# Requirements: {change-id}

## Project description
{2-3 lines of the problem and objective}

## Requirement 1: {Functional area name}

### 1.1 {Requirement name}
WHEN {event},
the {system} SHALL {observable behavior}.

Traces to PRD: {PRD section or objective}{ · Decision: D-NN (if it exists because of a business decision)}{ · Input: copy|legal|design @{commit} (if it comes from a pinned input)}

#### Scenario: {Success case}
GIVEN {precondition}
WHEN {action}
THEN {observable result}

#### Scenario: {Error case}
GIVEN {precondition}
WHEN {invalid action}
THEN the system {specific error response}

### 1.2 {Next requirement}
...

## Requirement 2: {Next area}
...

## Explicit exclusions
- {What is not in scope and why}
- {Behavior that does not change}
```

### Step 4 — Review gate (before writing)

Check the draft:
- [ ] Each requirement is testable and contains no ambiguity
- [ ] Each requirement traces to a section or objective of the PRD
- [ ] All PRD objectives are covered by at least one requirement
- [ ] No requirement mentions implementation technology
- [ ] The IDs are numeric (1.1, 1.2, 2.1...)
- [ ] Each requirement has at least one success scenario and one error scenario
- [ ] The explicit exclusions cover the most likely edges
- [ ] The security requirements reflect the Security Tier declared in spec.json
- [ ] Every requirement that exists because of a business decision cites its `D-NN`, and no requirement contradicts a decision linked in `spec.json:decisions` (a contradiction needs a new decision first — blocking)
- [ ] Legal/copy texts are taken from the pinned `inputs.legal` / `inputs.copy` commit, not rewritten

If there are issues local to the draft: fix and re-check (maximum 2 iterations).
If there's a real ambiguity that requires a user decision: ask before continuing.

### Step 5 — Write requirements.md

```
docs/spec/changes/{change-id}/requirements.md
```

Update `spec.json`:
- `phase: "requirements-generated"`
- `approvals.requirements.generated: true`
- `updated_at: {timestamp}`

### Step 6 — Generate spec-delta.md

Compare the new requirements against `docs/spec/specs/{capability}/spec.md`.

For each new requirement: `## ADDED Requirements` section
For each requirement that modifies an existing one: `## MODIFIED Requirements` section
For each requirement that removes an existing one: `## REMOVED Requirements` section

If the capability is new (empty spec.md), everything is ADDED.

Write `docs/spec/changes/{change-id}/specs/{capability}/spec-delta.md`.

### Step 7 — Present for approval

Show a summary:
```
📋 Requirements generated: docs/spec/changes/{change-id}/requirements.md

Areas covered:
  - Requirement 1: {name} ({N} requirements)
  - Requirement 2: {name} ({N} requirements)

Spec-delta:
  - ADDED: {N} requirements
  - MODIFIED: {N} requirements
  - REMOVED: {N} requirements

Review gate: ✅ passed

Do you approve the requirements to continue?
```

If the `-y` flag is present: auto-approve.

If the user approves: update `spec.json` with `approvals.requirements.approved: true` plus `by`, `role` (`human` | `ceo-delegate`), `date` and `ref` (the `D-NN` where the approval is recorded) — see `karvey/rules/multi-agent.md` §4.

**`ops` changes** (`spec.json:type = "ops"`): requirements are **lite** — the verifiable goal, one EARS requirement per observable end state (e.g. "the deploy service account SHALL hold role X on project Y") and the rollback expectation. No mockup/design phases follow; the next step is `/karvey-infra`.

### Step 8A — Create Features in the team's tracker (`management-adapters.md`)

Read `spec.json` to get the tracker ids (`clickup.epic_id`, `clickup.backlog_list_id` — the block keeps its historical key for every tool).
Create one Feature per functional area in requirements.md: `create_feature(epic, area)` in `project.json:management.tool`
(skip the level if `management.hierarchy` has no feature level; Jira/ADO: issue/work item of type Feature, Linear: sub-issue or project milestone, GitHub Projects: issue added to the project, spreadsheet: a `feature` row).

**ClickUp adapter example:**
```
clickup_create_task
  name: "E{n}.F{n} {Feature name}"
  list_id: "{backlog_list_id}"
  task_type: "Feature"
  tags: ["{client_tag}"]
  description: (see format)
```

Feature description format:
```
E{n}.F{n}: {Feature name}

Description:
{what it does, value to the user, functional flow}

Permissions:
{who can use it: agent/supervisor/admin/system}

Flow:
1. {step 1}
2. {step 2}

Requirements covered: {N.N, N.N, ...}
Security Tier: {N}

Tasks: (pending — karvey-tasks)
Estimated time: (pending)
```

Link Epic ← Feature (parent/child or dependency, per tool). ClickUp: dependency via REST API:
```bash
curl -s -X POST "https://api.clickup.com/api/v2/task/{EPIC_ID}/dependency" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -d '{"depends_on":"{FEATURE_ID}"}'
```

Update `spec.json` with `clickup.feature_ids` (the tracker's ids).

### Step 8B — Update PLAN.md (Markdown)

Add a Features section in `PLAN.md` with the list of features and their covered requirements.

### Step 8C — Update the knowledge graph

Sync knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`) to reflect the documents created or modified.
If `docs/spec/graphify-out/` doesn't exist, invoke `/graphify docs/spec/` without `--update`.

### Step 9 — Final output

```
✅ Requirements approved

Files created/updated:
  - docs/spec/changes/{change-id}/requirements.md
  - docs/spec/changes/{change-id}/specs/{capability}/spec-delta.md
  - spec.json updated

Management: {Features E{n}.F1..F{n} created in {tool} | PLAN.md updated}

Next step:
/karvey-mockup {change-id}
```


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Mockup phase now?"
- If they confirm → run `/karvey-mockup {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (a gate of the method).
- If you resume in another session, `/karvey {change-id}` indicates which phase you're on and which one comes next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`. Karvey = Afán, an ona/selknam word.*
