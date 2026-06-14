# Karvey

> **Karvey** es una palabra **ona/selknam** que significa ***Afán***.

Método de **spec-driven development (SDD)** para Claude Code, **agnóstico de stack** (web, iOS/Android, desktop, CLI, API, embedded). Lleva un cambio desde la idea hasta producción con un pipeline de 12 fases con gates de aprobación, más una capa transversal de skills de apoyo.

Creado por **Mauricio Quezada Ibáñez** · **HainTech**. Síntesis de experiencia propia con ideas conceptuales de **Kiro** (cc-sdd) y **gstack** (Garry Tan) — inspiración conceptual, sin su código.

## Pipeline (0–12)

```
0 grill → 1 init → 2 requirements → 3 mockup → 4 design-graphic → 5 architecture
→ 6 infra → 7 tasks → 8 impl → 9 test → 10 qa → 11 deploy → 12 archive
```

Cada fase produce un documento en `docs/spec/` y pide tu OK antes de avanzar. El orquestador `/karvey:karvey <change-id>` te dice siempre en qué fase vas y cuál sigue.

## Capa transversal (skills de apoyo, invocables en cualquier momento)

`investigate` · `second-opinion` · `health` · `browse` · `checkpoint` · `diagram` · `docs` · `guard` · `devex` · `retro` · `scrape` · `benchmark-models`

## Características

- **PRD como base** + requirements EARS trazables.
- **Mockup navegable** (con modo shotgun de variantes) y **diseño** con scoring 0-10 por plataforma (WCAG/HIG/Material).
- **Arquitectura** con diagramas, edge cases, trust boundaries e **Infraestructura Cloud**.
- **IaC + pipelines CI/CD** (Terraform/Bicep/Pulumi · GitHub Actions/Azure Pipelines) con revisión de seguridad.
- **QA en 8 dimensiones** con **gate de seguridad bloqueante** (OWASP + STRIDE) y second opinion cross-model.
- **Despliegue ordenado** `feature → dev → PR master`, gatillado por pipeline, con **canary** post-deploy.
- **Versionado semver + CHANGELOG** por componente/repo, con trazabilidad humano + modelo de IA.
- **Enforcement opcional por hooks** (git-flow + plan-gate) — opt-in por proyecto.

## Instalación (como plugin de Claude Code)

```
/plugin marketplace add MauricioQuezadaHaintech/karvey
/plugin install karvey@karvey-methods
```

Luego invocá las skills namespaceadas, por ejemplo:

```
/karvey:grill            # iniciar pre-spec
/karvey:karvey <id>      # ver estado y siguiente paso
```

## Licencia y marca

Código bajo **Apache License 2.0** (ver [`LICENSE`](LICENSE) y [`NOTICE`](NOTICE)). Podés usar, modificar y adaptar `karvey-*` con atribución.

El nombre **"Karvey"** y la convención `karvey-*` son marca de **HainTech** — ver [`TRADEMARK.md`](TRADEMARK.md). Las adaptaciones deben conservar la atribución a Mauricio Quezada Ibáñez / HainTech y no implicar endoso oficial sin permiso.
