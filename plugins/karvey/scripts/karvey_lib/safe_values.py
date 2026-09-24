"""Safe values: untrusted ``project.json`` / ``spec.json`` values checked before a command.

Architecture §3.1 (F-02 / S-01, REQ-W1-093, REQ-W1-097). ``project.json`` and ``spec.json`` are
committed files that can come from a contributor, a client repo or a cloned template, so every
value that is about to reach a command line is validated here first.

Two layers, both mandatory:

1. **Common refusal** (every kind): control characters (``\\x00-\\x1f``, ``\\x7f``), the
   characters `` ` $ ; | & < > \\ ( ) { } `` and ``"`` and a leading ``-`` (option injection).
   Two kind-specific exemptions exist because the kind's own pattern needs the character and
   confines it: ``{`` ``}`` for the Markdown location template (``docs/spec/changes/{change-id}/
   PLAN.md``), and ``\\`` for Azure Boards area/iteration paths (``Project\\Area``), where the
   pattern only admits it between two path segments.
2. **The kind's pattern** (§3.1 table): per channel for ``notifications.target``, per tool for
   ``management.location`` / ``management.sprints``, ``branchName`` / ``refPrefix`` for
   ``branch_flow.*``, the status-name pattern for status maps.

A value that fails raises :class:`UnsafeValue`, which names the key, the kind and the rule it
broke; callers turn it into exit 3. Nothing here runs a shell: the one subprocess call
(``git check-ref-format --branch``) is an argv list with a timeout.
"""
import posixpath
import re
import subprocess

# ----------------------------------------------------------------------------- common refusal
FORBIDDEN_CHARS = frozenset("`$;|&<>\\(){}\"")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")

# Kinds whose own pattern needs (and confines) a character of FORBIDDEN_CHARS.
KIND_EXEMPTIONS = {
    "location:markdown": frozenset("{}"),
    "location:azure-boards": frozenset("\\"),
    "sprints:azure-boards": frozenset("\\"),
}

# ----------------------------------------------------------------------------- the §3.1 table
_A = re.ASCII
TARGET_PATTERNS = {
    "google-chat": re.compile(r"^spaces/[A-Za-z0-9_-]{1,64}$"),
    "slack": re.compile(r"^(#[a-z0-9._-]{1,80}|C[A-Z0-9]{8,12})$"),
    "teams": re.compile(r"^[\w .:@-]{1,128}$", _A),
    "email": re.compile(r"^[^@\s]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,}$"),
    "webhook": re.compile(r"^[A-Z][A-Z0-9_]{2,63}$"),
}
CHANNEL_ALIASES = {"google_chat": "google-chat"}
NO_TARGET_CHANNELS = frozenset({"none"})

_AZURE_PATH = re.compile(r"^[\w .-]{1,128}(\\[\w .-]{1,128}){0,4}$", _A)
LOCATION_PATTERNS = {
    "clickup": re.compile(r"^\d{1,20}$", _A),
    "jira": re.compile(r"^[A-Z][A-Z0-9_]{1,9}$"),
    "linear": re.compile(r"^[A-Za-z0-9_-]{1,32}$"),
    "azure-boards": _AZURE_PATH,
    "github-projects": re.compile(r"^[A-Za-z0-9-]{1,39}/\d{1,6}$"),
    "markdown": re.compile(r"^docs/spec/[A-Za-z0-9_./{}-]+\.md$"),
    # Not in the §3.1 table: an "other" tool gets a conservative generic name.
    "other": re.compile(r"^[\w .:/@-]{1,128}$", _A),
}
TOOL_ALIASES = {"none": "markdown"}
SPREADSHEET_EXTENSIONS = (".csv", ".xlsx", ".ods", ".md")

# management.sprints is not in the §3.1 table: a ClickUp folder id, an Azure iteration path,
# otherwise a conservative generic name.
SPRINT_PATTERNS = {
    "clickup": re.compile(r"^\d{1,20}$", _A),
    "azure-boards": _AZURE_PATH,
}
GENERIC_SPRINT = re.compile(r"^[\w .:/-]{1,128}$", _A)

STATUS_PATTERN = re.compile(r"^[^\x00-\x1f`$\\;|&<>]{1,64}$")
BRANCH_PATTERN = re.compile(r"^(?!-)(?!.*\.\.)[A-Za-z0-9._/-]{1,100}(?<!\.lock)(?<!/)$")
REF_PREFIX_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,40}/$")

LOGICAL_STATES = ("todo", "in_progress", "review", "done", "blocked")


class UnsafeValue(ValueError):
    """A value refused for use in a command. ``str()`` names key, kind and rule."""

    def __init__(self, key, kind, rule, value=None):
        self.key = key
        self.kind = kind
        self.rule = rule
        self.value = value
        super().__init__("%s: unsafe value for kind %s: %s" % (key or "<value>", kind, rule))


def _show(value, limit=40):
    s = repr(value)
    return s if len(s) <= limit else s[:limit - 3] + "..."


