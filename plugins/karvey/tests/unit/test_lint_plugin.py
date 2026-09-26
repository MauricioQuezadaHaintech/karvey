"""lint-plugin.py (architecture §1.6): one passing and one failing mini-plugin per check.

The passing fixture is ``fixtures/lint/good/`` (a mini repository with a mini plugin that
passes every check). Each failing case copies it to a temp dir and applies one mutation.
"""
import contextlib
import importlib.util
import io
import json
import re
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

    def sub(self, rel, pattern, repl):
        s = self.read(rel)
        new, n = re.subn(pattern, repl, s)
        if not n:
            raise AssertionError("%r not in %s" % (pattern, rel))
        self.write(rel, new)

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


# --------------------------------------------------------------------------- L-05 .. L-10, L-14
INIT = SKILLS + "/karvey-init/SKILL.md"
REQS = SKILLS + "/karvey-requirements/SKILL.md"
ORCH = SKILLS + "/karvey/SKILL.md"


class L05(LintCase):
    def test_pass(self):
        self.assertPasses("L-05")

    def test_legacy_phase_in_skill(self):
        self.t.append(INIT, '\nUpdate spec.json: `phase: "tasks-generated"`.\n')
        self.assertFails("L-05", "tasks-generated", file=INIT)

    def test_legacy_phase_in_rule(self):
        self.t.append(RULES + "/phase-close.md", '\n```json\n{"phase": "qa-approved"}\n```\n')
        self.assertFails("L-05", "qa-approved", file=RULES + "/phase-close.md")

    def test_enum_value_passes(self):
        self.t.append(INIT, '\nThe change starts at `phase: "init"`.\n')
        self.assertPasses("L-05")


class L06(LintCase):
    def test_pass(self):
        self.assertPasses("L-06")

    def test_hand_approval_edit(self):
        self.t.append(REQS, "\nIf the user approves: update `spec.json` with `approvals.requirements.approved: true`.\n")
        self.assertFails("L-06", "hand edit", file=REQS)

    def test_hand_phase_edit(self):
        self.t.append(REQS, '\nUpdate spec.json: `phase: "requirements"`.\n')
        self.assertFails("L-06", file=REQS)

    def test_json_block_written_by_hand(self):
        self.t.append(INIT, '\n```json\n{\n  "change_id": "x",\n  "phase": "init",\n  "approvals": {}\n}\n```\n')
        fs = self.assertFails("L-06", "spec.json block", file=INIT)
        self.assertEqual(len(fs), 1)

    def test_state_tool_call_passes(self):
        self.t.append(REQS, '\nOn approval run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/karvey-state.py" approve '
                            '{id} requirements --by X --role human --ref D-NN` (sets `approvals.requirements.approved: true`).\n')
        self.assertPasses("L-06")

    def test_precondition_read_passes(self):
        self.t.append(REQS, "\n- Verify `approvals.architecture.approved = true` before starting.\n")
        self.assertPasses("L-06")


class L07(LintCase):
    def test_pass(self):
        self.assertPasses("L-07")

    def test_phase_table(self):
        self.t.append(ORCH, "\n| `phase` | `approvals` | Next skill |\n|---|---|---|\n"
                            "| `init` | x | `/karvey-requirements` |\n| `tasks` | x | `/karvey-impl` |\n")
        self.assertFails("L-07", "phase→next table")

    def test_no_next_call(self):
        self.t.replace(ORCH, "karvey-state.py\" next", "karvey-state.py\" active")
        self.assertFails("L-07", "does not call")


class L08(LintCase):
    def test_pass(self):
        self.assertPasses("L-08")

    def test_proposal_md(self):
        self.t.append(REQS, "\nRead `docs/spec/changes/{change-id}/proposal.md`.\n")
        self.assertFails("L-08", "proposal.md", file=REQS)

    def test_capability_spec_delta(self):
        self.t.append(REQS, "\nWrite `docs/spec/changes/{change-id}/specs/{capability}/spec-delta.md`.\n")
        self.assertFails("L-08", "change root", file=REQS)

    def test_reads_an_artifact_produced_later(self):
        self.t.append(REQS, "\nRead `docs/spec/changes/{change-id}/tasks.md` first.\n")
        self.assertFails("L-08", "produced only later", file=REQS)

    def test_state_machine_read_without_producer(self):
        sm = json.loads((_path.SCHEMAS_DIR / "state-machine.json").read_text(encoding="utf-8"))
        sm["phases"][1]["reads"] = ["nothing.md"]
        self.t.write("plugins/karvey/schemas/state-machine.json", sm)
        self.assertFails("L-08", "nothing.md", file="plugins/karvey/schemas/state-machine.json")


class L09(LintCase):
    def test_pass(self):
        self.assertPasses("L-09")

    def test_rule_cited_without_the_folder(self):
        self.t.append(REQS, "\nSee `karvey/rules/phase-close.md`.\n")
        self.assertFails("L-09", "karvey/rules/phase-close.md", file=REQS)

    def test_rules_prefix_from_a_skill_without_rules(self):
        self.t.append(REQS, "\nSee rules/phase-close.md for the ritual.\n")
        self.assertFails("L-09", "rules/phase-close.md", file=REQS)

    def test_missing_plugin_root_path(self):
        self.t.append(REQS, '\nRun `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/missing.py"`.\n')
        self.assertFails("L-09", "scripts/missing.py")

    def test_markdown_link(self):
        self.t.append(RULES + "/phase-close.md", "\nSee [the rule](nope.md).\n")
        self.assertFails("L-09", "nope.md")

    def test_project_paths_in_plugin_readmes_are_not_citations(self):
        # hooks/README.md and plugins/karvey/README.md describe the user's project (F-24)
        self.t.write("plugins/karvey/hooks/README.md", "# Hooks\n\nReads `docs/spec/project.json`.\n")
        self.assertPasses("L-09")

    def test_repo_readme_docs_paths_still_resolve(self):
        self.t.append("README.md", "\nSee `docs/spec/missing.md`.\n")
        self.assertFails("L-09", "docs/spec/missing.md", file="README.md")

    def test_placeholders_and_project_paths_are_not_citations(self):
        self.t.append(REQS, "\nRead `docs/spec/changes/{change-id}/prd.md` and `rules/{name}.md`.\n")
        self.assertPasses("L-09")


