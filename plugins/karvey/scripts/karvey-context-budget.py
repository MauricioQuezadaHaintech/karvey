#!/usr/bin/env python3
"""karvey-context-budget.py — per-phase instruction size (architecture §1.3, C-01; REQ-W3-001, 010, 011, 071, 072).

    karvey-context-budget.py measure [--label L] [--date YYYY-MM-DD] [--plugin DIR] [--json]
    karvey-context-budget.py compare BASE.json [AFTER.json | --live] [--target-median 40] [--warn-growth 10]
                                     [--reasons FILE] [--plugin DIR] [--json]
    karvey-context-budget.py order --baseline docs/spec/retros/context-size-4.0.0.json --change ID [--root DIR]
    karvey-context-budget.py contracts [--plugin DIR] [--json]

``measure`` prints one row per phase skill of ``schemas/state-machine.json`` plus the orchestrator: the skill's own
size, the rules it cites directly and the transitive closure (``closure_min`` / ``closure_max``, see
``karvey_lib/loadlist.py``), each in bytes, words and estimated tokens; and a ``session_hook`` row — the bytes the
session hook prints on the committed fixture project ``tests/fixtures/budget-project/`` (its temp path replaced by
``{project}``). The top block holds the label, the date of the last commit that touched the measured text (never
the wall clock; ``--date`` overrides it) and ``plugin_files_sha`` (sha256 of the measured files, sorted). Keys and
rows are sorted and no absolute path is printed, so two runs on the same tree give the same bytes (REQ-W3-071). A
``Load:`` entry that names a missing file → exit 1 naming the skill, the line and the file (REQ-W3-072).

``compare`` reads a baseline snapshot and an after snapshot (or measures now with ``--live``): the per-phase
reduction of ``closure_max`` bytes, the median, and every phase below the target with its recorded reason
(``--reasons`` JSON ``{skill: text}``, default ``schemas/contracts.json:reasons``) or ``unexplained``. Without
``--warn-growth`` it exits 1 when the median misses ``--target-median`` (the test-phase gate of REQ-W3-010). With
``--warn-growth N`` it is the CI step (REQ-W3-011): one ``::warning::`` line per phase grown more than N%, exit 0.

``order`` checks REQ-W3-002 in git history: the commit that added the baseline precedes (is an ancestor of, and is
not) every commit carrying ``Karvey-Change: ID`` that renames or deletes a skill or rule file, or adds a
``skills/*/references/`` or ``rules/adapters/`` file; else ``baseline missing or taken after the reorganisation``.

``contracts`` (C-02, REQ-W3-009) reads ``schemas/contracts.json``: for every ``(phase, contract)`` pair of its
``baseline`` map the contract's ``anchor`` must still be reachable — an ``{#contract-<id>}`` heading anchor found in
``rules/_core.md`` or in a file of the phase's current closure, or (before the core exists) an anchor naming a rule
file that is in that closure. Otherwise ``{phase}: contract {id} not loaded``, exit 1. A contract whose anchor is
``null`` is reported ``pending`` and does not fail (the core anchors it).

Exit: 0 · 1 findings (missing load file, median below target) · 2 usage · 4 snapshot not found. Stdlib only.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import loadlist  # noqa: E402

TOOL = "karvey-context-budget"
ORCHESTRATOR = "karvey"
BUDGET_PROJECT = Path("tests") / "fixtures" / "budget-project"
SESSION_HOOK = Path("hooks") / "karvey-session-context.sh"
PROJECT_TOKEN = "{project}"


class NotFound(Exception):
    pass


# --------------------------------------------------------------------------- measure
def phase_skills(plugin_dir):
    """``{skill: [phase, …]}`` from the state machine, plus the orchestrator."""
    try:
        machine = json.loads((Path(plugin_dir) / "schemas" / "state-machine.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        machine = {"phases": []}
    out = {}
    for ph in machine.get("phases", []):
        sk = ph.get("skill")
        if isinstance(sk, str) and sk:
            out.setdefault(sk, []).append(ph.get("id"))
    out.setdefault(ORCHESTRATOR, [])
    return out


def measured_files(plugin_dir):
    """Every Markdown file under ``skills/`` (the text the tool measures), sorted."""
    base = Path(plugin_dir) / "skills"
    return sorted((p for p in base.rglob("*.md") if p.is_file()), key=lambda p: p.as_posix()) if base.is_dir() else []


def files_sha(plugin_dir):
    h = hashlib.sha256()
    for p in measured_files(plugin_dir):
        h.update(loadlist.rel(p, plugin_dir).encode("utf-8") + b"\0")
        try:
            h.update(p.read_bytes())
        except OSError:
            pass
        h.update(b"\0")
    return h.hexdigest()


def content_date(plugin_dir):
    """Committer date (YYYY-MM-DD) of the last commit that touched the measured text, or None outside git."""
    try:
        cp = subprocess.run(["git", "-C", str(plugin_dir), "log", "-1", "--format=%cs", "--", "skills"],
                            capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    out = cp.stdout.strip()
    return out if cp.returncode == 0 and out else None


def session_hook_row(plugin_dir):
    """Bytes of the session hook's context on the fixture project (``None`` when either is absent)."""
    plugin_dir = Path(plugin_dir)
    hook, fixture = plugin_dir / SESSION_HOOK, plugin_dir / BUDGET_PROJECT
    if not hook.is_file() or not fixture.is_dir():
        return {"bytes": None, "note": "no session hook or no fixture project"}
    tmp = tempfile.mkdtemp(prefix="karvey-budget-")
    try:
        proj = Path(tmp) / "project"
        shutil.copytree(str(fixture), str(proj))
        env = {k: v for k, v in os.environ.items() if not k.startswith(("KARVEY_", "CLAUDE_", "GIT_"))}
        env["CLAUDE_PROJECT_DIR"] = str(proj)
        try:
            cp = subprocess.run(["bash", str(hook), "startup"], cwd=str(proj), env=env, capture_output=True,
                                text=True, timeout=60)
            raw = cp.stdout
        except (OSError, subprocess.SubprocessError):
            raw = ""
        text = raw
        try:
            text = json.loads(raw)["hookSpecificOutput"]["additionalContext"]
        except (ValueError, KeyError, TypeError):
            pass
        real = os.path.realpath(str(proj))
        text = text.replace(real, PROJECT_TOKEN).replace(str(proj), PROJECT_TOKEN)
        data = text.encode("utf-8")
        return {"bytes": len(data), "lines": len(text.splitlines()),
                "sha256": hashlib.sha256(data).hexdigest()}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def measure(plugin_dir, label=None, date=None):
    """``(snapshot, issues)`` of the plugin at ``plugin_dir``."""
    plugin_dir = Path(plugin_dir)
    rules_dir = plugin_dir / "skills" / "karvey" / "rules"
    g = loadlist.graph(rules_dir)
    rows, issues = [], []
    for skill, phases in sorted(phase_skills(plugin_dir).items()):
        md = plugin_dir / "skills" / skill / "SKILL.md"
        if not md.is_file():
            issues.append({"skill": skill, "line": 0, "file": "skills/%s/SKILL.md" % skill,
                           "message": "phase skill %s has no SKILL.md" % skill})
            continue
        row, iss = loadlist.measure_skill(plugin_dir, md, g)
        row["phases"] = [p for p in phases if p]
        rows.append(row)
        issues.extend(iss)
    snap = {"method_version": label, "date": date or content_date(plugin_dir),
            "plugin_files_sha": files_sha(plugin_dir), "measure": "closure_max bytes",
            "rows": rows, "session_hook": session_hook_row(plugin_dir)}
    return snap, issues


