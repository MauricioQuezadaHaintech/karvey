# Discovery Backlog — Karvey Method

| ID | Date | Origin | Type | Priority | Title | Status | Tracker | Promoted to change-id |
|----|------|--------|------|----------|-------|--------|---------|-----------------------|
| BL-01 | 2026-09-22 | session 3.8.0 → 3.9.1 (owner request) | tech-debt | high | Run graphify over the repo at the end of all the changes | done | — | — |
| BL-02 | 2026-09-22 | graphify review (owner) | feature | high | Notifications configurable per team (not Google Chat hard-coded in karvey-qa) | promoted | — | team-adapters |
| BL-03 | 2026-09-22 | graphify review (owner) | feature | high | Task-management tool + status flow configurable (not ClickUp `listo! para pap` hard-coded) | promoted | — | team-adapters |
| BL-04 | 2026-09-23 | panel review R-01 | tech-debt | high | [Ola 1] Máquina de estados única, con esquema y script (`karvey-state.py`) | promoted | — | wave1-hardening |
| BL-05 | 2026-09-23 | panel review R-02 | tech-debt | high | [Ola 1] Hooks que hagan lo que dicen, un `prod-gate` y tests de tabla | promoted | — | wave1-hardening |
| BL-06 | 2026-09-23 | panel review R-03 | tech-debt | high | [Ola 1] Sacar de `dev` los commits de deploy y archive, y ordenar el checklist | promoted | — | wave1-hardening |
| BL-07 | 2026-09-23 | panel review R-04 | tech-debt | high | [Ola 1] Un solo momento de versionado | promoted | — | wave1-hardening |
| BL-08 | 2026-09-23 | panel review R-05 | tech-debt | high | [Ola 1] No pisar la estimación; guardar el estimado y el real | promoted | — | wave1-hardening |
| BL-09 | 2026-09-23 | panel review R-06 | tech-debt | high | [Ola 1] Hook de sesión: `archive/`, inyección acotada y `state.json` por script | promoted | — | wave1-hardening |
| BL-10 | 2026-09-23 | panel review R-07 | tech-debt | high | [Ola 1] El plugin como código: sin copias, rutas resolubles y CI con linter | promoted | — | wave1-hardening |
| BL-11 | 2026-09-23 | panel review R-08 | feature | high | [Ola 2] Liberar por cambio, con manifiesto de release y modo trunk | open | — | — |
| BL-12 | 2026-09-23 | panel review R-09 | feature | high | [Ola 2] Carriles por tamaño de cambio | open | — | — |
| BL-13 | 2026-09-23 | panel review R-10 | feature | high | [Ola 2] Menos gates humanos, con más peso y sin auto-aprobación | open | — | — |
| BL-14 | 2026-09-23 | panel review R-11 | feature | high | [Ola 2] Paneles de jueces expertos en los gates tempranos | open | — | — |
| BL-15 | 2026-09-23 | panel review R-12 | feature | med | [Ola 2] Test-first y matriz de trazabilidad REQ → tarea → commit → test | open | — | — |
| BL-16 | 2026-09-23 | panel review R-13 | feature | med | [Ola 2] Gate de seguridad con herramientas deterministas | open | — | — |
| BL-17 | 2026-09-23 | panel review R-14 | feature | high | [Ola 2] Métricas de flujo y DORA desde los artefactos, con `phase_history` | open | — | — |
| BL-18 | 2026-09-23 | panel review R-15 | feature | med | [Ola 3] Presupuesto de contexto por fase y carga progresiva | open | — | — |
| BL-19 | 2026-09-23 | panel review R-16 | tech-debt | med | [Ola 1] Graphify y el ritual del tracker, fuera del camino caliente | promoted | — | wave1-hardening |
| BL-20 | 2026-09-23 | panel review R-17 | tech-debt | med | [Ola 1] Living specs: fusionar el spec-delta en el PR del código | promoted | — | wave1-hardening |
| BL-21 | 2026-09-23 | panel review R-18 | tech-debt | high | [Ola 1] Dashboard completo: trabajo abierto, antigüedad y WIP | promoted | — | wave1-hardening |
| BL-22 | 2026-09-23 | panel review R-19 | feature | med | [Ola 3] Visibilidad para stakeholders y eventos de "te toca a ti" | open | — | — |
| BL-23 | 2026-09-23 | panel review R-20 | feature | med | [Ola 2] Scripts de release-gate, IDs, health score y evidencia | open | — | — |
| BL-24 | 2026-09-23 | panel review R-21 | tech-debt | med | [Ola 1] QA observa sin arreglar, artefactos dentro del cambio y reglas de stack a `standards/` | promoted | — | wave1-hardening |
| BL-25 | 2026-09-23 | panel review R-22 | tech-debt | med | [Ola 1] Descripciones de frontmatter cortas y sin triggers genéricos | promoted | — | wave1-hardening |
| BL-26 | 2026-09-23 | panel review R-23 | feature | med | [Ola 2] El canary pasa a ser una verificación post-deploy con umbrales | open | — | — |
| BL-27 | 2026-09-23 | panel review R-24 | feature | med | [Ola 3] Decisiones pendientes (Q-NN) y riesgos con dueño y fecha | open | — | — |
| BL-28 | 2026-09-23 | panel review R-25 | feature | med | [Ola 3] Costo por cambio también con un solo agente | open | — | — |
| BL-29 | 2026-09-23 | panel review R-26 | feature | med | [Ola 3] Sistema de diseño a nivel de proyecto; design-graphic como delta | open | — | — |
| BL-30 | 2026-09-23 | panel review R-27 | feature | med | [Ola 3] WBS sin ambigüedad sobre qué es una Feature | open | — | — |
| BL-31 | 2026-09-23 | panel review R-28 | feature | med | [Ola 3] Vista de portafolio multi-cliente | open | — | — |
| BL-32 | 2026-09-23 | panel review R-29 | feature | low | [Ola 3] Backlog con priorización (WSJF) y estado `done-direct` | open | — | — |
| BL-33 | 2026-09-23 | panel review R-30 | feature | low | [Ola 3] Portabilidad a otros runtimes y equipos | open | — | — |
| BL-34 | 2026-09-23 | team-layer / F-01 | emergent | med | karvey-health checks team-layer readiness (handoff age per role, stale board) | open | — | — |
| BL-35 | 2026-09-23 | team-layer / F-02 | emergent | low | Sampled weekly audit where the auditor also audits whoever directs (retro/health) | open | — | — |
| BL-36 | 2026-09-23 | team-layer / F-04 | emergent | low | Statusline cannot be declared by a plugin — revisit if the plugin API changes | open | — | — |
| BL-37 | 2026-09-23 | team-layer / F-03 | spec-gap (deferred) | med | karvey-team cost: per-session usage collection is runtime-specific and unproven | open | — | — |
| BL-38 | 2026-09-23 | team-adapters / F-21 | emergent | med | Validate team settings (required keys, enums, documented aliases) in the session hook / karvey-context | open | — | — |
| BL-39 | 2026-09-23 | team-adapters / F-42 | emergent | low | Generate rule-citation tables, per-phase rule lists and command spellings from the source; one status notation | open | — | — |
| BL-40 | 2026-09-23 | team-adapters / F-45 | emergent | low | Settings nudge and skills for Karvey repos that keep specs under `spec/` instead of `docs/spec/` | open | — | — |
| BL-41 | 2026-09-23 | team-adapters / F-46 | emergent | low | Statusline: keep the rotate warning visible on narrow terminals; recommend the copy-to-~/.claude install path | open | — | — |
| BL-42 | 2026-09-23 | team-adapters / F-47 | emergent | low | Method page: alias table for the 12 anchors renamed after 3.10.0 | open | — | — |
| BL-43 | 2026-09-23 | team-adapters / F-48 | emergent | low | Notification deduplication: run id + timestamp in the payload; notify QA on first run and verdict changes | open | — | — |

