---
name: karvey-context
description: Karvey support — read-only dashboard from karvey-context.py: changes, open work, approvals, deploy queue — whenever you ask where things stand. Triggers include "karvey context", "estado del proyecto karvey", "karvey status".
allowed-tools: Read, Bash, Glob, Grep
argument-hint: [--capability <name>] [--change <change-id>]
---

# Karvey Context

Load: _core.md

## Purpose

Quick, read-only view of the project: changes and their phase, open work, approvals, enforcement state,
calibration, and the deploy queue. The dashboard is a script; this skill runs it and relays the output.

> **Read-only.** Nothing here writes, deploys or runs git that alters state (no `commit`, `push`, `merge`,
> `fetch`, `pull`). To deploy, use `karvey-deploy`.

## Execution steps

### 1. Run the dashboard

```bash
C="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-context.py"
python3 "$C"                                   # overview, open-work, approvals, enforcement, close-report, calibration
python3 "$C" --change "{change-id}"            # approvals and enforcement of one change
python3 "$C" --section open-work               # one section (overview | open-work | approvals | enforcement |
                                               #   close-report | calibration | convergence)
python3 "$C" --json                            # one JSON envelope, for another tool
```

Relay the output as it is. Do not recompute phases, approvals or counts from `spec.json` by hand: when the
script reports a file as `unreadable` or `invalid`, show that line and point at
`karvey-state.py validate {file}`. Exit 4 means there is no `docs/spec/` (suggest `karvey-init`).

### 2. `--capability <name>` (living spec detail)

```bash
cat "docs/spec/specs/{capability}/spec.md"
grep -c "### Requirement:" "docs/spec/specs/{capability}/spec.md"
```

### 3. Deploy queue (optional, read-only)

The phase of each change comes from the overview (`deploying`, `deployed`). For versions and unreleased
commits per repo, read the top of each repo's `CHANGELOG.md` and, if local git is available, count what
integration holds that production does not (no `fetch`):

```bash
CFG="${CLAUDE_PLUGIN_ROOT}/scripts/karvey-config.py"
INTEGRATION="$(python3 "$CFG" get branch_flow.integration --shell)"
PRODUCTION="$(python3 "$CFG" get branch_flow.production --shell)"
git -C "$repo" log --oneline "$PRODUCTION..$INTEGRATION" 2>/dev/null | wc -l   # >0 ⇒ not yet released
```

Live branches follow `deploy-workflow`[^r-deploy-workflow] → Branch hygiene: absorbed into production → report "should be
deleted"; not absorbed → report, never delete.

### 4. Active sprint (if the tracker has sprints)

Resolve the tracker with `karvey-config.py resolve management`. When it is external and `sprints` is set,
read the active sprint (read-only) and show its task counts by logical state; otherwise say "not
applicable".

---
*Part of the Karvey™ Method — © HainTech, by Mauricio Quezada Ibáñez · Apache 2.0 · see `karvey/LICENSE` and `../karvey/TRADEMARK.md`.*

[^r-deploy-workflow]: ../karvey/rules/deploy-workflow.md — context only, not opened.
