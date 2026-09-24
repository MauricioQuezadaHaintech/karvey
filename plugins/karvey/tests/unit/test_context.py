"""karvey-context.py: the read-only dashboard (REQ-W1-026, 043, 044, 068..072, 090, 107, 108)."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import unittest
from pathlib import Path

import _path
import _gitrepo as g

g.isolate_git()

_SPEC = importlib.util.spec_from_file_location("karvey_context", str(_path.SCRIPTS_DIR / "karvey-context.py"))
ctxmod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ctxmod)

FIXTURE = _path.UNIT_DIR / "fixtures" / "context"
NOW = "2026-09-24T12:00:00+00:00"


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ctxmod.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def tree_hash(root):
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames.sort()
        for n in sorted(filenames):
            p = Path(dirpath) / n
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path / "proj"
        shutil.copytree(str(FIXTURE), str(self.root))
        self._env = os.environ.get("XDG_STATE_HOME")
        os.environ["XDG_STATE_HOME"] = str(self.t.path / "xdg")

    def tearDown(self):
        if self._env is None:
            os.environ.pop("XDG_STATE_HOME", None)
        else:
            os.environ["XDG_STATE_HOME"] = self._env
        self.t.cleanup()

    def dash(self, *extra):
        code, out, _ = run("--root", str(self.root), "--now", NOW, "--json", *extra)
        return code, json.loads(out)

    def text(self, *extra):
        return run("--root", str(self.root), "--now", NOW, *extra)

    def write(self, rel, content):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if isinstance(content, str) else json.dumps(content, indent=2) + "\n", encoding="utf-8")


class OpenWork(Base):
    def test_findings_by_type_and_status(self):
        code, env = self.dash("--section", "open-work")
        self.assertEqual(code, 0)
        f = env["result"]["open-work"]["findings"]
        self.assertEqual(f["feat-a"]["counts"], {"bug": {"closed": 1, "routed": 1}, "emergent": {"routed": 1},
                                                 "spec-gap": {"open": 1}})
        self.assertEqual(f["feat-a"]["open"], ["F-01", "F-02", "F-03"])
        self.assertNotIn("feat-c", f, "an implemented change has no findings file here")

    def test_bugs_not_resuelto(self):
        _, env = self.dash("--section", "open-work")
        self.assertEqual([b["id"] for b in env["result"]["open-work"]["bugs"]], ["BUG-02"])

    def test_human_tasks_with_executor_and_since(self):
        _, env = self.dash("--section", "open-work")
        self.assertEqual(env["result"]["open-work"]["human"]["feat-a"],
                         [{"task": "E1.F1.T2 [human]", "executor": "owner", "since": "2026-09-20"}])

    def test_open_backlog_and_outbox(self):
        _, env = self.dash("--section", "open-work")
        ow = env["result"]["open-work"]
        self.assertEqual([b["id"] for b in ow["backlog"]], ["BL-02"])
        self.assertEqual([e["id"] for e in ow["outbox"]["feat-a"]], ["ob-1", "ob-2"])
        self.assertEqual(ow["outbox"]["feat-a"][1]["blocked_by"], "ob-0")

    def test_human_text(self):
        code, out, _ = self.text("--section", "open-work")
        self.assertEqual(code, 0)
        self.assertIn("bugs not RESUELTO (1): BUG-02 EN FIX", out)
        self.assertIn("awaiting human feat-a: E1.F1.T2 [human] · executor owner · since 2026-09-20", out)
        self.assertIn("tracker outbox feat-a: 2 pending", out)

    def test_unreadable_findings_shown_and_rest_renders(self):
        p = self.root / "docs/spec/changes/feat-a/findings.md"
        p.unlink()
        p.mkdir()  # reading a directory fails with an OSError on every platform
        code, env = self.dash()
        self.assertEqual(code, 0)
        un = env["result"]["unreadable"]
        self.assertEqual([u["path"] for u in un], ["docs/spec/changes/feat-a/findings.md"])
        self.assertIn("feat-b", env["result"]["open-work"]["findings"])
        self.assertIn("approvals", env["result"])
        _, out, _ = self.text()
        self.assertIn("unreadable: docs/spec/changes/feat-a/findings.md (", out)
        self.assertIn("== APPROVALS ==", out)

    def test_invalid_spec_json_is_unreadable_not_fatal(self):
        self.write("docs/spec/changes/feat-b/spec.json", "{not json")
        code, env = self.dash()
        self.assertEqual(code, 0)
        self.assertIn("docs/spec/changes/feat-b/spec.json", [u["path"] for u in env["result"]["unreadable"]])

    def test_columns_reordered_give_the_same_values(self):
        _, before = self.dash("--section", "open-work")
        self.write("docs/spec/changes/feat-a/findings.md", """# Findings

