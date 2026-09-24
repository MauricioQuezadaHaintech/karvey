"""approve / check-prod / marker consumption (REQ-W1-006, 016, 023, 031, 032; D-03, D-10)."""
import json
import os
import unittest
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from _state import make_project, run_json
from karvey_lib import approval as ap

g.isolate_git()
T0 = "2026-09-23T10:00:00-03:00"


def ok(ref="D-1"):
    return {"generated": True, "approved": True, "by": "M", "role": "human", "date": T0, "ref": ref}


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        self.envp = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg"), ap.COMPAT_ENV: ""})
        self.envp.start()
        a = {k: ok() for k in ("requirements", "architecture", "tasks")}
        a["qa"] = {"generated": True, "approved": False}
        self.f = make_project(self.root, spec={
            "change_id": "feat-a", "phase": "qa", "approvals": a,
            "skipped": {"mockup": "a", "design_graphic": "a", "infra": "a"},
            "phase_history": [{"phase": p, "entered_at": T0, "exited_at": T0}
                              for p in ("init", "requirements", "architecture", "tasks", "impl", "test")]
            + [{"phase": "qa", "entered_at": T0}]})
        (self.root / "docs/spec/decisions.md").write_text("| D-20 | 2026-09-24 | D | prod OK |\n\n## D-21 — x\n")

    def tearDown(self):
        self.envp.stop()
        self.t.cleanup()

    def st(self, *argv):
        return run_json(*(list(argv) + ["--root", str(self.root)]))

    def read(self):
        return json.loads(self.f.read_text(encoding="utf-8"))

    def refused(self, argv, needle, code=3):
        before = self.f.read_bytes()
        c, env = self.st(*argv)
        self.assertEqual(c, code, env)
        self.assertIn(needle, env["errors"][0]["message"])
        self.assertEqual(self.f.read_bytes(), before)
        return env


class Fields(Base):
    def test_missing_by_role_ref_refused(self):
        self.refused(("approve", "feat-a", "qa", "--role", "human", "--ref", "D-20"), "missing: --by")
        self.refused(("approve", "feat-a", "qa", "--by", "M", "--ref", "D-20"), "missing: --role")
        self.refused(("approve", "feat-a", "prod", "--by", "M", "--role", "human"), "missing: --ref")
        self.refused(("approve", "feat-a", "qa", "--by", "M", "--role", "boss", "--ref", "D-20"), "--role")

    def test_date_needs_a_zone(self):
        self.refused(("approve", "feat-a", "qa", "--by", "M", "--role", "human", "--ref", "D-20",
                      "--date", "2026-09-24"), "time and zone")


class NonProd(Base):
    def test_without_marker_is_a_warning_and_evidence_none(self):
        c, env = self.st("approve", "feat-a", "qa", "--by", "M", "--role", "ceo-delegate", "--ref", "D-20")
        self.assertEqual(c, 0, env)
        self.assertEqual([w["code"] for w in env["warnings"]], ["state.no_marker"])
        q = self.read()["approvals"]["qa"]
        self.assertEqual((q["approved"], q["by"], q["role"], q["ref"], q["evidence"]),
                         (True, "M", "ceo-delegate", "D-20", {"marker": "none"}))
        self.assertTrue(q["date"][10] == "T")

    def test_with_marker_records_its_evidence(self):
        m = ap.write_marker(self.root, "plan", "feat-a", "aprobado, ejecuta", session_id="s1")
        c, env = self.st("approve", "feat-a", "qa", "--by", "M", "--role", "human", "--ref", "D-20")
        self.assertEqual(env["warnings"], [])
        ev = self.read()["approvals"]["qa"]["evidence"]
        self.assertEqual(ev, {"marker": "approvals/feat-a.json", "marker_created_at": m["created_at"],
                              "prompt_excerpt": "aprobado, ejecuta", "session": "s1"})


