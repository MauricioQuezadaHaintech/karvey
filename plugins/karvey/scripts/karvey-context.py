#!/usr/bin/env python3
"""karvey-context.py — the Karvey dashboard (architecture §1.7, wave1-hardening). Read-only.

    karvey-context.py [--root DIR] [--change ID]
                      [--section overview|open-work|approvals|enforcement|calibration|convergence|close-report]
                      [--json]
    karvey-context.py --metrics [--from YYYY-MM-DD --to YYYY-MM-DD] [--as-of YYYY-MM-DD] [--lane L] [--json]
    karvey-context.py --readiness [--json]

- Opens every file read-only and never writes, also under ``--json`` (REQ-W1-072). JSON is parsed as
  JSON; Markdown tables are parsed by header name (``Type``, ``Status``, …), never by position.
- An unreadable file is listed as ``unreadable: <path> (<reason>)`` and the rest still renders.

Sections:
  overview      active changes, phase, days in phase (``stalled`` past ``stall_days``, ``unknown``
                without history), WIP against ``wip_limit`` (REQ-W1-069, REQ-W1-071)
  open-work     findings by type and status per change, BUG-NN not RESUELTO, ``[human]`` tasks
                awaiting a human, open backlog items, pending tracker outbox (REQ-W1-068, REQ-W1-090)
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
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import outbox as obx  # noqa: E402
from karvey_lib import approval, audit, metrics as mx, modes, project as pj  # noqa: E402

TOOL = "karvey-context"
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
    base = rd.root / pj.CHANGES_DIR
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


def overview(rd, ctx):
    changes = ctx["changes"]
    active = [c for c in changes if is_active(c)]
    rows = []
    for c in active:
        age = age_of(c, ctx["now"], ctx["stall_days"])
        row = {"change": c["id"], "phase": c["phase"], "age": age}
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
    res = {"active": rows, "active_count": len(active),
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
    t = rd.text(rd.root / pj.SPEC_DIR / "incidents-index.md")
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
    t = rd.text(rd.root / pj.SPEC_DIR / "backlog.md")
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
            row["text"] = "approved by %s (%s) %s%s%s" % (row["by"], row["role"] or "role missing",
                                                         row["date"] or "date missing",
                                                         " · " + row["ref"] if row["ref"] else "",
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
        res[c["id"]] = {"approvals": rows}
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
    arch = rd.root / pj.CHANGES_DIR / pj.ARCHIVE_NAME
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


BUILDERS = {"overview": overview, "open-work": open_work, "approvals": approvals, "enforcement": enforcement,
            "close-report": close_report, "calibration": calibration, "convergence": convergence}


# --------------------------------------------------------------------------- rendering
def render(result, ctx):
    L = []
    ov = result.get("overview")
    if ov is not None:
        L.append("== OVERVIEW ==")
        if not ov["active"]:
            L.append("no active change")
        for r in ov["active"]:
            nxt = r.get("next") or {}
            L.append("%-24s %-14s %-12s next: %s (%s)" % (r["change"], r["phase"], r["age"]["text"],
                                                          nxt.get("phase") or "—", nxt.get("status") or "?"))
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
            L.append(cid + ":")
            for r in a["approvals"]:
                L.append("  %-15s %s" % (r["key"], r["text"]))
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
    arch = rd.root / pj.CHANGES_DIR / pj.ARCHIVE_NAME
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
    base = rd.root / pj.CHANGES_DIR
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


def _fmt_value(v):
    if v is None:
        return "n/a"
    if isinstance(v, dict):
        return ", ".join("%s %s" % (k, _fmt_value(x)) for k, x in sorted(v.items()))
    return str(v)


def render_metrics(res):
    p = res["period"]
    L = ["== METRICS %s .. %s (as of %s)%s ==" % (p["from"], p["to"], p["as_of"],
                                                   " lane " + res["lane"] if res.get("lane") else ""),
         "changes: %s" % (", ".join(res["changes"]) or "none")]
    for m in mx.METRICS:
        tot = res["total"][m]
        L.append("%-26s %s" % (m, _fmt_value(tot["value"])))
        for lane, vals in sorted(res["lanes"].items()):
            L.append("  %-24s %s" % ("lane " + lane, _fmt_value(vals[m]["value"])))
        for r in tot["reasons"]:
            L.append("  %s" % r)
    for u in res.get("unreadable", []):
        L.append("unreadable: %s (%s)" % (u["path"], u["reason"]))
    return "\n".join(L)


# --------------------------------------------------------------------------- CLI
def build_context(args, rd):
    project = rd.json(rd.root / pj.PROJECT_JSON)
    if project is not None and not isinstance(project, dict):
        rd._fail(rd.root / pj.PROJECT_JSON, "not a JSON object")
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
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None or not (Path(root) / pj.SPEC_DIR).is_dir():
        raise NotFound("no docs/spec here (not a Karvey project): %s" % (args.root or os.getcwd()))
    rd = Reader(root)
    if args.readiness:
        res = readiness_view(args, rd)
        return kl.EXIT_OK, res, list(rd.warnings), render_readiness(res)
    if args.metrics:
        res = metrics_view(args, rd)
        return kl.EXIT_OK, res, list(rd.warnings), render_metrics(res)
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
    if args.json and (args.metrics or args.readiness):  # byte-identical output: sorted keys, no wall clock, no absolute path
        sys.stdout.write(json.dumps(env, ensure_ascii=False, sort_keys=True) + "\n")
        return code
    return kl.emit(env, args.json, human=human)


if __name__ == "__main__":
    sys.exit(main())
