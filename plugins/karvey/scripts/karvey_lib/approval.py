"""Approval markers and the release ledger (architecture §2.4, §3.3).

Two halves: the marker + ledger store, and the vocabulary that decides whether the human's
prompt is an approval (REQ-W1-017/019, §3.3 "Approval vocabulary"; default lists in
``vocabulary.json``, the one place).

Location: ``<git-common-dir>/karvey/`` (``project.state_dir``), shared by every worktree of the
clone and never tracked by git; directories 0700, files 0600::

    approvals/<scope>.json   scope = change-id | _project — written ONLY by the approval hook
    approvals/notify/confirm-<key>.json
                             a human confirmation of a changed notification destination (D-16,
                             F-15), key = hash of the project root within the clone — written ONLY
                             by the approval hook, consumed by ``karvey-config.py notify-check --confirm``
    ledger/<change>.json     release facts — written by karvey-state.py approve prod / advance deployed;
                             ``reopen`` moves a prod approval to ``superseded`` (D-36)

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
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

from . import atomicio, audit, clones, defaults
from . import project as pj

MARKER_VERSION = 1
LEDGER_VERSION = 1
KINDS = ("plan", "prod")
SCOPE_PROJECT = "_project"
EXCERPT_MAX = 80
CONSUMED_KEEP_H = 24
PROD_VALID_H = 24  # D-35: a prod approval is valid 24 h after the human's OK
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
    # D-34: the prod-gate matches a prod approval against this line (hash, session, time)
    _audit(root, {"guard": "approval", "event": "marker", "decision": "recorded", "reason": kind,
                  "change": scope, "session_id": session_id or "", "prompt_excerpt": marker["prompt_excerpt"],
                  "prompt_sha256": marker["prompt_sha256"], "created_at": marker["created_at"],
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
    if marker.get("stopped_at") is not None:
        return False, "withdrawn (the human said stop)"
    if "plan" not in kinds and marker.get("prod_used_at") is not None:
        return False, "consumed"  # BUG-41: one production approval, one change; it stays a plan approval (D-47)
    created = parse_dt(marker.get("created_at"))
    if created is None:
        return False, "bad created_at"
    now = now or now_dt()
    if "plan" not in kinds:  # D-47 / D-35: a production OK counts 24 h; a plan approval has no time limit
        if now - created > timedelta(hours=PROD_VALID_H):
            return False, "expired (older than %d h)" % PROD_VALID_H
    if created - now > timedelta(minutes=5):
        return False, "created in the future"
    return True, "ok"


def find_valid(root, change=None, kinds=KINDS, ttl_min=None, now=None, project_scope=True):
    """The first valid marker for ``(repo, change)`` then ``(repo, _project)`` (the latter only with
    ``project_scope``; a production approval is always of one change, BUG-41).

    Returns ``(marker, scope, reasons)``; ``marker`` is None when none is valid, and
    ``reasons`` maps each scope tried to why it did not count. A corrupt file is audited.
    """
    scopes = ([change] if change and valid_scope(change) and change != SCOPE_PROJECT else []) + \
        ([SCOPE_PROJECT] if project_scope else [])
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


def mark_prod_used(root, scope, created_at=None, now=None):
    """D-47 (REQ-HF-034): ``approve … prod`` uses the production OK once (BUG-41) but the same message stays the
    plan approval until the plan ends."""
    m, status = read_marker(root, scope)
    if status != "ok" or m.get("consumed_at") is not None or m.get("prod_used_at") is not None:
        return False
    if created_at is not None and m.get("created_at") != created_at:
        return False
    m["prod_used_at"] = iso(now or now_dt())
    _write_private(marker_path(root, scope), m)
    _audit(root, {"guard": "approval", "event": "marker", "decision": "prod-used", "change": scope})
    return True


def withdraw_all(root, now=None):
    """D-47 (REQ-HF-033): the human said stop — every live plan approval of this clone is withdrawn."""
    out = []
    d = approvals_dir(root, create=False)
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.json")):
        m, status = read_marker(root, p.stem)
        if status != "ok" or m.get("kind") not in KINDS or m.get("consumed_at") or m.get("stopped_at"):
            continue
        m["stopped_at"] = iso(now or now_dt())
        _write_private(marker_path(root, p.stem), m)
        out.append(p.stem)
    if out:
        _audit(root, {"guard": "approval", "event": "marker", "decision": "withdrawn", "reason": "stop",
                      "change": ",".join(out)})
    return out


_STOP_LEAD = re.compile(r"^((please|por favor|hey|oye|ok|okay|ya|ojo)[,!.]?\s+|(no|espera|wait)[,!.]\s+)+")
_STOP_WORD = r"(detente|detenete|deten|stop|alto|basta|cancela|cancelalo|cancel|halt|frena|pausa|pause|abort|aborta|" \
             r"no sigas|no continues|dont continue|don't continue|hold on|hold|wait|espera|para|paralo|paren)"
_STOP = re.compile(r"^%s(\s*[,.!;:]|\s*$|\s+(ya|todo|ahora|now|please|por favor|un momento|el|la|los|las|eso|"
                   r"esto|aqui|ahi|alli|it|that|this|everything|all|the|right|there)\b)" % _STOP_WORD)


def is_stop(prompt):
    """The human's own message tells the agent to stop (quoted material aside)."""
    cleaned = normalise(strip_quoted(prompt if isinstance(prompt, str) else ""))
    if not cleaned or cleaned.endswith("?") or "\u00bf" in cleaned:
        return False
    rest = _STOP_LEAD.sub("", cleaned)
    return bool(_STOP.match(rest))


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
            "session": marker.get("session_id", ""), "prompt_sha256": marker.get("prompt_sha256", "")}


