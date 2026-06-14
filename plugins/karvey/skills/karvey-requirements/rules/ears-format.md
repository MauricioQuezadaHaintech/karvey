# EARS Format — Easy Approach to Requirements Syntax

## EARS patterns

### UBIQUITOUS (always active)
```
The {system} shall {action}.
```
Example: `The API shall validate all request payloads before processing.`

### EVENT-DRIVEN (external trigger)
```
WHEN {event}, the {system} shall {action}.
```
Example: `WHEN a user submits valid credentials, the system shall create an authenticated session.`

### STATE-DRIVEN (state condition)
```
WHILE {state}, the {system} shall {action}.
```
Example: `WHILE a call is active, the system shall stream audio events to the frontend.`

### CONDITIONAL (business condition)
```
IF {condition}, THEN the {system} shall {action}.
```
Example: `IF the tenant has multi-factor authentication enabled, THEN the system shall require a second factor.`

### OPTIONAL (optional feature)
```
WHERE {feature is enabled}, the {system} shall {action}.
```

### COMBINED
```
WHEN {event}, IF {condition}, THEN the {system} shall {action}.
```

## Structure of a complete EARS requirement

```markdown
### Requirement {N}: {Name}

{WHEN/WHILE/IF/WHERE} {context},
the {system} SHALL {observable behavior}.

#### Scenario: {Success case}
GIVEN {precondition}
WHEN {actor's action}
THEN the system {observable result}
AND {additional result if applicable}

#### Scenario: {Error case}
GIVEN {precondition}
WHEN {invalid action}
THEN the system {error response}
```

## Quality rules

1. **Testable**: each requirement must be verifiable with a test
2. **Technology-free**: do not mention implementation (not "use Redis", but "cache for X seconds")
3. **Unambiguous**: avoid "fast", "intuitive", "appropriate" — use concrete values
4. **Numeric IDs**: use `Requirement 1`, `1.1`, `1.2` — never letters
5. **Clear subject**: always state "the {system/service/user}"
6. **SHALL vs SHOULD**: SHALL = mandatory, SHOULD = recommended

## Litmus test: Does it belong in requirements or design?
- Can the EARS criterion be written without mentioning technology? → **Requirements**
- Does it require choosing a technology or pattern? → **Design**