| Status | Type | # | Title | Routed to | Date | Severity | Source phase |
|---|---|---|---|---|---|---|---|
| routed | bug | F-01 | SP returns NULL on empty input | BUG-02 | 2026-09-10 | high | test |
| open | spec-gap | F-02 | timeout must be configurable | — | 2026-09-10 | — | qa |
| routed | emergent | F-03 | export the report as PDF | BL-02 | 2026-09-11 | — | browse |
| closed | bug | F-04 | typo in a label | BUG-01 (RESUELTO) | 2026-09-11 | low | qa |
""")
        _, after = self.dash("--section", "open-work")
        self.assertEqual(after["result"]["open-work"]["findings"], before["result"]["open-work"]["findings"])


class AgeAndWip(Base):
    def test_age_stalled_and_unknown(self):
        _, env = self.dash("--section", "overview")
        rows = {r["change"]: r for r in env["result"]["overview"]["active"]}
        self.assertEqual(rows["feat-a"]["age"]["text"], "9d stalled")
        self.assertTrue(rows["feat-a"]["age"]["stalled"])
        self.assertEqual(rows["feat-b"]["age"]["text"], "unknown")
        self.assertIsNone(rows["feat-b"]["age"]["days"])
        self.assertNotIn("feat-c", rows, "IMPLEMENTED changes are not active")

    def test_not_stalled_within_threshold(self):
        _, env = self.dash("--section", "overview", "--now", "2026-09-20T12:00:00+00:00")
        rows = {r["change"]: r for r in env["result"]["overview"]["active"]}
        self.assertEqual(rows["feat-a"]["age"]["text"], "5d")

    def test_wip_within_limit(self):
        code, out, _ = self.text("--section", "overview")
        self.assertIn("WIP 2/3", out)
        self.assertNotIn("WARNING", out)

    def test_wip_exceeded_warns(self):
        pj = json.loads((self.root / "docs/spec/project.json").read_text())
        pj["wip_limit"] = 1
        self.write("docs/spec/project.json", pj)
        code, env = self.dash("--section", "overview")
        self.assertEqual(code, 0)
        self.assertTrue(env["result"]["overview"]["wip"]["exceeded"])
        self.assertTrue(any(w["message"] == "WIP 2/1" for w in env["warnings"]))
        _, out, _ = self.text("--section", "overview")
        self.assertIn("WARNING WIP 2/1", out)

    def test_invalid_wip_limit_is_a_warning(self):
        pj = json.loads((self.root / "docs/spec/project.json").read_text())
        pj["wip_limit"] = 0
        self.write("docs/spec/project.json", pj)
        code, env = self.dash("--section", "overview")
        self.assertEqual(code, 0)
        self.assertIsNone(env["result"]["overview"]["wip"]["limit"])
        self.assertTrue(any(w["code"] == "context.bad_setting" for w in env["warnings"]))


class Approvals(Base):
    def rows(self, change="feat-a"):
        _, env = self.dash("--section", "approvals")
        return {r["key"]: r for r in env["result"]["approvals"][change]["approvals"]}

    def test_every_approval_requirements_to_prod(self):
        self.assertEqual(list(self.rows()), ["requirements", "mockup", "design_graphic", "architecture", "infra",
                                             "tasks", "qa", "deploy", "prod"])

    def test_skipped_with_reason(self):
        r = self.rows()
        self.assertEqual(r["mockup"]["text"], "skipped: no UI")
        self.assertEqual(r["infra"]["text"], "skipped: no cloud")

    def test_approver_missing(self):
        self.assertEqual(self.rows()["architecture"]["text"], "approved — approver missing")

    def test_who_role_date(self):
        r = self.rows()["requirements"]
        self.assertEqual((r["by"], r["role"], r["ref"]), ("Owner", "human", "D-01"))
        self.assertIn("approved by Owner (human)", r["text"])
        self.assertEqual(self.rows()["qa"]["text"], "awaiting approval")

    def test_reordered_pretty_printed_spec_json_same_values(self):
        before = self.rows()
        p = self.root / "docs/spec/changes/feat-a/spec.json"
        data = json.loads(p.read_text())
        reordered = dict(reversed(list(data.items())))
        reordered["approvals"] = dict(reversed(list(data["approvals"].items())))
        p.write_text(json.dumps(reordered, indent=7, sort_keys=False), encoding="utf-8")
        self.assertEqual(self.rows(), before)

    def test_change_filter(self):
        _, env = self.dash("--section", "approvals", "--change", "feat-b")
        self.assertEqual(list(env["result"]["approvals"]), ["feat-b"])
        self.assertEqual(run("--root", str(self.root), "--change", "nope", "--json")[0], 4)


class Enforcement(Base):
    def test_prod_gate_on_by_default(self):
        code, out, _ = self.text("--section", "enforcement")
        self.assertEqual(code, 0)
        self.assertIn("prod-gate  on (default)", out)
        self.assertNotIn("prod-gate  off", out)
        self.assertIn("marker     none", out)

    def test_prod_gate_off_only_in_working_copy_stays_on(self):
        pj = json.loads((self.root / "docs/spec/project.json").read_text())
        pj["enforcement"] = {"prod_gate_hook": False}
        self.write("docs/spec/project.json", pj)
        _, env = self.dash("--section", "enforcement")
        self.assertEqual(env["result"]["enforcement"]["prod_gate"]["state"], "on")

    def test_prod_gate_off_when_reviewed_on_origin(self):
        pj = json.loads((self.root / "docs/spec/project.json").read_text())
        pj["enforcement"] = {"prod_gate_hook": False}
        self.write("docs/spec/project.json", pj)
        g.init(self.root, branch="main")
        g.commit_all(self.root)
        g.with_origin(self.root, "main")
        g.run(["fetch", "-q", "origin"], self.root)
        _, env = self.dash("--section", "enforcement")
        self.assertEqual(env["result"]["enforcement"]["prod_gate"]["text"],
                         "off (project.json, reviewed on origin/main)")

    def test_valid_marker_shown(self):
        from karvey_lib import approval
        approval.write_marker(self.root, "plan", "feat-a", "aprobado", compat="")
        before = tree_hash(self.root)
        _, env = self.dash("--section", "enforcement", "--now",
                           approval.iso(approval.now_dt()))
        m = env["result"]["enforcement"]["marker"]
        self.assertEqual([x["state"] for x in m], ["valid"])
        self.assertEqual(tree_hash(self.root), before)


class ReadOnly(Base):
    def test_tree_unchanged_text_and_json(self):
        before = tree_hash(self.root)
        self.assertEqual(self.text()[0], 0)
        self.assertEqual(self.dash()[0], 0)
        for s in ("overview", "open-work", "approvals", "enforcement"):
            self.dash("--section", s)
        self.assertEqual(tree_hash(self.root), before)
        self.assertFalse((self.t.path / "xdg").exists(), "no state dir created either")

    def test_no_docs_spec_exit_4(self):
        empty = self.t.path / "empty"
        empty.mkdir()
        code, out, _ = run("--root", str(empty), "--json")
        self.assertEqual(code, 4)
        self.assertEqual(json.loads(out)["exit"], 4)


class Tables(unittest.TestCase):
    def test_escaped_pipe_and_short_rows(self):
        t = ctxmod.parse_tables("| A | B | C |\n|---|---|---|\n| x \\| y | 2 |\n")
        self.assertEqual(t[0]["rows"][0]["a"], "x | y")
        self.assertEqual(t[0]["rows"][0]["c"], "")


if __name__ == "__main__":
    unittest.main()
