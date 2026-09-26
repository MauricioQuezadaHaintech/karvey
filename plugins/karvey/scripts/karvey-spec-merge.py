#!/usr/bin/env python3
"""karvey-spec-merge.py — deterministic spec-delta merge (architecture §1.9, wave1-hardening).

    karvey-spec-merge.py <change> [--capability NAME] [--date YYYY-MM-DD] [--dry-run] [--root DIR] [--json]

Merges ``docs/spec/changes/<change>/spec-delta.md`` into the living spec
``docs/spec/specs/<capability>/spec.md`` (REQ-W1-065, REQ-W1-066). Python >= 3.9, stdlib only.

Delta format (the one ``karvey-requirements`` writes):

- three level-2 sections ``## ADDED Requirements``, ``## MODIFIED Requirements``,
  ``## REMOVED Requirements`` (any may be absent, at least one must exist);
- the unit is one requirement item: a bullet starting ``- **<ID>**`` plus its indented
  continuation lines;
- ADDED keeps its ``###`` group headings and their prose; a group heading ``### ADDED by …`` only
  carries prose for the top of the merged section;
- MODIFIED: ``### Requirement: <ID>`` followed by the item keyed by that id (HTML comments
  between them are the reason, never copied);
- REMOVED: a bullet ``- **<ID>** — <reason>``, or ``### Requirement: <ID>`` followed by the reason.

Behaviour:

- ADDED → appended under ``## ADDED by `<change>` (<version>, merged <date>)``. An id already
  present with the same text is a no-op; the same id with other text is a conflict.
- MODIFIED → replaced in place by id. A missing id is an error: nothing is written.
- REMOVED → the item becomes ``- ~~**<ID>**~~ — REMOVED by `<change>` (<date>): <reason>``. A second
  run is a no-op; a missing id is an error.
- ``--dry-run`` prints the unified diff and writes nothing.

Exit: 0 applied or no-op · 1 conflict / missing id (nothing written) · 2 usage · 3 unparsable delta
(with the line number) or a file over 5 MB · 4 file missing · 5 internal.
"""
import argparse
import difflib
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import atomicio, project as pj  # noqa: E402

TOOL = "karvey-spec-merge"
MAX_BYTES = 5 * 1024 * 1024
SECTIONS = {"ADDED Requirements": "added", "MODIFIED Requirements": "modified",
            "REMOVED Requirements": "removed"}
_ID = r"[A-Z][A-Z0-9]*(?:-[A-Za-z0-9]+)+"
ITEM_RE = re.compile(r"^- \*\*(" + _ID + r")\*\*")
STRUCK_RE = re.compile(r"^- ~~\*\*(" + _ID + r")\*\*~~")
LOOSE_ITEM_RE = re.compile(r"^- (?:~~)?\*\*")
REQ_HEADING_RE = re.compile(r"^### Requirement:\s*(\S+)\s*$")
H2_RE = re.compile(r"^## (?!#)(.*?)\s*$")
H3_RE = re.compile(r"^### (?!#)(.*?)\s*$")
VERSION_RE = re.compile(r"^ADDED by `[^`]+`\s*\(([^),]+)")


class ParseError(Exception):
    def __init__(self, line, message):
        super().__init__("line %d: %s" % (line, message))
        self.line = line


class NotFound(Exception):
    pass


class Refused(Exception):
    pass


class Usage(Exception):
    pass


# --------------------------------------------------------------------------- items
class Item:
    __slots__ = ("id", "lines", "line", "struck")

    def __init__(self, rid, lines, line, struck=False):
        self.id = rid
        self.lines = lines          # the bullet line + its continuation lines, without newlines
        self.line = line            # 1-based line number of the bullet
        self.struck = struck

    @property
    def text(self):
        return "\n".join(self.lines)

    @property
    def norm(self):
        return " ".join(" ".join(self.lines).split())


def _is_continuation(line):
    return bool(line.strip()) and line[:1] in (" ", "\t")


def read_item(lines, i):
    """The item whose bullet is ``lines[i]``: ``(lines, next_index)``."""
    j = i + 1
    while j < len(lines) and _is_continuation(lines[j]):
        j += 1
    return lines[i:j], j


