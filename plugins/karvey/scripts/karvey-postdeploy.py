#!/usr/bin/env python3
"""karvey-postdeploy.py — post-deploy verification against the contract in ``infra.md`` (architecture §1.15 C-19).

    karvey-postdeploy.py probe <change> [--env prod] [--service NAME] [--samples N] [--interval-s S] [--root] [--json]
    karvey-postdeploy.py evaluate <change> [--env prod] [--service NAME] [--observed FILE] [--version X]
                                          [--root] [--json]

**Contract.** A fenced block ``karvey-postdeploy`` (JSON) in ``changes/{id}/infra.md``, one per service and
environment: ``{service, env, health:[url], routes:[{url, expect_status}], thresholds:{error_rate_pct,
p95_ms_vs_baseline_pct, new_5xx}, window_min, metrics_source:{kind, how}, rollback:{command, doc}}``.
A contract without ``rollback.command`` is reported ``incomplete``.

**probe** runs the ``health`` and ``routes`` probes with ``urllib``: ``https://`` only (``http://localhost`` /
``127.0.0.1`` outside prod), 5 s per request, a redirect to another host is never followed (it counts as an
error), samples spread over ``window_min`` (``--samples`` / ``--interval-s`` override). Results go to
``changes/{id}/postdeploy_probe_{env}.json``.

**evaluate** compares the probe results and the observed metrics (``--observed``: ``{error_rate_pct, p95_ms,
baseline_p95_ms, new_5xx}``, gathered by the deploy skill from ``metrics_source``) with the thresholds:
``pass`` · ``regression`` · ``not-evaluated`` (no contract, no thresholds, nothing observed — never ``pass``).
It writes the env's section of ``changes/{id}/deploy_evidence.md`` and prints the ``deploy-record`` command.
Nothing in ``infra.md`` is ever executed: the rollback command is only shown.

Exit: 0 pass or not-evaluated · 1 regression · 2 usage · 3 refused (unsafe URL) · 4 not found. Stdlib only.
"""
import argparse
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import atomicio, project as pj  # noqa: E402

