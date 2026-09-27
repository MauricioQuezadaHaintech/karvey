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
| BL-44 | 2026-09-24 | wave1-hardening / F-26 | spec-gap (deferred) | low | Cross-repo decision refs (`D-12@{ops-repo}`) rejected by spec.schema.json | open | — | — |
| BL-45 | 2026-09-24 | wave1-hardening / F-27 | spec-gap (deferred) | low | Time-entry / worklog operation in management-adapters.md | open | — | — |
| BL-46 | 2026-09-24 | wave1-hardening / F-28 | spec-gap (deferred) | low | `approvals.deploy`: a write path or drop the key | open | — | — |
| BL-47 | 2026-09-24 | wave1-hardening / F-29 | spec-gap (deferred) | low | Where the prod OK D-NN is written during deploy (D-03 vs a commit on a branch) | open | — | — |
| BL-48 | 2026-09-24 | wave1-hardening / F-30 | spec-gap (deferred) | low | Release ledger is clone-local: `advance deployed` / `--write-spec` need the same clone | open | — | — |
| BL-49 | 2026-09-24 | wave1-hardening / F-31 | spec-gap (deferred) | low | karvey-import cannot resume at the furthest phase the content supports | open | — | — |
| BL-50 | 2026-09-24 | wave1-hardening / F-32 | spec-gap (deferred) | low | Per-period decision logs vs the single `docs/spec/decisions.md` path (L-30) | open | — | — |
| BL-51 | 2026-09-25 | project-upgrade / owner request (D-20) | emergent | med | Project upgrade plan after each plugin update; the statusline stable-launcher item folds in | in change `project-upgrade` | D-20 | — |
| BL-52 | 2026-09-25 | wave1-hardening / F-54 | spec-gap (deferred) | low | `spec.json:clickup.feature_ids` is an array; tracker ids should be keyed by natural key like `task_ids` | routed to change `wave2-structural` | — | wave2-structural |
| BL-53 | 2026-09-25 | wave1-hardening / F-87, F-88 | spec-gap (deferred) | med | Text cleanup after wave1: method page hooks section, stale rule/skill sentences, footers, env vars in hooks/README, repo-specific ids in method text | open | — | — |
| BL-54 | 2026-09-25 | wave1-hardening / F-78 | spec-gap (deferred) | med | plan-gate write classes: cp/mv/dd/curl -o/git apply/rm -f | open | — | — |
| BL-55 | 2026-09-25 | wave1-hardening / F-80 | spec-gap (deferred) | low | prod-gate: no-python HEAD/@ on production; production set when no main/master ref exists | open | — | — |
| BL-56 | 2026-09-25 | wave1-hardening / F-81 | spec-gap (deferred) | med | Approval vocabulary on affirmative statements; pending-sync and spec-write noise on legacy repos | open | — | — |
| BL-57 | 2026-09-25 | wave1-hardening / F-82 | emergent | low | Statusline outside the plugin and token-threshold env vars under percent thresholds | open | — | — |
| BL-58 | 2026-09-25 | wave1-hardening / F-83, F-55 | spec-gap (deferred) | med | Hook latency over the §9 budget; no-python git-flow compatibility with the 3.11 template | open | — | — |
| BL-59 | 2026-09-25 | wave1-hardening / F-84 | spec-gap (deferred) | med | spec-merge item format: blank lines inside an item, `### REQ-` headings in ADDED | open | — | — |
| BL-60 | 2026-09-25 | wave1-hardening / F-85 | spec-gap (deferred) | med | project.json ban line in every skill that dispatches subagents | open | — | — |
| BL-61 | 2026-09-25 | wave1-hardening / F-86 | emergent | low | Factor duplicated helpers (now_iso, parse_dt, git) and the TTL literals into karvey_lib | open | — | — |
| BL-62 | 2026-09-26 | wave1-hardening / F-90 | spec-gap (deferred) | med | Bind the human's prod OK to the commit at the approval hook; close the check-to-run window | open | — | — |
| BL-63 | 2026-09-26 | wave1-hardening / F-91 | spec-gap (deferred) | low | A reopen from `deploying` (D-36 in the documented flow) | open | — | — |
| BL-64 | 2026-09-26 | peer session report (3.12.0 in use) | emergent | med | protect-paths blocks a read-only `ls` of the plan-approval marker glob | open | — | — |
| BL-65 | 2026-09-26 | project-upgrade / F-29 | emergent | low | Duplicated git helpers across `project`, `karvey_hooks` and `upgrade` | open | — | — |
| BL-66 | 2026-09-26 | project-upgrade / F-04 | emergent | low | Re-record the upgrade-surface fingerprint at the release that ships `project-upgrade` | open | — | — |

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

