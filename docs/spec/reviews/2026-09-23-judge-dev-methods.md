# Revisión del Método Karvey 3.11.1 — lente: métodos de desarrollo

> Alcance leído: `README.md`, `CHANGELOG.md`, orquestador `plugins/karvey/skills/karvey/SKILL.md`, las 22 reglas de `skills/karvey/rules/` (y verifiqué que las 9 copias locales en init/requirements/architecture/tasks son byte-idénticas), los 13 SKILL.md de fase, las 18 skills de soporte, `plugins/karvey/hooks/` + `skills/karvey/hooks/`, y `docs/spec/` (el método aplicado a sí mismo). Rutas relativas a `plugins/karvey/` salvo que diga otra cosa. Revisión de solo lectura: no modifiqué ningún archivo del plugin.

---

## 1. Veredicto general

Karvey es un método **maduro en el diagnóstico y en la cultura de evidencia, e inmaduro en lo ejecutable**. Hay ideas que están por sobre el estado del arte de SDD: el loop de iteración con tres aristas (`bug` / `spec-gap` / `emergent`) y un único router, la disciplina causal de `karvey-investigate`, las 18 reglas de `verification.md` y la regla de "nunca pedir el OK de prod sobre un gate rojo". Ni Spec Kit ni Kiro traen algo así.

Lo que más frena el trabajo es que **el pipeline es uno solo para todos los tamaños de cambio**. Tiene 13 fases, 7 gates humanos y un "¿avanzamos?" en cada fase, sin carriles por tamaño. Además, **la máquina de estados vive en prosa y no está validada**: los valores de `phase` que escriben las skills no coinciden con los que lee el orquestador, y varias fases quedan en callejón sin salida. A eso se suma que **el release se hace promoviendo una rama de ambiente (`dev → master`)** y no por cambio. El propio repo lo confirma: de sus dos cambios, uno llegó a producción con `qa.approved=false` y el otro quedó en `impl` después de publicarse. Cuando el costo del método supera lo que el cambio vale, el equipo se salta los gates. La corrección de fondo es que el método **escale con el tamaño del cambio** y que **sus reglas se validen con código**, no con redacción.

---

## 2. Fortalezas

- **Loop de iteración con tres aristas y un solo router.** Hay un litmus test explícito para clasificar hallazgos (`skills/karvey/rules/iteration-loop.md:32-35`). Quien observa no enruta (`iteration-loop.md:80-85`). `emergent` nunca bloquea, pero se exige capturarlo (`iteration-loop.md:78`). Es la mejor respuesta que he visto al "queda botado" de los pipelines lineales de SDD.
- **Ripple set quirúrgico en `spec-gap`.** Solo se reabren las aprobaciones afectadas, sin rehacer el pipeline (`skills/karvey-iterate/SKILL.md:69-76`), y queda registro append-only en `revision_history` (`rules/living-specs.md:88`).
- **Disciplina causal en la depuración.** `karvey-investigate` exige fechar el síntoma, preguntar "¿qué cambió?" antes que "¿qué está mal?", y separar causa de fragilidad latente con un gate de coherencia temporal (`skills/karvey-investigate/SKILL.md:20-54`). Es una práctica de nivel SRE postmortem.
- **Reglas de verificación basadas en fallas reales.** Algunos ejemplos: "falló" vs "nunca corrió" se distingue por la duración; `curl | sha256sum` da exit 0 con una respuesta falsa; un test verde sobre código que nadie llama no prueba nada (`rules/verification.md:26-37`).
- **Gates del PR antes del OK humano.** "Never ask a human to approve over a red or unresolved gate — that turns the approval into a rubber stamp" (`rules/deploy-workflow.md:11-15`; `skills/karvey-deploy/SKILL.md:177-201`). Además detecta el host de git en vez de asumir `gh` (`karvey-deploy/SKILL.md:90-111`).
- **Higiene de ramas que verifica, no asume.** Usa `--merged`, `git cherry` y un tree-test con `merge-tree` para squash, y borra con `-d` en vez de `-D` para que la negativa de git sirva de señal (`rules/deploy-workflow.md:58-80`).
- **Estándares de ingeniería como restricción dura, con desviaciones explícitas.** Hay tres puntos de control (architecture, impl, QA-D9). "Not evaluated is not the same as conformant" (`rules/engineering-standards.md:118-120`). Método y datos del equipo quedan separados (`engineering-standards.md:15-28`).
- **Un incidente solo llega a `RESUELTO` con test de regresión** (`rules/incident-tracking.md:56,66`), y su historial de estados es append-only (`incident-tracking.md:59`).
- **Tareas `[human]` con comando, verificación read-only y rollback** (`rules/multi-agent.md:66-82`). Además, el test de IAM verifica el *binding* y no solo su efecto (`skills/karvey-infra/SKILL.md:172-173`).
- **Validación spec↔mockup antes de diseñar**, que es el punto más barato para corregir una spec (`skills/karvey-mockup/SKILL.md:162-175`).
- **Arquitectura con trust boundaries, edge cases obligatorios y plan de cobertura de tests** (`skills/karvey-architecture/SKILL.md:162-243`).
- **Versión leída desde el archivo de versión y no desde una variable de pipeline**, que "se queda pegada en silencio" (`rules/versioning.md:36`).
- **Honestidad sobre el costo de la capa de equipo.** La regla abre con "When NOT to use a team" y datos medidos: US$1.000, 7× por turno a 588k (`rules/team.md:13-41`).

---

## 3. Recomendaciones

### DM-01 — Carriles por tamaño de cambio (lanes), con saltos de fase registrados

