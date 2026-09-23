# Revisión del Método Karvey 3.11.1 desde la gestión de proyectos

> Lente: planificación, estimación, seguimiento, visibilidad para stakeholders, backlog, riesgos, decisiones, gobierno, costo y métricas.
> Revisión de solo lectura sobre `.`. Las rutas son relativas a ese repo. `rules/` = `plugins/karvey/skills/karvey/rules/`, `skills/` = `plugins/karvey/skills/`.

---

## 1. Veredicto general

Karvey está muy por sobre el promedio en **trazabilidad y control de calidad**: gates explícitos, aprobación de prod que nunca se delega, un loop de iteración que no deja findings botados, incidentes con historial de estados y un registro de decisiones con `cross`. En **gestión del trabajo** está bastante más débil. Casi todos los artefactos existen, pero nadie los agrega y nadie los mide. El estado de fase usa vocabularios que no calzan entre sí y en su propio repo quedó desactualizado. El tiempo real que se registra pisa la estimación, así que nunca vas a saber si las estimaciones en minutos sirven. El PR `dev → master` saca a prod más cambios de los que se aprobaron. Y el dashboard (`karvey-context`) no muestra backlog, findings, incidentes, tareas `awaiting-human` ni antigüedad. Tampoco hay métricas de flujo o DORA, costo por cambio (fuera de la capa de equipo), reporte para el cliente ni vista de portafolio, que es justo lo que necesita una consultora con muchos tenants. Casi todo esto se arregla con poco esfuerzo, porque los datos ya están en `spec.json`, `CHANGELOG.md`, `bugs_dev_testing.md` y `findings.md`: hoy nadie los lee de forma agregada.

---

## 2. Fortalezas

- **La aprobación de prod queda en el repo, dice quién aprobó y nunca se delega a un agente.** Ver `rules/multi-agent.md:63-64` y `skills/karvey-deploy/SKILL.md:206`. Queda registro de gobierno aunque la plataforma no pueda exigir reviewers.
- **No se pide el OK de prod sobre un gate rojo.** Ver `rules/deploy-workflow.md:11-15` y `skills/karvey-deploy/SKILL.md:198-201`. Así el humano no queda de timbre.
- **Loop de iteración con tres salidas y una regla de convergencia.** Ver `rules/iteration-loop.md:26-30` y `:73-78`. Separa defecto (`bug`), error de alcance (`spec-gap`) y alcance nuevo (`emergent`). Es control de alcance de verdad: *"Never silently absorbed into the current change"* (`:30`).
- **El ripple set evita rehacer todo el pipeline por un cambio de spec.** Ver `skills/karvey-iterate/SKILL.md:72-76`. Es gestión de cambios proporcional.
- **Incidentes con historial de estados que no se sobrescribe.** Ver `rules/incident-tracking.md:45-59`. Un incidente solo llega a RESUELTO con test de regresión (`:66`). Con esto ya se puede medir MTTR y reapertura (ver PM-05).
- **Registro de decisiones con el campo "What it does NOT say" y `cross` obligatorio antes de declarar un bloqueo.** Ver `skills/karvey-decisions/SKILL.md:41-47` y `:54-66`. Viene de un caso medido: 13 de 14 "bloqueos" ya estaban respondidos (`:19-21`).
- **Los estados lógicos independizan el método del tracker.** Ver `rules/management-adapters.md:30-41`. Un fallo del tracker se reporta y no se esconde (`:80`, `rules/phase-close.md:37`).
- **Las tareas `[human]` traen ejecutor, comando, verificación y rollback, y el estado `awaiting-human` bloquea solo a sus dependientes.** Ver `rules/multi-agent.md:66-82`. Resuelve bien un problema clásico de coordinación.
- **La capa de equipo parte con un análisis de costo medido y recomienda no usarla.** Ver `rules/team.md:13-41`: US$1.000, 3 días, 7× de costo por turno.
- **Reglas de verificación antes de reportar "done".** Ver `rules/verification.md:7-10`. Sirven directo contra los estados que mienten.
- **Branch hygiene con conteo explícito, sin limpiar a escondidas.** Ver `rules/deploy-workflow.md:49-80`. El trabajo que no se ha liberado nunca se borra.

---

## 3. Recomendaciones

### PM-01 · Una sola máquina de estados de fase, con un validador que detecte cuando miente

- **Problema observado.**
  - El orquestador decide el siguiente paso con los valores `init`, `requirements`, `mockup`, `design_graphic`, `architecture`, `infra`, `tasks`, `impl`, `test`, `qa` y `deployed` (`skills/karvey/SKILL.md:115-137`).
  - Las skills escriben otros valores: `requirements-generated` (`skills/karvey-requirements/SKILL.md:110`), `tasks-generated` / `tasks-approved` (`skills/karvey-tasks/SKILL.md:116`, `:254`), `architecture-approved`, `infra-approved`, `mockup-generated` y `design-graphic-approved`.
  - Ninguna skill escribe `phase: "impl"`: `karvey-impl` no toca `phase`.
  - El esquema no define un enum de fases (`rules/living-specs.md:43`).
  - En el propio repo del método (dogfooding):
    - `team-layer` sigue en `"phase": "impl"` con `tasks.approved=false` (`docs/spec/changes/team-layer/spec.json:12`, `:26`), pero salió publicado en 3.8.0 (`CHANGELOG.md:112-118`).
    - `team-adapters` está en `"phase": "deploy"`, un valor que no existe en el orquestador, con `qa.approved=false` y aun así con `prod` aprobado (`docs/spec/changes/team-adapters/spec.json:14`, `:68-82`). Tampoco tiene `tasks.md` ni `PLAN.md`, aunque declara `management: markdown` y `tasks.approved=true`.
    - `team-layer/findings.md:5-8` tiene un `spec-gap` y tres `emergent` en `open` que nunca pasaron a `docs/spec/backlog.md`. O sea, se desplegó sin convergencia.