class L10(LintCase):
    def test_pass(self):
        self.assertPasses("L-10")

    def test_hand_kept_copy(self):
        self.t.write(SKILLS + "/karvey-init/rules/phase-close.md", self.t.read(RULES + "/phase-close.md"))
        fs = self.assertFails("L-10", "hand-kept rule copy")
        self.assertIn(RULES + "/phase-close.md", fs[0]["message"])

    def test_generated_identical_copy_passes(self):
        src = self.t.read(RULES + "/phase-close.md")
        self.t.write(SKILLS + "/karvey-init/rules/phase-close.md",
                     "<!-- generated-from: ../../karvey/rules/phase-close.md -->\n" + src)
        self.assertPasses("L-10")

    def test_generated_copy_that_differs(self):
        self.t.write(SKILLS + "/karvey-init/rules/phase-close.md",
                     "<!-- generated-from: ../../karvey/rules/phase-close.md -->\nedited by hand\n")
        self.assertFails("L-10", "differs")


class L14(LintCase):
    def test_pass(self):
        self.assertPasses("L-14")

    def test_write_without_write(self):
        self.t.append(SKILLS + "/karvey-guard/SKILL.md", "\nWrite `docs/spec/changes/{id}/findings.md` with the result.\n")
        self.assertFails("L-14", "lacks Write")

    def test_ask_without_ask_user_question(self):
        self.t.append(SKILLS + "/karvey-guard/SKILL.md", "\nThen **ask the user** whether to continue.\n")
        self.assertFails("L-14", "lacks AskUserQuestion")

    def test_agent_without_agent(self):
        self.t.append(SKILLS + "/karvey-guard/SKILL.md", "\nLaunch two subagents in parallel.\n")
        self.assertFails("L-14", "lacks Agent")

    def test_bash_fence_without_bash(self):
        self.t.replace(SKILLS + "/karvey-guard/SKILL.md", "allowed-tools: Read, Edit, Bash", "allowed-tools: Read, Edit")
        self.t.append(SKILLS + "/karvey-guard/SKILL.md", "\n```bash\ngit status\n```\n")
        self.assertFails("L-14", "lacks Bash")

    def test_negated_write_passes(self):
        self.t.append(SKILLS + "/karvey-guard/SKILL.md", "\nNever write `docs/spec/project.json` by hand here.\n")
        self.assertPasses("L-14")


# --------------------------------------------------------------------------- L-11 .. L-13, L-17, L-18
PLUGIN_JSON = "plugins/karvey/.claude-plugin/plugin.json"
MARKET = ".claude-plugin/marketplace.json"


class L11(LintCase):
    def test_pass(self):
        self.assertPasses("L-11")

    def test_readme_support_count(self):
        self.t.sub("README.md", r"\d+ support skills", "18 support skills")
        self.assertFails("L-11", "says 18 support skills", file="README.md")

    def test_plugin_json_phase_count(self):
        self.t.sub(PLUGIN_JSON, r"a \d+-phase pipeline", "a 13-phase pipeline")
        self.assertFails("L-11", "phases", file=PLUGIN_JSON)

    def test_new_skill_changes_the_truth(self):
        self.t.write(SKILLS + "/karvey-docs/SKILL.md", self.t.read(SKILLS + "/karvey-guard/SKILL.md")
                     .replace("karvey-guard", "karvey-docs").replace('"karvey guard"', '"karvey docs"'))
        fs = self.assertFails("L-11", "support skills")
        self.assertEqual({f["file"] for f in fs}, {"README.md", "plugins/karvey/README.md", PLUGIN_JSON, MARKET})

    def test_rule_count(self):
        self.t.sub("README.md", r"\d+ rules", "99 rules")
        self.assertFails("L-11", "rules")


class L12(LintCase):
    def test_pass(self):
        self.assertPasses("L-12")

    def test_marketplace_disagrees(self):
        self.t.replace(MARKET, '"version": "1.0.0"', '"version": "0.9.0"')
        self.assertFails("L-12", "marketplace.json says 0.9.0", file=MARKET)

    def test_project_json_disagrees(self):
        self.t.replace("docs/spec/project.json", '"karvey_version": "1.0.0"', '"karvey_version": "0.9.0"')
        self.assertFails("L-12", "karvey_version", file="docs/spec/project.json")

    def test_changelog_top_release_disagrees(self):
        self.t.replace(PLUGIN_JSON, '"version": "1.0.0"', '"version": "1.1.0"')
        self.assertFails("L-12", "top CHANGELOG release is 1.0.0", file="CHANGELOG.md")

    def test_unreleased_is_not_a_release(self):
        s = self.t.read("CHANGELOG.md")
        self.t.write("CHANGELOG.md", s.split("## [1.0.0]")[0])
        self.assertFails("L-12", "no numbered release")


class L13(LintCase):
    def test_pass(self):
        self.assertPasses("L-13")

    def test_top_release_without_why(self):
        self.t.replace("CHANGELOG.md", "### Why\nA fixture for the linter.\n", "")
        self.assertFails("L-13", "Why", file="CHANGELOG.md")

    def test_page_history_behind(self):
        self.t.replace("docs/karvey.html",
                       '<li class="now"><span class="ver">1.0.0</span><span class="date">24-09-2026',
                       '<li class="now"><span class="ver">0.9.0</span><span class="date">01-09-2026')
        self.assertFails("L-13", "'es' marks 0.9.0", file="docs/karvey.html")

    def test_block_without_current(self):
        self.t.replace("docs/karvey.html",
                       '<li class="now"><span class="ver">1.0.0</span><span class="date">2026-09-24',
                       '<li><span class="ver">1.0.0</span><span class="date">2026-09-24')
        self.assertFails("L-13", "'en' has no version marked current")


