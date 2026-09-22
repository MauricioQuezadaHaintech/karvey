#!/usr/bin/env bash
# Karvey session context (OPTIONAL team layer) — SessionStart hook.
#
# Walks up from the session's directory looking for a team configuration
# (docs/spec/team.json, or a legacy .ceo-agentes). With it, it reinjects:
#   identity (who this agent is) + the compact manifest + this agent's handoff + its board.
#
# WITHOUT that configuration it prints NOTHING and exits 0: on a project with no team it is inert.
# Karvey works fully with a single agent; see karvey/rules/team.md before turning a team on.
set -u
exec 2>/dev/null

START="${CLAUDE_PROJECT_DIR:-$PWD}"
DIR="$START"
CFG=""; KIND=""
while [ "$DIR" != "/" ] && [ -n "$DIR" ]; do
  if [ -f "$DIR/docs/spec/team.json" ]; then CFG="$DIR/docs/spec/team.json"; KIND="json"; break; fi
  if [ -f "$DIR/.ceo-agentes" ];        then CFG="$DIR/.ceo-agentes";        KIND="legacy"; break; fi
  DIR=$(dirname "$DIR")
done
[ -z "$CFG" ] && exit 0

ROOT="$DIR"
# The role comes from the session's directory *relative to the team root*, not from the deepest folder.
REL="${START#"$ROOT"/}"; [ "$REL" = "$START" ] && REL=""
TOP="${REL%%/*}"

if [ "$KIND" = "json" ] && command -v python3 >/dev/null 2>&1; then
  eval "$(python3 - "$CFG" "$TOP" <<'PY'
import json, sys, shlex
try:
    d = json.load(open(sys.argv[1], encoding='utf-8'))
except Exception:
    sys.exit(0)
top = sys.argv[2]
role = (d.get('roles') or {}).get(top, 'ceo')
name = (d.get('display_names') or {}).get(role) or f"agent-{d.get('code','')}-{role}"
print(f"CODE={shlex.quote(str(d.get('code','')))}")
print(f"OPS={shlex.quote(str(d.get('ops_repo','')))}")
print(f"ROLE={shlex.quote(role)}")
print(f"NAME={shlex.quote(name)}")
PY
)"
else
  CODE=$(grep -E '^(CODIGO|CODE)=' "$CFG" | head -1 | cut -d= -f2-)
  OPS=$(grep -E '^OPS=' "$CFG" | head -1 | cut -d= -f2-)
  ROLE=$(grep -E "^(AGENTE|AGENT)_${TOP}=" "$CFG" | head -1 | cut -d= -f2-)
  [ -z "${ROLE:-}" ] && ROLE="ceo"
  NAME=$(grep -E "^(NOMBRE|NAME)_${ROLE}=" "$CFG" | head -1 | cut -d= -f2-)
  [ -z "${NAME:-}" ] && NAME="agent-${CODE}-${ROLE}"
fi

[ -z "${ROLE:-}" ] && exit 0
OPSDIR="$ROOT/${OPS:-}"
[ -d "$OPSDIR" ] || OPSDIR="$ROOT"

say() { [ -f "$1" ] && { printf '\n=== %s ===\n' "$2"; cat "$1"; }; }

printf '=== Karvey team context (SessionStart) ===\n'
printf 'You are `%s` (role: %s).\n' "$NAME" "$ROLE"
printf 'Board:   %s\n' "$OPSDIR/board/$ROLE.md"
printf 'Handoff: %s\n' "$OPSDIR/agents/$ROLE/handoff.md"
printf 'Names and refs are local to whoever lists them: introduce yourself in the first line of any\n'
printf 'message, and address whatever name YOUR own list shows right now (karvey/rules/team.md).\n'

say "$OPSDIR/agents/manifest-compact.md" "Compact manifest"
say "$OPSDIR/agents/$ROLE/handoff.md"    "Handoff ($ROLE)"

printf '\nRe-read your board (%s) and, if in doubt, %s.\n' "$OPSDIR/board/$ROLE.md" "$OPSDIR/MANIFESTO.md"
exit 0
