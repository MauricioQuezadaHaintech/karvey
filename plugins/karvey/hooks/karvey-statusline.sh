#!/usr/bin/env bash
# Karvey rotation statusline: context, account limits, session duration. Warns "TIME TO ROTATE".
# It costs no model tokens: it is a script, it runs outside the turn.
#
# Uses the fields Claude Code provides on stdin (context_window, rate_limits, cost).
# If this CLI version does not provide them, it falls back to reading the transcript.
#
# Thresholds (env): KARVEY_ROTATE_CTX_YELLOW (def. 100000) · KARVEY_ROTATE_CTX_RED (def. 150000)
#                   KARVEY_ROTATE_HOURS (def. 8)
#                   KARVEY_TZ (IANA zone for the reset clock, e.g. America/Santiago; def. the system's)
# Each account window shows when it resets and how long is left: `5h 29% ↻18:05 (1h31m)`.
# 150k comes from measurement: at 588k a turn costs 7x what it costs at 80k, and rotating costs ~40k.
#
# A plugin cannot declare a statusline (only `agent` and `subagentStatusLine` are accepted), so this
# is installed by the user, once, in their own settings.json. See hooks/README.md.
exec 2>/dev/null
IN=$(cat)
# per user and private: a fixed /tmp name was shared across OS users and world-readable (session ids)
DBG="${TMPDIR:-/tmp}/.karvey-statusline-last.$(id -u).json"
( umask 077; printf '%s' "$IN" > "$DBG" ) 2>/dev/null
# The output is captured instead of printed directly: if the CLI changes the stdin format (it did,
# with current_usage), the traceback shows up in the statusline instead of leaving it empty.
# A statusline that disappears is indistinguishable from one that is switched off.
ERRF=$(mktemp 2>/dev/null || echo "${TMPDIR:-/tmp}/.karvey-statusline-err.$$")
OUT=$(python3 - "$IN" 2>"$ERRF" <<'PY'
import sys, json, os, datetime

try:
    d = json.loads(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].strip() else {}
except Exception:
    d = {}

CTX_Y = int(os.environ.get('KARVEY_ROTATE_CTX_YELLOW', 100_000))
CTX_R = int(os.environ.get('KARVEY_ROTATE_CTX_RED', 150_000))
HOURS = float(os.environ.get('KARVEY_ROTATE_HOURS', 8))

cw     = d.get('context_window') or {}
cost   = d.get('cost') or {}
limits = d.get('rate_limits') or {}
model  = (d.get('model') or {}).get('display_name') or ''
cwd    = d.get('cwd') or (d.get('workspace') or {}).get('current_dir') or os.getcwd()
# basename does not split on '\', so on Windows it would show the whole path instead of the folder.
folder = os.path.basename(str(cwd).replace('\\', '/').rstrip('/'))
tp     = d.get('transcript_path') or ''
# Windows + WSL: the CLI hands over 'C:\\Users\\...' paths that do not exist inside WSL. Untranslated,
# os.path.isfile() returns False silently and the statusline loses 'new' and 'cache' without saying why.
if len(tp) > 2 and tp[1] == ':' and tp[0].isalpha():
    tp = '/mnt/' + tp[0].lower() + tp[2:].replace('\\', '/')

# --- context: native if present, otherwise computed from the transcript ---
# current_usage went from an integer to an object with the breakdown. Both forms are accepted.
cu = cw.get('current_usage')
if isinstance(cu, dict):
    ctx = sum(v for v in cu.values() if isinstance(v, (int, float)))
else:
    ctx = cu or 0
ctx_native = ctx
pct = cw.get('used_percentage')
new = read = 0
t0 = t1 = None

if (not ctx) or (tp and os.path.isfile(tp)):
    if tp and os.path.isfile(tp):
        with open(tp, encoding='utf-8', errors='replace') as f:
            for line in f:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                ts = o.get('timestamp')
                if ts:
                    t0 = t0 or ts
                    t1 = ts
                u = (o.get('message') or {}).get('usage')
                if not u:
                    continue
                new  += u.get('output_tokens', 0) + u.get('cache_creation_input_tokens', 0)
                read += u.get('cache_read_input_tokens', 0)
                if not ctx_native:
                    ctx = (u.get('input_tokens', 0)
                           + u.get('cache_read_input_tokens', 0)
                           + u.get('cache_creation_input_tokens', 0))

# --- duration: the CLI's if present, otherwise the transcript's ---
ms = cost.get('total_duration_ms')
if ms:
    h = ms / 3_600_000
else:
    def diff(a, b):
        try:
            fa = datetime.datetime.fromisoformat(a.replace('Z', '+00:00'))
            fb = datetime.datetime.fromisoformat(b.replace('Z', '+00:00'))
            return max(0.0, (fb - fa).total_seconds() / 3600)
        except Exception:
            return 0.0
    h = diff(t0, t1) if (t0 and t1) else 0.0

def k(n):
    n = n or 0
    if n >= 1_000_000: return f'{n/1_000_000:.1f}M'
    if n >= 1_000:     return f'{n/1_000:.0f}k'
    return str(int(n))

if   ctx >= CTX_R: light, why = '🔴', 'context'
elif ctx >= CTX_Y: light, why = '🟡', ''
else:              light, why = '🟢', ''
if h >= HOURS:
    light = '🔴'
    why = f'{why} + hours' if why else 'hours'

left = f'{light} ctx {k(ctx)}'
if pct is not None:
    left += f' ({pct:.0f}%)'
parts = [left]
if new:  parts.append(f'new {k(new)}')
if read: parts.append(f'cache {k(read)}')
parts.append(f'{h:.1f}h')

# account limit consumption: the number that actually decides a rotation

# next reset of each account window: local clock time + time left (resets_at = epoch seconds)
def _reset(w, week=False):
    # Never let a strange value take the whole statusline down (it would hide the rotation warning).
    try:
        ts = (w or {}).get('resets_at')
        if ts in (None, '', 0):
            return ''
        if isinstance(ts, str):
            s = ts.strip()
            try:
                ts = float(s)
            except ValueError:
                ts = datetime.datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()
        ts = float(ts)
        if ts != ts or ts in (float('inf'), float('-inf')):
            return ''
        if ts > 1e11:                      # milliseconds
            ts /= 1000.0
        now = datetime.datetime.now().timestamp()
        if ts <= now or ts - now > 400 * 86400:
            return ''                      # already reset, or absurd
        tz = None
        name = os.environ.get('KARVEY_TZ') or ''
        if name:
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(name)
            except Exception:
                tz = None
        at = datetime.datetime.fromtimestamp(ts, tz) if tz else datetime.datetime.fromtimestamp(ts)
        left = int(round((ts - now) / 60.0)) * 60
        d_, r_ = divmod(left, 86400); h_, r_ = divmod(r_, 3600); m_ = r_ // 60
        rem = f'{d_}d{h_}h' if d_ else (f'{h_}h{m_:02d}m' if h_ else f'{max(m_, 1)}m')
        day = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][at.weekday()] + ' ' if week else ''
        return f' ↻{day}{at:%H:%M} ({rem})'
    except Exception:
        return ''

