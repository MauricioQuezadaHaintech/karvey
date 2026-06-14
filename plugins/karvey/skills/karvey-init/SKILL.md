---
name: karvey-init
description: Initialize a new Karvey spec. Creates the directory structure, spec.json, and registers the Epic in ClickUp (or PLAN.md if not using ClickUp). Use after karvey-grill or when starting a new feature. Triggers include "karvey init", "iniciar spec", "nueva feature", "nuevo cambio", "spec-driven", "SDD", "kiro", "cc-sdd", "gstack", "Garry Tan", "PRD", "iniciar proyecto spec-driven", "nuevo método", "scaffolding".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id> [--capability <nombre>]
---

# Karvey Init

## Propósito

Inicializar la estructura de una nueva especificación y registrar el Epic en el sistema de gestión (ClickUp o Markdown).

## Pasos de ejecución

### Paso 1 — Verificar contexto pre-spec

Si existe un resumen de `karvey-grill` en la conversación, usarlo para pre-poblar los campos.
Si no, pedir al usuario: "Describí brevemente el problema que resuelve este cambio."

### Paso 2 — Generar change-id

Si `$ARGUMENTS` incluye el change-id, usarlo. Si no, generarlo desde la descripción:
- Formato: `{add|fix|update|remove}-{nombre-descriptivo-url-safe}`
- Ejemplos: `add-call-transfer`, `fix-webhook-retry`, `update-tenant-config`
- Verificar que no exista en `docs/spec/changes/`: `find docs/spec/changes -maxdepth 1 -type d -name "{change-id}"`
- Si existe conflicto, agregar sufijo numérico: `add-call-transfer-2`

### Paso 3 — Config del proyecto (project.json)

Verificar si existe `docs/spec/project.json`.

**Si YA existe:** leerlo y reutilizar sus valores. No volver a preguntar nada de esta config.

**Si NO existe:** crearlo. Pre-poblar desde la síntesis de `karvey-grill` si está disponible en la conversación; preguntar o inferir los campos faltantes. El esquema completo está en `karvey/rules/project-config.md` (citar esa regla). Campos:

- **`git_platform`**: `github` | `azure_devops`.
- **`cloud.provider`**: `azure` | `gcp` | `aws` | `mixed` | `none`.
- **`iac_tool`**: `terraform` | `bicep` | `pulumi` | `none`.
- **`knowledge_sync`**: decidir según `karvey/rules/knowledge-sync.md` — si hay un MCP de Obsidian disponible en la sesión → `"obsidian"`; si no → `"graphify"`.
- **`repos`**: arreglo de repos del proyecto. MÍNIMO 1 elemento, nunca vacío.
- **`spec_repo`**: si `repos` tiene 1 → ese mismo; si hay varios → preguntar cuál es el repo principal donde vive `docs/spec/`.
- **`branch_flow`**: por defecto `{ "feature_prefix": "feature/", "integration": "dev", "production": "master" }`.

Escribir `docs/spec/project.json` con estos valores (ver esquema en `karvey/rules/project-config.md`).

### Paso 3.5 — Enforcement opt-in (hooks)

Después de crear `project.json`, preguntar al usuario si quiere activar los **hooks de enforcement** del método Karvey. Ver detalle en `karvey/rules/enforcement.md`.

```
¿Querés activar los hooks de enforcement de Karvey? (OPT-IN, podés activarlos después)
  - git-flow hook: bloquea commits directos a las ramas de integración/producción y fuerza el flujo de feature branches (lee branch_flow).
  - plan-gate hook: bloquea modificaciones sin plan aprobado.
```

**Si acepta** uno o ambos: marcar en `project.json` el bloque `enforcement`:
```json
"enforcement": {
  "git_flow_hook": true,
  "plan_gate_hook": true
}
```
(poner `true` solo en los que el usuario aceptó). Indicar al usuario que los hooks se instalan ejecutando:
```
/karvey-guard --install
```
`karvey-guard --install` escribe los hooks en el `settings.json` del proyecto leyendo `branch_flow` de `project.json`.

