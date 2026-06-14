#!/usr/bin/env bash
# Karvey™ — Hook git-flow-guard (PreToolUse sobre Bash)
# Bloquea comportamiento git que se salte el flujo feature/* -> dev -> PR -> master.
# Plantilla instalada (opt-in) por karvey-init / gestionada por karvey-guard.
# Se parametriza con docs/spec/project.json:branch_flow.
#
# Convención de hooks: recibe JSON del tool por stdin. Para BLOQUEAR, imprime el
# motivo en stderr y sale con código 2.
set -euo pipefail

# Defaults (sobre-escribibles al instalar, leyendo project.json:branch_flow)
INTEGRATION="${KARVEY_BRANCH_INTEGRATION:-dev}"
PRODUCTION="${KARVEY_BRANCH_PRODUCTION:-master}"
FEATURE_PREFIX="${KARVEY_FEATURE_PREFIX:-feature/}"

input="$(cat)"
# Extraer el comando bash propuesto (jq si está disponible; si no, grep crudo)
if command -v jq >/dev/null 2>&1; then
  cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty')"
else
  cmd="$(printf '%s' "$input" | grep -o '"command"[^,]*' | head -1)"
fi
[ -z "$cmd" ] && exit 0

block() { echo "🚫 [Karvey git-flow] $1" >&2; exit 2; }

# Deploy manual prohibido (lo hacen los CI/CD)
if printf '%s' "$cmd" | grep -Eq 'func +azure +functionapp +publish|az +webapp +up|vercel +--prod|netlify +deploy +--prod'; then
  block "Deploy manual prohibido. El despliegue lo gatillan los pipelines (push a $INTEGRATION / merge a $PRODUCTION)."
fi

# Push directo a la rama de producción
if printf '%s' "$cmd" | grep -Eq "git +push[^&|;]*\b$PRODUCTION\b"; then
  block "Push directo a '$PRODUCTION' bloqueado. Flujo: $FEATURE_PREFIX* -> $INTEGRATION -> PR -> $PRODUCTION."
fi

# Commit estando en dev/master (debe ser feature/*)
if printf '%s' "$cmd" | grep -Eq 'git +commit'; then
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
  if [ "$branch" = "$INTEGRATION" ] || [ "$branch" = "$PRODUCTION" ]; then
    block "Commit directo en '$branch' bloqueado. Trabajá en una rama $FEATURE_PREFIX{change-id}."
  fi
fi

exit 0
