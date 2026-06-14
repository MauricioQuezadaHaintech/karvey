---
name: karvey-deploy
description: Execute the ordered deployment flow (feature branch → dev → PR master) honoring the team's hard rules. Pull before start and before merge. Pipeline-triggered, never manual. Prod requires explicit human OK. Bumps semver + changelog before push, auto-detects the deploy platform, and runs a post-deploy canary loop (dev and prod) to guard zero-downtime. Use after karvey-qa passes. Triggers include "karvey deploy", "desplegar", "deploy", "liberar", "subir a dev", "pasar a prod".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: <change-id>
---

# Karvey Deploy

## Propósito

FASE 11 del Método Karvey, entre `karvey-qa` (FASE 10) y `karvey-archive` (FASE 12). Ejecuta el **flujo de despliegue ordenado** (feature branch → `dev` → PR a `master`) respetando al pie de la letra las reglas duras del equipo: nunca commit directo en `dev`/`master`, nunca deploy manual (el deploy lo gatilla el pipeline), `pull` antes de empezar y antes de cada merge/PR, y **prod nunca sin OK humano explícito**.

Se ejecuta **solo después** de que `karvey-qa` haya pasado sin hallazgos críticos/altos abiertos. La regla central es `karvey/rules/deploy-workflow.md`; síguela exactamente.

## Pasos de ejecución

### Paso 0 — Pre-checks (gate de liberación)

ANTES de tocar git, leer:
- `docs/spec/changes/{change-id}/spec.json`
- `docs/spec/project.json`

Si `project.json` no existe, detener e indicar correr `karvey-init` primero (ver `karvey/rules/project-config.md`).

Verificar el gate de liberación. Si **algo falla, DETENER y reportar qué falta. No desplegar.**

1. **QA aprobada sin hallazgos críticos/altos abiertos.**
   - Localizar el documento de revisión más reciente: `REVISION_PR_*_{fecha}.md` en la raíz de cada repo afectado (`ls -t REVISION_PR_*.md | head -1`).
   - El gate de seguridad de `karvey-qa` debe estar OK: **0 hallazgos críticos y 0 hallazgos altos sin resolver** en la tabla de severidad / checklist antes del merge.
   - Confirmar estado de QA en `spec.json` (`approvals.qa` / `phase`).

2. **Tests PASS.** Revisar `docs/test_evidence.md`: debe haber entradas del `{change-id}` con resultado PASS para los tests del cambio.

3. **CHANGELOG actualizado en cada repo afectado** (ver `karvey/rules/changelog-policy.md`). Por cada repo de `project.json:repos` con cambios, verificar `CHANGELOG.md`:
   - [ ] Entrada para la versión actual.
   - [ ] **Humano responsable** (nombre + contacto) — nunca vacío ni reemplazado por "IA".
   - [ ] **Modelo de IA** que asistió (ej. `Claude Opus 4.8`).
   - [ ] El **por qué**, no solo el qué.
   - [ ] Versión del CHANGELOG coincide con el archivo de versión del proyecto.

Si cualquiera de estos falla, reportar exactamente qué falta y detener. **No desplegar.**

### Paso 1 — Determinar repos y orden

Leer de `project.json`:
- `repos` (arreglo, mínimo 1).
- `branch_flow`: `feature_prefix` (default `feature/`), `integration` (default `dev`), `production` (default `master`).

Si el cambio toca **varios repos**, respetar el orden de dependencias declarado en `architecture.md` (ej. **BD → backend → frontend**). Para cada repo se aplica el flujo del Paso 2 en ese orden.

Registrar el orden resuelto antes de empezar.

### Paso 1.5 — Auto-detección de la plataforma de deploy

Antes de desplegar, confirmar **cómo y dónde** se libera cada repo. Si `project.json` ya lo declara (`deploy.platform`, `deploy.prod_url`, `deploy.health_check` por repo), usar eso. Si **no está configurado**, detectarlo y registrarlo en `project.json` para próximas corridas.

**Detectar plataforma** por evidencia en el repo (no asumir):

| Señal en el repo | Plataforma probable |
|------------------|---------------------|
| `fly.toml` | Fly.io |
| `render.yaml` | Render |
| `vercel.json` / `.vercel/` | Vercel |
| `netlify.toml` | Netlify |
| `host.json` + `azure-pipelines.yml` / `.github/workflows/*azure*` | Azure Functions (pipeline) |
| `.github/workflows/*.yml` | GitHub Actions (target del workflow define el destino real) |
| `azure-pipelines.yml` / `.azure-pipelines/` | Azure DevOps Pipelines |
| `Dockerfile` + manifiestos `k8s/` o `helm/` | Kubernetes |

