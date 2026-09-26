"""Check-mode registry (architecture §1.5 of wave2-structural).

@req REQ-W2-083 REQ-W2-084 REQ-W2-085 REQ-W2-010
"""
import json
import unittest

import _path  # noqa: F401
import _gitrepo as g
from karvey_lib import modes

FOUR_ZERO_FLIPS = {"schema.strict", "gates.merged", "release.manifest"}
W3_BLOCKING = {"sponsor.leak", "loadlist.missing"}
W3_CHECKS = {"effort.record", "effort.mixed", "sponsor.leak", "loadlist.missing", "risks.owner", "risks.unreviewed",
             "questions.overdue", "design.undeclared", "design.contrast", "wbs.split", "wbs.legacy",
             "client.mismatch", "backlog.stale", "settings.valid", "incident.state", "cost.cap_key"}


def w2_ids():
    """The Wave 2 rows: those that declare a 3.13 default."""
    return [c for c in modes.check_ids() if "3.13" in modes.row(c)["defaults"]]


class Registry(unittest.TestCase):
    def test_REQ_W2_083_nine_checks_each_with_both_defaults(self):
        ids = w2_ids()
        self.assertEqual(len(ids), 9)
        self.assertEqual(len(set(modes.check_ids())), len(modes.check_ids()))
        for cid in ids:
            r = modes.row(cid)
            self.assertEqual(set(r["defaults"]), {"3.13", "4.0", "4.1"}, cid)
            for line in ("3.13", "4.0", "4.1"):
                self.assertIn(r["defaults"][line], modes.levels_of(cid), cid)

    def test_REQ_W2_084_no_313_default_is_blocking(self):
        for cid in w2_ids():
            self.assertNotEqual(modes.default(cid, "3.13"), "blocking", cid)
            self.assertNotEqual(modes.default(cid, "3.13"), "merged", cid)

    def test_REQ_W2_085_40_differs_only_for_the_three(self):
        flipped = {c for c in w2_ids() if modes.default(c, "3.13") != modes.default(c, "4.0")}
        self.assertEqual(flipped, FOUR_ZERO_FLIPS)

    def test_release_line(self):
        self.assertEqual(modes.release_line("3.13.0"), "3.13")
        self.assertEqual(modes.release_line("3.11.4"), "3.13")
        self.assertEqual(modes.release_line("4.0.0"), "4.0")
        self.assertEqual(modes.release_line("4.0.3"), "4.0")
        self.assertEqual(modes.release_line("4.1.0"), "4.1")
        self.assertEqual(modes.release_line("4.1.7"), "4.1")
        self.assertEqual(modes.release_line("4.2.0"), "4.1")

    def test_unknown_check(self):
        with self.assertRaises(modes.ModeError):
            modes.resolve(project={}, check_id="nope")


class Wave3Registry(unittest.TestCase):
    """@req REQ-W3-061 — every Wave 3 check has a 4.1 mode; only two are blocking."""

    def test_REQ_W3_061_the_sixteen_rows_declare_41(self):
        w3 = {c for c in modes.check_ids() if "3.13" not in modes.row(c)["defaults"]}
        self.assertEqual(w3, W3_CHECKS)
        for cid in w3:
            self.assertEqual(set(modes.row(cid)["defaults"]), {"4.1"}, cid)
            self.assertIn(modes.default(cid, "4.1"), modes.levels_of(cid), cid)

    def test_REQ_W3_061_no_41_default_blocking_but_two(self):
        blocking = {c for c in W3_CHECKS if modes.default(c, "4.1") == "blocking"}
        self.assertEqual(blocking, W3_BLOCKING)
        for cid in W3_CHECKS - W3_BLOCKING:
            self.assertIn(modes.default(cid, "4.1"), ("advisory", "warn"), cid)

    def test_wave2_rows_keep_their_40_values_under_41(self):
        for cid in w2_ids():
            self.assertEqual(modes.default(cid, "4.1"), modes.default(cid, "4.0"), cid)
            self.assertEqual(modes.resolve(project={}, check_id=cid, version="4.1.0")["mode"],
                             modes.default(cid, "4.0"), cid)

    def test_a_wave3_check_on_an_older_line_takes_its_first_default(self):
        self.assertEqual(modes.default("risks.owner", "3.13"), "warn")
        r = modes.resolve(project={"checks": {"risks.owner": "off"}}, check_id="risks.owner", version="4.1.0")
        self.assertEqual(r["mode"], "off")
        self.assertIn("4.1 default", r["warning"])


