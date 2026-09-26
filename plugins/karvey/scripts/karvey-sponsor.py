#!/usr/bin/env python3
"""karvey-sponsor.py — the sponsor page of a change (architecture §1.13, C-13; REQ-W3-021..024).

    karvey-sponsor.py build   <change> --gate what|how|release [--outcome approved|changes_requested] [--root] [--json]
    karvey-sponsor.py deliver <change> [--root] [--json]

``build`` builds the allow-listed model (``karvey_lib/sponsor.py``), renders ``templates/sponsor.html`` and runs the
leak check (``karvey_lib/leakcheck.py``) over the model **and** the rendered text **before writing**. A hit →
exit 3: nothing is written, the page last written stays byte-identical and
``changes/{id}/sponsor-refusals.jsonl`` gains ``{at, gate, field, rule}`` (never the value). A clean page is written
to ``changes/{id}/sponsor.html`` and ``sponsor-history.jsonl`` gains ``{at, gate, outcome, sha256}``. No sponsor
declared → ``sponsor page: no sponsor declared`` once per change (recorded as ``no-sponsor``), nothing written.

``deliver`` builds the message payload **from the checked model only** — e-mail: the page as attachment; chat: a
summary and the repo-relative path; never a public URL — and leak-checks the payload itself (F-74): a refused
payload is not printed (exit 3). The agent sends the printed payload verbatim through the notification adapter; a
failure goes to the outbox, the gate is already closed.

Exit: 0 · 2 usage · 3 refused (leak) · 4 not found. Stdlib only.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import atomicio, leakcheck, project as pj, sponsor as sp  # noqa: E402

TOOL = "karvey-sponsor"
PAGE = "sponsor.html"
HISTORY = "sponsor-history.jsonl"
REFUSALS = "sponsor-refusals.jsonl"
NO_SPONSOR = "sponsor page: no sponsor declared"
GATES = ("what", "how", "release")


class Usage(Exception):
    pass


class NotFound(Exception):
    pass


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _root(args):
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None:
        raise NotFound("no Karvey project (docs/spec/project.json or docs/spec/changes/) at or above the cwd")
    return Path(root)


def _cdir(root, change):
    if not isinstance(change, str) or not change or "/" in change or "\\" in change or change.startswith("."):
        raise Usage("invalid change id %r" % (change,))
    d = root / pj.CHANGES_DIR / change
    if not (d / "spec.json").is_file():
        raise NotFound("change %r not found" % change)
    return d


def _append(path, rec):
    line = json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n"
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def _history(cdir):
    out = []
    try:
        lines = (cdir / HISTORY).read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for ln in lines:
        try:
            rec = json.loads(ln)
        except ValueError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def other_clients(root, project):
    """Other clients' names from the portfolio file (``project.json:portfolio.file``), or None when unreadable."""
    pf = (project or {}).get("portfolio") if isinstance((project or {}).get("portfolio"), dict) else None
    f = pf.get("file") if pf else None
    if not isinstance(f, str) or not f:
        return None
    p = Path(f) if os.path.isabs(f) else Path(root) / f
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    own = (project or {}).get("client")
    names = set()
    for r in data.get("repos", []) if isinstance(data, dict) else []:
        c = r.get("client") if isinstance(r, dict) else None
        if isinstance(c, str) and c.strip() and c != own:
            names.add(c.strip())
    return sorted(names)


def leak_ctx(root, project, stake):
    emails = [s["destination"]["target"] for s in stake.values()
              if isinstance(s.get("destination"), dict) and s["destination"].get("channel") == "email"
              and isinstance(s["destination"].get("target"), str)]
    leak = (project or {}).get("leak") if isinstance((project or {}).get("leak"), dict) else {}
    deny = [t for t in leak.get("deny_terms") or [] if isinstance(t, str)]
    return {"allowed_emails": emails, "other_clients": other_clients(root, project), "deny_terms": deny}


def checked(root, change, today=None):
    """``(model, page_html, verdict, stakeholders, project)``: the model, its render and the leak verdict."""
    project, _ = pj.load_project_json(root)
    spec = json.loads((_cdir(root, change) / "spec.json").read_text(encoding="utf-8-sig"))
    stake = pj.stakeholders(project or {}, spec)
    if "sponsor" not in stake:
        return None, None, None, stake, project
    model = sp.build_model(root, change, today=today, project=project)
    page = sp.render(model)
    fields = leakcheck.flatten(model)
    fields["page"] = leakcheck.text_of_html(page)
    verdict = leakcheck.check(fields, leak_ctx(root, project, stake))
    return model, page, verdict, stake, project


def refuse(cdir, gate, verdict, at):
    for h in verdict["hits"]:
        _append(cdir / REFUSALS, {"at": at, "gate": gate, "field": h["field"], "rule": h["rule"]})
    lines = ["leak check: FAIL — page not written, not delivered"]
    lines += ["  field  %-32s rule: %s (value not shown)" % (h["field"], h["rule"]) for h in verdict["hits"]]
    lines.append("%s unchanged · refusal report: fields and rules only, no values" % (
        (pj.CHANGES_DIR / cdir.name / PAGE).as_posix()))
    lines += verdict["notes"]
    return lines


