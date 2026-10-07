# PRD — project-upgrade

> Draft from the owner's request (D-20). Input for `karvey-requirements`; not approved yet.

## Problem
Updating the Karvey plugin changes skills, rules and hooks, but nothing brings an existing **project** up to
the new method: old `spec.json` / `project.json` shapes stay, legacy hook templates stay copied in the repo, the
statusline and the owner's global config stay behind, and new standards/controls never reach the project unless
someone knows which command to run. Today the only signal is one session notice for legacy team settings.

## Goal
Every time someone updates Karvey, the first session in a Karvey project **asks once** whether they want a
**project upgrade plan**; if yes, the agent shows a plan (dry-run first) and applies only what the person
approves, on a branch, through one PR.

## Owner's decisions
- D-20: request verbatim; ships in the release right after 3.12.0 (not in 3.12.0); asks each person, per clone.

## Key idea
The plan is computed from the **project's current state** against what the installed version expects, not from
a version diff. Coming from 3.0 or from 3.11 gives the same result: everything still pending.

## Out of scope
Upgrading the plugin itself (`claude plugin update`); re-running gates of changes in flight (reported only);
applying anything under `~/.claude/` (D-01, D-11: diffs shown, the owner applies).
