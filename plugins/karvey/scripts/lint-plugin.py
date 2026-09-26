#!/usr/bin/env python3
"""lint-plugin.py — the Karvey plugin linter (architecture §1.6, wave1-hardening).

Every check is a registered function with an id (``L-NN``), a severity and the REQ-W1 ids it
proves. Python >= 3.9, standard library only.

Usage::

    lint-plugin.py [--root REPO] [--plugin DIR] [--only L-NN[,…]] [--paths GLOB …]
                   [--format text|json|github] [--list] [--requirements FILE …]

- ``--root``: the repository to lint (default: the git top level above the cwd, else the cwd).
- ``--plugin``: the plugin directory (default ``<root>/plugins/karvey``).
- ``--only``: run only these checks.
- ``--paths``: keep only findings whose file matches one of the globs (``*`` within a path
  segment, ``**`` across segments, ``{a,b}`` alternatives). An implementation convenience for
  scoped done-criteria, not a check of its own.
- ``--format github``: ``::error file=…,line=…::`` annotations for the PR.
- ``--list``: print the registry, and fail when a claimed REQ is absent from the requirements.

Exit codes: ``0`` no error-severity finding · ``1`` at least one · ``2`` usage error.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import loadlist  # noqa: E402
from karvey_lib import incidents  # noqa: E402

TOOL = "lint-plugin"
SCRIPTS_DIR = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- registry
class Check:
    __slots__ = ("id", "title", "reqs", "severity", "fn")

    def __init__(self, cid, title, reqs, severity, fn):
        self.id, self.title, self.reqs, self.severity, self.fn = cid, title, tuple(reqs), severity, fn


REGISTRY = []


def check(cid, title, reqs=(), severity="error"):
    """Register a check. ``fn(ctx)`` yields ``(file, line, message)`` or ``(…, severity)``."""
    def deco(fn):
        if any(c.id == cid for c in REGISTRY):
            raise ValueError("duplicate check id %s" % cid)
        REGISTRY.append(Check(cid, title, reqs, severity, fn))
        return fn
    return deco


def registry():
    return sorted(REGISTRY, key=lambda c: c.id)


# --------------------------------------------------------------------------- context
FENCE_RE = re.compile(r"^\s*(```+|~~~+)\s*([\w+-]*)")


class Ctx:
    """Read-only view of the repository being linted, with cached reads."""

    def __init__(self, root, plugin=None):
        self.root = Path(root).resolve()
        self.plugin = Path(plugin).resolve() if plugin else self.root / "plugins" / "karvey"
        self._text = {}

    # ---- paths
    def rel(self, path):
        p = Path(path)
        try:
            return p.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return p.as_posix()

    def read(self, path):
        p = Path(path)
        key = str(p)
        if key not in self._text:
            try:
                self._text[key] = p.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError):
                self._text[key] = None
        return self._text[key]

    def lines(self, path):
        text = self.read(path)
        return [] if text is None else text.splitlines()

    def json(self, path):
        text = self.read(path)
        if text is None:
            return None
        try:
            return json.loads(text)
        except ValueError:
            return None

    # ---- plugin layout
    @property
    def skills_dir(self):
        return self.plugin / "skills"

    @property
    def rules_dir(self):
        return self.skills_dir / "karvey" / "rules"

    def skills(self):
        """``{name: path}`` of every ``skills/*/SKILL.md``."""
        out = {}
        if self.skills_dir.is_dir():
            for d in sorted(self.skills_dir.iterdir()):
                if d.is_dir() and (d / "SKILL.md").is_file():
                    out[d.name] = d / "SKILL.md"
        return out

    def skill(self, name):
        p = self.skills_dir / name / "SKILL.md"
        return p if p.is_file() else None

    def rules(self):
        return sorted(self.rules_dir.glob("*.md")) if self.rules_dir.is_dir() else []

    def rule(self, name):
        p = self.rules_dir / name
        return p if p.is_file() else None

    def text_files(self):
        """Skill and rule text: every SKILL.md and every shared rule."""
        return list(self.skills().values()) + self.rules()

    def schemas_dir(self):
        d = self.plugin / "schemas"
        return d if d.is_dir() else kl.SCHEMAS_DIR

    def machine(self):
        data = self.json(self.schemas_dir() / "state-machine.json")
        if data is None:
            data = self.json(kl.SCHEMAS_DIR / "state-machine.json")
        return data or {"phases": []}

    def frontmatter(self, path):
        return parse_frontmatter(self.lines(path))


def iter_lines(lines):
    """``(lineno, line, fence_lang)``: ``fence_lang`` is None outside a fenced block."""
    fence = None
    lang = None
    for n, line in enumerate(lines, 1):
        m = FENCE_RE.match(line)
        if m:
            if fence is None:
                # keep the full opening run: a ````markdown wrapper is closed only by a fence at
                # least as long (CommonMark), not by the first inner ``` (F-34)
                fence, lang = m.group(1), (m.group(2) or "").lower()
                yield n, line, None
                continue
            if m.group(1).startswith(fence) and not m.group(2):
                fence = lang = None
                yield n, line, None
                continue
        yield n, line, (lang if fence is not None else None)


# --------------------------------------------------------------------------- frontmatter
FM_KEY_RE = re.compile(r"^([A-Za-z][\w-]*):(?:\s(.*))?$")
TOOL_NAME_RE = re.compile(r"^[A-Z][A-Za-z]*(\([^()]*\))?$")


def parse_frontmatter(lines):
    """``(fields, end_line, problems)``; problems are ``(line, message)``.

    Supported subset: the file starts with ``---``; one-line ``key: value`` scalars until the
    closing ``---``; no block scalars, continuation lines, lists or nested maps.
    """
    if not lines or lines[0].strip() != "---":
        return None, 0, [(1, "no frontmatter: the file must start with '---'")]
    fields, problems = {}, []
    for n in range(2, len(lines) + 1):
        line = lines[n - 1]
        if line.strip() == "---":
            return fields, n, problems
        if not line.strip():
            continue
        m = FM_KEY_RE.match(line)
        if not m:
            problems.append((n, "frontmatter line is not a one-line 'key: value' scalar: %r" % line[:60]))
            continue
        key, value = m.group(1), (m.group(2) or "").strip()
        if value in ("|", ">", "|-", ">-", "|+", ">+") or value == "":
            problems.append((n, "frontmatter key %r has a block or empty value; only one-line scalars "
                                "are supported" % key))
        if key in fields:
            problems.append((n, "frontmatter key %r repeated" % key))
        fields[key] = (value, n)
    return None, 0, [(1, "frontmatter is not closed with '---'")]


def fm_value(fields, key):
    v = fields.get(key) if fields else None
    if v is None:
        return None
    value = v[0]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def fm_line(fields, key, default=1):
    v = fields.get(key) if fields else None
    return v[1] if v else default


def allowed_tools(fields):
    value = fm_value(fields, "allowed-tools")
    if not value:
        return set()
    return {t.strip().split("(")[0] for t in value.split(",") if t.strip()}


TRIGGERS_RE = re.compile(r"Triggers? (?:include|includes|:)\s*(.*)$", re.S)
QUOTED_RE = re.compile(r"\"([^\"]+)\"|“([^”]+)”")


def triggers_of(fields):
    """Trigger phrases: the quoted phrases after ``Triggers include`` in the description, plus
    a ``triggers:`` key (comma list) when present."""
    out = []
    desc = fm_value(fields, "description") or ""
    m = TRIGGERS_RE.search(desc)
    if m:
        out += [a or b for a, b in QUOTED_RE.findall(m.group(1))]
    extra = fm_value(fields, "triggers")
    if extra:
        out += [t.strip().strip("\"'") for t in extra.split(",") if t.strip()]
    return out


def norm_phrase(s):
    return re.sub(r"\s+", " ", s.strip().lower())


# --------------------------------------------------------------------------- L-01 .. L-04
@check("L-01", "SKILL.md frontmatter in the supported subset (one-line scalars; allowed-tools a comma list)",
       reqs=("055", "077"))
def l01_frontmatter(ctx):
    for name, path in ctx.skills().items():
        fields, _, problems = ctx.frontmatter(path)
        for line, msg in problems:
            yield path, line, msg
        if fields is None:
            continue
        for key in ("name", "description"):
            if not fm_value(fields, key):
                yield path, 1, "frontmatter lacks %r" % key
        got = fm_value(fields, "name")
        if got and got != name:
            yield path, fm_line(fields, "name"), "name %r differs from the skill directory %r" % (got, name)
        tools = fm_value(fields, "allowed-tools")
        if tools is not None:
            for t in tools.split(","):
                if not TOOL_NAME_RE.match(t.strip()):
                    yield (path, fm_line(fields, "allowed-tools"),
                           "allowed-tools must be a comma list of tool names; got %r" % t.strip())
        dmi = fm_value(fields, "disable-model-invocation")
        if dmi is not None and dmi not in ("true", "false"):
            yield (path, fm_line(fields, "disable-model-invocation"),
                   "disable-model-invocation must be true or false; got %r" % dmi)


DESC_MAX = 250
DESC_SHAPE_RE = re.compile(r"^Karvey (phase \d+|support)\b")


@check("L-02", "Description <= 250 characters in the 'Karvey phase N | support — produces — when' shape",
       reqs=("077",))
def l02_description(ctx):
    for name, path in ctx.skills().items():
        fields, _, _ = ctx.frontmatter(path)
        if not fields:
            continue
        desc = fm_value(fields, "description")
        if not desc:
            continue
        line = fm_line(fields, "description")
        if len(desc) > DESC_MAX:
            yield path, line, "description of %s is %d characters (max %d)" % (name, len(desc), DESC_MAX)
        if not DESC_SHAPE_RE.match(desc):
            yield (path, line, "description of %s does not start with 'Karvey phase N' or 'Karvey support' "
                               "(shape: Karvey phase N | support — produces — when)" % name)


# Bare generic words and phrases (REQ-W1-078): a trigger equal to one of these collides with
# the user's own skills or with built-in commands.
GENERIC_TRIGGERS = frozenset(norm_phrase(s) for s in (
    "deploy", "qa", "code review", "review", "test", "tests", "testing", "archive", "iterate",
    "implement", "develop", "release", "architecture", "infrastructure", "technical design",
    "system design", "graphic design", "design system", "documentation", "docs", "readme",
    "debugging", "root cause", "screenshot", "onboarding", "lock", "freeze", "guardrails", "loop",
    "feedback loop", "prd", "sdd", "spec-driven", "spec driven development", "specification-driven",
    "requirements engineering", "pipeline", "development pipeline", "development method", "sdlc",
    "scaffolding", "handoff", "decision log", "diagram", "wireframe", "mockup", "prototype",
    "developer experience", "friction", "dx review", "retro", "retrospective", "health dashboard",
    "quality score", "iac", "pipeline ci/cd", "ci/cd", "new feature", "new change", "new bug",
    "interview me", "office hours", "reframe", "vibe coding", "agentic development",
    "ai-assisted development", "desplegar", "liberar", "implementar", "desarrollar", "arquitectura",
    "infraestructura", "documentación", "diagrama", "iterar", "archivar", "depurar", "candado",
    "guardar contexto", "restaurar contexto", "export pdf", "exportar pdf", "diataxis",
))
# Third-party product and person names (REQ-W1-078).
THIRD_PARTY_TRIGGERS = frozenset(norm_phrase(s) for s in (
    "gstack", "g-stack", "garry tan", "kiro", "cc-sdd", "openspec", "spec kit", "codex", "gemini",
    "gpt", "claude", "mermaid", "excalidraw", "terraform", "bicep", "clickup", "jira", "linear",
    "obsidian", "graphify", "playwright",
))


@check("L-03", "Trigger phrases carry method context: no bare generic or third-party trigger, no overlap",
       reqs=("078",))
def l03_triggers(ctx):
    seen = {}
    per_skill = {}
    for name, path in ctx.skills().items():
        fields, _, _ = ctx.frontmatter(path)
        if not fields:
            continue
        line = fm_line(fields, "description")
        trig = triggers_of(fields)
        per_skill[name] = (path, line, trig)
        for t in trig:
            n = norm_phrase(t)
            if n in GENERIC_TRIGGERS:
                yield path, line, "trigger %r of %s is a bare generic word; prefix it with the method" % (t, name)
            elif n in THIRD_PARTY_TRIGGERS:
                yield path, line, "trigger %r of %s is a third-party name" % (t, name)
            seen.setdefault(n, [])
            if name not in seen[n]:
                seen[n].append(name)
    for n, owners in sorted(seen.items()):
        if len(owners) > 1:
            for name in owners:
                path, line, _ = per_skill[name]
                others = ", ".join(o for o in owners if o != name)
                yield path, line, "trigger %r of %s overlaps with %s" % (n, name, others)


USER_ONLY_SKILLS = ("karvey-guard", "karvey-team", "karvey-benchmark-models", "karvey-scrape",
                    "karvey-import", "karvey-retro")


@check("L-04", "disable-model-invocation: true on guard, team, benchmark-models, scrape, import, retro",
       reqs=("079",))
def l04_user_only(ctx):
    for name in USER_ONLY_SKILLS:
        path = ctx.skill(name)
        if path is None:
            continue
        fields, _, _ = ctx.frontmatter(path)
        if fields is None:
            continue
        if fm_value(fields, "disable-model-invocation") != "true":
            yield path, 1, "%s must declare 'disable-model-invocation: true' (user-invoked only)" % name


# --------------------------------------------------------------------------- shared helpers (T2)
NEGATION_RE = re.compile(r"\b(?:(?i:never|do not|don't|must not|does not|doesn't|cannot|can't|no longer|"
                         r"not by hand|forbid\w*)|NOT)\b")
STATE_TOOL_RE = re.compile(r"karvey-state(\.py)?\b")


def phase_enum(ctx):
    return [p.get("id") for p in ctx.machine().get("phases", []) if p.get("id")]


def phase_index_of_skill(ctx):
    """``{skill: index}``: the first phase of state-machine.json each skill runs."""
    out = {}
    for i, p in enumerate(ctx.machine().get("phases", [])):
        s = p.get("skill")
        if s and s not in out:
            out[s] = i
    return out


def body_lines(ctx, path):
    """``(lineno, line, fence_lang)`` of a SKILL.md body (after the frontmatter)."""
    lines = ctx.lines(path)
    _, end, _ = parse_frontmatter(lines)
    for n, line, lang in iter_lines(lines):
        if n > end:
            yield n, line, lang


# --------------------------------------------------------------------------- L-05
PHASE_LIT_RE = re.compile(r"\bphase\b[`\"']?\s*(?::|==|=)\s*[`\"']([A-Za-z][\w-]*)[`\"']")
PHASE_YAML_RE = re.compile(r"^\s*-?\s*phase:\s*([a-z][\w-]*)\s*$")


@check("L-05", "Every phase literal in skill or rule text belongs to the state-machine.json enum",
       reqs=("001", "055"))
def l05_phase_literals(ctx):
    enum = set(phase_enum(ctx))
    for path in ctx.text_files():
        for n, line, _ in iter_lines(ctx.lines(path)):
            values = [m.group(1) for m in PHASE_LIT_RE.finditer(line)]
            m = PHASE_YAML_RE.match(line)
            if m:
                values.append(m.group(1))
            for v in values:
                if v not in enum:
                    yield (path, n, "phase literal %r is not in the state-machine.json enum (%s)"
                           % (v, " | ".join(sorted(enum, key=lambda x: phase_enum(ctx).index(x)))))


# --------------------------------------------------------------------------- L-06
OWNED_RES = (
    re.compile(r"\bphase\b[`\"']?\s*(?::|=(?!=))\s*[`\"']?[A-Za-z{]"),
    re.compile(r"\bapprovals\.[\w]+\.(approved|generated|by|role|date|ref)\b[`\"']?\s*(?::|=(?!=))"),
    re.compile(r"[\"']approvals[\"']\s*:\s*\{"),
    re.compile(r"\bskipped\b[`\"']?\s*(?::|=(?!=))\s*[{`\"']"),
    re.compile(r"\bphase_history\b"),
)
WRITE_VERB_RE = re.compile(r"\b(set|sets|update|updates|write|writes|mark|marks|record|records|flip|put|"
                           r"add|append|appends|on approval|becomes)\b|→", re.I)
PRECONDITION_RE = re.compile(r"^\s*(?:[-*]\s*(?:\[[ x]\]\s*)?)?\**(verify|check|requires?|must be)\b", re.I)


@check("L-06", "No instruction to edit phase, approvals, skipped or phase_history by hand "
               "(every hit is a karvey-state.py call)", reqs=("013",))
def l06_no_hand_phase_edits(ctx):
    for name, path in ctx.skills().items():
        reported_fence = None
        fence_start = None
        prev_lang = None
        for n, line, lang in body_lines(ctx, path):
            if lang is not None and prev_lang is None:
                fence_start = n
            prev_lang = lang
            if STATE_TOOL_RE.search(line):
                continue
            if not any(r.search(line) for r in OWNED_RES):
                continue
            if lang is not None and lang in ("json", "yaml", "yml", ""):
                if reported_fence == fence_start:
                    continue
                reported_fence = fence_start
                yield (path, n, "%s: a spec.json block with phase/approvals/skipped/phase_history written by "
                                "hand; create or change it through karvey-state.py" % name)
                continue
            if NEGATION_RE.search(line) or PRECONDITION_RE.search(line) or not WRITE_VERB_RE.search(line):
                continue
            yield (path, n, "%s instructs a hand edit of phase/approvals/skipped/phase_history; use "
                            "karvey-state.py (advance | generated | skip | approve | reopen)" % name)


# --------------------------------------------------------------------------- L-07
@check("L-07", "The orchestrator has no phase→next table; it calls karvey-state.py next", reqs=("005",))
def l07_orchestrator_next(ctx):
    path = ctx.skill("karvey")
    if path is None:
        return
    lines = ctx.lines(path)
    calls_next = False
    table, start = [], 0
    rows = list(iter_lines(lines)) + [(len(lines) + 1, "", None)]
    for n, line, lang in rows:
        if lang is None and re.search(r"karvey-state(\.py)?[\"'`]?\s+next\b", line):
            calls_next = True
        if lang is None and line.lstrip().startswith("|"):
            if not table:
                start = n
            table.append(line)
            continue
        if table:
            header = [c.strip().lower() for c in table[0].strip().strip("|").split("|")]
            body = [r for r in table[2:]] if len(table) > 2 else []
            phase_col = any("phase" in c or "fase" in c for c in header)
            next_col = any("next" in c or "siguiente" in c for c in header)
            skill_rows = sum(1 for r in body if "/karvey-" in r)
            if (phase_col and next_col) or (phase_col and skill_rows >= 3):
                yield (path, start, "orchestrator holds a phase→next table (%d rows); answer from "
                                    "`karvey-state.py next {id} --json` instead" % len(body))
            table = []
    if not calls_next:
        yield path, 1, "orchestrator does not call `karvey-state.py next`"


# --------------------------------------------------------------------------- L-08
DEPRECATED_ARTIFACTS = (
    (re.compile(r"\bproposal\.md\b"), "proposal.md: the product document is prd.md"),
    (re.compile(r"\bspecs/[{<]?[\w-]+[}>]?/spec-delta\.md\b"),
     "specs/{capability}/spec-delta.md: the spec-delta lives at the change root (spec-delta.md)"),
)
CHANGE_ARTIFACT_RE = re.compile(r"changes/(?:\{[^}]+\}|<[^>]+>|[\w-]+)/([\w.*/-]*[\w*/])")
READ_VERB_RE = re.compile(r"\b(read|reads|reading|cat|load|loads|consume|consumes|from|input|inputs|"
                          r"lee|leer)\b", re.I)


