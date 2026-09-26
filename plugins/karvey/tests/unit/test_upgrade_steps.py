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
        self.assertEqual(paths, sorted([SPEC60, PJ]))  # archive: history (F-22)
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


class TeamSettings(FixtureCase):
    def check(self, sid):
        steps = {s["id"]: s for s in upgrade.load_catalogue()}
        return upgrade.run_check(steps[sid], upgrade.Probe(self.root, home=self.home, installed=INSTALLED))

    def test_missing_notifications_previewed_from_propose_settings(self):
        cfg = upgrade.config_module()
        with mock.patch.object(cfg, "propose_settings", wraps=cfg.propose_settings) as ps:
            row, res = self.row("team-settings")
        self.assertTrue(ps.called)
        self.assertEqual(ps.call_args.kwargs.get("from_legacy"), True)
        self.assertEqual(row["status"], "applies")
        self.assertIn("notifications", row["summary"])
        new = json.loads(res.edits[0].text)
        self.assertEqual(new["notifications"]["channel"], "none")
        rep = self.apply(["schema-migrate", "team-settings"])
        self.assertEqual(rep.applied, ["schema-migrate", "team-settings"])
        self.assertEqual(self.row("team-settings")[0]["status"], "nothing")

    def test_a_placeholder_is_needs_input_and_apply_refuses_without_values(self):
        data = json.loads(self.read(PJ))
        data["management"] = "clickup"
        self.write(PJ, data)
        res = self.check("team-settings")
        self.assertEqual(res.status, "needs-input")
        self.assertEqual(res.inputs_needed, ["management.location"])
        with self.assertRaises(upgrade.Refused) as cm:
            self.apply(["team-settings"])
        self.assertIn("management.location", str(cm.exception))
        rep = self.apply(["team-settings"], inputs={"team-settings": {"management.location": "901234"}})
        self.assertEqual(rep.applied, ["team-settings"])
        self.assertEqual(json.loads(self.read(PJ))["management"]["location"], "901234")

    def test_values_go_through_safe_values(self):
        bad = [{"notifications.channel": "slack", "notifications.target": "https://hooks.example/x"},
               {"notifications.channel": "slack", "notifications.target": "#a; rm -rf ~"},
               {"notifications.channel": "carrier-pigeon"},
               {"management.tool": "markdown", "management.location": "../outside.md"},
               {"project": "x"}]
        for vals in bad:
            with self.subTest(values=vals):
                with self.assertRaises(upgrade.Refused) as cm:
                    self.apply(["team-settings"], inputs={"team-settings": vals})
                self.assertIn("value refused", str(cm.exception))
        rep = self.apply(["team-settings"], inputs={"team-settings": {"notifications.channel": "slack",
                                                                      "notifications.target": "#team-dev"}})
        self.assertEqual(rep.applied, ["team-settings"])
        self.assertEqual(json.loads(self.read(PJ))["notifications"]["target"], "#team-dev")

    def test_enforcement_defaults_lists_undeclared_keys_only(self):
        row, res = self.row("enforcement-defaults")
        self.assertEqual(row["status"], "applies")
        self.assertIn("enforcement.prod_gate_hook = true", row["summary"])
        self.assertIn("enforcement.plan_marker_ttl_min = 120", row["summary"])
        self.assertNotIn("git_flow_hook", row["summary"], "an explicit value is never listed")
        data = json.loads(self.read(PJ))
        data["enforcement"] = {"prod_gate_hook": False, "plan_marker_ttl_min": 30}
        self.write(PJ, data)
        row, _ = self.row("enforcement-defaults")
        self.assertEqual(row["status"], "nothing", "explicit non-default values are kept")

    def test_no_standards_block_names_the_standards_skill(self):
        row, _ = self.row("enforcement-defaults")
        self.assertTrue(any("/karvey:karvey-standards" in w for w in row["warnings"]))
        data = json.loads(self.read(PJ))
        data["standards"] = {"backend": "docs/spec/standards/backend.md"}
        self.write(PJ, data)
        self.assertEqual(self.row("enforcement-defaults")[0]["warnings"], [])

    def test_no_project_json_is_handed_to_init_settings(self):
        (self.root / PJ).unlink()
        g.commit_all(self.root)
        for sid in ("team-settings", "enforcement-defaults"):
            with self.subTest(step=sid):
                row, _ = self.row(sid)
                self.assertEqual(row["status"], "needs-input")
                self.assertIn("/karvey:karvey-init --settings", row["summary"])
                with self.assertRaises(upgrade.Refused):
                    self.apply([sid], inputs={sid: {"x": "y"}})


