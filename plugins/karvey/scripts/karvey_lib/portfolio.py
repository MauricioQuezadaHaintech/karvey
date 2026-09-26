"""The organisation portfolio: validated entries and bounded, read-only file reads (architecture §1.20, C-20;
REQ-W3-045, 047, 048).

``portfolio.json`` = ``{"repos": [{path, clone?, client, owner?}]}`` (``schemas/portfolio.schema.json``). Every
``path`` is validated **before any read**: a string with no control or shell characters, absolute or relative to
the portfolio file's directory, whose real path is a directory. ``clone`` is kept and shown, never used.

Reading is **file reads only** (``open`` / ``os.scandir``): no subprocess, no git, no socket; each read is capped at
2 MB. Every text taken from another repository goes through ``sanitise`` (control characters and ANSI escape
sequences removed, 200 characters at most) before it is printed. Stdlib only.
"""
import json
import os
import re
from pathlib import Path

from . import project as pj
from . import safe_values as sv
from . import schema_lite as sl

READ_MAX = 2 * 1024 * 1024
TEXT_MAX = 200
NOT_KARVEY = "not a Karvey project"
_ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-Z\\-_])")
_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


class NotRead(Exception):
    """A repository or file that is not read; ``str()`` is the reason shown after ``not read:``."""


def sanitise(text, limit=TEXT_MAX):
    """Foreign text made safe to print: ANSI escapes and control characters removed, whitespace folded, capped."""
    t = _ANSI.sub("", str(text if text is not None else ""))
    t = _CTRL.sub("", t.replace("\t", " ").replace("\n", " ").replace("\r", " "))
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= limit else t[:limit - 1] + "…"


def read_text(path, limit=READ_MAX):
    """A file's text, at most ``limit`` bytes; ``NotRead`` with the reason otherwise."""
    try:
        size = os.stat(str(path)).st_size
        if size > limit:
            raise NotRead("file too large")
        with open(str(path), "rb") as fh:
            raw = fh.read(limit + 1)
    except PermissionError:
        raise NotRead("permission denied")
    except FileNotFoundError:
        raise NotRead("missing")
    except OSError as exc:
        raise NotRead(exc.strerror or type(exc).__name__)
    if len(raw) > limit:
        raise NotRead("file too large")
    return raw.decode("utf-8-sig", errors="replace").replace("\r\n", "\n")


def read_json(path, limit=READ_MAX):
    try:
        return json.loads(read_text(path, limit))
    except ValueError:
        raise NotRead("invalid JSON")


def load(file):
    """``(entries, problems)`` of a portfolio file. Each entry is validated before anything else is read:
    ``{index, path, abs, clone, client, owner, state}`` with ``state`` ``ok`` or ``not read: {reason}``."""
    file = Path(file)
    data = read_json(file)
    issues = [i for i in sl.validate(data, sl.load_registry()["karvey:portfolio.schema.json"], file=file.name)
              if i["severity"] == "error"]
    problems = [i["message"] for i in issues]
    entries = []
    for n, e in enumerate((data or {}).get("repos") or [] if isinstance(data, dict) else []):
        if not isinstance(e, dict):
            continue
        entries.append(validate_entry(e, file.parent, n))
    return entries, problems


def validate_entry(e, base, index=0):
    """One entry, validated before any read (REQ-W3-045): the path's characters, then its real path."""
    out = {"index": index, "path": e.get("path"), "abs": None, "clone": e.get("clone"),
           "client": sanitise(e.get("client") or "unassigned", 80), "owner": sanitise(e.get("owner") or "", 80),
           "state": "ok"}
    raw = e.get("path")
    try:
        sv.check_common(raw, key="portfolio.repos[%d].path" % index, kind="path")
    except sv.UnsafeValue as exc:
        out["state"] = "not read: invalid path (%s)" % exc.rule
        out["path"] = sanitise(raw, 80)
        return out
    p = Path(raw)
    if not p.is_absolute():
        p = Path(base) / p
    real = Path(os.path.realpath(str(p)))
    if not real.is_dir():
        out["state"] = "not read: no local clone" if e.get("clone") else "not read: invalid path (not a directory)"
        return out
    if not os.access(str(real), os.R_OK | os.X_OK):
        out["state"] = "not read: permission denied"
        return out
    out["abs"] = str(real)
    return out


def repo_changes(abs_path):
    """``(layout, note, changes)`` of a repository by file reads only; ``NotRead`` when it cannot be read.
    ``changes`` = ``[{id, spec}]`` for the active ones (not archived, not implemented), sorted by id."""
    root = Path(abs_path)
    try:
        if not pj.is_karvey_project(root):
            raise NotRead(NOT_KARVEY)
        rel, layout, note = pj.spec_layout(root)
        base = root / rel / "changes"
        entries = sorted(os.scandir(str(base)), key=lambda d: d.name) if base.is_dir() else []
    except PermissionError:
        raise NotRead("permission denied")
    out = []
    for d in entries:
        if not d.is_dir() or d.name == pj.ARCHIVE_NAME or d.name.startswith("."):
            continue
        if os.path.exists(os.path.join(d.path, pj.IMPLEMENTED_MARKER)):
            continue
        try:
            spec = read_json(os.path.join(d.path, "spec.json"))
        except NotRead as exc:
            out.append({"id": d.name, "spec": None, "error": str(exc)})
            continue
        if not isinstance(spec, dict) or spec.get("phase") in pj.INACTIVE_PHASES:
            continue
        out.append({"id": d.name, "spec": spec, "error": None})
    return layout, note, out
