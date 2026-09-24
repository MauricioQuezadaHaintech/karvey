"""validate --fix (architecture §2.5, REQ-W1-009, REQ-W1-010). Inline mini files; the full legacy
catalogue arrives in E1.F14.T1."""
import json
import unittest

import _gitrepo as g
from _state import make_project, run, run_json

g.isolate_git()

HIST = [{"phase": "init", "entered_at": "2026-09-23T10:00:00-03:00", "exited_at": "2026-09-23T10:00:00-03:00"},
        {"phase": "requirements", "entered_at": "2026-09-23T10:00:00-03:00"}]
PROJECT = {"git_platform": "github", "repos": ["r"], "spec_repo": "r",
           "branch_flow": {"integration": "dev", "production": "main"}}


def approved_values(data):
    ap = data.get("approvals") or {}
    return {k: v.get("approved") for k, v in ap.items() if isinstance(v, dict)}


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path

    def tearDown(self):
        self.t.cleanup()

    def spec_file(self, data):
        return make_project(self.root, spec=data)

    def fix(self, f, *extra):
        return run_json("validate", str(f), "--root", str(self.root), "--fix", *extra)

    def read(self, f):
        return json.loads(f.read_text(encoding="utf-8"))


class PhaseTiers(Base):
    def test_exact_tier(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "tasks-approved", "phase_history": HIST})
        code, env = self.fix(f)
        self.assertEqual(self.read(f)["phase"], "tasks")
        self.assertTrue(env["result"]["files"][0]["written"])
        self.assertIn('-  "phase": "tasks-approved"', env["result"]["files"][0]["diff"])

    def test_deploy_maps_to_deploying(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "deploy"})
        self.fix(f)
        self.assertEqual(self.read(f)["phase"], "deploying")

    def test_proposed_tier_only_with_the_flag(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "implementing"})
        code, env = self.fix(f)
        self.assertEqual(self.read(f)["phase"], "implementing")
        self.assertIn("--accept-proposed", " ".join(env["result"]["files"][0]["notes"]))
        code, env = self.fix(f, "--accept-proposed")
        self.assertEqual(self.read(f)["phase"], "impl")

    def test_unmappable_exit_3_no_write(self):
        for value in ("shipping", "iterate", None):
            data = {"change_id": "feat-a", "phase": value}
            f = self.spec_file(data)
            before = f.read_bytes()
            code, env = self.fix(f)
            self.assertEqual(code, 3, value)
            self.assertEqual(f.read_bytes(), before)
            self.assertIn("unmappable", env["errors"][0]["message"])


class OtherRules(Base):
    def test_gates_skipped(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "requirements",
                            "gates_skipped": {"phases": ["mockup", "design-graphic"], "reason": "no UI"}})
        self.fix(f)
        d = self.read(f)
        self.assertEqual(d["skipped"], {"mockup": "no UI", "design_graphic": "no UI"})
        self.assertNotIn("gates_skipped", d)

    def test_gates_skipped_with_non_skippable_phases_is_kept(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "archived",
                            "gates_skipped": {"phases": ["architecture", "tasks", "qa"], "reason": "r"}})
        code, env = self.fix(f)
        d = self.read(f)
        self.assertIn("gates_skipped", d)
        self.assertNotIn("skipped", d)
        self.assertIn("not skippable", " ".join(env["result"]["files"][0]["notes"]))

    def test_embedded_skips(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "architecture", "approvals": {
            "mockup": {"skipped": True, "skip_reason": "no UI"},
            "design_graphic": {"na": True},
            "infra": {"not_applicable": True, "reason": "no cloud"},
            "tasks": {"skipped": True, "nota": "x"}}})
        self.fix(f)
        d = self.read(f)
        self.assertEqual(d["skipped"], {"mockup": "no UI", "design_graphic": "(legacy: no reason recorded)",
                                        "infra": "no cloud"})
        self.assertEqual(d["approvals"]["mockup"], {"skipped": True, "skip_reason": "no UI"})  # left in place

    def test_approvals_null(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "init", "approvals": None})
        self.fix(f)
        self.assertEqual(self.read(f)["approvals"], {})

    def test_hand_written_history(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "architecture", "phase_history": HIST + [
            {"from": "requirements", "to": "architecture", "at": "2026-09-23T21:00:00Z", "by": "M", "ref": "D-5"}]})
        self.fix(f)
        h = self.read(f)["phase_history"]
        self.assertEqual(h[1], {"phase": "requirements", "entered_at": "2026-09-23T10:00:00-03:00",
                                "exited_at": "2026-09-23T21:00:00Z"})
        self.assertEqual(h[2], {"phase": "architecture", "entered_at": "2026-09-23T21:00:00Z", "by": "M",
                                "ref": "D-5"})


