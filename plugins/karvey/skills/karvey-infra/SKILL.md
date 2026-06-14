---
name: karvey-infra
description: Generate and configure cloud infrastructure (IaC) and CI/CD pipelines from the architecture's cloud spec. Idempotent over existing infra. Includes infra security review. Use after karvey-architecture. Triggers include "karvey infra", "infraestructura", "pipeline CI/CD", "IaC", "terraform", "bicep".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, AskUserQuestion
argument-hint: <change-id> [-y]
---

# Karvey Infra

## Propósito

Generar y configurar la **infraestructura cloud (IaC)** y los **pipelines CI/CD** a partir de la sección "Infraestructura Cloud" del `architecture.md` del cambio. Esta es la **FASE 6** del Método Karvey, entre `karvey-architecture` (FASE 5) y `karvey-tasks` (FASE 7).

La fase es **idempotente sobre la infra existente**: nunca recrea lo que ya está, solo crea lo que falta o modifica lo necesario. Incluye una **revisión de seguridad de infra** como gate, y respeta el flujo de despliegue del equipo (deploy por pipeline, nunca manual).

## Pasos de ejecución

### Paso 1 — Cargar contexto

Leer en paralelo:
- `docs/spec/changes/{change-id}/spec.json` (en especial `security_tier`, `layers`, `management`)
- `docs/spec/changes/{change-id}/architecture.md` (en especial la sección **"## Infraestructura Cloud"**: qué servicios de qué nube)
- `docs/spec/project.json` (campos `git_platform`, `cloud.provider`, `iac_tool`, `repos`, `spec_repo`, `branch_flow`)
- Reglas compartidas: `rules/project-config.md`, `rules/deploy-workflow.md`, `rules/changelog-policy.md`, `rules/knowledge-sync.md`, `rules/security-tiers.md`

Verificaciones de entrada:
- Si **no existe** `docs/spec/project.json` → **detener** e indicar correr `karvey-init` primero (ver `project-config.md`).
- Verificar `approvals.architecture.approved = true`. Si **no** está aprobada → **detener**: la arquitectura debe estar aprobada antes de generar infra.

### Paso 2 — Discovery de infra existente (idempotencia)

El objetivo es **NO recrear lo que ya existe**, solo crear lo que falta o modificar lo necesario.

Explorar **cada repo** de `project.json:repos` (despachar subagentes en paralelo si hay varios) buscando:

**IaC existente:**
- Carpetas `terraform/`, `bicep/`, `infra/`, `pulumi/`
- Archivos `*.tf`, `*.tfvars`, `*.bicep`, `Pulumi.yaml`, `Pulumi.*.yaml`

**Pipelines CI/CD existentes:**
- `.github/workflows/*.yml` / `*.yaml` (GitHub Actions)
- `azure-pipelines.yml` / `azure-pipelines-*.yml` (Azure Pipelines)
- `.gitlab-ci.yml` (referencia, si aplica)

Reportar lo encontrado en un resumen:

```
Discovery de infra
──────────────────
Repo {repo}:
  IaC:        {terraform/ encontrado | sin IaC}
  Pipelines:  {.github/workflows/deploy.yml | sin pipeline}
  Recursos ya declarados: {lista breve}
```

A partir del discovery, decidir por cada recurso/pipeline: **crear** (no existe), **modificar** (existe pero le falta algo del cambio) o **dejar como está** (ya cumple).

### Paso 3 — Generar / actualizar IaC

Los recursos a crear/modificar salen de la sección **"## Infraestructura Cloud"** de `architecture.md` (qué servicios, de qué nube). Generar según `iac_tool` de `project.json`:

| `iac_tool` | Salida | Notas |
|------------|--------|-------|
| `terraform` | archivos `.tf` (+ `.tfvars` por ambiente) | módulos por servicio; backend de estado remoto |
| `bicep` | archivos `.bicep` (+ `.bicepparam` por ambiente) | un módulo por recurso/grupo |
| `pulumi` | según el lenguaje del proyecto (TS/Python/Go/C#) | stacks por ambiente |
| `none` | **no genera IaC** | salta a pipelines (Paso 4), deja **nota explícita** de que la infra es manual |

**Provider (`cloud.provider`):**
- `azure` → recursos Azure (Resource Group, Function App, SQL, Key Vault, Storage, etc.)
- `gcp` → recursos GCP (Cloud Run/Functions, Cloud SQL, Secret Manager, GCS, etc.)
- `aws` → recursos AWS (Lambda, RDS, Secrets Manager, S3, IAM, etc.)
- `mixed` → generar **por proveedor**, según lo que indique `architecture.md` para cada servicio (ej. cómputo en una nube, datos en otra). Separar por carpeta/módulo por proveedor.

Regla de idempotencia: solo escribir/editar lo que el Paso 2 marcó como crear/modificar. No tocar recursos ya conformes. Parametrizar por ambiente (`dev`/`prod`) sin duplicar lógica.

### Paso 4 — Generar / actualizar pipelines CI/CD

Generar según `git_platform` de `project.json`:

| `git_platform` | Salida |
|----------------|--------|
| `github` | `.github/workflows/` (GitHub Actions) |
| `azure_devops` | `azure-pipelines.yml` (Azure Pipelines) |

**El pipeline DEBE respetar el flujo del equipo** (ver `deploy-workflow.md`), leyendo `branch_flow` de `project.json`:
- Push a la rama de **integración** (`branch_flow.integration`, default `dev`) → **gatilla deploy a DEV**.
- Merge a la rama de **producción** (`branch_flow.production`, default `master`) → **gatilla deploy a PROD**.
- **NUNCA deploy manual.** El pipeline es el único mecanismo de despliegue (nada de `func azure functionapp publish`, `terraform apply` a mano, etc.).
- Prod requiere **OK humano explícito** (environment protegido / aprobación de PR).

El pipeline debe incluir, según corresponda: validación/lint de IaC (`terraform validate`/`fmt`, `bicep build`), plan en PR, apply en push a la rama del ambiente, y el deploy de la aplicación. El `apply` real lo ejecuta el pipeline, **no** se corre a mano (ver Restricciones).

### Paso 4b — Auto-detección y configuración one-time de la plataforma de deploy

**Objetivo:** detectar automáticamente la plataforma de despliegue del proyecto y dejarla configurada/documentada **una sola vez**, para que las fases posteriores (sobre todo `karvey-deploy`, FASE 11) no tengan que re-descubrirla. Inspirado en el flujo `/setup-deploy` de gstack.

**Idempotencia (one-time):** si ya existe la configuración de deploy detectada (bloque "Plataforma de deploy" en `infra.md`, o un archivo de config de plataforma ya presente y referenciado), **no re-configurar**: solo verificar que sigue válida y reportar "ya configurada". Solo correr la detección completa cuando falta.

**Detección de plataforma** (explorar repos de `project.json:repos`, despachar subagentes si hay varios). Señales por plataforma:

| Plataforma | Señales (archivos / config) |
|------------|------------------------------|
| Fly.io | `fly.toml` |
| Render | `render.yaml` |
| Vercel | `vercel.json`, carpeta `.vercel/` |
| Netlify | `netlify.toml`, carpeta `.netlify/` |
| Heroku | `Procfile`, `app.json`, remote `heroku` |
| Azure | Function App / App Service / Static Web Apps en IaC, `azure-pipelines.yml` |
| AWS | Lambda/ECS/Amplify en IaC, `samconfig.toml`, `serverless.yml` |
| GCP | Cloud Run / App Engine en IaC, `app.yaml` |
| GitHub Actions (deploy genérico) | `.github/workflows/*deploy*.yml` |
| Custom | scripts `deploy.sh`/`Makefile` con target de deploy, u otro mecanismo propio |

Cruzar lo detectado con `cloud.provider` y `git_platform` de `project.json` (deben ser coherentes; si no, reportar la discrepancia).

**Descubrir y documentar** (lo que se pueda inferir de la config existente; lo que no, dejar marcado como `<pendiente>` sin inventar):
- **URL de producción** (dominio del proyecto en la plataforma; p. ej. `app` de `fly.toml`, `name` de Vercel, host del App Service).
- **Health check** (endpoint/comando que confirma que el deploy quedó sano; p. ej. `GET /health`, ruta de readiness).
- **Comandos de deploy** por ambiente (el que ejecuta el pipeline, p. ej. `flyctl deploy`, `vercel deploy --prod`), recordando que el deploy real lo gatilla el **pipeline**, nunca un run manual (ver `deploy-workflow.md` y Restricciones).

**Dejar configurado/documentado:**
- En `infra.md`, agregar/actualizar el bloque **"## Plataforma de deploy"** con: plataforma detectada, URL de producción, health check, comandos de deploy por ambiente, y mapeo al `branch_flow` (dev/prod).
- En los **pipelines** (Paso 4): reflejar la plataforma detectada (acción/step de deploy correspondiente, health check post-deploy si aplica) sin duplicar lo ya presente.

**Agnosticismo de target (ver `../karvey/rules/targets.md`):** el **canal de release depende del target**, no se asume "web" por defecto. Según `targets` de `project.json`, la plataforma/canal de deploy puede ser: pipeline web, **App Store/TestFlight** (iOS), **Play Store** (Android), **package registry** (`library`/`sdk`), **OTA** (`embedded`), etc. La detección y la configuración deben corresponder al target real; si hay varios targets, documentar el canal de cada uno.

Formato del bloque a escribir en `infra.md`:

```markdown
## Plataforma de deploy
- Plataforma:        {fly.io | render | vercel | netlify | heroku | azure | aws | gcp | github-actions | custom}
- Target / canal:    {web pipeline | App Store/TestFlight | Play Store | package registry | OTA | ...}
- URL producción:    {url | <pendiente>}
- Health check:      {endpoint o comando | <pendiente>}
- Comando deploy:    dev → {comando}  ·  prod → {comando}  (ejecutado por pipeline)
- Estado:            {recién configurada | ya configurada (verificada)}
```

### Paso 5 — Revisión de seguridad de infra (gate)

Generar un **checklist de hallazgos** revisando:

- **IAM / roles con mínimo privilegio**: cada identidad (service principal, managed identity, service account, IAM role) tiene solo los permisos que necesita; nada de `Owner`/`*:*`/`roles/owner` salvo justificación explícita.
- **Secretos en gestor de secretos**: Azure Key Vault / GCP Secret Manager / AWS Secrets Manager. **NUNCA hardcodeados** en `.tf`/`.bicep`/YAML ni en variables de pipeline en claro. Referenciar por nombre/ID.
- **Exposición de red**: **nada público** salvo que `architecture.md` lo justifique. Bases de datos y backends sin IP pública por defecto; reglas de firewall/NSG/Security Group restrictivas.
- **Cifrado en reposo y en tránsito**: storage/BD con cifrado en reposo; TLS obligatorio en tránsito (HTTPS, conexiones cifradas a BD).
- **Security Tier**: el `security_tier` de `spec.json` se respeta **a nivel infra** (ver `security-tiers.md`); a mayor tier, controles más estrictos (segmentación de red, secretos rotados, logging/auditoría, etc.).

Formato del checklist:

```markdown
## Revisión de seguridad de infra
| Control | Estado | Severidad | Hallazgo / acción |
|---------|--------|-----------|-------------------|
| IAM mínimo privilegio | OK / Falla | — / Alta | {detalle} |
| Secretos en gestor | OK / Falla | — / Crítica | {detalle} |
| Sin exposición pública | OK / Falla | — / Alta | {detalle} |
| Cifrado reposo/tránsito | OK / Falla | — / Media | {detalle} |
| Security Tier respetado | OK / Falla | — / Alta | {detalle} |
```

**Gate:** los hallazgos **críticos y altos deben resolverse** antes de continuar (corregir el IaC/pipeline y re-revisar). Hallazgos medios/bajos se documentan en `infra.md`.

### Paso 6 — Restricciones duras (aplica durante todos los pasos)

- **NUNCA aplicar a PRODUCCIÓN** (`terraform apply` / `az deployment ... create` / `pulumi up` contra prod) sin **OK humano explícito**.
- Para **DEV**, se puede aplicar **solo si el usuario lo aprueba** en este flujo. Si no aprobó, dejar el IaC listo y que el pipeline lo aplique.
- El **apply real preferentemente lo hace el pipeline**, no a mano (ver `deploy-workflow.md`).
- **Zero downtime obligatorio**: ningún cambio de infra puede provocar caída del servicio.

### Paso 7 — CHANGELOG

Todo IaC/pipeline generado o modificado **debe registrar entrada** en el `CHANGELOG.md` del repo correspondiente, según `changelog-policy.md`:
- En la raíz de **cada repo** de `project.json:repos` que recibió cambios de infra/pipeline.
- Formato *Keep a Changelog* + bloque de trazabilidad con **humano responsable** (de `git config user.*`), **modelo de IA**, el "por qué" (no solo el qué), `change-id` y `Fase Karvey: infra`.

### Paso 8 — Gestión

Registrar en la gestión del proyecto, leyendo `management` de `spec.json`:
- `management = clickup` → crear tasks con prefijo `[Infra]` por recurso/pipeline relevante.
- `management = markdown` → agregar entradas en `PLAN.md` con el estado de la infra y pipelines por repo/ambiente.

### Paso 9 — Escribir salida y actualizar spec.json

Escribir la salida del cambio:

```
docs/spec/changes/{change-id}/infra.md
```

`infra.md` documenta:
- **Recursos** creados/modificados/conformes (por proveedor y ambiente).
- **Pipelines** CI/CD generados y su mapeo al `branch_flow` (dev/prod).
- **Plataforma de deploy** (el bloque del Paso 4b: plataforma detectada, URL de producción, health check, comandos de deploy y canal de release por target).
- **Revisión de seguridad** (el checklist del Paso 5 con hallazgos y resoluciones).
- Notas de idempotencia (qué se reutilizó) y, si `iac_tool = none`, la nota de infra manual.

Actualizar `spec.json`:
- `phase: "infra-generated"`
- `approvals.infra.generated: true`

Tras presentación/aprobación (auto-aprobar si flag `-y`; si no, presentar resumen y pedir aprobación):
- `approvals.infra.approved: true`
- `phase: "infra-approved"`

### Paso 10 — Knowledge sync

Al final, ejecutar el paso de sincronización según `rules/knowledge-sync.md`:
- Si `knowledge_sync = "obsidian"` → sincronizar `infra.md` al vault vía MCP de Obsidian (con fallback a graphify si falla).
- Si `knowledge_sync = "graphify"` → `/graphify docs/spec/ --update` (o `/graphify docs/spec/` si `graphify-out/` no existe).
- Multi-repo con cambios de código de infra → graphify también en los repos afectados.

### Paso 11 — Output final

Confirmar y mostrar el siguiente paso:

```
✅ Infra generada y aprobada

Siguiente paso:
/karvey-tasks {change-id}
```

## Safety

Gates duros que **NUNCA** se saltan:

- **No prod sin OK humano**: jamás aplicar IaC ni deployar a producción sin aprobación humana explícita. El deploy real lo gatilla el pipeline (push a `dev`, merge a `master`), nunca un apply manual (ver `deploy-workflow.md`).
- **No secretos hardcodeados**: ningún secreto en `.tf`/`.bicep`/Pulumi/YAML ni en variables de pipeline en claro. Todo via Key Vault / Secret Manager / Secrets Manager.
- **Idempotencia**: nunca recrear infra existente; solo crear lo que falta o modificar lo necesario. Respetar el discovery del Paso 2.
- **Zero downtime**: ningún cambio de infra puede provocar caída del servicio.
- **Gate de seguridad**: hallazgos críticos/altos del Paso 5 bloquean el avance hasta resolverse.


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Tasks ahora?»
- Si confirma → ejecutá `/karvey-tasks {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
