# Panel de expertos sobre el Método Karvey 3.11.1: informe de decisión

> **Fuentes:** tres jueces independientes. DM es el juez de métodos de desarrollo (DM-01…15), PM el de gestión de proyectos (PM-01…15) y AG el de uso de agentes (AG-01…14, con mediciones). A eso se suma la propuesta del dueño, JU-01.
> **Verificación:** cada hallazgo se volvió a comprobar en `.` (HEAD `e3bc6f3`, v3.11.1) con grep/lectura. Los hooks se ejecutaron con entradas sintéticas en el scratchpad. Todo fue de solo lectura sobre el repo.
> **Rutas:** son relativas a `plugins/karvey/skills/`, salvo que diga `hooks/` (= `plugins/karvey/hooks/`) o `docs/spec/` (= raíz del repo).

---

## 1. Resumen ejecutivo

Los tres jueces coinciden en lo mismo: **el contenido del método es de primer nivel y su ejecución es frágil**. El loop bug/spec-gap/emergent con un único router, `verification.md`, la Iron Law de investigate, el gate de prod indelegable y la capa de equipo con costo medido están por sobre Spec Kit, Kiro y gstack. Pero casi todo el determinismo está escrito en prosa, y esa prosa se contradice.

Los jueces convergen en cinco temas:

1. **La máquina de estados no existe como código.** Las skills escriben 11 valores de `phase` que el orquestador no reconoce, y `impl` no escribe ninguno. Mockup→architecture es un callejón sin salida para cambios sin UI. Los tres jueces lo detectaron por separado.
2. **Las garantías declaradas no son reales.** Los hooks hacen menos de lo que dice `enforcement.md`. Hay hooks citados que no existen y ningún hook protege el merge a prod. Tres instrucciones obligan al agente a romper la regla "nunca commitear en dev": `approvals.prod`, archive y el orden del checklist. DM y AG lo detectaron.
3. **La unidad aprobada no es la unidad liberada.** El PR `dev → master` saca todo lo que hay en dev, aunque QA y `approvals.prod` se validan por cambio. DM y PM lo detectaron.
4. **El costo del proceso no escala con el tamaño del cambio.** Hay un solo carril con 7 gates humanos, unas 50–70 interrupciones y ~92k tokens de instrucciones por ciclo. Graphify corre en cada fase, e incluso en cada iteración del mockup. El propio repo del método se saltó los gates. Los tres jueces lo detectaron.
5. **Hay datos que nadie agrega.** `time_estimate` se sobrescribe con el tiempo real, no hay métricas DORA ni costo por cambio, y el dashboard no muestra findings, backlog ni incidentes. PM y DM lo detectaron.

**Qué hacer primero (Ola 1, 3.12.0):** corregir los bugs verificados y reemplazar la prosa determinista por scripts. Eso significa `karvey-state.py` con su esquema, hooks corregidos y con tests, un `prod-gate`, un único momento de versionado, archive y registro de prod fuera de `dev`, y `time_estimate`. Va primero por dos razones: casi todo es esfuerzo S–M con riesgo bajo, y todo lo estructural de la Ola 2 (carriles, jueces, métricas, release por cambio) necesita un estado de fase confiable sobre el cual apoyarse.

---

## 2. Hallazgos verificados

**Resultado: 35 hallazgos. 34 Confirmado, 1 No reproducido.**

