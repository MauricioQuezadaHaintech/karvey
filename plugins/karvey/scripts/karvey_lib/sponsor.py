"""The sponsor page's model (architecture §1.13, C-13; REQ-W3-021, 080).

``build_model(root, change)`` reads **only** an allow-list of the change's artifacts and returns a dict that the
template renders and the leak check scans:

- *scope* — ``spec.json:goal``, the PRD's in-scope and out-of-scope bullets, the requirement **area** titles;
- *progress* — ``phase_history`` and ``lane`` through the wording table;
- *cost* — ``effort[]`` (US$, review minutes, estimated share, per phase) and ``judge_runs[]`` apart;
  none → ``not measured``, never a number;
- *risks* — ``changes/{id}/risks.md`` rows, state through the wording table;
- *waiting* — open ``Q-NN`` of ``docs/spec/questions.md`` whose owner matches the sponsor's role or name
  (case-insensitive), and the gate awaiting a human approval when the sponsor is also the declared approver;
- *released* — ``deploys[]`` with ``env: prod``.

Every section carries ``as_of``. Free text goes through :func:`normalise` (no requirement, finding, decision or
backlog id, no file path, no backticked command). Pure reads; standard library only.
"""
import json
import re
from datetime import date
from pathlib import Path

from . import SCHEMAS_DIR
from . import project as pj
from .judges import read_rows_text

WORDING_FILE = "wording.json"
NOT_MEASURED = "not measured"
NONE_RECORDED = "none recorded"
_ID_RE = re.compile(r"\b(?:REQ-[A-Z0-9]+-\d+|REQ-\d+|F-\d+|D-\d+|BL-\d+|Q-\d+|BUG-\d+|R-\d+|C-\d+|A-\d+)"
                    r"(?:@[\w.-]+)?\b")
_TICK_RE = re.compile(r"`[^`]*`")
_PATH_RE = re.compile(r"(?:(?<=\s)|^)(?:\.{0,2}/|~/)?[\w.-]+(?:/[\w.{}-]+)+/?(?=[\s,.;:)]|$)")
_EMPTY_PARENS = re.compile(r"\(\s*(?:see|cf\.?|e\.g\.|as in)?\s*[,;·]*\s*\)", re.I)
_TRAILING_BY = re.compile(r"\s+(?:by|with|see|in|at|via)\s*$", re.I)


def wording():
    with open(SCHEMAS_DIR / WORDING_FILE, encoding="utf-8-sig") as fh:
        return json.load(fh)


def word(table, cat, key, lang):
    entry = (table.get(cat) or {}).get(key) or {}
    return entry.get(lang) or entry.get("en") or key


def normalise(text):
    """Business text: ids, file paths and backticked commands removed, spaces collapsed."""
    if not isinstance(text, str):
        return ""
    t = _TICK_RE.sub("", text)
    t = _ID_RE.sub("", t)
    t = _PATH_RE.sub("", t)
    t = re.sub(r"\s*,\s*(?=[,)])", "", t)
    t = _EMPTY_PARENS.sub("", t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = _TRAILING_BY.sub("", t.strip())
    t = re.sub(r"\s{2,}", " ", t).strip(" ,;·-")
    return t.strip()


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return None


def _day(value):
    return value[:10] if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}", value) else None


def _section(text, *titles):
    """Bullet items of the first ``## title`` section (case-insensitive prefix match)."""
    if not text:
        return []
    out, on = [], False
    for ln in text.splitlines():
        if ln.startswith("## "):
            on = any(ln[3:].strip().lower().startswith(t) for t in titles)
            continue
        if on and re.match(r"^\s*[-*]\s+", ln):
            item = normalise(re.sub(r"^\s*[-*]\s+", "", ln))
            if item and not item.startswith("{"):
                out.append(item)
    return out


def _areas(text):
    """Requirement area titles (``## Requirement N: title (…)``), without ids."""
    out = []
    for ln in (text or "").splitlines():
        m = re.match(r"^##\s+Requirement\s+\d+\s*[:—-]\s*(.+?)\s*(?:\([^)]*\))?\s*$", ln)
        if m:
            t = normalise(m.group(1))
            if t:
                out.append(t)
    return out


