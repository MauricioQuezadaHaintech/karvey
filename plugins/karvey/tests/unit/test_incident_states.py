"""Incident states: neutral names and localized aliases (architecture §1.22, C-22).

@req REQ-W3-057
"""
import unittest

import _path
from karvey_lib import incidents as inc


class States(unittest.TestCase):
    def test_REQ_W3_057_localized_history_maps_each_state(self):
        self.assertEqual([inc.neutral(s) for s in ("DETECTADO", "DIAGNOSTICADO", "EN FIX", "RESUELTO", "REABIERTO")],
                         ["detected", "diagnosed", "in-fix", "resolved", "reopened"])

    def test_neutral_names_validate(self):
        self.assertEqual([inc.neutral(s) for s in ("detected", "In-Fix", "in fix", "resolved")],
                         ["detected", "in-fix", "in-fix", "resolved"])
        self.assertTrue(inc.is_resolved("RESUELTO") and inc.is_resolved("resolved"))

    def test_REQ_W3_057_unknown_state_reported_with_the_accepted_list(self):
        self.assertIsNone(inc.neutral("PARKED"))
        self.assertIn("resolved (RESUELTO)", inc.accepted())


class Dashboard(unittest.TestCase):
    def run_ow(self, state):
        import contextlib
        import importlib.util
        import io
        import json
        import shutil
        import tempfile
        from pathlib import Path
        from _state import make_project
        tmp = Path(tempfile.mkdtemp(prefix="karvey-inc-"))
        self.addCleanup(shutil.rmtree, str(tmp), True)
        make_project(tmp, project={"repos": ["r"]})
        (tmp / "docs/bugs_dev_testing.md").write_text(
            "# Bugs\n\n## BUG-01 — sample\n\n- **Current state:** %s\n\n### Regression test\n`tests/x.py`\n" % state,
            encoding="utf-8")
        m = importlib.util.spec_from_file_location("karvey_context_inc", str(_path.SCRIPTS_DIR / "karvey-context.py"))
        mod = importlib.util.module_from_spec(m)
        m.loader.exec_module(mod)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            mod.main(["--root", str(tmp), "--section", "open-work", "--json"])
        return json.loads(out.getvalue())

    def test_resolved_in_either_name_is_not_open(self):
        for st in ("RESUELTO", "resolved"):
            self.assertEqual(self.run_ow(st)["result"]["open-work"]["bugs"], [], st)
        self.assertEqual(len(self.run_ow("in-fix")["result"]["open-work"]["bugs"]), 1)

    def test_unknown_state_is_a_warning_with_the_list(self):
        env = self.run_ow("PARKED")
        msgs = [w["message"] for w in env["warnings"] if w["code"] == "incident.state"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("accepted: detected (DETECTADO)", msgs[0])


if __name__ == "__main__":
    unittest.main()
