# Rule: risks — one register per change, with an owner and a date

A change keeps its risks in `docs/spec/changes/{change-id}/risks.md`. A change without the file has no risks.

## Format

| ID | Risk | Probability | Impact | Owner | Trigger | Mitigation | State | Last review |
|----|------|-------------|--------|-------|---------|------------|-------|-------------|
| R-1 | {what could go wrong, in business words} | Low / Medium / High | Low / Medium / High | {role} | {what sets it off} | {what is done about it} | open | {YYYY-MM-DD} {reviewer role} |

- **Ids** `R-N` are local to the register (not minted by the id tool), never reused.
- **Owner** is a role (or the stakeholder name the project declares); a risk without an owner is reported by
  `karvey-state.py validate` (check `risks.owner`, warn).
- **States:** `open` (being watched) · `mitigated` (reduced) · `accepted` (accepted as is) · `closed` (no longer a
  risk) · `moved` (carried to later work, `moved → BL-NN`). The sponsor page shows them only through the
  wording table (`${CLAUDE_PLUGIN_ROOT}/schemas/wording.json`).

## Who writes it

- **Architecture creates it** from its risk analysis (the "Risks and mitigations" table), one row per risk with its
  owner and trigger.
- **Any phase adds rows.** In a lane that skips architecture, the first phase that finds a risk creates the file.
- **Judges never write it:** a judge proposes a risk as a finding; `/karvey-iterate` accepts it into the register.
- **State changes** go through `karvey-state.py risk {change-id} R-N review|close|move|mitigate|accept`, which
  rewrites the row and logs the change in `spec.json:risk_log`. The owner answers; the tool writes.
