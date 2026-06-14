# Rule: Knowledge synchronization across iterations

So that the method's iterations stay consistent (each phase knows the dependencies and decisions of the previous ones), Karvey maintains a knowledge graph. The mechanism depends on `knowledge_sync` in `docs/spec/project.json`.

## Choosing the mechanism

It is decided **once** in `karvey-init` and stored in `project.json`:

1. **Does the user have Obsidian with MCP integrated available in the session?**
   - Detect whether there are Obsidian MCP tools available (e.g. tools whose name contains `obsidian`).
   - If **yes** → `knowledge_sync = "obsidian"`.
   - If **no** → `knowledge_sync = "graphify"` (minimum, always).

> Golden rule: **never go without synchronization**. If Obsidian is not available, graphify is used as the minimum floor so dependency knowledge is not lost.

## Sync step (invoked at the end of each phase)

Every skill that produces or modifies documents in `docs/spec/` runs this step when it finishes:

### If `knowledge_sync = "obsidian"`
- Sync the created/modified documents to the vault via the Obsidian MCP (create/update the corresponding notes and their dependency links).
- If the Obsidian MCP fails or does not respond, **degrade to graphify** automatically so the update is not lost.

### If `knowledge_sync = "graphify"`
- Invoke `/graphify docs/spec/ --update` to reflect the created or modified documents.
- If `docs/spec/graphify-out/` does not exist (first time in the project), invoke `/graphify docs/spec/` without `--update`.
- In **multi-repo** projects: in addition to `docs/spec/`, run graphify in each repo of `project.json:repos` that had code changes in the current phase, to keep the code's dependency graph aligned with the spec.

## Summary

| Condition | Action |
|-----------|--------|
| Obsidian MCP available | Sync via Obsidian (fallback to graphify if it fails) |
| No Obsidian | `/graphify docs/spec/ --update` (guaranteed minimum) |
| Multi-repo with code changes | graphify also in the affected repos |