def home_digest(home):
    import hashlib
    h = hashlib.sha256()
    for p in sorted(Path(home).rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(home)).encode() + p.read_bytes())
    return h.hexdigest()


class HumanSteps(FixtureCase):
    def home_settings(self, data):
        (self.home / ".claude" / "settings.json").write_text(
            data if isinstance(data, str) else json.dumps(data, indent=2), encoding="utf-8")

    def test_versioned_statusline_gets_the_stable_command(self):
        row, res = self.row("statusline-launcher")
        self.assertEqual((row["status"], row["human"]), ("human", True))
        self.assertIn(json.dumps(upgrade_steps.STABLE_STATUSLINE)[1:-1], res.instructions)
        self.assertIn("/karvey/3.11.2/hooks/karvey-statusline.sh", res.diff)
        self.assertEqual(res.edits, [])

    def test_no_statusline_is_a_note_not_work(self):
        self.home_settings({})
        row, _ = self.row("statusline-launcher")
        self.assertEqual(row["status"], "nothing")  # REQ-UP-023 as revised by F-21

    def test_own_statusline_is_left_as_is(self):
        self.home_settings({"statusLine": {"type": "command", "command": "bash ~/bin/my-status.sh"}})
        row, _ = self.row("statusline-launcher")
        self.assertEqual(row["status"], "nothing")
        self.assertIn("own statusline, left as is", row["warnings"])

    def test_the_stable_command_passes(self):
        self.home_settings({"statusLine": dict(upgrade_steps.STATUSLINE_BLOCK)})
        self.assertEqual(self.row("statusline-launcher")[0]["status"], "nothing")

    def test_global_config_diff_of_karvey_keys_only(self):
        self.home_settings({"env": {"OTHER_SECRET": "do-not-print", "KARVEY_ROTATE_HOURS": "8"},
                            "permissions": {"allow": ["Bash(ls)"]},
                            "hooks": {"PreToolUse": [{"hooks": [
                                {"type": "command", "command": "bash ~/.claude/hooks/check-plan-approved.sh"},
                                {"type": "command",
                                 "command": "bash ~/.claude/plugins/cache/m/karvey/3.11.2/skills/karvey/hooks/"
                                            "git-flow-guard.sh"}]}]}})
        row, res = self.row("global-config")
        self.assertEqual(row["status"], "human")
        self.assertIn('+    "KARVEY_COMPAT_MARKER"', res.diff)
        self.assertIn("-    \"PreToolUse: bash ~/.claude/plugins/cache/m/karvey/3.11.2", res.diff)
        self.assertNotIn("OTHER_SECRET", res.diff)
        self.assertNotIn("do-not-print", res.diff)
        self.assertNotIn("permissions", res.diff)
        self.assertNotIn("check-plan-approved", res.diff, "the person's own hook is not a Karvey key")

    def test_global_config_claude_md_line(self):
        (self.home / ".claude" / "CLAUDE.md").write_text("| team | spaces/AAAAexample |\n", encoding="utf-8")
        row, res = self.row("global-config")
        self.assertEqual(row["status"], "human")
        self.assertIn("+Karvey reads notification destinations only from", res.diff)

    def test_global_config_nothing_on_a_clean_home(self):
        self.assertEqual(self.row("global-config")[0]["status"], "nothing")

    def test_unreadable_home_is_check_failed_the_rest_computed(self):
        self.home_settings("{not json")
        p = self.plan()
        by = {r["id"]: r for r in p.rows()}
        for sid in ("statusline-launcher", "global-config"):
            self.assertEqual(by[sid]["status"], "check-failed")
            self.assertIn("check-failed: unreadable", by[sid]["summary"])
        self.assertEqual(by["schema-migrate"]["status"], "applies")
        self.assertEqual(p.exit, 1)

    def test_the_home_is_byte_identical_after_plan_and_apply(self):
        before = home_digest(self.home)
        self.plan()
        rep = self.apply(["statusline-launcher", "schema-migrate"])
        self.assertEqual(rep.applied, ["schema-migrate"])
        self.assertIn("statusline-launcher", rep.shown)
        self.assertEqual(home_digest(self.home), before)