def audit_record_of(root, scope, ev):
    """D-34: True when ``audit.log`` (current or rotated) holds the approval hook's ``recorded`` line
    of the prod marker that ``ev`` names: same scope, prompt hash, session and creation time."""
    if not isinstance(ev, dict) or not isinstance(ev.get("prompt_sha256"), str) or \
            not _HEX64.match(ev["prompt_sha256"]) or not isinstance(ev.get("marker_created_at"), str):
        return False
    try:
        records = audit.read(pj.state_dir(root, create=False), include_rotated=True)
    except OSError:
        return False
    for r in records:
        if (r.get("guard"), r.get("event"), r.get("decision"), r.get("reason")) != \
                ("approval", "marker", "recorded", "prod"):
            continue
        if r.get("change") == scope and r.get("prompt_sha256") == ev["prompt_sha256"] and \
                r.get("session_id", "") == ev.get("session", "") and r.get("created_at") == ev["marker_created_at"]:
            return True
    return False


def prod_record(marker, scope, by, ref, date, head_sha):
    """The ledger record of a human prod approval (D-03, D-34, D-35): who, when, evidence, the
    approved head commit and ``expires_at`` = the human's OK (the marker) + 24 h."""
    created = parse_dt((marker or {}).get("created_at")) or now_dt()
    return {"by": by, "role": "human", "date": date, "ref": ref, "head_sha": head_sha,
            "expires_at": iso(created + timedelta(hours=PROD_VALID_H)), "evidence": evidence(marker, scope)}


# --------------------------------------------------------------------------- notify confirmation (D-16)
NOTIFY_KIND = "notify"
NOTIFY_CODE_LEN = 8
_HEXCODE = re.compile(r"^[0-9a-f]{%d}$" % NOTIFY_CODE_LEN)


def project_key(root):
    """The project inside its clone: the root relative to the git top level (``.`` at the top), so
    every worktree of the clone shares it; outside git, the realpath."""
    top = pj.git_toplevel(root)
    real = os.path.realpath(str(root))
    if top is None:
        return real
    return os.path.relpath(real, os.path.realpath(str(top))).replace(os.sep, "/")


def notify_code(dest_hash):
    """The short code a human types to confirm a destination: the first 8 hex of its hash."""
    return (dest_hash or "")[:NOTIFY_CODE_LEN]


def notify_marker_path(root, create=True):
    key = hashlib.sha256(project_key(root).encode("utf-8")).hexdigest()[:16]
    d = approvals_dir(root, create) / "notify"
    if create:
        d.mkdir(parents=True, exist_ok=True, mode=0o700)
    return d / ("confirm-%s.json" % key)


def notify_phrase(dest_hash, lang="es"):
    """What the human types, e.g. ``confirmo notificacion a1b2c3d4``."""
    code = notify_code(dest_hash)
    return ("confirmo notificacion %s" % code) if lang == "es" else ("confirm notification %s" % code)


