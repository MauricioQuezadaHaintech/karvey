"""The step catalogue contract: schema + invariants, nothing evaluated on error (REQ-UP-008)."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
from karvey_lib import upgrade, upgrade_steps

CALLS = []


def _check(probe, params):
    CALLS.append("check")
    raise AssertionError("a check was evaluated")


def _fix(probe, params, values):
    CALLS.append("fix")
    raise AssertionError("a fix was evaluated")


REG = {"t_check": _check, "t_fix": _fix}
GOOD = {"id": "t-step", "since": "3.13.0", "check": "t_check", "fix": "t_fix", "dry_run": True,
        "human": False, "risk": "low"}


class Catalogue(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        CALLS.clear()

    def tearDown(self):
        self._t.cleanup()

    def load(self, steps, **top):
        doc = {"catalogue_version": 1, "steps": steps}
        doc.update(top)
        p = Path(self._t.name) / "upgrade-steps.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        return upgrade.load_catalogue(p, registry=REG)

    def refused(self, steps, needle, **top):
        with self.assertRaises(upgrade.CatalogueError) as cm:
            self.load(steps, **top)
        self.assertIn(needle, str(cm.exception))
        self.assertEqual(CALLS, [], "nothing may be evaluated on a bad catalogue")
        return str(cm.exception)

    def test_good_step_loads_with_defaults(self):
        steps = self.load([GOOD])
        self.assertEqual(len(steps), 1)
        s = steps[0]
        self.assertEqual((s["report_only"], s["writes"], s["cost"], s["params"]), (False, ["project"], "low", {}))
        self.assertEqual(CALLS, [])

    def test_each_required_field_missing_is_named(self):
        for f in upgrade.REQUIRED_FIELDS:
            st = copy.deepcopy(GOOD)
            del st[f]
            with self.subTest(field=f):
                name = "#1" if f == "id" else "t-step"
                self.refused([st], "step %s: missing field %s" % (name, f))

    def test_duplicate_id(self):
        self.refused([GOOD, dict(GOOD)], "step t-step: duplicate id")

    def test_unknown_check_and_fix(self):
        self.refused([dict(GOOD, check="nope")], "unknown check function nope")
        self.refused([dict(GOOD, fix="nope")], "unknown fix function nope")

    def test_human_implies_fix_null(self):
        self.refused([dict(GOOD, human=True)], "a human step has fix null")
        self.assertEqual(self.load([dict(GOOD, human=True, fix=None)])[0]["human"], True)

    def test_report_only_implies_fix_null(self):
        self.refused([dict(GOOD, report_only=True)], "a report_only step has fix null")

    def test_fix_null_without_human_needs_report_only(self):
        self.refused([dict(GOOD, fix=None)], "fix null on a non-human step requires report_only")
        self.assertTrue(self.load([dict(GOOD, fix=None, report_only=True)])[0]["report_only"])

    def test_writes_outside_the_allowed_scopes(self):
        self.refused([dict(GOOD, writes=["home"])], "step t-step")
        self.assertEqual(self.load([dict(GOOD, writes=["project", "git_dir"])])[0]["writes"], ["project", "git_dir"])

    def test_schema_values(self):
        self.refused([dict(GOOD, risk="huge")], "step t-step: $.steps[0].risk")
        self.refused([dict(GOOD, id="Bad Id")], "step Bad Id")
        self.refused([dict(GOOD, since="3.13")], "since")
        self.refused([GOOD], "catalogue_version", catalogue_version=2)
        self.refused([], "fewer than 1 items")

    def test_missing_and_invalid_file(self):
        with self.assertRaises(upgrade.CatalogueError):
            upgrade.load_catalogue(Path(self._t.name) / "absent.json", registry=REG)
        p = Path(self._t.name) / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        with self.assertRaises(upgrade.CatalogueError) as cm:
            upgrade.load_catalogue(p, registry=REG)
        self.assertIn("unreadable", str(cm.exception))

    def test_shipped_catalogue_loads(self):
        steps = upgrade.load_catalogue()
        self.assertTrue(steps)
        for s in steps:
            self.assertIn(s["check"], upgrade_steps.REGISTRY)

    def test_shipped_catalogue_has_exactly_the_eight_steps_in_order(self):
        self.assertEqual([s["id"] for s in upgrade.load_catalogue()], [
            "schema-migrate", "schema-migrate-proposed", "legacy-shims", "team-settings", "enforcement-defaults",
            "statusline-launcher", "global-config", "changes-in-flight"])
        by = {s["id"]: s for s in upgrade.load_catalogue()}
        self.assertTrue(by["statusline-launcher"]["human"] and by["global-config"]["human"])
        self.assertTrue(by["changes-in-flight"]["report_only"])
        self.assertEqual({s["since"] for s in by.values()}, {"3.13.0"})


if __name__ == "__main__":
    unittest.main()
