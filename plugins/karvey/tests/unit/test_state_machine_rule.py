"""rules/state-machine.md carries a block generated from schemas/state-machine.json (E1.F12.T2).

The block between ``<!-- generated:state-machine -->`` and ``<!-- /generated:state-machine -->`` must equal
``render(state-machine.json)``. After editing the JSON, regenerate the block with::

    python3 plugins/karvey/tests/unit/test_state_machine_rule.py --write
"""
import json
import re
import sys
import unittest

import _path

RULE = _path.PLUGIN_ROOT / "skills" / "karvey" / "rules" / "state-machine.md"
BEGIN, END = "<!-- generated:state-machine -->", "<!-- /generated:state-machine -->"


def machine():
    with open(_path.SCHEMAS_DIR / "state-machine.json", encoding="utf-8-sig") as fh:
        return json.load(fh)


def _list(items):
    return ", ".join("`%s`" % i for i in items) if items else "—"


def render(sm):
    out = ["| # | Phase | Skill | Approval key | Skippable | Produces | Reads |",
           "|---|---|---|---|---|---|---|"]
    for i, p in enumerate(sm["phases"]):
        out.append("| %d | `%s` | `/%s` | %s | %s | %s | %s |" % (
            i, p["id"], p["skill"], "`%s`" % p["approval"] if p["approval"] else "—",
            "yes" if p["skippable"] else "no", _list(p.get("produces", [])), _list(p.get("reads", []))))
    out.append("")
    out.append("- **Edges:** %s." % sm["edges"])
    out.append("- **Reopen targets** (`karvey-state.py reopen`): %s." % _list(sm["reopen_targets"]))
    for k, v in sm["preconditions"].items():
        out.append("- **%s:** %s." % (k, v))
    return "\n".join(out)


def block_of(text):
    m = re.search(re.escape(BEGIN) + r"\n(.*?)\n" + re.escape(END), text, re.S)
    return m.group(1) if m else None


class StateMachineRule(unittest.TestCase):
    def test_rule_exists_with_markers(self):
        text = RULE.read_text(encoding="utf-8")
        self.assertIsNotNone(block_of(text), "generated block markers missing in %s" % RULE.name)

    def test_generated_block_equals_state_machine_json(self):
        got = block_of(RULE.read_text(encoding="utf-8"))
        self.assertEqual(got, render(machine()),
                         "rules/state-machine.md is stale: run this file with --write")

    def test_every_phase_named_once(self):
        got = block_of(RULE.read_text(encoding="utf-8"))
        for p in machine()["phases"]:
            self.assertEqual(len(re.findall(r"^\| \d+ \| `%s` \|" % re.escape(p["id"]), got, re.M)), 1, p["id"])


def write():
    text = RULE.read_text(encoding="utf-8")
    new = re.sub(re.escape(BEGIN) + r"\n(?:.*?\n)?" + re.escape(END),
                 lambda _m: BEGIN + "\n" + render(machine()) + "\n" + END, text, flags=re.S)
    RULE.write_text(new, encoding="utf-8")


if __name__ == "__main__":
    if "--write" in sys.argv:
        write()
    else:
        unittest.main()
