---
name: karvey-checkpoint
description: Save and restore work-in-progress state for the Karvey method. Captures git state, decisions made, and pending work so a future session (or another person) can resume cleanly. When a team is configured, `save` also captures the agent's rotation handoff. Triggers include "karvey checkpoint", "guardar contexto", "restaurar contexto", "guardar estado", "retomar trabajo", "handoff", "rotar sesión", "rotate session", "relevo".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [save | restore] [<change-id>] [--handoff-only | --no-handoff]
---

# Karvey Checkpoint

A **cross-cutting** skill of the Karvey Method: a support layer, **NOT a phase**. It does not advance or modify the change's lifecycle. In particular, it **does NOT touch `spec.json:phase`** nor any phase field.

Inspired by `gstack /context-save` + `/context-restore`, its only job is to ensure that work in progress is not lost between sessions or in a handoff to another person.

## Goal

That work in progress **is not lost between sessions / handoffs**. When a session ends half-finished, or when another person (or another agent, on another machine) must take over, the checkpoint writes down where everything stood: the git state, the decisions made, the pending work and the concrete next step.

This skill **complements, does not replace**, the living specs or `spec.json`. The specs remain the source of truth for the change; the checkpoint is just a snapshot of the work-in-progress to be able to resume cleanly.

## The two faces of a save

`save` writes **up to two artifacts**, because there are two things that get lost when a session ends:

| | Checkpoint of the **change** | Handoff of the **agent** |
|---|---|---|
| Saves | the work: branch, working tree, last commit, WIP | the worker: role, standing decisions, commitments, what is not in the repo |
| Where | `docs/spec/changes/{change-id}/checkpoint.md` | `{ops_repo}/agents/<role>/handoff.md` |
| Lives as long as | the change | the agent's whole tenure, across many changes |
| Written when | a session ends mid-change | a session rotates (context/hours/block close) |
| Required | always | **only if a team is configured** |

**The handoff is produced, not composed.** Its state section is the output of commands; only judgment
is written by hand. A handoff written from memory is the one that lies — it claims a version is live
when production still serves the previous one, or asks for decisions that were already made. Whatever
can be captured, is captured.

**If there is no team configured, `save` behaves exactly as before** and writes only the checkpoint.
Teams are opt-in; see `karvey/rules/team.md`, including when **not** to use one.

## Modes

The skill receives a mode (`save` or `restore`) and, optionally, a `<change-id>`. If no `change-id` is given, the active change is detected (see "Resolving the change-id"). Flags: `--handoff-only` (rotate without touching the change checkpoint) and `--no-handoff` (checkpoint only, even with a team configured).

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
5. **Resolve the team layer.** Read `docs/spec/team.json` (or a legacy `.ceo-agentes`, searching upward from the working directory). **If neither exists, skip to step 8** — no handoff, no warning, nothing to do.
6. **Capture the agent state** (Step 5-bis, detailed below) and **write the handoff** to `{ops_repo}/agents/<role>/handoff.md`, using the "Handoff format" section.
7. **Commit the handoff by explicit path**, in the ops repo:
   ```bash
   git pull --rebase --autostash
   git commit -- agents/<role>/handoff.md board/<role>.md -m "handoff: <one line>"
   ```
   **Never `git add -A`, and never a bare commit.** Agents sharing a working copy share one index; a
   bare commit carries away whatever someone else left staged, possibly half-written. See
   `rules/team.md`.
8. **Integrate with knowledge-sync**: after saving, apply the rules of `karvey/rules/knowledge-sync.md` to keep the repo's knowledge synced (memory, indexes, references). The checkpoint is a natural point to trigger this sync.
9. **Do NOT** modify `spec.json:phase` nor advance the phase. Confirm to the user the path of the written checkpoint and, if written, of the handoff — **and whether the session is now ready to rotate**.

#### Step 5-bis — capturing the agent state (not recalling it)

Run these and put the **output**, not your memory of it, into the handoff. For each repo in
`project.json:repos` that the agent owns:

```bash
git rev-parse --abbrev-ref HEAD                 # branch
git log -1 --pretty='%h %ad %s' --date=short    # last commit
git status --porcelain | wc -l                  # uncommitted
git log origin/{integration}..HEAD --oneline    # pushed but not merged
git log HEAD..origin/{integration} --oneline    # behind
```

Then, and this is the part that catches stale handoffs: **for every claim of "done", run the check
that measures it** — the published version stamp, the live resource, the API response — per
`rules/verification.md`. A handoff that says "deployed" without that check is the failure this step
exists to prevent.

