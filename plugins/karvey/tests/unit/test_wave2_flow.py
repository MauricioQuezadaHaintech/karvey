"""Integration: a `standard` change through the Wave 2 flow in a temp repository (AC-4, AC-5 of wave2-structural).

init → `lane set standard` → the three merged human gates (`approve-gate what|how|release`, one answer each, with a
planted approval marker standing in for the human's message) → every commit with the `Karvey-Change` trailer →
`release-gate check` passes and the release manifest is `pass`.

@req REQ-W2-034 REQ-W2-036 REQ-W2-045 REQ-W2-046 REQ-W2-069
"""
import contextlib
import importlib.util
import io
import json
import os
import unittest
from unittest import mock

import _path
import _gitrepo as g
from _state import run_json
from karvey_lib import approval as ap

g.isolate_git()
_SPEC = importlib.util.spec_from_file_location("karvey_release_gate_flow", str(_path.SCRIPTS_DIR / "karvey-release-gate.py"))
rg = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rg)
CID = "add-export"
TRAILER = "\n\nKarvey-Change: %s\n" % CID
REQS = "# Requirements\n\n### 1.1 REQ-EX-001 — export\nWHEN asked, the system SHALL export.\n"


class Wave2Flow(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        self.envp = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg"), ap.COMPAT_ENV: ""})
        self.envp.start()
        g.write(self.root, "docs/spec/project.json", {
            "git_platform": "github", "repos": ["r"], "spec_repo": "r", "gates": "merged",
            "branch_flow": {"integration": "main", "production": "main", "mode": "trunk"}})
        g.write(self.root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n## [1.0.0]\n- first\n")
        g.write(self.root, "package.json", {"name": "demo", "version": "1.0.0"})
        g.commit_all(self.root, "base")
        g.run(["tag", "base"], self.root)
        g.run(["checkout", "-q", "-b", "feature/" + CID], self.root)
        self.cdir = self.root / "docs/spec/changes" / CID

    def tearDown(self):
        self.envp.stop()
        self.t.cleanup()

    def ok(self, *argv):
        code, env = run_json(*(list(argv) + ["--root", str(self.root)]))
        self.assertEqual(code, 0, env)
        return env["result"]

    def commit(self, msg):
        g.commit_all(self.root, msg + TRAILER)

    def spec(self):
        return json.loads((self.cdir / "spec.json").read_text(encoding="utf-8"))

    def gate(self, name, ref):
        return self.ok("approve-gate", CID, name, "--by", "Owner", "--role", "human", "--ref", ref)

    def test_REQ_W2_034_three_gates_trailers_and_a_passing_release_gate(self):
        self.ok("init", CID)
        self.ok("lane", CID, "set", "standard")
        self.commit("chore: init %s" % CID)
        # what: requirements (mockup and design are passed by the lane)
        self.ok("advance", CID, "requirements")
        (self.cdir / "requirements.md").write_text(REQS, encoding="utf-8")
        self.ok("generated", CID, "requirements")
        self.assertEqual(self.ok("gate", CID, "requirements")["mode"], "merged")
        ap.write_marker(self.root, "plan", CID, "aprobado, sigue")
        self.assertEqual(self.gate("what", "D-1")["approved"], ["requirements"])
        self.commit("docs: requirements")
        # how: architecture + tasks (infra skipped with its reason)
        self.ok("advance", CID, "architecture")
        (self.cdir / "architecture.md").write_text("# Architecture\n\nNo cloud.\n", encoding="utf-8")
        self.ok("generated", CID, "architecture")
        self.ok("skip", CID, "infra", "--reason", "no cloud")
        self.ok("advance", CID, "tasks")
        (self.cdir / "tasks.md").write_text(
            "# Tasks\n\n### E1.F1.T1 [Test] export test\n\n**Requirements:** REQ-EX-001\n**Tests added:** yes\n\n"
            "### E1.F1.T2 [Backend] export — _Depends: E1.F1.T1_\n\n**Requirements:** REQ-EX-001\n", encoding="utf-8")
        self.ok("generated", CID, "tasks")
        ap.write_marker(self.root, "plan", CID, "aprobado, sigue")
        self.assertEqual(self.gate("how", "D-2")["approved"], ["architecture", "tasks"])
        self.commit("docs: architecture and tasks")
        # impl + test, with the trailer on every commit
        self.ok("advance", CID, "impl")
        g.write(self.root, "tests/test_export.py", '"""@req REQ-EX-001"""\n\ndef test_export():\n    assert True\n')
        self.commit("test: E1.F1.T1 export test fails first")
        g.write(self.root, "src/export.py", "def export():\n    return 'ok'\n")
        g.write(self.root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n- %s — export (E1.F1.T2)\n\n"
                                            "## [1.0.0]\n- first\n" % CID)
        self.commit("feat: E1.F1.T2 export")
        self.ok("advance", CID, "test")
        (self.cdir / "evidence.jsonl").write_text(json.dumps(
            {"argv": ["python3", "-m", "unittest", "discover", "-s", "tests"], "cwd_rel": ".", "exit": 0,
             "label": "unit"}) + "\n", encoding="utf-8")
        self.commit("test: evidence")
        # release: QA (prod stays pending without a prod-kind marker: the release gate records QA only)
        self.ok("advance", CID, "qa")
        self.ok("generated", CID, "qa")
        ap.write_marker(self.root, "plan", CID, "aprobado, sigue")
        r = self.gate("release", "D-3")
        self.assertEqual(r["approved"], ["qa"])
        self.commit("docs: qa approved")
        outcomes = [o for o in self.spec().get("gate_outcomes", []) if o.get("outcome") == "approved"]
        self.assertEqual([o["gate"] for o in outcomes], ["what", "how", "release"])  # exactly three questions
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = rg.main(["check", CID, "--base", "base", "--root", str(self.root), "--json"])
        res = json.loads(out.getvalue())["result"]
        self.assertEqual(res["items"]["manifest"]["status"], "pass", res)
        self.assertEqual(res["items"]["qa_gate"]["status"], "pass", res)
        self.assertEqual(res["items"]["tests"]["status"], "pass", res)
        self.assertEqual((code, res["verdict"]), (0, "pass"), res)
        man = json.loads(io.StringIO(json.dumps(res)).getvalue())
        self.assertIn(CID, man["items"]["manifest"]["detail"])


if __name__ == "__main__":
    unittest.main()
