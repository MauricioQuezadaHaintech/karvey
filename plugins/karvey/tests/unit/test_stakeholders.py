"""Stakeholders (architecture §1.12, C-12).

@req REQ-W3-020 REQ-W3-044
"""
import copy
import unittest

import _path  # noqa: F401
from karvey_lib import project as pj
from _state import GOOD_SPEC, state

PROJECT = {"git_platform": "github", "repos": ["r"], "spec_repo": "r",
           "branch_flow": {"feature_prefix": "feature/", "integration": "main", "production": "main"}}


def project(**stake):
    p = copy.deepcopy(PROJECT)
    p["stakeholders"] = stake
    return p


def errors(data, kind="project"):
    return [i for i in state.validate_data(data, kind, True, kind + ".json") if i["severity"] == "error"]


class Validate(unittest.TestCase):
    def test_REQ_W3_020_sponsor_with_a_webhook_secret_name_passes(self):
        p = project(sponsor={"role": "sponsor", "name": "Area sponsor",
                             "destination": {"channel": "webhook", "target": "SPONSOR_WEBHOOK"}})
        self.assertEqual(errors(p), [])

    def test_REQ_W3_020_literal_url_is_refused_asking_for_the_secret_name(self):
        p = project(sponsor={"role": "sponsor",
                             "destination": {"channel": "webhook", "target": "https://hooks.example.org/x/y"}})
        e = errors(p)
        self.assertEqual([i["path"] for i in e], ["$.stakeholders.sponsor.destination.target"])
        self.assertIn("secret", e[0]["message"])

    def test_F71_a_webhook_without_its_scheme_is_refused_by_the_pattern(self):
        p = project(sponsor={"role": "sponsor", "destination": {"channel": "webhook", "target": "hooks.example.org/x/y"}})
        self.assertEqual(len(errors(p)), 1)

    def test_email_destination_is_an_address(self):
        p = project(approver={"role": "approver", "destination": {"channel": "email", "target": "owner@example.org"}})
        self.assertEqual(errors(p), [])

    def test_spec_override_is_validated_too(self):
        spec = dict(GOOD_SPEC, stakeholders={"executor": {"role": "operator",
                                                          "destination": {"channel": "slack", "target": "https://x"}}})
        self.assertEqual([i["path"] for i in errors(spec, "spec")], ["$.stakeholders.executor.destination.target"])

    def test_leak_deny_terms_accepted(self):
        p = copy.deepcopy(PROJECT)
        p["leak"] = {"deny_terms": ["Other Sample Client"]}
        self.assertEqual(errors(p), [])


class Resolve(unittest.TestCase):
    def test_REQ_W3_020_change_override_wins_per_role(self):
        p = project(sponsor={"role": "sponsor", "name": "Area sponsor"}, approver={"role": "approver"})
        spec = {"stakeholders": {"sponsor": {"role": "sponsor", "name": "Program sponsor"}}}
        r = pj.stakeholders(p, spec)
        self.assertEqual(r["sponsor"]["name"], "Program sponsor")
        self.assertEqual(r["approver"]["name"], "approver")
        self.assertNotIn("executor", r)


class Client(unittest.TestCase):
    """@req REQ-W3-044 — ``client`` is first-level; a change inherits it; a differing tracker tag warns."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        from _state import make_project
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-client-"))
        self.addCleanup(__import__("shutil").rmtree, str(self.tmp), True)
        make_project(self.tmp, project=dict(PROJECT, client="sample-client-a"))

    def test_REQ_W3_044_a_new_change_inherits_the_project_client(self):
        import json
        from _state import run_json
        code, env = run_json("init", "new-change", "--root", str(self.tmp))
        self.assertEqual(code, 0, env)
        data = json.loads((self.tmp / "docs/spec/changes/new-change/spec.json").read_text(encoding="utf-8"))
        self.assertEqual(data["client"], "sample-client-a")

    def test_REQ_W3_044_a_differing_tracker_tag_warns_naming_both(self):
        import json
        from _state import run_json
        spec = dict(GOOD_SPEC, client="sample-client-a", clickup={"client_tag": "sample-client-b"})
        d = self.tmp / "docs/spec/changes/feat-a"
        d.mkdir(parents=True)
        (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        code, env = run_json("validate", "--all", "--root", str(self.tmp))
        self.assertEqual(code, 0, env["errors"])
        msgs = [w["message"] for w in env["warnings"] if w["code"] == "client.mismatch"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("'sample-client-a'", msgs[0])
        self.assertIn("'sample-client-b'", msgs[0])

    def test_client_is_a_valid_first_level_field(self):
        self.assertEqual(errors(dict(PROJECT, client="sample-client-a")), [])
        self.assertEqual(errors(dict(GOOD_SPEC, client="sample-client-a"), "spec"), [])


if __name__ == "__main__":
    unittest.main()
