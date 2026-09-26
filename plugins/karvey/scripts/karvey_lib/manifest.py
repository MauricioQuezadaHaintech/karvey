"""Commit → change mapping for the release manifest (architecture §1.9 of wave2-structural, A-12).

Every commit in ``base..head`` is mapped to one change id:

- ``trailer``: its ``Karvey-Change`` trailer, one value matching the change-id pattern;
- ``merge``: a merge commit with no trailer of its own, when every commit it brings in maps to the same change;
- ``path``: a commit that only touches ``docs/spec/changes/{id}/**`` (spec bookkeeping).

Anything else is ``unmapped`` with its reason. Read-only (``gitlog``), standard library only.
"""
import re

from . import gitlog

CHANGE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
_SPEC_PATH = re.compile(r"^docs/spec/changes/([a-z0-9][a-z0-9-]{1,62})/")
NOT_A_CHANGE = frozenset({"archive"})


class ManifestError(Exception):
    """git could not answer (bad ref, not a repository, timeout)."""


def parse_trailers(values):
    """``(change | None, reason | None)`` from the trailer values of one commit."""
    vals = [v.strip() for v in values or [] if v and v.strip()]
    if not vals:
        return None, "no Karvey-Change trailer"
    distinct = sorted(set(vals))
    if len(distinct) > 1:
        return None, "several Karvey-Change values: %s" % ", ".join(distinct)
    v = distinct[0]
    if not CHANGE_ID.match(v) or v in NOT_A_CHANGE:
        return None, "malformed Karvey-Change value %r (a change id: ^[a-z0-9][a-z0-9-]{1,62}$)" % v[:80]
    return v, None


def path_change(paths):
    """The change id when every path is under ``docs/spec/changes/{id}/`` of one change, else None."""
    ids = set()
    for p in paths or []:
        m = _SPEC_PATH.match(p)
        if not m or m.group(1) in NOT_A_CHANGE:
            return None
        ids.add(m.group(1))
    return ids.pop() if len(ids) == 1 else None


def _side_commits(root, parents):
    """Commits a merge brings in: reachable from its other parents, not from the first."""
    out = []
    for p in parents[1:]:
        text = gitlog.run(["rev-list", "%s..%s" % (gitlog.check_ref(parents[0]), gitlog.check_ref(p))], root)
        out.extend(x.strip() for x in text.splitlines() if x.strip())
    return out


def map_commits(root, base, head="HEAD"):
    """``{base, head, commits, changes, unmapped}`` for ``base..head`` (oldest first).

    ``commits``: ``[{sha, subject, change, mapped_by, reason}]``; ``changes``: ``{id: [sha]}`` in order;
    ``unmapped``: ``[{sha, subject, reason}]``. Raises :class:`ManifestError` when git cannot answer."""
    try:
        commits = gitlog.log_trailers(root, "%s..%s" % (gitlog.check_ref(base), gitlog.check_ref(head)))
    except gitlog.GitLogError as exc:
        raise ManifestError(str(exc))
    rows, by_sha, merges = [], {}, []
    for c in commits:
        change, reason = parse_trailers(c["trailers"])
        row = {"sha": c["sha"], "subject": c["subject"], "change": change,
               "mapped_by": "trailer" if change else None, "reason": reason}
        if change is None and not c["trailers"]:
            if len(c["parents"]) > 1:
                merges.append((row, c["parents"]))
            else:
                try:
                    pc = path_change(gitlog.changed_paths(root, c["sha"]))
                except gitlog.GitLogError as exc:
                    raise ManifestError(str(exc))
                if pc:
                    row.update(change=pc, mapped_by="path", reason=None)
        rows.append(row)
        by_sha[c["sha"]] = row
    for row, parents in merges:
        try:
            side = _side_commits(root, parents)
        except gitlog.GitLogError as exc:
            raise ManifestError(str(exc))
        got = {by_sha[s]["change"] if s in by_sha else None for s in side}
        if side and len(got) == 1 and None not in got:
            row.update(change=got.pop(), mapped_by="merge", reason=None)
        elif side:
            named = sorted(x for x in got if x)
            row["reason"] = "merge commit without a trailer whose merged commits map to %s" % (
                ", ".join(named + (["unmapped"] if None in got else [])) or "nothing")
        else:
            row["reason"] = "merge commit without a trailer that brings in no commit"
    changes, unmapped = {}, []
    for row in rows:
        if row["change"]:
            changes.setdefault(row["change"], []).append(row["sha"])
        else:
            unmapped.append({"sha": row["sha"], "subject": row["subject"], "reason": row["reason"]})
    return {"base": base, "head": head, "commits": rows, "changes": changes, "unmapped": unmapped}
