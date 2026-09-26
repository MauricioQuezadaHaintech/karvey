"""karvey-postdeploy.py: contract parse, probes, thresholds, evidence (architecture §1.15 C-19 of wave2-structural).

A local HTTP stub on 127.0.0.1 (env `dev`, the only place plain http is accepted). No network.

@req REQ-W2-002 REQ-W2-075 REQ-W2-076 REQ-W2-077
"""
import contextlib
import http.server
import importlib.util
import io
import json
import threading
import unittest

import _path
import _gitrepo as g

_SPEC = importlib.util.spec_from_file_location("karvey_postdeploy", str(_path.SCRIPTS_DIR / "karvey-postdeploy.py"))
pd = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pd)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self.send_response(200)
        elif self.path == "/boom":
            self.send_response(500)
        elif self.path == "/away":
            self.send_response(302)
            self.send_header("Location", "https://example.invalid/steal")
        elif self.path == "/moved":
            self.send_response(301)
            self.send_header("Location", "/health")
        else:
            self.send_response(404)
        self.end_headers()

    def log_message(self, *a):
        pass


def contract(base, **over):
    c = {"service": "web", "env": "dev", "health": [base + "/health"],
         "routes": [{"url": base + "/health", "expect_status": 200}],
         "thresholds": {"error_rate_pct": 1, "p95_ms_vs_baseline_pct": 20, "new_5xx": 0}, "window_min": 1,
         "metrics_source": {"kind": "platform", "how": "the deploy skill reads the dashboard"},
         "rollback": {"command": "platform rollback web --to previous", "doc": "runbook"}}
    c.update(over)
    return c


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]
        cls.th = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.th.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path
        g.write(self.root, "docs/spec/project.json", {})
        g.write(self.root, "docs/spec/changes/feat-a/spec.json", {"change_id": "feat-a", "phase": "deploying"})

    def tearDown(self):
        self.t.cleanup()

    def infra(self, *blocks):
        text = "# Infra\n\n" + "".join("```karvey-postdeploy\n%s\n```\n\n" % json.dumps(b) for b in blocks)
        (self.root / "docs/spec/changes/feat-a/infra.md").write_text(text, encoding="utf-8")

    def cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = pd.main(list(argv) + ["--root", str(self.root), "--json"])
        return code, json.loads(out.getvalue())

    def observed(self, **v):
        p = self.t.path / "observed.json"
        p.write_text(json.dumps(v), encoding="utf-8")
        return str(p)

    def probe_and_eval(self, **obs):
        code, env = self.cli("probe", "feat-a", "--env", "dev", "--samples", "2", "--interval-s", "0")
        self.assertEqual(code, 0, env)
        return self.cli("evaluate", "feat-a", "--env", "dev", "--version", "1.2.0",
                        "--observed", self.observed(**obs))


