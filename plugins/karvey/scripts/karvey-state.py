#!/usr/bin/env python3
"""karvey-state.py — the Karvey state tool (architecture §1.2, wave1-hardening).

The one writer of ``spec.json:phase``, ``approvals``, ``skipped``, ``phase_history`` and
``updated_at``. Python >= 3.9, standard library only.

Shared CLI contract (§1.1): ``--root DIR`` (else walk up from the cwd to the git top level),
``--json`` (one envelope on stdout), exit codes 0 ok · 1 findings · 2 usage · 3 refused ·
4 not found / unreadable / corrupt · 5 internal.

Commands:
  validate [PATH…|--all] [--strict]     schema + semantic checks (§2.2, §2.3)
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import atomicio, project as pj, schema_lite as sl  # noqa: E402

TOOL = "karvey-state"
SCHEMA_VERSION = 1


class Refused(Exception):
    """A precondition is unmet: exit 3 with this message."""

    def __init__(self, message, code="state.refused", result=None):
        super().__init__(message)
        self.code = code
        self.result = result or {}


class NotFound(Exception):
    """Input not found / unreadable / corrupt: exit 4."""


class Usage(Exception):
    """Usage error: exit 2."""


# --------------------------------------------------------------------------- data files
_CACHE = {}


def _schema_file(name):
    if name not in _CACHE:
        with open(kl.SCHEMAS_DIR / name, encoding="utf-8-sig") as fh:
            _CACHE[name] = json.load(fh)
    return _CACHE[name]


def machine():
    return _schema_file("state-machine.json")


def legacy_map():
    return _schema_file("legacy-phase-map.json")


def registry():
    if "registry" not in _CACHE:
        _CACHE["registry"] = sl.load_registry()
    return _CACHE["registry"]


def validator(kind, file=None):
    reg = registry()
    sid = "karvey:project.schema.json" if kind == "project" else "karvey:spec.schema.json"
    return sl.Validator(reg[sid], reg, file=file)


def phase_ids():
    return [p["id"] for p in machine()["phases"]]


def phase_def(pid):
    for p in machine()["phases"]:
        if p["id"] == pid:
            return p
    return None


def phase_index(pid):
    ids = phase_ids()
    return ids.index(pid) if pid in ids else -1


def map_phase(value):
    """``(phase, tier)``: tier ``enum`` · ``exact`` · ``proposed`` · ``unmappable``."""
    if isinstance(value, str) and value in phase_ids():
        return value, "enum"
    tiers = legacy_map()["tiers"]
    if isinstance(value, str) and value in tiers["exact"]:
        return tiers["exact"][value], "exact"
    if isinstance(value, str) and value in tiers["proposed"]:
        return tiers["proposed"][value], "proposed"
    return None, "unmappable"


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_dt(value):
    if not sl.is_datetime_tz(value):
        return None
    v = value[:-1] + "+00:00" if value.endswith("Z") else value
    if "." in v:
        head, rest = v.split(".", 1)
        digits = "".join(ch for ch in rest if ch.isdigit())
        tail = rest[len(digits):]
        v = head + "." + (digits + "000000")[:6] + tail
    try:
        return datetime.fromisoformat(v)
    except ValueError:
        return None


# --------------------------------------------------------------------------- files
def resolve_root(args):
    root = pj.find_root(start=os.getcwd(), root=getattr(args, "root", None))
    if root is None:
        where = args.root if getattr(args, "root", None) else os.getcwd()
        raise NotFound("not a Karvey project (no docs/spec/project.json or docs/spec/changes/): %s" % where)
    return root


def rel(root, path):
    try:
        return os.path.relpath(str(path), str(root)).replace(os.sep, "/")
    except ValueError:
        return str(path)


def all_files(root):
    """Every ``spec.json`` under ``docs/spec`` (archive included) and ``docs/spec/project.json``."""
    base = Path(root) / pj.SPEC_DIR
    out = sorted(p for p in base.rglob("spec.json") if p.is_file())
    pjson = Path(root) / pj.PROJECT_JSON
    if pjson.is_file():
        out.append(pjson)
    return out


def kind_of(path):
    return "project" if Path(path).name == "project.json" else "spec"


def schema_mode(root, override_strict=False):
    if override_strict:
        return "strict"
    data, _ = pj.load_project_json(root)
    if isinstance(data, dict) and data.get("schema_mode") == "strict":
        return "strict"
    return "advisory"


# --------------------------------------------------------------------------- validation
def _sev(strict):
    return "error" if strict else "warning"


def _is_legacy_transition(entry):
    return isinstance(entry, dict) and "phase" not in entry and "from" in entry and "to" in entry


def embedded_skip(approval):
    """The reason of a legacy embedded skip (``{skipped: true, …}``, ``{na: true}``), or None."""
    if not isinstance(approval, dict):
        return None
    if not any(approval.get(k) is True for k in ("skipped", "na", "not_applicable")):
        return None
    for k in ("skip_reason", "reason", "na_reason", "nota", "note"):
        v = approval.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "(legacy: no reason recorded)"


def approval_state(data, phase):
    """``approved`` · ``skipped`` · ``pending`` for an approvable phase of ``data``."""
    pdef = phase_def(phase)
    key = pdef["approval"] if pdef else None
    skipped = data.get("skipped") if isinstance(data.get("skipped"), dict) else {}
    if phase in skipped and isinstance(skipped[phase], str) and skipped[phase].strip():
        return "skipped"
    approvals = data.get("approvals") if isinstance(data.get("approvals"), dict) else {}
    ap = approvals.get(key) if key else None
    if key == "prod":
        if isinstance(ap, dict) and isinstance(ap.get("by"), str) and ap["by"].strip() \
                and ap.get("role") == "human" and isinstance(ap.get("ref"), str) and ap["ref"].strip():
            return "approved"
        return "pending"
    if isinstance(ap, dict) and ap.get("approved") is True:
        return "approved"
    if embedded_skip(ap) is not None and pdef and pdef["skippable"]:
        return "skipped"
    return "pending"


def gate_phases_before(index):
    """Approvable phases strictly before ``index`` that are preconditions (deploy and prod are not)."""
    out = []
    for p in machine()["phases"][:max(index, 0)]:
        if p["approval"] and p["approval"] not in ("deploy", "prod"):
            out.append(p["id"])
    return out


def _legacy_rewrite(issues, data, strict, file):
    """Recognised legacy shapes (§2.5, REQ-W1-003): one ``state.legacy_*`` issue instead of the
    raw schema errors, a warning in advisory mode and an error in strict mode."""
    out = []
    sev = _sev(strict)
    phase = data.get("phase")
    mapped, tier = map_phase(phase)
    legacy_hist = set()
    hist = data.get("phase_history")
    if isinstance(hist, list):
        legacy_hist = {i for i, e in enumerate(hist) if _is_legacy_transition(e)}
    for it in issues:
        p = it.get("path") or ""
        if p == "$.phase" and it["code"] == "schema.enum" and tier in ("exact", "proposed"):
            continue
        if p.startswith("$.phase_history[") and legacy_hist:
            try:
                idx = int(p[len("$.phase_history["):].split("]", 1)[0])
            except ValueError:
                idx = -1
            if idx in legacy_hist:
                continue
        if p == "$.approvals" and it["code"] == "schema.type" and data.get("approvals", 0) is None:
            continue
        out.append(it)
    if tier in ("exact", "proposed"):
        how = "validate --fix" if tier == "exact" else "validate --fix --accept-proposed"
        out.append(kl.issue("state.legacy_phase",
                            "phase %r is outside the enum: legacy value (%s tier) that maps to %r; run %s"
                            % (phase, tier, mapped, how),
                            severity=sev, file=file, path="$.phase", expected=phase_ids(), got=phase))
    for idx in sorted(legacy_hist):
        e = hist[idx]
        out.append(kl.issue("state.legacy_history",
                            "hand-written transition entry {from: %r, to: %r}; run validate --fix"
                            % (e.get("from"), e.get("to")),
                            severity=sev, file=file, path="$.phase_history[%d]" % idx,
                            expected="{phase, entered_at, exited_at?}", got=sorted(e)))
    if "approvals" in data and data["approvals"] is None:
        out.append(kl.issue("state.legacy_approvals_null", "approvals is null (legacy); run validate --fix",
                            severity=sev, file=file, path="$.approvals", expected="object", got=None))
    return out


def semantic_spec(data, strict, file):
    """§2.3 checks beyond the schema, for a spec.json."""
    out = []
    sev = _sev(strict)
    phase = data.get("phase")
    mapped, tier = map_phase(phase)
    # unknown / unmappable phase: the schema already reports the enum error.
    if mapped is None:
        return out
    idx = phase_index(mapped)
    skipped = data.get("skipped") if isinstance(data.get("skipped"), dict) else {}
    approvals = data.get("approvals") if isinstance(data.get("approvals"), dict) else {}

    # past an approvable phase that is neither approved nor skipped (H-22)
    for ph in gate_phases_before(idx):
        if approval_state(data, ph) == "pending":
            out.append(kl.issue("state.gate_skipped",
                                "phase %r is past %r, which is neither approved nor skipped" % (mapped, ph),
                                severity=sev, file=file, path="$.approvals.%s" % phase_def(ph)["approval"],
                                expected="approved or skipped", got="pending"))
    if mapped == "archived" and approval_state(data, "deployed") == "pending":
        out.append(kl.issue("state.prod_missing", "archived without a human approvals.prod (by, role, ref)",
                            severity="error", file=file, path="$.approvals.prod",
                            expected="{by, role: human, date, ref}", got=approvals.get("prod")))

    # embedded legacy skips
    for key, ap in approvals.items():
        reason = embedded_skip(ap)
        if reason is not None:
            pdef = phase_def(key)
            fix = "validate --fix moves it to skipped" if pdef and pdef["skippable"] else \
                "phase %r is not skippable: the owner decides" % key
            out.append(kl.issue("state.legacy_embedded_skip", "approval %r is an embedded skip (legacy); %s"
                                % (key, fix), severity="warning", file=file, path="$.approvals.%s" % key))

    # skipped and approved at the same time
    for ph in sorted(skipped):
        pdef = phase_def(ph)
        ap = approvals.get(pdef["approval"]) if pdef and pdef["approval"] else None
        if isinstance(ap, dict) and ap.get("approved") is True:
            out.append(kl.issue("state.skipped_and_approved", "phase %r is both skipped and approved" % ph,
                                severity="warning", file=file, path="$.skipped.%s" % ph))

    # management legacy alias
    if data.get("management") == "none":
        out.append(kl.issue("state.legacy_management", "management 'none' is a legacy alias of 'markdown'; "
                            "run validate --fix", severity="warning", file=file, path="$.management",
                            expected="markdown", got="none"))

    # phase_history: order, exited_at >= entered_at, gaps
    hist = data.get("phase_history")
    entries = [e for e in hist if isinstance(e, dict) and "phase" in e] if isinstance(hist, list) else []
    prev = None
    for i, e in enumerate(hist if isinstance(hist, list) else []):
        if not isinstance(e, dict) or "phase" not in e:
            continue
        ent, ext = parse_dt(e.get("entered_at")), parse_dt(e.get("exited_at"))
        if ent and ext and ext < ent:
            out.append(kl.issue("state.history_order", "exited_at is before entered_at", severity="error",
                                file=file, path="$.phase_history[%d].exited_at" % i,
                                expected=">= %s" % e.get("entered_at"), got=e.get("exited_at")))
        if ent and prev and ent < prev:
            out.append(kl.issue("state.history_order", "entry is out of order (entered before the previous one)",
                                severity="error", file=file, path="$.phase_history[%d].entered_at" % i,
                                expected=">= %s" % prev.isoformat(), got=e.get("entered_at")))
        if ent:
            prev = ent
    if not isinstance(hist, list) or not hist:
        if idx > 0:
            out.append(kl.issue("state.history_missing", "no phase_history (legacy file)", severity=sev,
                                file=file, path="$.phase_history", expected="entries up to %r" % mapped))
    else:
        seen = {e.get("phase") for e in entries}
        seen |= {map_phase(e.get("to"))[0] for e in hist if _is_legacy_transition(e)}
        seen |= {map_phase(e.get("from"))[0] for e in hist if _is_legacy_transition(e)}
        for p in machine()["phases"][:idx + 1]:
            if p["id"] in skipped or p["id"] in seen:
                continue
            if p["skippable"] and approval_state(data, p["id"]) == "skipped":
                continue
            out.append(kl.issue("state.history_gap", "phase_history has no entry for %r, a phase this change "
                                "went through" % p["id"], severity=sev, file=file, path="$.phase_history",
                                expected=p["id"], got=None))
    return out


def semantic_project(data, strict, file):
    out = []
    if isinstance(data.get("management"), str) and data["management"] == "none":
        out.append(kl.issue("state.legacy_management", "management 'none' is a legacy alias of 'markdown'; "
                            "run validate --fix", severity="warning", file=file, path="$.management"))
    # safe_values (§3.1) joins here when karvey_lib/safe_values.py lands (E1.F7.T1).
    return out


def validate_data(data, kind, strict, file=None):
    """All issues (schema + semantic) of one parsed file."""
    if not isinstance(data, dict):
        return [kl.issue("schema.type", "the file is not a JSON object", file=file, path="$",
                         expected="object", got=type(data).__name__)]
    issues = validator(kind, file=file).validate(data, strict=strict)
    if kind == "spec":
        issues = _legacy_rewrite(issues, data, strict, file)
        issues += semantic_spec(data, strict, file)
    else:
        issues += semantic_project(data, strict, file)
    return issues


def check_schema_version(data, file):
    """exit 4 for a file declaring a higher schema_version than this tool knows (§2.7)."""
    v = data.get("schema_version") if isinstance(data, dict) else None
    if isinstance(v, int) and not isinstance(v, bool) and v > SCHEMA_VERSION:
        raise NotFound("%s declares schema_version %d; this tool knows %d: upgrade Karvey"
                       % (file, v, SCHEMA_VERSION))


def load(path):
    try:
        return atomicio.read_json(path)
    except atomicio.ReadError as exc:
        raise NotFound(str(exc))


# --------------------------------------------------------------------------- commands
def cmd_validate(args, root):
    strict_mode = schema_mode(root, args.strict)
    strict = strict_mode == "strict"
    if args.all:
        files = all_files(root)
    elif args.paths:
        files = [Path(p) if os.path.isabs(p) else Path(os.getcwd()) / p for p in args.paths]
    else:
        raise Usage("validate needs PATH… or --all")
    errors, warnings, report = [], [], []
    worst = kl.EXIT_OK
    for f in files:
        name = rel(root, f)
        entry = {"file": name, "kind": kind_of(f), "errors": 0, "warnings": 0}
        try:
            loaded = load(f)
            check_schema_version(loaded.data, name)
        except NotFound as exc:
            errors.append(kl.issue("state.unreadable", str(exc), file=name))
            entry["unreadable"] = True
            report.append(entry)
            worst = kl.EXIT_NOT_FOUND
            continue
        issues = validate_data(loaded.data, kind_of(f), strict, file=name)
        e = [i for i in issues if i["severity"] == "error"]
        w = [i for i in issues if i["severity"] == "warning"]
        entry["errors"], entry["warnings"] = len(e), len(w)
        errors += e
        warnings += w
        report.append(entry)
        if e and worst == kl.EXIT_OK:
            worst = kl.EXIT_FINDINGS
    result = {"mode": strict_mode, "files": report}
    lines = []
    for r in report:
        state = "unreadable" if r.get("unreadable") else ("OK" if not r["errors"] else "INVALID")
        lines.append("%-10s %s (%d errors, %d warnings)" % (state, r["file"], r["errors"], r["warnings"]))
    lines.append("mode: %s · %d files · %d errors · %d warnings" % (strict_mode, len(report), len(errors),
                                                                   len(warnings)))
    return worst, result, errors, warnings, "\n".join(lines)


COMMANDS = {"validate": cmd_validate}


def build_parser():
    top = argparse.ArgumentParser(add_help=False)
    top.add_argument("--root", help="Karvey project root (default: walk up from the cwd)")
    top.add_argument("--json", action="store_true", help="print one JSON envelope")
    # the same options after the command; SUPPRESS keeps a value given before the command
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="print one JSON envelope")
    p = argparse.ArgumentParser(prog="karvey-state.py", description="Karvey state tool (architecture §1.2)",
                                parents=[top])
    sub = p.add_subparsers(dest="command")
    v = sub.add_parser("validate", parents=[common], help="validate spec.json / project.json")
    v.add_argument("paths", nargs="*", metavar="PATH")
    v.add_argument("--all", action="store_true", help="every spec.json and project.json under docs/spec")
    v.add_argument("--strict", action="store_true", help="strict mode (overrides project.json:schema_mode)")
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
    if not args.command:
        parser.print_help(sys.stderr)
        return kl.EXIT_USAGE
    try:
        root = resolve_root(args)
        code, result, errors, warnings, human = COMMANDS[args.command](args, root)
    except Usage as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", str(exc))]), args.json)
    except Refused as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, result=exc.result,
                                   errors=[kl.issue(exc.code, str(exc))]), args.json, human=None)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("state.not_found", str(exc))]),
                       args.json)
    except (atomicio.LockBusy, atomicio.CASConflict) as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, errors=[kl.issue("state.concurrent", str(exc))]),
                       args.json)
    except Exception as exc:  # pragma: no cover - last resort, exit 5
        return kl.emit(kl.envelope(TOOL, kl.EXIT_INTERNAL,
                                   errors=[kl.issue("internal", "%s: %s" % (type(exc).__name__, exc))]),
                       args.json)
    return kl.emit(kl.envelope(TOOL, code, result=result, errors=errors, warnings=warnings), args.json,
                   human=human)


if __name__ == "__main__":
    sys.exit(main())
