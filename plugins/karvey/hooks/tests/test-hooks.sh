#!/usr/bin/env bash
# Regression tests for the plugin hooks (BUG-01..04 in 3.11.2, BUG-18..19 in 3.11.3, BUG-20..21 in 3.11.4) and the
# wave1 dispatcher (E1.F4.T3: every hooks.json command run as written, no-python fail modes). Needs bash + python3.
# Run: bash plugins/karvey/hooks/tests/test-hooks.sh   → exit 0 if all pass. It is the entry point: it also runs
# every guard table (plugins/karvey/tests/hooks/run_tables.py) at the end.
set -u
H="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf '  ok   %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); printf '  FAIL %s\n       got: %s\n' "$1" "$2"; }
# Physical path: on macOS mktemp lives under /var, a symlink to /private/var, and the hook reports the
# resolved path (F-44).
T=$(cd "$(mktemp -d)" && pwd -P); trap 'rm -rf "$T"' EXIT
# Portable timeout: macOS has no timeout(1); perl's alarm is there on every runner (F-44).
to() { local s="$1"; shift; if command -v timeout >/dev/null 2>&1; then timeout "$s" "$@"; else perl -e 'alarm shift; exec @ARGV' "$s" "$@"; fi; }
ctx() { CLAUDE_PROJECT_DIR="$1" bash "$H/karvey-session-context.sh" 2>&1; }

echo "session-context: settings nudge (BUG-02)"
mkdir -p "$T/plain"; out=$(ctx "$T/plain");                      [ -z "$out" ] && ok "no docs/spec → silent" || bad "no docs/spec → silent" "$out"
mkdir -p "$T/openapi/docs/spec"; out=$(ctx "$T/openapi");        [ -z "$out" ] && ok "bare docs/spec (not Karvey) → silent" || bad "bare docs/spec → silent" "$out"
mkdir -p "$T/k1/docs/spec/changes"; out=$(ctx "$T/k1");          [[ "$out" == *"no project.json"* ]] && ok "changes/ without project.json → notice" || bad "changes/ without project.json" "$out"
mkdir -p "$T/k2/docs/spec"; echo '{"management":{"tool":"jira"}}' > "$T/k2/docs/spec/project.json"
# the nudge line itself (a jira block without location/statuses also gets the REQ-W3-059 "settings invalid" line)
out=$(ctx "$T/k2");                                               [[ "$out" == *"team settings not set (notifications)."* ]] && ok "missing notifications only" || bad "missing notifications only" "$out"
out=$(ctx "$T/k2");                                               [[ "$out" == *"settings invalid (management.location missing"* ]] && ok "incomplete management named (REQ-W3-059)" || bad "incomplete management named" "$out"
echo '{"management":"markdown","notifications":{"channel":"none"}}' > "$T/k2/docs/spec/project.json"
out=$(ctx "$T/k2");                                               [[ "$out" == *"management"* ]] && ok "management as legacy string → notice" || bad "legacy string" "$out"
echo '{"management":{},"notifications":{"channel":"none"}}' > "$T/k2/docs/spec/project.json"
out=$(ctx "$T/k2");                                               [[ "$out" == *"management"* ]] && ok "empty block counts as missing" || bad "empty block" "$out"
printf '\xef\xbb\xbf{"management":{"tool":"markdown"},"notifications":{"channel":"none"}}' > "$T/k2/docs/spec/project.json"
out=$(ctx "$T/k2");                                               [ -z "$out" ] && ok "BOM + complete settings → silent" || bad "BOM complete" "$out"
echo '[1]' > "$T/k2/docs/spec/project.json"; out=$(ctx "$T/k2"); [[ "$out" == *"not an object"* ]] && ok "non-object JSON → notice" || bad "non-object" "$out"
[[ "$(ctx "$T/k1")" == *"creates no change"* ]] && ok "notice says settings-only (BUG-01 guard)" || bad "notice wording" "$(ctx "$T/k1")"
( cd "$T" && out=$(CLAUDE_PROJECT_DIR=plain to 5 bash "$H/karvey-session-context.sh"; echo "rc=$?"); [[ "$out" == *"rc=0"* ]] && echo ok ) >/dev/null && ok "relative CLAUDE_PROJECT_DIR does not hang" || bad "relative dir" "timeout"