- **Recomendación.**
  1. Definir en `rules/living-specs.md` un enum cerrado de `phase` (por ejemplo `init | requirements | mockup | design_graphic | architecture | infra | tasks | impl | test | qa | deploying | deployed | archived`). El estado "generado / aprobado" vive **solo** en `approvals.*`, no en el nombre de la fase.
  2. Corregir las 8 skills que escriben variantes y hacer que `karvey-impl` escriba `phase: "impl"` al empezar.
  3. Agregar `karvey-health --method` (o un paso de `karvey-context`) que valide la consistencia: fase contra aprobaciones, fase contra versión publicada en el CHANGELOG, `deployed` con findings `open`, y artefactos obligatorios según la fase (`tasks.md` si `tasks.approved`).
  4. Conectarlo al "spec lint" que ya se propone para los PR de solo documentación (`rules/multi-agent.md:105`).
- **Justificación.** Un tablero sirve si su estado es verdadero. Si el mismo autor del método no logra mantenerlo al día a mano, un equipo con 10 clientes tampoco va a poder. Esto es lo mismo que plantea `rules/verification.md:7` (*"state what you verified, not what you expect"*), aplicado al estado de los cambios.
- **Beneficio.** El orquestador deja de recomendar pasos equivocados, el dashboard pasa a ser confiable para el PM y el cliente, y el trabajo ya publicado deja de aparecer como "en impl". Se mide así: el validador reporta 0 inconsistencias en los repos activos, y el porcentaje de cambios con estado inconsistente baja semana a semana.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** bajo. Solo toca vocabulario y un chequeo de lectura. Los `spec.json` antiguos se migran con un mapeo simple.

### PM-02 · No pisar la estimación con el tiempo real; guardar ambos números y medir la precisión

- **Problema observado.** Al cerrar cada tarea, `karvey-impl` registra el tiempo real sobrescribiendo el campo de la estimación: *"ClickUp: update the actual time via the REST API … `-d '{"time_estimate": {actual_time_ms}}'`"* (`skills/karvey-impl/SKILL.md:120-125`). Con eso se pierde la estimación original. Todo el modelo de estimación en minutos (`rules/clickup-protocol.md:129-154`, *"An AI develops a whole 30-SP API in ~15 min"*) no tiene cómo calibrarse. En `PLAN.md` sí hay columnas "Estimate | Actual" (`skills/karvey-tasks/SKILL.md:245-250`), pero ningún proceso compara las dos.
- **Recomendación.**
  1. En `karvey-impl` Step 6, registrar el tiempo real con el mecanismo propio de la herramienta (ClickUp: `time tracking` / `time_spent`, nunca `time_estimate`; Jira: worklog) y dejar la estimación intacta.
  2. Guardar en `tasks.md` / `spec.json` los campos `estimate_min`, `actual_ai_min` y `actual_review_min`. La tabla de `clickup-protocol.md:139-150` ya separa "AI dev" de "Human review": hay que medir los dos.
  3. En `karvey-archive` (o en `karvey-retro`, PM-12), calcular la precisión de la estimación por tipo de trabajo (mediana de real/estimado por fila de la tabla) y proponer ajustar la tabla cuando se desvíe más de ±30% en N cambios.
- **Justificación.** Una estimación que no se compara con el resultado es una opinión. La tabla de minutos es una hipótesis fuerte: dice que el cuello de botella es la revisión humana (`clickup-protocol.md:132-133`). Hay que medirla para confirmarla o corregirla. Hoy el propio código del método borra la evidencia.
- **Beneficio.** Mejores estimaciones con el tiempo, cotizaciones más defendibles ante el cliente y detección de qué tipo de trabajo se subestima de forma sistemática. Se mide con el error de estimación por tipo de trabajo y su tendencia.
- **Esfuerzo** S · **Prioridad** alta · **Riesgo** bajo. Es un cambio en un paso. Hay que revisar la API de cada tracker para el campo de tiempo registrado.

### PM-03 · Que `deployed` signifique "en producción", no "PR abierto"

