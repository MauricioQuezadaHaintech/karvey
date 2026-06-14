# Regla: Skills de apoyo (capa transversal)

Además de las 12 fases del pipeline (lineal, con gates), Karvey tiene una **capa transversal** de skills de apoyo que se invocan **en cualquier momento**, sin alterar la fase actual. Inspiradas en la filosofía de "equipo virtual" de gstack, pero integradas al método.

## Catálogo

| Skill | Rol | Cuándo usarla | Origen (gstack) |
|-------|-----|---------------|-----------------|
| `karvey-investigate` | Debugger | Algo falla y no se entiende por qué. **Iron Law: no fix sin investigar primero.** | investigate |
| `karvey-second-opinion` | Revisor cross-model | Antes de liberar algo sensible: review adversarial con OTRO modelo (Claude vs GPT/otro). | codex |
| `karvey-health` | Calidad de código | Chequeo periódico: score 0–10 (type-check + lint + tests + dead code) con tendencia. | health |
| `karvey-browse` | Ojos en el runtime | Inspeccionar/clickear/screenshot en el runtime real del target (browser/simulador/CLI). | browse, setup-browser-cookies |
| `karvey-checkpoint` | Estado de trabajo | Guardar/restaurar contexto de trabajo (git state, decisiones, WIP) entre sesiones/handoffs. | context-save/restore |
| `karvey-diagram` | Diagramador | Generar diagramas: texto → mermaid + excalidraw + SVG/PNG. | diagram |
| `karvey-docs` | Doc Engineer | Generar docs Diataxis (tutorial/how-to/reference/explanation), actualizar docs stale, export PDF. | document-generate/release, make-pdf |
| `karvey-guard` | Guardrails | Activar/quitar hooks de enforcement; edit-lock a un directorio para trabajo sensible. | careful, freeze, guard |
| `karvey-devex` | DX Reviewer | Auditar experiencia de desarrollador/onboarding: time-to-hello-world, fricción, "docs lies". | plan-devex-review, devex-review |
| `karvey-retro` | Retrospectiva | Cierre de ciclo: velocity, test health, por persona, oportunidades de mejora. | retro |
| `karvey-scrape` | Extractor web | Extraer datos de una web y codificar el scrape como skill reutilizable. | scrape, skillify |
| `karvey-benchmark-models` | Benchmark de modelos | Comparar modelos (latencia/tokens/costo/calidad) para una skill o tarea. | benchmark-models |

## Reglas de invocación

- Las skills de apoyo **no avanzan la fase** del cambio (`spec.json:phase` no cambia salvo que la skill de fase lo haga).
- Pueden invocarse antes, durante o después de cualquier fase.
- Respetan los mismos gates: `karvey-guard`/hooks siguen aplicando; `karvey-second-opinion` no aprueba por sí solo el gate de seguridad de `karvey-qa`, lo complementa.
- Al producir artefactos en `docs/spec/`, sincronizan conocimiento según `knowledge-sync.md`.

## Equivalencias rápidas (si vienes de gstack)

Lo que en gstack son comandos sueltos, en Karvey está **absorbido en fase** o en esta **capa de apoyo**. Ver la tabla de cobertura en `karvey/SKILL.md`.
