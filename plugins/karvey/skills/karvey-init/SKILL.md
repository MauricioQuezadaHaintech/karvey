---
name: karvey-init
description: Karvey phase 1 — creates a change (spec.json, prd.md, Epic or PLAN.md) and, on first use, the team settings. Triggers include "karvey init", "nuevo cambio karvey", "new karvey change", "karvey settings", "configurar equipo karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id> [--capability <nombre>] | --settings
---

# Karvey Init

## Purpose

Create a new change and register its Epic in the team's management tool (`../karvey/rules/management-adapters.md`). The first time Karvey is used in a project it also asks the **team settings** — notification channel, task tool and status flow — because a plugin cannot run anything at install time (Step 3.2).

`S="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py"` and `C="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py"` below.

## Execution steps

### Step 0 — Settings-only mode (`--settings`) — STOP after it

If invoked as `/karvey-init --settings` (or the user only asks to configure the team), run **Step 3.2 only**:
pre-fill every question with the current values, merge the answers without dropping untouched keys
(`events`, `location`, custom keys), write `project.json` on a docs branch (Step 3.3), print the `Settings:`
line and **STOP**. No change-id, no `docs/spec/changes/…`, no `spec.json`, no tracker item. If `project.json`
does not exist, say so and ask whether to create a minimal one (Step 3 fields) — nothing else.

### Step 1 — Verify pre-spec context

If a `karvey-grill` summary exists in the conversation, use it to pre-populate the fields.
If not, ask the user: "Briefly describe the problem this change solves."

### Step 2 — Generate change-id

If `$ARGUMENTS` includes the change-id, use it. If not, generate it from the description:
- Format: `{add|fix|update|remove}-{descriptive-url-safe-name}` (lowercase letters, digits, hyphens), e.g. `add-call-transfer`
- If `docs/spec/changes/{change-id}` exists, add a numeric suffix: `add-call-transfer-2`

### Step 3 — Project config (project.json)

**If `docs/spec/project.json` exists** (in the working copy, or on `origin/{integration}` or `origin/{production}`: `git show "origin/$I:docs/spec/project.json"` with `I` from Step 3.3, then the same on the production branch): reuse it. Step 3 does **not** re-ask any of its fields; Step 3.2 may still ask the team settings when their blocks are missing.

**If it does not exist:** create it, pre-populated from the grill synthesis; ask for or infer the rest. Schema: `../karvey/rules/project-config.md`.

- **`git_platform`**: `github` | `azure_devops`.
- **`cloud.provider`**: `azure` | `gcp` | `aws` | `mixed` | `none`. **`iac_tool`**: `terraform` | `bicep` | `pulumi` | `none`.
- **`knowledge_sync`** (`../karvey/rules/knowledge-sync.md`): `obsidian` if an Obsidian MCP is in the session, `graphify` if graphify is installed, otherwise `none` — say once that the sync then does not run. It runs only at archive or on demand.
- **`repos`**: MINIMUM 1 element. **`spec_repo`**: the one repo, or ask which holds `docs/spec/`.
- **`branch_flow`**: default `{ "feature_prefix": "feature/", "integration": "dev", "production": "master" }`.

### Step 3.2 — Team settings (first use, or `--settings`)

Run when `project.json` lacks `notifications` or `management`, or on `--settings`. Otherwise ask nothing.
Ask with `AskUserQuestion`, one block at a time, with examples — never assume the answer:

1. **Notifications** (`../karvey/rules/notifications.md`): `Google Chat` · `Slack` · `Microsoft Teams` ·
   `E-mail` · `Webhook` · `None` · `Not now`. Then the **target** (space id, `#channel`, list, or the *name*
   of the secret holding a webhook — never a URL), **via** (`mcp` · `cli` · `webhook` · `api`, checking what
   is available) and **events** (default `qa`, `deploy`). **Not now** → write `notifications.deferred: true`
   and say how to set it later (`/karvey-init --settings`); the question is not asked again.
   If the project's `CLAUDE.md` holds a destination table (pre-3.10 setups), offer those values as the
   pre-filled answer for the human to confirm; nothing is read from `CLAUDE.md` after that.
