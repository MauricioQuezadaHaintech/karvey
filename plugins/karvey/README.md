# Plugin: karvey

The **Karvey** Method (stack-agnostic SDD) packaged as a Claude Code plugin.

- **Skills:** under `skills/` (12 phases + 12 support). They are auto-discovered and invoked as `/karvey:<skill>`.
- **Rules and hooks:** inside `skills/karvey/` (`rules/`, `hooks/`). The enforcement hooks (`git-flow-guard.sh`, `plan-gate.sh`) are **opt-in** — `karvey-guard --install` installs them per project; they are NOT activated when installing the plugin.
- **Orchestrator:** `/karvey:karvey [<change-id>]`.

See the [repo README](../../README.md), `LICENSE`, `NOTICE` and `TRADEMARK.md`.
