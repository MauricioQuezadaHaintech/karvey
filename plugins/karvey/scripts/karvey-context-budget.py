#!/usr/bin/env python3
"""karvey-context-budget.py — per-phase instruction size (architecture §1.3, C-01; REQ-W3-001, 010, 011, 071, 072).

    karvey-context-budget.py measure [--label L] [--date YYYY-MM-DD] [--plugin DIR] [--json]
    karvey-context-budget.py compare BASE.json [AFTER.json | --live] [--target-median 40] [--warn-growth 10]
                                     [--reasons FILE] [--plugin DIR] [--json]

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
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "measure":
        return cmd_measure(args)
    if args.cmd == "compare":
        return cmd_compare(args)
    build_parser().print_usage(sys.stderr)
    return kl.EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
