---
name: karvey-tasks
description: Generate implementation tasks from approved architecture. Creates Tasks in ClickUp (E{n}.F{n}.T{n}) with dependencies, or updates PLAN.md checklist. Triggers include "karvey tasks", "generar tareas", "planificar implementación".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion
argument-hint: <change-id> [-y] [--sequential]
---

# Karvey Tasks

## Propósito

Generar el plan de tareas de implementación desde la arquitectura aprobada. Registrar en ClickUp (Epic > Feature > Tasks con dependencias) o en PLAN.md checklist. Tamaño objetivo: 10–30 minutos por task (tiempos IA).

## Pasos de ejecución

### Paso 1 — Cargar contexto

Leer:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/architecture.md`
- `docs/spec/changes/{change-id}/infra.md`
- `rules/clickup-protocol.md`

Verificar `approvals.infra.approved = true`. Si no, detener.

Determinar modo secuencial: si `--sequential`, no usar marcadores de paralelismo.

### Paso 2 — Generar borrador de tasks.md

Para cada Feature identificado en architecture.md, generar tasks por capa siguiendo el File Structure Plan.

**Reglas de granularidad:**
- 1 task = 1 unidad de trabajo ejecutable por un agente IA
- Tiempo estimado: 10–30 minutos (tiempos IA)
- Máximo 1h por task. Si excede, dividir.
- Cada task produce un artefacto verificable (SP, endpoint, componente, test)
- El criterio de "done" debe ser observable (no "implementar X", sino "SP funciona y retorna {Y}")

**Orden de ejecución obligatorio:**
```
[BD] → [Backend] → [Frontend]
```
Tasks de la misma capa dentro de un Feature pueden marcarse `(P)` si son independientes.

**Etiquetas de capa válidas:** `[BD/Backend/Frontend/Infra]`. Se permiten tasks de tipo `Infra` para ajustes de IaC/pipeline que surjan durante la implementación (la infra base ya viene definida en `infra.md`).

**Estructura de tasks.md:**
```markdown
# Tasks: {change-id}

## Feature F1: {Nombre}
Requirements cubiertos: {N.N, N.N}
Tiempo total estimado: {suma}

### F1.T1 [BD] {Descripción}
**Estimación:** 15min
**Artefacto:** `{db_path}/{sp_nombre}.sql`
**Done cuando:** SP / query compila sin errores, ejecuta con parámetros de prueba y retorna {resultado esperado}
- Crear `{schema}.{sp_nombre}` con parámetros: `@{contextKey}`, `@{param2}`
- Validar contexto de usuario en la primera línea
- Retornar {estructura de resultado}
- Requirements: {N.N}

### F1.T2 [Backend] {Descripción} — _Depends: F1.T1_
**Estimación:** 20min
**Artefacto:** `{backend_path}/{nombre}`
**Done cuando:** Endpoint retorna 200 con {estructura} para request válido, 401 sin auth, 422 con input inválido
- Crear endpoint `{nombre}`
- Validar auth token y extraer contexto de usuario
- Llamar BD con `{db_helper()}`
- Manejar errores sin exponer stack trace
- Requirements: {N.N}

### F1.T3 [Frontend] {Descripción} — _Depends: F1.T2_ (P)
**Estimación:** 25min
**Artefacto:** `{frontend_path}/{nombre}`
**Done cuando:** Componente renderiza datos del endpoint, maneja estado loading/error/empty
- Crear componente `{nombre}`
- Consumir endpoint via `{api_layer}/{servicio}`
- Implementar estados: loading, error, vacío, con datos
- Requirements: {N.N}
```

### Paso 3 — Review gate

Verificar antes de escribir:
- [ ] Cada requirement tiene al menos una task que lo implementa
- [ ] Cada componente del File Structure Plan tiene su task correspondiente
- [ ] El orden BD→Backend→Frontend se respeta con dependencias explícitas
- [ ] Cada task tiene un criterio de done observable
- [ ] Ninguna task supera 1h de estimación
- [ ] Tasks [BD] no modifican código de aplicación y viceversa
- [ ] Las tasks de testing están incluidas (al menos una por Feature)

Si hay gaps: corregir y re-verificar. Máximo 2 iteraciones.

### Paso 4 — Escribir tasks.md

```
docs/spec/changes/{change-id}/tasks.md
```

Actualizar `spec.json`: `phase: "tasks-generated"`, `approvals.tasks.generated: true`.

### Paso 4B — Actualizar grafo de conocimiento

Sincronizar el conocimiento según `karvey/rules/knowledge-sync.md` (Obsidian si está disponible; mínimo `/graphify docs/spec/ --update`) para reflejar el `tasks.md` creado.
Si `docs/spec/graphify-out/` no existe, invocar `/graphify docs/spec/` sin `--update`.

### Paso 5 — Presentar para aprobación

Si flag `-y`: auto-aprobar.

Mostrar resumen:
```
📋 Tasks generadas: docs/spec/changes/{change-id}/tasks.md

