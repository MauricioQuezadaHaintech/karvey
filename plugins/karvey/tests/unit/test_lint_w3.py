"""Wave 3 linter checks L-55..L-75 (architecture §1.25): one passing and one failing mutation per check.

Each case copies the good mini-plugin of ``test_lint_plugin`` and applies one mutation.
"""
import json
import unittest

import _path
from test_lint_plugin import SKILLS, LintCase

MODES = "plugins/karvey/schemas/check-modes.json"


class L62(LintCase):
    """@req REQ-W3-072 — a Load: entry names an existing file."""
    SKILL = SKILLS + "/karvey-qa/SKILL.md"

    def test_good_fixture_passes(self):
        self.assertPasses("L-62")

    def test_existing_entry_passes(self):
        self.t.write(SKILLS + "/karvey/rules/gates.md", "# Gates\n")
        self.t.sub(self.SKILL, r"(?m)^(# .*)$", r"\1\nLoad: gates.md")
        self.assertPasses("L-62")

    def test_missing_reference_fails_naming_skill_line_and_file(self):
        self.t.sub(self.SKILL, r"(?m)^(# .*)$", r"\1\nLoad: references/gone.md")
        fs = self.assertFails("L-62", "references/gone.md", file=self.SKILL)
        self.assertIn("skill karvey-qa", fs[0]["message"])
        text = self.t.read(self.SKILL).splitlines()
        self.assertEqual(text[fs[0]["line"] - 1], "Load: references/gone.md")


class L73(LintCase):
    """@req REQ-W3-061 — every check id used in code is registered with a 4.1 mode."""
    SCRIPT = "plugins/karvey/scripts/karvey-sample.py"

    def setUp(self):
        super().setUp()
        self.t.write(MODES, json.loads((_path.SCHEMAS_DIR / "check-modes.json").read_text(encoding="utf-8")))

    def test_registered_id_passes(self):
        self.t.write(self.SCRIPT, "from karvey_lib import modes\nm = modes.resolve(root, \"risks.owner\")\n")
        self.assertPasses("L-73")

    def test_unregistered_id_fails(self):
        self.t.write(self.SCRIPT, "from karvey_lib import modes\n\nm = modes.resolve(root, \"nope.check\")\n")
        fs = self.assertFails("L-73", "'nope.check'", file=self.SCRIPT)
        self.assertEqual(fs[0]["line"], 3)

    def test_row_without_41_fails(self):
        reg = json.loads(self.t.read(MODES))
        del reg["checks"][0]["defaults"]["4.1"]
        self.t.write(MODES, reg)
        self.assertFails("L-73", "no 4.1 default", file=MODES)


class L47(LintCase):
    """@req REQ-W2-083 REQ-W2-085 — the Wave 2 rows keep their 3.13/4.0 contract."""

    def setUp(self):
        super().setUp()
        self.t.write(MODES, json.loads((_path.SCHEMAS_DIR / "check-modes.json").read_text(encoding="utf-8")))

    def test_registry_passes(self):
        self.assertPasses("L-47")

    def test_blocking_313_default_fails(self):
        reg = json.loads(self.t.read(MODES))
        row = next(c for c in reg["checks"] if c["id"] == "lane.diff")
        row["defaults"]["3.13"] = "blocking"
        self.t.write(MODES, reg)
        self.assertFails("L-47", "lane.diff: the 3.13 default", file=MODES)


class L63(LintCase):
    """@req REQ-W3-017 — no text stops, shortens, skips or asks because of cost."""
    SKILL = SKILLS + "/karvey-qa/SKILL.md"

    def test_good_fixture_passes(self):
        self.assertPasses("L-63")

    def test_negated_statement_passes(self):
        self.t.append(self.SKILL, "\nThe judge flow never stops when the cost exceeds an estimate: cost is measured.\n")
        self.assertPasses("L-63")

    def test_stop_when_the_cost_exceeds_fails(self):
        self.t.append(self.SKILL, "\nStop when the cost exceeds the limit set in project.json.\n")
        self.assertFails("L-63", "because of cost", file=self.SKILL)

    def test_ask_to_confirm_over_budget_fails(self):
        self.t.append(self.SKILL, "\nIf the run is over budget, ask to confirm before the next lens.\n")
        self.assertFails("L-63", "ask to confirm", file=self.SKILL)


WORDING = "plugins/karvey/schemas/wording.json"


