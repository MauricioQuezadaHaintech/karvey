---
name: karvey-requirements
description: Generate EARS-format requirements and spec-delta for a Karvey spec. Creates Features in ClickUp or updates PLAN.md. Use after karvey-init. Triggers include "karvey requirements", "generar requisitos", "especificar requisitos".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, AskUserQuestion
argument-hint: <change-id> [-y]
---

# Karvey Requirements

## Propósito

Generar requisitos en formato EARS para el cambio, producir el spec-delta con operaciones ADDED/MODIFIED/REMOVED, y registrar los Features en ClickUp o PLAN.md.

## Pasos de ejecución

### Paso 1 — Cargar contexto

Leer:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/prd.md` (PRD generado en karvey-init)
- `docs/spec/changes/{change-id}/proposal.md`
- `docs/spec/specs/{capability}/spec.md` (living spec actual)
- `rules/ears-format.md`
- `rules/living-specs.md`
- `rules/security-tiers.md`

Los requirements deben derivar del PRD y cubrir sus objetivos y criterios de aceptación.

Si hay brief de `karvey-grill` en la conversación, incorporarlo.

Si el codebase es brownfield: despachar subagente para explorar implementaciones existentes:
> "Explora el codebase buscando funcionalidad relacionada con {capability}. Resumí: (1) qué existe, (2) interfaces/endpoints relevantes, (3) patrones que los nuevos requisitos deben respetar. Menos de 100 líneas."

### Paso 2 — Clarificar alcance antes de generar

Para cada área funcional identificada en `proposal.md`, preguntar si hay ambigüedad de alcance o comportamiento de borde. Hacer solo las preguntas necesarias — no preguntar lo que ya está claro.

**No preguntar sobre**: tecnología, arquitectura, patrones de implementación (eso va en karvey-architecture).

### Paso 3 — Generar borrador de requirements.md

Generar agrupando requisitos por área funcional. Aplicar formato EARS estricto.
Mantener como borrador en memoria — NO escribir aún.

Estructura del documento:
```markdown
# Requirements: {change-id}

## Descripción del proyecto
{2-3 líneas del problema y objetivo}

## Requirement 1: {Nombre del área funcional}

### 1.1 {Nombre del requisito}
WHEN {evento},
the {sistema} SHALL {comportamiento observable}.

Traza a PRD: {sección u objetivo del PRD}

#### Scenario: {Caso exitoso}
GIVEN {precondición}
WHEN {acción}
THEN {resultado observable}

#### Scenario: {Caso de error}
GIVEN {precondición}
WHEN {acción inválida}
THEN the system {respuesta de error específica}

### 1.2 {Siguiente requisito}
...

## Requirement 2: {Siguiente área}
...

## Exclusiones explícitas
- {Qué no está en scope y por qué}
- {Comportamiento que no cambia}
```

### Paso 4 — Review gate (antes de escribir)

Verificar el borrador:
- [ ] Cada requisito es testeable y no contiene ambigüedad
- [ ] Cada requirement traza a una sección u objetivo del PRD
- [ ] Todos los objetivos del PRD están cubiertos por al menos un requirement
- [ ] Ningún requisito menciona tecnología de implementación
- [ ] Los IDs son numéricos (1.1, 1.2, 2.1...)
- [ ] Cada requisito tiene al menos un scenario de éxito y uno de error
- [ ] Las exclusiones explícitas cubren los bordes más probables
- [ ] Los requisitos de seguridad reflejan el Security Tier declarado en spec.json

Si hay issues locales al borrador: corregir y re-verificar (máximo 2 iteraciones).
Si hay ambigüedad real que requiere decisión del usuario: preguntar antes de continuar.

### Paso 5 — Escribir requirements.md

```
docs/spec/changes/{change-id}/requirements.md
```

Actualizar `spec.json`:
- `phase: "requirements-generated"`
- `approvals.requirements.generated: true`
- `updated_at: {timestamp}`

### Paso 6 — Generar spec-delta.md

Comparar los nuevos requisitos contra `docs/spec/specs/{capability}/spec.md`.

Para cada requisito nuevo: sección `## ADDED Requirements`
Para cada requisito que modifica uno existente: sección `## MODIFIED Requirements`
Para cada requisito que elimina uno existente: sección `## REMOVED Requirements`

Si el capability es nuevo (spec.md vacío), todo es ADDED.

Escribir `docs/spec/changes/{change-id}/specs/{capability}/spec-delta.md`.

### Paso 7 — Presentar para aprobación

Mostrar resumen:
```
📋 Requirements generados: docs/spec/changes/{change-id}/requirements.md

Áreas cubiertas:
  - Requirement 1: {nombre} ({N} requisitos)
  - Requirement 2: {nombre} ({N} requisitos)

Spec-delta:
  - ADDED: {N} requisitos
  - MODIFIED: {N} requisitos
  - REMOVED: {N} requisitos

Review gate: ✅ pasado

¿Aprobás los requisitos para continuar?
```

Si el flag `-y` está presente: auto-aprobar.

Si el usuario aprueba: actualizar `spec.json` con `approvals.requirements.approved: true`.

### Paso 8A — Crear Features en ClickUp (si management=clickup)

Leer `spec.json` para obtener `clickup.epic_id` y `clickup.backlog_list_id`.
Crear un Feature por cada área funcional de requirements.md:

```
clickup_create_task
  name: "E{n}.F{n} {Nombre del Feature}"
  list_id: "{backlog_list_id}"
  task_type: "Feature"
  tags: ["{client_tag}"]
  description: (ver formato)
```

Formato de descripción del Feature:
```
E{n}.F{n}: {Nombre del Feature}

Descripción:
{qué hace, valor para el usuario, flujo funcional}

Permisos:
{quién puede usar: ejecutivo/supervisor/admin/sistema}

Flujo:
1. {paso 1}
2. {paso 2}

Requirements cubiertos: {N.N, N.N, ...}
Security Tier: {N}

Tasks: (pendiente — karvey-tasks)
Tiempo estimado: (pendiente)
```

Crear dependencia Epic ← Feature via REST API:
```bash
curl -s -X POST "https://api.clickup.com/api/v2/task/{EPIC_ID}/dependency" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -d '{"depends_on":"{FEATURE_ID}"}'
```

Actualizar `spec.json` con `clickup.feature_ids`.

### Paso 8B — Actualizar PLAN.md (si management=markdown)

Agregar sección Features en `PLAN.md` con la lista de features y sus requisitos cubiertos.

### Paso 8C — Actualizar grafo de conocimiento

Sincronizar el conocimiento según `karvey/rules/knowledge-sync.md` (Obsidian si está disponible; mínimo `/graphify docs/spec/ --update`) para reflejar los documentos creados o modificados.
Si `docs/spec/graphify-out/` no existe, invocar `/graphify docs/spec/` sin `--update`.

### Paso 9 — Output final

```
✅ Requirements aprobados

Archivos creados/actualizados:
  - docs/spec/changes/{change-id}/requirements.md
  - docs/spec/changes/{change-id}/specs/{capability}/spec-delta.md
  - spec.json actualizado

Gestión: {Features E{n}.F1..F{n} creados en ClickUp | PLAN.md actualizado}

Siguiente paso:
/karvey-mockup {change-id}
```


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Mockup ahora?»
- Si confirma → ejecutá `/karvey-mockup {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
