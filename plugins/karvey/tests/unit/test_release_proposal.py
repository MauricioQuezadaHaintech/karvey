"""D-50 (REQ-AN-016..024, BUG-162): production approval by a listed release proposal and a bare «apruebo».

The agent runs ``karvey-state.py propose-release`` (one pending proposal, the «Esta aprobación implica:» block); the
human's next own message with an approval word records a prod marker for every listed change, in the clone that
holds it, bound to its listed commit; the hook echoes exactly what it recorded. The agent can only propose."""
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
import _gitrepo as g
import _state
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


def head(root):
    rc, out = pj.git(["rev-parse", "HEAD"], root)
    return out


def marker(root, scope):
    m, status = approval.read_marker(root, scope)
    return m if status == "ok" else None


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dev = Path(self.tmp.name).resolve() / "work"
        self.web = karvey_repo(self.dev / "app-web", "web-search")
        self.api = karvey_repo(self.dev / "app-api", "api-rate-limit")
        env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(Path(self.tmp.name) / "state"),
                                           "CLAUDE_PROJECT_DIR": str(self.web)})
        env.start()
        self.addCleanup(env.stop)

    def prompt(self, text, cwd=None, transcript=""):
        cwd = cwd or self.web
        out, err = io.StringIO(), io.StringIO()
        payload = {"session_id": "s1", "transcript_path": transcript, "cwd": str(cwd),
                   "hook_event_name": "UserPromptSubmit", "prompt": text}
        code = kh.dispatch("prompt", json.dumps(payload), env=dict(os.environ, CLAUDE_PROJECT_DIR=str(cwd)),
                           out=out, err=err)
        self.assertEqual(code, 0)
        return out.getvalue()

    def propose(self, *argv, cwd=None):
        return _state.run_json("propose-release", *argv, cwd=cwd or self.web)

    def propose_both(self):
        code, env = self.propose("--change", "web-search", "--pr", "30", "--sha", "HEAD",
                                 "--change", "api-rate-limit", "--pr", "12", "--sha", head(self.api),
                                 "--effect", "merge a main; el pipeline despliega")
        self.assertEqual(code, 0, env)
        return env["result"]

    def proposal(self, cwd=None):
        p, status = approval.read_proposal(approval.session_anchor(pj.find_root(start=str(cwd or self.web)),
                                                                   str(cwd or self.web)))
        return p if status == "ok" else None


class Propose(Base):
    def test_one_pending_proposal_and_the_block(self):
        res = self.propose_both()
        block = res["block"]
        self.assertTrue(block.startswith("Esta aprobación implica:"), block)
        self.assertIn("1. web-search · %s · PR #30 · commit %s" % (self.web, head(self.web)[:7]), block)
        self.assertIn("2. api-rate-limit · %s · PR #12 · commit %s · merge a main; el pipeline despliega"
                      % (self.api, head(self.api)[:7]), block)
        self.assertIn(res["shown_id"], block)
        p = self.proposal()
        self.assertEqual(p["id"], approval.proposal_id(p))
        self.assertEqual([i["change"] for i in p["items"]], ["web-search", "api-rate-limit"])
        self.assertEqual(p["items"][0]["sha"], head(self.web))
        self.assertTrue(approval.proposal_pending(p))

    def test_the_human_output_prints_the_block(self):
        code, out, _ = _state.run("propose-release", "--change", "web-search", "--pr", "30", "--sha", "HEAD",
                                  cwd=self.web)
        self.assertEqual(code, 0)
        self.assertIn("Esta aprobación implica:\n  1. web-search", out)

    def test_refusals(self):
        for argv, code, needle in (
                (("--change", "nope-x", "--pr", "1", "--sha", "HEAD"), 3, "not in this project"),
                (("--change", "web-search", "--pr", "1", "--sha", "deadbeef"), 3, "not a commit"),
                (("--change", "web-search", "--sha", "HEAD"), 2, "--pr"),
                (("--pr", "1", "--change", "web-search"), 2, "invalid arguments"),
                (("--change", "web-search", "--pr", "x1", "--sha", "HEAD"), 2, "PR number")):
            c, env = self.propose(*argv)
            self.assertEqual(c, code, (argv, env))
            self.assertIn(needle, json.dumps(env, ensure_ascii=False), argv)
            self.assertIsNone(self.proposal(), argv)

    def test_repo_by_path_and_two_clones_holding_the_id(self):
        c, env = self.propose("--change", "api-rate-limit", "--repo", str(self.api), "--pr", "2", "--sha", "HEAD")
        self.assertEqual(c, 0, env)
        self.assertEqual(env["result"]["items"][0]["repo"], str(self.api))
        karvey_repo(self.dev / "app-api-copy", "api-rate-limit")
        c, env = self.propose("--change", "api-rate-limit", "--pr", "2", "--sha", "HEAD")
        self.assertEqual(c, 3)
        self.assertIn("held by 2 clones", env["errors"][0]["message"])


