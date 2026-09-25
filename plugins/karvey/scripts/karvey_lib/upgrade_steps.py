"""The check / fix functions of the project-upgrade step catalogue (``upgrade-steps.json``).

Every function is **pure**: it reads the project only through the read-only ``Probe`` it is given and
returns a ``StepResult`` (planned edits, never writes). Only ``upgrade.py`` writes. Lint check L-38
walks the AST of every function in ``REGISTRY`` and fails on any direct write (``open(..., 'w')``,
``os.remove``, ``shutil``, ``subprocess``, ``atomicio.write_*``) and on a non-human fix that reads
the user's home.

Signatures: ``check(probe, params) -> StepResult`` · ``fix(probe, params, values) -> StepResult``.
"""
import copy
import difflib
import json
import re

from . import safe_values as sv
from .upgrade import CheckFailed, Edit, NeedsInput, StepResult

PROJECT_JSON = "docs/spec/project.json"


# --------------------------------------------------------------------------- 1–2 schema-migrate(-proposed)
def _spec_files(probe):
    """Every ``spec.json`` under ``docs/spec`` (archive included) and ``docs/spec/project.json``."""
    files = [f for f in probe.glob("docs/spec/**/spec.json")]
    if probe.exists(PROJECT_JSON):
        files.append(PROJECT_JSON)
    return files


def _migrate(probe, proposed):
    """``(edits, needs_human)``: the state tool's own ``fix_spec`` / ``fix_project`` run in memory, exact tier
    (``proposed`` False) or what the proposed tier adds on top of it (``proposed`` True)."""
    st = probe.state
    edits, human = [], []
    for rel in _spec_files(probe):
        probe.check_deadline()
        try:
            doc = probe.read_json(rel)
        except CheckFailed as exc:
            human.append("%s: %s" % (rel, exc))
            continue
        data = doc.data
        if not isinstance(data, dict):
            human.append("%s: not a JSON object" % rel)
            continue
        v = data.get("schema_version")
        if isinstance(v, int) and not isinstance(v, bool) and v > st.SCHEMA_VERSION:
            human.append("%s: schema_version %d is newer than this Karvey" % (rel, v))
            continue
        fixer = st.fix_project if rel == PROJECT_JSON else st.fix_spec
        try:
            exact, _ = fixer(data, False)
            if proposed:
                new, _ = fixer(data, True)
                if new == exact:
                    continue  # the proposed tier adds nothing to this file
            else:
                new = exact
        except st.Unmigratable as exc:
            human.append("%s: %s" % (rel, exc))
            continue
        if new != data:
            edits.append(Edit("write", rel, before_sha256=doc.sha256, text=doc.dumps(new)))
    return edits, human


def _migrate_result(edits, human, tier, report_human=True):
    warnings = ["needs a human: %s" % h for h in human] if report_human else []
    tail = ""
    if human and report_human:
        tail = "; %d file%s need%s a human" % (len(human), "" if len(human) == 1 else "s",
                                                "s" if len(human) == 1 else "")
    if edits:
        return StepResult("applies", summary="migrate %d file%s (%s tier): %s%s" % (
            len(edits), "" if len(edits) == 1 else "s", tier, ", ".join(e.path for e in edits), tail),
            edits=edits, warnings=warnings)
    if human and report_human:
        return StepResult("human", summary=tail[2:],
                          instructions="These files cannot be migrated automatically; the owner picks the value:\n"
                                       + "\n".join("  - " + h for h in human), warnings=warnings)
    return StepResult("nothing")


def schema_migrate_check(probe, params):
    edits, human = _migrate(probe, proposed=False)
    return _migrate_result(edits, human, "exact")


def schema_migrate_fix(probe, params, values):
    return schema_migrate_check(probe, params)


def schema_migrate_proposed_check(probe, params):
    edits, human = _migrate(probe, proposed=True)
    return _migrate_result(edits, human, "proposed", report_human=False)


def schema_migrate_proposed_fix(probe, params, values):
    return schema_migrate_proposed_check(probe, params)



# --------------------------------------------------------------------------- 3 legacy-shims
SHIMS = {"plan-gate.sh": "plan_gate_hook", "git-flow-guard.sh": "git_flow_hook"}
SHIPPED_SHIMS = "skills/karvey/hooks/"
SETTINGS_FILES = (".claude/settings.json", ".claude/settings.local.json")


