# Risks: sample-change

| ID | Risk | Probability | Impact | Owner | Trigger | Mitigation | State | Last review |
|----|------|-------------|--------|-------|---------|------------|-------|-------------|
| R-1 | People who left keep access for a while (see D-12) | Medium | High | security officer | an account closed after the nightly check | a same-day check, waiting for the sponsor's answer | open | 2026-10-13 |
| R-2 | Sign-in records kept longer than allowed | Low | Medium | product owner | a retention review | records deleted after 12 months by `purge --older 12m` | mitigated | 2026-10-12 |