def _matches(owner, who):
    """Owner cell matches a stakeholder by role or name, case-insensitively."""
    if not isinstance(owner, str) or not who:
        return False
    o = owner.strip().lower()
    return any(isinstance(x, str) and x.strip() and o == x.strip().lower() for x in (who.get("role"), who.get("name")))


def _same_person(a, b):
    if not a or not b:
        return False
    keys = {x.strip().lower() for x in (a.get("role"), a.get("name")) if isinstance(x, str) and x.strip()}
    return any(isinstance(x, str) and x.strip().lower() in keys for x in (b.get("role"), b.get("name")))


def _cost(spec, lang, W):
    eff = [e for e in spec.get("effort") or [] if isinstance(e, dict) and e.get("kind", "phase") == "phase"]
    usd = est = 0.0
    review = 0
    measured = False
    phases, at = {}, None
    for e in eff:
        u = e.get("usd") if isinstance(e.get("usd"), dict) else {}
        v = u.get("value")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            measured = True
            usd += v
            if u.get("quality") == "estimated":
                est += v
            ph = e.get("phase") or "unknown"
            row = phases.setdefault(ph, {"usd": 0.0, "review_min": 0, "quality": "exact"})
            row["usd"] += v
            if u.get("quality") != "exact":
                row["quality"] = u.get("quality") or "n/a"
        r = e.get("review_min") if isinstance(e.get("review_min"), dict) else {}
        if isinstance(r.get("value"), (int, float)) and not isinstance(r.get("value"), bool):
            review += r["value"]
            phases.setdefault(e.get("phase") or "unknown", {"usd": 0.0, "review_min": 0, "quality": "exact"})[
                "review_min"] += r["value"]
        if isinstance(e.get("at"), str) and (at is None or e["at"] > at):
            at = e["at"]
    judge = sum(j["usd"] for j in spec.get("judge_runs") or []
                if isinstance(j, dict) and isinstance(j.get("usd"), (int, float)) and not isinstance(j["usd"], bool))
    if not measured:
        return {"measured": False, "text": word(W, "labels", "not_measured", lang), "as_of": _day(at)}
    return {"measured": True, "usd": round(usd, 2), "review_min": review,
            "estimated_share": round(est / usd, 2) if usd else 0.0, "judge_usd": round(judge, 2),
            "by_phase": [{"step": word(W, "phases", ph, lang), "usd": round(v["usd"], 2), "review_min": v["review_min"],
                          "quality": v["quality"]} for ph, v in phases.items()],
            "as_of": _day(at)}


def _progress(spec, lang, W, machine):
    hist = [h for h in spec.get("phase_history") or [] if isinstance(h, dict)]
    by_phase = {}
    for h in hist:
        by_phase[h.get("phase")] = h
    phase = spec.get("phase")
    approvals = spec.get("approvals") if isinstance(spec.get("approvals"), dict) else {}
    steps = []
    order = [p["id"] for p in machine]
    cur = order.index(phase) if phase in order else -1
    skipped = spec.get("skipped") if isinstance(spec.get("skipped"), dict) else {}
    for i, pid in enumerate(order):
        if pid in skipped or pid in ("deploying",):
            continue
        h = by_phase.get(pid)
        if i < cur:
            state, day = "done", _day((h or {}).get("exited_at")) or _day((h or {}).get("entered_at"))
        elif i == cur:
            state, day = ("done" if phase in ("deployed", "archived") else "now"), _day((h or {}).get("entered_at"))
        else:
            state, day = "planned", None
        a = approvals.get(pid) if isinstance(approvals.get(pid), dict) else {}
        steps.append({"step": word(W, "phases", pid, lang), "state": state, "date": day,
                      "approved": bool(a.get("approved"))})
    lane = spec.get("lane") if isinstance(spec.get("lane"), str) else "legacy"
    last = max([_day(h.get("exited_at")) or _day(h.get("entered_at")) or "" for h in hist] or [""]) or None
    outcomes = [o for o in spec.get("gate_outcomes") or [] if isinstance(o, dict)]
    changes = bool(outcomes) and outcomes[-1].get("outcome") == "changes_requested"
    return {"phase": word(W, "phases", phase, lang), "phase_id": phase, "lane": word(W, "lanes", lane, lang),
            "steps": steps, "changes_requested": changes, "as_of": last}


