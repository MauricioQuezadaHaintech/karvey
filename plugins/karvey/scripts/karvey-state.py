#!/usr/bin/env python3
"""karvey-state.py — the Karvey state tool (architecture §1.2, wave1-hardening).

The one writer of ``spec.json:phase``, ``approvals``, ``skipped``, ``phase_history`` and
``updated_at``. Python >= 3.9, standard library only.

Shared CLI contract (§1.1): ``--root DIR`` (else walk up from the cwd to the git top level),
``--json`` (one envelope on stdout), exit codes 0 ok · 1 findings · 2 usage · 3 refused ·
4 not found / unreadable / corrupt · 5 internal.

Commands:
  validate [PATH…|--all] [--strict]     schema + semantic checks (§2.2, §2.3)
           [--fix [--dry-run] [--accept-proposed]]   legacy migration (§2.5)
  next <change>                         the computed next phase (REQ-W1-005)
  active                                the active change (§5), shared with hooks and dashboard
  advance <change> <to> [--by] [--pipeline-run URL --post-deploy-check pass]
  generated <change> <phase>            approvals.<phase>.generated = true
  skip <change> <phase> --reason R      skipped[phase] = R (skippable phases only)
  reopen <change> <phase> --reason R [--ref]   backward edge for karvey-iterate (spec-gap)
  outcome <change> <phase|gate> changes_requested --by --role --ref [--reason] [--kind plan-exception]
  approve <change> <phase> --by --role human|ceo-delegate|auto --ref [--date] [--write-spec]
                                        prod → the release ledger (D-03), never spec.json
                                        unless --write-spec (archive branch, REQ-W1-032)
  check-prod <change>                   the prod-gate's question (REQ-W1-023)
  lane <change> set|raise|lower <lane> [--answers F] [--reason R] [--by --role human --ref]   (lower: the human)
  lane-check <change> --base REF [--head REF] [--finding F-NN]   (lane.diff hits → changes/{id}/checks.jsonl)
  lane-evidence <change> --bug BUG-NN --finding F-NN --regression-test PATH::NAME   (patch / hotfix)
  deploy-record <change> --env --version --verification pass|regression|not-evaluated [--rollback] [--evidence]
  advance <change> deployed --attested --ref D-NN --pipeline-run URL   (a clone without the ledger)
"""
import argparse
import copy
import re
import difflib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import approval, atomicio, gitlog, lanes as ln, modes, project as pj, schema_lite as sl  # noqa: E402

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
    if key and key != "prod" and lane_skips(data, phase):
        return "skipped"  # skipped by the change's lane (recorded as lane:{lane} when advance passes it)
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


def lane_skips(data, phase):
    """True when this change's own ``spec.json:lane`` marks ``phase`` skipped (``s``) (wave2 §1.3)."""
    lane = data.get("lane") if isinstance(data, dict) else None
    if not isinstance(lane, str) or not lane:
        return False
    try:
        return ln.lane_skips(lane, phase)
    except ln.LaneError:
        return False


def lane_optional(data, phase):
    """True when the change's lane marks ``phase`` optional (``o``): a skip with a reason is accepted."""
    lane = data.get("lane") if isinstance(data, dict) else None
    try:
        return isinstance(lane, str) and lane in ln.names() and ln.phase_rule(lane, phase) == "o"
    except ln.LaneError:
        return False


def lane_reason(data):
    return "lane:%s" % data.get("lane")


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

    # a non-skippable phase in skipped: only as a lane skip of this change's own lane (§2.1, wave2); a
    # lane:{x} reason must name this change's lane and a phase that lane skips
    for ph in sorted(skipped):
        pdef = phase_def(ph)
        is_lane = isinstance(skipped[ph], str) and skipped[ph].startswith("lane:")
        if not pdef or (pdef["skippable"] and not is_lane):
            continue
        if not is_lane and lane_optional(data, ph):
            continue  # an optional phase of the lane, skipped with a reason
        lane_reason = "lane:%s" % data.get("lane") if isinstance(data.get("lane"), str) else None
        if skipped[ph] != lane_reason or not lane_skips(data, ph):
            out.append(kl.issue("state.skip_not_lane", "phase %r is not skippable: only a lane skip of this "
                                "change's lane is accepted (reason %r, lane %r)" % (ph, skipped[ph], data.get("lane")),
                                severity="error", file=file, path="$.skipped.%s" % ph,
                                expected=lane_reason or "lane:{lane} with spec.json:lane set", got=skipped[ph]))

    # skipped and approved at the same time
    for ph in sorted(skipped):
        pdef = phase_def(ph)
        ap = approvals.get(pdef["approval"]) if pdef and pdef["approval"] else None
        if isinstance(ap, dict) and ap.get("approved") is True:
            out.append(kl.issue("state.skipped_and_approved", "phase %r is both skipped and approved" % ph,
                                severity="warning", file=file, path="$.skipped.%s" % ph))

    # approvals.deploy is retired: deploys live in spec.json:deploys (REQ-W2-051)
    if "deploy" in approvals:
        out.append(kl.issue("state.legacy_deploy_approval", "approvals.deploy is a legacy key: deploys are recorded "
                            "in deploys[] (deploy-record); run validate --fix to migrate it", severity="warning",
                            file=file, path="$.approvals.deploy", expected="deploys[]", got="approvals.deploy"))

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
            if p["id"] in skipped or p["id"] in seen or lane_skips(data, p["id"]):
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


PRE_312_REASON = "pre-3.12 recorded history (D-14)"
_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}")


def is_archived_path(file):
    """True for a spec.json under ``docs/spec/changes/archive/``."""
    f = "/" + str(file or "").replace("\\", "/").lstrip("/")
    return "/docs/spec/changes/archive/" in f or f.startswith("/changes/archive/")


def pre_312_history(data, file):
    """D-14 / F-35: an archived change whose recorded approval dates all predate the 3.12.0 release
    (``defaults.json:pre_3_12_history.released_on``; null = not released yet)."""
    if not is_archived_path(file):
        return False
    approvals = data.get("approvals") if isinstance(data.get("approvals"), dict) else {}
    dates = [a.get("date") for a in approvals.values() if isinstance(a, dict) and "date" in a]
    if not dates or not all(isinstance(d, str) and _DATE_PREFIX.match(d) for d in dates):
        return False
    cutoff = (kl.defaults().get("pre_3_12_history") or {}).get("released_on")
    return cutoff is None or all(d[:10] < cutoff for d in dates)


def _downgrade_pre_312(issues, data, file):
    """Approval-format errors of pre-3.12 archived history become warnings with their reason."""
    if not pre_312_history(data, file):
        return issues
    out = []
    for i in issues:
        p = i.get("path") or ""
        if i["severity"] == "error" and p.startswith("$.approvals") and \
                (i["code"].startswith("schema.") or i["code"] == "state.prod_missing"):
            i = dict(i, severity="warning", message="%s (warning: %s)" % (i["message"], PRE_312_REASON))
        out.append(i)
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
        issues = _downgrade_pre_312(issues, data, file)
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


# --------------------------------------------------------------------------- migration (§2.5)
class Unmigratable(Exception):
    """A value --fix cannot interpret: the file is not written (exit 3)."""


SKIP_REASON_NONE = "(legacy: no reason recorded)"


def _norm_phase_name(value):
    return value.replace("-", "_") if isinstance(value, str) else value


def with_exited(entry, at):
    """Copy of a history entry with ``exited_at`` placed right after ``entered_at``."""
    out = {}
    for k, v in entry.items():
        if k == "exited_at":
            continue
        out[k] = v
        if k == "entered_at":
            out["exited_at"] = at
    if "exited_at" not in out:
        out["exited_at"] = at
    return out


def _fix_history(hist, accept_proposed, notes):
    """Normalise hand-written ``{from, to, at, by, ref}`` transitions and legacy phase values."""
    if not isinstance(hist, list):
        return hist
    out = []
    for e in hist:
        if _is_legacy_transition(e):
            frm, _ = map_phase(e.get("from"))
            to, tier = map_phase(e.get("to"))
            if to is None or (tier == "proposed" and not accept_proposed):
                notes.append("phase_history: transition to %r left as is (unmappable)" % e.get("to"))
                out.append(e)
                continue
            at = e.get("at")
            for pos in range(len(out) - 1, -1, -1):
                prev = out[pos]
                if isinstance(prev, dict) and prev.get("phase") == frm:
                    if "exited_at" not in prev and at:
                        out[pos] = with_exited(prev, at)
                    break
            else:
                notes.append("phase_history: no open %r entry for the transition to %r" % (e.get("from"), to))
            new = {"phase": to, "entered_at": at}
            for k in ("by", "ref", "evidence"):
                if k in e:
                    new[k] = e[k]
            out.append(new)
            notes.append("phase_history: {from: %r, to: %r} → {phase: %r, entered_at}" % (e.get("from"),
                                                                                         e.get("to"), to))
            continue
        if isinstance(e, dict) and "phase" in e:
            mapped, tier = map_phase(e["phase"])
            if tier == "exact" or (tier == "proposed" and accept_proposed):
                e = dict(e)
                notes.append("phase_history: %r → %r" % (e["phase"], mapped))
                e["phase"] = mapped
        out.append(e)
    return out


