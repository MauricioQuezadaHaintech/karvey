#!/usr/bin/env bash
# Regression tests for the plugin hooks (BUG-01..BUG-04, Karvey 3.11.2). No dependencies beyond bash + python3.
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
