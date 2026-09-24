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
        self.t.replace("README.md", "1 support skills", "18 support skills")
        self.assertFails("L-11", "says 18 support skills", file="README.md")

    def test_plugin_json_phase_count(self):
        self.t.replace(PLUGIN_JSON, "a 2-phase pipeline", "a 13-phase pipeline")
        self.assertFails("L-11", "phases", file=PLUGIN_JSON)

    def test_new_skill_changes_the_truth(self):
        self.t.write(SKILLS + "/karvey-docs/SKILL.md", self.t.read(SKILLS + "/karvey-guard/SKILL.md")
                     .replace("karvey-guard", "karvey-docs").replace('"karvey guard"', '"karvey docs"'))
        fs = self.assertFails("L-11", "support skills")
        self.assertEqual({f["file"] for f in fs}, {"README.md", "plugins/karvey/README.md", PLUGIN_JSON, MARKET})

    def test_rule_count(self):
        self.t.replace("README.md", "3 rules", "4 rules")
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


if __name__ == "__main__":
    unittest.main()
