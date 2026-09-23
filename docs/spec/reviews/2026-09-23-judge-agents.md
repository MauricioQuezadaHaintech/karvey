# Revisión del Método Karvey (v3.11.1) como algo que ejecuta un agente

> Alcance: `.` (solo lectura). Leí `README.md`, `CHANGELOG.md`, los 32 `SKILL.md`, las 22 reglas de `skills/karvey/rules/`, las copias locales de reglas, `hooks/` (scripts, `hooks.json`, README), `skills/karvey/hooks/*.sh` y `plugin.json`. Los tokens son una aproximación (caracteres/4). Probé los hooks con entradas sintéticas y simulé el hook de sesión en el scratchpad.

---

## 1. Veredicto general

Karvey tiene un contenido de método muy bueno. Hay partes difíciles de encontrar en otros plugins: las 18 formas en que falla una verificación (`verification.md`), un handoff que se mide en vez de redactarse, la capa de equipo opt-in con datos de costo reales y un único enrutador de hallazgos. **Como programa que ejecuta un LLM, en cambio, es frágil.** Casi todo el determinismo está escrito en prosa. Solo hay 4 scripts en todo el plugin, y 2 de ellos son opt-in.

El estado del flujo (`spec.json:phase`) no tiene un vocabulario único. Cada skill escribe un valor distinto, y la tabla de ruteo del orquestador no reconoce la mayoría. Hay contradicciones que obligan al agente a romper sus propias reglas duras: tiene que commitear `approvals.prod` en `dev`, versionar dos veces y archivar sobre `dev`. Además hay una fase que se aprueba sola (design-graphic) y otra que no deja pasar a los cambios sin UI.

En costo, una fase carga entre 3k y 27k tokens de instrucciones, porque las reglas se referencian en cadena. Solo las instrucciones de un ciclo completo suman unos 92k tokens antes de leer código, así que el ciclo no cabe bajo el umbral de rotación de 150k que el propio método define. Los hooks cubren bien la identidad de la sesión, pero no cubren la única compuerta que el método declara "nunca delegable", el merge a producción. Mi recomendación es convertir las reglas mecánicas en scripts y hooks, y dejar al LLM solo el juicio.

---

## 2. Mediciones

### 2.1 Tamaño de cada SKILL.md

| Skill | Líneas | Tokens (~) | Descripción en frontmatter (chars) |
|---|---:|---:|---:|
| `karvey` (orquestador) | 321 | 6.383 | 847 |
| `karvey-deploy` | 364 | 6.107 | 678 |
| `karvey-qa` | 339 | 4.406 | 391 |
| `karvey-init` | 387 | 4.320 | 731 |
| `karvey-infra` | 257 | 4.317 | 317 |
| `karvey-design-graphic` | 388 | 4.206 | 372 |
| `karvey-checkpoint` | 274 | 4.156 | 533 |
| `karvey-test` | 366 | 3.773 | 260 |
| `karvey-architecture` | 317 | 3.721 | 301 |
| `karvey-mockup` | 241 | 3.341 | 346 |
| `karvey-iterate` | 131 | 2.613 | 621 |
| `karvey-tasks` | 275 | 2.532 | 280 |
| `karvey-grill` | 203 | 2.529 | 552 |
| `karvey-impl` | 205 | 2.516 | 319 |
| `karvey-archive` | 222 | 2.365 | 234 |
| `karvey-requirements` | 232 | 2.270 | 286 |
| `karvey-health` | 116 | 2.040 | 546 |
| `karvey-context` | 193 | 2.010 | 582 |
| `karvey-investigate` | 76 | 1.969 | 418 |
| `karvey-import` | 110 | 1.764 | 515 |
| `karvey-docs` | 97 | 1.687 | 422 |
| `karvey-standards` | 115 | 1.682 | 478 |
| `karvey-guard` | 91 | 1.653 | 342 |
| `karvey-team` | 99 | 1.602 | 384 |
| `karvey-second-opinion` | 91 | 1.441 | 353 |
| `karvey-devex` | 102 | 1.437 | 313 |
| `karvey-decisions` | 84 | 1.205 | 385 |
| `karvey-diagram` | 55 | 938 | 268 |
| `karvey-browse` | 55 | 928 | 325 |
| `karvey-retro` | 69 | 877 | 353 |
| `karvey-benchmark-models` | 51 | 831 | 404 |
| `karvey-scrape` | 48 | 813 | 335 |
| **Total (32)** | **5.974** | **82.432** | **13.491 (≈3,4k tokens siempre presentes)** |

### 2.2 Tamaño de cada regla (`skills/karvey/rules/`)

| Regla | Líneas | Tokens (~) |
|---|---:|---:|
| `engineering-standards.md` | 214 | 2.871 |
| `team.md` | 149 | 2.170 |
| `multi-agent.md` | 119 | 2.014 |
| `clickup-protocol.md` | 214 | 1.867 |
| `project-config.md` | 92 | 1.691 |
| `living-specs.md` | 139 | 1.662 |
| `deploy-workflow.md` | 95 | 1.541 |
| `verification.md` | 88 | 1.388 |
| `iteration-loop.md` | 85 | 1.229 |
| `support-skills.md` | 37 | 1.211 |
| `management-adapters.md` | 81 | 1.209 |
| `phase-close.md` | 45 | 986 |
| `versioning.md` | 48 | 979 |
| `incident-tracking.md` | 71 | 966 |
| `backlog.md` | 50 | 815 |
| `enforcement.md` | 40 | 787 |
| `notifications.md` | 54 | 749 |
| `changelog-policy.md` | 49 | 628 |
| `targets.md` | 31 | 543 |
| `ears-format.md` | 70 | 516 |
| `security-tiers.md` | 55 | 507 |
| `knowledge-sync.md` | 35 | 505 |
| **Total (22)** | **1.861** | **26.834** |

### 2.3 Copias duplicadas de reglas

Las 9 copias son idénticas byte a byte al canónico (md5 comprobado), así que hoy no hay drift. El riesgo es de proceso.

| Regla | Copias extra en | Tokens duplicados |
|---|---|---:|
| `security-tiers.md` | init, requirements, architecture | 3 × 510 |
| `ears-format.md` | init, requirements | 2 × 518 |
| `living-specs.md` | init, requirements | 2 × 1.711 |
| `clickup-protocol.md` | init, tasks | 2 × 1.892 |
| **Total** | 9 archivos | **≈9,8k tokens / 39 KB** |

El `CHANGELOG.md:63` de la 3.9.1 documenta que estas copias ya envejecieron una vez y lo llama *"a silent behavior bug"*: `init`/`tasks` estimaban en horas con una regla vieja.