def _artifact_matches(produced, name):
    p = produced.rstrip("?")
    if p.endswith("/"):
        return name == p or name.startswith(p) or name == p.rstrip("/")
    if "*" in p:
        return re.match("^" + re.escape(p).replace(r"\*", "[^/]*") + "$", name) is not None
    return name == p


def producer_index(ctx, name):
    for i, p in enumerate(ctx.machine().get("phases", [])):
        if any(_artifact_matches(x, name) for x in p.get("produces", [])):
            return i
    return None


@check("L-08", "Every change artifact a skill reads is produced by an earlier phase "
               "(state-machine.json produces/reads); proposal.md and specs/*/spec-delta.md fail",
       reqs=("012", "057"))
def l08_artifacts(ctx):
    phases = ctx.machine().get("phases", [])
    sm = ctx.schemas_dir() / "state-machine.json"
    for i, p in enumerate(phases):
        for r in p.get("reads", []):
            optional = r.endswith("?")
            j = producer_index(ctx, r.rstrip("?"))
            if j is None or (j >= i and not optional):
                yield (sm, 0, "phase %s reads %s, which no earlier phase produces" % (p.get("id"), r))
    index = phase_index_of_skill(ctx)
    for name, path in ctx.skills().items():
        mine = index.get(name)
        for n, line, _ in body_lines(ctx, path):
            for rx, why in DEPRECATED_ARTIFACTS:
                if rx.search(line):
                    yield path, n, "%s reads %s" % (name, why)
            if mine is None:
                continue
            for m in CHANGE_ARTIFACT_RE.finditer(line):
                art = m.group(1)
                j = producer_index(ctx, art)
                if j is not None and j > mine and READ_VERB_RE.search(line):
                    yield (path, n, "%s (phase %s) reads %s, produced only later by phase %s"
                           % (name, phases[mine]["id"], art, phases[j]["id"]))


# --------------------------------------------------------------------------- L-09
PLUGIN_SEGMENTS = ("rules", "karvey", "hooks", "scripts", "schemas", "skills", "tests", "references",
                   "templates", "..", ".")
README_SEGMENTS = PLUGIN_SEGMENTS + ("plugins", "docs", ".claude-plugin", ".github")
PATH_EXT_RE = re.compile(r"\.(md|sh|py|json|mjs|js|html|txt|yml|yaml|csv)$")
TICK_RE = re.compile(r"`([^`\s]+)`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
BARE_RULE_RE = re.compile(r"(?<![\w/.${}-])((?:\.\./)*(?:\./)?(?:karvey/)?rules/[\w.-]+\.md)\b")
PLUGIN_ROOT_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+[\w/])")


def cited_paths(line, segments):
    """Relative file paths a line cites (backticks, markdown links, bare rule paths)."""
    out = []
    for m in LINK_RE.finditer(line):
        target = m.group(1).split("#")[0]
        if target and not re.match(r"^[a-z]+:", target) and not target.startswith("/"):
            out.append(target)
    for m in TICK_RE.finditer(line):
        tok = re.sub(r":\d+(-\d+)?(,\d+(-\d+)?)*$", "", m.group(1)).rstrip(".,;:)")
        if "/" not in tok or not (PATH_EXT_RE.search(tok) or tok.endswith("/")):
            continue
        if tok.split("/")[0] not in segments:
            continue
        out.append(tok)
    for m in BARE_RULE_RE.finditer(line):
        out.append(m.group(1))
    clean = []
    for t in out:
        if any(ch in t for ch in "{}<>*$…") or "..." in t.replace("../", ""):
            continue
        if t not in clean:
            clean.append(t)
    return clean


def citing_files(ctx):
    files = [(p, PLUGIN_SEGMENTS) for p in ctx.text_files()]
    # The plugin's own READMEs describe the user's project: a `docs/spec/…` there is the project's
    # file, not a path in this repository (as in SKILL.md). Only the repository README cites docs/.
    for p in (ctx.plugin / "hooks" / "README.md", ctx.plugin / "README.md"):
        if p.is_file():
            files.append((p, PLUGIN_SEGMENTS))
    if (ctx.root / "README.md").is_file():
        files.append((ctx.root / "README.md", README_SEGMENTS))
    return files


@check("L-09", "Every cited path resolves from the citing file, or is written ${CLAUDE_PLUGIN_ROOT}/…",
       reqs=("053",))
def l09_paths(ctx):
    for path, segments in citing_files(ctx):
        base = path.parent
        for n, line, lang in iter_lines(ctx.lines(path)):
            for m in PLUGIN_ROOT_RE.finditer(line):
                rel = m.group(1)
                if any(ch in rel for ch in "{}<>*"):
                    continue
                if not (ctx.plugin / rel).exists():
                    yield path, n, "${CLAUDE_PLUGIN_ROOT}/%s does not exist in the plugin" % rel
            if lang is not None:
                continue
            for tok in cited_paths(PLUGIN_ROOT_RE.sub("", line), segments):
                if not (base / tok).exists():
                    yield (path, n, "cited path %s does not resolve from %s (use ../karvey/rules/x.md or "
                                    "${CLAUDE_PLUGIN_ROOT}/…)" % (tok, ctx.rel(base)))


# --------------------------------------------------------------------------- L-10
GENERATED_RE = re.compile(r"^<!--\s*generated-from:\s*(\S+)\s*-->\s*$")


@check("L-10", "No skills/*/rules/ copy; a copy declared generated is byte-identical to its source",
       reqs=("052",))
def l10_rule_copies(ctx):
    if not ctx.skills_dir.is_dir():
        return
    for d in sorted(ctx.skills_dir.glob("*/rules")):
        if d.parent.name == "karvey" or not d.is_dir():
            continue
        for f in sorted(p for p in d.rglob("*") if p.is_file()):
            text = ctx.read(f) or ""
            first, _, rest = text.partition("\n")
            m = GENERATED_RE.match(first)
            source = ctx.rules_dir / f.name
            if m:
                src = (f.parent / m.group(1)).resolve()
                src_text = ctx.read(src)
                if src_text is None:
                    yield f, 1, "generated copy names a missing source %s" % m.group(1)
                elif src_text != rest:
                    yield f, 1, "generated copy %s differs from its source %s" % (ctx.rel(f), ctx.rel(src))
                continue
            yield (f, 1, "hand-kept rule copy %s (source %s): delete it and cite ../karvey/rules/%s"
                   % (ctx.rel(f), ctx.rel(source), f.name))


# --------------------------------------------------------------------------- L-14
FILE_TOKEN = r"`[^`\s]*\.(?:md|json|html|txt|yml|yaml|sh|py|csv|mjs|js)`"
TOOL_NEEDS = (
    ("Write", ("Write",), re.compile(r"\b(write|writes|create|creates|save|saves|generate|generates)\b"
                                     r"[^`\n]{0,30}" + FILE_TOKEN, re.I)),
    ("Edit", ("Edit", "Write", "MultiEdit"), re.compile(r"\b(edit|edits|update|updates|modify|append|"
                                                        r"appends|amend|patch)\b[^`\n]{0,30}" + FILE_TOKEN,
                                                        re.I)),
    ("AskUserQuestion", ("AskUserQuestion",), re.compile(r"AskUserQuestion|\bask the (user|human|owner)\b",
                                                         re.I)),
    ("Agent", ("Agent", "Task"), re.compile(r"\bsub-?agents?\b|\bAgent tool\b|\blaunch(?:es)? (?:\w+ ){0,2}"
                                            r"agents?\b|\bspawn(?:s)? (?:\w+ ){0,2}agents?\b", re.I)),
    ("Bash", ("Bash",), re.compile(r"\b[Rr]un\s+`(?:git|python3?|bash|sh|gh|az|glab|npm|npx|node|curl|make|"
                                   r"pytest|ls|cat|grep|jq)\b")),
)
SHELL_FENCES = ("bash", "sh", "shell", "zsh", "console")


@check("L-14", "An instructed action (Write, Edit, AskUserQuestion, Bash, Agent) is declared in allowed-tools",
       reqs=("056",))
def l14_allowed_tools(ctx):
    for name, path in ctx.skills().items():
        fields, _, _ = ctx.frontmatter(path)
        if not fields or fm_value(fields, "allowed-tools") is None:
            continue
        have = allowed_tools(fields)
        first = {}
        for n, line, lang in body_lines(ctx, path):
            if lang in SHELL_FENCES:
                first.setdefault("Bash", n)
                continue
            if lang is not None:
                continue
            for tool, satisfied_by, rx in TOOL_NEEDS:
                if tool in first:
                    continue
                if tool in ("Write", "Edit") and NEGATION_RE.search(line):
                    continue
                if rx.search(line):
                    first[tool] = n
        for tool, satisfied_by, _ in TOOL_NEEDS:
            if tool in first and not have.intersection(satisfied_by):
                yield (path, first[tool], "%s instructs a %s action but allowed-tools lacks %s"
                       % (name, tool, tool))


# --------------------------------------------------------------------------- manifests and release (T3)
RELEASE_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]")


def plugin_json_path(ctx):
    return ctx.plugin / ".claude-plugin" / "plugin.json"


def marketplace_path(ctx):
    return ctx.root / ".claude-plugin" / "marketplace.json"


def line_of(ctx, path, needle, default=1):
    for n, line in enumerate(ctx.lines(path), 1):
        if needle in line:
            return n
    return default


def top_release(ctx):
    """``(version, heading_line, block_lines)`` of the first numbered CHANGELOG release."""
    path = ctx.root / "CHANGELOG.md"
    lines = ctx.lines(path)
    start = None
    for i, line in enumerate(lines):
        m = RELEASE_RE.match(line)
        if m and start is None:
            start, version = i, m.group(1)
            continue
        if start is not None and line.startswith("## ["):
            return version, start + 1, lines[start:i]
    if start is not None:
        return version, start + 1, lines[start:]
    return None, 0, []


def marketplace_entry(ctx):
    data = ctx.json(marketplace_path(ctx))
    pj = ctx.json(plugin_json_path(ctx)) or {}
    if not isinstance(data, dict):
        return None
    for p in data.get("plugins", []) or []:
        if isinstance(p, dict) and p.get("name") == pj.get("name", "karvey"):
            return p
    return None


# --------------------------------------------------------------------------- L-11
def phase_skills(ctx):
    """The pipeline's phase skills: the orchestrator's ``PHASE N ── /karvey-x`` lines, else the
    state machine's skills."""
    names = []
    orch = ctx.skill("karvey")
    if orch:
        for line in ctx.lines(orch):
            m = re.match(r"^\s*PHASE\s+\d+\s*[─—-]+\s*/(karvey-[\w-]+)", line)
            if m and m.group(1) not in names:
                names.append(m.group(1))
    if not names:
        names = sorted({p["skill"] for p in ctx.machine().get("phases", []) if p.get("skill")})
    return [n for n in names if n in ctx.skills()] or names


COUNT_RES = (
    ("phase", re.compile(r"\b(\d+)[ -]phases?\b")),
    ("support", re.compile(r"\b(\d+) support skills\b")),
    ("skills", re.compile(r"(?<!support )\b(\d+) skills\b")),
    ("rules", re.compile(r"\b(\d+) (?:shared )?rules\b")),
)


@check("L-11", "Skill and rule counts in README.md, plugins/karvey/README.md, plugin.json and "
               "marketplace.json match the files", reqs=("055",))
def l11_counts(ctx):
    skills = ctx.skills()
    phases = phase_skills(ctx)
    truth = {
        "phase": len(phases),
        "skills": len(skills),
        "support": len(skills) - len(phases) - (1 if "karvey" in skills else 0),
        "rules": len(ctx.rules()),
    }
    sources = []
    for p in (ctx.root / "README.md", ctx.plugin / "README.md"):
        if p.is_file():
            sources.append((p, ctx.lines(p)))
    pj = ctx.json(plugin_json_path(ctx))
    if isinstance(pj, dict) and pj.get("description"):
        n = line_of(ctx, plugin_json_path(ctx), '"description"')
        sources.append((plugin_json_path(ctx), [""] * (n - 1) + [pj["description"]]))
    mk = marketplace_entry(ctx)
    if mk and mk.get("description"):
        n = line_of(ctx, marketplace_path(ctx), mk["description"][:40])
        sources.append((marketplace_path(ctx), [""] * (n - 1) + [mk["description"]]))
    for path, lines in sources:
        for n, line in enumerate(lines, 1):
            for kind, rx in COUNT_RES:
                for m in rx.finditer(line):
                    got = int(m.group(1))
                    if got != truth[kind]:
                        yield (path, n, "says %d %s but the plugin has %d (%s)"
                               % (got, {"phase": "phases", "support": "support skills", "skills": "skills",
                                        "rules": "rules"}[kind], truth[kind], m.group(0)))


# --------------------------------------------------------------------------- L-12
@check("L-12", "plugin.json, marketplace.json, project.json:karvey_version and the top CHANGELOG release agree",
       reqs=("055",))
def l12_versions(ctx):
    pj = ctx.json(plugin_json_path(ctx))
    if not isinstance(pj, dict) or not pj.get("version"):
        yield plugin_json_path(ctx), 1, "plugin.json has no version"
        return
    want = str(pj["version"])
    mk = marketplace_entry(ctx)
    if mk is not None and str(mk.get("version")) != want:
        yield (marketplace_path(ctx), line_of(ctx, marketplace_path(ctx), '"version"'),
               "marketplace.json says %s, plugin.json says %s" % (mk.get("version"), want))
    proj_path = ctx.root / "docs" / "spec" / "project.json"
    proj = ctx.json(proj_path)
    if isinstance(proj, dict) and "karvey_version" in proj and str(proj["karvey_version"]) != want:
        yield (proj_path, line_of(ctx, proj_path, '"karvey_version"'),
               "project.json:karvey_version says %s, plugin.json says %s" % (proj["karvey_version"], want))
    if (ctx.root / "CHANGELOG.md").is_file():
        version, line, _ = top_release(ctx)
        if version is None:
            yield ctx.root / "CHANGELOG.md", 1, "CHANGELOG.md has no numbered release ([Unreleased] is not one)"
        elif version != want:
            yield (ctx.root / "CHANGELOG.md", line,
                   "top CHANGELOG release is %s, plugin.json says %s" % (version, want))


