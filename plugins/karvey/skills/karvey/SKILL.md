---
name: karvey
description: Orquestador del Método Karvey — pipeline completo de spec-driven development (SDD), agnóstico de stack. Muestra el estado del pipeline, guía qué skill ejecutar en cada fase, y es el punto de entrada del método. Síntesis de experiencia propia + Kiro + gstack. Triggers include "karvey", "método karvey", "pipeline karvey", "qué sigue en karvey", "iniciar proyecto", "spec-driven", "spec driven development", "SDD", "specification-driven", "kiro", "cc-sdd", "openspec", "gstack", "g-stack", "Garry Tan", "spec kit", "PRD", "requirements engineering", "living specs", "método de desarrollo", "development pipeline", "SDLC", "desarrollo con IA", "agentic development", "equipo virtual de ingeniería", "vibe coding".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [<change-id>] [--phase <fase>] [--autoplan]
---

# Karvey — Orquestador del Método

> **Karvey** es una palabra **ona/selknam** que significa ***Afán***.
> Método de desarrollo de negocio **agnóstico de stack** (web, mobile/iOS/Android, desktop, CLI, API, embedded…). Creado por **Mauricio Quezada Ibáñez** (HainTech). Ver "Autoría, licencia y marca" al final.

## Propósito

Punto de entrada al Método Karvey. Muestra el pipeline completo, el estado actual de un cambio específico, y guía al ingeniero hacia el siguiente skill a ejecutar. Funciona para **cualquier stack**: el proyecto declara sus `targets` y cada fase se adapta (ver `rules/targets.md`).

## El Método Karvey

Karvey es un método de spec-driven development (SDD) para proyectos empresariales, **agnóstico de stack**. Combina:
- **Pre-spec interrogation** (estilo grill-me) + reframe "producto 10 estrellas": descubrir y mejorar qué se va a construir antes de especificar
- **PRD como base**: cada cambio nace de un Product Requirements Document (`prd.md`); los requirements EARS trazan a él
- **EARS requirements + living specs** (estilo openspec/kiro): especificaciones formales acumulativas
- **Mockup navegable** (con modo shotgun de variantes): validar UX antes de diseñar
- **Diseño gráfico sistémico** con scoring 0-10: colores OKLCH, tipografía, espaciado, por plataforma (WCAG/HIG/Material)
- **Arquitectura empresarial**: seguridad por capas Tiers 1–4, diagramas, edge cases, trust boundaries, infraestructura cloud
- **Infraestructura como código + CI/CD**: IaC y pipelines según nube y plataforma git, con revisión de seguridad
- **Tasks 10–30 min con IA** + gestión ClickUp o Markdown
- **Testing BD/Backend/Frontend + E2E** en el runtime real del target, con benchmark y regresión
- **QA 8 dimensiones**: incluye gate de seguridad bloqueante (OWASP+STRIDE), second opinion cross-model y auditoría visual
- **Despliegue ordenado**: branch por feature → dev → PR a master, gatillado por pipeline, con canary post-deploy
- **Versionado semver + CHANGELOG** por componente/repo, con trazabilidad humano + modelo IA
- **Goal persistente**: norte que cada fase relee para no detenerse hasta lograr el resultado, respetando los gates
- **Capa transversal de skills de apoyo** (investigate, second-opinion, health, browse, etc.) invocables en cualquier momento
- **Enforcement opcional por hooks** (git-flow + plan-gate) y **archive** con merge de specs

## Pipeline completo

```
FASE 0 ─── /karvey-grill          → Pre-spec + reframe 10-estrellas (+ plataforma/nube)
FASE 1 ─── /karvey-init           → change-id, project.json, prd.md, spec.json, Epic ClickUp
FASE 2 ─── /karvey-requirements   → EARS requirements (trazan al PRD), spec-delta, aprobación
FASE 3 ─── /karvey-mockup         → Navegable 3 niveles (+ modo shotgun de variantes)
FASE 4 ─── /karvey-design-graphic → Sistema visual OKLCH + scoring 0-10 por dimensión
FASE 5 ─── /karvey-architecture   → Arquitectura, Tiers, diagramas, edge cases, Infra Cloud
FASE 6 ─── /karvey-infra          → IaC + pipelines CI/CD + revisión de seguridad de infra
FASE 7 ─── /karvey-tasks          → Tasks 10–30 min, E{n}.F{n}.T{n}, sprint ClickUp
FASE 8 ─── /karvey-impl           → Implementación BD→Backend→Frontend, commits + CHANGELOG
FASE 9 ─── /karvey-test           → Unit + E2E en runtime real del target, benchmark, regresión
FASE 10 ── /karvey-qa             → QA 8D + gate de seguridad bloqueante, REVISION_PR
FASE 11 ── /karvey-deploy         → Despliegue ordenado feature→dev→PR master + canary
FASE 12 ── /karvey-archive        → Merge spec-deltas, retro, docs, cerrar Epic
```