### 2.4 Costo de contexto por fase

- **mín** = SKILL.md más las reglas que la skill cita directamente.
- **máx** = lo anterior, más el cierre transitivo de las reglas (cada regla cita otras), más las 3 reglas "de todas las fases" (`phase-close`, `verification`, `knowledge-sync`).

| Fase | SKILL | Reglas directas (n/tokens) | Cierre transitivo (n) | **mín** | **máx** |
|---|---:|---:|---:|---:|---:|
| 0 grill | 2.529 | 1 / 505 | 1 | 3.034 | 5.408 |
| 1 init | 4.320 | 9 / 10.991 | 17 | **15.311** | **26.278** |
| 2 requirements | 2.270 | 6 / 6.413 | 14 | 8.683 | 18.890 |
| 3 mockup | 3.341 | 3 / 2.277 | 12 | 5.618 | 17.819 |
| 4 design-graphic | 4.206 | 3 / 3.062 | 12 | 7.268 | 18.684 |
| 5 architecture | 3.721 | 3 / 3.883 | 16 | 7.604 | 24.017 |
| 6 infra | 4.317 | 8 / 8.638 | 16 | 12.955 | 24.613 |
| 7 tasks | 2.532 | 4 / 5.595 | 11 | 8.127 | 16.467 |
| 8 impl | 2.516 | 6 / 9.249 | 15 | 11.765 | 22.305 |
| 9 test | 3.773 | 7 / 7.452 | 12 | 11.225 | 18.251 |
| 10 qa | 4.406 | 8 / 9.143 | 15 | 13.549 | 24.195 |
| 11 deploy | 6.107 | 9 / 9.859 | 16 | **15.966** | **26.875** |
| 12 archive | 2.365 | 4 / 4.070 | 11 | 6.435 | 16.300 |
| iterate (loop) | 2.613 | 8 / 8.473 | 12 | 11.086 | 17.297 |

- **Grafo de reglas casi completo.** `phase-close.md` cita 7 reglas y `project-config.md` cita 8. Cualquier fase que cierre con el ritual alcanza entre 11 y 17 de las 22 reglas.
- **Ciclo completo en una sesión.** La parte única de instrucciones suma unos 82k tokens: 49k de las 14 skills de fase, 26,8k de reglas y 6,4k del orquestador. A eso se suman unos **10,3k** del `SKILL.md` de graphify (41 KB), que cada fase invoca al cerrar. El total ronda los **92k tokens antes de leer un solo artefacto o archivo de código.** Con el umbral de rotación de 150k (`team.md:80`, `hooks/README.md`), un ciclo feature completo obliga a rotar al menos 1 o 2 veces, y cada rotación vuelve a pagar skill y reglas.
- **Conclusión de diseño.** Karvey funciona de hecho como "una fase por sesión", pero no lo declara ni lo optimiza.

### 2.5 Descripciones y triggers en conflicto

- **Triggers repetidos entre skills** (medido sobre las listas `Triggers include`):
  - `spec-driven`, `SDD`, `kiro`, `gstack`, `Garry Tan` y `PRD` están en `karvey`, `karvey-grill` **y** `karvey-init`.
  - `cc-sdd` está en `karvey` y `karvey-init`.
  - `método de desarrollo` / `development method` están en `karvey` y `karvey-grill`.
  - `relevo` está en `karvey-checkpoint` y `karvey-team`.
  - En total son 10 frases repetidas.
- **Triggers genéricos que chocan con skills fuera del plugin:**
  - `deploy`, `release`, `liberar` (`karvey-deploy`) chocan con la skill `deploy` que el usuario ya tiene instalada.
  - `code review`, `QA` (`karvey-qa`) chocan con la skill incorporada `code-review`.
  - Otros genéricos: `tests`, `testing`, `pruebas` (`karvey-test`), `architecture`, `iterate`, `loop`, `screenshot`, `documentation`.
- **Descripción del orquestador.** Tiene 847 caracteres y 32 triggers, entre ellos `vibe coding`, `SDLC`, `AI-assisted development` y `Garry Tan`.
- **Presupuesto de descripciones ya excedido.** En el listado de skills de **esta misma sesión**, 12 de las 32 skills de Karvey aparecen **sin descripción**: `devex`, `diagram`, `docs`, `grill`, `guard`, `import`, `qa`, `retro`, `scrape`, `second-opinion`, `standards` y `test`. El harness recortó el presupuesto, y con eso esas skills pierden sus triggers.

### 2.6 Qué garantiza un hook o script y qué es solo prosa

| "Regla dura" | ¿Dónde se garantiza? | Resultado medido |
|---|---|---|
| No `git push` directo a `master` | `git-flow-guard.sh` (opt-in) | Bloquea `git push origin master`. **No bloquea** `git push` a secas estando en master. **Falso positivo** con `git push origin master-notes` (rc=2), porque `\b` corta en el guion. |
| No commit en `dev`/`master` | `git-flow-guard.sh` (opt-in) | **Se salta** con `git -C /repo commit` o `cd repo && git commit`, porque revisa la rama del cwd del hook (rc=0). |
| No deploy manual | `git-flow-guard.sh` (opt-in) | Solo 4 patrones fijos. |
| Prod solo con OK humano y `approvals.prod` | **Solo prosa** (`karvey-deploy:203-210`) | `gh pr merge 12 --merge --admin` pasa (rc=0). |
| Bloqueo de push a `integration` "si no viene del flujo" (`enforcement.md:17`) | **No implementado** en el script | — |
| Plan aprobado antes de modificar | `plan-gate.sh` (opt-in) | **Bloquea `ls 2>/dev/null`** (rc=2), porque el regex `>[^>]` calza con cualquier redirección. **Deja pasar** `find . -delete`, `git clean -fdx` y `sed -i` (rc=0). El marcador `/tmp/claude-plan-approved` es global a la máquina, no expira (contradice `enforcement.md:25`, *"until it is consumed/expires"*) y lo crea **el propio agente** (`karvey-guard:53`). |
| `clickup-sync-guard` (`phase-close.md:41`) | **No existe** en el repo | — |
| Edit-lock `--freeze` | **Sin plantilla**: el agente debe escribir el hook a mano (`karvey-guard:61`) | — |
| Estado de sesión y drift | `karvey-session-context.sh` (automático) | Funciona. Tiene un bug con `archive/` (ver AG-09). |
| Contadores `BUG-NN`, `D-NN`, `BL-NN`, `F-NN`, transiciones de `phase`, compuerta de release, merge de spec-delta, score de health, cascada de estados en el tracker | **Solo prosa** | — |

### 2.7 Tareas deterministas que hoy hace el LLM