**Descubrir URL de producción y health check:**
- Buscar URL de prod en `project.json:deploy`, variables del pipeline, `README`/`docs/spec/`, o la config de la plataforma (ej. `fly.toml`, `vercel.json`).
- Determinar el endpoint de health: `/health`, `/healthz`, `/api/health`, página raíz del front, o el que declare `architecture.md`. Para targets no-web (CLI/API/mobile), el "health check" es el equivalente en el **runtime real del target** (ver `karvey/rules/targets.md`).

Si no se logra descubrir URL/health de prod, **no inventar**: registrar como pendiente y pedir el dato al usuario antes del canary de prod. La regla dura sigue: el deploy lo gatilla el pipeline, esta detección es **solo** para saber **dónde monitorear**, nunca para desplegar manualmente.

Registrar lo detectado en `project.json:deploy` (`platform`, `prod_url`, `dev_url`, `health_check`) por repo.

### Paso 2 — Flujo de despliegue ordenado (POR CADA repo)

Aplicar siguiendo `karvey/rules/deploy-workflow.md` EXACTAMENTE, en el orden de dependencias del Paso 1.

**2.1 — `git pull` antes de empezar:**
```bash
git pull
```

**2.2 — Asegurar feature branch.** NUNCA commit directo en `dev`/`master`. Verificar que se trabaja en `feature/{change-id}`:
```bash
git branch --show-current   # debe ser feature/{change-id}
```
Si la rama `feature/{change-id}` no existe, **detener** — `karvey-impl` debió crearla. No crearla aquí.

**2.3 — Antes del merge, `pull` de integración:**
```bash
git pull origin {integration}     # default: dev
```

**2.4 — Bump de versión + CHANGELOG ANTES del push (ver `karvey/rules/versioning.md` y `karvey/rules/changelog-policy.md`).** Esto es parte del checklist de 6 pasos (Paso 3) y es obligatorio: **NUNCA se despliega sin subir versión.**

1. **Determinar el segmento semver a incrementar** (`major.minor.rev`) según la naturaleza del cambio:
   - **major** → breaking change (rompe compatibilidad de API/contrato/esquema/comportamiento).
   - **minor** → feature nueva compatible hacia atrás.
   - **rev** → fix/ajuste/cambio menor sin nueva feature.
2. **Bump de versión en cada componente/repo afectado.** Editar el archivo de versión según el stack (`package.json`, `pyproject.toml`, `*.csproj`, `VERSION`, git tags, etc.). Si un repo tiene varios componentes desplegables, bumpear el del componente que cambió.
3. **Documentar en `CHANGELOG.md` por componente Y por repositorio** (formato de `changelog-policy.md`): entrada para la nueva versión con **humano responsable** (nombre + contacto, nunca vacío ni "IA"), **modelo de IA** que asistió (ej. `Claude Opus 4.8`), y el **por qué** del cambio (no solo el qué). Indicar el segmento semver incrementado y por qué.
4. **(Si el repo tiene frontend) recomendar versión visible en la UI** — ver Paso 2.4-bis.

**2.4-bis — Versión visible en el front (recomendación).** Si algún `target` de `project.json` es `web`/mobile/desktop con UI (revisar `project.json:targets`), **recomendar al usuario** exponer la versión en la interfaz (footer, pantalla "Acerca de") para trazabilidad visible en producción: inyectar la versión en build (ej. `VITE_APP_VERSION` o equivalente del stack) y mostrarla en un lugar discreto pero accesible. Si la versión ya está visible, solo confirmar que se actualizó con el bump.

**2.5 — Merge feature → integración:**
```bash
git checkout {integration}        # dev
git merge feature/{change-id}
```

**2.6 — Push a integración ⇒ gatilla pipeline DEV** (el deploy lo hace el pipeline, NO manualmente):
```bash
git push origin {integration}     # dev → gatilla pipeline de DEV
```

**2.7 — Canary post-deploy en DEV (ver Paso 2-bis):** esperar a que el pipeline despliegue y correr el **loop de canary** sobre el runtime real de DEV (build verde del pipeline + monitoreo de salud). No avanzar a prod si DEV no quedó sano o si el canary detecta regresión.

