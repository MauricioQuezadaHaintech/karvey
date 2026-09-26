# Rule: Support skills (cross-cutting layer)

In addition to the 13 pipeline phases (0–12) (linear, with gates), Karvey has a **cross-cutting layer** of support skills that are invoked **at any time**, without altering the current phase. Inspired by gstack's "virtual team" philosophy, but integrated into the method.

## Catalog

| Skill | Role | When to use it | Origin (gstack) |
|-------|-----|---------------|-----------------|
| `karvey-iterate` | Iteration engine | Findings appeared (test/qa/browse) or the spec turned out wrong/incomplete. Routes each finding: `bug` → incident tracker + QA micro-loop · `spec-gap` → re-open requirements · `emergent` → discovery backlog. The one place loop logic lives. | — (Karvey feedback loop) |
| `karvey-investigate` | Debugger | Something fails and it's not understood why. **Iron Law: no fix without investigating first.** Date the symptom, ask what changed, and never report a pre-existing weakness as the cause of a new failure. | investigate |
| `karvey-second-opinion` | Cross-model reviewer | Before releasing something sensitive: adversarial review with ANOTHER model (Claude vs GPT/other). | codex |
| `karvey-judges` | Independent judges | Before the requirements, architecture and qa gates: one clean-context subagent per lens reads the phase's closed inputs and reports cited findings into `findings.md`; advisory by default, cost logged (`judges.md`). | — (Karvey) |
| `karvey-health` | Code quality | Periodic check: score 0–10 (type-check + lint + tests + dead code) with trend. | health |
| `karvey-browse` | Eyes on the runtime | Inspect/click/screenshot in the target's real runtime (browser/simulator/CLI). | browse, setup-browser-cookies |
| `karvey-checkpoint` | Work state + agent handoff | Save/restore working context (git state, decisions, WIP) **and the agent's handoff** — identity, manifest, board, checklist, measured repo state, scheduled tasks — across sessions and rotations. Works with a single agent; a team only changes where it lives. | context-save/restore |
| `karvey-diagram` | Diagrammer | Generate diagrams: text → mermaid + excalidraw + SVG/PNG. | diagram |
| `karvey-docs` | Doc Engineer | Generate Diataxis docs (tutorial/how-to/reference/explanation), update stale docs, export PDF. | document-generate/release, make-pdf |
| `karvey-guard` | Guardrails | Activate/remove enforcement hooks; edit-lock on a directory for sensitive work. | careful, freeze, guard |
| `karvey-devex` | DX Reviewer | Audit developer/onboarding experience: time-to-hello-world, friction, "docs lies". | plan-devex-review, devex-review |
| `karvey-retro` | Retrospective | Cycle closure: velocity, test health, per person, improvement opportunities. | retro |
| `karvey-scrape` | Web extractor | Extract data from a website and encode the scrape as a reusable skill. | scrape, skillify |
| `karvey-benchmark-models` | Model benchmark | Compare models (latency/tokens/cost/quality) for a skill or task. | benchmark-models |
| `karvey-import` | Migration | Convert existing Kiro (`.kiro/specs/*`) or gstack specs into Karvey's `docs/spec/` structure. Non-destructive on the source. | — |
| `karvey-team` | Team layer (**optional**) | Set up and run a team of agents (roles, manifests, boards, census, relay) and **measure what it costs**. Opt-in: Karvey is complete with one agent, and a team is expensive — read `team.md` first. | — (Karvey) |
| `karvey-decisions` | Decision log | Single numbered registry (`D-NN` business, `C-NN` direction) that changes cite; **`cross` checks a question against the log before anything is declared blocked**. | — (Karvey) |
| `karvey-context` | Dashboard (read-only) | Any time: project config, capabilities, active/archived changes, deploy queue / landing report, open backlog count and **live branches** (absorbed vs carrying unreleased work). Never writes. | — (Karvey) |
| `karvey-standards` | Standards uplift | Distill the team's engineering golden paths (db/backend/frontend…) from the **real system** into the team's standards repo (`project.json:standards`), in the `engineering-standards.md` format. Re-runnable to refresh. Never writes into the public plugin. | — (Karvey) |

## Invocation rules

- Support skills **do not advance the change's phase forward**; only phase skills call `karvey-state.py advance`. Exception: `karvey-iterate` performs the controlled **backward** transition of the spec-revision sub-cycle with `karvey-state.py reopen`, since closing the feedback loop is its whole purpose.
- They can be invoked before, during or after any phase.
- They respect the same gates: `karvey-guard`/hooks still apply; `karvey-second-opinion` does not by itself approve the `karvey-qa` security gate, it complements it.
- They do not run the knowledge sync: it runs at archive and on demand only (`knowledge-sync.md`).

## Quick equivalences (if you come from gstack)

What in gstack are standalone commands, in Karvey is **absorbed into a phase** or into this **support layer**. See the coverage table in `../SKILL.md`.
