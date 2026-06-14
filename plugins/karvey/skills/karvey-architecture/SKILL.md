---
name: karvey-architecture
description: Generate enterprise architecture design with explicit security controls, component boundaries, and integration patterns. Use after karvey-design-graphic. Triggers include "karvey architecture", "diseño técnico", "technical design", "arquitectura", "architecture", "diseño de sistema", "system design".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, AskUserQuestion
argument-hint: <change-id> [-y]
---

# Karvey Architecture

## Purpose

Generate the enterprise architecture technical design: components, boundaries, integrations, security controls per tier, observability, and a concrete file structure per layer.

## Execution steps

### Step 1 — Load context

Read in parallel:
- `docs/spec/changes/{change-id}/spec.json` (security_tier, layers, capability)
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/design-spec.md`
- `docs/spec/project.json` (cloud.provider, iac_tool, git_platform)
- `rules/security-tiers.md`
- Project steering: `product.md`, `tech.md` or equivalents if they exist

Verify `approvals.design_graphic.approved = true`. If not, stop.

### Step 2 — Architecture discovery

**For features that extend the existing system (brownfield):**

Dispatch subagents to explore in parallel:
- Subagent A: `grep -r` of existing patterns related to the capability
- Subagent B: read existing endpoints/SPs of the affected area

Identify:
- Existing code patterns to follow (naming, function structure, error handling)
- Existing data access and its signatures (SPs, queries, ORM models, repositories, etc.)
- Existing API endpoints / operations and their contracts
- External integrations that already exist

**For completely new features (greenfield):**
- Define new patterns coherent with the existing stack

### Step 3 — Classify architectural complexity

| Type | Criterion | Discovery |
|------|----------|-----------|
| Simple addition | Only adds CRUD or UI with no new logic | Minimal |
| Extension | Extends the existing system with new logic | Medium |
| New capability | New capability, no existing base | Complete |
| Complex integration | Integration with an external or multi-layer system | Exhaustive |

### Step 4 — Generate architecture.md draft

Required structure:

```markdown
# Architecture: {change-id}

## Summary
{1 paragraph: what it solves and how, at a high level}

## Diagrams (MANDATORY — at least one)

This architecture MUST include at least one mermaid diagram: **data flow** and/or **components**. Recommended to generate it with the cross-cutting `karvey-diagram` skill, which produces mermaid coherent with the rest of the spec.

```mermaid
{component or data flow diagram — ideally generated with /karvey-diagram}
```

> Minimum required: 1 diagram. For "Complex integration" or "New capability" features, include both (components + data flow).

## System boundary
**This spec owns:**
- {component/endpoint/SP 1}
- {component/endpoint/SP 2}

**This spec does NOT touch:**
- {existing component that is kept}
- {adjacent functionality out of scope}

**Changes that require revalidating this design:**
- {condition 1 that would make this design obsolete}

## Components and responsibilities

### DB layer
| Component | Type | Responsibility | Security Tier |
|------------|------|----------------|---------------|
| `{schema}.{sp_name}` | New SP / function | {what it does} | Tier {N} |
| `{table}` | Modified table | {which column/index} | Tier {N} |

**DB security controls:**
- User context validation in every query/SP: YES/NO
- Typed parameters (no dynamic SQL/query): YES/NO
- Logging of critical operations: YES/NO

### Backend layer
| Component | Type | Responsibility | Security Tier |
|------------|------|----------------|---------------|
| `{backend_path}/{name}` | New endpoint / function | {what it does} | Tier {N} |
| `{module}` | Modified module | {what changes} | Tier {N} |

**Backend security controls:**
- Authentication required: Tier {N} → {mechanism: JWT, session, API key, etc.}
- Per-request user context validation: YES/NO
- Input sanitization at boundaries: YES/NO
- Error handling without exposing stack traces: YES/NO
- Sensitive variables via secrets manager: YES/NO

### Frontend layer
| Component | Type | Responsibility |
|------------|------|----------------|
| `{component}` | New component | {what it renders} |
| `{state_path}/{store}` | New/modified store | {what state it manages} |
| `{api_layer}/{service}` | API service | {which endpoints it consumes} |

**Frontend security controls:**
- Auth checks on routes: Frontend only as UX, enforcement in the backend
- Do not expose other tenants' data in the store
- Sanitization of dynamic outputs (no unsanitized v-html)

### External integrations
| System | Direction | Protocol | Auth | Timeout |
|---------|-----------|-----------|------|---------|
| {system} | inbound/outbound | REST/WebSocket | {mechanism} | {ms} |

## Cloud infrastructure

**Cloud provider(s):** {from `project.json` `cloud.provider`. If `mixed`, explicitly specify which part of the system runs in which cloud — e.g.: "backend and DB on Azure; file storage on GCP Cloud Storage"}

| Cloud service | Cloud | Purpose | Layer | Security Tier |
|----------------|------|-----------|------|---------------|
| {e.g. Azure Functions} | Azure | {what it does} | Backend | Tier {N} |
| {e.g. Azure SQL} | Azure | {what it does} | DB | Tier {N} |
| {e.g. GCP Cloud Storage} | GCP | {what it does} | {layer} | Tier {N} |

**Region(s) / zone:** {e.g. East US 2 / southamerica-west1}

**IaC tool:** {from `project.json` `iac_tool`}. The IaC code will live in {where — e.g. `infra/` of the corresponding repo, or a dedicated infra repo}.

**Deployment trigger:** push to `dev` → deploy DEV; merge to `master` → deploy PROD. Always triggered by the pipeline, NEVER manual.

> The IaC detail (modules, concrete resources) and pipelines are generated by PHASE 6 (`/karvey-infra`). This section only declares which services from which cloud are used at the design level.

## Main data flow