class HumanApproves(Base):
    def test_bare_apruebo_records_every_listed_change_bound_to_its_commit(self):
        res = self.propose_both()
        out = self.prompt("apruebo")
        self.assertIn("[karvey] production approval recorded: web-search@%s, api-rate-limit@%s (expires "
                      % (head(self.web)[:7], head(self.api)[:7]), out)
        self.assertIn(res["shown_id"], out)
        mw, ma = marker(self.web, "web-search"), marker(self.api, "api-rate-limit")
        self.assertEqual((mw["kind"], mw["sha"], mw["proposal"]), ("prod", head(self.web), res["proposal"]))
        self.assertEqual((ma["kind"], ma["sha"]), ("prod", head(self.api)))
        self.assertEqual(ma["repo"], approval.repo_id(self.api))
        self.assertIsNone(marker(self.web, "api-rate-limit"))
        self.assertEqual(self.proposal()["state"]["status"], "approved")
        self.assertEqual(self.proposal()["state"]["recorded"], ["web-search@%s" % head(self.web)[:7],
                                                                "api-rate-limit@%s" % head(self.api)[:7]])
        rec = [r for r in audit.read(pj.state_dir(self.api, create=False)) if r.get("event") == "marker"
               and r.get("decision") == "recorded" and r.get("change") == "api-rate-limit"]
        self.assertEqual(rec[-1]["sha"], head(self.api))

    def test_other_approval_words(self):
        for word in ("ok", "dale", "aprobado", "sí", "Apruebo."):
            self.propose_both()
            self.assertIn("[karvey] production approval recorded: web-search@", self.prompt(word), word)

    def test_a_second_approval_word_records_nothing_more(self):
        self.propose_both()
        self.prompt("apruebo")
        self.assertNotIn("production approval recorded", self.prompt("ok"))

    def test_not_an_approval_leaves_it_pending_and_silent(self):
        self.propose_both()
        for text in ("muéstrame el diff primero", "no apruebo todavía", "¿qué implica?", "ok pero antes revisa X"):
            self.assertEqual(self.prompt(text), "", text)
            self.assertTrue(approval.proposal_pending(self.proposal()), text)
        self.assertIsNone(marker(self.web, "web-search"))
        self.assertIsNone(marker(self.api, "api-rate-limit"))

    def test_stop_cancels_it(self):
        self.propose_both()
        out = self.prompt("detente")
        self.assertIn("[karvey] release proposal cancelled (stop)", out)
        self.assertEqual(self.proposal()["state"]["status"], "cancelled")
        out = self.prompt("apruebo")
        self.assertNotIn("production approval recorded", out)
        self.assertEqual(marker(self.web, "web-search")["kind"], "plan")
        self.assertIsNone(marker(self.api, "api-rate-limit"))

    def test_naming_production_and_a_change_still_works(self):
        self.propose_both()
        out = self.prompt("aprobado para producción web-search")
        self.assertIn("[karvey] approval recorded (prod, web-search", out)
        self.assertIsNone(marker(self.api, "api-rate-limit"))
        self.assertTrue(approval.proposal_pending(self.proposal()))

    def test_a_session_outside_a_project_approves_its_proposal(self):
        c, env = self.propose("--change", "api-rate-limit", "--pr", "4", "--sha", "HEAD", cwd=self.dev)
        self.assertEqual(c, 0, env)
        out = self.prompt("dale", cwd=self.dev)
        self.assertIn("[karvey] production approval recorded: api-rate-limit@%s" % head(self.api)[:7], out)
        self.assertEqual(marker(self.api, "api-rate-limit")["kind"], "prod")

    def test_another_worktree_does_not_approve_this_session_s_proposal(self):
        wt = self.dev / "app-web-wt"
        g.run(["worktree", "add", "-q", "-b", "wt", str(wt)], self.web)
        c, env = self.propose("--change", "web-search", "--pr", "30", "--sha", "HEAD", cwd=wt)
        self.assertEqual(c, 0, env)
        self.assertNotIn("production approval recorded", self.prompt("apruebo"))
        self.assertIn("production approval recorded", self.prompt("apruebo", cwd=wt))


