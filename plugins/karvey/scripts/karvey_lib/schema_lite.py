"""JSON-Schema subset validator, stdlib only (architecture §2.2).

Supported keywords (and nothing else; L-17 restricts the shipped schemas to them):
``type`` ``enum`` ``const`` ``required`` ``properties`` ``additionalProperties``
``propertyNames`` ``items`` ``minItems`` ``minLength`` ``maxLength`` ``pattern`` ``oneOf``
``anyOf`` ``if``/``then``/``else`` ``$ref`` ``minimum`` ``maximum``.

``$ref`` is either local (``#/$defs/name``) or cross-file (``karvey:<file>#/$defs/name``),
resolved through a registry of schemas by ``$id`` (by default the plugin's ``schemas/``).

Annotations accepted and ignored by validation: ``$schema`` ``$id`` ``$comment`` ``$defs``
``title`` ``description`` and the ``x-karvey-`` annotations ``note`` ``default`` ``safe``
``schema-version``.

The two behavioural extensions:
- ``x-karvey-severity: warning``: violations found under that node are warnings, not errors
  (in strict mode they are promoted to errors). When such a node also carries an
  ``x-karvey-note`` and it is *matched* as a property value, an ``additionalProperties``
  value or a ``oneOf``/``anyOf`` branch, the match itself is reported as a warning with the
  note (a legacy shape that validates, e.g. ``gates_skipped`` or a string ``management``).
- ``x-karvey-format: datetime-tz``: ISO 8601 date and time with an offset (or ``Z``).

Any other keyword makes the schema invalid (:class:`SchemaError`).
"""
import json
import re
from datetime import datetime
from pathlib import Path

from . import SCHEMAS_DIR, issue

VALIDATION_KEYWORDS = frozenset({
    "type", "enum", "const", "required", "properties", "additionalProperties", "propertyNames",
    "items", "minItems", "minLength", "maxLength", "pattern", "oneOf", "anyOf", "if", "then",
    "else", "$ref", "minimum", "maximum",
})
ANNOTATION_KEYWORDS = frozenset({"$schema", "$id", "$comment", "$defs", "title", "description"})
KARVEY_EXTENSIONS = frozenset({"x-karvey-severity", "x-karvey-format"})
KARVEY_ANNOTATIONS = frozenset({"x-karvey-note", "x-karvey-default", "x-karvey-safe",
                                "x-karvey-schema-version"})
SUPPORTED_KEYWORDS = VALIDATION_KEYWORDS | ANNOTATION_KEYWORDS | KARVEY_EXTENSIONS | KARVEY_ANNOTATIONS

TYPES = ("string", "integer", "number", "boolean", "object", "array", "null")

_DATETIME_TZ = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?(?:Z|[+-]\d{2}:\d{2})$")


class SchemaError(Exception):
    """The schema itself uses something outside the supported subset."""

    def __init__(self, problems):
        self.problems = problems
        super().__init__("; ".join("%s: %s" % p for p in problems))


def is_datetime_tz(value):
    if not isinstance(value, str) or not _DATETIME_TZ.match(value):
        return False
    v = value[:-1] + "+00:00" if value.endswith("Z") else value
    if "." in v:  # fromisoformat on 3.9/3.10 accepts only 3 or 6 fractional digits
        head, rest = v.split(".", 1)
        digits = re.match(r"\d+", rest).group(0)
        v = head + "." + (digits + "000000")[:6] + rest[len(digits):]
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return False
    return dt.tzinfo is not None


def _type_ok(value, t):
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "null":
        return value is None
    return False


def _type_name(value):
    for t in ("null", "boolean", "integer", "number", "string", "array", "object"):
        if _type_ok(value, t):
            return t
    return type(value).__name__


def _short(value, limit=60):
    try:
        s = json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        s = repr(value)
    return s if len(s) <= limit else s[: limit - 1] + "…"


def check_schema(schema, where="#"):
    """Return ``[(pointer, problem)]`` for everything outside the supported subset."""
    problems = []
    if isinstance(schema, bool):
        return problems
    if not isinstance(schema, dict):
        return [(where, "a schema must be an object or a boolean")]
    for key, val in schema.items():
        here = "%s/%s" % (where, key)
        if key not in SUPPORTED_KEYWORDS:
            problems.append((here, "unsupported keyword %r" % key))
            continue
        if key == "x-karvey-severity" and val != "warning":
            problems.append((here, "x-karvey-severity must be 'warning'"))
        elif key == "x-karvey-format" and val != "datetime-tz":
            problems.append((here, "x-karvey-format must be 'datetime-tz'"))
        elif key == "type":
            ts = val if isinstance(val, list) else [val]
            for t in ts:
                if t not in TYPES:
                    problems.append((here, "unknown type %r" % (t,)))
        elif key == "pattern":
            try:
                re.compile(val)
            except (re.error, TypeError) as exc:
                problems.append((here, "bad pattern: %s" % exc))
        elif key in ("properties", "$defs"):
            if not isinstance(val, dict):
                problems.append((here, "%s must be an object" % key))
            else:
                for name, sub in val.items():
                    problems.extend(check_schema(sub, "%s/%s" % (here, name)))
        elif key in ("additionalProperties", "propertyNames", "items", "if", "then", "else"):
            problems.extend(check_schema(val, here))
        elif key in ("oneOf", "anyOf"):
            if not isinstance(val, list) or not val:
                problems.append((here, "%s must be a non-empty array" % key))
            else:
                for i, sub in enumerate(val):
                    problems.extend(check_schema(sub, "%s/%d" % (here, i)))
        elif key == "required" and not (isinstance(val, list) and all(isinstance(x, str) for x in val)):
            problems.append((here, "required must be an array of strings"))
        elif key == "$ref" and not (isinstance(val, str) and (val.startswith("#") or val.startswith("karvey:"))):
            problems.append((here, "only local '#/…' and 'karvey:<file>#/…' references are supported"))
    return problems


