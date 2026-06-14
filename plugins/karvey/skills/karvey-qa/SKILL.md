---
name: karvey-qa
description: QA code review in 8 dimensions (Security with OWASP Top 10 + STRIDE, Errors, Consistency, Impact, Env vars, Versioning, Second opinion cross-model, Visual audit vs design-spec). Creates REVISION_PR document, ClickUp tasks or PLAN.md entries. Notifies Google Chat. Triggers include "karvey qa", "code review", "revisión de código", "QA".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
argument-hint: <change-id> [--source <branch>] [--target <branch>]
---

# Karvey QA

## Purpose

Code review across 8 dimensions, post-implementation. Generates a review document, creates subtasks in ClickUp or PLAN.md, and notifies the project's Google Chat group.

## Execution steps

### Step 0 — Identify branches and stack

Read `docs/spec/changes/{change-id}/spec.json`.

If the user did not specify branches, ask: "Which branches should be compared? (source → target)"
Default convention: `feature/{change-id}` → `dev`

Detect the repo stack (see `package.json`, `requirements.txt`, `pyproject.toml`).

Get the diff:
```bash
git diff {target}...{source} --stat
git diff {target}...{source}
git log {target}...{source} --oneline
```

### Step 1 — Analysis across 8 dimensions

Dispatch parallel subagents for dimensions 1–4, run 5–6 in the main context. Dimensions 7 (second opinion cross-model) and 8 (visual audit) run at the end, once the preliminary findings are consolidated:

**Dimension 1: Security**
- Hardcoded credentials (tokens, API keys, passwords)
- XSS: unsanitized `v-html`, `dangerouslySetInnerHTML`
- Auth only in the frontend with no backend enforcement
- Real personal data in code (RUTs, emails, phone numbers)
- Missing user-context validations in data operations or endpoints
- Unsanitized dynamic SQL
- Stack traces exposed to the client

**OWASP Top 10 coverage (explicitly review each category):**
- A01 Broken Access Control — IDOR, privilege escalation, missing tenant/user context validation
- A02 Cryptographic Failures — sensitive data in cleartext, weak algorithms, TLS not enforced
- A03 Injection — SQL/NoSQL/OS/LDAP injection, unparameterized dynamic queries
- A04 Insecure Design — missing rate limits, flows without business controls
- A05 Security Misconfiguration — insecure defaults, open CORS, missing security headers, debug enabled
- A06 Vulnerable & Outdated Components — dependencies with known CVEs
- A07 Identification & Authentication Failures — weak sessions, default credentials, MFA absent where it should be
- A08 Software & Data Integrity Failures — insecure deserialization, unverified pipelines/artifacts
- A09 Security Logging & Monitoring Failures — security events not logged, logs with sensitive data
- A10 Server-Side Request Forgery (SSRF) — fetch/requests with a user-controlled URL without validation

**STRIDE threat modeling (classify each finding and look for threats per category):**
- **S**poofing — impersonation of identity/origin
- **T**ampering — alteration of data in transit or at rest
- **R**epudiation — actions without traceability/audit
- **I**nformation Disclosure — leakage of sensitive data
- **D**enial of Service — resource exhaustion, lack of limits
- **E**levation of Privilege — privilege escalation

> **🚧 SECURITY GATE (blocking):** If any unresolved security finding of Critical or High severity exists, deployment is NOT enabled. The gate explicitly covers the **OWASP Top 10** categories and the **STRIDE** modeling described above: a critical/high finding in any of them blocks advancement. The change cannot advance to `/karvey-deploy` until it is resolved and QA is re-run.

**Dimension 2: Code errors**
- Null/undefined access without a guard
- Memory leaks (listeners, intervals, subscriptions without cleanup)
- Unhandled promises
- Function signatures changed without updating callers
- Race conditions in async

**Dimension 3: Consistency**
- Typos in naming
- Mixing of patterns within the same module
- Duplicated code (3+ repetitions that should be a helper)
- Direct Axios bypassing the apiService interceptors
- Tabs vs spaces

**Dimension 4: Impact on existing modules**
- Changes in shared files (router, root store, apiService, global components)
- Public interfaces modified without updating consumers
- Implicit behavior changes (timeouts, guards, interceptors)

**Dimension 5: Environment variables**
- Variables used in code but not declared in Dockerfile/pipeline
- Variables with no fallback in some environment
- Variables in `.env.example` but not used

**Dimension 6: Versioning**
- Project version file updated (`package.json`, `pyproject.toml`, `VERSION`, etc.)
- `CHANGELOG.md` with an entry for the current version
- Consistency between the version file and the CHANGELOG

Verify the CHANGELOG per the `karvey/rules/changelog-policy.md` rule, for each repo with changes:
- `CHANGELOG.md` has an entry for the current version
- The entry includes the **responsible human** (name + contact)
- The entry indicates the **AI model** used
- The entry explains the **why** of the change (not just the what)

If any of these fields is missing, it is a versioning finding and blocks advancement to deploy.

**Dimension 7: Second opinion cross-model (adversarial review)**

Before releasing, obtain an adversarial review with ANOTHER model, by invoking the cross-cutting skill `karvey-second-opinion` on the same diff (`{target}...{source}`).

- It is **complementary**, it does not replace QA's judgment: it serves to discover the main model's blind spots (biases, assumptions, edge cases not considered).
- Pass as context: the diff, the change-id's `spec.json`, and the preliminary findings of dimensions 1–6.
- Integrate the second model's new findings into the review document, marking them with their origin (model + skill).
- Severity rules: if the second model raises a critical/high finding that QA considers valid, the same blocking gate applies. Discrepancies between models are documented; the final decision is the human/main QA's.

**Dimension 8: Visual audit of the IMPLEMENTED product vs design-spec**

