"""lint-plugin.py (architecture §1.6): one passing and one failing mini-plugin per check.

The passing fixture is ``fixtures/lint/good/`` (a mini repository with a mini plugin that
passes every check). Each failing case copies it to a temp dir and applies one mutation.
"""
import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _path

LINT = _path.SCRIPTS_DIR / "lint-plugin.py"
GOOD = _path.UNIT_DIR / "fixtures" / "lint" / "good"
SKILLS = "plugins/karvey/skills"
RULES = SKILLS + "/karvey/rules"

_spec = importlib.util.spec_from_file_location("lint_plugin", str(LINT))
lp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lp)


def run_cli(*args):
    p = subprocess.run([sys.executable, str(LINT)] + list(args), capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def lint(root, only=None, paths=None):
    ctx = lp.Ctx(root)
    return lp.run_checks(ctx, only=set(only) if only else None, paths=paths)


class Tree:
    """A temp copy of the good fixture that a test can mutate."""

    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix="karvey-lint-")
        self.root = Path(self.tmp) / "repo"
        shutil.copytree(str(GOOD), str(self.root))

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def path(self, rel):
        return self.root / rel

    def read(self, rel):
        return self.path(rel).read_text(encoding="utf-8")

    def write(self, rel, text):
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not isinstance(text, str):
            text = json.dumps(text, indent=2, ensure_ascii=False) + "\n"
        p.write_text(text, encoding="utf-8")

    def append(self, rel, text):
        self.write(rel, self.read(rel) + text)

    def replace(self, rel, old, new):
        s = self.read(rel)
        if old not in s:
            raise AssertionError("%r not in %s" % (old, rel))
        self.write(rel, s.replace(old, new))

    def remove(self, rel):
        p = self.path(rel)
        if p.is_dir():
            shutil.rmtree(str(p))
        else:
            p.unlink()


class LintCase(unittest.TestCase):
    def setUp(self):
        self.t = Tree()

    def tearDown(self):
        self.t.cleanup()

    def ids(self, only=None, paths=None, severity=None):
        return [f["check"] for f in lint(self.t.root, only, paths)
                if severity is None or f["severity"] == severity]

    def assertFails(self, cid, contains=None, file=None):
        fs = [f for f in lint(self.t.root, [cid]) if f["check"] == cid]
        self.assertTrue(fs, "%s did not fire" % cid)
        if contains:
            self.assertTrue(any(contains in f["message"] for f in fs),
                            "no %s finding mentions %r: %s" % (cid, contains, [f["message"] for f in fs]))
        if file:
            self.assertTrue(any(f["file"] == file for f in fs),
                            "no %s finding in %s: %s" % (cid, file, [f["file"] for f in fs]))
        return fs

    def assertPasses(self, cid):
        fs = lint(self.t.root, [cid])
        self.assertEqual(fs, [], "%s fired on the good fixture: %s" % (cid, fs))


# --------------------------------------------------------------------------- framework
class GoodFixture(unittest.TestCase):
    def test_good_fixture_passes_every_check(self):
        self.assertEqual(lint(GOOD), [])

    def test_cli_exit_0_on_good(self):
        code, out, _ = run_cli("--root", str(GOOD))
        self.assertEqual(code, 0, out)
        self.assertIn("0 errors", out)


