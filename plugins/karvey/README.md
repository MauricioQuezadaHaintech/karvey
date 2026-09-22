# Plugin: karvey

The **Karvey** Method (stack-agnostic SDD) packaged as a Claude Code plugin.

- **Skills:** under `skills/` — **1 orchestrator + 13 phase skills (0–12) + 18 support skills = 32**. Auto-discovered and invoked as `/karvey:<skill>`. Full catalog in the [repo README](../../README.md#skills-catalog-32).
- **Shared rules:** `skills/karvey/rules/` (pipeline, iteration loop, deploy workflow + branch hygiene, standards, team layer, verification…). Phase skills keep local copies of the rules they need under their own `rules/`.
- **Hooks active on install:** `hooks/hooks.json` registers a `SessionStart` hook (`karvey-session-context.sh`) that reinjects the agent handoff and reports repo drift; inert in projects without a handoff. `hooks/karvey-statusline.sh` must be installed by hand (a plugin cannot declare a statusline) — see `hooks/README.md`.
- **Opt-in enforcement hooks:** `skills/karvey/hooks/` (`git-flow-guard.sh`, `plan-gate.sh`) — `karvey-guard --install` installs them per project; they are NOT activated when installing the plugin.
- **Orchestrator:** `/karvey:karvey [<change-id>]`.

See the [repo README](../../README.md), `LICENSE`, `NOTICE` and `TRADEMARK.md`.