class ChangesInFlight(FixtureCase):
    def test_the_impl_change_is_listed_the_archived_one_is_not(self):
        row, res = self.row("changes-in-flight")
        self.assertEqual((row["status"], row["report_only"]), ("report", True))
        self.assertIn("fixture-60 (phase impl)", res.instructions)
        self.assertIn("tasks", res.instructions.split("fixture-60", 1)[1].splitlines()[0])
        self.assertNotIn("fixture-61", res.instructions)
        self.assertNotIn("archive", res.instructions)

    def test_apply_writes_nothing(self):
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        rep = self.apply(["changes-in-flight"])
        self.assertEqual((rep.applied, rep.shown), ([], ["changes-in-flight"]))
        self.assertIn("fixture-60", rep.text())
        after = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(after, before)

    def test_a_change_with_its_gates_met_is_not_listed(self):
        (self.root / SPEC60).unlink()
        g.commit_all(self.root)
        self.assertEqual(self.row("changes-in-flight")[0]["status"], "nothing")



class RegressionProjectUpgradeQA(FixtureCase):
    """regression_project-upgrade_qa_* (QA 2026-09-25, F-11..F-19): each test reproduces a reviewer's case."""
    UB = "chore/karvey-upgrade-" + INSTALLED

    def git(self, *args, cwd=None):
        return subprocess.run(["git"] + list(args), cwd=str(cwd or self.root), capture_output=True, text=True)

    def commit(self):
        return upgrade.commit(self.root, "The Owner", installed=INSTALLED)

    def test_f11_nested_worktree_is_never_touched(self):
        self.write(".gitignore", ".claude/worktrees/\n")
        wt = self.root / ".claude" / "worktrees" / "w1"
        self.assertEqual(self.git("worktree", "add", "-q", str(wt), "-b", "other").returncode, 0)
        row, res = self.row("legacy-shims")
        self.assertNotIn("worktrees", row["summary"])
        self.assertTrue(all("worktrees" not in e.path for e in res.edits))
        self.apply(["legacy-shims"])
        self.assertTrue((wt / SHIM).exists())
        self.assertEqual(self.git("status", "--porcelain", cwd=wt).stdout, "")
        self.assertTrue(self.commit()["sha"])

    def test_f12_ignored_local_settings_are_shown_not_written(self):
        self.write(".gitignore", ".claude/settings.local.json\n")
        local = json.loads(self.read(".claude/settings.json"))
        self.write(".claude/settings.local.json", local, commit=False)
        before = self.read(".claude/settings.local.json")
        row, res = self.row("legacy-shims")
        self.assertTrue(all(e.path != ".claude/settings.local.json" for e in res.edits))
        self.assertTrue(any("git-ignored" in w for w in row["warnings"]))
        self.apply(["legacy-shims"])
        self.assertEqual(self.read(".claude/settings.local.json"), before)
        self.assertTrue(self.commit()["sha"])

    def test_f13_second_commit_after_a_deletion(self):
        self.apply(["legacy-shims"])
        self.commit()
        self.apply(["enforcement-defaults"])
        res = self.commit()
        msg = self.git("log", "-1", "--format=%B").stdout
        self.assertIn("Steps: enforcement-defaults\n", msg)
        self.assertEqual(res["steps"], ["enforcement-defaults"])

    def test_f13_a_new_upgrade_branch_starts_a_new_journal(self):
        self.apply(["legacy-shims"])
        self.commit()
        self.git("checkout", "-q", "dev")
        self.git("merge", "-q", "--no-ff", "-m", "merge", self.UB)
        self.git("branch", "-q", "-D", self.UB)
        self.apply(["enforcement-defaults"])
        self.assertEqual(self.commit()["steps"], ["enforcement-defaults"])

    def test_f14_the_flag_is_written_first_and_a_dangling_entry_is_work(self):
        _, res = self.row("legacy-shims")
        self.assertEqual((res.edits[0].op, res.edits[0].path), ("write", PJ))
        self.assertEqual(res.edits[-1].op, "delete")
        (self.root / SHIM).unlink()  # a half-applied run, or a copy deleted by hand: the entry still runs it
        g.commit_all(self.root)
        row, res = self.row("legacy-shims")
        self.assertEqual(row["status"], "applies")
        self.apply(["legacy-shims"])
        self.assertNotIn("plan-gate", self.read(".claude/settings.json"))
        self.assertTrue(json.loads(self.read(PJ))["enforcement"]["plan_gate_hook"])

    def test_f15_bad_journal_shape_and_unwritable_journal(self):
        d = self.root / ".git" / "karvey"
        d.mkdir(parents=True, exist_ok=True)
        (d / upgrade.JOURNAL_NAME).write_text(json.dumps({"v": 1, "branch": self.UB, "files": []}))
        self.assertEqual(upgrade.read_journal(self.root)["applied"], [])  # missing lists default, no KeyError
        (d / upgrade.JOURNAL_NAME).write_text(json.dumps({"v": 1, "branch": self.UB, "files": [["a"]]}))
        self.assertIsNone(upgrade.read_journal(self.root))
        (d / upgrade.JOURNAL_NAME).unlink()
        (d / upgrade.JOURNAL_NAME).mkdir()
        before = self.read(PJ)
        with self.assertRaises(upgrade.Refused) as cm:
            self.apply(["enforcement-defaults"])
        self.assertIn("journal", str(cm.exception))
        self.assertEqual(self.read(PJ), before)

    def test_f16_value_types_and_keys(self):
        for vals in ({"notifications.channel": ["slack"]}, {"notifications.webhook": "x"},
                     {"notifications.channel": 3}):
            with self.subTest(vals=vals):
                with self.assertRaises(upgrade.Refused):
                    upgrade.apply(self.root, ["team-settings"], dry_run=True, installed=INSTALLED, home=self.home,
                                  inputs={"team-settings": vals})

    def test_f17_a_refusal_leaves_the_branch_as_it_was(self):
        self.assertEqual(self.row("schema-migrate-proposed")[0]["status"], "nothing")
        with self.assertRaises(upgrade.Refused):
            upgrade.apply(self.root, ["legacy-shims", "schema-migrate-proposed"], preview="x", installed=INSTALLED,
                          home=self.home)
        with self.assertRaises(upgrade.Refused):
            upgrade.apply(self.root, ["legacy-shims"], preview="stale", installed=INSTALLED, home=self.home)
        rep = upgrade.apply(self.root, ["changes-in-flight"], installed=INSTALLED, home=self.home)
        self.assertEqual(rep.shown, ["changes-in-flight"])
        self.assertEqual(self.git("symbolic-ref", "--short", "HEAD").stdout.strip(), "dev")
        self.assertEqual(self.git("branch", "--list", "chore/*").stdout, "")

    def test_f18_the_current_phase_awaiting_its_approval_is_not_unmet(self):
        spec = {"schema_version": 1, "change_id": "fixture-60", "phase": "requirements", "management": "markdown",
                "goal": "x", "approvals": {}, "phase_history": [
                    {"phase": "init", "entered_at": "2026-09-01T10:00:00+00:00",
                     "exited_at": "2026-09-01T11:00:00+00:00"},
                    {"phase": "requirements", "entered_at": "2026-09-01T11:00:00+00:00"}]}
        self.write(SPEC60, spec)
        self.assertEqual(self.row("changes-in-flight")[0]["status"], "nothing")

    def test_f19_an_own_hook_with_a_similar_name_is_kept(self):
        data = json.loads(self.read(".claude/settings.json"))
        own = {"type": "command", "command": "bash ~/.claude/hooks/my-plan-gate.sh.v2"}
        data["hooks"]["PreToolUse"][0]["hooks"].append(own)
        self.write(".claude/settings.json", data)
        self.apply(["legacy-shims"])
        self.assertEqual(json.loads(self.read(".claude/settings.json"))["hooks"]["PreToolUse"][0]["hooks"], [own])

    def test_git_read_refuses_writing_options(self):
        p = upgrade.Probe(self.root, home=self.home, installed=INSTALLED)
        for bad in (("show", "--output=x", "HEAD"), ("ls-files", "--output=x")):
            with self.subTest(args=bad), self.assertRaises(upgrade.ProbeError):
                p.git_read(*bad)


