---
name: karvey-checkpoint
description: Save and restore work-in-progress state for the Karvey method. Captures git state, decisions made, and pending work so a future session (or another person) can resume cleanly. Triggers include "karvey checkpoint", "guardar contexto", "restaurar contexto", "guardar estado", "retomar trabajo", "handoff".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [save | restore] [<change-id>]
---

# Karvey Checkpoint

A **cross-cutting** skill of the Karvey Method: a support layer, **NOT a phase**. It does not advance or modify the change's lifecycle. In particular, it **does NOT touch `spec.json:phase`** nor any phase field.

Inspired by `gstack /context-save` + `/context-restore`, its only job is to ensure that work in progress is not lost between sessions or in a handoff to another person.

## Goal

That work in progress **is not lost between sessions / handoffs**. When a session ends half-finished, or when another person (or another agent, on another machine) must take over, the checkpoint writes down where everything stood: the git state, the decisions made, the pending work and the concrete next step.

This skill **complements, does not replace**, the living specs or `spec.json`. The specs remain the source of truth for the change; the checkpoint is just a snapshot of the work-in-progress to be able to resume cleanly.

## Modes

The skill receives a mode (`save` or `restore`) and, optionally, a `<change-id>`. If no `change-id` is given, the active change is detected (see "Resolving the change-id").

### `save` mode — save state

Captures the current state and writes it to a checkpoint file. Steps:

1. **Resolve the change-id** (see the "Resolving the change-id" section).
2. **Capture the git state** of the repo being worked on:
   - Current branch:
     ```bash
     git rev-parse --abbrev-ref HEAD
     ```
   - Working tree state (modified, staged, untracked files):
     ```bash
     git status --short
     ```
   - Last commit (short hash + subject):
     ```bash
     git log -1 --pretty='%h %s'
     ```
   - (Optional, if it helps the handoff) summarized diff:
     ```bash
     git diff --stat
     ```
3. **Collect the human context** of the session: decisions made, why, what is left pending and what the concrete next step is to resume.
4. **Write the checkpoint** to:
   - `docs/spec/changes/{change-id}/checkpoint.md` if there is an active change, or
   - a project-level checkpoint (e.g. `docs/spec/checkpoint.md`) if there is **no** active change.

   Use the template from the "Checkpoint format" section.
5. **Integrate with knowledge-sync**: after saving, apply the rules of `karvey/rules/knowledge-sync.md` to keep the repo's knowledge synced (memory, indexes, references). The checkpoint is a natural point to trigger this sync.
6. **Do NOT** modify `spec.json:phase` nor advance the phase. Confirm to the user the path of the written checkpoint.

### `restore` mode — restore state

Reads the checkpoint and leaves the user (or the new agent) ready to resume. Steps:

1. **Resolve the change-id** and locate the corresponding checkpoint (`docs/spec/changes/{change-id}/checkpoint.md`, or the project checkpoint if there is no active change).
2. **Read the checkpoint** in full.
3. **Verify the real git state** against what was recorded (branch, last commit, working tree) to detect divergences between what was saved and the current state.
4. **Summarize where everything stands**: branch, last commit, pending work and relevant decisions.
5. **Propose the next concrete step** to resume, based on the checkpoint's "Next step" field and on the verified real state.
6. **Do NOT** modify `spec.json:phase` nor advance the phase.

## Resolving the change-id

1. If the user passed an explicit `<change-id>`, use it.
2. If not, try to detect the active change: check `docs/spec/changes/` (the most recent folder or the one indicated by `spec.json`) and, if it exists, the project's `spec.json`.
3. If there is no active change, operate in **project** mode (checkpoint in `docs/spec/checkpoint.md`).

## Checkpoint format

```markdown
# Checkpoint — {change-id | project}

> Cross-cutting skill karvey-checkpoint. It is NOT a phase. It does NOT modify spec.json:phase.

- **Date:** {YYYY-MM-DD HH:MM CLT}
- **Author:** {name / agent}
- **Repo:** {repo path}

## Git state
- **Branch:** {branch}
- **Last commit:** {short hash} {subject}
- **Working tree:**
  ```
  {git status --short output}
  ```

## Decisions made
- {decision + why}

## Pending work
- [ ] {pending item}

## Next step
{The concrete step to resume cleanly.}
```

## Notes

- This skill is a support one: use it freely when closing or opening a session, before a handoff, or when the context is about to be lost.
- It does not replace the living specs nor `spec.json`; it only saves/restores the work-in-progress.
- It never advances the change's phase.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