def render_measure(snap):
    out = ["Context size — %s (%s)" % (snap.get("method_version") or "unlabelled", snap.get("date") or "no date"),
           "%-24s %6s %9s %9s %11s %11s %9s" % ("skill", "load", "own B", "direct B", "closure min", "closure max",
                                               "tok est")]
    for r in snap["rows"]:
        out.append("%-24s %6s %9d %9d %11d %11d %9d" % (
            r["skill"], "yes" if r["has_load_line"] else "no", r["own"]["bytes"], r["direct"]["bytes"],
            r["closure_min"]["bytes"], r["closure_max"]["bytes"], r["closure_max"]["tokens_est"]))
    sh = snap.get("session_hook") or {}
    out.append("session hook: %s bytes" % ("n/a" if sh.get("bytes") is None else sh["bytes"]))
    out.append("tokens are estimated (bytes / 4)")
    return "\n".join(out)


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_measure(args):
    plugin = Path(args.plugin) if args.plugin else kl.PLUGIN_ROOT
    snap, issues = measure(plugin, args.label, args.date)
    errors = [kl.issue("budget.load_missing", i["message"], file="skills/%s/SKILL.md" % i["skill"],
                       path="line %d" % i["line"], got=i["file"]) for i in issues]
    code = kl.EXIT_FINDINGS if errors else kl.EXIT_OK
    if args.json:
        sys.stdout.write(dump(kl.envelope(TOOL, code, snap, errors)))
    else:
        sys.stdout.write(render_measure(snap) + "\n")
        for e in errors:
            sys.stderr.write("[error] %s\n" % e["message"])
    return code