def index_items(lines):
    """``{id: Item}`` of every requirement item of a living spec (struck ones included)."""
    out = {}
    i = 0
    while i < len(lines):
        m = ITEM_RE.match(lines[i]) or STRUCK_RE.match(lines[i])
        if m:
            body, j = read_item(lines, i)
            if m.group(1) not in out:
                out[m.group(1)] = Item(m.group(1), body, i + 1, struck=lines[i].startswith("- ~~"))
            i = j
        else:
            i += 1
    return out


# --------------------------------------------------------------------------- delta
def _strip_comments(lines, start):
    """Skip blank lines and ``<!-- … -->`` blocks from ``start``; return ``(comment_text, index)``."""
    i, comment = start, []
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("<!--"):
            while i < len(lines):
                comment.append(lines[i].strip())
                if "-->" in lines[i]:
                    i += 1
                    break
                i += 1
            continue
        break
    text = " ".join(comment).replace("<!--", "").replace("-->", "").strip()
    return text, i


def parse_delta(text):
    """``{"added": [group…], "modified": [Item…], "removed": [(Item|None, id, reason, line)…],
    "version": str|None}``. A group is ``{"heading", "prose", "items"}``. Raises ParseError."""
    lines = text.splitlines()
    res = {"added": [], "modified": [], "removed": [], "version": None, "sections": []}
    section, i = None, 0
    group = None
    seen = set()
    while i < len(lines):
        line = lines[i]
        h2 = H2_RE.match(line)
        if h2 and not line.startswith("###"):
            name = h2.group(1)
            section = SECTIONS.get(name)
            if section:
                if section in res["sections"]:
                    raise ParseError(i + 1, "section '## %s' appears twice" % name)
                res["sections"].append(section)
            group = None
            i += 1
            continue
        if section is None:
            i += 1
            continue
        if section == "added":
            h3 = H3_RE.match(line)
            if h3:
                heading = h3.group(1)
                vm = VERSION_RE.match(heading)
                if vm and res["version"] is None:
                    res["version"] = vm.group(1).strip()
                group = {"heading": None if heading.startswith("ADDED by ") else heading,
                         "prose": [], "items": []}
                res["added"].append(group)
                i += 1
                continue
            if LOOSE_ITEM_RE.match(line):
                m = ITEM_RE.match(line)
                if not m:
                    raise ParseError(i + 1, "requirement item without a valid id: %r" % line[:60])
                if m.group(1) in seen:
                    raise ParseError(i + 1, "%s appears twice in the delta" % m.group(1))
                seen.add(m.group(1))
                body, j = read_item(lines, i)
                if group is None:
                    group = {"heading": None, "prose": [], "items": []}
                    res["added"].append(group)
                group["items"].append(Item(m.group(1), body, i + 1))
                i = j
                continue
            if group is not None and line.strip() and not group["items"]:
                group["prose"].append(line)
            elif line.strip() and group is None:
                group = {"heading": None, "prose": [line], "items": []}
                res["added"].append(group)
            i += 1
            continue
        if section == "modified":
            h = REQ_HEADING_RE.match(line)
            if h:
                rid = h.group(1)
                _, j = _strip_comments(lines, i + 1)
                m = ITEM_RE.match(lines[j]) if j < len(lines) else None
                if not m or m.group(1) != rid:
                    raise ParseError(i + 1, "'### Requirement: %s' is not followed by the item '- **%s**'"
                                     % (rid, rid))
                if rid in seen:
                    raise ParseError(i + 1, "%s appears twice in the delta" % rid)
                seen.add(rid)
                body, k = read_item(lines, j)
                res["modified"].append(Item(rid, body, j + 1))
                i = k
                continue
            if LOOSE_ITEM_RE.match(line):
                m = ITEM_RE.match(line)
                if not m:
                    raise ParseError(i + 1, "requirement item without a valid id: %r" % line[:60])
                if m.group(1) in seen:
                    raise ParseError(i + 1, "%s appears twice in the delta" % m.group(1))
                seen.add(m.group(1))
                body, k = read_item(lines, i)
                res["modified"].append(Item(m.group(1), body, i + 1))
                i = k
                continue
            if line.startswith("### "):
                raise ParseError(i + 1, "MODIFIED expects '### Requirement: <ID>', got %r" % line[:60])
            i += 1
            continue
        if section == "removed":
            h = REQ_HEADING_RE.match(line)
            if h:
                rid = h.group(1)
                comment, j = _strip_comments(lines, i + 1)
                reason = []
                while j < len(lines) and lines[j].strip() and not lines[j].startswith("#") \
                        and not LOOSE_ITEM_RE.match(lines[j]):
                    reason.append(lines[j].strip())
                    j += 1
                why = " ".join(reason) or comment
                why = re.sub(r"^Reason:\s*", "", why).strip()
                if not why:
                    raise ParseError(i + 1, "REMOVED %s has no reason" % rid)
                if rid in seen:  # BUG-45
                    raise ParseError(i + 1, "%s appears twice in the delta" % rid)
                seen.add(rid)
                res["removed"].append((rid, why, i + 1))
                i = j
                continue
            if LOOSE_ITEM_RE.match(line):
                m = ITEM_RE.match(line)
                if not m:
                    raise ParseError(i + 1, "requirement item without a valid id: %r" % line[:60])
                body, j = read_item(lines, i)
                why = " ".join(" ".join(body).split())[len(m.group(0)):].strip()
                why = re.sub(r"^[—:\-–]+\s*", "", why).strip()
                if not why:
                    raise ParseError(i + 1, "REMOVED %s has no reason" % m.group(1))
                if m.group(1) in seen:  # BUG-45
                    raise ParseError(i + 1, "%s appears twice in the delta" % m.group(1))
                seen.add(m.group(1))
                res["removed"].append((m.group(1), why, i + 1))
                i = j
                continue
            if line.startswith("### "):
                raise ParseError(i + 1, "REMOVED expects '### Requirement: <ID>' or a bullet, got %r" % line[:60])
            i += 1
            continue
    if not res["sections"]:
        raise ParseError(1, "no '## ADDED Requirements', '## MODIFIED Requirements' or "
                            "'## REMOVED Requirements' section")
    return res


