"""The backlog ranked by WSJF (architecture §1.21, C-21; REQ-W3-049..052).

``docs/spec/backlog.md`` keeps its table and gains the scoring columns
``Value | Effort | CoD | Needed by | Client | Reviewed | Commit`` (rules/backlog.md). The score is

    wsjf = (value + urgency) / effort          two decimals

- ``value`` 1–5;
- ``urgency`` = the cost of delay ``CoD`` 1–5, else from the days left to ``Needed by`` (past or ≤ 14 → 5, ≤ 30 → 4,
  ≤ 60 → 3, ≤ 90 → 2, otherwise 1);
- ``effort`` S / M / L = 1 / 2 / 3, or minutes: ≤ 60 → 1, ≤ 240 → 2, otherwise 3.

A missing value, effort or urgency makes the item ``unscored`` (never 0); a malformed cell makes the row an
``invalid row`` naming the column. States: ``open → promoted | discarded | done-direct`` (small work done without a
change: ``Commit`` is required). Standard library only.
"""
import re
from datetime import date

STATES = ("open", "promoted", "discarded", "done-direct")
STALE_DAYS = 30
EFFORT_SIZES = {"S": 1, "M": 2, "L": 3}
_BL_ID = re.compile(r"^BL-\d+$")
_NONE = ("", "—", "-", "–")
_COMMIT = re.compile(r"^[0-9a-f]{7,40}$")


def _cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def parse(text):
    """``[{id, title, status, value, effort, cod, needed_by, client, reviewed, commit, line, cells}]`` of the
    backlog table (by header name); the ``Last refinement:`` date is returned by ``last_refinement``."""
    out, head = [], None
    for n, line in enumerate((text or "").splitlines(), 1):
        if not line.lstrip().startswith("|"):
            head = None if out else head
            continue
        cells = _cells(line)
        if head is None:
            head = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        r = dict(zip(head, cells))
        bid = r.get("id", "")
        if not _BL_ID.match(bid):
            continue

        def g(k):
            v = (r.get(k) or "").strip()
            return None if v in _NONE else v
        out.append({"id": bid, "title": g("title") or "", "status": (g("status") or "open").lower(),
                    "value": g("value"), "effort": g("effort"), "cod": g("cod"), "needed_by": g("needed by"),
                    "client": g("client"), "reviewed": g("reviewed"), "commit": g("commit"), "line": n})
    return out


def last_refinement(text):
    """The ``Last refinement: YYYY-MM-DD`` header date, or None."""
    m = re.search(r"^\s*(?:\*\*)?Last refinement:(?:\*\*)?\s*(\d{4}-\d{2}-\d{2})\b", text or "", re.M)
    return m.group(1) if m else None


def _date(v):
    try:
        return date.fromisoformat(v)
    except (TypeError, ValueError):
        return None


def _int15(v):
    return int(v) if isinstance(v, str) and re.match(r"^[1-5]$", v.strip()) else None


def urgency(cod, needed_by, today):
    """``(urgency, error)``: the cost of delay, else from the days left to needed-by; ``(None, None)`` when neither."""
    if cod is not None:
        u = _int15(cod)
        return (u, None) if u else (None, "CoD %r is not 1-5" % cod)
    if needed_by is not None:
        d, t = _date(needed_by), _date(today) if isinstance(today, str) else today
        if d is None:
            return None, "Needed by %r is not YYYY-MM-DD" % needed_by
        days = (d - t).days
        for limit, u in ((14, 5), (30, 4), (60, 3), (90, 2)):
            if days <= limit:
                return u, None
        return 1, None
    return None, None


def effort(v):
    """``(effort 1-3, error)`` from S/M/L or minutes; ``(None, None)`` when empty."""
    if v is None:
        return None, None
    s = v.strip().upper()
    if s in EFFORT_SIZES:
        return EFFORT_SIZES[s], None
    m = re.match(r"^(\d+)\s*(?:M|MIN|MINS|MINUTES)?$", s)
    if m:
        mins = int(m.group(1))
        return (1 if mins <= 60 else 2 if mins <= 240 else 3), None
    return None, "Effort %r is not S/M/L or minutes" % v


def score(row, today):
    """``{score, urgency, effort, unscored, invalid}`` of one item (REQ-W3-049)."""
    out = {"score": None, "urgency": None, "effort": None, "unscored": None, "invalid": None}
    val = _int15(row.get("value")) if row.get("value") is not None else None
    if row.get("value") is not None and val is None:
        out["invalid"] = "Value %r is not 1-5" % row["value"]
        return out
    u, uerr = urgency(row.get("cod"), row.get("needed_by"), today)
    e, eerr = effort(row.get("effort"))
    if uerr or eerr:
        out["invalid"] = uerr or eerr
        return out
    if row.get("reviewed") is not None and _date(row["reviewed"]) is None:
        out["invalid"] = "Reviewed %r is not YYYY-MM-DD" % row["reviewed"]
        return out
    out["urgency"], out["effort"] = u, e
    missing = [k for k, v in (("value", val), ("effort", e), ("CoD or needed-by", u)) if v is None]
    if missing:
        out["unscored"] = "no " + ", ".join(missing)
        return out
    out["score"] = round((val + u) / e, 2)
    return out


def stale(row, today, days=STALE_DAYS):
    """True when the item was reviewed more than ``days`` ago (or never, when it has a date column at all)."""
    r = _date(row.get("reviewed"))
    t = _date(today) if isinstance(today, str) else today
    return r is not None and (t - r).days > days


def direct_problems(rows):
    """``done-direct`` without a commit (REQ-W3-050): ``[(id, line, message)]``."""
    out = []
    for r in rows:
        if r["status"] == "done-direct" and not (r.get("commit") and _COMMIT.match(r["commit"].lower())):
            out.append((r["id"], r["line"], "%s: done-direct needs the commit that did it (Commit column)" % r["id"]))
    return out
