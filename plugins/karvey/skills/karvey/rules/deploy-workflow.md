# Regla: Flujo de despliegue (git + pipeline)

Define el flujo ordenado de despliegue que usa el método. Lo aplican `karvey-impl` (durante el desarrollo) y `karvey-deploy` (FASE 11). Alineado con las reglas duras de deploy del equipo.

## Principios (NUNCA saltarse)

1. **Nunca commit directo en `dev` ni `master`.** Siempre feature branch.
2. **Nunca deploy manual.** El deploy lo gatilla el pipeline: push a `dev` → deploy dev; merge a `master` → deploy prod. Prohibido `func azure functionapp publish` o equivalentes manuales.
3. **`pull` antes de empezar y `pull` antes de cada merge/PR.** Evitar trabajar sobre base desactualizada.
4. **Prod requiere OK humano explícito.** El PR a `master` no se mergea sin aprobación.
5. **Zero downtime**: el despliegue no puede provocar caída del servicio.

## Flujo paso a paso

Para cada repo afectado (`project.json:repos`):

```
0. git pull                              # antes de comenzar
1. git checkout -b feature/{change-id}   # o el feature_prefix de project.json
   (desarrollo + commits por task — ver karvey-impl)
2. git pull origin {integration}         # antes de merge (default: dev)
3. merge feature/{change-id} → dev
4. git push origin dev                   # ⇒ gatilla pipeline de DEV
5. Verificar deploy DEV (smoke/healthcheck)
6. git pull origin {production}          # antes del PR (default: master)
7. PR dev → master
8. Merge a master SOLO con OK humano      # ⇒ gatilla pipeline de PROD
```

## Checklist de 6 pasos (antes de cualquier deploy)

1. ¿Estoy en feature branch? (no dev/master)
2. ¿Actualicé `CHANGELOG.md`? (ver `changelog-policy.md`)
3. ¿Commit de todo lo pendiente?
4. ¿Push del branch?
5. ¿Merge a `dev`?
6. ¿Push `dev`?

Solo después de los 6 → el pipeline despliega dev. Para prod, repetir verificación y PR a master con aprobación.

## Multi-repo

Si el cambio toca varios repos, aplicar el flujo en **cada uno**, respetando el orden de dependencias declarado en `architecture.md` (ej. BD antes que backend antes que frontend). Registrar el avance por repo en la gestión (ClickUp/`PLAN.md`).

## Gestión

`karvey-deploy` registra el despliegue en la gestión del proyecto:
- ClickUp: task `[Deploy] {change-id}` con el checklist de 6 pasos como subtareas/comentario y cierre al confirmar prod.
- Markdown: entrada en `PLAN.md` con el estado del deploy por repo y ambiente.
