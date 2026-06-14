# EARS Format — Easy Approach to Requirements Syntax

## Patrones EARS

### UBIQUITOUS (siempre activo)
```
The {sistema} shall {acción}.
```
Ejemplo: `The API shall validate all request payloads before processing.`

### EVENT-DRIVEN (trigger externo)
```
WHEN {evento}, the {sistema} shall {acción}.
```
Ejemplo: `WHEN a user submits valid credentials, the system shall create an authenticated session.`

### STATE-DRIVEN (condición de estado)
```
WHILE {estado}, the {sistema} shall {acción}.
```
Ejemplo: `WHILE a call is active, the system shall stream audio events to the frontend.`

### CONDITIONAL (condición de negocio)
```
IF {condición}, THEN the {sistema} shall {acción}.
```
Ejemplo: `IF the tenant has multi-factor authentication enabled, THEN the system shall require a second factor.`

### OPTIONAL (feature opcional)
```
WHERE {feature está habilitado}, the {sistema} shall {acción}.
```

### COMBINED
```
WHEN {evento}, IF {condición}, THEN the {sistema} shall {acción}.
```

## Estructura de un requisito EARS completo

```markdown
### Requirement {N}: {Nombre}

{WHEN/WHILE/IF/WHERE} {contexto},
the {sistema} SHALL {comportamiento observable}.

#### Scenario: {Caso exitoso}
GIVEN {precondición}
WHEN {acción del actor}
THEN the system {resultado observable}
AND {resultado adicional si aplica}

#### Scenario: {Caso de error}
GIVEN {precondición}
WHEN {acción inválida}
THEN the system {respuesta de error}
```

## Reglas de calidad

1. **Testeable**: cada requisito debe poder verificarse con un test
2. **Sin tecnología**: no mencionar implementación (no "usar Redis", sino "cachear durante X segundos")
3. **Sin ambigüedad**: evitar "rápido", "intuitivo", "apropiado" — usar valores concretos
4. **IDs numéricos**: usar `Requirement 1`, `1.1`, `1.2` — nunca letras
5. **Sujeto claro**: siempre indicar "the {system/service/user}"
6. **SHALL vs SHOULD**: SHALL = obligatorio, SHOULD = recomendado

## Litmus test: ¿Pertenece a requirements o a design?
- ¿Se puede escribir el criterio EARS sin mencionar tecnología? → **Requirements**
- ¿Requiere elegir una tecnología o patrón? → **Design**
