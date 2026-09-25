"""The initial step catalogue, step by step, on the anonymised legacy fixture (REQ-UP-015, 020..026)."""
import inspect
import json
import os
import shutil
import subprocess
import sys
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


SHIM = ".claude/hooks/plan-gate.sh"


class LegacyShims(FixtureCase):
    def dispatch_write(self):
        payload = {"session_id": "s", "cwd": str(self.root), "hook_event_name": "PreToolUse", "tool_name": "Write",
                   "tool_input": {"file_path": str(self.root / "src" / "a.py"), "content": "x"}}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        env.pop("KARVEY_COMPAT_MARKER", None)
        return subprocess.run(["bash", str(_path.PLUGIN_ROOT / "hooks" / "karvey-hook.sh"), "pre-edit"],
                              input=json.dumps(payload).encode(), cwd=str(self.root), env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)

    def test_identical_copy_is_replaced_by_the_flag(self):
        row, res = self.row("legacy-shims")
        self.assertEqual(row["status"], "applies")
        ops = sorted((e.op, e.path) for e in res.edits)
        self.assertEqual(ops, [("delete", SHIM), ("write", ".claude/settings.json"), ("write", PJ)])
        rep = self.apply(["legacy-shims"])
        self.assertEqual(rep.applied, ["legacy-shims"])
        self.assertFalse((self.root / SHIM).exists())
        self.assertEqual(json.loads(self.read(".claude/settings.json")), {}, "an empty hooks object drops the key")
        enf = json.loads(self.read(PJ))["enforcement"]
        self.assertEqual(enf, {"git_flow_hook": False, "plan_gate_hook": True})
        self.assertEqual(self.row("legacy-shims")[0]["status"], "nothing")

    def test_the_behaviour_is_kept_by_the_dispatcher(self):
        self.assertEqual(self.dispatch_write().returncode, 0, "before: only the copied shim gated, not the plugin")
        self.apply(["schema-migrate", "legacy-shims"])
        cp = self.dispatch_write()
        self.assertEqual(cp.returncode, 2, cp.stderr.decode())
        self.assertIn("plan-gate", cp.stderr.decode())

    def test_other_hook_entries_are_kept(self):
        data = json.loads(self.read(".claude/settings.json"))
        data["hooks"]["PreToolUse"][0]["hooks"].append({"type": "command", "command": "bash own-check.sh"})
        data["hooks"]["Stop"] = [{"hooks": [{"type": "command", "command": "bash done.sh"}]}]
        self.write(".claude/settings.json", data)
        self.apply(["legacy-shims"])
        left = json.loads(self.read(".claude/settings.json"))
        self.assertEqual(left["hooks"]["PreToolUse"][0]["hooks"], [{"type": "command", "command": "bash own-check.sh"}])
        self.assertIn("Stop", left["hooks"])

    def test_a_locally_edited_copy_is_left_for_a_human(self):
        self.write(SHIM, self.read(SHIM) + "# my change\n")
        row, res = self.row("legacy-shims")
        self.assertEqual(row["status"], "human")
        self.assertEqual(res.edits, [])
        self.assertIn("+# my change", res.diff)
        self.assertIn("shipped/plan-gate.sh", res.diff)
        rep = self.apply(["legacy-shims"])
        self.assertEqual((rep.applied, rep.shown), ([], ["legacy-shims"]))
        self.assertTrue((self.root / SHIM).exists())

    def test_known_hashes_cover_the_shipped_shims(self):
        steps = {s["id"]: s for s in upgrade.load_catalogue()}
        known = steps["legacy-shims"]["params"]["known_sha256"]
        for name in ("plan-gate.sh", "git-flow-guard.sh"):
            shipped = (_path.PLUGIN_ROOT / "skills" / "karvey" / "hooks" / name).read_bytes()
            self.assertIn(atomicio.sha256_bytes(shipped), known[name])

    @unittest.skipIf(os.environ.get("KARVEY_SKIP_TABLES") == "1", "KARVEY_SKIP_TABLES=1")
    def test_the_guard_tables_still_pass(self):
        self.apply(["legacy-shims"])
        cp = subprocess.run([sys.executable, str(_path.TESTS_DIR / "hooks" / "run_tables.py"), "--only", "plan-gate",
                             "--only", "git-flow"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        self.assertEqual(cp.returncode, 0, cp.stdout.decode()[-2000:])


if __name__ == "__main__":
    unittest.main()
