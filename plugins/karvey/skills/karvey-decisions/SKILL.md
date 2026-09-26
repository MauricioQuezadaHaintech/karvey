---
name: karvey-decisions
description: Karvey support — the numbered decision log (D-NN, C-NN) and `cross`, which checks a question against it — before declaring anything blocked. Triggers include "karvey decisions", "registro de decisiones karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [log | cross | ask | show <D-NN>] [--series D|C] [--repo <ops_repo>]
---

# Karvey Decisions

Load: _core.md, multi-agent.md

A **cross-cutting** skill of the Karvey Method. **NOT a phase**; it never moves `spec.json:phase`.

In Karvey, a change cites the decisions it comes from (`spec.json:decisions: ["D-NN@repo"]`, see
`../karvey/rules/multi-agent.md`). This skill owns the **other side**: the registry those references point at,
so a decision taken in one change is visible to the next one, and so nobody re-asks the human
something they already answered.

## Why it exists

Decisions taken inside a change are invisible to the change next door. The cost is not theoretical:
in the run that produced this layer, **14 items were escalated as "blocked on a decision" and 13 were
already answered** — the human answered the same questions twice and the work stalled meanwhile.
`cross` is the subcommand that pays for this skill on its own.

## The two series

| Series | Who decides | Examples |
|---|---|---|
| **`D-NN`** | The business owner / customer | price, brand, scope, legal, what gets sold, anything irreversible |
| **`C-NN`** | Whoever directs the work | order of merges, which branch is cut, who reviews, process calls |

Both live in **one decision log** in the ops repo, `{ops_repo}/docs/spec/decisions.md`, numbered
**once, never reused, never renumbered**. A decision is immutable: it is superseded by a later one that cites
it, never edited into something else.

**Per-period files** (`docs/spec/decisions/*.md`, e.g. one file per month) are an older shape. They are **read**
by `cross` and `show` and counted by `karvey-id.py`, but new decisions are **written only** to
`docs/spec/decisions.md`. The first time a run finds per-period files, show this migration note **once** (then record
that it was shown, e.g. a `<!-- decisions-migration-note-shown -->` line at the top of `docs/spec/decisions.md`):

> *This project also keeps per-period decision files (`docs/spec/decisions/*.md`). They are still read; new
> decisions go to `docs/spec/decisions.md`. To migrate, move their entries into `docs/spec/decisions.md` unchanged (same
> numbers, same text) in one reviewed commit, then delete the old files.*

The same `D-NN` in both shapes (or twice in one) is a **duplicate**: report it with both locations and never pick
one silently; the owner decides which entry stands and the other is superseded.

## Execution steps

### `log` — record a decision

1. Resolve the ops repo (`project.json:ops_repo`, else `spec_repo`) and the next free number in the
   series from `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-id.py" next D` — it scans the whole log, the per-period files and every branch.
2. Write the entry with four fields, all mandatory:
   - **What** was decided, in one sentence that survives out of context.
   - **Who** decided it and **when** — quoting their own words when they exist. A paraphrase of an
     approval is not an approval.
   - **Why** — the reasoning, because the next reader needs to know what it would take to revisit it.
   - **What it does NOT say.** The field that prevents over-application: a decision that corrects a
     model is routinely read as deleting the concept.
3. If it supersedes an earlier decision, cite it **in both directions**: the new one names the old,
   and the old one gets a superseded-by line. **Correct the body of anything the decision invalidates**
   — a decision appended at the end leaves the body lying (`verification`[^r-verification]).
4. **Record it before announcing it.** Whoever takes a decision writes it down first, so the person
   who goes looking for it finds it.

### `cross` — check before declaring a block

**Mandatory before any deliverable says "waiting on a decision".**

1. Search `{ops_repo}/docs/spec/decisions.md` **and** `{ops_repo}/docs/spec/decisions/*.md` for the question's
   subject — by concept, not only by keyword. Report any duplicate `D-NN` found on the way.
2. Search the **product/offer material** too (pricing, plans, commercial docs). Roughly half of what
   decides a product lives there rather than in the decision log, and crossing only one of the two
   sources is how the 13-out-of-14 happened.
3. Search the living specs (`docs/spec/specs/`) and the changes' `spec.json:decisions`.
4. **Result:**
   - Found → cite the `D-NN`, apply it, and **go on**. Do not escalate.
   - Not found → the block is written in this exact form: *"searched the decision log and the offer
     material, no answer exists for X"*. A block written any other way is not written. Then **offer `ask`**, so
     the open question gets an owner and a date instead of living only in a message.

### `ask` — record an open question

1. Collect: the question; its **owner** (who decides — a stakeholder role or name); its **needed-by** date
   (`YYYY-MM-DD`, the day from which it blocks); the changes it affects; optionally a **context** in business
   words (the options seen and the effect of waiting — the sponsor page shows it under the question).
   Without an owner or a needed-by date, refuse and name the missing field; never invent either.
2. Reserve the id with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-id.py" next Q`.
3. Append the row to `{ops_repo}/docs/spec/questions.md` (`| ID | Question | Owner | Needed by | Changes | Context
   | State | Resolved by |`, state `open`; the table is created on first use). `karvey_lib/questions.py` holds the
   format and the refusals.
4. **Answered** → record the answer with `log` as a `D-NN` that cites the `Q-NN`, then set the question's state to
   `resolved → D-NN` (and `Resolved by`). The row is never deleted.

### `show <D-NN>` — resolve a reference

Print the decision, what it superseded, what cites it (changes, specs, other decisions), and whether
anything in the repo contradicts it. Used by `karvey-requirements` when a requirement cites a decision
and by `karvey-checkpoint restore` before repeating an open question.

## Notes

- Works **with or without** the team layer: a single agent benefits from the registry just as much,
  and `cross` is worth it from the first week.
- `karvey-requirements` treats contradicting a linked decision as a blocking review-gate failure
  (`../karvey/rules/multi-agent.md`); this skill is where that link resolves.
- Never approves a gate on its own and never edits a change's phase.
- Shared ops repo: commit by explicit path (`git commit -- <paths>`).

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*

[^r-verification]: ../karvey/rules/verification.md — context only, not opened.