## Capa transversal — skills de apoyo (invocables en cualquier momento)

No son fases; no avanzan `spec.json:phase`. Ver `rules/support-skills.md`.

```
/karvey-investigate        → Debugging root-cause (Iron Law: no fix sin investigar)
/karvey-second-opinion     → Review cross-model adversarial (Claude vs otro modelo)
/karvey-health             → Dashboard 0-10 (type/lint/tests/dead-code) + tendencia
/karvey-browse             → "Dar ojos": runtime real del target (browser/sim/CLI)
/karvey-checkpoint         → Guardar/restaurar estado de trabajo (handoff)
/karvey-diagram            → Texto → mermaid + excalidraw + SVG/PNG
/karvey-docs               → Diataxis + actualizar docs stale + PDF
/karvey-guard              → Instalar/quitar hooks de enforcement; edit-lock
/karvey-devex              → Review de onboarding/DX (time-to-hello-world)
/karvey-retro              → Retrospectiva (velocity, test health, por persona)
/karvey-scrape             → Extraer datos web + codificar como skill
/karvey-benchmark-models   → Comparar modelos (latencia/tokens/costo/calidad)
```

Vista de apoyo: `/karvey-context [--capability X] [--change Y]` → dashboard + cola de despliegue.

## Ejecución según argumento

### Sin argumentos — Mostrar el pipeline y contexto del proyecto

Mostrar el pipeline de arriba, luego ejecutar los pasos de `/karvey-context` (capabilities, cambios activos, archivados, sprint, cola de despliegue).

### Con `<change-id>` — Mostrar fase actual del cambio

```bash
cat docs/spec/changes/{change-id}/spec.json 2>/dev/null || echo "No encontrado"
```

Leer `spec.json` y determinar la fase actual según `phase` y `approvals`:

| `phase` | `approvals` | Siguiente skill |
|---------|-------------|-----------------|
| `init` | requirements.generated=false | `/karvey-requirements {change-id}` |
| `requirements` | requirements.approved=false | Aprobar requirements con el usuario |
| `requirements` | mockup.generated=false | `/karvey-mockup {change-id}` |
| `mockup` | mockup.approved=false | Iterar mockup con el usuario |
| `mockup` | design_graphic.generated=false | `/karvey-design-graphic {change-id}` |
| `design_graphic` | design_graphic.approved=false | Revisar diseño con el usuario |
| `design_graphic` | architecture.generated=false | `/karvey-architecture {change-id}` |
| `architecture` | architecture.approved=false | Revisar arquitectura con el usuario |
| `architecture` | infra.generated=false | `/karvey-infra {change-id}` |
| `infra` | infra.approved=false | Revisar infra/pipelines con el usuario |
| `infra` | tasks.generated=false | `/karvey-tasks {change-id}` |
| `tasks` | tasks.approved=false | Revisar tasks con el usuario |
| `tasks` | tasks.approved=true | `/karvey-impl {change-id}` |
| `impl` | — | `/karvey-test {change-id}` |
| `test` | — | `/karvey-qa {change-id}` |
| `qa` | qa.approved=false (críticos/altos abiertos) | Corregir → re-impl → re-test → re-qa |
| `qa` | qa.approved=true | `/karvey-deploy {change-id}` |
| `deployed` | — | `/karvey-archive {change-id}` |

Mostrar al usuario el estado (capability, fase, Tier, gestión, **goal**, aprobaciones incluyendo `infra`, `qa`, `deploy`) y el siguiente paso.

### Con `--phase <fase>` — Descripción detallada de una fase

Fases válidas: `grill`, `init`, `requirements`, `mockup`, `design-graphic`, `architecture`, `infra`, `tasks`, `impl`, `test`, `qa`, `deploy`, `archive`.

### Con `--autoplan` — Cadena de planificación

Ejecutar en secuencia las fases de planificación (0→5) encadenando aprobaciones, escalando al usuario solo las decisiones de fondo (taste, scope, seguridad). Inspirado en el `autoplan` de gstack. No salta los gates de aprobación; los agrupa.

