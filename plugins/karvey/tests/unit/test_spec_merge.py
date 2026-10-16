"""karvey-spec-merge.py: ADDED / MODIFIED / REMOVED, idempotence, dry run (REQ-W1-065, REQ-W1-066)."""
import contextlib
import importlib.util
import io
import json
import shutil
import unittest
from pathlib import Path

import _path
import _gitrepo as g

_SPEC = importlib.util.spec_from_file_location("karvey_spec_merge", str(_path.SCRIPTS_DIR / "karvey-spec-merge.py"))
sm = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sm)

LIVING = """# Living spec — capability `demo`

## ADDED by `old` (1.0.0, archived 2026-01-01)

### Group

- **REQ-A-001** — THE thing SHALL work.
- **REQ-A-002** — THE other thing SHALL work
  across two lines.
- **REQ-A-003** — THE third thing SHALL go.
"""

DELTA = """# Spec Delta: feat-x

## ADDED Requirements

### ADDED by `feat-x` (2.0.0)

Traced to `prd.md`.

### New group
- **REQ-X-001** — THE new thing SHALL exist.
- **REQ-X-002** — THE newer thing SHALL exist
  with a continuation line.

## MODIFIED Requirements

### Requirement: REQ-A-002
<!-- COMPLETELY replaces REQ-A-002. Reason: clarity. -->
- **REQ-A-002** — THE other thing SHALL work, amended.

## REMOVED Requirements

- **REQ-A-003** — superseded by REQ-X-001.
"""


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = sm.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def run_json(*argv):
    code, out, _ = run(*(list(argv) + ["--json"]))
    return code, json.loads(out)