class L17(LintCase):
    def test_pass(self):
        self.assertPasses("L-17")

    def test_undocumented_project_field(self):
        self.t.replace(RULES + "/project-config.md", '"project": "Name",', '"project": "Name",\n  "shiny_flag": true,')
        self.assertFails("L-17", "shiny_flag", file=RULES + "/project-config.md")

    def test_undocumented_nested_spec_field(self):
        self.t.replace(RULES + "/living-specs.md", '"approved": false}', '"approved": false, "stamp": 1}')
        self.assertFails("L-17", "approvals.requirements.stamp")

    def test_map_values_are_not_fields(self):
        self.t.replace(RULES + "/living-specs.md", '{"mockup": "no UI"}', '{"mockup": "no UI", "infra": "no cloud"}')
        self.assertPasses("L-17")

    def test_unsupported_schema_keyword(self):
        for name in ("spec.schema.json", "state-machine.json"):
            self.t.write("plugins/karvey/schemas/" + name, (_path.SCHEMAS_DIR / name).read_text(encoding="utf-8"))
        schema = json.loads((_path.SCHEMAS_DIR / "project.schema.json").read_text(encoding="utf-8"))
        schema["patternProperties"] = {"^x-": {}}
        self.t.write("plugins/karvey/schemas/project.schema.json", schema)
        self.assertFails("L-17", "unsupported keyword 'patternProperties'")


class L18(LintCase):
    SPEC = "docs/spec/changes/feat-a/spec.json"

    def test_pass(self):
        self.assertPasses("L-18")

    def test_enum_violation(self):
        self.t.replace(self.SPEC, '"phase": "requirements",\n', '"phase": "qa-approved",\n')
        self.assertFails("L-18", "phase", file=self.SPEC)

    def test_prod_ref_missing(self):
        spec = json.loads(self.t.read(self.SPEC))
        spec["approvals"]["prod"] = {"approved": True, "by": "X", "role": "human",
                                     "date": "2026-09-24T10:00:00-03:00", "ref": ""}
        self.t.write(self.SPEC, spec)
        self.assertFails("L-18", "prod.ref")

    def test_legacy_shape_is_a_warning_in_advisory_mode(self):
        self.t.replace("docs/spec/project.json",
                       '{"tool": "markdown", "location": "docs/spec/changes/{change-id}/PLAN.md"}', '"none"')
        fs = lint(self.t.root, ["L-18"])
        self.assertTrue(fs)
        self.assertEqual({f["severity"] for f in fs}, {"warning"})


# --------------------------------------------------------------------------- L-15, L-16, L-19 .. L-24
IMPL = SKILLS + "/karvey-impl/SKILL.md"
QA = SKILLS + "/karvey-qa/SKILL.md"
DEPLOY = SKILLS + "/karvey-deploy/SKILL.md"
ARCHIVE = SKILLS + "/karvey-archive/SKILL.md"
ENF = RULES + "/enforcement.md"
HOOKS_README = "plugins/karvey/hooks/README.md"
TABLE = "plugins/karvey/tests/hooks/tables/mini.json"


class L15(LintCase):
    def test_pass(self):
        self.assertPasses("L-15")

    def test_phantom_clickup_sync_guard(self):
        self.t.append(RULES + "/phase-close.md", "\n`karvey-guard` can install a `clickup-sync-guard` hook.\n")
        self.assertFails("L-15", "clickup-sync-guard is cited but the plugin does not ship it")

    def test_phantom_standards_guard(self):
        self.t.append(INIT, "\nThe standards-guard hook warns on impl.\n")
        self.assertFails("L-15", "standards-guard", file=INIT)

    def test_shipped_hook_without_table_cases(self):
        table = json.loads(self.t.read(TABLE))
        table["cases"] = [c for c in table["cases"] if c["guard"] != "plan-gate"]
        self.t.write(TABLE, table)
        self.t.replace(ENF, " <!-- guard-case: pg-01 -->", "")
        self.assertFails("L-15", "plan-gate has no guard-table cases")

    def test_skill_names_are_not_hooks(self):
        self.t.append(INIT, "\nRun `/karvey-guard` to set the hooks.\n")
        self.assertPasses("L-15")


class L16(LintCase):
    def test_pass(self):
        self.assertPasses("L-16")

    def test_unanchored_promise(self):
        self.t.append(ENF, "\nThe git-flow guard blocks a push to main.\n")
        self.assertFails("L-16", "without a <!-- guard-case", file=ENF)

    def test_anchor_to_a_missing_case(self):
        self.t.append(HOOKS_README, "- A PR into dev passes silently. <!-- guard-case: prod-99 -->\n")
        self.assertFails("L-16", "prod-99 is not a case", file=HOOKS_README)

    def test_verb_contradicts_the_case(self):
        self.t.replace(ENF, "blocks an edit without an approved plan. <!-- guard-case: pg-01 -->",
                       "blocks an edit without an approved plan. <!-- guard-case: pg-02 -->")
        self.assertFails("L-16", "pg-02 expects allow")

    def test_readme_says_nothing_while_the_case_prints(self):
        self.t.append(HOOKS_README, "- A Karvey project without settings prints nothing. <!-- guard-case: prod-02 -->\n")
        self.assertFails("L-16", "contradicts")


    def test_context_contains_counts_as_prints(self):
        # session cases assert what the hook adds to the context (F-34)
        case = {"expect": {"decision": "allow", "context_contains": ["[karvey]"]}}
        self.assertTrue(lp._case_fits(case, {"prints"}))
        self.assertFalse(lp._case_fits(case, {"silent"}))