# --------------------------------------------------------------------------- L-13
LANG_BLOCK_RE = re.compile(r"<div class=\"lang-block\" data-lang=\"([\w-]+)\"")
NOW_VER_RE = re.compile(r"<li class=\"now\">\s*<span class=\"ver\">([^<]+)</span>")


@check("L-13", "The top CHANGELOG release has a 'Why' section; docs/karvey.html lists that version as "
               "current in every language block", reqs=("058",))
def l13_release_docs(ctx):
    changelog = ctx.root / "CHANGELOG.md"
    if not changelog.is_file():
        return
    version, line, block = top_release(ctx)
    if version is None:
        return
    if not any(re.match(r"^###\s+Why\b", b) for b in block):
        yield changelog, line, "release %s has no '### Why' section (changelog-policy.md)" % version
    page = ctx.root / "docs" / "karvey.html"
    text = ctx.read(page)
    if text is None:
        return
    starts = [(m.start(), m.group(1)) for m in LANG_BLOCK_RE.finditer(text)]
    if not starts:
        yield page, 1, "docs/karvey.html has no language blocks"
        return
    for i, (pos, lang) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        m = NOW_VER_RE.search(text, pos, end)
        n = text.count("\n", 0, pos) + 1
        if not m:
            yield page, n, "language block %r has no version marked current" % lang
        elif m.group(1).strip() != version:
            yield (page, text.count("\n", 0, m.start()) + 1,
                   "language block %r marks %s as current; the top release is %s" % (lang, m.group(1).strip(),
                                                                                     version))


# --------------------------------------------------------------------------- L-17
def _schema_registry(ctx):
    from karvey_lib import schema_lite
    return schema_lite, schema_lite.load_registry(ctx.schemas_dir())


def _resolve(ref, root_schema, reg):
    if ref.startswith("#"):
        doc, frag = root_schema, ref[1:]
    else:
        sid, _, frag = ref.partition("#")
        doc = reg.get(sid)
        if doc is None:
            return None, None
    node = doc
    for part in [p for p in frag.split("/") if p]:
        if not isinstance(node, dict) or part not in node:
            return None, None
        node = node[part]
    return node, doc


def _expand(node, root_schema, reg, depth=0):
    """``[(node, its root schema)]``: the node, its $ref target and every combinator branch."""
    if depth > 12 or not isinstance(node, dict):
        return []
    out = [(node, root_schema)]
    if "$ref" in node:
        target, doc = _resolve(node["$ref"], root_schema, reg)
        if target is not None:
            out += _expand(target, doc, reg, depth + 1)
    for key in ("oneOf", "anyOf", "allOf"):
        for sub in node.get(key, []) or []:
            out += _expand(sub, root_schema, reg, depth + 1)
    for key in ("then", "else"):
        if isinstance(node.get(key), dict):
            out += _expand(node[key], root_schema, reg, depth + 1)
    return out


def schema_misses(value, nodes, reg, path="$"):
    """Dotted paths of object keys in ``value`` that no schema node declares."""
    misses = []
    expanded = []
    for node, doc in nodes:
        expanded += _expand(node, doc, reg)
    if isinstance(value, dict):
        props, maps, typed = {}, [], False
        for node, doc in expanded:
            if isinstance(node.get("properties"), dict):
                typed = True
                for k, sub in node["properties"].items():
                    props.setdefault(k, []).append((sub, doc))
            ap = node.get("additionalProperties")
            if isinstance(ap, dict):
                maps.append((ap, doc))  # a map: its keys are data, not fields
            # additionalProperties: true keeps a schema open for forward compatibility; it does
            # not document a field, so it is not a map here.
        if not typed and not maps:
            return misses  # a free-form object: nothing to compare
        for k, v in value.items():
            if k in props:
                misses += schema_misses(v, props[k], reg, "%s.%s" % (path, k))
            elif maps:
                misses += schema_misses(v, maps, reg, "%s.%s" % (path, k))
            else:
                misses.append("%s.%s" % (path, k))
    elif isinstance(value, list):
        items = [(n["items"], doc) for n, doc in expanded if isinstance(n.get("items"), dict)]
        if items:
            for i, v in enumerate(value):
                misses += schema_misses(v, items, reg, "%s[%d]" % (path, i))
    return misses


JSON_FENCES = ("json", "jsonc", "json5")
SCHEMA_RULES = ("project-config.md", "living-specs.md")


def json_blocks(ctx, path):
    """``[(first_line, text)]`` of every fenced json block."""
    out, cur, start = [], None, 0
    for n, line, lang in iter_lines(ctx.lines(path)):
        if lang in JSON_FENCES:
            if cur is None:
                cur, start = [], n
            cur.append(line)
        elif cur is not None:
            out.append((start, "\n".join(cur)))
            cur = None
    if cur is not None:
        out.append((start, "\n".join(cur)))
    return out


@check("L-17", "Every field in the JSON blocks of rules/project-config.md and rules/living-specs.md is "
               "in a schema; the schemas use only the supported subset", reqs=("002",))
def l17_rule_json_vs_schema(ctx):
    sl, reg = _schema_registry(ctx)
    for sid, schema in sorted(reg.items()):
        spath = ctx.schemas_dir() / sid.split(":", 1)[-1]
        for pointer, problem in sl.check_schema(schema):
            yield spath, 1, "%s: %s (schema_lite subset)" % (pointer, problem)
    roots = [(sid, reg[sid]) for sid in ("karvey:spec.schema.json", "karvey:project.schema.json") if sid in reg]
    if not roots:
        return
    for name in SCHEMA_RULES:
        path = ctx.rule(name)
        if path is None:
            continue
        lines = ctx.lines(path)
        for start, text in json_blocks(ctx, path):
            try:
                data = json.loads(text)
            except ValueError as exc:
                yield path, start, "JSON block does not parse: %s" % exc
                continue
            if not isinstance(data, dict):
                continue
            best = None
            for sid, schema in roots:
                misses = schema_misses(data, [(schema, schema)], reg)
                if best is None or len(misses) < len(best[1]):
                    best = (sid, misses)
            sid, misses = best
            for miss in misses:
                key = miss.rsplit(".", 1)[-1]
                n = start
                for i in range(start - 1, min(len(lines), start + text.count("\n") + 1)):
                    if '"%s"' % key in lines[i]:
                        n = i + 1
                        break
                yield (path, n, "field %s documented in %s is absent from %s"
                       % (miss.replace("$.", "", 1), name, sid.split(":", 1)[-1]))


# --------------------------------------------------------------------------- L-18
_STATE = None