l5 = (limits.get('five_hour') or {}).get('used_percentage')
l7 = (limits.get('seven_day') or {}).get('used_percentage')
if l5 is not None or l7 is not None:
    lim = 'limit'
    if l5 is not None: lim += f' 5h {l5:.0f}%' + _reset(limits.get('five_hour'))
    if l7 is not None: lim += f' · 7d {l7:.0f}%' + _reset(limits.get('seven_day'), week=True)
    parts.append(lim)
    if (l5 or 0) >= 80 or (l7 or 0) >= 80:
        light = '🔴'
        why = f'{why} + limit' if why else 'limit'
        parts[0] = '🔴' + parts[0][1:]

usd = cost.get('total_cost_usd')
if usd:   parts.append(f'US${usd:.2f}')
if model: parts.append(model)
if folder: parts.append(folder)

line = ' · '.join(parts)
if light == '🔴':
    line += f'  ⟵ TIME TO ROTATE ({why}): /karvey-checkpoint save → handoff → clear'
print(line)
PY
)
RC=$?
if [ "$RC" -ne 0 ] || [ -z "$OUT" ]; then
  REASON=$(tail -n 1 "$ERRF" 2>/dev/null)
  printf '⚠️  karvey statusline down (rc=%s): %s — see %s\n' "$RC" "${REASON:-no output}" "$DBG"
else
  printf '%s\n' "$OUT"
fi
rm -f "$ERRF" 2>/dev/null
