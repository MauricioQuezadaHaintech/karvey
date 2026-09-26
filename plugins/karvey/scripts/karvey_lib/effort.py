"""The effort record of a phase close (architecture §1.9, C-09; REQ-W3-014, 015, 016).

The statusline captures the runtime's cumulative session cost into ``{state_dir}/cost/{hash}.json`` (it owns that
file and rewrites it whole). ``effort`` charges the interval since the previous close of the same session:

- **capture pick** (A-06): the capture of this repository root (``root_key``) with the latest ``at``; a second
  capture of the same root updated within 120 s of it → every value ``estimated``, reason ``two sessions active
  on this repository``;
- **tokens** (F-43) come only from the per-message ``usage`` of the session transcript (input, output, cache read,
  cache write; the last record of a message id counts once), never from the context-window figures;
- **charged** (F-42): what was already charged lives in ``{hash}.charged.json``, a file only this module writes, so
  a statusline rewrite never resets it; the first close of a session has none and counts from the session start;
- a **new transcript** (another path, or a cumulative total below the charged one) starts a new token interval;
- an **unreadable** source → ``n/a`` with the reason and the charged file untouched: the gap is charged once, to
  the next readable close; **no capture at all** → ``n/a — statusline not installed``, never 0.

Standard library only; the transcript and the captures are only read.
"""
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

CAPTURE_DIR = "cost"
CHARGED_SUFFIX = ".charged.json"
TWO_SESSIONS_S = 120
REASON_NO_STATUSLINE = "statusline not installed"
REASON_TWO_SESSIONS = "two sessions active on this repository"
USAGE_KEYS = (("in", "input_tokens"), ("out", "output_tokens"), ("cache_read", "cache_read_input_tokens"),
              ("cache_write", "cache_creation_input_tokens"))


def root_key(root):
    return hashlib.sha256(os.path.realpath(str(root)).encode("utf-8")).hexdigest()[:16]


