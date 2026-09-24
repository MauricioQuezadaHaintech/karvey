---
name: karvey-deploy
description: Karvey phase 11 — releases the change through the pipeline with the human prod OK. Use after karvey qa. Triggers include "karvey deploy".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: <change-id>
---

# karvey-deploy

Pre-check: `[Unreleased]` is not empty.
