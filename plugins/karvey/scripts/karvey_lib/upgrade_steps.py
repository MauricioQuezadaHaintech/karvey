"""The check / fix functions of the project-upgrade step catalogue (``upgrade-steps.json``).

Every function is **pure**: it reads the project only through the read-only ``Probe`` it is given and
returns a ``StepResult`` (planned edits, never writes). Only ``upgrade.py`` writes. Lint check L-38
walks the AST of every function in ``REGISTRY`` and fails on any direct write (``open(..., 'w')``,
``os.remove``, ``shutil``, ``subprocess``, ``atomicio.write_*``) and on a non-human fix that reads
the user's home.

Signatures: ``check(probe, params) -> StepResult`` · ``fix(probe, params, values) -> StepResult``.
"""
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


REGISTRY = {
    "schema_migrate_check": schema_migrate_check,
    "schema_migrate_fix": schema_migrate_fix,
    "schema_migrate_proposed_check": schema_migrate_proposed_check,
    "schema_migrate_proposed_fix": schema_migrate_proposed_fix,
}
