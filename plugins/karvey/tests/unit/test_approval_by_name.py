"""REQ-AN-001..007 (BUG-158): a production approval naming a change is recorded in the local clone that owns it,
found the way the prod-gate finds clones; ambiguity records nothing; the suggestion never names another change."""
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
from karvey_lib import approval, audit, karvey_hooks as kh, project as pj

g.isolate_git()

FLOW = {"branch_flow": {"feature_prefix": "feature/", "integration": "main", "production": "main"}}


def karvey_repo(path, *changes):
    root = g.init(path)
    g.write(root, "docs/spec/project.json", FLOW)
    for cid in changes:
        g.write(root, "docs/spec/changes/%s/spec.json" % cid, {"change_id": cid, "phase": "deploying"})
    g.commit_all(root)
    return root


def marker(root, scope):
    m, status = approval.read_marker(root, scope)
    return m if status == "ok" else None


def recorded(root, scope):
    return [r for r in audit.read(pj.state_dir(root, create=False)) if r.get("event") == "marker"
            and r.get("decision") == "recorded" and r.get("change") == scope]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dev = Path(self.tmp.name).resolve() / "work"
        self.web = karvey_repo(self.dev / "app-web", "web-search")
        self.api = karvey_repo(self.dev / "app-api", "api-rate-limit")
        env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(Path(self.tmp.name) / "state")})
        env.start()
        self.addCleanup(env.stop)

    def prompt(self, text, cwd=None):
        cwd = cwd or self.web
        out, err = io.StringIO(), io.StringIO()
        payload = {"session_id": "s1", "transcript_path": "", "cwd": str(cwd),
                   "hook_event_name": "UserPromptSubmit", "prompt": text}
        code = kh.dispatch("prompt", json.dumps(payload), env=dict(os.environ, CLAUDE_PROJECT_DIR=str(cwd)),
                           out=out, err=err)
        self.assertEqual(code, 0)
        return out.getvalue()


class ByName(Base):
    def test_bug158_named_change_of_a_sibling_clone_is_recorded_there(self):
        out = self.prompt("aprobado para producción api-rate-limit")
        self.assertIn("[karvey] approval recorded (prod, api-rate-limit", out)
        self.assertIn(str(self.api), out)
        m = marker(self.api, "api-rate-limit")
        self.assertIsNotNone(m)
        self.assertEqual(m["kind"], "prod")
        self.assertEqual(m["repo"], approval.repo_id(self.api))
        self.assertTrue(recorded(self.api, "api-rate-limit"))
        self.assertIsNone(marker(self.web, "api-rate-limit"))
        self.assertIsNone(marker(self.web, "web-search"))

    def test_bug158_the_owner_accepts_it_with_approve_sha(self):
        self.prompt("aprobado para producción api-rate-limit")
        ok, _ = approval.check_marker(marker(self.api, "api-rate-limit"), self.api, scope="api-rate-limit",
                                      kinds=("prod",))
        self.assertTrue(ok)
        m, scope, _ = approval.find_valid(self.api, "api-rate-limit", kinds=("prod",), project_scope=False)
        self.assertEqual(scope, "api-rate-limit")

    def test_bug158_two_owning_clones_record_nothing_and_are_listed(self):
        copy = karvey_repo(self.dev / "app-api-copy", "api-rate-limit")
        out = self.prompt("aprobado para producción api-rate-limit")
        self.assertIn("prod approval NOT recorded", out)
        self.assertIn(str(self.api), out)
        self.assertIn(str(copy), out)
        self.assertIn("«aprobado para producción api-rate-limit»", out)
        self.assertIsNone(marker(self.api, "api-rate-limit"))
        self.assertIsNone(marker(copy, "api-rate-limit"))

    def test_bug158_unknown_word_never_suggests_the_active_change(self):
        out = self.prompt("aprobado para producción api-rate-limt")
        self.assertIn("prod approval NOT recorded", out)
        self.assertNotIn("web-search", out)
        self.assertIn("«aprobado para producción <change-id>»", out)
        self.assertIsNone(marker(self.web, "web-search"))

    def test_bug158_negated_phrase_naming_another_clone_never_suggests_the_active_change(self):
        out = self.prompt("no apruebo producción de api-rate-limit todavía")
        self.assertNotIn("web-search", out)
        self.assertIsNone(marker(self.api, "api-rate-limit"))

    def test_named_change_here_wins_over_a_clone_holding_the_same_id(self):
        karvey_repo(self.dev / "app-other", "web-search")
        out = self.prompt("aprobado para producción web-search")
        self.assertIn("[karvey] approval recorded (prod, web-search, expires", out)
        self.assertIsNotNone(marker(self.web, "web-search"))

    def test_no_change_named_keeps_the_single_active_change(self):
        out = self.prompt("aprobado para producción")
        self.assertIn("(prod, web-search — the only active change", out)

    def test_change_in_another_worktree_of_the_same_clone_is_recorded(self):
        wt = self.dev / "app-web-wt"
        g.run(["worktree", "add", "-q", "-b", "feature/web-export", str(wt)], self.web)
        g.write(wt, "docs/spec/changes/web-export/spec.json", {"change_id": "web-export", "phase": "deploying"})
        g.commit_all(wt, "web-export")
        out = self.prompt("aprobado para producción web-export")
        self.assertIn("[karvey] approval recorded (prod, web-export", out)
        self.assertIsNotNone(marker(self.web, "web-export"))  # one clone: the state dir is shared

    def test_two_changes_of_other_clones_named_record_nothing(self):
        karvey_repo(self.dev / "app-db", "db-index")
        out = self.prompt("aprobado para producción api-rate-limit y db-index")
        self.assertIn("prod approval NOT recorded", out)
        self.assertIn("one message per change", out)

    def test_outside_a_karvey_project_one_owner_records_there(self):
        out = self.prompt("aprobado para producción api-rate-limit", cwd=self.dev)
        self.assertIn("[karvey] approval recorded (prod, api-rate-limit", out)
        self.assertIsNotNone(marker(self.api, "api-rate-limit"))

    def test_outside_a_karvey_project_nothing_named_stays_silent(self):
        self.assertEqual(self.prompt("aprobado para producción", cwd=self.dev), "")
        self.assertEqual(self.prompt("aprobado, sigue", cwd=self.dev), "")

    def test_search_error_fails_open_with_the_line(self):
        with mock.patch.object(approval, "clones_holding", side_effect=OSError("boom"), create=True):
            out = self.prompt("aprobado para producción api-rate-limit")
        self.assertIn("prod approval NOT recorded", out)
        self.assertIsNone(marker(self.api, "api-rate-limit"))
        self.assertNotIn("web-search", out)

