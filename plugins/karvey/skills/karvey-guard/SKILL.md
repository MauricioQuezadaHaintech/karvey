---
name: karvey-guard
description: Karvey support — switches the enforcement hooks in project.json:enforcement (prod-gate, git-flow, plan-gate) and edit-locks a directory — when setting up or auditing guards. Triggers include "karvey guard", "karvey freeze", "activar hooks karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
argument-hint: [--install | --disable-hooks | --freeze <dir> | --unfreeze | --verify]
---

# Karvey Guard

## Purpose

A **cross-cutting support layer** of the Karvey Method — NOT a pipeline phase: **it does NOT change
`spec.json:phase`**. It switches the enforcement hooks the plugin ships, which block deterministically
(`PreToolUse`), and runs the verification checklist. The canonical rule is
`../karvey/rules/enforcement.md`; the flags live in `project.json:enforcement`
(`../karvey/rules/project-config.md`).

The hooks are registered by the plugin itself (`${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json`). Nothing is
copied into the project and `settings.json` is never edited: a guard is on or off by its flag.

| Flag | Default | Guard |
|---|---|---|
| `enforcement.prod_gate_hook` | on | a merge to production needs a recorded human prod approval |
| `enforcement.git_flow_hook` | off (opt-in) | no commit on integration/production, no direct push to production, no manual deploy |
| `enforcement.plan_gate_hook` | off (opt-in) | edits and destructive commands need an approval marker (`plan_marker_ttl_min`) |

**Approval comes only from the human's message.** The approval hook records the marker when the human
types it; this skill never creates, touches or extends a marker, and has no override.

## Execution steps

Read `../karvey/rules/enforcement.md` first. Resolve the mode from `$ARGUMENTS`. With no argument, show
the current state (`karvey-context.py --section enforcement`) and offer the options.

### `--install` / `--disable-hooks` — switch the guards

1. `docs/spec/project.json` must exist; otherwise stop and point at `karvey-init`.
2. On a docs branch (never on integration or production), set the flags the user chose in
   `project.json:enforcement` — `git_flow_hook`, `plan_gate_hook` to `true` to install, `false` to
   disable; `prod_gate_hook: false` only on the owner's explicit request.
3. Commit it and open the docs PR. Switching a guard **on** works from the working copy; switching one
   **off** takes effect only after merge, because the guards also read the reviewed line on
   `origin/{production}` and stay on while either says on.
4. Confirm with `karvey-context.py --section enforcement`.

**3.11 template entries.** If the project's `.claude/settings.json` still registers
`.claude/hooks/git-flow-guard.sh` or `plan-gate.sh`, say so: they are deprecated shims that forward to the
plugin's dispatcher (removed in 4.0.0). Propose removing the entries and relying on the flags; remove them
only with the user's OK.

### `--freeze <dir>` / `--unfreeze` — edit boundary (recommendation)

No shipped guard enforces a freeze. Record the boundary (absolute path inside the project) in the change's
checkpoint and keep every `Edit`/`Write` inside it until `--unfreeze` clears it. Say plainly that it is a
discipline, not a block.

### `--verify` — Verification checklist before reporting "done"

Read `../karvey/rules/verification.md` and walk the deliverable (report, handoff, PR description, phase
close) against its failure modes. For every claim, ask what command proves it and whether that command
was run **in this session**.

1. List each claim the deliverable makes about a file, a resource, a deployment or a test result.
2. Mark each one `verified` (with the command and its output), or `unverified` **with the reason** —
   an unverifiable claim is stated as such, never dropped and never softened into a claim.
3. Block on the classics: a citation is not the thing cited; exit 0 is not success; a green test over
   uncalled code proves nothing; a filename does not identify a version; a review appended at the end
   leaves the body lying.
4. Report the list. This is a checklist, **not** a gate: it does not approve `karvey-qa` on its own.

## Notes

- `--verify` is read-only and always safe to run; `--install`/`--disable-hooks` change `project.json` as a
  reviewed change.
- This skill **complements** the phase gates (`karvey-qa`, etc.) but does not replace or approve them.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
