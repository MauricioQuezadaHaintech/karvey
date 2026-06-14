# Security Tiers — Karvey Method

## Tier definitions

### Tier 1 — Public
- No authentication required
- Non-sensitive data, reference information
- Basic rate limiting
- Controls: HTTPS, input validation, rate limit

### Tier 2 — Authenticated
- Requires a valid credential (token, session, API key)
- User or business-context data
- Controls: authentication, basic authorization, access logging

### Tier 3 — Privileged
- Requires a specific role (supervisor, admin, system)
- Sensitive operations: modify configuration, access other users' data
- Controls: RBAC, per-operation permission validation, basic audit trail

### Tier 4 — Critical
- Access to highly sensitive data (PII, financial, medical) or irreversible actions
- Controls: multi-factor authentication, full audit trail, encryption at rest and in transit, dual approval if applicable, automatic alerts on unusual access

## Application by layer

| Layer | Minimum tier | Notes |
|---|---|---|
| Public endpoints (incoming webhooks) | Tier 1 + signature validation | Verify the provider's signature |
| Authenticated user endpoints | Tier 2 | Validate the user context on every operation |
| Admin/config endpoints | Tier 3 | Validate the role before executing |
| PII data, sensitive logs, private files | Tier 4 | Never expose in logs |
| Data layer (queries, SPs, ORM) | Tier of the endpoint that calls them | Always validate the user context on data access |

## How to document it in the design

For each architecture component, indicate:
```
Component: {name}
Security Tier: {1|2|3|4}
Justification: {why this tier}
Required controls:
  - {control 1}
  - {control 2}
```

## Security anti-patterns (forbidden)

- Hardcoding API keys, tokens or passwords in code
- Relying only on frontend validations
- Exposing stack traces to the client
- Logs that include tokens, passwords or PII
- Endpoints without user-context validation
- Dynamic queries or commands concatenating inputs without sanitizing
- Environment variables not declared in the CI/CD pipeline
