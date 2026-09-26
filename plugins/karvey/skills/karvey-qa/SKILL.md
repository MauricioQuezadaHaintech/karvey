---
name: karvey-qa
description: Karvey phase 10 — 9-dimension review with a blocking security gate, written to changes/{id}/qa/; observes only, defects go to findings.md — after test. Triggers include "karvey qa", "revisión karvey", "karvey review", "revisar cambio karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion
argument-hint: <change-id> [--source <branch>] [--target <branch>]
---

# Karvey QA

## Purpose

Code review across 9 dimensions, post-implementation. **QA observes; it never changes the code under review and never commits a fix.** Every defect becomes a finding in the change's `findings.md`, fixed later through `/karvey-iterate` → impl → test → qa. QA writes the review document, creates items in the team's tracker (`../karvey/rules/management-adapters.md`) or PLAN.md, and notifies the team's configured channel (`../karvey/rules/notifications.md`).

## Execution steps

### Step 0 — Identify branches and stack

Enter the phase: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" advance "{change-id}" qa` (refused while an earlier gate is open).

If the user did not specify branches, ask: "Which branches should be compared? (source → target)". Default: `feature/{change-id}` → the integration branch.

Detect the repo stack (see `package.json`, `requirements.txt`, `pyproject.toml`).

Get the diff:
```bash
TARGET="$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" get branch_flow.integration --shell)"
SOURCE="feature/{change-id}"
git diff "$TARGET...$SOURCE" --stat
git diff "$TARGET...$SOURCE"
git log "$TARGET...$SOURCE" --oneline
```

### Step 0B — Lane check (QA and QA-lite)

The lane check measures the diff against the change's lane (`../karvey/rules/lanes.md`) before the review:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" lane-check "{change-id}" --base "$TARGET" --head "$SOURCE" --finding "{F-NN}"
```

Every exceeded criterion (`lane exceeded: 5 > 3 code files`, a schema or contract file in a `patch`) becomes one
`findings.md` row (type `spec-gap`, origin `qa`, phase `qa`) with the proposal `lane raise {lane}`, and the tool
records one `lane.diff` hit in `docs/spec/changes/{change-id}/checks.jsonl`. In 3.13 the check warns
(`check-modes.json`); the prod gate shows its result. A `patch` or `hotfix` change also shows its `lane_evidence`
(BUG-NN, finding, regression test): a missing regression test is reported as `patch without regression test`, and
the incident cannot reach `RESUELTO`. QA-lite (the `patch`, `hotfix` and `docs` lanes) runs this step, Dimension
1 (security) and Dimension 6 (versioning) only.

### Step 0C — Tests: run them or cite the exact run; coverage

QA never writes "tests pass" or "the build passes" from memory (REQ-W2-063). For the **exact commit reviewed**
(`git rev-parse "$SOURCE"`), either **run** the suite through the evidence wrapper and cite the line it prints —
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-evidence.py" --change "{change-id}" --label qa-suite -- {the test
command}` → `evidence.jsonl:{line}` — or **cite the CI run of that commit** (its URL and status). With neither,
the checklist line reads **`Tests: not evaluated`**, never "pass"; the fiscal flags any claim without one of them.
Then the coverage gate (REQ-W2-062), read from the script and quoted, not recomputed:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-trace.py" "{change-id}" --check
```
`coverage: N/N` goes into the review; each requirement without a green test or a `manual` exception is listed and
the gate summary shows the warning (warn in 3.13, `coverage.requirements`). Plan and evidence of the test phase are
read from `docs/spec/changes/{change-id}/` (`test_plan.md`, `test_evidence.md`, `traceability.md`).

### Step 1 — Analysis across 9 dimensions

Dispatch parallel subagents for dimensions 1–4, run 5–6 and 9 in the main context. Dimensions 7 (second opinion cross-model) and 8 (visual audit) run at the end, once the preliminary findings are consolidated:

**Dimension 1: Security**

*Tools first (deterministic, REQ-W2-064..067).* Before reading the code, run the fixed catalogue of security tools
and cite each category's line as the tool printed it — never a verdict of your own for a category:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-security-scan.py" run "{change-id}" --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-security-scan.py" validate-suppressions "{change-id}" --json
```
- Per category (secrets, sast, sca, iac) cite: tool, version, command, findings by severity and the
  `evidence.jsonl:{line}` it recorded. `not evaluated (no tool)` and `not evaluated (tool error)` are written
  as such in the review and counted on the dashboard — **never** turned into "pass" by reading the code;
  `not applicable` (no file of that kind) is stated as such.