- **Problema observado.**
  - El pipeline completo aplica a todo `feature`, y solo existen los tipos `feature | ops | hotfix` (`rules/multi-agent.md:88-89`).
  - Las fases verifican la aprobación de la anterior sin prever saltos:
    - architecture exige `approvals.design_graphic.approved = true` (`skills/karvey-architecture/SKILL.md:28`);
    - si mockup detecta que no hay UI, dice "skip to karvey-architecture" (`skills/karvey-mockup/SKILL.md:52`), y architecture se detiene. Es un callejón sin salida.
  - El carril hotfix (`skills/karvey/SKILL.md:141`: `iterate → impl → test → deploy`) choca con otras precondiciones:
    - impl exige `approvals.tasks.approved = true` (`skills/karvey-impl/SKILL.md:27`);
    - deploy exige un `REVISION_PR_*` de QA (`skills/karvey-deploy/SKILL.md:28-31`);
    - archive exige `tasks.approved` (`skills/karvey-archive/SKILL.md:24`).
  - El dogfooding lo confirma. `docs/spec/changes/team-adapters/spec.json` llegó a `"phase": "deploy"` (línea 14) con `qa.approved: false` (líneas 68-71), y con `prod.ref` = "session approval: 'perfecto, luego commit, push, merge'" (línea 81) en vez de un `D-NN`. Además no tiene `tasks.md` aunque `tasks.approved: true` (líneas 58-62).
  - La instrucción global del usuario obliga a pasar por Karvey incluso un BUG-NN de una línea.
- **Recomendación.** Crea una regla `rules/lanes.md`, referenciada desde el orquestador (`skills/karvey/SKILL.md:113-145`), con una matriz carril × fase que marque cada fase como obligatoria, opcional u omitida:

  | Carril | Fases | Gates humanos |
  |---|---|---|
  | `patch` (≤ ~50 líneas, sin cambio de contrato) | `iterate/init-lite → impl (test-first) → qa-lite → deploy` | 1 (prod) |
  | `standard` (sin UI nueva) | `requirements → architecture+tasks → impl → test → qa → deploy → archive` | — |
  | `feature-ui` | el pipeline completo actual | — |
  | `ops` y `hotfix` | los actuales | — |
  | `method/docs` | el carril docs-only de `multi-agent.md:103-111` | — |

  Además:
  - El carril se decide en `karvey-init` con 3 preguntas objetivas: ¿toca UI?, ¿cambia contratos o esquema?, ¿toca trust boundaries? Se guarda en `spec.json:lane`.
  - Una fase omitida se registra como `approvals.<fase> = { "skipped": true, "reason": "...", "lane": "patch" }`.
  - Cada precondición de fase acepta `approved || skipped`.
  - Se puede **subir de carril** (un `spec-gap` en `patch` que toca contrato sube a `standard`), pero nunca bajar sin un registro.
- **Justificación.** El costo de proceso debe ser proporcional al riesgo. Es el "appetite" de Shape Up, el "vibe vs spec" de Kiro, y el hecho de que Spec Kit deja `/clarify` y `/analyze` como opcionales. DORA muestra que los lotes pequeños con poco overhead correlacionan con menor lead time y menor tasa de fallas. Cuando el método no ofrece un camino barato y legítimo, el equipo toma uno ilegítimo, y eso es justo lo que muestra el propio `team-adapters`.
- **Beneficio.**
  - Menor lead time para fixes chicos. Se mide con `created_at → approvals.prod.date` por carril.
  - Fin de los callejones sin salida para cambios sin UI y hotfixes.
  - Dashboards honestos: "omitido con razón" deja de verse como "pendiente" o "saltado a escondidas".
  - Menos tokens por cambio pequeño.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo:** medio. Se puede abusar del carril `patch`. Mitígalo con criterios objetivos y con que QA-lite verifique que el diff respeta el tamaño del carril.

### DM-02 — Una sola máquina de estados, con esquema JSON y un linter ejecutable

- **Problema observado.**
  - El orquestador enruta por `phase ∈ {init, requirements, mockup, design_graphic, architecture, infra, tasks, impl, test, qa, deployed}` (`skills/karvey/SKILL.md:115-137`).
  - Las skills escriben otros valores:
    - `"requirements-generated"` (`karvey-requirements/SKILL.md:110`), `"mockup-generated"` (`karvey-mockup/SKILL.md:153`), `"design-graphic-approved"` (`karvey-design-graphic/SKILL.md:377`);
    - `"architecture-generated"` / `"architecture-approved"` (`karvey-architecture/SKILL.md:286,299`);
    - `"infra-generated"` / `"infra-approved"` (`karvey-infra/SKILL.md:212,217`);
    - `"tasks-generated"` / `"tasks-approved"` (`karvey-tasks/SKILL.md:117,255`).
  - `karvey-impl` no escribe `phase` en ninguna parte.
  - Los esquemas de `spec.json` no coinciden. `rules/living-specs.md:34-68` no trae `goal` ni `layers`, y trae `qa`/`deploy` solo con `approved`. `karvey-init/SKILL.md:150-188` agrega `goal`, `layers`, `qa.generated` y `deploy.generated`.
  - Hay artefactos fantasma:
    - `proposal.md` se lee en requirements (`:21,41`), mockup (`:48`), design-graphic (`:21,45`) y context (`:32`), pero ninguna fase lo crea; init crea `prd.md` (`karvey-init/SKILL.md:193-234`);
    - `spec-delta.md` está en la raíz del cambio según `living-specs.md:17` y el orquestador (`:230`), pero requirements lo escribe en `changes/{id}/specs/{capability}/spec-delta.md` (`karvey-requirements/SKILL.md:124`).
- **Recomendación.**
  1. Crea `rules/state-machine.md` con el enum único de `phase`, las transiciones válidas (incluidas las hacia atrás de `karvey-iterate`), la precondición de cada una y los artefactos que cada fase debe dejar.
  2. Publica `schemas/spec.schema.json` y `schemas/project.schema.json`.
  3. Crea un script `hooks/karvey-lint.py` que valide el esquema, las transiciones y los artefactos (si `phase ≥ tasks`, `tasks.md` existe y cubre cada ID de `requirements.md`). Ejecútalo en tres lugares:
     - como paso de `phase-close.md` (acción 4);
     - desde el hook de sesión, en modo advertencia;
     - como el "light CI / spec lint" que `multi-agent.md:105` ya promete.
  4. Reemplaza `proposal.md` por `prd.md` en todas partes y fija una sola ruta para `spec-delta.md`.
