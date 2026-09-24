---
name: karvey
description: Karvey support — orchestrator of the Karvey method; shows the pipeline state and the next skill of a change. Use to start or resume a change. Triggers include "karvey", "karvey next".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [<change-id>]
---

# Karvey

```
PHASE 1 ── /karvey-init          → prd.md, spec.json
PHASE 2 ── /karvey-requirements  → requirements.md, spec-delta.md
PHASE 8 ── /karvey-impl          → code, one commit per task
PHASE 9 ── /karvey-test          → test evidence
PHASE 10 ── /karvey-qa           → review, findings
PHASE 11 ── /karvey-deploy       → release
PHASE 12 ── /karvey-archive      → living specs
```

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" next {change-id} --json` and relay `skill`.