class L65(LintCase):
    """@req REQ-W3-080 — the wording table is complete per listed language."""

    def setUp(self):
        super().setUp()
        self.t.write(WORDING, json.loads((_path.SCHEMAS_DIR / "wording.json").read_text(encoding="utf-8")))

    def test_REQ_W3_080_english_risk_wording(self):
        w = json.loads((_path.SCHEMAS_DIR / "wording.json").read_text(encoding="utf-8"))
        self.assertEqual({k: v["en"] for k, v in w["risk_states"].items()},
                         {"open": "being watched", "mitigated": "reduced", "accepted": "accepted as is",
                          "closed": "no longer a risk", "moved": "carried to later work"})

    def test_complete_table_passes(self):
        self.assertPasses("L-65")

    def test_REQ_W3_080_a_state_removed_from_es_names_state_and_language(self):
        w = json.loads(self.t.read(WORDING))
        del w["risk_states"]["moved"]["es"]
        self.t.write(WORDING, w)
        self.assertFails("L-65", "risk state 'moved' has no wording in 'es'", file=WORDING)

    def test_a_phase_without_wording_fails(self):
        w = json.loads(self.t.read(WORDING))
        del w["phases"]["qa"]
        self.t.write(WORDING, w)
        self.assertFails("L-65", "phase 'qa' has no wording in 'en'")


TEMPLATE = "plugins/karvey/templates/sponsor.html"


class L64(LintCase):
    """@req REQ-W3-024 — no external request in the sponsor template or the method page."""

    def setUp(self):
        super().setUp()
        self.t.write(TEMPLATE, (_path.PLUGIN_ROOT / "templates" / "sponsor.html").read_text(encoding="utf-8"))

    def test_shipped_template_passes(self):
        self.assertPasses("L-64")

    def test_REQ_W3_024_a_remote_font_fails(self):
        self.t.replace(TEMPLATE, "<style>", "<style>\n@import url(\"https://fonts.example.org/css?family=Sample\");")
        self.assertFails("L-64", "@import", file=TEMPLATE)

    def test_a_remote_script_on_the_method_page_fails(self):
        self.t.write("docs/karvey.html", "<html><script src=\"https://cdn.example.org/x.js\"></script></html>\n")
        self.assertFails("L-64", "external request", file="docs/karvey.html")


DESIGN_SKILL = SKILLS + "/karvey-design-graphic/SKILL.md"


class L66(LintCase):
    """@req REQ-W3-037 — no country-specific identifier as a template example."""

    def test_good_fixture_passes(self):
        self.assertPasses("L-66")

    def test_shipped_skill_passes(self):
        self.t.write(DESIGN_SKILL, (_path.PLUGIN_ROOT / "skills/karvey-design-graphic/SKILL.md").read_text(
            encoding="utf-8"))
        self.assertPasses("L-66")

    def test_REQ_W3_037_a_country_identifier_example_fails(self):
        self.t.write("plugins/karvey/templates/form.md", "| Field | Example |\n|---|---|\n| RUT | 12.345.678-5 |\n")
        self.assertFails("L-66", "country-specific identifier 'RUT'", file="plugins/karvey/templates/form.md")


class L67(LintCase):
    """@req REQ-W3-039 — design-graphic does not score itself."""

    def setUp(self):
        super().setUp()
        self.t.write(DESIGN_SKILL, (_path.PLUGIN_ROOT / "skills/karvey-design-graphic/SKILL.md").read_text(
            encoding="utf-8"))

    def test_shipped_skill_passes(self):
        self.assertPasses("L-67")

    def test_REQ_W3_039_a_score_table_in_the_output_fails(self):
        self.t.append(DESIGN_SKILL, "\n| Dimension | Score (0-10) | What a 10 would be |\n|---|---|---|\n")
        self.assertFails("L-67", "self-assigned design score", file=DESIGN_SKILL)


class L68(LintCase):
    """@req REQ-W3-040 REQ-W3-041 — a phase is never mapped to a Feature."""
    RULE = "plugins/karvey/skills/karvey/rules/sample-tracker.md"

    def test_good_fixture_passes(self):
        self.assertPasses("L-68")

    def test_the_new_text_passes(self):
        self.t.write(self.RULE, "The pipeline phases are a checklist of the Epic, never Features.\n")
        self.assertPasses("L-68")

    def test_REQ_W3_040_each_pipeline_phase_maps_to_a_feature_fails(self):
        self.t.write(self.RULE, "Each pipeline phase maps to a Feature of the Epic.\n")
        self.assertFails("L-68", "pipeline phase mapped to a Feature", file=self.RULE)


GUIDE = "docs/portability.md"