2. **Task management** (`../karvey/rules/management-adapters.md`): `ClickUp` · `Jira` · `Linear` ·
   `Azure Boards` · `GitHub Projects` · `Spreadsheet` · `Markdown (PLAN.md)` · `Other`, then **location** and **via**.
3. **Status flow**: map the team's real statuses to `todo · in_progress · review · done · blocked`. For a
   tracker, read the statuses from the tool and propose the map; the user confirms. For `Markdown` the
   markers are fixed: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked · 🙋 awaiting-human (a blocked qualifier)`.

Credentials go to `.connections.json` (git-ignored) or the team's vault — never into `project.json`.

### Step 3.3 — Write the settings as a reviewed change

`project.json` changes travel on a docs branch and take effect **after merge** (the hooks read the reviewed
line on `origin/{production}`). Never commit it on the integration or production branch:

```bash
I="$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" get branch_flow.integration --shell)"
git switch -c "docs/karvey-settings" "origin/$I"   # skip if already on a feature/docs branch
```

Print one line: `Settings: notifications slack #dev-releases (webhook) · management jira PAY (5 states mapped)`
(or `notifications deferred`).

### Step 3.5 — Enforcement (hooks)

The plugin's hooks read `project.json:enforcement` (`../karvey/rules/enforcement.md`); nothing is copied into
`settings.json`. `prod-gate` is on by default. Ask whether to turn on the opt-in ones:

```
- git-flow: blocks commits on the integration/production branches (reads branch_flow).
- plan-gate: blocks edits without an approval recorded from the human's own message.
```

Write the answer as flags (only what the user accepted is `true`), together with every `enforcement` default
the installed version declares (the `x-karvey-default` keys under `enforcement` in
`${CLAUDE_PLUGIN_ROOT}/schemas/project.schema.json`), so a new project starts current and the upgrade offer has
nothing to propose:
```json
"enforcement": { "git_flow_hook": false, "plan_gate_hook": false, "prod_gate_hook": true, "plan_marker_ttl_min": 120 }
```

### Step 4 — Management for this change

Resolve the tool, never ask "ClickUp or not?":

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" resolve management --json
```

`external: true` → the Epic goes to the resolved tool and location (Step 9A, logical operations of
`../karvey/rules/management-adapters.md`; ClickUp detail in `../karvey/rules/clickup-protocol.md`).
`external: false` → `PLAN.md` (Step 9B). Ask only if this change must be tracked somewhere else than the
project default; then write the override into `spec.json:management`.

### Step 5 — Collect metadata

Ask (or infer from the pre-spec context):

1. **Capability**: the functional domain (e.g., `call-management`). Created in `docs/spec/specs/` if new.
2. **Security Tier**: 1-4 (`../karvey/rules/security-tiers.md`).
3. **Layers**: DB / Backend / Frontend / Infra (can be multiple).
4. **Brief description**: 1-2 lines of the problem it solves.
5. **Goal (north star)**: the observable, verifiable result that defines success. Save it verbatim in `spec.json:goal` and as a highlighted section of `prd.md`. Every phase re-reads it on start.
6. **Change type**: `feature` (default) · `ops` · `hotfix` (`../karvey/rules/multi-agent.md` §6–7).
7. **Multi-repo links** (only if `project.json:repos` has several repos): `links.parent` / `links.children`
   as `{change-id}@{repo}`, business `decisions`, and pinned `inputs` (`"{repo} {path} @{commit}"`), per `../karvey/rules/multi-agent.md`.

### Step 6 — Directories and living spec

```bash
mkdir -p "docs/spec/changes/{change-id}" "docs/spec/specs/{capability}"
```

If `docs/spec/specs/{capability}/spec.md` doesn't exist, create it with `# Spec: {Capability}` and one comment line. The spec-delta of this change will live at the change root (`spec-delta.md`).

