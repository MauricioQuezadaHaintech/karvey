"""The project design system and a change's design delta (architecture §1.18, C-18; REQ-W3-035, 036, 038, 076).

``docs/spec/design-system.md`` — one per project::

    ## Colour            (also Type, Spacing, Radius, Motion: any table whose header has Token and Light)
    | Token | Light | Dark | Changed by |
    | `--color-primary` | `#2b4256` | `#a3bfd8` | first-ui-change |

    ## Components
    | Component | Changed by |

    ## Pairs             (text/background token pairs and their WCAG target; default AA normal)
    | Text token | Background token | Level |
    | `--color-text-primary` | `--color-background` | AAA normal |

A ``Dark`` cell that is empty, ``—`` or ``=`` means the light value. A value ``= other-token`` (or ``= --other``)
refers to another token of the same scheme. A design-spec colour table (``Light (hex · OKLCH)``) parses too: the
first value of the cell (before ``·``) is taken.

``docs/spec/changes/{id}/design-delta.md`` — what a change adds or modifies::

    ## Added
    | Token | Scheme | Base value | New value |
    ## Modified
    | Token | Scheme | Base value | New value |      (Base value = the design system's value when design ran)
    ## Components
    | Component | Action |                           (added | modified)

``Scheme`` is ``light``, ``dark`` or ``both`` (the default when the column is absent). A delta with no row says
``empty`` on a line of its own. Colours: ``#rgb``, ``#rrggbb``, ``rgb()`` and ``oklch()`` (CSS Color 4). Stdlib only.
"""
import math
import re

SCHEMES = ("light", "dark")
LEVELS = {("AA", "normal"): 4.5, ("AA", "large"): 3.0, ("AAA", "normal"): 7.0, ("AAA", "large"): 4.5,
          ("UI", "normal"): 3.0}
DEFAULT_LEVEL = ("AA", "normal")
_TOKEN = re.compile(r"^--[A-Za-z0-9][\w-]*$")
_NONE = ("", "—", "-", "=", "–")


class DesignError(ValueError):
    """An unparseable value or row; ``token`` names the token."""

    def __init__(self, token, message):
        self.token = token
        super().__init__(message)


# --------------------------------------------------------------------------- tables
def _cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def _tables(text):
    """``[(section heading, [header lower-case], [row dicts with 'line'])]`` of the Markdown tables."""
    out, head, rows, section = [], None, None, ""
    for n, line in enumerate((text or "").splitlines(), 1):
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            section = m.group(1).strip()
        if not line.lstrip().startswith("|"):
            if head is not None:
                out.append((tsec, head, rows))
            head, rows = None, None
            continue
        cells = _cells(line)
        if head is None:
            head, rows, tsec = [c.lower() for c in cells], [], section
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        r = dict(zip(head, cells))
        r["line"] = n
        rows.append(r)
    if head is not None:
        out.append((tsec, head, rows))
    return out


def _col(head, prefix):
    return next((h for h in head if h == prefix or h.startswith(prefix + " ") or h.startswith(prefix + "(")), None)


def _token(cell):
    t = (cell or "").strip().strip("`").strip()
    return t if _TOKEN.match(t) else None


def value_of(cell):
    """The value a cell declares: the first code span, else the text before ``·``; ``None`` when empty."""
    c = (cell or "").strip()
    m = re.search(r"`([^`]+)`", c)
    v = m.group(1) if m else c.split("·")[0]
    v = v.strip()
    return None if v in _NONE else v


def _alias(value):
    """``= text-secondary`` / ``= --color-accent`` → the token it refers to, else None."""
    m = re.match(r"^=\s*(--)?([A-Za-z][\w-]*)$", (value or "").strip())
    if not m:
        return None
    return ("--" if m.group(1) else "") + m.group(2)


