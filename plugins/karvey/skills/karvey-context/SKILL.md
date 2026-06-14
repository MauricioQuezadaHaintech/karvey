---
name: karvey-context
description: Read-only dashboard of the current project spec state: project config (project.json), capabilities, active/archived changes, sprint status, and a deploy-queue / landing report (qué cambios están en dev, en prod, listos para liberar, y versiones por repo). Use at any point in the Karvey pipeline. Triggers include "karvey context", "estado del proyecto", "qué specs hay", "cambios activos", "cola de despliegue", "landing report", "qué hay en dev", "qué falta liberar".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [--capability <nombre>] [--change <change-id>]
---

# Karvey Context

## Propósito

Vista rápida del estado completo del proyecto: config del proyecto (`project.json`), capabilities documentados, cambios en curso, archivados, sprint actual, cobertura de specs y la **cola de despliegue / landing report** (estado de despliegue por cambio y versiones por componente/repo).

> **Solo lectura.** Este dashboard NUNCA escribe, modifica, despliega ni ejecuta git que altere estado (sin `commit`, `push`, `merge`, `fetch`, `pull`). Solo lee archivos del repo (`project.json`, `spec.json`, `CHANGELOG.md`) y, opcionalmente, `git log` local. Para desplegar, usar `karvey-deploy`.

## Pasos de ejecución

### Si se especifica --capability

Mostrar detalle del capability:
```bash
cat docs/spec/specs/{capability}/spec.md
grep -c "### Requirement:" docs/spec/specs/{capability}/spec.md
grep -c "#### Scenario:" docs/spec/specs/{capability}/spec.md
```

### Si se especifica --change

Mostrar detalle del cambio:
```bash
cat docs/spec/changes/{change-id}/spec.json
cat docs/spec/changes/{change-id}/proposal.md
# Estado de aprobaciones
```

### Si no se especifica nada — Dashboard completo

#### Config del proyecto (si existe `docs/spec/project.json`)

```bash
# Leer config a nivel proyecto
cat docs/spec/project.json 2>/dev/null
```

Si existe, mostrar un encabezado con su contenido (ver formato más abajo). Si NO existe, indicar "sin project.json (correr karvey-init)" y continuar con el resto del dashboard de todos modos. Esta vista es **solo lectura**: nunca escribir ni modificar `project.json`.

```bash
# Capabilities
find docs/spec/specs -mindepth 1 -maxdepth 1 -type d 2>/dev/null

# Requirements por capability
for cap in docs/spec/specs/*/; do
  name=$(basename "$cap")
  reqs=$(grep -c "### Requirement:" "$cap/spec.md" 2>/dev/null || echo "0")
  echo "$name: $reqs requirements"
done

# Cambios activos
find docs/spec/changes -maxdepth 1 -type d -not -path "docs/spec/changes" -not -path "*/archive" 2>/dev/null

# Cambios archivados
ls docs/spec/changes/archive/ 2>/dev/null | wc -l
```

#### Cola de despliegue / Landing report (solo lectura)

Snapshot del estado de despliegue por cambio. **No ejecuta git, no despliega, no escribe nada** — solo lee el repo principal y los `repos` de `project.json` para inferir el estado. Es el equivalente Karvey al "landing report".

Por cada cambio activo, derivar su estado de despliegue desde `spec.json` (campos `phase` y `approvals.deploy`):

```bash
# Estado de fase/deploy por cambio activo
for ch in $(find docs/spec/changes -maxdepth 1 -mindepth 1 -type d -not -name archive 2>/dev/null); do
  id=$(basename "$ch")
  phase=$(grep -o '"phase"[^,]*' "$ch/spec.json" 2>/dev/null | head -1)
  dep=$(grep -o '"deploy"[^}]*}' "$ch/spec.json" 2>/dev/null | head -1)
  qa=$(grep -o '"qa"[^}]*}' "$ch/spec.json" 2>/dev/null | head -1)
  echo "$id | $phase | qa=$qa | deploy=$dep"
done
```