class Fences(unittest.TestCase):
    def test_longer_outer_fence_is_not_closed_by_an_inner_one(self):
        lines = ["````markdown", "```bash", "echo hi", "```", "still inside", "````", "outside"]
        langs = {line: lang for _, line, lang in lp.iter_lines(lines)}
        self.assertEqual(langs["still inside"], "markdown")
        self.assertIsNone(langs["outside"])

    def test_plain_fence_still_closes(self):
        lines = ["```json", "{}", "```", "prose"]
        langs = {line: lang for _, line, lang in lp.iter_lines(lines)}
        self.assertEqual(langs["{}"], "json")
        self.assertIsNone(langs["prose"])


class L19(LintCase):
    def test_pass(self):
        self.assertPasses("L-19")

    def test_bump_per_commit(self):
        self.t.append(ORCH, "\nExecutes tasks on `feature/{id}` (never dev/master). Version bump + CHANGELOG per commit.\n")
        self.assertFails("L-19", "per commit", file=ORCH)

    def test_unreleased_per_commit_one_bump_per_release_passes(self):
        self.t.append(ORCH, "\nCHANGELOG `[Unreleased]` per commit; one bump per release.\n")
        self.assertPasses("L-19")

    def test_impl_bumps(self):
        self.t.append(IMPL, "\n**Version bump:** increment `rev` in `package.json`.\n")
        self.assertFails("L-19", "karvey-impl bumps", file=IMPL)

    def test_qa_without_unreleased(self):
        self.t.write(QA, self.t.read(QA).replace("[Unreleased]", "CHANGELOG"))
        self.assertFails("L-19", "karvey-qa never mentions [Unreleased]", file=QA)

    def test_deploy_without_unreleased(self):
        self.t.write(DEPLOY, self.t.read(DEPLOY).replace("[Unreleased]", "the new entry"))
        self.assertFails("L-19", "karvey-deploy", file=DEPLOY)

    def test_versioning_rule_without_per_release(self):
        self.t.replace(RULES + "/versioning.md", "Each release increments the version once",
                       "Each commit increments the version")
        self.assertFails("L-19", file=RULES + "/versioning.md")


class L20(LintCase):
    def test_pass(self):
        self.assertPasses("L-20")

    def test_rule_item_absent_from_d6(self):
        self.t.append(RULES + "/versioning.md", "- DEV shows the `-dev` pre-release format.\n")
        self.assertFails("L-20", "-dev")

    def test_anchored_items(self):
        self.t.append(RULES + "/versioning.md", "\n<!-- qa-item: visible version -->\n")
        self.assertFails("L-20", "visible version")

    def test_rule_assigns_qa_without_items(self):
        self.t.write(RULES + "/versioning.md", "# Rule\n\nEach release increments it. Verified by karvey-qa.\n")
        self.assertFails("L-20", "lists no QA items")


class L21(LintCase):
    def test_pass(self):
        self.assertPasses("L-21")

    def test_actual_into_estimate(self):
        self.t.append(IMPL, '\n```bash\ncurl -X PUT "$URL" -d \'{"time_estimate": {actual_time_ms}}\'\n```\n')
        self.assertFails("L-21", "estimate field", file=IMPL)

    def test_estimate_assigned_actual(self):
        self.t.append(RULES + "/phase-close.md", "\nSet `estimate = actual` when the task closes.\n")
        self.assertFails("L-21")


class L22(LintCase):
    def test_pass(self):
        self.assertPasses("L-22")

    def test_second_literal_in_text(self):
        self.t.append(RULES + "/phase-close.md", "\nRotation thresholds: 150k of context, 24 h, or a work block.\n")
        self.assertFails("L-22", "24 h")

    def test_literal_in_a_hook_script(self):
        self.t.write("plugins/karvey/hooks/karvey-statusline.sh",
                     "HOURS = float(os.environ.get('KARVEY_ROTATE_HOURS', 8))\n")
        self.assertFails("L-22", "literal 8")

    def test_citing_defaults_passes(self):
        self.t.append(RULES + "/phase-close.md",
                      "\nRotation threshold: 8 h, read from `karvey_lib/defaults.json` (`rotation_hours`).\n")
        self.assertPasses("L-22")

    def test_rate_limit_windows_are_not_thresholds(self):
        self.t.append(HOOKS_README, "\nRotation statusline: `5h 29% ↻18:05 (1h31m)`.\n")
        self.assertPasses("L-22")


class L23(LintCase):
    def test_pass(self):
        self.assertPasses("L-23")

    def test_sync_in_a_phase_skill(self):
        self.t.append(QA, "\nSync knowledge per `../karvey/rules/knowledge-sync.md` (`/graphify docs/spec/ --update`).\n")
        self.assertFails("L-23", "outside archive", file=QA)

    def test_sync_in_a_rule(self):
        self.t.append(RULES + "/phase-close.md", "\n4. Sync knowledge per `knowledge-sync.md`.\n")
        self.assertFails("L-23", file=RULES + "/phase-close.md")

    def test_on_demand_path_passes(self):
        self.t.append(QA, "\nThe user may run `/graphify docs/spec/` on demand.\n")
        self.assertPasses("L-23")


class L24(LintCase):
    def test_pass(self):
        self.assertPasses("L-24")

    def test_comment_per_task(self):
        self.t.append(IMPL, "\nThis is the per-task close ritual: comment + status + cascade, applied to every task.\n")
        self.assertFails("L-24", "per task", file=IMPL)

    def test_status_per_task_then_comment_per_feature_passes(self):
        self.t.append(IMPL, "\nStatus per task, comment and cascade per Feature.\n")
        self.assertPasses("L-24")

    def test_phase_close_without_per_feature(self):
        self.t.write(RULES + "/phase-close.md", "# Rule: phase close\n\nComment and set the status.\n")
        self.assertFails("L-24", "per Feature")


# --------------------------------------------------------------------------- L-25 .. L-30
ADAPTERS = RULES + "/management-adapters.md"


