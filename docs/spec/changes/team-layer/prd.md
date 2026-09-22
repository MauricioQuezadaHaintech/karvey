# PRD — Optional team layer (`team-layer`)

## 1. Why

Karvey knows how to take a change from idea to production. It knows nothing about **who** carries it:
what role they hold, how they survive a context reset, how they coordinate, or what that coordination
costs. Everything about the worker lived outside the method — in a separate skill and in one project's
operations repo — so it aged there and no other project could use it.

## 2. The evidence this is built on

A 6-agent team was run on a real product for 3 days. Measured outcome:

| | |
|---|---|
| Spend | ≈ US$1,000 |
| Result | went back to **one agent with good instructions** |
| Turn cost at 588k of context vs 80k | **7×** |
| 31% of the turns | consumed **48%** of the spend |
| Items escalated as "blocked on a decision" | **14, of which 13 were already answered** |

The cause was not model quality: every hop between sessions is new context for the receiver, with no
shared cache, so the same background is re-read and re-paid on each side. Late information is worse
than none, because someone already acted on the stale version.

## 3. What this change decides

**Teams become a first-class option of the method, and explicitly not its default.** Karvey stays
complete with one agent. The layer ships with its own counter-evidence attached, so the next person
chooses with the number in front of them instead of drifting into it.

## 4. Scope

- The **handoff** becomes an artifact of `karvey-checkpoint save` — *captured* from commands, not
  composed from memory — and `restore` contrasts it like it already contrasts git.
- `karvey-team` to set up, relay and **measure** a team; `karvey-decisions` for the log everyone cites,
  with a mandatory cross-check before declaring a block.
- `rules/team.md` (including *When NOT to use a team*) and `rules/verification.md`.
- A plugin `SessionStart` hook, inert without a team, plus the rotation statusline the user installs.

## 5. Out of scope

Launching, stopping or rotating sessions (a terminal action, never an agent's); anything that would
make a phase or a gate depend on the team layer; any change to the 13-phase pipeline.

## 6. Success

A single-agent project sees no difference. A team project gets a handoff whose state section is
command output, a log that answers before the human is asked twice, and a monthly number that says
whether the team is worth it.