class Resolve(unittest.TestCase):
    def test_default_when_no_override(self):
        r = modes.resolve(project={}, check_id="release.manifest", version="3.13.0")
        self.assertEqual((r["mode"], r["warning"]), ("warn", None))
        r = modes.resolve(project={}, check_id="release.manifest", version="4.0.0")
        self.assertEqual(r["mode"], "blocking")

    def test_stricter_override_taken(self):
        r = modes.resolve(project={"checks": {"lane.diff": "blocking"}}, check_id="lane.diff", version="3.13.0")
        self.assertEqual((r["mode"], r["source"], r["warning"]), ("blocking", "project.json", None))

    def test_laxer_than_40_warns_naming_the_check(self):
        r = modes.resolve(project={"checks": {"release.manifest": "off"}}, check_id="release.manifest",
                          version="3.13.0")
        self.assertEqual(r["mode"], "off")
        self.assertIn("release.manifest", r["warning"])
        self.assertIn("laxer", r["warning"])

    def test_project_keys(self):
        self.assertEqual(modes.resolve(project={"gates": "merged"}, check_id="gates.merged")["mode"], "merged")
        self.assertEqual(modes.resolve(project={"enforcement": {"trailer_guard": "warn"}},
                                       check_id="trailer.guard")["mode"], "warn")
        self.assertEqual(modes.resolve(project={"schema_mode": "strict"}, check_id="schema.strict")["mode"],
                         "blocking")
        self.assertEqual(modes.resolve(project={"judges": {"mode": "blocking"}}, check_id="judges.mode")["mode"],
                         "blocking")

    def test_invalid_value_falls_back_with_warning(self):
        r = modes.resolve(project={"checks": {"lane.diff": "loud"}}, check_id="lane.diff", version="3.13.0")
        self.assertEqual(r["mode"], "warn")
        self.assertIn("loud", r["warning"])


class Hits(unittest.TestCase):
    def setUp(self):
        self.t = g.TempDir()
        (self.t.path / "docs/spec/changes/feat-a").mkdir(parents=True)

    def tearDown(self):
        self.t.cleanup()

    def test_REQ_W2_010_record_hit_appends_one_line(self):
        rec = modes.record_hit(self.t.path, "feat-a", "lane.diff", "lane exceeded: 5 > 3 code files",
                               finding="F-3", at="2026-09-25T10:00:00-03:00")
        modes.record_hit(self.t.path, "feat-a", "release.manifest", "unmapped abc123")
        lines = (self.t.path / "docs/spec/changes/feat-a/checks.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 2)
        first = json.loads(lines[0])
        self.assertEqual(set(first), {"check", "at", "mode", "would_refuse", "detail", "finding"})
        self.assertEqual(first, rec)
        self.assertTrue(first["would_refuse"])
        self.assertEqual(first["mode"], "warn")
        self.assertEqual([h["check"] for h in modes.read_hits(self.t.path / "docs/spec/changes/feat-a/checks.jsonl")],
                         ["lane.diff", "release.manifest"])

    def test_invalid_change_refused(self):
        with self.assertRaises(modes.ModeError):
            modes.record_hit(self.t.path, "../x", "lane.diff", "d")
        with self.assertRaises(modes.ModeError):
            modes.record_hit(self.t.path, "missing", "lane.diff", "d")


if __name__ == "__main__":
    unittest.main()
