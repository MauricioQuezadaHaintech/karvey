"""Skill-text rules an agent must be told, proved by reading the text it loads (BUG-24, BUG-25).

The manual agent-behaviour scripts (tests/manual/) found that an agent followed the skill text exactly
and still did the wrong thing, because the text said the wrong thing or nothing at all. Each class pins
the sentence the fix added, so a later edit cannot drop it silently.
"""
import re
import unittest

import _path

SKILLS = _path.PLUGIN_ROOT / "skills"
RULES = SKILLS / "karvey" / "rules"


def read(path):
    return path.read_text(encoding="utf-8")


def paragraph(text, start):
    """The paragraph that begins with ``start`` (up to the next blank line)."""
    i = text.index(start)
    j = text.find("\n\n", i)
    return text[i:] if j < 0 else text[i:j]


class VisibleVersionCheck(unittest.TestCase):
    """BUG-24 / F-51, REQ-W1-041: the DEV visible-version check accepts the bumped version with a DEV mark
    in any format and compares it with the version file of the deployed commit, not the tip of dev."""

    def setUp(self):
        self.deploy = read(SKILLS / "karvey-deploy" / "SKILL.md")
        self.canary = paragraph(self.deploy, "**2.6 — DEV canary")
        self.versioning = read(RULES / "versioning.md")
        self.vcheck = paragraph(self.versioning, "`karvey-deploy` must **recommend this")

    def test_deploy_reads_the_version_file_of_the_deployed_commit(self):
        self.assertRegex(self.canary, r"git show [^`\n]*deployed[^`\n]*:")

    def test_deploy_accepts_any_dev_mark_format(self):
        self.assertIn("any format", self.canary)

    def test_deploy_does_not_demand_the_dev_prerelease_form(self):
        self.assertNotRegex(self.canary, r"must show `-dev`")

    def test_deploy_never_compares_with_the_tip(self):
        self.assertRegex(self.canary, r"not (with |against )?the tip")

    def test_versioning_rule_says_the_same(self):
        self.assertIn("any format", self.vcheck)
        self.assertRegex(self.vcheck, r"deployed commit")
        self.assertNotRegex(self.vcheck, r"DEV shows `-dev` of the version just bumped")


class SubagentPromptsCarryTheProjectJsonBan(unittest.TestCase):
    """BUG-25 / F-52, REQ-W1-081: a subagent never writes project.json, so every subagent prompt an agent
    composes says so, even when the user asked for the settings to be persisted."""

    LINE = "Do not write `docs/spec/project.json`"

    def setUp(self):
        self.adapters = read(RULES / "management-adapters.md")
        self.rule5 = paragraph(self.adapters, "5. **Subagents never write `project.json`**")
        self.impl = read(SKILLS / "karvey-impl" / "SKILL.md")

    def test_rule_5_puts_the_ban_in_every_prompt(self):
        self.assertRegex(self.rule5, r"[Ee]very subagent prompt")
        self.assertIn(self.LINE, self.rule5)

    def test_a_user_request_to_persist_is_not_delegated(self):
        self.assertRegex(self.rule5, r"(?s)asked[^.]*persist[^.]*never (passed|delegated)")

    def test_impl_dispatch_carries_the_ban(self):
        dispatch = paragraph(self.impl, "If there are `(P)` tasks: dispatch")
        self.assertIn("rule 5", dispatch)
        self.assertIn(self.LINE, dispatch)


if __name__ == "__main__":
    unittest.main()
