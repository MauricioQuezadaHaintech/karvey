"""Load lists, citation graph, closure and sizes (architecture §1.3, C-01; REQ-W3-001, 071, 072).

One measure for the baseline, the after snapshot and CI (F-49, F-56): a file's citations are the rule,
adapter and reference paths its text names **outside code fences and outside footnote definitions**, plus the
entries of its ``Load:`` line when it has one. The size of a phase is the size of its skill plus the transitive
closure of what it cites.

- ``parse_load(text)`` → ``(line, entries)`` of the ``Load:`` line in the first 15 lines after the frontmatter;
  ``declared(text)`` → the entries (``None`` when there is no line).
- ``cited(text)`` → the sorted citation tokens (fences, footnote definitions and frontmatter excluded).
- ``graph(rules_dir)`` → ``{rule: [ref, …]}`` for every rule under ``rules_dir`` (same exclusions).
- ``closure(direct, graph, mode)`` → sorted files, breadth first, cycle-safe.
- ``size(path)`` → ``{bytes, words, tokens_est, tokens_quality: "estimated"}``.

A ``ref`` is ``(alternatives, conditional)``: ``alternatives`` is the tuple of files a placeholder path
(``adapters/{tool}.md``) can be, ``conditional`` marks a ``Load:`` entry ending in ``?``. Mode ``max`` takes the
largest alternative and every conditional entry; mode ``min`` the smallest and none (F-48).
Standard library only; no clock, no absolute path in any result.
"""
import math
import os
import re
from pathlib import Path

LOAD_RE = re.compile(r"^Load:\s*(.*?)\s*$")
LOAD_WINDOW = 15
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
FOOTNOTE_DEF_RE = re.compile(r"^\s*\[\^[^\]]+\]:")
TOKEN_RE = re.compile(r"[A-Za-z0-9_{}./-]+\.md")
PLACEHOLDER_RE = re.compile(r"\{[^{}/]*\}")
TOKENS_QUALITY = "estimated"


