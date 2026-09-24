"""approval vocabulary: normalisation, stripping, negation precedence, position rule, kind (E1.F5.T2)."""
import unittest

import _path  # noqa: F401
from karvey_lib import approval as a


def ok(text, vocab=None):
    return a.classify(text, vocab)["approved"]


def kind(text, vocab=None):
    return a.classify(text, vocab)["kind"]


class Normalise(unittest.TestCase):
    def test_accents_case_whitespace_apostrophes(self):
        self.assertEqual(a.normalise("  Sí,\tAPROBADO\n\n  ejecutá "), "si, aprobado ejecuta")
        self.assertEqual(a.normalise("don’t"), "don't")
        self.assertEqual(a.normalise("PRODUCCIÓN"), "produccion")


class Strip(unittest.TestCase):
    def test_fences_inline_quotes_blockquotes_long_lines(self):
        t = a.strip_quoted('ok\n```\nstatus: approved\n```\n> approved by QA\n`approved` "approved" '
                           '“approved” «approved»\n' + "approved " * 30)
        self.assertNotIn("approved", t)
        self.assertIn("ok", t)

    def test_unterminated_fence_removes_to_the_end(self):
        self.assertNotIn("approved", a.strip_quoted("mira:\n```\napproved\n"))


class Classify(unittest.TestCase):
    def test_default_approvals(self):
        for t in ("aprobado, ejecuta", "ok", "dale", "approved, go ahead", "lgtm", "ship it", "Sí", "okey",
                  "procede", "perfecto"):
            self.assertTrue(ok(t), t)

    def test_negations_and_questions_win(self):
        for t in ("no apruebo todavía", "¿está aprobado?", "no, espera", "don't proceed yet", "ok pero antes revisa X",
                  "is it approved?", "ok, wait", "stop", "todavía no", "aún no, dale después", "ok? "):
            self.assertFalse(ok(t), t)

    def test_quoted_material_never_approves(self):
        for t in ("```\nstatus: approved\n```", "> approved by QA", 'el log dice "approved"', "`lgtm`"):
            self.assertFalse(ok(t), t)

    def test_word_boundaries(self):
        self.assertFalse(ok("okapi token broker"))   # 'ok' inside a word
        self.assertFalse(ok("notok"))
        self.assertTrue(ok("OK."))

    def test_position_rule_12_words_or_120_chars(self):
        short_late = "revisa esto y lo otro y lo de mas alla y despues ok"
        self.assertLessEqual(len(short_late), 120)
        self.assertTrue(ok(short_late))                       # ≤ 120 chars: anywhere
        long_late = "\n".join(["esto es contexto largo que explica la situacion"] * 3 + ["ok"])
        self.assertGreater(len(long_late), 120)
        self.assertFalse(ok(long_late))                       # > 120 chars: first 12 words only
        long_early = "ok, adelante\n" + "\n".join(["detalle del plan que sigue"] * 10)
        self.assertTrue(ok(long_early))

    def test_huge_prompt_scans_only_the_first_2kb(self):
        self.assertTrue(ok("dale\n" + "x\n" * 20000))
        self.assertFalse(ok("\n".join(["contexto"] * 3000) + "\nok"))

    def test_kind_prod_needs_both_words_d10(self):
        self.assertEqual(kind("ok, merge a prod"), "prod")
        self.assertEqual(kind("dale, release a producción"), "prod")
        self.assertEqual(kind("aprobado"), "plan")
        self.assertIsNone(kind("merge a prod"))              # a prod word alone approves nothing
        self.assertIsNone(kind("no hagas merge a main"))

    def test_project_override_replaces_lists(self):
        v = a.vocabulary({"approve": ["vamos"], "negate": ["ojo"], "bogus": ["x"], "prod_terms": [42]})
        self.assertTrue(ok("vamos", v))
        self.assertFalse(ok("ok", v))
        self.assertFalse(ok("vamos, ojo", v))
        self.assertIn("prod", v["prod_terms"])               # an invalid list keeps the default
        self.assertEqual(a.vocabulary(None)["approve"], a.default_vocabulary()["approve"])


class Scope(unittest.TestCase):
    def test_named_change_then_active_then_project(self):
        ids = ["feat-a", "feat-ab"]
        self.assertEqual(a.scope_for("ok con feat-ab", ids), "feat-ab")
        self.assertEqual(a.scope_for("ok con feat-a.", ids, active="feat-ab"), "feat-a")
        self.assertEqual(a.scope_for("ok", ids, active="feat-a"), "feat-a")
        self.assertEqual(a.scope_for("ok", ids), "_project")
        self.assertEqual(a.scope_for("ok feat-abc", ids), "_project")


if __name__ == "__main__":
    unittest.main()