def parse(text):
    """``{tokens: {name: {light, dark, changed_by, line}}, pairs: [{text, background, level, line}],
    components: [{name, changed_by, line}]}`` of a design-system (or design-spec) file."""
    tokens, pairs, comps = {}, [], []
    for section, head, rows in _tables(text):
        light, dark = _col(head, "light"), _col(head, "dark")
        if "token" in head and light:
            for r in rows:
                name = _token(r.get("token"))
                if not name:
                    continue
                lv, dv = value_of(r.get(light)), value_of(r.get(dark)) if dark else None
                raw_l, raw_d = (r.get(light) or "").strip(), (r.get(dark) or "").strip() if dark else ""
                if raw_l.startswith("="):
                    lv = raw_l
                if raw_d.startswith("=") and raw_d != "=":
                    dv = raw_d
                tokens[name] = {"light": lv, "dark": dv, "changed_by": value_of(r.get("changed by")), "line": r["line"]}
        elif "token" in head and "value" in head:  # a one-value table (motion, spacing)
            for r in rows:
                name = _token(r.get("token"))
                if name:
                    v = value_of(r.get("value"))
                    tokens[name] = {"light": v, "dark": None, "changed_by": value_of(r.get("changed by")),
                                    "line": r["line"]}
        elif "text token" in head and "background token" in head:
            for r in rows:
                t, b = _token(r.get("text token")), _token(r.get("background token"))
                if t and b:
                    pairs.append({"text": t, "background": b, "level": parse_level(r.get("level")), "line": r["line"]})
        elif head and head[0] == "component":
            for r in rows:
                name = (r.get("component") or "").strip().strip("`")
                if name:
                    comps.append({"name": name, "changed_by": value_of(r.get("changed by")),
                                  "action": (r.get("action") or "").strip().lower() or None, "line": r["line"]})
    return {"tokens": tokens, "pairs": pairs, "components": comps}


def parse_level(cell):
    """``AA`` / ``AAA`` / ``UI`` × ``normal`` / ``large`` from a Level cell; AA normal when undeclared."""
    c = (cell or "").upper()
    lvl = "AAA" if "AAA" in c else ("AA" if "AA" in c else ("UI" if re.search(r"\bUI\b|NON-TEXT", c) else None))
    size = "large" if "LARGE" in c else "normal"
    return (lvl, size) if lvl else DEFAULT_LEVEL


def resolved(tokens, name, scheme):
    """The value of ``name`` in ``scheme`` with dark falling back to light and ``= alias`` followed."""
    seen = set()
    cur = name
    while True:
        if cur in seen:
            raise DesignError(name, "%s: alias cycle" % name)
        seen.add(cur)
        t = tokens.get(cur)
        if t is None:
            raise DesignError(name, "%s: token not declared" % cur)
        v = t.get(scheme) if scheme == "dark" and t.get("dark") else t.get("light")
        a = _alias(v) if v and v.startswith("=") else None
        if not a:
            return v
        cur = a if a.startswith("--") else next((k for k in ("--" + a, "--color-" + a) if k in tokens),
                                                 next((k for k in sorted(tokens) if k.endswith("-" + a)), "--" + a))


# --------------------------------------------------------------------------- delta
def parse_delta(text):
    """``{empty, added: [{token, scheme, base, new, line}], modified: [...], components: [{name, action}]}``."""
    out = {"added": [], "modified": [], "components": [], "empty": False}
    for section, head, rows in _tables(text):
        sec = section.lower()
        if "token" in head and ("new value" in head):
            kind = "modified" if "modif" in sec else "added"
            for r in rows:
                name = _token(r.get("token"))
                if not name:
                    continue
                sch = (r.get("scheme") or "both").strip().lower() or "both"
                out[kind].append({"token": name, "scheme": sch, "base": value_of(r.get("base value")),
                                  "new": value_of(r.get("new value")), "line": r["line"]})
        elif head and head[0] == "component":
            for r in rows:
                name = (r.get("component") or "").strip().strip("`")
                if name:
                    out["components"].append({"name": name, "action": (r.get("action") or "added").strip().lower()})
    has_rows = out["added"] or out["modified"] or out["components"]
    out["empty"] = not has_rows and bool(re.search(r"^\s*`?empty`?\s*$", text or "", re.M | re.I))
    return out


# --------------------------------------------------------------------------- colour
def _clamp(x):
    return max(0.0, min(1.0, x))


def _num(s, pct_scale=1.0):
    s = s.strip()
    if s.endswith("%"):
        return float(s[:-1]) / 100.0 * pct_scale
    return float(s)


