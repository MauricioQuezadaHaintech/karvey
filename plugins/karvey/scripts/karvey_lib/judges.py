"""Judges (architecture §1.7, wave2-structural): the closed input list, the output filter, the cost.

A judge is a clean-context subagent; this module never starts one. It decides what a judge may read
(``build_inputs``), and it filters what a judge returned (``collect``): schema check, citation resolver,
sanitiser, cost. Kept findings are appended to ``findings.md``; the run records go to ``spec.json`` only
through ``karvey-state.py judge-run``. Standard library only.
"""
import glob
import json
import os
import re
from pathlib import Path

from . import SCHEMAS_DIR, defaults
from . import lanes as ln
from . import project as pj

PHASES_WITH_RUBRIC = ("requirements", "architecture", "qa")
TEXT_MAX = 300
NONE_FOR_LANE = "judges: none for lane %s"
DISABLED = "judges: disabled by project setting"
NOT_JUDGED = "judges: not run (phase %s is not in judges.phases)"
_LENS_HEAD = re.compile(r"^## Lens: ([a-z0-9-]+)\s*$", re.M)


class JudgeError(Exception):
    """Unknown phase, unknown change or an invalid setting."""


def _machine():
    with open(SCHEMAS_DIR / "state-machine.json", encoding="utf-8-sig") as fh:
        return {p["id"]: p for p in json.load(fh)["phases"]}


def settings(project):
    """``project.json:judges`` over ``defaults.json:judges``."""
    d = defaults().get("judges") or {}
    p = (project or {}).get("judges") if isinstance(project, dict) else None
    p = p if isinstance(p, dict) else {}
    out = {k: d.get(k) for k in ("enabled", "mode", "phases", "lenses", "always", "cross_model")}
    for k in ("enabled", "mode", "phases", "cross_model"):
        if k in p:
            out[k] = p[k]
    lenses = dict(out.get("lenses") or {})
    if isinstance(p.get("lenses"), dict):
        lenses.update({k: v for k, v in p["lenses"].items() if isinstance(v, list)})
    out["lenses"] = lenses
    out["per_lane"] = p.get("per_lane") if isinstance(p.get("per_lane"), dict) else {}
    out["budget_ignored"] = "budget" in p
    return out


def rubric_path(plugin_rules, phase):
    return Path(plugin_rules) / "judges" / ("%s.md" % phase)