**2.8 — Antes del PR, `pull` de producción:**
```bash
git pull origin {production}      # default: master
```

**2.9 — Crear PR `dev` → `master`:**
```bash
gh pr create --base {production} --head {integration} \
  --title "[Deploy] {change-id}" \
  --body "Deploy de {change-id}. QA OK, tests PASS, CHANGELOG actualizado. Requiere OK humano para merge a prod."
```

**2.10 — Merge a `master` SOLO con OK humano explícito ⇒ gatilla pipeline PROD.**
Usar `AskUserQuestion` para pedir aprobación explícita de prod. Sin OK humano, **no mergear**. Con OK:
```bash
gh pr merge --merge          # ⇒ gatilla pipeline de PROD
```

**2.11 — Canary post-deploy en PROD (ver Paso 2-bis):** tras el merge a `master`, esperar al pipeline PROD y correr el **loop de canary** sobre el runtime real de producción (`prod_url` / health del Paso 1.5). Es el refuerzo directo de zero-downtime: si el canary detecta regresión, **alertar y recomendar rollback inmediato**.

### Paso 2-bis — Loop de canary post-deploy (refuerzo zero-downtime)

Inspirado en el `/canary` de gstack y adaptado al runtime real del target (ver `karvey/rules/targets.md`). Se corre **después de cada deploy** (en DEV tras 2.7 y en PROD tras 2.11), apuntando al ambiente recién desplegado (`dev_url`/`prod_url` y health del Paso 1.5). Vigila que el deploy no haya degradado el servicio.

**Qué vigila el loop (varias iteraciones, no un solo check):**
1. **Errores de consola/logs** — consola del navegador (web, vía `karvey-browse`), logs del runtime/plataforma (Functions, contenedor, etc.). Buscar errores nuevos que no existían antes del deploy.
2. **Regresiones de performance** — latencia/tiempo de respuesta del health y de endpoints clave; comparar contra el baseline previo al deploy. Degradación notoria = regresión.
3. **Fallas de páginas/endpoints** — recorrer las rutas/endpoints críticos del cambio y los principales del producto; cualquier 5xx, timeout o página rota cuenta como falla.

**Cómo correrlo:**
- Apoyarse en **`karvey-browse`** ("dar ojos") para el runtime del target: navegador headless (web), simulador/dispositivo (mobile), cliente HTTP (API), proceso/terminal (CLI). No asume navegador.
- Repetir el ciclo (consola → performance → páginas/endpoints) durante una ventana razonable post-deploy (varias iteraciones espaciadas), no un único disparo. Registrar evidencia de cada iteración.
- En DEV: si el canary marca regresión, **detener y no avanzar a prod**; arreglar primero.
- En PROD: si el canary marca regresión, **alertar de inmediato y recomendar rollback** (revertir el merge / desplegar la versión anterior por pipeline). Nunca dejar prod degradado. El rollback también se ejecuta por pipeline, nunca manual.

**Resultado del canary:** OK (sin regresiones) o REGRESIÓN (con detalle de qué falló: consola/perf/endpoint). Dejar el resultado registrado para el output final y la gestión.

### Paso 3 — Checklist de 6 pasos (antes del push a dev)

De `karvey/rules/deploy-workflow.md`. Mostrar y verificar antes del push a `dev`:

1. ¿Estoy en feature branch? (no `dev`/`master`)
2. ¿Bumpée la versión semver (major/minor/rev) en cada componente/repo afectado y actualicé `CHANGELOG.md` por componente y por repo? (ver `versioning.md` y `changelog-policy.md`; si hay front, ¿recomendé/actualicé la versión visible en UI?) **NUNCA desplegar sin subir versión.**
3. ¿Commit de todo lo pendiente?
4. ¿Push del branch?
5. ¿Merge a `dev`?
6. ¿Push `dev`?

Solo después de los 6 → el pipeline despliega dev. Para prod, repetir verificación y PR a `master` con aprobación humana.

### Paso 4 — Reglas duras (NUNCA saltarse)

