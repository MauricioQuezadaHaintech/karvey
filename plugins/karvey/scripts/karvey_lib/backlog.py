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
import subprocess
from datetime import date

STATES = ("open", "promoted", "discarded", "done-direct")
STALE_DAYS = 30
REFINE_DAYS = 14
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
            head = None  # any non-table line ends the table: a row-less table never lends its header (BUG-115)
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
        status = (g("status") or "open").lower()
        out.append({"id": bid, "title": g("title") or "", "status": status, "state": state_of(status),
                    "value": g("value"), "effort": g("effort"), "cod": g("cod"), "needed_by": g("needed by"),
                    "client": g("client"), "reviewed": g("reviewed"), "commit": g("commit"), "line": n})
    return out


def state_of(status):
    """The state word of a Status cell: ``open (blocked)`` → ``open``, ``done-direct — abc1234`` → ``done-direct``
    (one rule for every view, BUG-135)."""
    m = re.match(r"\s*([a-z][a-z-]*)", (status or "open").lower())
    return m.group(1) if m else ""


def commit_exists(root, sha):
    """``True`` / ``False`` whether ``sha`` names a commit of the repository at ``root``; ``None`` when git cannot
    tell (no git, not a repository, timeout) — then only the format is checked."""
    try:
        cp = subprocess.run(["git", "cat-file", "-e", "%s^{commit}" % sha], cwd=str(root), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if cp.returncode == 0:
        return True
    try:
        top = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=str(root), stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return False if top.returncode == 0 else None


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


def refinement(text, today, refine_days=REFINE_DAYS):
    """``{date, days, state}`` of the ``Last refinement:`` line: state ``ok``, ``overdue`` (older than the cadence)
    or ``never refined`` (no line) — REQ-W3-052."""
    d = last_refinement(text)
    if d is None:
        return {"date": None, "days": None, "state": "never refined", "refine_days": refine_days}
    t = _date(today) if isinstance(today, str) else today
    days = (t - _date(d)).days
    return {"date": d, "days": days, "state": "overdue" if days > refine_days else "ok", "refine_days": refine_days}


def direct_problems(rows, root=None):
    """``done-direct`` without a commit of this repository (REQ-W3-050): ``[(id, line, message)]``. With ``root``
    the commit must exist in git (``git cat-file -e``), not only look like a hash (BUG-135)."""
    out = []
    for r in rows:
        if state_of(r["status"]) != "done-direct":
            continue
        c = (r.get("commit") or "").lower()
        if not _COMMIT.match(c):
            out.append((r["id"], r["line"], "%s: done-direct needs the commit that did it (Commit column)" % r["id"]))
        elif root is not None and commit_exists(root, c) is False:
            out.append((r["id"], r["line"], "%s: done-direct commit %s is not a commit of this repository"
                        % (r["id"], c)))
    return out


def state_problems(rows):
    """Items whose state is not one of ``STATES``: ``[(id, line, message)]`` (BUG-135)."""
    return [(r["id"], r["line"], "%s: status %r is not one of %s" % (r["id"], r["status"], ", ".join(STATES)))
            for r in rows if state_of(r["status"]) not in STATES]
