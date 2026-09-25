"""advance / generated / skip / reopen (REQ-W1-004, 007, 008, 011)."""
import json
import os
import unittest
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from _state import make_project, run_json, state
from karvey_lib import approval as ap

g.isolate_git()
T0 = "2026-09-23T10:00:00-03:00"


def ok(ref="D-1"):
    return {"generated": True, "approved": True, "by": "M", "role": "human", "date": T0, "ref": ref}


def base_spec(phase="requirements", approvals=None, skipped=None, history=None):
    s = {"change_id": "feat-a", "phase": phase,
         "phase_history": history if history is not None else [
             {"phase": "init", "entered_at": T0, "exited_at": T0}, {"phase": phase, "entered_at": T0}],
         "approvals": approvals if approvals is not None else {}}
    if skipped is not None:
        s["skipped"] = skipped
    return s


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        self.xdg = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg"),
                                                ap.COMPAT_ENV: ""})
        self.xdg.start()

    def tearDown(self):
        self.xdg.stop()
        self.t.cleanup()

    def put(self, data):
        self.f = make_project(self.root, spec=data)
        return self.f

    def read(self):
        return json.loads(self.f.read_text(encoding="utf-8"))

    def st(self, *argv):
        return run_json(*(list(argv) + ["--root", str(self.root)]))

    def assert_refused_unchanged(self, argv, needle):
        before = self.f.read_bytes()
        code, env = self.st(*argv)
        self.assertEqual(code, 3, env)
        self.assertIn(needle, env["errors"][0]["message"])
        self.assertEqual(self.f.read_bytes(), before)
        return env


class Advance(Base):
    def test_allowed_edge_closes_and_appends_history(self):
        self.put(base_spec(approvals={"requirements": ok()}, skipped={"mockup": "no UI", "design_graphic": "no UI"}))
        code, env = self.st("advance", "feat-a", "architecture", "--by", "M")
        self.assertEqual(code, 0, env)
        d = self.read()
        self.assertEqual(d["phase"], "architecture")
        h = d["phase_history"]
        self.assertEqual(h[0], {"phase": "init", "entered_at": T0, "exited_at": T0})  # never rewritten
        self.assertEqual(list(h[1]), ["phase", "entered_at", "exited_at"])
        self.assertTrue(state.parse_dt(h[1]["exited_at"]))
        self.assertEqual((h[2]["phase"], h[2]["by"]), ("architecture", "M"))
        self.assertTrue(state.parse_dt(h[2]["entered_at"]))
        self.assertEqual(d["updated_at"], h[2]["entered_at"])

    def test_refused_edge_is_byte_identical(self):
        self.put(base_spec(approvals={"requirements": {"generated": True, "approved": False}},
                           skipped={"mockup": "no UI", "design_graphic": "no UI"}))
        self.assert_refused_unchanged(("advance", "feat-a", "architecture"), "requirements not approved or skipped")

    def test_skipped_satisfies_a_precondition_but_pending_mockup_does_not(self):
        self.put(base_spec(approvals={"requirements": ok()}))
        self.assert_refused_unchanged(("advance", "feat-a", "architecture"), "mockup not approved or skipped")
        code, env = self.st("advance", "feat-a", "mockup")
        self.assertEqual(code, 0)

    def test_backward_and_jump_over_unapproved_phases_refused(self):
        self.put(base_spec(phase="tasks", approvals={"requirements": ok(), "architecture": ok(), "tasks": ok()},
                           skipped={"mockup": "a", "design_graphic": "a", "infra": "a"}))
        self.assert_refused_unchanged(("advance", "feat-a", "requirements"), "use reopen")
        self.assert_refused_unchanged(("advance", "feat-a", "qa"), "impl not passed")
        self.assert_refused_unchanged(("advance", "feat-a", "tasks"), "already in")

    def test_corrupt_last_history_entry(self):
        self.put(base_spec(approvals={"requirements": ok()}, skipped={"mockup": "a", "design_graphic": "a"},
                           history=[{"phase": "init", "entered_at": T0}, {"phase": "requirements"}]))
        self.assert_refused_unchanged(("advance", "feat-a", "architecture"), "last entry is corrupt")

    def test_legacy_exact_phase_mapped_and_normalised_on_write(self):
        s = base_spec(phase="requirements", approvals={"requirements": ok()},
                      skipped={"mockup": "a", "design_graphic": "a"},
                      history=[{"phase": "init", "entered_at": T0, "exited_at": T0},
                               {"phase": "requirements", "entered_at": T0},
                               ])
        s["phase"] = "requirements-generated"
        s["notes"] = "untouched"
        self.put(s)
        code, env = self.st("advance", "feat-a", "architecture")
        self.assertEqual(code, 0, env)
        d = self.read()
        self.assertEqual((d["phase"], d["notes"]), ("architecture", "untouched"))

    def test_unmappable_phase_refused(self):
        s = base_spec()
        s["phase"] = "iterate"
        self.put(s)
        self.assert_refused_unchanged(("advance", "feat-a", "requirements"), "validate --fix --dry-run")

    def test_hand_written_history_normalised_by_a_transition(self):
        s = base_spec(phase="architecture", approvals={"requirements": ok(), "architecture": ok()},
                      skipped={"mockup": "a", "design_graphic": "a", "infra": "a"},
                      history=[{"phase": "init", "entered_at": T0, "exited_at": T0},
                               {"phase": "requirements", "entered_at": T0},
                               {"from": "requirements", "to": "architecture", "at": "2026-09-23T21:00:00Z"}])
        self.put(s)
        code, env = self.st("advance", "feat-a", "tasks")
        self.assertEqual(code, 0, env)
        h = self.read()["phase_history"]
        self.assertEqual([e["phase"] for e in h], ["init", "requirements", "architecture", "tasks"])
        self.assertEqual(h[1]["exited_at"], "2026-09-23T21:00:00Z")


