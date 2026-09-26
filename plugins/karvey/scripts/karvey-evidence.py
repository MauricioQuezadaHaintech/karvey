#!/usr/bin/env python3
"""karvey-evidence.py — run a command and record verifiable evidence of it (architecture §1.14 C-18).

    karvey-evidence.py [--change ID] [--label TEXT] [--junit PATH] [--root DIR] -- <cmd> [args…]

Runs the argv as given (no shell), streaming stdout and stderr through unchanged, and appends one JSON line to
``docs/spec/changes/{id}/evidence.jsonl``: ``{at, change, label, argv, cwd_rel, exit, duration_ms,
stdout_sha256, stderr_sha256, bytes, junit}``. **No output text is stored** — only hashes and sizes — so the
file cannot leak a secret. A phase-close claim cites ``evidence.jsonl:{line}``.

The change is ``--change``, else the active change (branch, or the only open change). With none, the command
still runs and ``[karvey] evidence not recorded: no active change`` goes to stderr.

Exit: the command's own exit code (127 when it cannot be started) · 2 usage. Python >= 3.9, stdlib only.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from karvey_lib import project as pj  # noqa: E402

EVIDENCE_FILE = "evidence.jsonl"


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
    except (FileNotFoundError, PermissionError) as exc:
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
    cwd = os.getcwd()
    root = pj.find_root(start=cwd, root=args.root)
    code, ms, so, se, nbytes = run_streamed(cmd)
    change = resolve_change(root, args.change) if root else None
    if change is None:
        sys.stderr.write("[karvey] evidence not recorded: no active change\n")
        return code
    rec = {"at": datetime.now().astimezone().isoformat(timespec="seconds"), "change": change,
           "label": args.label[:120], "argv": cmd, "cwd_rel": os.path.relpath(cwd, str(root)).replace(os.sep, "/"),
           "exit": code, "duration_ms": ms, "stdout_sha256": so, "stderr_sha256": se, "bytes": nbytes,
           "junit": args.junit}
    path = Path(root) / pj.CHANGES_DIR / change / EVIDENCE_FILE
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, (json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        finally:
            os.close(fd)
        with open(path, "rb") as fh:
            line = sum(1 for _ in fh)
        sys.stderr.write("[karvey] evidence recorded: %s:%d (exit %d)\n"
                         % (os.path.relpath(str(path), str(root)).replace(os.sep, "/"), line, code))
    except OSError as exc:
        sys.stderr.write("[karvey] evidence not recorded: %s\n" % exc)
    return code


if __name__ == "__main__":
    sys.exit(main())
