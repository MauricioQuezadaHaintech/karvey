---
name: karvey-devex
description: Developer-experience reviewer for the Karvey method. Walks the actual onboarding flow, measures time-to-hello-world, finds friction points and "docs lies". Plan-stage and live modes. Triggers include "karvey devex", "developer experience", "onboarding", "time to hello world", "fricción", "DX review".
allowed-tools: Read, Bash, Glob, Grep, Agent
argument-hint: [--mode plan|live]
---

# Karvey DevEx — DX Reviewer

> **SKILL TRANSVERSAL del Método Karvey™.** Esto es una **capa de apoyo**, NO una fase.
> NO modifica `spec.json:phase`. NO avanza el flujo del método. Se puede invocar en
> cualquier momento, las veces que sea necesario, sin alterar el estado del proyecto.

Inspirado en `gstack /plan-devex-review` + `/devex-review`.

## Propósito

Medir y mejorar la **experiencia de quien adopta o usa el proyecto** (developer experience).
El foco no es la corrección funcional del código, sino qué tan fácil, rápido y agradable es
para una persona nueva llegar desde "cero" hasta su primer resultado útil — el famoso
**time-to-hello-world (TTHW)**.

El rol es el de un **DX Reviewer**: alguien que se pone en los zapatos de quien recién
llega, recorre el camino real de onboarding y reporta cada punto de fricción, cada
"momento mágico" y cada **"mentira de la documentación"** (docs que prometen algo que la
realidad no cumple).

### Dos modos

| Modo | Cuándo | Qué hace |
|------|--------|----------|
| **`plan`** | Hay plan/arquitectura pero aún no implementación corriendo | Revisión a nivel diseño: estima el TTHW esperado, identifica fricción anticipada y los "momentos mágicos" que el diseño debería entregar. |
| **`live`** | Hay algo ejecutable (repo, instalable, servicio) | Recorre el onboarding REAL: clona, instala, ejecuta el primer "hello world", **mide el TTHW real** y detecta pasos rotos y mentiras de la documentación. |

Si no se pasa `--mode`, inferir: si hay artefacto ejecutable disponible → `live`;
si solo hay plan/spec/arquitectura → `plan`.

### Tres lentes (siempre aplicar las tres)

1. **Expansion (qué falta)** — vacíos en el camino: pasos no documentados, prerequisitos
   ocultos, configuración que nadie explicó, casos que el onboarding ignora.
2. **Polish (qué pulir)** — cosas que funcionan pero rozan: mensajes de error poco claros,
   nombres confusos, comandos largos, defaults malos, salida ruidosa, copy mejorable.
3. **Triage (qué es crítico)** — qué bloquea o aleja al adoptante: lo que hace que alguien
   abandone antes del primer éxito. Esto es lo que se arregla primero.

## Pasos

### Modo `plan`

1. **Leer el plan / arquitectura / spec** del proyecto (`spec.json`, `requirements`,
   `architecture`, READMEs de diseño, mockups). Identificar quién es el adoptante objetivo
   (¿dev interno?, ¿integrador externo?, ¿usuario final técnico?).
2. **Trazar el camino esperado** desde "descubrí el proyecto" hasta "obtuve mi primer
   resultado útil". Enumerar cada paso previsto: instalar, configurar, autenticar,
   primer comando/llamada, primer output.
3. **Estimar el TTHW esperado** y marcar dónde el diseño introduce fricción innecesaria
   (pasos manuales evitables, dependencias pesadas, configuración previa, secretos que
   conseguir).
4. **Identificar los "momentos mágicos"** que el diseño debería producir — el instante en
   que el adoptante dice "ah, esto sí sirve". Verificar que el plan los entregue temprano.
5. **Aplicar las tres lentes** (Expansion / Polish / Triage) sobre el diseño.
6. **Reportar** hallazgos priorizados con recomendaciones concretas (ver formato abajo).

### Modo `live`

1. **Partir de cero de verdad.** Simular un entorno limpio. Si es posible, usar un
   subagente (`Agent`) con instrucciones de "no asumas nada, solo sigue la documentación
   literalmente" para recorrer el onboarding sin el sesgo de quien ya conoce el proyecto.
2. **Recorrer el onboarding REAL siguiendo SOLO la documentación**, paso a paso:
   clonar → instalar → configurar → primer "hello world". **Cronometrar** desde el inicio
   hasta el primer resultado útil → ese es el **TTHW real**.
3. **Anotar cada "mentira de la documentación"**: cada vez que un comando, ruta, nombre de
   variable, salida esperada o prerequisito en los docs **no coincide con la realidad**.
   Citar el doc, el comando ejecutado y lo que realmente pasó.
4. **Registrar los pasos rotos**: comandos que fallan, dependencias faltantes, pasos
   implícitos no documentados, errores que requieren conocimiento externo para resolver.
5. **Localizar el verdadero "momento mágico"** y medir cuánto cuesta llegar a él. Si llega
   tarde o nunca, eso es Triage crítico.
6. **Aplicar las tres lentes** sobre la experiencia real vivida.
7. **Reportar** hallazgos priorizados con recomendaciones (ver formato abajo).

### Formato de reporte (ambos modos)

- **Veredicto DX** + **TTHW** (estimado en `plan`, medido en `live`).
- **Crítico (Triage)** — lo que bloquea o ahuyenta al adoptante. Arreglar primero.
- **Fricción (Polish)** — lo que roza pero no bloquea.
- **Vacíos (Expansion)** — lo que falta.
- **Mentiras de la documentación** — solo en `live`: doc vs. realidad, con cita.
- **Momentos mágicos** — dónde están y si llegan a tiempo.
- Cada hallazgo con: ubicación, impacto en el adoptante, y recomendación accionable.

## Recordatorios

- **NO avanza la fase.** No tocar `spec.json:phase` ni marcar nada como completado en el
  flujo del método. Esta skill solo observa, mide y recomienda.
- Es **read-only sobre el estado del método**: puede ejecutar comandos de onboarding en
  `live` (instalar, correr), pero no edita el código del proyecto ni su spec.
- Se puede correr cuantas veces se quiera, en cualquier fase del proyecto.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