Resumen:
  Features: {N}
  Tasks totales: {N} ({N} BD, {N} Backend, {N} Frontend, {N} Test)
  Tiempo estimado total: {suma}

Cobertura:
  Requirements cubiertos: {N}/{N}
  Componentes del File Structure Plan: {N}/{N}

¿Aprobás las tasks para continuar?
```

### Paso 6A — Crear Tasks en ClickUp (si management=clickup)

Leer `spec.json` para `clickup.epic_id`, `clickup.feature_ids`, `clickup.backlog_list_id`.

Leer credenciales de `.connections.json` (ver `rules/clickup-protocol.md`). Si no existe, crearlo y agregarlo al `.gitignore` antes de continuar.

Para cada task, crear en ClickUp:
```
clickup_create_task
  name: "E{n}.F{n}.T{n} [Capa] {Descripción}"
  list_id: "{backlog_list_id}"
  tags: ["{client_tag}"]
  description: (ver formato)
  priority: "normal"
  start_date: "YYYY-MM-DD"
  due_date: "YYYY-MM-DD"
```

Formato de descripción de task:
```
E{n}.F{n}.T{n}: [Capa] {Nombre}

Feature padre: E{n}.F{n} {Nombre del Feature}

Descripción:
{qué hacer en detalle para que un agente IA lo ejecute}

Criterios de aceptación:
- [ ] {criterio 1}
- [ ] {criterio 2}

Dependencias:
- Depende de: {lista de tasks previas}
- Bloquea: {lista de tasks que esperan esta}

Estimación: {N}min

Al terminar:
1. Detener time tracking
2. Comentar: resumen de lo hecho, archivos modificados
3. Cambiar estado a "listo! para pap"

Realizado con Método Karvey
```

Inmediatamente después de crear cada task:
```
clickup_add_tag_to_task(task_id, "{client_tag}")
```

Actualizar `time_estimate` via REST API (MCP no lo guarda):
```bash
curl -s -X PUT "https://api.clickup.com/api/v2/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -d '{"time_estimate": {MIN * 60000}}'
```

Crear dependencias via REST API:
```bash
# Task B depende de Task A: B espera a A
curl -s -X POST "https://api.clickup.com/api/v2/task/{B_ID}/dependency" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json" \
  -d '{"depends_on":"{A_ID}"}'
```

Dependencias a crear:
- Feature ← sus Tasks (Feature depende de que todas las Tasks terminen)
- Epic ← sus Features
- [Backend] → [BD] dentro de cada Feature
- [Frontend] → [Backend] dentro de cada Feature

Verificar sprint activo y agregar tasks:
```bash
curl -s -X POST "https://api.clickup.com/api/v2/list/{SPRINT_LIST_ID}/task/{TASK_ID}" \
  -H "Authorization: $API_KEY" -H "Content-Type: application/json"
```

Actualizar `spec.json` con IDs de tasks creadas.

### Paso 6B — Actualizar PLAN.md (si management=markdown)

Reemplazar la sección "Tasks" y "Estado de tareas" con el checklist completo:

```markdown
## Tasks

### Feature F1: {Nombre}

- [ ] F1.T1 [BD] {descripción} — est: 15min
- [ ] F1.T2 [Backend] {descripción} — est: 20min (depende F1.T1)
- [ ] F1.T3 [Frontend] {descripción} — est: 25min (depende F1.T2)

## Estado de tareas
| Task | Estado | Estimado | Real | Notas |
|------|--------|----------|------|-------|
| F1.T1 [BD] | ⬜ pendiente | 15min | — | |
| F1.T2 [Backend] | ⬜ pendiente | 20min | — | |
| F1.T3 [Frontend] | ⬜ pendiente | 25min | — | |
```

### Paso 7 — Output final

Al aprobar: `approvals.tasks.approved: true`, `phase: "tasks-approved"`.

```
✅ Tasks aprobadas

Gestión: {N tasks creadas en ClickUp con dependencias | PLAN.md actualizado}

Siguiente paso:
/karvey-impl {change-id}
```


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Implementación ahora?»
- Si confirma → ejecutá `/karvey-impl {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
