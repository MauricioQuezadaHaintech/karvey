#!/usr/bin/env bash
# Karvey hook dispatcher (architecture §1.3, wave1-hardening). bash 3.2 compatible.
#
#   karvey-hook.sh <prompt|pre-bash|pre-edit|pre-agent|post-edit|session> [--only <guard>] [--force-enabled]
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
    pre-agent) echo "subagent-prompt" ;;
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
nopy_protect_block() {
  echo "[karvey] BLOCK protect-paths: approval comes only from the human's message (D-01) (no python)" >&2
}
nopy_protect_paths() {
  local subject needles n base
  if [ "$EVENT" = "pre-edit" ]; then subject="$(json_field file_path)"; [ -z "$subject" ] && subject="$(json_field notebook_path)"
  else subject="$(json_field command)"; fi
  [ -z "$subject" ] && return 0
  needles="karvey/approvals karvey/ledger .git/karvey notify-last.json approvals/notify"
  if [ -n "${KARVEY_COMPAT_MARKER:-}" ]; then base="${KARVEY_COMPAT_MARKER##*/}"; needles="$needles $base"; fi
  for n in $needles; do
    case "$subject" in *"$n"*)
      echo "[karvey] BLOCK protect-paths: approval comes only from the human's message (D-01) (no python)" >&2
      return 2 ;;
    esac
  done
  # BUG-27: a glob or a variable that could expand to a protected directory name ("kar?ey", ".git/*/ledger",
  # ".git/$D/…"); a glob word needs 2+ literal characters, so a plain `*` is not enough
  if [ "$EVENT" = "pre-bash" ]; then
    local w lit hit=0
    set -f  # the words are patterns here, never expanded against the disk
    for w in $(printf '%s' "$subject" | tr ';&|<>()"'"'"'/' '          '); do
      case "$w" in *[*?[]*) ;; *) continue ;; esac
      lit="$(printf '%s' "$w" | tr -d '*?[]')"
      [ "${#lit}" -lt 2 ] && continue
      case karvey in $w) hit=1 ;; esac
      case ledger in $w) hit=1 ;; esac
      case approvals in $w) hit=1 ;; esac
    done
    set +f
    if [ "$hit" = 1 ]; then nopy_protect_block; return 2; fi
    if printf '%s' "$subject" | grep -Eq '\.git/(\$|\*/|\?)|/(\$[{]?[A-Za-z_][A-Za-z0-9_]*[}]?|\*)/(ledger|approvals)(/|$| )'; then
      nopy_protect_block; return 2
    fi
  fi
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

# git-flow without python (§3.2): when enabled, block every commit/push/merge/cherry-pick/revert/am
# and the manual deploys (the target branch cannot be resolved without python).
nopy_git_flow() {
  local root cmd
  root="$(karvey_root)"
  if [ "$FORCE" != "1" ]; then [ -z "$root" ] && return 0; flag_on "$root" git_flow_hook || return 0; fi
  cmd="$(json_field command)"
  if printf '%s' "$cmd" | grep -Eq '\bgit\b[^;&|]*[[:space:]](commit|push|merge|cherry-pick|revert|am)\b'; then
    echo "[karvey] BLOCK git-flow: cannot resolve the target repository without python; rewrite without variables or retry with python3 available" >&2
    return 2
  fi
  if printf '%s' "$cmd" | grep -Eq 'func +azure +functionapp +publish|az +webapp +up|config-zip|vercel .*--prod|netlify +deploy .*--prod|firebase +deploy|gcloud +(app|run) +deploy'; then
    echo "[karvey] BLOCK git-flow: manual deploy is forbidden; deploys run from the pipeline (no python)" >&2
    return 2
  fi
  return 0
}

# prod-gate without python (§3.2): fail closed. Any PR/MR merge is blocked (its base cannot be
# resolved); a git push is blocked when it names master/main/the production branch, has no
# refspec, or has a wildcard or matching (`:`) refspec (BUG-47). Off only if prod_gate_hook is false in the working copy AND on origin/<production>.
nopy_prod_gate() {
  local root cmd pj prod kind rest n w
  root="$(karvey_root)"; [ -z "$root" ] && return 0
  cmd="$(json_field command)"
  if printf '%s' "$cmd" | grep -Eq 'gh +pr +merge|az +repos +pr +update.*(completed|auto-complete)|glab +mr +merge|gh +api.*(pulls/[0-9]+/merge|mergePullRequest|enablePullRequestAutoMerge)'; then kind=pr
  elif printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]_-])git[^;&|]*[[:space:]]push([[:space:]]|$)'; then kind=push
  else return 0; fi
  pj="$root/docs/spec/project.json"
  prod="$(sed -nE 's/.*"production"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' "$pj" 2>/dev/null | head -1)"
  if grep -Eq '"prod_gate_hook"[[:space:]]*:[[:space:]]*false' "$pj" 2>/dev/null && [ -n "$prod" ] &&
     git -C "$root" show "refs/remotes/origin/$prod:docs/spec/project.json" 2>/dev/null |
       grep -Eq '"prod_gate_hook"[[:space:]]*:[[:space:]]*false'; then
    echo "[karvey] prod-gate DISABLED for this project (project.json)"
    return 0
  fi
  if [ "$kind" = "pr" ]; then
    echo "[karvey] prod-gate BLOCK change=? missing=python reason=cannot verify the production approval: python3 not available" >&2
    return 2
  fi
  if printf '%s' "$cmd" | grep -Eq "(^|[[:space:]:/+])(master|main${prod:+|$prod})([[:space:]]|\$|;|&|\|)"; then
    echo "[karvey] prod-gate BLOCK change=? missing=python reason=cannot verify the production approval: python3 not available (push to a production branch)" >&2
    return 2
  fi
  rest="${cmd#*push}"; rest="${rest%%[;&|]*}"; n=0
  # BUG-47: a wildcard or a matching (`:`) refspec can reach production without naming it
  if printf '%s' "$rest" | grep -Eq '\*|(^|[[:space:]])["'"'"']?\+?:["'"'"']?([[:space:]]|$)'; then
    echo "[karvey] prod-gate BLOCK change=? missing=python reason=cannot verify the production approval: python3 not available (wildcard or matching refspec)" >&2
    return 2
  fi
  set -f
  for w in $rest; do case "$w" in -*) ;; *) n=$((n+1)) ;; esac; done
  set +f
  if [ "$n" -lt 2 ]; then
    echo "[karvey] prod-gate BLOCK change=? missing=python reason=cannot verify the production approval: python3 not available (push without a refspec)" >&2
    return 2
  fi
  return 0
}

# spec-write without python (§3.2): open, one line
nopy_spec_write() {
  local f; f="$(json_field file_path)"
  case "$f" in
    */docs/spec/*spec.json|*/docs/spec/project.json|docs/spec/*spec.json|docs/spec/project.json)
      echo "[karvey] spec.json not validated: python3 not available ($f)" ;;
  esac
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
    prod-gate) nopy_prod_gate; rc=$? ;;
    plan-gate) nopy_plan_gate; rc=$? ;;
    git-flow)  nopy_git_flow; rc=$? ;;
    spec-write) nopy_spec_write; rc=$? ;;
    *)        nopy_stub "$g"; rc=$? ;;
  esac
  if [ "$rc" -eq 2 ]; then exit 2; fi
done
exit 0
