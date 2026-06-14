---
name: karvey-docs
description: Documentation engineer for the Karvey method. Generates Diataxis docs (tutorial/how-to/reference/explanation) from code, updates stale project docs to match what shipped, and exports markdown to publication-quality PDF. Triggers include "karvey docs", "documentación", "diataxis", "actualizar docs", "generar documentación", "exportar PDF", "README".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [generate | release | pdf] [<feature o archivo>]
---

# karvey-docs — Doc Engineer (Método Karvey™)

## Propósito

Skill **transversal** del Método Karvey: capa de apoyo, **NO una fase**. **NO modifica** `spec.json:phase` ni hace avanzar el flujo. Se puede invocar en cualquier punto del ciclo, las veces que haga falta.

Rol: **Doc Engineer**. Inspirado en `gstack /document-generate`, `/document-release` y `/make-pdf`. Su trabajo es producir y mantener la documentación de **proyecto / usuario** con calidad publicable.

**Distinción crítica — dos universos de documentación:**

| Tipo | Qué es | Dónde vive | A cargo de |
|------|--------|------------|------------|
| **Docs de PROYECTO / USUARIO** | Tutoriales, guías, referencias y explicaciones para quien usa/mantiene el producto | Donde el proyecto las tenga (típicamente `docs/` del repo) | **Esta skill** |
| **Specs internas del método** | Artefactos del ciclo Karvey (requisitos, arquitectura, tareas, etc.) | `docs/spec/` | El resto de skills Karvey (fases) — **NO** esta |

Esta skill **nunca** toca `docs/spec/`. Si detecta que el usuario quiere editar specs internas, redirige a la fase correspondiente.

Modos disponibles (según el primer argumento): `generate`, `release`, `pdf`.

---

## Modo `generate` — Documentación Diataxis desde el código

Genera (o completa) la documentación de una feature siguiendo el framework **Diataxis**, a partir del código que existe en el repo. Cuatro cuadrantes, propósitos distintos, no se mezclan:

| Cuadrante | Orientado a | Responde a | Tono |
|-----------|-------------|------------|------|
| **Tutorial** | Aprendizaje | "Llévame de la mano la primera vez" | Paso a paso, resultado garantizado |
| **How-to (guía)** | Tarea concreta | "¿Cómo logro X?" | Receta, asume contexto |
| **Reference** | Información | "¿Qué parámetros/contratos/errores tiene?" | Exhaustivo, seco, exacto |
| **Explanation** | Comprensión | "¿Por qué funciona así?" | Contexto, decisiones, trade-offs |

### Pasos

1. **Resolver el objetivo.** Tomar el segundo argumento (`<feature o archivo>`). Si no se entrega, preguntar qué feature documentar o inferir desde el último cambio relevante (`git log`, `git diff`).
2. **Leer el código fuente real.** Usar Glob/Grep/Read sobre los archivos de la feature: funciones, firmas, endpoints, parámetros, tipos, errores, side effects. **La documentación describe lo que el código hace, no lo que se deseaba.** Cero invención.
3. **Ubicar el destino.** Detectar la carpeta de docs del proyecto (`docs/`, `documentation/`, etc.). Si no existe convención, proponer `docs/` y respetar la estructura ya presente. **Nunca** escribir en `docs/spec/`.
4. **Decidir qué cuadrantes aplican.** No toda feature necesita los cuatro. Una utilidad interna puede llevar solo reference + explanation; un feature de cara al usuario suele llevar tutorial + how-to.
5. **Redactar cada cuadrante** respetando su tono y propósito. Code snippets reales y verificables; comandos copy-paste; tablas para parámetros y errores.
6. **Enlazar.** Index/README de la sección con links a los cuadrantes generados. Mantener navegación coherente.
7. **Reportar** las rutas absolutas de cada archivo creado o modificado.

---

## Modo `release` — Actualizar docs stale tras el deploy

Detecta y corrige documentación desactualizada (stale) para que refleje **lo que se acaba de desplegar**. Es la pasada de saneamiento post-release.

### Pasos

1. **Determinar el delta de lo desplegado.** Revisar qué cambió: `git log` / `git diff` desde el último release o tag, CHANGELOG, archivos nuevos/movidos/borrados.
2. **Inventariar docs candidatas.** Buscar READMEs y docs de proyecto que probablemente quedaron stale (Glob de `**/README.md`, `docs/**/*.md`). Excluir `docs/spec/`.
3. **Detectar staleness concreta.** Buscar y cotejar contra la realidad del repo:
   - **Rutas de archivos** mencionadas que ya no existen o se movieron.
   - **Listas de comandos / scripts** (npm scripts, CLI, Makefile) que cambiaron.
   - **Árbol de estructura** del proyecto (bloques de `tree`/listados de carpetas) que ya no coincide.
   - **Snippets y ejemplos** que referencian APIs/firmas modificadas.
   - **Versiones, badges, enlaces** rotos o desactualizados.
4. **Actualizar con Edit** cada doc para que coincida con el estado real. Solo cambios respaldados por el código/estructura actual; no reescribir secciones que siguen correctas.
5. **Reportar** un resumen de qué docs se actualizaron y qué staleness se corrigió, con rutas absolutas.

---

## Modo `pdf` — Exportar markdown a PDF de calidad publicable

Convierte un archivo markdown a un PDF con presentación profesional.

### Pasos

1. **Resolver el markdown de entrada** (segundo argumento o el doc recién generado).
2. **Detectar herramienta disponible** (en este orden de preferencia): `pandoc` (con motor LaTeX como `xelatex`/`tectonic`), o alternativas como `md-to-pdf` / `weasyprint` / `prince`. Verificar con `command -v` antes de usar.
3. **Configurar calidad de salida:**
   - Márgenes razonables y tipografía legible.
   - **Números de página.**
   - **Tabla de contenidos (TOC) clickeable** con enlaces internos.
   - **Diagramas Mermaid / Excalidraw renderizados como vectores** (no bitmaps borrosos) cuando la cadena de herramientas lo permita.
4. **Generar el PDF** junto al markdown (o donde indique el usuario).
5. **Degradación con aviso.** Si **no hay** herramienta de PDF disponible, **no fallar en silencio**: avisar explícitamente al usuario qué falta (ej. "no se encontró `pandoc`; instalar con `brew install pandoc`") y ofrecer la mejor alternativa posible (ej. HTML autocontenido). Nunca producir un PDF degradado sin avisar.
6. **Reportar** la ruta absoluta del PDF (o del fallback) y la herramienta usada.

---

## Enganche con el ciclo Karvey

- **No avanza la fase.** Invocable en cualquier momento sin alterar `spec.json:phase`.
- **Engancha con `karvey-archive` (FASE 12):** la documentación post-release forma parte del cierre. Tras archivar, usar `karvey-docs release` para dejar las docs de usuario alineadas con lo entregado, y opcionalmente `karvey-docs pdf` para entregables.
- Las **specs internas** (`docs/spec/`) son responsabilidad de las skills de fase, no de esta.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
