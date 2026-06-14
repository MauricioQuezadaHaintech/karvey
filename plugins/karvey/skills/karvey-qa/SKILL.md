---
name: karvey-qa
description: QA code review in 8 dimensions (Security with OWASP Top 10 + STRIDE, Errors, Consistency, Impact, Env vars, Versioning, Second opinion cross-model, Visual audit vs design-spec). Creates REVISION_PR document, ClickUp tasks or PLAN.md entries. Notifies Google Chat. Triggers include "karvey qa", "code review", "revisión de código", "QA".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent
argument-hint: <change-id> [--source <branch>] [--target <branch>]
---

# Karvey QA

## Propósito

Revisión de código en 8 dimensiones post-implementación. Genera documento de revisión, crea subtareas en ClickUp o PLAN.md, y notifica al grupo de Google Chat del proyecto.

## Pasos de ejecución

### Paso 0 — Identificar ramas y stack

Leer `docs/spec/changes/{change-id}/spec.json`.

Si el usuario no especificó ramas, preguntar: "¿Cuáles son las ramas a comparar? (source → target)"
Convención por defecto: `feature/{change-id}` → `dev`

Detectar stack del repo (ver `package.json`, `requirements.txt`, `pyproject.toml`).

Obtener diff:
```bash
git diff {target}...{source} --stat
git diff {target}...{source}
git log {target}...{source} --oneline
```

### Paso 1 — Análisis en 8 dimensiones

Despachar subagentes paralelos para las dimensiones 1–4, ejecutar 5–6 en contexto principal. Las dimensiones 7 (second opinion cross-model) y 8 (auditoría visual) se ejecutan al final, una vez consolidados los hallazgos preliminares:

**Dimensión 1: Seguridad**
- Credenciales hardcodeadas (tokens, API keys, passwords)
- XSS: `v-html` sin sanitizar, `dangerouslySetInnerHTML`
- Auth solo en frontend sin enforcement en backend
- Datos personales reales en código (RUTs, emails, teléfonos)
- Validaciones de contexto de usuario ausentes en operaciones de datos o endpoints
- SQL dinámico sin sanitizar
- Stack traces expuestos al cliente

**Cobertura OWASP Top 10 (revisar explícitamente cada categoría):**
- A01 Broken Access Control — IDOR, escalamiento de privilegios, validación de contexto de tenant/usuario ausente
- A02 Cryptographic Failures — datos sensibles en claro, algoritmos débiles, TLS no forzado
- A03 Injection — SQL/NoSQL/OS/LDAP injection, queries dinámicas sin parametrizar
- A04 Insecure Design — falta de límites de tasa, flujos sin controles de negocio
- A05 Security Misconfiguration — defaults inseguros, CORS abierto, headers de seguridad faltantes, debug activo
- A06 Vulnerable & Outdated Components — dependencias con CVE conocidos
- A07 Identification & Authentication Failures — sesiones débiles, credenciales por defecto, MFA ausente donde corresponda
- A08 Software & Data Integrity Failures — deserialización insegura, pipelines/artefactos sin verificar
- A09 Security Logging & Monitoring Failures — eventos de seguridad sin registrar, logs con datos sensibles
- A10 Server-Side Request Forgery (SSRF) — fetch/requests con URL controlada por el usuario sin validar

**Modelado de amenazas STRIDE (clasificar cada hallazgo y buscar amenazas por categoría):**
- **S**poofing — suplantación de identidad/origen
- **T**ampering — alteración de datos en tránsito o reposo
- **R**epudiation — acciones sin trazabilidad/auditoría
- **I**nformation Disclosure — fuga de datos sensibles
- **D**enial of Service — agotamiento de recursos, falta de límites
- **E**levation of Privilege — escalamiento de permisos

> **🚧 GATE DE SEGURIDAD (bloqueante):** Si existe cualquier hallazgo de seguridad de severidad Crítica o Alta sin resolver, NO se habilita el despliegue. El gate cubre explícitamente las categorías **OWASP Top 10** y el modelado **STRIDE** descritos arriba: un hallazgo crítico/alto en cualquiera de ellas bloquea el avance. El cambio no puede avanzar a `/karvey-deploy` hasta resolver y re-ejecutar QA.

**Dimensión 2: Errores de código**
- Acceso a null/undefined sin guarda
- Memory leaks (listeners, intervals, subscriptions sin cleanup)
- Promesas no manejadas
- Firmas de funciones cambiadas sin actualizar callers
- Race conditions en async