def classify_notify(prompt, vocab=None):
    """The destination code a human confirmation carries, or None.

    The phrase is a confirm verb, a notification noun and the 8-hex code, in the human's own
    words: fenced blocks, ``>`` lines and lines over 200 characters are removed first (inline
    code and quotes are kept, so a pasted ``confirmo notificacion a1b2c3d4`` counts); a question
    or a negation records nothing."""
    vocab = vocab or default_vocabulary()
    rules = vocab.get("rules") or default_vocabulary()["rules"]
    nc = vocab.get("notify_confirm") or default_vocabulary()["notify_confirm"]
    raw = prompt if isinstance(prompt, str) else ""
    if len(raw.encode("utf-8")) > rules["huge_prompt_bytes"]:
        raw = raw.encode("utf-8")[:rules["scan_limit_bytes"]].decode("utf-8", "ignore")
    t = _FENCE.sub("\n", raw.replace("\r\n", "\n"))
    t = "\n".join(ln for ln in t.split("\n")
                  if len(ln) <= rules["pasted_line_chars"] and not ln.lstrip().startswith(">"))
    cleaned = normalise(t.replace("`", " "))
    if not cleaned or cleaned.endswith("?") or "\u00bf" in cleaned:
        return None
    if find_term(cleaned, vocab.get("negate") or []):
        return None
    alt = lambda terms: "|".join(re.escape(normalise(x)) for x in sorted(terms, key=len, reverse=True))
    rx = re.compile(r"(?<![\w'])(?:%s)\s*[:,]?\s+(?:%s)\s*[:,]?\s+([0-9a-f]{%d})(?![\w'])"
                    % (alt(nc["verbs"]), alt(nc["nouns"]), NOTIFY_CODE_LEN))
    codes = set(rx.findall(cleaned))
    return codes.pop() if len(codes) == 1 else None


def write_notify_marker(root, code, prompt, session_id="", ttl_min=None, now=None):
    """Record the human's confirmation of destination ``code`` (only the approval hook calls this)."""
    if not isinstance(code, str) or not _HEXCODE.match(code):
        raise ApprovalError("invalid destination code %r" % (code,))
    now = now or now_dt()
    marker = {
        "v": MARKER_VERSION, "kind": NOTIFY_KIND, "repo": repo_id(root), "project": project_key(root),
        "code": code, "created_at": iso(now),
        "ttl_min": clamp_ttl(ttl_min if ttl_min is not None else defaults()["plan_marker_ttl_min"]),
        "session_id": session_id or "", "prompt_sha256": prompt_hash(prompt),
        "prompt_excerpt": (prompt or "")[:EXCERPT_MAX], "consumed_at": None,
    }
    _write_private(notify_marker_path(root), marker)
    _audit(root, {"guard": "approval", "event": "notify-confirm", "decision": "recorded", "reason": code,
                  "session_id": session_id or "", "prompt_excerpt": marker["prompt_excerpt"]})
    return marker


def check_notify_marker(root, dest_hash, now=None):
    """``(ok, reason)``: a live human confirmation of exactly this destination in this project."""
    try:
        path = notify_marker_path(root, create=False)
        data = json.loads(path.read_bytes().decode("utf-8-sig"))
    except FileNotFoundError:
        return False, "no human confirmation recorded"
    except (OSError, UnicodeDecodeError, ValueError):
        data = None
    if not isinstance(data, dict) or data.get("v") != MARKER_VERSION or data.get("kind") != NOTIFY_KIND or \
            not isinstance(data.get("prompt_sha256"), str) or not _HEX64.match(data["prompt_sha256"]):
        _audit(root, {"guard": "approval", "event": "notify-confirm", "decision": "ignored",
                      "reason": "forged-or-corrupt notify confirmation ignored"})
        return False, "forged or corrupt confirmation ignored"
    if data.get("repo") != repo_id(root):
        return False, "confirmation recorded for another repository"
    if data.get("project") != project_key(root):
        return False, "confirmation recorded for another project (%s)" % data.get("project")
    if data.get("code") != notify_code(dest_hash):
        return False, "confirmation is for another destination (%s)" % data.get("code")
    if data.get("consumed_at") is not None:
        return False, "confirmation already used"
    created = parse_dt(data.get("created_at"))
    if created is None:
        return False, "forged or corrupt confirmation ignored"
    now = now or now_dt()
    ttl = clamp_ttl(data.get("ttl_min"))
    if now - created > timedelta(minutes=ttl):
        return False, "confirmation expired (older than %d min)" % ttl
    if created - now > timedelta(minutes=5):
        return False, "confirmation created in the future"
    return True, "ok"


