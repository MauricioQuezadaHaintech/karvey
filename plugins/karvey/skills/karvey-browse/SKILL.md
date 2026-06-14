---
name: karvey-browse
description: Give the agent eyes in the target's real runtime for the Karvey method. Real browser (web), simulator/device (mobile), terminal (CLI) — click, screenshot, inspect. Imports session cookies for authenticated views. Triggers include "karvey browse", "dar ojos", "navegador real", "screenshot", "inspeccionar UI", "abrir la app".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [url or target] [--target web|ios|android|cli]
---

# karvey-browse — Give the agent eyes

## Purpose

A **cross-cutting** skill of the Karvey Method: a **support layer, NOT a phase**. It does not advance the method nor change `spec.json:phase`. It can be invoked from any phase when the agent needs to **see with its own eyes** what is happening in the target's real runtime.

Its role is simple: **give it eyes**. The agent stops reasoning blindly about the code and starts observing the real behavior — open, click, screenshot and inspect state. Inspired by `gstack /browse` + `/setup-browser-cookies`.

### Stack-agnostic

It operates on the real runtime of the target declared in `project.json:targets` (see `karvey/rules/targets.md`). It does not assume a fixed stack:

| Target | Real runtime | How it is observed |
|--------|--------------|-----------------|
| `web` | Headless browser (e.g. Playwright) | navigate, click, screenshot, read DOM/console |
| `ios` / `android` | Simulator / device | open the app, interact, screenshot, read logs |
| `cli` | Process / terminal | run, capture stdout/stderr, inspect state |
| `api` | HTTP client | send requests, capture responses and headers |

### Capabilities

- **Navigate / open** the target in its real runtime.
- **Click / interact** (forms, buttons, gestures depending on the target).
- **Capture screenshots** as visual evidence.
- **Read state / console** (DOM, logs, process output, responses).

### Session handling (web target)

When the target is web, it can **import cookies/session from a real browser** to test authenticated views without manual re-login. This makes it possible to inspect screens behind login using the user's already-active session.

## Steps

1. **Determine the target.** Read `project.json:targets` (and `karvey/rules/targets.md`). If the user passed `--target`, use that; if not, infer it from the destination or from the project's main target.
2. **Bring up the corresponding runtime.** Headless browser for web, simulator/device for mobile, process/terminal for CLI, HTTP client for API. If it is authenticated web, import the real browser's cookies/session before navigating.
3. **Execute the requested actions.** Navigate/open, click/interact, capture and read state as requested.
4. **Return evidence.** Screenshots, DOM/state, console logs or process output — everything that backs up what was observed.

## Reminders

- **Close the runtime/browser when finished.** Do not leave processes or browsers hanging.
- **It does not advance the phase.** This skill is cross-cutting support; it never modifies `spec.json:phase` nor makes method transitions.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
