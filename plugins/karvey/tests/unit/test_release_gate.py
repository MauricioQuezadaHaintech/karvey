"""karvey-release-gate.py: the release manifest and the release gate (architecture §1.9 of wave2-structural).

@req REQ-W2-045 REQ-W2-046 REQ-W2-047 REQ-W2-050 REQ-W2-069 REQ-W2-014
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


class Check(Base):
    def setUp(self):
        super().setUp()
        g.write(self.root, "package.json", {"name": "x", "version": "1.0.0"})
        g.commit_all(self.root, "chore: package version\n\nKarvey-Change: feat-a")

    def evidence(self, cid, exit_code=0):
        p = self.root / "docs/spec/changes" / cid / "evidence.jsonl"
        p.write_text(json.dumps({"argv": ["python3", "-m", "unittest"], "cwd_rel": ".", "exit": exit_code,
                                 "label": "unit"}) + "\n", encoding="utf-8")

    def check(self, cid, *extra):
        code, out = run("check", cid, "--base", "base", "--root", str(self.root), "--json", *extra)
        return code, json.loads(out)["result"]

    def test_REQ_W2_069_all_items_pass(self):
        self.change("feat-a")
        self.evidence("feat-a")
        code, r = self.check("feat-a")
        self.assertEqual((code, r["verdict"]), (0, "pass"), r)
        self.assertEqual(set(r["items"]), set(rg.ITEMS))
        st = {k: v["status"] for k, v in r["items"].items()}
        self.assertEqual(st["qa_gate"], "pass")
        self.assertEqual(st["version_match"], "pass")
        self.assertEqual(st["lane_triplet"], "not-applicable")
        self.assertEqual(st["pr_body"], "not-applicable")

    def test_REQ_W2_069_no_changelog_line_exits_1_naming_changelog(self):
        self.change("feat-c")
        self.evidence("feat-c")
        code, r = self.check("feat-c")
        self.assertEqual((code, r["verdict"]), (1, "fail"))
        self.assertIn("changelog", r["failed"])
        self.assertEqual(r["items"]["changelog"]["status"], "fail")

    def test_tests_not_evaluated_without_evidence(self):
        self.change("feat-a")
        code, r = self.check("feat-a")
        self.assertEqual(code, 1)
        self.assertIn("not evaluated", r["items"]["tests"]["detail"])

    def test_red_last_run_fails_tests(self):
        self.change("feat-a")
        self.evidence("feat-a", exit_code=1)
        _, r = self.check("feat-a")
        self.assertEqual(r["items"]["tests"]["status"], "fail")

    def test_version_mismatch_fails(self):
        g.write(self.root, "package.json", {"name": "x", "version": "1.1.0"})
        self.change("feat-a")
        self.evidence("feat-a")
        code, r = self.check("feat-a")
        self.assertEqual((code, r["items"]["version_match"]["status"]), (1, "fail"))
        self.assertIn("1.1.0", r["items"]["version_match"]["detail"])

    def test_REQ_W2_047_pr_body_lists_one_of_two_changes(self):
        self.change("feat-a")
        self.change("feat-b")
        self.evidence("feat-a")
        body = self.t.path / "pr.md"
        body.write_text("Release\n- feat-a\n", encoding="utf-8")
        code, r = self.check("feat-a", "--pr-body", str(body))
        self.assertEqual((code, r["items"]["pr_body"]["status"]), (1, "fail"))
        self.assertIn("feat-b", r["items"]["pr_body"]["detail"])
        body.write_text("Release\n- feat-a\n- feat-b\n", encoding="utf-8")
        code, r = self.check("feat-a", "--pr-body", str(body))
        self.assertEqual((code, r["items"]["pr_body"]["status"]), (0, "pass"))

    def test_manifest_warn_is_not_a_failure(self):
        self.change("feat-a")
        self.change("feat-b", qa=False)
        self.evidence("feat-a")
        code, r = self.check("feat-a")
        self.assertEqual((code, r["verdict"], r["items"]["manifest"]["status"]), (0, "warn", "warn"))

    def test_REQ_W2_014_patch_without_regression_test_fails_the_triplet(self):
        self.change("feat-a", lane="patch")
        self.evidence("feat-a")
        _, r = self.check("feat-a")
        self.assertEqual(r["items"]["lane_triplet"]["status"], "fail")
        self.assertIn("regression test", r["items"]["lane_triplet"]["detail"])
        sp = json.loads((self.root / "docs/spec/changes/feat-a/spec.json").read_text())
        sp["lane_evidence"] = {"bug_id": "BUG-01", "finding": "F-01", "regression_test": "src/feat-a.py::test_x"}
        g.write(self.root, "docs/spec/changes/feat-a/spec.json", sp)
        _, r = self.check("feat-a")
        self.assertEqual(r["items"]["lane_triplet"]["status"], "pass")

    def test_spec_merged_item_reads_spec_merge_check(self):
        self.change("feat-a")
        self.evidence("feat-a")
        sp = json.loads((self.root / "docs/spec/changes/feat-a/spec.json").read_text())
        sp["capability"] = "cap"
        g.write(self.root, "docs/spec/changes/feat-a/spec.json", sp)
        g.write(self.root, "docs/spec/changes/feat-a/spec-delta.md",
                "# Spec delta\n\n## ADDED Requirements\n\n- **REQ-A-001** — the thing SHALL work.\n")
        _, r = self.check("feat-a")
        self.assertEqual(r["items"]["spec_merged"]["status"], "fail")
        self.assertIn("REQ-A-001", r["items"]["spec_merged"]["detail"])


class ReleaseBranch(Base):
    def test_REQ_W2_050_lists_the_approved_commits_in_order(self):
        self.change("feat-a")
        self.change("feat-b", qa=False)
        g.write(self.root, "src/a2.py", "x\n")
        g.commit_all(self.root, "feat: a again" + TRAILER % "feat-a")
        code, out = run("release-branch", "--version", "1.1.0", "--base", "base", "--root", str(self.root), "--json")
        r = json.loads(out)["result"]
        self.assertEqual(code, 0)
        self.assertEqual([c["subject"] for c in r["commits"]], ["docs: feat-a spec", "feat: feat-a", "feat: a again"])
        self.assertEqual(r["excluded"], [{"id": "feat-b", "qa": "missing"}])
        self.assertEqual(r["branch"], "release/1.1.0")
        self.assertEqual(r["commands"][0], "git switch -c release/1.1.0 base")
        self.assertFalse(r["executed"])
        import subprocess
        branches = subprocess.run(["git", "branch", "--list", "release/*"], cwd=str(self.root),
                                  capture_output=True, text=True).stdout
        self.assertEqual(branches.strip(), "")


if __name__ == "__main__":
    unittest.main()