- **Contadores:**
  - `BUG-NN`: *"continue the incremental counter — read the file first"* (`incident-tracking.md:9`, `karvey-iterate:57`, `karvey-test` Step 4C).
  - `D-NN`: *"Scan the whole `decisions/` directory"* (`karvey-decisions:40`).
- **Parseo de JSON con `grep -o`:** `karvey-context:75-77` usa `grep -o '"deploy"[^}]*}'`.
- **Merge de spec-delta a spec viva con grep/sed** (`karvey-archive:54-56`).
- **Compuerta de release** (`karvey-deploy` Step 0): lee la tabla de severidades de un `REVISION_PR_*.md`, entradas PASS en `test_evidence.md`, los 4 campos del CHANGELOG y la coincidencia entre versión y archivo.
- **Score de health:** promedio ponderado con renormalización, y sin función definida para calcular el sub-score (*"warnings discount little"*, `karvey-health:53`).
- **Contraste WCAG** en design-graphic: se estima "a ojo" dentro de un auto-puntaje de 0 a 10.
- **Captura de `state.json`:** *"written by the save, never by hand"* (`karvey-checkpoint:259`), pero no hay script, así que lo transcribe el LLM.
- **Tracker en impl:** entre 4 y 6 llamadas por tarea (estado, iniciar tracking, detener tracking, comentario, estado, `curl` de tiempo). Con 30 tareas son unas 150 llamadas.

### 2.8 Veces que el agente debe preguntarle al usuario (feature completo)

| Origen | Preguntas |
|---|---|
| Grill: reframe opcional (6 preguntas) + árbol de hasta ~27 preguntas, **una por mensaje** (`karvey-grill:109,187`) | ~20–34 |
| Init: 3 bloques de settings + enforcement + 7 metadatos + ¿avanzamos? | ~8–12 |
| 11 fases × (aprobar + *"Shall we advance…?"*): el bloque "Advance" está en 12 skills | ~22 |
| Deploy: OK de prod (justificado) + `docs_pr.merged_by` + datos que falten | 1–3 |
| **Total estimado** | **≈50–70 interrupciones** por ciclo |

La mitad de las interrupciones de fase son dobles: aprobar y después confirmar que se avanza.

---

## 3. Fortalezas

- **Verificación escrita como síntomas concretos**, no como principios: `verification.md:14-79`. Por ejemplo, "failed vs never ran se distingue por la duración" (`:29-30`) y "un pipe cuyo primer eslabón falla devuelve el hash del string vacío con exit 0" (`:32-34`). Es la mejor defensa que conozco contra el "verde falso" de los agentes.
- **Hook de sesión que mide en vez de creer.** Compara rama, commit y cambios sin commitear de `state.json` contra el repo vivo e imprime `DRIFT` (`hooks/karvey-session-context.sh:88-124`). Fuera de un proyecto Karvey no imprime nada (`:43`). Reconoce explícitamente que "un hook no puede invocar una skill" (`hooks/README.md`).
- **Statusline fuera del turno** (no cuesta tokens) con un umbral de 150k justificado por medición: *"at 588k a turn costs 7×"* (`hooks/karvey-statusline.sh:11`). Además es resiliente a cambios de formato del CLI (`current_usage` entero u objeto, rutas WSL).
- **Capa de equipo honesta y opt-in.** Parte con "cuándo NO usarla" y da datos: ≈US$1.000 en 3 días, 31% de los turnos se llevan el 48% del gasto (`team.md:13-41`). Queda como opción por defecto un solo agente (`karvey-team:12-20`).
- **Un único enrutador de hallazgos.** `test`, `qa` y `browse` solo clasifican, y `karvey-iterate` enruta (`karvey-iterate:16`, `karvey-qa:268`, `karvey-test` Step 5B). Esto evita que varios agentes o fases tomen decisiones contradictorias.
- **Subagentes con salida acotada.** `karvey-requirements:36-37` pide *"Less than 100 lines"*. `karvey-architecture:34-36` usa 2 subagentes en paralelo, y `karvey-qa:34` paraleliza las dimensiones 1–4. Es buena economía de contexto.
- **Compuerta de prod bien razonada en el texto.** Pide no solicitar el OK con la compuerta del PR en rojo (*"turns the approval into a rubber stamp"*, `karvey-deploy:198-201`) y detectar el host git por el remote (`:90-111`).
- **Tareas `[human]`** con ejecutor, comando, verificación de solo lectura y rollback, más el estado `awaiting-human` que bloquea solo a las dependientes (`multi-agent.md:66-82`).
- **Commit por ruta explícita** en working copies compartidas (`team.md:131-139`, `karvey-checkpoint:92-98`). Es un modo de falla real de los sistemas multi-agente.
- **Compuerta de standards calibrada:** una desviación aprobada no es hallazgo, un standard en `draft` no genera Critical o High, y una zona gris es Medium (`karvey-qa:131-134`). Así se evitan falsos bloqueos que queman confianza.
- **`decisions cross` justificado con datos:** 13 de 14 "bloqueos" ya estaban respondidos (`karvey-decisions:18-21`).
- **El handoff se produce, no se compone** (`karvey-checkpoint:36-39`), y tiene un gemelo `state.json` que se puede verificar por máquina.

---

## 4. Recomendaciones

### AG-01 — Una máquina de estados determinista para `spec.json`

**Problema observado.**
- **Vocabulario de `phase` sin fuente única:**
  - La tabla de ruteo del orquestador espera `requirements`, `mockup`, `design_graphic`, `architecture`, `infra`, `tasks`, `impl`, `test`, `qa` y `deployed` (`karvey/SKILL.md:115-137`).
  - Las skills escriben otra cosa: `"requirements-generated"` (`karvey-requirements:110`), `"mockup-generated"` (`karvey-mockup:153`), `"design-graphic-approved"` (`karvey-design-graphic:377`, con guion en vez del `design_graphic` de la tabla), `"architecture-generated"`/`"architecture-approved"` (`karvey-architecture:286,299`), `"infra-generated"`/`"infra-approved"` (`karvey-infra:212,217`) y `"tasks-generated"`/`"tasks-approved"` (`karvey-tasks:117,255`).
  - **Ninguna skill escribe `"impl"`.**
