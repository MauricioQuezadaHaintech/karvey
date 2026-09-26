---
name: karvey-qa
description: Karvey phase 10 — reviews the change in 9 dimensions and writes findings. Use after karvey test. Triggers include "karvey qa".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: <change-id>
---

# karvey-qa

QA observes only: every defect goes to `findings.md`; the review is written to `docs/spec/changes/{change-id}/qa/REVISION_PR_{n}_{date}.md`.

**Dimension 6: Versioning** — check that `[Unreleased]` has the change's lines and that the front reads the version file.

**Dimension 7: Second opinion** — another model.