def consume_notify_marker(root, now=None):
    path = notify_marker_path(root, create=False)
    try:
        data = json.loads(path.read_bytes().decode("utf-8-sig"))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    if not isinstance(data, dict) or data.get("consumed_at") is not None:
        return False
    data["consumed_at"] = iso(now or now_dt())
    _write_private(path, data)
    _audit(root, {"guard": "approval", "event": "notify-confirm", "decision": "consumed", "reason": data.get("code")})
    return True


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


def supersede_prod(root, change, at, reason, ref=None):
    """D-36: a reopen moves the ledger's prod approval to ``superseded[]``. Returns the moved record,
    or None when there is none. A corrupt ledger is left alone (check-prod already refuses it)."""
    data, status = read_ledger(root, change)
    if status != "ok" or not isinstance(data.get("prod"), dict):
        return None
    path = ledger_path(root, change)
    loaded = atomicio.read_json(path)
    data = loaded.data
    prod = data.pop("prod")
    entry = {"at": at, "reason": reason, "prod": prod}
    if ref:
        entry["ref"] = ref
    sup = data.get("superseded") if isinstance(data.get("superseded"), list) else []
    sup.append(entry)
    data["superseded"] = sup
    _write_private(path, data, expected=loaded.sha256)
    return prod


def record_release(root, change, pipeline_run, post_deploy_check, at=None):
    return _update_ledger(root, change, "release", {"pipeline_run": pipeline_run,
                                                     "post_deploy_check": post_deploy_check,
                                                     "at": at or iso(now_dt())})


# --------------------------------------------------------------------------- vocabulary (§3.3)
VOCAB_FILE = Path(__file__).resolve().parent / "vocabulary.json"
VOCAB_KEYS = ("approve", "negate", "prod_terms")
_VOCAB = None
_FENCE = re.compile(r"(^|\n)[ \t]*(```|~~~)[^\n]*\n.*?(\n[ \t]*\2[^\n]*(?=\n|$)|$)", re.S)
_INLINE = re.compile(r"`[^`\n]*`")
_QUOTED = re.compile(r'"[^"\n]*"|\u201c[^\u201d\n]*\u201d|\u00ab[^\u00bb\n]*\u00bb')


def default_vocabulary():
    global _VOCAB
    if _VOCAB is None:
        with open(VOCAB_FILE, encoding="utf-8-sig") as fh:
            _VOCAB = json.load(fh)
    return json.loads(json.dumps(_VOCAB))


def vocabulary(override=None):
    """The default vocabulary with the lists of ``override`` (``approval_vocabulary``) replacing
    the defaults key by key. Invalid override entries are ignored."""
    v = default_vocabulary()
    if isinstance(override, dict):
        for k in VOCAB_KEYS:
            terms = override.get(k)
            if isinstance(terms, list):
                clean = [t for t in terms if isinstance(t, str) and t.strip() and len(t) <= 40]
                if clean:
                    v[k] = clean
    return v


def normalise(text):
    """NFKD, accents stripped, casefolded, typographic apostrophes unified, whitespace collapsed."""
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("\u2019", "'").replace("\u2018", "'").casefold()
    return re.sub(r"\s+", " ", t).strip()


def strip_quoted(text, pasted_line_chars=200):
    """Remove quoted and pasted material: fenced blocks, inline code, ``>`` lines, text inside
    ``"…"``, ``\u201c…\u201d`` and ``\u00ab…\u00bb``, and lines longer than ``pasted_line_chars``."""
    t = (text or "").replace("\r\n", "\n")
    t = _FENCE.sub("\n", t)
    lines = [ln for ln in t.split("\n")
             if len(ln) <= pasted_line_chars and not ln.lstrip().startswith(">")]
    t = "\n".join(lines)
    t = _INLINE.sub(" ", t)
    return _QUOTED.sub(" ", t)


def _term_re(term):
    words = [re.escape(w) for w in normalise(term).split(" ") if w]
    return re.compile(r"(?<![\w'])" + r"\s+".join(words) + r"(?![\w'])") if words else None


def find_term(text, terms):
    """The first of ``terms`` found in ``text`` on word boundaries, or None."""
    for term in terms:
        rx = _term_re(term)
        if rx is not None and rx.search(text):
            return term
    return None


_ACCENTED_SI = re.compile(r"(?<![\w])s[\u00ed\u00cd](?![\w])")
_BARE_SI = re.compile(r"^si(?:\s*[,.!;:]|\s*$)")


