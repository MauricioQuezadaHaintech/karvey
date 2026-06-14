---
name: karvey-guard
description: Safety guardrails for the Karvey method. Installs/disables the opt-in enforcement hooks (git-flow + plan-gate), grants temporary override, and can edit-lock work to a single directory. Triggers include "karvey guard", "guardrails", "freeze", "edit lock", "activar hooks", "bloquear cambios", "candado".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [--install | --disable-hooks | --freeze <dir> | --unfreeze | --override]
---

# Karvey Guard

## Propósito

Capa de **apoyo transversal** del Método Karvey — NO es una fase del pipeline. Provee los **guardrails** del método: gestiona los hooks de enforcement (que sí bloquean de forma determinista vía `PreToolUse`), concede override temporal del plan-gate y puede aplicar un **edit-lock** que restringe `Edit`/`Write` a un solo directorio.

Inspirada en `/careful` + `/freeze` + `/guard` de gstack, absorbidos como una única skill integrada al método.

**Reglas duras:**
- Es una skill **transversal**, no una fase: **NO cambia `spec.json:phase`** ni el estado del cambio.
- Los hooks son **OPT-IN por proyecto**, reversibles. **Nunca** se imponen globalmente sin que el usuario lo decida.
- Alineada con `karvey/rules/enforcement.md` (la regla canónica) y `karvey/rules/project-config.md`.

Gestiona los dos hooks definidos en `karvey/rules/enforcement.md`, cuyas plantillas viven en `karvey/hooks/`:

- **git-flow-guard** (`git-flow-guard.sh`) — `PreToolUse` sobre `Bash`. Bloquea push directo a producción, commit en `dev`/`master` y deploy manual. Flujo permitido: `feature/* → integration → PR → production`.
- **plan-gate** (`plan-gate.sh`) — `PreToolUse` sobre `Edit`/`Write`/`Bash` destructivo. Exige plan aprobado (marca `KARVEY_PLAN_FLAG`, default `/tmp/claude-plan-approved`) en todo el flujo.

## Pasos de ejecución

Leer SIEMPRE primero `karvey/rules/enforcement.md` para alinearse antes de tocar nada.

Resolver el modo según `$ARGUMENTS`. Si no viene argumento, mostrar el estado actual (qué hooks están registrados en `settings.json`, si hay freeze activo, si existe la marca de aprobación) y ofrecer las opciones.

### `--install` — Activar los hooks de enforcement

1. **Localizar config del proyecto.** Leer `docs/spec/project.json` (esquema en `karvey/rules/project-config.md`). Si no existe, detener e indicar correr `karvey-init` primero. Tomar `branch_flow` (`feature_prefix`, `integration`, `production`) para parametrizar.
2. **Copiar las plantillas** desde `karvey/hooks/` a la ubicación de hooks del proyecto (p. ej. `.claude/hooks/git-flow-guard.sh` y `.claude/hooks/plan-gate.sh`). Mantenerlas ejecutables (`chmod +x`).
3. **Registrarlas en el `settings.json` del proyecto** (`.claude/settings.json`) como hooks `PreToolUse`:
   - `git-flow-guard` con matcher sobre `Bash`.
   - `plan-gate` con matcher sobre `Edit`, `Write`, `NotebookEdit` y `Bash`.
   - Pasar la parametrización vía env del comando del hook, leyendo `branch_flow`: `KARVEY_BRANCH_INTEGRATION`, `KARVEY_BRANCH_PRODUCTION`, `KARVEY_FEATURE_PREFIX`, y opcionalmente `KARVEY_PLAN_FLAG`.
4. **Marcar `enforcement` en `project.json`**: setear `enforcement.git_flow_hook: true` y `enforcement.plan_gate_hook: true`.
5. Confirmar al usuario qué quedó instalado y recordar que es reversible con `--disable-hooks`.

### `--disable-hooks` — Desactivar (reversible)

1. Quitar las entradas de `git-flow-guard` y `plan-gate` de la sección `PreToolUse` del `settings.json` del proyecto.
2. Setear `enforcement.git_flow_hook: false` y `enforcement.plan_gate_hook: false` en `project.json`.
3. Dejar las plantillas en `.claude/hooks/` (no se borran; solo se desregistran) para poder reinstalar rápido.
4. Confirmar que el enforcement quedó desactivado.

### `--override` — Override temporal del plan-gate

1. Presentar el plan al usuario y **esperar aprobación explícita** (no avanzar sin ella).
2. Una vez aprobado, **crear la marca de aprobación**: `touch "$KARVEY_PLAN_FLAG"` (default `/tmp/claude-plan-approved`).
3. El hook `plan-gate` dejará pasar `Edit`/`Write`/`Bash` destructivo mientras exista la marca. Informar que es un permiso puntual y que conviene removerlo (`rm <flag>`) al terminar el bloque de cambios aprobados.

### `--freeze <dir>` — Edit-lock a un directorio (boundary)

Para trabajo sensible o debugging: restringir `Edit`/`Write` a un único directorio.

1. Resolver `<dir>` a ruta absoluta y validar que exista dentro del proyecto.
2. Instalar/registrar un hook `PreToolUse` sobre `Edit`/`Write`/`NotebookEdit` que **bloquea** (exit 2) cualquier escritura cuyo `file_path` no esté bajo el boundary; persistir el boundary (p. ej. en una marca `KARVEY_FREEZE_DIR` o archivo de estado del freeze).
3. Confirmar el boundary activo y recordar que solo se puede editar dentro de `<dir>` hasta hacer `--unfreeze`.

### `--unfreeze` — Quitar el edit-lock

1. Remover el hook de freeze del `settings.json` y limpiar la marca/estado del boundary.
2. Confirmar que se levantó el candado y que vuelven a permitirse ediciones normales (sujetas a los demás hooks si están activos).

## Notas

- `--install`/`--freeze` editan `settings.json` y copian scripts: respetar el gate de plan aprobado como cualquier cambio.
- Esta skill **complementa** los gates de las fases (`karvey-qa`, etc.) pero no los reemplaza ni los aprueba por sí sola.
- Tras tocar artefactos en `docs/spec/`, sincronizar conocimiento según `karvey/rules/knowledge-sync.md`.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
