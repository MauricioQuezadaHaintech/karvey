#!/usr/bin/env bash
# Security-tool stub for test_security_scan.py (no real scanner, no network). `version` / `--version` prints
# "<name> stub 1.2.3". Otherwise it writes $KARVEY_STUB_SEC_REPORT (default "[]") to the path after
# --report-path / --output / -o (checkov: -o is the format), or to stdout when there is none, and exits $KARVEY_STUB_SEC_RC (default 0).
n="$(basename "$0")"
case "${1:-}" in version|--version) echo "$n stub 1.2.3"; exit 0 ;; esac
out=""
prev=""
for a in "$@"; do
  case "$prev" in --report-path|--output) out="$a" ;; -o) [ "$n" = checkov ] || out="$a" ;; esac
  prev="$a"
done
report="${KARVEY_STUB_SEC_REPORT:-[]}"
if [ -n "$out" ]; then printf '%s' "$report" > "$out"; else printf '%s' "$report"; fi
printf '%s %s\n' "$n" "$*" >> "${KARVEY_STUB_SEC_LOG:-/dev/null}"
exit "${KARVEY_STUB_SEC_RC:-0}"