class L25(LintCase):
    def test_pass(self):
        self.assertPasses("L-25")

    def test_qa_commits(self):
        self.t.append(QA, "\n- For visual fixes: apply **atomic commits** (one fix per commit).\n")
        self.assertFails("L-25", "QA instructs a commit", file=QA)

    def test_qa_never_commits_passes(self):
        self.t.append(QA, "\nQA never commits: it does not apply atomic commits.\n")
        self.assertPasses("L-25")

    def test_review_outside_the_change(self):
        self.t.replace(QA, "`docs/spec/changes/{change-id}/qa/REVISION_PR_{n}_{date}.md`", "`REVISION_PR_{n}.md`")
        self.assertFails("L-25", "does not write its review", file=QA)

    def test_deploy_reads_newest_at_root(self):
        self.t.append(DEPLOY, "\nLocate the review: `ls -t REVISION_PR_*.md | head -1`.\n")
        self.assertFails("L-25", "newest REVISION_PR", file=DEPLOY)

    def test_review_at_repo_root(self):
        self.t.write("REVISION_PR_17-19_20260923.md", "# review\n")
        self.assertFails("L-25", "sits at the repo root", file="REVISION_PR_17-19_20260923.md")


class L26(LintCase):
    def test_pass(self):
        self.assertPasses("L-26")

    def test_axios_rule(self):
        self.t.append(QA, "\n- Every HTTP call goes through `apiService` (Axios), never `fetch`.\n")
        self.assertFails("L-26", "apiService", file=QA)

    def test_v_html_and_rut(self):
        self.t.append(QA, "\n- No `v-html` with user data.\n- Validate the RUT.\n")
        fs = self.assertFails("L-26")
        self.assertEqual(len(fs), 2)


class L27(LintCase):
    def test_pass(self):
        self.assertPasses("L-27")

    def test_prod_approval_committed(self):
        self.t.append(DEPLOY, "\nRecord `approvals.prod` in spec.json and commit it on the branch that goes to "
                              "`master`. The prod gate is never delegated.\n")
        self.assertFails("L-27", "prod approval with a commit", file=DEPLOY)

    def test_push_before_checklist(self):
        self.t.replace(DEPLOY, "Pre-check:", "```bash\ngit push origin feature/x\n```\n\nPre-check:")
        self.assertFails("L-27", "comes before the 6-step checklist", file=DEPLOY)

    def test_no_checklist(self):
        self.t.replace(DEPLOY, "### Step 1 — 6-step checklist (before the first push)", "### Step 1 — Prepare")
        self.assertFails("L-27", "no pre-deploy checklist")

    def test_archive_without_its_branch(self):
        self.t.replace(ARCHIVE, "Start with `git checkout -b chore/archive-{change-id} origin/main`.\n\n", "")
        self.assertFails("L-27", "never creates chore/archive", file=ARCHIVE)

    def test_archive_commits_before_branching(self):
        self.t.replace(ARCHIVE, "Start with `git checkout -b chore/archive-{change-id} origin/main`.\n\n",
                       "```bash\ngit commit -m spec\n```\n\nThen `git checkout -b chore/archive-{change-id}`.\n\n")
        self.assertFails("L-27", "before creating chore/archive")


class L28(LintCase):
    def test_pass(self):
        self.assertPasses("L-28")

    def test_not_markdown_test(self):
        self.t.append(SKILLS + "/karvey-archive/SKILL.md", "\nIf `management.tool` != markdown, close the Epic.\n")
        self.assertFails("L-28", "!= markdown")

    def test_direct_backlog_list_id(self):
        self.t.append(REQS, "\nRead `project.json:clickup.backlog_list_id` for the list.\n")
        self.assertFails("L-28", "directly", file=REQS)

    def test_cascade_restated(self):
        self.t.append(IMPL, "\nWhen ALL tasks of a Feature are in `review`, move the Feature to `review`.\n")
        self.assertFails("L-28", "restates the cascade", file=IMPL)

    def test_epic_done_when_all_features(self):
        self.t.append(ADAPTERS, "\nThe Epic moves to done when all Features are done.\n")
        self.assertFails("L-28", "only at archive", file=ADAPTERS)

    def test_legend_without_awaiting_human(self):
        self.t.append(IMPL, "\n> Markers: `⬜ todo · 🔄 in_progress · 👀 review · ✅ done · ⛔ blocked`\n")
        self.assertFails("L-28", "🙋", file=IMPL)

    def test_phase_close_names_a_skill_that_does_not_cite_it(self):
        self.t.append(RULES + "/phase-close.md", "\nAlso run by `karvey-impl`.\n")
        self.assertFails("L-28", "names karvey-impl", file=IMPL)

    def test_skill_cites_phase_close_without_being_named(self):
        self.t.append(QA, "\nClose per `../karvey/rules/phase-close.md`.\n")
        self.assertFails("L-28", "karvey-qa cites phase-close.md", file=RULES + "/phase-close.md")

    def test_init_two_initial_epic_states(self):
        self.t.append(INIT, "\n- **Spreadsheet:** append an `epic` row with `status=todo`.\n"
                            "- **Markdown:** the Epic row starts 🔄 in_progress.\n")
        self.assertFails("L-28", "more than one initial state", file=INIT)


class L29(LintCase):
    def test_pass(self):
        self.assertPasses("L-29")

    def test_placeholder_in_a_command(self):
        self.t.append(DEPLOY, "\n```bash\ngit push origin {integration}\n```\n")
        self.assertFails("L-29", "{integration}", file=DEPLOY)

    def test_notification_target_placeholder(self):
        self.t.append(QA, '\n```bash\ngam create chatmessage space {notifications.target} text "done"\n```\n')
        self.assertFails("L-29", "{notifications.target}", file=QA)

    def test_direct_project_json_read(self):
        self.t.append(DEPLOY, "\n```bash\nLOC=$(jq -r .management.location docs/spec/project.json)\n```\n")
        self.assertFails("L-29", "reads project.json directly", file=DEPLOY)

    def test_unquoted_validated_value(self):
        self.t.replace(DEPLOY, 'git push origin "$INTEGRATION"', "git push origin $INTEGRATION")
        self.assertFails("L-29", "unquoted", file=DEPLOY)

    def test_get_without_shell(self):
        self.t.replace(DEPLOY, "get branch_flow.integration --shell)", "get branch_flow.integration)")
        self.assertFails("L-29", "without --shell")


