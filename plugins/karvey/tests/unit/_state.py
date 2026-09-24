"""Load karvey-state.py (hyphenated, so not importable by name) and run it in-process."""
import contextlib
import importlib.util
import io
import json
import os

import _path

_SPEC = importlib.util.spec_from_file_location("karvey_state", str(_path.SCRIPTS_DIR / "karvey-state.py"))
state = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(state)


def run(*argv, cwd=None):
    """``(exit_code, stdout, stderr)`` of ``karvey-state.py argv…``."""
    out, err = io.StringIO(), io.StringIO()
    old = os.getcwd()
    try:
        if cwd:
            os.chdir(str(cwd))
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = state.main(list(argv))
    finally:
        os.chdir(old)
    return code, out.getvalue(), err.getvalue()


def run_json(*argv, cwd=None):
    """``(exit_code, envelope)`` with ``--json``."""
    code, out, _ = run(*(list(argv) + ["--json"]), cwd=cwd)
    return code, json.loads(out)


GOOD_SPEC = {
    "change_id": "feat-a", "phase": "requirements", "schema_version": 1,
    "phase_history": [
        {"phase": "init", "entered_at": "2026-09-23T10:00:00-03:00", "exited_at": "2026-09-23T10:00:00-03:00"},
        {"phase": "requirements", "entered_at": "2026-09-23T10:00:00-03:00"}],
    "approvals": {"requirements": {"generated": True, "approved": False}},
}


def make_project(root, spec=None, project=None, change="feat-a"):
    """A minimal Karvey project tree (no git) with one change."""
    from pathlib import Path
    root = Path(root)
    (root / "docs/spec/changes").mkdir(parents=True, exist_ok=True)
    if project is not None:
        (root / "docs/spec/project.json").write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")
    if spec is not None:
        d = root / "docs/spec/changes" / change
        d.mkdir(parents=True, exist_ok=True)
        text = spec if isinstance(spec, str) else json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
        (d / "spec.json").write_text(text, encoding="utf-8")
        return d / "spec.json"
    return None