Audit the **already-built** UI in the target's actual runtime (not the mockup, not the isolated code), relying on `karvey-browse` to open the target and capture the actual state. It is **target-agnostic** (web, mobile, desktop, or other): what matters is comparing what the user actually sees against what was specified.

- Load the expected design from `docs/spec/changes/{change-id}/design-spec.md` (or the corresponding scope's `design-spec.md`).
- With `karvey-browse`, navigate the implemented flow in the target's actual runtime and capture evidence (screenshots/state) of each relevant screen/state.
- Compare implemented vs design-spec: layout, spacing, typography, colors/tokens, states (empty, loading, error, hover/focus), responsiveness, copy, and visual hierarchy.
- Record each deviation as a visual finding with severity and evidence.
- For visual fixes: apply **atomic commits** (one fix per commit) documenting **before/after** (capture before and after). Deviations that break accessibility or security inherit the blocking gate of their corresponding dimension.

### Step 2 — Generate review document

File name: `REVISION_PR_{number}_{YYYYMMDD}.md` at the repo root.

Structure:
```markdown
# Code Review — {change-id}: {source} → {target}

## General Information
- Repository: {name}
- Stack: {stack}
- Source branch: {source}
- Target branch: {target}
- Date: {YYYY-MM-DD}
- Commits included: {N}
- Files modified: {N}

## Executive Summary
{paragraph with the most important findings}

## Findings by Dimension

### 1. Security
{findings with: #N, file, line ~NNN, severity, description, problematic code, recommendation, instructions for the AI}

### 2. Code errors
...

### 3. Consistency
...

### 4. Impact on existing modules
...

### 5. Environment variables
{cross-reference table + discrepancies}

### 6. Versioning
{verification of the project version file and CHANGELOG or equivalent}

### 7. Second opinion cross-model
{model/skill used, second model's new findings marked with their origin, documented discrepancies}

### 8. Visual audit (implemented vs design-spec)
{deviations with severity, before/after evidence, reference to design-spec.md}

## Summary Table by Severity
| Severity | Count |
|-----------|---------|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |

## Pre-merge checklist
- [ ] All critical findings resolved
- [ ] All high findings resolved
- [ ] Security gate passed (OWASP Top 10 + STRIDE with no criticals/highs)
- [ ] Second opinion cross-model executed and integrated
- [ ] Visual audit vs design-spec with no blocking deviations
- [ ] Environment variables verified
- [ ] Tests pass
- [ ] Production build successful

## Areas requiring manual testing
- {area}: {reason}
```

### Step 3A — Create tasks in ClickUp (if management=clickup)

Get the active sprint: `clickup_get_list` with name "Sprint XX".

Create parent task:
```
clickup_create_task
  name: "QA Review {change-id} ({source} → {target})"
  list_id: "{sprint_list_id}"
  priority: "high"
  tags: ["{client_tag}"]
```

For each critical and high finding, create a subtask:
```
clickup_create_task
  name: "#{N} [{SEVERITY}] {file}: {short description}"
  parent: {parent_task_id}
  priority: {urgent|high|normal|low}
  assignees: [{author per the file's git log}]
  time_estimate: {5-60 min in ms}
  markdown_description: (see format in QA_CODE_REVIEW_STANDARD)
```

Fix estimation:
- Simple fix (null check, typo): 5-10min
- Medium fix (add validation, cleanup): 15-20min
- Complex fix (extract helper, move to env var): 30min
- Mass migration: 45-60min

### Step 3B — Update PLAN.md (if management=markdown)

Add a "QA Review" section at the end of PLAN.md with the list of findings and pending actions.

### Step 3C — Update knowledge graph

Sync knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`) to reflect the generated `REVISION_PR_{n}_{date}.md`.
If `docs/spec/graphify-out/` does not exist, invoke `/graphify docs/spec/` without `--update`.

### Step 3D — Update status in spec.json

Update `docs/spec/changes/{change-id}/spec.json` per the QA result:

- If there are NO critical or high findings (including the SECURITY GATE of Dimension 1 with OWASP Top 10 + STRIDE, the valid findings of the second opinion cross-model, and the blocking visual deviations) → set `approvals.qa.approved: true` and `phase: "qa"`.
- If there are blocking findings (critical/high, unresolved security gate, valid critical/high finding from the second model, or a visual deviation that breaks accessibility/security) → set `approvals.qa.approved: false`.

### Step 4 — Notify via Google Chat

Identify the project's space in the known-spaces table.
Send a summary to the group using the Google Chat protocol from CLAUDE.md.

Message format (Google Chat):
```
*QA Review — {change-id}*

*{source}* → *{target}*

*Findings:*
- 🔴 Critical: {N}
- 🟠 High: {N}
- 🟡 Medium: {N}
- ⚪ Low: {N}

*Manual testing areas:*
- {area 1}
- {area 2}

Full document: `REVISION_PR_{n}_{date}.md`
```

### Step 5 — Final output

```
✅ QA Review complete

Findings: {N} total ({critical}, {high}, {medium}, {low})
Document: REVISION_PR_{n}_{date}.md

Management: {N subtasks created in ClickUp | PLAN.md updated}
Google Chat: notification sent to {group}

Next step (if there are critical/high findings):
  Fix → re-run /karvey-impl {change-id} → /karvey-test {change-id} → /karvey-qa {change-id}

Next step (if no blocking findings):
  /karvey-deploy {change-id}
```


## Advance to the next phase

When finishing this phase and having the corresponding approval, **actively ask the user**: "Shall we advance to the Deploy phase now?"
- If they confirm → run `/karvey-deploy {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (the method's gate).
- If you resume in another session, `/karvey {change-id}` indicates which phase you are in and which one follows.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
