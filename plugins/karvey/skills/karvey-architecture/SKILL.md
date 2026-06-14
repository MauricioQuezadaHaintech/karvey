---
name: karvey-architecture
description: Generate enterprise architecture design with explicit security controls, component boundaries, and integration patterns. Use after karvey-design-graphic. Triggers include "karvey architecture", "diseño técnico", "arquitectura", "diseño de sistema".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, AskUserQuestion
argument-hint: <change-id> [-y]
---

# Karvey Architecture

## Propósito

Generar el diseño técnico de arquitectura empresarial: componentes, boundaries, integraciones, controles de seguridad por tier, observabilidad, y estructura de archivos concreta por capa.

## Pasos de ejecución

### Paso 1 — Cargar contexto

Leer en paralelo:
- `docs/spec/changes/{change-id}/spec.json` (security_tier, layers, capability)
- `docs/spec/changes/{change-id}/requirements.md`
- `docs/spec/changes/{change-id}/design-spec.md`
- `docs/spec/project.json` (cloud.provider, iac_tool, git_platform)
- `rules/security-tiers.md`
- Steering del proyecto: `product.md`, `tech.md` o equivalentes si existen

Verificar `approvals.design_graphic.approved = true`. Si no, detener.

### Paso 2 — Discovery de arquitectura

**Para features que extienden el sistema existente (brownfield):**

Despachar subagentes para explorar en paralelo:
- Subagente A: `grep -r` de patrones existentes relacionados con el capability
- Subagente B: leer endpoints/SPs existentes del área afectada

Identificar:
- Patrones de código existentes a seguir (naming, estructura de funciones, manejo de errores)
- Acceso a datos existente y sus firmas (SPs, queries, ORM models, repositorios, etc.)
- Endpoints / operaciones de API existentes y sus contratos
- Integraciones externas que ya existen

**Para features completamente nuevos (greenfield):**
- Definir los patrones nuevos coherentes con el stack existente

### Paso 3 — Clasificar complejidad arquitectónica

| Tipo | Criterio | Discovery |
|------|----------|-----------|
| Simple addition | Solo agrega CRUD o UI sin lógica nueva | Mínimo |
| Extension | Extiende sistema existente con lógica nueva | Medio |
| New capability | Capability nuevo, sin base existente | Completo |
| Complex integration | Integración con sistema externo o multi-capa | Exhaustivo |

### Paso 4 — Generar borrador de architecture.md

Estructura obligatoria:

```markdown
# Architecture: {change-id}

## Resumen
{1 párrafo: qué resuelve y cómo a alto nivel}

## Diagramas (OBLIGATORIO — al menos uno)

Esta arquitectura DEBE incluir al menos un diagrama en mermaid: de **flujo de datos** (data flow) y/o de **componentes**. Recomendado generarlo con la skill transversal `karvey-diagram`, que produce mermaid coherente con el resto de la spec.

```mermaid
{diagrama de componentes o data flow — generado idealmente con /karvey-diagram}
```

> Mínimo exigible: 1 diagrama. Para features de tipo "Complex integration" o "New capability", incluir ambos (componentes + data flow).

## Boundary del sistema
**Esta spec es dueña de:**
- {componente/endpoint/SP 1}
- {componente/endpoint/SP 2}

**Esta spec NO toca:**
- {componente existente que se mantiene}
- {funcionalidad adyacente fuera de scope}

**Cambios que requieren revalidación de este diseño:**
- {condición 1 que haría obsoleto este diseño}

## Componentes y responsabilidades

### Capa BD
| Componente | Tipo | Responsabilidad | Security Tier |
|------------|------|----------------|---------------|
| `{schema}.{sp_nombre}` | SP / función nueva | {qué hace} | Tier {N} |
| `{tabla}` | Tabla modificada | {qué columna/índice} | Tier {N} |

**Controles de seguridad BD:**
- Validación de contexto de usuario en cada query/SP: SÍ/NO
- Parámetros tipados (no SQL/query dinámico): SÍ/NO
- Logging de operaciones críticas: SÍ/NO

### Capa Backend
| Componente | Tipo | Responsabilidad | Security Tier |
|------------|------|----------------|---------------|
| `{backend_path}/{nombre}` | Endpoint / función nueva | {qué hace} | Tier {N} |
| `{módulo}` | Módulo modificado | {qué cambia} | Tier {N} |

**Controles de seguridad Backend:**
- Autenticación requerida: Tier {N} → {mecanismo: JWT, session, API key, etc.}
- Validación de contexto de usuario por request: SÍ/NO
- Sanitización de inputs en boundaries: SÍ/NO
- Manejo de errores sin exponer stack traces: SÍ/NO
- Variables sensibles via secrets manager: SÍ/NO

### Capa Frontend
| Componente | Tipo | Responsabilidad |
|------------|------|----------------|
| `{componente}` | Componente nuevo | {qué renderiza} |
| `{state_path}/{store}` | Store nuevo/modificado | {qué estado maneja} |
| `{api_layer}/{servicio}` | Servicio API | {qué endpoints consume} |

**Controles de seguridad Frontend:**
- Auth checks en rutas: Solo frontend como UX, enforcement en backend
- No exponer datos de otros tenants en store
- Sanitización de outputs dinámicos (no v-html sin sanitizar)

### Integraciones externas
| Sistema | Dirección | Protocolo | Auth | Timeout |
|---------|-----------|-----------|------|---------|
| {sistema} | inbound/outbound | REST/WebSocket | {mecanismo} | {ms} |

## Infraestructura Cloud

**Proveedor(es) de nube:** {de `project.json` `cloud.provider`. Si es `mixed`, especificar explícitamente qué parte del sistema corre en qué nube — ej: "backend y BD en Azure; almacenamiento de archivos en GCP Cloud Storage"}

| Servicio cloud | Nube | Propósito | Capa | Security Tier |
|----------------|------|-----------|------|---------------|
| {ej. Azure Functions} | Azure | {qué hace} | Backend | Tier {N} |
| {ej. Azure SQL} | Azure | {qué hace} | BD | Tier {N} |
| {ej. GCP Cloud Storage} | GCP | {qué hace} | {capa} | Tier {N} |

**Región(es) / zona:** {ej. East US 2 / southamerica-west1}

**Herramienta IaC:** {de `project.json` `iac_tool`}. El código IaC vivirá en {dónde — ej. `infra/` del repo correspondiente, o repo de infra dedicado}.

**Trigger de despliegue:** push a `dev` → deploy DEV; merge a `master` → deploy PROD. Siempre gatillado por pipeline, NUNCA manual.

> El detalle de IaC (módulos, recursos concretos) y pipelines lo genera la FASE 6 (`/karvey-infra`). Esta sección solo declara qué servicios de qué nube se usan a nivel de diseño.

## Flujo de datos principal

```
{Actor} → {Frontend} → {API Gateway / BFF} → {Backend} → {BD / Servicio}
                                                    ↓
                                         {Sistema externo}
