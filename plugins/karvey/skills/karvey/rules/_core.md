# Rule: the core — hard contracts every phase honours

Every phase skill loads this file first (`Load:` line, first entry). It states the seven contracts no phase may
break. Each has a stable id; `${CLAUDE_PLUGIN_ROOT}/schemas/contracts.json` maps every phase to the contracts that apply to it and
`karvey-context-budget.py contracts` proves each is still loaded.

**Load lists are closed.** A skill reads the rules and references on its `Load:` line and nothing else. A
citation in a footnote (`[^r-x]: x.md — context only`) is **never opened**: it tells a reader where a topic
lives, it is not an instruction to load it. When a step truly needs a rule that is not on the list, stop and say
so; the list is fixed by a spec revision, not at run time.

## State changes only through the state tool {#contract-state-tool}

- `phase`, `approvals`, `skipped`, `phase_history`, `risk_log` and `effort` in `spec.json` are written only by
  `karvey-state.py` (`generated`, `approve`, `approve-gate`, `advance`, `skip`, `reopen`, `outcome`, `risk`,
  `effort`). No skill edits them by hand and no skill keeps its own phase→next table.
- `karvey-state.py next {change-id}` says where a change is and what runs next. A refusal names the unmet
  phase and leaves the file byte-identical; the answer to a refusal is the missing step, never a hand edit.

## The gate and the approval {#contract-gate}

- One gate question per gate, asked once, after the phase-close actions and the judges. No second question
  about advancing follows an approval.
- Every approval records `--by`, `--role` and `--ref` (the `D-NN` or URL where the answer lives). An approval
  exists only when the human gave it; the agent never creates its own approval marker.
- `-y` means the agent records the answer as `--role auto` and continues; it is shown apart from human
  approvals and **never** records production.
- After the answer, the close steps run once through `karvey-close.py`; a failed step is reported and never
  reopens the gate.

## The production gate {#contract-prod-gate}

- Production needs the human's own words, recorded as a `D-NN` and in the release ledger
  (`karvey-state.py approve {change-id} prod --role human`). It is never delegated to another agent, never
  automatic, never recorded by `-y`, and never a commit on the integration or production branch.
- The PR's own gates (CI, branch policies) are green before the OK is requested. Bypassing a policy is the
  human's decision, never the agent's way to unblock itself. Deploys are triggered by the pipeline, never by
  hand.

## Branches and commits {#contract-branch-commit}

- Work happens on the change's feature branch (`branch_flow.feature_prefix` + id). Nothing is committed on
  the integration or production branch directly: they receive merges only, integration through a PR merged by
  the git host.
- Every commit of a change carries the trailer `Karvey-Change: {change-id}` and adds its line under
  `## [Unreleased]` in `CHANGELOG.md` (responsible human, AI model, the why). The version moves once per release,
  at deploy, never in a task commit.
- Commit by explicit paths; never sweep another session's work into your commit.

## Verification before a closing claim {#contract-verification}

State what you verified, not what you expect. A claim about a file, a resource or a deployment was verified in
this session, with a command, and its evidence is cited (`karvey-evidence.py` → `evidence.jsonl:{line}`). The
failure modes to check before saying "done":

1. **Citing is not verifying.** A message, comment or spec that names a thing does not prove it exists; where a
   control measures it, run the control.
2. **A green test over code nobody calls proves nothing.** Count the call sites of what the suite proves.
3. **"It failed" and "it never ran" look alike.** Check that each step produced something (duration, output,
   each link of a pipe); exit 0 is not success for every tool.
4. **A versioned file does not prove what is applied.** Settings and infrastructure are checked against the
   live resource, read-only.

A claim that cannot be verified is stated as unverified, with the reason, and never dropped.

## Findings go to the router {#contract-finding-router}

- Every observation from test, QA, browse or a judge is **appended** to the change's `findings.md` as
  `bug`, `spec-gap` or `emergent`. Who observes does not route and does not fix in place.
- Only `/karvey-iterate` routes a finding: a `bug` to the incident tracker and the QA micro-loop, a `spec-gap`
  back to requirements, an `emergent` item to the backlog. Nothing observed is dropped.

## Neutral public text {#contract-neutral-text}

Text that ships in the method or in public artifacts — skills, rules, examples, fixtures, translations, pages —
names no organisation, product, client or person as an actor, no internal URL or host, no home path, no id of
a real system and no secret. Examples use placeholders (`{change-id}`, `{name}`) or roles ("the owner",
"the reviewer").

[^r-state]: state-machine.md — the phase graph and the tool's commands; context only, not opened.
[^r-gates]: gates.md — the closing block in full; context only, not opened.
[^r-deploy]: deploy-workflow.md — the ordered deploy flow; context only, not opened.
[^r-verif]: verification.md — all eighteen failure modes; context only, not opened.
[^r-iter]: iteration-loop.md — the three feedback edges; context only, not opened.