- **Problema observado.** `karvey-deploy` Step 6 fija `phase: "deployed"` sin condición (`skills/karvey-deploy/SKILL.md:300-305`), aunque el resultado final contempla *"PROD ⏳ PR open, awaiting human OK"* (`:326`) y `approvals.deploy.approved` pueda quedar `null` (`:304`). `karvey-archive` acepta `phase = "deployed"` **o** `approvals.deploy.approved` (`skills/karvey-archive/SKILL.md:23`) y crea el marcador `IMPLEMENTED` (`:31`). Resultado: un cambio que no llegó a prod se puede archivar como implementado y su Epic cerrarse en `done`.
- **Recomendación.** Separar dos estados:
  - `deploying`: está en dev y el PR a prod está abierto.
  - `deployed`: el merge a producción está hecho, el pipeline de PROD está en verde y el canary está OK.
  `deployed` se escribe solo después del paso 2.11. `karvey-archive` debe exigir `deployed` **y** `approvals.prod.by` no vacío. En `karvey-context`, "IN DEV" se calcula desde `deploying` (hoy se infiere con heurística, `skills/karvey-context/SKILL.md:83-86`).
- **Justificación.** La distinción entre "desplegado" y "liberado" es lo que le importa al cliente, y el método ya la exige en el canary y en la versión visible (`rules/versioning.md:26-40`). El estado del cambio debe decir lo mismo.
- **Beneficio.** Se acaban los cierres de Epic en falso y la cola de despliegue queda exacta: qué está esperando el OK humano y desde cuándo. Se mide con 0 cambios archivados con `approvals.prod` vacío.
- **Esfuerzo** S · **Prioridad** alta · **Riesgo** bajo.

### PM-04 · Manifiesto de release: el PR `dev → master` saca todo lo que está en dev, no solo este cambio

- **Problema observado.** El flujo abre un PR de la **rama de integración completa** hacia producción (`rules/deploy-workflow.md:32`; `skills/karvey-deploy/SKILL.md:163-175`), con el cuerpo *"Deploy of {change-id}. QA OK, tests PASS…"* (`:169`). Pero `approvals.prod`, `qa.approved` y el release gate del Step 0 se validan **por cambio** (`:26-46`). Si hay varios cambios en `dev` (lo normal con varios clientes o features en paralelo), el merge saca a prod código de otros cambios que no pasaron el gate y que nadie aprobó. `karvey-context` cuenta los commits pendientes (`skills/karvey-context/SKILL.md:104-106`), pero no los vincula a ningún change-id.
- **Recomendación.**
  1. Antes del paso 2.9, generar un **manifiesto de release**: `git log {production}..{integration}` mapeado a change-ids (por la rama de origen o por el `(change-id)` que exige el CHANGELOG, `rules/changelog-policy.md:20`).
  2. Exigir que **cada** change-id del manifiesto tenga `qa.approved` y convergencia. Si alguno no cumple, detenerse y ofrecer opciones: esperar, hacer cherry-pick a una rama `release/*` (ya soportada en `branch_flow.protected_branches`) o sacarlo de dev.
  3. Poner el manifiesto en el cuerpo del PR y registrar `approvals.prod` en **todos** los cambios incluidos.
  4. El mismo manifiesto sirve de notas de release para el cliente (PM-07).
- **Justificación.** La aprobación tiene que cubrir exactamente lo que se libera. Hoy la unidad aprobada (el cambio) no es la unidad liberada (la rama). Es una brecha de gobierno y de cumplimiento, peor en multi-tenant, donde el cambio de un cliente puede arrastrar el de otro.
- **Beneficio.** Cada release queda auditable (qué entró, quién lo aprobó y por qué), no se cuela alcance sin revisar y las notas de release salen solas. Se mide con el porcentaje de releases cuyo manifiesto calza con los `approvals.prod` registrados (meta: 100%).
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** medio: puede frenar releases en equipos acostumbrados a promover dev completo. Conviene un modo "advertir" antes de "bloquear".

### PM-05 · Métricas de flujo y DORA calculadas con los datos que ya existen

- **Problema observado.**
  - El método no define ninguna métrica de entrega. `approvals.*` guarda solo la fecha, sin hora (`rules/multi-agent.md:57`), y no hay historial de transiciones de fase: `spec.json` tiene solo `created_at` / `updated_at` (`skills/karvey-init/SKILL.md:157-158`).
  - Aun así, los datos casi están:
    - `iteration_count` se declara *"useful for the retro"* (`rules/living-specs.md:87`), pero ninguna skill lo agrega.
    - El historial de BUG-NN tiene fecha y hora por estado (`rules/incident-tracking.md:37-42`).
    - Los hotfix registran `bug` y `release` (`rules/multi-agent.md:100`).
    - El canary registra OK o REGRESSION (`skills/karvey-deploy/SKILL.md:242`), pero no se persiste en ningún lado que se pueda agregar.
- **Recomendación.**
  1. Agregar `spec.json:phase_history: [{phase, entered_at, exited_at}]`, escrito por el ritual de cierre (`rules/phase-close.md:30-33`), y guardar hora (ISO 8601) en `approvals.*.date`. Con esto se obtiene lo que realmente cuesta: el **tiempo esperando la aprobación humana** (desde `generated_at` hasta `approved_at`).
  2. Persistir el resultado del canary y el rollback en `spec.json:deploys: [{env, version, date, canary, rollback}]`.
  3. Nuevo modo `karvey-context --metrics` (solo lectura) que calcule por proyecto y período:
     - **Lead time del cambio**: desde `created_at` hasta `approvals.prod.date`.
     - **Cycle time por fase** y **tiempo de espera de aprobación**.
     - **Throughput**: cambios archivados por semana.
     - **Frecuencia de despliegue**: versiones en el CHANGELOG.
     - **Change failure rate**: releases con hotfix, REABIERTO o canary REGRESSION sobre el total.
     - **MTTR**: desde DETECTADO hasta RESUELTO en `bugs_dev_testing.md`.
     - **Tasa de retrabajo**: `iteration_count`, `spec-gap` por cambio y REABIERTO.
     - **Precisión de estimación** (PM-02).
