"""The legacy fixtures carry shapes only, never client data (architecture §6.3, E1.F14.T1).

Rules for every file under ``tests/fixtures/legacy/``:
- a ``change_id`` is ``fixture-NN``;
- free text is ``"…"``: any string with whitespace in it is exactly ``"…"``;
- no ``@`` anywhere (no e-mail, no mention) and no run of 6 or more digits (no tracker, list or phone ids);
- every key is in the catalogue: a property of the two schemas, or one of the legacy keys §2.5/§6.3 names.
"""
import json
import re
import unittest

import _path

LEGACY = _path.FIXTURES_DIR / "legacy"

# Keys the scan found that no schema declares (architecture §2.5 and §6.3); anything else is not a shape
# the catalogue describes and must not be copied into a fixture.
LEGACY_KEYS = {
    # approvals: embedded skips and unknown approval names
    "skipped", "skip_reason", "na", "na_reason", "not_applicable", "reason", "note", "nota",
    "impl", "test", "deploy_dev", "deploy_prod", "design", "mockup_iter3",
    # spec.json multi-type fields and the legacy gates / history shapes
    "depends_on", "gates_skipped", "phases", "from", "to", "at",
    # unknown top-level keys, allowed by additionalProperties
    "fases", "orden", "verificacion", "notes", "ripple", "tenant",
    # project.json legacy extras
    "backlog_list_id", "status_flow", "location_name", "via", "client_tag", "wbs_note", "workspace_id", "hierarchy",
    "space", "channel",
    # project.json `repos` as objects (BUG-33)
    "name", "url", "stack", "layer",
}
KEY_PATTERNS = (re.compile(r"^E\d+\.F\d+\.T\d+$"), re.compile(r"^[DC]-\d+$"))
DIGIT_RUN = re.compile(r"\d{6,}")


def schema_keys():
    keys = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "properties" and isinstance(v, dict):
                    keys.update(v)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for name in ("spec.schema.json", "project.schema.json"):
        walk(json.loads((_path.SCHEMAS_DIR / name).read_text(encoding="utf-8")))
    return keys


def walk_items(node, path="$"):
    """Yield ``(path, key_or_None, value)`` for every key and every leaf."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k, v
            yield from walk_items(v, "%s.%s" % (path, k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_items(v, "%s[%d]" % (path, i))
    else:
        yield path, None, node


class Anonymous(unittest.TestCase):
    def fixtures(self):
        files = sorted(LEGACY.rglob("*.json"))
        self.assertTrue(files, "no legacy fixture found")
        return files

    def test_raw_text_has_no_at_sign_and_no_long_digit_run(self):
        for f in self.fixtures():
            text = f.read_text(encoding="utf-8-sig")
            with self.subTest(fixture=f.name):
                self.assertNotIn("@", text)
                self.assertIsNone(DIGIT_RUN.search(text), DIGIT_RUN.search(text))

    def test_change_id_and_free_text(self):
        for f in self.fixtures():
            data = json.loads(f.read_text(encoding="utf-8-sig"))
            with self.subTest(fixture=f.name):
                if "change_id" in data:
                    self.assertRegex(data["change_id"], r"^fixture-\d\d$")
                for path, key, value in walk_items(data):
                    if key is None and isinstance(value, str) and re.search(r"\s", value):
                        self.assertEqual(value, "…", "free text at %s" % path)

    def test_every_key_is_in_the_catalogue(self):
        allowed = schema_keys() | LEGACY_KEYS
        for f in self.fixtures():
            data = json.loads(f.read_text(encoding="utf-8-sig"))
            for path, key, _ in walk_items(data):
                if key is None or key in allowed or any(p.match(key) for p in KEY_PATTERNS):
                    continue
                self.fail("%s: key %r at %s is outside the §6.3 catalogue" % (f.name, key, path))

    def test_change_ids_are_unique(self):
        seen = {}
        for f in self.fixtures():
            cid = json.loads(f.read_text(encoding="utf-8-sig")).get("change_id")
            if cid is None:
                continue
            self.assertNotIn(cid, seen, "%s and %s share %s" % (seen.get(cid), f.name, cid))
            seen[cid] = f.name


class NoRealChatSpaceIds(unittest.TestCase):
    """BUG-32: the tests carried a real team chat space id. Every chat-space-shaped id in the plugin's tests
    (``spaces/`` plus 11 id characters, the real format) is a placeholder that says so."""

    SPACE_ID = re.compile(r"spaces/([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])")

    def test_space_ids_are_placeholders(self):
        for f in sorted(_path.TESTS_DIR.rglob("*")):
            if not f.is_file() or f.suffix not in (".py", ".json", ".md", ".sh", ".mjs"):
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            for m in self.SPACE_ID.finditer(text):
                with self.subTest(file=str(f.relative_to(_path.TESTS_DIR)), id=m.group(0)):
                    self.assertRegex(m.group(1).lower(), "example|fixture",
                                     "real-looking chat space id; use a placeholder such as spaces/AAAAexample1")


if __name__ == "__main__":
    unittest.main()