- Tool findings are triaged: a real one is a QA finding with its severity; a false positive is recorded in
  `changes/{change-id}/qa/suppressions.json` as `{tool, rule, path, reason, scope}` — `validate-suppressions`
  reports an entry without a reason or a scope, and QA is not approved with one.
- Then review **what the tools cannot see**, and say so in the review: authorisation per object (IDOR), tenant
  and user isolation, and business-logic abuse. The checklists below cover them.

*Model review (what the tools miss):*
- Hardcoded credentials (tokens, API keys, passwords)
- XSS: raw HTML injection of unsanitized input
- Auth only in the frontend with no backend enforcement
- Real personal data in code (national ids, emails, phone numbers)
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
- Bypassing the project's shared clients or wrappers (the team's standards name them; Dimension 9 cites the rule)
- Tabs vs spaces

**Dimension 4: Impact on existing modules**
- Changes in shared files (router, root store, shared clients, global components)
- Public interfaces modified without updating consumers
- Implicit behavior changes (timeouts, guards, interceptors)

**Dimension 5: Environment variables**
- Variables used in code but not declared in Dockerfile/pipeline
- Variables with no fallback in some environment
- Variables in `.env.example` but not used

**Dimension 6: Versioning** (`../karvey/rules/versioning.md`, `../karvey/rules/changelog-policy.md`), for each repo with changes:
- `unreleased-section`: `CHANGELOG.md` has a `## [Unreleased]` section with one line per commit of the change.
- `one-bump-per-release`: the diff does not bump the version; the bump happens once, at the release step of `/karvey-deploy`.
- `versions-agree`: the version files that exist (`package.json`, `pyproject.toml`, `VERSION`, manifests) agree with each other and with the top released CHANGELOG entry.
- `changelog-why`: each line names the **responsible human**, the **AI model** and the **why**, not just the what.

A missing item is a versioning finding and blocks deploy.

**Dimension 7: Second opinion cross-model (adversarial review)**

Before releasing, obtain an adversarial review with ANOTHER model, by invoking the cross-cutting skill `karvey-second-opinion` on the same diff (`{target}...{source}`).

- It is **complementary**, it does not replace QA's judgment: it serves to discover the main model's blind spots (biases, assumptions, edge cases not considered).
- Pass as context: the diff, the change-id's `spec.json`, and the preliminary findings of dimensions 1–6 and 9.
- Integrate the second model's new findings into the review document, marking them with their origin (model + skill).
- Severity rules: if the second model raises a critical/high finding that QA considers valid, the same blocking gate applies. Discrepancies between models are documented; the final decision is the human/main QA's.

**Dimension 8: Visual audit of the IMPLEMENTED product vs design-spec**

Audit the **already-built** UI in the target's actual runtime (not the mockup, not the isolated code), relying on `karvey-browse` to open the target and capture the actual state. It is **target-agnostic** (web, mobile, desktop, or other): what matters is comparing what the user actually sees against what was specified.