def fix_spec(data, accept_proposed=False):
    """``(new_data, notes)`` for a spec.json. Raises :class:`Unmigratable`. Never creates or flips an
    approval: only ``phase``, ``phase_history``, ``skipped``, ``approvals: null`` and
    ``management: "none"`` change."""
    new = copy.deepcopy(data)
    notes = []
    phase = new.get("phase")
    mapped, tier = map_phase(phase)
    if tier == "unmappable":
        raise Unmigratable("phase %r is unmappable: the owner picks the phase (nothing written)" % (phase,))
    if tier == "exact" or (tier == "proposed" and accept_proposed):
        new["phase"] = mapped
        notes.append("phase: %r → %r (%s tier)" % (phase, mapped, tier))
    elif tier == "proposed":
        notes.append("phase: %r → %r not applied: proposed tier, re-run with --accept-proposed" % (phase, mapped))

    if "approvals" in new and new["approvals"] is None:
        new["approvals"] = {}
        notes.append("approvals: null → {}")

    mgmt = new.get("management", None)
    if "management" in new:
        if mgmt == "none":
            new["management"] = "markdown"
            notes.append("management: 'none' → 'markdown'")
        elif not isinstance(mgmt, (str, dict)):
            raise Unmigratable("management %r is not migratable (expected a tool name or an object)" % (mgmt,))

    if "phase_history" in new:
        new["phase_history"] = _fix_history(new["phase_history"], accept_proposed, notes)

    skippable = {p["id"] for p in machine()["phases"] if p["skippable"]}
    skipped = new.get("skipped") if isinstance(new.get("skipped"), dict) else None
    additions = {}
    gs = new.get("gates_skipped")
    if isinstance(gs, dict):
        phases = gs.get("phases") if isinstance(gs.get("phases"), list) else []
        reason = gs.get("reason") if isinstance(gs.get("reason"), str) and gs["reason"].strip() else SKIP_REASON_NONE
        rest = []
        for ph in phases:
            name = _norm_phase_name(ph)
            if name in skippable:
                additions.setdefault(name, reason)
            else:
                rest.append(ph)
        if rest:
            notes.append("gates_skipped: %s not skippable, kept for the owner" % ", ".join(map(str, rest)))
        elif phases:
            del new["gates_skipped"]
            notes.append("gates_skipped removed (every phase moved to skipped)")
    approvals = new.get("approvals") if isinstance(new.get("approvals"), dict) else {}
    for key, ap in approvals.items():
        reason = embedded_skip(ap)
        if reason is not None and key in skippable:
            additions.setdefault(key, reason)
    if additions:
        if skipped is None:
            skipped = {}
            new["skipped"] = skipped
        for ph, reason in additions.items():
            if ph not in skipped:
                skipped[ph] = reason
                notes.append("skipped.%s = %r" % (ph, reason))
    return new, notes


def fix_project(data, accept_proposed=False):
    """``(new_data, notes)`` for a project.json (REQ-W1-010). Raises :class:`Unmigratable`.

    Exact: a ``management`` string → object, ``clickup.backlog_list_id`` → ``management.location``,
    ``notifications.channel: google_chat`` → ``google-chat``. Proposed (``--accept-proposed``, F-38): a
    legacy ``management.status_flow`` keyed by the logical states → ``management.statuses``."""
    new = copy.deepcopy(data)
    notes = []
    nt = new.get("notifications")
    if isinstance(nt, dict) and nt.get("channel") in pj.LEGACY_CHANNELS:
        notes.append("notifications.channel %r → %r" % (nt["channel"], pj.LEGACY_CHANNELS[nt["channel"]]))
        nt["channel"] = pj.LEGACY_CHANNELS[nt["channel"]]
    if "management" in new:
        m = new["management"]
        if isinstance(m, str):
            tool = "markdown" if m == "none" else m
            new["management"] = {"tool": tool}
            notes.append("management: %r → {\"tool\": %r}" % (m, tool))
        elif not isinstance(m, dict):
            raise Unmigratable("management %r is not migratable (expected a tool name or an object)" % (m,))
        mg = new["management"]
        cu = new.get("clickup")
        blid = None
        if isinstance(cu, dict) and isinstance(cu.get("backlog_list_id"), (str, int)) and cu["backlog_list_id"] != "":
            blid, src = str(cu["backlog_list_id"]), "clickup"
        elif isinstance(new.get("backlog_list_id"), (str, int)) and new["backlog_list_id"] != "":
            blid, src = str(new["backlog_list_id"]), "top"
        if blid is not None:
            if "location" not in mg:
                mg["location"] = blid
                if src == "clickup":
                    del cu["backlog_list_id"]
                    if not cu:
                        del new["clickup"]
                    notes.append("clickup.backlog_list_id → management.location")
                else:
                    del new["backlog_list_id"]
                    notes.append("backlog_list_id → management.location")
            elif mg["location"] != blid:
                notes.append("backlog_list_id %r kept: management.location is already %r" % (blid, mg["location"]))
        proposed = pj.legacy_status_flow(mg)
        if proposed is not None and accept_proposed:
            mg["statuses"] = proposed
            del mg["status_flow"]
            notes.append("management.status_flow → statuses (proposed, accepted)")
        elif proposed is not None:
            notes.append("management.status_flow can become statuses (proposed tier): run validate --fix "
                         "--accept-proposed")
    return new, notes


def fix_file(path, loaded, accept_proposed):
    if kind_of(path) == "project":
        return fix_project(loaded.data, accept_proposed)
    return fix_spec(loaded.data, accept_proposed)


def unified(before, after, name):
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile="a/" + name, tofile="b/" + name))


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
    if (args.dry_run or args.accept_proposed) and not args.fix:
        raise Usage("--dry-run and --accept-proposed need --fix")
    errors, warnings, report = [], [], []
    worst = kl.EXIT_OK
    refused = False
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
        data = loaded.data
        if args.fix:
            if not isinstance(data, dict):
                errors.append(kl.issue("state.unmigratable", "not a JSON object", file=name))
                entry["refused"] = "not a JSON object"
                report.append(entry)
                refused = True
                continue
            try:
                new, notes = fix_file(f, loaded, args.accept_proposed)
            except Unmigratable as exc:
                errors.append(kl.issue("state.unmigratable", str(exc), file=name))
                entry["refused"] = str(exc)
                report.append(entry)
                refused = True
                continue
            entry["notes"] = notes
            entry["changed"] = new != data
            entry["written"] = False
            if entry["changed"]:
                before = Path(f).read_bytes().decode("utf-8")
                after = atomicio.dumps(new, **loaded.fmt)
                entry["diff"] = unified(before, after, name)
                if not args.json:
                    sys.stdout.write(entry["diff"])  # the diff always comes first (§2.5)
                if not args.dry_run:
                    atomicio.write_json(f, new, loaded=loaded)
                    entry["written"] = True
            data = new
        issues = validate_data(data, kind_of(f), strict, file=name)
        e = [i for i in issues if i["severity"] == "error"]
        w = [i for i in issues if i["severity"] == "warning"]
        entry["errors"], entry["warnings"] = len(e), len(w)
        errors += e
        warnings += w
        report.append(entry)
        if e and worst == kl.EXIT_OK:
            worst = kl.EXIT_FINDINGS
    if refused:
        worst = kl.EXIT_REFUSED
    result = {"mode": strict_mode, "files": report}
    if args.fix:
        result["fix"] = {"dry_run": bool(args.dry_run), "accept_proposed": bool(args.accept_proposed)}
    lines = []
    for r in report:
        if r.get("refused"):
            state = "REFUSED"
        elif r.get("unreadable"):
            state = "unreadable"
        else:
            state = "OK" if not r["errors"] else "INVALID"
        extra = ""
        if args.fix and not r.get("refused") and not r.get("unreadable"):
            extra = " · " + ("fixed" if r.get("written") else ("would fix" if r.get("changed") else "nothing to fix"))
        lines.append("%-10s %s (%d errors, %d warnings)%s" % (state, r["file"], r["errors"], r["warnings"], extra))
        for n in r.get("notes", []):
            lines.append("           - " + n)
    lines.append("mode: %s · %d files · %d errors · %d warnings" % (strict_mode, len(report), len(errors),
                                                                   len(warnings)))
    return worst, result, errors, warnings, "\n".join(lines)