class L69(LintCase):
    """@req REQ-W3-053 — the portability guide covers every hook event and allowed tool."""

    def setUp(self):
        super().setUp()
        self.t.write(GUIDE, (_path.REPO_ROOT / "docs" / "portability.md").read_text(encoding="utf-8"))

    def test_the_guide_passes(self):
        self.assertPasses("L-69")

    def test_REQ_W3_053_a_new_hook_event_without_an_entry_fails(self):
        hj = json.loads(self.t.read("plugins/karvey/hooks/hooks.json"))
        (hj["hooks"] if "hooks" in hj else hj)["Notification"] = []
        self.t.write("plugins/karvey/hooks/hooks.json", hj)
        self.assertFails("L-69", "hook event Notification", file=GUIDE)

    def test_REQ_W3_053_an_allowed_tool_without_an_entry_fails(self):
        self.t.sub(SKILLS + "/karvey-qa/SKILL.md", r"(?m)^allowed-tools: (.*)$", r"allowed-tools: \1, NotebookEdit")
        self.assertFails("L-69", "tool NotebookEdit", file=GUIDE)



class L70(LintCase):
    """@req REQ-W3-055 — no OS-specific file-opening command in skills."""
    SKILL = SKILLS + "/karvey-qa/SKILL.md"

    def test_good_fixture_passes(self):
        self.assertPasses("L-70")

    def test_webbrowser_passes(self):
        self.t.append(self.SKILL, "\nOpen it: docs/x.html (or `python3 -m webbrowser docs/x.html`).\n")
        self.assertPasses("L-70")

    def test_REQ_W3_055_open_and_xdg_open_fail(self):
        self.t.append(self.SKILL, "\nOpen with: open docs/x.html\n\nor run `xdg-open x`\n")
        fs = self.assertFails("L-70", "OS-specific file-opening command", file=self.SKILL)
        self.assertEqual(len(fs), 2)



class L71(LintCase):
    """@req REQ-W3-056 — no fixed country time or IANA zone literal."""
    RULE = "plugins/karvey/skills/karvey/rules/sample-dates.md"

    def test_good_fixture_passes(self):
        self.assertPasses("L-71")

    def test_the_neutral_text_passes(self):
        self.t.write(self.RULE, "Dates use project.json:time_zone (an IANA name as Area/City), ISO 8601 with offset.\n")
        self.assertPasses("L-71")

    def test_REQ_W3_056_a_country_time_or_a_zone_literal_fails(self):
        self.t.write(self.RULE, "- **date**: local date (Chile, CLT/CLST) of the change.\n\nTZ=Europe/Madrid\n")
        fs = self.assertFails("L-71", "a fixed time zone or country time", file=self.RULE)
        self.assertEqual(len(fs), 2)



class L72(LintCase):
    """@req REQ-W3-060 — example actors are placeholders or roles."""
    RULE = "plugins/karvey/skills/karvey/rules/sample-actors.md"

    def test_good_fixture_passes(self):
        self.assertPasses("L-72")

    def test_placeholders_and_roles_pass(self):
        self.t.write(self.RULE, "Executor: {name / role}\n\n`karvey-state.py approve x qa --by \"{name}\" --role human`\n"
                                "\nOwner: tech lead\n\n| 2026-06-17 | detected | {human} / {AI model} | found |\n")
        self.assertPasses("L-72")

    def test_REQ_W3_060_a_person_as_executor_and_a_model_id_as_by_fail(self):
        self.t.write(self.RULE, "Executor: Jane Doe\n\n`karvey-state.py approve x qa --by \"claude-x\" --role human`\n"
                                "\n| 2026-06-17 | detected | J. Doe / a model | found |\n")
        fs = self.assertFails("L-72", file=self.RULE)
        self.assertEqual(len(fs), 3)
        msgs = " ".join(f["message"] for f in fs)
        self.assertIn("person's name ('Jane Doe')", msgs)
        self.assertIn("model id ('claude-x')", msgs)


CORE = SKILLS + "/karvey/rules/_core.md"
CONTRACTS = "plugins/karvey/schemas/contracts.json"


