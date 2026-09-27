# Karvey — equivalences with Kiro and gstack

Reference of the orchestrator, loaded only when the user comes from Kiro or gstack and asks where a command lives.

Karvey absorbs the value of both. What in gstack are standalone commands lives here in a **phase** or in the **cross-cutting layer**.

| Kiro / gstack | In Karvey |
|---------------|-----------|
| kiro `/spec`, `/kiro-spec-*` | grill + PRD + EARS requirements (PHASE 0–2) |
| office-hours, plan-ceo-review | 10-star reframe in `karvey-grill` |
| plan-design-review, design-consultation, design-shotgun | `karvey-design-graphic` + `karvey-mockup` (shotgun) |
| plan-eng-review, diagram | `karvey-architecture` + `karvey-diagram` |
| setup-deploy | `karvey-infra` (platform auto-detection) |
| review, cso (OWASP+STRIDE), codex, design-review | `karvey-qa` (9 dim) + `karvey-second-opinion` |
| qa, browse, benchmark | `karvey-test` + `karvey-browse` + `karvey-health` |
| ship, land-and-deploy, canary | `karvey-deploy` |
| investigate | `karvey-investigate` |
| (no direct equivalent — feedback loop) | `karvey-iterate` (route findings: bug/spec-gap/emergent) |
| health | `karvey-health` |
| context-save/restore | `karvey-checkpoint` |
| document-generate/release, make-pdf | `karvey-docs` |
| retro | `karvey-retro` / PHASE 12 |
| learn, gbrain | `knowledge-sync` (graphify/obsidian) |
| careful, freeze, guard | `karvey-guard` + `enforcement.md` hooks |
| devex-review | `karvey-devex` |
| scrape, skillify | `karvey-scrape` |
| benchmark-models | `karvey-benchmark-models` |
| ios-qa, ios-fix, ios-design-review | generalized via `targets.md` (real runtime per target) |
| existing `.kiro/specs/*` / gstack specs (migration) | `karvey-import --from kiro\|gstack` |

N/A (gstack-proprietary, with a generic equivalent): `open-gstack-browser` → `karvey-browse` runtime; `gstack-upgrade` → N/A; `pair-agent`/`gbrain` → `knowledge-sync`.