- **Bloqueo en cambios sin UI:** `karvey-mockup:52` dice *"skip to karvey-architecture"*, pero `karvey-architecture:28` exige `design_graphic.approved = true` y si no, *"stop"*. No existe un estado `skipped`.
- **Fase que se aprueba sola:** design-graphic escribe `approved: true` en su propio output sin preguntar (`:371,377`). La fila del orquestador "design_graphic.approved=false → Review the design with the user" nunca se alcanza.
- **Aprobación sin registro:** `-y` autoaprueba (`requirements:146`, `architecture:296`, `tasks:126`, `infra:215`) sin `by`/`role`/`ref`, que `multi-agent.md:55-63` exige.
- **Esquemas que no calzan:** `approvals.deploy.generated: {YYYY-MM-DD}` (`karvey-deploy:303`) es una fecha, mientras el esquema de `living-specs.md:65` usa booleano.

**Recomendación.**
- Agregar `plugins/karvey/scripts/karvey-state.py` con estas órdenes:
  - `next <change-id>`: calcula el siguiente paso con la tabla actual.
  - `advance <change-id> <phase>`: valida que la transición sea legal.
  - `approve <change-id> <gate> --by --role --ref`
  - `skip <gate> --reason`: estado `skipped`, que el paso siguiente acepta.
  - `validate`: aplica un JSON Schema en `schemas/spec.schema.json`.
- Sacar la tabla de `karvey/SKILL.md` y reemplazarla por `python3 …/karvey-state.py next {id}`.
- En cada skill de fase, cambiar las líneas "Update spec.json: phase …" por una sola llamada al script.
- `-y` pasa a registrar `role: "auto"` y queda prohibido para `prod`.

**Justificación.** Un LLM que lee `"requirements-generated"` y busca `requirements` en una tabla tiende a "interpretar" la fila más parecida, y lo hace distinto en cada sesión. Esa lectura aproximada es exactamente el tipo de decisión que no le conviene al método. Una transición validada por código elimina toda la clase de drift. Hoy hay 14 escritores del campo con 12 formatos distintos.

**Beneficio.** Desaparecen el bloqueo backend-only y la compuerta de diseño que se aprueba sola. El orquestador ya no necesita leer unos 700 tokens de tabla. Estimo 80–90% menos errores de ruteo entre sesiones.

**Esfuerzo:** M · **Prioridad:** alta · **Riesgo:** bajo. Los `spec.json` existentes se migran con un `validate --fix` que mapea los valores viejos.

---

### AG-02 — Resolver las contradicciones que obligan al agente a romper sus reglas duras

**Problema observado.**
1. **`approvals.prod` en `dev`.** `karvey-deploy:206` pide registrar `approvals.prod` en `spec.json` *"and commit it on the branch that goes to master"*. Esa rama es `dev`, porque el PR es dev→master (`:167`). La regla dura (`:259`) y el hook (`git-flow-guard.sh:38-43`) prohíben commitear en `dev`. Hacerlo por otra rama feature obliga a mergear a dev de nuevo, lo que dispara el pipeline DEV y cambia el PR ya verificado en 2.9-bis.
2. **Doble versionado.**
   - El orquestador describe impl como *"Version bump + CHANGELOG per commit"* (`karvey/SKILL.md:191`), y `karvey-impl:75-87` sube la versión.
   - `karvey-deploy` 2.4 (`:133-141`) vuelve a subirla antes del push.
   - `versioning.md:15`: *"it is not reused"*.
   - Resultado: dos subidas por ciclo, o una por commit.
3. **Checklist de 6 pasos después del push.** El checklist "antes del push a dev" (Step 3, `karvey-deploy:244-255`) aparece **después** del Step 2, que ya hizo `git push origin {integration}` (`:151-154`).
4. **Archive sobre `dev`.** `karvey-archive:63-91` hace `git commit` dos veces sin indicar rama. Tras el deploy el agente quedó en `dev` (`karvey-deploy:147`), así que archiva commiteando en `dev`.

**Recomendación.**
- (1) Registrar el OK de prod en el `D-NN` del repo de operaciones y en el cuerpo o aprobación del PR. `spec.json:approvals.prod` se escribe en el branch de archive (punto 4).
- (2) La versión sube **solo en deploy** 2.4. impl deja la entrada `Unreleased` del CHANGELOG.
- (3) Mover el checklist antes de 2.5 como `Step 1.9`, y que lo ejecute un script (AG-10).
- (4) Archive parte con `git checkout -b chore/archive-{id}` desde `production` y entra por PR docs-only (`multi-agent.md` §8).

**Justificación.** Cuando dos instrucciones se contradicen, el LLM obedece la más cercana en el contexto o se detiene a preguntar. Las dos salidas son malas: rompe una regla "NUNCA" o genera una interrupción no planificada. Estas cuatro contradicciones se dan en **todos** los ciclos, no son casos borde.

**Beneficio.** Cero violaciones forzadas de la regla de ramas. Se elimina un pipeline DEV extra por ciclo, se acaba la inflación de versiones y se evitan 1 o 2 preguntas imprevistas por deploy.

**Esfuerzo:** S · **Prioridad:** alta · **Riesgo:** bajo.

---

### AG-03 — Que los hooks cubran lo que el método llama "nunca"

**Problema observado.** Todo esto se midió con entradas sintéticas (ver 2.6):
- `gh pr merge 12 --merge --admin` pasa.
- `git -C /x commit` pasa.
- `git push` a secas en master pasa.
- `git push origin master-notes` se bloquea (falso positivo).
- `plan-gate.sh` bloquea `ls 2>/dev/null`, pero deja pasar `find . -delete`, `git clean -fdx` y `sed -i`.
- El marcador del plan es un único `/tmp/claude-plan-approved` para toda la máquina, sin expiración, y lo crea el agente mismo (`karvey-guard:53`).
- `enforcement.md:17` promete bloquear pushes a integration fuera del flujo, y el script no lo hace.
- `phase-close.md:41` cita un `clickup-sync-guard` que no existe.

**Recomendación.**
- **Nuevo hook `prod-gate.sh`** (PreToolUse sobre Bash) para `gh pr merge`, `az repos pr update .* --status completed` y `glab mr merge` apuntando a `production`. Bloquea salvo que `karvey-state.py` confirme `approvals.prod.by` con `role: human` para el change activo. Es la única compuerta que el método declara indelegable (`multi-agent.md:63`).
- **`git-flow-guard.sh`:**
  - Resolver la rama objetivo parseando `-C <dir>` y `cd <dir> &&`.
  - Bloquear `git push` sin refspec cuando `HEAD` es `production`.
  - Usar `(^|[ :])master($|[ ])` en lugar de `\b`.
- **`plan-gate.sh`:**
  - Reemplazar `>[^>]` por `(^|[^0-9&])>[^>&]`, que excluye `2>` y `>&`.
  - Agregar `find .* -delete`, `git clean`, `sed -i` y `truncate`.
  - Marcador por proyecto y sesión (`$CLAUDE_PROJECT_DIR`, hash) con TTL por `mtime`.
  - Que **lo cree un hook `UserPromptSubmit`** cuando el usuario escribe la palabra de aprobación, no el agente.