class L30(LintCase):
    def test_pass(self):
        self.assertPasses("L-30")

    def test_two_decision_log_paths(self):
        self.t.replace(RULES + "/multi-agent.md", "`docs/spec/decisions.md`", "`docs/decisiones.md`")
        fs = self.assertFails("L-30", "decision-log path")
        self.assertEqual({f["file"] for f in fs}, {RULES + "/multi-agent.md", SKILLS + "/karvey-decisions/SKILL.md"})

    def test_e_1_99_in_init(self):
        self.t.append(INIT, '\n  keywords: "E{1..99}"\n')
        self.assertFails("L-30", "E{1..99}", file=INIT)

    def test_duplicate_e2e_block(self):
        self.t.append(SKILLS + "/karvey-test/SKILL.md", "\nFor each E2E flow step, document:\n\nFor each E2E flow step document:\n")
        self.assertFails("L-30", "duplicate")

    def test_readme_short_skill_name(self):
        self.t.append("README.md", "\nStart with `/karvey:grill`.\n")
        self.assertFails("L-30", "/karvey:karvey-grill", file="README.md")

    def test_readme_full_names_pass(self):
        self.t.append("README.md", "\nStart with `/karvey:karvey-grill`, or `/karvey:karvey`.\n")
        self.assertPasses("L-30")


# --------------------------------------------------------------------------- L-31 .. L-35
BUGS = "docs/bugs_dev_testing.md"


class L31(LintCase):
    def test_pass(self):
        self.assertPasses("L-31")

    def test_markdown_plus_clickup_in_plugin_json(self):
        self.t.replace(PLUGIN_JSON, "Mini Karvey: a", "Mini Karvey with a discovery backlog (Markdown + ClickUp): a")
        self.assertFails("L-31", "Markdown + ClickUp", file=PLUGIN_JSON)

    def test_readme_presents_clickup_as_the_tracker(self):
        self.t.append("README.md", "\n- Incident tracker per repo, complementary to ClickUp.\n")
        self.assertFails("L-31", "as if it were the tracker", file="README.md")

    def test_plugin_readme(self):
        self.t.append("plugins/karvey/README.md", "\nEvery phase posts a ClickUp comment.\n")
        self.assertFails("L-31", file="plugins/karvey/README.md")


class L32(LintCase):
    def test_pass(self):
        self.assertPasses("L-32")

    def test_resuelto_without_regression(self):
        self.t.replace(BUGS, "`plugins/karvey/hooks/karvey-hook.sh` case \"smoke\", and lint check L-12.",
                       "Checked by hand.")
        self.assertFails("L-32", "names no regression", file=BUGS)

    def test_regression_file_missing(self):
        self.t.replace(BUGS, "plugins/karvey/hooks/karvey-hook.sh", "plugins/karvey/tests/unit/test_gone.py")
        self.assertFails("L-32", "test_gone.py, which does not exist")

    def test_lint_id_missing(self):
        self.t.replace(BUGS, "lint check L-12", "lint check L-99")
        self.assertFails("L-32", "L-99")

    def test_open_incident_needs_nothing(self):
        self.t.append(BUGS, "\n## BUG-03 — Another\n- **Current state:** EN FIX\n")
        self.assertPasses("L-32")


class L33(LintCase):
    def test_pass(self):
        self.assertPasses("L-33")

    def test_duplicate_decision_heading_is_a_warning(self):
        self.t.append("docs/spec/decisions.md", "\n## D-02 — Allocated twice\n")
        fs = self.assertFails("L-33", "duplicate heading D-02")
        self.assertEqual({f["severity"] for f in fs}, {"warning"})
        code, _, _ = run_cli("--root", str(self.t.root), "--only", "L-33")
        self.assertEqual(code, 0)

    def test_duplicate_backlog_row(self):
        self.t.append("docs/spec/backlog.md", "| BL-02 | Again | open |\n")
        self.assertFails("L-33", "table row BL-02")


class L33Released(LintCase):
    """@req REQ-W2-071 — a duplicate newer than the release line is an error."""

    def setUp(self):
        super().setUp()
        import _gitrepo as g
        g.isolate_git()
        r = self.t.root
        g.init(r)
        g.commit_all(r, "fixture")
        g.with_origin(r)

    def test_duplicate_above_release_line_is_an_error(self):
        text = self.t.read("docs/spec/decisions.md")
        import re as _re
        top = max(int(x) for x in _re.findall(r"D-(\d+)", text))
        self.t.append("docs/spec/decisions.md", "\n## D-%02d — new\n\n## D-%02d — new again\n" % (top + 1, top + 1))
        fs = self.assertFails("L-33", "newer than the release line")
        self.assertIn("error", {f["severity"] for f in fs})

    def test_old_duplicate_stays_a_warning(self):
        self.t.append("docs/spec/decisions.md", "\n## D-02 — Allocated twice\n")
        fs = self.assertFails("L-33", "duplicate heading D-02")
        self.assertEqual({f["severity"] for f in fs}, {"warning"})


class L45(LintCase):
    """@req REQ-W2-071 — no bounded Epic range."""

    def test_pass(self):
        self.assertPasses("L-45")

    def test_epic_range_in_a_skill_fails(self):
        f = SKILLS + "/karvey-init/SKILL.md"
        self.t.append(f, "\nEpic ids run from E{1..99}.\n")
        self.assertFails("L-45", "E{1..99}", file=f)