| # | Hallazgo (origen) | Estado | Evidencia propia |
|---|---|---|---|
| H-01 | Los valores de `phase` que escriben las skills no calzan con la tabla del orquestador (DM-02, PM-01, AG-01) | **Confirmado** | La tabla espera `init…deployed` (`karvey/SKILL.md:115-137`). Las skills escriben `requirements-generated` (`karvey-requirements/SKILL.md:110`), `mockup-generated` (`karvey-mockup/SKILL.md:153`), `design-graphic-approved` (`karvey-design-graphic/SKILL.md:377`), `architecture-generated/-approved` (`karvey-architecture/SKILL.md:286,299`), `infra-generated/-approved` (`karvey-infra/SKILL.md:212,217`) y `tasks-generated/-approved` (`karvey-tasks/SKILL.md:117,255`). Solo `init` y `deployed` calzan. |
| H-02 | `karvey-impl` nunca escribe `phase` (DM-02, PM-01, AG-01) | **Confirmado** | `grep phase karvey-impl/SKILL.md` solo encuentra el ritual y el bloque "Advance". |
| H-03 | Callejón sin salida en cambios sin UI (DM-01, AG-01) | **Confirmado** | Mockup dice "skip to karvey-architecture" (`karvey-mockup/SKILL.md:52`). Architecture exige `design_graphic.approved = true` y si no, se detiene (`karvey-architecture/SKILL.md:28`). No existe un estado `skipped`. |
| H-04 | Hotfix choca con las precondiciones (DM-01) | **Confirmado** | El carril es `iterate → impl → test → deploy` (`karvey/SKILL.md:141`), pero impl exige `tasks.approved` (`karvey-impl/SKILL.md:27`) y deploy busca `REVISION_PR_*` de QA (`karvey-deploy/SKILL.md:29`). |
| H-05 | design-graphic se aprueba sola (DM-06, AG-01) | **Confirmado** | Escribe `approvals.design_graphic.approved: true` en su output (`karvey-design-graphic/SKILL.md:371,377`). No hay ningún paso que pida la aprobación; solo aparece el "Shall we advance" (`:382`). |
| H-06 | `-y` auto-aprueba sin `by/role/ref` (DM-06, PM-09, AG-01) | **Confirmado** | `karvey-requirements/SKILL.md:146`, `karvey-architecture/SKILL.md:296`, `karvey-infra/SKILL.md:215` y `karvey-tasks/SKILL.md:126`. |
| H-07 | `deployed` se fija con el PR a prod todavía abierto, y archive lo acepta (PM-03) | **Confirmado** | En Step 6, `phase: "deployed"` es incondicional y `approvals.deploy.approved` puede ser `null` (`karvey-deploy/SKILL.md:300-305`). Archive acepta `phase=deployed` **o** `deploy.approved` (`karvey-archive/SKILL.md:23`) y crea `IMPLEMENTED` (`:32`). |
| H-08 | El hook de sesión toma `archive/` como cambio activo (DM-05, AG-09) | **Confirmado (reproducido)** | `hooks/karvey-session-context.sh:127` usa `ls -1dt changes/*/`. Simulé un proyecto con `changes/feat-a` y un `changes/archive/…` más nuevo, y la salida fue *"Run `/karvey-checkpoint restore` BEFORE anything else (active change: archive)"*. |
| H-09 | El hook de sesión inyecta el manifest compacto **y** el completo (AG-09) | **Confirmado** | `hooks/karvey-session-context.sh:79-80`, que contradice `karvey-checkpoint/SKILL.md:49`. |
| H-10 | plan-gate: falso positivo con `2>` y comandos destructivos que pasan (DM-05, AG-03) | **Confirmado (ejecutado)** | Regex `>[^>]` en `karvey/hooks/plan-gate.sh:31`. Resultados sin marcador: `ls 2>/dev/null` → rc=2 (bloquea); `git clean -fdx`, `find . -delete` y `sed -i` → rc=0 (pasan); `rm -rf build` → rc=2. |
| H-11 | El marcador de plan-gate no expira, es global y lo crea el agente (DM-05, AG-03) | **Confirmado** | Es `/tmp/claude-plan-approved` fijo (`plan-gate.sh:10`) y basta con `[ -f "$FLAG" ] && exit 0` (`:24`). No hay TTL ni consumo, aunque `karvey/rules/enforcement.md:25` dice "until it is consumed/expires". `karvey-guard/SKILL.md:53` le pide al agente hacer `touch`. |
| H-12 | git-flow-guard tiene evasiones y un falso positivo (AG-03) | **Confirmado (ejecutado)** | En el repo sintético, rc=0 (pasan): `git -C <repo-en-master> commit`, `git push` a secas en master, `git push origin dev` y `gh pr merge 12 --merge --admin`. Con rc=2 se bloquea `git push origin master-notes`, que es un falso positivo por el `\b` (`git-flow-guard.sh:33`). |
| H-13 | `enforcement.md` promete bloquear el push a integration fuera del flujo, y no está implementado (DM-05, AG-03) | **Confirmado** | `karvey/rules/enforcement.md:16` contra `git-flow-guard.sh`, que solo revisa production y commit. |
| H-14 | Hooks descritos que no existen: `clickup-sync-guard` y `standards-guard` (DM-05, AG-03) | **Confirmado** | Se citan en `karvey/rules/phase-close.md:41` y `karvey/rules/engineering-standards.md:181`. No hay ningún archivo con esos nombres en el disco. |
| H-15 | No hay ningún hook sobre el merge a prod (AG-03) | **Confirmado** | `gh pr merge --admin` pasa (H-12). El gate "nunca delegable" solo existe en prosa (`karvey-deploy/SKILL.md:203-210`). |
| H-16 | `time_estimate` se sobrescribe con el tiempo real (DM-15, PM-02) | **Confirmado** | `karvey-impl/SKILL.md:120-124` hace `curl … -d '{"time_estimate": {actual_time_ms}}'`. |
| H-17 | Doble versionado: bump en impl y otra vez en deploy (DM-04, AG-02) | **Confirmado** | Impl hace bump y CHANGELOG (`karvey-impl/SKILL.md:75-87`), y el orquestador lo describe como "Version bump + CHANGELOG per commit" (`karvey/SKILL.md:191`). Deploy 2.4 vuelve a hacer bump (`karvey-deploy/SKILL.md:133-141`). |
| H-18 | `approvals.prod` se commitea en la rama que va a master, que es `dev` (DM-05, AG-02) | **Confirmado** | `karvey-deploy/SKILL.md:206` dice "commit it on the branch that goes to `master`", y el PR es `--head {integration}` (`:167`). Eso choca con `git-flow-guard.sh:38-43` y con la regla dura del usuario. |
| H-19 | Archive commitea sin crear rama y queda en `dev` después del deploy (DM-05, AG-02) | **Confirmado** | Hay dos `git commit` sin checkout en `karvey-archive/SKILL.md:66-90`, y deploy dejó el HEAD en `dev` (`karvey-deploy/SKILL.md:147`). |
| H-20 | El checklist de 6 pasos "antes del push" aparece después del push (AG-02) | **Confirmado** | El push está en 2.6 (`karvey-deploy/SKILL.md:151-153`) y el checklist en Step 3 (`:244-255`). |
| H-21 | El PR `dev → master` arrastra cambios no aprobados (DM-03, PM-04) | **Confirmado (por diseño)** | `gh pr create --base {production} --head {integration} --title "[Deploy] {change-id}"` (`karvey-deploy/SKILL.md:165-168`). Los gates Step 0 y `approvals.prod` se validan para un solo change-id (`:26-46`). No existe un manifiesto de commits a change-ids. |
| H-22 | El repo del método se salta sus propios gates (DM-01, DM-09, PM-01) | **Confirmado** | `docs/spec/changes/team-adapters/spec.json` tiene `phase: "deploy"`, un valor inexistente (`:14`); `qa.approved:false` (`:68-71`); `tasks.approved:true` sin `tasks.md` en la carpeta; y `prod.ref` = "session approval: 'perfecto, luego commit, push, merge'" (`:81`) en vez de un D-NN. `team-layer/spec.json:12` quedó en `phase: "impl"` con `tasks.approved:false`, aunque salió en 3.8.0 (`CHANGELOG.md:112-118`) y tiene 4 findings `open` (`team-layer/findings.md:5-8`). No existen `docs/spec/specs/` ni `archive/`. |
| H-23 | 12 skills sin descripción en el listado de la sesión (AG-11) | **Confirmado** | En el listado de skills de **esta** sesión aparecen sin descripción `devex`, `diagram`, `docs`, `grill`, `guard`, `import`, `qa`, `retro`, `scrape`, `second-opinion`, `standards` y `test`. Los 12 frontmatter sí tienen descripción (273–565 caracteres), así que el harness las truncó por presupuesto. El total de las 32 descripciones es de 13.907 caracteres. |
| H-24 | `proposal.md` es un artefacto fantasma (DM-02, PM-06, AG-13) | **Confirmado** | Lo leen `karvey-requirements`, `karvey-mockup`, `karvey-design-graphic` y `karvey-context`. `karvey-init` crea `prd.md` (`karvey-init/SKILL.md:193-195`) y ninguna skill crea `proposal.md`. |
| H-25 | `spec-delta.md` tiene dos rutas (DM-02) | **Confirmado** | En la raíz del cambio según `karvey/rules/living-specs.md:17` y `karvey/SKILL.md:230`; en `specs/{capability}/spec-delta.md` según `karvey-requirements/SKILL.md:124`. |
| H-26 | Hay 9 copias de reglas (DM-12, AG-06) | **Confirmado** | Las 9 son byte-idénticas hoy (`cmp`), así que no hay drift. El riesgo ya se materializó una vez (`CHANGELOG.md` 3.9.1). |
| H-27 | El plugin no tiene CI propio (DM-12, AG-13) | **Confirmado** | `.github/workflows/` solo contiene `close-external-prs.yml`. |
| H-28 | QA commitea arreglos aunque "solo observa" (DM-14) | **Confirmado** | `karvey-qa/SKILL.md:121` ("apply atomic commits") contra `:268` ("QA only observes and classifies"). |
| H-29 | `REVISION_PR_*` en la raíz, leído con `ls -t` (DM-14) | **Confirmado** | `karvey-deploy/SKILL.md:29`. Con dos cambios en QA a la vez, puede leer el equivocado. |
| H-30 | `karvey-context` no muestra backlog, findings ni incidentes (PM-06) | **Confirmado** | `grep -ci 'backlog\|findings\|BUG-' karvey-context/SKILL.md` da 0, aunque `karvey/rules/backlog.md:44` lo promete. |
| H-31 | Graphify corre en cada fase y en cada iteración del mockup (DM-15, AG-05) | **Confirmado** | `karvey-mockup/SKILL.md:159,211` y `karvey/rules/knowledge-sync.md:14` ("never go without synchronization"). La skill de graphify pesa 41.276 bytes (~10k tokens). |
| H-32 | Umbral de rotación inconsistente (AG-09) | **Confirmado** | 24 h en `karvey/rules/team.md:58,66,80` y `karvey-checkpoint/SKILL.md:271`; 8 h en `hooks/karvey-statusline.sh:34` y `hooks/README.md:59`. |
| H-33 | Menores de consistencia (PM-11, AG-07, AG-13) | **Confirmado** | La ruta del log de decisiones difiere: `karvey/rules/multi-agent.md:24` dice `docs/decisiones.md` y `karvey-decisions/SKILL.md:31` dice `{ops_repo}/decisions/`. `E{1..99}` en `karvey-init/SKILL.md:248`. Bloque "For each E2E flow step" duplicado en `karvey-test/SKILL.md:154-164`. `README.md:146` dice `/karvey:grill`, pero la skill es `karvey:karvey-grill`. `allowed-tools` no incluye `Write` en `karvey-browse` y `karvey-health`, que escriben `findings.md` y el historial, ni `Write` ni `AskUserQuestion` en el orquestador. "Shall we advance" aparece en 12 skills. |
| H-34 | Costo de instrucciones por ciclo (AG, §2.4) | **Confirmado (medido)** | Los 32 SKILL.md suman 333 KB (~83k tokens), las 22 reglas 108 KB (~27k) y graphify 41 KB (~10k). La cifra de ~92k tokens únicos por ciclo de AG es consistente. |
| H-35 | Colisión de IDs `BUG-NN`, `D-NN` y `E{n}` entre sesiones paralelas (PM-13, AG-07) | **No reproducido** | El mecanismo "lee y suma 1" sí está en el texto (`karvey/rules/incident-tracking.md:9`, `karvey-decisions/SKILL.md:40`), pero no hay ningún caso dentro del repo. PM lo declara como inferencia. La memoria del usuario menciona colisiones en otros repos, pero eso no lo verifiqué aquí. |

