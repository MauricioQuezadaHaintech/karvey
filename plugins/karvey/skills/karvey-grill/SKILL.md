---
name: karvey-grill
description: Pre-spec interrogation. Interviews the engineer relentlessly about their problem before writing any spec. Use at the start of every new feature or initiative — before karvey-init. Triggers include "grill me", "entrevístame", "interview me", "quiero especificar algo", "I want to spec something", "tengo una idea", "I have an idea", "necesito una feature", "I need a feature", "spec-driven", "SDD", "kiro", "gstack", "Garry Tan", "office hours", "producto 10 estrellas", "10-star product", "reframe", "PRD", "método de desarrollo", "development method".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [descripción breve del problema o idea]
---

# Karvey Grill — Pre-Spec Interrogation

## Purpose

Before writing a single line of spec, this skill interviews you in depth until the problem is fully understood. One question at a time. With a recommendation included in each one.

## Execution instructions

### Step 0 — 10-star reframe (optional)

> **Optional mode.** This step comes BEFORE (or at the start of) the interrogation. Its goal is NOT to specify what was asked for, but to find the **best version of the product** hidden in the request. Inspired by `/office-hours` + `/plan-ceo-review`.
>
> **When to skip it:** if the user already has full clarity on the product they want, or explicitly asks to go straight to the interrogation, jump to Step 1. Offer it, don't impose it.

Before starting, ask:

```
Do you want to do the 10-star reframe first (find the best version of the product), or go straight to the interrogation?

*My recommendation:* {do it if the request is vague/ambitious/strategic; skip it if it's a well-defined, narrow change}
```

If the user accepts, walk through the **six forced questions**, **one question at a time, with a recommendation** (same rules as the interviewer). Each question reframes the product before specifying it:

1. **Challenge the premise.** Is the stated problem the real problem, or a symptom? What if the premise were wrong?
2. **10-star product.** If this were a perfect experience (10/10), what would it look like? What hidden version of the request would delight the user?
3. **Scope expansion (10x).** What would make it 10x better, not 10% better? What adjacent capability turns it from "useful" into "indispensable"?
4. **Selective expansion.** Of those big ideas, which ones are truly worth it and fit within this effort? (separate the viable "wow" from the fantasy "wow")
5. **Hold scope.** What do we deliberately leave for later (v2) even if it's tempting? Mark the conscious boundary.
6. **Reduction.** What's surplus in the original request? What can be removed without losing value, or that even improves the product by taking it out?

After closing the six, synthesize a **mini design-doc / vision** (see Step 4: "10-star vision" section). This document **feeds the PRD alongside the synthesis from the normal interrogation**: the reframe defines "what we should build" and the interrogation defines "how we build it".

> If the reframe was done, use its vision to focus and sharpen the questions in branches A–F (don't repeat what's already resolved).

### Step 1 — Initial context

If the user gave a description in `$ARGUMENTS`, use it as the starting point.
If not, ask the first open question: "What problem do you want to solve, and for whom?"

Before asking anything that could be answered by exploring the codebase, **explore first**:
- Search for whether similar functionality already exists (`grep`, `find`)
- Read existing configuration files or specs in `docs/spec/`
- If you find the answer, present it as context and move to the next question

### Step 2 — Interrogation tree

Systematically walk through these branches, **one question at a time**:

#### Branch A: The problem
1. Who has the problem? (person/system/role)
2. What is the current situation causing friction?
3. How frequently does it happen? What is the impact?
4. Did they try to solve it before? What failed?

#### Branch B: The scope
5. What is IN scope for this initiative?
6. What is explicitly OUT of scope?
7. What other systems or components are affected?
8. What new data is needed? What existing data is modified?

#### Branch C: Technical constraints
9. Which layer(s) does this operate on: DB / Backend / Frontend / Infra?
10. Are there external integrations involved?
11. What level of security does it require? (public data / authenticated / sensitive data / critical with audit trail)
12. Are there performance or SLA constraints?