def change_spec_path(root, change):
    """``docs/spec/changes/<change>/spec.json``, else the newest ``changes/archive/*<change>``."""
    if not isinstance(change, str) or not change or "/" in change or "\\" in change or change.startswith("."):
        raise Usage("invalid change id %r" % (change,))
    base = Path(root) / pj.CHANGES_DIR
    p = base / change / "spec.json"
    if p.is_file():
        return p
    arch = base / pj.ARCHIVE_NAME
    if arch.is_dir():
        hits = sorted(d for d in arch.iterdir() if d.is_dir() and (d.name == change or d.name.endswith("-" + change)))
        if hits and (hits[-1] / "spec.json").is_file():
            return hits[-1] / "spec.json"
    raise NotFound("change %r not found (no %s)" % (change, rel(root, p)))


def load_change(root, change):
    path = change_spec_path(root, change)
    loaded = load(path)
    check_schema_version(loaded.data, rel(root, path))
    if not isinstance(loaded.data, dict):
        raise NotFound("%s is not a JSON object" % rel(root, path))
    return path, loaded


def is_skipped(data, pid):
    pdef = phase_def(pid)
    if pdef and lane_skips(data, pid):
        return True  # the lane passes it (wave2 §1.4)
    return bool(pdef and (pdef["skippable"] or lane_optional(data, pid)) and approval_state(data, pid) == "skipped")


def next_phase_of(data, index):
    ids = phase_ids()
    for pid in ids[index + 1:]:
        if not is_skipped(data, pid):
            return pid
    return None


def release_evidence(ledger):
    """Missing pieces of the release evidence that ``deployed`` needs (REQ-W1-011)."""
    missing = []
    prod = (ledger or {}).get("prod") if isinstance(ledger, dict) else None
    rel_ = (ledger or {}).get("release") if isinstance(ledger, dict) else None
    if not (isinstance(prod, dict) and prod.get("by") and prod.get("role") == "human" and prod.get("ref")):
        missing.append("release ledger has no human prod approval (approve <change> prod)")
    if not (isinstance(rel_, dict) and rel_.get("pipeline_run")):
        missing.append("no pipeline run recorded (--pipeline-run)")
    if not (isinstance(rel_, dict) and rel_.get("post_deploy_check") == "pass"):
        missing.append("post-deploy check not passed (--post-deploy-check pass)")
    return missing


def compute_next(data, ledger=None, ledger_known=False):
    """The next-phase record of §1.2 for a parsed, valid spec.json."""
    raw = data.get("phase")
    mapped, tier = map_phase(raw)
    idx = phase_index(mapped)
    cur = phase_def(mapped)
    nxt = next_phase_of(data, idx)
    res = {"change": data.get("change_id"), "phase": mapped, "status": "in-progress", "next_phase": nxt,
           "skill": cur["skill"], "preconditions": [], "blockers": []}
    if tier in ("exact", "proposed"):
        res["phase_raw"] = raw
    if nxt is None:
        res.update(status="ready", skill=None, terminal=True)
        return res
    for ph in gate_phases_before(phase_index(nxt)):
        st = approval_state(data, ph)
        res["preconditions"].append({"phase": ph, "state": st})
        if st == "pending":
            res["blockers"].append("%s not approved or skipped" % ph)
    key = cur["approval"]
    if nxt == "deployed":
        if ledger_known:
            res["blockers"] += release_evidence(ledger)
        else:
            res["blockers"].append("release evidence is checked by advance deployed (ledger)")
        satisfied = not res["blockers"]
    elif nxt == "archived":
        if approval_state(data, "deployed") != "approved":
            res["blockers"].append("approvals.prod not in spec.json (approve <change> prod --write-spec)")
        satisfied = not res["blockers"]
    elif key and key not in ("deploy", "prod"):
        st = approval_state(data, mapped)
        ap = (data.get("approvals") or {}).get(key) if isinstance(data.get("approvals"), dict) else None
        if st in ("approved", "skipped"):
            satisfied = True
        elif isinstance(ap, dict) and ap.get("generated") is True:
            res["status"] = "awaiting-approval"
            satisfied = False
        else:
            satisfied = False
        if st == "pending":
            res["blockers"].append("%s not approved or skipped" % mapped)
    else:
        satisfied = False  # no approval: the phase's own skill says when it is done
    for m in lane_evidence_missing(data, nxt):
        res["blockers"].append("lane %s needs %s (lane-evidence)" % (data.get("lane"), m))
    res["blockers"] = list(dict.fromkeys(res["blockers"]))  # each blocker once, in order (F-26, REQ-W2-074)
    if satisfied and not [b for b in res["blockers"]]:
        res["status"] = "ready"
        res["skill"] = phase_def(nxt)["skill"]
    elif satisfied:
        res["status"] = "awaiting-approval"
    return res


def cmd_next(args, root):
    path, loaded = load_change(root, args.change)
    name = rel(root, path)
    strict = schema_mode(root) == "strict"
    issues = validate_data(loaded.data, "spec", strict, file=name)
    errs = [i for i in issues if i["severity"] == "error"]
    warns = [i for i in issues if i["severity"] == "warning"]
    mapped, _ = map_phase(loaded.data.get("phase"))
    if errs or mapped is None:
        res = {"change": args.change, "phase": loaded.data.get("phase"), "status": "invalid", "next_phase": None,
               "skill": None, "preconditions": [], "blockers": ["%s fails validation" % name], "file": name}
        return kl.EXIT_FINDINGS, res, errs, warns, "%s: invalid — fix the validation errors first" % args.change
    ledger, known = read_ledger_safe(root, args.change)
    res = compute_next(loaded.data, ledger, known)
    res["file"] = name
    lane, source = ln.lane_of(loaded.data)
    res["lane"], res["lane_source"] = lane, source
    if source != "spec" and mapped != "archived":
        warns = warns + [kl.issue("state.lane_missing", "no lane in spec.json: %s (every phase mandatory unless "
                                  "recorded as skipped); set one with lane set" % (
                                      "the 3.12 pipeline applies" if source == "legacy" else
                                      "type %r gives lane %r for display only" % (loaded.data.get("type"), lane)),
                                  severity="warning", file=name, path="$.lane")]
    human = "%s: phase %s · %s · next %s%s" % (
        args.change, res["phase"], res["status"], res["next_phase"] or "—",
        (" (" + res["skill"] + ")") if res.get("skill") else "")
    for b in res["blockers"]:
        human += "\n  blocker: " + b
    return kl.EXIT_OK, res, [], warns, human


def read_ledger_safe(root, change):
    """``(ledger, known)``: known is False when the release ledger cannot be located."""
    try:
        ledger, status = approval.read_ledger(root, change)
    except (approval.ApprovalError, OSError):
        return None, False
    return (ledger if status == "ok" else None), True


def cmd_active(args, root):
    res = pj.active_change(root)
    if res["change"]:
        human = "active: %s (%s)" % (res["change"], res["reason"])
    elif res["reason"] == "several":
        human = "several active: %s" % ", ".join(res["candidates"])
    else:
        human = "no active change"
    return kl.EXIT_OK, res, [], [], human


# --------------------------------------------------------------------------- transitions
def _approvals(data):
    if not isinstance(data.get("approvals"), dict):
        data["approvals"] = {}
    return data["approvals"]


def _normalise_owned(data):
    """Bring the fields the tool owns to their normal form (§1.2 legacy files): an exact-tier
    phase and hand-written history transitions; every other legacy field is left as is."""
    mapped, tier = map_phase(data.get("phase"))
    if tier == "unmappable":
        raise Refused("phase %r is unmappable legacy: run validate --fix --dry-run" % (data.get("phase"),),
                      code="state.unmappable")
    if tier == "proposed":
        raise Refused("phase %r is a proposed-tier legacy value (→ %r): run validate --fix --dry-run "
                      "--accept-proposed" % (data.get("phase"), mapped), code="state.unmappable")
    data["phase"] = mapped
    if "phase_history" in data:
        data["phase_history"] = _fix_history(data["phase_history"], False, [])
    return mapped