---

## 3. Recomendaciones consolidadas

La prioridad sube cuando hay consenso entre jueces. El orden es por impacto y, dentro del mismo impacto, por menor esfuerzo.

### R-01: Máquina de estados única, con esquema y script (`karvey-state.py`)
- **Origen:** DM-02 + PM-01 + PM-03 + AG-01 (3 jueces).
- **Problema:** H-01, H-02, H-03, H-07, H-22, H-24 y H-25. El ruteo depende de que el LLM "interprete" 11 valores que no están en la tabla (`karvey/SKILL.md:115-137`).
- **Recomendación:**
  - Crear `rules/state-machine.md` con un enum cerrado: `init | requirements | mockup | design_graphic | architecture | infra | tasks | impl | test | qa | deploying | deployed | archived`. "Generado" y "aprobado" viven **solo** en `approvals.*`.
  - Publicar `schemas/spec.schema.json` y `project.schema.json`.
  - Crear `scripts/karvey-state.py` con los comandos `next | advance | approve --by --role --ref | skip --reason | validate [--fix]`.
  - Reemplazar la tabla del orquestador por `karvey-state.py next {id}`. Cada skill cambia su "Update spec.json: phase…" por una llamada al script.
  - `impl` escribe `impl`. `deploy` escribe `deploying` y pasa a `deployed` solo después de que prod queda en verde y el canary OK. `archive` exige `deployed` y `approvals.prod.by`.
  - Toda precondición acepta `approved || skipped`.
  - Unificar `prd.md` (se elimina `proposal.md`) y una sola ruta para `spec-delta.md`.
  - Migrar con `--fix` los dos `spec.json` de `docs/spec/` y cerrar los findings `open` de `team-layer`.
- **Justificación:** es la base de todo lo demás. Carriles, jueces, métricas y el dashboard leen `phase` y `approvals`. Hoy hay 14 lugares que escriben el campo con 12 formatos distintos.
- **Beneficio:** ruteo reproducible entre sesiones, fin del callejón sin UI, y "deployed" pasa a significar que está en producción. Se mide con 0 `spec.json` inválidos en `validate` y 0 cambios archivados con `approvals.prod` vacío.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** bajo (migración asistida) · **Jueces:** DM, PM, AG.

### R-02: Hooks que hagan lo que dicen, un `prod-gate` y tests de tabla
- **Origen:** DM-05 + AG-03 (2 jueces).
- **Problema:** H-10 a H-15. La única capa determinista del método hace menos de lo que declara (`karvey/rules/enforcement.md:3,16,25`).
- **Recomendación:**
  - **`plan-gate.sh`:**
    - cambiar la regex a `(^|[^0-9&])>[^>&]`;
    - agregar `git clean`, `find … -delete`, `sed -i`, `truncate`, `DELETE FROM` sin `WHERE`, `terraform destroy` y `az … delete`;
    - usar un marcador por proyecto y change-id (hash de `$CLAUDE_PROJECT_DIR`), con TTL por `mtime` y consumido al cerrar la fase.
  - **`git-flow-guard.sh`:**
    - resolver la rama objetivo con `-C` y con `cd … &&`;
    - bloquear `git push` a secas cuando HEAD es production;
    - usar `(^|[ :])master($|[ ])`;
    - permitir push a integration solo si es fast-forward desde un merge de PR, o borrar esa promesa de `enforcement.md:16`.
  - **Nuevo `prod-gate.sh`** (PreToolUse sobre Bash) para `gh pr merge`, `az repos pr update --status completed` y `glab mr merge` hacia production. Deja pasar solo si `karvey-state.py` confirma `approvals.prod.by` con `role: human`.
  - **PostToolUse sobre `**/spec.json`** que corre `karvey-state.py validate`.
  - Implementar `clickup-sync-guard` y `standards-guard`, o borrarlos de `phase-close.md:41` y `engineering-standards.md:181`.
  - Agregar `tests/hooks/*.bats` con los casos de H-10 y H-12 como fixtures.
- **Justificación:** "A skill is guidance… it guarantees nothing" (`enforcement.md:3`). Un marcador que crea el mismo agente no controla nada. Y un gate que bloquea `2>/dev/null` el usuario lo termina desactivando.
- **Beneficio:** el gate de prod pasa de prosa a garantía, se cierran 5 evasiones medidas y se eliminan los falsos positivos más frecuentes. Se mide con los bats en verde y los bloqueos falsos reportados (meta 0).
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** medio: una regex mal probada bloquea el trabajo; los tests de tabla lo acotan · **Jueces:** DM, AG.
- **Tensión con la regla global del dueño:** su `~/.claude/CLAUDE.md` le pide al agente ejecutar `touch /tmp/claude-plan-approved-mauricio-haintech` después de la aprobación. AG propone que el marcador lo cree un hook `UserPromptSubmit` al detectar la palabra de aprobación. **Mi recomendación:** usar el hook `UserPromptSubmit`, dejar el `touch` manual como fallback y actualizar la regla global. Queda como decisión del dueño (§6).

### R-03: Sacar de `dev` los commits de deploy y archive, y ordenar el checklist
- **Origen:** AG-02 (1, 3, 4) + DM-05 (4, 5) (2 jueces).
- **Problema:** H-18, H-19 y H-20. En cada ciclo el agente se ve obligado a violar "nunca commitear en dev".
- **Recomendación:**
  - Registrar el OK de prod en el `D-NN` del ops repo y en el cuerpo o aprobación del PR. `approvals.prod.ref` acepta un `D-NN` **o** la URL de aprobación del PR (PM-11).
  - `spec.json:approvals.prod` se escribe en la rama de archive.
  - Archive parte con `git checkout -b chore/archive-{id}` desde production y entra por un PR docs-only.
  - Mover el checklist de 6 pasos antes de 2.5, como Step 1.9.
- **Justificación:** cuando dos instrucciones se contradicen, el LLM obedece la más cercana o se detiene a preguntar. Las dos salidas son malas.
- **Beneficio:** 0 violaciones forzadas de la regla de ramas, un pipeline DEV menos por ciclo y 1–2 preguntas imprevistas menos por deploy. Se mide con 0 commits directos en dev o master en `git log --first-parent`.
- **Esfuerzo** S · **Prioridad** alta · **Riesgo** bajo · **Jueces:** DM, AG. Hay un matiz entre ellos: DM guarda el registro solo en el PR y en `decisions/`, mientras AG además lo copia a `spec.json` en archive. **Recomiendo lo de AG**, para que `spec.json` siga siendo autocontenido.

### R-04: Un solo momento de versionado
- **Origen:** DM-04 + AG-02 (2) (2 jueces).
- **Problema:** H-17. También hay un orden circular: QA-D6 exige el CHANGELOG de "la versión actual" (`karvey-qa/SKILL.md:91-102`) y el pre-check 3 de deploy (`karvey-deploy/SKILL.md:35-40`) lo exige antes de 2.4, que es el paso que lo crea.
- **Recomendación:**
  - Durante impl, cada commit agrega una línea en `## [Unreleased]`, sin bump.
  - El bump ocurre **solo** en deploy 2.4, que convierte `Unreleased` en `[x.y.z]`.
  - QA-D6 y el pre-check 3 validan `Unreleased`.
  - Reescribir `karvey/rules/versioning.md:15` como "cada **release** incrementa la versión".
  - Corregir `karvey/SKILL.md:191`.
- **Justificación:** semver versiona releases, no commits, y el bump por tarea genera conflictos en archivos calientes.
- **Beneficio:** una versión con significado por release y fin de los conflictos de CHANGELOG entre features paralelas. Se mide con bumps por release = 1.
- **Esfuerzo** S · **Prioridad** alta · **Riesgo** bajo · **Jueces:** DM, AG.

