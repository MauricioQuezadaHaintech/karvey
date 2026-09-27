#!/usr/bin/env python3
"""karvey-close.py — the gate-close steps in a fixed order (architecture §1.22-bis, C-26; REQ-W3-013, 014, 022, 033).

    karvey-close.py <change> <phase> --outcome approved|changes_requested [--gate what|how|release]
                    [--review-min N] [--verdict V] [--version V --env E] [--run-id R] [--root DIR] [--json]

Run **once**, after the gate answer is recorded (``approve`` / ``approve-gate`` / ``outcome``). It runs the
deterministic close steps and prints what is left for the agent:

1. ``sponsor`` — ``karvey-sponsor.py build`` (approved or changes requested alike) and ``deliver`` → the checked
   payload, the refusal lines, or ``no sponsor declared``;
2. ``events`` — the notifications due at this close (``qa`` at the qa phase with ``--verdict``, ``deploy`` with a
   version and environment), each filtered by the sent-log (``notify-sent``) and printed as a payload;
3. ``risks`` — at the *qa* and *release* gates, the open risks whose owners are to be asked (the risk register);
4. ``effort`` — ``karvey-state.py effort`` **last**, so steps 1–3 are charged to the phase that closes;
5. ``checkpoint`` — the checkpoint offer; the script compares the latest capture's context reading with the
   checkpoint rotation threshold and prints ``recommend: checkpoint + fresh session before the next skill`` when it
   is reached, ``context reading unavailable`` when there is no reading (one phase per session, REQ-W3-013).

Each step's failure is reported and the next step still runs. The gate outcome is never changed here: this
script records nothing about approvals. Exit: 0 (every step ran, failures are in the result) · 2 usage · 4 not
found. Stdlib only.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import effort as ef  # noqa: E402
from karvey_lib import project as pj  # noqa: E402
from karvey_lib import risks as rsk  # noqa: E402

TOOL = "karvey-close"
HERE = Path(__file__).resolve().parent
OUTCOMES = ("approved", "changes_requested")
GATES = ("what", "how", "release")
RISK_GATES = ("qa", "release")


class Usage(Exception):
    pass


def _script(name, *argv, root):
    """``(exit, envelope | None, stderr)`` of a sibling script run with ``--root`` and ``--json``."""
    cmd = [sys.executable, str(HERE / name)] + list(argv) + ["--root", str(root), "--json"]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        return 5, None, "%s: %s" % (type(exc).__name__, exc)
    env = None
    for line in reversed(cp.stdout.strip().splitlines()):
        try:
            env = json.loads(line)
            break
        except ValueError:
            continue
    return cp.returncode, env, cp.stderr.strip()


def _errors(env, stderr):
    msgs = [e.get("message") for e in (env or {}).get("errors") or [] if isinstance(e, dict)]
    return "; ".join(m for m in msgs if m) or stderr or "no output"


def gate_of(phase):
    with open(kl.SCHEMAS_DIR / "state-machine.json", encoding="utf-8-sig") as fh:
        for p in json.load(fh)["phases"]:
            if p["id"] == phase:
                return p.get("gate")
    return None


def step_sponsor(args, root, gate):
    out = {"step": "sponsor", "ok": True, "lines": []}
    rc, env, err = _script("karvey-sponsor.py", "build", args.change, "--gate", gate or "what", "--outcome",
                           args.outcome, root=root)
    res = (env or {}).get("result") or {}
    if rc != 0:
        out.update(ok=False, error="sponsor build: %s" % _errors(env, err), written=False)
        hits = [h for h in res.get("hits") or [] if isinstance(h, dict)]
        if hits:  # a leak refusal: each field and rule, never the value (REQ-W3-023, BUG-96)
            out["refused"] = [{"field": h.get("field"), "rule": h.get("rule")} for h in hits]
            out["lines"] = ["leak check: %s — rule %s (value not shown)" % (h.get("field"), h.get("rule"))
                            for h in hits] + ["the last written page is unchanged and nothing was delivered"]
        return out
    if res.get("sponsor") is False:
        out.update(written=False, lines=["sponsor page: no sponsor declared"])
        return out
    out.update(written=bool(res.get("written")), page=res.get("page"), notes=res.get("notes") or [])
    rc, env, err = _script("karvey-sponsor.py", "deliver", args.change, root=root)
    if rc != 0:
        out.update(ok=False, error="sponsor deliver: %s" % _errors(env, err))
        return out
    dres = (env or {}).get("result") or {}
    out["payload"] = dres.get("payload")
    out["destination"] = dres.get("destination")
    out["lines"].append("send the sponsor payload as printed, then record a failure with outbox add --op "
                        "deliver_sponsor" if dres.get("payload") else "sponsor page: not delivered (no destination)")
    return out


def due_events(args, phase):
    ev = []
    if phase == "qa":
        ev.append({"event": "qa", "item": "qa", "state": args.verdict})  # the review verdict only (BUG-116)
    if phase in ("deploying", "deployed") and args.version and args.env:
        ev.append({"event": "deploy", "version": args.version, "env": args.env})
    return ev


def step_events(args, root, phase):
    out = {"step": "events", "ok": True, "payloads": [], "skipped": []}
    rc, env, err = _script("karvey-config.py", "resolve", "notifications", root=root)
    if rc != 0:
        out.update(ok=False, error="resolve notifications: %s" % _errors(env, err))
        return out
    enabled = set(((env or {}).get("result") or {}).get("events") or [])
    for e in due_events(args, phase):
        if e["event"] not in enabled:
            out["skipped"].append("%s: not in notifications.events" % e["event"])
            continue
        if e["event"] == "qa" and not e.get("state"):  # one state source for the sent-log: the verdict (BUG-116)
            out.update(ok=False, error="qa notification: the qa close needs --verdict {the review verdict}")
            continue
        argv = ["notify-sent", args.change, "--event", e["event"], "--record"]
        for k in ("item", "state", "version", "env"):
            if e.get(k):
                argv += ["--%s" % k, e[k]]
        if args.run_id:
            argv += ["--run-id", args.run_id]
        rc, env, err = _script("karvey-config.py", *argv, root=root)
        if rc != 0:
            out.update(ok=False, error="notify-sent %s: %s" % (e["event"], _errors(env, err)))
            continue
        res = (env or {}).get("result") or {}
        if res.get("status") == "sent":
            out["skipped"].append("%s: already sent (run %s)" % (e["event"], args.run_id or "—"))
            continue
        payload = dict(e, change=args.change, phase=phase, outcome=args.outcome, run_id=args.run_id,
                       at=res.get("at"))
        out["payloads"].append(payload)
    return out


def step_risks(args, root, gate):
    out = {"step": "risks", "ok": True, "ask": []}
    if gate not in RISK_GATES and args.phase != "qa":
        out["note"] = "no risk review at this gate"
        return out
    cdir = Path(root) / pj.CHANGES_DIR / args.change
    try:
        with open(cdir / "spec.json", encoding="utf-8-sig") as fh:
            spec = json.load(fh)
    except (OSError, ValueError) as exc:
        out.update(ok=False, error="risks: spec.json unreadable (%s)" % exc)
        return out
    items, warns = rsk.gate_review(rsk.read(cdir), rsk.phase_start(spec, "qa"))
    out["ask"] = [{"risk": r["id"], "owner": r["owner"] or "?", "trigger": r["trigger"],
                   "last_review": r["last_review"]} for r in items]
    out["warnings"] = warns
    out["note"] = ("ask each owner for a state, then record it with karvey-state.py risk %s R-N "
                   "review|close|mitigate|accept|move" % args.change) if items else "no open risk"
    return out


def step_effort(args, root):
    out = {"step": "effort", "ok": True}
    argv = ["effort", args.change, args.phase]
    if args.review_min is not None:
        argv += ["--review-min", str(args.review_min)]
    rc, env, err = _script("karvey-state.py", *argv, root=root)
    res = (env or {}).get("result") or {}
    if rc != 0:
        out.update(ok=False, error="effort: %s" % _errors(env, err))
        return out
    entry = res.get("entry") or {}
    out.update(usd=entry.get("usd"), tokens=entry.get("tokens"), review_min=entry.get("review_min"),
               advice=res.get("advice"))
    return out


def step_checkpoint(root):
    """Step 5 (C-08): the checkpoint offer, and the script's own comparison of the context reading with the
    checkpoint rotation threshold (``defaults.json`` ``context_pct.red``, else ``context_tokens.red``)."""
    line = "offer /karvey-checkpoint save: the next phase can start in a fresh session (one phase per session)"
    out = {"step": "checkpoint", "ok": True, "lines": [line]}
    d = kl.defaults()
    try:
        chk = ef.context_check(pj.state_dir(root, create=False) / ef.CAPTURE_DIR, ef.root_key(root),
                               (d.get("context_pct") or {}).get("red"), (d.get("context_tokens") or {}).get("red"))
    except OSError:
        chk = {"status": "unavailable", "line": ef.READING_UNAVAILABLE}
    out["context"] = chk["status"]
    out["lines"].append(chk["line"])
    if chk["status"] != "recommend":
        out["lines"].append("continuing in this session is allowed")
    return out


def run(args):
    if args.outcome not in OUTCOMES:
        raise Usage("--outcome must be one of %s" % ", ".join(OUTCOMES))
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None:
        return kl.EXIT_NOT_FOUND, None, "no Karvey project here"
    if not (Path(root) / pj.CHANGES_DIR / args.change / "spec.json").is_file():
        return kl.EXIT_NOT_FOUND, None, "change %r not found" % args.change
    gate = args.gate or gate_of(args.phase)
    steps = [step_sponsor(args, root, gate), step_events(args, root, args.phase), step_risks(args, root, gate)]
    steps += [step_effort(args, root), step_checkpoint(root)]
    res = {"change": args.change, "phase": args.phase, "gate": gate, "outcome": args.outcome,
           "order": [s["step"] for s in steps], "steps": steps,
           "failures": [s["error"] for s in steps if not s["ok"]]}
    return kl.EXIT_OK, res, None


def render(res):
    L = ["gate close — %s %s (%s)" % (res["change"], res["phase"], res["outcome"])]
    for s in res["steps"]:
        head = "%d. %s: %s" % (res["order"].index(s["step"]) + 1, s["step"], "ok" if s["ok"] else "FAILED — " +
                               s.get("error", ""))
        L.append(head)
        for ln in s.get("lines") or []:
            L.append("   " + ln)
        if s["step"] == "sponsor" and s.get("payload"):
            L.append("   payload: %s" % json.dumps(s["payload"], ensure_ascii=False, sort_keys=True))
        for p in s.get("payloads") or []:
            L.append("   send: %s" % json.dumps(p, ensure_ascii=False, sort_keys=True))
        for sk in s.get("skipped") or []:
            L.append("   skipped: %s" % sk)
        for a in s.get("ask") or []:
            L.append("   ask %s: %s (trigger %s · last review %s)" % (a["owner"], a["risk"], a["trigger"] or "?",
                                                                  a["last_review"]))
        for w in s.get("warnings") or []:
            L.append("   WARNING " + w)
        if s.get("note"):
            L.append("   " + s["note"])
        if s["step"] == "effort" and s["ok"]:
            usd = s.get("usd") or {}
            L.append("   US$ %s (%s)" % (usd.get("value", "n/a"), usd.get("quality", "n/a")))
    return "\n".join(L)


def build_parser():
    p = argparse.ArgumentParser(prog="karvey-close.py", description="Gate-close steps in a fixed order (C-26)")
    p.add_argument("change")
    p.add_argument("phase")
    p.add_argument("--outcome", required=True)
    p.add_argument("--gate", choices=GATES)
    p.add_argument("--review-min", type=int, default=None)
    p.add_argument("--verdict", help="qa: the review verdict the qa notification carries (required for it)")
    p.add_argument("--version", help="deploy event: the version")
    p.add_argument("--env", help="deploy event: the environment")
    p.add_argument("--run-id", dest="run_id", help="the run or iteration id the payloads carry")
    p.add_argument("--root")
    p.add_argument("--json", action="store_true")
    return p


def main(argv=None):
    parser = build_parser()
    as_json = "--json" in (argv if argv is not None else sys.argv[1:])
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else kl.EXIT_USAGE
        if code != 0 and as_json:
            kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", "invalid arguments")]), True)
        return kl.EXIT_USAGE if code != 0 else 0
    try:
        code, res, err = run(args)
    except Usage as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", str(exc))]), args.json)
    except Exception as exc:  # never a traceback: an envelope with exit 5 (BUG-119)
        return kl.emit(kl.envelope(TOOL, kl.EXIT_INTERNAL, errors=[kl.issue("close.internal", "%s: %s" % (
            type(exc).__name__, exc))]), args.json)
    if code != kl.EXIT_OK:
        return kl.emit(kl.envelope(TOOL, code, errors=[kl.issue("close.not_found", err)]), args.json)
    return kl.emit(kl.envelope(TOOL, code, result=res), args.json, human=render(res))


if __name__ == "__main__":
    sys.exit(main())