echo "hooks.json: every declared command runs as written (BUG-18, generalised)"
FIX="$(dirname "$H")/tests/fixtures/payloads"
python3 - "$H/hooks.json" > "$T/cmds.tsv" <<'PY'
import json, sys
for ev, groups in json.load(open(sys.argv[1]))["hooks"].items():
    for g in groups:
        for h in g["hooks"]:
            print("%s\x1f%s\x1f%s" % (ev, g.get("matcher", "") or "-", h["command"]))
PY
payload_for() {  # event matcher → a captured payload, cwd rewritten to $2
  case "$1:$3" in
    SessionStart:*)         f=session-start-startup.json ;;
    UserPromptSubmit:*)     f=user-prompt-submit.json ;;
    PreToolUse:Bash)        f=pre-tool-use-bash.json ;;
    PreToolUse:*)           f=pre-tool-use-edit.json ;;
    PostToolUse:*)          f=post-tool-use-write.json ;;
  esac
  [ -s "$FIX/$f" ] || { echo "MISSING-FIXTURE $f" >&2; return 1; }
  sed "s#/SCRATCH/proj#$2#g" "$FIX/$f"
}
N=$(wc -l < "$T/cmds.tsv" | tr -d ' ')
[ "$N" -ge 5 ] && ok "hooks.json declares $N commands (SessionStart, UserPromptSubmit, PreToolUse x2, PostToolUse)" || bad "hooks.json commands" "$N"
if grep -qF "'\${CLAUDE_PLUGIN_ROOT}" "$H/hooks.json"; then bad "no single-quoted CLAUDE_PLUGIN_ROOT (BUG-18)" "$(grep -nF "'\${" "$H/hooks.json")"; else ok "no single-quoted CLAUDE_PLUGIN_ROOT (BUG-18)"; fi
SP="$T/with space/plugin"; mkdir -p "$SP"; cp -R "$(dirname "$H")/hooks" "$(dirname "$H")/scripts" "$(dirname "$H")/schemas" "$(dirname "$H")/.claude-plugin" "$SP/"
US="$(printf '\037')"
while IFS="$US" read -r ev matcher cmd; do
  for root in "$(dirname "$H")" "$SP"; do
    out=$(cd "$T" && payload_for "$ev" "$T/plain" "$matcher" | CLAUDE_PLUGIN_ROOT="$root" CLAUDE_PROJECT_DIR="$T/plain" bash -c "$cmd" 2>&1; echo "rc=$?")
    label="$ev [$matcher] @ $( [ "$root" = "$SP" ] && echo 'path with spaces' || echo 'plugin root')"
    [[ "$out" == *"rc=0"* && "$out" != *"No such file"* && "$out" != *"MISSING-FIXTURE"* ]] && ok "$label runs as written" || bad "$label runs as written" "$out"
  done
done < "$T/cmds.tsv"
CMD=$(head -1 "$T/cmds.tsv" | cut -d "$US" -f3)
out=$(cd "$T" && CLAUDE_PLUGIN_ROOT="$T/missing space/plugin" bash -c "$CMD" 2>&1; echo "rc=$?")
[[ "$out" == *"missing space/plugin/hooks"* ]] && ok "a missing path with spaces stays one word" || bad "path with spaces" "$out"

