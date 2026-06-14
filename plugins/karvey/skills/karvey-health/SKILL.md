---
name: karvey-health
description: Code quality dashboard for the Karvey method. Wraps type checker, linter, tests and dead-code detection into a weighted 0-10 score; tracks the trend over time. Triggers include "karvey health", "salud del código", "calidad de código", "quality score", "health dashboard".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [<repo o ruta>]
---

# karvey-health — Dashboard de calidad de código

Skill **transversal** del Método Karvey. Es una **capa de apoyo, NO una fase**: se puede invocar en cualquier momento del ciclo y **NO modifica** `spec.json:phase` ni hace avanzar el método. Inspirado en el `/health` de gstack.

## Propósito

Entregar una **métrica continua y comparable de salud del código** por repo: un score único 0–10 que resume el estado del type checker, el linter, los tests y la detección de código muerto, junto con su **tendencia en el tiempo** y recomendaciones priorizadas para subir el puntaje.

El objetivo es que cualquier persona del equipo pueda preguntar "¿cómo está la salud del repo?" y obtener una respuesta objetiva, repetible y comparable entre ejecuciones.

## Cuándo se usa

- A demanda, cuando el usuario pide "karvey health", "salud del código", "calidad de código", "quality score" o "health dashboard".
- Como chequeo de apoyo antes o después de cualquier fase (requisitos, diseño, implementación, test, deploy), sin alterar el estado de la fase.
- En cualquier repo, **agnóstico de stack**.

## Pasos

### 1. Detectar el stack y las herramientas disponibles

Inspeccionar el repo (o la ruta del argumento `[<repo o ruta>]`; si no se pasa, usar el repo actual) para identificar lenguaje, gestor de paquetes y las herramientas de calidad disponibles. **Agnóstico de stack** — detectar por archivos de configuración y manifiestos, no asumir un lenguaje:

- **Type checker**: `tsc`/TypeScript (`tsconfig.json`), `mypy`/`pyright` (Python), `go vet`/compilador (Go), `flow`, etc.
- **Linter**: `eslint`, `biome`, `ruff`/`flake8`/`pylint` (Python), `golangci-lint`, `clippy` (Rust), etc.
- **Test runner**: `vitest`/`jest` (JS/TS), `pytest` (Python), `go test`, `cargo test`, etc.
- **Dead-code detector**: `knip`/`ts-prune` (JS/TS), `vulture` (Python), `deadcode`/`staticcheck` (Go), `cargo-udeps` (Rust), etc.

Registrar qué herramientas existen realmente. Una herramienta ausente **no penaliza** el score: se excluye y su peso se redistribuye entre las dimensiones disponibles.

### 2. Ejecutar las herramientas

Correr cada herramienta disponible en modo no destructivo (solo lectura/análisis, sin auto-fix), capturando:

- **Type checker**: número de errores de tipos.
- **Linter**: número de errores y warnings.
- **Tests**: pasados/fallidos y, si está disponible, cobertura.
- **Dead-code**: cantidad de símbolos/exports/archivos no usados.

Usar timeouts razonables y degradar con gracia: si una herramienta falla por configuración (no por el código), marcarla como "no evaluable" y excluirla del cómputo en vez de asignar 0.

### 3. Computar un score ponderado 0–10

Cada dimensión produce un sub-score 0–10. Pesos por defecto (ajustables según las herramientas presentes):

| Dimensión        | Peso | Sub-score 10 cuando… |
|------------------|------|----------------------|
| Type checker     | 0.30 | 0 errores de tipos   |
| Tests            | 0.30 | 100% pasan (bonus por cobertura) |
| Linter           | 0.25 | 0 errores; warnings descuentan poco |
| Dead-code        | 0.15 | 0 código muerto      |

`score_global = Σ (sub_score_i × peso_i) / Σ pesos_disponibles`, redondeado a 1 decimal.

Si una dimensión no tiene herramienta, su peso se reparte proporcionalmente entre las demás (renormalizar). Documentar en el reporte qué pesos efectivos se usaron.

Bandas de interpretación: **9–10** excelente · **7–8.9** sano · **5–6.9** atención · **<5** crítico.

### 4. Registrar el resultado para seguimiento de tendencia

Guardar un **historial pequeño** (append-only) del score y su desglose, para poder comparar entre ejecuciones. Ubicación preferida, en orden:

1. `docs/spec/health-history.json` (o `.jsonl`) dentro del repo, si existe la estructura `docs/spec/` del método.
2. Si no, un archivo de métricas del repo: `.karvey/health-history.jsonl`.

Cada registro incluye: timestamp (hora Chile), score global, sub-scores por dimensión, conteos crudos (errores de tipos, lint errors/warnings, tests pass/fail, cobertura, dead-code), commit/branch si está disponible, y los pesos efectivos usados. Append, nunca sobrescribir, para preservar la serie histórica.

### 5. Reportar score + desglose + tendencia + recomendaciones

Entregar un dashboard claro:

- **Score global 0–10** con su banda de interpretación.
- **Desglose por dimensión**: sub-score, peso efectivo y conteo crudo.
- **Tendencia**: comparación contra la ejecución anterior (Δ del score) y mini-serie de los últimos N registros (flecha ↑/↓/→).
- **Recomendaciones priorizadas**: las acciones de mayor impacto primero (p. ej. "resolver 12 errores de tipos sube el score ~1.2 pts"), ordenadas por ganancia esperada vs. esfuerzo.

## Multi-repo

Si existe `project.json` con una lista `repos`, correr la evaluación **por cada repo** y entregar:

- Un dashboard por repo (score, desglose, tendencia, recomendaciones).
- Un **resumen consolidado** del proyecto: promedio (o ponderado) de scores, repos en banda crítica destacados primero, y tendencia agregada.

Mantener un historial independiente por repo (paso 4) para que las tendencias no se mezclen.

## Límites

- **NO** avanza ni modifica la fase: no toca `spec.json:phase`.
- **NO** aplica auto-fix ni modifica código: es solo medición y reporte.
- No es una fase del método; es una capa de apoyo invocable en cualquier momento.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