def _strip_hook_entries(data, names):
    """``(new_data, removed)``: ``data["hooks"]`` without the command entries that name one of ``names``;
    empty groups, events and an empty ``hooks`` object are dropped."""
    if not isinstance(data, dict) or not isinstance(data.get("hooks"), dict):
        return data, 0
    new = json.loads(json.dumps(data))
    removed = 0
    for event in list(new["hooks"]):
        groups = new["hooks"][event]
        if not isinstance(groups, list):
            continue
        keep_groups = []
        for grp in groups:
            if isinstance(grp, dict) and isinstance(grp.get("hooks"), list):
                kept = [h for h in grp["hooks"] if not (isinstance(h, dict) and isinstance(h.get("command"), str)
                                                        and any(n in h["command"] for n in names))]
                removed += len(grp["hooks"]) - len(kept)
                if not kept:
                    continue
                grp = dict(grp, hooks=kept)
            keep_groups.append(grp)
        if keep_groups:
            new["hooks"][event] = keep_groups
        else:
            del new["hooks"][event]
    if not new["hooks"]:
        del new["hooks"]
    return new, removed


def legacy_shims_check(probe, params):
    known = params.get("known_sha256") or {}
    copies, edited = [], []
    for name in SHIMS:
        for rel in probe.glob(".claude/**/" + name):
            if probe.sha256(rel) in (known.get(name) or []):
                copies.append((name, rel))
            else:
                edited.append((name, rel))
    diffs = []
    for name, rel in edited:
        shipped = probe.plugin_read(SHIPPED_SHIMS + name) or ""
        diffs.append("".join(difflib.unified_diff(shipped.splitlines(True), (probe.read_text(rel) or "").splitlines(True),
                                                  fromfile="shipped/" + name, tofile=rel)))
    doc = probe.read_json(PROJECT_JSON) if copies else None
    if copies and (doc is None or not isinstance(doc.data, dict)):
        edited += copies
        copies = []
        diffs.append("(no readable docs/spec/project.json to carry enforcement.* — run /karvey:karvey-init "
                     "--settings first)\n")
    if not copies:
        if not edited:
            return StepResult("nothing")
        return StepResult("human", summary="%d locally edited shim cop%s: review by hand" % (
            len(edited), "y" if len(edited) == 1 else "ies"), diff="".join(diffs),
            instructions="These copies differ from every shipped version; nothing is deleted. Keep your change "
                         "or remove the copy and set project.json:enforcement.* yourself.")
    edits = [Edit("delete", rel, before_sha256=probe.sha256(rel)) for _, rel in copies]
    names = sorted({name for name, _ in copies})
    removed_entries = 0
    for sf in SETTINGS_FILES:
        sdoc = probe.read_json(sf)
        if sdoc is None:
            continue
        new, n = _strip_hook_entries(sdoc.data, names)
        if n:
            removed_entries += n
            edits.append(Edit("write", sf, before_sha256=sdoc.sha256, text=sdoc.dumps(new)))
    pdata = json.loads(json.dumps(doc.data))
    enf = pdata.get("enforcement") if isinstance(pdata.get("enforcement"), dict) else {}
    flags = []
    for name in names:
        key = SHIMS[name]
        if enf.get(key) is not True:
            enf[key] = True
            flags.append("enforcement.%s = true" % key)
    if flags:
        pdata["enforcement"] = enf
        edits.append(Edit("write", PROJECT_JSON, before_sha256=doc.sha256, text=doc.dumps(pdata)))
    summary = "remove %s%s%s" % (", ".join(rel for _, rel in copies),
                                  " + %d settings entr%s" % (removed_entries, "y" if removed_entries == 1 else "ies")
                                  if removed_entries else "",
                                  "; " + ", ".join(flags) if flags else "")
    res = StepResult("applies", summary=summary, edits=edits, diff="".join(diffs))
    if edited:
        res.warnings.append("%d locally edited cop%s left for a human" % (len(edited), "y" if len(edited) == 1
                                                                          else "ies"))
    return res


def legacy_shims_fix(probe, params, values):
    return legacy_shims_check(probe, params)



# --------------------------------------------------------------------------- 4 team-settings
INIT_SETTINGS = "/karvey:karvey-init --settings"
PLACEHOLDER = re.compile(r"^<[^<>]+>$")


def _no_project_json():
    return StepResult("needs-input", summary="no docs/spec/project.json: run %s (settings only)" % INIT_SETTINGS,
                      inputs_needed=["project.json (run %s)" % INIT_SETTINGS],
                      instructions="The team settings live in docs/spec/project.json; %s creates it, asking the "
                                   "person for each value." % INIT_SETTINGS)


def _project(probe):
    doc = probe.read_json(PROJECT_JSON)
    if doc is not None and not isinstance(doc.data, dict):
        raise CheckFailed("docs/spec/project.json is not a JSON object")
    return doc