class Base(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path
        self.cdir = self.root / "docs/spec/changes/feat-x"
        self.cdir.mkdir(parents=True)
        (self.cdir / "spec.json").write_text(json.dumps({"change_id": "feat-x", "capability": "demo"}),
                                             encoding="utf-8")
        self.target = self.root / "docs/spec/specs/demo/spec.md"
        self.target.parent.mkdir(parents=True)
        self.target.write_text(LIVING, encoding="utf-8")
        self.delta(DELTA)

    def tearDown(self):
        self.t.cleanup()

    def delta(self, text):
        (self.cdir / "spec-delta.md").write_text(text, encoding="utf-8")

    def merge(self, *extra):
        return run_json("feat-x", "--root", str(self.root), "--date", "2026-09-24", *extra)

    def text(self):
        return self.target.read_text(encoding="utf-8")


class Sections(Base):
    def test_added_appended_with_heading_and_groups(self):
        code, env = self.merge()
        self.assertEqual(code, 0, env["errors"])
        t = self.text()
        self.assertIn("## ADDED by `feat-x` (2.0.0, merged 2026-09-24)", t)
        self.assertIn("Traced to `prd.md`.", t)
        self.assertIn("### New group", t)
        self.assertIn("- **REQ-X-002** — THE newer thing SHALL exist\n  with a continuation line.", t)
        self.assertEqual(env["result"]["added"], ["REQ-X-001", "REQ-X-002"])
        self.assertTrue(t.index("REQ-A-001") < t.index("## ADDED by `feat-x`"))

    def test_modified_replaced_in_place(self):
        self.merge()
        t = self.text()
        self.assertIn("- **REQ-A-002** — THE other thing SHALL work, amended.\n", t)
        self.assertNotIn("across two lines", t)
        self.assertNotIn("COMPLETELY replaces", t)
        self.assertTrue(t.index("REQ-A-002") < t.index("## ADDED by `feat-x`"))

    def test_removed_leaves_deprecation_line(self):
        self.merge()
        self.assertIn("- ~~**REQ-A-003**~~ — REMOVED by `feat-x` (2026-09-24): superseded by REQ-X-001.",
                      self.text())

    def test_removed_heading_form(self):
        self.delta("## REMOVED Requirements\n\n### Requirement: REQ-A-003\nReason: no longer applies.\n")
        code, env = self.merge()
        self.assertEqual(code, 0, env["errors"])
        self.assertIn("REMOVED by `feat-x` (2026-09-24): no longer applies.", self.text())

    def test_second_run_is_idempotent(self):
        self.merge()
        first = self.text()
        code, env = self.merge()
        self.assertEqual(code, 0)
        self.assertFalse(env["result"]["changed"])
        self.assertEqual(self.text(), first)
        code, env = run_json("feat-x", "--root", str(self.root), "--date", "2027-01-01")
        self.assertEqual(self.text(), first, "a later date must not re-add anything")

    def test_grown_delta_appends_into_existing_section(self):
        self.merge()
        self.delta(DELTA.replace("### New group\n", "### New group\n- **REQ-X-003** — A late addition SHALL fit.\n"))
        code, env = self.merge()
        self.assertEqual(code, 0, env["errors"])
        self.assertEqual(env["result"]["added"], ["REQ-X-003"])
        t = self.text()
        self.assertEqual(t.count("## ADDED by `feat-x`"), 1)
        self.assertIn("REQ-X-003", t)


class Errors(Base):
    def test_missing_modified_id_writes_nothing_and_names_it(self):
        self.delta(DELTA.replace("REQ-A-002", "REQ-A-999"))
        code, env = self.merge()
        self.assertEqual(code, 1)
        self.assertEqual(env["result"]["missing"], ["REQ-A-999"])
        self.assertTrue(any("REQ-A-999" in e["message"] for e in env["errors"]))
        self.assertEqual(self.text(), LIVING)

    def test_missing_id_human_output_names_it(self):
        self.delta(DELTA.replace("REQ-A-002", "REQ-A-999"))
        code, out, err = run("feat-x", "--root", str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("REQ-A-999", err)
        self.assertIn("nothing written", err)

    def test_added_conflict(self):
        self.delta("## ADDED Requirements\n\n- **REQ-A-001** — THE thing SHALL work differently.\n")
        code, env = self.merge()
        self.assertEqual(code, 1)
        self.assertEqual(env["result"]["conflicts"], ["REQ-A-001"])
        self.assertEqual(self.text(), LIVING)

    def test_added_same_text_is_noop(self):
        self.delta("## ADDED Requirements\n\n- **REQ-A-001** —   THE thing SHALL\n  work.\n")
        code, env = self.merge()
        self.assertEqual(code, 0)
        self.assertEqual(env["result"]["noop"], ["REQ-A-001"])
        self.assertEqual(self.text(), LIVING)

    def test_unparsable_section_gives_line_and_exit_3(self):
        self.delta("# D\n\n## MODIFIED Requirements\n\n### Requirement: REQ-A-002\nno item here\n")
        code, env = self.merge("--dry-run")
        self.assertEqual(code, 3)
        self.assertIn("line 5", env["errors"][0]["message"])
        self.assertEqual(self.text(), LIVING)

    def test_bad_item_id_is_unparsable(self):
        self.delta("## ADDED Requirements\n\n- **not an id** — x\n")
        code, env = self.merge()
        self.assertEqual(code, 3)
        self.assertIn("line 3", env["errors"][0]["message"])

    def test_no_section_is_unparsable(self):
        self.delta("# Nothing here\n")
        self.assertEqual(self.merge()[0], 3)

    def test_missing_delta_exit_4(self):
        (self.cdir / "spec-delta.md").unlink()
        self.assertEqual(self.merge()[0], 4)

    def test_unknown_change_exit_4(self):
        self.assertEqual(run_json("nope", "--root", str(self.root))[0], 4)


class DryRun(Base):
    def test_dry_run_prints_diff_and_writes_nothing(self):
        code, out, _ = run("feat-x", "--root", str(self.root), "--dry-run", "--date", "2026-09-24")
        self.assertEqual(code, 0)
        self.assertIn("--- a/docs/spec/specs/demo/spec.md", out)
        self.assertIn("+- **REQ-X-001**", out)
        self.assertIn("nothing written", out)
        self.assertEqual(self.text(), LIVING)

    def test_dry_run_json_carries_the_diff(self):
        code, env = self.merge("--dry-run")
        self.assertEqual(code, 0)
        self.assertTrue(env["result"]["dry_run"])
        self.assertIn("+## ADDED by `feat-x`", env["result"]["diff"])
        self.assertEqual(self.text(), LIVING)


class RealDelta(unittest.TestCase):
    """This change's real spec-delta.md against a temp copy of the method living spec."""

    def setUp(self):
        self.t = g.TempDir()
        self.root = self.t.path
        repo = _path.REPO_ROOT
        src_change = repo / "docs/spec/changes/wave1-hardening"
        archived = sorted((repo / "docs/spec/changes/archive").glob("*-wave1-hardening"))
        # once archived, the living spec already holds this delta: the test checks idempotency only
        self.merged = not src_change.is_dir() and bool(archived)
        if self.merged:
            src_change = archived[-1]
        dst = self.root / "docs/spec/changes/wave1-hardening"
        dst.mkdir(parents=True)
        for name in ("spec-delta.md", "spec.json"):
            shutil.copy(str(src_change / name), str(dst / name))
        spec = self.root / "docs/spec/specs/method"
        spec.mkdir(parents=True)
        shutil.copy(str(repo / "docs/spec/specs/method/spec.md"), str(spec / "spec.md"))
        self.target = spec / "spec.md"

    def tearDown(self):
        self.t.cleanup()

    def test_real_delta_merges_and_is_idempotent(self):
        if self.merged:
            before = self.target.read_text(encoding="utf-8")
            self.assertIn("## ADDED by `wave1-hardening` (3.12.0, merged ", before)
            code, env = run_json("wave1-hardening", "--root", str(self.root), "--date", "2026-09-27")
            self.assertEqual(code, 0, env["errors"])
            self.assertFalse(env["result"]["changed"])
            self.assertEqual(self.target.read_text(encoding="utf-8"), before)
            return
        code, env = run_json("wave1-hardening", "--root", str(self.root), "--date", "2026-09-24")
        self.assertEqual(code, 0, env["errors"])
        r = env["result"]
        self.assertEqual(sorted(r["modified"]), ["REQ-TEAM-002", "REQ-TEAM-010d", "REQ-TEAM-014b", "REQ-TEAM-015"])
        self.assertEqual(r["removed"], [])
        w1 = [i for i in r["added"] if i.startswith("REQ-W1-")]
        self.assertEqual(len(w1), 109)
        self.assertIn("REQ-ADP-031", r["added"])
        t = self.target.read_text(encoding="utf-8")
        self.assertIn("## ADDED by `wave1-hardening` (3.12.0, merged 2026-09-24)", t)
        self.assertIn("except the one-line settings notice of REQ-W1-050", t)
        before = t
        code, env = run_json("wave1-hardening", "--root", str(self.root), "--date", "2026-09-25")
        self.assertEqual(code, 0)
        self.assertFalse(env["result"]["changed"])
        self.assertEqual(self.target.read_text(encoding="utf-8"), before)


class DuplicateIds(Base):
    """BUG-45: a REMOVED id listed twice, or both MODIFIED and REMOVED, produced overlapping line edits that
    silently deleted neighbouring requirements (exit 0)."""

    def test_removed_twice_is_refused_and_nothing_is_written(self):
        before = self.text()
        self.delta("## REMOVED Requirements\n\n- **REQ-A-001** — gone.\n- **REQ-A-001** — gone again.\n")
        code, env = self.merge()
        self.assertNotEqual(code, 0)
        self.assertEqual(self.text(), before)
        self.assertIn("twice", json.dumps(env["errors"]))

    def test_modified_and_removed_is_refused(self):
        before = self.text()
        self.delta("## MODIFIED Requirements\n\n### Requirement: REQ-A-002\n- **REQ-A-002** — changed.\n\n"
                   "## REMOVED Requirements\n\n- **REQ-A-002** — gone.\n")
        code, env = self.merge()
        self.assertNotEqual(code, 0)
        self.assertEqual(self.text(), before)


class LineEndings(Base):
    """BUG-38: a living spec with a BOM and CRLF line endings was rewritten with LF and no BOM, so git showed
    every line as changed."""

    def test_bom_and_crlf_are_kept(self):
        self.target.write_bytes(("\ufeff" + LIVING).replace("\n", "\r\n").encode("utf-8"))
        code, env = self.merge()
        self.assertEqual(code, 0, env["errors"])
        raw = self.target.read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
        self.assertIn("REQ-X-001", raw.decode("utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