class Framework(LintCase):
    def test_registry_ids_are_unique_and_well_formed(self):
        ids = [c.id for c in lp.registry()]
        self.assertEqual(len(ids), len(set(ids)))
        for cid in ids:
            self.assertRegex(cid, r"^L-\d\d$")

    def test_exit_1_on_error_finding(self):
        self.t.remove(SKILLS + "/karvey-init/SKILL.md")
        self.t.write(SKILLS + "/karvey-init/SKILL.md", "no frontmatter\n")
        code, out, _ = run_cli("--root", str(self.t.root), "--only", "L-01")
        self.assertEqual(code, 1)
        self.assertIn("L-01", out)

    def test_exit_2_on_usage_errors(self):
        self.assertEqual(run_cli("--root", str(self.t.root), "--only", "L-99")[0], 2)
        self.assertEqual(run_cli("--root", str(self.t.root), "--format", "yaml")[0], 2)
        self.assertEqual(run_cli("--root", str(self.t.root / "missing"))[0], 2)

    def test_format_github_annotations(self):
        self.t.write(SKILLS + "/karvey-init/SKILL.md", "no frontmatter\n")
        code, out, _ = run_cli("--root", str(self.t.root), "--only", "L-01", "--format", "github")
        self.assertEqual(code, 1)
        self.assertIn("::error file=%s/karvey-init/SKILL.md,line=1,title=L-01::" % SKILLS, out)

    def test_format_json_envelope(self):
        self.t.write(SKILLS + "/karvey-init/SKILL.md", "no frontmatter\n")
        code, out, _ = run_cli("--root", str(self.t.root), "--only", "L-01", "--format", "json")
        env = json.loads(out)
        self.assertEqual(tuple(env), ("tool", "version", "ok", "exit", "result", "errors", "warnings"))
        self.assertEqual((env["tool"], env["exit"], env["ok"]), ("lint-plugin", 1, False))
        self.assertEqual(env["errors"][0]["code"], "L-01")
        self.assertEqual(env["result"]["counts"]["L-01"]["error"], len(env["errors"]))

    def test_paths_limits_findings_to_matching_files(self):
        for name in ("karvey-init", "karvey-requirements"):
            self.t.write(SKILLS + "/%s/SKILL.md" % name, "no frontmatter\n")
        both = lint(self.t.root, ["L-01"])
        self.assertEqual({f["file"] for f in both},
                         {SKILLS + "/karvey-init/SKILL.md", SKILLS + "/karvey-requirements/SKILL.md"})
        one = lint(self.t.root, ["L-01"], paths=[SKILLS + "/{karvey,karvey-init}/SKILL.md"])
        self.assertEqual({f["file"] for f in one}, {SKILLS + "/karvey-init/SKILL.md"})
        star = lint(self.t.root, ["L-01"], paths=["plugins/karvey/skills/*/SKILL.md"])
        self.assertEqual(len(star), len(both))
        code, _, _ = run_cli("--root", str(self.t.root), "--only", "L-01", "--paths",
                             SKILLS + "/{karvey,karvey-guard}/SKILL.md")
        self.assertEqual(code, 0)

    def test_glob_semantics(self):
        rx = lp.glob_regex("a/*/c.md")
        self.assertTrue(rx.match("a/b/c.md"))
        self.assertFalse(rx.match("a/b/x/c.md"))
        self.assertTrue(lp.glob_regex("a/**/c.md").match("a/b/x/c.md"))
        self.assertTrue(lp.glob_regex("a/**/c.md").match("a/c.md"))
        self.assertEqual(lp.expand_braces("x/{a,b}/{c,d}"), ["x/a/c", "x/a/d", "x/b/c", "x/b/d"])

    def test_list_passes_when_every_req_is_in_the_requirements(self):
        code, out, _ = run_cli("--root", str(_path.REPO_ROOT), "--list")
        self.assertEqual(code, 0, out)
        self.assertIn("L-01", out)

    def test_list_fails_when_a_claimed_req_is_absent(self):
        req = self.t.path("reqs.md")
        req.write_text("REQ-W1-055 REQ-W1-077 REQ-W1-078\n", encoding="utf-8")
        code, _, err = run_cli("--root", str(self.t.root), "--list", "--requirements", str(req))
        self.assertEqual(code, 1)
        self.assertIn("REQ-W1-079", err)


# --------------------------------------------------------------------------- L-01 .. L-04
class L01(LintCase):
    def test_pass(self):
        self.assertPasses("L-01")

    def test_missing_frontmatter(self):
        self.t.write(SKILLS + "/karvey-init/SKILL.md", "# no frontmatter\n")
        self.assertFails("L-01", "no frontmatter")

    def test_block_scalar_and_continuation(self):
        self.t.replace(SKILLS + "/karvey-init/SKILL.md", "description: Karvey phase 1",
                       "description: >\n  Karvey phase 1")
        self.assertFails("L-01", "block or empty value")

    def test_allowed_tools_not_a_comma_list(self):
        self.t.replace(SKILLS + "/karvey-init/SKILL.md", "allowed-tools: Read, Write,",
                       "allowed-tools: [Read Write]")
        self.assertFails("L-01", "comma list")

    def test_name_differs_from_directory(self):
        self.t.replace(SKILLS + "/karvey-init/SKILL.md", "name: karvey-init", "name: karvey-start")
        self.assertFails("L-01", "differs")


class L02(LintCase):
    def test_pass(self):
        self.assertPasses("L-02")

    def test_too_long(self):
        self.t.replace(SKILLS + "/karvey-init/SKILL.md", "Use to start a new Karvey change.",
                       "Use to start a new Karvey change. " + "x" * 260)
        self.assertFails("L-02", "characters")

    def test_wrong_shape(self):
        self.t.replace(SKILLS + "/karvey-init/SKILL.md", "description: Karvey phase 1 —",
                       "description: Initialize a new Karvey spec —")
        self.assertFails("L-02", "does not start with")


class L03(LintCase):
    def test_pass(self):
        self.assertPasses("L-03")

    def test_bare_generic_trigger(self):
        self.t.replace(SKILLS + "/karvey-init/SKILL.md", '"karvey init"', '"karvey init", "deploy"')
        self.assertFails("L-03", "generic")

    def test_third_party_trigger(self):
        self.t.replace(SKILLS + "/karvey-init/SKILL.md", '"karvey init"', '"karvey init", "Garry Tan"')
        self.assertFails("L-03", "third-party")

    def test_overlap_across_skills(self):
        self.t.replace(SKILLS + "/karvey-requirements/SKILL.md", '"karvey requirements"',
                       '"karvey requirements", "karvey init"')
        fs = self.assertFails("L-03", "overlaps")
        self.assertEqual({f["file"] for f in fs},
                         {SKILLS + "/karvey-init/SKILL.md", SKILLS + "/karvey-requirements/SKILL.md"})


class L04(LintCase):
    def test_pass(self):
        self.assertPasses("L-04")

    def test_user_only_skill_without_flag(self):
        self.t.replace(SKILLS + "/karvey-guard/SKILL.md", "disable-model-invocation: true\n", "")
        self.assertFails("L-04", "karvey-guard")


if __name__ == "__main__":
    unittest.main()