---

## Descripción de cada fase

### FASE 0: /karvey-grill
Pre-spec interrogation + reframe "producto 10 estrellas" (opcional). Produce síntesis (insumo del PRD). Pregunta plataforma git, nube, IaC.

### FASE 1: /karvey-init
Crea/lee `docs/spec/project.json` (git, nube, IaC, knowledge_sync, targets, repos, spec_repo, branch_flow, enforcement). Captura el **goal**. Genera `change-id`, `prd.md`, `spec.json`. Epic ClickUp o `PLAN.md`.
**Reglas:** `project-config.md`, `clickup-protocol.md`, `living-specs.md`, `knowledge-sync.md`, `enforcement.md`

### FASE 2: /karvey-requirements
EARS requirements, cada uno **trazado a una sección del PRD**. `requirements.md`, `spec-delta.md`.
**Reglas:** `ears-format.md`, `living-specs.md`, `security-tiers.md`

### FASE 3: /karvey-mockup
Navegable 3 niveles, adaptado al target. Modo shotgun (N variantes + board). `mockup.html` (o equivalente del target).

### FASE 4: /karvey-design-graphic
Sistema OKLCH + scoring 0-10 por dimensión (qué sería un 10). Guía por plataforma (WCAG/HIG/Material). `design-spec.md`.

### FASE 5: /karvey-architecture
Boundaries, seguridad por Tier, diagramas (mermaid), edge cases, trust boundaries, plan de cobertura de tests, sección **Infraestructura Cloud**. `architecture.md`.
**Reglas:** `security-tiers.md`

### FASE 6: /karvey-infra
IaC (Terraform/Bicep/Pulumi) + pipelines CI/CD (GitHub Actions/Azure Pipelines) idempotentes + auto-detección de plataforma + revisión de seguridad de infra. `infra.md`.
**Reglas:** `project-config.md`, `deploy-workflow.md`, `security-tiers.md`, `changelog-policy.md`

### FASE 7: /karvey-tasks
Tasks 10–30 min, `E{n}.F{n}.T{n} [BD/Backend/Frontend/Infra]`. Lee `architecture.md` + `infra.md`. `tasks.md`.
**Reglas:** `clickup-protocol.md`

### FASE 8: /karvey-impl
Ejecuta tasks en `feature/{change-id}` (nunca dev/master). Bump versión + CHANGELOG por commit (humano + modelo IA + por qué).
**Reglas:** `deploy-workflow.md`, `changelog-policy.md`, `versioning.md`

### FASE 9: /karvey-test
Unit + E2E en el **runtime real del target**, benchmark de performance, regression tests. `test_evidence.md`.
**Reglas:** `targets.md`

### FASE 10: /karvey-qa
QA 8 dimensiones: Seguridad (gate bloqueante, OWASP+STRIDE), Errores, Consistencia, Impacto, Env vars, Versionamiento (CHANGELOG), Second-opinion cross-model, Auditoría visual. `REVISION_PR_{n}_{date}.md`.
**Reglas:** `changelog-policy.md`, `versioning.md`

### FASE 11: /karvey-deploy
Flujo ordenado por repo: pull → feature → pull → merge dev (pipeline DEV) → canary → pull → PR dev→master (PROD con OK humano) → canary. Bump semver + CHANGELOG por componente/repo. Versión visible en front (recomendado). Nunca deploy manual.
**Reglas:** `deploy-workflow.md`, `versioning.md`, `changelog-policy.md`, `project-config.md`

### FASE 12: /karvey-archive
Merge spec-deltas en living specs, archiva, cierra Epic. Opcional recomendado: `/karvey-retro` + `/karvey-docs`.

---

## Estructura de directorios del método

`docs/spec/` vive en el **repo principal** del proyecto (`spec_repo`). Un proyecto tiene 1 o más repos, nunca cero.

```
docs/spec/
├── project.json                       ← Config (git, nube, IaC, targets, knowledge_sync, repos, enforcement)
├── specs/{capability}/spec.md         ← Living specs (acumulativas por capability)
└── changes/{change-id}/
    ├── spec.json                      ← Metadatos, fase, aprobaciones, goal
    ├── prd.md                         ← Product Requirements Document
    ├── requirements.md                ← EARS (trazan al PRD)
    ├── spec-delta.md  · mockup.* · design-spec.md
    ├── architecture.md                ← + Infraestructura Cloud
    ├── infra.md  · tasks.md  · checkpoint.md
    ├── PLAN.md (si markdown)  · IMPLEMENTED
    └── archive/{YYYY-MM-DD}-{change-id}/
```

