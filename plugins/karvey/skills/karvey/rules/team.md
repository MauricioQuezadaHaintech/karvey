# Rule: Team layer (agent teams — OPTIONAL)

Karvey's pipeline carries the axis of the **work**: how a change goes from idea to production.
This rule adds the axis of the **worker**: who carries it, what role they hold, how they survive a
context reset, and how several of them coordinate without stepping on each other.

> **This layer is OPT-IN and it is NOT the recommended default.**
> Karvey works fully with **one agent**. Nothing in the pipeline requires a team, no phase asks for
> one, and no gate is weakened by its absence. A project that never creates `docs/spec/team.json`
> never sees this layer. Read "When NOT to use a team" before turning it on — it is written from a
> measured failure, not from theory.

## When NOT to use a team

A team of agents is a **cost decision before it is an engineering decision**. The evidence below is
first-hand, from the run that produced this rule (2026-09, a 6-agent team on a real product):

| What was measured | Value |
|---|---|
| Duration of the experiment | 3 days |
| Spend | ≈ **US$1,000** |
| Outcome | **Went back to one agent with good instructions** |
| Cost of a turn at 588k of context vs at 80k | **7×** |
| Share of spend: 31% of the turns | **48% of the total** |

**Why it got expensive, and it was not the model's fault:** every hop between agents is *new context*
for the receiver. There is no shared cache between sessions, so the same background gets re-read,
re-explained and re-paid for on each side. Ten short messages cost ten full re-reads. Work that one
agent holds in a single context becomes, across six, a permanent re-synchronization tax — and the
information arriving late is *worse* than no information, because someone already acted on the stale
version.

**Do not use a team when:** the budget matters; the work fits in one context; the split would be by
*topic* rather than by *repo with a real owner*; or nobody is measuring the spend. **Default to one
agent.** A team earns its cost only with genuinely parallel work on separate repos, long-running
independent tracks, or roles that need different tools and permissions (a machine with a browser, a
human-operated console). Turning it on is legitimate — with more budget it may pay off — but it is a
choice to make with the number in front of you, not a default to drift into.

**If it is on, measure it.** `karvey-team cost` exists for that, and the report belongs in the repo.
A team that cannot say what it spent cannot be judged.

## Configuration — `docs/spec/team.json` (optional)

Lives next to `project.json`. **If the file does not exist, the team layer is off** and every skill
behaves exactly as in a single-agent project.

```json
{
  "code": "M5D",
  "ops_repo": "Client_CODE_ops",
  "roles": {
    "Client_CODE_app": "app",
    "Client_CODE_web": "web",
    "Client_CODE_design": "designer"
  },
  "display_names": { "designer": "agent-M5D-designer" },
  "rotation": { "context_threshold": 150000, "max_session_hours": 8 },
  "cost_report": "reports/cost/"
}
```

- **`code`** — the business code; the agent's name is `agent-{code}-{role}`.
- **`roles`** — maps a working directory to a role. A directory not listed, and the root, are `ceo`.
- **`display_names`** — legacy names kept after a rename, so messages keep resolving.
- **`rotation`** — when a session must hand off (see below). Omitted values come from `karvey_lib/defaults.json` (`context_tokens.red`, `rotation_hours`; D-06).
- **`cost_report`** — where `karvey-team cost` writes, inside `ops_repo`.

A legacy `.ceo-agentes` file (`CODIGO=` / `OPS=` / `AGENTE_<dir>=<role>` / `NOMBRE_<role>=`) is read
with the same meaning when `team.json` is absent, so existing setups keep working unchanged.

Per-agent artifacts live in the ops repo: `agents/<role>/manifest.md`, `agents/<role>/handoff.md`,
`board/<role>.md`.
When `team.json` lives inside the repo it names (`ops_repo` is this same repo, or empty), the "ops repo" is the
folder that holds `team.json` — `docs/spec/agents/<role>/…` and `docs/spec/board/<role>.md`. The session hook and
`karvey-checkpoint` resolve both layouts the same way.

## Rotation — a session does not last forever

A long session drifts from its own rules, **and the one drifting is the last to notice**. So rotation
is scheduled, not improvised:

- **Thresholds:** `context_threshold` or `max_session_hours` (defaults: `karvey_lib/defaults.json`), whichever
  comes first, or the close of a work block. Restarting costs ~40k of context to re-read the
  handoff — it amortizes in under half a turn at that size.
- **An agent cannot rotate itself.** Clearing the context is a terminal command, not a tool. The
  agent writes its handoff, commits it, and **says it is ready to rotate**; the human (or whoever
  holds the terminal) rotates it. **It keeps working normally in the meantime** — it does not idle
  waiting to be relaunched.
- **Scheduled tasks die with the reset, silently.** Whatever the session had scheduled must be
  written into the handoff **with its full prompt**, or it stops existing and nobody is told.

**The handoff is not part of this layer.** `karvey-checkpoint save` writes it **with or without a
team**: a single agent rotates too, and it is the case with the least safety net, because nobody else
holds the context. Without a team the agent's profile lives in `docs/spec/agent/` (manifest, board,
checklist, handoff, `state.json`); a team only **moves** those files to `{ops_repo}/agents/<role>/`
and adds the roster around them. See `karvey-checkpoint` for the format and for what the handoff
carries: who I am, the rules I work under, the board, the closing checklist, the measured repo state
and the scheduled tasks.

## Addressing another agent — names are not identifiers

Portable, because it is where teams lose messages:

1. **Neither the display name nor the session ref is a shared identifier.** The ref you see for an
   agent is not the ref another session sees for it; a ref copied out of a document does not resolve.
2. **Introduce yourself in the first line** — who you are, which project, what you need. The anonymity
   is mutual: you do not appear under your own name in their list either.
3. **Send to the name your own list shows at that moment**, even when it looks wrong. A rename does
   not travel across remote-control sessions, and autogenerated names change on reconnect.
4. **The census is an inventory, not a directory** — it records who each agent claims to be and on
   which machine. Addressing is resolved live, never from the file.
5. A message to a stale name **is lost silently**. No answer means suspect the address before the
   content.

## Communication between agents — minimal, and telegraphic

The default channel is **the repo**: board, handoff, commit. A message is sent only when it (a)
unblocks something stopped, (b) corrects a course already taken, or (c) carries something the other
**cannot derive from the repo**. No read receipts; a report that asks for no decision gets no reply.
One message per agent per cycle.

When sent: instruction first, cite by ID (`D-NN`, `BUG-NN`, `{change-id}@{repo}`), no preamble, no
restating context the other already has, no explaining your own reasoning unless they must decide
with it. **Telegraphic means fewer words, not less precision:** never drop what makes a claim
verifiable (commit, path, size, figure), the conditions of an order, or what the other needs in
order to refuse with judgment.

**Delegation has two rules of its own:** a brief to investigate does not authorize publishing — the
one who delegates consolidates and publishes, the one who investigates returns findings. And whoever
delegates says **how many** they delegated to: a brief for "one subagent" that becomes four
multiplies the spend without the requester knowing.

## Shared working copy — the index is shared too

When several agents share one working copy of the ops repo, they share **one git index**. Staging a
path does not clear what someone else left staged, so a plain commit takes their work with it —
including a file caught half-written, which its owner never notices, because it no longer shows up in
their own status.

**Commit by explicit path, with the separator:** `git commit -- <paths>`, which commits only those
paths and ignores the rest of the index. Pull with `--rebase --autostash` before, and retry on a race.

## Relation to the rest of the method

- `multi-agent`[^r-multi-agent] covers the **work** side of several agents (parent/child changes, pinned inputs,
  `[human]` tasks, approvals). **This rule covers the agents themselves.** They are complementary and
  independent: multi-repo work does not require this layer.
- `karvey-team` manages the layer (`init`, `census`, `relay`, `cost`).
- `karvey-checkpoint` writes and restores the handoff — **independently of this layer**; here it only changes path and gains the roster.
- `karvey-decisions` keeps the decision log the whole team cites.
- `verification`[^r-verification] holds the verification rules that a team violates faster than one agent does.

[^r-multi-agent]: multi-agent.md — context only, not opened.
[^r-verification]: verification.md — context only, not opened.