# --------------------------------------------------------------------------- text
def split_frontmatter(text):
    """``(body_lines, offset)``: the lines after a leading ``---`` YAML block and how many lines it took."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1:], i + 1
    return lines, 0


def parse_load(text):
    """``(line_number, [entry, …])`` of the ``Load:`` line, or ``None`` when there is none."""
    body, off = split_frontmatter(text)
    for i, line in enumerate(body[:LOAD_WINDOW]):
        m = LOAD_RE.match(line)
        if m:
            entries = [e.strip().strip("`") for e in m.group(1).split(",")]
            return off + i + 1, [e for e in entries if e]
    return None


def declared(text):
    """The ``Load:`` entries in order (a trailing ``?`` kept), or ``None`` when the text has no line."""
    p = parse_load(text)
    return None if p is None else p[1]


def prose_lines(text):
    """``[(line_number, line)]`` outside the frontmatter, code fences and footnote definitions."""
    body, off = split_frontmatter(text)
    out, fence = [], None
    for i, line in enumerate(body):
        m = FENCE_RE.match(line)
        if m:
            mark = m.group(1)[0] * 3
            if fence is None:
                fence = mark
            elif mark == fence:
                fence = None
            continue
        if fence is not None or FOOTNOTE_DEF_RE.match(line):
            continue
        out.append((off + i + 1, line))
    return out


def cited(text):
    """Sorted, de-duplicated citation tokens of the text (``Load:`` entries included, ``?`` stripped)."""
    toks = set()
    for _, line in prose_lines(text):
        if LOAD_RE.match(line):
            continue
        toks.update(TOKEN_RE.findall(line))
    for e in declared(text) or []:
        toks.add(e.rstrip("?"))
    return sorted(toks)


# --------------------------------------------------------------------------- resolution
def _rules_rel(token):
    """The part of a token relative to ``skills/karvey/rules`` (or ``None`` when it names no rule path)."""
    if "rules/" in token:
        return token.rsplit("rules/", 1)[1]
    return None


def resolve(token, rules_dir, base_dir=None):
    """The files a citation token can name (sorted tuple, empty when none exists).

    ``…rules/x.md`` and bare ``x.md`` / ``judges/x.md`` are relative to ``rules_dir``; ``adapters/…`` too;
    ``references/…`` to ``base_dir`` (the citing skill's folder). A ``{placeholder}`` matches any name."""
    rules_dir = Path(rules_dir)
    tok = token.strip().rstrip("?").strip("`")
    rel = _rules_rel(tok)
    if rel is not None:
        base, rel_path = rules_dir, rel
    elif tok.startswith("references/"):
        base, rel_path = Path(base_dir) if base_dir else rules_dir.parent, tok
    elif tok.startswith("../") or tok.startswith("/"):
        return ()
    else:
        base, rel_path = rules_dir, tok
    if PLACEHOLDER_RE.search(rel_path):
        pattern = PLACEHOLDER_RE.sub("*", rel_path)
        return tuple(sorted(p for p in base.glob(pattern) if p.is_file()))
    p = base / rel_path
    return (p,) if p.is_file() else ()


def refs_of(text, rules_dir, base_dir=None):
    """``[(alternatives, conditional)]`` of a text: prose citations (unconditional) and ``Load:`` entries."""
    out = {}
    for _, line in prose_lines(text):
        if LOAD_RE.match(line):
            continue
        for tok in TOKEN_RE.findall(line):
            alts = resolve(tok, rules_dir, base_dir)
            if alts:
                out[alts] = False
    for e in declared(text) or []:
        alts = resolve(e, rules_dir, base_dir)
        if alts:
            cond = e.endswith("?")
            out[alts] = out.get(alts, cond) and cond
    return sorted(out.items(), key=lambda kv: ([str(p) for p in kv[0]], kv[1]))


def missing_load_entries(text, rules_dir, base_dir=None):
    """``[(line, entry)]`` of ``Load:`` entries that name no existing file (REQ-W3-072)."""
    p = parse_load(text)
    if p is None:
        return []
    line, entries = p
    return [(line, e) for e in entries if not resolve(e, rules_dir, base_dir)]


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return ""


def rule_files(rules_dir):
    d = Path(rules_dir)
    return sorted(p for p in d.rglob("*.md") if p.is_file()) if d.is_dir() else []


def graph(rules_dir):
    """``{rule_path: [ref, …]}`` for every rule (and adapter) under ``rules_dir``."""
    rules_dir = Path(rules_dir)
    g = {}
    for p in rule_files(rules_dir):
        g[p] = [r for r in refs_of(read_text(p), rules_dir, p.parent) if p not in r[0] or len(r[0]) > 1]
    return g


# --------------------------------------------------------------------------- sizes and closure
def size(path):
    """``{bytes, words, tokens_est, tokens_quality}`` of one file (words without YAML frontmatter)."""
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raw = b""
    text = raw.decode("utf-8", "replace")
    if text.startswith("﻿"):
        text = text[1:]
    body, _ = split_frontmatter(text)
    words = sum(len(ln.split()) for ln in body)
    return {"bytes": len(raw), "words": words, "tokens_est": int(math.ceil(len(raw) / 4.0)),
            "tokens_quality": TOKENS_QUALITY}


def total(paths):
    """The summed size of several files (``tokens_est`` from the summed bytes)."""
    b = w = 0
    for p in paths:
        s = size(p)
        b += s["bytes"]
        w += s["words"]
    return {"bytes": b, "words": w, "tokens_est": int(math.ceil(b / 4.0)), "tokens_quality": TOKENS_QUALITY}


def pick(ref, mode):
    """The file a ref contributes in ``mode`` (``None`` for a conditional entry in ``min``)."""
    alts, cond = ref
    if cond and mode == "min":
        return None
    if len(alts) == 1:
        return alts[0]
    ranked = sorted(alts, key=lambda p: (size(p)["bytes"], str(p)))
    return ranked[-1] if mode == "max" else ranked[0]


def closure(direct, g, mode="max"):
    """Sorted files reachable from ``direct`` refs through ``g`` (breadth first, cycle-safe)."""
    seen, queue = set(), []
    for ref in direct:
        f = pick(ref, mode)
        if f is not None and f not in seen:
            seen.add(f)
            queue.append(f)
    while queue:
        cur = queue.pop(0)
        for ref in g.get(cur, []):
            f = pick(ref, mode)
            if f is not None and f not in seen:
                seen.add(f)
                queue.append(f)
    return sorted(seen, key=str)


def rel(path, root):
    """``path`` relative to ``root`` with forward slashes (never absolute)."""
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return os.path.basename(str(path))


def measure_skill(plugin_dir, skill_md, g=None):
    """One size row for a skill file, plus the issues of its ``Load:`` line (missing files)."""
    plugin_dir = Path(plugin_dir)
    rules_dir = plugin_dir / "skills" / "karvey" / "rules"
    g = graph(rules_dir) if g is None else g
    text = read_text(skill_md)
    refs = [r for r in refs_of(text, rules_dir, Path(skill_md).parent)]
    direct_files = sorted({f for f in (pick(r, "max") for r in refs) if f is not None}, key=str)
    row = {"skill": Path(skill_md).parent.name, "has_load_line": parse_load(text) is not None,
           "own": size(skill_md), "direct": total(direct_files),
           "direct_files": [rel(p, plugin_dir) for p in direct_files]}
    for mode in ("min", "max"):
        files = closure(refs, g, mode)
        row["closure_%s" % mode] = total([Path(skill_md)] + [f for f in files if f != Path(skill_md)])
        row["closure_%s_files" % mode] = [rel(p, plugin_dir) for p in files]
    issues = [{"skill": row["skill"], "line": line, "file": entry,
               "message": "%s:%d: Load: names %s, which does not exist" % (rel(skill_md, plugin_dir), line, entry)}
              for line, entry in missing_load_entries(text, rules_dir, Path(skill_md).parent)]
    return row, issues


def first_diff(a, b):
    """``None`` when two outputs are equal, else ``(line_number, line_a, line_b)`` of the first difference."""
    if a == b:
        return None
    la, lb = a.splitlines(), b.splitlines()
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else "<end of output>"
        y = lb[i] if i < len(lb) else "<end of output>"
        if x != y:
            return i + 1, x, y
    return len(la) + 1, "<end of output>", "<end of output>"
