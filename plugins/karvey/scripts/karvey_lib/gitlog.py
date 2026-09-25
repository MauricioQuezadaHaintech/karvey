"""Read-only git queries (architecture §1.3, §1.9 of wave2-structural).

Every call goes through :func:`run`, which accepts only the read-only sub-commands of ``ALLOWED`` and passes an
argv list (never a shell). Refs and paths from files are checked before they reach git.
Standard library only.
"""
import re
import subprocess

ALLOWED = frozenset({"diff", "log", "rev-parse", "grep", "show", "for-each-ref", "merge-base", "rev-list",
                     "ls-files", "cat-file"})
TIMEOUT_S = 10
_REF = re.compile(r"^(?!-)[A-Za-z0-9._/@^~{}*-]{1,200}$")
# Karvey-Change: <change-id> (one trailer per line, the strict pattern of §1.9)
TRAILER_KEY = "Karvey-Change"


class GitLogError(Exception):
    """A refused sub-command or argument, or git failed."""


def check_ref(ref):
    if not isinstance(ref, str) or not _REF.match(ref.replace("...", "", 1).replace("..", "", 1)):
        raise GitLogError("unsafe git ref %r" % (ref,))
    return ref


def run(args, cwd, timeout=TIMEOUT_S):
    """``stdout`` of ``git <args>`` for an allowed sub-command; raises :class:`GitLogError`."""
    args = list(args)
    if not args or args[0] not in ALLOWED:
        raise GitLogError("git sub-command %r is not in the read-only allow-list (%s)"
                          % (args[0] if args else None, ", ".join(sorted(ALLOWED))))
    try:
        cp = subprocess.run(["git", "--no-pager"] + args, cwd=str(cwd), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout, check=False)
    except FileNotFoundError:
        raise GitLogError("git is not installed")
    except subprocess.TimeoutExpired:
        raise GitLogError("git %s timed out after %ds" % (args[0], timeout))
    if cp.returncode != 0:
        raise GitLogError("git %s failed: %s" % (args[0], cp.stderr.decode("utf-8", "replace").strip()[:200]))
    return cp.stdout.decode("utf-8", "replace")


def diff_names(cwd, base, head="HEAD"):
    """Paths changed between ``base`` and ``head`` (three-dot: since the merge base)."""
    out = run(["diff", "--name-only", "--no-renames", "%s...%s" % (check_ref(base), check_ref(head))], cwd)
    return sorted({ln.strip() for ln in out.splitlines() if ln.strip()})


def log_trailers(cwd, rev_range, key=TRAILER_KEY):
    """``[{sha, parents, subject, trailers: [values]}]`` for every commit in ``rev_range`` (oldest first)."""
    fmt = "%H%x1f%P%x1f%s%x1f%(trailers:key=" + key + ",valueonly,separator=%x1e)%x1d"
    out = run(["log", "--reverse", "--format=" + fmt, check_ref(rev_range)], cwd)
    commits = []
    for rec in out.split("\x1d"):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        parts = rec.split("\x1f")
        while len(parts) < 4:
            parts.append("")
        sha, parents, subject, trl = parts[:4]
        values = [v.strip() for v in trl.replace("\n", "\x1e").split("\x1e") if v.strip()]
        commits.append({"sha": sha.strip(), "parents": parents.split(), "subject": subject, "trailers": values})
    return commits


def changed_paths(cwd, sha):
    """Paths a single commit touched (first parent for a merge)."""
    out = run(["show", "--name-only", "--no-renames", "--format=", "--first-parent", "-m", check_ref(sha)], cwd)
    return sorted({ln.strip() for ln in out.splitlines() if ln.strip()})


def grep_refs(cwd, pattern, refs_glob="refs/remotes/"):
    """Refs whose name matches ``refs_glob`` (for-each-ref) — used to scan other clones' branches."""
    out = run(["for-each-ref", "--format=%(refname)", check_ref(refs_glob)], cwd)
    rx = re.compile(pattern)
    return [r for r in out.splitlines() if r and rx.search(r)]
