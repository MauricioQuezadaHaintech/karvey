---
name: karvey-archive
description: Archive a completed change: merge spec-deltas into living specs, move to archive, close Epic in ClickUp. Triggers include "karvey archive", "archivar", "cerrar epic", "merge specs".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: <change-id>
---

# Karvey Archive

## Propósito

Completar el ciclo de vida del cambio: fusionar spec-deltas en las living specs, archivar el directorio del cambio, y cerrar el Epic en ClickUp o marcar completo en PLAN.md.

## Pasos de ejecución

### Paso 1 — Verificar completitud

**Cuándo:** el cambio ya fue desplegado con `/karvey-deploy` (phase: deployed). Archive es la FASE 12 (última) del Método Karvey y se ejecuta DESPUÉS del despliegue.

Leer `docs/spec/changes/{change-id}/spec.json`.

Verificar:
- [ ] `phase = "deployed"` o `approvals.deploy.approved = true` — si no se cumple, advertir que falta desplegar el cambio con `/karvey-deploy` y detener.
- [ ] `approvals.tasks.approved = true`
- [ ] Tests ejecutados (existe `docs/test_evidence.md` con entradas del change-id)
- [ ] QA review completado (existe `REVISION_PR_*_{fecha}.md`)
- [ ] No hay hallazgos críticos o altos pendientes

Si hay bloqueantes: reportar y detener.

Como el despliegue ya ocurrió (`/karvey-deploy`), crear el marcador de producción `docs/spec/changes/{change-id}/IMPLEMENTED` si aún no existe. Si por alguna razón el deploy no se completó, advertir que se archivará sin el marcador de producción.

### Paso 2 — Leer spec-deltas

Leer todos los archivos `docs/spec/changes/{change-id}/specs/**/*.md`.

Para cada spec-delta, identificar las operaciones:
- `## ADDED Requirements` → append en living spec
- `## MODIFIED Requirements` → reemplazar bloque en living spec
- `## REMOVED Requirements` → eliminar bloque + dejar comentario deprecación

### Paso 3 — Mergear deltas en living specs

Para cada capability afectado, editar `docs/spec/specs/{capability}/spec.md`:

**ADDED:** Agregar al final del archivo:
```bash
cat >> docs/spec/specs/{capability}/spec.md << 'EOF'

{bloque del nuevo requirement completo}
EOF
```

**MODIFIED:** Localizar el requirement por nombre y reemplazar el bloque completo.
Búsqueda: `grep -n "### Requirement: {nombre}" docs/spec/specs/{capability}/spec.md`
Reemplazar desde esa línea hasta el próximo `### Requirement:` o fin de archivo.

**REMOVED:** Localizar el bloque y eliminarlo, dejando comentario:
```markdown
<!-- Eliminado {fecha}: {razón del spec-delta} -->
```

### Paso 4 — Commit del merge de specs

```bash
git add docs/spec/specs/
git commit -m "spec: merge deltas from {change-id}

- {capability}: ADDED {N} requirements, MODIFIED {N}, REMOVED {N}"
```

### Paso 5 — Archivar el directorio del cambio

```bash
TIMESTAMP=$(date +%Y-%m-%d)
mkdir -p docs/spec/changes/archive
mv docs/spec/changes/{change-id} docs/spec/changes/archive/${TIMESTAMP}-{change-id}
```

Verificar:
```bash
ls -la docs/spec/changes/archive/${TIMESTAMP}-{change-id}
# change-id ya no debe existir en docs/spec/changes/
```

```bash
git add docs/spec/changes/
git commit -m "chore: archive {change-id}

Spec deltas merged into living specs. Change archived."
```

### Paso 6A — Cerrar Epic en ClickUp (si management=clickup)

```
clickup_create_task_comment(epic_id,
  "✅ Epic completado y archivado.\n\nSpec deltas mergeados en: docs/spec/specs/{capability}/spec.md\nArchivado en: docs/spec/changes/archive/{fecha}-{change-id}\n\nRealizado con Método Karvey")
clickup_update_task(epic_id, status="complete")
```

### Paso 6B — Cerrar PLAN.md (si management=markdown)

