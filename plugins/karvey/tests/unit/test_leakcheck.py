"""The sponsor page's leak check (architecture §1.13, C-13). Synthetic values only, built at run time so the
repository never holds a token-shaped string.

@req REQ-W3-023
"""
import json
import unittest
from unittest import mock

import _path  # noqa: F401
from karvey_lib import leakcheck as lc

CONN = "Server=db.example;Database=sales;User Id=app;" + "Pass" + "word=" + "x" * 10
KEY = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
HOME = "/" + "home" + "/someone/project/notes.md"


def rules_of(text, **ctx):
    return sorted({h["rule"] for h in lc.check({"risks[0].description": text}, ctx)["hits"]})


class Rules(unittest.TestCase):
    def test_secret_connection_string(self):
        self.assertEqual(rules_of("The job reads %s at start." % CONN), ["secret"])

    def test_secret_cloud_key_shape(self):
        self.assertEqual(rules_of("key %s was rotated" % KEY), ["secret"])

    def test_path_home_directory(self):
        self.assertEqual(rules_of("see %s" % HOME), ["path"])
        self.assertEqual(rules_of("see ~/notes/today.md"), ["path"])

    def test_host_private_suffix_and_range(self):
        self.assertEqual(rules_of("served from db.internal"), ["host"])
        self.assertEqual(rules_of("served from 10.0.0.5"), ["host"])

    def test_email_not_declared(self):
        self.assertEqual(rules_of("write to someone@example.org"), ["email"])

    def test_F81_email_target_of_a_declared_stakeholder_passes(self):
        self.assertEqual(rules_of("the page goes to sponsor@example.org",
                                  allowed_emails=["sponsor@example.org"]), [])

    def test_pii_phone_shape(self):
        self.assertEqual(rules_of("call +1 555 010 0199 today"), ["pii"])

    def test_dates_amounts_and_versions_are_not_pii(self):
        self.assertEqual(rules_of("as of 2026-10-14, US$ 41200000 spent, version 4.1.0, 12,345,678 rows"), [])

    def test_client_name_from_portfolio_and_deny_terms(self):
        self.assertEqual(rules_of("same flow as Other Sample Client", other_clients=["Other Sample Client"]),
                         ["client"])
        self.assertEqual(rules_of("the old vendor codename", deny_terms=["codename"]), ["client"])

    def test_clean_business_text_passes(self):
        out = lc.check({"scope.summary": "People sign in with their company account; access ends when it closes."},
                       {"deny_terms": ["codename"]})
        self.assertEqual((out["ok"], out["hits"], out["notes"]), (True, [], []))


class Contract(unittest.TestCase):
    def test_REQ_W3_023_report_never_contains_the_value(self):
        out = lc.check({"risks[1].description": "uses " + CONN})
        self.assertFalse(out["ok"])
        self.assertEqual(out["hits"], [{"field": "risks[1].description", "rule": "secret"}])
        self.assertNotIn("x" * 10, json.dumps(out))

    def test_without_portfolio_or_deny_terms_other_rules_still_run(self):
        out = lc.check({"a": "see " + HOME})
        self.assertIn(lc.NOT_CHECKED, out["notes"])
        self.assertEqual(out["hits"], [{"field": "a", "rule": "path"}])

    def test_an_exception_inside_a_rule_is_a_check_error_refusal(self):
        with mock.patch.object(lc, "_scan", side_effect=RuntimeError("boom")):
            out = lc.check({"a": "fine"})
        self.assertEqual((out["ok"], out["hits"]), (False, [{"field": "*", "rule": "check-error"}]))

    def test_rendered_page_text_ignores_style_and_tags(self):
        page = "<style>a{background:url(data:x)}</style><p>People &amp; teams</p><!-- /tmp/x/y -->"
        self.assertEqual(lc.text_of_html(page).split(), ["People", "&", "teams"])

    def test_flatten_names_fields(self):
        self.assertEqual(lc.flatten({"risks": [{"description": "d"}], "scope": {"summary": "s"}}),
                         {"risks[0].description": "d", "scope.summary": "s"})


if __name__ == "__main__":
    unittest.main()
