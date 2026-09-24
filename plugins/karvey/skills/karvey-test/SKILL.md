---
name: karvey-test
description: Karvey phase 9 — runs unit, E2E and regression tests in the target's real runtime and records test_plan.md and test_evidence.md — after impl. Triggers include "karvey test", "karvey pruebas", "ejecutar tests karvey", "karvey evidence".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion
argument-hint: <change-id> [--e2e-only] [--unit-only]
---

# Karvey Test

## Purpose

Run the full post-implementation test plan: unit tests per layer and E2E tests of the complete flow. **The contract is §6 (test coverage plan) of `architecture.md`**: every case it lists is run or reported as not run, with the reason. Document evidence in `docs/test_evidence.md`.

## Execution steps

### Step 1 — Load context

Enter the phase: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" advance "{change-id}" test` (refused while an earlier gate is open; on a resumed run `next` shows it is already in `test`).

Read:
- `docs/spec/changes/{change-id}/architecture.md` — §6 is the test contract
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/mockup/` if the change has one (to map E2E flows)
- `docs/spec/changes/{change-id}/tasks.md`

Also read `docs/spec/project.json` and obtain the `targets` field (see `../karvey/rules/targets.md`). The actual runtime in which the E2E tests run depends on the declared target: browser (web), simulator/device (iOS/Android), terminal (CLI), HTTP client (API), hardware/emulator (embedded). **Do not assume "web" by default** — a project may have multiple targets.

Detect stack: `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `Gemfile`, `Cargo.toml`, or other project configuration files. Identify:
- Backend language and framework
- Database type and access pattern (ORM, SPs, direct queries)
- Available unit test framework
- Available E2E framework
- API protocol (REST, GraphQL, gRPC, etc.)
- Declared targets and their corresponding actual runtime

### Step 2 — Generate or update test_plan.md

If `docs/test_plan.md` does not exist, create it. If it exists, add a section for this change-id.

**Test plan structure:**

```markdown
# Test Plan: {change-id}

## Scope
Requirements covered: {list}
Layers: {DB / Backend / Frontend}

## Unit Tests

### DB
| ID | SP / Function | Case | Input | Expected |
|----|-------------|------|-------|----------|
| UT-BD-01 | `{schema}.{sp_name}` | Happy path | `@{contextKey}={value}, @param=X` | Returns {Y} |
| UT-BD-02 | `{schema}.{sp_name}` | Invalid context | `@{contextKey}={invalid_value}` | Controlled error |
| UT-BD-03 | `{schema}.{sp_name}` | Empty input | `@param=NULL` | Controlled error |

### Backend
| ID | Endpoint / Operation | Case | Input | Expected |
|----|---------|------|---------|----------|
| UT-BE-01 | {operation} | Happy path | `{valid input}` | {expected response} |
| UT-BE-02 | {operation} | No auth | No credential | Authentication error |
| UT-BE-03 | {operation} | Wrong context | `{another user's input}` | Authorization error |
| UT-BE-04 | {operation} | Invalid input | `{incomplete input}` | Validation error |

### Frontend
| ID | Component | Case | Action | Expected |
|----|-----------|------|--------|----------|
| UT-FE-01 | {Component} | Initial render | Mount | Shows skeleton |
| UT-FE-02 | {Component} | Data loaded | API returns data | Shows {N} items |
| UT-FE-03 | {Component} | API error | API returns 500 | Shows error message |
| UT-FE-04 | {Component} | No data | API returns [] | Shows empty state |

## E2E Tests

Flows derived from the 3 levels of the mockup:

### Flow 1: {Main flow name — Level 1→2→3}
| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to {section} | {Level 2} view loads |
| 2 | Click on {element} | {Level 3 Modal/Panel} opens |
| 3 | Fill in form with {valid data} | {expected result} |
| 4 | Confirm action | {final state} |

### Flow 2: {Error flow name}
...

### Flow 3: {Permissions / security flow}
...
```

### Step 3 — Run unit tests

#### DB
For each SP / function, run it directly in the dev DB using the stack's syntax:
```sql
-- UT-BD-01: Happy path (adapt syntax to the DB: EXEC, CALL, SELECT, etc.)
{DB_CALL} {schema}.{sp_name} @{contextKey}={value}, @param='test_value'
-- Verify expected result
```

Record the result in `docs/test_evidence.md`.

#### Backend
Use `curl`, the project's test runner, or the appropriate client per protocol:
```bash
# REST (adapt method, URL and port to the stack)
curl -s -X POST "http://localhost:{port}/{endpoint}" \
  -H "Authorization: {auth_mechanism}" \
  -H "Content-Type: application/json" \
  -d '{test_input}'

# GraphQL
curl -s -X POST "http://localhost:{port}/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{operation(args) { fields }}"}'

