"""The read-only Probe and the plan (REQ-UP-005, 007, 009, 010, 016)."""
import hashlib
import json
import os
import shutil
import subprocess
import time
import unittest
from pathlib import Path
from unittest import mock

import _gitrepo as g
import _path  # noqa: F401
from karvey_lib import upgrade


class ProbeReads(unittest.TestCase):
    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "proj")
        g.write(self.root, "docs/spec/project.json", {"a": 1})
        g.write(self.root, "notes.txt", "hello\n")
        self.outside = self.t.path / "outside.txt"
        self.outside.write_text("secret\n", encoding="utf-8")
        self.home = self.t.path / "home"
        g.write(self.home, ".claude/settings.json", {"statusLine": {"command": "x"}})
        g.write(self.home, ".ssh/id", "key\n")

    def tearDown(self):
        self.t.cleanup()

    def probe(self, **kw):
        return upgrade.Probe(self.root, home=self.home, **kw)

    def test_reads_only_under_the_root(self):
        p = self.probe()
        self.assertEqual(p.read_text("notes.txt"), "hello\n")
        self.assertIsNone(p.read_text("absent.txt"))
        for bad in ("../outside.txt", "/etc/hostname", str(self.outside), "docs/../../outside.txt"):
            with self.subTest(path=bad):
                with self.assertRaises(upgrade.ProbeError):
                    p.read_text(bad)

    def test_a_symlink_out_of_the_root_is_refused(self):
        os.symlink(str(self.outside), str(self.root / "link.txt"))
        with self.assertRaises(upgrade.ProbeError):
            self.probe().read_text("link.txt")

    def test_read_json_keeps_format_and_hash(self):
        doc = self.probe().read_json("docs/spec/project.json")
        self.assertEqual(doc.data, {"a": 1})
        self.assertEqual(doc.fmt["indent"], 2)
        self.assertEqual(doc.dumps(doc.data), (self.root / "docs/spec/project.json").read_text(encoding="utf-8"))
        g.write(self.root, "bad.json", "{nope")
        with self.assertRaises(upgrade.CheckFailed):
            self.probe().read_json("bad.json")

    def test_git_read_allow_list_and_no_shell(self):
        p = self.probe()
        rc, out = p.git_read("rev-parse", "--show-toplevel")
        self.assertEqual(rc, 0)
        self.assertEqual(os.path.realpath(out.strip()), str(self.root))
        for bad in (("commit", "-m", "x"), ("push",), ("checkout", "-b", "x"), ("config", "user.name", "x"),
                    ("status",), ("reset", "--hard")):
            with self.subTest(args=bad):
                with self.assertRaises(upgrade.ProbeError):
                    p.git_read(*bad)
        calls = []
        real = subprocess.run

        def spy(*a, **kw):
            calls.append((a, kw))
            return real(*a, **kw)
        with mock.patch.object(upgrade.subprocess, "run", side_effect=spy):
            p.git_read("status", "--porcelain")
        self.assertIsInstance(calls[0][0][0], list)
        self.assertNotIn("shell", calls[0][1])

    def test_home_read_only_three_files_capped(self):
        p = self.probe()
        self.assertIn("statusLine", p.home_read(".claude/settings.json"))
        self.assertIsNone(p.home_read(".claude/CLAUDE.md"))
        for bad in (".ssh/id", ".claude/../.ssh/id", ".bashrc"):
            with self.subTest(path=bad):
                with self.assertRaises(upgrade.ProbeError):
                    p.home_read(bad)
        big = self.home / ".claude/settings.local.json"
        big.write_bytes(b" " * (upgrade.HOME_READ_MAX + 1))
        with self.assertRaises(upgrade.CheckFailed):
            p.home_read(".claude/settings.local.json")

    def test_overlay_makes_a_pending_edit_visible(self):
        overlay = {}
        p = self.probe(overlay=overlay)
        upgrade.overlay_apply(overlay, [upgrade.Edit("write", "notes.txt", before_sha256=p.sha256("notes.txt"),
                                                     text="changed\n"),
                                        upgrade.Edit("write", "new.txt", text="n\n"),
                                        upgrade.Edit("delete", "docs/spec/project.json", before_sha256="x")])
        self.assertEqual(p.read_text("notes.txt"), "changed\n")
        self.assertTrue(p.exists("new.txt"))
        self.assertFalse(p.exists("docs/spec/project.json"))
        self.assertIn("new.txt", p.glob("*.txt"))
        self.assertNotIn("docs/spec/project.json", p.glob("docs/spec/*.json"))
        self.assertEqual((self.root / "notes.txt").read_text(encoding="utf-8"), "hello\n", "nothing written")

    def test_state_and_config_modules_load_via_importlib(self):
        p = self.probe()
        self.assertTrue(callable(p.state.fix_spec))
        self.assertTrue(callable(p.state.fix_project))
        self.assertTrue(callable(p.config.propose_settings))
        self.assertIs(p.state, upgrade.state_module())

    def test_edit_and_result_contracts(self):
        with self.assertRaises(ValueError):
            upgrade.Edit("move", "a")
        with self.assertRaises(ValueError):
            upgrade.Edit("write", "a", scope="home", text="x")
        with self.assertRaises(ValueError):
            upgrade.Edit("write", "a")
        with self.assertRaises(ValueError):
            upgrade.StepResult("maybe")

    def test_deadline(self):
        import time
        p = self.probe(deadline=time.monotonic() - 1)
        with self.assertRaises(upgrade.DeadlineExceeded):
            p.check_deadline()


