"""hookio against the real payloads captured by E1.F1.T1, plus the alternatives of A-1..A-3."""
import json
import unittest

import _path
from karvey_lib import hookio

FIX = _path.FIXTURES_DIR / "payloads"
ENV = {"CLAUDE_PROJECT_DIR": "/proj/from-env", "PWD": "/proj/pwd"}


def fixture(name):
    return (FIX / name).read_text(encoding="utf-8")


def p(obj, env=ENV):
    return hookio.parse(json.dumps(obj), env=env, platform="posix")


class CapturedFixtures(unittest.TestCase):
    def test_every_fixture_parses(self):
        files = sorted(FIX.glob("*.json"))
        self.assertGreaterEqual(len(files), 6)
        for f in files:
            pl = hookio.parse(f.read_text(encoding="utf-8"), env=ENV, platform="posix")
            self.assertTrue(pl.ok, f.name)
            self.assertEqual(pl.session_id, "00000000-0000-0000-0000-000000000000", f.name)
            self.assertEqual(pl.cwd, "/SCRATCH/proj", f.name)
            self.assertTrue(pl.transcript_path.endswith(".jsonl"), f.name)
            self.assertIn(pl.event, ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse"), f.name)

    def test_pre_tool_use_bash(self):
        pl = hookio.parse(fixture("pre-tool-use-bash.json"), env=ENV, platform="posix")
        self.assertEqual((pl.event, pl.tool_name, pl.command, pl.file_path), ("PreToolUse", "Bash", "ls", None))
        self.assertEqual(pl.permission_mode, "default")

    def test_write_and_edit_file_path(self):
        for name in ("pre-tool-use-write.json", "pre-tool-use-edit.json", "post-tool-use-write.json",
                     "post-tool-use-edit.json"):
            pl = hookio.parse(fixture(name), env=ENV, platform="posix")
            self.assertEqual(pl.file_path, "/SCRATCH/proj/a.txt", name)
            self.assertIsNone(pl.command, name)

    def test_user_prompt_submit(self):
        pl = hookio.parse(fixture("user-prompt-submit.json"), env=ENV, platform="posix")
        self.assertEqual(pl.event, "UserPromptSubmit")
        self.assertTrue(pl.prompt.startswith("Do exactly these steps"))
        self.assertIsNone(pl.tool_name)

    def test_session_start_source(self):
        self.assertEqual(hookio.parse(fixture("session-start-startup.json"), env=ENV).source, "startup")
        self.assertEqual(hookio.parse(fixture("session-start-resume.json"), env=ENV).source, "resume")


class Alternatives(unittest.TestCase):
    def test_prompt_fallbacks_a2(self):
        self.assertEqual(p({"user_prompt": "ok"}).prompt, "ok")
        self.assertEqual(p({"prompt": "first", "user_prompt": "second"}).prompt, "first")
        self.assertEqual(p({"message": {"content": "dale"}}).prompt, "dale")
        self.assertEqual(p({"message": {"content": [{"type": "text", "text": "a"}, {"type": "image"},
                                                    {"type": "text", "text": "b"}]}}).prompt, "a\nb")
        self.assertIsNone(p({"message": {"content": [{"type": "tool_result", "content": "ok"}]}}).prompt)
        self.assertIsNone(p({}).prompt)

    def test_path_fallbacks_a3(self):
        self.assertEqual(p({"cwd": "/r", "tool_name": "NotebookEdit", "tool_input": {"notebook_path": "n.ipynb"}})
                         .file_path, "/r/n.ipynb")
        self.assertEqual(p({"cwd": "/r", "tool_name": "MultiEdit", "tool_input": {"file_path": "/abs/x.py",
                                                                                   "edits": []}}).file_path, "/abs/x.py")
        self.assertEqual(p({"cwd": "/r", "tool_input": {"file_path": "../y"}}).file_path, "/y")

    def test_cwd_fallbacks_a1(self):
        self.assertEqual(p({"tool_name": "Bash"}).cwd, "/proj/from-env")
        self.assertEqual(p({}, env={"PWD": "/proj/pwd"}).cwd, "/proj/pwd")
        self.assertEqual(p({"cwd": "  "}, env={"PWD": "/proj/pwd"}).cwd, "/proj/pwd")

    def test_missing_session_and_wrong_types(self):
        pl = p({"session_id": 5, "tool_input": "nope", "tool_name": ["x"]})
        self.assertTrue(pl.ok)
        self.assertEqual((pl.session_id, pl.tool_input, pl.tool_name, pl.command), ("", {}, None, None))


class NonJson(unittest.TestCase):
    def test_non_json_stdin(self):
        for text in ("", "   ", "not json", "{", "[1, 2]", "42", b"\xff\xfe"):
            pl = hookio.parse(text, env=ENV)
            self.assertFalse(pl.ok, text)
            self.assertTrue(pl.error, text)
            self.assertEqual(pl.cwd, "/proj/from-env")

    def test_bom_is_tolerated(self):
        self.assertTrue(hookio.parse("﻿" + json.dumps({"prompt": "ok"}), env=ENV).ok)


if __name__ == "__main__":
    unittest.main()