def _placeholders(node, path=""):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            out += _placeholders(v, "%s.%s" % (path, k) if path else k)
    elif isinstance(node, str) and PLACEHOLDER.match(node):
        out.append(path)
    return out


def _set_value(blocks, key, value):
    top, _, rest = key.partition(".")
    if top not in blocks or not rest or "." in rest:
        raise sv.UnsafeValue(key, "settings", "not a settable key of the blocks this step adds (%s)"
                             % ", ".join("%s.<key>" % b for b in sorted(blocks)), value)
    blocks[top][rest] = value


def _check_block_values(blocks, cfg):
    """Every value the person gave goes through safe_values for its kind (REQ-UP-019, REQ-W1-093)."""
    nt = blocks.get("notifications")
    if isinstance(nt, dict):
        ch = sv.check_enum(sv.CHANNEL_ALIASES.get(nt.get("channel"), nt.get("channel")), cfg.CHANNELS,
                           "notifications.channel")
        nt["channel"] = ch
        tgt = nt.get("target", "")
        if not (isinstance(tgt, str) and PLACEHOLDER.match(tgt)):
            sv.check_target(ch, tgt, key="notifications.target")
        if nt.get("via") not in (None, ""):
            sv.check_enum(nt["via"], cfg.VIAS, "notifications.via")
        if "events" in nt:
            ev = nt["events"]
            if not isinstance(ev, list) or not all(e in cfg.EVENTS for e in ev):
                raise sv.UnsafeValue("notifications.events", "enum", "a list of %s" % "|".join(cfg.EVENTS), ev)
        if "detail" in nt:
            sv.check_enum(nt["detail"], cfg.DETAILS, "notifications.detail")
    mg = blocks.get("management")
    if isinstance(mg, dict):
        tool = sv.check_enum(cfg.LEGACY_TOOLS.get(mg.get("tool"), mg.get("tool")), cfg.TOOLS, "management.tool")
        loc = mg.get("location")
        if isinstance(loc, str) and not PLACEHOLDER.match(loc) and "{change-id}" not in loc:
            sv.check_location(tool, loc, key="management.location")
        if isinstance(mg.get("sprints"), str) and not PLACEHOLDER.match(mg["sprints"]):
            sv.check_sprints(tool, mg["sprints"], key="management.sprints")


def _team_settings(probe, values):
    doc = _project(probe)
    if doc is None:
        return None, _no_project_json()
    from .karvey_hooks import _settings_gaps
    missing, legacy = _settings_gaps(doc.data)
    change = list(missing) + (["management"] if legacy and "management" not in missing else [])
    if not change:
        return None, StepResult("nothing")
    cfg = probe.config
    settings = cfg.Settings.__new__(cfg.Settings)
    settings.root, settings.project = probe.root, copy.deepcopy(doc.data)
    settings._remote, settings._remote_done, settings.remote_name = None, True, None
    try:
        proposal = cfg.propose_settings(settings, from_legacy=True)
    except cfg.Refused as exc:
        raise CheckFailed(str(exc))
    blocks = {k: copy.deepcopy(proposal["snippet"][k]) for k in change}
    for key, value in (values or {}).items():
        _set_value(blocks, key, value)
    _check_block_values(blocks, cfg)
    new = copy.deepcopy(doc.data)
    new.update(blocks)
    holes = _placeholders(blocks)
    summary = "set %s: %s" % (" + ".join(change), json.dumps(blocks, ensure_ascii=False, sort_keys=True))
    if len(summary) > 240:
        summary = summary[:237] + "..."
    edit = Edit("write", PROJECT_JSON, before_sha256=doc.sha256, text=doc.dumps(new))
    return (holes, edit), StepResult("applies", summary=summary, edits=[edit], warnings=list(proposal["notes"]))


def team_settings_check(probe, params):
    state, res = _team_settings(probe, {})
    if state is None:
        return res
    holes, _ = state
    if holes:
        return StepResult("needs-input", summary=res.summary, inputs_needed=holes, warnings=res.warnings,
                          instructions="Ask the person for: %s (pass them with --values)" % ", ".join(holes))
    return res


def team_settings_fix(probe, params, values):
    state, res = _team_settings(probe, values)
    if state is None:
        if res.status == "needs-input":
            raise NeedsInput("project.json (run %s)" % INIT_SETTINGS)
        return res
    holes, _ = state
    if holes:
        raise NeedsInput(", ".join(holes))
    return res


# --------------------------------------------------------------------------- 5 enforcement-defaults
STANDARDS_SKILL = "/karvey:karvey-standards"


