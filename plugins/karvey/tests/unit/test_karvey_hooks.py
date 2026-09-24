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
        self.assertEqual([g.name for g in kh.REGISTRY if g.wired], ["selftest", "protect-paths", "prod-gate", "git-flow", "plan-gate", "approval"])

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
        self.assertEqual(kh.main(["session", "startup"]), 0)


if __name__ == "__main__":
    unittest.main()