def check_common(value, key=None, kind="common", allow=frozenset()):
    """The common refusal. Returns ``value`` or raises :class:`UnsafeValue`."""
    if not isinstance(value, str):
        raise UnsafeValue(key, kind, "not a string (got %s)" % type(value).__name__, value)
    m = _CONTROL.search(value)
    if m:
        raise UnsafeValue(key, kind, "control character %r refused" % m.group(0), value)
    bad = sorted(set(value) & (FORBIDDEN_CHARS - frozenset(allow)))
    if bad:
        raise UnsafeValue(key, kind, "shell metacharacter %s refused" % " ".join(bad), value)
    if value.startswith("-"):
        raise UnsafeValue(key, kind, "leading '-' refused (option injection)", value)
    return value


def _match(pattern, value, key, kind):
    if not pattern.match(value):
        raise UnsafeValue(key, kind, "does not match %s" % pattern.pattern, value)
    return value


def check_target(channel, value, key="notifications.target"):
    """``notifications.target`` for ``channel`` (REQ-W1-093, REQ-W1-097)."""
    ch = CHANNEL_ALIASES.get(channel, channel)
    kind = "target:%s" % ch
    if isinstance(value, str) and "://" in value:
        raise UnsafeValue(key, kind, "a URL ('://') is refused: store the secret's name, not the URL "
                          "(REQ-W1-097)", value)
    if ch in NO_TARGET_CHANNELS:
        if value in ("", None):
            return ""
        raise UnsafeValue(key, kind, "channel 'none' takes no target", value)
    if ch not in TARGET_PATTERNS:
        raise UnsafeValue(key, kind, "unknown channel %s" % _show(channel), value)
    check_common(value, key, kind)
    return _match(TARGET_PATTERNS[ch], value, key, kind)


def check_spreadsheet_path(value, key="management.location", kind="location:spreadsheet"):
    """A relative path, normalised, inside ``docs/spec/``, no ``..``, allowed extension."""
    check_common(value, key, kind)
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise UnsafeValue(key, kind, "absolute path refused; use a path inside docs/spec/", value)
    if ".." in value.replace("\\", "/").split("/"):
        raise UnsafeValue(key, kind, "'..' refused; the path must stay inside docs/spec/", value)
    norm = posixpath.normpath(value)
    if norm != value:
        raise UnsafeValue(key, kind, "path is not normalised (expected %s)" % _show(norm), value)
    if not norm.startswith("docs/spec/"):
        raise UnsafeValue(key, kind, "path outside docs/spec/ refused (REQ-W1-093)", value)
    if not norm.lower().endswith(SPREADSHEET_EXTENSIONS):
        raise UnsafeValue(key, kind, "extension must be one of %s" % "|".join(SPREADSHEET_EXTENSIONS), value)
    if not re.match(r"^[\w ./-]{1,200}$", norm, _A):
        raise UnsafeValue(key, kind, "path characters limited to letters, digits, space, _ . / -", value)
    return value


def check_location(tool, value, key="management.location"):
    """``management.location`` for ``tool`` (legacy ``none`` = ``markdown``)."""
    t = TOOL_ALIASES.get(tool, tool)
    kind = "location:%s" % t
    if t == "spreadsheet":
        return check_spreadsheet_path(value, key, kind)
    if t not in LOCATION_PATTERNS:
        raise UnsafeValue(key, kind, "unknown tool %s" % _show(tool), value)
    check_common(value, key, kind, allow=KIND_EXEMPTIONS.get(kind, frozenset()))
    _match(LOCATION_PATTERNS[t], value, key, kind)
    if t == "markdown" and ".." in value.split("/"):
        raise UnsafeValue(key, kind, "'..' refused; the path must stay inside docs/spec/", value)
    return value


def check_sprints(tool, value, key="management.sprints"):
    t = TOOL_ALIASES.get(tool, tool)
    kind = "sprints:%s" % t
    check_common(value, key, kind, allow=KIND_EXEMPTIONS.get(kind, frozenset()))
    return _match(SPRINT_PATTERNS.get(t, GENERIC_SPRINT), value, key, kind)


def check_status(value, key="status"):
    """A status name of a status map (``null`` is the unsupported state, never a command value)."""
    kind = "status"
    check_common(value, key, kind)
    return _match(STATUS_PATTERN, value, key, kind)


def _git_check_ref_format(value, timeout=5):
    """``True``/``False`` from ``git check-ref-format --branch``; ``None`` when git is absent."""
    try:
        cp = subprocess.run(["git", "check-ref-format", "--branch", value], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    return cp.returncode == 0


def check_branch(value, key="branch_flow", use_git=True):
    """A branch name (``branchName`` §2.6), also checked by git when git is present."""
    kind = "branch"
    check_common(value, key, kind)
    _match(BRANCH_PATTERN, value, key, kind)
    if use_git and "*" not in value and _git_check_ref_format(value) is False:
        raise UnsafeValue(key, kind, "git check-ref-format --branch refuses it", value)
    return value


def check_ref_prefix(value, key="branch_flow.feature_prefix"):
    kind = "ref-prefix"
    check_common(value, key, kind)
    return _match(REF_PREFIX_PATTERN, value, key, kind)


def check_enum(value, allowed, key, kind="enum"):
    if value not in allowed:
        raise UnsafeValue(key, kind, "must be one of %s" % "|".join(str(a) for a in allowed), value)
    check_common(value, key, kind)
    return value
