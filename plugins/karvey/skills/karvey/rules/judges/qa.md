# Judge rubric: qa

Inputs: the diff of the change (a file written by `karvey-judges.py inputs`), `qa/REVISION_PR_*.md`,
`spec.json:goal`. Each lens answers its questions with findings that cite a line of these files.

## Lens: fiscal

One question: **list every claim of the review that has no evidence**. Evidence is a command output with an
`evidence.jsonl` line, a CI run for the reviewed commit, or a `file:line` of the diff. A claim such as "tests
pass", "no security issue" or "backwards compatible" without one of them is a finding (severity High when the
claim supports an approval). The fiscal runs at every `qa` gate, before `approve qa`.

## Lens: security

- Does the diff introduce a value that reaches a shell, a query, a path or an approval without a check?
- Does it add a secret, a credential, a personal datum or an absolute personal path?
- Does it weaken a guard, a permission or a fail-closed default?
- Does the review's security dimension cite the tool output it relies on, and what does the diff show that no
  tool would catch?