**Si NO acepta:** dejar ambos flags en `false`. El enforcement es OPT-IN — nunca forzarlo.
```json
"enforcement": {
  "git_flow_hook": false,
  "plan_gate_hook": false
}
```

### Paso 4 — Preguntar sistema de gestión

```
¿Este proyecto usa ClickUp para gestión?
```

**Si SÍ (ClickUp):**
- Preguntar: ¿A qué proyecto/backlog pertenece? (obtener el `backlog_list_id` de ClickUp)
- Leer regla: `rules/clickup-protocol.md`

**Si NO (Markdown):**
- Se creará `PLAN.md` en el directorio del cambio
- No se requiere ninguna configuración adicional

### Paso 5 — Recopilar metadata

Preguntar (o inferir del contexto pre-spec):

1. **Capability**: dominio funcional al que pertenece (ej: `call-management`, `authentication`, `notifications`). Si no existe en `docs/spec/specs/`, se creará.
2. **Security Tier**: 1-4. Leer `rules/security-tiers.md` para orientar al usuario.
3. **Capas involucradas**: BD / Backend / Frontend / Infra (puede ser múltiple)
4. **Descripción breve**: 1-2 líneas del problema que resuelve
5. **Goal (norte del cambio)**: el objetivo concreto que se busca lograr — qué resultado, observable y verificable, define el éxito de este cambio. Preguntar: "¿Cuál es el norte de este cambio? ¿Qué resultado concreto queremos lograr?". Guardarlo tal cual en `spec.json` (`goal`) y reflejarlo como sección destacada en `prd.md`.

> **Nota — el goal da persistencia.** El `goal` queda como norte del cambio en todas las fases: cada fase Karvey lo relee al iniciar para perseguir el resultado sin detenerse hasta lograrlo, respetando siempre los gates de plan y seguridad.

### Paso 6 — Crear estructura de directorios

```bash
mkdir -p docs/spec/changes/{change-id}/specs/{capability}
mkdir -p docs/spec/specs/{capability}  # si no existe
```

Si `docs/spec/specs/{capability}/spec.md` no existe, crearlo:
```markdown
# Spec: {Capability}

<!-- Living spec del capability {capability}. Se actualiza al archivar cada cambio. -->
```

### Paso 7 — Crear spec.json

Escribir `docs/spec/changes/{change-id}/spec.json` con:
```json
{
  "change_id": "{change-id}",
  "capability": "{capability}",
  "description": "{descripción breve}",
  "goal": "{norte del cambio: resultado concreto y verificable que define el éxito}",
  "layers": ["{BD|Backend|Frontend|Infra}"],
  "created_at": "{ISO timestamp}",
  "updated_at": "{ISO timestamp}",
  "language": "es",
  "management": "{clickup|markdown}",
  "security_tier": {1-4},
  "phase": "init",
  "clickup": {
    "epic_id": "",
    "feature_ids": [],
    "backlog_list_id": "{list_id o vacío}",
    "client_tag": "{tag o vacío}"
  },
  "approvals": {
    "requirements": { "generated": false, "approved": false },
    "mockup": { "generated": false, "approved": false },
    "design_graphic": { "generated": false, "approved": false },
    "architecture": { "generated": false, "approved": false },
    "tasks": { "generated": false, "approved": false },
    "infra": { "generated": false, "approved": false },
    "qa": { "generated": false, "approved": false },
    "deploy": { "generated": false, "approved": false }
  }
}
```

### Paso 8 — Crear prd.md

Escribir `docs/spec/changes/{change-id}/prd.md` (Product Requirements Document formal):
```markdown
# PRD: {change-id}

## Resumen ejecutivo
{síntesis de 2-3 líneas: qué se construye y para qué}

## 🎯 Goal (norte del cambio)
> {resultado concreto y verificable que define el éxito de este cambio}

Este goal es el norte que persiguen todas las fases Karvey: cada fase lo relee al iniciar para avanzar hacia el resultado sin detenerse hasta lograrlo, respetando los gates de plan y seguridad.

## Problema y contexto
- **Quién lo tiene:** {usuarios/roles afectados}
- **Situación actual:** {cómo se resuelve hoy o por qué duele}
- **Impacto:** {costo de no resolverlo}

## Objetivos y métricas de éxito
{objetivos medibles, p.ej. "reducir X de N a M", "habilitar Y para Z usuarios"}

## User stories / casos de uso principales
- Como {rol}, quiero {acción} para {beneficio}.
- {…}

## Alcance (in scope)
- {qué SÍ entra en este cambio}

## Fuera de alcance (out of scope)
- {qué NO entra y por qué}

## Stakeholders
{quién pide, quién aprueba, quién se ve impactado}

## Restricciones
- Security Tier: {N} — {justificación}
- Dependencias previas: {lista}

## Criterios de aceptación
{condiciones verificables para dar el cambio por completo}
```

