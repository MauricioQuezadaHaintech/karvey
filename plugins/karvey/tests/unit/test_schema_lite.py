import unittest

import _path  # noqa: F401
from karvey_lib import schema_lite as sl


def errs(issues):
    return [i for i in issues if i["severity"] == "error"]


def warns(issues):
    return [i for i in issues if i["severity"] == "warning"]


def v(schema, inst, strict=False, registry=None):
    return sl.Validator(schema, registry or {}).validate(inst, strict=strict)


class Keywords(unittest.TestCase):
    def test_type_incl_list_and_bool_not_integer(self):
        self.assertEqual(v({"type": "string"}, "x"), [])
        self.assertEqual(errs(v({"type": "string"}, 1))[0]["code"], "schema.type")
        self.assertEqual(v({"type": ["boolean", "null"]}, None), [])
        self.assertTrue(errs(v({"type": "integer"}, True)))
        self.assertEqual(v({"type": "number"}, 1.5), [])
        self.assertTrue(errs(v({"type": "array"}, {})))

    def test_enum_const(self):
        self.assertEqual(v({"enum": ["a", 1]}, 1), [])
        e = errs(v({"enum": ["a", "b"]}, "qa-approved"))[0]
        self.assertEqual((e["code"], e["got"]), ("schema.enum", "qa-approved"))
        self.assertTrue(errs(v({"const": 1}, 2)))
        self.assertEqual(v({"const": "human"}, "human"), [])

    def test_required_properties_additional(self):
        s = {"type": "object", "required": ["a"], "properties": {"a": {"type": "string"}},
             "additionalProperties": False}
        self.assertEqual(v(s, {"a": "x"}), [])
        e = errs(v(s, {}))[0]
        self.assertEqual((e["code"], e["path"]), ("schema.required", "$.a"))
        self.assertEqual(errs(v(s, {"a": "x", "b": 1}))[0]["code"], "schema.additionalProperties")
        s2 = {"type": "object", "additionalProperties": {"type": "integer"}}
        self.assertEqual(errs(v(s2, {"k": "x"}))[0]["path"], "$.k")

    def test_property_names(self):
        s = {"type": "object", "propertyNames": {"enum": ["mockup", "infra"]}}
        self.assertEqual(v(s, {"infra": "x"}), [])
        self.assertIn("'tasks'", errs(v(s, {"tasks": "x"}))[0]["message"])

    def test_items_min_items(self):
        s = {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}}
        self.assertEqual(v(s, ["a"]), [])
        self.assertEqual(errs(v(s, []))[0]["code"], "schema.minItems")
        self.assertEqual(errs(v(s, ["a", ""]))[0]["path"], "$[1]")

    def test_strings(self):
        self.assertTrue(errs(v({"minLength": 2}, "a")))
        self.assertTrue(errs(v({"maxLength": 3}, "abcd")))
        self.assertEqual(v({"maxLength": 3}, "ñño"), [])
        self.assertEqual(v({"pattern": "^(D-\\d+|https://\\S+)$"}, "D-08"), [])
        self.assertTrue(errs(v({"pattern": "^(D-\\d+|https://\\S+)$"}, "session approval: ok")))
        self.assertEqual(v({"pattern": "b"}, "abc"), [])  # unanchored search, as JSON Schema
        # lookbehind used by project.schema branchName
        bn = "^(?!-)(?!.*\\.\\.)[A-Za-z0-9._/-]{1,100}(?<!\\.lock)(?<!/)$"
        self.assertEqual(v({"pattern": bn}, "feature/x"), [])
        self.assertTrue(errs(v({"pattern": bn}, "x.lock")))

    def test_numbers(self):
        s = {"type": "integer", "minimum": 5, "maximum": 1440}
        self.assertEqual(v(s, 120), [])
        self.assertEqual(errs(v(s, 4))[0]["code"], "schema.minimum")
        self.assertEqual(errs(v(s, 1441))[0]["code"], "schema.maximum")
        self.assertEqual(v({"minimum": 0}, "x"), [])  # applies to numbers only

    def test_one_of_any_of(self):
        s = {"oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]}
        self.assertEqual(v(s, "BL-1"), [])
        self.assertEqual(v(s, ["BL-1"]), [])
        self.assertEqual(errs(v(s, 3))[0]["code"], "schema.oneOf")
        both = {"oneOf": [{"type": "string"}, {"minLength": 1}]}
        self.assertIn("exactly one", errs(v(both, "x"))[0]["message"])
        a = {"anyOf": [{"type": "string"}, {"type": "array"}]}
        self.assertEqual(v(a, "x"), [])
        self.assertTrue(errs(v(a, 1)))

    def test_if_then_else(self):
        s = {"if": {"properties": {"approved": {"const": True}}, "required": ["approved"]},
             "then": {"required": ["by"]}, "else": {"required": ["why"]}}
        self.assertEqual(v(s, {"approved": True, "by": "x"}), [])
        self.assertEqual(errs(v(s, {"approved": True}))[0]["path"], "$.by")
        self.assertEqual(errs(v(s, {"approved": False}))[0]["path"], "$.why")

    def test_local_ref(self):
        s = {"$defs": {"phase": {"enum": ["init", "impl"]}}, "properties": {"phase": {"$ref": "#/$defs/phase"}}}
        self.assertEqual(v(s, {"phase": "impl"}), [])
        self.assertEqual(errs(v(s, {"phase": "shipping"}))[0]["path"], "$.phase")

    def test_cross_file_ref(self):
        other = {"$id": "karvey:other.schema.json", "$defs": {"t": {"enum": ["markdown"]}}}
        s = {"$id": "karvey:main.schema.json", "properties": {"m": {"$ref": "karvey:other.schema.json#/$defs/t"}}}
        reg = {"karvey:other.schema.json": other}
        self.assertEqual(v(s, {"m": "markdown"}, registry=reg), [])
        self.assertTrue(errs(v(s, {"m": "jira"}, registry=reg)))
        with self.assertRaises(sl.SchemaError):
            v(s, {"m": "x"}, registry={})

    def test_error_shape(self):
        e = sl.Validator({"type": "object", "required": ["phase"]}, {}, file="spec.json").validate({})[0]
        self.assertEqual(set(e), {"code", "severity", "file", "path", "expected", "got", "message"})
        self.assertEqual(e["file"], "spec.json")


class Extensions(unittest.TestCase):
    def test_severity_warning(self):
        s = {"properties": {"created_at": {"type": "string", "x-karvey-format": "datetime-tz",
                                            "x-karvey-severity": "warning"}}}
        out = v(s, {"created_at": "2026-09-23"})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["severity"], "warning")
        self.assertEqual(out[0]["code"], "schema.format")
        self.assertEqual(v(s, {"created_at": "2026-09-23"}, strict=True)[0]["severity"], "error")
        self.assertEqual(v(s, {"created_at": "2026-09-23T10:00:00-03:00"}), [])

    def test_severity_inherited_by_then(self):
        s = {"if": {"required": ["approved"]},
             "then": {"required": ["by", "ref"], "x-karvey-severity": "warning"}}
        out = v(s, {"approved": True})
        self.assertEqual([i["severity"] for i in out], ["warning", "warning"])

    def test_legacy_note_on_match(self):
        s = {"type": "object",
             "properties": {"gates_skipped": {"type": "object", "x-karvey-severity": "warning",
                                              "x-karvey-note": "legacy → skipped (--fix)"},
                            "lane": {"type": "string", "x-karvey-note": "data only"}},
             "additionalProperties": {"type": "object", "x-karvey-severity": "warning",
                                      "x-karvey-note": "unknown key"}}
        out = v(s, {"gates_skipped": {}, "lane": "standard", "impl": {}})
        self.assertEqual(sorted(i["message"] for i in out), ["legacy → skipped (--fix)", "unknown key"])
        self.assertTrue(all(i["severity"] == "warning" and i["code"] == "schema.legacy" for i in out))

    def test_legacy_branch_of_one_of(self):
        s = {"$defs": {"tool": {"enum": ["markdown", "clickup"]}},
             "oneOf": [{"$ref": "#/$defs/tool", "x-karvey-severity": "warning", "x-karvey-note": "legacy string"},
                       {"type": "object", "required": ["tool"], "properties": {"tool": {"$ref": "#/$defs/tool"}}}]}
        out = v(s, "markdown")
        self.assertEqual([(i["severity"], i["message"]) for i in out], [("warning", "legacy string")])
        self.assertEqual(v(s, {"tool": "markdown"}), [])
        self.assertTrue(errs(v(s, 42)))

    def test_datetime_tz(self):
        ok = ["2026-09-23T21:10:00-03:00", "2026-09-23T21:10Z", "2026-09-23T21:10:00.123456789+00:00"]
        bad = ["2026-09-23", "2026-09-23T21:10:00", "2026-13-01T00:00:00Z", "yesterday", 5]
        for x in ok:
            self.assertTrue(sl.is_datetime_tz(x), x)
        for x in bad:
            self.assertFalse(sl.is_datetime_tz(x), x)