# --------------------------------------------------------------------------- compare
def load_snapshot(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except OSError:
        raise NotFound("snapshot %s not found" % path)
    except ValueError as exc:
        raise NotFound("snapshot %s is not JSON: %s" % (path, exc))
    if isinstance(data, dict) and "result" in data and "tool" in data:
        data = data["result"]
    if not isinstance(data, dict) or not isinstance(data.get("rows"), list):
        raise NotFound("snapshot %s has no rows" % path)
    return data


def load_reasons(path, plugin_dir):
    p = Path(path) if path else Path(plugin_dir) / "schemas" / "contracts.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    if isinstance(data, dict) and isinstance(data.get("reasons"), dict):
        data = data["reasons"]
    return {k: v for k, v in data.items() if isinstance(v, str)} if isinstance(data, dict) else {}


def median(values):
    v = sorted(values)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def compare(base, after, target=40.0, reasons=None):
    """Per-phase reduction of ``closure_max`` bytes (percent, positive = smaller) and the median."""
    reasons = reasons or {}
    b = {r["skill"]: r for r in base["rows"]}
    a = {r["skill"]: r for r in after["rows"]}
    phases = []
    for skill in sorted(set(b) & set(a)):
        bb, ab = b[skill]["closure_max"]["bytes"], a[skill]["closure_max"]["bytes"]
        red = round((bb - ab) * 100.0 / bb, 1) if bb else 0.0
        row = {"skill": skill, "before": bb, "after": ab, "reduction_pct": red}
        if red < target:
            row["reason"] = reasons.get(skill) or "unexplained"
        phases.append(row)
    med = median([p["reduction_pct"] for p in phases])
    med = None if med is None else round(med, 1)
    sb = (base.get("session_hook") or {}).get("bytes")
    sa = (after.get("session_hook") or {}).get("bytes")
    return {"target_median_pct": target, "median_reduction_pct": med, "phases": phases,
            "below_target": [p for p in phases if "reason" in p],
            "only_in_base": sorted(set(b) - set(a)), "only_in_after": sorted(set(a) - set(b)),
            "session_hook": {"before": sb, "after": sa}}


def growth_warnings(res, warn_pct):
    out = []
    for p in res["phases"]:
        if p["before"] and -p["reduction_pct"] > warn_pct:
            out.append("::warning title=context size::%s closure grew %s%% (%d -> %d bytes, over %s%%)" % (
                p["skill"], _pct(-p["reduction_pct"]), p["before"], p["after"], _pct(warn_pct)))
    sh = res["session_hook"]
    if sh["before"] and sh["after"] is not None and (sh["after"] - sh["before"]) * 100.0 / sh["before"] > warn_pct:
        g = round((sh["after"] - sh["before"]) * 100.0 / sh["before"], 1)
        out.append("::warning title=context size::session hook grew %s%% (%d -> %d bytes, over %s%%)" % (
            _pct(g), sh["before"], sh["after"], _pct(warn_pct)))
    return out


def _pct(x):
    return ("%d" % x) if float(x).is_integer() else ("%.1f" % x)


def render_compare(res):
    out = ["%-24s %11s %11s %9s  %s" % ("skill", "before B", "after B", "change", "reason (below target)")]
    for p in res["phases"]:
        out.append("%-24s %11d %11d %8s%%  %s" % (p["skill"], p["before"], p["after"], _pct(-p["reduction_pct"]),
                                                   p.get("reason", "")))
    med = res["median_reduction_pct"]
    out.append("median reduction: %s (target %s%%)" % ("n/a" if med is None else _pct(med) + "%",
                                                      _pct(res["target_median_pct"])))
    return "\n".join(out)


def cmd_compare(args):
    plugin = Path(args.plugin) if args.plugin else kl.PLUGIN_ROOT
    try:
        base = load_snapshot(args.base)
        if args.live:
            after, issues = measure(plugin)
        elif args.after:
            after, issues = load_snapshot(args.after), []
        else:
            sys.stderr.write("compare: give AFTER.json or --live\n")
            return kl.EXIT_USAGE
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("budget.not_found", str(exc))]),
                       args.json)
    res = compare(base, after, args.target_median, load_reasons(args.reasons, plugin))
    errors = [kl.issue("budget.load_missing", i["message"], got=i["file"]) for i in issues]
    lines = []
    if args.warn_growth is not None:
        lines = growth_warnings(res, args.warn_growth)
        res["warnings"] = lines
    elif res["median_reduction_pct"] is None or res["median_reduction_pct"] < args.target_median:
        errors.append(kl.issue("budget.median", "median reduction %s is below the %s%% target" % (
            "n/a" if res["median_reduction_pct"] is None else _pct(res["median_reduction_pct"]) + "%",
            _pct(args.target_median)), expected=args.target_median, got=res["median_reduction_pct"]))
    code = kl.EXIT_FINDINGS if errors else kl.EXIT_OK
    if args.json:
        sys.stdout.write(dump(kl.envelope(TOOL, code, res, errors)))
    else:
        sys.stdout.write(render_compare(res) + "\n")
        for ln in lines:
            sys.stdout.write(ln + "\n")
        for e in errors:
            sys.stderr.write("[error] %s\n" % e["message"])
    return code


