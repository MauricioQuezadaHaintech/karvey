"""The routing-only orchestrator (architecture §1.8, C-06).

@req REQ-W3-008
"""
import json
import re
import unittest

import _path

PLUGIN = _path.SCRIPTS_DIR.parent
ORCH = PLUGIN / "skills" / "karvey" / "SKILL.md"
BLOCK_RE = re.compile(r"<!-- karvey:generated routing -->\n(.*?)<!-- /karvey:generated routing -->", re.S)


def routing(text):
    """``{(lane, phase): skill}`` for every cell of the routing table that is not ``s``."""
    m = BLOCK_RE.search(text)
    if m is None:
        return {}
    rows = [r for r in m.group(1).strip().splitlines() if r.startswith("|")]
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    lanes = header[2:]
    out = {}
    for row in rows[2:]:
        cells = [c.strip().strip("`") for c in row.strip("|").split("|")]
        phase, skill = cells[0], cells[1].lstrip("/")
        for lane, rule in zip(lanes, cells[2:]):
            if rule != "s":
                out[(lane, phase)] = skill
    return out


def missing(text):
    """``["{phase} ({lane})", …]`` the orchestrator cannot route, against state-machine.json + lanes.json."""
    machine = json.loads((PLUGIN / "schemas" / "state-machine.json").read_text(encoding="utf-8"))
    lanes = json.loads((PLUGIN / "schemas" / "lanes.json").read_text(encoding="utf-8"))["lanes"]
    skill_of = {p["id"]: p["skill"] for p in machine["phases"]}
    got = routing(text)
    out = []
    for lane, spec in sorted(lanes.items()):
        for phase, rule in spec["phases"].items():
            if rule != "s" and got.get((lane, phase)) != skill_of.get(phase):
                out.append("%s (%s)" % (phase, lane))
    return out


class Routing(unittest.TestCase):
    """@req REQ-W3-008 — every (lane, phase) that runs is routed to the skill the state machine names."""

    def test_every_lane_and_phase_is_routed(self):
        self.assertEqual(missing(ORCH.read_text(encoding="utf-8")), [])

    def test_a_removed_row_fails_naming_phase_and_lane(self):
        text = ORCH.read_text(encoding="utf-8")
        cut = re.sub(r"(?m)^\| `infra` .*\n", "", text)
        self.assertIn("infra (ops)", missing(cut))

    def test_the_orchestrator_calls_the_state_tool(self):
        self.assertIn('karvey-state.py" next', ORCH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
