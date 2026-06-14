---
name: karvey-grill
description: Pre-spec interrogation. Interviews the engineer relentlessly about their problem before writing any spec. Use at the start of every new feature or initiative — before karvey-init. Triggers include "grill me", "entrevístame", "quiero especificar algo", "tengo una idea", "necesito una feature", "spec-driven", "SDD", "kiro", "gstack", "Garry Tan", "office hours", "producto 10 estrellas", "reframe", "PRD", "método de desarrollo".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [descripción breve del problema o idea]
---

# Karvey Grill — Pre-Spec Interrogation

## Propósito

Antes de escribir una sola línea de spec, este skill te entrevista en profundidad hasta que el problema esté completamente comprendido. Una pregunta a la vez. Con recomendación incluida en cada una.

## Instrucciones de ejecución

### Paso 0 — Reframe 10-estrellas (opcional)

> **Modo opcional.** Este paso va ANTES (o al inicio) de la interrogación. Su objetivo NO es especificar lo pedido, sino encontrar la **mejor versión del producto** escondida en el pedido. Inspirado en `/office-hours` + `/plan-ceo-review`.
>
> **Cuándo saltarlo:** si el usuario ya tiene total claridad del producto que quiere, o pide explícitamente ir directo a la interrogación, saltar a Paso 1. Ofrecerlo, no imponerlo.

Antes de arrancar, preguntar:

```
¿Querés hacer el reframe 10-estrellas primero (encontrar la mejor versión del producto), o vamos directo a la interrogación?

*Mi recomendación:* {hacerlo si el pedido es vago/ambicioso/estratégico; saltarlo si es un cambio acotado y bien definido}
```

Si el usuario acepta, recorrer las **seis preguntas forzadas**, **una pregunta a la vez, con recomendación** (mismas reglas del entrevistador). Cada pregunta reformula el producto antes de especificarlo:

1. **Desafiar la premisa.** ¿El problema planteado es el problema real, o un síntoma? ¿Qué pasaría si la premisa estuviera equivocada?
2. **Producto 10 estrellas.** Si esto fuera una experiencia perfecta (10/10), ¿cómo se vería? ¿Qué versión escondida del pedido deleitaría al usuario?
3. **Scope expansion (10x).** ¿Qué lo haría 10x mejor, no 10% mejor? ¿Qué capacidad adyacente lo transforma de "útil" a "imprescindible"?
4. **Selective expansion.** De esas ideas grandes, ¿cuáles valen la pena de verdad y caben en este esfuerzo? (separar el "wow" viable del "wow" fantasía)
5. **Hold scope.** ¿Qué dejamos deliberadamente para después (v2) aunque sea tentador? Marcar el límite consciente.
6. **Reduction.** ¿Qué sobra del pedido original? ¿Qué se puede quitar sin perder valor, o que incluso mejora el producto al sacarlo?

Al cerrar las seis, sintetizar un **mini design-doc / visión** (ver Paso 4: sección "Visión 10-estrellas"). Este documento **alimenta el PRD junto con la síntesis de la interrogación normal**: el reframe define el "qué deberíamos construir" y la interrogación define el "cómo lo construimos".

> Si se hizo el reframe, usar su visión para enfocar y afinar las preguntas de las ramas A–F (no repetir lo ya resuelto).

### Paso 1 — Contexto inicial

Si el usuario dio una descripción en `$ARGUMENTS`, usarla como punto de partida.
Si no, hacer la primera pregunta abierta: "¿Qué problema querés resolver y para quién?"

Antes de preguntar algo que pueda responderse explorando el codebase, **explorar primero**:
- Buscar si ya existe funcionalidad similar (`grep`, `find`)
- Leer archivos de configuración o specs existentes en `docs/spec/`
- Si encontrás la respuesta, presentarla como contexto y avanzar a la siguiente pregunta

### Paso 2 — Árbol de interrogación

Recorrer sistemáticamente estas ramas, **una pregunta a la vez**:

#### Rama A: El problema
1. ¿Quién tiene el problema? (persona/sistema/rol)
2. ¿Cuál es la situación actual que causa fricción?
3. ¿Qué tan frecuente ocurre? ¿Cuál es el impacto?
4. ¿Intentaron resolverlo antes? ¿Qué falló?

#### Rama B: El alcance
5. ¿Qué está DENTRO del alcance de esta iniciativa?
6. ¿Qué está FUERA del alcance explícitamente?
7. ¿Qué otros sistemas o componentes se ven afectados?
8. ¿Qué datos nuevos se necesitan? ¿Qué datos existentes se modifican?

#### Rama C: Restricciones técnicas
9. ¿En qué capa(s) opera esto: BD / Backend / Frontend / Infra?
10. ¿Hay integraciones externas involucradas?
11. ¿Qué nivel de seguridad requiere? (datos públicos / autenticado / datos sensibles / crítico con audit trail)
12. ¿Hay restricciones de performance o SLA?

