"""The check / fix functions of the project-upgrade step catalogue (``upgrade-steps.json``).

Every function is **pure**: it reads the project only through the read-only ``Probe`` it is given and
returns a ``StepResult`` (planned edits, never writes). Only ``upgrade.py`` writes. Lint check L-38
walks the AST of every function in ``REGISTRY`` and fails on any direct write (``open(..., 'w')``,
``os.remove``, ``shutil``, ``subprocess``, ``atomicio.write_*``) and on a non-human fix that reads
the user's home.

Signatures: ``check(probe, params) -> StepResult`` · ``fix(probe, params, values) -> StepResult``.
"""
import difflib
import json

from .upgrade import CheckFailed, Edit, StepResult

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


REGISTRY = {
    "schema_migrate_check": schema_migrate_check,
    "schema_migrate_fix": schema_migrate_fix,
    "schema_migrate_proposed_check": schema_migrate_proposed_check,
    "schema_migrate_proposed_fix": schema_migrate_proposed_fix,
    "legacy_shims_check": legacy_shims_check,
    "legacy_shims_fix": legacy_shims_fix,
}