### R-05: No pisar la estimación; guardar el estimado y el real
- **Origen:** DM-15 + PM-02 (2 jueces).
- **Problema:** H-16 (`karvey-impl/SKILL.md:120-124`).
- **Recomendación:**
  - Registrar el real con time tracking (ClickUp: time entries, que ya se inician en `karvey-impl/SKILL.md:51`; Jira: worklog). Nunca sobre `time_estimate`.
  - Guardar `estimate_min`, `actual_ai_min` y `actual_review_min` en `tasks.md` / `spec.json`.
  - Archive o retro calcula real/estimado por fila de `karvey/rules/clickup-protocol.md:139-150` y propone recalibrar si la desviación supera ±30% en N cambios.
- **Justificación:** la hipótesis de estimar en minutos es valiosa, pero hoy el propio código borra la evidencia que permitiría validarla.
- **Beneficio:** cotizaciones defendibles y calibración real. Se mide con el error de estimación por tipo de trabajo.
- **Esfuerzo** S · **Prioridad** alta · **Riesgo** bajo · **Jueces:** DM, PM.

### R-06: Hook de sesión: `archive/`, inyección acotada y `state.json` por script
- **Origen:** AG-09 + DM-05 (3) (2 jueces).
- **Problema:** H-08, H-09 y H-32. `state.json` se declara "never by hand" (`karvey-checkpoint/SKILL.md:259`), pero lo escribe el LLM.
- **Recomendación:**
  - Excluir `archive/` y los cambios con `IMPLEMENTED` en `hooks/karvey-session-context.sh:127`.
  - Inyectar el manifest compacto **o** el completo, nunca ambos.
  - Del board, inyectar solo las filas abiertas (máximo ~40) y truncar el handoff a ~6 KB con aviso.
  - Emitir en JSON `additionalContext`.
  - Crear `scripts/karvey-handoff-capture.sh`, que escribe `state.json`.
  - Unificar el umbral de rotación (recomiendo 8 h, que es el valor que usa la statusline).
- **Beneficio:** 0 restores falsos después de cada archive, −50–80% de inyección en tableros grandes y drift medido por máquina.
- **Esfuerzo** S · **Prioridad** alta · **Riesgo** bajo · **Jueces:** DM, AG.

### R-07: El plugin como código: sin copias, rutas resolubles y CI con linter
- **Origen:** DM-12 + AG-06 + AG-13 (2 jueces).
- **Problema:** H-26, H-27, H-33 y H-24. AG midió 109 referencias con la forma `karvey/rules/x.md`, que no se resuelven desde la carpeta de cada skill. Además, `karvey-checkpoint`, `karvey-team` y `karvey-decisions` citan `rules/` sin tener esa carpeta.
- **Recomendación:**
  - Borrar las 9 copias y referenciar `../karvey/rules/x.md`. Si el empaquetado obliga a tener copias, generarlas en el build y compararlas en CI.
  - Crear `.github/workflows/lint.yml` con `scripts/lint-plugin.py`, que revise:
    - frontmatter y largo de las descripciones;
    - que las rutas referenciadas existan;
    - que no haya copias de reglas;
    - que los valores de `phase` pertenezcan al enum;
    - los conteos del README y `plugin.json` contra `ls skills/`;
    - que `plugin.json`, `marketplace.json` y el CHANGELOG tengan la misma versión;
    - que las herramientas mencionadas estén en `allowed-tools`;
    - que todo archivo que una skill lee lo produzca alguna fase anterior (así se habría detectado `proposal.md`);
    - los bats de R-02;
    - la validación de `docs/spec/*.json` contra el esquema de R-01.
- **Beneficio:** la deriva documental se detecta antes del release. Se mide con las entradas "Fixed — documentation drift" en el CHANGELOG, que deberían tender a 0.
- **Esfuerzo** S–M · **Prioridad** alta · **Riesgo** bajo · **Jueces:** DM, AG.

### R-08: Liberar por cambio, con manifiesto de release y modo trunk
- **Origen:** DM-03 + PM-04 (2 jueces). La regla global del dueño ya exige revisar `git log origin/master..origin/dev`.
- **Problema:** H-21. QA revisa `feature → dev` (`karvey-qa/SKILL.md:20-29`), no lo que llega a master. El rollback revierte todo junto (`karvey-deploy/SKILL.md:241`). El propio repo usa trunk (`docs/spec/project.json:16-20`: integration = production = `main`), y el método no modela ese caso.
- **Recomendación:**
  - Agregar un paso 2.8-bis: `git log origin/{production}..origin/{integration}` mapeado a change-ids mediante el trailer `Karvey-Change: {id}`, que impl agrega a cada commit.
  - Bloquear si hay commits sin trailer o de cambios sin `qa.approved` (o sin `skipped` por carril). Empezar en modo **advertir**.
  - El cuerpo del PR lista todos los change-ids y versiones, y `approvals.prod` se registra en todos.
  - La integración a dev pasa por PR (`--base dev`).
  - Agregar `branch_flow.mode: trunk | env-branches`.
  - Ofrecer `release/*` + cherry-pick como salida.
  - El manifiesto sirve también de notas de release para el cliente (R-19).
- **Justificación:** hoy la unidad aprobada es el cambio y la unidad liberada es la rama. Es una brecha de gobierno, peor en multi-tenant.
- **Beneficio:** 0 commits sin QA en prod por arrastre y rollback por cambio. Se mide con el % de releases cuyo manifiesto calza con `approvals.prod` (meta 100%).
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** medio: frena a equipos acostumbrados a promover dev completo · **Jueces:** DM, PM.

### R-09: Carriles por tamaño de cambio
- **Origen:** DM-01 + PM-09 (2) + AG-04 (implícito: "una fase por sesión") (3 jueces).
- **Problema:** un solo pipeline para todo `feature` (`karvey/rules/multi-agent.md:88-89`), además de H-03, H-04 y H-22. La regla global del usuario manda pasar por Karvey incluso un BUG-NN de una línea. Cuando el método no ofrece un camino barato y legítimo, el equipo toma uno ilegítimo, que es justo lo que muestra `team-adapters`.
- **Recomendación:** crear `rules/lanes.md` con una matriz carril × fase (obligatoria / opcional / omitida):
  - `patch` (≤ ~50 líneas, sin cambio de contrato): iterate/init-lite → impl test-first → qa-lite → deploy. 1 gate humano (prod).
  - `standard` (sin UI nueva): requirements → architecture + tasks → impl → test → qa → deploy → archive.
  - `feature-ui`: el pipeline completo.
  - `ops`, `hotfix` y `method/docs`: los actuales.

  Además:
  - `karvey-init` decide el carril con 3 preguntas objetivas: ¿toca UI?, ¿cambia contratos o esquema?, ¿toca trust boundaries? Se guarda en `spec.json:lane`.
  - Las fases omitidas quedan como `skipped` (R-01).
  - Se puede subir de carril, pero nunca bajar sin registro.
  - QA-lite verifica que el tamaño del diff respete el carril.
- **Beneficio:** menor lead time para fixes chicos, fin de los callejones y dashboards honestos. Se mide con el lead time por carril (R-14).
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** medio: abuso del carril `patch`, mitigado con criterios objetivos · **Jueces:** DM, PM, AG.

### R-10: Menos gates humanos, con más peso y sin auto-aprobación
- **Origen:** DM-06 + AG-08 + PM-09 (3) (3 jueces).
- **Problema:**
  - 7 aprobaciones por feature (`karvey/rules/living-specs.md:57-66`), cada una con un "Shall we advance" doble (12 skills). AG estima ≈50–70 interrupciones por ciclo.
  - H-05 y H-06.
  - Grill hace una pregunta por mensaje, hasta 27 + 6 (`karvey-grill/SKILL.md:187`).
- **Recomendación:**
  - En `standard` y `feature-ui`, 3 gates:
    1. **Qué**: requirements + mockup, con la validación spec↔mockup que ya existe.
    2. **Cómo**: architecture + infra + tasks, con un resumen de una página.
    3. **Prod.**
  - Dejar `--granular-gates` como opción.
  - Un solo `AskUserQuestion` por gate: `[Aprobar y avanzar (recomendado) · Aprobar y parar · Pedir cambios]`.
  - `-y` registra `role:"auto"` y queda prohibido en prod.
  - design-graphic pide su aprobación.
  - Grill pregunta por rama, hasta 4 preguntas por `AskUserQuestion`, y la rama de stack se infiere del repo.
  - Alinear `allowed-tools` con lo que cada skill hace.
