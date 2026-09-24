# Rule: Multi-agent and multi-repo work

Karvey assumes by default one engineer + one AI agent working on one change. Real projects often have **several specialist agents** (designer, web, app, ops…) working in **several repos**, a **browser operator** agent, non-programmer agents (design, copy, legal), and **humans who execute** steps an agent must not or cannot run (IAM, deletions, cloud consoles). This rule defines the minimum shared contract so that work stays traceable across agents and repos. It is applied by the orchestrator and by the phase skills that cite it.

> Principle: **every cross-agent or cross-repo dependency is a pinned, verifiable reference in `spec.json`** — never an implicit "the other agent already did it".

## 1. Parent / child changes (cross-repo)

When one business change spans several repos (e.g. web + app + DNS + cloud IAM), create a **parent change** in the operations repo (the repo that holds decisions and coordination; usually `spec_repo`) and one **child change** per repo that has its own code, tests and deploy.

```json
"links": {
  "parent":   "{change-id}@{repo}",          // in each child; "" in the parent
  "children": ["{change-id}@{repo}", "..."]  // in the parent; [] in a child
}
```

- `karvey-init` asks whether the change belongs to a parent, and fills `links` on both sides (the parent's `children` is appended with the new child).
- The parent holds the PRD, the business decisions and the cross-repo acceptance criteria; the children hold the EARS requirements, code, tests and deploy of their repo and **trace to the parent PRD**.
- A parent reaches `deployed` only when every child is `deployed` (or explicitly descoped with a decision). The orchestrator shows the children's phases when showing a parent.

## 2. Business decisions (`D-NN`)

Business decisions live in the decision log of the operations repo, `{ops_repo}/docs/spec/decisions.md` (`D-NN` numbering, owned by `karvey-decisions`). A change links the decisions it depends on:

```json
"decisions": ["D-12@{ops-repo}", "D-31@{ops-repo}"]
```

- Each requirement that exists because of a decision cites it (`Traces to PRD: … · Decision: D-12`).
- A requirement that contradicts a linked decision is a blocking review-gate failure: a new decision is needed first, not a silent change.

## 3. Inputs from other agents (design, copy, legal)

Work produced by non-programmer agents is consumed as a **pinned input**, never as "the latest file":

```json
"inputs": {
  "design":        "{repo} {path} @{commit}",
  "design_system": "{repo} {path} @{commit}",
  "copy":          "{repo} {path} @{commit}",
  "legal":         "{repo} {path} @{commit}"
}
```

- Only the keys that apply are filled. `@{commit}` is the full or short SHA the consumer actually read.
- The consuming phase (requirements, design-graphic, impl) reads the input **at that commit**.
- When the source repo advances past the pinned commit, `karvey-health` flags it and `karvey-iterate` treats it as a `spec-gap` candidate: re-read the diff, decide whether it changes requirements, and ripple only the affected phases. Updating the pin is recorded in `revision_history`.

## 4. Approvals with a decision reference

Every approval gate records **who** approved and **where** that approval is written down:

```json
"approvals": {
  "requirements": { "generated": true, "approved": true,
                    "by": "{name}", "role": "human | ceo-delegate", "date": "YYYY-MM-DD", "ref": "D-NN" },
  "...": {},
  "prod": { "by": "{name}", "date": "YYYY-MM-DD", "ref": "D-NN" }
}
```

- `role: "ceo-delegate"` is valid only when a decision (`ref`) records that the human owner delegated that gate to a coordinating agent. The `prod` gate is **never** delegated to an agent.
- `approvals.prod` is mandatory before merging to the production branch (see `karvey-deploy`). It makes the human approval part of the repo history even where the git platform cannot enforce required reviewers (e.g. no GitHub Enterprise / branch protection).

## 5. Human-executed tasks (`[human]`)

A step the agent must not or cannot execute (IAM grants, destructive deletions, console-only settings, DNS at a registrar without API, payments) is a task with the `[human]` label:

```markdown
### F2.T3 [human] Grant the deploy service account the Firebase Hosting Admin role
**Executor:** {name / role}
**Command:** `{exact command or console path — copy-pasteable}`
**Verification:** `{read-only command whose output proves it worked}` → expected: {…}
**Rollback:** `{exact command to undo}`
**Executed:** {name} · {YYYY-MM-DD HH:MM} · evidence: {output / link}
```

- The agent **prepares** the command, verification and rollback; the human **executes**; the agent **verifies** with the read-only check.
- While waiting, the task is in state **`awaiting-human`** (team's tracker: a comment + the tool's tag/label; Markdown: `🙋 awaiting-human` in `PLAN.md`). Dependent tasks do not start. Independent tasks continue.
- A `[human]` task is done only when the verification output matches the expected result and it is recorded under **Executed**.
- Where possible, the command lives as a **versioned script** in the repo (e.g. `infra/iam/grant-deploy-sa.sh`) so what the human ran is reviewable (see `karvey-infra` / `karvey-test`: IAM binding verification as an infra test).

## 6. Change type `ops`

Some changes have no application code: IAM, DNS, secrets rotation, quota, cloud console configuration. They use:

```json
"type": "ops"   // default: "feature"; also "hotfix"
```

An `ops` change runs a short pipeline: `init → requirements (lite: the verifiable goal) → infra (command plan) → tasks ([human]/[Infra]) → execution → verification → archive`. It skips mockup, design-graphic and architecture unless the plan touches trust boundaries (then architecture's security section applies). Its "test" is the read-only verification of each step, recorded in `test_evidence.md`.

## 7. Hotfix lane

A production defect that must be fixed now (including one discovered during an E2E run in production) uses `"type": "hotfix"`. The lane is fast, **not** unrecorded:

- **Same PR contains all three:** the fix + the `BUG-NN` entry (tracker + `findings.md`) + the regression test that fails without the fix.
- Root cause is still investigated (`karvey-investigate` Iron Law), but may be recorded right after the fix if the incident is live; the incident reaches `RESUELTO` only with the regression test.
- Chained hotfixes on the same day are each a separate version (rev bump + CHANGELOG), and each one is appended to `revision_history` with its release version: `{ "date", "finding": "F-NN", "bug": "BUG-NN", "release": "x.y.z", "reason" }`.
- The prod gate (`approvals.prod`) still applies.

## 8. Documentation-only PRs

PRs that only touch docs/specs (`docs/**`, `*.md`, `spec.json`) are not exempt from CI, but they run a **light CI**: spec lint (valid JSON in every `spec.json`, required fields present, `links`/`inputs`/`decisions` well-formed, markdown links not broken). Build/test/deploy jobs are skipped by path filter. `project.json:docs_pr` declares who merges them:

```json
"docs_pr": { "ci": "spec-lint", "merged_by": "{name or role}" }
```

A docs-only PR never triggers a deploy.

## 9. Agent environment readiness

Each agent environment (a lab server, a laptop, a CI runner, a remote sandbox) must have the Karvey skills installed at the version the project expects. `karvey-health` checks it (see that skill) and prints the install instructions per environment when they are missing or outdated. An agent that cannot load a Karvey skill must say so instead of improvising the phase.

## Outside the method — user hooks

Approval markers with an expiry (e.g. a plan-gate marker valid for 2 h that agents cannot renew) belong to the **user's own hooks**, not to Karvey. How a human delegates approvals to a coordinating agent, or extends a marker's validity, is defined in the user's environment. Karvey only records the resulting approval (`approvals.<phase>.role` + `ref: D-NN`). See the note in `enforcement.md`.
