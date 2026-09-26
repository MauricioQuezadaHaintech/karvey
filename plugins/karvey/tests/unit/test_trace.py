"""karvey-trace.py: requirement → task → commit → test (architecture §1.12 C-14 of wave2-structural).

@req REQ-W2-057 REQ-W2-058 REQ-W2-060
"""
import importlib.util
import unittest

import _path
import _gitrepo as g

g.isolate_git()
_SPEC = importlib.util.spec_from_file_location("karvey_trace", str(_path.SCRIPTS_DIR / "karvey-trace.py"))
tr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tr)

REQS = ("# Requirements\n\n### 1.1 REQ-X-001 — first\ntext\n\n### 1.2 REQ-X-002 — second\ntext\n\n"
        "### 1.3 REQ-X-003 — third\ntext\n")
TASKS = """# Tasks

### E1.F1.T1 [Test] Failing test for the first requirement

**Requirements:** REQ-X-001
**Tests added:** test_first.py

### E1.F1.T2 [Backend] Implement the first requirement — _Depends: E1.F1.T1_

**Requirements:** REQ-X-001
**Tests added:** none

### E1.F1.T3 [Backend] Implement the second requirement

**Requirements:** REQ-X-002
**Tests added:** none

### E1.F1.T4 [Backend] Documentation for the third requirement

**Requirements:** REQ-X-003
**Tests added:** none
manual: REQ-X-003 is checked by reading the rendered page
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"}})
        g.write(self.root, "docs/spec/changes/feat-a/spec.json", {"change_id": "feat-a", "phase": "impl"})
        g.write(self.root, "docs/spec/changes/feat-a/requirements.md", REQS)
        g.write(self.root, "docs/spec/changes/feat-a/tasks.md", TASKS)
        g.commit_all(self.root, "base")
        g.run(["tag", "base"], self.root)
        g.write(self.root, "tests/test_first.py", '"""@req REQ-X-001"""\ndef test_it():\n    pass\n')
        g.write(self.root, "tests/test_named.py", "def test_REQ_X_003_page():\n    pass\n")
        g.write(self.root, "tests/test_orphan.py", "def test_nothing():\n    pass\n")
        g.commit_all(self.root, "feat: E1.F1.T1 first\n\nKarvey-Change: feat-a")
        g.write(self.root, "src/x.py", "x\n")
        g.commit_all(self.root, "feat: unrelated\n\nKarvey-Change: other-change")

    def tearDown(self):
        self.t.cleanup()

    def model(self):
        res = tr.build(self.root, "feat-a", base="base")
        return res, {r["id"]: r for r in res["requirements"]}


class Trace(Base):
    def test_REQ_W2_057_uncovered_without_test_task_or_manual(self):
        res, by = self.model()
        self.assertEqual(res["uncovered"], ["REQ-X-002"])
        self.assertEqual(by["REQ-X-003"]["status"], "covered")  # manual: line
        self.assertTrue(by["REQ-X-003"]["manual"])

    def test_test_task_precedes_impl(self):
        _, by = self.model()
        self.assertEqual(by["REQ-X-001"]["test_tasks"], ["E1.F1.T1"])
        self.assertTrue(by["REQ-X-001"]["test_first"])

    def test_REQ_W2_058_tagged_and_named_tests_mapped(self):
        _, by = self.model()
        self.assertEqual(by["REQ-X-001"]["tests"], ["tests/test_first.py"])
        self.assertEqual(by["REQ-X-003"]["tests"], ["tests/test_named.py"])

    def test_REQ_W2_058_new_test_without_reference_is_unmapped(self):
        res, _ = self.model()
        self.assertEqual(res["unmapped_tests"], ["tests/test_orphan.py"])

    def test_REQ_W2_060_requirement_without_commit(self):
        res, by = self.model()
        self.assertEqual(len(by["REQ-X-001"]["commits"]), 1)  # cites E1.F1.T1, trailer feat-a
        self.assertEqual(by["REQ-X-002"]["commit_text"], "no commit")
        self.assertIn("REQ-X-002", res["no_commit"])

    def test_spec_delta_ids_included(self):
        g.write(self.root, "docs/spec/changes/feat-a/spec-delta.md",
                "## ADDED Requirements\n- **REQ-X-004** — new\n\n## REMOVED Requirements\n- **REQ-X-009** — gone\n")
        _, by = self.model()
        self.assertIn("REQ-X-004", by)
        self.assertNotIn("REQ-X-009", by)


if __name__ == "__main__":
    unittest.main()