- **Justificación.** Una máquina de estados que solo existe en prosa y que el LLM interpreta es no determinista. Es la falla nº 3 de tu propio `verification.md:23-24`: "a comment describes the contract the author had in mind, not the one the code honors". Kiro y cc-sdd resuelven esto con `spec.json` validado y `approvals` estructurados. Aquí la estructura existe, pero nadie la verifica.
- **Beneficio.**
  - El orquestador pasa a responder "¿en qué fase estoy?" de forma reproducible.
  - Desaparecen los arranques de fase que se detienen por una precondición mal leída.
  - Cualquier agente o CI puede validar un cambio sin LLM.
  - Se mide con el número de `spec.json` inválidos en `karvey-context`, que debería ser 0.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo:** bajo. Los `spec.json` existentes necesitan migrar; el linter puede traer `--fix` para mapear `*-generated` y `*-approved` al enum.

### DM-03 — Liberar por cambio, no por promoción de la rama de ambiente

- **Problema observado.**
  - El flujo abre el PR `dev → master` titulado `"[Deploy] {change-id}"` (`skills/karvey-deploy/SKILL.md:163-175`), pero ese PR incluye **todo lo que haya en `dev`**, también cambios de otras personas sin QA o con QA en curso.
  - QA revisa el diff `feature/{change-id} → dev` (`skills/karvey-qa/SKILL.md:20-29`), no lo que realmente llega a `master`.
  - El rollback recomendado es "revert the merge" (`karvey-deploy/SKILL.md:241`), que revierte todos los cambios juntos.
  - La integración se hace con merge local más push directo a `dev` (`karvey-deploy/SKILL.md:145-153`), sin PR. El CI del feature no corre antes de integrar.
  - `karvey-context` ya sabe calcular `git log {production}..{integration}` (`skills/karvey-context/SKILL.md:101-106`), pero deploy no lo usa.
  - El propio repo del plugin no usa este flujo: `branch_flow.integration = production = "main"` (`docs/spec/project.json:16-20`), con PRs `feature/* → main` (git log #12-#19). El método no modela trunk-based, que es justo lo que usa su autor.
- **Recomendación.** En `karvey-deploy`:
  1. **Paso 2.8-bis, manifiesto del release.** Calcula `git log origin/{production}..origin/{integration}` y mapea cada commit a su `change-id`, usando un trailer `Karvey-Change: {id}` que `karvey-impl` agrega a cada commit. Bloquea si el release incluye commits de cambios sin `qa.approved` (o `skipped` por carril), o commits sin trailer.
  2. El cuerpo del PR lista **todos** los change-ids y versiones incluidos, no solo uno.
  3. La integración a `dev` pasa por PR (`gh pr create --base dev`), para que el CI y las policies corran antes de integrar.
  4. Soporta `branch_flow.mode: "trunk" | "env-branches"`. En `trunk` (integration == production) el flujo es `feature → PR main` con deploy a dev desde la rama o un pre-release. Documéntalo en `rules/deploy-workflow.md`.
  5. Ofrece `release/*` + cherry-pick como salida cuando `dev` trae cosas no liberables.
- **Justificación.** DORA: tamaño de lote pequeño y trazabilidad del release. Promover una rama de ambiente es el antipatrón clásico de gitflow que "mezcla lo tuyo con lo ajeno". Trunk-based con release por cambio reduce el blast radius y hace el rollback selectivo. La instrucción global del usuario ya exige revisar `git log origin/master..origin/dev` en cada repo, pero el plugin no lo hace.
- **Beneficio.**
  - Ningún commit sin QA llega a prod por arrastre.
  - Rollback por cambio.
  - El título del PR deja de mentir.
  - Baja la Change Failure Rate y el MTTR. Se mide con reverts de prod que arrastraron cambios ajenos.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo:** medio. Exige disciplina de trailers en los commits. Mitígalo con un `commit-msg` hook opcional y con que el linter de DM-02 revise el trailer.

### DM-04 — Versión y CHANGELOG: un único momento de bump y un orden de gates coherente

- **Problema observado.** Hoy el bump ocurre en tres lugares y los gates se piden en orden circular:
  - `karvey-impl` hace bump y CHANGELOG **por tarea**: 1 commit por tarea (`:72`) y bump + entrada (`:75-87`).
  - `karvey-deploy` vuelve a hacer bump en el paso 2.4 (`:133-141`).
  - QA-D6 bloquea si falta la entrada de CHANGELOG de "la versión actual" (`karvey-qa/SKILL.md:91-102`), antes de que deploy haga su bump.
  - El pre-check 3 de deploy exige un CHANGELOG completo (`karvey-deploy/SKILL.md:35-40`) **antes** del paso 2.4 que lo crea.
  - `versioning.md:15` dice "NEVER deploy without incrementing… every time", y `versioning.md:44-48` ubica el bump "before the push to the integration branch".

  Con 10-30 tareas por Epic (`karvey-tasks/SKILL.md:36`), un cambio puede consumir decenas de versiones rev y generar conflictos de CHANGELOG entre ramas paralelas.
- **Recomendación.**
  - Adopta *Keep a Changelog* tal cual. Durante `impl`, cada commit agrega una línea en `## [Unreleased]` (sin bump).
  - El bump ocurre **una sola vez**, en `karvey-deploy` 2.4, y convierte `Unreleased` en `[x.y.z]`.
  - QA-D6 verifica que `Unreleased` cubra el cambio (humano, modelo, por qué). Deja de exigir la "versión actual".
  - El pre-check 3 de deploy pasa a validar `Unreleased`.
  - Quita el bump de `karvey-impl` y reescribe `versioning.md:15` como "cada release incrementa la versión". Aclara que una tarea no es un release.
- **Justificación.** Semver versiona releases, no commits. Los bumps por commit rompen la semántica (un "minor" repartido en 12 "rev") y crean conflictos de merge triviales en archivos calientes (`package.json`, `CHANGELOG.md`), que es desperdicio Lean de retrabajo.
- **Beneficio.**
  - Versiones con significado, una por release.
  - Se acaban los conflictos de CHANGELOG entre features paralelas.
  - QA y deploy dejan de pedirse mutuamente algo que el otro todavía no produjo.
  - Se mide con los bumps por release, que debería ser 1.
- **Esfuerzo** S · **Prioridad** alta · **Riesgo:** bajo.

### DM-05 — Los hooks deben hacer lo que las reglas dicen que hacen, y tener tests

- **Problema observado.** Contrasté cada regla con el script que la implementa:

  | Regla o promesa | Lo que hace el script |
  |---|---|
  | `rules/enforcement.md:17`: git-flow-guard "Blocks git push … to the integration branch when it does not come from a flow merge" | `skills/karvey/hooks/git-flow-guard.sh` solo bloquea push a production (`:33`) y `git commit` en dev/master (`:38`). Push directo a dev: libre. Merge commits en dev: no se bloquean (el flujo de deploy los crea con `git merge`, `karvey-deploy/SKILL.md:147-148`). |
  | `enforcement.md:25`: el marcador de plan-gate se deja pasar "until it is consumed/expires" | `plan-gate.sh:10,24`: `/tmp/claude-plan-approved` sin TTL, sin consumo y sin alcance por cambio. Una aprobación vale para siempre y para cualquier cosa. |
  | plan-gate bloquea comandos destructivos | La regex `>[^>]` (`plan-gate.sh:31`) bloquea comandos inocuos: lo verifiqué, `ls 2>/dev/null` queda bloqueado. `git clean -fdx`, `DELETE FROM` o `mv` sobre archivos no se detectan. |
  | `phase-close.md:41` y `engineering-standards.md:181` prometen hooks `clickup-sync-guard` y `standards-guard` | No existen. `karvey-guard/SKILL.md:21-24` solo gestiona dos hooks más el freeze. |
  | Reglas del flujo vs el propio hook | Chocan: deploy pide commitear `approvals.prod` en "the branch that goes to master" (`karvey-deploy/SKILL.md:206`), o sea `dev`, y archive hace `git commit` sin crear rama (`karvey-archive/SKILL.md:65-68,86-90`). Con git-flow-guard activo, ambos pasos se bloquean. |
  | El hook de sesión detecta el cambio activo | Toma `ls -1dt docs/spec/changes/*/ \| head -1` (`hooks/karvey-session-context.sh:127`), que incluye `archive/`. Lo reproduje: después del primer archive, el hook anuncia "active change: archive". |
- **Recomendación.**
  1. Implementa las reglas prometidas o bórralas del texto: push a integration solo fast-forward desde un merge de PR; marcador con TTL (`find -mmin`), con alcance por `change-id` y consumido al cerrar la fase.
  2. Corrige la regex de redirección (por ejemplo `(^|[^0-9&])>[^>&]`) y agrega `git clean -f`, `DELETE FROM` sin `WHERE`, `terraform destroy` y `az … delete`.
  3. Excluye `archive` en `karvey-session-context.sh:127`.
  4. Mueve `approvals.prod` a un archivo que no requiera commit en dev: el cuerpo o comentario del PR más el `decisions/` del ops repo.
  5. Haz que archive corra en una rama `chore/archive-{id}` con su PR.
  6. Agrega `tests/hooks/*.bats` con fixtures JSON de `tool_input` y córrelos en `.github/workflows/`, que hoy solo tiene `close-external-prs.yml`.
- **Justificación.** El propio método dice que "A skill is guidance … it guarantees nothing" y que solo los hooks bloquean (`enforcement.md:3`). Si la única capa determinista hace menos de lo que declara, el equipo cree tener una garantía que no existe. Además, un gate que bloquea `2>/dev/null` se desactiva por fastidio.
- **Beneficio.**
  - La garantía que se promete pasa a ser real.
  - Menos falsos positivos, así que el hook se mantiene activado.
  - Archive y el registro de prod dejan de chocar con git-flow.
  - Se mide con los tests de hooks en verde y los bloqueos falsos reportados.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo:** bajo. Son scripts opt-in; los tests lo acotan.

### DM-06 — Menos gates humanos y con más peso; eliminar la auto-aprobación silenciosa

- **Problema observado.**
  - Un `feature` pasa por 7 aprobaciones humanas: requirements, mockup, design_graphic, architecture, infra, tasks y prod (`rules/living-specs.md:57-66`). Encima, cada fase termina con "Shall we advance…?", unas 13 interrupciones.
  - Al mismo tiempo hay agujeros:
    - `-y` auto-aprueba requirements, architecture, infra y tasks (`karvey-requirements/SKILL.md:146`, `karvey-architecture/SKILL.md:296`, `karvey-infra/SKILL.md:215`, `karvey-tasks/SKILL.md:126`);
    - design-graphic se aprueba sola: escribe `approvals.design_graphic.approved: true` en su output, antes de preguntar (`karvey-design-graphic/SKILL.md:371,377`).
  - `--autoplan` "groups" los gates 0→5, pero no reduce su número (`skills/karvey/SKILL.md:155`).
- **Recomendación.** Deja tres gates humanos sustantivos por feature:
  1. **Qué**: requirements + mockup, validados juntos (la validación spec↔mockup ya existe).
  2. **Cómo**: una única revisión de plan que agrupe architecture + infra + tasks, con un resumen de 1 página: decisiones, desviaciones, riesgos, costo, tareas `[human]`.
  3. **Prod.**

  Los review-gates internos (checklists de `karvey-architecture/SKILL.md:262-275`, `karvey-tasks/SKILL.md:99-107`) pasan a ser chequeos automáticos del linter (DM-02), no aprobaciones. Además:
  - Elimina `-y` en las fases con gate y déjalo solo en re-runs idempotentes, registrando `role: "auto"` para que el dashboard lo muestre.
  - Corrige design-graphic para que pida la aprobación.
  - Reemplaza el "¿avanzamos?" de cada fase por una sola pregunta en los tres gates, con un modo de ejecución continua entre ellos.
- **Justificación.** Un gate que casi siempre se aprueba entrega poca información y mucha espera: desperdicio Lean de *waiting* y fatiga de aprobación. El mismo método teme convertir al humano en "rubber stamp" (`deploy-workflow.md:13-14`). Spec Kit tiene checkpoints por artefacto, pero sin aprobación formal; Kiro tiene tres documentos (requirements, design, tasks). Tres gates bien preparados valen más que siete de trámite.
- **Beneficio.**
  - Menos interrupciones: de ~13 a 3 por feature.
  - Revisiones humanas más profundas donde importan.
  - Se cierra el agujero de la auto-aprobación.
  - Se mide con la tasa de rechazo por gate (un gate que nunca rechaza es candidato a automatizar) y el tiempo de espera humano por cambio.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo:** medio. Es un cambio cultural para quien valora el paso a paso. Mantén el modo granular como opción (`--granular-gates`).

### DM-07 — Test-first y una matriz de trazabilidad REQ → tarea → commit → test que se pueda verificar

- **Problema observado.**
  - En `impl` los tests se hacen después del código: "Step 5 — Immediate test… Run a verification before marking it as completed" (`karvey-impl/SKILL.md:89-105`).
  - El plan de tests se genera **después** de implementar, en la fase 9 (`karvey-test/SKILL.md:34-89`), aunque architecture ya produjo un "Test coverage plan… the testing contract that `/karvey-test` consumes" (`karvey-architecture/SKILL.md:232-243`). `karvey-test` no menciona consumir esa tabla (`karvey-test/SKILL.md:18-22`).
  - Los IDs de test (`UT-BD-01`, `UT-BE-01`…) no referencian IDs de requisito.
  - `requirements.md` pide un escenario de éxito y otro de error por requisito (`karvey-requirements/SKILL.md:94`), pero nada exige que cada escenario tenga un test automatizado.
  - La evidencia vive en `docs/test_evidence.md` y `docs/test_plan.md`, compartidos entre cambios (`karvey-test/SKILL.md:12,36`).
  - El checklist de QA marca "Tests pass" y "Production build successful" (`karvey-qa/SKILL.md:202-203`), pero QA no los ejecuta.
- **Recomendación.**
  1. `karvey-tasks` genera, para cada requisito `N.M`, una tarea de test **antes** de su tarea de implementación, con el test en rojo esperado.
  2. Convención de nombres obligatoria: `test_REQ_1_2_*` o un tag `@req 1.2`.
  3. `karvey-test` parte del "Test coverage plan" de architecture y produce `changes/{id}/traceability.md`, generado por script: REQ → tarea → commit (trailer) → test → PASS/FAIL.
  4. La evidencia pasa a `changes/{id}/test_evidence.md`.
  5. Gate de QA y archive: cada requisito ADDED/MODIFIED tiene al menos un test automatizado verde, o una excepción `manual` justificada.
  6. QA ejecuta la suite y el build, o cita el run de CI del commit exacto.
- **Justificación.** TDD/XP: el test escrito antes fija el contrato y evita tests que confirman el código ya escrito, que es la falla nº 4 de tu `verification.md:26-27`. EARS rinde lo mejor cuando cada "SHALL" tiene un verificador. Spec Kit y Kiro derivan las tareas con sus tests; aquí la traza se corta entre `requirements` y `test_evidence`.
- **Beneficio.**
  - Menos defectos que escapan: un requisito sin test queda visible antes del merge.
  - Auditoría en 1 archivo por cambio.
  - Se mide con el % de requisitos con test automatizado y con los `spec-gap` detectados en test vs en prod.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo:** bajo-medio. En capas sin runner (SPs, UI legacy) se necesita la excepción `manual`.

### DM-08 — Gate de seguridad con herramientas deterministas, no solo juicio del LLM

- **Problema observado.**
  - La "🚧 SECURITY GATE (blocking)" sobre OWASP Top 10 + STRIDE (`karvey-qa/SKILL.md:36-65`) es un checklist que el modelo lee y juzga.
  - A06 "dependencies with known CVEs" (`:51`) no exige ninguna herramienta de SCA, y no hay escaneo de secretos ni SAST.
  - La revisión de seguridad de infra (`karvey-infra/SKILL.md:141-164`) tampoco pide checkov, tfsec ni trivy.
  - La "second opinion" puede caer a un subagente del mismo modelo (`karvey-second-opinion/SKILL.md:63`), así que la diversidad no está garantizada.
- **Recomendación.**
  - La Dimensión 1 debe **ejecutar** lo que esté disponible y citar su salida:
    - secretos: `gitleaks detect` / `trufflehog`;
    - SAST: `semgrep --config auto`;
    - SCA: `osv-scanner`, `npm audit`, `pip-audit` o `dotnet list package --vulnerable`;
    - IaC: `checkov` o `trivy config`.
  - Si una herramienta no existe, la categoría se registra como **not evaluated**, con la misma regla que la D9 (`engineering-standards.md:119-120`).
  - El LLM tría falsos positivos y cubre lo que las herramientas no ven (IDOR, lógica de tenant).
  - Propón en `karvey-infra` que esas herramientas queden en el pipeline de PR, para que el gate sea del CI y no de la sesión.
- **Justificación.** Un gate "bloqueante" basado solo en lectura del modelo no es reproducible: dos corridas pueden dar veredictos distintos. OWASP SAMM y SLSA piden controles automatizados y repetibles en CI. Tu propio principio: "Where a control exists that measures it, run the control" (`verification.md:19-21`).
- **Beneficio.**
  - Menos vulnerabilidades conocidas en prod.
  - Veredicto de seguridad reproducible y auditable.
  - Se mide con los hallazgos de herramienta por release y con los "not evaluated" en el dashboard.
- **Esfuerzo** S-M · **Prioridad** alta · **Riesgo:** bajo. Puede haber ruido de falsos positivos al principio; permite baseline y supresiones con motivo.

### DM-09 — Living specs: fusionar el spec-delta en el mismo PR del código, no después de prod

- **Problema observado.**
  - El merge de deltas hacia `specs/{capability}/spec.md` ocurre en archive, después de prod, con commits directos y sin rama (`karvey-archive/SKILL.md:42-90`).
  - Si archive no corre, la living spec nunca se actualiza. En el propio repo no existe `docs/spec/specs/` ni `archive/`:
    - `team-layer` quedó en `"phase": "impl"` (`docs/spec/changes/team-layer/spec.json:12`) aunque se publicó en 3.8.0 (`CHANGELOG.md:112-130`), con 4 findings `open` (`team-layer/findings.md:5-8`);
    - `team-adapters` quedó en `deploy`.
  - La fuente de verdad acumulativa, que es el principal valor de SDD a largo plazo, no existe en el único proyecto donde se puede inspeccionar.
- **Recomendación.**
  - Mueve el merge del spec-delta a `karvey-qa` o a `karvey-deploy` antes del PR a producción, dentro de la rama del cambio. Así la living spec y el código llegan juntos a `master`: "spec == lo que está en prod".
  - Archive queda en mover la carpeta, barrer el backlog y cerrar la Epic.
  - `karvey-context` alerta "deployed hace > N días sin archive" y "findings open en cambio desplegado".
  - El linter (DM-02) falla si un cambio en `deployed` no tiene su delta fusionado.
- **Justificación.** Living documentation: la spec se actualiza en la misma unidad atómica que el comportamiento. OpenSpec archiva al final, pero lo hace dentro del mismo flujo de revisión. Separar el merge de spec del merge de código crea deriva y deja un paso final que nadie siente obligatorio.
- **Beneficio.**
  - Living specs confiables para el próximo `requirements`, que las lee para calcular el delta (`karvey-requirements/SKILL.md:116`).
  - Menos `spec-gap` por especificar contra una spec desactualizada.
  - Se mide con los cambios desplegados sin delta fusionado, que debería ser 0.
- **Esfuerzo** S · **Prioridad** media-alta · **Riesgo:** bajo. Si el PR a prod se rechaza, el delta se revierte junto con el código, que es lo correcto.

### DM-10 — Convertir el "canary" en una verificación post-deploy con criterios numéricos y rollback definido

- **Problema observado.**
  - El paso se llama canary, pero no hay división de tráfico. Es el agente mirando: "Repeat the cycle… over a reasonable window post-deploy (several spaced iterations)" (`karvey-deploy/SKILL.md:238`), con "Noticeable degradation = regression" (`:234`).
  - No hay umbrales, ni ventana definida, ni una fuente de métricas de plataforma.
  - El rollback se "recomienda" (`:241`), pero no se define cómo ni quién lo gatilla.
  - La línea base de performance vive en `docs/test_evidence.md` (`karvey-test/SKILL.md:174-183`) y se mide en dev, no en prod.
- **Recomendación.**
  - `karvey-infra` define en `infra.md` un **contrato de verificación post-deploy** por servicio:
    - endpoints de health y rutas críticas;
    - umbrales (error rate ≤ X %, p95 ≤ Y ms respecto al baseline de prod, cero 5xx nuevos);
    - ventana (N sondas cada M s);
    - fuente de métricas (App Insights, CloudWatch, logs);
    - comando de rollback por pipeline (redeploy del tag anterior o swap de slot).
  - `karvey-deploy` ejecuta ese contrato y registra una tabla de sondas en `changes/{id}/deploy_evidence.md`.
  - Renombra el paso a "post-deploy verification". Deja "canary" solo cuando la plataforma haga división de tráfico real (slots, revisiones de Cloud Run, Argo Rollouts), y recomiéndala cuando exista.
- **Justificación.** DORA mide Change Failure Rate y tiempo de restauración. Sin umbrales, "regresión" es una opinión y el MTTR depende de quién esté mirando. Los canaries reales (Google SRE, progressive delivery) comparan métricas contra un baseline con criterios definidos de antemano.
- **Beneficio.**
  - Detección de regresiones reproducible.
  - Rollback en minutos con un comando conocido.
  - Se mide con el MTTR y la CFR por release, calculables desde `deploy_evidence.md`.
- **Esfuerzo** M · **Prioridad** media · **Riesgo:** bajo.

### DM-11 — Métricas del flujo (DORA + rework del método) calculadas desde los propios artefactos

- **Problema observado.**
  - `karvey-retro` mide commits por autor, rachas y tamaño del diff (`karvey-retro/SKILL.md:20-47`). No mide lead time, frecuencia de deploy, CFR, MTTR ni el retrabajo del propio método.
  - Los datos ya existen y nadie los agrega:
    - `created_at` y `approvals.*.date` en `spec.json` (`multi-agent.md:55-59`);
    - `iteration_count` y `revision_history` con el ripple de cada `spec-gap` (`living-specs.md:87-88`);
    - `BUG-NN` con historial de estados (`incident-tracking.md:37-43`).
  - No hay forma de saber qué fases o gates aportan valor y cuáles son pura ceremonia.
- **Recomendación.** Agrega `karvey-retro --metrics` (o una sección en `karvey-context`) que calcule, por carril y por periodo:
  - lead time (`created_at → approvals.prod.date`) y tiempo en cada fase;
  - deploys a prod por semana;
  - CFR (releases con hotfix o BUG-NN detectado en prod dentro de N días);
  - MTTR (`DETECTADO → RESUELTO` de los BUG-NN de prod);
  - tasa de `spec-gap` por cambio y fases rippleadas;
  - **tasa de rechazo por gate**;
  - hallazgos por dimensión de QA.

  Guárdalo append-only, como ya hace `karvey-health` (`karvey-health/SKILL.md:65-72`).
- **Justificación.** Las cuatro métricas de DORA son el estándar para medir capacidad de entrega. Las métricas de retrabajo (spec-gaps, ripples) son la medida directa de si las fases previas están haciendo su trabajo. Tu capa de equipo ya aplica este principio: "A team that cannot say what it spent cannot be judged" (`team.md:40-41`). El método en sí merece lo mismo.
- **Beneficio.**
  - Decisiones basadas en datos sobre qué fases o gates podar (alimenta DM-01 y DM-06).
  - Detección temprana de specs débiles.
  - Se mide con la tendencia de lead time y CFR entre versiones del método.
- **Esfuerzo** M · **Prioridad** media · **Riesgo:** bajo. Métricas mal usadas para juzgar personas; mantén el foco en el flujo, como ya pide `karvey-retro/SKILL.md:62-66`.

### DM-12 — Eliminar las copias de reglas y darle al plugin su propio CI "light"

- **Problema observado.**
  - Hay 9 copias de reglas en `karvey-init/rules/`, `karvey-requirements/rules/`, `karvey-architecture/rules/` y `karvey-tasks/rules/`. Hoy son byte-idénticas (lo verifiqué con `cmp`).
  - El propio CHANGELOG 3.9.1 reconoce que las copias viejas causaron "a silent behavior bug, not just a docs one": estimación en horas y `living-specs.md` sin findings (`CHANGELOG.md:59-71`). La misma versión corrigió conteos equivocados en varios documentos.
  - El método prescribe un "light CI (spec lint)" para PRs docs-only (`multi-agent.md:103-111`), pero el repo solo tiene `.github/workflows/close-external-prs.yml`.
- **Recomendación.**
  - Elimina las copias y referencia `../karvey/rules/*.md` desde cada SKILL. Si el empaquetado del plugin obliga a copiarlas, genéralas en build con un script y verifica en CI que no divergen.
  - Agrega un workflow `lint.yml` que:
    1. compare copias contra la regla canónica;
    2. valide los `spec.json` y `project.json` de `docs/spec/` contra los esquemas de DM-02;
    3. revise enlaces relativos entre skills y reglas;
    4. compare los conteos declarados (32 skills, 13 fases, 18 support) contra `ls skills/`;
    5. corra los bats de hooks (DM-05);
    6. verifique que la versión de `plugin.json` coincida con la de `marketplace.json` y con la primera entrada del CHANGELOG.
- **Justificación.** DRY y "treat the method as code". La deriva documental ya ocurrió y ya costó un bug de comportamiento. Un método que exige CI a sus usuarios y no se lo aplica pierde autoridad.
- **Beneficio.**
  - Cero deriva silenciosa entre reglas.
  - Releases del plugin sin correcciones de conteo.
  - Se mide con las entradas `Fixed — documentation drift` en el CHANGELOG, que deberían tender a 0.
- **Esfuerzo** S · **Prioridad** media · **Riesgo:** bajo.

### DM-13 — Sistema de diseño a nivel de proyecto; design-graphic como delta y opcional

- **Problema observado.**
  - `karvey-design-graphic` redefine **por cambio** la paleta OKLCH, la tipografía, la escala, el spacing, los radios y el motion (`:57-141`).
  - También genera un catálogo exhaustivo de arte por componente, que incluye "push notifications" y un "input … masked RUT/phone" (`:312,322-327`), y exige un scoring ≥ 8 con iteración (`:186`).
  - En un producto brownfield con sistema de diseño existente, cada cambio con UI vuelve a hacer un trabajo que ya está resuelto. Existe la entrada `inputs.design_system` (`:27`), pero es la excepción y no el modo por defecto.
- **Recomendación.**
  - Introduce `docs/spec/design-system.md` (o un `standards/frontend.md` con sección de tokens) como artefacto de **proyecto**, creado una vez.
  - Por cambio, `design-graphic` solo declara tokens o componentes **nuevos o modificados** y el scoring de las pantallas nuevas.
  - El catálogo de arte `design-components.md` es opt-in, solo cuando el cambio pide ilustraciones o assets.
  - En el carril `standard` (DM-01), la fase se omite si no hay componentes nuevos.
  - Saca las referencias locales (RUT) del template y déjalas como ejemplo.
- **Justificación.** Los design systems existen para no rediseñar en cada feature. Es la misma separación que el método ya hizo bien entre living spec (proyecto) y spec-delta (cambio), aplicada al diseño.
- **Beneficio.**
  - Menos tokens y menos tiempo en cambios de UI incremental.
  - Consistencia visual entre cambios.
  - Se mide con el tiempo o costo de la fase design por cambio y con la cantidad de tokens redefinidos por cambio.
- **Esfuerzo** S-M · **Prioridad** media · **Riesgo:** bajo.

### DM-14 — QA: observar sin arreglar, artefactos dentro del cambio, reglas del stack a los estándares

- **Problema observado.**
  - QA contradice al loop de iteración. La Dimensión 8 dice "For visual fixes: apply atomic commits (one fix per commit) documenting before/after" (`karvey-qa/SKILL.md:121`), mientras el mismo skill dice "QA only observes and classifies" (`:268`) y la regla separa a los que escriben del router (`iteration-loop.md:80-85`).
  - Hay reglas del stack de HainTech dentro de un método que se declara agnóstico: "Direct Axios bypassing the apiService interceptors" (`:78`), `v-html` (`:38`), "RUTs" (`:40`).
  - `REVISION_PR_{n}_{date}.md` queda en la raíz del repo (`:139`), y deploy lo busca con `ls -t REVISION_PR_*.md | head -1` (`karvey-deploy/SKILL.md:29`). Con dos cambios en QA a la vez, deploy puede leer la revisión del cambio equivocado.
- **Recomendación.**
  - QA no commitea. Los arreglos visuales van como findings `bug` → micro-loop.
  - El documento pasa a `docs/spec/changes/{id}/qa/REVISION_PR_{n}_{date}.md`, y deploy lo lee desde ahí.
  - Las reglas específicas de un stack (Axios/apiService, `v-html`, RUT) se mueven a `standards/frontend.md` del equipo y se evalúan vía D9. QA-D3 queda con criterios genéricos.
- **Justificación.** Separar a quien revisa de quien implementa (four-eyes) es la base de una revisión independiente. Los artefactos por cambio evitan cruces en trabajo paralelo. Las reglas del stack en el método contradicen la separación método/estándares que el propio plugin estableció (`engineering-standards.md:15-28`).
- **Beneficio.**
  - La revisión mantiene su independencia.
  - Deploy siempre lee la revisión correcta.
  - El método se puede adoptar sin heredar las convenciones de HainTech.
  - Se mide con 0 commits de QA en los diffs y con el hallazgo correcto por cambio en releases paralelos.
- **Esfuerzo** S · **Prioridad** media · **Riesgo:** bajo.

### DM-15 — Bajar el overhead por tarea (knowledge-sync y ritual de tracker) y corregir el registro de tiempos

- **Problema observado.**
  - Knowledge-sync corre "at the end of each phase" (`rules/knowledge-sync.md:16-27`), incluso en **cada iteración de mockup** (`karvey-mockup/SKILL.md:211`), y en multi-repo también sobre el código de cada repo (`knowledge-sync.md:27`).
  - Cada tarea de 10-30 min ejecuta el ritual completo de tracker (`phase-close.md:12-33`, `karvey-impl/SKILL.md:107-133`): comentario, estado, cascada y tiempo.
  - Hay un defecto concreto: impl escribe el **tiempo real sobre `time_estimate`**, "update the actual time via the REST API … `{"time_estimate": {actual_time_ms}}`" (`karvey-impl/SKILL.md:120-124`). Eso destruye la estimación original y hace imposible comparar estimado contra real, que es justo lo que `karvey-retro` y `archive` quieren analizar (`karvey-archive/SKILL.md:131`).
- **Recomendación.**
  - Knowledge-sync solo al cierre de gates humanos y en archive, o de forma asíncrona fuera del turno del modelo (hook post-commit). Nunca en cada iteración de mockup.
  - Para el tracker, en impl haz batch por Feature (un comentario y cascada al cerrar la Feature). El estado por tarea puede ir en `PLAN.md` y sincronizarse al cierre.
  - Registra el tiempo real con la API de time tracking (en ClickUp, las time entries ya iniciadas en `karvey-impl/SKILL.md:51`) y nunca sobre `time_estimate`.
- **Justificación.** Lean: el trabajo que no cambia una decisión es desperdicio. Tu propia memoria de sesión registra que la mayor parte de la cuota se va en contexto y que el costo crece de forma cuadrática (`rules/team.md:23-31` muestra 7× a 588k). Cada llamada de API o graphify por tarea suma contexto. Sobrescribir la estimación es un bug de datos, no una opción de diseño.
- **Beneficio.**
  - Menos tokens y latencia por cambio.
  - Datos de estimado vs real utilizables para calibrar la tabla de `clickup-protocol.md:139-150`.
  - Se mide con los tokens por tarea antes y después, y con el error de estimación por tipo de tarea.
- **Esfuerzo** S · **Prioridad** media · **Riesgo:** bajo. El board del tracker se actualiza con menos frecuencia; es aceptable si el cierre de cada Feature es puntual.

---

## 4. Lo que NO cambiaría

- **Separar a quien observa del que enruta** (`iteration-loop.md:80-85`). Parece burocrático tener `test`, `qa` y `browse` que solo anotan, pero concentrar la lógica del loop en `karvey-iterate` es lo que la mantiene consistente. Es un buen diseño de responsabilidad única.
- **`emergent` nunca se absorbe en silencio y nunca bloquea** (`iteration-loop.md:30,78`). Protege el alcance sin perder la idea. Es el equilibrio correcto entre Shape Up (lo que queda fuera no entra) y el backlog.
- **El gate de prod nunca se delega a un agente** (`multi-agent.md:63`). Con agentes cada vez más autónomos, es el único gate que siempre debe tener una persona responsable.
- **EARS con el litmus "¿se puede escribir sin mencionar tecnología?"** (`rules/ears-format.md:68-70`). Obliga a separar requisito y diseño, que es donde fallan la mayoría de las specs hechas con IA.
- **Estándares fuera del plugin público, con "not evaluated ≠ conformant"** (`engineering-standards.md:15-28,118-120`). La distinción parece sutil, pero evita el falso verde más común en revisiones automatizadas.
- **Estimar en minutos de IA más revisión humana** (`rules/clickup-protocol.md:129-137`). Suena raro frente a la tradición de horas o story points, pero es honesto: el cuello de botella es la revisión humana y las dependencias entre capas. Solo hay que corregir cómo se registra el real (DM-15).
- **Validación spec↔mockup antes de diseño y arquitectura** (`karvey-mockup/SKILL.md:162-175`). La mantendría en el carril `feature-ui` (DM-01). Es el punto más barato del pipeline para descubrir un `spec-gap`.
- **La Iron Law de investigate con la excepción del hotfix en vivo** (`multi-agent.md:99`; `karvey-iterate/SKILL.md:65`). Permitir registrar la causa raíz justo después del fix, sin llegar a `RESUELTO` sin regresión, es un balance maduro entre MTTR y rigor.
- **La capa de equipo opt-in que trae su propia contra-evidencia** (`team.md:7-41`). Que una regla abra diciendo cuándo *no* usarla es raro y correcto; es el tipo de honestidad que hace creíble al resto del método.
- **El handoff "producido, no redactado", con `state.json` contrastado por el hook** (`karvey-checkpoint/SKILL.md:36-39`; `hooks/karvey-session-context.sh:182-222`). Solo corregiría la detección de `archive/` (DM-05). La idea de medir antes de creer es exactamente la correcta para sesiones de agente.