- **PostToolUse sobre Write/Edit de `**/spec.json`** que corre `karvey-state.py validate` y devuelve el error al agente.
- Borrar la mención a `clickup-sync-guard`, o implementarlo.

**Justificación.** El propio `enforcement.md:3` lo dice bien: *"A skill is guidance… it guarantees nothing"*. Hoy la garantía tiene huecos medidos. Un marcador que el agente puede crear no cambia en nada el cumplimiento, porque el mismo modelo que se salta la regla crea el permiso. Los falsos positivos también empeoran las cosas: en la práctica el usuario terminará desactivando `plan-gate` por cómo bloquea el `2>/dev/null`, que usan casi todos los comandos del propio método.

**Beneficio.** La compuerta de prod pasa de prosa a garantía. Se eliminan los falsos positivos más frecuentes (cualquier `2>/dev/null`) y se cierran 5 evasiones medidas.

**Esfuerzo:** M · **Prioridad:** alta · **Riesgo:** medio. Hay que probar los regex con un test de tabla (ver AG-13).

---

### AG-04 — Presupuesto de contexto por fase y carga progresiva

**Problema observado.**
- Una fase carga entre 3k y 27k tokens (tabla 2.4). El cierre transitivo alcanza entre 11 y 17 de las 22 reglas porque `phase-close.md` cita 7 reglas y `project-config.md` cita 8.
- Hay contenido que no sirve para rutear y se carga igual:
  - El orquestador (6,4k) trae unos 2,9k tokens que no rutean: la lista de features (`:17-43`, 4,3 KB), la descripción por fase (`:159-209`, 4,6 KB), la tabla de equivalencias con Kiro y gstack (`:268-297`) y la autoría (`:310-321`).
  - `karvey-deploy` repite las reglas duras tres veces: en Purpose, en Step 4 (`:257-272`, 2,3 KB) y en Safety (`:344-353`).
  - Los ejemplos de ClickUp están incrustados en `init`, `tasks` e `impl` (11 o 12 menciones cada una) aunque el equipo use Jira.
  - El Step 3.2 de settings de `init` (`:47-103`, 3,1 KB) solo aplica la primera vez.

**Recomendación.**
- Crear `rules/_core.md` (unas 800 palabras) con los contratos duros. Cada SKILL.md de fase declara en su cabecera **una lista cerrada** de lo que carga, del tipo `Load: _core, ears-format`. Las reglas dejan de citarse entre sí con "see X" para cargar, y esas citas pasan a ser notas al pie que no se abren.
- Llevar los adaptadores a `adapters/{clickup,jira,…}.md`, cargados solo según `project.json:management.tool`.
- Partir `karvey-deploy` en un núcleo más `references/{docs-only,hotfix,canary,branch-hygiene}.md`.
- Mover `init --settings` a `references/settings.md`.
- En el orquestador, dejar solo el ruteo (que llama a `karvey-state.py next`) y pasar el resto a `README`/`references/`.
- Declarar explícitamente el patrón **"una fase por sesión"**: `checkpoint save` al cerrar, y el hook de sesión retoma.

**Justificación.** El costo de un turno crece con todo el contexto acumulado. Es el mismo 7× entre 588k y 80k que mide `team.md:23`. Además, las reglas cargadas y no usadas diluyen la atención (*context rot*): una regla de ClickUp presente en un proyecto Jira es ruido que compite con la instrucción que sí importa.

**Beneficio.** El promedio "máx" pasa de unos 20k a unos 9–11k tokens por fase (−45–55%). Las instrucciones únicas de un ciclo bajan de unos 92k a unos 50k, y el ciclo cabe en 1 o 2 sesiones en vez de 2 o 3.

**Esfuerzo:** M · **Prioridad:** alta · **Riesgo:** bajo-medio. Hay que re-probar que ninguna fase pierda una regla que necesita.

---

### AG-05 — Sacar graphify del cierre de cada fase

**Problema observado.**
- `knowledge-sync.md:14` dice *"never go without synchronization"* e invoca `/graphify docs/spec/ --update` al final de **cada** fase (`:25`).
- Esa invocación aparece en 11 skills, y `karvey-mockup` la corre además **en cada iteración del mockup** (`:211`).
- El `SKILL.md` de graphify pesa 41 KB (unos 10,3k tokens), y `--update` hace extracción con LLM.
- graphify no viene con el plugin ni se declara como dependencia. Si no está instalado, la instrucción obligatoria no se puede cumplir, y el agente la omite en silencio o improvisa.

**Recomendación.**
- Agregar `knowledge_sync: "none" | "graphify" | "obsidian"` y usar `"none"` por defecto cuando no se detecte graphify.
- Correr la sincronización **una vez** en `archive`, y a pedido con `/karvey-context --sync`.
- En las fases, dejar solo un paso determinista que agregue las rutas cambiadas a `docs/spec/.graph-pending`. Lo puede hacer un hook PostToolUse sobre Write/Edit en `docs/spec/**`, a costo cero de tokens.
- Detectar la dependencia en `karvey-health` 6a.

**Justificación.** Reconstruir el grafo dentro del turno es de lo más caro del ciclo, y en medio de una fase nadie lo consume: la fase siguiente lee los artefactos directamente. Una instrucción obligatoria que no se puede cumplir es la forma más común de "omisión silenciosa".

**Beneficio.** Entre 10 y 100k+ tokens menos por ciclo (10,3k por carga de la skill, más la extracción por cada una de las ≥11 fases y las iteraciones del mockup). Se acaba una fuente de omisiones silenciosas.

**Esfuerzo:** S · **Prioridad:** alta · **Riesgo:** bajo.

---

### AG-06 — Eliminar las copias de reglas y hacer que las rutas se puedan resolver

**Problema observado.**
- Hay 9 copias de reglas, unos 9,8k tokens duplicados (tabla 2.3). Ya produjeron un bug silencioso (`CHANGELOG.md:63`), y la 3.10.0 tuvo que volver a sincronizarlas a mano (*"Rule copies re-synced byte-identical"*, `CHANGELOG.md:41`).
- Las rutas son inconsistentes:
  - 109 referencias con la forma `karvey/rules/x.md`, que no existen relativas al directorio base de ninguna skill de fase.
  - 37 referencias con la forma `rules/x.md`.
  - `karvey-checkpoint`, `karvey-team` y `karvey-decisions` citan `rules/team.md` y `rules/verification.md` **sin tener carpeta `rules/`**.
  - `karvey-guard:35` copia las plantillas "de `karvey/hooks/`", que tampoco se puede resolver.

