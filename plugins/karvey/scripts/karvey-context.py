#!/usr/bin/env python3
"""karvey-context.py — the Karvey dashboard (architecture §1.7, wave1-hardening). Read-only.

    karvey-context.py [--root DIR] [--change ID]
                      [--section overview|open-work|approvals|enforcement|calibration|convergence|close-report]
                      [--json]
    karvey-context.py --metrics [--from YYYY-MM-DD --to YYYY-MM-DD] [--as-of YYYY-MM-DD] [--lane L] [--json]
    karvey-context.py --readiness [--json]
    karvey-context.py --backlog [--as-of YYYY-MM-DD] [--json]
    karvey-context.py --portfolio [--file PATH] [--client NAME] [--from --to --as-of] [--json]

- Opens every file read-only and never writes, also under ``--json`` (REQ-W1-072). JSON is parsed as
  JSON; Markdown tables are parsed by header name (``Type``, ``Status``, …), never by position.
- An unreadable file is listed as ``unreadable: <path> (<reason>)`` and the rest still renders.

Sections:
  overview      active changes, phase, days in phase (``stalled`` past ``stall_days``, ``unknown``
                without history), WIP against ``wip_limit`` (REQ-W1-069, REQ-W1-071)
  open-work     findings by type and status per change, BUG-NN not RESUELTO, ``[human]`` tasks
                awaiting a human, open backlog items, pending tracker outbox, open questions (owner, needed-by,
                ``overdue`` / ``date invalid``) and open risks of active changes (REQ-W1-068, REQ-W1-090, REQ-W3-030)
  approvals     every approval from requirements to prod: by, role, date, or ``skipped: <reason>``;
                ``approved`` without ``by`` is ``approver missing`` (REQ-W1-070)
  enforcement   prod-gate ``on (default)`` / ``on`` / ``off (…reviewed on origin/<prod>)``, git-flow,
                plan-gate, the approval marker (REQ-W1-026) and the guards' block counts from audit.log
  close-report  closed tasks without an actual (``actual missing``, REQ-W1-043)
  calibration   actual (AI + review) / estimate per work type over the last archived changes with data;
                a recalibration is proposed only when a type deviates by more than ``threshold_pct`` in
                each of the last ``window`` changes (D-07: 30 %, 3), else "not enough history" (REQ-W1-044)
  convergence   ``--change X``: exit 1 while a ``bug``/``spec-gap`` finding of X (or of a change X
                ``converges``) is ``open``/``routed``, or a BUG-NN routed to it is not RESUELTO with a
                named regression; each offender is listed (REQ-W1-107, REQ-W1-108). Not in the default set.

Work type (calibration): the task-status table's ``Type`` / ``work type`` column when present, else the
layer tag of the task (``[Backend]``, ``[Frontend]``, ``[Test]``, ``[Infra]``); ``[human]`` rows are skipped.

Exit: 0 · 1 only for ``--section convergence`` when not converged · 4 when there is no ``docs/spec``.
Python >= 3.9, standard library only.
"""
import argparse
import importlib.util
import json
import os
import re
import shlex
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import outbox as obx  # noqa: E402
from karvey_lib import approval, audit, metrics as mx, modes, project as pj  # noqa: E402
from karvey_lib import sponsor as spx  # noqa: E402
from karvey_lib import questions as qs, risks as rsk  # noqa: E402
from karvey_lib import portfolio as pfl  # noqa: E402
from karvey_lib import backlog as bkl  # noqa: E402

TOOL = "karvey-context"
CHANGE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SECTIONS = ("overview", "open-work", "approvals", "enforcement", "close-report", "calibration", "convergence")
DEFAULT_SECTIONS = SECTIONS[:-1]
ROW_MAX = 10 * 1024
RESOLVED = "RESUELTO"

_SPEC = importlib.util.spec_from_file_location("karvey_state", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                             "karvey-state.py"))
state = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(state)


class NotFound(Exception):
    pass


# --------------------------------------------------------------------------- read-only input
class Reader:
    """Every read goes through here, so unreadable files are collected instead of raised."""

    def __init__(self, root):
        self.root = Path(root)
        rel_spec, self.layout, self.layout_note = pj.spec_layout(self.root)  # docs/spec/ or spec/ (REQ-W3-048)
        self.spec = self.root / rel_spec
        self.unreadable = []   # [{"path", "reason"}]
        self.warnings = []

    def rel(self, p):
        try:
            return os.path.relpath(str(p), str(self.root)).replace(os.sep, "/")
        except ValueError:
            return str(p)

    def _fail(self, p, reason):
        item = {"path": self.rel(p), "reason": reason}
        if item not in self.unreadable:
            self.unreadable.append(item)

    def text(self, p, required=False):
        p = Path(p)
        try:
            with open(p, "rb") as fh:
                raw = fh.read()
        except FileNotFoundError:
            if required:
                self._fail(p, "missing")
            return None
        except OSError as exc:
            self._fail(p, exc.strerror or type(exc).__name__)
            return None
        try:
            return raw.decode("utf-8-sig").replace("\r\n", "\n")
        except UnicodeDecodeError as exc:
            self._fail(p, "not UTF-8 (%s)" % exc.reason)
            return None

    def json(self, p, required=False):
        t = self.text(p, required=required)
        if t is None:
            return None
        try:
            return json.loads(t)
        except ValueError as exc:
            self._fail(p, "invalid JSON (%s)" % exc)
            return None


