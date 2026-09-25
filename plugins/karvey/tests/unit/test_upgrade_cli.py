"""commit (library level) and the karvey-upgrade.py CLI (REQ-UP-013, 018, 028)."""
import json
import os
import shutil
import subprocess
import sys
import unittest

import _gitrepo as g
import _path
from karvey_lib import upgrade
from test_upgrade_apply import INSTALLED, REG, appender

TOOL = str(_path.SCRIPTS_DIR / "karvey-upgrade.py")


class CommitLibrary(unittest.TestCase):
    UB = "chore/karvey-upgrade-" + INSTALLED

    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = g.init(self.t.path / "proj")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"}})
        g.write(self.root, "notes.txt", "hello\n")
        g.commit_all(self.root)
        self.steps = [appender("a", "A"), appender("b", "B", file="b.txt")]
        upgrade.write_seen(self.root, "3.12.0", "accepted")
        rep = upgrade.apply(self.root, ["a", "b"], steps=self.steps, registry=REG, installed=INSTALLED, dry_run=True)
        rep = upgrade.apply(self.root, ["a", "b"], steps=self.steps, registry=REG, installed=INSTALLED,
                            preview=rep.preview)
        self.assertEqual(rep.applied, ["a", "b"])

    def tearDown(self):
        self.t.cleanup()

    def git(self, *args):
        return subprocess.run(["git"] + list(args), cwd=str(self.root), capture_output=True, text=True).stdout

    def test_message_and_pr_text(self):
        res = upgrade.commit(self.root, "The Owner", picked_at="2026-09-25T10:00:00-03:00",
                             answer="yes,\tgo ahead\n" + "x" * 300, trailers=["Co-Authored-By=An Agent <a.invalid>"],
                             installed=INSTALLED)
        msg = self.git("log", "-1", "--format=%B")
        self.assertTrue(msg.startswith("chore(karvey): project upgrade 3.12.0 → %s\n\n" % INSTALLED))
        self.assertIn("Steps: a, b\n", msg)
        self.assertIn("Picked-by: The Owner\n", msg)
        self.assertIn("Picked-at: 2026-09-25T10:00:00-03:00\n", msg)
        answer = [line for line in msg.splitlines() if line.startswith("Answer: ")][0]
        self.assertNotIn("\t", answer)
        self.assertLessEqual(len(answer), len('Answer: ""') + upgrade.ANSWER_MAX)
        self.assertIn("\nCo-Authored-By: An Agent <a.invalid>", msg)
        self.assertEqual(res["pr_title"], "chore(karvey): project upgrade 3.12.0 → %s" % INSTALLED)
        self.assertIn("Steps applied: a, b", res["pr_body"])
        self.assertIn("never merges", res["pr_body"])
        self.assertEqual(res["branch"], self.UB)
        self.assertEqual(res["sha"], self.git("rev-parse", "HEAD").strip())

    def test_stages_exactly_the_journal_files(self):
        g.write(self.root, "stray.txt", "not mine\n")
        g.write(self.root, "docs/spec/project.json", {"branch_flow": {"integration": "main", "production": "main"},
                                                      "x": 1})
        upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        files = sorted(self.git("show", "--name-only", "--format=", "HEAD").split())
        self.assertEqual(files, ["b.txt", "notes.txt"])
        status = self.git("status", "--porcelain")
        self.assertIn("stray.txt", status)
        self.assertIn("docs/spec/project.json", status)

    def test_refused_on_integration_or_production(self):
        g.run(["checkout", "-q", "main"], self.root)
        with self.assertRaises(upgrade.Refused) as cm:
            upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        self.assertIn("commit refused on main", str(cm.exception))

    def test_refused_on_a_branch_the_journal_does_not_name(self):
        g.run(["checkout", "-q", "-b", "other"], self.root)
        with self.assertRaises(upgrade.Refused) as cm:
            upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        self.assertIn("the journal belongs to " + self.UB, str(cm.exception))

    def test_picked_by_required_and_trailers_checked(self):
        with self.assertRaises(upgrade.Refused):
            upgrade.commit(self.root, "  \n", installed=INSTALLED)
        with self.assertRaises(upgrade.Refused):
            upgrade.commit(self.root, "The Owner", trailers=["no equals sign"], installed=INSTALLED)

    def test_nothing_left_to_commit(self):
        upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        with self.assertRaises(upgrade.Refused) as cm:
            upgrade.commit(self.root, "The Owner", installed=INSTALLED)
        self.assertIn("nothing to commit", str(cm.exception))


