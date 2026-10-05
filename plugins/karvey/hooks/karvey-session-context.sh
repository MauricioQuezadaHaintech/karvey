#!/usr/bin/env bash
# Karvey session context — SessionStart hook (startup | resume | compact | clear).
#
#   karvey-session-context.sh [startup|resume]    (hooks.json passes the matcher's source)
#
# With python 3 it delegates to `karvey_hooks.py session <mode>` (wave1-hardening E1.F6.T1: active
# change without archive/ or IMPLEMENTED, compact XOR full manifest, bounded board and handoff,
# hookSpecificOutput.additionalContext). Without python the bash code below is the degraded path.
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
MODE="${1:-startup}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
    exec "$c" "$HERE/../scripts/karvey_lib/karvey_hooks.py" session "$MODE" </dev/null
  fi
done
if command -v py >/dev/null 2>&1 && py -3 -c 'import sys' >/dev/null 2>&1; then
  exec py -3 "$HERE/../scripts/karvey_lib/karvey_hooks.py" session "$MODE" </dev/null
fi
# ---------------------------------------------------------------- no python: degraded bash path

START="${CLAUDE_PROJECT_DIR:-$PWD}"
# absolute path: a relative CLAUDE_PROJECT_DIR made the dirname loops below spin forever on "."
START=$(cd "$START" 2>/dev/null && pwd -P) || exit 0
CWD=$(pwd -P 2>/dev/null) || CWD="$START"
ROOT=""; CFG=""; KIND=""
# Team settings nudge (REQ-ADP-003): only inside a Karvey project (has docs/spec/), never elsewhere.
settings_nudge() {
  [ "$MODE" = "startup" ] || return 0   # REQ-W1-050: on session start only
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
  else
    printf 'Karvey (info): team settings could not be read (python3 not available). If they are missing, the user can run `/karvey:karvey-init --settings` — settings only, it creates no change and nothing in any tracker.\n'
    return
  fi
  [ -n "$missing" ] && printf 'Karvey (info): team settings not set (%s). To set them, the user can run `/karvey:karvey-init --settings` — settings only, it creates no change and nothing in any tracker.\n' "$missing"
}

