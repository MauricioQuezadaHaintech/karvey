# Incident Tracking — `BUG-NN` with state history

> Karvey keeps a **dedicated, persistent incident tracker** for bugs, with **state history** —
> complementary to the team's tracker (`management-adapters.md`), not a replacement. The tracker holds *work/tasks*; this tracker keeps
> the **technical history** of each incident (reproduction, root cause, state transitions over time).

## Where it lives — per repo + global index

- **Per repo:** `docs/bugs_dev_testing.md` at each repo root. Incidents numbered `BUG-NN`, incremental, **never reset** (continue the sequence across changes). Before adding one, **read the file** to continue the counter.
- **Project-wide index:** `docs/spec/incidents-index.md` in the `spec_repo`. Aggregates every `BUG-NN` from every repo with its current state, so there is a single global view.

A `bug`-type finding (see `iteration-loop.md`) is promoted to a `BUG-NN` here by `karvey-iterate`.

## Incident entry format (`docs/bugs_dev_testing.md`)

```markdown
## BUG-07 — SP returns NULL on empty input
- **Priority:** high
- **Detected:** 2026-06-17 · **Component:** db / sip.GetClaims
- **Change / origin:** add-claim-filter (finding F-01, source: test UT-BD-03)
- **Tracker:** abc123 (if `karvey-config.py resolve management` reports `external: true`)
- **Current state:** EN FIX

### Reproduction
{exact input / steps that trigger it}

### Actual vs expected
- Actual: returns NULL, frontend crashes
- Expected: returns empty set, controlled

### Root cause
{evidence-backed cause; if analyzed with karvey-investigate, paste its conclusion + ref}

### Fix
{proposed / applied fix, files, commit}

### Regression
`tests/unit/test_claims.py::test_empty_input` (the test, or `L-NN`, that fails if the bug returns)

### State history
| Date | State | By (human + AI model) | Note |
|------|-------|------------------------|------|
| 2026-06-17 14:02 | DETECTADO | M. Quezada / Opus 4.8 | found in test UT-BD-03 |
| 2026-06-17 14:30 | DIAGNOSTICADO | M. Quezada / Opus 4.8 | karvey-investigate: missing ISNULL guard |
| 2026-06-17 15:10 | EN FIX | M. Quezada / Opus 4.8 | patch on feature/add-claim-filter |
```

## State machine

```
DETECTADO ─→ DIAGNOSTICADO ─→ EN FIX ─→ RESUELTO
     ▲                                      │
     └──────────────── REABIERTO ◀──────────┘   (if it regresses)
```

- **DETECTADO** — logged from a finding, not yet root-caused.
- **DIAGNOSTICADO** — root cause established (with evidence). Complex cases: use `karvey-investigate` (diagnoses, does **not** fix) and paste its result here.
- **EN FIX** — a fix is being applied on the change's feature branch.
- **RESUELTO** — fixed + a **regression test** exists so it fails again if it reappears. The incident's `### Regression` section **names** it: a test file path that exists, or a lint id (`L-NN`); `lint-plugin.py` L-32 checks it.
- **REABIERTO** — a `RESUELTO` incident regressed; re-opens with a new history row, keeping the same `BUG-NN`.

**Every transition appends a row to "State history"** (date + responsible human + AI model + note). The history is never overwritten — that is the whole point.

## Relationship with the rest of the method

- **vs `findings.md`:** `findings.md` is the per-change inbox/triage. The incident tracker is the **persistent, cross-change** record of confirmed bugs. A finding of type `bug` → one `BUG-NN`.
- **vs the team's tracker:** if one is configured, the `BUG-NN` references its tracker item and vice-versa. Status changes are mirrored at the phase-close ritual (`phase-close.md`).
- **vs `karvey-investigate`:** complex bugs get a formal root-cause via `/karvey-investigate`; its output becomes the `Root cause` section and flips the state to `DIAGNOSTICADO`.
- **vs regression tests:** an incident only reaches `RESUELTO` once its named regression test is in the suite. No named regression → it stays `EN FIX`.

## When to use which

- Quick, obvious bug → log `BUG-NN`, fix, add regression test, `RESUELTO`.
- Bug whose cause is unclear → `/karvey-investigate` first (Iron Law: no fix without investigating), then log/advance the incident.
