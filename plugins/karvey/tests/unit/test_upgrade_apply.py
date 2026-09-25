"""apply: selection, values as data, confinement, preview, writes, journal, branch (REQ-UP-011..019)."""
import json
import os
import subprocess
import unittest
from pathlib import Path

import _gitrepo as g
import _path  # noqa: F401
from karvey_lib import upgrade


# ---------------------------------------------------------------- test-only steps
def _append(probe, params, suffix):
    path = params.get("file", "notes.txt")
    text = probe.read_text(path)
    return upgrade.StepResult("applies", summary="append %s to %s" % (suffix, path), edits=[
        upgrade.Edit("write", path, before_sha256=probe.sha256(path), text=(text or "") + suffix + "\n")])


def t_append_check(probe, params):
    if params.get("marker") and params["marker"] in (probe.read_text(params.get("file", "notes.txt")) or ""):
        return upgrade.StepResult("nothing")
    return _append(probe, params, params.get("marker", "x"))


def t_append_fix(probe, params, values):
    return _append(probe, params, params.get("marker", "x"))


def t_nothing(probe, params):
    return upgrade.StepResult("nothing")


def t_needs_check(probe, params):
    if probe.exists("name.txt"):
        return upgrade.StepResult("nothing")
    return upgrade.StepResult("needs-input", summary="write name.txt", inputs_needed=["name"])


def t_needs_fix(probe, params, values):
    if not values.get("name"):
        raise upgrade.NeedsInput("name")
    if not str(values["name"]).isalnum():
        raise upgrade.sv.UnsafeValue("name", "test", "letters and digits only", values["name"])
    return upgrade.StepResult("applies", edits=[upgrade.Edit("write", "name.txt", text=values["name"] + "\n")])


def t_human(probe, params):
    return upgrade.StepResult("human", summary="do it by hand", instructions="paste this line", diff="-a\n+b\n")


def t_escape(probe, params):
    return upgrade.StepResult("applies", edits=[upgrade.Edit("write", params["path"], scope=params.get("scope",
                                                                                                    "project"),
                                                             text="evil\n")])


def t_delete_check(probe, params):
    if not probe.exists(params["file"]):
        return upgrade.StepResult("nothing")
    return upgrade.StepResult("applies", edits=[upgrade.Edit("delete", params["file"],
                                                             before_sha256=probe.sha256(params["file"]))])


def t_bad_cas(probe, params, values):
    return upgrade.StepResult("applies", edits=[upgrade.Edit("write", params["file"], before_sha256="0" * 64,
                                                             text="lost\n")])


def t_delete_fix(probe, params, values):
    return t_delete_check(probe, params)


def t_escape_fix(probe, params, values):
    return t_escape(probe, params)


REG = {"t_delete_fix": t_delete_fix, "t_escape_fix": t_escape_fix, "t_append_check": t_append_check, "t_append_fix": t_append_fix, "t_nothing": t_nothing,
       "t_needs_check": t_needs_check, "t_needs_fix": t_needs_fix, "t_human": t_human, "t_escape": t_escape,
       "t_delete_check": t_delete_check, "t_bad_cas": t_bad_cas}


def step(sid, check, fix=None, **kw):
    st = {"id": sid, "since": "3.13.0", "title": sid, "check": check, "fix": fix, "dry_run": True,
          "human": False, "risk": "low", "report_only": False, "writes": ["project"], "cost": "low",
          "params": kw.pop("params", {})}
    st.update(kw)
    return st


def appender(sid, marker, file="notes.txt", **kw):
    return step(sid, "t_append_check", "t_append_fix", params={"marker": marker, "file": file}, **kw)


INSTALLED = "3.13.0"


class Base(unittest.TestCase):
    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "proj")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"}})
        g.write(self.root, "notes.txt", "hello\n")
        g.commit_all(self.root)

    def tearDown(self):
        self.t.cleanup()

    def apply(self, steps, ids, **kw):
        kw.setdefault("installed", INSTALLED)
        return upgrade.apply(self.root, ids, steps=steps, registry=REG, **kw)

    def refused(self, steps, ids, needle, **kw):
        before = self.snapshot()
        with self.assertRaises(upgrade.Refused) as cm:
            self.apply(steps, ids, **kw)
        self.assertEqual(cm.exception.exit_code, 3)
        self.assertIn(needle, str(cm.exception))
        self.assertEqual(self.snapshot(), before, "a refused apply changes nothing in the tree")
        return str(cm.exception)

    def snapshot(self):
        out = {}
        for p in sorted(self.root.rglob("*")):
            if ".git" in p.relative_to(self.root).parts or not p.is_file():
                continue
            out[p.relative_to(self.root).as_posix()] = p.read_bytes()
        return out

    def git(self, *args):
        return subprocess.run(["git"] + list(args), cwd=str(self.root), capture_output=True, text=True).stdout.strip()


