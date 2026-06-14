#!/usr/bin/env bash
# Karvey™ — Hook plan-gate (PreToolUse sobre Edit/Write/Bash destructivo)
# Exige plan aprobado en TODO el flujo: bloquea modificaciones si no hay marca de aprobación.
# Plantilla instalada (opt-in) por karvey-init / gestionada por karvey-guard.
#
# Override: tras presentar y aprobar el plan, crear la marca de aprobación
#   (por defecto: touch "$KARVEY_PLAN_FLAG"). El hook deja pasar mientras exista.
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

block() { echo "🚫 [Karvey plan-gate] $1 Presentá el plan, esperá aprobación y creá la marca: touch $FLAG" >&2; exit 2; }

# Si ya hay plan aprobado, dejar pasar.
[ -f "$FLAG" ] && exit 0

case "$tool" in
  Edit|Write|NotebookEdit)
    block "Cambio de archivos sin plan aprobado." ;;
  Bash)
    # Comandos destructivos sin plan
    if printf '%s' "$cmd" | grep -Eq '\brm +-rf?\b|\bDROP +TABLE\b|\bTRUNCATE\b|git +push +--force|git +reset +--hard|>[^>]'; then
      block "Comando destructivo sin plan aprobado."
    fi ;;
esac

exit 0