def state_tool():
    """karvey-state.py loaded in-process (the validator is shared, not re-implemented)."""
    global _STATE
    if _STATE is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("karvey_state", str(SCRIPTS_DIR / "karvey-state.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _STATE = mod
    return _STATE


@check("L-18", "docs/spec/**/*.json validate (karvey-state.py validator, in process)", reqs=("055", "109"))
def l18_spec_validate(ctx):
    base = ctx.root / "docs" / "spec"
    if not base.is_dir():
        return
    st = state_tool()
    strict = st.schema_mode(str(ctx.root)) == "strict"
    for f in st.all_files(str(ctx.root)):
        name = ctx.rel(f)
        try:
            loaded = st.load(f)
            st.check_schema_version(loaded.data, name)
        except st.NotFound as exc:
            yield f, 0, "cannot validate: %s" % exc
            continue
        issues = st.validate_data(loaded.data, st.kind_of(f), strict, file=name)
        warnings = 0
        for i in issues:
            if i["severity"] == "error":
                yield f, 0, "%s: %s" % (i.get("path") or "$", i["message"])
            else:
                warnings += 1
        if warnings:
            yield (f, 0, "%d validation warning(s) in %s mode (run karvey-state.py validate %s)"
                   % (warnings, "strict" if strict else "advisory", name), "warning")


# --------------------------------------------------------------------------- guard tables (T4)
def table_cases(ctx):
    """``{case_id: (case, table_file)}`` of every guard-table case."""
    out = {}
    d = ctx.plugin / "tests" / "hooks" / "tables"
    for f in sorted(d.glob("*.json")) if d.is_dir() else []:
        data = ctx.json(f)
        cases = data.get("cases", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for c in cases:
            if isinstance(c, dict) and c.get("id"):
                out[c["id"]] = (c, f)
    return out


def norm_hook(name):
    n = name[:-3] if name.endswith(".sh") else name
    for suffix in ("-guard", "-hook"):
        if n.endswith(suffix) and n != suffix.lstrip("-"):
            n = n[: -len(suffix)]
    return n


def shipped_hooks(ctx):
    """Normalised names of the hooks the plugin ships: the dispatcher's guard registry, the
    scripts under ``hooks/`` and the legacy template shims under ``skills/*/hooks/``."""
    names = set()
    reg = ctx.read(ctx.plugin / "scripts" / "karvey_lib" / "karvey_hooks.py") or ""
    names.update(norm_hook(m) for m in re.findall(r"Guard\(\s*[\"']([\w-]+)[\"']", reg))
    for d in [ctx.plugin / "hooks"] + sorted(ctx.skills_dir.glob("*/hooks")):
        if d.is_dir():
            names.update(norm_hook(p.name) for p in d.glob("*.sh"))
    hj = ctx.json(ctx.plugin / "hooks" / "hooks.json")
    if isinstance(hj, dict):
        for m in re.findall(r"hooks/([\w-]+)\.sh", json.dumps(hj)):
            names.add(norm_hook(m))
    return names


# --------------------------------------------------------------------------- L-15
HOOK_NAME_RE = re.compile(r"(?<![\w/-])([a-z][a-z0-9]*(?:-[a-z0-9]+)*-(?:guard|gate))(\.sh)?\b")


@check("L-15", "Every hook named in skills or rules exists in hooks.json or the dispatcher and has "
               "guard-table cases (clickup-sync-guard, standards-guard fail)", reqs=("029",))
def l15_hooks_exist(ctx):
    shipped = shipped_hooks(ctx)
    tabled = {norm_hook(c.get("guard", "")) for c, _ in table_cases(ctx).values()}
    for path in ctx.text_files():
        seen = set()
        for n, line, _ in iter_lines(ctx.lines(path)):
            for m in HOOK_NAME_RE.finditer(line):
                name, sh = m.group(1), m.group(2)
                if name.startswith("karvey-"):
                    continue  # a skill name (karvey-guard), not a hook
                if not sh and not re.search(r"\bhooks?\b", line, re.I):
                    continue
                key = norm_hook(name)
                if key in seen:
                    continue
                seen.add(key)
                if key not in shipped:
                    yield path, n, "hook %s is cited but the plugin does not ship it" % name
                elif key not in tabled:
                    yield path, n, "hook %s has no guard-table cases (tests/hooks/tables/*.json)" % name


# --------------------------------------------------------------------------- L-16
PROMISE_RE = re.compile(r"\b(blocks?|blocked|allows?|allowed|lets? (?:it|them|things|the command) through|"
                        r"prints?|printed|silent(?:ly)?|nothing|exits?)\b", re.I)
ANCHOR_RE = re.compile(r"<!--\s*guard-case:\s*([\w.,\s-]+?)\s*-->")
PROMISE_FILES = ("rules/enforcement.md", "hooks/README.md")


def _verb_classes(line):
    classes = set()
    line = re.sub(r"\b(prints?|outputs?|says?|emits?)\s+nothing\b", "silent", line, flags=re.I)
    for m in PROMISE_RE.finditer(line):
        v = m.group(1).lower()
        if v.startswith("block") or v.startswith("exit"):
            classes.add("block")
        elif v.startswith("allow") or v.startswith("let"):
            classes.add("allow")
        elif v.startswith("silent") or v == "nothing":
            classes.add("silent")
        else:
            classes.add("prints")
    return classes


def _case_fits(case, classes):
    exp = case.get("expect", {}) if isinstance(case.get("expect"), dict) else {}
    decision = exp.get("decision")
    # a session case asserts what the hook adds to the context (context_contains): that is its output
    prints = bool(exp.get("stdout_contains") or exp.get("stderr_contains") or exp.get("context_contains"))
    silent = decision == "allow" and not prints
    for c in classes:
        if c == "block" and decision == "block":
            return True
        if c == "allow" and decision == "allow":
            return True
        if c == "silent" and silent:
            return True
        if c == "prints" and prints:
            return True
    return False


@check("L-16", "In rules/enforcement.md and hooks/README.md every behaviour promise carries "
               "<!-- guard-case: ID --> whose table case matches the verb", reqs=("022", "051"))
def l16_guard_case_anchors(ctx):
    cases = table_cases(ctx)
    files = [ctx.rules_dir / "enforcement.md", ctx.plugin / "hooks" / "README.md"]
    for path in files:
        if not path.is_file():
            continue
        for n, line, lang in iter_lines(ctx.lines(path)):
            if lang is not None or line.lstrip().startswith("#") or re.match(r"^\s*\|[\s:|-]+\|\s*$", line):
                continue
            prose = ANCHOR_RE.sub("", line)
            classes = _verb_classes(prose)
            if not classes:
                continue
            ids = [i.strip() for m in ANCHOR_RE.finditer(line) for i in m.group(1).split(",") if i.strip()]
            if not ids:
                yield (path, n, "behaviour promise (%s) without a <!-- guard-case: ID --> anchor"
                       % "/".join(sorted(classes)))
                continue
            for cid in ids:
                if cid not in cases:
                    yield path, n, "guard-case %s is not a case of tests/hooks/tables/*.json" % cid
                elif not _case_fits(cases[cid][0], classes):
                    exp = cases[cid][0].get("expect", {})
                    yield (path, n, "guard-case %s expects %s, which contradicts the promise (%s)"
                           % (cid, exp.get("decision"), "/".join(sorted(classes))))


# --------------------------------------------------------------------------- L-19
BUMP_PER_COMMIT_RES = (
    re.compile(r"\b(bump\w*|increment\w*)\b[^.;\n]{0,60}\b(per|each|every)\s+(commit|task)\b", re.I),
    re.compile(r"\b(per|each|every)\s+(commit|task)\b[^.;\n]{0,40}\b(bump\w*|increments? the version)\b", re.I),
)


@check("L-19", "Versioning: no bump per commit or task; impl writes [Unreleased]; QA D6 and the deploy "
               "pre-check read [Unreleased]; the versioning rule says per release", reqs=("036", "038", "039"))
def l19_versioning(ctx):
    impl = ctx.skill("karvey-impl")
    for path in ctx.text_files():
        for n, line, _ in iter_lines(ctx.lines(path)):
            for rx in BUMP_PER_COMMIT_RES:
                m = rx.search(line)
                if m and not NEGATION_RE.search(line[max(0, m.start() - 25):m.end()]):
                    yield (path, n, "describes a version bump per commit/task; impl adds to [Unreleased], "
                                    "one bump per release")
                    break
            else:
                if path == impl:
                    m = re.search(r"\bbump\w*\b|\bincrement(s|ing)? the version\b", line, re.I)
                    if m and not NEGATION_RE.search(line[max(0, m.start() - 25):m.end() + 25]):
                        yield path, n, "karvey-impl bumps the version; impl only adds to [Unreleased] (REQ-W1-036)"
    for name, what in (("karvey-impl", "impl must add its line under ## [Unreleased]"),
                       ("karvey-qa", "QA D6 must verify the [Unreleased] section"),
                       ("karvey-deploy", "the deploy pre-check must read [Unreleased]")):
        path = ctx.skill(name)
        if path is not None and "[Unreleased]" not in (ctx.read(path) or ""):
            yield path, 1, "%s never mentions [Unreleased]: %s" % (name, what)
    rule = ctx.rule("versioning.md")
    if rule is not None and not re.search(r"\b(each|every|per|one)\s+(bump per\s+)?release\b", ctx.read(rule) or "",
                                          re.I):
        yield rule, 1, "versioning.md does not say that each release increments the version"


# --------------------------------------------------------------------------- L-20
QA_ITEM_RE = re.compile(r"<!--\s*qa-item:\s*([^>]+?)\s*-->")


def qa_items(ctx, rule):
    """``[(line, key)]``: ``<!-- qa-item: key -->`` anchors, else the bullets of a section whose
    heading names QA / Dimension 6."""
    lines = ctx.lines(rule)
    items = [(n, m.group(1)) for n, line in enumerate(lines, 1) for m in QA_ITEM_RE.finditer(line)]
    if items:
        return items
    in_qa = False
    for n, line in enumerate(lines, 1):
        h = re.match(r"^(#+)\s+(.*)", line)
        if h:
            in_qa = bool(re.search(r"\bQA\b|karvey-qa|Dimension 6|D6", h.group(2)))
            continue
        if in_qa:
            b = re.match(r"^\s*[-*]\s+(.*)", line)
            if b:
                t = b.group(1)
                key = re.search(r"`([^`]+)`", t) or re.search(r"\*\*([^*]+)\*\*", t)
                items.append((n, key.group(1) if key else t.strip()))
    return items


def d6_text(ctx, qa):
    lines = ctx.lines(qa)
    out, on = [], False
    for line in lines:
        if re.search(r"Dimension 6\b|^#+\s*6\.\s", line):
            on = True
        elif on and re.search(r"Dimension 7\b|^#+\s*7\.\s", line):
            on = False
        if on:
            out.append(line)
    return "\n".join(out)


@check("L-20", "Every QA item assigned in rules/versioning.md appears in karvey-qa Dimension 6", reqs=("040",))
def l20_versioning_qa_items(ctx):
    rule, qa = ctx.rule("versioning.md"), ctx.skill("karvey-qa")
    if rule is None or qa is None:
        return
    items = qa_items(ctx, rule)
    text = ctx.read(rule) or ""
    if not items:
        if re.search(r"karvey-qa|Dimension 6|\bQA\b", text):
            yield (rule, 1, "versioning.md assigns verification to QA but lists no QA items "
                            "(a QA section or <!-- qa-item: key --> anchors)")
        return
    d6 = d6_text(ctx, qa).lower()
    if not d6:
        yield qa, 1, "karvey-qa has no Dimension 6 section"
        return
    for n, key in items:
        if key.lower() not in d6:
            yield rule, n, "QA item %r of versioning.md is absent from karvey-qa Dimension 6" % key


# --------------------------------------------------------------------------- L-21
ESTIMATE_WRITE_RES = (
    re.compile(r"time_estimate[^\n]{0,80}\bactual", re.I),
    re.compile(r"\bestimate\w*\b\s*[`\"']?\s*[:=]\s*[{`\"']?\s*\$?\{?\s*actual", re.I),
)


@check("L-21", "No write of an actual time into an estimate field", reqs=("042",))
def l21_estimate_not_overwritten(ctx):
    for path in ctx.text_files():
        for n, line, _ in iter_lines(ctx.lines(path)):
            if NEGATION_RE.search(line):
                continue
            if any(rx.search(line) for rx in ESTIMATE_WRITE_RES):
                yield path, n, "writes the actual time into the estimate field; record it as a time entry / actual"


# --------------------------------------------------------------------------- L-22
ROTATION_RE = re.compile(r"rotat|rotar|rotaci|relevo|ROTATE", re.I)
HOURS_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s?(?:h|hours?|horas)\b(?!\s*\d+\s*%)(?!\d)")
SHELL_ROTATE_RE = re.compile(r"ROTATE_HOURS\D{0,40}?(\d+(?:\.\d+)?)")


def rotation_files(ctx):
    files = list(ctx.text_files())
    for p in (ctx.plugin / "hooks" / "README.md", ctx.plugin / "README.md", ctx.root / "README.md"):
        if p.is_file():
            files.append(p)
    d = ctx.plugin / "hooks"
    if d.is_dir():
        files += sorted(d.glob("*.sh"))
    return files


@check("L-22", "Rotation threshold: no literal other than one that cites karvey_lib/defaults.json",
       reqs=("049",))
def l22_rotation_threshold(ctx):
    for path in rotation_files(ctx):
        lines = ctx.lines(path)
        code = path.suffix in (".sh", ".py")
        for n, line in enumerate(lines, 1):
            if "defaults.json" in line:
                continue
            if code:
                m = SHELL_ROTATE_RE.search(line)
                if m:
                    yield (path, n, "rotation threshold literal %s; read it from karvey_lib/defaults.json"
                           % m.group(1))
                continue
            context = line if n == 1 else lines[n - 2] + " " + line
            if not ROTATION_RE.search(context):
                continue
            for m in HOURS_RE.finditer(line):
                if re.match(r"\d+h\d+m", line[m.start():]):
                    continue
                yield (path, n, "rotation threshold literal %s; cite karvey_lib/defaults.json instead"
                       % m.group(0).strip())


# --------------------------------------------------------------------------- L-23
SYNC_INVOKE_RES = (
    re.compile(r"/graphify\b"),
    re.compile(r"\b(sync|syncs|syncing)\b(?: the)? knowledge\b", re.I),
    re.compile(r"\brun the sync step\b|\btrigger the sync\b", re.I),
    re.compile(r"^#+\s.*\bknowledge sync\b", re.I),
)
ON_DEMAND_RE = re.compile(r"on[- ]demand|when the user asks|if the user asks|a pedido|only (?:at|in) archive|"
                          r"archive only|at archive", re.I)


@check("L-23", "graphify / knowledge sync is invoked only by karvey-archive and the explicit on-demand path",
       reqs=("062",))
def l23_sync_only_at_archive(ctx):
    for path in ctx.text_files():
        if path.parent.name == "karvey-archive" or path.name == "knowledge-sync.md":
            continue
        for n, line, _ in iter_lines(ctx.lines(path)):
            if ON_DEMAND_RE.search(line) or NEGATION_RE.search(line):
                continue
            if any(rx.search(line) for rx in SYNC_INVOKE_RES):
                yield path, n, "invokes the knowledge sync outside archive; it runs at archive and on demand only"


# --------------------------------------------------------------------------- L-24
# "per task … comment" must not cross a comma: "Status per task, comment and cascade per Feature" is the
# rule itself (F-34).
PER_TASK_RITUAL_RE = re.compile(r"\b(comment|cascade)\w*\b[^.;\n]{0,80}\b(per[- ]task|(?:each|every)\s+(?:impl\s+)?task)\b"
                                r"|\b(per[- ]task|(?:each|every)\s+(?:impl\s+)?task)\b[^.;,\n]{0,40}\b(comment|cascade)",
                                re.I)


@check("L-24", "Tracker ritual: status per task; comment and cascade per Feature (phase-close.md)",
       reqs=("064",))
def l24_tracker_ritual(ctx):
    files = ctx.rules() + [p for p in (ctx.skill("karvey-impl"),) if p]
    for path in files:
        for n, line, _ in iter_lines(ctx.lines(path)):
            if NEGATION_RE.search(line):
                continue
            if PER_TASK_RITUAL_RE.search(line):
                yield path, n, "requires a close comment or cascade per task; they run per Feature (status per task)"
    rule = ctx.rule("phase-close.md")
    if rule is not None and not re.search(r"per\s+Feature", ctx.read(rule) or "", re.I):
        yield rule, 1, "phase-close.md does not state the close comment and cascade per Feature"


# --------------------------------------------------------------------------- L-25 (T5)
def near_negation(line, pos, before=30, after=0):
    return NEGATION_RE.search(line[max(0, pos - before):pos + after]) is not None


QA_COMMIT_RE = re.compile(r"\b(apply|make|create|do|push)\b[^.\n]{0,30}\bcommits?\b|\bgit commit\b|"
                          r"\bcommit (?:the|it|them|your|a|each|every|fixes)\b", re.I)
QA_DIR_RE = re.compile(r"changes/(?:\{[^}]+\}|<[^>]+>|[\w-]+)/qa/")


@check("L-25", "QA has no commit instruction; the review is written to changes/{id}/qa/, deploy reads it "
               "from there; no REVISION_PR_*.md at the repo root", reqs=("073", "074", "075"))
def l25_qa_observes(ctx):
    qa = ctx.skill("karvey-qa")
    if qa is not None:
        for n, line, _ in body_lines(ctx, qa):
            m = QA_COMMIT_RE.search(line)
            if m and not near_negation(line, m.start()):
                yield qa, n, "QA instructs a commit; QA observes only: every defect goes to findings.md"
        if not QA_DIR_RE.search(ctx.read(qa) or ""):
            yield qa, 1, "karvey-qa does not write its review to docs/spec/changes/{change-id}/qa/"
    deploy = ctx.skill("karvey-deploy")
    if deploy is not None:
        text = ctx.read(deploy) or ""
        for n, line, _ in body_lines(ctx, deploy):
            if re.search(r"\bls\s+-\w*t\w*\b[^\n]*REVISION_PR", line):
                yield deploy, n, "deploy picks the newest REVISION_PR at the root; read changes/{id}/qa/ instead"
        if not QA_DIR_RE.search(text):
            yield deploy, 1, "karvey-deploy does not read the review from docs/spec/changes/{change-id}/qa/"
    for f in sorted(ctx.root.glob("REVISION_PR_*.md")):
        yield f, 1, "review %s sits at the repo root; move it into docs/spec/changes/{change-id}/qa/" % f.name


# --------------------------------------------------------------------------- L-26
STACK_RULE_RE = re.compile(r"\b(Axios|axios|apiService|v-html|RUT)\b")


@check("L-26", "QA text has no stack-specific rules (Axios/apiService, v-html, RUT)", reqs=("076",))
def l26_no_stack_rules_in_qa(ctx):
    qa = ctx.skill("karvey-qa")
    if qa is None:
        return
    for n, line, _ in body_lines(ctx, qa):
        m = STACK_RULE_RE.search(line)
        if m:
            yield qa, n, "stack-specific rule (%s) in QA; it belongs to the team's standards (D9)" % m.group(1)


# --------------------------------------------------------------------------- L-27
GIT_PUSH_RE = re.compile(r"\bgit\s+push\b")
CHECKLIST_HEADING_RE = re.compile(r"^#+\s.*\b(6-step|six-step|pre-deploy)\b.*checklist|^#+\s.*checklist\b", re.I)


@check("L-27", "Deploy never commits the prod approval on integration; the 6-step checklist precedes the "
               "first git push; archive branches chore/archive-{id} before its first commit",
       reqs=("031", "033", "034"))
def l27_deploy_archive_flow(ctx):
    deploy = ctx.skill("karvey-deploy")
    if deploy is not None:
        checklist = first_push = None
        for n, line, lang in body_lines(ctx, deploy):
            if lang is None:
                for m in re.finditer(r"\bcommit\b", line, re.I):
                    if re.search(r"approv", line, re.I) and not near_negation(line, m.start()):
                        yield (deploy, n, "deploy records the prod approval with a commit; record it as a D-NN, "
                                          "in the PR and in the ledger (never a commit on integration)")
                        break
                if checklist is None and CHECKLIST_HEADING_RE.search(line):
                    checklist = n
            if first_push is None and GIT_PUSH_RE.search(line):
                first_push = n
        if checklist is None:
            yield deploy, 1, "karvey-deploy has no pre-deploy checklist step"
        elif first_push is not None and first_push < checklist:
            yield (deploy, first_push, "first git push (line %d) comes before the 6-step checklist (line %d)"
                   % (first_push, checklist))
    archive = ctx.skill("karvey-archive")
    if archive is not None:
        branch = commit = None
        for n, line, _ in body_lines(ctx, archive):
            if branch is None and "chore/archive-" in line:
                branch = n
            if commit is None and re.search(r"\bgit\s+commit\b", line):
                commit = n
        if branch is None:
            yield archive, 1, "karvey-archive never creates chore/archive-{change-id}"
        elif commit is not None and commit < branch:
            yield archive, commit, "archive commits (line %d) before creating chore/archive-{id} (line %d)" % (
                commit, branch)


# --------------------------------------------------------------------------- L-28
NOT_MARKDOWN_RE = re.compile(r"(!=|≠|is not|isn't)\s*[`\"']?markdown\b", re.I)
BACKLOG_DIRECT_RE = re.compile(r"project\.json:clickup\b|project\.json[^\n]{0,60}\bbacklog_list_id\b")
CASCADE_RESTATE_RE = re.compile(r"\b(?i:when)\s+(?:ALL|all|every)\b[^.\n]{0,60}\b(?:tasks?|Features?|features?|children)\b"
                                r"[^.\n]{0,60}\b(?:review|done)\b")
EPIC_DONE_RE = re.compile(r"(?:\bEpic\b[^.\n]{0,40}\bdone\b[^.\n]{0,40}\b(?:all|ALL|every)\s+[Ff]eatures?)|"
                          r"(?:\b(?:all|ALL|every)\s+[Ff]eatures?\b[^.\n]{0,50}\bdone\b[^.\n]{0,30}"
                          r"(?:→|->|move|moves)\s*(?:the\s+)?Epic)")
MARKERS = ("⬜", "🔄", "👀", "✅", "⛔")
INIT_STATE_RE = re.compile(r"\b(todo|in_progress|in progress)\b|⬜|🔄", re.I)


@check("L-28", "Management: no '!= markdown' test, no direct clickup.backlog_list_id read, one cascade "
               "(management-adapters.md) cited not restated, 🙋 in every marker legend, phase-close scope "
               "matches its citations, one initial Epic state in init",
       reqs=("084", "086", "087", "091", "092", "094", "095"))
def l28_management(ctx):
    adapters = ctx.rule("management-adapters.md")
    for path in ctx.text_files():
        is_adapters = path == adapters
        for n, line, _ in iter_lines(ctx.lines(path)):
            if NOT_MARKDOWN_RE.search(line):
                yield (path, n, "tests the tracker with '!= markdown'; use the resolved tool "
                                "(karvey-config.py resolve management: external)")
            if not is_adapters and BACKLOG_DIRECT_RE.search(line):
                yield path, n, "reads project.json:clickup.backlog_list_id directly; resolve management.location"
            if EPIC_DONE_RE.search(line):
                yield path, n, "Epic → done when all Features are: the Epic reaches done only at archive"
            elif not is_adapters and CASCADE_RESTATE_RE.search(line):
                yield path, n, "restates the cascade; cite management-adapters.md (the one cascade) instead"
            if sum(1 for mk in MARKERS if mk in line) >= 4 and "🙋" not in line:
                yield path, n, "marker legend without 🙋 awaiting-human (qualifier of blocked)"
    if adapters is not None and "cascade" not in (ctx.read(adapters) or "").lower():
        yield adapters, 1, "management-adapters.md does not define the cascade"
    rule = ctx.rule("phase-close.md")
    if rule is not None:
        phases = set(phase_skills(ctx))
        named = set(re.findall(r"\b(karvey-[\w-]+)", ctx.read(rule) or "")) & phases
        citers = {s for s in phases if ctx.skill(s) and "phase-close.md" in (ctx.read(ctx.skill(s)) or "")}
        for s in sorted(named - citers):
            yield ctx.skill(s), 1, "phase-close.md names %s, which does not cite phase-close.md at its close" % s
        for s in sorted(citers - named):
            yield rule, 1, "%s cites phase-close.md but the rule does not name it" % s
    init = ctx.skill("karvey-init")
    if init is not None:
        states = {}
        for n, line, _ in body_lines(ctx, init):
            if not re.search(r"\bepic\b", line, re.I):
                continue
            for m in INIT_STATE_RE.finditer(line):
                v = m.group(0).lower()
                v = {"⬜": "todo", "🔄": "in_progress", "in progress": "in_progress"}.get(v, v)
                states.setdefault(v, n)
        if len(states) > 1:
            n = max(states.values())
            yield init, n, "init creates the Epic in more than one initial state (%s); use one" % ", ".join(
                sorted(states))


# --------------------------------------------------------------------------- L-29
PJ_PLACEHOLDER_RE = re.compile(r"\{(?:project\.json:)?(?:(?:notifications|management|branch_flow|clickup)\.[\w.]+|"
                               r"integration|production|feature_prefix|location|backlog_list_id|space_id)\}")
PJ_READ_RE = re.compile(r"\b(jq|python3?|grep|sed|awk|cat|node)\b[^\n]*project\.json")
CONFIG_GET_RE = re.compile(r"karvey-config(?:\.py)?[\"']?\s+get\b")
ASSIGN_RE = re.compile(r"^\s*(?:export\s+|local\s+)?([A-Za-z_]\w*)=\"?\$\(")


def _unquoted_uses(line, var):
    out = []
    for m in re.finditer(r"\$(?:\{%s\}|%s\b)" % (var, var), line):
        quotes = len(re.findall(r'(?<!\\)"', line[:m.start()]))
        if quotes % 2 == 0:
            out.append(m.start())
    return out


@check("L-29", "In command examples a project.json value is interpolated only through "
               "`karvey-config.py get --shell` and double-quoted", reqs=("093",))
def l29_shell_interpolation(ctx):
    for path in ctx.text_files():
        tracked = {}
        for n, line, lang in iter_lines(ctx.lines(path)):
            if lang not in SHELL_FENCES:
                if lang is None:
                    tracked = {}
                continue
            code = line.split(" #", 1)[0] if not line.lstrip().startswith("#") else ""
            if not code.strip():
                continue
            m = ASSIGN_RE.match(code)
            if CONFIG_GET_RE.search(code):
                if m:
                    tracked[m.group(1)] = n
                if "--shell" not in code:
                    yield path, n, "karvey-config.py get without --shell: the value is not validated for a shell"
                continue
            for pm in PJ_PLACEHOLDER_RE.finditer(code):
                yield (path, n, "command interpolates project.json value %s; fetch it with `karvey-config.py get "
                                "<key> --shell` and pass it double-quoted" % pm.group(0))
            if PJ_READ_RE.search(code):
                yield (path, n, "command reads project.json directly; use `karvey-config.py get <key> --shell` "
                                "(validated) instead")
                if m:
                    tracked[m.group(1)] = n
            for var in list(tracked):
                if m and m.group(1) == var:
                    continue
                if _unquoted_uses(code, var):
                    yield path, n, "$%s (a project.json value) is used unquoted; write \"$%s\"" % (var, var)


# --------------------------------------------------------------------------- L-30
DECISION_PATH_RE = re.compile(r"`([^`\s]*decisi[\w]*(?:\.md|/)[^`\s]*)`")


@check("L-30", "H-33: one decision-log path (multi-agent.md = karvey-decisions); no E{1..99} in karvey-init; "
               "one 'For each E2E flow step' block in karvey-test; README names skills /karvey:karvey-<name>",
       reqs=("059",))
def l30_minor_consistency(ctx):
    rule, dec = ctx.rule("multi-agent.md"), ctx.skill("karvey-decisions")
    if rule is not None and dec is not None:
        paths = {}
        for f in (rule, dec):
            for n, line in enumerate(ctx.lines(f), 1):
                for m in DECISION_PATH_RE.finditer(line):
                    p = re.sub(r"^(\{[^}]+\}|<[^>]+>)/", "", m.group(1))
                    if re.search(r"decisions/\*\.md$", p):
                        continue  # the per-period files: read-only legacy shape (wave2 REQ-W2-081), not a log path
                    paths.setdefault(p, (f, n))
        if len(paths) > 1:
            for p, (f, n) in sorted(paths.items()):
                yield (f, n, "decision-log path %s; multi-agent.md and karvey-decisions must cite one path (%s)"
                       % (p, ", ".join(sorted(paths))))
    init = ctx.skill("karvey-init")
    if init is not None:
        for n, line in enumerate(ctx.lines(init), 1):
            if "E{1..99}" in line:
                yield init, n, "karvey-init holds the literal E{1..99}"
    test = ctx.skill("karvey-test")
    if test is not None:
        hits = [n for n, line in enumerate(ctx.lines(test), 1) if "For each E2E flow step" in line]
        for n in hits[1:]:
            yield test, n, "duplicate 'For each E2E flow step' block (first at line %d)" % hits[0]
    for p in (ctx.root / "README.md", ctx.plugin / "README.md"):
        for n, line in enumerate(ctx.lines(p), 1):
            for m in re.finditer(r"/karvey:(?!karvey\b|karvey-)([\w-]+)", line):
                yield p, n, "skill named /karvey:%s; the plugin namespace form is /karvey:karvey-%s" % (
                    m.group(1), m.group(1))


# --------------------------------------------------------------------------- L-31 (T6)
OTHER_TRACKERS_RE = re.compile(r"\b(Jira|Linear|Azure Boards|GitHub Projects|spreadsheet|team's (?:configured )?"
                               r"(?:tracker|task tool)|configured tracker|any tracker)\b", re.I)
CLICKUP_PAIR_RE = re.compile(r"(Markdown|PLAN\.md)`?\s*\+\s*ClickUp|ClickUp\s*\+\s*`?(Markdown|PLAN\.md)")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+")


def public_text(ctx):
    """``[(path, line, text)]`` of the README files and the plugin.json description."""
    out = []
    for p in (ctx.root / "README.md", ctx.plugin / "README.md"):
        for n, line in enumerate(ctx.lines(p), 1):
            out.append((p, n, line))
    pj = ctx.json(plugin_json_path(ctx))
    if isinstance(pj, dict) and isinstance(pj.get("description"), str):
        out.append((plugin_json_path(ctx), line_of(ctx, plugin_json_path(ctx), '"description"'), pj["description"]))
    return out


@check("L-31", "README and plugin.json present the tracker as the team's configured one; ClickUp only as "
               "one option", reqs=("060",))
def l31_tracker_is_configurable(ctx):
    for path, n, text in public_text(ctx):
        if "ClickUp" not in text:
            continue
        for sentence in SENTENCE_SPLIT_RE.split(text):
            if "ClickUp" not in sentence:
                continue
            if CLICKUP_PAIR_RE.search(sentence):
                yield path, n, "presents ClickUp as the tracker (%r); name the team's configured tracker" % (
                    CLICKUP_PAIR_RE.search(sentence).group(0))
            elif not OTHER_TRACKERS_RE.search(sentence):
                yield (path, n, "mentions ClickUp as if it were the tracker; present the team's configured "
                                "tracker (ClickUp is one option)")


# --------------------------------------------------------------------------- L-32
BUG_HEADING_RE = re.compile(r"^##\s+(BUG-\d+)\b")
REF_PATH_RE = re.compile(r"`([\w./-]+\.(?:py|sh|mjs|js|json))(?:[:#][^`]*)?`")
LINT_ID_RE = re.compile(r"\bL-\d\d\b")


@check("L-32", "Every RESUELTO incident in docs/bugs_dev_testing.md names a regression test or lint id "
               "that exists", reqs=("107",))
def l32_resuelto_has_regression(ctx):
    path = ctx.root / "docs" / "bugs_dev_testing.md"
    lines = ctx.lines(path)
    if not lines:
        return
    known = {c.id for c in REGISTRY}
    sections, cur = [], None
    for n, line in enumerate(lines, 1):
        m = BUG_HEADING_RE.match(line)
        if m:
            cur = {"id": m.group(1), "line": n, "body": []}
            sections.append(cur)
        elif line.startswith("## "):
            cur = None
        elif cur is not None:
            cur["body"].append((n, line))
    for s in sections:
        state = None
        for _, line in s["body"]:
            m = re.search(r"\*\*Current state:\*\*\s*([A-Za-z][A-Za-z _-]*)", line)
            if m:
                state = m.group(1).strip()
                break
        if state and incidents.neutral(state) is None:  # REQ-W3-057: neutral names or their aliases
            yield (path, s["line"], "%s: state %r is not a known incident state (accepted: %s)"
                   % (s["id"], state, incidents.accepted()), "warning")
            continue
        if not incidents.is_resolved(state):
            continue
        reg, on = [], False
        for n, line in s["body"]:
            if re.match(r"^###\s+Regression", line, re.I):
                on = True
                continue
            if on and line.startswith("### "):
                break
            if on:
                reg.append((n, line))
        text = "\n".join(line for _, line in reg)
        paths = REF_PATH_RE.findall(text)
        ids = LINT_ID_RE.findall(text)
        if not paths and not ids:
            yield path, s["line"], "%s is RESUELTO but names no regression test or lint id" % s["id"]
            continue
        for p in paths:
            if "/" in p and not (ctx.root / p).exists():
                yield path, s["line"], "%s names regression %s, which does not exist" % (s["id"], p)
        for i in ids:
            if i not in known:
                yield path, s["line"], "%s names lint check %s, which does not exist" % (s["id"], i)


# --------------------------------------------------------------------------- L-33
ID_HEADING_RE = re.compile(r"^#{1,6}\s+((?:D|C|BUG|BL)-\d+)\b")
ID_ROW_RE = re.compile(r"^\|\s*((?:D|C|BUG|BL)-\d+)\s*\|")


def _released_floor(ctx, rel):
    """``{kind: max number}`` of the IDs in ``rel`` on ``origin/{production}``, or None when that line is not
    readable (no remote-tracking ref, not a git repository)."""
    import subprocess
    pj_data = ctx.json(ctx.root / "docs/spec/project.json")
    bf = pj_data.get("branch_flow") if isinstance(pj_data, dict) and isinstance(pj_data.get("branch_flow"), dict) else {}
    prod = bf.get("production") if isinstance(bf.get("production"), str) else "main"
    if not re.match(r"^[A-Za-z0-9._/-]{1,100}$", prod):
        return None
    try:
        cp = subprocess.run(["git", "--no-pager", "show", "origin/%s:%s" % (prod, rel)], cwd=str(ctx.root),
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if cp.returncode != 0:
        return None
    floor = {}
    for m in re.finditer(r"\b(D|C|BUG|BL)-(\d+)\b", cp.stdout.decode("utf-8", "replace")):
        floor[m.group(1)] = max(floor.get(m.group(1), 0), int(m.group(2)))
    return floor


@check("L-33", "Duplicate D-NN, BUG-NN or BL-NN headings: an error for an ID above what origin/{production} holds "
               "(created after the release; the ID tool should have prevented it), a warning for older ones",
       reqs=("W2-071",), severity="warning")
def l33_duplicate_ids(ctx):
    for rel in ("docs/spec/decisions.md", "docs/bugs_dev_testing.md", "docs/spec/backlog.md",
                "docs/spec/incidents-index.md"):
        path = ctx.root / rel
        if not path.is_file():
            continue
        floor = None
        for kind, rx in (("heading", ID_HEADING_RE), ("table row", ID_ROW_RE)):
            seen = {}
            for n, line in enumerate(ctx.lines(path), 1):
                m = rx.match(line)
                if not m:
                    continue
                if m.group(1) in seen:
                    if floor is None:
                        floor = _released_floor(ctx, rel) or {}
                    k, num = m.group(1).split("-")
                    new = k in floor and int(num) > floor[k]
                    msg = "duplicate %s %s (first at line %d): two branches allocated the same number?" % (
                        kind, m.group(1), seen[m.group(1)])
                    if new:
                        yield (path, n, msg + " It is newer than the release line (up to %s-%d): take IDs from "
                                              "karvey-id.py next %s" % (k, floor[k], k), "error")
                    else:
                        yield path, n, msg
                else:
                    seen[m.group(1)] = n


# --------------------------------------------------------------------------- L-46 (wave2-structural)
KS_TOOL_RE = re.compile(r"\b(graphify|obsidian|knowledge[ _-]sync|knowledge graph)\b", re.I)
KS_REQUIRED_RE = re.compile(r"\b(required|requires|mandatory|obligatory|must (?:be )?(?:installed|run|present)|"
                            r"needs? to be installed)\b", re.I)
KS_NEGATION_RE = re.compile(r"\b(not|never|no|optional|nothing|without)\b", re.I)


@check("L-46", "No skill, rule or README describes graphify or knowledge sync as required; the knowledge-sync "
               "rule makes none (or an absent key) the default with no sync step (REQ-W2-079)", reqs=("W2-079",))
def l46_knowledge_sync_optional(ctx):
    files = list(ctx.skills().values()) + sorted(ctx.rules_dir.glob("*.md")) + \
        [p for p in (ctx.root / "README.md", ctx.plugin / "README.md") if p.is_file()]
    for path in files:
        for n, line, lang in iter_lines(ctx.lines(path)):
            if lang is not None:
                continue
            for sentence in re.split(r"(?<=[.;:])\s+", line):
                if KS_TOOL_RE.search(sentence) and KS_REQUIRED_RE.search(sentence) \
                        and not KS_NEGATION_RE.search(sentence):
                    yield path, n, "knowledge sync described as required (%s); it is optional (none by default)" % (
                        sentence.strip()[:80])
    rule = ctx.rule("knowledge-sync.md")
    if rule is not None:
        text = ctx.read(rule) or ""
        row = re.search(r"^\|\s*`none`\s*\|.*$", text, re.M)
        if row and not re.search(r"\*\*yes\*\*[^\n]*absent", row.group(0)):
            yield rule, 1, "rules/knowledge-sync.md must make `none` the default, also when the key is absent"


# --------------------------------------------------------------------------- L-54 (wave2-structural)
@check("L-54", "The hooks README's statusline failure-line sentence carries a guard-case anchor to a "
               "statusline.json case that asserts the line (REQ-W2-082)", reqs=("W2-082",))
def l54_statusline_failure_anchor(ctx):
    readme = ctx.plugin / "hooks" / "README.md"
    if not readme.is_file():
        return
    lines = ctx.lines(readme)
    idx = [i for i, ln_ in enumerate(lines) if "statusline down" in ln_]
    if not idx:
        return
    cases = {cid: c for cid, (c, _f) in table_cases(ctx).items()}
    for i in idx:
        # the sentence may wrap: look from its line to the end of the paragraph (the next blank or list item)
        j, block = i, []
        while j < len(lines) and lines[j].strip() and (j == i or not lines[j].lstrip().startswith("- ")):
            block.append(lines[j])
            j += 1
        ids = [x.strip() for m in ANCHOR_RE.finditer(" ".join(block)) for x in m.group(1).split(",") if x.strip()]
        good = [x for x in ids if x in cases and "statusline down" in json.dumps(cases[x].get("expect", {}))]
        if not good:
            yield (readme, i + 1, "the statusline failure line ('statusline down') has no guard-case anchor to a "
                                  "statusline.json case that asserts it")


# --------------------------------------------------------------------------- L-49 (wave2-structural)
@check("L-49", "A change in deployed (not archived) has its spec-delta merged into the living spec "
               "(karvey-spec-merge.py --check = merged) (REQ-W2-056)", reqs=("W2-056",))
def l49_deployed_spec_merged(ctx):
    import subprocess
    base = ctx.root / "docs/spec/changes"
    if not base.is_dir():
        return
    script = ctx.plugin / "scripts" / "karvey-spec-merge.py"
    if not script.is_file():
        script = Path(__file__).resolve().parent / "karvey-spec-merge.py"
    for d in sorted(base.iterdir()):
        spec = d / "spec.json"
        if d.name == "archive" or not spec.is_file():
            continue
        data = ctx.json(spec)
        if not isinstance(data, dict) or data.get("phase") != "deployed" or not (d / "spec-delta.md").is_file():
            continue
        try:
            cp = subprocess.run([sys.executable, str(script), d.name, "--check", "--json", "--root", str(ctx.root)],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30, check=False)
            res = (json.loads(cp.stdout.decode("utf-8", "replace")) or {}).get("result") or {}
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            yield spec, 1, "cannot check the living spec of deployed change %s: %s" % (d.name, exc)
            continue
        status = res.get("status")
        if status != "merged":
            ids = res.get("pending") or res.get("conflict_ids") or []
            yield (spec, 1, "change %s is deployed but its spec-delta is %s in %s (%s): merge it before production "
                            "(karvey-deploy 2.4-bis) or at archive" % (d.name, status or "not checkable",
                                                                         res.get("target") or "the living spec",
                                                                         ", ".join(ids[:5]) or "-"))


# --------------------------------------------------------------------------- L-42, L-43, L-53 (wave2-structural)
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
COMMIT_WITH_MSG_RE = re.compile(r"\bgit\s+commit\b[^\n]*?(?:\s-[a-zA-Z]*[mF]\b|\s--message\b|\s--file\b)")
GIT_MERGE_RE = re.compile(r"\bgit\s+merge(?!-)\b(?!\s+--abort)")
PUSH_INTEGRATION_RE = re.compile(r"\bgit\s+push\b[^\n]*(?:\$\{?I\b|\{integration\}|\$INTEGRATION\b|\bintegration\b)")


def command_examples(ctx, path):
    """``(lineno, text)`` of every command example: a fenced line (continuations joined) or an inline code span."""
    out, buf, start = [], "", None
    for n, line, lang in iter_lines(ctx.lines(path)):
        if lang is not None and not FENCE_RE.match(line):
            if start is None:
                start = n
            buf += " " + line.strip().rstrip("\\")
            if not line.rstrip().endswith("\\"):
                out.append((start, buf.strip()))
                buf, start = "", None
            continue
        if buf:
            out.append((start, buf.strip()))
            buf, start = "", None
        if lang is None:
            out += [(n, m.group(1)) for m in INLINE_CODE_RE.finditer(line)]
    if buf:
        out.append((start, buf.strip()))
    return out


@check("L-42", "Every git commit example with a message in skill or rule text carries the Karvey-Change trailer "
               "(REQ-W2-043)", reqs=("W2-043",))
def l42_commit_examples_trailer(ctx):
    for path in ctx.text_files():
        for n, text in command_examples(ctx, path):
            if COMMIT_WITH_MSG_RE.search(text) and "Karvey-Change" not in text:
                yield path, n, "git commit example without the Karvey-Change trailer: %s" % text[:80]


@check("L-43", "No instruction merges locally into the integration branch and then pushes it: integration goes "
               "through a PR (REQ-W2-048)", reqs=("W2-048",))
def l43_no_local_merge_push(ctx):
    for path in ctx.text_files():
        ex = command_examples(ctx, path)
        for i, (n, text) in enumerate(ex):
            if not GIT_MERGE_RE.search(text):
                continue
            window = [t for m, t in ex[i:i + 6] if m - n <= 8]
            tail = text[GIT_MERGE_RE.search(text).end():]
            if PUSH_INTEGRATION_RE.search(tail) or any(PUSH_INTEGRATION_RE.search(t) for t in window[1:]):
                yield (path, n, "local merge followed by a push into the integration branch; integrate by a PR "
                                "to {integration} (its CI is the DEV gate)")


SHARED_EVIDENCE_RE = re.compile(r"(?<![\w/}.-])docs/test_(?:evidence|plan)\.md\b")


@check("L-44", "Evidence and test-plan paths in skill and rule text are under changes/{id}/: no docs/test_evidence.md "
               "or docs/test_plan.md shared across changes (REQ-W2-061)", reqs=("W2-061",))
def l44_evidence_inside_change(ctx):
    for path in ctx.text_files():
        for n, line in enumerate(ctx.lines(path), 1):
            m = SHARED_EVIDENCE_RE.search(line)
            if m:
                yield path, n, "%s is shared across changes; use docs/spec/changes/{change-id}/%s" % (
                    m.group(0), m.group(0).split("/")[-1])


PROD_PR_RE = re.compile(r"(?:\bpr\s+create\b|\bmr\s+create\b)[^\n]*(?:--base|--target-branch)\s+\"?\$\{?P\b")
CANARY_RE = re.compile(r"\bcanary\b", re.I)
TRAFFIC_RE = re.compile(r"traffic", re.I)


@check("L-53", "Deploy text: the living-spec merge (2.4-bis) and the release gate (2.8-bis) come before the "
               "production PR; the prod OK is in the PR body at deploy and a D-NN at archive; the step is named "
               "post-deploy verification ('canary' only where traffic is split) (REQ-W2-045, 052, 054, 076)",
       reqs=("W2-045", "W2-052", "W2-054", "W2-076"))
def l53_deploy_order_and_naming(ctx):
    deploy = ctx.skill("karvey-deploy")
    if deploy is None:
        return
    lines = ctx.lines(deploy)

    def first(rx):
        return next((n for n, ln_ in enumerate(lines, 1) if rx.search(ln_)), None)
    spec = first(re.compile(r"karvey-spec-merge\.py"))
    gate = first(re.compile(r"karvey-release-gate\.py[\"']?\s+check\b"))
    pr = first(PROD_PR_RE)
    for label, rx, n in (("2.4-bis", re.compile(r"\b2\.4-bis\b"), spec), ("2.8-bis", re.compile(r"\b2\.8-bis\b"), gate)):
        what = "the living-spec merge" if label == "2.4-bis" else "the release gate"
        if first(rx) is None or n is None:
            yield deploy, 1, "karvey-deploy has no step %s (%s)" % (label, what)
        elif pr is not None and n > pr:
            yield deploy, n, "%s (line %d) comes after the production PR (line %d)" % (what, n, pr)
    if pr is None:
        yield deploy, 1, "karvey-deploy opens no production PR (pr create --base \"$P\")"
    text = "\n".join(lines)
    if not re.search(r"PR body", text):
        yield deploy, 1, "karvey-deploy does not say the prod OK lives in the PR body at deploy"
    if not re.search(r"at archive", text, re.I) or "chore/archive-" not in text:
        yield deploy, 1, "karvey-deploy does not say the prod OK becomes a D-NN on chore/archive-{id} at archive"
    if "post-deploy verification" not in text:
        yield deploy, 1, "karvey-deploy does not name the step 'post-deploy verification'"
    for path in [deploy] + [x for x in (ctx.rule("deploy-workflow.md"),) if x is not None]:
        for n, ln_ in enumerate(ctx.lines(path), 1):
            if CANARY_RE.search(ln_) and not TRAFFIC_RE.search(ln_):
                yield path, n, "'canary' outside traffic splitting; the step is 'post-deploy verification'"


# --------------------------------------------------------------------------- L-45 (wave2-structural)
EPIC_RANGE_RES = (re.compile(r"\bE\{\d+\.\.\d+\}"), re.compile(r"\bE\d+\s*\.\.\s*E?\d+\b"),
                  re.compile(r"\bEpics?\b[^.\n]{0,40}?\b\d+\s*\.\.\s*\d+\b", re.I))


@check("L-45", "No skill bounds Epic numbers to a fixed range (E{1..99}): IDs are unbounded (REQ-W2-071)",
       reqs=("W2-071",))
def l45_no_epic_range(ctx):
    for name, path in ctx.skills().items():
        for n, line in enumerate(ctx.lines(path), 1):
            m = next((x for x in (r.search(line) for r in EPIC_RANGE_RES) if x), None)
            if m:
                yield path, n, "%s bounds Epic numbers (%s); Epic ids are unbounded" % (name, m.group(0))


# --------------------------------------------------------------------------- L-34
SUBAGENT_RE = re.compile(r"sub-?agents?|\bAgent\(|\bTask\(|subagent_type|\bprompt\s*=", re.I)
PJ_WRITE_RE = re.compile(r"\b(write|writes|writing|update|updates|edit|edits|persist|persists|modify|modifies|"
                         r"save|saves|set|sets|create|creates)\b[^.;\n]{0,60}project\.json|"
                         r"project\.json[^.;\n]{0,40}\b(written|updated|edited|persisted|modified|saved)\b", re.I)


def blocks_of(ctx, path):
    """Paragraphs of a SKILL.md body (a fenced block is one paragraph): ``[(first_line, [(n, line)])]``."""
    out, cur = [], []
    for n, line, lang in body_lines(ctx, path):
        if not line.strip() and lang is None:
            if cur:
                out.append(cur)
            cur = []
            continue
        cur.append((n, line))
    if cur:
        out.append(cur)
    return out


@check("L-34", "No subagent prompt in any skill allows writing project.json", reqs=("081",))
def l34_subagents_do_not_write_project_json(ctx):
    for name, path in ctx.skills().items():
        for block in blocks_of(ctx, path):
            text = " ".join(line for _, line in block)
            if not SUBAGENT_RE.search(text):
                continue
            for n, line in block:
                m = PJ_WRITE_RE.search(line)
                if m and not near_negation(line, m.start(), before=40, after=len(m.group(0))):
                    yield (path, n, "%s: a subagent prompt allows writing project.json; subagents never write it "
                                    "(settings travel as a reviewed change)" % name)


# --------------------------------------------------------------------------- L-35
COMPAT_FROM = (3, 12, 0)


def _vtuple(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except (AttributeError, ValueError):
        return (0,)


@check("L-35", "From 3.12.0 on, the top CHANGELOG release carries the CLAUDE.md-destinations compatibility line "
               "and defaults.json records the 3.12.0 release date (D-14)",
       reqs=("099",))
def l35_claude_md_compat_line(ctx):
    changelog = ctx.root / "CHANGELOG.md"
    version, line, block = top_release(ctx)
    if version is None or _vtuple(version) < COMPAT_FROM:
        return
    if not any("CLAUDE.md" in b and re.search(r"compatib|destination|notification", b, re.I) for b in block):
        yield (changelog, line, "release %s lacks the compatibility line for projects that took notification "
                                "destinations from CLAUDE.md tables (REQ-W1-099)" % version)
    # D-14: the pre-3.12 history cut-off the validator uses is the 3.12.0 release date
    dpath = ctx.plugin / "scripts" / "karvey_lib" / "defaults.json"
    d = ctx.json(dpath) if dpath.is_file() else None
    if isinstance(d, dict) and isinstance(d.get("pre_3_12_history"), dict):
        m = re.search(r"^## \[3\.12\.0\] - (\d{4}-\d{2}-\d{2})", ctx.read(changelog) or "", re.M)
        want = m.group(1) if m else None
        got = d["pre_3_12_history"].get("released_on")
        if want and got != want:
            yield (dpath, 1, "pre_3_12_history.released_on is %r; set it to the 3.12.0 release date %s "
                             "(CHANGELOG.md), the D-14 cut-off of karvey-state.py validate" % (got, want))


# --------------------------------------------------------------------------- L-36
IMPL_RULE_RE = re.compile(r"\bdepend|\bselect|\b(?:next|first)\b[^.]*\btask|\bresum", re.I)
IMPL_DEAD_STATE_RE = re.compile(r"\b(pending|completed?|finished)\b", re.I)
IMPL_DEP_RE = re.compile(r"\bdepend", re.I)


@check("L-36", "karvey-impl selects and resumes in logical states: a dependency is satisfied at review or done, "
               "never at a state no skill writes (BUG-05)", reqs=("085",))
def l36_impl_logical_dependencies(ctx):
    impl = ctx.skill("karvey-impl")
    if impl is None:
        return
    stated = False
    for n, line, lang in body_lines(ctx, impl):
        if lang is not None or not IMPL_RULE_RE.search(line):
            continue
        m = IMPL_DEAD_STATE_RE.search(line)
        if m:
            yield (impl, n, "selection/dependency rule uses %r, a task state no skill writes; use the logical "
                            "states (todo | in_progress | review | done | blocked; BUG-05)" % m.group(1))
        if IMPL_DEP_RE.search(line):
            has_review = re.search(r"`review`|\breview\b", line) is not None
            has_done = re.search(r"`done`|\bdone\b", line) is not None
            if has_review and has_done:
                stated = True
            elif has_done and not has_review and re.search(r"\b(until|only when|once)\b", line, re.I):
                yield (impl, n, "a dependency waits for `done` only: impl leaves tasks at `review` and done comes "
                                "at QA, so dependents never start (BUG-05 deadlock); accept `review` or `done`")
    if not stated:
        yield impl, 1, "karvey-impl does not state that a dependency is satisfied at `review` or `done` (REQ-W1-085)"


# --------------------------------------------------------------------------- L-40 (wave2-structural)
@check("L-40", "rules/lanes.md renders schemas/lanes.json between its generated markers, and the lane table lists "
               "every phase for every lane (REQ-W2-011, 021)", reqs=("W2-011", "W2-021"))
def l40_lanes_table(ctx):
    from karvey_lib import lanes as ln
    src = ctx.plugin / "schemas" / "lanes.json"
    rule = ctx.rule("lanes.md")
    if not src.is_file():
        return  # a plugin tree without its own lane table (the lint fixtures)
    table = ctx.json(src) if src.is_file() else None
    if not isinstance(table, dict):
        yield src, 1, "schemas/lanes.json is missing or not JSON"
        return
    bad = ln.problems(table)
    for msg in bad:
        yield src, 1, "lane table: %s" % msg
    if rule is None:
        yield src, 1, "rules/lanes.md is missing (it renders schemas/lanes.json)"
        return
    if bad:
        return
    block = ln.block_of(ctx.read(rule) or "")
    if block is None:
        yield rule, 1, "rules/lanes.md has no %s … %s block" % (ln.BEGIN, ln.END)
    elif block != ln.render(table):
        yield (rule, line_of(ctx, rule, ln.BEGIN), "the lanes block differs from render(schemas/lanes.json): "
               "regenerate it (do not edit the table by hand)")


# --------------------------------------------------------------------------- L-51 (wave2-structural)
JUDGE_TOOLS = ("Read", "Grep", "Glob")


@check("L-51", "Every judged phase has rules/judges/{phase}.md with one section per default lens; the judge prompt "
               "template forbids edits and allows only Read, Grep and Glob (REQ-W2-023, 024)",
       reqs=("W2-023", "W2-024"))
def l51_judge_rubrics(ctx):
    rule = ctx.rule("judges.md")
    if rule is None:
        return  # a plugin tree without judges (the lint fixtures)
    dpath = ctx.plugin / "scripts" / "karvey_lib" / "defaults.json"
    d = ctx.json(dpath) if dpath.is_file() else kl.defaults()
    lenses = ((d or {}).get("judges") or {}).get("lenses") or {}
    if not lenses:
        yield dpath, 1, "defaults.json has no judges.lenses (the default lenses per judged phase)"
    for phase, names in sorted(lenses.items()):
        rp = ctx.rules_dir / "judges" / ("%s.md" % phase)
        text = ctx.read(rp)
        if text is None:
            yield rule, 1, "judged phase %s has no rubric rules/judges/%s.md" % (phase, phase)
            continue
        have = set(re.findall(r"^## Lens: ([a-z0-9-]+)\s*$", text, re.M))
        for lens in names:
            if lens not in have:
                yield rp, 1, "rubric %s.md has no '## Lens: %s' section (a default lens)" % (phase, lens)
    text = ctx.read(rule) or ""
    m = re.search(r"<!-- judge-template -->(.*?)<!-- /judge-template -->", text, re.S)
    if not m:
        yield rule, 1, "rules/judges.md has no <!-- judge-template --> block"
        return
    block, line = m.group(1), line_of(ctx, rule, "<!-- judge-template -->")
    tools = re.search(r"^Allowed tools:\s*(.+)$", block, re.M)
    got = tuple(x.strip() for x in tools.group(1).split(",")) if tools else ()
    if got != JUDGE_TOOLS:
        yield rule, line, "the judge template must allow exactly Read, Grep, Glob (got %s)" % (", ".join(got) or "none")
    if not re.search(r"\bdo not edit any file\b", block, re.I):
        yield rule, line, "the judge template does not say 'Do not edit any file'"


# --------------------------------------------------------------------------- L-41, L-52 (wave2-structural)
SECOND_Q_RE = re.compile(r"shall we advance|advance to the \w+(?: \w+)? phase now\?", re.I)
CLOSING_HEAD_RE = re.compile(r"^##\s+(Advance to the next phase|Close the phase)\s*$")
Y_FLAG_RE = re.compile(r"`-y`|(?<![\w-])-y\b")
PROD_WORD_RE = re.compile(r"\b(prod|production)\b", re.I)
Y_NEGATION_RE = re.compile(r"\b(never|not|no|refus\w*|cannot)\b", re.I)


def _closing_section(ctx, path):
    """``(line, [text lines])`` of a skill's closing section, or ``(None, [])``."""
    lines = ctx.lines(path)
    for i, ln_ in enumerate(lines):
        if CLOSING_HEAD_RE.match(ln_):
            out = []
            for x in lines[i + 1:]:
                if x.startswith("## ") or x.strip() == "---":
                    break
                out.append(x)
            return i + 1, out
    return None, []


@check("L-41", "No phase skill asks a second 'shall we advance?' question: its closing cites rules/gates.md, the one "
               "closing block (REQ-W2-034, 035)", reqs=("W2-034", "W2-035"))
def l41_one_gate_question(ctx):
    if ctx.rule("gates.md") is None:
        return  # a plugin tree without the merged gates (the lint fixtures)
    for name, path in ctx.skills().items():
        for n, line, lang in body_lines(ctx, path):
            if lang is None and SECOND_Q_RE.search(line):
                yield path, n, "%s asks a second advance question; close the phase per rules/gates.md instead" % name
    for p in ctx.rules_dir.glob("*.md"):
        for n, line in enumerate(ctx.lines(p), 1):
            if SECOND_Q_RE.search(line) and p.name != "gates.md":
                yield p, n, "rule asks 'shall we advance?'; the gate question is the one in rules/gates.md"
    last = (ctx.machine().get("phases") or [{}])[-1].get("skill")  # archive closes the cycle: nothing to advance to
    phases = set(phase_skills(ctx)) - {last}
    for name in sorted(phases):
        path = ctx.skills().get(name)
        if path is None:
            continue
        head, body = _closing_section(ctx, path)
        if head is None:
            yield path, 1, "%s has no closing section ('## Advance to the next phase') citing rules/gates.md" % name
        elif not any("rules/gates.md" in x for x in body):
            yield path, head, "%s: the closing section does not cite rules/gates.md" % name


@check("L-52", "-y records role auto and never production: no text describes -y as approving prod, and rules/gates.md "
               "says -y = --role auto (REQ-W2-040)", reqs=("W2-040",))
def l52_y_is_auto_never_prod(ctx):
    rule = ctx.rule("gates.md")
    if rule is None:
        return
    text = ctx.read(rule) or ""
    m = re.search(r"^## `-y`\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m or not re.search(r"`-y` (?:means|records)[^.]*`--role auto`", m.group(1)):
        yield rule, 1, "rules/gates.md has no '## `-y`' section saying -y records --role auto"
    files = list(ctx.skills().values()) + sorted(ctx.rules_dir.glob("*.md"))
    for path in files:
        for n, line in enumerate(ctx.lines(path), 1):
            if Y_FLAG_RE.search(line) and PROD_WORD_RE.search(line) and not Y_NEGATION_RE.search(line):
                yield path, n, "-y described with production and no 'never': -y never approves production"


# --------------------------------------------------------------------------- L-48 (wave2-structural)
W2_DEFAULT_KEYS = ("gates", "judges", "checks", "lanes")
BASELINE_RE = re.compile(r"^baseline-(\d{4}-\d{2}-\d{2})\.json$")


def _w2_keys(project):
    return [k for k in W2_DEFAULT_KEYS if isinstance(project, dict) and k in project]


def _first_commit_setting(root, keys):
    """Date (YYYY-MM-DD) of the first commit whose docs/spec/project.json holds a Wave 2 key, or None."""
    try:
        log = subprocess.run(["git", "log", "--reverse", "--format=%H %cs", "--", "docs/spec/project.json"],
                             cwd=str(root), capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if log.returncode != 0:
        return None
    for line in log.stdout.splitlines():
        sha, _, day = line.partition(" ")
        try:
            show = subprocess.run(["git", "show", "%s:docs/spec/project.json" % sha], cwd=str(root),
                                  capture_output=True, text=True, timeout=10)
            data = json.loads(show.stdout) if show.returncode == 0 else None
        except (OSError, subprocess.SubprocessError, ValueError):
            data = None
        if _w2_keys(data):
            return day
    return None


@check("L-48", "A metrics baseline (docs/spec/retros/baseline-{date}.json) exists before this repo sets any Wave 2 "
               "default in project.json (REQ-W2-006)", reqs=("W2-006", "W2-088"))
def l48_baseline_before_defaults(ctx):
    pjson = ctx.root / "docs" / "spec" / "project.json"
    keys = _w2_keys(ctx.json(pjson) if pjson.is_file() else None)
    if not keys:
        return
    rdir = ctx.root / "docs" / "spec" / "retros"
    dates = sorted(m.group(1) for m in (BASELINE_RE.match(p.name) for p in (rdir.iterdir() if rdir.is_dir() else []))
                   if m)
    if not dates:
        yield (pjson, 1, "project.json sets %s but there is no metrics baseline: run karvey-context.py --metrics "
                         "--from … --to {date} --as-of {date} --json > docs/spec/retros/baseline-{date}.json first"
                         % ", ".join(keys))
        return
    first = _first_commit_setting(ctx.root, keys)
    if first and dates[0] > first:
        yield (rdir / ("baseline-%s.json" % dates[0]), 1,
               "baseline %s is dated after the first commit that set %s (%s): the baseline must precede the "
               "defaults" % (dates[0], ", ".join(keys), first))


# --------------------------------------------------------------------------- L-55 (wave3-optimization)
CORE_WORDS_MAX = 1000
CORE_HEADING_RE = re.compile(r"^##\s+(.*?)\s*$")
CONTRACT_ID_RE = re.compile(r"\{#contract-([a-z0-9-]+)\}")


@check("L-55", "The core rule (rules/_core.md) has at most 1,000 words, every contract heading carries an "
               "{#contract-<id>} id, every contract of contracts.json is anchored there, and it says footnotes "
               "are never opened (REQ-W3-003)", reqs=("W3-003",))
def l55_core_contracts(ctx):
    core = ctx.rules_dir / "_core.md"
    reg_path = ctx.schemas_dir() / "contracts.json" if (ctx.plugin / "schemas").is_dir() else None
    reg = ctx.json(reg_path) if reg_path is not None and reg_path.is_file() else None
    if not core.is_file():
        if reg is not None:
            yield (reg_path, 1, "contracts.json exists but rules/_core.md does not: the contracts have no core")
        return
    words = loadlist.size(core)["words"]
    if words > CORE_WORDS_MAX:
        yield (core, 1, "the core has %d words, over the %d-word limit" % (words, CORE_WORDS_MAX))
    ids = set()
    for n, line, lang in iter_lines(ctx.lines(core)):
        if lang is not None:
            continue
        m = CORE_HEADING_RE.match(line)
        if not m:
            continue
        cm = CONTRACT_ID_RE.search(m.group(1))
        if cm is None:
            yield (core, n, "contract heading without an id: %r needs {#contract-<id>}" % m.group(1))
        else:
            ids.add(cm.group(1))
    if "never opened" not in (ctx.read(core) or ""):
        yield (core, 1, "the core does not say that footnote citations are never opened")
    for c in (reg or {}).get("contracts", []) if isinstance(reg, dict) else []:
        cid = c.get("id") if isinstance(c, dict) else None
        if cid and cid not in ids:
            yield (reg_path, 1, "contract %s is not anchored in the core ({#contract-%s} missing)" % (cid, cid))
        elif cid and c.get("anchor") != "#contract-%s" % cid:
            yield (reg_path, 1, "contract %s: anchor must be #contract-%s (got %r)" % (cid, cid, c.get("anchor")))


# --------------------------------------------------------------------------- L-57 (wave3-optimization)
LOAD_VERB_RE = re.compile(r"\b(?:load|read|open|see first|consult)\b", re.I)


@check("L-57", "A rule names another rule only inside a footnote: rules do not load each other (REQ-W3-005)",
       reqs=("W3-005",))
def l57_rules_cite_rules_in_footnotes(ctx):
    rules_dir = ctx.rules_dir
    if not rules_dir.is_dir():
        return
    for path in sorted(rules_dir.rglob("*.md")):
        text = ctx.read(path) or ""
        for n, line in loadlist.prose_lines(text):
            for tok in loadlist.TOKEN_RE.findall(line):
                alts = loadlist.resolve(tok, rules_dir, path.parent)
                if not alts or all(a.resolve() == path.resolve() for a in alts):
                    continue
                kind = "a load instruction" if LOAD_VERB_RE.search(line) else "a citation"
                yield (path, n, "%s of rule %s outside a footnote: rules do not load each other; make it a footnote "
                                "(`[^r-x]: x.md — context only`)" % (kind, tok))


# --------------------------------------------------------------------------- L-58 (wave3-optimization)
TRACKER_API_RE = re.compile(r"api\.clickup\.com|\bclickup_[a-z]\w*|\bjira issue\b|\baz boards\b|\bgh project\b|"
                            r"linear\.app|api\.linear\b|/rest/api/\d", re.I)


@check("L-58", "Tracker-specific API calls and examples appear only in rules/adapters/{tool}.md, never in a skill "
               "body, a skill reference or a shared rule (REQ-W3-006)", reqs=("W3-006",))
def l58_tracker_detail_in_adapters(ctx):
    files = list(ctx.text_files())
    if ctx.skills_dir.is_dir():
        files += sorted(ctx.skills_dir.glob("*/references/*.md"))
    for path in files:
        for n, line in enumerate(ctx.lines(path), 1):
            m = TRACKER_API_RE.search(line)
            if m:
                yield (path, n, "tool-specific tracker detail %r outside rules/adapters/: move it to the tool's "
                                "adapter" % m.group(0))


# --------------------------------------------------------------------------- L-62 (wave3-optimization)
@check("L-62", "A skill's Load: line names only files that exist (blocking; REQ-W3-072)", reqs=("W3-072",))
def l62_load_entries_exist(ctx):
    for name, path in sorted(ctx.skills().items()):
        text = ctx.read(path) or ""
        for line, entry in loadlist.missing_load_entries(text, ctx.rules_dir, path.parent):
            yield (path, line, "skill %s: Load: names %s, which does not exist" % (name, entry))


# --------------------------------------------------------------------------- L-63 (wave3-optimization)
COST_TRIGGER_RE = re.compile(
    r"\b(?:cost|budget|spend|spending|usd|us\$|token count)\b[^.\n]{0,30}\b(?:exceeds?|is exceeded|goes over|"
    r"reach(?:es)?|passes|limit|cap|threshold)\b|\bover (?:the )?budget\b|\bbecause of (?:the )?(?:cost|budget)\b|"
    r"\b(?:cost|budget|spend) (?:limit|cap|ceiling)\b|\btoo (?:expensive|costly)\b", re.I)
COST_ACTION_RE = re.compile(r"\b(?:stops?|halts?|aborts?|shortens?|skips?|pauses?|cuts? short|truncates?|"
                            r"asks? (?:to|for) confirm(?:ation)?|confirms? before)\b", re.I)


@check("L-63", "No skill or rule text stops, shortens, skips or asks to confirm because of cost: cost is measured, "
               "never capped (D-30, REQ-W3-017)", reqs=("W3-017",))
def l63_no_cost_cap_text(ctx):
    for path in ctx.text_files():
        for n, line, lang in iter_lines(ctx.lines(path)):
            if lang is not None:
                continue
            trig = COST_TRIGGER_RE.search(line)
            act = COST_ACTION_RE.search(line)
            if not trig or not act or near_negation(line, act.start()):
                continue
            yield (path, n, "text %s because of cost (%r): cost is measured, never capped (D-30)" % (
                act.group(0).lower(), trig.group(0)))


# --------------------------------------------------------------------------- L-64 (wave3-optimization)
EXTERNAL_REQUEST_RES = (
    ("a script or image source", re.compile(r"\bsrc\s*=\s*[\"']?\s*(?:https?:)?//", re.I)),
    ("a stylesheet link", re.compile(r"<link\b[^>]*\bhref\s*=\s*[\"']?\s*(?:https?:)?//", re.I)),
    ("an @import", re.compile(r"@import\b", re.I)),
    ("a url()", re.compile(r"url\(\s*[\"']?\s*(?:https?:)?//", re.I)),
)


@check("L-64", "The sponsor template and the method page make no external request (src, link href, @import, url()) "
               "(REQ-W3-024, 068)", reqs=("W3-024", "W3-068"))
def l64_no_external_request(ctx):
    for path in (ctx.plugin / "templates" / "sponsor.html", ctx.root / "docs" / "karvey.html"):
        for n, line in enumerate(ctx.lines(path), 1):
            for what, rx in EXTERNAL_REQUEST_RES:
                if rx.search(line):
                    yield (path, n, "%s makes an external request: the page must be self-contained" % what)


# --------------------------------------------------------------------------- L-66 / L-67 (wave3-optimization)
COUNTRY_ID_RE = re.compile(r"\b(RUT|DNI|CPF|CNPJ|CURP|NIF|NIE|SSN|CUIT|CUIL|RUC|NIT|PESEL|Aadhaar|NINO)\b")


def _template_files(ctx):
    """The shipped templates: ``templates/*`` and the skills (their output templates and field lists)."""
    tdir = ctx.plugin / "templates"
    files = sorted(p for p in tdir.rglob("*") if p.is_file()) if tdir.is_dir() else []
    return files + [p for _, p in sorted(ctx.skills().items())]


@check("L-66", "No template carries a country-specific identifier as a field example or default (REQ-W3-037)",
       reqs=("W3-037",))
def l66_no_country_identifier(ctx):
    for path in _template_files(ctx):
        for n, line in enumerate(ctx.lines(path), 1):
            m = COUNTRY_ID_RE.search(line)
            if m:
                yield (path, n, "country-specific identifier %r in a template: use a neutral field (identifier, "
                                "phone) — the method serves every country" % m.group(1))


SELF_SCORE_RE = re.compile(r"^\s*\|.*\bscore\b[^|]*\(?\s*0\s*[-\u2013]\s*10\s*\)?", re.I)
SELF_SCORE_HEAD_RE = re.compile(r"^\s*#{1,6}.*\bscoring\b.*\b0\s*[-\u2013]\s*10\b", re.I)


@check("L-67", "design-graphic does not score its own output: no 0-10 score table or scoring section in its "
               "instructions — the design judge scores (REQ-W3-039)", reqs=("W3-039",))
def l67_no_design_self_score(ctx):
    path = ctx.skills().get("karvey-design-graphic")
    if path is None:
        return
    for n, line in enumerate(ctx.lines(path), 1):
        if SELF_SCORE_RE.search(line) or SELF_SCORE_HEAD_RE.search(line):
            yield (path, n, "a self-assigned design score in karvey-design-graphic: the design judge scores the "
                            "design (rules/judges/design_graphic.md)")


# --------------------------------------------------------------------------- L-68 (wave3-optimization)
PHASE_AS_FEATURE_RE = re.compile(
    r"\b(?:each|every|a|one)\s+(?:pipeline\s+)?phase\s+(?:maps|is mapped|becomes|is|corresponds)\s+(?:to\s+|as\s+)?"
    r"(?:a|one|its own)\s+feature\b|\bphases?\s+(?:are|as)\s+features\b", re.I)


@check("L-68", "No rule or skill maps a pipeline phase to a Feature: Features are functional areas, phases are an "
               "Epic checklist (REQ-W3-040, 041)", reqs=("W3-040", "W3-041"))
def l68_phase_is_not_a_feature(ctx):
    for path in ctx.text_files():
        for n, line, lang in iter_lines(ctx.lines(path)):
            if lang is not None:
                continue
            m = PHASE_AS_FEATURE_RE.search(line)
            if m and not near_negation(line, m.start()):
                yield (path, n, "a pipeline phase mapped to a Feature (%r): Features are functional areas; phases are "
                                "a checklist or field of the Epic (management-adapters.md)" % m.group(0))


# --------------------------------------------------------------------------- L-69 (wave3-optimization)
@check("L-69", "docs/portability.md has an entry for every hook event of hooks.json and every tool in any "
               "allowed-tools (REQ-W3-053)", reqs=("W3-053",))
def l69_portability_guide(ctx):
    guide = ctx.root / "docs" / "portability.md"
    text = ctx.read(guide)
    if text is None:
        return  # a plugin tree without the guide (the lint fixtures)
    have = set(re.findall(r"`([A-Za-z][\w-]*)`", text))
    hj = ctx.json(ctx.plugin / "hooks" / "hooks.json")
    events = sorted((hj.get("hooks") if isinstance(hj.get("hooks"), dict) else hj).keys()) \
        if isinstance(hj, dict) else []
    for ev in events:
        if not ev.startswith("$") and ev not in have:
            yield (guide, 1, "hook event %s (hooks.json) has no entry in the portability guide" % ev)
    for name, path in sorted(ctx.skills().items()):
        for tool in sorted(allowed_tools(ctx.frontmatter(path)[0])):
            if tool not in have:
                yield (guide, 1, "tool %s (allowed-tools of %s) has no entry in the portability guide" % (tool, name))


# --------------------------------------------------------------------------- L-70 (wave3-optimization)
OS_OPEN_RE = re.compile(r"(?:^|[\s`(:;])(open|xdg-open|start)\s+(?!-)(?:\"[^\"]+\"|'[^']+'|[^\s`)]+)"
                        r"\.(?:html?|pdf|png|svg|md)\b|(?:^|[\s`(:;])xdg-open\b")


@check("L-70", "Skills open a file OS-neutrally (the path, or python3 -m webbrowser <path>) — no bare open, "
               "xdg-open or start (REQ-W3-055)", reqs=("W3-055",))
def l70_os_neutral_open(ctx):
    for name, path in sorted(ctx.skills().items()):
        for n, line in enumerate(ctx.lines(path), 1):
            m = OS_OPEN_RE.search(line)
            if m:
                yield (path, n, "an OS-specific file-opening command in %s: give the path, or `python3 -m webbrowser "
                                "<path>` (stdlib on every OS)" % name)


# --------------------------------------------------------------------------- L-71 (wave3-optimization)
IANA_ZONE_RE = re.compile(r"\b(?:Africa|America|Antarctica|Asia|Atlantic|Australia|Europe|Indian|Pacific)/[A-Z][A-Za-z_]+")
ZONE_ABBR_RE = re.compile(r"\b(?:CLT|CLST|BRT|ART|PST|PDT|EDT|CEST)\b")  # upper case only: "art" is a word
COUNTRY_TIME_RE = re.compile(r"\b(?:Chile|Chilean|Argentin\w*|Mexic\w*|Spain|Spanish|Brazil\w*|Peru\w*|"
                             r"Colombia\w*)\b[^.\n]{0,20}\b(?:time|date|hour|clock)\b", re.I)


@check("L-71", "No rule, skill or hook fixes a country's time or an IANA zone literal: dates use the project's "
               "time_zone or the environment's (REQ-W3-056)", reqs=("W3-056",))
def l71_no_fixed_country_time(ctx):
    files = [p for _, p in sorted(ctx.skills().items())] + sorted(ctx.rules_dir.rglob("*.md")) + \
        sorted((ctx.plugin / "hooks").glob("*.sh"))
    seen = set()
    for path in files:
        if path in seen:
            continue
        seen.add(path)
        for n, line in enumerate(ctx.lines(path), 1):
            m = IANA_ZONE_RE.search(line) or ZONE_ABBR_RE.search(line) or COUNTRY_TIME_RE.search(line)
            if m:
                yield (path, n, "a fixed time zone or country time (%r): use project.json:time_zone or the "
                                "environment's, ISO 8601 with offset" % m.group(0))


# --------------------------------------------------------------------------- L-72 (wave3-optimization)
ACTOR_FIELD_RE = re.compile(r"(?:--by[ =]|\bExecutor:|\bOwner:|\bApproved by:?|\"by\":|(?:^|[\s|-])by:)\**\s*"
                            r"[\"'`]?([^\"'`,;|)\n]*)", re.I)
ROLE_WORDS = {"owner", "the owner", "sponsor", "approver", "executor", "human", "tech lead", "product owner",
              "security officer", "method owner", "team", "reviewer", "role", "architect", "developer", "operator",
              "maintainer", "qa", "auto", "ceo-delegate", "agent", "the team", "the human", "data owner", "dba"}
MODEL_ID_RE = re.compile(r"\b(?:claude|gpt|gemini|llama|mistral)-[\w.-]+", re.I)
INITIAL_NAME_RE = re.compile(r"\b[A-Z]\.\s?[A-Z][a-z]{2,}\b")


def _actor_ok(value):
    v = value.strip().strip("*").strip()
    if not v or v[0] in "{<$[-(…." or v.startswith("..."):
        return True
    low = v.lower()
    first = re.split(r"\s+(?:/|·|—|-|\()", low)[0].strip()
    return low in ROLE_WORDS or first in ROLE_WORDS or low.split(" (")[0] in ROLE_WORDS


@check("L-72", "Example actors in skills and rules are placeholders or roles, never a person's name or a model id "
               "(REQ-W3-060)", reqs=("W3-060",))
def l72_example_actors(ctx):
    files = [p for _, p in sorted(ctx.skills().items())] + sorted(ctx.rules_dir.rglob("*.md"))
    seen = set()
    for path in files:
        if path in seen:
            continue
        seen.add(path)
        for n, line in enumerate(ctx.lines(path), 1):
            if "Part of the Karvey" in line or "Created by" in line:
                continue  # the authorship footer is attribution, not an example actor
            m = MODEL_ID_RE.search(line)
            if m and ACTOR_FIELD_RE.search(line) and m.group(0).lower() in line.lower().split("by", 1)[-1].lower():
                yield (path, n, "a model id (%r) as an example actor: a model is never the actor" % m.group(0))
                continue
            m = INITIAL_NAME_RE.search(line)
            if m and line.lstrip().startswith("|"):
                yield (path, n, "a person's name (%r) in an example row: use a role or {placeholder}" % m.group(0))
                continue
            for a in ACTOR_FIELD_RE.finditer(line):
                val = a.group(1)
                if MODEL_ID_RE.search(val):
                    yield (path, n, "a model id (%r) as an example actor: a model is never the actor" % val.strip())
                elif not _actor_ok(val) and re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", val.strip()):
                    yield (path, n, "a person's name (%r) as an example actor: use a role or {placeholder}"
                           % val.strip()[:40])


# --------------------------------------------------------------------------- L-65 (wave3-optimization)
RISK_STATES = ("open", "mitigated", "accepted", "closed", "moved")


@check("L-65", "schemas/wording.json gives every phase, lane, risk state and label a non-empty wording in every "
               "listed language (REQ-W3-080)", reqs=("W3-080",))
def l65_wording_complete(ctx):
    path = ctx.schemas_dir() / "wording.json"
    data = ctx.json(path)
    if data is None:
        if path.is_file() or (ctx.plugin / "templates" / "sponsor.html").is_file():
            yield (path, 1, "wording.json is missing or not JSON")
        return
    langs = data.get("languages") or []
    if not isinstance(langs, list) or not langs:
        yield (path, 1, "wording.json lists no language")
        return
    required = {"phases": [p.get("id") for p in ctx.machine().get("phases", [])],
                "risk_states": list(RISK_STATES)}
    lanes_ = ctx.json(ctx.schemas_dir() / "lanes.json") or ctx.json(kl.SCHEMAS_DIR / "lanes.json") or {}
    lane_ids = lanes_.get("lanes")
    required["lanes"] = list(lane_ids.keys()) if isinstance(lane_ids, dict) else [
        x if isinstance(x, str) else x.get("id") for x in (lane_ids or [])]
    for cat in ("phases", "lanes", "risk_states", "labels"):
        table = data.get(cat) if isinstance(data.get(cat), dict) else {}
        keys = sorted(set(k for k in required.get(cat, []) if k) | set(table))
        for key in keys:
            entry = table.get(key) if isinstance(table.get(key), dict) else {}
            for lang in langs:
                v = entry.get(lang)
                if not isinstance(v, str) or not v.strip():
                    yield (path, line_of(ctx, path, '"%s"' % key),
                           "%s %r has no wording in %r" % (cat.rstrip("s").replace("_state", " state"), key, lang))


# --------------------------------------------------------------------------- L-47 (wave2-structural), L-73 (wave3)
MODE_CALL_RE = re.compile(r"modes\.(?:resolve|record_hit|default|row|levels_of)\(([^)]*)\)")
CHECK_ID_LITERAL_RE = re.compile(r"[\"']([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)[\"']")
W2_FLIPS = ("schema.strict", "gates.merged", "release.manifest")


def _mode_registry(ctx):
    p = ctx.schemas_dir() / "check-modes.json"
    data = ctx.json(p)
    if data is None:
        p = kl.SCHEMAS_DIR / "check-modes.json"
        data = ctx.json(p)
    return p, data or {"checks": [], "strictness": {"levels": []}}


def _registry_line(ctx, path, cid):
    return line_of(ctx, path, '"id": "%s"' % cid)


@check("L-47", "check-modes.json: every Wave 2 check has a 3.13 and a 4.0 mode; no 3.13 default is blocking; 4.0 "
               "differs from 3.13 only for schema.strict, gates.merged, release.manifest unless the row has a "
               "decision (REQ-W2-083, 085)", reqs=("W2-083", "W2-085"))
def l47_check_modes_w2(ctx):
    path, reg = _mode_registry(ctx)
    for c in reg.get("checks", []):
        d = c.get("defaults") or {}
        if "3.13" not in d and "4.0" not in d:
            continue  # a Wave 3 row (L-73)
        cid = c.get("id")
        ln = _registry_line(ctx, path, cid)
        if set(("3.13", "4.0")) - set(d):
            yield (path, ln, "%s: a Wave 2 check needs both a 3.13 and a 4.0 default" % cid)
            continue
        if d["3.13"] in ("blocking", "merged"):
            yield (path, ln, "%s: the 3.13 default %r refuses; no 3.13 default may (REQ-W2-084)" % (cid, d["3.13"]))
        if d["3.13"] != d["4.0"] and cid not in W2_FLIPS and not c.get("decision"):
            yield (path, ln, "%s: 4.0 differs from 3.13 without a decision reference" % cid)


def _mode_calls(ctx):
    """``(file, line, check_id)`` of every literal check id passed to a ``modes.*`` call in the scripts."""
    base = ctx.plugin / "scripts"
    files = sorted(base.rglob("*.py")) if base.is_dir() else []
    for f in files:
        if f.name == "modes.py" or "tests" in f.parts:
            continue
        text = ctx.read(f) or ""
        for m in MODE_CALL_RE.finditer(text):
            for lit in CHECK_ID_LITERAL_RE.finditer(m.group(1)):
                yield f, text.count("\n", 0, m.start()) + 1, lit.group(1)


@check("L-73", "Every check id a script passes to karvey_lib.modes is registered in check-modes.json, and every row "
               "declares a valid 4.1 default (REQ-W3-061)", reqs=("W3-061",))
def l73_check_ids_registered(ctx):
    path, reg = _mode_registry(ctx)
    rows = {c.get("id"): c for c in reg.get("checks", [])}
    strict = reg.get("strictness") or {}
    for cid, c in sorted(rows.items(), key=lambda kv: str(kv[0])):
        levels = strict.get(c.get("levels", "levels")) or []
        v = (c.get("defaults") or {}).get("4.1")
        if v is None:
            yield (path, _registry_line(ctx, path, cid), "%s: no 4.1 default" % cid)
        elif levels and v not in levels:
            yield (path, _registry_line(ctx, path, cid), "%s: 4.1 default %r is not one of %s" % (
                cid, v, ", ".join(levels)))
    for f, ln, cid in _mode_calls(ctx):
        if cid not in rows:
            yield (f, ln, "check id %r is used here but absent from check-modes.json" % cid)


# --------------------------------------------------------------------------- L-50 (wave2-structural)
def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


@check("L-50", "rules/management-adapters.md: every tool row has a log_time cell (an operation or none); "
               "karvey-impl records the actual with log_time and falls back to the actual columns on none",
       reqs=("W2-007",))
def l50_log_time(ctx):
    rule = ctx.rule("management-adapters.md")
    if rule is not None:
        lines = ctx.lines(rule)
        for i, line in enumerate(lines):
            if not line.startswith("|") or not re.match(r"^\|\s*Tool\s*\|", line):
                continue
            head = [h.lower() for h in _cells(line)]
            if "log_time" not in head:
                yield rule, i + 1, "the adapters table has no log_time column (REQ-W2-007)"
                continue
            k = head.index("log_time")
            for j in range(i + 2, len(lines)):
                if not lines[j].startswith("|"):
                    break
                cells = _cells(lines[j])
                if len(cells) <= k or not cells[k]:
                    yield rule, j + 1, "adapter row %s has no log_time cell (an operation or none)" % (
                        cells[0] if cells else "?")
    impl = ctx.skill("karvey-impl")
    if impl is None:
        return
    text = ctx.read(impl) or ""
    if "log_time" not in text:
        yield impl, 1, "karvey-impl does not record the actual through log_time (REQ-W2-007)"
    elif not re.search(r"log_time[^\n]*\bnone\b[^\n]*actual", text):
        yield impl, 1, "karvey-impl does not fall back to the actual columns when log_time is none"


# --------------------------------------------------------------------------- --paths globs
def expand_braces(pattern):
    """``a/{b,c}/d`` → ``[a/b/d, a/c/d]`` (nested braces supported)."""
    m = re.search(r"\{([^{}]*)\}", pattern)
    if not m:
        return [pattern]
    out = []
    for alt in m.group(1).split(","):
        out += expand_braces(pattern[:m.start()] + alt + pattern[m.end():])
    return out


def glob_regex(pattern):
    """Compile a path glob: ``**`` spans segments, ``*`` and ``?`` stay inside one."""
    i, out = 0, []
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "[":
            j = pattern.find("]", i)
            if j < 0:
                out.append(re.escape(c))
                i += 1
            else:
                out.append(pattern[i:j + 1])
                i = j + 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def path_filter(globs):
    if not globs:
        return None
    pats = []
    for g in globs:
        for p in expand_braces(g):
            pats.append(glob_regex(p[2:] if p.startswith("./") else p))
    return lambda rel: rel is not None and any(p.match(rel) for p in pats)


# --------------------------------------------------------------------------- running
def run_checks(ctx, only=None, paths=None):
    """Every finding of the selected checks, sorted, as dicts."""
    keep = path_filter(paths)
    findings = []
    for c in registry():
        if only and c.id not in only:
            continue
        try:
            items = list(c.fn(ctx))
        except Exception as exc:  # a crashing check is itself an error finding
            items = [(None, 0, "check crashed: %s: %s" % (type(exc).__name__, exc))]
        for item in items:
            path, line, msg = item[0], item[1], item[2]
            sev = item[3] if len(item) > 3 else c.severity
            rel = ctx.rel(path) if path is not None else None
            if keep is not None and not keep(rel):
                continue
            findings.append({"check": c.id, "severity": sev, "file": rel, "line": int(line or 0),
                             "message": msg})
    findings.sort(key=lambda f: (f["file"] or "", f["line"], f["check"], f["message"]))
    return findings


def requirement_ids(ctx, files=None):
    """Every ``REQ-W1-NNN`` number that appears in the requirements text."""
    if files:
        paths = [Path(f) for f in files]
    else:
        base = ctx.root / "docs" / "spec"
        paths = sorted(base.glob("changes/*/requirements.md")) + sorted(base.glob("changes/archive/*/requirements.md"))
        paths += sorted(base.glob("specs/**/spec.md"))
    ids = set()
    for p in paths:
        text = ctx.read(p) or ""
        ids.update(re.findall(r"REQ-W1-(\d{3})", text))
        ids.update("W2-" + n for n in re.findall(r"REQ-W2-(\d{3})", text))
        ids.update("W3-" + n for n in re.findall(r"REQ-W3-(\d{3})", text))
    return ids, paths


def req_label(r):
    """``REQ-W1-NNN`` for a bare number, ``REQ-W2-NNN`` for a ``W2-NNN`` entry."""
    return "REQ-" + r if r.startswith("W") else "REQ-W1-" + r


def cmd_list(ctx, args):
    ids, paths = requirement_ids(ctx, args.requirements)
    missing = []
    rows = []
    for c in registry():
        reqs = ",".join(c.reqs) if c.reqs else "—"
        rows.append("%-5s %-8s REQ %-24s %s" % (c.id, c.severity, reqs, c.title))
        for r in c.reqs:
            if r not in ids:
                missing.append((c.id, r))
    errors = [kl.issue("lint.req_missing", "%s claims %s, absent from the requirements" % (cid, req_label(r)),
                       file=None, path=cid) for cid, r in missing]
    code = kl.EXIT_FINDINGS if missing else kl.EXIT_OK
    result = {"checks": [{"id": c.id, "title": c.title, "severity": c.severity,
                          "reqs": [req_label(r) for r in c.reqs]} for c in registry()],
              "requirements": [ctx.rel(p) for p in paths]}
    if args.format == "json":
        sys.stdout.write(json.dumps(kl.envelope(TOOL, code, result, errors), ensure_ascii=False) + "\n")
    else:
        sys.stdout.write("\n".join(rows) + "\n")
        sys.stdout.write("%d checks\n" % len(rows))
        for cid, r in missing:
            msg = "%s claims %s, absent from the requirements" % (cid, req_label(r))
            if args.format == "github":
                sys.stdout.write("::error title=%s::%s\n" % (cid, msg))
            else:
                sys.stderr.write("[error] %s\n" % msg)
    return code


def _gh_escape(s):
    return s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def report(findings, fmt, checks_run):
    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] != "error"]
    code = kl.EXIT_FINDINGS if errors else kl.EXIT_OK
    if fmt == "json":
        def issue(f):
            return kl.issue(f["check"], f["message"], severity="error" if f["severity"] == "error" else "warning",
                            file=f["file"], path=("line %d" % f["line"]) if f["line"] else None)
        counts = {}
        for f in findings:
            counts.setdefault(f["check"], {"error": 0, "warning": 0})[
                "error" if f["severity"] == "error" else "warning"] += 1
        env = kl.envelope(TOOL, code, {"checks_run": checks_run, "counts": counts, "findings": findings},
                          [issue(f) for f in errors], [issue(f) for f in warnings])
        sys.stdout.write(json.dumps(env, ensure_ascii=False) + "\n")
        return code
    for f in findings:
        if fmt == "github":
            kind = "error" if f["severity"] == "error" else "warning"
            loc = ""
            if f["file"]:
                loc = " file=%s" % f["file"]
                if f["line"]:
                    loc += ",line=%d" % f["line"]
            sys.stdout.write("::%s%s,title=%s::%s\n" % (kind, loc, f["check"], _gh_escape(f["message"])) if loc
                             else "::%s title=%s::%s\n" % (kind, f["check"], _gh_escape(f["message"])))
        else:
            loc = f["file"] or "(plugin)"
            if f["line"]:
                loc += ":%d" % f["line"]
            sys.stdout.write("%s: %s %s: %s\n" % (loc, f["check"], f["severity"], f["message"]))
    if fmt == "text":
        sys.stdout.write("%d errors, %d warnings (%d checks)\n" % (len(errors), len(warnings), len(checks_run)))
    return code


def default_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                             timeout=5, check=False)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return os.getcwd()


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        sys.exit(kl.EXIT_USAGE)


def build_parser():
    p = _Parser(prog="lint-plugin.py", description="Karvey plugin linter (L-01..L-36).")
    p.add_argument("--root", help="repository root (default: git top level)")
    p.add_argument("--plugin", help="plugin directory (default: <root>/plugins/karvey)")
    p.add_argument("--only", help="comma list of check ids (L-NN)")
    p.add_argument("--paths", action="append", default=[], metavar="GLOB",
                   help="keep only findings in files matching GLOB (repeatable; {a,b} and ** supported)")
    p.add_argument("--format", choices=("text", "json", "github"), default="text")
    p.add_argument("--list", action="store_true", help="print the registry and check its REQ references")
    p.add_argument("--requirements", action="append", default=[], metavar="FILE",
                   help="requirements file(s) for --list (default: docs/spec/changes/*/requirements.md)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = Path(args.root) if args.root else Path(default_root())
    if not root.is_dir():
        sys.stderr.write("lint-plugin.py: error: root %s is not a directory\n" % root)
        return kl.EXIT_USAGE
    ctx = Ctx(root, args.plugin)
    if args.list:
        return cmd_list(ctx, args)
    only = None
    if args.only:
        only = {x.strip().upper() for x in args.only.split(",") if x.strip()}
        known = {c.id for c in REGISTRY}
        unknown = sorted(only - known)
        if unknown:
            sys.stderr.write("lint-plugin.py: error: unknown check id(s): %s\n" % ", ".join(unknown))
            return kl.EXIT_USAGE
    findings = run_checks(ctx, only=only, paths=args.paths)
    checks_run = [c.id for c in registry() if not only or c.id in only]
    return report(findings, args.format, checks_run)


if __name__ == "__main__":
    sys.exit(main())
