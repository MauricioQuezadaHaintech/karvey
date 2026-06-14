# Regla: Agnosticismo de stack (targets / plataformas)

Karvey es **agnóstico de stack**: sirve para cualquier plataforma. El proyecto declara sus **targets** en `docs/spec/project.json` y cada fase se adapta a ellos. Esto generaliza capacidades que en otros métodos están atadas a un stack (p. ej. la suite iOS de gstack), llevándolas a "el runtime real del target".

## Campo `targets` en project.json

```json
"targets": ["web", "ios", "android", "desktop", "cli", "api", "embedded"]
```

Valores típicos (no exhaustivo): `web`, `ios`, `android`, `desktop`, `cli`, `api`/`backend`, `embedded`, `library`/`sdk`, `game`, `data`/`ml`. Un proyecto puede tener varios.

## Cómo se adapta cada fase al target

| Fase | Adaptación según target |
|------|--------------------------|
| `mockup` (3) | Web → HTML navegable; mobile → flujo de pantallas; CLI → transcript de comandos; API → ejemplos request/response. |
| `design-graphic` (4) | Guía de diseño por plataforma: **WCAG** (web), **Apple HIG** (iOS), **Material** (Android), convenciones de escritorio/terminal. |
| `architecture` (5) | Infra y boundaries propios del target (app stores, dispositivos, edge, runtime embebido, etc.). |
| `test` (9) | **Runtime real del target**: browser (web), simulador/dispositivo (iOS/Android), terminal (CLI), cliente HTTP (API), hardware/emulador (embedded). |
| `qa` (10) | Auditoría visual y de UX en el runtime real; checklist de la plataforma (HIG/Material/WCAG). |
| `deploy` (11) | Canal de release del target: pipeline web, App Store/TestFlight, Play Store, package registry, OTA, etc. |

## Skills de apoyo y targets

- **`karvey-browse`** ("dar ojos") opera sobre el runtime real del target: browser headless (web), simulador/dispositivo vía túnel (mobile), proceso/terminal (CLI). No asume navegador.
- **`karvey-devex`** mide onboarding/time-to-hello-world del target correspondiente.

## Principio

Ninguna fase asume "web" por defecto. Si una capacidad existe para un target (ej. auditoría HIG en iPhone real), debe existir el equivalente para los demás targets declarados. El método describe el **qué** (verificar en el runtime real, auditar contra la guía de la plataforma); el **cómo** lo resuelve la skill según el target.