def _risks(root, change, lang, W):
    text = _read(Path(root) / pj.CHANGES_DIR / change / "risks.md")
    out = []
    for r in read_rows_text(text or ""):
        rid = (r.get("id") or "").strip()
        if not re.match(r"^R-\d+$", rid):
            continue
        state = (r.get("state") or "open").strip().split(" ")[0].lower()
        out.append({"description": normalise(r.get("risk") or r.get("description") or ""),
                    "likelihood": normalise(r.get("probability") or r.get("likelihood") or "").lower(),
                    "impact": normalise(r.get("impact") or "").lower(),
                    "owner": normalise(r.get("owner") or ""), "trigger": normalise(r.get("trigger") or ""),
                    "mitigation": normalise(r.get("mitigation") or ""), "state_id": state,
                    "state": word(W, "risk_states", state, lang),
                    "last_review": _day((r.get("last review") or "").strip())})
    reviewed = [r["last_review"] for r in out if r["last_review"]]
    return {"items": out, "open": sum(1 for r in out if r["state_id"] == "open"),
            "as_of": max(reviewed) if reviewed else None, "recorded": text is not None}


def _questions(root, change, sponsor, today):
    text = _read(Path(root) / "docs" / "spec" / "questions.md")
    out = []
    for r in read_rows_text(text or ""):
        if not re.match(r"^Q-\d+$", (r.get("id") or "").strip()):
            continue
        state = (r.get("state") or "").strip().lower()
        if state and not state.startswith("open"):
            continue
        changes = r.get("changes") or ""
        if changes.strip() and change not in re.split(r"[\s,;]+", changes):
            continue
        if not _matches(r.get("owner"), sponsor):
            continue
        needed = _day((r.get("needed by") or "").strip())
        out.append({"question": normalise(r.get("question") or ""), "needed_by": needed,
                    "overdue": bool(needed and today and needed < today),
                    "context": normalise(r.get("context") or "")})
    return sorted(out, key=lambda q: (q["needed_by"] or "9999", q["question"]))


def _gates_waiting(spec, sponsor, approver, lang, W, machine):
    if not _same_person(sponsor, approver):
        return []
    phase = spec.get("phase")
    pdef = next((p for p in machine if p["id"] == phase), None)
    a = (spec.get("approvals") or {}).get(phase) if isinstance(spec.get("approvals"), dict) else None
    if not pdef or not pdef.get("approval") or not isinstance(a, dict):
        return []
    if a.get("generated") and not a.get("approved"):
        return [{"step": word(W, "phases", phase, lang), "gate": pdef.get("gate")}]
    return []


def _released(spec):
    out = []
    for d in spec.get("deploys") or []:
        if isinstance(d, dict) and d.get("env") == "prod" and d.get("verification") != "regression":
            out.append({"version": str(d.get("version") or ""), "date": _day(d.get("at"))})
    return out


def _history(root, change):
    p = Path(root) / pj.CHANGES_DIR / change / "sponsor-history.jsonl"
    out = []
    for ln in (_read(p) or "").splitlines():
        try:
            rec = json.loads(ln)
        except ValueError:
            continue
        if isinstance(rec, dict) and rec.get("outcome") in ("approved", "changes_requested"):
            out.append({"date": _day(rec.get("at")), "gate": rec.get("gate"), "outcome": rec["outcome"]})
    return list(reversed(out))[:12]


def _title(spec, prd):
    t = spec.get("title")
    if isinstance(t, str) and t.strip():
        return normalise(t)
    goal = spec.get("goal")
    if isinstance(goal, str) and goal.strip():
        first = re.split(r"(?<=[.;:])\s", normalise(goal), 1)[0].rstrip(".;:")
        return first[:120]
    return spec.get("change_id") or "change"


