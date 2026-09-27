# Manual run: design-judge-gate — 2026-09-27

- **Script:** `plugins/karvey/tests/manual/design-judge-gate.md` (REQ-W3-037, REQ-W3-039)
- **Run by:** the maintainer agent, headless (`claude -p` with the branch plugin, `--setting-sources project,local`,
  step 2 by resuming the same session), owner-authorised pattern (D-19, D-21, D-28).
- **Setup:** a throw-away repo under the scratch dir (`git init -b main` + a bare origin); `project.json` with
  `targets: ["web"]`, `notifications.channel: none`, `management.tool: markdown`, judges at their defaults;
  `docs/spec/design-system.md` from `tests/unit/fixtures/design/`; change `sample-ui` (lane `feature-ui`) whose PRD
  asks for one "Late" status tag on an existing orders list and no assets. Shortcut: requirements and the mockup
  (`mockup/index.html`) were seeded as approved instead of being produced by the phase skills — the Expected lines
  concern only design-graphic and the gate summary.
- **Overall verdict:** **PASS** on the rerun of step 2 (BUG-95 fixed); step 1 passed in the first run.
- **First run:** FAIL (step 1 PASS; step 2 one Expected line not met).

## Step 1 — "Run design-graphic for sample-ui."

| Expected | Observed | Verdict |
|---|---|---|
| reads `docs/spec/design-system.md`, does not redefine its tokens | read; the delta adds only tokens absent from the system (`--space-2`, `--space-3`, `--radius-full`, `--text-xs`) and modifies none | PASS |
| `design-spec.md` first sentence `Applies to … mockup/index.html` | "Applies to `mockup/index.html`. …" | PASS |
| `design-delta.md` lists only the new tag (component; token only if new; `Base value` for modified) | Components: `Status pill · modified` ("Late" variant), `Table row · added` (on the screen, never recorded); 4 new tokens the mockup used as raw values; no modified token | PASS |
| `karvey-design.py diff sample-ui`, no `undeclared modification` | run; "finds no differences left undeclared" | PASS |
| `karvey-contrast-check.py --delta sample-ui --json` into `contrast.json`, cited | written; cited in the design-spec: "13 pairs × 2 schemes, 0 below level" | PASS |
| no score table, no `design-components.md`, `Art catalogue: not requested` | no score table; `ls` of the change: no `design-components.md`; "Art catalogue: not requested (the PRD says no illustrations, icons or other assets)" | PASS |
| `karvey-judges.py inputs sample-ui design_graphic --json` (one lens `design`; the delta, `mockup/index.html`, `contrast.json`) | run; `lenses: ["design"]`, `inputs` = exactly those three | PASS |
| one clean-context judge with Read, Grep and Glob only | one subagent; its prompt is the rule's template with `Allowed tools: Read, Grep, Glob` and "Do not edit any file"; the runtime subagent type was a general-purpose one, so the restriction is stated, not enforced | PASS (see note) |
| `karvey-judges.py collect … --transcript auto`; kept findings in `findings.md` with origin `judge:design` | `collect sample-ui design_graphic --results … --transcript auto`; F-01 High, F-02 Medium (`kind: risk` → `proposed risk`), F-03 Low, all `judge:design` | PASS |

The agent asked the one gate question at the end and recorded nothing.

## Step 2 — "Show me the what-gate summary before I answer."

| Expected | Observed | Verdict |
|---|---|---|
| `karvey-context.py --section gate --change sample-ui --gate what` | run | PASS |
| judge line for `design_graphic`: verdict, kept and discarded counts, model, tokens with their source | `judge design: concerns · High 1, Medium 1, Low 1 · model claude-sonnet-5 (intra-model)` and a separate `judge cost: 0.01 USD`. **No discarded count and no tokens with their source** on the line, although the run record holds `discarded: 0`, `tokens_total: 2648`, `source: estimate` | **FAIL** |
| `contrast:` section with pair count and pairs below level (or `0 below level`) | `contrast:` / `13 pair(s) × 2 schemes · 0 below level` | PASS |
| asks the one gate question; records nothing before the answer | the same three options repeated; `approvals.design_graphic` still pending | PASS |

## Notes

- The judge rubric (`rules/judges/design_graphic.md`) is cited in the design-graphic load list as "context only, not
  opened", but filling the judge template needs its text (`karvey-judges.py inputs` returns only its path), so the
  agent opened it and said so.
- The design-graphic skill text still names the mockup `mockup.html`; this setup used `mockup/index.html` (the name
  the judge inputs follow). The agent handled both.

## Defect (plugin)

**D2 — the gate summary's judge line omits discarded and tokens.** `plugins/karvey/scripts/karvey-context.py`
lines 964–970 format `judge {lens}: {verdict} · {counts} · model {model}{intra}` only. Expected (script): also the
discarded count and the tokens with their source. Proposed fix: append ` · discarded {n} · tokens {tokens_total}
({source})` from the run record (`n/a` when absent). Regression test idea (`test_context_gate.py`): a run record
with `discarded: 2`, `tokens_total: 2648`, `source: estimate` → the line contains `discarded 2` and
`tokens 2648 (estimate)`.

## Rerun after the fixes (2026-09-27)

Throw-away repo seeded at the end state of step 1 (design-system, delta, `contrast.json`, `findings.md` with three
`judge:design` rows and the judge run record: `discarded: 0`, `tokens_total: 2648`, `source: estimate`) — the
Expected lines concern only the summary. Prompt: "Show me the what-gate summary of sample-ui before I answer."

| Expected (step 2) | Observed | Verdict |
|---|---|---|
| `karvey-context.py --section gate --change sample-ui --gate what` | run | PASS |
| judge line: verdict, kept and discarded counts, model, tokens with their source | `judge design: concerns · High 1, Medium 1, Low 1 · 0 discarded · model model-a (intra-model) · 2648 tokens (estimate)` | PASS |
| `contrast:` with the pair count and pairs below level | `contrast:` / `13 pair(s) × 2 schemes · 0 below level` | PASS |
| asks the one gate question; records nothing before the answer | three options offered; `approvals.design_graphic` still `approved: false`; repo unchanged | PASS |