**Recomendación.**
- Borrar las copias.
- Referenciar siempre con una ruta relativa al directorio base de la skill (`../karvey/rules/x.md`), o con `${CLAUDE_PLUGIN_ROOT}/skills/karvey/rules/x.md` en los scripts.
- Normalizar las 146 referencias con un `sed` y agregar un chequeo de CI "toda ruta referenciada existe" (AG-13).

**Justificación.** El agente recibe el directorio base de la skill. Una ruta que no se resuelve le cuesta uno o más Glob o Grep por referencia, y con suerte encuentra la copia correcta. Con copias, encuentra la vieja.

**Beneficio.** −9,8k tokens en disco y cero drift por copias. Menos llamadas exploratorias por fase (estimo entre 2 y 5 por skill que carga reglas).

**Esfuerzo:** S · **Prioridad:** alta · **Riesgo:** bajo.

---

### AG-07 — Scripts de asignación de IDs (`BUG-NN`, `D-NN`, `BL-NN`, `F-NN`)

**Problema observado.**
- Todos los contadores funcionan con "lee el archivo y suma 1": `incident-tracking.md:9`, `karvey-iterate:57`, `karvey-test` Step 4C y `karvey-decisions:40`.
- `BUG-NN` es **por repo** (`incident-tracking.md:9`), pero se agrega a un índice global (`:10`). Así, `BUG-12@web` y `BUG-12@app` chocan en `incidents-index.md`.
- Con sesiones paralelas, dos agentes leen el mismo máximo y crean el mismo número. Es una colisión que el entorno del usuario ya registró.
- La ubicación del log de decisiones también está duplicada: `multi-agent.md:24` dice `docs/decisiones.md` (un archivo), y `karvey-decisions` dice `{ops_repo}/decisions/`, un archivo por período.

**Recomendación.**
- Agregar `scripts/karvey-id.py next {BUG|D|C|BL|F} [--repo]`. Toma un lock con `flock` sobre `docs/spec/.ids.lock`, escanea todas las fuentes (incluidas las ramas remotas con `git grep origin/*`) y reserva el número escribiendo una línea placeholder.
- Emitir IDs calificados, `BUG-NN@{repo}`, en el índice global.
- Unificar la ruta del log de decisiones en una sola, dentro de `project-config.md`.

**Justificación.** Contar y reservar es trabajo de máquina. El LLM lo hace bien en una sesión aislada, pero falla justamente en multi-agente, que es donde Karvey dice agregar valor.

**Beneficio.** Colisiones en cero. Unos 1–3k tokens menos por asignación, porque ya no hay que leer el tracker completo.

**Esfuerzo:** S · **Prioridad:** media-alta · **Riesgo:** bajo.

---

### AG-08 — Menos interrupciones: un solo `AskUserQuestion` por compuerta y un grill por lotes

**Problema observado.**
- Se estiman unas 50–70 interrupciones por ciclo (tabla 2.8).
- 12 skills cierran con *"Shall we advance to the X phase now?"* **además** de pedir la aprobación. Por ejemplo, `karvey-requirements:143` más `:226`.
- Grill pide *"One question at a time. Never ask two questions in the same message"* (`karvey-grill:187`), con hasta 27 preguntas más 6 del reframe, y la rama F (stack, preguntas 13–21) se puede inferir casi por completo del repo.
- `allowed-tools` no coincide con lo que las skills hacen, así que las herramientas no listadas no quedan pre-autorizadas y se agregan diálogos de permisos:
  - Faltan `AskUserQuestion` en `karvey-archive` (que decide cada ítem del backlog con el usuario, `:162`) y en `karvey-qa` (que pregunta ramas, `:20`).
  - Falta `Write`/`Edit` en `karvey-browse` y `karvey-health`, que escriben `findings.md` y el historial.
  - Faltan `Write` y `AskUserQuestion` en el orquestador (`Read, Bash, Glob, Grep`) aunque `--autoplan` corre las fases 0→5.

**Recomendación.**
- Un solo `AskUserQuestion` por compuerta, con opciones `[Aprobar y avanzar (recomendado) · Aprobar y parar · Pedir cambios]`.
- Grill por rama: hasta 4 preguntas en un `AskUserQuestion` multi-pregunta, con la recomendación ya puesta como primera opción. La rama F se detecta, se muestra y solo se pide confirmar una vez.
- Alinear `allowed-tools` con un linter (AG-13).

**Justificación.** Cada interrupción es un turno completo con todo el contexto a cuestas, que es caro cuando el contexto es grande. Además corta la ejecución autónoma. Las preguntas dobles no agregan control: la aprobación ya es la compuerta.

**Beneficio.** Entre 11 y 12 turnos menos por ciclo en las fases y entre 10 y 20 menos en grill (−40–50% de interrupciones). Menos diálogos de permisos.

**Esfuerzo:** S · **Prioridad:** media-alta · **Riesgo:** bajo.

---

### AG-09 — Handoff y hook de sesión: corregir bugs, acotar lo que se inyecta y capturar el estado por script

**Problema observado.**
- **Bug con `archive/`, reproducido.** `ACTIVE=$(ls -1dt "$ROOT"/docs/spec/changes/*/ | head -1)` (`karvey-session-context.sh:127`) cuenta `changes/archive/` como un cambio activo, y ahí es donde `karvey-archive:76-77` mueve los cambios cerrados. En la simulación, el hook imprimió *"Run `/karvey-checkpoint restore` BEFORE anything else (active change: archive)"*: después de cualquier archive, cada sesión fuerza un restore inútil.
- **Inyección sin tope.** Con un `board.md` de 400 líneas el hook emite 25 KB (unos 6,3k tokens) en cada startup, resume, compact y clear.
- **Manifest duplicado.** Inyecta **tanto** `manifest-compact.md` **como** `manifest.md` (`:79-80`), contra su propia regla: *"If a compact version exists, that is what a reload reinjects"* (`karvey-checkpoint:49`).
- **`state.json` a mano.** Se declara *"never by hand"* (`karvey-checkpoint:259`), pero lo escribe el LLM, así que la base de la detección de drift es una transcripción.
- **Umbrales de rotación inconsistentes:** 24 h en `team.md:58,80` y `karvey-checkpoint:271`, contra 8 h en `KARVEY_ROTATE_HOURS` (`hooks/README.md:59`).