echo "dispatcher: python path and no-python fail modes (§3.2)"
D="$H/karvey-hook.sh"
BASHBIN="$(command -v bash)"
NOPY="$T/nopy-bin"; mkdir -p "$NOPY"
for c in bash sh cat dirname grep sed tr head env; do p=$(command -v "$c") && ln -sf "$p" "$NOPY/$c"; done
disp() { ( cd "$T/plain" && printf '%s' "$2" | env -i HOME="$T" PATH="$1" ${3:+KARVEY_HOOK_SELFTEST=$3} "$BASHBIN" "$D" "$4" 2>&1; echo "rc=$?" ); }  # never the repo under test
LS='{"tool_name":"Bash","tool_input":{"command":"ls"},"cwd":"'"$T/plain"'"}'
TOK='{"tool_name":"Bash","tool_input":{"command":"echo KARVEY-SELFTEST-BLOCK"},"cwd":"'"$T/plain"'"}'
out=$(disp "$PATH" "$LS" "" pre-bash);        [[ "$out" == "rc=0" ]] && ok "python: pre-bash ls → allow, silent" || bad "python allow" "$out"
out=$(disp "$PATH" "$TOK" 1 pre-bash);        [[ "$out" == *"BLOCK selftest"*"rc=2" ]] && ok "python: a block exits 2 with the reason" || bad "python block" "$out"
out=$(disp "$PATH" "not json" "" pre-bash);   [[ "$out" == *"BLOCK protect-paths: cannot evaluate"*"rc=2" ]] && ok "python: non-JSON payload → protect-paths fails closed" || bad "python non-json" "$out"
out=$(disp "$PATH" '{"prompt":"ok","cwd":"'"$T/plain"'"}' "" prompt); [[ "$out" == "rc=0" ]] && ok "python: prompt outside a Karvey project → silent, no marker" || bad "python prompt" "$out"
out=$(disp "$PATH" "" "" nosuch);             [[ "$out" == *"unknown hook event"*"rc=0" ]] && ok "python: unknown event is not blocking" || bad "python unknown" "$out"
out=$(disp "$NOPY" "$LS" "" pre-bash);        [[ "$out" == "rc=0" ]] && ok "no python: pre-bash ls → allow by fail mode" || bad "nopy allow" "$out"
out=$(disp "$NOPY" "$TOK" 1 pre-bash);        [[ "$out" == *"BLOCK selftest"*"no python"*"rc=2" ]] && ok "no python: the classifier blocks (exit 2)" || bad "nopy block" "$out"
for ev in prompt post-edit pre-edit session; do
  out=$(disp "$NOPY" '{}' "" "$ev");          [[ "$out" == "rc=0" ]] && ok "no python: $ev → open (exit 0)" || bad "nopy $ev" "$out"
done
out=$(disp "$NOPY" "" "" nosuch);             [[ "$out" == *"unknown hook event"*"rc=0" ]] && ok "no python: unknown event is not blocking" || bad "nopy unknown" "$out"

echo "session-context: no python — one line, the fallback is not extended (F-85)"
nopyctx() { env -i HOME="$T" PATH="$NOPY" CLAUDE_PROJECT_DIR="$1" "$BASHBIN" "$H/karvey-session-context.sh" startup 2>&1; }
mkdir -p "$T/nopy-docs/docs/spec/changes" "$T/nopy-spec/spec/changes"
out=$(nopyctx "$T/nopy-docs"); [[ "$out" == *"spec/ folder detection and the settings-invalid check need python"* ]] && ok "no python, docs/spec project: the limitation line" || bad "nopy docs/spec line" "$out"
[ "$(printf '%s\n' "$out" | grep -c 'need python')" = 1 ] && ok "no python: the limitation is one line" || bad "nopy one line" "$out"
out=$(nopyctx "$T/nopy-spec"); [[ "$out" == *"need python"* && "$out" != *"team settings not set"* ]] && ok "no python, spec/ layout: the line, no detection (not extended)" || bad "nopy spec/ layout" "$out"
out=$(nopyctx "$T/plain"); [ -z "$out" ] && ok "no python, outside a Karvey project → silent" || bad "nopy plain" "$out"
out2=$(ctx "$T/nopy-docs"); [[ "$out2" != *"need python"* ]] && ok "with python: no limitation line" || bad "python no line" "$out2"

echo "session-context: team.json inside the repo (BUG-19)"
R="$T/myrepo"; mkdir -p "$R/docs/spec/agents/ceo" "$R/docs/spec/board"
echo '{"ops_repo":"myrepo","roles":{"myrepo":"ceo"},"display_names":{"ceo":"agente-x"}}' > "$R/docs/spec/team.json"
echo "MANIFEST-X" > "$R/docs/spec/agents/ceo/manifest.md"; echo "COMPACT-X" > "$R/docs/spec/agents/ceo/manifest-compact.md"
echo "HANDOFF-X" > "$R/docs/spec/agents/ceo/handoff.md"; echo "BOARD-X" > "$R/docs/spec/board/ceo.md"
out=$(ctx "$R")
[[ "$out" == *"Profile: $R/docs/spec/agents/ceo"* ]] && ok "profile resolves to docs/spec/agents/<role>" || bad "in-repo profile" "$out"
[[ "$out" == *"COMPACT-X"* && "$out" != *"MANIFEST-X"* && "$out" == *"HANDOFF-X"* ]] && ok "manifest-compact XOR manifest (REQ-W1-046), and handoff reinjected" || bad "in-repo reinjection" "$out"
[[ "$out" == *"agente-x"* ]] && ok "role from the root's own name when the session starts at the root" || bad "role at root" "$out"
rm "$R/docs/spec/agents/ceo/handoff.md"; out=$(ctx "$R")
[[ "$out" == *"no handoff at"* ]] && ok "missing handoff is said, not silent" || bad "missing handoff" "$out"
S="$T/team"; mkdir -p "$S/docs/spec" "$S/ops/agents/dev" "$S/app"
echo '{"ops_repo":"ops","roles":{"app":"dev"}}' > "$S/docs/spec/team.json"; echo "SIB-HANDOFF" > "$S/ops/agents/dev/handoff.md"
out=$(ctx "$S/app")
[[ "$out" == *"Profile: $S/ops/agents/dev"* && "$out" == *"SIB-HANDOFF"* ]] && ok "sibling ops repo layout still works" || bad "sibling layout" "$out"

