---
name: karvey-init
description: Karvey phase 1 — creates a change (prd.md, spec.json, PLAN.md). Use to start a new Karvey change. Triggers include "karvey init".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion
argument-hint: <change-id>
---

# karvey-init

Create the change with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" init {change-id}`.