# BUG-140 (REQ-HF-020, 021): the profile comes from the repo the session works in (its git top level), never
# from a folder above it and never by a default role; ambiguity injects nothing but one line. The 3.12.0 walk
# up the folder tree only decides whether that line is printed (elsewhere the hook stays silent).
old_walk() {
  local d="$1"
  while [ "$d" != "/" ] && [ -n "$d" ]; do
    if [ -f "$d/docs/spec/team.json" ] || [ -f "$d/.ceo-agentes" ] || [ -d "$d/docs/spec/agent" ]; then return 0; fi
    d=$(dirname "$d")
  done
  return 1
}
HIT=0; old_walk "$START" && HIT=1; old_walk "$CWD" && HIT=1
TO=""; command -v timeout >/dev/null 2>&1 && TO="timeout 2"
gtop() { local t; t=$($TO git -C "$1" rev-parse --show-toplevel 2>/dev/null | head -1); [ -n "$t" ] && (cd "$t" 2>/dev/null && pwd -P); }
rname() {
  local c b; c=$($TO git -C "$1" rev-parse --git-common-dir 2>/dev/null | head -1)
  case "$c" in "") basename "$1"; return ;; /*) ;; *) c="$1/$c" ;; esac
  c=$(cd "$c" 2>/dev/null && pwd -P) || { basename "$1"; return; }
  b=$(basename "$c")
  if [ "$b" = ".git" ]; then basename "$(dirname "$c")"; else printf '%s\n' "${b%.git}"; fi
}
not_loaded() {
  [ "$HIT" -eq 1 ] && printf '[karvey] profile not loaded: %s; run /karvey-checkpoint restore --profile <role|path> in the repo you work in.\n' "$1"
  settings_nudge
  exit 0
}
TS=$(gtop "$START"); TC=$(gtop "$CWD")
if [ "$TS" != "$TC" ]; then
  L=""
  for t in "$TS" "$TC"; do
    [ -n "$t" ] || continue
    n=$(rname "$t")
    if [ -d "$t/docs/spec/agent" ]; then L="${L:+$L, }solo ($n)"; else L="${L:+$L, }$n (no profile)"; fi
  done
  not_loaded "the session started in one repo and now works in another — candidates $L"
fi
[ -z "$TC" ] && not_loaded "the session's directory is not inside a git repository"
T="$TC"; N=$(rname "$T"); NC=0; L=""
if [ -d "$T/docs/spec/agent" ]; then NC=$((NC+1)); KIND="solo"; ROOT="$T"; CFG="$T/docs/spec/agent"; L="solo ($N)"; fi
d="$T"; TEAMCFG=""; LEGCFG=""
while [ "$d" != "/" ] && [ -n "$d" ]; do
  if [ -f "$d/docs/spec/team.json" ]; then TEAMCFG="$d/docs/spec/team.json"; break; fi
  if [ -f "$d/.ceo-agentes" ]; then LEGCFG="$d/.ceo-agentes"; break; fi
  d=$(dirname "$d")
done
[ -n "$TEAMCFG" ] && not_loaded "the team mapping in $TEAMCFG needs python3${L:+ (candidates $L, a team role)}"
LROLE=""
if [ -n "$LEGCFG" ]; then
  LROLE=$(awk -F= -v k="$N" '$1=="AGENTE_"k || $1=="AGENT_"k { print substr($0, index($0, "=") + 1); exit }' "$LEGCFG")
  if [ -n "$LROLE" ]; then
    NC=$((NC+1)); L="${L:+$L, }$LROLE ($N)"
    [ "$NC" -eq 1 ] && { KIND="legacy"; ROOT=$(dirname "$LEGCFG"); CFG="$LEGCFG"; }
  fi
fi
[ "$NC" -eq 0 ] && not_loaded "no profile claims the repo $N (no docs/spec/agent/ in it and no team mapping for its name)"
[ "$NC" -gt 1 ] && not_loaded "more than one profile claims the repo $N — candidates $L"

NAME=""; ROLE="solo"; PROFILE="$ROOT/docs/spec/agent"; BOARD="$PROFILE/board.md"
if [ "$KIND" = "legacy" ]; then
  CODE=$(grep -E '^(CODIGO|CODE)=' "$CFG" | head -1 | cut -d= -f2-)
  OPS=$(grep -E '^OPS=' "$CFG" | head -1 | cut -d= -f2-)
  ROLE="$LROLE"
  NAME=$(grep -E "^(NOMBRE|NAME)_${ROLE}=" "$CFG" | head -1 | cut -d= -f2-); [ -z "${NAME:-}" ] && NAME="agent-${CODE}-${ROLE}"
  PROFILE="$ROOT/${OPS:-}/agents/${ROLE}"; BOARD="$ROOT/${OPS:-}/board/${ROLE}.md"
fi
[ -z "$NAME" ] && NAME=$(basename "$ROOT")
# REQ-HF-022: here the profile always belongs to the working repo (solo: the repo itself; legacy: the role
# its own name maps to), so a sensitive handoff is the session's own.

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
def resolve(p):
    # '', '.' or the root's own name mean the root itself (team.json inside the repo it names) — BUG-20
    if p in ('', '.') or p.rstrip('/') == os.path.basename(root.rstrip('/')):
        cands = [root] + ([os.path.join(root, p)] if p not in ('', '.') else [])
    else:
        cands = [p] if os.path.isabs(p) else [os.path.join(root, p)]
    for c in cands:
        if is_repo(c): return c
    return cands[-1]
def is_repo(path):
    # a worktree has a .git FILE, not a directory — ask git instead of looking for .git/ (BUG-21)
    return os.path.isdir(path) and bool(git(path, 'rev-parse', '--git-dir'))
def rc(repo, *a):
    try:
        return subprocess.run(['git','-C',repo,*a], capture_output=True, timeout=10).returncode
    except Exception:
        return 1
PROFILE_FILES = ('state.json','handoff.md','board.md','manifest.md','checklist.md')
def profile_only_since(repo, recorded, profile_dir):
    # BUG-22: the recorded commit is an ancestor of HEAD and every path since it is a profile file
    # (the same rule as livestate.profile_only_since on the python path)
    if not isinstance(recorded, str) or not recorded or recorded.startswith('-'): return False
    if rc(repo, 'merge-base', '--is-ancestor', recorded, 'HEAD') != 0: return False
    top = git(repo, 'rev-parse', '--show-toplevel')
    if not top: return False
    rel = os.path.relpath(os.path.realpath(profile_dir), os.path.realpath(top))
    if rel == '..' or rel.startswith('..' + os.sep): return False
    allowed = {os.path.normpath(os.path.join(rel, f)).replace(os.sep, '/') for f in PROFILE_FILES}
    touched = set()
    for a in (('log','-z','--no-renames','--format=','--name-only',recorded+'..HEAD'),
              ('diff','-z','--no-renames','--name-only',recorded,'HEAD')):
        try:
            cp = subprocess.run(['git','-C',repo,*a], capture_output=True, text=True, timeout=10)
        except Exception:
            return False
        if cp.returncode != 0: return False
        touched.update(x.strip('\n') for x in cp.stdout.split('\0') if x.strip('\n'))
    return touched <= allowed
for r in d.get('repos', []):
    p = r.get('path','')
    rp = resolve(p)
    if not is_repo(rp):
        print(f"  {p}: NOT FOUND at {rp} — the handoff describes a tree that is not here."); drift = True; continue
    br  = git(rp,'rev-parse','--abbrev-ref','HEAD')
    cm  = git(rp,'log','-1','--pretty=%h')
    un  = len([x for x in git(rp,'status','--porcelain').splitlines() if x])
    marks = []; ru = r.get('uncommitted')
    po = br == r.get('branch') and cm != r.get('commit') and profile_only_since(rp, r.get('commit'), os.path.dirname(sys.argv[1]))
    if br != r.get('branch'): marks.append(f"branch {r.get('branch')} -> {br}")
    if cm != r.get('commit') and not po: marks.append(f"commit {r.get('commit')} -> {cm}")
    if un != ru and not (po and type(ru) is int and un <= ru): marks.append(f"uncommitted {ru} -> {un}")
    if marks:
        print(f"  {p}: DRIFT — " + " · ".join(marks)); drift = True
    elif po:
        print(f"  {p}: matches ({br} @{cm}; profile-only commits since the save)")
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

# the only change that is not archived and has no IMPLEMENTED marker (H-08; phases need python)
ACTIVE=""; NACT=0
for c in "$ROOT"/docs/spec/changes/*/; do
  [ -d "$c" ] || continue
  case "$(basename "$c")" in archive|.*) continue ;; esac
  [ -e "$c/IMPLEMENTED" ] && continue
  ACTIVE="$c"; NACT=$((NACT+1))
done
[ "$NACT" -ne 1 ] && ACTIVE=""
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
