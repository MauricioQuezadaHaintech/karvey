# Rule: Hook-based enforcement (git-flow + plan-gate)

A skill is **guidance** that the model follows voluntarily — it guarantees nothing. To **force** behavior deterministically, harness **hooks** (`PreToolUse`) are used, which do block. Karvey **provides and installs (opt-in)** two hooks that close the two most common holes:

1. **git-flow** — prevents skipping the flow (direct push to master, commit on dev/master).
2. **plan-gate** — prevents changes without an approved plan.

## Installation (opt-in per project)

- `karvey-init` asks whether to activate enforcement. If yes, it writes the hooks into the project's `settings.json` (or the corresponding `.claude/settings.json`), parameterized with `project.json:branch_flow`.
- `karvey-guard` manages them afterward: **install**, **disable**, or grant a temporary **override**.
- The templates live in `../hooks/` (`git-flow-guard.sh`, `plan-gate.sh`).

## Hook 1 — git-flow-guard (PreToolUse on Bash)

Intercepts `git` commands:
- **Blocks** `git push` directly to the production branch (`branch_flow.production`, default `master`) and to the integration branch when it does not come from a flow merge.
- **Blocks** `git commit` when the current branch is `dev`/`master` (it must be `feature/*`).
- **Blocks** manual deploy (`func azure functionapp publish` and equivalents) — the deploy is done by CI/CD.
- Permitted flow: `feature/* → dev → PR → master`. See `deploy-workflow.md`.

## Hook 2 — plan-gate (PreToolUse on destructive Edit/Write/Bash)

- **Requires an approved plan throughout the whole flow**: any `Edit`, `Write` or destructive command is blocked if the approval marker does not exist.
- **Override**: the user approves the plan and the marker is created (`touch <flag>` pattern); the hook lets things through until it is consumed/expires.
- Clear block message indicating that the plan still needs to be presented and approved.

## Override and reversion

- **One-off override**: create the approval marker (defined in the hook) after presenting the plan.
- **Disable**: `karvey-guard --disable-hooks` removes the hooks from the project's `settings.json`.
- The hooks are **reversible** and **per-project**; they are never imposed globally without the user deciding so.

## Relationship with gstack guardrails

It absorbs the value of `/careful`, `/freeze`, `/guard`: `karvey-guard` also offers an **edit-lock on a directory** (blocks Edit/Write outside a boundary) for sensitive work or debugging.

## Note — approval delegation and marker expiry (outside the method)

Some users run their **own** plan-gate hook with an approval marker that **expires** (e.g. valid for 2 h) and that agents are not allowed to renew. That hook is part of the user's environment, not of Karvey, and Karvey does not define it. In multi-agent work the user should decide, in their own hook/config, (a) how the human delegates phase approvals to a coordinating agent (a "CEO" agent) and (b) how a marker's validity is extended. Karvey only records the outcome: `approvals.<phase>.by` / `role` / `ref: D-NN` (see `multi-agent.md` §4). The production gate is never delegated to an agent.