## BL-44 — Cross-repo decision refs (`D-12@{ops-repo}`) rejected by spec.schema.json
- **Origin:** change `wave1-hardening`, finding F-26 (spec-gap, low), deferred to Wave 2 by D-17 («Sí, todas (Recomendado)»).
- **Why:** `spec.schema.json` accepts only `^[DC]-\d+$` in `decisions`, while `rules/multi-agent.md` §2 prescribes cross-repo references as `"D-12@{ops-repo}"`: a decision cited the way the rule says fails validation. The karvey-init example now uses `"D-NN"`; the schema pattern or the rule must change. Also cosmetic: `karvey-state.py next` prints the blocker line twice. (E1.F12.T3)
- **Status:** open

## BL-45 — Time-entry / worklog operation in management-adapters.md
- **Origin:** change `wave1-hardening`, finding F-27 (spec-gap, low), deferred to Wave 2 by D-17 («Sí, todas (Recomendado)»).
- **Why:** `rules/management-adapters.md` has no time-entry / worklog operation, so karvey-impl can only say "record the actual as a time entry where the tool has one, else the PLAN.md actual columns" — prose, not an adapter call (REQ-W1-042). The adapter should list a `log_time` operation per tool (ClickUp time entry, Jira worklog, …) with `none` for tools that have none. (E1.F12.T5)
- **Status:** open

## BL-46 — `approvals.deploy`: a write path or drop the key
- **Origin:** change `wave1-hardening`, finding F-28 (spec-gap, low), deferred to Wave 2 by D-17 («Sí, todas (Recomendado)»).
- **Why:** `approvals.deploy` has no write path: Wave 1 does not use it as a precondition (state-machine.json), so the rewritten karvey-deploy no longer records it. Architecture should say whether deploy ever runs `approve {id} deploy`, or drop the key. (E1.F12.T6)
- **Status:** open

## BL-47 — Where the prod OK D-NN is written during deploy (D-03 vs a commit on a branch)
- **Origin:** change `wave1-hardening`, finding F-29 (spec-gap, low), deferred to Wave 2 by D-17 («Sí, todas (Recomendado)»).
- **Why:** D-03 puts the prod OK "in the decision log", but writing `decisions.md` during deploy is a commit on some branch. The rewritten deploy keeps the D-NN text in the PR body and archive writes it into `decisions.md` on `chore/archive-{id}`; D-03 / `deploy-workflow.md` should state that order. (E1.F12.T6)
- **Status:** open

## BL-48 — Release ledger is clone-local: `advance deployed` / `--write-spec` need the same clone
- **Origin:** change `wave1-hardening`, finding F-30 (spec-gap, low), deferred to Wave 2 by D-17 («Sí, todas (Recomendado)»).
- **Why:** The release ledger lives under the local `<git-common-dir>/karvey/`, so `advance {id} deployed` and `approve {id} prod --write-spec` at archive work only in the clone where deploy recorded it. `approve --write-spec` can fall back to a D-NN / PR URL; `advance deployed` has no fallback and requires the ledger. Needs a decision (e.g. `advance deployed --ref D-NN --pipeline-run URL` accepted when the ledger is absent). (E1.F12.T6)
- **Status:** open

