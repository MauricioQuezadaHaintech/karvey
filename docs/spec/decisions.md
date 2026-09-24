# Decision log — Karvey Method

Registry of `D-NN` (business owner) and `C-NN` (whoever directs the work) decisions, per
`plugins/karvey/skills/karvey-decisions/SKILL.md`. Numbers are assigned once, never reused, never
renumbered. A decision is immutable: a later decision supersedes it and cites it; the superseded body is
corrected, not annotated at the end.

> **Location.** The decisions skill says `{ops_repo}/decisions/` (one file per period) and
> `rules/multi-agent.md:24` says `docs/decisiones.md` (panel finding H-33). This repo has no separate ops
> repo (`project.json` has no `ops_repo`, so it defaults to `spec_repo` = `karvey`), and this single file is
> the log until the path is unified (R-24, Wave 3). `wave1-hardening` REQ-W1-059 fixes the two texts to
> agree.
>
> **Scanned before numbering:** `docs/spec/**` and the whole repo for `D-[0-9]` entries — no earlier
> decision log exists, so the D series starts at D-01. No C-NN has been recorded.

| ID | Date | Series | Title | Cited by | Status |
|----|------|--------|-------|----------|--------|
| D-01 | 2026-09-23 | D | The plan-approval marker is created by a prompt hook when the human approves; the agent never creates it | wave1-hardening | in force |
| D-02 | 2026-09-23 | D | `prod-gate` is ON by default and can be switched off per project | wave1-hardening | in force |
| D-03 | 2026-09-23 | D | The prod approval lives in a D-NN, in the PR and in `spec.json` at archive — never as a commit on dev/integration | wave1-hardening | in force |
| D-04 | 2026-09-23 | D | 3.12.0 is built with Karvey on itself; `team-adapters` converges inside `wave1-hardening` | wave1-hardening, team-adapters | in force |

---

## D-01 — The plan-approval marker is created by a prompt hook, never by the agent

- **What:** the marker that lets the plan-gate hook allow modifications is created by a hook that runs
  when the **human submits a prompt** (`UserPromptSubmit`) and recognises an approval in it; the agent
  never creates, renews or touches the marker.
- **Who / when:** Mauricio Quezada Ibáñez (owner), 2026-09-23, in the session that opened `wave1-hardening`, answering a structured question (AskUserQuestion) on the panel's Wave 1 decisions (`docs/spec/reviews/2026-09-23-panel-review.md` §4, §6).
  - **Question:** «¿Quién crea el marcador de plan aprobado (/tmp/claude-plan-approved-*)? Hoy lo crea el propio agente con touch, así que la compuerta se aprueba sola.»
  - **His answer, verbatim:** «Un hook de prompt (Recomendado)», then «ok» to the Wave 1 plan that listed it.
