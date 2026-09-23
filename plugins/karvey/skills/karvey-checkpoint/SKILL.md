---
name: karvey-checkpoint
description: Save and restore work-in-progress state for the Karvey method. `save` captures the change's checkpoint AND the agent's handoff — identity, manifest, board, checklist, repo state, standing decisions and scheduled tasks — so a future session (or another person) resumes cleanly. Works with a single agent; a team only changes where the handoff lives. Triggers include "karvey checkpoint", "guardar contexto", "restaurar contexto", "guardar estado", "retomar trabajo", "handoff", "rotar sesión", "rotate session", "relevo", "quién soy".
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

`save` writes **two artifacts**, because two different things are lost when a session ends:

| | Checkpoint of the **change** | Handoff of the **agent** |
|---|---|---|
| Saves | the work: branch, working tree, last commit, WIP | the worker: who they are, the rules they follow, their board, their standing decisions |
| Where | `docs/spec/changes/{change-id}/checkpoint.md` | `docs/spec/agent/handoff.md` (single agent) or `{ops_repo}/agents/<role>/handoff.md` (team) |
| Lives as long as | the change | the agent's whole tenure, across many changes |
| Written when | a session ends mid-change | a session rotates: context threshold, session hours, or the close of a work block |

**Both are written whether or not there is a team.** A single agent rotates too, and it is the case
with the least safety net: nobody else holds the context. **A team changes only where the handoff
lives and adds the roster around it** — never whether it exists. The team layer (`rules/team.md`) is
optional; the handoff is not.

**The handoff is produced, not composed.** Its state section is the output of commands; only judgment
is written by hand. A handoff written from memory is the one that lies — it claims a version is live
when production still serves the previous one, or asks for decisions that were already made. Whatever
can be captured, is captured.

## What the handoff carries

Six things, and the state of the repos is only one of them. The other five are what makes a cold
session *competent* rather than merely informed:

| Piece | Why it is in the handoff |
|---|---|
| **Who I am** | Role, the repos owned, **what is explicitly not mine**, who approves what. A session that does not know its boundaries either overreaches or stalls. |
| **The manifest / standing rules** | The rules that govern how this agent works. **Referenced with its commit, not copied** — a copy ages and then two versions disagree. If a compact version exists, that is what a reload reinjects. |
| **The board** | The open tasks with their state. A request that lives only in a session's context disappears when the next task arrives, and whoever asked has no way to know. |
| **The closing checklist** | What must be true before this agent reports anything as done (`rules/verification.md`). It travels with the agent, because it is the first thing a tired session skips. |
| **Repo state** | Branch, last commit, uncommitted, unmerged — per owned repo, measured. |
| **Scheduled tasks, with their full prompt** | They die with a context reset, silently. Without this they stop existing and nobody is told. |

Plus what no artifact holds: **standing decisions that affect the work** (linked, with their *why*),
**commitments made** (to whom, by when), and **what a new session cannot derive from the repo**.

## Modes

The skill receives a mode (`save` or `restore`) and, optionally, a `<change-id>`. If no `change-id` is given, the active change is detected (see "Resolving the change-id"). Flags: `--handoff-only` (rotate without touching the change checkpoint) and `--no-handoff` (checkpoint only).

### `save` mode — save state

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
4. **Write the checkpoint** to `docs/spec/changes/{change-id}/checkpoint.md`, or to a project-level checkpoint (`docs/spec/checkpoint.md`) if there is **no** active change. Use the "Checkpoint format" section.
5. **Resolve the agent profile** — where this agent's own artifacts live:
   - **Team configured** (`docs/spec/team.json`, or a legacy `.ceo-agentes`, searching upward): role from the working directory, artifacts under `{ops_repo}/agents/<role>/` and `{ops_repo}/board/<role>.md`. See `rules/team.md`.
   - **No team** (the default): artifacts under `docs/spec/agent/` — `manifest.md`, `board.md`, `checklist.md`, `handoff.md`.
   - **Neither exists yet:** create `docs/spec/agent/` from the templates below, ask the three questions needed to fill the manifest (who this agent is, which repos it owns, what is not its call), and continue. **Bootstrapping is part of the save, not a prerequisite for it.**