class Prod(Base):
    def test_ceo_delegate_refused(self):
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod")
        self.refused(("approve", "feat-a", "prod", "--by", "M", "--role", "ceo-delegate", "--ref", "D-20"),
                     "never delegated")

    def test_without_prod_marker_refused(self):
        self.refused(("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20"),
                     "prod-kind approval marker")
        ap.write_marker(self.root, "plan", "feat-a", "aprobado")  # a plan marker is not a prod approval (D-10)
        self.refused(("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20"),
                     "prod-kind approval marker")
        self.assertEqual(ap.read_ledger(self.root, "feat-a"), (None, "missing"))

    def test_prose_ref_refused(self):
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod")
        self.refused(("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "session approval"),
                     "D-NN or a PR approval URL")

    def test_ledger_written_spec_untouched(self):
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod", session_id="s9")
        before = self.f.read_bytes()
        c, env = self.st("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20")
        self.assertEqual(c, 0, env)
        self.assertEqual(self.f.read_bytes(), before)
        led, _ = ap.read_ledger(self.root, "feat-a")
        self.assertEqual((led["prod"]["by"], led["prod"]["role"], led["prod"]["ref"]), ("M", "human", "D-20"))
        self.assertEqual(led["prod"]["evidence"]["marker"], "approvals/feat-a.json")
        self.assertEqual(env["result"]["written"], "ledger")

    def test_write_spec_copies_the_ledger(self):
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod")
        self.st("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20")
        c, env = self.st("approve", "feat-a", "prod", "--write-spec")
        self.assertEqual(c, 0, env)
        led, _ = ap.read_ledger(self.root, "feat-a")
        self.assertEqual(self.read()["approvals"]["prod"], led["prod"])
        self.assertEqual(env["result"]["source"], "ledger")

    def test_write_spec_from_a_recorded_decision(self):
        c, env = self.st("approve", "feat-a", "prod", "--write-spec", "--by", "M", "--role", "human", "--ref", "D-21")
        self.assertEqual(c, 0, env)
        p = self.read()["approvals"]["prod"]
        self.assertEqual((p["by"], p["role"], p["ref"], env["result"]["source"]), ("M", "human", "D-21", "decision"))

    def test_write_spec_without_ledger_or_decision_refused(self):
        self.refused(("approve", "feat-a", "prod", "--write-spec", "--by", "M", "--role", "human", "--ref", "D-99"),
                     "not recorded")
        self.refused(("approve", "feat-a", "qa", "--write-spec", "--by", "M", "--role", "human", "--ref", "D-20"),
                     "only for prod", code=2)


class CheckProd(Base):
    def test_ok_from_ledger(self):
        ap.write_marker(self.root, "prod", "feat-a", "ok, merge a prod")
        self.st("approve", "feat-a", "prod", "--by", "M", "--role", "human", "--ref", "D-20")
        c, env = self.st("check-prod", "feat-a")
        self.assertEqual(c, 0)
        r = env["result"]
        self.assertEqual(sorted(r), sorted(["ok", "change", "by", "role", "ref", "date", "source", "missing"]))
        self.assertEqual((r["ok"], r["by"], r["role"], r["ref"], r["source"], r["missing"]),
                         (True, "M", "human", "D-20", "ledger", []))

    def test_nothing_recorded(self):
        c, env = self.st("check-prod", "feat-a")
        self.assertEqual(c, 1)
        self.assertEqual((env["result"]["ok"], env["result"]["missing"]), (False, ["by", "role", "ref"]))

    def test_hand_edited_spec_without_ledger(self):
        d = self.read()
        d["approvals"]["prod"] = {"by": "M", "role": "human", "date": T0, "ref": "D-20"}
        self.f.write_text(json.dumps(d))
        c, env = self.st("check-prod", "feat-a")
        self.assertEqual(c, 1)
        self.assertEqual((env["result"]["source"], env["result"]["reason"]),
                         ("spec", "approval not recorded through the state tool"))

    def test_corrupt_spec_and_unknown_change(self):
        self.f.write_text("{")
        c, env = self.st("check-prod", "feat-a")
        self.assertEqual(c, 4)
        c, env = self.st("check-prod", "nope")
        self.assertEqual(c, 4)

    def test_invalid_spec_cannot_verify(self):
        d = self.read()
        d["phase"] = "qa-approved"
        self.f.write_text(json.dumps(d))
        c, env = self.st("check-prod", "feat-a")
        self.assertEqual(c, 1)
        self.assertIn("cannot verify the production approval", env["result"]["reason"])


class Consumption(Base):
    def test_advance_consumes_the_marker_of_the_closing_phase(self):
        m = ap.write_marker(self.root, "plan", "feat-a", "aprobado, ejecuta")
        self.st("approve", "feat-a", "qa", "--by", "M", "--role", "human", "--ref", "D-20")
        self.assertIsNotNone(ap.find_valid(self.root, "feat-a")[0])
        c, env = self.st("advance", "feat-a", "deploying")
        self.assertEqual(c, 0, env)
        self.assertEqual(env["result"]["consumed"], ["feat-a"])
        got, _ = ap.read_marker(self.root, "feat-a")
        self.assertIsNotNone(got["consumed_at"])
        self.assertIsNone(ap.find_valid(self.root, "feat-a")[0])

    def test_project_marker_used_as_evidence_is_consumed(self):
        ap.write_marker(self.root, "plan", "_project", "ok")
        self.st("approve", "feat-a", "qa", "--by", "M", "--role", "human", "--ref", "D-20")
        self.assertEqual(self.read()["approvals"]["qa"]["evidence"]["marker"], "approvals/_project.json")
        c, env = self.st("advance", "feat-a", "deploying")
        self.assertEqual(env["result"]["consumed"], ["_project"])
        self.assertIsNone(ap.find_valid(self.root, "feat-a")[0])

    def test_unrelated_project_marker_is_kept(self):
        self.st("approve", "feat-a", "qa", "--by", "M", "--role", "human", "--ref", "D-20")
        ap.write_marker(self.root, "plan", "_project", "ok")
        c, env = self.st("advance", "feat-a", "deploying")
        self.assertEqual(env["result"]["consumed"], [])
        self.assertIsNotNone(ap.find_valid(self.root, "feat-a")[0])

if __name__ == "__main__":
    unittest.main()