class Deployed(Base):
    def at_deploying(self):
        a = {k: ok() for k in ("requirements", "architecture", "tasks", "qa")}
        self.put(base_spec(phase="deploying", approvals=a, skipped={"mockup": "a", "design_graphic": "a",
                                                                    "infra": "a"}))

    def test_deployed_needs_ledger_evidence(self):
        self.at_deploying()
        self.assert_refused_unchanged(("advance", "feat-a", "deployed", "--pipeline-run", "https://ci/1",
                                       "--post-deploy-check", "pass"), "no human prod approval")
        ap.record_prod(self.root, "feat-a", {"by": "M", "role": "human", "date": T0, "ref": "D-20"})
        self.assert_refused_unchanged(("advance", "feat-a", "deployed"), "--pipeline-run")
        code, env = self.st("advance", "feat-a", "deployed", "--pipeline-run", "https://ci/1",
                            "--post-deploy-check", "pass")
        self.assertEqual(code, 0, env)
        led, _ = ap.read_ledger(self.root, "feat-a")
        self.assertEqual((led["release"]["pipeline_run"], led["release"]["post_deploy_check"]), ("https://ci/1", "pass"))
        self.assertEqual(self.read()["phase"], "deployed")
        self.assertEqual(self.read()["phase_history"][-1]["evidence"]["pipeline_run"], "https://ci/1")

    def test_flags_only_for_deployed(self):
        self.at_deploying()
        code, env = self.st("advance", "feat-a", "deployed", "--post-deploy-check", "fail")
        self.assertEqual(code, 2)


class Archived(Base):
    def at_deployed(self, prod=None):
        a = {k: ok() for k in ("requirements", "architecture", "tasks", "qa")}
        if prod:
            a["prod"] = prod
        self.put(base_spec(phase="deployed", approvals=a, skipped={"mockup": "a", "design_graphic": "a",
                                                                   "infra": "a"}))

    def test_archived_needs_human_prod_in_spec(self):
        self.at_deployed()
        self.assert_refused_unchanged(("advance", "feat-a", "archived"), "approvals.prod in spec.json")
        self.at_deployed(prod={"by": "M", "role": "human", "date": T0, "ref": "D-20"})
        code, env = self.st("advance", "feat-a", "archived")
        self.assertEqual(code, 0, env)

    def test_archive_from_deploying_refused(self):
        a = {k: ok() for k in ("requirements", "architecture", "tasks", "qa")}
        self.put(base_spec(phase="deploying", approvals=a, skipped={"mockup": "a", "design_graphic": "a",
                                                                    "infra": "a"}))
        env = self.assert_refused_unchanged(("advance", "feat-a", "archived"), "")
        self.assertEqual(env["exit"], 3)


