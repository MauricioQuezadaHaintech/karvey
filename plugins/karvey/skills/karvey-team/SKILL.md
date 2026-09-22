---
name: karvey-team
description: OPTIONAL team layer of the Karvey method — set up and run a team of agents (roles, manifests, boards, census, relay) and measure what it costs. Karvey works fully with one agent; this is opt-in and not the default. Triggers include "karvey team", "equipo de agentes", "agent team", "multi-agente", "censo de agentes", "relevo", "relay agents", "cuánto cuesta el equipo", "agent cost".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [init | census | relay | cost] [--role <role>] [--dry-run]
---

# Karvey Team

A **cross-cutting** skill of the Karvey Method: the layer of **who does the work**, as opposed to the
pipeline, which is the work itself. **NOT a phase** — it never touches `spec.json:phase`.

> **Read this before running `init`.** A team of agents is **opt-in and not recommended by default**.
> The measured run that produced this layer cost **≈US$1,000 over 3 days with 6 agents and ended by
> going back to a single agent**: every hop between sessions is new context for the receiver, there is
> no shared cache, and at 588k a turn costs **7×** what it costs at 80k. `rules/team.md` has the full
> table and the conditions under which a team does pay off. With a bigger budget it may well be worth
> it — but it is a choice made with the number in front of you.

**Karvey is complete with one agent.** No phase requires this layer, and no gate is weakened without
it. A project that never runs `init` never sees it — **including the handoff**, which
`karvey-checkpoint` writes for a lone agent just the same. This layer adds the roster, not the memory.

## Execution steps

Read `karvey/rules/team.md` first. Resolve the mode from `$ARGUMENTS`; with no argument, show the
current state (whether `team.json` exists, which roles are declared, which handoffs are stale, and the
last cost report) and offer the options.

### `init` — set the team up

1. **Warn first.** Show the cost table from `rules/team.md` and confirm the user wants a team rather
   than one agent. If they hesitate, recommend one agent. This is not a formality: it is the single
   most expensive decision in this layer.
2. **Ask the minimum** — business `code`, `ops_repo`, and which role lives in which working directory.
   Nothing else; the rest has defaults.
3. **Write `docs/spec/team.json`** (schema in `rules/team.md`), including `rotation` thresholds
   (defaults 150000 / 24h) and `cost_report`.
4. **Create the ops structure**: `agents/<role>/manifest.md`, `agents/<role>/handoff.md`,
   `agents/<role>/checklist.md`, `board/<role>.md`, `agents/census.md`, and the **compact manifest**
   (`agents/manifest-compact.md`) — the 15–20 line version that a session reload can reinject whole.
   **If the project already has a single-agent profile in `docs/spec/agent/`, MIGRATE it** (git mv,
   keeping history) instead of creating an empty one beside it: that agent already has a manifest, a
   board, a checklist and a handoff worth keeping, and two profiles for the same agent is how one of
   them starts lying.
5. **Offer the session hook** (`hooks/` in this plugin) so each session re-reads its identity, compact
   manifest and handoff on startup, resume, compact and clear. Explain that a plugin **cannot** declare
   a statusline (only `agent` and `subagentStatusLine` are accepted), so the rotation statusline is
   three lines the user pastes once into their own settings — the script ships here, the install does
   not happen behind their back.
6. **Do not create sessions.** Launching agents is the human's action; this skill writes the files that
   make a launched session know who it is.

### `census` — who is who

An **inventory, not a directory.** It records who each agent claims to be, on which machine, with what
it owns and when it was last seen. It is **never** used to address a message: names and refs are local
to whoever lists them and change on rename, reconnect and reset (`rules/team.md`).

1. Read `team.json` and the ops repo; list the declared roles and their artifacts.
2. Mark, for each role: last handoff commit, its age, and whether the board moved more recently than
   the handoff (a board ahead of the handoff means the handoff is stale).
3. Write `agents/census.md`. State explicitly, in the file, that it is not an address book.

### `relay` — close the cycle and leave the team rotatable

For each role, or for `--role <role>`:

1. Run `karvey-checkpoint save --handoff-only` for that agent (the handoff is captured, not composed).
2. Verify it landed: the file exists, its section 0 is command output, and it was committed **by
   explicit path**.
3. Report which sessions are **ready to rotate** — and stop there. **No agent can rotate another, and
   none can rotate itself**: clearing a context is a terminal command. This skill produces the list;
   the human rotates. Agents keep working normally meanwhile.
4. Remind that scheduled tasks die with the reset and must be in the handoff with their full prompt.

### `cost` — what the team actually spends

The layer that made the 6-agent run defensible only in hindsight. Without this, a team cannot be
judged, and the judgment arrives as a monthly bill.

1. Collect per-session usage from whatever the environment exposes (session transcripts/usage records).
2. Write `{ops_repo}/{cost_report}/{YYYY-MM}-agents.md`: spend per agent, per day, share of turns vs
   share of spend, and **context size at the time of the most expensive turns** — that correlation is
   the actionable one.
3. Compare against the **single-agent counterfactual**: how much of the spend was re-reading context
   that another session already held. Report it as a range, honestly labelled as an estimate.
4. If the trend says the team is not paying for itself, **say so in the report**, with the number. That
   sentence is the whole point of this subcommand.

## Notes

- Complements `rules/multi-agent.md` (several agents on the **work**: parent/child changes, pinned
  inputs, `[human]` tasks). This skill is about the **agents**; multi-repo work does not require it.
- Never touches `spec.json:phase`, never approves a gate, and never launches or stops a session.
- Writing to a shared ops repo: commit by explicit path (`git commit -- <paths>`).

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
