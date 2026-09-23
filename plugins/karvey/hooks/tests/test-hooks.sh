#!/usr/bin/env bash
# Regression tests for the plugin hooks (BUG-01..04 in 3.11.2, BUG-18..19 in 3.11.3). No dependencies beyond bash + python3.
# Run: bash plugins/karvey/hooks/tests/test-hooks.sh   → exit 0 if all pass.
set -u
H="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf '  ok   %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); printf '  FAIL %s\n       got: %s\n' "$1" "$2"; }
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
ctx() { CLAUDE_PROJECT_DIR="$1" bash "$H/karvey-session-context.sh" 2>&1; }

echo "session-context: settings nudge (BUG-02)"
mkdir -p "$T/plain"; out=$(ctx "$T/plain");                      [ -z "$out" ] && ok "no docs/spec → silent" || bad "no docs/spec → silent" "$out"
mkdir -p "$T/openapi/docs/spec"; out=$(ctx "$T/openapi");        [ -z "$out" ] && ok "bare docs/spec (not Karvey) → silent" || bad "bare docs/spec → silent" "$out"
mkdir -p "$T/k1/docs/spec/changes"; out=$(ctx "$T/k1");          [[ "$out" == *"no project.json"* ]] && ok "changes/ without project.json → notice" || bad "changes/ without project.json" "$out"
mkdir -p "$T/k2/docs/spec"; echo '{"management":{"tool":"jira"}}' > "$T/k2/docs/spec/project.json"
out=$(ctx "$T/k2");                                               [[ "$out" == *"notifications"* && "$out" != *"management"* ]] && ok "missing notifications only" || bad "missing notifications only" "$out"
echo '{"management":"markdown","notifications":{"channel":"none"}}' > "$T/k2/docs/spec/project.json"
out=$(ctx "$T/k2");                                               [[ "$out" == *"management"* ]] && ok "management as legacy string → notice" || bad "legacy string" "$out"
echo '{"management":{},"notifications":{"channel":"none"}}' > "$T/k2/docs/spec/project.json"
out=$(ctx "$T/k2");                                               [[ "$out" == *"management"* ]] && ok "empty block counts as missing" || bad "empty block" "$out"
printf '\xef\xbb\xbf{"management":{"tool":"markdown"},"notifications":{"channel":"none"}}' > "$T/k2/docs/spec/project.json"
out=$(ctx "$T/k2");                                               [ -z "$out" ] && ok "BOM + complete settings → silent" || bad "BOM complete" "$out"
echo '[1]' > "$T/k2/docs/spec/project.json"; out=$(ctx "$T/k2"); [[ "$out" == *"not an object"* ]] && ok "non-object JSON → notice" || bad "non-object" "$out"
[[ "$(ctx "$T/k1")" == *"creates no change"* ]] && ok "notice says settings-only (BUG-01 guard)" || bad "notice wording" "$(ctx "$T/k1")"
( cd "$T" && out=$(CLAUDE_PROJECT_DIR=plain timeout 5 bash "$H/karvey-session-context.sh"; echo "rc=$?"); [[ "$out" == *"rc=0"* ]] && echo ok ) >/dev/null && ok "relative CLAUDE_PROJECT_DIR does not hang" || bad "relative dir" "timeout"

echo "hooks.json: the declared command runs as written (BUG-18)"
CMD=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['hooks']['SessionStart'][0]['hooks'][0]['command'])" "$H/hooks.json")
out=$(cd "$T" && CLAUDE_PLUGIN_ROOT="$(dirname "$H")" CLAUDE_PROJECT_DIR="$T/plain" bash -c "$CMD" 2>&1; echo "rc=$?")
[[ "$out" == *"rc=0"* && "$out" != *"No such file"* ]] && ok "SessionStart command expands CLAUDE_PLUGIN_ROOT" || bad "SessionStart command" "$out"
out=$(cd "$T" && CLAUDE_PLUGIN_ROOT="$T/with space/plugin" bash -c "$CMD" 2>&1; echo "rc=$?")
[[ "$out" == *"with space/plugin/hooks"* ]] && ok "path with spaces stays one word" || bad "path with spaces" "$out"

echo "session-context: team.json inside the repo (BUG-19)"
R="$T/myrepo"; mkdir -p "$R/docs/spec/agents/ceo" "$R/docs/spec/board"
echo '{"ops_repo":"myrepo","roles":{"myrepo":"ceo"},"display_names":{"ceo":"agente-x"}}' > "$R/docs/spec/team.json"
echo "MANIFEST-X" > "$R/docs/spec/agents/ceo/manifest.md"; echo "COMPACT-X" > "$R/docs/spec/agents/ceo/manifest-compact.md"
echo "HANDOFF-X" > "$R/docs/spec/agents/ceo/handoff.md"; echo "BOARD-X" > "$R/docs/spec/board/ceo.md"
out=$(ctx "$R")
[[ "$out" == *"Profile: $R/docs/spec/agents/ceo"* ]] && ok "profile resolves to docs/spec/agents/<role>" || bad "in-repo profile" "$out"
[[ "$out" == *"COMPACT-X"* && "$out" == *"MANIFEST-X"* && "$out" == *"HANDOFF-X"* ]] && ok "manifest-compact, manifest and handoff reinjected" || bad "in-repo reinjection" "$out"
[[ "$out" == *"agente-x"* ]] && ok "role from the root's own name when the session starts at the root" || bad "role at root" "$out"
rm "$R/docs/spec/agents/ceo/handoff.md"; out=$(ctx "$R")
[[ "$out" == *"no handoff at"* ]] && ok "missing handoff is said, not silent" || bad "missing handoff" "$out"
S="$T/team"; mkdir -p "$S/docs/spec" "$S/ops/agents/dev" "$S/app"
echo '{"ops_repo":"ops","roles":{"app":"dev"}}' > "$S/docs/spec/team.json"; echo "SIB-HANDOFF" > "$S/ops/agents/dev/handoff.md"
out=$(ctx "$S/app")
[[ "$out" == *"Profile: $S/ops/agents/dev"* && "$out" == *"SIB-HANDOFF"* ]] && ok "sibling ops repo layout still works" || bad "sibling layout" "$out"

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

echo "result: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
