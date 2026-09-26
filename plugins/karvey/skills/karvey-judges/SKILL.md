---
name: karvey-judges
description: Karvey support — independent clean-context judges per lens over one phase's artifacts, findings with citations into findings.md, cost logged — before the requirements, architecture and qa gates. Triggers include "karvey judges", "jueces karvey".
allowed-tools: Read, Write, Bash, Glob, Grep, Agent
argument-hint: <change-id> <requirements|architecture|qa> [--base REF]
---

# Karvey Judges — an independent verdict before the human gate

Load: _core.md, judges.md, judges/{phase}.md

## Purpose

**CROSS-CUTTING SKILL of the Karvey Method.** It is a support layer, **NOT a phase**: it never changes
`spec.json:phase`, never approves, never routes a finding and never edits an artifact. A phase skill calls it
after writing its artifact and **before** presenting its gate, so the human decides with an independent reading
in front of them. The contract (settings, closed inputs, the prompt template, the output contract) lives in
`../karvey/rules/judges.md`; the rubrics in `../karvey/rules/judges/{phase}.md`.

Judges are **advisory** by default (`project.json:judges.mode`). Their cost is measured, never capped.

## Steps

### 1. Resolve the closed inputs

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts"
python3 "$S/karvey-judges.py" inputs "{change-id}" "{phase}" --json
```

For `qa`, add `--base {integration branch}` so the diff of the change is written to a file.

- `lenses` empty → print the `status` line (`judges: none for lane patch`, `judges: disabled by project
  setting`, or `judges: phase not judged`) and return to the calling skill. Nothing else runs.
- `dropped:` lines → show them: an extra item never reaches a judge.
- At `qa` the list always contains `fiscal`, whatever the lane count.

### 2. Run one subagent per lens, in parallel

Start one `Agent` per lens **in the same message**, each with the prompt template of
`../karvey/rules/judges.md` filled with: the lens, that lens's section of the rubric, and the `inputs` paths.
Pass **file paths and the rubric text only** — never this session's conversation, reasoning or drafts.
The subagent may use Read, Grep and Glob only and edits nothing.

Model: when `cross_model` is `prefer` and another model family's CLI is available (the detection
`/karvey-second-opinion` uses), run that lens through it; otherwise run it on this model and declare it
intra-model in step 3. Say which, in one line.

Write each subagent's reply, as returned, to `{tmp}/{lens}.json` (a temporary directory outside the repo).
Do not copy the token count the runtime shows for a subagent into that file: `collect --transcript auto` reads it
from the session transcript itself (`source: runtime`); a `usage` the reply carries is kept only as
`agent-reported`, estimated.

### 3. Collect: filter, append findings, write the run records

```bash
python3 "$S/karvey-judges.py" collect "{change-id}" "{phase}" --results "{tmp}" --model "{model}" \
  --transcript auto [--intra-model] [--diff "{diff file from step 1}"] --json
python3 "$S/karvey-state.py" judge-run "{change-id}" "{phase}" --from "{tmp}/runs.json"
```

`collect` discards findings without a resolvable citation, sanitises the text, takes each judge's tokens from the
session transcript (exact) or else estimates them over the prompt and every closed input, and adds the kept findings to `findings.md` as `open` rows with origin
`judge:{lens}`. `judge-run` is the only `spec.json` write of the flow (the cost log). An invalid reply is
reported as `not run (invalid output)`; it is not retried silently.

### 4. Hand back to the calling skill

Print one line per lens — verdict, findings by severity, model, `intra_model`, discarded count — and the
Critical/High findings in full. Say where two judges disagree. Then return to the calling skill, which
presents its gate with these verdicts (`karvey-context.py --section gate` shows them too).

With `judges.mode: blocking`, `approve` refuses while an `open` Critical/High judge finding of this phase is
in `findings.md`; the way forward is `/karvey-iterate`, never editing the row.

## What this skill never does

- Route, close or rewrite a finding (that is `/karvey-iterate`: `accepted:{type} {ref}` or `rejected: {reason}`).
- Apply a judge's suggestion to an artifact.
- Give a judge anything outside the closed input list.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
