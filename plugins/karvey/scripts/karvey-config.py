#!/usr/bin/env python3
"""karvey-config.py — the Karvey settings resolver and safe values (architecture §1.8).

Turns REQ-W1-080..099 into code: one resolution order for the tracker settings, one "is there
a tracker" test, shell-safe values for commands built by skills. Python >= 3.9, standard
library only. Destinations and tracker settings come only from ``project.json`` / ``spec.json``
(REQ-W1-099): no other file of the repo or of the user is read.

Shared CLI contract (§1.1): ``--root DIR`` (else walk up from the cwd to the git top level),
``--json`` (one envelope on stdout), exit codes 0 ok · 1 findings · 2 usage · 3 refused ·
4 not found / unreadable / corrupt · 5 internal.

Commands:
  resolve management [--change ID]   spec.json override, then project.json:management (REQ-W1-086)
  resolve notifications              {channel, target, via, events, detail}, defaults applied
  get <dotted.key> [--change ID] [--shell]
                                     --shell: the validated value (§3.1) or exit 3 naming the
                                     key and the rule; skills do VALUE=$(… get K --shell) || stop
  propose-settings [--from-legacy]   prints a management / notifications snippet; never writes

Settings missing from the working copy are looked up on ``origin/{integration}`` (local ref,
no fetch) before being declared missing (REQ-W1-083).
"""
import argparse
import copy
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import atomicio, project as pj, safe_values as sv  # noqa: E402

TOOL = "karvey-config"

TOOLS = ("clickup", "jira", "linear", "azure-boards", "github-projects", "spreadsheet", "markdown", "other")
LEGACY_TOOLS = {"none": "markdown"}
NO_TRACKER = frozenset({"markdown", "none"})
CHANNELS = ("google-chat", "slack", "teams", "email", "webhook", "none")
LEGACY_CHANNELS = {"google_chat": "google-chat"}
VIAS = ("mcp", "cli", "webhook", "api", "")
MGMT_VIAS = ("mcp", "cli", "api", "file")
EVENTS = ("qa", "deploy", "incident")
DETAILS = ("counts", "full")
DEFAULT_DETAIL = "counts"
OVERRIDE_FIELDS = ("tool", "location", "statuses", "sprints")
MARKDOWN_LOCATION = "docs/spec/changes/{change-id}/PLAN.md"


class Refused(Exception):
    def __init__(self, message, code="config.refused", result=None):
        super().__init__(message)
        self.code = code
        self.result = result or {}


class NotFound(Exception):
    def __init__(self, message, code="config.not_found"):
        super().__init__(message)
        self.code = code


class Usage(Exception):
    pass


# --------------------------------------------------------------------------- loading
class Settings:
    """``project.json`` of the working copy plus the ``origin/{integration}`` fallback."""

    def __init__(self, root):
        self.root = Path(root)
        data, err = pj.load_project_json(self.root)
        if data is None and err != "missing":
            raise NotFound("project.json unreadable: %s" % err)
        self.project = data or {}
        self._remote = None
        self._remote_done = False
        self.remote_name = None

    def remote(self):
        """``project.json`` on ``origin/{integration}`` or None (REQ-W1-083)."""
        if not self._remote_done:
            self._remote_done = True
            _, integ, _ = pj.branch_flow(self.project)
            integ = integ or "main"
            try:
                sv.check_branch(integ, key="branch_flow.integration", use_git=False)
            except sv.UnsafeValue:
                return None
            data, status = pj.read_reviewed_project_json(self.root, production=integ)
            if status == "ok":
                self._remote = data
                self.remote_name = "origin/%s" % integ
        return self._remote

    def block(self, key):
        """``(value, source)`` for a top-level key: working copy first, then origin/{integration}."""
        if key in self.project:
            return self.project[key], "project"
        remote = self.remote()
        if remote is not None and key in remote:
            return remote[key], self.remote_name
        return None, None

    def legacy_backlog_list_id(self):
        for data in (self.project, self.remote() or {}):
            cu = data.get("clickup")
            if isinstance(cu, dict) and cu.get("backlog_list_id") not in (None, ""):
                return str(cu["backlog_list_id"])
        return None