- **Justificación.** DORA (deployment frequency, lead time, change failure rate, MTTR) y las métricas de flujo de Kanban (cycle time, throughput) son el estándar para evaluar entrega. Karvey afirma que el cuello de botella es la revisión humana (`rules/clickup-protocol.md:132-133`). Sin medir el tiempo de espera de aprobación, esa afirmación no se puede comprobar ni mejorar.
- **Beneficio.** El PM puede pronosticar fechas con datos (throughput histórico en vez de minutos de IA sumados), ver dónde se acumula el trabajo (normalmente en los gates humanos) y mostrarle al cliente la tendencia de calidad. Se nota en la primera retro: aparecen los números.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** bajo: es de solo lectura, y `phase_history` es aditivo.

### PM-06 · `karvey-context`: completar el dashboard y agregar antigüedad y límites de WIP

- **Problema observado.**
  - `rules/backlog.md:44` promete que *"the dashboard surfaces the count of `open` backlog items"* y el README dice que el dashboard muestra *"backlog, live branches"* (`README.md:69`). Pero el formato de salida de `karvey-context` **no tiene** secciones de backlog, findings, incidentes ni tareas `awaiting-human` (`skills/karvey-context/SKILL.md:110-173`; buscar "backlog", "findings" o "BUG-" en el archivo no encuentra nada).
  - La línea de aprobaciones termina en `tasks` y no muestra qa, deploy ni prod (`:138`).
  - El modo `--change` lee `proposal.md` (`:32`), un archivo que el método no genera (el PRD es `prd.md`, `skills/karvey-init/SKILL.md:193-195`).
  - No hay ninguna noción de antigüedad (días desde `updated_at`) ni de límite de WIP. En el propio repo quedan dos cambios abiertos que ya se publicaron (PM-01), y nada lo avisa.
- **Recomendación.**
  1. Agregar a la salida:
     - `OPEN WORK`: findings `open` por tipo, BUG-NN no resueltos (de `incidents-index.md`), `[human]` en `awaiting-human` con su ejecutor y desde cuándo, y conteo del backlog `open`.
     - Una columna de **antigüedad** por cambio: días en la fase actual, marcando "estancado" si supera N días.
  2. Mostrar todas las aprobaciones, incluidas qa, deploy y prod con quién aprobó.
  3. Reemplazar `proposal.md` por `prd.md`.
  4. Agregar `project.json:wip_limit` (por ejemplo, cambios activos máximos por repo o por persona) y que `karvey-init` advierta al superarlo.
- **Justificación.** La limitación de WIP y la visibilidad del trabajo envejecido son la base de Kanban: sin ellas los cambios quedan "casi listos" indefinidamente. El trabajo que no aparece en el tablero, como un `awaiting-human` que el ejecutor no sabe que le toca, es trabajo invisible.
- **Beneficio.** El PM ve en un solo lugar qué está bloqueado, qué se envejeció y qué espera a una persona, y el humano ve su propia cola. Se nota en menos cambios abiertos sin movimiento. Se mide con la antigüedad promedio del WIP.
- **Esfuerzo** S · **Prioridad** alta · **Riesgo** bajo.

### PM-07 · Visibilidad para el cliente y los stakeholders: reporte periódico y eventos de "te toca a ti"

- **Problema observado.** Las notificaciones cubren solo `qa`, `deploy` e `incident` (opcional), todas dirigidas al canal del equipo (`rules/notifications.md:14`, `:30-34`). No hay:
  - aviso cuando una aprobación queda pendiente (cada fase pregunta *"Shall we advance…?"* solo en la sesión, p. ej. `skills/karvey-init/SKILL.md:381`);
  - aviso cuando una tarea `[human]` queda en `awaiting-human` (`rules/multi-agent.md:80`), que solo va como comentario en el tracker;
  - aviso cuando algo queda `blocked` (`skills/karvey-impl/SKILL.md:183-194`);
  - un reporte de estado dirigido a stakeholders o clientes. El PRD tiene una sección "Stakeholders" (`skills/karvey-init/SKILL.md:225-226`) que ninguna fase usa después.
- **Recomendación.**
  1. Agregar a `notifications.events` los eventos `approval_requested`, `awaiting_human` (dirigido al ejecutor declarado) y `blocked`.
  2. Nuevo modo `karvey-context --report [--since 7d] [--client <tag>]` que genere un **resumen de estado** en lenguaje de negocio, usando `project.json:notifications` o un destino `stakeholders`: qué se liberó (manifiesto de PM-04), qué está en curso con ETA según throughput, qué está bloqueado y quién lo desbloquea, riesgos abiertos (PM-11) y decisiones que espera del cliente.
  3. Usar la sección Stakeholders del PRD como destinatarios por defecto de ese reporte.