# --------------------------------------------------------------------------- order (REQ-W3-002)
MOVE_PATHSPECS = (":(glob)plugins/karvey/skills/*/references/**", ":(glob)plugins/karvey/skills/karvey/rules/adapters/**")
ORDER_MESSAGE = "baseline missing or taken after the reorganisation"


def _git(root, *args):
    try:
        cp = subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return cp.returncode, cp.stdout.strip()


def reorg_commits(root, change):
    """Commits of ``change`` (by trailer) that move skill or rule text, oldest first."""
    grep = ["--grep", "Karvey-Change: %s" % change, "--format=%H", "--reverse"]
    shas = []
    for extra in (["--diff-filter=RD", "--", "plugins/karvey/skills"], ["--diff-filter=A", "--"] + list(MOVE_PATHSPECS)):
        rc, out = _git(root, "log", *(grep + extra))
        if rc == 0:
            shas.extend(x for x in out.splitlines() if x and x not in shas)
    return shas


def baseline_order(root, baseline, change):
    """``{baseline_commit, reorg_commits, ok, message}`` for REQ-W3-002."""
    rc, out = _git(root, "log", "--diff-filter=A", "--format=%H", "--", baseline)
    base = out.splitlines()[-1] if rc == 0 and out else None
    moves = reorg_commits(root, change)
    late = []
    for sha in moves:
        if base is None or sha == base or _git(root, "merge-base", "--is-ancestor", base, sha)[0] != 0:
            late.append(sha)
    ok = not late and (base is not None or not moves)
    return {"baseline": baseline, "baseline_commit": base, "reorg_commits": moves, "late": late, "ok": ok,
            "message": None if ok else "%s (%s)" % (ORDER_MESSAGE, ", ".join(s[:10] for s in late) or "no baseline")}


def cmd_order(args):
    root = Path(args.root) if args.root else Path.cwd()
    res = baseline_order(root, args.baseline, args.change)
    errors = [] if res["ok"] else [kl.issue("budget.order", res["message"], file=args.baseline)]
    code = kl.EXIT_OK if res["ok"] else kl.EXIT_FINDINGS
    human = "baseline %s at %s precedes %d reorganisation commit(s)" % (
        args.baseline, (res["baseline_commit"] or "none")[:10], len(res["reorg_commits"])) if res["ok"] else None
    return kl.emit(kl.envelope(TOOL, code, res, errors), args.json, human)


# --------------------------------------------------------------------------- contracts (C-02, REQ-W3-009)
CONTRACTS = Path("schemas") / "contracts.json"
CORE = Path("skills") / "karvey" / "rules" / "_core.md"


def phase_label(skill):
    """``karvey-deploy`` → ``deploy``; the orchestrator stays ``karvey``."""
    return skill[len("karvey-"):] if skill.startswith("karvey-") else skill


def load_contracts(plugin_dir):
    p = Path(plugin_dir) / CONTRACTS
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except OSError:
        raise NotFound("%s not found" % CONTRACTS.as_posix())
    except ValueError as exc:
        raise NotFound("%s is not JSON: %s" % (CONTRACTS.as_posix(), exc))
    if not isinstance(data, dict) or not isinstance(data.get("contracts"), list) or \
            not isinstance(data.get("baseline"), dict):
        raise NotFound("%s needs contracts[] and baseline{}" % CONTRACTS.as_posix())
    return data


def closures(plugin_dir):
    """``{phase label: [closure_max file, …]}`` of every phase skill (plugin-relative paths)."""
    plugin_dir = Path(plugin_dir)
    g = loadlist.graph(plugin_dir / "skills" / "karvey" / "rules")
    out = {}
    for skill in sorted(phase_skills(plugin_dir)):
        md = plugin_dir / "skills" / skill / "SKILL.md"
        if md.is_file():
            row, _ = loadlist.measure_skill(plugin_dir, md, g)
            out[phase_label(skill)] = row["closure_max_files"]
    return out


