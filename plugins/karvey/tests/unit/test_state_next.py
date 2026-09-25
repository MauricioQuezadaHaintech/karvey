"""next and active (REQ-W1-005, REQ-W1-045)."""
import unittest

import _path  # noqa: F401
import _gitrepo as g
from _state import make_project, run, run_json, state

g.isolate_git()

PHASES = [p["id"] for p in state.machine()["phases"]]
T0 = "2026-09-23T10:00:00-03:00"


def ok(ref="D-1"):
    return {"generated": True, "approved": True, "by": "M", "role": "human", "date": T0, "ref": ref}


def spec_at(phase, approve_current=True, skipped=None):
    """A valid spec at ``phase`` with every earlier gate approved (and the current one if asked)."""
    idx = PHASES.index(phase)
    approvals = {}
    for p in state.machine()["phases"][:idx + (1 if approve_current else 0)]:
        key = p["approval"]
        if key == "prod":
            approvals["prod"] = {"by": "M", "role": "human", "date": T0, "ref": "D-8"}
        elif key:
            approvals[key] = ok()
    hist = [{"phase": p, "entered_at": T0, "exited_at": T0} for p in PHASES[:idx]]
    hist.append({"phase": phase, "entered_at": T0})
    s = {"change_id": "feat-a", "phase": phase, "phase_history": hist, "approvals": approvals}
    if skipped:
        s["skipped"] = skipped
    return s


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path

    def tearDown(self):
        self.t.cleanup()

    def next(self, data):
        make_project(self.root, spec=data)
        return run_json("next", "feat-a", "--root", str(self.root))


class EveryPhase(Base):
    def test_next_for_every_phase(self):
        expected_status = {"init": "in-progress", "impl": "in-progress", "test": "in-progress",
                           "deploying": "in-progress", "archived": "ready"}
        for i, ph in enumerate(PHASES):
            code, env = self.next(spec_at(ph))
            self.assertEqual(code, 0, (ph, env["errors"]))
            r = env["result"]
            self.assertEqual(r["phase"], ph)
            self.assertEqual(r["next_phase"], PHASES[i + 1] if i + 1 < len(PHASES) else None, ph)
            self.assertEqual(r["status"], expected_status.get(ph, "ready"), (ph, r))
            if r["status"] == "ready" and r["next_phase"]:
                self.assertEqual(r["skill"], state.phase_def(r["next_phase"])["skill"])

    def test_tasks_approved_proposes_impl(self):
        code, env = self.next(spec_at("tasks"))
        self.assertEqual((env["result"]["status"], env["result"]["next_phase"], env["result"]["skill"]),
                         ("ready", "impl", "karvey-impl"))

    def test_generated_not_approved_is_awaiting_approval(self):
        s = spec_at("requirements", approve_current=False)
        s["approvals"]["requirements"] = {"generated": True, "approved": False}
        code, env = self.next(s)
        self.assertEqual(env["result"]["status"], "awaiting-approval")
        self.assertEqual(env["result"]["skill"], "karvey-requirements")
        self.assertIn("requirements not approved or skipped", env["result"]["blockers"])


class ThisChangeShape(Base):
    def test_mockup_and_design_graphic_skipped_go_to_architecture(self):
        s = spec_at("requirements", skipped={"mockup": "no UI", "design_graphic": "no UI"})
        code, env = self.next(s)
        r = env["result"]
        self.assertEqual((r["status"], r["next_phase"], r["skill"]), ("ready", "architecture", "karvey-architecture"))
        self.assertIn({"phase": "mockup", "state": "skipped"}, r["preconditions"])

    def test_architecture_with_infra_skipped_goes_to_tasks(self):
        s = spec_at("architecture", skipped={"mockup": "no UI", "design_graphic": "no UI", "infra": "none"})
        for k in ("mockup", "design_graphic"):
            s["approvals"].pop(k)
        code, env = self.next(s)
        self.assertEqual(env["result"]["next_phase"], "tasks")

    def test_legacy_exact_phase_is_mapped_in_memory(self):
        s = spec_at("tasks")
        s["phase"] = "tasks-approved"
        code, env = self.next(s)
        self.assertEqual(code, 0)
        self.assertEqual((env["result"]["phase"], env["result"]["phase_raw"], env["result"]["next_phase"]),
                         ("tasks", "tasks-approved", "impl"))


class Invalid(Base):
    def test_invalid_file_reports_errors_instead_of_guessing(self):
        s = spec_at("tasks")
        s["phase"] = "qa-approved"
        code, env = self.next(s)
        self.assertEqual(code, 1)
        self.assertEqual(env["result"]["status"], "invalid")
        self.assertIsNone(env["result"]["next_phase"])
        self.assertIn("$.phase", [e["path"] for e in env["errors"]])

    def test_unreadable_exit_4(self):
        make_project(self.root, spec="{")
        code, env = run_json("next", "feat-a", "--root", str(self.root))
        self.assertEqual(code, 4)
        code, env = run_json("next", "missing", "--root", str(self.root))
        self.assertEqual(code, 4)


class Active(Base):
    def mk(self, cid, phase="impl", implemented=False):
        make_project(self.root, spec={"change_id": cid, "phase": phase}, change=cid)
        if implemented:
            (self.root / "docs/spec/changes" / cid / "IMPLEMENTED").write_text("")

    def test_excludes_archive_implemented_and_deployed(self):
        self.mk("feat-a")
        self.mk("feat-b", implemented=True)
        self.mk("feat-c", phase="deployed")
        (self.root / "docs/spec/changes/archive/2026-01-01-old").mkdir(parents=True)
        code, env = run_json("active", "--root", str(self.root))
        self.assertEqual(code, 0)
        self.assertEqual((env["result"]["change"], env["result"]["reason"]), ("feat-a", "single"))

    def test_only_archived_gives_none(self):
        (self.root / "docs/spec/changes/archive/2026-01-01-old").mkdir(parents=True)
        code, env = run_json("active", "--root", str(self.root))
        self.assertEqual((env["result"]["change"], env["result"]["reason"]), (None, "none"))

    def test_several_and_branch(self):
        repo = g.init(self.root, branch="feature/feat-b")
        self.mk("feat-a")
        self.mk("feat-b")
        code, out, _ = run("active", "--root", str(repo))
        self.assertIn("active: feat-b (branch)", out)
        g.run(["checkout", "-q", "-b", "other"], repo)
        code, out, _ = run("active", "--root", str(repo))
        self.assertIn("several active: feat-a, feat-b", out)


class BlockersOnce(Base):
    def test_REQ_W2_074_current_phase_blocker_listed_once(self):
        """@req REQ-W2-074 — the current phase is also a precondition of the next one (F-26)."""
        data = spec_at("architecture", approve_current=False, skipped={"mockup": "no UI", "design_graphic": "no UI"})
        data["approvals"]["architecture"] = {"generated": True, "approved": False}
        code, env = self.next(data)
        self.assertEqual(code, 0, env)
        self.assertEqual(env["result"]["blockers"].count("architecture not approved or skipped"), 1)
        code, out, _ = run("next", "feat-a", "--root", str(self.root))
        self.assertEqual(out.count("blocker: architecture not approved or skipped"), 1)


class ThisRepo(unittest.TestCase):
    def test_next_wave1_prints_a_status(self):
        code, env = run_json("next", "wave1-hardening", "--root", str(_path.REPO_ROOT))
        self.assertIn("status", env["result"])


if __name__ == "__main__":
    unittest.main()