- **Justificación.** En una consultora, el cliente no lee `spec.json` ni el canal interno. La comunicación con stakeholders (PMBOK, gestión de interesados) necesita un informe periódico y una cola visible de lo que se espera de cada uno. Hoy lo que espera al humano vive en la conversación con el agente y se pierde al rotar la sesión.
- **Beneficio.** Menos tiempo detenido esperando aprobaciones (el aviso llega a quien debe actuar), informes al cliente que no se arman a mano y menos "¿en qué va lo mío?". Se mide con el tiempo de espera de aprobación (PM-05) antes y después.
- **Esfuerzo** M · **Prioridad** alta · **Riesgo** bajo. Cuidar de no enviar datos internos o de otros tenants en el reporte al cliente.

### PM-08 · Costo por cambio (tokens y US$) también con un solo agente, asociado al cliente

- **Problema observado.** El costo se mide solo en la capa de equipo (`skills/karvey-team/SKILL.md:161-173`, `rules/team.md:40`: *"A team that cannot say what it spent cannot be judged"*). En el caso por defecto, un agente solo, no se registra costo por cambio. El statusline ya recibe el costo de la sesión (`plugins/karvey/hooks/karvey-statusline.sh:5`), pero no queda en ningún artefacto. La etiqueta del cliente existe (`spec.json:clickup.client_tag`, `rules/living-specs.md:55`), pero nada suma esfuerzo o costo por cliente.
- **Recomendación.**
  1. En el ritual de cierre (`rules/phase-close.md` §4), sumar a `spec.json:effort` los valores `{ai_usd, tokens, human_review_min}` del intervalo (desde el costo de sesión del statusline o del transcript, marcándolo como estimado cuando no sea exacto).
  2. `karvey-context --metrics` agrega por `client_tag` y período.
  3. Mover la sentencia de la regla de equipo ("si no paga, dilo con el número") al caso general: un cambio cuyo costo supere X veces la mediana se señala en la retro.
- **Justificación.** La misma regla que el autor aplicó a la capa de equipo vale para cualquier trabajo facturable. En una consultora el margen por cliente depende de conocer el costo por entrega, y con IA el costo marginal ya no es solo horas-persona.
- **Beneficio.** Rentabilidad por cliente visible, cotizaciones basadas en costo histórico real y detección temprana de cambios que se disparan (retrabajo o contexto inflado). Se mide con US$ por cambio y por cliente al mes.
- **Esfuerzo** M · **Prioridad** media · **Riesgo** medio: depende de lo que exponga el runtime, igual que el `spec-gap` F-03 abierto (`docs/spec/changes/team-layer/findings.md:7`). Hay que declarar el costo como estimado cuando lo sea.

### PM-09 · Ajustar el costo de los rituales al tamaño del trabajo

- **Problema observado.**
  - El ritual de cierre corre al final de **cada tarea de impl** (`rules/phase-close.md:10`) e incluye comentario, estado, cascada, barrido y sincronización de conocimiento (`:30-33`). La sincronización exige graphify cada vez que se toca `docs/spec/` (`rules/knowledge-sync.md:18-27`).
  - Con tareas de 10 a 30 minutos (`rules/clickup-protocol.md:135`), un cambio de 30 tareas genera unas 30 llamadas de comentario, 60 de estado o tiempo, llamadas REST de estimación y, potencialmente, 30 corridas de graphify.
  - Cada fase pide aprobación humana (`README.md:16`), unas 10 por feature. Sí existe `-y` para autoaprobar (`skills/karvey-requirements/SKILL.md:146`, `skills/karvey-tasks/SKILL.md:125`), pero entonces la aprobación queda sin `by` / `ref`, en conflicto con `rules/phase-close.md:32`.
  - El dogfooding muestra el síntoma: las aprobaciones de `team-adapters` no tienen `ref` y prod cita una frase de la conversación (`docs/spec/changes/team-adapters/spec.json:81`).
- **Recomendación.**
  1. **Agrupar**: estado por tarea (barato), pero comentario y cascada por Feature, y graphify por fase y no por tarea (en `phase-close.md`, distinguir entre cierre de tarea y cierre de fase).
  2. **Clases de servicio**: además de `ops` y `hotfix`, un carril `small` (por ejemplo Tier 1–2, una capa y menos de N tareas) que agrupe los gates de planificación en una sola aprobación (como `--autoplan`, `skills/karvey/SKILL.md:153-155`) y omita mockup y diseño cuando no hay UI.
  3. `-y` debe registrar igual `by` y `role: human` con la referencia `"-y flag"`, para que la aprobación quede atribuida.
- **Justificación.** El overhead del proceso tiene que ser proporcional al riesgo. El método ya lo reconoce en los carriles `ops` y `hotfix` (`rules/multi-agent.md:84-101`). Un ritual demasiado caro termina saltándose, que fue justo el problema que motivó `phase-close.md` (`:3-5`). Las clases de servicio de Kanban formalizan esto.
- **Beneficio.** Menos llamadas a la API y menos tokens por cambio, menos interrupciones al humano en cambios chicos y más cumplimiento del ritual, porque cuesta menos. Se mide con llamadas al tracker y aprobaciones por cambio, y con el porcentaje de fases cerradas con ritual completo.
- **Esfuerzo** M · **Prioridad** media · **Riesgo** medio: un carril `small` mal usado baja el control. Conviene definirlo con criterios objetivos (Tier, capas, número de tareas) y que QA y el gate de prod no cambien.

