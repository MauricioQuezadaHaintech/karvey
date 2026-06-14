---
name: karvey-benchmark-models
description: Cross-model benchmark for the Karvey method. Side-by-side comparison of models (e.g. Claude vs GPT vs Gemini) on a skill or task — latency, tokens, cost, and optional LLM-judged quality. Triggers include "karvey benchmark models", "comparar modelos", "benchmark de modelos", "qué modelo conviene", "latencia tokens costo".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [tarea o skill] [--models <lista>]
---

# Karvey — Benchmark de Modelos (cross-model)

**Skill transversal del Método Karvey.** Es una **capa de apoyo, NO una fase.** No avanza ni modifica el ciclo del método: **nunca toca `spec.json:phase`**. Se puede invocar en cualquier momento sin alterar el estado del proyecto.

Inspirado en `gstack /benchmark-models`: comparación lado a lado de modelos (por ejemplo Claude vs GPT vs Gemini) sobre una misma skill o tarea, midiendo latencia, tokens, costo y, opcionalmente, calidad juzgada por un LLM.

## Propósito

Decidir **con datos** qué modelo conviene para una tarea o skill determinada del proyecto. En vez de elegir un modelo por intuición o costumbre, esta skill corre la misma tarea en varios modelos y entrega una tabla comparativa objetiva más una recomendación fundamentada.

Es una skill **meta / diagnóstica**: observa y mide, pero **no modifica el código del proyecto** ni produce artefactos de las fases del método. No genera commits, no cambia archivos de la solución, no avanza la fase.

## Pasos

1. **Definir la tarea y los modelos a comparar.**
   - Identificar la tarea o skill objetivo (desde el argumento o preguntando al usuario).
   - Detectar las CLIs de modelos disponibles en el entorno: `claude`, `codex`/`gpt`, `gemini`, etc.
   - Degradar con gracia: si una CLI no está accesible, excluirla del benchmark y avisar. Comparar solo los modelos realmente disponibles.

2. **Correr la misma tarea en cada modelo.**
   - Usar exactamente el mismo prompt/entrada para todos, para que la comparación sea justa.
   - Ejecutar de forma aislada por modelo y capturar la salida completa de cada uno.

3. **Medir latencia, tokens y costo.**
   - Latencia: tiempo de pared (wall-clock) de cada corrida.
   - Tokens: entrada + salida reportados por cada CLI.
   - Costo: estimar a partir de tokens y el precio vigente de cada modelo.

4. **(Opcional) Calidad juzgada por un LLM-judge.**
   - Si se requiere evaluar calidad, usar un modelo como juez para puntuar las salidas según una rúbrica acordada (precisión, completitud, formato, etc.).
   - Mantener el juez fijo y la rúbrica explícita para que las notas sean comparables.

5. **Tabla comparativa + recomendación.**
   - Presentar una tabla lado a lado: modelo, latencia, tokens, costo y (si aplica) calidad.
   - Cerrar con una recomendación clara de qué modelo conviene para esa tarea y por qué (balance costo/calidad/latencia según el objetivo).

## Recordatorios

- **No avanza la fase.** Esta skill jamás escribe `spec.json:phase` ni dispara transiciones del método.
- **No toca el código del proyecto.** Solo lee, ejecuta corridas de prueba y reporta.
- Es invocable en cualquier punto del ciclo Karvey como apoyo a la toma de decisiones.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
