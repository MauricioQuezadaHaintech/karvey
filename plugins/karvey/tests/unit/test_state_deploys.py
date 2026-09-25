"""Deploy records, approvals.deploy retired, attested deployed (architecture §1.4 of wave2-structural).

@req REQ-W2-002 REQ-W2-051 REQ-W2-053
"""
import json
import os
import unittest
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from _state import make_project, run_json, state
from karvey_lib import approval as ap

g.isolate_git()
T0 = "2026-09-25T10:00:00-03:00"
RUN = "https://ci.example.test/runs/42"


def ok():
    return {"generated": True, "approved": True, "by": "M", "role": "human", "date": T0, "ref": "D-1"}


def deploying_spec(**over):
    a = {k: ok() for k in ("requirements", "architecture", "tasks", "qa")}
    s = {"change_id": "feat-a", "phase": "deploying", "approvals": a,
         "skipped": {"mockup": "no UI", "design_graphic": "no UI", "infra": "no cloud"},
         "phase_history": [{"phase": p, "entered_at": T0, "exited_at": T0}
                           for p in ("init", "requirements", "architecture", "tasks", "impl", "test", "qa")]
         + [{"phase": "deploying", "entered_at": T0}]}
    s.update(over)
    return s


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        self.envp = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.t.path / "xdg"), ap.COMPAT_ENV: ""})
        self.envp.start()
        self.f = make_project(self.root, spec=deploying_spec())
        (self.root / "docs/spec/decisions.md").write_text("| D-20 | 2026-09-25 | D | prod OK |\n")

    def tearDown(self):
        self.envp.stop()
        self.t.cleanup()

    def st(self, *argv):
        return run_json(*(list(argv) + ["--root", str(self.root)]))

    def read(self):
        return json.loads(self.f.read_text(encoding="utf-8"))

    def refused(self, argv, *needles):
        before = self.f.read_bytes()
        c, env = self.st(*argv)
        self.assertEqual(c, 3, env)
        for n in needles:
            self.assertIn(n, env["errors"][0]["message"])
        self.assertEqual(self.f.read_bytes(), before)


class DeployRecord(Base):
    def test_REQ_W2_002_prod_pass_appends_entry(self):
        c, env = self.st("deploy-record", "feat-a", "--env", "prod", "--version", "3.13.0", "--verification", "pass",
                         "--date", T0)
        self.assertEqual(c, 0, env)
        self.assertEqual(self.read()["deploys"], [{"env": "prod", "version": "3.13.0", "at": T0,
                                                   "verification": "pass", "rollback": None}])
        self.st("deploy-record", "feat-a", "--env", "prod", "--version", "3.13.1", "--verification", "regression",
                "--rollback", "reverted to 3.13.0")
        self.assertEqual([d["version"] for d in self.read()["deploys"]], ["3.13.0", "3.13.1"])
        self.assertEqual(self.read()["deploys"][1]["rollback"], "reverted to 3.13.0")

    def test_REQ_W2_002_without_env_refused(self):
        self.refused(("deploy-record", "feat-a", "--version", "1", "--verification", "pass"), "--env")
        self.refused(("deploy-record", "feat-a", "--env", "prod", "--version", "1", "--verification", "ok"),
                     "--verification")

    def test_REQ_W2_002_schema_names_missing_env(self):
        data = deploying_spec(deploys=[{"version": "1", "at": T0, "verification": "pass"}])
        errs = [i for i in state.validate_data(data, "spec", False, "spec.json") if i["severity"] == "error"]
        self.assertEqual([i["path"] for i in errs], ["$.deploys[0].env"])


class DeployApprovalRetired(Base):
    def test_REQ_W2_051_new_change_never_writes_approvals_deploy(self):
        for cmd in (("generated", "feat-a", "deploy"),
                    ("approve", "feat-a", "deploy", "--by", "M", "--role", "human", "--ref", "D-1")):
            c, _ = self.st(*cmd)
            self.assertEqual(c, 3)
        self.assertNotIn("deploy", self.read()["approvals"])
        self.assertIsNone(state.phase_def("deploying")["approval"])

    def test_REQ_W2_051_legacy_key_warns_naming_the_migration(self):
        a = deploying_spec()["approvals"]
        a["deploy"] = {"generated": True, "approved": True, "date": "2026-09-22", "by": "M"}
        issues = state.validate_data(deploying_spec(approvals=a), "spec", False, "spec.json")
        w = [i for i in issues if i["code"] == "state.legacy_deploy_approval"]
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0]["severity"], "warning")
        self.assertIn("validate --fix", w[0]["message"])


class Attested(Base):
    def test_REQ_W2_053_no_ledger_attested_with_ref_and_url(self):
        c, env = self.st("advance", "feat-a", "deployed", "--attested", "--ref", "D-20", "--pipeline-run", RUN)
        self.assertEqual(c, 0, env)
        data = self.read()
        self.assertEqual(data["phase"], "deployed")
        self.assertEqual(data["phase_history"][-1]["evidence"],
                         {"attested": True, "ref": "D-20", "pipeline_run": RUN})
        self.assertEqual(ap.read_ledger(self.root, "feat-a")[1], "missing")

    def test_REQ_W2_053_missing_evidence_names_both(self):
        self.refused(("advance", "feat-a", "deployed", "--attested", "--ref", "D-20"),
                     "--ref D-NN", "--pipeline-run https://")
        self.refused(("advance", "feat-a", "deployed", "--attested", "--pipeline-run", RUN), "missing: --ref D-NN")
        self.refused(("advance", "feat-a", "deployed", "--attested", "--ref", "D-99", "--pipeline-run", RUN),
                     "missing: --ref D-NN")

    def test_REQ_W2_053_no_ledger_no_attested_names_the_alternative(self):
        self.refused(("advance", "feat-a", "deployed"), "--attested --ref D-NN")

    def test_REQ_W2_053_attested_refused_when_a_ledger_exists(self):
        ap.record_release(self.root, "feat-a", RUN, "pass", at=T0)
        self.refused(("advance", "feat-a", "deployed", "--attested", "--ref", "D-20", "--pipeline-run", RUN),
                     "measured path")

    def test_attested_only_for_deployed(self):
        c, _ = self.st("advance", "feat-a", "archived", "--attested")
        self.assertEqual(c, 2)


if __name__ == "__main__":
    unittest.main()
