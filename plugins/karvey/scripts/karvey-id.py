#!/usr/bin/env python3
"""karvey-id.py — the next free ID of a kind, reserved under a lock (architecture §1.14 C-16).

    karvey-id.py next BUG|D|BL|F|Q [--change ID] [--qualified] [--root DIR] [--json]

It takes ``<git-common-dir>/karvey/ids.lock`` (O_EXCL, holding ``pid token``; stale after ``lock_stale_seconds``:
the stale file is renamed aside atomically before a new lock is created, and a release deletes the lock only while
it still holds this process's token), scans the working
tree and every local and ``refs/remotes/*`` branch (``git grep``, read-only, no fetch) for the kind's IDs, takes
``max + 1`` above the clone-local reservations in ``<git-common-dir>/karvey/ids.json``, records it and prints it.
``ids.json`` is a cache of this clone's reservations: when it is not ``{kind: [{"n": int, ...}]}`` it is kept aside
as ``ids.json.corrupt-{time}`` and rebuilt from the scan, with a note in the result.

Sources: BUG ``docs/bugs_dev_testing.md`` · D ``docs/spec/decisions.md`` and ``docs/spec/decisions/*.md`` ·
BL ``docs/spec/backlog.md`` · F ``docs/spec/changes/{change}/findings.md`` (per change: ``--change`` required) ·
Q ``docs/spec/questions.md`` and the change folders. ``--qualified`` prints ``KIND-NN@{repo}``
(``project.json:repos[0]``), validated before any number is reserved.

Residual risk: two clones that have not pushed can still pick the same number; the remote scan narrows it.

Exit: 0 · 2 usage · 3 refused (lock held, unsafe repo slug) · 4 not found · 5 internal. Stdlib only.
"""
import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import karvey_lib as kl  # noqa: E402
from karvey_lib import gitlog, project as pj  # noqa: E402

TOOL = "karvey-id"
KINDS = ("BUG", "D", "BL", "F", "Q")
LOCK_WAIT_S = 3.0
_SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


class Refused(Exception):
    pass


class NotFound(Exception):
    pass


def sources(kind, change=None):
    """Repo-relative paths (globs allowed) that hold IDs of ``kind``."""
    if kind == "BUG":
        return ["docs/bugs_dev_testing.md"]
    if kind == "D":
        return ["docs/spec/decisions.md", "docs/spec/decisions/*.md"]
    if kind == "BL":
        return ["docs/spec/backlog.md"]
    if kind == "F":
        return ["docs/spec/changes/%s/findings.md" % change]
    return ["docs/spec/questions.md", "docs/spec/changes/*/*.md"]


def id_re(kind):
    return re.compile(r"(?<![A-Za-z0-9-])%s-(\d+)(?!\d)" % re.escape(kind))


def scan_tree(root, kind, change):
    rx, top = id_re(kind), 0
    for pat in sources(kind, change):
        for p in sorted(Path(root).glob(pat)):
            try:
                text = p.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            for m in rx.finditer(text):
                top = max(top, int(m.group(1)))
    return top


def scan_refs(root, kind, change):
    """Max ID on every local and remote-tracking branch (read-only ``git grep`` per ref)."""
    try:
        refs = gitlog.run(["for-each-ref", "--format=%(refname)", "refs/heads/", "refs/remotes/"], root).split()
    except gitlog.GitLogError:
        return 0, []
    rx, top, seen = id_re(kind), 0, []
    pats = sources(kind, change)
    for ref in refs:
        if ref.endswith("/HEAD"):
            continue
        try:
            # the boundary of id_re (not preceded by a letter, digit or hyphen): ``HEAD-977`` is not ``D-977``
            out = gitlog.run(["grep", "-h", "-o", "-E", "(^|[^A-Za-z0-9-])%s-[0-9]+" % kind, gitlog.check_ref(ref),
                              "--"] + pats, root)
        except gitlog.GitLogError:
            continue  # no match (exit 1) or an unreadable ref
        seen.append(ref)
        for m in rx.finditer(out):
            top = max(top, int(m.group(1)))
    return top, seen


def state_dir(root):
    d = pj.git_common_dir(root)
    if d is None:
        raise NotFound("not a git repository: %s" % root)
    p = Path(d) / "karvey"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


class Lock:
    """``O_EXCL`` lock file holding ``pid token``. Release deletes it only while it still holds our token; a stale
    lock is renamed aside (atomic) and checked to be the one judged stale before a new lock is created (BUG-60)."""

    def __init__(self, path, stale_s):
        self.path, self.stale_s, self.fd = Path(path), stale_s, None
        self.token = uuid.uuid4().hex

    def _take_over_stale(self, seen):
        """Move the stale lock whose content was ``seen`` out of the way; False when it was not that file."""
        aside = self.path.with_name("%s.stale-%s" % (self.path.name, self.token))
        try:
            os.rename(str(self.path), str(aside))
        except FileNotFoundError:
            return False  # another waiter took it over first
        if _read(aside) == seen:
            os.unlink(str(aside))
            return True
        try:  # not the stale file we judged: a fresh lock of another process; put it back, never overwrite
            os.link(str(aside), str(self.path))
        except OSError:
            pass
        os.unlink(str(aside))
        return False

    def __enter__(self):
        deadline = time.monotonic() + float(os.environ.get("KARVEY_ID_LOCK_WAIT_S", LOCK_WAIT_S))
        while True:
            try:
                self.fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                os.write(self.fd, ("%d %s\n" % (os.getpid(), self.token)).encode())
                return self
            except FileExistsError:
                try:
                    seen = _read(self.path)
                    if seen is not None and time.time() - self.path.stat().st_mtime > self.stale_s:
                        self._take_over_stale(seen)
                        continue
                except FileNotFoundError:
                    continue
                if time.monotonic() > deadline:
                    raise Refused("the ID lock %s is held by another process; no number was taken (retry, or remove "
                                  "it if no karvey-id is running)" % self.path.name)
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            os.close(self.fd)
        finally:
            got = (_read(self.path) or "").split()
            if len(got) == 2 and got[1] == self.token:
                try:
                    self.path.unlink()
                except FileNotFoundError:
                    pass