def _anchored(anchor, files, plugin_dir, core_text):
    if anchor.startswith("#"):
        mark = "{%s}" % anchor
        if mark in core_text:
            return True
        return any(mark in loadlist.read_text(Path(plugin_dir) / f) for f in files)
    return any(f == anchor or f.endswith("/rules/" + anchor) for f in files)


def contract_coverage(plugin_dir, data=None):
    """``{pairs, covered, missing[], pending[]}`` for every baseline ``(phase, contract)`` pair."""
    plugin_dir = Path(plugin_dir)
    data = data or load_contracts(plugin_dir)
    anchors = {c.get("id"): c.get("anchor") for c in data["contracts"] if isinstance(c, dict)}
    core_text = loadlist.read_text(plugin_dir / CORE)
    now = closures(plugin_dir)
    missing, pending, covered, pairs = [], [], 0, 0
    for phase in sorted(data["baseline"]):
        for cid in data["baseline"][phase]:
            pairs += 1
            if cid not in anchors:
                missing.append({"phase": phase, "contract": cid,
                                "message": "%s: contract %s is not declared in contracts[]" % (phase, cid)})
            elif anchors[cid] is None:
                pending.append({"phase": phase, "contract": cid})
            elif phase in now and _anchored(anchors[cid], now[phase], plugin_dir, core_text):
                covered += 1
            else:
                missing.append({"phase": phase, "contract": cid,
                                "message": "%s: contract %s not loaded" % (phase, cid)})
    return {"pairs": pairs, "covered": covered, "missing": missing, "pending": pending}


def cmd_contracts(args):
    plugin = Path(args.plugin) if args.plugin else kl.PLUGIN_ROOT
    try:
        res = contract_coverage(plugin)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("budget.not_found", str(exc))]),
                       args.json)
    errors = [kl.issue("budget.contract", m["message"], got=m["contract"]) for m in res["missing"]]
    code = kl.EXIT_FINDINGS if errors else kl.EXIT_OK
    human = "contracts: %d of %d (phase, contract) pairs covered%s" % (
        res["covered"], res["pairs"], ", %d pending" % len(res["pending"]) if res["pending"] else "")
    return kl.emit(kl.envelope(TOOL, code, res, errors), args.json, human)


# --------------------------------------------------------------------------- cli
class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        sys.exit(kl.EXIT_USAGE)


def build_parser():
    p = _Parser(prog="karvey-context-budget.py", description="Per-phase instruction size (C-01).")
    sub = p.add_subparsers(dest="cmd", parser_class=_Parser)
    m = sub.add_parser("measure", help="size rows per phase skill")
    m.add_argument("--label", help="method version recorded in the snapshot")
    m.add_argument("--date", help="date recorded in the snapshot (default: last commit touching skills/)")
    m.add_argument("--plugin", help="plugin directory (default: this plugin)")
    m.add_argument("--json", action="store_true")
    c = sub.add_parser("compare", help="reduction against a baseline snapshot")
    c.add_argument("base")
    c.add_argument("after", nargs="?")
    c.add_argument("--live", action="store_true", help="measure the plugin now instead of reading AFTER")
    c.add_argument("--target-median", type=float, default=40.0)
    c.add_argument("--warn-growth", type=float, default=None,
                   help="CI mode: warn per phase grown more than N%%, always exit 0")
    c.add_argument("--reasons", help="JSON {skill: reason} (default: schemas/contracts.json:reasons)")
    c.add_argument("--plugin", help="plugin directory (default: this plugin)")
    c.add_argument("--json", action="store_true")
    o = sub.add_parser("order", help="the baseline commit precedes every reorganisation commit (REQ-W3-002)")
    o.add_argument("--baseline", required=True, help="repo-relative path of the baseline snapshot")
    o.add_argument("--change", required=True)
    o.add_argument("--root", help="repository root (default: cwd)")
    o.add_argument("--json", action="store_true")
    k = sub.add_parser("contracts", help="every baseline (phase, contract) pair is still loaded (REQ-W3-009)")
    k.add_argument("--plugin", help="plugin directory (default: this plugin)")
    k.add_argument("--json", action="store_true")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "measure":
        return cmd_measure(args)
    if args.cmd == "compare":
        return cmd_compare(args)
    if args.cmd == "order":
        return cmd_order(args)
    if args.cmd == "contracts":
        return cmd_contracts(args)
    build_parser().print_usage(sys.stderr)
    return kl.EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
