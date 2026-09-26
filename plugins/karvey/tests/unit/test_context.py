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
        # ob-0 is not pending any more, so ob-2 is ready (the karvey-config.py rule, karvey_lib.outbox)
        self.assertEqual([e["state"] for e in ow["outbox"]["feat-a"]], ["ready", "ready"])

    def test_outbox_written_by_karvey_config_reads_the_same(self):  # D2: one format, one ready/blocked rule
        import _config as C
        self.write("docs/spec/changes/feat-a/tracker-outbox.jsonl", "")
        add = lambda *a: C.run_json("outbox", "add", "feat-a", "--root", self.root, *a)[1]["result"]  # noqa: E731
        epic = add("--op", "create_epic", "--key", "E1", "--error", "HTTP 503")
        feat = add("--op", "create_feature", "--key", "E1.F1", "--parent-key", "E1")
        cfg = C.run_json("outbox", "list", "feat-a", "--root", self.root)[1]["result"]
        ob = self.dash("--section", "open-work")[1]["result"]["open-work"]["outbox"]["feat-a"]
        self.assertEqual([(e["id"], e["state"], e["key"]) for e in ob],
                         [(epic["id"], "ready", "E1"), (feat["id"], "blocked", "E1.F1")])
        self.assertEqual((cfg["ready"], cfg["blocked"]), ([epic["id"]], [feat["id"]]))
        self.assertIn("blocked_by " + epic["id"], self.text("--section", "open-work")[1])
        C.run_json("outbox", "done", "feat-a", epic["id"], "--root", self.root)  # applied → removed
        ob = self.dash("--section", "open-work")[1]["result"]["open-work"]["outbox"]["feat-a"]
        self.assertEqual([(e["id"], e["state"]) for e in ob], [(feat["id"], "ready")])
        self.assertNotIn("blocked_by", self.text("--section", "open-work")[1])

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
                                             "tasks", "qa", "prod"])  # wave2: approvals.deploy retired

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

    def test_opt_in_guard_on_when_only_the_reviewed_line_enables_it(self):  # same rule as the guards (F-10)
        pj = json.loads((self.root / "docs/spec/project.json").read_text())
        pj["enforcement"] = {"git_flow_hook": True}
        self.write("docs/spec/project.json", pj)
        g.init(self.root, branch="main")
        g.commit_all(self.root)
        g.with_origin(self.root, "main")
        g.run(["fetch", "-q", "origin"], self.root)
        pj["enforcement"] = {}
        self.write("docs/spec/project.json", pj)  # the working copy no longer says so; origin/main does
        enf = self.dash("--section", "enforcement")[1]["result"]["enforcement"]
        self.assertEqual((enf["git_flow"]["state"], enf["plan_gate"]["state"]), ("on", "off"))

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


def plan(rows):
    head = ("| Task | Status | estimate_min | actual_ai_min | actual_review_min | Notes |\n"
            "|------|--------|--------------|---------------|-------------------|-------|\n")
    return "# Plan\n\n## Task status\n\n" + head + "".join(
        "| %s | ✅ done | %s | %s | %s | |\n" % r for r in rows)