echo "session-context: state.json paths (BUG-20) and worktrees (BUG-21)"
R2="$T/repoA"; mkdir -p "$R2/docs/spec/agents/ceo"; git -C "$R2" init -q -b main; git -C "$R2" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
echo '{"ops_repo":"repoA","roles":{"repoA":"ceo"}}' > "$R2/docs/spec/team.json"; echo H > "$R2/docs/spec/agents/ceo/handoff.md"
C=$(git -C "$R2" log -1 --pretty=%h)
for pth in repoA . ""; do
  printf '{"repos":[{"path":"%s","branch":"main","commit":"%s","uncommitted":0}]}' "$pth" "$C" > "$R2/docs/spec/agents/ceo/state.json"
  git -C "$R2" add -A >/dev/null; git -C "$R2" -c user.email=t@t -c user.name=t commit -q -m s; C=$(git -C "$R2" log -1 --pretty=%h)
  printf '{"repos":[{"path":"%s","branch":"main","commit":"%s","uncommitted":0}]}' "$pth" "$C" > "$R2/docs/spec/agents/ceo/state.json"
  git -C "$R2" -c user.email=t@t -c user.name=t commit -qam s2 >/dev/null 2>&1; C=$(git -C "$R2" log -1 --pretty=%h)
  printf '{"repos":[{"path":"%s","branch":"main","commit":"%s","uncommitted":1}]}' "$pth" "$C" > "$R2/docs/spec/agents/ceo/state.json"
  out=$(ctx "$R2")
  [[ "$out" != *"NOT FOUND"* && "$out" == *"matches"* ]] && ok "state path '$pth' resolves to the root itself" || bad "state path '$pth'" "$(echo "$out" | grep -A2 'Live state')"
done
W="$T/wt"; git -C "$R2" worktree add -q "$W" -b wtb >/dev/null 2>&1
mkdir -p "$T/wteam/docs/spec/agent"; WC=$(git -C "$W" log -1 --pretty=%h)
printf '{"repos":[{"path":"%s","branch":"wtb","commit":"%s","uncommitted":0}]}' "$W" "$WC" > "$T/wteam/docs/spec/agent/state.json"; echo H > "$T/wteam/docs/spec/agent/handoff.md"
out=$(ctx "$T/wteam")
[[ "$out" != *"NOT FOUND"* ]] && ok "a git worktree (.git file) is found" || bad "worktree" "$(echo "$out" | grep -A2 'Live state')"

