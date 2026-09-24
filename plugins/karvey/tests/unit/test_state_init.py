"""karvey-state.py init: the state of a new change is created by the tool (REQ-W1-013, F-25)."""
import json
import os
import unittest
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from _state import make_project, run_json, state

g.isolate_git()


class Init(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        make_project(self.root)
        self.env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.t.cleanup()

    def spec(self, change="feat-a"):
        return json.loads((self.root / "docs/spec/changes" / change / "spec.json").read_text(encoding="utf-8"))

    def test_creates_a_valid_spec_in_init(self):
        code, env = run_json("--root", str(self.root), "init", "feat-a", "--by", "M")
        self.assertEqual(code, 0, env)
        self.assertTrue(env["result"]["created"])
        d = self.spec()
        self.assertEqual(d["phase"], "init")
        self.assertEqual(d["change_id"], "feat-a")
        self.assertEqual(d["phase_history"][0]["phase"], "init")
        self.assertEqual(d["phase_history"][0]["by"], "M")
        self.assertEqual(d["approvals"], {})
        code, env = run_json("--root", str(self.root), "validate", str(self.root / "docs/spec/changes/feat-a/spec.json"))
        self.assertEqual(code, 0, env)

    def test_adds_state_to_a_spec_without_phase_and_keeps_its_fields(self):
        make_project(self.root, spec={"change_id": "feat-a", "goal": "x", "layers": ["Backend"]})
        code, env = run_json("--root", str(self.root), "init", "feat-a")
        self.assertEqual(code, 0, env)
        self.assertFalse(env["result"]["created"])
        d = self.spec()
        self.assertEqual((d["phase"], d["goal"], d["layers"]), ("init", "x", ["Backend"]))

    def test_refuses_a_spec_that_already_has_a_phase(self):
        path = make_project(self.root, spec={"change_id": "feat-a", "phase": "requirements"})
        before = path.read_bytes()
        code, env = run_json("--root", str(self.root), "init", "feat-a")
        self.assertEqual(code, 3, env)
        self.assertEqual(path.read_bytes(), before)

    def test_refuses_an_invalid_change_id(self):
        code, _ = run_json("--root", str(self.root), "init", "../evil")
        self.assertEqual(code, 2)

    def test_next_after_init_points_at_requirements(self):
        run_json("--root", str(self.root), "init", "feat-a")
        code, env = run_json("--root", str(self.root), "next", "feat-a")
        self.assertEqual(code, 0, env)
        self.assertIn("requirements", json.dumps(env["result"]))


if __name__ == "__main__":
    unittest.main()