def split_row(line):
    """Cells of a Markdown table row; ``\\|`` is a literal pipe."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, i = [], [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if c == "|":
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    cells.append("".join(cur).strip())
    return cells


_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def parse_tables(text):
    """Every Markdown table: ``[{"header": [names], "rows": [{name: cell}], "line": n}]``.

    Header names are lower-cased and stripped; a row keyed by header name, so reordering the
    columns gives the same values. Missing trailing cells are empty strings; rows over 10 KB are
    skipped.
    """
    lines = (text or "").split("\n")
    out = []
    i = 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and _SEP.match(lines[i + 1]):
            header = [h.strip().strip("*`").lower() for h in split_row(lines[i])]
            tbl = {"header": header, "rows": [], "line": i + 1}
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                if len(lines[j]) <= ROW_MAX:
                    cells = split_row(lines[j])
                    row = {h: (cells[k] if k < len(cells) else "") for k, h in enumerate(header)}
                    row["_line"] = j + 1
                    tbl["rows"].append(row)
                j += 1
            out.append(tbl)
            i = j
        else:
            i += 1
    return out


def find_table(tables, *required):
    """The first table whose header holds every name in ``required``."""
    for t in tables:
        if all(r in t["header"] for r in required):
            return t
    return None


def col(row, *names):
    for n in names:
        if n in row and row[n] != "":
            return row[n]
    return ""


def first_word(v):
    m = re.match(r"\s*([A-Za-z][A-Za-z-]*)", v or "")
    return m.group(1).lower() if m else ""


# --------------------------------------------------------------------------- model
def parse_dt(v):
    return state.parse_dt(v) if isinstance(v, str) else None


def now_dt(args):
    if getattr(args, "now", None):
        dt = parse_dt(args.now)
        if dt is None:
            raise ValueError("--now must be an ISO 8601 date-time with a zone")
        return dt
    return datetime.now().astimezone()


def settings(project):
    """``(wip_limit, stall_days, calibration)`` with defaults and warnings for bad values."""
    d = kl.defaults()
    warns = []
    p = project if isinstance(project, dict) else {}
    wip = p.get("wip_limit")
    if wip is not None and (not isinstance(wip, int) or isinstance(wip, bool) or wip < 1):
        warns.append(kl.issue("context.bad_setting", "wip_limit %r is invalid (integer >= 1); ignored" % (wip,),
                              severity="warning", file="docs/spec/project.json", path="$.wip_limit"))
        wip = None
    stall = p.get("stall_days", d["stall_days"])
    if not isinstance(stall, int) or isinstance(stall, bool) or stall < 1:
        warns.append(kl.issue("context.bad_setting", "stall_days %r is invalid; the default %d is used"
                              % (stall, d["stall_days"]), severity="warning", file="docs/spec/project.json",
                              path="$.stall_days"))
        stall = d["stall_days"]
    cal = dict(d["calibration"])
    pc = p.get("calibration") if isinstance(p.get("calibration"), dict) else {}
    for k in ("threshold_pct", "window"):
        v = pc.get(k)
        if v is None:
            continue
        if isinstance(v, int) and not isinstance(v, bool) and v >= 1:
            cal[k] = v
        else:
            warns.append(kl.issue("context.bad_setting", "calibration.%s %r is invalid; the default %d is used"
                                  % (k, v, cal[k]), severity="warning", file="docs/spec/project.json",
                                  path="$.calibration.%s" % k))
    return wip, stall, cal, warns


def load_changes(rd):
    """Every change directory (archive excluded) with its parsed spec.json (or None)."""
    base = rd.spec / "changes"
    out = []
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir(), key=lambda p: p.name):
        if not d.is_dir() or d.name == pj.ARCHIVE_NAME or d.name.startswith("."):
            continue
        data = rd.json(d / "spec.json", required=True)
        if data is not None and not isinstance(data, dict):
            rd._fail(d / "spec.json", "not a JSON object")
            data = None
        raw = data.get("phase") if data else None
        mapped, tier = state.map_phase(raw)
        out.append({"id": d.name, "dir": d, "data": data, "phase": mapped or raw, "phase_raw": raw,
                    "phase_tier": tier, "implemented": (d / pj.IMPLEMENTED_MARKER).exists()})
    return out


def is_active(c):
    return not c["implemented"] and c["phase"] not in pj.INACTIVE_PHASES


def entered_at(entry):
    if not isinstance(entry, dict):
        return None
    return parse_dt(entry.get("entered_at") if "phase" in entry else entry.get("at"))


def age_of(c, now, stall_days):
    hist = (c["data"] or {}).get("phase_history")
    last = hist[-1] if isinstance(hist, list) and hist else None
    at = entered_at(last)
    if at is None:
        return {"days": None, "text": "unknown", "stalled": False, "since": None}
    days = max(0, (now - at).days)
    stalled = days > stall_days
    return {"days": days, "text": "%dd%s" % (days, " stalled" if stalled else ""), "stalled": stalled,
            "since": at.isoformat(timespec="seconds")}


def deployed_not_archived(changes, ctx):
    """Changes in ``deployed`` for more than ``deployed_stall_days`` (REQ-W2-056): the deploy date is the
    ``deployed`` entry of ``phase_history``, else the last production ``deploys[]`` record."""
    limit = (ctx["project"] or {}).get("deployed_stall_days") if isinstance(ctx["project"], dict) else None
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        limit = kl.defaults().get("deployed_stall_days", 7)
    out = []
    for c in changes:
        data = c["data"] or {}
        if c["phase"] != "deployed":
            continue
        at = None
        for e in reversed(data.get("phase_history") or []):
            if isinstance(e, dict) and e.get("phase") == "deployed":
                at = parse_dt(e.get("entered_at"))
                break
        if at is None:
            prod = [d for d in (data.get("deploys") or []) if isinstance(d, dict) and d.get("env") == "prod"]
            at = parse_dt(prod[-1].get("at")) if prod else None
        if at is None:
            continue
        days = max(0, (ctx["now"] - at).days)
        if days > limit:
            out.append({"change": c["id"], "days": days, "text": "deployed %d d, not archived" % days})
    return out


def overview(rd, ctx):
    changes = ctx["changes"]
    active = [c for c in changes if is_active(c)]
    rows = []
    for c in active:
        age = age_of(c, ctx["now"], ctx["stall_days"])
        row = {"change": c["id"], "phase": c["phase"], "age": age,
               "lane": state.ln.lane_of(c["data"])[0] if c["data"] else None}
        if c["phase_tier"] in ("exact", "proposed"):
            row["phase_raw"] = c["phase_raw"]
        if c["data"] is not None and c["phase_tier"] != "unmappable":
            try:
                nxt = state.compute_next(c["data"])
                row["next"] = {"phase": nxt.get("next_phase"), "status": nxt.get("status")}
            except Exception:  # an odd legacy shape must not take the dashboard down
                row["next"] = None
        rows.append(row)
    wip = ctx["wip_limit"]
    stall_deployed = deployed_not_archived(changes, ctx)
    res = {"layout": rd.layout, "layout_note": rd.layout_note,
           "deployed_not_archived": stall_deployed, "active": rows, "active_count": len(active),
           "wip": {"count": len(active), "limit": wip, "exceeded": bool(wip and len(active) > wip)}}
    try:
        act = pj.active_change(rd.root, project=ctx["project"] or {})
        res["current"] = act
    except Exception:
        res["current"] = None
    if res["wip"]["exceeded"]:
        ctx["warnings"].append(kl.issue("context.wip", "WIP %d/%d" % (len(active), wip), severity="warning"))
    return res


def read_findings(rd, cdir):
    t = rd.text(cdir / "findings.md")
    if t is None:
        return None
    tbl = find_table(parse_tables(t), "type", "status")
    items = []
    for r in (tbl["rows"] if tbl else []):
        fid = col(r, "#", "id")
        if not fid:
            continue
        items.append({"id": fid, "type": first_word(col(r, "type")), "status": first_word(col(r, "status")),
                      "status_text": col(r, "status"), "title": col(r, "title"),
                      "routed_to": col(r, "routed to"), "origin": col(r, "origin"), "phase": col(r, "phase")})
    return items


_BUG_HEAD = re.compile(r"^## (BUG-\d+)\s*[—-]\s*(.*)$")
_BUG_FIELD = re.compile(r"^- \*\*(Current state|Change / origin|Priority):\*\*\s*(.*)$")


def read_bugs(rd):
    """``{BUG-NN: {id, title, state, origin, regression, priority, sources}}`` from the tracker and the
    index; the tracker's state wins, a mismatch is a warning."""
    bugs = {}
    t = rd.text(rd.root / "docs" / "bugs_dev_testing.md")
    if t is not None:
        cur, section = None, None
        for line in t.split("\n"):
            m = _BUG_HEAD.match(line)
            if m:
                cur = bugs.setdefault(m.group(1), {"id": m.group(1), "title": m.group(2).strip(), "state": "",
                                                   "origin": "", "regression": "", "priority": "", "sources": []})
                cur["sources"].append("docs/bugs_dev_testing.md")
                section = None
                continue
            if cur is None:
                continue
            f = _BUG_FIELD.match(line)
            if f:
                key = {"Current state": "state", "Change / origin": "origin", "Priority": "priority"}[f.group(1)]
                cur[key] = f.group(2).strip()
                continue
            if line.startswith("### "):
                section = line[4:].strip().lower()
                continue
            if line.startswith("## "):
                cur, section = None, None
                continue
            if section == "regression test" and line.strip() and not cur["regression"]:
                cur["regression"] = line.strip()
    t = rd.text(rd.spec / "incidents-index.md")
    if t is not None:
        tbl = find_table(parse_tables(t), "bug", "current state")
        for r in (tbl["rows"] if tbl else []):
            bid = col(r, "bug")
            if not re.match(r"^BUG-\d+$", bid):
                continue
            b = bugs.get(bid)
            st = col(r, "current state")
            if b is None:
                b = bugs[bid] = {"id": bid, "title": col(r, "title"), "state": st, "origin": "",
                                 "regression": "", "priority": col(r, "priority"), "sources": []}
            elif b["state"] and st and st != b["state"]:
                rd.warnings.append(kl.issue("context.bug_state_mismatch",
                                            "%s is %s in bugs_dev_testing.md but %s in incidents-index.md"
                                            % (bid, b["state"], st), severity="warning",
                                            file="docs/spec/incidents-index.md"))
            b["sources"].append("docs/spec/incidents-index.md")
            b["index_change"] = col(r, "change / finding")
            b["planned_in"] = col(r, "fix planned in")
            if not b["regression"]:
                b["regression"] = col(r, "regression test")
    return bugs


def has_regression(text):
    t = (text or "").strip()
    return bool(t) and not t.startswith("—") and not t.startswith("-") and t.lower() not in ("none", "n/a")


def read_plan_rows(rd, cdir):
    """The PLAN.md task-status rows ``[{task, status, estimate, actual_ai, actual_review, notes, …}]``."""
    t = rd.text(cdir / "PLAN.md")
    if t is None:
        return None, None
    tbl = find_table(parse_tables(t), "task", "status")
    rows = []
    for r in (tbl["rows"] if tbl else []):
        rows.append({"task": col(r, "task"), "status": col(r, "status"), "notes": col(r, "notes"),
                     "estimate": col(r, "estimate_min", "estimate"), "actual_ai": col(r, "actual_ai_min"),
                     "actual_review": col(r, "actual_review_min"), "type": col(r, "type", "work type", "work_type"),
                     "line": r["_line"]})
    return rows, t


_EXEC = re.compile(r"executor:\s*([^()\n|;,]+?)\s*(?:\(|$|\||;|,)")
_SINCE = re.compile(r"since\s+(\d{4}-\d{2}-\d{2}(?:[T ][0-9:]+(?:[+-]\d{2}:?\d{2}|Z)?)?)", re.I)


def human_waiting(rows, plan_text):
    out = []
    for r in rows or []:
        blob = " ".join((r["status"], r["notes"]))
        if "🙋" not in blob and "awaiting-human" not in blob.lower():
            continue
        tid = r["task"].split()[0] if r["task"] else ""
        executor = None
        m = _EXEC.search(r["notes"])
        if m:
            executor = m.group(1).strip()
        elif plan_text and tid:
            for line in plan_text.split("\n"):
                if tid in line and "executor:" in line:
                    m = _EXEC.search(line)
                    if m:
                        executor = m.group(1).strip()
                        break
        s = _SINCE.search(blob)
        out.append({"task": r["task"], "executor": executor or "unknown", "since": s.group(1) if s else "unknown"})
    return out


def read_backlog(rd):
    t = rd.text(rd.spec / "backlog.md")
    if t is None:
        return None
    tbl = find_table(parse_tables(t), "id", "status")
    return [{"id": col(r, "id"), "title": col(r, "title"), "priority": col(r, "priority"), "type": col(r, "type")}
            for r in (tbl["rows"] if tbl else []) if first_word(col(r, "status")) == "open"]


def read_outbox(rd, cdir):
    """Pending entries in the format ``karvey-config.py outbox`` writes (``karvey_lib.outbox``), with the
    same ready/blocked rule; an unparsable line is a warning here (the dashboard is read-only)."""
    p = cdir / obx.FILE
    t = rd.text(p)
    if t is None:
        return []
    entries = []
    for n, line in enumerate(t.split("\n"), 1):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            rd.warnings.append(kl.issue("context.outbox_line", "unparsable outbox line %d" % n, severity="warning",
                                        file=rd.rel(p)))
            continue
        if obx.is_pending(e):
            entries.append(e)
    return [{"id": e.get("id"), "op": e.get("op"), "key": e.get("key"), "parent_key": e.get("parent_key"),
             "blocked_by": e.get("blocked_by"), "state": e["state"], "attempts": e.get("attempts"),
             "last_error": e.get("last_error"), "created_at": e.get("created_at")}
            for e in obx.annotate(entries)]