def _last_entry_ok(data):
    hist = data.get("phase_history")
    if hist is None:
        data["phase_history"] = []
        return
    if not isinstance(hist, list):
        raise Refused("phase_history is not a list: run validate", code="state.history_corrupt")
    if not hist:
        return
    last = hist[-1]
    if not isinstance(last, dict) or not isinstance(last.get("phase"), str) or not last.get("entered_at"):
        raise Refused("phase_history last entry is corrupt (no phase/entered_at): %s"
                      % json.dumps(last, ensure_ascii=False)[:120], code="state.history_corrupt")


def _move_history(data, to, now, by=None, ref=None, evidence=None):
    hist = data["phase_history"]
    if hist and "exited_at" not in hist[-1]:
        hist[-1] = with_exited(hist[-1], now)
    entry = {"phase": to, "entered_at": now}
    if by:
        entry["by"] = by
    if ref:
        entry["ref"] = ref
    if evidence:
        entry["evidence"] = evidence
    hist.append(entry)


def _key_of(phase):
    """The approval key of a phase id (or an approval key itself, e.g. ``deploy``)."""
    pdef = phase_def(phase)
    if pdef and pdef["approval"]:
        return pdef["approval"]
    keys = {p["approval"] for p in machine()["phases"] if p["approval"]}
    return phase if phase in keys else None


def transact(root, change, mutate):
    """Read → mutate a copy → check the write keeps the owned fields valid → atomic CAS write."""
    path, loaded = load_change(root, change)
    before = loaded.data
    data = copy.deepcopy(before)
    result = mutate(data)
    if data == before:
        return path, result, False
    name = rel(root, path)
    old = {(i["code"], i["path"]) for i in validate_data(before, "spec", False, name) if i["severity"] == "error"}
    new = [i for i in validate_data(data, "spec", False, name) if i["severity"] == "error"
           and (i["code"], i["path"]) not in old]
    if new:
        raise Refused("the write would make %s invalid: %s" % (name, "; ".join(
            "%s %s" % (i["path"], i["message"]) for i in new[:3])), code="state.invalid_write")
    atomicio.write_json(path, data, loaded=loaded)
    return path, result, True


def consume_on_close(root, change, data, closing):
    """Consume the markers of the phase that closed (REQ-W1-016, §3.3 control 7): the marker its
    approval recorded as evidence, and the change's marker created while that phase was current."""
    consumed = []
    try:
        pdef = phase_def(closing)
        key = pdef["approval"] if pdef else None
        aps = data.get("approvals") if isinstance(data.get("approvals"), dict) else {}
        ev = (aps.get(key) or {}).get("evidence") if key and isinstance(aps.get(key), dict) else None
        if isinstance(ev, dict) and isinstance(ev.get("marker"), str) and ev["marker"].startswith("approvals/"):
            scope = ev["marker"][len("approvals/"):-len(".json")] if ev["marker"].endswith(".json") else ""
            if approval.valid_scope(scope) and approval.consume(root, scope, created_at=ev.get("marker_created_at")):
                consumed.append(scope)
        entered = None
        for e in reversed(data.get("phase_history") or []):
            if isinstance(e, dict) and e.get("phase") == closing:
                entered = parse_dt(e.get("entered_at"))
                break
        m, status = approval.read_marker(root, change)
        if change not in consumed and status == "ok" and m.get("consumed_at") is None:
            created = parse_dt(m.get("created_at"))
            if created is not None and (entered is None or created >= entered):
                if approval.consume(root, change):
                    consumed.append(change)
        approval.gc(root)
    except (approval.ApprovalError, atomicio.AtomicIOError, OSError):
        pass
    return consumed


def cmd_advance(args, root):
    to = args.to
    if to not in phase_ids():
        raise Usage("unknown phase %r (one of %s)" % (to, ", ".join(phase_ids())))
    if (args.pipeline_run or args.post_deploy_check or args.attested) and to != "deployed":
        raise Usage("--pipeline-run, --post-deploy-check and --attested are only for 'deployed'")
    now = now_iso()
    info = {}

    def mutate(data):
        cur = _normalise_owned(data)
        _last_entry_ok(data)
        ci, ti = phase_index(cur), phase_index(to)
        if ti == ci:
            raise Refused("%s is already in %s" % (args.change, to), code="state.edge")
        if ti < ci:
            raise Refused("edge not in the graph: %s → %s (backward: use reopen)" % (cur, to), code="state.edge")
        for ph in gate_phases_before(ti):
            if approval_state(data, ph) == "pending":
                raise Refused("%s not approved or skipped" % ph, code="state.precondition")
        for p in machine()["phases"][ci + 1:ti]:
            if is_skipped(data, p["id"]) or (p["approval"] and approval_state(data, p["id"]) == "approved"):
                continue
            raise Refused("edge not in the graph: %s → %s (%s not passed)" % (cur, to, p["id"]), code="state.edge")
        missing_ev = lane_evidence_missing(data, to)
        if missing_ev:
            raise Refused("lane %s needs %s before %s: record them with lane-evidence %s --bug BUG-NN "
                          "--regression-test PATH::NAME" % (data.get("lane"), " and ".join(missing_ev), to,
                                                            args.change), code="state.lane_evidence")
        evidence = None
        if to == "deployed" and args.attested:
            evidence = attested_evidence(root, args)
            info["ledger"] = "none (attested)"
        elif to == "deployed":
            ledger, _ = read_ledger_safe(root, args.change)
            missing = []
            prod = (ledger or {}).get("prod") if ledger else None
            if not (isinstance(prod, dict) and prod.get("by") and prod.get("role") == "human" and prod.get("ref")):
                missing.append("release ledger has no human prod approval (approve %s prod)" % args.change)
            if not args.pipeline_run:
                missing.append("--pipeline-run <url> (the green production pipeline)")
            if args.post_deploy_check != "pass":
                missing.append("--post-deploy-check pass")
            if missing:
                if ledger is None:
                    missing.append("or, without a release ledger in this clone: --attested --ref D-NN "
                                   "--pipeline-run https://…")
                raise Refused("deployed needs release evidence: " + "; ".join(missing), code="state.evidence")
            evidence = {"pipeline_run": args.pipeline_run, "post_deploy_check": "pass"}
            info["ledger"] = "release"
        if to == "archived" and approval_state(data, "deployed") != "approved":
            raise Refused("archived needs approvals.prod in spec.json (by, role human, ref): run "
                          "approve %s prod --write-spec on the archive branch" % args.change, code="state.precondition")
        lane_skipped = record_lane_skips(data, ti)
        if lane_skipped:
            info["lane_skipped"] = lane_skipped
        _move_history(data, to, now, by=args.by, evidence=evidence)
        data["phase"] = to
        data["updated_at"] = now
        info.update({"from": cur, "to": to})
        return info

    path, loaded = load_change(root, args.change)  # exit 4 before touching the ledger
    if to == "deployed" and not args.attested:
        # validate first, then write the ledger, then spec.json (a re-run is idempotent)
        mutate(copy.deepcopy(loaded.data))
        approval.record_release(root, args.change, args.pipeline_run, "pass", at=now)
    info.clear()
    path, res, _ = transact(root, args.change, mutate)
    res["consumed"] = consume_on_close(root, args.change, loaded.data, res["from"])
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], [], "%s: %s → %s" % (args.change, res["from"], res["to"])


HOTFIX_EVIDENCE = (("bug_id", "a BUG-NN (--bug)"), ("regression_test", "a regression test (--regression-test)"))


def lane_evidence_missing(data, to):
    """The hotfix preconditions of REQ-W2-018: impl (and later) need the BUG-NN and the regression test."""
    if data.get("lane") != "hotfix" or to is None or phase_index(to) < phase_index("impl"):
        return []
    ev = data.get("lane_evidence") if isinstance(data.get("lane_evidence"), dict) else {}
    return [text for key, text in HOTFIX_EVIDENCE if not (isinstance(ev.get(key), str) and ev[key].strip())]


def record_lane_skips(data, before_index):
    """Write ``skipped[phase] = lane:{lane}`` for every approvable phase before ``before_index`` that the change's
    lane skips and that is not recorded yet (REQ-W2-015). A manual skip is never overwritten."""
    out = []
    for p in machine()["phases"][:max(before_index, 0)]:
        if not p["approval"] or p["approval"] == "prod" or not lane_skips(data, p["id"]):
            continue
        sk = data.get("skipped")
        if not isinstance(sk, dict):
            sk = {}
            data["skipped"] = sk
        if p["id"] not in sk:
            sk[p["id"]] = lane_reason(data)
            out.append(p["id"])
    return out