```

Describir el flujo paso a paso para el caso de uso principal:
1. {paso 1: qué hace el actor}
2. {paso 2: cómo responde el frontend}
3. {paso N: qué persiste en BD}

## Trust boundaries (límites de confianza)

Marcar explícitamente DÓNDE entra input no confiable y DÓNDE se valida. Todo dato que cruza un límite hacia adentro debe validarse/sanitizarse en ese cruce.

| Límite de confianza | Qué cruza | Lado no confiable | Dónde se valida/sanitiza | Control |
|---------------------|-----------|-------------------|--------------------------|---------|
| Cliente → Backend | {payload del request} | Frontend / red pública | {endpoint / capa de entrada} | {validación de schema, auth, sanitización} |
| Backend → BD | {parámetros del query/SP} | {capa backend} | {SP / capa de acceso a datos} | {parámetros tipados, contexto de usuario} |
| Sistema externo → Backend | {webhook / respuesta de API} | {sistema externo} | {handler de inbound} | {verificación de firma, validación de payload} |

> Regla: ningún dato proveniente del lado no confiable se usa sin validar. Marcar en el diagrama de data flow el cruce de cada trust boundary (ej. línea punteada `-. untrusted .->`).

## Puntos de control de seguridad

| Punto | Tier | Control |
|-------|------|---------|
| Entrada al endpoint | {N} | Validar auth token, extraer identidad del usuario |
| Llamada a BD / servicio | {N} | Pasar contexto de usuario, no trustar input |
| Respuesta al cliente | {N} | No filtrar datos de otros usuarios/tenants |
| Logging | {N} | No loggear PII ni tokens |

## Plan de archivos (concreto)

### Archivos a CREAR
| Archivo | Capa | Responsabilidad |
|---------|------|----------------|
| `{backend_path}/{nombre}` | Backend | {descripción} |
| `{frontend_path}/{nombre}` | Frontend | {descripción} |

### Archivos a MODIFICAR
| Archivo | Capa | Cambio |
|---------|------|--------|
| `{backend_path}/{existente}` | Backend | Agregar {qué} |

### Archivos de BD
| Archivo | Tipo | Cambio |
|---------|------|--------|
| `{db_path}/{sp_nombre}.sql` | SP / migración nueva | {descripción} |

## Estrategia de observabilidad

- Logging estructurado en: {puntos de log}
- Métricas a trackear: {lista}
- Alertas recomendadas: {lista}
- Trazabilidad de request: {correlationId, userId/contextKey en cada log}

## Decisiones arquitectónicas

| Decisión | Alternativa considerada | Por qué se eligió esta |
|----------|------------------------|------------------------|
| {decisión 1} | {alternativa} | {razón} |

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| {riesgo} | Alta/Media/Baja | Alto/Medio/Bajo | {cómo se mitiga} |

## Edge cases / casos extremos (OBLIGATORIO)

Listar los casos límite identificados y cómo los maneja el diseño. Cubrir al menos: inputs vacíos/nulos, valores fuera de rango, concurrencia/duplicados, fallas de dependencias externas (timeout, error, indisponibilidad), datos inconsistentes y límites de tamaño/cantidad.

| Caso extremo | Cómo se maneja | Componente responsable |
|--------------|----------------|------------------------|
| {input vacío / nulo} | {comportamiento esperado} | {componente} |
| {valor fuera de rango / inválido} | {validación + respuesta} | {componente} |
| {request duplicado / concurrencia} | {idempotencia / lock / dedup} | {componente} |
| {timeout o error de sistema externo} | {retry / fallback / degradación} | {componente} |
| {dato inconsistente o estado inesperado} | {detección + manejo} | {componente} |

## Plan de cobertura de tests (alimenta /karvey-test)

Declarar qué se testea y a qué nivel. Cada requirement y cada edge case crítico debe tener al menos un test asociado en algún nivel.

| Qué se testea | Nivel (unit / integración / E2E) | Componente / capa | Caso(s) que cubre |
|---------------|----------------------------------|-------------------|-------------------|
| {lógica de validación} | unit | Backend | {requirement / edge case} |
| {flujo endpoint → BD} | integración | Backend + BD | {requirement} |
| {flujo de usuario completo} | E2E | Frontend + Backend | {caso de uso principal} |
| {manejo de edge case} | unit / integración | {capa} | {edge case del listado anterior} |

> Esta tabla es el contrato de testing que consume `/karvey-test` en la FASE de testing.
```