TOOL = "karvey-postdeploy"
TIMEOUT_S = 5
DEFAULT_WINDOW_MIN = 10
DEFAULT_SAMPLES = 5
EVIDENCE_FILE = "deploy_evidence.md"
_BLOCK = re.compile(r"^```karvey-postdeploy[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
_LOCAL = ("localhost", "127.0.0.1", "::1")
RECOMMEND = "add a post-deploy contract to infra.md (karvey-infra: health, routes, thresholds, rollback)"


class NotFound(Exception):
    pass


class Refused(Exception):
    pass


# --------------------------------------------------------------------------- contract
def contracts(text):
    """Every ``karvey-postdeploy`` block of ``infra.md`` as ``(contract | None, error | None)``."""
    out = []
    for m in _BLOCK.finditer(text or ""):
        try:
            c = json.loads(m.group(1))
            out.append((c, None) if isinstance(c, dict) else (None, "block is not a JSON object"))
        except ValueError as exc:
            out.append((None, "block is not valid JSON: %s" % exc))
    return out


def contract_problems(c):
    """``incomplete`` reasons of one contract (REQ-W2-075)."""
    out = []
    if not (c.get("health") or c.get("routes")):
        out.append("no health endpoint or route")
    th = c.get("thresholds")
    if not isinstance(th, dict) or not any(k in th for k in ("error_rate_pct", "p95_ms_vs_baseline_pct", "new_5xx")):
        out.append("no thresholds")
    rb = c.get("rollback")
    if not (isinstance(rb, dict) and isinstance(rb.get("command"), str) and rb["command"].strip()):
        out.append("no rollback command")
    if not isinstance(c.get("metrics_source"), dict):
        out.append("no metrics source")
    return out


def load_contract(root, change, env, service=None):
    """``(contract, problems, errors)`` for ``env`` (and ``service``); ``(None, …)`` when there is none."""
    cdir = Path(root) / pj.CHANGES_DIR / change
    if not (cdir / "spec.json").is_file():
        raise NotFound("change %r not found" % change)
    try:
        text = (cdir / "infra.md").read_text(encoding="utf-8-sig")
    except OSError:
        return None, [], ["no infra.md"]
    found, errors = [], []
    for c, err in contracts(text):
        if err:
            errors.append(err)
        elif c.get("env") == env and (service is None or c.get("service") == service):
            found.append(c)
    if not found:
        return None, [], errors + ["no karvey-postdeploy block for env %r%s" % (
            env, "" if service is None else " and service %r" % service)]
    if len(found) > 1:
        return None, [], errors + ["%d blocks for env %r: pass --service" % (len(found), env)]
    return found[0], contract_problems(found[0]), errors


def check_url(url, env):
    """``https://`` only; ``http://`` to the local host outside prod. Raises :class:`Refused`."""
    if not isinstance(url, str):
        raise Refused("probe URL is not a string: %r" % (url,))
    p = urllib.parse.urlsplit(url)
    if p.scheme == "https" and p.hostname:
        return url
    if p.scheme == "http" and p.hostname in _LOCAL and env != "prod":
        return url
    raise Refused("probe URL %r refused: https:// only (http://localhost outside prod)" % url[:120])


# --------------------------------------------------------------------------- probe
class _SameHostRedirect(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only to the same scheme and host; anything else stays a 3xx (not followed)."""

    def __init__(self, env):
        super().__init__()
        self.env = env

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old = urllib.parse.urlsplit(req.full_url)
        new = urllib.parse.urlsplit(urllib.parse.urljoin(req.full_url, newurl))
        if (new.scheme, new.hostname, new.port) != (old.scheme, old.hostname, old.port):
            return None
        try:
            check_url(new.geturl(), self.env)
        except Refused:
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, env):
    """``{url, status, latency_ms, error}`` of one GET."""
    opener = urllib.request.build_opener(_SameHostRedirect(env))
    t0 = time.monotonic()
    rec = {"url": url, "status": None, "latency_ms": None, "error": None}
    try:
        with opener.open(urllib.request.Request(url, method="GET", headers={"User-Agent": "karvey-postdeploy"}),
                         timeout=TIMEOUT_S) as resp:
            resp.read(65536)
            rec["status"] = resp.status
    except urllib.error.HTTPError as exc:
        rec["status"] = exc.code
        if 300 <= exc.code < 400:
            rec["error"] = "redirect to another host not followed"
    except (urllib.error.URLError, OSError, ValueError) as exc:
        rec["error"] = str(getattr(exc, "reason", exc))[:160]
    rec["latency_ms"] = int((time.monotonic() - t0) * 1000)
    return rec


def probe_targets(c, env):
    out = [{"kind": "health", "url": check_url(u, env), "expect_status": 200} for u in c.get("health") or []]
    for r in c.get("routes") or []:
        url = r.get("url") if isinstance(r, dict) else r
        exp = r.get("expect_status", 200) if isinstance(r, dict) else 200
        out.append({"kind": "route", "url": check_url(url, env), "expect_status": exp})
    return out


def run_probes(c, env, samples, interval_s):
    targets = probe_targets(c, env)  # every URL checked before the first request
    rows = []
    for i in range(samples):
        for t in targets:
            rec = fetch(t["url"], env)
            rec.update(kind=t["kind"], expect_status=t["expect_status"], sample=i + 1)
            rec["ok"] = rec["error"] is None and _status_ok(rec["status"], t["expect_status"])
            rows.append(rec)
        if i + 1 < samples and interval_s > 0:
            time.sleep(interval_s)
    return rows


def _status_ok(status, expect):
    if status is None:
        return False
    if isinstance(expect, list):
        return status in expect
    return status == expect


def probe_path(root, change, env):
    return Path(root) / pj.CHANGES_DIR / change / ("postdeploy_probe_%s.json" % re.sub(r"[^a-z0-9-]", "", env))


# --------------------------------------------------------------------------- evaluate
def _p95(values):
    v = sorted(x for x in values if isinstance(x, (int, float)))
    if not v:
        return None
    return v[max(0, int(math.ceil(0.95 * len(v))) - 1)]


def evaluate(contract, problems, probes, observed):
    """``{result, checks, notes}`` — pass · regression · not-evaluated (REQ-W2-076, 077)."""
    if contract is None:
        return {"result": "not-evaluated", "checks": [], "notes": [RECOMMEND]}
    th = contract.get("thresholds") if isinstance(contract.get("thresholds"), dict) else {}
    if not th:
        return {"result": "not-evaluated", "checks": [], "notes": ["the contract has no thresholds: " + RECOMMEND]}
    observed = observed if isinstance(observed, dict) else {}
    probes = probes or []
    if not probes and not observed:
        return {"result": "not-evaluated", "checks": [], "notes": ["no probe ran and no metric was observed"]}
    checks, notes = [], []
    if "error_rate_pct" in th:
        probe_rate = (100.0 * sum(1 for p in probes if not p.get("ok")) / len(probes)) if probes else None
        obs = observed.get("error_rate_pct")
        values = [x for x in (probe_rate, obs) if isinstance(x, (int, float))]
        if values:
            v = max(values)
            checks.append({"name": "error_rate_pct", "value": round(v, 2), "threshold": th["error_rate_pct"],
                           "ok": v <= th["error_rate_pct"],
                           "source": "probes %s · observed %s" % (_fmt(probe_rate), _fmt(obs))})
        else:
            notes.append("error rate not evaluated (no probe, no observed value)")
    if "p95_ms_vs_baseline_pct" in th:
        p95 = observed.get("p95_ms")
        if not isinstance(p95, (int, float)):
            p95 = _p95(p.get("latency_ms") for p in probes if p.get("ok"))
        base = observed.get("baseline_p95_ms")
        if isinstance(p95, (int, float)) and isinstance(base, (int, float)) and base > 0:
            inc = 100.0 * (p95 - base) / base
            checks.append({"name": "p95_ms_vs_baseline_pct", "value": round(inc, 1),
                           "threshold": th["p95_ms_vs_baseline_pct"], "ok": inc <= th["p95_ms_vs_baseline_pct"],
                           "source": "p95 %s ms vs baseline %s ms" % (_fmt(p95), _fmt(base))})
        else:
            notes.append("p95 vs baseline not evaluated (no production baseline observed)")
    if "new_5xx" in th:
        probe_5xx = sum(1 for p in probes if isinstance(p.get("status"), int) and p["status"] >= 500)
        obs = observed.get("new_5xx")
        v = max(probe_5xx, obs if isinstance(obs, int) else 0)
        checks.append({"name": "new_5xx", "value": v, "threshold": th["new_5xx"], "ok": v <= th["new_5xx"],
                       "source": "probes %d · observed %s" % (probe_5xx, _fmt(obs))})
    if not checks:
        return {"result": "not-evaluated", "checks": [], "notes": notes}
    if problems:
        notes.append("contract incomplete: %s" % "; ".join(problems))
    return {"result": "pass" if all(c["ok"] for c in checks) else "regression", "checks": checks, "notes": notes}


def _fmt(v):
    return "—" if v is None else (("%.2f" % v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v))


def _cell(v):
    return str(v).replace("|", "\\|").replace("\n", " ")


def render_section(env, contract, verdict, probes):
    out = ["## %s" % env, "", "Result: **%s**" % verdict["result"]]
    if contract is not None:
        out.append("Service: `%s` · window %s min · metrics: %s" % (
            _cell(contract.get("service", "?")), contract.get("window_min", DEFAULT_WINDOW_MIN),
            _cell((contract.get("metrics_source") or {}).get("kind", "—"))))
    out.append("")
    if verdict["checks"]:
        out += ["| Threshold | Value | Limit | OK | Source |", "|---|---|---|---|---|"]
        out += ["| %s | %s | %s | %s | %s |" % (c["name"], c["value"], c["threshold"], "yes" if c["ok"] else "NO",
                                              _cell(c["source"])) for c in verdict["checks"]]
        out.append("")
    if probes:
        out += ["| Sample | Kind | URL | Status | Expected | Latency ms | OK |", "|---|---|---|---|---|---|---|"]
        out += ["| %d | %s | %s | %s | %s | %s | %s |" % (p["sample"], p["kind"], _cell(p["url"]), _fmt(p["status"]),
                                                        _cell(p["expect_status"]), _fmt(p["latency_ms"]),
                                                        "yes" if p["ok"] else "NO" + (" (%s)" % _cell(p["error"])
                                                                                      if p["error"] else ""))
                for p in probes]
        out.append("")
    out += ["- %s" % _cell(n) for n in verdict["notes"]]
    if contract is not None and isinstance(contract.get("rollback"), dict) and contract["rollback"].get("command"):
        out.append("- rollback (shown, never run by this tool): `%s`" % _cell(contract["rollback"]["command"]))
    return "\n".join(out).rstrip() + "\n"


def write_evidence(root, change, env, section):
    path = Path(root) / pj.CHANGES_DIR / change / EVIDENCE_FILE
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        text = "# Deploy evidence: %s\n\n> Written by `karvey-postdeploy.py evaluate`, one section per environment.\n" \
               % change
    parts = re.split(r"(?m)^(?=## )", text)
    head, sections = parts[0], [s for s in parts[1:]]
    sections = [s for s in sections if not s.startswith("## %s\n" % env)] + [section]
    atomicio.write_text_atomic(path, head.rstrip() + "\n\n" + "\n".join(s.rstrip() + "\n" for s in sections),
                               expected_sha256="*")
    return path


# --------------------------------------------------------------------------- commands
def _root(args):
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None:
        raise NotFound("not a Karvey project (no docs/spec)")
    return root


def cmd_probe(args):
    root = _root(args)
    c, problems, errors = load_contract(root, args.change, args.env, args.service)
    if c is None:
        res = {"change": args.change, "env": args.env, "result": "not-evaluated", "notes": errors + [RECOMMEND]}
        return kl.EXIT_OK, res, "not-evaluated: %s" % "; ".join(res["notes"])
    samples = args.samples if args.samples is not None else DEFAULT_SAMPLES
    window = c.get("window_min", DEFAULT_WINDOW_MIN)
    interval = args.interval_s if args.interval_s is not None else (
        (float(window) * 60.0 / samples) if samples > 1 and isinstance(window, (int, float)) else 0)
    rows = run_probes(c, args.env, max(1, samples), interval)
    path = probe_path(root, args.change, args.env)
    atomicio.write_text_atomic(path, json.dumps({"env": args.env, "service": c.get("service"), "probes": rows},
                                                indent=2) + "\n", expected_sha256="*")
    bad = sum(1 for r in rows if not r["ok"])
    res = {"change": args.change, "env": args.env, "probes": rows, "failed": bad, "problems": problems,
           "file": os.path.relpath(str(path), str(root)).replace(os.sep, "/")}
    return kl.EXIT_OK, res, "%d probe(s), %d failed → %s%s" % (
        len(rows), bad, res["file"], ("\ncontract incomplete: " + "; ".join(problems)) if problems else "")


def cmd_evaluate(args):
    root = _root(args)
    c, problems, errors = load_contract(root, args.change, args.env, args.service)
    observed = None
    if args.observed:
        try:
            observed = json.loads(Path(args.observed).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise NotFound("--observed %s is unreadable: %s" % (args.observed, exc))
    probes = []
    pp = probe_path(root, args.change, args.env)
    if c is not None and pp.is_file():
        try:
            probes = json.loads(pp.read_text(encoding="utf-8")).get("probes") or []
        except ValueError:
            probes = []
    verdict = evaluate(c, problems, probes, observed)
    if c is None:
        verdict["notes"] = errors + verdict["notes"]
    path = write_evidence(root, args.change, args.env, render_section(args.env, c, verdict, probes))
    ev_rel = os.path.relpath(str(path), str(root)).replace(os.sep, "/")
    record = 'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" deploy-record %s --env %s --version %s ' \
             '--verification %s --evidence %s' % (args.change, args.env, args.version or "{version}",
                                                  verdict["result"], ev_rel)
    res = dict(verdict, change=args.change, env=args.env, evidence=ev_rel, deploy_record=record,
               problems=problems,
               rollback=(c or {}).get("rollback") if verdict["result"] == "regression" else None)
    lines = ["post-deploy verification %s (%s): %s" % (args.change, args.env, verdict["result"])]
    lines += ["  %s %s (limit %s) %s" % (x["name"], x["value"], x["threshold"], "ok" if x["ok"] else "EXCEEDED")
              for x in verdict["checks"]]
    lines += ["  note: %s" % n for n in verdict["notes"]]
    if res["rollback"]:
        lines.append("  rollback to propose to the human (not run): %s" % res["rollback"].get("command"))
    lines.append("record: %s" % record)
    return (kl.EXIT_FINDINGS if verdict["result"] == "regression" else kl.EXIT_OK), res, "\n".join(lines)


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root")
    common.add_argument("--json", action="store_true")
    common.add_argument("--env", default="prod")
    common.add_argument("--service")
    p = argparse.ArgumentParser(prog="karvey-postdeploy.py", description="post-deploy verification")
    sub = p.add_subparsers(dest="command")
    pr = sub.add_parser("probe", parents=[common])
    pr.add_argument("change")
    pr.add_argument("--samples", type=int)
    pr.add_argument("--interval-s", type=float)
    ev = sub.add_parser("evaluate", parents=[common])
    ev.add_argument("change")
    ev.add_argument("--observed", help="JSON: {error_rate_pct, p95_ms, baseline_p95_ms, new_5xx}")
    ev.add_argument("--version")
    return p


COMMANDS = {"probe": cmd_probe, "evaluate": cmd_evaluate}


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
    if not re.match(r"^[a-z0-9][a-z0-9-]{0,30}$", args.env or ""):
        return kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", "invalid --env")]), args.json)
    try:
        code, result, human = COMMANDS[args.command](args)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("postdeploy.not_found", str(exc))]),
                       args.json)
    except Refused as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, errors=[kl.issue("postdeploy.refused", str(exc))]),
                       args.json)
    return kl.emit(kl.envelope(TOOL, code, result=result), args.json, human=human)


if __name__ == "__main__":
    sys.exit(main())