**Recomendación.**
- Excluir `archive/` y los cambios con `IMPLEMENTED`.
- Inyectar el manifest compacto **o** el completo, nunca ambos.
- Del board, inyectar solo las filas abiertas (`grep -v done | head -40`), y truncar el handoff a unos 6 KB con un aviso "(truncado; lee el archivo)".
- Emitir en JSON `hookSpecificOutput.additionalContext`.
- Agregar `scripts/karvey-handoff-capture.sh`, que escribe `state.json` a partir de los comandos de `karvey-checkpoint` Step 7-bis.
- Unificar el umbral de horas en uno solo.

**Justificación.** Un hook inyecta contexto que el agente paga en cada turno de la sesión, no solo al inicio. Y una medición transcrita por el LLM no es una medición, lo que contradice el principio central del handoff.

**Beneficio.** Se eliminan los restores falsos después de cada archive. La inyección queda acotada (−50–80% en tableros grandes), y la detección de drift pasa a ser 100% por máquina.

**Esfuerzo:** S · **Prioridad:** media-alta · **Riesgo:** bajo.

---

### AG-10 — Compuerta de release, dashboard, merge de specs y score de health como scripts

**Problema observado.**
- `karvey-deploy` Step 0 (`:18-46`) le pide al LLM:
  - revisar la tabla de severidades del `REVISION_PR` más reciente,
  - buscar entradas PASS en `docs/test_evidence.md`,
  - verificar los 4 campos del CHANGELOG por repo,
  - comprobar que el CHANGELOG coincide con el archivo de versión.
- `karvey-context:75-77` parsea JSON anidado con `grep -o '"deploy"[^}]*}'` y declara *"no git"* (`:14`) aunque después usa `git log` (`:104`).
- `karvey-archive:54-56` reemplaza bloques de requisitos "hasta el próximo `### Requirement:`".
- La fórmula de `karvey-health` no se puede reproducir (sub-scores sin función definida, `:53`) y el timestamp va fijo en "Chile time" (`:72`).

**Recomendación.**
- `scripts/karvey-release-gate.py {id}`: JSON `{qa_gate, tests, changelog[], version_match, hotfix_triplet, verdict}`, con exit ≠ 0 si falla. La skill solo lo ejecuta y explica el resultado.
- `scripts/karvey-context.py`: dashboard parseando JSON de verdad.
- `scripts/karvey-spec-merge.py {id}`: aplica ADDED/MODIFIED/REMOVED con un modo `--dry-run` que muestra el diff para aprobar.
- `scripts/karvey-health-score.py`: sub-scores con funciones explícitas (por ejemplo `10·e^(−errores/k)`), usando la zona horaria de `KARVEY_TZ`.

**Justificación.** Esas tareas son parseo y aritmética. En ellas el LLM falla de forma intermitente y **sin avisar**: lee la tabla del REVISION_PR equivocado o redondea un promedio. `verification.md:7` pide *"state what you verified"*, y un script con exit code es la evidencia más barata que existe.

**Beneficio.** La compuerta de release es reproducible y auditable. El score de health se puede comparar entre corridas, que es su razón de ser. Ahorra unos 2–4k tokens por deploy (ya no se leen los CHANGELOG ni el REVISION_PR completos).

**Esfuerzo:** M · **Prioridad:** media · **Riesgo:** bajo.

---

### AG-11 — Frontmatter: descripciones cortas, sin triggers genéricos ni de marca

**Problema observado.**
- Las descripciones suman 13.491 caracteres (unos 3,4k tokens presentes en cada sesión).
- En esta sesión, 12 de las 32 skills de Karvey se listan sin descripción, porque el presupuesto ya está excedido.
- Hay 10 frases de trigger compartidas entre `karvey`, `grill` e `init`, y hay triggers genéricos que compiten con otras skills: `deploy` (existe una skill `deploy` del usuario), `code review`/`QA` (skill incorporada `code-review`), `tests`, `iterate`, `loop` y `screenshot`.
- El orquestador tiene 847 caracteres, con triggers como `vibe coding`, `SDLC` y `Garry Tan`.

**Recomendación.**
- Descripciones de 250 caracteres o menos con la forma "Karvey fase N — qué produce — cuándo usarla". Solo el orquestador conserva `karvey`/`spec-driven`/`SDD`, y se quitan las marcas de terceros de los triggers.
- Prefijar los triggers genéricos con el contexto ("karvey deploy", "desplegar con karvey").
- En las skills de uso solo manual (`guard`, `team`, `benchmark-models`, `scrape`, `import`, `retro`), evaluar `disable-model-invocation: true` para sacarlas del listado.

**Justificación.** La elección de skill depende solo de la descripción. Si esta se trunca o compite, el modelo elige la skill equivocada, por ejemplo la `deploy` del usuario en vez de la de Karvey, o ninguna. Las descripciones largas también le quitan presupuesto a las demás skills del usuario.

**Beneficio.** Unos −2,3k tokens por sesión (de 13,5k a unos 4k caracteres) y una activación correcta de las 32 skills.

**Esfuerzo:** S · **Prioridad:** media · **Riesgo:** bajo. Conviene re-probar las frases en español.

---

### AG-12 — Verificación independiente de los auto-juicios

**Problema observado.**
- **Auto-puntaje de diseño.** design-graphic se puntúa a sí misma de 0 a 10 e itera hasta que el promedio sea ≥8 y ninguna dimensión esté bajo 7 (`karvey-design-graphic:154-186`), sin juez externo. El contraste de color, que es calculable, se juzga ahí mismo.
- **QA sin revisión cruzada.** QA consolida sus propios hallazgos y pone `qa.approved` (`karvey-qa:258`).
- **Second-opinion del mismo modelo.** Si no hay otro CLI, second-opinion recurre a un subagente de la misma familia (`karvey-second-opinion` paso 2).
- **Compuerta que no es compuerta.** `verification.md:84` dice que `karvey-guard --verify` aplica el checklist, pero la propia skill aclara *"This is a checklist, not a gate"* (`karvey-guard:76`).

**Recomendación.**
- El puntaje de diseño lo pone un subagente con **contexto limpio**, que recibe solo `design-spec.md`, el `mockup.html` y la rúbrica.
- Agregar `scripts/contrast-check.py` (OKLCH → sRGB → razón WCAG) como sub-puntaje determinista.
- Antes de `qa.approved`, un subagente "fiscal" recibe el diff y el REVISION_PR y responde solo "¿qué claim no tiene evidencia?".
- Agregar un wrapper `scripts/karvey-evidence.sh -- <cmd>` que guarda comando, exit, duración y hash del output en `evidence.jsonl`. `phase-close` cita líneas de ese archivo en vez de prosa.

**Justificación.** Los LLM sobreestiman su propio trabajo y con eso se conforman con un umbral autoimpuesto. Un juez con contexto limpio no hereda el razonamiento que llevó al error. La evidencia registrada por máquina convierte la regla 17 de `verification.md` ("abre el archivo") en algo que se puede comprobar.

