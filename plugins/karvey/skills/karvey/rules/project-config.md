# Rule: Project configuration (`project.json`)

The Karvey Method operates at two levels: **project** (stable config, shared by all changes) and **change** (`spec.json` per change-id). This rule defines the project-level config.

## Location

```
docs/spec/project.json
```

`docs/spec/` lives in the project's **main repo** (`spec_repo`). A project has **1 or more repos, never zero**. If there is a single repo, that one is the `spec_repo`. If there are several, the main/orchestrator repo is designated.

## Schema

```json
{
  "project": "{project name}",
  "git_platform": "github | azure_devops",
  "cloud": {
    "provider": "azure | gcp | aws | mixed | none"
  },
  "iac_tool": "terraform | bicep | pulumi | none",
  "knowledge_sync": "obsidian | graphify",
  "targets": ["web", "ios", "android", "desktop", "cli", "api", "embedded"],
  "repos": ["path/or/name/repo1", "path/or/name/repo2"],
  "spec_repo": "main-repo-where-docs-spec-lives",
  "branch_flow": {
    "feature_prefix": "feature/",
    "integration": "dev",
    "production": "master"
  },
  "enforcement": {
    "git_flow_hook": false,
    "plan_gate_hook": false
  }
}
```

## Handling rules

- **`repos`**: mandatory array with **at least 1** entry. Validate on create/read; if it comes in empty, stop and ask for at least one repo.
- **`spec_repo`**: if `repos` has 1 element, `spec_repo` = that repo. If it has several, ask which one is the main one.
- **`git_platform`**: determines which pipelines `karvey-infra` generates (GitHub Actions vs Azure Pipelines).
- **`cloud.provider`**: `mixed` means services from more than one cloud are used; the detail of which service from which cloud is specified in the "Cloud Infrastructure" section of `architecture.md` for each change.
- **`iac_tool`**: `none` means infra is managed manually; `karvey-infra` still generates/validates the CI/CD pipelines.
- **`knowledge_sync`**: see `knowledge-sync.md`.
- **`targets`**: the project's platforms (at least 1). Defines how each phase verifies/designs. See `targets.md`. Stack-agnostic: never assume `web` by default.
- **`branch_flow`**: branch convention; respected by `karvey-impl`, `karvey-qa` and `karvey-deploy`. Default: `feature/*` → `dev` → `master`.
- **`enforcement`**: opt-in activation of the hooks in `enforcement.md`. `karvey-init` asks and `karvey-guard` manages them. Default both `false`.

> **Note — `goal`**: the change's goal does NOT live in `project.json` but per change, in `prd.md` and in `spec.json` (`"goal"`). It sets the direction to pursue the outcome without stopping, while respecting the plan and security gates.

## Who creates / reads it

- **Creates**: `karvey-init` (first time in the project). Pre-populated from the `karvey-grill` synthesis if it exists.
- **Reads**: all phases. In particular `karvey-architecture` (cloud), `karvey-infra` (git_platform, cloud, iac_tool, repos), `karvey-deploy` (branch_flow, repos), and any phase that syncs knowledge (`knowledge_sync`).

If a phase needs `project.json` and it does not exist, stop and indicate to run `karvey-init` first.