**Dimensión 3: Consistencia**
- Typos en naming
- Mezcla de patrones en mismo módulo
- Código duplicado (3+ repeticiones que deberían ser helper)
- Axios directo saltando interceptores del apiService
- Tabs vs spaces

**Dimensión 4: Impacto en módulos existentes**
- Cambios en archivos compartidos (router, store raíz, apiService, componentes globales)
- Interfaces públicas modificadas sin actualizar consumidores
- Cambios de comportamiento implícitos (timeouts, guards, interceptores)

**Dimensión 5: Variables de entorno**
- Variables usadas en código pero no declaradas en Dockerfile/pipeline
- Variables sin fallback en algún ambiente
- Variables en `.env.example` pero no usadas

**Dimensión 6: Versionamiento**
- Archivo de versión del proyecto actualizado (`package.json`, `pyproject.toml`, `VERSION`, etc.)
- `CHANGELOG.md` con entrada para la versión actual
- Consistencia entre version file y CHANGELOG

Verificar el CHANGELOG según la regla `karvey/rules/changelog-policy.md`, para cada repo con cambios:
- `CHANGELOG.md` tiene entrada para la versión actual
- La entrada incluye **humano responsable** (nombre + contacto)
- La entrada indica el **modelo de IA** usado
- La entrada explica el **por qué** del cambio (no solo el qué)

Si falta cualquiera de estos campos, es hallazgo de versionamiento y bloquea el avance a deploy.

**Dimensión 7: Second opinion cross-model (revisión adversarial)**

Antes de liberar, obtener una revisión adversarial con OTRO modelo, invocando la skill transversal `karvey-second-opinion` sobre el mismo diff (`{target}...{source}`).

- Es **complementaria**, no reemplaza el juicio de QA: sirve para descubrir puntos ciegos del modelo principal (sesgos, suposiciones, casos borde no considerados).
- Pasar como contexto: el diff, el `spec.json` del change-id y los hallazgos preliminares de las dimensiones 1–6.
- Integrar los hallazgos nuevos del segundo modelo al documento de revisión, marcándolos con su origen (modelo + skill).
- Reglas de severidad: si el segundo modelo levanta un hallazgo crítico/alto que QA considera válido, aplica el mismo gate bloqueante. Las discrepancias entre modelos se documentan; la decisión final es del QA humano/principal.

**Dimensión 8: Auditoría visual del producto IMPLEMENTADO vs design-spec**

Auditar la UI **ya construida** en el runtime real del target (no el mockup, no el código aislado), apoyándose en `karvey-browse` para abrir el target y capturar el estado real. Es **agnóstico de target** (web, mobile, escritorio u otro): lo que importa es comparar lo que el usuario realmente ve contra lo especificado.

- Cargar el diseño esperado desde `docs/spec/changes/{change-id}/design-spec.md` (o el `design-spec.md` del scope correspondiente).
- Con `karvey-browse`, navegar el flujo implementado en el runtime real del target y capturar evidencia (screenshots/estado) de cada pantalla/estado relevante.
- Comparar implementado vs design-spec: layout, espaciados, tipografía, colores/tokens, estados (vacío, carga, error, hover/focus), responsividad, copy y jerarquía visual.
- Registrar cada desviación como hallazgo visual con severidad y evidencia.
- Para los fixes visuales: aplicar **commits atómicos** (un fix por commit) documentando **before/after** (captura antes y después). Las desviaciones que rompan accesibilidad o seguridad heredan el gate bloqueante de su dimensión correspondiente.

### Paso 2 — Generar documento de revisión

Nombre del archivo: `REVISION_PR_{numero}_{YYYYMMDD}.md` en la raíz del repo.

Estructura:
```markdown
# Revisión de Código — {change-id}: {source} → {target}

## Información General
- Repositorio: {nombre}
- Stack: {stack}
- Rama source: {source}
- Rama target: {target}
- Fecha: {YYYY-MM-DD}
- Commits incluidos: {N}
- Archivos modificados: {N}

## Resumen Ejecutivo
{párrafo con hallazgos más importantes}

## Hallazgos por Dimensión

### 1. Seguridad
{hallazgos con: #N, archivo, línea ~NNN, severidad, descripción, código problemático, recomendación, instrucciones para IA}

### 2. Errores de código
...

### 3. Consistencia
...

### 4. Impacto en módulos existentes
...

### 5. Variables de entorno
{tabla de cruce + discrepancias}

### 6. Versionamiento
{verificación del archivo de versión del proyecto y CHANGELOG o equivalente}

### 7. Second opinion cross-model
{modelo/skill usado, hallazgos nuevos del segundo modelo marcados con su origen, discrepancias documentadas}

### 8. Auditoría visual (implementado vs design-spec)
{desviaciones con severidad, evidencia before/after, referencia a design-spec.md}

## Tabla Resumen por Severidad
| Severidad | Cantidad |
|-----------|---------|
| Crítico | N |
| Alto | N |
| Medio | N |
| Bajo | N |

## Checklist antes del merge
- [ ] Todos los hallazgos críticos resueltos
- [ ] Todos los hallazgos altos resueltos
- [ ] Gate de seguridad superado (OWASP Top 10 + STRIDE sin críticos/altos)
- [ ] Second opinion cross-model ejecutada e integrada
- [ ] Auditoría visual vs design-spec sin desviaciones bloqueantes
- [ ] Variables de entorno verificadas
- [ ] Tests pasan
- [ ] Build de producción exitoso

## Áreas que requieren testing manual
- {área}: {razón}
```