- **Justificación:** un gate que casi nunca rechaza entrega poca información, genera espera y termina en "rubber stamp", que es lo que el mismo método teme (`karvey/rules/deploy-workflow.md:13-14`).
- **Beneficio:** de ~13 a 3 interrupciones de fase por feature y −40–50% de interrupciones en total. Se mide con la tasa de rechazo por gate y el tiempo de espera humano (R-14).
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** medio: cambio cultural · **Jueces:** DM, PM, AG.
- **Desacuerdo:** DM quiere fusionar gates (de 7 a 3). PM y AG no reducen el número: PM agrupa solo en el carril `small` y AG mantiene los gates pero quita la pregunta doble. **Mi recomendación:** fusionar a 3 gates **solo si** se hace junto con R-11 (jueces). Un gate fusionado revisa más superficie, y el veredicto independiente de los jueces es lo que evita que se vuelva un timbre. Si el dueño rechaza los jueces, conviene quedarse con la versión de AG: mismos gates y un solo `AskUserQuestion`.

### R-11 (JU-01): Paneles de jueces expertos en los gates tempranos
- **Origen:** Mauricio (dueño). Se superpone con AG-12 (juez con contexto limpio para design, "fiscal" antes de `qa.approved`), DM-08 y AG-12 (second-opinion cae al mismo modelo) y DM-06 (gates con más peso).
- **Verificación en el repo:**
  - La única revisión independiente es QA Dimensión 7, que invoca `karvey-second-opinion` sobre el **diff**, al final (`karvey-qa/SKILL.md:104-106,177`). Su fallback es un subagente de la misma familia (`karvey-second-opinion/SKILL.md:63`).
  - El LLM-judge existe solo para comparar modelos (`karvey-benchmark-models/SKILL.md:36-38`).
  - Los subagentes de architecture son de descubrimiento, no de revisión (`karvey-architecture/SKILL.md:34-36`).
  - design-graphic se autopuntúa (`karvey-design-graphic/SKILL.md:154-186`), y la validación spec↔mockup la hace el mismo autor.
  - `grep -ri judge` no encuentra ningún panel en requirements, architecture ni tasks. **Confirmado: no hay revisión independiente antes de QA.**
- **Problema:** los defectos de spec y de diseño se descubren en QA o en prod, donde son más caros. La aprobación humana llega solo con la versión del autor. Esta misma evaluación con 3 jueces encontró 34 defectos confirmados que ningún gate había detectado.
- **Recomendación:**
  - Nueva skill `karvey-judges` + regla `rules/judges.md`. Antes de los gates de requirements, architecture y tasks (y opcionalmente mockup y design), corren 2–3 jueces en paralelo como subagentes con contexto limpio.
  - Lentes según la fase:
    - requirements: dominio/negocio + métodos (EARS, testabilidad);
    - mockup/design: UX/accesibilidad (con el `contrast-check.py` determinista de AG-12);
    - architecture: seguridad + métodos + agentes/costo;
    - tasks: gestión (dependencias, tamaño, tareas `[human]`) + testabilidad.
  - Cada juez recibe solo los artefactos de la fase y una **rúbrica por fase** en `rules/judges/{fase}.md`, y debe citar `archivo:línea`. Un hallazgo sin cita se descarta.
  - La salida va a `findings.md` con `origin: judge:{lente}` y la enruta `karvey-iterate`. El juez observa y no enruta, igual que test y QA.
  - El gate humano muestra un resumen: veredicto por juez, hallazgos bloqueantes y el desacuerdo entre jueces, si lo hay.
  - Configuración en `project.json:judges`:
    ```json
    "judges": {
      "phases": {
        "requirements": ["domain", "methods"],
        "architecture": ["security", "methods", "agents"],
        "tasks": ["pm", "testability"]
      },
      "mode": "advisory",
      "budget": {"tokens_per_gate": 40000, "usd_per_change": 3},
      "cross_model": "prefer"
    }
    ```
  - Con `mode: blocking`, un hallazgo Critical/High abierto impide el approve en `karvey-state.py`.
  - Por carril: `patch` sin jueces, `standard` con 2 y `feature-ui` con 3.
  - Usar otro modelo cuando exista un CLI disponible, reutilizando la detección de `karvey-second-opinion`, y declarar siempre si fue intra-modelo.
- **Justificación:** revisión independiente en el punto más barato del ciclo, y un juez con contexto limpio no hereda el razonamiento del autor. Es el mismo principio four-eyes que el método ya aplica en QA, adelantado a las fases donde un error cuesta menos.
- **Beneficio:**
  - Los spec-gaps se detectan antes de impl y hay menos retrabajo.
  - El humano aprueba con información independiente.
  - Hace viable fusionar gates (R-10).
  - Se mide con: spec-gaps encontrados en judges contra los encontrados en test, QA o prod (debería desplazarse hacia la izquierda); `iteration_count` por cambio; costo de los jueces contra retrabajo evitado; tasa de hallazgos de juez aceptados (si es baja, sobra un juez o la rúbrica es mala).
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** medio: costo en tokens (AG estima ~3–6k por subagente, más la lectura de artefactos) y ruido si la rúbrica es vaga. Se mitiga con presupuesto, modo advisory por defecto y la métrica de aceptación · **Jueces que la respaldan:** AG (AG-12) y DM (DM-06, DM-08), en forma parcial.
- **Tensión:** esto choca con AG-04 (bajar el costo de contexto). Se resuelve porque los jueces son subagentes: su costo no se acumula en el contexto del hilo principal, que solo recibe el resumen. El límite es el `budget` del proyecto.

### R-12: Test-first y matriz de trazabilidad REQ → tarea → commit → test
- **Origen:** DM-07 (1 juez).
- **Problema:**
  - En impl el test va después del código (`karvey-impl/SKILL.md:89-105`).
  - `karvey-test` no consume el "Test coverage plan" de architecture (`karvey-architecture/SKILL.md:232-243`).
  - Los IDs de test no referencian requisitos.
  - La evidencia está en `docs/test_evidence.md`, compartido entre cambios.
  - QA marca "Tests pass" sin ejecutar la suite (`karvey-qa/SKILL.md:202-203`).
- **Recomendación:**
  - `karvey-tasks` genera una tarea de test en rojo antes de cada requisito.
  - Convención `test_REQ_1_2_*` o `@req 1.2`.
  - Crear `changes/{id}/traceability.md` por script, usando el trailer de R-08.
  - Mover la evidencia a `changes/{id}/`.
  - Gate: todo requisito ADDED/MODIFIED tiene un test verde o una excepción `manual` justificada.
  - QA ejecuta la suite o cita el run de CI del commit exacto.
- **Beneficio:** un requisito sin test queda visible antes del merge. Se mide con el % de requisitos con test automatizado.
- **Esfuerzo** M · **Prioridad** media-alta · **Riesgo** bajo-medio: capas sin runner (SPs, UI legacy) · **Jueces:** DM.

### R-13: Gate de seguridad con herramientas deterministas
- **Origen:** DM-08 + AG-12 (parcial) (2 jueces).
- **Problema:** el "SECURITY GATE (blocking)" es un checklist que juzga el LLM (`karvey-qa/SKILL.md:36-65`). No hay SCA, secretos ni SAST, y en infra no hay escaneo de IaC (`karvey-infra/SKILL.md:141-164`).
- **Recomendación:**
  - La Dimensión 1 ejecuta lo que esté disponible y cita la salida: `gitleaks` o `trufflehog`, `semgrep --config auto`, `osv-scanner` o `npm/pip audit`, y `checkov` o `trivy config`.
  - Si una herramienta falta, la categoría queda como **not evaluated**.
  - El LLM tría falsos positivos y cubre lo que las herramientas no ven (IDOR, lógica de tenant).
  - `karvey-infra` propone llevar estas herramientas al pipeline de PR.
