#!/usr/bin/env bash
# Karvey™ — plan-gate hook (PreToolUse on Edit/Write/destructive Bash)
# Requires an approved plan throughout the flow: blocks modifications if there is no approval marker.
# Template installed (opt-in) by karvey-init / managed by karvey-guard.
#
# Override: after presenting and approving the plan, create the approval marker
#   (default: touch "$KARVEY_PLAN_FLAG"). The hook lets things through while it exists.
set -euo pipefail

FLAG="${KARVEY_PLAN_FLAG:-/tmp/claude-plan-approved}"

input="$(cat)"
if command -v jq >/dev/null 2>&1; then
  tool="$(printf '%s' "$input" | jq -r '.tool_name // empty')"
  cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty')"
else
  tool="$(printf '%s' "$input" | grep -o '"tool_name"[^,]*' | head -1)"
  cmd="$(printf '%s' "$input" | grep -o '"command"[^,]*' | head -1)"
fi

block() { echo "🚫 [Karvey plan-gate] $1 Present the plan, wait for approval and create the marker: touch $FLAG" >&2; exit 2; }

# If a plan is already approved, let it through.
[ -f "$FLAG" ] && exit 0

case "$tool" in
  Edit|Write|NotebookEdit)
    block "File change without an approved plan." ;;
  Bash)
    # Destructive commands without a plan
    if printf '%s' "$cmd" | grep -Eq '\brm +-rf?\b|\bDROP +TABLE\b|\bTRUNCATE\b|git +push +--force|git +reset +--hard|>[^>]'; then
      block "Destructive command without an approved plan."
    fi ;;
esac

exit 0
