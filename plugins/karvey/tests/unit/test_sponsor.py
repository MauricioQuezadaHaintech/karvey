"""The sponsor page (architecture §1.13, C-13): the allow-listed model and ``karvey-sponsor.py``.

@req REQ-W3-021 REQ-W3-022 REQ-W3-023 REQ-W3-080
"""
import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import contextlib
import hashlib
import importlib.util
import io
from unittest import mock

import _path
from karvey_lib import sponsor

_SPEC = importlib.util.spec_from_file_location("karvey_sponsor", str(_path.SCRIPTS_DIR / "karvey-sponsor.py"))
cli = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cli)
CONN = "Server=db.example;Database=sales;" + "Pass" + "word=" + "y" * 12


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()

FIX = _path.UNIT_DIR / "fixtures" / "sponsor"
CHANGE = "sample-change"
TODAY = "2026-10-14"


class Tree:
    """A temp copy of the sponsor fixture a test can edit."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-sponsor-"))
        self.root = self.tmp / "proj"
        shutil.copytree(str(FIX), str(self.root))
        self.cdir = self.root / "docs/spec/changes" / CHANGE

    def spec(self):
        return json.loads((self.cdir / "spec.json").read_text(encoding="utf-8"))

    def write_spec(self, data):
        (self.cdir / "spec.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    def cleanup(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)


class Model(unittest.TestCase):
    """@req REQ-W3-021 REQ-W3-080"""

    def setUp(self):
        self.t = Tree()

    def tearDown(self):
        self.t.cleanup()

    def model(self):
        return sponsor.build_model(self.t.root, CHANGE, today=TODAY)

    def test_REQ_W3_021_scope_phase_cost_risks_questions_each_dated(self):
        m = self.model()
        self.assertIn("company account", m["scope"]["summary"])
        self.assertEqual(m["scope"]["areas"], ["Sign-in with the company account", "Access ends with the account"])
        self.assertEqual(m["progress"]["phase"], "Technical design")
        self.assertEqual((m["cost"]["usd"], m["cost"]["estimated_share"], m["cost"]["judge_usd"]), (41.2, 0.25, 2.1))
        self.assertEqual(m["risks"]["open"], 1)
        for sec in ("scope", "progress", "cost", "risks", "waiting"):
            self.assertRegex(m[sec]["as_of"] or "", r"^\d{4}-\d{2}-\d{2}$", sec)

    def test_REQ_W3_021_owner_matched_by_role_or_name_case_insensitively(self):
        qs = self.model()["waiting"]["questions"]
        # Q-01 owner "area lead" = the sponsor's name; Q-02 is someone else's; Q-03 resolved; Q-04 another change
        self.assertEqual([q["question"] for q in qs], ["Should people who leave lose access the same day?"])
        self.assertTrue(qs[0]["overdue"])
        self.assertIn("nightly check", qs[0]["context"])

    def test_REQ_W3_021_sponsor_who_is_the_approver_sees_the_pending_gate(self):
        self.assertEqual(self.model()["waiting"]["gates"], [{"step": "Technical design", "gate": "how"}])

    def test_sponsor_who_is_not_the_approver_sees_no_gate(self):
        pj = self.t.root / "docs/spec/project.json"
        data = json.loads(pj.read_text(encoding="utf-8"))
        data["stakeholders"]["approver"]["name"] = "Someone else"
        pj.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.model()["waiting"]["gates"], [])

    def test_REQ_W3_021_no_effort_is_not_measured(self):
        s = self.t.spec()
        del s["effort"]
        self.t.write_spec(s)
        c = self.model()["cost"]
        self.assertEqual((c["measured"], c["text"]), (False, "Not measured"))
        self.assertNotIn("usd", c)

    def test_REQ_W3_021_ids_paths_and_commands_removed_from_the_body(self):
        body = json.dumps({k: v for k, v in self.model().items() if k != "change"})
        self.assertNotRegex(body, r"\b(?:REQ-[A-Z0-9-]+|F-\d+|D-\d+|Q-\d+|R-\d+)\b")
        self.assertNotIn("docs/spec", body)
        self.assertNotIn("purge", body)

    def test_REQ_W3_080_risk_state_through_the_wording_table(self):
        states = [r["state"] for r in self.model()["risks"]["items"]]
        self.assertEqual(states, ["being watched", "reduced"])

    def test_spanish_change_uses_the_spanish_wording(self):
        s = self.t.spec()
        s["language"] = "es"
        self.t.write_spec(s)
        m = self.model()
        self.assertEqual((m["progress"]["phase"], m["risks"]["items"][1]["state"]), ("Diseño técnico", "reducido"))

    def test_unlisted_language_falls_back_to_english_with_a_note(self):
        s = self.t.spec()
        s["language"] = "it"
        self.t.write_spec(s)
        m = self.model()
        self.assertEqual(m["language"], "en")
        self.assertTrue(m["language_note"])


class Cli(unittest.TestCase):
    """@req REQ-W3-022 REQ-W3-023 — ``karvey-sponsor.py build|deliver``."""

    def setUp(self):
        self.t = Tree()
        self.page = self.t.cdir / "sponsor.html"

    def tearDown(self):
        self.t.cleanup()

    def build(self, gate="how"):
        return run("build", CHANGE, "--gate", gate, "--root", str(self.t.root))

    def lines(self, name):
        p = self.t.cdir / name
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.is_file() else []

    def test_REQ_W3_022_clean_change_writes_the_page_and_a_history_line(self):
        code, out, _ = self.build()
        self.assertEqual(code, 0, out)
        self.assertIn("leak check PASS", out)
        h = self.lines("sponsor-history.jsonl")
        self.assertEqual((h[0]["gate"], h[0]["outcome"]), ("how", "approved"))
        self.assertEqual(h[0]["sha256"], hashlib.sha256(self.page.read_bytes()).hexdigest())
        html = self.page.read_text(encoding="utf-8")
        self.assertIn("Waiting for you", html)
        self.assertEqual(html.count("<table>"), html.count('<div class="table-scroll"><table>'))

    def test_REQ_W3_023_a_leaked_connection_string_refuses_and_keeps_the_last_page(self):
        self.build()
        before = self.page.read_bytes()
        risks = self.t.cdir / "risks.md"
        risks.write_text(risks.read_text(encoding="utf-8").replace("Sign-in records kept longer than allowed",
                                                                   "The job reads " + CONN), encoding="utf-8")
        code, out, err = self.build()
        self.assertEqual(code, 3)
        self.assertEqual(self.page.read_bytes(), before)
        self.assertIn("risks.items[1].description", err)
        ref = self.lines("sponsor-refusals.jsonl")
        self.assertIn({"field": "risks.items[1].description", "rule": "secret"},
                      [{"field": r["field"], "rule": r["rule"]} for r in ref])
        self.assertNotIn("y" * 12, (self.t.cdir / "sponsor-refusals.jsonl").read_text(encoding="utf-8") + out + err)
        self.assertEqual(len(self.lines("sponsor-history.jsonl")), 1)

    def test_no_page_written_on_a_first_refusal(self):
        risks = self.t.cdir / "risks.md"
        risks.write_text(risks.read_text(encoding="utf-8") + "| R-3 | served from reports.internal | Low | Low "
                         "| owner | t | m | open | 2026-10-13 |\n", encoding="utf-8")
        code, _, err = self.build()
        self.assertEqual(code, 3)
        self.assertFalse(self.page.exists())
        self.assertIn("rule: host", err)

    def test_a_path_in_free_text_is_removed_by_the_normaliser_before_the_check(self):
        risks = self.t.cdir / "risks.md"
        risks.write_text(risks.read_text(encoding="utf-8") + "| R-3 | kept in " + "/" + "srv/data/x.db | Low | Low "
                         "| owner | t | m | open | 2026-10-13 |\n", encoding="utf-8")
        code, _, _ = self.build()
        self.assertEqual(code, 0)
        self.assertNotIn("srv/data", self.page.read_text(encoding="utf-8"))

    def test_REQ_W3_022_no_sponsor_is_said_once_per_change(self):
        pj = self.t.root / "docs/spec/project.json"
        data = json.loads(pj.read_text(encoding="utf-8"))
        del data["stakeholders"]
        pj.write_text(json.dumps(data), encoding="utf-8")
        code1, out1, _ = self.build("what")
        code2, out2, _ = self.build("how")
        self.assertEqual((code1, code2), (0, 0))
        self.assertEqual((out1 + out2).count("no sponsor declared"), 1)
        self.assertFalse(self.page.exists())

    def test_deliver_prints_the_checked_payload(self):
        code, out, _ = run("deliver", CHANGE, "--root", str(self.t.root), "--json")
        res = json.loads(out)["result"]
        self.assertEqual(code, 0)
        self.assertEqual(res["payload"]["attachment"], "docs/spec/changes/sample-change/sponsor.html")
        self.assertEqual(res["destination"], {"channel": "email", "target": "sponsor@example.org"})
        self.assertNotIn("://", out)

    def test_F74_a_payload_with_a_leaked_value_is_not_printed(self):
        leaky = ({"channel": "email", "change": CHANGE, "subject": "s", "summary": "see " + CONN}, {"channel": "email"})
        with mock.patch.object(cli, "payload_of", return_value=leaky):
            code, out, err = run("deliver", CHANGE, "--root", str(self.t.root))
        self.assertEqual(code, 3)
        self.assertNotIn("y" * 12, out + err)
        self.assertNotIn("summary", out)


if __name__ == "__main__":
    unittest.main()
