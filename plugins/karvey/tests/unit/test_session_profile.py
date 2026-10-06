"""Session identity (REQ-HF-020..023, BUG-140): the profile comes from the working repo only."""
import io
import json
import os
import unittest

import _path  # noqa: F401
import _gitrepo as gr
from karvey_lib import karvey_hooks as kh
from karvey_lib import livestate

SENSITIVE = "---\nsensitive: true\n---\nSECRET-HANDOFF\n"


def team(root, roles, ops=""):
    gr.write(root, "docs/spec/team.json", {"code": "x", "ops_repo": ops, "roles": roles})
    for role in set(roles.values()) | {"ceo"}:
        gr.write(root, "docs/spec/agents/%s/manifest.md" % role, "%s-MANIFEST\n" % role.upper())
        gr.write(root, "docs/spec/agents/%s/handoff.md" % role, "%s-HANDOFF\n" % role.upper())


class SessionProfile(unittest.TestCase):
    def setUp(self):
        gr.isolate_git()
        self.tmp = gr.TempDir()
        self.t = self.tmp.path / "team"
        self.t.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def repo(self, name, **files):
        p = gr.init(self.t / name)
        for rel, content in files.items():
            gr.write(p, rel, content)
        return p

    def text(self, start, cwd=None, mode="resume"):
        return kh.session_text(mode, {"CLAUDE_PROJECT_DIR": str(start)}, cwd=str(cwd or start))

    # REQ-HF-020
    def test_bug140_ancestor_folder_profile_is_not_injected(self):
        gr.write(self.t, "docs/spec/agent/handoff.md", "OTHER-HANDOFF\n")
        web = self.repo("app-web")
        out = self.text(web)
        self.assertNotIn("OTHER-HANDOFF", out)
        self.assertIn("profile not loaded", out)
        self.assertIn("restore --profile", out)

    def test_bug140_unmapped_repo_gets_no_default_role(self):
        team(self.t, {"app-web": "web"})
        tools = self.repo("app-tools")
        out = self.text(tools)
        self.assertNotIn("CEO-HANDOFF", out)
        self.assertNotIn("CEO-MANIFEST", out)
        self.assertIn("profile not loaded", out)

    def test_bug140_team_folder_that_is_not_a_repo_gets_nothing(self):
        team(self.t, {"app-web": "web", "team": "ceo"})
        out = self.text(self.t)
        self.assertNotIn("CEO-HANDOFF", out)
        self.assertIn("profile not loaded", out)

    def test_mapped_repo_gets_its_own_profile(self):
        team(self.t, {"app-web": "web", "app-api": "api"})
        web = self.repo("app-web")
        (web / "src").mkdir()
        out = self.text(web / "src")
        self.assertIn("WEB-HANDOFF", out)
        self.assertNotIn("API-HANDOFF", out)
        self.assertNotIn("CEO-HANDOFF", out)

    def test_linked_worktree_maps_by_main_clone_name(self):
        team(self.t, {"app-web": "web"})
        web = self.repo("app-web")
        gr.commit_all(web)
        wt = self.t / "app-web-wt"
        gr.run(["worktree", "add", "-q", "-b", "wt", str(wt)], web)
        out = self.text(wt)
        self.assertIn("WEB-HANDOFF", out)

    def test_bug150_session_moved_into_a_worktree_of_the_same_repo(self):
        team(self.t, {"app-web": "web"})
        web = self.repo("app-web")
        gr.commit_all(web)
        wt = self.t / "app-web-wt"
        gr.run(["worktree", "add", "-q", "-b", "wt", str(wt)], web)
        out = self.text(web, cwd=wt)
        self.assertIn("WEB-HANDOFF", out)
        self.assertNotIn("profile not loaded", out)

    def test_plain_folder_without_any_profile_stays_silent(self):
        plain = self.tmp.path / "plain"
        plain.mkdir()
        self.assertEqual(self.text(plain), "")

    # REQ-HF-021
    def test_bug140_cwd_changed_to_another_repo_is_ambiguous(self):
        web = self.repo("app-web", **{"docs/spec/agent/handoff.md": "WEB-HANDOFF\n"})
        api = self.repo("app-api", **{"docs/spec/agent/handoff.md": "API-HANDOFF\n"})
        out = self.text(api, cwd=web)
        self.assertNotIn("WEB-HANDOFF", out)
        self.assertNotIn("API-HANDOFF", out)
        lines = [ln for ln in out.splitlines() if "profile not loaded" in ln]
        self.assertEqual(len(lines), 1, out)
        self.assertIn("app-web", lines[0])
        self.assertIn("app-api", lines[0])
        self.assertIn("/karvey-checkpoint restore --profile", lines[0])

    def test_bug140_two_candidates_inject_nothing(self):
        team(self.t, {"app-web": "web"})
        web = self.repo("app-web", **{"docs/spec/agent/handoff.md": "SOLO-HANDOFF\n"})
        out = self.text(web)
        self.assertNotIn("SOLO-HANDOFF", out)
        self.assertNotIn("WEB-HANDOFF", out)
        self.assertIn("profile not loaded", out)
        self.assertIn("candidates", out)

    def test_same_repo_on_resume_injects_as_before(self):
        web = self.repo("app-web", **{"docs/spec/agent/handoff.md": "WEB-HANDOFF\n"})
        (web / "src").mkdir()
        out = self.text(web, cwd=web / "src")
        self.assertIn("WEB-HANDOFF", out)

    # REQ-HF-018: an error injects no profile content
    def test_resolution_error_injects_no_profile_content(self):
        web = self.repo("app-web", **{"docs/spec/agent/handoff.md": "WEB-HANDOFF\n"})
        orig = livestate.resolve_session_profile

        def boom(*a, **k):
            raise RuntimeError("broken")
        livestate.resolve_session_profile = boom
        try:
            buf = io.StringIO()
            old = os.getcwd()
            os.chdir(str(web))
            try:
                kh.session_main("resume", env={"CLAUDE_PROJECT_DIR": str(web)}, out=buf)
            finally:
                os.chdir(old)
        finally:
            livestate.resolve_session_profile = orig
        text = json.loads(buf.getvalue())["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("WEB-HANDOFF", text)
        self.assertEqual(len(text.strip().splitlines()), 1)

    # REQ-HF-022
    def test_sensitive_front_matter(self):
        self.assertTrue(livestate.handoff_sensitive(SENSITIVE))
        self.assertTrue(livestate.handoff_sensitive("---\nsensitive: yes\n---\nx\n"))
        self.assertFalse(livestate.handoff_sensitive("---\nsensitive: false\n---\nx\n"))
        self.assertFalse(livestate.handoff_sensitive("no front matter\nsensitive: true\n"))

    def test_sensitive_handoff_shown_in_its_own_repo(self):
        team(self.t, {"app-ops": "ops"})
        gr.write(self.t, "docs/spec/agents/ops/handoff.md", SENSITIVE)
        ops = self.repo("app-ops")
        self.assertIn("SECRET-HANDOFF", self.text(ops))

    def test_bug140_sensitive_handoff_withheld_on_explicit_restore_elsewhere(self):
        team(self.t, {"app-ops": "ops", "app-web": "web"})
        gr.write(self.t, "docs/spec/agents/ops/handoff.md", SENSITIVE)
        self.repo("app-ops")
        web = self.repo("app-web")
        buf = io.StringIO()
        rc = kh.restore_profile("ops", cwd=str(web), out=buf)
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("OPS-MANIFEST", out)
        self.assertNotIn("SECRET-HANDOFF", out)
        self.assertIn("sensitive handoff withheld", out)
        self.assertIn("app-ops", out)

    # REQ-HF-023
    def test_restore_profile_by_role(self):
        team(self.t, {"app-web": "web", "app-api": "api"})
        web = self.repo("app-web")
        buf = io.StringIO()
        self.assertEqual(kh.restore_profile("web", cwd=str(web), out=buf), 0)
        out = buf.getvalue()
        self.assertIn("WEB-HANDOFF", out)
        self.assertIn("restored profile", out)

    def test_restore_profile_by_path(self):
        web = self.repo("app-web", **{"docs/spec/agent/handoff.md": "WEB-HANDOFF\n"})
        buf = io.StringIO()
        self.assertEqual(kh.restore_profile(str(web / "docs/spec/agent"), cwd=str(web), out=buf), 0)
        self.assertIn("WEB-HANDOFF", buf.getvalue())

    def test_restore_unknown_profile_lists_the_ones_found(self):
        team(self.t, {"app-web": "web", "app-api": "api"})
        web = self.repo("app-web")
        buf = io.StringIO()
        self.assertEqual(kh.restore_profile("mobile", cwd=str(web), out=buf), 1)
        out = buf.getvalue()
        self.assertIn("api", out)
        self.assertIn("web", out)
        self.assertNotIn("HANDOFF", out)


if __name__ == "__main__":
    unittest.main()