#### Branch F: Technology stack
> Before asking, explore the codebase: `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `Gemfile`, `Cargo.toml`, DB config files, etc. Only ask what can't be inferred.

13. What is the backend language and framework? (Node/Express, Python/FastAPI, Go, Java/Spring, Ruby/Rails, etc.)
14. What database does it use and how does it access it? (PostgreSQL/ORM, MySQL/queries, MongoDB, Oracle/SPs, Redis, etc.)
15. Does the change have a UI? With what framework? (React, Vue, Angular, Svelte, server-rendered, not applicable, etc.)
16. What API protocol does it use? (REST, GraphQL, gRPC, messaging, WebSockets, etc.)
17. How are releases versioned? (package.json, pyproject.toml, VERSION file, git tags, none, etc.)
18. Are there established git conventions? (Conventional Commits, gitflow, trunk-based, squash, etc.)
19. Code/CI platform: GitHub or Azure DevOps? (where the repos live and the pipelines run)

    *My recommendation:* {detect from git remotes / pipeline files — `.github/workflows`, `azure-pipelines.yml` — and confirm where the pipelines run}
20. Cloud provider: Azure, GCP, AWS, mixed, or none? If mixed, which part on which cloud?

    *My recommendation:* {infer from the SDKs/CLIs and IaC files present; if mixed, ask for the breakdown of which component lives on which cloud}
21. IaC tool: Terraform, Bicep, Pulumi, or none (manual infra)?

    *My recommendation:* {look for `*.tf`, `*.bicep`, `Pulumi.yaml`; if there's none, assume manual infra and confirm it}

> **Note:** the knowledge-sync decision (Obsidian vs graphify) is NOT asked here — karvey-init resolves it based on the availability of the Obsidian MCP (see `karvey/rules/knowledge-sync.md`).

#### Branch D: Success criteria
22. How will we know this works correctly?
23. What are the critical error cases that must be handled?
24. What about the current behavior must NOT change?

#### Branch E: Dependencies and risks
25. What must be ready BEFORE starting this?
26. What blocks this work if it isn't resolved first?
27. What is the biggest risk of this initiative?

### Step 3 — Format of each question

```
**Question N/~27:** {clear and specific question}

*My recommendation:* {your suggested answer based on what you already know about the context}
```

Adapt the questions based on the previous answers. If a branch is already clear, skip it.
If an answer raises sub-questions, dig deeper before moving on.

### Step 4 — Final synthesis

When the tree is covered (or the user signals they're done), generate a summary:

> This summary is the **input to the PRD** (`prd.md`) that karvey-init will generate. Keep it complete and faithful: whatever is missing here will be missing in the PRD.

```markdown
## Pre-Spec Summary: {tentative name of the change}

### 10-star vision (if Step 0 was done)
> Mini design-doc from the reframe. Omit this section if Step 0 was skipped.
- **Reframed premise:** {the real problem vs. the stated symptom}
- **10-star product:** {what the perfect experience looks like}
- **Selected expansion:** {10x ideas that DO fit within this effort}
- **Held scope (v2):** {the big stuff deliberately left for later}
- **Reduction:** {what's removed from the original request and why}

### The problem
{who, current situation, impact}

### What changes
{what's in scope, what's out}

### Detected stack
- Backend: {language/framework}
- Database: {DB and access pattern}
- Frontend: {framework or "not applicable"}
- API: {protocol}
- Versioning: {mechanism}
- Git: {conventions}

### Platform & Deployment
- Git platform: {GitHub | Azure DevOps}
- Cloud provider(s): {Azure | GCP | AWS | mixed | none — if mixed, which part on which cloud}
- IaC tool: {Terraform | Bicep | Pulumi | none (manual infra)}

> Knowledge sync (Obsidian vs graphify): decided by karvey-init based on the availability of the Obsidian MCP (see `karvey/rules/knowledge-sync.md`).

### Key constraints
- Layers: {DB/Backend/Frontend/Infra}
- Security: {level — justification}
- External integrations: {list}
- Technical constraints: {list}

### Success criteria
{how it's verified that it works}

### Critical error cases
{list}

### Main risks
{list}

### Prerequisite dependencies
{what must exist beforehand}

### Suggested Change ID
`{add|fix|update|remove}-{descriptive-name}` — {rationale}
```

### Step 5 — Transition

When done, indicate:
```
✅ Interrogation complete. Next step:
/karvey-init {suggested-change-id}
```

## Interviewer rules

- **One question at a time**. Never ask two questions in the same message.
- **Always include a recommendation** in each question.
- **Explore the codebase** before asking something that can be discovered on your own.
- **Don't assume** technology, scale, or users without confirming.
- **Don't advance** to specification until the tree is covered.
- The tone is collaborative, not inquisitorial. The goal is to build shared understanding.


## Advance to the next phase

When you finish this phase and have the corresponding approval, **actively ask the user**: "Shall we advance to the Init phase (create the change) now?"
- If they confirm → run `/karvey-init {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (a gate of the method).
- If you resume in another session, `/karvey {change-id}` indicates which phase you're on and which one comes next.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`. Karvey = Afán, an ona/selknam word.*
