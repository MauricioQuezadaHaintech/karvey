"""Tolerant hook-payload parser and path normalisation (architecture §3.6, A-1..A-10).

The field names follow the payloads captured from CLI 2.1.281 (E1.F1.T1, fixtures in
``tests/fixtures/payloads/``): every event carries ``session_id``, ``transcript_path``, ``cwd`` and
``hook_event_name``; tool events add ``tool_name``, ``tool_input``, ``tool_use_id``; PostToolUse adds
``tool_response``; SessionStart adds ``source``; UserPromptSubmit carries the text in ``prompt``.

Tolerance, in the order each field is looked up:
- prompt (A-2): ``prompt`` → ``user_prompt`` → ``message.content`` (a string, or a list of
  ``{type: text, text}`` blocks);
- path (A-3): ``tool_input.file_path`` → ``tool_input.notebook_path`` (NotebookEdit) →
  ``tool_input.path``; MultiEdit uses ``file_path``;
- cwd (A-1): ``cwd`` → ``$CLAUDE_PROJECT_DIR`` → ``$PWD`` → the process cwd, always absolute;
- a missing ``session_id`` is empty (a marker still works without it).

Non-JSON (or non-object) stdin gives ``ok = False``; the caller applies each guard's fail mode.
The payload is data: nothing here executes or interprets it.
"""
import json
import os
import posixpath
import re

_DRIVE = re.compile(r"^([A-Za-z]):[\\/]")
_GITBASH = re.compile(r"^/([A-Za-z])(/|$)")
_WSL_UNC = re.compile(r"^(?:\\\\|//)wsl(?:\$|\.localhost)[\\/]+[^\\/]+(.*)$", re.I)


def host_platform():
    return "windows" if os.name == "nt" else "posix"


def norm_path(path, cwd=None, platform=None, home=None):
    """Normalise a path from a payload for the host platform (A-10).

    posix (Linux, WSL): ``C:\\x`` → ``/mnt/c/x``; ``\\\\wsl$\\<distro>\\x`` → ``/x``.
    windows: ``/c/x`` (Git Bash) → ``C:/x``; ``C:\\x`` → ``C:/x``.
    ``~`` is expanded, a relative path is joined to ``cwd``, and the result is normalised.
    Returns None for an empty or non-string input.
    """
    if not isinstance(path, str) or not path.strip():
        return None
    platform = platform or host_platform()
    p = path.strip()
    if home is None:
        home = os.path.expanduser("~")
    if p == "~" or p.startswith("~/") or p.startswith("~\\"):
        p = home + p[1:]
    m = _WSL_UNC.match(p)
    if m:
        rest = m.group(1).replace("\\", "/") or "/"
        return posixpath.normpath("/" + rest.lstrip("/")) if platform == "posix" else p
    m = _DRIVE.match(p)
    if m:
        drive, rest = m.group(1), p[3:].replace("\\", "/")
        if platform == "posix":
            return posixpath.normpath("/mnt/%s/%s" % (drive.lower(), rest)) if rest else "/mnt/%s" % drive.lower()
        return "%s:/%s" % (drive.upper(), posixpath.normpath(rest) if rest else "")
    if platform == "windows":
        m = _GITBASH.match(p.replace("\\", "/"))
        if m:
            rest = p.replace("\\", "/")[3:]
            return "%s:/%s" % (m.group(1).upper(), posixpath.normpath(rest) if rest else "")
        q = p.replace("\\", "/")
        if not q.startswith("/") and cwd:
            base = norm_path(cwd, platform=platform, home=home) or cwd
            q = base.rstrip("/") + "/" + q
        return posixpath.normpath(q)
    if not p.startswith("/"):
        base = norm_path(cwd, platform=platform, home=home) if cwd else _getcwd()
        p = posixpath.join(base or _getcwd(), p)
    return posixpath.normpath(p)


