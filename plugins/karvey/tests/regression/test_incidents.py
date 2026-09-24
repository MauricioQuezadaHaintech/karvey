"""Regression index BUG-05..BUG-21 (architecture §6.4, REQ-W1-107, E1.F14.T3).

Each incident names the check that proves its fix. This file does not re-run those checks' own suites (CI
runs them: the unit suite, the guard tables, test-hooks.sh and the node page tests). It fails when:

- a named check disappears: a lint id leaves the registry, a table case id or a test function / node test
  title is renamed or deleted, a manual script or a test-hooks.sh section goes away;
- a named lint check reports an error on this repository (the check is run in process, so the fix is proved
  live, not only by its fixture);
- ``docs/bugs_dev_testing.md`` marks an incident RESUELTO while this index gives it no automated check, or
  its ``### Regression test`` section does not name one of the checks listed here (L-32 cross-checks the
  same section against the files on disk);
- ``docs/spec/incidents-index.md`` disagrees with the tracker on an incident's state.
"""
import ast
import importlib.util
import json
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent.parent
REPO = PLUGIN.parent.parent
TESTS = PLUGIN / "tests"
TRACKER = REPO / "docs" / "bugs_dev_testing.md"
INCIDENTS_INDEX = REPO / "docs" / "spec" / "incidents-index.md"

_spec = importlib.util.spec_from_file_location("lint_plugin", str(PLUGIN / "scripts" / "lint-plugin.py"))
lp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lp)

# Kinds: lint (L-NN) · table (file stem, case id) · unit (file, Class.test) · node (file, title fragment) ·
# hooks (test-hooks.sh section fragment) · manual (script under tests/manual/). "manual" alone is not an
# automated regression: an incident whose only checks are manual cannot be RESUELTO.
INDEX = {
    "BUG-05": [  # impl resume on dead states (REQ-W1-085)
        ("manual", "impl-resume.md"),
    ],
    "BUG-06": [  # legacy management string breaks the != markdown guards
        ("lint", "L-28"),
        ("unit", "test_config_resolve.py", "LegacyShapes.test_legacy_string_markdown"),
        ("unit", "test_config_resolve.py", "LegacyShapes.test_legacy_clickup_string_with_backlog_list_id"),
        ("unit", "test_config_resolve.py", "LegacyShapes.test_none_string_and_object_are_markdown"),
        ("unit", "test_config_resolve.py", "LegacyProjectFixtures.test_resolve_management"),
        ("unit", "test_state_fix.py", "Management.test_project_string"),
        ("unit", "test_state_fix.py", "Management.test_spec_none_to_markdown_and_string_kept"),
    ],
    "BUG-07": [("lint", "L-31")],  # README / plugin.json present ClickUp as the tracker
    "BUG-08": [  # invalid KARVEY_TZ silently falls back
        ("table", "statusline", "statusline-01-valid-tz-no-marker"),
        ("table", "statusline", "statusline-02-invalid-tz-marked"),
        ("table", "statusline", "statusline-03-no-tz-no-marker"),
    ],
    "BUG-09": [  # stray separator with only the 7-day window
        ("table", "statusline", "statusline-04-only-7d-no-leading-separator"),
        ("table", "statusline", "statusline-05-both-windows-one-separator"),
        ("table", "statusline", "statusline-06-only-5h"),
    ],
    "BUG-10": [  # malformed hash throws before the switch binds
        ("node", "test_page.mjs", "safeDecodeHash returns null for a malformed or empty hash, never throws (BUG-10)"),
        ("node", "test_page.mjs", "init with a malformed hash still binds the switch"),
    ],
    "BUG-11": [  # invalid ?lang= saved as the viewer's choice
        ("node", "test_page.mjs", "pickLang: a ?lang= link is one-off when a choice was saved (BUG-11"),
        ("node", "test_page.mjs", "pickLang: an invalid ?lang= is ignored and nothing is saved"),
        ("node", "test_page.mjs", "init: ?lang=xx saves nothing (BUG-11)"),
    ],
    "BUG-12": [  # switching language drops the other query parameters
        ("node", "test_page.mjs", "withLang changes only lang and keeps the other parameters (BUG-12"),
        ("node", "test_page.mjs", "init: switching keeps the other query parameters (BUG-12)"),
    ],
    "BUG-13": [  # no hashchange handling
        ("node", "test_page.mjs", "init binds hashchange and jumps to the shown block (BUG-13"),
    ],
    "BUG-14": [  # inert switch without JS
        ("unit", "test_page_static.py", "NoInertSwitch.test_switch_links_are_inside_a_hidden_container"),
        ("unit", "test_page_static.py", "NoInertSwitch.test_css_hides_the_switch_until_js"),
        ("unit", "test_page_static.py", "NoInertSwitch.test_scripts_add_the_js_class"),
        ("node", "test_page.mjs", "init shows the switch (hidden without JS, BUG-14)"),
    ],
    "BUG-15": [("lint", "L-15")],  # clickup-sync-guard referenced, nothing installs it
    "BUG-16": [  # hooks/README vs session-hook behaviour
        ("lint", "L-16"),
        ("table", "session", "ss-13-empty-notifications-startup-one-line"),
        ("table", "session", "ss-15-bare-openapi-under-karvey-parent-silent"),
        ("table", "session", "ss-20-non-karvey-dir-silent"),
    ],
    "BUG-17": [("lint", "L-13")],  # release docs incomplete (CHANGELOG Why, page history)
    # 3.11.3 / 3.11.4: already regression-tested in test-hooks.sh; listed, not re-implemented.
    "BUG-18": [("hooks", "every declared command runs as written (BUG-18")],
    "BUG-19": [("hooks", "team.json inside the repo (BUG-19)")],
    "BUG-20": [("hooks", "state.json paths (BUG-20)")],
    "BUG-21": [("hooks", "worktrees (BUG-21)")],
}
AUTOMATED = {"lint", "table", "unit", "node", "hooks"}


