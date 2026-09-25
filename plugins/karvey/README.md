# Plugin: karvey

The **Karvey** Method (stack-agnostic SDD) packaged as a Claude Code plugin.

- **Skills:** under `skills/` — **1 orchestrator + 13 phase skills (0–12) + 19 support skills = 33**. Auto-discovered and invoked as `/karvey:karvey-<name>`. Full catalog in the [repo README](../../README.md#skills-catalog-33).
- **Shared rules:** `skills/karvey/rules/` (pipeline, iteration loop, deploy workflow + branch hygiene, standards, team layer, verification…). Skills cite them relative to their own folder (`../karvey/rules/<rule>.md`); there are no local copies.
- **Hooks** (python ≥ 3.9): `hooks/hooks.json` registers the session hook and the dispatcher `hooks/karvey-hook.sh` (approval, protect-paths, prod-gate on by default; git-flow and plan-gate opt-in through `project.json:enforcement`; spec-write validator). The statusline is installed by hand. See `hooks/README.md`.
- **Orchestrator:** `/karvey:karvey [<change-id>]`.
- **Project upgrade** after a plugin update: the first startup asks once per clone; run `/karvey:karvey-upgrade` or `scripts/karvey-upgrade.py plan` any time ([repo README](../../README.md#upgrading-your-project)).

See the [repo README](../../README.md), `LICENSE`, `NOTICE` and `TRADEMARK.md`.