class PlanningHalf(Base):
    def test_unknown_id_refused_before_any_change(self):
        self.refused([appender("a", "A")], ["a", "zzz"], "unknown step id(s): zzz")

    def test_mixed_selection_refused_all_satisfied_is_nothing_to_do(self):
        g.write(self.root, "notes.txt", "hello\nA\n")
        g.commit_all(self.root)
        steps = [appender("a", "A"), appender("b", "B")]
        self.refused(steps, ["a", "b"], "not applicable (nothing to do): a")
        rep = self.apply(steps, ["a"], dry_run=True)
        self.assertEqual((rep.exit, rep.nothing), (0, ["a"]))
        self.assertIn("a: nothing to do", rep.text())

    def test_needs_input_without_values_names_the_input(self):
        self.refused([step("n", "t_needs_check", "t_needs_fix")], ["n"], "needs input: n: name")
        self.refused([step("n", "t_needs_check", "t_needs_fix")], ["n"], "value refused",
                     inputs={"n": {"name": "a b; rm"}}, dry_run=True)
        rep = self.apply([step("n", "t_needs_check", "t_needs_fix")], ["n"], inputs={"n": {"name": "abc"}},
                         dry_run=True)
        self.assertIn("+abc", rep.diffs["n"])

    def test_catalogue_order_whatever_the_argument_order(self):
        steps = [appender("a", "A"), appender("b", "B")]
        rep = self.apply(steps, ["b", "a"], dry_run=True)
        self.assertEqual(list(rep.diffs), ["a", "b"])
        self.assertIn("+A", rep.diffs["a"])
        self.assertIn("+B", rep.diffs["b"])
        self.assertIn(" A", rep.diffs["b"], "b sees a's pending edit")

    def test_human_step_is_never_performed(self):
        steps = [step("h", "t_human", human=True), step("h2", "t_append_check", human=True,
                                                          params={"marker": "Z"})]
        rep = self.apply(steps, ["h", "h2"], dry_run=True)
        self.assertEqual(rep.shown, ["h", "h2"])
        self.assertIn("paste this line", rep.text())
        self.assertIsNone(rep.preview)
        before = self.snapshot()
        rep = self.apply(steps, ["h", "h2"], confirm_no_preview=["h", "h2"])
        self.assertEqual((rep.applied, rep.shown), ([], ["h", "h2"]))
        self.assertEqual(self.snapshot(), before)

    def test_symlinked_dir_out_of_the_tree_is_refused(self):
        outside = self.t.path / "outside"
        outside.mkdir()
        os.symlink(str(outside), str(self.root / ".claude"))
        st = step("e", "t_escape", "t_escape_fix", params={"path": ".claude/settings.json"})
        self.refused([st], ["e"], "resolves outside the working tree", dry_run=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_edits_naming_the_gate_evidence_are_refused(self):
        for path, scope in ((".git/karvey/approvals/m.json", "project"), ("karvey/approvals/m.json", "git_dir"),
                            ("karvey/ledger/c.json", "git_dir"), ("karvey/seen-version", "git_dir")):
            with self.subTest(path=path):
                st = step("e", "t_escape", "t_escape_fix", params={"path": path, "scope": scope},
                          writes=["project", "git_dir"])
                self.refused([st], ["e"], "refused", dry_run=True)

    def test_branch_flow_values_are_data(self):
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "dev; rm -rf ~"}})
        msg = self.refused([appender("a", "A")], ["a"], "project.json:branch_flow.integration", dry_run=True)
        self.assertIn("invalid branch name", msg)
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "$(x)"}})
        self.refused([appender("a", "A")], ["a"], "project.json:branch_flow.production", dry_run=True)
        self.refused([appender("a", "A")], ["a"], "not a release number", dry_run=True, installed="3.13")

    def test_dry_run_prints_diffs_writes_nothing_returns_preview(self):
        before = self.snapshot()
        rep = self.apply([appender("a", "A")], ["a"], dry_run=True)
        self.assertEqual(self.snapshot(), before)
        self.assertRegex(rep.preview, r"^[0-9a-f]{64}$")
        self.assertIn("--- a/notes.txt", rep.text())
        self.assertIn("+A", rep.text())
        self.assertIn("preview id: " + rep.preview, rep.text())
        again = self.apply([appender("a", "A")], ["a"], dry_run=True)
        self.assertEqual(again.preview, rep.preview, "the preview id is deterministic")
        self.assertFalse((self.root / ".git" / "karvey").exists())

    def test_deletion_diff_against_dev_null(self):
        rep = self.apply([step("d", "t_delete_check", "t_delete_fix", params={"file": "notes.txt"})], ["d"],
                         dry_run=True)
        self.assertIn("+++ /dev/null", rep.diffs["d"])

    def test_apply_without_or_with_a_stale_preview_is_refused(self):
        steps = [appender("a", "A")]
        self.refused(steps, ["a"], "run apply --dry-run")
        rep = self.apply(steps, ["a"], dry_run=True)
        g.write(self.root, "notes.txt", "hello\nchanged\n")
        g.commit_all(self.root)
        self.refused(steps, ["a"], "the tree changed since the preview", preview=rep.preview)

    def test_a_step_without_preview_needs_confirm(self):
        steps = [appender("a", "A", dry_run=False)]
        rep = self.apply(steps, ["a"], dry_run=True)
        self.assertIsNone(rep.preview)
        self.assertIn("--confirm-no-preview a", rep.text())
        self.refused(steps, ["a"], "--confirm-no-preview: a")


if __name__ == "__main__":
    unittest.main()