def _enforcement_defaults(probe):
    schema = probe.plugin_json("schemas/project.schema.json")
    props = (((schema.data if schema else {}).get("properties") or {}).get("enforcement") or {}).get("properties") or {}
    return {k: v["x-karvey-default"] for k, v in props.items() if isinstance(v, dict) and "x-karvey-default" in v}


def enforcement_defaults_check(probe, params):
    doc = _project(probe)
    if doc is None:
        return _no_project_json()
    data = doc.data
    enf = data.get("enforcement") if isinstance(data.get("enforcement"), dict) else {}
    missing = {k: v for k, v in _enforcement_defaults(probe).items() if k not in enf}
    warnings = []
    if "standards" not in data:
        templates = params.get("standards") or []
        warnings.append("no engineering standards declared → %s%s" % (
            STANDARDS_SKILL, " (templates: %s)" % ", ".join(templates) if templates else ""))
    if not missing:
        return StepResult("nothing", warnings=warnings)
    new = copy.deepcopy(data)
    new_enf = dict(enf)
    new_enf.update(missing)
    new["enforcement"] = new_enf
    return StepResult("applies", summary="add %s (this version's defaults)" % ", ".join(
        "enforcement.%s = %s" % (k, json.dumps(v)) for k, v in missing.items()),
        edits=[Edit("write", PROJECT_JSON, before_sha256=doc.sha256, text=doc.dumps(new))], warnings=warnings)


def enforcement_defaults_fix(probe, params, values):
    res = enforcement_defaults_check(probe, params)
    if res.status == "needs-input":
        raise NeedsInput("project.json (run %s)" % INIT_SETTINGS)
    return res



# --------------------------------------------------------------------------- 6 statusline-launcher (F-51)
# A plugin cannot declare a statusline and the tool never writes under ~/.claude, so the stable launcher is a
# command the person pastes once. It resolves the newest installed Karvey the same way the deprecated shims do,
# so a plugin update never breaks it. hooks/README.md shows the same text (lint check L-39 compares them).
STABLE_STATUSLINE = ("bash -c 'f=$(ls -1dt \"$HOME\"/.claude/plugins/cache/*/karvey/*/hooks/karvey-statusline.sh "
                     "2>/dev/null | head -1); [ -n \"$f\" ] && exec bash \"$f\"'")
STATUSLINE_BLOCK = {"type": "command", "padding": 0, "command": STABLE_STATUSLINE}
VERSIONED_STATUSLINE = re.compile(r"/karvey/\d+\.\d+\.\d+[^/\s\"']*/hooks/karvey-statusline\.sh")
HOME_SETTINGS = ".claude/settings.json"
HOME_CLAUDE_MD = ".claude/CLAUDE.md"


def _home_json(probe, rel):
    try:
        return probe.home_json(rel)
    except CheckFailed as exc:
        msg = str(exc)
        raise CheckFailed(msg if msg.startswith("unreadable") else "unreadable: %s" % msg)


def _statusline_of(data):
    sl = data.get("statusLine") if isinstance(data, dict) else None
    return sl.get("command") if isinstance(sl, dict) and isinstance(sl.get("command"), str) else None


def statusline_launcher_check(probe, params):
    found = []
    home = _home_json(probe, HOME_SETTINGS)
    if home is not None:
        found.append(("~/" + HOME_SETTINGS, home.data))
    for rel in SETTINGS_FILES:
        try:
            doc = probe.read_json(rel)
        except CheckFailed as exc:
            raise CheckFailed("unreadable: %s" % exc)
        if doc is not None:
            found.append((rel, doc.data))
    kinds = []
    for where, data in found:
        cmd = _statusline_of(data)
        if cmd is None:
            continue
        if "karvey-statusline.sh" in cmd and VERSIONED_STATUSLINE.search(cmd):
            kinds.append(("versioned", where, data))
        elif "karvey-statusline.sh" in cmd or cmd == STABLE_STATUSLINE:
            kinds.append(("stable", where, data))
        else:
            kinds.append(("own", where, data))
    snippet = json.dumps({"statusLine": STATUSLINE_BLOCK}, indent=2)
    versioned = [k for k in kinds if k[0] == "versioned"]
    if versioned:
        _, where, data = versioned[0]
        new = dict(data, statusLine=STATUSLINE_BLOCK)
        diff = "".join(difflib.unified_diff(
            json.dumps({"statusLine": data["statusLine"]}, indent=2).splitlines(True),
            json.dumps({"statusLine": new["statusLine"]}, indent=2).splitlines(True),
            fromfile=where, tofile=where))
        return StepResult("human", summary="statusline on a versioned plugin path (%s): replace it with the stable "
                                           "command" % where, diff=diff + "\n",
                          instructions="Replace statusLine in %s by (Karvey never writes it):\n%s" % (where, snippet))
    if not kinds:
        return StepResult("human", summary="no statusline: the stable Karvey command is available",
                          instructions="Optional: add to ~/.claude/settings.json (Karvey never writes it):\n%s"
                                       % snippet)
    if all(k[0] == "own" for k in kinds):
        return StepResult("nothing", warnings=["own statusline, left as is"])
    return StepResult("nothing")


