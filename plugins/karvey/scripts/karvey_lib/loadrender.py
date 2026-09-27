"""Generated per-phase lists (architecture §1.8, C-07; REQ-W3-012).

The per-phase rule lists are rendered from the skills' ``Load:`` lines and never kept by hand:

- ``routing`` (orchestrator) — phase → skill per lane, from ``state-machine.json`` + ``lanes.json`` (C-06);
- ``load-lists:orchestrator`` (orchestrator) — each loaded rule and the skills that apply it;
- ``load-lists:adapter-used-by`` (every ``rules/adapters/*.md``) — the skills that load the adapter;
- ``load-lists:readme`` (the repository README) — each skill's closed list.

``targets(plugin_dir)`` → ``[(path, block, expected_body)]``; ``block_of(text, name)`` → the current body or
``None``; ``replace(text, name, body)`` → the text with the block rewritten; ``drift(plugin_dir)`` →
``[(path, block, message)]``. Standard library only, deterministic output.
"""
import json
from pathlib import Path

from . import loadlist

ROUTING = "routing"
ORCH = "load-lists:orchestrator"
ADAPTER = "load-lists:adapter-used-by"
README = "load-lists:readme"


def begin(name):
    return "<!-- karvey:generated %s -->" % name


def end(name):
    return "<!-- /karvey:generated %s -->" % name


def block_of(text, name):
    """The body between the block's markers (without the surrounding newlines), or ``None``."""
    b, e = begin(name), end(name)
    if b not in text or e not in text:
        return None
    return text.split(b, 1)[1].split(e, 1)[0].strip("\n")


def replace(text, name, body):
    """``text`` with the block's body replaced (the markers kept); unchanged when the markers are absent."""
    b, e = begin(name), end(name)
    if b not in text or e not in text:
        return text
    head, rest = text.split(b, 1)
    _, tail = rest.split(e, 1)
    inner = "\n" + body + "\n" if body else "\n"
    return head + b + inner + e + tail


def _json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def label(skill):
    return skill[len("karvey-"):] if skill.startswith("karvey-") else skill


def ordered_skills(plugin_dir):
    """``[(skill, [Load: entries])]`` of every skill with a ``Load:`` line: pipeline order, then the others."""
    plugin_dir = Path(plugin_dir)
    machine = _json(plugin_dir / "schemas" / "state-machine.json")
    order = []
    for ph in machine.get("phases", []):
        sk = ph.get("skill")
        if isinstance(sk, str) and sk and sk not in order:
            order.append(sk)
    found = {}
    base = plugin_dir / "skills"
    if base.is_dir():
        for d in sorted(base.iterdir()):
            md = d / "SKILL.md"
            if md.is_file():
                entries = loadlist.declared(loadlist.read_text(md))
                if entries is not None:
                    found[d.name] = entries
    rest = sorted(s for s in found if s not in order and s != "karvey")
    tail = ["karvey"] if "karvey" in found else []
    return [(s, found[s]) for s in [s for s in order if s in found] + rest + tail]


def render_routing(plugin_dir):
    plugin_dir = Path(plugin_dir)
    machine = _json(plugin_dir / "schemas" / "state-machine.json")
    lanes = _json(plugin_dir / "schemas" / "lanes.json").get("lanes", {})
    names = list(lanes)
    out = ["| Phase | Skill | %s |" % " | ".join(names), "|---|---|" + "---|" * len(names)]
    for ph in machine.get("phases", []):
        pid, sk = ph.get("id"), ph.get("skill")
        if not pid or not sk:
            continue
        cells = [lanes[n].get("phases", {}).get(pid, "s") for n in names]
        out.append("| `%s` | `/%s` | %s |" % (pid, sk, " | ".join(cells)))
    return "\n".join(out)


def _rule_entries(skills):
    """``{entry: [skill label, …]}`` for the shared-rule entries (skill references excluded)."""
    out = {}
    for sk, entries in skills:
        for e in entries:
            e = e.rstrip("?")
            if e.startswith("references/"):
                continue
            out.setdefault(e, [])
            if label(sk) not in out[e]:
                out[e].append(label(sk))
    return out


def render_orchestrator(plugin_dir):
    skills = ordered_skills(plugin_dir)
    rows = _rule_entries(skills)
    everyone = len(skills)
    # rule names without ".md": a path here would be a citation of the orchestrator (L-56, the size tool)
    out = ["| Rule | Applies in |", "|---|---|"]
    for e in sorted(rows, key=lambda k: (k != "_core.md", k)):
        who = rows[e]
        name = e[:-3] if e.endswith(".md") else e
        out.append("| `%s` | %s |" % (name, "every skill with a `Load:` line" if len(who) == everyone
                                        else ", ".join(who)))
    return "\n".join(out)


def render_adapter(plugin_dir, adapter_name):
    """The used-by line of ``rules/adapters/{adapter_name}``."""
    who = []
    for sk, entries in ordered_skills(plugin_dir):
        for e in entries:
            e = e.rstrip("?")
            if e in ("adapters/{tool}.md", "adapters/" + adapter_name) and label(sk) not in who:
                who.append(label(sk))
    return "Used by: %s." % (", ".join("`/karvey-%s`" % w if w != "karvey" else "`/karvey`" for w in who)
                              if who else "no skill")


def render_readme(plugin_dir):
    out = ["| Skill | Loads (its closed `Load:` list; `?` = only when its condition holds) |", "|---|---|"]
    for sk, entries in ordered_skills(plugin_dir):
        out.append("| `%s` | %s |" % (sk, ", ".join("`%s`" % e for e in entries)))
    return "\n".join(out)


def readme_path(plugin_dir):
    return Path(plugin_dir).resolve().parent.parent / "README.md"


def targets(plugin_dir):
    """``[(path, block, expected_body)]`` of every generated block this plugin owns."""
    plugin_dir = Path(plugin_dir)
    orch = plugin_dir / "skills" / "karvey" / "SKILL.md"
    out = [(orch, ROUTING, render_routing(plugin_dir)), (orch, ORCH, render_orchestrator(plugin_dir))]
    adapters = plugin_dir / "skills" / "karvey" / "rules" / "adapters"
    if adapters.is_dir():
        for p in sorted(adapters.glob("*.md")):
            out.append((p, ADAPTER, render_adapter(plugin_dir, p.name)))
    out.append((readme_path(plugin_dir), README, render_readme(plugin_dir)))
    return out


def drift(plugin_dir):
    """``[(path, block, message)]``: a missing block or a body that differs from its rendering."""
    out = []
    for path, name, body in targets(plugin_dir):
        text = loadlist.read_text(path)
        cur = block_of(text, name)
        if cur is None:
            out.append((path, name, "no %s … %s block" % (begin(name), end(name))))
        elif cur != body:
            out.append((path, name, "the %s block differs from its rendering: run karvey-context-budget.py render "
                                    "(do not edit a generated block by hand)" % name))
    return out


def render_all(plugin_dir):
    """Rewrite every block in place; ``[path, …]`` of the files that changed."""
    changed = {}
    for path, name, body in targets(plugin_dir):
        text = changed.get(path)
        if text is None:
            text = loadlist.read_text(path)
        changed[path] = replace(text, name, body)
    out = []
    for path, text in changed.items():
        if text != loadlist.read_text(path):
            Path(path).write_text(text, encoding="utf-8")
            out.append(path)
    return sorted(out, key=str)