El código (incl. IaC y pipelines), `CHANGELOG.md` por componente/repo, y los hooks de `settings.json` viven en cada repo de `project.json:repos`.

## Reglas compartidas

| Archivo | Aplica en |
|---------|-----------|
| `rules/project-config.md` | init, architecture, infra, deploy, context |
| `rules/clickup-protocol.md` | init, tasks, impl, qa, deploy, archive |
| `rules/ears-format.md` | requirements |
| `rules/security-tiers.md` | requirements, architecture, infra, qa |
| `rules/living-specs.md` | init, requirements, archive |
| `rules/knowledge-sync.md` | todas las fases (al cierre) |
| `rules/targets.md` | mockup, design-graphic, architecture, test, qa, deploy |
| `rules/deploy-workflow.md` | infra, impl, deploy |
| `rules/changelog-policy.md` | impl, infra, deploy, qa |
| `rules/versioning.md` | impl, deploy, qa |
| `rules/enforcement.md` | init, guard |
| `rules/support-skills.md` | capa transversal |

## Si vienes de Kiro o gstack — equivalencias

Karvey absorbe el valor de ambos. Lo que en gstack son comandos sueltos, acá está en **fase** o en la **capa transversal**.

| Kiro / gstack | En Karvey |
|---------------|-----------|
| kiro `/spec`, `/kiro-spec-*` | grill + PRD + requirements EARS (FASE 0–2) |
| office-hours, plan-ceo-review | reframe 10-estrellas en `karvey-grill` |
| plan-design-review, design-consultation, design-shotgun | `karvey-design-graphic` + `karvey-mockup` (shotgun) |
| plan-eng-review, diagram | `karvey-architecture` + `karvey-diagram` |
| setup-deploy | `karvey-infra` (auto-detección plataforma) |
| review, cso (OWASP+STRIDE), codex, design-review | `karvey-qa` (8 dim) + `karvey-second-opinion` |
| qa, browse, benchmark | `karvey-test` + `karvey-browse` + `karvey-health` |
| ship, land-and-deploy, canary | `karvey-deploy` |
| investigate | `karvey-investigate` |
| health | `karvey-health` |
| context-save/restore | `karvey-checkpoint` |
| document-generate/release, make-pdf | `karvey-docs` |
| retro | `karvey-retro` / FASE 12 |
| learn, gbrain | `knowledge-sync` (graphify/obsidian) |
| careful, freeze, guard | `karvey-guard` + hooks de `enforcement.md` |
| devex-review | `karvey-devex` |
| scrape, skillify | `karvey-scrape` |
| benchmark-models | `karvey-benchmark-models` |
| ios-qa, ios-fix, ios-design-review | generalizado vía `targets.md` (runtime real por target) |

N/A (propietario de gstack, con equivalente genérico): `open-gstack-browser` → runtime de `karvey-browse`; `gstack-upgrade` → N/A; `pair-agent`/`gbrain` → `knowledge-sync`.

## Comandos de referencia rápida

```
/karvey [<change-id>] [--phase <f>] [--autoplan]   → Estado / pipeline / planificación encadenada
/karvey-context                                     → Dashboard + cola de despliegue
Fases:  grill init requirements mockup design-graphic architecture infra
        tasks impl test qa deploy archive
Apoyo:  investigate second-opinion health browse checkpoint diagram
        docs guard devex retro scrape benchmark-models
```

---

## Autoría, licencia y marca

- **Etimología:** *Karvey* es una palabra **ona/selknam** que significa ***Afán***.
- **Autor:** Modelo de desarrollo de negocio creado por **Mauricio Quezada Ibáñez**, **HainTech**. Propiedad de HainTech.
- **Licencia:** **Apache License 2.0** — ver `LICENSE` y `NOTICE`. Cualquiera puede usar, modificar y adaptar (incl. comercial) respetando la licencia.
- **Marca:** "Karvey" y la convención `karvey-*` son marca de HainTech. Adaptaciones permitidas con atribución; ver `TRADEMARK.md`.
- **Créditos / inspiración:** Karvey sintetiza la **experiencia propia** de Mauricio Quezada Ibáñez (HainTech) con ideas conceptuales de **Kiro** (spec-driven / cc-sdd) y **gstack** (Garry Tan). Es síntesis e inspiración conceptual; **no incorpora código** de esos proyectos.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