def load_change_spec(root, change):
    if not isinstance(change, str) or not change or "/" in change or "\\" in change or change.startswith("."):
        raise Usage("invalid change id %r" % (change,))
    p = Path(root) / pj.CHANGES_DIR / change / "spec.json"
    if not p.is_file():
        raise NotFound("change %s: spec.json not found" % change)
    try:
        data = atomicio.read_json(p).data
    except atomicio.ReadError as exc:
        raise NotFound(str(exc))
    if not isinstance(data, dict):
        raise NotFound("change %s: spec.json is not an object" % change)
    return data


# --------------------------------------------------------------------------- management
def _normalise_management(value, where, warnings):
    """A ``management`` value (string or object) as a dict with a canonical ``tool``."""
    if value is None:
        return None
    if isinstance(value, str):
        warnings.append(kl.issue("config.legacy_management", "%s: management is a legacy string; "
                                 "run karvey-state.py validate --fix" % where, severity="warning",
                                 path="$.management"))
        value = {"tool": value}
    if not isinstance(value, dict):
        raise Refused("%s: management %r is neither a tool name nor an object" % (where, value),
                      code="config.invalid_management")
    out = copy.deepcopy(value)
    tool = out.get("tool")
    if tool is not None:
        if tool in LEGACY_TOOLS:
            warnings.append(kl.issue("config.legacy_alias", "%s: management tool %r is a legacy alias of %r"
                                     % (where, tool, LEGACY_TOOLS[tool]), severity="warning",
                                     path="$.management.tool"))
            out["tool"] = LEGACY_TOOLS[tool]
        elif tool not in TOOLS:
            raise Refused("%s: management.tool %r is not one of %s" % (where, tool, "|".join(TOOLS)),
                          code="config.invalid_management")
    return out


def _statuses_report(statuses):
    """``(missing, unsupported)`` for a status map (flat or by_level / by_list)."""
    if not isinstance(statuses, dict) or not statuses:
        return ["statuses"], []
    maps = []
    if "by_level" in statuses or "by_list" in statuses:
        for group in ("by_level", "by_list"):
            for name, m in (statuses.get(group) or {}).items():
                maps.append(("statuses.%s.%s." % (group, name), m))
    else:
        maps.append(("statuses.", statuses))
    missing, unsupported = [], []
    for prefix, m in maps:
        if not isinstance(m, dict):
            missing.append(prefix.rstrip("."))
            continue
        for state in sv.LOGICAL_STATES:
            if state not in m:
                missing.append(prefix + state)
            elif m[state] is None:
                unsupported.append(prefix + state)
    return missing, unsupported


def resolve_management(settings, change=None):
    """REQ-W1-086 / 087 / 088: the spec override first, then ``project.json:management``."""
    warnings = []
    proj_raw, proj_src = settings.block("management")
    proj = _normalise_management(proj_raw, "project.json" if proj_src == "project" else str(proj_src), warnings)
    override = None
    if change:
        spec = load_change_spec(settings.root, change)
        override = _normalise_management(spec.get("management"), "spec.json(%s)" % change, warnings)
    sources = {}
    res = {}
    # A different tool in the override means the project's location/statuses belong to another tool.
    inherit = override is None or override.get("tool") in (None, (proj or {}).get("tool"))
    for field in OVERRIDE_FIELDS:
        if override is not None and override.get(field) is not None:
            res[field], sources[field] = override[field], "spec"
        elif proj is not None and inherit and proj.get(field) is not None:
            res[field], sources[field] = proj[field], proj_src
        else:
            res[field] = None
    if res["tool"] is None:
        res["tool"], sources["tool"] = "markdown", "default"
        if proj is None:
            warnings.append(kl.issue("config.no_management", "no management block in project.json "
                                     "(nor on origin/{integration}); using markdown", severity="warning"))
    if (res["tool"] == "clickup" and res["location"] is None and inherit):
        blid = settings.legacy_backlog_list_id()
        if blid:
            res["location"], sources["location"] = blid, "legacy:clickup.backlog_list_id"
            warnings.append(kl.issue("config.legacy_backlog_list_id", "location taken from the legacy "
                                     "clickup.backlog_list_id; run karvey-state.py validate --fix",
                                     severity="warning", path="$.clickup.backlog_list_id"))
    for extra in ("hierarchy", "via"):
        src = override if override is not None and override.get(extra) is not None else (proj if inherit else None)
        res[extra] = (src or {}).get(extra)
    external = res["tool"] not in NO_TRACKER
    missing, unsupported = [], []
    if external:
        if res["location"] in (None, ""):
            missing.append("location")
        m, unsupported = _statuses_report(res["statuses"])
        missing.extend(m)
    elif isinstance(res["statuses"], dict):
        _, unsupported = _statuses_report(res["statuses"])
    for field, value in (("location", res["location"]), ("sprints", res["sprints"])):
        if value in (None, ""):
            continue
        try:
            (sv.check_location if field == "location" else sv.check_sprints)(res["tool"], value,
                                                                              key="management." + field)
        except sv.UnsafeValue as exc:
            warnings.append(kl.issue("config.unsafe_value", str(exc), severity="warning",
                                     path="$.management." + field))
    srcs = sorted(set(sources.values()))
    res.update({"source": "+".join(srcs) if srcs else "default", "sources": sources,
                "external": external, "missing": missing, "unsupported": unsupported})
    return res, warnings