class RegressionProjectUpgradeIterate(FixtureCase):
    """regression_project-upgrade_iterate_* (karvey-iterate 2026-09-26): the spec revisions of F-08, F-21..F-25
    and the emergent F-28, each reproduced on the legacy fixture."""
    UB = "chore/karvey-upgrade-" + INSTALLED

    def git(self, *args, cwd=None):
        return subprocess.run(["git"] + list(args), cwd=str(cwd or self.root), capture_output=True, text=True)

    def test_f21_no_statusline_is_not_work_only_a_note(self):
        (self.home / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
        row, res = self.row("statusline-launcher")
        self.assertEqual(row["status"], "nothing")
        self.assertTrue(any(w.startswith("no statusline") for w in row["warnings"]), row["warnings"])
        # every other step satisfied + no statusline = an empty plan (REQ-UP-005 reachable)
        self.assertEqual(upgrade.any_applicable(self.root, 1e18, steps=[s for s in upgrade.load_catalogue()
                                                                    if s["id"] == "statusline-launcher"],
                                                home=self.home), "none")

    def test_f22_archived_changes_are_never_migrated(self):
        before = self.read(SPEC61)
        row, res = self.row("schema-migrate")
        self.assertNotIn(SPEC61, [e.path for e in res.edits])
        self.assertNotIn("archive/", row["summary"])
        self.apply(["schema-migrate"])
        self.assertEqual(self.read(SPEC61), before, "archived history is never rewritten (D-14)")

    def test_f23_the_init_enforcement_block_declares_every_default(self):
        import re
        text = (_path.PLUGIN_ROOT / "skills" / "karvey-init" / "SKILL.md").read_text(encoding="utf-8")
        m = re.search(r'^"enforcement": (\{.*\})$', text, re.M)
        self.assertIsNotNone(m, "karvey-init shows the enforcement block it writes")
        block = json.loads(m.group(1))
        schema = json.loads((_path.PLUGIN_ROOT / "schemas" / "project.schema.json").read_text(encoding="utf-8"))
        props = schema["properties"]["enforcement"]["properties"]
        defaults = {k for k, v in props.items() if "x-karvey-default" in v}
        self.assertLessEqual(defaults, set(block), "init declares every enforcement default")
        data = json.loads(self.read(PJ))
        data["enforcement"] = block
        data["standards"] = {}
        self.write(PJ, data)
        self.assertEqual(self.row("enforcement-defaults")[0]["status"], "nothing")

    def test_f24_a_dry_run_off_the_upgrade_branch_must_preview_its_base(self):
        g.with_origin(self.root, "dev")
        self.write("local.txt", "a local commit origin/dev does not have\n")
        with self.assertRaises(upgrade.Refused) as cm:
            upgrade.apply(self.root, ["enforcement-defaults"], dry_run=True, installed=INSTALLED, home=self.home)
        self.assertIn("branch", str(cm.exception))
        upgrade.ensure_branch(self.root, INSTALLED)
        rep = self.apply(["enforcement-defaults"])
        self.assertEqual(rep.applied, ["enforcement-defaults"])

    def test_f08_a_second_clone_builds_on_the_remote_upgrade_branch(self):
        bare = g.with_origin(self.root, "dev")
        self.apply(["legacy-shims"])
        upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        self.assertEqual(self.git("push", "-q", "origin", self.UB).returncode, 0)
        other = self.t.path / "other"
        self.assertEqual(subprocess.run(["git", "clone", "-q", "-b", "dev", str(bare), str(other)],
                                        capture_output=True).returncode, 0)
        res = upgrade.ensure_branch(other, INSTALLED)
        self.assertEqual((res["base"], res["created"]), ("refs/remotes/origin/" + self.UB, True))
        self.assertTrue(res.get("remote"), res)
        p = upgrade.plan(other, home=self.home, installed=INSTALLED)
        self.assertEqual({r["id"]: r["status"] for r in p.rows()}["legacy-shims"], "nothing")
        rep = upgrade.apply(other, ["enforcement-defaults"], dry_run=True, installed=INSTALLED, home=self.home)
        upgrade.apply(other, ["enforcement-defaults"], preview=rep.preview, installed=INSTALLED, home=self.home)
        upgrade.commit(other, "Someone Else", installed=INSTALLED)
        push = self.git("push", "-q", "origin", self.UB, cwd=other)
        self.assertEqual(push.returncode, 0, "a fast-forward of the first clone's branch: " + push.stderr)

    def test_f25_project_reads_are_capped_and_the_walk_honours_the_deadline(self):
        big = "docs/spec/changes/big/spec.json"
        self.write(big, '{"x": "%s"}\n' % ("a" * (upgrade.PROJECT_READ_MAX + 1)), commit=False)
        p = upgrade.Probe(self.root, home=self.home, installed=INSTALLED)
        with self.assertRaises(upgrade.CheckFailed) as cm:
            p.read_text(big)
        self.assertIn("larger than", str(cm.exception))
        late = upgrade.Probe(self.root, home=self.home, installed=INSTALLED, deadline=0.0)
        with self.assertRaises(upgrade.DeadlineExceeded):
            late.glob("docs/spec/**/spec.json")
        (self.root / "node_modules" / "deep").mkdir(parents=True)
        with mock.patch("os.scandir", wraps=os.scandir) as sc:
            p.glob("docs/spec/**/spec.json")
        walked = [str(c.args[0]) for c in sc.call_args_list if c.args]
        self.assertFalse(any("node_modules" in w for w in walked), "pruned, not filtered")
        self.assertTrue(all(w.startswith(str(self.root / "docs" / "spec")) for w in walked), walked[:3])

    def test_f28_project_strings_cannot_add_lines_to_the_plan(self):
        evil = "docs/spec/changes/evil\n| injected | x | yes | low | no |/spec.json"
        self.write(evil, self.read(SPEC60))
        p = self.plan()
        for line in p.table().splitlines():
            self.assertFalse(line.lstrip("|/ ").startswith("injected"), line)
        for r in p.rows():
            self.assertNotIn("\n", r["summary"])
            self.assertTrue(all("\n" not in w for w in r["warnings"]))
        rep = upgrade.apply(self.root, ["changes-in-flight"], installed=INSTALLED, home=self.home)
        self.assertFalse(any(ln.startswith("| injected") for x in rep.lines for ln in x.splitlines()), rep.lines)


if __name__ == "__main__":
    unittest.main()
