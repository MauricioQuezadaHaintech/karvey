"""Integration: the official `patch` lane end to end in a temp repository (AC-2 of wave2-structural, E1.F2.T9).

init → `lane set patch` (D-29 answers, admitted) → BUG-NN + finding + fix + regression test on the change
branch, every commit with the trailer → `lane-evidence` → impl / test / qa with the six design phases recorded as
`lane:patch` → QA-lite by `role: auto` → `release-gate check` (`lane_triplet: pass`) — the production gate is the
only human gate left. The same change touching a migration is refused at `lane set`.

@req REQ-W2-013 REQ-W2-014
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
from karvey_lib import approval as ap, lanes

g.isolate_git()
_SPEC = importlib.util.spec_from_file_location("karvey_release_gate", str(_path.SCRIPTS_DIR / "karvey-release-gate.py"))
rg = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rg)
CID = "fix-login-typo"
TRAILER = "\n\nKarvey-Change: %s\n" % CID
DESIGN = ("requirements", "mockup", "design_graphic", "architecture", "infra", "tasks")


class PatchLaneFlow(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        self.envp = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg"), ap.COMPAT_ENV: ""})
        self.envp.start()
        g.write(self.root, "docs/spec/project.json", {
            "git_platform": "github", "repos": ["r"], "spec_repo": "r",
            "branch_flow": {"integration": "main", "production": "main"}})
        g.write(self.root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n## [1.0.0]\n- first\n")
        g.write(self.root, "package.json", {"name": "demo", "version": "1.0.0"})
        g.write(self.root, "src/login.py", "MSG = 'Pasword'\n")
        g.commit_all(self.root, "base")
        g.run(["tag", "base"], self.root)
        g.run(["checkout", "-q", "-b", "feature/" + CID], self.root)

    def tearDown(self):
        self.envp.stop()
        self.t.cleanup()

    def st(self, *argv):
        return run_json(*(list(argv) + ["--root", str(self.root)]))

    def ok(self, *argv):
        code, env = self.st(*argv)
        self.assertEqual(code, 0, env)
        return env["result"]

    def answers(self, **over):
        a = {"touches_ui": False, "schema": False, "api_contract": False, "permissions_or_trust": False,
             "tier": 2, "code_files": 2}
        a.update(over)
        p = self.t.path / "answers.json"
        p.write_text(json.dumps(a), encoding="utf-8")
        return str(p)

    def spec(self):
        return json.loads((self.root / "docs/spec/changes" / CID / "spec.json").read_text(encoding="utf-8"))

    def release_gate(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = rg.main(["check", CID, "--base", "base", "--root", str(self.root), "--json"])
        return code, json.loads(out.getvalue())["result"]

    def test_REQ_W2_013_REQ_W2_014_patch_flow_one_human_gate(self):
        self.ok("init", CID)
        self.assertEqual(self.ok("lane", CID, "set", "patch", "--answers", self.answers())["lane"], "patch")
        # the triplet: incident, finding, fix and a regression test — every commit carries the trailer
        g.write(self.root, "docs/bugs_dev_testing.md", "| BUG-01 | login label typo | ABIERTO |\n")
        g.write(self.root, "docs/spec/changes/%s/findings.md" % CID, "| F-01 | test | bug | login label typo |\n")
        g.write(self.root, "tests/test_login.py",
                '"""@req REQ-P-001"""\nfrom src import login\n\ndef test_bug_01():\n'
                '    assert login.MSG == "Password"\n')
        g.commit_all(self.root, "test: BUG-01 regression test (fails before the fix)" + TRAILER)
        g.write(self.root, "src/login.py", "MSG = 'Password'\n")
        g.write(self.root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n- %s — BUG-01 fixed\n\n"
                                            "## [1.0.0]\n- first\n" % CID)
        g.commit_all(self.root, "fix: BUG-01 login label" + TRAILER)
        self.ok("lane-evidence", CID, "--bug", "BUG-01", "--finding", "F-01",
                "--regression-test", "tests/test_login.py::test_bug_01")
        # impl straight from init: the six design phases are recorded as lane-skipped, never approved
        self.ok("advance", CID, "impl")
        data = self.spec()
        self.assertEqual({p: data["skipped"][p] for p in DESIGN}, {p: "lane:patch" for p in DESIGN})
        self.assertFalse(any(isinstance(v, dict) and v.get("approved") for v in data["approvals"].values()))
        self.ok("advance", CID, "test")
        (self.root / "docs/spec/changes" / CID / "evidence.jsonl").write_text(
            json.dumps({"argv": ["python3", "-m", "unittest", "discover", "-s", "tests"], "cwd_rel": ".",
                        "exit": 0, "label": "regression"}) + "\n", encoding="utf-8")
        self.ok("advance", CID, "qa")
        self.ok("approve", CID, "qa", "--by", "agent", "--role", "auto", "--ref", "qa-lite")
        # one human gate: the lane declares only prod, and prod is never satisfied by auto
        self.assertEqual(lanes.gates_of("patch"), ["prod"])
        code, env = self.st("approve", CID, "prod", "--by", "agent", "--role", "auto", "--ref", "D-1")
        self.assertEqual(code, 3, env)
        code, r = self.release_gate()
        self.assertEqual(r["items"]["lane_triplet"]["status"], "pass", r)
        self.assertEqual(r["items"]["qa_gate"]["status"], "pass", r)
        self.assertEqual(r["items"]["changelog"]["status"], "pass", r)
        self.assertEqual(r["items"]["manifest"]["status"], "pass", r)
        self.assertEqual((code, r["verdict"]), (0, "pass"), r)

    def test_REQ_W2_013_patch_with_a_migration_refused_at_lane_set(self):
        self.ok("init", CID)
        before = (self.root / "docs/spec/changes" / CID / "spec.json").read_bytes()
        code, env = self.st("lane", CID, "set", "patch", "--answers", self.answers(schema=True))
        self.assertEqual(code, 3, env)
        self.assertIn("schema change", env["errors"][0]["message"])
        self.assertEqual(env["result"]["proposed"], "standard")
        self.assertEqual((self.root / "docs/spec/changes" / CID / "spec.json").read_bytes(), before)

    def test_REQ_W2_014_patch_without_regression_test_is_not_releasable(self):
        self.ok("init", CID)
        self.ok("lane", CID, "set", "patch", "--answers", self.answers())
        g.write(self.root, "src/login.py", "MSG = 'Password'\n")
        g.commit_all(self.root, "fix: login label" + TRAILER)
        self.ok("lane-evidence", CID, "--bug", "BUG-01", "--finding", "F-01")
        code, r = self.release_gate()
        self.assertEqual(code, 1)
        self.assertEqual(r["items"]["lane_triplet"]["status"], "fail")
        self.assertIn("regression test", r["items"]["lane_triplet"]["detail"])


if __name__ == "__main__":
    unittest.main()
