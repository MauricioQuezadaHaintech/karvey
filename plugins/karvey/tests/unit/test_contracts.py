"""Contract coverage (architecture §1.4, C-02): ``schemas/contracts.json`` and ``karvey-context-budget.py contracts``.

@req REQ-W3-009 REQ-W3-003
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401

TOOL = _path.SCRIPTS_DIR / "karvey-context-budget.py"
PLUGIN = _path.SCRIPTS_DIR.parent
CONTRACTS = PLUGIN / "schemas" / "contracts.json"
IDS = ["state-tool", "gate", "prod-gate", "branch-commit", "verification", "finding-router", "neutral-text"]


def run(*args):
    return subprocess.run([sys.executable, str(TOOL)] + list(args), capture_output=True, text=True, timeout=120)


def fixture_plugin(root, deploy_cites_prod_rule=True, anchor="enforcement.md"):
    """A two-phase plugin: deploy's closure holds (or not) the rule that anchors ``prod-gate``."""
    root = Path(root)
    rules = root / "skills" / "karvey" / "rules"
    rules.mkdir(parents=True)
    (rules / "enforcement.md").write_text("# Enforcement\nProduction needs the human's words.\n", encoding="utf-8")
    (rules / "gates.md").write_text("# Gates\n", encoding="utf-8")
    (root / "schemas").mkdir()
    (root / "schemas" / "state-machine.json").write_text(json.dumps({"phases": [
        {"id": "deploying", "skill": "karvey-deploy"}, {"id": "tasks", "skill": "karvey-tasks"}]}), encoding="utf-8")
    for sk, body in (("karvey-deploy", "Read `rules/enforcement.md` and `rules/gates.md` first.\n" if deploy_cites_prod_rule
                      else "Read `rules/gates.md` first.\n[^r]: rules/enforcement.md — context only.\n"),
                     ("karvey-tasks", "Read `rules/gates.md`.\n"), ("karvey", "# Router\n")):
        (root / "skills" / sk).mkdir(parents=True, exist_ok=True)
        (root / "skills" / sk / "SKILL.md").write_text("---\nname: %s\n---\n%s" % (sk, body), encoding="utf-8")
    (root / "schemas" / "contracts.json").write_text(json.dumps({
        "contracts": [{"id": "prod-gate", "anchor": anchor}, {"id": "gate", "anchor": "gates.md"}],
        "baseline": {"deploy": ["prod-gate", "gate"] if deploy_cites_prod_rule else ["prod-gate"],
                     "tasks": ["gate"]}, "reasons": {}}), encoding="utf-8")
    return root


class Registry(unittest.TestCase):
    """@req REQ-W3-009 — the seven contracts and a baseline row per phase skill."""

    def test_seven_contracts_with_ids(self):
        data = json.loads(CONTRACTS.read_text(encoding="utf-8"))
        self.assertEqual([c["id"] for c in data["contracts"]], IDS)
        self.assertIn("deploy", data["baseline"])
        self.assertIn("prod-gate", data["baseline"]["deploy"])
        for phase, ids in data["baseline"].items():
            self.assertTrue(set(ids) <= set(IDS), phase)
            self.assertIn("neutral-text", ids, phase)

    def test_current_tree_covers_every_pair(self):
        cp = run("contracts", "--json")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        res = json.loads(cp.stdout)["result"]
        self.assertEqual(res["missing"], [])
        self.assertEqual(res["covered"] + len(res["pending"]), res["pairs"])


class Coverage(unittest.TestCase):
    """@req REQ-W3-009 — a removed anchor fails naming the phase and the contract."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="karvey-contracts-"))

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def test_covered_when_the_rule_is_in_the_closure(self):
        plug = fixture_plugin(self.tmp / "ok")
        cp = run("contracts", "--plugin", str(plug))
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("3 of 3", cp.stdout)

    def test_REQ_W3_009_prod_gate_removed_from_deploy_path(self):
        plug = fixture_plugin(self.tmp / "gone", deploy_cites_prod_rule=False)
        cp = run("contracts", "--plugin", str(plug))
        self.assertEqual(cp.returncode, 1)
        self.assertIn("deploy: contract prod-gate not loaded", cp.stderr)

    BODY = ("Production needs the human's own words and a decision id; it is never delegated, never automatic and "
            "never recorded by an agent.\n")

    def core_plugin(self, name, body=BODY, deploy_loads_core=True):
        plug = fixture_plugin(self.tmp / name, deploy_cites_prod_rule=False, anchor="#contract-prod-gate")
        (plug / "skills" / "karvey" / "rules" / "_core.md").write_text(
            "# Core\n## Production gate {#contract-prod-gate}\n" + body + "## Next\nx\n", encoding="utf-8")
        if deploy_loads_core:
            md = plug / "skills" / "karvey-deploy" / "SKILL.md"
            md.write_text(md.read_text(encoding="utf-8") + "Read `rules/_core.md`.\n", encoding="utf-8")
        return plug

    def test_core_heading_anchor_counts_without_the_rule(self):
        self.assertEqual(run("contracts", "--plugin", str(self.core_plugin("core"))).returncode, 0)

    def test_BUG_128_the_core_counts_only_for_a_phase_that_loads_it(self):
        cp = run("contracts", "--plugin", str(self.core_plugin("noload", deploy_loads_core=False)))
        self.assertEqual(cp.returncode, 1, cp.stdout)
        self.assertIn("deploy: contract prod-gate not loaded", cp.stderr)

    def test_BUG_128_an_emptied_contract_section_is_not_loaded(self):
        cp = run("contracts", "--plugin", str(self.core_plugin("empty", body="TBD.\n")))
        self.assertEqual(cp.returncode, 1, cp.stdout)
        self.assertIn("deploy: contract prod-gate not loaded", cp.stderr)

    def test_missing_registry_exits_4(self):
        plug = fixture_plugin(self.tmp / "noreg")
        (plug / "schemas" / "contracts.json").unlink()
        self.assertEqual(run("contracts", "--plugin", str(plug)).returncode, 4)


if __name__ == "__main__":
    unittest.main()
