"""karvey-security-scan.py: fixed catalogue, first tool on PATH, not evaluated / not applicable (C-15).

@req REQ-W2-064 REQ-W2-065 REQ-W2-066 REQ-W2-067
"""
import contextlib
import importlib.util
import io
import json
import os
import unittest
from unittest import mock

import _path
import _gitrepo as g

g.isolate_git()
_SPEC = importlib.util.spec_from_file_location("karvey_security_scan", str(_path.SCRIPTS_DIR / "karvey-security-scan.py"))
ss = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ss)
STUBS = str(_path.Path(__file__).resolve().parent / "stubs" / "security")
EMPTY_BIN = None


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "repo")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"}})
        g.write(self.root, "docs/spec/changes/feat-a/spec.json", {"change_id": "feat-a", "phase": "qa"})
        g.write(self.root, "src/app.py", "print('x')\n")
        g.commit_all(self.root, "base")
        empty = self.t.path / "empty-bin"
        empty.mkdir()
        self.env = {"PATH": os.pathsep.join([STUBS, str(empty), "/usr/bin", "/bin"]), "KARVEY_STUB_SEC_RC": "0",
                    "KARVEY_STUB_SEC_REPORT": "[]", "KARVEY_STUB_SEC_LOG": str(self.t.path / "calls.log")}

    def tearDown(self):
        self.t.cleanup()

    def scan(self, *extra, env=None):
        e = dict(self.env)
        e.update(env or {})
        out = io.StringIO()
        with mock.patch.dict(os.environ, e), mock.patch.object(ss.shutil, "which", self.which(e["PATH"])), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = ss.main(["run", "feat-a", "--root", str(self.root), "--json"] + list(extra))
        env_ = json.loads(out.getvalue())
        return code, env_, {r["category"]: r for r in (env_.get("result") or {}).get("categories", [])}

    @staticmethod
    def which(path):
        dirs = path.split(os.pathsep)

        def _which(name):
            if name in ("semgrep", "trufflehog", "osv-scanner", "npm", "trivy"):  # never a real scanner here
                return None
            for d in dirs:
                p = os.path.join(d, name)
                if os.path.isfile(p) and os.access(p, os.X_OK):
                    return p
            return None
        return _which


