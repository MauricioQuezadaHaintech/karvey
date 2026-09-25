---
name: karvey-impl
description: Karvey phase 8 — implements tasks.md, one commit per task. Use after the tasks gate. Triggers include "karvey impl".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: <change-id>
---

# karvey-impl

Read `docs/spec/changes/{change-id}/tasks.md`.

Per task: add its line under `## [Unreleased]` in `CHANGELOG.md`; the version is not changed.

At review, record the actual with `log_time`; when the tool's `log_time` is `none`, fill the actual columns.

Select the first `todo` task; a dependency is satisfied at `review` or `done`.
