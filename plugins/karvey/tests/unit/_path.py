"""Put plugins/karvey/scripts on sys.path so tests can `import karvey_lib`."""
import sys
from pathlib import Path

UNIT_DIR = Path(__file__).resolve().parent
TESTS_DIR = UNIT_DIR.parent
PLUGIN_ROOT = TESTS_DIR.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
SCHEMAS_DIR = PLUGIN_ROOT / "schemas"
REPO_ROOT = PLUGIN_ROOT.parent.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