# --------------------------------------------------------------------------- notifications
def resolve_notifications(settings):
    """``{channel, target, via, events, detail, deferred, source}`` with defaults (REQ-W1-098)."""
    warnings = []
    raw, src = settings.block("notifications")
    res = {"channel": "none", "target": "", "via": "", "events": [], "detail": DEFAULT_DETAIL,
           "deferred": False, "source": src or "default", "target_error": None}
    if raw is None:
        return res, warnings
    if not isinstance(raw, dict):
        raise Refused("notifications must be an object, got %r" % (raw,), code="config.invalid_notifications")
    ch = raw.get("channel", "none")
    if ch in LEGACY_CHANNELS:
        warnings.append(kl.issue("config.legacy_alias", "notifications.channel %r is a legacy alias of %r"
                                 % (ch, LEGACY_CHANNELS[ch]), severity="warning", path="$.notifications.channel"))
        ch = LEGACY_CHANNELS[ch]
    if ch not in CHANNELS:
        raise Refused("notifications.channel %r is not one of %s" % (ch, "|".join(CHANNELS)),
                      code="config.invalid_notifications")
    res["channel"] = ch
    target = raw.get("target", "")
    res["target"] = "" if target is None else target
    via = raw.get("via", "")
    if via not in VIAS:
        warnings.append(kl.issue("config.invalid_value", "notifications.via %r is not one of %s; ignored"
                                 % (via, "|".join(v or '""' for v in VIAS)), severity="warning"))
        via = ""
    res["via"] = via
    events = raw.get("events", [])
    if not isinstance(events, list):
        events = []
    bad = [e for e in events if e not in EVENTS]
    if bad:
        warnings.append(kl.issue("config.invalid_value", "notifications.events %r ignored" % bad, severity="warning"))
    res["events"] = [e for e in events if e in EVENTS]
    detail = raw.get("detail", DEFAULT_DETAIL)
    if detail not in DETAILS:
        warnings.append(kl.issue("config.invalid_value", "notifications.detail %r is not counts|full; "
                                 "using counts (REQ-W1-098)" % (detail,), severity="warning",
                                 path="$.notifications.detail"))
        detail = DEFAULT_DETAIL
    res["detail"] = detail
    res["deferred"] = raw.get("deferred") is True
    try:
        sv.check_target(ch, res["target"])
    except sv.UnsafeValue as exc:
        res["target_error"] = exc.rule
        warnings.append(kl.issue("config.unsafe_value", str(exc), severity="warning", path="$.notifications.target"))
    return res, warnings


# --------------------------------------------------------------------------- get --shell
BRANCH_KEYS = {"branch_flow.integration", "branch_flow.production"}


def _dig(obj, parts):
    for p in parts:
        if not isinstance(obj, dict) or p not in obj:
            return None, False
        obj = obj[p]
    return obj, True


