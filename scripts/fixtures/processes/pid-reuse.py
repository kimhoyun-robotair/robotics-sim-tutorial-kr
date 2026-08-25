import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.fixtures.processes._fixture_support import spawn_registered_sentinel  # noqa: E402


spawn_registered_sentinel(stale_identity=True)
raise SystemExit(70)