## BL-49 — karvey-import cannot resume at the furthest phase the content supports
- **Origin:** change `wave1-hardening`, finding F-31 (spec-gap, low), deferred to Wave 2 by D-17 («Sí, todas (Recomendado)»).
- **Why:** karvey-import can no longer resume "at the furthest phase the content supports": `karvey-state.py advance` refuses to pass an unapproved gate and imported gates are unapproved by design, so an import resumes at `requirements` and walks the gates in order. Either accept that (current text) or add an import path that records the imported artifacts as `generated` and asks the human per gate. (E1.F12.T7)
- **Status:** open

## BL-50 — Per-period decision logs vs the single `docs/spec/decisions.md` path (L-30)
- **Origin:** change `wave1-hardening`, finding F-32 (spec-gap, low), deferred to Wave 2 by D-17 («Sí, todas (Recomendado)»).
- **Why:** One decision-log path (L-30): karvey-decisions described one file per period under `{ops_repo}/decisions/`, multi-agent.md named `docs/decisiones.md`; both now say `{ops_repo}/docs/spec/decisions.md` (the shape this repo uses). A project keeping per-period files needs a migration note; architecture §8 does not say which shape wins. (E1.F12.T7)
- **Status:** open

## BL-51 — Project upgrade plan after each plugin update (D-20)
- **Origin:** owner request 2026-09-25 (D-20); the statusline stable-launcher item (README suggests a versioned plugin path for the statusline, which goes stale on the next update) folds in.
- **Why:** updating the plugin never brings an existing project up to the new method (legacy shapes, copied hook shims, versioned statusline path, new standards). Routed to change `project-upgrade` (REQ-UP-001..032).
- **Status:** in change `project-upgrade`

## BL-52 — `clickup.feature_ids` keyed by natural key, like `task_ids`
- **Origin:** change `wave1-hardening`, finding F-54 (spec-gap, low), seen during the E1.F17.T3 manual scripts
  (`find-or-create`, `missing-status-map`); not an Expected line of any script, so not fixed in Wave 1.
- **Why:** `spec.schema.json` types `clickup.feature_ids` as an array while `task_ids` is a map keyed by natural key, and
  `management-adapters.md` stores every tracker id by its natural key for find-or-create. With an array a Feature id
  loses its key `E{n}.F{n}`; an agent that wrote the keyed form had to rewrite it as an array to pass `validate`.
  Decide the shape: a keyed map `{"E1.F1": "<id>"}`, with the array kept as a legacy warning and migrated by
  `validate --fix`.
- **Scope:** schema, `validate --fix` migration, the find-or-create text in `management-adapters.md` / `karvey-tasks`.
- **Status:** routed to change `wave2-structural`

## BL-53 — Text cleanup after wave1: method page hooks section, stale rule/skill sentences, footers, env vars in hooks/README, repo-specific ids in method text
- **Origin:** change `wave1-hardening`, QA finding F-87, F-88 (spec-gap (deferred)), deferred: out of the fix scope of the QA micro-loop.
- **Why:** Text out of date with the code: `docs/karvey.html` hooks section still describes the 3.11 model (settings.json, `--override`, no prod-gate/protect-paths/approval hook/subagent-prompt) and fixed token thresholds; `karvey-checkpoint` says a committed `state.json` costs a drift line (BUG-22 says not); `multi-agent.md` says expiring markers belong to the user's hooks; half-fixed LICENSE footers; no pending-sync row in the enforcement switches table; §3.5 wording on main/master; `karvey-guard` shim text; `KARVEY_HOOK_SELFTEST` / `KARVEY_DEFAULTS_JSON` undocumented in `hooks/README.md`. Page audit (D8) was static only: no design-spec for this change and no browser on the review host. Method text cites this repository's own decision/incident ids (D-01, D-02, D-10, D-16, BUG-25, H-10 …) in `rules/enforcement.md`, `hooks/README.md` and several skills; they mean nothing to an adopting team (company-neutral method).
- **Status:** open

