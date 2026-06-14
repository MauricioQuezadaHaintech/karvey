# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/) + trazabilidad humano/IA (política Karvey).

## [3.0.0] - 2026-06-14

### Added
- Publicación inicial del Método **Karvey** como plugin/marketplace de Claude Code.
- Pipeline de 12 fases (0–12): grill, init, requirements, mockup, design-graphic, architecture, **infra**, tasks, impl, test, qa, **deploy**, archive.
- Capa transversal de 12 skills de apoyo: investigate, second-opinion, health, browse, checkpoint, diagram, docs, guard, devex, retro, scrape, benchmark-models.
- Agnosticismo de stack (`targets`), PRD base, EARS trazable, gate de seguridad bloqueante (OWASP+STRIDE), despliegue ordenado con canary, versionado semver, enforcement opcional por hooks (git-flow + plan-gate), campo `goal` persistente.
- Reglas compartidas: project-config, knowledge-sync, targets, deploy-workflow, changelog-policy, versioning, enforcement, support-skills (+ las previas).
- Licencia Apache 2.0, NOTICE y TRADEMARK.md (marca "Karvey" = *Afán*, selknam).

### Por qué
Formalizar Karvey como método propio de HainTech, agnóstico de stack, absorbiendo el valor de Kiro y gstack, e instalable/versionable como plugin (sin copiar skills a mano).

> 👤 Humano responsable: Mauricio Quezada Ibáñez <mauricio.quezada@haintech.cl>
> 🤖 Asistido por IA: Claude Opus 4.8
> 🔗 Fase Karvey: publicación inicial · Apache 2.0
