---
name: karvey-guard
description: Safety guardrails for the Karvey method. Installs/disables the opt-in enforcement hooks (git-flow + plan-gate), grants temporary override, and can edit-lock work to a single directory. Triggers include "karvey guard", "guardrails", "freeze", "edit lock", "activar hooks", "enable hooks", "bloquear cambios", "lock changes", "candado", "lock".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [--install | --disable-hooks | --freeze <dir> | --unfreeze | --override]
---

# Karvey Guard

## Purpose

A **cross-cutting support layer** of the Karvey Method — NOT a pipeline phase. It provides the method's **guardrails**: it manages the enforcement hooks (which do block deterministically via `PreToolUse`), grants temporary override of the plan-gate, and can apply an **edit-lock** that restricts `Edit`/`Write` to a single directory.

Inspired by gstack's `/careful` + `/freeze` + `/guard`, absorbed as a single skill integrated into the method.

**Hard rules:**
- It is a **cross-cutting** skill, not a phase: **it does NOT change `spec.json:phase`** or the change's state.
- The hooks are **OPT-IN per project**, reversible. They are **never** imposed globally without the user deciding so.
- Aligned with `karvey/rules/enforcement.md` (the canonical rule) and `karvey/rules/project-config.md`.

It manages the two hooks defined in `karvey/rules/enforcement.md`, whose templates live in `karvey/hooks/`:

- **git-flow-guard** (`git-flow-guard.sh`) — `PreToolUse` over `Bash`. Blocks direct push to production, commits on `dev`/`master`, and manual deploy. Allowed flow: `feature/* → integration → PR → production`.
- **plan-gate** (`plan-gate.sh`) — `PreToolUse` over `Edit`/`Write`/destructive `Bash`. Requires an approved plan (the `KARVEY_PLAN_FLAG` marker, default `/tmp/claude-plan-approved`) throughout the flow.

## Execution steps

ALWAYS read `karvey/rules/enforcement.md` first to align before touching anything.

Resolve the mode from `$ARGUMENTS`. If no argument is provided, show the current state (which hooks are registered in `settings.json`, whether a freeze is active, whether the approval marker exists) and offer the options.

### `--install` — Enable the enforcement hooks

1. **Locate the project config.** Read `docs/spec/project.json` (schema in `karvey/rules/project-config.md`). If it doesn't exist, stop and indicate that `karvey-init` should be run first. Take `branch_flow` (`feature_prefix`, `integration`, `production`) to parameterize.
2. **Copy the templates** from `karvey/hooks/` to the project's hooks location (e.g., `.claude/hooks/git-flow-guard.sh` and `.claude/hooks/plan-gate.sh`). Keep them executable (`chmod +x`).
3. **Register them in the project's `settings.json`** (`.claude/settings.json`) as `PreToolUse` hooks:
   - `git-flow-guard` with a matcher over `Bash`.
   - `plan-gate` with a matcher over `Edit`, `Write`, `NotebookEdit`, and `Bash`.
   - Pass the parameterization via the hook command's env, reading `branch_flow`: `KARVEY_BRANCH_INTEGRATION`, `KARVEY_BRANCH_PRODUCTION`, `KARVEY_FEATURE_PREFIX`, and optionally `KARVEY_PLAN_FLAG`.
4. **Mark `enforcement` in `project.json`**: set `enforcement.git_flow_hook: true` and `enforcement.plan_gate_hook: true`.
5. Confirm to the user what was installed and remind them it is reversible with `--disable-hooks`.

### `--disable-hooks` — Disable (reversible)

1. Remove the `git-flow-guard` and `plan-gate` entries from the `PreToolUse` section of the project's `settings.json`.
2. Set `enforcement.git_flow_hook: false` and `enforcement.plan_gate_hook: false` in `project.json`.
3. Leave the templates in `.claude/hooks/` (they are not deleted; only deregistered) so they can be quickly reinstalled.
4. Confirm that enforcement is disabled.

### `--override` — Temporary override of the plan-gate

1. Present the plan to the user and **wait for explicit approval** (do not proceed without it).
2. Once approved, **create the approval marker**: `touch "$KARVEY_PLAN_FLAG"` (default `/tmp/claude-plan-approved`).
3. The `plan-gate` hook will let `Edit`/`Write`/destructive `Bash` through while the marker exists. Inform that this is a one-off grant and that it's best to remove it (`rm <flag>`) when the approved block of changes is done.

### `--freeze <dir>` — Edit-lock to a directory (boundary)

For sensitive work or debugging: restrict `Edit`/`Write` to a single directory.

1. Resolve `<dir>` to an absolute path and validate that it exists inside the project.
2. Install/register a `PreToolUse` hook over `Edit`/`Write`/`NotebookEdit` that **blocks** (exit 2) any write whose `file_path` is not under the boundary; persist the boundary (e.g., in a `KARVEY_FREEZE_DIR` marker or a freeze state file).
3. Confirm the active boundary and remind that edits are only allowed inside `<dir>` until `--unfreeze`.

### `--unfreeze` — Remove the edit-lock

1. Remove the freeze hook from `settings.json` and clear the boundary marker/state.
2. Confirm that the lock is lifted and that normal edits are allowed again (subject to the other hooks if they are active).

## Notes

- `--install`/`--freeze` edit `settings.json` and copy scripts: respect the approved-plan gate like any other change.
- This skill **complements** the phase gates (`karvey-qa`, etc.) but does not replace them or approve them on its own.
- After touching artifacts in `docs/spec/`, sync knowledge per `karvey/rules/knowledge-sync.md`.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