def load_registry(directory=None):
    """Every ``*.schema.json`` in ``directory`` (default: the plugin's schemas/), by ``$id``."""
    reg = {}
    d = Path(directory) if directory else SCHEMAS_DIR
    if d.is_dir():
        for p in sorted(d.glob("*.schema.json")):
            with open(p, encoding="utf-8-sig") as fh:
                s = json.load(fh)
            reg[s.get("$id", "karvey:" + p.name)] = s
    return reg


def _violations(issues):
    """Issues that make a value invalid (a recognised legacy shape does not)."""
    return [i for i in issues if i["code"] != "schema.legacy"]


class Validator:
    """Validate instances against one root schema.

    ``validate(instance, strict=False)`` returns a list of issues (see ``karvey_lib.issue``).
    """

    def __init__(self, schema, registry=None, file=None):
        self.registry = dict(registry or {})
        self.root = schema
        self.root_id = schema.get("$id", "") if isinstance(schema, dict) else ""
        if self.root_id:
            self.registry.setdefault(self.root_id, schema)
        self.file = file
        problems = []
        for sid, s in [(self.root_id, schema)] + [(k, v) for k, v in self.registry.items() if k != self.root_id]:
            problems.extend(("%s%s" % (sid, ptr), msg) for ptr, msg in check_schema(s))
        if problems:
            raise SchemaError(problems)

    # -- references -------------------------------------------------------------------
    def _resolve(self, ref, base):
        if ref.startswith("#"):
            doc, frag, doc_id = base, ref[1:], None
        else:
            doc_id, _, frag = ref.partition("#")
            doc = self.registry.get(doc_id)
            if doc is None:
                raise SchemaError([(ref, "unresolvable reference (schema %r not in registry)" % doc_id)])
        node = doc
        for part in [p for p in frag.split("/") if p]:
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or part not in node:
                raise SchemaError([(ref, "unresolvable reference")])
            node = node[part]
        return node, doc

    # -- public -----------------------------------------------------------------------
    def validate(self, instance, strict=False):
        out = []
        self._v(instance, self.root, "$", self.root, False, out)
        if strict:
            for it in out:
                it["severity"] = "error"
        return out

    def is_valid(self, instance, strict=False):
        return not any(i["severity"] == "error" for i in self.validate(instance, strict))

    # -- core -------------------------------------------------------------------------
    def _add(self, out, warn, code, path, message, expected=None, got=None):
        out.append(issue("schema." + code, message, severity="warning" if warn else "error",
                         file=self.file, path=path, expected=expected, got=got))

    def _branch(self, instance, schema, path, base):
        tmp = []
        self._v(instance, schema, path, base, False, tmp)
        return tmp

    def _note_match(self, schema, base, path, out):
        """A matched warning node with a note reports the legacy shape it recognised."""
        node = schema
        seen = 0
        while isinstance(node, dict) and seen < 32:
            if node.get("x-karvey-severity") == "warning" and "x-karvey-note" in node:
                self._add(out, True, "legacy", path, str(node["x-karvey-note"]))
                return
            if "$ref" in node and len(node) <= 3:
                node, base = self._resolve(node["$ref"], base)
                seen += 1
                continue
            return

    def _v(self, inst, schema, path, base, warn, out):
        if schema is True:
            return
        if schema is False:
            self._add(out, warn, "false", path, "no value is allowed here")
            return
        if not isinstance(schema, dict):
            return
        warn = warn or schema.get("x-karvey-severity") == "warning"

        if "$ref" in schema:
            target, tbase = self._resolve(schema["$ref"], base)
            self._v(inst, target, path, tbase, warn, out)

        if "type" in schema:
            ts = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
            if not any(_type_ok(inst, t) for t in ts):
                self._add(out, warn, "type", path, "expected %s, got %s" % ("|".join(ts), _type_name(inst)),
                          expected="|".join(ts), got=_type_name(inst))
                return  # the other keywords would only repeat the mismatch
        if "const" in schema and inst != schema["const"]:
            self._add(out, warn, "const", path, "expected %s, got %s" % (_short(schema["const"]), _short(inst)),
                      expected=schema["const"], got=inst)
        if "enum" in schema and inst not in schema["enum"]:
            self._add(out, warn, "enum", path, "%s is not one of %s" % (_short(inst), _short(schema["enum"], 200)),
                      expected=schema["enum"], got=inst)

        if isinstance(inst, str):
            if "minLength" in schema and len(inst) < schema["minLength"]:
                self._add(out, warn, "minLength", path, "shorter than %d characters" % schema["minLength"],
                          expected=">= %d chars" % schema["minLength"], got=inst)
            if "maxLength" in schema and len(inst) > schema["maxLength"]:
                self._add(out, warn, "maxLength", path, "longer than %d characters" % schema["maxLength"],
                          expected="<= %d chars" % schema["maxLength"], got=_short(inst))
            if "pattern" in schema and not re.search(schema["pattern"], inst):
                self._add(out, warn, "pattern", path, "%s does not match %s" % (_short(inst), schema["pattern"]),
                          expected=schema["pattern"], got=inst)
            if schema.get("x-karvey-format") == "datetime-tz" and not is_datetime_tz(inst):
                self._add(out, warn, "format", path,
                          "%s is not an ISO 8601 date-time with offset" % _short(inst),
                          expected="datetime-tz", got=inst)

        if isinstance(inst, (int, float)) and not isinstance(inst, bool):
            if "minimum" in schema and inst < schema["minimum"]:
                self._add(out, warn, "minimum", path, "%s < minimum %s" % (inst, schema["minimum"]),
                          expected=">= %s" % schema["minimum"], got=inst)
            if "maximum" in schema and inst > schema["maximum"]:
                self._add(out, warn, "maximum", path, "%s > maximum %s" % (inst, schema["maximum"]),
                          expected="<= %s" % schema["maximum"], got=inst)

        if isinstance(inst, list):
            if "minItems" in schema and len(inst) < schema["minItems"]:
                self._add(out, warn, "minItems", path, "fewer than %d items" % schema["minItems"],
                          expected=">= %d items" % schema["minItems"], got=len(inst))
            if "items" in schema:
                for i, item in enumerate(inst):
                    self._v(item, schema["items"], "%s[%d]" % (path, i), base, warn, out)

        if isinstance(inst, dict):
            for req in schema.get("required", []):
                if req not in inst:
                    self._add(out, warn, "required", "%s.%s" % (path, req), "missing required field %r" % req,
                              expected="present", got=None)
            props = schema.get("properties", {})
            for key, val in inst.items():
                sub = "%s.%s" % (path, key)
                if "propertyNames" in schema:
                    tmp = self._branch(key, schema["propertyNames"], sub, base)
                    for it in tmp:
                        it["message"] = "property name %r: %s" % (key, it["message"])
                        if warn:
                            it["severity"] = "warning"
                    out.extend(tmp)
                if key in props:
                    before = len(out)
                    self._v(val, props[key], sub, base, warn, out)
                    if not _violations(out[before:]):
                        self._note_match(props[key], base, sub, out)
                elif "additionalProperties" in schema:
                    ap = schema["additionalProperties"]
                    if ap is False:
                        self._add(out, warn, "additionalProperties", sub, "unknown field %r" % key,
                                  expected=sorted(props), got=key)
                    elif isinstance(ap, dict):
                        before = len(out)
                        self._v(val, ap, sub, base, warn, out)
                        if not _violations(out[before:]):
                            self._note_match(ap, base, sub, out)

        for comb in ("oneOf", "anyOf"):
            if comb in schema:
                results = [self._branch(inst, b, path, base) for b in schema[comb]]
                ok = [i for i, r in enumerate(results) if not _violations(r)]
                good = (len(ok) == 1) if comb == "oneOf" else bool(ok)
                if good:
                    out.extend(results[ok[0]])  # legacy notes found inside the matched branch
                    self._note_match(schema[comb][ok[0]], base, path, out)
                else:
                    if comb == "oneOf" and len(ok) > 1:
                        msg = "matches %d alternatives of oneOf, expected exactly one" % len(ok)
                    else:
                        best = min((_violations(r) for r in results), key=len)
                        msg = "matches none of the %d alternatives (closest: %s)" % (
                            len(results), best[0]["message"] if best else "?")
                    self._add(out, warn, comb, path, msg, got=_short(inst))

        if "if" in schema:
            cond = not _violations(self._branch(inst, schema["if"], path, base))
            branch = schema.get("then") if cond else schema.get("else")
            if branch is not None:
                self._v(inst, branch, path, base, warn, out)


def validate(instance, schema, registry=None, strict=False, file=None):
    """Convenience wrapper: validate ``instance`` against ``schema``."""
    if registry is None:
        registry = load_registry()
    return Validator(schema, registry, file=file).validate(instance, strict=strict)
