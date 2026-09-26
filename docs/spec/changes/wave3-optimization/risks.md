# Risks: wave3-optimization

Created by architecture (REQ-W3-031) from `architecture.md` §12. Format of `rules/risks.md` (C-17); states `open |
mitigated | accepted | closed | moved`. Later state changes go through `karvey-state.py risk` once it exists.

| ID | Risk | Probability | Impact | Owner | Trigger | Mitigation | State | Last review |
|----|------|-------------|--------|-------|---------|------------|-------|-------------|
| R-1 | The reorganisation drops a hard contract a phase needs | Medium | High | method owner | contracts check red | contract map from the 4.0 closure; check in the test phase and CI | open | 2026-09-26 architect |
| R-2 | The 40% median is not reached without redesigning text | Medium | Medium | method owner | `compare` below 40% | references, adapters and the orchestrator carry most of the weight; reasons per phase recorded; F2 runs on the final text | open | 2026-09-26 architect |
| R-3 | Leak check false negative (a secret or personal-data shape not in the patterns, e.g. a person's name in free text) | Low | High | method owner | a leaked value found in review | allow-listed model first, then patterns and `leak.deny_terms`; refusals logged; the QA security judge reviews the patterns | open | 2026-09-26 architect |
| R-4 | Leak check false positive blocks every page | Medium | Low | method owner | refusals on clean pages | refusal names field and rule; patterns are data, tuned without code | open | 2026-09-26 architect |
| R-5 | The runtime changes the statusline `cost` fields or the transcript usage format | Low | Medium | method owner | captures stop or tokens read `n/a` | `n/a` with the reason, never zero; revalidation condition in architecture §1.0 | open | 2026-09-26 architect |
| R-6 | Wave 2 text changes after the baseline is taken | Medium | Medium | method owner | a wave2 commit touching skills or rules after the fork point | re-take the baseline in its own commit before the first move | open | 2026-09-26 architect |
| R-7 | The method page grows from about 426 KB to about 760 KB | High | Low | method owner | page size in the release notes | self-contained is required; no external assets; size reported | open | 2026-09-26 architect |
| R-8 | Translation quality in four new languages | Medium | Medium | method owner | a reader reports a wrong term | fixed terms (commands, ids) kept in English; completeness lint; fixes through the `patch` lane | open | 2026-09-26 architect |
| R-9 | The portfolio shows one client's data to another client's reader | Low | High | method owner | output shared outside the team | `--client` filter; stdout only, never published | open | 2026-09-26 architect |