### PM-10 · WBS sin ambigüedad: "Feature" hoy significa dos cosas distintas

- **Problema observado.**
  - `karvey-requirements` crea *"one Feature per functional area"* (`skills/karvey-requirements/SKILL.md:155`), y la cascada mueve una Feature cuando están listas *"ALL layers (BD+Backend+Frontend+Infra)"* (`rules/clickup-protocol.md:183`).
  - Al mismo tiempo, `phase-close` dice *"each pipeline phase maps to a Feature/checklist item in the Epic"* (`rules/phase-close.md:23`; también `rules/clickup-protocol.md:187`).
  - Además, `karvey-qa` crea un ítem padre "QA Review" (`skills/karvey-qa/SKILL.md:211`) y `karvey-deploy` una tarea "[Deploy]" (`skills/karvey-deploy/SKILL.md:278`), fuera de la jerarquía E.F.T.
  - Y `karvey-tasks` crea dependencias "Feature ← sus Tasks" y "Epic ← sus Features" (`skills/karvey-tasks/SKILL.md:216-217`), que duplican con dependencias la relación padre-hijo.
- **Recomendación.**
  - Fijar en `rules/management-adapters.md`: **Feature = área funcional** (la unidad de valor). **Las fases del pipeline** se registran como un checklist del Epic o como un campo personalizado "Karvey phase" en el Epic, nunca como Features.
  - Colgar QA Review y Deploy del Epic como tareas `E{n}.QA` y `E{n}.DEPLOY`, para que la suma del Epic incluya el retrabajo de QA.
  - Usar parent/child en vez de dependencias para la jerarquía.
- **Justificación.** Una WBS tiene que ser una descomposición única del alcance (regla del 100% del PMI). Si mezcla entregables con fases, se duplica el conteo, la cascada se vuelve impredecible y el tablero se llena de ítems que no son entregables.
- **Beneficio.** El tablero del cliente muestra avance por funcionalidad, el esfuerzo de QA queda sumado en el Epic (retrabajo visible) y la cascada se comporta de forma predecible. Se nota en tableros más limpios y en Epics cuya suma cuadra.
- **Esfuerzo** S · **Prioridad** media · **Riesgo** bajo.

### PM-11 · Decisiones pendientes y riesgos con dueño y fecha límite

- **Problema observado.**
  - El registro de decisiones guarda las decisiones **tomadas** (`skills/karvey-decisions/SKILL.md:37-52`). `cross` termina en *"no answer exists for X"* (`:65-66`), pero esa pregunta abierta no queda en ninguna parte con **dueño y fecha límite**.
  - La ubicación del registro es inconsistente: `rules/multi-agent.md:24` dice `docs/decisiones.md`, mientras la skill usa `{ops_repo}/decisions/`, un archivo por período (`skills/karvey-decisions/SKILL.md:31`).
  - Los riesgos aparecen en `karvey-grill` (`skills/karvey-grill/SKILL.md:101-104`, `:167`) y en una tabla de `architecture.md` (`skills/karvey-architecture/SKILL.md:214-218`), sin dueño, sin estado y sin revisión posterior. Ninguna fase (qa, deploy, archive) vuelve a mirarlos.
  - `approvals.prod.ref` exige un `D-NN` (`rules/multi-agent.md:59`), pero en el propio repo se llenó con una frase de chat (`docs/spec/changes/team-adapters/spec.json:81`).
- **Recomendación.**
  1. Agregar a `karvey-decisions` el subcomando `ask`, que registre `Q-NN` (pregunta abierta) con **dueño** (quién decide, idealmente un stakeholder del PRD), **needed-by** (la fecha a partir de la cual bloquea) y los cambios afectados. Cuando se resuelve, pasa a `D-NN`.
  2. `karvey-context` lista las `Q-NN` vencidas.
  3. Convertir la tabla de riesgos de arquitectura en `risks.md` por cambio, con dueño, estado y disparador. `karvey-qa` y `karvey-deploy` revisan los riesgos `open` antes de su gate, y `karvey-archive` los cierra o los traspasa al backlog.
  4. Unificar la ruta del registro de decisiones en `multi-agent.md`.
  5. Permitir que `approvals.prod.ref` sea un `D-NN` **o** la URL de aprobación del PR, para que no se invente una referencia.
- **Justificación.** Un registro de decisiones y un registro de riesgos sin dueño ni fecha son archivos, no herramientas de gestión. El caso medido de 13 de 14 bloqueos ya respondidos (`skills/karvey-decisions/SKILL.md:19-21`) muestra que el costo real está en las preguntas: la pregunta que sí está abierta necesita un dueño que la responda a tiempo.
- **Beneficio.** Queda claro quién debe decidir qué y para cuándo (sobre todo del lado del cliente), los riesgos se revisan antes de prod y las aprobaciones quedan con referencias que se pueden verificar. Se mide con las Q-NN vencidas y con los riesgos abiertos al momento del deploy.
- **Esfuerzo** M · **Prioridad** media · **Riesgo** bajo.