class Calibration(Base):
    def archive(self, name, rows):
        self.write("docs/spec/changes/archive/%s/PLAN.md" % name, plan(rows))
        self.write("docs/spec/changes/archive/%s/IMPLEMENTED" % name, "")

    def three(self, devs):
        for i, d in enumerate(devs, 1):
            # Backend: estimate 100 → actual 100 + d; the Test row stays on target; [human] is skipped
            self.archive("2026-0%d-01-ch%d" % (i, i), [("E1.F1.T1 [Backend]", "60", str(40 + d), "20"),
                                                      ("E1.F1.T2 [Backend]", "40", "20", "20"),
                                                      ("E1.F1.T3 [Test]", "10", "5", "5"),
                                                      ("E1.F1.T4 [human]", "—", "—", "—")])

    def test_three_changes_over_threshold_propose(self):
        self.three([45, 38, 40])
        code, env = self.dash("--section", "calibration")
        self.assertEqual(code, 0)
        c = env["result"]["calibration"]
        self.assertTrue(c["enough_history"])
        self.assertEqual([p["type"] for p in c["proposals"]], ["Backend"])
        self.assertEqual(c["proposals"][0]["deviations_pct"], [45.0, 38.0, 40.0])
        _, out, _ = self.text("--section", "calibration")
        self.assertIn("recalibrate Backend", out)

    def test_one_change_within_threshold_no_proposal(self):
        self.three([45, 10, 40])
        _, env = self.dash("--section", "calibration")
        self.assertEqual(env["result"]["calibration"]["proposals"], [])

    def test_fewer_than_window_not_enough_history(self):
        self.archive("2026-01-01-ch1", [("E1.F1.T1 [Backend]", "60", "80", "20")])
        self.archive("2026-02-01-ch2", [("E1.F1.T1 [Backend]", "60", "80", "20")])
        _, env = self.dash("--section", "calibration")
        c = env["result"]["calibration"]
        self.assertFalse(c["enough_history"])
        self.assertEqual(len(c["changes"]), 2, "the ratios are still reported")
        self.assertEqual(c["changes"][0]["types"]["Backend"]["ratio"], round(100 / 60, 3))
        _, out, _ = self.text("--section", "calibration")
        self.assertIn("not enough history (2 of 3", out)

    def test_threshold_and_window_from_project_json(self):
        self.three([45, 38, 40])
        pj = json.loads((self.root / "docs/spec/project.json").read_text())
        pj["calibration"] = {"threshold_pct": 50, "window": 2}
        self.write("docs/spec/project.json", pj)
        _, env = self.dash("--section", "calibration")
        c = env["result"]["calibration"]
        self.assertEqual((c["threshold_pct"], c["window"], c["proposals"]), (50, 2, []))


class CloseReport(Base):
    def test_closed_task_without_actual_is_listed(self):
        code, env = self.dash("--section", "close-report", "--change", "feat-a")
        self.assertEqual(code, 0)
        m = env["result"]["close-report"]["feat-a"]["missing"]
        self.assertEqual([x["task"] for x in m], ["E1.F1.T3 [Backend]"])
        self.assertEqual(m[0]["missing"], ["actual_ai_min", "actual_review_min"])
        _, out, _ = self.text("--section", "close-report", "--change", "feat-a")
        self.assertIn("E1.F1.T3 [Backend] — actual missing", out)


class Convergence(Base):
    def conv(self, change="feat-a"):
        return self.dash("--section", "convergence", "--change", change)

    def test_not_converged_lists_each_offender(self):
        code, env = self.conv()
        self.assertEqual(code, 1)
        off = env["result"]["convergence"]["feat-a"]["offenders"]
        self.assertEqual([(o["kind"], o["id"]) for o in off],
                         [("finding", "F-01"), ("finding", "F-02"), ("bug", "BUG-02"), ("bug", "BUG-03")])
        self.assertEqual(off[3]["reason"], "RESUELTO without a named regression test")
        _, out, _ = self.text("--section", "convergence", "--change", "feat-a")
        self.assertIn("NOT converged, 4 offender(s)", out)

    def test_converged_exits_0(self):
        f = self.root / "docs/spec/changes/feat-a/findings.md"
        f.write_text(f.read_text().replace("| routed | BUG-02 |", "| closed | BUG-02 |")
                     .replace("| open | — |", "| closed | spec revision |"), encoding="utf-8")
        b = self.root / "docs/bugs_dev_testing.md"
        b.write_text(b.read_text().replace("EN FIX", "RESUELTO")
                     .replace("### Regression test\n—", "### Regression test\n`tests/test_x.py`"), encoding="utf-8")
        i = self.root / "docs/spec/incidents-index.md"
        i.write_text(i.read_text().replace("EN FIX", "RESUELTO").replace("| — | feat-a |", "| tests/test_x.py | feat-a |"),
                     encoding="utf-8")
        code, env = self.conv()
        self.assertEqual(code, 0, env["result"]["convergence"])
        self.assertTrue(env["result"]["convergence"]["feat-a"]["converged"])

    def test_converges_list_is_in_scope(self):
        spec = self.root / "docs/spec/changes/feat-b/spec.json"
        data = json.loads(spec.read_text())
        data["converges"] = ["feat-a"]
        spec.write_text(json.dumps(data), encoding="utf-8")
        code, env = self.conv("feat-b")
        self.assertEqual(code, 1)
        r = env["result"]["convergence"]["feat-b"]
        self.assertEqual(r["scope"], ["feat-b", "feat-a"])
        self.assertIn("F-02", [o["id"] for o in r["offenders"]])

    def test_not_in_default_run_and_default_exit_0(self):
        code, env = self.dash()
        self.assertEqual(code, 0)
        self.assertNotIn("convergence", env["result"])

    def test_read_only(self):
        before = tree_hash(self.root)
        self.conv()
        self.dash("--section", "calibration")
        self.dash("--section", "close-report")
        self.assertEqual(tree_hash(self.root), before)