- **NUNCA commit directo en `dev` ni `master`.** Siempre feature branch.
- **NUNCA deploy manual.** El deploy lo gatilla el pipeline (push a `dev`, merge a `master`). PROHIBIDO `func azure functionapp publish` o equivalentes manuales.
- **`pull` antes de comenzar y antes de cada merge/PR.**
- **Prod NUNCA sin OK humano explícito.** El PR a `master` no se mergea sin aprobación.
- **NUNCA desplegar sin subir versión** (semver + CHANGELOG por componente y repo).
- **Zero downtime**: el despliegue no puede provocar caída del servicio; el canary post-deploy lo refuerza y, ante regresión en prod, recomienda rollback (por pipeline, nunca manual).

### Paso 5 — Registrar en la gestión

Leer `management` de `spec.json`.

**Si `management = clickup`:** crear task `[Deploy] {change-id}` con el checklist de 6 pasos como subtareas y cierre al confirmar prod:
```
clickup_create_task
  name: "[Deploy] {change-id}"
  list_id: "{sprint_list_id}"
  priority: "high"
```
Por cada repo, registrar estado de deploy DEV y PROD. Cerrar la task al confirmar el merge a prod (pipeline PROD OK).

**Si `management = markdown`:** agregar entrada en `PLAN.md` con el estado del deploy **por repo y ambiente**:
```markdown
## Deploy — {change-id}
| Repo | DEV | PROD |
|------|-----|------|
| {repo1} | ✅ desplegado | ⏳ PR abierto / ✅ mergeado |
| {repo2} | ... | ... |
```

### Paso 6 — Actualizar spec.json

```
spec.json:
  phase: "deployed"
  approvals.deploy.generated: {YYYY-MM-DD}
  approvals.deploy.approved: {YYYY-MM-DD si hubo OK humano de prod, si no null}
```

### Paso 7 — Knowledge sync

Ejecutar el paso de sincronización de `karvey/rules/knowledge-sync.md` según `knowledge_sync` de `project.json`:
- `obsidian` → sincronizar los documentos modificados al vault vía MCP de Obsidian (fallback a graphify si falla).
- `graphify` → `/graphify docs/spec/ --update` (si `docs/spec/graphify-out/` no existe, sin `--update`).
- Multi-repo con cambios de código → graphify también en cada repo afectado.

### Paso 8 — Output final

```
✅ Deploy completo — {change-id}

Repos desplegados (en orden de dependencias):
  - {repo1}: v{nueva_versión} · DEV ✅ canary OK  |  PROD {✅ mergeado, canary OK / ⏳ PR abierto, esperando OK humano}
  - {repo2}: v{nueva_versión} · DEV ✅ canary OK  |  PROD ...

Checklist de 6 pasos: verificado
QA gate: OK (0 críticos, 0 altos) · Tests: PASS · Versión bumpeada + CHANGELOG: OK
Plataforma de deploy: {Fly | Render | Vercel | Netlify | Azure | GitHub Actions | ...} · Prod URL: {prod_url}
Canary post-deploy: DEV {OK / REGRESIÓN} · PROD {OK / REGRESIÓN → rollback recomendado / N/A}
{Si hay front} Versión visible en UI: {sí / recomendado al usuario}

Gestión: {[Deploy] {change-id} en ClickUp | PLAN.md actualizado}
Knowledge sync: {obsidian | graphify} actualizado

Siguiente paso: /karvey-archive {change-id}
```

## Safety

- **NUNCA commit directo en `dev` ni `master`** — siempre feature branch.
- **NUNCA deploy manual** — prohibido `func azure functionapp publish` y equivalentes; el deploy lo gatilla el pipeline (push `dev`, merge `master`).
- **`pull` antes de comenzar y antes de cada merge/PR.**
- **Prod NUNCA sin OK humano explícito** — el PR a `master` no se mergea sin aprobación.
- **NUNCA desplegar sin subir versión** — semver (major/minor/rev) bumpeado y CHANGELOG por componente y por repo (ver `versioning.md` y `changelog-policy.md`).
- **Zero downtime** — el despliegue no puede provocar caída del servicio; el canary post-deploy (DEV y PROD) lo refuerza y, ante regresión en prod, recomienda rollback (siempre por pipeline, nunca manual).
- **Gate de liberación obligatorio** — sin QA OK (0 críticos/altos), tests PASS, versión bumpeada y CHANGELOG completo, no se despliega.
- En multi-repo, respetar el orden de dependencias de `architecture.md` (BD → backend → frontend).


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Archive (cierre) ahora?»
- Si confirma → ejecutá `/karvey-archive {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