def _affirmative_si(raw, cleaned):
    """BUG-42: "si" approves only as the affirmative: written "sí" (accent kept), or a bare "si" that is the
    whole reply or opens it followed by punctuation. The conditional "si" ("revisa si …") never does."""
    return bool(_ACCENTED_SI.search(unicodedata.normalize("NFC", strip_quoted(raw)))) or bool(_BARE_SI.match(cleaned))


def classify(prompt, vocab=None):
    """Decide whether ``prompt`` is an approval. Returns a dict:
    ``{approved, kind, reason, term, cleaned}``; ``kind`` is ``plan`` or ``prod`` (D-10) when
    approved. Order (§3.3): strip, then reject questions and negations, then the position rule."""
    vocab = vocab or default_vocabulary()
    rules = vocab.get("rules") or default_vocabulary()["rules"]
    raw = prompt if isinstance(prompt, str) else ""
    if len(raw.encode("utf-8")) > rules["huge_prompt_bytes"]:
        raw = raw.encode("utf-8")[:rules["scan_limit_bytes"]].decode("utf-8", "ignore")
    cleaned = normalise(strip_quoted(raw, rules["pasted_line_chars"]))
    res = {"approved": False, "kind": None, "reason": None, "term": None, "cleaned": cleaned}
    if not cleaned:
        res["reason"] = "empty after removing quoted material"
        return res
    if cleaned.endswith("?") or "\u00bf" in cleaned:
        res["reason"] = "question"
        return res
    neg = find_term(cleaned, vocab["negate"])
    if neg:
        res["reason"] = "negation: %s" % neg
        return res
    window = cleaned if len(cleaned) <= rules["short_prompt_chars"] else " ".join(
        cleaned.split(" ")[:rules["position_words"]])
    term = find_term(window, [t for t in vocab["approve"] if normalise(t) != "si"])
    if not term and any(normalise(t) == "si" for t in vocab["approve"]) and _affirmative_si(raw, cleaned):
        term = "si"
    if not term:
        res["reason"] = "no approval term" + ("" if window is cleaned else " in the first %d words"
                                              % rules["position_words"])
        return res
    res.update(approved=True, term=term, reason="approval: %s" % term,
               kind="prod" if find_term(cleaned, vocab["prod_terms"]) else "plan")
    return res


def scope_for(prompt_cleaned, change_ids, active=None):
    """A change id named in the prompt; else the single active change; else ``_project``."""
    for cid in sorted(change_ids, key=len, reverse=True):
        if valid_scope(cid) and re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(cid.casefold()), prompt_cleaned):
            return cid
    if active and valid_scope(active):
        return active
    return SCOPE_PROJECT


# --------------------------------------------------------------------------- prod scope (REQ-HF-001..004, 029)
_TOKEN = re.compile(r"(?<![\w-])([a-z0-9]+(?:-[a-z0-9]+)+)(?![\w-])")
_ES_TERMS = ("aprobado", "apruebo", "aprueba", "dale", "ejecuta", "adelante", "procede", "perfecto", "si",
             "produccion", "publica", "libera", "pasa", "sube")
REF_SCAN_MAX = 50
# hyphenated words of a release conversation that are not change ids (a token found nowhere else is refused
# as a possible typo of a change id, REQ-HF-002; these never are)
COMMON_HYPHENATED = frozenset({"go-live", "hot-fix", "follow-up", "roll-back", "roll-out", "e-mail", "re-deploy",
                               "re-run", "check-in", "sign-off", "pre-prod", "post-deploy", "read-only",
                               "end-to-end", "on-call", "q-a", "fast-forward", "no-ff", "ff-only"})


def suggested_phrase(cleaned, change=None):
    """The phrase the human types to approve production of ``change`` (BUG-143), in the prompt's language."""
    words = set(re.findall(r"[a-z]+", cleaned or ""))
    cid = change or "<change-id>"
    if words & set(_ES_TERMS):
        return "aprobado para producción %s" % cid
    return "approved for production %s" % cid


def prod_shaped(prompt, vocab=None):
    """An approval term and a production term anywhere in the human's own words (quoted material aside)."""
    vocab = vocab or default_vocabulary()
    cleaned = normalise(strip_quoted(prompt if isinstance(prompt, str) else ""))
    if not cleaned:
        return False
    approve = [t for t in vocab["approve"] if normalise(t) != "si"]
    return bool(find_term(cleaned, approve) and find_term(cleaned, vocab["prod_terms"]))


