---
name: karvey-checkpoint
description: Save and restore work-in-progress state for the Karvey method. Captures git state, decisions made, and pending work so a future session (or another person) can resume cleanly. Triggers include "karvey checkpoint", "guardar contexto", "restaurar contexto", "guardar estado", "retomar trabajo", "handoff".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [save | restore] [<change-id>]
---

# Karvey Checkpoint

Skill **transversal** del Método Karvey: una capa de apoyo, **NO una fase**. No avanza ni modifica el ciclo de vida del cambio. En particular, **NO toca `spec.json:phase`** ni ningún campo de fase.

Inspirada en `gstack /context-save` + `/context-restore`, su único trabajo es que el trabajo en curso no se pierda entre sesiones ni en un handoff a otra persona.

## Objetivo

Que el trabajo en curso **no se pierda entre sesiones / handoffs**. Cuando una sesión termina a medias, o cuando otra persona (u otro agente, en otra máquina) debe retomar, el checkpoint deja por escrito dónde quedó todo: el estado de git, las decisiones tomadas, el trabajo pendiente y el siguiente paso concreto.

Esta skill **complementa, no reemplaza**, las living specs ni `spec.json`. Las specs siguen siendo la fuente de verdad del cambio; el checkpoint es solo una foto del trabajo-en-progreso para poder retomar limpiamente.

## Modos

La skill recibe un modo (`save` o `restore`) y, opcionalmente, un `<change-id>`. Si no se entrega `change-id`, se intenta detectar el cambio activo (ver "Resolución del change-id").

### Modo `save` — guardar estado

Captura el estado actual y lo escribe en un archivo de checkpoint. Pasos:

1. **Resolver el change-id** (ver sección "Resolución del change-id").
2. **Capturar el estado de git** del repo en el que se está trabajando:
   - Rama actual:
     ```bash
     git rev-parse --abbrev-ref HEAD
     ```
   - Estado del working tree (archivos modificados, staged, untracked):
     ```bash
     git status --short
     ```
   - Último commit (hash corto + asunto):
     ```bash
     git log -1 --pretty='%h %s'
     ```
   - (Opcional, si ayuda al handoff) diff resumido:
     ```bash
     git diff --stat
     ```
3. **Recolectar el contexto humano** de la sesión: decisiones tomadas, por qué, qué quedó pendiente y cuál es el siguiente paso concreto para retomar.
4. **Escribir el checkpoint** en:
   - `docs/spec/changes/{change-id}/checkpoint.md` si hay un cambio activo, o
   - un checkpoint a nivel de proyecto (p. ej. `docs/spec/checkpoint.md`) si **no** hay change activo.

   Usa la plantilla de la sección "Formato del checkpoint".
5. **Integrar con knowledge-sync**: tras guardar, aplica las reglas de `karvey/rules/knowledge-sync.md` para mantener sincronizado el conocimiento del repo (memoria, índices, referencias). El checkpoint es un punto natural para gatillar este sync.
6. **NO** modificar `spec.json:phase` ni avanzar la fase. Confirmar al usuario la ruta del checkpoint escrito.

### Modo `restore` — restaurar estado

Lee el checkpoint y deja al usuario (o al nuevo agente) listo para retomar. Pasos:

1. **Resolver el change-id** y localizar el checkpoint correspondiente (`docs/spec/changes/{change-id}/checkpoint.md`, o el checkpoint de proyecto si no hay change activo).
2. **Leer el checkpoint** completo.
3. **Verificar el estado real de git** contra lo registrado (rama, último commit, working tree) para detectar divergencias entre lo guardado y lo actual.
4. **Resumir dónde quedó todo**: rama, último commit, trabajo pendiente y decisiones relevantes.
5. **Proponer el siguiente paso** concreto para retomar, basado en el campo "Siguiente paso" del checkpoint y en el estado real verificado.
6. **NO** modificar `spec.json:phase` ni avanzar la fase.

## Resolución del change-id

1. Si el usuario pasó un `<change-id>` explícito, usarlo.
2. Si no, intentar detectar el cambio activo: revisar `docs/spec/changes/` (carpeta más reciente o la indicada por `spec.json`) y, si existe, el `spec.json` del proyecto.
3. Si no hay cambio activo, operar en modo **proyecto** (checkpoint en `docs/spec/checkpoint.md`).

## Formato del checkpoint

```markdown
# Checkpoint — {change-id | proyecto}

> Skill transversal karvey-checkpoint. NO es una fase. NO modifica spec.json:phase.

- **Fecha:** {YYYY-MM-DD HH:MM CLT}
- **Autor:** {nombre / agente}
- **Repo:** {ruta del repo}

## Estado de git
- **Rama:** {rama}
- **Último commit:** {hash corto} {asunto}
- **Working tree:**
  ```
  {salida de git status --short}
  ```

## Decisiones tomadas
- {decisión + por qué}

## Trabajo pendiente
- [ ] {item pendiente}

## Siguiente paso
{El paso concreto para retomar limpiamente.}
```

## Notas

- Esta skill es de apoyo: úsala libremente al cerrar o abrir una sesión, antes de un handoff, o cuando el contexto esté por perderse.
- No reemplaza las living specs ni `spec.json`; solo guarda/restaura el trabajo-en-progreso.
- Nunca avanza la fase del cambio.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