### Paso 9A — Crear Epic en ClickUp (si management=clickup)

Leer credenciales de `.connections.json` (ver `rules/clickup-protocol.md`). Si no existe, crearlo y agregarlo al `.gitignore` antes de continuar.
Determinar el próximo número de Epic buscando en ClickUp:
```
clickup_search
  keywords: "E{1..99}"
  filters.location.categories: ["{backlog_list_id}"]
```

Crear Epic:
```
clickup_create_task
  name: "E{n} {Nombre del Epic}"
  list_id: "{backlog_list_id}"
  task_type: "Epic"
  description: (ver formato en reglas)
  tags: ["{client_tag}"]
```

Actualizar `spec.json` con `clickup.epic_id`.

Formato de descripción del Epic:
```
E{n}: {Nombre del Epic}

Definición:
{descripción de 2-3 párrafos: qué problema resuelve, para quién, por qué es importante}

Valor Estratégico:
{impacto en el negocio}

Security Tier: {N} — {justificación}

Decisiones de Diseño:
(pendiente — se completa en karvey-architecture)

Features:
(pendiente — se completa en karvey-requirements)

Realizado con Método Karvey
```

### Paso 9B — Crear PLAN.md (si management=markdown)

Escribir `docs/spec/changes/{change-id}/PLAN.md`:
```markdown
# Plan: {change-id}

**Capability:** {capability} | **Security Tier:** {N} | **Capas:** {lista}
**Creado:** {fecha} | **Estado:** 🟡 En progreso

---

## Epic: {Nombre}

### Descripción
{problema, quién, impacto}

### Valor estratégico
{impacto en el negocio}

### Decisiones de diseño
| Tema | Decisión |
|------|----------|
| (pendiente — karvey-architecture) | |

---

## Features
(pendiente — karvey-requirements)

---

## Tasks
(pendiente — karvey-tasks)

---

## Estado de tareas
| Task | Estado | Tiempo estimado | Tiempo real |
|------|--------|----------------|-------------|
| (pendiente) | | | |

---

## Historial
| Fecha | Fase | Acción |
|-------|------|--------|
| {fecha} | init | Spec inicializada |
```

### Paso 9C — Actualizar grafo de conocimiento

Sincronizar el conocimiento según `karvey/rules/knowledge-sync.md` (Obsidian si está disponible; mínimo `/graphify docs/spec/ --update`) para reflejar los documentos creados.
Si `docs/spec/graphify-out/` no existe (primera vez en el proyecto), invocar `/graphify docs/spec/` sin `--update`.

### Paso 10 — Output final

```
✅ Spec inicializada: docs/spec/changes/{change-id}/

Config del proyecto: docs/spec/project.json (creado | leído)

Archivos creados:
  - docs/spec/changes/{change-id}/spec.json
  - docs/spec/changes/{change-id}/prd.md
  - docs/spec/changes/{change-id}/PLAN.md (si markdown)
  - docs/spec/specs/{capability}/spec.md (si nuevo capability)

Gestión: {ClickUp Epic E{n} creado | PLAN.md creado}
Security Tier: {N}

Siguiente paso:
/karvey-requirements {change-id}
```

## Safety

- Si `docs/spec/changes/{change-id}` ya existe con `spec.json`, preguntar antes de sobrescribir
- Si ClickUp falla, ofrecer continuar en modo markdown como fallback
- Validar que el `change-id` sea URL-safe (solo letras minúsculas, números y guiones)


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Requirements ahora?»
- Si confirma → ejecutá `/karvey-requirements {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