def _named_ids(cleaned, ids):
    found = []
    for cid in sorted(ids, key=len, reverse=True):
        if valid_scope(cid) and cid != SCOPE_PROJECT and re.search(
                r"(?<![\w-])%s(?![\w-])" % re.escape(cid.casefold()), cleaned):
            found.append(cid)
    return found


def ids_elsewhere(root):
    """``{change id: (kind, where)}`` of the changes other worktrees and branches of this clone hold
    (BUG-148: any id, with or without a hyphen). At most ``REF_SCAN_MAX`` refs are read."""
    out = {}
    here = os.path.realpath(str(root))
    rc, wts = pj.git(["worktree", "list", "--porcelain"], root)
    for ln in (wts.splitlines() if rc == 0 else []):
        if ln.startswith("worktree "):
            wt = ln[len("worktree "):].strip()
            if os.path.realpath(wt) == here:
                continue
            base = os.path.join(wt, "docs", "spec", "changes")
            try:
                names = os.listdir(base)
            except OSError:
                continue
            for n in names:
                if os.path.isfile(os.path.join(base, n, "spec.json")):
                    out.setdefault(n, ("worktree", os.path.realpath(wt)))
    rc, refs = pj.git(["for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"], root)
    for ref in [r for r in (refs.splitlines() if rc == 0 else []) if r and not r.endswith("/HEAD")][:REF_SCAN_MAX]:
        rc2, listing = pj.git(["ls-tree", "-d", "--name-only", "%s:docs/spec/changes" % ref], root)
        for n in (listing.splitlines() if rc2 == 0 else []):
            n = n.strip()
            if n and n != "archive":
                out.setdefault(n, ("branch", ref))
    return out


_WORD = re.compile(r"(?<![\w-])[a-z0-9][a-z0-9-]{1,62}(?![\w-])")


def _words(cleaned, exclude=()):
    """The words of the prompt that could be change ids (BUG-148: with or without a hyphen)."""
    ex = set(exclude)
    return [w for w in dict.fromkeys(_WORD.findall(cleaned or "")) if w not in ex and valid_scope(w) and
            w != SCOPE_PROJECT]


def _change_like(cleaned, exclude=()):
    """Hyphenated words that look like a change id (not versions, not common words, BUG-148)."""
    ex = set(exclude)
    return [t for t in dict.fromkeys(_TOKEN.findall(cleaned or ""))
            if 3 <= len(t) <= 63 and t not in ex and t not in COMMON_HYPHENATED and
            not any(seg.isdigit() for seg in t.split("-"))]


def _vocab_words(vocab=None):
    v = vocab or default_vocabulary()
    out = set()
    for key in ("approve", "prod_terms", "negate"):
        for term in v.get(key) or []:
            out.update(normalise(term).split())
    return out | set(_ES_TERMS)


def _after_prod_term(cleaned, vocab=None):
    """The word typed right after a production term («… producción <id>», "… production <id>"), separated by
    spaces only: the one place a change id without a hyphen counts as named for another clone (D1 on BUG-158)."""
    v = vocab or default_vocabulary()
    out = []
    for term in v.get("prod_terms") or []:
        rx = _term_re(term)
        if rx is None:
            continue
        for m in rx.finditer(cleaned or ""):
            nxt = re.match(r"[ \t]+([a-z0-9][a-z0-9-]{2,62})(?![\w-])", cleaned[m.end():])
            if nxt:
                out.append(nxt.group(1))
    return out


def elsewhere_candidates(cleaned, exclude=(), vocab=None):
    """D1 on BUG-158: the words that may name a change of another clone — change-like (hyphenated, not a version,
    not a common word) or the word right after a production term — never an approval / production word. Any other
    word of the message never routes the approval to another clone."""
    ex = set(exclude) | _vocab_words(vocab)
    cands = _change_like(cleaned, ex) + [w for w in _after_prod_term(cleaned, vocab) if w not in ex]
    return [w for w in dict.fromkeys(cands) if valid_scope(w) and w != SCOPE_PROJECT]


def _committed(top, cid):
    """The change's spec.json is committed on the clone's HEAD (a file the agent just wrote does not count)."""
    rc, _ = pj.git(["cat-file", "-e", "HEAD:%s/%s/spec.json" % (Path(pj.CHANGES_DIR).as_posix(), cid)], top)
    return rc == 0