def build_model(root, change, today=None, project=None):
    """The allow-listed page model of ``change`` (see the module docstring)."""
    root = Path(root)
    cdir = root / pj.CHANGES_DIR / change
    spec = json.loads((cdir / "spec.json").read_text(encoding="utf-8-sig"))
    if project is None:
        project, _ = pj.load_project_json(root)
    W = wording()
    lang = spec.get("language") if spec.get("language") in W.get("languages", []) else "en"
    note = None if spec.get("language") in (None, lang) else word(W, "labels", "language_note", "en")
    with open(SCHEMAS_DIR / "state-machine.json", encoding="utf-8-sig") as fh:
        machine = json.load(fh)["phases"]
    st = pj.stakeholders(project or {}, spec)
    sponsor = st.get("sponsor")
    today = today or date.today().isoformat()
    prd = _read(cdir / "prd.md")
    req = _read(cdir / "requirements.md")
    goal = normalise(spec.get("goal") or "")
    waiting_q = _questions(root, change, sponsor, today) if sponsor else []
    gates = _gates_waiting(spec, sponsor, st.get("approver"), lang, W, machine) if sponsor else []
    model = {
        "change": change, "language": lang, "language_note": note, "title": _title(spec, prd),
        "sponsor": {"role": normalise(sponsor.get("role", "")), "name": normalise(sponsor.get("name", ""))}
        if sponsor else None,
        "scope": {"summary": goal, "included": _section(prd, "scope"), "excluded": _section(prd, "out of scope"),
                  "areas": _areas(req), "as_of": _day(spec.get("updated_at")) or _day(spec.get("created_at"))},
        "progress": _progress(spec, lang, W, machine),
        "cost": _cost(spec, lang, W),
        "risks": _risks(root, change, lang, W),
        "waiting": {"questions": waiting_q, "gates": gates, "as_of": today},
        "released": {"items": _released(spec)},
        "history": _history(root, change),
        "as_of": today,
    }
    return model


# --------------------------------------------------------------------------- render
TEMPLATE_FILE = SCHEMAS_DIR.parent / "templates" / "sponsor.html"


def _e(v):
    import html as _html
    return _html.escape("" if v is None else str(v), quote=True)


def _money(v):
    return "US$ %.2f" % v


def _minutes(m, lang):
    m = int(round(m or 0))
    h, mm = divmod(m, 60)
    return ("%d h %02d min" % (h, mm)) if h else ("%d min" % mm)


