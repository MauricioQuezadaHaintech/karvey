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
                                                     "enforcement": {"plan_gate_hook": True, "plan_gate_edits": True}})
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


    def test_d1_role_or_ops_that_points_into_code_exempts_nothing(self):
        team = self.web.parent
        g.write(team, "docs/spec/team.json", {"code": "x", "ops_repo": "ops", "roles": {"app-web": "../../app-web/src/main"}})
        self.assertEqual(self.edit(self.web / "src/main.md")[0], 2)
        self.assertEqual(self.edit(self.web / "src/main/state.json")[0], 2)
        g.write(team, "docs/spec/team.json", {"code": "x", "ops_repo": "app-web", "roles": {"app-web": "web"}})
        self.assertEqual(self.edit(self.web / "board/web.md")[0], 2)
        self.assertEqual(self.edit(self.web / "agents/web/handoff.md")[0], 2)


if __name__ == "__main__":
    unittest.main()


class ProjectMarkerSession(unittest.TestCase):
    """D7 on D-47: a project-wide plan approval has no phase to close; it belongs to the session that gave it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = g.init(Path(os.path.realpath(self.tmp.name)) / "app")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"},
                                                      "enforcement": {"plan_gate_hook": True}})
        g.write(self.root, "src/a.py", "x\n")
        g.commit_all(self.root)
        e = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root.parent / "xdg"), approval.COMPAT_ENV: ""})
        e.start()
        self.addCleanup(e.stop)
        approval.write_marker(self.root, "plan", "_project", "ok", session_id="s-old", compat="")

    def run_rm(self, session):
        out, err = io.StringIO(), io.StringIO()
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": str(self.root), "session_id": session,
                   "tool_input": {"command": "rm src/a.py"}}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        return kh.dispatch("pre-bash", json.dumps(payload), env=env, out=out, err=err, only=["plan-gate"])

    def test_same_session_proceeds_another_session_is_gated(self):
        self.assertEqual(self.run_rm("s-old"), 0)
        self.assertEqual(self.run_rm("s-new"), 2)


class StopInListedClones(unittest.TestCase):
    """D-47 (REQ-HF-033), D1 re-check: a stop withdraws the plan approvals of the clones project.json lists too."""

    def test_stop_reaches_a_listed_clone(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(os.path.realpath(t))
            other = g.init(base / "app-api")
            g.write(other, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"}})
            g.commit_all(other)
            web = g.init(base / "app-web")
            g.write(web, "docs/spec/project.json", {"repos": ["app-web", "../app-api"],
                                                    "branch_flow": {"integration": "main", "production": "main"}})
            g.commit_all(web)
            with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(base / "xdg"), approval.COMPAT_ENV: ""}):
                approval.write_marker(other, "plan", "_project", "ok", session_id="s", compat="")
                out, err = io.StringIO(), io.StringIO()
                payload = {"hook_event_name": "UserPromptSubmit", "cwd": str(web), "session_id": "s",
                           "prompt": "detente"}
                kh.dispatch("prompt", json.dumps(payload), env=dict(os.environ, CLAUDE_PROJECT_DIR=str(web)),
                            out=out, err=err)
                self.assertIn("plan approval withdrawn", out.getvalue())
                m, _ = approval.read_marker(other, "_project")
                self.assertIsNotNone(m.get("stopped_at"))


class ApprovalSurvivesPhases(unittest.TestCase):
    """BUG-157 (REQ-HF-037): «apruebo» → the agent records the approvals of several phases of three changes →
    the implementation's first consequential action still passes; a stop still revokes it."""

    def setUp(self):
        from _state import state, run_json
        self.state, self.run_json = state, run_json
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = g.init(Path(os.path.realpath(self.tmp.name)) / "app")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"},
                                                      "enforcement": {"plan_gate_hook": True,
                                                                      "plan_gate_edits": True}})
        t0 = "2026-10-05T10:00:00-03:00"
        for cid in ("feat-a", "feat-b", "feat-c"):
            g.write(self.root, "docs/spec/changes/%s/spec.json" % cid, {
                "change_id": cid, "phase": "design_graphic", "skipped": {"mockup": "x"},
                "approvals": {k: {"generated": True, "approved": True, "by": "M", "role": "human", "date": t0,
                                  "ref": "D-1"} for k in ("requirements",)} | {
                    "design_graphic": {"generated": True, "approved": False}},
                "phase_history": [{"phase": p, "entered_at": t0, "exited_at": t0} for p in ("init", "requirements")]
                + [{"phase": "design_graphic", "entered_at": t0}]})
        g.write(self.root, "src/a.py", "x\n")
        g.commit_all(self.root)
        e = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root.parent / "xdg"), approval.COMPAT_ENV: ""})
        e.start()
        self.addCleanup(e.stop)

    def hook(self, event, extra):
        out, err = io.StringIO(), io.StringIO()
        payload = dict({"cwd": str(self.root), "session_id": "s-1"}, **extra)
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        return kh.dispatch(event, json.dumps(payload), env=env, out=out, err=err), out.getvalue(), err.getvalue()

    def st(self, *argv):
        return self.run_json(*(list(argv) + ["--root", str(self.root)]))

    def test_one_approval_covers_the_phases_and_the_implementation(self):
        self.assertIn("approval recorded (plan, _project", self.hook("prompt", {"prompt": "apruebo"})[1])
        for cid in ("feat-a", "feat-b", "feat-c"):
            c, env = self.st("approve", cid, "design_graphic", "--by", "M", "--role", "human", "--ref", "D-2")
            self.assertEqual(c, 0, env)
            c, env = self.st("advance", cid, "architecture")
            self.assertEqual(c, 0, env)
        write = {"tool_name": "Write", "tool_input": {"file_path": str(self.root / "src/a.py"), "content": "y"}}
        code, _o, err = self.hook("pre-edit", write)
        self.assertEqual(code, 0, err)
        rm = {"tool_name": "Bash", "tool_input": {"command": "rm src/a.py"}}
        self.assertEqual(self.hook("pre-bash", rm)[0], 0)
        self.assertIn("withdrawn", self.hook("prompt", {"prompt": "detente"})[1])
        self.assertEqual(self.hook("pre-bash", rm)[0], 2)
