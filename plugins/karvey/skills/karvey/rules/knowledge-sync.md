# Rule: Knowledge synchronization

Karvey can keep a knowledge graph of `docs/spec/` (and of the code) so later changes see earlier decisions and
dependencies. The mechanism is `knowledge_sync` in `docs/spec/project.json`, chosen once by `karvey-init`.

## Choosing the mechanism

| Value | When | Default |
|---|---|---|
| `obsidian` | an Obsidian MCP is available in the session (tools whose name contains `obsidian`) | — |
| `graphify` | graphify is installed | — |
| `none` | neither is available, or the team does not want a graph | yes, when graphify is not detected |

`karvey-init` says once which value it chose and why; `none` is a valid choice, not an error.

## When the sync runs: at archive and on demand only

The sync is **not** a step of each phase. Phases only accumulate what changed: the PostToolUse hook appends
every written path under `docs/spec/` to `docs/spec/.graph-pending` (sorted, deduplicated; it never records
itself or `graphify-out/`).

It runs:

1. **At archive** (`karvey-archive`), over `.graph-pending` ∪ the change's git diff, then `.graph-pending`
   is cleared.
2. **On demand**, when the user asks for it.

### `knowledge_sync = "obsidian"`
- Sync the created/modified documents to the vault via the Obsidian MCP (notes and their dependency links).
- If the Obsidian MCP fails, fall back to graphify when it is installed; otherwise report it and keep
  `.graph-pending` for the next run.

### `knowledge_sync = "graphify"`
- Run `/graphify docs/spec/ --update` over the pending set; the first time (no `graphify-out/`), without
  `--update`.
- Multi-repo: also in each repo of `project.json:repos` whose code the change touched.

### `knowledge_sync = "none"`
- Nothing runs; `.graph-pending` is still kept, so enabling a mechanism later can catch up.