## BL-01 — Run graphify over the repo at the end of all the changes
- **Origin:** owner request (Mauricio Quezada Ibáñez), 2026-09-22, after publishing 3.8.0 / 3.9.0 and during the 3.9.1 docs sync.
- **Why:** `project.json:knowledge_sync = "graphify"` — the method's own knowledge-sync step (`rules/knowledge-sync.md`) was never run on this repo, so there is no `graphify-out/` reflecting skills, rules and their relations. The owner wants the repo left ordered once the pending changes land.
- **Rough scope:** after the last merge to `main`, run `/graphify` on the repo root (then `--update` on later changes); review `GRAPH_REPORT.md` for orphan rules, skills not referenced by the orchestrator, and broken cross-references; decide whether `graphify-out/` is versioned or ignored.
- **Status:** done — 2026-09-22, resolved directly (no change-id): `graphify-out/` built over the repo (82 files → 399 nodes, 753 edges, 21 communities) and versioned with repo-relative paths; only `graphify-out/.graphify_python` (machine-specific interpreter path) is ignored. Refresh with `graphify . --update` after later changes.

## BL-02 — Notifications configurable per team
- **Origin:** graphify review of the repo, 2026-09-22 — `karvey-qa` Step 4 always notified Google Chat via a `CLAUDE.md` table.
- **Why:** another team uses Slack, Teams, e-mail or nothing; the step failed or did not apply.
- **Status:** promoted → `team-adapters`