def clones_holding(anchors, ids):
    """BUG-158 (REQ-AN-001): ``{id: {clone id: top level}}`` for each of ``ids`` committed in the working tree of a
    Karvey clone found by the prod-gate's discovery (``clones.search_dirs``); a clone (its git common dir) counts
    once whatever number of its worktrees hold the change. Also returns how many clones were searched."""
    want = [i for i in dict.fromkeys(ids) if valid_scope(i) and i != SCOPE_PROJECT]
    out, seen = {}, set()
    clones_holding.uncommitted = {}
    for d in clones.search_dirs([a for a in anchors if a]):
        top = clones.toplevel(d)
        if not top or top in seen:
            continue
        seen.add(top)
        if not want or not pj.is_karvey_project(top):
            continue
        rid = None
        for cid in want:
            if not (Path(top) / pj.CHANGES_DIR / cid / "spec.json").is_file():
                continue
            if not _committed(top, cid):  # D7 R2: said in the reason, never recorded
                clones_holding.uncommitted.setdefault(cid, []).append(top)
                continue
            rid = rid or repo_id(top)
            out.setdefault(cid, {}).setdefault(rid, top)
    return out, len(seen)


def resolve_named_elsewhere(cleaned, anchors, exclude=()):
    """REQ-AN-001..003: the one change the prompt names among the local clones, or None when it names none of
    theirs. ``{scope, owner, why, candidates, searched}``; ``scope`` None = record nothing (``why`` says why)."""
    cands = elsewhere_candidates(cleaned, exclude)
    if not cands:  # nothing in the message names a change: the active-change fallback stays (REQ-AN-005)
        return None
    index, searched = clones_holding(anchors, cands)
    found = [w for w in cands if w in index]
    res = {"scope": None, "owner": None, "why": "", "candidates": [], "implicit": False, "searched": searched}
    if not found:
        loose = [w for w in cands if w in getattr(clones_holding, "uncommitted", {}) and _TOKEN.fullmatch(w)]
        if loose:  # D7 R2: the right reason, nothing recorded
            res["candidates"] = [loose[0]]
            res["why"] = ("change %s is held by %s but not committed on its HEAD; commit the change there, then "
                          "approve again" % (loose[0], ", ".join(clones_holding.uncommitted[loose[0]])))
            return res
        return None
    if len(found) > 1:
        res["candidates"] = sorted(found)
        res["why"] = ("it names %d changes (%s); one production approval covers one change: send one message per "
                      "change" % (len(found), ", ".join(sorted(found))))
        return res
    cid = found[0]
    owners = sorted(index[cid].values())
    res["candidates"] = [cid]
    if len(owners) > 1:
        res["why"] = ("change %s is held by %d clones (%s); approve it in a session inside the one you mean, "
                      "or remove the copy" % (cid, len(owners), ", ".join(owners)))
        return res
    if not _TOKEN.fullmatch(cid):
        # D1 H1b: an id without a hyphen may be an ordinary word ("now", "hoy") that another clone holds as a
        # change; it is never recorded from a session outside that clone: refuse and say where to approve it
        res["why"] = ("change %s is held by clone %s; an id without a hyphen is recorded only in a session inside "
                      "its clone (it may be an ordinary word): approve it there" % (cid, owners[0]))
        return res
    res.update(scope=cid, owner=owners[0], why="held by clone %s" % owners[0])
    return res


def phrase_change(cleaned, ids, active):
    """REQ-AN-004: the change a suggested phrase may name — the one id of this tree the prompt names; ``None``
    (``<change-id>``) when it names anything else that looks like a change; the active change only when the
    prompt names nothing."""
    named = _named_ids(cleaned, ids)
    others = elsewhere_candidates(cleaned, exclude=named)  # D7 F3: a word that may name a change elsewhere
    if named:
        return named[0] if len(named) == 1 and not others else None
    if others or _change_like(cleaned):
        return None
    return active


