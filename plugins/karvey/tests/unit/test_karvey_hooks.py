"""karvey_hooks: the guard registry, the dispatch contract and the time budgets (E1.F4.T3)."""
import io
import json
import unittest

import _path
from karvey_lib import karvey_hooks as kh

PAYLOADS = _path.FIXTURES_DIR / "payloads"


def run(event, payload, env=None, **kw):
    out, err = io.StringIO(), io.StringIO()
    text = payload if isinstance(payload, str) else json.dumps(payload)
    env = dict(env or {})
    env.setdefault("CLAUDE_PROJECT_DIR", "/nonexistent-karvey-unit")  # never the repo under test
    code = kh.dispatch(event, text, env=env, out=out, err=err, **kw)
    return code, out.getvalue(), err.getvalue()


class Registry(unittest.TestCase):
    def test_order_and_fail_modes_of_section_1_3(self):
        names = lambda ev: [g.name for g in kh.guards_for(ev) if g.name != "selftest"]  # noqa: E731
        self.assertEqual(names("pre-bash"), ["protect-paths", "prod-gate", "git-flow", "plan-gate"])
        self.assertEqual(names("pre-edit"), ["protect-paths", "plan-gate"])
        self.assertEqual(names("post-edit"), ["spec-write", "pending-sync"])
        self.assertEqual(names("prompt"), ["approval"])
        fail = {g.name: g.fail for g in kh.REGISTRY}
        self.assertEqual(fail, {"selftest": "closed", "protect-paths": "closed", "prod-gate": "closed",
                                "git-flow": "closed", "plan-gate": "closed", "spec-write": "open",
                                "pending-sync": "open", "approval": "open"})
        default = {g.name: g.default_on for g in kh.REGISTRY}
        self.assertTrue(default["prod-gate"])        # D-02
        self.assertFalse(default["git-flow"])        # opt-in
        self.assertFalse(default["plan-gate"])       # opt-in

    def test_wired_guards(self):
        self.assertEqual([g.name for g in kh.REGISTRY if g.wired], ["selftest", "protect-paths", "prod-gate", "git-flow", "plan-gate", "spec-write", "pending-sync", "approval"])

    def test_only_filter(self):
        self.assertEqual([g.name for g in kh.guards_for("pre-bash", ["git-flow"])], ["git-flow"])

    def test_budget_below_every_hooks_json_timeout(self):
        hooks = json.loads((_path.PLUGIN_ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        seen = set()
        for groups in hooks.values():
            for g in groups:
                for h in g["hooks"]:
                    cmd = h["command"]
                    self.assertIn('"${CLAUDE_PLUGIN_ROOT}', cmd)  # BUG-18: double quotes
                    if "karvey-hook.sh" in cmd:
                        ev = cmd.rsplit(" ", 1)[-1]
                        seen.add(ev)
                        self.assertLess(kh.BUDGET_S[ev], h["timeout"], ev)
        self.assertEqual(seen, {"prompt", "pre-bash", "pre-edit", "post-edit"})


class Dispatch(unittest.TestCase):
    def test_every_captured_payload_is_allowed_silently(self):
        events = {"pre-tool-use-bash.json": "pre-bash", "pre-tool-use-write.json": "pre-edit",
                  "pre-tool-use-edit.json": "pre-edit", "post-tool-use-write.json": "post-edit",
                  "post-tool-use-edit.json": "post-edit", "user-prompt-submit.json": "prompt"}
        for name, ev in events.items():
            code, out, err = run(ev, (PAYLOADS / name).read_text())
            self.assertEqual((code, out, err), (0, "", ""), name)

    def test_selftest_blocks_only_when_enabled(self):
        p = {"tool_name": "Bash", "tool_input": {"command": "echo KARVEY-SELFTEST-BLOCK"}, "cwd": "/nonexistent"}
        self.assertEqual(run("pre-bash", p)[0], 0)
        code, out, err = run("pre-bash", p, env={"KARVEY_HOOK_SELFTEST": "1"})
        self.assertEqual(code, 2)
        self.assertIn("[karvey] BLOCK selftest", err)
        code, _, err = run("pre-edit", {"tool_name": "Write", "tool_input": {"file_path": "KARVEY-SELFTEST-BLOCK"},
                                        "cwd": "/nonexistent"}, env={"KARVEY_HOOK_SELFTEST": "1"})
        self.assertEqual(code, 2)

    def test_unparsable_payload_applies_the_closed_fail_mode(self):
        code, _, err = run("pre-bash", "not json", env={"KARVEY_HOOK_SELFTEST": "1"})
        self.assertEqual(code, 2)
        self.assertIn("cannot evaluate", err)
        code, _, err = run("pre-bash", "not json")  # protect-paths is always on and fails closed
        self.assertEqual(code, 2)
        self.assertIn("BLOCK protect-paths: cannot evaluate", err)

    def test_guard_exception_fail_modes(self):
        boom = kh.Guard("boom-closed", ("pre-bash",), "closed", True, wired=True,
                        run=lambda ctx: 1 / 0)
        soft = kh.Guard("boom-open", ("post-edit",), "open", True, wired=True, run=lambda ctx: 1 / 0)
        kh.REGISTRY.extend([boom, soft])
        try:
            code, _, err = run("pre-bash", {"tool_name": "Bash", "tool_input": {"command": "ls"}})
            self.assertEqual(code, 2)
            self.assertIn("BLOCK boom-closed: cannot evaluate: ZeroDivisionError", err)
            code, _, err = run("post-edit", {"tool_name": "Write", "tool_input": {"file_path": "/x"}})
            self.assertEqual(code, 0)
            self.assertIn("boom-open not evaluated", err)
        finally:
            kh.REGISTRY.remove(boom)
            kh.REGISTRY.remove(soft)

    def test_main_unknown_event_and_session_are_not_blocking(self):
        self.assertEqual(kh.main(["nosuch"]), 0)
        import os
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": d}):
            # never the repository under test: the startup offer may write its seen record there
            self.assertEqual(kh.main(["session", "startup"]), 0)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------- the project-upgrade offer (REQ-UP-002..006)
import os  # noqa: E402
import shutil  # noqa: E402
from unittest import mock  # noqa: E402

import _gitrepo as g  # noqa: E402
import karvey_lib  # noqa: E402
from karvey_lib import upgrade, upgrade_steps  # noqa: E402

CLEAN_PROJECT = {
    "git_platform": "github", "repos": ["repo-a"], "spec_repo": "repo-a",
    "branch_flow": {"feature_prefix": "feature/", "integration": "main", "production": "main"},
    "enforcement": {"prod_gate_hook": True, "plan_marker_ttl_min": 120},
    "notifications": {"channel": "none", "target": "", "via": "", "events": []},
    "management": {"tool": "markdown", "location": "docs/spec/changes/{change-id}/PLAN.md"},
    "standards": {},
}


class UpgradeOffer(unittest.TestCase):
    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.home = self.t.path / "home"
        g.write(self.home, ".claude/settings.json", {"statusLine": dict(upgrade_steps.STATUSLINE_BLOCK)})
        self._env = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        self._env.start()
        self.clean = g.init(self.t.path / "clean")
        g.write(self.clean, "docs/spec/project.json", CLEAN_PROJECT)
        g.commit_all(self.clean)
        self.legacy = self.t.path / "legacy"
        shutil.copytree(str(_path.FIXTURES_DIR / "upgrade" / "legacy-project"), str(self.legacy))
        g.init(self.legacy, branch="dev")
        g.commit_all(self.legacy)

    def tearDown(self):
        self._env.stop()
        self.t.cleanup()

    def offer(self, root, mode="startup", env=None):
        return kh.upgrade_offer(str(root), None, mode, env or {})

    def test_only_on_startup(self):
        for mode in ("resume", "compact", "clear"):
            self.assertEqual(self.offer(self.legacy, mode), [])
        self.assertIsNone(upgrade.read_seen(self.legacy))

    def test_silent_outside_a_karvey_project_no_record(self):
        plain = g.init(self.t.path / "plain")
        g.write(plain, "docs/spec/openapi.yaml", "x: 1\n")
        self.assertEqual(self.offer(plain), [])
        self.assertFalse((plain / ".git" / "karvey").exists())

    def test_silent_when_the_version_was_resolved(self):
        upgrade.write_seen(self.legacy, karvey_lib.__version__, "declined")
        self.assertEqual(self.offer(self.legacy), [])

    def test_nothing_applies_records_empty_and_stays_silent(self):
        self.assertEqual(self.offer(self.clean), [])
        rec = upgrade.read_seen(self.clean)
        self.assertEqual((rec["resolution"], rec["version"]), ("empty", karvey_lib.__version__))

    def test_found_gives_two_bounded_lines(self):
        lines = self.offer(self.legacy)
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertLessEqual(len(line), 300)
        self.assertIn("no upgrade resolved yet in this clone", lines[0])
        self.assertIn("→ %s: do you want a plan" % karvey_lib.__version__, lines[1])
        self.assertIn("/karvey:karvey-upgrade", lines[1])
        self.assertIn("Not for this version", lines[1])
        self.assertIsNone(upgrade.read_seen(self.legacy), "an unanswered offer records nothing")
        upgrade.write_seen(self.legacy, "3.0.0", "declined")
        lines = self.offer(self.legacy)
        self.assertIn("last resolved in this clone 3.0.0", lines[0])
        self.assertIn('"Karvey 3.0.0 → %s' % karvey_lib.__version__, lines[1])

    def test_the_plugin_path_is_shell_quoted(self):
        with mock.patch.object(kh, "kl_plugin_root", return_value="/opt/a b/karvey"):
            lines = self.offer(self.legacy)
        self.assertIn("python3 '/opt/a b/karvey/scripts/karvey-upgrade.py' seen --decline", lines[0])

    def test_timeout_and_a_raising_check_offer(self):
        lines = self.offer(self.clean, env={kh.UPGRADE_PROBE_ENV: "0"})
        self.assertEqual(len(lines), 2)
        self.assertIsNone(upgrade.read_seen(self.clean), "a timeout records nothing")
        with mock.patch.object(upgrade, "any_applicable", return_value="failed"):
            self.assertEqual(len(self.offer(self.clean)), 2)

    def test_the_test_override_can_only_lower_the_budget(self):
        seen = {}

        def spy(root, deadline, **kw):
            seen["left"] = deadline - __import__("time").monotonic()
            return "found"
        with mock.patch.object(upgrade, "any_applicable", side_effect=spy):
            self.offer(self.clean, env={kh.UPGRADE_PROBE_ENV: "999999"})
        self.assertLessEqual(seen["left"], 1.5)

    def test_bad_catalogue_or_version_is_one_line_record_unchanged(self):
        bad = self.t.path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        with mock.patch.object(upgrade, "CATALOGUE_PATH", bad):
            lines = self.offer(self.clean)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("[karvey] upgrade offer unavailable: "))
        self.assertIsNone(upgrade.read_seen(self.clean))
        with mock.patch.object(karvey_lib, "__version__", "3.13"):
            lines = self.offer(self.clean)
        self.assertEqual(len(lines), 1)
        self.assertIn("not a release number", lines[0])
        self.assertIsNone(upgrade.read_seen(self.clean))

    def test_any_exception_is_one_line_and_the_session_text_is_still_produced(self):
        with mock.patch.object(upgrade, "read_seen", side_effect=RuntimeError("boom")):
            self.assertEqual(self.offer(self.legacy), ["[karvey] upgrade offer unavailable: RuntimeError: boom"])
            text = kh.session_text("startup", {"CLAUDE_PROJECT_DIR": str(self.legacy)})
        self.assertIn("team settings not set", text)
        self.assertIn("upgrade offer unavailable: RuntimeError: boom", text)

    def test_f09_the_offer_reads_as_the_plugins_own_notice(self):
        """regression_project-upgrade_iterate_offer_wording (F-09): phrased like the settings notice (what the
        user can do), not as an imperative order naming a command, which a model may take for an injection."""
        lines = self.offer(self.legacy)
        text = " ".join(lines)
        self.assertNotIn("Ask ONE", text)
        self.assertNotIn("the decline command above", text)
        self.assertTrue(lines[0].startswith("Karvey (upgrade): "), "signed like the settings notice")
        self.assertIn("the user can decline", lines[0])
        self.assertTrue(lines[1].startswith("The user can get an upgrade plan"), lines[1])
        self.assertIn("do you want a plan to upgrade this project?", lines[1])
        self.assertIn("Not for this version", lines[1])

    def test_f25_a_stuck_probe_is_cut_by_the_watchdog(self):
        import time as _t

        def stuck(root, deadline, **kw):
            _t.sleep(3)
            return "none"
        t0 = _t.monotonic()
        with mock.patch.object(upgrade, "any_applicable", side_effect=stuck):
            lines = self.offer(self.clean, env={kh.UPGRADE_PROBE_ENV: "100"})
        self.assertLess(_t.monotonic() - t0, 1.5, "the hook does not wait for a stuck check")
        self.assertEqual(len(lines), 2, "cut by the watchdog = a timeout: the offer is shown")
        self.assertIsNone(upgrade.read_seen(self.clean), "nothing recorded")

    def test_f27_a_karvey_project_outside_git_gets_no_offer_and_no_record(self):
        plain = self.t.path / "nogit"
        g.write(plain, "docs/spec/project.json", {"a": 1})
        state = self.t.path / "xdg"
        with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(state)}):
            self.assertEqual(self.offer(plain), [])
        self.assertFalse(state.exists(), "nothing under the home's state dir")

    def test_session_text_places_the_offer(self):
        text = kh.session_text("startup", {"CLAUDE_PROJECT_DIR": str(self.legacy)})
        lines = text.splitlines()
        self.assertTrue(lines[0].startswith("Karvey (info): team settings"))
        self.assertTrue(lines[1].startswith("Karvey (upgrade): "))
        g.write(self.legacy, "docs/spec/agent/manifest.md", "# me\n")
        text = kh.session_text("startup", {"CLAUDE_PROJECT_DIR": str(self.legacy)})
        first = text.split("=== First action ===", 1)[1].strip().splitlines()
        self.assertTrue(first[0].startswith("Run `/karvey-checkpoint restore`"))
        self.assertTrue(first[3].startswith("Karvey (upgrade): "), first)
        self.assertEqual(kh.session_text("resume", {"CLAUDE_PROJECT_DIR": str(self.legacy)}).count("(upgrade)"), 0)
