"""karvey-release-gate.py: the release manifest and the release gate (architecture §1.9 of wave2-structural).

@req REQ-W2-045 REQ-W2-046
"""
import contextlib
import importlib.util
import io
import json
import unittest

import _path
import _gitrepo as g

g.isolate_git()
_SPEC = importlib.util.spec_from_file_location("karvey_release_gate", str(_path.SCRIPTS_DIR / "karvey-release-gate.py"))
rg = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rg)
T0 = "2026-09-25T10:00:00-03:00"
TRAILER = "\n\nKarvey-Change: %s\n"
PROJECT = {"git_platform": "github", "repos": ["r"], "spec_repo": "r",
           "branch_flow": {"integration": "main", "production": "main"}}


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = rg.main(list(argv))
    return code, out.getvalue()


def spec(cid, qa=True, lane="standard"):
    s = {"change_id": cid, "phase": "qa", "lane": lane,
         "phase_history": [{"phase": "init", "entered_at": T0}], "approvals": {}}
    if qa:
        s["approvals"]["qa"] = {"generated": True, "approved": True, "by": "o", "role": "human", "date": T0,
                                "ref": "D-1"}
    return s


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        g.write(self.root, "docs/spec/project.json", dict(PROJECT, checks=self.checks()))
        g.write(self.root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n- feat-a — x\n- feat-b — y\n\n## [1.0.0]\n- old\n")
        g.commit_all(self.root, "base")
        g.run(["tag", "base"], self.root)

    def checks(self):
        return {}

    def tearDown(self):
        self.t.cleanup()

    def change(self, cid, qa=True, lane="standard", trailer=True):
        g.write(self.root, "docs/spec/changes/%s/spec.json" % cid, spec(cid, qa, lane))
        g.commit_all(self.root, "docs: %s spec" % cid)
        g.write(self.root, "src/%s.py" % cid, "x\n")
        g.commit_all(self.root, "feat: %s" % cid + (TRAILER % cid if trailer else ""))

    def manifest(self, *extra):
        code, out = run("manifest", "--base", "base", "--root", str(self.root), "--json", *extra)
        return code, json.loads(out)

    def hits(self, cid):
        p = self.root / "docs/spec/changes" / cid / "checks.jsonl"
        return [json.loads(x) for x in p.read_text().splitlines()] if p.is_file() else []


class Manifest(Base):
    def test_REQ_W2_045_two_changes_listed_with_commits(self):
        self.change("feat-a")
        self.change("feat-b")
        code, env = self.manifest()
        r = env["result"]
        self.assertEqual(code, 0, env)
        self.assertEqual([c["id"] for c in r["changes"]], ["feat-a", "feat-b"])
        self.assertTrue(all(len(c["commits"]) == 2 for c in r["changes"]))
        self.assertEqual(r["changes"][0]["version"], "Unreleased")
        self.assertEqual((r["verdict"], r["unmapped"]), ("pass", []))
        self.assertEqual(self.hits("feat-a"), [])

    def test_REQ_W2_046_unmapped_is_warn_in_warn_mode_with_hits(self):
        self.change("feat-a")
        g.write(self.root, "src/z.py", "z\n")
        g.commit_all(self.root, "chore: stray")
        code, env = self.manifest()
        self.assertEqual((code, env["result"]["verdict"], env["result"]["mode"]), (0, "warn", "warn"))
        h = self.hits("feat-a")
        self.assertEqual(len(h), 1)
        self.assertEqual((h[0]["check"], h[0]["would_refuse"]), ("release.manifest", True))
        self.assertIn("no Karvey-Change trailer", h[0]["detail"])

    def test_change_without_qa_is_not_pass(self):
        self.change("feat-a", qa=False)
        code, env = self.manifest()
        self.assertEqual(env["result"]["verdict"], "warn")
        self.assertEqual(env["result"]["changes"][0]["qa"], "missing")

    def test_hotfix_without_qa_record_is_missing(self):
        self.change("feat-a", qa=False, lane="hotfix")  # hotfix: qa optional and not skipped
        code, env = self.manifest()
        self.assertEqual(env["result"]["changes"][0]["qa"], "missing")

    def test_no_record_writes_nothing(self):
        self.change("feat-a", qa=False)
        self.manifest("--no-record")
        self.assertEqual(self.hits("feat-a"), [])

    def test_bad_base_is_not_found(self):
        code, out = run("manifest", "--base", "nope", "--root", str(self.root), "--json")
        self.assertEqual(code, 4)
        self.assertIn("not computable", json.loads(out)["errors"][0]["message"])


class Blocking(Base):
    def checks(self):
        return {"release.manifest": "blocking"}

    def test_REQ_W2_046_unmapped_is_fail_in_blocking(self):
        self.change("feat-a", trailer=False)
        code, env = self.manifest()
        self.assertEqual((code, env["result"]["verdict"]), (1, "fail"))
        self.assertEqual(env["result"]["unmapped"][0]["reason"], "no Karvey-Change trailer")

    def test_all_approved_is_pass_even_in_blocking(self):
        self.change("feat-a")
        code, env = self.manifest()
        self.assertEqual((code, env["result"]["verdict"]), (0, "pass"))


if __name__ == "__main__":
    unittest.main()