Actualizar `docs/spec/changes/archive/{fecha}-{change-id}/PLAN.md`:
- Estado general: `✅ Completado y archivado`
- Agregar entrada en historial: `| {fecha} | archive | Spec mergeada y archivada |`

### Paso 6C — Actualizar spec.json

Actualizar `docs/spec/changes/archive/{fecha}-{change-id}/spec.json`:
- Dejar `phase: "archived"` (transición desde `deployed`).

### Paso 7 — Validar living specs

```bash
grep -n "### Requirement:" docs/spec/specs/{capability}/spec.md
# Verificar que los requirements ADDED aparecen
# Verificar que los REMOVED ya no están
```

### Paso 7B — Actualizar grafo de conocimiento

Sincronizar el conocimiento según `karvey/rules/knowledge-sync.md` (Obsidian si está disponible; mínimo `/graphify docs/spec/ --update`) para reflejar el merge de spec-deltas y el archivado.
El `--update` también elimina del grafo los nodos de documentos que fueron borrados (REMOVED requirements).

### Paso 7C — Retrospectiva del ciclo (opcional, recomendado)

Una vez mergeadas las specs y archivado el cambio, ofrecer cerrar el ciclo con una retrospectiva. Es **opcional pero recomendado**, sobre todo en Epics grandes o ciclos que tomaron varios días.

Recomendar correr la skill transversal `karvey-retro` para extraer aprendizajes del ciclo:
- **Velocity:** cuánto tomó cada fase vs. lo estimado, dónde se fue el tiempo.
- **Test health:** cobertura, tests flaky, hallazgos de QA recurrentes.
- **Oportunidades:** deuda técnica detectada, mejoras de proceso, riesgos para el próximo ciclo.

```
¿Querís correr la retrospectiva del ciclo con /karvey-retro {change-id}?
(opcional — recomendado para capturar aprendizajes de velocity, test health y oportunidades)
```

No es bloqueante: si el usuario la omite, continuar igual con el output final.

### Paso 7D — Documentación post-release (opcional, recomendado)

Las living specs internas (`docs/spec/specs/`) ya quedaron mergeadas en el Paso 3 — eso **no** se toca acá. Este paso es para la documentación **de usuario / de proyecto** (READMEs, guías, docs Diataxis), que es distinta de las specs internas.

Recomendar correr la skill transversal `karvey-docs` para, después del release:
- **Actualizar docs stale:** detectar y refrescar documentación de proyecto/usuario que quedó desactualizada por lo que se shipeó en este cambio.
- **Generar docs Diataxis:** crear documentación nueva (tutorial / how-to / referencia / explicación) de las funcionalidades entregadas, cuando aplique.

```
¿Querís actualizar/generar la documentación de usuario con /karvey-docs {change-id}?
(opcional — recomendado; distingue docs de usuario/proyecto de las living specs internas que archive ya mergeó)
```

No es bloqueante: si el usuario la omite, continuar igual con el output final.

### Paso 8 — Output final

```
✅ Cambio archivado: {change-id}

Spec deltas mergeados:
  - docs/spec/specs/{capability}/spec.md
    - ADDED: {N} requirements
    - MODIFIED: {N} requirements
    - REMOVED: {N} requirements

Archivado en: docs/spec/changes/archive/{fecha}-{change-id}
IMPLEMENTED: {sí / no — sin marcar}

Gestión: {Epic E{n} cerrado en ClickUp | PLAN.md marcado completo}

Commits:
  - "spec: merge deltas from {change-id}"
  - "chore: archive {change-id}"

Pasos finales opcionales (recomendados):
  - 🔁 Retrospectiva del ciclo:        /karvey-retro {change-id}
  - 📚 Documentación post-release:     /karvey-docs {change-id}

🏁 Ciclo completo del Método Karvey finalizado para {change-id}
```


## Cierre del ciclo

Tras archivar, **preguntá al usuario** si quiere correr los pasos finales opcionales recomendados:
- `/karvey-retro {change-id}` — retrospectiva del ciclo.
- `/karvey-docs {change-id}` — documentación post-release (Diataxis / actualizar docs).

Con esto el ciclo del cambio queda cerrado. Para un nuevo cambio: `/karvey-grill` o `/karvey-init`.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
