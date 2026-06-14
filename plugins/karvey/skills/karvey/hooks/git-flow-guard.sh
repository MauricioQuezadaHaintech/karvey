#!/usr/bin/env bash
# Karvey™ — git-flow-guard hook (PreToolUse on Bash)
# Blocks git behavior that skips the feature/* -> dev -> PR -> master flow.
# Template installed (opt-in) by karvey-init / managed by karvey-guard.
# Parameterized with docs/spec/project.json:branch_flow.
#
# Hook convention: receives the tool JSON on stdin. To BLOCK, print the reason
# to stderr and exit with code 2.
set -euo pipefail

# Defaults (overridable at install time, reading project.json:branch_flow)
INTEGRATION="${KARVEY_BRANCH_INTEGRATION:-dev}"
PRODUCTION="${KARVEY_BRANCH_PRODUCTION:-master}"
FEATURE_PREFIX="${KARVEY_FEATURE_PREFIX:-feature/}"

input="$(cat)"
# Extract the proposed bash command (jq if available; otherwise raw grep)
if command -v jq >/dev/null 2>&1; then
  cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty')"
else
  cmd="$(printf '%s' "$input" | grep -o '"command"[^,]*' | head -1)"
fi
[ -z "$cmd" ] && exit 0

block() { echo "🚫 [Karvey git-flow] $1" >&2; exit 2; }

# Manual deploy forbidden (CI/CD does it)
if printf '%s' "$cmd" | grep -Eq 'func +azure +functionapp +publish|az +webapp +up|vercel +--prod|netlify +deploy +--prod'; then
  block "Manual deploy forbidden. Deployment is triggered by the pipelines (push to $INTEGRATION / merge to $PRODUCTION)."
fi

# Direct push to the production branch
if printf '%s' "$cmd" | grep -Eq "git +push[^&|;]*\b$PRODUCTION\b"; then
  block "Direct push to '$PRODUCTION' blocked. Flow: $FEATURE_PREFIX* -> $INTEGRATION -> PR -> $PRODUCTION."
fi

# Commit while on dev/master (must be feature/*)
if printf '%s' "$cmd" | grep -Eq 'git +commit'; then
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
  if [ "$branch" = "$INTEGRATION" ] || [ "$branch" = "$PRODUCTION" ]; then
    block "Direct commit on '$branch' blocked. Work on a $FEATURE_PREFIX{change-id} branch."
  fi
fi

exit 0
