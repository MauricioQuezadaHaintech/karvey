"""The project-upgrade engine (architecture §1.3, §1.4 of the project-upgrade change).

After a plugin update, a project may need upgrade steps: migrate legacy file shapes, drop copied hook
shims, add team settings, adopt new defaults. The steps are **data plus pure functions**:

- the catalogue ``upgrade-steps.json`` declares every step (validated against
  ``schemas/upgrade-steps.schema.json`` and the invariants below, REQ-UP-008);
- each step's ``check`` / ``fix`` lives in ``upgrade_steps.REGISTRY`` and only reads the project
  through a read-only :class:`Probe`, returning planned :class:`Edit` objects;
- this engine is the **only writer**: path confinement, compare-and-swap atomic writes, the preview
  digest and the journal are implemented once, here.

Python >= 3.9, standard library only. Every subprocess is an argv list.
"""
import fnmatch
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import LIB_DIR, PLUGIN_ROOT, SCHEMAS_DIR, SCRIPTS_DIR
from . import __version__ as INSTALLED
from . import atomicio
from . import schema_lite as sl

CATALOGUE_PATH = LIB_DIR / "upgrade-steps.json"
SCHEMA_PATH = SCHEMAS_DIR / "upgrade-steps.schema.json"
REQUIRED_FIELDS = ("id", "since", "check", "fix", "dry_run", "human", "risk")
WRITE_SCOPES = ("project", "git_dir")
STEP_DEFAULTS = {"title": "", "report_only": False, "writes": ["project"], "cost": "low", "params": {}}


# --------------------------------------------------------------------------- catalogue (REQ-UP-008)
class CatalogueError(Exception):
    """The catalogue is missing, unreadable or invalid: nothing is evaluated."""


def _step_name(step, index):
    if isinstance(step, dict) and isinstance(step.get("id"), str) and step["id"]:
        return step["id"]
    return "#%d" % (index + 1)


def _default_registry():
    from . import upgrade_steps
    return upgrade_steps.REGISTRY


