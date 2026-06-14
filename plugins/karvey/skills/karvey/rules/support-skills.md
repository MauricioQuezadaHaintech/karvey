# Rule: Support skills (cross-cutting layer)

In addition to the 12 pipeline phases (linear, with gates), Karvey has a **cross-cutting layer** of support skills that are invoked **at any time**, without altering the current phase. Inspired by gstack's "virtual team" philosophy, but integrated into the method.

## Catalog

| Skill | Role | When to use it | Origin (gstack) |
|-------|-----|---------------|-----------------|
| `karvey-investigate` | Debugger | Something fails and it's not understood why. **Iron Law: no fix without investigating first.** | investigate |
| `karvey-second-opinion` | Cross-model reviewer | Before releasing something sensitive: adversarial review with ANOTHER model (Claude vs GPT/other). | codex |
| `karvey-health` | Code quality | Periodic check: score 0–10 (type-check + lint + tests + dead code) with trend. | health |
| `karvey-browse` | Eyes on the runtime | Inspect/click/screenshot in the target's real runtime (browser/simulator/CLI). | browse, setup-browser-cookies |
| `karvey-checkpoint` | Work state | Save/restore working context (git state, decisions, WIP) across sessions/handoffs. | context-save/restore |
| `karvey-diagram` | Diagrammer | Generate diagrams: text → mermaid + excalidraw + SVG/PNG. | diagram |
| `karvey-docs` | Doc Engineer | Generate Diataxis docs (tutorial/how-to/reference/explanation), update stale docs, export PDF. | document-generate/release, make-pdf |
| `karvey-guard` | Guardrails | Activate/remove enforcement hooks; edit-lock on a directory for sensitive work. | careful, freeze, guard |
| `karvey-devex` | DX Reviewer | Audit developer/onboarding experience: time-to-hello-world, friction, "docs lies". | plan-devex-review, devex-review |
| `karvey-retro` | Retrospective | Cycle closure: velocity, test health, per person, improvement opportunities. | retro |
| `karvey-scrape` | Web extractor | Extract data from a website and encode the scrape as a reusable skill. | scrape, skillify |
| `karvey-benchmark-models` | Model benchmark | Compare models (latency/tokens/cost/quality) for a skill or task. | benchmark-models |

## Invocation rules

- Support skills **do not advance the change's phase** (`spec.json:phase` does not change unless a phase skill does it).
- They can be invoked before, during or after any phase.
- They respect the same gates: `karvey-guard`/hooks still apply; `karvey-second-opinion` does not by itself approve the `karvey-qa` security gate, it complements it.
- When producing artifacts in `docs/spec/`, they sync knowledge according to `knowledge-sync.md`.

## Quick equivalences (if you come from gstack)

What in gstack are standalone commands, in Karvey is **absorbed into a phase** or into this **support layer**. See the coverage table in `karvey/SKILL.md`.