def open_work(rd, ctx):
    res = {"findings": {}, "bugs": [], "human": {}, "backlog": [], "outbox": {}}
    for c in ctx["changes"]:
        items = read_findings(rd, c["dir"])
        if items is not None:
            counts = {}
            for it in items:
                counts.setdefault(it["type"] or "?", {}).setdefault(it["status"] or "?", 0)
                counts[it["type"] or "?"][it["status"] or "?"] += 1
            res["findings"][c["id"]] = {"counts": counts,
                                        "open": [it["id"] for it in items if it["status"] in ("open", "routed")]}
        rows, text = read_plan_rows(rd, c["dir"])
        hw = human_waiting(rows, text)
        if hw:
            res["human"][c["id"]] = hw
        ob = read_outbox(rd, c["dir"])
        if ob:
            res["outbox"][c["id"]] = ob
    bugs = read_bugs(rd)
    ctx["bugs"] = bugs
    res["bugs"] = [{"id": b["id"], "title": b["title"], "state": b["state"] or "unknown",
                    "priority": b.get("priority", "")}
                   for b in sorted(bugs.values(), key=lambda b: int(b["id"].split("-")[1]))
                   if (b["state"] or "").upper() != RESOLVED]
    res["backlog"] = read_backlog(rd) or []
    # open questions (owner, needed-by, overdue / date invalid) and open risks of active changes (REQ-W3-030)
    today = ctx["now"].date().isoformat()
    qt = rd.text(rd.spec / "questions.md")
    res["questions"] = [{k: q[k] for k in ("id", "question", "owner", "needed_by", "overdue", "date_invalid")}
                        for q in qs.open_questions(qs.parse(qt or ""), today)]
    res["risks"] = []
    for c in ctx["changes"]:
        if not is_active(c):
            continue
        rt = rd.text(c["dir"] / rsk.FILE)
        for r in rsk.open_risks(rsk.parse(rt or "")):
            res["risks"].append({"change": c["id"], "id": r["id"], "risk": r["risk"], "owner": r["owner"],
                                 "trigger": r["trigger"], "last_review": r["last_review"]})
    return res


def approval_row(c, key, phase, rd):
    data = c["data"] or {}
    aps = data.get("approvals") if isinstance(data.get("approvals"), dict) else {}
    ap = aps.get(key) if isinstance(aps.get(key), dict) else {}
    st = state.approval_state(data, phase)
    skipped = data.get("skipped") if isinstance(data.get("skipped"), dict) else {}
    row = {"phase": phase, "key": key, "state": st, "by": ap.get("by") or None, "role": ap.get("role") or None,
           "date": ap.get("date") or None, "ref": ap.get("ref") or None}
    if st == "skipped":
        reason = skipped.get(phase) if isinstance(skipped.get(phase), str) else state.embedded_skip(ap)
        if (reason or "").startswith("lane:") or (reason is None and state.lane_skips(data, phase)):
            row["state"] = "skipped (lane)"  # never pending, never awaiting approval (REQ-W2-021)
            row["text"] = "skipped (lane %s)" % data.get("lane")
            row["reason"] = reason or "lane:%s" % data.get("lane")
            return row
        row["text"] = "skipped: %s" % (reason or "(no reason)")
        row["reason"] = reason
        return row
    if key == "prod" and st != "approved":
        try:
            ledger, status = approval.read_ledger(rd.root, c["id"])
        except (approval.ApprovalError, OSError):
            ledger, status = None, "missing"
        lp = (ledger or {}).get("prod") if status == "ok" else None
        if isinstance(lp, dict) and lp.get("by"):
            row.update(state="approved", by=lp.get("by"), role=lp.get("role"), date=lp.get("date"),
                       ref=lp.get("ref"), source="ledger")
    if row["state"] == "approved":
        if not (isinstance(row["by"], str) and row["by"].strip()):
            row["text"] = "approved — approver missing"
            row["approver_missing"] = True
        else:
            ref = " · " + row["ref"] if row["ref"] else ""
            if row["role"] == "auto":  # shown apart from human approvals (REQ-W2-040)
                row["auto"] = True
                row["text"] = "auto-approved (-y) %s%s" % (row["date"] or "date missing", ref)
            else:
                row["text"] = "approved by %s (%s) %s%s%s" % (row["by"], row["role"] or "role missing",
                                                             row["date"] or "date missing", ref,
                                                             " · ledger" if row.get("source") == "ledger" else "")
    elif ap.get("approved") is True:  # prod with approved:true but not by/role/ref
        row["text"] = "approved — approver missing"
        row["approver_missing"] = True
    elif ap.get("generated") is True:
        row["text"] = "awaiting approval"
    else:
        row["text"] = "pending"
    return row


def approvals(rd, ctx):
    res = {}
    targets = ctx["targets"]
    for c in targets:
        if c["data"] is None:
            res[c["id"]] = {"unreadable": True}
            continue
        rows = []
        for p in state.machine()["phases"]:
            if p["approval"]:
                rows.append(approval_row(c, p["approval"], p["id"], rd))
        lane, source = state.ln.lane_of(c["data"])
        res[c["id"]] = {"approvals": rows, "lane": lane, "lane_source": source,
                        "auto": [r["key"] for r in rows if r.get("auto")]}
    return res


def enforcement(rd, ctx):
    project = ctx["project"] or {}
    enf = pj.enforcement_of(project)
    _, _, prod = pj.branch_flow(project)
    memo = []

    def reviewed():  # read once, only when a rule needs it (karvey_lib/project.py §3.5 rules)
        if not memo:
            memo.append(pj.read_reviewed_project_json(rd.root))
        return memo[0]

    res = {}
    on, code = pj.prod_gate_state(project, reviewed)
    if code == "default":
        res["prod_gate"] = {"state": "on", "text": "on (default)"}
    elif code == "on":
        res["prod_gate"] = {"state": "on", "text": "on"}
    elif code == "invalid":
        res["prod_gate"] = {"state": "on", "text": "on (invalid value %r)" % (enf["prod_gate_hook"],)}
    elif code == "off":
        res["prod_gate"] = {"state": "off", "text": "off (project.json, reviewed on origin/%s)" % prod}
    else:
        res["prod_gate"] = {"state": "on", "text": "on (off only in the working copy; origin/%s says otherwise: %s)"
                            % (prod or "?", reviewed()[1])}
    for k, name in (("git_flow_hook", "git_flow"), ("plan_gate_hook", "plan_gate")):
        v = pj.opt_in_state(k, project, reviewed)  # the guards' rule: working copy OR reviewed line
        res[name] = {"state": "on" if v else "off", "text": "on" if v else "off (opt-in)"}
    markers = []
    scopes = [c["id"] for c in ctx["targets"] if approval.valid_scope(c["id"])] + [approval.SCOPE_PROJECT]
    # the TTL the plan-gate applies: reviewed line only, clamped (guards.ttl_min)
    ttl = approval.clamp_ttl(pj.reviewed_value("plan_marker_ttl_min", reviewed))
    for scope in scopes:
        m, status = approval.read_marker(rd.root, scope)
        if status == "missing":
            continue
        if status == "corrupt":
            markers.append({"scope": scope, "state": "invalid", "text": "%s: ignored (forged or corrupt)" % scope})
            continue
        ok, why = approval.check_marker(m, rd.root, scope=scope, ttl_min=ttl, now=ctx["now"])
        if ok:
            created = parse_dt(m.get("created_at"))
            until = created + timedelta(minutes=approval.clamp_ttl(ttl if ttl is not None else m.get("ttl_min")))
            markers.append({"scope": scope, "state": "valid", "kind": m.get("kind"),
                            "until": until.isoformat(timespec="seconds"), "session_id": m.get("session_id"),
                            "text": "%s %s valid until %s" % (scope, m.get("kind"), until.isoformat(timespec="minutes"))})
        else:
            markers.append({"scope": scope, "state": "invalid", "text": "%s: %s" % (scope, why)})
    res["marker"] = markers or [{"scope": None, "state": "none", "text": "none"}]
    res["blocks"] = audit_blocks(rd)
    return res


def audit_blocks(rd):
    """Block decisions per guard in this clone's audit.log (read-only; no state dir is created)."""
    try:
        d = pj.state_dir(rd.root, create=False)
    except OSError:
        return {"total": 0, "by_guard": {}, "last": None}
    recs = audit.read(d, include_rotated=True) if d.is_dir() else []
    by, last = {}, None
    for r in recs:
        if isinstance(r, dict) and r.get("decision") == "block":
            gname = str(r.get("guard") or "?")
            by[gname] = by.get(gname, 0) + 1
            last = r.get("ts") or last
    return {"total": sum(by.values()), "by_guard": dict(sorted(by.items())), "last": last}


# --------------------------------------------------------------------------- estimates (T2)
_LAYER = re.compile(r"\[([A-Za-z][A-Za-z -]*)\]")


def num(v):
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(?:min)?\s*$", v or "")
    return float(m.group(1)) if m else None


def work_type(row):
    if row.get("type"):
        return row["type"].strip()
    m = _LAYER.search(row.get("task") or "")
    return m.group(1).strip() if m else "untyped"


def is_human(row):
    return "[human]" in (row.get("task") or "").lower()


def is_done(row):
    st = row.get("status") or ""
    return "✅" in st or first_word(st) == "done"


def close_report(rd, ctx):
    res = {}
    for c in ctx["targets"]:
        rows, _ = read_plan_rows(rd, c["dir"])
        if rows is None:
            continue
        missing = []
        for r in rows:
            if is_human(r) or not is_done(r):
                continue
            gaps = [k for k, v in (("actual_ai_min", r["actual_ai"]), ("actual_review_min", r["actual_review"]))
                    if num(v) is None]
            if gaps:
                missing.append({"task": r["task"], "missing": gaps, "text": "actual missing"})
        res[c["id"]] = {"missing": missing}
    return res