6. **Refresh the pieces before quoting them** — a handoff that cites a stale board is worse than one that cites nothing:
   - **Board:** move what this session actually did to its real state, and **write down every request that arrived and was not resolved**, before anything else.
   - **Manifest / checklist:** verify they still describe how this agent works; if a rule changed, **correct the body** and note the change. Record their commit (`git log -1 --pretty=%h -- <path>`) in the handoff, so `restore` can detect drift.
7. **Capture the agent state** (Step 7-bis below), **write the handoff** using the "Handoff format" section, and write its machine-readable twin **`state.json`** beside it (schema below). The handoff is for whoever reads; `state.json` is what the session hook compares against the live repos to detect drift **before** anyone believes the prose.
8. **Commit by explicit path**:
   ```bash
   git pull --rebase --autostash
   git commit -- docs/spec/agent/handoff.md docs/spec/agent/state.json docs/spec/agent/board.md -m "handoff: <one line>"
   ```
   In a **shared** ops repo this is mandatory, not stylistic: agents sharing a working copy share one
   index, and a bare commit carries away whatever someone else left staged, possibly half-written.
9. **Integrate with knowledge-sync** (`karvey/rules/knowledge-sync.md`): the checkpoint is a natural point to trigger the sync.
10. **Do NOT** modify `spec.json:phase`. Confirm the paths written and **whether the session is now ready to rotate**.

#### Step 7-bis — capturing the agent state (not recalling it)

Run these and put the **output**, not your memory of it, into the handoff. For each owned repo:

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

Finally, list the **scheduled tasks** of this session **with their full prompt**.

### `restore` mode — restore state

1. **Resolve the change-id** and locate the corresponding checkpoint.
2. **Read the checkpoint** in full.
3. **Verify the real git state** against what was recorded (branch, last commit, working tree) to detect divergences between what was saved and the current state.
4. **Resolve the agent profile and read it whole**: handoff, manifest (or its compact version), board and checklist. This is what turns a blank session into *this* agent.
5. **Contrast the handoff, do not believe it** — starting from `state.json`, which the session hook may already have compared for you. If the branch it declares no longer exists, if the commit it cites has been superseded, if what it lists as pending is already merged, or if the manifest's commit differs from the one recorded, **say the handoff has aged, and say which parts**, before presenting any of it as current. An aged handoff is not an error; believing it silently is.
6. **Cross open questions against the decision log** before repeating them (`karvey-decisions cross`). Most "blocked on a decision" items are already answered; re-asking costs the human the same answer twice.
7. **Summarize where everything stands**: identity, board, branch, last commit, pending work, standing decisions.
8. **Propose the next concrete step**, from the handoff's next steps and the verified real state.
9. **Recreate the scheduled tasks** listed in the handoff, if any.
10. **Do NOT** modify `spec.json:phase`.

## Resolving the change-id

1. If the user passed an explicit `<change-id>`, use it.
2. If not, detect the active change: `docs/spec/changes/` (most recent, or as indicated by `spec.json`).
3. If there is no active change, operate in **project** mode (`docs/spec/checkpoint.md`). `--handoff-only` is the normal way to rotate outside any change.

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

Written **to be read cold**, by a session with no memory of this one. The chronology lives in the
board; this file is the *state at the moment of relay*.

```markdown
# Handoff — {agent name}

## 0. Verified state — {YYYY-MM-DD HH:MM TZ}
Captured with commands, not from memory. If this does not match on startup, this handoff has aged:
believe the commands.

| Repo | Branch | Uncommitted | Last commit | Published? |
|---|---|---|---|---|
| {repo} | {branch} | {n} | {hash} {subject} | {the check that measures it} |

## 1. Blocking right now
What stops the work, first line, with what it waits on and who can unblock it.

## 2. Who I am
Role and scope · repos I own · **what is NOT mine** · who approves what.
Manifest: {path} @{commit} · Board: {path} · Checklist: {path} @{commit}

## 3. Rules I work under
The short version, or the pointer to the compact manifest a reload reinjects. **Referenced, not
copied** — if this section and the manifest disagree, the manifest wins and this section is wrong.

## 4. Board — open, in one place
The open items with their state, including every request that arrived and was not resolved. A pending
item that lives only in a session's context does not exist.

## 5. Closing checklist
What must be true before I report anything as done (`rules/verification.md`), plus whatever this
project adds.

## 6. Standing decisions that affect me
`D-NN` + **why**, not just what. Linked, not copied.

## 7. In flight, and what I am waiting for
Deliverables out for review, open PRs, promises made — to whom and by when.

## 8. What a new session CANNOT derive from the repo
The expensive section. Traps, things measured once, corrections of my own earlier claims, conventions
that exist only because something broke.

## 9. Scheduled tasks — with their full prompt
They die with the context reset, silently.

## 10. Last updated
{date · who · what changed since the previous handoff}
```

