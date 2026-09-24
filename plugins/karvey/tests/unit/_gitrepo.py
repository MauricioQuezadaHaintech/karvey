"""Throw-away git repositories for unit tests, isolated from the user's git config and hooks."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

ISOLATED_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Karvey Test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "Karvey Test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
    "GIT_TERMINAL_PROMPT": "0",
}


def isolate_git():
    """Apply the isolated git environment to this process (inherited by karvey_lib calls)."""
    os.environ.update(ISOLATED_ENV)


def run(args, cwd):
    subprocess.run(["git"] + args, cwd=str(cwd), check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def init(path, branch="main"):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    run(["init", "-q", "-b", branch], path)
    run(["config", "commit.gpgsign", "false"], path)
    return path


def write(path, rel, content):
    p = Path(path) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(content, str):
        content = json.dumps(content, indent=2) + "\n"
    p.write_text(content, encoding="utf-8")
    return p


def commit_all(path, msg="c"):
    run(["add", "-A"], path)
    run(["commit", "-q", "--allow-empty", "-m", msg], path)


def with_origin(path, branch="main"):
    """Create a bare origin next to ``path`` and push ``branch`` so ``origin/<branch>`` is real."""
    path = Path(path)
    bare = path.parent / (path.name + "-origin.git")
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, stdout=subprocess.DEVNULL)
    run(["remote", "add", "origin", str(bare)], path)
    run(["push", "-q", "origin", branch], path)
    return bare


class TempDir:
    def __init__(self):
        self._t = tempfile.TemporaryDirectory()
        self.path = Path(os.path.realpath(self._t.name))

    def cleanup(self):
        self._t.cleanup()