### Paso 5 — Review gate

Verificar antes de escribir:
- [ ] Todos los requirements tienen al menos un componente que los implementa
- [ ] El boundary está explícitamente definido
- [ ] Cada componente tiene su Security Tier declarado
- [ ] No hay componentes con responsabilidad vaga ("helper", "utils" sin descripción)
- [ ] El plan de archivos es concreto (paths reales, no "crear archivo para X")
- [ ] Los controles de seguridad cubren el Tier declarado en spec.json
- [ ] La sección Infraestructura Cloud especifica qué servicios de qué nube se usan (y qué parte de qué nube si es mixto)
- [ ] Hay estrategia de observabilidad
- [ ] Hay al menos un diagrama en mermaid (data flow y/o componentes); para "Complex integration" / "New capability" están ambos. Recomendado generarlo con `/karvey-diagram`
- [ ] Hay sección de Edge cases que cubre al menos: inputs vacíos/nulos, fuera de rango, concurrencia/duplicados, fallas de sistemas externos y datos inconsistentes
- [ ] Los Trust boundaries están marcados explícitamente: dónde entra input no confiable y dónde se valida cada cruce
- [ ] Hay Plan de cobertura de tests con nivel (unit/integración/E2E) por ítem; cada requirement y cada edge case crítico tiene al menos un test asociado

Si hay issues: corregir y re-verificar. Máximo 2 iteraciones.

### Paso 6 — Escribir architecture.md

```
docs/spec/changes/{change-id}/architecture.md
```

Actualizar `spec.json`:
- `phase: "architecture-generated"`
- `approvals.architecture.generated: true`

### Paso 6B — Actualizar grafo de conocimiento

Sincronizar el conocimiento según `karvey/rules/knowledge-sync.md` (Obsidian si está disponible; mínimo `/graphify docs/spec/ --update`) para reflejar el `architecture.md` creado.
Si `docs/spec/graphify-out/` no existe, invocar `/graphify docs/spec/` sin `--update`.

### Paso 7 — Presentar para aprobación

Si flag `-y`: auto-aprobar.
Si no: presentar resumen y pedir aprobación.

Al aprobar: `approvals.architecture.approved: true`, `phase: "architecture-approved"`.

```
✅ Architecture aprobada

Siguiente paso:
/karvey-infra {change-id}
```


## Avanzar a la siguiente fase

Al terminar esta fase y contar con la aprobación correspondiente, **preguntá activamente al usuario**: «¿Avanzamos a la fase Infraestructura ahora?»
- Si confirma → ejecutá `/karvey-infra {change-id}`.
- Si prefiere revisar o ajustar antes → esperá. El avance siempre es con el OK del usuario (gate del método).
- Si retomás en otra sesión, `/karvey {change-id}` indica en qué fase vas y cuál sigue.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