class Skip(Base):
    def test_skip_records_reason(self):
        self.put(base_spec())
        code, env = self.st("skip", "feat-a", "mockup", "--reason", "no UI")
        self.assertEqual(code, 0)
        self.assertEqual(self.read()["skipped"], {"mockup": "no UI"})
        code, env = self.st("skip", "feat-a", "design_graphic", "--reason", "no UI")
        self.assertEqual(self.read()["skipped"], {"mockup": "no UI", "design_graphic": "no UI"})

    def test_non_skippable_and_empty_reason_refused(self):
        self.put(base_spec())
        self.assert_refused_unchanged(("skip", "feat-a", "tasks", "--reason", "x"), "not skippable")
        self.assert_refused_unchanged(("skip", "feat-a", "mockup"), "non-empty --reason")
        self.assert_refused_unchanged(("skip", "feat-a", "mockup", "--reason", "   "), "non-empty --reason")


class Generated(Base):
    def test_generated(self):
        self.put(base_spec())
        code, env = self.st("generated", "feat-a", "requirements")
        self.assertEqual(code, 0)
        rec = self.read()["approvals"]["requirements"]
        self.assertTrue(rec.pop("generated_at"))  # wave2 REQ-W2-001: the first generation time
        self.assertEqual(rec, {"generated": True, "approved": False})
        self.assert_refused_unchanged(("generated", "feat-a", "prod"), "non-generable")
        self.assert_refused_unchanged(("generated", "feat-a", "nope"), "unknown")


class Reopen(Base):
    def test_reopen_moves_downstream_approvals_to_revision_history(self):
        a = {k: ok("D-%d" % i) for i, k in enumerate(("requirements", "architecture", "tasks"))}
        self.put(base_spec(phase="impl", approvals=a, skipped={"mockup": "a", "design_graphic": "a", "infra": "a"}))
        code, env = self.st("reopen", "feat-a", "architecture", "--reason", "spec-gap F-9", "--ref", "F-9")
        self.assertEqual(code, 0, env)
        d = self.read()
        self.assertEqual(d["phase"], "architecture")
        self.assertEqual(d["approvals"]["requirements"], a["requirements"])
        self.assertEqual(d["approvals"]["architecture"], {"generated": True, "approved": False})
        self.assertEqual(d["approvals"]["tasks"], {"generated": True, "approved": False})
        rh = d["revision_history"][-1]
        self.assertEqual((rh["reopened"], rh["from_phase"], rh["reason"], rh["ref"]),
                         ("architecture", "impl", "spec-gap F-9", "F-9"))
        self.assertEqual(rh["superseded_approvals"], {"architecture": a["architecture"], "tasks": a["tasks"]})
        self.assertEqual(d["phase_history"][-1]["phase"], "architecture")

    def test_reopen_refusals(self):
        self.put(base_spec(phase="impl"))
        self.assert_refused_unchanged(("reopen", "feat-a", "qa", "--reason", "x"), "not a reopen target")
        self.assert_refused_unchanged(("reopen", "feat-a", "tasks"), "non-empty --reason")
        self.put(base_spec(phase="requirements"))
        self.assert_refused_unchanged(("reopen", "feat-a", "tasks", "--reason", "x"), "forward")
        self.put(base_spec(phase="deploying"))
        self.assert_refused_unchanged(("reopen", "feat-a", "tasks", "--reason", "x"), "up to qa")


class Concurrency(Base):
    def test_cas_refuses_when_another_writer_changed_the_file(self):
        self.put(base_spec(approvals={"requirements": ok()}, skipped={"mockup": "a", "design_graphic": "a"}))
        real = state.load_change

        def racing(root, change):
            path, loaded = real(root, change)
            path.write_text(path.read_text() + " ", encoding="utf-8")  # another session writes meanwhile
            return path, loaded

        with mock.patch.object(state, "load_change", side_effect=racing):
            code, env = self.st("advance", "feat-a", "architecture")
        self.assertEqual(code, 3)
        self.assertIn("another writer", env["errors"][0]["message"])
        self.assertEqual(json.loads(self.f.read_text())["phase"], "requirements")

    def test_fresh_lock_refuses(self):
        self.put(base_spec(approvals={"requirements": ok()}, skipped={"mockup": "a", "design_graphic": "a"}))
        lock = str(self.f) + ".lock"
        open(lock, "w").close()
        real_lock = state.atomicio.lock

        def quick(path, wait_s=5.0, stale_s=None):
            return real_lock(path, wait_s=0.1, stale_s=stale_s)

        with mock.patch.object(state.atomicio, "lock", side_effect=quick):
            code, env = self.st("advance", "feat-a", "architecture")
        self.assertEqual(code, 3)
        self.assertIn("locked", env["errors"][0]["message"])
        os.unlink(lock)


if __name__ == "__main__":
    unittest.main()
