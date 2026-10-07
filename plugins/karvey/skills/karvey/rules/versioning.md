# Rule: Semantic versioning and changelog on deployment

Defines how Karvey versions and documents each change. It is applied by `karvey-impl` (during development) and `karvey-deploy` (PHASE 11), and verified by `karvey-qa` (Dimension 6). Complements `changelog-policy.md`.

## Semantic versioning — `major.minor.rev`

Each deployable component carries a **`major.minor.rev`** (semver) version:

| Segment | When it is incremented |
|----------|----------------------|
| **major** | Breaking change: breaks compatibility (API, contract, schema, behavior). |
| **minor** | New backward-compatible feature. |
| **rev** | Fix, adjustment or minor change without a new feature. |

**Hard rule:** **each release increments the version, once.** During implementation every commit adds its
line under `## [Unreleased]` in `CHANGELOG.md` and never touches the version; the release step
(`karvey-deploy`) turns `[Unreleased]` into `[x.y.z]` and bumps the version files in the same commit. A
version is never reused and never deployed unbumped.

The version file depends on the stack (detect it): `package.json`, `pyproject.toml`, `*.csproj`, `VERSION`, git tags, etc.

## Changelog per component AND per repository

- **Per repository:** each repo of `project.json:repos` with changes carries its own `CHANGELOG.md`.
- **Per component:** if a repo contains several deployable components (e.g. multiple Azure Functions, microservices, packages), each component carries its changelog entry/section with its own version.

Each entry follows the format of `changelog-policy.md` (human owner + AI model + the **why**, not just the what) and indicates the semver segment that was incremented and why.

## Version visible in the frontend (recommendation) — DEV shows the dev version, PROD the release

If the project has a **frontend** (any `target` with a UI), it is **recommended to expose the version in the UI** (footer, "About" screen, or similar), **differentiated by environment**, so anyone looking at a screen knows which build they are on:

| Environment | What the UI shows | Example |
|---|---|---|
| **DEV** (`integration` branch) | the **dev version**: the bumped version as a semver pre-release + build metadata, and a visible environment mark | `v3.10.1-dev.42+74571ae` · `DEV` badge |
| **PROD** (`production` branch) | the **release version**, clean | `v3.10.1` (commit only in a tooltip / About screen, if wanted) |

How to build it:
- **The version comes from the version file** (`package.json`, `pyproject.toml`, `*.csproj`, `VERSION`…) read at build time — **never from a pipeline variable**, which silently stays stuck on an old value while the code moves on (the label lies, the code does not). E.g. Vite: `define: { 'import.meta.env.VITE_APP_VERSION': JSON.stringify(pkg.version) }`.
- **The environment and the build identity come from the pipeline:** the stage sets `APP_ENV` (`dev` | `prod`), the CI provides the build number and the short commit (`git rev-parse --short HEAD`). The code composes: `APP_ENV === 'prod' ? version : `${version}-dev.${build}+${sha}``.
- Discreet but accessible place; the DEV mark must be impossible to confuse with production.

`karvey-deploy` must **recommend this to the user** when it detects a frontend layer whose version is not visible or not differentiated by environment, and its canary **checks the visible version** (see `karvey-deploy` 2.6 / 2.10): DEV shows the version in the version file **of the deployed commit** (`git show <deployed-sha>:<version file>`, never the tip of the integration branch, where a later change may already have bumped it) with an unmistakable DEV mark, in any format — the `-dev.{build}+{sha}` form above is the recommendation, not the test; PROD shows exactly the released version. A mismatch is a finding (stale build, wrong stage variable, or a version read from the wrong source); a UI with no visible version is a recommendation, not a finding.

## In the step-by-step deployment (`karvey-deploy`)

At the release step, before the first push (part of the 6-step checklist of `deploy-workflow.md`):
1. Determine the segment (major/minor/rev) from the `[Unreleased]` lines.
2. Bump the version once in each affected component/repo.
3. Rename `## [Unreleased]` to `## [x.y.z] - date`, with its **Why** (`changelog-policy.md`).
4. (If there is a front) verify/recommend a visible version in the UI — dev version in DEV, release version in PROD — and check it in the canary.
5. (A release of the Karvey plugin itself) if its upgrade surface changed — lint check L-37 warns during `[Unreleased]` — add a project-upgrade step whose `since` is this release **or** a `- No project upgrade needed: <reason>` line in the release entry, then refresh the fingerprint with `karvey-upgrade.py surface --write`.

## QA items (`karvey-qa` Dimension 6)

QA verifies each item by its key:

- `unreleased-section` — every commit of the change has its line under `## [Unreleased]`. <!-- qa-item: unreleased-section -->
- `one-bump-per-release` — no commit of the change bumps a version file outside the release step. <!-- qa-item: one-bump-per-release -->
- `versions-agree` — the version files, the plugin/package manifests and the top CHANGELOG release agree. <!-- qa-item: versions-agree -->
- `changelog-why` — each entry says why, with the human owner and the AI model. <!-- qa-item: changelog-why -->