Finally, list the **scheduled tasks** of this session **with their full prompt**. They die with the
context reset, silently; the handoff is the only way they are ever recreated.

### `restore` mode — restore state

Reads the checkpoint and leaves the user (or the new agent) ready to resume. Steps:

1. **Resolve the change-id** and locate the corresponding checkpoint (`docs/spec/changes/{change-id}/checkpoint.md`, or the project checkpoint if there is no active change).
2. **Read the checkpoint** in full.
3. **Verify the real git state** against what was recorded (branch, last commit, working tree) to detect divergences between what was saved and the current state.
4. **If a team is configured, read the handoff too** — `{ops_repo}/agents/<role>/handoff.md`, plus the compact manifest and the role's board — and **apply the same contrast to it**: if the branch it declares no longer exists, if the commit it cites has been superseded, if what it calls pending is already merged, **the handoff has aged, and that is reported before anything in it is believed**. An aged handoff is not an error; believing it silently is.
5. **Cross the open questions against the decision log** before repeating them (`karvey-decisions cross`). Most "blocked on a decision" items are already answered; re-asking costs the human the same answer twice.
6. **Summarize where everything stands**: branch, last commit, pending work and relevant decisions.
7. **Propose the next concrete step** to resume, based on the checkpoint's "Next step" field and on the verified real state.
8. **Recreate the scheduled tasks** listed in the handoff, if any.
9. **Do NOT** modify `spec.json:phase` nor advance the phase.

## Resolving the change-id

1. If the user passed an explicit `<change-id>`, use it.
2. If not, try to detect the active change: check `docs/spec/changes/` (the most recent folder or the one indicated by `spec.json`) and, if it exists, the project's `spec.json`.
3. If there is no active change, operate in **project** mode (checkpoint in `docs/spec/checkpoint.md`). With a team configured, `--handoff-only` is the normal way to rotate outside any change.

## Checkpoint format

```markdown
# Checkpoint — {change-id | project}

> Cross-cutting skill karvey-checkpoint. It is NOT a phase. It does NOT modify spec.json:phase.

- **Date:** {YYYY-MM-DD HH:MM TZ}
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

## Handoff format

Written **to be read cold**, by a session that has no memory of this one. The chronology lives in the
board; this file is the *state at the moment of relay*.

```markdown
# Handoff — agent-{code}-{role}

## 0. Verified state — {YYYY-MM-DD HH:MM TZ}
Captured with commands, not from memory. If this does not match on startup, this handoff has aged:
believe the commands.

| Repo | Branch | Uncommitted | Last commit | Published? |
|---|---|---|---|---|
| {repo} | {branch} | {n} | {hash} {subject} | {the check that measures it} |

## 1. Blocking right now
What stops the work, first line, with what it is waiting on and who can unblock it.

## 2. Who you are
Role, repos you own, what is NOT yours, chain of approval.

## 3. Standing decisions that affect you
`D-NN` (or `C-NN`) + **why**, not just what. Link, do not copy.

## 4. In flight, and what I am waiting for
Deliverables out for review, open PRs, promises made — to whom and by when.

## 5. What a new session CANNOT derive from the repo
The expensive section. Traps, things measured once, corrections of your own earlier claims,
conventions that exist only because something broke.

## 6. Scheduled tasks — with their full prompt
They die with the context reset, silently. Without this they stop existing and nobody is told.

## 7. Last updated
{date · who · what changed since the previous handoff}
```

**Rules for writing it** (each one from a real failure — see `rules/verification.md`):

- **Correct the body; never append a revision at the end.** The next reader goes top-down and stops at the stale paragraph without reaching the note that closed it.
- **Measured, not recalled.** Section 0 is command output. Anything claimed as done was checked in this session.
- **When you correct your own earlier claim, the document says so** — not a message. The message is lost; the wrong number stays.
- **Commit by explicit path** (`git commit -- <paths>`) when the ops repo is shared.
- **An agent cannot rotate itself.** Clearing the context is a terminal command, not a tool. Write the handoff, commit it, **say it is ready to rotate**, and **keep working normally** until someone rotates it.
- **If this skill is not installed in that session, a handoff written by hand satisfies the method.** Do not simulate the skill and do not invent a substitute under its name.

## Notes

- This skill is a support one: use it freely when closing or opening a session, before a handoff, or when the context is about to be lost.
- It does not replace the living specs nor `spec.json`; it only saves/restores the work-in-progress.
- It never advances the change's phase.
- Rotation thresholds (context size, session hours) are declared in `team.json:rotation` and explained in `rules/team.md`.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
