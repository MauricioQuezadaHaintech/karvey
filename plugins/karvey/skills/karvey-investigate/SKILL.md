---
name: karvey-investigate
description: Systematic root-cause debugging for the Karvey method. Iron Law — no fixes without investigation first. Traces data flow, forms and tests hypotheses, stops after repeated failures. Triggers include "karvey investigate", "investigar bug", "root cause", "depurar", "por qué falla", "debugging".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [descripción del síntoma]
---

# Karvey Investigate — Root-Cause Analysis

## Propósito

Skill **transversal** del Método Karvey: una capa de apoyo de depuración y análisis de causa raíz (rol Debugger, inspirado en gstack `/investigate`). **NO es una fase del pipeline lineal**: no modifica `spec.json:phase` ni avanza el flujo de fases. Se invoca en cualquier momento que aparezca un síntoma, bug o comportamiento inesperado, y al terminar el pipeline continúa exactamente donde estaba.

**Iron Law:** NUNCA aplicar fixes sin investigar primero la causa raíz. La investigación produce evidencia y una recomendación; el fix lo aplica `karvey-impl`, respetando los gates correspondientes.

Es **agnóstica de stack**: usa el runtime real del target (ver `karvey/rules/targets.md`), sea Python/Azure Functions, Vue, SQL Server, Node-RED, Asterisk, etc.

## Pasos

1. **Capturar el síntoma exacto y cómo reproducirlo.**
   - Anotar el comportamiento observado vs. el esperado, mensaje de error literal, stack trace, código de salida, y los pasos mínimos para reproducir.
   - Si no hay repro confiable, conseguir uno antes de seguir. Sin repro no hay investigación seria.

2. **Trazar el data flow / camino del código relevante.**
   - Usar Grep/Glob para localizar el punto de entrada y seguir el flujo de datos hasta el síntoma.
   - Leer (Read) los archivos involucrados de punta a punta del camino: entrada → transformaciones → salida.
   - Identificar las fronteras (llamadas a SP, webhooks, APIs externas, colas/eventos) donde el dato puede corromperse o perderse.

3. **Formular hipótesis explícitas.**
   - Escribir cada hipótesis como una afirmación falsable: "X falla porque Y".
   - Priorizar por probabilidad y por costo de verificación (verificar primero lo barato y lo más probable).

4. **Testear cada hipótesis con evidencia.**
   - Confirmar o descartar con evidencia concreta: logs, prints/trazas temporales, queries de lectura, inspección de estado, y **reproducción en el runtime real del target** (ver `karvey/rules/targets.md`).
   - Cada hipótesis se cierra con un veredicto: confirmada / descartada, y la evidencia que lo respalda.
   - No mezclar varios cambios de diagnóstico a la vez: cambiar una variable por vez para no contaminar la señal.

5. **Detenerse tras ~3 intentos fallidos.**
   - Si tras ~3 ciclos de hipótesis-test no se llega a la causa raíz, **parar y pedir ayuda** en vez de seguir a ciegas o disparar fixes especulativos.
   - Reportar lo descartado, lo aún incierto y qué información o acceso falta para avanzar.

6. **Reportar causa raíz con evidencia y recomendación de fix.**
   - Entregar: causa raíz identificada, evidencia que la sustenta, alcance del impacto, y la recomendación de fix.
   - **No aplicar el fix aquí.** El fix lo ejecuta `karvey-impl`, respetando los gates del método.

## Restricciones

- No avanza ni cambia la fase del pipeline (`spec.json:phase` queda intacto).
- No aplica cambios de corrección; solo diagnostica y recomienda.
- Cambios de diagnóstico temporales (prints, trazas) deben revertirse o quedar señalados para que `karvey-impl` los limpie.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
