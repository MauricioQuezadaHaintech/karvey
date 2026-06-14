---
name: karvey-diagram
description: Diagram maker for the Karvey method. Natural language in, diagram out — mermaid source + editable .excalidraw + rendered SVG/PNG. Offline-friendly. Triggers include "karvey diagram", "diagrama", "mermaid", "excalidraw", "diagrama de flujo", "diagrama de arquitectura".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [descripción del diagrama] [--type flow|sequence|architecture|er]
---

# karvey-diagram

## Propósito

Skill **transversal** del Método Karvey — es una **capa de apoyo**, NO una fase. **No cambia `spec.json:phase`** ni hace avanzar el flujo del método. Su único trabajo es convertir una descripción en lenguaje natural en un diagrama **editable y renderizado**.

Inspirada en el `/diagram` de gstack: lenguaje natural entra, diagrama sale (fuente mermaid + `.excalidraw` editable + SVG/PNG renderizado). Pensada para funcionar **offline-friendly**: si no hay herramienta de render disponible, degrada limpiamente a solo-fuente.

Es especialmente útil como apoyo de:
- **karvey-architecture** — diagramas de arquitectura y de flujo de datos (data flow).
- **docs** en general — cualquier documento del change que necesite un diagrama.

## Cuándo usarla

Cuando el usuario pide un diagrama: "diagrama de flujo", "diagrama de arquitectura", "hazme un mermaid", "exporta esto a excalidraw", etc. Puede invocarse en cualquier momento del ciclo Karvey sin alterar el estado de la fase.

## Pasos

1. **Entender qué se quiere diagramar.**
   - Leer la descripción en lenguaje natural del usuario (y el `--type` si lo pasó).
   - Si el contexto vive en el repo (spec, docs de arquitectura, código), usar Read/Glob/Grep para entender entidades, componentes, flujos y relaciones antes de dibujar.
   - Inferir el tipo de diagrama si no se especificó: `flow` (flujo/proceso), `sequence` (secuencia/interacción), `architecture` (componentes/data flow), `er` (entidad-relación / modelo de datos).

2. **Generar la fuente mermaid.**
   - Producir el bloque mermaid correcto para el tipo elegido (`flowchart`, `sequenceDiagram`, `erDiagram`, etc.).
   - Mantener nombres claros y consistentes con la spec/arquitectura del change.
   - Esta es la salida mínima garantizada — siempre se entrega, aunque no haya render.

3. **(Opcional) Versión `.excalidraw` editable.**
   - Si el usuario quiere editar a mano o presentar, generar también un archivo `.excalidraw` (JSON Excalidraw) equivalente al diagrama.
   - Si existe una herramienta de conversión mermaid→excalidraw disponible, usarla; si no, construir un `.excalidraw` simple con los nodos y aristas principales.

4. **Renderizar a SVG/PNG si hay herramienta disponible (detectar; degradar si no).**
   - Detectar herramientas de render, en orden de preferencia: `mmdc` (mermaid-cli) → `npx @mermaid-js/mermaid-cli` → contenedor/local equivalente.
   - Comprobar disponibilidad antes de invocar (p. ej. `command -v mmdc`). Si hay red/herramienta, renderizar `SVG` (preferido por ser vectorial) y/o `PNG`.
   - **Degradación offline-friendly:** si no hay ninguna herramienta de render, NO fallar — entregar la fuente mermaid (y el `.excalidraw` si se pidió) e indicar explícitamente que el render quedó pendiente y cómo generarlo localmente.

5. **Guardar en la ubicación correcta.**
   - Si el change está activo, guardar en `docs/spec/changes/{change-id}/` (junto a la spec/docs del change).
   - Si no aplica un change-id, guardar donde corresponda al contexto (carpeta de docs/arquitectura relevante).
   - Nombrar de forma descriptiva: `<nombre>.mmd`, `<nombre>.excalidraw`, `<nombre>.svg` / `<nombre>.png`.

## Importante

- **No avanza la fase.** Esta skill nunca escribe ni modifica `spec.json:phase` ni el estado del Método Karvey. Es puro apoyo de visualización.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
