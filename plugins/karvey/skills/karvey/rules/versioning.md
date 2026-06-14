# Regla: Versionado semántico y changelog en despliegue

Define cómo Karvey versiona y documenta cada cambio. La aplican `karvey-impl` (durante el desarrollo) y `karvey-deploy` (FASE 11), y la verifica `karvey-qa` (Dimensión 6). Complementa `changelog-policy.md`.

## Versionado semántico — `major.minor.rev`

Cada componente desplegable lleva versión **`major.minor.rev`** (semver):

| Segmento | Cuándo se incrementa |
|----------|----------------------|
| **major** | Breaking change: rompe compatibilidad (API, contrato, esquema, comportamiento). |
| **minor** | Feature nueva compatible hacia atrás. |
| **rev** | Fix, ajuste o cambio menor sin nueva feature. |

**Regla dura:** **NUNCA se despliega sin incrementar la versión.** Todo cambio que llega a deploy sube al menos `rev`. La versión se incrementa **cada vez**, no se reutiliza.

El archivo de versión depende del stack (detectarlo): `package.json`, `pyproject.toml`, `*.csproj`, `VERSION`, git tags, etc.

## Changelog por componente Y por repositorio

- **Por repositorio:** cada repo de `project.json:repos` con cambios lleva su propio `CHANGELOG.md`.
- **Por componente:** si un repo contiene varios componentes desplegables (p. ej. múltiples Azure Functions, microservicios, paquetes), cada componente lleva su entrada/sección de changelog con su propia versión.

Cada entrada sigue el formato de `changelog-policy.md` (humano responsable + modelo de IA + el **por qué**, no solo el qué) e indica el segmento semver que se incrementó y por qué.

## Versión visible en el frontend (recomendación)

Si el proyecto tiene **frontend**, se **recomienda exponer la versión en la UI** (footer, pantalla "Acerca de", o similar) para trazabilidad visible en producción:
- Inyectar la versión en build (ej. `VITE_APP_VERSION`, variable de entorno, o lectura del archivo de versión).
- Mostrarla en un lugar discreto pero accesible.

`karvey-deploy` debe **recomendar esto al usuario** cuando detecte que el proyecto tiene capa frontend y la versión no esté visible.

## En el paso a paso de despliegue (`karvey-deploy`)

Antes del push a la rama de integración (parte del checklist de 6 pasos):
1. Determinar el segmento a incrementar (major/minor/rev) según la naturaleza del cambio.
2. Bump de versión en cada componente/repo afectado.
3. Documentar los cambios: actualizar `CHANGELOG.md` por componente y por repo.
4. (Si hay front) verificar/recomendar versión visible en la UI.
