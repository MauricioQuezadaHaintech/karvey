---
name: karvey-browse
description: Give the agent eyes in the target's real runtime for the Karvey method. Real browser (web), simulator/device (mobile), terminal (CLI) — click, screenshot, inspect. Imports session cookies for authenticated views. Triggers include "karvey browse", "dar ojos", "navegador real", "screenshot", "inspeccionar UI", "abrir la app".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [url o destino] [--target web|ios|android|cli]
---

# karvey-browse — Dar ojos al agente

## Propósito

Skill **transversal** del Método Karvey: una **capa de apoyo, NO una fase**. No avanza el método ni cambia `spec.json:phase`. Se puede invocar desde cualquier fase cuando el agente necesita **ver con sus propios ojos** lo que pasa en el runtime real del target.

Su rol es simple: **dar ojos**. El agente deja de razonar a ciegas sobre el código y pasa a observar el comportamiento real — abrir, clickear, capturar pantalla e inspeccionar estado. Inspirado en `gstack /browse` + `/setup-browser-cookies`.

### Agnóstico de stack

Opera sobre el runtime real del target declarado en `project.json:targets` (ver `karvey/rules/targets.md`). No asume un stack fijo:

| Target | Runtime real | Cómo se observa |
|--------|--------------|-----------------|
| `web` | Navegador headless (ej. Playwright) | navegar, clickear, screenshot, leer DOM/consola |
| `ios` / `android` | Simulador / dispositivo | abrir la app, interactuar, capturar pantalla, leer logs |
| `cli` | Proceso / terminal | ejecutar, capturar stdout/stderr, inspeccionar estado |
| `api` | Cliente HTTP | enviar requests, capturar respuestas y headers |

### Capacidades

- **Navegar / abrir** el target en su runtime real.
- **Clickear / interactuar** (formularios, botones, gestos según target).
- **Capturar screenshots** como evidencia visual.
- **Leer estado / consola** (DOM, logs, salida de proceso, respuestas).

### Manejo de sesión (target web)

Cuando el target es web, puede **importar cookies/sesión desde un navegador real** para probar vistas autenticadas sin re-login manual. Esto permite inspeccionar pantallas detrás de login usando la sesión ya activa del usuario.

## Pasos

1. **Determinar el target.** Leer `project.json:targets` (y `karvey/rules/targets.md`). Si el usuario pasó `--target`, usar ese; si no, inferir del destino o del target principal del proyecto.
2. **Levantar el runtime correspondiente.** Browser headless para web, simulador/dispositivo para mobile, proceso/terminal para CLI, cliente HTTP para API. Si es web autenticado, importar las cookies/sesión del navegador real antes de navegar.
3. **Ejecutar las acciones pedidas.** Navegar/abrir, clickear/interactuar, capturar y leer estado según lo solicitado.
4. **Devolver evidencia.** Screenshots, DOM/estado, logs de consola o salida del proceso — todo lo que respalde lo observado.

## Recordatorios

- **Cerrar el runtime/navegador al terminar.** No dejar procesos ni navegadores colgando.
- **No avanza la fase.** Esta skill es apoyo transversal; nunca modifica `spec.json:phase` ni hace transiciones del método.

---
*Parte del Método Karvey™ — © HainTech, por Mauricio Quezada Ibáñez · Apache 2.0 · ver `karvey/LICENSE` y `karvey/TRADEMARK.md`.*