# gRPC / others: use the project's native client
```

Run with the detected test runner:
- Python: `pytest`, `unittest`
- Node/JS: `jest`, `vitest`, `mocha`, `npm run test`
- Go: `go test ./...`
- Java: `mvn test`, `gradle test`
- Ruby: `rspec`, `rails test`
- Rust: `cargo test`
- Other: use whatever test command exists in the project (`Makefile`, `package.json scripts`, etc.)

If there is no configured test runner: manual verification documented as evidence.

#### Frontend
Run with the detected frontend test runner:
- `npm run test`, `npx vitest run`, `jest`, `ng test`, etc.
If there is no frontend test runner: manual verification documented as evidence.

### Step 4 — Run E2E tests in the target's actual runtime

E2E tests run **in the target's actual runtime** declared in `docs/spec/project.json:targets` (see `../karvey/rules/targets.md`), never against a stub or assuming "web":
- **web** → browser (headless or real). Framework: Playwright (`npx playwright test`), Cypress (`npx cypress run`), Selenium.
- **iOS / Android** → simulator or physical device (via tunnel). Native framework or mobile E2E (XCUITest, Espresso, Detox, Maestro).
- **CLI** → terminal: run the actual binary/command and verify the stdout/stderr transcript and exit code.
- **API / backend** → actual HTTP client (`curl`, protocol client) against the endpoint deployed in dev.
- **embedded** → the project's hardware or emulator.

To "get eyes" on the actual runtime (capture screen, navigate, interact), rely on the cross-cutting skill **`karvey-browse`**, which operates on the target's runtime (web browser, mobile simulator/device via tunnel, CLI process/terminal). It does not assume a browser.

Detect the E2E framework available in the project per target:
- **Playwright**: `npx playwright test`
- **Cypress**: `npx cypress run`
- **Selenium**: run the configured suite
- **native / mobile framework** (Go, Java, XCUITest, Espresso, Detox, Maestro, etc.): use the project's integration command
- **No E2E framework**: manually run each flow in the target's actual runtime in dev

For each E2E flow step, regardless of method, document:
- URL or screen visited
- Action performed
- Observed response/behavior
- PASS / FAIL

### Step 4-bis — Infrastructure tests (IAM bindings and ops steps)

If the change has `[human]` or `[Infra]` tasks that grant permissions, or is an `ops` change (`../karvey/rules/multi-agent.md` §5–6), run the **read-only verification scripts** that `karvey-infra` produced (e.g. `infra/iam/{change-id}.verify.sh`) as infrastructure tests:
- Assert the **binding itself** (member · role · resource), not only its effect — an end-to-end success can hide an over-granted role.
- Also assert that no broader role was granted to the same member than the one declared (least privilege).
- Record each check in `docs/test_evidence.md` (Infrastructure section) with the command, output and PASS/FAIL. A FAIL is a `bug` finding; if the human step was not executed yet, the task stays `awaiting-human` and the test is reported as **pending**, not FAIL.
- Where the CI has read-only credentials, add the verification to CI so drift (someone removing or widening the binding) is detected later.

### Step 4B — Performance benchmark (baseline)

Measure performance metrics **in the target's actual runtime**, to have a comparable baseline across runs (detect performance regressions, not just functional ones). The metrics depend on the target:
- **web** → Core Web Vitals (LCP, CLS, INP/FID), TTFB, load time.
- **iOS / Android** → startup time (cold/warm start), interaction response time, memory usage.
- **CLI** → command execution time, process startup time.
- **API / backend** → response latency (p50/p95/p99), throughput.

This measurement can be delegated to or related with the **`karvey-health`** skill (runtime health/performance check). Record the measured values in `docs/test_evidence.md` (Benchmark section) to compare against previous runs: if a key metric degrades relative to the previous baseline, flag it as a finding.

### Step 4C — Automatic regression tests + incident logging

**Every time a test detects a bug**, log it in the incident tracker `docs/bugs_dev_testing.md` as a `BUG-NN` (continue the incremental counter — read the file first), opening its **State history** at `DETECTADO` (see `../karvey/rules/incident-tracking.md`), and mirror it to `docs/spec/incidents-index.md`. The same bug is also recorded as a `bug`-type finding in `findings.md` (Step 5B).

**When it is fixed**, generate an automatic regression test that covers exactly that case, so it fails again if the bug reappears, and move the incident to `RESUELTO` (a regression test is required to reach `RESUELTO`). That is: for every fixed FAIL, a new test must remain in the suite.

- Write the test in the framework of the layer where the bug was (unit or E2E) using the runner detected in Step 1.
- Name it traceably to the bug (e.g., `regression_{change-id}_{short-description}`).
- The test must reproduce the input/scenario that caused the failure and assert the correct behavior.
- Verify that the test passes against the fixed code (and, ideally, that it fails against the previous code).
- Record the generated regression test in `docs/test_evidence.md` (Regression section), referencing the ID of the original failed test.

### Step 5 — Document evidence

Write or update `docs/test_evidence.md`:

````markdown
# Test Evidence: {change-id}

**Date:** {YYYY-MM-DD HH:MM}
**Environment:** dev / local
**Stack:** {detected stack}
**Targets:** {targets from project.json}
**E2E Runtime:** {actual runtime used per target — browser / simulator / terminal / HTTP client / ...}

## Unit Tests — DB

### UT-BD-01: {SP name} — Happy path
**Result: ✅ PASS**

Request:
```sql
{DB_CALL} {schema}.{sp_name} @{contextKey}={value}, @param='value'
```

Response:
```
{actual result — format per the project's protocol (JSON, XML, binary, etc.)}
```

Notes: {if applicable}

---

### UT-BD-02: Invalid context
**Result: ✅ PASS**
...

## Unit Tests — Backend

### UT-BE-01: POST /endpoint — Happy path
**Result: ✅ PASS**

Request:
```
POST http://localhost:{port}/api/{endpoint}
Authorization: Bearer ***
Content-Type: application/json

{body}
```

Response:
```
HTTP/1.1 200 OK

{response body}
```

---

## E2E Tests

### Flow 1: {Name}
**Result: ✅ PASS**

| Step | Action | Result | Status |
|------|--------|-----------|--------|
| 1 | {action} | {result} | ✅ |
| 2 | {action} | {result} | ✅ |

Actual runtime used: {browser / simulator / terminal / HTTP client / ...}

---

## Performance benchmark (baseline)

**Measured runtime:** {target / actual runtime}

| Metric | Current run | Previous baseline | Delta | Status |
|---------|----------------|-----------------|-------|--------|
| {LCP / cold start / p95 latency / CLI time} | {value} | {value or —} | {±} | ✅ / ⚠️ regression |

Notes: {detected degradations relative to the baseline, if applicable}

---

## Generated regression tests

| Regression test ID | Covers bug (original test ID) | Layer | File | Status |
|-------------------|------------------------------|------|---------|--------|
| `regression_{change-id}_{desc}` | {UT-XX-NN / E2E Flow N} | {DB/Backend/Frontend/E2E} | {path} | ✅ PASS |

---

## Summary

| Category | Total | PASS | FAIL |
|-----------|-------|------|------|
| DB | {N} | {N} | {N} |
| Backend | {N} | {N} | {N} |
| Frontend | {N} | {N} | {N} |
| E2E | {N} | {N} | {N} |
| Regression | {N} | {N} | {N} |
| **Total** | **{N}** | **{N}** | **{N}** |
````

### Step 5B — Classify findings (feed the iteration loop)

Append every observation from this run to `docs/spec/changes/{change-id}/findings.md`, classified by type (see `../karvey/rules/iteration-loop.md`):
- `bug` — a FAIL where the code doesn't do what the (correct) spec says → already logged as `BUG-NN` in Step 4C.
- `spec-gap` — while testing you realized the **spec itself** is wrong/incomplete (e.g. the requirement never defined this case). Don't silently "fix" it in code — record it so it can re-open requirements.
- `emergent` — a valid new idea/scope that surfaced but is **out of this change's scope**.

You only **classify and append** here; routing is `karvey-iterate`'s job. If `findings.md` ends with any open `bug`/`spec-gap`, the next step is `/karvey-iterate {change-id}`, not `/karvey-qa`.

### Step 5C — Phase-close

Run the phase-close ritual (`../karvey/rules/phase-close.md`): status in the team's tracker (`../karvey/rules/management-adapters.md`) or `PLAN.md`, findings and incidents recorded. The state was advanced in Step 1; nothing in `spec.json` is edited by hand.

### Step 6 — Report to the user

If all tests PASS:
```
✅ Testing complete

Results:
  DB: {N}/{N} PASS
  Backend: {N}/{N} PASS
  Frontend: {N}/{N} PASS
  E2E: {N}/{N} PASS

Evidence: docs/test_evidence.md

Next step:
/karvey-qa {change-id}
```

If there are FAILs:
```
⚠️ {N} tests failed

FAILs:
  - {ID}: {failure description}
  - {ID}: {failure description}

Logged as incidents: BUG-{list} (docs/bugs_dev_testing.md)
Findings recorded: {N bug · N spec-gap · N emergent} → findings.md

For every fixed FAIL, generate its regression test (Step 4C) and leave it in the suite.

Next step:
  - Route the findings (recommended): /karvey-iterate {change-id}
  - Or fix bugs and re-run directly: /karvey-test {change-id}
```

> If any finding is a `spec-gap` (the spec, not the code, was wrong), do **not** just patch code — `/karvey-iterate` will re-open requirements so the spec is corrected and the fix is traceable.


## Advance to the next phase

When finishing this phase, first check convergence: if `findings.md` has open `bug`/`spec-gap` items, the next step is `/karvey-iterate {change-id}` (route them), not QA. Once routed or clear, **ask the user**: "Shall we advance to the QA phase now?" On their OK, run `/karvey-qa {change-id}`; otherwise wait. In a new session, `karvey-state.py next "{change-id}"` says where the change is.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `../karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
