#!/usr/bin/env bash
# Karvey™ — git-flow-guard (PreToolUse on Bash) — DEPRECATED SHIM, removed in 4.0.0.
#
# Since 3.12.0 the git-flow guard lives in the plugin's hook dispatcher (hooks/karvey-hook.sh →
# karvey_lib/guards.py) and is switched on per project with project.json:enforcement.git_flow_hook.
# This file stays for 3.12.x so a project that copied it into its settings.json keeps the same
# behaviour — now with the H-12 fixes (target repository per segment, whole-name branch match,
# bare push, aliases). It execs the dispatcher with `--only git-flow --force-enabled`.
# `karvey-guard` detects this entry and proposes removing it (the plugin's hooks.json covers it).
#
# Branches come from project.json:branch_flow; outside a Karvey project the old variables
# KARVEY_BRANCH_INTEGRATION / KARVEY_BRANCH_PRODUCTION (default dev / master) still apply.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
find_dispatcher() {
  local c
  for c in "${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/hooks/karvey-hook.sh}" "$HERE/../../../hooks/karvey-hook.sh"; do
    [ -n "$c" ] && [ -f "$c" ] && { printf '%s' "$c"; return 0; }
  done
  c="$(ls -1dt "$HOME"/.claude/plugins/cache/*/karvey/*/hooks/karvey-hook.sh 2>/dev/null | head -1)"
  [ -n "$c" ] && { printf '%s' "$c"; return 0; }
  return 1
}
D="$(find_dispatcher)" || {
  echo "[karvey] git-flow-guard shim: the Karvey plugin (hooks/karvey-hook.sh) was not found; not evaluated. Install the plugin or remove this entry from settings.json." >&2
  exit 0
}
exec bash "$D" pre-bash --only git-flow --force-enabled
