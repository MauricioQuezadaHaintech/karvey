# Rule: Stack agnosticism (targets / platforms)

Karvey is **stack-agnostic**: it works for any platform. The project declares its **targets** in `docs/spec/project.json` and each phase adapts to them. This generalizes capabilities that in other methods are tied to a stack (e.g. gstack's iOS suite), bringing them to "the target's real runtime".

## `targets` field in project.json

```json
"targets": ["web", "ios", "android", "desktop", "cli", "api", "embedded"]
```

Typical values (not exhaustive): `web`, `ios`, `android`, `desktop`, `cli`, `api`/`backend`, `embedded`, `library`/`sdk`, `game`, `data`/`ml`. A project can have several.

## How each phase adapts to the target

| Phase | Adaptation by target |
|------|--------------------------|
| `mockup` (3) | Web → navigable HTML; mobile → screen flow; CLI → command transcript; API → request/response examples. |
| `design-graphic` (4) | Per-platform design guide: **WCAG** (web), **Apple HIG** (iOS), **Material** (Android), desktop/terminal conventions. |
| `architecture` (5) | Infra and boundaries specific to the target (app stores, devices, edge, embedded runtime, etc.). |
| `test` (9) | **Target's real runtime**: browser (web), simulator/device (iOS/Android), terminal (CLI), HTTP client (API), hardware/emulator (embedded). |
| `qa` (10) | Visual and UX audit in the real runtime; platform checklist (HIG/Material/WCAG). |
| `deploy` (11) | The target's release channel: web pipeline, App Store/TestFlight, Play Store, package registry, OTA, etc. |

## Support skills and targets

- **`karvey-browse`** ("give eyes") operates on the target's real runtime: headless browser (web), simulator/device via tunnel (mobile), process/terminal (CLI). It does not assume a browser.
- **`karvey-devex`** measures onboarding/time-to-hello-world of the corresponding target.

## Principle

No phase assumes "web" by default. If a capability exists for one target (e.g. HIG audit on a real iPhone), the equivalent must exist for the other declared targets. The method describes the **what** (verify in the real runtime, audit against the platform guide); the **how** is solved by the skill according to the target.
