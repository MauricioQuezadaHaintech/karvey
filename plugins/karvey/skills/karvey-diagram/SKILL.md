---
name: karvey-diagram
description: Diagram maker for the Karvey method. Natural language in, diagram out — mermaid source + editable .excalidraw + rendered SVG/PNG. Offline-friendly. Triggers include "karvey diagram", "diagrama", "mermaid", "excalidraw", "diagrama de flujo", "diagrama de arquitectura".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [diagram description] [--type flow|sequence|architecture|er]
---

# karvey-diagram

## Purpose

A **cross-cutting** skill of the Karvey Method — it is a **support layer**, NOT a phase. **It does not change `spec.json:phase`** nor advance the method's flow. Its only job is to turn a natural-language description into an **editable and rendered** diagram.

Inspired by gstack's `/diagram`: natural language in, diagram out (mermaid source + editable `.excalidraw` + rendered SVG/PNG). Designed to work **offline-friendly**: if no render tool is available, it degrades cleanly to source-only.

It is especially useful as support for:
- **karvey-architecture** — architecture and data-flow diagrams.
- **docs** in general — any document of the change that needs a diagram.

## When to use it

When the user asks for a diagram: "flow diagram", "architecture diagram", "make me a mermaid", "export this to excalidraw", etc. It can be invoked at any point of the Karvey cycle without altering the phase state.

## Steps

1. **Understand what is to be diagrammed.**
   - Read the user's natural-language description (and the `--type` if passed).
   - If the context lives in the repo (spec, architecture docs, code), use Read/Glob/Grep to understand entities, components, flows and relationships before drawing.
   - Infer the diagram type if not specified: `flow` (flow/process), `sequence` (sequence/interaction), `architecture` (components/data flow), `er` (entity-relationship / data model).

2. **Generate the mermaid source.**
   - Produce the correct mermaid block for the chosen type (`flowchart`, `sequenceDiagram`, `erDiagram`, etc.).
   - Keep names clear and consistent with the change's spec/architecture.
   - This is the minimum guaranteed output — it is always delivered, even if there is no render.

3. **(Optional) Editable `.excalidraw` version.**
   - If the user wants to edit it by hand or present it, also generate an `.excalidraw` file (Excalidraw JSON) equivalent to the diagram.
   - If a mermaid→excalidraw conversion tool is available, use it; if not, build a simple `.excalidraw` with the main nodes and edges.

4. **Render to SVG/PNG if a tool is available (detect; degrade if not).**
   - Detect render tools, in order of preference: `mmdc` (mermaid-cli) → `npx @mermaid-js/mermaid-cli` → equivalent container/local.
   - Check availability before invoking (e.g. `command -v mmdc`). If there is network/tool, render `SVG` (preferred for being vectorial) and/or `PNG`.
   - **Offline-friendly degradation:** if there is no render tool at all, do NOT fail — deliver the mermaid source (and the `.excalidraw` if requested) and explicitly indicate that the render is pending and how to generate it locally.

5. **Save in the correct location.**
   - If the change is active, save in `docs/spec/changes/{change-id}/` (next to the change's spec/docs).
   - If a change-id does not apply, save where the context corresponds (relevant docs/architecture folder).
   - Name descriptively: `<name>.mmd`, `<name>.excalidraw`, `<name>.svg` / `<name>.png`.

## Important

- **It does not advance the phase.** This skill never writes nor modifies `spec.json:phase` nor the state of the Karvey Method. It is pure visualization support.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