# --------------------------------------------------------------------------- 7 global-config
KARVEY_HOOK = re.compile(r"(plan-gate\.sh|git-flow-guard\.sh|/karvey/\d+\.\d+\.\d+[^/\s\"']*/)")


def _home_hook_commands(data):
    out = []
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return out
    for event, groups in hooks.items():
        for grp in groups if isinstance(groups, list) else []:
            for h in (grp.get("hooks") if isinstance(grp, dict) and isinstance(grp.get("hooks"), list) else []):
                if isinstance(h, dict) and isinstance(h.get("command"), str):
                    out.append((event, h["command"]))
    return out


def global_config_check(probe, params):
    rec = params.get("recommend") or {}
    home = _home_json(probe, HOME_SETTINGS)
    try:
        claude_md = probe.home_read(HOME_CLAUDE_MD)
    except CheckFailed as exc:
        raise CheckFailed("unreadable: %s" % exc)
    data = home.data if home is not None and isinstance(home.data, dict) else {}
    cmds = _home_hook_commands(data)
    env = data.get("env") if isinstance(data.get("env"), dict) else {}
    before = {"hooks naming Karvey": sorted("%s: %s" % c for c in cmds if KARVEY_HOOK.search(c[1])),
              "env": {k: v for k, v in sorted(env.items()) if k.startswith("KARVEY_")}}
    after = json.loads(json.dumps(before))
    reasons = []
    if after["hooks naming Karvey"]:
        after["hooks naming Karvey"] = []
        reasons.append("hook entries that name a deprecated shim or a versioned plugin path (the plugin's own "
                       "hooks.json already runs every guard)")
    compat = rec.get("compat_marker") or {}
    pat = compat.get("hook_pattern")
    if pat and compat.get("env") and compat["env"] not in env and any(
            re.search(pat, c) and not KARVEY_HOOK.search(c) for _, c in cmds):
        after["env"][compat["env"]] = compat.get("value", "<path>")
        reasons.append("%s, so the approval hook also writes the marker your own plan hook checks" % compat["env"])
    diffs = []
    if before != after:
        diffs.append("".join(difflib.unified_diff(json.dumps(before, indent=2).splitlines(True),
                                                  json.dumps(after, indent=2).splitlines(True),
                                                  fromfile="~/%s (Karvey-related keys only)" % HOME_SETTINGS,
                                                  tofile="~/%s (recommended)" % HOME_SETTINGS)))
    md = rec.get("claude_md_line") or {}
    if claude_md and md.get("when") and md.get("line") and re.search(md["when"], claude_md) \
            and md["line"] not in claude_md:
        diffs.append("--- ~/%s\n+++ ~/%s (recommended)\n@@ end of file @@\n+%s\n" % (HOME_CLAUDE_MD, HOME_CLAUDE_MD,
                                                                                    md["line"]))
        reasons.append("the CLAUDE.md destinations line (destinations come only from project.json)")
    if not diffs:
        return StepResult("nothing")
    return StepResult("human", summary="global configuration: %s" % "; ".join(reasons),
                      diff="\n".join(d.rstrip("\n") for d in diffs) + "\n",
                      instructions="Apply these lines by hand; Karvey never writes under ~/.claude.")


REGISTRY = {
    "schema_migrate_check": schema_migrate_check,
    "schema_migrate_fix": schema_migrate_fix,
    "schema_migrate_proposed_check": schema_migrate_proposed_check,
    "schema_migrate_proposed_fix": schema_migrate_proposed_fix,
    "legacy_shims_check": legacy_shims_check,
    "legacy_shims_fix": legacy_shims_fix,
    "team_settings_check": team_settings_check,
    "team_settings_fix": team_settings_fix,
    "enforcement_defaults_check": enforcement_defaults_check,
    "enforcement_defaults_fix": enforcement_defaults_fix,
    "statusline_launcher_check": statusline_launcher_check,
    "global_config_check": global_config_check,
}
