"""Approval markers and the release ledger (architecture §2.4, §3.3).

This module holds the marker + ledger half. The vocabulary half (the matching of the human's
prompt, REQ-W1-017/019) joins it in E1.F5.T2.

Location: ``<git-common-dir>/karvey/`` (``project.state_dir``), shared by every worktree of the
clone and never tracked by git; directories 0700, files 0600::

    approvals/<scope>.json   scope = change-id | _project — written ONLY by the approval hook
    ledger/<change>.json     release facts — written by karvey-state.py approve prod / advance deployed

A marker is valid only as JSON ``v: 1`` with ``kind`` in plan|prod, the expected ``scope``,
``repo`` equal to this clone's common dir, ``created_at`` within its TTL (clamped to 5..1440 min),
``consumed_at: null`` and a 64-hex ``prompt_sha256``. Anything else — an empty file from
``touch`` included — is ignored and recorded in ``audit.log`` as ``forged-or-corrupt marker
ignored``.

The transcript cross-check (A-8, F-04) is advisory: it hashes only ``user`` lines whose
``message.content`` is a string or a list of ``text`` blocks — never ``tool_result`` lines, which
carry agent-influenced tool output — and never blocks.
"""
import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

from . import atomicio, audit, defaults
from . import project as pj

MARKER_VERSION = 1
LEDGER_VERSION = 1
KINDS = ("plan", "prod")
SCOPE_PROJECT = "_project"
EXCERPT_MAX = 80
CONSUMED_KEEP_H = 24
COMPAT_ENV = "KARVEY_COMPAT_MARKER"
_SCOPE_RE = re.compile(r"^(_project|[a-z0-9][a-z0-9-]{1,62})$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ApprovalError(Exception):
    pass


# --------------------------------------------------------------------------- basics
def now_dt():
    return datetime.now().astimezone()


def iso(dt):
    return dt.isoformat(timespec="seconds")


def parse_dt(value):
    if not isinstance(value, str):
        return None
    v = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else None


def prompt_hash(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def valid_scope(scope):
    return isinstance(scope, str) and bool(_SCOPE_RE.match(scope))


def clamp_ttl(value):
    """The TTL in minutes, clamped to the D-07 bounds; a non-integer gives the default."""
    d = defaults()
    lo, hi = d["plan_marker_ttl_bounds"]["minimum"], d["plan_marker_ttl_bounds"]["maximum"]
    if not isinstance(value, int) or isinstance(value, bool):
        return d["plan_marker_ttl_min"]
    return max(lo, min(hi, value))


def repo_id(root):
    """This clone's identity: the realpath of its git common dir, else of the project root."""
    common = pj.git_common_dir(root)
    return str(common) if common is not None else os.path.realpath(str(root))


def _subdir(root, name, create=True):
    d = pj.state_dir(root, create=create) / name
    if create:
        d.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(str(d), 0o700)
        except OSError:
            pass
    return d


def _audit(root, record):
    try:
        audit.append(pj.state_dir(root), record)
    except OSError:
        pass


def _write_private(path, data, expected="*"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    atomicio.write_text_atomic(path, atomicio.dumps(data), expected_sha256=expected, mode=0o600)
    try:
        os.chmod(str(path), 0o600)
    except OSError:
        pass


# --------------------------------------------------------------------------- markers
def approvals_dir(root, create=True):
    return _subdir(root, "approvals", create)


def marker_path(root, scope, create=True):
    if not valid_scope(scope):
        raise ApprovalError("invalid marker scope %r" % (scope,))
    return approvals_dir(root, create) / (scope + ".json")


def marker_rel(scope):
    """How evidence names a marker: relative to the state dir (``approvals/<scope>.json``)."""
    return "approvals/%s.json" % scope


def write_marker(root, kind, scope, prompt, session_id="", ttl_min=None, now=None, compat=None):
    """Write the marker of ``scope`` (only the approval hook calls this). Returns the marker.

    With ``KARVEY_COMPAT_MARKER`` set (D-11) the same content is also written to that path, so
    the owner's personal ``require-plan*.sh`` hooks keep working.
    """
    if kind not in KINDS:
        raise ApprovalError("invalid marker kind %r" % (kind,))
    now = now or now_dt()
    marker = {
        "v": MARKER_VERSION, "kind": kind, "scope": scope, "repo": repo_id(root),
        "created_at": iso(now), "ttl_min": clamp_ttl(ttl_min if ttl_min is not None else defaults()["plan_marker_ttl_min"]),
        "session_id": session_id or "", "prompt_sha256": prompt_hash(prompt),
        "prompt_excerpt": (prompt or "")[:EXCERPT_MAX], "consumed_at": None,
    }
    path = marker_path(root, scope)
    _write_private(path, marker)
    compat = os.environ.get(COMPAT_ENV) if compat is None else compat
    compat_written = None
    if compat:
        try:
            _write_private(os.path.expanduser(compat), marker)
            compat_written = os.path.expanduser(compat)
        except (OSError, atomicio.AtomicIOError) as exc:
            _audit(root, {"guard": "approval", "event": "compat-marker", "decision": "error",
                          "reason": str(exc)})
    _audit(root, {"guard": "approval", "event": "marker", "decision": "recorded", "reason": kind,
                  "change": scope, "session_id": session_id or "", "prompt_excerpt": marker["prompt_excerpt"],
                  "compat": compat_written})
    return marker


def read_marker(root, scope):
    """``(marker, status)``; status ``ok`` · ``missing`` · ``corrupt`` (empty, not JSON, not an object)."""
    try:
        path = marker_path(root, scope, create=False)
    except ApprovalError:
        return None, "corrupt"
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None, "missing"
    except OSError:
        return None, "corrupt"
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        return None, "corrupt"
    if not isinstance(data, dict):
        return None, "corrupt"
    return data, "ok"


def check_marker(marker, root, scope=None, ttl_min=None, now=None, kinds=KINDS):
    """``(ok, reason)`` for a parsed marker. ``ttl_min`` (from reviewed config) wins over the
    marker's own ``ttl_min``; both are clamped."""
    if not isinstance(marker, dict):
        return False, "not an object"
    if marker.get("v") != MARKER_VERSION:
        return False, "unknown version"
    if marker.get("kind") not in KINDS:
        return False, "unknown kind"
    if marker.get("kind") not in kinds:
        return False, "kind %s does not satisfy %s" % (marker.get("kind"), "|".join(kinds))
    if scope is not None and marker.get("scope") != scope:
        return False, "wrong scope"
    if marker.get("repo") != repo_id(root):
        return False, "wrong repo"
    if not isinstance(marker.get("prompt_sha256"), str) or not _HEX64.match(marker["prompt_sha256"]):
        return False, "bad prompt_sha256"
    if marker.get("consumed_at") is not None:
        return False, "consumed"
    created = parse_dt(marker.get("created_at"))
    if created is None:
        return False, "bad created_at"
    now = now or now_dt()
    ttl = clamp_ttl(ttl_min if ttl_min is not None else marker.get("ttl_min"))
    if now - created > timedelta(minutes=ttl):
        return False, "expired (older than %d min)" % ttl
    if created - now > timedelta(minutes=5):
        return False, "created in the future"
    return True, "ok"


def find_valid(root, change=None, kinds=KINDS, ttl_min=None, now=None):
    """The first valid marker for ``(repo, change)`` then ``(repo, _project)``.

    Returns ``(marker, scope, reasons)``; ``marker`` is None when none is valid, and
    ``reasons`` maps each scope tried to why it did not count. A corrupt file is audited.
    """
    scopes = ([change] if change and valid_scope(change) and change != SCOPE_PROJECT else []) + [SCOPE_PROJECT]
    reasons = {}
    for scope in scopes:
        m, status = read_marker(root, scope)
        if status == "missing":
            reasons[scope] = "missing"
            continue
        if status == "corrupt":
            reasons[scope] = "forged-or-corrupt"
            _audit(root, {"guard": "approval", "event": "marker", "decision": "ignored",
                          "reason": "forged-or-corrupt marker ignored", "change": scope})
            continue
        ok, why = check_marker(m, root, scope=scope, ttl_min=ttl_min, now=now, kinds=kinds)
        if ok:
            return m, scope, reasons
        reasons[scope] = why
        if why in ("unknown version", "unknown kind", "bad prompt_sha256", "bad created_at", "not an object"):
            _audit(root, {"guard": "approval", "event": "marker", "decision": "ignored",
                          "reason": "forged-or-corrupt marker ignored (%s)" % why, "change": scope})
    return None, None, reasons


def consume(root, scope, now=None, created_at=None):
    """Mark the marker of ``scope`` consumed (the file is kept for audit). Returns True if it was
    live. With ``created_at``, only the marker created at that instant is consumed."""
    m, status = read_marker(root, scope)
    if status != "ok" or m.get("consumed_at") is not None:
        return False
    if created_at is not None and m.get("created_at") != created_at:
        return False
    m["consumed_at"] = iso(now or now_dt())
    _write_private(marker_path(root, scope), m)
    _audit(root, {"guard": "approval", "event": "marker", "decision": "consumed", "change": scope})
    return True


def gc(root, now=None):
    """Remove markers consumed more than 24 h ago. Returns the removed scopes."""
    now = now or now_dt()
    removed = []
    d = approvals_dir(root, create=False)
    if not d.is_dir():
        return removed
    for p in sorted(d.glob("*.json")):
        m, status = read_marker(root, p.stem)
        if status != "ok":
            continue
        when = parse_dt(m.get("consumed_at"))
        if when is not None and now - when > timedelta(hours=CONSUMED_KEEP_H):
            try:
                p.unlink()
                removed.append(p.stem)
            except OSError:
                pass
    return removed


def _user_texts(obj):
    """The human-typed texts of one transcript line, or [] (F-04: never ``tool_result``)."""
    if not isinstance(obj, dict):
        return []
    msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
    if obj.get("type") != "user" and msg.get("role") != "user":
        return []
    content = msg.get("content", obj.get("content"))
    if isinstance(content, str):
        return [content]
    if isinstance(content, list) and content:
        if not all(isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
                   for b in content):
            return []  # tool_result (or mixed) lines carry agent-influenced output
        texts = [b["text"] for b in content]
        return texts + ["".join(texts), "\n".join(texts)]
    return []


def verify_transcript(transcript_path, prompt_sha256, max_bytes=64 * 1024 * 1024):
    """``match`` · ``mismatch`` · ``unverified`` (unreadable or absent). Advisory only."""
    if not transcript_path or not isinstance(prompt_sha256, str):
        return "unverified"
    try:
        fh = open(transcript_path, "rb")
    except OSError:
        return "unverified"
    read = 0
    with fh:
        for line in fh:
            read += len(line)
            if read > max_bytes:
                return "unverified"
            try:
                obj = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                continue
            for text in _user_texts(obj):
                if prompt_hash(text) == prompt_sha256:
                    return "match"
    return "mismatch"


def cross_check(root, marker, transcript_path):
    """Run the advisory transcript check for ``marker`` and log a mismatch. Never raises."""
    try:
        result = verify_transcript(transcript_path, (marker or {}).get("prompt_sha256"))
    except Exception:  # advisory: an unexpected format must not break the caller
        result = "unverified"
    if result == "mismatch":
        _audit(root, {"guard": "approval", "event": "transcript", "decision": "warn",
                      "reason": "marker not found in transcript", "change": (marker or {}).get("scope")})
    return result


def evidence(marker, scope):
    """The ``evidence`` object an approval records for ``marker`` (§2.2 evidence)."""
    if not marker:
        return {"marker": "none"}
    return {"marker": marker_rel(scope), "marker_created_at": marker.get("created_at", ""),
            "prompt_excerpt": (marker.get("prompt_excerpt") or "")[:EXCERPT_MAX],
            "session": marker.get("session_id", "")}


# --------------------------------------------------------------------------- ledger
def ledger_path(root, change, create=True):
    if not valid_scope(change) or change == SCOPE_PROJECT:
        raise ApprovalError("invalid change id %r" % (change,))
    return _subdir(root, "ledger", create) / (change + ".json")


def read_ledger(root, change):
    """``(ledger, status)``; status ``ok`` · ``missing`` · ``corrupt``."""
    try:
        path = ledger_path(root, change, create=False)
    except ApprovalError:
        return None, "corrupt"
    if not path.is_file():
        return None, "missing"
    try:
        data = atomicio.read_json(path).data
    except atomicio.ReadError:
        return None, "corrupt"
    if not isinstance(data, dict) or data.get("v") != LEDGER_VERSION or data.get("change") != change:
        return None, "corrupt"
    return data, "ok"


def _update_ledger(root, change, key, value):
    path = ledger_path(root, change)
    try:
        loaded = atomicio.read_json(path)
        data, expected = loaded.data, loaded.sha256
    except atomicio.ReadError:
        if path.exists():
            raise ApprovalError("release ledger %s is corrupt; not overwritten" % path)
        data, expected = {"v": LEDGER_VERSION, "change": change}, None
    if not isinstance(data, dict) or data.get("change") != change:
        raise ApprovalError("release ledger %s is corrupt; not overwritten" % path)
    data[key] = value
    _write_private(path, data, expected=expected)
    return data


def record_prod(root, change, approval):
    """Write the human prod approval into the ledger (never into spec.json, D-03)."""
    return _update_ledger(root, change, "prod", approval)


def record_release(root, change, pipeline_run, post_deploy_check, at=None):
    return _update_ledger(root, change, "release", {"pipeline_run": pipeline_run,
                                                     "post_deploy_check": post_deploy_check,
                                                     "at": at or iso(now_dt())})
