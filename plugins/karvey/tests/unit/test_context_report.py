"""``karvey-context.py --report`` (architecture §1.14, C-14): the business-language status. Read-only.

@req REQ-W3-025
"""
import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
import shutil
from pathlib import Path

import _path
import _gitrepo as g

g.isolate_git()
_SPEC = importlib.util.spec_from_file_location("karvey_context_r", str(_path.SCRIPTS_DIR / "karvey-context.py"))
ctxmod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ctxmod)
T = "2026-10-%02dT10:00:00-03:00"


def run_ctx(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = ctxmod.main(list(argv))
    return code, out.getvalue()


def spec(cid, phase, client, created=1, deploys=None):
    return {"schema_version": 1, "change_id": cid, "phase": phase, "lane": "standard", "client": client,
            "created_at": T % created,
            "phase_history": [{"phase": "init", "entered_at": T % created, "exited_at": T % created},
                              {"phase": phase, "entered_at": T % (created + 2)}],
            "approvals": {}, "deploys": deploys or []}


class Report(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-report-"))
        self.root = g.init(self.tmp / "repo")
        g.write(self.root, "docs/spec/project.json", {"notifications": {"channel": "none"},
                                                       "management": {"tool": "markdown"}})
        g.write(self.root, "docs/spec/changes/archive/2026-10-05-first/spec.json",
                spec("first", "archived", "sample-client-a", deploys=[
                    {"env": "prod", "version": "1.4.0", "at": T % 5, "verification": "pass"}]))
        g.write(self.root, "docs/spec/changes/second/spec.json", spec("second", "architecture", "sample-client-a", 3))
        g.write(self.root, "docs/spec/changes/third/spec.json", spec("third", "impl", "sample-client-a", 6))
        g.write(self.root, "docs/spec/changes/third/PLAN.md",
                "## Task status\n\n| Task | Status | estimate_min | actual_ai_min | actual_review_min | Notes |\n"
                "|---|---|---|---|---|---|\n| E1.F1.T1 | ✅ done | 5 | 4 | 1 |  |\n"
                "| E1.F1.T2 | 🙋 awaiting-human | 5 | — | — | executor: operator (since 2026-10-10) |\n")
        g.write(self.root, "docs/spec/changes/second/risks.md",
                "| ID | Risk | Probability | Impact | Owner | Trigger | Mitigation | State | Last review |\n"
                "|---|---|---|---|---|---|---|---|---|\n"
                "| R-1 | The provider changes its sign-in (see D-3) | Low | High | tech lead | notice | watch | open | "
                "2026-10-09 |\n| R-2 | Old risk | Low | Low | tech lead | t | m | closed | 2026-10-09 |\n")
        g.write(self.root, "docs/spec/questions.md",
                "| ID | Question | Owner | Needed by | Changes | Context | State | Resolved by |\n"
                "|---|---|---|---|---|---|---|---|\n"
                "| Q-01 | Keep the old screen? | sponsor | 2026-10-20 | second | — | open | — |\n"
                "| Q-02 | Log retention? | tech lead | 2026-10-22 | third | — | open | — |\n")
        g.run(["add", "-A"], self.root)
        g.run(["commit", "-q", "-m", "fixture"], self.root)

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def report(self, *extra):
        code, out = run_ctx("--root", str(self.root), "--report", "--from", "2026-10-01", "--to", "2026-10-14",
                            "--as-of", "2026-10-14", *extra)
        return code, out

    def test_REQ_W3_025_released_and_in_progress_sections(self):
        code, out = self.report("--json")
        self.assertEqual(code, 0)
        r = json.loads(out)["result"]
        self.assertEqual(r["released"], [{"change": "first", "version": "1.4.0", "date": "2026-10-05"}])
        self.assertEqual([(c["change"], c["phase"], c["age_days"]) for c in r["in_progress"]],
                         [("second", "Technical design", 11), ("third", "Build", 8)])
        self.assertEqual(r["blocked"], [{"change": "third", "task": "E1.F1.T2", "unblocks": "operator"}])
        self.assertEqual(r["open_risks"], [{"change": "second", "risk": "The provider changes its sign-in",
                                            "owner": "tech lead", "state": "being watched"}])
        self.assertEqual(sorted(r["decisions_awaited"]), ["sponsor", "tech lead"])

    def test_human_table_uses_business_wording(self):
        code, out = self.report()
        self.assertIn("second — Technical design · 11 days", out)
        self.assertIn("unblocks: operator", out)
        self.assertNotIn("architecture", out)

    def test_REQ_W3_025_unknown_client_says_so_and_exits_0(self):
        code, out = self.report("--client", "nobody-here")
        self.assertEqual(code, 0)
        self.assertIn("no changes for client nobody-here", out)

    def test_REQ_W3_025_read_only_and_reproducible(self):
        a = self.report("--json")
        b = self.report("--json")
        self.assertEqual(a, b)
        st = subprocess.run(["git", "status", "--porcelain"], cwd=str(self.root), capture_output=True, text=True)
        self.assertEqual(st.stdout, "")


if __name__ == "__main__":
    unittest.main()
