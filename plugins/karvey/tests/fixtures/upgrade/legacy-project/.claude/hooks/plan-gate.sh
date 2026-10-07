#!/usr/bin/env bash
# Karvey™ — plan-gate (PreToolUse on Edit/Write/Bash) — DEPRECATED SHIM, removed in 4.0.0.
#
# Since 3.12.0 the plan-gate lives in the plugin's hook dispatcher (hooks/karvey-hook.sh →
# karvey_lib/guards.py) and is switched on per project with project.json:enforcement.plan_gate_hook.
# This file stays for 3.12.x so a project that copied it into its settings.json keeps the same
# behaviour — now with the H-10/H-11 fixes (stream redirections are not writes; git clean,
# find -delete, sed -i … are gated; the marker is scoped, expires and is created only by the
# approval hook from the human's own message, never by the agent). It execs the dispatcher with
# `--only plan-gate --force-enabled`. The old $KARVEY_PLAN_FLAG file is no longer honoured.
# `karvey-guard` detects this entry and proposes removing it.
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
  echo "[karvey] plan-gate shim: the Karvey plugin (hooks/karvey-hook.sh) was not found; not evaluated. Install the plugin or remove this entry from settings.json." >&2
  exit 0
}
INPUT="$(cat)"
case "$INPUT" in
  *'"tool_name"'*'"Bash"'*) EVENT=pre-bash ;;
  *) EVENT=pre-edit ;;
esac
printf '%s' "$INPUT" | exec bash "$D" "$EVENT" --only plan-gate --force-enabled