echo "session-context: profile-only commits since the save (BUG-22)"
# The degraded path's live-state block, run on its own so both comparisons are held to the same cases.
awk '/<<.PY.$/ && /STATE/ {f=1; next} f && /^PY$/ {exit} f' "$H/karvey-session-context.sh" > "$T/degraded-live.py"
gc() { git -C "$1" -c user.email=t@t -c user.name=t commit -q "${@:2}"; }
b22() {  # a solo repo with its profile committed, then the capture: $1 = directory
  mkdir -p "$1/docs/spec/agent"; git -C "$1" init -q -b main; echo H > "$1/docs/spec/agent/handoff.md"; echo x > "$1/app.txt"
  git -C "$1" add -A; gc "$1" -m init; echo H2 > "$1/docs/spec/agent/handoff.md"; git -C "$1" add -A; gc "$1" -m handoff
  python3 "$(dirname "$H")/scripts/karvey-handoff-capture.py" --profile "$1/docs/spec/agent" >/dev/null
}
b22check() {  # $1 = repo, $2 = label, $3 = want (match|drift)
  local py dg; py=$(ctx "$1" | grep -A3 'Live state'); dg=$(python3 "$T/degraded-live.py" "$1/docs/spec/agent/state.json" "$1" 2>&1)
  for pair in "python path:$py" "degraded path:$dg"; do
    local lab="${pair%%:*}" o="${pair#*:}"
    if [ "$3" = match ]; then
      [[ "$o" == *"profile-only commits since the save"* && "$o" != *"DRIFT"* ]] && ok "$2 ($lab)" || bad "$2 ($lab)" "$o"
    else
      [[ "$o" == *"DRIFT"* && "$o" != *"profile-only"* ]] && ok "$2 ($lab)" || bad "$2 ($lab)" "$o"
    fi
  done
}
P="$T/b22a"; b22 "$P"; git -C "$P" add docs/spec/agent/state.json; gc "$P" -m state
b22check "$P" "commit of state.json alone after the capture → matches, no DRIFT" match
P="$T/b22b"; b22 "$P"; echo y >> "$P/app.txt"; git -C "$P" add -A; gc "$P" -m "state + app"
b22check "$P" "commit of state.json plus another file → DRIFT" drift
P="$T/b22c"; b22 "$P"; git -C "$P" add docs/spec/agent/state.json; gc "$P" --amend -m "handoff + state"
b22check "$P" "HEAD not a descendant of the recorded commit (amend) → DRIFT" drift
P="$T/b22d"; b22 "$P"; git -C "$P" add docs/spec/agent/state.json; gc "$P" -m state; echo n > "$P/new1.txt"; echo n > "$P/new2.txt"
b22check "$P" "higher uncommitted count after a profile-only commit → DRIFT" drift

echo "statusline: reset time (BUG-03) and private debug copy (BUG-04)"
NOW=$(date +%s)
export TMPDIR="$T/tmp"; mkdir -p "$TMPDIR"   # isolated: a leftover debug file from an earlier run must not make BUG-04 pass
sl() { printf '%s' "$1" | bash "$H/karvey-statusline.sh" 2>&1; }
base='"context_window":{"current_usage":1000},"model":{"display_name":"M"},"cwd":"/x/p"'
for v in "$((NOW+3600))" "$(( (NOW+3600)*1000 ))" "\"$(date -u -d @$((NOW+3600)) +%Y-%m-%dT%H:%M:%SZ)\"" '"abc"' '1e400' '"nan"' '[1]' "$((NOW-60))" 'null'; do
  out=$(sl "{$base,\"rate_limits\":{\"five_hour\":{\"used_percentage\":10,\"resets_at\":$v}}}")
  if [[ "$out" == *"karvey statusline down"* || -z "$out" ]]; then bad "resets_at=$v keeps the line up" "$out"; else ok "resets_at=$v keeps the line up"; fi
done
out=$(sl "{$base,\"rate_limits\":{\"five_hour\":{\"used_percentage\":10,\"resets_at\":$((NOW+5400))}}}")
[[ "$out" == *"(1h30m)"* ]] && ok "rounds the time left (1h30m)" || bad "rounding" "$out"
f="${TMPDIR:-/tmp}/.karvey-statusline-last.$(id -u).json"
[ -f "$f" ] && [ "$(stat -c %a "$f" 2>/dev/null || stat -f %Lp "$f")" = "600" ] && ok "debug copy is per user and mode 600" || bad "debug copy perms" "$(ls -l "$f" 2>&1)"

echo "guard tables: every tests/hooks/tables/*.json case (E1.F6.T4; set KARVEY_SKIP_TABLES=1 to skip)"
if [ "${KARVEY_SKIP_TABLES:-}" != "1" ]; then
  RT="$(dirname "$H")/tests/hooks/run_tables.py"
  if python3 "$RT" > "$T/tables.out" 2>&1; then ok "$(tail -1 "$T/tables.out")"
  else bad "guard tables (python3 $RT -v for details)" "$(grep -E 'FAIL|guard tables' "$T/tables.out" | head -20)"; fi
fi

echo "result: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