**Beneficio.** Menos falsos "listo" en diseño y QA. Las afirmaciones de cierre quedan respaldadas por evidencia, y un QA posterior las puede auditar sin volver a ejecutar nada.

**Esfuerzo:** M · **Prioridad:** media · **Riesgo:** bajo (unos 3–6k tokens por subagente por fase).

---

### AG-13 — CI del plugin: un linter que detecte el drift antes del release

**Problema observado.**
- El único workflow es `close-external-prs.yml`.
- La 3.9.1 corrigió conteos equivocados en toda la documentación (`CHANGELOG.md:58-62`).
- Hay contratos de artefactos rotos que nada detecta:
  - `proposal.md` lo leen `requirements` (`:21,41`), `mockup` (`:48`), `design-graphic` (`:21`) y `context` (`:32`), pero **`init` nunca lo crea** (crea `prd.md`). `requirements` Step 2 recorre las "áreas funcionales de `proposal.md`".
  - `README.md:147` documenta `/karvey:grill`, cuando la skill es `karvey:karvey-grill`.
  - `karvey-test` repite dos veces el bloque "For each E2E flow step document" (líneas 154-164).

**Recomendación.** Agregar `.github/workflows/lint.yml`, que corre `scripts/lint-plugin.py` con estos chequeos:
- frontmatter válido, con la descripción bajo el límite;
- las rutas `*.md` referenciadas existen;
- no hay copias de reglas;
- los valores de `phase` escritos pertenecen al enum del schema;
- los conteos de README y `plugin.json` coinciden con las skills reales;
- toda herramienta mencionada en el cuerpo (`AskUserQuestion`, `Agent`, `Write`) está en `allowed-tools`;
- todo archivo que una skill lee lo produce alguna fase anterior;
- tests de tabla para los regex de los hooks (los casos de 2.6).

**Justificación.** Este tipo de drift no lo ve un revisor humano ni un LLM leyendo una skill a la vez. Sí lo ve un script que compara el conjunto completo, y el historial del repo muestra que reaparece en cada release.

**Beneficio.** Detecta antes del release todo lo de AG-01, AG-06 y AG-11, y evita que reaparezca. El mantenimiento del método deja de depender de revisiones manuales.

**Esfuerzo:** S-M · **Prioridad:** media · **Riesgo:** bajo.

---

### AG-14 — Portabilidad a otros runtimes y equipos

**Problema observado.**
- **Dependencias propias de Claude Code:** `allowed-tools`, `AskUserQuestion`, `Agent` y el `SessionStart` en `hooks.json`.
- **Rastros de un stack y entorno particulares:**
  - `karvey-qa:38-40,78` revisa `v-html`, "Direct Axios bypassing the apiService" y "RUTs".
  - Los estados de incidente están en español (`DETECTADO`, `RESUELTO`) dentro de un cuerpo en inglés (`incident-tracking.md:40-42`).
  - `karvey-mockup:187` usa `open …`, que es solo de macOS.
  - "Chile time" en `karvey-health:72`.
- **Browse sin delegación:** `karvey-browse` asume un navegador local. No tiene un adaptador `via` (como sí lo tiene `notifications.md`) para delegar en otro agente o máquina con UI, que es justamente el caso de este mismo usuario.
- **Readiness que revisa la copia equivocada:** `karvey-health` 6a busca la versión instalada en `~/.claude/plugins/marketplaces/*`, pero lo que realmente carga el runtime es `~/.claude/plugins/cache/<mkt>/karvey/<ver>/` (según `installed_plugins.json`). El clon del marketplace puede estar más adelante que la versión cargada.

**Recomendación.**
- Mover los ítems específicos de un stack a `standards/` del proyecto.
- Usar estados neutrales con alias localizados.
- Reemplazar `open` por `xdg-open`/`open` detectado, o por "abre la ruta".
- Agregar `project.json:browse.via` (`local` · `agent:<name>` · `none`).
- Leer la versión desde `installed_plugins.json`.
- Documentar un "modo sin harness": un `AGENTS.md` generado que concatena `_core.md` y el SKILL de la fase para Codex, Gemini u otros.

**Justificación.** El método se vende como agnóstico de stack y de herramienta (`plugin.json`). Cada suposición oculta se traduce en un paso que otro equipo no puede ejecutar y que el agente omite o improvisa. Es el mismo patrón que la 3.10.0 corrigió para Google Chat y ClickUp (`CHANGELOG.md:36-42`).

**Beneficio.** Se puede adoptar fuera de HainTech y fuera de Claude Code, y hay menos pasos que se omiten en silencio en otros entornos.

**Esfuerzo:** M · **Prioridad:** baja-media · **Riesgo:** bajo.

---

## 5. Lo que NO cambiaría

- **`verification.md` tal cual.** Está escrito como síntomas observables, y eso es lo que un LLM reconoce en el momento en que ocurren. Convertirlo en principios abstractos le quitaría efecto. Solo lo haría ejecutable por partes (AG-12).
- **Un solo enrutador (`karvey-iterate`).** Concentrar las decisiones de ruteo en un único lugar es lo correcto para agentes: evita que test, qa o browse "arreglen" por su cuenta y que se contradigan.
- **Un solo agente por defecto y la capa de equipo opt-in, con su tabla de costos.** Es la decisión más sensata del plugin y está respaldada por mediciones propias. No la suavizaría.
- **Un hook de sesión que mide y no invoca.** Reconoce el límite real ("un hook no puede invocar una skill") y hace lo que un hook sí hace bien: medir y avisar. Solo le corregiría los bugs (AG-09).
- **La statusline fuera del turno.** Tiene costo cero de tokens y umbrales justificados, así que es el lugar correcto para las alarmas de rotación.
- **El OK humano de prod indelegable, y no pedirlo con la compuerta en rojo.** El criterio es correcto. Lo único que falta es aplicarlo por hook (AG-03).
- **Tareas `[human]` con verificación de solo lectura y rollback, y `awaiting-human` que bloquea solo a las dependientes.** Es el contrato justo entre agente y humano.
- **El trazado PRD → EARS y la validación spec↔mockup temprana.** Sirven para encontrar huecos del spec en la fase más barata.
- **Los estados lógicos del tracker mapeados por adaptador.** Es un buen desacople. Solo movería los ejemplos de ClickUp fuera del camino caliente (AG-04).
- **La prohibición explícita de leer destinos desde `CLAUDE.md`** (`karvey-qa:285`). Evita un acoplamiento oculto y la fuga de configuración entre proyectos.
