"""karvey-spec-merge.py --check (architecture §1.11 of wave2-structural).

@req REQ-W1-067 REQ-W2-054 REQ-W2-055 REQ-W2-056
"""
import unittest

from test_spec_merge import Base


class Check(Base):
    def check(self):
        before = self.text()
        code, env = self.merge("--check")
        self.assertEqual(self.text(), before)  # read-only
        return code, env["result"]

    def test_REQ_W2_055_merged_delta_reports_merged_and_writes_nothing(self):
        code, env = self.merge()
        self.assertEqual(code, 0, env["errors"])
        code, r = self.check()
        self.assertEqual((code, r["status"], r["pending"]), (0, "merged", []))

    def test_REQ_W2_054_unmerged_names_the_ids(self):
        code, r = self.check()
        self.assertEqual((code, r["status"]), (1, "unmerged"))
        self.assertEqual(sorted(r["pending"]), ["REQ-A-002", "REQ-A-003", "REQ-X-001", "REQ-X-002"])

    def test_REQ_W2_054_different_text_is_a_conflict(self):
        self.target.write_text(self.text() + "- **REQ-X-001** — THE other text.\n", encoding="utf-8")
        code, r = self.check()
        self.assertEqual((code, r["status"]), (1, "conflict"))
        self.assertIn("REQ-X-001", r["conflict_ids"])

    def test_human_line(self):
        from test_spec_merge import run
        code, out, _ = run("feat-x", "--root", str(self.root), "--check")
        self.assertEqual(code, 1)
        self.assertIn("unmerged into docs/spec/specs/demo/spec.md", out + _)


class L49(Base):
    """@req REQ-W2-056 — a deployed change with an unmerged delta is a lint error."""

    def lint(self):
        import importlib.util
        import json as _json
        import _path
        spec = importlib.util.spec_from_file_location("lint_plugin_l49", str(_path.SCRIPTS_DIR / "lint-plugin.py"))
        lp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lp)
        (self.cdir / "spec.json").write_text(_json.dumps({"change_id": "feat-x", "capability": "demo",
                                                           "phase": "deployed"}), encoding="utf-8")
        return lp.run_checks(lp.Ctx(self.root), only={"L-49"})

    def test_REQ_W2_056_deployed_unmerged_is_an_error(self):
        fs = self.lint()
        self.assertEqual([f["severity"] for f in fs], ["error"])
        self.assertIn("deployed but its spec-delta is unmerged", fs[0]["message"])

    def test_deployed_merged_passes(self):
        self.merge()
        self.assertEqual(self.lint(), [])


if __name__ == "__main__":
    unittest.main()
