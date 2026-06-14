# Regla: Política de CHANGELOG (trazabilidad humano + IA)

**Todo código generado por el método Karvey debe quedar registrado en un CHANGELOG.** El objetivo es trazabilidad mínima: **quién, cuándo y por qué**, dejando explícito que el trabajo fue **asistido por IA y con qué modelo**, pero **identificando siempre al humano responsable** detrás del cambio.

Aplica a TODO el código: aplicación (`karvey-impl`), infraestructura como código y pipelines (`karvey-infra`), y scripts de despliegue (`karvey-deploy`).

## Ubicación

- `CHANGELOG.md` en la raíz de **cada repo** que recibió cambios de código (`project.json:repos`).
- Si el repo ya tiene un mecanismo de versionado (ver `karvey-impl`: `package.json`, `pyproject.toml`, `VERSION`, git tags), la entrada del CHANGELOG se alinea con esa versión.

## Formato de entrada (obligatorio)

Estilo *Keep a Changelog* + bloque de trazabilidad:

```markdown
## [{version}] - {YYYY-MM-DD}

### {Added | Changed | Fixed | Removed}
- {Qué cambió y **por qué** — descripción funcional} ({change-id})

> 👤 Humano responsable: {Nombre Apellido} <{email}>
> 🤖 Asistido por IA: {modelo, ej. Claude Opus 4.8}
> 🔗 Cambio: {change-id} · Fase Karvey: impl | infra | deploy
```

### Campos
- **version**: versión del proyecto tras el bump.
- **fecha**: fecha local (Chile, CLT/CLST) del cambio.
- **qué + por qué**: una línea por cambio relevante; el "por qué" es obligatorio, no solo el "qué".
- **Humano responsable**: la persona que dirige el trabajo. Obtener de, en orden de preferencia:
  1. `git config user.name` / `git config user.email` del repo.
  2. El usuario de la sesión, si git no está configurado.
  El humano **nunca** puede quedar vacío ni reemplazado por "IA".
- **Asistido por IA**: nombre del modelo en uso (ej. `Claude Opus 4.8`). Deja claro que hubo asistencia de IA, sin ocultar al humano.

## Relación con commits

Coherente con la convención de commits del proyecto. Cuando el proyecto use `Co-Authored-By`, el commit incluye la línea de co-autoría de IA, pero el **autor del commit es el humano**. La entrada de CHANGELOG y el commit deben contar la misma historia (quién/cuándo/por qué).

## Verificación (gate)

`karvey-qa` (Dimensión 6 — Versionamiento) verifica para cada repo con cambios:
- [ ] `CHANGELOG.md` tiene entrada para la versión actual.
- [ ] La entrada incluye **humano responsable** (nombre + contacto) y **modelo de IA**.
- [ ] Incluye el "por qué", no solo el "qué".
- [ ] Versión del CHANGELOG coincide con el archivo de versión del proyecto.

Si falta cualquiera de estos, es hallazgo de versionamiento y bloquea el avance a deploy junto con el resto del gate.
