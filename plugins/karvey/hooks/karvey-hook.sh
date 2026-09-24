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

GUARDS="$(guards_for "$EVENT")" || { echo "[karvey] unknown hook event '$EVENT' (not blocking)" >&2; exit 0; }
for g in $GUARDS; do
  case "$g" in
    selftest) nopy_selftest; rc=$? ;;
    *)        nopy_stub "$g"; rc=$? ;;
  esac
  if [ "$rc" -eq 2 ]; then exit 2; fi
done
exit 0
