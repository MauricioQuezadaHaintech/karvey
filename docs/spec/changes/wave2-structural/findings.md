# Findings: wave2-structural

Triage inbox of this change (`plugins/karvey/skills/karvey/rules/iteration-loop.md`). Judges, `karvey-test`,
`karvey-qa` and `karvey-browse` append observations here with a type guess and their origin (`judge:{lens}`,
`test`, `qa`, `browse`); only `karvey-iterate` routes them. Types: `bug` → incident `BUG-NN` in
`docs/bugs_dev_testing.md` · `spec-gap` → re-open requirements · `emergent` → `docs/spec/backlog.md`.

Status: `open` → `routed` → `closed`. Convergence needs no `open`/`routed` `bug` or `spec-gap`.

| ID | Date | Phase | Origin | Type | Severity | Finding | Status | Routed to |
|----|------|-------|--------|------|----------|---------|--------|-----------|
| F-01 | 2026-09-26 | impl | impl | emergent | Low | Deviation E1.F4.T2: `karvey-state.py gate <change> <phase> [--granular-gates]` added so the one closing block of `rules/gates.md` can ask "close the gate now?" deterministically; the design names only `gate_mode` and `approve-gate`. | open | — |
| F-02 | 2026-09-26 | impl | impl | emergent | Low | Deviation E1.F9.T2: L-33 reads "created after the release" as an id above the highest one the file holds on `origin/{production}`; without that ref every duplicate stays a warning. | open | — |
| F-03 | 2026-09-26 | impl | impl | emergent | Low | Deviation E1.F7.T1: a requirement also counts as covered by a task whose `Tests added` is not `none` (this repo's tasks carry tests inside `[Backend]` tasks); `test_first` is reported apart and is true only with a `[Test]` task that the implementation tasks depend on. | open | — |
| F-04 | 2026-09-26 | impl | impl | emergent | Low | Deviation E1.F12.T2: lint L-30 (one decision-log path) now ignores `docs/spec/decisions/*.md`, the per-period shape REQ-W2-081 keeps readable; E1.F6.T3's L-49 tests live in `test_spec_merge_check.py`, not `test_lint_plugin.py`. | open | — |
| F-05 | 2026-09-26 | impl | impl | bug | Low | The method page `docs/karvey.html` still says 32 skills / 18 support / 22 rules after `karvey-judges` and the new rules (`lanes.md`, `judges.md`, `gates.md`); L-11 does not read the page. To fix with the release docs (E1.F13.T7). | open | — |
