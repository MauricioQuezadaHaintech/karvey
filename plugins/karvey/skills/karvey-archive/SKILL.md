---
name: karvey-archive
description: Archive a completed change: merge spec-deltas into living specs, move to archive, close Epic in ClickUp. Triggers include "karvey archive", "archivar", "archive", "cerrar epic", "close epic", "merge specs".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: <change-id>
---

# Karvey Archive

## Purpose

Complete the change's lifecycle: merge spec-deltas into the living specs, archive the change directory, and close the Epic in ClickUp or mark it complete in PLAN.md.

## Execution steps

### Step 1 — Verify completeness

**When:** the change has already been deployed with `/karvey-deploy` (phase: deployed). Archive is PHASE 12 (the last) of the Karvey Method and runs AFTER the deployment.

Read `docs/spec/changes/{change-id}/spec.json`.

Verify:
- [ ] `phase = "deployed"` or `approvals.deploy.approved = true` — if not met, warn that the change still needs to be deployed with `/karvey-deploy` and stop.
- [ ] `approvals.tasks.approved = true`
- [ ] Tests executed (`docs/test_evidence.md` exists with entries for the change-id)
- [ ] QA review completed (`REVISION_PR_*_{date}.md` exists)
- [ ] No pending critical or high findings

If there are blockers: report and stop.

Since the deployment already happened (`/karvey-deploy`), create the production marker `docs/spec/changes/{change-id}/IMPLEMENTED` if it does not already exist. If for some reason the deploy did not complete, warn that it will be archived without the production marker.

### Step 2 — Read spec-deltas

Read all files `docs/spec/changes/{change-id}/specs/**/*.md`.

For each spec-delta, identify the operations:
- `## ADDED Requirements` → append to the living spec
- `## MODIFIED Requirements` → replace the block in the living spec
- `## REMOVED Requirements` → remove the block + leave a deprecation comment

### Step 3 — Merge deltas into living specs

For each affected capability, edit `docs/spec/specs/{capability}/spec.md`:

**ADDED:** Add to the end of the file:
```bash
cat >> docs/spec/specs/{capability}/spec.md << 'EOF'

{full block of the new requirement}
EOF
```

**MODIFIED:** Locate the requirement by name and replace the full block.
Search: `grep -n "### Requirement: {name}" docs/spec/specs/{capability}/spec.md`
Replace from that line to the next `### Requirement:` or end of file.

**REMOVED:** Locate the block and delete it, leaving a comment:
```markdown
<!-- Removed {date}: {reason from the spec-delta} -->
```

### Step 4 — Commit the spec merge

```bash
git add docs/spec/specs/
git commit -m "spec: merge deltas from {change-id}

- {capability}: ADDED {N} requirements, MODIFIED {N}, REMOVED {N}"
```

### Step 5 — Archive the change directory

```bash
TIMESTAMP=$(date +%Y-%m-%d)
mkdir -p docs/spec/changes/archive
mv docs/spec/changes/{change-id} docs/spec/changes/archive/${TIMESTAMP}-{change-id}
```

Verify:
```bash
ls -la docs/spec/changes/archive/${TIMESTAMP}-{change-id}
# change-id must no longer exist in docs/spec/changes/
```

```bash
git add docs/spec/changes/
git commit -m "chore: archive {change-id}

Spec deltas merged into living specs. Change archived."
```

### Step 6A — Close Epic in ClickUp (if management=clickup)

```
clickup_create_task_comment(epic_id,
  "✅ Epic completed and archived.\n\nSpec deltas merged into: docs/spec/specs/{capability}/spec.md\nArchived in: docs/spec/changes/archive/{date}-{change-id}\n\nDone with the Karvey Method")
clickup_update_task(epic_id, status="complete")
```

### Step 6B — Close PLAN.md (if management=markdown)

Update `docs/spec/changes/archive/{date}-{change-id}/PLAN.md`:
- General status: `✅ Completed and archived`
- Add a history entry: `| {date} | archive | Spec merged and archived |`

### Step 6C — Update spec.json

Update `docs/spec/changes/archive/{date}-{change-id}/spec.json`:
- Set `phase: "archived"` (transition from `deployed`).

### Step 7 — Validate living specs

```bash
grep -n "### Requirement:" docs/spec/specs/{capability}/spec.md
# Verify that the ADDED requirements appear
# Verify that the REMOVED ones are no longer there
```

### Step 7B — Update knowledge graph

Sync knowledge per `karvey/rules/knowledge-sync.md` (Obsidian if available; at minimum `/graphify docs/spec/ --update`) to reflect the spec-delta merge and the archiving.
The `--update` also removes from the graph the nodes of documents that were deleted (REMOVED requirements).

### Step 7C — Cycle retrospective (optional, recommended)

Once the specs are merged and the change archived, offer to close the cycle with a retrospective. It is **optional but recommended**, especially on large Epics or cycles that took several days.

Recommend running the cross-cutting skill `karvey-retro` to extract learnings from the cycle:
- **Velocity:** how long each phase took vs. the estimate, where the time went.
- **Test health:** coverage, flaky tests, recurring QA findings.
- **Opportunities:** detected technical debt, process improvements, risks for the next cycle.

```
Do you want to run the cycle retrospective with /karvey-retro {change-id}?
(optional — recommended to capture learnings on velocity, test health, and opportunities)
```

It is not blocking: if the user skips it, continue anyway with the final output.

### Step 7D — Post-release documentation (optional, recommended)

The internal living specs (`docs/spec/specs/`) were already merged in Step 3 — that is **not** touched here. This step is for the **user / project** documentation (READMEs, guides, Diataxis docs), which is distinct from the internal specs.

Recommend running the cross-cutting skill `karvey-docs` to, after the release:
- **Update stale docs:** detect and refresh project/user documentation that became outdated by what was shipped in this change.
- **Generate Diataxis docs:** create new documentation (tutorial / how-to / reference / explanation) for the delivered features, when applicable.

```
Do you want to update/generate the user documentation with /karvey-docs {change-id}?
(optional — recommended; it distinguishes user/project docs from the internal living specs that archive already merged)
```

It is not blocking: if the user skips it, continue anyway with the final output.

### Step 8 — Final output

```
✅ Change archived: {change-id}

Spec deltas merged:
  - docs/spec/specs/{capability}/spec.md
    - ADDED: {N} requirements
    - MODIFIED: {N} requirements
    - REMOVED: {N} requirements

Archived in: docs/spec/changes/archive/{date}-{change-id}
IMPLEMENTED: {yes / no — not marked}

Management: {Epic E{n} closed in ClickUp | PLAN.md marked complete}

Commits:
  - "spec: merge deltas from {change-id}"
  - "chore: archive {change-id}"

Optional final steps (recommended):
  - 🔁 Cycle retrospective:           /karvey-retro {change-id}
  - 📚 Post-release documentation:    /karvey-docs {change-id}

🏁 Full Karvey Method cycle finished for {change-id}
```


## Cycle closure

After archiving, **ask the user** whether they want to run the recommended optional final steps:
- `/karvey-retro {change-id}` — cycle retrospective.
- `/karvey-docs {change-id}` — post-release documentation (Diataxis / update docs).

With this, the change's cycle is closed. For a new change: `/karvey-grill` or `/karvey-init`.

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `karvey/TRADEMARK.md`.*
