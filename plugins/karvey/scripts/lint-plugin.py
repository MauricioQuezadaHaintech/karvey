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
                fence, lang = m.group(1)[0] * 3, (m.group(2) or "").lower()
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
    return ids, paths


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
    errors = [kl.issue("lint.req_missing", "%s claims REQ-W1-%s, absent from the requirements" % (cid, r),
                       file=None, path=cid) for cid, r in missing]
    code = kl.EXIT_FINDINGS if missing else kl.EXIT_OK
    result = {"checks": [{"id": c.id, "title": c.title, "severity": c.severity,
                          "reqs": ["REQ-W1-" + r for r in c.reqs]} for c in registry()],
              "requirements": [ctx.rel(p) for p in paths]}
    if args.format == "json":
        sys.stdout.write(json.dumps(kl.envelope(TOOL, code, result, errors), ensure_ascii=False) + "\n")
    else:
        sys.stdout.write("\n".join(rows) + "\n")
        sys.stdout.write("%d checks\n" % len(rows))
        for cid, r in missing:
            msg = "%s claims REQ-W1-%s, absent from the requirements" % (cid, r)
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
    p = _Parser(prog="lint-plugin.py", description="Karvey plugin linter (L-01..L-35).")
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
