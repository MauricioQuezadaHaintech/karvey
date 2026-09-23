#!/usr/bin/env bash
# Karvey session context — SessionStart hook (startup | resume | compact | clear).
#
# Brings a blank session back to being THIS agent:
#   1. identity, rules, board, checklist and handoff, reinjected;
#   2. the live repo state MEASURED and compared against what the handoff claims (state.json);
#   3. the instruction to run `/karvey-checkpoint restore` when there is something to restore.
#
# A hook cannot invoke a skill: it reinjects and measures, and the restore itself (crossing decisions,
# recreating scheduled tasks, proposing the next step) is the skill's job, told to the session here.
#
# Works with a SINGLE agent (docs/spec/agent/) and with a team (docs/spec/team.json or a legacy
# .ceo-agentes). With neither, it prints nothing — except, inside a Karvey project (docs/spec/project.json
# or docs/spec/changes/), a one-line notice when the team settings are missing — and exits 0.
set -u
exec 2>/dev/null

START="${CLAUDE_PROJECT_DIR:-$PWD}"
# absolute path: a relative CLAUDE_PROJECT_DIR made the dirname loops below spin forever on "."
START=$(cd "$START" 2>/dev/null && pwd -P) || exit 0
DIR="$START"; ROOT=""; CFG=""; KIND=""
while [ "$DIR" != "/" ] && [ -n "$DIR" ]; do
  if [ -f "$DIR/docs/spec/team.json" ]; then ROOT="$DIR"; CFG="$DIR/docs/spec/team.json"; KIND="team"; break; fi
  if [ -f "$DIR/.ceo-agentes" ];        then ROOT="$DIR"; CFG="$DIR/.ceo-agentes";        KIND="legacy"; break; fi
  if [ -d "$DIR/docs/spec/agent" ];     then ROOT="$DIR"; CFG="$DIR/docs/spec/agent";     KIND="solo"; break; fi
  DIR=$(dirname "$DIR")
done
# Team settings nudge (REQ-ADP-003): only inside a Karvey project (has docs/spec/), never elsewhere.
settings_nudge() {
  # Only a Karvey project: docs/spec/project.json or docs/spec/changes/ (a bare docs/spec/ can be an
  # OpenAPI folder, RFCs, a study). The root found above wins over walking up from the cwd.
  local d="${ROOT:-$START}" kp=""
  while [ -n "$d" ] && [ "$d" != "/" ]; do
    if [ -f "$d/docs/spec/project.json" ] || [ -d "$d/docs/spec/changes" ]; then kp="$d"; break; fi
    [ -n "$ROOT" ] && break
    d=$(dirname "$d")
  done
  [ -z "$kp" ] && return
  local pj="$kp/docs/spec/project.json" missing=""
  if [ ! -f "$pj" ]; then missing="no project.json"
  elif command -v python3 >/dev/null 2>&1; then
    missing=$(python3 -c "import json,sys
try: d=json.load(open(sys.argv[1],encoding='utf-8-sig'))
except Exception: print('project.json unreadable'); sys.exit()
if not isinstance(d,dict): print('project.json is not an object'); sys.exit()
print(' + '.join(k for k in ('notifications','management') if not isinstance(d.get(k),dict) or not d.get(k)))" "$pj")
  else missing="unknown: python3 not available to check"
  fi
  [ -n "$missing" ] && printf 'Karvey (info): team settings not set (%s). To set them, the user can run `/karvey:karvey-init --settings` — settings only, it creates no change and nothing in any tracker.\n' "$missing"
}

[ -z "$ROOT" ] && { settings_nudge; exit 0; }

REL="${START#"$ROOT"/}"; [ "$REL" = "$START" ] && REL=""
TOP="${REL%%/*}"
NAME=""; ROLE="solo"; PROFILE="$ROOT/docs/spec/agent"; BOARD="$PROFILE/board.md"

case "$KIND" in
  team)
    eval "$(python3 - "$CFG" "$TOP" "$(basename "$ROOT")" <<'PY'
import json, sys, shlex
try:    d = json.load(open(sys.argv[1], encoding='utf-8'))
except Exception: sys.exit(0)
roles = d.get('roles') or {}
# the session may start at the team root itself (TOP empty): then the root's own name is the key
role = roles.get(sys.argv[2]) or (roles.get(sys.argv[3]) if not sys.argv[2] else None) or 'ceo'
name = (d.get('display_names') or {}).get(role) or f"agent-{d.get('code','')}-{role}"
print(f"ROLE={shlex.quote(role)}"); print(f"NAME={shlex.quote(name)}")
print(f"OPS={shlex.quote(str(d.get('ops_repo','')))}")
PY
)"
    # ops_repo is a sibling repo under the team root — unless team.json lives inside the repo it names
    # (ops_repo = this repo, or empty): then the ops area is the folder that holds team.json (docs/spec/),
    # which is where karvey-checkpoint save writes agents/<role>/ and board/<role>.md.
    if [ -n "${OPS:-}" ] && [ "$OPS" != "$(basename "$ROOT")" ] && [ -d "$ROOT/$OPS" ]; then OPSDIR="$ROOT/$OPS"
    else OPSDIR=$(dirname "$CFG"); fi
    PROFILE="$OPSDIR/agents/${ROLE}"; BOARD="$OPSDIR/board/${ROLE}.md" ;;
  legacy)
    CODE=$(grep -E '^(CODIGO|CODE)=' "$CFG" | head -1 | cut -d= -f2-)
    OPS=$(grep -E '^OPS=' "$CFG" | head -1 | cut -d= -f2-)
    ROLE=$(grep -E "^(AGENTE|AGENT)_${TOP}=" "$CFG" | head -1 | cut -d= -f2-); [ -z "${ROLE:-}" ] && ROLE="ceo"
    NAME=$(grep -E "^(NOMBRE|NAME)_${ROLE}=" "$CFG" | head -1 | cut -d= -f2-); [ -z "${NAME:-}" ] && NAME="agent-${CODE}-${ROLE}"
    PROFILE="$ROOT/${OPS:-}/agents/${ROLE}"; BOARD="$ROOT/${OPS:-}/board/${ROLE}.md" ;;
