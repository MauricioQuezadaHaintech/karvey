#!/usr/bin/env python3
"""karvey-evidence.py — run a command and record verifiable evidence of it (architecture §1.14 C-18).

    karvey-evidence.py [--change ID] [--label TEXT] [--junit PATH] [--root DIR] -- <cmd> [args…]

Runs the argv as given (no shell), streaming stdout and stderr through unchanged, and appends one JSON line to
``docs/spec/changes/{id}/evidence.jsonl``: ``{at, change, label, argv, cwd_rel, exit, duration_ms,
stdout_sha256, stderr_sha256, bytes, junit}``. **No output text is stored** — only hashes and sizes — and the
argv is redacted before it is written (``--password=…``, the value after ``--api-key``, ``DB_SECRET=…``,
``scheme://user:pass@host`` become ``***``), so the file does not leak a secret. A phase-close claim cites ``evidence.jsonl:{line}``.

The change is ``--change`` (a plain change id, never a path), else the active change (branch, or the only open change). With none, the command
still runs and ``[karvey] evidence not recorded: no active change`` goes to stderr.

Exit: the command's own exit code (127 when it cannot be started) · 2 usage. Python >= 3.9, stdlib only.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from karvey_lib import atomicio, project as pj  # noqa: E402
from karvey_lib.manifest import CHANGE_ID, NOT_A_CHANGE  # noqa: E402

EVIDENCE_FILE = "evidence.jsonl"
REDACTED = "***"
_SECRET_TOKENS = {"pass", "password", "passwd", "pwd", "passphrase", "secret", "secrets", "token", "apikey", "auth",
                  "credential", "credentials", "key"}
_SECRET_ENDINGS = ("password", "passwd", "passphrase", "secret", "token", "apikey", "credential", "credentials")


class _SecretName:
    """BUG-55 / BUG-71 (F-42): a flag or variable name is secret when one of its ``-``/``_``/``.`` words is a secret
    word (or ends with one: ``authToken``); ``--passWithNoTests`` or ``--author`` are not."""

    @staticmethod
    def search(name):
        words = [w for w in re.split(r"[-_.]+", (name or "").lower()) if w]
        return any(w in _SECRET_TOKENS or w.endswith(_SECRET_ENDINGS) for w in words)


_SECRET_WORD = _SecretName()
_LONG_FLAG = re.compile(r"^--([A-Za-z0-9][A-Za-z0-9_.-]*)$")
_LONG_FLAG_EQ = re.compile(r"^(--[A-Za-z0-9][A-Za-z0-9_.-]*)=(.*)$", re.S)
_ENV_ARG = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*)=(.*)$", re.S)
_USERINFO = re.compile(r"(\b[A-Za-z][A-Za-z0-9+.-]*://)[^/@\s]+@")


def _collapse_home(a):
    """BUG-69 (F-40): the user's home directory is written as ``~`` (a path under it names the user)."""
    home = os.path.expanduser("~").rstrip("/\\")
    if not isinstance(a, str) or len(home) < 2:
        return a
    return re.sub(r"(?<![\w.-])" + re.escape(home) + r"(?=[/\\]|$)", "~", a)


def redact_argv(argv):
    """BUG-55 (F-16): argv without secret values; BUG-69: the home directory collapsed to ``~``. ``argv[0]`` and
    ordinary arguments otherwise stay as given."""
    argv = [_collapse_home(a) for a in argv]
    out, hide_next = [], False
    for i, a in enumerate(argv):
        if not isinstance(a, str) or i == 0:
            out.append(a)
            continue
        if hide_next and not a.startswith("-"):
            out.append(REDACTED)
            hide_next = False
            continue
        hide_next = False
        m = _LONG_FLAG_EQ.match(a) or _ENV_ARG.match(a)
        if m and _SECRET_WORD.search(m.group(1).lstrip("-")):
            out.append("%s=%s" % (m.group(1), REDACTED))
            continue
        m = _LONG_FLAG.match(a)
        if m and _SECRET_WORD.search(m.group(1)):
            hide_next = True
        out.append(_USERINFO.sub(r"\1%s@" % REDACTED, a))
    return out


def valid_change_id(change):
    """A plain change id (same rule as the ``Karvey-Change`` trailer), never a path."""
    return isinstance(change, str) and bool(CHANGE_ID.match(change)) and change not in NOT_A_CHANGE