- **Why:** a marker the gated agent can create does not gate anything (panel H-11, R-02: "un marcador que
  crea el mismo agente no controla nada"). Moving creation to a hook on the human's own message makes the
  approval an act of the human, observable and testable.
- **Consequence outside this repo:** the owner's global `~/.claude/CLAUDE.md` today tells the agent to run
  `touch /tmp/claude-plan-approved-mauricio-haintech` after approval. That rule must change. The change is
  **shown to him as a diff before editing** and is **not part of this repo** or of any PR of this change.
- **What it does NOT say:**
  - It does not decide the approval vocabulary, the marker's TTL or its scope (project / change) — those
    are requirements of `wave1-hardening` (REQ-W1-016..019), not of this decision.
  - It does not forbid the human from creating the marker himself outside the agent session.
  - It does not make plan-gate mandatory: plan-gate stays opt-in per project (`enforcement.plan_gate_hook`);
    only `prod-gate` changes its default (D-02).
  - It does not authorise editing `~/.claude/CLAUDE.md` without that diff being approved.

## D-02 — `prod-gate` is ON by default, switchable off per project

- **What:** the new `prod-gate` hook (blocks a merge to the production branch unless the change records a
  human production approval) is **enabled by default** when Karvey's hooks are present, and a project can
  switch it off explicitly in `project.json`.
- **Who / when:** Mauricio Quezada Ibáñez (owner), 2026-09-23, in the session that opened `wave1-hardening`, answering a structured question (AskUserQuestion) on the panel's Wave 1 decisions (`docs/spec/reviews/2026-09-23-panel-review.md` §4, §6).
  - **Question:** «¿El nuevo prod-gate (bloquea el merge a producción sin approvals.prod registrado) viene activado o es opt-in?»
  - **His answer, verbatim:** «Activado por defecto (Recomendado)», then «ok» to the Wave 1 plan that listed it.
- **Why:** the production gate is the one gate the method declares never delegable (`rules/multi-agent.md`,
  `rules/deploy-workflow.md`), and it exists only in prose (H-15). An opt-in guard for the one
  non-negotiable gate would leave it unguarded in most projects.
- **What it does NOT say:**
  - It does not turn `git-flow` or `plan-gate` on by default — they remain opt-in (`rules/enforcement.md`).
  - It does not say how the off switch is named; `wave1-hardening` specifies it (REQ-W1-027).
  - It does not let an agent switch it off: switching it off is a committed `project.json` change, reviewed
    like any other.
  - It does not decide per-change release manifests (R-08, Wave 2): in Wave 1 the check is per change-id.

## D-03 — Where the production approval is recorded

- **What:** the human's production OK is recorded (1) as a `D-NN` in this decision log, (2) in the PR (body
  or approval), and (3) copied into the change's `spec.json:approvals.prod` **at archive**, on the archive
  branch. It is **never** recorded by a commit on the integration (`dev`) or production branch.
- **Who / when:** Mauricio Quezada Ibáñez (owner), 2026-09-23, in the session that opened `wave1-hardening`, answering a structured question (AskUserQuestion) on the panel's Wave 1 decisions (`docs/spec/reviews/2026-09-23-panel-review.md` §4, §6).
  - **Question:** «¿Dónde queda registrada la aprobación de prod, sin obligar a commitear en dev?»
  - **His answer, verbatim:** «D-NN + PR + spec.json al archivar (Recomendado)», then «ok» to the Wave 1 plan that listed it.
