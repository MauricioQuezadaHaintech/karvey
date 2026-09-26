---
name: karvey-retro
description: Karvey support — retrospective from the method's artifacts: flow metrics, findings by type and phase, estimate accuracy, judge cost, followed-up process actions — at the end of a cycle. Triggers include "karvey retro", "retrospectiva karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
disable-model-invocation: true
argument-hint: --from YYYY-MM-DD --to YYYY-MM-DD [--per-person]
---

# Karvey Retro — Retrospective on the method's artifacts

## Purpose

**CROSS-CUTTING SKILL of the Karvey Method.** It is a support layer, **NOT a phase**: it does not change
`spec.json:phase` or advance the cycle, and it can run at any time.

The retro learns from what the method itself recorded: the flow metrics of the period (lead time, cycle time
per phase, approval wait per gate, throughput, deploy frequency, change failure rate, time to restore, gate
rejection rate, automatic approvals), the findings by type and by the phase that found them, the estimate
accuracy and the judge cost. Every number comes from the change's own artifacts through a read-only script
(`karvey-context.py --metrics`), so two retros over the same period show the same numbers. The focus is
**improving the process, never blaming people**.

## Steps

### 1. Fix the period and read the metrics

The period is explicit: `--from` and `--to` (default: the 28 days before today, stated in the retro).
`--as-of` is the day the retro runs. Read the metrics as JSON and as the human table:

```bash
C="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-context.py"
python3 "$C" --metrics --from "{from}" --to "{to}" --as-of "{today}" --json   # per lane and total
python3 "$C" --metrics --from "{from}" --to "{to}" --as-of "{today}"          # the table for the retro file
```

Report a metric as the script prints it. A `n/a — {reason} ({change-id})` stays `n/a` with its reason in the
retro: it is never turned into 0 or into a guess.

### 2. Findings, estimate accuracy and judge cost

From the same output and the archived changes of the period:

- **Findings by type and phase:** count the `findings.md` rows of each change by `Type` (`bug`, `spec-gap`,
  `emergent`) and by the `Phase` column (which phase found them). A spec-gap found at QA costs more than one found
  at requirements: say where they cluster.
- **Estimate accuracy:** the `estimate_accuracy` metric (actual / estimate, 1.0 = on estimate), and the
  calibration proposal of `karvey-context.py --section calibration` when it makes one.
- **Judge cost and acceptance:** `judge_cost_usd` (per gate and per change; `estimated` is shown as such) and
  `judge_acceptance` per lens (routed / routed + rejected).

### 3. Follow up the previous actions

When a previous `docs/spec/retros/retro-*.md` exists, list **every** action it agreed with its current state,
read from `docs/spec/backlog.md` (`open`, `promoted`, `done`, …). An action the backlog no longer holds is
reported as `not found in backlog.md`, never dropped silently.

### 4. Agree the actions and record them

Present the retro and agree the actions with the team. Each agreed action becomes one `docs/spec/backlog.md` row
of type `process`, with the next free `BL-NN` (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-id.py" next BL`), the retro as its origin and an **owner** (a role or a person the
team names). An action without an owner is **asked for once**; if no owner is given, the action stays in the
retro file as `unowned` and **no backlog row is written for it**.

### 5. Store the retro

Write `docs/spec/retros/retro-{to}.md` with: the period and the exact commands of Step 1, the metrics table
(per lane and total), findings by type and phase, estimate accuracy, judge cost and acceptance, the follow-up of
the previous actions and the agreed actions with their `BL-NN` and owner. The retro file and the backlog rows
travel on a docs branch like any other spec change (`../karvey/rules/deploy-workflow.md`).

### 6. Optional: the per-person view (`--per-person`)

Only when the team explicitly asks for it with `--per-person`, add a section on the work history of each
repository in `project.json:repos`:

- Commits per author, frequency and the areas each person touched, as a signal for a conversation about load
  and focus, never as a ranking:

```bash
git -C "{repo}" shortlog -sne --since="{from}" --until="{to}" --no-merges
```

Without `--per-person`, no per-author analysis or ranking is printed.

## Hook into the cycle

This skill can close the cycle after `karvey-archive` as its learning step. It does not advance the phase:
`spec.json:phase` is the same before and after the retro.

## Privacy and tone

- Improvement, not blame: the metrics are signals for a conversation about the process.
- The per-person view is opt-in and never compares people.
- No data beyond what the retrospective needs.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