class Security(Base):
    """D1 / D7: only the human's prompt records; integrity, freshness and display are checked."""

    def test_the_agent_cannot_approve_its_own_proposal(self):
        self.propose_both()
        c, env = _state.run_json("approve", "web-search", "prod", "--by", "M", "--role", "human", "--ref", "D-50",
                                 cwd=self.web)
        self.assertEqual(c, 3)
        self.assertIn("propose-release", env["errors"][0]["message"])
        self.assertIsNone(marker(self.web, "web-search"))

    def _write(self, now=None, items=None):
        anchor = approval.session_anchor(pj.find_root(start=str(self.web)), str(self.web))
        return anchor, approval.write_proposal(anchor, items or [
            {"change": "web-search", "repo": str(self.web), "pr": 30, "sha": head(self.web), "effect": "x"}],
            now=now)

    def test_a_proposal_created_after_the_message_is_refused(self):
        self._write(now=approval.now_dt() + approval.timedelta(minutes=2))
        out = self.prompt("apruebo")
        self.assertIn("NOT approved: the proposal was created after your message", out)
        self.assertNotEqual((marker(self.web, "web-search") or {}).get("kind"), "prod")

    def test_a_tampered_proposal_is_refused(self):
        anchor, p = self._write()
        p["items"][0]["sha"] = head(self.api)  # another commit, written after it was shown
        path = approval.proposal_path(anchor)
        path.write_text(json.dumps(p), encoding="utf-8")
        out = self.prompt("apruebo")
        self.assertIn("NOT approved: the proposal changed after it was shown (hash mismatch)", out)
        self.assertNotEqual((marker(self.web, "web-search") or {}).get("kind"), "prod")

    def test_a_stale_proposal_is_refused(self):
        self._write(now=approval.now_dt() - approval.timedelta(minutes=61))
        out = self.prompt("apruebo")
        self.assertIn("NOT approved: the proposal expired", out)
        self.assertNotEqual((marker(self.web, "web-search") or {}).get("kind"), "prod")

    def test_the_transcript_must_show_the_proposal(self):
        res = self.propose_both()
        tr = Path(self.tmp.name) / "t.jsonl"
        tr.write_text(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Listo, ¿apruebas?"}]}}) + "\n" + json.dumps(
            {"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "content": res["block"]}]}}) + "\n", encoding="utf-8")
        out = self.prompt("apruebo", transcript=str(tr))
        self.assertIn("NOT approved: the agent never showed this proposal to you", out)
        self.assertNotEqual((marker(self.web, "web-search") or {}).get("kind"), "prod")
        res = self.propose_both()
        tr.write_text(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": res["block"]}]}}) + "\n", encoding="utf-8")
        self.assertIn("production approval recorded", self.prompt("apruebo", transcript=str(tr)))

    def test_the_echo_lists_exactly_what_was_recorded(self):
        self.propose_both()
        g.run(["rm", "-q", "-r", "docs/spec/changes/api-rate-limit"], self.api)
        out = self.prompt("apruebo")
        self.assertIn("[karvey] production approval recorded: web-search@%s (expires" % head(self.web)[:7], out)
        self.assertNotIn("api-rate-limit@", out)
        self.assertIn("[karvey] production approval NOT recorded: api-rate-limit (", out)
        self.assertIsNone(marker(self.api, "api-rate-limit"))


class StateTool(Base):
    def test_approve_binds_the_listed_commit_and_check_prod_accepts_it(self):
        self.propose_both()
        self.prompt("apruebo")
        c, env = _state.run_json("approve", "web-search", "prod", "--by", "M", "--role", "human", "--ref", "D-50",
                                 cwd=self.web)
        self.assertEqual(c, 0, env)
        self.assertEqual(env["result"]["prod"]["head_sha"], head(self.web))
        self.assertEqual(env["result"]["prod"]["evidence"]["proposal_sha"], head(self.web))
        c, env = _state.run_json("check-prod", "web-search", "--sha", head(self.web), cwd=self.web)
        self.assertEqual(c, 0, env)
        c, env = _state.run_json("approve", "api-rate-limit", "prod", "--by", "M", "--role", "human", "--ref",
                                 "D-50", "--sha", head(self.api), cwd=self.api)
        self.assertEqual(c, 0, env)

    def test_another_commit_needs_a_new_proposal(self):
        self.propose_both()
        self.prompt("apruebo")
        listed = head(self.web)
        g.write(self.web, "x.txt", "new")
        g.commit_all(self.web)
        c, env = _state.run_json("approve", "web-search", "prod", "--by", "M", "--role", "human", "--ref", "D-50",
                                 "--sha", "HEAD", cwd=self.web)
        self.assertEqual(c, 3)
        self.assertIn("new proposal", env["errors"][0]["message"])
        self.assertIn(listed[:12], env["errors"][0]["message"])


class Bug162Silence(Base):
    """BUG-162: a message that only discusses approvals prints nothing (no "negation: no")."""

    def test_talk_about_approvals_is_silent(self):
        for text in ("el approve prod no funcionó ayer, revisa el log",
                     "no entiendo por qué el ok de producción no quedó registrado",
                     "ok pero el merge a main no se ve en el PR",
                     "the approval for production did not record, can you look at it, not now"):
            self.assertNotIn("NOT recorded", self.prompt(text), text)
            self.assertNotIn("negation", self.prompt(text), text)

    def test_an_approval_attempt_still_says_why(self):
        out = self.prompt("aprobado para producción, no hay más cambios")
        self.assertIn("prod approval NOT recorded: negation", out)
        self.assertIn("propose-release", out)
        self.assertIn("«apruebo»", out)


if __name__ == "__main__":
    unittest.main()
