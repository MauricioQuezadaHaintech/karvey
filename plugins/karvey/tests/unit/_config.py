"""Load karvey-config.py (hyphenated, so not importable by name) and run it in-process."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path

import _path

_SPEC = importlib.util.spec_from_file_location("karvey_config", str(_path.SCRIPTS_DIR / "karvey-config.py"))
config = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(config)


def run(*argv, cwd=None):
    """``(exit_code, stdout, stderr)`` of ``karvey-config.py argv…``."""
    out, err = io.StringIO(), io.StringIO()
    old = os.getcwd()
    try:
        if cwd:
            os.chdir(str(cwd))
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = config.main([str(a) for a in argv])
    finally:
        os.chdir(old)
    return code, out.getvalue(), err.getvalue()


def run_json(*argv, cwd=None):
    """``(exit_code, envelope)`` with ``--json``."""
    code, out, _ = run(*(list(argv) + ["--json"]), cwd=cwd)
    return code, json.loads(out)


def make_project(root, project=None, specs=None):
    """A Karvey project tree (no git): ``project`` → project.json, ``specs`` {change: spec dict}."""
    root = Path(root)
    (root / "docs/spec/changes").mkdir(parents=True, exist_ok=True)
    if project is not None:
        (root / "docs/spec/project.json").write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")
    for cid, spec in (specs or {}).items():
        d = root / "docs/spec/changes" / cid
        d.mkdir(parents=True, exist_ok=True)
        (d / "spec.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return root


def tree_digest(root):
    """``{relpath: bytes}`` of every file under ``root`` (to prove nothing was written)."""
    root = Path(root)
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
