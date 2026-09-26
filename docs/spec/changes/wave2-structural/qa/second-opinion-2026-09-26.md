# Second opinion (QA Dimension 7) — wave2-structural, 2026-09-26

- **Reviewer:** a clean-context subagent of the **same model family** as the main QA (intra-model, declared: no
  other family's CLI is installed and client projects' keys are never used for internal work). Adversarial mode.
- **Input:** `git diff origin/feature/wave1-hardening...HEAD` at `db870a9`, the change's requirements,
  architecture and findings; asked to attack the fixes of `6287d5b` and the approval / release paths.
- **Verdict: FAIL** (before the fixes of `aec40dc`).

The reviewer's findings, verbatim in substance, with the main QA's decision:

| # | Sev | Finding (reviewer) | Decision |
|---|---|---|---|
| 1 | High | A project-wide prod marker records prod for every change: `approve-gate … release` never consumes it, and it falls back to `_project` — the defect Wave 1 fixed as BUG-41 | accepted for the release gate and `approve prod` → BUG-70 (F-41); for `approve prod --manifest` the main QA keeps one approval for the manifest (REQ-W2-052) — **open as F-61 for the owner** |
| 2 | Medium | `--passWithNoTests` makes the redaction hide the next argument (a test path), so the trace sees the test as not run | accepted → BUG-71 (F-42) |
| 3 | Medium | Under `schema.strict: blocking`, the missing-lane error advises `lane set`, refused outside init | accepted → BUG-72 (F-43) |
| 4 | Medium | `deployed --attested` accepts any existing D-NN and any https URL, no marker | deferred → F-44 |
| 5 | Medium | The prod-gate reads each manifest change's QA state from the working tree, not from the head | deferred → F-44 |
| 6 | Low | A code commit can carry the trailer of an archived QA-approved change | deferred → F-44 |
| 7 | Low | A window between rename and link in the BUG-60 stale-lock takeover | deferred → F-45 |
| 8 | Low | Any repeat `generated` releases the BUG-81 hold | deferred → F-45 (the human still answers the gate) |
| 9 | Low | `-y` approves QA without a marker | accepted as designed (REQ-W2-040) → F-45 |
| 10 | Info | Checked and correct: BUG-62 `is_raise`, BUG-63 cluster parsing (`-am`, `-sF`, `-Cx`, `-uno`), BUG-52 connection failure as 5xx, BUG-61 NaN / infinity refusal | — |

The reviewer ran the unit suite on the tree it reviewed (1094 tests OK); that run is not in `evidence.jsonl` (it
was the reviewer's own read-only check). The main QA's own runs are cited in the review.