# --------------------------------------------------------------------------- merge
def merge(target_text, delta, change, version, date):
    """``(new_text, report, errors)``; ``errors`` non-empty means nothing may be written."""
    lines = target_text.splitlines()
    trailing_nl = target_text.endswith("\n") or not target_text
    items = index_items(lines)
    report = {"added": [], "modified": [], "removed": [], "noop": [], "conflicts": [], "missing": []}
    errors = []

    # MODIFIED and REMOVED are applied in place, by line range, bottom-up.
    edits = []  # (start_index, end_index, replacement_lines)
    for it in delta["modified"]:
        cur = items.get(it.id)
        if cur is None or cur.struck:
            report["missing"].append(it.id)
            errors.append(kl.issue("merge.missing_id", "MODIFIED %s is not in the living spec%s"
                                   % (it.id, " (it was removed)" if cur else ""), path=it.id,
                                   got="absent" if cur is None else "removed"))
            continue
        if cur.norm == it.norm:
            report["noop"].append(it.id)
            continue
        edits.append((cur.line - 1, cur.line - 1 + len(cur.lines), list(it.lines)))
        report["modified"].append(it.id)
    for rid, why, _line in delta["removed"]:
        cur = items.get(rid)
        if cur is None:
            report["missing"].append(rid)
            errors.append(kl.issue("merge.missing_id", "REMOVED %s is not in the living spec" % rid, path=rid,
                                   got="absent"))
            continue
        if cur.struck:
            report["noop"].append(rid)
            continue
        edits.append((cur.line - 1, cur.line - 1 + len(cur.lines),
                      ["- ~~**%s**~~ — REMOVED by `%s` (%s): %s" % (rid, change, date, why)]))
        report["removed"].append(rid)

    # ADDED: new ids only; an existing id must carry the same text.
    new_groups = []
    for grp in delta["added"]:
        fresh = []
        for it in grp["items"]:
            cur = items.get(it.id)
            if cur is None:
                fresh.append(it)
                report["added"].append(it.id)
            elif not cur.struck and cur.norm == it.norm:
                report["noop"].append(it.id)
            else:
                report["conflicts"].append(it.id)
                errors.append(kl.issue("merge.conflict", "ADDED %s already exists in the living spec (line %d) "
                                       "with different text" % (it.id, cur.line), path=it.id,
                                       expected=it.norm[:120], got=cur.norm[:120]))
        new_groups.append((grp, fresh))
    if errors:
        return None, report, errors

    ordered = sorted(edits, key=lambda e: e[0])
    for (s1, e1, _), (s2, _e2, _) in zip(ordered, ordered[1:]):
        if s2 < e1:  # BUG-45: overlapping edits would delete a neighbour
            return None, report, [kl.issue("merge.overlap", "edits overlap at lines %d-%d of the living spec"
                                           % (s1 + 1, e1), path="line %d" % (s2 + 1))]
    for start, end, repl in reversed(ordered):
        lines[start:end] = repl

    if any(fresh for _, fresh in new_groups):
        prefix = "## ADDED by `%s`" % change
        existing = next((k for k, ln in enumerate(lines) if ln.startswith(prefix)), None)
        block = []
        if existing is None:
            head = prefix + (" (%s, merged %s)" % (version, date) if version else " (merged %s)" % date)
            block += ["", head]
            for grp, fresh in new_groups:
                if grp["heading"] is None and grp["prose"]:
                    block += [""] + grp["prose"]
            for grp, fresh in new_groups:
                if grp["heading"] is None and not grp["items"]:
                    continue
                if grp["heading"] is not None:
                    block += ["", "### " + grp["heading"]]
                    if grp["prose"]:
                        block += [""] + grp["prose"]
                if fresh:
                    block += [""]
                    for it in fresh:
                        block += it.lines
            while lines and not lines[-1].strip():
                lines.pop()
            lines += block
        else:
            # The change's section exists (a delta that grew): append the new items at its end.
            end = next((k for k in range(existing + 1, len(lines)) if H2_RE.match(lines[k])
                        and not lines[k].startswith("###")), len(lines))
            while end > existing + 1 and not lines[end - 1].strip():
                end -= 1
            for grp, fresh in new_groups:
                if not fresh:
                    continue
                if grp["heading"] is not None:
                    block += ["", "### " + grp["heading"]]
                block += [""]
                for it in fresh:
                    block += it.lines
            lines[end:end] = block
    out = "\n".join(lines)
    if trailing_nl and out:
        out += "\n"
    return out, report, errors


