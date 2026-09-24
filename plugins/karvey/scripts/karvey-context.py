#!/usr/bin/env python3
"""karvey-context.py — the Karvey dashboard (architecture §1.7, wave1-hardening). Read-only.

    karvey-context.py [--root DIR] [--change ID]
                      [--section overview|open-work|approvals|enforcement|calibration|convergence|close-report]
                      [--json]

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
                plan-gate and the approval marker (REQ-W1-026)

Exit: 0 · 4 when there is no ``docs/spec``. Python >= 3.9, standard library only.
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
from karvey_lib import approval, project as pj  # noqa: E402

TOOL = "karvey-context"
SECTIONS = ("overview", "open-work", "approvals", "enforcement")
DEFAULT_SECTIONS = SECTIONS
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
                      "routed_to": col(r, "routed to")})
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
    p = cdir / "tracker-outbox.jsonl"
    t = rd.text(p)
    if t is None:
        return []
    out = []
    for n, line in enumerate(t.split("\n"), 1):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            rd.warnings.append(kl.issue("context.outbox_line", "unparsable outbox line %d" % n, severity="warning",
                                        file=rd.rel(p)))
            continue
        if not isinstance(e, dict) or e.get("done_at") or e.get("status") == "done":
            continue
        out.append({"id": e.get("id"), "op": e.get("op"), "parent_key": e.get("parent_key"),
                    "blocked_by": e.get("blocked_by"), "attempts": e.get("attempts"),
                    "last_error": e.get("last_error"), "created_at": e.get("created_at")})
    return out


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
    enf = project.get("enforcement") if isinstance(project.get("enforcement"), dict) else {}
    _, _, prod = pj.branch_flow(project)
    res = {}
    if "prod_gate_hook" not in enf:
        res["prod_gate"] = {"state": "on", "text": "on (default)"}
    elif enf["prod_gate_hook"] is True:
        res["prod_gate"] = {"state": "on", "text": "on"}
    elif enf["prod_gate_hook"] is False:
        reviewed, status = pj.read_reviewed_project_json(rd.root)
        renf = (reviewed or {}).get("enforcement") if isinstance((reviewed or {}).get("enforcement"), dict) else {}
        if status == "ok" and renf.get("prod_gate_hook") is False:
            res["prod_gate"] = {"state": "off", "text": "off (project.json, reviewed on origin/%s)" % prod}
        else:
            res["prod_gate"] = {"state": "on", "text": "on (off only in the working copy; origin/%s says otherwise: %s)"
                                % (prod or "?", status)}
    else:
        res["prod_gate"] = {"state": "on", "text": "on (invalid value %r)" % (enf["prod_gate_hook"],)}
    for k, name in (("git_flow_hook", "git_flow"), ("plan_gate_hook", "plan_gate")):
        v = enf.get(k)
        res[name] = {"state": "on" if v is True else "off", "text": "on" if v is True else "off (opt-in)"}
    markers = []
    scopes = [c["id"] for c in ctx["targets"] if approval.valid_scope(c["id"])] + [approval.SCOPE_PROJECT]
    ttl = enf.get("plan_marker_ttl_min")
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
    return res


BUILDERS = {"overview": overview, "open-work": open_work, "approvals": approvals, "enforcement": enforcement}


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
                " · %s %s%s" % (e.get("id"), e.get("op"), " blocked_by " + str(e["blocked_by"]) if e.get("blocked_by") else "")
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
    for extra in ctx.get("renderers", []):
        extra(result, L)
    for u in result.get("unreadable", []):
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
            "changes": changes, "targets": targets, "now": now_dt(args), "warnings": warns, "args": args}


def run(args):
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None or not (Path(root) / pj.SPEC_DIR).is_dir():
        raise NotFound("no docs/spec here (not a Karvey project): %s" % (args.root or os.getcwd()))
    rd = Reader(root)
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
    return kl.emit(kl.envelope(TOOL, code, result=result, warnings=warnings), args.json, human=human)


if __name__ == "__main__":
    sys.exit(main())
