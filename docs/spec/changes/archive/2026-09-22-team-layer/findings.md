# Findings — `team-layer`

| # | Type | Finding | State |
|---|---|---|---|
| F-01 | emergent | `karvey-health` could check the team layer's readiness (handoff age per role, stale board ahead of handoff) the way it already checks method readiness. Not implemented here. | routed → BL-34 |
| F-02 | emergent | The auditing idea from the source proposal — a sampled weekly audit where **the auditor also audits whoever directs**, and the report declares what it could not verify — belongs in `karvey-retro`/`karvey-health`. Not implemented here. | routed → BL-35 |
| F-03 | spec-gap | `karvey-team cost` depends on what the runtime exposes about per-session usage; the skill describes the report but the collection is environment-specific and unproven. | routed → BL-37 |
| F-04 | emergent | The statusline cannot be declared by a plugin (only `agent` / `subagentStatusLine`). Documented as a manual three-line install; worth revisiting if the plugin API changes. | routed → BL-36 |