def get_value(settings, key, change=None):
    """``(value, kind, checker)`` for a whitelisted key; ``checker(value)`` validates it."""
    parts = key.split(".")
    if parts[0] == "management" and len(parts) >= 2:
        mg, _ = resolve_management(settings, change)
        tool = mg["tool"]
        if key == "management.tool":
            return tool, "enum", lambda v: sv.check_enum(v, TOOLS, key)
        if key == "management.location":
            return mg["location"], "location:%s" % tool, lambda v: sv.check_location(tool, v, key=key)
        if key == "management.sprints":
            return mg["sprints"], "sprints:%s" % tool, lambda v: sv.check_sprints(tool, v, key=key)
        if key == "management.via":
            return mg["via"], "enum", lambda v: sv.check_enum(v, MGMT_VIAS, key)
        if parts[1] == "statuses" and len(parts) in (3, 5) and parts[-1] in sv.LOGICAL_STATES:
            if len(parts) == 5 and parts[2] not in ("by_level", "by_list"):
                raise Refused("%s: no safe kind for this key" % key, code="config.no_safe_kind")
            value, found = _dig(mg["statuses"], parts[2:])
            if found and value is None:
                raise Refused("%s: null = the tracker cannot represent this state (REQ-W1-082); keep the "
                              "tracker status and record it in PLAN.md" % key, code="config.unsupported_state")
            return (value if found else None), "status", lambda v: sv.check_status(v, key=key)
    elif parts[0] == "notifications" and len(parts) == 2:
        nt, _ = resolve_notifications(settings)
        field = parts[1]
        if field == "target":
            ch = nt["channel"]
            return nt["target"], "target:%s" % ch, lambda v: sv.check_target(ch, v, key=key)
        enums = {"channel": CHANNELS, "via": VIAS, "detail": DETAILS}
        if field in enums:
            return nt[field], "enum", lambda v, a=enums[field]: sv.check_enum(v, a, key)
    elif key in BRANCH_KEYS or key == "branch_flow.feature_prefix":
        bf, _ = settings.block("branch_flow")
        value = bf.get(parts[1]) if isinstance(bf, dict) else None
        if key == "branch_flow.feature_prefix":
            return value, "ref-prefix", lambda v: sv.check_ref_prefix(v, key=key)
        return value, "branch", lambda v: sv.check_branch(v, key=key)
    raise Refused("%s: no safe kind for this key; it may not be used in a command (§3.1)" % key,
                  code="config.no_safe_kind")


# --------------------------------------------------------------------------- propose-settings
def propose_settings(settings, from_legacy=False):
    """A ``management`` / ``notifications`` snippet (§7.2). Never writes."""
    notes = []
    raw, _ = settings.block("management")
    if isinstance(raw, str):
        tool = LEGACY_TOOLS.get(raw, raw)
        mg = {"tool": tool}
        notes.append("management: legacy string %r → object" % raw)
    elif isinstance(raw, dict):
        mg = copy.deepcopy(raw)
        tool = LEGACY_TOOLS.get(mg.get("tool"), mg.get("tool") or "markdown")
        mg["tool"] = tool
    else:
        tool, mg = "markdown", {"tool": "markdown"}
        notes.append("management: absent → markdown")
    if tool not in TOOLS:
        raise Refused("management.tool %r is not one of %s" % (tool, "|".join(TOOLS)),
                      code="config.invalid_management")
    if not mg.get("location"):
        blid = settings.legacy_backlog_list_id()
        if tool == "clickup" and blid:
            mg["location"] = blid
            notes.append("clickup.backlog_list_id → management.location")
        elif tool == "markdown":
            mg["location"] = MARKDOWN_LOCATION
        else:
            mg["location"] = "<%s location>" % tool
            notes.append("management.location: placeholder, ask the human")
    if tool not in NO_TRACKER and "statuses" not in mg:
        notes.append("statuses left absent: the missing-map clause resolves them with the human (REQ-W1-080)")
    nraw, _ = settings.block("notifications")
    if isinstance(nraw, dict):
        nt = copy.deepcopy(nraw)
    else:
        nt = {"channel": "none", "target": "", "via": "", "events": []}
        notes.append("notifications: absent → channel none (set it with /karvey:karvey-init --settings)")
    if nt.get("channel") in LEGACY_CHANNELS:
        nt["channel"] = LEGACY_CHANNELS[nt["channel"]]
    snippet = {"management": mg, "notifications": nt}
    return {"snippet": snippet, "notes": notes, "from_legacy": bool(from_legacy), "written": False}


