---
name: karvey-archive
description: Karvey phase 12 — archives the change and merges its spec-delta. Use after karvey deploy. Triggers include "karvey archive".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: <change-id>
---

# karvey-archive

Read `docs/spec/changes/{change-id}/spec-delta.md`.

Sync the knowledge: `/graphify docs/spec/ --update`.