def render(model, template=None):
    """The page HTML: every value escaped, sections in the design-spec order (waiting first)."""
    tpl = template if template is not None else TEMPLATE_FILE.read_text(encoding="utf-8")
    W = wording()
    lang = model.get("language") or "en"

    def L(key):
        return word(W, "labels", key, lang)

    prog, cost, risks, waiting = model["progress"], model["cost"], model["risks"], model["waiting"]
    released = model["released"]["items"]
    n_wait = len(waiting["questions"]) + len(waiting["gates"])
    sponsor = model.get("sponsor") or {}
    if released:
        status = '<span class="status done"><span class="dot" aria-hidden="true"></span>%s</span>' % _e(
            word(W, "phases", "deployed", lang))
    elif prog.get("changes_requested"):
        status = '<span class="status"><span class="dot" aria-hidden="true"></span>%s</span>' % _e(
            L("changes_requested"))
    else:
        status = '<span class="status"><span class="dot" aria-hidden="true"></span>%s</span>' % _e(prog["phase"])
    sections = [("waiting", L("waiting")), ("scope", L("scope")), ("progress", L("progress")), ("cost", L("cost")),
                ("risks", L("risks")), ("released", L("released")), ("history", L("history"))]
    toc = "".join('<a href="#%s">%s</a>' % (k, _e(t)) for k, t in sections)
    cost_fact = _money(cost["usd"]) if cost.get("measured") else L("not_measured")
    facts = "".join("<li><span>%s</span><b>%s</b></li>" % (_e(a), _e(b)) for a, b in (
        (L("step"), prog["phase"]), (L("cost_to_date"), cost_fact),
        (L("open_risks"), risks["open"] or L("none")), (L("waiting"), n_wait or L("none"))))
    # waiting
    if n_wait:
        items = []
        for g in waiting["gates"]:
            items.append('<div class="ask"><span class="tag">%s</span><div><strong>%s</strong></div></div>' % (
                _e(L("your_approval")), _e(g["step"])))
        for q in waiting["questions"]:
            when = ""
            if q["needed_by"]:
                cls, lab = ("err", L("overdue_since")) if q["overdue"] else ("warn", L("needed_by"))
                when = '<span class="tag %s">%s %s</span>' % (cls, _e(lab), _e(q["needed_by"]))
            ctx = ('<details><summary>%s</summary><p class="small">%s</p></details>' % (
                _e(L("options")), _e(q["context"]))) if q["context"] else ""
            items.append('<div class="ask">%s<div><strong>%s</strong>%s</div></div>' % (when, _e(q["question"]), ctx))
        waiting_html = ('<section id="waiting" class="card emph"><h2>%s</h2><p class="muted small">%s</p>%s'
                        '<p class="stamp">%s %s</p></section>' % (_e(L("waiting")), _e(L("waiting_intro")),
                                                                  "".join(items), _e(L("as_of")),
                                                                  _e(waiting["as_of"])))
    else:
        waiting_html = '<section id="waiting" class="card"><h2>%s</h2><p>%s</p></section>' % (
            _e(L("waiting")), _e(L("nothing_waiting")))
    # scope
    sc = model["scope"]
    lists = ""
    if sc["included"] or sc["excluded"]:
        lists = '<div class="grid2"><div><h3>%s</h3><ul class="small">%s</ul></div><div><h3>%s</h3><ul class="small">' \
                '%s</ul></div></div>' % (_e(L("included")), "".join("<li>%s</li>" % _e(x) for x in sc["included"]),
                                        _e(L("not_included")), "".join("<li>%s</li>" % _e(x) for x in sc["excluded"]))
    areas = ('<ul class="small">%s</ul>' % "".join("<li>%s</li>" % _e(a) for a in sc["areas"])) if sc["areas"] else ""
    scope_html = '<section id="scope"><h2>%s</h2><p>%s</p>%s%s<p class="stamp">%s %s</p></section>' % (
        _e(L("scope")), _e(sc["summary"]), lists, areas, _e(L("as_of")), _e(sc["as_of"]))
    # progress
    steps = "".join('<li class="%s">%s<small>%s</small></li>' % (
        s["state"] if s["state"] in ("done", "now") else "", _e(s["step"]),
        _e(("%s %s" % (L("since") if s["state"] == "now" else "", s["date"])).strip() if s["date"] else L("planned")))
        for s in prog["steps"])
    progress_html = ('<section id="progress"><h2>%s</h2><ol class="steps">%s</ol><p class="small">%s: <strong>%s'
                     '</strong></p><p class="stamp">%s %s</p></section>' % (
                         _e(L("progress")), steps, _e(L("work_size")), _e(prog["lane"]), _e(L("as_of")),
                         _e(prog["as_of"])))
    # cost
    if cost.get("measured"):
        rows = "".join('<tr><td>%s</td><td class="num">%.2f</td><td class="num">%s</td><td><span class="tag %s">%s'
                       '</span></td></tr>' % (_e(r["step"]), r["usd"], _e(_minutes(r["review_min"], lang)),
                                              "ok" if r["quality"] == "exact" else "warn", _e(r["quality"]))
                       for r in cost["by_phase"])
        cost_html = ('<section id="cost"><h2>%s</h2><p><strong>%s</strong> %s · <strong>%s</strong> %s · %s %s '
                     '<span class="tag">%d%% %s</span></p><p class="small muted">%s: %s</p><details><summary>%s'
                     '</summary><div class="table-scroll"><table><thead><tr><th>%s</th><th class="num">US$</th>'
                     '<th class="num">%s</th><th>%s</th></tr></thead><tbody>%s</tbody></table></div><p class="xs '
                     'muted">%s</p></details></section>' % (
                         _e(L("cost")), _e(_money(cost["usd"])), _e(L("ai_work")),
                         _e(_minutes(cost["review_min"], lang)), _e(L("review_time")), _e(L("as_of")),
                         _e(cost["as_of"]), int(round(cost["estimated_share"] * 100)), _e(L("estimated_share")),
                         _e(L("judges_apart")), _e(_money(cost["judge_usd"])), _e(L("by_step")), _e(L("step")),
                         _e(L("review_time_col")), _e(L("how_measured")), rows, _e(L("cost_note"))))
    else:
        cost_html = '<section id="cost"><h2>%s</h2><p><strong>%s</strong></p></section>' % (
            _e(L("cost")), _e(cost["text"]))
    # risks
    if risks["items"]:
        rows = "".join('<tr><td>%s%s</td><td>%s / %s</td><td>%s</td><td><span class="tag %s">%s</span><br><span '
                       'class="xs muted">%s %s</span></td></tr>' % (
                           _e(r["description"]),
                           ('<details><summary class="small">%s</summary><p class="small">%s</p></details>' % (
                               _e(L("set_off_by")), _e(r["trigger"]))) if r["trigger"] else "",
                           _e(r["likelihood"]), _e(r["impact"]), _e(r["owner"]),
                           "warn" if r["state_id"] == "open" else "ok", _e(r["state"]), _e(L("last_review")),
                           _e(r["last_review"] or "—")) for r in risks["items"])
        risks_html = ('<section id="risks"><h2>%s</h2><div class="table-scroll"><table><thead><tr><th>%s</th><th>'
                      '%s</th><th>%s</th><th>%s</th></tr></thead><tbody>%s</tbody></table></div></section>' % (
                          _e(L("risks")), _e(L("risk")), _e(L("likelihood_impact")), _e(L("who_watches")),
                          _e(L("state")), rows))
    else:
        risks_html = '<section id="risks"><h2>%s</h2><p>%s</p></section>' % (_e(L("risks")), _e(L("no_open_risks")))
    # released
    if released:
        rel = "".join("<li>%s %s %s</li>" % (_e(r["version"]), _e(L("reached_production")), _e(r["date"]))
                      for r in released)
        released_html = '<section id="released"><h2>%s</h2><ul>%s</ul></section>' % (_e(L("released")), rel)
    else:
        released_html = '<section id="released"><h2>%s</h2><p class="muted">%s</p></section>' % (
            _e(L("released")), _e(L("nothing_released")))
    hist = "".join("<li>%s — %s: %s</li>" % (_e(h["date"]), _e(h["gate"]), _e(L(h["outcome"])))
                   for h in model.get("history") or [])
    history_html = '<section id="history"><h2>%s</h2><p class="small muted">%s</p>%s</section>' % (
        _e(L("history")), _e(L("history_intro")), ('<ul class="small">%s</ul>' % hist) if hist else "")
    note = ('<p class="xs muted">%s</p>' % _e(model["language_note"])) if model.get("language_note") else ""
    slots = {
        "lang": lang, "title": model["title"], "label_page_title": L("page_title"),
        "change_line": "%s · %s: %s" % (model["change"], L("prepared_for"), sponsor.get("name") or sponsor.get("role")
                                        or "—"),
        "updated_line": "%s %s" % (L("updated"), model["as_of"]), "label_sections": L("progress"),
        "label_summary": L("step"), "label_footer": L("footer"),
    }
    raw = {"language_note": note, "status": status, "toc": toc, "facts": facts, "section_waiting": waiting_html,
           "section_scope": scope_html, "section_progress": progress_html, "section_cost": cost_html,
           "section_risks": risks_html, "section_released": released_html, "section_history": history_html}
    out = tpl
    for k, v in raw.items():
        out = out.replace("{{{%s}}}" % k, v)
    for k, v in slots.items():
        out = out.replace("{{%s}}" % k, _e(v))
    left = re.findall(r"\{\{\{?[a-z_]+\}?\}\}", out)
    if left:
        raise ValueError("template slots not filled: %s" % ", ".join(sorted(set(left))))
    return out