# ---------------------------------------------------------------- test-only steps (REQ-UP-005, 007, 009)
EVALUATED = []


def t_nothing(probe, params):
    EVALUATED.append(params.get("tag", "nothing"))
    return upgrade.StepResult("nothing")


def t_applies(probe, params):
    EVALUATED.append(params.get("tag", "applies"))
    text = probe.read_text("notes.txt") or ""
    return upgrade.StepResult("applies", summary="append a line", edits=[
        upgrade.Edit("write", "notes.txt", before_sha256=probe.sha256("notes.txt"), text=text + "more\n")])


def t_sees_overlay(probe, params):
    EVALUATED.append("overlay")
    return upgrade.StepResult("applies" if "more" not in (probe.read_text("notes.txt") or "") else "nothing")


def t_raises(probe, params):
    EVALUATED.append("raises")
    raise RuntimeError("boom")


def t_slow(probe, params):
    EVALUATED.append("slow")
    time.sleep(0.05)
    return upgrade.StepResult("nothing")


REG = {"t_nothing": t_nothing, "t_applies": t_applies, "t_sees_overlay": t_sees_overlay, "t_raises": t_raises,
       "t_slow": t_slow}


def step(sid, check, fix=None, cost="low", **kw):
    st = {"id": sid, "since": "3.13.0", "title": sid, "check": check, "fix": fix, "dry_run": True,
          "human": False, "risk": "low", "report_only": fix is None, "writes": ["project"], "cost": cost,
          "params": kw.pop("params", {})}
    st.update(kw)
    return st


def tree_digest(*dirs):
    h = hashlib.sha256()
    for d in dirs:
        for p in sorted(Path(d).rglob("*")):
            if p.is_file() and not p.is_symlink():
                h.update(str(p.relative_to(d)).encode())
                h.update(p.read_bytes())
                h.update(str(p.stat().st_mode).encode())
    return h.hexdigest()


