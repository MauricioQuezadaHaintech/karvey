# Risks: mockup-conformance

Created by architecture from `architecture.md` §12 (rule `risks.md`); states `open | mitigated | accepted | closed |
moved`. Later state changes go through `karvey-state.py risk`.

| ID | Risk | Probability | Impact | Owner | Trigger | Mitigation | State | Last review |
|----|------|-------------|--------|-------|---------|------------|-------|-------------|
| R-1 | Rendering noise (fonts, anti-aliasing) makes every pair `over threshold`, and owners approve deviations in bulk | Medium | High | method owner | median ratio of passing fixtures > threshold/2 | text/style/box compared exactly and separately; tolerance + masking; per-project tuning on the reviewed line; ≤ 10 ids per phrase | open | 2026-09-27 architect |
| R-2 | Pure-Python PNG comparison is slow on large viewports or many entries | Medium | Low | method owner | a run > 60 s on the fixture | row-wise `bytes` loops over `memoryview`; one pass per gate recomputation; run time measured in the fixture test and reported | open | 2026-09-27 architect |
| R-3 | No browser automation available where `browse.via: local` | Medium | Medium | method owner | MC-3 reports it | `agent:<name>` delegation; `not evaluated` + owner deviation as the explicit exit | open | 2026-09-27 architect |
| R-4 | A delegated agent fabricates images that pass | Low | High | method owner | a capture whose probe disagrees with its image | manifest + request binding, probe hash, commit and mockup hash; the owner sees side-by-side images; honest limit stated (S-7) | open | 2026-09-27 architect |
| R-5 | Screenshots of a development build expose data in a public repository | Low | High | method owner | a capture showing non-fixture data | fixture-only plan, production refusal, `captures: local`, review of images in the PR | open | 2026-09-27 architect |
| R-6 | Teams find element ids a burden and mark everything `gap` or `no-spec-impact` | Medium | Medium | method owner | a high share of gaps / dismissals in metrics | gaps block approval; dismissals shown at the gate; metrics per change | open | 2026-09-27 architect |
| R-7 | The new rule and skill text push a phase's closure above +10 % | Medium | Medium | method owner | `compare --fail-growth 10` red | rule ≤ 900 words, details in scripts, L-82 | open | 2026-09-27 architect |
| R-8 | Rebasing onto `living-docs`' final head moves the confirm markers, settings reader, component code or lint ids this design cites | High | Low | method owner | `living-docs` impl merged | §13 re-verification list; first impl task | open | 2026-09-27 architect |
| R-9 | Same-OS-user forgery of the deviation ledger | Low | High | method owner | a ledger line without a hook audit record | protect-paths, audit cross-check at every blocker call, honest limit stated (S-2) | open | 2026-09-27 architect |
| R-10 | The runtime delivers another agent's message to the prompt hook as a user turn | Low | High | method owner | a deviation marker whose transcript turn is not the owner's | transcript cross-check before writing the marker; the notice echoes what was bound; the owner reads the release summary | open | 2026-09-27 architect |
| R-11 | Captures come from a build that is not the recorded commit (running server not rebuilt) | Medium | Medium | method owner | `build commit unproven` or a meta mismatch | build-commit meta tag checked by the probe; mismatch unverified; unproven listed at the gate | open | 2026-09-27 architect |