class Run(Base):
    def test_REQ_W2_064_stub_scanner_cites_command_version_and_zero_findings(self):
        code, env, by = self.scan("--categories", "secrets")
        self.assertEqual(code, 0, env)
        r = by["secrets"]
        self.assertEqual((r["status"], r["tool"], r["findings"]), ("evaluated", "gitleaks", 0))
        self.assertEqual(r["version"], "gitleaks stub 1.2.3")
        self.assertEqual(r["argv"][:2], ["gitleaks", "detect"])
        self.assertTrue(r["evidence"].startswith("evidence.jsonl:"))
        ev = (self.root / "docs/spec/changes/feat-a/evidence.jsonl").read_text().splitlines()
        self.assertEqual(json.loads(ev[-1])["label"], "security:secrets:gitleaks")
        self.assertTrue((self.root / r["report"]).is_file())

    def test_findings_are_counted_by_severity(self):
        rep = json.dumps({"results": [{"issue_severity": "HIGH"}, {"issue_severity": "LOW"}]})
        _, _, by = self.scan("--categories", "sast", env={"KARVEY_STUB_SEC_REPORT": rep, "KARVEY_STUB_SEC_RC": "1"})
        self.assertEqual(by["sast"]["findings_by_severity"], {"high": 1, "low": 1})

    def test_REQ_W2_064_tool_error_is_not_evaluated_never_pass(self):
        _, _, by = self.scan("--categories", "secrets", env={"KARVEY_STUB_SEC_RC": "2"})
        self.assertEqual(by["secrets"]["status"], "not evaluated (tool error)")
        self.assertIsNone(by["secrets"]["findings"])
        hits = (self.root / "docs/spec/changes/feat-a/checks.jsonl").read_text().splitlines()
        self.assertEqual(json.loads(hits[-1])["check"], "security.tools")

    def test_unreadable_report_is_tool_error(self):
        _, _, by = self.scan("--categories", "sast", env={"KARVEY_STUB_SEC_REPORT": "not json"})
        self.assertEqual(by["sast"]["status"], "not evaluated (tool error)")

    def test_REQ_W2_065_no_tool_is_not_evaluated(self):
        _, env, by = self.scan("--categories", "sca,secrets", env={"PATH": "/usr/bin:/bin"})
        g.write(self.root, "requirements.txt", "x==1\n")
        g.commit_all(self.root, "deps")
        _, env, by = self.scan("--categories", "sca,secrets", env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(by["secrets"]["status"], "not evaluated (no tool)")
        self.assertEqual(by["sca"]["status"], "not evaluated (no tool)")
        self.assertEqual(env["result"]["not_evaluated"], ["sca", "secrets"])

    def test_REQ_W2_065_no_iac_files_is_not_applicable(self):
        _, _, by = self.scan("--categories", "iac")
        self.assertEqual(by["iac"]["status"], "not applicable")
        g.write(self.root, "infra/main.tf", "resource \"x\" \"y\" {}\n")
        g.commit_all(self.root, "iac")
        _, _, by = self.scan("--categories", "iac", env={"KARVEY_STUB_SEC_REPORT": "{\"results\": {}}"})
        self.assertEqual((by["iac"]["status"], by["iac"]["tool"]), ("evaluated", "checkov"))

    def test_REQ_W2_067_project_value_with_semicolon_refused(self):
        g.write(self.root, "docs/spec/project.json", {"security": {"tools": {"secrets": ["gitleaks; rm -rf /"]}}})
        code, env, _ = self.scan()
        self.assertEqual(code, 3)
        self.assertIn("shell metacharacter", env["errors"][0]["message"])
        self.assertFalse((self.t.path / "calls.log").exists())

    def test_REQ_W2_067_no_catalogue_command_replaceable(self):
        for bad in ({"secrets": [["sh", "-c", "id"]]}, {"secrets": "gitleaks detect"},
                    {"secrets": ["my-scanner"]}, {"shell": ["gitleaks"]}):
            g.write(self.root, "docs/spec/project.json", {"security": {"tools": bad}})
            code, env, _ = self.scan()
            self.assertEqual(code, 3, (bad, env))
        self.assertFalse((self.t.path / "calls.log").exists())

    def test_project_can_choose_among_catalogue_ids(self):
        g.write(self.root, "docs/spec/project.json", {"security": {"tools": {"sast": ["bandit"]}}})
        _, _, by = self.scan("--categories", "sast", env={"KARVEY_STUB_SEC_REPORT": "{\"results\": []}"})
        self.assertEqual(by["sast"]["tool"], "bandit")

    def test_catalogue_templates_use_only_the_two_placeholders(self):
        for c, d in ss.catalogue()["categories"].items():
            for t in d["tools"]:
                self.assertIsInstance(t["run_argv"], list)
                ss.build_argv(t["run_argv"], "/r", "/o")  # raises on any other placeholder
        with self.assertRaises(ss.Refused):
            ss.build_argv(["x", "{cmd}"], "/r", "/o")

    def test_unknown_category_refused(self):
        code, _, _ = self.scan("--categories", "dast")
        self.assertEqual(code, 3)


class Suppressions(Base):
    def validate(self, entries):
        p = self.root / "docs/spec/changes/feat-a/qa"
        p.mkdir(parents=True, exist_ok=True)
        (p / "suppressions.json").write_text(json.dumps(entries), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = ss.main(["validate-suppressions", "feat-a", "--root", str(self.root), "--json"])
        return code, json.loads(out.getvalue())["result"]

    def test_REQ_W2_066_fixture_key_suppressed_with_file_and_reason(self):
        code, r = self.validate([{"tool": "gitleaks", "rule": "generic-api-key", "path": "tests/fixtures/key.pem",
                                  "reason": "test fixture key, never deployed", "scope": "this file"}])
        self.assertEqual((code, r["problems"]), (0, []))

    def test_REQ_W2_066_suppression_without_reason_or_scope_reported(self):
        code, r = self.validate([{"tool": "gitleaks", "rule": "r", "path": "a.py", "reason": " ", "scope": "file"},
                                 {"tool": "bandit", "rule": "B101", "path": "b.py", "reason": "assert in tests"}])
        self.assertEqual(code, 1)
        self.assertEqual(len(r["problems"]), 2)
        self.assertIn("no reason", r["problems"][0])
        self.assertIn("no scope", r["problems"][1])

    def test_no_file_is_fine(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ss.main(["validate-suppressions", "feat-a", "--root", str(self.root)])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
