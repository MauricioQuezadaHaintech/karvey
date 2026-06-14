# Plugin: karvey

Método **Karvey** (SDD agnóstico de stack) empaquetado como plugin de Claude Code.

- **Skills:** en `skills/` (12 fases + 12 de apoyo). Se autodescubren; se invocan como `/karvey:<skill>`.
- **Reglas y hooks:** dentro de `skills/karvey/` (`rules/`, `hooks/`). Los hooks de enforcement (`git-flow-guard.sh`, `plan-gate.sh`) son **opt-in** — los instala `karvey-guard --install` por proyecto, NO se activan al instalar el plugin.
- **Orquestador:** `/karvey:karvey [<change-id>]`.

Ver el [README del repo](../../README.md), `LICENSE`, `NOTICE` y `TRADEMARK.md`.
