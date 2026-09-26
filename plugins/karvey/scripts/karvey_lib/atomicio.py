"""Atomic, format-preserving JSON I/O (architecture §1.1 "Writes").

- Reads with ``utf-8-sig`` (a BOM written by a Windows editor is tolerated).
- Writes keep the key order, the indent (2 spaces unless the file used another), the
  newline style, the trailing newline and a leading BOM when the original had one.
- A write goes to a temporary file in the same directory and replaces the target with
  ``os.replace`` under an ``O_EXCL`` lock file ``<file>.lock`` (stale after 30 s).
- Compare-and-swap: the caller passes the content hash it read; if another writer changed
  the file in between, the write is refused (exit 3) and nothing is written.
"""
import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from . import EXIT_NOT_FOUND, EXIT_REFUSED, defaults

BOM = "﻿"


class AtomicIOError(Exception):
    exit_code = EXIT_REFUSED


class ReadError(AtomicIOError):
    """Input not found, unreadable or not JSON (exit 4)."""
    exit_code = EXIT_NOT_FOUND


class LockBusy(AtomicIOError):
    """Another writer holds a fresh lock (exit 3)."""


class CASConflict(AtomicIOError):
    """The file changed since it was read (exit 3)."""


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    """Hash of the file's bytes, or None if it does not exist."""
    try:
        with open(path, "rb") as fh:
            return sha256_bytes(fh.read())
    except FileNotFoundError:
        return None


class Loaded:
    """Result of :func:`read_json`: data plus what is needed to write it back unchanged."""

    __slots__ = ("path", "data", "sha256", "indent", "newline", "bom", "trailing_newline")

    def __init__(self, path, data, sha256, indent, newline, bom, trailing_newline):
        self.path = path
        self.data = data
        self.sha256 = sha256
        self.indent = indent
        self.newline = newline
        self.bom = bom
        self.trailing_newline = trailing_newline

    @property
    def fmt(self):
        return {"indent": self.indent, "newline": self.newline, "bom": self.bom,
                "trailing_newline": self.trailing_newline}


def detect_format(text):
    """Indent, newline style, BOM and trailing newline of a JSON text."""
    bom = text.startswith(BOM)
    body = text[1:] if bom else text
    newline = "\r\n" if "\r\n" in body else "\n"
    indent = 2
    m = re.search(r"\n([ \t]+)\S", body)
    if m:
        ws = m.group(1)
        indent = "\t" if ws.startswith("\t") else len(ws)
    elif body.strip() and "\n" not in body.strip():
        indent = None  # a one-line JSON stays one line
    trailing = body.endswith("\n")
    return {"indent": indent, "newline": newline, "bom": bom, "trailing_newline": trailing}


def read_json(path):
    """Read a JSON file BOM-tolerantly. Raises :class:`ReadError` (exit 4)."""
    p = Path(path)
    try:
        raw = p.read_bytes()
    except FileNotFoundError:
        raise ReadError("not found: %s" % p)
    except OSError as exc:
        raise ReadError("unreadable: %s (%s)" % (p, exc))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReadError("not UTF-8: %s (%s)" % (p, exc))
    fmt = detect_format(text)
    try:
        data = json.loads(text[1:] if fmt["bom"] else text)
    except ValueError as exc:
        raise ReadError("invalid JSON: %s (%s)" % (p, exc))
    return Loaded(p, data, sha256_bytes(raw), fmt["indent"], fmt["newline"], fmt["bom"],
                  fmt["trailing_newline"])


def dumps(data, indent=2, newline="\n", bom=False, trailing_newline=True):
    """Serialise keeping key order; non-ASCII is kept as is."""
    text = json.dumps(data, indent=indent, ensure_ascii=False)
    if newline != "\n":
        text = text.replace("\n", newline)
    if trailing_newline:
        text += newline
    if bom:
        text = BOM + text
    return text


def _lock_path(path):
    return Path(str(path) + ".lock")