```
{Actor} → {Frontend} → {API Gateway / BFF} → {Backend} → {DB / Service}
                                                    ↓
                                         {External system}
```

Describe the flow step by step for the main use case:
1. {step 1: what the actor does}
2. {step 2: how the frontend responds}
3. {step N: what is persisted in the DB}

## Trust boundaries

Explicitly mark WHERE untrusted input enters and WHERE it is validated. Any data crossing a boundary inward must be validated/sanitized at that crossing.

| Trust boundary | What crosses | Untrusted side | Where it is validated/sanitized | Control |
|---------------------|-----------|-------------------|--------------------------|---------|
| Client → Backend | {request payload} | Frontend / public network | {endpoint / entry layer} | {schema validation, auth, sanitization} |
| Backend → DB | {query/SP parameters} | {backend layer} | {SP / data access layer} | {typed parameters, user context} |
| External system → Backend | {webhook / API response} | {external system} | {inbound handler} | {signature verification, payload validation} |

> Rule: no data from the untrusted side is used without validation. Mark each trust boundary crossing in the data flow diagram (e.g. dotted line `-. untrusted .->`).

## Security control points

| Point | Tier | Control |
|-------|------|---------|
| Endpoint entry | {N} | Validate auth token, extract user identity |
| DB / service call | {N} | Pass user context, do not trust input |
| Response to client | {N} | Do not leak other users'/tenants' data |
| Logging | {N} | Do not log PII or tokens |

## File plan (concrete)

### Files to CREATE
| File | Layer | Responsibility |
|---------|------|----------------|
| `{backend_path}/{name}` | Backend | {description} |
| `{frontend_path}/{name}` | Frontend | {description} |

### Files to MODIFY
| File | Layer | Change |
|---------|------|--------|
| `{backend_path}/{existing}` | Backend | Add {what} |

### DB files
| File | Type | Change |
|---------|------|--------|
| `{db_path}/{sp_name}.sql` | New SP / migration | {description} |

## Observability strategy

- Structured logging at: {log points}
- Metrics to track: {list}
- Recommended alerts: {list}
- Request traceability: {correlationId, userId/contextKey in every log}

## Architectural decisions

| Decision | Alternative considered | Why this one was chosen |
|----------|------------------------|------------------------|
| {decision 1} | {alternative} | {reason} |

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|--------|-------------|---------|-----------|
| {risk} | High/Medium/Low | High/Medium/Low | {how it is mitigated} |

## Edge cases (MANDATORY)

List the identified edge cases and how the design handles them. Cover at least: empty/null inputs, out-of-range values, concurrency/duplicates, external dependency failures (timeout, error, unavailability), inconsistent data, and size/quantity limits.

| Edge case | How it is handled | Responsible component |
|--------------|----------------|------------------------|
| {empty / null input} | {expected behavior} | {component} |
| {out-of-range / invalid value} | {validation + response} | {component} |
| {duplicate request / concurrency} | {idempotency / lock / dedup} | {component} |
| {external system timeout or error} | {retry / fallback / degradation} | {component} |
| {inconsistent data or unexpected state} | {detection + handling} | {component} |

## Test coverage plan (feeds /karvey-test)

Declare what is tested and at which level. Every requirement and every critical edge case must have at least one associated test at some level.

| What is tested | Level (unit / integration / E2E) | Component / layer | Case(s) covered |
|---------------|----------------------------------|-------------------|-------------------|
| {validation logic} | unit | Backend | {requirement / edge case} |
| {endpoint → DB flow} | integration | Backend + DB | {requirement} |
| {full user flow} | E2E | Frontend + Backend | {main use case} |
| {edge case handling} | unit / integration | {layer} | {edge case from the list above} |

> This table is the testing contract that `/karvey-test` consumes in the testing PHASE.
```

### Step 5 — Review gate

Verify before writing:
- [ ] Every requirement has at least one component that implements it
- [ ] The boundary is explicitly defined
- [ ] Each component has its Security Tier declared
- [ ] No components with vague responsibility ("helper", "utils" without a description)
- [ ] The file plan is concrete (real paths, not "create a file for X")
- [ ] The security controls cover the Tier declared in spec.json
- [ ] The Cloud Infrastructure section specifies which services from which cloud are used (and which part in which cloud if mixed)
- [ ] There is an observability strategy
- [ ] There is at least one mermaid diagram (data flow and/or components); for "Complex integration" / "New capability" both are present. Recommended to generate it with `/karvey-diagram`
- [ ] There is an Edge cases section covering at least: empty/null inputs, out of range, concurrency/duplicates, external system failures, and inconsistent data
- [ ] Trust boundaries are explicitly marked: where untrusted input enters and where each crossing is validated
- [ ] There is a Test coverage plan with a level (unit/integration/E2E) per item; every requirement and every critical edge case has at least one associated test

If there are issues: fix and re-verify. Maximum 2 iterations.

### Step 6 — Write architecture.md

```
docs/spec/changes/{change-id}/architecture.md
```

Update `spec.json`:
- `phase: "architecture-generated"`
- `approvals.architecture.generated: true`

### Step 6B — Update knowledge graph

Sync the knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`) to reflect the created `architecture.md`.
If `docs/spec/graphify-out/` does not exist, invoke `/graphify docs/spec/` without `--update`.

### Step 7 — Present for approval

If flag `-y`: auto-approve.
If not: present a summary and ask for approval.

On approval: `approvals.architecture.approved: true`, `phase: "architecture-approved"`.

```
✅ Architecture approved

Next step:
/karvey-infra {change-id}
```


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Infrastructure phase now?"
- If they confirm → run `/karvey-infra {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (the method's gate).
- If you resume in another session, `/karvey {change-id}` shows which phase you are in and which one is next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
