---
name: karvey-retro
description: Team-aware retrospective for the Karvey method. Per-person breakdowns, shipping streaks, test-health trends, and growth opportunities from commit history and work patterns. Triggers include "karvey retro", "retrospectiva", "retro semanal", "velocity", "qué mejorar", "review de equipo".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [--since <fecha/rango>] [<repo>]
---

# Karvey Retro — Retrospectiva de equipo

## Propósito

**Skill TRANSVERSAL del Método Karvey.** Es una capa de apoyo, **NO una fase**: no cambia `spec.json:phase` ni hace avanzar el ciclo. Se puede invocar en cualquier momento sin alterar el estado del proyecto.

Inspirada en `gstack /retro`, su objetivo es **aprender del ciclo a nivel equipo y persona, para mejorar**. Mira el historial de trabajo (commits, autores, frecuencia, salud de tests) y produce una retrospectiva con desglose por persona, rachas de entregas, tendencias y oportunidades concretas de crecimiento.

El foco es **constructivo, orientado a la mejora — nunca a la culpa**. Respeta la privacidad de las personas: el tono es de aprendizaje, no de evaluación punitiva.

## Pasos

### 1. Analizar el historial git

Recorrer los repos declarados en `project.json:repos` y extraer la actividad del rango pedido (por defecto el último ciclo / la última semana; respetar `--since` si se entrega).

- Commits por autor, frecuencia y distribución temporal.
- Archivos/áreas tocadas por cada persona.
- Tamaño de los cambios (líneas agregadas/eliminadas) como señal de magnitud, no como métrica de productividad.

```bash
# Por cada repo en project.json:repos
git -C <repo> log --since="<rango>" --pretty='%an|%ad|%s' --date=short --no-merges
git -C <repo> shortlog -sne --since="<rango>" --no-merges
```

### 2. Cruzar con salud de tests y avance de spec/docs

- Apoyarse en **karvey-health** (si está disponible) para la tendencia de salud de tests del ciclo.
- Cruzar la actividad con el avance reflejado en `docs/` y en la spec (qué requisitos/tareas se cerraron, qué quedó pendiente).
- Buscar señales: tests que se rompieron y se arreglaron, áreas frágiles, deuda que reaparece ciclo a ciclo.

### 3. Generar el desglose

Producir, a partir de los datos anteriores:

- **Por persona:** en qué trabajó, su racha de entregas (shipping streak), su tendencia respecto a ciclos previos.
- **Rachas de entregas:** continuidad y consistencia del envío de trabajo del equipo.
- **Tendencias:** salud de tests subiendo/bajando, velocidad, foco vs. dispersión.
- **Oportunidades de crecimiento:** áreas donde cada persona/equipo puede mejorar, en lenguaje de apoyo.

### 4. Presentar el retro con acciones concretas

Entregar la retrospectiva con:

- Resumen del ciclo (qué salió bien, qué costó).
- Desglose por persona y por equipo.
- **Acciones concretas** y accionables para el próximo ciclo (no generalidades).
- Tono constructivo en todo momento.

## Enganche con el ciclo

Esta skill **se puede enganchar al cierre de ciclo en karvey-archive (FASE 12)** como paso de aprendizaje del ciclo. Aun así, **no avanza la fase**: `spec.json:phase` permanece intacto antes y después de ejecutar la retro.

## Privacidad y tono

- Foco en **mejora, no en culpa**.
- Lenguaje constructivo; las métricas son señales para conversar, no para rankear personas.
- No exponer datos sensibles más allá de lo necesario para la retrospectiva del equipo.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
