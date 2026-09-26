"""The organisation portfolio (architecture §1.20, C-20).

@req REQ-W3-045 REQ-W3-046 REQ-W3-047 REQ-W3-048 REQ-W3-078 REQ-W3-079
"""
import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path

import _path
from karvey_lib import portfolio as pf


def karvey_repo(path, layout="docs/spec", changes=()):
    path.mkdir(parents=True, exist_ok=True)
    (path / layout / "changes").mkdir(parents=True, exist_ok=True)
    (path / layout / "project.json").write_text("{}\n", encoding="utf-8")
    for cid, spec in changes:
        d = path / layout / "changes" / cid
        d.mkdir(parents=True, exist_ok=True)
        (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    return path


class Reader(unittest.TestCase):
    """@req REQ-W3-045 REQ-W3-047"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-portfolio-"))

    def tearDown(self):
        for dirpath, dirnames, _ in os.walk(str(self.tmp)):
            for d in dirnames:
                try:
                    os.chmod(os.path.join(dirpath, d), 0o755)
                except OSError:
                    pass
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def portfolio(self, repos):
        f = self.tmp / "ops/docs/spec/portfolio.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"repos": repos}), encoding="utf-8")
        return f

    def test_REQ_W3_045_five_entries_validated(self):
        repos = []
        for i in range(5):
            karvey_repo(self.tmp / ("repo-%d" % i))
            repos.append({"path": "../../../repo-%d" % i, "client": "sample-client-a", "owner": "team"})
        entries, problems = pf.load(self.portfolio(repos))
        self.assertEqual(problems, [])
        self.assertEqual([e["state"] for e in entries], ["ok"] * 5)
        self.assertTrue(all(os.path.isabs(e["abs"]) for e in entries))

    def test_REQ_W3_045_shell_metacharacters_are_refused_and_named_before_any_read(self):
        entries, _ = pf.load(self.portfolio([{"path": "repo;rm -rf x", "client": "a"},
                                             {"path": "$(touch pwned)", "client": "a"}]))
        self.assertTrue(entries[0]["state"].startswith("not read: invalid path (shell metacharacter ;"))
        self.assertTrue(entries[1]["state"].startswith("not read: invalid path (shell metacharacter"))
        self.assertFalse((self.tmp / "ops/docs/spec/pwned").exists())

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root reads everything")
    def test_REQ_W3_047_permission_denied(self):
        r = karvey_repo(self.tmp / "locked")
        os.chmod(str(r), 0)
        entries, _ = pf.load(self.portfolio([{"path": str(r), "client": "a"}]))
        self.assertEqual(entries[0]["state"], "not read: permission denied")

    def test_REQ_W3_047_clone_without_a_local_path(self):
        entries, _ = pf.load(self.portfolio([{"path": "../../../absent", "clone": "https://example.org/r.git",
                                              "client": "a"}]))
        self.assertEqual(entries[0]["state"], "not read: no local clone")

    def test_a_file_over_2_mb_is_not_read(self):
        big = self.tmp / "big.json"
        big.write_bytes(b" " * (3 * 1024 * 1024))
        with self.assertRaises(pf.NotRead) as cm:
            pf.read_text(big)
        self.assertEqual(str(cm.exception), "file too large")

    def test_an_escape_sequence_in_foreign_text_is_stripped(self):
        self.assertEqual(pf.sanitise("Late \x1b[31mimport\x1b[0m\x1b]0;title\x07 risk\x00"), "Late import risk")
        self.assertEqual(len(pf.sanitise("x" * 500)), pf.TEXT_MAX)

    def test_a_non_karvey_repository_and_the_spec_layout(self):
        (self.tmp / "plain").mkdir()
        with self.assertRaises(pf.NotRead) as cm:
            pf.repo_changes(self.tmp / "plain")
        self.assertEqual(str(cm.exception), "not a Karvey project")
        r = karvey_repo(self.tmp / "alt", layout="spec", changes=[("feat-a", {"change_id": "feat-a", "phase": "impl"})])
        layout, note, changes = pf.repo_changes(r)
        self.assertEqual((layout, note, [c["id"] for c in changes]), ("spec/", None, ["feat-a"]))


FIX = _path.UNIT_DIR / "fixtures" / "portfolio"
PERIOD = ["--from", "2026-10-01", "--to", "2026-10-14", "--as-of", "2026-10-14"]


def context():
    import importlib.util
    spec = importlib.util.spec_from_file_location("karvey_context_pf", str(_path.SCRIPTS_DIR / "karvey-context.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CTX = context()


def run_view(*argv):
    import contextlib
    import io
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = CTX.main(["--portfolio", "--file", str(FIX / "portfolio.json")] + PERIOD + list(argv))
    return code, out.getvalue()


class View(unittest.TestCase):
    """@req REQ-W3-046 REQ-W3-048"""

    def test_REQ_W3_046_grouped_by_client_with_the_four_column_groups(self):
        code, out = run_view("--json")
        self.assertEqual(code, 0, out)
        res = json.loads(out)["result"]
        self.assertEqual([c["client"] for c in res["clients"]], ["sample-client-a", "sample-client-b"])
        a = res["clients"][0]
        repo_a = a["repos"][0]
        act = dict(repo_a["active"][0])
        act.pop("dashboard")
        self.assertEqual(act, {"change": "feat-a", "phase": "tasks", "lane": "standard", "age_days": 13,
                               "in_phase_days": 4})
        self.assertEqual([(w["kind"], w["item"]) for w in repo_a["waiting"]], [("approval", "tasks"),
                                                                                ("question", "Q-01")])
        self.assertEqual(repo_a["waiting"][1]["flag"], "overdue")
        self.assertEqual(repo_a["released"], [{"change": "old", "version": "1.4.0", "date": "2026-10-05"}])
        self.assertEqual(repo_a["cost"], {"usd": 12.0, "changes": 2, "estimated_share": 0.17})
        self.assertEqual(a["totals"], {"active": 2, "waiting": 2, "released": 1, "usd": 12.0})

    def test_REQ_W3_048_the_spec_layout_is_read_and_marked(self):
        code, out = run_view("--json")
        repo_b = json.loads(out)["result"]["clients"][0]["repos"][1]
        self.assertEqual((repo_b["layout"], [x["change"] for x in repo_b["active"]]), ("spec/", ["feat-b"]))

    def test_REQ_W3_046_a_non_karvey_repository_is_shown_and_the_rest_render(self):
        code, out = run_view()
        self.assertEqual(code, 0, out)
        self.assertIn("repo-c · owner team-b — not a Karvey project", out)
        self.assertIn("active   feat-a · tasks · lane standard", out)

    def test_byte_identical_across_runs(self):
        self.assertEqual(run_view("--json")[1], run_view("--json")[1])
        self.assertEqual(run_view()[1], run_view()[1])


class ClientAndCommand(unittest.TestCase):
    """@req REQ-W3-078 REQ-W3-079"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-portfolio-client-"))
        repos = []
        for i in range(6):
            client = "Sample-Client-A" if i % 2 == 0 else "sample-client-b"
            name = "repo %d" % i if i == 0 else "repo-%d" % i  # the first path has a space
            cid = "x;rm" if i == 2 else "feat-%d" % i
            karvey_repo(self.tmp / name, changes=[(cid, {"change_id": cid, "phase": "impl", "lane": "standard",
                                                         "effort": [{"kind": "phase", "phase": "tasks",
                                                                     "at": "2026-10-10T10:00:00-03:00",
                                                                     "usd": {"value": 1.5, "quality": "exact"}}]})])
            repos.append({"path": name, "client": client, "owner": "team"})
        (self.tmp / "portfolio.json").write_text(json.dumps({"repos": repos}), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def view(self, *argv):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = CTX.main(["--portfolio", "--file", str(self.tmp / "portfolio.json")] + PERIOD + list(argv))
        return code, out.getvalue()

    def test_REQ_W3_078_one_client_its_three_repositories_and_totals(self):
        code, out = self.view("--client", "sample-client-a", "--json")
        res = json.loads(out)["result"]
        self.assertEqual(code, 0)
        self.assertEqual([c["client"] for c in res["clients"]], ["Sample-Client-A"])
        self.assertEqual(len(res["clients"][0]["repos"]), 3)
        self.assertEqual(res["clients"][0]["totals"]["usd"], 4.5)
        self.assertEqual(res["note"], "other clients: not shown")

    def test_REQ_W3_078_unknown_client_exit_0_with_the_line(self):
        code, out = self.view("--client", "sample-client-z")
        self.assertEqual(code, 0)
        self.assertIn("no repositories for client sample-client-z", out)

    def test_REQ_W3_079_invalid_change_id_prints_no_command(self):
        code, out = self.view("--client", "sample-client-a", "--json")
        repos = json.loads(out)["result"]["clients"][0]["repos"]
        bad = [a for r in repos for a in r["active"] if a["change"] == "x;rm"][0]
        self.assertIsNone(bad["dashboard"])
        self.assertEqual(bad["note"], "invalid change id")
        code, text = self.view("--client", "sample-client-a")
        self.assertIn("invalid change id: no dashboard command", text)
        self.assertNotIn("--change x;rm", text)

    def test_REQ_W3_079_a_path_with_a_space_is_quoted(self):
        code, out = self.view("--client", "sample-client-a", "--json")
        repos = json.loads(out)["result"]["clients"][0]["repos"]
        cmd = [a for r in repos for a in r["active"] if a["change"] == "feat-0"][0]["dashboard"]
        import shlex
        argv = shlex.split(cmd)
        self.assertEqual(argv[argv.index("--root") + 1], os.path.realpath(str(self.tmp / "repo 0")))
        self.assertEqual(argv[-2:], ["--change", "feat-0"])


class Offline(unittest.TestCase):
    """@req REQ-W3-047 — no process, no socket, no write: the fixture repositories are unchanged."""

    def snapshot(self):
        out = {}
        for dirpath, dirnames, filenames in os.walk(str(FIX)):
            dirnames.sort()
            for n in sorted(filenames + dirnames):
                p = os.path.join(dirpath, n)
                st = os.stat(p)
                out[os.path.relpath(p, str(FIX))] = (st.st_mtime_ns, st.st_size)
        return out

    def test_REQ_W3_047_no_process_no_socket_nothing_written(self):
        import socket
        import subprocess
        from unittest import mock

        def refuse(*a, **k):
            raise AssertionError("the portfolio view started a process or opened a socket")
        before = self.snapshot()
        with mock.patch.object(subprocess, "Popen", side_effect=refuse), \
                mock.patch.object(socket, "socket", side_effect=refuse), \
                mock.patch.object(os, "system", side_effect=refuse):
            code, out = run_view("--json")
            code2, text = run_view("--client", "sample-client-a")
        self.assertEqual((code, code2), (0, 0), out + text)
        self.assertEqual(len(json.loads(out)["result"]["clients"]), 2)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