### Paso 3A — Crear tareas en ClickUp (si management=clickup)

Obtener sprint activo: `clickup_get_list` con nombre "Sprint XX".

Crear tarea padre:
```
clickup_create_task
  name: "QA Review {change-id} ({source} → {target})"
  list_id: "{sprint_list_id}"
  priority: "high"
  tags: ["{client_tag}"]
```

Por cada hallazgo crítico y alto, crear subtarea:
```
clickup_create_task
  name: "#{N} [{SEVERIDAD}] {archivo}: {descripción corta}"
  parent: {tarea_padre_id}
  priority: {urgent|high|normal|low}
  assignees: [{autor según git log del archivo}]
  time_estimate: {5-60 min en ms}
  markdown_description: (ver formato en QA_CODE_REVIEW_STANDARD)
```

Estimación de fixes:
- Fix simple (null check, typo): 5-10min
- Fix medio (agregar validación, cleanup): 15-20min
- Fix complejo (extraer helper, mover a env var): 30min
- Migración masiva: 45-60min

### Paso 3B — Actualizar PLAN.md (si management=markdown)

Agregar sección "QA Review" al final del PLAN.md con la lista de hallazgos y acciones pendientes.

### Paso 3C — Actualizar grafo de conocimiento

Sincronizar el conocimiento según `karvey/rules/knowledge-sync.md` (Obsidian si está disponible; mínimo `/graphify docs/spec/ --update`) para reflejar el `REVISION_PR_{n}_{fecha}.md` generado.
Si `docs/spec/graphify-out/` no existe, invocar `/graphify docs/spec/` sin `--update`.

### Paso 3D — Actualizar estado en spec.json

Actualizar `docs/spec/changes/{change-id}/spec.json` según el resultado del QA:

- Si NO hay hallazgos críticos ni altos (incluido el GATE DE SEGURIDAD de la Dimensión 1 con OWASP Top 10 + STRIDE, los hallazgos válidos del second opinion cross-model y las desviaciones visuales bloqueantes) → marcar `approvals.qa.approved: true` y `phase: "qa"`.
- Si hay hallazgos bloqueantes (críticos/altos, gate de seguridad sin resolver, hallazgo crítico/alto válido del segundo modelo, o desviación visual que rompe accesibilidad/seguridad) → marcar `approvals.qa.approved: false`.

### Paso 4 — Notificar por Google Chat

Identificar el space del proyecto en la tabla de espacios conocidos.
Enviar resumen al grupo usando el protocolo de Google Chat del CLAUDE.md.

Formato del mensaje (Google Chat):
```
*QA Review — {change-id}*

*{source}* → *{target}*

*Hallazgos:*
- 🔴 Críticos: {N}
- 🟠 Altos: {N}
- 🟡 Medios: {N}
- ⚪ Bajos: {N}

*Áreas de testing manual:*
- {área 1}
- {área 2}

Documento completo: `REVISION_PR_{n}_{fecha}.md`
```

### Paso 5 — Output final

```
✅ QA Review completo

Hallazgos: {N} total ({críticos}, {altos}, {medios}, {bajos})
Documento: REVISION_PR_{n}_{fecha}.md

Gestión: {N subtareas creadas en ClickUp | PLAN.md actualizado}
Google Chat: notificación enviada a {grupo}

Siguiente paso (si hay hallazgos críticos/altos):
  Corregir → re-ejecutar /karvey-impl {change-id} → /karvey-test {change-id} → /karvey-qa {change-id}

Siguiente paso (si sin hallazgos bloqueantes):
  /karvey-deploy {change-id}
```


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Despliegue ahora?»
- Si confirma → ejecutá `/karvey-deploy {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
