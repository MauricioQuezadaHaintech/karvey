---
name: karvey-test
description: Execute unit tests and E2E tests after implementation. Generates test_plan.md and test_evidence.md with request/response/PASS/FAIL evidence. Triggers include "karvey test", "ejecutar tests", "run tests", "pruebas", "tests", "testing", "evidencias", "evidence".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
argument-hint: <change-id> [--e2e-only] [--unit-only]
---

# Karvey Test

## Purpose

Run the full post-implementation test plan: unit tests per layer and E2E tests of the complete flow. Document evidence in `docs/test_evidence.md`.

## Execution steps

### Step 1 — Load context

Read:
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/architecture.md`
- `docs/spec/changes/{change-id}/mockup.html` (to map E2E flows)
- `docs/spec/changes/{change-id}/tasks.md`

Also read `docs/spec/project.json` and obtain the `targets` field (see `karvey/rules/targets.md`). The actual runtime in which the E2E tests run depends on the declared target: browser (web), simulator/device (iOS/Android), terminal (CLI), HTTP client (API), hardware/emulator (embedded). **Do not assume "web" by default** — a project may have multiple targets.

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

E2E tests run **in the target's actual runtime** declared in `docs/spec/project.json:targets` (see `karvey/rules/targets.md`), never against a stub or assuming "web":
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

For each E2E flow step document:
- URL visited
- Action performed
- Observed response/behavior
- PASS / FAIL

### Step 4B — Performance benchmark (baseline)

Measure performance metrics **in the target's actual runtime**, to have a comparable baseline across runs (detect performance regressions, not just functional ones). The metrics depend on the target:
- **web** → Core Web Vitals (LCP, CLS, INP/FID), TTFB, load time.
- **iOS / Android** → startup time (cold/warm start), interaction response time, memory usage.
- **CLI** → command execution time, process startup time.
- **API / backend** → response latency (p50/p95/p99), throughput.

This measurement can be delegated to or related with the **`karvey-health`** skill (runtime health/performance check). Record the measured values in `docs/test_evidence.md` (Benchmark section) to compare against previous runs: if a key metric degrades relative to the previous baseline, flag it as a finding.

### Step 4C — Automatic regression tests

**Every time a test detects a bug and it is fixed**, generate an automatic regression test that covers exactly that case, so it fails again if the bug reappears. That is: for every fixed FAIL, a new test must remain in the suite.

- Write the test in the framework of the layer where the bug was (unit or E2E) using the runner detected in Step 1.
- Name it traceably to the bug (e.g., `regression_{change-id}_{short-description}`).
- The test must reproduce the input/scenario that caused the failure and assert the correct behavior.
- Verify that the test passes against the fixed code (and, ideally, that it fails against the previous code).
- Record the generated regression test in `docs/test_evidence.md` (Regression section), referencing the ID of the original failed test.

### Step 5 — Document evidence

Write or update `docs/test_evidence.md`:

```markdown
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
```

### Step 5B — Update knowledge graph

Sync knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`) to reflect `test_plan.md` and `test_evidence.md`.
If `docs/spec/graphify-out/` does not exist, invoke `/graphify docs/spec/` without `--update`.

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

For every fixed FAIL, generate its regression test (Step 4C) and leave it in the suite.

Fix and re-run: /karvey-test {change-id}
Or proceed with documented failures (not recommended): /karvey-qa {change-id}
```


## Advance to the next phase

When finishing this phase and having the corresponding approval, **actively ask the user**: "Shall we advance to the QA phase now?"
- If they confirm → run `/karvey-qa {change-id}`.
- If they prefer to review or adjust first → wait. Advancing is always with the user's OK (the method's gate).
- If you resume in another session, `/karvey {change-id}` indicates which phase you are in and which one follows.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