def _parse_at(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return dt if dt.tzinfo else None


def read_captures(cost_dir, rkey):
    """``(captures, unreadable)``: ``[(hash, record)]`` of this root, and the count of unreadable capture files."""
    out, bad = [], 0
    d = Path(cost_dir)
    if not d.is_dir():
        return out, bad
    for p in sorted(d.glob("*.json")):
        if p.name.endswith(CHARGED_SUFFIX) or p.name.startswith("."):
            continue
        try:
            rec = json.loads(p.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            bad += 1
            continue
        if not isinstance(rec, dict) or _parse_at(rec.get("at")) is None:
            bad += 1
            continue
        if rec.get("root_key") == rkey:
            out.append((p.name[:-len(".json")], rec))
    return out, bad


def pick_capture(captures):
    """``(hash, record, quality, reason)`` of the latest capture; ``estimated`` when two are within 120 s."""
    if not captures:
        return None, None, None, None
    ranked = sorted(captures, key=lambda hr: (_parse_at(hr[1]["at"]), hr[0]))
    h, rec = ranked[-1]
    latest = _parse_at(rec["at"])
    for oh, orec in ranked[:-1]:
        if abs((latest - _parse_at(orec["at"])).total_seconds()) <= TWO_SESSIONS_S:
            return h, rec, "estimated", REASON_TWO_SESSIONS
    return h, rec, "exact", None


def transcript_usage(path):
    """Cumulative ``{in, out, cache_read, cache_write, total}`` of a session transcript, or ``None`` when it
    cannot be read. A message id seen on several lines counts once (its last record)."""
    if not path:
        return None
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return None
    per_msg = {}
    with fh:
        for i, line in enumerate(fh):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            msg = o.get("message") if isinstance(o, dict) else None
            u = msg.get("usage") if isinstance(msg, dict) else None
            if not isinstance(u, dict):
                continue
            key = msg.get("id") or ("line-%d" % i)
            per_msg[key] = {k: int(u.get(src) or 0) for k, src in USAGE_KEYS
                            if isinstance(u.get(src, 0), (int, float))}
    tot = {k: 0 for k, _ in USAGE_KEYS}
    for rec in per_msg.values():
        for k in tot:
            tot[k] += rec.get(k, 0)
    tot["total"] = sum(tot[k] for k, _ in USAGE_KEYS)
    return tot


def read_charged(cost_dir, h):
    p = Path(cost_dir) / (h + CHARGED_SUFFIX)
    try:
        rec = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) else None


def write_charged(cost_dir, h, rec):
    """Atomic write of ``{hash}.charged.json`` (mode 600)."""
    d = Path(cost_dir)
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=str(d), prefix=".charged-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, sort_keys=True)
        os.chmod(tmp, 0o600)
        os.replace(tmp, str(d / (h + CHARGED_SUFFIX)))
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _na(reason, source=None):
    v = {"value": None, "quality": "n/a", "reason": reason}
    if source:
        v["source"] = source
    return v


def compute(cost_dir, rkey, phase, at, review_min=None):
    """``(entry, charge)``: the ``effort[]`` entry of a phase close and the charged record to write after it is
    stored (``charge`` is ``None`` when nothing may be written — an ``n/a`` source leaves the gap for later)."""
    review = ({"value": review_min, "quality": "exact", "source": "stated at the gate"}
              if review_min is not None else _na("review minutes not stated at the gate"))
    captures, bad = read_captures(cost_dir, rkey)
    h, rec, quality, reason = pick_capture(captures)
    entry = {"kind": "phase", "phase": phase, "at": at, "session": h, "review_min": review}
    if rec is None:
        why = "capture unreadable" if bad else REASON_NO_STATUSLINE
        entry["usd"] = _na(why, "runtime statusline")
        entry["tokens"] = _na(why, "session transcript")
        entry["tokens"].pop("value")
        return entry, None
    usd_now = rec.get("usd")
    if not isinstance(usd_now, (int, float)) or isinstance(usd_now, bool):
        entry["usd"] = _na("capture without a cost figure", "runtime statusline")
        entry["tokens"] = {"quality": "n/a", "reason": "capture without a cost figure", "source": "session transcript"}
        return entry, None
    charged = read_charged(cost_dir, h) or {}
    usd_prev = charged.get("usd") if isinstance(charged.get("usd"), (int, float)) else 0.0
    usd_iv = max(0.0, float(usd_now) - float(usd_prev))
    entry["usd"] = {"value": round(usd_iv, 6), "quality": quality, "source": "runtime statusline"}
    if reason:
        entry["usd"]["reason"] = reason
    charge = {"usd": float(usd_now), "at": at, "transcript": charged.get("transcript"), "tokens": charged.get("tokens")}
    transcript = rec.get("transcript")
    usage = transcript_usage(transcript)
    if usage is None:
        entry["tokens"] = {"quality": "n/a", "reason": "transcript unreadable", "source": "session transcript"}
    else:
        prev = charged.get("tokens") if isinstance(charged.get("tokens"), dict) else None
        new_transcript = (prev is None or charged.get("transcript") != transcript
                          or int(prev.get("total", 0)) > usage["total"])
        base = {k: 0 for k in usage} if new_transcript else {k: int(prev.get(k, 0)) for k in usage}
        iv = {k: max(0, usage[k] - base[k]) for k in usage}
        entry["tokens"] = {"in": iv["in"], "out": iv["out"], "cache": iv["cache_read"] + iv["cache_write"],
                           "total": iv["total"], "quality": quality, "source": "session transcript"}
        if reason:
            entry["tokens"]["reason"] = reason
        charge["transcript"], charge["tokens"] = transcript, usage
    return entry, charge


def rotation_advice(cost_dir, rkey, red_pct):
    """The checkpoint-rotation line when the latest capture's context is at or above ``red_pct`` (F-47)."""
    captures, _ = read_captures(cost_dir, rkey)
    _, rec, _, _ = pick_capture(captures)
    pct = rec.get("context_pct") if rec else None
    if isinstance(pct, (int, float)) and red_pct is not None and pct >= red_pct:
        return ("context at %s%% (>= %s%%): save a checkpoint and start the next phase in a fresh session"
                % (("%g" % pct), ("%g" % red_pct)))
    return None
