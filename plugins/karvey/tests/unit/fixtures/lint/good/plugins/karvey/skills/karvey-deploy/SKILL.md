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

The prod OK is recorded as a D-NN and in the PR; it is never a commit on integration.