def change_ratios(rows):
    """``{type: {estimate, actual, ratio, deviation_pct, tasks}}`` for rows with an estimate and an actual."""
    acc = {}
    for r in rows or []:
        if is_human(r):
            continue
        est, ai, rev = num(r["estimate"]), num(r["actual_ai"]), num(r["actual_review"])
        if not est or ai is None:
            continue
        a = acc.setdefault(work_type(r), {"estimate": 0.0, "actual": 0.0, "tasks": 0})
        a["estimate"] += est
        a["actual"] += ai + (rev or 0.0)
        a["tasks"] += 1
    for a in acc.values():
        a["ratio"] = round(a["actual"] / a["estimate"], 3)
        a["deviation_pct"] = round((a["ratio"] - 1.0) * 100, 1)
    return acc


def calibration(rd, ctx):
    cal = ctx["calibration"]
    thr, window = cal["threshold_pct"], cal["window"]
    arch = rd.spec / "changes" / pj.ARCHIVE_NAME
    history = []
    if arch.is_dir():
        for d in sorted((x for x in arch.iterdir() if x.is_dir()), key=lambda x: x.name):
            rows, _ = read_plan_rows(rd, d)
            ratios = change_ratios(rows)
            if ratios:
                history.append({"change": d.name, "types": ratios})
    last = history[-window:]
    res = {"threshold_pct": thr, "window": window, "changes": last, "proposals": [],
           "enough_history": len(history) >= window}
    if not res["enough_history"]:
        res["text"] = "not enough history (%d of %d archived changes with data)" % (len(history), window)
        return res
    types = set(last[0]["types"])
    for h in last[1:]:
        types &= set(h["types"])
    for t in sorted(types):
        devs = [h["types"][t]["deviation_pct"] for h in last]
        if all(abs(x) > thr for x in devs):
            factor = round(sum(h["types"][t]["ratio"] for h in last) / len(last), 2)
            res["proposals"].append({"type": t, "deviations_pct": devs, "factor": factor,
                                     "text": "recalibrate %s: estimates x%.2f (deviation %s in the last %d changes)"
                                     % (t, factor, ", ".join("%+.0f%%" % x for x in devs), window)})
    res["text"] = "%d recalibration(s) proposed" % len(res["proposals"]) if res["proposals"] else \
        "no type deviates by more than %d%% in each of the last %d changes" % (thr, window)
    return res


# --------------------------------------------------------------------------- convergence (T2)
_BUG_ID = re.compile(r"\bBUG-\d+\b")


def routed_bugs(change, bugs, findings):
    ids = set()
    for b in bugs.values():
        origin = (b.get("origin") or "").strip()
        idx = (b.get("index_change") or "").strip()
        planned = b.get("planned_in") or ""
        if origin.split(" ")[0] == change or idx.split(" ")[0] == change or re.search(
                r"(^|[\s,(])%s($|[\s,)])" % re.escape(change), planned):
            ids.add(b["id"])
    for f in findings or []:
        ids.update(_BUG_ID.findall(f.get("routed_to") or ""))
        ids.update(_BUG_ID.findall(f.get("status_text") or ""))
    return sorted(ids, key=lambda x: int(x.split("-")[1]))


def convergence(rd, ctx):
    if ctx.get("bugs") is None:
        ctx["bugs"] = read_bugs(rd)
    bugs = ctx["bugs"]
    by_id = {c["id"]: c for c in ctx["changes"]}
    res, not_converged = {}, False
    for c in ctx["targets"]:
        scope = [c["id"]] + [x for x in ((c["data"] or {}).get("converges") or []) if isinstance(x, str)]
        offenders = []
        for cid in scope:
            cc = by_id.get(cid)
            if cc is None:
                offenders.append({"kind": "change", "id": cid, "reason": "change not found"})
                continue
            findings = read_findings(rd, cc["dir"])
            if findings is None:
                offenders.append({"kind": "findings", "id": cid, "reason": "findings.md missing or unreadable"})
                findings = []
            for f in findings:
                if f["type"] in ("bug", "spec-gap") and f["status"] in ("open", "routed"):
                    offenders.append({"kind": "finding", "change": cid, "id": f["id"], "type": f["type"],
                                      "reason": "%s %s" % (f["type"], f["status"])})
                elif (f.get("origin") or "").startswith("judge:") and f["status"] == "closed" and \
                        not re.match(r"^(accepted:(bug|spec-gap|emergent)\b|rejected:\s*\S)", f.get("routed_to") or ""):
                    offenders.append({"kind": "finding", "change": cid, "id": f["id"], "type": f["type"],
                                      "reason": "unresolved (no routing or reason)"})
            for bid in routed_bugs(cid, bugs, findings):
                b = bugs.get(bid)
                if b is None:
                    offenders.append({"kind": "bug", "change": cid, "id": bid, "reason": "not in the incident tracker"})
                elif (b.get("state") or "").upper() != RESOLVED:
                    offenders.append({"kind": "bug", "change": cid, "id": bid, "reason": b.get("state") or "no state"})
                elif not has_regression(b.get("regression")):
                    offenders.append({"kind": "bug", "change": cid, "id": bid,
                                      "reason": "RESUELTO without a named regression test"})
        res[c["id"]] = {"scope": scope, "converged": not offenders, "offenders": offenders}
        not_converged = not_converged or bool(offenders)
    return res, (kl.EXIT_FINDINGS if not_converged else kl.EXIT_OK)


def _render_t2(result, L):
    cr = result.get("close-report")
    if cr is not None:
        L.append("== CLOSE REPORT ==")
        for cid, r in sorted(cr.items()):
            if not r["missing"]:
                L.append("%s: every closed task has its actuals" % cid)
            for m in r["missing"]:
                L.append("%s: %s — actual missing (%s)" % (cid, m["task"], ", ".join(m["missing"])))
    ca = result.get("calibration")
    if ca is not None:
        L.append("== CALIBRATION ==")
        for h in ca["changes"]:
            L.append("%s: %s" % (h["change"], "; ".join("%s %.2f (%+.0f%%)" % (t, v["ratio"], v["deviation_pct"])
                                                       for t, v in sorted(h["types"].items()))))
        L.append(ca["text"])
        for p_ in ca["proposals"]:
            L.append("  " + p_["text"])
    cv = result.get("convergence")
    if cv is not None:
        L.append("== CONVERGENCE ==")
        for cid, r in sorted(cv.items()):
            L.append("%s (%s): %s" % (cid, ", ".join(r["scope"]), "converged" if r["converged"] else
                                      "NOT converged, %d offender(s)" % len(r["offenders"])))
            for o in r["offenders"]:
                L.append("  %s %s%s: %s" % (o["kind"], (o.get("change") + " ") if o.get("change") else "", o["id"],
                                            o["reason"]))


# --------------------------------------------------------------------------- gate summary (REQ-W2-027, 037)
_DEV_ID = re.compile(r"\bDEV-\d+\b")
_EST = re.compile(r"^\*\*Estimate:\*\*\s*(\d+(?:\.\d+)?)\s*min", re.M)
_HUMAN_TASK = re.compile(r"^###\s+(\S+)\s+\[human\]\s*(.*)$", re.M)
_REQ_ID = re.compile(r"\bREQ-[A-Z0-9]+-\d+\b")


def _postdeploy_gaps(infra_text):
    """REQ-W2-075: every ``karvey-postdeploy`` contract of ``infra.md`` that is incomplete (C-19 rules)."""
    spec = importlib.util.spec_from_file_location("karvey_postdeploy_ctx", str(Path(__file__).resolve().parent /
                                                                             "karvey-postdeploy.py"))
    pd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pd)
    found = pd.contracts(infra_text)
    if not found:
        return ["post-deploy contract: no karvey-postdeploy block in infra.md"]
    out = []
    for c, err in found:
        if err:
            out.append("post-deploy contract: %s" % err)
            continue
        probs = pd.contract_problems(c)
        if probs:
            out.append("post-deploy contract %s/%s: incomplete (%s)" % (c.get("service", "?"), c.get("env", "?"),
                                                                        "; ".join(probs)))
    return out


def _section_lines(text, rx, limit=12):
    """Non-empty lines under the first heading matching ``rx`` (up to the next heading of that level)."""
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(.*)$", ln)
        if m and re.search(rx, m.group(2), re.I):
            level, out = len(m.group(1)), []
            for x in lines[i + 1:]:
                h = re.match(r"^(#{1,6})\s", x)
                if h and len(h.group(1)) <= level:
                    break
                if x.strip() and not set(x.strip()) <= set("|-: "):
                    out.append(x.strip())
            return out[:limit]
    return None