ATTESTED_MSG = ("an attested deployed needs both evidences: --ref D-NN (a decision in docs/spec/decisions.md) "
                "and --pipeline-run https://… (the green production pipeline run)")


def attested_evidence(root, args):
    """``deployed`` recorded from a clone without the release ledger (REQ-W2-053): attested, not measured."""
    ledger, status = approval.read_ledger(root, args.change)
    if status != "missing":
        raise Refused("--attested is only for a clone without a release ledger; this clone has one (%s): use the "
                      "measured path (approve %s prod, --pipeline-run, --post-deploy-check pass)"
                      % (status, args.change), code="state.attested_with_ledger")
    ref = (args.ref or "").strip()
    run = (args.pipeline_run or "").strip()
    missing = []
    if not (re.match(r"^D-\d+$", ref) and decision_exists(root, ref)):
        missing.append("--ref D-NN")
    if not re.match(r"^https://\S+$", run):
        missing.append("--pipeline-run https://…")
    if missing:
        raise Refused("%s (missing: %s)" % (ATTESTED_MSG, ", ".join(missing)), code="state.evidence")
    return {"attested": True, "ref": ref, "pipeline_run": run}


def cmd_init(args, root):
    """Create the state of a new change: ``phase: init`` with its ``phase_history`` entry (REQ-W1-013).

    A missing ``spec.json`` is created; an existing one without ``phase`` (the skill wrote its descriptive
    fields first) gets the state fields added and keeps every other key. A file that already has a phase is
    refused: use ``advance``, ``reopen`` or ``validate --fix``."""
    change = args.change
    if not isinstance(change, str) or not re.match(r"^[a-z0-9][a-z0-9._-]*$", change):
        raise Usage("invalid change id %r (lowercase letters, digits, . _ -)" % (change,))
    now = now_iso()
    entry = {"phase": "init", "entered_at": now}
    if args.by:
        entry["by"] = args.by
    state_fields = {"schema_version": SCHEMA_VERSION, "change_id": change, "phase": "init",
                    "phase_history": [entry], "approvals": {}}
    path = Path(root) / pj.CHANGES_DIR / change / "spec.json"
    if not path.is_file():
        data = dict(state_fields, created_at=now, updated_at=now)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomicio.write_text_atomic(str(path), atomicio.dumps(data))
        return kl.EXIT_OK, {"change": change, "created": True, "file": rel(root, path)}, [], [], \
            "%s: created in init" % change

    def mutate(data):
        if data.get("phase") is not None:
            raise Refused("%s already has phase %r: use advance, reopen or validate --fix" % (change, data["phase"]),
                          code="state.exists")
        if data.get("change_id") not in (None, change):
            raise Refused("%s holds change_id %r" % (rel(root, path), data["change_id"]), code="state.exists")
        for k, v in state_fields.items():
            if k == "approvals" and isinstance(data.get("approvals"), dict):
                continue
            data[k] = v
        data.setdefault("created_at", now)
        data["updated_at"] = now
        return {"change": change, "created": False}

    path, res, _ = transact(root, change, mutate)
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], [], "%s: state initialised in init" % change


def cmd_generated(args, root):
    key = _key_of(args.phase)
    if key is None or key == "prod":
        raise Refused("unknown or non-generable phase %r" % args.phase, code="state.unknown_phase")

    def mutate(data):
        ap = _approvals(data)
        cur = ap.get(key) if isinstance(ap.get(key), dict) else {"generated": False, "approved": False}
        cur = dict(cur)
        cur["generated"] = True
        cur.setdefault("approved", False)
        now = now_iso()
        if not cur.get("generated_at"):
            cur["generated_at"] = now  # first time only: the approval wait starts here (REQ-W2-001)
        ap[key] = cur
        data["updated_at"] = now
        return {"change": args.change, "approval": key, "generated": True, "generated_at": cur["generated_at"]}

    path, res, changed = transact(root, args.change, mutate)
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], [], "%s: approvals.%s.generated = true" % (args.change, key)


def cmd_skip(args, root):
    pdef = phase_def(args.phase)
    skippable = [p["id"] for p in machine()["phases"] if p["skippable"]]
    if not pdef or not pdef["approval"] or pdef["approval"] == "prod":
        raise Refused("phase %r is not skippable (skippable: %s)" % (args.phase, ", ".join(skippable)),
                      code="state.not_skippable")
    reason = (args.reason or "").strip()
    if not reason:
        raise Refused("a skip needs a non-empty --reason", code="state.reason")
    if reason.startswith("lane:"):
        raise Refused("a lane:{lane} reason is written by advance, not by skip", code="state.reason")
    warnings = []

    def mutate(data):
        if not pdef["skippable"] and not lane_optional(data, args.phase):
            raise Refused("phase %r is not skippable (skippable: %s; or a phase the change's lane marks optional)"
                          % (args.phase, ", ".join(skippable)), code="state.not_skippable")
        sk = data.get("skipped")
        if not isinstance(sk, dict):
            sk = {}
            data["skipped"] = sk
        sk[args.phase] = reason
        data["updated_at"] = now_iso()
        if approval_state(dict(data, skipped={}), args.phase) == "approved":
            warnings.append(kl.issue("state.skipped_and_approved", "phase %r is also approved" % args.phase,
                                     severity="warning", path="$.skipped.%s" % args.phase))
        return {"change": args.change, "skipped": args.phase, "reason": reason}

    path, res, _ = transact(root, args.change, mutate)
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], warnings, "%s: skipped.%s = %r" % (args.change, args.phase, reason)


def cmd_reopen(args, root):
    targets = machine()["reopen_targets"]
    if args.phase not in targets:
        raise Refused("%r is not a reopen target (%s)" % (args.phase, ", ".join(targets)), code="state.edge")
    reason = (args.reason or "").strip()
    if not reason:
        raise Refused("a reopen needs a non-empty --reason", code="state.reason")
    now = now_iso()

    def mutate(data):
        cur = _normalise_owned(data)
        _last_entry_ok(data)
        ci, ti = phase_index(cur), phase_index(args.phase)
        if ci > phase_index("qa"):
            raise Refused("reopen is allowed up to qa; %s is in %s" % (args.change, cur), code="state.edge")
        if ti > ci:
            raise Refused("cannot reopen forward: %s is in %s" % (args.change, cur), code="state.edge")
        ap = _approvals(data)
        superseded = {}
        for p in machine()["phases"][ti:]:
            key = p["approval"]
            if key and key != "prod" and isinstance(ap.get(key), dict):
                superseded[key] = copy.deepcopy(ap[key])
                ap[key] = {"generated": ap[key].get("generated", False) is True, "approved": False}
        rh = data.get("revision_history")
        if not isinstance(rh, list):
            rh = []
            data["revision_history"] = rh
        entry = {"at": now, "reopened": args.phase, "from_phase": cur, "reason": reason}
        if args.ref:
            entry["ref"] = args.ref
        entry["superseded_approvals"] = superseded
        rh.append(entry)
        _move_history(data, args.phase, now, ref=args.ref)
        data["phase"] = args.phase
        data["updated_at"] = now
        return {"change": args.change, "from": cur, "to": args.phase, "superseded": sorted(superseded)}

    path, res, _ = transact(root, args.change, mutate)
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], [], "%s: reopened %s (from %s); superseded: %s" % (
        args.change, res["to"], res["from"], ", ".join(res["superseded"]) or "none")


# --------------------------------------------------------------------------- approvals (§1.2, D-03, D-10)
PROD_REF = re.compile(r"^(D-\d+|https://\S+)$")
ROLES = ("human", "ceo-delegate", "auto")
OUTCOMES = ("changes_requested",)
GATES = ("what", "how", "release")
NO_REASON = "no reason given"


def reviewed_ttl(root):
    """``plan_marker_ttl_min`` from the reviewed line (``origin/{production}``), else the default (§3.5)."""
    data, status = pj.read_reviewed_project_json(root)
    enf = data.get("enforcement") if status == "ok" and isinstance(data.get("enforcement"), dict) else {}
    return approval.clamp_ttl(enf.get("plan_marker_ttl_min"))


def _date_arg(value):
    if value is None:
        return now_iso()
    if not sl.is_datetime_tz(value):
        raise Refused("--date must be ISO 8601 with time and zone (got %r)" % value, code="state.date")
    return value


