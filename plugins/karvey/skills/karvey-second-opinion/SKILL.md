---
name: karvey-second-opinion
description: Independent cross-model code review for the Karvey method. Get an adversarial second opinion from a different AI model (e.g. Claude vs GPT/Codex/Gemini). Three modes: Review (PASS/FAIL), Challenge (adversarial), Consult. Triggers include "karvey second opinion", "segunda opinión", "cross-model review", "revisión independiente", "codex", "otro modelo".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [--mode review|challenge|consult] [<archivo o diff>]
---

# Karvey — Second Opinion (revisor cross-model)

## Propósito

Esta es una **skill transversal** del Método Karvey: una **capa de apoyo, NO una fase**. No cambia el `spec.json:phase` ni hace avanzar el flujo del método. Se puede invocar en cualquier momento sin alterar el estado del proyecto Karvey.

El objetivo es obtener una **segunda opinión independiente cross-model**: pedirle a un modelo de IA *distinto* al actual (por ejemplo Claude revisando trabajo de GPT/Codex/Gemini, o viceversa) que mire el mismo código con ojos frescos. La diversidad de modelo atrapa fallas que un solo modelo, por sus propios sesgos y puntos ciegos, no logra ver por sí mismo.

Es especialmente útil **antes de liberar algo sensible**: cambios en producción, lógica de seguridad, manejo de datos, migraciones, o cualquier cosa de alto impacto donde un solo par de ojos no basta.

Inspirado en el patrón `/codex` de gstack: invocar a un revisor externo para contrastar.

### Lo que esta skill NO hace

- **NO reemplaza el gate de seguridad de `karvey-qa`.** Es un complemento. El veredicto de esta skill por sí solo NO aprueba nada para liberación.
- **NO avanza la fase** del Método Karvey ni modifica `spec.json`.
- **NO es autoridad final**: es una entrada más para la decisión humana.

## Modos

| Modo | Qué hace | Cuándo usarlo |
|------|----------|---------------|
| **Review** | Revisión estructurada con veredicto **PASS / FAIL** y lista de hallazgos priorizados. | Antes de liberar; chequeo de calidad estándar. |
| **Challenge** | Revisión **adversarial**: el modelo externo intenta activamente refutar, romper o encontrar el caso límite que tumba la solución. | Cuando algo "parece bien" pero el costo de equivocarse es alto. |
| **Consult** | Conversación abierta, sin veredicto. Preguntas de diseño, trade-offs, alternativas. | Exploración, dudas de arquitectura, comparar enfoques. |

Modo por defecto si no se especifica: **Review**.

## Pasos

### 1. Identificar el diff / archivos a revisar

Determinar el alcance exacto de la revisión:

- Si el usuario pasó un archivo o ruta como argumento → ese es el alcance.
- Si no, obtener el diff actual del trabajo en curso:
  ```bash
  git diff
  git diff --staged
  git diff origin/dev...HEAD   # o la rama base que corresponda
  ```
- Reunir el contexto mínimo necesario: el diff, los archivos tocados, y el requisito/objetivo que el código debe cumplir (leer `spec.json` o la tarea Karvey si existe).

### 2. Invocar un modelo distinto al actual

La clave es **diversidad de modelo**. Detectar qué hay disponible y degradar con elegancia:

1. **CLI externo de otro modelo** (preferido). Detectar si existe en el sistema:
   ```bash
   command -v codex   2>/dev/null && echo "codex disponible"
   command -v gemini  2>/dev/null && echo "gemini disponible"
   command -v llm     2>/dev/null && echo "llm disponible"
   ```
   Si hay uno disponible, invocarlo pasándole el diff/contexto y el prompt según el modo. Esto da una opinión genuinamente cross-model.

2. **Degradación con elegancia (fallback)**: si NO hay ningún CLI de otro modelo accesible, usar un subagente (`Agent`) con un **prompt adversarial explícito** que lo instruya a actuar como revisor independiente y escéptico — explícitamente buscando lo que el autor original pasó por alto. Dejar claro en el reporte que fue un fallback intra-modelo (misma familia de modelo), por lo que la diversidad real es menor.

El prompt al revisor externo debe incluir, según el modo:
- **Review**: "Eres un revisor independiente. Evalúa este cambio contra el requisito. Entrega veredicto PASS o FAIL y hallazgos priorizados (bloqueante / mayor / menor)."
- **Challenge**: "Eres un revisor adversarial. Tu trabajo es intentar romper esta solución: encuentra casos límite, supuestos frágiles, condiciones de carrera, fallas de seguridad o de datos. Asume que hay un bug y búscalo."
- **Consult**: "Conversemos abiertamente sobre este diseño. ¿Qué trade-offs ves? ¿Qué alternativas considerarías?"

### 3. Consolidar y comparar con el review propio

- Tomar los hallazgos del modelo externo.
- Contrastarlos con la revisión propia (la del modelo actual).
- Clasificar cada punto en: **coincidencias** (ambos modelos lo ven), **discrepancias** (uno sí, otro no), y **nuevos hallazgos** que solo el modelo externo levantó.

### 4. Reportar

Entregar un reporte claro con:
- **Modo usado** y **qué modelo externo** se invocó (o si fue fallback intra-modelo).
- **Veredicto** (en modos Review/Challenge): PASS / FAIL — recordando que NO es aprobación de liberación por sí solo.
- **Coincidencias**: hallazgos donde ambos modelos concuerdan (alta confianza).
- **Discrepancias**: dónde difieren las opiniones, con el porqué de cada postura.
- **Nuevos hallazgos**: lo que solo el segundo modelo detectó.
- **Recomendación**: qué llevar de vuelta al gate de `karvey-qa` y a la decisión humana.

## Recordatorio final

Esta skill **complementa, no reemplaza** el gate de seguridad de `karvey-qa`. Una segunda opinión favorable no autoriza una liberación: el gate de QA y la aprobación humana siguen siendo obligatorios. Y esta skill **nunca avanza la fase** del Método Karvey.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