def _judges_block(rd, c, phases, gate_res):
    from karvey_lib import judges as jd
    data = c["data"] or {}
    runs = [r for r in (data.get("judge_runs") or []) if isinstance(r, dict)]
    rows = jd.read_rows(c["dir"] / "findings.md")
    out = []
    for ph in phases:
        if ph not in jd.PHASES_WITH_RUBRIC:
            continue
        try:
            exp = jd.build_inputs(rd.root, c["id"], ph)
        except Exception as exc:  # noqa: BLE001 - a summary line, never a crash
            out.append({"phase": ph, "line": "judges: not run (%s)" % exc})
            continue
        if not exp["lenses"]:
            out.append({"phase": ph, "line": exp["status"]})
            continue
        got = {}
        for r in runs:
            if r.get("phase", ph) == ph and r.get("lens") in exp["lenses"]:
                got[r["lens"]] = r  # the last run of the lens counts
        verdicts = set()
        for lens in exp["lenses"]:
            r = got.get(lens)
            if r is None:
                out.append({"phase": ph, "lens": lens, "line": "judge %s: not run (no run record)" % lens})
                continue
            verdicts.add(r.get("verdict"))
            counts = r.get("findings") if isinstance(r.get("findings"), dict) else {}
            out.append({"phase": ph, "lens": lens, "verdict": r.get("verdict"), "model": r.get("model"),
                        "intra_model": r.get("intra_model"),
                        "line": "judge %s: %s · %s · model %s%s" % (
                            lens, r.get("verdict") or "?",
                            ", ".join("%s %s" % (k, counts[k]) for k in jd.SEVERITIES if counts.get(k)) or "no findings",
                            r.get("model") or "?", " (intra-model)" if r.get("intra_model") else "")})
        if len(verdicts) > 1:
            out.append({"phase": ph, "line": "judges disagree at %s: %s" % (ph, " vs ".join(sorted(v for v in verdicts if v)))})
        for f in rows:
            if (f.get("origin") or "").startswith("judge:") and f.get("phase") == ph \
                    and f.get("severity") in ("Critical", "High"):
                out.append({"phase": ph, "line": "  %s %s %s [%s]: %s" % (
                    f.get("id") or f.get("#"), f.get("severity"), f.get("origin"), f.get("status"), f.get("finding"))})
    return out


def gate_summary(rd, ctx):
    """One page per gate, built by the script so no section is silently omitted (REQ-W2-027, 037)."""
    args = ctx["args"]
    if not args.change or args.gate not in ("what", "how", "release"):
        raise ValueError("--section gate needs --change and --gate what|how|release")
    c = ctx["targets"][0]
    data = c["data"] or {}
    cdir, missing = c["dir"], []

    def src(name):
        t = rd.text(cdir / name)
        if t is None:
            missing.append("missing: %s" % rd.rel(cdir / name))
        return t

    lane = data.get("lane") or "legacy"
    phases, arts = [], []
    for pid in state.gate_phases(args.gate):
        st = state.approval_state(data, pid)
        lane_skip = st == "skipped" and state.lane_skips(data, pid)
        phases.append({"phase": pid, "state": "skipped (lane)" if lane_skip else st})
        if st == "skipped":
            continue
        for item in (state.phase_def(pid).get("produces") or []):
            item = item.rstrip("?")
            if any(ch in item for ch in "*["):
                continue
            arts.append("%s: %s" % (item, "present" if (cdir / item).exists() else "missing"))
    res = {"change": c["id"], "gate": args.gate, "lane": lane, "phases": phases, "artifacts": arts,
           "judges": _judges_block(rd, c, [p["phase"] for p in phases if p["state"] not in ("skipped", "skipped (lane)")], None),
           "sections": {}, "omissions": [], "missing": missing}
    cost = sum(float(r.get("usd") or 0) for r in (data.get("judge_runs") or []) if isinstance(r, dict))
    res["judge_cost_usd"] = round(cost, 2)
    if args.gate == "how":
        arch = src("architecture.md")
        if arch is not None:
            for key, rx in (("decisions", r"decision"), ("risks", r"risk")):
                lines = _section_lines(arch, rx)
                res["sections"][key] = lines if lines is not None else ["missing: %s section in architecture.md" % key]
            gaps = []
            if not re.search(r"post-deploy", arch, re.I):
                gaps.append("post-deploy verification contract: missing")
            if not re.search(r"rollback", arch, re.I):
                gaps.append("rollback: missing")
            res["sections"]["contract_gaps"] = gaps or ["none"]
        dev = rd.text(cdir / "deviations.md")
        if dev is None:
            res["sections"]["deviations"] = ["none (no deviations.md)"]
        else:
            entries = [ln.strip() for ln in dev.split("\n") if re.match(r"^(#{2,3}\s|\|\s*DEV-)", ln)
                       and _DEV_ID.search(ln)]
            res["sections"]["deviations"] = entries or ["none"]
            shown = set(_DEV_ID.findall("\n".join(entries)))
            for did in sorted(set(_DEV_ID.findall(dev)) - shown):
                res["omissions"].append("deviations.md: %s is not shown by this summary (no heading or table row)" % did)
        infra = rd.text(cdir / "infra.md")
        if infra is not None:
            gaps = [x for x in res["sections"].get("contract_gaps", []) if x != "none"]
            gaps += _postdeploy_gaps(infra)
            res["sections"]["contract_gaps"] = gaps or ["none"]
        if infra is not None and not re.search(r"security-scan", infra, re.I):
            # REQ-W2-068: the PR pipeline carries the same security-tool categories as QA
            devs = [x for x in res["sections"]["deviations"] if not x.startswith("none")]
            res["sections"]["deviations"] = devs + ["pipeline without a security-scan stage (infra.md; REQ-W2-068)"]
        tasks = src("tasks.md")
        if tasks is not None:
            est = sum(float(x) for x in _EST.findall(tasks))
            res["sections"]["estimated_cost"] = ["%g min over %d task(s) (tasks.md)" % (est, len(_EST.findall(tasks)))]
            res["sections"]["human_tasks"] = ["%s %s" % m for m in _HUMAN_TASK.findall(tasks)] or ["none"]
    if args.gate == "what" and any(p["phase"] == "design_graphic" and p["state"] not in ("skipped", "skipped (lane)")
                                   for p in phases):
        # the design judge's deterministic sub-score beside its verdict (REQ-W3-039)
        ct = rd.text(cdir / "contrast.json")
        try:
            cj = (json.loads(ct).get("result") or json.loads(ct)) if ct else None
        except (ValueError, AttributeError):
            cj = None
        if not isinstance(cj, dict) or "rows" not in cj:
            res["sections"]["contrast"] = ["not computed (karvey-contrast-check.py --delta %s --json > contrast.json)"
                                           % c["id"]]
        else:
            below = cj.get("below") or []
            res["sections"]["contrast"] = ["%d pair(s) × 2 schemes · %d below level" % (cj.get("pairs") or 0,
                                                                                        len(below))] + [
                "%s on %s (%s): %.2f:1 < %s" % (b["text"], b["background"], b["scheme"], b["ratio"], b["level"])
                for b in below] + ["unparseable: %s" % u for u in cj.get("unparseable") or []]
    if args.gate in ("how", "release"):
        req, tasks_t = rd.text(cdir / "requirements.md"), rd.text(cdir / "tasks.md")
        if req is None:
            missing.append("missing: %s" % rd.rel(cdir / "requirements.md"))
        elif tasks_t is not None:
            unc = sorted(set(_REQ_ID.findall(req)) - set(_REQ_ID.findall(tasks_t)))
            res["sections"]["uncovered_requirements"] = unc or ["none"]
    if args.gate == "release":
        # the risk review asked at the qa / release gate (REQ-W3-033): every open risk with owner, trigger and
        # last review; `risk R-N unreviewed` (risks.unreviewed, warn in 4.1) when reviewed before the qa entry
        items, warns = rsk.gate_review(rsk.parse(rd.text(cdir / rsk.FILE) or ""), rsk.phase_start(data, "qa"))
        mode = modes.resolve(root=rd.root, check_id="risks.unreviewed", project=ctx.get("project"))["mode"]
        res["sections"]["open_risks"] = ["%s %s · owner %s · trigger %s · last review %s" % (
            r["id"], r["risk"], r["owner"] or "?", r["trigger"] or "?", r["last_review"]) for r in items] or ["none"]
        res["risk_warnings"] = ["%s (%s)" % (w, mode) for w in warns] if mode != "off" else []
        hits = modes.read_hits(cdir / modes.HITS_FILE)
        for key, check in (("lane_check", "lane.diff"), ("coverage", "coverage.requirements"),
                           ("security", "security.tools"), ("manifest", "release.manifest")):
            hs = [h for h in hits if h.get("check") == check]
            res["sections"][key] = ["%s would refuse: %s" % (h.get("mode"), h.get("detail")) for h in hs] or \
                ["no %s hit recorded" % check]
    return res


def _render_gate(g, L):
    L.append("== GATE %s — %s (lane %s) ==" % (g["gate"], g["change"], g["lane"]))
    L.append("phases: " + ", ".join("%s %s" % (p["phase"], p["state"]) for p in g["phases"]))
    for a in g["artifacts"]:
        L.append("  " + a)
    for j in g["judges"]:
        L.append(j["line"])
    L.append("judge cost: %.2f USD" % g["judge_cost_usd"])
    for k, v in g["sections"].items():
        L.append("%s:" % k.replace("_", " "))
        L.extend("  " + x for x in v)
    for w in g.get("risk_warnings") or []:
        L.append("WARNING " + w)
    for o in g["omissions"]:
        L.append("OMISSION " + o)
    L.extend(g["missing"])


BUILDERS = {"overview": overview, "open-work": open_work, "approvals": approvals, "enforcement": enforcement,
            "close-report": close_report, "calibration": calibration, "convergence": convergence,
            "gate": gate_summary}