def decision_exists(root, ref):
    """A ``D-NN`` recorded in ``docs/spec/decisions.md`` (heading or table row)."""
    p = Path(root) / pj.SPEC_DIR / "decisions.md"
    try:
        text = p.read_text(encoding="utf-8-sig")
    except OSError:
        return False
    pat = re.compile(r"^(#+\s*%s\b|\|\s*%s\s*\|)" % (re.escape(ref), re.escape(ref)), re.M)
    return bool(pat.search(text))


def _require(args, fields):
    missing = ["--" + f for f in fields if not (getattr(args, f, None) or "").strip()]
    if missing:
        raise Refused("an approval needs %s (missing: %s)" % (", ".join("--" + f for f in fields),
                                                              ", ".join(missing)), code="state.fields")


def check_prod(root, change):
    """The prod-gate's question, in-process (§1.2 check-prod). Raises :class:`NotFound`."""
    path, loaded = load_change(root, change)
    name = rel(root, path)
    res = {"ok": False, "change": change, "by": None, "role": None, "ref": None, "date": None,
           "source": None, "missing": []}
    errs = [i for i in validate_data(loaded.data, "spec", False, name) if i["severity"] == "error"]
    if errs:
        res["missing"].append("valid spec.json")
        res["reason"] = "cannot verify the production approval: %s fails validation (%s %s)" % (
            name, errs[0]["path"], errs[0]["message"])
        return res
    ledger, status = approval.read_ledger(root, change)
    prod = ledger.get("prod") if ledger and isinstance(ledger.get("prod"), dict) else None
    if status == "corrupt":
        res["missing"].append("ledger")
        res["reason"] = "cannot verify the production approval: the release ledger is corrupt"
        return res
    if prod:
        res.update({"by": prod.get("by"), "role": prod.get("role"), "ref": prod.get("ref"),
                    "date": prod.get("date"), "source": "ledger"})
        if not (isinstance(prod.get("by"), str) and prod["by"].strip()):
            res["missing"].append("by")
        if prod.get("role") != "human":
            res["missing"].append("role")
        if not (isinstance(prod.get("ref"), str) and PROD_REF.match(prod["ref"])):
            res["missing"].append("ref")
        ev = prod.get("evidence") if isinstance(prod.get("evidence"), dict) else {}
        if not (isinstance(ev.get("marker"), str) and ev["marker"].startswith("approvals/")):
            res["missing"].append("evidence")
        res["ok"] = not res["missing"]
        if not res["ok"]:
            res["reason"] = "release ledger prod approval incomplete"
        return res
    sp = (loaded.data.get("approvals") or {}).get("prod") if isinstance(loaded.data.get("approvals"), dict) else None
    if isinstance(sp, dict) and isinstance(sp.get("by"), str) and sp["by"].strip():
        res.update({"by": sp.get("by"), "role": sp.get("role"), "ref": sp.get("ref"), "date": sp.get("date"),
                    "source": "spec", "missing": ["ledger"],
                    "reason": "approval not recorded through the state tool"})
        return res
    res["missing"] = ["by", "role", "ref"]
    res["reason"] = "no production approval recorded"
    return res


def cmd_check_prod(args, root):
    res = check_prod(root, args.change)
    human = ("prod approval OK: %s by %s ref %s (%s)" % (args.change, res["by"], res["ref"], res["source"])
             if res["ok"] else "prod approval MISSING for %s: %s (%s)" % (
                 args.change, ", ".join(res["missing"]), res.get("reason", "")))
    return (kl.EXIT_OK if res["ok"] else kl.EXIT_FINDINGS), res, [], [], human


def _approve_prod_write_spec(args, root):
    ledger, status = approval.read_ledger(root, args.change)
    prod = ledger.get("prod") if ledger and isinstance(ledger.get("prod"), dict) else None
    if prod:
        rec = {k: prod[k] for k in ("by", "role", "date", "ref", "evidence") if k in prod}
        source = "ledger"
    else:
        _require(args, ("by", "role", "ref"))
        if args.role != "human":
            raise Refused("production approval is never delegated", code="state.delegated")
        ref = args.ref.strip()
        if not PROD_REF.match(ref) or (ref.startswith("D-") and not decision_exists(root, ref)):
            raise Refused("the production approval is not recorded: no release-ledger entry, and %r is not a "
                          "D-NN in docs/spec/decisions.md nor a PR approval URL" % ref, code="state.prod_unrecorded")
        rec = {"by": args.by.strip(), "role": "human", "date": _date_arg(args.date), "ref": ref}
        source = "decision"
    if rec.get("role") != "human":
        raise Refused("production approval is never delegated", code="state.delegated")

    def mutate(data):
        _approvals(data)["prod"] = rec
        data["updated_at"] = now_iso()
        return {"change": args.change, "phase": "prod", "source": source, "written": "spec.json", "prod": rec}

    path, res, _ = transact(root, args.change, mutate)
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], [], "%s: approvals.prod written to spec.json from the %s (ref %s)" % (
        args.change, source, rec.get("ref"))


def cmd_approve(args, root):
    key = "prod" if args.phase in ("prod", "deployed") else _key_of(args.phase)
    if key is None:
        raise Refused("unknown phase %r" % args.phase, code="state.unknown_phase")
    if args.write_spec and key != "prod":
        raise Usage("--write-spec is only for prod")
    change_spec_path(root, args.change)  # exit 4 if the change does not exist
    if key == "prod" and args.write_spec:
        return _approve_prod_write_spec(args, root)
    _require(args, ("by", "role", "ref"))
    if args.role not in ROLES:
        raise Refused("--role must be human, ceo-delegate or auto", code="state.role")
    date = _date_arg(args.date)
    by, ref = args.by.strip(), args.ref.strip()
    if key == "prod":
        if args.role == "auto":
            raise Refused("production approval is never automatic", code="state.auto_prod")
        if args.role != "human":
            raise Refused("production approval is never delegated", code="state.delegated")
        if not PROD_REF.match(ref):
            raise Refused("prod --ref must be a D-NN or a PR approval URL (got %r)" % ref, code="state.ref")
        marker, scope, reasons = approval.find_valid(root, args.change, kinds=("prod",), ttl_min=reviewed_ttl(root))
        if marker is None:
            raise Refused("production approval needs a prod-kind approval marker: the human's own message must "
                          "contain an approval word and a production word (D-10); none is valid for %s (%s)"
                          % (args.change, ", ".join("%s: %s" % kv for kv in sorted(reasons.items()))),
                          code="state.no_prod_marker")
        rec = {"by": by, "role": "human", "date": date, "ref": ref, "evidence": approval.evidence(marker, scope)}
        approval.record_prod(root, args.change, rec)
        res = {"change": args.change, "phase": "prod", "source": "ledger", "written": "ledger", "prod": rec}
        return kl.EXIT_OK, res, [], [], "%s: prod approval recorded in the release ledger (ref %s); spec.json " \
                                        "untouched (D-03)" % (args.change, ref)
    marker, scope, _ = approval.find_valid(root, args.change, kinds=("plan", "prod"), ttl_min=reviewed_ttl(root))
    warnings = []
    if marker is None:
        warnings.append(kl.issue("state.no_marker", "no valid approval marker for %s: recorded with "
                                 "evidence.marker = none (a warning in 3.12.0)" % args.change,
                                 severity="warning", path="$.approvals.%s.evidence" % key))
    ev = approval.evidence(marker, scope)

    def mutate(data):
        aps = _approvals(data)
        old = aps.get(key) if isinstance(aps.get(key), dict) else {}
        rec = {"generated": old.get("generated", True) if isinstance(old.get("generated"), bool) else True,
               "approved": True, "by": by, "role": args.role, "date": date, "ref": ref, "evidence": ev}
        for k in ("generated_at", "imported"):
            if k in old:
                rec[k] = old[k]
        aps[key] = rec
        append_outcome(data, {"outcome": "approved", "kind": "gate", "gate": "phase", "phases": [key],
                              "by": by, "role": args.role, "ref": ref, "at": date})
        data["updated_at"] = now_iso()
        return {"change": args.change, "phase": key, "written": "spec.json", "approval": aps[key]}

    path, res, _ = transact(root, args.change, mutate)
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], warnings, "%s: approvals.%s approved by %s (%s, ref %s)" % (
        args.change, key, by, args.role, ref)


def append_outcome(data, entry):
    """Append one ``gate_outcomes`` entry; earlier entries are never rewritten (REQ-W2-001)."""
    log = data.get("gate_outcomes")
    if not isinstance(log, list):
        log = []
        data["gate_outcomes"] = log
    log.append(entry)
    return entry


