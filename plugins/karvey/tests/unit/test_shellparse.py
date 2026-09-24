"""shellparse (architecture §3.4; REQ-W1-014, REQ-W1-020)."""
import unittest

import _path  # noqa: F401
from karvey_lib import shellparse as sp

H = "/home/u"


def P(cmd, cwd="/w"):
    return sp.parse(cmd, cwd=cwd, home=H)


def argv0s(cmd, cwd="/w"):
    return [s.argv0 for s in P(cmd, cwd).segments]


def seg(cmd, name, cwd="/w"):
    return next(s for s in P(cmd, cwd).segments if s.argv0 == name)


class Separators(unittest.TestCase):
    def test_all_separators(self):
        r = P("a; b && c || d | e & f\ng |& h")
        self.assertEqual([s.argv0 for s in r.segments], list("abcdefgh"))
        self.assertEqual([s.op for s in r.segments], ["", ";", "&&", "||", "|", "&", "\n", "|&"])
        self.assertFalse(r.unparsed)

    def test_quoted_separators_are_one_segment(self):
        r = P(r"""echo "a; b && c" 'x | y' z\;w""")
        self.assertEqual(len(r.segments), 1)
        self.assertEqual(r.segments[0].argv, ["echo", "a; b && c", "x | y", "z;w"])

    def test_comment_and_subshell(self):
        self.assertEqual(argv0s("ls # ; rm -rf /"), ["ls"])
        self.assertEqual(argv0s("(cd x && git push) && ls"), ["cd", "git", "ls"])

    def test_keywords_skipped(self):
        self.assertEqual(argv0s("if true; then git push; fi"), ["true", "git"])
        self.assertEqual(argv0s("for f in a b; do rm -r $f; done"), ["for", "rm"])
        self.assertEqual(argv0s("! git diff --quiet"), ["git"])

    def test_empty(self):
        self.assertEqual(P("").segments, [])
        self.assertEqual(P("   ").segments, [])


class Wrappers(unittest.TestCase):
    def test_env_prefixes(self):
        s = seg('FOO=1 BAR="x y" git push', "git")
        self.assertEqual(s.assignments, {"FOO": "1", "BAR": "x y"})
        self.assertEqual(s.argv, ["git", "push"])

    def test_wrappers(self):
        for cmd in ("command git push", "builtin git push", "exec git push", "time git push", "time -p git push",
                    "nohup git push", "env git push", "env -i A=1 -u B git push", "sudo git push",
                    "sudo -u root -E git push", "sudo -- git push", "nice -n 5 git push", "timeout 5 git push",
                    "timeout -s KILL 5s git push", "command -p env sudo nohup git push"):
            r = P(cmd)
            self.assertEqual(r.segments[0].argv, ["git", "push"], cmd)

    def test_command_v_is_a_lookup(self):
        self.assertEqual(P("command -v git").segments[0].argv0, "command")

    def test_normalised_names(self):
        self.assertEqual(P("/usr/bin/gh pr merge 1").segments[0].argv0, "gh")
        self.assertEqual(P("\\git status").segments[0].argv0, "git")
        self.assertEqual(P("./bin/tool x").segments[0].argv0, "tool")

    def test_env_chdir(self):
        self.assertEqual(seg("env -C /r git commit -m x", "git").git["dir"], "/r")


class Recursion(unittest.TestCase):
    def test_bash_c(self):
        s = seg("bash -c 'git commit -m x'", "git")
        self.assertEqual((s.depth, s.source, s.argv), (1, "shell-c", ["git", "commit", "-m", "x"]))
        self.assertEqual(seg('sh -lc "cd /tmp && git push"', "git").cwd, "/tmp")
        self.assertEqual(seg("zsh -e -c 'git push'", "git").depth, 1)
        self.assertEqual(argv0s("bash script.sh -c x"), ["bash"])

    def test_eval(self):
        s = seg('eval "git push origin main"', "git")
        self.assertEqual((s.source, s.argv), ("eval", ["git", "push", "origin", "main"]))

    def test_substitutions(self):
        s = seg("echo $(git push)", "git")
        self.assertEqual((s.source, s.depth), ("subst", 1))
        self.assertEqual(seg("echo `git push`", "git").source, "subst")
        self.assertEqual(seg('echo "result: $(gh pr merge 1)"', "gh").argv, ["gh", "pr", "merge", "1"])
        self.assertEqual(argv0s("echo '$(git push)'"), ["echo"])  # single quotes: data
        self.assertEqual(argv0s("echo $((1 + 2))"), ["echo"])  # arithmetic, not a command

    def test_depth_3_and_beyond(self):
        d3 = "bash -c \"bash -c 'bash -c \\\"git push\\\"'\""
        s = seg(d3, "git")
        self.assertEqual(s.depth, 3)
        self.assertFalse(P(d3).unparsed)
        d4 = "echo $(echo $(echo $(echo $(git push))))"
        r = P(d4)
        self.assertTrue(r.unparsed)
        self.assertIn("deeper", r.reasons[0])