# --------------------------------------------------------------------------- rendering
def render(result, ctx):
    L = []
    ov = result.get("overview")
    if ov is not None:
        L.append("== OVERVIEW ==")
        L.append("layout %s%s" % (ov.get("layout") or "docs/spec/",
                                  " (%s: docs/spec/ used)" % ov["layout_note"] if ov.get("layout_note") else ""))
        if not ov["active"]:
            L.append("no active change")
        for r in ov["active"]:
            nxt = r.get("next") or {}
            L.append("%-24s %-14s lane %-11s %-12s next: %s (%s)" % (
                r["change"], r["phase"], r.get("lane") or "?", r["age"]["text"], nxt.get("phase") or "—",
                nxt.get("status") or "?"))
        for s in ov.get("deployed_not_archived") or []:
            L.append("%-24s %s — run /karvey-archive" % (s["change"], s["text"]))
        w = ov["wip"]
        if w["limit"]:
            L.append(("WARNING WIP %d/%d" if w["exceeded"] else "WIP %d/%d") % (w["count"], w["limit"]))
        else:
            L.append("WIP %d (no wip_limit)" % w["count"])
        cur = ov.get("current") or {}
        if cur.get("reason") == "several":
            L.append("several active: %s" % ", ".join(cur.get("candidates") or []))
    ow = result.get("open-work")
    if ow is not None:
        L.append("== OPEN WORK ==")
        for cid, f in sorted(ow["findings"].items()):
            parts = ["%s %s" % (t, ", ".join("%s %d" % (s, n) for s, n in sorted(st.items())))
                     for t, st in sorted(f["counts"].items())]
            L.append("findings %s: %s%s" % (cid, "; ".join(parts) or "none",
                                            " · open/routed: " + ", ".join(f["open"]) if f["open"] else ""))
        if ow["bugs"]:
            L.append("bugs not RESUELTO (%d): %s" % (len(ow["bugs"]),
                                                     ", ".join("%s %s" % (b["id"], b["state"]) for b in ow["bugs"])))
        else:
            L.append("bugs not RESUELTO: none")
        for cid, hw in sorted(ow["human"].items()):
            for h in hw:
                L.append("awaiting human %s: %s · executor %s · since %s" % (cid, h["task"], h["executor"], h["since"]))
        L.append("backlog open (%d): %s" % (len(ow["backlog"]), ", ".join(b["id"] for b in ow["backlog"]) or "none"))
        L.append("open questions (%d)%s" % (len(ow.get("questions") or []), ":" if ow.get("questions") else ": none"))
        L.extend("  " + qs.line(q) for q in ow.get("questions") or [])
        L.append("open risks of active changes (%d)%s" % (len(ow.get("risks") or []),
                                                         ":" if ow.get("risks") else ": none"))
        L.extend("  " + rsk.line(r["change"], r) for r in ow.get("risks") or [])
        for cid, ob in sorted(ow["outbox"].items()):
            L.append("tracker outbox %s: %d pending%s" % (cid, len(ob), "".join(
                " · %s %s%s" % (e.get("id"), e.get("op"), " blocked_by " + str(e["blocked_by"]) if e.get("state") == "blocked" else "")
                for e in ob)))
    ap = result.get("approvals")
    if ap is not None:
        L.append("== APPROVALS ==")
        for cid, a in sorted(ap.items()):
            if a.get("unreadable"):
                L.append("%s: spec.json unreadable" % cid)
                continue
            L.append("%s (lane %s):" % (cid, a.get("lane") or "?"))
            for r in a["approvals"]:
                L.append("  %-15s %s" % (r["key"], r["text"]))
            if a.get("auto"):
                L.append("  automatic approvals (role auto, not human): %s" % ", ".join(a["auto"]))
    en = result.get("enforcement")
    if en is not None:
        L.append("== ENFORCEMENT ==")
        L.append("prod-gate  %s" % en["prod_gate"]["text"])
        L.append("git-flow   %s" % en["git_flow"]["text"])
        L.append("plan-gate  %s" % en["plan_gate"]["text"])
        L.append("marker     %s" % "; ".join(m["text"] for m in en["marker"]))
        b = en.get("blocks") or {}
        L.append("blocks     %s" % ("none recorded" if not b.get("total") else "%d (%s) · last %s" % (
            b["total"], ", ".join("%s %d" % kv for kv in b["by_guard"].items()), b.get("last") or "?")))
    _render_t2(result, L)
    if result.get("gate") is not None:
        _render_gate(result["gate"], L)
    for u in result.get("unreadable", []):
        L.append("unreadable: %s (%s)" % (u["path"], u["reason"]))
    return "\n".join(L)


# --------------------------------------------------------------------------- metrics (wave2 §1.6)
_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _day(value, flag):
    if value is None:
        return None
    if not _ISO_DAY.match(value):
        raise ValueError("%s must be YYYY-MM-DD (got %r)" % (flag, value))
    datetime.strptime(value, "%Y-%m-%d")
    return value


def metric_period(args):
    """``(from, to, as_of)``: explicit inputs; without them the 28 days before ``--as-of`` (default today)."""
    as_of = _day(args.as_of, "--as-of") or datetime.now().astimezone().date().isoformat()
    to = _day(args.to, "--to") or as_of
    frm = _day(args.frm, "--from") or (datetime.strptime(to, "%Y-%m-%d") - timedelta(days=28)).date().isoformat()
    if frm > to:
        raise ValueError("--from %s is after --to %s" % (frm, to))
    return frm, to, as_of


def metric_records(rd, frm, to):
    """Change records (``karvey_lib.metrics``) of every change archived in ``[frm, to]``."""
    arch = rd.spec / "changes" / pj.ARCHIVE_NAME
    out = []
    if not arch.is_dir():
        return out
    for d in sorted((x for x in arch.iterdir() if x.is_dir()), key=lambda x: x.name):
        on = d.name[:10] if _ISO_DAY.match(d.name[:10]) else None
        if not on or on < frm or on > to:
            continue
        spec = rd.json(d / "spec.json", required=True)
        if not isinstance(spec, dict):
            continue
        rows, _ = read_plan_rows(rd, d)
        out.append({"id": spec.get("change_id") if isinstance(spec.get("change_id"), str) else d.name,
                    "spec": spec, "findings": read_findings(rd, d), "plan_rows": rows, "archived_on": on})
    return out


def metrics_view(args, rd):
    frm, to, as_of = metric_period(args)
    recs = metric_records(rd, frm, to)
    res = mx.compute_all(recs, frm, to, lane=args.lane)
    res["period"] = {"from": frm, "to": to, "as_of": as_of}
    if args.lane:
        res["lane"] = args.lane
    res["unreadable"] = list(rd.unreadable)
    return res


def readiness_records(rd):
    """Every change (active and archived) with its hits and its ``validate --strict`` error count."""
    base = rd.spec / "changes"
    dirs = []
    if base.is_dir():
        dirs = [d for d in sorted(base.iterdir(), key=lambda x: x.name) if d.is_dir() and d.name != pj.ARCHIVE_NAME
                and not d.name.startswith(".")]
        arch = base / pj.ARCHIVE_NAME
        if arch.is_dir():
            dirs += sorted((d for d in arch.iterdir() if d.is_dir()), key=lambda x: x.name)
    out = []
    for d in dirs:
        spec = rd.json(d / "spec.json")
        if not isinstance(spec, dict):
            continue
        strict = [i for i in state.validate_data(spec, "spec", True, rd.rel(d / "spec.json"))
                  if i["severity"] == "error"]
        out.append({"id": spec.get("change_id") if isinstance(spec.get("change_id"), str) else d.name,
                    "spec": spec, "findings": read_findings(rd, d), "hits": modes.read_hits(d / modes.HITS_FILE),
                    "strict_errors": len(strict)})
    return out


def readiness_view(args, rd):
    res = mx.readiness(readiness_records(rd), modes.check_ids())
    res["unreadable"] = list(rd.unreadable)
    return res


def render_readiness(res):
    L = ["== READINESS FOR 4.0 ==", "%d measured: %s" % (res["measured"], ", ".join(res["measured_changes"]) or "none")]
    for cid, c in sorted(res["checks"].items()):
        L.append("%-24s %s" % (cid, c["text"]))
    L.append(res["text"])
    return "\n".join(L)


# --------------------------------------------------------------------------- report (wave3 §1.14)
NO_CHANGES_FOR_CLIENT = "no changes for client"


def _change_dirs(rd):
    """``[(dir, archived)]`` of every change folder, active first then archived, by name."""
    base = rd.spec / "changes"
    out = []
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir(), key=lambda x: x.name):
        if d.is_dir() and d.name != pj.ARCHIVE_NAME and not d.name.startswith("."):
            out.append((d, False))
    arch = base / pj.ARCHIVE_NAME
    if arch.is_dir():
        out += [(d, True) for d in sorted(arch.iterdir(), key=lambda x: x.name) if d.is_dir()]
    return out


def _days_between(a, b):
    try:
        return (datetime.strptime(b, "%Y-%m-%d") - datetime.strptime(a, "%Y-%m-%d")).days
    except (TypeError, ValueError):
        return None