- **Beneficio:** veredicto reproducible. Se mide con los hallazgos de herramienta por release y los "not evaluated" en el dashboard.
- **Esfuerzo** S–M · **Prioridad** media-alta · **Riesgo** bajo · **Jueces:** DM, AG.

### R-14: Métricas de flujo y DORA desde los artefactos, con `phase_history`
- **Origen:** DM-11 + PM-05 + PM-12 (2 jueces).
- **Problema:** los datos existen (`created_at`, `approvals.*.date`, `iteration_count`, `revision_history`, el historial de BUG-NN), pero nadie los agrega. `approvals` guarda solo la fecha, sin hora. `karvey-retro` mide commits por autor (`karvey-retro/SKILL.md:20-47`).
- **Recomendación:**
  - Agregar `spec.json:phase_history[{phase, entered_at, exited_at}]`, escrito por `karvey-state.py`, y fechas ISO con hora en `approvals`.
  - Agregar `spec.json:deploys[{env, version, canary, rollback}]`.
  - Nuevo `karvey-context --metrics` que calcule, por carril y período: lead time, cycle time por fase, espera de aprobación humana, throughput, frecuencia de deploy, CFR, MTTR, tasa de spec-gap y ripple, tasa de rechazo por gate, precisión de estimación (R-05) y aceptación de jueces (R-11).
  - Rehacer `karvey-retro` sobre estas métricas y guardar `retro-{fecha}.md`. Cada acción queda como un `BL-NN` de tipo `process` con dueño, y la retro siguiente revisa si se cumplieron. El análisis por persona queda como opcional.
- **Beneficio:** decidir con datos qué gates, fases y jueces sirven. Cierra el circuito de R-09, R-10 y R-11.
- **Esfuerzo** M · **Prioridad** alta: es la condición para evaluar la Ola 2 · **Riesgo** bajo · **Jueces:** DM, PM.

### R-15: Presupuesto de contexto por fase y carga progresiva
- **Origen:** AG-04 (1 juez, con medición).
- **Problema:** H-34. Una fase carga entre 3k y 27k tokens. El cierre transitivo alcanza 11–17 de las 22 reglas porque `phase-close.md` cita 7 y `project-config.md` cita 8. El ciclo no cabe bajo el umbral de rotación de 150k.
- **Recomendación:**
  - Crear `rules/_core.md` (~800 palabras) con los contratos duros, y que cada skill declare `Load:` como una lista cerrada.
  - Llevar los adaptadores a `adapters/{tool}.md`, cargados según `management.tool`.
  - Partir deploy en un núcleo más `references/`.
  - Mover `init --settings` a `references/`.
  - El orquestador queda solo con el ruteo.
  - Declarar el patrón "una fase por sesión" con `checkpoint`.
- **Beneficio:** −45–55% de tokens por fase y ciclos que caben en 1–2 sesiones (estimación de AG).
- **Esfuerzo** M · **Prioridad** media · **Riesgo** bajo-medio: hay que re-probar que ninguna fase pierda una regla que necesita · **Jueces:** AG, con apoyo indirecto de DM-15 y PM-09.

### R-16: Graphify y el ritual del tracker, fuera del camino caliente
- **Origen:** AG-05 + DM-15 + PM-09 (1) (3 jueces).
- **Problema:**
  - H-31.
  - El ritual completo por tarea (`karvey/rules/phase-close.md:10`): AG cuenta 4–6 llamadas por tarea, unas 150 por Epic.
  - Graphify no se declara como dependencia.
- **Recomendación:**
  - Agregar `knowledge_sync: none | graphify | obsidian`, con `none` por defecto si no se detecta graphify.
  - Correr la sincronización en archive y a pedido.
  - Un hook PostToolUse sobre `docs/spec/**` anota las rutas cambiadas en `.graph-pending`.
  - El tracker actualiza el estado por tarea, pero el comentario y la cascada van por Feature.
- **Desacuerdo:** DM quiere sincronizar en cada gate humano y en archive, AG solo en archive, y PM por fase. **Mi recomendación:** la de AG. En medio de una fase nadie consume el grafo, porque la fase siguiente lee los artefactos directamente.
- **Beneficio:** entre 10k y más de 100k tokens menos por ciclo, y menos omisiones silenciosas cuando graphify no está.
- **Esfuerzo** S · **Prioridad** media-alta · **Riesgo** bajo · **Jueces:** DM, PM, AG.

### R-17: Living specs: fusionar el spec-delta en el PR del código
- **Origen:** DM-09 + AG-10 (spec-merge) (2 jueces).
- **Problema:** el merge del delta ocurre en archive, después de prod (`karvey-archive/SKILL.md:42-90`). En el único proyecto inspeccionable nunca ocurrió: no existe `docs/spec/specs/`.
- **Recomendación:**
  - Fusionar el delta en la rama del cambio, antes del PR a prod, con `scripts/karvey-spec-merge.py --dry-run`.
  - Archive queda en mover la carpeta y cerrar la Epic.
  - `karvey-context` avisa "deployed sin archive > N días".
- **Desacuerdo:** AG ubica el script en archive y DM el momento antes de prod. **Mi recomendación:** el momento de DM con el script de AG.
- **Beneficio:** "spec == prod" y menos spec-gaps por especificar contra una spec vieja. Se mide con 0 cambios desplegados sin delta fusionado.
- **Esfuerzo** S · **Prioridad** media-alta · **Riesgo** bajo · **Jueces:** DM, AG.

### R-18: Dashboard completo: trabajo abierto, antigüedad y WIP
- **Origen:** PM-06 + AG-10 (`karvey-context.py`) (2 jueces).
- **Problema:** H-30. La línea de aprobaciones termina en `tasks` (`karvey-context/SKILL.md:138`). El JSON se parsea con `grep -o` (`:75-77`). No hay antigüedad ni límite de WIP.
- **Recomendación:**
  - Crear `scripts/karvey-context.py` con una sección `OPEN WORK`: findings por tipo, BUG-NN no resueltos, tareas `[human]` en `awaiting-human` con su ejecutor y desde cuándo, y backlog `open`.
  - Mostrar días en la fase actual y marcar "estancado".
  - Mostrar todas las aprobaciones, con quién aprobó.
  - Agregar `project.json:wip_limit`.
- **Beneficio:** en un solo lugar se ve qué está bloqueado y qué espera a una persona. Se mide con la antigüedad media del WIP.
- **Esfuerzo** S · **Prioridad** alta · **Riesgo** bajo · **Jueces:** PM, AG.

### R-19: Visibilidad para stakeholders y eventos de "te toca a ti"
- **Origen:** PM-07 (1 juez).
- **Problema:** las notificaciones cubren solo qa, deploy e incident (`karvey/rules/notifications.md:14,30-34`). La sección "Stakeholders" del PRD no se usa después.
- **Recomendación:**
  - Agregar los eventos `approval_requested`, `awaiting_human` y `blocked`, este último incluyendo el veredicto de los jueces (R-11).
  - Nuevo `karvey-context --report [--since] [--client]` en lenguaje de negocio, que parte del manifiesto de R-08.
- **Beneficio:** menos espera de aprobación. Se mide con R-14.
- **Esfuerzo** M · **Prioridad** media · **Riesgo** bajo: cuidar la fuga de información entre tenants · **Jueces:** PM.

### R-20: Scripts de release-gate, IDs, health score y evidencia
- **Origen:** AG-10 + AG-07 + PM-13 + AG-12 (evidence) (2 jueces).
- **Problema:**
  - El Step 0 de deploy lo lee el LLM (`karvey-deploy/SKILL.md:18-46`).
  - Los contadores funcionan con "lee y suma 1" (H-35, no reproducido en el repo, pero el mecanismo está en el texto).
  - `E{1..99}`.
  - La fórmula de health no es reproducible (`karvey-health/SKILL.md:53`) y el timestamp va fijo en "Chile time".
