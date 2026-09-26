"""The effort record (architecture §1.9, C-09): ``karvey_lib/effort.py`` and ``karvey-state.py effort``.

@req REQ-W3-014 REQ-W3-015 REQ-W3-016 REQ-W3-017
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import _path
from karvey_lib import effort

FIX = _path.UNIT_DIR / "fixtures" / "effort"
TA, TB = str(FIX / "transcript-a.jsonl"), str(FIX / "transcript-b.jsonl")
RK = "0123456789abcdef"
AT = "2026-09-26T10:00:00-03:00"


class Lib(unittest.TestCase):
    """@req REQ-W3-015 — capture pick, intervals, charged file, gaps."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="karvey-effort-"))

    def tearDown(self):
        shutil.rmtree(str(self.dir), ignore_errors=True)

    def capture(self, h="sess1", usd=1.5, transcript=TA, at="2026-09-26T10:00:00-03:00", rk=RK, **extra):
        rec = dict({"root_key": rk, "usd": usd, "transcript": transcript, "context_pct": 12.0,
                    "context_tokens": 24000, "at": at}, **extra)
        (self.dir / (h + ".json")).write_text(json.dumps(rec), encoding="utf-8")

    def close(self, phase="requirements", review=None):
        entry, charge = effort.compute(self.dir, RK, phase, AT, review)
        if charge is not None:
            effort.write_charged(self.dir, entry["session"], charge)
        return entry

    def test_transcript_usage_counts_a_message_once(self):
        u = effort.transcript_usage(TA)
        self.assertEqual(u, {"in": 120, "out": 80, "cache_read": 2500, "cache_write": 200, "total": 2900})

    def test_first_close_counts_from_session_start(self):
        self.capture()
        e = self.close()
        self.assertEqual(e["usd"], {"value": 1.5, "quality": "exact", "source": "runtime statusline"})
        self.assertEqual((e["tokens"]["total"], e["tokens"]["quality"]), (2900, "exact"))
        self.assertEqual(e["session"], "sess1")
        self.assertEqual(e["review_min"]["quality"], "n/a")

    def test_F42_statusline_rewrite_does_not_reset_the_charged_file(self):
        self.capture()
        self.close()
        self.capture(usd=2.0, at="2026-09-26T10:30:00-03:00")   # the statusline rewrites its file whole
        e = self.close("mockup")
        self.assertEqual(e["usd"]["value"], 0.5)
        self.assertEqual(e["tokens"]["total"], 0)

    def test_two_changes_in_one_session_get_their_own_interval(self):
        self.capture(usd=1.0)
        a = self.close("requirements")
        self.capture(usd=2.5, at="2026-09-26T11:00:00-03:00")
        b = self.close("architecture")
        self.assertEqual((a["usd"]["value"], b["usd"]["value"]), (1.0, 1.5))

    def test_unreadable_capture_is_na_and_the_gap_is_charged_once(self):
        self.capture(usd=1.0)
        self.close()
        (self.dir / "sess1.json").write_text("{broken", encoding="utf-8")
        e, charge = effort.compute(self.dir, RK, "mockup", AT)
        self.assertEqual((e["usd"]["value"], e["usd"]["quality"], e["usd"]["reason"]),
                         (None, "n/a", "capture unreadable"))
        self.assertIsNone(charge)
        self.capture(usd=3.0, at="2026-09-26T12:00:00-03:00")
        self.assertEqual(self.close("design_graphic")["usd"]["value"], 2.0)
        self.capture(usd=3.0, at="2026-09-26T12:10:00-03:00")
        self.assertEqual(self.close("architecture")["usd"]["value"], 0.0)

    def test_a_new_shorter_transcript_starts_a_new_interval(self):
        self.capture()
        self.close()
        self.capture(usd=2.0, transcript=TB, at="2026-09-26T11:00:00-03:00")
        self.assertEqual(self.close("mockup")["tokens"]["total"], 15)

    def test_F43_context_window_figures_are_never_tokens(self):
        self.capture(transcript=None, context_tokens=50000)
        e = self.close()
        self.assertEqual((e["tokens"]["quality"], e["tokens"]["reason"]), ("n/a", "transcript unreadable"))
        self.assertNotIn("50000", json.dumps(e))
        self.assertEqual(e["usd"]["value"], 1.5)

    def test_no_capture_is_na_statusline_not_installed_never_zero(self):
        e = self.close()
        self.assertEqual(e["usd"], {"value": None, "quality": "n/a", "reason": "statusline not installed",
                                    "source": "runtime statusline"})
        self.assertEqual(e["tokens"]["quality"], "n/a")

    def test_two_sessions_within_120s_are_estimated(self):
        self.capture("sess1", usd=1.0, at="2026-09-26T10:00:00-03:00")
        self.capture("sess2", usd=4.0, at="2026-09-26T10:01:30-03:00")
        e = self.close()
        self.assertEqual(e["session"], "sess2")
        self.assertEqual((e["usd"]["quality"], e["usd"]["reason"]),
                         ("estimated", "two sessions active on this repository"))

    def test_another_roots_capture_is_ignored(self):
        self.capture("other", rk="ffffffffffffffff")
        self.assertEqual(self.close()["usd"]["reason"], "statusline not installed")

    def test_review_minutes_exact_when_stated(self):
        self.capture()
        self.assertEqual(self.close(review=12)["review_min"],
                         {"value": 12, "quality": "exact", "source": "stated at the gate"})


if __name__ == "__main__":
    unittest.main()
