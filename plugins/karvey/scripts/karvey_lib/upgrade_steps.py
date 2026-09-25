"""The check / fix functions of the project-upgrade step catalogue (``upgrade-steps.json``).

Every function is **pure**: it reads the project only through the read-only ``Probe`` it is given and
returns a ``StepResult`` (planned edits, never writes). Only ``upgrade.py`` writes. Lint check L-38
walks the AST of every function in ``REGISTRY`` and fails on any direct write (``open(..., 'w')``,
``os.remove``, ``shutil``, ``subprocess``, ``atomicio.write_*``) and on a non-human fix that reads
the user's home.

Signatures: ``check(probe, params) -> StepResult`` · ``fix(probe, params, values) -> StepResult``.
"""


def placeholder_nothing(probe, params):
    """Test-only placeholder of the empty catalogue: never applies (removed with the first real step)."""
    from .upgrade import StepResult
    return StepResult("nothing")


REGISTRY = {
    "placeholder_nothing": placeholder_nothing,
}
