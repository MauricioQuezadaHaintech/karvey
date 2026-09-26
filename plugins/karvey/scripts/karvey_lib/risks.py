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
