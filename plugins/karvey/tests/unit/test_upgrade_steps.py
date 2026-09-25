"""The initial step catalogue, step by step, on the anonymised legacy fixture (REQ-UP-015, 020..026)."""
import inspect
import json
import os
import shutil
import unittest
from pathlib import Path
from unittest import mock

import _gitrepo as g
import _path
from karvey_lib import atomicio, upgrade, upgrade_steps

FIXTURE = _path.FIXTURES_DIR / "upgrade" / "legacy-project"
FAKE_HOME = _path.FIXTURES_DIR / "upgrade" / "fake-home"
INSTALLED = "3.13.0"


class FixtureCase(unittest.TestCase):
    """A throw-away git copy of the legacy fixture, plus a copy of the fixture home."""

    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = self.t.path / "proj"
        shutil.copytree(str(FIXTURE), str(self.root))
        g.init(self.root, branch="dev")  # the fixture's integration branch
        g.commit_all(self.root, "fixture")
        self.home = self.t.path / "home"
        shutil.copytree(str(FAKE_HOME), str(self.home))
        self._env = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self.t.cleanup()

    def plan(self):
        return upgrade.plan(self.root, home=self.home, installed=INSTALLED)

    def row(self, sid, p=None):
        p = p or self.plan()
        return {r["id"]: r for r in p.rows()}[sid], p.results[sid]

    def apply(self, ids, **kw):
        kw.setdefault("installed", INSTALLED)
        kw.setdefault("home", self.home)
        rep = upgrade.apply(self.root, ids, dry_run=True, **kw)
        return upgrade.apply(self.root, ids, preview=rep.preview, confirm_no_preview=ids, **kw)

    def read(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def write(self, rel, content, commit=True):
        g.write(self.root, rel, content)
        if commit:
            g.commit_all(self.root)


SPEC60 = "docs/spec/changes/fixture-60/spec.json"
SPEC61 = "docs/spec/changes/archive/2026-01-10-fixture-61/spec.json"
PJ = "docs/spec/project.json"


class SchemaMigrate(FixtureCase):
    def test_exact_tier_migrates_and_keeps_the_format(self):
        row, res = self.row("schema-migrate")
        self.assertEqual(row["status"], "applies")
        paths = sorted(e.path for e in res.edits)
        self.assertEqual(paths, sorted([SPEC60, SPEC61, PJ]))
        for e in res.edits:
            before = atomicio.read_json(self.root / e.path)
            self.assertEqual(e.before_sha256, before.sha256)
            self.assertTrue(e.text.endswith("\n"))
            self.assertIn('\n  "', e.text, "two-space indent kept")
        rep = self.apply(["schema-migrate"])
        self.assertEqual(rep.applied, ["schema-migrate"])
        self.assertEqual(json.loads(self.read(PJ))["management"], {"tool": "markdown"})
        self.assertEqual(json.loads(self.read(SPEC60))["approvals"], {})
        self.assertEqual(self.row("schema-migrate")[0]["status"], "nothing", "a second plan no longer lists it")

    def test_an_unmappable_phase_is_left_for_a_human(self):
        self.write("docs/spec/changes/fixture-62/spec.json", {"change_id": "fixture-62", "phase": 42,
                                                              "approvals": None})
        row, res = self.row("schema-migrate")
        self.assertEqual(row["status"], "applies")
        self.assertNotIn("docs/spec/changes/fixture-62/spec.json", [e.path for e in res.edits])
        self.assertIn("1 file needs a human", row["summary"])
        self.assertTrue(any("fixture-62" in w and "unmappable" in w for w in row["warnings"]))
        self.apply(["schema-migrate"])
        self.assertIsNone(json.loads(self.read("docs/spec/changes/fixture-62/spec.json"))["approvals"])
        row, _ = self.row("schema-migrate")
        self.assertEqual(row["status"], "human")
        self.assertIn("1 file needs a human", row["summary"])

    def test_proposed_tier_only_with_its_own_id(self):
        self.write("docs/spec/changes/fixture-63/spec.json", {"change_id": "fixture-63", "phase": "implementing",
                                                              "approvals": {}})
        p = self.plan()
        self.assertNotIn("docs/spec/changes/fixture-63/spec.json",
                         [e.path for e in p.results["schema-migrate"].edits])
        prop = p.results["schema-migrate-proposed"]
        self.assertEqual([e.path for e in prop.edits], ["docs/spec/changes/fixture-63/spec.json"])
        self.apply(["schema-migrate"])
        self.assertEqual(json.loads(self.read("docs/spec/changes/fixture-63/spec.json"))["phase"], "implementing")
        self.apply(["schema-migrate-proposed"])
        self.assertEqual(json.loads(self.read("docs/spec/changes/fixture-63/spec.json"))["phase"], "impl")
        self.assertEqual(self.row("schema-migrate-proposed")[0]["status"], "nothing")

    def test_proposed_applies_only_for_what_the_proposed_tier_adds(self):
        row, _ = self.row("schema-migrate-proposed")
        self.assertEqual(row["status"], "nothing", "the fixture has nothing of the proposed tier")

    def test_the_state_tool_migration_is_imported_not_duplicated(self):
        src = inspect.getsource(upgrade_steps)
        self.assertNotIn("def fix_spec", src)
        self.assertNotIn("def fix_project", src)
        st = upgrade.state_module()
        with mock.patch.object(st, "fix_spec", wraps=st.fix_spec) as fs, \
                mock.patch.object(st, "fix_project", wraps=st.fix_project) as fp:
            self.row("schema-migrate")
        self.assertTrue(fs.called)
        self.assertTrue(fp.called)


if __name__ == "__main__":
    unittest.main()
