---
name: karvey-archive
description: Karvey phase 12 — archives the change and merges its spec-delta. Use after karvey deploy. Triggers include "karvey archive".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: <change-id>
---

# karvey-archive

Start with `git checkout -b chore/archive-{change-id} origin/main`.

Read `docs/spec/changes/{change-id}/spec-delta.md`.

```bash
git commit -m "chore: archive" --trailer "Karvey-Change: {change-id}"
```

Sync the knowledge: `/graphify docs/spec/ --update`.
