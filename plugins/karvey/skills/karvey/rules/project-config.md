# Rule: Project configuration (`project.json`)

The Karvey Method operates at two levels: **project** (stable config, shared by all changes) and **change** (`spec.json` per change-id). This rule defines the project-level config.

## Location

```
docs/spec/project.json
```

`docs/spec/` lives in the project's **main repo** (`spec_repo`). A project has **1 or more repos, never zero**. If there is a single repo, that one is the `spec_repo`. If there are several, the main/orchestrator repo is designated.

## Schema

Machine-readable contract: `${CLAUDE_PLUGIN_ROOT}/schemas/project.schema.json` (validated by
`karvey-state.py validate`; values used in commands are read with `karvey-config.py get <key> --shell`).

```json
{
  "project": "{project name}",
  "git_platform": "github | azure_devops | gitlab",
  "cloud": {
    "provider": "azure | gcp | aws | mixed | none"
  },
  "iac_tool": "terraform | bicep | pulumi | none",
  "knowledge_sync": "none | graphify | obsidian",
  "targets": ["web", "ios", "android", "desktop", "cli", "api", "embedded"],
  "repos": ["path/or/name/repo1", "path/or/name/repo2"],
  "spec_repo": "main-repo-where-docs-spec-lives",
  "branch_flow": {
    "feature_prefix": "feature/",
    "integration": "dev",
    "production": "master",
    "protected_branches": ["release/*"]
  },
  "standards": {
    "source": "git",
    "dir": "docs/spec/standards",
    "repo": "https://dev.azure.com/{org}/{project}/_git/{standards-repo}",
    "ref": "main",
    "path": "standards",
    "by_layer": { "db": "db.md", "backend": "backend.md", "frontend": "frontend.md" }
  },
  "enforcement": {
    "git_flow_hook": false,
    "plan_gate_hook": false,
    "prod_gate_hook": true,
    "plan_marker_ttl_min": 120,
    "approval_vocabulary": { "approve": ["dale"], "negate": ["todavía no"], "prod_terms": ["a prod"] }
  },
  "notifications": {
    "channel": "google-chat | slack | teams | email | webhook | none",
    "target": "{space / #channel / list / name of the secret holding the webhook}",
    "via": "mcp | cli | webhook | api",
    "events": ["qa", "deploy"],
    "detail": "counts",
    "deferred": false
  },
  "management": {
    "tool": "clickup | jira | linear | azure-boards | github-projects | spreadsheet | markdown | other",
    "location": "{list id | project key | team | spreadsheet path}",
    "statuses": { "todo": "", "in_progress": "", "review": "", "done": "", "blocked": null },
    "sprints": "{optional folder, iteration or cycle}",
    "hierarchy": "epic>feature>task",
    "via": "mcp | cli | api | file"
  },
  "wip_limit": 3,
  "stall_days": 7,
  "calibration": { "threshold_pct": 30, "window": 3 },
  "schema_mode": "advisory",
  "ops_repo": "repo-with-the-decision-log-and-parent-changes",
  "karvey_version": "3.12.0",
  "docs_pr": { "ci": "spec-lint", "merged_by": "{name or role}" }
}
```

## Handling rules