def _text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text") for b in content if isinstance(b, dict) and b.get("type") == "text"
                 and isinstance(b.get("text"), str)]
        return "\n".join(parts) if parts else None
    return None


def prompt_text(raw):
    """The human's prompt text of a UserPromptSubmit payload (A-2), or None."""
    if not isinstance(raw, dict):
        return None
    for key in ("prompt", "user_prompt"):
        if isinstance(raw.get(key), str):
            return raw[key]
    msg = raw.get("message")
    if isinstance(msg, dict):
        return _text_of(msg.get("content"))
    return None


def tool_path(tool_input):
    """The path an Edit/Write/MultiEdit/NotebookEdit call acts on (A-3), or None."""
    if not isinstance(tool_input, dict):
        return None
    for key in ("file_path", "notebook_path", "path"):
        v = tool_input.get(key)
        if isinstance(v, str) and v.strip():
            return v
    return None


class Payload:
    """One parsed hook payload. ``ok`` is False when stdin was not a JSON object."""

    __slots__ = ("ok", "error", "raw", "event", "session_id", "transcript_path", "cwd", "tool_name",
                 "tool_input", "command", "file_path", "file_path_raw", "prompt", "source", "permission_mode")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def as_dict(self):
        return {k: getattr(self, k) for k in self.__slots__ if k != "raw"}


def _getcwd():
    """``os.getcwd()``, or ``/`` when the directory was deleted (BUG-34: never raise before a guard runs)."""
    try:
        return os.getcwd()
    except OSError:
        return "/"


def _fallback_cwd(env):
    for key in ("CLAUDE_PROJECT_DIR", "PWD"):
        v = env.get(key)
        if v:
            return v
    return _getcwd()


def parse(text, env=None, platform=None):
    """Parse stdin ``text`` into a :class:`Payload` (never raises)."""
    env = os.environ if env is None else env
    base = {"ok": False, "raw": None, "session_id": "", "cwd": None}
    if isinstance(text, bytes):
        text = text.decode("utf-8", "replace")
    if not isinstance(text, str) or not text.strip():
        base["error"] = "empty stdin"
    else:
        try:
            raw = json.loads(text.lstrip("﻿"))
        except ValueError as exc:
            raw = None
            base["error"] = "stdin is not JSON (%s)" % exc
        if raw is not None and not isinstance(raw, dict):
            base["error"] = "stdin is not a JSON object"
            raw = None
        if raw is not None:
            base.update(ok=True, raw=raw)
    raw = base["raw"] or {}
    cwd_raw = raw.get("cwd") if isinstance(raw.get("cwd"), str) and raw.get("cwd").strip() else _fallback_cwd(env)
    cwd = norm_path(cwd_raw, cwd=_getcwd(), platform=platform)
    tool_input = raw.get("tool_input") if isinstance(raw.get("tool_input"), dict) else {}
    fp_raw = tool_path(tool_input)
    cmd = tool_input.get("command")
    return Payload(
        ok=base["ok"], error=base.get("error"), raw=base["raw"],
        event=raw.get("hook_event_name") if isinstance(raw.get("hook_event_name"), str) else None,
        session_id=raw.get("session_id") if isinstance(raw.get("session_id"), str) else "",
        transcript_path=raw.get("transcript_path") if isinstance(raw.get("transcript_path"), str) else "",
        cwd=cwd,
        tool_name=raw.get("tool_name") if isinstance(raw.get("tool_name"), str) else None,
        tool_input=tool_input,
        command=cmd if isinstance(cmd, str) else None,
        file_path=norm_path(fp_raw, cwd=cwd, platform=platform) if fp_raw else None,
        file_path_raw=fp_raw,
        prompt=prompt_text(raw),
        source=raw.get("source") if isinstance(raw.get("source"), str) else None,
        permission_mode=raw.get("permission_mode") if isinstance(raw.get("permission_mode"), str) else None,
    )