class Management(Base):
    def test_spec_none_to_markdown_and_string_kept(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "init", "management": "none"})
        self.fix(f)
        self.assertEqual(self.read(f)["management"], "markdown")
        f = self.spec_file({"change_id": "feat-a", "phase": "init", "management": "clickup"})
        code, env = self.fix(f)
        self.assertFalse(env["result"]["files"][0]["changed"])

    def test_spec_42_not_migratable(self):
        f = self.spec_file({"change_id": "feat-a", "phase": "init", "management": 42})
        before = f.read_bytes()
        code, env = self.fix(f)
        self.assertEqual(code, 3)
        self.assertEqual(f.read_bytes(), before)
        self.assertIn("not migratable", env["errors"][0]["message"])

    def project_file(self, data):
        make_project(self.root, project=data)
        return self.root / "docs/spec/project.json"

    def test_project_string(self):
        f = self.project_file(dict(PROJECT, management="markdown", knowledge_sync="none"))
        self.fix(f)
        d = self.read(f)
        self.assertEqual(d["management"], {"tool": "markdown"})
        self.assertEqual(dict(d, management=None), dict(PROJECT, management=None, knowledge_sync="none"))
        self.assertNotIn("statuses", d["management"])

    def test_project_clickup_backlog_list(self):
        f = self.project_file(dict(PROJECT, management="clickup",
                                   clickup={"backlog_list_id": "901234", "space": "S"}))
        self.fix(f)
        d = self.read(f)
        self.assertEqual(d["management"], {"tool": "clickup", "location": "901234"})
        self.assertEqual(d["clickup"], {"space": "S"})

    def test_project_42(self):
        f = self.project_file(dict(PROJECT, management=42))
        before = f.read_bytes()
        code, env = self.fix(f)
        self.assertEqual(code, 3)
        self.assertEqual(f.read_bytes(), before)


class Invariants(Base):
    LEGACY = {"change_id": "feat-a", "phase": "tasks-generated", "management": "none",
              "gates_skipped": {"phases": ["infra"], "reason": "no cloud"},
              "phase_history": HIST + [{"from": "requirements", "to": "architecture",
                                        "at": "2026-09-23T21:00:00Z"}],
              "approvals": {"requirements": {"approved": True, "date": "2026-09-22"},
                            "architecture": {"approved": False, "generated": True},
                            "mockup": {"skipped": True, "skip_reason": "no UI"},
                            "qa": {"approved": None}, "prod": {"by": "", "date": "", "ref": ""}}}

    def test_idempotent_second_run_is_a_noop(self):
        f = self.spec_file(self.LEGACY)
        self.fix(f)
        once = f.read_bytes()
        code, env = self.fix(f)
        self.assertEqual(f.read_bytes(), once)
        self.assertFalse(env["result"]["files"][0]["changed"])
        self.assertNotIn("diff", env["result"]["files"][0])

    def test_no_approval_created_or_flipped(self):
        f = self.spec_file(self.LEGACY)
        self.fix(f, "--accept-proposed")
        after = self.read(f)
        self.assertEqual(approved_values(after), approved_values(self.LEGACY))
        self.assertEqual(after["approvals"], self.LEGACY["approvals"])

    def test_dry_run_writes_nothing_and_shows_the_diff_first(self):
        f = self.spec_file(self.LEGACY)
        before = f.read_bytes()
        code, out, _ = run("validate", str(f), "--root", str(self.root), "--fix", "--dry-run")
        self.assertEqual(f.read_bytes(), before)
        self.assertTrue(out.startswith("--- a/docs/spec/changes/feat-a/spec.json"))
        self.assertIn("would fix", out)

    def test_after_fix_it_validates(self):
        f = self.spec_file(self.LEGACY)
        code, env = self.fix(f)
        self.assertEqual(code, 0, env["errors"])
        code, env = run_json("validate", str(f), "--root", str(self.root))
        self.assertEqual(code, 0)
        self.assertNotIn("state.legacy_phase", [w["code"] for w in env["warnings"]])

    def test_fix_flags_need_fix(self):
        f = self.spec_file(self.LEGACY)
        code, env = run_json("validate", str(f), "--root", str(self.root), "--dry-run")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