def report_view(args, rd):
    """The business-language status (REQ-W3-025): released in the period, in progress with phase and age, blocked
    and who unblocks, open risks, decisions awaited per stakeholder. Read-only."""
    frm, to, as_of = metric_period(args)
    W = spx.wording()
    lang = "en"
    client = (args.client or "").strip()
    res = {"period": {"from": frm, "to": to, "as_of": as_of}, "client": client or None, "released": [],
           "in_progress": [], "blocked": [], "open_risks": [], "decisions_awaited": {}, "note": None}
    ids = set()
    for d, archived in _change_dirs(rd):
        spec = rd.json(d / "spec.json")
        if not isinstance(spec, dict):
            continue
        if client and mx.client_of(spec).lower() != client.lower():
            continue
        cid = spec.get("change_id") if isinstance(spec.get("change_id"), str) else d.name
        ids.add(cid)
        for dep in spec.get("deploys") or []:
            day = spx._day(dep.get("at")) if isinstance(dep, dict) else None
            if dep.get("env") == "prod" and day and frm <= day <= to:
                res["released"].append({"change": cid, "version": str(dep.get("version") or ""), "date": day})
        phase = spec.get("phase")
        if archived or phase in ("deployed", "archived"):
            continue
        hist = [h for h in spec.get("phase_history") or [] if isinstance(h, dict)]
        start = spx._day(spec.get("created_at")) or (spx._day(hist[0].get("entered_at")) if hist else None)
        since = spx._day(hist[-1].get("entered_at")) if hist else None
        res["in_progress"].append({"change": cid, "phase": spx.word(W, "phases", phase, lang),
                                   "age_days": _days_between(start, as_of), "in_phase_days": _days_between(since, as_of)})
        rows, plan = read_plan_rows(rd, d)
        for r in rows or []:
            blob = " ".join((r["status"], r["notes"]))
            if "⛔" in blob or "blocked" in r["status"].lower():
                res["blocked"].append({"change": cid, "task": r["task"], "unblocks": "the team"})
        for h in human_waiting(rows, plan):
            ex = h["executor"] if h["executor"] != "unknown" else "no executor declared"
            res["blocked"].append({"change": cid, "task": h["task"], "unblocks": ex})
        rtext = rd.text(d / "risks.md")
        for r in spx.read_rows_text(rtext or ""):
            if re.match(r"^R-\d+$", (r.get("id") or "").strip()) and \
                    (r.get("state") or "open").strip().lower().startswith("open"):
                res["open_risks"].append({"change": cid, "risk": spx.normalise(r.get("risk") or ""),
                                          "owner": (r.get("owner") or "").strip() or "no owner",
                                          "state": spx.word(W, "risk_states", "open", lang)})
    qtext = rd.text(rd.spec / "questions.md")
    for r in spx.read_rows_text(qtext or ""):
        if not re.match(r"^Q-\d+$", (r.get("id") or "").strip()):
            continue
        if (r.get("state") or "open").strip().lower() not in ("", "open"):
            continue
        chs = [c for c in re.split(r"[\s,;]+", r.get("changes") or "") if c and c != "—"]
        if client and not (set(chs) & ids):
            continue
        owner = (r.get("owner") or "").strip() or "no owner"
        res["decisions_awaited"].setdefault(owner, []).append(
            {"question": spx.normalise(r.get("question") or ""), "needed_by": spx._day((r.get("needed by") or "").strip()),
             "changes": chs})
    res["released"].sort(key=lambda x: (x["date"], x["change"]))
    if client and not ids:
        res["note"] = "%s %s" % (NO_CHANGES_FOR_CLIENT, client)
    res["unreadable"] = list(rd.unreadable)
    return res


def render_report(res):
    p = res["period"]
    L = ["== REPORT %s .. %s (as of %s)%s ==" % (p["from"], p["to"], p["as_of"],
                                                  " client " + res["client"] if res.get("client") else "")]
    if res.get("note"):
        L.append(res["note"])
        return "\n".join(L)
    L.append("Released:")
    L += ["  %s — version %s on %s" % (r["change"], r["version"] or "?", r["date"]) for r in res["released"]] or \
        ["  nothing reached production in the period"]
    L.append("In progress:")
    L += ["  %s — %s · %s days (%s in this step)" % (c["change"], c["phase"], c["age_days"] if c["age_days"] is not None
                                                     else "?", c["in_phase_days"] if c["in_phase_days"] is not None
                                                     else "?") for c in res["in_progress"]] or ["  nothing"]
    L.append("Blocked:")
    L += ["  %s — %s · unblocks: %s" % (b["change"], b["task"], b["unblocks"]) for b in res["blocked"]] or ["  nothing"]
    L.append("Open risks:")
    L += ["  %s — %s · watched by %s" % (r["change"], r["risk"], r["owner"]) for r in res["open_risks"]] or ["  none"]
    L.append("Decisions awaited:")
    if res["decisions_awaited"]:
        for owner, qs in sorted(res["decisions_awaited"].items()):
            L.append("  %s:" % owner)
            L += ["    %s%s" % (q["question"], (" (needed by %s)" % q["needed_by"]) if q["needed_by"] else "") for q in qs]
    else:
        L.append("  none")
    return "\n".join(L)


def _fmt_value(v):
    if v is None:
        return "n/a"
    if isinstance(v, dict):
        return ", ".join("%s %s" % (k, _fmt_value(x)) for k, x in sorted(v.items()))
    return str(v)


def _fmt_cost(v):
    if not isinstance(v, dict):
        return _fmt_value(v)
    return "US$ %s · %d change(s) · estimated share %s · judges US$ %s" % (
        v["total_usd"], v["changes"], v["estimated_share"], v["judge_usd"])


def render_metrics(res):
    p = res["period"]
    L = ["== METRICS %s .. %s (as of %s)%s ==" % (p["from"], p["to"], p["as_of"],
                                                   " lane " + res["lane"] if res.get("lane") else ""),
         "changes: %s" % (", ".join(res["changes"]) or "none")]
    for m in mx.METRICS:
        tot = res["total"][m]
        fmt = _fmt_cost if m == "cost_per_change" else _fmt_value
        L.append("%-26s %s" % (m, fmt(tot["value"])))
        for lane, vals in sorted(res["lanes"].items()):
            L.append("  %-24s %s" % ("lane " + lane, fmt(vals[m]["value"])))
        if m == "cost_per_change" and isinstance(tot["value"], dict):
            for client, g in sorted(tot["value"]["by_client"].items()):
                L.append("  %-24s US$ %s · %d change(s) · estimated share %s" % (
                    "client " + client, g["usd"], g["changes"], g["estimated_share"]))
            for cid, c in sorted(tot["value"]["by_change"].items()):
                L.append("  %-24s US$ %s · %s tokens · review %s min · judges US$ %s · estimated share %s" % (
                    "change " + cid, c["usd"], c["tokens"], c["review_min"], c["judge_usd"], c["estimated_share"]))
        for r in tot["reasons"]:
            L.append("  %s" % r)
    for u in res.get("unreadable", []):
        L.append("unreadable: %s (%s)" % (u["path"], u["reason"]))
    return "\n".join(L)


# --------------------------------------------------------------------------- backlog (wave3 §1.21)
def backlog_view(args, rd):
    """Open items by WSJF score, the unscored apart, ``stale`` past 30 days since ``Reviewed``, malformed rows as
    ``invalid row`` with their id (REQ-W3-051). Read-only."""
    as_of = _day(args.as_of, "--as-of") or datetime.now().astimezone().date().isoformat()
    text = rd.text(rd.spec / "backlog.md")
    rows = bkl.parse(text or "")
    scored, unscored, invalid = [], [], []
    for r in rows:
        if r["status"] != "open":
            continue
        sc = bkl.score(r, as_of)
        item = {"id": r["id"], "title": r["title"], "client": r["client"], "reviewed": r["reviewed"],
                "stale": bkl.stale(r, as_of)}
        if sc["invalid"]:
            invalid.append({"id": r["id"], "reason": sc["invalid"]})
        elif sc["unscored"]:
            unscored.append(dict(item, reason=sc["unscored"]))
        else:
            scored.append(dict(item, score=sc["score"], urgency=sc["urgency"], effort=sc["effort"]))
    scored.sort(key=lambda x: (-x["score"], x["id"]))
    unscored.sort(key=lambda x: x["id"])
    return {"as_of": as_of, "file": None if text is None else "backlog.md", "scored": scored, "unscored": unscored,
            "invalid": invalid, "last_refinement": bkl.last_refinement(text or ""),
            "unreadable": list(rd.unreadable)}


def render_backlog(res):
    L = ["== BACKLOG (as of %s) · %d scored · %d unscored · %d invalid ==" % (
        res["as_of"], len(res["scored"]), len(res["unscored"]), len(res["invalid"]))]
    if res["file"] is None:
        L.append("no backlog.md")
    for x in res["scored"]:
        L.append("%6.2f  %-6s %s%s%s" % (x["score"], x["id"], x["title"], (" · " + x["client"]) if x["client"] else "",
                                         " · stale (reviewed %s)" % x["reviewed"] if x["stale"] else ""))
    if res["unscored"]:
        L.append("unscored:")
        L += ["        %-6s %s · %s%s" % (x["id"], x["title"], x["reason"], " · stale" if x["stale"] else "")
              for x in res["unscored"]]
    L += ["invalid row %s: %s" % (x["id"], x["reason"]) for x in res["invalid"]]
    return "\n".join(L)


# --------------------------------------------------------------------------- portfolio (wave3 §1.20)
def portfolio_file(args, root):
    """``--file``, else ``{ops_repo}/docs/spec/portfolio.json`` beside this repository, else this spec dir's."""
    if args.file:
        return Path(args.file) if os.path.isabs(args.file) else Path(os.getcwd()) / args.file
    if root is None:
        raise NotFound("no portfolio file: pass --file PATH (outside a Karvey project)")
    proj, _ = pj.load_project_json(root)
    ops = (proj or {}).get("ops_repo") if isinstance(proj, dict) else None
    if isinstance(ops, str) and ops and "/" not in ops and ops not in (".", ".."):
        cand = Path(root).parent / ops / pj.SPEC_DIR / "portfolio.json"
        if cand.is_file():
            return cand
    return pj.spec_dir(root) / "portfolio.json"


