# Iteration Loop — Karvey is a spiral, not a line

> **Afán** (the meaning of *Karvey*) = you don't stop until the result is really achieved.
> The pipeline (0→12) is the **happy path**. Reality is iterative: testing, QA and real-runtime
> use surface defects and new ideas. This rule defines the **feedback edges** that send each
> finding back to where it belongs, so **nothing is dropped** ("queda botado").

## The problem this solves

The base pipeline only has ONE backward edge — the QA micro-loop for code bugs:

```
qa.approved=false (criticals/highs) → Fix → re-impl → re-test → re-qa
```

That covers **code bugs found in QA**. It does NOT cover:
- A finding that is actually a **spec defect / missing requirement** → there was no edge back to `requirements`.
- A **new scope / emergent idea** discovered mid-cycle or after archive → it stayed "in the air".

Karvey closes these with three feedback edges + one engine (`karvey-iterate`).

## The three feedback edges

Every finding observed in `test`, `qa` or `browse` is classified into exactly one type. The type decides its edge:

| Finding type | Meaning | Edge (where it goes) |
|--------------|---------|----------------------|
| `bug` | The code does not do what the (correct) spec says. | Incident tracker (`BUG-NN`, see `incident-tracking.md`) → QA micro-loop `impl→test→qa`. |
| `spec-gap` | The spec itself is wrong, incomplete or was misunderstood. The code may be "correct" against a wrong spec. | **Re-open `requirements`**: amend `spec-delta.md`, re-trace to the PRD, ripple forward only the affected phases. |
| `emergent` | Valid new scope / idea, but **out of this change's scope**. | **Backlog** (see `backlog.md`) → becomes a future `change-id`. Never silently absorbed into the current change. |

> Litmus test to classify:
> - "The spec is right, the code is wrong" → `bug`.
> - "If we'd specified this correctly, impl would have been different" → `spec-gap`.
> - "This is a good idea but it's a different change" → `emergent`.

## findings.md — the triage artifact

`test`, `qa` and `browse` append every observation to `docs/spec/changes/{change-id}/findings.md`.
This is the **single inbox** the iteration engine reads.

```markdown
# Findings: {change-id}

| # | Date | Source phase | Type | Severity | Title | Status | Routed to |
|---|------|--------------|------|----------|-------|--------|-----------|
| F-01 | 2026-06-17 | test | bug | high | SP returns NULL on empty input | routed | BUG-07 |
| F-02 | 2026-06-17 | qa | spec-gap | — | timeout must be tenant-configurable | routed | spec-delta (req 4.2) |
| F-03 | 2026-06-17 | browse | emergent | — | allow PDF export of the report | routed | backlog #BL-12 |

## F-01 — SP returns NULL on empty input
- **Type:** bug · **Severity:** high · **Source:** test (UT-BD-03)
- **Detail:** ...
- **Routed to:** incident BUG-07 → QA micro-loop
```

`status`: `open` → `routed` (the engine acted on it) → `closed` (resolved at the destination).

## The spec-revision sub-cycle (the `spec-gap` edge)

When a `spec-gap` is routed, the change **re-opens `requirements` in revision mode**:

1. `spec.json`: set `approvals.requirements.approved = false`, increment `iteration_count`, append to `revision_history`.
2. Amend `requirements.md` + `spec-delta.md` for **only the affected requirement** (not a full rewrite), keeping PRD traceability.
3. Re-approve requirements with the user (the gate still applies).
4. **Ripple forward only the affected phases** — not the whole pipeline from scratch. Re-touch mockup/design/architecture/tasks/impl **only if** the spec change affects them. The orchestrator's state machine drives which phases re-open.
5. Re-run `test`/`qa` for the affected scope.

This is a real backward edge in the state machine, not an ad-hoc fix.

## Convergence — when does the loop stop

A change is **done** (eligible for `deploy`/`archive`) only when:
- `findings.md` has no `open` items of type `bug` or `spec-gap`.
- All `emergent` findings have been moved to the backlog (none left `open`).
- The QA security gate passes (no critical/high).

`emergent` findings never block the current change — they only need to be **captured** (routed to backlog), not resolved. `bug` and `spec-gap` findings **do** block until resolved. This is how *Afán* is enforced: the change cannot pretend to be finished while its own findings inbox still has unrouted or unresolved work.

## Who writes / who routes

- **Writers** (observe and classify): `karvey-test`, `karvey-qa`, `karvey-browse`. They only **append** to `findings.md` with a type guess; they never route.
- **Router** (one brain): `karvey-iterate`. It reads `findings.md`, confirms/corrects each type, and dispatches to the right edge (incident tracker, spec-revision, or backlog), updating `status` and `routed to`.

Separating observation from routing keeps the loop logic in one place and the phase skills simple.