### PM-12 · Una retro que mida lo que produce el método, que se guarde y que alimente el backlog

- **Problema observado.**
  - `karvey-retro` analiza solo el historial de git: commits por autor, frecuencia, líneas y *"shipping streaks"* (`skills/karvey-retro/SKILL.md:19-31`, `:43-46`).
  - No lee `findings.md`, `iteration_count`, `revision_history`, la estimación contra el real, BUG-NN, el canary ni el costo, aunque el esquema dice que `iteration_count` es *"useful for the retro"* (`rules/living-specs.md:87`) y `karvey-archive` le promete *"how long each phase took vs. the estimate"* (`skills/karvey-archive/SKILL.md:131`).
  - No define dónde se guarda el resultado. Las acciones no se registran en el backlog, aunque `rules/backlog.md:16` dice que las oportunidades de la retro aterrizan ahí.
  - Con desarrollo asistido por IA, los commits por persona dicen poco del desempeño y pueden leerse como ranking, algo que la misma skill quiere evitar (`:63-65`).
- **Recomendación.** Rehacer los pasos 1–3 de `karvey-retro` sobre los artefactos del método:
  - las métricas de PM-05 del período;
  - la distribución de findings por tipo y origen (qué fase detecta más `spec-gap`, lo que indica un requirements débil);
  - la precisión de estimación (PM-02) y el costo (PM-08).
  Guardar `retro-{fecha}.md` en el cambio archivado o en `docs/spec/retros/`. Cada acción concreta se registra como `BL-NN` de tipo `process` con dueño. La retro siguiente revisa si las acciones anteriores se cumplieron. El análisis por persona queda como opcional.
- **Justificación.** Una retro sin datos del proceso ni seguimiento de acciones es la ceremonia que más cuesta en relación con lo que devuelve. El ciclo de mejora continua (inspect & adapt) exige que las acciones queden registradas y se verifiquen.
- **Beneficio.** Mejora del proceso con evidencia (por ejemplo, "los spec-gap salen en QA y no en mockup, así que hay que reforzar la validación spec-mockup"), acciones que no se pierden y menos riesgo de métricas de vanidad por persona. Se mide con el porcentaje de acciones de retro cerradas en el ciclo siguiente.
- **Esfuerzo** M · **Prioridad** media · **Riesgo** bajo.

### PM-13 · IDs secuenciales globales (BUG-NN, BL-NN, D-NN, E{n}) que chocan entre trabajo en paralelo

- **Problema observado.**
  - BUG-NN se asigna leyendo el archivo y continuando el contador (`rules/incident-tracking.md:9`; `skills/karvey-iterate/SKILL.md:57`).
  - D-NN se asigna escaneando el directorio (`skills/karvey-decisions/SKILL.md:39-40`).
  - El número del Epic sale de una búsqueda `E{1..99}` en ClickUp (`skills/karvey-init/SKILL.md:245-250`).
  - Con cambios en paralelo en ramas o worktrees distintos (el caso que el método promueve, `rules/multi-agent.md`), dos sesiones leen el mismo máximo y asignan el mismo número. El choque aparece recién al hacer merge, o no aparece nunca si cae en archivos distintos. Esto es una inferencia a partir de las reglas: no encontré un caso documentado dentro del repo.
  - El límite `E{1..99}` además no escala.
- **Recomendación.** Usar IDs que no necesiten coordinación, o reservarlos de forma atómica:
  - un prefijo por repo o cambio (`BUG-{repo}-NN`) y numeración en `incidents-index.md` al hacer merge a integración; o
  - reservar el número con un commit en la rama de integración antes de usarlo; o
  - usar el ID del tracker como fuente cuando existe.
  Documentar la regla en `incident-tracking.md`, `backlog.md` y `karvey-decisions`, y quitar el `E{1..99}`.
- **Justificación.** La trazabilidad depende de que los identificadores sean únicos. Un BUG-12 duplicado rompe los vínculos cruzados (finding → BUG → tracker → CHANGELOG) que son la gracia del método.
- **Beneficio.** Referencias confiables entre repos y sesiones, y ningún conflicto de merge ni corrección manual de numeración. Se mide con 0 IDs duplicados en `incidents-index.md`.
- **Esfuerzo** S · **Prioridad** media · **Riesgo** bajo.

### PM-14 · Vista de portafolio multi-cliente y multi-proyecto

- **Problema observado.** Toda la configuración y el dashboard son por proyecto: `docs/spec/project.json` en un solo `spec_repo` (`rules/project-config.md:5-11`). `karvey-context` recorre solo ese repo y sus `repos` (`skills/karvey-context/SKILL.md:12`). El cliente existe solo como `client_tag`, dentro del bloque de ClickUp (`rules/clickup-protocol.md:68`; `rules/living-specs.md:55`). No hay forma de ver, para toda la consultora, qué cambios hay por cliente, qué está bloqueado esperando al cliente ni cuánta capacidad se va a cada uno.
- **Recomendación.**
  1. Subir `client` a campo de primer nivel en `project.json` (y en `spec.json`) y sacarlo de `clickup`.
  2. Agregar `karvey-context --portfolio <file>`, donde el archivo (por ejemplo `portfolio.json` en el repo de operaciones) lista las rutas de varios `project.json`. Muestra, por cliente, cambios activos por fase, antigüedad, Q-NN y aprobaciones pendientes del cliente, releases del período y costo (PM-08).
  3. Mantenerlo de solo lectura, como `karvey-context` hoy.