# --------------------------------------------------------------------------- CLI
def change_dir(root, change):
    if not change or "/" in change or "\\" in change or change.startswith("."):
        raise Usage("invalid change id %r" % (change,))
    base = Path(root) / pj.CHANGES_DIR
    d = base / change
    if d.is_dir():
        return d
    arch = base / pj.ARCHIVE_NAME
    if arch.is_dir():
        hits = sorted(x for x in arch.iterdir() if x.is_dir() and (x.name == change or x.name.endswith("-" + change)))
        if hits:
            return hits[-1]
    raise NotFound("change %r not found under %s" % (change, os.path.relpath(str(base), str(root))))


def _read_text(path):
    p = Path(path)
    try:
        size = p.stat().st_size
    except FileNotFoundError:
        raise NotFound("not found: %s" % p)
    if size > MAX_BYTES:
        raise Refused("%s is larger than 5 MB (%d bytes); refused" % (p, size))
    try:
        raw = p.read_bytes()
    except OSError as exc:
        raise NotFound("unreadable: %s (%s)" % (p, exc))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise NotFound("not UTF-8: %s (%s)" % (p, exc))
    style = {"bom": raw.startswith(b"\xef\xbb\xbf"), "crlf": b"\r\n" in raw}  # BUG-38
    return text.replace("\r\n", "\n"), atomicio.sha256_bytes(raw), style


def _capability(cdir, override):
    if override:
        if not re.match(r"^[a-z0-9][a-z0-9._-]*$", override):
            raise Usage("invalid capability %r" % override)
        return override
    try:
        data = atomicio.read_json(cdir / "spec.json").data
    except atomicio.ReadError as exc:
        raise NotFound("cannot read the capability from spec.json (%s); pass --capability" % exc)
    cap = data.get("capability") if isinstance(data, dict) else None
    if not isinstance(cap, str) or not re.match(r"^[a-z0-9][a-z0-9._-]*$", cap):
        raise NotFound("spec.json has no valid 'capability'; pass --capability")
    return cap