def portfolio_view(args, root):
    """Per client and repository, read-only and offline (REQ-W3-046, 047): active changes (phase, lane, age),
    questions and approvals awaited, releases and cost of the period; a repository that cannot be read says why."""
    frm, to, as_of = metric_period(args)
    f = portfolio_file(args, root)
    try:
        entries, problems = pfl.load(f)
    except pfl.NotRead as exc:
        raise NotFound("portfolio file %s: %s" % (f.name, exc))
    want = (args.client or "").strip().lower()
    clients, others = {}, set()
    for e in entries:
        if want and e["client"].lower() != want:  # REQ-W3-078: case-insensitive, the others not even read
            others.add(e["client"])
            continue
        row = {"path": pfl.sanitise(e["path"], 120), "owner": e["owner"], "state": e["state"], "layout": None,
               "active": [], "waiting": [], "released": [], "cost": None}
        if e["state"] == "ok":
            try:
                row.update(pfl.read_repo(e["abs"], frm, to, as_of))
            except pfl.NotRead as exc:
                row["state"] = pfl.NOT_KARVEY if str(exc) == pfl.NOT_KARVEY else "not read: %s" % exc
            for a in row["active"]:  # REQ-W3-079: printed, never run; a foreign id is checked first (F-69)
                rid = a.pop("id_raw", None)
                if isinstance(rid, str) and CHANGE_ID_RE.match(rid):
                    a["dashboard"] = "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/karvey-context.py\" --root %s --change %s" % (
                        shlex.quote(e["abs"]), rid)
                else:
                    a["dashboard"] = None
                    a["note"] = "invalid change id"
        clients.setdefault(e["client"], []).append(row)
    out = []
    for client in sorted(clients, key=str.lower):
        repos = sorted(clients[client], key=lambda r: r["path"])
        tot = {"active": sum(len(r["active"]) for r in repos), "waiting": sum(len(r["waiting"]) for r in repos),
               "released": sum(len(r["released"]) for r in repos),
               "usd": round(sum((r["cost"] or {}).get("usd", 0) for r in repos), 2)}
        out.append({"client": client, "repos": repos, "totals": tot})
    res = {"period": {"from": frm, "to": to, "as_of": as_of}, "file": f.name, "problems": problems,
           "clients": out, "repositories": sum(len(c["repos"]) for c in out), "client": args.client or None,
           "note": None}
    if want and not out:
        res["note"] = "no repositories for client %s" % pfl.sanitise(args.client, 80)
    elif want and others:
        res["note"] = "other clients: not shown"
    return res


def render_portfolio(res):
    p = res["period"]
    L = ["== PORTFOLIO %s .. %s (as of %s) · %d repositories · %d clients ==" % (
        p["from"], p["to"], p["as_of"], res["repositories"], len(res["clients"]))]
    L += ["portfolio file: %s" % x for x in res["problems"]]
    if res.get("note"):
        L.append(res["note"])
    for c in res["clients"]:
        L.append("client %s" % c["client"])
        for r in c["repos"]:
            head = "  %s%s%s" % (r["path"], (" (%s)" % r["layout"]) if r.get("layout") else "",
                                 (" · owner %s" % r["owner"]) if r["owner"] else "")
            if r["state"] != "ok":
                L.append("%s — %s" % (head, r["state"]))
                continue
            L.append(head + ((" · %s" % r["note"]) if r.get("note") else ""))
            L += ["    active   %s · %s · lane %s · %s d (%s d in step)" % (
                a["change"], a["phase"], a["lane"], "?" if a["age_days"] is None else a["age_days"],
                "?" if a["in_phase_days"] is None else a["in_phase_days"]) + (
                "\n             dashboard: %s" % a["dashboard"] if a.get("dashboard") else
                "\n             %s: no dashboard command" % a.get("note", "")) for a in r["active"]] or \
                ["    active   none"]
            for w in r["waiting"]:
                if w["kind"] == "approval":
                    L.append("    waiting  approval %s (%s)" % (w["item"], w["change"]))
                else:
                    L.append("    waiting  %s · owner %s · needed by %s%s" % (
                        w["item"], w["owner"], w["needed_by"], (" · " + w["flag"]) if w["flag"] else ""))
            L += ["    released %s %s on %s" % (x["change"], x["version"], x["date"]) for x in r["released"]]
            cost = r["cost"] or {}
            L.append("    cost     US$ %.2f · %d change(s) · estimated share %.2f" % (
                cost.get("usd", 0), cost.get("changes", 0), cost.get("estimated_share", 0)))
        t = c["totals"]
        L.append("  totals: %d active · %d waiting · %d released · US$ %.2f" % (t["active"], t["waiting"],
                                                                               t["released"], t["usd"]))
    return "\n".join(L)


# --------------------------------------------------------------------------- CLI
def build_context(args, rd):
    project = rd.json(rd.spec / "project.json")
    if project is not None and not isinstance(project, dict):
        rd._fail(rd.spec / "project.json", "not a JSON object")
        project = None
    wip, stall, cal, warns = settings(project)
    changes = load_changes(rd)
    if args.change:
        targets = [c for c in changes if c["id"] == args.change]
        if not targets:
            raise NotFound("change %r not found under docs/spec/changes" % args.change)
    else:
        targets = [c for c in changes if is_active(c)]
    return {"project": project, "wip_limit": wip, "stall_days": stall, "calibration": cal,
            "changes": changes, "targets": targets, "now": now_dt(args), "warnings": warns, "args": args,
            "bugs": None}


def run(args):
    if args.portfolio:  # with --file no project lookup at all: the view starts no process (REQ-W3-047)
        root = None if args.file else pj.find_root(start=os.getcwd(), root=args.root)
        res = portfolio_view(args, root)
        return kl.EXIT_OK, res, [], render_portfolio(res)
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None or not pj.spec_dir(root).is_dir():
        raise NotFound("no docs/spec or spec here (not a Karvey project): %s" % (args.root or os.getcwd()))
    rd = Reader(root)
    if rd.layout_note:
        rd.warnings.append(kl.issue("context.layout", "%s: docs/spec/ and spec/ both hold a Karvey spec; docs/spec/ "
                                    "is used" % rd.layout_note, severity="warning"))
    if args.readiness:
        res = readiness_view(args, rd)
        return kl.EXIT_OK, res, list(rd.warnings), render_readiness(res)
    if args.metrics:
        res = metrics_view(args, rd)
        return kl.EXIT_OK, res, list(rd.warnings), render_metrics(res)
    if args.report:
        res = report_view(args, rd)
        return kl.EXIT_OK, res, list(rd.warnings), render_report(res)
    if args.backlog:
        res = backlog_view(args, rd)
        return kl.EXIT_OK, res, list(rd.warnings), render_backlog(res)
    ctx = build_context(args, rd)
    sections = [args.section] if args.section else list(DEFAULT_SECTIONS)
    result = {"root": str(root), "sections": sections}
    code = kl.EXIT_OK
    for s in sections:
        out = BUILDERS[s](rd, ctx)
        if isinstance(out, tuple):
            out, c = out
            code = max(code, c)
        result[s] = out
    result["unreadable"] = list(rd.unreadable)
    return code, result, ctx["warnings"] + rd.warnings, render(result, ctx)


def build_parser():
    p = argparse.ArgumentParser(prog="karvey-context.py", description="Karvey dashboard (read-only).")
    p.add_argument("--root", help="Karvey project root (default: walk up from the cwd)")
    p.add_argument("--change", help="limit approvals/enforcement to this change")
    p.add_argument("--section", choices=sorted(BUILDERS), help="print only this section")
    p.add_argument("--now", help=argparse.SUPPRESS)  # tests: a fixed 'now'
    p.add_argument("--metrics", action="store_true", help="flow metrics over archived changes (read-only, reproducible)")
    p.add_argument("--from", dest="frm", metavar="YYYY-MM-DD", help="--metrics: first day of the period")
    p.add_argument("--to", metavar="YYYY-MM-DD", help="--metrics: last day of the period")
    p.add_argument("--as-of", dest="as_of", metavar="YYYY-MM-DD", help="--metrics: the reference day (default today)")
    p.add_argument("--lane", help="--metrics: only this lane")
    p.add_argument("--readiness", action="store_true",
                   help="4.0 readiness: measured changes and would-refuse / confirmed hits per check")
    p.add_argument("--gate", choices=["what", "how", "release"], help="--section gate: which merged gate")
    p.add_argument("--report", action="store_true",
                   help="business-language status for a period (released, in progress, blocked, risks, decisions)")
    p.add_argument("--client", help="--report / --portfolio: only this client's changes")
    p.add_argument("--backlog", action="store_true", help="open backlog items ranked by WSJF (read-only)")
    p.add_argument("--portfolio", action="store_true",
                   help="read-only, offline view of every repository of the portfolio file, per client")
    p.add_argument("--file", help="--portfolio: the portfolio file (default {ops_repo}/docs/spec/portfolio.json)")
    p.add_argument("--json", action="store_true", help="print one JSON envelope")
    return p


def main(argv=None):
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else kl.EXIT_USAGE
        if code != 0 and as_json:
            kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", "invalid arguments")]), True)
        return kl.EXIT_USAGE if code != 0 else 0
    try:
        code, result, warnings, human = run(args)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("context.not_found", str(exc))]),
                       args.json)
    except ValueError as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", str(exc))]), args.json)
    except Exception as exc:  # pragma: no cover - last resort, exit 5
        return kl.emit(kl.envelope(TOOL, kl.EXIT_INTERNAL,
                                   errors=[kl.issue("internal", "%s: %s" % (type(exc).__name__, exc))]), args.json)
    env = kl.envelope(TOOL, code, result=result, warnings=warnings)
    if args.json and (args.metrics or args.readiness or args.report or args.portfolio or args.backlog):  # byte-identical output: sorted keys, no wall clock, no absolute path
        sys.stdout.write(json.dumps(env, ensure_ascii=False, sort_keys=True) + "\n")
        return code
    return kl.emit(env, args.json, human=human)


if __name__ == "__main__":
    sys.exit(main())
