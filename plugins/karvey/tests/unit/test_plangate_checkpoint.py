"""BUG-154 (REQ-HF-031): a checkpoint or handoff save never needs a plan approval; nothing else is exempt."""
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from karvey_lib import approval
from karvey_lib import karvey_hooks as kh

g.isolate_git()


class TeamLayout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        team = Path(os.path.realpath(self.tmp.name)) / "team"
        g.write(team, "docs/spec/team.json", {"code": "x", "ops_repo": "ops", "roles": {"app-web": "web",
                                                                                         "app-api": "api"}})
        self.ops = g.init(team / "ops")
        for role in ("web", "api"):
            g.write(self.ops, "agents/%s/handoff.md" % role, "h\n")
            g.write(self.ops, "board/%s.md" % role, "b\n")
        self.web = g.init(team / "app-web")
        g.write(self.web, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"},
                                                     "enforcement": {"plan_gate_hook": True}})
        g.commit_all(self.web)
        e = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(team / "xdg"), approval.COMPAT_ENV: ""})
        e.start()
        self.addCleanup(e.stop)

    def edit(self, path):
        out, err = io.StringIO(), io.StringIO()
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": str(self.web), "session_id": "s",
                   "tool_input": {"file_path": str(path), "content": "x"}}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.web))
        return kh.dispatch("pre-edit", json.dumps(payload), env=env, out=out, err=err, only=["plan-gate"]), err.getvalue()

    def test_own_team_profile_files_need_no_approval(self):
        self.assertEqual(self.edit(self.ops / "agents/web/handoff.md")[0], 0)
        self.assertEqual(self.edit(self.ops / "agents/web/state.json")[0], 0)
        self.assertEqual(self.edit(self.ops / "board/web.md")[0], 0)

    def test_another_agents_profile_and_other_files_stay_gated(self):
        self.assertEqual(self.edit(self.ops / "agents/api/handoff.md")[0], 2)
        self.assertEqual(self.edit(self.ops / "agents/web/manifest.md")[0], 2)
        self.assertEqual(self.edit(self.web / "docs/spec/project.json")[0], 2)


if __name__ == "__main__":
    unittest.main()