## BL-54 — plan-gate write classes: cp/mv/dd/curl -o/git apply/rm -f
- **Origin:** change `wave1-hardening`, QA finding F-78 (spec-gap (deferred)), deferred: out of the fix scope of the QA micro-loop.
- **Why:** plan-gate (opt-in) does not class `cp`/`mv`/`dd of=`/`curl -o`/`git apply`/`rm -f` as writes; §3.4 lists only redirections and `tee`.
- **Status:** open

## BL-55 — prod-gate: no-python HEAD/@ on production; production set when no main/master ref exists
- **Origin:** change `wave1-hardening`, QA finding F-80 (spec-gap (deferred)), deferred: out of the fix scope of the QA micro-loop.
- **Why:** No-python prod-gate: `git push origin HEAD` / `@` on the production branch pass (HEAD counts as a refspec); with python, a project without `branch_flow` and with no `origin/master`/`origin/main` ref lets `git push origin master` through (the set holds only existing names).
- **Status:** open

## BL-56 — Approval vocabulary on affirmative statements; pending-sync and spec-write noise on legacy repos
- **Origin:** change `wave1-hardening`, QA finding F-81 (spec-gap (deferred)), deferred: out of the fix scope of the QA micro-loop.
- **Why:** Approval vocabulary: "Sí, eso es lo que falla en prod" records a prod marker (an affirmative statement, not an approval); pending-sync leaves an untracked `docs/spec/.graph-pending` in legacy repos even with `knowledge_sync: none`; the advisory spec-write validator exits 2 on every save of an archived legacy spec with undated approvals.
- **Status:** open

## BL-57 — Statusline outside the plugin and token-threshold env vars under percent thresholds
- **Origin:** change `wave1-hardening`, QA finding F-82 (emergent), deferred: out of the fix scope of the QA micro-loop.
- **Why:** Statusline: a copy of the script outside the plugin cannot find `defaults.json` and shows `rot?` without warnings (by design, BUG-08 family); `KARVEY_ROTATE_CTX_YELLOW/RED` token thresholds are ignored when the window size is known (D-18 percent thresholds) and the CHANGELOG does not say so.
- **Status:** open

## BL-58 — Hook latency over the §9 budget; no-python git-flow compatibility with the 3.11 template
- **Origin:** change `wave1-hardening`, QA finding F-83, F-55 (spec-gap (deferred)), deferred: out of the fix scope of the QA micro-loop.
- **Why:** Without python, an enabled git-flow blocks every `git commit`/`git push` (documented fail mode, §3.2) where the 3.11 template needed no python; 10 known projects enable it. Dispatcher latency 135–167 ms median, over the §9 p95 150 ms budget; `find_python` spends 30–50 ms starting a second interpreter for the version check. Benchmark (F-55): pre-bash median 128–148 ms against the 88 ms phase-1 baseline.
- **Status:** open

## BL-59 — spec-merge item format: blank lines inside an item, `### REQ-` headings in ADDED
- **Origin:** change `wave1-hardening`, QA finding F-84 (spec-gap (deferred)), deferred: out of the fix scope of the QA micro-loop.
- **Why:** spec-merge: `read_item` stops at the first blank line (a MODIFIED item with an indented Scenario after a blank line keeps the old scenario), and an ADDED section written as `### REQ-…` headings reports "already up to date" with exit 0; the delta item format is not specified in karvey-requirements.
- **Status:** open

