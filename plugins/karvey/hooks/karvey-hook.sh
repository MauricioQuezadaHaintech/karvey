#!/usr/bin/env bash
# Karvey hook dispatcher (architecture §1.3, wave1-hardening). bash 3.2 compatible.
#
#   karvey-hook.sh <prompt|pre-bash|pre-edit|post-edit|session> [--only <guard>] [--force-enabled]
#
# 1. Finds the interpreter: python3, then python if it is major version 3, then `py -3` (Windows).
# 2. With one: exec python "$ROOT/scripts/karvey_lib/karvey_hooks.py" <event> "$@" (stdin passes through).
# 3. Without one: applies each guard's fail mode (§3.2) with a bash-only classifier, then exits.
#    Harness contract: exit 0 = allow, exit 2 = block (reason on stderr). Critical output is ASCII.
#
# The guards are allow-stubs until batch 3 wires them (E1.F5.*); the no-python classifier follows
# the same registry and order, so a guard wired in Python is wired here in the same task.
EVENT="${1:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
LIB="$ROOT/scripts/karvey_lib/karvey_hooks.py"

find_python() {
  for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1 && \
       "$c" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
      printf '%s' "$c"; return 0
    fi
  done
  if command -v py >/dev/null 2>&1 && py -3 -c 'import sys' >/dev/null 2>&1; then
    printf 'py'; return 0
  fi
  return 1
}

PY="$(find_python)"
if [ -n "$PY" ]; then
  if [ "$PY" = "py" ]; then exec py -3 "$LIB" "$@"; fi
  exec "$PY" "$LIB" "$@"
fi

# ---------------------------------------------------------------- no python (§3.2 fail modes)
INPUT="$(cat)"

guards_for() {
  case "$1" in
    pre-bash)  echo "selftest protect-paths prod-gate git-flow plan-gate" ;;
    pre-edit)  echo "selftest protect-paths plan-gate" ;;
    post-edit) echo "spec-write pending-sync" ;;
    prompt)    echo "approval" ;;
    session)   echo "" ;;
    *)         return 1 ;;
  esac
}

# nopy_<guard>: return 2 (and print the reason) to block. Allow-stubs until batch 3:
# protect-paths (E1.F5.T1) and prod-gate (E1.F5.T6) block here; git-flow and plan-gate block
# when enabled; approval, spec-write and pending-sync stay open (no marker = the safe side).
nopy_selftest() {
  if [ "${KARVEY_HOOK_SELFTEST:-}" = "1" ]; then
    case "$INPUT" in
      *KARVEY-SELFTEST-BLOCK*)
        echo "[karvey] BLOCK selftest: KARVEY-SELFTEST-BLOCK found (diagnostic guard, no python)" >&2
        return 2 ;;
    esac
  fi
  return 0
}
nopy_stub() { return 0; }

# crude JSON string field extraction (no python, no jq): the first "<field>": "<value>", unescaped
json_field() {
  printf '%s' "$INPUT" | tr '\n' ' ' | sed -nE 's/.*"'"$1"'"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p' | head -1 |
    sed -e 's/\\"/"/g' -e 's#\\/#/#g' -e 's/\\\\/\\/g'
}

