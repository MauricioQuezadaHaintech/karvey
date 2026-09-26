#!/usr/bin/env python3
"""karvey-contrast-check.py — WCAG 2.x contrast of every declared token pair (architecture §1.18, C-18; REQ-W3-038).

    karvey-contrast-check.py [--file PATH | --delta CHANGE] [--root DIR] [--json]

- ``--file`` (default ``docs/spec/design-system.md``): the pairs table of that file, both schemes.
- ``--delta CHANGE``: the design system with the change's ``design-delta.md`` new values applied, plus any pair the
  delta declares — what the design would look like after archive.

Each pair (``Text token | Background token | Level``, AA normal when undeclared) is computed per scheme (light,
dark) with the WCAG relative luminance; the result lists the ratio, the target, the levels reached (``AA``,
``AAA``) and every pair below its target. A colour that cannot be parsed (``#rgb``, ``#rrggbb``, ``rgb()``,
``oklch()``) is named and the exit is 1 — a value is never assumed. Pairs below target are reported with exit 0
while the ``design.contrast`` check is advisory or warn, exit 1 when a project makes it blocking.

Exit: 0 · 1 unparseable colour (or below target in blocking mode) · 2 usage · 4 file not found. Read-only, stdlib.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import designsys as ds, modes, project as pj  # noqa: E402

TOOL = "karvey-contrast-check"
SYSTEM = pj.SPEC_DIR / "design-system.md"


def load(args, root):
    """``(tokens, pairs, source)`` for the requested scope; raises FileNotFoundError naming the file."""
    if args.delta:
        dpath = Path(root) / pj.CHANGES_DIR / args.delta / "design-delta.md"
        if not dpath.is_file():
            raise FileNotFoundError(str(dpath))
        spath = Path(root) / SYSTEM
        base = ds.parse(spath.read_text(encoding="utf-8-sig")) if spath.is_file() else ds.parse("")
        delta = ds.parse_delta(dpath.read_text(encoding="utf-8-sig"))
        tokens = {k: dict(v) for k, v in base["tokens"].items()}
        for row in delta["added"] + delta["modified"]:
            t = tokens.setdefault(row["token"], {"light": None, "dark": None, "changed_by": args.delta, "line": 0})
            for sch in (ds.SCHEMES if row["scheme"] == "both" else (row["scheme"],)):
                t[sch] = row["new"]
        extra = ds.parse(dpath.read_text(encoding="utf-8-sig"))["pairs"]
        return tokens, base["pairs"] + extra, "%s + %s" % (SYSTEM.as_posix(), dpath.relative_to(root).as_posix())
    p = Path(args.file) if args.file else Path(root) / SYSTEM
    if not p.is_absolute() and args.file:
        p = Path(os.getcwd()) / p
    if not p.is_file():
        raise FileNotFoundError(str(p))
    parsed = ds.parse(p.read_text(encoding="utf-8-sig"))
    return parsed["tokens"], parsed["pairs"], p.name


def check(tokens, pairs):
    """``(rows, below, errors)`` over every pair and scheme."""
    rows, below, errors, bad = [], [], [], set()
    colours = {}

    def colour(name, scheme):
        key = (name, scheme)
        if key not in colours:
            colours[key] = ds.parse_color(ds.resolved(tokens, name, scheme), name)
        return colours[key]
    for name in sorted(tokens):  # every colour token must parse, not only the paired ones
        if not name.startswith("--color-"):
            continue
        for sch in ds.SCHEMES:
            try:
                colour(name, sch)
            except ds.DesignError as exc:
                if exc.token not in bad:
                    bad.add(exc.token)
                    errors.append(str(exc))
    for p in pairs:
        for sch in ds.SCHEMES:
            try:
                ratio = ds.contrast(colour(p["text"], sch), colour(p["background"], sch))
            except ds.DesignError as exc:
                if exc.token not in bad:
                    bad.add(exc.token)
                    errors.append(str(exc))
                continue
            lvl, size = p["level"]
            target = ds.LEVELS[(lvl, size)]
            r = {"text": p["text"], "background": p["background"], "scheme": sch, "ratio": round(ratio, 2),
                 "level": "%s %s" % (lvl, size), "target": target, "passed": ds.passed_levels(ratio, size),
                 "ok": ratio + 1e-9 >= target}
            rows.append(r)
            if not r["ok"]:
                below.append(r)
    return rows, below, errors


def run(args):
    root = pj.find_root(start=os.getcwd(), root=args.root) or Path(args.root or os.getcwd())
    try:
        tokens, pairs, source = load(args, root)
    except FileNotFoundError as exc:
        return kl.EXIT_NOT_FOUND, None, [kl.issue("contrast.not_found", "not found: %s" % exc)]
    rows, below, errors = check(tokens, pairs)
    mode = modes.resolve(root=root, check_id="design.contrast")["mode"]
    res = {"source": source, "pairs": len(pairs), "rows": rows, "below": below, "mode": mode,
           "unparseable": errors}
    if errors:
        return kl.EXIT_FINDINGS, res, [kl.issue("contrast.unparseable", e) for e in errors]
    if below and modes.would_refuse(mode):
        return kl.EXIT_FINDINGS, res, [kl.issue("contrast.below", "%d pair(s) below target" % len(below))]
    return kl.EXIT_OK, res, []


def render(res):
    L = ["contrast — %s (%d pair(s) × light, dark)" % (res["source"], res["pairs"])]
    for r in res["rows"]:
        L.append("%-6s %s on %s: %.2f:1 · target %s (%.1f) · %s%s" % (
            r["scheme"], r["text"], r["background"], r["ratio"], r["level"], r["target"],
            " and ".join(r["passed"]) + " passed" if r["passed"] else "no level passed",
            "" if r["ok"] else " · BELOW TARGET"))
    for e in res["unparseable"]:
        L.append("UNPARSEABLE " + e)
    L.append("%d below target (design.contrast: %s)" % (len(res["below"]), res["mode"]))
    return "\n".join(L)


def build_parser():
    p = argparse.ArgumentParser(prog="karvey-contrast-check.py", description="WCAG contrast of declared token pairs")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--file", help="a design-system file (default docs/spec/design-system.md)")
    g.add_argument("--delta", metavar="CHANGE", help="the design system with this change's delta applied")
    p.add_argument("--root")
    p.add_argument("--json", action="store_true")
    return p


def main(argv=None):
    parser = build_parser()
    as_json = "--json" in (argv if argv is not None else sys.argv[1:])
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else kl.EXIT_USAGE
        if code != 0 and as_json:
            kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", "invalid arguments")]), True)
        return kl.EXIT_USAGE if code != 0 else 0
    code, res, errors = run(args)
    return kl.emit(kl.envelope(TOOL, code, result=res, errors=errors), args.json,
                   human=render(res) if res else "; ".join(e["message"] for e in errors))


if __name__ == "__main__":
    sys.exit(main())