class AuditBlocks(Base):
    def test_block_counts_per_guard(self):
        from karvey_lib import audit, project as pjm
        d = pjm.state_dir(self.root)
        audit.append(d, {"guard": "prod-gate", "decision": "block", "reason": "no approval"})
        audit.append(d, {"guard": "prod-gate", "decision": "block", "reason": "no approval"})
        audit.append(d, {"guard": "flow-guard", "decision": "block"})
        audit.append(d, {"guard": "prod-gate", "decision": "allow"})
        _, env = self.dash("--section", "enforcement")
        b = env["result"]["enforcement"]["blocks"]
        self.assertEqual((b["total"], b["by_guard"]), (3, {"flow-guard": 1, "prod-gate": 2}))
        _, out, _ = self.text("--section", "enforcement")
        self.assertIn("blocks     3 (flow-guard 1, prod-gate 2)", out)

    def test_no_audit_log(self):
        _, out, _ = self.text("--section", "enforcement")
        self.assertIn("blocks     none recorded", out)


class Tables(unittest.TestCase):
    def test_escaped_pipe_and_short_rows(self):
        t = ctxmod.parse_tables("| A | B | C |\n|---|---|---|\n| x \\| y | 2 |\n")
        self.assertEqual(t[0]["rows"][0]["a"], "x | y")
        self.assertEqual(t[0]["rows"][0]["c"], "")


class Layout(unittest.TestCase):
    """@req REQ-W3-048 — both spec layouts are found; with both, docs/spec/ is used."""

    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path / "repo"
        self.root.mkdir()

    def tearDown(self):
        self.t.cleanup()

    def put(self, base, cid, phase="impl", marker=False):
        d = self.root / base / "changes" / cid
        d.mkdir(parents=True, exist_ok=True)
        (d / "spec.json").write_text(json.dumps({"change_id": cid, "phase": phase}), encoding="utf-8")
        if marker:
            (d / "IMPLEMENTED").write_text("")

    def overview(self):
        code, out, _ = run("--root", str(self.root), "--section", "overview", "--now", NOW, "--json")
        self.assertEqual(code, 0, out)
        return json.loads(out)

    def test_REQ_W3_048_a_spec_folder_is_found_and_marked(self):
        (self.root / "spec").mkdir()
        (self.root / "spec/project.json").write_text("{}\n", encoding="utf-8")
        self.put("spec", "feat-a")
        self.put("spec", "feat-b", marker=True)
        self.put("spec/changes/archive", "2026-old")
        env = self.overview()
        ov = env["result"]["overview"]
        self.assertEqual(ov["layout"], "spec/")
        self.assertEqual([r["change"] for r in ov["active"]], ["feat-a"])

    def test_REQ_W3_048_two_spec_roots_use_docs_spec(self):
        self.put("docs/spec", "feat-a")
        self.put("spec", "feat-z")
        env = self.overview()
        ov = env["result"]["overview"]
        self.assertEqual((ov["layout"], ov["layout_note"]), ("docs/spec/", "two spec roots"))
        self.assertEqual([r["change"] for r in ov["active"]], ["feat-a"])
        self.assertIn("two spec roots", " ".join(w["message"] for w in env["warnings"]))


if __name__ == "__main__":
    unittest.main()
