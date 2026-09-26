---
name: karvey-deploy
description: Karvey phase 11 — releases the change through the pipeline with the human prod OK. Use after karvey qa. Triggers include "karvey deploy".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: <change-id>
---

# karvey-deploy

Pre-check: `[Unreleased]` is not empty, and the review is read from `docs/spec/changes/{change-id}/qa/`.

### Step 1 — 6-step checklist (before the first push)

Feature branch, CHANGELOG, everything committed, branch pushed, merged to integration, integration pushed.

### Step 2 — Push

```bash
INTEGRATION=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py" get branch_flow.integration --shell) || exit 3
git push origin "$INTEGRATION"
```

### Step 3 — Production

**2.4-bis** — living spec on the change branch: `karvey-spec-merge.py "{change-id}" --dry-run`.

**2.8-bis** — release gate before the PR: `karvey-release-gate.py check "{change-id}" --pr-body "$PR_BODY"`.

```bash
gh pr create --base "$P" --head "$INTEGRATION" --body-file "$PR_BODY"
```

The prod OK is recorded as a D-NN and in the PR; it is never a commit on integration. At deploy its text is in the PR body; at archive the D-NN is written on `chore/archive-{change-id}`.

Then the post-deploy verification against the contract in `infra.md`.
