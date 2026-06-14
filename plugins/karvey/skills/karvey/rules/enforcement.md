# Regla: Enforcement por hooks (git-flow + plan-gate)

Una skill es **guía** que el modelo sigue voluntariamente — no garantiza nada. Para **forzar** comportamiento de forma determinista se usan **hooks** del harness (`PreToolUse`), que sí bloquean. Karvey **provee e instala (opt-in)** dos hooks que cierran los dos agujeros más comunes:

1. **git-flow** — evita que se salte el flujo (push directo a master, commit en dev/master).
2. **plan-gate** — evita cambios sin plan aprobado.

## Instalación (opt-in por proyecto)

- `karvey-init` pregunta si activar el enforcement. Si sí, escribe los hooks en el `settings.json` del proyecto (o el `.claude/settings.json` correspondiente), parametrizados con `project.json:branch_flow`.
- `karvey-guard` los gestiona después: **instalar**, **desactivar**, o conceder **override** temporal.
- Las plantillas viven en `karvey/hooks/` (`git-flow-guard.sh`, `plan-gate.sh`).

## Hook 1 — git-flow-guard (PreToolUse sobre Bash)

Intercepta comandos `git`:
- **Bloquea** `git push` directo a la rama de producción (`branch_flow.production`, default `master`) y a la de integración cuando no viene de merge del flujo.
- **Bloquea** `git commit` cuando la rama actual es `dev`/`master` (debe ser `feature/*`).
- **Bloquea** deploy manual (`func azure functionapp publish` y equivalentes) — el deploy lo hacen los CI/CD.
- Flujo permitido: `feature/* → dev → PR → master`. Ver `deploy-workflow.md`.

## Hook 2 — plan-gate (PreToolUse sobre Edit/Write/Bash destructivo)

- **Exige plan aprobado en TODO el flujo**: cualquier `Edit`, `Write` o comando destructivo se bloquea si no existe la marca de aprobación.
- **Override**: el usuario aprueba el plan y se crea la marca (patrón `touch <flag>`); el hook deja pasar hasta que se consuma/expire.
- Mensaje de bloqueo claro indicando que falta presentar y aprobar el plan.

## Override y reversión

- **Override puntual**: crear la marca de aprobación (definida en el hook) tras presentar el plan.
- **Desactivar**: `karvey-guard --disable-hooks` quita los hooks del `settings.json` del proyecto.
- Los hooks son **reversibles** y **por proyecto**; nunca se imponen globalmente sin que el usuario lo decida.

## Relación con guardrails de gstack

Absorbe el valor de `/careful`, `/freeze`, `/guard`: `karvey-guard` también ofrece **edit-lock a un directorio** (bloquea Edit/Write fuera de un boundary) para trabajo sensible o debugging.