- Load the expected design from `docs/spec/changes/{change-id}/design-spec.md` (or the corresponding scope's `design-spec.md`).
- With `karvey-browse`, navigate the implemented flow in the target's actual runtime and capture evidence (screenshots/state) of each relevant screen/state.
- Compare implemented vs design-spec: layout, spacing, typography, colors/tokens, states (empty, loading, error, hover/focus), responsiveness, copy, and visual hierarchy.
- Record each deviation as a visual finding with severity and evidence.
- Each deviation is a finding with its before evidence and the expected after (from design-spec); the fix is not QA's. Deviations that break accessibility or security inherit the blocking gate of their corresponding dimension.

**Dimension 9: Standards conformance (golden path)**

`karvey-impl` loads the engineering standards as a hard constraint and requires a Deviation Request before departing from them (`../karvey/rules/engineering-standards.md`). This dimension **verifies that it actually happened**. Without it the method only trusts: an implementation that skipped the golden path without raising the Deviation Request reaches production with nothing having checked.

Do not confuse it with Dimension 3: **Consistency** measures coherence *internal* to the module (patterns, naming, duplication); **conformance** measures agreement with the *documented standard*. A module can be impeccably consistent with itself and be entirely outside the golden path.

- Resolve `project.json:standards` (or `docs/spec/standards/_index.md`) and load the `standards/{layer}.md` **only for the layers the diff touches**.
- Compare the diff against each standard's `MUST` / `MUST NOT`, citing the standard and the concrete rule breached (e.g. `db.md § SP contract`). A finding with no citation is not a conformance finding.
- **Approved deviation is not a finding:** if `docs/spec/changes/{change-id}/deviations.md` holds an approved entry covering the case, it conforms. Say so in the review — it is evidence the gate worked.
- **Unregistered deviation → High.** It is the failure this dimension exists to catch: the code departed from the standard and nobody decided it.
- **Gray zone → Medium, tagged `gray-zone`,** and escalate to design mode. Never Critical by the reviewer's own reading of a standard that does not cover the case.
- **A standard in `draft` does not by itself produce Critical/High findings** — only an explicit `MUST` violation does. Blocking on a rule still being drafted burns the team's trust in the gate.
- If there are no standards for the project, record the dimension as **not evaluated**. Not evaluated is not the same as conformant.

### Step 2 — Generate review document

Write `docs/spec/changes/{change-id}/qa/REVISION_PR_{number}_{YYYYMMDD}.md` — inside the change, never at the repo root. `/karvey-deploy` reads it from there.

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

### 9. Standards conformance (golden path)
{per layer touched: standard + rule breached, or "conforms"; approved deviations cited from deviations.md; gray zones escalated. If there are no standards: "not evaluated"}

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
- [ ] Standards conformance verified for every layer the diff touches (or recorded as not evaluated)
- [ ] Environment variables verified
- [ ] Tests: {pass — evidence.jsonl:{line} | pass — CI run {url} of {sha} | not evaluated}
- [ ] Coverage: {N}/{N} (karvey-trace.py --check){; not green: REQ-…}
- [ ] Production build: {pass — evidence.jsonl:{line} or CI run {url} | not evaluated}

## Areas requiring manual testing
- {area}: {reason}
```

### Step 3A — Create tasks in the team's tracker (`management-adapters.md`)

Find or create the QA item **`E{n}.QA`** under the change's Epic — `QA Review {change-id} ({source} → {target})`, priority high; never at the root of the list (`../karvey/rules/management-adapters.md` → *One work breakdown*) — and one child per critical/high
finding (`create_task`, state `todo`, estimate per the table below, assignee = the file's author per git log), in
the tool `karvey-config.py resolve management` returns (only when `external: true`) — in the active sprint/iteration if the team uses one. `link(parent, REVISION_PR)`. Tool-specific calls live in the adapter (`../karvey/rules/clickup-protocol.md` for ClickUp).

Fix estimation:
- Simple fix (null check, typo): 5-10min
- Medium fix (add validation, cleanup): 15-20min
- Complex fix (extract helper, move to env var): 30min
- Mass migration: 45-60min

### Step 3B — Update PLAN.md (Markdown)

Add a "QA Review" section at the end of PLAN.md with the list of findings and pending actions.

### Step 3C — Record the result through the state tool

- **Blocking findings** (critical/high, the security gate of Dimension 1, a valid critical/high from the second model, a visual deviation that breaks accessibility/security, or a standards departure with no approved entry in `deviations.md`) → QA is not approved; route the findings (Step 3D).
- **The fiscal before the approval.** After writing `REVISION_PR_*.md` and before asking for the QA approval (or the *release* gate), run `/karvey-judges {change-id} qa --base {integration branch}`. The `fiscal` lens always runs: it lists every claim of the review without evidence (an `evidence.jsonl` line, a CI run of the reviewed commit, or a `file:line`). Its findings are in `findings.md` like any other and go into the summary the human sees.
- **None** → `karvey-state.py generated "{change-id}" qa`, then ask the human for the QA approval. On their OK:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" approve "{change-id}" qa --by "{human}" --role human --ref "{D-NN or PR URL}"
  ```
  and set to `done` every Task and Feature of the change that is in `review` (`set_status`, or `👀` → `✅` in `PLAN.md`).

### Step 3D — Classify findings & route the iteration loop

QA findings are not all the same kind. Append each to `docs/spec/changes/{change-id}/findings.md` classified by type (see `../karvey/rules/iteration-loop.md`), because each goes to a different edge:
- `bug` — code defect against a correct spec (most security/error/consistency findings). → incident tracker `BUG-NN` (`incident-tracking.md`) + the QA micro-loop `impl→test→qa`.
- `spec-gap` — QA revealed the **spec was wrong/incomplete** (e.g. an impact finding that shows a requirement contradicts existing behavior, or a visual deviation because `design-spec` never specified that state). → re-open `requirements`.
- `emergent` — a valid improvement that is **out of this change's scope**. → discovery backlog.

Then **route them** with `/karvey-iterate {change-id}` (the engine confirms types and dispatches). Do not hand-route here — QA only observes and classifies; `karvey-iterate` is the single router.

**Convergence:** the change may advance to deploy only when there are no open `bug`/`spec-gap` findings (and the security gate passes) and all `emergent` are captured. Otherwise the next step is `/karvey-iterate`, not `/karvey-deploy`.

### Step 3E — Phase-close

Run the phase-close ritual (`../karvey/rules/phase-close.md`): status in the team's tracker (or `PLAN.md`), findings, incidents and backlog recorded. Nothing in `spec.json` is edited by hand.

### Step 4 — Notify the team (per `notifications.md`)

Resolve the destination with `karvey-config.py resolve notifications`; never look it up in `CLAUDE.md` or any other file.
- `channel` unset → skip and say `Notification: not configured — run /karvey:karvey-init --settings`.
- `channel: none`, or `qa` not in `events` → skip and say so.
- Otherwise run `karvey-config.py notify-check` first: exit 10 means the destination changed since the last confirmed send — show it and ask the human to type the phrase it prints (`confirmo notificacion <code>`); only then does `notify-check --confirm` record it (D-16). Then send through `via`. A failed send is reported, not swallowed; the phase still closes.
- Send only when `karvey-config.py notify-sent {change-id} --event qa --item qa --state {verdict} --run-id {run}` says `new` (the first run and a verdict change; every run with `notifications.qa_every_run`), then re-run it with `--record`; the message carries the run id and the time.

Content (event `qa`): change-id, source → target, **counts** by severity and the review path (`detail: counts`, the default); finding titles and manual-testing areas only with `detail: full`.
Write it in the **channel's own markup** (`notifications.md` → Message format per channel). Google Chat / Slack example:
```
*QA Review — {change-id}*

*{source}* → *{target}*

*Findings:*
- 🔴 Critical: {N}
- 🟠 High: {N}
- 🟡 Medium: {N}
- ⚪ Low: {N}

Full document: `docs/spec/changes/{change-id}/qa/REVISION_PR_{n}_{date}.md`
```

### Step 5 — Final output

```
✅ QA Review complete

Findings: {N} total ({critical}, {high}, {medium}, {low})
Document: docs/spec/changes/{change-id}/qa/REVISION_PR_{n}_{date}.md

Management: {N subtasks created in {tool} | PLAN.md updated}
Notification: {channel → target | skipped (none) | not configured}

Findings recorded: {N bug · N spec-gap · N emergent} → findings.md

Next step (if there are open findings):
  Route them: /karvey-iterate {change-id}
    → bug:      fix via /karvey-impl → /karvey-test → /karvey-qa
    → spec-gap: re-opens requirements (ripple only affected phases)
    → emergent: captured in the backlog

Next step (if converged — no open bug/spec-gap, security gate passed):
  /karvey-deploy {change-id}
```


## Advance to the next phase

Close the phase per `../karvey/rules/gates.md` (phase `qa`, gate *release*): `generated`, then `karvey-state.py gate {change-id} qa` says whether this phase asks the one gate question now (granular, or the last phase of the merged gate) or records `generated` and continues. The answer is recorded with `approve`/`approve-gate` or `outcome … changes_requested`; *Approve and advance* runs the skill `next` names with no second question. First check convergence: with open `bug`/`spec-gap` items in `findings.md` (or the security gate unresolved), the next step is `/karvey-iterate {change-id}`, not the gate. The fiscal runs before the gate question (Step 3C). In a new session, `karvey-state.py next {change-id}` says where the change is.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `../karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