def lane_rank(lane):
    """How much process a lane runs: the phases it does not skip (``legacy`` = all)."""
    if lane in (None, ln.LEGACY):
        return len(phase_ids())
    return len([p for p, r in ln.lane_def(lane)["phases"].items() if r != "s"])


def _read_answers(path):
    if not path:
        return None
    try:
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise NotFound("--answers %s is unreadable: %s" % (path, exc))
    if not isinstance(data, dict):
        raise Refused("--answers must hold a JSON object", code="state.answers")
    return data


def cmd_lane(args, root):
    """``lane <change> set|raise|lower <lane>`` (REQ-W2-012, 013, 016)."""
    if args.lane not in ln.names():
        raise Refused("unknown lane %r (one of %s)" % (args.lane, ", ".join(ln.names())), code="state.lane")
    now = now_iso()
    answers = _read_answers(args.answers)
    warnings = []
    if args.action == "set" and args.lane == "patch":
        adm = ln.admit_patch(answers)
        if not adm["admitted"]:
            raise Refused("; ".join(adm["reasons"]) or "patch needs the init answers (--answers)",
                          code="state.lane_criteria", result={"proposed": adm["lane"]})
    if args.action in ("raise", "lower"):
        if not (args.reason or "").strip():
            raise Refused("a lane %s needs --reason" % args.action, code="state.reason")
    if args.action == "lower":
        _require(args, ("by", "role", "ref"))
        if args.role != "human":
            raise Refused("lowering a lane needs the human (--role human)", code="state.lane_lower")
        marker, _, reasons = approval.find_valid(root, args.change, kinds=("plan", "prod"), ttl_min=reviewed_ttl(root))
        if marker is None:
            raise Refused("lowering a lane needs the human's approval: no valid approval marker for %s (%s)" % (
                args.change, ", ".join("%s: %s" % kv for kv in sorted(reasons.items()))), code="state.lane_lower")

    def mutate(data):
        cur = data.get("lane") if isinstance(data.get("lane"), str) and data.get("lane") else None
        if args.action == "set":
            if cur:
                raise Refused("%s already has lane %s: use lane raise|lower" % (args.change, cur), code="state.lane")
            if data.get("phase") not in ("init", None):
                raise Refused("lane set is only for a change in init (%s is in %s): use lane raise|lower"
                              % (args.change, data.get("phase")), code="state.lane")
            data["lane"] = args.lane
            data["updated_at"] = now
            return {"change": args.change, "lane": args.lane, "action": "set"}
        frm = cur or ln.LEGACY
        if frm == args.lane:
            raise Refused("%s is already in lane %s" % (args.change, args.lane), code="state.lane")
        up = lane_rank(args.lane) > lane_rank(frm)
        if args.action == "raise" and not up:
            raise Refused("%s → %s is not a raise (it runs fewer phases): use lane lower, which needs the human"
                          % (frm, args.lane), code="state.lane_lower")
        entry = {"from": frm, "to": args.lane, "at": now, "reason": args.reason.strip()}
        if args.by:
            entry["by"] = args.by.strip()
        if args.action == "lower":
            entry["ref"] = args.ref.strip()
        hist = data.get("lane_history") if isinstance(data.get("lane_history"), list) else []
        hist.append(entry)
        data["lane_history"] = hist
        data["lane"] = args.lane
        reopened = []
        sk = data.get("skipped") if isinstance(data.get("skipped"), dict) else {}
        for ph, reason in list(sk.items()):
            if not (isinstance(reason, str) and reason.startswith("lane:")):
                continue  # a manual skip survives any lane change
            if lane_skips(data, ph):
                sk[ph] = lane_reason(data)
            else:
                del sk[ph]
                reopened.append(ph)
        if "skipped" in data and not sk:
            del data["skipped"]
        moved = None
        cur_phase, _ = map_phase(data.get("phase"))
        pend = [p for p in reopened if approval_state(data, p) == "pending"]
        if pend and cur_phase and phase_index(pend[0]) < phase_index(cur_phase):
            _last_entry_ok(data)
            target = min(pend, key=phase_index)
            _move_history(data, target, now, by=args.by, ref=args.ref)
            data["phase"] = moved = target
        data["updated_at"] = now
        return {"change": args.change, "lane": args.lane, "action": args.action, "from": frm,
                "pending": sorted(pend, key=phase_index), "phase": data.get("phase"), "moved_to": moved}

    path, res, _ = transact(root, args.change, mutate)
    res["file"] = rel(root, path)
    human = "%s: lane %s %s%s" % (args.change, args.action, args.lane,
                                  (" (from %s; pending: %s)" % (res["from"], ", ".join(res["pending"]) or "none"))
                                  if args.action != "set" else "")
    return kl.EXIT_OK, res, [], warnings, human


def cmd_lane_evidence(args, root):
    """``lane-evidence``: the BUG-NN, finding and regression test of a patch / hotfix change (REQ-W2-014, 018)."""
    fields = (("bug", "bug_id"), ("finding", "finding"), ("regression_test", "regression_test"))
    given = {k: (getattr(args, a) or "").strip() for a, k in fields}
    if not any(given.values()):
        raise Refused("lane-evidence needs --bug BUG-NN, --finding F-NN and/or --regression-test PATH::NAME",
                      code="state.fields")
    if given["bug_id"] and not re.match(r"^BUG-\d+(@[a-z0-9][a-z0-9._-]*)?$", given["bug_id"]):
        raise Refused("--bug must be BUG-NN (got %r)" % given["bug_id"], code="state.fields")
    if given["regression_test"] and "::" not in given["regression_test"]:
        raise Refused("--regression-test must be PATH::NAME (got %r)" % given["regression_test"], code="state.fields")

    def mutate(data):
        if data.get("lane") not in ("patch", "hotfix"):
            raise Refused("lane-evidence is for the patch and hotfix lanes (%s is %r)" % (args.change, data.get("lane")),
                          code="state.lane")
        ev = dict(data["lane_evidence"]) if isinstance(data.get("lane_evidence"), dict) else {}
        ev.update({k: v for k, v in given.items() if v})
        data["lane_evidence"] = ev
        data["updated_at"] = now_iso()
        return {"change": args.change, "lane_evidence": ev}

    path, res, _ = transact(root, args.change, mutate)
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], [], "%s: lane evidence %s" % (args.change, json.dumps(res["lane_evidence"]))


def cmd_lane_check(args, root):
    """``lane-check <change> --base REF [--head REF] [--finding F-NN]``: the diff against the lane's criteria
    (REQ-W2-017). Each exceeded criterion is one ``lane.diff`` hit in ``changes/{id}/checks.jsonl``; the check's mode
    (``check-modes.json``) decides the exit: warn → 0, blocking → 1. spec.json is never written."""
    path, loaded = load_change(root, args.change)
    lane = loaded.data.get("lane")
    if not isinstance(lane, str) or lane not in ln.names():
        res = {"change": args.change, "lane": lane, "exceeded": [], "text": "no lane: nothing to check"}
        return kl.EXIT_OK, res, [], [], "%s: no lane recorded — lane check not evaluated" % args.change
    mode = modes.resolve(root, "lane.diff")
    try:
        exceeded = ln.measure_diff(root, args.base, args.head, lane=lane, project=pj.load_project_json(root)[0])
    except gitlog.GitLogError as exc:
        raise Refused("cannot measure the diff: %s" % exc, code="state.git")
    for e in exceeded:
        modes.record_hit(root, args.change, "lane.diff", e, finding=args.finding, mode=mode["mode"])
    raise_to = "standard" if exceeded and lane in ("patch", "hotfix", "docs") else None
    res = {"change": args.change, "lane": lane, "mode": mode["mode"], "exceeded": exceeded, "propose": raise_to}
    warns = [kl.issue("modes.lax", mode["warning"], severity="warning")] if mode.get("warning") else []
    if not exceeded:
        return kl.EXIT_OK, res, [], warns, "%s: lane check passed (%s)" % (args.change, lane)
    human = "%s: lane check (%s, %s):\n%s\n  propose: lane raise %s" % (
        args.change, lane, mode["mode"], "\n".join("  " + e for e in exceeded), raise_to or "(a larger lane)")
    code = kl.EXIT_FINDINGS if modes.would_refuse(mode["mode"]) else kl.EXIT_OK
    return code, res, [], warns, human


VERIFICATIONS = ("pass", "regression", "not-evaluated")
_ENV = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$")


