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
  notify-check [--confirm]           exit 0 = destination unchanged since the last confirmed
                                     send; exit 10 = changed (or never confirmed): show it to the
                                     human; --confirm records it only when the human typed
                                     "confirmo notificacion <code>" (the approval hook records
                                     it for this project and destination, TTL; D-16), else 10
  outbox add <change> --op OP [--args JSON] [--key K] [--parent-key P] [--error MSG]
  outbox list <change>               pending tracker operations (REQ-W1-090); a child whose
                                     parent is itself pending is ``blocked_by`` it, never sent
  outbox done <change> <id> [--failed MSG]   applied → removed; --failed keeps it, attempts+1

Exit codes: the shared ones plus ``10`` = confirmation required (notify-check).

Settings missing from the working copy are looked up on ``origin/{integration}`` (local ref,
no fetch) before being declared missing (REQ-W1-083).
"""
import argparse
import copy
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import approval, atomicio, outbox as obx, project as pj, safe_values as sv  # noqa: E402

TOOL = "karvey-config"

TOOLS = ("clickup", "jira", "linear", "azure-boards", "github-projects", "spreadsheet", "markdown", "other")
LEGACY_TOOLS = {"none": "markdown"}
NO_TRACKER = frozenset({"markdown", "none"})
CHANNELS = ("google-chat", "slack", "teams", "email", "webhook", "none")
LEGACY_CHANNELS = pj.LEGACY_CHANNELS
VIAS = ("mcp", "cli", "webhook", "api", "")
MGMT_VIAS = ("mcp", "cli", "api", "file")
EVENTS = ("qa", "deploy", "incident", "approval_requested", "awaiting_human", "blocked")
# "your turn" events (wave3 §1.15, REQ-W3-026): who must act, and what is expected of them
EVENT_ACTOR = {"approval_requested": "approver", "awaiting_human": "executor", "blocked": "executor"}
EVENT_EXPECTED = {"approval_requested": "approve or request changes at the %s gate",
                  "awaiting_human": "run the step %s and report it done",
                  "blocked": "unblock %s"}
DETAILS = ("counts", "full")
DEFAULT_DETAIL = "counts"
OVERRIDE_FIELDS = ("tool", "location", "statuses", "sprints")
MARKDOWN_LOCATION = "docs/spec/changes/{change-id}/PLAN.md"
EXIT_CONFIRM = 10  # notify-check: the destination changed, the human must confirm it
NOTIFY_FILE = "notify-last.json"
NOTIFY_FIELDS = ("channel", "target", "via", "events", "detail")
OUTBOX_FILE = obx.FILE
OP_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
ITEM_KEY_MAX = 200


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


def resolve_event(settings, notif, event, change=None, item=None, verdict=None, run_id=None, at=None):
    """The destination and payload of a "your turn" event (REQ-W3-026): the stakeholder whose role acts
    (``approver`` / ``executor``; whoever unblocks is the executor), else the team destination with ``no approver
    declared`` / ``no executor declared``. A ``blocked`` raised by a judge carries the verdict line."""
    if event not in EVENT_ACTOR:
        raise Usage("--event must be one of %s" % ", ".join(EVENT_ACTOR))
    spec = None
    if change:
        sp_ = Path(settings.root) / pj.CHANGES_DIR / change / "spec.json"
        try:
            spec = json.loads(sp_.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            spec = None
    raw, _ = settings.block("stakeholders")
    stake = pj.stakeholders({"stakeholders": raw} if isinstance(raw, dict) else {}, spec)
    role = EVENT_ACTOR[event]
    who = stake.get(role)
    dest = who.get("destination") if isinstance(who, dict) and isinstance(who.get("destination"), dict) else None
    note = None
    if who and dest and dest.get("channel") not in (None, "none"):
        destination = {"channel": dest["channel"], "target": dest.get("target", "")}
        source = "stakeholder:%s" % role
    else:
        destination = {"channel": notif["channel"], "target": notif["target"]}
        source = "team"
        note = "no %s declared" % role
    payload = {"event": event, "change": change, "item": item, "expected": EVENT_EXPECTED[event] % (item or "the"),
               "to": (who or {}).get("name") or role, "run_id": run_id, "at": at}
    if note:
        payload["note"] = note
    if event == "blocked" and verdict:
        payload["verdict"] = verdict
    return {"event": event, "enabled": event in notif["events"], "actor_role": role, "destination": destination,
            "source": source, "note": note, "payload": payload}


# --------------------------------------------------------------------------- sent-log (wave3 §1.15, REQ-W3-027)
SENT_LOG = "notifications.jsonl"


def _h(*parts):
    return hashlib.sha256("|".join("" if p is None else str(p) for p in parts).encode("utf-8")).hexdigest()


def sent_log_path(root, change):
    if not isinstance(change, str) or not re.match(r"^[a-z0-9][a-z0-9._-]*$", change):
        raise Usage("invalid change id %r" % (change,))
    d = Path(root) / pj.CHANGES_DIR / change
    if not d.is_dir():
        raise NotFound("change %r not found" % change, code="config.no_change")
    return d / SENT_LOG


def read_sent(path):
    out = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
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


def notify_status(log, event, change, item=None, state=None, version=None, env=None, qa_every_run=False):
    """``(status, key, scope)``: ``new`` or ``sent``. ``deploy`` once per version and environment; ``qa`` on the
    first run and on a verdict change (every run with ``qa_every_run``); any other event once per state change of
    its item."""
    scope = _h(event, change, item)
    if event == "deploy":
        key = _h(event, change, item, None, version, env)
        return ("sent" if any(r.get("key") == key for r in log) else "new"), key, scope
    key = _h(event, change, item, state, version, env)
    if event == "qa" and qa_every_run:
        return "new", key, scope
    last = [r for r in log if r.get("scope") == scope]
    if last and last[-1].get("state_key") == _h(state):
        return "sent", key, scope
    return "new", key, scope


def cmd_notify_sent(args, root):
    path = sent_log_path(root, args.change)
    settings = Settings(root)
    notif, _ = resolve_notifications(settings)
    raw, _ = settings.block("notifications")
    every = isinstance(raw, dict) and raw.get("qa_every_run") is True
    log = read_sent(path)
    status, key, scope = notify_status(log, args.event, args.change, args.item, args.state, args.version, args.env,
                                       every)
    at = datetime.now().astimezone().isoformat(timespec="seconds")
    recorded = False
    if args.record and status == "new":
        rec = {"event": args.event, "key": key, "scope": scope, "state_key": _h(args.state), "at": at,
               "run_id": args.run_id}
        line = json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n"
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
        recorded = True
    res = {"status": status, "key": key, "event": args.event, "run_id": args.run_id, "at": at, "recorded": recorded}
    human = "%s: %s%s" % (args.event, status, " (recorded)" if recorded else "")
    return kl.EXIT_OK, res, [], [], human


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
    proposed = pj.legacy_status_flow(mg)
    if proposed is not None:
        mg["statuses"] = proposed
        del mg["status_flow"]
        notes.append("management.status_flow → statuses (the map already in project.json; the human confirms "
                     "it by merging the snippet, F-38)")
    elif isinstance(mg.get("status_flow"), dict) and "statuses" not in mg:
        notes.append("management.status_flow kept as is: its keys are not the logical states "
                     "(todo | in_progress | review | done | blocked)")
    if tool not in NO_TRACKER and "statuses" not in mg:
        notes.append("statuses left absent: the missing-map clause resolves them with the human (REQ-W1-080)")
    nraw, _ = settings.block("notifications")
    if isinstance(nraw, dict):
        nt = copy.deepcopy(nraw)
    else:
        nt = {"channel": "none", "target": "", "via": "", "events": []}
        notes.append("notifications: absent → channel none (set it with /karvey:karvey-init --settings)")
    if nt.get("channel") in LEGACY_CHANNELS:
        notes.append("notifications.channel %r → %r" % (nt["channel"], LEGACY_CHANNELS[nt["channel"]]))
        nt["channel"] = LEGACY_CHANNELS[nt["channel"]]
    snippet = {"management": mg, "notifications": nt}
    return {"snippet": snippet, "notes": notes, "from_legacy": bool(from_legacy), "written": False}


# --------------------------------------------------------------------------- notify-check
def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def destination(nt):
    """The part of the resolved notifications block that decides where a notice goes."""
    return {k: nt[k] for k in NOTIFY_FIELDS}


def destination_hash(nt):
    blob = json.dumps(destination(nt), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _root_key(root):
    """The record key: the root relative to the git top level, so every worktree shares it."""
    return approval.project_key(root)


def notify_check(root, confirm=False):
    """``(exit_code, result)``: 0 unchanged / recorded, 10 confirmation required (REQ-W1-097)."""
    nt, warnings = resolve_notifications(Settings(root))
    dest = destination(nt)
    if nt["target_error"] is not None:
        raise Refused("notifications.target refused: %s" % nt["target_error"], code="config.unsafe_value",
                      result={"key": "notifications.target", "rule": nt["target_error"], "destination": dest})
    h = destination_hash(nt)
    path = pj.state_dir(root) / NOTIFY_FILE
    try:
        loaded = atomicio.read_json(path)
        record = loaded.data if isinstance(loaded.data, dict) else {}
        sha = loaded.sha256
    except atomicio.ReadError:
        record, sha = {}, atomicio.file_sha256(path)
    entries = record.get("entries") if isinstance(record.get("entries"), dict) else {}
    key = _root_key(root)
    last = entries.get(key) if isinstance(entries.get(key), dict) else None
    result = {"destination": dest, "hash": h, "send": nt["channel"] != "none",
              "last": ({"hash": last.get("hash"), "destination": last.get("destination"),
                        "confirmed_at": last.get("confirmed_at")} if last else None),
              "changed": last is None or last.get("hash") != h, "recorded": False,
              "code": approval.notify_code(h), "confirm_phrase": approval.notify_phrase(h),
              "human_confirmation": None}
    if not result["send"]:
        return kl.EXIT_OK, result, warnings  # channel none: nothing is sent, nothing to confirm
    if not result["changed"]:
        return kl.EXIT_OK, result, warnings  # already the confirmed destination: nothing to record
    if confirm:
        # D-16 / F-15: only a confirmation the human typed (recorded by the UserPromptSubmit hook for
        # this project and exactly this destination, within its TTL) lets the destination be recorded
        ok, why = approval.check_notify_marker(root, h)
        result["human_confirmation"] = why
        if not ok:
            return EXIT_CONFIRM, result, warnings
        entries[key] = {"hash": h, "destination": dest, "confirmed_at": now_iso()}
        record = {"schema_version": 1, "entries": entries}
        atomicio.write_json(path, record, expected_sha256=sha, mode=0o600)
        approval.consume_notify_marker(root)
        result.update({"recorded": True, "changed": False})
        return kl.EXIT_OK, result, warnings
    return EXIT_CONFIRM, result, warnings


def _dest_line(dest):
    return "%s → %s (via %s, events %s, detail %s)" % (
        dest["channel"], dest["target"] or '""', dest["via"] or '""', ",".join(dest["events"]) or "none",
        dest["detail"])


# --------------------------------------------------------------------------- outbox
def outbox_path(root, change):
    if not isinstance(change, str) or not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$", change):
        raise Usage("invalid change id %r" % (change,))
    d = Path(root) / pj.CHANGES_DIR / change
    if not d.is_dir():
        raise NotFound("change %s not found" % change)
    return d / OUTBOX_FILE


def read_outbox(path):
    """``(entries, sha256)``; a corrupt line is exit 4 (never silently dropped)."""
    if not path.is_file():
        return [], None
    raw = path.read_bytes()
    entries = []
    for n, line in enumerate(raw.decode("utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            raise NotFound("%s:%d: invalid JSON line" % (path, n), code="config.outbox_corrupt")
        if not isinstance(e, dict) or not isinstance(e.get("id"), str):
            raise NotFound("%s:%d: not an outbox entry" % (path, n), code="config.outbox_corrupt")
        entries.append(e)
    return entries, atomicio.sha256_bytes(raw)


def write_outbox(path, entries, sha):
    text = "".join(json.dumps(e, ensure_ascii=False, sort_keys=False) + "\n" for e in entries)
    atomicio.write_text_atomic(path, text, expected_sha256=sha)


def _item_key(value, name):
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > ITEM_KEY_MAX \
            or re.search(r"[\x00-\x1f\x7f]", value):
        raise Usage("%s must be a one-line natural key of at most %d characters" % (name, ITEM_KEY_MAX))
    return value


annotate = obx.annotate  # the one ready/blocked rule, shared with karvey-context.py


def outbox_add(root, change, op, args_json=None, key=None, parent_key=None, error=None):
    path = outbox_path(root, change)
    if not isinstance(op, str) or not OP_PATTERN.match(op):
        raise Usage("--op must match %s (e.g. create_task, set_status)" % OP_PATTERN.pattern)
    try:
        op_args = json.loads(args_json) if args_json else {}
    except ValueError as exc:
        raise Usage("--args is not JSON: %s" % exc)
    if not isinstance(op_args, dict):
        raise Usage("--args must be a JSON object")
    key = _item_key(key, "--key")
    parent_key = _item_key(parent_key, "--parent-key")
    entries, sha = read_outbox(path)
    # a random id, so an id is never reused after its entry is removed (blocked_by stays exact)
    entry = {"id": "ob-" + uuid.uuid4().hex[:12], "op": op, "args": op_args, "key": key, "parent_key": parent_key,
             "created_at": now_iso(), "attempts": 1 if error else 0, "last_error": error, "blocked_by": None}
    if parent_key:
        parent = next((e for e in entries if e.get("key") == parent_key), None)
        if parent is not None:
            entry["blocked_by"] = parent["id"]  # REQ-W1-090: never created under a missing parent
    entries.append(entry)
    write_outbox(path, entries, sha)
    return annotate(entries)[-1]


def outbox_done(root, change, entry_id, failed=None):
    path = outbox_path(root, change)
    entries, sha = read_outbox(path)
    ann = {e["id"]: e for e in annotate(entries)}
    if entry_id not in ann:
        raise NotFound("outbox %s: no pending entry %s" % (change, entry_id), code="config.outbox_no_entry")
    if ann[entry_id]["state"] == "blocked":
        raise Refused("outbox %s: %s is blocked by pending %s; it is never sent before its parent"
                      % (change, entry_id, ann[entry_id]["blocked_by"]), code="config.outbox_blocked")
    if failed is not None:
        for e in entries:
            if e["id"] == entry_id:
                e["attempts"] = int(e.get("attempts") or 0) + 1
                e["last_error"] = str(failed)[:500]
        write_outbox(path, entries, sha)
        return {"id": entry_id, "removed": False, "attempts": ann[entry_id].get("attempts", 0) + 1}
    entries = [e for e in entries if e["id"] != entry_id]
    write_outbox(path, entries, sha)
    return {"id": entry_id, "removed": True, "unblocked": [e["id"] for e in entries if e.get("blocked_by") == entry_id]}


# --------------------------------------------------------------------------- commands
def cmd_notify_check(args, root):
    code, res, warnings = notify_check(root, args.confirm)
    dest = _dest_line(res["destination"])
    if res["recorded"]:
        human = "notify-check: destination confirmed and recorded: " + dest
    elif not res["send"]:
        human = "notify-check: channel none, nothing to send"
    elif code == EXIT_CONFIRM:
        prev = _dest_line(res["last"]["destination"]) if res["last"] and res["last"].get("destination") else "never confirmed"
        head = ("notify-check: NOT CONFIRMED — %s. The agent cannot confirm a destination; the human must.\n"
                % res["human_confirmation"]) if args.confirm else \
            "notify-check: CONFIRMATION REQUIRED — the destination changed since the last send.\n"
        human = (head + "  new:      %s\n  previous: %s\n"
                 "Show both to the human. To confirm, the human types in their own message:\n"
                 "  %s\n"
                 "(or: confirm notification %s); then run: karvey-config.py notify-check --confirm"
                 % (dest, prev, res["confirm_phrase"], res["code"]))
    else:
        human = "notify-check: unchanged: " + dest
    return code, res, [], warnings, human


def cmd_outbox(args, root):
    if args.action == "add":
        if args.entry_id:
            raise Usage("outbox add takes no entry id")
        if not args.op:
            raise Usage("outbox add requires --op")
        e = outbox_add(root, args.change, args.op, args.args, args.key, args.parent_key, args.error)
        human = "outbox %s: %s %s%s" % (args.change, e["id"], e["op"],
                                         (" (blocked by %s)" % e["blocked_by"]) if e["blocked_by"] else "")
        return kl.EXIT_OK, e, [], [], human
    if args.action == "list":
        entries, _ = read_outbox(outbox_path(root, args.change))
        ann = annotate(entries)
        res = {"change": args.change, "entries": ann, "pending": len(ann),
               "ready": [e["id"] for e in ann if e["state"] == "ready"],
               "blocked": [e["id"] for e in ann if e["state"] == "blocked"]}
        lines = ["outbox %s: %d pending" % (args.change, len(ann))]
        lines += ["  %s %-7s %s %s%s" % (e["id"], e["state"], e["op"], e.get("key") or "",
                                        (" ← %s" % e["blocked_by"]) if e["state"] == "blocked" else "")
                  for e in ann]
        return kl.EXIT_OK, res, [], [], "\n".join(lines)
    if not args.entry_id:
        raise Usage("outbox done requires an entry id")
    res = outbox_done(root, args.change, args.entry_id, args.failed)
    human = ("outbox %s: %s applied and removed" % (args.change, args.entry_id) if res["removed"]
             else "outbox %s: %s failed again (attempts %d)" % (args.change, args.entry_id, res["attempts"]))
    return kl.EXIT_OK, res, [], [], human


def cmd_resolve(args, root):
    settings = Settings(root)
    if args.what == "management":
        res, warnings = resolve_management(settings, args.change)
        human = json.dumps({k: res[k] for k in ("tool", "location", "statuses", "sprints", "source",
                                                "external", "missing")}, ensure_ascii=False)
    else:
        if args.change and not args.event:
            raise Usage("--change applies to 'resolve management' or to 'resolve notifications --event'")
        res, warnings = resolve_notifications(settings)
        if args.event:
            at = datetime.now().astimezone().isoformat(timespec="seconds")
            res["event"] = resolve_event(settings, res, args.event, args.change, args.item, args.verdict,
                                         args.run_id, at)
            human = json.dumps(res["event"], ensure_ascii=False, sort_keys=True)
            return kl.EXIT_OK, res, [], warnings, human
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


COMMANDS = {"resolve": cmd_resolve, "get": cmd_get, "propose-settings": cmd_propose,
            "notify-check": cmd_notify_check, "outbox": cmd_outbox, "notify-sent": cmd_notify_sent}


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
    r.add_argument("--change", help="change id whose spec.json override applies (management; notifications --event)")
    r.add_argument("--event", help="notifications: a 'your turn' event (approval_requested, awaiting_human, blocked)")
    r.add_argument("--item", help="--event: the gate or task the event is about")
    r.add_argument("--verdict", help="--event blocked: the judge's verdict line that raised it")
    r.add_argument("--run-id", dest="run_id", help="--event: the run or iteration id carried by the payload")
    g = sub.add_parser("get", parents=[common], help="one setting; --shell validates it for a command")
    g.add_argument("key", help="dotted key, e.g. management.location")
    g.add_argument("--change", help="change id whose spec.json override applies")
    g.add_argument("--shell", action="store_true", help="validate (§3.1) and print the bare value, or exit 3")
    ps = sub.add_parser("propose-settings", parents=[common], help="print a settings snippet; never writes")
    ps.add_argument("--from-legacy", action="store_true", help="build it from the legacy shapes")
    nc = sub.add_parser("notify-check", parents=[common],
                        help="exit 10 when the destination changed since the last confirmed send")
    nc.add_argument("--confirm", action="store_true",
                    help="record the destination; needs the human's typed confirmation (D-16)")
    ns = sub.add_parser("notify-sent", parents=[common],
                        help="new or sent: was this notification already sent (changes/{id}/notifications.jsonl)?")
    ns.add_argument("change")
    ns.add_argument("--event", required=True, choices=EVENTS)
    ns.add_argument("--item", help="the gate, task or phase the notification is about")
    ns.add_argument("--state", help="qa: the verdict; your-turn events: the state of the item")
    ns.add_argument("--version", help="deploy: the version")
    ns.add_argument("--env", help="deploy: the environment")
    ns.add_argument("--run-id", dest="run_id", help="the run or iteration id the payload carries")
    ns.add_argument("--record", action="store_true", help="record it as sent when new (after sending)")
    ob = sub.add_parser("outbox", parents=[common], help="pending tracker operations of a change")
    ob.add_argument("action", choices=["add", "list", "done"])
    ob.add_argument("change")
    ob.add_argument("entry_id", nargs="?", help="done: the entry id")
    ob.add_argument("--op", help="add: the tracker operation (create_task, set_status, …)")
    ob.add_argument("--args", help="add: the operation's arguments as a JSON object")
    ob.add_argument("--key", help="add: natural key of the item the operation creates or changes")
    ob.add_argument("--parent-key", help="add: natural key of the parent item")
    ob.add_argument("--error", help="add: the error of the failed attempt")
    ob.add_argument("--failed", metavar="ERROR", help="done: the retry failed again; keep it, attempts+1")
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
    if code == EXIT_CONFIRM:
        # not a shared exit code: build the envelope as "findings", then state the real code
        env = kl.envelope(TOOL, kl.EXIT_FINDINGS, result=result, errors=errors, warnings=warnings)
        env["exit"] = EXIT_CONFIRM
        return kl.emit(env, args.json, human=human)
    return kl.emit(kl.envelope(TOOL, code, result=result, errors=errors, warnings=warnings), args.json,
                   human=human)


if __name__ == "__main__":
    sys.exit(main())
