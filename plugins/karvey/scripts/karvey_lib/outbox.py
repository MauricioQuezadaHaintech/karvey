"""Tracker outbox format, shared by ``karvey-config.py outbox`` (the writer) and ``karvey-context.py`` (a reader).

``changes/<id>/tracker-outbox.jsonl`` holds one JSON object per pending operation::

    {"id": "ob-…", "op": "set_status", "args": {…}, "key": …, "parent_key": …, "created_at": …,
     "attempts": N, "last_error": …, "blocked_by": "<id of the parent entry>" | null}

``outbox done`` removes an applied entry; nothing is ever marked done in place. An entry is ``blocked``
only while the entry named by ``blocked_by`` is still in the file (REQ-W1-090), otherwise ``ready``.
Legacy lines with ``done_at`` or ``status: "done"`` are not pending.
"""

FILE = "tracker-outbox.jsonl"


def is_pending(entry):
    return isinstance(entry, dict) and not entry.get("done_at") and entry.get("status") != "done"


def annotate(entries):
    """Copies of ``entries`` with ``state`` (ready | blocked): blocked while its parent entry is pending."""
    pending = {e.get("id") for e in entries}
    out = []
    for e in entries:
        e = dict(e)
        e["state"] = "blocked" if e.get("blocked_by") in pending else "ready"
        out.append(e)
    return out