def _break_stale(lp, seen_ino, stale_s):
    """Break the stale lock ``lp`` whose inode was ``seen_ino`` (BUG-37). The file is first renamed aside,
    which only one waiter can do; if the renamed file is not the stale one seen (another waiter broke it and
    took a fresh lock in between), it is put back and the lock is left to its owner. True when broken."""
    aside = lp.with_name("%s.%s.stale" % (lp.name, uuid.uuid4().hex[:12]))
    try:
        os.rename(str(lp), str(aside))
    except FileNotFoundError:
        return False
    try:
        st = aside.stat()
        if st.st_ino == seen_ino and time.time() - st.st_mtime > stale_s:
            return True
        try:
            os.link(str(aside), str(lp))  # put the fresh lock back (fails if a newer one exists)
        except (FileExistsError, OSError):
            pass
        return False
    finally:
        try:
            aside.unlink()
        except FileNotFoundError:
            pass


@contextmanager
def lock(path, wait_s=5.0, stale_s=None):
    """Exclusive ``<file>.lock`` via ``O_EXCL``. A lock older than ``stale_s`` is broken. The lock holds a
    token, and only its owner removes it (BUG-37)."""
    if stale_s is None:
        stale_s = defaults().get("lock_stale_seconds", 30)
    lp = _lock_path(path)
    deadline = time.monotonic() + wait_s
    token = ("%d %f %s\n" % (os.getpid(), time.time(), uuid.uuid4().hex)).encode()
    while True:
        try:
            # O_BINARY: on Windows a text-mode fd turns the token's "\n" into "\r\n", and the owner check at
            # release would never match (the lock would stay behind)
            fd = os.open(str(lp), os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o600)
            break
        except FileExistsError:
            try:
                st = lp.stat()
            except FileNotFoundError:
                continue
            if time.time() - st.st_mtime > stale_s:
                _break_stale(lp, st.st_ino, stale_s)
                continue
            if time.monotonic() >= deadline:
                raise LockBusy("locked by another writer: %s (re-run)" % lp)
            time.sleep(0.05)
    try:
        os.write(fd, token)
        os.close(fd)
        yield lp
    finally:
        try:
            with open(str(lp), "rb") as fh:
                mine = fh.read() == token
        except OSError:
            mine = False
        if mine:
            try:
                lp.unlink()
            except FileNotFoundError:
                pass


def write_text_atomic(path, text, expected_sha256=None, mode=None):
    """Replace ``path`` with ``text`` atomically, under the lock, with compare-and-swap.

    ``expected_sha256``: the content hash the caller read; ``None`` means the file must not
    exist yet; ``"*"`` skips the check (only for files no other writer owns).
    """
    p = Path(path)
    data = text.encode("utf-8")
    with lock(p):
        current = file_sha256(p)
        if expected_sha256 != "*" and current != expected_sha256:
            raise CASConflict("changed by another writer, re-run: %s" % p)
        if mode is None:
            try:
                mode = p.stat().st_mode & 0o7777
            except FileNotFoundError:
                mode = None
        fd, tmp = tempfile.mkstemp(prefix="." + p.name + ".", suffix=".tmp", dir=str(p.parent))
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            if mode is not None:
                os.chmod(tmp, mode)
            os.replace(tmp, str(p))
        except BaseException:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise
    return sha256_bytes(data)


def write_json(path, data, loaded=None, expected_sha256=None, fmt=None, mode=None):
    """Write JSON atomically, keeping the original format.

    Pass the :class:`Loaded` returned by :func:`read_json` (its hash is the CAS token and
    its format is kept), or an explicit ``expected_sha256`` (None = the file must not exist).
    Returns the new content hash.
    """
    if loaded is not None:
        fmt = fmt or loaded.fmt
        expected_sha256 = loaded.sha256
    fmt = fmt or {"indent": 2, "newline": "\n", "bom": False, "trailing_newline": True}
    return write_text_atomic(path, dumps(data, **fmt), expected_sha256=expected_sha256, mode=mode)