- **Recomendación:**
  - `karvey-release-gate.py` con salida JSON y exit ≠ 0 si falla.
  - `karvey-id.py next {BUG|D|BL|F}` con `flock`, IDs `BUG-NN@repo` y lectura de las ramas remotas.
  - `karvey-health-score.py` con funciones explícitas y `KARVEY_TZ`.
  - `karvey-evidence.sh -- <cmd>` que escribe en `evidence.jsonl`.
- **Beneficio:** gates reproducibles, 0 IDs duplicados y ~2–4k tokens menos por deploy.
- **Esfuerzo** M · **Prioridad** media · **Riesgo** bajo · **Jueces:** PM, AG.

### R-21: QA observa sin arreglar, artefactos dentro del cambio y reglas de stack a `standards/`
- **Origen:** DM-14 + AG-14 (parcial) (2 jueces).
- **Problema:** H-28 y H-29. Hay reglas propias del stack de HainTech en QA: Axios/apiService, `v-html` y RUT (`karvey-qa/SKILL.md:38-40,78`).
- **Recomendación:**
  - QA no commitea; los arreglos visuales van como finding `bug`.
  - La revisión se guarda en `changes/{id}/qa/REVISION_PR_*.md`.
  - Las reglas de stack pasan a `standards/frontend.md` y se evalúan en D9.
- **Esfuerzo** S · **Prioridad** media · **Riesgo** bajo · **Jueces:** DM, AG.

### R-22: Descripciones de frontmatter cortas y sin triggers genéricos
- **Origen:** AG-11 (1 juez, con medición).
- **Problema:** H-23. Además, triggers como `deploy` y `QA` compiten con la skill `deploy` del usuario y con la skill incorporada `code-review`, y hay 10 frases repetidas entre `karvey`, `grill` e `init`.
- **Recomendación:**
  - Descripciones de ≤250 caracteres con la forma "Karvey fase N — qué produce — cuándo".
  - Prefijar los triggers genéricos con el contexto ("karvey deploy").
  - Quitar las marcas de terceros de los triggers.
  - Usar `disable-model-invocation: true` en `guard`, `team`, `benchmark-models`, `scrape`, `import` y `retro`.
  - El lint de R-07 controla el largo.
- **Beneficio:** las 32 skills visibles en el listado y ~2,3k tokens menos por sesión.
- **Esfuerzo** S · **Prioridad** media-alta: hoy 12 skills no se activan bien, y es barato · **Riesgo** bajo · **Jueces:** AG.

### R-23: El canary pasa a ser una verificación post-deploy con umbrales
- **Origen:** DM-10 + PM-05 (2) (2 jueces).
- **Problema:** "Noticeable degradation = regression" (`karvey-deploy/SKILL.md:234`). No hay umbrales, ni una ventana definida, ni un rollback definido (`:238-241`).
- **Recomendación:**
  - En `infra.md`, un contrato por servicio con health, rutas críticas, umbrales (error rate, p95 contra el baseline de prod), ventana, fuente de métricas y comando de rollback.
  - `deploy_evidence.md` por cambio.
  - Renombrar el paso a "post-deploy verification".
- **Beneficio:** CFR y MTTR medibles.
- **Esfuerzo** M · **Prioridad** media · **Riesgo** bajo · **Jueces:** DM, PM.

### R-24: Decisiones pendientes (Q-NN) y riesgos con dueño y fecha
- **Origen:** PM-11 (1 juez).
- **Problema:** `cross` termina en "no answer exists" sin dueño ni fecha (`karvey-decisions/SKILL.md:65-66`). Los riesgos de architecture no se revisan en ninguna fase posterior (`karvey-architecture/SKILL.md:214-218`). La ruta del log de decisiones es inconsistente (H-33).
- **Recomendación:**
  - Nuevo `decisions ask`, que registra `Q-NN` con dueño y `needed-by` y pasa a `D-NN` cuando se resuelve.
  - Un `risks.md` por cambio, revisado en QA y deploy.
  - Unificar la ruta del log.
  - El juez de seguridad de R-11 alimenta `risks.md`.
- **Esfuerzo** M · **Prioridad** media · **Riesgo** bajo · **Jueces:** PM.

### R-25: Costo por cambio también con un solo agente
- **Origen:** PM-08 (1 juez).
- **Problema:** el costo solo se mide en la capa de equipo (`karvey/rules/team.md:40`). La statusline ya recibe el costo de la sesión (`hooks/karvey-statusline.sh:5`), pero no se guarda en ningún artefacto.
- **Recomendación:**
  - Guardar `spec.json:effort{ai_usd, tokens, human_review_min}` en el cierre de fase, marcado como estimado cuando no sea exacto.
  - Agregarlo por `client_tag`.
  - El costo de los jueces se registra aparte, para evaluar R-11.
- **Esfuerzo** M · **Prioridad** media · **Riesgo** medio: depende de lo que exponga el runtime (`team-layer` F-03 sigue abierto) · **Jueces:** PM.

### R-26: Sistema de diseño a nivel de proyecto; design-graphic como delta
- **Origen:** DM-13 + AG-12 (autopuntaje) (2 jueces).
- **Problema:** design-graphic redefine la paleta y la tipografía **en cada cambio** (`karvey-design-graphic/SKILL.md:57-141`) y se autopuntúa (≥8).
- **Recomendación:**
  - Crear `docs/spec/design-system.md` una sola vez por proyecto; por cambio, solo el delta.
  - El catálogo de arte pasa a opt-in.
  - El puntaje lo pone el juez UX de R-11, con `contrast-check.py`.
- **Esfuerzo** S–M · **Prioridad** media · **Riesgo** bajo · **Jueces:** DM, AG.

### R-27: WBS sin ambigüedad sobre qué es una Feature
- **Origen:** PM-10 (1 juez).
- **Problema:** "Feature" es a la vez un área funcional (`karvey-requirements/SKILL.md:155`) y una fase del pipeline (`karvey/rules/phase-close.md:23`). QA y Deploy quedan fuera de la jerarquía E.F.T, y hay dependencias que duplican la relación padre-hijo.
- **Recomendación:**
  - Feature = área funcional.
  - Las fases van como checklist o campo del Epic.
  - Agregar `E{n}.QA` y `E{n}.DEPLOY`.
  - Usar parent/child en vez de dependencias para la jerarquía.
- **Esfuerzo** S · **Prioridad** media · **Riesgo** bajo · **Jueces:** PM.

### R-28: Vista de portafolio multi-cliente
- **Origen:** PM-14 (1 juez).
- **Recomendación:**
  - Subir `client` a campo de primer nivel en `project.json` y `spec.json`.
  - Agregar `karvey-context --portfolio portfolio.json`, que lee varios `project.json`, de solo lectura.
- **Beneficio:** responder "¿cómo vamos con el cliente X?" con un comando.
- **Esfuerzo** M · **Prioridad** media-baja · **Riesgo** bajo: controlar quién ve el portafolio consolidado · **Jueces:** PM.

### R-29: Backlog con priorización (WSJF) y estado `done-direct`
- **Origen:** PM-15 (1 juez).
- **Problema:** solo hay prioridad `high/med/low`. BL-01 quedó en `done` "resolved directly", un estado que no está definido (`docs/spec/backlog.md:5,13`).
- **Recomendación:**
  - Agregar las columnas value, effort, cost_of_delay y client, con un puntaje WSJF.
  - Agregar el estado `done-direct` con el commit como referencia.
  - Agregar `karvey-context --backlog`.
  - Refinar el backlog cada 2 semanas.
- **Esfuerzo** S · **Prioridad** baja · **Riesgo** bajo · **Jueces:** PM.

### R-30: Portabilidad a otros runtimes y equipos
- **Origen:** AG-14 (1 juez).
- **Problema:**
  - `open` es solo de macOS (`karvey-mockup/SKILL.md:187`).
  - "Chile time" fijo.
  - Estados en español dentro de un cuerpo en inglés.
  - `karvey-browse` no tiene un adaptador `via`, y este mismo usuario delega el navegador al agente del Mac.
  - `karvey-health` lee la versión desde `marketplaces/`, no desde `cache/`, que es lo que realmente carga el runtime.