## BL-60 — project.json ban line in every skill that dispatches subagents
- **Origin:** change `wave1-hardening`, QA finding F-85 (spec-gap (deferred)), deferred: out of the fix scope of the QA micro-loop.
- **Why:** Only karvey-impl carries the `project.json` ban line in the subagent prompts it composes; karvey-qa, -architecture, -requirements, -infra and -standards dispatch subagents without it, although `management-adapters.md` rule 5 requires it everywhere. The subagent-prompt guard backstops it.
- **Status:** open

## BL-61 — Factor duplicated helpers (now_iso, parse_dt, git) and the TTL literals into karvey_lib
- **Origin:** change `wave1-hardening`, QA finding F-86 (emergent), deferred: out of the fix scope of the QA micro-loop.
- **Why:** Duplicated helpers (`now_iso` ×3, `parse_dt` ×2 disagreeing on fractional seconds on Python 3.9/3.10, `git()` ×2, an unreachable inline copy of `profile_only_since` in the session hook's no-python branch) and the plan-marker TTL values written in three places.
- **Status:** open

## BL-62 — Bind the human's prod OK to the commit at the approval hook; close the check-to-run window
- **Origin:** change `wave1-hardening`, QA re-run finding F-90 (spec-gap (deferred)); needs the owner's decision.
- **Why:** `approve … prod --sha` records the commit the agent names; neither the marker nor its audit line ties the human's words to a commit, so the agent can pick any existing commit (D-35 says "the head shown when the owner approved"). Candidate: the approval hook stores the SHAs written in the human's message (or the local HEAD at prompt time) in the marker and its audit line, and `approve --sha` must match one of them. Related residual: a writer started in an earlier tool call can move the pushed ref in the milliseconds between the gate's check and the push; `gh pr merge --match-head-commit` or a push by explicit SHA closes it.
- **Status:** open

## BL-63 — A reopen from `deploying` (D-36 in the documented flow)
- **Origin:** change `wave1-hardening`, QA re-run finding F-91 (spec-gap (deferred)).
- **Why:** The deploy skill records the prod approval in `deploying`, where `reopen` is refused ("allowed up to qa"), so D-36 only supersedes approvals recorded earlier. The SHA binding and the 24 h expiry limit the damage (a rework is a new commit and needs a new OK). Decide whether a spec-gap found in `deploying` reopens (and supersedes), or whether `approve prod` is restricted to `deploying` and documented as such.
- **Status:** open

## BL-64 — protect-paths blocks a read-only `ls` of the plan-approval marker glob
- **Origin:** observed by a peer session on 2026-09-26 with 3.12.0 installed.
- **Why:** a read-only `ls /tmp/claude-plan-approved-*` was BLOCKED by protect-paths. Listing is not a write; the guard should let read-only commands (the `READ_ONLY` set) list or stat the marker paths and still refuse creating, touching or removing them. Needs a table case (read-only glob over the marker → allow) and a check that the BUG-27 glob rule is not what trips it.
- **Status:** open

## BL-65 — Duplicated git helpers across `project`, `karvey_hooks` and `upgrade`
- **Origin:** change `project-upgrade`, QA finding F-29 (emergent), deferred: a refactor of shared git helpers touches guard code outside that change's risk budget.
- **Why:** `current_branch` / `_origin_head` are copies of `project` / `karvey_hooks`; four git runners with different error handling; two path normalisers; the release-number check repeated four times. No behaviour defect. Related to BL-61 (helpers in `karvey_lib`); do them together.
- **Status:** open

## BL-66 — Re-record the upgrade-surface fingerprint at the release that ships `project-upgrade`
- **Origin:** change `project-upgrade`, finding F-04 (emergent), deferred: a release action, not code of that change.
- **Why:** `upgrade-surface.json` is recorded for 3.11.4. With 3.12.0 released first, the merge of `project-upgrade` must re-record the fingerprint from the 3.12.0 tree (not `surface --write` on the merged tree, which would hide that change's own surface edits from the release check); otherwise L-37 errors (top release newer than the fingerprint). Owner of the step: `karvey-deploy` of the release that ships it.
- **Status:** open
