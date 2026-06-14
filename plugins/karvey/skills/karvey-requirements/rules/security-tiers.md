# Security Tiers — Método Karvey

## Definición de tiers

### Tier 1 — Público
- Sin autenticación requerida
- Datos no sensibles, información de referencia
- Rate limiting básico
- Controles: HTTPS, input validation, rate limit

### Tier 2 — Autenticado
- Requiere credencial válida (token, sesión, API key)
- Datos del usuario o del contexto de negocio
- Controles: autenticación, autorización básica, logging de acceso

### Tier 3 — Privilegiado
- Requiere rol específico (supervisor, admin, sistema)
- Operaciones sensibles: modificar configuración, acceder a datos de otros usuarios
- Controles: RBAC, validación de permisos por operación, audit trail básico

### Tier 4 — Crítico
- Acceso a datos muy sensibles (PII, financiero, médico) o acciones irreversibles
- Controles: autenticación multifactor, audit trail completo, cifrado en reposo y tránsito, aprobación dual si aplica, alertas automáticas en acceso inusual

## Aplicación por capa

| Capa | Tier mínimo | Notas |
|---|---|---|
| Endpoints públicos (webhooks entrantes) | Tier 1 + validación de firma | Verificar firma del proveedor |
| Endpoints de usuario autenticado | Tier 2 | Validar contexto de usuario en cada operación |
| Endpoints admin/config | Tier 3 | Validar rol antes de ejecutar |
| Datos PII, logs sensibles, archivos privados | Tier 4 | Nunca exponer en logs |
| Capa de datos (queries, SPs, ORM) | Tier del endpoint que los llama | Siempre validar contexto de usuario en el acceso a datos |

## Cómo documentar en el diseño

Para cada componente de la arquitectura, indicar:
```
Componente: {nombre}
Security Tier: {1|2|3|4}
Justificación: {por qué este tier}
Controles requeridos:
  - {control 1}
  - {control 2}
```

## Anti-patrones de seguridad (prohibidos)

- Hardcodear API keys, tokens o passwords en código
- Confiar en validaciones solo del frontend
- Exponer stack traces al cliente
- Logs que incluyan tokens, passwords o PII
- Endpoints sin validación del contexto de usuario
- Queries o comandos dinámicos concatenando inputs sin sanitizar
- Variables de entorno sin declarar en pipeline CI/CD