#### Rama F: Stack tecnológico
> Antes de preguntar, explorar el codebase: `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `Gemfile`, `Cargo.toml`, archivos de config de BD, etc. Solo preguntar lo que no se pueda inferir.

13. ¿Cuál es el lenguaje y framework del backend? (Node/Express, Python/FastAPI, Go, Java/Spring, Ruby/Rails, etc.)
14. ¿Qué base de datos usa y cómo accede a ella? (PostgreSQL/ORM, MySQL/queries, MongoDB, Oracle/SPs, Redis, etc.)
15. ¿El cambio tiene UI? ¿Con qué framework? (React, Vue, Angular, Svelte, server-rendered, no aplica, etc.)
16. ¿Qué protocolo de API usa? (REST, GraphQL, gRPC, mensajería, WebSockets, etc.)
17. ¿Cómo se versionan los releases? (package.json, pyproject.toml, archivo VERSION, git tags, ninguno, etc.)
18. ¿Hay convenciones de git establecidas? (Conventional Commits, gitflow, trunk-based, squash, etc.)
19. ¿Plataforma de código/CI: GitHub o Azure DevOps? (dónde viven los repos y corren los pipelines)

    *Mi recomendación:* {detectar por remotes git / archivos de pipeline — `.github/workflows`, `azure-pipelines.yml` — y confirmar dónde corren los pipelines}
20. ¿Proveedor de nube: Azure, GCP, AWS, mixto o ninguno? Si es mixto, ¿qué parte en qué nube?

    *Mi recomendación:* {inferir por SDKs/CLIs y archivos de IaC presentes; si es mixto, pedir el desglose de qué componente vive en qué nube}
21. ¿Herramienta de IaC: Terraform, Bicep, Pulumi o ninguna (infra manual)?

    *Mi recomendación:* {buscar `*.tf`, `*.bicep`, `Pulumi.yaml`; si no hay, asumir infra manual y confirmarlo}

> **Nota:** la decisión de sincronización de conocimiento (Obsidian vs graphify) NO se pregunta aquí — la resuelve karvey-init según la disponibilidad del MCP de Obsidian (ver `karvey/rules/knowledge-sync.md`).

#### Rama D: Criterios de éxito
22. ¿Cómo sabremos que esto funciona correctamente?
23. ¿Cuáles son los casos de error críticos que deben manejarse?
24. ¿Qué NO debe cambiar del comportamiento actual?

#### Rama E: Dependencias y riesgos
25. ¿Qué debe estar listo ANTES de empezar esto?
26. ¿Qué bloquea este trabajo si no se resuelve primero?
27. ¿Cuál es el riesgo más grande de esta iniciativa?

### Paso 3 — Formato de cada pregunta

```
**Pregunta N/~27:** {pregunta clara y específica}

*Mi recomendación:* {tu respuesta sugerida basada en lo que ya sabés del contexto}
```

Adaptar las preguntas según las respuestas anteriores. Si una rama ya está clara, saltarla.
Si una respuesta genera sub-preguntas, profundizar antes de avanzar.

### Paso 4 — Síntesis final

Cuando el árbol esté cubierto (o el usuario indique que terminó), generar un resumen:

> Este resumen es el **insumo del PRD** (`prd.md`) que generará karvey-init. Mantenerlo completo y fiel: lo que falte aquí, faltará en el PRD.

```markdown
## Resumen Pre-Spec: {nombre tentativo del cambio}

### Visión 10-estrellas (si se hizo Paso 0)
> Mini design-doc del reframe. Omitir esta sección si el Paso 0 se saltó.
- **Premisa reencuadrada:** {el problema real vs. el síntoma planteado}
- **Producto 10 estrellas:** {cómo se ve la experiencia perfecta}
- **Expansión seleccionada:** {ideas 10x que SÍ entran en este esfuerzo}
- **Scope en espera (v2):** {lo grande que se deja deliberadamente para después}
- **Reducción:** {qué se quita del pedido original y por qué}

### El problema
{quién, situación actual, impacto}

### Lo que cambia
{qué entra en scope, qué queda fuera}

### Stack detectado
- Backend: {lenguaje/framework}
- Base de datos: {BD y patrón de acceso}
- Frontend: {framework o "no aplica"}
- API: {protocolo}
- Versionamiento: {mecanismo}
- Git: {convenciones}

### Plataforma & Despliegue
- Plataforma git: {GitHub | Azure DevOps}
- Proveedor(es) de nube: {Azure | GCP | AWS | mixto | ninguno — si es mixto, qué parte en qué nube}
- Herramienta IaC: {Terraform | Bicep | Pulumi | ninguna (infra manual)}

> Sincronización de conocimiento (Obsidian vs graphify): la decide karvey-init según disponibilidad del MCP de Obsidian (ver `karvey/rules/knowledge-sync.md`).

### Restricciones clave
- Capas: {BD/Backend/Frontend/Infra}
- Seguridad: {nivel — justificación}
- Integraciones externas: {lista}
- Restricciones técnicas: {lista}

### Criterios de éxito
{cómo se verifica que funciona}

### Casos de error críticos
{lista}

### Riesgos principales
{lista}

### Dependencias previas
{qué debe existir antes}

### Change ID sugerido
`{add|fix|update|remove}-{nombre-descriptivo}` — {rationale}
```

### Paso 5 — Transición

Al terminar, indicar:
```
✅ Interrogación completa. Siguiente paso:
/karvey-init {change-id-sugerido}
```

## Reglas del entrevistador

- **Una pregunta a la vez**. Nunca hacer dos preguntas en el mismo mensaje.
- **Siempre incluir recomendación** en cada pregunta.
- **Explorar el codebase** antes de preguntar algo que pueda descubrirse solo.
- **No asumir** tecnología, escala ni usuarios sin confirmar.
- **No avanzar** a especificación hasta que el árbol esté cubierto.
- El tono es colaborativo, no inquisitorial. El objetivo es construir entendimiento compartido.


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Init (crear el cambio) ahora?»
- Si confirma → ejecutá `/karvey-init {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