def cmd_deploy_record(args, root):
    """``deploy-record``: append ``deploys[{env, version, at, verification, rollback, evidence}]`` (REQ-W2-002)."""
    env, version = (args.env or "").strip(), (args.version or "").strip()
    missing = [n for n, v in (("--env", env), ("--version", version), ("--verification", args.verification)) if not v]
    if missing:
        raise Refused("a deploy record needs --env, --version and --verification (missing: %s)" % ", ".join(missing),
                      code="state.fields")
    if args.verification not in VERIFICATIONS:
        raise Refused("--verification must be one of %s (got %r)" % (", ".join(VERIFICATIONS), args.verification),
                      code="state.verification")
    if not _ENV.match(env) or len(version) > 60:
        raise Refused("invalid --env %r or --version %r" % (env, version), code="state.fields")
    entry = {"env": env, "version": version, "at": _date_arg(args.date), "verification": args.verification,
             "rollback": (args.rollback or "").strip() or None}
    if args.evidence:
        entry["evidence"] = args.evidence.strip()

    def mutate(data):
        log = data.get("deploys")
        if not isinstance(log, list):
            log = []
            data["deploys"] = log
        log.append(entry)
        data["updated_at"] = now_iso()
        return {"change": args.change, "deploy": entry}

    path, res, _ = transact(root, args.change, mutate)
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], [], "%s: deploy recorded (%s %s, verification %s%s)" % (
        args.change, env, version, args.verification, ", rollback" if entry["rollback"] else "")


def gate_phases(gate):
    """The phases a merged gate covers, from ``state-machine.json`` (``gate`` per phase)."""
    return [p["id"] for p in machine()["phases"] if p.get("gate") == gate]


def cmd_outcome(args, root):
    """``outcome <change> <phase|gate> changes_requested``: the human asked for changes (REQ-W2-001, 042)
    or answered a plan-rule question (``--kind plan-exception``, REQ-W2-038). The phase is not changed."""
    if args.outcome not in OUTCOMES:
        raise Usage("outcome must be one of %s (an approval is recorded by approve)" % ", ".join(OUTCOMES))
    _require(args, ("by", "role", "ref"))
    if args.role not in ROLES:
        raise Refused("--role must be human, ceo-delegate or auto", code="state.role")
    if args.target in GATES:
        gate, phases = args.target, gate_phases(args.target)
    else:
        key = _key_of(args.target)
        if key is None:
            raise Refused("unknown phase or gate %r (gates: %s)" % (args.target, ", ".join(GATES)),
                          code="state.unknown_phase")
        gate, phases = "phase", [key]
    change_spec_path(root, args.change)
    reason = (args.reason or "").strip() or NO_REASON
    entry = {"outcome": args.outcome, "kind": args.kind, "gate": gate, "phases": phases, "by": args.by.strip(),
             "role": args.role, "ref": args.ref.strip(), "at": _date_arg(args.date), "reason": reason}

    def mutate(data):
        append_outcome(data, entry)
        data["updated_at"] = now_iso()
        return {"change": args.change, "outcome": entry}

    path, res, _ = transact(root, args.change, mutate)
    res["file"] = rel(root, path)
    return kl.EXIT_OK, res, [], [], "%s: %s recorded for %s (%s; reason: %s)" % (
        args.change, args.outcome, args.target, args.kind, reason)


COMMANDS = {"validate": cmd_validate, "init": cmd_init, "next": cmd_next, "active": cmd_active, "advance": cmd_advance,
            "generated": cmd_generated, "skip": cmd_skip, "reopen": cmd_reopen, "approve": cmd_approve,
            "check-prod": cmd_check_prod, "outcome": cmd_outcome,
            "deploy-record": cmd_deploy_record, "lane": cmd_lane, "lane-evidence": cmd_lane_evidence,
            "lane-check": cmd_lane_check}


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
    v.add_argument("--fix", action="store_true", help="migrate legacy shapes (§2.5); the diff is printed first")
    v.add_argument("--dry-run", action="store_true", help="with --fix: show the diff, write nothing")
    v.add_argument("--accept-proposed", action="store_true", help="with --fix: also apply the proposed tier (D-09)")
    it = sub.add_parser("init", parents=[common], help="create a change's state: phase init + phase_history")
    it.add_argument("change")
    it.add_argument("--by", help="who opens the change (recorded in phase_history)")
    n = sub.add_parser("next", parents=[common], help="the computed next phase of a change")
    n.add_argument("change")
    sub.add_parser("active", parents=[common], help="the active change (§5)")
    a = sub.add_parser("advance", parents=[common], help="apply a forward edge of the phase graph")
    a.add_argument("change")
    a.add_argument("to")
    a.add_argument("--by", help="who applies it (recorded in phase_history)")
    a.add_argument("--pipeline-run", help="deployed only: URL of the green production pipeline run")
    a.add_argument("--post-deploy-check", choices=["pass"], help="deployed only: the post-deploy check passed")
    a.add_argument("--attested", action="store_true",
                   help="deployed only, a clone without the release ledger: needs --ref D-NN and --pipeline-run URL")
    a.add_argument("--ref", help="deployed --attested: the D-NN that records the production OK")
    gnr = sub.add_parser("generated", parents=[common], help="approvals.<phase>.generated = true")
    gnr.add_argument("change")
    gnr.add_argument("phase")
    sk = sub.add_parser("skip", parents=[common], help="record a skipped phase with its reason")
    sk.add_argument("change")
    sk.add_argument("phase")
    sk.add_argument("--reason")
    ro = sub.add_parser("reopen", parents=[common], help="backward edge (karvey-iterate, spec-gap)")
    ro.add_argument("change")
    ro.add_argument("phase")
    ro.add_argument("--reason")
    ro.add_argument("--ref")
    apv = sub.add_parser("approve", parents=[common], help="record an approval (prod → the release ledger)")
    apv.add_argument("change")
    apv.add_argument("phase")
    apv.add_argument("--by")
    apv.add_argument("--role")
    apv.add_argument("--ref")
    apv.add_argument("--date", help="ISO 8601 with time and zone (default: now)")
    apv.add_argument("--write-spec", action="store_true", help="prod only: copy the ledger/D-NN approval into spec.json")
    oc = sub.add_parser("outcome", parents=[common], help="record changes_requested at a gate (the phase stays)")
    oc.add_argument("change")
    oc.add_argument("target", metavar="PHASE|GATE")
    oc.add_argument("outcome", metavar="changes_requested")
    oc.add_argument("--by")
    oc.add_argument("--role")
    oc.add_argument("--ref")
    oc.add_argument("--reason")
    oc.add_argument("--kind", choices=["gate", "plan-exception"], default="gate")
    oc.add_argument("--date", help="ISO 8601 with time and zone (default: now)")
    lnp = sub.add_parser("lane", parents=[common], help="set (at init), raise or lower (human) a change's lane")
    lnp.add_argument("change")
    lnp.add_argument("action", choices=["set", "raise", "lower"])
    lnp.add_argument("lane")
    lnp.add_argument("--answers", help="set: JSON file with the init answers (touches_ui, schema, …)")
    lnp.add_argument("--reason")
    lnp.add_argument("--by")
    lnp.add_argument("--role")
    lnp.add_argument("--ref")
    lev = sub.add_parser("lane-evidence", parents=[common], help="record BUG-NN, finding, regression test (patch/hotfix)")
    lev.add_argument("change")
    lev.add_argument("--bug")
    lev.add_argument("--finding")
    lev.add_argument("--regression-test", dest="regression_test")
    lck = sub.add_parser("lane-check", parents=[common], help="measure the diff against the lane (QA / QA-lite)")
    lck.add_argument("change")
    lck.add_argument("--base", required=True, help="the integration ref the change branches from")
    lck.add_argument("--head", default="HEAD")
    lck.add_argument("--finding", help="the F-NN QA opened for the exceeded criteria")
    dr = sub.add_parser("deploy-record", parents=[common], help="append a deploys[] entry (env, version, verification)")
    dr.add_argument("change")
    dr.add_argument("--env")
    dr.add_argument("--version")
    dr.add_argument("--verification")
    dr.add_argument("--rollback", help="the rollback taken, if any")
    dr.add_argument("--evidence", help="path of the deploy evidence (e.g. deploy_evidence.md)")
    dr.add_argument("--date", help="ISO 8601 with time and zone (default: now)")
    cp = sub.add_parser("check-prod", parents=[common], help="is a human prod approval recorded? (prod-gate)")
    cp.add_argument("change")
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