# --------------------------------------------------------------------------- commands
def cmd_resolve(args, root):
    settings = Settings(root)
    if args.what == "management":
        res, warnings = resolve_management(settings, args.change)
        human = json.dumps({k: res[k] for k in ("tool", "location", "statuses", "sprints", "source",
                                                "external", "missing")}, ensure_ascii=False)
    else:
        if args.change:
            raise Usage("--change applies to 'resolve management' only")
        res, warnings = resolve_notifications(settings)
        human = json.dumps({k: res[k] for k in ("channel", "target", "via", "events", "detail")},
                           ensure_ascii=False)
    return kl.EXIT_OK, res, [], warnings, human


def cmd_get(args, root):
    settings = Settings(root)
    value, kind, checker = get_value(settings, args.key, args.change)
    if value is None:
        raise NotFound("%s: not set" % args.key, code="config.not_set")
    if args.shell:
        try:
            checker(value)
        except sv.UnsafeValue as exc:
            raise Refused(str(exc), code="config.unsafe_value",
                          result={"key": args.key, "kind": exc.kind, "rule": exc.rule})
        human = value
    else:
        human = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return kl.EXIT_OK, {"key": args.key, "kind": kind, "value": value}, [], [], human


def cmd_propose(args, root):
    res = propose_settings(Settings(root), args.from_legacy)
    human = json.dumps(res["snippet"], indent=2, ensure_ascii=False)
    if res["notes"]:
        human += "\n" + "\n".join("# " + n for n in res["notes"])
    human += "\n# printed only: nothing was written. Apply it on a docs branch (REQ-W1-083)."
    return kl.EXIT_OK, res, [], [], human


COMMANDS = {"resolve": cmd_resolve, "get": cmd_get, "propose-settings": cmd_propose}


def resolve_root(args):
    root = pj.find_root(root=getattr(args, "root", None)) if getattr(args, "root", None) else pj.find_root()
    if root is None:
        raise NotFound("no Karvey project here (docs/spec/project.json or docs/spec/changes/)",
                       code="config.no_project")
    return root


def build_parser():
    top = argparse.ArgumentParser(add_help=False)
    top.add_argument("--root", help="Karvey project root (default: walk up from the cwd)")
    top.add_argument("--json", action="store_true", help="print one JSON envelope")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="print one JSON envelope")
    p = argparse.ArgumentParser(prog="karvey-config.py", description="Karvey settings resolver (architecture §1.8)",
                                parents=[top])
    sub = p.add_subparsers(dest="command")
    r = sub.add_parser("resolve", parents=[common], help="resolve management or notifications")
    r.add_argument("what", choices=["management", "notifications"])
    r.add_argument("--change", help="change id whose spec.json override applies (management)")
    g = sub.add_parser("get", parents=[common], help="one setting; --shell validates it for a command")
    g.add_argument("key", help="dotted key, e.g. management.location")
    g.add_argument("--change", help="change id whose spec.json override applies")
    g.add_argument("--shell", action="store_true", help="validate (§3.1) and print the bare value, or exit 3")
    ps = sub.add_parser("propose-settings", parents=[common], help="print a settings snippet; never writes")
    ps.add_argument("--from-legacy", action="store_true", help="build it from the legacy shapes")
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
                                   errors=[kl.issue(exc.code, str(exc))]), args.json)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue(exc.code, str(exc))]), args.json)
    except (atomicio.LockBusy, atomicio.CASConflict) as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, errors=[kl.issue("config.concurrent", str(exc))]),
                       args.json)
    except Exception as exc:  # pragma: no cover - last resort, exit 5
        return kl.emit(kl.envelope(TOOL, kl.EXIT_INTERNAL,
                                   errors=[kl.issue("internal", "%s: %s" % (type(exc).__name__, exc))]),
                       args.json)
    return kl.emit(kl.envelope(TOOL, code, result=result, errors=errors, warnings=warnings), args.json,
                   human=human)


if __name__ == "__main__":
    sys.exit(main())
