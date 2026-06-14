# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/) + human/AI traceability (Karvey policy).

## [3.0.0] - 2026-06-14

### Added
- Initial publication of the **Karvey** Method as a Claude Code plugin/marketplace.
- 12-phase pipeline (0–12): grill, init, requirements, mockup, design-graphic, architecture, **infra**, tasks, impl, test, qa, **deploy**, archive.
- Cross-cutting layer of 12 support skills: investigate, second-opinion, health, browse, checkpoint, diagram, docs, guard, devex, retro, scrape, benchmark-models.
- Stack agnosticism (`targets`), PRD base, traceable EARS, blocking security gate (OWASP+STRIDE), ordered deployment with canary, semver versioning, optional hook-based enforcement (git-flow + plan-gate), persistent `goal` field.
- Shared rules: project-config, knowledge-sync, targets, deploy-workflow, changelog-policy, versioning, enforcement, support-skills (+ the previous ones).
- Apache 2.0 license, NOTICE and TRADEMARK.md ("Karvey" trademark = *Afán*, Selknam).
- Skill bodies authored in English with bilingual triggers; generated artifacts follow the project's language.

### Why
Formalize Karvey as HainTech's own stack-agnostic method, absorbing the value of Kiro and gstack, installable/versionable as a plugin (no manual copying of skills).

> 👤 Human owner: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 AI-assisted: Claude Opus 4.8
> 🔗 Karvey phase: initial publication · Apache 2.0