# protect-paths without python (§3.2): block any Bash command or Edit path naming the Karvey state
# dirs or the compat marker; an Edit under the plugin root.
nopy_protect_paths() {
  local subject needles n base
  if [ "$EVENT" = "pre-edit" ]; then subject="$(json_field file_path)"; [ -z "$subject" ] && subject="$(json_field notebook_path)"
  else subject="$(json_field command)"; fi
  [ -z "$subject" ] && return 0
  needles="karvey/approvals karvey/ledger .git/karvey"
  if [ -n "${KARVEY_COMPAT_MARKER:-}" ]; then base="${KARVEY_COMPAT_MARKER##*/}"; needles="$needles $base"; fi
  for n in $needles; do
    case "$subject" in *"$n"*)
      echo "[karvey] BLOCK protect-paths: approval comes only from the human's message (D-01) (no python)" >&2
      return 2 ;;
    esac
  done
  if [ "$EVENT" = "pre-edit" ]; then
    for base in "$ROOT" "${CLAUDE_PLUGIN_ROOT:-}"; do
      [ -z "$base" ] && continue
      case "$subject" in "$base"/*)
        echo "[karvey] BLOCK protect-paths: the plugin files are not edited from a session (no python)" >&2
        return 2 ;;
      esac
    done
  fi
  return 0
}

# The Karvey project root of the payload cwd (walk up no further than the git top level), or "".
karvey_root() {
  local d top
  d="$(json_field cwd)"; [ -z "$d" ] && d="${CLAUDE_PROJECT_DIR:-$PWD}"
  d="$(cd "$d" 2>/dev/null && pwd -P)" || return 0
  top="$(git -C "$d" rev-parse --show-toplevel 2>/dev/null || true)"
  while [ -n "$d" ]; do
    if [ -f "$d/docs/spec/project.json" ] || [ -d "$d/docs/spec/changes" ]; then printf '%s' "$d"; return 0; fi
    { [ -z "$top" ] || [ "$d" = "$top" ] || [ "$d" = "/" ]; } && return 0
    d="$(dirname "$d")"
  done
}

# enforcement.<key> is true in the working copy or on origin/<production> (grep, no JSON parser)
flag_on() {
  local root="$1" key="$2" prod
  grep -Eq '"'"$key"'"[[:space:]]*:[[:space:]]*true' "$root/docs/spec/project.json" 2>/dev/null && return 0
  prod="$(sed -nE 's/.*"production"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' "$root/docs/spec/project.json" 2>/dev/null | head -1)"
  [ -n "$prod" ] && git -C "$root" show "refs/remotes/origin/$prod:docs/spec/project.json" 2>/dev/null |
    grep -Eq '"'"$key"'"[[:space:]]*:[[:space:]]*true'
}

# plan-gate without python (§3.2): when enabled, block Edit/Write and the conservative regex over
# the raw command; the marker cannot be verified without python, so it does not count.
nopy_plan_gate() {
  local root cmd
  root="$(karvey_root)"
  if [ "$FORCE" != "1" ]; then [ -z "$root" ] && return 0; flag_on "$root" plan_gate_hook || return 0; fi
  if [ "$EVENT" = "pre-edit" ]; then
    echo "[karvey] BLOCK plan-gate: file edit, and the approval marker cannot be verified without python. Present the plan and wait for the human's approval." >&2
    return 2
  fi
  cmd="$(json_field command)"
  if printf '%s' "$cmd" | grep -Eiq '(^|[^0-9&>])>>?\|?[[:space:]]*([^&[:space:]/]|/([^d]|d[^e]|de[^v]))|\brm[[:space:]]+-[a-zA-Z]*[rR]|\bgit[[:space:]]+(clean|reset[[:space:]]+--hard|push[[:space:]].*(--force|-f\b))|\bsed[[:space:]]+-[a-zA-Z]*i|\btruncate\b|\bfind\b.*-(delete|exec)|\bdrop[[:space:]]+(table|database)|\bterraform[[:space:]]+destroy|\b(az|gcloud|kubectl)\b.*[[:space:]]delete\b'; then
    echo "[karvey] BLOCK plan-gate: command may write or destroy, and the approval marker cannot be verified without python. Present the plan and wait for the human's approval." >&2
    return 2
  fi
  return 0
}

FORCE=0
for a in "$@"; do [ "$a" = "--force-enabled" ] && FORCE=1; done
ONLY=""
prev=""
for a in "$@"; do [ "$prev" = "--only" ] && ONLY="$ONLY,$a"; prev="$a"; done

GUARDS="$(guards_for "$EVENT")" || { echo "[karvey] unknown hook event '$EVENT' (not blocking)" >&2; exit 0; }
for g in $GUARDS; do
  if [ -n "$ONLY" ]; then case ",$ONLY," in *",$g,"*) ;; *) continue ;; esac; fi
  case "$g" in
    selftest) nopy_selftest; rc=$? ;;
    protect-paths) nopy_protect_paths; rc=$? ;;
    plan-gate) nopy_plan_gate; rc=$? ;;
    *)        nopy_stub "$g"; rc=$? ;;
  esac
  if [ "$rc" -eq 2 ]; then exit 2; fi
done
exit 0