Mapeo de estado (solo lectura, inferido — **no es verdad de la nube, es lo que dice el spec**):
- **Listo para liberar**: `approvals.qa.approved=true` y `approvals.deploy.approved=false` (QA OK, aún sin desplegar).
- **En dev**: `phase` indica deploy en curso a integración, o `approvals.deploy.generated=true` con merge a `integration` hecho y PR a `production` aún abierto/sin mergear.
- **En prod**: `approvals.deploy.approved=true` (merge a `production` con OK humano) o el cambio ya está archivado.
- **No listo**: cualquier otro estado (QA pendiente o gate de liberación incompleto).

Versiones desplegadas por componente/repo — leer el `CHANGELOG.md` de cada repo de `project.json:repos` (la versión tope del changelog es la última liberada de ese componente). **Solo lectura, sin `git`:**

```bash
# Versión actual por repo (desde su CHANGELOG.md)
# REPOS proviene de project.json:repos
for repo in $REPOS; do
  ver=$(grep -m1 -oE '\[?[0-9]+\.[0-9]+\.[0-9]+\]?' "$repo/CHANGELOG.md" 2>/dev/null)
  echo "$repo: ${ver:-sin CHANGELOG}"
done
```

Si `git` está disponible y se quiere afinar qué está en dev vs prod por repo (opcional, **solo lectura**, sin `fetch`/`pull`):

```bash
# Diferencia dev↔prod ya conocida localmente (no hace fetch)
# integration/production provienen de project.json:branch_flow
git -C "$repo" log --oneline {production}..{integration} 2>/dev/null | wc -l
# >0 ⇒ hay commits en integración aún no liberados a producción
```

Mostrar al usuario:

```
📊 Karvey Context — {fecha}

PROYECTO  (docs/spec/project.json)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{nombre del proyecto}
  Targets: {targets}            Nube: {cloud.provider} / IaC: {iac_tool}
  Git: {git_platform}           Knowledge sync: {knowledge_sync}
  Repos ({N}): {repo1, repo2, …}  (principal: {spec_repo})
  Branch flow: {feature_prefix} → {integration} → {production}
  Enforcement: git_flow_hook={on|off}  plan_gate_hook={on|off}
  (si no existe project.json → "sin project.json — correr karvey-init")

CAPABILITIES ({N} total)
━━━━━━━━━━━━━━━━━━━━━━━━
{capability-1}: {N} requirements, {N} scenarios
{capability-2}: {N} requirements, {N} scenarios

CAMBIOS ACTIVOS ({N})
━━━━━━━━━━━━━━━━━━━━
{change-id-1}
  Fase: {phase}
  Capability: {capability}
  Security Tier: {N}
  Gestión: {ClickUp Epic E{n} | Markdown}
  Aprobaciones: requirements={✅|⬜} mockup={✅|⬜} design={✅|⬜} arch={✅|⬜} tasks={✅|⬜}

{change-id-2}
  ...

CAMBIOS ARCHIVADOS: {N}
Último archivado: {fecha-change-id}

COLA DE DESPLIEGUE / LANDING REPORT  (solo lectura)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Estado de despliegue por cambio (inferido de spec.json — no es verdad de la nube):

  🟢 LISTO PARA LIBERAR ({N})
    {change-id}  — QA OK, deploy pendiente  (capability: {capability})

  🟡 EN DEV ({N})
    {change-id}  — desplegado a {integration}, PR a {production} pendiente

  🔵 EN PROD ({N})
    {change-id}  — liberado a {production}  ({fecha})

  ⬜ NO LISTO ({N})
    {change-id}  — {QA pendiente | gate de liberación incompleto}

Versiones desplegadas por componente/repo (tope de CHANGELOG.md):
    {repo1}: {x.y.z}   {repo2}: {x.y.z}   {repo3}: {sin CHANGELOG}
    (si hay git local: "{repo}: {N} commits en {integration} sin liberar a {production}")

SPRINT ACTIVO
━━━━━━━━━━━━
{verificar con clickup_get_workspace_hierarchy o indicar "no aplica (markdown)"}
```

### Para el sprint activo (si ClickUp disponible)

```
clickup_get_workspace_hierarchy
  max_depth: 2
```

Buscar el folder "Dev Sprints Metodo Karvey" y el sprint activo.

Mostrar:
```
Sprint activo: Sprint {N} (hasta {fecha})
Tasks del sprint: {total} | En progreso: {N} | Listo para PAP: {N} | Bloqueado: {N}
```

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
