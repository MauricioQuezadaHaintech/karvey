"""Stakeholders (architecture §1.12, C-12).

@req REQ-W3-020
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


if __name__ == "__main__":
    unittest.main()
