# Regla: Configuración del proyecto (`project.json`)

El Método Karvey opera a dos niveles: **proyecto** (config estable, compartida por todos los cambios) y **cambio** (`spec.json` por change-id). Esta regla define la config a nivel proyecto.

## Ubicación

```
docs/spec/project.json
```

`docs/spec/` vive en el **repo principal** del proyecto (`spec_repo`). Un proyecto tiene **1 o más repos, nunca cero**. Si hay un solo repo, ese es el `spec_repo`. Si hay varios, se designa el principal/orquestador.

## Esquema

```json
{
  "project": "{nombre del proyecto}",
  "git_platform": "github | azure_devops",
  "cloud": {
    "provider": "azure | gcp | aws | mixed | none"
  },
  "iac_tool": "terraform | bicep | pulumi | none",
  "knowledge_sync": "obsidian | graphify",
  "targets": ["web", "ios", "android", "desktop", "cli", "api", "embedded"],
  "repos": ["ruta/o/nombre/repo1", "ruta/o/nombre/repo2"],
  "spec_repo": "repo-principal-donde-vive-docs-spec",
  "branch_flow": {
    "feature_prefix": "feature/",
    "integration": "dev",
    "production": "master"
  },
  "enforcement": {
    "git_flow_hook": false,
    "plan_gate_hook": false
  }
}
```

## Reglas de manejo

- **`repos`**: arreglo obligatorio con **mínimo 1** entrada. Validar al crear/leer; si viene vacío, detener y pedir al menos un repo.
- **`spec_repo`**: si `repos` tiene 1 elemento, `spec_repo` = ese repo. Si tiene varios, preguntar cuál es el principal.
- **`git_platform`**: determina qué pipelines genera `karvey-infra` (GitHub Actions vs Azure Pipelines).
- **`cloud.provider`**: `mixed` significa que se usan servicios de más de una nube; el detalle de qué servicio de qué nube se especifica en la sección "Infraestructura Cloud" de `architecture.md` por cada cambio.
- **`iac_tool`**: `none` significa que la infra se gestiona manualmente; `karvey-infra` igual genera/valida los pipelines CI/CD.
- **`knowledge_sync`**: ver `knowledge-sync.md`.
- **`targets`**: plataformas del proyecto (mínimo 1). Define cómo cada fase verifica/diseña. Ver `targets.md`. Agnóstico de stack: nunca asumir `web` por defecto.
- **`branch_flow`**: convención de ramas; respetada por `karvey-impl`, `karvey-qa` y `karvey-deploy`. Default: `feature/*` → `dev` → `master`.
- **`enforcement`**: activación (opt-in) de los hooks de `enforcement.md`. `karvey-init` pregunta y `karvey-guard` los gestiona. Default ambos `false`.

> **Nota — `goal`**: el objetivo del cambio NO vive en `project.json` sino por cambio, en `prd.md` y en `spec.json` (`"goal"`). Da el norte para perseguir el resultado sin detenerse, respetando los gates de plan y seguridad.

## Quién la crea / lee

- **Crea**: `karvey-init` (primera vez en el proyecto). Pre-poblada desde la síntesis de `karvey-grill` si existe.
- **Lee**: todas las fases. En particular `karvey-architecture` (cloud), `karvey-infra` (git_platform, cloud, iac_tool, repos), `karvey-deploy` (branch_flow, repos), y cualquier fase que sincronice conocimiento (`knowledge_sync`).

Si una fase necesita `project.json` y no existe, detener e indicar correr `karvey-init` primero.