class L55(LintCase):
    """@req REQ-W3-003 — the core: at most 1,000 words, every contract heading with an id."""

    def setUp(self):
        super().setUp()
        self.t.write(CORE, "# Core\nFootnote citations are never opened.\n\n## Gate {#contract-gate}\nOne question.\n")
        self.t.write(CONTRACTS, {"contracts": [{"id": "gate", "anchor": "#contract-gate"}], "baseline": {}})

    def test_good_fixture_passes(self):
        self.assertPasses("L-55")

    def test_shipped_core_passes(self):
        self.t.write(CORE, (_path.SCRIPTS_DIR.parent / "skills" / "karvey" / "rules" / "_core.md").read_text(
            encoding="utf-8"))
        self.t.write(CONTRACTS, json.loads((_path.SCHEMAS_DIR / "contracts.json").read_text(encoding="utf-8")))
        self.assertPasses("L-55")

    def test_REQ_W3_003_a_core_of_1200_words_fails_with_the_count(self):
        self.t.write(CORE, self.t.read(CORE) + ("word " * 1200) + "\n")
        self.assertFails("L-55", "words, over the 1000-word limit", file=CORE)

    def test_a_contract_heading_without_an_id_fails(self):
        self.t.write(CORE, self.t.read(CORE) + "\n## Commits\nTrailer.\n")
        self.assertFails("L-55", "contract heading without an id", file=CORE)

    def test_a_registered_contract_missing_from_the_core_fails(self):
        self.t.write(CONTRACTS, {"contracts": [{"id": "gate", "anchor": "#contract-gate"},
                                               {"id": "prod-gate", "anchor": "#contract-prod-gate"}], "baseline": {}})
        self.assertFails("L-55", "contract prod-gate is not anchored in the core", file=CONTRACTS)


class L58(LintCase):
    """@req REQ-W3-006 — tracker API detail only in rules/adapters/."""
    SKILL = SKILLS + "/karvey-tasks/SKILL.md"

    def test_good_fixture_passes(self):
        self.assertPasses("L-58")

    def test_an_adapter_may_hold_the_call(self):
        self.t.write(SKILLS + "/karvey/rules/adapters/clickup.md",
                     "curl -s -X PUT https://api.clickup.com/api/v2/task/{id}\n")
        self.assertPasses("L-58")

    def test_REQ_W3_006_an_api_call_in_the_tasks_skill_fails(self):
        self.t.write(self.SKILL, "---\nname: karvey-tasks\n---\n# Tasks\n```bash\n"
                                 "curl -s https://api.clickup.com/api/v2/task/{id}\n```\n")
        self.assertFails("L-58", "api.clickup.com", file=self.SKILL)

    def test_an_mcp_call_in_a_shared_rule_fails(self):
        self.t.write(SKILLS + "/karvey/rules/phase-close.md", "# Close\nclickup_update_task(id, status=x)\n")
        self.assertFails("L-58", "clickup_update_task")


class L57(LintCase):
    """@req REQ-W3-005 — rules cite rules only in footnotes."""
    RULE = SKILLS + "/karvey/rules/phase-close.md"

    def test_good_fixture_passes(self):
        self.assertPasses("L-57")

    def test_REQ_W3_005_a_load_instruction_in_a_rule_fails(self):
        self.t.write(SKILLS + "/karvey/rules/gates.md", "# Gates\n")
        self.t.append(self.RULE, "\nLoad `rules/gates.md` before continuing.\n")
        fs = self.assertFails("L-57", "a load instruction of rule rules/gates.md", file=self.RULE)
        self.assertEqual(len(fs), 1)

    def test_a_footnote_citation_passes(self):
        self.t.write(SKILLS + "/karvey/rules/gates.md", "# Gates\n")
        self.t.append(self.RULE, "\nThe gate question[^r-g] comes last.\n\n[^r-g]: gates.md — context only.\n")
        self.assertPasses("L-57")


class L56(LintCase):
    """@req REQ-W3-004 — a skill reads only what its Load: line lists."""
    SKILL = SKILLS + "/karvey-qa/SKILL.md"

    def setUp(self):
        super().setUp()
        self.t.write(SKILLS + "/karvey/rules/gates.md", "# Gates\n")
        self.t.write(SKILLS + "/karvey/rules/x.md", "# X\n")
        self.t.write(self.SKILL, "---\nname: karvey-qa\n---\n# QA\nLoad: gates.md\n\nClose per `../karvey/rules/gates.md`.\n")

    def test_listed_citation_passes(self):
        self.assertPasses("L-56")

    def test_REQ_W3_004_read_a_rule_missing_from_load_fails_with_skill_line_rule(self):
        self.t.append(self.SKILL, "Read `../karvey/rules/x.md` first.\n")
        fs = self.assertFails("L-56", "cites ../karvey/rules/x.md", file=self.SKILL)
        self.assertIn("skill karvey-qa", fs[0]["message"])
        self.assertEqual(fs[0]["line"], 8)

    def test_a_footnote_citation_passes(self):
        self.t.append(self.SKILL, "Context[^r-x].\n\n[^r-x]: ../karvey/rules/x.md — context only.\n")
        self.assertPasses("L-56")


if __name__ == "__main__":
    unittest.main()
