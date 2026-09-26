"""The risk register of a change (architecture §1.17, C-17; REQ-W3-031..034).

``docs/spec/changes/{id}/risks.md`` holds one table::

    | ID | Risk | Probability | Impact | Owner | Trigger | Mitigation | State | Last review |

ids ``R-N`` are local to the register (not minted by the id tool); states ``open | mitigated | accepted | closed |
moved``; ``Last review`` = ``YYYY-MM-DD reviewer``. Architecture creates it from its risk analysis; any phase adds
rows; a lane without architecture creates it at the first risk; no file = no risks. State changes go through
``karvey-state.py risk`` (which also logs them in ``spec.json:risk_log``). Standard library only.
"""
import re
from pathlib import Path

FILE = "risks.md"
STATES = ("open", "mitigated", "accepted", "closed", "moved")
COLUMNS = ("ID", "Risk", "Probability", "Impact", "Owner", "Trigger", "Mitigation", "State", "Last review")
HEADER = "| " + " | ".join(COLUMNS) + " |\n|" + "|".join("-" * (len(c) + 2) for c in COLUMNS) + "|\n"
R_ID = re.compile(r"^R-\d+$")


def _cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def state_of(cell):
    """The state word of a ``State`` cell (``moved → BL-12`` → ``moved``), lower case."""
    w = (cell or "").strip().split(" ")[0].lower()
    return w


def parse(text):
    """``[{id, risk, probability, impact, owner, trigger, mitigation, state, state_cell, last_review,
    reviewed_on, line}]`` of the register table."""
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
        rid = r.get("id", "")
        if not R_ID.match(rid):
            continue
        lr = r.get("last review", "")
        m = re.match(r"^(\d{4}-\d{2}-\d{2})", lr)
        out.append({"id": rid, "risk": r.get("risk", r.get("description", "")),
                    "probability": r.get("probability", r.get("likelihood", "")), "impact": r.get("impact", ""),
                    "owner": r.get("owner", ""), "trigger": r.get("trigger", ""), "mitigation": r.get("mitigation", ""),
                    "state": state_of(r.get("state", "")), "state_cell": r.get("state", ""), "last_review": lr,
                    "reviewed_on": m.group(1) if m else None, "line": n})
    return out


def read(change_dir):
    """The rows of ``{change_dir}/risks.md``; ``[]`` when there is no register (a change without risks)."""
    p = Path(change_dir) / FILE
    try:
        return parse(p.read_text(encoding="utf-8-sig"))
    except OSError:
        return []


def problems(rows):
    """``[(risk id, field, message)]``: a risk without owner, an unknown state, a duplicate id."""
    out, seen = [], set()
    for r in rows:
        if r["id"] in seen:
            out.append((r["id"], "id", "%s: duplicate id" % r["id"]))
        seen.add(r["id"])
        if not r["owner"].strip() or r["owner"].strip() in ("—", "-"):
            out.append((r["id"], "owner", "%s: owner missing" % r["id"]))
        if r["state"] not in STATES:
            out.append((r["id"], "state", "%s: state %r is not one of %s" % (r["id"], r["state"], ", ".join(STATES))))
    return out


def open_risks(rows):
    return [r for r in rows if r["state"] == "open"]


ACTIONS = {"review": None, "close": "closed", "mitigate": "mitigated", "accept": "accepted", "move": "moved"}


def rewrite(text, rid, state_cell=None, last_review=None):
    """The register text with ``rid``'s ``State`` and ``Last review`` cells replaced (other rows untouched)."""
    lines = (text or "").split("\n")
    rows = {r["id"]: r for r in parse(text)}
    if rid not in rows:
        raise KeyError(rid)
    head_line = next(ln for ln in lines if ln.lstrip().startswith("|") and "ID" in ln and "Owner" in ln)
    head = [c.lower() for c in _cells(head_line)]
    n = rows[rid]["line"] - 1
    cells = _cells(lines[n])
    for i, h in enumerate(head):
        if h == "state" and state_cell is not None and i < len(cells):
            cells[i] = state_cell
        elif h == "last review" and last_review is not None and i < len(cells):
            cells[i] = last_review
    lines[n] = "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"
    return "\n".join(lines)


def line(change, r):
    """One open risk of a change as a dashboard line: change, id, owner, trigger, last review."""
    return "%s %s %s · owner %s · trigger %s · last review %s" % (
        change, r["id"], r["risk"], r["owner"] or "?", r["trigger"] or "?", r["last_review"] or "never")


def open_work_lines(root, today, active_ids, cap=None):
    """``(question lines, risk lines)`` for the open-work views: open questions of ``docs/spec/questions.md``
    (overdue first) and the open risks of the given active changes; ``cap`` bounds each list (REQ-W3-030)."""
    from . import questions as qs
    from . import project as pj
    root = Path(root)
    sdir = pj.spec_dir(root)
    try:
        qrows = qs.parse((sdir / "questions.md").read_text(encoding="utf-8-sig"))
    except OSError:
        qrows = []
    ql = [qs.line(q) for q in qs.open_questions(qrows, today)]
    rl = []
    for cid in active_ids:
        rl.extend(line(cid, r) for r in open_risks(read(sdir / "changes" / cid)))
    if cap:
        return qs.capped(ql, cap), qs.capped(rl, cap)
    return ql, rl


def phase_start(spec, phase="qa"):
    """The date (``YYYY-MM-DD``) the change last entered ``phase``, from ``spec.json:phase_history``; else None."""
    days = [str(e.get("entered_at") or "")[:10] for e in (spec or {}).get("phase_history") or []
            if isinstance(e, dict) and e.get("phase") == phase and e.get("entered_at")]
    return max(days) if days else None


def gate_review(rows, since):
    """The gate's risk review (REQ-W3-033): every ``open`` risk with owner, trigger and last review, and
    ``risk R-N unreviewed`` for each whose last review predates ``since`` (the qa phase entry) or is missing.

    Returns ``(items, warnings)``; items keep the register order, which is the order the owners are asked."""
    items, warns = [], []
    for r in open_risks(rows):
        unrev = bool(since) and (r["reviewed_on"] is None or r["reviewed_on"] < since)
        items.append({"id": r["id"], "risk": r["risk"], "owner": r["owner"], "trigger": r["trigger"],
                      "last_review": r["last_review"] or "never", "unreviewed": unrev})
        if unrev:
            warns.append("risk %s unreviewed" % r["id"])
    return items, warns


def archive_blockers(rows, risk_log):
    """What stops ``advance archived`` (REQ-W3-034, F-75): a risk still ``open`` (named), and a risk in another
    state with no ``spec.json:risk_log`` record reaching that state (``R-N: state without record`` — a hand edit)."""
    logged = {(e.get("risk"), e.get("to")) for e in (risk_log or []) if isinstance(e, dict)}
    out = []
    for r in rows:
        if r["state"] == "open":
            out.append("%s: open — close it with a reason or move it to the backlog (karvey-state.py risk "
                       "<change> %s close --reason … | move)" % (r["id"], r["id"]))
        elif (r["id"], r["state"]) not in logged:
            out.append("%s: state without record (%s set by hand; record it with karvey-state.py risk)"
                       % (r["id"], r["state"]))
    return out
