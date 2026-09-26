# Rule: judges — an independent verdict before the human gate

A **judge** is a clean-context subagent that reads the artifacts of one phase through one **lens** and reports
findings with a `file:line` citation. Judges run before the human gate of the phases in `project.json:judges.phases`
(default: `requirements`, `architecture`, `qa`). They observe: they never route a finding, edit an artifact,
approve a phase or write a `spec.json` state field. The human still decides at the gate, with their verdicts in
the gate summary.

## Settings (`project.json:judges`)

| Key | Default | Meaning |
|---|---|---|
| `enabled` | `true` | `false` → the gate summary says `judges: disabled by project setting` |
| `mode` | `advisory` | `blocking` → `approve` refuses while a Critical/High judge finding of that phase is `open` |
| `phases` | `requirements`, `architecture`, `qa` | where judges run |
| `lenses` | per phase, below | which lens sections of the rubric run (an unknown lens is reported) |
| `per_lane` | `lanes.json` (`patch` 0, `standard` 2, `feature-ui` 3) | lenses per judged phase, integer ≥ 0 |
| `cross_model` | `prefer` | another model family when one is available; otherwise intra-model, declared |
| `budget` | — | ignored: judge cost is measured, never capped (D-30) |

Default lenses (`defaults.json:judges.lenses`, one section each in the phase's rubric):

- `requirements`: `domain`, `methods` — `judges/requirements.md`
- `architecture`: `security`, `methods`, `agents-cost` — `judges/architecture.md`
- `qa`: `fiscal`, `security` — `judges/qa.md`. The **fiscal** always runs at `qa`, whatever the lane count.

## Closed inputs

`karvey-judges.py inputs <change> <phase> --json` builds the list; nothing else is given to a judge:

- the phase's `produces` and `reads` from `state-machine.json` (architecture: `requirements.md`, `architecture.md`);
- `spec.json:goal`;
- the phase's rubric and the lens section;
- for `qa`: the diff of the change (written to a file) and `qa/REVISION_PR_*.md`.

A judge gets **file paths and the rubric text only**, never the author's conversation or reasoning. An extra
argument is dropped and listed as `dropped: {item} (not a phase input)`.

## The prompt template

Every judge is started with this template, filled with the lens, the rubric section and the input paths.

<!-- judge-template -->
```text
You are an independent reviewer of one phase of a software change, reading it through one lens: {lens}.
Rubric for this lens:
{rubric section}

Inputs (read only these files): {input paths}
Allowed tools: Read, Grep, Glob
Do not edit any file. Do not run commands. Do not propose patches or code.

Return exactly one JSON object and nothing else:
{"lens": "{lens}", "verdict": "pass|concerns|fail",
 "findings": [{"severity": "Critical|High|Medium|Low", "type_guess": "bug|spec-gap|emergent",
               "text": "one finding, at most 300 characters", "cite": "path:line"}]}
Every finding cites a line of one of the inputs; a finding without a citation is discarded.
```
<!-- /judge-template -->

## Output contract and collection

`karvey-judges.py collect <change> <phase> --results DIR --json` reads one JSON file per judge:

- an unparsable result is `not run (invalid output)`;
- a `cite` that does not resolve to an input file and a line within its length is discarded and counted;
- text is capped at 300 characters, `|`, control characters and newlines are escaped, code blocks and patches
  are stripped;
- cost is measured when the session transcript records the subagent's usage (`--transcript auto`: `source:
  runtime`, tokens exact); a `usage` the judge wrote itself is `agent-reported` and `estimated: true`; otherwise it is
  estimated over the prompt template and every closed input (characters ÷ 4 × `defaults.json:judge_price_table`,
  `source: estimate`, `estimated: true`).

Kept findings are appended to the change's `findings.md` as `open` rows with origin `judge:{lens}`, the phase,
the type guess and the severity. The per-judge run records (lens, model, `intra_model`, verdict, counts, tokens,
US$, `estimated`, discarded) go to `spec.json:judge_runs[]` through `karvey-state.py judge-run`, the only
`spec.json` write of the judge flow. `karvey-iterate` routes the rows like any other finding and records
`accepted:{type} {ref}` or `rejected: {reason}`, so the acceptance rate per lens is computable.
