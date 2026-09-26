#!/usr/bin/env python3
"""karvey-security-scan.py — the deterministic security tools of QA Dimension 1 (architecture §1.13 C-15).

    karvey-security-scan.py run <change> [--categories secrets,sast,sca,iac] [--root DIR] [--json]

``run``, per category of the fixed catalogue ``karvey_lib/security_tools.json``:

1. **applies?** — a tracked file matches the category's globs; else ``not applicable``.
2. **tool?** — the first catalogue tool on ``PATH`` (the project may narrow the list to catalogue ids with
   ``project.json:security.tools.{category}: [id]``, never supply a command); none → ``not evaluated (no tool)``.
3. **run** — the tool's fixed argv (placeholders ``{repo}`` and ``{out}`` only), no shell, with the timeout
   ``defaults.json:security_tool_timeout_s`` and a 5 MB output cap. Exit 0 or a documented "findings found"
   code → the report is parsed into findings by severity; any other exit, a timeout or an unreadable report →
   ``not evaluated (tool error)``, never ``pass``.
4. **record** — the report goes to ``changes/{id}/qa/security-{category}.json`` and one hashed line to
   ``changes/{id}/evidence.jsonl`` (the same record ``karvey-evidence.py`` writes); a category that applies
   and was not evaluated records a ``security.tools`` hit in ``checks.jsonl``.

Exit: 0 · 2 usage · 3 refused (unsafe project value) · 4 not found. Stdlib only.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import modes, project as pj, safe_values as sv  # noqa: E402

TOOL = "karvey-security-scan"
CATALOGUE = Path(os.path.dirname(os.path.abspath(__file__))) / "karvey_lib" / "security_tools.json"
OUTPUT_CAP = 5 * 1024 * 1024
PLACEHOLDERS = ("{repo}", "{out}")
SEVERITIES = ("critical", "high", "medium", "low", "info", "unknown")


class NotFound(Exception):
    pass


class Refused(Exception):
    pass


def catalogue():
    with open(CATALOGUE, encoding="utf-8-sig") as fh:
        return json.load(fh)


def category_ids(cat=None):
    return list((cat or catalogue())["categories"])


# --------------------------------------------------------------------------- project choice (REQ-W2-067)
def chosen_tools(project, cat):
    """``{category: [tool ids]}`` — the catalogue order, narrowed by ``project.json:security.tools``.

    Only catalogue ids are accepted: a command, a list of argv, a value with a shell metacharacter or an unknown
    id is refused (:class:`Refused`) before anything runs."""
    out = {c: [t["id"] for t in d["tools"]] for c, d in cat["categories"].items()}
    sec = (project or {}).get("security") if isinstance(project, dict) else None
    tools = sec.get("tools") if isinstance(sec, dict) else None
    if tools is None:
        return out
    if not isinstance(tools, dict):
        raise Refused("project.json:security.tools must map a category to a list of catalogue tool ids")
    for c, ids in tools.items():
        key = "security.tools.%s" % c
        try:
            sv.check_enum(c, tuple(out), "security.tools", kind="category")
            if not isinstance(ids, list) or not ids:
                raise sv.UnsafeValue(key, "tool ids", "must be a non-empty list of catalogue ids", ids)
            for i in ids:
                sv.check_common(i, key, "tool id")
                sv.check_enum(i, tuple(out[c]), key, kind="tool id")
        except sv.UnsafeValue as exc:
            raise Refused(str(exc))
        out[c] = [t for t in out[c] if t in ids]
    return out


# --------------------------------------------------------------------------- repository and files
def repo_top(root):
    """``git rev-parse --show-toplevel``, realpath-checked under the project root (else the root itself)."""
    root_real = os.path.realpath(str(root))
    try:
        p = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root_real, capture_output=True, text=True,
                           timeout=10)
        top = os.path.realpath(p.stdout.strip()) if p.returncode == 0 and p.stdout.strip() else root_real
    except (OSError, subprocess.SubprocessError):
        top = root_real
    if not (root_real == top or root_real.startswith(top + os.sep) or top.startswith(root_real + os.sep)):
        raise Refused("repository %s is not the project root %s" % (top, root_real))
    return top


def tracked_files(top):
    try:
        p = subprocess.run(["git", "ls-files"], cwd=top, capture_output=True, text=True, timeout=30)
        if p.returncode == 0:
            return [x for x in p.stdout.splitlines() if x]
    except (OSError, subprocess.SubprocessError):
        pass
    base = Path(top)
    return [str(x.relative_to(base)).replace(os.sep, "/") for x in base.rglob("*")
            if x.is_file() and ".git" not in x.parts]


def matches(files, globs):
    return [f for f in files if any(fnmatch.fnmatch(f, g) or fnmatch.fnmatch(f.rsplit("/", 1)[-1], g)
                                    for g in globs)]


# --------------------------------------------------------------------------- parsers (report → severities)
def _sev(value):
    v = str(value or "").strip().lower()
    return {"error": "high", "warning": "medium", "moderate": "medium", "note": "low", "information": "info",
            "negligible": "info"}.get(v, v if v in SEVERITIES else "unknown")


def _count(items):
    out = {s: 0 for s in SEVERITIES}
    for s in items:
        out[_sev(s)] += 1
    return {k: v for k, v in out.items() if v}


def parse(parser, text):
    """``{severity: count}`` from a tool report; raises ValueError when the report is not the tool's shape."""
    text = text.strip()
    if parser == "trufflehog":
        rows = [json.loads(x) for x in text.splitlines() if x.strip()]
        return _count("high" for _ in rows)
    data = json.loads(text) if text else ([] if parser == "gitleaks" else None)
    if parser == "gitleaks":
        if not isinstance(data, list):
            raise ValueError("gitleaks report is not a list")
        return _count("high" for _ in data)
    if parser == "semgrep":
        return _count(r.get("extra", {}).get("severity") for r in data["results"])
    if parser == "bandit":
        return _count(r.get("issue_severity") for r in data["results"])
    if parser == "osv":
        return _count("unknown" for r in data.get("results") or [] for pk in r.get("packages") or []
                      for _ in pk.get("vulnerabilities") or [])
    if parser == "npm_audit":
        v = data["metadata"]["vulnerabilities"]
        return {_sev(k): int(n) for k, n in v.items() if k != "total" and int(n)}
    if parser == "checkov":
        reports = data if isinstance(data, list) else [data]
        return _count(c.get("severity") for r in reports for c in (r.get("results") or {}).get("failed_checks") or [])
    if parser == "trivy":
        return _count(m.get("Severity") for r in data.get("Results") or [] for m in r.get("Misconfigurations") or [])
    raise ValueError("unknown parser %r" % parser)