class L34(LintCase):
    def test_pass(self):
        self.assertPasses("L-34")

    def test_subagent_prompt_writes_project_json(self):
        self.t.append(IMPL, "\nLaunch a subagent with this prompt: \"resolve the status map and write it to "
                            "docs/spec/project.json\".\n")
        self.assertFails("L-34", "subagent prompt allows writing project.json", file=IMPL)

    def test_subagent_forbidden_passes(self):
        self.t.append(IMPL, "\nSubagents read the settings; they never write project.json.\n")
        self.assertPasses("L-34")

    def test_project_json_write_outside_a_subagent_prompt_passes(self):
        self.t.append(INIT, "\nWrite the answers to `docs/spec/project.json` on a docs branch.\n")
        self.assertPasses("L-34")


class L35(LintCase):
    def test_pass_before_3_12(self):
        self.assertPasses("L-35")

    def release_3_12(self, extra=""):
        for rel in (PLUGIN_JSON, MARKET):
            self.t.replace(rel, '"version": "1.0.0"', '"version": "3.12.0"')
        self.t.replace("CHANGELOG.md", "## [1.0.0] - 2026-09-24\n", "## [3.12.0] - 2026-10-01\n" + extra)

    def test_3_12_without_the_line(self):
        self.release_3_12()
        self.assertFails("L-35", "compatibility line", file="CHANGELOG.md")

    def test_3_12_with_the_line(self):
        self.release_3_12("\n### Compatibility\n- Notification destinations are read only from project.json; "
                          "projects that relied on CLAUDE.md tables run `/karvey:karvey-init --settings`.\n")
        self.assertPasses("L-35")

    def test_3_12_release_date_must_be_recorded_for_d14(self):
        line = ("\n### Compatibility\n- Notification destinations are read only from project.json; "
                "projects that relied on CLAUDE.md tables run `/karvey:karvey-init --settings`.\n")
        self.release_3_12(line)
        rel = "plugins/karvey/scripts/karvey_lib/defaults.json"
        self.t.write(rel, {"pre_3_12_history": {"version": "3.12.0", "released_on": None}})
        self.assertFails("L-35", "3.12.0 release date 2026-10-01", file=rel)
        self.t.write(rel, {"pre_3_12_history": {"version": "3.12.0", "released_on": "2026-10-01"}})
        self.assertPasses("L-35")


class L36(LintCase):
    def test_pass(self):
        self.assertPasses("L-36")

    def test_completed_dependency_fails(self):
        # the pre-3.10 wording that caused the BUG-05 deadlock
        self.t.append(IMPL, "\n- Do not execute [Backend] until its dependent [DB] is completed\n")
        self.assertFails("L-36", "'completed'", file=IMPL)

    def test_first_pending_task_fails(self):
        self.t.append(IMPL, "\nIf nothing is specified: start from the first pending task.\n")
        self.assertFails("L-36", "'pending'", file=IMPL)

    def test_dependency_at_done_only_fails(self):
        self.t.append(IMPL, "\nStart a [Frontend] task only when its [Backend] dependency is `done`.\n")
        self.assertFails("L-36", "waits for `done` only", file=IMPL)

    def test_rule_not_stated_fails(self):
        self.t.replace(IMPL, "; a dependency is satisfied at `review` or `done`", "")
        self.assertFails("L-36", "does not state", file=IMPL)

    def test_completed_outside_the_selection_rule_passes(self):
        self.t.append(IMPL, "\nComment the Feature as completed with the files touched.\n")
        self.assertPasses("L-36")

    def test_code_block_is_ignored(self):
        self.t.append(IMPL, "\n```text\nnext pending task: none\n```\n")
        self.assertPasses("L-36")


class L40(LintCase):
    """@req REQ-W2-011 REQ-W2-021 — the lanes rule renders the lane table."""
    SRC = "plugins/karvey/schemas/lanes.json"
    RULE = RULES + "/lanes.md"

    def setUp(self):
        super().setUp()
        self.t.write(self.SRC, (_path.SCHEMAS_DIR / "lanes.json").read_text(encoding="utf-8"))
        self.t.write(self.RULE, (_path.PLUGIN_ROOT / "skills/karvey/rules/lanes.md").read_text(encoding="utf-8"))
        # the state machine the lane table is checked against
        self.t.write("plugins/karvey/schemas/state-machine.json",
                     (_path.SCHEMAS_DIR / "state-machine.json").read_text(encoding="utf-8"))

    def test_pass(self):
        self.assertPasses("L-40")

    def test_hand_edited_table_fails(self):
        self.t.replace(self.RULE, "| `standard` | m | s | s | m | o |", "| `standard` | m | s | s | m | s |")
        self.assertFails("L-40", "differs from render", file=self.RULE)

    def test_lane_missing_a_phase_fails(self):
        data = json.loads(self.t.read(self.SRC))
        del data["lanes"]["docs"]["phases"]["qa"]
        self.t.write(self.SRC, data)
        self.assertFails("L-40", "docs does not list qa", file=self.SRC)

    def test_missing_rule_fails(self):
        self.t.remove(self.RULE)
        self.assertFails("L-40", "rules/lanes.md is missing")


class L51(LintCase):
    """@req REQ-W2-023 REQ-W2-024 — rubrics per lens and a read-only judge template."""
    RULE = RULES + "/judges.md"

    def setUp(self):
        super().setUp()
        real = _path.PLUGIN_ROOT / "skills/karvey/rules"
        self.t.write(self.RULE, (real / "judges.md").read_text(encoding="utf-8"))
        for ph in ("requirements", "architecture", "qa"):
            self.t.write(RULES + "/judges/%s.md" % ph, (real / "judges" / ("%s.md" % ph)).read_text(encoding="utf-8"))

    def test_pass(self):
        self.assertPasses("L-51")

    def test_rubric_missing_a_default_lens_fails(self):
        self.t.replace(RULES + "/judges/architecture.md", "## Lens: agents-cost", "## Cost")
        self.assertFails("L-51", "no '## Lens: agents-cost' section", file=RULES + "/judges/architecture.md")

    def test_template_allowing_edit_fails(self):
        self.t.replace(self.RULE, "Allowed tools: Read, Grep, Glob", "Allowed tools: Read, Grep, Glob, Edit")
        self.assertFails("L-51", "exactly Read, Grep, Glob", file=self.RULE)

    def test_template_without_no_edit_fails(self):
        self.t.replace(self.RULE, "Do not edit any file. ", "")
        self.assertFails("L-51", "Do not edit any file", file=self.RULE)

    def test_missing_rubric_fails(self):
        self.t.remove(RULES + "/judges/qa.md")
        self.assertFails("L-51", "no rubric rules/judges/qa.md")