def run_tool(*args, cwd=None, home=None):
    env = dict(os.environ, **g.ISOLATED_ENV)
    if home:
        env["HOME"] = str(home)
    cp = subprocess.run([sys.executable, TOOL] + list(args), cwd=str(cwd) if cwd else None, env=env,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    return cp.returncode, cp.stdout.decode("utf-8"), cp.stderr.decode("utf-8")


class Cli(unittest.TestCase):
    """The tool as a subprocess on a git copy of the legacy fixture (the fixture home as HOME)."""

    def setUp(self):
        g.isolate_git()
        self.t = g.TempDir()
        self.root = self.t.path / "proj"
        shutil.copytree(str(_path.FIXTURES_DIR / "upgrade" / "legacy-project"), str(self.root))
        g.init(self.root, branch="dev")
        g.commit_all(self.root, "fixture")
        self.home = self.t.path / "home"
        shutil.copytree(str(_path.FIXTURES_DIR / "upgrade" / "fake-home"), str(self.home))

    def tearDown(self):
        self.t.cleanup()

    def tool(self, *args):
        return run_tool(*(list(args) + ["--root", str(self.root)]), home=self.home)

    def tool_json(self, *args):
        code, out, err = self.tool(*(list(args) + ["--json"]))
        env = json.loads(out)
        self.assertEqual(env["exit"], code, err)
        self.assertEqual(set(env), {"tool", "version", "ok", "exit", "result", "errors", "warnings"})
        return code, env

    def test_plan_json_rows_equal_the_table_rows(self):
        code, env = self.tool_json("plan")
        self.assertIn(code, (0, 1))
        res = env["result"]
        self.assertEqual(set(res), {"from", "to", "computed_on", "steps"})
        self.assertEqual(res["computed_on"], "dev")
        _, text, _ = self.tool("plan")
        table = [line.split("|")[1].strip() for line in text.splitlines()
                 if line.startswith("| ") and not line.startswith("| step")]
        self.assertEqual(table, [r["id"] for r in res["steps"] if r["status"] != "nothing"])
        for r in res["steps"]:
            self.assertEqual(set(r), {"id", "since", "title", "status", "summary", "dry_run", "risk", "human",
                                      "report_only", "inputs_needed", "warnings"})

    def test_full_cycle_through_the_cli(self):
        code, env = self.tool_json("apply", "--steps", "schema-migrate,enforcement-defaults", "--dry-run")
        self.assertEqual(code, 0, env)
        pid = env["result"]["preview"]
        self.assertRegex(pid, r"^[0-9a-f]{64}$")
        code, env = self.tool_json("apply", "--steps", "schema-migrate,enforcement-defaults", "--preview", pid)
        self.assertEqual(code, 0, env)
        self.assertEqual(env["result"]["applied"], ["schema-migrate", "enforcement-defaults"])
        self.assertEqual(env["result"]["branch"], "chore/karvey-upgrade-" + upgrade.INSTALLED)
        code, env = self.tool_json("commit", "--picked-by", "The Owner", "--answer", "yes",
                                   "--trailer", "Co-Authored-By=An Agent <a.invalid>")
        self.assertEqual(code, 0, env)
        self.assertTrue(env["result"]["pr_title"].startswith("chore(karvey): project upgrade "))
        self.assertIn("Steps applied: schema-migrate, enforcement-defaults", env["result"]["pr_body"])
        self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=str(self.root), capture_output=True,
                                        text=True).stdout, "")

    def test_values_file_is_validated_per_key(self):
        vals = self.t.path / "values.json"
        vals.write_text(json.dumps({"team-settings": {"notifications.channel": "slack",
                                                      "notifications.target": "a; rm -rf ~"}}), encoding="utf-8")
        code, env = self.tool_json("apply", "--steps", "team-settings", "--dry-run", "--values", str(vals))
        self.assertEqual(code, 3)
        self.assertIn("value refused", env["errors"][0]["message"])
        vals.write_text(json.dumps({"team-settings": {"notifications.target": {"x": 1}}}), encoding="utf-8")
        code, _ = self.tool_json("apply", "--steps", "team-settings", "--dry-run", "--values", str(vals))
        self.assertEqual(code, 2)
        code, _ = self.tool_json("apply", "--steps", "team-settings", "--dry-run", "--values",
                                 str(self.t.path / "absent.json"))
        self.assertEqual(code, 4)
        vals.write_text(json.dumps({"team-settings": {"notifications.channel": "slack",
                                                      "notifications.target": "#team-dev"}}), encoding="utf-8")
        code, env = self.tool_json("apply", "--steps", "team-settings", "--dry-run", "--values", str(vals))
        self.assertEqual(code, 0, env)
        self.assertIn("#team-dev", env["result"]["diffs"]["team-settings"])

    def test_unknown_step_and_usage(self):
        self.assertEqual(self.tool_json("apply", "--steps", "nope", "--dry-run")[0], 3)
        self.assertEqual(self.tool("apply")[0], 2)
        self.assertEqual(self.tool("bogus")[0], 2)

    def test_not_a_karvey_project_refuses(self):
        plain = g.init(self.t.path / "plain")
        for args in (["plan"], ["seen", "--decline"], ["apply", "--steps", "schema-migrate", "--dry-run"]):
            with self.subTest(args=args):
                code, out, _ = run_tool(*(args + ["--json"]), cwd=plain, home=self.home)
                self.assertEqual(code, 3)
                self.assertIn("not a Karvey project", json.loads(out)["errors"][0]["message"])
        self.assertFalse((plain / ".git" / "karvey").exists())

    def test_every_subprocess_is_an_argv_list(self):
        src = _path.Path(TOOL).read_text(encoding="utf-8") + (_path.SCRIPTS_DIR / "karvey_lib" / "upgrade.py").read_text(
            encoding="utf-8")
        self.assertNotIn("shell=True", src)
        self.assertNotIn("os.system", src)


if __name__ == "__main__":
    unittest.main()
