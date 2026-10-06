"""Worlds of sibling clones for the prod-gate unit tests (REQ-HF-007, 008, 010..015, 024..026)."""
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from karvey_lib import approval, guards
from karvey_lib import karvey_hooks as kh

g.isolate_git()
SESSION = "s-unit"


def git_out(args, cwd):
    return subprocess.run(["git"] + args, cwd=str(cwd), check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL).stdout.decode().strip()


class World(unittest.TestCase):
    """A temp folder with sibling clones; ``self.cli`` maps ``(argv0, sub…)`` prefixes to canned answers."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(os.path.realpath(self.tmp.name))
        self.cli = []  # [(prefix tuple, answer dict | None, error str | None)]
        self.calls = []
        p = mock.patch.object(guards, "_run_cli", side_effect=self._fake_cli)
        p.start()
        self.addCleanup(p.stop)
        e = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.base / "xdg"), approval.COMPAT_ENV: ""})
        e.start()
        self.addCleanup(e.stop)

    def _fake_cli(self, argv, cwd, budget):
        self.calls.append((list(argv), cwd))
        for prefix, ans, err in self.cli:
            if tuple(argv[:len(prefix)]) == tuple(prefix):
                return (None, err) if err else (dict(ans), None)
        return None, "%s: no canned answer" % argv[0]

    def answer(self, prefix, data=None, err=None):
        self.cli.insert(0, (tuple(prefix), data or {}, err))

    def clone(self, name, flow=None, changes=None, project_extra=None, karvey=True, origin_head=None,
              remote_url=None):
        root = g.init(self.base / name)
        if karvey:
            pj = {"repos": [name], "branch_flow": flow or {"feature_prefix": "feature/", "integration": "dev",
                                                            "production": "main"}}
            pj.update(project_extra or {})
            g.write(root, "docs/spec/project.json", pj)
            for cid, data in (changes or {}).items():
                d = {"change_id": cid, "phase": "deploying"}
                d.update(data or {})
                g.write(root, "docs/spec/changes/%s/spec.json" % cid, d)
        else:
            g.write(root, "README.md", "x\n")
        g.commit_all(root, "fixture")
        bare = g.with_origin(root, "main")
        for b in ("dev",):
            g.run(["push", "-q", "origin", "HEAD:refs/heads/%s" % b], root)
        g.run(["fetch", "-q", "origin"], root)
        g.run(["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/%s" % (origin_head or "main")], root)
        if remote_url:
            g.run(["remote", "set-url", "origin", remote_url], root)
            g.run(["remote", "add", "real", str(bare)], root)
        return root

    def head(self, root):
        return git_out(["rev-parse", "HEAD"], root)

    def approve(self, root, cid, sha):
        m = approval.write_marker(root, "prod", cid, "ok, merge a prod %s" % cid, session_id=SESSION, compat="")
        approval.record_prod(root, cid, approval.prod_record(m, cid, "Owner Name", "D-08", approval.iso(
            approval.now_dt()), sha))
        approval.consume(root, cid, created_at=m["created_at"])

    def run_gate(self, command, cwd, project_dir=None):
        out, err = io.StringIO(), io.StringIO()
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": SESSION,
                   "cwd": str(cwd), "tool_input": {"command": command}}
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(project_dir or cwd)
        code = kh.dispatch("pre-bash", json.dumps(payload), env=env, out=out, err=err, only=["prod-gate"])
        return code, out.getvalue(), err.getvalue()

    def assertAllow(self, res, contains=None):
        code, out, err = res
        self.assertEqual(code, 0, (out, err))
        if contains:
            self.assertIn(contains, out)

    def assertBlock(self, res, contains=None):
        code, out, err = res
        self.assertEqual(code, 2, (out, err))
        if contains:
            self.assertIn(contains, err)

    def gh_pr(self, base, head, sha, title="Deploy", url=None):
        d = {"baseRefName": base, "headRefName": head, "headRefOid": sha, "title": title, "number": 12}
        if url:
            d["url"] = url
        self.answer(("gh", "pr", "view"), d)