class PlanTests(unittest.TestCase):
    def setUp(self):
        g.isolate_git()
        EVALUATED.clear()
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "proj")
        g.write(self.root, "docs/spec/project.json", {"a": 1})
        g.write(self.root, "notes.txt", "hello\n")
        g.commit_all(self.root)

    def tearDown(self):
        self.t.cleanup()

    def test_all_nothing_is_nothing_to_do_exit_0(self):
        p = upgrade.plan(self.root, steps=[step("a", "t_nothing"), step("b", "t_nothing")], registry=REG,
                         seen_version=None)
        self.assertEqual(p.exit, 0)
        self.assertTrue(p.nothing_to_do())
        self.assertIn("nothing to do", p.table())

    def test_a_raising_check_is_check_failed_and_the_others_still_run(self):
        steps = [step("a", "t_raises"), step("b", "t_applies", fix="t_applies"), step("c", "t_nothing")]
        p = upgrade.plan(self.root, steps=steps, registry=REG, seen_version=None)
        self.assertEqual(p.exit, 1)
        by = {r["id"]: r for r in p.rows()}
        self.assertEqual(by["a"]["status"], "check-failed")
        self.assertIn("check-failed: RuntimeError: boom", by["a"]["summary"])
        self.assertEqual((by["b"]["status"], by["c"]["status"]), ("applies", "nothing"))
        self.assertEqual(EVALUATED, ["raises", "applies", "nothing"])

    def test_the_overlay_carries_earlier_edits_to_later_checks(self):
        steps = [step("a", "t_applies", fix="t_applies"), step("b", "t_sees_overlay", fix="t_applies")]
        by = {r["id"]: r for r in upgrade.plan(self.root, steps=steps, registry=REG, seen_version=None).rows()}
        self.assertEqual(by["b"]["status"], "nothing")

    def test_catalogue_flags_win_over_the_check(self):
        steps = [step("h", "t_applies", human=True), step("r", "t_applies", report_only=True)]
        p = upgrade.plan(self.root, steps=steps, registry=REG, seen_version=None)
        by = {r["id"]: r for r in p.rows()}
        self.assertEqual((by["h"]["status"], by["r"]["status"]), ("human", "report"))
        self.assertEqual(p.results["h"].edits, [])
        self.assertEqual(p.results["r"].edits, [])

    def test_json_rows_equal_the_table_rows(self):
        steps = [step("a", "t_applies", fix="t_applies"), step("b", "t_nothing"), step("c", "t_raises")]
        p = upgrade.plan(self.root, steps=steps, registry=REG, seen_version="3.0.0")
        doc = json.loads(json.dumps(p.as_json()))
        self.assertEqual(set(doc), {"from", "to", "computed_on", "steps"})
        self.assertEqual([r["id"] for r in doc["steps"]], ["a", "b", "c"])
        keys = {"id", "since", "title", "status", "summary", "dry_run", "risk", "human", "report_only",
                "inputs_needed", "warnings"}
        for r in doc["steps"]:
            self.assertEqual(set(r), keys)
        table_ids = [line.split("|")[1].strip() for line in p.table().splitlines() if line.startswith("| ")
                     and not line.startswith("| step")]
        self.assertEqual(table_ids, [r["id"] for r in doc["steps"] if r["status"] != "nothing"])
        self.assertEqual(doc["computed_on"], "main")

    def test_plan_is_state_based_not_version_based(self):
        steps = [step("a", "t_applies", fix="t_applies"), step("b", "t_nothing")]
        a = upgrade.plan(self.root, steps=steps, registry=REG, seen_version="3.0.0")
        b = upgrade.plan(self.root, steps=steps, registry=REG, seen_version="3.11.4")
        self.assertEqual(a.rows(), b.rows())
        self.assertEqual((a.from_version, b.from_version), ("3.0.0", "3.11.4"))

    def test_any_applicable_stops_at_the_first_hit_low_cost_first(self):
        steps = [step("s", "t_nothing", cost="scan", params={"tag": "scan"}), step("l", "t_applies", fix="t_applies"),
                 step("z", "t_nothing", params={"tag": "late"})]
        self.assertEqual(upgrade.any_applicable(self.root, time.monotonic() + 5, steps=steps, registry=REG), "found")
        self.assertEqual(EVALUATED, ["applies"])

    def test_any_applicable_none_timeout_failed(self):
        self.assertEqual(upgrade.any_applicable(self.root, time.monotonic() + 5,
                                                steps=[step("a", "t_nothing")], registry=REG), "none")
        EVALUATED.clear()
        steps = [step("a", "t_slow"), step("b", "t_slow"), step("c", "t_applies", fix="t_applies")]
        self.assertEqual(upgrade.any_applicable(self.root, time.monotonic() + 0.01, steps=steps, registry=REG),
                         "timeout")
        self.assertNotIn("applies", EVALUATED)
        self.assertEqual(upgrade.any_applicable(self.root, time.monotonic() - 1, steps=steps, registry=REG),
                         "timeout")
        self.assertEqual(upgrade.any_applicable(self.root, time.monotonic() + 5, steps=[step("x", "t_raises")],
                                                registry=REG), "failed")


class PlanWritesNothing(unittest.TestCase):
    """sha256 of tree + git dir + fixture home identical before and after plan (REQ-UP-010)."""

    def test_plan_on_the_legacy_fixture_writes_nothing(self):
        g.isolate_git()
        t = g.TempDir()
        try:
            root = t.path / "proj"
            shutil.copytree(str(_path.FIXTURES_DIR / "upgrade" / "legacy-project"), str(root))
            g.init(root)
            g.commit_all(root, "fixture")
            home = t.path / "home"
            shutil.copytree(str(_path.FIXTURES_DIR / "upgrade" / "fake-home"), str(home))
            before = tree_digest(root, home)
            with mock.patch.dict(os.environ, {"HOME": str(home)}):
                p = upgrade.plan(root, home=home)
                upgrade.any_applicable(root, time.monotonic() + 5, home=home)
            self.assertIn(p.exit, (0, 1))
            self.assertEqual(tree_digest(root, home), before)
            self.assertFalse((root / ".git" / "karvey").exists(), "no state dir, lock, journal or audit")
        finally:
            t.cleanup()


if __name__ == "__main__":
    unittest.main()
