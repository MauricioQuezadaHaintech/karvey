---
name: karvey-archive
description: Karvey phase 12 — on chore/archive-{id}: records the release, checks the living spec, archives the change, closes the Epic, knowledge sync. After karvey-deploy. Triggers include "karvey archive", "archivar con karvey", "cerrar epic karvey".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: <change-id>
---

# Karvey Archive

## Purpose

PHASE 12, the last: after `/karvey-deploy`, close the change's lifecycle on its own docs branch — record the release in `spec.json`, check that the living specs already hold the spec-delta (merged before production; a legacy leftover is merged here), archive the change directory, close the Epic in the team's tracker (`../karvey/rules/management-adapters.md`) or in `PLAN.md`, and run the knowledge sync. Nothing is committed on the integration or production branch (`../karvey/rules/state-machine.md`, D-03).

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py"
C="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py"
P="$(python3 "$C" get branch_flow.production --shell)"
```

## Execution steps

### Step 0 — Archive branch first

Before any edit or commit:
```bash
git fetch origin
git checkout -b "chore/archive-{change-id}" "origin/$P"
```

### Step 1 — Verify completeness

`python3 "$S" next "{change-id}" --json` must show the change in `deploying` with every gate before it approved or skipped (`invalid` → show the errors and stop). Also verify:
- [ ] Tests executed: `docs/test_evidence.md` has entries for the change.
- [ ] QA review in `docs/spec/changes/{change-id}/qa/`, no pending critical or high finding.
- [ ] `findings.md` converged: no `open`/`routed` `bug` or `spec-gap` (`../karvey/rules/iteration-loop.md`).
- [ ] No Task or Feature of the change left in `review` in the tracker; list any that remain and stop until QA moves them.

Blockers → report and stop.

### Step 2 — Record the release in spec.json

1. **Deployed**, with the evidence of the green production run and the canary from `karvey-deploy` (or the CI):
   ```bash
   python3 "$S" advance "{change-id}" deployed --pipeline-run "{run-url}" --post-deploy-check pass
   ```
   It is refused without a human prod approval in the release ledger.
2. **Prod approval copied into spec.json** from the ledger (or from the `D-NN` / PR URL that holds the human's OK):
   ```bash
   python3 "$S" approve "{change-id}" prod --write-spec
   ```
   Neither ledger nor D-NN / PR URL → **stop**: there is no recorded human prod OK to copy. If the `D-NN` is not yet in `docs/spec/decisions.md`, write it now from the PR text (who, when, the words verbatim).
3. Create the production marker `docs/spec/changes/{change-id}/IMPLEMENTED`.

### Step 3 — Check the living specs; merge only a legacy leftover

The spec-delta is merged **on the change branch, before the production PR** (`/karvey-deploy` step 2.4-bis), so
archive normally only moves and closes. Ask the read-only check first:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-spec-merge.py" "{change-id}" --check
```
- `merged` → nothing is merged again; go to Step 4.
- `unmerged` (a legacy change deployed before this rule; the ids are listed) → say so, then merge it here, on
  `chore/archive-{change-id}`, deterministic and never by hand — review the diff first, then apply:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-spec-merge.py" "{change-id}" --dry-run
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-spec-merge.py" "{change-id}"
  git add docs/spec/specs/ docs/spec/changes/ docs/spec/decisions.md
  git commit -m "spec: record release and merge deltas from {change-id}" -m "Karvey-Change: {change-id}"
  ```
- `conflict` → stop and route it through `/karvey-iterate` (the living spec and the delta disagree).
The capability comes from `spec.json:capability` (`--capability` overrides). ADDED is appended, MODIFIED replaces the block, REMOVED leaves a deprecation comment (`../karvey/rules/living-specs.md`).

### Step 4 — Archive the change directory

```bash
python3 "$S" advance "{change-id}" archived
TIMESTAMP=$(date +%Y-%m-%d)
mkdir -p docs/spec/changes/archive
git mv "docs/spec/changes/{change-id}" "docs/spec/changes/archive/${TIMESTAMP}-{change-id}"
git commit -m "chore: archive {change-id}"
```

### Step 5 — Close the Epic and calibrate

- Resolve the tracker: `python3 "$C" resolve management --change "{change-id}" --json` (missing status map → the one clause of `management-adapters.md`). `external` → `comment(epic, "✅ Archived: specs merged into docs/spec/specs/{capability}/spec.md, change in docs/spec/changes/archive/{date}-{change-id}")` and `set_status(epic, done)`: the Epic reaches `done` here, at archive. A failed call goes to the outbox (`karvey-config.py outbox add`); pending outbox entries are retried now. Otherwise update the archived `PLAN.md`: status `✅ Completed and archived` and a history row `| {date} | archive | Spec merged and archived |`.
- Calibration: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-context.py" --change "{change-id}" --section calibration` — relay the actual/estimate ratio per work type and any recalibration it proposes.

### Step 6 — Knowledge sync (here only)

The knowledge sync is optional and runs at archive and on demand, never per phase (`../karvey/rules/knowledge-sync.md`). Only when `project.json` declares `knowledge_sync: graphify` or `obsidian`: otherwise (absent or `none`) skip this step silently — it is not a missing step. When declared, sync the union of the paths queued in `.graph-pending` and `git diff --name-only "origin/$P"...HEAD` — e.g. `/graphify docs/spec/ --update` (without `--update` when there is no graph yet); `--update` also drops the nodes of deleted documents. Clear `.graph-pending` after a successful sync.

### Step 7 — Close the loop (sweeps and optional steps)

1. **Discovery backlog** (`../karvey/rules/backlog.md`): list the `open` items from this change; for each, with the user, **promote** (new change via `/karvey-grill` or `/karvey-init`, recording `seed_backlog_id`), **keep** or **discard** (with a reason); mirror the status to the tracker's backlog if there is one. Report the counts — never sweep silently.
2. **Branch sweep** (`../karvey/rules/deploy-workflow.md` → *Branch hygiene*): absorbed non-protected branches are deleted; not absorbed ones are listed for the human. Report the counts.
3. **Optional, recommended:** `/karvey-retro {change-id}` (velocity, test health, opportunities) and `/karvey-docs {change-id}` (user/project documentation — not the living specs, already merged). Ask with `AskUserQuestion`; not blocking.

### Step 8 — Docs-only PR

Push `chore/archive-{change-id}` and open one PR through the docs-only lane (`../karvey/rules/multi-agent.md` §8): light CI, no version bump, no deploy.

### Step 9 — Final output

```
✅ Change archived: {change-id}

Release recorded: deployed (run {url}) · approvals.prod ← {ledger | D-NN}
Spec deltas merged: docs/spec/specs/{capability}/spec.md — ADDED {N} · MODIFIED {N} · REMOVED {N}
Archived in: docs/spec/changes/archive/{date}-{change-id} · IMPLEMENTED: yes
Management: {Epic → done in {tool} | PLAN.md marked done} · outbox: {N} retried
Calibration: {ratio per work type | no proposal}
Knowledge sync: {graphify/obsidian updated ({N} paths) | none}
Branches swept: deleted {N} · kept {N} ({branch} — {reason})
Backlog swept: promoted {N} ({list}) · kept {N} · discarded {N}
PR: chore/archive-{change-id} → #{n} (docs-only)

Optional: 🔁 /karvey-retro {change-id} · 📚 /karvey-docs {change-id}
🏁 Karvey cycle finished for {change-id}. New change: /karvey-grill or /karvey-init.
```

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*