- **`repos`**: mandatory array with **at least 1** entry. Validate on create/read; if it comes in empty, stop and ask for at least one repo.
- **`spec_repo`**: if `repos` has 1 element, `spec_repo` = that repo. If it has several, ask which one is the main one.
- **`git_platform`**: determines which pipelines `karvey-infra` generates (GitHub Actions vs Azure Pipelines) **and which CLI `karvey-deploy` uses to open, verify and merge the PR** (`gh pr` vs `az repos pr` vs `glab mr`) — they are not interchangeable. If a repo's remote contradicts it, the remote wins and the config is stale.
- **`cloud.provider`**: `mixed` means services from more than one cloud are used; the detail of which service from which cloud is specified in the "Cloud Infrastructure" section of `architecture.md` for each change.
- **`iac_tool`**: `none` means infra is managed manually; `karvey-infra` still generates/validates the CI/CD pipelines.
- **`knowledge_sync`**: `none` (the default when no graphify/Obsidian is detected) or the tool; it runs at archive and on demand only — see `knowledge-sync.md`.
- **`targets`**: the project's platforms (at least 1). Defines how each phase verifies/designs. See `targets.md`. Stack-agnostic: never assume `web` by default.
- **`branch_flow`**: branch convention; respected by `karvey-impl`, `karvey-qa` and `karvey-deploy`. Default: `feature/*` → `dev` → `master`. `protected_branches` (optional, globs) lists long-lived branches besides `integration`/`production` that the branch-hygiene cleanup never deletes (see `deploy-workflow.md` → *Branch hygiene*).
- **`standards`**: engineering golden paths per layer (see `engineering-standards.md`). Two source modes:
  - `source: "local"` → standards live in `dir` inside the `spec_repo` (single-repo / simplest case).
  - `source: "git"` → standards live in a **separate, team-owned repo** (e.g. a private Azure DevOps repo) given by `repo` + `ref` + `path`. Phases resolve it by cloning/pulling a shallow working copy into a cache (`.karvey/standards/`) and reading from there. This keeps the **method** (public plugin) and the **standards** (org's private data) decoupled and independently installable/versioned.
  - `by_layer` maps a layer to its standard file. Loaded as a **hard constraint** by `karvey-architecture` and `karvey-impl`; populated/refreshed by `karvey-standards`. The standards repo is **never** the public plugin repo. Optional but recommended; if absent, those phases fall back to `standards/_index.md` and, failing that, treat non-trivial pattern choices as gray zones to ask (never silently picked).
- **`ops_repo`** (optional, multi-agent/multi-repo): the repo that holds the business decision log (`D-NN`) and the **parent** changes. Defaults to `spec_repo`. See `multi-agent.md`.
- **`karvey_version`** (optional): the Karvey version the project expects every agent environment to have installed; checked by `karvey-health` (method readiness).
- **`docs_pr`** (optional): the documentation-only PR lane — `ci` is the light job that runs (spec lint) and `merged_by` who merges them. See `multi-agent.md` §8.
- **`notifications`** (team setting, asked by `karvey-init` on first use or with `--settings`): the team's channel for QA/deploy notices. `none` is valid; `deferred: true` records a "not now"; `detail` is `counts` (default) or `full`. A `target` with `://` is refused — reference the secret. See `notifications.md`.
- **`management`** (team setting, same moment): the team's tracker (`tool`, `location`, `via`, optional `sprints`) and its **status flow mapped to the 5 logical states**, flat or per level/list, `null` for a state the tool cannot represent. Resolution order, the missing-map clause and `none` (alias of `markdown`): `management-adapters.md`.
- **`enforcement`**: switches of the hooks in `enforcement.md`, managed by `karvey-guard`. `git_flow_hook`, `plan_gate_hook` default `false` (opt-in); `prod_gate_hook` defaults to `true` (D-02) and is off only when `false` in the working copy **and** on `origin/{production}`. `plan_marker_ttl_min` (5..1440, default 120) and `approval_vocabulary` tune the approval hook.
- **`wip_limit`**, **`stall_days`** (default 7), **`calibration`** (`threshold_pct` 30, `window` 3): read by `karvey-context.py` (open work, stalled items, estimate calibration). Defaults live in `karvey_lib/defaults.json`.
- **`schema_mode`**: `advisory` (default: legacy shapes are warnings) or `strict` (they are errors).
- Settings are persisted on a feature or docs branch and take effect after merge; subagents never write this file.

> **Note — `goal`**: the change's goal does NOT live in `project.json` but per change, in `prd.md` and in `spec.json` (`"goal"`). It sets the direction to pursue the outcome without stopping, while respecting the plan and security gates.

## Who creates / reads it

- **Creates**: `karvey-init` (first time in the project). Pre-populated from the `karvey-grill` synthesis if it exists.
- **Reads**: all phases. In particular `karvey-architecture` (cloud, **standards**), `karvey-impl` (**standards**, branch_flow), `karvey-infra` (git_platform, cloud, iac_tool, repos), `karvey-deploy` (branch_flow, repos, git_platform), and `karvey-archive`, which runs the knowledge sync (`knowledge_sync`).

If a phase needs `project.json` and it does not exist, stop and indicate to run `karvey-init` first.