class Cd(unittest.TestCase):
    def test_cd_chain(self):
        self.assertEqual(seg("cd sub && git commit -m x", "git").cwd, "/w/sub")
        self.assertEqual(seg("cd /abs; cd ../x; git status", "git").cwd, "/x")
        self.assertEqual(seg("cd; git status", "git").cwd, H)
        self.assertEqual(seg("cd ~/r && git status", "git").cwd, H + "/r")
        self.assertEqual(seg('cd "$HOME/r" && git status', "git").cwd, H + "/r")
        self.assertEqual(seg("pushd r >/dev/null && git status", "git").cwd, "/w/r")

    def test_unresolved(self):
        self.assertIsNone(seg("cd $REPO && git commit", "git").cwd)
        self.assertIsNone(seg("cd - && git commit", "git").cwd)
        self.assertTrue(seg("cd $REPO && git commit", "git").git["unresolved"])

    def test_pipe_does_not_change_dir(self):
        self.assertEqual(seg("cd a | git status", "git").cwd, "/w")

    def test_relative_to_payload_cwd(self):
        self.assertEqual(seg("cd ../other && git push", "git", cwd="/repos/me").cwd, "/repos/other")


class GitOptions(unittest.TestCase):
    def test_c_config_no_pager(self):
        g = seg("git -C repo -c user.name=x --no-pager commit -m m", "git").git
        self.assertEqual((g["dir"], g["config"], g["no_pager"], g["sub"], g["args"]),
                         ("/w/repo", ["user.name=x"], True, "commit", ["-m", "m"]))

    def test_cumulative_c(self):
        self.assertEqual(seg("git -C a -C b status", "git").git["dir"], "/w/a/b")
        self.assertEqual(seg("git -C /abs -C ../b status", "git").git["dir"], "/b")

    def test_git_dir_work_tree(self):
        g = seg("git --git-dir=/r/.git --work-tree /r push", "git").git
        self.assertEqual((g["git_dir"], g["work_tree"], g["sub"]), ("/r/.git", "/r", "push"))
        g = seg("GIT_DIR=/r/.git git commit", "git").git
        self.assertEqual((g["git_dir"], g["sub"]), ("/r/.git", "commit"))

    def test_unresolved_c(self):
        g = seg('git -C "$X" commit', "git").git
        self.assertTrue(g["unresolved"])
        self.assertIsNone(g["dir"])

    def test_version_has_no_subcommand(self):
        self.assertIsNone(seg("git --version", "git").git["sub"])


class Redirections(unittest.TestCase):
    def redirs(self, cmd):
        return [r.as_tuple() for r in P(cmd).segments[0].redirects]

    def test_fd_and_null(self):
        self.assertEqual(self.redirs("ls 2>/dev/null"), [(">", "2", "/dev/null")])
        self.assertEqual(self.redirs("ls 2> /dev/null"), [(">", "2", "/dev/null")])
        self.assertEqual(self.redirs("cmd 2>&1"), [(">&", "2", "1")])
        self.assertEqual(self.redirs("echo x >&2"), [(">&", None, "2")])
        self.assertEqual(self.redirs("cmd &>/dev/null"), [("&>", None, "/dev/null")])
        self.assertEqual(P("ls 2>/dev/null").segments[0].argv, ["ls"])

    def test_writes(self):
        self.assertEqual(self.redirs("echo x > notes.txt"), [(">", None, "notes.txt")])
        self.assertEqual(self.redirs("echo x >> log"), [(">>", None, "log")])
        self.assertEqual(self.redirs("echo x >| f"), [(">|", None, "f")])
        self.assertEqual(self.redirs('echo "a > b"'), [])  # quoted: not a redirection

    def test_heredoc_body_is_data(self):
        r = P("git commit -F - <<'EOF'\nline; rm -rf /\n$(git push)\nEOF\ngit push origin x")
        self.assertEqual([s.argv0 for s in r.segments], ["git", "git"])
        self.assertEqual(r.segments[0].redirects[0].body, "line; rm -rf /\n$(git push)")
        self.assertEqual(r.segments[1].argv, ["git", "push", "origin", "x"])
        r = P("cat > f <<-END\n\tx\n\tEND\nls")
        self.assertEqual([s.argv0 for s in r.segments], ["cat", "ls"])
        self.assertEqual(r.segments[0].redirects[0].as_tuple(), (">", None, "f"))


class Unparsed(unittest.TestCase):
    def test_unbalanced(self):
        for cmd in ('echo "abc', "echo 'x", "echo $(ls", "echo `ls", "echo ${X"):
            r = P(cmd)
            self.assertTrue(r.unparsed, cmd)
            self.assertTrue(r.reasons, cmd)
            self.assertEqual(r.raw, cmd)

    def test_never_raises_on_odd_input(self):
        for cmd in (None, 5, ")(", "&&", "|||", ">", "<<", "\\", "a\\\nb"):
            sp.parse(cmd, cwd="/w")


if __name__ == "__main__":
    unittest.main()