def run(args):
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None:
        raise NotFound("not a Karvey project (no docs/spec/project.json or docs/spec/changes/)")
    cdir = change_dir(root, args.change)
    delta_path = cdir / "spec-delta.md"
    delta_text, _, _ = _read_text(delta_path)
    try:
        delta = parse_delta(delta_text)
    except ParseError as exc:
        raise Refused("%s: %s" % (os.path.relpath(str(delta_path), str(root)), exc))
    cap = _capability(cdir, args.capability)
    target = Path(root) / pj.SPEC_DIR / "specs" / cap / "spec.md"
    if target.is_file():
        target_text, sha, style = _read_text(target)
    else:
        target_text, sha, style = "# Living spec — capability `%s`\n" % cap, None, {"bom": False, "crlf": False}
    date = args.date or datetime.now().astimezone().date().isoformat()
    new_text, report, errors = merge(target_text, delta, args.change, delta.get("version"), date)
    rel_target = os.path.relpath(str(target), str(root)).replace(os.sep, "/")
    result = {"change": args.change, "capability": cap, "target": rel_target, "dry_run": bool(args.dry_run)}
    result.update(report)
    if errors:
        for e in errors:
            e["file"] = rel_target
        return kl.EXIT_FINDINGS, result, errors, "nothing written: " + "; ".join(e["message"] for e in errors)
    changed = new_text != (target_text if sha is not None else "")
    diff = "".join(difflib.unified_diff(
        (target_text if sha is not None else "").splitlines(True), new_text.splitlines(True),
        fromfile="a/" + rel_target, tofile="b/" + rel_target))
    result["diff"] = diff
    result["changed"] = changed
    summary = "added %d · modified %d · removed %d · unchanged %d" % (
        len(report["added"]), len(report["modified"]), len(report["removed"]), len(report["noop"]))
    if not changed:
        return kl.EXIT_OK, result, [], "%s: already up to date (%s)" % (rel_target, summary)
    if args.dry_run:
        return kl.EXIT_OK, result, [], diff + "\n(dry run, nothing written) %s" % summary
    target.parent.mkdir(parents=True, exist_ok=True)
    out_text = new_text.replace("\n", "\r\n") if style["crlf"] else new_text
    atomicio.write_text_atomic(target, ("\ufeff" if style["bom"] else "") + out_text, expected_sha256=sha)
    return kl.EXIT_OK, result, [], "%s merged into %s (%s)" % (args.change, rel_target, summary)


def build_parser():
    p = argparse.ArgumentParser(prog="karvey-spec-merge.py", description=__doc__.split("\n\n")[0])
    p.add_argument("change", help="change id (docs/spec/changes/<change>/spec-delta.md)")
    p.add_argument("--capability", help="living-spec capability (default: spec.json:capability)")
    p.add_argument("--date", help="merge date YYYY-MM-DD (default: today)")
    p.add_argument("--dry-run", action="store_true", help="print the unified diff, write nothing")
    p.add_argument("--root", help="Karvey project root (default: walk up from the cwd)")
    p.add_argument("--json", action="store_true", help="print one JSON envelope")
    return p


def main(argv=None):
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else kl.EXIT_USAGE
        if code != 0 and as_json:
            kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", "invalid arguments")]), True)
        return kl.EXIT_USAGE if code != 0 else 0
    try:
        if args.date and not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
            raise Usage("--date must be YYYY-MM-DD")
        code, result, errors, human = run(args)
    except Usage as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", str(exc))]), args.json)
    except Refused as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, errors=[kl.issue("merge.refused", str(exc))]), args.json)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("merge.not_found", str(exc))]),
                       args.json)
    except (atomicio.LockBusy, atomicio.CASConflict) as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, errors=[kl.issue("merge.concurrent", str(exc))]),
                       args.json)
    except Exception as exc:  # pragma: no cover - last resort, exit 5
        return kl.emit(kl.envelope(TOOL, kl.EXIT_INTERNAL,
                                   errors=[kl.issue("internal", "%s: %s" % (type(exc).__name__, exc))]),
                       args.json)
    if args.json:
        return kl.emit(kl.envelope(TOOL, code, result=result, errors=errors), True)
    # errors are already in the human text; print it and exit.
    stream = sys.stdout if code == kl.EXIT_OK else sys.stderr
    stream.write(human.rstrip("\n") + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