esac
[ -z "$NAME" ] && NAME=$(basename "$ROOT")

HANDOFF="$PROFILE/handoff.md"; STATE="$PROFILE/state.json"

printf '=== Karvey — session context (%s) ===\n' "$KIND"
printf 'You are `%s`%s. Profile: %s\n' "$NAME" "$( [ "$ROLE" != "solo" ] && printf ' (role: %s)' "$ROLE" )" "$PROFILE"

emit() { [ -f "$1" ] && { printf '\n=== %s ===\n' "$2"; cat "$1"; }; }
if [ -f "$PROFILE/manifest-compact.md" ]; then emit "$PROFILE/manifest-compact.md" "Compact manifest"
else emit "$PROFILE/../manifest-compact.md" "Compact manifest"; fi
[ -d "$PROFILE" ] || printf '\n(profile directory not found: %s — nothing to reinject; run `/karvey-checkpoint save` to create it)\n' "$PROFILE"
[ -d "$PROFILE" ] && [ ! -f "$PROFILE/handoff.md" ] && printf '\n(no handoff at %s — the previous session did not save one)\n' "$PROFILE/handoff.md"
emit "$PROFILE/manifest.md"            "Manifest ($NAME)"
emit "$PROFILE/checklist.md"           "Closing checklist"
emit "$BOARD"                          "Board"
emit "$HANDOFF"                        "Handoff"

# --- the part a document cannot do: measure, and contrast ---
DRIFT=0
if [ -f "$STATE" ] && command -v python3 >/dev/null 2>&1; then
  printf '\n=== Live state vs. what the handoff claims ===\n'
  OUT=$(python3 - "$STATE" "$ROOT" <<'PY'
import json, subprocess, sys, os
try:    d = json.load(open(sys.argv[1], encoding='utf-8'))
except Exception:
    print("state.json unreadable — treat the handoff as unverified."); raise SystemExit(3)
root = sys.argv[2]; drift = False
def git(repo, *a):
    try:
        return subprocess.run(['git','-C',repo,*a], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ''
for r in d.get('repos', []):
    p = r.get('path','')
    rp = p if os.path.isabs(p) else os.path.join(root, p)
    if not os.path.isdir(os.path.join(rp, '.git')):
        print(f"  {p}: NOT FOUND at {rp} — the handoff describes a tree that is not here."); drift = True; continue
    br  = git(rp,'rev-parse','--abbrev-ref','HEAD')
    cm  = git(rp,'log','-1','--pretty=%h')
    un  = len([x for x in git(rp,'status','--porcelain').splitlines() if x])
    marks = []
    if br != r.get('branch'): marks.append(f"branch {r.get('branch')} -> {br}")
    if cm != r.get('commit'): marks.append(f"commit {r.get('commit')} -> {cm}")
    if un != r.get('uncommitted'): marks.append(f"uncommitted {r.get('uncommitted')} -> {un}")
    if marks:
        print(f"  {p}: DRIFT — " + " · ".join(marks)); drift = True
    else:
        print(f"  {p}: matches ({br} @{cm})")
if d.get('saved_at'): print(f"  saved_at: {d['saved_at']}")
if d.get('scheduled_tasks'): print(f"  scheduled tasks to recreate: {d['scheduled_tasks']} (they died with the reset)")
if d.get('ready_to_rotate'): print("  this agent had already declared itself ready to rotate.")
raise SystemExit(1 if drift else 0)
PY
); RC=$?; printf '%s\n' "$OUT"; [ "$RC" -ne 0 ] && DRIFT=1
elif [ -f "$HANDOFF" ]; then
  printf '\n(no state.json beside the handoff: nothing was measured, so treat every claim in it as unverified)\n'
  DRIFT=1
fi

ACTIVE=$(ls -1dt "$ROOT"/docs/spec/changes/*/ 2>/dev/null | head -1)
settings_nudge
printf '\n=== First action ===\n'
if [ -n "$ACTIVE" ] || [ "$DRIFT" -eq 1 ] || [ ! -f "$HANDOFF" ]; then
  printf 'Run `/karvey-checkpoint restore` BEFORE anything else'
  [ -n "$ACTIVE" ] && printf ' (active change: %s)' "$(basename "$ACTIVE")"
  printf '.\nIt contrasts the rest, crosses open questions against the decision log, recreates the\n'
  printf 'scheduled tasks and proposes the next step. A hook cannot do any of that.\n'
else
  printf 'Nothing pending to restore. Re-read the board before starting.\n'
fi
exit 0