def repo_slug(root):
    project, _ = pj.load_project_json(root)
    repos = (project or {}).get("repos") if isinstance(project, dict) else None
    slug = repos[0] if isinstance(repos, list) and repos and isinstance(repos[0], str) else None
    if slug is None:
        slug = Path(root).name
    slug = slug.rstrip("/").split("/")[-1]
    if slug.endswith(".git"):
        slug = slug[:-4]
    if not _SLUG.match(slug):
        raise Refused("repos[0] %r is not a safe repo slug for --qualified" % slug[:60])
    return slug


def load_reservations(rpath):
    """``(data, note)``: ``ids.json`` as ``{key: [{"n": int, ...}]}``; a corrupt file is kept aside and rebuilt."""
    try:
        text = rpath.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}, None
    except OSError as exc:
        return {}, "ids.json unreadable (%s): rebuilt from the scan" % exc
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    ok = isinstance(data, dict) and all(
        isinstance(v, list) and all(isinstance(r, dict) and isinstance(r.get("n"), int)
                                    and not isinstance(r.get("n"), bool) for r in v) for v in data.values())
    if ok:
        return data, None
    aside = rpath.with_name("ids.json.corrupt-%s" % datetime.now().strftime("%Y%m%dT%H%M%S%f"))
    try:
        os.replace(str(rpath), str(aside))
    except OSError:
        aside = None
    return {}, "ids.json is not {kind: [{\"n\": int}]}: rebuilt from the scan%s" % (
        " (the old file is %s)" % aside.name if aside else "")


def cmd_next(args):
    root = pj.find_root(start=os.getcwd(), root=args.root)
    if root is None:
        raise NotFound("not a Karvey project (no docs/spec): %s" % (args.root or os.getcwd()))
    kind = args.kind
    if kind == "F" and not args.change:
        raise Refused("F-NN is per change: pass --change")
    if args.change and not re.match(r"^[a-z0-9][a-z0-9-]{1,62}$", args.change):
        raise Refused("invalid change id %r" % args.change)
    slug = repo_slug(root) if args.qualified else None  # refuse before a number is reserved (BUG-60)
    sd = state_dir(root)
    stale = (kl.defaults() or {}).get("lock_stale_seconds", 30)
    with Lock(sd / "ids.lock", stale):
        tree = scan_tree(root, kind, args.change)
        refs, seen = scan_refs(root, kind, args.change)
        rpath = sd / "ids.json"
        res, note = load_reservations(rpath)
        key = kind if kind != "F" else "F:%s" % args.change
        held = [r for r in res.get(key, []) if isinstance(r, dict) and isinstance(r.get("n"), int)]
        reserved = max([r["n"] for r in held] or [0])
        n = max(tree, refs, reserved) + 1
        held.append({"n": n, "at": datetime.now().astimezone().isoformat(timespec="seconds"), "change": args.change})
        res[key] = held
        tmp = rpath.with_suffix(".tmp")
        tmp.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(str(tmp), str(rpath))
    width = 2
    ident = "%s-%0*d" % (kind, width, n)
    if args.qualified:
        ident += "@%s" % slug
    result = {"kind": kind, "id": ident, "n": n, "max_tree": tree, "max_refs": refs, "max_reserved": reserved,
              "refs_scanned": len(seen), "change": args.change, "notes": [note] if note else []}
    return kl.EXIT_OK, result, ident


def build_parser():
    p = argparse.ArgumentParser(prog="karvey-id.py", description="next free ID of a kind, reserved under a lock")
    sub = p.add_subparsers(dest="command")
    n = sub.add_parser("next")
    n.add_argument("kind", choices=KINDS)
    n.add_argument("--change")
    n.add_argument("--qualified", action="store_true", help="KIND-NN@{repo}")
    n.add_argument("--root")
    n.add_argument("--json", action="store_true")
    return p


def main(argv=None):
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else kl.EXIT_USAGE
        if code != 0 and as_json:
            kl.emit(kl.envelope(TOOL, kl.EXIT_USAGE, errors=[kl.issue("usage", "invalid arguments")]), True)
        return kl.EXIT_USAGE if code != 0 else 0
    if not args.command:
        parser.print_help(sys.stderr)
        return kl.EXIT_USAGE
    try:
        code, result, human = cmd_next(args)
    except Refused as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_REFUSED, errors=[kl.issue("id.refused", str(exc))]), args.json)
    except NotFound as exc:
        return kl.emit(kl.envelope(TOOL, kl.EXIT_NOT_FOUND, errors=[kl.issue("id.not_found", str(exc))]), args.json)
    except Exception as exc:  # pragma: no cover
        return kl.emit(kl.envelope(TOOL, kl.EXIT_INTERNAL,
                                   errors=[kl.issue("internal", "%s: %s" % (type(exc).__name__, exc))]), args.json)
    return kl.emit(kl.envelope(TOOL, code, result=result), args.json, human=human)


if __name__ == "__main__":
    sys.exit(main())
