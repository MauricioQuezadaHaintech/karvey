"""REQ-HF-001..004, 029 (BUG-138, BUG-143): the scope of a production approval and its one answer line."""
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
import _gitrepo as g
from karvey_lib import approval

g.isolate_git()


def _change(root, cid, phase="impl"):
    g.write(root, "docs/spec/changes/%s/spec.json" % cid, {"change_id": cid, "phase": phase})


class ProdScope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = g.init(Path(self.tmp.name) / "app-web")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"feature_prefix": "feature/",
                                                                       "integration": "main", "production": "main"}})
        _change(self.root, "team-adapters")
        g.commit_all(self.root)

    def resolve(self, text, active="team-adapters", reason="single"):
        cleaned = approval.normalise(approval.strip_quoted(text))
        ids = [c.name for c in (self.root / "docs/spec/changes").iterdir()]
        act = {"change": active, "reason": reason, "candidates": [active] if active else []}
        return approval.resolve_prod_scope(self.root, cleaned, ids, act)

    def test_named_change_in_a_worktree_is_named_as_the_fix(self):
        wt = Path(self.tmp.name) / "app-web-wt-upgrade"
        g.run(["worktree", "add", "-q", "-b", "feature/project-upgrade", str(wt)], self.root)
        _change(wt, "project-upgrade", "deploying")
        r = self.resolve("aprobado para producción project-upgrade 3.13.0")
        self.assertIsNone(r["scope"])
        self.assertIn("is not in this working tree", r["why"])
        self.assertIn(str(wt.resolve()), r["why"])

    def test_named_change_on_a_branch_names_the_branch(self):
        g.run(["checkout", "-q", "-b", "feature/project-upgrade"], self.root)
        _change(self.root, "project-upgrade", "deploying")
        g.commit_all(self.root, "upgrade")
        g.run(["checkout", "-q", "main"], self.root)
        r = self.resolve("aprobado para producción project-upgrade")
        self.assertIsNone(r["scope"])
        self.assertIn("feature/project-upgrade", r["why"])

    def test_typo_is_found_nowhere(self):
        r = self.resolve("aprobado para producción proyect-upgrade")
        self.assertIsNone(r["scope"])
        self.assertIn("no worktree, branch or local clone holds it", r["why"])
        self.assertEqual(r["candidates"], [])  # BUG-158: never the active change

    def test_named_change_here_wins(self):
        _change(self.root, "project-upgrade")
        r = self.resolve("aprobado para producción project-upgrade")
        self.assertEqual(r["scope"], "project-upgrade")
        self.assertFalse(r["implicit"])

    def test_single_active_is_said_out_loud(self):
        r = self.resolve("aprobado para producción")
        self.assertEqual(r["scope"], "team-adapters")
        self.assertTrue(r["implicit"])

    def test_several_named(self):
        _change(self.root, "app-login")
        _change(self.root, "app-search")
        r = self.resolve("aprobado para producción app-login y app-search")
        self.assertIsNone(r["scope"])
        self.assertIn("one message per change", r["why"])

    def test_common_hyphenated_words_are_not_change_ids(self):
        r = self.resolve("aprobado para producción, go-live hoy")
        self.assertEqual(r["scope"], "team-adapters")
        self.assertTrue(r["implicit"])

    def test_bug148_change_id_without_hyphen_on_a_branch(self):
        g.run(["checkout", "-q", "-b", "feature/billing"], self.root)
        _change(self.root, "billing", "deploying")
        g.commit_all(self.root, "billing")
        g.run(["checkout", "-q", "main"], self.root)
        r = self.resolve("aprobado para producción billing")
        self.assertIsNone(r["scope"])
        self.assertIn("feature/billing", r["why"])

    def test_bug148_versions_and_release_names_are_not_change_ids(self):
        for text in ("aprobado para producción 3.12.1-hotfix", "ok merge a prod la PR release-3.13",
                     "aprobado para producción, roll-out hoy"):
            r = self.resolve(text)
            self.assertEqual(r["scope"], "team-adapters", text)

    def test_bug148_unknown_word_is_never_the_suggested_change(self):
        r = self.resolve("aprobado para producción del fix cross-tenant")
        self.assertIsNone(r["scope"])
        self.assertEqual(r["candidates"], [])  # BUG-158: nor the active change: «… <change-id>»

    def test_bug148_two_named_ids_one_inside_the_other(self):
        _change(self.root, "login")
        _change(self.root, "api-login")
        r = self.resolve("aprobado para producción login y api-login")
        self.assertIsNone(r["scope"])

    def test_phrase_language(self):
        self.assertEqual(approval.suggested_phrase("aprobado para produccion", "x"), "aprobado para producción x")
        self.assertEqual(approval.suggested_phrase("approved, ship it to production", None),
                         "approved for production <change-id>")

    def test_prod_words_without_approval_verdict(self):
        v = approval.classify("aprobado para producción, no hay más cambios")
        self.assertFalse(v["approved"])
        self.assertTrue(approval.prod_shaped("aprobado para producción, no hay más cambios"))
        self.assertFalse(approval.prod_shaped('el log dice "aprobado para producción"'))
        self.assertFalse(approval.prod_shaped("revisa la producción"))


if __name__ == "__main__":
    unittest.main()