class Verify(Base):
    def test_REQ_W2_076_all_probes_inside_thresholds_pass(self):
        self.infra(contract(self.base))
        code, env = self.probe_and_eval(error_rate_pct=0.2, p95_ms=110, baseline_p95_ms=100, new_5xx=0)
        r = env["result"]
        self.assertEqual((code, r["result"]), (0, "pass"), r)
        self.assertEqual({c["name"] for c in r["checks"]}, {"error_rate_pct", "p95_ms_vs_baseline_pct", "new_5xx"})
        text = (self.root / "docs/spec/changes/feat-a/deploy_evidence.md").read_text()
        self.assertIn("## dev", text)
        self.assertIn("Result: **pass**", text)
        self.assertIn("/health", text)
        self.assertIn("deploy-record feat-a --env dev --version 1.2.0 --verification pass", r["deploy_record"])

    def test_REQ_W2_076_error_rate_above_threshold_is_regression(self):
        self.infra(contract(self.base, routes=[{"url": self.base + "/boom", "expect_status": 200}]))
        code, env = self.probe_and_eval(p95_ms=100, baseline_p95_ms=100)
        r = env["result"]
        self.assertEqual((code, r["result"]), (1, "regression"))
        self.assertEqual(r["rollback"]["command"], "platform rollback web --to previous")
        self.assertIn("--verification regression", r["deploy_record"])

    def test_unreachable_service_is_never_pass(self):
        """@req REQ-W2-076 — BUG-52 (F-13): a probe with no HTTP status (connection refused) counts as a server
        error, so a contract whose only threshold is new_5xx cannot pass while the service is down."""
        down = "http://127.0.0.1:1"
        self.infra(contract(down, thresholds={"new_5xx": 0}, health=[down + "/health"],
                            routes=[{"url": down + "/orders", "expect_status": 200}]))
        code, env = self.probe_and_eval()
        r = env["result"]
        self.assertEqual(r["result"], "regression", r)
        self.assertEqual(code, 1)

    def test_probe_urls_are_redacted_in_the_evidence(self):
        """@req REQ-W2-076 — BUG-52 (F-13): credentials and query values of a probe URL never reach the evidence."""
        host = self.base.replace("http://", "")
        secret = "http://user:s3cr3tpw@%s/health?token=abc123" % host
        self.infra(contract(self.base, health=[secret], routes=[{"url": secret, "expect_status": 200}]))
        self.probe_and_eval(error_rate_pct=0, p95_ms=100, baseline_p95_ms=100, new_5xx=0)
        change = self.root / "docs/spec/changes/feat-a"
        for f in ("deploy_evidence.md", "postdeploy_probe_dev.json"):
            text = (change / f).read_text()
            self.assertNotIn("s3cr3tpw", text, f)
            self.assertNotIn("abc123", text, f)
            self.assertIn("/health", text, f)

    def test_observed_error_rate_alone_is_regression(self):
        self.infra(contract(self.base))
        code, env = self.probe_and_eval(error_rate_pct=4.0, p95_ms=100, baseline_p95_ms=100)
        self.assertEqual(env["result"]["result"], "regression")

    def test_REQ_W2_077_no_contract_is_not_evaluated_never_pass(self):
        code, env = self.cli("evaluate", "feat-a", "--env", "dev", "--observed", self.observed(error_rate_pct=0))
        r = env["result"]
        self.assertEqual((code, r["result"]), (0, "not-evaluated"))
        self.assertTrue(any("add a post-deploy contract" in n for n in r["notes"]))
        self.assertIn("Result: **not-evaluated**",
                      (self.root / "docs/spec/changes/feat-a/deploy_evidence.md").read_text())

    def test_REQ_W2_077_contract_without_thresholds_is_not_evaluated(self):
        self.infra(contract(self.base, thresholds={}))
        _, env = self.probe_and_eval(error_rate_pct=0)
        self.assertEqual(env["result"]["result"], "not-evaluated")

    def test_REQ_W2_075_contract_without_rollback_reported_incomplete(self):
        self.infra(contract(self.base, rollback={}))
        code, env = self.cli("probe", "feat-a", "--env", "dev", "--samples", "1", "--interval-s", "0")
        self.assertIn("no rollback command", env["result"]["problems"])
        _, env = self.cli("evaluate", "feat-a", "--env", "dev")
        self.assertTrue(any("contract incomplete" in n for n in env["result"]["notes"]))

    def test_redirect_to_another_host_not_followed(self):
        self.infra(contract(self.base, routes=[{"url": self.base + "/away", "expect_status": 200}],
                            health=[self.base + "/moved"]))
        _, env = self.cli("probe", "feat-a", "--env", "dev", "--samples", "1", "--interval-s", "0")
        by = {p["url"].rsplit("/", 1)[-1]: p for p in env["result"]["probes"]}
        self.assertEqual(by["away"]["status"], 302)
        self.assertFalse(by["away"]["ok"])
        self.assertIn("not followed", by["away"]["error"])
        self.assertEqual(by["moved"]["status"], 200)  # same host: followed

    def test_plain_http_refused_in_prod(self):
        self.infra(contract(self.base, env="prod"))
        code, env = self.cli("probe", "feat-a", "--env", "prod", "--samples", "1")
        self.assertEqual(code, 3)
        self.assertIn("https:// only", env["errors"][0]["message"])

    def test_evidence_sections_per_env(self):
        self.infra(contract(self.base))
        self.probe_and_eval(error_rate_pct=0, p95_ms=100, baseline_p95_ms=100)
        self.cli("evaluate", "feat-a", "--env", "prod")
        text = (self.root / "docs/spec/changes/feat-a/deploy_evidence.md").read_text()
        self.assertEqual(text.count("## dev"), 1)
        self.assertEqual(text.count("## prod"), 1)
        self.probe_and_eval(error_rate_pct=0, p95_ms=100, baseline_p95_ms=100)
        self.assertEqual((self.root / "docs/spec/changes/feat-a/deploy_evidence.md").read_text().count("## dev"), 1)

    def test_new_5xx_without_probe_or_observed_value_is_not_evaluated(self):
        """@req REQ-W2-077 — BUG-52 (F-13): with no probe run and no observed new_5xx nothing was measured, so the
        new_5xx threshold is a note, never a passing check."""
        self.infra(contract(self.base, thresholds={"new_5xx": 0}))
        code, env = self.cli("evaluate", "feat-a", "--env", "dev", "--observed", self.observed(p95_ms=100))
        r = env["result"]
        self.assertEqual((code, r["result"]), (0, "not-evaluated"), r)
        self.assertEqual(r["checks"], [])
        self.assertIn("new_5xx not evaluated (no probe, no observed value)", r["notes"])

    def test_non_numeric_threshold_is_not_evaluated_not_a_crash(self):
        """@req REQ-W2-075 — BUG-52 (F-13): a threshold that is not a number is a contract problem naming the key,
        the verdict is not-evaluated and the exit is never 1 (1 means only regression)."""
        self.infra(contract(self.base, thresholds={"error_rate_pct": "5", "new_5xx": 0}))
        code, env = self.probe_and_eval(error_rate_pct=0, new_5xx=0)
        r = env["result"]
        self.assertEqual((code, r["result"]), (0, "not-evaluated"), env)
        self.assertTrue(any("error_rate_pct" in n and "not a number" in n for n in r["notes"]), r["notes"])

    def test_malformed_probe_file_counts_as_no_probes(self):
        """@req REQ-W2-076 — BUG-52 (F-13): a probe file that is a JSON list, or holds non-dict rows, is read as
        no probes with a note — never a traceback."""
        self.infra(contract(self.base, thresholds={"new_5xx": 0}))
        pp = self.root / "docs/spec/changes/feat-a/postdeploy_probe_dev.json"
        for body in ("[1, 2]", json.dumps({"probes": ["x", 3]}), json.dumps({"probes": "nope"})):
            pp.write_text(body, encoding="utf-8")
            code, env = self.cli("evaluate", "feat-a", "--env", "dev", "--observed", self.observed(new_5xx=0))
            self.assertEqual(code, 0, env)
            r = env["result"]
            self.assertTrue(any("probe file" in n for n in r["notes"]), (body, r["notes"]))
            self.assertEqual(r["result"], "pass", r)  # the observed new_5xx is still a real measurement

    def test_internal_error_is_an_error_envelope_not_exit_1(self):
        """BUG-52 (F-13): an unexpected exception comes out as the tool's internal-error envelope (exit 5)."""
        self.infra(contract(self.base))
        orig = pd.evaluate
        pd.evaluate = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            code, env = self.cli("evaluate", "feat-a", "--env", "dev")
        finally:
            pd.evaluate = orig
        self.assertEqual(code, 5)
        self.assertEqual(env["errors"][0]["code"], "internal")

    def test_infra_text_is_never_executed(self):
        src = (_path.SCRIPTS_DIR / "karvey-postdeploy.py").read_text()
        self.assertNotIn("subprocess", src)
        self.assertNotIn("os.system", src)


if __name__ == "__main__":
    unittest.main()