- **Recomendación:**
  - `project.json:browse.via` (`local | agent:<name> | none`).
  - Estados neutrales con alias localizados.
  - Leer la versión desde `installed_plugins.json`.
  - Un `AGENTS.md` generado para Codex o Gemini.
- **Esfuerzo** M · **Prioridad** baja-media · **Riesgo** bajo · **Jueces:** AG.

---

## 4. Plan por olas

### Ola 1: corrección y quick wins → **3.12.0** (compatible hacia atrás)
**Incluye** R-01, R-02, R-03, R-04, R-05, R-06, R-07, R-16, R-18, R-22, R-17 (solo el script) y R-21.
- La Ola 1 cierra todos los hallazgos Confirmado de §2.
- Scripts nuevos: `karvey-state.py`, `prod-gate.sh`, `karvey-handoff-capture.sh`, `karvey-context.py` y `lint-plugin.py`, más los bats.
- `validate` corre en modo **advertencia** sobre los `spec.json` viejos. `--fix` los migra, empezando por los dos de `docs/spec/`.
- **Karvey 3.12.0 se hace con Karvey**, en carril `standard` y usando el modo trunk que ya usa el repo. Así se corrige también el dogfooding (H-22).

**El dueño decide antes de empezar:**
1. Quién crea el marcador de plan: un hook `UserPromptSubmit` o el agente. Esto obliga a ajustar la regla global.
2. Si `prod-gate` viene activado por defecto o sigue siendo opt-in, como los otros hooks.
3. Dónde vive el registro de prod: D-NN + PR + `spec.json` en archive (recomendado) o solo en el PR.
4. El umbral de rotación: 8 h o 24 h.

### Ola 2: estructural → **3.13.0** en modo advisory; **4.0.0** al pasar los defaults a bloqueante
**Incluye** R-09 (carriles), R-10 (3 gates), R-11 (jueces, JU-01), R-08 (release por cambio), R-14 (métricas + retro), R-12 (test-first), R-13 (herramientas de seguridad), R-20, R-23 y R-17 (momento del merge antes de prod).

**Orden interno:**
1. R-14, para tener la línea base antes de cambiar el proceso.
2. R-09 + R-11 en modo advisory.
3. R-10 + R-08 en modo advertir.
4. Después de 4–6 cambios medidos, pasar a bloqueante y publicar 4.0.0.

Es **breaking** porque cambia el número de gates, el esquema de `spec.json` pasa a ser obligatorio (`lane`, `phase_history`, `skipped`), el manifiesto de release bloquea y la integración a dev pasa por PR.

**El dueño decide antes de empezar:**
- 3 gates (fusionados) o 7 gates con una sola pregunta cada uno.
- Jueces advisory o blocking por defecto, y en qué fases.
- El presupuesto por gate y por cambio para los jueces.
- Si se exige el trailer `Karvey-Change` en los commits.
- Los criterios objetivos del carril `patch`, y si su regla global ("Karvey siempre, incluso un BUG de una línea") acepta que ese carril sea el camino legítimo para los BUG-NN chicos.

### Ola 3: optimización → **4.1.0**
**Incluye** R-15 (presupuesto de contexto y `_core.md`), R-19 (stakeholders), R-24 (Q-NN y riesgos), R-25 (costo por cambio), R-26 (design system), R-27 (WBS), R-28 (portafolio), R-29 (backlog WSJF) y R-30 (portabilidad).
- R-15 va aquí porque reorganiza todas las skills. Conviene hacerlo cuando el contenido ya esté estable después de la Ola 2, para no reestructurar dos veces.

**El dueño decide antes de empezar:**
- El formato del reporte al cliente y quién lo recibe.
- El alcance del portafolio: HainTech completo o por célula.
- Si Karvey debe soportar otros runtimes (R-30) o sigue solo en Claude Code.

---

## 5. Lo que el panel recomienda NO cambiar

Es la unión deduplicada de las tres listas.

- **Un solo router de hallazgos, y quien observa no enruta** (`karvey/rules/iteration-loop.md:80-85`). Los tres jueces lo incluyen. Los jueces de R-11 deben respetarlo: observan y `karvey-iterate` enruta.
- **La clasificación `bug` / `spec-gap` / `emergent`, con el ripple quirúrgico** (`iteration-loop.md:26-35`, `karvey-iterate/SKILL.md:69-76`). Además, `emergent` nunca bloquea y nunca se absorbe en silencio.
- **El gate de prod nunca se delega a un agente y no se pide sobre un gate rojo** (`karvey/rules/multi-agent.md:63`, `karvey/rules/deploy-workflow.md:11-15`). Los tres jueces lo incluyen. Solo falta hacerlo cumplir con un hook (R-02).
- **`verification.md` tal cual**, escrito como síntomas observables. A lo más se hacen ejecutables algunas partes (R-20).
- **Un solo agente por defecto y la capa de equipo opt-in**, con su propia contra-evidencia de costo (`karvey/rules/team.md:7-41`).
- **El handoff "producido, no redactado", y un hook de sesión que mide y no invoca skills.** Solo hay que corregir sus bugs (R-06).
- **La statusline fuera del turno**, con costo cero de tokens.
- **EARS con el litmus "¿se puede escribir sin mencionar tecnología?"** y la trazabilidad PRD → EARS.
- **La validación spec↔mockup antes de diseño y arquitectura**, que es el punto más barato para encontrar un spec-gap. Se mantiene en `feature-ui`.
- **Estimar en minutos de IA más revisión humana**, como hipótesis. Solo hay que medir el real (R-05).
- **Tareas `[human]` con comando, verificación read-only y rollback**, y `awaiting-human` que bloquea solo a las dependientes.
- **Los estados lógicos del tracker con adaptadores por herramienta.**
- **Estándares fuera del plugin público, y "not evaluated ≠ conformant".** El gate de standards calibrado: una desviación aprobada no es hallazgo y un `draft` no genera Critical.
- **La Iron Law de investigate, con la excepción del hotfix en vivo**, y el carril hotfix con fix + BUG-NN + regresión en el mismo PR.
- **Un incidente solo llega a RESUELTO con test de regresión, y su historial de estados no se sobrescribe.**
- **`decisions cross` antes de declarar un bloqueo**, respaldado por el dato de 13 de 14 bloqueos ya respondidos.
- **La prohibición de leer destinos desde `CLAUDE.md`** (`karvey-qa/SKILL.md:285`).

---

## 6. Decisiones que necesita el dueño

1. **Número de gates humanos por feature:** 3 fusionados (DM, recomendado junto con los jueces) o 7 con un solo `AskUserQuestion` cada uno (AG). En los dos casos queda `--granular-gates` como opción.
2. **Jueces (JU-01):** advisory o blocking por defecto (recomiendo advisory hasta tener 4–6 cambios medidos); en qué fases; presupuesto de tokens y US$; si exigir otro modelo o aceptar intra-modelo declarado.
3. **Breaking changes:** si la Ola 2 sale como 4.0.0 con el esquema de `spec.json` obligatorio, los gates fusionados y el manifiesto bloqueante, o si todo queda opt-in en la línea 3.x.
4. **Carril `patch` y tu regla global.** Hoy tu `CLAUDE.md` exige el método completo incluso para un BUG de una línea. Hay que decidir si `patch` es el camino oficial para esos casos.
5. **Quién crea el marcador de plan:** un hook `UserPromptSubmit` (recomendado) o el agente, como dice hoy tu regla global.
6. **`prod-gate`:** activado por defecto o opt-in.
7. **Release por cambio:** si exigir el trailer `Karvey-Change` y la integración a dev por PR. También, si el modo trunk pasa a ser el recomendado, que es el que usa el propio repo.
8. **Graphify:** si queda como dependencia declarada del método o pasa a ser opcional con `knowledge_sync: none` por defecto.
9. **Dogfooding:** si 3.12.0 se hace obligatoriamente con Karvey sobre sí mismo, lo que exige cerrar `team-layer` y `team-adapters` antes de empezar.
