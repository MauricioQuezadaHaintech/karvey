"""The sponsor page's leak check (architecture §1.13, C-13; REQ-W3-023). Fail closed.

``check(fields, ctx)`` scans every field of the allow-listed page model (and the rendered page's text, passed as
one more field) with the rules of ``leak_patterns.json``:

- ``secret`` — public token formats, credential assignments, connection strings, URL credentials, signed URLs and
  long high-entropy strings;
- ``path`` — absolute POSIX or Windows paths, UNC paths, ``~/``;
- ``host`` — hostnames under non-public suffixes and private, loopback or link-local addresses;
- ``email`` — any address other than the ``email``-channel targets of the declared stakeholders (F-81);
- ``pii`` — phone-number shapes and digit runs of 8 or more that are not a date, an amount or a version (F-73);
- ``client`` — other clients' names (portfolio) and the project's ``leak.deny_terms`` (F-72); with neither, the
  note ``other-client names not checked`` and the other rules still run.

The result names the field and the rule of each hit, **never the matched value**. An exception inside the check is
itself a refusal (``rule: check-error``). Standard library only.
"""
import html
import json
import math
import re
from pathlib import Path

PATTERNS_FILE = Path(__file__).resolve().parent / "leak_patterns.json"
NOT_CHECKED = "other-client names not checked"
RULES = ("secret", "path", "host", "email", "pii", "client")
_CACHE = {}
_DATE = re.compile(r"^\d{4}[-/.]\d{2}[-/.]\d{2}$|^\d{2}[-/.]\d{2}[-/.]\d{4}$|^\d{8}$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:\.\d+)?$")
_TOKEN = re.compile(r"[A-Za-z0-9+/_=-]{32,}")


def patterns():
    if "p" not in _CACHE:
        raw = json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))
        comp = {k: [(r["id"], re.compile(r["re"])) for r in raw[k]] for k in ("secret", "path", "host")}
        comp["email"] = re.compile(raw["email"]["re"])
        comp["pii"] = re.compile(raw["pii"]["re"])
        comp["pii_min"] = int(raw["pii"]["min_digits"])
        comp["entropy"] = raw["entropy"]
        _CACHE["p"] = comp
    return _CACHE["p"]


def text_of_html(page):
    """The visible text of a rendered page: no style/script blocks, no tags, entities decoded."""
    t = re.sub(r"(?is)<(style|script)\b.*?</\1>", " ", page or "")
    t = re.sub(r"(?s)<!--.*?-->", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return html.unescape(t)


def _entropy(s):
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = float(len(s))
    return -sum(c / n * math.log(c / n, 2) for c in counts.values())


def _high_entropy(text, cfg):
    for m in _TOKEN.finditer(text):
        tok = m.group(0)
        if len(tok) < int(cfg["min_length"]):
            continue
        if not (re.search(r"[0-9]", tok) and re.search(r"[A-Za-z]", tok)):
            continue
        if _entropy(tok) >= float(cfg["min_bits_per_char"]):
            return True
    return False


def _pii(text, p):
    for m in p["pii"].finditer(text):
        s = m.group(0).strip()
        digits = re.sub(r"\D", "", s)
        if len(digits) < p["pii_min"]:
            continue
        if _DATE.match(s) or _VERSION.match(s):
            continue
        before = text[max(0, m.start() - 4):m.start()]
        after = text[m.end():m.end() + 4]
        if "$" in before or re.match(r"\s*(?:%|USD|US\$|EUR|CLP)", after):
            continue  # an amount
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?", s):
            continue  # a grouped amount
        return True
    return False


def _client(text, terms):
    low = text.lower()
    for t in terms:
        t = t.strip().lower()
        if t and re.search(r"(?<!\w)%s(?!\w)" % re.escape(t), low):
            return True
    return False


def _scan(text, ctx, p):
    rules = []
    for rid, rx in p["secret"]:
        if rx.search(text):
            rules.append("secret")
            break
    else:
        if _high_entropy(text, p["entropy"]):
            rules.append("secret")
    if any(rx.search(text) for _, rx in p["path"]):
        rules.append("path")
    if any(rx.search(text) for _, rx in p["host"]):
        rules.append("host")
    allowed = {a.lower() for a in ctx.get("allowed_emails") or []}
    if any(m.group(0).lower() not in allowed for m in p["email"].finditer(text)):
        rules.append("email")
    if _pii(text, p):
        rules.append("pii")
    terms = list(ctx.get("other_clients") or []) + list(ctx.get("deny_terms") or [])
    if terms and _client(text, terms):
        rules.append("client")
    return rules


def flatten(model, prefix=""):
    """``{field path: text}`` of every string in a model (lists indexed ``[i]``, dict keys dotted)."""
    out = {}
    if isinstance(model, dict):
        for k in sorted(model, key=str):
            out.update(flatten(model[k], "%s.%s" % (prefix, k) if prefix else str(k)))
    elif isinstance(model, list):
        for i, v in enumerate(model):
            out.update(flatten(v, "%s[%d]" % (prefix, i)))
    elif isinstance(model, str):
        out[prefix or "$"] = model
    return out


def check(fields, ctx=None):
    """``{ok, hits: [{field, rule}], notes}`` for ``{field: text}`` (use :func:`flatten` on a model).

    ``ctx``: ``allowed_emails`` (email-channel stakeholder targets), ``other_clients`` (names read from the
    portfolio file, ``None`` when it is not readable), ``deny_terms``."""
    ctx = ctx or {}
    notes = []
    if not ctx.get("other_clients") and not ctx.get("deny_terms"):
        notes.append(NOT_CHECKED)
    try:
        p = patterns()
        hits = []
        for field in sorted(fields):
            text = fields[field]
            if not isinstance(text, str) or not text:
                continue
            for rule in _scan(text, ctx, p):
                hits.append({"field": field, "rule": rule})
    except Exception as exc:  # fail closed: a broken check refuses the page
        return {"ok": False, "hits": [{"field": "*", "rule": "check-error"}],
                "notes": notes + ["check error: %s" % type(exc).__name__]}
    return {"ok": not hits, "hits": hits, "notes": notes}