def check_path(ref):
    """The file on disk that holds the named check (repo-relative string)."""
    kind = ref[0]
    if kind == "lint":
        return "plugins/karvey/scripts/lint-plugin.py"
    if kind == "table":
        return "plugins/karvey/tests/hooks/tables/%s.json" % ref[1]
    if kind == "unit":
        return "plugins/karvey/tests/unit/%s" % ref[1]
    if kind == "node":
        return "plugins/karvey/tests/page/%s" % ref[1]
    if kind == "hooks":
        return "plugins/karvey/hooks/tests/test-hooks.sh"
    if kind == "manual":
        return "plugins/karvey/tests/manual/%s" % ref[1]
    raise AssertionError("unknown kind %r" % kind)


def test_names(path):
    """``{"Class.method"}`` of a unittest file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test"):
                    out.add("%s.%s" % (node.name, item.name))
    return out


def tracker_sections():
    """``{BUG-NN: {"state": str, "regression": str}}`` from docs/bugs_dev_testing.md."""
    out, cur, in_reg = {}, None, False
    for line in TRACKER.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(BUG-\d+)\b", line)
        if m:
            cur = out.setdefault(m.group(1), {"state": None, "regression": ""})
            in_reg = False
            continue
        if line.startswith("## "):
            cur = None
            continue
        if cur is None:
            continue
        m = re.search(r"\*\*Current state:\*\*\s*([A-Z ]+)", line)
        if m and cur["state"] is None:
            cur["state"] = m.group(1).strip()
        if re.match(r"^###\s+Regression", line, re.I):
            in_reg = True
            continue
        if line.startswith("### "):
            in_reg = False
        elif in_reg:
            cur["regression"] += line + "\n"
    return out


class NamedChecksExist(unittest.TestCase):
    def test_every_routed_incident_is_indexed(self):
        for n in range(5, 22):
            self.assertIn("BUG-%02d" % n, INDEX)

    def test_lint_ids_are_registered(self):
        known = {c.id for c in lp.registry()}
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] == "lint":
                    self.assertIn(ref[1], known, "%s names %s" % (bug, ref[1]))

    def test_table_cases_exist(self):
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] != "table":
                    continue
                data = json.loads((REPO / check_path(ref)).read_text(encoding="utf-8"))
                cases = data["cases"] if isinstance(data, dict) else data
                ids = {c.get("id") for c in cases}
                self.assertIn(ref[2], ids, "%s names table case %s/%s" % (bug, ref[1], ref[2]))

    def test_unit_tests_exist(self):
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] == "unit":
                    self.assertIn(ref[2], test_names(REPO / check_path(ref)), "%s names %s" % (bug, ref[1:]))

    def test_node_tests_exist(self):
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] != "node":
                    continue
                text = (REPO / check_path(ref)).read_text(encoding="utf-8")
                titles = re.findall(r"\btest\(\s*'((?:[^'\\]|\\.)*)'", text)
                self.assertTrue(any(ref[2] in t for t in titles), "%s names node test %r" % (bug, ref[2]))

    def test_hooks_sections_exist(self):
        text = (REPO / "plugins/karvey/hooks/tests/test-hooks.sh").read_text(encoding="utf-8")
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] == "hooks":
                    self.assertIn(ref[1], text, "%s names test-hooks.sh section %r" % (bug, ref[1]))

    def test_manual_scripts_exist(self):
        for bug, refs in INDEX.items():
            for ref in refs:
                if ref[0] == "manual":
                    p = REPO / check_path(ref)
                    self.assertTrue(p.is_file(), "%s names %s" % (bug, p))
                    self.assertIn("Expected:", p.read_text(encoding="utf-8"))


class NamedLintChecksPassOnThisRepo(unittest.TestCase):
    """The fix is proved live: each named lint check reports no error on this repository."""

    def test_named_lint_checks_are_green(self):
        ids = {ref[1] for refs in INDEX.values() for ref in refs if ref[0] == "lint"}
        findings = lp.run_checks(lp.Ctx(REPO), only=ids)
        errors = ["%s %s:%s %s" % (f["check"], f["file"], f["line"], f["message"])
                  for f in findings if f["severity"] == "error"]
        self.assertEqual(errors, [])


class TrackerAgreesWithTheIndex(unittest.TestCase):
    def setUp(self):
        self.sections = tracker_sections()

    def test_resuelto_needs_an_automated_check_named_in_the_tracker(self):
        for bug, refs in sorted(INDEX.items()):
            sec = self.sections.get(bug)
            self.assertIsNotNone(sec, "%s is not in docs/bugs_dev_testing.md" % bug)
            if sec["state"] != "RESUELTO":
                continue
            automated = [r for r in refs if r[0] in AUTOMATED]
            self.assertTrue(automated, "%s is RESUELTO but its only checks are manual" % bug)
            named = [r for r in automated
                     if check_path(r) in sec["regression"] or (r[0] == "lint" and r[1] in sec["regression"])]
            self.assertTrue(named, "%s: the tracker's Regression test section names none of %s" % (bug, automated))

    def test_incidents_index_state_matches_the_tracker(self):
        rows = {}
        for line in INCIDENTS_INDEX.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and re.match(r"^BUG-\d+$", cells[0]) and len(cells) >= 8:
                rows[cells[0]] = cells
        for bug, sec in self.sections.items():
            with self.subTest(bug=bug):
                self.assertIn(bug, rows, "%s missing from incidents-index.md" % bug)
                self.assertEqual(rows[bug][5], sec["state"])
                if sec["state"] == "RESUELTO":
                    self.assertNotIn(rows[bug][6], ("", "—"), "%s RESUELTO without a regression column" % bug)


if __name__ == "__main__":
    unittest.main()