- **Why:** `karvey-deploy` today tells the agent to commit `approvals.prod` on the branch that goes to
  master, which is `dev` (H-18), forcing a violation of "never commit on dev" every cycle. Keeping the copy
  in `spec.json` (AG's variant of R-03) keeps `spec.json` self-contained.
- **What it does NOT say:**
  - It does not make the PR approval sufficient on its own: the D-NN is still required.
  - It does not decide release-per-change (R-08); with several changes in one release, each one's
    approval is still recorded per change.
  - It does not apply retroactively: the `approvals.prod.ref` already written in `team-adapters` and
    `team-layer` stays as history.

## D-04 — Dogfooding: 3.12.0 is built with Karvey on itself

- **What:** Karvey 3.12.0 (Wave 1) is built **through the Karvey method on this repo**, as the change
  `wave1-hardening`. `team-layer` is already archived; `team-adapters` (released without `approvals.qa`,
  QA NOT APPROVED) **converges inside `wave1-hardening`**: its open bugs (BUG-05..BUG-17) and its spec-gaps
  are resolved and its REQ-ADP-* amended there, instead of reopening a separate cycle.
- **Who / when:** Mauricio Quezada Ibáñez (owner), 2026-09-23, in the session that opened `wave1-hardening`, answering a structured question (AskUserQuestion) on the panel's Wave 1 decisions (`docs/spec/reviews/2026-09-23-panel-review.md` §4, §6).
  - **Question:** «¿Karvey 3.12.0 se hace obligatoriamente con Karvey sobre sí mismo (dogfooding)? Eso exige cerrar primero los changes team-layer y team-adapters.»
  - **His answer, verbatim:** «Sí, con el método completo (Recomendado)», then «ok» to the Wave 1 plan that listed it.
- **Why:** the method's own repo skipped its gates (H-22). The Wave 1 changes (state machine, guards) are
  exactly what makes skipping visible, so building them under the method is both the test and the fix.
- **What it does NOT say:**
  - It does not introduce lanes (R-09 is Wave 2). The phases this change does not need (mockup,
    design_graphic) are recorded as skipped in `spec.json` as this change's own workaround.
  - It does not archive `team-adapters` now; it converges when `wave1-hardening` converges.
  - It does not require a cross-model second opinion; if none is available, QA says so (as in the
    team-adapters review).

## D-05 — Requirements of `wave1-hardening` approved

- **What:** the 109 EARS requirements REQ-W1-001..109 in `docs/spec/changes/wave1-hardening/requirements.md` are approved; the change advances to architecture.
- **Who / when:** Mauricio Quezada Ibáñez (owner), 2026-09-23, structured question at the requirements gate.
  - **Question:** «¿Apruebas los requisitos de wave1-hardening (109 EARS en docs/spec/changes/wave1-hardening/requirements.md) para pasar a arquitectura?»
  - **His answer, verbatim:** «Apruebo»
- **What it does NOT say:** it does not approve architecture, tasks or prod; it does not bring H-04/H-05/H-06/H-21/H-35 into Wave 1 (they stay in Wave 2).

## D-06 — Rotation threshold: 8 hours (Q-01)

- **What:** the statusline raises TIME TO ROTATE at 8 h of session (`KARVEY_ROTATE_HOURS` default stays 8).
- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-23.
  - **Question:** «Umbral de horas del statusline para avisar 'HORA DE ROTAR' (Q-01; lo necesita la fase tasks).»
  - **His answer, verbatim:** «8 horas (Recomendado)»
- **What it does NOT say:** it does not change the context thresholds (100k yellow / 150k red).

## D-07 — Defaults that make the requirements testable

- **What:** plan-approval marker expires after **120 min**; a change is **stalled** after **7 days** without a phase change; estimates are **recalibrated** when a work type deviates by more than **±30 %** in each of the last **3** changes. All three configurable in `project.json`.
- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-23.
  - **Question:** «Valores por defecto que hacen testeables los requisitos: el marcador de aprobación vence a los 120 min; un change queda 'estancado' tras 7 días sin cambio de fase; se recalibra la estimación si un tipo de trabajo se desvía >±30% en los últimos 3 changes. ¿Los acepto?»
  - **His answer, verbatim:** «Sí, los tres (Recomendado)»
- **What it does NOT say:** they are initial values, not fixed rules; a project may override them.

## D-08 — Retroactive record of the prod approval of `team-adapters` (3.10.0 → 3.11.1)

- **What:** `team-adapters` reached `main` (prod of this repo) in PR #17 (3.10.0), #18 (3.11.0) and #19 (3.11.1) without a D-NN. This entry records, **retroactively**, the owner's words that authorised those merges. It does **not** approve QA: the retroactive QA (`docs/spec/changes/team-adapters/qa/REVISION_PR_17-19_20260923.md`) is NOT approved and stays so until `wave1-hardening` converges.
- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-22/23, in the session that built the change.
  - PR #17 (3.10.0): «perfecto, luego commit,push, merge (lo que corresponda) y actualizas en local, le avisas a todos los agentes que actualicen el plugin»
  - PR #18 (3.11.0) and PR #19 (3.11.1): merged under that same standing instruction, after the owner's requests «el html tiene que estar consecuentemente en inglés y con un swich a español, portugues, aleman, chino» and «agrega que descubra el idioma del explorador y lo seleccione, si no está en la lista, inglés.» — no separate prod word was given for these two; recorded as such, not upgraded.
- **Answer that created this entry:** «D-NN retroactivo citando tus mensajes (Recomendado)»
- **What it does NOT say:** it does not make the missing `approvals.qa` acceptable; it does not back-fill `team-layer` (that change keeps its `gates_skipped`, reported as warnings).

## D-09 — Architecture of `wave1-hardening` approved

- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-23. **Question:** «¿Apruebas la arquitectura de wave1-hardening para pasar a tareas?» **Answer, verbatim:** «Apruebo»
- **Includes the architect's recommended defaults** stated at the gate: legacy phase map only with `--accept-proposed`; script name `karvey-spec-merge.py`; keep `karvey-config.py`; multi-repo prod-gate gap documented for 3.12.0; `node --test` without npm in CI; `git push origin dev` from a feature branch allowed. Branch protection on `main` is a human task at deploy.
- **What it does NOT say:** it does not approve tasks or prod.

## D-10 — A prod approval needs an approval word AND a production word in the human's own prompt

- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-23. **Answer, verbatim:** «Sí, ambas palabras (Recomendado)»
- **What:** the approval hook records a prod approval only when the human's prompt contains both (e.g. «ok, merge a prod»); a bare «ok» is not a prod approval.

## D-11 — Compatibility with the owner's personal plan hooks: `KARVEY_COMPAT_MARKER`

- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-23. **Answer, verbatim:** «KARVEY_COMPAT_MARKER (Recomendado)»
- **What:** an env var in his `~/.claude/settings.json` makes Karvey's approval hook also write his legacy marker `/tmp/claude-plan-approved-*`, so his `require-plan*.sh` keep working after the CLAUDE.md change (D-01). The diff to his settings is shown to him before editing; it is not part of this repo.

## D-12 — `infra` phase skipped for `wave1-hardening`

- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-24. **Answer, verbatim:** «Omitida, con motivo (Recomendado)»
- **What:** `skipped.infra = "no cloud; the CI workflow is built as tasks E1.F13"`.

## D-13 — Tasks of `wave1-hardening` approved

- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-24. **Question:** «¿Apruebas las tareas de wave1-hardening (73 tareas) para pasar a implementación?» **Answer, verbatim:** «Apruebo»
- **What it does NOT say:** it does not approve QA or prod; the five `[human]` tasks stay his.

## D-14 — Pre-3.12 approvals: team-adapters gets a real prod phrase; team-layer stays recorded history

- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-24. **Question:** «Aprobaciones anteriores a 3.12.0 (team-layer archivado y team-adapters) … ¿Cómo las tratamos? (F-35)» **Answer, verbatim:** «Escribo la frase de prod ahora»
- **What:** E1.F15.T2 runs: the owner types a prod-approval phrase (approval word + production word, D-10) for `team-adapters` in a session that loads the 3.12 plugin, and the approval hook records it. `team-layer` (archived, merged without a human prod record) is reported as a **warning** with its reason — never back-filled.
- **What it does NOT say:** it does not make pre-3.12 data errors silent in general; only archived changes whose approvals predate 3.12.0 are downgraded to warnings.

## D-15 — The integration branch is not "production" when it differs from it (F-12)

- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-24. **Answer, verbatim:** «Sí, excluir integración (Recomendado)»
- **What:** prod-gate removes `branch_flow.integration` from the production set when it differs from `branch_flow.production`; `main`/`master` and the remote default (when it is not the integration branch) stay protected even if renamed.

## D-16 — Close the notification-confirmation gap in Wave 1 (F-15)

- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-24. **Answer, verbatim:** «Cerrarlo ahora (Recomendado)»
- **What:** `karvey-config.py notify-check --confirm` counts only when backed by a human-written confirmation captured by the UserPromptSubmit hook, like the approval markers; the agent cannot confirm a changed destination by itself.

## D-17 — Minor implementation decisions accepted

- **Who / when:** Mauricio Quezada Ibáñez, 2026-09-24. **Answer, verbatim:** «Sí, todas (Recomendado)»
- **What:** protect-paths blocks editing the plugin from a session that loads it from the same working copy (F-09; dogfood with another copy); a prompt line over 200 characters records no approval (F-11); the diagnostic `selftest` guard stays (F-08); low findings F-26..F-33 go to the Wave 2 backlog.

