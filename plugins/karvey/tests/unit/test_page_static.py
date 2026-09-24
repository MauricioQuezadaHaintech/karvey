"""Static checks of the method page docs/karvey.html (E1.F11.T2; BUG-14, REQ-W1-106, REQ-ADP-030).

html.parser only (stdlib): the markup nests cleanly, ids are unique, every in-page anchor resolves,
nothing is fetched from outside the file, the five language blocks share one structure, and the
language switch is not visible without JavaScript.
"""
import re
import unittest
from html.parser import HTMLParser

import _path

PAGE = _path.REPO_ROOT / "docs" / "karvey.html"
LANGS = ("en", "es", "pt", "de", "zh")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
        "track", "wbr", "path", "circle", "rect", "line", "polyline", "polygon", "ellipse", "use", "stop"}
# elements whose end tag HTML lets you omit; the page closes them anyway, so they are checked too
FETCHING = {("script", "src"), ("link", "href"), ("img", "src"), ("iframe", "src"), ("source", "src"),
            ("video", "src"), ("audio", "src"), ("embed", "src"), ("object", "data"), ("image", "href"),
            ("use", "href"), ("img", "srcset")}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = {}
        self.hrefs = []
        self.fetches = []
        self.elements = []          # (tag, attrs, path of open tags)
        self.block = None           # current language block
        self.block_depth = None
        self.shapes = {l: [] for l in LANGS}
        self.style = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.elements.append((tag, a, tuple(t for t, _ in self.stack)))
        if "id" in a:
            self.ids.setdefault(a["id"], 0)
            self.ids[a["id"]] += 1
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        for t, attr in FETCHING:
            if tag == t and a.get(attr):
                self.fetches.append((tag, attr, a[attr]))
        if tag == "div" and "lang-block" in (a.get("class") or "").split() and self.block is None:
            self.block, self.block_depth = a.get("data-lang"), len(self.stack)
        if self.block in self.shapes:
            self.shapes[self.block].append((tag, re.sub(r"^%s-" % self.block, "", a.get("id") or "")))
        if tag == "style":
            self._in_style = True
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1][0] != tag:
            self.errors.append("line %d: </%s> does not close %r" % (self.getpos()[0], tag,
                                                                    self.stack[-1] if self.stack else None))
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break
            return
        self.stack.pop()
        if tag == "style":
            self._in_style = False
        if self.block is not None and len(self.stack) == self.block_depth:
            self.block, self.block_depth = None, None

    def handle_data(self, data):
        if self._in_style:
            self.style.append(data)


def parse():
    p = Page()
    p.feed(PAGE.read_text(encoding="utf-8"))
    p.close()
    return p


class Markup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = parse()
        cls.css = "".join(cls.p.style)

    def test_parses_without_errors(self):
        self.assertEqual(self.p.errors, [])
        self.assertEqual([t for t, _ in self.p.stack], [], "unclosed elements at the end")

    def test_no_duplicate_ids(self):
        dup = sorted(i for i, n in self.p.ids.items() if n > 1)
        self.assertEqual(dup, [])

    def test_every_in_page_anchor_resolves(self):
        broken = sorted({h for h in self.p.hrefs if h.startswith("#") and len(h) > 1 and h[1:] not in self.p.ids})
        self.assertEqual(broken, [])

    def test_self_contained(self):
        self.assertEqual(self.p.fetches, [], "the page must not fetch anything")
        self.assertNotRegex(self.css, r"@import|url\(\s*['\"]?(https?:)?//")

    def test_five_blocks_share_one_structure(self):
        for l in LANGS:
            self.assertTrue(self.p.shapes[l], "block %s missing" % l)
        base = [t for t, _ in self.p.shapes["en"]]
        for l in LANGS[1:]:
            self.assertEqual([t for t, _ in self.p.shapes[l]], base, "block %s differs in structure from en" % l)
        ids = [i for _, i in self.p.shapes["en"] if i]
        for l in LANGS[1:]:
            self.assertEqual([i for _, i in self.p.shapes[l] if i], ids, "block %s ids differ from en" % l)


class NoInertSwitch(unittest.TestCase):
    """BUG-14 / REQ-W1-106: with JavaScript disabled no language switch is visible; English renders."""

    @classmethod
    def setUpClass(cls):
        cls.p = parse()
        cls.css = "".join(cls.p.style)

    def test_html_has_no_js_class_in_static_markup(self):
        html = [a for t, a, _ in self.p.elements if t == "html"][0]
        self.assertNotIn("js", (html.get("class") or "").split())
        self.assertNotIn("data-lang", html, "data-lang must come from the script, not the markup")

    def test_switch_links_are_inside_a_hidden_container(self):
        links = [(a, path) for t, a, path in self.p.elements if t == "a" and "data-set-lang" in a]
        self.assertEqual(sorted(a["data-set-lang"] for a, _ in links), sorted(LANGS))
        navs = [a for t, a, _ in self.p.elements if "langs" in (a.get("class") or "").split()]
        self.assertEqual(len(navs), 1)
        self.assertIn("hidden", navs[0], "the switch container carries the hidden attribute")
        for _, path in links:
            self.assertIn("nav", path)

    def test_css_hides_the_switch_until_js(self):
        self.assertIn("html:not(.js) .langs{display:none}", self.css)
        self.assertIn(".langs[hidden]{display:none}", self.css)
        self.assertIn("html.js .langs[hidden]{display:flex}", self.css)

    def test_english_renders_without_js(self):
        self.assertIn('.lang-block:not([data-lang="en"]){display:none}', self.css)
        self.assertNotRegex(self.css, r'\.lang-block\[data-lang="en"\]\{display:none')

    def test_scripts_add_the_js_class(self):
        text = PAGE.read_text(encoding="utf-8")
        scripts = re.findall(r"<script>([\s\S]*?)</script>", text)
        self.assertEqual(len(scripts), 2)
        self.assertIn("'js'", scripts[0])
        self.assertIn("nav.hidden=false", scripts[1])


if __name__ == "__main__":
    unittest.main()