class Subset(unittest.TestCase):
    def test_unsupported_keyword_is_an_error(self):
        for bad in ({"format": "date-time"}, {"patternProperties": {}}, {"uniqueItems": True},
                    {"properties": {"a": {"maxItems": 2}}}, {"$defs": {"x": {"allOf": []}}},
                    {"x-karvey-unknown": 1}):
            with self.assertRaises(sl.SchemaError, msg=str(bad)) as cm:
                sl.Validator(bad, {})
            self.assertIn("unsupported keyword", str(cm.exception))

    def test_bad_extension_values(self):
        with self.assertRaises(sl.SchemaError):
            sl.Validator({"x-karvey-severity": "info"}, {})
        with self.assertRaises(sl.SchemaError):
            sl.Validator({"x-karvey-format": "date"}, {})
        with self.assertRaises(sl.SchemaError):
            sl.Validator({"$ref": "https://example.com/x.json"}, {})

    def test_annotations_allowed(self):
        s = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "karvey:x.schema.json",
             "$comment": "c", "title": "t", "description": "d", "x-karvey-schema-version": 1,
             "properties": {"a": {"type": "integer", "x-karvey-default": 7, "x-karvey-note": "n",
                                  "x-karvey-safe": "status"}}}
        self.assertEqual(sl.check_schema(s), [])
        self.assertEqual(v(s, {"a": 1}), [])


if __name__ == "__main__":
    unittest.main()