def load_catalogue(path=None, registry=None):
    """The validated step list, in catalogue order, with the optional fields filled in.

    Raises :class:`CatalogueError` naming the step and the field (``step <id>: missing field <f>``).
    """
    p = Path(path) if path is not None else CATALOGUE_PATH
    try:
        with open(p, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise CatalogueError("step catalogue not found: %s" % p.name)
    except (OSError, ValueError) as exc:
        raise CatalogueError("step catalogue unreadable: %s (%s)" % (p.name, exc))
    if registry is None:
        registry = _default_registry()
    if not isinstance(data, dict):
        raise CatalogueError("step catalogue is not a JSON object")
    steps = data.get("steps")
    # the per-step required fields first, so the message names the step and the field
    if isinstance(steps, list):
        for i, st in enumerate(steps):
            if not isinstance(st, dict):
                raise CatalogueError("step %s: not an object" % _step_name(st, i))
            for f in REQUIRED_FIELDS:
                if f not in st:
                    raise CatalogueError("step %s: missing field %s" % (_step_name(st, i), f))
    try:
        with open(SCHEMA_PATH, encoding="utf-8-sig") as fh:
            schema = json.load(fh)
        issues = sl.validate(data, schema, registry={})
    except (OSError, ValueError, sl.SchemaError) as exc:
        raise CatalogueError("step catalogue schema unusable: %s" % exc)
    errs = [i for i in issues if i["severity"] == "error"]
    if errs:
        first = errs[0]
        where = first.get("path") or "$"
        name = "catalogue"
        if where.startswith("$.steps["):
            try:
                idx = int(where[len("$.steps["):].split("]", 1)[0])
                name = "step %s" % _step_name(steps[idx], idx)
            except (ValueError, IndexError, TypeError):
                pass
        raise CatalogueError("%s: %s: %s" % (name, where, first["message"]))
    seen = set()
    out = []
    for i, st in enumerate(steps):
        sid = st["id"]
        if sid in seen:
            raise CatalogueError("step %s: duplicate id" % sid)
        seen.add(sid)
        if st["check"] not in registry:
            raise CatalogueError("step %s: unknown check function %s" % (sid, st["check"]))
        if st["fix"] is not None and st["fix"] not in registry:
            raise CatalogueError("step %s: unknown fix function %s" % (sid, st["fix"]))
        full = dict(STEP_DEFAULTS)
        full["params"] = {}
        full.update(st)
        if full["human"] and full["fix"] is not None:
            raise CatalogueError("step %s: a human step has fix null" % sid)
        if full["report_only"] and full["fix"] is not None:
            raise CatalogueError("step %s: a report_only step has fix null" % sid)
        if full["fix"] is None and not full["human"] and not full["report_only"]:
            raise CatalogueError("step %s: fix null on a non-human step requires report_only" % sid)
        if not full["human"] and not set(full["writes"]) <= set(WRITE_SCOPES):
            raise CatalogueError("step %s: writes outside %s" % (sid, "|".join(WRITE_SCOPES)))
        out.append(full)
    return out


# --------------------------------------------------------------------------- results and edits (§1.4)
STATUSES = ("nothing", "applies", "human", "report", "needs-input", "check-failed")
EDIT_OPS = ("write", "delete")


@dataclass
class Edit:
    """One planned file change. ``path`` is relative POSIX (to the project root for scope ``project``,
    to the git common dir for scope ``git_dir``); ``before_sha256`` None = the file is created."""
    op: str
    path: str
    scope: str = "project"
    before_sha256: object = None
    text: object = None

    def __post_init__(self):
        if self.op not in EDIT_OPS:
            raise ValueError("edit op must be one of %s" % "|".join(EDIT_OPS))
        if self.scope not in WRITE_SCOPES:
            raise ValueError("edit scope must be one of %s" % "|".join(WRITE_SCOPES))
        if self.op == "write" and not isinstance(self.text, str):
            raise ValueError("a write edit carries text")


@dataclass
class StepResult:
    status: str
    summary: str = ""
    edits: list = field(default_factory=list)
    diff: str = ""
    instructions: str = ""
    warnings: list = field(default_factory=list)
    inputs_needed: list = field(default_factory=list)

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError("status must be one of %s" % "|".join(STATUSES))


class CheckFailed(Exception):
    """Raised by a check that cannot decide (unreadable input): the row becomes ``check-failed``."""


class NeedsInput(Exception):
    """Raised by a fix whose values are missing or invalid: ``apply`` refuses naming them."""


class ProbeError(Exception):
    """A read the Probe does not allow (outside the root, a git sub-command off the list, …)."""


class DeadlineExceeded(Exception):
    """The probe's deadline passed (the hook's budget, REQ-UP-005)."""


# --------------------------------------------------------------------------- the read-only Probe
GIT_READ_ALLOW = (("rev-parse",), ("symbolic-ref",), ("show",), ("status", "--porcelain"), ("ls-files",),
                  ("config", "--get"))
HOME_FILES = (".claude/settings.json", ".claude/settings.local.json", ".claude/CLAUDE.md")
HOME_READ_MAX = 1024 * 1024
_MODULES = {}


def _load_script(name, filename):
    """``karvey-state.py`` / ``karvey-config.py`` loaded once with importlib (as karvey-context.py does)."""
    if name not in _MODULES:
        spec = importlib.util.spec_from_file_location(name, str(SCRIPTS_DIR / filename))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MODULES[name] = mod
    return _MODULES[name]


def state_module():
    return _load_script("karvey_state", "karvey-state.py")


def config_module():
    return _load_script("karvey_config", "karvey-config.py")


def _sha_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class JsonDoc:
    """A JSON file as a step sees it: data, the format to write it back with, and its content hash."""
    __slots__ = ("path", "data", "fmt", "sha256", "text")

    def __init__(self, path, data, fmt, sha256, text):
        self.path, self.data, self.fmt, self.sha256, self.text = path, data, fmt, sha256, text

    def dumps(self, data):
        return atomicio.dumps(data, **self.fmt)


class Probe:
    """The read-only view a step sees (§1.4). ``overlay`` maps a relative POSIX path to the pending
    text (``None`` = pending deletion), so a later step reads what an earlier one will write."""

    def __init__(self, root, overlay=None, home=None, installed=None, deadline=None):
        self.root = Path(os.path.realpath(str(root)))
        self.overlay = overlay if overlay is not None else {}
        self._home = home
        self.installed = installed or INSTALLED
        self.deadline = deadline

    # -- deadline (the hook's budget)
    def check_deadline(self):
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise DeadlineExceeded("probe deadline passed")

    # -- the project tree
    def _norm(self, rel):
        if not isinstance(rel, str) or not rel:
            raise ProbeError("empty path")
        rel = rel.replace("\\", "/")
        if rel.startswith("/") or (len(rel) > 1 and rel[1] == ":"):
            raise ProbeError("absolute path refused: %s" % rel)
        parts = [p for p in rel.split("/") if p not in ("", ".")]
        if ".." in parts:
            raise ProbeError("'..' refused: %s" % rel)
        return "/".join(parts)

    def _abs(self, rel):
        rel = self._norm(rel)
        p = self.root / rel
        real = Path(os.path.realpath(str(p)))
        if real != self.root and self.root not in real.parents:
            raise ProbeError("outside the project root: %s" % rel)
        return rel, p

    def exists(self, rel):
        rel, p = self._abs(rel)
        if rel in self.overlay:
            return self.overlay[rel] is not None
        return p.is_file()

    def read_text(self, rel):
        """The file's text (overlay first), or None when absent."""
        rel, p = self._abs(rel)
        if rel in self.overlay:
            return self.overlay[rel]
        try:
            return p.read_bytes().decode("utf-8")
        except (FileNotFoundError, IsADirectoryError, NotADirectoryError):
            return None
        except UnicodeDecodeError as exc:
            raise CheckFailed("not UTF-8: %s (%s)" % (rel, exc))
        except OSError as exc:
            raise CheckFailed("unreadable: %s (%s)" % (rel, exc))

    def sha256(self, rel):
        """Content hash of the current (overlay) text, or None when absent."""
        text = self.read_text(rel)
        return None if text is None else _sha_text(text)

    def read_json(self, rel):
        """A :class:`JsonDoc`, or None when absent. Invalid JSON raises :class:`CheckFailed`."""
        text = self.read_text(rel)
        if text is None:
            return None
        return _parse_json(text, rel)

    def glob(self, pattern):
        """Relative POSIX paths of files matching ``pattern`` under the root (overlay applied; ``.git`` and
        ``node_modules`` never listed)."""
        pattern = self._norm(pattern)
        out = set()
        for p in self.root.glob(pattern):
            rel = p.relative_to(self.root).as_posix()
            if ".git" in rel.split("/") or "node_modules" in rel.split("/") or not p.is_file():
                continue
            out.add(rel)
        for rel, text in self.overlay.items():
            if text is None:
                out.discard(rel)
            elif fnmatch.fnmatchcase(rel, pattern) or Path(rel).match(pattern):
                out.add(rel)
        return sorted(out)

    # -- git (read-only sub-commands, argv only)
    def git_read(self, *args):
        """``(returncode, stdout)`` of an allowed read-only git sub-command."""
        args = [str(a) for a in args]
        if not any(tuple(args[:len(a)]) == a for a in GIT_READ_ALLOW):
            raise ProbeError("git sub-command not allowed for a step: %s" % " ".join(args[:2]))
        try:
            cp = subprocess.run(["git", "--no-optional-locks"] + args, cwd=str(self.root), stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=5, check=False)
        except FileNotFoundError:
            return 127, ""
        except subprocess.TimeoutExpired:
            return 124, ""
        return cp.returncode, cp.stdout.decode("utf-8", "replace")

    # -- the user's home (three fixed files, read only)
    @property
    def home(self):
        return Path(self._home) if self._home else Path(os.path.expanduser("~"))

    def home_read(self, rel):
        """The text of one of the three allowed home files, or None when absent."""
        if rel not in HOME_FILES:
            raise ProbeError("home file not allowed: %s" % rel)
        p = self.home / rel
        try:
            size = p.stat().st_size
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise CheckFailed("unreadable: ~/%s (%s)" % (rel, exc))
        if size > HOME_READ_MAX:
            raise CheckFailed("unreadable: ~/%s is larger than %d bytes" % (rel, HOME_READ_MAX))
        try:
            return p.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise CheckFailed("unreadable: ~/%s (%s)" % (rel, exc))

    def home_json(self, rel):
        text = self.home_read(rel)
        if text is None:
            return None
        return _parse_json(text, "~/" + rel)

    # -- the installed plugin's own files (shipped shims, schemas)
    def plugin_read(self, rel):
        rel = self._norm(rel)
        p = PLUGIN_ROOT / rel
        try:
            return p.read_bytes().decode("utf-8")
        except FileNotFoundError:
            return None
        except (OSError, UnicodeDecodeError) as exc:
            raise CheckFailed("unreadable plugin file %s (%s)" % (rel, exc))

    def plugin_json(self, rel):
        text = self.plugin_read(rel)
        return None if text is None else _parse_json(text, rel)

    # -- the state and config tools, in process
    @property
    def state(self):
        return state_module()

    @property
    def config(self):
        return config_module()


def _parse_json(text, where):
    fmt = atomicio.detect_format(text)
    body = text[1:] if fmt["bom"] else text
    try:
        data = json.loads(body)
    except ValueError as exc:
        raise CheckFailed("invalid JSON: %s (%s)" % (where, exc))
    return JsonDoc(where, data, fmt, _sha_text(text), text)


def overlay_apply(overlay, edits):
    """Record ``edits`` (scope ``project``) in ``overlay`` so later reads see them."""
    for e in edits:
        if e.scope == "project":
            overlay[e.path] = e.text if e.op == "write" else None


# --------------------------------------------------------------------------- the plan (§1.4, REQ-UP-007..010)
COST_ORDER = {"low": 0, "scan": 1}
_UNSET = object()


def _registry(registry):
    return registry if registry is not None else _default_registry()


def run_check(step, probe, registry=None):
    """One step's check as a :class:`StepResult`; a raising check becomes ``check-failed`` (REQ-UP-009).

    The catalogue's flags win over the function: a ``human`` or ``report_only`` step never carries edits
    (a check may downgrade itself to ``human``, never upgrade itself to a write, §3.3)."""
    fn = _registry(registry)[step["check"]]
    try:
        res = fn(probe, step["params"])
    except DeadlineExceeded:
        raise
    except CheckFailed as exc:
        res = StepResult("check-failed", summary="check-failed: %s" % exc)
    except Exception as exc:  # a broken check must not stop the others
        res = StepResult("check-failed", summary="check-failed: %s: %s" % (type(exc).__name__, exc))
    if not isinstance(res, StepResult):
        res = StepResult("check-failed", summary="check-failed: %s returned %s" % (step["check"], type(res).__name__))
    if step["human"] and res.status in ("applies", "needs-input"):
        res.status = "human"
    if step["report_only"] and res.status in ("applies", "needs-input"):
        res.status = "report"
    if step["human"] or step["report_only"] or res.status not in ("applies",):
        res.edits = []
    return res


def current_branch(root):
    rc, out = _git(["symbolic-ref", "--quiet", "--short", "HEAD"], root)
    return out.strip() if rc == 0 and out.strip() else None


def _git(args, cwd, timeout=5, env=None):
    """``(returncode, stdout)`` of ``git <args>`` (argv, never a shell; stdout not stripped)."""
    try:
        cp = subprocess.run(["git"] + list(args), cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=timeout, check=False, env=env)
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired:
        return 124, ""
    except (NotADirectoryError, OSError):
        return 128, ""
    out = cp.stdout.decode("utf-8", "replace")
    if cp.returncode != 0 and not out:
        out = cp.stderr.decode("utf-8", "replace")
    return cp.returncode, out


@dataclass
class Plan:
    from_version: object
    to_version: str
    computed_on: object
    steps: list
    results: dict
    exit: int

    def rows(self):
        return list(self.steps)

    def as_json(self):
        return {"from": self.from_version, "to": self.to_version, "computed_on": self.computed_on,
                "steps": [dict(r) for r in self.steps]}

    def nothing_to_do(self):
        return all(r["status"] == "nothing" for r in self.steps)

    def table(self):
        head = "Karvey project upgrade %s → %s (computed on %s)" % (
            self.from_version or "(none resolved)", self.to_version, self.computed_on or "no branch")
        if self.nothing_to_do():
            return head + "\nnothing to do: every step is already satisfied."
        lines = [head, "", "| step | what changes | dry-run | risk | needs human |", "|---|---|---|---|---|"]
        for r in self.steps:
            if r["status"] == "nothing":
                continue
            what = r["summary"] or r["status"]
            if r["status"] not in ("applies",):
                what = "[%s] %s" % (r["status"], what)
            lines.append("| %s | %s | %s | %s | %s |" % (r["id"], what.replace("|", "/"),
                                                        "yes" if r["dry_run"] else "no", r["risk"],
                                                        "yes" if r["human"] else "no"))
        done = [r["id"] for r in self.steps if r["status"] == "nothing"]
        if done:
            lines.append("")
            lines.append("already satisfied: %s" % ", ".join(done))
        for r in self.steps:
            for w in r["warnings"]:
                lines.append("  %s: %s" % (r["id"], w))
        return "\n".join(lines)


def _row(step, res):
    return {"id": step["id"], "since": step["since"], "title": step["title"], "status": res.status,
            "summary": res.summary, "dry_run": step["dry_run"], "risk": step["risk"],
            "human": bool(step["human"] or res.status == "human"), "report_only": step["report_only"],
            "inputs_needed": list(res.inputs_needed), "warnings": list(res.warnings)}


def plan(root, steps=None, registry=None, home=None, seen_version=_UNSET, installed=None):
    """Evaluate **every** step in catalogue order over one overlay. Writes nothing (REQ-UP-010)."""
    if steps is None:
        steps = load_catalogue(registry=registry)
    overlay = {}
    probe = Probe(root, overlay=overlay, home=home, installed=installed)
    rows, results = [], {}
    for st in steps:
        res = run_check(st, probe, registry)
        results[st["id"]] = res
        rows.append(_row(st, res))
        if res.status == "applies" and res.edits:
            overlay_apply(overlay, res.edits)
    if seen_version is _UNSET:
        rec = read_seen(root) if "read_seen" in globals() else None
        seen_version = rec["version"] if rec else None
    failed = any(r["status"] == "check-failed" for r in rows)
    return Plan(seen_version, probe.installed, current_branch(root), rows, results, 1 if failed else 0)


def any_applicable(root, deadline, steps=None, registry=None, home=None):
    """The hook's short-circuit probe (REQ-UP-005): ``found`` (a step does not return ``nothing``),
    ``failed`` (a check raised), ``timeout`` (the deadline passed first) or ``none``.

    Steps run in ``cost`` order (``low`` first, then ``scan``) and it stops at the first hit."""
    if steps is None:
        steps = load_catalogue(registry=registry)
    ordered = sorted(steps, key=lambda s: COST_ORDER.get(s["cost"], 1))
    probe = Probe(root, home=home, deadline=deadline)
    for st in ordered:
        if time.monotonic() > deadline:
            return "timeout"
        try:
            res = run_check(st, probe, registry)
        except DeadlineExceeded:
            return "timeout"
        if res.status == "check-failed":
            return "failed"
        if res.status != "nothing":
            return "found"
    return "none"