def resolve_prod_scope(root, cleaned, ids, active, anchors=None):
    """The change a production approval is for (REQ-HF-001..004; REQ-AN-001..007). Returns ``{scope, why,
    implicit, candidates, owner}``; ``scope`` is None when no marker may be written, ``why`` then says how to fix
    it; ``owner`` is the top level of the clone that receives the marker (None: this working tree)."""
    res = {"scope": None, "why": "", "implicit": False, "candidates": [], "owner": None}
    named = _named_ids(cleaned, ids)
    if len(named) > 1:
        res["why"] = ("it names %d changes (%s); one production approval covers one change: send one message "
                      "per change" % (len(named), ", ".join(sorted(named))))
        res["candidates"] = sorted(named)
        return res
    idset = set(ids)
    if len(named) == 1:
        # D7 F2: one id here and another change named elsewhere (a clone, a branch) is two changes: refuse
        others = elsewhere_candidates(cleaned, exclude=idset)
        if others:
            try:
                held = set(ids_elsewhere(root))
                if anchors is not None:
                    held |= set(clones_holding([str(root)] + list(anchors), others)[0])
            except Exception as exc:  # REQ-AN-007: fail open (no marker) with the line
                res["why"] = "the search for the named change failed (%s)" % type(exc).__name__
                return res
            extra = sorted(w for w in others if w in held)
            if extra:
                both = sorted(named + extra)
                res["candidates"] = both
                res["why"] = ("it names %d changes (%s); one production approval covers one change: send one "
                              "message per change" % (len(both), ", ".join(both)))
                return res
        res["scope"] = named[0]
        return res
    searched = None
    if anchors is not None:  # BUG-158: the clone that owns the named change, found as the prod-gate finds it
        try:
            other = resolve_named_elsewhere(cleaned, [str(root)] + list(anchors), exclude=idset)
        except Exception as exc:  # REQ-AN-007: fail open (no marker) with the line
            res["why"] = "the search for the named change failed (%s)" % type(exc).__name__
            res["candidates"] = []
            return res
        if other is not None:
            searched = other.pop("searched")
            if other["scope"] is not None or other["why"]:
                res.update(other)
                return res
    elsewhere = ids_elsewhere(root)
    words = [w for w in _words(cleaned, idset)]
    tokens = [w for w in words if w in elsewhere] + [  # BUG-148: an id elsewhere, hyphen or not
        t for t in _change_like(cleaned, idset) if t not in elsewhere]
    for tok in tokens:
        kind, where = elsewhere.get(tok, (None, None))
        res["candidates"] = [tok]
        if kind == "worktree":
            res["why"] = ("change %s is not in this working tree; approve it in the worktree that holds it: %s"
                          % (tok, where))
        elif kind == "branch":
            res["why"] = ("change %s is not in this working tree; the branch %s holds it: open the session in a "
                          "tree of that branch and approve there" % (tok, where))
        else:
            continue
        return res
    if tokens:
        res["candidates"] = []  # BUG-158: never another change (the active one), never the unknown word (BUG-148)
        res["why"] = ("%s is not a change of this working tree, and no worktree, branch or local clone holds it%s; "
                      "check the id, or clone the repo that owns it next to this one or list it in project.json "
                      "repos" % (tokens[0], "" if searched is None else " (%d clones searched)" % searched))
        return res
    act = active or {}
    cands = list(act.get("candidates") or [])
    if act.get("change") and valid_scope(act["change"]):
        res.update(scope=act["change"], implicit=True, candidates=[act["change"]],
                   why="the active change of this branch" if act.get("reason") == "branch"
                   else "the only active change")
        return res
    res["candidates"] = cands
    res["why"] = ("no change named and %d active (%s); name the change" % (len(cands), ", ".join(cands))
                  if cands else "no change named and none active; name the change")
    return res


def describe_markers(root, ttl_min=None, now=None):
    """Every marker file of this clone as ``{kind, scope, age_min, state}`` (BUG-144), newest first."""
    out = []
    try:
        d = approvals_dir(root, create=False)
        files = sorted(Path(d).glob("*.json")) if Path(d).is_dir() else []
    except Exception:
        files = []
    now = now or now_dt()
    for f in files:
        try:
            m = json.loads(f.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, UnicodeDecodeError):
            out.append({"kind": "?", "scope": f.stem, "age_min": None, "state": "unreadable"})
            continue
        if not isinstance(m, dict) or m.get("kind") not in KINDS:
            continue
        created = parse_dt(m.get("created_at"))
        age = int((now - created).total_seconds() // 60) if created else None
        if m.get("consumed_at"):
            state = "consumed"
        else:
            ok, why = check_marker(m, root, ttl_min=ttl_min, now=now,
                                   kinds=("prod",) if m.get("kind") == "prod" else KINDS)
            state = "live" if ok else ("expired" if why.startswith("expired") else
                                       "used" if why == "consumed" and m.get("prod_used_at") else why)
        out.append({"kind": m.get("kind"), "scope": m.get("scope") or f.stem, "age_min": age, "state": state})
    out.sort(key=lambda x: (x["age_min"] is None, x["age_min"] or 0))
    return out