def parse_color(value, token="?"):
    """``(r, g, b)`` in 0..1 sRGB for ``#rgb``, ``#rrggbb``, ``rgb()`` or ``oklch()``; else ``DesignError`` naming
    the token."""
    v = (value or "").strip().lower()
    try:
        m = re.match(r"^#([0-9a-f]{3}|[0-9a-f]{6})$", v)
        if m:
            h = m.group(1)
            if len(h) == 3:
                h = "".join(c * 2 for c in h)
            return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        m = re.match(r"^rgba?\(\s*([^)]*)\)$", v)
        if m:
            parts = [p for p in re.split(r"[\s,/]+", m.group(1)) if p][:3]
            if len(parts) == 3:
                return tuple(_clamp(_num(p, 255.0) / 255.0) for p in parts)
        m = re.match(r"^oklch\(\s*([^)]*)\)$", v)
        if m:
            parts = [p for p in re.split(r"[\s/]+", m.group(1)) if p][:3]
            if len(parts) == 3:
                L = _num(parts[0]) if parts[0].endswith("%") else float(parts[0])
                C = _num(parts[1], 0.4)
                H = float(parts[2].replace("deg", ""))
                return oklch_to_srgb(L, C, H)
    except ValueError:
        pass
    raise DesignError(token, "%s: colour %r cannot be parsed (#rgb, #rrggbb, rgb(), oklch())" % (token, value))


def oklch_to_srgb(L, C, H):
    """OKLCH → gamma-encoded sRGB (0..1, clipped), with the CSS Color 4 OKLab matrices."""
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    lin = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)

    def enc(x):
        x = _clamp(x)
        return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    return tuple(enc(x) for x in lin)


def luminance(rgb):
    """WCAG 2.x relative luminance of a 0..1 sRGB triple."""
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    la, lb = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def passed_levels(ratio, size="normal"):
    """The WCAG levels a ratio reaches for a text size (``["AA", "AAA"]``, ``["AA"]`` or ``[]``)."""
    return [lvl for lvl in ("AA", "AAA") if ratio + 1e-9 >= LEVELS[(lvl, size)]]


# --------------------------------------------------------------------------- diff (REQ-W3-036)
def _norm(v):
    return re.sub(r"\s+", "", (v or "").lower())


def _covers(rows, token, scheme):
    return any(r["token"] == token and r["scheme"] in ("both", scheme) for r in rows)


def diff(system, spec, delta):
    """Compare a design-spec's tokens and components with the design system and the declared delta.

    Returns ``{added, modified, components, undeclared, empty}``: the computed additions and modifications (with
    the system's value as the base) and ``undeclared`` — every modification (or addition) the delta does not
    declare (``undeclared modification: --color-primary``)."""
    st, sp = system["tokens"], spec["tokens"]
    added, modified, undeclared = [], [], []
    for name in sorted(sp):
        for sch in SCHEMES:
            new = sp[name].get(sch) if sch == "light" or sp[name].get("dark") else None
            if new is None:
                continue
            if name not in st:
                if sch == "light":
                    added.append({"token": name, "light": sp[name].get("light"), "dark": sp[name].get("dark")})
                    if not _covers(delta["added"], name, "light"):
                        undeclared.append("undeclared addition: %s" % name)
                continue
            base = st[name].get(sch) if sch == "light" or st[name].get("dark") else st[name].get("light")
            if _norm(base) == _norm(new):
                continue
            modified.append({"token": name, "scheme": sch, "base": base, "new": new})
            if not _covers(delta["modified"], name, sch):
                msg = "undeclared modification: %s" % name
                if msg not in undeclared:
                    undeclared.append(msg)
    have = {c["name"].lower() for c in system["components"]}
    declared = {c["name"].lower() for c in delta["components"]}
    comps = [c["name"] for c in spec["components"] if c["name"].lower() not in have]
    for c in comps:
        if c.lower() not in declared:
            undeclared.append("undeclared component: %s" % c)
    empty = not (added or modified or comps or delta["added"] or delta["modified"] or delta["components"])
    return {"added": added, "modified": modified, "components": comps, "undeclared": undeclared, "empty": empty}