- **Justificación.** La gestión de portafolio (balancear capacidad y compromisos entre clientes) es lo central del trabajo de una consultora con muchos tenants. Sin una vista agregada, las prioridades entre clientes se deciden por quién reclama más fuerte.
- **Beneficio.** Priorización entre clientes con datos, detección de clientes desatendidos o sobrecomprometidos y una base para la conversación comercial mensual. Se mide con el tiempo para contestar "¿cómo vamos con el cliente X?" (de horas a un comando).
- **Esfuerzo** M · **Prioridad** media · **Riesgo** bajo: es solo lectura, pero hay que controlar quién puede ver el portafolio consolidado.

### PM-15 · Backlog con criterios de priorización y un ciclo de vida completo

- **Problema observado.**
  - El backlog prioriza solo con `high/med/low` y sus estados son `open → promoted → discarded` (`rules/backlog.md:25-37`). No hay valor, costo de postergar ni esfuerzo aproximado, así que no se puede ordenar entre ítems ni entre clientes.
  - Solo se revisa en `karvey-archive` los ítems que salieron de ese mismo cambio (`rules/backlog.md:43`), así que los ítems huérfanos o antiguos no tienen revisión periódica.
  - En el propio repo aparece un estado que no está definido: BL-01 `done`, *"resolved directly (no change-id)"* (`docs/spec/backlog.md:5`, `:13`). Es trabajo hecho fuera del método que el ciclo de vida no contempla.
- **Recomendación.**
  1. Agregar a `backlog.md` las columnas `value` (1–5), `effort` (S/M/L o minutos), `cost_of_delay` / `needed_by` y `client`, y un puntaje simple tipo WSJF: (valor + urgencia) / esfuerzo.
  2. Agregar el estado `done-direct`, con el commit como referencia, para el trabajo chico que no merece un change-id.
  3. Agregar `karvey-context --backlog`, que ordene por puntaje y marque los ítems con más de N días sin revisión.
  4. Sugerir una revisión del backlog (refinamiento) cada 2 semanas en vez de depender solo del archive.
- **Justificación.** El backlog de descubrimiento hoy captura muy bien, porque nada queda en el aire, pero no ayuda a **decidir**. La priorización económica (WSJF o costo de postergar) es lo que convierte una lista en un plan.
- **Beneficio.** Se decide con criterio explícito qué change-id viene después, el backlog deja de envejecer y queda registrado el trabajo directo que hoy es invisible. Se mide con la antigüedad mediana del backlog `open` y con el porcentaje de ítems con puntaje.
- **Esfuerzo** S · **Prioridad** baja · **Riesgo** bajo.

---

## 4. Lo que NO cambiaría

- **Que el gate de prod no se delegue y quede registrado en el repo** (`rules/multi-agent.md:63-64`). Es el control de gobierno más valioso del método. Las mejoras de PM-04 y PM-11 lo amplían, no lo relajan.
- **Que no se pida el OK sobre gates rojos** (`rules/deploy-workflow.md:11-15`). Protege la aprobación humana de volverse un trámite.
- **La clasificación `bug` / `spec-gap` / `emergent` y el ripple quirúrgico** (`rules/iteration-loop.md:26-35`, `skills/karvey-iterate/SKILL.md:72-76`). Es gestión de cambios de alcance bien resuelta y proporcional. Solo le falta medirla (PM-05, PM-12).
- **La estimación en minutos de IA más revisión humana, como hipótesis** (`rules/clickup-protocol.md:129-154`). No la eliminaría: separar el tiempo de IA de la revisión humana es la distinción correcta. Lo que falta es registrar el real sin pisar la estimación (PM-02).
- **La capa de equipo opcional con su advertencia de costo al comienzo** (`rules/team.md:7-41`). Es un ejemplo de decidir con el número adelante. Lo que haría es extender la medición de costo al caso de un solo agente (PM-08), no sacar la advertencia.
- **Los estados lógicos con adaptadores por herramienta** (`rules/management-adapters.md:30-41`). Son el diseño adecuado para una consultora cuyos clientes usan trackers distintos.
- **Que los findings se registren en un lugar y se enruten desde otro** (`rules/iteration-loop.md:80-85`). Mantiene simples las skills de fase y concentra la lógica en un punto. Es fácil de auditar.
- **Las reglas de verificación** (`rules/verification.md`). Las usaría como justificación del validador de estado de PM-01 y no les agregaría nada: son la base para que cualquier métrica futura sea verdadera.
- **El carril `hotfix` con fix, BUG-NN y test de regresión en el mismo PR** (`rules/multi-agent.md:94-101`). Es rápido sin perder registro, y deja la materia prima para el change failure rate y el MTTR.
