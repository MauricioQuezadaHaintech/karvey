"""Stub of the dispatcher registry for the lint fixture."""
REGISTRY = [
    Guard("plan-gate", ("pre-bash", "pre-edit"), "closed", False),
    Guard("prod-gate", ("pre-bash",), "closed", True),
]
