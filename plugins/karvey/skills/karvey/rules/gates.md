# Rule: gates — the one closing block of every phase skill

Every phase skill ends with **this block** (it cites this rule as its closing), and asks no
other question about advancing. There is **one gate question** per gate, never a second "shall we advance?" after
an approval. The phase-close actions 1–4 (`phase-close`[^r-phase-close]) run **before** the gate question.

## The three gates

Each approvable phase belongs to one gate (`${CLAUDE_PLUGIN_ROOT}/schemas/state-machine.json`, key `gate`):

| Gate | Phases | Records |
|---|---|---|
| *what* | requirements, mockup, design_graphic | `approve-gate {change} what` |
| *how* | architecture, infra, tasks | `approve-gate {change} how` |
| *release* | qa, prod | `approve-gate {change} release` — prod only through the production rule (below) |

Phases skipped by the lane or with a recorded `skip` are passed; the gate covers what is left.

## Which mode

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" gate "{change-id}" "{phase}" [--granular-gates] --json
```

It answers `mode` (`granular` | `merged`), `closes_gate` and `record_with`. The mode comes from
`project.json:gates` through the check-mode registry (`gates.merged`: 3.13 `granular`, 4.0 `merged`);
`--granular-gates` on a phase skill forces `granular` for that invocation; any other value is refused.

## The closing block

1. `karvey-state.py generated {change-id} {phase}` once the artifact is written.
2. **Granular** (or the phase closes its gate): run the judges when the phase is judged (`/karvey-judges`),
   print `karvey-context.py --section gate --change {change-id} --gate {gate}` (merged) or the phase summary
   (granular), then ask **one** `AskUserQuestion`:
   - *Approve and advance (recommended)* → record with `record_with` (`approve` or `approve-gate`), then run the
     skill that `karvey-state.py next {change-id}` names, **with no second question**.
   - *Approve and stop* → record the same way and stop; `next` says where to resume.
   - *Request changes* → `karvey-state.py outcome {change-id} {phase|gate} changes_requested --by --role --ref
     --reason "…"` (an empty reason is recorded as `no reason given`); the phase stays; re-run the skill that owns
     the requested artifact (for a merged gate, the earliest phase named in the reason, else the gate's first
     phase).
3. **Merged and the phase does not close its gate**: record `generated` and continue to the next phase of the
   gate. No question is asked.

Every approval records `--by`, `--role` and `--ref` (the `D-NN` or URL where the answer lives).

**After the answer is recorded** (approved or changes requested), run the close steps once:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-close.py" "{change-id}" "{phase}" --outcome approved|changes_requested \
  [--review-min N] --json
```

It builds and leak-checks the sponsor page, filters the notifications due through the sent-log, lists the risk
owners to ask at *qa* and *release*, records the phase's effort last and offers the checkpoint. Then only: send
the payloads it prints, verbatim (a failed send goes to the outbox); ask the listed owners and record each answer
with `karvey-state.py risk`. A failed step is reported; it never reopens the gate.

## Phases without a gate

`grill`, `init`, `impl`, `test` and `deploying` have no approval of their own. They end by stating what the
change needs next (`karvey-state.py next {change-id}`) — `/karvey-iterate` first when `findings.md` has an open
`bug` or `spec-gap` — and they continue into that skill only when the user's own request already covered the
chain; otherwise they stop there. They ask no "advance?" question: the next approval is a gate of its own.

## `-y`

`-y` means the agent records the answer itself: `--role auto`, and continues. It is shown apart from human
approvals in the dashboard and the metrics. `-y` **never records production**: the state tool refuses
`--role auto` on `prod`, and on the *release* gate when prod would be recorded (`production approval is never
automatic`). Production stays the human's own words (prod-kind marker, D-10), through `karvey-deploy`.

## Plan-rule exceptions are not gates

A question about an action outside the approved plan, or a change to production data, is asked on its own when
it arises, recorded with `outcome … --kind plan-exception`, and is not counted as a gate.

[^r-phase-close]: phase-close.md — context only, not opened.
