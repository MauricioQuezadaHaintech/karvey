# Living Specs — Estructura y Protocolo

## Estructura de directorios

```
docs/spec/
├── specs/                          # Living specs (fuente de verdad acumulativa)
│   └── {capability}/
│       └── spec.md                 # Spec maestra del capability (crece con el tiempo)
└── changes/                        # Cambios en curso
    ├── {change-id}/
    │   ├── spec.json               # Metadata del cambio
    │   ├── proposal.md             # Por qué, qué y el impacto
    │   ├── requirements.md         # EARS requirements del cambio
    │   ├── spec-delta.md           # ADDED/MODIFIED/REMOVED sobre las living specs
    │   ├── design-spec.md          # Especificación de diseño gráfico
    │   ├── architecture.md         # Diseño técnico y arquitectura
    │   ├── tasks.md                # Plan de tareas de implementación
    │   ├── PLAN.md                 # (solo si management=markdown) Plan y checklist
    │   ├── mockup.html             # Mockup navegable HTML
    │   └── IMPLEMENTED             # Archivo vacío que marca: desplegado a producción
    └── archive/                    # Cambios completados y archivados
        └── {YYYY-MM-DD}-{change-id}/
            └── (mismos archivos del change)
```

## spec.json — estructura

```json
{
  "change_id": "add-feature-name",
  "capability": "nombre-del-capability",
  "created_at": "2026-05-31T00:00:00Z",
  "updated_at": "2026-05-31T00:00:00Z",
  "language": "es",
  "management": "clickup",
  "security_tier": 2,
  "phase": "requirements",
  "clickup": {
    "epic_id": "",
    "feature_ids": [],
    "backlog_list_id": "",
    "client_tag": ""
  },
  "approvals": {
    "requirements": { "generated": false, "approved": false },
    "mockup": { "generated": false, "approved": false },
    "design_graphic": { "generated": false, "approved": false },
    "architecture": { "generated": false, "approved": false },
    "tasks": { "generated": false, "approved": false }
  }
}
```

## spec-delta.md — formato

```markdown
# Spec Delta: {change-id}

## ADDED Requirements

### Requirement: {Nombre}
WHEN {evento},
the system SHALL {comportamiento}.

#### Scenario: {caso}
GIVEN ...
WHEN ...
THEN ...

## MODIFIED Requirements

### Requirement: {Nombre existente}
<!-- Reemplaza COMPLETAMENTE el requirement en docs/spec/specs/{capability}/spec.md -->
WHEN {nuevo comportamiento},
the system SHALL {nuevo resultado}.

## REMOVED Requirements

### Requirement: {Nombre a eliminar}
<!-- Razón: {por qué se elimina} -->
```

## Protocolo de archiving

Al completar e implementar un cambio:

1. Verificar que `IMPLEMENTED` existe en el directorio del change
2. Por cada operación en spec-delta.md:
   - **ADDED**: append al final de `docs/spec/specs/{capability}/spec.md`
   - **MODIFIED**: reemplazar el bloque completo del requirement por nombre
   - **REMOVED**: eliminar el bloque + agregar comentario de deprecación
3. Git commit: "Merge spec deltas from {change-id}"
4. Mover carpeta: `mv docs/spec/changes/{change-id} docs/spec/changes/archive/{fecha}-{change-id}`
5. Git commit: "Archive {change-id}"

## Convención de capabilities

Los capabilities representan dominios funcionales del producto, no features individuales.
Ejemplos válidos: `authentication`, `call-management`, `contact-search`, `notifications`, `tenant-config`
Evitar: `fix-bug-123`, `add-button`, `update-sp` (demasiado granulares)
