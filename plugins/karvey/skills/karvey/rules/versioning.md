# Rule: Semantic versioning and changelog on deployment

Defines how Karvey versions and documents each change. It is applied by `karvey-impl` (during development) and `karvey-deploy` (PHASE 11), and verified by `karvey-qa` (Dimension 6). Complements `changelog-policy.md`.

## Semantic versioning — `major.minor.rev`

Each deployable component carries a **`major.minor.rev`** (semver) version:

| Segment | When it is incremented |
|----------|----------------------|
| **major** | Breaking change: breaks compatibility (API, contract, schema, behavior). |
| **minor** | New backward-compatible feature. |
| **rev** | Fix, adjustment or minor change without a new feature. |

**Hard rule:** **NEVER deploy without incrementing the version.** Every change that reaches deploy bumps at least `rev`. The version is incremented **every time**, it is not reused.

The version file depends on the stack (detect it): `package.json`, `pyproject.toml`, `*.csproj`, `VERSION`, git tags, etc.

## Changelog per component AND per repository

- **Per repository:** each repo of `project.json:repos` with changes carries its own `CHANGELOG.md`.
- **Per component:** if a repo contains several deployable components (e.g. multiple Azure Functions, microservices, packages), each component carries its changelog entry/section with its own version.

Each entry follows the format of `changelog-policy.md` (human owner + AI model + the **why**, not just the what) and indicates the semver segment that was incremented and why.

## Version visible in the frontend (recommendation)

If the project has a **frontend**, it is **recommended to expose the version in the UI** (footer, "About" screen, or similar) for visible traceability in production:
- Inject the version at build time (e.g. `VITE_APP_VERSION`, environment variable, or reading the version file).
- Show it in a discreet but accessible place.

`karvey-deploy` must **recommend this to the user** when it detects that the project has a frontend layer and the version is not visible.

## In the step-by-step deployment (`karvey-deploy`)

Before the push to the integration branch (part of the 6-step checklist):
1. Determine the segment to increment (major/minor/rev) according to the nature of the change.
2. Bump the version in each affected component/repo.
3. Document the changes: update `CHANGELOG.md` per component and per repo.
4. (If there is a front) verify/recommend a visible version in the UI.