## BL-03 — Task-management tool and status flow configurable
- **Origin:** graphify review of the repo, 2026-09-22 — `listo! para pap` hard-coded in clickup-protocol, phase-close, karvey-impl, karvey-tasks.
- **Why:** teams use Jira, Linear, Azure Boards, a spreadsheet… and their own status names.
- **Status:** promoted → `team-adapters`

## BL-04 — Máquina de estados única, con esquema y script (`karvey-state.py`)
- **Origin:** expert panel review 2026-09-23, `R-01` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** alta
- **Status:** promoted → `wave1-hardening`

## BL-05 — Hooks que hagan lo que dicen, un `prod-gate` y tests de tabla
- **Origin:** expert panel review 2026-09-23, `R-02` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** alta
- **Status:** promoted → `wave1-hardening`

## BL-06 — Sacar de `dev` los commits de deploy y archive, y ordenar el checklist
- **Origin:** expert panel review 2026-09-23, `R-03` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** alta
- **Status:** promoted → `wave1-hardening`

## BL-07 — Un solo momento de versionado
- **Origin:** expert panel review 2026-09-23, `R-04` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** alta
- **Status:** promoted → `wave1-hardening`

## BL-08 — No pisar la estimación; guardar el estimado y el real
- **Origin:** expert panel review 2026-09-23, `R-05` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** alta
- **Status:** promoted → `wave1-hardening`

## BL-09 — Hook de sesión: `archive/`, inyección acotada y `state.json` por script
- **Origin:** expert panel review 2026-09-23, `R-06` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** alta
- **Status:** promoted → `wave1-hardening`

## BL-10 — El plugin como código: sin copias, rutas resolubles y CI con linter
- **Origin:** expert panel review 2026-09-23, `R-07` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** alta
- **Status:** promoted → `wave1-hardening`

## BL-11 — Liberar por cambio, con manifiesto de release y modo trunk
- **Origin:** expert panel review 2026-09-23, `R-08` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 2 · **Priority:** alta
- **Status:** open

## BL-12 — Carriles por tamaño de cambio
- **Origin:** expert panel review 2026-09-23, `R-09` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 2 · **Priority:** alta
- **Status:** open

## BL-13 — Menos gates humanos, con más peso y sin auto-aprobación
- **Origin:** expert panel review 2026-09-23, `R-10` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 2 · **Priority:** alta
- **Status:** open

## BL-14 — Paneles de jueces expertos en los gates tempranos
- **Origin:** expert panel review 2026-09-23, `R-11` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 2 · **Priority:** alta
- **Status:** open

## BL-15 — Test-first y matriz de trazabilidad REQ → tarea → commit → test
- **Origin:** expert panel review 2026-09-23, `R-12` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 2 · **Priority:** media
- **Status:** open

## BL-16 — Gate de seguridad con herramientas deterministas
- **Origin:** expert panel review 2026-09-23, `R-13` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 2 · **Priority:** media
- **Status:** open

