"""BUG-164 / BUG-165 (D-54): one approval, no clock, no re-asking.

The incident: an agent showed a release proposal; the human answered «Si» 80 minutes later, «Te dije si», then
«apruebo» 89 minutes after the next one. Every answer was refused (the proposal "expired" after 60 min, «te dije si»
was not an approval) and the agent regenerated the block and asked again, four times. Meanwhile ``find -iname
"*approval*"`` under the plugin was blocked as if it wrote a protected path.

D-54: the human's approved plan is the production approval; nothing approved expires by time; a proposal stays
approvable until it is approved, cancelled or replaced; reading is never blocked."""
import io
import json
import os
import unittest

import _path  # noqa: F401
import _state
from karvey_lib import approval, karvey_hooks as kh
from test_release_proposal import Base, head, marker


class NoClock(Base):
    def test_the_dialogue_records_on_the_first_answer_even_80_minutes_later(self):
        self.propose_both()
        p = self.proposal()
        created = approval.now_dt() - approval.timedelta(minutes=80)
        p["created_at"] = approval.iso(created)
        p["expires_at"] = approval.iso(created + approval.timedelta(minutes=60))  # a pre-3.13.3 deadline: ignored
        p.pop("id")
        p["id"] = approval.proposal_id(p)
        approval._write_private(approval.proposal_path(p["session_tree"]), p)
        out = self.prompt("Si")
        self.assertIn("[karvey] production approval recorded: web-search@%s" % head(self.web)[:7], out)
        self.assertNotIn("expired", out)
        self.assertEqual(marker(self.web, "web-search")["kind"], "prod")

    def test_te_dije_si_is_an_approval(self):
        self.propose_both()
        out = self.prompt("Te dije si")
        self.assertIn("[karvey] production approval recorded", out)

    def test_the_block_names_no_deadline(self):
        res = self.propose_both()
        self.assertNotIn("vence", res["block"])
        self.assertIsNone(res["expires_at"])

    def test_an_unshown_proposal_stays_pending_and_the_hook_never_says_ask_again(self):
        self.propose_both()
        transcript = os.path.join(self.tmp.name, "t.jsonl")
        with open(transcript, "w") as fh:
            fh.write(json.dumps({"type": "assistant", "timestamp": approval.iso(approval.now_dt()),
                                 "message": {"content": [{"type": "text", "text": "nada que ver"}]}}) + "\n")
        out = self.prompt("apruebo", transcript=transcript)
        self.assertIn("NOT approved", out)
        self.assertNotIn("propose-release again", out)
        self.assertTrue(approval.proposal_pending(self.proposal()))


class PlanIsTheApproval(Base):
    def test_an_approved_plan_records_production_without_a_second_question(self):
        out = self.prompt("apruebo")  # the plan, presented by the agent with the release in it
        self.assertIn("approval recorded (plan", out)
        c, env = _state.run_json("approve", "web-search", "prod", "--by", "Owner", "--role", "human", "--ref",
                                 "D-54", "--sha", "HEAD", cwd=self.web)
        self.assertEqual(c, 0, env)
        c, env = _state.run_json("check-prod", "web-search", "--sha", head(self.web), cwd=self.web)
        self.assertEqual(c, 0, env)


class ReadingIsFree(Base):
    def pre_bash(self, command):
        out, err = io.StringIO(), io.StringIO()
        payload = {"session_id": "s1", "cwd": str(self.web), "hook_event_name": "PreToolUse", "tool_name": "Bash",
                   "tool_input": {"command": command}}
        code = kh.dispatch("pre-bash", json.dumps(payload), env=dict(os.environ, CLAUDE_PROJECT_DIR=str(self.web)),
                           out=out, err=err)
        return code, err.getvalue()

    def test_find_by_name_is_not_blocked(self):
        code, err = self.pre_bash('find %s/.git -iname "*approval*"' % self.web)
        self.assertNotIn("BLOCK protect-paths", err)

    def test_find_that_deletes_is_still_blocked(self):
        code, err = self.pre_bash("find %s/.git/karvey -name '*.json' -delete" % self.web)
        self.assertIn("BLOCK protect-paths", err)


if __name__ == "__main__":
    unittest.main()