def cmd_build(args):
    root = _root(args)
    cdir = _cdir(root, args.change)
    if args.gate not in GATES:
        raise Usage("--gate must be one of %s" % ", ".join(GATES))
    at = now_iso()
    model, page, verdict, _, _ = checked(root, args.change)
    if model is None:
        if any(h.get("outcome") == "no-sponsor" for h in _history(cdir)):
            return kl.EXIT_OK, {"change": args.change, "written": False, "sponsor": False}, [], ""
        _append(cdir / HISTORY, {"at": at, "gate": args.gate, "outcome": "no-sponsor", "sha256": None})
        return kl.EXIT_OK, {"change": args.change, "written": False, "sponsor": False}, [], NO_SPONSOR
    if not verdict["ok"]:
        lines = refuse(cdir, args.gate, verdict, at)
        return kl.EXIT_REFUSED, {"change": args.change, "written": False, "hits": verdict["hits"],
                                 "notes": verdict["notes"]}, [kl.issue("sponsor.leak", lines[0])], "\n".join(lines)
    data = page.encode("utf-8")
    atomicio.write_text_atomic(str(cdir / PAGE), page)
    sha = hashlib.sha256(data).hexdigest()
    _append(cdir / HISTORY, {"at": at, "gate": args.gate, "outcome": args.outcome, "sha256": sha})
    rel = (pj.CHANGES_DIR / args.change / PAGE).as_posix()
    lines = ["sponsor page: regenerated · leak check PASS · %s" % rel] + verdict["notes"]
    return kl.EXIT_OK, {"change": args.change, "written": True, "page": rel, "sha256": sha,
                        "notes": verdict["notes"]}, [], "\n".join(lines)


def payload_of(model, stake, change):
    """The delivery payload, from the checked model only."""
    dest = (stake.get("sponsor") or {}).get("destination") or {}
    ch = dest.get("channel") or "none"
    cost = model["cost"]
    waiting = len(model["waiting"]["questions"]) + len(model["waiting"]["gates"])
    summary = "%s — %s. %s: %s. %s: %s. %s: %s." % (
        model["title"], model["progress"]["phase"],
        "Cost to date", ("US$ %.2f" % cost["usd"]) if cost.get("measured") else cost.get("text", "not measured"),
        "Open risks", model["risks"]["open"], "Waiting for you", waiting)
    rel = (pj.CHANGES_DIR / change / PAGE).as_posix()
    body = {"channel": ch, "change": change, "subject": "Change report: %s" % model["title"], "summary": summary}
    if ch == "email":
        body["attachment"] = rel
    else:
        body["page"] = rel
    return body, dest


def cmd_deliver(args):
    root = _root(args)
    cdir = _cdir(root, args.change)
    model, page, verdict, stake, project = checked(root, args.change)
    if model is None:
        return kl.EXIT_OK, {"change": args.change, "delivered": False}, [], NO_SPONSOR
    if not verdict["ok"]:
        lines = refuse(cdir, "deliver", verdict, now_iso())
        return kl.EXIT_REFUSED, {"change": args.change, "delivered": False}, [kl.issue("sponsor.leak", lines[0])], \
            "\n".join(lines)
    body, dest = payload_of(model, stake, args.change)
    if body["channel"] == "none":
        return kl.EXIT_OK, {"change": args.change, "delivered": False, "payload": None}, [], \
            "not delivered: no destination declared"
    pv = leakcheck.check(leakcheck.flatten(body), leak_ctx(root, project, stake))
    if not pv["ok"]:
        lines = refuse(cdir, "deliver", pv, now_iso())
        return kl.EXIT_REFUSED, {"change": args.change, "delivered": False}, [kl.issue("sponsor.leak", lines[0])], \
            "\n".join(lines)
    res = {"change": args.change, "payload": body, "destination": {"channel": dest.get("channel"),
                                                                    "target": dest.get("target")}}
    human = "deliver to %s (%s): %s" % (dest.get("channel"), dest.get("target") or "—", json.dumps(
        body, ensure_ascii=False, sort_keys=True))
    return kl.EXIT_OK, res, [], human


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="Karvey project root (default: walk up from the cwd)")
    common.add_argument("--json", action="store_true", help="print one JSON envelope")
    p = argparse.ArgumentParser(prog="karvey-sponsor.py", description="The sponsor page of a change (C-13)")
    sub = p.add_subparsers(dest="command")
    b = sub.add_parser("build", parents=[common], help="build, leak-check and write the page")
    b.add_argument("change")
    b.add_argument("--gate", required=True, help="what | how | release")
    b.add_argument("--outcome", default="approved", choices=("approved", "changes_requested"))
    d = sub.add_parser("deliver", parents=[common], help="the checked delivery payload")
    d.add_argument("change")
    return p


COMMANDS = {"build": cmd_build, "deliver": cmd_deliver}


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
    if not args.command:
        parser.print_help(sys.stderr)
        return kl.EXIT_USAGE
    try:
        code, res, errors, human = COMMANDS[args.command](args)
    except Usage as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", str(exc))]), args.json)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("sponsor.not_found", str(exc))]),
                       args.json)
    if not args.json:
        if human:
            (sys.stderr if code else sys.stdout).write(human.rstrip("\n") + "\n")
        return code
    return kl.emit(kl.envelope(TOOL, code, result=res, errors=errors), True)


if __name__ == "__main__":
    sys.exit(main())
