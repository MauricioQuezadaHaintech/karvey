# Karvey

> **Karvey** is an Ona/Selknam word meaning ***Afán*** (zeal / drive).

A **spec-driven development (SDD)** method for Claude Code, **stack-agnostic** (web, iOS/Android, desktop, CLI, API, embedded). It takes a change from idea to production through a 12-phase pipeline with approval gates, plus a cross-cutting layer of support skills.

Created by **Mauricio Quezada Ibáñez** · **HainTech**. A synthesis of first-hand experience with conceptual ideas from **Kiro** (cc-sdd) and **gstack** (Garry Tan) — conceptual inspiration, none of their code.

## Pipeline (0–12)

```
0 grill → 1 init → 2 requirements → 3 mockup → 4 design-graphic → 5 architecture
→ 6 infra → 7 tasks → 8 impl → 9 test → 10 qa → 11 deploy → 12 archive
```

Each phase produces a document under `docs/spec/` and asks for your OK before advancing. The orchestrator `/karvey:karvey <change-id>` always tells you which phase you're in and which comes next.

### A spiral, not a line — the iteration loop

The pipeline is the happy path; real work iterates. Findings from `test`/`qa`/`browse` land in `findings.md` and the **iteration engine** `/karvey:karvey-iterate` routes each one:

```
test · qa · browse → findings.md → karvey-iterate
                                      ├─ bug      → BUG-NN incident tracker → impl→test→qa micro-loop
                                      ├─ spec-gap → re-open requirements (ripple only affected phases)
                                      └─ emergent → discovery backlog → future change-id (swept at archive)
```

A change is *done* only when no open `bug`/`spec-gap` remains and every `emergent` idea is captured — so nothing gets dropped and nothing stays "in the air".

## Cross-cutting layer (support skills, invokable any time)

`iterate` · `investigate` · `second-opinion` · `health` · `browse` · `checkpoint` · `diagram` · `docs` · `guard` · `devex` · `retro` · `scrape` · `benchmark-models`

## Features

- **PRD as the base** + traceable EARS requirements.
- **Navigable mockup** (with shotgun variant mode) and **design** with 0-10 scoring per platform (WCAG/HIG/Material).
- **Architecture** with diagrams, edge cases, trust boundaries and a **Cloud Infrastructure** section.
- **IaC + CI/CD pipelines** (Terraform/Bicep/Pulumi · GitHub Actions/Azure Pipelines) with security review.
- **8-dimension QA** with a **blocking security gate** (OWASP + STRIDE) and cross-model second opinion.
- **Iteration loop** that routes findings back to their edge (`bug` / `spec-gap` / `emergent`) so the method guides you through iteration, not just the happy path.
- **Incident tracker** (`BUG-NN` with state history) per repo + a global index — complementary to ClickUp.
- **Discovery backlog** (Markdown + ClickUp) so emergent ideas become future change-ids, swept at archive.
- **Mandatory phase-close** ritual: every phase/task updates management (ClickUp comment + status + cascade) so nothing goes stale.
- **Ordered deployment** `feature → dev → PR master`, pipeline-triggered, with **canary** post-deploy.
- **Semver versioning + CHANGELOG** per component/repo, with human + AI-model traceability.
- **Optional hook-based enforcement** (git-flow + plan-gate) — opt-in per project.

## Install (as a Claude Code plugin)

```
/plugin marketplace add MauricioQuezadaHaintech/karvey
/plugin install karvey@karvey-methods
```

Then invoke the namespaced skills, for example:

```
/karvey:grill            # start pre-spec
/karvey:karvey <id>      # see status and next step
```

The skills' bodies are in English (what Claude reads), but **artifacts are generated in the project's language** (`spec.json` `language` field) and Claude replies in your language. Triggers are bilingual (English + Spanish).

## License and trademark

Code under the **Apache License 2.0** (see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE)). You may use, modify and adapt `karvey-*` with attribution.

The **"Karvey"** name and the `karvey-*` convention are trademarks of **HainTech** — see [`TRADEMARK.md`](TRADEMARK.md). Adaptations must keep attribution to Mauricio Quezada Ibáñez / HainTech and must not imply official endorsement without permission.