# --------------------------------------------------------------------------- one tool run
def _version(tool):
    try:
        p = subprocess.run(tool["version_argv"], capture_output=True, text=True, timeout=30)
        line = (p.stdout or p.stderr).strip().splitlines()
        return line[0][:120] if line else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def build_argv(template, repo, out):
    """Fill the only two placeholders; any other brace in a template is a catalogue error."""
    argv = []
    for a in template:
        rest = a
        for ph in PLACEHOLDERS:
            rest = rest.replace(ph, "")
        if "{" in rest or "}" in rest:
            raise Refused("catalogue template %r has an unknown placeholder" % a)
        argv.append(a.replace("{repo}", repo).replace("{out}", out))
    return argv


def append_evidence(root, change, rec):
    path = Path(root) / pj.CHANGES_DIR / change / "evidence.jsonl"
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, (json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    with open(path, "rb") as fh:
        return sum(1 for _ in fh)


def run_tool(root, change, category, tool, repo, timeout):
    qa = Path(root) / pj.CHANGES_DIR / change / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    report = qa / ("security-%s.json" % category)
    if report.exists():
        report.unlink()
    argv = build_argv(tool["run_argv"], repo, str(report))
    res = {"category": category, "tool": tool["id"], "version": _version(tool), "argv": argv, "exit": None,
           "findings_by_severity": None, "findings": None,
           "report": os.path.relpath(str(report), str(root)).replace(os.sep, "/")}
    t0 = time.monotonic()
    try:
        p = subprocess.run(argv, capture_output=True, timeout=timeout, cwd=repo)
        out, err, code = p.stdout[:OUTPUT_CAP + 1], p.stderr[:OUTPUT_CAP + 1], p.returncode
    except subprocess.TimeoutExpired:
        out, err, code = b"", b"", None
    except OSError as exc:
        out, err, code = b"", str(exc).encode(), None
    ms = int((time.monotonic() - t0) * 1000)
    res["exit"] = code
    if tool["output"] == "stdout" and code is not None:
        report.write_bytes(out[:OUTPUT_CAP])
    ev = {"at": datetime.now().astimezone().isoformat(timespec="seconds"), "change": change,
          "label": "security:%s:%s" % (category, tool["id"]), "argv": argv, "cwd_rel": ".", "exit": code,
          "duration_ms": ms, "stdout_sha256": hashlib.sha256(out).hexdigest(),
          "stderr_sha256": hashlib.sha256(err).hexdigest(), "bytes": len(out) + len(err), "junit": None}
    try:
        res["evidence"] = "evidence.jsonl:%d" % append_evidence(root, change, ev)
    except OSError:
        res["evidence"] = None
    if code is None:
        res["status"] = "not evaluated (tool error)"
        res["reason"] = "timeout after %ds" % timeout if not err else err.decode("utf-8", "replace")[:200]
        return res
    if code != 0 and code not in tool.get("findings_exit", []):
        res["status"] = "not evaluated (tool error)"
        res["reason"] = "exit %d is not a findings code of %s" % (code, tool["id"])
        return res
    try:
        if report.stat().st_size > OUTPUT_CAP:
            raise ValueError("report over 5 MB")
        sev = parse(tool["parser"], report.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        res["status"] = "not evaluated (tool error)"
        res["reason"] = "unreadable report: %s" % str(exc)[:160]
        return res
    res["findings_by_severity"] = sev
    res["findings"] = sum(sev.values())
    res["status"] = "evaluated"
    return res


# --------------------------------------------------------------------------- commands
def _root(args):
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None:
        raise NotFound("not a Karvey project (no docs/spec)")
    if not (Path(root) / pj.CHANGES_DIR / args.change).is_dir():
        raise NotFound("change %r not found" % args.change)
    return root


def cmd_run(args):
    root = _root(args)
    cat = catalogue()
    project, _ = pj.load_project_json(root)
    chosen = chosen_tools(project, cat)
    cats = category_ids(cat)
    if args.categories:
        want = [c.strip() for c in args.categories.split(",") if c.strip()]
        for c in want:
            if c not in cats:
                raise Refused("unknown category %r (one of %s)" % (c, ", ".join(cats)))
        cats = want
    repo = repo_top(root)
    files = tracked_files(repo)
    timeout = int(kl.defaults().get("security_tool_timeout_s", 300))
    rows = []
    for c in cats:
        d = cat["categories"][c]
        hit = matches(files, d["applies_if_globs"])
        if not hit:
            rows.append({"category": c, "status": "not applicable", "reason": "no file matches the category"})
            continue
        tool = None
        for tid in chosen[c]:
            t = next(x for x in d["tools"] if x["id"] == tid)
            if shutil.which(t["detect"]) and (not t.get("requires_globs") or matches(files, t["requires_globs"])):
                tool = t
                break
        if tool is None:
            row = {"category": c, "status": "not evaluated (no tool)",
                   "reason": "none of %s on PATH" % ", ".join(chosen[c])}
        else:
            row = run_tool(root, args.change, c, tool, repo, timeout)
        if row["status"].startswith("not evaluated"):
            try:
                modes.record_hit(root, args.change, "security.tools", "%s: %s" % (c, row["status"]))
            except (modes.ModeError, OSError):
                pass
        rows.append(row)
    lines = []
    for r in rows:
        if r["status"] == "evaluated":
            sev = ", ".join("%s %d" % kv for kv in r["findings_by_severity"].items()) or "0 findings"
            lines.append("%-8s %s (%s): %s · `%s` · %s" % (r["category"], r["tool"], r["version"], sev,
                                                           " ".join(r["argv"]), r.get("evidence") or ""))
        else:
            lines.append("%-8s %s — %s" % (r["category"], r["status"], r.get("reason", "")))
    return kl.EXIT_OK, {"change": args.change, "categories": rows,
                        "not_evaluated": [r["category"] for r in rows if r["status"].startswith("not evaluated")]}, \
        "\n".join(lines)


COMMANDS = {"run": cmd_run}


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root")
    common.add_argument("--json", action="store_true")
    p = argparse.ArgumentParser(prog="karvey-security-scan.py", description="deterministic security tools")
    sub = p.add_subparsers(dest="command")
    r = sub.add_parser("run", parents=[common])
    r.add_argument("change")
    r.add_argument("--categories", help="comma list of secrets, sast, sca, iac (default: all)")
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
    if not args.command:
        parser.print_help(sys.stderr)
        return kl.EXIT_USAGE
    try:
        code, result, human = COMMANDS[args.command](args)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("security.not_found", str(exc))]),
                       args.json)
    except Refused as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, errors=[kl.issue("security.refused", str(exc))]),
                       args.json)
    return kl.emit(kl.envelope(TOOL, code, result=result), args.json, human=human)


if __name__ == "__main__":
    sys.exit(main())