### Step 7 — Create spec.json

Write the descriptive fields to `docs/spec/changes/{change-id}/spec.json` (schema in `../karvey/rules/living-specs.md`; omit keys that don't apply):
```json
{
  "change_id": "{change-id}",
  "capability": "{capability}",
  "description": "{brief description}",
  "goal": "{north star}",
  "layers": ["{DB|Backend|Frontend|Infra}"],
  "language": "es",
  "security_tier": 2,
  "type": "{feature|ops|hotfix}",
  "links": { "parent": "", "children": [] },
  "decisions": ["D-NN"],
  "inputs": {},
  "iteration_count": 0,
  "revision_history": []
}
```

Then let the state tool add the state (phase `init`, `phase_history`, `approvals`) — never write those by hand:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" init "{change-id}" --by "{name}"
```

Approvals are recorded later by each phase with `karvey-state.py approve … --by --role --ref` (`../karvey/rules/state-machine.md`).

### Step 8 — Create prd.md

Write `docs/spec/changes/{change-id}/prd.md` (formal Product Requirements Document):
```markdown
# PRD: {change-id}

## Executive summary
{2-3 line synthesis: what's being built and what for}

## 🎯 Goal (the change's north star)
> {concrete, verifiable result that defines the success of this change}

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

`create_epic(change)` in the resolved tool and location (`../karvey/rules/management-adapters.md`), found by its
natural key (the change-id) before creating, so a re-run does not duplicate it. Credentials from
`.connections.json`, env vars or a vault — never in the repo. The Epic is created in **`todo`**, whatever the tool.
Store the returned id in the tracker-ids block of `spec.json` (`clickup.epic_id`, the historical key for every tool).

Epic description (same for every tool):
```
{Epic name}

Definition: {what problem it solves, for whom, why it matters}
Strategic Value: {business impact}
Security Tier: {N} — {justification}
Design Decisions: (pending — karvey-architecture)
Features: (pending — karvey-requirements)

Built with the Karvey Method
```

### Step 9B — Create PLAN.md (Markdown)

Write `docs/spec/changes/{change-id}/PLAN.md`:
```markdown
# Plan: {change-id}

**Capability:** {capability} | **Security Tier:** {N} | **Layers:** {list}
**Created:** {date} | **Status:** ⬜ todo

## Epic: {Name}
### Description
{problem, who, impact}
### Strategic value
{business impact}
### Design decisions
| Topic | Decision |
|------|----------|
| (pending — karvey-architecture) | |

## Features
(pending — karvey-requirements)

## Tasks
(pending — karvey-tasks)

## History
| Date | Phase | Action |
|-------|------|--------|
| {date} | init | Spec initialized |
```

### Step 10 — Final output

```
✅ Spec initialized: docs/spec/changes/{change-id}/   (phase init, via karvey-state.py)
Project config: docs/spec/project.json (created | read)
Settings: {notifications … · management … | unchanged}
Files: spec.json · prd.md · PLAN.md (if Markdown) · docs/spec/specs/{capability}/spec.md (if new)
Management: {Epic created in {tool} ({location}) | PLAN.md}
Security Tier: {N} · Type: {feature | ops | hotfix} · Links: {…| none}

Next step:
/karvey-requirements {change-id}      (feature, ops — lite requirements)
/karvey-iterate {change-id}           (hotfix — register BUG-NN + finding first)
```

## Safety

- If `docs/spec/changes/{change-id}/spec.json` already exists, ask before touching it (`karvey-state.py init` refuses a file that has a phase)
- If the tracker fails, offer to continue with `PLAN.md` as a fallback (and say so)

## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Requirements phase now?"
- If they confirm → run `/karvey-requirements {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (a gate of the method).
- If you resume in another session, `karvey-state.py next {change-id}` (or `/karvey {change-id}`) says where the change is.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`. Karvey = Afán, an ona/selknam word.*
