---
name: karvey-docs
description: Documentation engineer for the Karvey method. Generates Diataxis docs (tutorial/how-to/reference/explanation) from code, updates stale project docs to match what shipped, and exports markdown to publication-quality PDF. Triggers include "karvey docs", "documentación", "documentation", "diataxis", "actualizar docs", "update docs", "generar documentación", "generate documentation", "exportar PDF", "export PDF", "README".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [generate | release | pdf] [<feature or file>]
---

# karvey-docs — Doc Engineer (Karvey™ Method)

## Purpose

A **cross-cutting** skill of the Karvey Method: a support layer, **NOT a phase**. It **does NOT modify** `spec.json:phase` and does not advance the flow. It can be invoked at any point in the cycle, as many times as needed.

Role: **Doc Engineer**. Inspired by `gstack /document-generate`, `/document-release`, and `/make-pdf`. Its job is to produce and maintain **project / user** documentation at publication quality.

**Critical distinction — two universes of documentation:**

| Type | What it is | Where it lives | Owned by |
|------|------------|----------------|----------|
| **PROJECT / USER docs** | Tutorials, guides, references, and explanations for whoever uses/maintains the product | Wherever the project keeps them (typically the repo's `docs/`) | **This skill** |
| **Internal method specs** | Karvey cycle artifacts (requirements, architecture, tasks, etc.) | `docs/spec/` | The rest of the Karvey skills (phases) — **NOT** this one |

This skill **never** touches `docs/spec/`. If it detects that the user wants to edit internal specs, it redirects to the corresponding phase.

Available modes (based on the first argument): `generate`, `release`, `pdf`.

---

## `generate` mode — Diataxis documentation from code

Generates (or completes) the documentation of a feature following the **Diataxis** framework, based on the code that exists in the repo. Four quadrants, distinct purposes, never mixed:

| Quadrant | Oriented to | Answers | Tone |
|----------|-------------|---------|------|
| **Tutorial** | Learning | "Walk me through it the first time" | Step by step, guaranteed result |
| **How-to (guide)** | A concrete task | "How do I achieve X?" | Recipe, assumes context |
| **Reference** | Information | "What parameters/contracts/errors does it have?" | Exhaustive, dry, exact |
| **Explanation** | Understanding | "Why does it work this way?" | Context, decisions, trade-offs |

### Steps

1. **Resolve the target.** Take the second argument (`<feature or file>`). If not provided, ask which feature to document or infer it from the latest relevant change (`git log`, `git diff`).
2. **Read the actual source code.** Use Glob/Grep/Read over the feature's files: functions, signatures, endpoints, parameters, types, errors, side effects. **The documentation describes what the code does, not what was intended.** Zero invention.
3. **Locate the destination.** Detect the project's docs folder (`docs/`, `documentation/`, etc.). If there's no convention, propose `docs/` and respect the structure already in place. **Never** write to `docs/spec/`.
4. **Decide which quadrants apply.** Not every feature needs all four. An internal utility may only need reference + explanation; a user-facing feature usually needs tutorial + how-to.
5. **Write each quadrant** respecting its tone and purpose. Real, verifiable code snippets; copy-paste commands; tables for parameters and errors.
6. **Link.** Index/README for the section with links to the generated quadrants. Maintain coherent navigation.
7. **Report** the absolute paths of each file created or modified.

---

## `release` mode — Update stale docs after the deploy

Detects and fixes stale documentation so it reflects **what was just deployed**. It's the post-release cleanup pass.

### Steps

1. **Determine the delta of what was deployed.** Review what changed: `git log` / `git diff` since the last release or tag, CHANGELOG, new/moved/deleted files.
2. **Inventory candidate docs.** Look for READMEs and project docs that likely went stale (Glob of `**/README.md`, `docs/**/*.md`). Exclude `docs/spec/`.
3. **Detect concrete staleness.** Search and cross-check against the repo's reality:
   - **File paths** mentioned that no longer exist or were moved.
   - **Command / script lists** (npm scripts, CLI, Makefile) that changed.
   - **Structure tree** of the project (`tree` blocks / folder listings) that no longer matches.
   - **Snippets and examples** that reference modified APIs/signatures.
   - **Versions, badges, links** that are broken or outdated.
4. **Update with Edit** each doc so it matches the real state. Only changes backed by the current code/structure; do not rewrite sections that are still correct.
5. **Report** a summary of which docs were updated and what staleness was fixed, with absolute paths.

---

## `pdf` mode — Export markdown to publication-quality PDF

Converts a markdown file into a PDF with professional presentation.

### Steps

1. **Resolve the input markdown** (second argument or the doc just generated).
2. **Detect available tooling** (in this order of preference): `pandoc` (with a LaTeX engine such as `xelatex`/`tectonic`), or alternatives like `md-to-pdf` / `weasyprint` / `prince`. Verify with `command -v` before using.
3. **Configure output quality:**
   - Reasonable margins and legible typography.
   - **Page numbers.**
   - **Clickable table of contents (TOC)** with internal links.
   - **Mermaid / Excalidraw diagrams rendered as vectors** (not blurry bitmaps) when the toolchain allows it.
4. **Generate the PDF** next to the markdown (or wherever the user indicates).
5. **Degrade with a warning.** If **no** PDF tool is available, **do not fail silently**: explicitly warn the user what's missing (e.g., "`pandoc` not found; install with `brew install pandoc`") and offer the best possible alternative (e.g., self-contained HTML). Never produce a degraded PDF without warning.
6. **Report** the absolute path of the PDF (or the fallback) and the tool used.

---

## Hook into the Karvey cycle

- **Does not advance the phase.** Invocable at any time without altering `spec.json:phase`.
- **Hooks into `karvey-archive` (PHASE 12):** post-release documentation is part of the closeout. After archiving, use `karvey-docs release` to bring the user docs in line with what shipped, and optionally `karvey-docs pdf` for deliverables.
- The **internal specs** (`docs/spec/`) are the responsibility of the phase skills, not this one.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
