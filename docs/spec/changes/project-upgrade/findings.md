# Findings: project-upgrade

Triage inbox of this change (`plugins/karvey/skills/karvey/rules/iteration-loop.md`). `karvey-impl`, `karvey-test`,
`karvey-qa` and `karvey-browse` append observations here with a type guess; only `karvey-iterate` routes them.
Types: `bug` → incident `BUG-NN` in `docs/bugs_dev_testing.md` · `spec-gap` → re-open requirements or amend the
architecture · `emergent` → `docs/spec/backlog.md`.

Status: `open` → `routed` → `closed`. Convergence needs no `open`/`routed` `bug` or `spec-gap`.

| # | Date | Source phase | Type | Severity | Title | Status | Routed to |
|---|------|--------------|------|----------|-------|--------|-----------|
| F-01 | 2026-09-25 | impl | spec-gap | low | Architecture §1.8 L-38 says "`since` ≤ the plugin version", but §1.6 / A-12 set every step's `since` to the working number 3.13.0 while `plugin.json` stays 3.11.4 until the release (the version moves only at `karvey-deploy`), so L-38 would fail the whole-repo lint for the entire impl. Smallest deviation (E1.F7.T1): a `since` newer than `plugin.json` is **one warning** naming the steps while `## [Unreleased]` holds entries, and an **error** once `[Unreleased]` is empty (at the release, where `karvey-deploy` must set `since` to the release). Unit test `test_lint_plugin.py: L38.test_since_newer_than_the_plugin`. The architecture §1.8 row should say so. | open | architecture.md §1.8 (at QA or archive) |
| F-02 | 2026-09-25 | impl | spec-gap | low | `legacy-shims` must diff an edited copy against the **shipped** shim and `enforcement-defaults` must read the plugin's `project.schema.json`, but the §1.4 `Probe` only reads under the project root and the home. Added `Probe.plugin_read` / `plugin_json` (read-only, confined to the plugin root); L-38 still forbids any direct I/O in step functions. §1.4 should list them. | open | architecture.md §1.4 |
| F-03 | 2026-09-25 | impl | spec-gap | low | `tasks.md` E1.F5.T2 names `bash plugins/karvey/tests/test-hooks.sh`; the suite lives at `plugins/karvey/hooks/tests/test-hooks.sh` (the one CI runs). Ran that one. The same suite ran the session hook with the real `HOME`; it now uses an isolated `HOME` / `XDG_STATE_HOME`, because the startup offer may write its seen record under the state dir of a project outside git. | closed | E1.F5.T2 |