## BL-17 — Métricas de flujo y DORA desde los artefactos, con `phase_history`
- **Origin:** expert panel review 2026-09-23, `R-14` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 2 · **Priority:** alta
- **Status:** open

## BL-18 — Presupuesto de contexto por fase y carga progresiva
- **Origin:** expert panel review 2026-09-23, `R-15` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 3 · **Priority:** media
- **Status:** open

## BL-19 — Graphify y el ritual del tracker, fuera del camino caliente
- **Origin:** expert panel review 2026-09-23, `R-16` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** media
- **Status:** promoted → `wave1-hardening`

## BL-20 — Living specs: fusionar el spec-delta en el PR del código
- **Origin:** expert panel review 2026-09-23, `R-17` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** media
- **Status:** promoted → `wave1-hardening`

## BL-21 — Dashboard completo: trabajo abierto, antigüedad y WIP
- **Origin:** expert panel review 2026-09-23, `R-18` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** alta
- **Status:** promoted → `wave1-hardening`

## BL-22 — Visibilidad para stakeholders y eventos de "te toca a ti"
- **Origin:** expert panel review 2026-09-23, `R-19` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 3 · **Priority:** media
- **Status:** open

## BL-23 — Scripts de release-gate, IDs, health score y evidencia
- **Origin:** expert panel review 2026-09-23, `R-20` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 2 · **Priority:** media
- **Status:** open

## BL-24 — QA observa sin arreglar, artefactos dentro del cambio y reglas de stack a `standards/`
- **Origin:** expert panel review 2026-09-23, `R-21` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** media
- **Status:** promoted → `wave1-hardening`

## BL-25 — Descripciones de frontmatter cortas y sin triggers genéricos
- **Origin:** expert panel review 2026-09-23, `R-22` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 1 · **Priority:** media
- **Status:** promoted → `wave1-hardening`

## BL-26 — El canary pasa a ser una verificación post-deploy con umbrales
- **Origin:** expert panel review 2026-09-23, `R-23` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 2 · **Priority:** media
- **Status:** open

## BL-27 — Decisiones pendientes (Q-NN) y riesgos con dueño y fecha
- **Origin:** expert panel review 2026-09-23, `R-24` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 3 · **Priority:** media
- **Status:** open

## BL-28 — Costo por cambio también con un solo agente
- **Origin:** expert panel review 2026-09-23, `R-25` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 3 · **Priority:** media
- **Status:** open

## BL-29 — Sistema de diseño a nivel de proyecto; design-graphic como delta
- **Origin:** expert panel review 2026-09-23, `R-26` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 3 · **Priority:** media
- **Status:** open

## BL-30 — WBS sin ambigüedad sobre qué es una Feature
- **Origin:** expert panel review 2026-09-23, `R-27` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 3 · **Priority:** media
- **Status:** open

## BL-31 — Vista de portafolio multi-cliente
- **Origin:** expert panel review 2026-09-23, `R-28` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 3 · **Priority:** media
- **Status:** open

## BL-32 — Backlog con priorización (WSJF) y estado `done-direct`
- **Origin:** expert panel review 2026-09-23, `R-29` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 3 · **Priority:** baja
- **Status:** open

## BL-33 — Portabilidad a otros runtimes y equipos
- **Origin:** expert panel review 2026-09-23, `R-30` in `docs/spec/reviews/2026-09-23-panel-review.md` (problem, recommendation, justification, benefit, effort and risk there).
- **Wave:** 3 · **Priority:** baja
- **Status:** open

## BL-34 — karvey-health checks team-layer readiness (handoff age per role, stale board)
- **Origin:** change `team-layer`, finding F-01 (emergent), swept at archive on 2026-09-23.
- **Status:** open

## BL-35 — Sampled weekly audit where the auditor also audits whoever directs (retro/health)
- **Origin:** change `team-layer`, finding F-02 (emergent), swept at archive on 2026-09-23.
- **Status:** open

## BL-36 — Statusline cannot be declared by a plugin — revisit if the plugin API changes
- **Origin:** change `team-layer`, finding F-04 (emergent), swept at archive on 2026-09-23.
- **Status:** open