def rubric_lenses(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return []
    return _LENS_HEAD.findall(text)


def lens_section(path, lens):
    """The text of ``## Lens: {lens}`` in a rubric, or None."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return None
    m = re.search(r"^## Lens: %s\s*$(.*?)(?=^## |\Z)" % re.escape(lens), text, re.M | re.S)
    return m.group(1).strip() if m else None


def pick_lenses(phase, count, st):
    """The first ``count`` lenses of the phase, with the ``always`` ones (the qa fiscal) first."""
    if count <= 0:
        return []
    always = list((st.get("always") or {}).get(phase) or [])
    rest = [x for x in (st.get("lenses") or {}).get(phase, []) if x not in always]
    return (always + rest)[:max(count, len(always))]


def _expand(cdir, item):
    """Change-relative paths of one ``produces`` / ``reads`` item (``?`` optional, globs, dirs)."""
    optional = item.endswith("?")
    item = item.rstrip("?")
    if any(c in item for c in "*?["):
        return sorted(os.path.relpath(p, cdir) for p in glob.glob(str(cdir / item)))
    p = cdir / item
    if p.exists():
        return [item.rstrip("/")]
    return [] if optional else [item.rstrip("/") + " (missing)"]


def build_inputs(root, change, phase, extras=(), project=None, diff_path=None, plugin_rules=None):
    """The closed input list of a judge run (REQ-W2-022, 023, 031). Pure of side effects."""
    machine = _machine()
    if phase not in machine:
        raise JudgeError("unknown phase %r" % phase)
    cdir = Path(root) / pj.CHANGES_DIR / change
    spec_p = cdir / "spec.json"
    if not spec_p.is_file():
        raise JudgeError("change %r not found (no %s)" % (change, spec_p))
    spec = json.loads(spec_p.read_text(encoding="utf-8-sig"))
    if project is None:
        project, _ = pj.load_project_json(root)
    st = settings(project)
    lane, _src = ln.lane_of(spec)
    res = {"change": change, "phase": phase, "lane": lane, "mode": st["mode"], "cross_model": st["cross_model"],
           "lenses": [], "inputs": [], "goal": spec.get("goal"), "rubric": None, "dropped": [], "status": None,
           "notes": []}
    if st["budget_ignored"]:
        res["notes"].append("judges.budget: ignored (measure only, D-30)")
    if st["enabled"] is False:
        res["status"] = DISABLED
        return res
    if phase not in (st["phases"] or []):
        res["status"] = NOT_JUDGED % phase
        return res
    count = ln.judges_for(lane, {"judges": {"per_lane": st["per_lane"]}})
    if count == 0:
        res["status"] = NONE_FOR_LANE % lane
        return res
    rules = Path(plugin_rules) if plugin_rules else SCHEMAS_DIR.parent / "skills" / "karvey" / "rules"
    rp = rubric_path(rules, phase)
    have = rubric_lenses(rp)
    if not rp.is_file():
        res["notes"].append("no rubric rules/judges/%s.md: no lens can run" % phase)
    lenses = pick_lenses(phase, count, st)
    for lens in lenses:
        if lens not in have:
            res["notes"].append("unknown lens %s (no section in rules/judges/%s.md)" % (lens, phase))
    res["lenses"] = [x for x in lenses if x in have]
    res["rubric"] = str(rp) if rp.is_file() else None  # the plugin's own file (read by path)
    pdef = machine[phase]
    items = list(pdef.get("produces") or []) + list(pdef.get("reads") or [])
    paths = []
    for it in items:
        for p in _expand(cdir, it):
            q = "%s/%s/%s" % (pj.CHANGES_DIR.as_posix(), change, p)
            if q not in paths:
                paths.append(q)
    if phase == "qa" and diff_path:
        paths.append(str(diff_path))
    res["inputs"] = paths
    allowed = set(paths) | {res["rubric"]}
    for x in extras or ():
        if x not in allowed:
            res["dropped"].append("dropped: %s (not a phase input)" % x)
    res["status"] = "%d judge(s): %s" % (len(res["lenses"]), ", ".join(res["lenses"]) or "none")
    return res


# --------------------------------------------------------------------------- collect (REQ-W2-025, 026, 029, 030)
VERDICTS = ("pass", "concerns", "fail")
SEVERITIES = ("Critical", "High", "Medium", "Low")
TYPES = ("bug", "spec-gap", "emergent")
# a judge only proposes risks; any output field that targets the register is dropped and reported (REQ-W3-032)
REGISTER_KEYS = ("risks", "register_edit")
PROPOSED_RISK = "proposed risk"
FINDINGS_HEAD = "| ID | Date | Phase | Origin | Type | Severity | Finding | Status | Routed to |"
_FENCE = re.compile(r"```.*?(```|\Z)", re.S)
_PATCH_LINE = re.compile(r"^(diff --git|@@|\+\+\+|---|[+-])", re.M)
_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_FID = re.compile(r"^\|\s*F-(\d+)\s*\|", re.M)


def sanitise(text):
    """Finding text for a Markdown table cell: no code block or patch, escaped, at most 300 characters."""
    t = _FENCE.sub(" ", str(text or ""))
    if re.search(r"^(@@|diff --git|\+\+\+ )", t, re.M):  # a patch: drop its lines, keep the prose
        t = "\n".join(ln for ln in t.splitlines() if not _PATCH_LINE.match(ln))
    t = t.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    t = _CTRL.sub("", t).replace("|", "\\|")
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= TEXT_MAX else t[:TEXT_MAX - 1] + "…"


def _lines_of(root, path):
    p = Path(path) if os.path.isabs(path) else Path(root) / path
    try:
        return len(p.read_text(encoding="utf-8-sig", errors="replace").splitlines())
    except OSError:
        return None


def resolve_cite(root, cite, allowed):
    """True when ``path:line`` names one of the inputs and a line within its length."""
    if not isinstance(cite, str) or ":" not in cite:
        return False
    path, _, line = cite.rpartition(":")
    path = path.strip()
    if not line.strip().isdigit():
        return False
    if path not in allowed:
        return False
    n = _lines_of(root, path)
    return n is not None and 1 <= int(line) <= n


def _valid_result(r):
    if not isinstance(r, dict) or r.get("verdict") not in VERDICTS or not isinstance(r.get("lens"), str):
        return False
    fs = r.get("findings", [])
    if not isinstance(fs, list):
        return False
    return all(isinstance(f, dict) and f.get("severity") in SEVERITIES and isinstance(f.get("text"), str)
               for f in fs)


def price(model):
    table = defaults().get("judge_price_table") or {}
    p = table.get(model) or table.get("default") or {"in": 0.0, "out": 0.0}
    return float(p.get("in", 0.0)), float(p.get("out", 0.0))


def cost(usage, chars_in, chars_out, model, runtime_total=None):
    """The cost of one judge run (wave3 §1.10, REQ-W3-077, MODIFIES REQ-W2-030) as a dict:
    ``{tokens_in, tokens_out, tokens_total, usd, estimated, usd_estimated, source}``.

    - ``runtime_total`` (the subagent's token total read from the session transcript) → ``source: runtime``,
      tokens exact; the US$ uses the input price and is ``usd_estimated`` (the in/out split is unknown);
    - else a ``usage`` the model wrote into its reply (``tokens_in``/``tokens_out`` or ``total_tokens``) →
      ``source: agent-reported``, kept but ``estimated`` (F-45, F-78: a number the model copies is not a measure);
    - else characters ÷ 4 over the prompt and every closed input → ``source: estimate``, ``estimated``."""
    pin, pout = price(model)
    if isinstance(runtime_total, int) and not isinstance(runtime_total, bool) and runtime_total >= 0:
        return {"tokens_total": runtime_total, "usd": round(runtime_total * pin / 1e6, 6), "estimated": False,
                "usd_estimated": True, "source": "runtime"}
    if isinstance(usage, dict):
        ti, to, tt = usage.get("tokens_in"), usage.get("tokens_out"), usage.get("total_tokens")
        if isinstance(ti, int) and isinstance(to, int):
            usd = usage.get("usd")
            if not isinstance(usd, (int, float)) or isinstance(usd, bool):
                usd = (ti * pin + to * pout) / 1e6
            return {"tokens_in": ti, "tokens_out": to, "tokens_total": ti + to, "usd": round(float(usd), 6),
                    "estimated": True, "usd_estimated": not isinstance(usage.get("usd"), (int, float)),
                    "source": "agent-reported"}
        if isinstance(tt, int) and not isinstance(tt, bool):
            return {"tokens_total": tt, "usd": round(tt * pin / 1e6, 6), "estimated": True, "usd_estimated": True,
                    "source": "agent-reported"}
    ti, to = chars_in // 4, chars_out // 4
    return {"tokens_in": ti, "tokens_out": to, "tokens_total": ti + to, "usd": round((ti * pin + to * pout) / 1e6, 6),
            "estimated": True, "usd_estimated": True, "source": "estimate"}


LENS_LINE_RE = re.compile(r"through one lens:\s*([A-Za-z0-9_-]+)")
SUBAGENT_TOOLS = ("Agent", "Task")


def _usage_total(u):
    if not isinstance(u, dict):
        return None
    if isinstance(u.get("total_tokens"), int):
        return u["total_tokens"]
    keys = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
    vals = [u.get(k) for k in keys if isinstance(u.get(k), int)]
    return sum(vals) if vals else None


def transcript_judge_usage(path):
    """``{lens: tokens_total}`` of the judge subagents a session transcript records (the runtime's own figure).

    A subagent call is an ``Agent``/``Task`` ``tool_use`` whose prompt carries the template's lens line; its
    result is the ``tool_result`` with the same id, whose ``toolUseResult.totalTokens`` (or ``usage``) the runtime
    wrote. The last run of a lens wins. An unreadable transcript → ``{}``."""
    calls, out = {}, {}
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except (OSError, TypeError):
        return out
    with fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            msg = o.get("message") if isinstance(o.get("message"), dict) else {}
            content = msg.get("content") if isinstance(msg.get("content"), list) else []
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use" and b.get("name") in SUBAGENT_TOOLS:
                    prompt = (b.get("input") or {}).get("prompt") or ""
                    m = LENS_LINE_RE.search(prompt if isinstance(prompt, str) else "")
                    if m and b.get("id"):
                        calls[b["id"]] = m.group(1)
                elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                    tur = o.get("toolUseResult") if isinstance(o.get("toolUseResult"), dict) else {}
                    total = tur.get("totalTokens") if isinstance(tur.get("totalTokens"), int) else None
                    if total is None:
                        total = _usage_total(tur.get("usage")) or _usage_total(b.get("usage"))
                    if isinstance(total, int):
                        out[calls[b["tool_use_id"]]] = total
    return out


def prompt_template_chars(rules_dir):
    """Characters of the judge prompt template (``rules/judges.md``), part of every judge's input."""
    try:
        text = (Path(rules_dir) / "judges.md").read_text(encoding="utf-8-sig")
    except OSError:
        return 0
    m = re.search(r"<!-- judge-template -->(.*?)<!-- /judge-template -->", text, re.S)
    return len(m.group(1)) if m else 0


def collect(root, change, phase, results, allowed, model=None, intra_model=None, at=None, chars_in=0,
            runtime_usage=None):
    """Filter the judge results (``[(name, raw_text)]``). Returns ``(runs, kept, lines)``; writes nothing.
    ``runtime_usage`` = ``{lens: tokens_total}`` read from the session transcript (``transcript_judge_usage``)."""
    runtime_usage = runtime_usage or {}
    runs, kept, lines = [], [], []
    for name, raw in results:
        try:
            r = json.loads(raw)
        except ValueError:
            r = None
        if not _valid_result(r):
            lens = r.get("lens") if isinstance(r, dict) and isinstance(r.get("lens"), str) else Path(name).stem
            rmodel = r.get("model") if isinstance(r, dict) and isinstance(r.get("model"), str) else None
            runs.append({"phase": phase, "lens": lens, "model": rmodel or model or "unknown",
                         "intra_model": bool(intra_model), "verdict": "not-run",
                         "findings": {}, "discarded": 0, "at": at, "reason": "invalid output"})
            lines.append("%s: not run (invalid output)" % lens)
            continue
        discarded, counts = 0, {}
        dropped = [k for k in REGISTER_KEYS if k in r]
        for f in r.get("findings", []):
            dropped += [k for k in REGISTER_KEYS if k in f]
            if not resolve_cite(root, f.get("cite"), allowed):
                discarded += 1
                continue
            sev = f["severity"]
            counts[sev] = counts.get(sev, 0) + 1
            if f.get("kind") == "risk":  # a risk, not a defect: proposed for iterate to accept (REQ-W3-032)
                kept.append({"lens": r["lens"], "severity": sev, "type": "emergent", "routed": PROPOSED_RISK,
                             "text": sanitise(f["text"]), "cite": f["cite"]})
                continue
            kept.append({"lens": r["lens"], "severity": sev, "type": f.get("type_guess") if f.get("type_guess") in TYPES
                         else "emergent", "text": sanitise(f["text"]), "cite": f["cite"]})
        for k in sorted(set(dropped)):
            lines.append("%s: dropped: register edit (%s) — judges propose risks, they never write the register"
                         % (r["lens"], k))
        m = r.get("model") or model or "unknown"
        im = r.get("intra_model") if isinstance(r.get("intra_model"), bool) else bool(intra_model)
        c = cost(r.get("usage"), chars_in, len(raw), m, runtime_usage.get(r["lens"]))
        run = {"phase": phase, "lens": r["lens"], "model": m, "intra_model": im, "verdict": r["verdict"],
               "findings": counts, "discarded": discarded, "at": at}
        run.update(c)
        runs.append(run)
        agent = cost(r.get("usage"), 0, 0, m) if c["source"] == "runtime" else None
        side = (" (agent-reported %d)" % agent["tokens_total"]) if agent and agent["source"] == "agent-reported" else ""
        lines.append("%s: %s · %d kept · %d discarded (no citation) · %s%s · %d tokens %s%s" % (
            r["lens"], r["verdict"], sum(counts.values()), discarded, m, " (intra-model)" if im else "",
            c["tokens_total"], c["source"], side))
    return runs, kept, lines


def append_findings(path, phase, kept, day):
    """Append the kept judge findings as ``open`` rows (origin ``judge:{lens}``); returns the new ids."""
    from . import atomicio
    path = Path(path)
    exists = path.is_file()
    text = path.read_text(encoding="utf-8-sig") if exists else "# Findings\n\n%s\n%s\n" % (
        FINDINGS_HEAD, "|" + "----|" * 9)
    expected = atomicio.file_sha256(path) if exists else None  # compare-and-swap under the writer's lock
    nums = [int(n) for n in _FID.findall(text)]
    nxt = max(nums) + 1 if nums else 1
    rows, ids = [], []
    for k in kept:
        fid = "F-%02d" % nxt
        nxt += 1
        ids.append(fid)
        rows.append("| %s | %s | %s | judge:%s | %s | %s | %s (%s) | open | %s |" % (
            fid, day, phase, k["lens"], k["type"], k["severity"], k["text"], k["cite"].replace("|", "\\|"),
            k.get("routed") or "—"))
    if rows:
        lines = text.rstrip("\n").split("\n")
        last = max((i for i, ln in enumerate(lines) if ln.startswith("|")), default=len(lines) - 1)
        lines[last + 1:last + 1] = rows
        atomicio.write_text_atomic(str(path), "\n".join(lines) + "\n", expected_sha256=expected)
    return ids


def read_rows(path):
    """The rows of the findings table (by header name, lower-case keys), or []."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return []
    return read_rows_text(text)


def read_rows_text(text):
    head, rows = None, []
    for ln in text.splitlines():
        if not ln.startswith("|"):
            head = None if rows or head is None else head
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", ln.strip())[1:-1]]
        if head is None:
            head = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(dict(zip(head, cells)))
    return rows


def open_blocking(path, phase):
    """Ids of ``open`` Critical/High judge findings of ``phase`` (REQ-W2-028)."""
    out = []
    for r in read_rows(path):
        if (r.get("origin") or "").startswith("judge:") and r.get("phase") == phase \
                and r.get("severity") in ("Critical", "High") and (r.get("status") or "").split(" ")[0] == "open":
            out.append(r.get("id") or r.get("#") or "?")
    return out
