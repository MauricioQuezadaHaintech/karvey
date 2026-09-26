"""Open questions ``Q-NN`` (architecture §1.16, C-16; REQ-W3-028, 029, 030).

``docs/spec/questions.md`` (in the ops repo, beside ``decisions.md``) holds one table::

    | ID | Question | Owner | Needed by | Changes | Context | State | Resolved by |

``Q-NN`` ids are reserved with ``karvey-id.py next Q``. A question needs an owner (who decides: a stakeholder role
or name) and a needed-by date (``YYYY-MM-DD``, the day from which it blocks); the context (options seen, the effect
of waiting) is optional and is what the sponsor page shows under the question. Answering records a ``D-NN`` that
cites the ``Q-NN``; the row is kept and reads ``resolved → D-NN``. Rows are never deleted. Standard library only.
"""
import re
from datetime import datetime

HEADER = ("| ID | Question | Owner | Needed by | Changes | Context | State | Resolved by |\n"
          "|----|----------|-------|-----------|---------|---------|-------|-------------|\n")
TITLE = "# Open questions\n\n"
Q_ID = re.compile(r"^Q-\d+$")
D_ID = re.compile(r"^D-\d+(?:@[\w.-]+)?$")
OPEN, RESOLVED = "open", "resolved"


class QuestionError(ValueError):
    """A refused question: ``field`` names what is missing or wrong."""

    def __init__(self, field, message):
        self.field = field
        super().__init__(message)


def _cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def _esc(v):
    return re.sub(r"\s+", " ", str(v or "")).replace("|", "\\|").strip()


def valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return re.match(r"^\d{4}-\d{2}-\d{2}$", value) is not None
    except (TypeError, ValueError):
        return False


def parse(text):
    """``[{id, question, owner, needed_by, changes, context, state, resolved_by, line}]`` of the table."""
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
        qid = r.get("id", "")
        if not Q_ID.match(qid):
            continue
        state = r.get("state", "")
        m = re.search(r"\bD-\d+(?:@[\w.-]+)?", state + " " + r.get("resolved by", ""))
        out.append({"id": qid, "question": r.get("question", ""), "owner": r.get("owner", ""),
                    "needed_by": r.get("needed by", ""),
                    "changes": [c for c in re.split(r"[\s,;]+", r.get("changes", "")) if c and c not in ("—", "-")],
                    "context": "" if r.get("context", "") in ("—", "-") else r.get("context", ""),
                    "state": RESOLVED if state.lower().startswith(RESOLVED) else (state.lower() or OPEN),
                    "resolved_by": m.group(0) if m else None, "line": n})
    return out


def check_new(question, owner, needed_by):
    """Refuse a question without its text, owner or a valid needed-by date, naming the field (REQ-W3-028)."""
    if not (isinstance(question, str) and question.strip()):
        raise QuestionError("question", "ask refused: the question text is missing")
    if not (isinstance(owner, str) and owner.strip()):
        raise QuestionError("owner", "ask refused: owner is missing (who decides: a stakeholder role or name)")
    if not (isinstance(needed_by, str) and needed_by.strip()):
        raise QuestionError("needed_by", "ask refused: needed-by is missing (the date from which it blocks)")
    if not valid_date(needed_by.strip()):
        raise QuestionError("needed_by", "ask refused: needed-by %r is not a date YYYY-MM-DD" % needed_by)


def add(text, qid, question, owner, needed_by, changes=(), context=""):
    """The file text with a new ``open`` row (the table is created when absent)."""
    if not Q_ID.match(qid or ""):
        raise QuestionError("id", "ask refused: %r is not a Q-NN id (reserve it with karvey-id.py next Q)" % qid)
    check_new(question, owner, needed_by)
    if any(q["id"] == qid for q in parse(text)):
        raise QuestionError("id", "ask refused: %s already exists" % qid)
    row = "| %s | %s | %s | %s | %s | %s | %s | — |\n" % (
        qid, _esc(question), _esc(owner), needed_by.strip(), _esc(", ".join(changes) or "—"),
        _esc(context) or "—", OPEN)
    t = text or ""
    if not parse(t) and "| ID | Question |" not in t:
        return (t.rstrip("\n") + "\n\n" if t.strip() else TITLE) + HEADER + row
    lines = t.rstrip("\n").split("\n")
    last = max(i for i, ln in enumerate(lines) if ln.lstrip().startswith("|"))
    lines.insert(last + 1, row.rstrip("\n"))
    return "\n".join(lines) + "\n"


def resolve(text, qid, decision):
    """The file text with ``qid`` marked ``resolved → D-NN`` (the row is kept, REQ-W3-029)."""
    if not D_ID.match(decision or ""):
        raise QuestionError("decision", "%r is not a D-NN reference" % decision)
    rows = {q["id"]: q for q in parse(text)}
    if qid not in rows:
        raise QuestionError("id", "%s not found in questions.md" % qid)
    lines = (text or "").split("\n")
    n = rows[qid]["line"] - 1
    cells = _cells(lines[n])
    head = [c.lower() for c in _cells(next(ln for ln in lines if ln.lstrip().startswith("| ID")))]
    for i, h in enumerate(head):
        if h == "state":
            cells[i] = "resolved → %s" % decision
        elif h == "resolved by":
            cells[i] = decision
    lines[n] = "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"
    return "\n".join(lines)


def open_questions(rows, today):
    """Open questions with ``overdue`` (needed-by before ``today``) and ``date_invalid`` flags, overdue first."""
    out = []
    for q in rows:
        if q["state"] != OPEN:
            continue
        ok = valid_date(q["needed_by"])
        out.append(dict(q, overdue=bool(ok and q["needed_by"] < today), date_invalid=not ok))
    return sorted(out, key=lambda q: (not q["overdue"], q["needed_by"] if not q["date_invalid"] else "9999", q["id"]))


def capped(lines, cap=5):
    """At most ``cap`` lines, then ``+N more — karvey-context`` (the session hook's bound, F-50; REQ-W3-030)."""
    lines = list(lines)
    if len(lines) <= cap:
        return lines
    return lines[:cap] + ["+%d more — karvey-context" % (len(lines) - cap)]


def line(q):
    """One open question as a dashboard line: id, text, owner, needed-by and its flag."""
    flag = " · overdue" if q.get("overdue") else (" · date invalid" if q.get("date_invalid") else "")
    return "%s %s · owner %s · needed by %s%s" % (q["id"], q["question"], q["owner"] or "?",
                                                          q["needed_by"] or "?", flag)
