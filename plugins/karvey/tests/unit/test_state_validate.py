import copy
import shutil
import unittest

import _path
import _gitrepo as g
from _state import GOOD_SPEC, make_project, run, run_json

g.isolate_git()


def spec(**over):
    s = copy.deepcopy(GOOD_SPEC)
    for k, v in over.items():
        if v is None:
            s.pop(k, None)
        else:
            s[k] = v
    return s


def codes(env, sev="errors"):
    return [(i["code"], i["path"]) for i in env[sev]]


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path

    def tearDown(self):
        self.t.cleanup()

    def validate(self, data, *extra, project=None):
        f = make_project(self.root, spec=data, project=project)
        return run_json("validate", str(f), "--root", str(self.root), *extra)


class Valid(Base):
    def test_valid_spec_no_violation_exit_0(self):
        code, env = self.validate(spec())
        self.assertEqual(code, 0)
        self.assertEqual((env["errors"], env["warnings"]), ([], []))
        self.assertEqual(tuple(env), ("tool", "version", "ok", "exit", "result", "errors", "warnings"))
        self.assertEqual(env["result"]["files"][0]["file"], "docs/spec/changes/feat-a/spec.json")

    def test_human_output(self):
        f = make_project(self.root, spec=spec())
        code, out, _ = run("validate", str(f), "--root", str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("OK", out)


class Enum(Base):
    def test_unknown_phase_is_an_error_naming_the_field(self):
        code, env = self.validate(spec(phase="qa-approved"))
        self.assertEqual(code, 1)
        self.assertIn(("schema.enum", "$.phase"), codes(env))
        self.assertEqual(env["errors"][0]["file"], "docs/spec/changes/feat-a/spec.json")

    def test_exact_legacy_phase_warns_in_advisory_errors_in_strict(self):
        code, env = self.validate(spec(phase="requirements-generated"))
        self.assertEqual(code, 0)
        self.assertIn(("state.legacy_phase", "$.phase"), codes(env, "warnings"))
        self.assertIn("outside the enum", env["warnings"][0]["message"])
        code, env = self.validate(spec(phase="requirements-generated"), "--strict")
        self.assertEqual(code, 1)
        self.assertIn(("state.legacy_phase", "$.phase"), codes(env))

    def test_unmappable_phase_is_an_error(self):
        code, env = self.validate(spec(phase="iterate"))
        self.assertEqual(code, 1)


class Prod(Base):
    def test_prod_by_without_ref_is_an_error_even_advisory(self):
        s = spec(approvals={"prod": {"by": "X", "role": "human", "date": "2026-09-23T10:00:00-03:00", "ref": ""}})
        code, env = self.validate(s)
        self.assertEqual(code, 1)
        self.assertIn("$.approvals.prod.ref", [i["path"] for i in env["errors"]])


class Modes(Base):
    LEGACY = {"requirements": {"generated": True, "approved": True, "date": "2026-09-22"}}

    def test_advisory_legacy_approval_exit_0(self):
        code, env = self.validate(spec(approvals=self.LEGACY))
        self.assertEqual(code, 0)
        self.assertEqual(env["result"]["mode"], "advisory")
        self.assertTrue(env["warnings"])

    def test_strict_flag(self):
        code, env = self.validate(spec(approvals=self.LEGACY), "--strict")
        self.assertEqual(code, 1)
        self.assertEqual(env["result"]["mode"], "strict")

    def test_schema_mode_strict_in_project_json(self):
        proj = {"git_platform": "github", "repos": ["r"], "spec_repo": "r",
                "branch_flow": {"integration": "main", "production": "main"}, "schema_mode": "strict"}
        code, env = self.validate(spec(approvals=self.LEGACY), project=proj)
        self.assertEqual(code, 1)
        self.assertEqual(env["result"]["mode"], "strict")


class History(Base):
    def test_gap_warns_and_is_an_error_in_strict(self):
        s = spec(phase="tasks", approvals={
            "requirements": {"approved": True, "by": "X", "role": "human", "date": "2026-09-23T10:00:00-03:00",
                             "ref": "D-1"},
            "architecture": {"approved": True, "by": "X", "role": "human", "date": "2026-09-23T10:00:00-03:00",
                             "ref": "D-2"}},
                 skipped={"mockup": "no UI", "design_graphic": "no UI", "infra": "none"})
        code, env = self.validate(s)
        self.assertEqual(code, 0)
        gaps = [i["expected"] for i in env["warnings"] if i["code"] == "state.history_gap"]
        self.assertEqual(gaps, ["architecture", "tasks"])  # REQ-W1-109 error scenario
        code, env = self.validate(s, "--strict")
        self.assertEqual(code, 1)

    def test_out_of_order_and_exit_before_enter(self):
        s = spec(phase_history=[
            {"phase": "init", "entered_at": "2026-09-23T12:00:00-03:00", "exited_at": "2026-09-23T11:00:00-03:00"},
            {"phase": "requirements", "entered_at": "2026-09-23T09:00:00-03:00"}])
        code, env = self.validate(s)
        self.assertEqual(code, 1)
        self.assertEqual([i["path"] for i in env["errors"] if i["code"] == "state.history_order"],
                         ["$.phase_history[0].exited_at", "$.phase_history[1].entered_at"])

    def test_hand_written_transition_is_a_legacy_warning(self):
        s = spec(phase="architecture", phase_history=GOOD_SPEC["phase_history"] + [
            {"from": "requirements", "to": "architecture", "at": "2026-09-23T21:00:00Z", "by": "X", "ref": "D-5"}],
                 approvals={"requirements": {"approved": True, "by": "X", "role": "human",
                                             "date": "2026-09-23T10:00:00-03:00", "ref": "D-5"}},
                 skipped={"mockup": "no UI", "design_graphic": "no UI"})
        code, env = self.validate(s)
        self.assertEqual(code, 0, env["errors"])
        self.assertEqual(codes(env, "warnings"), [("state.legacy_history", "$.phase_history[2]")])


class SemanticTable(Base):
    """architecture §2.3"""

    def test_past_unapproved_gate(self):
        s = spec(phase="architecture", skipped={"mockup": "no UI", "design_graphic": "no UI"},
                 phase_history=GOOD_SPEC["phase_history"] + [
                     {"phase": "architecture", "entered_at": "2026-09-23T11:00:00-03:00"}])
        code, env = self.validate(s)
        self.assertEqual(code, 0)
        self.assertIn(("state.gate_skipped", "$.approvals.requirements"), codes(env, "warnings"))
        code, env = self.validate(s, "--strict")
        self.assertEqual(code, 1)
        self.assertIn(("state.gate_skipped", "$.approvals.requirements"), codes(env))

    def test_skipped_and_approved_warns(self):
        s = spec(skipped={"mockup": "no UI"}, approvals={"mockup": {
            "approved": True, "by": "X", "role": "human", "date": "2026-09-23T10:00:00-03:00", "ref": "D-1"}})
        code, env = self.validate(s)
        self.assertIn(("state.skipped_and_approved", "$.skipped.mockup"), codes(env, "warnings"))

    def test_management_none_warns(self):
        code, env = self.validate(spec(management="none"))
        self.assertEqual(code, 0)
        self.assertIn(("state.legacy_management", "$.management"), codes(env, "warnings"))

    def test_approvals_null_warns(self):
        code, env = self.validate(dict(spec(), approvals=None))
        self.assertEqual(code, 0, env["errors"])
        self.assertIn(("state.legacy_approvals_null", "$.approvals"), codes(env, "warnings"))

    def test_embedded_skip_warns_and_counts_as_skipped(self):
        s = spec(phase="architecture", approvals={
            "requirements": {"approved": True, "by": "X", "role": "human", "date": "2026-09-23T10:00:00-03:00",
                             "ref": "D-1"},
            "mockup": {"skipped": True, "skip_reason": "no UI"}, "design_graphic": {"na": True}},
                 phase_history=GOOD_SPEC["phase_history"] + [
                     {"phase": "architecture", "entered_at": "2026-09-23T11:00:00-03:00"}])
        code, env = self.validate(s)
        self.assertEqual(code, 0)
        self.assertNotIn("state.gate_skipped", [c for c, _ in codes(env, "warnings")])
        self.assertEqual(len([1 for c, _ in codes(env, "warnings") if c == "state.legacy_embedded_skip"]), 2)

    def test_project_prod_gate_hook_not_boolean(self):
        (self.root / "docs/spec").mkdir(parents=True)
        p = self.root / "docs/spec/project.json"
        p.write_text('{"git_platform":"github","repos":["r"],"spec_repo":"r","branch_flow":'
                     '{"integration":"dev","production":"main"},"enforcement":{"prod_gate_hook":"no"}}')
        code, env = run_json("validate", str(p), "--root", str(self.root))
        self.assertEqual(code, 1)
        self.assertEqual([i["path"] for i in env["errors"]], ["$.enforcement.prod_gate_hook"])


class Errors(Base):
    def test_higher_schema_version_exit_4(self):
        code, env = self.validate(spec(schema_version=2))
        self.assertEqual(code, 4)
        self.assertIn("upgrade Karvey", env["errors"][0]["message"])

    def test_corrupt_file_exit_4(self):
        code, env = self.validate('{"phase": ')
        self.assertEqual(code, 4)

    def test_no_paths_is_usage(self):
        make_project(self.root, spec=spec())
        code, env = run_json("validate", "--root", str(self.root))
        self.assertEqual(code, 2)

    def test_not_a_karvey_project_exit_4(self):
        code, env = run_json("validate", "--all", "--root", str(self.root / "nowhere"))
        self.assertEqual(code, 4)


class ThisRepo(unittest.TestCase):
    def test_validate_all_envelope(self):
        code, env = run_json("validate", "--all", "--root", str(_path.REPO_ROOT))
        self.assertIn(code, (0, 1))
        self.assertEqual(env["exit"], code)
        names = [f["file"] for f in env["result"]["files"]]
        self.assertIn("docs/spec/changes/wave1-hardening/spec.json", names)
        self.assertIn("docs/spec/project.json", names)
        for i in env["errors"] + env["warnings"]:
            self.assertEqual(tuple(i), ("code", "severity", "file", "path", "expected", "got", "message"))



class LegacyFixtures(unittest.TestCase):
    """E1.F14.T1: validate never crashes on any legacy shape (architecture §6.3), in either mode."""

    def test_every_fixture_validates_without_crashing(self):
        fixtures = sorted((_path.FIXTURES_DIR / "legacy" / "spec").glob("*.json"))
        self.assertGreaterEqual(len(fixtures), 50)
        t = g.TempDir()
        try:
            changes = t.path / "docs/spec/changes"
            for fx in fixtures:
                (changes / fx.stem).mkdir(parents=True)
                shutil.copyfile(str(fx), str(changes / fx.stem / "spec.json"))
            for mode in ((), ("--strict",)):
                with self.subTest(mode=mode):
                    code, env = run_json("validate", "--all", "--root", str(t.path), *mode)
                    self.assertIn(code, (0, 1), env)
                    self.assertEqual(len(env["result"]["files"]), len(fixtures))
                    for i in env["errors"] + env["warnings"]:
                        self.assertEqual(tuple(i), ("code", "severity", "file", "path", "expected", "got", "message"))
                        self.assertNotIn("Traceback", i["message"])
                    for fx in fixtures:
                        code, out, err = run("validate", str(changes / fx.stem / "spec.json"), "--root",
                                             str(t.path), *mode)
                        self.assertIn(code, (0, 1), (fx.name, err))
                        self.assertNotIn("Traceback", err)
            # the four unmappable/erroring shapes are errors, not crashes
            code, env = run_json("validate", "--all", "--root", str(t.path))
            bad = {i["file"].split("/")[3] for i in env["errors"]}
            self.assertTrue({"phase-iterate", "phase-null", "phase-missing", "team-adapters-like"} <= bad, bad)
        finally:
            t.cleanup()

if __name__ == "__main__":
    unittest.main()
