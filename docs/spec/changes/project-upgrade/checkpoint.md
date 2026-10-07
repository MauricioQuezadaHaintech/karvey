# Checkpoint — project-upgrade

> Cross-cutting skill karvey-checkpoint. It is NOT a phase. It does NOT modify spec.json:phase.

- **Date:** 2026-09-25 (session rotated by the owner right after init)
- **Author:** agente-karvey (Claude Opus 5.5) for Mauricio Quezada Ibáñez
- **Repo:** worktree `~/Dev/karvey-wt-project-upgrade`, branch `feature/project-upgrade` (from `feature/wave1-hardening` @9395588)
- **Why a worktree:** another session works `wave1-hardening` in `~/Dev/karvey` (same working copy otherwise).

## Decisions made (D-20, owner, 2026-09-25)
- Request, verbatim: «entonces agrega un lo que sea para upgrade, cada vez que alguien actualiza, que le pregunte si quiere refrescar su proyecto con un plan de actualización, no del plugin, sino del proyecto con las recomendaciones y revisiones nuevas.»
- Release: «Justo después de 3.12.0 (Recomendado)» — separate change; 3.12.0 does not slip.
- Who is asked: «A cada persona, por clon (Recomendado)» — seen-version in `<git-common-dir>/karvey/`, not committed.
- Plan approved by answering the two questions above; next gate is requirements.

## Plan — checklist (Karvey full flow; no UI, no cloud)

### Phase gates
- [x] init — `karvey-state.py init project-upgrade` (spec.json), `prd.md`
- [ ] requirements — EARS `requirements.md` + `spec-delta.md` from `prd.md` → **owner approves (gate)**
- [ ] mockup / design_graphic — `skip` (no UI): `karvey-state.py skip project-upgrade mockup|design_graphic --reason "no UI"`
- [ ] architecture — hook change, script, skill, steps file, lint check → **owner approves (gate)**
- [ ] infra — `skip` (no cloud)
- [ ] tasks — E{n}.F{n}.T{n} in PLAN.md with estimates (estimates run ~10× high: calibrate) → **owner approves (gate)**
- [ ] impl → test → qa (**owner approves**) → deploy with the owner's prod OK (D-10) → archive

### What gets built
1. [ ] **Session hook — once per version, per clone**
   - [ ] record last seen plugin version in `<git-common-dir>/karvey/seen-version` (local; absent = never seen)
   - [ ] on change (or absent) in a Karvey project: inject one instruction telling the agent to ask, via AskUserQuestion, «Karvey X → Y: ¿quieres un plan para actualizar tu proyecto?»
   - [ ] "no" → record declined for that version; do not ask again until the next version
   - [ ] silent outside Karvey projects (same test as the settings notice)
2. [ ] **`scripts/karvey-upgrade.py plan|apply [--json] [--dry-run]`** — deterministic (AG-10); the skill only relays
   - [ ] reads `scripts/karvey_lib/upgrade-steps.json`: each step = id, since, check, fix, dry-run, human?, risk
   - [ ] `plan` runs every check against the project state and lists what applies
   - [ ] `apply --steps a,b` runs the approved fixes, dry-run first; idempotent (second run = nothing to do)
3. [ ] **Initial steps in `upgrade-steps.json`**
   - [ ] migrate `spec.json` / `project.json` (`validate --all --fix`; `--accept-proposed` only if approved)
   - [ ] team settings missing (`karvey-config.py propose-settings`)
   - [ ] legacy hook templates copied into the repo (`.claude/hooks/plan-gate.sh`, `git-flow-guard.sh`) → remove
   - [ ] statusline: not the plugin's, or pointing to a versioned path → stable launcher (**F-51**)
   - [ ] changes in flight vs the new gates → report only, never reprocess; archived = history (D-14)
   - [ ] global config (`~/.claude/CLAUDE.md`, `settings.json`) → show diffs only, owner applies (D-01, D-11)
   - [ ] project standards/rules the new version adds (`docs/spec/standards`, `project.json:enforcement`)
4. [ ] **Skill `/karvey-upgrade`** — plan as a table (step · what changes · dry-run · risk) → the person picks steps → apply on `chore/karvey-upgrade-<version>` → one PR; never a commit on integration/production
5. [ ] **Lint check L-NN** — a release that changes schemas, rules, hooks or settings must declare its upgrade step; CI fails otherwise ("every time" enforced by CI, not memory)
6. [ ] **Tests** — tables: notice once / not outside Karvey / not after decline / again on next version; unit: plan + apply on `tests/fixtures/legacy/*`, apply idempotent
7. [ ] **Docs** — hooks/README (notice), plugin README (upgrade section), CHANGELOG `[Unreleased]`

### Records (do at requirements)
- [ ] D-20 in `docs/spec/decisions.md` (text above) — **check D-20 is still free**: the other session may have taken it (IDs collide across sessions)
- [ ] backlog entry BL-51 (or next free) → this change; F-51 (statusline stable launcher) folds in here
- [ ] cross-link from wave1 findings when that session is idle (do not edit wave1 files from here)

### Related pending (not this change)
- AG-12 cheap pieces proposed to the owner (evidence wrapper, "fiscal" before `qa.approved` / "done") → backlog proposal, not decided.

## Next step
Run `/karvey-requirements project-upgrade` in `~/Dev/karvey-wt-project-upgrade`: EARS from `prd.md`, record D-20, then stop at the requirements gate for the owner.
