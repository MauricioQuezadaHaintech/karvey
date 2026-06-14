# Regla: Sincronización de conocimiento entre iteraciones

Para que las iteraciones del método sean consistentes (cada fase conoce las dependencias y decisiones de las anteriores), Karvey mantiene un grafo de conocimiento. El mecanismo depende de `knowledge_sync` en `docs/spec/project.json`.

## Decisión del mecanismo

Se decide **una vez** en `karvey-init` y se guarda en `project.json`:

1. **¿El usuario tiene Obsidian con MCP integrado disponible en la sesión?**
   - Detectar si hay herramientas MCP de Obsidian disponibles (ej. tools cuyo nombre contiene `obsidian`).
   - Si **sí** → `knowledge_sync = "obsidian"`.
   - Si **no** → `knowledge_sync = "graphify"` (mínimo, siempre).

> Regla de oro: **jamás quedarse sin sincronización**. Si Obsidian no está disponible, se usa graphify como piso mínimo para no perder el conocimiento de dependencias.

## Paso de sincronización (invocado al final de cada fase)

Cada skill que produce o modifica documentos en `docs/spec/` ejecuta este paso al terminar:

### Si `knowledge_sync = "obsidian"`
- Sincronizar los documentos creados/modificados al vault vía el MCP de Obsidian (crear/actualizar las notas correspondientes y sus enlaces de dependencia).
- Si el MCP de Obsidian falla o no responde, **degradar a graphify** automáticamente para no perder la actualización.

### Si `knowledge_sync = "graphify"`
- Invocar `/graphify docs/spec/ --update` para reflejar los documentos creados o modificados.
- Si `docs/spec/graphify-out/` no existe (primera vez en el proyecto), invocar `/graphify docs/spec/` sin `--update`.
- En proyectos **multi-repo**: además de `docs/spec/`, ejecutar graphify en cada repo de `project.json:repos` que haya tenido cambios de código en la fase actual, para mantener el grafo de dependencias del código alineado con la spec.

## Resumen

| Condición | Acción |
|-----------|--------|
| Obsidian MCP disponible | Sync vía Obsidian (fallback a graphify si falla) |
| Sin Obsidian | `/graphify docs/spec/ --update` (mínimo garantizado) |
| Multi-repo con cambios de código | graphify también en los repos afectados |