**Rules for writing it** (each from a real failure — see `rules/verification.md`):

- **Correct the body; never append a revision at the end.** The next reader goes top-down and stops at the stale paragraph without reaching the note that closed it.
- **Measured, not recalled.** Section 0 is command output. Anything claimed as done was checked in this session.
- **Reference the manifest and the checklist; do not inline them.** Two copies of a rule become two different rules.
- **When you correct your own earlier claim, the document says so** — not a message. The message is lost; the wrong number stays.
- **Commit by explicit path** (`git commit -- <paths>`).
- **An agent cannot rotate itself.** Clearing the context is a terminal command, not a tool. Write the handoff, commit it, **say it is ready to rotate**, and **keep working normally** until someone rotates it.
- **If this skill is not installed in that session, a handoff written by hand satisfies the method.** Do not simulate the skill and do not invent a substitute under its name.

## `state.json` — the handoff's machine-readable twin

Written beside the handoff on every save. It exists so the session hook can tell, **with commands and
before a single line of prose is believed**, whether the handoff still describes reality:

```json
{
  "agent": "{agent name}",
  "role": "{role}",
  "saved_at": "{ISO timestamp}",
  "handoff": "{path}",
  "manifest_commit": "{short hash of the manifest at save time}",
  "repos": [
    { "path": "{repo path}", "branch": "{branch}", "commit": "{short hash}", "uncommitted": 0 }
  ],
  "active_change": "{change-id or empty}",
  "scheduled_tasks": 0,
  "ready_to_rotate": false
}
```

Keep it small and factual: it is evidence, not a second handoff. If it and the prose disagree, **the
prose is the one that aged**.

## Templates for a first save (single agent)

`docs/spec/agent/manifest.md` — who I am, the repos I own, **what is not my call**, who approves what,
and how I communicate. `docs/spec/agent/board.md` — a table of `id · priority · task · state · updated
· note`. `docs/spec/agent/state.json` — written by the save, never by hand. `docs/spec/agent/checklist.md` — the closing checks, starting from `rules/verification.md` and
adding whatever this project has paid for once. `handoff.md` — the format above.

With a team these same four files move to `{ops_repo}/agents/<role>/` and the board to
`{ops_repo}/board/<role>.md` — where `{ops_repo}` is the sibling ops repo under the team root, or, when
`team.json` lives **inside** the repo it names (`ops_repo` = this repo, or empty), the folder that holds
`team.json` (`docs/spec/`), i.e. `docs/spec/agents/<role>/` and `docs/spec/board/<role>.md`. The session
hook resolves the same two layouts; `karvey-team init` migrates them rather than duplicating them.

## Notes

- Use it freely when closing or opening a session, before a handoff, or when the context is about to be lost.
- It does not replace the living specs nor `spec.json`; it only saves/restores the work-in-progress.
- It never advances the change's phase.
- **On session start** (startup, resume, compact, clear) the plugin's hook reinjects identity, manifest, board and handoff, compares `state.json` against the live repos, and **tells the session to run `/karvey-checkpoint restore` first** when there is an active change or the state has drifted. The hook reinjects and measures; the restore itself — crossing decisions, recreating scheduled tasks, proposing the next step — is this skill's job, because a hook cannot invoke a skill.
- Rotation thresholds: `team.json:rotation` when there is a team, otherwise the defaults in `rules/team.md` (150k of context, 24 h, or the close of a work block).

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