class L48(LintCase):
    """@req REQ-W2-006 REQ-W2-088 — the baseline precedes any Wave 2 default."""
    PJ = "docs/spec/project.json"

    def set_gates(self):
        pj = json.loads(self.t.read(self.PJ))
        pj["gates"] = "merged"
        self.t.write(self.PJ, pj)

    def test_pass_without_wave2_defaults(self):
        self.assertPasses("L-48")

    def test_gates_merged_without_baseline_fails(self):
        self.set_gates()
        self.assertFails("L-48", "no metrics baseline", file=self.PJ)

    def test_gates_merged_with_baseline_passes(self):
        self.set_gates()
        self.t.write("docs/spec/retros/baseline-2026-09-25.json", {"result": {}})
        self.assertPasses("L-48")

    def test_baseline_after_the_setting_commit_fails(self):
        import os
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.test", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@example.test", GIT_COMMITTER_DATE="2026-09-20T10:00:00+00:00",
                   GIT_AUTHOR_DATE="2026-09-20T10:00:00+00:00", GIT_CONFIG_GLOBAL="/dev/null",
                   GIT_CONFIG_NOSYSTEM="1")
        self.set_gates()
        for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "gates"]):
            subprocess.run(["git"] + cmd, cwd=str(self.t.root), env=env, check=True, capture_output=True)
        self.t.write("docs/spec/retros/baseline-2026-09-25.json", {"result": {}})
        self.assertFails("L-48", "dated after the first commit", file="docs/spec/retros/baseline-2026-09-25.json")
        self.t.write("docs/spec/retros/baseline-2026-09-19.json", {"result": {}})
        self.assertPasses("L-48")


class L50(LintCase):
    """@req REQ-W2-007 — the log_time column and the impl fallback."""
    ADAPTERS = RULES + "/management-adapters.md"

    def test_pass(self):
        self.assertPasses("L-50")

    def test_row_without_log_time_cell_fails(self):
        self.t.replace(self.ADAPTERS, "| **Jira** | REST | worklog | transition |", "| **Jira** | REST |  | transition |")
        self.assertFails("L-50", "Jira", file=self.ADAPTERS)

    def test_table_without_the_column_fails(self):
        self.t.replace(self.ADAPTERS, "| Tool | How the session does it | log_time | Notes |",
                       "| Tool | How the session does it | Time | Notes |")
        self.assertFails("L-50", "no log_time column", file=self.ADAPTERS)

    def test_impl_without_fallback_fails(self):
        self.t.replace(IMPL, "; when the tool's `log_time` is `none`, fill the actual columns", "")
        self.assertFails("L-50", "fall back", file=IMPL)


class L41L52(LintCase):
    """@req REQ-W2-034 REQ-W2-035 REQ-W2-040 — one gate question; -y = auto, never prod."""
    RULE = RULES + "/gates.md"
    PHASES = ("karvey-init", "karvey-requirements", "karvey-impl", "karvey-test", "karvey-qa", "karvey-deploy")
    CLOSE = "\n## Advance to the next phase\n\nClose the phase per `../karvey/rules/gates.md`.\n"

    def setUp(self):
        super().setUp()
        real = _path.PLUGIN_ROOT / "skills/karvey/rules/gates.md"
        self.t.write(self.RULE, real.read_text(encoding="utf-8"))
        for s in self.PHASES:
            self.t.append(SKILLS + "/%s/SKILL.md" % s, self.CLOSE)

    def test_pass(self):
        self.assertPasses("L-41")
        self.assertPasses("L-52")

    def test_second_question_after_approval_fails(self):
        f = SKILLS + "/karvey-qa/SKILL.md"
        self.t.append(f, "\nAfter the approval, ask: \"Shall we advance to the Deploy phase now?\"\n")
        self.assertFails("L-41", "second advance question", file=f)

    def test_closing_without_gates_citation_fails(self):
        f = SKILLS + "/karvey-requirements/SKILL.md"
        self.t.replace(f, "Close the phase per `../karvey/rules/gates.md`.", "Ask the user whether to go on.")
        self.assertFails("L-41", "does not cite rules/gates.md", file=f)

    def test_y_approving_prod_fails(self):
        f = SKILLS + "/karvey-deploy/SKILL.md"
        self.t.append(f, "\nWith `-y` the agent approves the production release for the user.\n")
        self.assertFails("L-52", "never approves production", file=f)

    def test_gates_rule_without_role_auto_fails(self):
        self.t.replace(self.RULE, "`--role auto`, and continues", "and continues")
        self.assertFails("L-52", "--role auto", file=self.RULE)


class ListAll(unittest.TestCase):
    def test_list_names_l01_to_l36(self):
        code, out, _ = run_cli("--root", str(_path.REPO_ROOT), "--list")
        self.assertEqual(code, 0, out)
        for i in range(1, 37):
            self.assertIn("L-%02d " % i, out)
        ids = [c.id for c in lp.registry()]
        self.assertEqual(ids[:36], ["L-%02d" % i for i in range(1, 37)])
        # wave2-structural checks start at L-40 (L-37..L-39 are reserved by project-upgrade)
        self.assertTrue(all(40 <= int(i[2:]) <= 54 for i in ids[36:]), ids[36:])


if __name__ == "__main__":
    unittest.main()