class D1OnBug158(Base):
    """QA D1 (H1): only a change-like word, or the word right after the production term, may route the approval to
    another clone, and only a change committed there counts."""

    def add(self, root, cid, commit=True):
        g.write(root, "docs/spec/changes/%s/spec.json" % cid, {"change_id": cid, "phase": "impl"})
        if commit:
            g.commit_all(root, cid)

    def test_d1_a_vocabulary_word_never_names_a_change_of_another_clone(self):
        self.add(self.api, "produccion")
        out = self.prompt("aprobado para producción")
        self.assertIn("(prod, web-search \u2014 the only active change", out)
        self.assertIsNone(marker(self.api, "produccion"))

    def test_d1_c_an_ordinary_word_never_names_a_change_of_another_clone(self):
        self.add(self.api, "search")
        out = self.prompt("approved for production, ship the search fix")
        self.assertIsNone(marker(self.api, "search"))
        self.assertNotIn("clone", out)

    def test_d1_e_outside_a_project_a_vocabulary_word_records_nothing(self):
        self.add(self.api, "para")
        self.assertEqual(self.prompt("aprobado para producción", cwd=self.dev), "")
        self.assertIsNone(marker(self.api, "para"))

    def test_d1_an_uncommitted_change_of_another_clone_does_not_count(self):
        self.add(self.api, "api-quota", commit=False)
        out = self.prompt("aprobado para producción api-quota")
        self.assertIn("prod approval NOT recorded", out)
        self.assertIsNone(marker(self.api, "api-quota"))

    def test_d1_a_hyphenless_id_right_after_the_production_word_is_named(self):
        self.add(self.api, "billing")
        out = self.prompt("aprobado para producción billing")
        self.assertIn("[karvey] approval recorded (prod, billing, clone %s" % self.api, out)
        self.assertIsNotNone(marker(self.api, "billing"))


    def test_d7_f1_common_words_never_route_to_another_clone(self):
        for cid, text in (("release", "ok aprobado para producción, sube el release"),
                          ("deploy", "aprobado deploy a producción")):
            self.add(self.api, cid)
            out = self.prompt(text)
            self.assertIn("(prod, web-search \u2014 the only active change", out, text)
            self.assertIsNone(marker(self.api, cid))

    def test_d7_f2_one_id_here_and_one_in_another_clone_records_nothing(self):
        out = self.prompt("aprobado para producción web-search y api-rate-limit")
        self.assertIn("prod approval NOT recorded", out)
        self.assertIn("one message per change", out)
        self.assertIsNone(marker(self.web, "web-search"))

    def test_d7_f3_negated_phrase_naming_a_hyphenless_id_elsewhere_never_suggests_the_active_change(self):
        self.add(self.api, "ratelimit")
        out = self.prompt("no apruebo producción ratelimit todavía")
        self.assertNotIn("web-search", out)
        self.assertIn("<change-id>", out)


if __name__ == "__main__":
    unittest.main()