def _pump(src, dst, h, counter):
    while True:
        chunk = src.read1(65536) if hasattr(src, "read1") else src.read(65536)
        if not chunk:
            break
        h.update(chunk)
        counter[0] += len(chunk)
        try:
            dst.write(chunk)
            dst.flush()
        except (OSError, ValueError):
            pass


def run_streamed(argv, cwd=None):
    """``(exit, duration_ms, stdout_sha256, stderr_sha256, bytes)``; output passes through unchanged."""
    t0 = time.monotonic()
    try:
        p = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:  # not found, permission, exec format error… (BUG-55)
        sys.stderr.write("[karvey] evidence: cannot start %s: %s\n" % (argv[0], exc))
        return 127, 0, hashlib.sha256().hexdigest(), hashlib.sha256().hexdigest(), 0
    ho, he, n = hashlib.sha256(), hashlib.sha256(), [0]
    out = getattr(sys.stdout, "buffer", sys.stdout)
    err = getattr(sys.stderr, "buffer", sys.stderr)
    th = [threading.Thread(target=_pump, args=(p.stdout, out, ho, n)),
          threading.Thread(target=_pump, args=(p.stderr, err, he, n))]
    for t in th:
        t.start()
    for t in th:
        t.join()
    code = p.wait()
    return code, int((time.monotonic() - t0) * 1000), ho.hexdigest(), he.hexdigest(), n[0]


def resolve_change(root, change):
    if change:
        return change if (Path(root) / pj.CHANGES_DIR / change).is_dir() else None
    return pj.active_change(root).get("change")


def append_record(path, rec):
    """Append one JSON line under the file lock; returns its 1-based line number (BUG-55: counted from the
    pre-append content, with a newline separator when the file does not end in one)."""
    data = (json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    with atomicio.lock(path):
        try:
            with open(path, "rb") as fh:
                before = fh.read()
        except FileNotFoundError:
            before = b""
        if before and not before.endswith(b"\n"):
            data = b"\n" + data
            before += b"\n"
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
    return before.count(b"\n") + 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" not in argv:
        sys.stderr.write("usage: karvey-evidence.py [--change ID] [--label TEXT] [--junit PATH] -- <cmd> [args…]\n")
        return 2
    i = argv.index("--")
    opts, cmd = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(prog="karvey-evidence.py", description="run a command, record hashed evidence")
    ap.add_argument("--change")
    ap.add_argument("--label", default="")
    ap.add_argument("--junit", help="a JUnit XML the command writes (its path is recorded for karvey-trace)")
    ap.add_argument("--root")
    try:
        args = ap.parse_args(opts)
    except SystemExit:
        return 2
    if not cmd:
        sys.stderr.write("karvey-evidence.py: no command after --\n")
        return 2
    if args.change is not None and not valid_change_id(args.change):
        sys.stderr.write("karvey-evidence.py: invalid change id %r (a plain id: ^[a-z0-9][a-z0-9-]{1,62}$)\n"
                         % args.change[:80])
        return 2
    cwd = os.getcwd()
    root = pj.find_root(start=cwd, root=args.root)
    code, ms, so, se, nbytes = run_streamed(cmd)
    change = resolve_change(root, args.change) if root else None
    if change is None:
        sys.stderr.write("[karvey] evidence not recorded: no active change\n")
        return code
    rec = {"at": datetime.now().astimezone().isoformat(timespec="seconds"), "change": change,
           "label": args.label[:120], "argv": redact_argv(cmd), "cwd_rel": os.path.relpath(cwd, str(root)).replace(os.sep, "/"),
           "exit": code, "duration_ms": ms, "stdout_sha256": so, "stderr_sha256": se, "bytes": nbytes,
           "junit": args.junit}
    path = Path(root) / pj.CHANGES_DIR / change / EVIDENCE_FILE
    try:
        line = append_record(path, rec)
        sys.stderr.write("[karvey] evidence recorded: %s:%d (exit %d)\n"
                         % (os.path.relpath(str(path), str(root)).replace(os.sep, "/"), line, code))
    except (OSError, atomicio.LockBusy) as exc:
        sys.stderr.write("[karvey] evidence not recorded: %s\n" % exc)
    return code


if __name__ == "__main__":
    sys.exit(main())