## BL-37 — karvey-team cost: per-session usage collection is runtime-specific and unproven
- **Origin:** change `team-layer`, finding F-03 (spec-gap (deferred)), swept at archive on 2026-09-23.
- **Status:** open
- **Note:** a spec-gap normally re-opens requirements; `team-layer` had already shipped in 3.8.0, so it is deferred here as a known limitation instead of silently dropped.

## BL-38 — Validate team settings (required keys, enums, documented aliases) in the session hook / karvey-context
- **Origin:** change `team-adapters`, finding F-21 (emergent; source I-03), retroactive QA on 2026-09-23 (`docs/spec/changes/team-adapters/qa/REVISION_PR_17-19_20260923.md`).
- **Why:** Tarien stores `status_flow` instead of `statuses` and `google_chat` instead of `google-chat`; the hook only checks that each block is an object, so a drifted project looks configured and the first status change re-asks. Validate `tool`, `statuses` (5 keys), `channel`, `target`, `via` and print "settings invalid (...)", or accept documented aliases. Can reuse `project.schema.json` from BL-04. Fixing Tarien itself belongs to Tarien's repo.
- **Status:** open

## BL-39 — Generate rule-citation tables, per-phase rule lists and command spellings from the source; one status notation
- **Origin:** change `team-adapters`, finding F-42 (emergent; source C-08, C-12, C-13, C-14, C-17), retroactive QA on 2026-09-23 (`docs/spec/changes/team-adapters/qa/REVISION_PR_17-19_20260923.md`).
- **Why:** The orchestrator's "Applies in" column, the management-adapters "Used by" column, the per-phase "Rules:" lines and README "Key rules" drift from what the skills actually cite; three notations for a status change and three spellings of the settings command. Generate them from citations and lint them (complements BL-10).
- **Status:** open

## BL-40 — Settings nudge and skills for Karvey repos that keep specs under `spec/` instead of `docs/spec/`
- **Origin:** change `team-adapters`, finding F-45 (emergent; source I-05), retroactive QA on 2026-09-23 (`docs/spec/changes/team-adapters/qa/REVISION_PR_17-19_20260923.md`).
- **Why:** `paautin-newcapital` and `onnet_ams` keep changes under `spec/changes/`; the hook looks only for `docs/spec/`. Either detect `spec/project.json` / `spec/changes/*/spec.json` or document `docs/spec/` as required and list the repos that must move.
- **Status:** open

## BL-41 — Statusline: keep the rotate warning visible on narrow terminals; recommend the copy-to-~/.claude install path
- **Origin:** change `team-adapters`, finding F-46 (emergent; source I-08), retroactive QA on 2026-09-23 (`docs/spec/changes/team-adapters/qa/REVISION_PR_17-19_20260923.md`).
- **Why:** The reset suffix made the line 34 characters longer (199 -> 233) and pushed "TIME TO ROTATE" from column 124 to 158, the part cut first on narrow terminals. Put the warning first or shorten the suffix; the README install path also pins `<version>`.
- **Status:** open

## BL-42 — Method page: alias table for the 12 anchors renamed after 3.10.0
- **Origin:** change `team-adapters`, finding F-47 (emergent; source I-09), retroactive QA on 2026-09-23 (`docs/spec/changes/team-adapters/qa/REVISION_PR_17-19_20260923.md`).
- **Why:** 12 of the 59 ids published in 3.10.0 (`organigrama`, `inicio`, `como`, `instalar`, `iteracion`, `reglas`, `versiones`, ...) no longer resolve; no file links to them. Add an alias table in `mapHash` or note the rename in the CHANGELOG.
- **Status:** open

## BL-43 — Notification deduplication: run id + timestamp in the payload; notify QA on first run and verdict changes
- **Origin:** change `team-adapters`, finding F-48 (emergent; source N-13), retroactive QA on 2026-09-23 (`docs/spec/changes/team-adapters/qa/REVISION_PR_17-19_20260923.md`).
- **Why:** Each micro-loop run and each deploy retry posts the full summary again; a noisy channel gets muted. Add `run`/`iteration` and `ts` to the payload; notify `qa` only on the first run and on verdict changes, or by option (`events: ["qa:verdict"]`).
- **Status:** open
